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

Undefined cells (D9b)
    A0 x P0   A0 must show the artifact to frame it as a correction task.
    A3 x P1   showing the artifact stops it being a bare re-draw.
    So A0 in {P1, P2, P3}, A3 in {P0}, and A1/A2 span all four.

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

# Kept as a record of what was authored here rather than imported, so the memo
# and the appendix have one list to check. Previously named PENDING_SIGN_OFF.
AUTHORED_WORDING = ("A0_PREAMBLE", "A2_FEEDBACK", "P3_MARKER")


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


def build_messages(
    base_messages: list[dict],
    arm: str,
    placement: str,
    injected_output: str,
    feedback: str | None = None,
) -> list[dict]:
    """The message list for one trial.

    ``base_messages`` is the stage's own prompt, exactly as the agent would build
    it (system + user). ``injected_output`` is the defective JSON as a string.
    ``feedback`` is the supervisor's retry string and is required for A1 — it is
    the manipulation, so a missing one is an error rather than an empty arm.
    """
    if not is_defined(arm, placement):
        raise UndefinedCell(
            f"{arm} x {placement} is structurally undefined (D9b): "
            "A0 needs an artifact to correct; A3 stops being a bare re-draw once shown one"
        )
    if arm == "A1" and not feedback:
        raise ValueError("A1 is defined by the measured-fact feedback; none was given")

    messages = copy.deepcopy(base_messages)

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
    lines.append(f"authored here (not imported): {', '.join(AUTHORED_WORDING)}")
    return "\n".join(lines)


if __name__ == "__main__":
    print(cell_summary())
