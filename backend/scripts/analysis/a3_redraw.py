"""What A3 will score on injected defects — JOURNAL_PLAN 17.6.

A3 is the bare re-draw: the original prompt again, nothing added, and only ever
at P0 (D9b). At P0 the injected output never enters the model's context (D10).
So an A3 trial regenerates the stage from pinned, clean upstream with no
feedback: a fresh draw that has never seen the synthetic defect.

The plan's A3 prediction ("near zero or negative", PREREGISTRATION section 5)
and ``power.py``'s ``p(A3) = 0.05`` both come from self-correction work on
*self-generated* errors, which a temperature-0 re-draw tends to reproduce. An
injected defect it cannot reproduce, because it never saw it.

This script estimates A3's score without an API call: inject into one
repetition run, treat an independent repetition of the same business as the
re-draw, and score it with the study's own scorer.

Two limits, both stated in 17.6:

- Repetition runs regenerate *every* stage, so a reasoning-stage "re-draw" here
  sits on different analysis output from its base. That inflates
  ``unrepaired`` for O1-O3 (O3's figure is mostly that), so their A3 estimates
  are **low**, not high.
- O6 and O7 are exact by construction: an invented corpus item cannot appear in
  a draw that never saw it. Those 52 of the 142 defects put a hard floor under
  pooled A3 that does not depend on this approximation at all.

Read-only: no API calls, no dataset. Run from backend/:

    venv/Scripts/python.exe scripts/analysis/a3_redraw.py
"""

from __future__ import annotations

import argparse
import glob
import importlib.util
import itertools
import json
import os
import sys
from collections import Counter, defaultdict

BACKEND = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BACKEND)

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def _load(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, os.path.join(BACKEND, relative))
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


score_repair = _load("score_repair", "scripts/analysis/score_repair.py")
inject_defects = score_repair.inject_defects
supervision = score_repair.supervision

CLASSES = score_repair.OUTCOME_CLASSES
BY_CONSTRUCTION = ("O6", "O7")  # insertion operators: the invented item cannot recur


def _descriptions(state: dict) -> list[str]:
    return [p.get("description", "") for p in (state.get("reasoning_output") or {}).get("patterns") or []]


def _upstream_stable(a: dict, b: dict) -> bool:
    """D3c's conditioning rule: symmetric pattern-description match >= 0.95."""
    fwd = score_repair.churn_mod.matched_fraction(_descriptions(a), _descriptions(b), score_repair.SAME_ITEM)
    rev = score_repair.churn_mod.matched_fraction(_descriptions(b), _descriptions(a), score_repair.SAME_ITEM)
    return fwd is not None and rev is not None and (fwd + rev) / 2 >= 0.95


def _redraw(base: dict, other: dict, stage: str) -> dict:
    """``other``'s draw of ``stage``, placed the way ``_regenerate`` places a retry."""
    key = inject_defects.OUTPUT_KEY[stage]
    if stage == "report_agent":
        # A report re-draw is consistent with the upstream it was written from.
        retried = dict(other)
    else:
        retried = dict(base)
        retried[key] = other.get(key)  # replay semantics: upstream pinned, the stage re-drawn
    later = supervision.AGENT_SEQUENCE[supervision.AGENT_SEQUENCE.index(stage) + 1:]
    for stage_after in later:
        if stage_after in inject_defects.OUTPUT_KEY:
            retried[inject_defects.OUTPUT_KEY[stage_after]] = None
    return retried


def plan_counts(root: str) -> dict[str, int]:
    """Applicable defects per repair operator on the Phase-A bases — the N = 142 mix."""
    counts: Counter = Counter()
    for d in inject_defects.base_dirs(root):
        state = inject_defects.state_from_dump(d)
        for op in inject_defects.REPAIR_OPERATORS:
            counts[op] += inject_defects.applicable(op, state)[0]
    return dict(counts)


def estimate(root: str) -> dict:
    by_business: dict[str, list[dict]] = defaultdict(list)
    for rep in sorted(glob.glob(os.path.join(root, "R", "rep*", "A"))):
        for d in sorted(glob.glob(os.path.join(rep, "*"))):
            if os.path.isdir(d):
                by_business[os.path.basename(d)].append(inject_defects.state_from_dump(d))

    operators = tuple(inject_defects.REPAIR_OPERATORS) + ("O4",)
    counts: dict[str, Counter] = defaultdict(Counter)
    for states in by_business.values():
        for base, other in itertools.permutations(states, 2):
            stable = _upstream_stable(base, other)
            for op in operators:
                stage = inject_defects.STAGE[op]
                if stage != "reasoning_agent" and not stable:
                    continue
                if not inject_defects.applicable(op, base)[0]:
                    continue
                _, descriptor = inject_defects.inject(op, base, seed=0)
                if not descriptor.applied:
                    continue
                retried = _redraw(base, other, stage)
                if (retried.get(inject_defects.OUTPUT_KEY[stage]) or {}).get("status") != "success":
                    counts[op]["not_success"] += 1
                    continue
                counts[op][score_repair.score(descriptor, base, retried).outcome] += 1

    per_op = {}
    for op in operators:
        c = counts[op]
        n = sum(c[k] for k in CLASSES)
        per_op[op] = {"n": n, **{k: c[k] for k in CLASSES},
                      "repair_rate": round(c["repaired"] / n, 3) if n else None,
                      "not_success": c["not_success"]}

    mix = plan_counts(root)
    total = sum(mix.values())
    pooled = sum(mix[op] * (per_op[op]["repair_rate"] or 0.0) for op in mix) / total
    floor = sum(mix[op] for op in BY_CONSTRUCTION) / total
    return {"per_operator": per_op, "plan_mix": mix, "plan_N": total,
            "pooled_repair_rate": round(pooled, 3),
            "by_construction_floor": round(floor, 3),
            "power_py_assumes": 0.05}


def report(e: dict) -> None:
    print("A3 (bare re-draw at P0) on injected defects - an independent repetition scored as the re-draw\n")
    print(f"  {'op':3} {'n':>4} {'repaired':>9} {'replaced':>9} {'deleted':>8} {'unrepaired':>11}")
    for op, r in e["per_operator"].items():
        if not r["n"]:
            print(f"  {op:3}    0  (no scorable pairs)")
            continue
        n = r["n"]
        print(f"  {op:3} {n:>4} {r['repaired']/n:>9.0%} {r['replaced']/n:>9.0%} "
              f"{r['deleted']/n:>8.0%} {r['unrepaired']/n:>11.0%}")
    print(f"\n  pooled over the plan's N={e['plan_N']} mix {e['plan_mix']}: "
          f"A3 repair ~ {e['pooled_repair_rate']:.0%}")
    print(f"  floor from O6/O7 alone (by construction): {e['by_construction_floor']:.0%}")
    print(f"  power.py assumes p(A3) = {e['power_py_assumes']:.0%}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", default="out_study")
    ap.add_argument("--json", default=None, help="also write the estimate here")
    args = ap.parse_args()
    e = estimate(args.root)
    report(e)
    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(e, fh, indent=2)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
