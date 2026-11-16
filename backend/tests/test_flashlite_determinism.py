"""A15 calibration: deterministic selection, raw receipts, accounting and gate wiring."""
import copy
import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

BACKEND = Path(__file__).resolve().parents[1]
for p in (BACKEND, BACKEND / "scripts"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
import flashlite_determinism as measure
from app.agents.base_agent import BaseAgent


def plan(pairs=2):
    return [{"pair_id": f"pair-{i}", "defect_id": f"pair-{i}::D{slot}", "slot": slot,
             "operator": "O1", "stage": "reasoning_agent", "bases_sha256": "synthetic-base",
             "prompt_sha256": measure.sha(f"prompt-{i}"), "prompt_bytes": 20,
             "messages": [{"role": "user", "content": f"prompt-{i}"}],
             "runnable": True, "arms": [{"measurement": "determinism", "slot": slot}]}
            for i in range(pairs) for slot in (1, 2)]


def read_rows(out):
    return [json.loads(s) for s in (out / "checkpoint.jsonl").read_text(encoding="utf-8").splitlines()]


class FakeAgent:
    temperature = 0.0
    reasoning_effort = None

    def __init__(self, responses=None, error=None, served=measure.MODEL):
        self.responses = iter(responses or ['{ "a": 1 }', '{"a":1}'])
        self.error, self.served, self.calls = error, served, 0

    def _create(self, model, messages):
        self.calls += 1
        assert model == measure.MODEL
        if self.error:
            raise self.error
        return SimpleNamespace(model=self.served, usage=SimpleNamespace(
            total_tokens=10, prompt_tokens=6, completion_tokens=4),
            choices=[SimpleNamespace(message=SimpleNamespace(content=next(self.responses)))])

    def _record_usage(self, *args, **kwargs):
        BaseAgent._record_usage(self, *args, **kwargs)


def factory_list(**kwargs):
    agents = []
    def factory(stage):
        a = FakeAgent(**kwargs)
        agents.append(a)
        return a
    return agents, factory


def test_selection_is_operator_balanced_longest_first_and_order_independent():
    candidates = [{"operator": op, "pair_id": f"{op}-{i}", "prompt_bytes": i,
                   "prompt_sha256": f"{op}-{i}"} for op in ("O1", "O2", "O3") for i in range(4)]
    chosen = measure.select_prompts(candidates, 6)
    assert [c["pair_id"] for c in chosen] == ['O1-3','O2-3','O3-3','O1-2','O2-2','O3-2']
    assert chosen == measure.select_prompts(list(reversed(candidates)), 6)
    duplicate = {**candidates[0], "pair_id": "long-duplicate", "prompt_bytes": 100}
    chosen = measure.select_prompts(candidates + [duplicate], 10)
    assert len({c["prompt_sha256"] for c in chosen}) == 10
    with pytest.raises(ValueError, match="distinct real prompts"):
        measure.select_prompts(candidates, 20)


def test_prompt_rendering_matches_production_regeneration_without_sdk(monkeypatch):
    import run_injection_study as runner  # another test module may reload it
    from app.agents import base_agent
    from app.core import supervision
    def forbidden(**kwargs):
        raise AssertionError("offline prompt assembly must not create an HTTP client")
    monkeypatch.setattr(base_agent, "OpenAI", forbidden)
    found = set()
    for d in runner.build_plan("out_study", cell="core"):
        if not d["runnable"]:
            continue
        actual = measure.assemble(d)
        stage = actual["stage"]
        if stage in found:
            continue
        found.add(stage)
        base = runner.inject_defects.state_from_dump(d["dump_dir"])
        injected, descriptor = runner.inject_defects.inject(d["operator"], base, seed=d["seed"])
        decision = supervision.decide(stage, supervision.measure(stage, injected), {})
        module, name = runner.STAGE_AGENT[stage]
        cls = getattr(__import__(module, fromlist=[name]), name)
        agent = object.__new__(cls)
        captured = []
        agent.run_messages = lambda messages, *args: captured.append(messages) or {}
        monkeypatch.setattr(runner, "_agent_for", lambda stage: agent)
        runner._regenerate({"arm":"A1","placement":"P1","condition":"C0"}, base,
                           injected, descriptor, decision, defect_cell="flashlite")
        assert captured == [actual["messages"]]
        if len(found) == 3:
            break
    assert len(found) == 3


def test_live_agent_pins_both_layers_omits_reasoning_and_disables_sdk_retries(monkeypatch):
    import run_injection_study as runner  # patch the instance used by the collector
    from app.agents.reasoning_agent import ReasoningAgent
    for k in ("OPENAI_MODEL", "OPENAI_FALLBACK_MODEL", "LLM_DISABLE_FALLBACK"):
        monkeypatch.setenv(k, "wrong")
    requests, options = [], []
    receipt = SimpleNamespace(model=measure.MODEL, usage=SimpleNamespace(
        total_tokens=10, prompt_tokens=6, completion_tokens=4),
        choices=[SimpleNamespace(message=SimpleNamespace(content='{}'))])
    client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(
        create=lambda **kw: requests.append(kw) or receipt)))
    client.with_options = lambda **kw: options.append(kw) or client
    agent = object.__new__(ReasoningAgent)
    agent._client = client
    monkeypatch.setattr(runner, "_agent_for", lambda stage: agent)
    agent = measure.new_agent("reasoning_agent")
    call = measure.call_once(agent, [{"role":"user","content":"synthetic"}], "session")
    assert options == [{"max_retries":0}]
    assert agent._model == agent._fallback_model == measure.MODEL
    assert requests[0]["model"] == measure.MODEL and requests[0]["temperature"] == 0
    assert "reasoning_effort" not in requests[0]
    assert call["served_models"] == [measure.MODEL] and call["total_tokens"] == 10
    import os
    assert os.environ["OPENAI_MODEL"] == os.environ["OPENAI_FALLBACK_MODEL"] == measure.MODEL
    assert os.environ["LLM_DISABLE_FALLBACK"] == "1"


def test_raw_and_canonical_identity_are_distinct_and_resume_does_not_reissue(tmp_path):
    agents, factory = factory_list()
    p = plan()
    measure.collect(p, tmp_path, agent_factory=factory)
    rows = read_rows(tmp_path)
    report = measure.verify_measurements(rows, p)
    assert not report["problems"]
    assert report["raw_identical_pairs"] == 0 and report["canonical_identical_pairs"] == 2
    assert report["valid_raw_pairs"] == report["valid_json_pairs"] == 2
    assert len(rows) == 8 and report["tokens"] == 40
    assert sum(a.calls for a in agents) == 4
    measure.collect(p, tmp_path, agent_factory=lambda s: pytest.fail("must not reissue"))
    assert read_rows(tmp_path) == rows
    assert all(not {"repaired", "restored", "post_facts"} & set(t) for r in rows for t in r.get("trials", []))
    changed = copy.deepcopy(p)
    changed[0]["prompt_sha256"] = "changed"
    with pytest.raises(ValueError, match="changed"):
        measure.collect(changed, tmp_path, agent_factory=factory)


def test_errors_are_reported_without_false_identity_or_replacements(tmp_path):
    agents, factory = factory_list(error=RuntimeError("synthetic provider error"))
    measure.collect(plan(), tmp_path, agent_factory=factory)
    report = measure.verify_measurements(read_rows(tmp_path), plan())
    assert not report["problems"]
    assert report["status"] == {"error":4}
    assert report["valid_raw_pairs"] == report["raw_identical_pairs"] == 0
    assert all(item["raw_identical"] is None for item in report["items"])
    measure.collect(plan(), tmp_path, agent_factory=lambda s: pytest.fail("must not replace errors"))


def test_identical_invalid_json_is_raw_identity_only(tmp_path):
    agents, factory = factory_list(responses=['invalid', 'invalid'])
    measure.collect(plan(1), tmp_path, agent_factory=factory)
    result = measure.verify_measurements(read_rows(tmp_path), plan(1))
    assert not result["problems"]
    assert result["raw_identical_pairs"] == 1 and result["valid_json_pairs"] == 0
    assert result["invalid_json_calls"] == 2


def test_interrupted_request_is_never_silently_issued_again(tmp_path):
    _, factory = factory_list(error=KeyboardInterrupt())
    with pytest.raises(KeyboardInterrupt):
        measure.collect(plan(), tmp_path, agent_factory=factory)
    assert read_rows(tmp_path)[0]["status"] == "started"
    with pytest.raises(ValueError, match="Unfinished request"):
        measure.collect(plan(), tmp_path, agent_factory=lambda s: pytest.fail("must preserve interruption"))


def test_wrong_model_stops_collection_and_fails_provenance(tmp_path):
    _, factory = factory_list(served='gemini-2.5-flash')
    with pytest.raises(ValueError, match="Wrong served model"):
        measure.collect(plan(), tmp_path, agent_factory=factory)
    assert any("wrong served model" in p for p in measure.verify_measurements(read_rows(tmp_path), plan())["problems"])


def test_dry_receipts_cannot_become_real_measurements(tmp_path):
    measure.collect(plan(), tmp_path, dry_run=True, agent_factory=lambda s: pytest.fail("no SDK"))
    rows = read_rows(tmp_path)
    assert any("dry-run" in p for p in measure.verify_measurements(rows, plan())["problems"])
    assert not measure.verify_measurements(rows, plan(), allow_dry_run=True)["problems"]


def test_duplicate_completions_corruption_and_cross_session_pairs_fail(tmp_path):
    _, factory = factory_list()
    measure.collect(plan(), tmp_path, agent_factory=factory)
    rows = read_rows(tmp_path)
    assert "duplicate completed request slots" in measure.verify_measurements(rows + [rows[-1]], plan())["problems"]
    bad = copy.deepcopy(rows)
    bad[-1]["trials"][0]["raw_sha256"] = "corrupt"
    assert any("hash mismatch" in p for p in measure.verify_measurements(bad, plan())["problems"])
    bad = copy.deepcopy(rows)
    bad[-1]["session_id"] = bad[-1]["trials"][0]["session_id"] = "other-session"
    assert any("spans sessions" in p for p in measure.verify_measurements(bad, plan())["problems"])


def test_cell_gate_writes_and_reproduces_measurement_analysis(tmp_path, monkeypatch):
    # Load the gate in its normal registry; preserve the preparation-only flag.
    import cell
    from dataclasses import replace
    spec = replace(cell.CELLS["flashlite_determinism"], out=str(tmp_path))
    p = plan()
    _, factory = factory_list()
    measure.collect(p, tmp_path, agent_factory=factory)
    monkeypatch.setattr(cell, "build_plan", lambda s:p)
    report = cell.run_verify(spec)
    assert not report["problems"]
    assert cell.write_analysis(spec)[0]
    assert cell.write_analysis(spec)[0]
    (tmp_path / "manifest.json").write_text('{}', encoding='utf-8')
    assert any("manifest" in x for x in cell.run_verify(spec)["problems"])
