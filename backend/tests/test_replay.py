"""Tests for the injection-study build items: replay (B3) and the defect bank.

The headline test is ``test_replay_fidelity_gate``: JOURNAL_PLAN section 11
makes exact reproduction of recorded facts a hard gate on the whole study, so it
belongs in the suite rather than in a script anyone can forget to run.

``scripts/`` is not a package, so both modules are loaded by path.
"""

import importlib.util
import json
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parent.parent
STUDY_ROOT = BACKEND / "out_study"


def _load_module(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, BACKEND / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


replay_stage = _load_module("replay_stage", "scripts/replay_stage.py")
defect_bank = _load_module("defect_bank", "scripts/analysis/defect_bank.py")

needs_study = pytest.mark.skipif(
    not (STUDY_ROOT / "A").is_dir(),
    reason="backend/out_study/ not present",
)


# ── B3: replay ────────────────────────────────────────────────────────────────


def test_state_from_dump_omits_reviews(tmp_path):
    """Replay must not silently substitute an empty review frame.

    The analysis-stage check measures against state['reviews_df']; if replay
    supplied an empty one, a contradiction rate of 0.0 would look like a clean
    result instead of an unmeasurable one. Absence is the correct behaviour.
    """
    (tmp_path / "_summary.json").write_text(
        json.dumps({"business_id": "b1", "business_name": "Test Diner"}), encoding="utf-8"
    )
    (tmp_path / "analysis.json").write_text(json.dumps([]), encoding="utf-8")
    for name in ("reasoning", "strategy", "report"):
        (tmp_path / f"{name}.json").write_text("null", encoding="utf-8")

    state = replay_stage.state_from_dump(str(tmp_path))

    assert state["business_name"] == "Test Diner"
    assert "reviews_df" not in state


def test_replay_uses_the_stage_it_is_given_not_the_latest():
    """The latest_stage trap: a full state must not resolve to report_agent.

    supervision.latest_stage scans backward from report_output, so routing a
    replay through the orchestrator would always measure the report stage. Every
    entry point takes an explicit stage; this pins that.
    """
    state = {
        "business_name": "Test Diner",
        "analysis_results": [
            {"review_id": "r1", "status": "success",
             "aspects": [{"category": "food_quality", "label": "negative"}]}
        ],
        "reasoning_output": {
            "status": "success",
            "patterns": [{
                "description": "bad food", "aspect": "food_quality",
                "frequency": 1.0, "evidence_review_ids": ["r1"],
            }],
            "root_causes": [],
        },
        "strategy_output": {"status": "success", "recommendations": []},
        "report_output": {"status": "success", "root_causes": [], "recommendations": []},
    }

    from app.core import supervision
    assert supervision.latest_stage(state) == "report_agent"

    facts, decision = replay_stage.replay("reasoning_agent", state)
    assert "patterns" in facts  # reasoning facts, not report facts
    assert decision.verdict == "proceed"


def test_replay_rejects_an_unknown_stage():
    with pytest.raises(ValueError):
        replay_stage.replay("nonexistent_agent", {})


@needs_study
def test_replay_fidelity_gate():
    """HARD GATE (JOURNAL_PLAN section 11): recomputed facts == recorded facts."""
    mismatches = replay_stage.verify(str(STUDY_ROOT))
    assert mismatches == 0


# ── defect bank ───────────────────────────────────────────────────────────────


def test_api_error_is_not_a_content_defect():
    classes, genuine, reason = defect_bank.classify(
        "reasoning_agent", {"status_error": True, "error_detail": "Error code: 503"}
    )
    assert classes == ["api_error"]
    assert genuine is False
    assert reason == "api_error"


def test_retry_verdict_with_no_recognised_class_is_surfaced():
    """classify() and supervision.decide() must not drift apart silently."""
    classes, genuine, reason = defect_bank.classify("reasoning_agent", {"patterns": []})
    assert classes == ["unclassified"]
    assert genuine is False
    assert reason == "unclassified"


def test_classes_map_to_the_operators_that_model_them():
    classes, genuine, _ = defect_bank.classify(
        "reasoning_agent",
        {"patterns": [{"missing_evidence_ids": ["abc"], "misaligned_evidence_ids": []}]},
    )
    assert genuine is True
    assert classes == ["missing_evidence_id"]
    assert defect_bank._OPERATORS["missing_evidence_id"] == ["O1", "O2"]


def test_cascade_detection_flags_a_broken_upstream(tmp_path):
    """A report defect downstream of an errored reasoning stage is a cascade.

    Built from the real shape of rep1/2qVZiMB22YPC2HCM62Gnbw, where a 503 at the
    reasoning stage left the report agent inventing content to fill the gap.
    """
    (tmp_path / "reasoning.json").write_text(
        json.dumps({"status": "error", "error_type": "api_error"}), encoding="utf-8"
    )
    reason = defect_bank.upstream_degenerate(str(tmp_path), "report_agent")
    assert reason is not None
    assert "reasoning_agent errored" in reason


def test_healthy_upstream_is_not_a_cascade(tmp_path):
    (tmp_path / "reasoning.json").write_text(
        json.dumps({"status": "success", "patterns": [{"aspect": "food_quality"}],
                    "root_causes": []}),
        encoding="utf-8",
    )
    (tmp_path / "strategy.json").write_text(
        json.dumps({"status": "success", "recommendations": [{"issue": "x"}]}),
        encoding="utf-8",
    )
    assert defect_bank.upstream_degenerate(str(tmp_path), "report_agent") is None


@needs_study
def test_defect_bank_matches_the_numbers_the_plan_cites():
    """Pins JOURNAL_PLAN section 5. If a re-run changes these, the plan is stale."""
    bank = defect_bank.build(str(STUDY_ROOT))
    s = bank["summary"]

    assert s["retry_observations"] == 15
    assert s["excluded_by_reason"] == {"api_error": 3}
    assert s["cascade"] == 1
    assert s["genuine"] == 11
    assert s["by_stage"] == {"strategy_agent": 6, "reasoning_agent": 5}
    assert s["distinct_cells"] == 5
    assert s["distinct_businesses"] == 4
    # The warn-level frequency signal the plan argues is worth reclaiming.
    assert bank["warn_level_flags"]["frequency_corrected"] == 27
