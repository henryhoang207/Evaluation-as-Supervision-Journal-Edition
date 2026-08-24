"""Run-to-run churn baseline for the collateral threshold (JOURNAL_PLAN D3c).

D3 defines `collateral` as "non-defective items materially changed", and leaves
"materially" undefined. It cannot stay undefined, because the retried stage
**regenerates** its whole output rather than editing it - so some churn happens
in every trial whether or not the feedback caused it.

This script measures how much an *unperturbed* pipeline already churns, using
the repetition sub-study: the same 5 businesses re-run 5 times in observe mode,
same seed, same sampled reviews, temperature 0, no injection and no feedback.
Whatever churn appears there is the floor. A collateral threshold set below it
would flag noise as damage.

Items are matched across runs with `supervision._similar` at the same 0.35
threshold the traceability check uses, so "same item" means here what it means
to the supervisor.

Run (from backend/, venv active - read-only, no API calls, no dataset):

    python scripts/analysis/churn.py
"""

from __future__ import annotations

import argparse
import glob
import itertools
import json
import os
import statistics
import sys

# scripts/analysis/churn.py -> backend/ is three levels up.
sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
)

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from app.core.supervision import _similar, TRACE_SIMILARITY  # noqa: E402


def _load(path):
    if not os.path.exists(path):
        return None
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (json.JSONDecodeError, OSError):
        return None


def _items(dump_dir: str) -> dict[str, list[str]]:
    """The item sets a collateral measure would compare."""
    out: dict[str, list[str]] = {}
    reasoning = _load(os.path.join(dump_dir, "reasoning.json")) or {}
    strategy = _load(os.path.join(dump_dir, "strategy.json")) or {}
    if isinstance(reasoning, dict) and reasoning.get("status") == "success":
        out["pattern_aspects"] = [p.get("aspect", "") for p in reasoning.get("patterns") or []]
        out["pattern_descriptions"] = [p.get("description", "") for p in reasoning.get("patterns") or []]
        out["root_causes"] = [rc.get("cause", "") for rc in reasoning.get("root_causes") or []]
    if isinstance(strategy, dict) and strategy.get("status") == "success":
        out["rec_issues"] = [r.get("issue", "") for r in strategy.get("recommendations") or []]
    return out


def matched_fraction(a: list[str], b: list[str], threshold: float) -> float | None:
    """Fraction of `a` with a distinct partner in `b` above the threshold.

    Greedy one-to-one matching, so duplicating an item cannot inflate the score.
    """
    if not a and not b:
        return None
    if not a or not b:
        return 0.0
    remaining = list(b)
    hits = 0
    for item in a:
        best, best_score = None, threshold
        for cand in remaining:
            score = _similar(item, cand)
            if score >= best_score:
                best, best_score = cand, score
        if best is not None:
            remaining.remove(best)
            hits += 1
    return hits / len(a)


def exact_fraction(a: list[str], b: list[str]) -> float | None:
    """Same, but requiring identical strings - the report-stage containment rule."""
    if not a and not b:
        return None
    if not a or not b:
        return 0.0
    remaining = list(b)
    hits = 0
    for item in a:
        if item in remaining:
            remaining.remove(item)
            hits += 1
    return hits / len(a)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default="out_study/R")
    ap.add_argument("--threshold", type=float, default=TRACE_SIMILARITY)
    args = ap.parse_args()

    reps = sorted(glob.glob(os.path.join(args.root, "rep*", "A")))
    if len(reps) < 2:
        print(f"Need at least two repetitions under {args.root!r}.")
        return 1

    businesses = sorted({
        os.path.basename(d)
        for rep in reps
        for d in glob.glob(os.path.join(rep, "*"))
        if os.path.isdir(d)
    })

    print(f"Repetitions: {len(reps)}  ·  businesses: {len(businesses)}  ·  "
          f"similarity threshold: {args.threshold}")
    print("Identical inputs, temperature 0, no injection, no feedback.")
    print("Every departure from 1.00 below is churn the pipeline produces on its own.\n")

    fields = ["pattern_aspects", "pattern_descriptions", "root_causes", "rec_issues"]
    fuzzy: dict[str, list[float]] = {f: [] for f in fields}
    exact: dict[str, list[float]] = {f: [] for f in fields}
    counts: dict[str, list[int]] = {f: [] for f in fields}

    for bid in businesses:
        per_rep = {}
        for rep in reps:
            d = os.path.join(rep, bid)
            if os.path.isdir(d):
                items = _items(d)
                if items:
                    per_rep[rep] = items
        for r1, r2 in itertools.combinations(sorted(per_rep), 2):
            for f in fields:
                a, b = per_rep[r1].get(f), per_rep[r2].get(f)
                if a is None or b is None:
                    continue
                # Symmetrise: churn should not depend on comparison direction.
                mf = matched_fraction(a, b, args.threshold)
                mr = matched_fraction(b, a, args.threshold)
                if mf is not None and mr is not None:
                    fuzzy[f].append((mf + mr) / 2)
                ef = exact_fraction(a, b)
                er = exact_fraction(b, a)
                if ef is not None and er is not None:
                    exact[f].append((ef + er) / 2)
        for f in fields:
            for items in per_rep.values():
                if f in items:
                    counts[f].append(len(items[f]))

    print(f"{'item set':<24} {'pairs':>6} {'fuzzy match':>22} {'exact match':>14} {'n items':>9}")
    print("-" * 80)
    for f in fields:
        vals, evals_, cs = fuzzy[f], exact[f], counts[f]
        if not vals:
            print(f"{f:<24} {'-':>6}")
            continue
        mean = statistics.mean(vals)
        lo, hi = min(vals), max(vals)
        emean = statistics.mean(evals_) if evals_ else float("nan")
        cmean = statistics.mean(cs) if cs else float("nan")
        print(f"{f:<24} {len(vals):>6} "
              f"{mean:>9.2f}  (min {lo:.2f}, max {hi:.2f}) "
              f"{emean:>13.2f} {cmean:>9.1f}")

    print()
    print("Reading: 'fuzzy match' is the fraction of items with a counterpart in")
    print("the other run at the supervisor's own similarity threshold. 1 - that")
    print("value is the baseline churn rate a collateral threshold must clear.")

    print("\n" + "=" * 80)
    print("NULL CHURN DISTRIBUTION - what a collateral threshold has to clear")
    print("=" * 80)
    print(f"{'item set':<24} {'median':>8} {'p75':>8} {'p90':>8} {'p95':>8}  verdict")
    print("-" * 80)
    for f in fields:
        vals = fuzzy[f]
        if not vals:
            continue
        churn = sorted(1 - v for v in vals)

        def pct(q):
            if len(churn) == 1:
                return churn[0]
            i = min(len(churn) - 1, max(0, int(round(q * (len(churn) - 1)))))
            return churn[i]

        p50, p75, p90, p95 = pct(0.50), pct(0.75), pct(0.90), pct(0.95)
        if p95 >= 0.90:
            verdict = "very weak - see the upstream caveat below"
        elif p95 >= 0.50:
            verdict = "weak - only gross damage detectable"
        else:
            verdict = f"usable, threshold > {p95:.2f}"
        print(f"{f:<24} {p50:>8.2f} {p75:>8.2f} {p90:>8.2f} {p95:>8.2f}  {verdict}")

    print()
    print("A collateral threshold set below a column's p95 would fire on runs where")
    print("nothing was injected and no feedback was given. Caveat: 5 businesses,")
    print("so these are calibration estimates, not population values.")

    # These figures OVERSTATE the floor for a replay experiment, and by how much
    # is measurable. In a repetition run every stage regenerates, so downstream
    # churn compounds upstream churn. In a replay trial the upstream output is
    # pinned from the dump, so only the retried stage varies. Conditioning on
    # near-identical upstream recovers the number the experiment will actually
    # face.
    ups, downs = [], []
    for bid in businesses:
        per_rep = {}
        for rep in reps:
            d = os.path.join(rep, bid)
            if os.path.isdir(d):
                it = _items(d)
                if it:
                    per_rep[rep] = it
        for r1, r2 in itertools.combinations(sorted(per_rep), 2):
            ua, ub = per_rep[r1].get("pattern_descriptions"), per_rep[r2].get("pattern_descriptions")
            da, db = per_rep[r1].get("rec_issues"), per_rep[r2].get("rec_issues")
            if None in (ua, ub, da, db):
                continue
            u = (matched_fraction(ua, ub, args.threshold)
                 + matched_fraction(ub, ua, args.threshold)) / 2
            d_ = (matched_fraction(da, db, args.threshold)
                  + matched_fraction(db, da, args.threshold)) / 2
            ups.append(u)
            downs.append(d_)

    stable = [d for u, d in zip(ups, downs) if u >= 0.95]
    drifted = [d for u, d in zip(ups, downs) if u < 0.95]
    if stable and drifted:
        print("\n" + "=" * 80)
        print("UPSTREAM CAVEAT - the figures above are NOT the replay-condition floor")
        print("=" * 80)
        print("Repetition runs regenerate every stage, so strategy churn compounds")
        print("reasoning churn. A replay trial pins the upstream output, so only the")
        print("retried stage moves. Splitting the pairs on upstream stability:")
        print(f"  upstream near-identical (>=0.95): n={len(stable):>3}  "
              f"rec_issues churn = {1 - statistics.mean(stable):.0%}")
        print(f"  upstream drifted        (< 0.95): n={len(drifted):>3}  "
              f"rec_issues churn = {1 - statistics.mean(drifted):.0%}")
        print("Use the first row for the strategy-stage collateral threshold.")
        print("It rests on few pairs, so treat it as an upper-bounded estimate.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
