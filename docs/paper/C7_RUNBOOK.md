# C7 runbook — the second model (plan D5b / C7, run queue Q6)

**Written 2026-10-08** for the next session. Nothing in this file has been run.
Every Gemini cell is done (`RESULTS.md`); this is the last experiment.

## Why it matters

- **D15** — *one model, one provider* — is the objection that limits the venue.
  Every result so far is `gemini-2.5-flash` at temperature 0.
- The core result is a **null at ceiling** explained by **copy-and-correct**:
  shown its defective output at P1, the model copies it and fixes the one
  injected change. Whether that holds for a different model family is exactly
  what C7 answers.
- C7's original premise (plan C7): on a deterministic local runtime a bare
  re-draw is bit-identical, so any difference between arms is attributable to
  feedback content. The hosted runs showed temperature 0 is **not**
  deterministic across sessions (83 % byte-identical) — C7 can measure that
  directly.

## Decided / recommended so far

| Item | State |
|---|---|
| Hardware | The author's other computer, **RTX 5060**. Assumed **8 GB VRAM** — ⚠ confirm; a 16 GB 5060 Ti changes the model choice (below) |
| Model | **Recommended, not yet confirmed by the author:** `qwen2.5:7b-instruct-q4_K_M` (Qwen2.5-7B-Instruct, Q4_K_M) served by **Ollama** |
| Why this model | Fits 8 GB **with the 32k context our prompts need** (weights ≈ 4.7 GB + KV cache ≈ 1.9 GB at 32k, thanks to 4 KV heads); strong at JSON output for its size; **no hidden thinking mode** (clean determinism); Apache-2.0, pinned by digest; a different family from Gemini |
| Rejected at 8 GB | Llama-3.1-8B and Qwen3-8B: their KV cache at 32k context (≈ 4–5 GB) does not fit beside the weights; Qwen3 also needs its thinking mode disabled, which changes the prompt. **If the card has 16 GB**, revisit: both become viable |
| Context | **32k (`num_ctx 32768`) is mandatory.** The longest reasoning-stage prompts are ≈ 100k characters (≈ 25–30k tokens). Ollama's default context silently truncates |
| Code support | `app/core/llm_config.py` already treats any base URL containing `:11434` as a local runtime (placeholder key). No pipeline change is needed to *call* the model |

## Step 1 — server setup (the author, on the RTX 5060 machine)

1. Install Ollama; `ollama pull qwen2.5:7b-instruct-q4_K_M`.
2. Create a file named `Modelfile` with two lines —
   `FROM qwen2.5:7b-instruct-q4_K_M` and `PARAMETER num_ctx 32768` — then
   `ollama create qwen25-7b-c7 -f Modelfile`.
3. Set environment variables `OLLAMA_HOST=0.0.0.0:11434` (listen on the LAN) and
   `OLLAMA_NUM_PARALLEL=1` (no batching — needed for determinism); restart
   Ollama.
4. Firewall: allow TCP 11434 **from the home network only**. Ollama has no
   authentication — never forward the port to the internet.
5. Load the model once and check `ollama ps` shows **100 % GPU** (any CPU share
   means it does not fit and will be slow and possibly non-deterministic).
6. Record for provenance and send to the session: the machine's **LAN IP**,
   `ollama --version`, the model **ID/digest** from `ollama list`, the GPU model
   and VRAM, and the NVIDIA driver version.

## Step 2 — gates on the laptop (free, before any trial)

Run everything with environment variables set **inline for the run only**.
**Do not edit `backend/.env`** (it holds the Gemini settings every other cell
used):

- `OPENAI_BASE_URL=http://<server-ip>:11434/v1`
- `OPENAI_MODEL=qwen25-7b-c7` and `OPENAI_FALLBACK_MODEL=qwen25-7b-c7`
- `OPENAI_API_KEY=ollama-local` — ⚠ set it explicitly, or the Gemini key from
  `.env` is sent to the server as the bearer token
- `LLM_DISABLE_FALLBACK=1`

| Gate | What | Pass condition |
|---|---|---|
| G1 connectivity | `GET http://<ip>:11434/v1/models` | lists `qwen25-7b-c7` |
| G2 determinism | the same ≈ 10 real trial prompts (A1@P1 message lists from the core plan) sent twice each | byte-identical outputs, 10/10. If not, stop and decide: it changes what C7 can claim |
| G3 context | token count of every planned prompt (calibrate characters-per-token on G2's `usage.prompt_tokens`) | defects whose prompt + ≈ 2k output exceed 32k are **excluded at plan time and counted**, like the D20 gates |
| G4 pilot | ≈ 5 defects across reasoning, strategy, report | record schema pass rate (`attempts_made`) and seconds per trial. If most first attempts fail validation, the model is not usable as is — stop and decide |

None of G2–G4 has code yet: write them as a small `scripts/c7_gates.py` with
tests, reusing `run_injection_study.build_plan` and `arms.build_messages` so the
prompts are exactly the trial prompts.

## Step 3 — build the pass (proposal; finalise in amendment A10)

- **`run_injection_study.py --cell c7`** into `out_study/T2L`, following the
  pattern of the existing `c1`/`d19`/`placement`/`severity`/`warm` passes
  (`CELLS`, `CELL_OUT`, a `_c7_cells` builder, `REQUIRED_ARMS`, `verify_order`
  checks, tests).
- **Cells (proposal):** all 142 core defects minus G3 exclusions; **A1@P1 and
  A2@P1** (the confirmatory contrast), **r = 1** if G2 passes, plus a **second
  repetition on a stratified ≈ 20-defect subset** to measure determinism in the
  run itself; **A3@P0** on the core's A3 subset (34). ≈ 142 × 2 + 34 + 40 ≈ **360
  trials**, **$0** in API fees. Time unknown until G4 (guess 30–90 s per trial →
  3–9 h).
- Record the runtime provenance (Ollama version, model digest, GPU, driver) in
  the run header and in the amendment.
- **Analysis:** `repair_analysis.py --cell c7` — A1 − A2 with a defect-bootstrap
  CI and the exact McNemar (descriptive here: C7 is exploratory), A3's
  regeneration rate, byte-identity to the clean output (the copy-and-correct
  mechanism), the determinism rate from the repeated subset, and a paired
  comparison with the Gemini core on the same defects.

## Step 4 — amendment A10, then run

File `PREREGISTRATION.md` §0.1 **A10** before any trial: model identity by name
(parameter count, quantisation, digest, runtime version, `num_ctx`, seed or
greedy decoding), the gates and their exclusions, the cells, the reads, and
**readings fixed in advance**, for example:

1. **The null replicates** — A1 ≈ A2 near ceiling on a second model family: the
   result is not a property of Gemini.
2. **A gap opens** (A1 > A2) on the smaller model: the null was a ceiling of a
   capable model; feedback content matters when repair is hard.
3. **Repair falls well below ceiling in both arms**: the injected defects are
   not easy for this model, and the contrast becomes informative rather than
   ceilinged.

Then: full suite green → commit **and push** the amendment and code → `--plan-only`
→ launch detached (`Start-Process`, logs in `%TEMP%`) → inspect the first defect
→ verify gate (complete checkpoint, one session per defect, offline re-score) →
analysis → commit and push → add the results to `RESULTS.md`.

## Operational traps learned on the Gemini runs

- A run started from this session **dies if the Claude desktop app restarts**;
  a laptop sleep or network drop turns in-flight calls into permanent
  `status_error` exclusions. Keep the app open and both machines awake. For C7
  the server must stay up too.
- Stopping a run deliberately is safe: resume re-runs only unfinished defects.
- GitHub pushes have failed with HTTP 500 for a few minutes at a time; retry.
- Long bash heredocs with apostrophes or backticks break in this shell — write
  scripts and prose with the Write tool.
