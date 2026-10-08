"""Tests for the offline secondaries (scripts/analysis/secondary_extra.py)."""

import importlib.util
import sys
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parent.parent
STUDY_ROOT = BACKEND / "out_study"


def _load_module(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, BACKEND / relative)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


se = _load_module("secondary_extra", "scripts/analysis/secondary_extra.py")

needs_study = pytest.mark.skipif(
    not (STUDY_ROOT / "A").is_dir(), reason="backend/out_study/ not present"
)


def _trial(defect, op, arm, outcome, rep=0, stage="reasoning_agent", placement="P1",
           post_verdict="proceed"):
    return {"defect_id": defect, "operator": op, "arm": arm, "rep": rep, "status": "ok",
            "stage": stage, "placement": placement, "post_verdict": post_verdict,
            "outcome": {"outcome": outcome}}


def test_class_ordering_compares_defect_level_a1_rates_by_class():
    rows = [{"trials": [_trial("a", "O1", "A1", "unrepaired")]},
            {"trials": [_trial("b", "O3", "A1", "repaired")]},
            {"trials": [_trial("c", "O5", "A1", "repaired", 0), _trial("c", "O5", "A1", "replaced", 1)]}]
    res = se.class_ordering(rows)
    assert res["observed_order"] == ["structural", "semantic", "referential"]
    assert res["prediction_holds"] is False
    rows[0]["trials"][0]["outcome"]["outcome"] = "repaired"
    rows[1]["trials"][0]["outcome"]["outcome"] = "deleted"
    rows[2]["trials"][1]["outcome"]["outcome"] = "unrepaired"
    res = se.class_ordering(rows)
    assert res["observed_order"] == ["referential", "semantic", "structural"]


def test_origin_judges_injected_trials_by_the_supervisors_verdict():
    core = [{"trials": [_trial("x", "O1", "A3", "repaired", placement="P0", post_verdict="retry")]}]
    placement = [{"trials": [_trial("y", "O1", "A1", "repaired", placement="P0", post_verdict="proceed")]}]
    tier1 = [{"trials": [{"defect_id": "t", "arm": "A1", "stage": "reasoning_agent", "status": "ok",
                          "accepted": False},
                         {"defect_id": "t", "arm": "A3", "stage": "reasoning_agent", "status": "ok",
                          "accepted": True}]}]
    res = se.origin(core, placement, tier1)
    assert res["A1|all"]["injected"]["rate"] == pytest.approx(1.0)
    assert res["A1|all"]["real"]["rate"] == pytest.approx(0.0)
    # an injected trial the supervisor still routes to retry is not accepted
    assert res["A3|all"]["injected"]["rate"] == pytest.approx(0.0)


@needs_study
def test_the_frequency_check_steps_at_its_tolerance():
    curve = se.c6_frequency(str(STUDY_ROOT), deltas=(0.04, 0.051, 0.10))["curve"]
    assert curve["0.04"]["detected"] == 0.0
    assert curve["0.051"]["detected"] == 1.0
    assert curve["0.1"]["detected"] == 1.0


@needs_study
def test_every_real_defect_couples_to_a_synthetic_operator():
    res = se.coupling(str(STUDY_ROOT))
    assert res["real_defects"] == res["with_a_synthetic_operator"] == 13


@needs_study
def test_the_trace_curve_counts_grounded_and_foreign_issues():
    res = se.c6_trace(str(STUDY_ROOT))
    for key in ("grounded_issues", "foreign_corpus_issues"):
        assert res[key]["n"] > 0
        assert 0.0 <= res[key]["production_difflib_fires"] <= 1.0
        assert 0.0 <= res[key]["content_jaccard_fires"] <= 1.0
    # a grounded issue fires the production check only below its threshold
    for band, v in res["grounded_by_production_similarity"].items():
        lo = float(band.strip("[)").split(",")[0])
        if lo >= 0.35:
            assert v["production_difflib_fires"] == 0.0
