"""Tests for the outcome scorer (JOURNAL_PLAN B6).

Two gates the plan requires before any trial runs:

1. **The section 13.5 replacement-value case.** A fabricated evidence id swapped
   for a *different* fabricated-but-resolving id must score ``replaced``, not
   ``repaired`` — the check passes but the output is still wrong.
2. **Collateral must discriminate.** B6 predicts the originally specified metric
   ("any added/removed/altered item beyond the injected one") pins at ~100% in
   every arm, because retry regenerates the stage rather than editing it. Both
   halves of that prediction are checked here against the real repetition runs,
   which are genuine unperturbed regenerations of the same input.
"""

import importlib.util
import os
import sys
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parent.parent
STUDY_ROOT = BACKEND / "out_study"


def _load_module(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, BACKEND / relative)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


score_repair = _load_module("score_repair", "scripts/analysis/score_repair.py")
inject_defects = _load_module("inject_defects", "scripts/inject_defects.py")

from app.core import supervision  # noqa: E402

needs_study = pytest.mark.skipif(
    not (STUDY_ROOT / "R").is_dir(), reason="backend/out_study/R not present"
)

REPAIRED = score_repair.REPAIRED
REPLACED = score_repair.REPLACED
DELETED = score_repair.DELETED
UNREPAIRED = score_repair.UNREPAIRED


def _base_state():
    """Two reviews on the same aspect, one pattern citing the first."""
    return {
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


def _with_evidence(base, ids):
    out = {k: v for k, v in base.items()}
    out["reasoning_output"] = {
        "status": "success", "root_causes": [],
        "patterns": [{"description": "cold food", "aspect": "food_quality",
                      "frequency": 1.0, "evidence_review_ids": list(ids)}],
    }
    return out


# ── gate 1: replacement value (section 13.5) ──────────────────────────────────


def test_a_different_resolving_id_is_replaced_not_repaired():
    """THE section 13.5 case. The check passes; the value is still wrong."""
    base = _base_state()
    _, descriptor = inject_defects.inject("O1", base, seed=0)
    assert descriptor.applied

    outcome = score_repair.score(descriptor, base, _with_evidence(base, ["rB"]))

    assert outcome.check_fired is False, "a resolving id must not trip the check"
    assert outcome.outcome == REPLACED
    assert outcome.detail["item_restored"] is False


def test_restoring_the_original_id_is_repaired():
    base = _base_state()
    _, descriptor = inject_defects.inject("O1", base, seed=0)
    outcome = score_repair.score(descriptor, base, _with_evidence(base, ["rA"]))
    assert outcome.outcome == REPAIRED
    assert outcome.detail["item_restored"] is True


def test_leaving_the_corruption_is_unrepaired():
    base = _base_state()
    injected, descriptor = inject_defects.inject("O1", base, seed=0)
    outcome = score_repair.score(descriptor, base, injected)
    assert outcome.outcome == UNREPAIRED
    assert outcome.check_fired is True


def test_evidence_ids_compare_as_a_set_not_a_sequence():
    """Reordering evidence is not a wrong replacement — the check ignores order."""
    base = _base_state()
    base["reasoning_output"]["patterns"][0]["evidence_review_ids"] = ["rA", "rB"]
    _, descriptor = inject_defects.inject("O1", base, seed=0)
    outcome = score_repair.score(descriptor, base, _with_evidence(base, ["rB", "rA"]))
    assert outcome.outcome == REPAIRED


def test_replaced_is_unreachable_for_deletion_operators():
    """O6/O7/O8 have no wrong-replacement mode; an empty cell is structural."""
    assert "O6" not in score_repair.CAN_REPLACE
    assert "O7" not in score_repair.CAN_REPLACE
    assert "O8" not in score_repair.CAN_REPLACE
    assert score_repair.CAN_REPLACE == frozenset({"O1", "O2", "O3", "O5"})


# ── gate 1b: the deletion class (D18) ─────────────────────────────────────────


def _with_patterns(base, patterns):
    out = {k: v for k, v in base.items()}
    out["reasoning_output"] = {
        "status": "success", "root_causes": [], "patterns": list(patterns),
    }
    return out


def test_dropping_the_flagged_pattern_is_deleted_not_replaced():
    """THE D18 case. Before the class existed this scored `replaced`.

    The check passes only because there is nothing left to check, so this is
    neither a repair nor a wrong replacement value.
    """
    base = _base_state()
    _, descriptor = inject_defects.inject("O1", base, seed=0)
    outcome = score_repair.score(descriptor, base, _with_patterns(base, []))

    assert outcome.check_fired is False
    assert outcome.outcome == DELETED
    assert outcome.detail["item_located"] is False


def test_deletion_does_not_also_register_as_collateral():
    """The two dimensions must stay independent.

    Scoring the deleted item as collateral damage counts one event twice, and
    on a single-pattern base it pins churn at 1.0 — so `deleted` would imply
    `collateral` by construction rather than by measurement.
    """
    base = _base_state()
    _, descriptor = inject_defects.inject("O1", base, seed=0)
    outcome = score_repair.score(descriptor, base, _with_patterns(base, []))
    assert outcome.collateral is False, outcome.churn
    assert outcome.churn["pattern_description"] == 0.0


def test_an_unrelated_pattern_lost_alongside_the_injected_one_is_collateral():
    """Excluding the injected item must not blind the metric to real damage."""
    base = _base_state()
    # Same aspect and frequency as the first pattern, so the base stays clean:
    # an unmentioned aspect would trip misaligned_aspect and refuse the
    # injection, and a frequency the supervisor recomputes differently would
    # trip frequency_divergence.
    base["reasoning_output"]["patterns"].append(
        {"description": "portions much smaller than advertised",
         "aspect": "food_quality", "frequency": 1.0, "evidence_review_ids": ["rB"]}
    )
    _, descriptor = inject_defects.inject("O1", base, seed=0)
    assert descriptor.applied, descriptor.reason
    idx = score_repair._host_index(descriptor)
    survivor = base["reasoning_output"]["patterns"][1 - idx]

    # Only the injected pattern comes back; the unrelated one is gone.
    injected_desc = base["reasoning_output"]["patterns"][idx]
    outcome = score_repair.score(descriptor, base, _with_patterns(base, [injected_desc]))
    assert outcome.collateral is True, (
        f"losing {survivor['description']!r} must still count as collateral"
    )


def test_a_reordered_pattern_is_not_deleted():
    """Identity, not index (D17): retry regenerates, so positions move.

    Index-based lookup scored every retry that emitted fewer patterns as a
    deletion, which is the common case rather than the exception.
    """
    base = _base_state()
    # Same aspect and frequency as the first pattern, so the base stays clean:
    # an unmentioned aspect would trip misaligned_aspect and refuse the
    # injection, and a frequency the supervisor recomputes differently would
    # trip frequency_divergence.
    base["reasoning_output"]["patterns"].append(
        {"description": "portions much smaller than advertised",
         "aspect": "food_quality", "frequency": 1.0, "evidence_review_ids": ["rB"]}
    )
    _, descriptor = inject_defects.inject("O1", base, seed=0)
    assert descriptor.applied, descriptor.reason
    idx = score_repair._host_index(descriptor)

    # Both patterns come back correctly, with their positions swapped. Index
    # lookup at `idx` now reads the OTHER pattern's evidence and scores
    # `replaced`; identity lookup reads the right one. Swapping rather than
    # truncating keeps the test discriminating whichever index the injector's
    # RNG happens to pick — truncation only exercises the identity path when
    # idx != 0, which is a property of the seed, not of the code.
    patterns = base["reasoning_output"]["patterns"]
    swapped = _with_patterns(base, list(reversed(patterns)))
    assert swapped["reasoning_output"]["patterns"].index(patterns[idx]) != idx

    outcome = score_repair.score(descriptor, base, swapped)
    assert outcome.outcome == REPAIRED, outcome.detail
    assert outcome.detail["item_located"] is True
    assert outcome.collateral is False, "nothing was lost — only reordered"


def test_an_emptied_evidence_list_is_replaced_not_deleted():
    """The boundary, chosen rather than stumbled into.

    A pattern asserted with no supporting evidence at all is still asserted —
    a wrong value, not a missing item.
    """
    base = _base_state()
    _, descriptor = inject_defects.inject("O1", base, seed=0)
    outcome = score_repair.score(descriptor, base, _with_evidence(base, []))
    assert outcome.outcome == REPLACED
    assert outcome.detail["item_located"] is True


def test_deletion_is_the_repair_for_insertion_operators():
    """O6/O7 invent an item; removing it is the fix, not an evasion."""
    assert "O6" not in score_repair.CAN_DELETE
    assert "O7" not in score_repair.CAN_DELETE
    assert "O8" not in score_repair.CAN_DELETE
    assert score_repair.CAN_DELETE == frozenset({"O1", "O2", "O3", "O4", "O5"})


def test_o4_can_be_deleted_but_never_replaced():
    """D19, and the divergence D18 named the two sets separately to allow.

    Dropping the pattern rather than making a frequency claim is evasion, so O4
    can be `deleted`. But a frequency within tolerance of the recomputed value
    is correct *by construction* — there is no passes-but-wrong-value mode — so
    O4 must stay out of CAN_REPLACE or every genuine repair would score
    `replaced`.
    """
    assert "O4" in score_repair.CAN_DELETE
    assert "O4" not in score_repair.CAN_REPLACE
    assert score_repair.CAN_DELETE != score_repair.CAN_REPLACE


def test_identity_anchors_are_fields_the_operator_leaves_alone():
    """A wrong anchor silently mis-locates the item and fabricates deletions."""
    assert score_repair.IDENTITY_ANCHOR == {
        "O1": "description", "O2": "description", "O3": "description",
        "O4": "description", "O5": "action",
    }
    # The anchor must never be the field the operator mutates.
    assert score_repair.IDENTITY_ANCHOR["O3"] != "aspect"
    assert score_repair.IDENTITY_ANCHOR["O4"] != "frequency"
    assert score_repair.IDENTITY_ANCHOR["O5"] != "issue"


def test_dropping_the_pattern_under_o4_is_deleted_not_repaired():
    """Before D19 wired O4 into IDENTITY_ANCHOR this scored `repaired`.

    O4 had no anchor, so `_base_host` returned None, `item_deleted` could never
    be True, and O4 is not in CAN_REPLACE — so a retry that answered "no
    frequency claim at all" fell straight through to `repaired`. That is the
    same evasion D18 fixed for the substitution operators.
    """
    base = _base_state()
    _, descriptor = inject_defects.inject("O4", base, seed=0)
    assert descriptor.applied

    outcome = score_repair.score(descriptor, base, _with_patterns(base, []))
    assert outcome.check_fired is False
    assert outcome.outcome == DELETED


def test_recomputing_the_frequency_under_o4_is_repaired():
    """The other side of the same path: O4 has no wrong-but-passing mode."""
    base = _base_state()
    injected, descriptor = inject_defects.inject("O4", base, seed=0)
    assert descriptor.applied
    assert injected["reasoning_output"]["patterns"][0]["frequency"] !=         base["reasoning_output"]["patterns"][0]["frequency"]

    # The retried output restores the frequency the checker would recompute.
    outcome = score_repair.score(descriptor, base, base)
    assert outcome.check_fired is False
    assert outcome.outcome == REPAIRED


def test_empty_pre_after_exclusion_is_zero_churn_not_total_churn():
    """churn.matched_fraction returns 0.0 matched for an empty `pre`.

    Passed through unguarded that reads as 100% churn — reachable now that the
    injected item is excluded from a base carrying one item of its class.
    """
    assert score_repair.churn_rate([], ["anything at all"]) == 0.0


# ── gate 2: collateral must discriminate ──────────────────────────────────────


def _rep_pairs():
    """(rep_i, rep_j) dumps of the same business — the calibration's own unit.

    churn.py compares repetitions against each other, not against Phase A, so
    this mirrors it exactly. These are unperturbed regenerations at temperature
    0 with no injection and no feedback.
    """
    import itertools

    r_root = STUDY_ROOT / "R"
    reps = sorted(d for d in os.listdir(r_root) if (r_root / d / "A").is_dir())
    by_business: dict[str, list] = {}
    for rep in reps:
        rep_a = r_root / rep / "A"
        for bid in sorted(os.listdir(rep_a)):
            if (rep_a / bid).is_dir():
                by_business.setdefault(bid, []).append(
                    inject_defects.state_from_dump(str(rep_a / bid))
                )
    pairs = []
    for states in by_business.values():
        pairs.extend(itertools.combinations(states, 2))
    return pairs


def _upstream_stable(a, b) -> bool:
    """The calibration's condition: symmetric pattern-description match >= 0.95.

    A replay trial pins the upstream output from the dump, so only the retried
    stage moves. Repetition runs regenerate everything, so a strategy-stage
    figure taken over all pairs compounds reasoning churn — the confound D3c
    exists to remove.
    """
    ua = score_repair._items(a, "pattern_description")
    ub = score_repair._items(b, "pattern_description")
    fwd = score_repair.churn_mod.matched_fraction(ua, ub, score_repair.SAME_ITEM)
    rev = score_repair.churn_mod.matched_fraction(ub, ua, score_repair.SAME_ITEM)
    if fwd is None or rev is None:
        return False
    return (fwd + rev) / 2 >= 0.95


def _collateral_rate(pairs, kind) -> float:
    over = sum(
        1 for a, b in pairs
        if score_repair.churn_rate(
            score_repair._items(a, kind), score_repair._items(b, kind),
            exact=(kind == "pattern_aspect"),
        ) > score_repair.CHURN_FLOOR[kind]
    )
    return over / len(pairs) if pairs else 0.0


@needs_study
def test_the_naive_collateral_metric_pins_and_is_therefore_useless():
    """Documents why B6 redefines the metric, rather than asserting it.

    "Any item changed at all" is what the plan originally specified. If this
    ever stops pinning, the redefinition deserves revisiting.
    """
    pairs = _rep_pairs()
    assert pairs, "no regeneration pairs found"
    for kind in ("pattern_description", "root_cause", "recommendation_issue"):
        fires = sum(
            1 for a, b in pairs
            if score_repair._items(a, kind) != score_repair._items(b, kind)
        )
        assert fires / len(pairs) >= 0.90, f"{kind} naive rate {fires}/{len(pairs)}"


@needs_study
def test_set_overlap_collateral_does_not_pin():
    """The replacement metric must discriminate on unperturbed regenerations.

    Each kind is evaluated under the condition its floor was calibrated on:
    reasoning items over all pairs, strategy items only where upstream held
    still, because that is what a replay trial guarantees.
    """
    all_pairs = _rep_pairs()
    stable = [p for p in all_pairs if _upstream_stable(*p)]
    assert stable, "no upstream-stable pairs — the conditioning rule is wrong"

    for kind in ("pattern_aspect", "pattern_description", "root_cause"):
        rate = _collateral_rate(all_pairs, kind)
        assert rate < 0.50, f"{kind} flags collateral on {rate:.0%} of unperturbed reruns"

    rate = _collateral_rate(stable, "recommendation_issue")
    assert rate < 0.50, (
        f"recommendation_issue flags collateral on {rate:.0%} of upstream-stable reruns"
    )


@needs_study
def test_the_strategy_floor_must_be_applied_to_the_conditioned_population():
    """Pins the confound itself (D3c, and NEXT_SESSION do-not-redo item 17).

    Applying the conditioned 0.23 floor to unconditioned pairs overstates
    collateral badly. This is a live trap: the same mistake was made once
    already when the first collateral estimate was taken at 37%.
    """
    all_pairs = _rep_pairs()
    stable = [p for p in all_pairs if _upstream_stable(*p)]
    unconditioned = _collateral_rate(all_pairs, "recommendation_issue")
    conditioned = _collateral_rate(stable, "recommendation_issue")
    assert conditioned < unconditioned, (
        "conditioning on stable upstream should reduce apparent collateral; "
        f"got conditioned={conditioned:.2f} unconditioned={unconditioned:.2f}"
    )


@needs_study
def test_churn_uses_the_same_matcher_that_calibrated_the_floors():
    """Greedy one-to-one, not any-match.

    An any-match comparison lets one retried item cover several pre-injection
    items, understating churn and applying floors measured under another rule.
    """
    assert score_repair.churn_rate(["a", "a"], ["a"]) == pytest.approx(0.5)
    assert score_repair.churn_rate(["a", "a"], ["a", "a"]) == pytest.approx(0.0)


def test_churn_floors_are_the_measured_d3c_values():
    """Pins D3c. These are measurements, not choices — a change means a re-run."""
    assert score_repair.CHURN_FLOOR == {
        "pattern_aspect": 0.07,
        "pattern_description": 0.33,
        "root_cause": 0.29,
        "recommendation_issue": 0.23,
    }
    assert score_repair.SAME_ITEM == supervision.TRACE_SIMILARITY


def test_empty_item_sets_are_not_counted_as_total_churn():
    assert score_repair.churn_rate([], []) == 0.0


# ── denominators ──────────────────────────────────────────────────────────────


def test_tabulate_reports_per_operator_denominators():
    base = _base_state()
    _, descriptor = inject_defects.inject("O1", base, seed=0)
    outcomes = [
        score_repair.score(descriptor, base, _with_evidence(base, ["rA"])),
        score_repair.score(descriptor, base, _with_evidence(base, ["rB"])),
    ]
    table = score_repair.tabulate(outcomes)
    assert table["O1"]["n"] == 2
    assert table["O1"][REPAIRED] == 1
    assert table["O1"][REPLACED] == 1
    assert table["O1"]["repair_rate"] == 0.5
    assert table["O1"]["can_replace"] is True


def test_deleted_counts_against_the_primary_dichotomy():
    """D18's pre-registered rule: repair_rate is strictly `repaired` over n.

    Deleting the item the supervisor complained about is not a repair, or
    "drop the pattern you were asked about" scores as a supervisor success.
    """
    base = _base_state()
    _, descriptor = inject_defects.inject("O1", base, seed=0)
    outcomes = [
        score_repair.score(descriptor, base, _with_evidence(base, ["rA"])),
        score_repair.score(descriptor, base, _with_patterns(base, [])),
    ]
    table = score_repair.tabulate(outcomes)
    assert table["O1"][DELETED] == 1
    assert table["O1"][REPAIRED] == 1
    assert table["O1"]["repair_rate"] == 0.5, "deleted must not count as repaired"


# ── the uncalibrated stage ────────────────────────────────────────────────────


@needs_study
def test_report_stage_collateral_is_marked_unmeasurable_not_clean():
    """D3c calibrated reasoning and strategy items only — never report items.

    Defaulting report trials to collateral=False would report "no collateral
    damage" when the truth is "never checked", and two of the six repair
    operators (O6, O7) live at that stage. The churn is still recorded.
    """
    base = inject_defects.state_from_dump(inject_defects.base_dirs(str(STUDY_ROOT))[0])
    for op in ("O6", "O7", "O8"):
        injected, descriptor = inject_defects.inject(op, base, seed=0)
        if not descriptor.applied:
            continue
        outcome = score_repair.score(descriptor, base, injected)
        assert outcome.collateral_measurable is False
        assert outcome.churn, "report-stage churn must still be recorded"
        assert set(outcome.churn) == {"report_root_cause", "report_recommendation"}


@needs_study
def test_calibrated_stages_stay_measurable():
    base = inject_defects.state_from_dump(inject_defects.base_dirs(str(STUDY_ROOT))[0])
    for op in ("O1", "O5"):
        injected, descriptor = inject_defects.inject(op, base, seed=0)
        if descriptor.applied:
            assert score_repair.score(descriptor, base, injected).collateral_measurable is True


def test_collateral_rate_uses_its_own_denominator():
    """An unmeasurable trial counts toward n but not toward the collateral rate."""
    class _O:
        operator, collateral, collateral_measurable = "O6", False, False
        outcome = score_repair.UNREPAIRED
    table = score_repair.tabulate([_O(), _O()])
    assert table["O6"]["n"] == 2
    assert table["O6"]["n_collateral_measurable"] == 0
    assert table["O6"]["collateral_rate"] is None, "must be None, never 0.0"


# ── D22: O5's check is scored on content words ────────────────────────────────


def _strategy_base(extra_patterns=()):
    """A clean O5 base: every recommendation traces, lexically and on content."""
    return {
        "business_id": "b2", "business_name": "Test Bistro",
        "analysis_results": [],
        "reasoning_output": {
            "status": "success",
            "root_causes": [{"cause": "kitchen understaffed at peak hours",
                             "pattern": "slow service at dinner", "confidence": "high"}],
            "patterns": [
                {"description": "the restaurant's ambience is often described negatively",
                 "aspect": "ambience", "frequency": 0.3, "evidence_review_ids": []},
                {"description": "slow service at dinner",
                 "aspect": "wait_time", "frequency": 0.4, "evidence_review_ids": []},
                *extra_patterns,
            ],
        },
        "strategy_output": {
            "status": "success",
            "recommendations": [
                {"priority": 1, "issue": "slow service at dinner",
                 "action": "add a second line cook on weekend evenings",
                 "category": "operations", "expected_impact": "shorter waits"},
                {"priority": 2, "issue": "kitchen understaffed at peak hours",
                 "action": "hire part-time staff for the dinner rush",
                 "category": "operations", "expected_impact": "faster service"},
            ],
        },
        "report_output": None,
    }


def _with_issue_at(state, idx, issue):
    import copy
    out = copy.deepcopy(state)
    out["strategy_output"]["recommendations"][idx]["issue"] = issue
    return out


def _all_candidates(state):
    return [c for c in inject_defects._trace_candidates(state) if c]


def test_a_paraphrase_the_production_matcher_misses_does_not_score_unrepaired():
    """THE D22 case: a recommendation that restates an upstream pattern.

    The production check compares characters and calls it untraceable; before
    D22 that scored a correct regeneration `unrepaired` in every arm. (The real
    Tier-1 string "Negative ambience." sits at exactly 0.35 against this
    fixture's candidates, so the fixture uses a paraphrase with a clear margin.)
    """
    base = _strategy_base()
    _, descriptor = inject_defects.inject("O5", base, seed=0)
    assert descriptor.applied, descriptor.reason
    paraphrase = "Diners dislike the ambience"
    assert max(supervision._similar(paraphrase, c) for c in _all_candidates(base)) < 0.35

    retried = _with_issue_at(base, descriptor.target["recommendation_index"], paraphrase)
    outcome = score_repair.score(descriptor, base, retried)

    assert outcome.detail["check_fired_production"] is True, "precondition: production flags it"
    assert outcome.check_fired is False
    assert outcome.outcome != UNREPAIRED
    assert outcome.detail["trace_matcher"] == "content_jaccard>=0.1"


def test_alien_content_the_production_matcher_calls_traceable_scores_unrepaired():
    """The other direction (JOURNAL_PLAN 16.4): D13 item I28's exact string.

    'uniform size profile absent' shares no content word with "Unpleasant or
    undesirable atmosphere", yet scores 0.444 on characters. Left in the
    retried output it must not count as a repair.
    """
    base = _strategy_base(extra_patterns=[
        {"description": "Unpleasant or undesirable atmosphere", "aspect": "ambience",
         "frequency": 0.2, "evidence_review_ids": []},
    ])
    _, descriptor = inject_defects.inject("O5", base, seed=0)
    assert descriptor.applied, descriptor.reason
    alien = "uniform size profile absent"
    assert max(supervision._similar(alien, c) for c in _all_candidates(base)) >= 0.35

    retried = _with_issue_at(base, descriptor.target["recommendation_index"], alien)
    outcome = score_repair.score(descriptor, base, retried)

    assert outcome.detail["check_fired_production"] is False, "precondition: production misses it"
    assert outcome.check_fired is True
    assert outcome.outcome == UNREPAIRED
    assert outcome.detail["untraceable_content"] == [alien]


def test_leaving_the_injected_o5_issue_is_unrepaired_under_both_matchers():
    base = _strategy_base()
    injected, descriptor = inject_defects.inject("O5", base, seed=0)
    outcome = score_repair.score(descriptor, base, injected)
    assert outcome.check_fired is True
    assert outcome.detail["check_fired_production"] is True
    assert outcome.outcome == UNREPAIRED


def test_restoring_the_clean_o5_output_is_repaired():
    base = _strategy_base()
    _, descriptor = inject_defects.inject("O5", base, seed=0)
    outcome = score_repair.score(descriptor, base, base)
    assert outcome.check_fired is False
    assert outcome.outcome == REPAIRED


def test_only_the_trace_check_changes_matcher():
    """D22 corrects one measurement. Every other operator keeps the production check."""
    base = _base_state()
    injected, descriptor = inject_defects.inject("O1", base, seed=0)
    outcome = score_repair.score(descriptor, base, injected)
    assert outcome.detail["trace_matcher"] == "production"
    assert outcome.detail["untraceable_content"] is None
    assert outcome.check_fired == outcome.detail["check_fired_production"] is True


def test_the_content_threshold_is_the_pre_registered_one_and_has_one_home():
    """0.10 was fixed on calibration data before any trial; a change is an amendment."""
    assert score_repair.content_match.TRACE_JACCARD == 0.10
    assert score_repair.TRACE_CHECK_CLASS == inject_defects.CHECK_CLASS["O5"]
    source = (BACKEND / "scripts" / "analysis" / "matcher_shrinkage.py").read_text(encoding="utf-8")
    assert "def tokens(" not in source, "matcher_shrinkage must reuse content_match, not copy it"


# ── D24: O5's identity anchor is matched on content words ─────────────────────


def _o5_descriptor_at(base, idx):
    """The O5 injection whose target is recommendation ``idx``: first seed that hits it."""
    for seed in range(50):
        _, descriptor = inject_defects.inject("O5", base, seed=seed)
        if descriptor.applied and descriptor.target["recommendation_index"] == idx:
            return descriptor
    raise AssertionError(f"no seed in 0..49 targets recommendation {idx}")


def test_a_reworded_action_is_located_rather_than_scored_deleted():
    """THE D24 case: a regeneration that rewords the action has deleted nothing.

    The production matcher compares characters and failed to locate 70% of
    recommendations in an unperturbed re-draw, scoring them `deleted` -- which
    counts against repair, and happens more at P0 (A3) than at P1 (A1/A2),
    where the model can copy the artifact.
    """
    import copy
    base = _strategy_base()
    descriptor = _o5_descriptor_at(base, 0)
    want = base["strategy_output"]["recommendations"][0]["action"]
    retried = copy.deepcopy(base)
    retried["strategy_output"]["recommendations"][0]["action"] = "Weekend: extra hands, one more cook"
    for rec in retried["strategy_output"]["recommendations"]:
        assert supervision._similar(want, rec["action"]) < 0.35, "precondition: production cannot locate it"

    outcome = score_repair.score(descriptor, base, retried)

    assert outcome.detail["item_located"] is True
    assert outcome.outcome == REPAIRED
    assert outcome.detail["anchor_matcher"] == "content_jaccard>=0.2"


def test_dropping_the_recommendation_is_still_deleted():
    """The anchor got more tolerant of rewording, not blind to deletion."""
    import copy
    base = _strategy_base()
    descriptor = _o5_descriptor_at(base, 0)
    retried = copy.deepcopy(base)
    del retried["strategy_output"]["recommendations"][0]

    outcome = score_repair.score(descriptor, base, retried)

    assert outcome.detail["item_located"] is False
    assert outcome.outcome == DELETED


def test_only_o5_anchors_on_content_words_and_at_the_calibrated_threshold():
    """Pattern descriptions (O1-O4) are located 97% of the time on characters and
    stay there; restoration is not part of D24 at all."""
    assert score_repair.CONTENT_ANCHORED == frozenset({"O5"})
    assert score_repair.content_match.ANCHOR_JACCARD == 0.20
    base = _base_state()
    injected, descriptor = inject_defects.inject("O1", base, seed=0)
    assert score_repair.score(descriptor, base, injected).detail["anchor_matcher"] == "production"
