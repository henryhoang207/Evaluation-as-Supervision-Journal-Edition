import json
import logging
import os
from abc import ABC, abstractmethod
from collections.abc import Callable

from dotenv import load_dotenv
from openai import OpenAI

from app.core import llm_config
from app.schemas.contracts import AgentError
from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)

load_dotenv()

_CORRECTION_PROMPT = """\
You are correcting your previous output.

Original task:
{original_task}

Your previous output (invalid):
{invalid_output}

Validation error:
{validation_error}

Required JSON schema:
{schema}

Return only valid JSON that matches the schema. Do not add explanation."""

# Appended when the orchestrator ordered a re-run with retry_feedback: without
# changed input, a temperature-0 re-run would reproduce the identical output
# (docs/ORCHESTRATOR_SIMPLE_HUB.md §5.3).
_SUPERVISOR_FEEDBACK_PROMPT = """\
A deterministic quality check rejected your previous answer to this task:

{feedback}

Produce a corrected answer that fixes exactly these issues. Return only valid JSON."""


# Set LLM_DISABLE_FALLBACK=1 to make a primary-model failure raise instead of
# silently retrying on the fallback model. Trials in the injection study must
# never mix served models within one matched comparison (JOURNAL_PLAN B2), and
# a silent failover is indistinguishable from a slow call in the logs.
FALLBACK_DISABLED_ENV = "LLM_DISABLE_FALLBACK"
_TRUTHY = {"1", "true", "yes", "on"}


def fallback_disabled() -> bool:
    """True when a primary-model failure must propagate rather than fail over.

    Read per call, not at import, so a batch runner can flip it between runs
    inside one process (same convention as ``graph.observe_mode``).
    """
    return os.getenv(FALLBACK_DISABLED_ENV, "").strip().lower() in _TRUTHY


class BaseAgent(ABC):
    MAX_RETRIES = 2

    # A stage is (a) the messages it builds from its input and (b) the contract
    # its output must satisfy. Naming both here lets run() be composed from two
    # halves a caller can drive separately -- see build_prompt/run_messages.
    AGENT_NAME: str = "agent"
    OUTPUT_SCHEMA: type[BaseModel] | None = None

    # Cumulative prompt+completion tokens across all agent instances, used by
    # eval/harness.py to report LLM cost per 100 reviews. Additive/optional:
    # if the provider's response has no `usage` field this simply stays 0.
    total_tokens_used: int = 0

    # Per-call provenance for every request any agent makes: requested vs served
    # model, whether the fallback fired, and the token split.
    #
    # Class-level for the same reason as total_tokens_used: the module-level
    # helpers (reason_over_reviews, generate_recommendations, ...) construct the
    # agent and throw it away, so a batch runner can never reach instance state.
    # The injection study needs the served-model snapshot per call to defend the
    # matched analysis against serving-stack drift (JOURNAL_PLAN 14.1).
    call_log: list[dict] = []

    # These bind to BaseAgent explicitly, never to `cls`. `cls.x = ...` on a
    # subclass creates a shadowing subclass attribute while _record_usage keeps
    # writing to BaseAgent's, so `AnalysisAgent.reset_token_usage()` would look
    # like it worked and silently leave the real counter running — which would
    # corrupt exactly the per-trial accounting the injection study depends on.
    @classmethod
    def reset_token_usage(cls) -> None:
        BaseAgent.total_tokens_used = 0

    @classmethod
    def reset_call_log(cls) -> None:
        BaseAgent.call_log = []

    @classmethod
    def reset_instrumentation(cls) -> None:
        """Clear both counters. Call once per run, before the first stage."""
        cls.reset_token_usage()
        cls.reset_call_log()

    # Sampling temperature. Production pins 0 and nothing in production sets
    # it; the injection study's warm-resample cell (PREREGISTRATION.md section
    # 0.1 A7) sets it on its own, freshly constructed agent instance. A class
    # attribute, so every existing construction path keeps the production value.
    temperature: float = 0.0

    def __init__(self) -> None:
        self._client = OpenAI(**llm_config.client_kwargs())
        self._model = llm_config.primary_model()
        self._fallback_model = llm_config.fallback_model()

    @staticmethod
    def _with_feedback(messages: list[dict], feedback: str | None) -> list[dict]:
        """Append the orchestrator's retry feedback (if any) to the prompt."""
        if not feedback:
            return messages
        return messages + [
            {"role": "user", "content": _SUPERVISOR_FEEDBACK_PROMPT.format(feedback=feedback)}
        ]

    # ── prompt / execute seam ────────────────────────────────────────────────
    #
    # run() = build_prompt() + _with_feedback() + run_messages(). Splitting it
    # is what lets the injection study (scripts/arms.py) wrap the *same* prompt
    # production sends instead of re-typing it: an arm is defined as a
    # modification of the production prompt, so a re-typed copy would make the
    # A1-vs-A2 contrast a wording contrast as well as a content one, which is
    # precisely the confound the design exists to avoid. Production behaviour is
    # unchanged -- run() composes the same two halves in the same order.

    def build_prompt(self, input_data: dict) -> tuple[list[dict], str]:
        """This stage's own (messages, original_task), before any feedback."""
        raise NotImplementedError(f"{type(self).__name__} exposes no prompt seam")

    def _postprocess(self, result: dict, input_data: dict) -> dict:
        """Fields a stage restores from its input rather than trusting the model."""
        return result

    def run_messages(self, messages: list[dict], original_task: str,
                     input_data: dict | None = None) -> dict:
        """Execute an already-built message list under this stage's contract.

        Validation, the self-correction loop and the AgentError shape are
        identical whether the messages came from ``build_prompt`` or from a
        study arm, so a trial cannot accidentally diverge from production on
        anything except the manipulation itself.
        """
        if self.OUTPUT_SCHEMA is None:
            raise NotImplementedError(f"{type(self).__name__} declares no OUTPUT_SCHEMA")

        result, error, error_type, attempts = self._run_with_retry(
            messages, self.OUTPUT_SCHEMA, original_task
        )
        if result is not None:
            return self._postprocess(result, input_data or {})

        return AgentError(
            agent=self.AGENT_NAME,
            error_type=error_type or "unknown_error",
            error_detail=error or "Unknown error",
            retry_count=attempts,
            recoverable=False,
        ).model_dump()

    def _record_usage(self, resp, requested_model: str, fallback_used: bool) -> None:
        """Accumulate token usage and append one row of call provenance.

        ``resp.model`` is what the provider actually served, which is not
        necessarily what was requested — the distinction is the whole point of
        the log, so it is recorded even when the usage block is absent.
        """
        usage = getattr(resp, "usage", None)
        tokens = getattr(usage, "total_tokens", None) if usage is not None else None
        if tokens:
            BaseAgent.total_tokens_used += tokens
        BaseAgent.call_log.append(
            {
                "agent": type(self).__name__,
                "requested_model": requested_model,
                "served_model": getattr(resp, "model", None),
                "fallback_used": fallback_used,
                "prompt_tokens": getattr(usage, "prompt_tokens", None) if usage else None,
                "completion_tokens": getattr(usage, "completion_tokens", None) if usage else None,
                "total_tokens": tokens,
                "temperature": self.temperature,
            }
        )

    def _create(self, model: str, messages: list[dict]):
        return self._client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=self.temperature,
            response_format={"type": "json_object"},
        )

    def _call_llm(self, messages: list[dict], model: str | None = None) -> str:
        target = model or self._model
        try:
            resp = self._create(target, messages)
            self._record_usage(resp, target, fallback_used=False)
            return resp.choices[0].message.content
        except Exception as primary_exc:
            if target == self._fallback_model:
                raise
            if fallback_disabled():
                # Deliberate: an experiment that silently swaps served models
                # mid-comparison produces uninterpretable arms.
                logger.error(
                    "Primary model %s failed (%s) and %s is set — not failing over",
                    target, primary_exc, FALLBACK_DISABLED_ENV,
                )
                raise
            logger.warning("Primary model %s failed (%s), switching to fallback %s", target, primary_exc, self._fallback_model)
            resp = self._create(self._fallback_model, messages)
            self._record_usage(resp, self._fallback_model, fallback_used=True)
            return resp.choices[0].message.content

    def _run_with_retry(
        self,
        initial_messages: list[dict],
        schema_model: type[BaseModel],
        original_task: str,
        result_validator: Callable[[dict], None] | None = None,
    ) -> tuple[dict | None, str | None, str | None, int]:
        """Returns (result, error_detail, error_type, attempts_made)."""
        messages = list(initial_messages)
        last_raw: str | None = None
        last_error: str | None = None
        last_error_type: str | None = None
        attempt = 0

        for attempt in range(self.MAX_RETRIES + 1):
            try:
                last_raw = self._call_llm(messages)
            except Exception as exc:
                last_error = str(exc)
                last_error_type = "api_error"
                logger.error("LLM API call failed on attempt %d: %s", attempt, last_error)
                break
            try:
                parsed = json.loads(last_raw)
                validated = schema_model.model_validate(parsed)
                result = validated.model_dump()
                if result_validator:
                    result_validator(result)
                return result, None, None, attempt
            except (json.JSONDecodeError, ValidationError, ValueError) as exc:
                last_error = str(exc)
                last_error_type = "schema_validation_error"
                if attempt < self.MAX_RETRIES:
                    correction = _CORRECTION_PROMPT.format(
                        original_task=original_task,
                        invalid_output=last_raw,
                        validation_error=last_error,
                        schema=json.dumps(schema_model.model_json_schema(), indent=2),
                    )
                    messages = list(initial_messages)
                    messages.append({"role": "assistant", "content": last_raw})
                    messages.append({"role": "user", "content": correction})

        return None, last_error, last_error_type, attempt

    @abstractmethod
    def run(self, input_data: dict) -> dict:
        pass
