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


# ── D8/D8d: the constraint-completeness cell ──────────────────────────────────
#
# Wired 2026-09-20, after the prereg-freeze tag. The gate that matters most is
# the first one: the frozen core must not move because the cell now exists.


@needs_study
def test_the_frozen_core_is_unchanged_when_the_c1_cell_is_not_asked_for():
    """HARD GATE: 1,167 C0 trials, exactly as the pre-registration froze them.

    The C1 cell is a post-freeze addition. A default that quietly added 222
    trials to the core would spend budget the freeze did not cover and would
    make --plan-only stop agreeing with PREREGISTRATION.md.
    """
    s = runner.plan_summary(runner.build_plan(str(STUDY_ROOT)))
    assert s["trials"] == s["core_trials"] == 1167
    assert s["c1_trials"] == 0 and s["defects_c1"] == 0
    assert set(s["trials_by_condition"]) == {"C0"}


@needs_study
def test_the_c1_cell_is_a1_and_a2_only_at_full_repetitions():
    """D8d: the cell asks whether the A1-vs-A2 gap survives disclosure."""
    plan = [d for d in runner.build_plan(str(STUDY_ROOT), with_c1=True) if d["runnable"]]
    carrying = [d for d in plan
                if any(c["condition"] == "C1" for c in d["arms"])]
    assert carrying

    for defect in carrying:
        c1 = [c for c in defect["arms"] if c["condition"] == "C1"]
        assert {c["arm"] for c in c1} == set(runner.C1_ARMS)
        for arm in runner.C1_ARMS:
            assert sum(1 for c in c1 if c["arm"] == arm) == 3
        # D10: the cell runs at the Tier-2 placement, like the core
        assert all(c["placement"] == "P1" for c in c1)


@needs_study
def test_the_c1_cell_realises_the_size_the_plan_documents():
    """37 defects and 222 trials, not D8d's round 40/240 — per-operator floors.

    Pinned rather than rounded: if the bank grows and this moves, the number in
    PREREGISTRATION.md section 0.1 has to move with it.
    """
    s = runner.plan_summary(runner.build_plan(str(STUDY_ROOT), with_c1=True))
    assert s["defects_c1"] == 37
    assert s["c1_trials"] == 222
    assert s["core_trials"] == 1167
    assert s["trials"] == 1167 + 222
    assert s["trials_by_cell"]["C1:A1"] == s["trials_by_cell"]["C1:A2"] == 111


@needs_study
def test_the_c1_subset_is_stratified_by_operator():
    """A subset falling in a block would confound the condition with operator."""
    plan = [d for d in runner.build_plan(str(STUDY_ROOT), with_c1=True) if d["runnable"]]
    by_op: dict[str, list[bool]] = {}
    for d in plan:
        by_op.setdefault(d["operator"], []).append(
            any(c["condition"] == "C1" for c in d["arms"]))

    assert len(by_op) > 1
    for op, flags in by_op.items():
        assert any(flags), f"{op} carries no C1 defect at all"
        expected = [runner._in_subset(i, runner.C1_FRACTION) for i in range(len(flags))]
        assert flags == expected, f"{op}: the C1 allocation is not a clean stride"


@needs_study
def test_the_c1_cell_shares_the_defect_and_therefore_the_session():
    """D8b option (ii): C0 and C1 see the identical injected base.

    The cells are appended to the defect's own block, so the C0-vs-C1 contrast
    is matched within a defect exactly as arm-vs-arm is, and both run inside the
    one session id (section 14.1).
    """
    plan = [d for d in runner.build_plan(str(STUDY_ROOT), with_c1=True) if d["runnable"]]
    carrying = [d for d in plan if any(c["condition"] == "C1" for c in d["arms"])][0]

    conditions = [c["condition"] for c in carrying["arms"]]
    assert conditions == sorted(conditions, key=lambda c: c != "C0"), \
        "the C1 cells must be one trailing block, not interleaved with the core"
    assert conditions.count("C1") == 6


@needs_study
def test_adding_the_c1_cell_leaves_the_core_cells_byte_identical():
    """The cell must extend the plan, never perturb it."""
    core = runner.build_plan(str(STUDY_ROOT))
    both = runner.build_plan(str(STUDY_ROOT), with_c1=True)
    assert len(core) == len(both)

    for a, b in zip(core, both):
        assert a["defect_id"] == b["defect_id"]
        assert a["arms"] == [c for c in b["arms"] if c["condition"] == "C0"]


@needs_study
def test_order_holds_with_the_c1_cell_attached():
    """Contiguity is per (condition, arm): C1 re-runs A1 and A2 legitimately."""
    assert runner.verify_order(runner.build_plan(str(STUDY_ROOT), with_c1=True)) == []


def test_verify_order_catches_an_interleaved_c1_cell():
    """The relaxed key must not have relaxed the invariant it protects."""
    bad = [{
        "defect_id": "d1", "applicable": True,
        "arms": [
            {"arm": "A1", "condition": "C0", "rep": 0},
            {"arm": "A1", "condition": "C1", "rep": 0},
            {"arm": "A1", "condition": "C0", "rep": 1},
            {"arm": "A2", "condition": "C0", "rep": 0},
        ],
    }]
    assert any("not contiguous" in p for p in runner.verify_order(bad))


def test_verify_order_catches_a_half_populated_c1_cell():
    """One arm under C1 yields no C0-vs-C1 contrast for that defect."""
    bad = [{
        "defect_id": "d1", "applicable": True,
        "arms": [
            {"arm": "A1", "condition": "C0", "rep": 0},
            {"arm": "A2", "condition": "C0", "rep": 0},
            {"arm": "A1", "condition": "C1", "rep": 0},
        ],
    }]
    assert any("C1 cell is not" in p for p in runner.verify_order(bad))


@needs_study
def test_the_trial_row_records_the_condition():
    """Unrecorded, a C1 trial is indistinguishable from a core one in the data."""
    plan = [d for d in runner.build_plan(str(STUDY_ROOT), with_c1=True) if d["runnable"]]
    defect = [d for d in plan if any(c["condition"] == "C1" for c in d["arms"])][0]
    base = inject_defects.state_from_dump(defect["dump_dir"])
    injected, descriptor = inject_defects.inject(defect["operator"], base, seed=0)

    c1_cell = [c for c in defect["arms"] if c["condition"] == "C1"][0]
    row = runner.run_trial(defect, c1_cell, base, injected, descriptor, "s", dry_run=True)
    assert row["condition"] == "C1"

    c0_cell = [c for c in defect["arms"] if c["condition"] == "C0"][0]
    row = runner.run_trial(defect, c0_cell, base, injected, descriptor, "s", dry_run=True)
    assert row["condition"] == "C0"


@needs_study
def test_the_c1_seam_states_the_constraints_in_productions_own_prompt(monkeypatch):
    """The live seam must carry C1 into the system turn — and only there.

    This is the one that would fail silently: a runner that dropped the
    condition on the floor would still produce rows labelled C1.
    """
    from app.agents.reasoning_agent import ReasoningAgent

    arms_mod = runner.arms_mod
    _, base, injected, descriptor, decision = _reasoning_defect()

    seen_c0, seen_c1 = {}, {}
    monkeypatch.setattr(runner, "_agent_for",
                        lambda stage: _capturing_agent(ReasoningAgent, seen_c0))
    runner._regenerate({"arm": "A1", "placement": "P1", "condition": "C0"},
                       base, injected, descriptor, decision)
    monkeypatch.setattr(runner, "_agent_for",
                        lambda stage: _capturing_agent(ReasoningAgent, seen_c1))
    runner._regenerate({"arm": "A1", "placement": "P1", "condition": "C1"},
                       base, injected, descriptor, decision)

    block = arms_mod.constraint_block("reasoning_agent")
    assert block not in seen_c0["messages"][0]["content"]
    assert block in seen_c1["messages"][0]["content"]
    assert seen_c1["messages"][0]["content"].rstrip().endswith(arms_mod.C1_CLOSING)
    # everything downstream of the system turn is untouched by the condition
    assert seen_c0["messages"][1:] == seen_c1["messages"][1:]


@needs_study
def test_a_cell_without_a_condition_key_still_runs_as_c0(monkeypatch):
    """Resuming a checkpoint written before factor C existed must not crash."""
    from app.agents.reasoning_agent import ReasoningAgent

    _, base, injected, descriptor, decision = _reasoning_defect()
    seen = {}
    monkeypatch.setattr(runner, "_agent_for",
                        lambda stage: _capturing_agent(ReasoningAgent, seen))

    runner._regenerate({"arm": "A1", "placement": "P1"}, base, injected,
                       descriptor, decision)
    assert runner.arms_mod.C1_PREAMBLE not in seen["messages"][0]["content"]


# ── the post-core passes (PREREGISTRATION.md section 0.1 A2, A3) ─────────────


@needs_study
def test_the_default_pass_is_still_the_frozen_core():
    """HARD GATE: adding passes must not move the 1,167-trial core."""
    s = runner.plan_summary(runner.build_plan(str(STUDY_ROOT), cell="core"))
    assert s["trials"] == s["core_trials"] == 1167
    assert s["not_in_pass"] == 0


@needs_study
def test_the_c1_pass_runs_the_same_37_defects_the_c1_flag_selects():
    flagged = {d["defect_id"] for d in runner.build_plan(str(STUDY_ROOT), with_c1=True)
               if any(c["condition"] == "C1" for c in d["arms"])}
    c1_pass = {d["defect_id"] for d in runner.build_plan(str(STUDY_ROOT), cell="c1")
               if d["runnable"]}
    assert c1_pass == flagged and len(c1_pass) == 37


@needs_study
def test_the_c1_pass_matches_c0_and_c1_inside_one_defect():
    """Section 14.1: the C0 comparator runs in the same session as C1."""
    plan = [d for d in runner.build_plan(str(STUDY_ROOT), cell="c1") if d["runnable"]]
    for d in plan:
        cells = [(c["condition"], c["arm"]) for c in d["arms"]]
        assert cells == ([("C0", "A1")] * 3 + [("C0", "A2")] * 3
                         + [("C1", "A1")] * 3 + [("C1", "A2")] * 3)
        assert all(c["placement"] == "P1" for c in d["arms"])
    s = runner.plan_summary(runner.build_plan(str(STUDY_ROOT), cell="c1"))
    assert s["trials"] == 444 and s["c1_trials"] == 222
    assert s["untriggered"] == 0 and s["not_in_pass"] == 105
    assert runner.verify_order(runner.build_plan(str(STUDY_ROOT), cell="c1")) == []


@needs_study
def test_the_d19_pass_is_o4_with_a1_at_p1_and_a3_at_p0():
    plan = runner.build_plan(str(STUDY_ROOT), cell="d19")
    runnable = [d for d in plan if d["runnable"]]
    assert {d["operator"] for d in plan} == {"O4"}
    assert len(runnable) == 23                      # PREREGISTRATION.md section 7
    for d in runnable:
        assert [(c["arm"], c["placement"]) for c in d["arms"]] == (
            [("A1", "P1")] * 3 + [("A3", "P0")] * 3)
    assert runner.verify_order(plan) == []
    assert runner.plan_summary(plan)["trials"] == 138


@needs_study
def test_the_d19_gate_requires_the_warning_production_overwrites():
    """D19 inverts the trigger: O4 must reach proceed_with_warning, not retry."""
    for d in runner.build_plan(str(STUDY_ROOT), cell="d19"):
        if d["runnable"]:
            assert d["gate"]["verdict"] == "proceed_with_warning"


def test_d19_routes_only_the_frequency_flags_into_the_feedback():
    decision = runner.supervision.Decision(
        "proceed_with_warning",
        ["frequency_corrected:food:0.6->0.30", "low_confidence:n=12",
         "frequency_corrected:service:0.5->0.20"])
    routed = runner.d19_decision(decision)
    assert routed.verdict == "retry"
    assert routed.retry_feedback == (
        "frequency_corrected:food:0.6->0.30 | frequency_corrected:service:0.5->0.20")
    # production's own decision object is left alone
    assert decision.verdict == "proceed_with_warning" and decision.retry_feedback is None


def test_d19_leaves_a_decision_without_frequency_flags_unchanged():
    decision = runner.supervision.Decision("proceed")
    assert runner.d19_decision(decision) is decision


@needs_study
def test_a_d19_trial_records_productions_verdict_and_the_routed_feedback():
    defect = [d for d in runner.build_plan(str(STUDY_ROOT), cell="d19") if d["runnable"]][0]
    base = inject_defects.state_from_dump(defect["dump_dir"])
    injected, descriptor = inject_defects.inject("O4", base, seed=0)
    row = runner.run_trial(defect, defect["arms"][0], base, injected, descriptor,
                           "s", dry_run=True)
    assert row["pre_verdict"] == "proceed_with_warning"
    assert row["retry_feedback"].startswith("frequency_corrected:")
    assert row["cell"] == "d19"


@needs_study
def test_the_d19_a1_prompt_carries_the_measured_frequency(monkeypatch):
    from app.agents.reasoning_agent import ReasoningAgent

    defect = [d for d in runner.build_plan(str(STUDY_ROOT), cell="d19") if d["runnable"]][0]
    base = inject_defects.state_from_dump(defect["dump_dir"])
    injected, descriptor = inject_defects.inject("O4", base, seed=0)
    decision = runner.supervision.decide(
        "reasoning_agent", runner.supervision.measure("reasoning_agent", injected), {})
    routed = runner.d19_decision(decision)
    seen = {}
    monkeypatch.setattr(runner, "_agent_for",
                        lambda stage: _capturing_agent(ReasoningAgent, seen))
    runner._regenerate({"arm": "A1", "placement": "P1"}, base, injected, descriptor, routed)
    tail = "".join(m["content"] for m in seen["messages"][2:])
    assert routed.retry_feedback in tail


def test_the_c1_flag_cannot_be_combined_with_a_separate_pass():
    with pytest.raises(ValueError):
        runner.build_plan(str(STUDY_ROOT), with_c1=True, cell="d19")


def test_a_pass_the_c1_cell_does_not_carry_is_not_written_to_its_checkpoint(tmp_path, monkeypatch):
    plan = [
        {"defect_id": "a:O1", "operator": "O1", "runnable": False,
         "reason": "not_in_c1_subset", "arms": []},
    ]
    monkeypatch.setattr(runner, "build_plan", lambda *a, **k: plan)
    monkeypatch.setattr(runner, "verify_order", lambda p: [])
    monkeypatch.setattr(runner, "plan_summary", lambda p: {
        "defects_runnable": 0, "defects_inapplicable": 0, "injection_verified": 0,
        "defects_applicable": 0, "injection_success_rate": None, "triggered": 0,
        "trigger_rate": None, "trials": 0, "trials_by_arm": {}, "c1_trials": 0})
    assert runner.run("r", str(tmp_path), 3, "P1", 0, dry_run=True, cell="c1") == 0
    assert not (tmp_path / "checkpoint.jsonl").exists()


# ── the placement and severity passes (section 0.1 A5, A6) ──────────────────


@needs_study
def test_the_placement_pass_runs_a1_at_all_four_levels_on_a_third():
    plan = runner.build_plan(str(STUDY_ROOT), cell="placement")
    runnable = [d for d in plan if d["runnable"]]
    assert len(runnable) == 45
    for d in runnable:
        assert [(c["arm"], c["placement"]) for c in d["arms"]] == [
            ("A1", level) for level in runner.PLACEMENT_LEVELS for _ in range(3)]
    s = runner.plan_summary(plan)
    assert s["trials"] == 540 and s["not_in_pass"] == 97
    assert s["trials_by_placement"] == {"P0": 135, "P1": 135, "P2": 135, "P3": 135}
    assert runner.verify_order(plan) == []


@needs_study
def test_the_placement_subset_is_a_per_operator_stride():
    plan = [d for d in runner.build_plan(str(STUDY_ROOT), cell="placement")
            if d.get("triggers")]
    by_op: dict[str, list[bool]] = {}
    for d in plan:
        by_op.setdefault(d["operator"], []).append(d["runnable"])
    for op, flags in by_op.items():
        expected = [runner._in_subset(i, runner.PLACEMENT_FRACTION) for i in range(len(flags))]
        assert flags == expected, op


@needs_study
def test_the_severity_pass_runs_both_o1_levels_in_one_defect():
    plan = runner.build_plan(str(STUDY_ROOT), cell="severity")
    runnable = [d for d in plan if d["runnable"]]
    assert {d["operator"] for d in plan} == {"O1"} and len(runnable) == 24
    for d in runnable:
        assert [(c["arm"], c["placement"], c["severity"]) for c in d["arms"]] == (
            [("A1", "P1", 1)] * 3 + [("A1", "P1", 2)] * 3)
        assert d["gate_severity2"]["verdict"] == "retry"
    s = runner.plan_summary(plan)
    assert s["trials"] == 144 and s["trials_by_severity"] == {"1": 72, "2": 72}
    assert runner.verify_order(plan) == []


def test_verify_order_catches_a_half_populated_placement_or_severity_defect():
    bad_p = [{"defect_id": "d", "runnable": True, "cell": "placement",
              "arms": [{"arm": "A1", "placement": "P0", "rep": 0},
                       {"arm": "A1", "placement": "P1", "rep": 0}]}]
    bad_s = [{"defect_id": "d", "runnable": True, "cell": "severity",
              "arms": [{"arm": "A1", "placement": "P1", "rep": 0, "severity": 1}]}]
    assert any("placement levels" in p for p in runner.verify_order(bad_p))
    assert any("severity levels" in p for p in runner.verify_order(bad_s))


@needs_study
def test_a_severity_trial_runs_on_its_own_levels_injection(tmp_path):
    """Each cell must see the injection of its own level, not the defect's first."""
    assert runner.run(str(STUDY_ROOT), str(tmp_path), 3, "P1", 0, dry_run=True,
                      limit=1, cell="severity") == 0
    row = json.loads((tmp_path / "checkpoint.jsonl").read_text(encoding="utf-8").splitlines()[0])
    by_level = {}
    for t in row["trials"]:
        by_level.setdefault(t["severity"], set()).add(json.dumps(t["descriptor"], sort_keys=True))
    assert set(by_level) == {1, 2}
    assert all(len(v) == 1 for v in by_level.values())
    d1 = json.loads(next(iter(by_level[1])))
    d2 = json.loads(next(iter(by_level[2])))
    assert "severity" not in d1["target"] and d2["target"]["severity"] == 2


@needs_study
def test_a_placement_pass_defect_outside_the_subset_is_not_written(tmp_path):
    assert runner.run(str(STUDY_ROOT), str(tmp_path), 3, "P1", 0, dry_run=True,
                      limit=3, cell="placement") == 0
    rows = [json.loads(l) for l in
            (tmp_path / "checkpoint.jsonl").read_text(encoding="utf-8").splitlines()]
    assert all(r.get("status") in ("dry-run", "skipped") for r in rows)
    assert not any(runner.not_in_pass(r) for r in rows)



# -- the warm-resample pass (section 0.1 A7) ----------------------------------


@needs_study
def test_the_warm_pass_runs_t0_comparators_beside_t1_on_the_placement_subset():
    plan = runner.build_plan(str(STUDY_ROOT), cell="warm")
    runnable = [d for d in plan if d["runnable"]]
    placement_ids = {d["defect_id"] for d in runner.build_plan(str(STUDY_ROOT), cell="placement")
                     if d["runnable"]}
    assert {d["defect_id"] for d in runnable} == placement_ids and len(runnable) == 45
    for d in runnable:
        assert [(c["arm"], c["placement"], c["temperature"]) for c in d["arms"]] == (
            [("A1", "P1", 0.0)] * 3 + [("A1", "P1", 1.0)] * 3
            + [("A2", "P1", 0.0)] * 3 + [("A2", "P1", 1.0)] * 3 + [("A3", "P0", 1.0)] * 3)
    s = runner.plan_summary(plan)
    assert s["trials"] == 675 and s["trials_by_temperature"] == {"0.0": 270, "1.0": 405}
    assert runner.verify_order(plan) == []


def test_verify_order_catches_a_warm_arm_missing_a_temperature():
    bad = [{"defect_id": "d", "runnable": True, "cell": "warm", "arms": [
        {"arm": "A1", "placement": "P1", "rep": 0, "temperature": 0.0},
        {"arm": "A2", "placement": "P1", "rep": 0, "temperature": 0.0},
        {"arm": "A2", "placement": "P1", "rep": 0, "temperature": 1.0},
        {"arm": "A3", "placement": "P0", "rep": 0, "temperature": 1.0}]}]
    assert any("A1 temperatures" in p for p in runner.verify_order(bad))


@needs_study
def test_the_warm_seam_sets_the_temperature_on_the_trials_own_agent(monkeypatch):
    from app.agents.reasoning_agent import ReasoningAgent

    _, base, injected, descriptor, decision = _reasoning_defect()
    agents = []

    def make(stage):
        agent = _capturing_agent(ReasoningAgent, {})
        agents.append(agent)
        return agent

    monkeypatch.setattr(runner, "_agent_for", make)
    runner._regenerate({"arm": "A1", "placement": "P1", "temperature": 1.0},
                       base, injected, descriptor, decision)
    runner._regenerate({"arm": "A1", "placement": "P1"}, base, injected, descriptor, decision)
    assert agents[0].temperature == 1.0
    assert agents[1].temperature == 0.0
    assert ReasoningAgent.temperature == 0.0      # the class default is never touched


@needs_study
def test_the_trial_row_records_the_temperature():
    _, base, injected, descriptor, _ = _reasoning_defect()
    defect = {"defect_id": "x", "operator": descriptor.operator, "cell": "warm"}
    row = runner.run_trial(defect, {"arm": "A1", "placement": "P1", "rep": 0,
                                    "temperature": 1.0},
                           base, injected, descriptor, "s", dry_run=True)
    assert row["temperature"] == 1.0
