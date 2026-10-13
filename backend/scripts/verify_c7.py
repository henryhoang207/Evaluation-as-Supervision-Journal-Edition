"""Verify complete C7 checkpoint and reproduce every scored outcome offline."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import c7_runtime as runtime
import run_injection_study as runner
from app.core import supervision


def verify(root: str, out: str) -> dict:
    directory = Path(out)
    header = json.loads((directory / "run_header.json").read_text(encoding="utf-8"))
    plan = runner.build_plan(root, cell="c7", c7_gates=header["gates"])
    rows = {}
    with (directory / "checkpoint.jsonl").open(encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                row = json.loads(line)  # torn records are a verification failure
                rows[row["defect_id"]] = row
    problems, scores, usable, failures, raw_calls = [], 0, 0, 0, 0
    if set(rows) != {d["defect_id"] for d in plan}:
        problems.append("Checkpoint defect ids differ from the frozen plan")
    for defect in plan:
        row = rows.get(defect["defect_id"])
        if row is None:
            continue
        if not defect["runnable"]:
            if row.get("status") != "skipped" or row.get("reason") != defect["reason"]:
                problems.append(f"{defect['defect_id']}: exclusion changed")
            continue
        trials = row.get("trials", [])
        key = lambda t: (t["arm"], t["placement"], t["rep"])
        if [key(t) for t in trials] != [key(c) for c in defect["arms"]]:
            problems.append(f"{defect['defect_id']}: cells differ")
        if row.get("status") != "ok" or len({t["session_id"] for t in trials}) != 1:
            problems.append(f"{defect['defect_id']}: incomplete or split session")
        base = runner.inject_defects.state_from_dump(defect["dump_dir"])
        _injected, descriptor = runner.inject_defects.inject(defect["operator"], base, seed=defect["seed"])
        for trial in trials:
            for call in trial.get("local_calls", []):
                if call.get("status") != "ok":
                    continue
                raw_calls += 1
                if hashlib.sha256(call["raw_output"].encode()).hexdigest() != call["raw_sha256"]:
                    problems.append(f"{defect['defect_id']}: raw output hash mismatch")
                if abs(call["prompt_tokens_local"] - call["prompt_tokens_server"]) > 64:
                    problems.append(f"{defect['defect_id']}: token count mismatch/truncation")
            if trial.get("status") != "ok":
                failures += 1
                continue
            usable += 1
            if set(trial.get("served_models", [])) != {runtime.MODEL}:
                problems.append(f"{defect['defect_id']}: wrong served model")
            retried = dict(base)
            stage = descriptor.stage
            retried[runner.inject_defects.OUTPUT_KEY[stage]] = trial["retried_output"]
            reproduced = runner.score_repair.score(descriptor, base, retried).to_dict()
            if reproduced != trial["outcome"]:
                problems.append(f"{defect['defect_id']} {trial['arm']} {trial['rep']}: score mismatch")
            else:
                scores += 1
            if supervision.measure(stage, retried) != trial["post_facts"]:
                problems.append(f"{defect['defect_id']}: post-measurement mismatch")
    result = {"passed": not problems, "defect_rows": len(rows),
              "trials_planned": runner.plan_summary(plan)["trials"],
              "trials_usable": usable, "trials_excluded": failures,
              "offline_scores_agree": scores, "raw_calls_checked": raw_calls,
              "problems": problems}
    (directory / "verification.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default="out_study")
    ap.add_argument("--out", default="out_study/T2L")
    args = ap.parse_args()
    result = verify(args.root, args.out)
    print(json.dumps(result, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
