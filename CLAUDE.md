# CLAUDE.md

Auto-loaded guidance for Claude Code (and any AI agent) working in this
repository. **Read [`AGENTS.md`](AGENTS.md) before changing architecture, agent
contracts, data handling, or the plan** — it holds the binding project rules.
This file is the practical "how to work here" companion, and is the single one:
the former `docs/CLAUDE.md` has been folded in here.

## What lives here

Two tracks share one repository.

1. **The system** (COS30018 Intelligent Systems, Group 4.1 — *complete*). A
   four-stage LLM pipeline over the Yelp Open Dataset: analysis → reasoning →
   strategy → report, each an agent with a Pydantic contract, routed through a
   **deterministic supervisor hub**
   ([`backend/app/core/supervision.py`](backend/app/core/supervision.py)) that
   measures every stage output against upstream state and returns
   `proceed | proceed_with_warning | retry | halt` with **no LLM call**.
   FastAPI backend, Vite/React frontend — both working.

2. **The research paper** the supervisor became — *"Evaluation as Supervision"*.
   Conference version **submitted and under review**; a journal extension
   (injected-defect repair study) is the active work. **Start at
   [`docs/paper/NEXT_SESSION.md`](docs/paper/NEXT_SESSION.md)**, with
   `docs/paper/JOURNAL_PLAN.md` as the authoritative plan and
   `docs/paper/PUBLICATION_STRATEGY.md` for how many papers the work becomes.

The system is the testbed; the paper is about its supervision layer. Changes to
`supervision.py`, `graph.py`, or the agent prompts have paper consequences —
check the journal plan before touching them.

## Repository layout

- `backend/app/agents/` — analysis, reasoning, strategy, report agents.
  `base_agent.py` holds the shared LLM client, the schema self-correction loop,
  and `_with_feedback` (how supervisor retry feedback reaches a prompt).
- `backend/app/core/` — `supervision.py` (measure/decide, the hub's brain),
  `graph.py` (LangGraph wiring), `state.py` (`PipelineState`),
  `orchestrator.py` (legacy recovery agent), `llm_config.py`, `config.py`.
- `backend/app/data/` — `loader.py`, `matching.py` (fuzzy), `preprocessor.py`.
- `backend/app/schemas/contracts.py` — Pydantic contracts shared by every stage.
- `backend/eval/` — four-tier evaluation harness; `tier1_checks.py` is the
  offline twin of `supervision.py` and the two must stay in agreement.
- `backend/scripts/` — `build_db.py`, study runners, `analysis/` reproduction
  scripts.
- `backend/tests/` — unit, integration, e2e.
- `frontend/` — Vite/React dashboard and pipeline monitor.

## Environment traps

These cost real time every session.

- **The repo path contains `Tài liệu` in two Unicode normalisations.** Absolute
  paths built by hand silently miss. For `Read`/`Write`/`Edit`, use the 8.3 short
  path: `C:\Users\hoanh\OneDrive\TAILIU~1\CSMATE~1\COS30018\Project\COS300~1.1_M\…`
  Bash with repo-relative paths also works.
- **Long bash heredocs fail on apostrophes.** A few lines survive; a long prose
  body dies with ``unexpected EOF while looking for matching `'``. Use the
  `Write` tool for prose, or `python - <<'PYEOF'` for scripted edits.
- **The Bash cwd persists between calls** and does not reliably reset. Start with
  `cd "$(git rev-parse --show-toplevel)"` rather than assuming.
- **Always run backend commands from `backend/`** — paths and pytest config
  assume that cwd.
- **Use the project venv** — system Python lacks the deps:
  `backend/venv/Scripts/python.exe` (Python 3.14.3). PowerShell activate:
  `./venv/Scripts/Activate.ps1`. Install: `pip install -r requirements.txt`.

## Commands

From `backend/`:

```bash
venv/Scripts/python.exe -m pytest -m "not integration"
```

- `-m integration` runs real LLM calls (needs `OPENAI_API_KEY`; auto-skips
  without it). Bare `pytest` runs everything.
- API: `uvicorn app.main:app --reload`.
- Frontend: `npm install && npm run dev` in `frontend/`.
- Full pipeline on a real restaurant:
  `python run_pipeline.py --name "McDonald's" --pick 1 --dump-stages out/` —
  `--dump-stages` writes each stage's JSON, which is what the evaluator and the
  replay tooling consume.
- Interactive data demo: `python -m tests.test_data_pipeline`.
- SQLite index: `python scripts/build_db.py` (`--rebuild` to replace). Without
  it every lookup scans the 5.34 GB review file.
- Reproduce any paper number (read-only, no API cost):
  `venv/Scripts/python.exe scripts/analysis/tally.py`, plus `rep_verdict.py`
  and `audit.py`.
- Journal extension, also read-only and **needing no dataset**:
  `scripts/analysis/defect_bank.py` (Tier-1 defect inventory) and
  `scripts/replay_stage.py --verify out_study` (the replay-fidelity gate that
  gates every injection trial). Both are covered by `tests/test_replay.py`.
- Re-running an *experiment* needs `MAX_REVIEW_SAMPLE=214` in the environment —
  `loader.MAX_REVIEWS` is read at import, so `--sample-size` alone cannot lift
  the cap. That guard is deliberate.

## What is and is not tracked

**Corrected 2026-08-24 — the previous version of this section was wrong.**
`docs/paper/` and `backend/out_study/` are **tracked**, not ignored. `git status`
is clean because the work is committed.

- The paper (`main.tex`, `references.bib`), the journal plan, the study dumps and
  the study checkpoints are all **in the repository**.
- The literature extractions live **outside the repo** at `../Reading List/` —
  that part is still true, and they are the one irreplaceable thing a clone
  misses.
- `backend/out_study/` holds ~260 result files. Three `.bak` files record
  failures deliberately — **do not delete them.**
- Until 2026-08-24 the blanket `*.jsonl` rule ignored every `checkpoint.jsonl`,
  so the repo tracked the records of *failed* runs while ignoring the
  `observations[]` behind every paper number. A negation rule
  (`!backend/out_study/**/*.jsonl`) fixes it. Do not remove that line.

⚠ **Two physical repo directories exist** — `Tài liệu` in NFD and NFC
normalisation, visually identical. The NFD one is the git repo; the NFC one is a
stray shadow with no `.git`. Check it before concluding a file was never written.

Never commit `.env` or raw Yelp data. Generated SQLite/CSV and non-study JSONL
stay ignored.

## Conventions

- Every agent returns a JSON-compatible dict with `status` and `error_detail`,
  validated against `app/schemas/contracts.py` — don't pass loose dicts between
  stages.
- Self-correction retries at most twice; after that the stage returns
  `status: "error"` and the supervisor decides.
- **Critical stages are analysis and reasoning**
  (`supervision.CRITICAL_STAGES`); strategy may degrade to a warning on retry
  exhaustion. `orchestrator.CRITICAL_AGENTS` is the older equivalent.
- **`strategy_agent` and `report_agent` support a deterministic `use_llm=False`
  mode** for offline and unit tests. Analysis and reasoning do not.
- Keep data loading separate from agent logic, and fuzzy matching separate from
  sampling.
- `docs/DECISIONS.md` is append-only — add an entry for any contract or
  architecture change rather than editing history.
- Distinguish agreed target behaviour from current implementation behaviour
  (`AGENTS.md`) — that rule exists because the orchestrator drifted once already.
- Talk straight. If something is unknown, say so.

## Gotchas (learned the hard way)

- **Dataset paths anchor to the repo root** (`Path(__file__).parents[3]` in
  `loader.py`), so `.env` paths must be repo-root-relative, e.g.
  `backend/data/raw/yelp_academic_dataset_business.json`.
- **Dataset files are flat** at `backend/data/raw/*.json` (once wrapped in
  redundant same-named folders) and are gitignored.
- **Real-LLM tests are non-deterministic.** Don't assert the model echoes input
  fields verbatim, and expect occasional graceful degradation. The e2e test
  retries the whole pipeline to stay reliable.
- **Temperature 0 is not run-to-run determinism** on a hosted API — served
  weights drift between sessions. This matters for any matched comparison; see
  `JOURNAL_PLAN.md` §14.1.
- **Secret hygiene:** `backend/.env.example` historically contained a
  live-looking key. Never commit real keys; use placeholders.

## Stale docs — do not trust

- **`README.md` §6 and §9** describe the *old* failure-only orchestrator
  ("retry, skip, or halt after stage failure"). The hub supervisor replaced it;
  `supervision.py` and `docs/FINDINGS_2026-07-16.md` F7 are correct.
- **`AGENTS.md`** predates the hub too, and points at `docs/LOCAL_LLM.md`.
- `PROJECT_AUDIT.md`, `RUNNING.md`, `docs/DECISIONS.md`, `docs/PROGRESS.md`,
  `docs/RUN_TESTS.md`, `docs/PLAN.md`, `docs/LOCAL_LLM.md` and both
  `ORCHESTRATOR_*.md` **do not exist and are not tracked**. An earlier version of
  this file said they were tracked and recoverable with `git restore` — that is
  false: this repository starts at "Initial import" and never contained them.
  They survive only in the old conference repo, if at all.
- Consequently ~12 references in shipped source point at missing docs:
  `graph.py`, `supervision.py`, `base_agent.py`, `state.py`, `main.py` and
  `orchestrator.py` cite `docs/ORCHESTRATOR_SIMPLE_HUB.md`; `llm_config.py`
  cites `docs/LOCAL_LLM.md` and `docs/DECISIONS.md`; `README.md` cites seven.
  Treat those pointers as historical notes, not as readable documents.
- `docs/DECISIONS.md` does not exist, so the "append a decision entry" rule
  below currently has nowhere to write. Record contract/architecture decisions in
  the relevant plan document until it is recreated.

When code and docs disagree, the code wins — then fix the doc.

## Git

Do not commit or push unless asked. Check `git status --short` first; stage only
task-related files. Never rewrite history unless explicitly told to.
