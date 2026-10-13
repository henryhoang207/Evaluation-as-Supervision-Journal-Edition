"""C7 design gates: allocation, truncation protection, repeat handling, provenance."""
import importlib.util
import copy
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND / "scripts"))
import c7_runtime as runtime
import c7_gates as gates
import run_injection_study as runner
import verify_c7

spec = importlib.util.spec_from_file_location("repair_analysis_c7", BACKEND / "scripts/analysis/repair_analysis.py")
analysis = importlib.util.module_from_spec(spec)
spec.loader.exec_module(analysis)


def test_frozen_core_and_c7_allocation():
    root = str(BACKEND / "out_study")
    assert runner.plan_summary(runner.build_plan(root))["trials"] == 1167
    plan = runner.build_plan(root, cell="c7")
    assert runner.verify_order(plan) == []
    s = runner.plan_summary(plan)
    assert s["defects_runnable"] == 142
    assert s["trials_by_arm"] == {"A1": 426, "A2": 426, "A3": 102}
    assert s["trials"] == 954
    assert sum(any(c["rep"] == 2 for c in d["arms"]) for d in plan) == 142


def test_context_exclusion_removes_a_whole_defect_without_reshuffling_subsets():
    root = str(BACKEND / "out_study")
    original = runner.build_plan(root, cell="c7")
    selected = next(d for d in original if d["runnable"])
    report = {"context": {"defects": {d["defect_id"]: {"eligible": d != selected}
                                      for d in original if d["runnable"]}}}
    plan = runner.build_plan(root, cell="c7", c7_gates=report)
    changed = next(d for d in plan if d["defect_id"] == selected["defect_id"])
    assert not changed["runnable"] and changed["arms"] == []
    assert runner.plan_summary(plan)["c7_context_excluded"] == 1
    assert [d["arms"] for d in plan if d["runnable"]] == [d["arms"] for d in original
                                                              if d["runnable"] and d != selected]


def test_c7_live_run_requires_passed_gates(tmp_path):
    with pytest.raises(ValueError, match="passed gates"):
        runner.run(str(BACKEND / "out_study"), str(tmp_path), 3, "P1", 0, False, cell="c7")


def test_runtime_blocks_oversized_correction_before_any_provider_call(monkeypatch):
    monkeypatch.setattr(runtime, "token_count", lambda _: runtime.CONTEXT)
    agent = SimpleNamespace()
    runtime.configure_agent(agent)
    with pytest.raises(ValueError, match="context_overflow"):
        agent._create(runtime.MODEL, [{"role": "user", "content": "correction"}])
    assert agent._c7_calls[0]["status"] == "context_overflow"


def test_runtime_records_raw_bytes_and_pins_decoding(monkeypatch):
    monkeypatch.setattr(runtime, "token_count", lambda _: 10)
    received = {}
    def create(**kwargs):
        received.update(kwargs)
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content='{"a": 1}'),
                                                       finish_reason="stop")],
                               usage=SimpleNamespace(prompt_tokens=10, completion_tokens=6))
    agent = SimpleNamespace(_client=SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create))))
    runtime.configure_agent(agent)
    agent._create(runtime.MODEL, [{"role": "user", "content": "task"}])
    assert received["seed"] == runtime.SEED and received["temperature"] == 0
    assert received["max_tokens"] == runtime.MAX_OUTPUT
    assert agent._c7_calls[0]["raw_output"] == '{"a": 1}'


def test_runtime_detects_silent_truncation(monkeypatch):
    monkeypatch.setattr(runtime, "token_count", lambda _: 1000)
    response = SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="{}"), finish_reason="stop")],
                               usage=SimpleNamespace(prompt_tokens=500, completion_tokens=1))
    agent = SimpleNamespace(_client=SimpleNamespace(chat=SimpleNamespace(
        completions=SimpleNamespace(create=lambda **kw: response))))
    runtime.configure_agent(agent)
    with pytest.raises(ValueError, match="truncation"):
        agent._create(runtime.MODEL, [])


def _trial(arm, rep, outcome, raw):
    return {"defect_id": "d:O1", "operator": "O1", "stage": "reasoning_agent", "arm": arm,
            "rep": rep, "status": "ok", "attempts_made": 1, "outcome": {"outcome": outcome},
            "local_calls": [{"status": "ok", "raw_sha256": raw}]}


def test_primary_averages_repetitions_per_defect_and_reports_raw_instability():
    ts = [_trial("A1", 0, "repaired", "raw-a"), _trial("A1", 1, "unrepaired", "raw-b"),
          _trial("A1", 2, "repaired", "raw-a"),
          _trial("A2", 0, "unrepaired", "raw-c"), _trial("A2", 1, "unrepaired", "raw-c"),
          _trial("A2", 2, "unrepaired", "raw-c")]
    result = analysis.analyse_c7([{"defect_id": "d:O1", "trials": ts}], seed=0)
    assert result["A1_minus_A2"]["estimate"] == pytest.approx(2 / 3)
    assert result["first_draw_only"]["A1_minus_A2"]["estimate"] == 1
    assert result["repeat_stability"]["A1"]["share_identical"] == 0
    assert result["repeat_stability"]["A2"]["share_identical"] == 1


def test_runtime_refuses_cloud_endpoint(monkeypatch):
    monkeypatch.setenv("OPENAI_BASE_URL", "https://example.com/v1")
    with pytest.raises(ValueError, match="localhost"):
        runtime.endpoint()


def test_schema_failure_sensitivity_does_not_count_network_failure_as_model_error():
    rows = [{"defect_id": "d:O1", "trials": [
        {**_trial("A1", 0, "repaired", "raw-a"), "status": "status_error",
         "error_type": "schema_validation_error"},
        _trial("A2", 0, "repaired", "raw-b"),
        {**_trial("A3", 0, "repaired", "raw-c"), "status": "status_error",
         "error_type": "api_error"}]}]
    result = analysis.analyse_c7(rows, seed=0)
    assert result["A1_minus_A2"]["n_defects"] == 0
    sensitive = result["schema_failure_sensitivity"]
    assert sensitive["failures_counted_unrepaired"] == 1
    assert sensitive["A1_minus_A2"]["estimate"] == -1
    assert sensitive["rates"]["A3"]["n_defects"] == 0


def _verification_fixture(tmp_path, monkeypatch):
    defect = copy.deepcopy(next(d for d in runner.build_plan(str(BACKEND / "out_study"), cell="c7")
                                if d["runnable"]))
    base = runner.inject_defects.state_from_dump(defect["dump_dir"])
    _, descriptor = runner.inject_defects.inject(defect["operator"], base, seed=0)
    trials = []
    for cell in defect["arms"]:
        trials.append({**cell, "session_id": "one-session", "status": "ok",
                       "served_models": [runtime.MODEL], "local_calls": [],
                       "retried_output": base[runner.inject_defects.OUTPUT_KEY[descriptor.stage]],
                       "outcome": runner.score_repair.score(descriptor, base, base).to_dict(),
                       "post_facts": gates.supervision.measure(descriptor.stage, base)})
    row = {"defect_id": defect["defect_id"], "status": "ok", "trials": trials}
    (tmp_path / "run_header.json").write_text(json.dumps({"gates": {}}))
    (tmp_path / "checkpoint.jsonl").write_text(json.dumps(row) + "\n")
    monkeypatch.setattr(verify_c7.runner, "build_plan", lambda *a, **kw: [defect])
    return row


def test_offline_verifier_reproduces_scores(tmp_path, monkeypatch):
    _verification_fixture(tmp_path, monkeypatch)
    result = verify_c7.verify("unused", str(tmp_path))
    assert result["passed"] and result["offline_scores_agree"] == 6


def test_measured_nondeterminism_is_not_misreported_as_bit_identity():
    measurement = {"pairs": 10, "passed": False, "identical": 8,
                   "items": [{"token_counter_agrees": True} for _ in range(10)]}
    assert gates.measured(measurement)
    measurement["items"][0]["token_counter_agrees"] = False
    assert not gates.measured(measurement)


@pytest.mark.parametrize("tamper", ["score", "session", "model", "cell"])
def test_offline_verifier_detects_corrupted_records(tmp_path, monkeypatch, tamper):
    row = _verification_fixture(tmp_path, monkeypatch)
    trial = row["trials"][0]
    if tamper == "score":
        trial["outcome"]["outcome"] = "unrepaired"
    elif tamper == "session":
        trial["session_id"] = "another-session"
    elif tamper == "model":
        trial["served_models"] = ["gemini-2.5-flash"]
    else:
        row["trials"].pop()
    (tmp_path / "checkpoint.jsonl").write_text(json.dumps(row) + "\n")
    assert not verify_c7.verify("unused", str(tmp_path))["passed"]
