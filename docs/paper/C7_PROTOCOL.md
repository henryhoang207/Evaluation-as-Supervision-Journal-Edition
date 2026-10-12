# C7 local replication — protocol fixed before preflight

**2026-10-12.** The author authorised setup and execution of the C7 experiment.
All Gemini cells and their results already exist. C7 is exploratory; it does
not change the frozen core or add a confirmatory claim. Model: the runbook's
Qwen2.5-7B-Instruct Q4_K_M, Ollama 0.40.3, on the measured RTX 5060 Ti **16 GB**,
i7-14700KF and 32 GB RAM. This is the same machine as the runner; the service
listens on **127.0.0.1:11434**. No LAN server or firewall change is needed.

## Runtime and context

- Temperature 0, seed **20261012**, **32768** context, **4096** maximum output
  tokens, one request at a time, one loaded model, flash attention, F16 KV cache.
- The 4096 output reserve replaces the runbook's approximate 2000 to accommodate
  the structured stage outputs. The production prompts and schema correction
  limit of two retries are unchanged. Decoding controls apply only to C7.
- Initial prompts are counted using Qwen's pinned tokenizer and text-only
  ChatML template, calibrated against actual server counts. An additional
  **64 tokens** cover framing differences. A defect is excluded in advance
  if *any* of its planned arms exceeds 32768 minus the output reserve/margin.
  Allocation strides are determined before exclusions and never reshuffled.
- The same context guard checks every schema-correction call. An oversized
  correction is refused before inference, counted separately, and never
  resampled to obtain a success. Raw response text, hashes, server/local token
  counts and finish reasons are recorded for successful calls.
- The model digest, tokenizer hash, runtime executable hash, server parameters,
  GPU/driver and dependency versions are recorded before the final trials.
  The original cloud `.env` is untouched; the credential is `ollama-local` and
  fallback is disabled. No cloud model calls are authorised by this pass.

## Gates and preflight data

G1: the OpenAI-compatible model listing contains the model, all layers are on
GPU, and the loaded context is 32768. G3 is computed before calls: the context
inventory covers every planned prompt. G2 then sends **10 A1@P1 prompts twice**;
operator round-robin selection takes the longest eligible prompt in each
bucket first. Raw outputs must match **10/10** and server/local token counts
must differ by no more than 64. G4 uses **five defects**, covering all three
stages, under A1 and A2 (ten trials); **more than half** must pass schema on
their first call. Record eventual validity, correction frequency and elapsed
time. No final trial runs unless G1–G4 pass. A failed gate is recorded; changing
the model/design requires an explicit additional amendment before final data.

The gate outputs live in `backend/out_study/C7_preflight/`; they are **excluded
from all final estimates**. Pilot repair outcomes do not determine selection,
wording or the analysis. This protocol is recorded before those calls.

## Trial allocation and analysis

- All **142** core defects before context exclusions: A1@P1 and A2@P1, one draw.
- A second draw of each primary arm on a per-operator **1/6 stride**: **22**
  defects before exclusions. The runbook proposed about 20; the unadjusted
  stride yields 22 and is retained without tuning.
- A3@P0 once on the frozen core's quarter stride: **34** defects before exclusions.
- **362 trials before exclusions** (164 A1, 164 A2, 34 A3). Within each defect,
  each arm's repetitions are contiguous and all arms share one session.
- **Rep 0 alone** estimates A1 minus A2 and absolute rates. Extra repetitions
  measure raw-output and outcome stability; they do not change the primary
  weights or turn an r=1 replication into a majority-of-two design.
- Defect-bootstrap 95% intervals (10000 draws, seed 20260803), exact McNemar
  reported **exploratorily**, four outcome classes, per-operator/stage rates,
  rates with/without schema corrections, identity to the clean Gemini output,
  collateral, token/time counts, and context/provider exclusions.
- Pair with Gemini on the identical eligible defects and arms: local rep 0
  minus the mean of Gemini's usable core repetitions, with a defect-bootstrap
  interval. This is a **model-and-runtime comparison**, with Gemini-generated
  clean bases held fixed, not a pure model or provider causal effect.

Readings fixed before preflight: (1) both primary rates at least 90% and an
interval containing zero are consistent with replication of the ceiling;
they do not establish equivalence. (2) A positive interval excluding zero is
exploratory evidence that measured feedback helps this model/runtime. (3)
both rates below 90% make the contrast a repair task with headroom; its interval
still determines what can be inferred. (4) any other pattern is reported as
mixed/inconclusive. Successful and failed gates, exclusions and every planned
secondary are reported without selecting on significance.

Final data: `backend/out_study/T2L/`. The design/code and then the passed gate
record plus exact provenance are committed and pushed **before** final trials.
Completion requires checkpoint counts, one session per defect, matching model
identity, no detected truncation, and full offline re-scoring agreement.
