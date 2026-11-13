# Run queue — post-core experiments

**Created 2026-10-07.** The working list for the remaining runs, advanced one step
at a time by a self-paced loop: *finish → verify → commit → build the next →
amend → commit → launch → verify the first row → wait*. This file is the loop's
state. `NEXT_SESSION.md` §0 is still the map; `PREREGISTRATION.md` §0.1 is still
where every design decision is filed, **before** its run.

## Rules every step follows

1. **Amend before you spend.** A new step's design is filed as a dated
   `PREREGISTRATION.md` §0.1 amendment, committed **and pushed** before its
   first trial. It states which results already existed when it was written.
2. **Production defaults stay put.** Any new parameter defaults to production
   behaviour, and the core plan must still print 1,167 trials.
3. **Build gate:** new tests, full suite green (`pytest -m "not integration"`),
   `--plan-only` checked, first live defect inspected before walking away.
4. **Verify gate** after each run: complete checkpoint (planned rows and trials),
   one session per defect, offline re-score agrees 100 %, analysis written with
   `--json`, then commit + push data and analysis.
5. **Runs:** `LLM_DISABLE_FALLBACK=1`, detached via `Start-Process`, logs in
   `%TEMP%`. A dead run is resumed (resume skips whole defects; it never
   re-runs a `status_error`). Three dead runs in a row → stop and ask.
6. **Token accounting (no cap, author decision I7, 2026-11-13):** the former
   75 M-token / $150 ceiling (raised from 55 M for A12) is **lifted** for S2,
   Option H and S5 (`SUPERVISOR_FEEDBACK_2026-11-13.md` §2). Before launching,
   still sum `total_tokens` over every checkpoint and log the cell's exact
   pre-run estimate; after it is verified, log its exact actual `total_tokens`.
   Spent before the lift: 64.3 M (after Q7).
7. **Blocked = stop and ask.** Never guess a decision the author owns.

## Queue

| # | Step | Status | Notes |
|---|---|---|---|
| Q1 | **Placement pass** (§0.1 A5) — `--cell placement` → `T2P` | ✅ done 2026-10-07 22:47, verified | 540 trials. Verify, then `repair_analysis.py --cell placement` (reports with/without `attempts_made > 1`; P0 report-stage schema retries are concentrated) |
| Q2 | **O1 severity sweep** (§0.1 A6) — `--cell severity` → `T2S` | ✅ done 2026-10-08 00:32, verified | 144 trials. Verify, then `--cell severity` |
| Q3 | **Warm resampling** (plan D2, "REQUIRED"; §0.1 A7 filed) — `--cell warm` → `T2W` | ✅ done 2026-10-08 04:09, verified | Defaults below. Needs a temperature parameter threaded through `BaseAgent` with default 0 |
| Q4 | **Downstream propagation** (plan D12; §0.1 A9; endpoint (b), author's choice) — `run_downstream.py` → `T2D` | ✅ done 2026-10-08 12:09, verified |
| Q5 | **Tier-1 replay** (prereg §3 item 5; §0.1 A8 filed) — `run_tier1_replay.py` → `T1` | ✅ done 2026-10-08 06:36, verified | 13 real defects × {A1, A2, A3} at P0 (A0 undefined at P0, D9b) × r = 3 = 117 trials. Judged by the same checks (plan §5 Tier 1, item 2), descriptive only (MDE ≈ 31 pp) |
| Q6 | **Second model — C7** (plan D5b) | ✅ **done 2026-10-12 17:31, verified** on the RTX 5060 Ti 16 GB | [Full results](C7_STATUS.md). A10/A11, r=3; 138 eligible defects, 930 local trials, 929 usable, no API fees. A1 72.9%, A2 66.2%; exploratory gap +6.8 pp [+0.5, +13.3], McNemar p=0.0525. Data `T2L`, commit `7188bb9` |
| Q7 | **Thinking-budget sweep — Gemini 2.5 Flash** (§0.1 A12) — `--cell thinking` → `T2T` | ✅ **done 2026-11-02, verified** | 71/71 rows, 45/45 runnable defects, 1,224/1,224 usable trials, 1 session per defect, 1,224/1,224 offline re-score agreement, 11.16M tokens, total spent 64.3M < 75M. Binary repair at ceiling (100% at `none`); exact copy gap widens to +23.7 pp [+12.6, +36.3] at `none` ($p=0.00098$); dose-response slope +5.48 pp/step [+0.44, +10.59] |
| Q8 | **S2a A0 fill** (§0.1 A13) — `--cell a0fill` → `T2A0` | built, amendment committed, ready to launch | 71 defects, 284 trials (213 A0 + 71 A1 anchor). Estimate ≈ 3.5 M tokens |
| Q9 | **S2b A0 at none/high** (§0.1 A13) — `--cell thinking_a0` → `T2TA0` | built, amendment committed, ready to launch | 45 defects, 360 trials (270 A0 + 90 A1 anchor). Estimate ≈ 3.2 M tokens |
| Q10 | **S3 Option H harvest + replay** (§0.1 A14) — `run_study.py --out out_study/H` → `run_tier1_replay.py --out T1H` | lists built; pooled analysis to write | Batch 1 (28), Batch 2 (28) only if pooled cells < 18. Estimate ≈ 5–6 M tokens |

### Q3 defaults (to be filed as A7 — the author may change them before launch)

- **Temperature 1.0.** D2 cites Tyen §4(d), which needed temperature 1 to force
  a different step; it is also Gemini's default sampling temperature.
- **Defects:** the placement subset (45, one-third per-operator stride), so the
  warm cells stratify exactly like the placement cells.
- **Cells, one session per defect, r = 3:** A1@P1 and A2@P1 at T = 0 (in-session
  comparators, as for C1 and placement) and A1@P1, A2@P1, A3@P0 at T = 1.0 →
  15 trials per defect, **675 trials**.
- **Reads:** A1 − A2 at T = 1 beside T = 0 (two gaps with CIs); share of retried
  outputs byte-identical to the clean output at each temperature (the ceiling
  mechanism); A3 best-of-k (k = 1..3) at T = 1 against A1 single-shot, with
  tokens per arm (the Olausson equal-budget baseline).

## Log

- 2026-11-13 — **A13 and A14 filed** (`gemini-2.5-flash` withdrawn 2026-12-01, notice 2026-11-03). Q8 `a0fill` (284 trials) and Q9 `thinking_a0` (360) built, plan-only and dry-run checked, model pinned in code; 1-call live smoke served `gemini-2.5-flash`. Q10 Option H batch lists in `out_study/H/`; `run_study.py` / `run_tier1_replay.py` gained `--model`. Token cap lifted (I7); billed checkpoints sum to >= 65.4 M. Suite: 463 fast tests pass.
- 2026-11-02 — **Q7 verified; full queue complete.** Live `--cell thinking` batch finished across 45 runnable defects with 100% (1,224/1,224) usable trials, 71/71 checkpoint rows, 1 session per defect, 100% offline re-score agreement, consuming 11.16M tokens (total spent 64.3M < 75M budget cap). Binary repair remains at ceiling (100% at `none`). Exact restoration widens monotonically from +10.4 pp at `high` to +23.7 pp at `none` ($p=0.00098$, 11 vs 0 discordant); dose-response slope +5.48 pp/step [+0.44, +10.59]. Within-weights A3 baseline rises from 75.0% to 91.7% at `none` (+16.7 pp), demonstrating that thinking traces generate paraphrase churn. Zero thinking cuts latency by $2.4\times$ (7.17 s vs 17.44 s) and suppresses schema-retry loops.
- 2026-11-01 — **Q7 amended to Option A (thinking-budget sweep)** following HTTP 404 endpoint rejection on gemini-2.5-flash-lite. Implemented BaseAgent.reasoning_effort, run_injection_study.py --cell thinking (45 defects, 1,224 trials across 4 effort levels: none, low, medium, high), and repair_analysis.py --cell thinking (OLS dose-response trend test against rank and -log2(1+budget), level rates, within-effort and cross-effort contrasts, exact copy contrast, repair decomposition, drift, tokens). All tests pass; frozen core intact at 1,167 trials.
- 2026-10-12 17:32 — **Q6 verified; queue complete.** Qwen2.5-7B Q4_K_M / Ollama 0.40.3, all GPU, 32k context, 4096 output cap. Original G2 failed 8/10 identity; A11 r=3 was committed/pushed before final trials, G4 passed 8/10. 168/168 rows, 138 runnable defects, 930/930 trials, 929 usable, one session per defect; 929/929 offline scores/post-facts agree and all 966 returned raw calls verified. Four whole-defect context exclusions and 26 inapplicable rows. One A2 correction was blocked after its first response hit the output cap; counting it as unrepaired leaves results unchanged. A1 72.9%, A2 66.2%, gap +6.8 pp [+0.5, +13.3], exact majority McNemar p=0.0525; first-draw +5.8 pp [−0.7, +12.4]. Severe gap +9.5 pp [+3.2, +16.4]. Gemini ceiling does not replicate; feedback evidence is exploratory. Valid trials: 7.36 M unbilled local tokens, about 4 h 34 min collection, 426 offline tests passed. Data commit `7188bb9`; full report `C7_STATUS.md`. Charged Gemini budget unchanged. Next is journal writing; conference `main.tex` untouched.

- 2026-10-07 — queue created; Q1 running, Q2 chained behind it.
- 2026-10-07 23:45 — **Q1 verified**: 71/71 rows, 540/540 trials (1 `status_error`), 45/45 defects in one session, offline re-score 539/539, descriptors identical. A1 repair P0 94.1 %, P1 97.8 %, P2 97.8 %, P3 97.0 %; P1−P2 0.0 pp [−4.4, +4.4], P1−P3 +0.7 pp, P3−P2 −0.7 pp, P1−P0 +3.7 pp [−1.5, +9.6]. §5 prediction P1 ≫ P3 ≈ P2: **P3 ≈ P2 holds, P1 ≫ P2/P3 does not** (ceiling). All 16 report-stage defects needed a schema retry at P0 (50 of 52 multi-attempt trials); without them P0 = 90.8 % on 29 defects. Collateral P0 38 % vs P1 1 %. Drift of re-run P1 vs core: 97 % same class, 81 % byte-identical.
- 2026-10-07 23:50 — **Q3 built**: `BaseAgent.temperature` (class default 0, written to the call log), `--cell warm` (45 defects, 675 trials, 270 at T=0 / 405 at T=1), `repair_analysis.py --cell warm` (gaps, byte-identity, best-of-k, tokens). §0.1 A7 filed with both readings fixed. Fast tests 51 pass; core plan still 1,167.
- 2026-10-08 00:35 — **Q2 verified**: 28/28 rows, 144/144 trials all ok, 24/24 defects in one session, offline re-score 144/144. A1 repair on O1: **level 1 86.1 % [72.2, 97.2], level 2 88.9 % [76.4, 98.6]**, level 1 − level 2 **−2.8 pp [−11.1, +5.6]** (discordant 1 vs 2). Breaking every evidence id of the pattern did not lower repair. Drift of re-run level 1 vs core O1 A1: 96 % same class, 76 % byte-identical. Push of Q3 (`a81f5a6`) landed 00:01 after a GitHub 500 on five attempts.
- 2026-10-08 00:37 — **Q3 launched** after the budget guard (33.5 M spent + 7.1 M projected = 40.5 M < 55 M). First defect: one session, temperature 1.0 visibly varies the outputs (A3 3/3 distinct).
- 2026-10-08 00:55 — **Q5 built** ahead of Q4 (Q4 needs the author to choose the downstream endpoint). All 13 bank defects replay their recorded retry exactly; 117 trials in 7 cells. §0.1 A8 filed.
- 2026-10-08 04:20 — **Q3 verified**: 71/71 rows, 675/675 trials all ok, 45/45 defects in one session, offline re-score 675/675, 7.3 M tokens (projected 7.1 M). Repair at T1: A1 99.3 %, A2 97.0 %, A3 80.7 % (best-of-2 88.9 %, best-of-3 93.3 %). Byte-identity at P1 unchanged by temperature (A1 69.6→68.9 %, A2 48.9→48.9 %), A3 at P0 0 % at T1 vs 45 % at T0 in the core → **the P1 ceiling is copy-and-correct of the shown artifact, not re-derivation**; the earlier explanation is corrected in NEXT_SESSION. Gap difference T1−T0 +5.2 pp [+0.7, +11.1] (exploratory). Neither A7 reading applies: identity did not fall, repair did not fall. T0 reruns vs core: 99.6 % same class, 83 % byte-identical.
- 2026-10-08 04:25 — **Q5 launched** after the budget guard (40.75 M + 2.9 M projected).
- 2026-10-08 06:45 — **Q5 verified**: 13/13 defects, 117/117 trials ok, one session each, offline re-judge 117/117, 4.1 M tokens. Accepted after the retry (production checks): A1 28.2 %, A2 76.9 %, A3 25.6 %; trace class under the content-word check: A1 87.5 %, A2 100 %, A3 79.2 %. Descriptive only.
- 2026-10-08 06:45 — **Loop stopped at Q4 and Q6**: both need the author (downstream endpoint; second model). Total spent ≈ 44.9 M tokens.
- 2026-10-08 — **Author chose (b) for Q4.** Q4 built: 90 defects, 447 conditions, 796 downstream calls; §0.1 A9 filed with three readings fixed. Loop restarted.
- 2026-10-08 09:00 — **Q4 launched** after the budget guard (44.9 M + 4.9 M projected; the real cost was 8.2 M — 3 calls and ~22k tokens per reasoning condition, because the report stage needs a schema-correction second call every time).
- 2026-10-08 12:20 — **Q4 verified**: 90/90 defects, 447/447 conditions ok, one session each, offline re-judge of every downstream stage 447/447. E3: unrepaired +8.2 pp over the noise floor, A1 +4.1 pp, A1 − unrepaired −4.2 pp. E2 (O5): planted issue in the report 70 % → 0 % with repair. Report check: 14/14 propagating runs accepted, 6/6 non-propagating rejected. Total spent ≈ 53.1 M tokens.
- 2026-10-08 12:20 — **Loop stopped at Q6**: waiting for the author's RTX 5060 server (address, Ollama version, model digest).
- 2026-10-08 — **Offline items done (no API cost):** O5 matcher sensitivity (§2.3) — the confirmatory A1 − A2 is +0.72 pp [−2.9, +4.3] under all four criteria, primary recomputation reproduces 157/157 stored O5 outcomes; defect origin (§3 item 5) — A1 accepted at P0 for 98.5 % of injected vs 28.2 % of real defects; change-then-resolve (§3 item 6); class ordering — §5 prediction reversed (structural 98.6 % > semantic 93.0 % > referential 89.6 %); C6 detection curves (frequency step at 0.05; trace: difflib flags 5.0 % of grounded issues and misses 4 % of foreign ones, content-word 0 % / 0 %); coupling 13/13. Results consolidated in `RESULTS.md`; stale status lines in PUBLICATION_STRATEGY, JOURNAL_PLAN and NEXT_SESSION marked superseded. Suite 411 pass.
- 2026-10-08 — **Author decided: journal only** (no conference split). Next session: C7 (`C7_RUNBOOK.md`) and writing (`JOURNAL_PAPER_PLAN.md`).
