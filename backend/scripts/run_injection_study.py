"""Batch runner for the injected-defect repair study (JOURNAL_PLAN B7).

Clones ``run_study.py``: JSONL checkpoint with fsync, resume-by-skip,
``--dry-run``, backoff on 429/503, and the ``status_error`` exclusion carried
over verbatim (an API failure is not a defect the retry could repair).

Four requirements here are not stylistic, and each has a reason recorded in the
plan.

**Iteration order is ``for defect: for arm: for repetition:``.** Never
arm-outer. All arms for one defect must execute contiguously in one session, or
the matched pairing is confounded with serving epoch (section 14.1). Checkpoint
granularity is therefore the *defect*, not the trial: resuming mid-defect would
split its arms across two sessions and silently destroy the matching.

**``attempts_made`` is logged per trial.** ``BaseAgent._run_with_retry`` reacts
to a JSON/schema failure by appending the model's own invalid output as an
**assistant** turn plus a correction prompt. That converts the trial to a
P2-like condition mid-flight, contaminating exactly the placement manipulation
D9 measures — and it means a trial is 1-3 LLM calls, not 1. Analysis must
stratify or exclude on it; it cannot do either if it is not recorded.

**Pre and post facts are logged for every check, not only the injected one**
(section 14.6). Free, because ``measure()`` has no rule precedence and returns
the whole measurement. It is what lets a fifth outcome (a defect the four
classes cannot represent) be seen at all.

**D12 — downstream propagation is in scope, so the full retried stage output is
persisted along with enough state to re-run the downstream stages later.** Not
just facts and a verdict. Nearly free on this pass; recovering it afterwards
means re-running every trial.

Run (from backend/, venv active):

    python scripts/run_injection_study.py --dry-run          # no API key needed
    python scripts/run_injection_study.py --root out_study --out out_study/T2
    python scripts/run_injection_study.py --cell c1    # the D8 cell, own pass (prereg 0.1 A3)
    python scripts/run_injection_study.py --cell d19   # the overwrite counterfactual (0.1 A2)
    python scripts/run_injection_study.py --cell placement  # A1 x {P0..P3} (0.1 A5)
    python scripts/run_injection_study.py --cell severity   # O1 at two levels (0.1 A6)
    python scripts/run_injection_study.py --cell warm       # temperature 1.0 (0.1 A7)

``--c1`` (C1 appended to every core defect) predates the core run and is kept
for the record; after the core ran it would re-run all 1,167 core trials, so
the cell runs as ``--cell c1`` instead.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
import time
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from app.core import supervision  # noqa: E402


def _load_by_path(name: str, relative: str):
    here = os.path.dirname(os.path.abspath(__file__))
    spec = importlib.util.spec_from_file_location(name, os.path.join(here, relative))
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


inject_defects = _load_by_path("inject_defects", "inject_defects.py")
arms_mod = _load_by_path("arms", "arms.py")
score_repair = _load_by_path("score_repair", "analysis/score_repair.py")

# D4c: allocate by contrast difficulty. A2-vs-A3 (28 pp) is already at 0.996
# with five businesses, so equal allocation overspends on the easy contrast.
#
# ⚠ The allocation is over **defects**, not over repetitions. "A1 and A2 at the
# full set, A3 at a quarter, A0 at a half" means A3 runs on a quarter of the
# defects with full repetitions — not on every defect with fewer. Both spend the
# same budget; only the first keeps each arm's blocks intact, which is what the
# matched analysis needs.
ARM_FRACTION = {"A1": 1.0, "A2": 1.0, "A3": 0.25, "A0": 0.5}

# D8/D8d: the constraint-completeness cell. C1 is the stage prompt with the
# supervisor's obligations stated up front (arms.C1_CONSTRAINTS); C0 is the
# production prompt, which is what every core trial runs. Three properties,
# each decided rather than convenient:
#
#   - **{A1, A2} only** (D8d). The cell exists to ask whether the A1-vs-A2 gap
#     survives constraint disclosure, so it needs those two arms and no more.
#   - **The same defect, the same injected base, the same session** (D8b
#     option (ii)). The C1 cells are appended to the defect's own block rather
#     than run as a second pass, so C0-vs-C1 is matched within a defect exactly
#     as arm-vs-arm is. Regenerating the base under C1 would confound the
#     difference-in-differences with C1 having made the clean output cleaner.
#   - **A fraction over defects, on the same stride as ARM_FRACTION**, so
#     growing the bank never reshuffles which defects already carry it.
#
# The fraction is written as the D8d count over the pre-registered N so the
# arithmetic stays visible. ⚠ It realises **37 defects, not 40**: the stride is
# applied per operator, and six independent floors lose three defects between
# them. Stratifying is worth more than the round number -- a C1 subset that fell
# in a block would confound the condition with operator, which is the one thing
# a 6-defect gain could not buy back -- so the shortfall is reported rather than
# tuned away. 37 x {A1,A2} x r=3 = **222 trials**, inside D8d's "~240".
# ⚠ Off by default (``--c1``). The frozen core is 1,167 C0 trials and the
# runner must keep producing exactly that unless the cell is asked for; C1 is
# a post-freeze addition and is exploratory (PREREGISTRATION.md §0.1).
C1_DEFECTS = 40           # D8d, against the pre-registered N below
C1_N_AT_FREEZE = 142      # PREREGISTRATION.md §6 — the N the fraction is set at
C1_FRACTION = C1_DEFECTS / C1_N_AT_FREEZE
C1_ARMS = ("A1", "A2")

DEFAULT_REPS = 3          # D4d: r=3 if 0.80 power is the target
DEFAULT_PLACEMENT = "P1"  # D10: the Tier-2 core runs at P1, not the production P0

# The passes the runner can make, each into its own checkpoint. ``core`` is the
# frozen 1,167-trial plan; the other two were added after it ran (2026-10-07).
#
#   c1  -- PREREGISTRATION.md 0.1 A3. The D8 cell as a pass of its own, on the
#          same 37 defects ``--c1`` selects. Each carries {A1, A2} under C0 *and*
#          C1, so C0-vs-C1 is matched within one session (14.1) instead of
#          against core trials run days earlier. The re-run C0 cells double as
#          a measurement of serving drift against the core.
#   d19 -- 7 and 0.1 A2. O4 x {A1 at P1, A3 at P0}, r = 3, every applicable
#          defect. O4 resolves to ``proceed_with_warning`` in production and is
#          overwritten, never retried; this pass routes it to retry on purpose,
#          outside the production path, to measure what the overwrite bought.
#   placement -- 0.1 A5. A1 x {P0, P1, P2, P3}, r = 3, on a third of the
#          defects (per-operator stride, as the plan sized it). P1 is re-run in
#          the same session as the other three for the reason c1 re-runs C0.
#   severity  -- 0.1 A6. O1 at level 1 (the frozen operator) and level 2 (every
#          resolving id of the targeted pattern corrupted), A1 at P1, r = 3,
#          all O1 defects. Both levels in one session per defect.
#   warm      -- 0.1 A7 (plan D2's warm-resample subset). On the placement
#          subset: A1@P1 and A2@P1 at temperature 0 (in-session comparators)
#          and at WARM_TEMPERATURE, plus A3@P0 at WARM_TEMPERATURE, r = 3.
CELLS = ("core", "c1", "d19", "placement", "severity", "warm", "c7", "thinking")
CELL_OUT = {"core": "out_study/T2", "c1": "out_study/T2C1", "d19": "out_study/T2D19",
            "placement": "out_study/T2P", "severity": "out_study/T2S",
            "warm": "out_study/T2W", "c7": "out_study/T2L", "thinking": "out_study/T2T"}
C7_REPS = 3  # A11: G2 returned 8/10 identical; determinism is measured, not assumed
# D2 cites Tyen section 4(d), which needed temperature 1 to force a different
# step; it is also the provider's default sampling temperature.
WARM_TEMPERATURE = 1.0
WARM_CELLS = (("A1", "P1", (0.0, WARM_TEMPERATURE)),
              ("A2", "P1", (0.0, WARM_TEMPERATURE)),
              ("A3", "P0", (WARM_TEMPERATURE,)))
D19_OPERATORS = ("O4",)
D19_CELLS = (("A1", DEFAULT_PLACEMENT), ("A3", "P0"))
PLACEMENT_FRACTION = 1 / 3
PLACEMENT_LEVELS = ("P0", "P1", "P2", "P3")
SEVERITY_OPERATORS = ("O1",)
# Amendment A12 pinned thinking sweep on primary model
THINKING_MODEL = "gemini-2.5-flash"
THINKING_EFFORTS = ("none", "low", "medium", "high")
THINKING_BUDGETS = {"none": 0, "low": 1024, "medium": 8192, "high": 24576}
# Arms the order check requires each pass's defects to hold.
REQUIRED_ARMS = {"d19": ("A1", "A3"), "placement": ("A1",), "severity": ("A1",),
                 "warm": ("A1", "A2", "A3"), "thinking": ("A1", "A2")}


# ── checkpointing ─────────────────────────────────────────────────────────────


def checkpoint_path(out_dir: str) -> str:
    return os.path.join(out_dir, "checkpoint.jsonl")


def load_done(path: str) -> set[str]:
    """Defect ids already completed. Resume skips whole defects, never trials."""
    done: set[str] = set()
    if not os.path.exists(path):
        return done
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue  # tolerate a torn final line from a hard kill
            if row.get("defect_id") and row.get("status") in ("ok", "skipped"):
                done.add(row["defect_id"])
    return done


def append_row(path: str, row: dict) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")
        fh.flush()
        os.fsync(fh.fileno())  # survive a kill between defects


# ── the trial plan ────────────────────────────────────────────────────────────


def _in_subset(index: int, fraction: float) -> bool:
    """Evenly spread deterministic selection of a fraction of defects.

    Stride rather than a seeded shuffle: adding a defect later must not
    reshuffle which existing ones carry the reduced arms, or a resumed run and a
    fresh run would disagree about what has already been done.
    """
    if fraction >= 1.0:
        return True
    return int((index + 1) * fraction) > int(index * fraction)


def _cells_for(index: int, reps: int, placement: str,
               with_c1: bool = False) -> list[dict]:
    """Arm x condition x repetition cells for one defect, in execution order.

    A3 is a determinism floor at P0 by construction; A0 cannot run at P0 at all
    (D9b). Enforced here rather than special-cased in the loop.

    The C1 cells come last, as a block, so a defect that does not carry them
    produces a byte-identical cell list to the one the frozen core planned.
    """
    cells: list[dict] = []
    for arm in ("A0", "A1", "A2", "A3"):
        if not _in_subset(index, ARM_FRACTION[arm]):
            continue
        arm_placement = "P0" if arm == "A3" else placement
        if not arms_mod.is_defined(arm, arm_placement):
            continue
        cells.extend({"arm": arm, "placement": arm_placement,
                      "condition": "C0", "rep": r}
                     for r in range(reps))
    if with_c1 and _in_subset(index, C1_FRACTION):
        for arm in C1_ARMS:
            cells.extend({"arm": arm, "placement": placement,
                          "condition": "C1", "rep": r}
                         for r in range(reps))
    return cells


def _c1_cells(index: int, reps: int, placement: str) -> list[dict]:
    """The C1 pass: {A1, A2} under C0 then C1, on the ``--c1`` stride, else none."""
    if not _in_subset(index, C1_FRACTION):
        return []
    return [{"arm": arm, "placement": placement, "condition": condition, "rep": r}
            for condition in ("C0", "C1") for arm in C1_ARMS for r in range(reps)]


def _d19_cells(reps: int) -> list[dict]:
    """The D19 pass: A1 at the Tier-2 placement, A3 at P0 -- the only one it has."""
    return [{"arm": arm, "placement": placement, "condition": "C0", "rep": r}
            for arm, placement in D19_CELLS for r in range(reps)]


def _placement_cells(index: int, reps: int) -> list[dict]:
    """The placement pass: A1 at every level, on the one-third stride, else none."""
    if not _in_subset(index, PLACEMENT_FRACTION):
        return []
    return [{"arm": "A1", "placement": level, "condition": "C0", "rep": r}
            for level in PLACEMENT_LEVELS for r in range(reps)]


def _severity_cells(reps: int, placement: str) -> list[dict]:
    """The severity pass: A1 at the Tier-2 placement, both O1 levels."""
    return [{"arm": "A1", "placement": placement, "condition": "C0", "rep": r,
             "severity": level}
            for level in inject_defects.SEVERITY_LEVELS for r in range(reps)]


def _warm_cells(index: int, reps: int) -> list[dict]:
    """The warm pass: arm-major, each arm's temperatures contiguous, else none."""
    if not _in_subset(index, PLACEMENT_FRACTION):
        return []
    return [{"arm": arm, "placement": placement, "condition": "C0", "rep": r,
             "temperature": temp}
            for arm, placement, temps in WARM_CELLS for temp in temps for r in range(reps)]


def _c7_cells(index: int) -> list[dict]:
    """A11: three draws per arm; A3 on the unchanged frozen core stride."""
    cells = [{"arm": arm, "placement": "P1", "condition": "C0", "rep": r}
             for arm in ("A1", "A2") for r in range(C7_REPS)]
    if _in_subset(index, ARM_FRACTION["A3"]):
        cells.extend({"arm": "A3", "placement": "P0", "condition": "C0", "rep": r}
                     for r in range(C7_REPS))
    return cells


def _thinking_cells(index: int, reps: int = DEFAULT_REPS) -> list[dict]:
    """A12: within-weights thinking-budget sweep on 45-defect subset (1/3 per operator).

    A1, A2 at P1 on all 45 defects; A3 at P0 on 1/3 of the subset (14 defects).
    Each arm runs across all four reasoning_efforts ('none', 'low', 'medium', 'high').
    """
    if not _in_subset(index, PLACEMENT_FRACTION):
        return []
    subset_index = int((index + 1) * PLACEMENT_FRACTION) - 1
    arm_specs = [("A1", "P1"), ("A2", "P1")]
    if _in_subset(subset_index, PLACEMENT_FRACTION):
        arm_specs.append(("A3", "P0"))
    return [
        {"arm": arm, "placement": placement, "condition": "C0", "rep": r,
         "reasoning_effort": effort}
        for arm, placement in arm_specs
        for effort in THINKING_EFFORTS
        for r in range(reps)
    ]


def not_in_pass(entry: dict) -> bool:
    """Cleared every gate but this pass's subset does not carry it."""
    reason = entry.get("reason") or ""
    return reason.startswith("not_in_") and reason.endswith("_subset")


def d19_decision(decision):
    """Route O4's warn-level measurement to a retry, for the D19 pass only.

    Production resolves frequency divergence with ``proceed_with_warning`` and
    overwrites the value; ``retry_feedback`` is None, so A1 would have nothing
    to carry. The measured facts already exist as the decision's
    ``frequency_corrected:{aspect}:{claimed}->{recomputed}`` flags, so A1
    receives exactly those, joined the way production joins retry problems
    (`` | ``) and wrapped by the unchanged production template. No new wording
    is authored (PREREGISTRATION.md section 7). Production's own ``decide`` is
    not touched; this function exists only in the runner.
    """
    flags = [f for f in decision.flags if f.startswith("frequency_corrected:")]
    if not flags:
        return decision
    return supervision.Decision("retry", list(decision.flags), " | ".join(flags))


def build_plan(root: str, reps: int = DEFAULT_REPS, placement: str = DEFAULT_PLACEMENT,
               seed: int = 0, operators: tuple[str, ...] | None = None,
               with_c1: bool = False, cell: str = "core",
               c7_gates: dict | None = None) -> list[dict]:
    """Every defect to run, in execution order, with its arms attached.

    One entry per (base, operator) — that is one *defect*. Its arms and their
    repetitions are nested inside so the runner cannot accidentally reorder
    them.

    **D20 — three gates, in order, all before any money is spent.** They run
    here rather than in ``run()`` deliberately: every one of them is pure
    ``measure()``/``decide()`` at zero API cost, so a defect that fails must
    disappear from the plan *before* trials execute and must be visible in
    ``--plan-only``. Checking them at execution time would mean discovering a
    dead defect after paying for its arms.

    1. **applicable** — the operator has something to corrupt (structural).
    2. **injection validity** — the injected defect trips the check the
       descriptor claims, and trips *no other* retry-level check. An operator
       that fires two classes cannot be attributed to one.
    3. **trigger** — the supervisor routes the measured state to ``retry``. A
       defect the supervisor flags but does not route yields no arm contrast
       at all: every arm would be the same non-event.

    Each gate has its own denominator (``plan_summary``), which is what settles
    section 14.3: an untriggered defect is *excluded and counted*, never scored
    ``unrepaired`` — scoring it would score the arms on a trial where the arms
    are identical by construction.
    """
    if cell not in CELLS:
        raise ValueError(f"unknown cell {cell!r}; expected one of {CELLS}")
    if cell != "core" and with_c1:
        raise ValueError("--c1 extends the core plan; the c1 and d19 passes are separate")
    operators = operators or {"d19": D19_OPERATORS, "severity": SEVERITY_OPERATORS}.get(
        cell, inject_defects.REPAIR_OPERATORS)
    # D19 inverts the trigger gate: O4 must reach the warn-level verdict that
    # production overwrites, and must not already be routed to retry.
    expected_verdict = "proceed_with_warning" if cell == "d19" else "retry"
    plan: list[dict] = []
    # Per-operator counter so the arm subsets are stratified by operator rather
    # than falling in a block wherever one operator happens to sit in the order.
    # It advances only for defects that clear every gate: a gated-out defect
    # carries no arms, so counting it would put a hole in the A0/A3 stride.
    op_index: dict[str, int] = {op: 0 for op in operators}

    for dump_dir in inject_defects.base_dirs(root):
        state = inject_defects.state_from_dump(dump_dir)
        for op in operators:
            entry = {
                "defect_id": f"{os.path.basename(dump_dir)}:{op}",
                "dump_dir": dump_dir.replace("\\", "/"),
                "operator": op, "seed": seed,
                "applicable": False, "injection_valid": None, "triggers": None,
                "runnable": False, "reason": None, "gate": None, "arms": [],
                "cell": cell,
            }

            ok, reason = inject_defects.applicable(op, state)
            if not ok:
                entry["reason"] = reason
                plan.append(entry)
                continue
            entry["applicable"] = True

            # Deterministic in (state, op, seed), so re-deriving the same
            # injection inside run() reproduces exactly what was gated here.
            injected, descriptor = inject_defects.inject(op, state, seed=seed)
            if not descriptor.applied:
                entry["reason"] = descriptor.reason or "injection_not_applied"
                plan.append(entry)
                continue

            valid, detail = inject_defects.verify_injection(op, injected, state)
            entry["gate"] = detail
            entry["injection_valid"] = valid
            if not valid:
                entry["reason"] = (
                    "injection_did_not_fire" if not detail["target_fired"]
                    else "injection_collateral:" + ",".join(detail["collateral_classes"])
                )
                plan.append(entry)
                continue

            entry["triggers"] = detail["verdict"] == expected_verdict
            if not entry["triggers"]:
                kind = "warning" if cell == "d19" else "retry"
                entry["reason"] = f"no_{kind}_verdict:{detail['verdict']}"
                plan.append(entry)
                continue

            if cell == "severity":
                # Level 2 must clear the same two gates, or the levels would not
                # be comparable defect for defect. Both levels or neither.
                inj2, _ = inject_defects.inject(op, state, seed=seed, severity=2)
                valid2, detail2 = inject_defects.verify_injection(op, inj2, state)
                entry["gate_severity2"] = detail2
                if not (valid2 and detail2["verdict"] == "retry"):
                    entry["reason"] = f"severity2_gate:{detail2['verdict']}"
                    plan.append(entry)
                    continue

            if cell == "c1":
                arms = _c1_cells(op_index[op], reps, placement)
            elif cell == "d19":
                arms = _d19_cells(reps)
            elif cell == "placement":
                arms = _placement_cells(op_index[op], reps)
            elif cell == "severity":
                arms = _severity_cells(reps, placement)
            elif cell == "warm":
                arms = _warm_cells(op_index[op], reps)
            elif cell == "c7":
                arms = _c7_cells(op_index[op])
            elif cell == "thinking":
                arms = _thinking_cells(op_index[op], reps)
            else:
                arms = _cells_for(op_index[op], reps, placement, with_c1)
            op_index[op] += 1
            if not arms:
                # Cleared every gate, but this pass's subset does not carry it.
                # Not runnable here; the stride above still counted it.
                entry["reason"] = f"not_in_{cell}_subset"
                plan.append(entry)
                continue
            entry["runnable"] = True
            entry["arms"] = arms
            if cell == "c7" and c7_gates is not None:
                context = c7_gates["context"]["defects"].get(entry["defect_id"])
                if context is None:
                    raise ValueError(f"C7 context gate missing {entry['defect_id']}")
                if not context["eligible"]:
                    entry.update(runnable=False, arms=[], reason="c7_context_overflow")
            plan.append(entry)
    return plan


def plan_summary(plan: list[dict]) -> dict:
    """Counts for every gate, each against its own denominator (D20).

    ``injection_success_rate`` is over the *applicable* defects; ``trigger_rate``
    is over the ones whose injection verified. Reporting one pooled "yield"
    would hide which of the two moved.

    ``core_trials`` is the C0 count and is reported separately from ``trials``
    for the same reason: the pre-registration froze a 1,167-trial core, and a
    single total that silently absorbed the C1 cell would stop anyone checking
    the plan against it.
    """
    applicable = [d for d in plan if d.get("applicable")]
    verified = [d for d in applicable if d.get("injection_valid")]
    triggered = [d for d in verified if d.get("triggers")]
    runnable = [d for d in plan if d.get("runnable")]
    by_arm: dict[str, int] = {}
    by_condition: dict[str, int] = {}
    by_cell: dict[str, int] = {}
    by_placement: dict[str, int] = {}
    by_severity: dict[str, int] = {}
    by_temperature: dict[str, int] = {}
    by_effort: dict[str, int] = {}
    c1_defects = 0
    for d in runnable:
        if any(c.get("condition", "C0") == "C1" for c in d["arms"]):
            c1_defects += 1
        for cell in d["arms"]:
            condition = cell.get("condition", "C0")
            by_arm[cell["arm"]] = by_arm.get(cell["arm"], 0) + 1
            by_condition[condition] = by_condition.get(condition, 0) + 1
            key = f"{condition}:{cell['arm']}"
            by_cell[key] = by_cell.get(key, 0) + 1
            by_placement[cell["placement"]] = by_placement.get(cell["placement"], 0) + 1
            level = str(cell.get("severity", 1))
            by_severity[level] = by_severity.get(level, 0) + 1
            temp = str(cell.get("temperature", 0.0))
            by_temperature[temp] = by_temperature.get(temp, 0) + 1
            effort = str(cell.get("reasoning_effort") or "default")
            by_effort[effort] = by_effort.get(effort, 0) + 1

    def _rate(num: int, den: int) -> float | None:
        return round(num / den, 4) if den else None

    return {
        "defects_planned": len(plan),
        "defects_applicable": len(applicable),
        "defects_inapplicable": len(plan) - len(applicable),
        "injection_verified": len(verified),
        "injection_failed": len(applicable) - len(verified),
        "injection_success_rate": _rate(len(verified), len(applicable)),
        "triggered": len(triggered),
        "untriggered": len(verified) - len(triggered),
        "trigger_rate": _rate(len(triggered), len(verified)),
        # Cleared every gate but not carried by this pass (the c1 subset).
        "not_in_pass": len(triggered) - len(runnable),
        "c7_context_excluded": sum(d.get("reason") == "c7_context_overflow" for d in plan),
        "defects_runnable": len(runnable),
        "trials": sum(len(d["arms"]) for d in runnable),
        "trials_by_arm": by_arm,
        "trials_by_condition": by_condition,
        "trials_by_cell": by_cell,
        "trials_by_placement": by_placement,
        "trials_by_severity": by_severity,
        "trials_by_temperature": by_temperature,
        "trials_by_reasoning_effort": by_effort,
        "core_trials": by_condition.get("C0", 0),
        "c1_trials": by_condition.get("C1", 0),
        "defects_c1": c1_defects,
        "operators": sorted({d["operator"] for d in runnable}),
    }


def verify_order(plan: list[dict]) -> list[str]:
    """The 14.1 invariant, checkable without running anything.

    Within a defect, every arm's repetitions must be contiguous, and the defect
    must hold all of its arms. If the loop is ever rewritten arm-outer, this is
    what says so.

    Contiguity is keyed on **(condition, arm)**, not on arm alone: the C1 cell
    re-runs A1 and A2 under a different prompt, so arm alone would read a
    correctly ordered C1 block as an arm-outer rewrite. The invariant it
    protects is unchanged — one block per cell, all of them in one session.
    """
    problems = []
    for d in plan:
        # Keyed on runnable, not applicable: a defect the D20 gates removed
        # carries no arms by design, and must not be reported as missing one.
        if not d.get("runnable", d.get("applicable")):
            continue
        seen: list[tuple[str, str]] = []
        for cell in d["arms"]:
            key = (cell.get("condition", "C0"), cell["arm"])
            if not seen or seen[-1] != key:
                if key in seen:
                    problems.append(
                        f"{d['defect_id']}: arm {key[1]} under {key[0]} is not contiguous")
                seen.append(key)
        # A0 and A3 run on subsets by design (D4c); the primary contrast does not.
        core = [arm for condition, arm in seen if condition == "C0"]
        needed = REQUIRED_ARMS.get(d.get("cell"), ("A1", "A2"))
        if any(arm not in core for arm in needed):
            problems.append(f"{d['defect_id']}: missing a primary arm ({core})")
        # The two factor passes are useless half-populated: a defect missing a
        # level contributes no within-defect contrast for it.
        if d.get("cell") == "placement":
            levels = {c["placement"] for c in d["arms"]}
            if levels != set(PLACEMENT_LEVELS):
                problems.append(f"{d['defect_id']}: placement levels {sorted(levels)}")
        if d.get("cell") == "severity":
            levels = {c.get("severity", 1) for c in d["arms"]}
            if levels != set(inject_defects.SEVERITY_LEVELS):
                problems.append(f"{d['defect_id']}: severity levels {sorted(levels)}")
        if d.get("cell") == "warm":
            for arm, _placement, temps in WARM_CELLS:
                got = {c.get("temperature", 0.0) for c in d["arms"] if c["arm"] == arm}
                if got != set(temps):
                    problems.append(f"{d['defect_id']}: {arm} temperatures {sorted(got)}")
        if d.get("cell") == "thinking":
            for arm in {c["arm"] for c in d["arms"]}:
                efforts = {c.get("reasoning_effort") for c in d["arms"] if c["arm"] == arm}
                if efforts != set(THINKING_EFFORTS):
                    problems.append(
                        f"{d['defect_id']}: arm {arm} reasoning efforts {sorted(str(e) for e in efforts)}")
        # A half-populated C1 cell yields no C0-vs-C1 contrast for this defect,
        # which is the one thing the cell exists to produce (D8d).
        c1 = [arm for condition, arm in seen if condition == "C1"]
        if c1 and set(c1) != set(C1_ARMS):
            problems.append(
                f"{d['defect_id']}: the C1 cell is not {'/'.join(C1_ARMS)} ({c1})")
    return problems


# ── one trial ─────────────────────────────────────────────────────────────────


def run_trial(defect: dict, cell: dict, base_state: dict, injected_state: dict,
              descriptor, session_id: str, dry_run: bool) -> dict:
    """Execute one (defect, arm, repetition) trial.

    In ``--dry-run`` nothing is imported that needs an API key and no call is
    made; the row records the cell so the plan can be inspected end to end.
    """
    stage = descriptor.stage
    pre_facts = supervision.measure(stage, injected_state)
    pre_decision = supervision.decide(stage, pre_facts, {})
    # D19 only: what reaches the arm is the routed decision; the row still
    # records the verdict production itself returned.
    routed = d19_decision(pre_decision) if defect.get("cell") == "d19" else pre_decision

    row = {
        "defect_id": defect["defect_id"],
        "operator": defect["operator"],
        "stage": stage,
        "check_class": descriptor.check_class,
        "arm": cell["arm"],
        "placement": cell["placement"],
        "condition": cell.get("condition", "C0"),
        "rep": cell["rep"],
        "session_id": session_id,
        "descriptor": descriptor.to_dict(),
        # 14.6: the entire measurement, not only the injected check.
        "pre_facts": pre_facts,
        "pre_verdict": pre_decision.verdict,
        "retry_feedback": routed.retry_feedback,
        "cell": defect.get("cell", "core"),
        "severity": cell.get("severity", 1),
        "temperature": cell.get("temperature", 0.0),
        "reasoning_effort": cell.get("reasoning_effort"),
    }

    if dry_run:
        row.update(status="dry-run", attempts_made=0)
        return row

    # Imported lazily so --dry-run needs no API key configured.
    from app.agents.base_agent import BaseAgent  # noqa: PLC0415

    started = time.time()
    calls_before = len(BaseAgent.call_log)
    try:
        retried_state = _regenerate(cell, base_state, injected_state, descriptor, routed,
                                    defect_cell=defect.get("cell", "core"))
    except Exception as exc:  # noqa: BLE001 — recorded, not swallowed
        row.update(status="error", error_type=type(exc).__name__, error_detail=str(exc)[:400])
        return row

    calls = BaseAgent.call_log[calls_before:]
    if defect.get("cell") == "c7":
        row["local_calls"] = retried_state.get("_c7_calls", [])
    post_facts = supervision.measure(stage, retried_state)
    post_decision = supervision.decide(stage, post_facts, {})

    # The status_error exclusion, carried over verbatim: an API failure means
    # there was no output for the retry to repair, so the trial has no
    # interpretation under any arm.
    if post_facts.get("status_error"):
        output = retried_state.get(inject_defects.OUTPUT_KEY[stage]) or {}
        row.update(status="status_error", attempts_made=len(calls),
                   error_detail=output.get("error_detail"),
                   error_type=output.get("error_type"),
                   wall_clock_s=round(time.time() - started, 2))
        return row

    outcome = score_repair.score(descriptor, base_state, retried_state)
    row.update(
        status="ok",
        wall_clock_s=round(time.time() - started, 2),
        # A trial is 1-3 LLM calls, not 1: a schema failure appends the model's
        # own invalid output as an assistant turn, which is a P2-like condition
        # the placement manipulation did not ask for.
        attempts_made=len(calls),
        served_models=[c.get("served_model") for c in calls],
        prompt_tokens=sum(c.get("prompt_tokens") or 0 for c in calls) or None,
        completion_tokens=sum(c.get("completion_tokens") or 0 for c in calls) or None,
        thinking_tokens=sum(c.get("thinking_tokens") or 0 for c in calls) if any(c.get("thinking_tokens") is not None for c in calls) else None,
        total_tokens=sum(c.get("total_tokens") or 0 for c in calls) or None,
        post_facts=post_facts,
        post_verdict=post_decision.verdict,   # 14.4: the terminal run-level verdict
        outcome=outcome.to_dict(),
        # D12: the full retried output plus the upstream it was produced
        # against, so the downstream stages can be re-run later without
        # repeating this trial.
        retried_output=retried_state.get(inject_defects.OUTPUT_KEY[stage]),
        downstream_state={
            "business_id": base_state.get("business_id"),
            "business_name": base_state.get("business_name"),
            "analysis_results": base_state.get("analysis_results"),
            "reasoning_output": retried_state.get("reasoning_output"),
            "strategy_output": retried_state.get("strategy_output"),
            "report_output": retried_state.get("report_output"),
        },
    )
    return row


# The three in-scope stages (D6). analysis_agent is absent because its input is
# the sampled reviews, which a dump does not carry.
STAGE_AGENT = {
    "reasoning_agent": ("app.agents.reasoning_agent", "ReasoningAgent"),
    "strategy_agent": ("app.agents.strategy_agent", "StrategyAgent"),
    "report_agent": ("app.agents.report_agent", "ReportAgent"),
}


def _agent_for(stage: str):
    """Construct the production agent for a stage.

    Imported lazily: constructing one opens an LLM client, which --dry-run must
    never do.
    """
    from importlib import import_module  # noqa: PLC0415

    if stage not in STAGE_AGENT:
        raise ValueError(f"stage {stage!r} is out of scope for a replay trial (D6)")
    module_name, cls_name = STAGE_AGENT[stage]
    return getattr(import_module(module_name), cls_name)()


def _regenerate(cell: dict, base_state: dict, injected_state: dict,
                descriptor, decision, defect_cell: str = "core") -> dict:
    """Re-run the defective stage under this arm's prompt. Live call.

    Three properties this function exists to enforce, each of which would be a
    silent confound if it were merely intended:

    1. **The prompt is production's own.** ``agent.build_prompt`` is the same
       call ``agent.run`` makes, so an arm is a documented modification of the
       production prompt rather than a re-typed lookalike. A re-typed prompt
       would make A1 vs A2 a wording contrast as well as a content one, which
       is the confound D8 is already fighting.
    2. **The stage input is production's own.** ``nodes.stage_payload`` is what
       the graph node hands the stage. It is built from the **base** state:
       upstream is pinned from the dump and an operator only ever rewrites the
       target stage's own output, so base and injected upstream are identical
       by construction -- reading it from the base is what says so.
    3. **Nothing downstream of the retried stage survives.** The dump's
       strategy/report outputs were produced from the *pre-injection* output of
       this stage. They are not this trial's downstream, and leaving them in a
       field named ``downstream_state`` (D12) invites a later analysis to read
       them as such.
    4. **Factor C reaches the prompt here and nowhere else.** C1 rewrites the
       stage prompt this function just built; the *base output* it injects into
       came from a dump generated under production, so it is C0's under either
       condition. That is D8b option (ii), and it is what makes the cell a
       claim about retry-time disclosure rather than about a whole pipeline.
    """
    from app.core import nodes  # noqa: PLC0415

    stage = descriptor.stage
    payload = nodes.stage_payload(stage, base_state)
    agent = _agent_for(stage)
    if cell.get("runtime") == "c7":
        runtime = sys.modules.get("c7_runtime") or _load_by_path("c7_runtime", "c7_runtime.py")
        runtime.configure_agent(agent)
    if defect_cell == "thinking" or cell.get("cell") == "thinking":
        agent._model = THINKING_MODEL
        agent._fallback_model = THINKING_MODEL
    agent.reasoning_effort = cell.get("reasoning_effort")
    # Warm pass only (0.1 A7). A fresh agent per trial, so this cannot leak
    # into another trial; every other cell leaves the production value, 0.
    agent.temperature = float(cell.get("temperature", 0.0))
    base_messages, original_task = agent.build_prompt(payload)

    injected_output = json.dumps(
        injected_state.get(inject_defects.OUTPUT_KEY[stage]), ensure_ascii=False, indent=2
    )
    # A1 without feedback raises rather than silently degrading into A2 -- the
    # measured facts *are* the manipulation. run_trial records the exception.
    messages = arms_mod.build_messages(
        base_messages,
        cell["arm"],
        cell["placement"],
        injected_output,
        feedback=getattr(decision, "retry_feedback", None),
        # D8b: factor C varies the retry prompt only. The base output this
        # trial injects into was generated under C0 either way.
        condition=cell.get("condition", "C0"),
        stage=stage,
    )

    result = agent.run_messages(messages, original_task, payload)

    retried_state = dict(base_state)
    if cell.get("runtime") == "c7":
        retried_state["_c7_calls"] = agent._c7_calls
    retried_state[inject_defects.OUTPUT_KEY[stage]] = result
    later_stages = supervision.AGENT_SEQUENCE[supervision.AGENT_SEQUENCE.index(stage) + 1:]
    for later in later_stages:
        if later in inject_defects.OUTPUT_KEY:
            retried_state[inject_defects.OUTPUT_KEY[later]] = None
    return retried_state


# ── driver ────────────────────────────────────────────────────────────────────


def run(root: str, out_dir: str, reps: int, placement: str, seed: int,
        dry_run: bool, limit: int | None = None, sleep: float = 0.0,
        with_c1: bool = False, cell: str = "core", c7_gates: dict | None = None) -> int:
    plan = build_plan(root, reps=reps, placement=placement, seed=seed, with_c1=with_c1,
                      cell=cell, c7_gates=c7_gates)
    if cell == "c7":
        if seed != 0:
            raise ValueError("C7 uses the core's frozen injection seed 0")
        if not dry_run:
            if not c7_gates or not c7_gates.get("ready"):
                raise ValueError("C7 requires passed gates before a live run")
            if c7_gates.get("design") != "c7_r3_A11":
                raise ValueError("C7 requires the A11 repeated-trial gate record")
            runtime = sys.modules.get("c7_runtime") or _load_by_path("c7_runtime", "c7_runtime.py")
            runtime.verify_runtime(c7_gates)
            gates_module = _load_by_path("c7_gates", "c7_gates.py")
            if gates_module.source_digest(build_plan(root, cell="c7")) != c7_gates["source_digest"]:
                raise ValueError("C7 source data/prompts changed after the gates")
        for defect in plan:
            for trial_cell in defect["arms"]:
                trial_cell["runtime"] = "c7"
    problems = verify_order(plan)
    if problems:
        print("ORDER VIOLATION (section 14.1) — refusing to run:")
        for p in problems[:10]:
            print(f"  ! {p}")
        return 1

    if cell == "thinking":
        os.environ["LLM_PRIMARY_MODEL"] = THINKING_MODEL
        os.environ["LLM_FALLBACK_MODEL"] = THINKING_MODEL
        from app.agents import base_agent  # noqa: PLC0415
        os.environ[base_agent.FALLBACK_DISABLED_ENV] = "1"
        print(f"Cell thinking: pinned model {THINKING_MODEL}")

    if not dry_run:
        # B2 / section 14.1: a silent failover to the fallback model inside one
        # defect's arms is indistinguishable from a slow call in the logs, and
        # it breaks the matched comparison the whole design rests on. Fail the
        # trial instead -- the row records the error, and resume retries the
        # defect because load_done() does not treat "error" as done.
        from app.agents import base_agent  # noqa: PLC0415

        os.environ.setdefault(base_agent.FALLBACK_DISABLED_ENV, "1")
        if base_agent.fallback_disabled():
            print(f"{base_agent.FALLBACK_DISABLED_ENV}=1 (no silent model failover)")
        else:
            # An explicit override wins -- but never quietly. D5 says a trial
            # where the fallback fired is discarded, and the log cannot tell a
            # failover from a slow call.
            print(f"!! {base_agent.FALLBACK_DISABLED_ENV} is explicitly off. Arms in one "
                  f"defect may be served by different models, which breaks the matched "
                  f"comparison (D5, section 14.1).")

    path = checkpoint_path(out_dir)
    if cell == "c7" and not dry_run:
        header = os.path.join(out_dir, "run_header.json")
        os.makedirs(out_dir, exist_ok=True)
        manifest = {"cell": cell, "seed": seed, "summary": plan_summary(plan),
                    "gates": c7_gates,
                    "plan": [{k: d[k] for k in ("defect_id", "runnable", "reason", "arms")}
                             for d in plan]}
        if os.path.exists(header):
            with open(header, encoding="utf-8") as fh:
                if json.load(fh) != manifest:
                    raise ValueError("C7 resume header differs from the frozen runtime/plan")
        else:
            with open(header, "w", encoding="utf-8") as fh:
                json.dump(manifest, fh, indent=2)
    done = load_done(path)
    # A defect a pass does not carry is not written to that pass's checkpoint.
    pending = [d for d in plan if d["defect_id"] not in done
               and (d.get("runnable") or not not_in_pass(d))]
    if limit:
        pending = pending[:limit]

    s = plan_summary(plan)
    print(f"defects: {s['defects_runnable']} runnable, {s['defects_inapplicable']} inapplicable")
    print(f"gates  : injection {s['injection_verified']}/{s['defects_applicable']} "
          f"({s['injection_success_rate']}) · trigger {s['triggered']}/{s['injection_verified']} "
          f"({s['trigger_rate']})")
    print(f"trials : {s['trials']}  by arm {s['trials_by_arm']}")
    if s["c1_trials"]:
        print(f"cond   : core(C0) {s['core_trials']} · C1 {s['c1_trials']} "
              f"on {s['defects_c1']} defects {s['trials_by_cell']}")
    print(f"resume : {len(done)} done, {len(pending)} pending\n")

    for i, defect in enumerate(pending, 1):
        if not defect.get("runnable", defect.get("applicable")):
            append_row(path, {**defect, "status": "skipped"})
            continue

        # One session id per defect: all its arms share the serving stack of one
        # moment, which is the whole point of the ordering (14.1).
        session_id = uuid.uuid4().hex[:12]
        base_state = inject_defects.state_from_dump(defect["dump_dir"])
        injected_state, descriptor = inject_defects.inject(
            defect["operator"], base_state, seed=defect["seed"]
        )
        if not descriptor.applied:
            append_row(path, {**defect, "status": "skipped", "reason": descriptor.reason})
            continue
        # Only the severity pass varies the injection within a defect; every
        # other pass uses level 1 for every cell, exactly as before.
        injections = {1: (injected_state, descriptor)}
        for level in sorted({c.get("severity", 1) for c in defect["arms"]} - {1}):
            injections[level] = inject_defects.inject(
                defect["operator"], base_state, seed=defect["seed"], severity=level)

        trials = [
            run_trial(defect, cell, base_state, *injections[cell.get("severity", 1)],
                      session_id, dry_run)
            for cell in defect["arms"]
        ]
        # A defect whose trials hit an *exception* must not be marked done, or
        # resume skips it for good and the defect vanishes from the sample
        # silently. "error" here means a bug or a misconfiguration escaped
        # _regenerate -- not a provider failure, which base_agent converts into
        # an AgentError and run_trial records as "status_error". That one IS
        # data: it is the pre-registered exclusion, and re-running it until it
        # succeeds would be resampling on the outcome.
        #
        # Resume re-runs the whole defect, so a second row appears for the same
        # defect_id. Analysis takes the LAST row per defect_id.
        failed = [t for t in trials if t.get("status") == "error"]
        status = "dry-run" if dry_run else ("error" if failed else "ok")
        append_row(path, {
            "defect_id": defect["defect_id"],
            "operator": defect["operator"],
            "session_id": session_id,
            "status": status,
            "n_trials": len(trials),
            "n_failed": len(failed),
            "trials": trials,
        })
        note = f"  {len(failed)} FAILED" if failed else ""
        print(f"[{i}/{len(pending)}] {defect['defect_id']}  {len(trials)} trials{note}")
        if sleep and not dry_run and i < len(pending):
            time.sleep(sleep)

    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default="out_study")
    ap.add_argument("--out", default=None,
                    help="Checkpoint directory; defaults per --cell (core: out_study/T2).")
    ap.add_argument("--reps", type=int, default=DEFAULT_REPS)
    ap.add_argument("--placement", default=DEFAULT_PLACEMENT,
                    choices=list(arms_mod.PLACEMENTS))
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--sleep", type=float, default=0.0,
                    help="Seconds between defects; transient 503s are common at volume.")
    ap.add_argument("--dry-run", action="store_true",
                    help="Enumerate the plan and make no LLM calls.")
    ap.add_argument("--plan-only", action="store_true", help="Print the plan summary and exit.")
    ap.add_argument("--c1", action="store_true",
                    help="Add the D8 constraint-completeness cell: {A1,A2} under the "
                         "constraint-complete prompt, on a subset of defects (D8d). "
                         "Off by default -- the frozen core is C0 only.")
    ap.add_argument("--cell", default="core", choices=list(CELLS),
                    help="Which pass to make: the frozen core, the C1 cell as its own "
                         "pass (prereg 0.1 A3), the D19 counterfactual (0.1 A2), the "
                         "placement cell (0.1 A5), the O1 severity sweep (0.1 A6) or "
                         "the warm-resample cell (0.1 A7).")
    ap.add_argument("--c7-gates", default=None, help="Passed C7 gate report (A10).")
    args = ap.parse_args()
    if args.c1 and args.cell != "core":
        ap.error("--c1 extends the core plan; use --cell c1 for the C1 pass")
    out_dir = args.out or CELL_OUT[args.cell]
    gates = None
    if args.c7_gates:
        with open(args.c7_gates, encoding="utf-8") as fh:
            gates = json.load(fh)

    if args.plan_only:
        plan = build_plan(args.root, args.reps, args.placement, args.seed,
                          with_c1=args.c1, cell=args.cell, c7_gates=gates)
        print(json.dumps(plan_summary(plan), indent=2))
        problems = verify_order(plan)
        print("order OK" if not problems else f"ORDER VIOLATIONS: {problems[:5]}")
        return 0

    if not args.dry_run:
        from app.core import llm_config  # noqa: PLC0415
        if not llm_config.is_configured():
            print("No LLM configured. Use --dry-run, or set OPENAI_API_KEY.")
            return 1

    return run(args.root, out_dir, args.reps, args.placement, args.seed,
               args.dry_run, args.limit, args.sleep, args.c1, args.cell, gates)


if __name__ == "__main__":
    sys.exit(main())
