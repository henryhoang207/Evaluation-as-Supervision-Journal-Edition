# Binary Repair and Exact Restoration under Measured Feedback in a Supervised LLM Pipeline

**Replication package and source code** for:

> **Binary Repair and Exact Restoration under Measured Feedback in a Supervised LLM Pipeline**  
> Hoan Huu Hoang, Toan Manh Nguyen  
> Swinburne Vietnam, FPT University, Hanoi, Vietnam

This repository holds the supervised four-stage restaurant-review pipeline, the deterministic runtime supervisor, the fault-injection and replay harness, the pre-registrations, every trial record, and every offline analysis script needed to regenerate all numbers reported in the paper without making model calls.

### Relation to the conference paper

This journal study extends *Evaluation as Supervision: Deterministic Runtime Verification of Claims in a Multi-Agent LLM Pipeline* (EAI FISAT 2026, in press; source in [`docs/paper/main.tex`](docs/paper/main.tex)), which introduced the pipeline, the deterministic runtime supervisor, and the initial defect-incidence and instability measurements. The pipeline and deterministic supervisor (`backend/app/core/supervision.py`) are unchanged in production behaviour for this study; all fault injections, controlled repair trials, real-defect replays, downstream-propagation analyses, check calibrations, local-model runs (`Qwen2.5-7B-Instruct`), thinking-budget sweeps, and the pre-registered `gemini-3.5-flash-lite` replication are new.

---

## Pre-registrations and Frozen Tags

Both confirmatory passes were pre-registered in [`docs/paper/PREREGISTRATION.md`](docs/paper/PREREGISTRATION.md) and frozen with annotated Git tags before their first repair trial ran:

| Tag | Target commit | Date | Scope |
| --- | --- | --- | --- |
| `prereg-freeze` | `5f78d21` | 14 Sep 2026 | Core `gemini-2.5-flash` repair study (`T2`) and analysis rules |
| `prereg-fl-freeze` | `edfb406` | 16 Nov 2026 | Amendment A15 confirmatory exact-restoration replication on `gemini-3.5-flash-lite` (`T2FL`) |

Every post-freeze exploratory cell and protocol amendment (A1–A15) is logged in [`docs/paper/PREREGISTRATION.md`](docs/paper/PREREGISTRATION.md), the run ledger is in [`backend/out_study/ledger.jsonl`](backend/out_study/ledger.jsonl), and the consolidated numerical summary is in [`docs/paper/RESULTS.md`](docs/paper/RESULTS.md).

---

## Offline Reproduction (No API Keys / No Model Calls)

Every number in the paper can be regenerated offline from the committed trial records in [`backend/out_study/`](backend/out_study/).

### 1. Environment setup

Tested with Python 3.14 (Python 3.11+ supported):

```bash
cd backend
python -m venv venv
# Windows PowerShell:
.\venv\Scripts\Activate.ps1
# Linux / macOS:
# source venv/bin/activate

pip install -r requirements.txt
# Optional (pins numpy/scipy/pandas/tokenizers used for C7 local replication):
# pip install -r requirements-c7.txt
```

### 2. Run the offline test suite

From `backend/`:

```bash
python -m pytest -m "not integration"
```

All 552 offline unit, supervisor, injector, scorer, replay, and analysis tests run without network access or API keys (13 live integration tests are deselected).

### 3. Regenerate cell analyses

Run from `backend/`. Passing `--json <path>` writes the full JSON output (omitting `--json` prints the summary without modifying committed files):

```bash
# Confirmatory core (gemini-2.5-flash, T2)
python scripts/analysis/repair_analysis.py --cell core

# Confirmatory replication (gemini-3.5-flash-lite on own bases, T2FL)
python scripts/analysis/repair_analysis.py --cell flashlite

# Pooled real-defect replay (T1 + Option-H harvest T1H)
python scripts/analysis/repair_analysis.py --cell tier1_pooled

# Secondary offline diagnostics and calibration (writes out_study/secondary_extra.json when --json is set)
python scripts/analysis/secondary_extra.py
```

All 15 `--cell` targets supported by [`backend/scripts/analysis/repair_analysis.py`](backend/scripts/analysis/repair_analysis.py):

| `--cell` value | Study cell | Committed trial log | Committed analysis output |
| --- | --- | --- | --- |
| `core` | Confirmatory core (`gemini-2.5-flash`) | `backend/out_study/T2/checkpoint.jsonl` | [`T2/analysis.json`](backend/out_study/T2/analysis.json) |
| `d19` | Frequency-overwrite counterfactual (A2) | `backend/out_study/T2D19/checkpoint.jsonl` | [`T2D19/analysis.json`](backend/out_study/T2D19/analysis.json) |
| `c1` | Constraint disclosure C0 vs C1 (A1, A3) | `backend/out_study/T2C1/checkpoint.jsonl` | [`T2C1/analysis.json`](backend/out_study/T2C1/analysis.json) |
| `placement` | Artifact placement P0–P3 (A5) | `backend/out_study/T2P/checkpoint.jsonl` | [`T2P/analysis.json`](backend/out_study/T2P/analysis.json) |
| `severity` | O1 severity levels 1 vs 2 (A6) | `backend/out_study/T2S/checkpoint.jsonl` | [`T2S/analysis.json`](backend/out_study/T2S/analysis.json) |
| `warm` | Warm resampling `T=0` vs `T=1` (A7) | `backend/out_study/T2W/checkpoint.jsonl` | [`T2W/analysis.json`](backend/out_study/T2W/analysis.json) |
| `tier1` | Initial real-defect replay (A8) | `backend/out_study/T1/checkpoint.jsonl` | [`T1/analysis.json`](backend/out_study/T1/analysis.json) |
| `tier1_pooled` | Pooled real-defect replay `T1 + T1H` (A14) | `backend/out_study/T1/checkpoint.jsonl` + `T1H/checkpoint.jsonl` | [`T1H/analysis.json`](backend/out_study/T1H/analysis.json) |
| `downstream` | Downstream propagation (A9) | `backend/out_study/T2D/checkpoint.jsonl` | [`T2D/analysis.json`](backend/out_study/T2D/analysis.json) |
| `o5sens` | O5 four-matcher sensitivity | `backend/out_study/T2/checkpoint.jsonl` | Computed from `T2` |
| `c7` | Second model `Qwen2.5-7B-Instruct` (A10, A11) | `backend/out_study/T2L/checkpoint.jsonl` | [`T2L/analysis.json`](backend/out_study/T2L/analysis.json) |
| `thinking` | Thinking-budget sweep (A12) | `backend/out_study/T2T/checkpoint.jsonl` | [`T2T/analysis.json`](backend/out_study/T2T/analysis.json) |
| `a0fill` | Full-bank A0 completion (A13) | `backend/out_study/T2A0/checkpoint.jsonl` | [`T2A0/analysis.json`](backend/out_study/T2A0/analysis.json) |
| `thinking_a0` | Thinking-budget A0 at `none`/`high` (A13) | `backend/out_study/T2TA0/checkpoint.jsonl` | [`T2TA0/analysis.json`](backend/out_study/T2TA0/analysis.json) |
| `flashlite` | Confirmatory `gemini-3.5-flash-lite` replication (A15) | `backend/out_study/T2FL/checkpoint.jsonl` | [`T2FL/analysis.json`](backend/out_study/T2FL/analysis.json) |

Additional offline analysis scripts in [`backend/scripts/analysis/`](backend/scripts/analysis/):

- `secondary_extra.py` — check calibration, clean-run acceptance, and pre-specified secondary checks ([`secondary_extra.json`](backend/out_study/secondary_extra.json)).
- `defect_bank.py` — real-defect bank extraction and replay-fidelity verification ([`defect_bank.json`](backend/out_study/defect_bank.json)).
- `audit.py`, `tally.py`, `rep_tally.py`, `rep_verdict.py` — observe-mode Phase-A and repetition diagnostics.
- `power.py`, `churn.py`, `prompt_audit.py`, `matcher_shrinkage.py` — pre-study design and audit utilities.

---

## System Under Study

The pipeline analyses a bounded set of Yelp restaurant reviews in four closed LLM stages orchestrated through a LangGraph hub (`backend/app/core/graph.py`):

1. **Analysis** (`analysis_agent.py`): labels each review's overall sentiment and aspect-level polarities.
2. **Reasoning** (`reasoning_agent.py`): aggregates recurring patterns (with review-ID evidence lists and claimed frequencies) and root causes.
3. **Strategy** (`strategy_agent.py`): proposes prioritised recommendations grounded in upstream patterns and root causes.
4. **Report** (`report_agent.py`): assembles the final structured report with trusted business metadata.

After every stage, the deterministic runtime supervisor (`backend/app/core/supervision.py`, zero model calls) runs `measure()` against upstream state and `decide()` to route `proceed`, `proceed_with_warning`, `retry` (writing the measured failure into the stage prompt, capped at two retries per stage), or `halt`, and deterministically overwrites recomputable pattern frequencies on accepted reasoning outputs.

---

## Repository Structure

```text
.
|-- backend/
|   |-- app/
|   |   |-- agents/              # Four-stage LLM agents & shared retry/validation base
|   |   |-- core/                # LangGraph hub, deterministic supervisor, LLM config
|   |   |-- data/                # Yelp loader, SQLite lookup, fuzzy matching, preprocessing
|   |   |-- schemas/             # Pydantic output and error contracts
|   |   `-- main.py              # FastAPI endpoints (sync & SSE)
|   |-- eval/                    # Offline/live evaluation harness and fixtures
|   |-- scripts/
|   |   |-- analysis/            # Offline statistical analysis & verification scripts
|   |   |-- arms.py              # Frozen arm (A0-A3), placement (P0-P3), and C1 templates
|   |   |-- inject_defects.py    # Deterministic fault operators (O1-O7)
|   |   |-- run_injection_study.py
|   |   |-- run_tier1_replay.py
|   |   |-- run_downstream.py
|   |   |-- run_study.py
|   |   `-- build_db.py          # Optional local SQLite indexer for raw Yelp JSON
|   |-- out_study/               # Committed Phase-A/R/H/FL dumps, trial logs, analysis JSONs
|   |-- tests/                   # 552 offline tests + 13 live integration tests
|   |-- requirements.txt
|   |-- requirements-c7.txt
|   |-- .env.example
|   `-- .env.local.example
|-- docs/
|   |-- paper/
|   |   |-- PREREGISTRATION.md   # Frozen pre-registration + Amendments A1-A15
|   |   |-- RESULTS.md           # Consolidated study results ledger
|   |   |-- main.tex             # Conference version (EAI FISAT 2026)
|   |   `-- journal/             # Journal draft sources
|   `-- EVALUATION_REPORT.md
`-- frontend/                    # React dashboard and SSE pipeline monitor
```

---

## Data Availability and Re-execution Scope

- **Committed study data:** `backend/out_study/` contains the pipeline's structured outputs, supervisor measurements, repair labels, and Yelp business names and business/review identifiers, **with no raw review text**.
- **Yelp Open Dataset:** Not redistributed in this repository. Download directly from Yelp under its dataset terms at https://business.yelp.com/data/resources/open-dataset/ (the copy used in this study was downloaded on 18 May 2026). Place `yelp_academic_dataset_business.json` and `yelp_academic_dataset_review.json` in `backend/data/raw/` and build the local SQLite index (`backend/data/processed/yelp.db`, gitignored) if you wish to run fresh Phase-A executions:
  ```bash
  cd backend
  python scripts/build_db.py
  ```
- **Model availability:** Offline re-analysis from committed records runs indefinitely without API access. Live re-execution on `gemini-2.5-flash` will no longer be available after its scheduled withdrawal on 1 December 2026; live re-execution remains available on `gemini-3.5-flash-lite` (Amendment A15) and locally via Ollama (`Qwen2.5-7B-Instruct`, see `backend/.env.local.example`).

---

## Optional: Running the Pipeline and Web UI

Copy `backend/.env.example` (hosted Gemini OpenAI-compatible endpoint) or `backend/.env.local.example` (local Ollama endpoint) to `backend/.env` and configure your credentials.

- **FastAPI backend** (from `backend/`):
  ```bash
  uvicorn app.main:app --reload
  ```
  Endpoints: `GET /health`, `GET /api/businesses/search`, `POST /api/reports`, `GET /api/reports/stream` (SSE).
- **React frontend** (from `frontend/`):
  ```bash
  npm install
  npm run dev
  ```
  Set `VITE_API_BASE_URL` if the backend is not served at `http://localhost:8000`.
