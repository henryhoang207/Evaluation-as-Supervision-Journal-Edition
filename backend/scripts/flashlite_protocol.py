"""Offline provenance checks for S5's own-model bases. No model calls."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

REPLICATION_MODEL = "gemini-3.5-flash-lite"
BACKEND = Path(__file__).resolve().parents[1]


def validate_bases(root: str | Path, sample_path: str | Path | None = None) -> dict:
    """Require the whole fixed sample, untruncated and served by the pinned model.

    Checking only a model name in a command is insufficient: the stored bases
    themselves must have been produced by it. This also refuses absent bases
    instead of returning an empty plan that could be mistaken for N_FL = 0.
    """
    root = Path(root)
    sample_path = Path(sample_path) if sample_path is not None else BACKEND / "out_study/sample.json"
    sample = json.loads(sample_path.read_text(encoding="utf-8"))
    businesses = [{**b, "stratum": s["stratum"]}
                  for s in sample["strata"] for b in s["businesses"]]
    expected = {b["business_id"]: b for b in businesses}
    if not expected or len(expected) != len(businesses):
        raise ValueError("The replication sample must contain unique businesses")
    phase = root / "A"
    checkpoint = phase / "checkpoint.jsonl"
    if not checkpoint.exists():
        raise FileNotFoundError(f"Flash-lite bases are not built: {checkpoint}")
    rows = [json.loads(line) for line in checkpoint.read_text(encoding="utf-8").splitlines() if line.strip()]
    latest = {r["business_id"]: r for r in rows}
    if set(latest) != set(expected):
        raise ValueError("Flash-lite checkpoint does not cover exactly the fixed sample")
    if {p.name for p in phase.iterdir() if p.is_dir()} != set(expected):
        raise ValueError("Flash-lite dump directories do not match the fixed sample")
    fingerprints = {"sample.json": hashlib.sha256(sample_path.read_bytes()).hexdigest(),
                    "A/checkpoint.jsonl": hashlib.sha256(checkpoint.read_bytes()).hexdigest()}
    strata = {}
    for bid, business in sorted(expected.items()):
        row = latest[bid]
        if row.get("status") != "ok" or row.get("pipeline_status") != "complete":
            raise ValueError(f"{bid}: base collection is not complete")
        if row.get("phase") != "A" or row.get("mode") != "observe":
            raise ValueError(f"{bid}: base is not Phase-A observe mode")
        if set(row.get("served_models") or []) != {REPLICATION_MODEL} or row.get("fallback_calls") != 0:
            raise ValueError(f"{bid}: base was not served exclusively by {REPLICATION_MODEL}")
        count = business["review_count"]
        if row.get("loaded_review_count") != count or row.get("expected_review_count") != count:
            raise ValueError(f"{bid}: truncated or mismatched review count (expected {count})")
        if row.get("stratum") != business["stratum"]:
            raise ValueError(f"{bid}: review-count stratum changed")
        if row.get("review_sample_seed") != 42:
            raise ValueError(f"{bid}: review sampling seed is not 42")
        for name in ("analysis", "reasoning", "strategy", "report", "_summary"):
            path = phase / bid / (name + ".json")
            data = path.read_bytes()
            payload = json.loads(data)
            valid = (isinstance(payload, list) and bool(payload)
                     and all(isinstance(item, dict) for item in payload)) if name == "analysis" else isinstance(payload, dict)
            if not valid:
                raise ValueError(f"{bid}: missing or malformed {name} output")
            fingerprints[f"A/{bid}/{name}.json"] = hashlib.sha256(data).hexdigest()
            if name == "_summary":
                config = payload.get("run_config") or {}
                if (config.get("primary_model") != REPLICATION_MODEL or
                        config.get("fallback_model") != REPLICATION_MODEL):
                    raise ValueError(f"{bid}: dump model configuration differs from the pinned model")
                if payload.get("phase") != "A" or payload.get("mode") != "observe":
                    raise ValueError(f"{bid}: dump is not Phase-A observe mode")
                if payload.get("review_sample_seed") != 42:
                    raise ValueError(f"{bid}: dump review sampling seed is not 42")
        label = f"{business['stratum']}={count}"
        strata[label] = strata.get(label, 0) + 1
    digest = hashlib.sha256(json.dumps(fingerprints, sort_keys=True).encode("utf-8")).hexdigest()
    return {"model": REPLICATION_MODEL, "businesses": len(expected),
            "reviews_by_stratum": strata, "bases_sha256": digest}
