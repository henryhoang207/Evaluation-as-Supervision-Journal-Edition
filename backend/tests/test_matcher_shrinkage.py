"""Pins the PHASE0_MEMO Q1 measurement (JOURNAL_PLAN section 17).

These numbers decided D22: the production supervisor stays as shipped for the
repair study, and the O5 scorer does not. Each test pins one premise of that
decision. If one fails, the premise moved, and the decision must be re-read
before anything is re-pinned.
"""

import importlib.util
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


ms = _load_module("matcher_shrinkage", "scripts/analysis/matcher_shrinkage.py")

needs_study = pytest.mark.skipif(
    not (STUDY_ROOT / "A").is_dir(), reason="backend/out_study/ not present"
)


@pytest.fixture(scope="module")
def summary():
    return ms.measure(str(STUDY_ROOT))


@needs_study
def test_the_measurement_reproduces_every_recorded_production_flag(summary):
    """Without this the rest measures a different matcher from the one that ran."""
    assert summary["tier1"]["sanity_mismatches"] == []


@needs_study
def test_tier1_shrinks_to_the_reasoning_defects_plus_one(summary):
    """13 -> 6 under the D22 matcher. The 5 reasoning defects never use it."""
    t = summary["tier1"]
    assert t["usable"] == 13 and t["reasoning"] == 5
    assert t["by_matcher"][ms.SHIPPED] == 13
    assert t["by_matcher"][ms.PRIMARY] == 6
    # the shrinkage does not hinge on the threshold: laxer matchers give 5
    assert t["by_matcher"]["contain>0"] == 5
    assert t["by_matcher"]["jaccard>=0.05"] == 5


@needs_study
def test_every_issue_the_shipped_check_flagged_shares_content_with_upstream(summary):
    """The premise that the production flags are false alarms, not real misses."""
    flagged = summary["tier1"]["flagged_issues"]
    assert len(flagged) == 13
    assert all(f["containment"] > 0 for f in flagged)
    assert all(f["lexical"] < 0.35 for f in flagged)


@needs_study
def test_the_primary_matcher_raises_no_flag_the_shipped_one_did_not(summary):
    """A fix that trades one false-alarm direction for the other is no fix."""
    v = summary["population"]["versus_shipped"][ms.PRIMARY]
    assert v["fix_only"] == 0 and v["issues_fix_only"] == 0
    assert summary["population"]["flagged_stages"][ms.SHIPPED] == 8
    assert summary["population"]["stages"] == 49


@needs_study
def test_strict_content_thresholds_are_worse_in_the_other_direction(summary):
    """Why the primary is not a strict containment threshold (JOURNAL_PLAN 17.2)."""
    assert summary["population"]["versus_shipped"]["contain>=0.34"]["fix_only"] > 0
    assert summary["population"]["versus_shipped"]["contain>=0.50"]["fix_only"] > 0


@needs_study
def test_the_shipped_check_calls_alien_content_traceable_and_the_primary_does_not(summary):
    a = summary["alien"]
    assert a["issue_base_pairs"] == 168
    assert a["traced"][ms.SHIPPED] == 6
    assert a["traced"][ms.PRIMARY] == 0
    # JOURNAL_PLAN 16.4's "16 pairs" counted issue x candidate: same measurement
    assert a["shipped_issue_candidate_pairs"] == 16


@needs_study
def test_the_o5_manipulation_is_identical_under_either_matcher(summary):
    """THE premise of D22. If the bug reached the bases or the injected issue,
    keeping the production supervisor as shipped would contaminate the arms."""
    x = summary["manipulation"]
    assert x["bases"] == 20
    assert x["bases_flagged"][ms.SHIPPED] == 0
    assert x["bases_flagged"][ms.PRIMARY] == 0
    for seed, v in x["injected"].items():
        assert v["n"] == 20, seed
        for matcher, traced in v["traced"].items():
            assert traced == 0, f"seed {seed}: {matcher} traces an injected alien issue"
