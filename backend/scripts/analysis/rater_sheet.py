"""Defect-bank audit instrument (JOURNAL_PLAN D13).

The bank is defined by the detector that found it, so validating it with that
detector proves nothing. D13 breaks the circularity by splitting the construct:

    groundedness   factual, machine-checkable, and already checked EXHAUSTIVELY
                   by supervision.measure plus tests/test_replay.py. It is
                   verification, not a rating, and no kappa applies to it.
    meaningfulness judgement. Needs two humans, and this module is the
                   instrument they use.

An LLM is not a legitimate rater here. It wrote defect_bank.py, which *defines*
the bank; rating its own classifier's output reproduces exactly the circularity
the audit exists to break. This module builds a sheet for humans and scores what
they return. It never rates.

Where each item's content comes from
------------------------------------
Never from re-deriving the defect off the state. A Tier-1 item is rendered from
the **recorded facts** (defect_bank entry -> facts), which name every offending
pattern; a Tier-2 item is rendered from the **injection descriptor**, which names
exactly the one thing that was changed. An earlier version of this module
recomputed "the first pattern with a problem" and so showed a rater one pattern
of a defect that spanned six. That is the same trap NEXT_SESSION item 13 records
for the defect bank itself: do not re-derive what a script already pinned.

What the blinding does and does not achieve
-------------------------------------------
Hidden: tier (real vs injected), operator, check class, business, defect id.
**Not hidden:** an item's shape still hints at its class -- an evidence-citation
item cannot be made to look like a recommendation item. That is unavoidable, and
it is not what the blinding is for. What matters is that a rater cannot tell
**which items are the real defects and which were injected**, so agreement
cannot be an artefact of knowing which ones are supposed to count.

Run (from backend/, read-only, no API calls, no dataset):

    python scripts/analysis/rater_sheet.py --build --out out_study/audit
    # two humans fill in a copy of the CSV each, without opening key.json
    python scripts/analysis/rater_sheet.py --score out_study/audit
        --a out_study/audit/rating_a.csv --b out_study/audit/rating_b.csv
"""

from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def _load(name: str, relative: str):
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    spec = importlib.util.spec_from_file_location(name, os.path.join(here, relative))
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module          # dataclasses resolve through sys.modules
    spec.loader.exec_module(module)
    return module


inject_defects = _load("inject_defects", "inject_defects.py")

TIER2_SAMPLE = 20        # plus the 11 usable Tier-1 defects = 31 items
SEED = 20260826

RATINGS = ("E", "T", "U")

RUBRIC = """\
## What you are looking at

An automated pipeline reads customer reviews of one restaurant and passes them
through several stages. An early stage summarises each review; later stages find
recurring patterns across those reviews, propose recommendations, and write a
final report. Each stage may only draw on what the stages before it produced.

Each item below is one such output, shown in three blocks:

- **What the output claimed** - what the stage actually wrote.
- **What it was given** - the material it was entitled to draw on.
- **What the check found** - a factual discrepancy between the two. This has
  already been verified mechanically and is true. You are not being asked to
  re-check it, and you do not need the original reviews to do so.

So you are judging the **output**, not the checker. Granting that the
discrepancy is real, does it amount to an error?

## The one question

For each item below, answer with a single letter.

> **Reading only what is shown: is this a defect a competent analyst would call
> an error in the output, or is it a technicality of an automated check?**

- **E - error.** The output makes a claim that is not supported by what it was
  given. A reader relying on this output would be misled.
- **T - technicality.** The check fired, but the output is defensible: a
  reasonable paraphrase, a harmless restatement, or something a careful human
  reviewer would let stand.
- **U - cannot judge** from what is shown. Use sparingly. A high U rate is
  itself a finding about the instrument; U items are excluded from kappa and
  reported separately.

Add a short note whenever you hesitate. The notes are what make a disagreement
useful; the letters alone only make it countable.

## Rules

1. **Rate independently.** Do not discuss items with the other rater until both
   sheets are submitted.
2. **Do not open key.json.** It records which items are real and which were
   injected, and reading it ends the blinding.
3. Rate in the order given. The order is already randomised.
"""


# -- item rendering -----------------------------------------------------------
#
# One renderer per check class. Each returns the CLAIM the stage made, the
# CONTEXT needed to judge it, and the FACT the check established. The fact is
# stated rather than left for the rater to verify: groundedness is settled
# programmatically, and the human is being asked about meaning, not about
# whether the string is really there.


def _fmt_list(items: list[str], limit: int = 12) -> str:
    if not items:
        return "  (none)"
    shown = [f"  - {s}" for s in items[:limit]]
    if len(items) > limit:
        shown.append(f"  - ... and {len(items) - limit} more")
    return "\n".join(shown)


def _pattern_block(pattern: dict) -> str:
    return (f"  \"{pattern.get('description', '')}\"\n"
            f"  aspect: {pattern.get('aspect', '')}\n"
            f"  cites: "
            f"{', '.join(str(i) for i in pattern.get('evidence_review_ids', [])) or '(none)'}")


def _render_missing_evidence(state: dict, offences: list[tuple[dict, list[str]]]) -> dict:
    """`offences` is every (pattern, unresolvable-ids) pair the check recorded."""
    known = {a.get("review_id") for a in (state.get("analysis_results") or [])}
    claim = "\n\n".join(_pattern_block(p) for p, _ in offences)
    facts = []
    for pattern, bad in offences:
        head = (pattern.get("description") or "")[:60]
        facts.append(f"  in \"{head}...\":\n" + "\n".join(f"    - {b}" for b in bad))
    n_patterns = len(offences)
    n_bad = sum(len(bad) for _, bad in offences)
    scope = f"{n_patterns} pattern" + ("" if n_patterns == 1 else "s")
    subject = ("this cited review id does" if n_bad == 1
               else "these cited review ids do")
    return {
        "claim": (f"Recurring negative {'pattern' if len(offences) == 1 else 'patterns'} "
                  f"reported, with the reviews cited as evidence:\n\n{claim}"),
        "context": f"The stage was given {len(known)} analysed reviews to work from.",
        "fact": (f"Across {scope}, {subject} not appear anywhere in "
                 f"the reviews the stage was given:\n" + "\n".join(facts)),
    }


def _render_misaligned_aspect(state: dict, offences: list[tuple[dict, list[dict]]]) -> dict:
    claim = "\n\n".join(_pattern_block(p) for p, _ in offences)
    facts = []
    for pattern, offenders in offences:
        head = (pattern.get("description") or "")[:60]
        rows = [f"    - review {o['review_id']} mentions: "
                f"{', '.join(o['aspects']) or '(no aspects recorded)'}"
                for o in offenders]
        facts.append(f"  in \"{head}...\" (aspect {pattern.get('aspect')}):\n"
                     + ("\n".join(rows) if rows else "    (none)"))
    return {
        "claim": (f"Recurring negative {'pattern' if len(offences) == 1 else 'patterns'} "
                  f"reported, with the reviews cited as evidence:\n\n{claim}"),
        "context": ("Each cited review was analysed earlier, and that analysis "
                    "recorded which aspects the review actually mentions."),
        "fact": ("Cited reviews that do not mention the pattern's aspect:\n"
                 + "\n".join(facts)),
    }


def _render_untraceable(state: dict, issues: list[str]) -> dict:
    reasoning = state.get("reasoning_output") or {}
    patterns = [p.get("description", "") for p in reasoning.get("patterns", [])]
    causes = [c.get("cause", "") for c in reasoning.get("root_causes", [])]
    return {
        "claim": ("A recommendation was made addressing these problems:\n"
                  + _fmt_list(issues)),
        "context": ("Everything the recommending stage was given.\n\n"
                    f"Patterns found upstream:\n{_fmt_list(patterns)}\n\n"
                    f"Root causes found upstream:\n{_fmt_list(causes)}"),
        "fact": ("An automated match found no upstream pattern or root cause "
                 "close enough to any of the problems above."),
    }


def _render_containment(item: str, kind: str, upstream: list[str]) -> dict:
    return {
        "claim": f"The final report includes this {kind}:\n\n  \"{item}\"",
        "context": ("The report stage is only supposed to restate what upstream "
                    f"produced. Everything upstream offered:\n{_fmt_list(upstream)}"),
        "fact": f"This {kind} does not appear in any upstream output.",
    }


# -- helpers over a state -----------------------------------------------------


def _aspects(review: dict) -> list[str]:
    """Through inject_defects, which is what the supervisor's own check reads."""
    return sorted(a for a in inject_defects._aspects_of(review) if a)


def _offenders_for(state: dict, pattern: dict) -> list[dict]:
    by_id = {a.get("review_id"): a for a in (state.get("analysis_results") or [])}
    aspect = pattern.get("aspect")
    out = []
    for rid in pattern.get("evidence_review_ids", []):
        row = by_id.get(rid)
        if row is not None and aspect not in _aspects(row):
            out.append({"review_id": rid, "aspects": _aspects(row)})
    return out


def _unresolved_for(state: dict, pattern: dict) -> list[str]:
    known = {a.get("review_id") for a in (state.get("analysis_results") or [])}
    return [str(i) for i in pattern.get("evidence_review_ids", []) if i not in known]


# -- tier 1 -------------------------------------------------------------------


def _tier1_items(bank: dict) -> list[dict]:
    """One rateable item per usable natural defect, rendered from its facts."""
    out = []
    for entry in bank.get("entries", []):
        if not entry.get("usable"):
            continue
        state = inject_defects.state_from_dump(entry["dump_dir"])
        facts = entry.get("facts") or {}
        classes = entry.get("classes") or []
        patterns = (state.get("reasoning_output") or {}).get("patterns") or []
        body = None

        if "untraceable_recommendation" in classes:
            body = _render_untraceable(state, facts.get("untraceable_issues") or [])

        elif "missing_evidence_id" in classes:
            # Every pattern the measurement flagged, not the first one found by
            # re-deriving: one banked defect spans six patterns, and showing one
            # of them would put a different question to the rater.
            offences = [(patterns[f["index"]], [str(i) for i in f["missing_evidence_ids"]])
                        for f in facts.get("patterns", [])
                        if f.get("missing_evidence_ids") and f["index"] < len(patterns)]
            if offences:
                body = _render_missing_evidence(state, offences)

        elif "misaligned_aspect" in classes:
            offences = [(patterns[f["index"]], _offenders_for(state, patterns[f["index"]]))
                        for f in facts.get("patterns", [])
                        if f.get("misaligned_evidence_ids") and f["index"] < len(patterns)]
            if offences:
                body = _render_misaligned_aspect(state, offences)

        if body:
            out.append({**body, "_tier": "tier1", "_label": ",".join(classes),
                        "_source": entry["defect_id"]})
    return out


# -- tier 2 -------------------------------------------------------------------


def _tier2_items(root: str, n: int, rng: random.Random) -> list[dict]:
    """A stratified sample of injected defects, so every operator is represented."""
    pool: dict[str, list[str]] = {op: [] for op in inject_defects.REPAIR_OPERATORS}
    for dump_dir in inject_defects.base_dirs(root):
        state = inject_defects.state_from_dump(dump_dir)
        for op in inject_defects.REPAIR_OPERATORS:
            ok, _ = inject_defects.applicable(op, state)
            if ok:
                pool[op].append(dump_dir)

    for op in pool:
        rng.shuffle(pool[op])

    picked: list[tuple[str, str]] = []
    while len(picked) < n and any(pool.values()):
        for op in inject_defects.REPAIR_OPERATORS:      # round-robin = stratified
            if pool[op] and len(picked) < n:
                picked.append((pool[op].pop(), op))

    out = []
    for dump_dir, op in picked:
        base = inject_defects.state_from_dump(dump_dir)
        injected, descriptor = inject_defects.inject(op, base, seed=0)
        if not descriptor.applied:
            continue
        body = _render_injected(descriptor, injected)
        if body:
            out.append({**body, "_tier": "tier2", "_label": op,
                        "_source": f"{os.path.basename(dump_dir)}:{op}"})
    return out


def _render_injected(descriptor, injected: dict) -> dict | None:
    """Rendered from the descriptor, which names exactly what was changed.

    Re-deriving "the first pattern with a problem" would sometimes surface a
    pre-existing defect in the base rather than the injected one.
    """
    target = descriptor.target or {}
    cls = descriptor.check_class
    patterns = (injected.get("reasoning_output") or {}).get("patterns") or []
    index = target.get("pattern_index")

    if cls == "missing_evidence_id":
        if index is None or index >= len(patterns):
            return None
        pattern = patterns[index]
        return _render_missing_evidence(injected, [(pattern, _unresolved_for(injected, pattern))])

    if cls == "misaligned_aspect":
        if index is None or index >= len(patterns):
            return None
        pattern = patterns[index]
        return _render_misaligned_aspect(injected, [(pattern, _offenders_for(injected, pattern))])

    if cls == "untraceable_recommendation":
        return _render_untraceable(injected, [str(target.get("after", ""))])

    if cls == "report_containment":
        reasoning = injected.get("reasoning_output") or {}
        strategy = injected.get("strategy_output") or {}
        if "inserted_root_cause" in target:
            item = target["inserted_root_cause"].get("cause", "")
            upstream = [c.get("cause", "") for c in reasoning.get("root_causes", [])
                        if c.get("cause") != item]
            return _render_containment(item, "root cause", upstream)
        if "inserted_recommendation" in target:
            item = target["inserted_recommendation"].get("action", "")
            upstream = [r.get("action", "") for r in strategy.get("recommendations", [])
                        if r.get("action") != item]
            return _render_containment(item, "recommended action", upstream)
    return None


# -- build --------------------------------------------------------------------


def build(root: str, out_dir: str, seed: int = SEED, n_tier2: int = TIER2_SAMPLE) -> int:
    bank_path = os.path.join(root, "defect_bank.json")
    if not os.path.exists(bank_path):
        print(f"no defect bank at {bank_path}; run scripts/analysis/defect_bank.py first")
        return 1
    with open(bank_path, encoding="utf-8") as fh:
        bank = json.load(fh)

    rng = random.Random(seed)
    items = _tier1_items(bank) + _tier2_items(root, n_tier2, rng)
    rng.shuffle(items)

    os.makedirs(out_dir, exist_ok=True)
    key = {}
    lines = ["# Defect-bank audit - rating sheet", "",
             f"{len(items)} items, order randomised with seed {seed}.", "",
             "**Rater name:** ______________________    **Date:** ____________", "",
             RUBRIC, "---", ""]

    for i, item in enumerate(items, 1):
        item_id = f"I{i:02d}"
        key[item_id] = {"tier": item["_tier"], "label": item["_label"],
                        "source": item["_source"]}
        lines += [f"## {item_id}", "",
                  "**What the output claimed**", "", "```", item["claim"], "```", "",
                  "**What it was given**", "", "```", item["context"], "```", "",
                  "**What the check found**", "", "```", item["fact"], "```", "",
                  f"**{item_id} rating (E / T / U):** ____", "",
                  "**Note:** ______________________________________________", "",
                  "---", ""]

    with open(os.path.join(out_dir, "rating_sheet.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))

    with open(os.path.join(out_dir, "rating_sheet.csv"), "w", encoding="utf-8",
              newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["item_id", "rating", "note"])
        for i in range(1, len(items) + 1):
            writer.writerow([f"I{i:02d}", "", ""])

    with open(os.path.join(out_dir, "key.json"), "w", encoding="utf-8") as fh:
        json.dump({"seed": seed, "n_items": len(items), "key": key}, fh,
                  indent=2, ensure_ascii=False)

    n1 = sum(1 for i in items if i["_tier"] == "tier1")
    print(f"built {len(items)} items ({n1} real, {len(items) - n1} injected) -> {out_dir}")
    print("  rating_sheet.md   give a copy to each rater")
    print("  rating_sheet.csv  each rater fills in their own copy")
    print("  key.json          SEALED. Do not open until both sheets are back.")
    return 0


# -- score --------------------------------------------------------------------


def _read_sheet(path: str) -> dict[str, tuple[str, str]]:
    out = {}
    with open(path, encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            rating = (row.get("rating") or "").strip().upper()
            if rating:
                out[row["item_id"].strip()] = (rating, (row.get("note") or "").strip())
    return out


def kappa(pairs: list[tuple[str, str]]) -> float:
    """Cohen's kappa for two raters on one categorical judgement.

    Returns NaN when the table has a single occupied category. Both raters
    calling everything an error is not perfect agreement, it is no information,
    and 1.0 would be the flattering answer rather than the true one.
    """
    n = len(pairs)
    if not n:
        return float("nan")
    observed = sum(1 for a, b in pairs if a == b) / n
    categories = {c for pair in pairs for c in pair}
    expected = sum((sum(1 for a, _ in pairs if a == c) / n) *
                   (sum(1 for _, b in pairs if b == c) / n) for c in categories)
    if expected >= 1.0:
        return float("nan")
    return (observed - expected) / (1 - expected)


def score(out_dir: str, path_a: str, path_b: str, n_boot: int = 5000) -> int:
    a, b = _read_sheet(path_a), _read_sheet(path_b)
    shared = sorted(set(a) & set(b))
    if not shared:
        print("no items rated by both raters")
        return 1

    unknown = sorted({r for i in shared for r in (a[i][0], b[i][0]) if r not in RATINGS})
    if unknown:
        print(f"unrecognised ratings {unknown}; allowed: {list(RATINGS)}")
        return 1

    unratable = [i for i in shared if "U" in (a[i][0], b[i][0])]
    pairs = [(a[i][0], b[i][0]) for i in shared if i not in unratable]

    print(f"items rated by both  : {len(shared)}")
    print(f"excluded as U        : {len(unratable)} {unratable if unratable else ''}")
    print(f"kappa computed on    : {len(pairs)}")
    if not pairs:
        print("nothing left to score")
        return 1

    agreed = sum(1 for x, y in pairs if x == y)
    k = kappa(pairs)
    rng = random.Random(SEED)
    boot = [kappa([pairs[rng.randrange(len(pairs))] for _ in pairs]) for _ in range(n_boot)]
    boot = sorted(v for v in boot if v == v)              # drop degenerate resamples
    lo, hi = ((boot[int(0.025 * len(boot))], boot[int(0.975 * len(boot))])
              if boot else (float("nan"), float("nan")))

    print()
    print(f"raw agreement        : {agreed}/{len(pairs)} = {agreed / len(pairs):.3f}")
    print(f"Cohen's kappa        : {k:.3f}  95% CI [{lo:.3f}, {hi:.3f}]")
    print(f"  bootstrap over items, {len(boot)} usable resamples of {n_boot}")
    if k != k:
        print("  kappa is undefined here: one category, so there is no information "
              "in the table. Report raw agreement and n instead.")
    print()
    print("Report the CI, or report raw agreement and n. A bare kappa on "
          f"{len(pairs)} items overstates what this settles.")

    disagreements = [i for i in shared if a[i][0] != b[i][0]]
    if disagreements:
        print(f"\ndisagreements ({len(disagreements)}) - resolve and record each:")
        for i in disagreements:
            print(f"  {i}: A={a[i][0]} B={b[i][0]}")
            for who, sheet in (("A", a), ("B", b)):
                if sheet[i][1]:
                    print(f"      {who}: {sheet[i][1]}")

    key_path = os.path.join(out_dir, "key.json")
    if os.path.exists(key_path):
        with open(key_path, encoding="utf-8") as fh:
            key = json.load(fh)["key"]
        print("\nunblinded breakdown (both sheets are in, so this is now safe):")
        for tier in ("tier1", "tier2"):
            rows = [i for i in shared
                    if key.get(i, {}).get("tier") == tier and i not in unratable]
            if not rows:
                continue
            both_error = sum(1 for i in rows if a[i][0] == "E" and b[i][0] == "E")
            print(f"  {tier}: {len(rows)} rated, {both_error} called an error by both "
                  f"({both_error / len(rows):.0%})")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default="out_study")
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--out", default="out_study/audit")
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--n-tier2", type=int, default=TIER2_SAMPLE)
    ap.add_argument("--score", metavar="DIR")
    ap.add_argument("--a", help="rater A's filled CSV")
    ap.add_argument("--b", help="rater B's filled CSV")
    args = ap.parse_args()

    if args.build:
        return build(args.root, args.out, args.seed, args.n_tier2)
    if args.score:
        if not (args.a and args.b):
            ap.error("--score needs --a and --b")
        return score(args.score, args.a, args.b)
    ap.error("give --build, or --score DIR --a A.csv --b B.csv")
    return 1


if __name__ == "__main__":
    sys.exit(main())
