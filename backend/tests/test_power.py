"""Tests for the power analysis (JOURNAL_PLAN D4d).

`power.py` produces the figures the pre-registration cites -- the MDE that
D11b's split threshold must clear, and the power that decides how many Phase-A
dumps to collect. It had no tests until 2026-08-25, which is backwards: a
number nobody can regression-test is a number carried by hand with extra steps.

The one that matters most is the first. `cluster_bootstrap` was rewritten to
chunk over simulations, because the one-liner it replaced allocated 24 GB at
sims=20000 and that is what stopped the cited table being computed at a useful
precision. Simulations are independent, so the split must be exact -- not
approximately exact.
"""

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pytest

BACKEND = Path(__file__).resolve().parent.parent


def _load_module(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, BACKEND / relative)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


power = _load_module("power", "scripts/analysis/power.py")


def _reference_bootstrap(idx, a, b):
    """The unchunked computation, written out per simulation.

    Deliberately naive and deliberately not the implementation: a chunking bug
    that reused a stale slice would still agree with a cleverer reference.
    """
    diff = a.mean(axis=2) - b.mean(axis=2)
    out = []
    for sim in range(a.shape[0]):
        boot = diff[sim][idx].mean(axis=1)
        lo, hi = np.percentile(boot, [2.5, 97.5])
        out.append(bool(lo > 0 or hi < 0))
    return np.array(out)


@pytest.mark.parametrize("n_sims, n_defects", [(1, 8), (7, 8), (64, 12), (200, 102)])
def test_the_chunked_bootstrap_is_exactly_the_unchunked_one(n_sims, n_defects):
    """Chunk boundaries must not change a single decision, at any size."""
    rng = np.random.default_rng(7)
    a, b = power.simulate(rng, n_sims, n_defects, 3, power.P_A1, power.P_A2, 1.0)

    # The implementation draws its resample index first, so replay that draw to
    # feed the reference the identical bootstrap.
    probe = np.random.default_rng(11)
    idx = probe.integers(0, n_defects, size=(1000, n_defects))

    got = power.cluster_bootstrap(np.random.default_rng(11), a, b)
    assert got.shape == (n_sims,)
    assert got.dtype == bool
    np.testing.assert_array_equal(got, _reference_bootstrap(idx, a, b))


@pytest.mark.parametrize("chunk", [1, 2, 7, 53, 500])
def test_every_chunk_size_gives_the_same_answer(chunk):
    """Including sizes that divide unevenly and leave a ragged final block."""
    a, b = power.simulate(np.random.default_rng(3), 53, 16, 2,
                          power.P_A1, power.P_A2, 1.0)
    idx = np.random.default_rng(5).integers(0, 16, size=(1000, 16))
    expected = _reference_bootstrap(idx, a, b)

    got = power.cluster_bootstrap(np.random.default_rng(5), a, b, chunk=chunk)
    np.testing.assert_array_equal(got, expected)


# ── properties the cited table depends on ─────────────────────────────────────


def test_more_defects_detect_a_smaller_effect():
    """If the MDE did not fall with N, the +8-dump recommendation is nonsense."""
    rng = np.random.default_rng(42)
    small = power.mde(rng, 400, 40, 3, 1.0)
    large = power.mde(np.random.default_rng(42), 400, 143, 3, 1.0)
    assert large < small


def test_the_occasion_effect_costs_power_rather_than_adding_it():
    """Section 14.1 forces arms into one session, which makes them MORE alike.

    Every figure computed without it is optimistic; if this ever inverted, the
    'w/ occasion' column would be reassuring for the wrong reason.
    """
    plain = power.run_cell(np.random.default_rng(1), 1500, 102, 3,
                           power.P_A1, power.P_A2, 1.0)
    shared = power.run_cell(np.random.default_rng(1), 1500, 102, 3,
                            power.P_A1, power.P_A2, 1.0, sigma_occasion=1.5)
    assert shared["cluster"] < plain["cluster"]


def test_a_cell_is_reproducible_from_its_seed():
    """The plan cites these by value, so the same seed must give the same number."""
    first = power.run_cell(np.random.default_rng(99), 800, 102, 3,
                           power.P_A1, power.P_A2, 1.0)
    second = power.run_cell(np.random.default_rng(99), 800, 102, 3,
                            power.P_A1, power.P_A2, 1.0)
    assert first == second


def test_no_effect_means_no_systematic_rejection():
    """A sanity floor: with both arms at the same rate, rejection sits near alpha."""
    res = power.run_cell(np.random.default_rng(5), 2000, 102, 3,
                         power.P_A1, power.P_A1, 1.0)
    assert res["cluster"] < 0.12, "the cluster estimator should not over-reject badly here"


# ── the shared bootstrap helper ───────────────────────────────────────────────


def test_bootstrap_means_matches_a_direct_computation():
    """Shape is (n_boot, n_sims), and the values are the plain resampled means."""
    rng = np.random.default_rng(21)
    diff = rng.normal(size=(37, 14))
    idx = rng.integers(0, 14, size=(50, 14))

    got = power.bootstrap_means(diff, idx)

    assert got.shape == (50, 37)
    expected = np.array([[diff[sim][row].mean() for sim in range(37)] for row in idx])
    np.testing.assert_allclose(got, expected)


@pytest.mark.parametrize("chunk", [1, 3, 37, 1000])
def test_bootstrap_means_is_chunk_invariant(chunk):
    rng = np.random.default_rng(22)
    diff = rng.normal(size=(37, 14))
    idx = rng.integers(0, 14, size=(50, 14))
    np.testing.assert_allclose(power.bootstrap_means(diff, idx, chunk=chunk),
                               power.bootstrap_means(diff, idx, chunk=1000))


def test_only_one_bootstrap_expression_exists_in_the_source():
    """The guard for the bug that actually happened.

    `cluster_bootstrap` and the section-7 difference-in-differences each used to
    carry their own `diff[:, idx].mean(axis=2)`. Chunking one for memory left
    the other allocating 38 GB, and the first --sims 20000 run died there --
    five sections after the part that had been "fixed". A second copy must fail
    here rather than at hour one of a long run.
    """
    import io
    import re
    import tokenize

    path = BACKEND / "scripts" / "analysis" / "power.py"
    source = path.read_text(encoding="utf-8")

    # Strings and comments are dropped first: the helper's own docstring quotes
    # the very expression being banned, and a guard that trips on the sentence
    # explaining it would be worse than no guard.
    code = []
    with io.open(path, encoding="utf-8") as fh:
        for tok in tokenize.generate_tokens(fh.readline):
            if tok.type not in (tokenize.STRING, tokenize.COMMENT):
                code.append(tok.string)
    code = " ".join(code)

    hits = re.findall(r"\[ *: *, *i\w* *\] *\. *mean \( *axis *= *2 *\)", code)
    assert len(hits) == 1, (
        f"found {len(hits)} un-shared bootstrap expressions in code; route them "
        f"all through bootstrap_means()"
    )
    assert "diff[:, idx].mean(axis=2)" in source, (
        "the helper docstring should still explain what it replaced"
    )
