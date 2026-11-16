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

Two reads are post hoc and labelled exploratory (``RESULTS.md`` section 4):
with ``--root`` (the study dumps), the share of retries identical to the clean
pre-injection output, and the number of distinct outputs each (defect, arm)
cell gave across its repetitions. Both compare outputs as canonical JSON
(sorted keys), as the warm and c7 cells do.

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


def ratio(cellmap: dict, num: str, den: str, seed: int, defects=None) -> dict:
    """Ratio of mean defect-level rates (section 3 item 2), CI over defects."""
    kept, dropped = paired(cellmap, num, den, defects)
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


def analyse(rows: list[dict], seed: int = DEFAULT_SEED, root: str | None = None) -> dict:
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

    out = {
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
    if root is not None:
        clean = _clean_outputs(rows, root)
        cm_copy = copy_cells(trials, clean, planned=planned)
        out["exploratory"] = {
            "note": "post hoc, not pre-specified (RESULTS.md section 4); outputs "
                    "compared as canonical JSON",
            "identical_to_clean": identity_to_clean(trials, clean),
            "copy_contrast_A1_minus_A2": contrast(cm_copy, "A1", "A2", seed),
            "repair_decomposition": compute_repair_decomposition(trials, clean),
            "distinct_outputs_per_cell": distinct_outputs(trials),
        }
    return out


def analyse_flashlite(rows: list[dict], seed: int = DEFAULT_SEED,
                      root: str = "out_study/FL") -> dict:
    """S5: one primary restoration test; repair remains exploratory.

    Unconditional means not conditioned on successful repair. Provider losses
    follow the frozen per-trial exclusions and strict-majority tie rule.
    """
    protocol = sys.modules.get("flashlite_protocol")
    if protocol is None:
        spec = importlib.util.spec_from_file_location(
            "flashlite_protocol", Path(__file__).resolve().parents[1] / "flashlite_protocol.py")
        protocol = importlib.util.module_from_spec(spec)
        sys.modules["flashlite_protocol"] = protocol
        spec.loader.exec_module(protocol)
    bases = protocol.validate_bases(root)
    model = "gemini-3.5-flash-lite"
    for row in rows:
        for trial in row.get("trials", []):
            if trial.get("reasoning_effort") is not None:
                raise ValueError("S5 reasoning_effort must be omitted (None), not 'none'")
            if trial.get("status") == "ok" and set(trial.get("served_models") or []) != {model}:
                raise ValueError("S5 successful trials must be served exclusively by " + model)
    trials, excluded = usable_trials(rows)
    single, excluded_single = usable_trials(rows, drop_multi_attempt=True)
    clean = _clean_outputs(rows, root)
    missing = {t["defect_id"] for t in trials if not isinstance(clean.get(t["defect_id"]), dict)}
    if missing:
        raise ValueError("Missing own-model clean reference for " + ", ".join(sorted(missing)))
    planned = planned_cells(rows)
    copy_map = copy_cells(trials, clean, planned=planned)
    repair_map = cells(trials, planned=planned)
    primary = contrast(copy_map, "A1", "A2", seed)
    lo, hi = primary.get("ci95", (None, None))
    positive = primary.get("estimate", 0.0) > 0
    excludes_zero = lo is not None and (lo > 0 or hi < 0)
    rejects = primary.get("mcnemar_p", 1.0) < ALPHA
    copied_trials = _copy_trials(trials, clean)
    strata = _strata(root)
    def over_a0(cellmap):
        result = ratio(cellmap, "A1", "A0", seed)
        if result.get("estimate") is None:
            result["ci95"] = [None, None]
            result["note"] = "undefined: no paired data or a zero A0 denominator"
        return result
    report = {
        "provenance": {
            "cell": "flashlite", "model": model, "reasoning_effort": None,
            "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "seed": seed, "n_boot": N_BOOT, "bases": bases,
            "trials_total": sum(len(r.get("trials", [])) for r in rows),
            "trials_usable": len(trials), "exclusions": dict(excluded),
            "total_tokens": sum(t.get("total_tokens") or 0 for r in rows for t in r.get("trials", [])),
        },
        "confirmatory": {
            "outcome": "unconditional canonical-JSON exact restoration",
            "unit": "defect; strictly more than half of usable repetitions for McNemar",
            "test": "two-sided exact McNemar", "alpha": ALPHA,
            "primary_A1_minus_A2": primary,
            "criterion": {"positive_estimate": bool(positive),
                          "two_sided_ci_excludes_zero": bool(excludes_zero),
                          "two_sided_mcnemar_rejects": bool(rejects)},
            "replicated": bool(positive and excludes_zero and rejects),
            "without_multi_attempt_trials": {
                "exclusions": dict(excluded_single),
                **contrast(copy_cells(single, clean, planned=planned), "A1", "A2", seed)},
        },
        "secondary_exploratory": {
            "repair_A1_minus_A2": contrast(repair_map, "A1", "A2", seed),
            "repair_A1_over_A0": over_a0(repair_map),
            "restoration_A1_over_A0": over_a0(copy_map),
            "restoration_A1_minus_A0": contrast(copy_map, "A1", "A0", seed),
            "restoration_A0_minus_A2": contrast(copy_map, "A0", "A2", seed),
            "restoration_by_arm": {a: _rate_ci(copy_map, a, seed) for a in ("A0", "A1", "A2", "A3")},
            "repair_by_operator": rates_by(trials, lambda t: t["operator"]),
            "restoration_by_operator": rates_by(copied_trials, lambda t: t["operator"]),
            "repair_by_review_stratum": rates_by(
                trials, lambda t: strata[t["defect_id"].rsplit(":", 1)[0]]),
            "restoration_by_review_stratum": rates_by(
                copied_trials, lambda t: strata[t["defect_id"].rsplit(":", 1)[0]]),
            "identity_to_clean": identity_to_clean(trials, clean),
            "repair_decomposition": compute_repair_decomposition(trials, clean),
        },
    }
    return report


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


THINKING_EFFORTS = ("none", "low", "medium", "high")
THINKING_BUDGETS = {"none": 0, "low": 1024, "medium": 8192, "high": 24576}
THINKING_LEVELS = tuple(f"{a}@{e}" for a in ("A1", "A2", "A3") for e in THINKING_EFFORTS)
THINKING_A0_EFFORTS = ("none", "high")  # S2b: the ends of the sweep


def thinking_level(t: dict) -> str:
    return f"{t['arm']}@{t.get('reasoning_effort') or 'default'}"


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
    cache = {}
    out = {}
    for r in rows:
        trials = r.get("trials") or []
        if not trials:
            continue
        biz_id = r["defect_id"].rsplit(":", 1)[0]
        if biz_id not in cache:
            cache[biz_id] = inj.state_from_dump(dirs[biz_id])
        base = cache[biz_id]
        out[r["defect_id"]] = base.get(inj.OUTPUT_KEY[trials[0]["stage"]])
    return out


def canonical(output) -> str:
    """An output as canonical JSON (sorted keys): the same identity the warm, c7
    and drift reads compare."""
    return json.dumps(output, sort_keys=True, ensure_ascii=False)


def trial_is_copy(trial: dict, clean: dict) -> bool:
    """True if trial's retried output is canonical-JSON identical to clean output."""
    did = trial.get("defect_id")
    if not did or did not in clean:
        return False
    return canonical(trial.get("retried_output")) == canonical(clean[did])


def copy_cells(trials: list[dict], clean: dict, planned: tuple[tuple[str, str], ...] = (),
               condition: str = "C0") -> dict:
    out: dict = defaultdict(list)
    for key in planned:
        out[key]
    for t in trials:
        if t.get("condition", "C0") != condition:
            continue
        if t.get("defect_id") in clean:
            out[(t["defect_id"], t["arm"])].append(1 if trial_is_copy(t, clean) else 0)
    return dict(out)


def _decompose_trial_list(trials: list[dict], clean: dict) -> dict:
    """Decompose a single list of trials into 3-way and 4-way categories."""
    trials_with_clean = [t for t in trials if t.get("defect_id") in clean]
    n = len(trials_with_clean)
    if n == 0:
        return {"trials": 0}

    n_copy = 0
    n_rewrite = 0
    n_replaced_deleted = 0
    n_unrepaired = 0

    for t in trials_with_clean:
        cls = outcome_class(t)
        is_copy = trial_is_copy(t, clean)
        if cls == "repaired":
            if is_copy:
                n_copy += 1
            else:
                n_rewrite += 1
        elif cls in ("replaced", "deleted"):
            n_replaced_deleted += 1
        else:
            n_unrepaired += 1

    n_repaired = n_copy + n_rewrite
    n_not_repaired = n_replaced_deleted + n_unrepaired
    n_non_copy = n - n_copy

    within_rewrite_rate = n_rewrite / n_non_copy if n_non_copy > 0 else None

    return {
        "trials": n,
        "3_way": {
            "repaired_copy": {"count": n_copy, "share": n_copy / n},
            "repaired_rewrite": {"count": n_rewrite, "share": n_rewrite / n},
            "not_repaired": {"count": n_not_repaired, "share": n_not_repaired / n},
        },
        "4_way": {
            "repaired_copy": {"count": n_copy, "share": n_copy / n},
            "repaired_rewrite": {"count": n_rewrite, "share": n_rewrite / n},
            "replaced_or_deleted": {"count": n_replaced_deleted, "share": n_replaced_deleted / n},
            "unrepaired": {"count": n_unrepaired, "share": n_unrepaired / n},
        },
        "total_repaired": {"count": n_repaired, "share": n_repaired / n},
        "within_rewrite": {
            "note": "descriptive only; non-identical subset subject to composition artefact",
            "repaired": n_rewrite,
            "trials": n_non_copy,
            "rate": within_rewrite_rate,
        },
    }


def compute_repair_decomposition(trials: list[dict], clean: dict) -> dict:
    """3-way and 4-way repair decomposition overall and by operator."""
    arms = sorted({t["arm"] for t in trials if t.get("defect_id") in clean})
    operators = sorted({t["operator"] for t in trials if t.get("operator")})

    overall = {}
    for arm in arms:
        ts = [t for t in trials if t["arm"] == arm]
        overall[arm] = _decompose_trial_list(ts, clean)

    by_operator = {}
    for op in operators:
        by_operator[op] = {}
        for arm in arms:
            ts = [t for t in trials if t.get("operator") == op and t["arm"] == arm]
            by_operator[op][arm] = _decompose_trial_list(ts, clean)

    return {
        "overall": overall,
        "by_operator": by_operator,
    }


def identity_to_clean(trials: list[dict], clean: dict) -> dict:
    """Per arm, the share of retries identical to the clean pre-injection output.

    The paper's "byte for byte" means this canonical-JSON identity. Trials whose
    defect has no clean output in ``clean`` are not counted.
    """
    same, n = Counter(), Counter()
    for t in trials:
        if t["defect_id"] in clean:
            n[t["arm"]] += 1
            same[t["arm"]] += canonical(t.get("retried_output")) == canonical(clean[t["defect_id"]])
    return {arm: {"identical": same[arm], "trials": n[arm], "share": same[arm] / n[arm]}
            for arm in sorted(n)}


def distinct_outputs(trials: list[dict], reps: int = 3) -> dict:
    """Per arm, how many distinct outputs each (defect, arm) cell gave.

    Only cells with all ``reps`` repetitions usable are counted, so a cell that
    lost a repetition cannot read as more stable than it was.
    """
    outputs = defaultdict(list)
    for t in trials:
        outputs[(t["defect_id"], t["arm"])].append(canonical(t.get("retried_output")))
    by_arm: dict = defaultdict(Counter)
    for (_, arm), outs in outputs.items():
        if len(outs) == reps:
            by_arm[arm][len(set(outs))] += 1
    return {arm: {"cells": sum(c.values()),
                  "by_distinct": {str(k): c[k] for k in range(1, reps + 1)},
                  "shares": {str(k): c[k] / sum(c.values()) for k in range(1, reps + 1)}}
            for arm, c in sorted(by_arm.items())}


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
        copy_trials = [{**t, "outcome": {"outcome": "repaired" if trial_is_copy(t, clean) else "unrepaired"}}
                       for t in trials if t.get("defect_id") in clean]
        cm_copy_warm = factor_cells(copy_trials, warm_level, arm=None)
        out["copy_contrast"] = {
            "A1@T0-A2@T0": contrast(cm_copy_warm, "A1@T0", "A2@T0", seed),
            "A1@T1-A2@T1": contrast(cm_copy_warm, "A1@T1", "A2@T1", seed),
        }
        decomp = compute_repair_decomposition(trials, clean)
        by_level_decomp = compute_repair_decomposition([{**t, "arm": warm_level(t)} for t in trials], clean)
        decomp["by_level"] = by_level_decomp["overall"]
        decomp["by_level_and_operator"] = by_level_decomp["by_operator"]
        out["repair_decomposition"] = decomp
    if core_rows is not None:
        rerun = [t for t in trials if float(t.get("temperature", 0.0)) == 0.0]
        core = [t for t in usable_trials(core_rows)[0] if t["arm"] in ("A1", "A2")]
        out["drift_vs_core"] = _drift(rerun, core)
    return out


TIER1_ARMS = ("A1", "A2", "A3")


def analyse_c7(rows: list[dict], core_rows: list[dict] | None = None,
               seed: int = DEFAULT_SEED, root: str | None = None) -> dict:
    """A11 exploratory replication: defect means over three completed draws."""
    usable, excluded = usable_trials(rows)
    trials = usable
    planned = planned_cells(rows)
    cm = cells(trials, planned=planned)
    single = [t for t in trials if t.get("attempts_made", 1) == 1]
    # A smaller model may exhaust schema correction. Distinguish that from an
    # infrastructure failure and report a conservative sensitivity, fixed in A10.
    failures = [t for r in rows for t in r.get("trials", []) if t.get("status") != "ok"]
    schema_failures = [t for t in failures if
                       (t.get("error_type") == "schema_validation_error" or
                        "context_overflow" in (t.get("error_detail") or ""))]
    conservative = trials + [{**t, "outcome": {"outcome": "unrepaired"}} for t in schema_failures]
    conservative_cm = cells(conservative, planned=planned)
    repeats = defaultdict(list)
    for t in usable:
        repeats[(t["defect_id"], t["arm"])].append(t)
    stability = {}
    for arm in ("A1", "A2"):
        complete = [sorted(ts, key=lambda t: t["rep"]) for (d, a), ts in repeats.items()
                    if a == arm and len(ts) == 3]
        # Compare every successful call's raw output, including any schema correction.
        hashes = lambda t: [c["raw_sha256"] for c in t.get("local_calls", [])
                            if c.get("status") == "ok"]
        identical = sum(all(hashes(t) for t in ts) and
                        len({tuple(hashes(t)) for t in ts}) == 1 for ts in complete)
        stability[arm] = {"cells_complete": len(complete), "identical_raw_call_sequences": identical,
                          "cells_planned": sum(sum(t.get("arm") == arm for t in r.get("trials", [])) == 3
                                               for r in rows),
                          "same_outcome": sum(len({outcome_class(t) for t in ts}) == 1 for ts in complete),
                          "share_identical": identical / len(complete) if complete else None}
    out = {
        "provenance": {"script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                       "seed": seed, "n_boot": N_BOOT, "exploratory": True,
                       "trials_usable": len(usable), "repetitions_planned": 3,
                       "exclusions": dict(excluded),
                       "served_models": dict(Counter(m for t in usable for m in t.get("served_models", []))),
                       "total_tokens": sum(t.get("total_tokens") or 0 for t in usable)},
        "A1_minus_A2": contrast(cm, "A1", "A2", seed),
        "rates": {a: _rate_ci(cm, a, seed) for a in ("A1", "A2", "A3")},
        "by_operator": rates_by(trials, lambda t: t["operator"]),
        "by_stage": rates_by(trials, lambda t: t["stage"]),
        "rates_by_severity": {
            group: {a: _rate_ci(cells([t for t in trials if t["operator"] in operators]), a, seed)
                    for a in ("A1", "A2", "A3")}
            for group, operators in (("O1", O1_CELL), ("severe", SEVERE_CELL))},
        "contrast_by_severity": {
            group: contrast(cells([t for t in trials if t["operator"] in operators]), "A1", "A2", seed)
            for group, operators in (("O1", O1_CELL), ("severe", SEVERE_CELL))},
        "failure_types": dict(Counter(t.get("error_type") or "unknown" for t in failures)),
        "schema_failure_sensitivity": {
            "failures_counted_unrepaired": len(schema_failures),
            "A1_minus_A2": contrast(conservative_cm, "A1", "A2", seed),
            "rates": {a: _rate_ci(conservative_cm, a, seed) for a in ("A1", "A2", "A3")}},
        "outcome_classes": {f"{a}|{o}": n for (a, o), n in sorted(
            Counter((t["arm"], outcome_class(t)) for t in trials).items())},
        "multi_attempt_trials": dict(Counter(t["arm"] for t in trials
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
        "first_draw_only": {
            "A1_minus_A2": contrast(cells([t for t in trials if t.get("rep", 0) == 0], planned=planned),
                                    "A1", "A2", seed)},
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
        cm_copy = copy_cells(trials, clean, planned=planned)
        out["copy_contrast_A1_minus_A2"] = contrast(cm_copy, "A1", "A2", seed)
        out["repair_decomposition"] = compute_repair_decomposition(trials, clean)
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


def analyse_thinking(rows: list[dict], core_rows: list[dict] | None = None,
                     seed: int = DEFAULT_SEED, root: str | None = None) -> dict:
    """Amendment A12: within-weights thinking-budget sweep (T2T).

    Sweep across reasoning_effort in ('none', 'low', 'medium', 'high') on gemini-2.5-flash.
    Evaluates rates per level, within-effort A1-A2 contrasts, cross-effort contrasts,
    gap differences against high, dose-response OLS trend test, tokens & latency,
    without-multi-attempt sensitivity, exact copy contrast, and repair decomposition.
    """
    usable, excluded = usable_trials(rows)
    trials = usable
    cm = factor_cells(trials, thinking_level, arm=None)
    single = [t for t in trials if t.get("attempts_made", 1) == 1]
    cm_sa = factor_cells(single, thinking_level, arm=None)

    present_levels = [lv for lv in THINKING_LEVELS if any(thinking_level(t) == lv for t in trials)]

    # Rates per level
    rates = {lv: _rate_ci(cm, lv, seed) for lv in present_levels}

    # Within-effort A1 - A2 contrasts
    within_contrasts = {
        f"A1@{e}-A2@{e}": contrast(cm, f"A1@{e}", f"A2@{e}", seed)
        for e in THINKING_EFFORTS
        if f"A1@{e}" in present_levels and f"A2@{e}" in present_levels
    }

    # Cross-effort contrasts for each arm (A1, A2, A3) comparing "none", "low", "medium" against "high"
    cross_contrasts = {}
    for arm in ("A1", "A2", "A3"):
        for e in ("none", "low", "medium"):
            lvl_e = f"{arm}@{e}"
            lvl_h = f"{arm}@high"
            if lvl_e in present_levels and lvl_h in present_levels:
                cross_contrasts[f"{lvl_e}-{lvl_h}"] = contrast(cm, lvl_e, lvl_h, seed)

    # Gap differences comparing A1@e - A2@e against A1@high - A2@high
    gap_differences = {}
    for e in ("none", "low", "medium"):
        if (f"A1@{e}" in present_levels and f"A2@{e}" in present_levels
                and "A1@high" in present_levels and "A2@high" in present_levels):
            gap_differences[f"gap_{e}_minus_gap_high"] = _gap_difference(
                cm, f"A1@{e}", f"A2@{e}", "A1@high", "A2@high", seed
            )

    # Dose-response trend test dose_response_A1_minus_A2
    # For each defect d in the 45-defect subset, let g_{d, e} = y_bar_{d, A1@e} - y_bar_{d, A2@e}
    # for e in (high, medium, low, none) mapped to rank x in (0, 1, 2, 3) and to -log2(1 + budget_e).
    def _dose_response_thinking(cell_map: dict) -> dict:
        defects = sorted({
            d for d, _ in cell_map
            if all((d, f"A1@{e}") in cell_map and (d, f"A2@{e}") in cell_map and cell_map[(d, f"A1@{e}")] and cell_map[(d, f"A2@{e}")]
                   for e in ("high", "medium", "low", "none"))
        })

        rank_x = np.array([0.0, 1.0, 2.0, 3.0])
        rank_x_centered = rank_x - rank_x.mean()
        rank_ss = np.sum(rank_x_centered ** 2)

        log_x = np.array([-np.log2(1.0 + THINKING_BUDGETS[e]) for e in ("high", "medium", "low", "none")])
        log_x_centered = log_x - log_x.mean()
        log_ss = np.sum(log_x_centered ** 2)

        rank_slopes_list = []
        log_slopes_list = []
        for d in defects:
            g_de = np.array([
                float(np.mean(cell_map[(d, f"A1@{e}")]) - np.mean(cell_map[(d, f"A2@{e}")]))
                for e in ("high", "medium", "low", "none")
            ])
            beta_rank = float(np.sum(rank_x_centered * g_de) / rank_ss) if rank_ss > 0 else 0.0
            beta_log = float(np.sum(log_x_centered * g_de) / log_ss) if log_ss > 0 else 0.0
            rank_slopes_list.append(beta_rank)
            log_slopes_list.append(beta_log)

        rank_slopes_arr = np.array(rank_slopes_list)
        log_slopes_arr = np.array(log_slopes_list)
        rng = np.random.default_rng(seed)
        ci_rank = cluster_bootstrap_ci(rank_slopes_arr, rng) if len(rank_slopes_arr) else (None, None)
        ci_log = cluster_bootstrap_ci(log_slopes_arr, rng) if len(log_slopes_arr) else (None, None)

        return {
            "n_defects": len(defects),
            "mean_slope_rank": float(rank_slopes_arr.mean()) if len(rank_slopes_arr) else None,
            "ci95_rank": list(ci_rank),
            "mean_slope_neg_log2_budget": float(log_slopes_arr.mean()) if len(log_slopes_arr) else None,
            "ci95_neg_log2_budget": list(ci_log),
            "by_rank": {
                "n_defects": len(defects),
                "mean_slope": float(rank_slopes_arr.mean()) if len(rank_slopes_arr) else None,
                "ci95": list(ci_rank),
            },
            "by_neg_log2_budget": {
                "n_defects": len(defects),
                "mean_slope": float(log_slopes_arr.mean()) if len(log_slopes_arr) else None,
                "ci95": list(ci_log),
            },
        }

    dose_response = _dose_response_thinking(cm)

    # Token & latency metrics by level
    mean_tokens = {}
    mean_thinking_tokens = {}
    mean_completion_tokens = {}
    mean_seconds = {}
    for lv in present_levels:
        matching = [t for t in trials if thinking_level(t) == lv]
        toks = [t["total_tokens"] for t in matching if t.get("total_tokens") is not None]
        th_toks = [t["thinking_tokens"] for t in matching if t.get("thinking_tokens") is not None]
        comp_toks = [t["completion_tokens"] for t in matching if t.get("completion_tokens") is not None]
        secs = [t["wall_clock_s"] for t in matching if t.get("wall_clock_s") is not None]
        mean_tokens[lv] = float(np.mean(toks)) if toks else None
        mean_thinking_tokens[lv] = float(np.mean(th_toks)) if th_toks else None
        mean_completion_tokens[lv] = float(np.mean(comp_toks)) if comp_toks else None
        mean_seconds[lv] = float(np.mean(secs)) if secs else None

    # Token metrics by effort
    mean_thinking_by_effort = {}
    for e in THINKING_EFFORTS:
        th_toks_e = [t["thinking_tokens"] for t in trials
                     if (t.get("reasoning_effort") or "default") == e and t.get("thinking_tokens") is not None]
        mean_thinking_by_effort[e] = float(np.mean(th_toks_e)) if th_toks_e else None

    # without_multi_attempt_trials
    rates_sa = {lv: _rate_ci(cm_sa, lv, seed) for lv in present_levels if any(thinking_level(t) == lv for t in single)}
    contrasts_sa = {
        f"A1@{e}-A2@{e}": contrast(cm_sa, f"A1@{e}", f"A2@{e}", seed)
        for e in THINKING_EFFORTS
        if any(thinking_level(t) == f"A1@{e}" for t in single) and any(thinking_level(t) == f"A2@{e}" for t in single)
    }

    multi_count = Counter(thinking_level(t) for t in trials if (t.get("attempts_made") or 0) > 1)

    out = {
        "provenance": {
            "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "seed": seed, "n_boot": N_BOOT, "prospective": True,
            "cell": "thinking",
            "trials_usable": len(usable),
            "exclusions": dict(excluded),
            "served_models": dict(Counter(m for t in usable for m in t.get("served_models", []))),
            "total_tokens": sum(t.get("total_tokens") or 0 for t in usable),
        },
        "rates": rates,
        "within_effort_contrasts": within_contrasts,
        "cross_effort_contrasts": cross_contrasts,
        "contrasts": {**within_contrasts, **cross_contrasts},
        "gap_differences": gap_differences,
        "dose_response_A1_minus_A2": dose_response,
        "mean_tokens_per_trial": mean_tokens,
        "mean_thinking_tokens_per_trial": mean_thinking_tokens,
        "mean_completion_tokens_per_trial": mean_completion_tokens,
        "mean_seconds_per_trial": mean_seconds,
        "mean_thinking_tokens_by_effort": mean_thinking_by_effort,
        "multi_attempt_trials_by_level": {lv: multi_count.get(lv, 0) for lv in present_levels},
        "without_multi_attempt_trials": {
            "rates": rates_sa,
            "within_effort_contrasts": contrasts_sa,
            "contrasts": contrasts_sa,
        },
        "outcome_classes": {f"{lv}|{o}": n for (lv, o), n in sorted(
            Counter((thinking_level(t), outcome_class(t)) for t in trials).items())},
        "collateral": _collateral(trials),
    }

    if root is not None:
        clean = _clean_outputs(rows, root)
        canon = lambda o: json.dumps(o, sort_keys=True, ensure_ascii=False)
        same, n_tot = Counter(), Counter()
        for t in trials:
            if t["defect_id"] in clean:
                lv = thinking_level(t)
                n_tot[lv] += 1
                same[lv] += canon(t.get("retried_output")) == canon(clean[t["defect_id"]])
        out["byte_identical_to_clean"] = {
            lv: {"identical": same[lv], "trials": n_tot[lv],
                 "share": same[lv] / n_tot[lv] if n_tot[lv] else None}
            for lv in present_levels
        }
        copy_trials = [{**t, "outcome": {"outcome": "repaired" if trial_is_copy(t, clean) else "unrepaired"}}
                       for t in trials if t.get("defect_id") in clean]
        cm_copy_thinking = factor_cells(copy_trials, thinking_level, arm=None)
        out["copy_contrast"] = {
            f"A1@{e}-A2@{e}": contrast(cm_copy_thinking, f"A1@{e}", f"A2@{e}", seed)
            for e in THINKING_EFFORTS
            if f"A1@{e}" in present_levels and f"A2@{e}" in present_levels
        }
        copy_gap_differences = {}
        for e in ("none", "low", "medium"):
            if (f"A1@{e}" in present_levels and f"A2@{e}" in present_levels
                    and "A1@high" in present_levels and "A2@high" in present_levels):
                copy_gap_differences[f"gap_{e}_minus_gap_high"] = _gap_difference(
                    cm_copy_thinking, f"A1@{e}", f"A2@{e}", "A1@high", "A2@high", seed
                )
        out["copy_gap_differences"] = copy_gap_differences
        out["dose_response_copy_A1_minus_A2"] = _dose_response_thinking(cm_copy_thinking)
        decomp = compute_repair_decomposition(trials, clean)
        by_level_decomp = compute_repair_decomposition(
            [{**t, "arm": thinking_level(t)} for t in trials], clean
        )
        decomp["by_level"] = by_level_decomp["overall"]
        decomp["by_level_and_operator"] = by_level_decomp["by_operator"]
        out["repair_decomposition"] = decomp

    if core_rows is not None:
        rerun_none = [t for t in trials if (t.get("reasoning_effort") or "default") in ("none", "default") and t["arm"] in ("A1", "A2")]
        rerun_high = [t for t in trials if t.get("reasoning_effort") == "high" and t["arm"] in ("A1", "A2")]
        core = [t for t in usable_trials(core_rows)[0] if t["arm"] in ("A1", "A2")]
        # §0.1 A12 item 5: Serving drift compares in-pass unthought / baseline runs vs frozen core.
        out["drift_vs_core"] = _drift(rerun_none if rerun_none else rerun_high, core)
        out["drift_vs_core_none"] = _drift(rerun_none, core)
        out["drift_vs_core_high"] = _drift(rerun_high, core)

    return out


# -- S2: completing the A0 ceiling (SUPERVISOR_FEEDBACK_2026-11-13 section 5) --
#
# Both cells run in a later session than the trials they are joined to, so every
# read is labelled by where its arms came from. The r = 1 in-session A1 anchor is
# kept apart from the earlier A1 under its own arm name ("A1anchor") so that it
# can never be pooled into the 3-rep A1 by accident.

ANCHOR = "A1anchor"


def _relabel_anchor(trials: list[dict]) -> list[dict]:
    return [{**t, "arm": ANCHOR} if t["arm"] == "A1" else t for t in trials]


def _strata(root: str) -> dict:
    """{business dir name: review-count stratum}, from each dump's _summary.json."""
    spec = importlib.util.spec_from_file_location(
        "inject_defects", Path(__file__).resolve().parents[1] / "inject_defects.py")
    inj = importlib.util.module_from_spec(spec)
    sys.modules["inject_defects"] = inj
    spec.loader.exec_module(inj)
    out = {}
    for d in inj.base_dirs(root):
        summary = Path(d) / "_summary.json"
        if summary.exists():
            out[Path(d).name] = json.loads(summary.read_text(encoding="utf-8")).get("stratum")
    return out


def _copy_trials(trials: list[dict], clean: dict) -> list[dict]:
    """Trials re-scored on exact restoration: 'repaired' iff identical to clean."""
    return [{**t, "outcome": {"outcome": "repaired" if trial_is_copy(t, clean) else "unrepaired"}}
            for t in trials if t.get("defect_id") in clean]


def share_of_gap(cm: dict, a0: str, a1: str, a2: str, seed: int) -> dict:
    """(A1 - A2) / (A0 - A2) on defects carrying all three, defect bootstrap.

    Reported only when the CI of A0 - A2 lies wholly above 0 (A13, as clarified
    by its 2026-11-14 note). If the CI includes 0 the denominator can sit near
    zero and the ratio is unstable, so it is withheld. If the CI lies wholly
    below 0, A0 restores less often than A2: there is no gap to close and the
    ratio is not applicable. Its literal value is kept under
    ``literal_rule_value`` for the record, never as ``estimate``.
    """
    ids = sorted(d for d in {d for d, _ in cm}
                 if all(cm.get((d, lv)) for lv in (a0, a1, a2)))
    if not ids:
        return {"reported": False, "reason": "no defect carries all three arms", "n_defects": 0}
    m = {lv: np.array([np.mean(cm[(d, lv)]) for d in ids]) for lv in (a0, a1, a2)}
    den = m[a0] - m[a2]
    rng = np.random.default_rng(seed)
    lo, hi = cluster_bootstrap_ci(den, rng)
    base = {"n_defects": len(ids), "A0_minus_A2": float(den.mean()),
            "A0_minus_A2_ci95": [lo, hi]}
    if not (lo is not None and (lo > 0 or hi < 0)):
        return {**base, "reported": False, "reason": "CI of A0 - A2 includes 0"}
    num = m[a1] - m[a2]
    idx = rng.integers(0, len(ids), size=(N_BOOT, len(ids)))
    nb, db = num[idx].mean(axis=1), den[idx].mean(axis=1)
    ok = db != 0
    blo, bhi = np.percentile(nb[ok] / db[ok], [2.5, 97.5])
    value = {"estimate": float(num.mean() / den.mean()), "ci95": [float(blo), float(bhi)]}
    if hi < 0:
        return {**base, "reported": False, "applicable": False,
                "reason": "not applicable: A0 below A2 (CI of A0 - A2 below 0), no gap to close",
                "literal_rule_value": value}
    return {**base, "reported": True, **value}


def restoration_reading(a1_minus_a0: dict) -> str:
    """The reading fixed in the S2 amendment before any A0 trial ran.

    ceiling       -- A0 restores more than A1 and the CI of A1 - A0 lies below 0:
                     A1 approaches a restoration ceiling that A0 sets.
    a2_below_task -- A1 restores at least as often as A0 (point estimate >= 0):
                     the A1 - A2 restoration gap is A2 falling below the
                     correction-task level, not A1 approaching a ceiling.
    indeterminate -- A0 above A1 by the point estimate, CI includes 0.
    """
    est = a1_minus_a0.get("estimate")
    ci = a1_minus_a0.get("ci95") or (None, None)
    if est is None:
        return "no_estimate"
    if est >= 0:
        return "a2_below_task"
    if ci[1] is not None and ci[1] < 0:
        return "ceiling"
    return "indeterminate"


def _provenance(cell: str, rows: list[dict], usable: list[dict], excluded: Counter,
                seed: int) -> dict:
    all_trials = [t for r in rows for t in r.get("trials", [])]
    return {
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "seed": seed, "n_boot": N_BOOT, "prospective": True, "cell": cell,
        "defect_rows": len(rows),
        "defect_rows_by_status": dict(Counter(r.get("status") for r in rows)),
        "sessions_per_defect_max": max(
            (len({t.get("session_id") for t in r.get("trials", [])}) for r in rows
             if r.get("trials")), default=0),
        "trials_total": len(all_trials),
        "trials_usable": len(usable),
        "exclusions": dict(excluded),
        "served_models": dict(Counter(
            m for t in all_trials for m in (t.get("served_models") or []))),
        "total_tokens": int(sum(t.get("total_tokens") or 0 for t in all_trials)),
    }


def analyse_a0fill(rows: list[dict], core_rows: list[dict], seed: int = DEFAULT_SEED,
                   root: str | None = None) -> dict:
    """S2a: A0 on the 71 core defects without it, joined to T2 on defect_id.

    Pooled A0 = the core's in-session A0 (71 defects) plus this cell's later-
    session A0 (71 defects); A1 and A2 always come from the core. The in-session
    reads use only this cell (A0 against the r = 1 A1 anchor).
    """
    new, excluded = usable_trials(rows)
    core, _ = usable_trials(core_rows)
    new_a0 = [t for t in new if t["arm"] == "A0"]
    anchor = _relabel_anchor([t for t in new if t["arm"] == "A1"])
    fill_ids = {t["defect_id"] for t in new}
    core_a0_ids = {t["defect_id"] for t in core if t["arm"] == "A0"}
    overlap = sorted(fill_ids & core_a0_ids)
    if overlap:
        raise ValueError(f"a0fill re-ran core A0 defects: {overlap[:5]}")

    pooled = [t for t in core if t["arm"] in ("A0", "A1", "A2")] + new_a0
    cm_pool = cells(pooled)
    cm_new = cells(new_a0 + anchor)
    cm_core = cells(core)
    core_in_fill = [t for t in core if t["defect_id"] in fill_ids]

    out = {
        "provenance": _provenance("a0fill", rows, new, excluded, seed),
        "sources": {"A0": "T2 (in-session, 71 defects) + T2A0 (later session, 71 defects)",
                    "A1, A2": "T2", ANCHOR: "T2A0, r = 1"},
        "repair": {
            "A1_over_A0_pooled": ratio(cm_pool, "A1", "A0", seed),
            "A1_minus_A0_pooled": contrast(cm_pool, "A1", "A0", seed),
            "A1_over_A0_core_in_session": ratio(cm_core, "A1", "A0", seed),
            "anchor_over_A0_in_session": ratio(cm_new, ANCHOR, "A0", seed),
            "anchor_minus_A0_in_session": contrast(cm_new, ANCHOR, "A0", seed),
            "rates_pooled": {a: _rate_ci(cm_pool, a, seed) for a in ("A0", "A1", "A2")},
            "A0_by_operator": {k: v for k, v in rates_by(
                pooled, lambda t: t["operator"]).items() if k.endswith("|A0")},
        },
        "drift_anchor_vs_core_A1": _drift(
            [{**t, "arm": "A1"} for t in anchor],
            [t for t in core_in_fill if t["arm"] == "A1"]),
    }
    if root is not None:
        clean = _clean_outputs(core_rows, root)
        strata = _strata(root)

        def stratum(t):
            return strata.get(t["defect_id"].rsplit(":", 1)[0])

        pooled_copy = _copy_trials(pooled, clean)
        cp_pool = cells(pooled_copy)
        cp_new = cells(_copy_trials(new_a0 + anchor, clean))
        cp_core_fill = cells(_copy_trials(core_in_fill, clean))
        a1_a0 = contrast(cp_pool, "A1", "A0", seed)
        out["repair"]["A0_by_stratum"] = {
            k: v for k, v in rates_by(pooled, stratum).items() if k.endswith("|A0")}
        out["restoration"] = {
            "rates_pooled": {a: _rate_ci(cp_pool, a, seed) for a in ("A0", "A1", "A2")},
            "A1_minus_A0_pooled": a1_a0,
            "A0_minus_A2_pooled": contrast(cp_pool, "A0", "A2", seed),
            "A1_minus_A2_pooled": contrast(cp_pool, "A1", "A2", seed),
            "reading": restoration_reading(a1_a0),
            "share_of_gap_closed": share_of_gap(cp_pool, "A0", "A1", "A2", seed),
            "anchor_minus_A0_in_session": contrast(cp_new, ANCHOR, "A0", seed),
            "anchor_rate_vs_core_A1_same_defects": {
                ANCHOR: _rate_ci(cp_new, ANCHOR, seed),
                "core_A1": _rate_ci(cp_core_fill, "A1", seed)},
            "A0_by_operator": {k: v for k, v in rates_by(
                pooled_copy, lambda t: t["operator"]).items() if k.endswith("|A0")},
            "A0_by_stratum": {k: v for k, v in rates_by(
                pooled_copy, stratum).items() if k.endswith("|A0")},
        }
        out["repair_decomposition_A0_pooled"] = compute_repair_decomposition(
            [t for t in pooled if t["arm"] == "A0"], clean)["overall"]
    return out


def analyse_thinking_a0(rows: list[dict], thinking_rows: list[dict],
                        seed: int = DEFAULT_SEED, root: str | None = None) -> dict:
    """S2b: A0 at none and high, joined to T2T (A1, A2) on defect_id and effort.

    Within-session: A0 against the r = 1 A1 anchor (this cell). Cross-session:
    A0 against T2T's A1 and A2 at the same effort.
    """
    new, excluded = usable_trials(rows)
    sweep, _ = usable_trials(thinking_rows)
    efforts = THINKING_A0_EFFORTS
    new_a0 = [t for t in new if t["arm"] == "A0"]
    anchor = _relabel_anchor([t for t in new if t["arm"] == "A1"])
    ids = {t["defect_id"] for t in new}
    sweep = [t for t in sweep if t["defect_id"] in ids and t["arm"] in ("A1", "A2")
             and t.get("reasoning_effort") in efforts]
    joined = new_a0 + anchor + sweep
    cm = factor_cells(joined, thinking_level, arm=None)

    out = {
        "provenance": _provenance("thinking_a0", rows, new, excluded, seed),
        "sources": {"A0, " + ANCHOR: "T2TA0", "A1, A2": "T2T"},
        "repair": {e: {
            "A0": _rate_ci(cm, f"A0@{e}", seed),
            "A1_minus_A0_cross_session": contrast(cm, f"A1@{e}", f"A0@{e}", seed),
            "anchor_minus_A0_in_session": contrast(cm, f"{ANCHOR}@{e}", f"A0@{e}", seed),
        } for e in efforts},
        "drift_anchor_vs_T2T_A1": {e: _drift(
            [{**t, "arm": "A1"} for t in anchor if t.get("reasoning_effort") == e],
            [t for t in sweep if t["arm"] == "A1" and t.get("reasoning_effort") == e])
            for e in efforts},
    }
    if root is not None:
        clean = _clean_outputs(thinking_rows, root)
        cp = factor_cells(_copy_trials(joined, clean), thinking_level, arm=None)
        restoration = {}
        for e in efforts:
            a1_a0 = contrast(cp, f"A1@{e}", f"A0@{e}", seed)
            restoration[e] = {
                "rates": {a: _rate_ci(cp, f"{a}@{e}", seed)
                          for a in ("A0", "A1", "A2", ANCHOR)},
                "A0_minus_A1": contrast(cp, f"A0@{e}", f"A1@{e}", seed),
                "A0_minus_A2": contrast(cp, f"A0@{e}", f"A2@{e}", seed),
                "A1_minus_A2": contrast(cp, f"A1@{e}", f"A2@{e}", seed),
                "A1_minus_A0_cross_session": a1_a0,
                "anchor_minus_A0_in_session": contrast(
                    cp, f"{ANCHOR}@{e}", f"A0@{e}", seed),
                "reading": restoration_reading(a1_a0),
                "share_of_gap_closed": share_of_gap(
                    cp, f"A0@{e}", f"A1@{e}", f"A2@{e}", seed),
            }
        out["restoration"] = restoration
    return out


def _cell_bootstrap(per_defect: dict, cell_of: dict, seed: int, n_boot: int = N_BOOT):
    """Percentile CI of a mean over defects, resampling business x stage cells.

    Tier-1 defects nest in their cell (section 2.2), so the resampling unit is
    the cell; a bootstrap over defects would treat neighbours as independent.
    """
    lo, hi = np.percentile(_cell_boot_dist(per_defect, cell_of, seed, n_boot), [2.5, 97.5])
    return [float(lo), float(hi)]


def _cell_boot_dist(per_defect: dict, cell_of: dict, seed: int, n_boot: int = N_BOOT):
    """The bootstrap distribution behind ``_cell_bootstrap`` (same draws)."""
    cells = sorted({cell_of[d] for d in per_defect})
    by_cell = {c: [per_defect[d] for d in per_defect if cell_of[d] == c] for c in cells}
    rng = np.random.default_rng(seed)
    boot = []
    for _ in range(n_boot):
        pick = rng.integers(0, len(cells), size=len(cells))
        vals = [v for i in pick for v in by_cell[cells[i]]]
        boot.append(np.mean(vals))
    return np.array(boot)


def _tier1_cell(trial: dict) -> tuple[str, str]:
    """The business x stage cell of a Tier-1 trial, keyed by business ID.

    Until 2026-11-14 the stored ``cell`` label named only the business, and
    chains share names (two Wingstops are sampled), so the label alone could
    pool two businesses. The ID comes from the bank's defect ID
    (``source:business_id:stage:index``, ``defect_bank.build``). The label
    stays first in the key, so where no two businesses share a name the cells
    sort, and the cluster bootstrap resamples, exactly as before: T1's
    intervals are unchanged.
    """
    parts = trial["defect_id"].split(":")
    if len(parts) != 4:
        raise ValueError(f"not a defect-bank ID: {trial['defect_id']!r}")
    return (trial["cell"], parts[1])


def analyse_tier1(rows: list[dict], seed: int = DEFAULT_SEED) -> dict:
    """Section 0.1 A8: the production retry on real defects. Descriptive only.

    No hypothesis test is run (plan section 5, Tier 1: MDE about 31 pp, and a
    cluster bootstrap with few cells over-rejects). Rates are defect-level
    means of the repetitions; intervals resample business x stage cells.
    """
    usable = [t for r in rows for t in r.get("trials", []) if t.get("status") == "ok"]
    excluded = Counter(t.get("status") for r in rows for t in r.get("trials", [])
                       if t.get("status") != "ok")
    cell_of = {t["defect_id"]: _tier1_cell(t) for t in usable}

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


# ── Tier 1 pooled with the Option-H harvest (section 0.1 A14) ─────────────────

TIER1_TEST_MIN_CELLS = 15     # A14: the one test runs iff the pooled bank has >= 15 cells
SINGLE_PASS_LABEL = "A"       # defect_bank source label of a Phase-A dump (out_study/A, H/A)


def clean_check_pass(trial: dict) -> bool | None:
    """A14's clean-check pass: the supervisor passes the retried output outright.

    ``post_verdict == "proceed"``: no check fires at any level. ``accepted``
    also counts ``proceed_with_warning`` (no *retry*-level class fires), so
    this rate is never above acceptance. Fixed 2026-11-14, before any T1H trial.
    """
    v = trial.get("post_verdict")
    return None if v is None else v == "proceed"


def _tier1_bank(usable: list[dict], seed: int) -> dict:
    """One column of A14's RQ3 table: rates by arm and two acceptance differences."""
    cell_of = {t["defect_id"]: _tier1_cell(t) for t in usable}

    def per_defect(arm: str, value) -> dict:
        reps: dict = defaultdict(list)
        for t in usable:
            v = value(t) if t["arm"] == arm else None
            if v is not None:
                reps[t["defect_id"]].append(1.0 if v else 0.0)
        return {d: float(np.mean(v)) for d, v in reps.items()}

    def rate(arm: str, value) -> dict:
        pd = per_defect(arm, value)
        if not pd:
            return {"n_defects": 0, "n_cells": 0}
        return {"rate": float(np.mean(list(pd.values()))),
                "ci95_cells": _cell_bootstrap(pd, cell_of, seed),
                "n_defects": len(pd), "n_cells": len({cell_of[d] for d in pd})}

    def difference(arm_a: str, arm_b: str) -> dict:
        a = per_defect(arm_a, lambda t: t.get("accepted"))
        b = per_defect(arm_b, lambda t: t.get("accepted"))
        diff = {d: a[d] - b[d] for d in sorted(a.keys() & b.keys())}
        if not diff:
            return {"n_defects": 0, "n_cells": 0}
        boot = _cell_boot_dist(diff, cell_of, seed)
        lo, hi = np.percentile(boot, [2.5, 97.5])
        return {"estimate": float(np.mean(list(diff.values()))),
                "ci95_cells": [float(lo), float(hi)],
                "n_defects": len(diff), "n_cells": len({cell_of[d] for d in diff}),
                "_boot": boot}

    accepted = lambda t: t.get("accepted")
    resolved = lambda t: t.get("target_resolved")
    return {
        "n_defects": len(cell_of),
        "n_cells": len(set(cell_of.values())),
        "defects_by_stage": dict(Counter(
            t["stage"] for t in {t["defect_id"]: t for t in usable}.values())),
        "accepted": {a: rate(a, accepted) for a in TIER1_ARMS},
        "target_resolved": {a: rate(a, resolved) for a in TIER1_ARMS},
        "clean_check_pass": {a: rate(a, clean_check_pass) for a in TIER1_ARMS},
        "A2_minus_A1_accepted": difference("A2", "A1"),
        "A1_minus_A3_accepted": difference("A1", "A3"),
    }


def _strip_boot(res: dict) -> dict:
    return {k: ({kk: vv for kk, vv in v.items() if kk != "_boot"} if isinstance(v, dict) else v)
            for k, v in res.items()}


def analyse_tier1_pooled(t1_rows: list[dict], t1h_rows: list[dict],
                         seed: int = DEFAULT_SEED) -> dict:
    """Section 0.1 A14: T1, T1H, pooled and the single-pass (A + H) sensitivity.

    The one test (A14): iff the pooled bank has >= 15 distinct business x stage
    cells with an A2 - A1 difference, a two-sided cell-cluster bootstrap test of
    A2 - A1 acceptance at alpha = 0.05. It rejects iff the percentile 95 % CI
    excludes 0; p is 2 x the smaller bootstrap tail share at 0, capped at 1.
    Nothing else is tested.
    """
    def usable_of(rows):
        return [t for r in rows for t in r.get("trials", []) if t.get("status") == "ok"]

    t1, t1h = usable_of(t1_rows), usable_of(t1h_rows)
    shared = {t["defect_id"] for t in t1} & {t["defect_id"] for t in t1h}
    if shared:
        raise ValueError(f"defects in both T1 and T1H: {sorted(shared)[:5]}")
    keys: dict = defaultdict(set)
    for t in t1 + t1h:
        parts = t["defect_id"].split(":")
        keys[(parts[1], t["stage"])].add(_tier1_cell(t))
    split = {k: v for k, v in keys.items() if len(v) > 1}
    if split:
        raise ValueError(f"one business x stage under two cell labels: {split}")

    pooled = t1 + t1h
    single = [t for t in pooled if t["defect_id"].split(":")[0] == SINGLE_PASS_LABEL]
    banks = {"T1": _tier1_bank(t1, seed), "T1H": _tier1_bank(t1h, seed),
             "Pooled": _tier1_bank(pooled, seed), "A+H": _tier1_bank(single, seed)}

    gap = banks["Pooled"]["A2_minus_A1_accepted"]
    n_cells = gap.get("n_cells", 0)
    if n_cells >= TIER1_TEST_MIN_CELLS:
        boot = gap["_boot"]
        lo, hi = gap["ci95_cells"]
        test = {"run": True, "n_cells": n_cells, "alpha": ALPHA,
                "estimate": gap["estimate"], "ci95_cells": [lo, hi],
                "rejects": bool(lo > 0 or hi < 0),
                "p_two_sided": float(min(1.0, 2 * min(np.mean(boot <= 0),
                                                      np.mean(boot >= 0))))}
    else:
        test = {"run": False, "n_cells": n_cells,
                "reason": f"pooled bank has {n_cells} < {TIER1_TEST_MIN_CELLS} cells: no p-value "
                          "(small-cluster Type I inflation, paper section 4.7)"}

    all_trials = [t for r in t1_rows + t1h_rows for t in r.get("trials", [])]
    return {
        "provenance": {
            "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "seed": seed, "n_boot": N_BOOT,
            "trials_usable": {"T1": len(t1), "T1H": len(t1h)},
            "exclusions": dict(Counter(t.get("status") for t in all_trials
                                       if t.get("status") != "ok")),
            "served_models": dict(Counter(m for t in all_trials
                                          for m in (t.get("served_models") or []))),
            "total_tokens": {"T1": int(sum(t.get("total_tokens") or 0 for t in t1)),
                             "T1H": int(sum(t.get("total_tokens") or 0 for t in t1h))},
        },
        "note": ("descriptive apart from the one A14 test on the pooled A2 - A1 acceptance; "
                 "A+H keeps only defects from single-pass Phase-A dumps (drops out_study/R)"),
        "banks": {name: _strip_boot(b) for name, b in banks.items()},
        "test_pooled_A2_minus_A1_accepted": test,
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


def analyse_downstream(rows: list[dict], seed: int = DEFAULT_SEED,
                       root: str = "out_study",
                       core_path: str = "out_study/T2/checkpoint.jsonl") -> dict:
    """Section 0.1 A9: pipeline-level outcomes of clean, unrepaired and repaired outputs.

    Three endpoints, fixed in the amendment before the pass ran:
    E1 ``accepted`` -- every downstream stage passes the supervisor; E2 (O5
    only) -- the injected issue survives into the final report; E3 --
    divergence of the final report's claims from the clean run's, against the
    clean-vs-clean divergence measured in the same session (the noise floor).
    """
    cm_mod = _content_match_module()
    accepted: dict = {c: {} for c in DOWNSTREAM_CONDITIONS}
    accepted_cal: dict = {c: {} for c in DOWNSTREAM_CONDITIONS}
    diverg: dict = {c: {} for c in ("clean_rerun", "unrepaired", "A1", "A2")}
    e2: dict = {c: {} for c in DOWNSTREAM_CONDITIONS}
    coupling = Counter()
    excluded = Counter()
    operator_of = {}
    stage_of = {}

    spec = importlib.util.spec_from_file_location(
        "inject_defects", Path(__file__).resolve().parents[1] / "inject_defects.py")
    inj = importlib.util.module_from_spec(spec)
    sys.modules["inject_defects"] = inj
    spec.loader.exec_module(inj)
    dirs = {Path(d).name: d for d in inj.base_dirs(root)} if Path(root).exists() else {}
    core_rows = {r["defect_id"]: r for r in load_rows(core_path)} if Path(core_path).exists() else {}

    def is_calibrated(c, r):
        if c.get("status") != "ok":
            return False
        report_stage = c.get("stages", {}).get("report_agent", {})
        if report_stage.get("verdict") in ("retry", "halt"):
            return False
        strat_stage = c.get("stages", {}).get("strategy_agent")
        if strat_stage is not None:
            if strat_stage.get("status_error"):
                return False
            if "untraceable_recommendation" in strat_stage.get("fired", []):
                bid = r["defect_id"].rsplit(":", 1)[0]
                if bid in dirs:
                    base = inj.state_from_dump(dirs[bid])
                    injected, _ = inj.inject(r["operator"], base, seed=r.get("seed", 0))
                    core_row = core_rows.get(r["defect_id"], {})
                    arm_outputs = {t["arm"]: t.get("retried_output") for t in core_row.get("trials", [])
                                   if t.get("rep") == 0 and t.get("condition", "C0") == "C0"}
                    cond_name = c["condition"]
                    if cond_name == "clean":
                        ro = base.get("reasoning_output")
                    elif cond_name == "unrepaired":
                        ro = injected.get("reasoning_output")
                    else:
                        ro = arm_outputs.get(cond_name)
                    candidates = ([rc.get("cause", "") for rc in (ro or {}).get("root_causes") or []] +
                                  [rc.get("pattern", "") for rc in (ro or {}).get("root_causes") or []] +
                                  [p.get("description", "") for p in (ro or {}).get("patterns") or []])
                    issues = [str(x.get("issue") or "") for x in ((c.get("strategy_output") or {}).get("recommendations") or [])]
                    if cm_mod.untraceable(issues, candidates, threshold=0.10):
                        return False
            if any(f != "untraceable_recommendation" for f in strat_stage.get("fired", [])):
                if strat_stage.get("verdict") in ("retry", "halt"):
                    return False
        return True

    for r in rows:
        conds = {}
        for c in r.get("conditions", []):
            if c.get("status") != "ok":
                excluded[c.get("status")] += 1
                continue
            conds[(c["condition"], c["rep"])] = c
        d = r["defect_id"]
        operator_of[d] = r.get("operator")
        stage_of[d] = r.get("stage")
        clean0 = conds.get(("clean", 0))
        ref = report_items(clean0.get("final_report")) if clean0 else []
        for name in DOWNSTREAM_CONDITIONS:
            c = conds.get((name, 0))
            if c is None:
                continue
            accepted[name][d] = 1.0 if c["accepted"] else 0.0
            accepted_cal[name][d] = 1.0 if is_calibrated(c, r) else 0.0
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

    # Upstream group linkage to T2 rep=0
    by_arm_group = defaultdict(lambda: {"defects": [], "e3": [], "clean_rerun": [], "unrepaired": [], "e1_prod": [], "e1_cal": []})
    by_stage_arm_group = defaultdict(lambda: defaultdict(lambda: {"defects": [], "e3": [], "clean_rerun": [], "unrepaired": [], "e1_prod": [], "e1_cal": []}))

    if core_rows and dirs:
        for r in rows:
            d = r["defect_id"]
            stage = r.get("stage")
            bid = d.rsplit(":", 1)[0]
            if bid not in dirs:
                continue
            base = inj.state_from_dump(dirs[bid])
            clean_stage = base.get(inj.OUTPUT_KEY[stage])
            core_row = core_rows.get(d, {})

            conds = {(c["condition"], c["rep"]): c for c in r.get("conditions", []) if c.get("status") == "ok"}
            clean0 = conds.get(("clean", 0))
            clean1 = conds.get(("clean", 1))
            unrep = conds.get(("unrepaired", 0))
            ref = report_items(clean0.get("final_report")) if clean0 else []
            if not ref:
                continue
            div_clean1 = content_divergence(ref, report_items(clean1.get("final_report")), cm_mod) if clean1 else None
            div_unrep = content_divergence(ref, report_items(unrep.get("final_report")), cm_mod) if unrep else None

            for arm in ("A1", "A2"):
                c = conds.get((arm, 0))
                if not c:
                    continue
                t = [t for t in core_row.get("trials", []) if t.get("arm") == arm and t.get("rep") == 0 and t.get("condition", "C0") == "C0"]
                if not t:
                    continue
                t0 = t[0]
                outcome = t0.get("outcome", {}).get("outcome")
                retried = t0.get("retried_output")
                is_copy = canonical(retried) == canonical(clean_stage)
                grp = "repaired_copy" if outcome == "repaired" and is_copy else ("repaired_rewrite" if outcome == "repaired" else "fail")

                div_arm = content_divergence(ref, report_items(c.get("final_report")), cm_mod)
                for target_dict in (by_arm_group[(arm, grp)], by_stage_arm_group[stage][(arm, grp)]):
                    target_dict["defects"].append(d)
                    target_dict["e3"].append(div_arm)
                    target_dict["clean_rerun"].append(div_clean1)
                    target_dict["unrepaired"].append(div_unrep)
                    target_dict["e1_prod"].append(1.0 if c["accepted"] else 0.0)
                    target_dict["e1_cal"].append(1.0 if is_calibrated(c, r) else 0.0)

    def summarize_group_dict(gdict):
        res = {}
        for (arm, grp), v in sorted(gdict.items()):
            n = len(v["defects"])
            e3_vals = np.array([x for x in v["e3"] if x is not None])
            cr_vals = np.array([x for x in v["clean_rerun"] if x is not None])
            un_vals = np.array([x for x in v["unrepaired"] if x is not None])
            e1_p_vals = np.array(v["e1_prod"])
            e1_c_vals = np.array(v["e1_cal"])

            e3_m = float(e3_vals.mean()) if len(e3_vals) else None
            cr_m = float(cr_vals.mean()) if len(cr_vals) else None
            un_m = float(un_vals.mean()) if len(un_vals) else None
            excess = float(e3_m - cr_m) if e3_m is not None and cr_m is not None else None

            res[f"{arm}|{grp}"] = {
                "arm": arm,
                "group": grp,
                "n": n,
                "E3_divergence": {"mean": e3_m, "ci95": list(cluster_bootstrap_ci(e3_vals, np.random.default_rng(seed))) if len(e3_vals) else [None, None]},
                "clean_rerun_noise_floor": {"mean": cr_m, "ci95": list(cluster_bootstrap_ci(cr_vals, np.random.default_rng(seed))) if len(cr_vals) else [None, None]},
                "excess_over_noise_pp": excess,
                "unrepaired_baseline": {"mean": un_m, "ci95": list(cluster_bootstrap_ci(un_vals, np.random.default_rng(seed))) if len(un_vals) else [None, None]},
                "E1_accepted_prod": {"rate": float(e1_p_vals.mean()) if len(e1_p_vals) else None, "ci95": list(cluster_bootstrap_ci(e1_p_vals, np.random.default_rng(seed))) if len(e1_p_vals) else [None, None]},
                "E1_accepted_calibrated": {"rate": float(e1_c_vals.mean()) if len(e1_c_vals) else None, "ci95": list(cluster_bootstrap_ci(e1_c_vals, np.random.default_rng(seed))) if len(e1_c_vals) else [None, None]},
            }
        return res

    pooled_upstream = summarize_group_dict(by_arm_group)
    stage_upstream = {st: summarize_group_dict(by_stage_arm_group[st]) for st in sorted(by_stage_arm_group)}

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
        "E1_calibrated_accepted": {c: rate(v) for c, v in accepted_cal.items()},
        "E1_calibrated_contrasts": {
            f"{a}-{b}": _paired(accepted_cal[a], accepted_cal[b], seed)
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
        "E1_calibrated_by_operator": {
            f"{op}|{c}": rate({d: v for d, v in accepted_cal[c].items() if operator_of.get(d) == op})
            for op in sorted({o for o in operator_of.values() if o}) for c in DOWNSTREAM_CONDITIONS},
        "upstream_group_breakdown": {
            "pooled": pooled_upstream,
            "by_stage": stage_upstream,
        },
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
    ex = res.get("exploratory")
    if ex:
        print("\nEXPLORATORY (post hoc, RESULTS.md section 4; canonical JSON)")
        print("  identical to the clean output:", {
            a: f"{v['identical']}/{v['trials']} = {_pct(v['share'])}"
            for a, v in ex["identical_to_clean"].items()})
        print("  distinct outputs per complete cell:", {
            a: {k: _pct(s) for k, s in v["shares"].items()}
            for a, v in ex["distinct_outputs_per_cell"].items()})


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--cell", default="core",
                    choices=("core", "c1", "d19", "placement", "severity", "warm", "tier1",
                             "tier1_pooled",
                             "downstream", "o5sens", "c7", "thinking", "a0fill",
                             "thinking_a0", "flashlite"))
    ap.add_argument("--checkpoint", default=None,
                    help="defaults per --cell: out_study/T2, T2C1, T2D19, T2P, T2S or T2W")
    ap.add_argument("--root", default="out_study",
                    help="--cell core, warm, c7, thinking: the study dumps, for the identity "
                         "reads; o5sens: for re-scoring")
    ap.add_argument("--core-checkpoint", default="out_study/T2/checkpoint.jsonl",
                    help="c1/placement/severity: the core, for the serving-drift comparison")
    ap.add_argument("--thinking-checkpoint", default="out_study/T2T/checkpoint.jsonl",
                    help="thinking_a0: the sweep's A1/A2, joined on defect_id and effort")
    ap.add_argument("--t1h-checkpoint", default="out_study/T1H/checkpoint.jsonl",
                    help="tier1_pooled: the Option-H replay, pooled with --checkpoint (T1)")
    ap.add_argument("--json", default=None, help="write the full result here")
    ap.add_argument("--seed", type=int, default=DEFAULT_SEED)
    args = ap.parse_args()
    if args.cell == "flashlite" and args.root == "out_study":
        args.root = "out_study/FL"
    checkpoint = args.checkpoint or {
        "core": "out_study/T2", "c1": "out_study/T2C1", "d19": "out_study/T2D19",
        "placement": "out_study/T2P", "severity": "out_study/T2S", "warm": "out_study/T2W",
        "tier1": "out_study/T1", "tier1_pooled": "out_study/T1", "downstream": "out_study/T2D", "o5sens": "out_study/T2",
        "c7": "out_study/T2L", "thinking": "out_study/T2T",
        "a0fill": "out_study/T2A0", "thinking_a0": "out_study/T2TA0",
        "flashlite": "out_study/T2FL",
    }[args.cell] + "/checkpoint.jsonl"
    if args.cell == "core":
        res = analyse(load_rows(checkpoint), seed=args.seed, root=args.root)
        print_summary(res)
    else:
        core = (load_rows(args.core_checkpoint)
                if args.cell != "flashlite" and Path(args.core_checkpoint).exists() else None)
        if args.cell == "flashlite":
            res = analyse_flashlite(load_rows(checkpoint), seed=args.seed, root=args.root)
        elif args.cell == "c1":
            res = analyse_c1(load_rows(checkpoint), core, seed=args.seed)
        elif args.cell == "placement":
            res = analyse_placement(load_rows(checkpoint), core, seed=args.seed)
        elif args.cell == "severity":
            res = analyse_severity(load_rows(checkpoint), core, seed=args.seed)
        elif args.cell == "warm":
            res = analyse_warm(load_rows(checkpoint), core, seed=args.seed, root=args.root)
        elif args.cell == "tier1":
            res = analyse_tier1(load_rows(checkpoint), seed=args.seed)
        elif args.cell == "tier1_pooled":
            res = analyse_tier1_pooled(load_rows(checkpoint), load_rows(args.t1h_checkpoint),
                                       seed=args.seed)
        elif args.cell == "c7":
            res = analyse_c7(load_rows(checkpoint), core, seed=args.seed, root=args.root)
        elif args.cell == "thinking":
            res = analyse_thinking(load_rows(checkpoint), core, seed=args.seed, root=args.root)
        elif args.cell == "a0fill":
            res = analyse_a0fill(load_rows(checkpoint), core, seed=args.seed, root=args.root)
        elif args.cell == "thinking_a0":
            res = analyse_thinking_a0(load_rows(checkpoint),
                                      load_rows(args.thinking_checkpoint),
                                      seed=args.seed, root=args.root)
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
