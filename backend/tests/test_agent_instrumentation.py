"""Tests for BaseAgent call instrumentation and fallback control (B1, B1b, B2).

The injection study needs three things the agents did not previously expose:
per-call token usage, the model the provider actually *served*, and a way to
make a primary-model failure raise instead of silently failing over. A silent
failover mid-comparison makes the matched arms uninterpretable
(JOURNAL_PLAN 14.1), so it has to be detectable rather than merely rare.
"""

import pytest

from app.agents import base_agent
from app.agents.base_agent import BaseAgent


class _Usage:
    def __init__(self, prompt=11, completion=22, total=33):
        self.prompt_tokens = prompt
        self.completion_tokens = completion
        self.total_tokens = total


class _Response:
    def __init__(self, content="{}", model="served-model", usage=_Usage()):
        self.model = model
        self.usage = usage
        self.choices = [type("C", (), {"message": type("M", (), {"content": content})()})()]


class _Agent(BaseAgent):
    """A BaseAgent with the network replaced by a scripted _create."""

    def __init__(self, responses):
        self._responses = list(responses)
        self._model = "primary-model"
        self._fallback_model = "fallback-model"
        self.requested = []

    def _create(self, model, messages):
        self.requested.append(model)
        item = self._responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return item

    def run(self, input_data):  # pragma: no cover - abstract satisfaction
        return {}


@pytest.fixture(autouse=True)
def _clean_counters(monkeypatch):
    monkeypatch.delenv(base_agent.FALLBACK_DISABLED_ENV, raising=False)
    BaseAgent.reset_instrumentation()
    yield
    BaseAgent.reset_instrumentation()


# ── B1 / B1b: usage and served-model provenance ──────────────────────────────


def test_call_log_records_requested_and_served_model():
    agent = _Agent([_Response(model="gemini-2.5-flash-002")])

    agent._call_llm([{"role": "user", "content": "hi"}])

    assert len(BaseAgent.call_log) == 1
    row = BaseAgent.call_log[0]
    assert row["requested_model"] == "primary-model"
    assert row["served_model"] == "gemini-2.5-flash-002"
    assert row["fallback_used"] is False
    assert (row["prompt_tokens"], row["completion_tokens"], row["total_tokens"]) == (11, 22, 33)


def test_tokens_accumulate_across_calls_and_reset():
    agent = _Agent([_Response(), _Response()])

    agent._call_llm([])
    agent._call_llm([])
    assert BaseAgent.total_tokens_used == 66
    assert len(BaseAgent.call_log) == 2

    BaseAgent.reset_instrumentation()
    assert BaseAgent.total_tokens_used == 0
    assert BaseAgent.call_log == []


def test_missing_usage_block_still_records_provenance():
    """A provider that returns no usage must not cost us the served-model row."""
    agent = _Agent([_Response(usage=None)])

    agent._call_llm([])

    row = BaseAgent.call_log[0]
    assert row["served_model"] == "served-model"
    assert row["total_tokens"] is None
    assert BaseAgent.total_tokens_used == 0


# ── B2: fallback control ──────────────────────────────────────────────────────


def test_fallback_fires_by_default_and_is_marked_in_the_log():
    agent = _Agent([RuntimeError("503"), _Response(model="fallback-served")])

    agent._call_llm([])

    assert agent.requested == ["primary-model", "fallback-model"]
    assert len(BaseAgent.call_log) == 1  # the failed primary produced no response
    row = BaseAgent.call_log[0]
    assert row["fallback_used"] is True
    assert row["requested_model"] == "fallback-model"
    assert row["served_model"] == "fallback-served"


@pytest.mark.parametrize("value", ["1", "true", "TRUE", "yes", "on"])
def test_fallback_disabled_raises_instead_of_failing_over(monkeypatch, value):
    monkeypatch.setenv(base_agent.FALLBACK_DISABLED_ENV, value)
    agent = _Agent([RuntimeError("503"), _Response()])

    with pytest.raises(RuntimeError):
        agent._call_llm([])

    assert agent.requested == ["primary-model"]  # never reached the fallback
    assert BaseAgent.call_log == []


def test_reset_from_a_subclass_clears_the_real_counters():
    """Regression: `cls.x = ...` would shadow instead of reset.

    _record_usage writes to BaseAgent's attributes, so a reset bound to `cls`
    creates a subclass attribute and silently leaves the real counter running —
    per-trial accounting would then accumulate across the whole batch.
    """
    from app.agents.analysis_agent import AnalysisAgent

    BaseAgent.call_log.append({"marker": True})
    BaseAgent.total_tokens_used = 99

    AnalysisAgent.reset_instrumentation()

    assert BaseAgent.call_log == []
    assert BaseAgent.total_tokens_used == 0
    assert "call_log" not in AnalysisAgent.__dict__
    assert "total_tokens_used" not in AnalysisAgent.__dict__


def test_fallback_flag_is_read_per_call_not_at_import(monkeypatch):
    """A batch runner must be able to flip it between runs in one process."""
    assert base_agent.fallback_disabled() is False
    monkeypatch.setenv(base_agent.FALLBACK_DISABLED_ENV, "1")
    assert base_agent.fallback_disabled() is True
    monkeypatch.setenv(base_agent.FALLBACK_DISABLED_ENV, "0")
    assert base_agent.fallback_disabled() is False



# -- temperature (PREREGISTRATION.md section 0.1 A7) --------------------------


def test_production_temperature_is_zero_and_reaches_the_request():
    """Production pins temperature 0. Only the warm-resample cell changes it,
    on its own agent instance, so the class default must stay 0."""
    assert BaseAgent.temperature == 0.0
    sent = {}

    class _Completions:
        def create(self, **kwargs):
            sent.update(kwargs)
            return _Response()

    agent = _Agent([])
    agent._client = type("C", (), {"chat": type("Ch", (), {"completions": _Completions()})()})()
    BaseAgent._create(agent, "m", [{"role": "user", "content": "x"}])
    assert sent["temperature"] == 0.0

    agent.temperature = 1.0
    BaseAgent._create(agent, "m", [{"role": "user", "content": "x"}])
    assert sent["temperature"] == 1.0
    assert BaseAgent.temperature == 0.0


def test_the_call_log_records_the_temperature_used():
    agent = _Agent([_Response()])
    agent.temperature = 1.0
    agent._call_llm([{"role": "user", "content": "x"}])
    assert BaseAgent.call_log[0]["temperature"] == 1.0
