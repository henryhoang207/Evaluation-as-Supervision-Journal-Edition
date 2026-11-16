"""Gate command for study cells: the RUN_QUEUE.md rules as code.

    python scripts/cell.py list
    python scripts/cell.py preflight <cell> [--skip-suite]
    python scripts/cell.py launch    <cell> --estimate <tokens>
    python scripts/cell.py status    <cell>
    python scripts/cell.py verify    <cell>

``preflight`` is the build gate (Rules 1-3, 6), ``launch`` starts the detached
run (Rule 5) and refuses unless preflight passes, ``verify`` is the verify gate
(Rule 4). Each appends a row to ``out_study/ledger.jsonl`` and ``verify`` prints
a draft RUN_QUEUE log line. The command works from any directory.

A new cell is one entry in ``CELLS`` below, naming its section 0.1 amendment.
A preparation-only entry may reserve an unfiled amendment; it cannot launch
live. Release requires the approved amendment to be committed and pushed.
The S5 trial cell additionally requires its separate freeze tag.

Nothing here commits, pushes or edits a document.
"""

from __future__ import annotations

import argparse
import ctypes
import datetime as dt
import glob
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
from collections import Counter
from dataclasses import dataclass

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(BACKEND)
PREREG = "docs/paper/PREREGISTRATION.md"
FROZEN_DIRS = ("backend/out_study/T2", "backend/out_study/T2T")
LEDGER = "out_study/ledger.jsonl"
CORE_TRIALS = 1167            # PREREGISTRATION section 6; RUN_QUEUE Rule 2
REVIEW_CAP = 500              # loader.MAX_REVIEW_HARD_CEILING; never truncate a p90 base
FLASH = "gemini-2.5-flash"
REPLICATION_MODEL = "gemini-3.5-flash-lite"

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


@dataclass(frozen=True)
class Spec:
    name: str
    kind: str                       # "injection" | "tier1" | "harvest"
    out: str                        # result directory, relative to backend/
    amendment: str | None           # section 0.1 id; None = filed at prereg-freeze
    model: str | None               # the one model every call must be served by
    frozen: bool = False            # never run again, never written
    runner_cell: str | None = None  # run_injection_study.py --cell
    root: str = "out_study"         # dump root (tier1: the bank's root)
    analysis: str | None = None     # repair_analysis.py --cell
    samples: tuple[str, ...] = ()   # harvest: the sample lists, in batch order
    marker: str | None = None       # text the amendment row must contain (default: out)
    preparing: bool = False         # offline preparation only; live launch is forbidden
    freeze_tag: str | None = None   # a separately frozen replication protocol

    @property
    def checkpoint(self) -> str:
        sub = "A/checkpoint.jsonl" if self.kind == "harvest" else "checkpoint.jsonl"
        return f"{self.out}/{sub}"


CELLS = {s.name: s for s in (
    # S5: A15 preparation protocol releases bases only. Amendment-in-HEAD and
    # upstream gates still apply; trials stay preparing until the separate
    # prereg-fl-freeze completion. Registration alone never authorizes a run.
    Spec("flashlite_bases", "harvest", "out_study/FL", "A15", REPLICATION_MODEL,
         samples=("out_study/sample.json",), marker="out_study/FL/A"),
    Spec("flashlite", "injection", "out_study/T2FL", "A15", REPLICATION_MODEL,
         runner_cell="flashlite", root="out_study/FL", analysis="flashlite",
         preparing=True, freeze_tag="prereg-fl-freeze"),
    Spec("core", "injection", "out_study/T2", None, None, frozen=True,
         runner_cell="core", analysis="core"),
    Spec("thinking", "injection", "out_study/T2T", "A12", FLASH, frozen=True,
         runner_cell="thinking", analysis="thinking"),
    Spec("a0fill", "injection", "out_study/T2A0", "A13", FLASH,
         runner_cell="a0fill", analysis="a0fill"),
    Spec("thinking_a0", "injection", "out_study/T2TA0", "A13", FLASH,
         runner_cell="thinking_a0", analysis="thinking_a0"),
    Spec("tier1", "tier1", "out_study/T1", "A8", None, analysis="tier1", marker="Tier-1"),
    Spec("tier1h", "tier1", "out_study/T1H", "A14", FLASH, root="out_study/H",
         analysis="tier1_pooled", marker="T1H"),
    Spec("harvest_h", "harvest", "out_study/H", "A14", FLASH,
         samples=("out_study/H/sample_batch1.json", "out_study/H/sample_batch2.json"),
         marker="out_study/H/A"),
)}


# ── helpers ───────────────────────────────────────────────────────────────────

_MODULES: dict[str, object] = {}


def _load(name: str, rel: str):
    """Import a script by path, once. The runners import each other this way."""
    if name not in _MODULES:
        for p in (BACKEND, os.path.join(BACKEND, "scripts")):
            if p not in sys.path:
                sys.path.insert(0, p)
        if name in sys.modules:
            _MODULES[name] = sys.modules[name]
        else:
            spec = importlib.util.spec_from_file_location(name, os.path.join(BACKEND, "scripts", rel))
            module = importlib.util.module_from_spec(spec)
            sys.modules[name] = module
            spec.loader.exec_module(module)
            _MODULES[name] = module
    return _MODULES[name]


def injection_runner():
    return _load("run_injection_study", "run_injection_study.py")


def tier1_runner():
    return _load("run_tier1_replay", "run_tier1_replay.py")


def _git(*args: str) -> tuple[int, str]:
    proc = subprocess.run(["git", *args], cwd=REPO, capture_output=True)
    return proc.returncode, proc.stdout.decode("utf-8", "replace").strip()


def read_rows(path: str) -> list[dict]:
    """Every parseable row of a checkpoint, in file order."""
    rows = []
    if not os.path.exists(path):
        return rows
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue  # a torn final line from a hard kill
    return rows


def last_by(rows: list[dict], key: str) -> dict[str, dict]:
    """The last row per key: a resumed defect supersedes its earlier row."""
    return {r[key]: r for r in rows if r.get(key)}


def tokens_in(rows: list[dict]) -> int:
    total = 0
    for r in rows:
        if isinstance(r.get("trials"), list):
            total += sum(t.get("total_tokens") or 0 for t in r["trials"])
        else:
            total += r.get("total_tokens") or 0
    return total


def tokens_spent(root: str = "out_study") -> dict:
    """``total_tokens`` over every checkpoint under ``root`` (Rule 6), all rows counted."""
    by_dir = {}
    for path in sorted(glob.glob(os.path.join(root, "**", "checkpoint*.jsonl"), recursive=True)):
        n = tokens_in(read_rows(path))
        if n:
            by_dir[os.path.relpath(os.path.dirname(path), root).replace("\\", "/")] = n
    return {"total": sum(by_dir.values()), "by_dir": by_dir}


def append_ledger(ledger: str, event: str, spec: Spec, **fields) -> dict:
    row = {"at": dt.datetime.now().isoformat(timespec="seconds"), "event": event,
           "cell": spec.name, "head": _git("rev-parse", "--short", "HEAD")[1], **fields}
    os.makedirs(os.path.dirname(os.path.abspath(ledger)), exist_ok=True)
    with open(ledger, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    return row


def _m(n: int) -> str:
    return f"{n / 1e6:.2f} M"


# ── gate checks ───────────────────────────────────────────────────────────────

_AMENDMENT_ROW = re.compile(r"^\|\s*\*\*(A\d+)\*\*\s*\|\s*\*\*(\d{4}-\d{2}-\d{2})\*\*\s*\|(.*)$",
                            re.MULTILINE)


def amendment_rows(prereg_text: str) -> dict[str, dict]:
    """The section 0.1 table: amendment id -> date and row text."""
    return {m.group(1): {"date": m.group(2), "text": m.group(3)}
            for m in _AMENDMENT_ROW.finditer(prereg_text)}


def check_amendment_text(spec: Spec, prereg_text: str) -> tuple[bool, str]:
    if spec.amendment is None:
        return True, "filed in the frozen pre-registration itself (no section 0.1 amendment)"
    row = amendment_rows(prereg_text).get(spec.amendment)
    if not row:
        return False, f"section 0.1 has no row for {spec.amendment}"
    marker = spec.marker or spec.out
    if marker not in row["text"]:
        return False, f"{spec.amendment} ({row['date']}) does not mention {marker!r}"
    return True, f"{spec.amendment}, dated {row['date']}, names {marker}"


def check_amendment(spec: Spec) -> tuple[bool, str]:
    """Rule 1: the amendment is in HEAD, unmodified on disk, and pushed."""
    rc, text = _git("show", f"HEAD:{PREREG}")
    if rc:
        return False, f"cannot read {PREREG} at HEAD"
    ok, detail = check_amendment_text(spec, text)
    if not ok:
        return ok, detail
    if _git("status", "--porcelain", "--", PREREG)[1]:
        return False, f"{detail}; but {PREREG} has uncommitted changes"
    rc, last = _git("rev-list", "-1", "HEAD", "--", PREREG)
    if rc or not last:
        return False, f"{detail}; but no commit touches {PREREG}"
    if _git("merge-base", "--is-ancestor", last, "@{upstream}")[0]:
        return False, f"{detail}; but its commit {last[:7]} is not on the upstream branch (not pushed)"
    return True, f"{detail}; committed in {last[:7]} and pushed"


def check_replication_freeze(spec: Spec) -> tuple[bool, str]:
    """S5 trials require the separate freeze tag, with sources and bases pinned."""
    if not spec.freeze_tag:
        return True, "no separate replication freeze required"
    tag = spec.freeze_tag
    rc, commit = _git("rev-parse", "--verify", f"refs/tags/{tag}^{{commit}}")
    if rc:
        return False, f"missing replication freeze tag {tag}"
    if _git("merge-base", "--is-ancestor", commit, "HEAD")[0]:
        return False, f"{tag} is not an ancestor of HEAD"
    if _git("merge-base", "--is-ancestor", commit, "@{upstream}")[0]:
        return False, f"{tag}'s commit is not on the upstream branch"
    rc, text = _git("show", f"{tag}:{PREREG}")
    if rc or not check_amendment_text(spec, text)[0]:
        return False, f"{tag} does not contain the replication amendment"
    paths = ["backend/" + spec.root + "/A", "backend/out_study/sample.json",
             "backend/scripts/run_injection_study.py", "backend/scripts/run_study.py",
             "backend/scripts/flashlite_protocol.py", "backend/scripts/analysis/repair_analysis.py",
             "backend/scripts/analysis/power.py", "backend/scripts/inject_defects.py",
             "backend/scripts/arms.py", "backend/scripts/analysis/score_repair.py"]
    if _git("cat-file", "-e", f"{tag}:backend/{spec.root}/A/checkpoint.jsonl")[0]:
        return False, f"{tag} has no model-specific base checkpoint"
    if _git("diff", "--quiet", tag, "--", *paths)[0] or _git("status", "--porcelain", "--", *paths)[1]:
        return False, f"replication sources or bases differ from {tag}"
    return True, f"{tag} contains the amendment, sources and own-model bases"


def check_frozen() -> tuple[bool, str]:
    """Exact: the frozen checkpoints equal HEAD, with no stray files beside them."""
    dirty = _git("status", "--porcelain", "--", *FROZEN_DIRS)[1]
    if dirty:
        return False, "frozen checkpoints differ from HEAD: " + "; ".join(dirty.splitlines()[:5])
    return True, "out_study/T2 and out_study/T2T match HEAD"


_PROBE = r"""
import importlib.util, json, os, sys
sys.path.insert(0, os.getcwd()); sys.path.insert(0, os.path.join(os.getcwd(), "scripts"))
def load(name, rel):
    spec = importlib.util.spec_from_file_location(name, os.path.join("scripts", rel))
    m = importlib.util.module_from_spec(spec); sys.modules[name] = m; spec.loader.exec_module(m); return m
runner = load("run_injection_study", "run_injection_study.py")
model, cell = sys.argv[1], sys.argv[2]
from app.core import llm_config
from app.agents import base_agent
from app.data import loader
out = {"configured": llm_config.is_configured(), "max_reviews": loader.MAX_REVIEWS,
       "code_pin": runner.PINNED_MODEL.get(cell)}
if model:
    runner.pin_model_env(model)
    out.update(primary=llm_config.primary_model(), fallback=llm_config.fallback_model(),
               fallback_disabled=base_agent.fallback_disabled())
    try:
        agent = runner._agent_for("reasoning_agent")
        out.update(agent_model=agent._model, agent_fallback=agent._fallback_model)
    except Exception as exc:
        out["agent_error"] = f"{type(exc).__name__}: {exc}"
print("PROBE " + json.dumps(out))
"""


def probe_environment(spec: Spec) -> dict:
    """What a run would see, read in a child process so the pins do not leak here."""
    proc = subprocess.run([sys.executable, "-c", _PROBE, spec.model or "", spec.runner_cell or ""],
                          cwd=BACKEND, capture_output=True, timeout=300)
    for line in reversed(proc.stdout.decode("utf-8", "replace").splitlines()):
        if line.startswith("PROBE "):
            return json.loads(line[6:])
    return {"error": proc.stderr.decode("utf-8", "replace")[-400:]}


def check_pins(spec: Spec, probe: dict) -> tuple[bool, str]:
    if "error" in probe:
        return False, "environment probe failed: " + probe["error"]
    if not spec.model:
        return False, "no model is pinned for this cell (add `model` to its CELLS entry)"
    wrong = [f"{k}={probe.get(k)!r}" for k in ("primary", "fallback") if probe.get(k) != spec.model]
    if not probe.get("fallback_disabled"):
        wrong.append("LLM_DISABLE_FALLBACK is off")
    if "agent_error" in probe:
        wrong.append("agent not built: " + probe["agent_error"])
    else:
        wrong += [f"{k}={probe.get(k)!r}" for k in ("agent_model", "agent_fallback")
                  if probe.get(k) != spec.model]
    if spec.kind == "injection" and probe.get("code_pin") != spec.model:
        wrong.append(f"run_injection_study.PINNED_MODEL[{spec.runner_cell!r}]={probe.get('code_pin')!r}")
    if wrong:
        return False, f"expected {spec.model} everywhere: " + ", ".join(wrong)
    how = "pinned in code" if spec.kind == "injection" else "passed as --model"
    return True, (f"{spec.model} for OPENAI_MODEL, OPENAI_FALLBACK_MODEL, agent._model and "
                  f"agent._fallback_model; LLM_DISABLE_FALLBACK=1 ({how})")


def harvest_expected(spec: Spec, samples: tuple[str, ...] | None = None) -> list[dict]:
    study = _load("run_study", "run_study.py")
    out = []
    for path in samples or spec.samples:
        with open(os.path.join(BACKEND, path), encoding="utf-8") as fh:
            out += study.businesses_from_sample(json.load(fh))
    return out


def check_review_cap(spec: Spec, probe: dict) -> tuple[bool, str]:
    cap = probe.get("max_reviews")
    if cap != REVIEW_CAP:
        return False, f"MAX_REVIEW_SAMPLE resolves to {cap}, not {REVIEW_CAP}"
    if spec.kind == "harvest":
        biggest = max((b.get("review_count") or 0) for b in harvest_expected(spec))
        if biggest > cap:
            return False, f"largest sampled business has {biggest} reviews, above the cap {cap}"
        return True, f"MAX_REVIEW_SAMPLE={cap}; largest sampled business has {biggest} reviews"
    return True, f"MAX_REVIEW_SAMPLE={cap}"


_PLANS: dict[str, list[dict]] = {}


def build_plan(spec: Spec) -> list[dict]:
    """The runner's own plan for the cell, built once per process and only read."""
    if spec.name not in _PLANS:
        if spec.kind == "injection":
            _PLANS[spec.name] = injection_runner().build_plan(spec.root, cell=spec.runner_cell)
        elif spec.kind == "tier1":
            _PLANS[spec.name] = tier1_runner().build_plan(spec.root)
        else:
            raise ValueError(f"{spec.kind} cells have no trial plan")
    return _PLANS[spec.name]


def expected_rows(spec: Spec, plan: list[dict]) -> set[str]:
    """Defects the checkpoint must hold a row for (runnable or recorded as skipped)."""
    if spec.kind == "injection":
        runner = injection_runner()
        return {d["defect_id"] for d in plan if d["runnable"] or not runner.not_in_pass(d)}
    return {d["defect_id"] for d in plan}


def planned_trials(plan: list[dict]) -> int:
    return sum(len(d["arms"]) for d in plan if d["runnable"])


def check_plan(spec: Spec) -> tuple[bool, str, dict]:
    if spec.kind == "harvest":
        n = len(harvest_expected(spec))
        return True, f"{n} businesses in {len(spec.samples)} sample lists", {"businesses": n}
    plan = build_plan(spec)
    info = {"rows": len(expected_rows(spec, plan)), "trials": planned_trials(plan),
            "runnable": sum(1 for d in plan if d["runnable"])}
    if spec.kind == "injection":
        runner = injection_runner()
        problems = runner.verify_order(plan)
        core = runner.plan_summary(runner.build_plan("out_study", cell="core"))["trials"]
        info["core_trials"] = core
        if problems:
            return False, f"order violations: {problems[:3]}", info
        if core != CORE_TRIALS:
            return False, f"the core plan prints {core} trials, not {CORE_TRIALS} (Rule 2)", info
        detail = (f"{info['runnable']} runnable defects, {info['rows']} rows, {info['trials']} trials; "
                  f"order OK; core plan still {core}")
    else:
        summary = tier1_runner().plan_summary(plan)
        info["cells"] = summary["cells"]
        if summary["not_reproduced"]:
            return False, f"{summary['not_reproduced']} bank defects do not reproduce their retry", info
        detail = (f"{info['runnable']} runnable defects in {summary['cells']} cells, "
                  f"{info['trials']} trials {summary['trials_by_arm']}")
    return True, detail, info


def runner_argv(spec: Spec, out: str | None = None, dry_run: bool = False,
                sample: str | None = None) -> list[str]:
    py = [sys.executable, "-u"]
    if spec.kind == "injection":
        argv = py + ["scripts/run_injection_study.py", "--cell", spec.runner_cell]
        if spec.root != "out_study":
            argv += ["--root", spec.root]
        if out:
            argv += ["--out", out]
    elif spec.kind == "tier1":
        argv = py + ["scripts/run_tier1_replay.py", "--root", spec.root, "--out", out or spec.out]
        if spec.model:
            argv += ["--model", spec.model]
    else:
        if not sample and len(spec.samples) == 1:
            sample = spec.samples[0]
        if not sample:
            raise ValueError("a harvest run needs --sample (one batch list)")
        if sample not in spec.samples:
            raise ValueError("harvest sample must be one of the registered sample lists")
        argv = py + ["scripts/run_study.py", "--phase", "A", "--sample", sample,
                     "--out", out or spec.out]
        if spec.model:
            argv += ["--model", spec.model]
    if dry_run:
        argv.append("--dry-run")
    return argv


def check_dry_run(spec: Spec, plan_info: dict) -> tuple[bool, str]:
    """The runner's own dry run, into a temporary directory: rows, trials, sessions."""
    if spec.kind == "harvest":
        return True, "not applicable (the harvest plan is the sample list)"
    with tempfile.TemporaryDirectory(prefix=f"cell_{spec.name}_dry_") as tmp:
        proc = subprocess.run(runner_argv(spec, out=tmp, dry_run=True), cwd=BACKEND,
                              capture_output=True, timeout=1800)
        if proc.returncode:
            return False, "dry run failed: " + proc.stderr.decode("utf-8", "replace")[-300:]
        rows = last_by(read_rows(os.path.join(tmp, "checkpoint.jsonl")), "defect_id")
    ran = [r for r in rows.values() if r.get("trials")]
    trials = sum(len(r["trials"]) for r in ran)
    split = [r["defect_id"] for r in ran if len({t.get("session_id") for t in r["trials"]}) != 1]
    ok = len(rows) == plan_info["rows"] and trials == plan_info["trials"] and not split
    return ok, (f"{len(rows)}/{plan_info['rows']} rows, {trials}/{plan_info['trials']} trials, "
                f"{'one session per defect' if not split else f'{len(split)} defects span sessions'}")


def check_suite() -> tuple[bool, str]:
    proc = subprocess.run([sys.executable, "-m", "pytest", "-m", "not integration", "-q"],
                          cwd=BACKEND, capture_output=True)
    tail = proc.stdout.decode("utf-8", "replace").strip().splitlines()[-1:] or ["no output"]
    return proc.returncode == 0, tail[0]


def progress(spec: Spec) -> dict:
    """Rows done against the plan, read from the checkpoint as it stands."""
    rows = read_rows(os.path.join(BACKEND, spec.checkpoint))
    if spec.kind == "harvest":
        done = {k for k, r in last_by(rows, "business_id").items() if r.get("status") == "ok"}
        want = {b["business_id"] for b in harvest_expected(spec)}
        return {"done": len(done & want), "expected": len(want), "tokens": tokens_in(rows),
                "errors": sum(1 for r in last_by(rows, "business_id").values()
                              if r.get("status") != "ok")}
    last = last_by(rows, "defect_id")
    want = expected_rows(spec, build_plan(spec))
    done = {k for k, r in last.items() if r.get("status") in ("ok", "skipped")}
    trials = [t for r in last.values() for t in r.get("trials") or []]
    return {"done": len(done & want), "expected": len(want), "tokens": tokens_in(rows),
            "trials": len(trials), "errors": sum(1 for t in trials if t.get("status") != "ok")}


# ── preflight ─────────────────────────────────────────────────────────────────

def preflight(spec: Spec, skip_suite: bool = False) -> dict:
    checks: list[dict] = []

    def add(name, result):
        ok, detail = result[0], result[1]
        checks.append({"check": name, "ok": bool(ok), "detail": detail})
        print(f"  [{'ok' if ok else 'FAIL'}] {name}: {detail}", flush=True)
        return result

    print(f"preflight {spec.name} -> {spec.out}")
    add("not frozen", (not spec.frozen, "this cell is frozen and is never run again"
                       if spec.frozen else "cell may be run"))
    add("released", (not spec.preparing, "preparation-only: A15 approval is pending"
                     if spec.preparing else "cell is released"))
    add("replication freeze", check_replication_freeze(spec))
    add("frozen checkpoints", check_frozen())
    add("amendment (Rule 1)", check_amendment(spec))
    probe = probe_environment(spec)
    add("model pins", check_pins(spec, probe))
    add("review cap", check_review_cap(spec, probe))
    add("LLM configured", (bool(probe.get("configured")), "OPENAI_API_KEY is set"
                           if probe.get("configured") else "no API key in the environment"))
    try:
        plan_result = check_plan(spec)
    except (ValueError, FileNotFoundError) as exc:
        plan_result = (False, str(exc), {})
    plan = add("plan (Rules 2-3)", plan_result)
    add("dry run", check_dry_run(spec, plan[2]) if plan[0] else (False, "skipped: plan failed"))
    if plan[0]:
        state = progress(spec)
        pending = state["expected"] - state["done"]
        add("checkpoint", (True, f"{state['done']}/{state['expected']} rows done, {pending} pending"))
    else:
        pending = None
        add("checkpoint", (False, "unavailable: plan failed; no denominator is inferred"))
    add("fast suite", (True, "skipped by --skip-suite") if skip_suite else check_suite())
    spent = tokens_spent(os.path.join(BACKEND, "out_study"))
    print(f"  tokens in every checkpoint: {_m(spent['total'])} (Rule 6: log the estimate before launch)")
    passed = all(c["ok"] for c in checks)
    print("PREFLIGHT " + ("PASS" if passed else "FAIL"))
    return {"passed": passed, "checks": checks, "pending": pending, "suite_run": not skip_suite,
            "tokens_spent": spent["total"]}


# ── launch ────────────────────────────────────────────────────────────────────

_DETACHED_PROCESS = 0x00000008
_CREATE_NEW_PROCESS_GROUP = 0x00000200
_CREATE_BREAKAWAY_FROM_JOB = 0x01000000
_ES_CONTINUOUS, _ES_SYSTEM_REQUIRED = 0x80000000, 0x00000001


def _inside(path: str, parent: str) -> bool:
    path, parent = os.path.realpath(path), os.path.realpath(parent)
    return path == parent or path.startswith(parent + os.sep)


def spawn_detached(argv: list[str], log: str) -> tuple[int, bool]:
    """Start argv detached with output in ``log``. Returns (pid, left the parent's job)."""
    with open(log, "ab") as fh:
        kwargs = dict(cwd=BACKEND, stdin=subprocess.DEVNULL, stdout=fh, stderr=subprocess.STDOUT,
                      close_fds=True)
        if os.name != "nt":
            return subprocess.Popen(argv, start_new_session=True, **kwargs).pid, True
        flags = _DETACHED_PROCESS | _CREATE_NEW_PROCESS_GROUP
        try:
            return subprocess.Popen(argv, creationflags=flags | _CREATE_BREAKAWAY_FROM_JOB,
                                    **kwargs).pid, True
        except OSError:
            return subprocess.Popen(argv, creationflags=flags, **kwargs).pid, False


def launch(spec: Spec, estimate: int | None, ledger: str, dry_run: bool = False,
           out: str | None = None, sample: str | None = None, skip_suite: bool = False) -> int:
    if spec.preparing and not dry_run:
        print("REFUSED: this cell is preparation-only; A15 approval and release are pending.")
        return 1
    if spec.frozen:
        print(f"REFUSED: {spec.name} is frozen ({spec.out} is never altered).")
        return 1
    if dry_run:
        if not out or _inside(os.path.join(BACKEND, out), os.path.join(BACKEND, "out_study")):
            print("REFUSED: a dry run needs --out outside out_study (dry-run rows are appended "
                  "to whatever checkpoint they are given).")
            return 1
    else:
        if out:
            print("REFUSED: a live run writes to the cell's own directory; --out is for dry runs.")
            return 1
        if estimate is None:
            print("REFUSED: pass --estimate <tokens> so the pre-run estimate is logged (Rule 6).")
            return 1
        report = preflight(spec, skip_suite=skip_suite)
        if not report["passed"]:
            print("REFUSED: preflight failed.")
            return 1
        if not report["pending"]:
            print("REFUSED: the checkpoint is complete; there is nothing to run.")
            return 1
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    log = os.path.join(tempfile.gettempdir(), f"cell_{spec.name}_{stamp}.log")
    argv = runner_argv(spec, out=out, dry_run=dry_run, sample=sample)
    # Options go before the cell: argparse hands everything after it to the runner.
    wrapper = [sys.executable, "-u", os.path.abspath(__file__), "_exec",
               "--ledger", ledger, "--log", log, spec.name, "--"] + argv
    pid, broke_away = spawn_detached(wrapper, log)
    append_ledger(ledger, "launch", spec, pid=pid, log=log, dry_run=dry_run, argv=argv[2:],
                  estimate_tokens=estimate, left_parent_job=broke_away,
                  tokens_spent_before=tokens_spent(os.path.join(BACKEND, "out_study"))["total"])
    print(f"launched {spec.name}{' (dry run)' if dry_run else ''}: PID {pid}, log {log}")
    if not broke_away:
        print("note: the process could not leave this session's job, so it dies if the "
              "desktop app restarts. Resume is safe: finished defects are skipped.")
    print(f"next: python scripts/cell.py status {spec.name}")
    return 0


def _exec(spec: Spec, ledger: str, log: str, argv: list[str]) -> int:
    """The detached wrapper: keep the machine awake, run, record the exit."""
    if spec.preparing and "--dry-run" not in argv:
        print("REFUSED: this cell is preparation-only.")
        return 1
    if os.name == "nt":
        ctypes.windll.kernel32.SetThreadExecutionState(_ES_CONTINUOUS | _ES_SYSTEM_REQUIRED)
    env = dict(os.environ, LLM_DISABLE_FALLBACK="1", PYTHONUNBUFFERED="1", PYTHONIOENCODING="utf-8")
    if spec.kind == "harvest":
        env["MAX_REVIEW_SAMPLE"] = str(REVIEW_CAP)
    if spec.model == REPLICATION_MODEL:
        env["MAX_REVIEW_SAMPLE"] = str(REVIEW_CAP)
        env["RANDOM_SEED"] = "42"  # set before loader.py is imported
    try:
        rc = subprocess.call(argv, cwd=BACKEND, env=env)
    finally:
        if os.name == "nt":
            ctypes.windll.kernel32.SetThreadExecutionState(_ES_CONTINUOUS)
    append_ledger(ledger, "exit", spec, returncode=rc, log=log)
    print(f"[cell.py] runner exited with code {rc}")
    return rc


# ── verify ────────────────────────────────────────────────────────────────────

def _served_problem(spec: Spec, served) -> bool:
    return bool(spec.model) and set(served or []) != {spec.model}


def verify_injection(spec: Spec, rows: list[dict], only: set[str] | None = None) -> dict:
    """Rule 4 for an injection cell: plan coverage, sessions, models, offline re-score."""
    runner = injection_runner()
    inj, score_repair, supervision = (sys.modules["inject_defects"], sys.modules["score_repair"],
                                      runner.supervision)
    plan = {d["defect_id"]: d for d in build_plan(spec)}
    if only is not None:
        plan = {k: v for k, v in plan.items() if k in only}
    last = last_by(rows, "defect_id")
    want = {k for k, d in plan.items() if d["runnable"] or not runner.not_in_pass(d)}
    problems, status, models = [], Counter(), Counter()
    missing = sorted(want - set(last))
    if missing:
        problems.append(f"missing rows: {len(missing)}, e.g. {missing[:3]}")
    extra = sorted(set(last) - want) if only is None else []
    if extra:
        problems.append(f"unexpected rows: {extra[:3]}")
    n_trials = n_ok = agree_score = agree_facts = multi = 0
    for did, d in plan.items():
        if not d["runnable"] or did not in last:
            continue
        r = last[did]
        trials = r.get("trials") or []
        planned = [(c["arm"], c.get("placement"), c.get("reasoning_effort"), c["rep"]) for c in d["arms"]]
        got = [(t["arm"], t.get("placement"), t.get("reasoning_effort"), t["rep"]) for t in trials]
        if planned != got:
            problems.append(f"{did}: trials differ from the plan")
        if len({t.get("session_id") for t in trials}) != 1:
            problems.append(f"{did}: more than one session")
        if r.get("status") != "ok":
            problems.append(f"{did}: row status {r.get('status')}")
        base = inj.state_from_dump(d["dump_dir"])
        _, descriptor = inj.inject(d["operator"], base, seed=d["seed"])
        stage = descriptor.stage
        later = supervision.AGENT_SEQUENCE[supervision.AGENT_SEQUENCE.index(stage) + 1:]
        for t in trials:
            n_trials += 1
            status[t["status"]] += 1
            if t["status"] != "ok":
                continue
            n_ok += 1
            multi += (t.get("attempts_made") or 0) > 1
            models[", ".join(sorted(set(t.get("served_models") or [])))] += 1
            label = f"{did} {t['arm']} r{t['rep']}"
            if _served_problem(spec, t.get("served_models")):
                problems.append(f"{label}: served by {t.get('served_models')}")
            state = dict(base)
            state[inj.OUTPUT_KEY[stage]] = t["retried_output"]
            for s in later:
                if s in inj.OUTPUT_KEY:
                    state[inj.OUTPUT_KEY[s]] = None
            if score_repair.score(descriptor, base, state).to_dict() == t["outcome"]:
                agree_score += 1
            else:
                problems.append(f"{label}: offline re-score disagrees")
            if json.loads(json.dumps(supervision.measure(stage, state))) == t["post_facts"]:
                agree_facts += 1
            else:
                problems.append(f"{label}: offline post_facts disagree")
    return {"rows": len(set(last) & want), "rows_expected": len(want), "trials": n_trials,
            "trials_planned": planned_trials(list(plan.values())), "status": dict(status),
            "n_ok": n_ok, "rescore_agree": agree_score, "facts_agree": agree_facts,
            "multi_attempt": multi, "served_models": dict(models), "tokens": tokens_in(rows),
            "problems": problems}


_TIER1_KEYS = ("accepted", "target_resolved", "post_verdict", "trace_resolved_content", "post_fired")


def verify_tier1(spec: Spec, rows: list[dict]) -> dict:
    """Rule 4 for a Tier-1 replay: plan coverage, sessions, models, offline re-judge."""
    t1 = tier1_runner()
    plan = {d["defect_id"]: d for d in build_plan(spec)}
    last = last_by(rows, "defect_id")
    problems, status, models = [], Counter(), Counter()
    missing = sorted(set(plan) - set(last))
    if missing:
        problems.append(f"missing rows: {len(missing)}, e.g. {missing[:3]}")
    extra = sorted(set(last) - set(plan))
    if extra:
        problems.append(f"unexpected rows: {extra[:3]}")
    n_trials = n_ok = agree = multi = 0
    for did, d in plan.items():
        if not d["runnable"] or did not in last:
            continue
        r = last[did]
        trials = r.get("trials") or []
        if [(c["arm"], c["rep"]) for c in d["arms"]] != [(t["arm"], t["rep"]) for t in trials]:
            problems.append(f"{did}: trials differ from the plan")
        if len({t.get("session_id") for t in trials}) != 1:
            problems.append(f"{did}: more than one session")
        if r.get("status") != "ok":
            problems.append(f"{did}: row status {r.get('status')}")
        state = t1.inject_defects.state_from_dump(d["dump_dir"])
        for t in trials:
            n_trials += 1
            status[t["status"]] += 1
            if t["status"] != "ok":
                continue
            n_ok += 1
            multi += (t.get("attempts_made") or 0) > 1
            models[", ".join(sorted(set(t.get("served_models") or [])))] += 1
            label = f"{did} {t['arm']} r{t['rep']}"
            if _served_problem(spec, t.get("served_models")):
                problems.append(f"{label}: served by {t.get('served_models')}")
            verdict = t1.judge(d, state, t["retried_output"])
            if all(verdict[k] == t.get(k) for k in _TIER1_KEYS):
                agree += 1
            else:
                problems.append(f"{label}: offline re-judge disagrees")
    return {"rows": len(set(last) & set(plan)), "rows_expected": len(plan), "trials": n_trials,
            "trials_planned": planned_trials(list(plan.values())), "status": dict(status),
            "n_ok": n_ok, "rescore_agree": agree, "multi_attempt": multi,
            "served_models": dict(models), "tokens": tokens_in(rows), "problems": problems}


def verify_harvest(spec: Spec, rows: list[dict], expected: list[dict]) -> dict:
    """Rule 4 for a Phase-A harvest: every sampled business ran whole, on one model."""
    last = last_by(rows, "business_id")
    want = {b["business_id"]: b for b in expected}
    problems, models = [], Counter()
    missing = sorted(set(want) - set(last))
    if missing:
        problems.append(f"missing businesses: {len(missing)}, e.g. {missing[:3]}")
    extra = sorted(set(last) - set(want))
    if extra:
        problems.append(f"businesses outside the sample lists: {extra[:3]}")
    for bid in sorted(set(want) & set(last)):
        r = last[bid]
        models[", ".join(sorted(set(r.get("served_models") or [])))] += 1
        if r.get("status") != "ok" or r.get("pipeline_status") != "complete":
            problems.append(f"{bid}: status {r.get('status')}, pipeline {r.get('pipeline_status')}")
        if _served_problem(spec, r.get("served_models")):
            problems.append(f"{bid}: served by {r.get('served_models')}")
        if r.get("fallback_calls"):
            problems.append(f"{bid}: {r['fallback_calls']} fallback calls")
        if r.get("loaded_review_count") != r.get("expected_review_count"):
            problems.append(f"{bid}: loaded {r.get('loaded_review_count')} of "
                            f"{r.get('expected_review_count')} reviews (truncated base)")
        if r.get("expected_review_count") != want[bid].get("review_count"):
            problems.append(f"{bid}: sample lists {want[bid].get('review_count')} reviews, "
                            f"row expected {r.get('expected_review_count')}")
    kept = [last[b] for b in set(want) & set(last)]
    return {"rows": len(kept), "rows_expected": len(want),
            "calls": sum(r.get("llm_calls") or 0 for r in kept),
            "would_retry": sum(1 for r in kept if r.get("would_retry_stages")),
            "loaded_by_stratum": dict(sorted(Counter(
                f"{r.get('stratum')}={r.get('loaded_review_count')}" for r in kept).items())),
            "served_models": dict(models), "tokens": tokens_in(rows), "problems": problems}


def run_verify(spec: Spec, checkpoint: str | None = None) -> dict:
    rows = read_rows(checkpoint or os.path.join(BACKEND, spec.checkpoint))
    if spec.kind == "injection":
        return verify_injection(spec, rows)
    if spec.kind == "tier1":
        return verify_tier1(spec, rows)
    return verify_harvest(spec, rows, harvest_expected(spec))


def write_analysis(spec: Spec, rewrite: bool = False) -> tuple[bool, str]:
    """Rule 4: the analysis, written with --json.

    A first verify writes ``<out>/analysis.json``. A repeat writes to a
    temporary file and reports whether it reproduces the stored one, so
    re-verifying never changes a committed result unless ``rewrite`` is given.
    """
    if not spec.analysis or spec.frozen:
        return True, "not written (frozen cell)" if spec.frozen else "no analysis for this cell"
    target = os.path.join(BACKEND, spec.out, "analysis.json")
    exists = os.path.exists(target)
    with tempfile.TemporaryDirectory(prefix="cell_analysis_") as tmp:
        dest = target if (rewrite or not exists) else os.path.join(tmp, "analysis.json")
        argv = [sys.executable, "scripts/analysis/repair_analysis.py",
                "--cell", spec.analysis, "--json", dest]
        if spec.root != "out_study":
            argv += ["--root", spec.root]
        proc = subprocess.run(argv,
                              cwd=BACKEND, capture_output=True)
        if proc.returncode:
            return False, "analysis failed: " + proc.stderr.decode("utf-8", "replace")[-300:]
        if dest == target:
            return True, f"written to {spec.out}/analysis.json"
        with open(dest, "rb") as a, open(target, "rb") as b:
            same = a.read() == b.read()
    return same, (f"reproduces {spec.out}/analysis.json byte for byte" if same else
                  f"differs from the stored {spec.out}/analysis.json (pass --rewrite-analysis to replace it)")


def log_line(spec: Spec, v: dict, analysis: str) -> str:
    """A draft RUN_QUEUE log entry: the mechanical facts only."""
    today = dt.date.today().isoformat()
    models = "; ".join(f"{k or 'none'} x{n}" for k, n in v["served_models"].items())
    if spec.kind == "harvest":
        body = (f"{v['rows']}/{v['rows_expected']} businesses `status ok`, `pipeline complete`; "
                f"served by {models}; loaded reviews by stratum {v['loaded_by_stratum']}; "
                f"{v['calls']} calls, **{_m(v['tokens'])} tokens**; "
                f"{v['would_retry']} businesses carry a would-retry.")
    else:
        body = (f"{v['rows']}/{v['rows_expected']} rows, {v['n_ok']}/{v['trials_planned']} trials ok, "
                f"one session per defect, served by {models}; offline re-score "
                f"{v['rescore_agree']}/{v['n_ok']}"
                + (f" and post-facts {v['facts_agree']}/{v['n_ok']}" if "facts_agree" in v else "")
                + f"; {v['multi_attempt']} multi-attempt trials; **{_m(v['tokens'])} tokens**. "
                f"Analysis: {analysis}.")
    return f"- {today} — **{spec.name} verified** (`{spec.out}`). {body}"


def verify(spec: Spec, ledger: str, checkpoint: str | None = None, rewrite: bool = False,
           skip_analysis: bool = False) -> int:
    print(f"verify {spec.name} <- {checkpoint or spec.checkpoint}")
    v = run_verify(spec, checkpoint)
    frozen_ok, frozen_detail = check_frozen()
    if not frozen_ok:
        v["problems"].append(frozen_detail)
    for key in ("rows", "trials", "n_ok", "rescore_agree", "facts_agree", "calls", "multi_attempt"):
        if key in v:
            suffix = {"rows": f"/{v['rows_expected']}",
                      "trials": f"/{v.get('trials_planned')}"}.get(key, "")
            print(f"  {key}: {v[key]}{suffix}")
    if v.get("status"):
        print(f"  trial status: {v['status']}")
    print(f"  served models: {v['served_models']}")
    print(f"  tokens: {v['tokens']:,} ({_m(v['tokens'])})")
    if spec.kind != "harvest" and v["trials"] != v["trials_planned"]:
        v["problems"].append(f"{v['trials']} trials recorded, {v['trials_planned']} planned")
    not_ok = {k: n for k, n in (v.get("status") or {}).items() if k != "ok"}
    if not_ok:
        print(f"  WARNING: trials not ok {not_ok}: they are exclusions, and resume does not re-run them")
    analysis = "not run"
    if v["problems"]:
        analysis = "skipped: the checkpoint did not verify"
    elif checkpoint or skip_analysis:
        analysis = "skipped"
    else:
        ok, analysis = write_analysis(spec, rewrite)
        if not ok:
            v["problems"].append("analysis: " + analysis)
    print(f"  analysis: {analysis}")
    passed = not v["problems"]
    for p in v["problems"][:20]:
        print(f"  ! {p}")
    append_ledger(ledger, "verify", spec, passed=passed, analysis=analysis,
                  **{k: v[k] for k in v if k != "problems"}, problems=v["problems"][:20])
    print("VERIFY " + ("PASS" if passed else f"FAIL ({len(v['problems'])})"))
    if passed:
        print("\ndraft RUN_QUEUE log line:\n" + log_line(spec, v, analysis))
    return 0 if passed else 1


# ── status ────────────────────────────────────────────────────────────────────

def _alive(pid: int) -> bool:
    if os.name != "nt":
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False
    out = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/NH"], capture_output=True)
    return str(pid) in out.stdout.decode("utf-8", "replace")


def status(spec: Spec, ledger: str) -> int:
    try:
        state = progress(spec)
    except (ValueError, FileNotFoundError) as exc:
        print(f"{spec.name}: not ready: {exc}")
        return 1
    line = f"{spec.name}: {state['done']}/{state['expected']} rows done"
    if "trials" in state:
        line += f", {state['trials']} trials"
    print(f"{line}, {state['errors']} not ok, {_m(state['tokens'])} tokens")
    launches = [r for r in read_rows(ledger) if r.get("cell") == spec.name and r.get("event") == "launch"]
    if launches:
        last = launches[-1]
        print(f"last launch {last['at']}: PID {last['pid']} "
              f"({'running' if _alive(last['pid']) else 'not running'}), log {last['log']}")
        if os.path.exists(last["log"]):
            with open(last["log"], encoding="utf-8", errors="replace") as fh:
                for tail in fh.read().splitlines()[-5:]:
                    print("    " + tail)
    return 0


# ── cli ───────────────────────────────────────────────────────────────────────

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="command", required=True)
    sub.add_parser("list", help="the registered cells")
    for name in ("preflight", "launch", "status", "verify", "_exec"):
        p = sub.add_parser(name)
        p.add_argument("cell", choices=sorted(CELLS))
        p.add_argument("--ledger", default=LEDGER)
        if name in ("preflight", "launch"):
            p.add_argument("--skip-suite", action="store_true",
                           help="skip the fast test suite (run it at least once per change)")
        if name == "launch":
            p.add_argument("--estimate", type=int, help="pre-run token estimate, logged (Rule 6)")
            p.add_argument("--dry-run", action="store_true")
            p.add_argument("--out", help="dry runs only: a directory outside out_study")
            p.add_argument("--sample", help="harvest only: the batch list to run")
        if name == "verify":
            p.add_argument("--checkpoint", help="verify this file instead (no analysis is written)")
            p.add_argument("--rewrite-analysis", action="store_true")
            p.add_argument("--skip-analysis", action="store_true")
        if name == "_exec":
            p.add_argument("--log", required=True)
            p.add_argument("argv", nargs=argparse.REMAINDER)
    args = ap.parse_args(argv)
    os.chdir(BACKEND)
    if args.command == "list":
        for s in CELLS.values():
            print(f"{s.name:12} {s.kind:9} {s.out:18} {s.amendment or 'prereg':7} "
                  f"{s.model or '-':17} {'frozen' if s.frozen else 'preparing' if s.preparing else ''}")
        return 0
    spec = CELLS[args.cell]
    if args.command == "preflight":
        report = preflight(spec, skip_suite=args.skip_suite)
        append_ledger(args.ledger, "preflight", spec, **report)
        return 0 if report["passed"] else 1
    if args.command == "launch":
        return launch(spec, args.estimate, args.ledger, dry_run=args.dry_run, out=args.out,
                      sample=args.sample, skip_suite=args.skip_suite)
    if args.command == "status":
        return status(spec, args.ledger)
    if args.command == "verify":
        return verify(spec, args.ledger, checkpoint=args.checkpoint,
                      rewrite=args.rewrite_analysis, skip_analysis=args.skip_analysis)
    return _exec(spec, args.ledger, args.log, [a for a in args.argv if a != "--"])


if __name__ == "__main__":
    sys.exit(main())
