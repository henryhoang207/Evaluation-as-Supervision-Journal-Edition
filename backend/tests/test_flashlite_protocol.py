"""S5 provenance and restoration rules, using synthetic files and rows only."""
import importlib.util
import json
import sys
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, BACKEND / path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


protocol = load("flashlite_protocol", "scripts/flashlite_protocol.py")
ra = load("flashlite_analysis_test", "scripts/analysis/repair_analysis.py")
MODEL = protocol.REPLICATION_MODEL


@pytest.fixture
def bases(tmp_path):
    sample = {"strata": [{"stratum": s, "businesses": [{"business_id": bid, "review_count": n}]}
                         for bid, s, n in [("small", "p25", 14), ("large", "p90", 214)]]}
    sample_path = tmp_path / "sample.json"
    sample_path.write_text(json.dumps(sample), encoding="utf-8")
    root = tmp_path / "FL"
    rows = []
    for bid, s, n in [("small", "p25", 14), ("large", "p90", 214)]:
        directory = root / "A" / bid
        directory.mkdir(parents=True)
        for stage in ("analysis", "reasoning", "strategy", "report"):
            output = [{"synthetic": stage} for _ in range(n)] if stage == "analysis" else {"synthetic": stage}
            (directory / (stage + ".json")).write_text(json.dumps(output), encoding="utf-8")
        summary = {"phase": "A", "mode": "observe", "review_sample_seed": 42, "run_config": {
            "primary_model": MODEL, "fallback_model": MODEL}}
        (directory / "_summary.json").write_text(json.dumps(summary), encoding="utf-8")
        rows.append({"business_id": bid, "status": "ok", "pipeline_status": "complete",
                     "phase": "A", "mode": "observe", "stratum": s, "review_sample_seed": 42,
                     "loaded_review_count": n, "expected_review_count": n,
                     "served_models": [MODEL], "fallback_calls": 0})
    checkpoint = root / "A/checkpoint.jsonl"
    checkpoint.write_text("\n".join(map(json.dumps, rows)) + "\n", encoding="utf-8")
    return root, sample_path, rows


def test_own_bases_are_complete_untruncated_and_fingerprinted(bases):
    root, sample, _ = bases
    result = protocol.validate_bases(root, sample)
    assert result["businesses"] == 2
    assert result["reviews_by_stratum"] == {"p90=214": 1, "p25=14": 1}
    before = result["bases_sha256"]
    (root / "A/large/reasoning.json").write_text('{"synthetic":"changed"}', encoding="utf-8")
    assert protocol.validate_bases(root, sample)["bases_sha256"] != before


@pytest.mark.parametrize("change", [
    {"loaded_review_count": 100}, {"served_models": ["gemini-2.5-flash"]},
    {"served_models": []}, {"fallback_calls": 1}, {"mode": "enforce"},
    {"pipeline_status": "halted"}, {"stratum": "p50"}, {"review_sample_seed": 43},
])
def test_wrong_or_truncated_bases_are_rejected(bases, change):
    root, sample, rows = bases
    rows[1].update(change)
    (root / "A/checkpoint.jsonl").write_text("\n".join(map(json.dumps, rows)), encoding="utf-8")
    with pytest.raises(ValueError):
        protocol.validate_bases(root, sample)


def test_dump_configuration_must_match_returned_models(bases):
    root, sample, _ = bases
    path = root / "A/large/_summary.json"
    summary = json.loads(path.read_text())
    summary["run_config"]["fallback_model"] = "gemini-2.5-flash"
    path.write_text(json.dumps(summary), encoding="utf-8")
    with pytest.raises(ValueError, match="configuration"):
        protocol.validate_bases(root, sample)


def test_absent_or_partial_bases_do_not_become_zero_defects(bases):
    root, sample, rows = bases
    with pytest.raises(FileNotFoundError, match="not built"):
        protocol.validate_bases(root / "missing", sample)
    (root / "A/checkpoint.jsonl").write_text(json.dumps(rows[0]), encoding="utf-8")
    with pytest.raises(ValueError, match="exactly the fixed sample"):
        protocol.validate_bases(root, sample)


def synthetic_analysis(monkeypatch, reverse=False, n=12):
    rows, clean = [], {}
    for i in range(n):
        did = f"b{i}:O1"
        output = {"answer": {"a": i, "b": [1, 2]}}
        clean[did] = output
        trials = []
        for arm in ("A0", "A1", "A2"):
            copies = arm == "A0" or arm == ("A2" if reverse else "A1")
            for rep in range(3):
                trials.append({"defect_id": did, "operator": "O1", "stage": "reasoning_agent",
                    "arm": arm, "rep": rep, "condition": "C0", "placement": "P1",
                    "status": "ok", "served_models": [MODEL], "reasoning_effort": None,
                    "attempts_made": 1, "outcome": {"outcome": "repaired"},
                    "retried_output": output if copies else {"paraphrase": i}})
        rows.append({"defect_id": did, "operator": "O1", "trials": trials})
    monkeypatch.setitem(sys.modules, "flashlite_protocol", protocol)
    monkeypatch.setattr(protocol, "validate_bases", lambda root: {"bases_sha256": "synthetic"})
    monkeypatch.setattr(ra, "_clean_outputs", lambda rows, root: clean)
    monkeypatch.setattr(ra, "_strata", lambda root: {f"b{i}": "p90" for i in range(n)})
    return rows, clean


def test_primary_is_restoration_even_when_repair_is_identical(monkeypatch):
    rows, _ = synthetic_analysis(monkeypatch)
    result = ra.analyse_flashlite(rows, root="synthetic/FL")
    primary = result["confirmatory"]
    assert primary["primary_A1_minus_A2"]["estimate"] == 1
    assert primary["primary_A1_minus_A2"]["mcnemar_p"] < 0.05
    assert primary["replicated"] is True
    assert result["secondary_exploratory"]["repair_A1_minus_A2"]["estimate"] == 0
    assert result["secondary_exploratory"]["restoration_by_review_stratum"]["p90|A1"]["rate"] == 1


def test_significant_reverse_effect_is_not_a_replication(monkeypatch):
    rows, _ = synthetic_analysis(monkeypatch, reverse=True)
    result = ra.analyse_flashlite(rows, root="synthetic/FL")["confirmatory"]
    assert result["primary_A1_minus_A2"]["estimate"] == -1
    assert result["primary_A1_minus_A2"]["mcnemar_p"] < 0.05
    assert result["replicated"] is False


def test_missing_reference_is_an_error_instead_of_a_noncopy(monkeypatch):
    rows, clean = synthetic_analysis(monkeypatch)
    clean.pop(rows[0]["defect_id"])
    with pytest.raises(ValueError, match="Missing own-model clean reference"):
        ra.analyse_flashlite(rows, root="synthetic/FL")


@pytest.mark.parametrize("change", [{"served_models": ["gemini-2.5-flash"]},
                                     {"reasoning_effort": "none"}])
def test_primary_refuses_wrong_model_or_reasoning_setting(monkeypatch, change):
    rows, _ = synthetic_analysis(monkeypatch)
    rows[0]["trials"][0].update(change)
    with pytest.raises(ValueError):
        ra.analyse_flashlite(rows, root="synthetic/FL")


def test_losses_keep_the_strict_majority_tie_rule(monkeypatch):
    rows, _ = synthetic_analysis(monkeypatch, n=2)
    a1 = [t for t in rows[0]["trials"] if t["arm"] == "A1"]
    a1[1]["retried_output"] = {"rewrite": 1}
    a1[2]["status"] = "status_error"
    for trial in rows[1]["trials"]:
        if trial["arm"] == "A2":
            trial["status"] = "status_error"
    primary = ra.analyse_flashlite(rows, root="synthetic/FL")["confirmatory"]["primary_A1_minus_A2"]
    assert primary["n_defects"] == 1 and primary["dropped"] == 1
    assert primary["estimate"] == 0.5
    assert primary["discordant"] == {"A1_only": 0, "A2_only": 0}
    assert primary["mcnemar_p"] == 1


def test_analysis_dump_is_a_list_of_review_records(bases):
    root, sample, _ = bases
    (root / "A/large/analysis.json").write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="malformed analysis"):
        protocol.validate_bases(root, sample)


def test_zero_restoration_ceiling_ratio_stays_valid_json(monkeypatch):
    rows, _ = synthetic_analysis(monkeypatch)
    for row in rows:
        for trial in row["trials"]:
            if trial["arm"] == "A0":
                trial["retried_output"] = {"rewrite": True}
    report = ra.analyse_flashlite(rows, root="synthetic/FL")
    ratio = report["secondary_exploratory"]["restoration_A1_over_A0"]
    assert ratio["estimate"] is None and ratio["ci95"] == [None, None]
    json.dumps(report, allow_nan=False)
