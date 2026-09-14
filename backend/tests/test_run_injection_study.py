"""Tests for the injection batch runner (JOURNAL_PLAN B7).

The gates that matter before any trial runs:

- ``--dry-run`` makes **zero** live calls and still enumerates the whole plan.
- Iteration order is defect-outer, with each defect's arms contiguous and in one
  session (section 14.1). Arm-outer would confound arm with serving epoch.
- Resume skips whole **defects**, never trials — a defect split across two
  sessions loses its matching.
- The D12 record carries the full retried output plus re-runnable downstream
  state, not just facts and a verdict.
"""

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


runner = _load_module("run_injection_study", "scripts/run_injection_study.py")
inject_defects = _load_module("inject_defects", "scripts/inject_defects.py")

needs_study = pytest.mark.skipif(
    not (STUDY_ROOT / "A").is_dir(), reason="backend/out_study/ not present"
)


@needs_study
def _plan():
    return runner.build_plan(str(STUDY_ROOT))


# ── ordering (section 14.1) ───────────────────────────────────────────────────


@needs_study
def test_iteration_order_is_defect_outer_with_contiguous_arms():
    """HARD GATE: arm-outer would confound arm with serving epoch."""
    assert runner.verify_order(runner.build_plan(str(STUDY_ROOT))) == []


@needs_study
def test_a_defect_holds_all_its_arms_rather_than_arms_holding_defects():
    plan = [d for d in runner.build_plan(str(STUDY_ROOT)) if d["runnable"]]
    assert plan
    for defect in plan:
        arms_seen = [c["arm"] for c in defect["arms"]]
        assert "A1" in arms_seen and "A2" in arms_seen
        # contiguity: an arm's repetitions never interleave with another's
        runs = [a for i, a in enumerate(arms_seen) if i == 0 or arms_seen[i - 1] != a]
        assert len(runs) == len(set(runs)), f"{defect['defect_id']} interleaves arms"


def test_verify_order_catches_an_arm_outer_rewrite():
    """The invariant must actually be able to fail."""
    bad = [{
        "defect_id": "d1", "applicable": True,
        "arms": [{"arm": "A1", "rep": 0}, {"arm": "A2", "rep": 0}, {"arm": "A1", "rep": 1}],
    }]
    assert any("not contiguous" in p for p in runner.verify_order(bad))


# ── D4c allocation ────────────────────────────────────────────────────────────


@needs_study
def test_arms_are_allocated_over_defects_not_over_repetitions():
    """D4c: A3 runs on a quarter of the defects at full reps, not on all at fewer."""
    plan = [d for d in runner.build_plan(str(STUDY_ROOT), reps=3) if d["runnable"]]
    with_a3 = [d for d in plan if any(c["arm"] == "A3" for c in d["arms"])]
    with_a1 = [d for d in plan if any(c["arm"] == "A1" for c in d["arms"])]

    assert len(with_a1) == len(plan), "A1 must run on every defect"
    assert 0 < len(with_a3) < len(plan), "A3 must run on a subset"
    # every defect that carries an arm carries its full repetitions
    for defect in with_a3:
        assert sum(1 for c in defect["arms"] if c["arm"] == "A3") == 3


def test_subset_selection_is_stable_under_growth():
    """A resumed run and a fresh run must agree on which defects carry A3.

    A seeded shuffle would reshuffle the assignment when a defect is added,
    which is why selection is a stride.
    """
    before = [runner._in_subset(i, 0.25) for i in range(20)]
    after = [runner._in_subset(i, 0.25) for i in range(40)][:20]
    assert before == after


@needs_study
def test_a3_runs_at_p0_and_never_elsewhere():
    """A3 stops being a bare re-draw the moment it is shown the artifact (D9b)."""
    for defect in runner.build_plan(str(STUDY_ROOT)):
        for cell in defect["arms"]:
            if cell["arm"] == "A3":
                assert cell["placement"] == "P0"
            if cell["arm"] == "A0":
                assert cell["placement"] != "P0"


@needs_study
def test_tier2_defaults_to_p1_not_the_production_placement():
    """D10: at P0 the injected defect never enters the model's context."""
    assert runner.DEFAULT_PLACEMENT == "P1"
    assert runner.DEFAULT_REPS == 3  # D4d


# ── dry run makes no calls ────────────────────────────────────────────────────


@needs_study
def test_dry_run_makes_no_llm_calls_and_needs_no_key(tmp_path, monkeypatch):
    """If this ever imports an agent, the guard has broken."""
    def explode(*a, **k):
        raise AssertionError("dry-run reached the LLM client")

    monkeypatch.setattr("app.core.llm_config.client_kwargs", explode, raising=False)
    rc = runner.run(str(STUDY_ROOT), str(tmp_path), reps=3, placement="P1",
                    seed=0, dry_run=True, limit=3)
    assert rc == 0

    rows = [json.loads(l) for l in
            (tmp_path / "checkpoint.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    assert rows
    for row in rows:
        for trial in row.get("trials", []):
            assert trial["status"] == "dry-run"
            assert trial["attempts_made"] == 0


@needs_study
def test_dry_run_still_records_the_pre_injection_measurement():
    """The whole measurement, not only the injected check (section 14.6)."""
    plan = [d for d in runner.build_plan(str(STUDY_ROOT)) if d["runnable"]]
    defect = plan[0]
    base = inject_defects.state_from_dump(defect["dump_dir"])
    injected, descriptor = inject_defects.inject(defect["operator"], base, seed=0)

    row = runner.run_trial(defect, defect["arms"][0], base, injected,
                           descriptor, "sess1", dry_run=True)

    assert row["pre_verdict"] == "retry"
    assert row["retry_feedback"]
    assert row["pre_facts"], "facts must be the full measurement"
    assert row["descriptor"]["check_class"] == descriptor.check_class


# ── resume ────────────────────────────────────────────────────────────────────


def test_resume_skips_whole_defects(tmp_path):
    path = str(tmp_path / "checkpoint.jsonl")
    runner.append_row(path, {"defect_id": "d1", "status": "ok"})
    runner.append_row(path, {"defect_id": "d2", "status": "skipped"})
    runner.append_row(path, {"defect_id": "d3", "status": "error"})
    done = runner.load_done(path)
    assert done == {"d1", "d2"}, "an errored defect must be retried, not skipped"


def test_a_torn_final_line_does_not_break_resume(tmp_path):
    path = tmp_path / "checkpoint.jsonl"
    path.write_text('{"defect_id": "d1", "status": "ok"}\n{"defect_id": "d2", "sta',
                    encoding="utf-8")
    assert runner.load_done(str(path)) == {"d1"}


# ── D12 ───────────────────────────────────────────────────────────────────────


# The seam was a deliberate NotImplementedError until 2026-08-25; the test that
# pinned it has been replaced by the four below, which pin what it now does.


def _reasoning_defect():
    """One applicable reasoning-stage defect, with its state and decision."""
    plan = [d for d in runner.build_plan(str(STUDY_ROOT))
            if d["runnable"] and inject_defects.STAGE[d["operator"]] == "reasoning_agent"]
    assert plan, "no applicable reasoning-stage defect in the bank"
    defect = plan[0]
    base = inject_defects.state_from_dump(defect["dump_dir"])
    injected, descriptor = inject_defects.inject(defect["operator"], base, seed=0)
    facts = runner.supervision.measure(descriptor.stage, injected)
    decision = runner.supervision.decide(descriptor.stage, facts, {})
    return defect, base, injected, descriptor, decision


def _capturing_agent(cls, seen):
    """A real agent with its real build_prompt, but no LLM client and no call."""
    agent = cls.__new__(cls)   # __init__ would open an OpenAI client

    def run_messages(messages, original_task, input_data=None):
        seen["messages"] = messages
        seen["task"] = original_task
        seen["payload"] = input_data
        return {"patterns": [], "root_causes": [], "status": "success", "error_detail": None}

    agent.run_messages = run_messages
    return agent


@needs_study
def test_the_live_seam_prompts_with_productions_own_message_list(monkeypatch):
    """An arm is a modification of the production prompt, not a lookalike.

    If the runner ever re-types a stage prompt, A1 vs A2 stops being a pure
    content contrast and this fails.
    """
    from app.agents.reasoning_agent import ReasoningAgent
    from app.core import nodes

    _, base, injected, descriptor, decision = _reasoning_defect()
    seen = {}
    monkeypatch.setattr(runner, "_agent_for",
                        lambda stage: _capturing_agent(ReasoningAgent, seen))

    runner._regenerate({"arm": "A1", "placement": "P1"}, base, injected, descriptor, decision)

    reference = ReasoningAgent.__new__(ReasoningAgent)
    expected, expected_task = reference.build_prompt(
        nodes.stage_payload("reasoning_agent", base))
    assert seen["messages"][:len(expected)] == expected
    assert seen["task"] == expected_task
    assert seen["payload"] == nodes.stage_payload("reasoning_agent", base)


@needs_study
def test_a1_carries_the_supervisors_own_measured_feedback(monkeypatch):
    from app.agents.reasoning_agent import ReasoningAgent

    _, base, injected, descriptor, decision = _reasoning_defect()
    assert decision.retry_feedback, "the injected defect must produce retry feedback"
    seen = {}
    monkeypatch.setattr(runner, "_agent_for",
                        lambda stage: _capturing_agent(ReasoningAgent, seen))

    runner._regenerate({"arm": "A1", "placement": "P1"}, base, injected, descriptor, decision)

    tail = "".join(m["content"] for m in seen["messages"][2:])
    assert decision.retry_feedback in tail


@needs_study
def test_the_retried_state_pins_upstream_and_clears_stale_downstream(monkeypatch):
    """The dump's downstream came from the PRE-injection output of this stage.

    Recording it under ``downstream_state`` (D12) would invite a later analysis
    to read a stale artifact as this trial's downstream.
    """
    from app.agents.reasoning_agent import ReasoningAgent

    _, base, injected, descriptor, decision = _reasoning_defect()
    before = json.dumps(base, sort_keys=True, ensure_ascii=False)
    monkeypatch.setattr(runner, "_agent_for",
                        lambda stage: _capturing_agent(ReasoningAgent, {}))

    retried = runner._regenerate({"arm": "A1", "placement": "P1"}, base, injected,
                                 descriptor, decision)

    assert retried["analysis_results"] == base["analysis_results"], "upstream must be pinned"
    assert retried["reasoning_output"]["status"] == "success"
    assert retried["strategy_output"] is None
    assert retried["report_output"] is None
    assert json.dumps(base, sort_keys=True, ensure_ascii=False) == before, "base was mutated"


def test_the_seam_refuses_a_stage_outside_the_replay_scope():
    """analysis_agent needs the sampled reviews, which a dump does not carry (D6)."""
    with pytest.raises(ValueError):
        runner._agent_for("analysis_agent")


@needs_study
def test_a_live_run_disables_the_silent_model_failover(tmp_path, monkeypatch):
    """A mid-comparison failover is indistinguishable from a slow call (B2)."""
    import os as _os

    from app.agents import base_agent

    monkeypatch.setattr(_os, "environ", dict(_os.environ))
    _os.environ.pop(base_agent.FALLBACK_DISABLED_ENV, None)
    monkeypatch.setattr(runner, "build_plan", lambda *a, **k: [])

    rc = runner.run(str(STUDY_ROOT), str(tmp_path), reps=1, placement="P1",
                    seed=0, dry_run=False)

    assert rc == 0
    assert base_agent.fallback_disabled(), "a live run must not fail over silently"


def test_d12_downstream_fields_are_in_the_record_shape():
    """Persisting these on the first pass is nearly free; recovering costs a re-run."""
    source = (BACKEND / "scripts" / "run_injection_study.py").read_text(encoding="utf-8")
    for field in ("retried_output", "downstream_state", "attempts_made",
                  "served_models", "post_verdict", "post_facts"):
        assert f'"{field}"' in source or f"{field}=" in source, field


# ── failure handling on resume ────────────────────────────────────────────────


@needs_study
def test_a_defect_whose_trials_failed_is_not_marked_done(tmp_path, monkeypatch):
    """Otherwise resume skips it for good and the defect leaves the sample silently.

    This is more likely now than it was: live runs disable model failover, so a
    provider problem surfaces rather than being papered over.
    """
    def explode(*a, **k):
        raise RuntimeError("seam blew up")

    monkeypatch.setattr(runner, "_regenerate", explode)
    monkeypatch.setattr(runner, "_agent_for", lambda stage: None)

    plan = [d for d in runner.build_plan(str(STUDY_ROOT)) if d["runnable"]][:1]
    monkeypatch.setattr(runner, "build_plan", lambda *a, **k: plan)

    rc = runner.run(str(STUDY_ROOT), str(tmp_path), reps=1, placement="P1",
                    seed=0, dry_run=False)
    assert rc == 0

    path = str(tmp_path / "checkpoint.jsonl")
    rows = [json.loads(l) for l in
            (tmp_path / "checkpoint.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    assert rows and rows[-1]["status"] == "error"
    assert rows[-1]["n_failed"] == rows[-1]["n_trials"]
    assert runner.load_done(path) == set(), "a failed defect must be retried on resume"


@needs_study
def test_a_provider_failure_is_data_and_does_not_force_a_rerun(tmp_path, monkeypatch):
    """status_error is the pre-registered exclusion. Re-running it until it
    succeeds would be resampling on the outcome."""
    plan = [d for d in runner.build_plan(str(STUDY_ROOT)) if d["runnable"]][:1]
    monkeypatch.setattr(runner, "build_plan", lambda *a, **k: plan)
    monkeypatch.setattr(
        runner, "run_trial",
        lambda *a, **k: {"arm": "A1", "status": "status_error", "attempts_made": 1})

    runner.run(str(STUDY_ROOT), str(tmp_path), reps=1, placement="P1",
               seed=0, dry_run=False)

    rows = [json.loads(l) for l in
            (tmp_path / "checkpoint.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    assert rows[-1]["status"] == "ok"
    assert runner.load_done(str(tmp_path / "checkpoint.jsonl")) == {plan[0]["defect_id"]}


# ── D20: the injection-validity and trigger gates ─────────────────────────────
#
# Both are pure measure()/decide(), so they belong in build_plan where a failure
# removes the defect before money is spent and shows up in --plan-only. They
# were specified on 2026-09-02 and wired on 2026-09-08; verify_injection had
# existed, unwired, since the injector was written.


@needs_study
def test_every_runnable_defect_cleared_both_gates():
    """The gates ran, and the plan records what they saw — not just a boolean."""
    plan = runner.build_plan(str(STUDY_ROOT))
    runnable = [d for d in plan if d["runnable"]]
    assert runnable

    for d in runnable:
        assert d["injection_valid"] is True
        assert d["triggers"] is True
        assert d["gate"]["target_fired"] is True
        assert d["gate"]["collateral_classes"] == [], d["defect_id"]
        assert d["gate"]["verdict"] == "retry"
        assert d["reason"] is None


@needs_study
def test_a_gated_out_defect_carries_no_arms_and_states_why():
    """An inapplicable defect must not silently reach the runner with arms."""
    for d in runner.build_plan(str(STUDY_ROOT)):
        if d["runnable"]:
            continue
        assert d["arms"] == []
        assert d["reason"], f"{d['defect_id']} was excluded without a reason"


@needs_study
def test_plan_summary_reports_each_gate_against_its_own_denominator():
    """D20: injection success rate and trigger rate are two numbers, not one.

    Pooling them into a single 'yield' would hide which gate moved.
    """
    s = runner.plan_summary(runner.build_plan(str(STUDY_ROOT)))

    assert s["defects_applicable"] + s["defects_inapplicable"] == s["defects_planned"]
    assert s["injection_verified"] + s["injection_failed"] == s["defects_applicable"]
    assert s["triggered"] + s["untriggered"] == s["injection_verified"]
    assert s["defects_runnable"] == s["triggered"]
    # rates are over their own denominator, not over defects_planned
    assert s["injection_success_rate"] == round(
        s["injection_verified"] / s["defects_applicable"], 4)
    assert s["trigger_rate"] == round(s["triggered"] / s["injection_verified"], 4)


def test_plan_summary_rates_are_none_rather_than_zero_on_an_empty_plan():
    """0/0 is undefined, and reporting it as 0.0 would read as total failure."""
    s = runner.plan_summary([])
    assert s["injection_success_rate"] is None
    assert s["trigger_rate"] is None
    assert s["defects_runnable"] == 0


@needs_study
def test_a_defect_whose_injection_does_not_fire_is_excluded_and_counted(monkeypatch):
    """The gate must be able to fail — otherwise it is decoration."""
    monkeypatch.setattr(
        inject_defects, "verify_injection",
        lambda op, injected, base: (False, {
            "target_fired": False, "collateral_classes": [],
            "classes_before": [], "classes_after": [], "verdict": "proceed"}))
    monkeypatch.setattr(runner.inject_defects, "verify_injection",
                        inject_defects.verify_injection)

    plan = runner.build_plan(str(STUDY_ROOT))
    s = runner.plan_summary(plan)

    assert s["defects_applicable"] > 0
    assert s["injection_verified"] == 0
    assert s["injection_success_rate"] == 0.0
    assert s["defects_runnable"] == 0 and s["trials"] == 0
    # the trigger rate is undefined, not 0 -- nothing survived to be triggered
    assert s["trigger_rate"] is None
    assert all(d["reason"] == "injection_did_not_fire"
               for d in plan if d["applicable"])


@needs_study
def test_a_defect_the_supervisor_does_not_route_to_retry_is_excluded(monkeypatch):
    """Section 14.3, settled: excluded from the denominator and counted
    separately -- never scored ``unrepaired``.

    Scoring it would score the arms on a trial where every arm is identical by
    construction: with no retry there is no feedback, so A1, A2 and A3 differ in
    nothing at all.
    """
    real = inject_defects.verify_injection

    def no_retry(op, injected, base):
        ok, detail = real(op, injected, base)
        return ok, {**detail, "verdict": "proceed_with_warning"}

    monkeypatch.setattr(runner.inject_defects, "verify_injection", no_retry)

    plan = runner.build_plan(str(STUDY_ROOT))
    s = runner.plan_summary(plan)

    assert s["injection_verified"] == s["defects_applicable"] > 0
    assert s["injection_success_rate"] == 1.0
    assert s["triggered"] == 0 and s["trigger_rate"] == 0.0
    assert s["untriggered"] == s["injection_verified"]
    assert s["trials"] == 0
    assert all(d["reason"] == "no_retry_verdict:proceed_with_warning"
               for d in plan if d["injection_valid"])


@needs_study
def test_verify_order_does_not_flag_gated_out_defects(monkeypatch):
    """A gated-out defect has no arms by design; that is not an order violation."""
    monkeypatch.setattr(
        runner.inject_defects, "verify_injection",
        lambda op, injected, base: (False, {
            "target_fired": False, "collateral_classes": [],
            "classes_before": [], "classes_after": [], "verdict": "proceed"}))

    assert runner.verify_order(runner.build_plan(str(STUDY_ROOT))) == []


@needs_study
def test_the_arm_stride_counts_only_defects_that_cleared_the_gates():
    """A0/A3 are allocated over a stride of the *runnable* defects (D4c).

    If the counter advanced on gated-out defects too, the stride would carry
    holes and the subsets would stop being evenly spread.
    """
    plan = [d for d in runner.build_plan(str(STUDY_ROOT), reps=3) if d["runnable"]]
    by_op: dict[str, list[bool]] = {}
    for d in plan:
        by_op.setdefault(d["operator"], []).append(
            any(c["arm"] == "A3" for c in d["arms"]))

    for op, flags in by_op.items():
        expected = [runner._in_subset(i, runner.ARM_FRACTION["A3"])
                    for i in range(len(flags))]
        assert flags == expected, f"{op}: A3 allocation is not a clean stride"


@needs_study
def test_the_gates_are_free_and_run_before_the_runner_spends_anything(monkeypatch):
    """They must sit in build_plan, not run(): a failure has to remove the
    defect before its arms are paid for, and has to be visible in --plan-only."""
    def explode(*a, **k):
        raise AssertionError("build_plan reached the LLM client")

    monkeypatch.setattr("app.core.llm_config.client_kwargs", explode, raising=False)
    plan = runner.build_plan(str(STUDY_ROOT))

    assert any(d["gate"] for d in plan), "no gate detail recorded"
    source = (BACKEND / "scripts" / "run_injection_study.py").read_text(encoding="utf-8")
    gate_call = source.index("verify_injection(op, injected, state)")
    assert gate_call < source.index("def run("), "the gate must run before run()"
