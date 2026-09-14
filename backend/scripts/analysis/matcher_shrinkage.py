"""Trace-matcher shrinkage — PHASE0_MEMO Q1, JOURNAL_PLAN section 17.

``supervision._measure_strategy`` decides whether a recommendation traces to
upstream with ``difflib`` — a character-level ratio — against
``TRACE_SIMILARITY = 0.35``. The D13 audit (JOURNAL_PLAN 15.4, 16.4) showed that
comparing characters both misses real paraphrases and matches unrelated strings.
This script measures what a content-word matcher would change, without changing
anything:

1. the Tier-1 defect bank;
2. every observe-mode strategy output (Phase A and the repetitions), in both
   error directions;
3. O5 applicability, and so the Tier-2 N;
4. the frozen O5 corpus issues against every Phase-A base (alien content);
5. whether the O5 *manipulation* is touched at all — its bases and the issues
   it injects.

The answer decided D22: the bug reaches O5's measurement but not its
manipulation, so the production supervisor stays as shipped for the study and
the scorer is corrected instead.

Read-only: no API calls, no dataset. Run from backend/:

    venv/Scripts/python.exe scripts/analysis/matcher_shrinkage.py
"""

from __future__ import annotations

import argparse
import glob
import importlib.util
import json
import os
import sys
from collections import Counter

BACKEND = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BACKEND)

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from app.core import supervision  # noqa: E402


def _load(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, os.path.join(BACKEND, relative))
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


inject_defects = _load("inject_defects", "scripts/inject_defects.py")

# The single copy of the content-word tokeniser (verify_claim3.py's, verbatim).
# score_repair decides O5 with the same module, so what this script measures and
# what the scorer applies cannot drift onto two definitions.
content_match = _load("content_match", "scripts/analysis/content_match.py")
tokens = content_match.tokens
jaccard = content_match.jaccard
containment = content_match.containment


def lexical(issue: str, candidate: str) -> float:
    return supervision._similar(issue, candidate)


def _best(fn, issue: str, candidates: list[str]) -> float:
    return max((fn(issue, c) for c in candidates), default=0.0)


# Each matcher answers one question: does this issue TRACE to an upstream candidate?
MATCHERS = {
    "lexical>=0.35": lambda i, cs: _best(lexical, i, cs) >= supervision.TRACE_SIMILARITY,
    "contain>0": lambda i, cs: _best(containment, i, cs) > 0.0,
    "contain>=0.34": lambda i, cs: _best(containment, i, cs) >= 0.34,
    "contain>=0.50": lambda i, cs: _best(containment, i, cs) >= 0.50,
    "jaccard>=0.05": lambda i, cs: _best(jaccard, i, cs) >= 0.05,
    "jaccard>=0.10": lambda i, cs: _best(jaccard, i, cs) >= 0.10,
}
SHIPPED = "lexical>=0.35"
PRIMARY = "jaccard>=0.10"  # the D22 choice; see JOURNAL_PLAN 17.2 for why this one
CONTENT = [m for m in MATCHERS if m != SHIPPED]
SEEDS = (0, 1, 42)


def candidates(state: dict) -> list[str]:
    return [c for c in inject_defects._trace_candidates(state) if c]


def issues(state: dict) -> list[str]:
    recs = (state.get("strategy_output") or {}).get("recommendations") or []
    return [r.get("issue", "") for r in recs]


def untraceable(state: dict, matcher: str) -> list[str]:
    cs = candidates(state)
    return [i for i in issues(state) if not MATCHERS[matcher](i, cs)]


def _strategy_ok(state: dict) -> bool:
    out = state.get("strategy_output")
    return out is not None and out.get("status") != "error"


def _resolve(path: str) -> str:
    return path if os.path.isabs(path) or os.path.exists(path) else os.path.join(BACKEND, path)


# ── 1. Tier 1 ─────────────────────────────────────────────────────────────────


def tier1(root: str) -> dict:
    with open(os.path.join(root, "defect_bank.json"), encoding="utf-8") as fh:
        bank = json.load(fh)
    usable = [e for e in bank["entries"] if e["usable"]]
    reasoning = sum(1 for e in usable if e["stage"] != "strategy_agent")

    survive: Counter = Counter()
    mismatches: list[str] = []
    flagged: list[dict] = []
    for entry in usable:
        if entry["stage"] != "strategy_agent":
            for m in MATCHERS:
                survive[m] += 1  # reasoning-stage classes never consult the trace matcher
            continue
        state = inject_defects.state_from_dump(_resolve(entry["dump_dir"]))
        recorded = list((entry.get("facts") or {}).get("untraceable_issues") or [])
        if sorted(recorded) != sorted(untraceable(state, SHIPPED)):
            mismatches.append(entry["defect_id"])
        cs = candidates(state)
        for issue in recorded:
            flagged.append({
                "business": entry.get("business_name"), "issue": issue,
                "lexical": round(_best(lexical, issue, cs), 3),
                "containment": round(_best(containment, issue, cs), 3),
                "jaccard": round(_best(jaccard, issue, cs), 3),
            })
        for m in MATCHERS:
            if untraceable(state, m):
                survive[m] += 1

    return {"usable": len(usable), "reasoning": reasoning, "by_matcher": dict(survive),
            "sanity_mismatches": mismatches, "flagged_issues": flagged}


# ── 2. every observe-mode strategy output ────────────────────────────────────


def population(root: str) -> dict:
    dirs = inject_defects.base_dirs(root) + sorted(
        d for d in glob.glob(os.path.join(root, "R", "rep*", "A", "*")) if os.path.isdir(d)
    )
    states, unreadable = [], 0
    for d in dirs:
        try:
            state = inject_defects.state_from_dump(d)
        except Exception:
            unreadable += 1
            continue
        if _strategy_ok(state) and issues(state):
            states.append(state)

    flagged_stages = {m: sum(1 for s in states if untraceable(s, m)) for m in MATCHERS}
    flagged_issues = {m: sum(len(untraceable(s, m)) for s in states) for m in MATCHERS}
    versus: dict[str, dict] = {}
    for m in CONTENT:
        c: Counter = Counter()
        for s in states:
            shipped, fix = set(untraceable(s, SHIPPED)), set(untraceable(s, m))
            key = ("both" if shipped and fix else "shipped_only" if shipped
                   else "fix_only" if fix else "neither")
            c[key] += 1
            c["issues_shipped_only"] += len(shipped - fix)
            c["issues_fix_only"] += len(fix - shipped)
        versus[m] = {k: c[k] for k in ("shipped_only", "fix_only", "both", "neither",
                                       "issues_shipped_only", "issues_fix_only")}

    return {"stages": len(states), "issues": sum(len(issues(s)) for s in states),
            "unreadable": unreadable, "flagged_stages": flagged_stages,
            "flagged_issues": flagged_issues, "versus_shipped": versus}


# ── 3. O5 applicability and N ─────────────────────────────────────────────────


def o5_applicability(root: str) -> dict:
    ceiling = inject_defects.matrix(root)["summary"]["repair_operators"]
    counts, reasons = {}, {}
    for m in MATCHERS:
        n, why = 0, Counter()
        for d in inject_defects.base_dirs(root):
            state = inject_defects.state_from_dump(d)
            if not _strategy_ok(state):
                why["stage_absent_or_error"] += 1
            elif untraceable(state, m):
                why["base_not_clean"] += 1
            elif not issues(state):
                why["no_recommendations"] += 1
            elif not [ci for ci in inject_defects.CORPUS_ISSUES
                      if not MATCHERS[m](ci, candidates(state))]:
                why["no_untraceable_corpus_issue"] += 1
            else:
                n += 1
        counts[m], reasons[m] = n, dict(why)
    return {"applicable": counts, "inapplicable": reasons,
            "N": {m: ceiling - counts[SHIPPED] + counts[m] for m in MATCHERS},
            "shipped_N": ceiling}


# ── 4. alien content ──────────────────────────────────────────────────────────


def alien(root: str) -> dict:
    per_base = [candidates(inject_defects.state_from_dump(d)) for d in inject_defects.base_dirs(root)]
    pairs = [(ci, cs) for cs in per_base for ci in inject_defects.CORPUS_ISSUES]
    candidate_pairs = sum(
        1 for ci, cs in pairs for c in cs if lexical(ci, c) >= supervision.TRACE_SIMILARITY
    )
    return {
        "issue_base_pairs": len(pairs),
        "traced": {m: sum(1 for ci, cs in pairs if MATCHERS[m](ci, cs)) for m in MATCHERS},
        "zero_content_words": sum(1 for ci, cs in pairs if _best(containment, ci, cs) == 0.0),
        # JOURNAL_PLAN 16.4 counted issue x CANDIDATE pairs; this reconciles the two.
        "shipped_issue_candidate_pairs": candidate_pairs,
    }


# ── 5. is the O5 manipulation touched? ────────────────────────────────────────


def o5_manipulation(root: str, seeds: tuple[int, ...] = SEEDS) -> dict:
    bases = []
    for d in inject_defects.base_dirs(root):
        state = inject_defects.state_from_dump(d)
        if inject_defects.applicable("O5", state)[0]:
            bases.append(state)

    injected: dict[int, dict] = {}
    for seed in seeds:
        found = []
        for base in bases:
            after, _ = inject_defects.inject("O5", base, seed=seed)
            found.extend((i, candidates(base)) for i in issues(after) if i not in issues(base))
        injected[seed] = {"n": len(found),
                          "traced": {m: sum(1 for i, cs in found if MATCHERS[m](i, cs))
                                     for m in MATCHERS}}

    return {"bases": len(bases),
            "bases_flagged": {m: sum(1 for b in bases if untraceable(b, m)) for m in MATCHERS},
            "injected": injected}


def measure(root: str) -> dict:
    return {"tier1": tier1(root), "population": population(root),
            "o5": o5_applicability(root), "alien": alien(root),
            "manipulation": o5_manipulation(root)}


def report(s: dict) -> None:
    t = s["tier1"]
    print("=" * 96)
    print(f"1. TIER 1 - usable today {t['usable']} ({t['usable'] - t['reasoning']} strategy, "
          f"{t['reasoning']} reasoning)")
    print("=" * 96)
    print(f"{'business':28} {'lex':>5} {'cont':>5} {'jac':>5}  flagged issue")
    for f in t["flagged_issues"]:
        print(f"{(f['business'] or '')[:28]:28} {f['lexical']:5.2f} {f['containment']:5.2f} "
              f"{f['jaccard']:5.2f}  {f['issue'][:56]}")
    for m in MATCHERS:
        mark = "  <- shipped" if m == SHIPPED else "  <- D22 primary" if m == PRIMARY else ""
        print(f"  {m:15} Tier-1 usable {t['by_matcher'][m]:2d}{mark}")
    print(f"  shipped matcher reproduces every recorded flag: "
          f"{'YES' if not t['sanity_mismatches'] else t['sanity_mismatches']}")

    p = s["population"]
    print("\n" + "=" * 96)
    print(f"2. ALL OBSERVE-MODE STRATEGY OUTPUTS - {p['stages']} stages, {p['issues']} issues")
    print("=" * 96)
    print(f"  shipped flags {p['flagged_stages'][SHIPPED]} stages / {p['flagged_issues'][SHIPPED]} issues")
    print(f"  {'content matcher':15} {'shipped-only':>13} {'fix-only':>9} {'both':>5} {'neither':>8}"
          f" {'issues shipped-only':>20} {'fix-only':>9}")
    for m, v in p["versus_shipped"].items():
        print(f"  {m:15} {v['shipped_only']:>13} {v['fix_only']:>9} {v['both']:>5} {v['neither']:>8}"
              f" {v['issues_shipped_only']:>20} {v['issues_fix_only']:>9}")

    o = s["o5"]
    print("\n" + "=" * 96)
    print("3. O5 APPLICABILITY AND N")
    print("=" * 96)
    for m in MATCHERS:
        print(f"  {m:15} O5 {o['applicable'][m]:2d}  N {o['N'][m]:3d}  {o['inapplicable'][m]}")

    a = s["alien"]
    print("\n" + "=" * 96)
    print(f"4. ALIEN CONTENT - {a['issue_base_pairs']} issue x base pairs, "
          f"{a['zero_content_words']} share no content word")
    print("=" * 96)
    for m in MATCHERS:
        print(f"  {m:15} calls alien content traceable in {a['traced'][m]:3d}")
    print(f"  (shipped, counted as issue x candidate pairs: {a['shipped_issue_candidate_pairs']})")

    x = s["manipulation"]
    print("\n" + "=" * 96)
    print(f"5. IS THE O5 MANIPULATION TOUCHED? - {x['bases']} O5 bases")
    print("=" * 96)
    print(f"  bases flagged: {x['bases_flagged']}")
    for seed, v in x["injected"].items():
        print(f"  seed {seed:>2}: {v['n']} injected issues, traced: {v['traced']}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", default="out_study")
    ap.add_argument("--json", default=None, help="also write the measurement here")
    args = ap.parse_args()
    summary = measure(args.root)
    report(summary)
    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(summary, fh, indent=2)
        print(f"\nwrote {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
