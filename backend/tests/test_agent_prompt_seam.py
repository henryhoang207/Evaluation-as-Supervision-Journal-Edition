"""The prompt/execute seam must not change what production sends.

``run()`` was split into ``build_prompt`` + ``_with_feedback`` + ``run_messages``
so the injection study can wrap the *same* prompt production uses
(scripts/arms.py) instead of re-typing it. That is only safe if the composition
is exactly what the single method used to do -- these tests pin it, one agent at
a time, without an API key or a network call.

The failure this guards against is silent: a stage prompt that drifts from the
one the study wraps turns every arm contrast into a wording contrast as well.
"""

import pytest

from app.agents.base_agent import BaseAgent, _SUPERVISOR_FEEDBACK_PROMPT
from app.agents.reasoning_agent import ReasoningAgent
from app.agents.report_agent import ReportAgent
from app.agents.strategy_agent import StrategyAgent
from app.schemas.contracts import ReasoningOutput, ReportOutput, StrategyOutput

REASONING_INPUT = {
    "business_id": "biz1",
    "sample_size": 2,
    "analysis_results": [
        {"review_id": "r1", "sentiment": "negative", "aspects": ["wait_time"]},
        {"review_id": "r2", "sentiment": "negative", "aspects": ["food_quality"]},
    ],
}
STRATEGY_INPUT = {
    "patterns": [{"description": "slow service", "aspect": "wait_time",
                  "frequency": 0.5, "evidence_review_ids": ["r1"]}],
    "root_causes": [{"pattern": "slow service", "cause": "understaffed",
                     "confidence": "high"}],
}
REPORT_INPUT = {
    "business_name": "Cafe One",
    "sample_size": 2,
    "analysis_summary": {},
    "reasoning_summary": {"patterns": [], "root_causes": []},
    "recommendations": [],
}

CASES = [
    pytest.param(ReasoningAgent, REASONING_INPUT, "reasoning_agent", ReasoningOutput,
                 id="reasoning"),
    pytest.param(StrategyAgent, STRATEGY_INPUT, "strategy_agent", StrategyOutput,
                 id="strategy"),
    pytest.param(ReportAgent, REPORT_INPUT, "report_agent", ReportOutput,
                 id="report"),
]


def _bare(cls):
    """An agent whose real methods are intact but which opened no LLM client."""
    return cls.__new__(cls)


@pytest.mark.parametrize("cls, payload, name, schema", CASES)
def test_the_stage_declares_its_identity_and_contract(cls, payload, name, schema):
    assert cls.AGENT_NAME == name
    assert cls.OUTPUT_SCHEMA is schema


@pytest.mark.parametrize("cls, payload, name, schema", CASES)
def test_build_prompt_is_system_then_user_and_the_user_turn_is_the_task(
    cls, payload, name, schema
):
    messages, original_task = _bare(cls).build_prompt(payload)
    assert [m["role"] for m in messages] == ["system", "user"]
    assert messages[1]["content"] == original_task
    assert messages[0]["content"], "the stage must still send its system prompt"


@pytest.mark.parametrize("cls, payload, name, schema", CASES)
def test_run_is_exactly_build_prompt_plus_feedback_plus_run_messages(
    cls, payload, name, schema, monkeypatch
):
    """The refactor's whole claim, pinned per agent."""
    agent = _bare(cls)
    seen = {}

    def capture(messages, original_task, input_data=None):
        seen["messages"] = messages
        seen["task"] = original_task
        return {"status": "success"}

    agent.run_messages = capture
    agent.run(payload, feedback="EVIDENCE ID r9 DOES NOT RESOLVE")

    expected_messages, expected_task = _bare(cls).build_prompt(payload)
    expected_messages = BaseAgent._with_feedback(
        expected_messages, "EVIDENCE ID r9 DOES NOT RESOLVE"
    )
    assert seen["messages"] == expected_messages
    assert seen["task"] == expected_task


@pytest.mark.parametrize("cls, payload, name, schema", CASES)
def test_no_feedback_leaves_the_prompt_at_two_turns(cls, payload, name, schema):
    agent = _bare(cls)
    seen = {}
    agent.run_messages = lambda m, t, i=None: seen.update(messages=m) or {"status": "success"}
    agent.run(payload)
    assert len(seen["messages"]) == 2, "a plain run must add nothing to the prompt"


def test_feedback_uses_the_production_template_the_study_imports():
    """arms.py imports this constant rather than re-typing A1's text."""
    messages = BaseAgent._with_feedback(
        [{"role": "system", "content": "s"}, {"role": "user", "content": "u"}], "FACTS"
    )
    assert messages[-1]["content"] == _SUPERVISOR_FEEDBACK_PROMPT.format(feedback="FACTS")


def test_an_agent_without_a_schema_refuses_to_execute_messages():
    """run_messages must not validate against nothing and call it a success."""

    class Nameless(BaseAgent):
        def run(self, input_data):
            raise NotImplementedError

    with pytest.raises(NotImplementedError):
        _bare(Nameless).run_messages([], "task")


def test_the_report_stage_restores_upstream_metadata_after_the_model_answers():
    """O8 is a positive control precisely because these two are handed back."""
    agent = _bare(ReportAgent)
    result = agent._postprocess({"business_name": "wrong", "sample_size": 999},
                                REPORT_INPUT)
    assert result["business_name"] == "Cafe One"
    assert result["sample_size"] == 2


# ── stage payloads (app/core/nodes.py) ────────────────────────────────────────
#
# The other half of the seam: a replay trial must hand the retried stage the
# same input the graph node would. These pin that the node and the study read
# one builder rather than two copies that can drift apart.


def test_stage_payload_refuses_the_analysis_stage():
    """Its input is the sampled reviews, which a dump does not carry (D6)."""
    from app.core import nodes

    with pytest.raises(ValueError):
        nodes.stage_payload("analysis_agent", {})


def test_stage_payload_is_exactly_what_the_node_hands_the_stage(monkeypatch):
    from app.core import nodes

    state = {
        "business_id": "biz1",
        "business_name": "Cafe One",
        "analysis_results": [
            {"review_id": "r1", "sentiment": "negative", "aspects": ["wait_time"],
             "status": "success"},
            {"review_id": "r2", "sentiment": "negative", "aspects": ["food_quality"],
             "status": "error"},
        ],
        "reasoning_output": {"patterns": STRATEGY_INPUT["patterns"],
                             "root_causes": STRATEGY_INPUT["root_causes"]},
        "strategy_output": {"recommendations": [{"priority": 1, "issue": "i",
                                                 "action": "a", "category": "c",
                                                 "expected_impact": "e"}]},
    }
    seen = {}

    monkeypatch.setattr(nodes, "reason_over_reviews",
                        lambda results, business_id, feedback: seen.update(
                            reasoning=(results, business_id)) or {"status": "success"})
    monkeypatch.setattr(nodes, "generate_recommendations",
                        lambda payload, use_llm, feedback: seen.update(
                            strategy=payload) or {"status": "success"})
    monkeypatch.setattr(nodes, "generate_report",
                        lambda payload, use_llm, feedback: seen.update(
                            report=payload) or {"status": "success"})

    nodes.reasoning_node(dict(state))
    nodes.strategy_node(dict(state))
    nodes.report_node(dict(state))

    expected_reasoning = nodes.stage_payload("reasoning_agent", state)
    assert seen["reasoning"] == (expected_reasoning["analysis_results"],
                                 expected_reasoning["business_id"])
    assert seen["strategy"] == nodes.stage_payload("strategy_agent", state)
    assert seen["report"] == nodes.stage_payload("report_agent", state)


def test_the_reasoning_payload_still_drops_failed_analysis_rows():
    """Behaviour the extraction must not have quietly changed."""
    from app.core import nodes

    payload = nodes.stage_payload("reasoning_agent", {
        "business_id": "biz1",
        "analysis_results": [
            {"review_id": "r1", "sentiment": "negative", "aspects": [], "status": "success"},
            {"review_id": "r2", "sentiment": "negative", "aspects": [], "status": "error"},
        ],
    })
    assert [r["review_id"] for r in payload["analysis_results"]] == ["r1"]
    assert payload["sample_size"] == 1
