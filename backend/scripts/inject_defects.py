"""Synthetic defect injection operators (JOURNAL_PLAN B4).

Each operator corrupts one clean stage output in a way that is designed to trip
exactly one supervisor check class. The operator and the supervisor are
independent programs: the operator writes a ground-truth descriptor saying what
it did and which check it expects to fire, and ``supervision.measure`` then says
what actually fired. Agreement between the two is the correctness gate for this
module (``tests/test_inject.py``), and it costs no LLM calls.

**Determinism.** Every operator takes a seed and makes every choice through
``random.Random(f"{business_id}:{op}:{seed}")``. Re-running with the same seed
reproduces the injected output byte for byte.

**Applicability is a first-class outcome.** An operator with nothing to corrupt
records ``applied=False`` with a reason rather than being silently skipped
(B4). The per-operator applicability matrix over a study root is what sets the
Tier-2 defect ceiling, and it is computed here rather than multiplied by hand —
the plan's original 160 came from ``8 operators x 20 dumps`` and was wrong,
because operators are stage-specific and stages differ in how many clean bases
they have.

**Two operators are not repair operators.** See ``ENDPOINT``:

- **O4** (frequency divergence) yields ``proceed_with_warning``, never a retry,
  and ``graph`` then overwrites the claimed value deterministically
  (``apply_frequency_corrections``). There is no retry for an arm to act on and
  no LLM involvement in the correction. It is carried here as a *warn-level*
  operator so the grid composition stays a config choice.
- **O8** (metadata mismatch) is a **positive control**: ``report_node`` passes
  the correct values in the prompt payload, so any retry copies them back at
  ~100% in every arm. Its repair rate should be 1.0; a value below that means
  the scorer is broken, not that the model failed.

Run (from backend/, venv active — read-only, no API calls, no dataset):

    python scripts/inject_defects.py --root out_study --matrix
    python scripts/inject_defects.py --dump-dir out_study/A/<bid> --op O1
"""

from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import os
import random
import string
import sys
from dataclasses import asdict, dataclass, field
from typing import Any

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from app.core import supervision  # noqa: E402
from app.schemas.contracts import AspectCategory  # noqa: E402
from eval.common import load_dump  # noqa: E402


def _load_by_path(name: str, relative: str):
    """scripts/ is not a package; load a sibling analysis module by path."""
    here = os.path.dirname(os.path.abspath(__file__))
    spec = importlib.util.spec_from_file_location(name, os.path.join(here, relative))
    module = importlib.util.module_from_spec(spec)
    # Register before exec: @dataclass resolves cls.__module__ through
    # sys.modules, and a path-loaded module that is not there yields None.
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


defect_bank = _load_by_path("defect_bank", "analysis/defect_bank.py")

ASPECTS: tuple[str, ...] = tuple(AspectCategory.__args__)

# Yelp review ids are 22 characters of base64url. O2 fabricates ids in the same
# shape so the defect is "this id does not exist", not "this id is malformed" —
# a malformed id would be caught by anything, which is not the check under test.
_ID_ALPHABET = string.ascii_letters + string.digits + "-_"
_ID_LENGTH = 22


# ── frozen insertion corpora ──────────────────────────────────────────────────
#
# Generated once and pinned here as source, never regenerated per run (B4).
#
# Calibrated against the observed defect mode rather than invented blind. The
# nine real untraceable issues in the Tier-1 bank are terse abstractions —
# "Negative ambience.", "Excessive customer wait times." — not alien vocabulary:
# the strategy agent fails by writing a short label instead of echoing the
# verbose upstream description, and difflib then finds too little shared
# sequence. Two consequences shaped these entries:
#
#   1. Untraceability is **base-relative, not a property of the string**. Those
#      same nine real strings score up to 0.548 against other businesses'
#      reasoning output, well above the 0.35 threshold, and on one base none of
#      them is untraceable at all. So the corpus cannot be validated globally;
#      _o5_issue selects per base and applicability reports a miss.
#   2. supervision._similar returns 1.0 on a substring match in either
#      direction, so an entry must not be a fragment of any real description.
#
# These six are short, operationally distant, and usable on all 20 bases, worst
# case 0.349 against a 0.35 threshold. The margin is thin because difflib on
# English prose has a narrow dynamic range — which is why selection is verified
# at injection time rather than assumed here.

CORPUS_ISSUES: tuple[str, ...] = (
    "till float count skipped",
    "gift card ledger unreconciled",
    "walk-in cooler telemetry gap",
    "POS firmware rounds tax early",
    "linen contract auto-renewed",
    "uniform size profile absent",
)

CORPUS_CAUSES: tuple[tuple[str, str], ...] = (
    ("covers per labour hour drift", "the forecasting model was never retrained after the refit"),
    ("void rate on split checks", "the terminal firmware rounds tax before applying the split"),
    ("uniform replacement spend", "no size profile is kept, so orders default to a fixed mix"),
)

CORPUS_RECS: tuple[tuple[str, str], ...] = (
    ("supplier invoice variance is unreviewed",
     "reconcile delivered weights against invoiced weights weekly"),
    ("no owner for the allergen matrix",
     "assign the allergen matrix to a named manager and review it quarterly"),
    ("table turn timing is not instrumented",
     "record seat and clear timestamps at the terminal for one month"),
)


# ── operator registry ─────────────────────────────────────────────────────────

STAGE: dict[str, str] = {
    "O1": "reasoning_agent", "O2": "reasoning_agent", "O3": "reasoning_agent",
    "O4": "reasoning_agent",
    "O5": "strategy_agent",
    "O6": "report_agent", "O7": "report_agent", "O8": "report_agent",
}

CHECK_CLASS: dict[str, str] = {
    "O1": "missing_evidence_id", "O2": "missing_evidence_id",
    "O3": "misaligned_aspect",
    "O4": "frequency_divergence",
    "O5": "untraceable_recommendation",
    "O6": "report_containment", "O7": "report_containment",
    "O8": "metadata_mismatch",
}

# "retry" operators produce a retry verdict and can carry the repair endpoint.
# See the module docstring for why O4 and O8 do not.
ENDPOINT: dict[str, str] = {op: "retry" for op in STAGE}
ENDPOINT["O4"] = "warn_level"
ENDPOINT["O8"] = "positive_control"

OUTPUT_KEY = {
    "reasoning_agent": "reasoning_output",
    "strategy_agent": "strategy_output",
    "report_agent": "report_output",
}

OPERATORS: tuple[str, ...] = tuple(sorted(STAGE))

# Operators whose defect the repair endpoint is defined on. The grid composition
# is a config choice, not a code change — flip an entry in ENDPOINT and this
# follows.
REPAIR_OPERATORS: tuple[str, ...] = tuple(op for op in OPERATORS if ENDPOINT[op] == "retry")


@dataclass
class Descriptor:
    """Ground truth for one injection: what was done, and what must fire.

    Consumed by the outcome scorer (B6), which must score the *replacement
    value* of the retried output rather than merely the disappearance of this
    descriptor's target (section 13.5).
    """

    operator: str
    stage: str
    check_class: str
    endpoint: str
    business_id: str | None
    seed: int
    applied: bool
    reason: str | None = None
    target: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


# ── helpers over a replay state ───────────────────────────────────────────────


def _rng(state: dict, op: str, seed: int) -> random.Random:
    return random.Random(f"{state.get('business_id')}:{op}:{seed}")


def _analysis_index(state: dict) -> dict[str, dict]:
    return {
        str(a.get("review_id")): a
        for a in (state.get("analysis_results") or [])
        if isinstance(a, dict)
    }


def _patterns(state: dict) -> list[dict]:
    return ((state.get("reasoning_output") or {}).get("patterns")) or []


def _resolving(pattern: dict, by_id: dict[str, dict]) -> list[str]:
    return [rid for rid in (pattern.get("evidence_review_ids") or []) if rid in by_id]


def _aspects_of(review: dict) -> set[str]:
    return {a.get("category") for a in (review.get("aspects") or [])}


def _trace_candidates(state: dict) -> list[str]:
    """Exactly the strings supervision._measure_strategy traces against."""
    reasoning = state.get("reasoning_output") or {}
    return (
        [rc.get("cause", "") for rc in reasoning.get("root_causes") or []]
        + [rc.get("pattern", "") for rc in reasoning.get("root_causes") or []]
        + [p.get("description", "") for p in reasoning.get("patterns") or []]
    )


def stage_is_clean(state: dict, stage: str) -> tuple[bool, str | None]:
    """Can this stage's recorded output serve as a Tier-2 injection base?

    Eligible means *no retry-level defect is already present*. A base that
    already trips a check would put a second problem into the A1 feedback text,
    which contaminates the arm manipulation: A1 is defined as feedback about the
    injected defect, not about that defect plus whatever else was wrong.

    ``proceed_with_warning`` stays eligible — a warn does not enter the retry
    feedback at all — but the caller is told, because such a base already
    carries a frequency divergence and is therefore not a clean base for O4.
    """
    if state.get(OUTPUT_KEY[stage]) is None:
        return False, "stage_absent"
    facts = supervision.measure(stage, state)
    verdict = supervision.decide(stage, facts, {}).verdict
    if verdict in ("retry", "halt"):
        fired = defect_bank.fired_classes(stage, facts)
        return False, f"base_not_clean:{','.join(fired) or verdict}"
    return True, ("base_warns" if verdict == "proceed_with_warning" else None)


# ── applicability ─────────────────────────────────────────────────────────────


def applicable(op: str, state: dict) -> tuple[bool, str | None]:
    """Whether ``op`` has something to corrupt in ``state``.

    Returns ``(False, reason)`` rather than raising, because an inapplicable
    operator is data the study reports (an injection success rate), not an
    error.
    """
    if op not in STAGE:
        raise ValueError(f"unknown operator {op!r}")

    stage = STAGE[op]
    clean, note = stage_is_clean(state, stage)
    if not clean:
        return False, note
    if op == "O4" and note == "base_warns":
        return False, "base_already_frequency_divergent"

    by_id = _analysis_index(state)
    patterns = _patterns(state)

    if op == "O1":
        if not any(_resolving(p, by_id) for p in patterns):
            return False, "no_resolving_evidence_id"
    elif op == "O2":
        if not patterns:
            return False, "no_patterns"
    elif op == "O3":
        if not any(_o3_target(p, by_id) for p in patterns):
            return False, "no_pattern_with_an_unmentioned_aspect"
    elif op == "O4":
        if not any(p.get("frequency") is not None for p in patterns):
            return False, "no_claimed_frequency"
    elif op == "O5":
        if not ((state.get("strategy_output") or {}).get("recommendations")):
            return False, "no_recommendations"
        if _o5_issue(state, random.Random(0)) is None:
            return False, "no_corpus_issue_below_trace_threshold"
    elif op in ("O6", "O7"):
        if not (state.get("report_output") or {}):
            return False, "no_report"
    elif op == "O8":
        report = state.get("report_output") or {}
        if "business_name" not in report and "sample_size" not in report:
            return False, "no_metadata_keys"

    return True, None


def _o3_target(pattern: dict, by_id: dict[str, dict]) -> str | None:
    """An aspect none of this pattern's resolving evidence mentions.

    ``_measure_reasoning`` only counts an evidence id as misaligned when the id
    resolves, so a pattern whose evidence is all missing cannot carry an O3
    defect — it would report as O1/O2 instead.
    """
    resolving = _resolving(pattern, by_id)
    if not resolving:
        return None
    mentioned: set[str] = set()
    for rid in resolving:
        mentioned |= _aspects_of(by_id[rid])
    for aspect in ASPECTS:
        if aspect != pattern.get("aspect") and aspect not in mentioned:
            return aspect
    return None


def _o5_issue(state: dict, rng: random.Random) -> str | None:
    """A corpus issue that traces to nothing in this state's reasoning output."""
    candidates = _trace_candidates(state)
    usable = [
        issue for issue in CORPUS_ISSUES
        if max((supervision._similar(issue, c) for c in candidates), default=0.0)
        < supervision.TRACE_SIMILARITY
    ]
    return rng.choice(sorted(usable)) if usable else None


def _fabricate_id(rng: random.Random, by_id: dict[str, dict]) -> str:
    for _ in range(64):
        rid = "".join(rng.choice(_ID_ALPHABET) for _ in range(_ID_LENGTH))
        if rid not in by_id:
            return rid
    raise RuntimeError("could not fabricate an unused review id")


# ── injection ─────────────────────────────────────────────────────────────────


SEVERITY_LEVELS: tuple[int, ...] = (1, 2)


def inject(op: str, state: dict, seed: int = 0, delta: float = 0.15,
           severity: int = 1) -> tuple[dict, Descriptor]:
    """Apply ``op`` to a copy of ``state``. Never mutates the caller's state.

    ``delta`` parameterises O4 as an **absolute** frequency divergence rather
    than the multiplier the plan first specified. On this corpus the median
    claimed frequency is 0.16, so a 1.1x multiplier moves it by 0.016 — under
    the 0.05 tolerance, producing no measurable defect in 81 of 89 patterns.
    Absolute divergence is the unit the check itself uses and is constructible
    for every pattern.

    ``severity`` exists for O1 only (PREREGISTRATION.md section 0.1 A6). Level 1
    is the frozen operator, byte for byte: the default path is untouched and
    its descriptor carries no new key. Level 2 applies level 1 and then, from
    the same random stream, drops one character from **every other resolving
    evidence id of the same pattern** -- so per-id damage is identical and only
    the extent varies, and level 2 always contains level 1's corruption.
    """
    if severity not in SEVERITY_LEVELS:
        raise ValueError(f"severity must be one of {SEVERITY_LEVELS}, got {severity!r}")
    if severity != 1 and op != "O1":
        raise ValueError(f"severity levels are defined for O1 only, not {op}")
    descriptor = Descriptor(
        operator=op,
        stage=STAGE[op],
        check_class=CHECK_CLASS[op],
        endpoint=ENDPOINT[op],
        business_id=state.get("business_id"),
        seed=seed,
        applied=False,
    )

    ok, reason = applicable(op, state)
    if not ok:
        descriptor.reason = reason
        return copy.deepcopy(state), descriptor

    out = copy.deepcopy(state)
    rng = _rng(state, op, seed)
    by_id = _analysis_index(out)
    handler = _HANDLERS[op]
    handler(out, by_id, rng, descriptor, delta)
    if severity == 2:
        _escalate_o1(out, by_id, rng, descriptor)
    descriptor.applied = True
    return out, descriptor


def _escalate_o1(out, by_id, rng, d):
    """O1 severity 2: every remaining resolving id of the pattern loses a char.

    Runs after ``_apply_o1`` on the same ``rng``, so level 1's draw is consumed
    first and reproduced exactly. A 21-character string cannot equal a real
    22-character id, so no corrupted id can resolve to a different review.
    """
    idx = d.target["pattern_index"]
    ids = _patterns(out)[idx]["evidence_review_ids"]
    also = []
    for j, rid in enumerate(ids):
        if rid not in by_id:
            continue  # level 1's id, or an id that never resolved
        drop = rng.randrange(len(rid))
        ids[j] = rid[:drop] + rid[drop + 1:]
        also.append({"evidence_index": j, "before": rid, "after": ids[j]})
    d.target["severity"] = 2
    d.target["also_corrupted"] = also


def _apply_o1(out, by_id, rng, d, _delta):
    patterns = _patterns(out)
    idx = rng.choice(sorted(i for i, p in enumerate(patterns) if _resolving(p, by_id)))
    ids = patterns[idx]["evidence_review_ids"]
    pos = ids.index(rng.choice(sorted(_resolving(patterns[idx], by_id))))
    before = ids[pos]
    drop = rng.randrange(len(before))
    after = before[:drop] + before[drop + 1:]
    ids[pos] = after
    d.target = {"pattern_index": idx, "evidence_index": pos, "before": before, "after": after}


def _apply_o2(out, by_id, rng, d, _delta):
    patterns = _patterns(out)
    idx = rng.randrange(len(patterns))
    fabricated = _fabricate_id(rng, by_id)
    patterns[idx].setdefault("evidence_review_ids", []).append(fabricated)
    d.target = {"pattern_index": idx, "added_evidence_id": fabricated}


def _apply_o3(out, by_id, rng, d, _delta):
    patterns = _patterns(out)
    choices = sorted(i for i, p in enumerate(patterns) if _o3_target(p, by_id))
    idx = rng.choice(choices)
    before = patterns[idx].get("aspect")
    after = _o3_target(patterns[idx], by_id)
    patterns[idx]["aspect"] = after
    d.target = {"pattern_index": idx, "before": before, "after": after}


def _apply_o4(out, by_id, rng, d, delta):
    facts = supervision.measure("reasoning_agent", out)
    patterns = _patterns(out)
    choices = sorted(i for i, p in enumerate(patterns) if p.get("frequency") is not None)
    idx = rng.choice(choices)
    recomputed = facts["patterns"][idx]["recomputed_frequency"]
    before = patterns[idx]["frequency"]
    # The contract caps frequency at 1.0, so a divergence that would overflow is
    # placed below the recomputed value instead of above it. Same magnitude,
    # same check, no clamping that would silently weaken the manipulation.
    after = recomputed + delta if recomputed + delta <= 1.0 else max(0.0, recomputed - delta)
    patterns[idx]["frequency"] = round(after, 3)
    d.target = {
        "pattern_index": idx, "before": before, "after": round(after, 3),
        "recomputed": recomputed, "delta": round(abs(after - recomputed), 3),
    }


def _apply_o5(out, _by_id, rng, d, _delta):
    recs = out["strategy_output"]["recommendations"]
    idx = rng.randrange(len(recs))
    issue = _o5_issue(out, rng)
    before = recs[idx].get("issue")
    recs[idx]["issue"] = issue
    d.target = {"recommendation_index": idx, "before": before, "after": issue}


def _apply_o6(out, _by_id, rng, d, _delta):
    report = out["report_output"]
    upstream = (out.get("reasoning_output") or {}).get("root_causes") or []
    used = {(u.get("cause"), u.get("pattern")) for u in upstream}
    pool = [c for c in CORPUS_CAUSES if (c[1], c[0]) not in used]
    pattern, cause = rng.choice(sorted(pool))
    entry = {"pattern": pattern, "cause": cause, "confidence": "medium"}
    report.setdefault("root_causes", []).append(entry)
    d.target = {"inserted_root_cause": entry, "index": len(report["root_causes"]) - 1}


def _apply_o7(out, _by_id, rng, d, _delta):
    report = out["report_output"]
    upstream = (out.get("strategy_output") or {}).get("recommendations") or []
    used = {(u.get("issue"), u.get("action")) for u in upstream}
    pool = [r for r in CORPUS_RECS if r not in used]
    issue, action = rng.choice(sorted(pool))
    entry = {
        "priority": len(report.get("recommendations") or []) + 1,
        "issue": issue, "action": action,
        "category": "operations", "expected_impact": "unquantified",
    }
    report.setdefault("recommendations", []).append(entry)
    d.target = {"inserted_recommendation": entry, "index": len(report["recommendations"]) - 1}


def _apply_o8(out, _by_id, rng, d, _delta):
    report = out["report_output"]
    if "business_name" in report:
        before = report["business_name"]
        report["business_name"] = f"{before} Express"
        d.target = {"field": "business_name", "before": before, "after": report["business_name"]}
    else:
        before = report.get("sample_size")
        report["sample_size"] = (before or 0) + 7
        d.target = {"field": "sample_size", "before": before, "after": report["sample_size"]}


_HANDLERS = {
    "O1": _apply_o1, "O2": _apply_o2, "O3": _apply_o3, "O4": _apply_o4,
    "O5": _apply_o5, "O6": _apply_o6, "O7": _apply_o7, "O8": _apply_o8,
}


# ── verification: did the injected defect trip the check it claims? ───────────


def verify_injection(op: str, injected: dict, base: dict) -> tuple[bool, dict]:
    """Independent confirmation that the descriptor tells the truth.

    The operator says which check class it targets; ``supervision.measure`` says
    which classes actually fire. This compares them, and also checks that no
    *additional* retry-level class appeared that was not already present in the
    base — an operator that trips two checks cannot be attributed to one.
    """
    stage = STAGE[op]
    before = set(defect_bank.fired_classes(stage, supervision.measure(stage, base)))
    facts = supervision.measure(stage, injected)
    after = set(defect_bank.fired_classes(stage, facts))

    if CHECK_CLASS[op] == "frequency_divergence":
        fired = defect_bank.frequency_divergent(facts, supervision.FREQUENCY_TOLERANCE)
        collateral = sorted(after - before)
    else:
        fired = CHECK_CLASS[op] in after
        collateral = sorted(after - before - {CHECK_CLASS[op]})

    return (fired and not collateral), {
        "target_fired": fired,
        "collateral_classes": collateral,
        "classes_before": sorted(before),
        "classes_after": sorted(after),
        "verdict": supervision.decide(stage, facts, {}).verdict,
    }


# ── applicability matrix (sets the Tier-2 ceiling) ────────────────────────────


def state_from_dump(dump_dir: str) -> dict:
    """The parts of PipelineState supervision reads. Mirrors replay_stage."""
    dump = load_dump(dump_dir)
    return {
        "business_id": dump.summary.get("business_id"),
        "business_name": dump.summary.get("business_name"),
        "analysis_results": dump.analysis,
        "reasoning_output": dump.reasoning,
        "strategy_output": dump.strategy,
        "report_output": dump.report,
    }


def base_dirs(root: str) -> list[str]:
    """Phase-A dump directories, which are the Tier-2 injection bases.

    Phase A ran in observe mode, so each stage executed exactly once and the
    output on disk is the one that was measured. An enforce-mode dump would hold
    a post-retry, frequency-corrected output and is not a comparable base.
    """
    phase_a = os.path.join(root, "A")
    if not os.path.isdir(phase_a):
        return []
    return [
        os.path.join(phase_a, d)
        for d in sorted(os.listdir(phase_a))
        if os.path.isdir(os.path.join(phase_a, d))
    ]


def matrix(root: str, seed: int = 0) -> dict:
    """Per-operator applicable-base counts over a study root.

    This is the number the plan calls the Tier-2 ceiling. It is computed, not
    multiplied by hand: ``8 operators x 20 dumps = 160`` assumed every operator
    can use every dump, which is false in both directions — operators are
    stage-specific, and stages differ in how many bases are clean.
    """
    dirs = base_dirs(root)
    per_op: dict[str, dict] = {}

    for op in OPERATORS:
        applied: list[str] = []
        reasons: dict[str, int] = {}
        for dump_dir in dirs:
            state = state_from_dump(dump_dir)
            ok, reason = applicable(op, state)
            if ok:
                applied.append(os.path.basename(dump_dir))
            else:
                reasons[reason or "unknown"] = reasons.get(reason or "unknown", 0) + 1
        per_op[op] = {
            "stage": STAGE[op],
            "check_class": CHECK_CLASS[op],
            "endpoint": ENDPOINT[op],
            "applicable": len(applied),
            "inapplicable_reasons": reasons,
            "bases": applied,
        }

    repair_total = sum(per_op[op]["applicable"] for op in REPAIR_OPERATORS)
    return {
        "root": root,
        "n_dumps": len(dirs),
        "seed": seed,
        "operators": per_op,
        "summary": {
            "all_operators": sum(v["applicable"] for v in per_op.values()),
            "repair_operators": repair_total,
            "repair_operator_ids": list(REPAIR_OPERATORS),
            "excluded_operators": {
                op: ENDPOINT[op] for op in OPERATORS if ENDPOINT[op] != "retry"
            },
            "yield_per_dump": round(repair_total / len(dirs), 2) if dirs else 0.0,
        },
    }


def report_matrix(m: dict) -> None:
    s = m["summary"]
    print(f"Tier-2 injection bases: {m['n_dumps']} Phase-A dumps under {m['root']}\n")
    print(f"{'op':<4} {'stage':<16} {'endpoint':<17} {'n':>4}   inapplicable")
    print("-" * 78)
    for op, v in sorted(m["operators"].items()):
        print(f"{op:<4} {v['stage']:<16} {v['endpoint']:<17} {v['applicable']:>4}   "
              f"{v['inapplicable_reasons'] or ''}")
    print("-" * 78)
    print(f"{'all 8 operators':<44} {s['all_operators']:>4}")
    print(f"{'repair endpoint only ' + str(s['repair_operator_ids']):<44} "
          f"{s['repair_operators']:>4}   <- Tier-2 ceiling")
    print(f"\nExcluded from the repair grid: {s['excluded_operators']}")
    print(f"Yield per dump (repair operators): {s['yield_per_dump']}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default="out_study")
    ap.add_argument("--matrix", action="store_true", help="print the applicability matrix")
    ap.add_argument("--out", default=None, help="write the matrix as JSON here")
    ap.add_argument("--dump-dir", help="inject into a single dump and print the result")
    ap.add_argument("--op", choices=list(OPERATORS))
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    if args.dump_dir:
        if not args.op:
            ap.error("--dump-dir needs --op")
        base = state_from_dump(args.dump_dir)
        injected, descriptor = inject(args.op, base, args.seed)
        ok, detail = verify_injection(args.op, injected, base)
        print(json.dumps(
            {"descriptor": descriptor.to_dict(), "verified": ok, "detail": detail},
            indent=2, ensure_ascii=False,
        ))
        return 0 if (descriptor.applied and ok) else 1

    if not os.path.isdir(args.root):
        print(f"No study root at {args.root!r}.")
        return 1

    m = matrix(args.root, args.seed)
    report_matrix(m)
    if args.out:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump(m, fh, indent=2, ensure_ascii=False)
        print(f"\nWrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
