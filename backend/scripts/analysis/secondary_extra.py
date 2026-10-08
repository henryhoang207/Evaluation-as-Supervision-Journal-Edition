"""The remaining pre-specified analyses that need no API call (2026-10-08).

Every number here comes from data already on disk; nothing calls an LLM.

1. **Defect origin** (PREREGISTRATION.md section 3 item 5): real (Tier-1) beside
   injected defects on the one footing they share -- the supervisor's own
   acceptance of the retried output at P0 -- per arm and stage.
2. **Change, then resolution** (section 3 item 6, MAS-FIRE's O/L split): did
   the retried output change at all, and among those that changed, was the
   defect resolved.
3. **Class ordering** (section 5's prediction): referential (O1/O2) >
   structural (O3, O6, O7) > semantic (O5), on A1's defect-level repair rate.
4. **C6 detection curves** (plan section 3, C6): O4 swept across frequency
   gaps; and the trace check's two matchers on grounded recommendation issues
   (every clean strategy output) against foreign ones (every corpus issue on
   every base) -- the D22 finding as a measured curve.
5. **Coupling** (plan section 5, Tier 1 item 3): the share of real defects
   whose firing check has a synthetic operator.

Run (from backend/, venv active):

    python scripts/analysis/secondary_extra.py --json out_study/secondary_extra.json
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


inj = _load("inject_defects", HERE.parent / "inject_defects.py")   # also puts backend/ on sys.path
ra = _load("repair_analysis", HERE / "repair_analysis.py")
cm = _load("content_match", HERE / "content_match.py")
db = inj.defect_bank

from app.core import supervision  # noqa: E402

BLOCKING = ("retry", "halt")
CLASSES = {"referential": ("O1", "O2"), "structural": ("O3", "O6", "O7"), "semantic": ("O5",)}
SEED = ra.DEFAULT_SEED


def _boot(values, seed=SEED):
    arr = np.array(list(values))
    if not len(arr):
        return {"n_defects": 0}
    lo, hi = ra.cluster_bootstrap_ci(arr, np.random.default_rng(seed))
    return {"rate": float(arr.mean()), "ci95": [lo, hi], "n_defects": int(len(arr))}


def _per_defect(trials, value):
    reps = defaultdict(list)
    for t in trials:
        reps[t["defect_id"]].append(value(t))
    return {d: float(np.mean(v)) for d, v in reps.items()}


def _ok(rows):
    return [t for r in rows for t in r.get("trials", []) if t.get("status") == "ok"]


# -- 1. defect origin ----------------------------------------------------------


def origin(core_rows, placement_rows, tier1_rows) -> dict:
    """Supervisor acceptance at P0: real vs injected, per arm and stage."""
    accepted = lambda t: 0.0 if t.get("post_verdict") in BLOCKING else 1.0
    t1 = _ok(tier1_rows)
    syn = {"A1": [t for t in _ok(placement_rows) if t["arm"] == "A1" and t["placement"] == "P0"],
           "A3": [t for t in _ok(core_rows) if t["arm"] == "A3" and t["placement"] == "P0"]}
    out = {"note": ("Real defects run at P0 by design (D10); injected ones are taken at P0 "
                    "from the placement pass (A1) and the core (A3). Same criterion for "
                    "both: the supervisor routes the retried output to no retry. "
                    "Descriptive; the real cell has 13 defects in 7 cells.")}
    for arm in ("A1", "A3"):
        for stage in ("reasoning_agent", "strategy_agent", "all"):
            pick = lambda ts: [t for t in ts if t["arm"] == arm and (stage == "all" or t["stage"] == stage)]
            real = _per_defect(pick(t1), lambda t: 1.0 if t["accepted"] else 0.0)
            injected = _per_defect([t for t in syn[arm] if stage == "all" or t["stage"] == stage], accepted)
            out[f"{arm}|{stage}"] = {"real": _boot(real.values()), "injected": _boot(injected.values())}
    return out


# -- 2. change, then resolution ------------------------------------------------


def change_then_resolve(core_rows, tier1_rows, root) -> dict:
    canon = lambda o: json.dumps(o, sort_keys=True, ensure_ascii=False)
    dirs = {Path(d).name: d for d in inj.base_dirs(root)}
    injected_out = {}
    for r in core_rows:
        if not r.get("trials"):
            continue
        op = r["operator"]
        base = inj.state_from_dump(dirs[r["defect_id"].rsplit(":", 1)[0]])
        state, desc = inj.inject(op, base, seed=0)
        injected_out[r["defect_id"]] = canon(state.get(inj.OUTPUT_KEY[desc.stage]))
    out = {}
    for arm in ("A0", "A1", "A2", "A3"):
        ts = [t for t in _ok(core_rows) if t["arm"] == arm]
        changed = [t for t in ts if canon(t.get("retried_output")) != injected_out[t["defect_id"]]]
        resolved = [t for t in changed if t["outcome"]["outcome"] == "repaired"]
        out[f"core|{arm}"] = {"trials": len(ts), "changed": len(changed),
                              "changed_share": len(changed) / len(ts) if ts else None,
                              "repaired_given_changed": len(resolved) / len(changed) if changed else None}
    for arm in ("A1", "A2", "A3"):
        ts = [t for t in _ok(tier1_rows) if t["arm"] == arm]
        changed = [t for t in ts if not t["same_as_original"]]
        resolved = [t for t in changed if t["accepted"]]
        out[f"tier1|{arm}"] = {"trials": len(ts), "changed": len(changed),
                               "changed_share": len(changed) / len(ts) if ts else None,
                               "accepted_given_changed": len(resolved) / len(changed) if changed else None}
    return out


# -- 3. class ordering ---------------------------------------------------------


def class_ordering(core_rows) -> dict:
    trials = [t for t in _ok(core_rows) if t["arm"] == "A1"]
    repaired = lambda t: 1.0 if t["outcome"]["outcome"] == "repaired" else 0.0
    out = {}
    for name, ops in CLASSES.items():
        out[name] = _boot(_per_defect([t for t in trials if t["operator"] in ops], repaired).values())
    order = sorted(CLASSES, key=lambda c: -out[c]["rate"])
    out["observed_order"] = order
    out["predicted_order"] = ["referential", "structural", "semantic"]
    out["prediction_holds"] = order == out["predicted_order"]
    out["per_operator"] = {op: _boot(_per_defect([t for t in trials if t["operator"] == op],
                                                 repaired).values()).get("rate")
                           for op in ("O1", "O2", "O3", "O5", "O6", "O7")}
    return out


# -- 4. C6 detection curves ----------------------------------------------------


def c6_frequency(root, deltas=(0.0, 0.01, 0.02, 0.03, 0.04, 0.05, 0.051, 0.06, 0.08,
                               0.10, 0.15, 0.20, 0.30)) -> dict:
    bases = [inj.state_from_dump(d) for d in inj.base_dirs(root)]
    bases = [b for b in bases if inj.applicable("O4", b)[0]]
    out = {"bases": len(bases), "tolerance": supervision.FREQUENCY_TOLERANCE, "curve": {}}
    for delta in deltas:
        hits, verdicts = 0, Counter()
        for b in bases:
            state, _ = inj.inject("O4", b, seed=0, delta=delta)
            facts = supervision.measure("reasoning_agent", state)
            hits += db.frequency_divergent(facts, supervision.FREQUENCY_TOLERANCE)
            verdicts[supervision.decide("reasoning_agent", facts, {}).verdict] += 1
        out["curve"][f"{delta:g}"] = {"detected": hits / len(bases), "verdicts": dict(verdicts)}
    return out


def c6_trace(root) -> dict:
    """Both trace matchers on grounded issues vs foreign ones, across every base."""
    grounded, foreign = [], []
    for d in inj.base_dirs(root):
        state = inj.state_from_dump(d)
        cands = inj._trace_candidates(state)
        if not cands:
            continue
        for rec in (state.get("strategy_output") or {}).get("recommendations") or []:
            grounded.append((str(rec.get("issue") or ""), cands))
        for issue in inj.CORPUS_ISSUES:
            foreign.append((issue, cands))

    def production_fires(issue, cands):
        return max((supervision._similar(issue, c) for c in cands if c), default=0.0) \
            < supervision.TRACE_SIMILARITY

    def content_fires(issue, cands):
        return cm.best_jaccard(issue, cands) < cm.TRACE_JACCARD

    def rates(items):
        return {"n": len(items),
                "production_difflib_fires": sum(production_fires(i, c) for i, c in items) / len(items),
                "content_jaccard_fires": sum(content_fires(i, c) for i, c in items) / len(items)}

    bins = [(0.0, 0.2), (0.2, 0.3), (0.3, 0.35), (0.35, 0.45), (0.45, 1.01)]
    curve = {}
    for lo, hi in bins:
        sel = [(i, c) for i, c in grounded
               if lo <= max((supervision._similar(i, x) for x in c if x), default=0.0) < hi]
        if sel:
            curve[f"[{lo:.2f},{hi:.2f})"] = rates(sel)
    return {"grounded_issues": rates(grounded), "foreign_corpus_issues": rates(foreign),
            "grounded_by_production_similarity": curve,
            "note": ("A grounded issue is a recommendation from a clean observe-mode strategy "
                     "output; 'fires' on it is a false positive. A foreign issue is a corpus "
                     "issue placed on another business; 'fires' on it is a true positive.")}


# -- 5. coupling ---------------------------------------------------------------


def coupling(root) -> dict:
    bank = db.build(root)
    usable = [e for e in bank["entries"] if e["usable"]]
    coupled = [e for e in usable if e["operators"]]
    return {"real_defects": len(usable), "with_a_synthetic_operator": len(coupled),
            "share": len(coupled) / len(usable) if usable else None,
            "classes": dict(Counter(c for e in usable for c in e["classes"])),
            "note": "by construction at the check-class level: every class that fires has an operator"}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--root", default="out_study")
    ap.add_argument("--json", default=None)
    args = ap.parse_args()
    core = ra.load_rows(f"{args.root}/T2/checkpoint.jsonl")
    placement = ra.load_rows(f"{args.root}/T2P/checkpoint.jsonl")
    tier1 = ra.load_rows(f"{args.root}/T1/checkpoint.jsonl")
    res = {
        "origin": origin(core, placement, tier1),
        "change_then_resolve": change_then_resolve(core, tier1, args.root),
        "class_ordering": class_ordering(core),
        "c6_frequency": c6_frequency(args.root),
        "c6_trace": c6_trace(args.root),
        "coupling": coupling(args.root),
    }
    print(json.dumps(res, indent=1)[:6000])
    if args.json:
        Path(args.json).write_text(json.dumps(res, indent=2), encoding="utf-8")
        print(f"\nwrote {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
