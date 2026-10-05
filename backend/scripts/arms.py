"""Arms and placement — the message list for one trial (JOURNAL_PLAN B5).

One function builds the prompt for an (arm, placement) cell, so no cell is
special-cased in the runner. **B5's claim that this makes the design fully
crossed is false, and D9b says so:** two cells are structurally undefined and
this module raises on them rather than inventing a message list.

Arms (D2)
    A0  capability ceiling — the defect presented as a fresh correction task,
        with no retry framing. Bounds what any feedback could achieve.
    A1  measured-fact feedback — the production ``_SUPERVISOR_FEEDBACK_PROMPT``
        with the supervisor's own retry string. Imported, never re-typed.
    A2  generic rejection — same structure, no specifics.
    A3  bare re-draw — the original prompt again, nothing added. Declared as a
        determinism floor at temperature 0, not as resampling.

Placement (D9), four levels
    P0  the defective output is **absent** from the context. The production
        path, and the Tier-1 default.
    P1  the defective output sits in the **user** turn as an artifact under
        review. The Tier-2 default (D10).
    P2  the defective output sits in an **assistant** turn, as the model's own.
    P3  exploratory: P2 plus a correction marker, wording pinned per 14.5.

Condition (D8, D8b) -- constraint completeness, two levels
    C0  the production stage prompt, unchanged. Every core trial is C0.
    C1  that same prompt with the supervisor's obligations stated before the
        answer is written. Crossed with {A1, A2} on a subset of defects (D8d).
        Per D8b the base output is always C0's: only the retry prompt varies,
        so the claim the cell licenses is about *stating the constraints at
        retry time*, not about a constraint-complete pipeline.

Undefined cells (D9b)
    A0 x P0   A0 must show the artifact to frame it as a correction task.
    A3 x P1   showing the artifact stops it being a bare re-draw.
    So A0 in {P1, P2, P3}, A3 in {P0}, and A1/A2 span all four.
    Factor C adds no undefined cell -- it rewrites the stage prompt, which
    every arm carries -- but the *plan* runs it on {A1, A2} only (D8d).

**Wording frozen 2026-08-25.** The plan specifies these arms' structure but never
their text. Each string below is derived from a stated constraint rather than
chosen for tone, and the derivation is recorded beside it so a reviewer can
check the manipulation rather than take it on trust. A1 is exempt: it is
imported from the production path, never authored here.

⚠ These are pre-registration items. They are frozen, not unreviewable — confirm
them at memo sign-off, and if any changes, change it *before* a trial runs, not
after.
"""

from __future__ import annotations

import copy
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.agents.base_agent import _SUPERVISOR_FEEDBACK_PROMPT  # noqa: E402

ARMS = ("A0", "A1", "A2", "A3")
PLACEMENTS = ("P0", "P1", "P2", "P3")
CONDITIONS = ("C0", "C1")

# D9b: structurally undefined cells. Not "not run" — not *definable*.
UNDEFINED_CELLS = frozenset({("A0", "P0"), ("A3", "P1"), ("A3", "P2"), ("A3", "P3")})

DEFAULT_PLACEMENT = {"tier1": "P0", "tier2": "P1"}  # D10


# ── frozen wording (see the module note) ──────────────────────────────────────

# A0 — capability ceiling.
#
# Derivation. A0 must (a) put the artifact in context, (b) carry **no** retry
# framing and no claim that the model itself produced it, (c) disclose nothing
# about the defect, or it becomes a weak A1, and (d) end in the same output
# instruction as every other arm, or arm is confounded with output format.
#
# ⚠ **Authorship is deliberately left neutral.** An earlier draft read "produced
# by another system", to maximise the distance from the self-attribution blind
# spot SC-Bench measures. That is wrong here: it contradicts itself at A0 x P2,
# where the placement puts the artifact in the model's *own* assistant turn, and
# more importantly it would bake an attribution claim into the **arm** when
# attribution is exactly what the **placement** factor manipulates. Confounding
# the two would make A0 x P1 and A0 x P2 differ on two things at once.
A0_PREAMBLE = (
    "Below is a draft answer to this task. "
    "Review it and produce the best answer you can to the original task. "
    "Return only valid JSON."
)

# A2 — generic rejection.
#
# Derivation. A2 is A1's own template with the measured facts removed and
# nothing else changed: same opening sentence verbatim, same closing
# instruction verbatim. Only the {feedback} substitution and the dangling
# deictic it leaves behind ("fixes exactly these issues" -> "a corrected
# answer") differ. Matching everything except the manipulated variable is what
# makes A1 vs A2 a content contrast rather than a wording contrast.
A2_FEEDBACK = """\
A deterministic quality check rejected your previous answer to this task.

Produce a corrected answer. Return only valid JSON."""

# P3 — correction marker (exploratory; 13.4 demotes this placement).
#
# Derivation, per 14.5's marker audit. It is a **statement, not an
# instruction** — the arm already supplies the instruction, and a marker that
# asked for a correction would duplicate it. It names no field, no count and no
# check, because a marker that discloses what is wrong stops being a placement
# manipulation and becomes a weak A1.
P3_MARKER = "The answer above contains an error."

# ── C1 — the constraint-complete prompt (D8, D8b) ─────────────────────────────
#
# Factor C is constraint completeness. C0 is the production stage prompt,
# untouched; C1 is that same prompt with the supervisor's obligations stated
# before the answer is written. The cell exists because `prompt_audit.py`
# adjudicated **5 of 5** obligations the supervisor asserts in its retry
# feedback as appearing in no stage prompt at all — so without C1 an A1 > A2
# result is partly prompt completeness rather than feedback specificity (Huang
# et al., ICLR 2024 §5; Kamoi et al., TACL 2024 Table 7, *Required* row).
#
# **Derivation.** Each clause restates one row of `prompt_audit.CONSTRAINTS` —
# its ``supervisor_asserts`` field, which is the adjudicated *obligation*, never
# the retry string. That distinction is the manipulation:
#
#   - the **retry string** carries the measured facts of *this* defect
#     ("evidence ids not found in the analysis output: ['r_7']"). That is A1.
#     Putting it here would make C1 a second A1 and collapse the C x arm
#     contrast into nothing.
#   - the **obligation** is generic, is true before any output exists, and names
#     no defect. A deployment could ship it unchanged. That is C1.
#
# Four properties, each a confound if it were merely intended:
#
# 1. **Stage-scoped.** A stage is told its own obligations and no others.
#    Stating all five everywhere would disclose obligations belonging to stages
#    the trial never runs, and would vary the block's length for no reason.
# 2. **Complete for the stage.** Every obligation the supervisor can assert at
#    retry for that stage is stated, *including the ones this defect did not
#    violate*. A block naming only the violated obligation would be a weak A1.
# 3. **No mechanism.** The obligation is stated; the checker that measures it is
#    not — no threshold, no similarity rule, no field the production prompt does
#    not already name. Disclosing the mechanism would make C1 a "how to pass the
#    check" prompt, which is a different manipulation with a different claim.
# 4. **It goes inside the system message, ahead of the closing instruction.**
#    Not in a turn of its own: placement (D9) *is* the manipulation of which
#    turn carries what, so a C1 turn would confound C with placement. And ahead
#    of "Return only valid JSON." so C0 and C1 still end in the same output
#    instruction — the rule `test_every_arm_ends_in_the_same_output_instruction`
#    already pins for the arms, for the same reason.
#
# ⚠ **The frequency check is deliberately absent.** It resolves to
# `proceed_with_warning`, never to `retry`, so it never reaches an A1 feedback
# string. Stating it would give C1 information A1 does not have, and C1 is
# defined as closing the A1-minus-prompt delta — not as exceeding it.
#
# ⚠ Pre-registration item, added **after** the `prereg-freeze` tag. The C1 cell
# was already exploratory (PREREGISTRATION.md §2.1) and is reported as an
# estimate with a CI, never as a test (D8c). See §0.1, amendment A1.
C1_PREAMBLE = "Your answer must satisfy all of the following requirements:"

C1_CONSTRAINTS: dict[str, tuple[str, ...]] = {
    "reasoning_agent": (
        "Every id in evidence_review_ids must be the review_id of a review "
        "present in the analysed reviews you were given.",
        "Every review cited as evidence for a pattern must itself mention that "
        "pattern's aspect.",
    ),
    "strategy_agent": (
        "Every recommendation's issue must trace back to one of the reasoning "
        "patterns or root causes you were given.",
    ),
    "report_agent": (
        "The report must only restate the upstream outputs you were given. Do "
        "not introduce a root cause or a recommendation that is not present "
        "upstream.",
        "business_name and sample_size must match the values supplied with the "
        "task, not values inferred from the text.",
    ),
}

# The sentence every production stage prompt ends on, and therefore the splice
# point. Imported behaviour would be better than a literal, but the prompts end
# on it as plain prose with no constant to import; `test_c1_splices_before_the
# _production_closing_instruction` pins all three against this string, so a
# prompt edit fails offline rather than mid-study.
C1_CLOSING = "Return only valid JSON."

# Kept as a record of what was authored here rather than imported, so the memo
# and the appendix have one list to check. Previously named PENDING_SIGN_OFF.
AUTHORED_WORDING = ("A0_PREAMBLE", "A2_FEEDBACK", "P3_MARKER",
                    "C1_PREAMBLE", "C1_CONSTRAINTS")


def authored_texts() -> dict[str, str]:
    """Every string authored here, flattened to name -> text.

    ``AUTHORED_WORDING`` names the constants; this expands the one that is a
    per-stage mapping, so the memo and the appendix publish one flat list and a
    test has one thing to check is non-empty.
    """
    texts: dict[str, str] = {}
    for name in AUTHORED_WORDING:
        value = globals()[name]
        if isinstance(value, dict):
            for stage, clauses in value.items():
                for i, clause in enumerate(clauses):
                    texts[f"{name}[{stage}][{i}]"] = clause
        else:
            texts[name] = value
    return texts


class UndefinedCell(ValueError):
    """Raised for an (arm, placement) combination D9b declares undefined."""


def is_defined(arm: str, placement: str) -> bool:
    if arm not in ARMS:
        raise ValueError(f"unknown arm {arm!r}")
    if placement not in PLACEMENTS:
        raise ValueError(f"unknown placement {placement!r}")
    return (arm, placement) not in UNDEFINED_CELLS


def defined_cells() -> list[tuple[str, str]]:
    return [(a, p) for a in ARMS for p in PLACEMENTS if is_defined(a, p)]


def constraint_block(stage: str) -> str:
    """C1's added text for one stage, verbatim — the appendix publishes this."""
    try:
        clauses = C1_CONSTRAINTS[stage]
    except KeyError:
        raise ValueError(
            f"no C1 constraints adjudicated for stage {stage!r}; prompt_audit.py "
            "is the source, and a stage it does not cover cannot silently run as C1"
        ) from None
    return "\n".join([C1_PREAMBLE] + [f"- {c}" for c in clauses])


def apply_condition(messages: list[dict], condition: str, stage: str) -> list[dict]:
    """``messages`` under factor C, as a new list. C0 is production's own prompt.

    C1 splices the stage's obligations into the **system** message, ahead of the
    closing output instruction. Both placements are load-bearing: a separate
    turn would confound C with placement (D9), and text *after* the closing
    instruction would leave C0 and C1 ending on different sentences.

    Raises rather than degrading to C0 if the prompt has moved out from under
    the splice point — a C1 trial that silently ran as C0 would still be
    recorded, and scored, as a C1 observation.
    """
    if condition not in CONDITIONS:
        raise ValueError(f"unknown condition {condition!r}")
    if condition == "C0":
        return list(messages)
    if not messages or messages[0].get("role") != "system":
        raise ValueError("C1 states the constraints up front; this message list "
                         "has no system turn to state them in")

    system = messages[0]["content"].rstrip()
    if not system.endswith(C1_CLOSING):
        raise ValueError(
            f"the {stage} system prompt no longer ends in {C1_CLOSING!r}, so C1's "
            "splice point is gone; re-derive it before a trial runs"
        )
    head = system[: -len(C1_CLOSING)].rstrip()
    spliced = list(messages)
    spliced[0] = {**messages[0],
                  "content": f"{head}\n\n{constraint_block(stage)}\n\n{C1_CLOSING}"}
    return spliced


def build_messages(
    base_messages: list[dict],
    arm: str,
    placement: str,
    injected_output: str,
    feedback: str | None = None,
    condition: str = "C0",
    stage: str | None = None,
) -> list[dict]:
    """The message list for one trial.

    ``base_messages`` is the stage's own prompt, exactly as the agent would build
    it (system + user). ``injected_output`` is the defective JSON as a string.
    ``feedback`` is the supervisor's retry string and is required for A1 — it is
    the manipulation, so a missing one is an error rather than an empty arm.
    ``condition`` is factor C; C1 additionally needs ``stage``, because the
    obligations it states are that stage's and no others.
    """
    if not is_defined(arm, placement):
        raise UndefinedCell(
            f"{arm} x {placement} is structurally undefined (D9b): "
            "A0 needs an artifact to correct; A3 stops being a bare re-draw once shown one"
        )
    if arm == "A1" and not feedback:
        raise ValueError("A1 is defined by the measured-fact feedback; none was given")

    messages = copy.deepcopy(base_messages)

    # Factor C acts on the stage prompt, so it applies before arm and placement
    # do — including for A3, whose whole message list *is* the stage prompt.
    if condition != "C0":
        if stage is None:
            raise ValueError(
                f"{condition} is stage-scoped: pass the stage whose obligations to state"
            )
        messages = apply_condition(messages, condition, stage)

    # A3 is the original prompt and nothing else, at P0 by construction.
    if arm == "A3":
        return messages

    # Placement decides where (and whether) the defective artifact appears.
    if placement == "P1":
        messages.append({
            "role": "user",
            "content": (f"{A0_PREAMBLE}\n\n{injected_output}" if arm == "A0"
                        else f"Your previous answer to this task was:\n\n{injected_output}"),
        })
    elif placement in ("P2", "P3"):
        if arm == "A0":
            messages.append({"role": "user", "content": A0_PREAMBLE})
        messages.append({"role": "assistant", "content": injected_output})
        if placement == "P3":
            messages.append({"role": "user", "content": P3_MARKER})

    # Arm decides what is said about it. A0 has already said its piece: it is a
    # fresh correction task and must carry no retry framing.
    if arm == "A1":
        messages.append({
            "role": "user",
            "content": _SUPERVISOR_FEEDBACK_PROMPT.format(feedback=feedback),
        })
    elif arm == "A2":
        messages.append({"role": "user", "content": A2_FEEDBACK})

    return messages


def cell_summary() -> str:
    lines = ["arm x placement grid (X = undefined, D9b)", "",
             "      " + "  ".join(PLACEMENTS)]
    for arm in ARMS:
        row = "  ".join(" o" if is_defined(arm, p) else " X" for p in PLACEMENTS)
        lines.append(f"{arm}    {row}")
    lines.append("")
    lines.append(f"defined cells: {len(defined_cells())} of {len(ARMS) * len(PLACEMENTS)}")
    lines.append(f"conditions (D8): {', '.join(CONDITIONS)} — C1 states "
                 f"{sum(len(v) for v in C1_CONSTRAINTS.values())} obligations across "
                 f"{len(C1_CONSTRAINTS)} stages")
    lines.append(f"authored here (not imported): {', '.join(AUTHORED_WORDING)}")
    for stage in C1_CONSTRAINTS:
        lines.append("")
        lines.append(f"C1 x {stage}:")
        lines.extend(f"  {line}" for line in constraint_block(stage).splitlines())
    return "\n".join(lines)


if __name__ == "__main__":
    print(cell_summary())
