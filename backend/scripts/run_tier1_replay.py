"""Tier-1 replay — the production retry on real, production-caught defects.

PREREGISTRATION.md section 3 item 5 stratifies by defect origin (replayed-real
vs synthetic), which needs trials on the real defects; section 0.1 A8 fixes how
they run. Plan section 5 (Tier 1) fixed the rest before the freeze:

- **Placement P0** (D10): these defects really were the model's own, and the
  production retry really is blind to the defective output -- it re-sends the
  stage prompt plus the supervisor's feedback and nothing else.
- **Arms A1, A2, A3.** A1 *is* the production retry. A0 cannot run at P0 (D9b),
  which is why the plan's "132 trials" (with A0) realises as 117.
- **Judged at that stage by the same checks.** There is no clean reference
  output for a real defect, so there is no replacement value to score: a
  retried output is *accepted* when the supervisor's own checks no longer route
  it to retry. For the trace class the content-word trace (D22) is reported
  beside the production verdict, as it is for O5 in Tier 2.
- **Descriptive only.** MDE about 31 pp, and the defects nest in 7 business x
  stage cells (section 2.2): no hypothesis test is run, and any interval is a
  bootstrap over cells, not over defects.

The defect bank (``analysis/defect_bank.py``) is the input; every usable entry
is replayed through ``supervision.measure`` / ``decide`` at plan time, and a
defect runs only if the replay reproduces the recorded retry exactly.

Run (from backend/, venv active):

    python scripts/run_tier1_replay.py --plan-only
    python scripts/run_tier1_replay.py --dry-run
    python scripts/run_tier1_replay.py            # -> out_study/T1
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
arms_mod = runner.arms_mod
score_repair = runner.score_repair
defect_bank = _load_by_path("defect_bank", "analysis/defect_bank.py")
content_match = _load_by_path("content_match", "analysis/content_match.py")

ARMS = ("A1", "A2", "A3")
PLACEMENT = "P0"
DEFAULT_REPS = 3
DEFAULT_OUT = "out_study/T1"
TRACE_CLASS = "untraceable_recommendation"


def cell_of(entry: dict) -> str:
    """The business x stage cell a Tier-1 defect nests in (section 2.2)."""
    return f"{entry.get('business_name')} / {entry['stage']}"


def build_plan(root: str, reps: int = DEFAULT_REPS) -> list[dict]:
    """Every usable bank entry, replayed, with its arms attached.

    A defect runs only if replaying the dump reproduces the recorded retry:
    the verdict is ``retry``, the fired classes are the bank's, and the
    feedback string is byte-identical. Anything else means the dump does not
    hold the state the supervisor judged, and the trial would not be a replay.
    """
    bank = defect_bank.build(root)
    plan = []
    for e in bank["entries"]:
        if not e["usable"]:
            continue
        state = inject_defects.state_from_dump(e["dump_dir"])
        facts = supervision.measure(e["stage"], state)
        decision = supervision.decide(e["stage"], facts, {})
        fired = defect_bank.fired_classes(e["stage"], facts)
        reproduces = (decision.verdict == "retry"
                      and sorted(fired) == sorted(e["classes"])
                      and decision.retry_feedback == e["retry_feedback"])
        plan.append({
            "defect_id": e["defect_id"],
            "stage": e["stage"],
            "dump_dir": e["dump_dir"],
            "business_name": e["business_name"],
            "cell": cell_of(e),
            "classes": e["classes"],
            "runnable": reproduces,
            "reason": None if reproduces else "replay_does_not_reproduce_the_recorded_retry",
            "arms": ([{"arm": a, "placement": PLACEMENT, "rep": r}
                      for a in ARMS for r in range(reps)] if reproduces else []),
        })
    return plan


def plan_summary(plan: list[dict]) -> dict:
    runnable = [d for d in plan if d["runnable"]]
    by_arm: dict[str, int] = {}
    for d in runnable:
        for c in d["arms"]:
            by_arm[c["arm"]] = by_arm.get(c["arm"], 0) + 1
    return {
        "defects_in_bank": len(plan),
        "defects_runnable": len(runnable),
        "not_reproduced": len(plan) - len(runnable),
        "cells": len({d["cell"] for d in runnable}),
        "trials": sum(len(d["arms"]) for d in runnable),
        "trials_by_arm": by_arm,
        "by_stage": {s: sum(1 for d in runnable if d["stage"] == s)
                     for s in sorted({d["stage"] for d in runnable})},
    }


def _retried_state(state: dict, stage: str, output: dict) -> dict:
    retried = dict(state)
    retried[inject_defects.OUTPUT_KEY[stage]] = output
    for later in supervision.AGENT_SEQUENCE[supervision.AGENT_SEQUENCE.index(stage) + 1:]:
        if later in inject_defects.OUTPUT_KEY:
            retried[inject_defects.OUTPUT_KEY[later]] = None
    return retried


def judge(entry: dict, state: dict, output: dict) -> dict:
    """Section 0.1 A8's outcome, from the retried stage output alone.

    ``accepted``: no retry-level class fires on the retried output -- the
    supervisor would let the run proceed. ``target_resolved``: none of the
    classes that fired on the original output fires now. For the trace class,
    ``trace_resolved_content`` applies D22's content-word trace beside them.
    """
    stage = entry["stage"]
    retried = _retried_state(state, stage, output)
    facts = supervision.measure(stage, retried)
    decision = supervision.decide(stage, facts, {})
    fired = defect_bank.fired_classes(stage, facts)
    out = {
        "post_facts": facts,
        "post_verdict": decision.verdict,
        "post_fired": fired,
        "accepted": not fired,
        "target_resolved": not (set(fired) & set(entry["classes"])),
        "trace_resolved_content": None,
        "status_error": bool(facts.get("status_error")),
    }
    if TRACE_CLASS in entry["classes"]:
        untraceable = content_match.untraceable(
            score_repair._items(retried, "recommendation_issue"),
            inject_defects._trace_candidates(retried))
        out["untraceable_content"] = untraceable
        out["trace_resolved_content"] = not untraceable
    return out


def run_trial(entry: dict, cell: dict, state: dict, decision, session_id: str,
              dry_run: bool) -> dict:
    stage = entry["stage"]
    original = state.get(inject_defects.OUTPUT_KEY[stage])
    row = {
        "defect_id": entry["defect_id"], "stage": stage, "cell": entry["cell"],
        "classes": entry["classes"], "arm": cell["arm"], "placement": cell["placement"],
        "rep": cell["rep"], "session_id": session_id,
        "pre_verdict": decision.verdict, "retry_feedback": decision.retry_feedback,
    }
    if dry_run:
        row.update(status="dry-run", attempts_made=0)
        return row

    from app.agents.base_agent import BaseAgent  # noqa: PLC0415
    from app.core import nodes  # noqa: PLC0415

    started = time.time()
    calls_before = len(BaseAgent.call_log)
    try:
        payload = nodes.stage_payload(stage, state)
        agent = runner._agent_for(stage)
        if PINNED_MODEL:
            agent._model = agent._fallback_model = PINNED_MODEL
        base_messages, task = agent.build_prompt(payload)
        messages = arms_mod.build_messages(
            base_messages, cell["arm"], cell["placement"],
            json.dumps(original, ensure_ascii=False, indent=2),
            feedback=decision.retry_feedback)
        output = agent.run_messages(messages, task, payload)
    except Exception as exc:  # noqa: BLE001 -- recorded, not swallowed
        row.update(status="error", error_type=type(exc).__name__, error_detail=str(exc)[:400])
        return row

    calls = BaseAgent.call_log[calls_before:]
    verdict = judge(entry, state, output)
    if verdict["status_error"]:
        row.update(status="status_error", attempts_made=len(calls))
        return row
    row.update(
        status="ok",
        wall_clock_s=round(time.time() - started, 2),
        attempts_made=len(calls),
        served_models=[c.get("served_model") for c in calls],
        total_tokens=sum(c.get("total_tokens") or 0 for c in calls) or None,
        retried_output=output,
        same_as_original=(json.dumps(output, sort_keys=True, ensure_ascii=False)
                          == json.dumps(original, sort_keys=True, ensure_ascii=False)),
        **{k: v for k, v in verdict.items() if k != "status_error"},
    )
    return row


# --model (Option H, S5): pin primary and fallback in code so a .env default
# cannot serve the replay. None keeps the production configuration (T1 ran so).
PINNED_MODEL: str | None = None


def run(root: str, out_dir: str, reps: int, dry_run: bool, limit: int | None = None,
        model: str | None = None) -> int:
    global PINNED_MODEL
    PINNED_MODEL = model
    if model:
        runner.pin_model_env(model)
        print(f"pinned model {model}")
    plan = build_plan(root, reps)
    if not dry_run:
        from app.agents import base_agent  # noqa: PLC0415
        os.environ.setdefault(base_agent.FALLBACK_DISABLED_ENV, "1")
        print(f"{base_agent.FALLBACK_DISABLED_ENV}="
              f"{os.environ.get(base_agent.FALLBACK_DISABLED_ENV)} (no silent model failover)")
    path = runner.checkpoint_path(out_dir)
    done = runner.load_done(path)
    pending = [d for d in plan if d["defect_id"] not in done]
    if limit:
        pending = pending[:limit]
    s = plan_summary(plan)
    print(f"defects: {s['defects_runnable']} runnable of {s['defects_in_bank']} "
          f"({s['not_reproduced']} not reproduced) in {s['cells']} cells")
    print(f"trials : {s['trials']}  by arm {s['trials_by_arm']}")
    print(f"resume : {len(done)} done, {len(pending)} pending\n")

    for i, entry in enumerate(pending, 1):
        if not entry["runnable"]:
            runner.append_row(path, {**entry, "status": "skipped"})
            continue
        session_id = uuid.uuid4().hex[:12]   # one serving moment per defect (14.1)
        state = inject_defects.state_from_dump(entry["dump_dir"])
        decision = supervision.decide(entry["stage"], supervision.measure(entry["stage"], state), {})
        trials = [run_trial(entry, cell, state, decision, session_id, dry_run)
                  for cell in entry["arms"]]
        failed = [t for t in trials if t.get("status") == "error"]
        runner.append_row(path, {
            "defect_id": entry["defect_id"], "stage": entry["stage"], "cell": entry["cell"],
            "session_id": session_id,
            "status": "dry-run" if dry_run else ("error" if failed else "ok"),
            "n_trials": len(trials), "n_failed": len(failed), "trials": trials,
        })
        note = f"  {len(failed)} FAILED" if failed else ""
        print(f"[{i}/{len(pending)}] {entry['defect_id']}  {len(trials)} trials{note}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default="out_study")
    ap.add_argument("--out", default=DEFAULT_OUT)
    ap.add_argument("--reps", type=int, default=DEFAULT_REPS)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--plan-only", action="store_true")
    ap.add_argument("--model", default=None,
                    help="Pin primary and fallback to this model, failover off (Option H, S5).")
    args = ap.parse_args()

    if args.plan_only:
        plan = build_plan(args.root, args.reps)
        print(json.dumps(plan_summary(plan), indent=2))
        for d in plan:
            if not d["runnable"]:
                print("NOT RUNNABLE:", d["defect_id"], d["reason"])
        return 0
    if not args.dry_run:
        from app.core import llm_config  # noqa: PLC0415
        if not llm_config.is_configured():
            print("No LLM configured. Use --dry-run, or set OPENAI_API_KEY.")
            return 1
    return run(args.root, args.out, args.reps, args.dry_run, args.limit, args.model)


if __name__ == "__main__":
    sys.exit(main())
