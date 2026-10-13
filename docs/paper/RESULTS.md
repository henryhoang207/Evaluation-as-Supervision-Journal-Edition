# Results — injected-defect repair study

**Written 2026-10-08; C7 added 2026-10-12.** The record of what the journal-extension experiments
found, for writing the paper from. Every number here is printed by a committed
script from committed data; the source is named beside each block. Design and
every deviation from it: `PREREGISTRATION.md` (frozen at tag `prereg-freeze`,
amendments §0.1 A1–A11). Operational history: `RUN_QUEUE.md`.

All cells except C7: `gemini-2.5-flash` through Google's OpenAI-compatible endpoint, no
fallback (`LLM_DISABLE_FALLBACK=1`), temperature 0 unless stated. Total spend
≈ 53 M charged tokens. **C7 is complete and verified**: Qwen2.5-7B-Instruct
Q4_K_M via Ollama on an RTX 5060 Ti 16 GB; 930 local trials, 929 usable,
7.36 M tokens in valid trials, zero API fees. All planned experiments are done.

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

Every pass: one session per defect (all checked), offline re-score of every
trial in full agreement with the live score, `status_error` excluded and
counted. The core's 18 exclusions are network drops and one overnight laptop
sleep; they cost 3 defects their A1/A2 pair.
C7's single exclusion is a capped response followed by a blocked oversized
schema correction; it is counted as unrepaired in the pre-specified sensitivity.

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
| A0 ceiling | high | **100 %** (209/209 trials) | ✅ |
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
  pre-injection output byte for byte** (core).
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
  40 %; A0 77 % / 23 %). r = 3 carries little more than r = 1 — the occasion
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
(`T1/analysis.json`; descriptive only, intervals over 7 cells). Accepted by the
supervisor's own checks after the retry at P0: **A1 (the production retry)
28.2 %, A2 76.9 %, A3 25.6 %**. On the trace class (8 of 13) the content-word
check accepts A1 87.5 %, A2 100 %, A3 79.2 %. A3 returns the original
defective output 48.7 % of the time; A1 and A2 never do.

**Defect origin** (§3 item 5; `secondary_extra.json`). On the one shared
footing — supervisor acceptance of the retried output at P0 — A1 is accepted
for **98.5 % of injected defects but 28.2 % of real ones** (A3: 98.0 % vs
25.6 %). The D13 audit already found 0 of 11 real defects to be errors to a
human: most are checker false positives the retry cannot "fix", because the
checker keeps misreading the regenerated output.

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

---

## 6. Calibration and validity (no API cost)

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

## 7. Production observations that are not about repair

- The **report stage needs a schema-correction second call every time** it
  runs from the production prompt (downstream pass: 2 calls per report stage in
  every one of 447 conditions; placement P0: all 16 report-stage defects).
- **Clean pipelines fail the supervisor 16 %** of the time in the downstream
  pass (≈ 20 % when the strategy stage is re-run). **All 29 rejections of clean
  runs are `untraceable_recommendation` at the re-run strategy stage** — the
  trace matcher's false positives above, met in fresh generations.

---

## 8. What remains

- **No planned experiment remains.** The author chose journal only on
  2026-10-08; the conference paper remains under review and untouched.
- Journal writing: replace C7 placeholders with the verified results, record
  amendments A1–A11, and cover limitations — no specific-but-wrong feedback
  arm (D14), the bundled model/runtime comparison on fixed Gemini bases (D15),
  shallow checks (D16), Gemini's ceiling and local repair headroom.
- Author decisions for submission remain in `JOURNAL_PAPER_PLAN.md`; existing
  draft and unrelated local edits have been preserved.
