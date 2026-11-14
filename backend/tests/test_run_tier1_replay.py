"""Tests for the Tier-1 replay runner (PREREGISTRATION.md section 0.1 A8)."""

import importlib.util
import json
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


t1 = _load_module("run_tier1_replay", "scripts/run_tier1_replay.py")

needs_study = pytest.mark.skipif(
    not (STUDY_ROOT / "A").is_dir(), reason="backend/out_study/ not present"
)


@needs_study
def test_every_usable_bank_defect_replays_its_recorded_retry_exactly():
    plan = t1.build_plan(str(STUDY_ROOT))
    s = t1.plan_summary(plan)
    assert s["defects_in_bank"] == s["defects_runnable"] == 13
    assert s["trials"] == 117 and s["cells"] == 7
    assert s["trials_by_arm"] == {"A1": 39, "A2": 39, "A3": 39}


def test_a_cell_is_business_id_by_stage_not_business_name():
    # Chains share names (two Wingstops are sampled); A14's stopping rule counts cells.
    w1 = {"defect_id": "A:w1:reasoning_agent:0", "business_id": "w1",
          "business_name": "Wingstop", "stage": "reasoning_agent"}
    w2 = {**w1, "defect_id": "A:w2:reasoning_agent:0", "business_id": "w2"}
    w1_rep = {**w1, "defect_id": "rep1:w1:reasoning_agent:0"}
    assert t1.cell_of(w1) != t1.cell_of(w2)
    assert t1.cell_of(w1) == t1.cell_of(w1_rep)
    assert t1.cell_of(w1) != t1.cell_of({**w1, "stage": "strategy_agent"})
    plan = [{"cell": t1.cell_of(e), "stage": e["stage"], "runnable": True, "arms": []}
            for e in (w1, w2, w1_rep)]
    assert t1.plan_summary(plan)["cells"] == 2
    with pytest.raises(ValueError):
        t1.cell_of({**w1, "business_id": None})


@needs_study
def test_tier1_runs_a1_a2_a3_at_p0_and_never_a0():
    for d in t1.build_plan(str(STUDY_ROOT)):
        assert {c["arm"] for c in d["arms"]} == {"A1", "A2", "A3"}
        assert all(c["placement"] == "P0" for c in d["arms"])


@needs_study
def test_the_original_defective_output_is_judged_unaccepted():
    for d in t1.build_plan(str(STUDY_ROOT)):
        state = t1.inject_defects.state_from_dump(d["dump_dir"])
        original = state[t1.inject_defects.OUTPUT_KEY[d["stage"]]]
        verdict = t1.judge(d, state, original)
        assert verdict["accepted"] is False and verdict["target_resolved"] is False


def _capturing(seen, output):
    class _Agent:
        def build_prompt(self, payload):
            return [{"role": "system", "content": "SYS"}, {"role": "user", "content": "TASK"}], "task"

        def run_messages(self, messages, task, payload=None):
            seen.setdefault("messages", []).append(messages)
            return output
    return _Agent()


@needs_study
def test_a1_at_p0_is_the_production_retry_and_a3_is_the_bare_prompt(monkeypatch):
    d = t1.build_plan(str(STUDY_ROOT))[0]
    state = t1.inject_defects.state_from_dump(d["dump_dir"])
    original = state[t1.inject_defects.OUTPUT_KEY[d["stage"]]]
    decision = t1.supervision.decide(d["stage"], t1.supervision.measure(d["stage"], state), {})
    seen = {}
    monkeypatch.setattr(t1.runner, "_agent_for", lambda stage: _capturing(seen, original))
    a1 = t1.run_trial(d, {"arm": "A1", "placement": "P0", "rep": 0}, state, decision, "s", False)
    a3 = t1.run_trial(d, {"arm": "A3", "placement": "P0", "rep": 0}, state, decision, "s", False)
    m1, m3 = seen["messages"]
    assert decision.retry_feedback in m1[-1]["content"]          # the feedback reaches A1
    artifact = json.dumps(original, ensure_ascii=False, indent=2)
    assert all(artifact not in m["content"] for m in m1)         # P0: no artifact
    assert len(m3) == 2                                          # A3: the stage prompt only
    assert a1["status"] == "ok" and a1["accepted"] is False and a1["same_as_original"] is True
    assert a3["arm"] == "A3"


@needs_study
def test_a_dry_run_writes_one_session_per_defect(tmp_path):
    assert t1.run(str(STUDY_ROOT), str(tmp_path), 3, dry_run=True, limit=2) == 0
    rows = [json.loads(l) for l in (tmp_path / "checkpoint.jsonl").read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 2
    for r in rows:
        assert len({t["session_id"] for t in r["trials"]}) == 1
        assert len(r["trials"]) == 9


@needs_study
def test_the_model_flag_pins_env_and_agent_and_defaults_to_off(tmp_path, monkeypatch):
    for name in ("OPENAI_MODEL", "OPENAI_FALLBACK_MODEL", "LLM_DISABLE_FALLBACK"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr(t1, "PINNED_MODEL", None)
    assert t1.run(str(STUDY_ROOT), str(tmp_path / "a"), 3, dry_run=True, limit=1) == 0
    assert t1.PINNED_MODEL is None and "OPENAI_MODEL" not in __import__("os").environ
    assert t1.run(str(STUDY_ROOT), str(tmp_path / "b"), 3, dry_run=True, limit=1,
                  model="gemini-2.5-flash") == 0
    import os
    assert t1.PINNED_MODEL == "gemini-2.5-flash"
    assert os.environ["OPENAI_MODEL"] == os.environ["OPENAI_FALLBACK_MODEL"] == "gemini-2.5-flash"
    assert os.environ["LLM_DISABLE_FALLBACK"] == "1"
