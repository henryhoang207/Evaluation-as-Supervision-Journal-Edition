# Journal Extension Plan — Injected-Defect Repair Study

**Written:** 2026-08-24 · **Amended:** 2026-08-24 after the Tier-A reading and Tier B in full — 9/9 read (see §13, §14)
(extraction: `..\Reading List\Tier_A\Tier_A_extraction.md`) — D1 reversed,
arm set extended, statistics refined · **Status:** proposed, not yet agreed with supervisor

> **Second review pass, 2026-08-24 — code-verified against the repository, not
> the literature.** Unlike §13 and §14, which amend by accretion, this pass
> **edits the affected sections in place** (the consolidation `NEXT_SESSION.md`
> called overdue). Changes, all traceable to the code or to `out_study/`:
> **§3** gains D8 (was implicit), **D9** (placement has four levels, and the
> production one was unnamed) and **D10** (Tier-2 context condition);
> **§5** — the Tier-1 bank is **11, not 15**, and covers **two stages**: three
> entries are API 503s and the only report-stage entry is a cascade of one of
> them (`scripts/analysis/defect_bank.py` reproduces this);
> **§6.1** — the Tier-2 core must run at **P1**, or every arm hits ceiling;
> **§4** — B1/B2/B3 are substantially cheaper than budgeted, B6's collateral
> metric cannot discriminate as written, B7 must log `attempts_made`;
> **§8** — Tier-1 blocking is over ~5 clusters. Nothing in §13/§14 is retracted.

> **Publication-strategy pass, 2026-08-24.** Conference paper #1 is **submitted
> and under review**, and the repair study may ship as its own conference paper
> before the journal. That adds **D11** (number of papers — decided: build and
> run first, then branch on the result) and **D12** (downstream propagation
> moves *in* scope, and **blocks B7**). §11's scope-creep list and §12's venue
> analysis are amended accordingly. The reasoning — pros and cons of splitting,
> what remains for the journal, whether either claim is significant enough, and
> what changes regardless of the split — lives in
> **`PUBLICATION_STRATEGY.md`**.

> **Power pass and §3 restructure, 2026-08-24.** Two Phase-0 items that could
> not be settled by argument were settled by computation, and both changed the
> design: **D4d** (`scripts/analysis/power.py`) shows the arm-ablation cell has
> **0.30 power** for the plan's own predicted 12 pp effect, that **160 defects
> is a hard ceiling** set by the 20 Phase-A dumps, and that the **D8 C1
> interaction is undetectable at any affordable size**; **D3c**
> (`scripts/analysis/churn.py`) measures the collateral floor from the
> repetition sub-study and finds it differs by an order of magnitude across item
> types. See §6.1b.
>
> §3 was also **restructured from chronological to functional order** — it had
> become an archaeology of the revision history, with D1 partly superseded by
> D9/D10, D7 by D11, and D3 contradicted by §13.5. Decision **numbers are
> unchanged**, so every cross-reference elsewhere in this file still resolves.
> The table now runs D1–D17 in six groups, with ⛔ marking blockers and ❓
> marking the four questions the Phase-0 memo must actually ask.

**Relationship to other docs:** conference paper #1 is **submitted and under
review** (`main.tex`; see `NEXT_SESSION.md`). This plan covers the journal
extension only; `PUBLICATION_STRATEGY.md` decides how many papers the work
becomes. Where this plan cites conference results it cites them as fixed.

**One-line goal.** Convert the conference paper's honestly-unmeasured quantity
— *does feedback-injected retry repair a detected defect?* — into the journal
version's headline result, using controlled defect injection and replay
instead of waiting for stochastic defects.

---

## 1. Claim structure of the journal version

Conference claims (kept as-is): the evaluation-as-supervision pattern +
derivability precondition; 35% defect incidence; defect instability (single-run
evaluation reports a draw, not a property).

New claims this study adds, in descending order of ambition:

| # | Claim | Measured by |
|---|---|---|
| C4 | **First measured repair rate for deterministic-feedback retry** in a staged LLM pipeline, with causal attribution: measured-fact feedback vs. generic rejection vs. bare re-draw, reported against a capability ceiling | Tier 1 + Tier 2, arms A0–A3 |
| C5 | **Self-attribution (blind-spot) effect at pipeline-stage granularity** — does presenting the defective output as the model's own prior turn change the repair rate? Decomposes attribution from triggering in a pipeline setting, which no paper has done | Placement arms P1/P2 (§3 amendments) |
| C6 | **First calibration data for the supervisor's thresholds** — detection curves vs. injected severity per check | Severity sweeps (no LLM calls) |
| C7 | (stretch) **Clean causal identification on a deterministic local runtime** — bare retry is bit-identical locally, so any repair in the feedback arm is attributable to feedback content; reconciles Insight I3 with the instability finding | Local Ollama arm |

Framing insight worth a sentence in the abstract: *the same closure property
that makes verification free also makes the pipeline a replayable
fault-injection testbed* — every stage's input is fully captured in state, so
real defects already on disk can be re-entered under enforcement.

**Known tension to resolve in writing:** conference I3 says a temperature-0
retry without new content is "mechanically wasted"; the repetition study shows
68% of identical-input hosted runs differ. Resolution: I3 is exactly true on a
deterministic runtime (C7 demonstrates it), leaky on hosted APIs — say
precisely that.

---

## 2. Reading list

Priority tiers: **A** = read deeply before designing (these papers dictate
design decisions), **B** = read carefully during the build, **C** = skim for
positioning while writing Related Work. ✱ = already in `references.bib`
(re-read, don't re-verify yet). arXiv IDs for 2026 papers came from a
2026-08-24 search; run `/ars-citation-check` over the final bib before
submission.

### Tier A — design-defining (read first, ~1 week)

| Paper | Venue | Why you must read it |
|---|---|---|
| **Self-Correction Bench: Uncovering and Addressing the Self-Correction Blind Spot** (arXiv 2507.02778) | COLM 2026 (v3; single author Ken Tsui) | ✅ Read 2026-08-24. The controlled-error-injection methodology this study extends to pipeline stages. Key result: 64.5% blind spot — models correct externally-presented errors 2–3× better than self-attributed ones. **Decided D1 (reversed it) and defined arms A0/P1–P3.** |
| **Is Self-Repair a Silver Bullet for Code Generation?** — Olausson et al. (arXiv 2306.09896) | ICLR 2024 | ✅ Read 2026-08-24. The methodological standard for repair claims: compare against best-of-n resampling under equal budget; feedback quality drives everything; cost-adjusted metrics. **Dictates the three-arm design and budget accounting.** |
| **LLMs cannot find reasoning errors, but can correct them given the error location** — Tyen et al. (arXiv 2311.08516) | ACL Findings 2024 | ✅ Read 2026-08-24. Separates error *location* from *correction*: correction works when the location is supplied. Your supervisor supplies location + content deterministically — this paper predicts your feedback arm works, which makes either outcome publishable. |
| **Are Mutants a Valid Substitute for Real Faults in Software Testing?** — Just et al. | FSE 2014 | ✅ Read 2026-08-24. The realism objection and the validation protocol that answers it: couple synthetic operators to real faults empirically. **Dictates the Tier-1-validates-Tier-2 design.** |
| **MAS-FIRE: Fault Injection and Reliability Evaluation for LLM-Based Multi-Agent Systems** (arXiv 2602.19843) | 2026 preprint | Nearest 2026 neighbour: 15-fault taxonomy, injection via prompt/response/routing manipulation, measures propagation and diagnosis — **not repair**. Your gap statement. ⚠ Read 2026-08-24: submission preprint (ACM placeholders); the abstract's ">40%" figure has no located derivation in its results — cite taxonomy and injection mechanisms, not that number. |

### Tier B — read during the build (~week 2–3)

| Paper | Venue | What to extract |
|---|---|---|
| **AgentChaos** — Tan et al. (arXiv 2608.06790) | **ASE 2026** (peer-reviewed; DOI 10.1145/3832783.3837437) | ✅ Read 2026-08-24. **Highest-value citation in Tier B for an SE venue.** Supplies: trigger-verification norm, the aborted/reported/silent scheme your four classes refine, the stage-position prior (pipeline Δpass@1 −4.84%→83.87%), and diagnosis accuracy ~50% — the argument for a deterministic supervisor (§14.3, §14.8). No repair measurement: gap confirmed. |
| **Large Language Models Cannot Self-Correct Reasoning Yet** — Huang et al. (arXiv 2310.01798) | ICLR 2024 | ✅ Read 2026-08-24. Intrinsic self-correction fails; external verifier feedback is the carve-out your system occupies. **Its §5 prompt-completeness argument is a confirmed hit on the frozen design — see §13.1.** |
| **When Can LLMs Actually Correct Their Own Mistakes?** — Kamoi et al. (arXiv 2406.01297) | TACL 2024 | ✅ Read 2026-08-24. Framework category = **RQ2, fair-asymmetric, external non-LLM verifier** (§3.2 interpreter analogy legitimises it). **Independently confirms D8** via its Table 7 checklist, and its Table 8 negative-results checklist forces pre-specifying the A1 template now (§14.7). |
| **Role Relabeling Gates Explicit Error Flagging in LLMs** — Chen, Su, Lin, Li, Chiang (arXiv 2606.05976**v2**, 31 Jul 2026) ⚠ *filename/title mismatch: not "The Self-Correction Illusion"* | Preprint, unrefereed | ✅ Read 2026-08-24. Byte-identical claim, role varied: +23 to +93 pp, 12 model–domain combinations, n=30 each. **Contradicts SC-Bench on "Wait" and demotes P3 — see §13.4.** Also supplies published precedent for synthetic injection. |
| **Why Do Multi-Agent LLM Systems Fail?** (MAST) — Cemri et al. (arXiv 2503.13657) | NeurIPS 2025 D&B | ✅ Read 2026-08-24. Mapping done (§14.10): reachable modes 1.1/1.2/2.3/2.4/2.5/2.6; **3.2 and 3.3 eliminated by the deterministic supervisor rather than mitigated.** ⚠ Category percentages are internally inconsistent across the paper — do not quote until the denominator is established (§14.9). |
| **Teaching Large Language Models to Self-Debug** — Xinyun Chen et al. (arXiv 2304.05128) | ICLR 2024 | ✅ Read 2026-08-24. The feedback-content gradient; the analogue of the A1-vs-A2 manipulation. **Its own numbers put A2 at ~70% of A1 — evidence for the activation hypothesis, not the feedback-quality one it is usually cited for (§13.3).** |
| **How Many Tries Does It Take?** — Arimbur (arXiv 2604.10508) | Preprint, single author, no venue | ✅ Read 2026-08-24. **Two hits: the session-blocking requirement (§14.1) and the ~45% expected repair rate (§14.2).** Cite for curve shape and the determinism threat only — never point estimates. |
| **Self-Edit** — Zhang et al. | ACL 2023 | ✅ Read 2026-08-24. A3 evidence: the no-comment ablation captures 70% of A1 on APPS-dev pass@1 but **0%** on APPS-test pass@10 — A3 collapses as difficulty rises (§14.2). Also a second, independent mechanism for P2 < P1 (§4.5 provenance mismatch). Most droppable of the group. |
| **On the Resilience of MAS with Faulty Agents** (AUTOINJECT) — Huang et al. (arXiv 2408.00989v4) | **ICML 2025** (peer-reviewed despite arXiv stamp) | ✅ Read 2026-08-24. Quantitative basis for stratifying by defect origin (−12.45 vs −8.83, not exchangeable); the distraction-comment result forces the P3 wording audit (§14.5); Double Checking needs a logging change (§14.6). ⚠ Disambiguate from Huang et al. 2024. |

### Tier C — skim for Related Work (~writing phase)

| Paper | Why cite |
|---|---|
| **AgenTracer** (arXiv 2509.03312) | Uses counterfactual replay + programmatic injection — but to train failure *attribution*, not to measure repair. Distinguish purpose. |
| **Who&When** — Zhang et al. 2025 (verify ID) + **Seeing the Whole Elephant** (arXiv 2604.22708) | Failure-attribution benchmarks; adjacent problem (who failed) vs. yours (does repair work). |
| **AgentSpec: Customizable Runtime Enforcement for LLM Agents** (arXiv 2503.18666, ICSE 2026) | Runtime enforcement thread — action-safety policies vs. your content-groundedness. State the distinction explicitly. |
| **Reason Less, Verify More: Deterministic Gates…** (arXiv 2607.07405, July 2026) | Closest in spirit (deterministic gates in agent loops); differentiate: policy compliance vs. inter-stage derivability. |
| **From Agent Traces to Trust** — provenance survey (arXiv 2606.04990) | Situates derivability in the provenance/evidence-tracing literature. |
| **RARR** — Gao et al. (arXiv 2210.08726, ACL 2023) | Revision-with-preservation metric — the model for your collateral-damage measure. |
| **Measuring Faithfulness in Chain-of-Thought Reasoning** — Lanham et al. (arXiv 2307.13702) | Error injection into reasoning as measurement — methodological ancestor. |
| **Defects4J** — Just et al., ISSTA 2014 | Real-vs-seeded benchmark tradition; one citation in the realism paragraph. |
| **Let's Verify Step by Step** — Lightman et al. (arXiv 2305.20050) | Learned step-level verifiers (PRMs) vs. your deterministic stage-level one; one-paragraph contrast. |
| **Chaos Engineering** — Basiri et al., IEEE Software 2016 | Lineage citation for the Tier-2 framing. |
| ✱ **CRITIC**, ✱ **Pan et al. survey**, ✱ **Self-Refine**, ✱ **Reflexion** | Already cited; re-read Pan's feedback-source taxonomy — the journal version's Table 1 gains a "feedback = deterministic measured fact" row backed by the new experiment. |

Reading order: Tier A in week 1 (Self-Correction Bench and Olausson first —
they change the design), then the Phase-0 memo to your supervisor. Tier B
alongside the harness build. Tier C while writing.

---

## 3. Phase 0 — decisions to lock with supervisor (before any code)

**Restructured 2026-08-24.** The table was chronological — D1 partly superseded
by D9/D10, D7 by D11, D3 contradicted by §13.5 — so a reader was doing
archaeology on the revision history instead of reading a decision list. Now
grouped by function.

**Legend.** ⛔ blocks work and cannot be deferred. ❓ is **not yet decided** and
is what the Phase-0 memo must ask for. Everything else is a standing
recommendation.

### 3.1 What is manipulated

| # | Decision | Position |
|---|---|---|
| D2 | **Arms** | **A0** capability ceiling — the defect presented as a fresh correction task, no retry framing; bounds what any feedback can achieve. **A1** measured-fact feedback (production `_SUPERVISOR_FEEDBACK_PROMPT`). **A2** generic rejection, no specifics. **A3** bare re-draw, **declared** as a determinism/noise floor at temperature 0, not as resampling (Tyen §4(d): they needed temperature 1 and up to 8 loops to force a different step). ⚠ **The warm-resample subset (temp > 0) is REQUIRED, not optional** — it carries the Olausson equal-budget comparison, which is the first thing a testing venue asks about A3. Best-of-k curves still come free from A3 repetitions. |
| D9 | **Placement — four levels** | **P0** artifact absent — *the production path; it ships, so it must be measured*. **P1** artifact in the user turn as an object under review. **P2** artifact as the model's own assistant turn. **P3** exploratory, P2 + correction marker, wording pinned per §14.5. |
| D1 | **Why user-turn framing is the reference — and the limit of that evidence** | SC-Bench's 64.5% blind spot compares an error *shown* in an assistant turn against the same error *shown* in a user turn; all eight of Olausson's repair prompts include the faulty artifact. ⚠ **That evidence supports P1 over P2. It says nothing about P0**, because no cited study withholds the artifact entirely — and P0 is what the system does. Earlier versions of this row used SC-Bench to justify P0; that was a misattribution. P0 is an *unstudied* cell, which is a contribution provided we do not claim literature support for it. P3 is **demoted to exploratory** by §13.4; the "closes 89.3% of the gap" reading is contradicted by Role Relabeling. |
| D9b ⛔ | **The design is not fully crossed, and must say so** | **A0 × P0 and A3 × P1 are structurally undefined.** A0 needs an artifact to correct; A3 stops being a bare re-draw the moment it is shown one. So A0 ∈ {P1, P2}, A3 ∈ {P0}, A1/A2 span all levels. B5's claim that "one function builds the message list from (arm, placement) so no cell is special-cased" is false as written. Declare the empty cells in the Method section or they read as unreported. |
| D10 ⛔ | **Tier 2 runs at P1; Tier 1 runs at P0** | Tier 2 cannot run at P0: the injected defect would never enter the model's context, so measured repair would be dominated by the model reproducing its own clean output and arm differences would reflect only how feedback text perturbs generation — not the estimand. Core, ablation, severity and C1 cells run at **P1**; P0 becomes a diagnostic cell. Tier 1 runs at **P0**, because there the defect genuinely was the model's own and the production retry genuinely is blind to it. Full argument: §6.1. |
| D8 ⛔ | **Constraint completeness** | The A1 feedback discloses obligations the stage prompts never state — verified against the code, all four rows (§13.1) — so A1 > A2 is not a specificity result without this control. Factor **C**: C0 production prompt, C1 constraint-complete prompt, crossed with A1/A2. C1 pre-registered and published verbatim. Two independent sources make it settled rather than optional (Huang §5; Kamoi Table 7 **Required** row). **This cell belongs in the conference core, not the journal** — deferring it breaks the very contrast such a paper would lead with. ⚠ But see D8c: it can no longer be a *test*. |
| D8b ❓ | **What base output does C1 use?** | **Unresolved; it forks the build.** C1 changes the *stage prompt*, so the clean pre-injection output would change under it too. Either (i) regenerate the base under C1 — clean identification, costs a full generation pass — or (ii) inject into a C0 base and vary only the retry prompt — cheap, but the manipulation is retry-only and must be described that way. **Recommendation: (ii)**, since D8c shows (i) buys clean identification of an effect that cannot be detected at any affordable size. Supervisor decision requested. |
| D8c ⛔ | **C1 is an estimate, not a test — the interaction is undetectable** | `scripts/analysis/power.py` §7: detecting a 6 pp interaction (constraint disclosure explaining half the A1−A2 gap) has power **0.12** at the planned 160/40 defects, **0.19** at 160/160, and **0.32** even at 320/320 — 2,560 trials. Report both gaps with CIs and pre-register the interpretation: *if the C1 gap CI includes zero while the C0 gap CI excludes it, that is suggestive, not conclusive.* Put the power figure in threats to validity. Kamoi's Required row is a **design** requirement — that prompt completeness is addressed — not a statistical one, so running the cell and publishing C1 satisfies it. Run C1 at 80 defects, not 40: half the CI width for double the calls. |

### 3.2 What is measured

| # | Decision | Position |
|---|---|---|
| D3 | **Success criterion (frozen before runs)** | Supervisor verdict on the retried output is `proceed`/`proceed_with_warning` **and** the injected defect is genuinely resolved. ⚠ **"The descriptor no longer fires" is NOT the criterion.** §13.5 shows why: a fabricated evidence ID swapped for a *different* fabricated-but-resolving ID stops the descriptor firing while the output got worse. **Score the replacement value.** Earlier versions of this row froze the wrong criterion. |
| D3b | **Outcome structure — corrected** | The original four classes were **not mutually exclusive** (`collateral` overlapped `repaired_clean`), so they could not be the multinomial D4 analysed them as. Outcome is now a **3-class multinomial** {`repaired`, `replaced`, `unrepaired`} **crossed with a binary collateral flag**. Collateral is a second dimension, not a fourth class. |
| D3c | **Collateral threshold — measured, not chosen** | `scripts/analysis/churn.py` measures what an *unperturbed* pipeline already churns, from the repetition sub-study (same 5 businesses, 5 runs, same seed, temperature 0, no injection, no feedback). **There is no single threshold** — the floors differ by an order of magnitude: pattern aspects p95 churn **0.07** (closed 7-value enum), pattern descriptions **0.33**, root causes **0.29**. ⚠ Strategy recommendation issues measure 37% churn, **but that figure is confounded** — repetition runs regenerate every stage, so strategy churn compounds reasoning churn, whereas a replay trial pins upstream from the dump. Conditioning on near-identical upstream gives **23%** (n=13 pairs). Use 23% for the strategy stage; collateral there is **weak, not unmeasurable**. Set per-item-class thresholds above these floors and cite the calibration. |
| D3d | **Exact-string matching is unusable for most items** | Same source: across identical runs, exact-match rates are **0.01** (pattern descriptions), **0.03** (root causes), **0.00** (recommendation issues). Those items are essentially never byte-identical between runs. The report-containment check relies on exact equality and only passes because the report agent copies from its own prompt payload within a single run. State this in the Method section before a referee finds it. |
| D6 | **Injection scope** | Reasoning, strategy, report stages — their defects are item-level. Analysis excluded for two reasons: its defects are distributional (contradiction *rate*), and its measurement needs `reviews_df`, which the dumps do not carry. ⚠ **Tier 1 covers only reasoning and strategy** — the bank holds 0 report-stage and 0 analysis-stage defects (§5) — so Tier 2 carries the stage comparison outright. |

### 3.3 How it is analysed

| # | Decision | Position |
|---|---|---|
| D4 | **Primary endpoint — confirmatory set** | **Exactly three confirmatory tests**, alpha controlled across them (Holm): (1) **A1 vs A2** — feedback content; (2) **A2 vs A3** — bare trigger; (3) the **A1/A0 ratio**. Everything else in §8 is **exploratory and labelled as such**. ⚠ The CI on the A1/A0 ratio must come from a **cluster bootstrap over defect blocks**, not the independent-sample delta method the earlier version specified — the arms are matched by design. |
| D4a | **Cochran's Q runs on a dichotomised outcome** | Q is a **binary** test and cannot take the multinomial of D3b. The earlier row asked for both in one sentence. Q is the omnibus over `repaired` vs not; the multinomial is reported descriptively and, if inference on it is wanted, via a separate model. |
| D4b ⛔ | **Tier-1 blocking is over clusters, not defects** | 11 usable defects sit in **5 business × stage cells**, one holding 4. Blocking on defect identity alone treats near-duplicates as independent blocks and re-narrows exactly the CIs blocking exists to widen. Nest repeated observations within cell. |
| D4c ⛔ | **Grid rebalanced — allocate by contrast difficulty** | The §6 grid gave A1 320 trials and the other arms 240 over only 5 businesses → **80 matched quadruples**, power **0.30**. But **A2-vs-A3 (28 pp) is already at 0.996 with 5 businesses**, so equal allocation overspends on the easy contrast. Allocate: **A1 and A2 at the full 160 defects, A3 at 40, A0 at 80.** |
| D4d | **Power — computed, and it constrains the design** | `scripts/analysis/power.py`; simulation-based because arms are matched within defect, reps nest inside (defect, arm), and Tier-1 defects cluster — closed-form McNemar assumes independent pairs and overstates everything. At the plan's own predicted **12 pp** effect: 8×5 r=2 → **0.30** (MDE 22 pp); 8×20 r=2 → **0.80** (MDE 12 pp); 8×20 r=3 → 0.93. **160 defects is a hard ceiling** (8 operators × the 20 Phase-A dumps), so once the sample is exhausted **r is the only lever**; reps and blocks buy power about equally here (8×10 r=4 ≈ 8×20 r=2 ≈ 0.81), contrary to the usual advice. ⚠ A **shared-occasion effect** (§14.1 requires all arms for one defect in one session, so they share that moment's serving stack) raises arm-to-arm correlation, cuts discordant pairs, and drops 8×20 r=2 from 0.81 to **0.75**. **Plan r=3 if 0.80 is the target.** |
| D4e | **Tier 1 supports no inference** | MDE ≈ **31 pp**, and the cluster bootstrap **over-rejects at 0.086** against a nominal 0.05 with 5 clusters (naive McNemar is conservative there at 0.026, but that is luck, not validity). Tier 1 is a realism anchor reported descriptively. Run no hypothesis test on it. |
| D4f | **Pre-register as estimation, not NHST** | Given the MDEs, report A1 − A2 as a **difference with a CI** (half-width ≈ 0.7 × MDE: ±8 pp at 160 defects, ±11 pp at 80). A null then *says something* — "3 pp, 95% CI [−5, 11]" excludes large effects — instead of being indistinguishable from insufficient power. This also makes D11b's threshold meaningful. |
| D4g | **The go/no-go is a pre-specified interim analysis** | §10's "Tier 1 → preliminary analysis → go/no-go" *is* an interim look. Declare it descriptive-only with no stopping rule on the confirmatory tests, or specify an alpha-spending function. |
| — | **Retained from the original D4** | Wilson CIs on all proportions; **never pool replayed-real with synthetic in a headline**; Tier 2 gives precision, Tier 1 gives realism; Just-style coupling licenses reading Tier-2 rates — **noting it covers only 4 of 8 operators** (§5). Publish whatever the sign is. |

### 3.4 Apparatus and provenance

| # | Decision | Position |
|---|---|---|
| D5 | **Models** | Hosted: `gemini-2.5-flash`, **pinned to a dated snapshot if the API exposes one** — recording drift after the fact is strictly worse than preventing it, and §14.1 only requires recording. Fallback **disabled** during trials (`LLM_DISABLE_FALLBACK=1`, built); a trial where fallback fired is discarded and logged. |
| D5b ❓ | **Local model — a placeholder, not a decision** | "One open-weights instruct model via the existing Ollama profile" does not support C7's reproducibility claim, which is the journal's strongest generalisation asset. **Pre-register model, parameter count, quantisation, seed and runtime version by name.** Supervisor input requested. |
| D5c | **No-injection control — downgraded** | The recorded clean Phase-A verdict is **not** a valid control: it was produced weeks earlier in a different serving epoch, which is precisely what §14.1 blocks against. Either re-run the clean condition **in-session as a fifth cell**, or report it as a historical reference value and stop calling it a control. |
| D12 ⛔ | **Downstream propagation is in scope, and blocks B7** | Moving it in gives the journal an actual claim — *defect-level repair does not equal pipeline-level improvement* (MAST App. J) — instead of five ablations. **B7 must persist the full retried stage output plus enough state to re-run downstream stages later**, not just facts and verdict. Nearly free on the first pass; a full re-run of ~1,400 trials to recover afterwards. |

### 3.5 Publication

| # | Decision | Position |
|---|---|---|
| D11 | **Number of papers** | Conference core and journal core are the same experiment, so **build and run first, then branch on the result**. Full analysis in `PUBLICATION_STRATEGY.md`. |
| D11b ❓ | **The branch threshold, quantified** | "A1 ≫ A2" is not a criterion. X must be **≥ the MDE**, or the split would rest on an effect the design cannot reliably detect. At 160 defects that is 12 pp. Proposed: **split iff the A1 − A2 point estimate ≥ 12 pp AND its 95% CI excludes zero.** Supervisor sign-off requested — note the threshold falls out of the design rather than being chosen after seeing data, which is what makes the pre-registration real. |
| D7 | **Venue** | **EMSE regular track for the journal vehicle** (§12). Conference vehicle open; ASE and the ESEM registered-report route are live options. ⚠ Every deadline cited in `PUBLICATION_STRATEGY.md` §8 is **unverified** — confirm against official CFPs. Ask the #1 chairs about an extended-version route while #1 is still under review. |

### 3.6 Threats this design does not remove

| # | Item | Position |
|---|---|---|
| D13 ❓ | **The defect-bank audit has no second rater** | §5 requires two-pass review with disagreements recorded. A solo researcher cannot be their own second rater, and κ computed by one person is not inter-rater agreement. ⚠ **An LLM is not a legitimate second rater here** — it wrote `defect_bank.py`, which *defines* the bank, so rating its own classifier's output reproduces the circularity the audit exists to break. **Better split:** *groundedness* is factual and should be **verified programmatically** (is the evidence ID actually absent? does the review actually lack the aspect?) — no rater needed; *meaningfulness* is judgment and needs the supervisor as rater 2, over a much smaller set. Reportable as: "groundedness verified programmatically; defect meaningfulness rated independently by two humans." Supervisor decision requested. |
| D14 | **A1 confounds *specific* with *correct*** | There is no specific-but-wrong feedback arm. Claim feedback **content** effects, not specificity effects; concede in limitations. |
| D15 | **One model, one provider, one pipeline, one domain** | Everything is `gemini-2.5-flash` on Yelp restaurant reviews across 20 workloads. "Is this a property of the method or of this model?" has no answer in the data. C7 (local runtime) is the cheapest partial fix. This is the objection that rules out a top-tier venue at current scale — state it rather than let a referee state it. |
| D16 | **The checks are shallow by design** | ID resolution, set membership, `difflib` ≥ 0.35, exact string containment. That determinism is the *thesis* — zero LLM calls, correct by construction — but a referee will read it as string matching and ask whether the defects are correspondingly shallow. Frame it as a deliberate trade, explicitly. |
| D17 | **"Repair" here means repair by regeneration** | The retried stage regenerates its whole output rather than editing the faulty artifact, so what is measured is *regenerate-under-measured-feedback*, not *fix-this-object*. P1 narrows the gap by putting the artifact in context; it does not close it. Say "repair by regeneration" — overclaiming "self-repair" summons the referee who knows the self-correction literature. |


### Phase-0 amendments after the Tier-A reading (2026-08-24)

Source: `..\Reading List\Tier_A\Tier_A_extraction.md` (all five papers read; the
extraction's blocks 4–5 and cross-paper synthesis are the basis). D1, D2 and D4
above already incorporate these; the rest are recorded here.

**Adopted**

1. **A1 vs A2 is promoted to the adjudicating contrast.** The literatures make
   opposite predictions: Olausson (feedback quality binds — human feedback lifted
   repair 33.3%→52.6%) predicts A1 ≫ A2; SC-Bench (a contentless "Wait" closes
   89.3% of the gap) predicts A2 ≈ A1. Our experiment decides between them —
   lead with that framing. MAS-FIRE Finding 5 adds a mechanism prediction:
   an authoritative but contentless rejection (A2) is the arm most likely to
   produce *replaced-by-a-different-defect* outcomes.
2. **D-real becomes a two-half defense.** Necessity from SC-Bench §3.1
   (injection *identifies the estimand*: on-policy defects conflate activation
   failure with capability limits — lift the argument's structure). Sufficiency
   from Just et al.: a coupling check — for each banked real defect, does the
   rule that fires on it also fire on ≥1 synthetic operator's output? Report the
   percentage, expect a residue, characterize it (their 17% analogue: defects
   where the stage's *whole reasoning* is wrong, not one citation). Plus the
   realism ladder (SC-Bench Table 4): synthetic → templated → replayed-real,
   with the effect ordering reported across tiers.
3. **Independent audit of the natural-defect bank.** A supervisor-flagged defect
   is defined by the detector, so validating operators against the bank alone is
   partly circular. Manually confirm each banked defect is genuinely ungrounded;
   two-pass review, disagreements recorded (Just et al.'s isolation discipline).
4. **Injection hygiene (MAS-FIRE):** freeze the O5–O7 insertion corpora to disk
   (LLM-generated content is otherwise non-reproducible across runs); log
   per-operator applicability so every rate has an explicit applicable-trials
   denominator (you cannot corrupt an evidence ID in an output that cites none);
   report an injection success rate.
5. **New confound to control: checkable items per stage output.** More citations
   = more opportunity both to receive an injected defect and to be caught. Hold
   it fixed across arms; report conditional on it, run-both-ways
   (Just et al.'s coverage-control presentation pattern).
6. **Model-class caveat for the writing phase.** SC-Bench's blind-spot magnitude
   collapses — sometimes reverses — for reasoning-class models. State what
   `gemini-2.5-flash` is; cite the *mechanism* (role attribution gates
   correction), never the 64.5% as if it transferred.

**Deferred (recorded, not scoped)**

- Truncate-and-regenerate arm (Tyen's operator — delete the flagged item,
  regenerate; nobody has compared it against feedback retry). One arm if weeks
  5–6 free.
- Specific-but-wrong feedback arm. A1 confounds *specific* with *correct* —
  expect a reviewer to ask; concede it in limitations if unrun.
- Cross-stage repair (SC-Bench §5 predicts routing the defect to the *next*
  agent beats re-running the same one — their "multi-agent architectures convert
  internal errors into external ones" sentence is also the related-work anchor
  for the hub topology). Future work.

**Corrections to this plan's own citations**

- SC-Bench is **COLM 2026**, single author (Ken Tsui) — not NeurIPS 2025 as
  listed below.
- MAS-FIRE is a **submission preprint** (ACM template placeholders); its
  abstract's ">40% of faults" figure has **no located derivation in its
  results** — cite its taxonomy and injection mechanisms, never that number.
  Check for a peer-reviewed version before submission.

---

## 4. Phase 1 — instrumentation and harness (~2–3 focused days)

All build items anchor to existing code; golden tests gate each one.

**Status 2026-08-24.** B1, B1b, B2 and B3 are built, plus the defect-bank
inventory §5 depends on. The B3 fidelity gate **passes**: `python
scripts/replay_stage.py --verify out_study` reproduces **135 recorded
`observations[].facts` exactly, 0 mismatches**, across all 45 observe-mode runs
and without touching the Yelp data. The 45 analysis-stage observations are
reported as *skipped*, not passed — they need `reviews_df` and are out of scope
(D6). Remaining: B4–B8.

| # | Item | Where / how |
|---|---|---|
| B1 | Token accounting per stage | **Smaller than billed — this is not a missing feature.** `BaseAgent.total_tokens_used` / `reset_token_usage()` exist and `eval/harness.py:68-91` already uses them correctly. `total_tokens` is null in all 45 study runs only because `scripts/run_study.py:177` hard-codes `total_tokens=None` under a comment claiming the codebase has no instrumentation. That comment is wrong. Copy the harness pattern; snapshot around each trial call. |
| B1b | Served-model provenance | Separate from B1 and easy to miss: `_call_llm` returns a bare `str`, so `resp.model` is discarded and **the served-model snapshot §14.1 requires cannot be recorded**. Change its return shape (or stash per-call metadata on the instance) *before* writing the runner — it is a base-class signature change touching all four agents. |
| B2 | Fallback control | New env flag (e.g. `LLM_DISABLE_FALLBACK=1`) consumed in `BaseAgent._call_llm`; a trial where fallback fired is discarded and logged. **Already proven de facto:** every conference dump's `_summary.json → run_config` shows `primary_model: gemini-2.5-flash, fallback_model: gemini-2.5-flash` — the study ran with fallback pinned equal to primary, so `OPENAI_FALLBACK_MODEL=gemini-2.5-flash` is a zero-code B2. Add the flag anyway, so a failover is *detected* rather than masked. |
| B3 | **Replay entry point** — `scripts/replay_stage.py` | **The dataset is not needed. Corrected 2026-08-24 (second review pass).** The three in-scope stages read only upstream *outputs*: `_measure_reasoning` needs `reasoning_output` + `analysis_results`; `_measure_strategy` needs `strategy_output` + `reasoning_output`; `_measure_report` needs `report_output` + `reasoning_output` + `strategy_output` + `business_name` + `len(analysis_results)`. `reviews_df` is read **only** by `_measure_analysis` (stars-vs-sentiment), and D6 excludes the analysis stage. Generation side is the same: `reasoning_node` / `strategy_node` / `report_node` rebuild their inputs purely from upstream dumps. So replay needs **no `loader`, no SQLite, no 5.34 GB review file, and no `MAX_REVIEW_SAMPLE=214`** — the four dump JSONs plus `_summary.json` are sufficient, and the study becomes runnable on a machine without the Yelp data. This removes most of the §11 replay-fidelity risk. **Golden test (kept, and now cheaper):** replaying every clean Phase-A dump must reproduce the recorded `observations[].facts` from `checkpoint.jsonl` exactly, with no seeded reload in the loop to drift. ⚠ **Trap:** do *not* route through `orchestrator_node`. `supervision.latest_stage` infers the stage by scanning backward from `report_output`, so a state holding all four dumps reports `report_agent` whichever stage you meant. Call `measure(stage, state)` / `decide(...)` with an explicit stage. |
| B4 | **Injection operators** — `scripts/inject_defects.py` | Table below. Deterministic given seed; each application records a ground-truth descriptor for scoring. **O5–O7 insertion content comes from a fixed corpus frozen to disk — generated once, never regenerated per run.** Log per-operator applicability (an operator with nothing to corrupt is recorded, not silently skipped) and an injection success rate. |
| B5 | Arms + placement | **Arms:** A0 = fresh-task correction framing (new prompt template, no retry language). A1 = production `_SUPERVISOR_FEEDBACK_PROMPT`. A2 = fixed generic-rejection string. A3 = plain re-call. **Placement is a four-level factor (D9), not two:** **P0** = defective output *absent* — the production path, and the default for Tier 1; **P1** = defective output in the **user** turn as an artifact under review — the default for Tier 2 (D10, §6.1); **P2** = defective output via a `prior_output` **assistant** turn; **P3** (exploratory) = P2 + correction marker, wording pinned per §14.5. Arm and placement are orthogonal in the implementation: one function builds the message list from (arm, placement) so no cell is special-cased. |
| B6 | Outcome scorer — `scripts/analysis/score_repair.py` | Classifies each trial into D3's taxonomy from (pre-injection output, injected output, retried output, descriptor). Pure Python, unit-tested. Emits per-operator applicable-trials denominators. ⚠ **Collateral must be redefined — the specified metric cannot discriminate.** "Any added/removed/altered pattern-or-recommendation beyond the injected one" assumes retry is an *edit*. It is not: the retried stage regenerates its whole output from upstream state (see B3/§6.1), so essentially every trial changes essentially every item and the collateral rate pins at ~100% in **all** arms. Score it instead as semantic set-overlap against the **pre-injection** output (or restrict scoring to the items the feedback explicitly named). This is §13.5's replacement-value problem one level up, and it needs the same kind of golden test before any trial runs. **Must score the replacement *value*, not the disappearance of the original defect** — a swapped-but-still-wrong ID or a differently-wrong frequency is `replaced`, not `repaired`. Golden test for this case required before any trial (§13.5). |
| B8 | **A1 template information-equivalence audit + C1 prompt variant** | Blocks all trials. Diff every supervisor feedback string against the stage system prompt; where the feedback discloses a constraint the prompt omits (all four checked cases do — §13.1), either fold it into a pre-registered constraint-complete prompt C1 or record the delta. Publish C1 verbatim in an appendix. |
| B7 | Batch runner — `scripts/run_injection_study.py` | Clone the `run_study.py` pattern: JSONL checkpoint with fsync, resume-by-skip, `--dry-run`, backoff on 429/503, `status_error` exclusion carried over verbatim. **Iteration order is `for defect: for arm: for repetition:` — never arm-outer.** All arms for one defect must execute contiguously in one session or the matched pairing is confounded with serving epoch (§14.1). Checkpoint granularity = defect, not trial. Record session id + served model snapshot per call; log the terminal supervisor verdict per trial (§14.4) and pre/post facts for **all** checks, not only the injected one (§14.6) — the latter is free, because `measure()` has no rule precedence and returns the entire measurement. ⚠ **Log `attempts_made` per trial and stratify or exclude on it.** `BaseAgent._run_with_retry` reacts to a JSON/schema failure by appending the model's own invalid output as an **assistant turn** plus a correction prompt. That silently converts the trial to a P2-like condition mid-flight, contaminating exactly the placement manipulation D9 measures — and it means **a trial is 1–3 LLM calls, not 1**, which every budget line in §6 currently assumes away. ⚠ **Resolve D12 before writing this runner.** If downstream propagation is in scope, the runner must persist the full retried stage output and enough state to re-run the *downstream* stages later — not just the facts and the verdict. Adding that to the record on the first pass is nearly free; recovering it afterwards means re-running every trial. |

**Operator catalog (B4), one per supervisor check class, parameterized from
observed defects:**

| Op | Check class it violates | Parameterization from real data |
|---|---|---|
| O1 evidence-ID corrupt | unresolvable evidence ID | drop 1 char from a real 22-char ID (the conference §3 motivating example — which finally pays off) |
| O2 evidence-ID fabricate | unresolvable evidence ID | well-formed ID absent from analysis output |
| O3 aspect misalign | misaligned aspect | swap `pattern.aspect` to an aspect its evidence lacks |
| O4 frequency inflate | statistic divergence | multiply by f ∈ {1.1, 1.5, 1.8} — brackets the observed 1.6–1.8× case and the 0.05 tolerance |
| O5 untraceable recommendation | traceability | replace `rec.issue` with an unrelated issue from a fixed pre-generated corpus |
| O6 invented root cause | report containment | insert a cause absent upstream |
| O7 invented recommendation | report containment | insert a rec absent upstream |
| O8 metadata mismatch | trusted metadata | perturb `business_name` / `sample_size` — ⚠ **ceiling operator, see below** |

**Operator-coverage notes (added 2026-08-24, second review pass).**

- **O6/O7 lost their only real counterpart** to the cascade exclusion (§5). The
  report-containment operators are now unvalidated against real data, and the
  report stage has no Tier-1 presence at all. Tier 2 is the only evidence for
  that stage; say so rather than implying the coupling check covers it.
- **O8 has no real counterpart and is a ceiling operator on both counts.** Zero
  natural instances were ever recorded (§5), so it contributes nothing to the
  coupling check; and `report_node` passes the correct `business_name` and
  `sample_size` *in the prompt payload*, so any retry copies them straight back
  at ~100% in every arm. It will contribute noise, not signal. Either drop it,
  or keep it explicitly as a **positive control** — an operator whose repair
  rate *should* be 1.0, useful for detecting a broken scorer — and say which.
- **O4 has no retry-level counterpart, but the richest natural sample in the
  data.** Frequency divergence never reaches the retry threshold, so it is
  absent from the Tier-1 bank — yet the study recorded **27
  `frequency_corrected` warn-level observations** across Phase A and the
  repetition runs. That is by far the largest natural-defect signal available
  and the only operator class with real observed parameterization. §11 currently
  lists the warn-level frequency sub-experiment as out-of-scope scope creep;
  **reconsider** — it is the cheapest realism evidence in the repository.
- **Report-stage containment is checked by exact string equality.**
  `_measure_report` compares `(cause, pattern)` and `(issue, action)` verbatim
  against upstream, so any legitimate rewording during a retry scores as
  *invented*. For O6/O7 this conflates *removed the invention* with *reproduced
  the upstream strings verbatim*. The scorer (B6) must separate the two, and the
  paper must say the check is exact-match.

---

## 5. Phase 2 — Tier 1: natural-defect replay

1. **Inventory first** — `scripts/analysis/defect_bank.py` scans
   `out_study/A/checkpoint.jsonl` + `out_study/R/rep*/A/checkpoint.jsonl` for
   retry-triggering observations.

   **Re-verified 2026-08-24 (second pass, superseding the first).** There are
   15 retry-triggering observations — 6 Phase A + 9 repetition, as recorded —
   but **three of them are Gemini 503 `status_error` retries, not groundedness
   defects**:

   ```
   A    | Scarpetta | reasoning_agent | Error code: 503 - high demand...
   A    | Scarpetta | report_agent    | Error code: 503 - high demand...
   rep1 | Scarpetta | reasoning_agent | Error code: 503 - high demand...
   ```

   Replaying those replays an API outage. A fourth entry is worse: the **only**
   report-stage defect in the bank is a **cascade of one of those 503s**.
   `rep1 / 2qVZiMB22YPC2HCM62Gnbw` has `reasoning.json` = `status: error`
   (503), strategy consequently emitting zero recommendations, and the report
   agent then inventing three root causes and three recommendations to fill the
   empty upstream — its first invented cause literally reads *"Upstream analysis
   did not provide detailed patterns..."*. That is degenerate-input containment,
   not repair of an ungrounded claim, and it must not be pooled with the rest.

   **The usable Tier-1 bank is 11, over two stages.**

   | Stage | Check class | Nearest operator | Usable instances |
   |---|---|---|---|
   | reasoning | missing evidence ID | O1 / O2 | 3 |
   | reasoning | misaligned aspect | O3 | 2 |
   | strategy | untraceable recommendation | O5 | 6 |
   | report | containment | O6 / O7 | **0** (1 cascade, reported separately) |
   | analysis | — | — | 0 |
   | **Total** | | | **11** |

   Reproduce with `python scripts/analysis/defect_bank.py`, which encodes every
   exclusion rule above and prints the cluster structure.

   ⚠ **Shape is much worse than the count.** Those 11 fall on **5 distinct
   business × stage cells** across 4 businesses — Izzo's/strategy alone
   contributes 4 and Nomzilla/reasoning 3, so the repetition study largely
   re-observed the same defects rather than finding new ones.

   Consequences, all of which must be stated rather than smoothed over:

   - **Tier 1 covers two stages, not four.** Report is n=0 and analysis is n=0.
     Any per-stage claim from Tier 1 is about reasoning and strategy only, and
     Tier 2 must carry the stage comparison outright — that is no longer a
     caution, it is the design.
   - **Effective independent units ≈ 5, not 15.** The matched analysis (§8)
     must block over ~5 clusters with repeated observations nested inside, or
     the CIs will still be too narrow after having correctly worried about
     exactly that. Do not treat the 11 as 11 exchangeable defects.
   - **The `< 10` escape hatch has effectively fired.** 11 clears 10 nominally;
     5 clusters does not clear its intent. Either raise repetitions to r=5, or
     accept Tier 1 as a realism anchor only and let Tier 2 carry every rate —
     the latter is the honest option and it is already the plan.

   ⚠ **This weakens the Just-style coupling argument further** (§13, D-real
   "sufficiency" half). Just et al. earned their 73% coupling figure on 357
   isolated real faults; a coupling check over 5 cells is descriptive, not
   inferential. Report it as descriptive, and let the **necessity** argument
   (SC-Bench §3.1 — injection is what identifies the estimand) plus the realism
   ladder carry the D-real defense. Promising a coupling result at this n and
   then reporting a ratio over 5 cells is the weakest move available.

   ⚠ **Half the operator catalog has no real counterpart.** Only **O1, O2, O3,
   O5** have a natural instance to be coupled against. **O4** (frequency) never
   reaches the retry threshold, **O6/O7** (report containment) lose their only
   instance to the cascade exclusion, and **O8** (metadata) has never occurred
   at all. Say which four operators the coupling check covers and which four are
   unvalidated — a reviewer who recomputes this will find it in ten minutes.
   See the operator-catalog notes in §4 for what to do about each.

   Bank entry fields (as emitted): `defect_id`, `source`, `business_id`,
   `business_name`, `stage`, `dump_dir`, `classes`, `operators`, `genuine`,
   `excluded_reason`, `cascade_of`, `usable`, `retry_feedback`, `facts`.
2. Design: every usable instance × arms {A0, A1, A2, A3} × r=3 → **132 trials**.
   ⚠ **Descriptive only — `scripts/analysis/power.py` puts Tier 1's MDE at
   ~31 pp and shows the cluster bootstrap over-rejecting at 0.086 against a
   nominal 0.05 with 5 clusters.** No hypothesis test may be run on Tier 1. The
   132 trials buy a realism anchor and per-class descriptive rates, nothing more;
   spend them knowing that, or cut r to 2 and spend the difference on Tier 2
   where it buys power.
   (not ~180), one LLM call each *when validation passes first time* — see the
   B7 note on the schema-correction loop, which makes a trial 1–3 calls. Only
   the retried stage is re-run; repair is judged at that stage by the same
   checks, and downstream re-runs are out of scope. Tier 1 runs at **P0**, the
   production placement (D9) — these defects really were the model's own and the
   production retry really is blind to them.
3. **Independent audit first**: manually confirm each banked defect is genuinely
   ungrounded (two-pass review, disagreements recorded) — the bank is defined by
   the detector, and the audit breaks that circularity. Then the **coupling
   check**: for each real defect, does its firing rule also fire on ≥1 synthetic
   operator output? Report the percentage (Just et al.'s 73% analogue).
4. Realism is unimpeachable: these are defects the model actually produced on
   real workloads, replayed with upstream compute already paid for.

## 6. Phase 3 — Tier 2: synthetic injection

Base material: the 20 Phase-A dumps (skip a business×class cell when that
class already occurs naturally there, or score around it).

### 6.1 BLOCKING — the Tier-2 core must run at P1, not at the production placement

**Decision D10. Corrected 2026-08-24 (second review pass); the previous core
grid could not have produced C4.**

In the production retry path the retried stage **never sees its own previous
output**. `nodes.py` rebuilds the stage input from upstream state and
`base_agent._with_feedback` appends only the feedback string:

```python
cleaned = [... for a in state["analysis_results"] if a["status"] == "success"]
output = reason_over_reviews(cleaned, business_id=..., feedback=feedback)
```

For **Tier 1** that is exactly right, and it is the estimand: *given a
description of what was wrong, does the production path regenerate a clean
output?* The defect really was the model's own, and the retry really is blind
to it.

For **Tier 2 it breaks the experiment.** The base material is a *clean* dump.
We corrupt it programmatically, then retry a stage that regenerates from the
same input that produced the clean output in the first place, with no sight of
the corruption. At temperature 0 the model reproduces something close to its
clean output and the scorer records `repaired`. Two consequences:

- **Repair goes to ceiling in every arm, A3 included.** A1 vs A2 vs A3
  collapses — and that contrast is the whole point of the study (§13.3).
- **A1 is no longer A1.** The feedback names evidence IDs and issues the model
  never wrote. That is not *specific* feedback, it is *specific and
  inapplicable* feedback — a different construct from production A1, so Tier 2
  would not be estimating the same quantity as Tier 1 even in principle.

**Therefore: the Tier-2 core, arm ablation, severity and D8 cells all run at
P1** (defective output supplied in the user turn as an artifact under review),
which is the cheapest placement that puts the injected defect in context. The
production-absent placement becomes a *diagnostic* cell rather than the core —
it should show ceiling, and if it does not, that is itself worth reporting.

Cost is neutral: the placement cell and the core cell swap roles.

### 6.1b Power (D4d) — the grid below is NOT yet powered for its own endpoint

`scripts/analysis/power.py`, simulation-based (matched arms, reps nested in
defect, Tier-1 defects clustered — closed-form McNemar would overstate all of
it). At the plan's own predicted effect, **A1 − A2 ≈ 12 pp** (A1 = 0.45 from
§14.2; A2 = 0.33 from §13.3's "A2 captures ~70% of A1's gain"):

| Design | Matched defects | Power | MDE @ 80% |
|---|---|---|---|
| **Arm ablation as specified (8 ops × 5 businesses, r=2)** | 40 | **0.30** | **22 pp** |
| 8 × 10, r=2 | 80 | 0.50 | 16 pp |
| 8 × 20, r=2 — **the whole sample** | 160 | 0.80 | 12 pp |
| 8 × 20, r=3 | 160 | 0.93 | — |
| Tier 1 (11 defects, 5 cells, r=3) | 11 | — | **31 pp** |

Four consequences:

1. **A2 vs A3 (28 pp) is already at 0.996 with 5 businesses.** Equal allocation
   across arms overspends on the easy contrast. Allocate by difficulty: A1 and
   A2 at the full 160 defects, A3 at 40, A0 at 80.
2. **160 defects is a hard ceiling** — 8 operators × the 20 Phase-A dumps. More
   blocks would need new Phase-A runs (a full pipeline each), so **r is the only
   lever left** once the sample is exhausted. Reps and blocks buy power about
   equally here (8×10 r=4 ≈ 8×20 r=2 ≈ 0.81), which is contrary to the usual
   advice and worth stating.
3. **A shared-occasion effect makes all of the above optimistic.** §14.1 requires
   all arms for one defect to run contiguously in one session, so they share the
   serving stack of that moment; that raises arm-to-arm correlation, cuts
   discordant pairs, and costs power. At occasion SD 1.0, 8 × 20 r=2 falls
   0.81 → 0.75. **Plan for r=3 if 0.80 is the target.**
4. **Tier 1 cannot support inference** — MDE ~31 pp, and the cluster bootstrap
   over-rejects at 0.086. Descriptive only (§5).

**Therefore: pre-register this as estimation, not NHST.** Report A1 − A2 with a
CI (half-width ≈ 0.7 × MDE: ±8 pp at 160 defects). A null then *says* something —
"3 pp, 95% CI [−5, 11]" excludes large effects — instead of being
indistinguishable from insufficient power.

### 6.2 Grid

| Grid | Placement | Trials |
|---|---|---|
| Core: 8 operators × 20 businesses × A1 × r=2 | **P1** | 320 |
| Arm ablation: 8 × 5 businesses × {A0, A2, A3} × r=2 | **P1** | 240 |
| Placement: 8 × 5 × A1 × {**P0** production-absent, **P2** assistant-turn} × r=2 | P0, P2 | 160 |
| Severity sweeps: O4 three levels + O1 two levels × 10 businesses × r=2 | P1 | ~100 |
| **D8 constraint-completeness (§13.2b): 8 × 5 × {A1,A2} × C1 prompt × r=2** | P1 | 160 |
| *(optional)* P3 exploratory cell: 8 × 5 × r=2 | P3 | 80 |
| **Total** | | **~980 core; ~1,060 with P3** |

P1 is measured by the core cell, so the placement row buys the other two levels
and the three-level contrast **P0 vs P1 vs P2** comes out whole. See D9 in §3
for why P0 has to be named.

Detection-side calibration (C6) is free: run `measure`/`decide` over every
injected output offline — above-threshold severities confirm ~100% detection
by construction; sub-threshold ones trace each check's detection curve.

Budget: ~24 s/stage-call (derived: 597.3 s mean run ÷ ~25 calls for a p90
business), so ~980 calls ≈ 6.5 h of pure inference; call it **3 nights**
unattended once 429/503 backoff is included
with backoff, using the checkpointed runner. Rate limits, not cost, binding —
same as the conference study.

## 7. Phase 4 (stretch) — local deterministic arm

Ollama profile already exists (`.env.local.example`). Do **not** replay
Gemini's natural defects through the local model (confounded); instead: run a
small local Phase A (20 businesses, observe) → harvest local natural defects →
replay locally; repeat the Tier-2 core grid locally (operators are
model-agnostic). Delivers: (i) bit-identity of A3 → Insight I3 confirmed in
its pure form, any A1 repair causally attributable to feedback content;
(ii) cross-model transfer; (iii) a fully reproducible headline number (public
model, public data, deterministic runtime) — a genuine selling point. Wall-clock
bound, ~2 nights; zero API cost.

## 8. Phase 5 — analysis

- Omnibus: **Cochran's Q** over the matched arms per defect — **on the
  dichotomised `repaired`/not outcome**, because Q is a binary test and cannot
  take the multinomial (D4a). Planned **exact-McNemar** contrasts A1-vs-A2
  (feedback content) and A2-vs-A3 (bare trigger); headline = **A1/A0 ratio**
  with a **cluster bootstrap CI over defect blocks** — *not* the
  independent-sample delta method an earlier version specified, since the arms
  are matched by design (D4). Absolute rates alongside; block on defect identity
  throughout. **Exactly three confirmatory tests under Holm; everything else in
  this section is exploratory and must be labelled so (D4).**
- ⚠ **Tier-1 blocking is over ~5 clusters, not 11 defects** (§5). The 11 usable
  instances sit in 5 business × stage cells, with up to 4 observations in one
  cell. Blocking on defect identity alone treats near-duplicates as independent
  blocks and re-narrows the CIs the blocking was introduced to widen. Nest
  repeated observations inside the cell, or report the Tier-1 rate as a
  descriptive count with the cluster structure printed next to it. Decide which
  before running, not after seeing the width.
- Outcome reported as a **3-class multinomial** {`repaired`, `replaced`,
  `unrepaired`} **crossed with a binary collateral flag** — the original four
  classes were not mutually exclusive (`collateral` overlapped `repaired_clean`)
  and so could not be a multinomial at all (D3b). Plus the two-stage
  chain *did the output change at all → did the targeted defect resolve*
  (MAS-FIRE's O/L decomposition; global-success S stays out of scope).
- Control the **checkable-items-per-output** confound: hold fixed across arms,
  report conditional on it, run-both-ways.
- Stratify by defect origin (replayed-real vs synthetic) and stage; never pool
  in a headline.
- Best-of-k curves (k = 1..3) from A3 reps vs A1 single-shot, **cost-adjusted
  in tokens** (B1 makes this possible for the first time).
- Per-class repair rates; pre-registered hypothesis: referential (O1/O2) >
  structural (O3, O6–O8) > semantic (O5). **Expected single-retry repair rate
  ≈45%** (Arimbur's assertion-error class), not ~70% — power calculation runs
  off 45% (§14.2).
- Report the **A3 share of A1 by stratum**, not pooled — Self-Edit predicts the
  A1−A3 gap widens on harder defects (§14.2).
- **Trigger rate** reported alongside injection success rate; state whether
  never-flagged defects are dropped or counted `unrepaired` (§14.3).
- Placement effect (C5) — stage-level blind-spot test over **four** levels
  (D9): pre-registered **P1 ≫ P3 ≈ P2**, with **P0 (production) reported
  separately** rather than folded into the ordering. P0 is not a weaker P1: the
  model never sees the artifact at all, so it is a different mechanism —
  regenerate-from-description, not correct-an-artifact. In Tier 2 the P0 cell
  is a ceiling diagnostic (§6.1); in Tier 1 it is the production estimand.
- **Placement × arm interaction**: predicted A1−A2 larger at P2 than at P1; report it, do not average over placement (§13.6).
- **A0 call-count disclosure** — state calls per arm; A0 is a ceiling, not a cost-matched competitor (Huang §4).
- Collateral rate per arm — does feedback cause *less* collateral than a
  re-draw? Plausible and novel either way. **Only under the redefined metric
  (B6):** the original "anything changed beyond the injected item" definition
  saturates at ~100% in every arm because retry regenerates rather than edits,
  and would report a null that is an artefact of the measure.
- Severity → detection curves per check (C6).
- Everything with denominators visible; no population claims.

## 9. Phase 6 — writing

- New Method subsections (replay, operators, arms, outcome taxonomy) and a new
  Results section; conference §6.3 becomes its motivation.
- Related Work gains three threads: fault injection in MAS (MAS-FIRE,
  AgentChaos, AgenTracer, MAST mapping table), self-correction measurement
  (SC-Bench, Illusion, Tyen, Huang, Kamoi), repair methodology (Olausson,
  Self-Debug, APR realism). Runtime-enforcement positioning updated (AgentSpec,
  Reason-Less-Verify-More).
- Reconcile I3 vs instability (deterministic vs hosted runtime — C7).
- The §3 dropped-character example ↔ §6.6 reconciliation from `NEXT_SESSION.md`
  resolves itself: O1 makes that example an actually-measured condition.
- Rewrite contributions and abstract around C4–C6(±C7).
- `/ars-citation-check` over the grown bib (~35–40 entries), Table 1 cell by
  cell as before.

## 10. Timeline (part-time, ~8 weeks)

Weeks 1 and part of 2 are **done** — Tier A and Tier B are read (14/14 incl.
Tier C debt outstanding) and the amendments are folded in. Revised:

| Week | Work | Status |
|---|---|---|
| 1 | Tier-A reading; design decisions D1–D7 | ✅ done 2026-08-24 |
| 1 | Tier-B reading (9 papers, 3 sittings) | ✅ done 2026-08-24 |
| 2 | **Phase-0 memo → supervisor sign-off on D1–D17.** Seven block work (⛔ in §3): D8, D8c, D9b, D10, D4b, D4c, D12. Four are open questions for the supervisor (❓): **D8b** C1 base output · **D5b** local model identity · **D11b** split threshold · **D13** who audits the defect bank | ⬜ next |
| 2 | B1/B1b/B2 instrumentation; B3 replay entry point; defect-bank inventory | ✅ done 2026-08-24 |
| 2–3 | Build B4 (operators), B5 (arms × placement), B6 (scorer), B7 (runner), B8 (C1 audit) + golden tests incl. the §13.5 replacement-value test | ⬜ |
| 3 | Tier 1 runs (**132** trials, P0) + preliminary analysis → go/no-go | ⬜ |
| 4 | Tier 2 grids (~980 calls, 3 nights) + analysis | ⬜ |
| 5 | (stretch) local deterministic arm — now higher value, see §14.1 | ⬜ |
| 6–7 | Writing; stats hardening; related-work integration; Tier-C skim | ⬜ |
| 8 | `/ars-citation-check`; internal review; supervisor pass; submit | ⬜ |

## 11. Risks and pre-commitments

- **Pre-commit to the negative result.** If A1 ≈ A3 (feedback adds nothing over
  a re-draw), that is a publishable finding against the self-correction
  literature's assumptions — but only if the three-arm design was declared up
  front. Put it in the Phase-0 memo.
- **Model deprecation.** `gemini-2.5-flash` must still exist when trials run
  (the conference `gemini-2.5-pro` 404 is the precedent). Run hosted trials
  early; the local arm is the hedge.
- **Replay fidelity.** The B3 golden test is a hard gate: if reconstructed
  facts don't match recorded facts exactly, stop and fix before any trial.
  **Downgraded from the largest build risk to a routine test** now that replay
  needs no seeded reload of the review data (B3) — the only moving part left is
  the dump-to-state mapping.
- **Placement contamination via the schema-correction loop.** A trial whose
  first call fails JSON/schema validation is silently re-issued with the
  model's own invalid output in an **assistant turn** — a P2-like condition
  inside what was meant to be a P0 or P1 trial. Log `attempts_made`, and decide
  before running whether such trials are excluded or analysed separately (B7).
- **Trial cost is 1–3 LLM calls, not 1.** Same cause. The §6 budget and the
  Olausson-style cost-adjusted comparison both assume one call per trial; with
  B1 in place the *actual* token cost is measured, so report that rather than
  the nominal call count.
- **Contamination.** Fallback-served calls: discard and log (B2). Never mix.
- **Scope creep.** Judge re-runs on repaired reports and the warn-level
  frequency sub-experiment are out of scope unless weeks 5–6 are free.
  ⚠ **Downstream propagation is no longer on this list — see D12.** If the
  repair result splits off to a conference paper, propagation is one of only two
  items left that can carry a journal thesis, so it moves in scope. **Its
  logging requirements block B7**: capture what it needs on the first pass
  rather than re-running ~980 trials for it later.
- **The supervisor-is-never-wrong claim is load-bearing.** The A1-favourable
  reading of MAS-FIRE's Finding 5 (compliance helps when the directive is
  correct) holds only if the supervisor's facts are correct by construction —
  that is a claim about the rules, argue it explicitly.
- **A1 confounds *specific* with *correct*.** Without a specific-but-wrong
  feedback arm, claim feedback *content* effects, not specificity effects;
  concede in limitations.
- **Model class.** If `gemini-2.5-flash` counts as a reasoning-class model,
  SC-Bench's blind-spot magnitude largely does not transfer — cite mechanism,
  not magnitude.
- **Environment.** All the `NEXT_SESSION.md` §8 traps still apply (Unicode
  path split, UTF-8 console reconfigure in every new script, background long
  runs, checkpoint everything).

## 12. Venue (decision D7)

> **Scope note added 2026-08-24.** This section assumed a **single** output.
> Conference paper #1 is now **submitted and under review**, and the repair
> study may ship as its own conference paper first (D11). The analysis below
> still stands **for the journal vehicle**; for the conference vehicle, the
> split decision, and the constraints that follow from #1 being in review, see
> **`PUBLICATION_STRATEGY.md`**. Two things that section gets wrong by omission:
> **ASE** belongs in the table (AgentChaos is ASE 2026, peer-reviewed — direct
> precedent), and the **ESEM Registered Reports** route in §12.4 is stronger
> than its one-line treatment there suggests.

**Recommendation: Empirical Software Engineering (EMSE), Springer — regular
track, not a special issue.**

### 12.1 The direction problem, and why it rules out the tempting special issues

The work is **SE4AI** — software-engineering method (runtime verification, fault
injection, mutation-style validation) applied *to* an LLM system. Almost every
currently open LLM special issue in SE journals runs the other direction,
**AI4SE** — agents *doing* software engineering work. Checked 2026-08-24:

| Venue / special issue | Deadline | Verdict |
|---|---|---|
| EMSE — *Agentic Software Engineering: The Rise of AI Teammates* | 2026-09-28 | **No.** AI teammates doing SE tasks. Our agents analyse restaurant reviews. Also ~5 weeks out vs. an 8-week plan. |
| EMSE — *Advancing Software Engineering with LLMs* | 2025-11-28 | Closed, and AI4SE anyway. |
| EMSE — *Software Reliability Engineering* (covers "reliability of LLMs") | 2025-03-01 | **Closed.** Would have been the ideal fit. |
| EMSE — *Software Security Testing (SECUTE)* | 2026-11-30 | No — security testing, not groundedness. |
| JSS — *Reliable and Secure LLMs for Software Engineering* (rolling) | rolling | Borderline-no: scoped to "LLM-powered code generators and other AI-driven tools in software engineering". Our pipeline is neither. |

Submitting to an AI4SE special issue invites the one-line desk rejection *"this
is not software engineering."* The regular track has no such framing trap: SE4AI
is squarely in EMSE's remit, and EMSE published an empirical study of testing
practices in open-source AI agent frameworks in 2026 — direct precedent for
agent-reliability empirical work with no SE application domain.

### 12.2 Why EMSE specifically

- **Methodological culture matches.** Explicit threats to validity, visible
  denominators, honest null results, naming our own circularity — EMSE reviewers
  reward exactly this. ML venues are indifferent to it.
- **The methods are native SE.** Fault injection and the Just et al.
  mutants-vs-real-faults validation protocol are SE methodology; the
  MAS-FIRE / AgentChaos conversation sits in this literature.
- **Scale is acceptable here.** One system, 20 workloads and ~800 injection
  trials reads as a credible empirical case study in EMSE. It reads as thin in
  TOSEM/TSE.
- Springer, Q1, and consistent with the LNCS toolchain already in use.

Framing sentence for the intro: *LLM-based multi-agent pipelines are increasingly
shipped as software components; we study how to verify their outputs at runtime.
The testbed is a review-analysis pipeline, chosen because it exhibits the
derivability property — the contribution is architectural and domain-independent.*

### 12.3 Check this before anything else

Two questions that can outrank the whole table above:

1. **Does the conference offer an extended-version route?** Many Springer
   conferences invite selected papers to an affiliated journal special issue.
   That is the cheapest possible path and it is worth one email to the chairs.
2. **The 30% rule.** Journal extensions of conference papers normally require
   ~30% new material and a declaration citing the conference version. The
   injection study clears that comfortably — but the declaration is mandatory,
   not optional. Self-plagiarism complaints usually start here.

### 12.4 Alternatives, ranked

| Venue | When to prefer it |
|---|---|
| **JSS** or **IST** (Elsevier) | Faster turnaround than EMSE, more tolerant of single-system studies. Sensible if a first-round EMSE rejection would cost too much time. |
| **TMLR** | If the SE framing feels forced, or the headline result is null. Judged on correctness and interest rather than novelty or SOTA; explicitly welcomes negative results. Downside: no impact factor, which may matter for institutional credit. |
| **ACM TOSEM / IEEE TSE** | Only after a second system or second provider is added. At current scale the generalisability objection is fatal, and cycles run 12–18 months. |
| **ESEM Registered Reports track** | Strategically strong: submit the *protocol* before running, get design review exactly when it is useful, and secure in-principle acceptance that survives a null A1≈A3 result. Check the current cycle's dates — this changes the timeline in §10, so decide before week 2. |

## 13. Tier-B amendments (2026-08-24)

Source: `..\Reading List\Tier_B\related_work_tierB_triad.md` — Self-Debug (Chen
et al., ICLR 2024), Huang et al. (ICLR 2024), Role Relabeling (Chen et al.,
arXiv 2606.05976v2). Six of nine Tier-B papers remain unread; **all of group
B-III is outstanding, including AutoInject, which gates the operator catalog.**

### 13.1 CONFIRMED CONFOUND — the A1 feedback teaches constraints the stage prompts never gave

Huang et al. §5: a measured self-correction gain can be an artefact of an
under-specified *initial* prompt. Their demonstration — moving the missing
instruction into the initial prompt raised the baseline above what
self-correction reached, and applying correction on top then *reduced*
performance (Table 8).

**Checked against this repo on 2026-08-24. The attack lands.** Comparing
`supervision.py` retry feedback against the stage system prompts:

| Constraint asserted by A1 feedback | Stated in the stage prompt? |
|---|---|
| Evidence IDs must resolve against the analysis output | **No** — `reasoning_agent` asks only for "list of review_ids that support this pattern" |
| Evidence reviews must carry the pattern's aspect | **No** — aspect alignment is never stated as an obligation |
| Recommendation issues must trace to an upstream pattern or root cause | **No** — `strategy_agent` asks only for "the underlying problem being addressed" |
| The report must only restate upstream outputs | **No** — `report_agent` asks for "root causes" and "recommendations" with no containment rule; the feedback states the rule outright |

So A1 does not merely *report a failure*; it *discloses a constraint the model
was never given*. As frozen, an A1 > A2 result is not interpretable as feedback
specificity, because A2 withholds both the specifics and the constraint.

**This is a frozen-decision problem, not a writing problem.** Resolve before any
trial — see D8.

### 13.2 New decision D8 — constraint-completeness factor

| Option | What it does | Cost | Assessment |
|---|---|---|---|
| **(a) Fold constraints into the stage prompts and re-run everything** | Huang's own prescription; A1 becomes a pure failure report | Changes the system under test relative to the conference paper; defect incidence would shift | Cleanest identification, highest cost, breaks continuity with published numbers |
| **(b) Add a constraint-completeness factor C** — C0 = production prompt, C1 = prompt with all supervisor obligations stated upfront — crossed with A1/A2 on a subset | Measures the confound instead of removing it | ~+80–120 calls on a Tier-2 subset | **Recommended.** Turns a reviewer attack into a reported result: if A1−A2 shrinks under C1 the difference was completeness; if it persists it is specificity |
| **(c) Report the confound and reframe** | A1−A2 becomes "specificity inclusive of constraint disclosure" | Free | Honest but weakens the headline; the adjudicating contrast stops being clean |

Recommendation **(b)**, with the C1 prompt text pre-registered and published
verbatim in an appendix. Whichever is chosen, the paper must carry Huang's
information-equivalence statement — the extraction supplies a drop-in template
for threats to validity.

### 13.3 Pre-registered predictions (record before running)

The Tier-B triad reconciles into a sharper prediction than the plan carried, and
it changes which literature says what:

- **Self-Debug is evidence for the activation hypothesis, not the feedback-quality
  hypothesis it is usually cited for.** Computed from its Tables 2b/2c,
  A2 (Simple) captures a median **70%** of A1's (UT) gain across seven
  model × benchmark settings (range 31–85%), with median A1−A2 ≈ **1.6 points**.
- **The real disagreement is about the trigger, not the content.** Huang's
  oracle-*stopped* condition is content-free and gains 8.4 points on GSM8K;
  removing the trigger from Self-Debug's Simple condition drops MBPP/Codex to
  57.6 against a 61.4 baseline. Both literatures agree on A0, A1 and A3 and
  disagree **only on A2** — exactly where the adjudicating contrast sits. State
  this explicitly; it is the cleanest justification for the experiment.

| Arm | Prediction | Basis |
|---|---|---|
| A0 ceiling | High — neither literature disputes the underlying capability | Huang §3.3 is a *judging* claim, not a fixing claim |
| A1 measured fact | High | Self-Debug UT rows; Huang §6 endorses valid external feedback |
| A2 generic rejection | **≈70% of A1's gain**, provided the trigger is trustworthy | Self-Debug Simple rows; Huang oracle-stopped rows |
| A3 bare re-draw | Near zero or negative | Self-Debug Table 3b; Huang intrinsic rows |
| Placement | **P1 ≫ P3 ≈ P2**, with P3 − P2 ≈ 7 pp and likely non-significant | Role Relabeling §4.3 duplication control (+6.7 pp, p = 0.26) |

### 13.4 P3 is demoted — the correction marker is contradicted

The plan added P3 (assistant turn + correction marker) on SC-Bench's "Wait"
result (89.3% blind-spot reduction). Role Relabeling contradicts that reading
directly: `L_user_neutral` matches or exceeds `L_user_wait` in most rows of its
Table 2, and §5.2 states the position outright — Tsui "reads 'Wait' as a
correction trigger; we show the trigger is incidental and the carrier role
primary."

P3 therefore combines two ingredients that paper shows do not carry the effect.
**Keep P3 but demote it to exploratory**, with the null pre-registered above: the
P3 cell is now a direct test of SC-Bench versus Role Relabeling, which is
informative either way, but it should not consume a third of the placement power
budget on an expected-large effect it is unlikely to show.

**Do not import Role Relabeling's effect sizes as power assumptions.** Their
`L_memory` (system role) beat `L_user_neutral` on math, which they attribute to
arithmetic being out-of-genre for a user turn. Schema-validated structured
objects are out-of-genre in the same way, so P1's advantage is likely
*attenuated* for this artefact type. [Optional, if a fourth placement level is
ever affordable: a system-role/`<memory>`-style level is the one their data
favours for out-of-genre content.]

### 13.5 Outcome-coding validity — a real defect in B6 as specified

Role Relabeling App. A.4, Llama-70B math: `L_memory` has the **highest** strict
correction rate (86.7%) and the **lowest** final-answer correctness (56.7%,
paired ∆ = −13.3 pp); `L_tool` inverts it (strict 3.3%, final 86.7%). Their
explanation: an agent that explicitly commits to a replacement value sometimes
locks in a wrong one, whereas silent re-derivation is free to re-roll.

**Consequence:** if `repaired` is coded as "the originally-failing check no
longer fires", a trial where the model swapped a fabricated evidence ID for a
*different* fabricated-but-resolving ID, or replaced an inflated frequency with a
differently-wrong one, scores as repaired while the output got worse. B6 must
score the **replacement value**, not the disappearance of the original defect.
Add a golden test constructed from exactly this case before any trial runs.

### 13.6 Analysis additions

- **Placement × arm interaction.** Reading Huang's prompt-variant results
  against Role Relabeling's paraphrase robustness: wording is the only lever when
  there is no role handle and stops mattering once there is one. Prediction:
  **A1's advantage over A2 is larger at P2 than at P1.** The design can detect
  this; the analysis plan must report it rather than averaging over placement.
- **A0 call-count disclosure.** Huang §4 requires cost-matched baselines. A0 is
  plausibly one call against the retry arms' two. A0 is a ceiling, not a
  competitor, so this is framing rather than validity — but state the call counts
  explicitly or a reviewer holding §4 will read the ceiling as inflated.
- **Collateral damage now has three-source support** and no dissent: Huang
  (8.8% correct→incorrect on 1,319 items), Self-Debug (MBPP/Codex 57.6 vs 61.4
  baseline once execution is removed), Role Relabeling (−13.3 pp final-answer
  correctness at the highest strict correction rate). Worth one sentence noting
  the convergence.

### 13.7 Citation corrections

- **The "Self-Correction Illusion" entry in §2 is wrong.** Actual title:
  *Role Relabeling Gates Explicit Error Flagging in Large Language Models*,
  Chen, Su, Lin, Li, Chiang, arXiv:2606.05976**v2**, 31 July 2026. Unrefereed —
  no venue line, no acceptance note. The plan's earlier description ("replicates
  the blind spot across 7 model families") is also inaccurate: it is 9 models ×
  3 domains yielding **12 model–domain combinations**, n = 30 paired tasks each,
  and it *reinterprets* rather than replicates SC-Bench.
- **Two distinct first authors surnamed Chen** — Xinyun Chen (Self-Debug, 2024,
  also second author of Huang et al.) and Chen et al. (Role Relabeling, 2026).
  Disambiguate in the bib before `/ars-citation-check`.
- Both Self-Debug and Huang et al. are **ICLR 2024**; the plan listed Self-Debug
  as "2023".

### 13.8 Citation economy

The extraction recommends keeping Self-Debug and Role Relabeling and reducing
Huang to a single thread sentence plus a threats-to-validity citation — Huang's
§5 (prompt completeness) and §4 (cost matching) arguments must be made regardless,
and making them uncited invites the assumption they were not known. Adopt that:
full treatment for Self-Debug and Role Relabeling, one sentence plus two
methodological citations for Huang.

---

## 14. Group B-III amendments (2026-08-24)

Source: `..\Reading List\Tier_B\related_work_B-III.md` — Self-Edit (Zhang et al.,
ACL 2023), Kamoi et al. (TACL 2024), AutoInject/faulty-agents (Huang et al.,
ICML 2025), Arimbur (preprint), AgentChaos (Tan et al., **ASE 2026**), MAST
(Cemri et al., NeurIPS 2025). Tier B is now complete: 9/9 read.

Four challenge hits. **14.1 is the one that can invalidate the primary endpoint
and it is a runner-scheduling fix, not a redesign.**

### 14.1 BLOCKING REQUIREMENT — all arms for one defect must run in one session

Arimbur §V.H documents that temperature 0 does **not** give run-to-run
determinism on a hosted API: identical prompt and model returned R0 pass rates of
84.1%, 82.9% and 81.1% across three sessions, and §VIII notes providers "may
serve quantized or otherwise optimized model variants" without notice.

The matched analysis (Cochran's Q, exact McNemar, blocking on defect identity)
assumes the defect is the only blocking factor. If served weights drift between
sessions and the runner batches **by arm**, then arm is confounded with serving
epoch and the pairing is broken.

**Requirement, added to B7:** the injection runner must iterate
`for defect: for arm: for repetition:` — never `for arm: for defect:`. All arms
for one defect execute contiguously in a single session, and the runner records a
session identifier plus the served model snapshot per call. Checkpoint
granularity becomes the *defect*, not the trial, so a resumed batch cannot split
one defect's arms across sessions.

Also report, per §VIII: serving path (hosted vs self-hosted), provider, model
snapshot string, and whether all arms for a defect shared a session. The
extraction supplies a drop-in threats-to-validity block.

**Bearing on the conference paper's 20% figure.** Arimbur offers an alternative
reading of the published recurrence rate — serving-stack drift rather than a
property of the pipeline. The conference paper already concedes that temperature 0
"constrains but does not eliminate non-determinism in a hosted API", so the
finding stands; but the journal version should own the alternative explicitly in
one sentence rather than let a referee introduce it. **This materially raises the
value of the C7 local-runtime arm** (§7): on a deterministic local runtime the
two explanations separate, which no amount of hosted-API work can do.

### 14.2 Expected repair rate is ~45%, not ~70% — the power calculation changes

Arimbur §V.E, repair success by error type: name errors ~77%, syntax ~66%,
**assertion errors ~45%**. Assertion errors are "code runs without crashing but
produces incorrect output" (§III.C) — the direct analogue of a schema-valid but
ungrounded claim, and the hardest class measured.

Self-Edit supplies the complementary result: the no-comment ablation (the A3
analogue) collapses as instance difficulty rises — A3 captures 70% of A1 on
APPS-dev pass@1 but **0%** on APPS-test pass@10 (Table 7).

**Pre-register an expected single-retry repair rate near 45%, not the ~70%
headline**, and re-derive the trial counts against it. [INFERENCE] Also consider
reporting the A3 share of A1 **by stratum** rather than pooled — Self-Edit's
monotone collapse predicts the A1−A3 gap widens on harder defects.

### 14.3 Trigger verification — a denominator decision, and an SE reviewer will ask

AgentChaos §4.4 discards tasks where the configured fault never fired: "Including
such untriggered tasks in the evaluation would mix faulted and unfaulted results,
making the system appear more robust than it actually is."

Your injected defect is present by construction, but a defect the **supervisor
does not flag** fires no retry and therefore yields no arm comparison. Decide and
state which: dropped from the denominator (AgentChaos's choice), or counted as
`unrepaired`. The two give materially different rates. Report an injection
trigger rate alongside the injection success rate (§13, B4).

### 14.4 Log the run-level verdict — free, and it pre-empts an overclaim

MAST Appendix J (Table 7): verification failure modes appear frequently in
*successful* runs — FM-3.3 in 20.0% of successful ChatDev runs against 25.0% of
failed ones. Defect presence and run outcome are only loosely coupled.

Consequence: `repaired` does not imply the run became good, and `unrepaired` does
not imply it became bad. Two actions, neither a redesign:

1. State early and explicitly that the outcome unit is **defect-level, not
   run-level**, and that run-level utility is out of scope.
2. **Log the terminal supervisor verdict per trial anyway** — it costs nothing and
   is already computed. If A1 repairs more defects without shifting the run-level
   verdict distribution, that is a finding (and the one MAST predicts), not a
   failure. Not logging it means being unable to answer the question when asked.

### 14.5 P3 marker wording audit — a marker can suppress detection

Huang et al. (ICML 2025) §4.5, Fig. 6b: a "distraction comment" asserting a bug
had been corrected caused **all six** evaluated systems to accept code they had
otherwise detected as faulty. Pair with Role Relabeling's trust-framing result
(§13.4 source: adoption 3.3% → 70.0% under one "treat as truth" sentence).

Two independent papers now agree that assertions *about* defective content
suppress scrutiny. **Pin the P3 marker wording before running:** a rejection cue
("the following was rejected by the supervisor") is safe; a completion cue
("corrected output follows") reproduces the failure mode above and would make P3
measure something other than intended. The current placeholder is "Wait", which
reads as hesitation rather than assertion — probably safe, but specify it
verbatim in the pre-registration.

### 14.6 Double Checking — a fifth outcome that the four classes cannot represent

Huang et al. §4.2 report injected faults sometimes *improving* performance (up to
+12.1% on MAD), via "Double Checking" — an obvious injected error prompts a
correction pass that also repairs *pre-existing* faults — and "Divergent
Thinking".

Applies asymmetrically across the two tiers, and the plan must say which:

- **Tier 2 (synthetic, applied to clean outputs):** void by construction. No
  pre-existing defect exists to be incidentally fixed. State this.
- **Tier 1 (replayed real defects):** **live.** A Phase-A run carrying one
  retry-triggering defect may also carry latent warn-level defects (low-rate
  contradictions, sub-tolerance statistic divergences). A retry could repair
  those too. Log pre- and post-retry supervisor facts for *all* checks, not only
  the injected one — then the incidental-repair count is recoverable without a
  fifth class.

### 14.7 Kamoi independently confirms D8, and adds a pre-specification deadline

The Kamoi checklist (Table 7) contains a **Required** row for RQ2: *"using
external tools or knowledge to improve initial response generation as much as
possible"*, and a Required row for RQ1/RQ2 on *"sufficiently strong prompts for
generating initial responses"*. Table 4 names Self-Refine as failing the
analogous requirement.

This is Huang et al. §5 (§13.1) reached from a different direction, by a TACL
survey, as a formal checklist item. **D8 now has two independent sources and
should be treated as settled rather than optional.**

New, and time-sensitive: **Table 8's negative-results checklist becomes live if
A1 ≈ A2**, and its Required row is "using sufficiently strong prompts for
self-correction". **Pre-specify the A1 template and document its derivation from
the supervisor's output schema now**, before any result is seen — otherwise the
strength defence is post hoc and reads as such.

Also from Kamoi, free wins to state explicitly:

- **Framework category: RQ2, realistic, fair-asymmetric, external non-LLM
  verifier.** The legitimising quote is §3.2's interpreter analogy —
  "self-correction with code interpreters is not intrinsic but fair because we
  cannot easily use code interpreters to directly improve the initial response
  generation." Your supervisor cannot run before the stage output exists, so the
  analogy holds exactly.
- **"Not using oracle information": PASS.** Say so explicitly — reviewers will
  assume otherwise given the phrase "measured fact".
- Do **not** cite Kamoi as evidence that self-correction fails; its claim is
  conditional on prompted-LLM feedback in general tasks, and it explicitly exempts
  settings with a reliable external tool. Cite the *checklist*, not the verdict.

### 14.8 Framing wins from AgentChaos (ASE 2026 — peer-reviewed, and your venue's house journal)

- **Diagnosis accuracy is the argument for a deterministic supervisor.** §5.4:
  rule-based diagnosis 52.45% (type) / 55.5% (step); LLM-based 47.25% / 53.52%;
  the most damaging fault type is diagnosed at 4.3% by rules. The literature
  measures at ~50% the capability your supervisor supplies for free and exactly.
  **One sentence in the introduction, with these numbers.**
- **Your four classes refine an ASE-published scheme rather than inventing one.**
  Their aborted/reported/silent classification collapses `repaired` and
  `replaced` into a single *silent* class worth 21.82%–65.71% of failures
  (Table 6). Cite the refinement; the extraction supplies drop-in text.
- **Stage stratification is load-bearing, not caution.** Injection position in
  *pipeline* architectures swings Δpass@1 from −4.84% to 83.87% (MapCoder,
  Table 7), against −1.61% to 6.45% for an iterative system. A four-stage chain
  is their pipeline reference class.
- **Their taxonomy has no cell for a well-formed but unsupported response** — the
  nearest is character-level Corrupt, which is the *least* damaging type. That
  sharpens the gap statement.

### 14.9 Citation corrections and reading-list status

- **AgentChaos is peer-reviewed and accepted**, not a preprint: Tan et al., ASE
  2026 (41st IEEE/ACM ASE, Munich, 12–16 Oct 2026), DOI
  `10.1145/3832783.3837437`. The plan listed it as "Aug 2026 preprint" — fix
  before `/ars-citation-check`. Given the venue, it is the highest-value citation
  in this group for an SE journal.
- **Huang et al. (faulty agents / AutoInject) is ICML 2025** despite the arXiv
  2408.00989v4 stamp. **Disambiguate from Huang et al. (2024)**, "LLMs Cannot
  Self-Correct Reasoning Yet" — two different Huangs, both cited.
- **Arimbur is a single-author preprint, no venue, IEEE template.** Cite for the
  diminishing-returns *curve shape* and the determinism threat; never for point
  estimates.
- ⚠ **MAST category percentages are internally inconsistent** — three mutually
  incompatible sets appear (44.2/32.3/23.5, 41.8/36.9/21.3, 37.17/31.41/31.41).
  Only the Fig. 1 set is verified self-consistent (per-mode values sum exactly to
  category totals). **Do not quote any MAST category percentage until the
  denominator is established in the rendered PDF.** Highest-priority verification
  item in this group.
- Self-Edit's published v3 carries an unresolved Chinese-language drafting note in
  §3; check the ACL Anthology canonical PDF before quoting page numbers.

### 14.10 Related-work budget (adopt)

The extraction's recommendation for an SE journal: **full treatment for Tan
(AgentChaos), Kamoi and Cemri (MAST)**; **one sentence each for Huang (faulty
agents — defect-origin stratification) and Arimbur (serving determinism)**; drop
Self-Edit unless the placement discussion needs a second, mechanistically
independent witness for P2 < P1. Three full treatments plus two clauses.

Also usable now: the MAST-to-pipeline mapping is done. Reachable modes in a closed
four-stage pipeline are **1.1, 1.2, 2.3, 2.4, 2.5, 2.6**; modes 1.3–1.5, 2.1–2.2
and 3.1 cannot arise by construction; and **3.2/3.3 are eliminated by the
deterministic supervisor rather than mitigated** — which is the strongest single
argument for zero LLM calls in the control path, and pairs with MAST §4's finding
that prompted verifiers "perform only superficial checks".
