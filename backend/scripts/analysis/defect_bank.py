"""Tier-1 defect bank inventory (JOURNAL_PLAN section 5, build item preceding B3).

Scans the study checkpoints for retry-triggering observations, classifies each
by the supervisor check that fired, and separates *genuine* content defects from
infrastructure noise.

Why the separation matters. Three of the fifteen retry-triggering observations
recorded by the conference study are Gemini 503 ``status_error`` retries, not
groundedness defects. Replaying one of those replays an API outage: there is no
defect for the retried stage to repair, so the trial has no interpretation under
any arm. Counting them would inflate the Tier-1 denominator by 25%.

The bank this writes is the input to the replay runner. It is deliberately
read-only over ``out_study/`` and makes no LLM calls.

Run (from backend/, venv active):

    python scripts/analysis/defect_bank.py
    python scripts/analysis/defect_bank.py --root out_study --out out_study/defect_bank.json
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import sys
from collections import Counter

# The repository path contains non-ASCII characters and the Windows console
# defaults to cp1252. Force UTF-8 so printing a business name cannot kill a run.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


# Maps a fired check to the synthetic operator that models it (section 4
# operator catalog). Used for the Just-style coupling check: an operator with no
# real counterpart here cannot participate in it.
_OPERATORS = {
    "missing_evidence_id": ["O1", "O2"],
    "misaligned_aspect": ["O3"],
    "frequency_divergence": ["O4"],
    "untraceable_recommendation": ["O5"],
    "report_containment": ["O6", "O7"],
    "metadata_mismatch": ["O8"],
}


def _read_jsonl(path: str) -> list[dict]:
    rows = []
    if not os.path.exists(path):
        return rows
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue  # tolerate a torn final line from a hard kill
    return rows


def sources(root: str) -> list[tuple[str, str, str]]:
    """(label, checkpoint path, dump root) for Phase A and every repetition."""
    found = [("A", os.path.join(root, "A", "checkpoint.jsonl"), os.path.join(root, "A"))]
    for path in sorted(glob.glob(os.path.join(root, "R", "rep*", "A", "checkpoint.jsonl"))):
        rep_a_dir = os.path.dirname(path)
        label = os.path.basename(os.path.dirname(rep_a_dir))  # rep1, rep2, ...
        found.append((label, path, rep_a_dir))
    return [(lab, p, d) for lab, p, d in found if os.path.exists(p)]


def fired_classes(stage: str, facts: dict) -> list[str]:
    """Retry-level check classes evidenced by ``facts``, in taxonomy order.

    Single source of truth for the taxonomy. ``classify`` uses it to inventory
    natural defects; the injection operators (B4) use it to verify that a
    synthetic defect trips the check it was built to trip, and only that one.
    Two private copies would drift, and the section 5 coupling check would then
    be comparing two different taxonomies without saying so.

    Deliberately excludes frequency divergence: it never reaches a retry, so it
    is not a class ``classify`` can ever see. See :func:`frequency_divergent`.
    """
    classes: list[str] = []

    if stage == "analysis_agent":
        if (facts.get("failure_ratio") or 0) > 0.5:
            classes.append("analysis_failure_ratio")
        if facts.get("contradiction_rate") is not None:
            classes.append("stars_sentiment_contradiction")
    elif stage == "reasoning_agent":
        patterns = facts.get("patterns") or []
        if any(p.get("missing_evidence_ids") for p in patterns):
            classes.append("missing_evidence_id")
        if any(p.get("misaligned_evidence_ids") for p in patterns):
            classes.append("misaligned_aspect")
    elif stage == "strategy_agent":
        if facts.get("untraceable_issues"):
            classes.append("untraceable_recommendation")
    elif stage == "report_agent":
        if facts.get("invented_root_causes") or facts.get("invented_recommendations"):
            classes.append("report_containment")
        if facts.get("name_mismatch") or facts.get("size_mismatch"):
            classes.append("metadata_mismatch")

    return classes


def frequency_divergent(facts: dict, tolerance: float = 0.05) -> bool:
    """Whether any reasoning pattern's claimed frequency is out of tolerance.

    Separate from :func:`fired_classes` because it is a different severity, not
    a different check: ``supervision._quality_rules`` turns this into
    ``proceed_with_warning`` and never into a retry, and ``graph`` then
    overwrites the claimed value outright. Nothing an LLM does affects it.
    """
    for p in facts.get("patterns") or []:
        claimed = p.get("claimed_frequency")
        if claimed is None:
            continue
        if abs(claimed - (p.get("recomputed_frequency") or 0.0)) > tolerance:
            return True
    return False


def classify(stage: str, facts: dict) -> tuple[list[str], bool, str | None]:
    """Return (classes, genuine, excluded_reason) for one retry observation.

    ``status_error`` is checked first and short-circuits: an API failure is the
    reason the retry fired, and whatever else the facts contain was measured on
    an output that does not exist.
    """
    if facts.get("status_error"):
        return ["api_error"], False, "api_error"

    classes = fired_classes(stage, facts)

    if not classes:
        # A retry verdict with no recognised class means decide() and this
        # function have drifted apart — surface it rather than dropping it.
        return ["unclassified"], False, "unclassified"
    return classes, True, None


_STAGE_FILE = {
    "analysis_agent": "analysis",
    "reasoning_agent": "reasoning",
    "strategy_agent": "strategy",
    "report_agent": "report",
}
_ORDER = ["analysis_agent", "reasoning_agent", "strategy_agent", "report_agent"]


def upstream_degenerate(dump_dir: str, stage: str) -> str | None:
    """Was this stage handed a broken or empty upstream?

    A defect produced while every upstream stage was healthy is an ordinary
    content defect. A defect produced downstream of an errored or empty stage is
    a *cascade*: the model invented content to fill a gap that only existed
    because something upstream failed. Both are real, but they are different
    estimands and must not be pooled — replaying a cascade measures
    degenerate-input containment, not repair of an ungrounded claim.
    """
    for earlier in _ORDER[: _ORDER.index(stage)]:
        path = os.path.join(dump_dir, f"{_STAGE_FILE[earlier]}.json")
        if not os.path.exists(path):
            continue
        try:
            with open(path, encoding="utf-8") as fh:
                payload = json.load(fh)
        except (json.JSONDecodeError, OSError):
            continue
        if isinstance(payload, dict):
            if payload.get("status") == "error":
                return f"{earlier} errored ({payload.get('error_type') or 'unknown'})"
            if earlier == "reasoning_agent" and not (
                payload.get("patterns") or payload.get("root_causes")
            ):
                return "reasoning_agent produced no patterns or root causes"
            if earlier == "strategy_agent" and not payload.get("recommendations"):
                return "strategy_agent produced no recommendations"
    return None


def build(root: str) -> dict:
    entries: list[dict] = []
    warn_flags: Counter = Counter()

    for label, checkpoint, dump_root in sources(root):
        for row in _read_jsonl(checkpoint):
            if row.get("status") != "ok":
                continue
            bid = row.get("business_id")
            for i, obs in enumerate(row.get("observations") or []):
                verdict = obs.get("would_be_verdict")
                if verdict == "proceed_with_warning":
                    for flag in obs.get("flags") or []:
                        warn_flags[flag.split(":")[0]] += 1
                    continue
                if verdict != "retry":
                    continue

                stage = obs.get("stage")
                facts = obs.get("facts") or {}
                classes, genuine, excluded = classify(stage, facts)
                operators = sorted({op for c in classes for op in _OPERATORS.get(c, [])})
                dump_dir = os.path.join(dump_root, bid or "")
                cascade = upstream_degenerate(dump_dir, stage) if genuine else None

                entries.append(
                    {
                        "defect_id": f"{label}:{bid}:{stage}:{i}",
                        "source": label,
                        "business_id": bid,
                        "business_name": row.get("business_name"),
                        "stage": stage,
                        "dump_dir": dump_dir.replace("\\", "/"),
                        "classes": classes,
                        "operators": operators,
                        "genuine": genuine,
                        "excluded_reason": excluded,
                        "cascade_of": cascade,
                        "usable": genuine and cascade is None,
                        "retry_feedback": obs.get("retry_feedback"),
                        "facts": facts,
                    }
                )

    genuine = [e for e in entries if e["usable"]]
    cascades = [e for e in entries if e["genuine"] and not e["usable"]]
    # A cell is business ID x stage: chains share names (two Wingstops are
    # sampled), so keying on the name could pool two businesses.
    names = {e["business_id"]: e["business_name"] for e in genuine}
    cells = sorted({(e["business_id"], e["stage"]) for e in genuine},
                   key=lambda c: (names[c[0]] or "", c[0], c[1]))

    return {
        "root": root,
        "entries": entries,
        "warn_level_flags": dict(warn_flags),
        "cascades": [
            {"defect_id": e["defect_id"], "stage": e["stage"], "cascade_of": e["cascade_of"]}
            for e in cascades
        ],
        "summary": {
            "retry_observations": len(entries),
            "genuine": len(genuine),
            "cascade": len(cascades),
            "excluded": len(entries) - len(genuine) - len(cascades),
            "excluded_by_reason": dict(
                Counter(e["excluded_reason"] for e in entries if not e["genuine"])
            ),
            "by_stage": dict(Counter(e["stage"] for e in genuine)),
            "by_class": dict(Counter(c for e in genuine for c in e["classes"])),
            "distinct_cells": len(cells),
            "distinct_businesses": len(names),
            "cells": [{"business": names[b], "business_id": b, "stage": s} for b, s in cells],
            "observations_per_cell": dict(
                Counter(f"{e['business_name']} [{e['business_id']}] / {e['stage']}" for e in genuine)
            ),
        },
    }


def report(bank: dict) -> None:
    s = bank["summary"]
    print(f"Retry-triggering observations : {s['retry_observations']}")
    print(f"  usable content defects      : {s['genuine']}")
    print(f"  cascade (report separately) : {s['cascade']}")
    print(f"  excluded                    : {s['excluded']} {s['excluded_by_reason'] or ''}")
    for c in bank["cascades"]:
        print(f"      {c['defect_id']}  <- {c['cascade_of']}")
    print()
    print(f"Genuine by stage : {s['by_stage']}")
    print(f"Genuine by class : {s['by_class']}")
    print()
    print(
        f"Cluster structure: {s['genuine']} instances in {s['distinct_cells']} "
        f"business x stage cells across {s['distinct_businesses']} businesses"
    )
    for cell, n in sorted(s["observations_per_cell"].items(), key=lambda kv: -kv[1]):
        print(f"  {n:>2} x  {cell}")
    print()
    print(f"Warn-level flags (not retries): {bank['warn_level_flags']}")

    # Operator coupling coverage — which synthetic operators have a real
    # counterpart to be validated against, and which have none.
    covered = {op for e in bank["entries"] if e["usable"] for op in e["operators"]}
    missing = sorted({op for ops in _OPERATORS.values() for op in ops} - covered)
    print(f"Operators with a real counterpart : {sorted(covered)}")
    print(f"Operators WITHOUT one             : {missing}  <- no coupling check possible")

    trials = s["genuine"] * 4 * 3
    print()
    print(f"Tier-1 design size: {s['genuine']} defects x 4 arms x r=3 = {trials} trials")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default="out_study", help="study output root")
    ap.add_argument("--out", default=None, help="write the bank as JSON here")
    args = ap.parse_args()

    if not os.path.isdir(args.root):
        print(f"No study root at {args.root!r} — nothing to inventory.")
        return 1

    bank = build(args.root)
    report(bank)

    if args.out:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump(bank, fh, indent=2, ensure_ascii=False)
        print(f"\nWrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
