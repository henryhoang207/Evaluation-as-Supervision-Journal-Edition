"""The PreToolUse guard (scripts/claude_guard.py): what it asks, denies and lets through."""

import importlib.util
import json
import os
import subprocess
import sys
import unicodedata

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
GUARD_PATH = os.path.join(HERE, "..", "scripts", "claude_guard.py")

spec = importlib.util.spec_from_file_location("claude_guard", GUARD_PATH)
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)


# No go-ahead unless a test grants one: the author's real file must not decide a test.
NO_MARKER = os.path.join(os.path.dirname(GUARD_PATH), "no-such-dir", "absent")


def shell(command, marker=NO_MARKER):
    verdict = guard.decide({"tool_name": "Bash", "tool_input": {"command": command}}, marker=marker)
    return verdict[0] if verdict else None


def file_tool(tool, rel, repo=guard.REPO):
    verdict = guard.decide({"tool_name": tool, "tool_input": {"file_path": os.path.join(repo, rel)}},
                           repo, marker=NO_MARKER)
    return verdict[0] if verdict else None


GIT_WRITES = [
    "git commit -m 'x'",
    'cd "$(git rev-parse --show-toplevel)" && git add a.py && git commit -m "x"',
    "git -C backend commit --amend --no-edit",
    "git push",
    "git push origin main --dry-run",
    "git tag -a prereg-s5 -m 'freeze'",
    "git tag -d prereg-s5",
    "git rebase main",
    "git reset --hard HEAD~1",
    "git clean -fd",
    "git status; git push",
    "gh pr create --title x --body y",
]


@pytest.mark.parametrize("command", GIT_WRITES)
def test_git_writes_are_denied_without_a_go_ahead(command):
    verdict = guard.decide({"tool_name": "Bash", "tool_input": {"command": command}},
                           marker=NO_MARKER)
    assert verdict[0] == "deny" and "--go-ahead" in verdict[1]


@pytest.mark.parametrize("command", GIT_WRITES)
def test_git_writes_pass_while_the_go_ahead_is_fresh(command, tmp_path):
    marker = str(tmp_path / ".claude" / guard.MARKER_NAME)
    assert guard.grant_go_ahead(marker) == 0
    assert shell(command, marker) is None


def test_a_stale_go_ahead_no_longer_counts(tmp_path):
    marker = str(tmp_path / guard.MARKER_NAME)
    guard.grant_go_ahead(marker)
    old = os.path.getmtime(marker) - guard.GO_AHEAD_MINUTES * 60 - 5
    os.utime(marker, (old, old))
    assert shell("git push", marker) == "deny"
    guard.grant_go_ahead(marker)                       # granting again restarts the window
    assert shell("git push", marker) is None


def test_a_go_ahead_does_not_lift_the_other_rules(tmp_path):
    marker = str(tmp_path / guard.MARKER_NAME)
    guard.grant_go_ahead(marker)
    assert shell("rm backend/out_study/T2/checkpoint.jsonl", marker) == "deny"
    assert shell("git add -A && echo x > out_study/T2T/checkpoint.jsonl && git commit -m x",
                 marker) == "deny"


@pytest.mark.parametrize("command", [
    "touch .claude/git-go-ahead",
    "echo ok > .claude/git-go-ahead && git push",
    "New-Item -Force .claude\\git-go-ahead",
    "python backend/scripts/claude_guard.py --go-ahead",
    "venv/Scripts/python.exe scripts/claude_guard.py --go-ahead && git commit -m x",
    "python -c \"open('.claude/git-go-ahead','w')\"",
])
def test_tool_calls_cannot_grant_the_go_ahead(command, tmp_path):
    marker = str(tmp_path / guard.MARKER_NAME)
    guard.grant_go_ahead(marker)                       # even while one is already fresh
    assert shell(command, marker) == "deny"
    assert shell(command) == "deny"


def test_a_longer_file_name_is_not_the_go_ahead_file():
    assert shell("cat memory/git-go-ahead-hook.md") is None
    assert shell("ls .claude/git-go-ahead.bak") is None
    assert shell("cat '.claude/git-go-ahead'") == "deny"


@pytest.mark.parametrize("tool", ["Write", "Edit"])
def test_file_tools_cannot_write_the_go_ahead_file(tool):
    assert file_tool(tool, guard.MARKER_REL) == "deny"


def test_the_grant_command_writes_the_file(tmp_path):
    marker = str(tmp_path / "sub" / guard.MARKER_NAME)
    proc = subprocess.run([sys.executable, GUARD_PATH, "--go-ahead", "--marker", marker],
                          capture_output=True, timeout=30)
    assert proc.returncode == 0 and b"granted until" in proc.stdout
    assert guard.go_ahead_is_fresh(marker)


@pytest.mark.parametrize("command", [
    "git status --short",
    "git log --oneline -5",
    "git diff HEAD -- backend/out_study/T2",
    "git tag",
    "git tag -l 'prereg*'",
    "git tag --contains HEAD",
    "git reset HEAD a.py",
    "git add backend/scripts/cell.py",
    "git show HEAD:docs/paper/PREREGISTRATION.md | head",
    "grep -rn 'git commit' docs/",
    "gh pr view 12",
    "ls",
])
def test_git_reads_pass(command):
    assert shell(command) is None


@pytest.mark.parametrize("command", [
    "rm backend/out_study/T2/checkpoint.jsonl",
    "echo x >> out_study/T2T/checkpoint.jsonl",
    "python scripts/x.py > out_study/T2/analysis.json",
    "sed -i 's/a/b/' out_study/T2/checkpoint.jsonl",
    "cp /tmp/new.jsonl out_study/T2T/checkpoint.jsonl",
    "mv out_study/T2 out_study/T2_old",
    "Remove-Item out_study\\T2\\checkpoint.jsonl",
    "cat a | tee out_study/T2/checkpoint.jsonl",
    "venv/Scripts/python.exe scripts/run_injection_study.py",
    "venv/Scripts/python.exe scripts/run_injection_study.py --dry-run",
    "venv/Scripts/python.exe scripts/run_injection_study.py --cell thinking",
    "python scripts/run_injection_study.py --cell a0fill --out out_study/T2",
    "python scripts/analysis/repair_analysis.py --cell core --json out_study/T2/analysis.json",
    "sed -i 's/a/b/' docs/paper/main.tex",
    "echo x > docs/paper/main.tex",
])
def test_frozen_writes_are_denied(command):
    assert shell(command) == "deny"


@pytest.mark.parametrize("command", [
    "cat out_study/T2/checkpoint.jsonl | head -1",
    "wc -l out_study/T2T/checkpoint.jsonl > /tmp/n.txt",
    "cp out_study/T2/checkpoint.jsonl /tmp/copy.jsonl",
    "rm out_study/T2A0/analysis.json",
    "echo x > out_study/T2TA0/analysis.json",
    "rm /tmp/x && cat out_study/T2/checkpoint.jsonl",
    "venv/Scripts/python.exe scripts/run_injection_study.py --plan-only",
    "venv/Scripts/python.exe scripts/run_injection_study.py --cell thinking --plan-only",
    "venv/Scripts/python.exe scripts/run_injection_study.py --cell a0fill",
    "python scripts/run_injection_study.py --dry-run --out /tmp/dry",
    "python scripts/analysis/repair_analysis.py --cell core --json /tmp/core.json",
    "python scripts/analysis/repair_analysis.py --cell a0fill --json out_study/T2A0/analysis.json",
    "sed -i 's/a/b/' docs/paper/journal/main.tex",
    "cat docs/paper/main.tex",
])
def test_reads_and_other_cells_pass(command):
    assert shell(command) is None


@pytest.mark.parametrize("tool", ["Write", "Edit", "MultiEdit"])
@pytest.mark.parametrize("rel", [
    "backend/out_study/T2/checkpoint.jsonl",
    "backend/out_study/T2/analysis.json",
    "backend/out_study/T2T/checkpoint.jsonl",
    "docs/paper/main.tex",
])
def test_file_tools_cannot_write_frozen_files(tool, rel):
    assert file_tool(tool, rel) == "deny"


@pytest.mark.parametrize("rel", [
    "backend/out_study/T2A0/analysis.json",
    "backend/out_study/T2TA0/checkpoint.jsonl",
    "backend/out_study/T1H/analysis.json",
    "docs/paper/journal/main.tex",
    "docs/paper/RUN_QUEUE.md",
    "backend/scripts/cell.py",
])
def test_file_tools_can_write_elsewhere(rel):
    assert file_tool("Edit", rel) is None


def test_reading_a_frozen_file_is_allowed():
    assert file_tool("Read", "backend/out_study/T2/checkpoint.jsonl") is None


def test_relative_paths_resolve_against_the_hook_cwd():
    payload = {"tool_name": "Write", "cwd": os.path.join(guard.REPO, "backend"),
               "tool_input": {"file_path": "out_study/T2/checkpoint.jsonl"}}
    assert guard.decide(payload)[0] == "deny"


def test_paths_outside_the_repository_pass(tmp_path):
    payload = {"tool_name": "Write", "tool_input": {"file_path": str(tmp_path / "note.txt")}}
    assert guard.decide(payload) is None


def test_shadow_copy_is_denied_for_reads_and_writes(tmp_path):
    """Two directories whose names differ only in Unicode normalisation."""
    real = tmp_path / unicodedata.normalize("NFD", "T\u00e0i li\u1ec7u") / "repo"
    shadow = tmp_path / unicodedata.normalize("NFC", "T\u00e0i li\u1ec7u") / "repo"
    real.mkdir(parents=True)
    shadow.mkdir(parents=True)
    if os.path.samefile(real, shadow):
        pytest.skip("this filesystem normalises names, so no shadow can exist")
    repo = os.path.realpath(real)
    for tool in ("Read", "Write", "Edit"):
        inside = {"tool_name": tool, "tool_input": {"file_path": str(real / "a.md")}}
        ghost = {"tool_name": tool, "tool_input": {"file_path": str(shadow / "a.md")}}
        assert guard.decide(inside, repo) is None
        assert guard.decide(ghost, repo)[0] == "deny"


def test_shell_command_naming_the_shadow_is_denied():
    composed = unicodedata.normalize("NFC", "T\u00e0i li\u1ec7u")
    assert shell(f'cat "C:/Users/x/OneDrive/{composed}/repo/a.md"') == "deny"


def test_short_path_resolves_into_the_repository():
    if not os.path.isdir(guard.SHORT_PATH):
        pytest.skip("8.3 short path is specific to the author's machine")
    for tool, rel, want in (("Write", r"backend\out_study\T2\checkpoint.jsonl", "deny"),
                            ("Write", r"docs\paper\RUN_QUEUE.md", None),
                            ("Read", r"docs\paper\main.tex", None)):
        verdict = guard.decide({"tool_name": tool,
                                "tool_input": {"file_path": os.path.join(guard.SHORT_PATH, rel)}})
        assert (verdict[0] if verdict else None) == want


def _run(payload_bytes):
    return subprocess.run([sys.executable, GUARD_PATH], input=payload_bytes,
                          capture_output=True, timeout=30)


def test_script_prints_a_hook_decision_and_reads_utf8():
    payload = {"tool_name": "Bash",
               "tool_input": {"command": "rm out_study/T2/checkpoint.jsonl  # \u2212 T\u00e0i"}}
    proc = _run(json.dumps(payload, ensure_ascii=False).encode("utf-8"))
    assert proc.returncode == 0
    out = json.loads(proc.stdout)["hookSpecificOutput"]
    assert out["hookEventName"] == "PreToolUse"
    assert out["permissionDecision"] == "deny"
    assert out["permissionDecisionReason"]


def test_script_is_silent_when_it_allows_and_fails_open_on_bad_input():
    proc = _run(json.dumps({"tool_name": "Bash", "tool_input": {"command": "ls"}}).encode())
    assert proc.returncode == 0 and proc.stdout == b""
    for junk in (b"not json", b"", b'{"tool_input": 3}', b"[1, 2]"):
        proc = _run(junk)
        assert proc.returncode == 0 and proc.stdout == b""
