"""Pins the finding behind PREREGISTRATION section 11 item 6 (JOURNAL_PLAN 17.6).

A3 re-draws at P0, where the injected output never enters the context, so it
cannot be a near-zero floor for *injected* defects. These tests pin the part of
that claim that does not depend on the repetition-run approximation, and the
size of the gap from what ``power.py`` assumes.
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


a3 = _load_module("a3_redraw", "scripts/analysis/a3_redraw.py")

needs_study = pytest.mark.skipif(
    not (STUDY_ROOT / "R").is_dir() or not (STUDY_ROOT / "A").is_dir(),
    reason="backend/out_study/A and R not present",
)


@pytest.fixture(scope="module")
def estimate():
    return a3.estimate(str(STUDY_ROOT))


def test_a3_is_defined_only_at_the_placement_that_hides_the_defect():
    """The mechanism, pinned at its source: A3 exists only at P0, and P0 omits the artifact."""
    arms = a3.score_repair.inject_defects  # noqa: F841 - keeps the loader order of the suite
    arms_mod = _load_module("arms", "scripts/arms.py")
    for placement in ("P1", "P2", "P3"):
        assert not arms_mod.is_defined("A3", placement)
    assert arms_mod.is_defined("A3", "P0")


@needs_study
def test_the_plan_mix_is_the_pre_registered_n(estimate):
    assert estimate["plan_N"] == 142


@needs_study
def test_a_redraw_repairs_every_insertion_defect_by_construction(estimate):
    """An invented corpus item cannot recur in a draw that never saw it."""
    for op in a3.BY_CONSTRUCTION:
        r = estimate["per_operator"][op]
        assert r["n"] > 0, op
        assert r["repair_rate"] == 1.0, f"{op}: {r}"


@needs_study
def test_pooled_a3_is_nowhere_near_the_power_assumption(estimate):
    """The floor alone is ~7x what power.py assumes, before any approximation."""
    assert estimate["by_construction_floor"] >= 0.36
    assert estimate["pooled_repair_rate"] >= estimate["by_construction_floor"]
    assert estimate["pooled_repair_rate"] > 5 * estimate["power_py_assumes"]
