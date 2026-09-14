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
    assert set(arms.AUTHORED_WORDING) == {"A0_PREAMBLE", "A2_FEEDBACK", "P3_MARKER"}
    for name in arms.AUTHORED_WORDING:
        assert getattr(arms, name).strip()


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
