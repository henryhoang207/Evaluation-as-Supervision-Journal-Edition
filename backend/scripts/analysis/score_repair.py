"""Outcome scorer for injection trials (JOURNAL_PLAN B6).

Turns one trial — (pre-injection output, retried output, descriptor; the
injected output is reconstructible from the first and last) — into D3b's
outcome structure: a **4-class multinomial**
``repaired | replaced | deleted | unrepaired`` crossed with a **binary
collateral flag**. Collateral is a second dimension, not a fifth class; the
*original* four classes were not mutually exclusive (``collateral`` overlapped
``repaired_clean``) and could not be the multinomial D4 analysed. These four
are, because they are decided in a fixed order — see :func:`score`.

Three corrections from the plan are the whole point of this module.

**The success criterion is replacement value, not descriptor disappearance
(D3, section 13.5).** "The injected defect no longer fires" is the wrong test: a
fabricated evidence id swapped for a *different* fabricated-but-resolving id
stops the check firing while the output is still wrong. So a passing check is
compared against the **pre-injection** item, and only a match counts as
``repaired``. Anything else that passes is ``replaced``.

**Collateral is set-overlap against the pre-injection output, not "anything
changed" (B6).** Retry regenerates the whole stage rather than editing the
faulty artifact (D17), so "any added/removed/altered item beyond the injected
one" is true of essentially every trial in every arm and pins at ~100%. What
discriminates is whether the *unrelated* items survive semantically, measured
against the churn an unperturbed pipeline already produces (D3c) — which differs
by an order of magnitude across item classes, so there is no single threshold.

``replaced`` is only reachable for operators that substitute a value (O1, O2,
O3, O5). A deletion-style operator (O6, O7) either leaves an invented item, in
which case the check still fires, or does not; O8 likewise. ``CAN_REPLACE``
records this so an empty cell reads as structural rather than as a null result.

**Deleting the offending item is its own outcome, not a repair and not a wrong
replacement (D18).** Before this class existed the same model behaviour scored
two different ways depending on which operator ran: dropping the flagged
pattern scored ``replaced`` for O1/O2/O3/O5 (the value lookup returned None and
fell through to the replacement branch) and ``repaired`` for O6/O7. For an
*insertion* operator that is correct — the item was invented, so removing it is
the fix, and O6/O7 keep scoring ``repaired``. For a *substitution* operator it
is evasion: an item that should exist is gone, and the check passes only
because there is nothing left to check. ``CAN_DELETE`` marks the operators for
which that distinction is meaningful.

Deletion is decided by **identity, not by index**. Retry regenerates the whole
stage (D17), so the pattern that was at index 2 in the base may be at index 0
in the retried output, or reworded. Each substitution operator therefore has an
untouched field that anchors the item across a regeneration (``IDENTITY_ANCHOR``
below): O1/O2/O3 corrupt evidence ids or the aspect and leave ``description``
alone, O5 rewrites ``issue`` and leaves ``action`` alone. Index identity would
have scored every retry that emitted fewer patterns as ``deleted``.

**O5's check is scored on content words, not with the production matcher
(D22).** The production trace check compares characters: it flags 8 of 49
*correct* observe-mode strategy outputs and calls alien content traceable in 6
of 168 pairs (JOURNAL_PLAN 17.2), so re-running it to decide whether O5 "still
fires" would score correct regenerations ``unrepaired``. The outcome uses
``content_match``; the production verdict is kept in ``detail`` as a reported
secondary. The production supervisor itself is untouched — the bug was measured
not to reach O5's bases, injected issue, trigger or feedback.

Run (from backend/, venv active — read-only, no API calls, no dataset):

    python scripts/analysis/score_repair.py --selftest
"""

from __future__ import annotations

import argparse
import importlib.util
import os
import sys
from dataclasses import asdict, dataclass, field
from typing import Any

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from app.core import supervision  # noqa: E402


def _load_by_path(name: str, path: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


_HERE = os.path.dirname(os.path.abspath(__file__))
defect_bank = _load_by_path("defect_bank", os.path.join(_HERE, "defect_bank.py"))
# The churn floors below were calibrated with churn.matched_fraction, which does
# GREEDY ONE-TO-ONE matching. Reimplementing the comparison here with a plain
# any() would let one retried item cover several pre-injection items, understate
# churn, and quietly apply floors that were measured under a different rule.
churn_mod = _load_by_path("churn", os.path.join(_HERE, "churn.py"))
inject_defects = _load_by_path(
    "inject_defects", os.path.join(os.path.dirname(_HERE), "inject_defects.py")
)
# D22: the O5 trace check is scored on content words, not with the production
# matcher. One shared tokeniser, also used by matcher_shrinkage.py.
content_match = _load_by_path("content_match", os.path.join(_HERE, "content_match.py"))


# ── churn floors (D3c — measured, not chosen) ─────────────────────────────────
#
# scripts/analysis/churn.py measures what an *unperturbed* pipeline already
# churns across identical runs (same 5 businesses, 5 runs, same seed,
# temperature 0, no injection, no feedback). Collateral means churn above the
# floor for that item class. The floors differ by an order of magnitude, which
# is why D3c rejects a single threshold.
#
# The strategy figure is the **conditioned** 0.23, not the raw 0.37: repetition
# runs regenerate every stage, so strategy churn there compounds reasoning
# churn, whereas a replay trial pins upstream from the dump.
CHURN_FLOOR: dict[str, float] = {
    "pattern_aspect": 0.07,       # closed 7-value enum
    "pattern_description": 0.33,
    "root_cause": 0.29,
    "recommendation_issue": 0.23,  # conditioned on stable upstream (n=13 pairs)
}

# Two strings are "the same item" at or above this similarity. Deliberately the
# same constant the supervisor traces with, so the scorer and the checks share
# one notion of sameness. D3d is the reason this cannot be exact matching:
# across identical runs, exact-match rates are 0.01 for pattern descriptions,
# 0.03 for root causes and 0.00 for recommendation issues.
SAME_ITEM = supervision.TRACE_SIMILARITY

# Operators for which a passing check can still be a wrong value.
CAN_REPLACE: frozenset[str] = frozenset({"O1", "O2", "O3", "O5"})

# Operators for which the flagged item is one the clean output HAD, so its
# absence from the retried output is evasion rather than repair (D18). D18 named
# this set separately from CAN_REPLACE although the two then coincided, on the
# grounds that an operator added later might satisfy one and not the other.
# **O4 is that operator** (D19): dropping the pattern rather than making a
# frequency claim is evasion, so O4 can be deleted — but a frequency within
# tolerance of the recomputed value is correct *by construction*, so O4 has no
# passes-but-wrong-value mode and is deliberately absent from CAN_REPLACE.
# For an insertion operator (O6, O7) deletion IS the repair, so those are absent
# from both and keep scoring ``repaired``.
CAN_DELETE: frozenset[str] = frozenset({"O1", "O2", "O3", "O4", "O5"})

# The field each operator does NOT touch, used to find the injected item's host
# in a regenerated output. Wrong anchors silently mis-locate the item, so each is
# justified against the operator in scripts/inject_defects.py:
#   O1 `_apply_o1` / O2 `_apply_o2` mutate evidence_review_ids
#   O3 `_apply_o3` mutates aspect
#   O4 `_apply_o4` mutates frequency and leaves description alone (D19)
#   O5 `_apply_o5` mutates issue and leaves action alone
# Operators whose anchor is matched on content words rather than characters
# (D24). O5's anchor is a whole recommended action — a sentence the model
# paraphrases on every regeneration — and the production matcher located only
# 30% of recommendations in an unperturbed re-draw, scoring the rest `deleted`.
# That error is placement-linked (A3 re-draws at P0; A1/A2 see the artifact at
# P1 and can copy it), so it would bias the A2-vs-A3 confirmatory test rather
# than add noise. Pattern descriptions (O1-O4) are short, and the production
# matcher locates 97% of them in a re-draw, so they stay on characters.
CONTENT_ANCHORED: frozenset[str] = frozenset({"O5"})

IDENTITY_ANCHOR: dict[str, str] = {
    "O1": "description", "O2": "description", "O3": "description",
    "O4": "description", "O5": "action",
}

# The one check class whose outcome is scored on content words (D22).
TRACE_CHECK_CLASS = "untraceable_recommendation"

REPAIRED, REPLACED, DELETED, UNREPAIRED = (
    "repaired", "replaced", "deleted", "unrepaired",
)
OUTCOME_CLASSES = (REPAIRED, REPLACED, DELETED, UNREPAIRED)


@dataclass
class Outcome:
    outcome: str
    collateral: bool
    collateral_measurable: bool
    check_fired: bool
    operator: str
    stage: str
    fired_classes: list[str] = field(default_factory=list)
    churn: dict[str, float] = field(default_factory=dict)
    detail: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


# ── item extraction ───────────────────────────────────────────────────────────


def _items(state: dict, kind: str) -> list[str]:
    """The item list for one churn class, as comparable strings."""
    reasoning = state.get("reasoning_output") or {}
    if kind == "pattern_aspect":
        return [str(p.get("aspect")) for p in reasoning.get("patterns") or []]
    if kind == "pattern_description":
        return [str(p.get("description") or "") for p in reasoning.get("patterns") or []]
    if kind == "root_cause":
        return [str(rc.get("cause") or "") for rc in reasoning.get("root_causes") or []]
    if kind == "recommendation_issue":
        return [
            str(r.get("issue") or "")
            for r in (state.get("strategy_output") or {}).get("recommendations") or []
        ]
    report = state.get("report_output") or {}
    if kind == "report_root_cause":
        return [str(rc.get("cause") or "") for rc in report.get("root_causes") or []]
    if kind == "report_recommendation":
        return [str(r.get("issue") or "") for r in report.get("recommendations") or []]
    raise ValueError(f"unknown item kind {kind!r}")


# Which churn class holds the item each substitution operator corrupted. The
# injected item must be excluded from the collateral measure, or the two
# dimensions stop being independent: dropping the flagged pattern would score
# `deleted` AND raise `collateral` off the same event, and on a single-pattern
# base that pins churn at 1.0 (D18). Insertion operators (O6, O7) are absent
# because they add an item the base never had, so no pre-injection item is
# theirs to exclude.
INJECTED_KINDS: dict[str, tuple[str, ...]] = {
    "O1": ("pattern_aspect", "pattern_description"),
    "O2": ("pattern_aspect", "pattern_description"),
    "O3": ("pattern_aspect", "pattern_description"),
    "O5": ("recommendation_issue",),
}


def _pre_items_excluding_injected(base_state: dict, kind: str, descriptor) -> list[str]:
    """``_items`` on the base, minus the item the operator corrupted.

    Index lookup is safe: the base is the state the descriptor's index was
    recorded against. Only the *retried* side needs identity matching.

    ⚠ **Granularity, not bias.** The D3c floors were calibrated over full item
    lists; this rate is over n-1 items. Both estimate the same quantity — the
    per-item probability of loss — so the comparison is sound, and lost/(n-1)
    is the right estimator for the non-injected population rather than a
    rescale to lost/n, which would understate it. What *does* change is
    resolution: the flag can only move in steps of 1/(n-1), so on a small base
    one lost item can land either side of a floor. Measured: with a 4-pattern
    base losing one unrelated pattern, the rate is 0.333 against a 0.33 floor
    (flags) where the full-list rate is 0.250 (does not). Collateral is
    exploratory and the design is matched — every arm for a defect shares the
    same base and the same exclusion — so this affects the absolute rate's
    resolution, never the between-arm comparison. Report per-operator n
    alongside the collateral rate.
    """
    items = _items(base_state, kind)
    if kind not in INJECTED_KINDS.get(descriptor.operator, ()):
        return items
    idx = _host_index(descriptor)
    if idx is None or idx >= len(items):
        return items
    return items[:idx] + items[idx + 1:]


# Item classes with a calibrated D3c floor — only these can raise the collateral
# flag, because a flag needs a threshold and a threshold needs a measurement.
KINDS_BY_STAGE: dict[str, tuple[str, ...]] = {
    "reasoning_agent": ("pattern_aspect", "pattern_description", "root_cause"),
    "strategy_agent": ("recommendation_issue",),
    "report_agent": (),
}

# Report-stage items were never calibrated: churn.py measures reasoning and
# strategy items only. Their churn is still recorded — it is free and a reader
# will want it — but it cannot raise the flag, and ``collateral_measurable``
# says so on every row. Defaulting these to collateral=False would report "no
# collateral damage" for O6, O7 and O8 when the truth is "never checked", and
# two of the six repair operators live at this stage.
UNCALIBRATED_KINDS: dict[str, tuple[str, ...]] = {
    "report_agent": ("report_root_cause", "report_recommendation"),
}


def churn_rate(pre: list[str], post: list[str], exact: bool = False) -> float:
    """Fraction of pre-injection items with no counterpart in the retried output.

    Delegates to ``churn.matched_fraction`` / ``churn.exact_fraction`` — the
    same functions that produced CHURN_FLOOR — so the scorer and the
    calibration cannot drift into two different notions of "the same item".

    Directional on purpose: a dropped item is collateral damage, whereas an
    added item is the stage being more verbose, which the supervisor judges
    separately.
    """
    if not pre:
        # Nothing to lose. matched_fraction returns 0.0 for an empty `pre`
        # against a non-empty `post`, which would read as 100% churn — and once
        # the injected item is excluded (D18) an empty `pre` is reachable
        # whenever the base carried exactly one item of that class.
        return 0.0
    matched = (
        churn_mod.exact_fraction(pre, post) if exact
        else churn_mod.matched_fraction(pre, post, SAME_ITEM)
    )
    if matched is None:  # both sides empty — nothing to lose
        return 0.0
    return 1.0 - matched


# ── the injected item, before and after ───────────────────────────────────────


def _hosts(state: dict, op: str) -> list[dict]:
    """The item list the operator corrupts one element of."""
    if op in ("O1", "O2", "O3", "O4"):
        return (state.get("reasoning_output") or {}).get("patterns") or []
    if op == "O5":
        return (state.get("strategy_output") or {}).get("recommendations") or []
    return []


def _host_index(descriptor) -> int | None:
    key = "recommendation_index" if descriptor.operator == "O5" else "pattern_index"
    return (descriptor.target or {}).get(key)


def _base_host(base_state: dict, descriptor) -> dict | None:
    """The pre-injection item the operator corrupted.

    Index lookup is correct *here* and only here: the descriptor's index was
    recorded against this exact state when the injection was applied.
    """
    if descriptor.operator not in IDENTITY_ANCHOR:
        return None
    hosts = _hosts(base_state, descriptor.operator)
    idx = _host_index(descriptor)
    if idx is None or idx >= len(hosts):
        return None
    return hosts[idx]


def _locate_host(state: dict, descriptor, base_host: dict | None) -> dict | None:
    """The same item in a *regenerated* state, found by its untouched anchor.

    Returns None when nothing in ``state`` corresponds to it — which is what
    ``deleted`` means. Identity, not index: a retry that emits the same pattern
    in a different position, or reworded above the similarity threshold, has not
    deleted anything (D18).
    """
    op = descriptor.operator
    if base_host is None or op not in IDENTITY_ANCHOR:
        return None
    anchor = IDENTITY_ANCHOR[op]
    want = str(base_host.get(anchor) or "")
    if not want:
        # No anchor value to match on. Fall back to the recorded index rather
        # than reporting a deletion that was never observed — a false `deleted`
        # is worse than a false `replaced`, because it is the class the
        # dichotomy treats as failure.
        hosts = _hosts(state, op)
        idx = _host_index(descriptor)
        return hosts[idx] if idx is not None and idx < len(hosts) else None

    if op in CONTENT_ANCHORED:
        similarity, floor = content_match.jaccard, content_match.ANCHOR_JACCARD
    else:
        similarity, floor = supervision._similar, SAME_ITEM
    best, best_score = None, floor
    for cand in _hosts(state, op):
        score_ = similarity(want, str(cand.get(anchor) or ""))
        if score_ >= best_score:
            best, best_score = cand, score_
    return best


def _injected_value(host: dict | None, op: str) -> Any:
    """The field the operator corrupted, read out of a located item."""
    if host is None:
        return None
    if op in ("O1", "O2"):
        return list(host.get("evidence_review_ids") or [])
    if op == "O3":
        return host.get("aspect")
    if op == "O5":
        return host.get("issue")
    return None


def _item_restored(op: str, pre: Any, post: Any) -> bool:
    """Did the retried output restore the pre-injection value of the item?

    Evidence-id lists compare as sets: order carries no meaning to the check,
    and requiring order would score a reordering as a wrong replacement.
    """
    if pre is None or post is None:
        return False
    if op in ("O1", "O2"):
        return set(pre) == set(post)
    if op == "O3":
        return pre == post
    if op == "O5":
        return supervision._similar(str(pre), str(post)) >= SAME_ITEM
    return False


# ── scoring ───────────────────────────────────────────────────────────────────


def score(
    descriptor,
    base_state: dict,
    retried_state: dict,
    floors: dict[str, float] | None = None,
) -> Outcome:
    """Classify one trial.

    ``base_state`` is the **pre-injection** output — the correct one. That is
    what makes this a replacement-value test rather than a
    did-the-descriptor-stop-firing test.

    The four classes are decided in a fixed order, which is what makes them
    mutually exclusive and therefore a multinomial at all (D3b, D18):

    1. the check still fires                    → ``unrepaired``
    2. the item is gone (substitution operator) → ``deleted``
    3. the item is back to its clean value      → ``repaired``
    4. otherwise                                → ``replaced``

    Step 2 is skipped for insertion operators (O6, O7), where the item's
    absence is the repair. An evidence list that survives but is *empty* is not
    ``deleted``: the pattern is still asserted, now with no support at all,
    which is a wrong value rather than a missing item.
    """
    floors = {**CHURN_FLOOR, **(floors or {})}
    stage = descriptor.stage
    op = descriptor.operator

    facts = supervision.measure(stage, retried_state)
    fired = defect_bank.fired_classes(stage, facts)
    if descriptor.check_class == "frequency_divergence":
        check_fired_production = defect_bank.frequency_divergent(
            facts, supervision.FREQUENCY_TOLERANCE)
    else:
        check_fired_production = descriptor.check_class in fired

    # D22: for the trace check the production matcher is not a valid measure of
    # the outcome (module docstring). Same semantics as the production check —
    # any recommendation in the regenerated output that fails to trace — decided
    # on content words instead of characters.
    untraceable_content: list[str] | None = None
    if descriptor.check_class == TRACE_CHECK_CLASS:
        untraceable_content = content_match.untraceable(
            _items(retried_state, "recommendation_issue"),
            inject_defects._trace_candidates(retried_state),
        )
        check_fired = bool(untraceable_content)
    else:
        check_fired = check_fired_production

    base_host = _base_host(base_state, descriptor)
    post_host = _locate_host(retried_state, descriptor, base_host)
    pre_item = _injected_value(base_host, op)
    post_item = _injected_value(post_host, op)
    restored = _item_restored(op, pre_item, post_item)
    item_deleted = op in CAN_DELETE and base_host is not None and post_host is None

    if check_fired:
        outcome = UNREPAIRED
    elif item_deleted:
        # The offending item is gone rather than corrected. The check passes
        # only because there is nothing left to check, so this is neither a
        # repair nor a wrong replacement value (D18).
        outcome = DELETED
    elif op in CAN_REPLACE and not restored:
        # The check passes but the value is not the one the clean stage
        # produced. This is section 13.5's case and the reason the criterion is
        # not "the descriptor stopped firing".
        outcome = REPLACED
    else:
        outcome = REPAIRED

    churn: dict[str, float] = {}
    collateral = False
    calibrated = KINDS_BY_STAGE.get(stage, ())
    for kind in calibrated:
        rate = churn_rate(
            _pre_items_excluding_injected(base_state, kind, descriptor),
            _items(retried_state, kind),
            exact=(kind == "pattern_aspect"),
        )
        churn[kind] = round(rate, 3)
        if rate > floors[kind]:
            collateral = True
    for kind in UNCALIBRATED_KINDS.get(stage, ()):
        churn[kind] = round(
            churn_rate(
                _pre_items_excluding_injected(base_state, kind, descriptor),
                _items(retried_state, kind),
            ), 3
        )

    return Outcome(
        outcome=outcome,
        collateral=collateral,
        collateral_measurable=bool(calibrated),
        check_fired=check_fired,
        operator=op,
        stage=stage,
        fired_classes=fired,
        churn=churn,
        detail={
            "pre_item": pre_item,
            "post_item": post_item,
            "item_restored": restored,
            "item_located": post_host is not None,
            "identity_anchor": IDENTITY_ANCHOR.get(op),
            "anchor_matcher": (f"content_jaccard>={content_match.ANCHOR_JACCARD}"
                               if op in CONTENT_ANCHORED else "production"),
            "can_replace": op in CAN_REPLACE,
            "can_delete": op in CAN_DELETE,
            "verdict": supervision.decide(stage, facts, {}).verdict,
            # D22: the production check's own answer, reported as a secondary.
            "check_fired_production": check_fired_production,
            "trace_matcher": (f"content_jaccard>={content_match.TRACE_JACCARD}"
                              if untraceable_content is not None else "production"),
            "untraceable_content": untraceable_content,
        },
    )


def tabulate(outcomes: list[Outcome]) -> dict:
    """Per-operator counts with applicable-trial denominators (B6).

    ``repair_rate`` is the **pre-registered primary dichotomy** (D18): strictly
    ``repaired`` over n. ``deleted`` counts against it, because deleting the
    item the supervisor complained about is not a repair — otherwise
    "drop the pattern you were asked about" would score as a supervisor
    success. The other three classes are reported alongside so the reader can
    recompose any looser criterion; the confirmatory tests may not.
    """
    table: dict[str, dict] = {}
    for o in outcomes:
        row = table.setdefault(
            o.operator,
            {"n": 0, REPAIRED: 0, REPLACED: 0, DELETED: 0, UNREPAIRED: 0,
             "collateral": 0, "n_collateral_measurable": 0,
             "can_replace": o.operator in CAN_REPLACE,
             "can_delete": o.operator in CAN_DELETE},
        )
        row["n"] += 1
        row[o.outcome] += 1
        # Collateral gets its own denominator: a stage with no calibrated floor
        # contributes trials to n but cannot contribute to the collateral rate.
        if o.collateral_measurable:
            row["n_collateral_measurable"] += 1
            row["collateral"] += int(o.collateral)
    for row in table.values():
        row["repair_rate"] = round(row[REPAIRED] / row["n"], 3) if row["n"] else None
        m = row["n_collateral_measurable"]
        row["collateral_rate"] = round(row["collateral"] / m, 3) if m else None
    return table


# ── selftest ──────────────────────────────────────────────────────────────────


def _selftest() -> int:
    """The section 13.5 case, runnable without pytest."""
    base = {
        "business_id": "b1", "business_name": "Test Diner",
        "analysis_results": [
            {"review_id": "rA", "status": "success",
             "aspects": [{"category": "food_quality", "label": "negative"}]},
            {"review_id": "rB", "status": "success",
             "aspects": [{"category": "food_quality", "label": "negative"}]},
        ],
        "reasoning_output": {
            "status": "success", "root_causes": [],
            "patterns": [{"description": "cold food", "aspect": "food_quality",
                          "frequency": 1.0, "evidence_review_ids": ["rA"]}],
        },
        "strategy_output": None, "report_output": None,
    }
    injected, descriptor = inject_defects.inject("O1", base, seed=0)
    assert descriptor.applied, descriptor.reason

    # Retry swaps the corrupted id for a DIFFERENT id that resolves. The check
    # passes; the value is still not the one the clean stage produced.
    retried = {**base, "reasoning_output": {
        "status": "success", "root_causes": [],
        "patterns": [{"description": "cold food", "aspect": "food_quality",
                      "frequency": 1.0, "evidence_review_ids": ["rB"]}]}}
    out = score(descriptor, base, retried)
    assert out.outcome == REPLACED, out.outcome
    assert not out.check_fired

    # Retry restores the original id.
    good = {**base, "reasoning_output": base["reasoning_output"]}
    assert score(descriptor, base, good).outcome == REPAIRED

    # Retry leaves the corruption in place.
    assert score(descriptor, base, injected).outcome == UNREPAIRED

    # D18: retry drops the flagged pattern instead of correcting it. Neither a
    # repair nor a wrong replacement value — and the deletion must not also
    # register as collateral damage off the same event.
    dropped = {**base, "reasoning_output": {
        "status": "success", "root_causes": [], "patterns": []}}
    out = score(descriptor, base, dropped)
    assert out.outcome == DELETED, out.outcome
    assert not out.check_fired
    assert not out.collateral, out.churn

    print("selftest OK — 13.5 replacement-value case discriminates; "
          "D18 deletion class separates")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        return _selftest()
    ap.error("nothing to do; --selftest is the only offline entry point")


if __name__ == "__main__":
    sys.exit(main())
