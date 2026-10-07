"""Tests for the confirmatory analysis (PREREGISTRATION.md sections 2-4, 6).

Every rule here is one the pre-registration fixed in prose; each test pins one
of them on synthetic rows, so the script was checked against the document
before it was ever pointed at real trial data.
"""

import importlib.util
import sys
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parent.parent


def _load_module(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, BACKEND / relative)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


ra = _load_module("repair_analysis", "scripts/analysis/repair_analysis.py")


def _trial(defect, arm, outcome, rep=0, status="ok", models=("m",), attempts=1,
           op="O2", placement=None):
    return {"defect_id": defect, "arm": arm, "rep": rep, "status": status,
            "served_models": list(models), "attempts_made": attempts,
            "operator": op, "condition": "C0", "stage": "reasoning_agent",
            "placement": placement or ("P0" if arm == "A3" else "P1"),
            "outcome": None if status != "ok" else {"outcome": outcome}}


def _row(defect, trials, op="O2"):
    return {"defect_id": defect, "operator": op, "status": "ok", "trials": trials}


def _pair(defect, a1, a2, op="O2"):
    """One defect with A1 and A2 repetitions given as outcome-class lists."""
    ts = [_trial(defect, "A1", o, i, op=op) for i, o in enumerate(a1)]
    ts += [_trial(defect, "A2", o, i, op=op) for i, o in enumerate(a2)]
    return _row(defect, ts, op)


# ── 2.1 the majority rule ────────────────────────────────────────────────────


@pytest.mark.parametrize("reps, expected", [
    ([1, 1, 1], 1), ([1, 1, 0], 1), ([1, 0, 0], 0), ([0, 0, 0], 0),
    ([1, 0], 0),          # a 1-1 split after a lost rep resolves to not repaired
    ([1, 1], 1), ([1], 1), ([0], 0),
])
def test_majority_is_strictly_more_than_half_of_completed(reps, expected):
    assert ra.majority(reps) == expected


# ── 2.3 the dichotomy is strict and applied before aggregation ──────────────


def test_deleted_and_replaced_count_against_repair():
    rows = [_pair("d1", ["deleted"] * 3, ["replaced"] * 3)]
    cm = ra.cells(ra.usable_trials(rows)[0])
    assert cm[("d1", "A1")] == [0, 0, 0]
    assert cm[("d1", "A2")] == [0, 0, 0]


# ── 2.1 exact McNemar on discordant defects, not on (defect, rep) pairs ─────


def test_exact_mcnemar_matches_the_binomial():
    assert ra.exact_mcnemar(0, 0) == 1.0
    assert ra.exact_mcnemar(5, 5) == 1.0
    assert ra.exact_mcnemar(6, 0) == pytest.approx(2 * 0.5 ** 6)
    assert ra.exact_mcnemar(0, 6) == pytest.approx(2 * 0.5 ** 6)


def test_mcnemar_counts_defects_not_repetitions():
    # One defect whose three A1 reps all succeed and A2 reps all fail is ONE
    # discordant pair. The naive (defect, rep) version would count three.
    rows = [_pair("d1", ["repaired"] * 3, ["unrepaired"] * 3)]
    res = ra.contrast(ra.cells(ra.usable_trials(rows)[0]), "A1", "A2", seed=0)
    assert res["discordant"] == {"A1_only": 1, "A2_only": 0}
    assert res["mcnemar_p"] == 1.0


# ── 2.4 the estimate averages reps per defect, then defects ─────────────────


def test_estimate_is_mean_of_per_defect_differences():
    rows = [
        _pair("d1", ["repaired"] * 3, ["unrepaired"] * 3),                  # +1
        _pair("d2", ["repaired", "repaired", "unrepaired"], ["repaired"] * 3),  # -1/3
    ]
    res = ra.contrast(ra.cells(ra.usable_trials(rows)[0]), "A1", "A2", seed=0)
    assert res["estimate"] == pytest.approx((1 - 1 / 3) / 2)
    assert res["n_defects"] == 2


def test_lost_reps_leave_the_defect_in_with_fewer_reps():
    row = _pair("d1", ["repaired"] * 3, ["unrepaired"] * 3)
    row["trials"][0]["status"] = "status_error"
    row["trials"][0]["outcome"] = None
    res = ra.contrast(ra.cells(ra.usable_trials([row])[0]), "A1", "A2", seed=0)
    assert res["n_defects"] == 1
    assert res["reps_per_cell"] == {"2/3": 1}


def test_defect_without_a_usable_rep_in_one_arm_is_dropped_and_counted():
    row = _pair("d1", ["repaired"] * 3, ["unrepaired"] * 3)
    for t in row["trials"]:
        if t["arm"] == "A2":
            t["status"], t["outcome"] = "status_error", None
    keep = _pair("d2", ["repaired"] * 3, ["repaired"] * 3)
    trials, excluded = ra.usable_trials([row, keep])
    planned = ra.planned_cells([row, keep])
    res = ra.contrast(ra.cells(trials, planned=planned), "A1", "A2", seed=0)
    assert res["n_defects"] == 1 and res["dropped"] == 1
    assert excluded["provider_failure"] == 3
    # Without the plan, the lost arm is indistinguishable from a never-planned one.
    assert ra.contrast(ra.cells(trials), "A1", "A2", seed=0)["dropped"] == 0


def test_a_defect_that_never_carried_an_arm_is_not_counted_as_dropped():
    # A3 runs on a subset by design; absence there is not a loss.
    rows = [_pair("d1", ["repaired"] * 3, ["repaired"] * 3)]
    res = ra.contrast(ra.cells(ra.usable_trials(rows)[0]), "A2", "A3", seed=0)
    assert res["n_defects"] == 0 and res["dropped"] == 0


def test_bootstrap_ci_is_deterministic_and_brackets_the_estimate():
    rows = [_pair(f"d{i}", ["repaired"] * 3,
                  ["repaired"] * 3 if i % 3 else ["unrepaired"] * 3) for i in range(30)]
    cm = ra.cells(ra.usable_trials(rows)[0])
    a, b = ra.contrast(cm, "A1", "A2", seed=7), ra.contrast(cm, "A1", "A2", seed=7)
    assert a["ci95"] == b["ci95"]
    assert a["ci95"][0] <= a["estimate"] <= a["ci95"][1]


# ── 4 exclusions ─────────────────────────────────────────────────────────────


def test_a_trial_served_by_two_models_is_excluded_as_fallback():
    row = _pair("d1", ["repaired"] * 3, ["repaired"] * 3)
    row["trials"][0]["served_models"] = ["primary", "fallback"]
    _, excluded = ra.usable_trials([row])
    assert excluded["fallback_fired"] == 1


def test_the_same_model_twice_is_a_schema_retry_not_a_fallback():
    row = _pair("d1", ["repaired"] * 3, ["repaired"] * 3)
    row["trials"][0]["served_models"] = ["m", "m"]
    row["trials"][0]["attempts_made"] = 2
    trials, excluded = ra.usable_trials([row])
    assert not excluded and len(trials) == 6
    trials_sa, excluded_sa = ra.usable_trials([row], drop_multi_attempt=True)
    assert excluded_sa["multi_attempt"] == 1 and len(trials_sa) == 5


def test_skipped_rows_contribute_nothing():
    rows = [{"defect_id": "x:O4", "operator": "O4", "status": "skipped"},
            _pair("d1", ["repaired"] * 3, ["unrepaired"] * 3)]
    res = ra.analyse(rows, seed=0)
    assert res["confirmatory"]["primary_A1_minus_A2"]["n_defects"] == 1


# ── 6 the split rule ─────────────────────────────────────────────────────────


@pytest.mark.parametrize("est, ci, branch", [
    (0.15, (0.02, 0.28), True),
    (0.15, (-0.01, 0.30), False),   # CI touches zero
    (0.11, (0.01, 0.21), False),    # below 12 pp
    (-0.15, (-0.28, -0.02), False), # excludes zero, wrong direction
])
def test_split_rule(est, ci, branch):
    assert ra.split_rule({"estimate": est, "ci95": ci})["branch"] is branch


# ── 3 secondaries ────────────────────────────────────────────────────────────


def test_o1_and_severe_contrasts_partition_the_pooled_defects():
    rows = [_pair("a:O1", ["repaired"] * 3, ["unrepaired"] * 3, op="O1"),
            _pair("b:O2", ["repaired"] * 3, ["repaired"] * 3, op="O2"),
            _pair("c:O5", ["unrepaired"] * 3, ["repaired"] * 3, op="O5")]
    res = ra.analyse(rows, seed=0)
    sec = res["secondary"]
    assert sec["1a_O1_contrast"]["n_defects"] == 1
    assert sec["1a_severe_contrast"]["n_defects"] == 2
    assert sec["8_without_O5"]["n_defects"] == 2


def test_cochran_q_is_zero_when_all_arms_agree():
    ts = []
    for arm in ("A1", "A2", "A3"):
        ts += [_trial("d1", arm, "repaired", i) for i in range(3)]
    ts2 = []
    for arm in ("A1", "A2", "A3"):
        ts2 += [_trial("d2", arm, "unrepaired", i) for i in range(3)]
    cm = ra.cells(ra.usable_trials([_row("d1", ts), _row("d2", ts2)])[0])
    q = ra.cochran_q(cm, ("A1", "A2", "A3"))
    assert q["n_defects"] == 2 and q["Q"] == 0.0


# ── the post-core passes (section 0.1 A2, A3) ───────────────────────────────


def _c1_row(defect, c0_a1, c0_a2, c1_a1, c1_a2, op="O2"):
    ts = []
    for cond, arm, outs in (("C0", "A1", c0_a1), ("C0", "A2", c0_a2),
                            ("C1", "A1", c1_a1), ("C1", "A2", c1_a2)):
        for i, o in enumerate(outs):
            t = _trial(defect, arm, o, i, op=op)
            t["condition"] = cond
            t["retried_output"] = {"o": o}
            ts.append(t)
    return _row(defect, ts, op)


def test_c1_reports_one_gap_per_condition_from_its_own_pass():
    rows = [_c1_row("d1", ["repaired"] * 3, ["unrepaired"] * 3,
                    ["repaired"] * 3, ["repaired"] * 3)]
    res = ra.analyse_c1(rows, seed=0)
    assert res["gap_C0"]["estimate"] == pytest.approx(1.0)
    assert res["gap_C1"]["estimate"] == pytest.approx(0.0)
    assert res["gap_C1_minus_gap_C0"]["estimate"] == pytest.approx(-1.0)
    # the conditions are never mixed into one cell
    assert res["rates"]["C1|A2"]["rate"] == pytest.approx(1.0)
    assert res["rates"]["C0|A2"]["rate"] == pytest.approx(0.0)


def test_c1_drift_pairs_rerun_c0_trials_with_the_cores_by_defect_arm_and_rep():
    rerun = [_c1_row("d1", ["repaired"] * 3, ["unrepaired"] * 3,
                     ["repaired"] * 3, ["repaired"] * 3)]
    core = [_pair("d1", ["repaired"] * 3, ["repaired", "unrepaired", "unrepaired"])]
    for t in core[0]["trials"]:
        t["retried_output"] = {"o": t["outcome"]["outcome"]}
    drift = ra.analyse_c1(rerun, core, seed=0)["drift_vs_core"]
    assert drift["pairs"] == 6
    assert drift["same_outcome_class"] == 5
    assert drift["flips_core_to_rerun"] == {"repaired->unrepaired": 1}


def test_d19_reads_retry_against_an_exact_zero_call_overwrite():
    ts = [_trial("x:O4", "A1", o, i, op="O4") for i, o in
          enumerate(["repaired", "repaired", "replaced"])]
    ts += [_trial("x:O4", "A3", "repaired", i, op="O4") for i in range(3)]
    res = ra.analyse_d19([_row("x:O4", ts, op="O4")], seed=0)
    assert res["overwrite"] == {"rate": 1.0, "llm_calls": 0, "note": "exact by construction"}
    assert res["A1_retry"]["rate"] == pytest.approx(2 / 3)
    assert res["A3_regeneration"]["rate"] == pytest.approx(1.0)
    assert res["A1_minus_A3"]["n_defects"] == 1


def test_an_all_success_arm_gets_an_exact_interval_not_just_a_degenerate_bootstrap():
    cm = {(f"d{i}", "A1"): [1, 1, 1] for i in range(23)}
    r = ra._rate_ci(cm, "A1", seed=0)
    assert r["ci95"] == [1.0, 1.0]                       # the bootstrap of a constant
    lo, hi = r["exact_ci95_defects"]
    assert hi == 1.0 and lo == pytest.approx(0.025 ** (1 / 23))   # 23/23 -> [0.852, 1]


def test_a_mixed_arm_carries_no_exact_interval():
    cm = {("d1", "A1"): [1, 0, 1], ("d2", "A1"): [1, 1, 1]}
    assert "exact_ci95_defects" not in ra._rate_ci(cm, "A1", seed=0)


def test_clopper_pearson_matches_known_values():
    assert ra.clopper_pearson(0, 10) == [0.0, pytest.approx(0.3084971)]
    lo, hi = ra.clopper_pearson(5, 10)
    assert lo == pytest.approx(0.187086, abs=1e-5) and hi == pytest.approx(0.812914, abs=1e-5)


# ── the placement and severity passes (section 0.1 A5, A6) ──────────────────


def _placement_row(defect, by_level, op="O2"):
    ts = []
    for level, outs in by_level.items():
        for i, o in enumerate(outs):
            t = _trial(defect, "A1", o, i, op=op, placement=level)
            t["retried_output"] = {"o": o}
            ts.append(t)
    return _row(defect, ts, op)


def test_placement_contrasts_pair_levels_within_a_defect():
    rows = [_placement_row("d1", {"P0": ["repaired"] * 3, "P1": ["repaired"] * 3,
                                  "P2": ["unrepaired"] * 3, "P3": ["repaired"] * 3})]
    res = ra.analyse_placement(rows, seed=0)
    assert res["rates"]["P2"]["rate"] == pytest.approx(0.0)
    assert res["contrasts"]["P1-P2"]["estimate"] == pytest.approx(1.0)
    assert res["contrasts"]["P3-P2"]["estimate"] == pytest.approx(1.0)
    assert res["contrasts"]["P1-P0"]["estimate"] == pytest.approx(0.0)
    assert "P1 >> P3 ~ P2" in res["prediction"]


def test_placement_drift_compares_only_the_rerun_p1_cells_with_the_core():
    rows = [_placement_row("d1", {"P0": ["unrepaired"] * 3, "P1": ["repaired"] * 3,
                                  "P2": ["repaired"] * 3, "P3": ["repaired"] * 3})]
    core = [_pair("d1", ["repaired", "repaired", "unrepaired"], ["repaired"] * 3)]
    for t in core[0]["trials"]:
        t["retried_output"] = {"o": t["outcome"]["outcome"]}
    drift = ra.analyse_placement(rows, core, seed=0)["drift_vs_core"]
    assert drift["pairs"] == 3                    # P1 x 3 reps vs core A1 x 3 reps
    assert drift["flips_core_to_rerun"] == {"unrepaired->repaired": 1}


def test_severity_contrasts_level_1_against_level_2():
    ts = []
    for level, outs in ((1, ["repaired"] * 3), (2, ["replaced", "repaired", "replaced"])):
        for i, o in enumerate(outs):
            t = _trial("x:O1", "A1", o, i, op="O1")
            t["severity"] = level
            ts.append(t)
    res = ra.analyse_severity([_row("x:O1", ts, op="O1")], seed=0)
    assert res["rates"]["1"]["rate"] == pytest.approx(1.0)
    assert res["rates"]["2"]["rate"] == pytest.approx(1 / 3)
    c = res["contrasts"]["1-2"]
    assert c["estimate"] == pytest.approx(2 / 3)
    assert c["discordant"] == {"1_only": 1, "2_only": 0}


def test_factor_passes_report_every_level_also_without_multi_attempt_trials():
    """Section 4 applies to the exploratory passes too: with and without."""
    rows = [_placement_row("d1", {"P0": ["repaired"] * 3, "P1": ["repaired"] * 3,
                                  "P2": ["repaired"] * 3, "P3": ["repaired"] * 3})]
    for t in rows[0]["trials"]:
        if t["placement"] == "P0" and t["rep"] < 2:
            t["attempts_made"] = 2
    res = ra.analyse_placement(rows, seed=0)
    assert res["multi_attempt_trials_by_level"] == {"P0": 2, "P1": 0, "P2": 0, "P3": 0}
    sa = res["without_multi_attempt_trials"]
    assert sa["rates"]["P0"]["n_defects"] == 1           # one P0 rep survives
    assert sa["contrasts"]["P1-P0"]["reps_per_cell"] == {"3/1": 1}



# -- the warm-resample pass (section 0.1 A7) ----------------------------------


def _warm_row(defect, spec, op="O2"):
    """spec: {(arm, temperature): [outcomes]}"""
    ts = []
    for (arm, temp), outs in spec.items():
        for i, o in enumerate(outs):
            t = _trial(defect, arm, o, i, op=op)
            t["temperature"] = temp
            t["total_tokens"] = 100 if temp == 0.0 else 120
            t["retried_output"] = {"o": o}
            ts.append(t)
    return _row(defect, ts, op)


def test_warm_reports_both_gaps_and_their_difference():
    rows = [_warm_row("d1", {("A1", 0.0): ["repaired"] * 3, ("A2", 0.0): ["repaired"] * 3,
                             ("A1", 1.0): ["repaired"] * 3, ("A2", 1.0): ["unrepaired"] * 3,
                             ("A3", 1.0): ["unrepaired", "repaired", "repaired"]})]
    res = ra.analyse_warm(rows, seed=0)
    assert res["contrasts"]["A1@T0-A2@T0"]["estimate"] == pytest.approx(0.0)
    assert res["contrasts"]["A1@T1-A2@T1"]["estimate"] == pytest.approx(1.0)
    assert res["gap_T1_minus_gap_T0"]["estimate"] == pytest.approx(1.0)
    assert res["mean_tokens_per_trial"]["A1@T1"] == pytest.approx(120)


def test_best_of_k_follows_repetition_order():
    rows = [_warm_row("d1", {("A3", 1.0): ["unrepaired", "repaired", "unrepaired"]}),
            _warm_row("d2", {("A3", 1.0): ["unrepaired", "unrepaired", "unrepaired"]})]
    bok = ra.analyse_warm(rows, seed=0)["A3_best_of_k_T1"]
    assert bok["1"]["rate"] == pytest.approx(0.0)
    assert bok["2"]["rate"] == pytest.approx(0.5)
    assert bok["3"]["rate"] == pytest.approx(0.5)


def test_warm_levels_name_arm_and_temperature():
    assert ra.warm_level({"arm": "A1", "temperature": 0.0}) == "A1@T0"
    assert ra.warm_level({"arm": "A3", "temperature": 1.0}) == "A3@T1"
    assert ra.warm_level({"arm": "A2"}) == "A2@T0"   # rows written before the field existed
