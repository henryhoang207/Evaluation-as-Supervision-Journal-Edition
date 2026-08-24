# Chapter Plan — Short Paper, Track 1 (AI & Data Science)

**Mode:** `/ars-plan` (Socratic planning; originality-spectrum, very-high oversight)
**Date:** 2026-08-02
**Status:** Draft plan. Empirical chapters are specified but **not yet executed** — see §Evidence Ledger.

> [!WARNING]
> **Section 3 below is superseded.** It is the original 6-page / 7-chapter
> spec. The live target is **11 pages excluding references, 8 sections**.
> The current section skeleton and the 8-table / 2-figure list live in
> `HANDOFF.md` section 3, and are already scaffolded in `main.tex`
> (restructured 2026-08-03). Sections 1, 2, 4, 5 and 6 of this file remain
> current and are still the source of truth for positioning, insights,
> the evidence ledger, and the open decisions.

**Scope decided in dialogue:**
- Anchor: the deterministic supervision layer (`backend/app/core/supervision.py` + hub graph)
- Format: short paper (~6 pages, 2-column, incl. references)
- Evidence: multi-business empirical study, **observe-first** two-phase design
- Authorship: **deferred** — see §Open Decisions D5

---

## 1. Positioning

**Track 1 sub-area (recommended): Natural Language Processing and Multimodal AI.**
The contribution is about grounding and verification of LLM-generated claims, which
is NLP-native. *AI Applications* is the safe fallback if the venue reads NLP as
model-centric only. Decide before writing the abstract (D1).

**One-sentence pitch.**
> In a staged LLM pipeline, every downstream claim is derivable from upstream output —
> so groundedness is checkable deterministically, with no labels, *at runtime*. We promote
> an offline evaluation harness into a runtime supervisor and measure, across a real
> distribution of workloads, how often it fires and whether feedback-injected retry
> actually repairs the defect.

**What the paper claims.** Three things, in descending confidence:
1. An architectural pattern: *evaluation-as-supervision*, enabled by stage derivability.
2. A measured defect-incidence rate for an unsupervised multi-agent LLM pipeline
   across the real workload distribution. **No published number exists for this.**
3. A measured repair rate for deterministic feedback-injected retry. **This is the
   genuine open question** — the mechanism is not guaranteed to work, and the answer
   could be negative. A negative result here is still publishable and still honest.

**What the paper must NOT claim** (from `docs/report_supporting/novelty_assessment.md`,
independently corroborated by my own read of the code):
- Multi-agent role decomposition — standard (MetaGPT/AutoGen lineage)
- ABSA itself, or the 7-category taxonomy — SemEval-2014 territory, and the taxonomy is project-defined
- LLM-as-judge with rubrics — established (MT-Bench, G-Eval)
- Pydantic-validated structured output, LangGraph, FastAPI/React — commodity engineering

---

## 2. INSIGHT Collection

The claims the paper rests on. Each is tagged with its evidentiary status.

### Core insights (headline material)

**I1 — Derivability enables label-free runtime verification.** `[HAVE — argument]`
Each stage consumes only what earlier stages in the same run produced. The condition is
**closure, not linearity** — the report stage reads analysis, reasoning *and* strategy,
so "only the previous stage" is false and must not be written. Therefore every
downstream claim has a checkable provenance in upstream state, and correctness reduces
to consistency checks needing no ground truth. *This is the enabling condition and the paper's
transferable claim* — it holds for any staged LLM pipeline, not just this one.
Source: `docs/EVALUATION_REPORT.md` §3.

**I2 — Schema validity is not groundedness.** `[HAVE — code]`
A fabricated but Pydantic-valid output is `status: "success"`. Retry, model fallback,
and criticality downgrade all protect against *breaking*; none protects against
*being wrong*. Source: `docs/FINDINGS_2026-07-16.md` F4. This is the gap the paper enters.

**I3 — Retry without feedback at temperature 0 is mechanically wasted.** `[HAVE — argument]`
Identical prompt → identical wrong output; the retry cap burns for nothing. The
*content* of the feedback is the active ingredient, not the retry. Sharp, under-stated
in the self-correction literature, and directly motivates the `retry_feedback` mechanism.
Source: `docs/ORCHESTRATOR_SIMPLE_HUB.md` §5.3.

**I4 — A verifier sharing logic with its evaluator cannot be evaluated by it.** `[HAVE — methodological]`
`supervision.py` deliberately mirrors `eval/tier1_checks.py` ("so that what the
orchestrator enforces mid-run and what Tier 1 scores offline can never disagree").
Good engineering; a methodological trap. **Stating this ourselves is worth more than
any result it costs us.** Drives the non-circular measure set in §5.

### Supporting insights

**I5 — Arithmetic delegated to an LLM is a self-inflicted hallucination class.** `[HAVE — code]`
`Pattern.frequency` was asked of the model *and* recomputed in Python for checking —
so the guess added a failure mode and no information. Recompute-and-overwrite deletes
the class. Source: FINDINGS F2a, implemented in `supervision.apply_frequency_corrections`.

**I6 — Determinism where determinism suffices.** `[HAVE — design]`
The canonical LangGraph supervisor routes with an LLM. Hard rules over measured facts
are auditable, reproducible, zero marginal cost, unit-testable — and remove the
supervisor's dependency on the provider it supervises. Source: FINDINGS F7.

**I7 — The median restaurant has 34 reviews.** `[HAVE — measured, n=52,268]`
Over the businesses carrying the *Restaurants* category with at least five reviews:
**p10=7, p25=14, p50=34, p75=92, p90=214** (measured 2026-08-03).
**Do not quote 6/8/15/38/101** — that is the ALL-CATEGORY distribution over 150,346
businesses of every kind (hotels, car dealers, visitor centres), and this paper is
about restaurants. The correction is load-bearing: with `LOW_CONFIDENCE_N=30` the
median restaurant sits *above* the confidence floor, so the sharper framing — that the
median case falls beneath the system's own threshold — **does not survive and must not
be used**. Still justifies stratifying by review count rather than sampling uniformly.
Source: FINDINGS F1, re-measured against the restaurant subset.

**I8 — A healthy harness catches errors.** `[HAVE — one live instance]`
24/25 with one real caught defect (a 22-character Yelp ID transcribed with one
character dropped) is a stronger signal than a suspicious 25/25. Use as a vignette
in §4, not as a headline result.

---

## 3. Chapter Structure

**Eight sections, full-paper scale.** At 11 pages excluding references this is a
full LNCS paper, not a short one: Related Work gets a proper treatment, the
supervision layer gets its own section separate from the system description, and
Threats to Validity is broken out rather than folded into Discussion. Page
budget in section 7.

### 1 - Introduction `[1.0 pg]`
- Open on I2: the defense gap. Structured-output tooling has made LLM pipelines
  *well-formed*; it has not made them *grounded*.
- State I1 as the enabling observation, in its own paragraph.
- State the three contributions.
- **Do not** open on restaurants or Yelp. The domain is the testbed, not the
  point; a Track 1 reviewer must see a verification paper.

### 2 - Background and Related Work `[1.5 pg]`
Four subsections, each ending in the gap it leaves. At this length, add a
**positioning table** (Table 1) comparing this work against AutoGen, MetaGPT,
CRITIC, Reflexion, and the LangGraph supervisor pattern along three axes:
*who decides routing*, *what the feedback signal is*, *is verification
inter-stage or single-generation*. A table earns its space here because the
contribution is differential, not absolute.

1. **Multi-agent LLM systems** - AutoGen, MetaGPT, Guo survey.
   *Gap: the manager concept is supported; a supervisor routing on
   deterministically measured facts is not described.*
2. **Self-correction from feedback** - Self-Refine, Reflexion, CRITIC, Pan
   survey. *Gap: feedback is LLM self-critique or tool output. Deterministic
   measured-fact feedback under an enforced cap is unstudied, and I3 appears
   untested.*
3. **Grounding and verification** - CRITIC is the nearest neighbour.
   *Gap: verification applies to a single generation, not to inter-stage
   consistency, which is what derivability makes available.*
4. **LLM-as-judge and its biases** - MT-Bench, G-Eval, position bias,
   self-preference. Used as a non-circular measure in section 6; biases return
   in section 7.

> **Provenance note.** The 22-reference base is
> `docs/report_supporting/research_grounding.md`, which records a live
> verification pass (July 2026) on every entry. **Not independently re-verified
> here.** Re-run `/ars-citation-check` before submission - D4.

### 3 - System and the Derivability Property `[1.0 pg]`
Now its own section rather than a subsection, because derivability is the
paper's transferable claim and should not be buried in an architecture
description.
- **3.1 Pipeline.** Four agents: analysis, reasoning, strategy, report. State
  precisely which state each stage reads.
- **3.2 Derivability.** Formalise lightly: stage *k* consumes only the output of
  stage *k-1*, so every claim at *k* must resolve against *k-1*. Derive the
  consequence - groundedness becomes a consistency question, not a ground-truth
  question. This paragraph is the paper.
- **3.3 Design alternatives considered.** The full validator-node redesign
  versus the simple hub actually built (`docs/ORCHESTRATOR_DESIGN.md` versus
  `docs/ORCHESTRATOR_SIMPLE_HUB.md`). Contract-change cost, test-rewrite cost,
  and the decision to drop the `skip` verdict as self-contradictory. Real
  engineering trade-off analysis, already documented in the repo - it is
  evidence of design discipline and costs nothing new to write.

### 4 - The Supervision Layer `[2.25 pg]` - **Figure 1, Tables 2-3**
- **4.1 Hub architecture.** `agent -> orchestrator(measure -> decide) -> next`.
  The orchestrator is the entry point and the only routing node. Contrast with
  a failure-only error handler: a supervisor whose verdict vocabulary has no
  word for *proceed* cannot own the happy path.
- **4.2 Measurement.** Deterministic, per stage, no LLM. **Table 2** maps stage
  to checks: evidence-ID resolution, aspect alignment, statistic recomputation,
  star-versus-sentiment contradiction rate, recommendation traceability,
  report-subset containment, trusted-metadata match.
- **4.3 Decision rules.** Four verdicts, hard rules, retry cap evaluated first
  so the graph cannot loop. The LLM-escalation branch was considered and
  rejected (I6).
- **4.4 Two correction layers, one channel.** Syntactic (validation error) and
  semantic (measured fact). Motivate with I3.
- **4.5 Recompute-and-overwrite.** I5.
- **4.6 Failure-mode coverage.** **Table 3** - the 22 unit-verified scenarios in
  `tests/test_supervision.py`, mapped to the defect classes in
  `docs/FINDINGS_2026-07-16.md` that each closes. *This was cut from the
  short-paper scope and now fits.* It establishes what the supervisor **can**
  catch before section 6 reports what it **did** catch - capability, then
  incidence. Costs no new runs.

### 5 - Method `[1.5 pg]` - **Tables 4-5**
- **5.1 Testbed and data.** Yelp Open Dataset, SQLite-indexed. State the
  sampling cap and that whole-dataset coverage is never claimed.
- **5.2 Workload sampling.** Stratified by review count (I7), not uniform.
  **Table 4** = stratum, businesses, review-count min/median/max.
- **5.3 Two-phase design.** Phase A observe (measure, log, always proceed);
  Phase B enforce (only businesses with a retry-triggering defect).
  **Justify the asymmetry explicitly** - where nothing is detected the arms are
  identical by construction, so a second arm consumes compute without producing
  evidence.
- **5.4 Controls.** One provider and model across both arms, recorded per run;
  temperature 0; fixed seed. State honestly that API non-determinism at
  temperature 0 is not fully eliminable.
- **5.5 Measures and circularity.** **Table 5.** This subsection is where I4
  earns its keep - place it before any result is reported.

### 6 - Results `[2.25 pg]` - **Tables 6-8, Figure 2**
- **6.1 Defect incidence (Phase A).** **Table 6** by check type. Lead with the
  aggregate, then decompose.
- **6.2 Defect rate versus review count.** **Figure 2.** Tests whether
  *grounding* defects scale with sample size or only the by-definition
  low-sample flag does. Either outcome is informative.
- **6.3 Does feedback-injected retry repair the defect?** **Table 7.**
  **Report failures prominently.** A low repair rate is the more interesting
  finding and directly tests I3. Separate *repaired* from *replaced by a
  different defect*.
- **6.4 Cost of supervision.** **Table 8.** The supervisor makes no LLM call, so
  all overhead is attributable to retries - state that, it is a genuine
  architectural advantage.
- **6.5 Independent judge assessment.** The only affordable non-circular
  *quality* measure. See D3.
- **6.6 Worked example.** *New at this length.* Trace one business end to end -
  measured facts, verdict, feedback text, retry outcome. Use the existing
  `backend/out_hub/` dump. Makes the mechanism concrete in a way no table does,
  and needs no new runs.
- **6.7 A caught defect.** The I8 vignette: a 22-character identifier
  transcribed with one character dropped, cited as evidence for a pattern whose
  aspect and recomputed statistic were both otherwise correct.

### 7 - Discussion, Limitations, and Threats to Validity `[1.0 pg]`
Lead with limitations - a credibility asset, not a tax.
- **Circularity (I4).** State plainly; name the non-circular subset the headline
  rests on.
- **Derivability is a precondition, not a universal.** Name the architectures it
  does *not* cover: shared-scratchpad agents, free-form conversational loops -
  anywhere provenance is not structural.
- **Single domain, dataset, provider.** No generalisation claim.
- **Reference labels for one business only**, single annotator, so Cohen's kappa
  is uncomputed. Calibration, not a validated accuracy claim.
- **Thresholds are uncalibrated proposals.** `MIN_VIABLE_N=5`,
  `LOW_CONFIDENCE_N=30`, `CONTRADICTION_MAX=0.20`, `FREQUENCY_TOLERANCE=0.05`
  have no literature derivation. This study's data is the first calibration
  input - say so.
- **Judge bias** bounds the section 6.5 measure.

### 8 - Conclusion `[0.5 pg]`
Restate derivability as the transferable result, not the system as the result.
Close on one concrete future-work item: Wilson confidence intervals over the
now-exact recomputed statistic, which matters because the median business here
carries 15 reviews - a regime where a two-decimal point estimate is
indistinguishable from noise.

---
## 4. Evidence Ledger

What exists versus what the study must produce.

| Need | Status | Source / gap |
|---|---|---|
| Supervision layer implemented | `[HAVE]` | `app/core/supervision.py`, `app/core/graph.py` (commit `953a6bd`) |
| 22 failure-mode scenarios, unit-verified | `[HAVE]` | `tests/test_supervision.py` — 22 named tests |
| One real caught defect, live | `[HAVE]` | Mistyped evidence ID; `docs/EVALUATION_REPORT.md` §3 |
| 6/6 degradation paths | `[HAVE]` | `eval/harness.py::check_degradation_paths` |
| Review-count distribution, n=150,346 | `[HAVE — measured]` | FINDINGS F1 |
| Tier 2 gold set (73 reviews, 1 annotator) | `[HAVE — limited]` | Sentiment acc. 0.753, aspect macro-F1 0.852 |
| Tier 3 rubric scores (1 business) | `[HAVE]` | 4.8 / 4.2 / 5.0, judge `gemini-pro-latest` |
| Latency & token baseline | `[HAVE]` | 3.57 s/review, ~1,483 tokens/review |
| SQLite index on this machine | `[HAVE]` | `backend/data/processed/yelp.db`, 5.4 GB, 2026-07-10 |
| **Observe mode (measure, always proceed)** | `[BUILD]` | ~15 lines in `graph.orchestrator_node` |
| **`--business-id` selection** | `[BUILD]` | ~5 lines in `run_pipeline.py` (currently name+fuzzy only) |
| **Stratified business sampler** | `[BUILD]` | Query `yelp.db`; percentile query exists in FINDINGS F1 |
| **Batch runner + resume** | `[BUILD]` | ~120 lines; `tier1_checks.run_all()` is already programmatic |
| **Phase A + B results** | `[RUN]` | ~26 runs, ~1.5–2 h unattended, ~1.5 M tokens |
| **Figure 1 (architecture)** | `[MAKE]` | Carries the paper |

⚠️ **Do not reuse the two existing dumps as a before/after pair.** `backend/out/` ran on
Gemini and `backend/out_hub/` ran on Groq/Llama — different providers, so the diff would
confound supervision with model change. Both arms must be re-run on one fixed provider.

⚠️ **Do not use the pre-hub commit as the supervision-off arm.** That is the old linear-chain
graph; the comparison would confound supervision with graph shape. Use observe mode.

---

## 5. Open Decisions

| # | Decision | Recommendation |
|---|---|---|
| **D1** | Track sub-area: NLP vs. AI Applications | **NLP** — the contribution is grounding/verification. Affects framing of Ch. 1–2. |
| **D2** | N and stratification | **20 businesses, 5 each at ≈p25/p50/p75/p90** (14/34/92/214 reviews; the 8/15/38/101 figures were the all-category distribution and are wrong). Weighting toward the median is defensible via I7 but costs statistical power in the high-n strata where grounding defects may concentrate. |
| **D3** | Run Tier 3 judge on the Phase B subset? | **Yes** — ~3 calls per output, and it is the only affordable non-circular *quality* measure. Cheap insurance against the circularity objection. |
| **D4** | Re-verify the 22 references | **Yes, before submission.** They were verified by a teammate in July 2026; I have not re-checked them. `/ars-citation-check`. |
| **D5** | Authorship | **Still deferred.** The supervision layer is a teammate's commit (`953a6bd`) built deliberately on your `eval/tier1_checks.py`. The *study* in Ch. 4–5 would be entirely your own new work. Resolve before writing the author block — it does not block starting Ch. 3–4. |
| **D6** | Provider for the study | **`gemini-2.5-flash`** — the approved config, and consistent with the existing evaluation report. Record via `run_config` per run. |

---

## 6. Suggested Order of Work

1. **Ch. 3 + Figure 1** — pure writing from code that already exists; no dependency on the runs.
2. **Build** the four `[BUILD]` items (~half a day).
3. **Run** Phase A, then Phase B (~2 h unattended; checkpoint and resume — 26 runs is 300+ LLM calls and rate limits, not cost, are the binding constraint).
4. **Ch. 4 + 5** against real numbers.
5. **Ch. 2** — cheapest to write late, once the gap statements are sharp.
6. **Ch. 1, 6, 7** last.
7. `/ars-citation-check`, then `/ars-abstract`.

Step 1 is genuinely independent of the runs, so start there if the compute slot is uncertain.

## 7. LNCS Page Budget

**Confirmed limit: 11 pages excluding references.** With references at roughly
1 to 1.5 pages, the submission runs about 12.5 pages - a standard LNCS **full
paper**. Earlier drafts of this plan assumed a short paper and advised
compressing Related Work; that advice is superseded.

LNCS is single-column at roughly 450 words per page, against roughly 950 for
IEEE two-column. Eleven LNCS pages is therefore about 4,950 words of body, of
which tables and figures will consume perhaps a page and a half - leaving
roughly 4,000 to 4,300 words of prose.

| Section | Pages |
|---|---|
| 1 Introduction | 1.0 |
| 2 Background and Related Work (incl. Table 1) | 1.5 |
| 3 System and the Derivability Property | 1.0 |
| 4 The Supervision Layer (Fig. 1, Tables 2-3) | 2.25 |
| 5 Method (Tables 4-5) | 1.5 |
| 6 Results (Tables 6-8, Fig. 2) | 2.25 |
| 7 Discussion, Limitations, Threats to Validity | 1.0 |
| 8 Conclusion | 0.5 |
| **Body total** | **11.0** |
| References (excluded from the limit) | ~1.0-1.5 |

### The budget grew, so add rather than cut

Moving from 8 pages including references to 11 excluding them roughly doubles
the available body. Four additions, in order of value per hour:

1. **Failure-mode coverage table (4.6).** The 22 unit-verified scenarios mapped
   to the defect classes each closes. Cut from the short-paper scope; now it
   fits. **No new runs.**
2. **Worked example (6.6).** One business traced end to end through
   measure - decide - feedback - retry, from the existing `backend/out_hub/`
   dump. **No new runs.**
3. **Design alternatives (3.3).** Validator-node redesign versus simple hub;
   contract-change cost, test-rewrite cost, and why `skip` was dropped. Already
   written up in the repo. **No new runs.**
4. **Related-work positioning table (2).** Differential positioning against
   AutoGen, MetaGPT, CRITIC, Reflexion, and the LangGraph supervisor.

All four are writing tasks against material that already exists. None depends on
the Phase A/B runs, so all four can proceed while compute is pending.

### If it still overruns

1. **Section 2** - the positioning table can absorb two of the four
   subsections.
2. **Section 3.3** - design alternatives is the most droppable *new* material.
3. **Figure 2** - the most droppable visual.

**Never cut the circularity paragraph in section 7.** It is load-bearing.
