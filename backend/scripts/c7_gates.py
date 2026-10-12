"""C7 preflight, never pooled into final trial data (PREREGISTRATION A10)."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import c7_runtime as runtime
import run_injection_study as runner
from app.core import nodes, supervision


def assemble(defect: dict, cell: dict):
    base = runner.inject_defects.state_from_dump(defect["dump_dir"])
    injected, descriptor = runner.inject_defects.inject(defect["operator"], base, seed=defect["seed"])
    decision = supervision.decide(descriptor.stage, supervision.measure(descriptor.stage, injected), {})
    payload = nodes.stage_payload(descriptor.stage, base)
    agent = runner._agent_for(descriptor.stage)
    messages, task = agent.build_prompt(payload)
    messages = runner.arms_mod.build_messages(
        messages, cell["arm"], cell["placement"],
        json.dumps(injected[runner.inject_defects.OUTPUT_KEY[descriptor.stage]],
                   ensure_ascii=False, indent=2), feedback=decision.retry_feedback,
        stage=descriptor.stage)
    return agent, messages, task, base, injected, descriptor


def source_digest(plan: list[dict]) -> str:
    # Include the bases, prompts, arm wording and cell allocation, not absolute paths.
    sources = []
    for defect in plan:
        if not defect["runnable"]:
            continue
        base = runner.inject_defects.state_from_dump(defect["dump_dir"])
        sources.append((defect["defect_id"], defect["arms"], runtime.sha(base)))
    files = ["arms.py", "inject_defects.py", "c7_runtime.py", "run_injection_study.py"]
    code = {name: hashlib.sha256((Path(__file__).parent / name).read_bytes()).hexdigest()
            for name in files}
    for name in ("reasoning_agent.py", "strategy_agent.py", "report_agent.py", "base_agent.py"):
        code[name] = hashlib.sha256((Path(__file__).parents[1] / "app/agents" / name).read_bytes()).hexdigest()
    for name in ("core/supervision.py", "core/nodes.py", "schemas/contracts.py"):
        code[name] = hashlib.sha256((Path(__file__).parents[1] / "app" / name).read_bytes()).hexdigest()
    for name in ("score_repair.py", "content_match.py"):
        code[name] = hashlib.sha256((Path(__file__).parent / "analysis" / name).read_bytes()).hexdigest()
    return runtime.sha({"data": sources, "code": code})


def context_gate(plan: list[dict]) -> dict:
    counts = {}
    for defect in plan:
        if not defect["runnable"]:
            continue
        by_arm = {}
        stage = None
        for cell in defect["arms"]:
            if cell["arm"] in by_arm:
                continue
            _agent, messages, _task, _base, _inj, descriptor = assemble(defect, cell)
            stage = descriptor.stage
            by_arm[cell["arm"]] = runtime.token_count(messages)
        largest = max(by_arm.values())
        counts[defect["defect_id"]] = {
            "eligible": largest + 64 + runtime.MAX_OUTPUT <= runtime.CONTEXT,
            "stage": stage, "tokens_by_arm": by_arm, "max_prompt_tokens": largest}
    return {"defects": counts, "eligible": sum(c["eligible"] for c in counts.values()),
            "excluded": sum(not c["eligible"] for c in counts.values()),
            "output_reserve": runtime.MAX_OUTPUT, "framing_margin": 64}


def choose_sample(plan: list[dict], context: dict, count: int) -> list[dict]:
    # Round-robin over operators; longest eligible prompt in each bucket first.
    groups = defaultdict(list)
    for d in plan:
        if d["runnable"] and context["defects"][d["defect_id"]]["eligible"]:
            groups[d["operator"]].append(d)
    for group in groups.values():
        group.sort(key=lambda d: (-context["defects"][d["defect_id"]]["max_prompt_tokens"],
                                  d["defect_id"]))
    selected = []
    while len(selected) < count and any(groups.values()):
        for op in sorted(groups):
            if groups[op] and len(selected) < count:
                selected.append(groups[op].pop(0))
    return selected


def determinism_gate(plan: list[dict], context: dict, out: Path) -> dict:
    results = []
    for d in choose_sample(plan, context, 10):
        agent, messages, _task, *_ = assemble(d, d["arms"][0])
        runtime.configure_agent(agent)
        started = time.time()
        for _ in range(2):
            agent._create(runtime.MODEL, messages)
        calls = agent._c7_calls
        result = {"defect_id": d["defect_id"], "identical": calls[0]["raw_sha256"] == calls[1]["raw_sha256"],
                  "token_counter_agrees": all(abs(c["prompt_tokens_local"] - c["prompt_tokens_server"]) <= 64
                                              for c in calls),
                  "wall_clock_s": round(time.time() - started, 2), "calls": calls}
        results.append(result)
        runner.append_row(str(out / "determinism.jsonl"), result)
        print(f"G2 {len(results)}/10 {d['defect_id']}: identical={result['identical']}", flush=True)
    return {"passed": len(results) == 10 and all(r["identical"] and r["token_counter_agrees"]
                                                for r in results),
            "identical": sum(r["identical"] for r in results), "pairs": len(results),
            "items": [{k: v for k, v in r.items() if k != "calls"} for r in results]}


def measured(report: dict) -> bool:
    """A11: token calibration is a gate; bit-identity is a reported observation."""
    return (report.get("pairs") == 10 and len(report.get("items", [])) == 10 and
            all(r["token_counter_agrees"] for r in report["items"]))


def import_determinism(previous: str, plan: list[dict], context: dict) -> dict:
    """Keep the failed G2 data; reuse only when runtime and all prompt hashes agree."""
    path = Path(previous)
    old = json.loads(path.read_text(encoding="utf-8"))
    if old["runtime"] != runtime.provenance() or not measured(old.get("determinism", {})):
        raise ValueError("Prior G2 runtime/calibration does not match")
    records = [json.loads(line) for line in (path.parent / "determinism.jsonl").read_text(
        encoding="utf-8").splitlines() if line.strip()]
    selected = choose_sample(plan, context, 10)
    if [r["defect_id"] for r in records] != [d["defect_id"] for d in selected]:
        raise ValueError("Prior G2 sample does not match")
    for defect, record in zip(selected, records):
        _agent, messages, *_ = assemble(defect, defect["arms"][0])
        if len(record["calls"]) != 2 or any(c["prompt_sha256"] != runtime.sha(messages)
                                          for c in record["calls"]):
            raise ValueError("Prior G2 prompts changed")
    return {"measurement": old["determinism"], "path": str(path),
            "report_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "source_digest": old["source_digest"]}


def pilot_gate(plan: list[dict], context: dict, out: Path) -> dict:
    # Five defects, all three stages; A1 and A2 for each, independent of G2 data.
    eligible = [d for d in plan if d["runnable"] and context["defects"][d["defect_id"]]["eligible"]]
    chosen, stages = [], set()
    for d in choose_sample(plan, context, len(eligible)):
        stage = context["defects"][d["defect_id"]]["stage"]
        if stage not in stages:
            chosen.append(d)
            stages.add(stage)
    for d in choose_sample(plan, context, 10):
        if d not in chosen and len(chosen) < 5:
            chosen.append(d)
    rows = []
    for d in chosen:
        _agent, _messages, _task, base, injected, descriptor = assemble(d, d["arms"][0])
        for arm in ("A1", "A2"):
            cell = next(c for c in d["arms"] if c["arm"] == arm)
            trial = runner.run_trial(d, {**cell, "runtime": "c7"}, base, injected,
                                     descriptor, "c7-preflight", False)
            rows.append(trial)
            runner.append_row(str(out / "pilot.jsonl"), trial)
            print(f"G4 {len(rows)}/10 {d['defect_id']} {arm}: {trial['status']}, "
                  f"attempts={trial.get('attempts_made')}", flush=True)
    first_pass = sum(r.get("status") == "ok" and r.get("attempts_made") == 1 for r in rows)
    return {"passed": len(rows) == 10 and len(stages) == 3 and first_pass > len(rows) / 2,
            "trials": len(rows), "schema_pass_first_attempt": first_pass,
            "schema_valid_eventually": sum(r.get("status") == "ok" for r in rows),
            "stages": sorted(stages),
            "mean_seconds": sum(r.get("wall_clock_s", 0) for r in rows) / len(rows) if rows else None}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default="out_study")
    ap.add_argument("--out", default="out_study/C7_preflight")
    ap.add_argument("--phase", choices=("context", "determinism", "pilot", "all"), default="all")
    ap.add_argument("--previous-gates", default=None, help="A11: preserved G2 for identical runtime/prompts")
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    report_path = out / "gates.json"
    report = json.loads(report_path.read_text()) if report_path.exists() else {}
    plan = runner.build_plan(args.root, cell="c7")
    if not report:
        report = {"ready": False, "runtime": runtime.provenance(),
                  "source_digest": source_digest(plan), "context": context_gate(plan),
                  "design": "c7_r3_A11"}
        models = runtime.request("/v1/models")["data"]
        loaded = runtime.request("/api/ps")["models"]
        model = next((m for m in loaded if m["name"].split(":")[0] == runtime.MODEL), {})
        report["connectivity"] = {
            "passed": any(m["id"].split(":")[0] == runtime.MODEL for m in models),
            "all_gpu": bool(model) and model.get("size_vram", 0) >= model.get("size", 1),
            "loaded_context": model.get("context_length"),
        }
        if not (report["connectivity"]["passed"] and report["connectivity"]["all_gpu"]
                and report["connectivity"]["loaded_context"] == runtime.CONTEXT):
            raise ValueError(f"G1 failed: {report['connectivity']}")
        report["hardware"] = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader"],
            text=True).strip()
        report["dependencies"] = subprocess.check_output([sys.executable, "-m", "pip", "freeze"],
                                                          text=True).splitlines()
        if args.previous_gates:
            previous = import_determinism(args.previous_gates, plan, report["context"])
            report["determinism"] = previous.pop("measurement")
            report["prior_determinism"] = previous
    elif source_digest(plan) != report["source_digest"]:
        raise ValueError("C7 code/data changed after preflight; use a fresh preflight directory")
    runtime.verify_runtime(report)
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"G3: {report['context']['eligible']} eligible, {report['context']['excluded']} excluded", flush=True)
    if args.phase in ("determinism", "all") and "determinism" not in report:
        report["determinism"] = determinism_gate(plan, report["context"], out)
        report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    if args.phase in ("pilot", "all"):
        if not measured(report.get("determinism", {})):
            raise ValueError("G2 calibration/measurement is incomplete")
        if "pilot" not in report:
            report["pilot"] = pilot_gate(plan, report["context"], out)
    report["ready"] = bool(measured(report.get("determinism", {})) and
                           report.get("pilot", {}).get("passed"))
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k not in ("runtime", "context")}, indent=2))
    return 0 if args.phase == "context" or report["ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
