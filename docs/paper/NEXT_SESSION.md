# START HERE — next session

**Rewritten:** 2026-08-24. Supersedes the 2026-08-04 version, which described
production of the conference paper. **That paper is finished.** The active work
is now the journal extension.

Where this file disagrees with `JOURNAL_PLAN.md`, **`JOURNAL_PLAN.md` wins** —
it is the authoritative plan. This file is the map.

---

## 0. ▶ START HERE (2026-10-08) — two tracks left: C7 and the journal paper

**Where things stand.** Every experiment that runs on Gemini is **done, verified
and pushed** (core, D19, C1, placement, severity, warm, Tier-1 replay,
downstream propagation), and every pre-specified offline analysis with it. The
whole record is **[`RESULTS.md`](RESULTS.md)**. Spend ≈ 53 M tokens (≈ $95 at a
realistic input/output mix) of the $150 budget. Suite **411 pass**. The working
tree was clean and in sync with `origin/main` at the end of 2026-10-08.

**Decided 2026-10-08 by the author: journal only** — no conference split (the
pre-registered split rule was not met). Venue per `JOURNAL_PLAN.md` D7: **EMSE
regular track**.

| Track | Start with | First step |
|---|---|---|
| **C7 — the second model** | **[`C7_RUNBOOK.md`](C7_RUNBOOK.md)** | The author sets up Ollama on the RTX 5060 machine (Qwen2.5-7B-Instruct Q4_K_M, `num_ctx 32768`, LAN access) and reports its IP, Ollama version and model digest. Then gates G1–G4 → build `--cell c7` → amendment A10 → run (≈ 360 trials, $0) |
| **The journal paper** | **[`JOURNAL_PAPER_PLAN.md`](JOURNAL_PAPER_PLAN.md)** | Settle authorship and the extension declaration; download the Springer Nature template; draft Study design and Results first, from `PREREGISTRATION.md` and `RESULTS.md`. **Do not edit `main.tex`** (conference #1, under review) |

**Document map.** `RESULTS.md` (numbers, with sources) · `PREREGISTRATION.md`
(frozen design, amendments §0.1 A1–A9) · `RUN_QUEUE.md` (run history and the
rules runs follow) · `C7_RUNBOOK.md` · `JOURNAL_PAPER_PLAN.md` ·
`JOURNAL_PLAN.md` (authoritative plan; reading tables in §2, venue in §12) ·
`PUBLICATION_STRATEGY.md`. The table below is the per-cell results summary;
everything after it is history.

---

## 0b. Results summary, 2026-10-07/08 (every Gemini cell)

| | |
|---|---|
| **Core** | ✅ Ran 2026-10-05 → 07 into `backend/out_study/T2/checkpoint.jsonl`. **1,167 trials, 1,149 usable, 18 `status_error`** (network drops + one overnight laptop sleep). All `gemini-2.5-flash`, no fallback, 16.6M tokens. Re-scored offline: **1,149/1,149 agree** with the live scores |
| **Confirmatory (§2.1)** | **Null at ceiling.** N = 139 (3 lost their A1/A2 pair). A1 94.7 %, A2 94.0 %, **A1 − A2 = +0.7 pp, 95 % CI [−2.9, +4.3]**, exact McNemar p = 0.75 (discordant 6 vs 4). **Split rule not met → no branch.** Same without `attempts_made > 1` trials |
| **Why at ceiling** | 68 % of A1, 53 % of A2 and 45 % of A3 retries are **byte-identical to the clean pre-injection output**. ⚠ **Corrected 2026-10-08 by the warm cell (A7):** at P1 this is **copy-and-correct of the artifact the model is shown**, not temperature-0 re-derivation — byte-identity is unchanged at temperature 1 (A1 69.6 % → 68.9 %, A2 48.9 % → 48.9 %) while A3's fresh draws at P0 fall from 45 % to 0 %. Only A3 at P0 is re-derivation. A0 100 %, A3 ≈ 95 % on the severe cell. Predictions were A1 ≈ 45 %, A2 ≈ 33 %, A3 ≈ 53 %. O1 is the only cell with headroom (≈ 85 %) |
| **Analysis code** | `scripts/analysis/repair_analysis.py` (`--cell core|c1|d19`), 28 tests. Output `out_study/T2/analysis.json` |
| **Post-core passes** | Wired 2026-10-07 as prereg **§0.1 A2 (D19)** and **A3 (C1 as its own pass, C0 re-run beside it)**; A4 records the analysis code and the one interim budget look. Both **ran 2026-10-07** |
| **Placement (§0.1 A5)** | ✅ `out_study/T2P`, 45 defects, 540 trials (1 `status_error`). A1 repair **P0 94.1 % · P1 97.8 % · P2 97.8 % · P3 97.0 %**. Prediction P1 ≫ P3 ≈ P2: **P3 ≈ P2 holds; P1 ≫ P2/P3 does not** (P1−P2 0.0 pp [−4.4, +4.4]). Every report-stage defect needed a schema retry at P0 (production placement); collateral P0 38 % vs P1 1 % |
| **O1 severity (§0.1 A6)** | ✅ `out_study/T2S`, 24 defects, 144/144 usable. A1 repair **level 1 86.1 %, level 2 88.9 %**; level 1 − level 2 **−2.8 pp [−11.1, +5.6]**. Breaking every evidence id of the pattern did not lower repair |
| **Warm resampling (§0.1 A7)** | ✅ `out_study/T2W`, 45 defects, 675/675 usable. Temperature 1.0: **A1 99.3 %, A2 97.0 %** (T0 in-session: 97.0 %, 100 %); A3 fresh draws 80.7 %. **The ceiling is not a temperature-0 artefact.** Byte-identity at P1 is temperature-invariant (copy-and-correct; see the row above). A1 − A2: T0 −3.0 pp [−7.4, 0.0], T1 +2.2 pp [0.0, +5.2], difference +5.2 pp [+0.7, +11.1] — exploratory, a handful of defects, one of many intervals. Equal budget: A1 single retry 97.0 % at ≈ 9.7k tokens vs A3 best-of-3 at T1 93.3 % at ≈ 41k. Neither of A7's pre-fixed readings applies — reported as the third case. A3 at P0, T1: 48/135 schema retries (report stage), 70.1 % without them |
| **Tier-1 replay (§0.1 A8)** | ✅ `out_study/T1`, 13 real defects in 7 cells, 117/117 usable. **Descriptive only.** Accepted by the supervisor's own checks after the retry at P0: **A1 (the production retry) 28.2 %, A2 (generic rejection) 76.9 %, A3 (bare re-draw) 25.6 %** (intervals over cells, wide). On the trace class the content-word check (D22) accepts A1 87.5 %, A2 100 %, A3 79.2 % — the gap is the production matcher's false positives (D13). A3 returns the original defective output 48.7 % of the time; A1/A2 never do |
| **Downstream propagation (§0.1 A9)** | ✅ `out_study/T2D`, 90 defects, 447/447 conditions, one session each. E1 accepted: clean 84.4 %, unrepaired 80.0 %, A1 88.8 %, A2 88.6 % (unrepaired − clean −4.4 pp [−14.4, +6.7]). E3 divergence of the final report from clean: noise floor 2.6 %, **unrepaired 10.8 % (+8.2 pp over noise [+5.6, +11.0])**, A1 6.7 % (+4.1 pp [+1.4, +6.8]), A2 7.4 %; A1 − unrepaired −4.2 pp [−7.5, −1.0]; A1 − A2 −0.6 pp. E2 (O5): planted issue in the final report **70 % unrepaired → 0 % after A1 or A2**. **Reading 1 holds (silent propagation); reading 2 holds partly** (repair removes the planted issue but leaves +4 pp divergence from regeneration churn). **The report check rewards propagation:** of 20 unrepaired O5 runs, the 14 that carried the planted issue into the report were all accepted and the 6 whose report dropped it were all rejected (`report_containment`). Coupling: all 8 A1 runs whose defect was not repaired passed every downstream check; 10 of 81 repaired runs did not. The report stage needed a schema-correction second call in every condition. Clean runs fail the supervisor 16 % of the time (O1/O3 reasoning re-runs ≈ 20 %, consistent with D22's matcher false positives) |
| **Placement + severity wiring** | Wired 2026-10-07 as prereg **§0.1 A5** (`--cell placement`: A1 × {P0, P1, P2, P3}, 45 defects, 540 trials → `T2P`, P1 re-run in-session) and **A6** (`--cell severity`: O1 level 1 vs level 2 = every resolving id of the pattern corrupted, author's choice; A1 at P1, 24 defects, 144 trials → `T2S`). Committed and pushed before either ran. Best-of-k and collateral need no new trials |
| **D19 — overwrite counterfactual (§7)** | ✅ `out_study/T2D19`, 23 defects, **138/138 usable**. **A1 retry repaired 69/69 (23/23 defects, exact 95 % CI over defects [85.2 %, 100 %]), collateral 0 %**; A3 regeneration 97.1 %, collateral 30 %. Overwrite = 100 % at 0 calls; retry = 1 call, ≈ 22k tokens. **§7's pre-fixed reading: the overwrite was a cost optimisation, not a correctness decision**; §4.5's principle rests on the zero-call argument alone |
| **C1 — constraint completeness (§0.1 A1/A3)** | ✅ `out_study/T2C1`, 37 defects, **444/444 usable**, all 12 trials per defect in one session. Gap under C0 **−1.8 pp [−6.3, +1.8]**, under C1 **−1.8 pp [−6.3, +1.8]**, difference **0.0 pp [−6.3, +6.3]** — two gaps with CIs, never a test (D8c). Stating the constraints at retry time changed nothing measurable; prediction was "undetectable" |
| **Serving drift (C1 pass vs core)** | 222 re-run C0 trials paired with the core's by defect/arm/rep: **96 % same outcome class, 83 % byte-identical output**. Temperature 0 is not run-to-run determinism (§14.1); 9 flips, 7 of them toward `repaired` |
| Suite | **358 pass**, 13 integration deselected (2026-10-07); `test_repair_analysis.py` now 31 |
| Commits | `2515fcf` core data + analysis · `4d03268` passes + amendments A2–A4 · `212d02f` D19 data · `66c0e07` C1 · `c13f5af` placement · `e657b65` severity · `0f20f66` warm · `657bd00` Tier 1 · `0428190` downstream |
| **Results record** | **`RESULTS.md`** — every cell's numbers with their source, the §5 predictions against results, and the remaining secondaries: O5 matcher sensitivity (confirmatory result unchanged under all four criteria), defect origin (A1 accepted at P0 for 98.5 % of injected vs 28.2 % of real defects), change-then-resolve, class ordering (prediction reversed), C6 detection curves, coupling 13/13 |

---

## 0a. Thirty seconds — where things actually stood (2026-09-08)

**The build is wired, the D11b collection is DONE, and the pre-registration's
four blockers are CLOSED (2026-09-08). Zero *trials* have run.** The only calls
spent on this study are the 8 Phase-A dumps (2026-08-26).
**Nothing from 2026-08-25 onward is committed** — four sessions of work.

### ⛔ THE GATE IS NOW THE FREEZE TAG (updated 2026-09-14)

Everything was committed and pushed 2026-09-14. **Committing is not
freezing**: the freeze is the annotated tag `prereg-freeze`. **No trial may run
before the tag.** Q1 was measured and decided the same day (`JOURNAL_PLAN.md`
§17), and it opened one pre-freeze item, `PREREGISTRATION.md` §11 item 5. What
was on the free list before that is done:

| Was | Now |
|---|---|
| D20 gates specified, not wired | ✅ **Wired** in `build_plan`, two denominators. Both gates pass **142/142** across seeds 0/1/42/20260803 — **N stays 142, 1,167 trials**, power figure stands as computed |
| Prereg blocker 1 — pool the contrast? | ✅ **Pool for the contrast, never pool the rates.** O1 × arm interaction promoted to a secondary reported unconditionally |
| Prereg blocker 2 — D19 in scope? | ✅ **In scope**, exploratory, sequenced after the core. Scorer prerequisite **built** (O4 anchor + `CAN_DELETE` + `_hosts`) |
| Prereg blocker 3 — the gates | ✅ see row 1 |
| Prereg blocker 4 — McNemar dichotomy | ✅ **Majority** (> half of completed reps); `any-of-3` and `unanimity` rejected with reasons |
| `injection_matrix.json` stale at 20 dumps | ✅ **Regenerated** at 28 dumps (191 all-operator, 142 repair, yield 5.07) |
| Memo §11 said "6 of the 11" | ✅ **Corrected to 8 of 13** — the matcher bug's share went *up*, 55% → 62% |

✅ **Q1 and Q2 answered 2026-09-14** (`JOURNAL_PLAN.md` §17). **Q2:** paper #1
stands as submitted; the matcher defect is a journal-paper finding. **Q1:** Tier 1
shrinks 13 → 6 under a content matcher, and the bug reaches O5's *scoring* but
not its *manipulation* — so the production supervisor stays as shipped (D22) and
the scorer is corrected.

### ▶ Before the freeze tag, in order — supersedes the "First actions" table below

| # | Do | Why |
|---|---|---|
| ~~1~~ | ✅ **DONE 2026-09-14** — O5's check on content words (D22) | — |
| ~~2~~ | ✅ **DONE 2026-09-14** — O5 anchor on Jaccard ≥ 0.20 (D24); restoration stays on the production matcher | — |
| ~~3~~ | ✅ **DONE 2026-09-14** — Q3 pool · Q4 D19 after the core · Q5 majority | — |
| ~~3b~~ | ✅ **DONE 2026-09-14** — A3 re-roled as a regeneration baseline (D25); the confirmatory set is A1 vs A2 alone (`JOURNAL_PLAN.md` §17.7) | — |
| ~~4~~ | ✅ **DONE 2026-09-14** — pre-registration frozen at annotated tag `prereg-freeze` (commit `5f78d21`), pushed | — |
| ~~5~~ | ✅ **DONE 2026-09-14** — live smoke test **7/7 passed** (A1/A2 at P1; A1 at P0, P2, P3; A0 at P1; A3 at P0), fallback disabled, none skipped for provider errors, 6 min 49 s. It covers one reasoning-stage defect only, so the D22/D24 O5 scoring path has not yet run live | — |
| **▶ 6** | **The ≈1,180-trial core (1,167 planned), after an API budget check** — `scripts/run_injection_study.py` with `LLM_DISABLE_FALLBACK=1`. The first rows it writes are the study's first trial data | A credit ceiling was hit once already; a trial is 1–3 calls |
| 7 | **The C1 cell, after the core** — same runner, `--c1`, **222 trials** on 37 defects. Built 2026-09-20; exploratory, and it changes nothing above | It reuses the C0 base (D8b), so it is retry trials only. Sequenced after the core because it is an estimate with a CI, never a test (D8c) |

### ▶ First actions, in order

Items **3–5 cost nothing and are blocked on nobody** — no API calls, no
dataset, no answer needed — so do them while the supervisor questions are out.
Item 6 is also free but waits on the answers to Q3 and Q4.

| # | Do | Why it is first |
|---|---|---|
| **1** | ⛔ **`git add` + commit + push.** Unstage the drawio false alarm first: `git reset docs/paper/Evaluation_as_Supervision.drawio`. ⚠ Never commit `backend/.env`. | Three sessions sit on one disk, including 8 paid-for dumps and an audit that cannot be re-run. `git status --short` is the check; §11 below is the manifest. Verified safe: every large data file is gitignored, so `git add -A` cannot pull in the 5.4 GB `yelp.db`. |
| **2** | **Send `PHASE0_MEMO.md` §11 + §12 to the supervisor.** **Five questions**, numbered continuously across the two sections: **Q1** fix the matcher now? · **Q2** what to tell the conference, given #1 is in review · **Q3** pool the primary contrast or estimate it in the severe cell · **Q4** is D19 (the overwrite counterfactual) in scope · **Q5** the McNemar dichotomy. | Q1–Q4 gate the money. Everything below is free; the ≈1,180-trial core is not. |
| ~~3~~ | ✅ **DONE 2026-09-08** — D20 gates wired into `build_plan`; both pass 142/142 across four seeds, so N and the 1.1 pp margin are untouched. | — |
| **4** | **Measure the Tier-1 matcher shrinkage** (memo §11 Q1). | Read-only, dataset-free. The decision should not be made with the size of the consequence unknown. |
| ~~5~~ | ✅ **DONE 2026-09-08** — decided **majority**, with `any-of-3` and `unanimity` rejected on the record. Items 1 and 2 decided too; §11 is empty. | — |
| **⛔ 6 — NOW THE GATE** | **Freeze and commit `PREREGISTRATION.md`.** §11 *is* empty. | A pre-registration not in git before the first trial is not one. Nothing downstream may run until this commit exists. |
| 7 | Live 7-cell smoke test (`tests/test_injection_seam_live.py -m integration`, 7–21 calls) — the seam is wired but has never made a call. | First real money. |
| 8 | The ≈1,180-trial core, after confirming API budget. | — |

⚠ **D13 is done, and it returned a finding against the supervisor rather than a
reassurance. Two blinded human raters called 0 of 11 real, production-caught
defects an error. Read `JOURNAL_PLAN.md` §15 before planning anything else** —
it changes what the repair study can claim and it touches a paper under review.

⚠ **Supervisor methodology review landed 2026-09-02 — four points, all accepted,
recorded as D18–D21 in `JOURNAL_PLAN.md` §3.7.** D18 (`deleted` outcome class)
is **implemented**; D19–D21 are open. There is now a
**`docs/paper/PREREGISTRATION.md`** — draft, **not yet frozen**, with **four**
blocking items in its §11. **It must be committed before the first trial**, and
one of them (pool or split the primary contrast) moves the power gate: excluding
O1 takes N from 142 to 118 and the MDE from 10.9 pp to **11.9 pp against the
12 pp threshold**.

| | |
|---|---|
| Tests | **322 pass**, 13 integration deselected. Measured 2026-09-20; the 278 recorded here was the 2026-09-08 figure and had not been updated through the 2026-09-14 matcher/A3 work. **+24 on 2026-09-20** for the C1 cell |
| Gates | replay **159/0** · injector cross-check 191 applicable · prompt audit 5/5 · scorer selftest · `--plan-only` **1,167 trials** (and **1,389** with `--c1`), order OK · suite **322 pass** · ✅ **D20 gates wired and passing 142/142 on both** (injection success 1.00, trigger 1.00) |
| **Collection (D11b)** | ✅ **DONE 2026-08-26.** 8/8 ok, observe mode, no truncation, ~49 min. **28 dumps.** N **142** (predicted ≈143), yield **5.07**/dump. Tier 1 **11 → 13**, cells 5→7, businesses 4→6 |
| **Power gate** | ✅ **PASS at N=142, r=3** — MDE **10.9 pp** w/ occasion vs X **12 pp**, margin **1.1 pp** (§16.5). ✅ **And it survives the matcher fix**: swept 120–150, MDE stays under 12 pp even below the worst case of losing O5 entirely (§16.6). Contingency if N drops under ~130 is **r=4** |
| **D13 audit** | ✅ **complete 2026-08-26.** κ **0.870** CI [0.674, 1.000], 29/31 raw, 0 `U`, two human raters. **Tier 1: 0/11 called an error. Tier 2: 16/20.** See §15 of the plan |
| Decided & approved | **D11b** grow the sample (+8 dumps, N→≈143, X stays 12 pp) · **D8b** one shared C0 base · **D8d** C1 at 40 defects · the four §7 positions |
| Study size approved | core **≈1,180** trials + C1 **≈240** = **≈1,420 trials ≈ 1,420–4,260 calls**. Realised: core **1,167** + C1 **222** = **1,389** |
| Still outstanding | **D5b** local model · **§7 item 3** warm-resample (REQUIRED by D2, not built, needs a *choice*) · ⛔ **the `untraceable_recommendation` matcher bug** — fix it, and decide what it means for the paper under review (memo §11) · ⛔ **D19** O4 counterfactual: in scope? · ⛔ **D20** gates specified, **not wired** · ⛔ **D21** pre-registration DRAFT, 4 blockers (memo §12) |

### ⛔ NUMBERS SUPERSEDED 2026-08-26 — read this before believing anything below

The D11b collection ran. **Every figure computed over 20 dumps is historical.**
Where this file or the plan disagrees with the table below, **this table wins**;
the authoritative record is `JOURNAL_PLAN.md` §16.

| Quantity | old (20 dumps) | **now (28 dumps)** |
|---|---|---|
| Phase-A dumps | 20 | **28** |
| Tier-2 ceiling N | 102 | **142** |
| Core trials | 822 | **1,167** |
| Tier-1 usable defects | 11 | **13** |
| Tier-1 cells / businesses | 5 / 4 | **7 / 6** |
| Retry observations | 15 | **19** |
| Replay facts | 135 | **159** |
| Yield per dump | 5.1 | **5.07** |
| MDE w/ occasion (r=3) | 12.6 pp ✗ | **10.8 pp ✓** vs X = 12 pp |

Per-operator applicability: **O1 24 · O2 24 · O3 22 · O4 23 · O5 20 · O6 26 ·
O7 26 · O8 26** (191 all-operator, **142** with a repair endpoint).
Arms: **A1 426 · A2 426 · A0 213 · A3 102**.

So: **822, 102, 11, 135, 15, "20 dumps" and "N=102" are all stale below.** They
are left in place because they record why decisions were made, not what is true.

**Do these in this order.** Each gates the next.

1. ⛔ **Commit.** Two sessions of work sit on one disk. See §11 for the manifest.
2. ✅ **Collect 8 Phase-A dumps — DONE 2026-08-26.** 8/8 ok in observe mode, no
   truncation, ~49 min. All four downstream figures were recomputed and the
   power gate re-checked: **N=142, 1,167 trials, MDE 10.9 pp < 12 pp.** Full
   record in `JOURNAL_PLAN.md` §16. ⚠ **Do not re-run this** — the dumps are on
   disk and `run_study.py` skips them by checkpoint anyway.
   ⚠ `MAX_REVIEW_SAMPLE` must be **set inline** for a collection run, not left
   in `.env`: it also bounds `ReportRequest.sample_size`, and the suite pins
   that bound. `.env` now holds **500**, the hard ceiling, and the unit test
   matches. 1000 raises at import.
3. **Smoke-test the live seam** — `pytest tests/test_injection_seam_live.py -m
   integration`, 7 cells, 7–21 calls. The seam is wired but has never made a
   call. **This is now the next thing that spends money.**
4. ✅ **The blinded defect-bank rating (D13) is DONE** — rated, scored and
   verified 2026-08-26. The hard sequencing constraint is discharged: it
   happened before any core result existed, so the blinding is intact and
   cannot be lost later. Results in `JOURNAL_PLAN.md` §15.
5. ⛔ **NEW — decide the matcher bug before the core runs.** §15.4: the
   `untraceable_recommendation` check compares *characters*, not content, so it
   cannot separate a real paraphrase from injected alien content. It accounts
   for 6 of the 11 Tier-1 defects. Fixing it likely shrinks the Tier-1 bank from
   11 toward ~2–5, and it touches conference paper #1, which is **under review**.
   Measure the shrinkage first (read-only, dataset-free); then it is a
   supervisor call.
6. **Run the core** — ≈1,180 trials. ⚠ Check the API budget first; a credit
   ceiling was hit once already.

⚠ **Do not spend on steps 2 or 5 without confirming the budget** — a trial is
1–3 calls, not 1.

---

## 1. Status

**Updated 2026-08-25 (second pass — seam wired, memo written, plan corrected).**
Everything is on `main`; the `journal/build-b1-b3-and-plan-corrections` branch
was merged and is gone.

**266 tests pass** (257 before the 2026-09-02 supervisor review added D18's 9;
195 at the start of 2026-08-25). Everything from all three days is
**uncommitted** — see §11 for the manifest.

| Track | State |
|---|---|
| Conference paper #1 | **Submitted, under review.** Nothing to do but wait — except the cheap, time-sensitive item: email the chairs about an extended-version route *while* it is in review. |
| Journal / repair study | ~~Build complete and wired. No trial has run.~~ **Superseded — see §0:** every cell except C7 ran 2026-10-05 → 08. |

### ✅ Decisions taken and approved 2026-08-26

- **D11b — keep X = 12 pp, grow the sample.** Collect 8 more Phase-A dumps in
  **observe mode**; N 102 → ≈143, power 0.883 and MDE 10.8 pp *with* the
  occasion effect, margin 1.2 pp. Rejected: lowering X (post-hoc), raising X to
  13 (free, conservative, but forfeits the split), and r=4 at N=102 (≈1,120
  trials vs ≈1,180 — near-identical cost, worse MDE, because repetitions of one
  defect are correlated and a new defect is not).
  ⚠ **The core grows with the sample: 822 → ≈1,180 trials.** The ~30–55
  collection calls are the small part of the bill. Re-run `--plan-only` after
  collection; the ≈1,180 is arithmetic, not measurement.
- **D8b — option (ii): one C0 base shared by C0 and C1; only the retry prompt
  varies.** Decided on **validity**, not cost: regenerating the base under C1
  would break the within-defect matching every other contrast depends on, and
  would confound the difference-in-differences with C1 having made the clean
  output cleaner. Consequence: the paper claims *retry-time constraint
  disclosure*, not a constraint-complete pipeline.

**✅ Supervisor approved 2026-08-26**, along with **D8d: the C1 cell runs at 40
defects (≈240 trials)**, not 80.

**Study size as approved:** core ≈1,180 + C1 ≈240 = **≈1,420 trials
≈ 1,420–4,260 calls**, before the placement, severity and P3 cells.

**Two things approval did NOT settle.** (1) **D5b** — the local model, still
open; needed before Phase 4/C7, or immediately on the ESEM registered-report
route. (2) **§7 item 3, the warm-resample subset** — D2 marks it REQUIRED and it
is not built; the memo asks for a *choice* (build / drop / defer) and a
ratification does not make one. **D13 is ✅ done** — executed 2026-08-26 by two
blinded human raters, and it produced §15's finding plus the new memo §11
question about the matcher bug and paper #1.

### What changed in the second pass of 2026-08-25

1. ✅ **The live seam is wired.** `run_injection_study._regenerate` no longer
   raises. `BaseAgent` gained a prompt/execute seam — `build_prompt` +
   `run_messages`, with `run()` composed from them — so all three stage agents
   expose the prompt production sends, and `arms.build_messages` wraps *that*
   rather than a re-typed copy. `nodes.stage_payload` does the same for the
   stage's input. Production behaviour is unchanged and pinned per agent by
   `tests/test_agent_prompt_seam.py`.
2. ✅ **`PHASE0_MEMO.md` is written**, and on **2026-08-26 two of its four
   questions were decided** — see the box below. **This is still the document
   that gates the run**: three questions remain, and nothing has been spent.
3. ✅ **`JOURNAL_PLAN.md` is corrected** against the computed figures — §3's
   D4c/D4d/D4f/D8c/D11b/D12 rows, §6.1b's power table and §6.2's grid, each
   marked in place with its date and regenerating command.
4. ✅ **`power.py` gained a §9** that reports power at the *computed* defect
   counts instead of the `8 × dumps` multiplication. The plan can now cite a
   number a script prints.
5. ✅ **The typed power figures were right.** Computed at `--sims 20000`,
   N=102 r=3 is **0.801 power / 11.9 pp MDE** against the typed 0.790 / 11.9 —
   the MDEs reproduce exactly and the powers differ by 0.011, inside Monte
   Carlo error. Same for N=143 (0.913 / 10.2 vs 0.902 / 10.2) and for D8c.
   ⚠ **An earlier version of this list claimed all four figures "moved". That
   was wrong** — it compared two noisy 2,000-simulation runs and read the noise
   as a correction. What the recomputation actually buys is reproducibility and
   the **shared-occasion column**, which the typed row never had: at N=102 the
   MDE is 11.9 pp bare but **12.6 pp under the occasion effect the design will
   face**, i.e. above D11b's threshold rather than a hair below it.

**B1, B1b, B2, B3** (2026-08-24) **plus B4, B5, B6, B7, B8** (2026-08-25). The
runner enumerates 822 trials over 102 defects and its `--dry-run` works end to
end. **One seam is deliberately unwired** — see §4.

**Gates, all green** — re-run before trusting anything below (§8):

- `pytest -m "not integration"` → 195 passed
- `replay_stage.py --verify out_study` → 135 facts, 0 mismatches
- `inject_defects.py --matrix` → the Tier-2 ceiling, computed
- `prompt_audit.py` → 5 of 5 constraints feedback-only, no drift
- `run_injection_study.py --plan-only` → 822 trials, order OK

### ⚠ Six numbers changed on 2026-08-25. The plan is stale where it disagrees.

1. **The Tier-2 ceiling is 102, not 160.** `8 operators x 20 dumps` assumed
   every operator can use every dump. Four things break that: operators are
   **stage-specific**; stages differ in **clean bases** (reasoning 18, strategy
   17, report 19 of 20); **O3** needs a pattern with an aspect its *resolving*
   evidence lacks, which is 15 not 17; and **O4/O8 carry no repair endpoint**.
   Now computed by `inject_defects.matrix()` and pinned in
   `tests/test_inject.py`. Per-operator: O1 17, O2 17, O3 15, O4 16, O5 15,
   O6 19, O7 19, O8 19 — 137 in total, **102 with a repair endpoint**.
2. **O4 cannot be a repair operator at all.** It never produces a retry (a
   frequency divergence is `proceed_with_warning`), and `graph.py:140` then
   overwrites the claimed value deterministically via
   `apply_frequency_corrections`. There is no retry for an arm to act on and no
   LLM involvement in the correction. It is kept as a **warn-level** operator so
   grid composition stays a config flip (`inject_defects.ENDPOINT`).
3. **O4's multiplier parameterization was broken independently.** Median claimed
   frequency on this corpus is **0.16**, so f=1.1 moves it by 0.016 — under the
   0.05 tolerance. **81 of 89 patterns would have been silent no-ops.**
   Re-parameterized as **absolute divergence**, which is constructible for every
   pattern. Keep 1.6–1.8x as a provenance note only.
4. **O8 is a declared positive control**, not a repair operator: `report_node`
   passes the correct metadata in the prompt payload, so any retry copies it
   back at ~100% in every arm. Its repair rate should be 1.0; below that means
   the scorer is broken.
5. **Power at N=102, r=3 is 0.790** — under 0.80 — with **MDE 11.9 pp** against
   D11b's 12 pp split threshold. The margin is gone. **See §4 item 1.**
6. **Trial budget is 822, not ~1,320.** Smaller N, plus D4c allocating arms over
   **defect subsets** rather than over repetitions (A1 306, A2 306, A0 144,
   A3 66).

**Three findings that changed the design (2026-08-24), still current:**

1. **The Tier-1 defect bank is 11, not 15**, over two stages, in 5 clusters.
   MDE ≈ 31 pp and the cluster bootstrap over-rejects, so **Tier 1 cannot
   support inference** — realism anchor only.
2. **The Tier-2 core must run at placement P1** (D10).
3. **D8's constraint-completeness interaction is undetectable** at any
   affordable size (0.19 power at 160/160). It is an estimate, not a test (D8c).

**And one that got stronger:** the A1 feedback discloses **5 of 5** supervisor
obligations that no stage prompt states — §13.1 said four. All three stage
prompts are pure output-schema descriptions. `prompt_audit.py` proves it and
fails if either side drifts.

---

## 2. Read in this order

1. **`JOURNAL_PLAN.md` §3 first** — the decision table, restructured 2026-08-24
   from chronological into functional order (D1–D17 in six groups). **⛔ marks
   the seven blockers; ❓ marks the open questions — **one now (D5b), after
   D11b, D8b and D8d were approved on 2026-08-26**; **D13 is ✅ complete —
   executed 2026-08-26, results in §15**. ⚠ **Then §3.7 — D18–D21, the
   supervisor's methodology review of 2026-09-02.** D18 is implemented; D19–D21
   are open and two of them need a supervisor answer. Read those, and you have
   the design.

   Then the rest of the plan (~1,050 lines). It grew by accretion: **§13 and
   §14 amend earlier sections**, so where §5/§6 and §13/§14 disagree, the later
   section wins. **Exception:** the 2026-08-24 passes (banners at the top of the
   file) **edited §3/§4/§5/§6/§8 in place** — those are current, not superseded,
   and they are the parts checked against the repository and against
   simulation rather than against the literature.
2. **`PREREGISTRATION.md`** — ⚠ **new 2026-09-02, and the shortest complete
   statement of what the study will do.** Estimand, primary contrast, outcome
   classes, exclusions, the split rule, and what is exploratory. **Still DRAFT:
   four items in its §11 block the freeze, and it must be committed before the
   first trial or it is not a pre-registration at all.**
3. **`PHASE0_MEMO.md`** — what is being asked of the supervisor and why. §11 is
   the matcher bug; **§12 is the 2026-09-02 review and the three decisions it
   created**. It is the gate: until it is answered, the next action is not
   "run the study".
4. **`PUBLICATION_STRATEGY.md`** — how many papers this becomes, what is left
   for the journal if the repair study splits off, whether either claim is
   significant enough, and the constraints that follow from #1 being in review.
   Short, and it decides things §12 of the plan could not.
5. This file, for traps and do-not-redo items.

⛔ **Do not read `HANDOFF.md` for instructions.** It is the conference-era
handoff and three of its statements are *wrong*, not merely stale — most
dangerously its §1.3, which claims `docs/paper/` is gitignored. It is not. The
file now carries a correction table at the top; treat it as a historical
record.

⚠ **`READING_PROMPTS.md` no longer exists** — it is in neither copy of the repo
and was never committed. The Tier-A/Tier-B extraction prompts are lost; the
extractions themselves survive at `..\Reading List\` (§3). Rebuild the prompts
from those extractions if Tier C needs them.

Do **not** re-explore the repository first. Do **not** re-read the papers —
the extractions already exist (§3).

---

## 3. Where everything lives — including outside the repo

| What | Path | On GitHub? |
|---|---|---|
| Journal plan | `docs/paper/JOURNAL_PLAN.md` | **Yes** (tracked 2026-08-24) |
| **Phase-0 memo (the gate on the run)** | `docs/paper/PHASE0_MEMO.md` | **Yes** (written 2026-08-25) |
| Publication strategy (split decision, venues) | `docs/paper/PUBLICATION_STRATEGY.md` | **Yes** |
| Conference paper source | `docs/paper/main.tex`, `references.bib` | **Yes** (rescued 2026-08-24) |
| **Tier A extraction (5 papers)** | `..\Reading List\Tier_A\Tier_A_extraction.md` | **No — outside the repo** |
| **Tier B extractions (9 papers)** | `..\Reading List\Tier_B\related_work_tierB_triad.md` and `related_work_B-III.md` | **No — outside the repo** |
| Paper PDFs | `..\Reading List\Tier_A\` and `Tier_B\` | No |
| Study dumps (251 stage JSONs) | `backend/out_study/*/*/` | **Yes** |
| Study checkpoints (`observations[]`) | `backend/out_study/**/checkpoint.jsonl` | **Yes** (was ignored until 2026-08-24) |
| Defect bank (generated) | `backend/out_study/defect_bank.json` | Yes |
| Supervision layer | `backend/app/core/supervision.py` | Yes |
| Reading prompts | *gone* — see §2 | — |

⚠ **The "gitignored on purpose" note that used to sit here was wrong and has
been removed.** `docs/paper/` has been tracked since the journal-edition switch,
and `git status` is clean because the work is *committed*, not because it is
ignored. The remote is
`https://github.com/Hahhahahaadsa/Evaluation-as-Supervision-Journal-Edition.git`.

⚠ **Two physical repo directories exist.** `Tài liệu` appears on disk in two
Unicode normalisations (NFD and NFC) and they render identically in every
listing. The **NFD** one holds the git repo, `Reading List/`, `venv/` and the
dataset. The **NFC** one is a stray shadow with no `.git`; until 2026-08-24 it
held the only copy of the conference paper source. If a file you are certain you
wrote is missing, look there before rewriting it. It should be deleted once
confirmed empty of anything unique.

⚠ **Data-loss inversion, now fixed.** `.gitignore`'s blanket `*.jsonl` rule
meant the repository tracked the `.bak` files recording *failed* runs while
ignoring every `checkpoint.jsonl` — the `observations[]` behind every paper
number and the entire defect bank, ~143 KB, on one disk only. A negation rule
(`!backend/out_study/**/*.jsonl`) now tracks them.

---

## 4. Journal extension — the design

Goal: measure whether feedback-injected retry **repairs** a detected defect —
the quantity the conference paper honestly could not measure. ⚠ Say **"repair by
regeneration"**: the retried stage regenerates its whole output rather than
editing the faulty artifact (D17).

- **Two tiers.** Tier 1 replays real defects captured on disk (**13 usable,
  2 stages, descriptive only** — 11 before the D11b collection); Tier 2 applies
  synthetic operators to clean outputs and **carries every rate and the stage
  comparison**.
- **Four arms.** A0 capability ceiling · A1 measured-fact feedback (production
  path) · A2 generic rejection · A3 bare re-draw (a determinism floor at
  temperature 0, not resampling).
- **Placement — four levels (D9).** **P0** artifact absent (production;
  Tier-1 default) · **P1** user-turn artifact (**Tier-2 default, D10**) ·
  **P2** assistant-turn · **P3** exploratory. ⚠ **Not fully crossed** — A0 × P0
  and A3 × P1 are structurally undefined (D9b).
- **Analysis.** Three confirmatory tests under Holm; Cochran's Q on the
  **dichotomised** outcome (it is a binary test); A1/A0 ratio by **cluster
  bootstrap**, not delta method; outcome is a **4-class multinomial crossed with
  a binary collateral flag** — {`repaired`, `replaced`, `deleted`,
  `unrepaired`}, `deleted` added by D18 on 2026-09-02; the *original* four
  classes were not mutually exclusive, these four are because they are decided
  in a fixed order. **Pre-register as estimation, not NHST** (D4f) — and the
  pre-registration is now a document, `PREREGISTRATION.md`, still DRAFT with
  four blocking items in its §11.
- **Venue.** EMSE regular track for the journal; ASE and the ESEM registered
  report are live conference options. All deadlines cited are **unverified**.

### Next actions, in order

**Items 2, 3 and 4 are done. The remaining work is items 0, 1 and 5, and item 0
gates the other two.**

0. ⛔ **Get `PHASE0_MEMO.md` ratified.** D11b, D8b and D8d are **decided and
   approved 2026-08-26**, and **D13 is executed** — but nothing has been spent
   on the study itself. What is live in the memo now is **§7 item 3** (the
   warm-resample choice), **§5 (D5b)**, and — new and most urgent — **§11, the
   matcher bug D13 uncovered.** Item 1 spends the supervisor's API budget and
   item 6 spends a great deal of it, so neither should start before the memo
   comes back.
   ⚠ **D5b does not block items 1–6**; it is needed before Phase 4/C7 only
   (unless the ESEM registered-report route is taken, which needs the whole
   protocol filed up front).
   ⚠ **§11 DOES block the core run.** It decides how large Tier 1 actually is,
   and re-deriving that after trials have run means re-running them.
   ✅ **D13 no longer needs scheduling at all.** It ran before any core result
   existed, so the blinding held and cannot now be lost — the study's one hard
   sequencing constraint is permanently discharged.

1. ⛔ **Collect 8 more Phase-A dumps — ✅ decided (D11b, 2026-08-26), not yet
   run.** At N=102 the MDE is **11.9 pp** — a 0.1 pp margin under D11b's 12 pp
   split threshold, and **12.6 pp** once §14.1's shared-occasion effect is
   counted, which puts it above the threshold. That threshold is
   *defined* as "must be ≥ the MDE" — so the pre-registration
   is incoherent as it stands. Measured yield is **5.1 repair defects per
   dump**; +8 dumps → N≈143 → power **0.913** (0.883 with the occasion effect),
   MDE **10.2 pp** (10.8), margin 1.8 pp (1.2 pp).
   Computed by `power.py --sims 20000`, seed 42.
   - **Run them in observe mode.** Phase A was observe-mode, which is why dumps
     with `retry` verdicts still sit on disk. Enforce mode fires retries and
     applies `apply_frequency_corrections`, giving post-retry,
     frequency-corrected outputs that are **not comparable bases**.
   - Collect 8, not 6: the 5.1/dump yield is itself estimated from 20 dumps.
   - This is the **only** remaining step that needs the Yelp dataset and
     `MAX_REVIEW_SAMPLE=214`. Everything else is dataset-free.
   - ⚠ **Cost is NOT just the ~30–55 collection calls.** More defects means more
     trials: the core scales at ~2.75 arm-cells per defect per repetition, so
     102 → ≈143 defects takes it from **822 to ≈1,180 trials**
     (≈1,180–3,540 calls). An earlier version of this line called the collection
     "negligible against 822 trials" and ignored that the 822 itself grows.
   - Base provenance does not confound: matching happens within-defect at trial
     time, all arms in one session per §14.1.

2. ✅ **`run_injection_study._regenerate` is wired** (2026-08-25). Nothing to
   do. What was built, so it is not re-derived:
   - `BaseAgent.build_prompt(input_data) -> (messages, original_task)` and
     `BaseAgent.run_messages(messages, original_task, input_data)`, with
     `run()` composed from them via `_with_feedback`. `AGENT_NAME` and
     `OUTPUT_SCHEMA` are class attributes; `report_agent` overrides
     `_postprocess` to restore `business_name`/`sample_size` from upstream.
   - `nodes.stage_payload(stage, state)` — the stage input, factored out of the
     graph node that builds it, so the runner cannot drift from the pipeline it
     measures. `analysis_agent` raises rather than returning an empty batch.
   - `_regenerate` builds the payload from the **base** state, wraps
     production's own messages with `arms.build_messages`, and **clears every
     stage downstream of the retried one** — the dump's strategy/report came
     from the pre-injection output and are not that trial's downstream.
   - `run()` sets `LLM_DISABLE_FALLBACK=1` on live runs. A silent failover
     inside one defect's arms is indistinguishable from a slow call in the logs
     (B2), and it breaks the matched comparison.
   - `tests/test_injection_seam_live.py` is an **integration-marked** smoke
     test: **7 cells, one per defined (arm, placement) shape**, on one real
     defect. It is the only part of the wiring a live call can verify — that
     the assembled arm is accepted by the provider and comes back
     schema-valid — and it costs 7–21 calls. P2 and P3 in particular produce
     message shapes the production path never sends (artifact in an assistant
     turn; two adjacent user turns). **Run it before committing to the 822.**

3. ✅ **The Phase-0 memo is written and answered** — `docs/paper/PHASE0_MEMO.md`.
   **Approved 2026-08-26**: D11b, D8b and D8d, plus the four §7 positions.
   ⚠ **Two things approval did not settle** and they are the live items:
   **D5b** (local model) and **§7 item 3** — the warm-resample subset, which
   D2 marks REQUIRED and which is not built; that one asks for a *choice*
   (build / drop / defer) and a ratification does not make one. **D13** is not
   open in method — the instrument is built — it needs a *person*. The full
   list:
   - ✅ **D8b — DECIDED 2026-08-26: option (ii)**, one C0 base shared by both
     conditions, only the retry prompt varies.
   - ✅ **D11b — DECIDED 2026-08-26:** keep X = 12 pp, collect 8 more dumps.
     Re-check the MDE against the delivered N **before** any trial.
   - ❓ **D5b** — which local model, quantisation, seed **and runtime settings**?
     A seed alone is not determinism: batch size, thread count and GPU-offload
     layers can all move the output, and C7's whole selling point is that A3
     comes back byte-identical. Deferrable to before Phase 4 — unless the ESEM
     registered-report route is taken, which needs the whole protocol up front.
   - 🔧 **D13 — method settled, instrument built 2026-08-26**
     (`scripts/analysis/rater_sheet.py`, 16 tests). Groundedness is verified
     programmatically — **verification, not a rating**, no κ applies. A human
     rates *meaningfulness* over 31 blinded items (11 Tier-1 + 20 Tier-2,
     every repair operator represented) against one binary question. What is
     still needed is a **person**: an hour, as rater 2.
     ⚠ **The rating must happen before core results exist** — once they do,
     nobody is blind. That is the only hard sequencing constraint in the study.
   - ✅ **D8d — DECIDED 2026-08-26: 40 defects (≈240 trials)**, not 80. C1 is
     an estimate, not a test, so a ~1.4× wider CI is a small price for halving
     the cell.
   Plus **D12 sign-off** — the runner is already built to its stated position
   (full retried output + re-runnable downstream state persisted).

4. ✅ **`JOURNAL_PLAN.md` is corrected** (2026-08-25). Done rather than held:
   editing a pre-registration is legitimate *before* data collection, and every
   edit is marked in place with its date, its old value and the command that
   regenerates the new one — so the supervisor ratifies a visible change rather
   than discovering a silent one. §7 of the memo puts it up for sign-off.

4b. ⚠ **Known gap: the warm-resample subset (D2) cannot be run.** D2 marks
   temperature > 0 as "REQUIRED, not optional" — it carries Olausson's
   equal-budget comparison against A3 — but `BaseAgent._create` hard-codes
   `temperature=0` and nothing threads a temperature through `_call_llm`,
   `run_messages` or the runner. Found during the 2026-08-25 self-review;
   **not** fixed, because it needs its own trial budget on top of the 822 and
   that is a supervisor decision (memo §7, item 3). Build it, drop it from D2,
   or defer it — but do not let it sit as an unbuilt "REQUIRED".

5. **Run the core** — now **≈1,180 trials, not 822**, because D11b grows the
   defect set — then branch on the result (D11/D11b). ⚠ **Check the API budget
   first**: `out_study/B/checkpoint.credit-depleted.jsonl.bak` records a cost
   ceiling being hit once already, and a trial is **1–3 LLM calls, not 1**
   (`attempts_made` is logged per trial for exactly this reason). So the core is
   ≈1,180–3,540 calls, and the study with the C1 cell and the additional
   placements is **≈1,700–6,000**.
   ⚠ Between steps 4 and 5, do the **blinded defect-bank rating** (D13) — after
   this point no rater is blind.

### 4a. Arm wording — frozen 2026-08-25

`arms.AUTHORED_WORDING` lists what was authored here rather than imported. A1 is
exempt: it *is* `base_agent._SUPERVISOR_FEEDBACK_PROMPT`, imported, never
re-typed. Each derivation is recorded beside the constant in `scripts/arms.py`
and pinned by tests. **Confirm at memo sign-off; change before a trial runs, not
after.**

- **A0_PREAMBLE** — "Below is a draft answer to this task. Review it and produce
  the best answer you can to the original task. Return only valid JSON."
  ⚠ **Authorship is deliberately neutral.** An earlier draft said "produced by
  another system"; that contradicts itself at A0 × P2 (where the placement puts
  the artifact in the model's *own* assistant turn) and would bake an
  attribution claim into the **arm** when attribution is what the **placement**
  factor manipulates.
- **A2_FEEDBACK** — A1's template with the measured facts removed and nothing
  else changed: same opening sentence verbatim, same closing instruction
  verbatim, the dangling "these issues" repaired. Matching everything except the
  manipulated variable is what makes A1 vs A2 a *content* contrast.
- **P3_MARKER** — "The answer above contains an error." A **statement, not an
  instruction** (the arm supplies the instruction), naming no field, count or
  check — a marker that discloses what is wrong becomes a weak A1.

Two tests keep these honest: `test_a2_matches_a1_on_everything_except_the_specifics`
and `test_every_arm_ends_in_the_same_output_instruction` — the latter because a
differing output instruction would confound arm with output format and inflate
`attempts_made`.

---

## 5. Blocking issue: D8 (read before building anything)

The A1 feedback **discloses constraints the stage prompts never state**.
Verified 2026-08-24 against the code: `supervision.py`'s retry strings assert
that evidence IDs must resolve, aspects must align, recommendations must trace
upstream, and the report must only restate upstream — **none of which appears in
`reasoning_agent.py`, `strategy_agent.py`, or `report_agent.py`'s system
prompts.**

So an A1 > A2 result would be partly prompt-completeness, not feedback
specificity. Two independent sources say this invalidates the contrast: Huang et
al. (ICLR 2024) §5, and Kamoi et al. (TACL 2024) Table 7's Required row.

**Recommended fix (D8b):** add a constraint-completeness factor — C0 production
prompt, C1 prompt stating all supervisor obligations — crossed with A1/A2 on a
Tier-2 subset (~160 calls, already in the §6 budget). Pre-specify the C1 text and
publish it verbatim. Full options in §13.2.

---

## 6. Do not redo / do not reintroduce

**From the conference paper (still binding):**

1. **Derivability is closure, not linearity.** The report stage reads analysis,
   reasoning *and* strategy.
2. **Restaurant distribution ≠ all-business.** Restaurants only (n=52,268):
   p10=7, p25=14, p50=34, p75=92, p90=214. **Never quote 6/8/15/38/101.**
3. **21 failure modes, not 22** (23 tests; 2 are routing utilities).
4. **Latency overhead is not +0.2%** — that compared single runs and sits inside
   the noise floor.
5. **"Defects don't recur" was wrong** — it conflated "no retry fired" with "no
   defect occurred".
6. **`gemini-2.5-pro` 404s** ("no longer available to new users"). The judge used
   `gemini-3.1-pro-preview`.
7. **Do not delete the quarantined files.** They record failures deliberately:
   `out_study/B/checkpoint.credit-depleted.jsonl.bak` and
   `out_study/judge/results.contaminated.jsonl.bak`.

**New, from the 2026-08-24 literature pass:**

8. **Citation metadata was wrong three times** — always verify venue and status
   in the PDF, never from a web-search snippet. Corrected: Self-Correction Bench
   is **COLM 2026** (not NeurIPS 2025); AgentChaos is **ASE 2026, peer-reviewed**
   (not a preprint); the "Self-Correction Illusion" file is really *Role
   Relabeling Gates Explicit Error Flagging in LLMs* (arXiv 2606.05976v2).
9. **Do not cite MAS-FIRE's ">40%" abstract figure** — no derivation was found in
   its results.
10. **Do not quote any MAST category percentage** until the denominator is
    established — three mutually inconsistent sets appear in that paper.
11. **The Tier-1 defect bank is 13 usable defects over two stages** —
    reasoning **5**, strategy **8**, **report 0, analysis 0** — in **7 business
    × stage cells across 6 businesses**, the largest cell holding 4.
    By class: `untraceable_recommendation` 8, `missing_evidence_id` 3,
    `misaligned_aspect` 2.

    Of **19** retry-triggering observations, **4 are Gemini 503 `status_error`
    retries** and **2 are cascades** — a report stage inventing content to fill
    the gap left when its upstream reasoning stage 503'd and strategy emitted
    nothing. Those are a different estimand and are reported separately.

    ⚠ **Refreshed 2026-09-02 from `defect_bank.py`. Every figure in this item
    changed with the D11b collection** (before it: 15 observations, 11 usable,
    3 api-errors, 1 cascade, strategy 6, 5 cells, 4 businesses) — and earlier
    counts of "15 usable" and "12" were wrong on top of that. **Cite what the
    script prints, never a remembered figure.** `tests/test_replay.py` pins
    these, so a stale plan fails the suite.
12. **Runner iteration order must be `for defect: for arm: for repetition:`** —
    never arm-outer, or arm gets confounded with serving epoch (§14.1).

**New, from the 2026-08-24 code-review, power and self-review passes:**

13. **Do not re-derive the defect bank by hand.** `scripts/analysis/defect_bank.py`
    encodes every exclusion rule and `tests/test_replay.py` pins its numbers, so
    a stale plan fails the suite. Same for the replay gate.
14. **Closed-form power formulas do not apply here** — arms are matched within
    defect, reps nest inside (defect, arm), Tier-1 defects cluster. Use
    `scripts/analysis/power.py`. And remember the **shared-occasion effect**:
    §14.1 forces all arms for one defect into one session, which raises
    arm-to-arm correlation and *costs* power. Ignoring it overstates everything.
15. **160 defects is a hard ceiling** (8 operators × 20 Phase-A dumps). Once the
    sample is exhausted, **r is the only lever** — and reps and blocks buy power
    about equally here, contrary to the usual advice.
16. **Never measure a "baseline" on data from a different serving epoch.** The
    old no-injection control used the recorded Phase-A verdict from weeks
    earlier — confounded by exactly the drift §14.1 exists to prevent (D5c).
17. **Measure churn under the condition the experiment will actually face.** The
    first collateral estimate (37% at the strategy stage) was confounded:
    repetition runs regenerate every stage, but a replay trial pins upstream
    from the dump. Conditioning on stable upstream gives 23%.
18. **The analysis scripts do not share a working directory.** `tally.py`,
    `rep_tally.py`, `rep_verdict.py`, `audit.py`, `check_tex.py` run from the
    **repo root**; `defect_bank.py`, `churn.py`, `power.py`, `replay_stage.py`
    run from **`backend/`**. §8 has the exact commands.
19. **Verify venue deadlines against official CFPs.** Every date in
    `PUBLICATION_STRATEGY.md` §8 arrived second-hand and is unverified — in a
    project whose own §14.9 records citation metadata being wrong three times
    from precisely that sourcing.

---

**New, from the 2026-08-25 build pass (B4–B8):**

20. **Do not re-derive the Tier-2 ceiling by hand.** `8 x 20 = 160` was wrong
    four ways at once (§1). `inject_defects.matrix()` computes it and
    `tests/test_inject.py` pins it, the same contract `test_replay.py` enforces
    for the Tier-1 bank.
21. **O4 is not a repair operator and O8 is a positive control.** Both are
    implemented and both are excluded from the repair grid via
    `inject_defects.ENDPOINT`. Do not silently fold them back in to make N look
    larger — `REPAIR_OPERATORS` derives from that table.
22. **Never define collateral as "anything changed".** Measured against the real
    repetition runs, that fires on **96%** of *unperturbed* regenerations. The
    set-overlap replacement discriminates. Both facts are pinned in
    `tests/test_score_repair.py`.
23. **Churn must use `churn.matched_fraction`** — greedy one-to-one, the same
    function that produced the D3c floors. An `any()` match lets one retried
    item cover several pre-injection items, understates churn, and applies
    floors measured under a different rule. `score_repair` imports it rather
    than reimplementing it.
24. **Apply the strategy floor only to the conditioned population.** The 0.23
    figure assumes stable upstream (symmetric pattern-description match ≥ 0.95).
    Applied to unconditioned rep pairs it reports 56% collateral. This trap was
    hit once during the build and once before, at the original 37% estimate.
25. **Report-stage collateral is UNMEASURABLE, not clean.** D3c calibrated
    reasoning and strategy items only. `Outcome.collateral_measurable` is False
    for O6/O7/O8 and `collateral_rate` is `None`, never `0.0`. Two of the six
    repair operators live at that stage — calibrating a report-stage floor is an
    open opportunity.
26. **Do not infer prompt-constraint coverage by keyword.** A substring
    heuristic returned a false STATED for aspect alignment: the reasoning prompt
    contains "mention", but only inside the *frequency* field's definition. A
    false STATED **understates** the gap. `prompt_audit.CONSTRAINTS` is
    adjudicated with quoted evidence and `verify()` fails if either side drifts.
27. **A retry string may span a line continuation in `supervision.py`.** A
    fragment that crosses the concatenation boundary is never found in the
    source. `prompt_audit.verify()` caught this on its first run.
28. **Arm wording is frozen (§4a), not open.** Changing it after a trial runs
    breaks the pre-registration.

---

**New, from the 2026-08-25 wiring pass:**

29. **The repo is CRLF; the tools are not.** Rewriting a file with a hard-coded
    LF newline reflows every line and produces a whole-file diff that hides the
    real change. Read with `newline=""`, detect the ending, write it back with
    the ending you found. Hit once on `base_agent.py`, caught by
    `git diff --stat` showing far more changed lines than were edited.
30. **A backslash does not survive a bash heredoc here**, even a quoted one. A
    doubled backslash-n inside a Python string arrives as a real newline: the
    patch anchor then silently misses, or — worse — the written file has an
    unterminated string literal that only fails at import. Build literal
    backslashes with `chr(92)` and substitute a placeholder, or use the `Write`
    tool. This footgun mangled its own do-not-redo entry on the first attempt.
31. **Do not duplicate a stage's prompt or payload in the runner.** Both are now
    exposed by the production path (`BaseAgent.build_prompt`,
    `nodes.stage_payload`) and pinned by `tests/test_agent_prompt_seam.py`. A
    re-typed prompt makes A1 vs A2 a *wording* contrast as well as a content
    one, which is the confound D8 already exists to fight — and it would drift
    invisibly the next time a stage prompt changes.
32. **A replay trial's downstream is not the dump's downstream.** The dump's
    strategy and report outputs were produced from the *pre-injection* output of
    the retried stage. Leaving them in `downstream_state` (D12) invites a later
    analysis to read a stale artifact as the trial's own result. `_regenerate`
    clears every stage after the retried one.
33. **`power.py`'s sections 1–8 are indexed by `8 operators × N dumps`**, which
    is the multiplication that produced 160. Section 9 (added 2026-08-25) takes
    the defect count directly, and is the one the plan cites.
34. **`power.py` had two copies of the same bootstrap expression**, and only
    one was fixed. `cluster_bootstrap` and the section-7
    difference-in-differences each built `diff[:, idx].mean(axis=2)` inline,
    which allocates (n_sims, n_boot, n_defects) floats — 24 GB at sims=20000.
    Chunking the first left the second untouched, and the run died in section 7
    **after about forty minutes**, five sections past the part that had been
    "fixed". Both now go through `bootstrap_means()`, and
    `test_only_one_bootstrap_expression_exists_in_the_source` fails if a third
    copy appears. Lesson: when fixing a resource bug, grep for the expression
    before assuming there is one of it.
35. **Do not read Monte Carlo noise as a correction.** Mid-session this file
    claimed the morning's hand-carried power figures had "all moved". They had
    not: at `--sims 20000` both MDEs reproduce **exactly** (11.9 pp, 10.2 pp)
    and the powers land within 0.011. The apparent movement came from comparing
    two independent 2,000-simulation runs, where power carries ±0.02. Same for
    D8c: 0.12/0.19/0.32 typed against 0.109/0.177/0.300 computed. **Before
    calling a figure wrong, check whether the estimator's own error covers the
    gap** — the correction was itself the overstatement, in a file whose whole
    purpose is to stop overstatements propagating. What recomputation genuinely
    bought was reproducibility and the shared-occasion column.

**New, from the 2026-08-26 audit-instrument pass:**

36. **Render a rating item from what was RECORDED, never by re-deriving it.**
    The first `rater_sheet.py` recomputed "the first pattern with a problem" off
    the state. One banked defect spans **six** patterns — all six citing the
    same fabricated review id, which is the clearest possible signal of a
    systematic hallucination — and the rater would have been shown one of them.
    Tier-1 items now render from the recorded `facts`, Tier-2 items from the
    injection `descriptor`. Caught by self-review, not by a test; there are now
    three tests. This is trap 13 again, in a new place: **do not re-derive what
    a script already pinned.**
37. **The defect-bank audit is code, not a procedure.**
    `scripts/analysis/rater_sheet.py --build` samples and blinds; `--score`
    computes agreement, κ and a bootstrap CI. Do not hand-pick the items or
    hand-shuffle them — the sample is stratified round-robin across all six
    repair operators and seeded, and `tests/test_rater_sheet.py` fails if the
    sheet leaks tier, operator, class or defect id.
38. **κ has one honest failure mode this project will hit.** If both raters call
    everything an error, agreement is 100% and κ is **undefined**, not 1.0 —
    there is no information in a table with one occupied category. `kappa()`
    returns NaN there deliberately; do not "fix" it to 1.0. With 31 items,
    report the CI or report raw agreement and n.
39b. **The stray-citation denominator is the FLAGGED pattern, not every pattern
    the review appears in.** Summing across patterns reported "1 of 172" where
    the truth is "1 of 27"; the offending review is cited by five patterns and
    only one of them was flagged. Hit while checking the raters' own arithmetic
    — they were right and the first script was wrong. `verify_claim2.py` now
    reports per-pattern.

39c. **A blinded rating sheet must give the rater what the judgement needs.**
    Rater B's two errors (I10, I27) came from searching *the sheet* for a
    near-neighbour id, because the sheet is all they had; the real id was in the
    corpus but not in any other item. Before reusing `rater_sheet.py`, either
    include the corpus id list or pre-compute nearest-real-id distance as a
    stated fact. This is an instrument limitation, not a rater failure.

39d. **Do not read the resolved 31/31 as the blind agreement.** The blind
    figure is κ 0.870 on 29/31. The two disagreements were resolved *afterwards*
    by edit distance and by reading `_apply_o1`. Report them as separate
    numbers; collapsing them inflates the instrument's reliability.

39. **Aspect membership must be read through `inject_defects._aspects_of`.**
    Analysis results store aspects as `{"category": ..., "label": ...}` dicts,
    not strings — a local unpacking silently produced a `TypeError` here and
    would elsewhere produce a wrong answer instead.

---

---

**New, from the 2026-08-26 collection pass:**

40. **`MAX_REVIEW_SAMPLE` is not just a loader setting — it bounds the API
    schema.** `app/main.py`'s `ReportRequest.sample_size` is
    `Field(ge=1, le=MAX_REVIEWS)`, and
    `test_report_request_validates_sample_size` pins that bound. So the suite is
    green only when the test and the env agree. Collection needs a high cap, the
    test wants a fixed one — set it **inline for the run**
    (`MAX_REVIEW_SAMPLE=214 python scripts/run_study.py --phase A`) or set both
    together. `.env` now holds **500** with the test pinned to match.

41. **`MAX_REVIEW_SAMPLE=1000` raises at import.**
    `loader.MAX_REVIEW_HARD_CEILING` is **500** and `loader` validates on
    import, so an over-ceiling value does not clip — the pipeline never starts.
    500 is the highest legal value.

42. **Grow the sample with `--per-stratum`, never by hand-picking businesses.**
    `sample_businesses.py --per-stratum 7 --seed 20260803` is a **strict
    superset** of the per-stratum-5 sample — verified prefix-stable within every
    stratum, because `picked = ranked[:per_stratum]`. The existing 20 keep their
    identity, the checkpoint skips them, and exactly the 8 new ones run. Picking
    replacements by hand would break both the stratification and the resume.

43. **A 503 mid-run is not a lost dump and not a defect.** The stage records
    `status_error=True`, `defect_bank.py` excludes it as `api_error`, and any
    downstream stage that invented content to fill the gap is excluded as a
    **cascade**. Both fired on 2026-08-26 exactly as they did for Scarpetta.
    Do not hand-remove the business, and do not count its retries.

44. **The corpus-margin tripwire fired, and it is the matcher bug again.**
    Worst-case `difflib` similarity between an injected O5 corpus issue and an
    upstream candidate is now **0.444** — *above* the 0.35 trace threshold — with
    **16 pairs at or above it**. `uniform size profile absent` scores 0.444
    against `Unpleasant or undesirable atmosphere`, whose content-word overlap is
    **0.00**, and which is **D13 item I28 that both raters called an error**. The
    study is safe (`_o5_issue` stops selecting an over-threshold issue, which is
    why O5 is the lowest at 20) but the margin is gone.
    ⚠ **Do NOT edit `CORPUS_ISSUES` to fix it** — D13 rated those exact strings,
    and changing them severs the audit from the operators it audited.

45. **Do not rebuild the D13 rating sheet.** `out_study/audit/` holds a
    **31-item** sheet over the **11**-defect bank, and its sealed key matches
    that. The bank is now 13, so a rebuild produces a 33-item sheet and orphans
    the completed ratings. The audit stands as executed; **the 2 newest Tier-1
    defects are unrated**, and that is a stated scope limit, not a gap to fill.
    `tests/test_rater_sheet.py` now derives the expected size from the bank so it
    stops failing for this non-reason.

---

## 7. Environment traps (all verified this session)

- **The repo path contains `Tài liệu` in two Unicode normalisations.** Absolute
  paths typed with precomposed characters silently miss. **Use the 8.3 short
  path for Read/Write/Edit:**
  `C:\Users\hoanh\OneDrive\TAILIU~1\CSMATE~1\COS30018\Project\COS300~1.1_M\...`
  Bash with paths relative to the repo root also works.
- **Long bash heredocs fail on apostrophes.** A short one survives; a
  several-hundred-line markdown body does not (`unexpected EOF while looking for
  matching '`). Use the `Write` tool for prose, or a `python - <<'PYEOF'`
  heredoc, which is reliable.
- **The Bash working directory persists** between calls and does *not* always
  reset to the repo root — a bare `cd docs/paper` failed because the shell was
  already there. Prefer `cd "$(git rev-parse --show-toplevel)"` at the start of
  each call.
- Long runs go in the background; every runner checkpoints and resumes.
- Transient Gemini 503s are common at volume; `--sleep 5` helps.

---

## 8. Reproduce any conference number

All read-only, no API cost. ⚠ **The scripts do not share a working directory** —
verified 2026-08-24, and an earlier version of this section was wrong about it.
`tally.py`, `rep_tally.py`, `rep_verdict.py`, `audit.py` and `check_tex.py`
hard-code repo-root-relative paths (`backend/out_study/…`, `docs/paper/…`) and
**must run from the repo root**. The journal-extension scripts take
`--root`/`--dump-dir` arguments and run from `backend/`.

From the **repo root**:

```bash
backend/venv/Scripts/python.exe backend/scripts/analysis/tally.py
```

Also `rep_verdict.py` (recurrence), `audit.py` (latency, input identity,
stability), `check_tex.py` (braces, refs, citations, placeholders) — same cwd.

From **`backend/`**, for the journal extension — read-only and dataset-free:

```bash
venv/Scripts/python.exe scripts/analysis/defect_bank.py --out out_study/defect_bank.json
```

```bash
venv/Scripts/python.exe scripts/replay_stage.py --verify out_study
```

```bash
venv/Scripts/python.exe scripts/analysis/power.py
```

```bash
venv/Scripts/python.exe scripts/analysis/churn.py
```

`power.py` answers D4d (simulation-based; closed-form McNemar does not apply).
`churn.py` answers D3c by measuring the unperturbed pipeline's own churn from
the repetition sub-study — the floor a collateral threshold has to clear.

Inspect one banked defect with
`scripts/replay_stage.py --dump-dir <dump> --stage <stage>`.

Re-running an *experiment* needs `MAX_REVIEW_SAMPLE` to cover the largest
business in the sample (**214** for the current one) — `loader.MAX_REVIEWS` is
read at import, so `--sample-size` alone cannot lift the cap and the runner
refuses to start without it. That guard is deliberate, and it fired correctly on
2026-08-26.

⚠ **Two traps around that variable, both hit on 2026-08-26** — see §6 items 40
and 41. `.env` now holds **500** (`loader.MAX_REVIEW_HARD_CEILING`, the highest
legal value, so it covers any future sample and cannot drift up), and
`tests/test_data_pipeline.py::test_report_request_validates_sample_size` is
pinned to match. **1000 raises at import.**

---

### Journal build items B4–B8 (2026-08-25) — all from `backend/`, all dataset-free

```bash
venv/Scripts/python.exe scripts/inject_defects.py --root out_study --matrix
```

Also: `scripts/analysis/prompt_audit.py` (the B8 gap + drift check),
`scripts/analysis/score_repair.py --selftest` (the §13.5 case),
`scripts/arms.py` (the arm × placement grid), and
`scripts/run_injection_study.py --plan-only` (822 trials today, ≈1,180 once
D11b's dumps land; order invariant). `--dry-run` executes the whole runner
without an API key.

### Added 2026-08-26 — also from `backend/`, also dataset-free

```bash
venv/Scripts/python.exe scripts/analysis/rater_sheet.py --build --out out_study/audit
```

The D13 audit instrument: 31 blinded items (11 Tier-1 + 20 Tier-2, round-robin
over all six repair operators), a blank CSV per rater, and a **sealed**
`key.json`. Score two filled sheets with
`--score out_study/audit --a A.csv --b B.csv`.

```bash
venv/Scripts/python.exe scripts/analysis/power.py --sims 20000
```

Section 9 is the one the plan and the memo cite. ⚠ It is slow at 20,000
simulations (tens of minutes); the default 2,000 is fine for a sanity check but
carries ±0.02 on power and ±0.4 pp on an MDE — do not quote a third decimal
from it.

⚠ **The live regeneration seam is wired but has never made a call.** Before
committing to the core, run the integration-marked smoke test — 7 cells, one per
defined (arm, placement) shape, 7–21 calls:

```bash
venv/Scripts/python.exe -m pytest tests/test_injection_seam_live.py -v -m integration
```

---

## 9. Verification state at this handoff

- Tier A: 5/5 read · Tier B: 9/9 read · **Tier C: 0/11, still outstanding**
- ✅ **D11b COLLECTION DONE 2026-08-26** — 8/8 dumps in observe mode, ~49 min,
  `status=complete`, no skipped agents, **`loaded == expected` on all 8** (no
  truncation). **28 dumps.** Delivered **N=142** (predicted ≈143), **1,167**
  trials, yield **5.07**/dump. Full record: `JOURNAL_PLAN.md` §16.
  - The two transient 503s self-recovered. Honey Baked Ham Company's
    `reasoning_agent` logged `status_error=True` (excluded `api_error`) and its
    `report_agent` entry is the downstream **cascade** (excluded) — that business
    contributes **zero** defects, same shape as Scarpetta. Handled with no
    intervention; 19 − 4 − 2 = 13.
  - ⚠ **Second serving epoch** — the original 20 ran 2026-08-03, these
    2026-08-26, and the checkpoint records no model. §14.1 covers it; it belongs
    in the methods section.
- ✅ **POWER GATE PASS** — N=142, r=3: **MDE 10.8–10.9 pp w/ occasion** against
  X = **12 pp**. At N=102 it was 12.6 pp, i.e. *above* the threshold, which is
  what made the pre-registration incoherent. **And it survives the matcher fix**:
  swept 120–150 defects, the MDE stays under 12 pp even below the worst case of
  losing O5 entirely (§16.6). Contingency if N drops under ~130 is **r=4**.
- Defect bank: **re-verified and encoded in code** — **13 usable, 2 cascades,
  4 API errors, from 19 retry observations** (`scripts/analysis/defect_bank.py`),
  over **7 cells / 6 businesses**. ⚠ Both new defects are
  `untraceable_recommendation`, taking that class to **8 of 13** — the class §15.4
  showed the matcher gets wrong.
- Replay fidelity gate: **PASS** — **159** recorded facts reproduced exactly,
  0 mismatches, 53 analysis-stage observations skipped as unverifiable
- Test suite: **266 pass**, 13 integration deselected (257 before D18 on
  2026-09-02; 195 earlier on 2026-08-25 and 134 on 2026-08-24). The 62 new tests cover the prompt/execute
  seam, the stage-payload extraction, the wired regeneration path, the
  resume-on-failure fix, `power.py` (which had none at all) and the D13 audit
  instrument; 7 of the 13 deselected are the live smoke test, one per defined
  arm x placement cell
- Defect bank **cross-validates exactly against the pre-existing `tally.py`** on
  Phase A (0 unresolvable evidence IDs, 1 misaligned aspect, 3 untraceable
  recommendations) — two independently written implementations, same answer.
  `tally.py` had already excluded `status_error`, so the repository's own
  analysis code encoded the 503 exclusion all along; only the plan's prose was
  wrong. **Cross-validate against existing scripts before building a new one.**
- Power analysis (D4d) and collateral calibration (D3c) are **computed and
  committed** — `scripts/analysis/power.py`, `scripts/analysis/churn.py`. Both
  read-only, both dataset-free.
- `total_tokens` is null in all 45 runs, but **B1 was never a real gap** —
  `BaseAgent.total_tokens_used` and `eval/harness.py` already did this;
  `run_study.py` simply hard-coded `total_tokens=None`. Now fixed, so any token
  figure must come from a **fresh** run — the 45 on disk cannot be back-filled.
- Conference paper #1: **submitted, under review.** `main.tex` verified
  structurally sound
  (`check_tex.py`: braces balanced, 0 placeholders, 0 dangling refs, 0 missing
  citations). It was recovered from the NFC shadow directory on 2026-08-24 and
  is now tracked. `check_tex.py` itself had a false-positive brace bug — fixed.
- **B4–B8 built and gated 2026-08-25.** The injector cross-checks against
  `supervision.measure` on every base; the scorer discriminates the §13.5
  replacement-value case; the runner's order invariant and zero-call `--dry-run`
  are pinned. 61 new tests.
- **Two independent programs still agree**: the injector declares a check class,
  the supervisor reports what fired, and they match on all 137 applicable
  injections — the same cross-validation discipline that vindicated the defect
  bank against `tally.py`.
- **Seam wired and gated 2026-08-25.** `--dry-run` still makes zero calls over
  the full plan; `--plan-only` still reports 822 trials with the order invariant
  intact; the production `run()` of all three agents is pinned to be exactly
  `build_prompt` + `_with_feedback` + `run_messages`. The one thing no offline
  test can show — that the assembled arm is accepted by the provider and returns
  schema-valid output — is `tests/test_injection_seam_live.py`, deliberately
  integration-marked and **not yet run**.
- **`PHASE0_MEMO.md` written, and ✅ approved 2026-08-26** on D11b, D8b and D8d,
  plus the four §7 positions. **Nothing has been spent on any of it**: no dump
  collected, no trial run.
- **D13 instrument built and gated 2026-08-26** — `scripts/analysis/rater_sheet.py`,
  19 tests. Builds a 31-item blinded sheet from the *recorded facts* and the
  *injection descriptors*, never by re-deriving; `--score` returns agreement,
  kappa with a bootstrap CI, and every disagreement with its notes.
- **D13 EXECUTED 2026-08-26** — two human raters, blinded, 31 items.
  κ **0.870** CI [0.674, 1.000], raw **29/31**, **0 `U`**. Unblinded:
  **Tier 1 0/11 called an error, Tier 2 16/20.** Both disagreements (I10, I27,
  both O1) resolved mechanically in rater A's favour by edit distance and by
  `_apply_o1`, giving 31/31 resolved. The raters' reasoning was then verified
  against the corpus: edit distance is **bimodal, 1–2 for corruption vs 20 for
  fabrication, nothing between**; real `misaligned_aspect` is ~3% of citations
  against O3's 100%; and the `untraceable_recommendation` lexical bands for real
  (0.23–0.35) and injected (0.21–0.28) defects **overlap completely** while
  content-word overlap separates them perfectly (0.08–0.44 vs 0.00). Full
  results and consequences: `JOURNAL_PLAN.md` §15. Artifacts:
  `out_study/audit/` (sheets, sealed key, `claim_check.txt`, `claim_check.json`).
- ⛔ **A supervisor bug is now measured, not suspected.**
  `supervision._measure_strategy` matches with `difflib.SequenceMatcher` — a
  character-level ratio — so it cannot see paraphrase. It accounts for **6 of
  the 11** Tier-1 defects, and 9 of the 11 are false positives overall. This is
  a finding about the paper's own subject and it touches paper #1, under review.
- **Two things still outstanding**, both listed in §4: **D5b** (local model) and
  **§7 item 3** (the warm-resample subset, marked REQUIRED by D2 and not built —
  it needs a *choice*, which a ratification does not make). D13 needs a
  **person**, not a decision.
- *(Superseded — see §0.)* **Still not verified:** no trial has run, no memo is written, and
  `run_injection_study._regenerate` is deliberately unwired (§4 item 2). The
  eight extra Phase-A dumps (§4 item 1) have not been collected.

## 10. Known documentation drift (pre-existing, unfixed)

`README.md` §6/§9 still describe the *old* failure-only orchestrator
("retry, skip, or halt decisions after stage failure") and list Tier 1 as not
enforced at runtime. The hub supervisor superseded that. The code and
`docs/FINDINGS_2026-07-16.md` F7 are correct; the README is stale. Not fixed
here because it is outside the journal work — but do not trust README §6/§9.

✅ **`HANDOFF.md` — three false statements, FIXED 2026-09-02.** It claimed
(§1.3) that `docs/paper/` is gitignored and never pushed — verified false with
`git check-ignore`; the directory is tracked and only build artefacts are
ignored. It also carried a superseded Unicode-path workaround (§1.1) and
repeated the "token accounting does not exist" claim `JOURNAL_PLAN.md` B1
disproved (§10). All three are now corrected in place and the file carries a
HISTORICAL banner. The §1.3 error was the dangerous one: a session acting on it
would have left the paid-for study dumps uncommitted.

## 11. Uncommitted work (2026-08-25, 2026-08-26 and 2026-09-02)

⛔ **Nothing from any of the three days is committed. This is now the single
largest risk in the project** — it includes **8 Phase-A dumps that cost real API
budget and exist in exactly one place**, plus a completed human audit that cannot
be re-run (the raters are no longer blind). **Committing is the first thing a new
session should do, before anything else.**

⚠ **One staging artefact to resolve first.**
`docs/paper/Evaluation_as_Supervision.drawio` shows as a *staged deletion plus an
untracked file of the same name*. It is a **false alarm** — verified
byte-identical to HEAD modulo CRLF. Unstage it, do not re-create it:

```bash
git reset docs/paper/Evaluation_as_Supervision.drawio
```

**New on 2026-09-02 (the supervisor methodology review — D18-D21):**

| Path | What |
|---|---|
| `docs/paper/PREREGISTRATION.md` | ⚠ **NEW, and the point of the day.** DRAFT, not frozen; **four blocking items in its §11**, two of which are supervisor decisions. **It must be committed before the first trial or it is not a pre-registration.** |
| `docs/paper/JOURNAL_PLAN.md` | **new §3.7 (D18-D21)**, plus consistency edits to D3b, B6, §6.2, §8, §11 and §14.3 |
| `backend/scripts/analysis/score_repair.py` | D18: 4-class outcome, identity-based deletion, injected item excluded from churn, empty-pre churn fix |
| `backend/tests/test_score_repair.py` | 9 new tests (15 -> 24); suite 257 -> **266** |
| `docs/paper/NEXT_SESSION.md` | this file - status, gates, taxonomy, counts |
| `docs/paper/PHASE0_MEMO.md` | test-count refresh + the two new supervisor decisions in its open list |

⚠ **D19-D21 are NOT built.** The `verify_injection` gate is still not called from
`run_injection_study.run()`, and O4 has no repair path. Nothing was run.

**New on 2026-08-26, second pass (the collection):**

| Path | What |
|---|---|
| `backend/out_study/A/<8 new business ids>/` | ⚠ **The 8 Phase-A dumps. Real API spend, one disk, irreplaceable without paying again.** |
| `backend/out_study/A/checkpoint.jsonl` | 20 → **28** rows |
| `backend/out_study/sample.json` | regenerated at **`--per-stratum 7`** (28 businesses, strict superset — see trap 42) |
| `backend/out_study/defect_bank.json` | regenerated: **13 usable**, 7 cells, 6 businesses |
| `backend/out_study/injection_matrix.json` | regenerated: **142** repair-endpoint defects |
| `backend/.env` | `MAX_REVIEW_SAMPLE` → **500** (traps 40/41) — ⚠ **gitignored, never commit** |
| `backend/tests/test_replay.py` | defect-bank pins re-pinned to 19/4/2/13/7/6 |
| `backend/tests/test_inject.py` | ceiling pins re-pinned to 28 dumps / 191 / **142**; corpus-margin tripwire bound + finding recorded |
| `backend/tests/test_rater_sheet.py` | sheet size now **derived from the bank**, not hard-coded 31 |
| `backend/tests/test_data_pipeline.py` | `sample_size` bound 100 → **500**, matching `.env` |
| `docs/paper/JOURNAL_PLAN.md` | **§16 + §16.6** — delivered numbers, the matcher finding, the power gate and its sensitivity bound |

**New on 2026-08-26, first pass (the wiring, audit and decision pass):**

**New on 2026-08-26** (the wiring, audit and decision pass):

| File | What |
|---|---|
| `backend/tests/test_agent_prompt_seam.py` | 18 tests — production `run()` is exactly `build_prompt` + `_with_feedback` + `run_messages`, per agent, plus the `nodes.stage_payload` anti-drift guards |
| `backend/tests/test_power.py` | 19 tests — `power.py` had none; includes the chunked-vs-unchunked bootstrap equality and the guard against a second copy of that expression |
| `backend/tests/test_injection_seam_live.py` | integration-marked live smoke test, 7 cells (one per defined arm x placement) |
| `backend/tests/test_rater_sheet.py` | 19 tests — blinding guards and item fidelity |
| `backend/scripts/analysis/rater_sheet.py` | D13 audit instrument (`--build` / `--score`) |
| `docs/paper/PHASE0_MEMO.md` | the supervisor memo, now answered |
| `backend/out_study/audit/` | **D13 executed** — `rating_sheet.md`, both filled rater CSVs, sealed `key.json`, `README.md`, `BRIEFING.md`, `claim_check.txt`, `claim_check.json` |
| `backend/scripts/analysis/verify_claims.py` | corruption-vs-fabrication check (edit distance to the real corpus) |
| `backend/scripts/analysis/verify_claim2.py` | stray-citation ratios, per flagged pattern |
| `backend/scripts/analysis/verify_claim3.py` | the matcher false-negative check (lexical vs content-word overlap) |

Modified on 2026-08-26: `backend/app/agents/base_agent.py` (the prompt/execute
seam), `reasoning_agent.py`, `strategy_agent.py`, `report_agent.py` (composed
onto it), `backend/app/core/nodes.py` (stage payloads extracted),
`backend/scripts/run_injection_study.py` (live seam wired, resume-on-failure
fixed, failover guard), `backend/scripts/analysis/power.py` (section 9, chunked
bootstrap, `--defects`), plus `JOURNAL_PLAN.md` and this file.

**New on 2026-08-25** (the B4–B8 build):

| File | Item |
|---|---|
| `backend/scripts/inject_defects.py` | B4 operators + applicability matrix |
| `backend/scripts/arms.py` | B5 arms × placement, frozen wording |
| `backend/scripts/analysis/score_repair.py` | B6 outcome scorer |
| `backend/scripts/analysis/prompt_audit.py` | B8 A1-vs-prompt audit |
| `backend/scripts/run_injection_study.py` | B7 batch runner |
| `backend/tests/test_inject.py` | 12 tests, incl. the cross-check gate |
| `backend/tests/test_score_repair.py` | 15 tests, incl. §13.5 |
| `backend/tests/test_arms_and_audit.py` | 21 tests |
| `backend/tests/test_run_injection_study.py` | 13 tests |
| `backend/out_study/injection_matrix.json` | generated ceiling |
| `backend/out_study/prompt_audit.json` | generated B8 gap |

Modified: `backend/scripts/analysis/defect_bank.py` — `fired_classes()` and
`frequency_divergent()` extracted so the injector and the bank share one check
taxonomy. Pinned numbers unchanged (11 usable defects, 5 cells, 4 businesses).

⚠ Also pending: `docs/paper/Evaluation_as_Supervision.drawio` shows as a staged
deletion plus an untracked file of the same name — an editor rewrite, not an
intentional delete. Resolve before committing.
