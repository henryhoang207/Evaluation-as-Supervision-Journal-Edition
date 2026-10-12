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
6. **Budget guard:** before launching, sum `total_tokens` over every checkpoint.
   If spent + projected > **55 M tokens** (≈ $137 if every token were billed at
   the output rate), stop and ask. Budget: $150.
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
