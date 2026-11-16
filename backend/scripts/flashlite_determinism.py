"""A15: ten fixed real A1/P1 prompts, two raw calls each; never repair scoring."""
from __future__ import annotations

import argparse
import hashlib
import importlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import sys
import uuid
from collections import Counter, defaultdict

BACKEND = Path(__file__).resolve().parents[1]
for directory in (BACKEND, BACKEND / "scripts"):
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))
MODEL = "gemini-3.5-flash-lite"
PAIRS = 10


def sha(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def encoded(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def canonical(raw: str | None) -> str | None:
    try:
        value = json.loads(raw)
    except (ValueError, TypeError):
        return None
    return sha(encoded(value)) if isinstance(value, dict) else None


def assemble(defect: dict) -> dict:
    import run_injection_study as runner
    from app.core import nodes, supervision
    base = runner.inject_defects.state_from_dump(defect["dump_dir"])
    injected, descriptor = runner.inject_defects.inject(defect["operator"], base, seed=defect["seed"])
    decision = supervision.decide(descriptor.stage, supervision.measure(descriptor.stage, injected), {})
    module_name, class_name = runner.STAGE_AGENT[descriptor.stage]
    cls = getattr(importlib.import_module(module_name), class_name)
    # Production prompt builders are stateless. Render without constructing an
    # HTTP client; planning and dry runs must work without a configured SDK.
    prompt_only = object.__new__(cls)
    messages, _ = prompt_only.build_prompt(nodes.stage_payload(descriptor.stage, base))
    messages = runner.arms_mod.build_messages(
        messages, "A1", "P1",
        json.dumps(injected[runner.inject_defects.OUTPUT_KEY[descriptor.stage]], ensure_ascii=False, indent=2),
        feedback=decision.retry_feedback, condition="C0", stage=descriptor.stage)
    text = encoded(messages)
    return {"pair_id": defect["defect_id"], "stage": descriptor.stage,
            "operator": defect["operator"], "messages": messages,
            "prompt_sha256": sha(text), "prompt_bytes": len(text.encode("utf-8"))}


def select_prompts(candidates: list[dict], count: int = PAIRS) -> list[dict]:
    """C7-style operator round-robin, longest UTF-8 serialization first; deduplicate."""
    groups = defaultdict(list)
    for candidate in candidates:
        groups[candidate["operator"]].append(candidate)
    for group in groups.values():
        group.sort(key=lambda x: (-x["prompt_bytes"], x["pair_id"]))
    chosen, seen = [], set()
    while len(chosen) < count and any(groups.values()):
        for operator in sorted(groups):
            group = groups[operator]
            while group:
                item = group.pop(0)
                if item["prompt_sha256"] not in seen:
                    chosen.append(item)
                    seen.add(item["prompt_sha256"])
                    break
            if len(chosen) == count:
                break
    if len(chosen) != count:
        raise ValueError(f"Need {count} distinct real prompts, found {len(chosen)}")
    return chosen


def build_plan(root: str = "out_study/FL") -> list[dict]:
    import run_injection_study as runner
    from flashlite_protocol import validate_bases
    bases = validate_bases(root)
    eligible = runner.build_plan(root, cell="flashlite")
    selected = select_prompts([assemble(d) for d in eligible if d["runnable"]])
    return [{**pair, "defect_id": f"{pair['pair_id']}::D{slot}", "slot": slot,
             "runnable": True, "arms": [{"measurement": "determinism", "slot": slot}],
             "bases_sha256": bases["bases_sha256"]}
            for pair in selected for slot in (1, 2)]


def manifest(plan: list[dict]) -> dict:
    files = ["scripts/flashlite_determinism.py", "scripts/run_injection_study.py",
             "scripts/arms.py", "scripts/inject_defects.py", "scripts/flashlite_protocol.py",
             "app/core/nodes.py", "app/core/supervision.py", "app/agents/base_agent.py",
             "app/agents/reasoning_agent.py", "app/agents/strategy_agent.py", "app/agents/report_agent.py"]
    return {"model": MODEL, "reasoning_effort": None, "temperature": 0,
            "sdk_max_retries": 0, "python": platform.python_version(),
            "dependencies": {n: importlib.metadata.version(n) for n in ("openai", "httpx")},
            "sources": {n: hashlib.sha256((BACKEND / n).read_bytes()).hexdigest() for n in files},
            "calls": [{k: d[k] for k in ("defect_id", "pair_id", "slot", "operator", "stage",
                                         "prompt_sha256", "prompt_bytes", "bases_sha256")} for d in plan]}


def new_agent(stage: str):
    import run_injection_study as runner
    runner.pin_model_env(MODEL)
    agent = runner._agent_for(stage)
    agent._model = agent._fallback_model = MODEL
    agent.temperature, agent.reasoning_effort = 0.0, None
    agent._client = agent._client.with_options(max_retries=0)
    return agent


def call_once(agent, messages: list[dict], session: str) -> dict:
    from app.agents.base_agent import BaseAgent
    BaseAgent.reset_instrumentation()
    meta = {"requested_model": MODEL, "served_models": [], "fallback_used": False,
            "temperature": 0.0, "reasoning_effort": None, "session_id": session,
            "prompt_tokens": None, "completion_tokens": None, "total_tokens": None}
    raw, error = None, None
    try:
        response = agent._create(MODEL, messages)
        agent._record_usage(response, MODEL, fallback_used=False)
        meta.update(BaseAgent.call_log[-1])
        served = getattr(response, "model", None)
        meta["served_models"] = [served] if served else []
        raw = response.choices[0].message.content
        if served != MODEL:
            error = "wrong served model"
        elif not isinstance(raw, str):
            error = "no text response"
    except Exception as exc:
        error = type(exc).__name__ + ": " + str(exc)[:1000]
    return {**meta, "status": "error" if error else "ok", "error": error,
            "raw_response": raw, "raw_sha256": sha(raw) if isinstance(raw, str) else None,
            "canonical_sha256": canonical(raw), "json_valid": canonical(raw) is not None}


def collect(plan: list[dict], out: Path, dry_run: bool = False, agent_factory=new_agent) -> None:
    import run_injection_study as runner
    out.mkdir(parents=True, exist_ok=True)
    info = manifest(plan)
    info_path = out / "manifest.json"
    if info_path.exists() and json.loads(info_path.read_text(encoding="utf-8")) != info:
        raise ValueError("Calibration sources/prompts/runtime changed; do not reuse this cell")
    info_path.write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding="utf-8")
    checkpoint = out / "checkpoint.jsonl"
    existing = {}
    if checkpoint.exists():
        for line in checkpoint.read_text(encoding="utf-8").splitlines():
            if line.strip():
                row = json.loads(line)
                existing[row["defect_id"]] = row
    if any(r.get("status") != "ok" for r in existing.values()):
        raise ValueError("Unfinished request slot: preserve it and inspect before any further call")
    for pair in {d["pair_id"] for d in plan}:
        have = [d for d in plan if d["pair_id"] == pair and d["defect_id"] in existing]
        if len(have) == 1:
            raise ValueError("Interrupted prompt pair: do not replace or split it across sessions")
    session = str(uuid.uuid4())
    agents = {}
    for d in plan:
        if d["defect_id"] in existing:
            continue  # completed/error responses are never reissued
        base = {k: d[k] for k in ("defect_id", "pair_id", "slot", "operator", "stage",
                                  "prompt_sha256", "prompt_bytes", "bases_sha256")}
        base.update(cell="flashlite_determinism", session_id=session, dry_run=dry_run)
        runner.append_row(str(checkpoint), {**base, "status": "started", "trials": []})
        if dry_run:
            call = {"status": "ok", "served_models": [MODEL], "session_id": session,
                    "reasoning_effort": None, "temperature": 0.0, "fallback_used": False,
                    "total_tokens": 0, "raw_response": "{}", "raw_sha256": sha("{}"),
                    "canonical_sha256": canonical("{}"), "json_valid": True}
        else:
            if d["pair_id"] not in agents:
                agents[d["pair_id"]] = agent_factory(d["stage"])
            call = call_once(agents[d["pair_id"]], d["messages"], session)
        runner.append_row(str(checkpoint), {**base, "status": "ok", "trials": [call]})
        print(f"{len(existing)+1}/{len(plan)} {d['defect_id']}: {call['status']}", flush=True)
        existing[d["defect_id"]] = base
        if call.get("served_models") and call["served_models"] != [MODEL]:
            raise ValueError("Wrong served model; calibration stopped")


def verify_measurements(rows: list[dict], plan: list[dict], *, allow_dry_run: bool = False) -> dict:
    latest = {r["defect_id"]: r for r in rows}
    expected = {d["defect_id"]: d for d in plan}
    problems = []
    if set(latest) != set(expected):
        problems.append("calibration checkpoint does not match the 20 fixed request slots")
    pairs = defaultdict(list)
    calls, statuses, models = [], Counter(), Counter()
    for key, d in expected.items():
        r = latest.get(key, {})
        if r.get("status") != "ok" or len(r.get("trials", [])) != 1:
            problems.append(f"{key}: request slot unfinished or absent")
            continue
        if r.get("dry_run") and not allow_dry_run:
            problems.append(f"{key}: dry-run response cannot be measurement data")
        if any(r.get(k) != d[k] for k in ("pair_id", "slot", "stage", "operator", "prompt_sha256", "prompt_bytes", "bases_sha256")):
            problems.append(f"{key}: prompt/base provenance changed")
        t = r["trials"][0]
        calls.append(t)
        statuses[t.get("status", "unknown")] += 1
        models[", ".join(t.get("served_models") or [])] += 1
        if t.get("reasoning_effort") is not None or t.get("temperature") != 0.0 or t.get("fallback_used"):
            problems.append(f"{key}: calibration configuration changed")
        if not t.get("session_id") or t.get("session_id") != r.get("session_id"):
            problems.append(f"{key}: invalid session provenance")
        if t.get("served_models") and t["served_models"] != [MODEL]:
            problems.append(f"{key}: wrong served model")
        if t.get("status") == "ok":
            if t.get("served_models") != [MODEL]:
                problems.append(f"{key}: wrong served model")
            if not isinstance(t.get("raw_response"), str) or t.get("raw_sha256") != sha(t["raw_response"]):
                problems.append(f"{key}: raw response/hash mismatch")
            if bool(t.get("json_valid")) != (canonical(t.get("raw_response")) is not None):
                problems.append(f"{key}: JSON-validity flag mismatch")
            if t.get("canonical_sha256") != canonical(t.get("raw_response")):
                problems.append(f"{key}: canonical response/hash mismatch")
            if not isinstance(t.get("total_tokens"), int):
                problems.append(f"{key}: successful call has no usage")
        pairs[d["pair_id"]].append(t)
    raw_equal = canonical_equal = valid_raw = valid_json = 0
    summaries = []
    for pair in sorted({d["pair_id"] for d in plan}):
        items = pairs[pair]
        summary = {"pair_id": pair, "calls": len(items), "statuses": [t.get("status") for t in items],
                   "raw_identical": None, "canonical_identical": None}
        summaries.append(summary)
        if len(items) != 2:
            problems.append(f"{pair}: incomplete pair")
            continue
        if len({t.get("session_id") for t in items}) != 1:
            problems.append(f"{pair}: spans sessions")
        if all(t.get("status") == "ok" for t in items):
            valid_raw += 1
            summary["raw_identical"] = items[0].get("raw_sha256") == items[1].get("raw_sha256")
            raw_equal += summary["raw_identical"]
            if all(t.get("canonical_sha256") is not None for t in items):
                valid_json += 1
                summary["canonical_identical"] = items[0]["canonical_sha256"] == items[1]["canonical_sha256"]
                canonical_equal += summary["canonical_identical"]
    # Sum all completed call rows, preserving the global token-accounting rule;
    # started rows carry no calls/tokens. Duplicate completions are a failure.
    all_calls = [t for r in rows for t in r.get("trials", [])]
    if len(all_calls) != len(calls):
        problems.append("duplicate completed request slots")
    return {"rows": len(latest), "rows_expected": len(expected), "trials": len(calls),
            "trials_planned": len(plan), "n_ok": statuses.get("ok", 0), "status": dict(statuses),
            "served_models": dict(models), "tokens": sum(t.get("total_tokens") or 0 for t in all_calls),
            "pairs": len(pairs), "pairs_planned": len({d["pair_id"] for d in plan}), "items": summaries,
            "valid_raw_pairs": valid_raw, "raw_identical_pairs": int(raw_equal),
            "valid_json_pairs": valid_json, "canonical_identical_pairs": int(canonical_equal),
            "invalid_json_calls": sum(t.get("status") == "ok" and not t.get("json_valid") for t in calls),
            "problems": problems}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default="out_study/FL")
    ap.add_argument("--out", default="out_study/FL/determinism")
    ap.add_argument("--model", default=MODEL, choices=[MODEL])
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--plan-only", action="store_true")
    args = ap.parse_args()
    from dotenv import load_dotenv
    load_dotenv(BACKEND / ".env", override=False)
    import run_injection_study as runner
    runner.pin_model_env(MODEL)
    plan = build_plan(args.root)
    if args.plan_only:
        print(json.dumps(manifest(plan), ensure_ascii=False, indent=2))
        return 0
    out = Path(args.out).resolve()
    frozen = [BACKEND / "out_study/T2", BACKEND / "out_study/T2T", Path(args.root).resolve() / "A"]
    if any(out == p.resolve() or p.resolve() in out.parents for p in frozen):
        raise ValueError("Cannot write calibration into frozen trials or base dumps")
    if args.dry_run and (out == BACKEND / "out_study" or BACKEND / "out_study" in out.parents):
        raise ValueError("Dry calibration writes outside out_study only")
    if not args.dry_run and out != Path(args.root).resolve() / "determinism":
        raise ValueError("Live calibration writes only to its registered measurement directory")
    collect(plan, out, args.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
