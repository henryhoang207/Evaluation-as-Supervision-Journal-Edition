"""Content-word matching — how the scorer decides O5's trace check (D22).

``supervision._similar`` compares *characters*. JOURNAL_PLAN 15.4, 16.4 and 17
showed that this both misses real paraphrases ("Negative ambience." against
"the restaurant's ambience is often described negatively") and matches
unrelated strings ("uniform size profile absent" against "Unpleasant or
undesirable atmosphere", 0.444 against a 0.35 threshold). Content-word Jaccard
at 0.10 is right in both directions on every observe-mode strategy output and
every frozen O5 corpus issue (JOURNAL_PLAN 17.2).

This module is the **single copy** of that tokeniser. ``score_repair`` uses it
to decide whether O5's check still fires; ``matcher_shrinkage`` uses it to
measure why. Two private copies would let the measurement and the decision
drift onto different definitions without saying so.

The production supervisor does **not** use it. D22 keeps the system under study
identical to the one paper #1 describes and corrects only the measurement.

The tokeniser is the one ``verify_claim3.py`` used for the D13 audit numbers,
copied verbatim, so those numbers and this decision rest on the same definition.
"""

from __future__ import annotations

import re
from collections.abc import Iterable

# Fixed on pre-study calibration data before any trial outcome existed
# (JOURNAL_PLAN 17.2). A change is a PREREGISTRATION amendment, not a tweak.
TRACE_JACCARD = 0.10

# O5's identity anchor: locating the corrupted recommendation in a regenerated
# output by its untouched ``action`` (D24, JOURNAL_PLAN 17.5). Calibrated on the
# upstream-stable repetition pairs, where recommendation counts barely move, so a
# failure to locate is almost always a false ``deleted``. Rule, stated before the
# choice: the lowest false-deletion rate among matchers whose within-output
# ambiguity is no worse than the production matcher's. Production 0.35 on
# characters deletes 70% of an unperturbed re-draw; this deletes 17%, at the same
# 3% ambiguity. 0.10 fails the ambiguity rule (40%); 0.30 still deletes 39%.
ANCHOR_JACCARD = 0.20

STOP = frozenset(
    "a an the and or of to in for on with is are be been being that this those these "
    "at by from as it its their there here we you they i not no more most very can could "
    "should would may might will shall do does did have has had".split()
)


def tokens(text: str | None) -> set[str]:
    """Lower-cased alphabetic words of three or more letters, stopwords removed."""
    return {w for w in re.findall(r"[a-z]+", (text or "").lower()) if w not in STOP and len(w) > 2}


def jaccard(a: str | None, b: str | None) -> float:
    ta, tb = tokens(a), tokens(b)
    return len(ta & tb) / len(ta | tb) if (ta | tb) else 0.0


def containment(issue: str | None, candidate: str | None) -> float:
    """Share of the issue's content words that also appear in the candidate."""
    ti = tokens(issue)
    return len(ti & tokens(candidate)) / len(ti) if ti else 0.0


def best_jaccard(text: str, candidates: Iterable[str]) -> float:
    return max((jaccard(text, c) for c in candidates if c), default=0.0)


def untraceable(issues: Iterable[str], candidates: Iterable[str],
                threshold: float = TRACE_JACCARD) -> list[str]:
    """The issues that share too few content words with every upstream candidate.

    The content-word analogue of ``supervision._measure_strategy``'s
    ``untraceable_issues``, over the same candidate strings.
    """
    pool = [c for c in candidates if c]
    return [i for i in issues if best_jaccard(i, pool) < threshold]
