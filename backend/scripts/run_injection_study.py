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

DEFAULT_REPS = 3          # D4d: r=3 if 0.80 power is the target
DEFAULT_PLACEMENT = "P1"  # D10: the Tier-2 core runs at P1, not the production P0


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


def _cells_for(index: int, reps: int, placement: str) -> list[dict]:
    """Arm x repetition cells for one defect, in execution order.

    A3 is a determinism floor at P0 by construction; A0 cannot run at P0 at all
    (D9b). Enforced here rather than special-cased in the loop.
    """
    cells: list[dict] = []
    for arm in ("A0", "A1", "A2", "A3"):
        if not _in_subset(index, ARM_FRACTION[arm]):
            continue
        arm_placement = "P0" if arm == "A3" else placement
        if not arms_mod.is_defined(arm, arm_placement):
            continue
        cells.extend({"arm": arm, "placement": arm_placement, "rep": r}
                     for r in range(reps))
    return cells


def build_plan(root: str, reps: int = DEFAULT_REPS, placement: str = DEFAULT_PLACEMENT,
               seed: int = 0, operators: tuple[str, ...] | None = None) -> list[dict]:
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
    operators = operators or inject_defects.REPAIR_OPERATORS
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

            entry["triggers"] = detail["verdict"] == "retry"
            if not entry["triggers"]:
                entry["reason"] = f"no_retry_verdict:{detail['verdict']}"
                plan.append(entry)
                continue

            entry["runnable"] = True
            entry["arms"] = _cells_for(op_index[op], reps, placement)
            op_index[op] += 1
            plan.append(entry)
    return plan


def plan_summary(plan: list[dict]) -> dict:
    """Counts for every gate, each against its own denominator (D20).

    ``injection_success_rate`` is over the *applicable* defects; ``trigger_rate``
    is over the ones whose injection verified. Reporting one pooled "yield"
    would hide which of the two moved.
    """
    applicable = [d for d in plan if d.get("applicable")]
    verified = [d for d in applicable if d.get("injection_valid")]
    runnable = [d for d in plan if d.get("runnable")]
    by_arm: dict[str, int] = {}
    for d in runnable:
        for cell in d["arms"]:
            by_arm[cell["arm"]] = by_arm.get(cell["arm"], 0) + 1

    def _rate(num: int, den: int) -> float | None:
        return round(num / den, 4) if den else None

    return {
        "defects_planned": len(plan),
        "defects_applicable": len(applicable),
        "defects_inapplicable": len(plan) - len(applicable),
        "injection_verified": len(verified),
        "injection_failed": len(applicable) - len(verified),
        "injection_success_rate": _rate(len(verified), len(applicable)),
        "triggered": len(runnable),
        "untriggered": len(verified) - len(runnable),
        "trigger_rate": _rate(len(runnable), len(verified)),
        "defects_runnable": len(runnable),
        "trials": sum(len(d["arms"]) for d in runnable),
        "trials_by_arm": by_arm,
        "operators": sorted({d["operator"] for d in runnable}),
    }


def verify_order(plan: list[dict]) -> list[str]:
    """The 14.1 invariant, checkable without running anything.

    Within a defect, every arm's repetitions must be contiguous, and the defect
    must hold all of its arms. If the loop is ever rewritten arm-outer, this is
    what says so.
    """
    problems = []
    for d in plan:
        # Keyed on runnable, not applicable: a defect the D20 gates removed
        # carries no arms by design, and must not be reported as missing one.
        if not d.get("runnable", d.get("applicable")):
            continue
        seen: list[str] = []
        for cell in d["arms"]:
            if not seen or seen[-1] != cell["arm"]:
                if cell["arm"] in seen:
                    problems.append(f"{d['defect_id']}: arm {cell['arm']} is not contiguous")
                seen.append(cell["arm"])
        # A0 and A3 run on subsets by design (D4c); the primary contrast does not.
        if "A1" not in seen or "A2" not in seen:
            problems.append(f"{d['defect_id']}: missing a primary arm ({seen})")
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

    row = {
        "defect_id": defect["defect_id"],
        "operator": defect["operator"],
        "stage": stage,
        "check_class": descriptor.check_class,
        "arm": cell["arm"],
        "placement": cell["placement"],
        "rep": cell["rep"],
        "session_id": session_id,
        "descriptor": descriptor.to_dict(),
        # 14.6: the entire measurement, not only the injected check.
        "pre_facts": pre_facts,
        "pre_verdict": pre_decision.verdict,
        "retry_feedback": pre_decision.retry_feedback,
    }

    if dry_run:
        row.update(status="dry-run", attempts_made=0)
        return row

    # Imported lazily so --dry-run needs no API key configured.
    from app.agents.base_agent import BaseAgent  # noqa: PLC0415

    started = time.time()
    calls_before = len(BaseAgent.call_log)
    try:
        retried_state = _regenerate(cell, base_state, injected_state, descriptor, pre_decision)
    except Exception as exc:  # noqa: BLE001 — recorded, not swallowed
        row.update(status="error", error_type=type(exc).__name__, error_detail=str(exc)[:400])
        return row

    calls = BaseAgent.call_log[calls_before:]
    post_facts = supervision.measure(stage, retried_state)
    post_decision = supervision.decide(stage, post_facts, {})

    # The status_error exclusion, carried over verbatim: an API failure means
    # there was no output for the retry to repair, so the trial has no
    # interpretation under any arm.
    if post_facts.get("status_error"):
        row.update(status="status_error", attempts_made=len(calls))
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
                descriptor, decision) -> dict:
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
    """
    from app.core import nodes  # noqa: PLC0415

    stage = descriptor.stage
    payload = nodes.stage_payload(stage, base_state)
    agent = _agent_for(stage)
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
    )

    result = agent.run_messages(messages, original_task, payload)

    retried_state = dict(base_state)
    retried_state[inject_defects.OUTPUT_KEY[stage]] = result
    later_stages = supervision.AGENT_SEQUENCE[supervision.AGENT_SEQUENCE.index(stage) + 1:]
    for later in later_stages:
        if later in inject_defects.OUTPUT_KEY:
            retried_state[inject_defects.OUTPUT_KEY[later]] = None
    return retried_state


# ── driver ────────────────────────────────────────────────────────────────────


def run(root: str, out_dir: str, reps: int, placement: str, seed: int,
        dry_run: bool, limit: int | None = None, sleep: float = 0.0) -> int:
    plan = build_plan(root, reps=reps, placement=placement, seed=seed)
    problems = verify_order(plan)
    if problems:
        print("ORDER VIOLATION (section 14.1) — refusing to run:")
        for p in problems[:10]:
            print(f"  ! {p}")
        return 1

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
    done = load_done(path)
    pending = [d for d in plan if d["defect_id"] not in done]
    if limit:
        pending = pending[:limit]

    s = plan_summary(plan)
    print(f"defects: {s['defects_runnable']} runnable, {s['defects_inapplicable']} inapplicable")
    print(f"gates  : injection {s['injection_verified']}/{s['defects_applicable']} "
          f"({s['injection_success_rate']}) · trigger {s['triggered']}/{s['injection_verified']} "
          f"({s['trigger_rate']})")
    print(f"trials : {s['trials']}  by arm {s['trials_by_arm']}")
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

        trials = [
            run_trial(defect, cell, base_state, injected_state, descriptor,
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
    ap.add_argument("--out", default="out_study/T2")
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
    args = ap.parse_args()

    if args.plan_only:
        plan = build_plan(args.root, args.reps, args.placement, args.seed)
        print(json.dumps(plan_summary(plan), indent=2))
        problems = verify_order(plan)
        print("order OK" if not problems else f"ORDER VIOLATIONS: {problems[:5]}")
        return 0

    if not args.dry_run:
        from app.core import llm_config  # noqa: PLC0415
        if not llm_config.is_configured():
            print("No LLM configured. Use --dry-run, or set OPENAI_API_KEY.")
            return 1

    return run(args.root, args.out, args.reps, args.placement, args.seed,
               args.dry_run, args.limit, args.sleep)


if __name__ == "__main__":
    sys.exit(main())
