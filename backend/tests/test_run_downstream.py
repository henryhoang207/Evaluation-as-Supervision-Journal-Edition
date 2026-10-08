"""Tests for the downstream-propagation runner (PREREGISTRATION.md section 0.1 A9)."""

import importlib.util
import json
import sys
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parent.parent
STUDY_ROOT = BACKEND / "out_study"
CORE = STUDY_ROOT / "T2" / "checkpoint.jsonl"


def _load_module(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, BACKEND / relative)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


ds = _load_module("run_downstream", "scripts/run_downstream.py")

needs_core = pytest.mark.skipif(not CORE.exists(), reason="core checkpoint not present")


@needs_core
def test_the_plan_covers_every_core_defect_with_a_downstream_stage():
    plan = ds.build_plan(str(STUDY_ROOT), str(CORE))
    s = ds.plan_summary(plan)
    assert s["defects"] == 90
    assert s["by_operator"] == {"O1": 24, "O2": 24, "O3": 22, "O5": 20}
    assert s["missing_arm_outputs"] == 3          # the core's lost rep-0 arm trials
    assert all(d["stage"] in ("reasoning_agent", "strategy_agent") for d in plan)


@needs_core
def test_every_defect_runs_clean_twice_unrepaired_and_the_two_arms():
    for d in ds.build_plan(str(STUDY_ROOT), str(CORE)):
        names = [(c["condition"], c["rep"]) for c in d["conditions"]]
        assert names[:3] == [("clean", 0), ("clean", 1), ("unrepaired", 0)]
        assert set(names[3:]) <= {("A1", 0), ("A2", 0)}
        assert len(names[3:]) + len(d["missing_arms"]) == 2


@needs_core
def test_each_condition_starts_from_its_own_output_with_downstream_cleared():
    d = [x for x in ds.build_plan(str(STUDY_ROOT), str(CORE)) if x["stage"] == "reasoning_agent"][0]
    base = ds.inject_defects.state_from_dump(d["dump_dir"])
    injected, _ = ds.inject_defects.inject(d["operator"], base, seed=d["seed"])
    marker = {"patterns": [], "root_causes": [], "status": "success"}
    for name, expected in (("clean", base["reasoning_output"]),
                           ("unrepaired", injected["reasoning_output"]), ("A1", marker)):
        st = ds.start_state(d, name, base, injected, marker if name == "A1" else None)
        assert st["reasoning_output"] == expected
        assert st["strategy_output"] is None and st["report_output"] is None
        assert st["retry_feedback"] is None
    assert base["reasoning_output"] != injected["reasoning_output"]


@needs_core
def test_a_condition_runs_each_downstream_stage_once_through_the_production_node(monkeypatch):
    from app.core import nodes

    d = [x for x in ds.build_plan(str(STUDY_ROOT), str(CORE)) if x["stage"] == "reasoning_agent"][0]
    base = ds.inject_defects.state_from_dump(d["dump_dir"])
    injected, _ = ds.inject_defects.inject(d["operator"], base, seed=d["seed"])
    ran = []

    def fake_strategy(state):
        ran.append("strategy")
        state["strategy_output"] = base["strategy_output"]
        return state

    def fake_report(state):
        ran.append("report")
        state["report_output"] = base["report_output"]
        return state

    monkeypatch.setattr(nodes, "strategy_node", fake_strategy)
    monkeypatch.setattr(nodes, "report_node", fake_report)
    st = ds.start_state(d, "clean", base, injected, None)
    row = ds.run_condition(d, {"condition": "clean", "rep": 0}, st, "s", dry_run=False)
    assert ran == ["strategy", "report"]
    assert row["status"] == "ok" and set(row["stages"]) == {"strategy_agent", "report_agent"}
    assert row["final_report"] == base["report_output"]
    # the clean pipeline, replayed, passes its own checks
    assert row["accepted"] is True


@needs_core
def test_a_dry_run_writes_one_session_per_defect_and_records_the_o5_issue(tmp_path):
    assert ds.run(str(STUDY_ROOT), str(tmp_path), str(CORE), dry_run=True) == 0
    rows = [json.loads(l) for l in (tmp_path / "checkpoint.jsonl").read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 90
    for r in rows:
        assert len({c["session_id"] for c in r["conditions"]}) == 1
        assert (r["injected_issue"] is not None) == (r["operator"] == "O5")
