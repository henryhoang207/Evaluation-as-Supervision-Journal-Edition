"""Confirmatory and pre-specified secondary analysis of the repair study.

Implements ``docs/paper/PREREGISTRATION.md`` sections 2-4 and 6 over the core
checkpoint the runner writes (``out_study/T2/checkpoint.jsonl``). Written
2026-10-07, after the core finished and before any outcome was tabulated; the
rules below are transcribed from the frozen document, not chosen here. Where
this file and the pre-registration disagree, the pre-registration wins and this
file is the bug.

The rules, with their section numbers:

- **Repetition outcome (2.3).** Strict dichotomy: ``repaired`` vs everything
  else. ``deleted`` counts against repair, and the dichotomy is applied per
  repetition *before* any aggregation.
- **Analysis unit (2.4).** The defect. Within each (defect, arm) the completed
  repetitions are averaged into one rate; the primary estimate is the mean of
  per-defect A1 - A2 differences, with a 95% percentile CI from a bootstrap that
  resamples whole defects.
- **Confirmatory test (2.1).** Exactly one: exact McNemar, A1 vs A2, alpha 0.05,
  on the per-defect *majority* dichotomy -- repaired iff strictly more than half
  of completed repetitions were repaired (a 1-1 split is not repaired; r = 1
  scores that repetition). Never McNemar over (defect, rep) pairs.
- **Inclusion (2.4).** A defect enters a contrast only with >= 1 usable
  repetition in both arms; otherwise it is dropped from that contrast and
  counted.
- **Exclusions (4).** ``status_error`` trials and any trial served by more than
  one model are excluded per trial and counted. ``attempts_made > 1`` trials are
  kept, and the primary is also reported without them.
- **Split rule (6).** Branch iff the A1 - A2 point estimate >= 12 pp AND its
  95% CI excludes zero.

Secondaries (3) are computed and labelled as such: the O1 / severe split of the
contrast (1a, reported unconditionally), absolute rates never pooled across O1
and the severe cell (1), A1/A0 (2), A3 by operator (3), per-operator rates (4),
by stage (5), the changed-at-all chain (6), terminal verdicts (7), the O5
sensitivity pair (8), and A2 vs A3 plus Cochran's Q (9).

Run (from backend/, no API calls):

    python scripts/analysis/repair_analysis.py
    python scripts/analysis/repair_analysis.py --checkpoint out_study/T2/checkpoint.jsonl --json out_study/T2/analysis.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from scipy import stats

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ALPHA = 0.05
SPLIT_X = 0.12            # section 6 / D11b
N_BOOT = 10_000
DEFAULT_SEED = 20260803   # the study's sampling seed, reused so nothing is tuned here

O1_CELL = ("O1",)
SEVERE_CELL = ("O2", "O3", "O5", "O6", "O7")


# ── loading and per-trial classification ─────────────────────────────────────


def load_rows(path: str) -> list[dict]:
    rows = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue  # a torn final line from a hard kill; resume rewrote the defect
    # Resume can in principle write a defect twice; the last complete row wins.
    latest: dict[str, dict] = {}
    for row in rows:
        latest[row["defect_id"]] = row
    return list(latest.values())


def outcome_class(trial: dict) -> str | None:
    out = trial.get("outcome")
    if isinstance(out, dict):
        return out.get("outcome")
    return out


def exclusion_reason(trial: dict) -> str | None:
    """Per-trial exclusions of section 4, or None if the trial is usable."""
    if trial.get("status") != "ok":
        return "provider_failure"
    if len(set(trial.get("served_models") or [])) > 1:
        return "fallback_fired"
    if outcome_class(trial) is None:
        return "unscored"
    return None


def usable_trials(rows: list[dict], drop_multi_attempt: bool = False):
    """(usable trials, Counter of exclusions). Trials carry their row's operator."""
    usable, excluded = [], Counter()
    for row in rows:
        for t in row.get("trials", []):
            reason = exclusion_reason(t)
            if reason is None and drop_multi_attempt and (t.get("attempts_made") or 0) > 1:
                reason = "multi_attempt"
            if reason:
                excluded[reason] += 1
                continue
            usable.append({**t, "operator": t.get("operator") or row.get("operator")})
    return usable, excluded


# ── per-(defect, arm) cells ──────────────────────────────────────────────────


def planned_cells(rows: list[dict], condition: str = "C0") -> set:
    """Every (defect, arm) the plan ran under ``condition``, usable or not."""
    return {(t["defect_id"], t["arm"]) for r in rows for t in r.get("trials", [])
            if t.get("condition", "C0") == condition}


def cells(trials: list[dict], success=("repaired",), planned=(), condition: str = "C0") -> dict:
    """{(defect_id, arm): [0/1 per completed repetition]} under ``condition``.

    The dichotomy is applied here, per repetition, before anything aggregates.
    ``planned`` seeds an empty list for every cell the plan ran, so a cell whose
    repetitions were all excluded reads as *lost* rather than as never planned
    -- A0 and A3 run on subsets by design, and their absence is not a loss.
    """
    out: dict = defaultdict(list)
    for key in planned:
        out[key]
    for t in trials:
        if t.get("condition", "C0") != condition:
            continue
        out[(t["defect_id"], t["arm"])].append(1 if outcome_class(t) in success else 0)
    return dict(out)


def majority(reps: list[int]) -> int:
    """Section 2.1: repaired iff strictly more than half of completed reps were."""
    return 1 if sum(reps) * 2 > len(reps) else 0


def paired(cellmap: dict, arm_a: str, arm_b: str, defects=None):
    """Defects with >= 1 usable repetition in both arms, and the rest counted."""
    ids = sorted({d for d, _ in cellmap})
    if defects is not None:
        ids = [d for d in ids if d in defects]
    kept, dropped = [], 0
    for d in ids:
        a, b = cellmap.get((d, arm_a)), cellmap.get((d, arm_b))
        if a is None or b is None:
            continue  # the plan never gave this defect both arms; not a loss
        if a and b:
            kept.append((d, a, b))
        else:
            dropped += 1
    return kept, dropped


# ── estimators ───────────────────────────────────────────────────────────────


def exact_mcnemar(b: int, c: int) -> float:
    """Two-sided exact McNemar on discordant counts b (a only) and c (b only)."""
    n = b + c
    if n == 0:
        return 1.0
    return float(min(1.0, 2.0 * stats.binom.cdf(min(b, c), n, 0.5)))


def cluster_bootstrap_ci(values: np.ndarray, rng, n_boot: int = N_BOOT):
    """Percentile 95% CI of the mean, resampling defects (rows) with replacement."""
    if len(values) == 0:
        return (None, None)
    idx = rng.integers(0, len(values), size=(n_boot, len(values)))
    boot = values[idx].mean(axis=1)
    lo, hi = np.percentile(boot, [2.5, 97.5])
    return (float(lo), float(hi))


def contrast(cellmap: dict, arm_a: str, arm_b: str, seed: int, defects=None) -> dict:
    """Rate difference arm_a - arm_b at the defect level, CI and exact McNemar."""
    kept, dropped = paired(cellmap, arm_a, arm_b, defects)
    rng = np.random.default_rng(seed)
    if not kept:
        return {"arms": f"{arm_a}-{arm_b}", "n_defects": 0, "dropped": dropped}
    ra = np.array([np.mean(a) for _, a, _ in kept])
    rb = np.array([np.mean(b) for _, _, b in kept])
    diff = ra - rb
    lo, hi = cluster_bootstrap_ci(diff, rng)
    ma = [majority(a) for _, a, _ in kept]
    mb = [majority(b) for _, _, b in kept]
    b_count = sum(1 for x, y in zip(ma, mb) if x and not y)
    c_count = sum(1 for x, y in zip(ma, mb) if y and not x)
    reps = Counter((len(a), len(b)) for _, a, b in kept)
    return {
        "arms": f"{arm_a}-{arm_b}",
        "n_defects": len(kept),
        "dropped": dropped,
        f"rate_{arm_a}": float(ra.mean()),
        f"rate_{arm_b}": float(rb.mean()),
        "estimate": float(diff.mean()),
        "ci95": [lo, hi],
        f"majority_{arm_a}": sum(ma),
        f"majority_{arm_b}": sum(mb),
        "discordant": {f"{arm_a}_only": b_count, f"{arm_b}_only": c_count},
        "mcnemar_p": exact_mcnemar(b_count, c_count),
        "reps_per_cell": {f"{k[0]}/{k[1]}": v for k, v in sorted(reps.items())},
    }


def ratio(cellmap: dict, num: str, den: str, seed: int) -> dict:
    """Ratio of mean defect-level rates (section 3 item 2), CI over defects."""
    kept, dropped = paired(cellmap, num, den)
    if not kept:
        return {"arms": f"{num}/{den}", "n_defects": 0, "dropped": dropped}
    rn = np.array([np.mean(a) for _, a, _ in kept])
    rd = np.array([np.mean(b) for _, _, b in kept])
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(kept), size=(N_BOOT, len(kept)))
    num_b, den_b = rn[idx].mean(axis=1), rd[idx].mean(axis=1)
    ok = den_b > 0
    boot = num_b[ok] / den_b[ok]
    lo, hi = (np.percentile(boot, [2.5, 97.5]) if ok.any() else (np.nan, np.nan))
    return {"arms": f"{num}/{den}", "n_defects": len(kept), "dropped": dropped,
            "estimate": float(rn.mean() / rd.mean()) if rd.mean() > 0 else None,
            "ci95": [float(lo), float(hi)]}


def cochran_q(cellmap: dict, arms: tuple[str, ...]) -> dict:
    """Cochran's Q on per-defect majority outcomes, defects carrying every arm."""
    ids = sorted({d for d, _ in cellmap})
    rows = [[majority(cellmap[(d, a)]) for a in arms]
            for d in ids if all(cellmap.get((d, a)) for a in arms)]
    if not rows:
        return {"arms": list(arms), "n_defects": 0}
    x = np.array(rows)
    k = x.shape[1]
    col, row = x.sum(axis=0), x.sum(axis=1)
    n_total = x.sum()
    denom = k * n_total - (row ** 2).sum()
    q = 0.0 if denom == 0 else (k - 1) * (k * (col ** 2).sum() - n_total ** 2) / denom
    return {"arms": list(arms), "n_defects": len(rows), "Q": float(q), "df": k - 1,
            "p": float(stats.chi2.sf(q, k - 1)) if denom else 1.0,
            "majority_by_arm": dict(zip(arms, map(int, col)))}


def rates_by(trials: list[dict], key, success=("repaired",)) -> dict:
    """Defect-level mean rate per (group, arm): repetitions averaged first."""
    per_cell: dict = defaultdict(list)
    for t in trials:
        if t.get("condition", "C0") != "C0":
            continue
        per_cell[(key(t), t["arm"], t["defect_id"])].append(
            1 if outcome_class(t) in success else 0)
    grouped: dict = defaultdict(list)
    for (g, arm, _), reps in per_cell.items():
        grouped[(g, arm)].append(np.mean(reps))
    return {f"{g}|{arm}": {"rate": float(np.mean(v)), "n_defects": len(v)}
            for (g, arm), v in sorted(grouped.items())}


def split_rule(primary: dict) -> dict:
    est, (lo, hi) = primary.get("estimate"), primary.get("ci95", (None, None))
    if est is None:
        return {"branch": False, "reason": "no estimate"}
    excludes_zero = lo is not None and (lo > 0 or hi < 0)
    return {"branch": bool(est >= SPLIT_X and excludes_zero),
            "estimate_ge_12pp": bool(est >= SPLIT_X), "ci_excludes_zero": bool(excludes_zero)}


# ── the report ───────────────────────────────────────────────────────────────


def analyse(rows: list[dict], seed: int = DEFAULT_SEED) -> dict:
    trials, excluded = usable_trials(rows)
    trials_sa, excluded_sa = usable_trials(rows, drop_multi_attempt=True)
    all_trials = [t for r in rows for t in r.get("trials", [])]

    planned = planned_cells(rows)
    cm = cells(trials, planned=planned)
    defects_by_op = defaultdict(set)
    for t in trials:
        defects_by_op[t["operator"]].add(t["defect_id"])
    o1 = set().union(*(defects_by_op[o] for o in O1_CELL))
    severe = set().union(*(defects_by_op[o] for o in SEVERE_CELL))
    no_o5 = {d for o, ds in defects_by_op.items() if o != "O5" for d in ds}

    primary = contrast(cm, "A1", "A2", seed)
    rep_change = Counter()
    for t in trials:
        rep_change[(t["arm"], outcome_class(t))] += 1

    return {
        "provenance": {
            "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "seed": seed, "n_boot": N_BOOT,
            "defect_rows": len(rows),
            "defect_rows_by_status": dict(Counter(r.get("status") for r in rows)),
            "trials_total": len(all_trials),
            "trials_usable": len(trials),
            "exclusions": dict(excluded),
            "attempts_made": dict(Counter(t.get("attempts_made") for t in all_trials)),
            "served_models": dict(Counter(m for t in all_trials for m in (t.get("served_models") or []))),
            "total_tokens": int(sum(t.get("total_tokens") or 0 for t in all_trials)),
        },
        "confirmatory": {
            "primary_A1_minus_A2": primary,
            "significant_at_alpha": bool(primary.get("mcnemar_p", 1.0) < ALPHA),
            "split_rule": split_rule(primary),
            "without_multi_attempt_trials": {
                "exclusions": dict(excluded_sa),
                **contrast(cells(trials_sa, planned=planned), "A1", "A2", seed),
            },
        },
        "secondary": {
            "1a_O1_contrast": contrast(cm, "A1", "A2", seed, defects=o1),
            "1a_severe_contrast": contrast(cm, "A1", "A2", seed, defects=severe),
            "1_rates_O1_vs_severe": rates_by(
                trials, lambda t: "O1" if t["operator"] in O1_CELL else "severe"),
            "2_A1_over_A0": ratio(cm, "A1", "A0", seed),
            "3_A3_by_operator": {k: v for k, v in rates_by(trials, lambda t: t["operator"]).items()
                                 if k.endswith("|A3")},
            "4_rates_by_operator": rates_by(trials, lambda t: t["operator"]),
            "5_rates_by_stage": rates_by(trials, lambda t: t.get("stage")),
            "6_outcome_classes_by_arm": {f"{a}|{o}": n for (a, o), n in sorted(rep_change.items())},
            "7_terminal_verdict_by_arm": {
                f"{a}|{v}": n for (a, v), n in sorted(
                    Counter((t["arm"], t.get("post_verdict")) for t in trials).items())},
            "8_without_O5": contrast(cm, "A1", "A2", seed, defects=no_o5),
            "8_O5_repaired_or_replaced": rates_by(
                [t for t in trials if t["operator"] == "O5"], lambda t: "O5",
                success=("repaired", "replaced")),
            "9_A2_vs_A3": contrast(cm, "A2", "A3", seed),
            "9_cochran_q_A1_A2_A3": cochran_q(cm, ("A1", "A2", "A3")),
            "collateral_by_arm": _collateral(trials),
        },
    }


# ── the post-core passes (PREREGISTRATION.md section 0.1 A2, A3) ─────────────


def _rate_ci(cellmap: dict, arm: str, seed: int) -> dict:
    """One arm's defect-level repair rate with a defect-bootstrap CI."""
    per_defect = np.array([np.mean(v) for (d, a), v in sorted(cellmap.items())
                           if a == arm and v])
    if not len(per_defect):
        return {"arm": arm, "n_defects": 0}
    lo, hi = cluster_bootstrap_ci(per_defect, np.random.default_rng(seed))
    return {"arm": arm, "n_defects": int(len(per_defect)),
            "rate": float(per_defect.mean()), "ci95": [lo, hi]}


def analyse_c1(rows: list[dict], core_rows: list[dict] | None = None,
               seed: int = DEFAULT_SEED) -> dict:
    """Section 0.1 A3: two gaps with CIs, never a test (D8c).

    Both gaps come from the c1 pass alone, so C0 and C1 share a session per
    defect. The difference of gaps is reported as an estimate with a CI, as
    ``power.py`` section 7 computes it, not as a hypothesis test. Against the
    core, the re-run C0 cells measure serving drift.
    """
    trials, excluded = usable_trials(rows)
    gaps = {}
    for cond in ("C0", "C1"):
        cm = cells(trials, planned=planned_cells(rows, cond), condition=cond)
        gaps[cond] = contrast(cm, "A1", "A2", seed)
    cm0 = cells(trials, condition="C0")
    cm1 = cells(trials, condition="C1")
    did, ids = [], []
    for d in sorted({d for d, _ in cm0} & {d for d, _ in cm1}):
        parts = [cm0.get((d, "A1")), cm0.get((d, "A2")), cm1.get((d, "A1")), cm1.get((d, "A2"))]
        if all(parts):
            m = [np.mean(p) for p in parts]
            did.append((m[2] - m[3]) - (m[0] - m[1]))
            ids.append(d)
    did = np.array(did)
    lo, hi = cluster_bootstrap_ci(did, np.random.default_rng(seed))
    out = {
        "provenance": {
            "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "seed": seed, "n_boot": N_BOOT, "trials_usable": len(trials),
            "exclusions": dict(excluded),
            "served_models": dict(Counter(m for r in rows for t in r.get("trials", [])
                                          for m in (t.get("served_models") or []))),
        },
        "gap_C0": gaps["C0"],
        "gap_C1": gaps["C1"],
        "gap_C1_minus_gap_C0": {"n_defects": len(did),
                                "estimate": float(did.mean()) if len(did) else None,
                                "ci95": [lo, hi]},
        "rates": {f"{c}|{a}": _rate_ci(cells(trials, condition=c), a, seed)
                  for c in ("C0", "C1") for a in ("A1", "A2")},
    }
    if core_rows is not None:
        out["drift_vs_core"] = _drift(trials, usable_trials(core_rows)[0])
    return out


def _drift(rerun: list[dict], core: list[dict]) -> dict:
    """Re-run C0 trials against the core's C0 trials: same defect, arm and rep."""
    key = lambda t: (t["defect_id"], t["arm"], t.get("rep"))
    core_by = {key(t): t for t in core if t.get("condition", "C0") == "C0"}
    pairs = [(t, core_by[key(t)]) for t in rerun
             if t.get("condition", "C0") == "C0" and key(t) in core_by]
    same_class = sum(1 for a, b in pairs if outcome_class(a) == outcome_class(b))
    canon = lambda t: json.dumps(t.get("retried_output"), sort_keys=True, ensure_ascii=False)
    same_bytes = sum(1 for a, b in pairs if canon(a) == canon(b))
    flips = Counter((outcome_class(b), outcome_class(a)) for a, b in pairs
                    if outcome_class(a) != outcome_class(b))
    return {"pairs": len(pairs), "same_outcome_class": same_class,
            "byte_identical_output": same_bytes,
            "flips_core_to_rerun": {f"{x}->{y}": n for (x, y), n in sorted(flips.items())}}


def analyse_d19(rows: list[dict], seed: int = DEFAULT_SEED) -> dict:
    """Section 7: retry (A1) against overwrite, with A3 beside it.

    Overwrite is exact by construction at zero calls, so it is a constant, not
    an arm. Section 7 fixes both readings: retry well below 1.0, or repaired at a
    cost in collateral, means the overwrite was a correctness decision; ~100%
    with no collateral means it was a cost optimisation.
    """
    trials, excluded = usable_trials(rows)
    cm = cells(trials, planned=planned_cells(rows))
    classes = Counter((t["arm"], outcome_class(t)) for t in trials)
    calls = defaultdict(list)
    for t in trials:
        calls[t["arm"]].append(t.get("attempts_made") or 0)
    return {
        "provenance": {
            "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "seed": seed, "n_boot": N_BOOT, "trials_usable": len(trials),
            "exclusions": dict(excluded),
            "served_models": dict(Counter(m for r in rows for t in r.get("trials", [])
                                          for m in (t.get("served_models") or []))),
            "total_tokens": int(sum(t.get("total_tokens") or 0 for t in trials)),
        },
        "overwrite": {"rate": 1.0, "llm_calls": 0, "note": "exact by construction"},
        "A1_retry": _rate_ci(cm, "A1", seed),
        "A3_regeneration": _rate_ci(cm, "A3", seed),
        "A1_minus_A3": contrast(cm, "A1", "A3", seed),
        "outcome_classes": {f"{a}|{o}": n for (a, o), n in sorted(classes.items())},
        "collateral_by_arm": _collateral(trials),
        "llm_calls_per_trial": {a: float(np.mean(v)) for a, v in calls.items()},
    }


def _collateral(trials: list[dict]) -> dict:
    out = {}
    for arm in sorted({t["arm"] for t in trials}):
        meas = [t for t in trials if t["arm"] == arm
                and isinstance(t.get("outcome"), dict) and t["outcome"].get("collateral_measurable")]
        hit = sum(1 for t in meas if t["outcome"].get("collateral"))
        out[arm] = {"rate": hit / len(meas) if meas else None, "measurable": len(meas)}
    return out


def _pct(x):
    return "n/a" if x is None else f"{100 * x:.1f}%"


def print_summary(res: dict) -> None:
    p = res["provenance"]
    c = res["confirmatory"]["primary_A1_minus_A2"]
    print(f"trials {p['trials_usable']}/{p['trials_total']} usable · exclusions {p['exclusions']}")
    print(f"attempts {p['attempts_made']} · models {p['served_models']}")
    print("\nCONFIRMATORY — A1 vs A2 (pre-registration 2.1)")
    print(f"  defects {c['n_defects']} (dropped {c['dropped']}) · reps per cell {c['reps_per_cell']}")
    print(f"  A1 {_pct(c['rate_A1'])} · A2 {_pct(c['rate_A2'])} · "
          f"A1-A2 {100 * c['estimate']:+.1f} pp, 95% CI [{100 * c['ci95'][0]:+.1f}, {100 * c['ci95'][1]:+.1f}]")
    print(f"  majority repaired: A1 {c['majority_A1']} · A2 {c['majority_A2']} · "
          f"discordant {c['discordant']} · exact McNemar p = {c['mcnemar_p']:.4g}")
    print(f"  split rule: {res['confirmatory']['split_rule']}")
    s = res["confirmatory"]["without_multi_attempt_trials"]
    print(f"  without attempts>1: {100 * s['estimate']:+.1f} pp [{100 * s['ci95'][0]:+.1f}, "
          f"{100 * s['ci95'][1]:+.1f}] on {s['n_defects']} defects, p = {s['mcnemar_p']:.4g}")
    sec = res["secondary"]
    print("\nSECONDARY (not confirmatory)")
    for k in ("1a_O1_contrast", "1a_severe_contrast", "8_without_O5", "9_A2_vs_A3"):
        x = sec[k]
        if x.get("n_defects"):
            print(f"  {k:22s} {x['arms']}: {100 * x['estimate']:+.1f} pp "
                  f"[{100 * x['ci95'][0]:+.1f}, {100 * x['ci95'][1]:+.1f}] n={x['n_defects']} p={x['mcnemar_p']:.4g}")
    r = sec["2_A1_over_A0"]
    if r.get("estimate") is not None:
        print(f"  A1/A0 ratio {r['estimate']:.3f} [{r['ci95'][0]:.3f}, {r['ci95'][1]:.3f}] n={r['n_defects']}")
    q = sec["9_cochran_q_A1_A2_A3"]
    if q.get("n_defects"):
        print(f"  Cochran Q (A1,A2,A3) = {q['Q']:.3f}, df {q['df']}, p = {q['p']:.4g}, n={q['n_defects']}")
    print("  rates O1 vs severe:", {k: _pct(v["rate"]) for k, v in sec["1_rates_O1_vs_severe"].items()})
    print("  outcome classes by arm:", sec["6_outcome_classes_by_arm"])


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--cell", default="core", choices=("core", "c1", "d19"))
    ap.add_argument("--checkpoint", default=None,
                    help="defaults per --cell: out_study/T2, T2C1 or T2D19")
    ap.add_argument("--core-checkpoint", default="out_study/T2/checkpoint.jsonl",
                    help="--cell c1 only: the core, for the serving-drift comparison")
    ap.add_argument("--json", default=None, help="write the full result here")
    ap.add_argument("--seed", type=int, default=DEFAULT_SEED)
    args = ap.parse_args()
    checkpoint = args.checkpoint or {
        "core": "out_study/T2", "c1": "out_study/T2C1", "d19": "out_study/T2D19",
    }[args.cell] + "/checkpoint.jsonl"
    if args.cell == "core":
        res = analyse(load_rows(checkpoint), seed=args.seed)
        print_summary(res)
    else:
        if args.cell == "c1":
            core = load_rows(args.core_checkpoint) if Path(args.core_checkpoint).exists() else None
            res = analyse_c1(load_rows(checkpoint), core, seed=args.seed)
        else:
            res = analyse_d19(load_rows(checkpoint), seed=args.seed)
        print(json.dumps({k: v for k, v in res.items() if k != "provenance"}, indent=2))
        print("provenance:", json.dumps(res["provenance"]))
    if args.json:
        Path(args.json).write_text(json.dumps(res, indent=2), encoding="utf-8")
        print(f"\nwrote {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
