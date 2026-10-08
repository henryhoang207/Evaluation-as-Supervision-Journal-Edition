"""Downstream propagation (plan D12) -- does repairing a defect improve the pipeline?

PREREGISTRATION.md section 0.1 A9 fixes this design; the author chose its
endpoint (option (b)) on 2026-10-08. The thesis it tests is the journal's:
*defect-level repair does not equal pipeline-level improvement* (MAST App. J).

For every core defect at the reasoning or strategy stage, the stages downstream
of the defective stage are re-run, in one session, from five starting points:

    clean x 2     the pre-injection output -- the reference pipeline, twice, so
                  the second run measures run-to-run noise in the same session
    unrepaired    the injected (defective) output -- what the pipeline does
                  when the defect is let through: the no-repair baseline
    A1, A2        the core's retried output for that arm, repetition 0 (the
                  first executed, chosen before any downstream result existed)

Each downstream stage runs exactly once through the **production node**
(``nodes.strategy_node`` / ``nodes.report_node``) at temperature 0, in observe
mode -- measured and judged by the supervisor, never retried -- which is how the
Phase-A dumps these defects came from were produced. Report-stage defects (O6,
O7) have no downstream stage and are not part of this pass.

Run (from backend/, venv active):

    python scripts/run_downstream.py --plan-only
    python scripts/run_downstream.py --dry-run
    python scripts/run_downstream.py             # -> out_study/T2D
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


runner = _load_by_path("run_injection_study", "run_injection_study.py")
inject_defects = runner.inject_defects
defect_bank = _load_by_path("defect_bank", "analysis/defect_bank.py")

DEFAULT_OUT = "out_study/T2D"
DEFAULT_CORE = "out_study/T2/checkpoint.jsonl"
DOWNSTREAM = {"reasoning_agent": ("strategy_agent", "report_agent"),
              "strategy_agent": ("report_agent",)}
CONDITIONS = (("clean", 0), ("clean", 1), ("unrepaired", 0), ("A1", 0), ("A2", 0))
ARM_REP = 0          # the core repetition whose retried output is propagated
BLOCKING = ("retry", "halt")


def _latest_rows(path: str) -> dict:
    latest = {}
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            latest[row["defect_id"]] = row
    return latest


def build_plan(root: str, core_path: str = DEFAULT_CORE) -> list[dict]:
    """Core defects with a downstream stage, and the arm outputs they propagate."""
    core = _latest_rows(core_path)
    plan = []
    for d in runner.build_plan(root):
        if not d["runnable"]:
            continue
        stage = inject_defects.STAGE[d["operator"]]
        if stage not in DOWNSTREAM:
            continue
        row = core.get(d["defect_id"]) or {}
        arm_trials = {}
        for t in row.get("trials", []):
            if t.get("rep") == ARM_REP and t.get("arm") in ("A1", "A2") \
                    and t.get("condition", "C0") == "C0":
                arm_trials[t["arm"]] = t
        conditions, missing = [], []
        for name, rep in CONDITIONS:
            if name in ("A1", "A2"):
                t = arm_trials.get(name)
                if not t or t.get("status") != "ok":
                    missing.append(name)
                    continue
                conditions.append({"condition": name, "rep": rep,
                                   "core_outcome": (t.get("outcome") or {}).get("outcome")})
            else:
                conditions.append({"condition": name, "rep": rep})
        plan.append({
            "defect_id": d["defect_id"], "operator": d["operator"], "stage": stage,
            "dump_dir": d["dump_dir"], "seed": d["seed"],
            "downstream": list(DOWNSTREAM[stage]),
            "conditions": conditions, "missing_arms": missing, "runnable": True,
        })
    return plan


def plan_summary(plan: list[dict]) -> dict:
    calls = sum(len(d["conditions"]) * len(d["downstream"]) for d in plan)
    by_op: dict[str, int] = {}
    for d in plan:
        by_op[d["operator"]] = by_op.get(d["operator"], 0) + 1
    return {
        "defects": len(plan),
        "by_operator": by_op,
        "conditions": sum(len(d["conditions"]) for d in plan),
        "downstream_calls_planned": calls,
        "missing_arm_outputs": sum(len(d["missing_arms"]) for d in plan),
    }


def start_state(entry: dict, condition: str, base: dict, injected: dict,
                arm_output: dict | None) -> dict:
    """The pipeline state the downstream stages start from, for one condition."""
    stage = entry["stage"]
    key = inject_defects.OUTPUT_KEY[stage]
    state = {
        "business_id": base.get("business_id"),
        "business_name": base.get("business_name"),
        "analysis_results": base.get("analysis_results"),
        "reasoning_output": base.get("reasoning_output"),
        "strategy_output": base.get("strategy_output"),
        "report_output": None,
        "retry_feedback": None,
        "errors": {},
    }
    state[key] = {"clean": base.get(key), "unrepaired": injected.get(key)}.get(condition, arm_output)
    for later in entry["downstream"]:
        state[inject_defects.OUTPUT_KEY[later]] = None
    return state


def _arm_output(core_row: dict, arm: str) -> dict | None:
    for t in core_row.get("trials", []):
        if t.get("arm") == arm and t.get("rep") == ARM_REP and t.get("condition", "C0") == "C0":
            return t.get("retried_output")
    return None


def run_condition(entry: dict, cond: dict, state: dict, session_id: str, dry_run: bool) -> dict:
    row = {"defect_id": entry["defect_id"], "operator": entry["operator"],
           "stage": entry["stage"], "condition": cond["condition"], "rep": cond["rep"],
           "core_outcome": cond.get("core_outcome"), "session_id": session_id}
    if dry_run:
        row.update(status="dry-run")
        return row

    from app.agents.base_agent import BaseAgent  # noqa: PLC0415
    from app.core import nodes  # noqa: PLC0415

    node = {"strategy_agent": nodes.strategy_node, "report_agent": nodes.report_node}
    started = time.time()
    calls_before = len(BaseAgent.call_log)
    stages = {}
    try:
        for stage in entry["downstream"]:
            node[stage](state)
            facts = supervision.measure(stage, state)
            decision = supervision.decide(stage, facts, {})
            stages[stage] = {"verdict": decision.verdict,
                             "fired": defect_bank.fired_classes(stage, facts),
                             "status_error": bool(facts.get("status_error"))}
            if facts.get("status_error"):
                break
    except Exception as exc:  # noqa: BLE001 -- recorded, not swallowed
        row.update(status="error", error_type=type(exc).__name__, error_detail=str(exc)[:400])
        return row

    calls = BaseAgent.call_log[calls_before:]
    errored = any(s["status_error"] for s in stages.values())
    row.update(
        status="status_error" if errored else "ok",
        wall_clock_s=round(time.time() - started, 2),
        calls=len(calls),
        served_models=[c.get("served_model") for c in calls],
        total_tokens=sum(c.get("total_tokens") or 0 for c in calls) or None,
        stages=stages,
        accepted=(not errored) and all(s["verdict"] not in BLOCKING for s in stages.values()),
        strategy_output=state.get("strategy_output") if "strategy_agent" in entry["downstream"] else None,
        final_report=state.get("report_output"),
    )
    return row


def run(root: str, out_dir: str, core_path: str, dry_run: bool, limit: int | None = None) -> int:
    plan = build_plan(root, core_path)
    if not dry_run:
        from app.agents import base_agent  # noqa: PLC0415
        os.environ.setdefault(base_agent.FALLBACK_DISABLED_ENV, "1")
        print(f"{base_agent.FALLBACK_DISABLED_ENV}="
              f"{os.environ.get(base_agent.FALLBACK_DISABLED_ENV)} (no silent model failover)")
    core = _latest_rows(core_path)
    path = runner.checkpoint_path(out_dir)
    done = runner.load_done(path)
    pending = [d for d in plan if d["defect_id"] not in done]
    if limit:
        pending = pending[:limit]
    s = plan_summary(plan)
    print(f"defects: {s['defects']} {s['by_operator']} · conditions {s['conditions']} · "
          f"downstream calls {s['downstream_calls_planned']} · missing arm outputs {s['missing_arm_outputs']}")
    print(f"resume : {len(done)} done, {len(pending)} pending\n")

    for i, entry in enumerate(pending, 1):
        session_id = uuid.uuid4().hex[:12]   # every condition of a defect shares one moment (14.1)
        base = inject_defects.state_from_dump(entry["dump_dir"])
        injected, descriptor = inject_defects.inject(entry["operator"], base, seed=entry["seed"])
        # O5 is the one operator whose injected content can be traced into the
        # final report: the alien recommendation issue it planted.
        injected_issue = descriptor.target.get("after") if entry["operator"] == "O5" else None
        core_row = core.get(entry["defect_id"]) or {}
        results = []
        for cond in entry["conditions"]:
            arm_out = _arm_output(core_row, cond["condition"]) if cond["condition"] in ("A1", "A2") else None
            state = start_state(entry, cond["condition"], base, injected, arm_out)
            results.append(run_condition(entry, cond, state, session_id, dry_run))
        failed = [r for r in results if r.get("status") == "error"]
        runner.append_row(path, {
            "defect_id": entry["defect_id"], "operator": entry["operator"], "stage": entry["stage"],
            "session_id": session_id, "missing_arms": entry["missing_arms"],
            "injected_issue": injected_issue,
            "status": "dry-run" if dry_run else ("error" if failed else "ok"),
            "n_conditions": len(results), "n_failed": len(failed), "conditions": results,
        })
        note = f"  {len(failed)} FAILED" if failed else ""
        print(f"[{i}/{len(pending)}] {entry['defect_id']}  {len(results)} conditions{note}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default="out_study")
    ap.add_argument("--core", default=DEFAULT_CORE)
    ap.add_argument("--out", default=DEFAULT_OUT)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--plan-only", action="store_true")
    args = ap.parse_args()
    if args.plan_only:
        print(json.dumps(plan_summary(build_plan(args.root, args.core)), indent=2))
        return 0
    if not args.dry_run:
        from app.core import llm_config  # noqa: PLC0415
        if not llm_config.is_configured():
            print("No LLM configured. Use --dry-run, or set OPENAI_API_KEY.")
            return 1
    return run(args.root, args.out, args.core, args.dry_run, args.limit)


if __name__ == "__main__":
    sys.exit(main())
