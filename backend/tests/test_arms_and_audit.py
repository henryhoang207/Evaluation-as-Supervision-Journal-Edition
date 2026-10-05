"""Tests for arms x placement (B5) and the A1 prompt audit (B8).

B5's gate is D9b: the design is **not** fully crossed, and the builder must
refuse the undefined cells rather than invent a message list for them. B8's gate
is that its adjudicated table cannot rot — the retry strings it quotes must
still be in supervision.py, and the prompt text it quotes must still be in the
prompts.
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


arms = _load_module("arms", "scripts/arms.py")
prompt_audit = _load_module("prompt_audit", "scripts/analysis/prompt_audit.py")

BASE = [
    {"role": "system", "content": "You are a restaurant review pattern analyst."},
    {"role": "user", "content": "Identify patterns from 42 analysed reviews."},
]
INJECTED = '{"patterns": [{"evidence_review_ids": ["bad"]}]}'
FEEDBACK = "evidence ids not found in the analysis output: ['bad']"


# ── B5: D9b, the cells that are not definable ─────────────────────────────────


def test_the_undefined_cells_raise_rather_than_improvise():
    """A0 needs an artifact; A3 stops being a bare re-draw once shown one."""
    with pytest.raises(arms.UndefinedCell):
        arms.build_messages(BASE, "A0", "P0", INJECTED)
    with pytest.raises(arms.UndefinedCell):
        arms.build_messages(BASE, "A3", "P1", INJECTED)


def test_the_grid_is_not_fully_crossed():
    """B5's own text claims no cell is special-cased. D9b says otherwise."""
    assert len(arms.defined_cells()) == 12
    assert ("A0", "P0") in arms.UNDEFINED_CELLS
    assert ("A3", "P1") in arms.UNDEFINED_CELLS
    assert arms.is_defined("A1", "P0")
    assert arms.is_defined("A2", "P3")


def test_a1_without_feedback_is_an_error_not_an_empty_arm():
    """A1 *is* the measured-fact feedback; silently dropping it would make it A3."""
    with pytest.raises(ValueError):
        arms.build_messages(BASE, "A1", "P1", INJECTED, feedback=None)


def test_a1_uses_the_production_feedback_template_verbatim():
    """A1 must be the production path, not a re-typed lookalike."""
    from app.agents.base_agent import _SUPERVISOR_FEEDBACK_PROMPT

    messages = arms.build_messages(BASE, "A1", "P1", INJECTED, feedback=FEEDBACK)
    assert messages[-1]["content"] == _SUPERVISOR_FEEDBACK_PROMPT.format(feedback=FEEDBACK)
    assert FEEDBACK in messages[-1]["content"]


def test_a2_carries_no_specifics():
    """A2 is generic rejection: the same structure, none of the measured facts."""
    messages = arms.build_messages(BASE, "A2", "P1", INJECTED, feedback=FEEDBACK)
    assert FEEDBACK not in messages[-1]["content"]
    assert "bad" not in messages[-1]["content"]


def test_a3_is_the_original_prompt_and_nothing_else():
    """The determinism floor: no artifact, no feedback, no extra turn."""
    assert arms.build_messages(BASE, "A3", "P0", INJECTED) == BASE


def test_placement_decides_which_role_carries_the_artifact():
    p1 = arms.build_messages(BASE, "A1", "P1", INJECTED, feedback=FEEDBACK)
    p2 = arms.build_messages(BASE, "A1", "P2", INJECTED, feedback=FEEDBACK)

    assert any(m["role"] == "user" and INJECTED in m["content"] for m in p1)
    assert not any(m["role"] == "assistant" for m in p1)
    assert any(m["role"] == "assistant" and INJECTED in m["content"] for m in p2)


def test_p0_withholds_the_artifact_entirely():
    """The production path — and the cell no cited study covers (D1)."""
    p0 = arms.build_messages(BASE, "A1", "P0", INJECTED, feedback=FEEDBACK)
    assert not any(INJECTED in m["content"] for m in p0)


def test_p3_adds_the_marker_after_the_assistant_turn():
    p3 = arms.build_messages(BASE, "A1", "P3", INJECTED, feedback=FEEDBACK)
    roles = [m["role"] for m in p3]
    assert "assistant" in roles
    assert any(arms.P3_MARKER in m["content"] for m in p3)


def test_p3_marker_discloses_no_specifics():
    """14.5: a marker that says what is wrong becomes a weak A1, not a placement."""
    assert "evidence" not in arms.P3_MARKER.lower()
    assert "aspect" not in arms.P3_MARKER.lower()


def test_a0_carries_no_retry_framing():
    """A0 is a capability ceiling: a fresh task, not a correction of its own work."""
    a0 = arms.build_messages(BASE, "A0", "P1", INJECTED)
    text = " ".join(m["content"] for m in a0).lower()
    assert "previous answer" not in text
    assert "rejected" not in text


def test_build_does_not_mutate_the_base_messages():
    before = [dict(m) for m in BASE]
    arms.build_messages(BASE, "A1", "P2", INJECTED, feedback=FEEDBACK)
    assert BASE == before


def test_authored_wording_is_declared_and_non_empty():
    """The memo and the appendix need one list of what was authored vs imported."""
    assert set(arms.AUTHORED_WORDING) == {"A0_PREAMBLE", "A2_FEEDBACK", "P3_MARKER",
                                          "C1_PREAMBLE", "C1_CONSTRAINTS"}
    texts = arms.authored_texts()
    assert texts, "the appendix list cannot be empty"
    for name, text in texts.items():
        assert text.strip(), name


def test_a2_matches_a1_on_everything_except_the_specifics():
    """A1 vs A2 must isolate feedback *content*, not incidental wording.

    A2 is derived as A1's template with the measured facts removed, so the
    opening sentence and the closing output instruction must survive verbatim.
    If someone rewrites either arm's prose, this fails before a trial runs.
    """
    from app.agents.base_agent import _SUPERVISOR_FEEDBACK_PROMPT

    a1_opening = "A deterministic quality check rejected your previous answer to this task"
    assert a1_opening in _SUPERVISOR_FEEDBACK_PROMPT
    assert a1_opening in arms.A2_FEEDBACK

    assert _SUPERVISOR_FEEDBACK_PROMPT.rstrip().endswith("Return only valid JSON.")
    assert arms.A2_FEEDBACK.rstrip().endswith("Return only valid JSON.")

    # The deictic A1 uses to point at the facts must not survive into A2, where
    # there are no facts for it to point at.
    assert "these issues" in _SUPERVISOR_FEEDBACK_PROMPT
    assert "these issues" not in arms.A2_FEEDBACK


def test_a0_asserts_no_authorship_either_way():
    """Attribution is the placement factor's job, not the arm's.

    An earlier draft said "produced by another system", which contradicts itself
    at A0 x P2 (the artifact sits in the model's own assistant turn) and would
    make A0 x P1 and A0 x P2 differ on two things at once.
    """
    text = arms.A0_PREAMBLE.lower()
    assert "another system" not in text
    assert "different system" not in text
    assert "your previous" not in text
    assert "you wrote" not in text


def test_every_arm_ends_in_the_same_output_instruction():
    """Otherwise arm is confounded with output format, and a schema failure
    inflates attempts_made — which is the placement contamination D9 measures."""
    from app.agents.base_agent import _SUPERVISOR_FEEDBACK_PROMPT

    for text in (arms.A0_PREAMBLE, arms.A2_FEEDBACK, _SUPERVISOR_FEEDBACK_PROMPT):
        assert text.rstrip().endswith("Return only valid JSON.")


def test_p3_marker_is_a_statement_not_an_instruction():
    """14.5: the arm supplies the instruction; a marker that also does duplicates it."""
    text = arms.P3_MARKER.lower()
    for imperative in ("produce", "correct", "fix", "return", "please"):
        assert imperative not in text
    assert text.rstrip().endswith(".")


# ── B8: the audit table must track the code ───────────────────────────────────


def test_the_audit_table_has_not_drifted_from_supervision():
    """Every quoted retry string must still exist in supervision.py.

    This caught a real error on its first run: one retry string is split across
    a line continuation, so a fragment spanning the join is never found.
    """
    assert prompt_audit.verify() == []


def test_every_supervisor_constraint_is_feedback_only():
    """Section 13.1, confirmed against the code — and it is five, not four.

    All three stage prompts are output-schema descriptions; none states an
    obligation. If a prompt ever starts stating one, verify() fails first.
    """
    result = prompt_audit.audit()
    assert result["summary"]["n_constraints"] == 5
    assert result["summary"]["disclosed_only_by_feedback"] == 5
    assert result["summary"]["stated_in_prompt"] == 0


def test_a_row_claiming_the_prompt_states_it_must_quote_evidence():
    """Guards the adjudication itself against an unevidenced flip."""
    bogus = ({**prompt_audit.CONSTRAINTS[0], "stated_in_prompt": True,
              "prompt_evidence": None},)
    problems = prompt_audit.verify(bogus)
    assert any("quotes no evidence" in p for p in problems)


def test_quoted_prompt_evidence_must_actually_be_in_the_prompt():
    bogus = ({**prompt_audit.CONSTRAINTS[0], "stated_in_prompt": True,
              "prompt_evidence": "evidence ids must resolve"},)
    problems = prompt_audit.verify(bogus)
    assert any("not in the prompt" in p for p in problems)


# ── C1: the constraint-complete prompt (D8, D8b) ──────────────────────────────
#
# Added 2026-09-20, after the prereg-freeze tag. The cell was already
# exploratory (PREREGISTRATION.md section 2.1); the amendment is section 0.1.


def test_c1_states_every_obligation_the_audit_found_and_no_others():
    """C1 is defined as closing the A1-minus-prompt delta — exactly.

    Stating fewer leaves the completeness confound in place, which is the whole
    reason the cell exists. Stating more gives C1 information A1 never carries,
    which would make the C0-vs-C1 contrast measure something the study did not
    specify. The audit is the single source for the list.
    """
    audited = {c["stage"]: [] for c in prompt_audit.CONSTRAINTS}
    for c in prompt_audit.CONSTRAINTS:
        if not c["stated_in_prompt"]:
            audited[c["stage"]].append(c["id"])

    assert set(arms.C1_CONSTRAINTS) == set(audited)
    for stage, ids in audited.items():
        assert len(arms.C1_CONSTRAINTS[stage]) == len(ids), stage


def test_c1_restates_the_obligation_and_never_the_measured_facts():
    """The retry string is A1's manipulation. In C1 it would be a second A1."""
    block = " ".join(
        arms.constraint_block(s) for s in arms.C1_CONSTRAINTS
    ).lower()
    for c in prompt_audit.CONSTRAINTS:
        # the *fragment* of the retry string is the facts-carrying wording
        assert c["feedback_fragment"].lower() not in block, c["id"]
    # nor anything that could only come from a measurement
    for leak in ("not found", "do not mention", "does not match", "previous"):
        assert leak not in block, leak


def test_c1_is_stage_scoped():
    """A stage is told its own obligations and no others (D8 derivation 1)."""
    reasoning = arms.constraint_block("reasoning_agent")
    assert "evidence_review_ids" in reasoning
    assert "business_name" not in reasoning
    assert "recommendation" not in reasoning

    report = arms.constraint_block("report_agent")
    assert "business_name" in report and "sample_size" in report
    assert "evidence_review_ids" not in report


def test_c1_discloses_no_checker_mechanism():
    """Derivation 3: state the obligation, never how it is measured.

    A threshold or a similarity rule would make C1 a 'how to pass the check'
    prompt, which is a different manipulation with a different claim.
    """
    block = " ".join(arms.constraint_block(s) for s in arms.C1_CONSTRAINTS).lower()
    for mechanism in ("jaccard", "similarity", "threshold", "0.", "token", "overlap",
                      "supervisor", "check", "retry"):
        assert mechanism not in block, mechanism


def test_c1_names_no_defect_and_could_ship_in_production():
    """The obligation holds before any output exists; a deployment could ship it."""
    block = " ".join(arms.constraint_block(s) for s in arms.C1_CONSTRAINTS).lower()
    for retrospective in ("rejected", "your previous", "corrected", "the error",
                          "was wrong", "injected"):
        assert retrospective not in block, retrospective


def test_c1_splices_before_the_production_closing_instruction():
    """C0 and C1 must end on the same sentence.

    Otherwise C is confounded with output format the same way arm would be —
    and a schema failure inflates attempts_made, contaminating the placement
    manipulation D9 measures.
    """
    from app.agents import reasoning_agent, report_agent, strategy_agent

    for stage, module in (("reasoning_agent", reasoning_agent),
                          ("strategy_agent", strategy_agent),
                          ("report_agent", report_agent)):
        production = module._SYSTEM_PROMPT
        assert production.rstrip().endswith(arms.C1_CLOSING), stage

        spliced = arms.apply_condition(
            [{"role": "system", "content": production}], "C1", stage)[0]["content"]
        assert spliced.rstrip().endswith(arms.C1_CLOSING)
        assert spliced.count(arms.C1_CLOSING) == 1, "the closing must not be duplicated"
        assert arms.C1_PREAMBLE in spliced
        # every production sentence survives: C1 adds, it never edits
        head = production.rstrip()[: -len(arms.C1_CLOSING)].rstrip()
        assert head in spliced


def test_c0_is_productions_own_prompt_untouched():
    """The control arm of factor C must be a no-op, not a re-typed lookalike."""
    assert arms.apply_condition(BASE, "C0", "reasoning_agent") == BASE


def test_c1_refuses_rather_than_degrading_to_c0():
    """A C1 trial that silently ran as C0 would still be scored as a C1 observation."""
    moved = [{"role": "system", "content": "A prompt that no longer ends the same way."}]
    with pytest.raises(ValueError, match="splice point"):
        arms.apply_condition(moved, "C1", "reasoning_agent")

    with pytest.raises(ValueError, match="no system turn"):
        arms.apply_condition([{"role": "user", "content": "x"}], "C1", "reasoning_agent")

    with pytest.raises(ValueError):
        arms.apply_condition(BASE, "C2", "reasoning_agent")

    with pytest.raises(ValueError, match="no C1 constraints"):
        arms.constraint_block("analysis_agent")


def test_c1_without_a_stage_is_an_error_not_a_silent_c0():
    """C1 is stage-scoped; guessing the stage would state the wrong obligations."""
    with pytest.raises(ValueError, match="stage-scoped"):
        arms.build_messages(BASE, "A1", "P1", INJECTED, feedback=FEEDBACK,
                            condition="C1", stage=None)


def test_c1_changes_only_the_system_turn():
    """Derivation 4: a C1 turn would confound the condition with placement (D9)."""
    system = "You are an analyst. Return only valid JSON."
    base = [{"role": "system", "content": system},
            {"role": "user", "content": "Identify patterns."}]

    c0 = arms.build_messages(base, "A1", "P1", INJECTED, feedback=FEEDBACK,
                             condition="C0", stage="reasoning_agent")
    c1 = arms.build_messages(base, "A1", "P1", INJECTED, feedback=FEEDBACK,
                             condition="C1", stage="reasoning_agent")

    assert len(c0) == len(c1), "C1 must not add or remove a turn"
    assert [m["role"] for m in c0] == [m["role"] for m in c1]
    assert c0[0]["content"] != c1[0]["content"]
    assert c0[1:] == c1[1:], "only the system turn may differ"


def test_c1_is_identical_across_the_arms_it_crosses():
    """C is orthogonal to arm: the same constraint text under A1 and under A2.

    If the block varied by arm, the C0-vs-C1 difference-in-differences would be
    measuring the variation rather than the disclosure.
    """
    system = "You are an analyst. Return only valid JSON."
    base = [{"role": "system", "content": system}, {"role": "user", "content": "t"}]
    a1 = arms.build_messages(base, "A1", "P1", INJECTED, feedback=FEEDBACK,
                             condition="C1", stage="reasoning_agent")
    a2 = arms.build_messages(base, "A2", "P1", INJECTED, feedback=FEEDBACK,
                             condition="C1", stage="reasoning_agent")
    assert a1[0] == a2[0]


def test_c1_does_not_mutate_the_base_messages():
    before = [dict(m) for m in BASE]
    system = "You are an analyst. Return only valid JSON."
    live = [{"role": "system", "content": system}]
    arms.apply_condition(live, "C1", "reasoning_agent")
    assert live[0]["content"] == system
    assert BASE == before
