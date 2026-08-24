"""Replay one pipeline stage's supervision cycle from a dump directory (B3).

The closure property that makes verification free also makes the pipeline a
replayable fault-injection testbed: every stage's input is fully captured in the
stage outputs already on disk, so a recorded run can be re-entered offline.

**The Yelp dataset is not needed.** The three in-scope stages (D6: reasoning,
strategy, report) read only upstream *outputs*:

    _measure_reasoning  <- reasoning_output, analysis_results
    _measure_strategy   <- strategy_output,  reasoning_output
    _measure_report     <- report_output,    reasoning_output, strategy_output,
                           business_name, len(analysis_results)

``reviews_df`` is read by ``_measure_analysis`` alone (the stars-vs-sentiment
contradiction check), and the analysis stage is out of scope. So replay needs no
loader, no SQLite index, no 5.34 GB review file and no ``MAX_REVIEW_SAMPLE``
override — the four dump JSONs plus ``_summary.json`` are sufficient, and the
study runs on a machine that has never seen the dataset.

Trap this module exists to avoid: do NOT route a replay through
``graph.orchestrator_node``. ``supervision.latest_stage`` infers the stage by
scanning backward from ``report_output``, so a state holding all four dumps
always reports ``report_agent`` whichever stage you meant. Every entry point
here takes an explicit stage.

Run (from backend/, venv active — read-only, no API calls):

    python scripts/replay_stage.py --dump-dir out_study/A/<bid> --stage reasoning_agent
    python scripts/replay_stage.py --verify out_study        # fidelity gate
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from app.core import supervision  # noqa: E402
from eval.common import load_dump  # noqa: E402

# Stages this module can replay from dumps alone. analysis_agent is excluded
# because its measurement needs the sampled reviews, which dumps do not carry —
# the same boundary as JOURNAL_PLAN D6.
REPLAYABLE = ("reasoning_agent", "strategy_agent", "report_agent")


def state_from_dump(dump_dir: str) -> dict:
    """Reconstruct the parts of PipelineState that supervision actually reads."""
    dump = load_dump(dump_dir)
    return {
        "business_id": dump.summary.get("business_id"),
        "business_name": dump.summary.get("business_name"),
        "analysis_results": dump.analysis,
        "reasoning_output": dump.reasoning,
        "strategy_output": dump.strategy,
        "report_output": dump.report,
        # Deliberately absent: reviews_df. Any future check that needs it must
        # fail loudly here rather than silently measure against an empty frame.
    }


def replay(stage: str, state: dict, retry_counts: dict | None = None) -> tuple[dict, supervision.Decision]:
    """One supervision cycle for an explicit stage: measure, then decide."""
    if stage not in supervision.AGENT_SEQUENCE:
        raise ValueError(f"unknown stage {stage!r}")
    facts = supervision.measure(stage, state)
    decision = supervision.decide(stage, facts, retry_counts or {})
    return facts, decision


# ── fidelity gate ────────────────────────────────────────────────────────────


def _observed_runs(root: str) -> list[tuple[str, str, list[dict]]]:
    """(label, dump_dir, observations) for every observe-mode run under root.

    Observations are recorded only in observe mode (graph.orchestrator_node), so
    each stage in these runs executed exactly once and the dump on disk is
    precisely the output that was measured. That is what makes an exact
    comparison meaningful.
    """
    out = []
    checkpoints = [("A", os.path.join(root, "A", "checkpoint.jsonl"))]
    checkpoints += [
        (os.path.basename(os.path.dirname(os.path.dirname(p))), p)
        for p in sorted(glob.glob(os.path.join(root, "R", "rep*", "A", "checkpoint.jsonl")))
    ]
    for label, path in checkpoints:
        if not os.path.exists(path):
            continue
        base = os.path.dirname(path)
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if row.get("status") != "ok" or not row.get("observations"):
                    continue
                dump_dir = os.path.join(base, row["business_id"])
                if os.path.isdir(dump_dir):
                    out.append((f"{label}/{row['business_id']}", dump_dir, row["observations"]))
    return out


def _norm(value):
    """JSON round-trip so recomputed facts and recorded facts compare like-for-like."""
    return json.loads(json.dumps(value, ensure_ascii=False, sort_keys=True))


def verify(root: str) -> int:
    """Golden gate: recomputed facts must equal the recorded facts exactly.

    Returns the number of mismatches. Analysis-stage observations are reported
    as skipped rather than passed — they are unverifiable from dumps, and
    counting them as passes would overstate the gate.
    """
    checked = mismatched = skipped = 0
    failures: list[str] = []

    for label, dump_dir, observations in _observed_runs(root):
        state = state_from_dump(dump_dir)
        for obs in observations:
            stage = obs.get("stage")
            if stage not in REPLAYABLE:
                skipped += 1
                continue
            recomputed, _ = replay(stage, state)
            if _norm(recomputed) == _norm(obs.get("facts")):
                checked += 1
            else:
                mismatched += 1
                failures.append(f"{label} :: {stage}")

    print(f"replay fidelity: {checked} facts reproduced exactly, "
          f"{mismatched} mismatched, {skipped} skipped (analysis stage, needs reviews)")
    for f in failures[:20]:
        print(f"  MISMATCH  {f}")
    if mismatched == 0 and checked:
        print("GATE PASS — dumps replay bit-identically; injection trials may proceed.")
    elif mismatched:
        print("GATE FAIL — stop and fix before any trial (JOURNAL_PLAN section 11).")
    return mismatched


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dump-dir", help="a single dump directory to replay")
    ap.add_argument("--stage", choices=list(supervision.AGENT_SEQUENCE))
    ap.add_argument("--verify", metavar="ROOT", help="run the fidelity gate over a study root")
    args = ap.parse_args()

    if args.verify:
        return 1 if verify(args.verify) else 0

    if not args.dump_dir or not args.stage:
        ap.error("give --dump-dir and --stage, or --verify ROOT")

    if args.stage not in REPLAYABLE:
        print(f"warning: {args.stage} needs reviews_df, which dumps do not carry; "
              f"facts will be measured against an absent review set.", file=sys.stderr)

    facts, decision = replay(args.stage, state_from_dump(args.dump_dir))
    print(json.dumps(
        {
            "stage": args.stage,
            "verdict": decision.verdict,
            "flags": decision.flags,
            "retry_feedback": decision.retry_feedback,
            "facts": facts,
        },
        indent=2,
        ensure_ascii=False,
    ))
    return 0


if __name__ == "__main__":
    sys.exit(main())
