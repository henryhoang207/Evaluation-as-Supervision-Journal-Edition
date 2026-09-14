import json

from app.agents.base_agent import BaseAgent
from app.schemas.contracts import ReasoningOutput

_SYSTEM_PROMPT = """\
You are a restaurant review pattern analyst. Given a collection of analysed reviews for a single restaurant, identify recurring negative patterns and their root causes.

Return a JSON object with:

- patterns: list of recurring negative patterns, each with:
  - description: human-readable description of the pattern
  - aspect: the aspect category this pattern relates to (e.g. "food_quality", "wait_time")
  - frequency: proportion of reviews (0.0–1.0) that mention this aspect negatively
  - evidence_review_ids: list of review_ids that support this pattern
- root_causes: list of likely root causes, each with:
  - pattern: description of the pattern this root cause explains
  - cause: the underlying cause
  - confidence: "low", "medium", or "high"
- status: "success"
- error_detail: null

Focus only on patterns that appear in multiple reviews. Return only valid JSON."""


class ReasoningAgent(BaseAgent):
    AGENT_NAME = "reasoning_agent"
    OUTPUT_SCHEMA = ReasoningOutput

    def build_prompt(self, input_data: dict) -> tuple[list[dict], str]:
        business_id = input_data.get("business_id", "unknown")
        sample_size = input_data.get("sample_size", 0)
        analysis_results = input_data.get("analysis_results", [])

        original_task = (
            f"Identify patterns and root causes from {sample_size} analysed reviews "
            f"for business '{business_id}':\n"
            f"{json.dumps(analysis_results, indent=2)}"
        )
        return [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": original_task},
        ], original_task

    def run(self, input_data: dict, feedback: str | None = None) -> dict:
        messages, original_task = self.build_prompt(input_data)
        return self.run_messages(
            self._with_feedback(messages, feedback), original_task, input_data
        )


def reason_over_reviews(
    analysis_results: list[dict],
    business_id: str = "unknown",
    feedback: str | None = None,
) -> dict:
    return ReasoningAgent().run(
        {
            "business_id": business_id,
            "sample_size": len(analysis_results),
            "analysis_results": analysis_results,
        },
        feedback=feedback,
    )
