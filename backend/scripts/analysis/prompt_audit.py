"""A1 feedback vs stage prompt — information-equivalence audit (B8, section 13.1).

**This blocks all trials.** The A1 arm's feedback discloses obligations the stage
system prompts never state. Where it does, an A1 > A2 result is partly
prompt-completeness rather than feedback specificity — Huang et al. (ICLR 2024)
section 5 and Kamoi et al. (TACL 2024) Table 7's *Required* row both say the
contrast is invalid without this control.

This script does the deterministic half: for every constraint the supervisor
asserts in a retry string, does the stage's own system prompt state it? The
output is the delta that D8's C1 prompt variant must close, and it is meant to
be published verbatim in an appendix.

It cannot decide *what C1 should say* — that is D8b, an open question for the
Phase-0 memo. It reports the gap.

Run (from backend/, venv active — read-only, no API calls, no dataset):

    python scripts/analysis/prompt_audit.py
    python scripts/analysis/prompt_audit.py --out out_study/prompt_audit.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from app.agents import report_agent, reasoning_agent, strategy_agent  # noqa: E402

STAGE_PROMPT = {
    "reasoning_agent": reasoning_agent._SYSTEM_PROMPT,
    "strategy_agent": strategy_agent._SYSTEM_PROMPT,
    "report_agent": report_agent._SYSTEM_PROMPT,
}

# The obligations supervision.decide asserts in its retry feedback.
#
# ⚠ **Adjudicated by reading the prompts, not inferred by keyword.** A substring
# heuristic was tried first and produced a false STATED for aspect_alignment: the
# reasoning prompt contains the word "mention", but only inside the definition of
# the *frequency* field ("proportion of reviews that mention this aspect
# negatively"), never as a requirement that a pattern's evidence must discuss its
# aspect. The failure direction matters — a false STATED understates the gap,
# which is the opposite of conservative — so the judgement is recorded explicitly
# and the evidence is machine-verified instead.
#
# All three stage prompts are pure output-schema descriptions. Not one of the
# five obligations appears in any of them, which is why every row below has
# stated_in_prompt=False and prompt_evidence=None. Section 13.1 reported four
# such cases; there are five.
CONSTRAINTS: tuple[dict, ...] = (
    {
        "id": "evidence_resolves",
        "stage": "reasoning_agent",
        "supervisor_asserts": "evidence ids must resolve to reviews in the analysis output",
        "feedback_fragment": "evidence ids not found in the analysis output",
        "stated_in_prompt": False,
        "prompt_evidence": None,
        "prompt_says_instead": "evidence_review_ids: list of review_ids that support this pattern",
    },
    {
        "id": "aspect_alignment",
        "stage": "reasoning_agent",
        "supervisor_asserts": "each evidence review must mention the pattern's aspect",
        "feedback_fragment": "do not mention aspect",
        "stated_in_prompt": False,
        "prompt_evidence": None,
        "prompt_says_instead": "aspect: the aspect category this pattern relates to",
    },
    {
        "id": "recommendation_traceability",
        "stage": "strategy_agent",
        "supervisor_asserts": "each recommendation issue must trace to a reasoning pattern or root cause",
        # Split across a line continuation in supervision.py, so the fragment must
        # stop at the concatenation boundary to be found in the source.
        "feedback_fragment": "do not trace back to any reasoning",
        "stated_in_prompt": False,
        "prompt_evidence": None,
        "prompt_says_instead": "issue: the underlying problem being addressed",
    },
    {
        "id": "report_containment",
        "stage": "report_agent",
        "supervisor_asserts": "the report must only restate upstream outputs",
        "feedback_fragment": "the report must only restate upstream outputs",
        "stated_in_prompt": False,
        "prompt_evidence": None,
        "prompt_says_instead": "Given upstream analysis, reasoning, and recommendation outputs, produce a clear report.",
    },
    {
        "id": "trusted_metadata",
        "stage": "report_agent",
        "supervisor_asserts": "business_name and sample_size must match the pipeline's values",
        "feedback_fragment": "does not match the pipeline",
        "stated_in_prompt": False,
        "prompt_evidence": None,
        "prompt_says_instead": "business_name: the restaurant name",
    },
)


def _supervision_source() -> str:
    path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "app", "core", "supervision.py",
    )
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def verify(constraints=CONSTRAINTS) -> list[str]:
    """Machine checks that keep an adjudicated table from rotting.

    Three ways this table could silently stop being true:
      - the supervisor stops asserting a constraint (feedback_fragment vanishes)
      - a stage prompt starts stating one (quoted counter-text vanishes)
      - a row claims the prompt states it but quotes no evidence
    """
    source = _supervision_source()
    problems = []
    for c in constraints:
        if c["feedback_fragment"] not in source:
            problems.append(
                f"{c['id']}: retry string {c['feedback_fragment']!r} no longer in supervision.py"
            )
        prompt = STAGE_PROMPT[c["stage"]]
        if c["prompt_says_instead"] and c["prompt_says_instead"] not in prompt:
            problems.append(
                f"{c['id']}: quoted prompt text has changed; re-adjudicate this row"
            )
        if c["stated_in_prompt"] and not c["prompt_evidence"]:
            problems.append(f"{c['id']}: claims the prompt states it but quotes no evidence")
        if c["prompt_evidence"] and c["prompt_evidence"] not in prompt:
            problems.append(f"{c['id']}: prompt_evidence is not in the prompt")
    return problems


def audit() -> dict:
    rows = [dict(c) for c in CONSTRAINTS]
    gap = [r for r in rows if not r["stated_in_prompt"]]
    return {
        "constraints": rows,
        "drift": verify(),
        "summary": {
            "n_constraints": len(rows),
            "stated_in_prompt": len(rows) - len(gap),
            "disclosed_only_by_feedback": len(gap),
            "gap_ids": [r["id"] for r in gap],
            "c1_must_close": [r["supervisor_asserts"] for r in gap],
        },
    }


def report(result: dict) -> None:
    s = result["summary"]
    print("A1 feedback vs stage system prompt (B8, section 13.1)\n")
    for r in result["constraints"]:
        verdict = "STATED" if r["stated_in_prompt"] else "FEEDBACK-ONLY"
        print(f"  [{verdict:^13}] {r['id']}  ({r['stage']})")
        print(f"      supervisor asserts : {r['supervisor_asserts']}")
        print(f"      prompt says only   : {r['prompt_says_instead']}")
    print("-" * 78)
    print(f"{s['disclosed_only_by_feedback']} of {s['n_constraints']} constraints reach the "
          f"model only through the A1 feedback.\n")
    if result["drift"]:
        print("DRIFT — the adjudicated table no longer matches the code:")
        for d in result["drift"]:
            print(f"  ! {d}")
        print()
    if s["gap_ids"]:
        print("C1 (D8) must state these for A1 vs A2 to be a specificity contrast:")
        for text in s["c1_must_close"]:
            print(f"  - {text}")
        print("\nD8b (open): whether C1 also regenerates the base output, or varies")
        print("only the retry prompt over a C0 base, is a Phase-0 decision.")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    result = audit()
    report(result)
    if args.out:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump(result, fh, indent=2, ensure_ascii=False)
        print(f"\nWrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
