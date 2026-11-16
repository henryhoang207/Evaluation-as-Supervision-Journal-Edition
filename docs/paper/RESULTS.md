# Results — injected-defect repair study

**Written 2026-10-08; C7 added 2026-10-12; A12 added 2026-11-02; A13–A14 added 2026-11-15; A15 added 2026-11-17.** The record of what the journal-extension experiments
found, for writing the paper from. Every number here is printed by a committed
script from committed data; the source is named beside each block. Design and
every deviation from it: `PREREGISTRATION.md` (core frozen 2026-09-14 at tag
`prereg-freeze`; amendments §0.1 A1–A15; Flash-Lite replication frozen
2026-11-16 at `edfb406` / tag `prereg-fl-freeze`). Operational history: `RUN_QUEUE.md`.

All hosted `gemini-2.5-flash` cells (`T2`, `T2D19`, `T2C1`, `T2P`, `T2S`, `T2W`,
`T1`, `T2D`, `T2T`, `T2A0`, `T2TA0`, `H/A`, `T1H`) ran through Google's
OpenAI-compatible endpoint with fallback disabled (`LLM_DISABLE_FALLBACK=1`),
at temperature 0 unless stated (`74,534,450` recorded tokens across those
checkpoints, noting the earliest `A`/`B`/`R` rows predate token accounting).
**C7 (`T2L`)** ran Qwen2.5-7B-Instruct Q4_K_M locally via Ollama on an RTX 5060 Ti
16 GB (`930` local trials, `929` usable, `7,361,433` unbilled local tokens).
**S5 (`FL/A`, `FL/determinism`, `T2FL`)** ran `gemini-3.5-flash-lite` through
Google's OpenAI-compatible endpoint with fallback disabled, temperature 0, and
`reasoning_effort=None` omitted (`14,684,261` recorded tokens). Total recorded
tokens across all checkpoints: **`96,580,144`** (`89,218,711` hosted API tokens +
`7,361,433` unbilled local tokens). All planned and supervisor-requested
experiments are complete and verified.

---

## 1. What ran

| Cell | Amendment | Data | Defects | Trials | Usable | Commit |
|---|---|---|---|---|---|---|
| Core (confirmatory) | frozen | `out_study/T2` | 142 | 1,167 | 1,149 | `2515fcf` |
| D19 overwrite counterfactual | A2 | `T2D19` | 23 | 138 | 138 | `212d02f` |
| C1 constraint completeness | A1, A3 | `T2C1` | 37 | 444 | 444 | `66c0e07` |
| Placement P0–P3 | A5 | `T2P` | 45 | 540 | 539 | `c13f5af` |
| O1 severity | A6 | `T2S` | 24 | 144 | 144 | `e657b65` |
| Warm resampling (T = 1.0) | A7 | `T2W` | 45 | 675 | 675 | `0f20f66` |
| Tier-1 replay (real defects) | A8 | `T1` | 13 | 117 | 117 | `657bd00` |
| Downstream propagation | A9 | `T2D` | 90 | 447 conditions | 447 | `0428190` |
| C7 second model (exploratory) | A10, A11 | `T2L` | 138 | 930 | 929 | `7188bb9` |
| Thinking-budget sweep (`none`/`low`/`medium`/`high`) | A12 | `T2T` | 45 | 1,224 | 1,224 | `8ff3b4d` |
| S2a `A0` fill + `A1` anchor (`a0fill`) | A13 | `T2A0` | 71 | 284 | 284 | `aed6944` |
| S2b `A0` at `none`/`high` + `A1` anchor (`thinking_a0`) | A13 | `T2TA0` | 45 | 360 | 360 | `43d4d86` |
| S3 Option H Phase-A harvest | A14 | `H/A` | 56 businesses | 56 runs (860 calls) | 56 | `0b6059b` |
| S3 Option H Tier-1 replay (`T1 + T1H` pooled = 21 defects / 15 cells) | A14 | `T1H` | 8 (8 cells) | 72 | 72 | `e3720a1` |
| S5 Flash-Lite own bases (`flashlite_bases`) | A15 | `FL/A` | 28 businesses | 28 runs (503 calls) | 28 | `5f12198` |
| S5 Flash-Lite determinism (`flashlite_determinism`) | A15 | `FL/determinism` | 10 prompt pairs | 20 requests | 20 | `edfb406` |
| S5 Flash-Lite repair replication (`flashlite`, confirmatory) | A15 (`prereg-fl-freeze`) | `T2FL` | 157 (`Q_FL = 36` on `A3`) | 1,521 | 1,520 | staged |

Every pass: one session per defect (all checked), offline re-score of every
trial in full agreement with the live score, `status_error` excluded and
counted. The core's 18 exclusions are network drops and one overnight laptop
sleep; they cost 3 defects their A1/A2 pair.
C7's single exclusion is a capped response followed by a blocked oversized
schema correction; it is counted as unrepaired in the pre-specified sensitivity.
`T2FL`'s single exclusion is `PbqJmjSijS7aXr0qkjbuxA:O1` (`A1` rep 2, P1/C0), a
provider `Connection error.` (`status_error`, `attempts_made=0`, no served model,
0 recorded tokens); the defect retains 2 usable `A1` repetitions, so 0 defects
are dropped (`N = 157`).

---

## 2. The confirmatory test (§2.1) — null, at ceiling

*Source: `repair_analysis.py --cell core` → `out_study/T2/analysis.json`.*

- N = 139 defects (3 lost their pair), r = 3 completed in every cell.
- **A1 94.7 %, A2 94.0 %; A1 − A2 = +0.7 pp, 95 % CI [−2.9, +4.3]**; exact
  McNemar on the majority dichotomy, discordant 6 vs 4, **p = 0.754**.
- Unchanged without `attempts_made > 1` trials: +1.0 pp [−2.2, +4.1], p = 0.727.
- Unchanged under every O5 trace criterion §2.3 names — content-word Jaccard ≥
  0.10 (primary), ≥ 0.05, containment > 0, and the production difflib matcher:
  +0.72 pp [−2.9, +4.3] each (`T2/o5_sensitivity.json`; recomputing the primary
  reproduces all 157 stored O5 outcomes).
- **Split rule (§6): not met.** The repair study does not branch into its own
  paper.

The interval excludes effects larger than ≈ 4 pp in either direction: on this
model and these defects, the *content* of the supervisor's feedback does not
change whether the retried stage is repaired. This sides with SC-Bench
(contentless rejection ≈ measured feedback) against Olausson (feedback content
binds).

---

## 3. §5 directional predictions against results

| Quantity | Recorded before results | Result | Holds? |
|---|---|---|---|
| A0 ceiling | high | **100 %** (core 71-defect stride, 209/209 trials); **98.8 % [97.2, 100.0]** pooled over 142 defects (`T2A0`, `A1/A0 = 0.959 [0.928, 0.988]` over 141 defects) | ✅ |
| A1 | ≈ 45 % | **94.7 %** | ❌ ceiling |
| A2 | ≈ 33 % | **94.0 %** | ❌ ceiling |
| A3 | not a floor; ≈ 100 % on O6/O7, ≈ 53 % pooled | O6/O7 **100 %**; pooled **92.2 %** (A2 vs A3 on 34 defects: 96.1 % vs 92.2 %) | ✅ not a floor; ❌ the 53 % |
| Class ordering | referential (O1/O2) > structural (O3, O6–O8) > semantic (O5) | **structural 98.6 % > semantic 93.0 % > referential 89.6 %** (O1 84.7 %, O2 94.4 %) | ❌ reversed |
| Placement | P1 ≫ P3 ≈ P2; P0 apart | P1 97.8 %, P2 97.8 %, P3 97.0 %; P0 94.1 % | ½ — P3 ≈ P2 holds, P1 ≫ does not |
| C1 interaction | undetectable | gap difference **0.0 pp [−6.3, +6.3]** | ✅ |

*Sources: `T2/analysis.json`, `secondary_extra.json` (class ordering, A3 pooled
by trial), `T2P/analysis.json`, `T2C1/analysis.json`.*

---

## 4. Why everything sits at the ceiling

- **68 % of A1, 53 % of A2 and 45 % of A3 retries reproduce the clean
  pre-injection output byte for byte** (core; 288/421, 223/417, 46/102; A0
  149/209). "Byte for byte" means identical as canonical JSON (sorted keys).
  Since 2026-10-20 `repair_analysis.py --cell core` prints these figures and the
  distinct-output shares below, and writes them to the `exploratory` block of
  `T2/analysis.json`.
- **At P1 this is copy-and-correct of the artifact the model is shown, not
  re-derivation.** At temperature 1.0 byte-identity at P1 does not move (A1
  69.6 % → 68.9 %, A2 48.9 % → 48.9 %), while A3's fresh draws at P0 fall from
  45 % to **0 %** (warm cell). Repair stays at ceiling at temperature 1.0
  (A1 99.3 %, A2 97.0 %), so the null is **not** a temperature-0 artefact.
- **Change, then resolution** (§3 item 6): every retry in the core changes the
  injected output (100 %, all arms), and ≈ 94 % of those changes repair it
  (A1 94.8 %, A2 94.0 %, A3 92.2 %, A0 100 %).
- Repetitions are near-identical: **73 % of A1 cells** (defect × arm) produce
  one distinct output across their three repetitions and 27 % two (A2 60 % /
  40 %, plus one cell of 139 with three; A0 77 % / 23 %; cells with all three
  repetitions only). r = 3 carries little more than r = 1 — the occasion
  term of `power.py` was the right one to plan with. A3 at P0 is the exception:
  94 % of its cells give two distinct outputs.

The injected defects are easy for this model to undo once it can see them. The
experiment therefore measures feedback content on defects the model fixes
regardless, which is why the contrast is null rather than a test of a hard
repair.

---

## 5. Exploratory cells

**D19 — what the overwrite bought** (`T2D19/analysis.json`). Retry with the
measured frequency (A1) repaired **69/69 trials, 23/23 defects** (exact 95 % CI
over defects [85.2 %, 100 %]), collateral 0 %; A3 regeneration 97.1 %,
collateral 30 %. Overwrite is exact at 0 calls; retry costs 1 call and ≈ 22k
tokens. **§7's pre-fixed reading: the overwrite is a cost optimisation, not a
correctness decision**; §4.5's principle rests on the zero-call argument.

**C1 — stating the constraints at retry time** (`T2C1/analysis.json`). Gap
under C0 −1.8 pp [−6.3, +1.8], under C1 −1.8 pp [−6.3, +1.8], difference
0.0 pp. Retry-time disclosure changed nothing measurable. Serving drift, C0
re-run vs core: 96 % same outcome class, 83 % byte-identical.

**Placement** (`T2P/analysis.json`). A1: P0 94.1 %, P1 97.8 %, P2 97.8 %, P3
97.0 %; P1 − P2 0.0 pp [−4.4, +4.4], P1 − P0 +3.7 pp [−1.5, +9.6]. At P0 (the
production placement) **every report-stage defect needed a schema-correction
second call**; without those trials P0 is 90.8 % on 29 defects. Collateral at
P0 38 % vs 1 % at P1.

**O1 severity** (`T2S/analysis.json`). Level 1 (one id corrupted) 86.1 %,
level 2 (every evidence id of the pattern corrupted) 88.9 %; difference
−2.8 pp [−11.1, +5.6]. Breaking all of a pattern's support did not lower
repair.

**Warm resampling** (`T2W/analysis.json`). See §4. Equal budget: A1's single
retry repairs 97.0 % at ≈ 9.7k tokens; A3's best-of-k at temperature 1.0 is
82.2 % / 88.9 % / 93.3 % for k = 1/2/3 at ≈ 13.6k tokens per draw (≈ 41k for
k = 3). A1 − A2 gap at T = 0 −3.0 pp, at T = 1 +2.2 pp, difference +5.2 pp
[+0.7, +11.1] — a handful of defects, one of many exploratory intervals.
**Neither of A7's pre-fixed readings applies** (identity did not fall; repair
did not fall).

**Tier-1 replay — the production retry on real, production-caught defects**
(`T1/analysis.json`, `T1H/analysis.json`; A8 and A14). Original `T1` replayed
13 defects (7 business × stage cells; 117 trials) harvested from `out_study/A`
and `out_study/R`. Under Option H (A14), 56 fresh businesses (`out_study/H/A`,
`7.73 M` harvest tokens, 860 calls) yielded 8 runnable defects across 8 disjoint
business-ID × stage cells (`T1H`, `72` trials, `1.01 M` tokens), bringing the
pooled bank to **21 defects in 15 cells** (meeting A14's `≥ 15`-cell test gate).
Single-pass sensitivity `A + H` (excluding `out_study/R`) covers 14 defects in
14 cells. Acceptance after the retry at `P0` (`A1` / `A2` / `A3`, with
cell-cluster 95% CIs):
- **`T1` (13 defects, 7 cells; descriptive):** `28.2 % [15.1, 46.2]` / `76.9 % [55.6, 89.7]` / `25.6 % [12.8, 41.7]`; `A2 − A1 = +48.7 pp [+22.2, +66.7]`; `A1 − A3 = +2.6 pp [−12.1, +15.2]`. On the trace class (8 of 13) the content-word check accepts `A1` `87.5 %`, `A2` `100 %`, `A3` `79.2 %`; `A3` returns the original defective output `48.7 %` of the time while `A1`/`A2` never do.
- **`T1H` (8 defects, 8 cells; descriptive):** `70.8 % [45.8, 91.7]` / `50.0 % [20.8, 79.2]` / `37.5 % [12.5, 62.5]`; `A2 − A1 = −20.8 pp [−54.2, +12.5]`; `A1 − A3 = +33.3 pp [+16.7, +50.0]`. The `T1` `A2 > A1` gap did not reproduce in the fresh harvest (its sign reversed).
- **`Pooled` (`T1 + T1H`, 21 defects, 15 cells):** `44.4 % [30.0, 64.7]` / `66.7 % [45.8, 82.1]` / `30.2 % [18.7, 45.1]`; `A2 − A1 = +22.2 pp [−10.4, +44.9]`; `A1 − A3 = +14.3 pp [+2.9, +28.9]`. Clean-check pass (`post_verdict == proceed`): `36.5 % / 58.7 % / 30.2 %`; target resolved: `50.8 % / 66.7 % / 34.9 %`. **A14 formal test (15 cells ≥ 15):** two-sided cell-cluster bootstrap on pooled `A2 − A1` acceptance **does not reject (`p = 0.1656`)**.
- **`A + H` single-pass sensitivity (14 defects, 14 cells):** `52.4 % [31.0, 73.8]` / `57.1 % [35.7, 78.6]` / `35.7 % [19.0, 54.8]`; `A2 − A1 = +4.8 pp [−26.2, +33.3]`; `A1 − A3 = +16.7 pp [−2.4, +33.3]`; clean-check pass `45.2 % / 57.1 % / 35.7 %`.

**Defect origin** (§3 item 5; `secondary_extra.json`, `T1H/analysis.json`). On
the one shared footing — supervisor acceptance of the retried output at `P0` —
`A1` is accepted for **`98.5 %` of injected defects**, compared with `28.2 %` in
the original `T1` bank, `44.4 %` in the pooled 21-defect bank, and `52.4 %` in
single-pass `A + H` (`A3`: `98.0 %` vs `25.6 %` in `T1` / `30.2 %` pooled). The
D13 audit already found 0 of 11 real defects to be errors to a human: most are
checker false positives the retry cannot "fix", because the checker keeps
misreading the regenerated output.

**Downstream propagation** (`T2D/analysis.json`). From clean, unrepaired and
repaired stage outputs, the later stages re-run once each:

| | clean | clean rerun | unrepaired | A1 | A2 |
|---|---|---|---|---|---|
| E1 every downstream stage accepted | 84.4 % | — | 80.0 % | 88.8 % | 88.6 % |
| E3 final-report claims diverging from clean | — | 2.6 % | **10.8 %** | 6.7 % | 7.4 % |
| E2 planted O5 issue in the final report | 0 % | — | **70 %** | 0 % | 0 % |

- **Reading 1 holds — silent propagation**: unrepaired runs are accepted about
  as often as clean ones (−4.4 pp [−14.4, +6.7]) while their reports diverge
  +8.2 pp beyond noise [+5.6, +11.0].
- **Reading 2 holds partly**: repair removes the planted issue entirely and
  cuts divergence by 4.2 pp [−7.5, −1.0], but stays +4.1 pp above noise
  [+1.4, +6.8] — regeneration churn.
- **The report check rewards propagation**: of 20 unrepaired O5 runs, the 14
  that carried the planted issue into the report were all accepted and the 6
  whose report dropped it were all rejected (`report_containment`). The check
  measures fidelity to upstream, not correctness.
- Defect-level and pipeline-level outcomes are loosely coupled (MAST App. J):
  all 8 A1 runs whose defect was not repaired passed every downstream check;
  10 of 81 repaired runs did not.
- A1 = A2 at pipeline level too (E1 0.0 pp, E3 −0.6 pp).

**C7 — local second-model replication** (`T2L/analysis.json`, A10/A11;
full gates, exclusions and secondaries in [`C7_STATUS.md`](C7_STATUS.md)).
138 paired defects, three repetitions per arm (one A2 cell has two usable
draws): **A1 72.9%, A2 66.2%; A1 − A2 = +6.8 pp [+0.5, +13.3]**.
Both rates are below 90%: **the Gemini ceiling does not replicate on this
model/runtime**. The bootstrap interval suggests a feedback advantage, but
the majority McNemar test is borderline (**p = 0.0525**, 16 vs 6 discordant)
and rep 0 alone is **+5.8 pp [−0.7, +12.4]** on 137 pairs. Exploratory evidence,
not a new confirmatory claim.

- O1: A1 39.4%, A2 47.0%, gap −7.6 pp [−25.8, +10.6]. Severe operators:
  A1 79.3%, A2 69.8%, gap **+9.5 pp [+3.2, +16.4]**, p = 0.0127.
- Reasoning repair: A1 58.6%, A2 42.9%; strategy 75.0% vs 80.0%; report
  90.4% for both. A3 regeneration repairs **38.2%** on 34 defects (0% reasoning,
  20% strategy, 100% report). All 36 A3 report trials need a second schema
  call; without multi-attempt trials A3 is 4.5% on the remaining 22 defects.
- The sole final failure hit the 4096 output cap, then the 32k context guard
  refused correction. Counting it as unrepaired leaves the primary unchanged;
  its other two draws were already unrepaired. No valid A1/A2 trial uses
  schema correction. Nothing was resampled.
- Canonical JSON identity to the clean **Gemini** output: A1 42.0%, A2 39.5%,
  A3 0%. Collateral: 10.5%, 15.2%, 100.0% of measurable trials respectively.
- Original G2 **failed** (8/10 byte-identical pairs). A11 filed before final
  trials uses r=3, preserving that failure. Final three-draw raw stability:
  A1 131/138 identical sequences (94.9%), A2 116/137 (84.7%); outcome stability
  136/138 and 134/137. Contiguous repetitions are not independent draws.
- Paired with Gemini on the same eligible defects: local − Gemini A1
  **−24.1 pp [−32.4, −16.1]**, A2 **−29.4 pp [−37.5, −21.5]**, A3
  **−53.9 pp [−69.6, −38.2]**. Model family, size, quantisation and runtime
  are bundled, and clean Gemini bases are held fixed: this is not a pure
  model causal comparison or a complete Qwen pipeline evaluation.
- 930/930 trials, 168/168 rows (26 inapplicable, four context-excluded);
  929/929 offline scores and post-facts agree, 966 raw calls checked, one
  session per defect, runtime/source unchanged, no detected prompt truncation.

**Thinking-budget sweep (`T2T/analysis.json`, A12).** 45 placement-stride
defects (`12` on `A3`), 4 `reasoning_effort` levels (`none`, `low`, `medium`,
`high`), `1,224/1,224` usable trials, `11,161,973` tokens.
- Binary repair stays at ceiling across every budget (`A1`: `100.0 %` `none`,
  `99.3 %` `low`, `94.8 %` `medium`, `97.8 %` `high`; `A2`: `100.0 %`, `98.5 %`,
  `94.8 %`, `100.0 %`; within-effort `A1 − A2` is `0.0 pp`, `+0.7 pp`, `0.0 pp`,
  `−2.2 pp`). Within-weights `A3` regeneration rises from `75.0 % [50.0, 100.0]`
  at `high` to `91.7 % [75.0, 100.0]` at `none` (`+16.7 pp`).
- Unconditional canonical-JSON exact restoration (`A1 − A2`) widens as thinking
  traces are removed: `+10.4 pp [−3.0, +23.0]` at `high` (`60.7 %` vs `50.4 %`,
  exact McNemar `p = 0.302`, 10 vs 5), `+8.9 pp [−2.2, +20.0]` at `medium`
  (`60.0 %` vs `51.1 %`, `p = 0.754`, 6 vs 4), `+23.7 pp [+11.9, +36.3]` at
  `low` (`59.3 %` vs `35.6 %`, `p = 0.0074`, 13 vs 2), and **`+23.7 pp [+12.6,
  +36.3]` at `none` (`80.7 %` vs `57.0 %`, exact McNemar `p = 0.00098`, 11 vs 0
  discordant)**.
- OLS dose-response slope of `A1 − A2` exact restoration across effort rank:
  **`+5.48 pp/step [+0.44, +10.59]`** (`+0.95 pp [−0.08, +2.02]` per
  `−log2(1 + budget)`). Zero thinking cuts mean `A1` trial latency from
  `17.44 s` (`high`) to `7.17 s` (`none`, `2.4×`).

**S2 `A0` ceiling completion (`T2A0/analysis.json`, `T2TA0/analysis.json`, A13).**
- *S2a (`a0fill`, `T2A0`):* `71` core-complement defects, `284/284` usable trials
  (`213` `A0@P1` + `71` in-session `A1@P1` anchor, `4,957,763` tokens). Pooled
  across all `142` core defects (`T2` + `T2A0`), `A0` repair is `98.8 % [97.2,
  100.0]`, and the `A1/A0` repair ratio over `141` paired defects is **`0.959
  [0.928, 0.988]`** (core in-session 71-defect ratio `0.962 [0.915, 1.000]`;
  `T2A0` in-session anchor ratio `0.981 [0.938, 1.019]`; `A1 − A0` repair `−4.0
  pp [−7.1, −1.2]`, `p = 0.070`). Exact restoration over `142` defects: `A0`
  `64.1 % [56.6, 71.4]`, `A1` `68.6 % [61.2, 75.7]` (`141` defects), `A2`
  `53.5 % [46.0, 60.9]` (`139` defects); `A1 − A0` restoration is `+4.0 pp
  [−2.6, +10.6]` (`p = 0.362`), `A0 − A2` is `+11.8 pp [+5.0, +18.5]` (`p =
  0.0135`), in-session `A1anchor − A0` is `+4.7 pp [−4.2, +13.6]` (`p = 0.424`).
  Pre-registered A13 reading: **`a2_below_task`** (`A1 ≥ A0`); share of gap
  closed `1.24 [0.74, 2.50]`. Cross-session drift (`A1anchor` vs core `A1` rep
  0): `67/70` (`95.7 %`) same outcome class, `43/70` (`61.4 %`) byte-identical.
- *S2b (`thinking_a0`, `T2TA0`):* `45` sweep defects at `none` and `high`,
  `360/360` usable trials (`270` `A0@P1` + `90` in-session `A1@P1` anchor,
  `3,642,358` tokens). Repair: `A0@none` `97.8 % [93.3, 100.0]`, `A0@high`
  `100.0 %` (exact CI `[92.1, 100.0]`). Exact restoration at `none`: `A0`
  **`38.5 % [24.4, 53.3]`** vs `A1` `80.7 % [68.9, 91.1]`, `A2` `57.0 % [43.0,
  71.1]`, in-session `A1anchor` `77.8 % [64.4, 88.9]`; cross-session `A1 − A0 =
  +42.2 pp [+28.1, +56.3]` (`p = 1.91e-6`), in-session `A1anchor − A0 = +39.3 pp
  [+25.2, +53.3]` (`p = 7.63e-6`), `A0 − A2 = −18.5 pp [−31.1, −7.4]` (`p =
  0.0039`). At `high`: `A0` **`58.5 % [45.2, 71.1]`** vs `A1` `60.7 %`, `A2`
  `50.4 %`, `A1anchor` `60.0 %`; cross-session `A1 − A0 = +2.2 pp [−13.3,
  +17.8]` (`p = 1.0`), in-session `A1anchor − A0 = +1.5 pp [−14.1, +17.0]` (`p =
  1.0`), `A0 − A2 = +8.1 pp [−5.2, +21.5]` (`p = 0.454`). Reading at both
  levels: **`a2_below_task`**; share-of-gap is not applicable at `none` (`A0`
  below `A2`, dated A13 note; literal value `−1.28`) and withheld at `high`
  (`A0 − A2` CI includes 0). Single-call `A0@none` restores `22.2 %` (`99`
  trials, `33` defects) vs `83.3 %` on the `36` `O6`/`O7` schema-retry trials.
  Drift (`A1anchor` vs `T2T` `A1` rep 0): `45/45` same outcome class at both
  levels; byte-identical `42/45` (`93.3 %`) at `none` and `38/45` (`84.4 %`) at
  `high`.

---

## 6. Pre-registered second-model replication on `gemini-3.5-flash-lite` (A15)

*Sources: `out_study/FL/A`, `out_study/FL/determinism/analysis.json`,
`out_study/T2FL/analysis.json`; frozen at `edfb406` / tag `prereg-fl-freeze`.*

- **Own bases and determinism.** Phase A (`FL/A`) ran all 28 sampled businesses
  (`503` calls, `2,603,688` tokens, seed 42, full `14/34/92/214` reviews per
  stratum; 3 businesses carry a `would_retry`). D20 gates yield `N_FL = 157`
  runnable defects (`168` attempted, `11` inapplicable; `Q_FL = 36` on the `A3`
  quarter stride; `1,521` planned trials; simulated 80%-power joint MDE `10.65
  pp`, joint power `97.7 %` at `15 pp` and `45.45 %` at `7.5 pp`). Determinism
  measurement (`FL/determinism/analysis.json`, `20/20` calls, `409,450`
  tokens): `8/10` raw-identical and `8/10` canonical-JSON-identical prompt
  pairs (`r = 3` unchanged).
- **Primary confirmatory test (A15 / I5) — replicated.** `1,520/1,521` usable
  trials across `157` defects (`0` defects dropped; `11,671,123` recorded
  tokens; 1 provider-failure `status_error` excluded). Unconditional
  canonical-JSON exact restoration is **`60.3 % [52.9, 67.7]`** on `A1`
  (`283/470` usable trials, `93/157` defect majorities) vs **`49.3 % [41.8,
  56.5]`** on `A2` (`232/471` trials, `77/157` majorities); **`A1 − A2 = +11.0
  pp, 95 % defect-cluster bootstrap CI [+5.1, +17.0]`**; discordant defect
  majorities **`23` (`A1` only) vs `7` (`A2` only)**, two-sided exact McNemar
  **`p = 0.0052`**. Positive estimate, 95% CI excluding 0, and `p < 0.05` all
  hold → **replicated**. Sensitivity excluding the `114` multi-attempt trials
  (`152` defects, `5` dropped): `59.9 %` vs `48.5 %`, **`+11.4 pp [+5.5,
  +17.5]`**, discordant `22` vs `7`, **`p = 0.0081`**.
- **Exploratory repair, `A0` comparisons, and dissociation pattern.** Binary
  repair is near ceiling across arms (`A0` `97.0 %`, `A1` `94.3 %`, `A2`
  `97.5 %`, `A3` `79.6 %` across 108 trials on 36 defects), with **`A1 − A2 =
  −3.2 pp [−6.4, −0.2]`** (discordant `2` vs `5`, exact McNemar `p = 0.453`;
  negative difference driven by `O1`, where `A1` repairs `71.8 %` vs `A2`
  `93.6 %`, while `O2`/`O3`/`O5`/`O6`/`O7` are `94.9–100.0 %`). The `A1/A0`
  repair ratio is **`0.972 [0.936, 1.004]`**, whose 95% CI contains `1`; under
  A15's prospective rule this predicted a **restoration-type** pattern, which
  matches the observed outcome (`restoration-type`: restoration CI wholly above
  0, repair CI not above 0). `A0` exact restoration is `51.2 % [43.9, 58.2]`;
  `A1 − A0` restoration is `+9.1 pp [+2.1, +15.9]` (`p = 0.060`), `A0 − A2` is
  `+1.9 pp [−3.8, +7.6]` (`p = 0.711`), `A1/A0` restoration ratio is `1.178
  [1.038, 1.341]`, and `A3` at `P0` restores `0/108` (`0.0 %`). Three-/four-way
  trial decomposition: `A0` `51.2 %` copy / `45.9 %` repaired rewrite / `1.7 %`
  replaced-or-deleted / `1.3 %` unrepaired; `A1` `60.2 %` / `34.0 %` / `5.7 %` /
  `0.0 %`; `A2` `49.3 %` / `48.2 %` / `1.9 %` / `0.6 %`. Model and Phase-A bases
  changed together, so this establishes replication on a second model run on
  its own bases rather than isolating model weights from base outputs.

---

## 7. Calibration and validity (no API cost)

*Source: `secondary_extra.json`.*

- **C6, frequency check (O4 swept over 23 bases):** 0 % detected for gaps ≤
  0.04, **52 % at exactly 0.05**, 100 % from 0.051 — the strict `> 0.05` in the
  check, with the 0.05 cases split by floating-point rounding of the injected
  value. The threshold behaves as designed.
- **C6, trace check:** on **139 grounded** recommendation issues (every clean
  strategy output across the 28 dumps) the production difflib matcher fires on
  **5.0 %** — the 7 grounded issues whose best lexical similarity to their own
  upstream falls below 0.35; the content-word matcher fires on none. On **150 foreign** corpus issues placed on other
  businesses, difflib fires on 96.0 %, content-word on 100 %. The production
  matcher both misses foreign content and flags grounded paraphrase — D13/D22,
  now as rates.
- **Coupling:** 13 of 13 real defects fire a check class that has a synthetic
  operator (by construction at the class level).

---

## 8. Production observations that are not about repair

- The **report stage needs a schema-correction second call every time** it
  runs from the production prompt (downstream pass: 2 calls per report stage in
  every one of 447 conditions; placement P0: all 16 report-stage defects).
- **Clean pipelines fail the supervisor 16 %** of the time in the downstream
  pass (≈ 20 % when the strategy stage is re-run). **All 29 rejections of clean
  runs are `untraceable_recommendation` at the re-run strategy stage** — the
  trace matcher's false positives above, met in fresh generations.

---

## 9. What remains

- **All planned and supervisor-requested experiments (through A15 / Q13) are
  complete, verified, and written to `analysis.json` (2026-11-17).** The author
  chose journal only on 2026-10-08; the conference paper was accepted at EAI
  FISAT 2026 (author, 2026-10-23; not yet published) and remains untouched.
- ✅ **2026-10-13 / 2026-10-23:** the journal draft's C7 placeholders are filled
  from `T2L/analysis.json`, amendments A10–A11 are recorded, and every `\TODO`
  is closed.
- ✅ **2026-11-02:** `T2T` (A12) is integrated into `05-results.tex`, `00-abstract.tex`,
  `01-introduction.tex`, `04-design.tex`, `06-discussion.tex`, `07-threats.tex`,
  `08-conclusion.tex`, and `highlights.txt`.
- **Remaining manuscript integration and build (`SUPERVISOR_FEEDBACK_2026-11-13.md` §3/§9/§10):**
  1. **S5 (`FL` / `T2FL`, A15):** add the replication design subsection and update
     the pending-S5 sentence in `04-design.tex`; add `FL`/`T2FL` to `tab:cells`
     and A15 to `tab:amendments`; update RQ2 in `05-results.tex` to lead with the
     pre-registered Flash-Lite replication (`+11.0 pp [+5.1, +17.0]`, `p = 0.0052`)
     ahead of the core's post-hoc estimate; add the third model to RQ6 and
     `appendix-diagnostics.tex`; revise `06-discussion.tex` and `07-threats.tex`
     ("discovered post hoc" / "one model", noting model and own bases changed together).
  2. **S2 (`T2A0`, `T2TA0`, A13) & S3 (`T1H` + pooled Tier-1, A14):** add cells
     to `tab:cells` and A13–A14 to `tab:amendments`; add 142-defect `A1/A0` to
     RQ1, `A0` at `none`/`high` to `tab:thinking` (reading `+23.7 pp` against
     `A0`), and 142-defect `A0` to `appendix-diagnostics.tex`; revise RQ3 across
     `04-design.tex`, `05-results.tex`, `06-discussion.tex`, `07-threats.tex`, and
     `08-conclusion.tex` to report `T1`, `T1H`, `Pooled`, and `A + H` side-by-side.
  3. **S1 & S4:** extend the S1 collection date window in `04-design.tex` §4.8 to
     include `T2FL` (`2026-11-16`); restore the 3-item numbered contributions in
     `01-introduction.tex` (dissociation + Flash-Lite replication) and align
     `00-abstract.tex`, `highlights.txt`, and `08-conclusion.tex`.
  4. **Checks and PDF build:** run `docs/paper/journal/check_draft.py`, compile
     `main.pdf` cleanly (`pdflatex` / `bibtex` / `pdflatex` × 2 if `latexmk`
     lacks Perl), and review manuscript length against JSS's 36-page target.
