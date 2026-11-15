"""PreToolUse guard for this repository's standing rules.

Claude Code runs this before a shell or file tool call (wired in
``.claude/settings.json``). It reads the hook payload on stdin and prints a
permission decision, or prints nothing to let the call through.

Rules:

* deny  -- ``git commit`` / ``tag`` / ``push`` and history rewrites, and
           ``gh`` commands that publish, unless the author's go-ahead is fresh.
           "No commit, tag or push without my go-ahead" (CLAUDE.md, Git).
           The author grants ``GO_AHEAD_MINUTES`` by running, in their own
           terminal:  ``python backend/scripts/claude_guard.py --go-ahead``
           That touches ``.claude/git-go-ahead``. Claude's own tool calls
           cannot create the file: this guard denies them. (A hook "ask" is
           not used because bypass-permissions mode does not prompt for it.)
* deny  -- any write into the frozen checkpoints ``backend/out_study/T2``
           (cell ``core``, 1,167 trials) and ``backend/out_study/T2T``
           (1,224 trials), and a study runner pointed at them.
* deny  -- any write to ``docs/paper/main.tex`` (the accepted conference
           paper). ``docs/paper/journal/main.tex`` is not covered.
* deny  -- a file-tool path, or a shell command, that names the shadow copy of
           this repository: the same path with ``Tai lieu`` in another Unicode
           normalisation, which has no ``.git`` (CLAUDE.md, Environment traps).

Shell commands are matched by pattern, so the shell rules are a best effort: a
script that opens a frozen file itself is not seen here. ``cell.py`` checks the
frozen directories exactly, with ``git status``.

The script uses the standard library only and fails open: if it raises, the
tool call proceeds.
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
import unicodedata

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))

GO_AHEAD_MINUTES = 15
MARKER_NAME = "git-go-ahead"
MARKER_REL = ".claude/" + MARKER_NAME
GRANT_HINT = (f" The author grants {GO_AHEAD_MINUTES} minutes by running, in their own terminal: "
              "python backend/scripts/claude_guard.py --go-ahead")


def marker_path(repo: str = REPO) -> str:
    return os.path.join(repo, ".claude", MARKER_NAME)


def go_ahead_is_fresh(marker: str) -> bool:
    try:
        age = time.time() - os.path.getmtime(marker)
    except OSError:
        return False
    return -60 <= age <= GO_AHEAD_MINUTES * 60

FROZEN_DIRS = ("backend/out_study/T2", "backend/out_study/T2T")
NEVER_EDIT = ("docs/paper/main.tex",)

WRITE_TOOLS = {"Write", "Edit", "MultiEdit", "NotebookEdit"}
READ_TOOLS = {"Read"}

# Cells of run_injection_study.py whose default --out is a frozen directory.
FROZEN_RUNNER_CELLS = {"core": "T2", "thinking": "T2T"}

SHORT_PATH = r"C:\Users\hoanh\OneDrive\TAILIU~1\CSMATE~1\COS30018\Project\COS300~1.1_M"


def _fold(path: str) -> str:
    return unicodedata.normalize("NFC", path).replace("\\", "/").rstrip("/").casefold()


def _is_under(path: str, root: str) -> bool:
    p, r = _fold(path), _fold(root)
    return p == r or p.startswith(r + "/")


def classify_path(file_path: str, cwd: str | None = None, repo: str = REPO) -> tuple[str, str]:
    """Where a path points: ("repo", relative path), ("shadow", ""), or ("outside", "").

    ``realpath`` expands 8.3 short names and keeps the on-disk spelling, so the
    real repository and its shadow stay distinct here even though they print
    alike. A path is the shadow when it is not inside the repository but
    becomes so once both are normalised to NFC.
    """
    if not os.path.isabs(file_path):
        file_path = os.path.join(cwd or os.getcwd(), file_path)
    real = os.path.realpath(file_path)
    exact = real.replace("\\", "/").rstrip("/").casefold()
    root = repo.replace("\\", "/").rstrip("/").casefold()
    if exact == root or exact.startswith(root + "/"):
        return "repo", exact[len(root):].lstrip("/")
    if _is_under(real, repo):
        return "shadow", ""
    return "outside", ""


def _in_dirs(rel: str, dirs: tuple[str, ...]) -> str | None:
    rel = rel.casefold()
    for d in dirs:
        d = d.casefold()
        if rel == d or rel.startswith(d + "/"):
            return d
    return None


def decide_file(tool: str, tool_input: dict, cwd: str | None, repo: str = REPO):
    path = tool_input.get("file_path") or tool_input.get("notebook_path")
    if not isinstance(path, str) or not path:
        return None
    where, rel = classify_path(path, cwd, repo)
    if where == "shadow":
        return ("deny", "This path is the shadow copy of the repository (same name, another Unicode "
                        "normalisation, no .git). Use the 8.3 short path: " + SHORT_PATH)
    if tool not in WRITE_TOOLS or where != "repo":
        return None
    if rel.casefold() == MARKER_REL:
        return ("deny", "Only the author creates the go-ahead file." + GRANT_HINT)
    frozen = _in_dirs(rel, FROZEN_DIRS)
    if frozen:
        return ("deny", f"{frozen} is frozen: cell core (1,167 trials) and T2T (1,224) are never "
                        "altered. Write a new cell under a dated section 0.1 amendment instead.")
    if _in_dirs(rel, NEVER_EDIT):
        return ("deny", f"{rel} is the accepted conference paper and is never edited. "
                        "The journal paper is docs/paper/journal/main.tex.")
    return None


# ── shell commands ────────────────────────────────────────────────────────────

# A command position: start of the string, or after a separator / subshell opener.
_AT_CMD = r"(?:^|[;&|(\n`{]|\$\()\s*(?:[A-Za-z_]\w*=\S*\s+)*"
_GIT = _AT_CMD + r"git(?:\.exe)?\b((?:\s+(?:-[Cc]\s+\S+|--[\w-]+(?:=\S+)?))*)\s+([a-z][\w-]*)\b([^;&|\n]*)"
_GIT_RE = re.compile(_GIT, re.IGNORECASE)
_GH_RE = re.compile(_AT_CMD + r"gh(?:\.exe)?\s+(pr\s+(?:create|merge|close|comment|review|edit)"
                              r"|release\s+(?:create|delete|edit|upload)"
                              r"|repo\s+(?:create|delete|rename|edit)|issue\s+(?:create|comment|close|edit))\b",
                    re.IGNORECASE)

_GIT_ALWAYS_ASK = {"commit", "push", "rebase", "filter-branch", "filter-repo", "cherry-pick",
                   "revert", "am", "merge", "update-ref"}
_TAG_READ_ONLY = re.compile(r"(?:^|\s)(?:-l|--list|-n\d*|--contains|--points-at|--merged|"
                            r"--no-merged|--sort\S*|-v|--verify)(?:\s|=|$)")

_FROZEN_PATH = r"out_study[\\/]+(?:T2T|T2)(?=[\\/\s\"'`;&|)]|$)"
_FROZEN_RE = re.compile(_FROZEN_PATH, re.IGNORECASE)
_MAIN_TEX = r"(?<![\w.-])docs[\\/]+paper[\\/]+main\.tex\b"
_MAIN_TEX_RE = re.compile(_MAIN_TEX, re.IGNORECASE)
_REDIRECT = r"(?<![0-9&])>{1,2}\s*[\"']?[^\s\"'|;&]*"
_DESTRUCTIVE = re.compile(
    r"(?:^|[\s;&|(])(?:rm|rmdir|mv|truncate|tee|touch|shred|"
    r"Remove-Item|Move-Item|Rename-Item|Set-Content|Add-Content|Clear-Content|Out-File|"
    r"New-Item)\s|(?:^|\s)sed\s+(?:-\S*\s+)*-\S*i|(?:^|\s)perl\s+(?:-\S*\s+)*-\S*i",
    re.IGNORECASE)
_COPY = re.compile(r"(?:^|[\s;&|(])(?:cp|copy|Copy-Item|xcopy|robocopy)\b", re.IGNORECASE)
_SEGMENT_SPLIT = re.compile(r"&&|\|\||[;\n|]")
_SHADOW_NAME = unicodedata.normalize("NFC", "T\u00e0i li\u1ec7u")


def _git_decision(command: str):
    for m in _GIT_RE.finditer(command):
        sub, rest = m.group(2).lower(), m.group(3) or ""
        if sub in _GIT_ALWAYS_ASK:
            return ("ask", f"git {sub}: no commit, tag or push, and no history rewrite, "
                           "without the author's go-ahead.")
        if sub == "tag":
            words = rest.split()
            if words and not _TAG_READ_ONLY.search(" " + rest + " "):
                return ("ask", "git tag creates or deletes a tag: needs the author's go-ahead.")
        if sub == "reset" and re.search(r"--hard\b", rest):
            return ("ask", "git reset --hard discards uncommitted work; backend/out_study is "
                           "partly uncommitted and cost API budget.")
        if sub == "clean" and re.search(r"(?:^|\s)-\w*f", rest):
            return ("ask", "git clean -f deletes untracked files, including the author's own.")
        if sub == "branch" and re.search(r"(?:^|\s)-\w*D\b", rest):
            return ("ask", "git branch -D deletes a branch that may hold unmerged work.")
    if _GH_RE.search(command):
        return ("ask", "This gh command publishes or changes something on GitHub.")
    return None


def _runner_decision(segment: str):
    if not re.search(r"run_injection_study\.py\b", segment):
        return None
    if re.search(r"(?:^|\s)--plan-only\b", segment):
        return None
    out = re.search(r"--out(?:=|\s+)[\"']?([^\s\"']+)", segment)
    if out:
        if _FROZEN_RE.search(out.group(1).rstrip("\\/") + "/"):
            return ("deny", "run_injection_study.py would write into a frozen checkpoint "
                            "(out_study/T2 or T2T).")
        return None
    cell = re.search(r"--cell(?:=|\s+)[\"']?([\w-]+)", segment)
    name = cell.group(1) if cell else "core"
    if name in FROZEN_RUNNER_CELLS:
        return ("deny", f"run_injection_study.py --cell {name} writes into the frozen "
                        f"out_study/{FROZEN_RUNNER_CELLS[name]}. Pass --plan-only, or --out to a "
                        "temporary directory for a dry run.")
    return None


def _write_target_decision(segment: str, pattern: re.Pattern, what: str):
    if not pattern.search(segment):
        return None
    for m in re.finditer(_REDIRECT, segment):
        if pattern.search(m.group(0) + " "):
            return ("deny", f"The command redirects output into {what}.")
    if re.search(r"--json(?:=|\s+)[\"']?[^\s\"']*", segment):
        target = re.search(r"--json(?:=|\s+)[\"']?([^\s\"']*)", segment).group(1)
        if pattern.search(target + " "):
            return ("deny", f"The command writes its result into {what}.")
    if _DESTRUCTIVE.search(segment):
        return ("deny", f"The command modifies or deletes {what}.")
    if _COPY.search(segment):
        words = segment.split()
        if words and pattern.search(words[-1].strip("\"'") + " "):
            return ("deny", f"The command copies into {what}.")
    return None


def decide_shell(command: str):
    if not isinstance(command, str) or not command.strip():
        return None
    if (re.search(re.escape(MARKER_NAME) + r"(?![\w.-])", command)
            or re.search(r"claude_guard\.py\S*\s[^;&|\n]*--go-ahead", command)):
        return ("deny", "Only the author grants the git go-ahead, from their own terminal.")
    # The real directory is stored decomposed, so the composed spelling, typed
    # literally, can only be the shadow.
    if _SHADOW_NAME in command:
        return ("deny", "The command spells the repository path with the composed form of "
                        "'Tai lieu', which is the shadow copy with no .git. Use "
                        "\"$(git rev-parse --show-toplevel)\" or the 8.3 short path: " + SHORT_PATH)
    frozen_what = "a frozen checkpoint (out_study/T2 or T2T; cell core and T2T are never altered)"
    for segment in _SEGMENT_SPLIT.split(command):
        hit = (_runner_decision(segment)
               or _write_target_decision(segment, _FROZEN_RE, frozen_what)
               or _write_target_decision(segment, _MAIN_TEX_RE,
                                         "docs/paper/main.tex (the accepted conference paper)"))
        if hit:
            return hit
    return _git_decision(command)


def decide(payload: dict, repo: str = REPO, marker: str | None = None):
    """The decision for one tool call: ("deny", reason) or None to let it through.

    The rules above mark go-ahead actions as "ask". Here that becomes a pass
    while the author's go-ahead file is fresh, and a deny otherwise.
    """
    tool = payload.get("tool_name") or ""
    tool_input = payload.get("tool_input") or {}
    if not isinstance(tool_input, dict):
        return None
    verdict = None
    if tool in WRITE_TOOLS or tool in READ_TOOLS:
        verdict = decide_file(tool, tool_input, payload.get("cwd"), repo)
    elif isinstance(tool_input.get("command"), str):
        verdict = decide_shell(tool_input["command"])
    if verdict and verdict[0] == "ask":
        if go_ahead_is_fresh(marker or marker_path(repo)):
            return None
        return ("deny", verdict[1] + GRANT_HINT)
    return verdict


def grant_go_ahead(marker: str) -> int:
    """Run by the author: start the go-ahead window."""
    os.makedirs(os.path.dirname(marker), exist_ok=True)
    with open(marker, "a", encoding="utf-8"):
        pass
    os.utime(marker, None)
    until = time.strftime("%H:%M", time.localtime(time.time() + GO_AHEAD_MINUTES * 60))
    print(f"git go-ahead granted until {until} ({GO_AHEAD_MINUTES} minutes). "
          f"Delete {marker} to end it sooner.")
    return 0


def main() -> int:
    if "--go-ahead" in sys.argv[1:]:
        args = sys.argv[1:]
        custom = args[args.index("--marker") + 1] if "--marker" in args else None
        return grant_go_ahead(custom or marker_path())
    try:
        payload = json.loads(sys.stdin.buffer.read().decode("utf-8", "replace") or "{}")
        verdict = decide(payload)
    except Exception as exc:  # fail open: a broken guard must not block the session
        sys.stderr.write(f"claude_guard: {type(exc).__name__}: {exc}\n")
        return 0
    if verdict:
        decision, reason = verdict
        sys.stdout.write(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": decision,
            "permissionDecisionReason": reason,
        }}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
