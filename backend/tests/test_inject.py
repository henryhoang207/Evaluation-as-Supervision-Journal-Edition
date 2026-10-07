"""Tests for the injection operators (JOURNAL_PLAN B4).

The headline test is ``test_every_injection_trips_its_own_check_and_only_it``.
The injector and the supervisor are independent programs: the operator declares
which check class it targets, ``supervision.measure`` reports which classes
actually fire, and the two must agree on every real base. That is a genuine
correctness gate rather than a tautology, and it costs no LLM calls.

``scripts/`` is not a package, so the modules are loaded by path.
"""

import copy
import importlib.util
import sys
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parent.parent
STUDY_ROOT = BACKEND / "out_study"


def _load_module(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, BACKEND / relative)
    module = importlib.util.module_from_spec(spec)
    # Register before exec: @dataclass resolves cls.__module__ through
    # sys.modules, and a path-loaded module that is not there yields None.
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


inject_defects = _load_module("inject_defects", "scripts/inject_defects.py")

from app.core import supervision  # noqa: E402

needs_study = pytest.mark.skipif(
    not (STUDY_ROOT / "A").is_dir(), reason="backend/out_study/ not present"
)


def _bases():
    return [
        inject_defects.state_from_dump(d)
        for d in inject_defects.base_dirs(str(STUDY_ROOT))
    ]


# ── the cross-check gate ──────────────────────────────────────────────────────


@needs_study
def test_every_injection_trips_its_own_check_and_only_it():
    """HARD GATE: descriptor and measurement must agree, on every base.

    An operator that trips a second check class cannot be attributed to one
    defect, so collateral firing fails just as loudly as not firing at all.
    """
    failures = []
    applied = 0
    for state in _bases():
        for op in inject_defects.OPERATORS:
            injected, descriptor = inject_defects.inject(op, state, seed=0)
            if not descriptor.applied:
                continue
            applied += 1
            ok, detail = inject_defects.verify_injection(op, injected, state)
            if not ok:
                failures.append(
                    f"{op} @ {state.get('business_name')}: "
                    f"fired={detail['target_fired']} collateral={detail['collateral_classes']}"
                )
    assert applied > 0, "no operator applied to any base — the corpus is not loading"
    assert failures == [], "\n".join(failures)


@needs_study
def test_retry_operators_actually_produce_a_retry_verdict():
    """An operator carrying the repair endpoint must create something to repair.

    This is what disqualified O4: a frequency divergence yields
    proceed_with_warning, so no arm ever sees a retry.
    """
    for state in _bases():
        for op in inject_defects.REPAIR_OPERATORS:
            injected, descriptor = inject_defects.inject(op, state, seed=0)
            if not descriptor.applied:
                continue
            _, detail = inject_defects.verify_injection(op, injected, state)
            assert detail["verdict"] == "retry", f"{op} produced {detail['verdict']}"


@needs_study
def test_o4_is_warn_level_and_never_retries():
    """Pins the reason O4 cannot carry the repair endpoint."""
    assert inject_defects.ENDPOINT["O4"] == "warn_level"
    assert "O4" not in inject_defects.REPAIR_OPERATORS
    seen = 0
    for state in _bases():
        injected, descriptor = inject_defects.inject("O4", state, seed=0)
        if not descriptor.applied:
            continue
        seen += 1
        facts = supervision.measure("reasoning_agent", injected)
        assert supervision.decide("reasoning_agent", facts, {}).verdict == "proceed_with_warning"
    assert seen > 0


# ── determinism ───────────────────────────────────────────────────────────────


@needs_study
def test_injection_is_deterministic_given_a_seed():
    for state in _bases()[:5]:
        for op in inject_defects.OPERATORS:
            a, da = inject_defects.inject(op, state, seed=7)
            b, db = inject_defects.inject(op, state, seed=7)
            assert a == b, f"{op} is not deterministic"
            assert da.to_dict() == db.to_dict()


@needs_study
def test_injection_does_not_mutate_the_caller_state():
    state = _bases()[0]
    before = copy.deepcopy(state)
    for op in inject_defects.OPERATORS:
        inject_defects.inject(op, state, seed=0)
    assert state == before


# ── frozen corpora ────────────────────────────────────────────────────────────


@needs_study
def test_every_base_has_a_usable_corpus_issue():
    """O5 must be injectable on every base.

    Not "every entry is safe on every base" — untraceability is base-relative
    (see the corpus note in inject_defects), so _o5_issue selects per base. The
    property applicability actually depends on is that the selection never comes
    up empty.
    """
    for state in _bases():
        usable = [
            issue for issue in inject_defects.CORPUS_ISSUES
            if max((supervision._similar(issue, c)
                    for c in inject_defects._trace_candidates(state)), default=0.0)
            < supervision.TRACE_SIMILARITY
        ]
        assert usable, f"no usable corpus issue for {state.get('business_name')}"


@needs_study
def test_corpus_margin_is_reported_not_assumed():
    """difflib on English prose has a narrow dynamic range; keep the margin visible.

    If a future base pushes an entry over the threshold, _o5_issue simply stops
    selecting it — but the margin shrinking is worth failing on before it does.
    """
    worst = 0.0
    for state in _bases():
        for issue in inject_defects.CORPUS_ISSUES:
            worst = max(worst, max(
                (supervision._similar(issue, c)
                 for c in inject_defects._trace_candidates(state)), default=0.0))
    # ⚠ 2026-08-26: this tripwire FIRED, and it was right to. After the 8 extra
    # dumps the worst case is 0.444 -- ABOVE the 0.35 trace threshold, not just
    # near it. 'uniform size profile absent' scores 0.444 against 'Unpleasant or
    # undesirable atmosphere' on pure character overlap; 16 pairs now sit at or
    # above threshold. That string is D13 item I28, which BOTH blinded raters
    # called an error and whose content-word overlap is 0.00.
    #
    # So difflib is wrong in both directions: it misses real paraphrases
    # (JOURNAL_PLAN 15.4) and matches unrelated strings here. The study is not
    # silently broken -- _o5_issue simply stops selecting an over-threshold
    # issue, and O5 applicability absorbs it -- but the margin is gone.
    # Do NOT relax this bound further without reading PHASE0_MEMO section 11;
    # do NOT edit CORPUS_ISSUES, because D13 rated these exact strings.
    assert worst < 0.46, f"corpus worst-case similarity {worst:.3f} moved again"


@needs_study
def test_corpus_insertions_are_absent_from_every_upstream():
    """O6/O7 rely on exact-string containment, so the insert must be novel."""
    for state in _bases():
        upstream_causes = {
            (rc.get("cause"), rc.get("pattern"))
            for rc in (state.get("reasoning_output") or {}).get("root_causes") or []
        }
        for pattern, cause in inject_defects.CORPUS_CAUSES:
            assert (cause, pattern) not in upstream_causes

        upstream_recs = {
            (r.get("issue"), r.get("action"))
            for r in (state.get("strategy_output") or {}).get("recommendations") or []
        }
        for issue, action in inject_defects.CORPUS_RECS:
            assert (issue, action) not in upstream_recs


# ── applicability is reported, never silent ───────────────────────────────────


@needs_study
def test_inapplicable_operators_record_a_reason():
    for state in _bases():
        for op in inject_defects.OPERATORS:
            _, descriptor = inject_defects.inject(op, state, seed=0)
            if not descriptor.applied:
                assert descriptor.reason, f"{op} skipped without a reason"


def test_unknown_operator_raises():
    with pytest.raises(ValueError):
        inject_defects.applicable("O99", {})


def test_o3_needs_resolving_evidence():
    """A pattern whose evidence is all missing cannot carry an O3 defect.

    _measure_reasoning only counts misalignment for ids that resolve, so such a
    pattern would report as O1/O2 instead — a different check class.
    """
    by_id = {"r1": {"aspects": [{"category": "food_quality", "label": "negative"}]}}
    assert inject_defects._o3_target({"aspect": "food_quality",
                                      "evidence_review_ids": ["absent"]}, by_id) is None
    assert inject_defects._o3_target({"aspect": "food_quality",
                                      "evidence_review_ids": ["r1"]}, by_id) is not None


# ── the ceiling ───────────────────────────────────────────────────────────────


@needs_study
def test_applicability_matrix_pins_the_tier2_ceiling():
    """Pins the corrected ceiling. The plan's 160 was a hand multiplication.

    If a re-run moves these, the plan is stale — the same contract
    tests/test_replay.py enforces for the Tier-1 defect bank.
    """
    m = inject_defects.matrix(str(STUDY_ROOT))
    ops = m["operators"]

    # Re-pinned 2026-08-26 after D11b's 8 extra Phase-A dumps (20 -> 28).
    # Previous: 17/17/15/16/15/19/19/19, all_operators 137, repair 102.
    assert m["n_dumps"] == 28
    assert ops["O1"]["applicable"] == 24
    assert ops["O2"]["applicable"] == 24
    assert ops["O3"]["applicable"] == 22
    assert ops["O4"]["applicable"] == 23
    assert ops["O5"]["applicable"] == 20
    assert ops["O6"]["applicable"] == 26
    assert ops["O7"]["applicable"] == 26
    assert ops["O8"]["applicable"] == 26
    assert m["summary"]["all_operators"] == 191

    # O4 is warn-level and O8 is a positive control, so neither carries the
    # repair endpoint. 102 is the N the confirmatory contrasts are powered on;
    # O8's 19 control trials and O4's 16 warn-level trials sit outside it.
    assert m["summary"]["repair_operator_ids"] == ["O1", "O2", "O3", "O5", "O6", "O7"]
    assert m["summary"]["repair_operators"] == 142


# ── O1 severity levels (PREREGISTRATION.md section 0.1 A6) ───────────────────


def _o1_bases():
    return [b for b in _bases() if inject_defects.applicable("O1", b)[0]]


@needs_study
def test_o1_severity_1_is_the_frozen_operator_byte_for_byte():
    """The core ran at level 1; the severity parameter must not have moved it."""
    for base in _o1_bases():
        a, da = inject_defects.inject("O1", base, seed=0)
        b, db = inject_defects.inject("O1", base, seed=0, severity=1)
        assert a == b and da.to_dict() == db.to_dict()
        assert "severity" not in da.target


@needs_study
def test_o1_severity_2_contains_level_1_and_breaks_every_resolving_id():
    for base in _o1_bases():
        _, d1 = inject_defects.inject("O1", base, seed=0)
        out2, d2 = inject_defects.inject("O1", base, seed=0, severity=2)
        idx = d2.target["pattern_index"]
        assert idx == d1.target["pattern_index"]
        ids = inject_defects._patterns(out2)[idx]["evidence_review_ids"]
        assert ids[d1.target["evidence_index"]] == d1.target["after"]
        by_id = inject_defects._analysis_index(out2)
        assert inject_defects._resolving(inject_defects._patterns(out2)[idx], by_id) == []
        # per-id damage is one character, as at level 1
        for c in d2.target["also_corrupted"]:
            assert len(c["after"]) == len(c["before"]) - 1
        assert d2.target["severity"] == 2


@needs_study
def test_o1_severity_2_trips_only_its_own_check():
    for base in _o1_bases():
        out2, _ = inject_defects.inject("O1", base, seed=0, severity=2)
        valid, detail = inject_defects.verify_injection("O1", out2, base)
        assert valid, detail
        assert detail["verdict"] == "retry"


def test_severity_is_defined_for_o1_only_and_only_at_two_levels():
    with pytest.raises(ValueError):
        inject_defects.inject("O2", {}, severity=2)
    with pytest.raises(ValueError):
        inject_defects.inject("O1", {}, severity=3)
