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
import importlib.util
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
    out = {"arm": arm, "n_defects": int(len(per_defect)),
           "rate": float(per_defect.mean()), "ci95": [lo, hi]}
    # A percentile bootstrap of a constant is that constant: [1.0, 1.0] when
    # every defect scored 1.0, which reads as certainty. Report the exact
    # Clopper-Pearson interval over defects beside it in that case.
    if np.all(per_defect == 1.0) or np.all(per_defect == 0.0):
        out["exact_ci95_defects"] = clopper_pearson(int(per_defect.sum()), len(per_defect))
    return out


def clopper_pearson(k: int, n: int, alpha: float = ALPHA) -> list[float]:
    """Exact two-sided binomial interval for k successes in n."""
    lo = 0.0 if k == 0 else float(stats.beta.ppf(alpha / 2, k, n - k + 1))
    hi = 1.0 if k == n else float(stats.beta.ppf(1 - alpha / 2, k + 1, n - k))
    return [lo, hi]


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


def factor_cells(trials: list[dict], level_of, arm: str | None = "A1",
                 success=("repaired",)) -> dict:
    """{(defect_id, level): [0/1 per rep]} for one arm, the level read by ``level_of``.

    The placement and severity passes vary a factor *within* one arm, so the
    second key is the factor level rather than the arm; ``contrast`` and
    ``_rate_ci`` take it unchanged. ``arm=None`` keeps every arm, for passes
    whose levels are (arm, factor) pairs.
    """
    out: dict = defaultdict(list)
    for t in trials:
        if (arm is not None and t["arm"] != arm) or t.get("condition", "C0") != "C0":
            continue
        out[(t["defect_id"], level_of(t))].append(1 if outcome_class(t) in success else 0)
    return dict(out)


def _factor_report(rows: list[dict], level_of, levels, contrasts, seed: int,
                   core_rows: list[dict] | None, comparator_level, comparator_filter) -> dict:
    trials, excluded = usable_trials(rows)
    cm = factor_cells(trials, level_of)
    out = {
        "provenance": {
            "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "seed": seed, "n_boot": N_BOOT, "trials_usable": len(trials),
            "exclusions": dict(excluded),
            "served_models": dict(Counter(m for r in rows for t in r.get("trials", [])
                                          for m in (t.get("served_models") or []))),
            "total_tokens": int(sum(t.get("total_tokens") or 0 for t in trials)),
        },
        "rates": {str(lv): _rate_ci(cm, lv, seed) for lv in levels},
        "contrasts": {f"{a}-{b}": contrast(cm, a, b, seed) for a, b in contrasts},
        "outcome_classes": {f"{lv}|{o}": n for (lv, o), n in sorted(
            Counter((level_of(t), outcome_class(t)) for t in trials).items())},
        "collateral_by_level": {
            str(lv): _collateral([t for t in trials if level_of(t) == lv]).get("A1")
            for lv in levels},
    }
    # Section 4: trials with attempts_made > 1 are analysed separately, and every
    # estimate is also reported without them. A schema retry appends the
    # model's own invalid output as an assistant turn, a P2-like condition, so
    # where retries concentrate in one level the contrast is partly a
    # contamination contrast.
    multi = Counter(str(level_of(t)) for t in trials if (t.get("attempts_made") or 0) > 1)
    trials_sa, _ = usable_trials(rows, drop_multi_attempt=True)
    cm_sa = factor_cells(trials_sa, level_of)
    out["multi_attempt_trials_by_level"] = {str(lv): multi.get(str(lv), 0) for lv in levels}
    out["without_multi_attempt_trials"] = {
        "rates": {str(lv): _rate_ci(cm_sa, lv, seed) for lv in levels},
        "contrasts": {f"{a}-{b}": contrast(cm_sa, a, b, seed) for a, b in contrasts},
    }
    if core_rows is not None:
        rerun = [t for t in trials if level_of(t) == comparator_level]
        core = [t for t in usable_trials(core_rows)[0] if comparator_filter(t)]
        out["drift_vs_core"] = _drift(rerun, core)
    return out


def analyse_placement(rows: list[dict], core_rows: list[dict] | None = None,
                      seed: int = DEFAULT_SEED) -> dict:
    """Section 0.1 A5: A1 at P0-P3, matched within defect and session.

    Section 5 recorded the prediction before any result: **P1 >> P3 ~ P2**, with
    P0 reported separately and not folded into the ordering. Exploratory.
    """
    res = _factor_report(
        rows, lambda t: t["placement"], ("P0", "P1", "P2", "P3"),
        (("P1", "P2"), ("P1", "P3"), ("P3", "P2"), ("P1", "P0")), seed,
        core_rows, "P1", lambda t: t["arm"] == "A1" and t["placement"] == "P1")
    res["prediction"] = "P1 >> P3 ~ P2; P0 reported separately (PREREGISTRATION.md section 5)"
    return res


def analyse_severity(rows: list[dict], core_rows: list[dict] | None = None,
                     seed: int = DEFAULT_SEED) -> dict:
    """Section 0.1 A6: O1 at level 1 vs level 2, A1 at P1. Exploratory."""
    return _factor_report(
        rows, lambda t: t.get("severity", 1), (1, 2), ((1, 2),), seed,
        core_rows, 1, lambda t: t["arm"] == "A1" and t.get("operator") == "O1")


WARM_LEVELS = ("A1@T0", "A2@T0", "A1@T1", "A2@T1", "A3@T1")


def warm_level(t: dict) -> str:
    return f"{t['arm']}@T{float(t.get('temperature', 0.0)):g}"


def _gap_difference(cm: dict, a1: str, b1: str, a0: str, b0: str, seed: int) -> dict:
    """Per-defect (a1 - b1) - (a0 - b0), bootstrapped over defects."""
    vals = []
    for d in sorted({d for d, _ in cm}):
        parts = [cm.get((d, lv)) for lv in (a1, b1, a0, b0)]
        if all(parts):
            m = [np.mean(p) for p in parts]
            vals.append((m[0] - m[1]) - (m[2] - m[3]))
    vals = np.array(vals)
    lo, hi = cluster_bootstrap_ci(vals, np.random.default_rng(seed))
    return {"n_defects": int(len(vals)),
            "estimate": float(vals.mean()) if len(vals) else None, "ci95": [lo, hi]}


def best_of_k(cm: dict, level: str, k_max: int, seed: int) -> dict:
    """Share of defects repaired by at least one of the first k draws, k = 1..k_max.

    Draws are taken in repetition order, which is execution order, so this is
    the curve a caller resampling k times would have seen -- not the best k of
    any order, which would be the same number for every k >= the first success.
    """
    reps = [v for (d, lv), v in sorted(cm.items()) if lv == level and v]
    out = {}
    for k in range(1, k_max + 1):
        hits = np.array([1.0 if any(r[:k]) else 0.0 for r in reps if len(r) >= k])
        if not len(hits):
            continue
        lo, hi = cluster_bootstrap_ci(hits, np.random.default_rng(seed))
        out[str(k)] = {"rate": float(hits.mean()), "ci95": [lo, hi], "n_defects": int(len(hits))}
    return out


def _clean_outputs(rows: list[dict], root: str) -> dict:
    """{defect_id: the pre-injection output of its stage}, from the study dumps."""
    spec = importlib.util.spec_from_file_location(
        "inject_defects", Path(__file__).resolve().parents[1] / "inject_defects.py")
    inj = importlib.util.module_from_spec(spec)
    sys.modules["inject_defects"] = inj
    spec.loader.exec_module(inj)
    dirs = {Path(d).name: d for d in inj.base_dirs(root)}
    out = {}
    for r in rows:
        trials = r.get("trials") or []
        if not trials:
            continue
        base = inj.state_from_dump(dirs[r["defect_id"].rsplit(":", 1)[0]])
        out[r["defect_id"]] = base.get(inj.OUTPUT_KEY[trials[0]["stage"]])
    return out


def analyse_warm(rows: list[dict], core_rows: list[dict] | None = None,
                 seed: int = DEFAULT_SEED, root: str | None = None) -> dict:
    """Section 0.1 A7: the warm-resample cell. Exploratory.

    Three reads, fixed in the amendment before the pass ran: the A1 - A2 gap at
    temperature 1 beside the in-session gap at 0 (two gaps with CIs and their
    difference); how often a retry reproduces the clean output byte for byte at
    each temperature (the ceiling mechanism); and A3's best-of-k at temperature
    1 against A1's single shot at 0, with tokens per trial (the equal-budget
    baseline plan D2 requires).
    """
    trials, excluded = usable_trials(rows)
    cm = factor_cells(trials, warm_level, arm=None)
    tokens = defaultdict(list)
    multi = Counter()
    for t in trials:
        tokens[warm_level(t)].append(t.get("total_tokens") or 0)
        if (t.get("attempts_made") or 0) > 1:
            multi[warm_level(t)] += 1
    trials_sa, _ = usable_trials(rows, drop_multi_attempt=True)
    cm_sa = factor_cells(trials_sa, warm_level, arm=None)
    contrasts = (("A1@T0", "A2@T0"), ("A1@T1", "A2@T1"), ("A1@T1", "A1@T0"),
                 ("A2@T1", "A2@T0"))
    out = {
        "provenance": {
            "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "seed": seed, "n_boot": N_BOOT, "trials_usable": len(trials),
            "exclusions": dict(excluded),
            "served_models": dict(Counter(m for r in rows for t in r.get("trials", [])
                                          for m in (t.get("served_models") or []))),
            "total_tokens": int(sum(t.get("total_tokens") or 0 for t in trials)),
        },
        "rates": {lv: _rate_ci(cm, lv, seed) for lv in WARM_LEVELS},
        "contrasts": {f"{a}-{b}": contrast(cm, a, b, seed) for a, b in contrasts},
        "gap_T1_minus_gap_T0": _gap_difference(cm, "A1@T1", "A2@T1", "A1@T0", "A2@T0", seed),
        "A3_best_of_k_T1": best_of_k(cm, "A3@T1", 3, seed),
        "mean_tokens_per_trial": {lv: float(np.mean(v)) for lv, v in sorted(tokens.items())},
        "outcome_classes": {f"{lv}|{o}": n for (lv, o), n in sorted(
            Counter((warm_level(t), outcome_class(t)) for t in trials).items())},
        "multi_attempt_trials_by_level": {lv: multi.get(lv, 0) for lv in WARM_LEVELS},
        "without_multi_attempt_trials": {
            "rates": {lv: _rate_ci(cm_sa, lv, seed) for lv in WARM_LEVELS},
            "contrasts": {f"{a}-{b}": contrast(cm_sa, a, b, seed) for a, b in contrasts},
        },
    }
    if root is not None:
        clean = _clean_outputs(rows, root)
        canon = lambda o: json.dumps(o, sort_keys=True, ensure_ascii=False)
        same, n = Counter(), Counter()
        for t in trials:
            if t["defect_id"] in clean:
                n[warm_level(t)] += 1
                same[warm_level(t)] += canon(t.get("retried_output")) == canon(clean[t["defect_id"]])
        out["byte_identical_to_clean"] = {
            lv: {"identical": same[lv], "trials": n[lv],
                 "share": same[lv] / n[lv] if n[lv] else None} for lv in WARM_LEVELS}
    if core_rows is not None:
        rerun = [t for t in trials if float(t.get("temperature", 0.0)) == 0.0]
        core = [t for t in usable_trials(core_rows)[0] if t["arm"] in ("A1", "A2")]
        out["drift_vs_core"] = _drift(rerun, core)
    return out


TIER1_ARMS = ("A1", "A2", "A3")


def analyse_c7(rows: list[dict], core_rows: list[dict] | None = None,
               seed: int = DEFAULT_SEED, root: str | None = None) -> dict:
    """A10 exploratory replication; rep 0 is primary, repeats measure stability."""
    usable, excluded = usable_trials(rows)
    trials = [t for t in usable if t.get("rep", 0) == 0]
    planned = {(d, a) for r in rows for t in r.get("trials", [])
               if t.get("rep", 0) == 0 for d, a in [(t["defect_id"], t["arm"])]}
    cm = cells(trials, planned=planned)
    single = [t for t in trials if t.get("attempts_made", 1) == 1]
    repeats = defaultdict(list)
    for t in usable:
        repeats[(t["defect_id"], t["arm"])].append(t)
    stability = {}
    for arm in ("A1", "A2"):
        pairs = [sorted(ts, key=lambda t: t["rep"]) for (d, a), ts in repeats.items()
                 if a == arm and len(ts) == 2]
        # Compare every successful call's raw output, including any schema correction.
        hashes = lambda t: [c["raw_sha256"] for c in t.get("local_calls", [])
                            if c.get("status") == "ok"]
        identical = sum(bool(hashes(a)) and hashes(a) == hashes(b) for a, b in pairs)
        stability[arm] = {"pairs": len(pairs), "identical_raw_call_sequences": identical,
                          "pairs_planned": sum(sum(t.get("arm") == arm for t in r.get("trials", [])) == 2
                                               for r in rows),
                          "same_outcome": sum(outcome_class(a) == outcome_class(b) for a, b in pairs),
                          "share_identical": identical / len(pairs) if pairs else None}
    out = {
        "provenance": {"script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                       "seed": seed, "n_boot": N_BOOT, "exploratory": True,
                       "trials_usable": len(usable), "first_draw_trials_usable": len(trials),
                       "exclusions": dict(excluded),
                       "served_models": dict(Counter(m for t in usable for m in t.get("served_models", []))),
                       "total_tokens": sum(t.get("total_tokens") or 0 for t in usable)},
        "A1_minus_A2": contrast(cm, "A1", "A2", seed),
        "rates": {a: _rate_ci(cm, a, seed) for a in ("A1", "A2", "A3")},
        "by_operator": rates_by(trials, lambda t: t["operator"]),
        "by_stage": rates_by(trials, lambda t: t["stage"]),
        "outcome_classes": {f"{a}|{o}": n for (a, o), n in sorted(
            Counter((t["arm"], outcome_class(t)) for t in trials).items())},
        "multi_attempt_first_draws": dict(Counter(t["arm"] for t in trials
                                                  if t.get("attempts_made", 1) > 1)),
        "without_multi_attempt_trials": {
            "A1_minus_A2": contrast(cells(single, planned=planned), "A1", "A2", seed),
            "rates": {a: _rate_ci(cells(single), a, seed) for a in ("A1", "A2", "A3")}},
        "repeat_stability": stability,
        "runtime_context_failures": sum("context_overflow" in (t.get("error_detail") or "")
                                        for r in rows for t in r.get("trials", [])),
        "mean_seconds_by_arm": {a: float(np.mean([t["wall_clock_s"] for t in usable
                                                   if t["arm"] == a and "wall_clock_s" in t]))
                                for a in ("A1", "A2", "A3")
                                if any(t["arm"] == a and "wall_clock_s" in t for t in usable)},
        "collateral": _collateral(trials),
    }
    if root is not None:
        clean = _clean_outputs(rows, root)
        canon = lambda o: json.dumps(o, sort_keys=True, ensure_ascii=False)
        out["identical_to_clean"] = {}
        for arm in ("A1", "A2", "A3"):
            subset = [t for t in trials if t["arm"] == arm and t["defect_id"] in clean]
            hits = sum(canon(t.get("retried_output")) == canon(clean[t["defect_id"]]) for t in subset)
            out["identical_to_clean"][arm] = {"trials": len(subset), "identical": hits,
                                             "share": hits / len(subset) if subset else None}
    if core_rows is not None:
        core = usable_trials(core_rows)[0]
        local_ids = {t["defect_id"] for t in trials}
        matched_core = [t for t in core if t["defect_id"] in local_ids]
        core_cm = cells(matched_core)
        out["paired_with_gemini"] = {}
        for arm in ("A1", "A2", "A3"):
            ids = sorted(d for d, a in cm if a == arm and cm[(d, a)] and core_cm.get((d, a)))
            vals = np.array([np.mean(cm[(d, arm)]) - np.mean(core_cm[(d, arm)]) for d in ids])
            ci = cluster_bootstrap_ci(vals, np.random.default_rng(seed)) if len(vals) else (None, None)
            out["paired_with_gemini"][arm] = {
                "n_defects": len(ids), "local_minus_gemini": float(vals.mean()) if len(vals) else None,
                "ci95": list(ci),
                "local_rate": float(np.mean([np.mean(cm[(d, arm)]) for d in ids])) if ids else None,
                "gemini_rate": float(np.mean([np.mean(core_cm[(d, arm)]) for d in ids])) if ids else None}
    return out


def _cell_bootstrap(per_defect: dict, cell_of: dict, seed: int, n_boot: int = N_BOOT):
    """Percentile CI of a mean over defects, resampling business x stage cells.

    Tier-1 defects nest in their cell (section 2.2), so the resampling unit is
    the cell; a bootstrap over defects would treat neighbours as independent.
    """
    cells = sorted({cell_of[d] for d in per_defect})
    by_cell = {c: [per_defect[d] for d in per_defect if cell_of[d] == c] for c in cells}
    rng = np.random.default_rng(seed)
    boot = []
    for _ in range(n_boot):
        pick = rng.integers(0, len(cells), size=len(cells))
        vals = [v for i in pick for v in by_cell[cells[i]]]
        boot.append(np.mean(vals))
    lo, hi = np.percentile(boot, [2.5, 97.5])
    return [float(lo), float(hi)]


def analyse_tier1(rows: list[dict], seed: int = DEFAULT_SEED) -> dict:
    """Section 0.1 A8: the production retry on real defects. Descriptive only.

    No hypothesis test is run (plan section 5, Tier 1: MDE about 31 pp, and a
    cluster bootstrap with few cells over-rejects). Rates are defect-level
    means of the repetitions; intervals resample business x stage cells.
    """
    usable = [t for r in rows for t in r.get("trials", []) if t.get("status") == "ok"]
    excluded = Counter(t.get("status") for r in rows for t in r.get("trials", [])
                       if t.get("status") != "ok")
    cell_of = {t["defect_id"]: t["cell"] for t in usable}

    def per_arm(field: str, arm: str, only=None) -> dict:
        reps: dict = defaultdict(list)
        for t in usable:
            if t["arm"] != arm or t.get(field) is None:
                continue
            if only is not None and not only(t):
                continue
            reps[t["defect_id"]].append(1.0 if t[field] else 0.0)
        per_defect = {d: float(np.mean(v)) for d, v in reps.items()}
        if not per_defect:
            return {"n_defects": 0}
        return {"rate": float(np.mean(list(per_defect.values()))),
                "ci95_cells": _cell_bootstrap(per_defect, cell_of, seed),
                "n_defects": len(per_defect),
                "n_cells": len({cell_of[d] for d in per_defect})}

    trace = lambda t: "untraceable_recommendation" in (t.get("classes") or [])
    return {
        "provenance": {
            "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "seed": seed, "n_boot": N_BOOT, "trials_usable": len(usable),
            "exclusions": dict(excluded),
            "served_models": dict(Counter(m for r in rows for t in r.get("trials", [])
                                          for m in (t.get("served_models") or []))),
            "total_tokens": int(sum(t.get("total_tokens") or 0 for t in usable)),
        },
        "note": "descriptive only: no hypothesis test (plan section 5, Tier 1)",
        "accepted": {a: per_arm("accepted", a) for a in TIER1_ARMS},
        "target_resolved": {a: per_arm("target_resolved", a) for a in TIER1_ARMS},
        "trace_class_production": {a: per_arm("accepted", a, trace) for a in TIER1_ARMS},
        "trace_class_content_words": {a: per_arm("trace_resolved_content", a, trace)
                                      for a in TIER1_ARMS},
        "same_as_original_output": {a: per_arm("same_as_original", a) for a in TIER1_ARMS},
        "by_stage_accepted": {
            f"{s}|{a}": per_arm("accepted", a, lambda t, s=s: t["stage"] == s)
            for s in sorted({t["stage"] for t in usable}) for a in TIER1_ARMS},
        "multi_attempt_trials_by_arm": dict(Counter(
            t["arm"] for t in usable if (t.get("attempts_made") or 0) > 1)),
    }


# ── O5 matcher sensitivity (section 2.3, D22) ────────────────────────────────


O5_CRITERIA = ("content_jaccard_0.10", "content_jaccard_0.05", "containment_gt_0",
               "production_difflib")


def o5_class_without_firing(detail: dict) -> str:
    """The outcome class a trial gets when the trace check does *not* fire.

    Steps 2-4 of section 2.3 depend only on the item, never on the matcher, so
    they can be re-derived from what the scorer stored: gone -> ``deleted``,
    present but not restored -> ``replaced``, else ``repaired``.
    """
    if detail.get("can_delete") and detail.get("pre_item") is not None \
            and not detail.get("item_located"):
        return "deleted"
    if detail.get("can_replace") and not detail.get("item_restored"):
        return "replaced"
    return "repaired"


def analyse_o5_sensitivity(rows: list[dict], root: str = "out_study",
                           seed: int = DEFAULT_SEED) -> dict:
    """Section 2.3: O5 re-scored under every trace criterion the document names.

    The primary is the content-word trace (Jaccard >= 0.10); the production
    difflib verdict is the named secondary; containment > 0 and Jaccard >= 0.05
    are the named sensitivities. Each criterion is recomputed from the retried
    output against the same upstream candidates, the outcome class re-derived,
    and the primary A1 - A2 contrast re-estimated with O5 scored that way.
    """
    spec = importlib.util.spec_from_file_location(
        "inject_defects", Path(__file__).resolve().parents[1] / "inject_defects.py")
    inj = importlib.util.module_from_spec(spec)
    sys.modules["inject_defects"] = inj
    spec.loader.exec_module(inj)
    from app.core import supervision  # noqa: PLC0415 -- path set by inject_defects
    cm_mod = _content_match_module()
    dirs = {Path(d).name: d for d in inj.base_dirs(root)}

    def fires(criterion: str, issues: list[str], candidates: list[str], state: dict) -> bool:
        if criterion == "content_jaccard_0.10":
            return bool(cm_mod.untraceable(issues, candidates, threshold=0.10))
        if criterion == "content_jaccard_0.05":
            return bool(cm_mod.untraceable(issues, candidates, threshold=0.05))
        if criterion == "containment_gt_0":
            return any(max((cm_mod.containment(i, c) for c in candidates if c), default=0.0) == 0.0
                       for i in issues)
        facts = supervision.measure("strategy_agent", state)
        return bool(facts.get("untraceable_issues"))

    reclassified: dict = {c: {} for c in O5_CRITERIA}
    primary_matches_stored = 0
    n = 0
    for r in rows:
        if r.get("operator") != "O5" or not r.get("trials"):
            continue
        base = inj.state_from_dump(dirs[r["defect_id"].rsplit(":", 1)[0]])
        for t in r["trials"]:
            if t.get("status") != "ok":
                continue
            state = dict(base)
            state["strategy_output"] = t.get("retried_output")
            state["report_output"] = None
            issues = [str(x.get("issue") or "") for x in
                      ((t.get("retried_output") or {}).get("recommendations") or [])]
            candidates = inj._trace_candidates(state)
            detail = t["outcome"]["detail"]
            for crit in O5_CRITERIA:
                cls = "unrepaired" if fires(crit, issues, candidates, state) \
                    else o5_class_without_firing(detail)
                reclassified[crit][(t["defect_id"], t["arm"], t["rep"])] = cls
            n += 1
            primary_matches_stored += \
                reclassified["content_jaccard_0.10"][(t["defect_id"], t["arm"], t["rep"])] \
                == t["outcome"]["outcome"]

    trials, _ = usable_trials(rows)
    planned = planned_cells(rows)
    out = {"o5_trials": n,
           "primary_reproduces_stored_outcomes": f"{primary_matches_stored}/{n}",
           "by_criterion": {}}
    for crit in O5_CRITERIA:
        relabelled = []
        for t in trials:
            key = (t["defect_id"], t["arm"], t["rep"])
            if t["operator"] == "O5" and key in reclassified[crit]:
                t = {**t, "outcome": {**t["outcome"], "outcome": reclassified[crit][key]}}
            relabelled.append(t)
        o5_rates = rates_by([t for t in relabelled if t["operator"] == "O5"], lambda t: "O5")
        out["by_criterion"][crit] = {
            "o5_class_counts": {
                f"{arm}|{cls}": cnt for (arm, cls), cnt in sorted(Counter(
                    (k[1], v) for k, v in reclassified[crit].items()).items())},
            "o5_rates": o5_rates,
            "primary_A1_minus_A2": contrast(cells(relabelled, planned=planned), "A1", "A2", seed),
        }
    return out


# ── downstream propagation (section 0.1 A9) ──────────────────────────────────


DOWNSTREAM_CONDITIONS = ("clean", "unrepaired", "A1", "A2")


def _content_match_module():
    spec = importlib.util.spec_from_file_location(
        "content_match", Path(__file__).resolve().parent / "content_match.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def report_items(report: dict | None) -> list[str]:
    """A final report's structured claims: its root causes and recommendation issues."""
    report = report or {}
    return ([str(rc.get("cause") or "") for rc in report.get("root_causes") or []]
            + [str(r.get("issue") or "") for r in report.get("recommendations") or []])


def content_divergence(reference: list[str], other: list[str], cm=None) -> float | None:
    """Share of the reference report's claims with no content-word partner in ``other``.

    Greedy one-to-one matching at the D24 identity threshold (content-word
    Jaccard >= ANCHOR_JACCARD), the matcher calibrated for "the same item" after
    the production difflib matcher was shown blind to paraphrase (D22, D24).
    """
    cm = cm or _content_match_module()
    if not reference:
        return None
    remaining = [o for o in other if o]
    hits = 0
    for item in reference:
        best, best_score = None, cm.ANCHOR_JACCARD
        for cand in remaining:
            score = cm.jaccard(item, cand)
            if score >= best_score:
                best, best_score = cand, score
        if best is not None:
            remaining.remove(best)
            hits += 1
    return 1.0 - hits / len(reference)


def _paired(values_a: dict, values_b: dict, seed: int) -> dict:
    ids = sorted(set(values_a) & set(values_b))
    diff = np.array([values_a[d] - values_b[d] for d in ids])
    lo, hi = cluster_bootstrap_ci(diff, np.random.default_rng(seed))
    return {"n_defects": len(ids), "estimate": float(diff.mean()) if len(ids) else None,
            "ci95": [lo, hi]}


def analyse_downstream(rows: list[dict], seed: int = DEFAULT_SEED) -> dict:
    """Section 0.1 A9: pipeline-level outcomes of clean, unrepaired and repaired outputs.

    Three endpoints, fixed in the amendment before the pass ran:
    E1 ``accepted`` -- every downstream stage passes the supervisor; E2 (O5
    only) -- the injected issue survives into the final report; E3 --
    divergence of the final report's claims from the clean run's, against the
    clean-vs-clean divergence measured in the same session (the noise floor).
    """
    cm_mod = _content_match_module()
    accepted: dict = {c: {} for c in DOWNSTREAM_CONDITIONS}
    diverg: dict = {c: {} for c in ("clean_rerun", "unrepaired", "A1", "A2")}
    e2: dict = {c: {} for c in DOWNSTREAM_CONDITIONS}
    coupling = Counter()
    excluded = Counter()
    operator_of = {}
    for r in rows:
        conds = {}
        for c in r.get("conditions", []):
            if c.get("status") != "ok":
                excluded[c.get("status")] += 1
                continue
            conds[(c["condition"], c["rep"])] = c
        d = r["defect_id"]
        operator_of[d] = r.get("operator")
        clean0 = conds.get(("clean", 0))
        ref = report_items(clean0.get("final_report")) if clean0 else []
        for name in DOWNSTREAM_CONDITIONS:
            c = conds.get((name, 0))
            if c is None:
                continue
            accepted[name][d] = 1.0 if c["accepted"] else 0.0
            if r.get("injected_issue"):
                issues = [str(x.get("issue") or "") for x in
                          ((c.get("final_report") or {}).get("recommendations") or [])]
                e2[name][d] = 1.0 if cm_mod.best_jaccard(r["injected_issue"], issues) \
                    >= cm_mod.ANCHOR_JACCARD else 0.0
        if clean0 is not None and ref:
            for key, cond in (("clean_rerun", ("clean", 1)), ("unrepaired", ("unrepaired", 0)),
                              ("A1", ("A1", 0)), ("A2", ("A2", 0))):
                c = conds.get(cond)
                if c is not None:
                    diverg[key][d] = content_divergence(ref, report_items(c.get("final_report")), cm_mod)
        for name in ("A1", "A2"):
            c = conds.get((name, 0))
            if c is not None and c.get("core_outcome"):
                coupling[(name, c["core_outcome"] == "repaired", bool(c["accepted"]))] += 1

    def rate(values: dict) -> dict:
        if not values:
            return {"n_defects": 0}
        arr = np.array(list(values.values()))
        lo, hi = cluster_bootstrap_ci(arr, np.random.default_rng(seed))
        return {"rate": float(arr.mean()), "ci95": [lo, hi], "n_defects": len(arr)}

    def mean_div(values: dict) -> dict:
        vals = {k: v for k, v in values.items() if v is not None}
        if not vals:
            return {"n_defects": 0}
        arr = np.array(list(vals.values()))
        lo, hi = cluster_bootstrap_ci(arr, np.random.default_rng(seed))
        return {"mean": float(arr.mean()), "ci95": [lo, hi], "n_defects": len(arr)}

    div_clean = {k: v for k, v in diverg["clean_rerun"].items() if v is not None}
    return {
        "provenance": {
            "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "seed": seed, "n_boot": N_BOOT,
            "defects": len(rows), "exclusions": dict(excluded),
            "served_models": dict(Counter(m for r in rows for c in r.get("conditions", [])
                                          for m in (c.get("served_models") or []))),
            "total_tokens": int(sum(c.get("total_tokens") or 0 for r in rows
                                    for c in r.get("conditions", []))),
        },
        "E1_accepted": {c: rate(v) for c, v in accepted.items()},
        "E1_contrasts": {
            f"{a}-{b}": _paired(accepted[a], accepted[b], seed)
            for a, b in (("unrepaired", "clean"), ("A1", "unrepaired"), ("A2", "unrepaired"),
                         ("A1", "A2"), ("A1", "clean"))},
        "E2_injected_issue_in_final_report_O5": {c: rate(v) for c, v in e2.items()},
        "E3_divergence_from_clean": {c: mean_div(v) for c, v in diverg.items()},
        "E3_contrasts": {
            f"{a}-clean_rerun": _paired({k: v for k, v in diverg[a].items() if v is not None},
                                        div_clean, seed)
            for a in ("unrepaired", "A1", "A2")} | {
            "A1-unrepaired": _paired({k: v for k, v in diverg["A1"].items() if v is not None},
                                     {k: v for k, v in diverg["unrepaired"].items() if v is not None},
                                     seed),
            "A1-A2": _paired({k: v for k, v in diverg["A1"].items() if v is not None},
                             {k: v for k, v in diverg["A2"].items() if v is not None}, seed)},
        "E1_by_operator": {
            f"{op}|{c}": rate({d: v for d, v in accepted[c].items() if operator_of.get(d) == op})
            for op in sorted({o for o in operator_of.values() if o}) for c in DOWNSTREAM_CONDITIONS},
        "coupling_defect_level_vs_E1": {
            f"{arm}|core_repaired={rep}|accepted={acc}": n
            for (arm, rep, acc), n in sorted(coupling.items())},
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
    ap.add_argument("--cell", default="core",
                    choices=("core", "c1", "d19", "placement", "severity", "warm", "tier1",
                             "downstream", "o5sens", "c7"))
    ap.add_argument("--checkpoint", default=None,
                    help="defaults per --cell: out_study/T2, T2C1, T2D19, T2P, T2S or T2W")
    ap.add_argument("--root", default="out_study",
                    help="--cell warm: the study dumps, for the byte-identity read")
    ap.add_argument("--core-checkpoint", default="out_study/T2/checkpoint.jsonl",
                    help="c1/placement/severity: the core, for the serving-drift comparison")
    ap.add_argument("--json", default=None, help="write the full result here")
    ap.add_argument("--seed", type=int, default=DEFAULT_SEED)
    args = ap.parse_args()
    checkpoint = args.checkpoint or {
        "core": "out_study/T2", "c1": "out_study/T2C1", "d19": "out_study/T2D19",
        "placement": "out_study/T2P", "severity": "out_study/T2S", "warm": "out_study/T2W",
        "tier1": "out_study/T1", "downstream": "out_study/T2D", "o5sens": "out_study/T2",
        "c7": "out_study/T2L",
    }[args.cell] + "/checkpoint.jsonl"
    if args.cell == "core":
        res = analyse(load_rows(checkpoint), seed=args.seed)
        print_summary(res)
    else:
        core = load_rows(args.core_checkpoint) if Path(args.core_checkpoint).exists() else None
        if args.cell == "c1":
            res = analyse_c1(load_rows(checkpoint), core, seed=args.seed)
        elif args.cell == "placement":
            res = analyse_placement(load_rows(checkpoint), core, seed=args.seed)
        elif args.cell == "severity":
            res = analyse_severity(load_rows(checkpoint), core, seed=args.seed)
        elif args.cell == "warm":
            res = analyse_warm(load_rows(checkpoint), core, seed=args.seed, root=args.root)
        elif args.cell == "tier1":
            res = analyse_tier1(load_rows(checkpoint), seed=args.seed)
        elif args.cell == "c7":
            res = analyse_c7(load_rows(checkpoint), core, seed=args.seed, root=args.root)
        elif args.cell == "downstream":
            res = analyse_downstream(load_rows(checkpoint), seed=args.seed)
        elif args.cell == "o5sens":
            res = analyse_o5_sensitivity(load_rows(checkpoint), root=args.root, seed=args.seed)
            res["provenance"] = {
                "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                "seed": args.seed}
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
