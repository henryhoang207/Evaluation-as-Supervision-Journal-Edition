"""The cell gate command (scripts/cell.py): RUN_QUEUE's rules as checks.

The verify tests run on committed study data and never write beside it: rows are
mutated in memory, and the ledger and every dry-run target live in tmp_path.
"""

import copy
from dataclasses import replace
import importlib.util
import json
import os
import shutil
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.dirname(HERE)

spec = importlib.util.spec_from_file_location("cell", os.path.join(BACKEND, "scripts", "cell.py"))
cell = importlib.util.module_from_spec(spec)
sys.modules["cell"] = cell
spec.loader.exec_module(cell)

HAS_GIT = shutil.which("git") is not None and os.path.isdir(os.path.join(cell.REPO, ".git"))


def _rows(name):
    path = os.path.join(BACKEND, cell.CELLS[name].checkpoint)
    if not os.path.exists(path):
        pytest.skip(f"{path} is not in this checkout")
    return cell.read_rows(path)


# ── the registry ──────────────────────────────────────────────────────────────

def test_frozen_cells_are_exactly_the_frozen_directories():
    frozen = {"backend/" + s.out for s in cell.CELLS.values() if s.frozen}
    assert frozen == set(cell.FROZEN_DIRS)


def test_injection_cells_agree_with_the_runner():
    runner = cell.injection_runner()
    for s in cell.CELLS.values():
        if s.kind != "injection":
            continue
        assert s.out == runner.CELL_OUT[s.runner_cell]
        if not s.frozen:
            assert s.model == runner.PINNED_MODEL[s.runner_cell]


# ── Rule 1: the amendment ─────────────────────────────────────────────────────

TABLE = """
| **A12** | **2026-11-01** | **Sweep** (`--cell thinking` -> `out_study/T2T`): 45 defects | Exploratory |
| **A13** | **2026-11-13** | **S2.** `--cell a0fill` -> `out_study/T2A0`; `out_study/T2TA0` | Exploratory |
| A99 | 2026-11-13 | not an amendment row: no bold id | - |
"""


def test_amendment_rows_reads_the_table():
    rows = cell.amendment_rows(TABLE)
    assert set(rows) == {"A12", "A13"}
    assert rows["A13"]["date"] == "2026-11-13"


def test_amendment_must_exist_and_name_the_cell():
    assert cell.check_amendment_text(cell.CELLS["a0fill"], TABLE)[0]
    assert cell.check_amendment_text(cell.CELLS["core"], TABLE)[0]          # filed at the freeze
    missing = cell.check_amendment_text(cell.CELLS["tier1h"], TABLE)         # A14 not in the table
    assert not missing[0] and "no row for A14" in missing[1]
    wrong = cell.check_amendment_text(
        cell.Spec("x", "injection", "out_study/T9", "A13", cell.FLASH), TABLE)
    assert not wrong[0] and "does not mention" in wrong[1]


def test_every_launchable_cell_is_filed_in_the_preregistration():
    path = os.path.join(cell.REPO, cell.PREREG)
    if not os.path.exists(path):
        pytest.skip("PREREGISTRATION.md is not in this checkout")
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    for s in cell.CELLS.values():
        ok, detail = cell.check_amendment_text(s, text)
        if s.preparing:
            assert s.amendment is not None  # launch is separately pinned closed below
        else:
            assert ok, f"{s.name}: {detail}"


@pytest.mark.skipif(not HAS_GIT, reason="needs the git checkout")
def test_frozen_checkpoints_match_head():
    ok, detail = cell.check_frozen()
    assert ok, detail


# ── Rule 6: tokens ────────────────────────────────────────────────────────────

def test_tokens_count_every_row_of_every_checkpoint(tmp_path):
    (tmp_path / "T9").mkdir()
    (tmp_path / "H" / "A").mkdir(parents=True)
    trial_rows = [{"defect_id": "d1", "trials": [{"total_tokens": 10}, {"total_tokens": None}]},
                  {"defect_id": "d1", "trials": [{"total_tokens": 5}]}]     # a re-run still cost tokens
    (tmp_path / "T9" / "checkpoint.jsonl").write_text(
        "\n".join(json.dumps(r) for r in trial_rows) + '\n{"torn', encoding="utf-8")
    (tmp_path / "H" / "A" / "checkpoint.jsonl").write_text(
        json.dumps({"business_id": "b", "total_tokens": 100}) + "\n", encoding="utf-8")
    spent = cell.tokens_spent(str(tmp_path))
    assert spent == {"total": 115, "by_dir": {"H/A": 100, "T9": 15}}


def test_the_last_row_per_defect_wins():
    rows = [{"defect_id": "d", "status": "error"}, {"defect_id": "d", "status": "ok"}, {"x": 1}]
    assert cell.last_by(rows, "defect_id") == {"d": {"defect_id": "d", "status": "ok"}}


# ── Rule 5: launch refusals (none of these reach a runner) ────────────────────

def test_launch_refuses_a_frozen_cell(tmp_path, capsys):
    for name in ("core", "thinking"):
        assert cell.launch(cell.CELLS[name], 1, str(tmp_path / "l.jsonl")) == 1
        assert cell.launch(cell.CELLS[name], None, str(tmp_path / "l.jsonl"),
                           dry_run=True, out=str(tmp_path)) == 1
    assert "frozen" in capsys.readouterr().out
    assert not (tmp_path / "l.jsonl").exists()


def test_launch_refuses_a_dry_run_into_the_study_directory(tmp_path):
    s = cell.CELLS["a0fill"]
    ledger = str(tmp_path / "l.jsonl")
    assert cell.launch(s, None, ledger, dry_run=True) == 1
    assert cell.launch(s, None, ledger, dry_run=True, out="out_study/T2A0") == 1
    assert cell.launch(s, None, ledger, dry_run=True, out="out_study/scratch") == 1
    assert not os.path.exists(ledger)


def test_live_launch_needs_an_estimate_and_takes_no_out(tmp_path):
    s = cell.CELLS["a0fill"]
    ledger = str(tmp_path / "l.jsonl")
    assert cell.launch(s, None, ledger) == 1
    assert cell.launch(s, 100, ledger, out=str(tmp_path)) == 1
    assert not os.path.exists(ledger)


def test_the_detached_wrapper_parses_its_own_command_line(tmp_path, monkeypatch):
    """launch hands a command to a detached process; that command must run as written."""
    spawned = {}
    monkeypatch.setattr(cell, "spawn_detached",
                        lambda argv, log: spawned.update(argv=argv, log=log) or (4242, True))
    monkeypatch.setattr(cell, "runner_argv",
                        lambda *a, **k: [sys.executable, "-c", "print('runner ran')"])
    ledger = str(tmp_path / "l.jsonl")
    assert cell.launch(cell.CELLS["tier1h"], None, ledger, dry_run=True, out=str(tmp_path / "d")) == 0
    wrapper = spawned["argv"]
    assert wrapper[2].endswith("cell.py") and wrapper[3] == "_exec"
    assert cell.main(wrapper[3:]) == 0
    events = [(r["event"], r.get("pid"), r.get("returncode")) for r in cell.read_rows(ledger)]
    assert events == [("launch", 4242, None), ("exit", None, 0)]


def test_runner_commands():
    a0 = cell.runner_argv(cell.CELLS["a0fill"])
    assert a0[2:] == ["scripts/run_injection_study.py", "--cell", "a0fill"]
    dry = cell.runner_argv(cell.CELLS["a0fill"], out="/tmp/d", dry_run=True)
    assert dry[-3:] == ["--out", "/tmp/d", "--dry-run"]
    t1h = cell.runner_argv(cell.CELLS["tier1h"])
    assert t1h[2:] == ["scripts/run_tier1_replay.py", "--root", "out_study/H",
                       "--out", "out_study/T1H", "--model", cell.FLASH]
    harvest = cell.runner_argv(cell.CELLS["harvest_h"], sample="out_study/H/sample_batch1.json")
    assert harvest[2:] == ["scripts/run_study.py", "--phase", "A", "--sample",
                           "out_study/H/sample_batch1.json", "--out", "out_study/H",
                           "--model", cell.FLASH]
    with pytest.raises(ValueError):
        cell.runner_argv(cell.CELLS["harvest_h"])


def test_a_frozen_cell_never_gets_its_analysis_rewritten():
    assert cell.write_analysis(cell.CELLS["core"], rewrite=True) == (True, "not written (frozen cell)")


# ── Rule 4: verify, harvest ───────────────────────────────────────────────────

HARVEST = cell.Spec("h", "harvest", "out_study/X", "A14", cell.FLASH)


def _harvest():
    expected = [{"business_id": f"b{i}", "review_count": n, "stratum": s}
                for i, (n, s) in enumerate([(14, "p25"), (214, "p90")])]
    rows = [{"business_id": b["business_id"], "stratum": b["stratum"], "status": "ok",
             "pipeline_status": "complete", "expected_review_count": b["review_count"],
             "loaded_review_count": b["review_count"], "served_models": [cell.FLASH],
             "fallback_calls": 0, "llm_calls": 6, "total_tokens": 1000, "would_retry_stages": []}
            for b in expected]
    return rows, expected


def test_harvest_verifies_when_every_business_ran_whole():
    rows, expected = _harvest()
    v = cell.verify_harvest(HARVEST, rows, expected)
    assert v["problems"] == []
    assert (v["rows"], v["rows_expected"], v["calls"], v["tokens"]) == (2, 2, 12, 2000)
    assert v["loaded_by_stratum"] == {"p25=14": 1, "p90=214": 1}


@pytest.mark.parametrize("change, expect", [
    ({"loaded_review_count": 100}, "truncated base"),
    ({"fallback_calls": 2}, "fallback calls"),
    ({"served_models": ["gemini-3.5-flash"]}, "served by"),
    ({"served_models": [cell.FLASH, "gemini-3.5-flash"]}, "served by"),
    ({"pipeline_status": "halted"}, "pipeline halted"),
    ({"status": "error"}, "status error"),
    ({"expected_review_count": 200, "loaded_review_count": 200}, "sample lists 214"),
])
def test_harvest_catches_a_bad_row(change, expect):
    rows, expected = _harvest()
    rows[1].update(change)
    problems = cell.verify_harvest(HARVEST, rows, expected)["problems"]
    assert len(problems) == 1 and expect in problems[0]


def test_harvest_catches_missing_and_stray_businesses():
    rows, expected = _harvest()
    assert "missing businesses" in cell.verify_harvest(HARVEST, rows[:1], expected)["problems"][0]
    stray = rows + [{**rows[0], "business_id": "elsewhere"}]
    assert "outside the sample lists" in cell.verify_harvest(HARVEST, stray, expected)["problems"][0]


# ── Rule 4: verify, Tier-1 replay (committed T1H data) ────────────────────────

def test_tier1h_verifies_as_logged():
    v = cell.verify_tier1(cell.CELLS["tier1h"], _rows("tier1h"))
    assert v["problems"] == []
    assert (v["rows"], v["rows_expected"]) == (8, 8)
    assert (v["trials"], v["trials_planned"], v["n_ok"], v["rescore_agree"]) == (72, 72, 72, 72)
    assert v["served_models"] == {cell.FLASH: 72}
    assert v["tokens"] == 1011159
    assert v["multi_attempt"] == 1


def _mutate_tier1(fn):
    rows = copy.deepcopy(_rows("tier1h"))
    fn(rows)
    return cell.verify_tier1(cell.CELLS["tier1h"], rows)["problems"]


def test_tier1_catches_a_dropped_row():
    problems = _mutate_tier1(lambda rows: rows.pop())
    assert any("missing rows: 1" in p for p in problems)


def test_tier1_catches_a_second_session():
    problems = _mutate_tier1(lambda rows: rows[0]["trials"][-1].update(session_id="another"))
    assert any("more than one session" in p for p in problems)


def test_tier1_catches_another_model():
    problems = _mutate_tier1(
        lambda rows: rows[0]["trials"][0].update(served_models=["gemini-3.5-flash"]))
    assert any("served by" in p for p in problems)


def test_tier1_catches_a_flipped_outcome():
    def flip(rows):
        t = rows[0]["trials"][0]
        t["accepted"] = not t["accepted"]
    problems = _mutate_tier1(flip)
    assert len(problems) == 1 and "re-judge disagrees" in problems[0]


def test_tier1_catches_a_dropped_trial_and_a_failed_row():
    def damage(rows):
        rows[0]["trials"].pop()
        rows[1]["status"] = "error"
    problems = _mutate_tier1(damage)
    assert any("trials differ from the plan" in p for p in problems)
    assert any("row status error" in p for p in problems)


# ── Rule 4: verify, injection cell (committed T2A0 data, three defects) ───────

def _a0fill_sample():
    rows = _rows("a0fill")
    ran = [r for r in rows if r.get("trials")][:3]
    return copy.deepcopy(ran), {r["defect_id"] for r in ran}


def test_injection_cell_verifies_on_committed_rows():
    rows, only = _a0fill_sample()
    v = cell.verify_injection(cell.CELLS["a0fill"], rows, only=only)
    assert v["problems"] == []
    assert v["rows"] == 3 and v["trials"] == v["trials_planned"] == v["n_ok"]
    assert v["rescore_agree"] == v["facts_agree"] == v["n_ok"]


def test_injection_cell_catches_tampering():
    rows, only = _a0fill_sample()
    rows[0]["trials"][0]["outcome"] = {**rows[0]["trials"][0]["outcome"], "repaired": "tampered"}
    rows[1]["trials"][0]["served_models"] = ["gemini-3.5-flash"]
    rows[2]["trials"][-1]["session_id"] = "another"
    problems = cell.verify_injection(cell.CELLS["a0fill"], rows, only=only)["problems"]
    assert any("offline re-score disagrees" in p for p in problems)
    assert any("served by" in p for p in problems)
    assert any("more than one session" in p for p in problems)
    missing = cell.verify_injection(cell.CELLS["a0fill"], rows[:2], only=only)["problems"]
    assert any("missing rows: 1" in p for p in missing)


# ── the ledger and the log line ───────────────────────────────────────────────

def test_ledger_rows_are_appended(tmp_path):
    ledger = str(tmp_path / "sub" / "ledger.jsonl")
    cell.append_ledger(ledger, "verify", cell.CELLS["tier1h"], passed=True)
    cell.append_ledger(ledger, "launch", cell.CELLS["tier1h"], pid=1)
    rows = cell.read_rows(ledger)
    assert [r["event"] for r in rows] == ["verify", "launch"]
    assert rows[0]["cell"] == "tier1h" and rows[0]["passed"] is True and "at" in rows[0]


def test_log_line_states_the_gate_facts():
    v = {"rows": 8, "rows_expected": 8, "n_ok": 72, "trials_planned": 72, "rescore_agree": 72,
         "multi_attempt": 1, "served_models": {cell.FLASH: 72}, "tokens": 1011159}
    line = cell.log_line(cell.CELLS["tier1h"], v, "written")
    for fact in ("tier1h verified", "8/8 rows", "72/72 trials ok", "re-score 72/72",
                 "1.01 M tokens", cell.FLASH):
        assert fact in line


# A preparation-only entry cannot launch, even if other gates are bypassed.
def test_preparing_cells_cannot_launch_even_when_other_checks_are_stubbed(tmp_path, monkeypatch):
    monkeypatch.setattr(cell, "preflight", lambda *a, **kw: {"passed": True, "pending": 1})
    def forbidden(*args, **kwargs):
        raise AssertionError("a preparation-only cell must not spawn a process")
    monkeypatch.setattr(cell, "spawn_detached", forbidden)
    for name in ("flashlite", "flashlite_bases", "flashlite_determinism"):
        spec = replace(cell.CELLS[name], preparing=True)
        assert spec.amendment == "A15"
        assert cell.launch(spec, 100, str(tmp_path / "ledger.jsonl")) == 1
        assert cell._exec(spec, str(tmp_path / "ledger.jsonl"), "unused", ["unused"]) == 1
    assert not (tmp_path / "ledger.jsonl").exists()


def test_a15_repair_trials_stay_closed_while_preparatory_cells_release():
    bases, trials = cell.CELLS["flashlite_bases"], cell.CELLS["flashlite"]
    assert bases.amendment == trials.amendment == "A15"
    assert not bases.preparing and bases.freeze_tag is None
    assert not cell.CELLS["flashlite_determinism"].preparing
    assert trials.preparing and trials.freeze_tag == "prereg-fl-freeze"
    ok, _ = cell.check_amendment_text(bases, "")
    assert not ok  # releasing the flag does not replace the filed-amendment gate


def test_flashlite_commands_use_their_own_root_and_fixed_sample():
    argv = cell.runner_argv(cell.CELLS["flashlite"])
    assert argv[2:] == ["scripts/run_injection_study.py", "--cell", "flashlite",
                        "--root", "out_study/FL"]
    bases = cell.runner_argv(cell.CELLS["flashlite_bases"])
    assert bases[2:] == ["scripts/run_study.py", "--phase", "A", "--sample", "out_study/sample.json",
                         "--out", "out_study/FL", "--model", "gemini-3.5-flash-lite"]
    with pytest.raises(ValueError):
        cell.runner_argv(cell.CELLS["flashlite_bases"], sample="out_study/H/sample_batch1.json")


def test_replication_trials_need_their_separate_freeze_tag(monkeypatch):
    monkeypatch.setattr(cell, "_git", lambda *args: (1, "missing"))
    ok, detail = cell.check_replication_freeze(cell.CELLS["flashlite"])
    assert not ok and "missing replication freeze tag" in detail


def test_replication_freeze_rejects_changed_sources(monkeypatch):
    def git(*args):
        if args[0] == "rev-parse":
            return 0, "abc123"
        if args[0] == "show":
            return 0, '| **A15** | **2026-11-16** | S5 out_study/T2FL | Replication |'
        if args[0] == "diff":
            return 1, ""
        return 0, ""
    monkeypatch.setattr(cell, "_git", git)
    ok, detail = cell.check_replication_freeze(cell.CELLS["flashlite"])
    assert not ok and "differ" in detail


def test_missing_bases_make_preflight_fail_cleanly(monkeypatch):
    monkeypatch.setattr(cell, "probe_environment", lambda spec: {"configured": True})
    monkeypatch.setattr(cell, "check_pins", lambda *a: (True, "synthetic"))
    monkeypatch.setattr(cell, "check_review_cap", lambda *a: (True, "synthetic"))
    monkeypatch.setattr(cell, "tokens_spent", lambda *a: {"total": 0})
    def absent(spec):
        raise FileNotFoundError("FL/A is not built")
    monkeypatch.setattr(cell, "check_plan", absent)
    result = cell.preflight(cell.CELLS["flashlite"], skip_suite=True)
    assert not result["passed"]
    assert any("FL/A is not built" in c["detail"] for c in result["checks"])


@pytest.mark.parametrize("name", ["flashlite_bases", "flashlite", "flashlite_determinism"])
def test_flashlite_wrapper_pins_the_review_seed_before_import(tmp_path, monkeypatch, name):
    seen = {}
    monkeypatch.setenv("RANDOM_SEED", "999")
    def run(argv, cwd, env):
        seen.update(env)
        return 0
    monkeypatch.setattr(cell.subprocess, "call", run)
    spec = cell.CELLS[name]
    assert cell._exec(spec, str(tmp_path / "ledger.jsonl"), "unused", ["unused", "--dry-run"]) == 0
    assert seen["RANDOM_SEED"] == "42"
    assert seen["MAX_REVIEW_SAMPLE"] == "500"
    assert seen["LLM_DISABLE_FALLBACK"] == "1"


def test_replication_freeze_requires_power_and_measurement_artifacts(monkeypatch):
    def git(*args):
        if args[0] == "rev-parse":
            return 0, "abc123"
        if args[0] == "show":
            return 0, '| **A15** | **2026-11-16** | S5 out_study/T2FL | Replication |'
        if args[0] == "cat-file" and args[-1].endswith('/power.json'):
            return 1, ""
        return 0, ""
    monkeypatch.setattr(cell, "_git", git)
    ok, detail = cell.check_replication_freeze(cell.CELLS["flashlite"])
    assert not ok and "power.json" in detail


def test_measurement_launch_dispatches_only_its_collector(tmp_path, monkeypatch):
    spec = cell.CELLS["flashlite_determinism"]
    seen = []
    monkeypatch.setattr(cell, "preflight", lambda *a, **kw: {"passed": True, "pending":20})
    monkeypatch.setattr(cell, "tokens_spent", lambda *a: {"total":100})
    monkeypatch.setattr(cell, "spawn_detached", lambda argv, log: seen.append(argv) or (123,True))
    ledger = str(tmp_path / "ledger.jsonl")
    assert cell.launch(spec, 520402, ledger, skip_suite=True) == 0
    assert "scripts/flashlite_determinism.py" in seen[0]
    assert cell.runner_argv(spec)[2:] == ["scripts/flashlite_determinism.py", "--root", "out_study/FL",
        "--out", "out_study/FL/determinism", "--model", cell.REPLICATION_MODEL]
    row = cell.read_rows(ledger)[0]
    assert row["cell"] == "flashlite_determinism" and row["estimate_tokens"] == 520402
