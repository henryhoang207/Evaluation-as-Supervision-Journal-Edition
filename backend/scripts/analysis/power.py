"""Power analysis for the injected-defect repair study (JOURNAL_PLAN D4d).

Simulation-based, because the design is not a textbook one: outcomes are matched
across arms within a defect, repetitions are nested inside each (defect, arm),
and in Tier 1 the defects themselves cluster into a handful of
business x stage cells. Closed-form McNemar power formulas assume independent
pairs and would overstate every number here.

Effect sizes are taken from the plan, not invented:

    p(A1) = 0.45   Arimbur section V.E, assertion-error class (section 14.2) -
                   the hardest measured class and the direct analogue of a
                   schema-valid but ungrounded claim
    p(A3) = 0.05   near floor; Self-Debug Table 3b, Huang intrinsic rows
    p(A2) = 0.33   Self-Debug: A2 captures ~70% of A1's *gain* over A3
                   (section 13.3), i.e. 0.05 + 0.70 * (0.45 - 0.05)
    p(A0) = 0.65   capability ceiling; least constrained by literature, so it
                   is swept rather than assumed

So the headline contrast A1 vs A2 is a **12 pp** difference, and A2 vs A3 is
28 pp. The question this script answers is whether the planned grid can detect
12 pp.

Two estimators are compared:

    naive   exact McNemar over every (defect, repetition) pair - what D4
            currently specifies
    cluster defect-level paired differences with a bootstrap over defects -
            what D4b requires

The gap between their type-I error rates is the reason D4b exists.

Run (from backend/, venv active - no API calls, no dataset):

    python scripts/analysis/power.py
    python scripts/analysis/power.py --sims 5000
"""

from __future__ import annotations

import argparse
import sys

import numpy as np
from scipy import stats

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


ALPHA = 0.05

# Plan-derived rates (see module docstring).
P_A0, P_A1, P_A2, P_A3 = 0.65, 0.45, 0.33, 0.05

# Defect-level heterogeneity on the logit scale. Unknown, so everything is
# reported across a sweep; 1.0 is the working assumption (defects differ
# substantially in how repairable they are, which the 4x spread in per-class
# repair rates in Arimbur section V.E supports).
SIGMA_DEFAULT = 1.0

# Tier-1 reality: 11 usable defects in 5 business x stage cells, sizes below.
# Produced by scripts/analysis/defect_bank.py.
TIER1_CELLS = [4, 3, 2, 1, 1]


def _logit(p):
    return np.log(p / (1 - p))


def _expit(x):
    return 1.0 / (1.0 + np.exp(-x))


def simulate(rng, n_sims, n_defects, reps, p_a, p_b, sigma, cluster_sizes=None,
             sigma_occasion=0.0):
    """Outcomes for two arms under a shared per-defect random effect.

    Returns two boolean arrays of shape (n_sims, n_defects, reps). The shared
    effect is what makes the arms matched; when cluster_sizes is given, defects
    inside a cluster additionally share a cluster effect, which is what makes
    near-duplicate Tier-1 defects non-exchangeable.
    """
    if cluster_sizes is None:
        u = rng.normal(0.0, sigma, size=(n_sims, n_defects, 1))
    else:
        # Most of the variance sits at the cluster level: repeated observations
        # of the same business x stage cell are near-duplicates, not new draws.
        n_clusters = len(cluster_sizes)
        v = rng.normal(0.0, sigma * 0.9, size=(n_sims, n_clusters, 1))
        v = np.repeat(v, np.array(cluster_sizes), axis=1)
        w = rng.normal(0.0, sigma * 0.44, size=(n_sims, n_defects, 1))
        u = v + w

    # Occasion effect: all arms for one defect run contiguously in one session
    # (section 14.1), so they share whatever the serving stack was doing at that
    # moment. That makes the arms MORE alike than conditional independence
    # implies, which reduces discordant pairs and therefore reduces McNemar
    # power. Ignoring it makes every power figure optimistic.
    w = 0.0
    if sigma_occasion:
        w = rng.normal(0.0, sigma_occasion, size=(n_sims, n_defects, reps))

    a = rng.random((n_sims, n_defects, reps)) < _expit(_logit(p_a) + u + w)
    b = rng.random((n_sims, n_defects, reps)) < _expit(_logit(p_b) + u + w)
    return a, b


def mcnemar_naive(a, b):
    """Exact McNemar p-value per simulation, over every (defect, rep) pair."""
    n_sims = a.shape[0]
    flat_a = a.reshape(n_sims, -1)
    flat_b = b.reshape(n_sims, -1)
    b_count = np.sum(flat_a & ~flat_b, axis=1)
    c_count = np.sum(~flat_a & flat_b, axis=1)
    n_disc = b_count + c_count
    k = np.minimum(b_count, c_count)

    p = np.ones(n_sims)
    nz = n_disc > 0
    p[nz] = np.minimum(1.0, 2.0 * stats.binom.cdf(k[nz], n_disc[nz], 0.5))
    return p, n_disc


def bootstrap_means(diff, idx, chunk=None):
    """Bootstrap means over defects, as (n_boot, n_sims). Chunked over sims.

    The obvious one-liner -- ``diff[:, idx].mean(axis=2)`` -- materialises
    (n_sims, n_boot, n_defects) floats: 24 GB at n_sims=20000, which is what
    stopped the cited table being computed at a precision worth quoting.
    Simulations are independent, so chunking over them is exact rather than
    approximate.

    Shared by cluster_bootstrap and by the section-7 difference-in-differences.
    They used to carry separate copies of the same expression, so fixing the
    memory blow-up in one left it live in the other -- which is exactly how the
    first --sims 20000 run died, five sections after the part that was fixed.
    """
    n_sims, n_defects = diff.shape
    n_boot = idx.shape[0]
    if chunk is None:
        chunk = max(1, 20_000_000 // max(1, n_boot * n_defects))

    out = np.empty((n_boot, n_sims))
    for start in range(0, n_sims, chunk):
        block = diff[start:start + chunk]                  # (chunk, n_defects)
        out[:, start:start + chunk] = block[:, idx].mean(axis=2).T
    return out


def cluster_bootstrap(rng, a, b, n_boot=1000, chunk=None):
    """Reject H0 when a bootstrap CI over defect-level differences excludes 0.

    Resampling whole defects (not pairs) is what keeps repeated observations of
    the same defect from being counted as independent evidence.
    """
    n_sims, n_defects, _ = a.shape
    diff = a.mean(axis=2) - b.mean(axis=2)          # (n_sims, n_defects)

    idx = rng.integers(0, n_defects, size=(n_boot, n_defects))

    boot = bootstrap_means(diff, idx, chunk)               # (n_boot, n_sims)
    lo, hi = np.percentile(boot, [2.5, 97.5], axis=0)
    return (lo > 0) | (hi < 0)


def run_cell(rng, n_sims, n_defects, reps, p_a, p_b, sigma, cluster_sizes=None,
             sigma_occasion=0.0):
    a, b = simulate(rng, n_sims, n_defects, reps, p_a, p_b, sigma, cluster_sizes,
                    sigma_occasion)
    p_naive, n_disc = mcnemar_naive(a, b)
    rej_naive = p_naive < ALPHA
    rej_cluster = cluster_bootstrap(rng, a, b)
    return {
        "naive": rej_naive.mean(),
        "cluster": rej_cluster.mean(),
        "median_discordant": float(np.median(n_disc)),
    }


def mde(rng, n_sims, n_defects, reps, sigma, target=0.80, cluster_sizes=None,
        sigma_occasion=0.0):
    """Smallest p(A1) - p(A2) the cluster estimator detects at `target` power."""
    lo, hi = 0.0, 0.44
    for _ in range(12):
        mid = (lo + hi) / 2
        res = run_cell(rng, n_sims, n_defects, reps, P_A1, P_A1 - mid, sigma,
                       cluster_sizes, sigma_occasion)
        if res["cluster"] >= target:
            hi = mid
        else:
            lo = mid
    return hi


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sims", type=int, default=2000)
    ap.add_argument("--defects", default="102,143",
                    help="Comma-separated defect counts for section 9. Default is the "
                         "computed Tier-2 ceiling and the +8-dump projection.")
    ap.add_argument("--sigma", type=float, default=SIGMA_DEFAULT)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    rng = np.random.default_rng(args.seed)
    s, sig = args.sims, args.sigma

    print(f"Simulation-based power. sims={s}, defect SD (logit)={sig}, alpha={ALPHA}")
    print(f"Rates: A0={P_A0} A1={P_A1} A2={P_A2} A3={P_A3}  "
          f"-> A1-A2 = {100*(P_A1-P_A2):.0f}pp, A2-A3 = {100*(P_A2-P_A3):.0f}pp")

    print("\n" + "=" * 74)
    print("1. TYPE-I ERROR under H0 (both arms at p=0.45) - is naive McNemar valid?")
    print("=" * 74)
    print(f"{'design':<34} {'naive':>10} {'cluster':>10}")
    for label, nd, r, cl in [
        ("Tier 2: 8 ops x 5 biz, r=2", 40, 2, None),
        ("Tier 2: 8 ops x 10 biz, r=2", 80, 2, None),
        ("Tier 2: 8 ops x 20 biz, r=2", 160, 2, None),
        ("Tier 1: 11 defects / 5 cells, r=3", 11, 3, TIER1_CELLS),
    ]:
        res = run_cell(rng, s, nd, r, P_A1, P_A1, sig, cl)
        print(f"{label:<34} {res['naive']:>10.3f} {res['cluster']:>10.3f}")
    print("nominal is 0.050; naive inflation is the cost of treating repetitions")
    print("of one defect as independent pairs.")

    print("\n" + "=" * 74)
    print("2. POWER for A1 vs A2 (12pp) - the primary endpoint")
    print("=" * 74)
    print(f"{'design':<34} {'quadruples':>11} {'naive':>9} {'cluster':>9}")
    for label, nd, r, cl in [
        ("CURRENT ablation: 8 x 5, r=2", 40, 2, None),
        ("proposed: 8 x 10, r=2", 80, 2, None),
        ("8 x 15, r=2", 120, 2, None),
        ("8 x 20, r=2", 160, 2, None),
        ("8 x 10, r=3", 80, 3, None),
        ("8 x 20, r=3", 160, 3, None),
    ]:
        res = run_cell(rng, s, nd, r, P_A1, P_A2, sig, cl)
        print(f"{label:<34} {nd:>11} {res['naive']:>9.3f} {res['cluster']:>9.3f}")

    print("\n" + "=" * 74)
    print("3. POWER for A2 vs A3 (28pp) - the easier contrast")
    print("=" * 74)
    print(f"{'design':<34} {'naive':>10} {'cluster':>10}")
    for label, nd, r in [
        ("8 x 5, r=2", 40, 2),
        ("8 x 10, r=2", 80, 2),
    ]:
        res = run_cell(rng, s, nd, r, P_A2, P_A3, sig)
        print(f"{label:<34} {res['naive']:>10.3f} {res['cluster']:>10.3f}")

    print("\n" + "=" * 74)
    print("4. MINIMUM DETECTABLE EFFECT (cluster estimator, 80% power)")
    print("=" * 74)
    for label, nd, r, cl in [
        ("CURRENT ablation: 8 x 5, r=2", 40, 2, None),
        ("proposed: 8 x 10, r=2", 80, 2, None),
        ("8 x 20, r=2", 160, 2, None),
        ("Tier 1: 11 defects / 5 cells, r=3", 11, 3, TIER1_CELLS),
    ]:
        d = mde(rng, max(600, s // 3), nd, r, sig, cluster_sizes=cl)
        print(f"{label:<34} MDE = {100*d:>5.1f} pp")

    print("\n" + "=" * 74)
    print("5. SENSITIVITY to defect heterogeneity (A1 vs A2, cluster estimator)")
    print("=" * 74)
    print(f"{'sigma':<10} {'8 x 5':>10} {'8 x 10':>10} {'8 x 20':>10}")
    for sg in (0.5, 1.0, 1.5, 2.0):
        row = [run_cell(rng, s, nd, 2, P_A1, P_A2, sg)["cluster"]
               for nd in (40, 80, 160)]
        print(f"{sg:<10} {row[0]:>10.3f} {row[1]:>10.3f} {row[2]:>10.3f}")

    print("\n" + "=" * 74)
    print("8. ROBUSTNESS - shared-occasion effect (arms run contiguously, 14.1)")
    print("=" * 74)
    print("Sections 1-7 assume arms are independent given the defect. They are not:")
    print("all arms for one defect run in one session and share the serving stack")
    print("of that moment, which makes them MORE alike, cuts discordant pairs, and")
    print("costs McNemar power. Every figure above is optimistic by this much:")
    print(f"{'occasion SD':<14} {'8 x 10':>10} {'8 x 20':>10} {'8 x 30':>10}")
    for so in (0.0, 0.5, 1.0, 1.5):
        row = [run_cell(rng, s, nd, 2, P_A1, P_A2, sig, sigma_occasion=so)["cluster"]
               for nd in (80, 160, 240)]
        print(f"{so:<14} {row[0]:>10.3f} {row[1]:>10.3f} {row[2]:>10.3f}")

    print("\n" + "=" * 74)
    print("7. INTERACTION power - can the D8 C1 cell do what it exists to do?")
    print("=" * 74)
    print("H1: constraint disclosure explains half the A1-A2 gap, so the gap is")
    print("    12pp under the production prompt C0 and 6pp under C1.")
    print("    The question is a difference-in-differences, not a main effect.")
    print(f"{'C0 defects / C1 defects':<34} {'power':>10}")
    for n0, n1 in [(160, 40), (160, 80), (160, 160), (320, 320)]:
        # gap under C0 minus gap under C1, bootstrapped over defects in each cell
        a0, b0 = simulate(rng, s, n0, 2, P_A1, P_A2, sig)
        a1, b1 = simulate(rng, s, n1, 2, P_A1, P_A2 + 0.06, sig)
        d0 = (a0.mean(axis=2) - b0.mean(axis=2))
        d1 = (a1.mean(axis=2) - b1.mean(axis=2))
        n_boot = 800
        i0 = rng.integers(0, n0, size=(n_boot, n0))
        i1 = rng.integers(0, n1, size=(n_boot, n1))
        boot = bootstrap_means(d0, i0) - bootstrap_means(d1, i1)
        lo, hi = np.percentile(boot, [2.5, 97.5], axis=0)
        power = float(((lo > 0) | (hi < 0)).mean())
        print(f"{f'{n0} / {n1}':<34} {power:>10.3f}")

    print("\n" + "=" * 74)
    print("6. REPS vs BLOCKS - where does the next call buy the most?")
    print("=" * 74)
    print(f"{'design':<34} {'trials/arm':>11} {'power':>9}")
    for label, nd, r in [
        ("8 x 10, r=2", 80, 2),
        ("8 x 10, r=4  (more reps)", 80, 4),
        ("8 x 20, r=2  (more blocks)", 160, 2),
    ]:
        res = run_cell(rng, s, nd, r, P_A1, P_A2, sig)
        print(f"{label:<34} {nd*r:>11} {res['cluster']:>9.3f}")

    print("\n" + "=" * 74)
    print("9. THE DESIGN AS BUILT - power at the COMPUTED defect counts")
    print("=" * 74)
    print("Sections 1-8 sweep '8 operators x N dumps', which assumes every")
    print("operator can use every dump. It cannot: operators are stage-specific,")
    print("stages differ in clean bases, and two operators carry no repair")
    print("endpoint at all. scripts/inject_defects.py --matrix computes the real")
    print("ceiling; this section takes it as given so the plan can cite a number")
    print("rather than a multiplication. Occasion SD 1.0 is the honest column:")
    print("section 14.1 forces all arms for one defect into one session.")
    # Each row gets its OWN generator, not the one threaded through sections
    # 1-8. These are the figures the plan and the Phase-0 memo cite by value, so
    # a row must not move because an earlier section was edited, reordered, or
    # because --defects listed a different count ahead of it.
    #
    # They are still Monte Carlo estimates. At the default sims=2000 a power
    # figure carries roughly +/-0.02 and an MDE roughly +/-0.4 pp, which is why
    # the cited table was produced at --sims 20000 and why nothing here should
    # be quoted to three decimals.
    counts = [int(x) for x in args.defects.split(",") if x.strip()]
    print(f"{'defects':>8} {'r':>3} {'power':>9} {'w/ occasion':>13} {'MDE':>9} "
          f"{'MDE w/ occ':>12}")
    for i, nd in enumerate(counts):
        for j, r in enumerate((2, 3, 4)):
            rng9 = np.random.default_rng(args.seed + 1000 * i + j)
            res = run_cell(rng9, s, nd, r, P_A1, P_A2, sig)
            occ = run_cell(rng9, s, nd, r, P_A1, P_A2, sig, sigma_occasion=1.0)
            d = mde(rng9, max(600, s // 3), nd, r, sig)
            d_occ = mde(rng9, max(600, s // 3), nd, r, sig, sigma_occasion=1.0)
            print(f"{nd:>8} {r:>3} {res['cluster']:>9.3f} {occ['cluster']:>13.3f} "
                  f"{100*d:>8.1f}pp {100*d_occ:>11.1f}pp")
    print()
    print("D11b requires the split threshold X to be >= the MDE. Read the MDE")
    print("column against the proposed 12 pp: where it is not comfortably below,")
    print("the pre-registration is incoherent and needs more defects, not a")
    print("smaller threshold chosen after the fact.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
