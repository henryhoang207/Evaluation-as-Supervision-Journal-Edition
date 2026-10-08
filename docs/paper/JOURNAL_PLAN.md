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
> marking the questions the Phase-0 memo must actually ask. ⚠ **As of
> 2026-08-26 only D5b is still ❓.** D11b, D8b and D8d are approved; **D13 is
> ✅ COMPLETE — rated, scored and verified 2026-08-26. Its result is a finding
> against the supervisor, not a reassurance: see §15.**

> **Build-and-wire pass, 2026-08-25.** B4–B8 are built and the live
> regeneration seam is **wired**: `run_injection_study._regenerate` re-runs the
> defective stage through the production agent's own prompt
> (`BaseAgent.build_prompt` / `run_messages` over `nodes.stage_payload`), so an
> arm is a documented modification of the production prompt rather than a
> re-typed lookalike. **No trial has run — not one LLM call.** ⚠ *Superseded
> 2026-10-08: every cell except C7 has run (core, D19, C1, placement, severity,
> warm, Tier-1 replay, downstream propagation) — see `RESULTS.md`.*
>
> This pass edits **§3, §6.1b and §6.2 in place**, replacing figures that were
> multiplied by hand with figures the scripts compute. Every number below now
> has a command that regenerates it, and `tests/` pins it. Headline changes: the
> Tier-2 ceiling is **102**, not 160; the core budget is **822 trials**, not
> ~980 (⚠ superseded the next day — D11b grows the sample to ≈143 defects and
> the core to ≈1,180 trials; see the box below); and at N=102 the **MDE has caught D11b's threshold**, which is what
> makes the +8-dump collection a blocker rather than a nicety.
>
> Arm wording was frozen on the same date (`scripts/arms.py`,
> `NEXT_SESSION.md` §4a).

> **✅ SUPERVISOR APPROVED, 2026-08-26** (reported by the author; see
> `PHASE0_MEMO.md` for what was put to them). Three decisions now stand:
>
> - **D11b — keep X = 12 pp and grow the sample.** Collect 8 more Phase-A dumps
>   in observe mode, N 102 → ≈143, MDE 10.8 pp with the occasion effect.
>   ⚠ **The core grows with it: 822 → ≈1,180 trials.** The collection calls are
>   the small part of that bill.
> - **D8b — option (ii): one C0 base, shared by C0 and C1; only the retry
>   prompt varies.** Decided on validity, not cost: regenerating the base under
>   C1 would break the within-defect matching every other contrast relies on.
>   The paper must therefore claim *retry-time constraint disclosure*, not a
>   constraint-complete pipeline.
>
> - **D8d — the C1 cell runs at 40 defects (≈240 trials)**, not 80. C1 is
>   reported as an estimate with a CI (D8c), so a ~1.4× wider interval is a
>   small loss and it halves the cell's cost.
>
> **Study size as approved:** core ≈1,180 trials + C1 ≈240 = **≈1,420 trials
> ≈ 1,420–4,260 calls**, before the placement, severity and P3 cells.
>
> **Still open: D5b** (local model identity — needed before Phase 4/C7, or
> immediately if the ESEM registered-report route is taken) and **D13**
> (second rater — the *scheduling* is free, but the rating must happen before
> core results exist or the rater is not blind).
>
> ⚠ **One §7 item is not answered by "approved".** The warm-resample subset
> (temperature > 0) is marked REQUIRED by D2 and is **not built**; the memo asks
> for a *choice* — build it, drop it from D2, or defer it — and a ratification
> does not make that choice. Still outstanding.

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
| D8b ✅ | **What base output does C1 use?** | **DECIDED 2026-08-26, supervisor approved: option (ii) — one C0 base, shared by both C0 and C1; only the retry prompt varies.** The deciding argument is validity, not cost: **(i) breaks the matched design.** Every contrast here is matched within a defect (§14.1's session rule, D4b's blocking). Under (ii) C0 and C1 see the *identical* injected base, so C0-vs-C1 is matched exactly as the arms are; under (i) the two cells hold different base outputs and the difference-in-differences is confounded with whatever C1 changed about the clean output — plausibly including making it *cleaner*, which is the very thing C1 exists to do. Cost agrees (D8c: unreachable N). **Consequence for the write-up:** the manipulation is retry-time constraint disclosure, and the paper must say so — the claim is *"stating the constraints at retry time"*, not *"a constraint-complete pipeline"*. That is also the cheaper deployment change, so it is the more useful claim. ⚠ **The C1 cell's *size* is still open** — see D8d. |
| D8d ✅ | **How large is the C1 cell?** | **DECIDED 2026-08-26: 40 defects × {A1,A2} × r=3 = ≈240 trials.** Split out of D8b because deciding the *base* did not decide the *budget*: at the specified 80 defects the cell was ≈480 trials, 58% of the core again, for a quantity D8c had already declared untestable. Since C1 is reported as an **estimate with a CI rather than a test**, a ~1.4× wider interval is a far smaller loss than it would be if we were trying to reject a null — and halving the cell buys back ≈240 trials. Dropping it was rejected: it would hand a referee the exact objection Huang §5 and Kamoi Table 7 already raise, and *"we knew and did not measure it"* reads worse than *"we measured it imprecisely"*. ⚠ Verify both citations in the PDFs before C1's text is filed. |
| D8c ⛔ | **C1 is an estimate, not a test — the interaction is undetectable** | `scripts/analysis/power.py` §7: detecting a 6 pp interaction (constraint disclosure explaining half the A1−A2 gap) has power **0.109** at 160/40 defects, **0.136** at 160/80, **0.177** at 160/160 and **0.300** even at 320/320 — 2,560 trials (recomputed 2026-08-25 at `--sims 20000`; the row's earlier 0.12/0.19/0.32 were within Monte Carlo error of these, so this is a re-emission, not a correction). ⚠ **And every one of those N is unreachable**: the Tier-2 ceiling is 102, so the honest statement is stronger than the row's — the interaction is not merely underpowered, it is out of reach by a factor of three in sample. Report both gaps with CIs and pre-register the interpretation: *if the C1 gap CI includes zero while the C0 gap CI excludes it, that is suggestive, not conclusive.* Put the power figure in threats to validity. Kamoi's Required row is a **design** requirement — that prompt completeness is addressed — not a statistical one, so running the cell and publishing C1 satisfies it. Run C1 at 80 defects, not 40: half the CI width for double the calls. |

### 3.2 What is measured

| # | Decision | Position |
|---|---|---|
| D3 | **Success criterion (frozen before runs)** | Supervisor verdict on the retried output is `proceed`/`proceed_with_warning` **and** the injected defect is genuinely resolved. ⚠ **"The descriptor no longer fires" is NOT the criterion.** §13.5 shows why: a fabricated evidence ID swapped for a *different* fabricated-but-resolving ID stops the descriptor firing while the output got worse. **Score the replacement value.** Earlier versions of this row froze the wrong criterion. |
| D3b | **Outcome structure — corrected** | The original four classes were **not mutually exclusive** (`collateral` overlapped `repaired_clean`), so they could not be the multinomial D4 analysed them as. Outcome is now a **3-class multinomial** {`repaired`, `replaced`, `unrepaired`} **crossed with a binary collateral flag**. Collateral is a second dimension, not a fourth class. ⚠ **Superseded 2026-09-02 by D18 (§3.7): the multinomial is now 4-class**, {`repaired`, `replaced`, `deleted`, `unrepaired`}, still crossed with the collateral flag. Mutual exclusivity survives because the four are decided in a fixed order, which is the property this row exists to protect. |
| D3c | **Collateral threshold — measured, not chosen** | `scripts/analysis/churn.py` measures what an *unperturbed* pipeline already churns, from the repetition sub-study (same 5 businesses, 5 runs, same seed, temperature 0, no injection, no feedback). **There is no single threshold** — the floors differ by an order of magnitude: pattern aspects p95 churn **0.07** (closed 7-value enum), pattern descriptions **0.33**, root causes **0.29**. ⚠ Strategy recommendation issues measure 37% churn, **but that figure is confounded** — repetition runs regenerate every stage, so strategy churn compounds reasoning churn, whereas a replay trial pins upstream from the dump. Conditioning on near-identical upstream gives **23%** (n=13 pairs). Use 23% for the strategy stage; collateral there is **weak, not unmeasurable**. Set per-item-class thresholds above these floors and cite the calibration. |
| D3d | **Exact-string matching is unusable for most items** | Same source: across identical runs, exact-match rates are **0.01** (pattern descriptions), **0.03** (root causes), **0.00** (recommendation issues). Those items are essentially never byte-identical between runs. The report-containment check relies on exact equality and only passes because the report agent copies from its own prompt payload within a single run. State this in the Method section before a referee finds it. |
| D6 | **Injection scope** | Reasoning, strategy, report stages — their defects are item-level. Analysis excluded for two reasons: its defects are distributional (contradiction *rate*), and its measurement needs `reviews_df`, which the dumps do not carry. ⚠ **Tier 1 covers only reasoning and strategy** — the bank holds 0 report-stage and 0 analysis-stage defects (§5) — so Tier 2 carries the stage comparison outright. |

### 3.3 How it is analysed

| # | Decision | Position |
|---|---|---|
| D4 | **Primary endpoint — confirmatory set** | **Exactly three confirmatory tests**, alpha controlled across them (Holm): (1) **A1 vs A2** — feedback content; (2) **A2 vs A3** — bare trigger; (3) the **A1/A0 ratio**. Everything else in §8 is **exploratory and labelled as such**. ⚠ The CI on the A1/A0 ratio must come from a **cluster bootstrap over defect blocks**, not the independent-sample delta method the earlier version specified — the arms are matched by design. |
| D4a | **Cochran's Q runs on a dichotomised outcome** | Q is a **binary** test and cannot take the multinomial of D3b. The earlier row asked for both in one sentence. Q is the omnibus over `repaired` vs not; the multinomial is reported descriptively and, if inference on it is wanted, via a separate model. |
| D4b ⛔ | **Tier-1 blocking is over clusters, not defects** | ⚠ **Figures refreshed 2026-09-02 from `defect_bank.py`: 13 usable defects in 7 business × stage cells across 6 businesses**, the largest holding 4 (was 11 / 5 / 4 before the D11b collection). The structural point is unchanged and is the reason this row exists. Blocking on defect identity alone treats near-duplicates as independent blocks and re-narrows exactly the CIs blocking exists to widen. Nest repeated observations within cell. |
| D4c ⛔ | **Grid rebalanced — allocate by contrast difficulty** | The §6 grid gave A1 320 trials and the other arms 240 over only 5 businesses → **80 matched quadruples**, power **0.30**. But **A2-vs-A3 (28 pp) is already at 0.996 with 5 businesses**, so equal allocation overspends on the easy contrast. Allocate: **A1 and A2 at the full defect set, A3 at a quarter, A0 at a half.** ⚠ **Corrected 2026-08-25:** the allocation is over *defect subsets*, not over repetitions, and the full set is **102**, not 160. As built today (`--plan-only`): A1 102 defects / 306 trials, A2 102 / 306, A0 48 / 144, A3 22 / 66 — **822 trials at r=3**. ⚠ **After D11b (2026-08-26) the same fractions apply to ≈143 defects: ≈1,180 trials.** Take the figure from `--plan-only` once the dumps land, not from this row. |
| D4d | **Power — computed, and it constrains the design** | `scripts/analysis/power.py`; simulation-based because arms are matched within defect, reps nest inside (defect, arm), and Tier-1 defects cluster — closed-form McNemar assumes independent pairs and overstates everything. At the plan's own predicted **12 pp** effect: 8×5 r=2 → **0.30** (MDE 22 pp); 8×20 r=2 → **0.80** (MDE 12 pp); 8×20 r=3 → 0.93. **160 defects is a hard ceiling** (8 operators × the 20 Phase-A dumps) ⚠ **corrected 2026-08-25: the real ceiling is 102 — see the banner at §4**, so once the sample is exhausted **r is the only lever**; reps and blocks buy power about equally here (8×10 r=4 ≈ 8×20 r=2 ≈ 0.81), contrary to the usual advice. ⚠ A **shared-occasion effect** (§14.1 requires all arms for one defect in one session, so they share that moment's serving stack) raises arm-to-arm correlation, cuts discordant pairs, and drops 8×20 r=2 from 0.81 to **0.75**. **Plan r=3 if 0.80 is the target.** ⚠ **Recomputed 2026-08-25 at the real defect counts** (`power.py` §9, `--sims 20000`, seed 42): **N=102, r=3 → power 0.801, MDE 11.9 pp**; with the occasion effect at SD 1.0, **0.755 and 12.6 pp**. **N=143 (+8 dumps), r=3 → 0.913 / 0.883, MDE 10.2 / 10.8 pp.** The r=2 row is not viable at either N (0.618 / 0.764). |
| D4e | **Tier 1 supports no inference** | MDE ≈ **31 pp**, and the cluster bootstrap **over-rejects at 0.086** against a nominal 0.05 with 5 clusters (naive McNemar is conservative there at 0.026, but that is luck, not validity). Tier 1 is a realism anchor reported descriptively. Run no hypothesis test on it. |
| D4f | **Pre-register as estimation, not NHST** | Given the MDEs, report A1 − A2 as a **difference with a CI** (half-width ≈ 0.7 × MDE: **±8.3 pp at the current 102 defects, ±7.1 pp at 143** — recomputed 2026-08-25; the earlier ±8/±11 assumed 160/80). A null then *says something* — "3 pp, 95% CI [−5, 11]" excludes large effects — instead of being indistinguishable from insufficient power. This also makes D11b's threshold meaningful. |
| D4g | **The go/no-go is a pre-specified interim analysis** | §10's "Tier 1 → preliminary analysis → go/no-go" *is* an interim look. Declare it descriptive-only with no stopping rule on the confirmatory tests, or specify an alpha-spending function. |
| — | **Retained from the original D4** | Wilson CIs on all proportions; **never pool replayed-real with synthetic in a headline**; Tier 2 gives precision, Tier 1 gives realism; Just-style coupling licenses reading Tier-2 rates — **noting it covers only 4 of 8 operators** (§5). Publish whatever the sign is. |

### 3.4 Apparatus and provenance

| # | Decision | Position |
|---|---|---|
| D5 | **Models** | Hosted: `gemini-2.5-flash`, **pinned to a dated snapshot if the API exposes one** — recording drift after the fact is strictly worse than preventing it, and §14.1 only requires recording. Fallback **disabled** during trials (`LLM_DISABLE_FALLBACK=1`, built); a trial where fallback fired is discarded and logged. |
| D5b ❓ | **Local model — a placeholder, not a decision** | "One open-weights instruct model via the existing Ollama profile" does not support C7's reproducibility claim, which is the journal's strongest generalisation asset. **Pre-register model, parameter count, quantisation, seed and runtime version by name.** Supervisor input requested. ⏳ **2026-10-08: recommended `qwen2.5:7b-instruct-q4_K_M` via Ollama on the author's RTX 5060 (8 GB assumed), `num_ctx 32768`** — awaiting the author's confirmation and server; procedure in `C7_RUNBOOK.md`, to be filed as prereg amendment A10. |
| D5c | **No-injection control — downgraded** | The recorded clean Phase-A verdict is **not** a valid control: it was produced weeks earlier in a different serving epoch, which is precisely what §14.1 blocks against. Either re-run the clean condition **in-session as a fifth cell**, or report it as a historical reference value and stop calling it a control. |
| D12 ⛔ | **Downstream propagation is in scope, and blocks B7** | Moving it in gives the journal an actual claim — *defect-level repair does not equal pipeline-level improvement* (MAST App. J) — instead of five ablations. **B7 must persist the full retried stage output plus enough state to re-run downstream stages later**, not just facts and verdict. Nearly free on the first pass; a full re-run of the whole core to recover afterwards — **822 trials today, ≈1,180 after D11b** (corrected 2026-08-25 from ~1,400). **Built:** `run_trial` persists `retried_output` plus a `downstream_state` from which the later stages can be re-run — and clears the dump's own strategy/report outputs, which were produced from the *pre-injection* output of the retried stage and are not this trial's downstream. |

### 3.5 Publication

| # | Decision | Position |
|---|---|---|
| D11 | **Number of papers** | Conference core and journal core are the same experiment, so **build and run first, then branch on the result**. Full analysis in `PUBLICATION_STRATEGY.md`. |
| D11b ✅ | **The branch threshold, quantified** | **DECIDED 2026-08-26, supervisor approved: keep X = 12 pp and fix the sample instead — collect 8 more Phase-A dumps, taking N from 102 to ≈143.** Rejected: lowering X (chooses the threshold after seeing what the design can detect); raising X to 13 (free and conservative, but forfeits the split and with it the ~6-month conference route); and buying the same precision with r=4 at N=102 (**≈1,120 trials against ≈1,180 — near-identical cost for a worse MDE, 11.2 pp vs 10.8 pp, because repetitions of one defect are correlated and a new defect is not**). The chosen option is the only one that also adds eight workloads, which answers the "n is small and clustered" objection in `PUBLICATION_STRATEGY.md` §4 with the same money. ⚠ **Budget consequence:** more defects means more trials — the core goes from 822 to **≈1,180**; the ~30–55 collection calls are the small part. Re-run `--plan-only` after collection for the exact figure. — Original reasoning follows. "A1 ≫ A2" is not a criterion. X must be **≥ the MDE**, or the split would rest on an effect the design cannot reliably detect. ⚠ **Corrected 2026-08-25 — the threshold is currently incoherent.** At the real N=102, r=3 the MDE is **11.9 pp**, a 0.1 pp margin under the proposed X of 12 pp — and **12.6 pp** once §14.1's shared-occasion effect is included, which puts the MDE *above* the threshold outright. Collecting 8 more Phase-A dumps takes N to ~143 and the MDE to **10.2 pp** (10.8 pp with the occasion effect), restoring a 1.8 pp margin (1.2 pp). **Fix the sample, not the threshold** — lowering X after seeing the MDE is the move a pre-registration exists to prevent. **The rule, as approved: split iff the A1 − A2 point estimate ≥ 12 pp AND its 95% CI excludes zero.** The threshold falls out of the design rather than being chosen after seeing data, which is what makes the pre-registration real — and it is why the sample moved instead of the threshold. |
| D7 | **Venue** | **EMSE regular track for the journal vehicle** (§12). Conference vehicle open; ASE and the ESEM registered-report route are live options. ⚠ Every deadline cited in `PUBLICATION_STRATEGY.md` §8 is **unverified** — confirm against official CFPs. Ask the #1 chairs about an extended-version route while #1 is still under review. ✅ **2026-10-08: the author chose journal only** (no conference split) — see `JOURNAL_PAPER_PLAN.md`. |

### 3.6 Threats this design does not remove

| # | Item | Position |
|---|---|---|
| D13 ✅ | **EXECUTED 2026-08-26 — two blinded human raters, κ 0.870. ⚠ It found a supervisor precision bug rather than validating the bank; results and consequences in §15, and the decision it forces in `PHASE0_MEMO.md` §11.** The method as originally settled: | §5 requires two-pass review with disagreements recorded. A solo researcher cannot be their own second rater, and κ computed by one person is not inter-rater agreement. ⚠ **An LLM is not a legitimate second rater here** — it wrote `defect_bank.py`, which *defines* the bank, so rating its own classifier's output reproduces the circularity the audit exists to break. **Split the construct.** *Groundedness* is factual and **verified programmatically** — exhaustively, by `supervision.measure` and `tests/test_replay.py`. ⚠ It is **verification, not a second rating**: it answers an implementation question, and no κ applies to it. *Meaningfulness* is judgement and needs a second human. **Instrument built 2026-08-26: `scripts/analysis/rater_sheet.py`** (19 tests) — `--build` emits a blinded sheet of **31 items (all 11 Tier-1 defects plus 20 Tier-2 injections, round-robin so every one of the six repair operators is represented)** in seeded random order, plus a sealed `key.json`; `--score` returns raw agreement, Cohen's κ with a bootstrap CI, and every disagreement with its notes. One binary question per item — *an error, or a technicality of the check?* — plus **U** for unratable, excluded from κ and reported separately. Blinding hides tier, operator, class, business and defect id, and `tests/test_rater_sheet.py` fails if any of them leaks. ⚠ **It does not hide item shape** — an evidence-citation item cannot be made to look like a recommendation item — and that limit is stated rather than papered over. **Sequencing: the rating must happen before core results exist**, or the rater is no longer blind. Report κ **with a CI, or raw agreement and n**; 31 items does not support a bare κ. Reportable as: "groundedness verified programmatically; defect meaningfulness rated independently by two blinded humans." |
| D14 | **A1 confounds *specific* with *correct*** | There is no specific-but-wrong feedback arm. Claim feedback **content** effects, not specificity effects; concede in limitations. |
| D15 | **One model, one provider, one pipeline, one domain** | Everything is `gemini-2.5-flash` on Yelp restaurant reviews across **28**
workloads (20 until the D11b collection of 2026-08-26 — do not print 20). "Is this a property of the method or of this model?" has no answer in the data. C7 (local runtime) is the cheapest partial fix. This is the objection that rules out a top-tier venue at current scale — state it rather than let a referee state it. |
| D16 | **The checks are shallow by design** | ID resolution, set membership, `difflib` ≥ 0.35, exact string containment. That determinism is the *thesis* — zero LLM calls, correct by construction — but a referee will read it as string matching and ask whether the defects are correspondingly shallow. Frame it as a deliberate trade, explicitly. |
| D17 | **"Repair" here means repair by regeneration** | The retried stage regenerates its whole output rather than editing the faulty artifact, so what is measured is *regenerate-under-measured-feedback*, not *fix-this-object*. P1 narrows the gap by putting the artifact in context; it does not close it. Say "repair by regeneration" — overclaiming "self-repair" summons the referee who knows the self-correction literature. |

### 3.7 Supervisor review of the methodology (2026-09-02)

Four points from the supervisor, all four accepted. **Zero trials had run when
they landed**, which is what makes them design amendments rather than post-hoc
adjustment — and it is the last moment at which they could have been.

Two of the four are new; D18 and D20 largely formalise or repair things the
build already half-contained, which is the more useful kind of review finding.

| # | Decision | Position |
|---|---|---|
| D18 ✅ | **`deleted` is a fifth outcome class — IMPLEMENTED 2026-09-02** | *"Add a fifth outcome class: `deleted`. The offending claim needs to be deleted rather than corrected."* Accepted, and it was fixing a live scoring bug rather than refining a taxonomy. **The built scorer handled deletion two different ways depending on which operator ran**: dropping the flagged item scored `replaced` for O1/O2/O3/O5 (`_injected_item` returned `None`, `_item_restored` returned `False`, and the trial fell through to the `CAN_REPLACE` branch) and `repaired` for O6/O7. For an *insertion* operator that is correct — the item was invented, so removing it **is** the fix — and O6/O7 keep scoring `repaired`. For a *substitution* operator it is evasion: an item the clean output had is gone, and the check passes only because there is nothing left to check. **Outcome is now a 4-class multinomial `{repaired, replaced, deleted, unrepaired}` still crossed with the binary collateral flag**, decided in a fixed order — check fires → `unrepaired`; item gone → `deleted`; item back to its clean value → `repaired`; else `replaced` — which is what keeps the classes mutually exclusive and so preserves D3b. Three consequences the change forced, none cosmetic: **(a)** deletion is decided by **identity, not index**. Retry regenerates the whole stage (D17), so index identity scored every retry that emitted fewer patterns as a deletion. Each substitution operator now anchors on the field it does *not* touch — `description` for O1/O2/O3, `action` for O5 (`_apply_o5` rewrites `issue` only). **(b)** the injected item is **excluded from the churn computation**. It was not, so a deletion raised `collateral` off the same event that set the outcome class, and on a single-pattern base pinned churn at 1.0 — the two dimensions were not independent. **(c)** `churn_rate` returned 1.0 for an empty pre-list, a latent bug reachable only once exclusion could empty it. ⚠ **One stated limit, checked rather than assumed:** excluding the item leaves the rate over n−1 against floors calibrated over n. That is the *correct* estimator for the non-injected population — rescaling to lost/n would understate it — but the flag's resolution becomes 1/(n−1), so on a small base one lost item can straddle a floor (measured: a 4-pattern base losing one unrelated pattern scores 0.333 against the 0.33 floor, where the full-list rate is 0.250). Matched design, so it touches the absolute collateral rate's resolution and never the between-arm comparison. **Dichotomy, pre-registered: `deleted` counts against `repaired`** in the Cochran's Q / McNemar outcome, or "drop the pattern you were asked about" scores as a supervisor success. An evidence list that survives but is *empty* is `replaced`, not `deleted` — the pattern is still asserted, now with no support at all. Power is untouched: the confirmatory tests were always run on a dichotomy. `CAN_DELETE` is named separately from `CAN_REPLACE` although the two sets coincide today — see D19, where they diverge. **9 new tests; suite 257 → 266.** |
| D19 ✅⏳ | **O4 is reframed as the recompute-and-overwrite counterfactual** | *"The inflated-frequency cell can be reframed as a counterfactual confirming the overwrite decision in §4.5, rather than treated as an ordinary retry branch."* **The strongest of the four, and it revives an operator this plan had written off twice** — "dead as a repair cell" (§6.2) and the warn-level frequency sub-experiment listed as scope creep (§11) — while §4's own operator notes call it the only operator with real observed parameterisation (27 natural `frequency_corrected` observations). Conference §4.5 asserts a design principle — *any quantity the checker can compute should not be asked of the model* — and **neither paper contains a counterfactual for it**; §6.7 illustrates it, nothing tests it. The cell asks: *what would overwrite have cost had frequency divergence been routed to retry?* Overwrite is exact at 0 calls; retry is p<1 at 1–3 calls plus prose churn. **Design: O4 × {A1, A3}, P1, r=3.** A1 is best-case retry, A3 the floor; A2 is omitted because the cell is not about feedback content. **23 of 28 dumps are applicable** (measured 2026-09-02, `inject_defects.py --matrix`; the committed `injection_matrix.json` is stale at 20 dumps / 16 bases) → **≈138 trials**. **It needs no new frozen wording**: `supervision.py:323` already emits `frequency_corrected:{aspect}:{claimed}->{recomputed}`, a measured-fact string, and A1 routes it through the production template — `arms.py:AUTHORED_WORDING` is untouched. It *is* a new A1 instantiation for a check that produces no `retry_feedback` in production, so log it as a dated pre-registration addendum. ⚠ **Two prerequisites.** (i) **Not pooled into the A1−A2 primary contrast**, or N and the power gate move. (ii) **The scorer's O4 path is untested and needs D18 applied to it**: `IDENTITY_ANCHOR["O4"] = "description"` and O4 added to `CAN_DELETE` — dropping the pattern to avoid making a frequency claim is evasion — but **not** to `CAN_REPLACE`, since a frequency within tolerance of the recomputed value is correct by construction and has no passes-but-wrong-value mode. That is the case where the two sets diverge, and the reason D18 named them separately. ⚠ **Pre-specify the interpretation both ways or the cell reads as built to confirm a decision already shipped:** *if retry repairs frequency at ~100% with no collateral churn, overwrite is a cost optimisation, not a correctness one.* |
| D20 ✅ | **Injection-validity gate, with its own denominator** | *"Add an injection-validity gate ensuring the supervisor performs the expected check before proceeding to retry; count the failures separately."* Accepted. **~80% already built and never wired**: `inject_defects.verify_injection()` exists and checks the right thing — the target class fired **and** no additional retry-level class appeared — but `run_injection_study.run()` goes `inject()` → straight to trials and never calls it. `run_trial` records `pre_facts`/`pre_verdict` and nothing asserts on them. Three changes. **(1)** Call `verify_injection` in **`build_plan`, not `run`** — it is pure `measure()` at zero API cost, so a failure must remove the defect *before* money is spent and must show up in `--plan-only`. **(2)** Add the second gate the supervisor names: `decide(...).verdict == "retry"`. A defect the supervisor flags but does not route to retry yields no arm contrast at all. **(3)** Two counters, two denominators: **injection success rate** and **trigger rate**, both reported. **This decides §14.3, which was left open:** untriggered defects are **excluded from the denominator and reported as a separate count** (AgentChaos's choice), *not* scored `unrepaired` — scoring them would score the arms on trials where the arms are identical by construction. ⚠ **Run the gate before re-running `power.py`.** N=142 clears the 12 pp threshold by **1.1 pp**; every defect the gate removes comes straight out of that margin. |
| D21 ✅ | **The pre-registration becomes a document, and it forces the pooling decision** | *"Pre-specify measured-fact vs generic rejection as the primary comparison, before seeing results."* The **substance** is already decided and correct — §6.2 names A1/A2 the primary contrast, D4f pre-registers estimation-with-CI, D11b freezes the split rule, §8 fixes three confirmatory tests under Holm, §13.3 records directional predictions. What does not exist is a **frozen, dated, committed artifact**: it is spread across 1,572 lines of a plan carrying correction banners, and `PHASE0_MEMO.md` is a memo of *open* decisions, not a pre-registration. ⛔ **And nothing in this work is committed** — a pre-registration not in git before the first trial is not one. **Deliverable: `docs/paper/PREREGISTRATION.md`, drafted 2026-09-02, committed with a dated hash before any trial.** ⚠ **Writing it surfaced a collision nobody had noticed.** §15.6 (D13 audit) says *do not pool O1 with O2–O7* — O1 is the only production-like operator, the rest are more severe than anything production catches. Honour that in the **primary contrast** and N drops 142 → 118, because O1 carries 24 defects. Measured (`power.py --defects 118 --sims 6000 --seed 42`, a coarser run than the plan's 20,000): **118 at r=3 gives MDE 11.9 pp with the occasion effect against X = 12 pp — a 0.1 pp margin**, i.e. exactly the incoherent state D11b's eight extra dumps were collected to escape. r=4 restores it (10.5 pp) at ~944 trials on A1/A2 alone. **Recommendation, adopted in the draft: pool for the contrast, split for the rates.** A1−A2 is a claim about feedback *content*; there is no principled reason to estimate it inside the severe cell only. So: primary contrast at N=142; O1-vs-severe stratification pre-specified as a **secondary** analysis with CIs; **absolute repair rates never pooled**, which is what §15.6 is actually protecting. ⚠ **Supervisor decision required** — the alternative (primary contrast within the severe cell at r=4) is defensible and costs the trials above. It must be settled *before* the pre-registration is committed, because it is precisely the kind of choice that cannot be made after seeing data. |

#### Closure of D19–D21 (2026-09-08)

All four supervisor points are now discharged as far as they can be before the
first trial. **Marker key: ✅ done · ✅⏳ decided and built, cell not yet run.**

| # | What closed | What remains |
|---|---|---|
| D18 ✅ | Implemented 2026-09-02, suite 257 → 266. | — |
| D19 ✅⏳ | **Decided in scope** (`PREREGISTRATION.md` §7), exploratory, sequenced after the core. Its scorer prerequisite is **built**: `IDENTITY_ANCHOR["O4"] = "description"`, `"O4"` added to `CAN_DELETE` and deliberately **not** to `CAN_REPLACE`. | The ~138-trial cell itself, after the core and on a confirmed budget. If the budget cannot cover it, the paper reports it as pre-registered and unrun. |
| D20 ✅ | **Wired** into `run_injection_study.build_plan` — injection-validity gate plus the trigger gate (`decide(...).verdict == "retry"`), two counters against two denominators in `plan_summary`, and the runner keyed on `runnable` rather than `applicable`. | — |
| D21 ✅ | `PREREGISTRATION.md` §11 is **empty**; all three decisions taken and recorded with their rejected alternatives. | The **freeze commit**. Until it exists there is no pre-registration. |

**Three findings from doing the work, none of them cosmetic.**

**1. The D20 gates remove nothing on this bank — 142/142 on both, across four
seeds.** This was not expected: §6 of the pre-registration had been written
warning that every gated-out defect eats into a 1.1 pp power margin. It does not
happen, because `applicable()` already encodes most of what the gate re-checks.
**N stays 142, 1,167 trials, and the power figure stands as computed rather than
as a projection.** The gate is therefore a *standing guarantee*, not a filter,
and must be reported as one — a 100% injection-success rate is only interesting
prospectively, and claiming it as validation would oversell it.

**2. D19's specification had a third gap it did not name.** It called for the
anchor and the `CAN_DELETE` membership. Both alone are inert: `_hosts()` mapped
no item list for O4, so `_base_host` returned `None`, `item_deleted` could never
be True, and a retry that dropped the pattern rather than making a frequency
claim would have kept scoring **`repaired`** — the exact evasion D18 was raised
to fix, surviving in the one operator D18 did not touch. Fixed, with a test that
fails against the old behaviour.

**3. The matcher bug is larger than `PHASE0_MEMO.md` §11 says.** The memo quotes
`untraceable_recommendation` as **6 of the 11** Tier-1 defects. That is the
20-dump figure. The regenerated bank reads `untraceable_recommendation: 8` of
`genuine: 13` — **8 of 13**. The memo understates its own question's blast
radius and should be corrected before it goes to the supervisor. ⚠ Relatedly,
`out_study/injection_matrix.json` is still the **20-dump** artifact
(`n_dumps: 20`, `repair_operators: 102`) while `defect_bank.json` beside it has
been regenerated at 28; it is tracked, so committing as-is puts a superseded
number into the record.

**What was decided by the author rather than the supervisor, and why.** Q3, Q4
and Q5 of the memo were answered here without waiting, because each is a choice
that becomes illegitimate once a result exists and the study cannot start
without them. They are **open to override up to the freeze commit**. The two
questions that are genuinely not the author's — **Q1** (fix the matcher now?)
and **Q2** (what to tell the conference chairs about a paper in review) — remain
open and block nothing, because neither touches the analysis the
pre-registration specifies.

---

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

> ### ⚠ CORRECTION 2026-08-25 — the Tier-2 ceiling in this section is wrong
>
> **This section says 160 defects (8 operators × 20 Phase-A dumps). The real
> figure is 102.** The multiplication assumed every operator can use every dump.
> Four things break that, all now computed rather than asserted:
>
> - operators are **stage-specific**, and stages differ in **clean bases**
>   (reasoning 18, strategy 17, report 19 of 20);
> - **O3** requires a pattern with an aspect its *resolving* evidence lacks — 15,
>   not 17;
> - **O4 carries no repair endpoint.** A frequency divergence yields
>   `proceed_with_warning`, never a retry, and `graph.py:140` then overwrites the
>   claimed value deterministically. No retry, no LLM involvement, nothing to
>   repair. It is retained as a *warn-level* operator.
> - **O8 is a positive control.** `report_node` passes correct metadata in the
>   prompt payload, so every arm copies it back at ~100%.
>
> Per operator: O1 17 · O2 17 · O3 15 · O4 16 · O5 15 · O6 19 · O7 19 · O8 19 =
> **137 total, 102 with a repair endpoint.**
>
> **Consequences**, computed by `power.py` §9 at `--sims 20000`:
>
> | N | r | power | power w/ occasion | MDE | MDE w/ occ |
> |---|---|---|---|---|---|
> | 102 (now) | 3 | 0.801 | 0.755 | **11.9 pp** | **12.6 pp** |
> | 143 (+8 dumps) | 3 | 0.913 | 0.883 | 10.2 pp | 10.8 pp |
>
> Monte Carlo estimates from `power.py --sims 20000` (seed 42; the MDE bisection runs at 6,666): power carries about **±0.01**, an MDE about **±0.3 pp**. Two significant figures is all that is real.
>
> ⚠ **The first version of this banner typed 0.790 / 11.9 / 0.902 / 10.2, and
> those were right** — both MDEs reproduce exactly and the powers differ by
> 0.011, inside Monte Carlo error. What the recomputation adds is not a
> correction but two things the typed row could not carry: a **command that
> re-emits them**, and the **shared-occasion column**, which is where the
> threshold problem actually bites.
>
> **The MDE has caught D11b's 12 pp threshold** — a threshold defined as "must
> be ≥ the MDE". Without the occasion effect the MDE is 11.9 pp against a 12 pp
> threshold — a 0.1 pp margin, which is no margin. Under the occasion effect the
> design will actually face, it is **12.6 pp, above the threshold outright**.
> Either way the pre-registration is incoherent until more dumps are collected.
> Measured yield is 5.1 repair defects per dump; **+8 dumps restores N≈143 and a
> 1.8 pp margin (1.2 pp with the occasion effect).** The trial budget is **822**, not ~1,320,
> because D4c allocates arms over defect *subsets*.
>
> Regenerate with `python scripts/inject_defects.py --root out_study --matrix`;
> `tests/test_inject.py` pins every number above, so a stale plan fails the
> suite. **Do not re-derive this by hand** — that is what produced 160.
>
> Also corrected: O4's `f ∈ {1.1, 1.5, 1.8}` multiplier is mis-specified for this
> corpus. Median claimed frequency is 0.16, so f=1.1 moves it 0.016 — under the
> 0.05 tolerance, a **silent no-op in 81 of 89 patterns**. Parameterize O4 as an
> **absolute divergence**; keep 1.6–1.8× as provenance only.

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
| B6 | Outcome scorer — `scripts/analysis/score_repair.py` | Classifies each trial into D3's taxonomy from (pre-injection output, injected output, retried output, descriptor). Pure Python, unit-tested. Emits per-operator applicable-trials denominators. ⚠ **Collateral must be redefined — the specified metric cannot discriminate.** "Any added/removed/altered pattern-or-recommendation beyond the injected one" assumes retry is an *edit*. It is not: the retried stage regenerates its whole output from upstream state (see B3/§6.1), so essentially every trial changes essentially every item and the collateral rate pins at ~100% in **all** arms. Score it instead as semantic set-overlap against the **pre-injection** output (or restrict scoring to the items the feedback explicitly named). This is §13.5's replacement-value problem one level up, and it needs the same kind of golden test before any trial runs. **Must score the replacement *value*, not the disappearance of the original defect** — a swapped-but-still-wrong ID or a differently-wrong frequency is `replaced`, not `repaired`. Golden test for this case required before any trial (§13.5). ✅ **Amended 2026-09-02 by D18 (§3.7): the outcome is 4-class, `deleted` added**, deletion is located by identity rather than index, and the injected item is excluded from the churn computation so the outcome class and the collateral flag stop being raised by the same event. 9 new tests. |
| B8 ✅ | **A1 template information-equivalence audit + C1 prompt variant** | ✅ **Both halves done.** The audit ran and is a passing gate: **5 of 5** obligations (not four — §13.1 undercounted) reach the model only through the A1 feedback, recorded in `out_study/prompt_audit.json`. D8's *or record the delta* branch is what unblocked trials. ✅ **The C1 prompt was written 2026-09-20** — `scripts/arms.py`, `C1_PREAMBLE` + `C1_CONSTRAINTS`, each clause restating the audit's `supervisor_asserts` field and never a retry string; `python scripts/arms.py` prints it verbatim for the appendix. Wired as `run_injection_study.py --c1`, **off by default**. Post-freeze, so `PREREGISTRATION.md` §0.1 A1 records it and the cell stays exploratory. |
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

⚠ **Recomputed 2026-08-25 against the measured defect counts.** The table
below used to sweep "8 operators × N dumps", which assumes every operator can
use every dump. It cannot — see the correction banner at the end of §3 — so the
designs are now indexed by the **defect count the injector actually produces**.
`power.py` §9 emits this table (`--sims 20000`, seed 42); `inject_defects.py
--matrix` emits the counts.

| Design | Matched defects | Power | Power w/ occasion | MDE @ 80% | MDE w/ occ |
|---|---|---|---|---|---|
| The sample before D11b, r=2 | 102 | 0.618 | 0.564 | 14.7 pp | 15.6 pp |
| The sample before D11b, r=3 | 102 | 0.801 | 0.755 | 11.9 pp | 12.6 pp |
| The sample before D11b, r=4 — *the rejected alternative* | 102 | 0.893 | 0.853 | 10.5 pp | 11.2 pp |
| ✅ **THE DESIGN (D11b, 2026-08-26): +8 dumps, r=3** | **≈143** | **0.913** | **0.883** | **10.2 pp** | **10.8 pp** |
| +8 dumps, r=4 | 143 | 0.967 | 0.948 | 8.9 pp | 9.5 pp |
| Tier 1 (11 defects, 5 cells, r=3) | 11 | — | — | **32 pp** | — |

Monte Carlo estimates from `power.py --sims 20000` (seed 42; the MDE bisection runs at 6,666): power carries about **±0.01**, an MDE about **±0.3 pp**. Two significant figures is all that is real.

The "w/ occasion" columns are the honest ones: §14.1 forces all arms for one
defect into a single session, so they share that moment's serving stack. That
makes the arms *more* alike, cuts discordant pairs, and costs power.

Five consequences:

1. **A2 vs A3 (28 pp) is already at 0.996 with 5 businesses.** Equal allocation
   across arms overspends on the easy contrast. Allocate by difficulty — as
   built: A1 and A2 at all 102 defects, A0 at 48, A3 at 22 (D4c).
2. **102 defects is the ceiling, not 160**, and it is set by the injector's
   applicability matrix rather than by a multiplication. More blocks need new
   Phase-A runs (a full pipeline each); **r is otherwise the only lever**, and
   reps and blocks buy power about equally here, contrary to the usual advice.
3. ✅ **RESOLVED by D11b, 2026-08-26 — the sample grows.** At N=102 the MDE was
   11.9 pp against a 12 pp threshold (a 0.1 pp margin) and **12.6 pp under the
   occasion effect the design will actually face** — above the threshold, which
   is defined as "≥ the MDE". Rather than move the threshold, collect **8 more
   Phase-A dumps**: N≈143, power 0.883 even with the occasion effect, MDE
   10.2–10.8 pp, margin 1.2–1.8 pp. ⚠ Note what this costs beyond the ~30–55
   collection calls: the core scales with the defect count, **822 → ≈1,180
   trials**. The rejected alternative, r=4 at N=102, cost ≈1,120 trials for a
   worse MDE (11.2 pp) — repetitions of one defect are correlated, a new defect
   is not, so per call the eighth dump beats the fourth repetition.
4. **r=2 is not viable at either N** (0.618 at 102, 0.764 at 143). r=3 is the
   floor, which is what the runner defaults to.
5. **Tier 1 cannot support inference** — MDE ~31 pp, and the cluster bootstrap
   over-rejects at 0.086. Descriptive only (§5).

**Therefore: pre-register this as estimation, not NHST.** Report A1 − A2 with a
CI (half-width ≈ 0.7 × MDE: **±8.3 pp at 102 defects, ±7.1 pp at 143**). A null
then *says* something — "3 pp, 95% CI [−5, 11]" excludes large effects — instead
of being indistinguishable from insufficient power.

### 6.2 Grid

⚠ **Rewritten 2026-08-25 from the built runner.** The old grid multiplied
8 operators by 20 businesses and split the core from the arm ablation. Neither
holds: **6 operators carry a repair endpoint** (O4 is warn-level, O8 a positive
control), applicability varies by operator, and the runner allocates arms over
**defect subsets** in one pass rather than running a core and an ablation
separately. Regenerate the first block with
`python scripts/run_injection_study.py --plan-only`.

**The core, as built** — one command, `--placement P1 --reps 3`. Two columns:
what the runner enumerates today, and what it becomes once D11b's eight dumps
land. ⚠ **The right-hand column is arithmetic, not measurement** — applicability
varies per dump, so re-run `--plan-only` after collection and use what it
prints. That is the whole point of the `--plan-only` gate.

| Arm | Defects now | Trials now | Defects after D11b | Trials after D11b | Why this share (D4c) |
|---|---|---|---|---|---|
| A1 measured-fact feedback | 102 | 306 | ≈143 | ≈429 | the primary contrast |
| A2 generic rejection | 102 | 306 | ≈143 | ≈429 | the primary contrast |
| A0 capability ceiling | 48 | 144 | ≈67 | ≈201 | bounds A1; half the set is enough for a bound |
| A3 bare re-draw | 22 | 66 | ≈31 | ≈93 | A2 vs A3 is at 0.996 with a quarter of the set |
| **Total** | **102** | **822** | **≈143** | **≈1,180** | 120 planned, 18 inapplicable with a recorded reason |

**Additional cells**, each another run of the same runner with different flags.
Sizes are stated as *fractions of the 102*, not as fresh multiplications:

| Cell | Placement | Size |
|---|---|---|
| Placement: A1 × {**P0** production-absent, **P2** assistant-turn}, r=3 | P0, P2 | 2 × a third of the set ≈ 200 |
| **D8 constraint-completeness (§13.2b): {A1,A2} × C1 prompt, r=3** | P1 | **40 defects → ≈240 trials** as approved (D8d); **realised 37 defects → 222 trials** at N = 142, because the subset uses the same per-operator stride as the arm subsets and six floors cost three defects. Per D8b the cell reuses the **same C0 base**, so it buys no extra generation pass. Run it with `--c1` |
| Severity sweep: O1 two levels × a third of the set, r=3 | P1 | ~100 |
| *(optional)* P3 exploratory: A1, r=3 | P3 | ~100 |

⚠ The old grid's "O4 three levels" severity sweep is **dead as a repair cell** —
O4 produces no retry, so there is nothing for an arm to act on. An O4 severity
sweep measures *detection*, and belongs with C6 below.

⚠ **Amended 2026-09-02 by D19 (§3.7).** That paragraph is right about the
*production* routing and wrong about what follows from it. O4 produces no retry
**because §4.5 decided it should not**, and that decision has no counterfactual
anywhere in either paper. Routing it to retry deliberately, as a cell that is
not part of the production path, measures what the overwrite bought:

| Cell | Placement | Size |
|---|---|---|
| **D19 overwrite counterfactual: O4 × {A1, A3}, r=3** | P1 | **23 defects → ≈138 trials.** Not pooled into the primary contrast |

A2 is omitted on purpose: the cell is about the *routing* decision, not about
feedback content, so it needs a best case (A1) and a floor (A3) and nothing
between them.

P1 is measured by the core, so the placement row buys the other two levels and
the three-level contrast **P0 vs P1 vs P2** comes out whole. See D9 in §3 for
why P0 has to be named.

Detection-side calibration (C6) is free: run `measure`/`decide` over every
injected output offline — above-threshold severities confirm ~100% detection by
construction; sub-threshold ones trace each check's detection curve. The
injector already cross-checks itself against `supervision.measure` on all 137
applicable injections.

**Budget.** ⚠ A trial is **1–3 LLM calls, not 1** — a schema failure appends the
model's own invalid output and re-asks, which is why `attempts_made` is logged
per trial. After D11b the core is ≈1,180 trials = **≈1,180–3,540 calls**. Add
the C1 cell (240 or 480 trials, D8d) and the placement, severity and P3 cells,
and the study as planned is **≈1,660–2,000 trials ≈ 1,700–6,000 calls**. At
~24 s/stage-call (597.3 s mean run ÷ ~25 calls for a p90 business) the core
alone is **8–24 h of pure inference**: three to five nights unattended with
429/503 backoff, on the checkpointed runner. ⚠ **Check the API budget before starting** —
`out_study/B/checkpoint.credit-depleted.jsonl.bak` records this ceiling being
hit once already. Rate limits and credit, not wall-clock, are binding.

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
- ⚠ **Tier-1 blocking is over ~7 clusters, not 13 defects** (§5; figures
  refreshed 2026-09-02 from `defect_bank.py` — 11 in 5 cells before D11b). The
  13 usable instances sit in 7 business × stage cells across 6 businesses, with
  up to 4 observations in one cell. Blocking on defect identity alone treats near-duplicates as independent
  blocks and re-narrows the CIs the blocking was introduced to widen. Nest
  repeated observations inside the cell, or report the Tier-1 rate as a
  descriptive count with the cluster structure printed next to it. Decide which
  before running, not after seeing the width.
- Outcome reported as a **4-class multinomial** {`repaired`, `replaced`,
  `deleted`, `unrepaired`} **crossed with a binary collateral flag** (D3b as
  amended by D18). The *original* four classes were not mutually exclusive
  (`collateral` overlapped `repaired_clean`) and so could not be a multinomial
  at all; these four are, because they are decided in a fixed order. Plus the
  two-stage chain *did the output change at all → did the targeted defect
  resolve* (MAS-FIRE's O/L decomposition; global-success S stays out of scope).
  **The dichotomy the confirmatory tests run on is strictly `repaired`**:
  `deleted` counts against it (D18), and `deleted` is structurally unreachable
  for the insertion operators O6/O7, where removing the item is the repair.
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
| 2 | **Phase-0 memo → supervisor sign-off on D1–D17.** Seven block work (⛔ in §3): D8, D8c, D9b, D10, D4b, D4c, D12. **D11b and D8b were decided 2026-08-26** (grow the sample; one shared C0 base). **D8d approved and D13 executed 2026-08-26.** One remains open (❓): **D5b** local model identity | 🟨 in progress |
| 2 | B1/B1b/B2 instrumentation; B3 replay entry point; defect-bank inventory | ✅ done 2026-08-24 |
| 2–3 | Build B4 (operators), B5 (arms × placement), B6 (scorer), B7 (runner), B8 (C1 audit **and the C1 prompt**, 2026-09-20) + golden tests incl. the §13.5 replacement-value test | ✅ |
| 3 | Tier 1 runs (**132** trials, P0) + preliminary analysis → go/no-go | ✅ ran 2026-10-08 as 117 trials (A0 undefined at P0) — prereg A8; the go/no-go step was overtaken by the frozen pre-registration |
| 4 | Tier 2 grids (~980 calls, 3 nights) + analysis | ✅ ran 2026-10-05 → 08: core 1,167 trials, then D19, C1, placement, severity, warm and downstream — `RESULTS.md` |
| 5 | (stretch) local deterministic arm — now higher value, see §14.1 | ⏳ C7: model recommended 2026-10-08 (Qwen2.5-7B-Instruct Q4_K_M, Ollama, RTX 5060); waiting on the author's server |
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
  ⚠ **The frequency half of that is reversed by D19 (§3.7), 2026-09-02.** Framed
  as a warn-level sub-experiment it was scope creep; framed as the missing
  counterfactual for §4.5's overwrite decision it is ≈138 trials that put a
  measurement under a design principle the conference paper currently only
  asserts. The judge re-runs remain out of scope.
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
- **Scale is acceptable here.** One system, **28** workloads and **~1,180** injection
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

✅ **DECIDED 2026-09-02 by D20 (§3.7): dropped from the denominator and reported
as a separate count.** Counting an untriggered defect `unrepaired` would score
the arms on a trial where the arms are *identical by construction* — no retry
fired, so no feedback of any kind reached the model, so A1, A2 and A3 are the
same condition. The count is reported next to the rate, never folded into it.
Both gates run at plan time, before any call is spent (D20).

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


---

## 15. Defect-bank audit results (D13) — executed 2026-08-26

**This section reports a completed measurement. Where §5 or §13 assume the
Tier-1 bank is a realism anchor for Tier 2, this section supersedes them.**

Reproduce with, from `backend/`:

```
venv/Scripts/python.exe scripts/analysis/rater_sheet.py --score out_study/audit     --a out_study/audit/rating_a.csv --b out_study/audit/rating_b.csv
venv/Scripts/python.exe scripts/analysis/verify_claims.py
venv/Scripts/python.exe scripts/analysis/verify_claim2.py
venv/Scripts/python.exe scripts/analysis/verify_claim3.py
```

### 15.1 Reliability

Two **human** raters, independently, on the 31-item blinded sheet
(11 Tier-1 + 20 Tier-2, seed 20260826).

| | |
|---|---|
| Cohen's κ | **0.870**, 95% CI **[0.674, 1.000]** (bootstrap, 5,000 resamples) |
| Raw agreement | **29/31** |
| `U` (unratable) | **0** — the escape hatch was never needed |

Report the CI, or raw agreement and n. Both disagreements were later resolved
mechanically (§15.3), giving **31/31**; report that as a *resolved* figure, never
as the blind κ.

### 15.2 The result — meaningfulness separates by MECHANISM, not by tier

| | n | both raters called it an error |
|---|---|---|
| **Tier 1 — real, production-caught defects** | 11 | **0 (0%)** |
| **Tier 2 — injected** | 20 | 16 (80%) |

Per operator, after resolving §15.3:

| Operator | what it does | verdict |
|---|---|---|
| **O1** | drops one character from a **real** evidence id | **4/4 technicality** |
| O2 | appends a **fabricated** id | 4/4 error |
| O3 | mislabels a pattern's aspect | 3/3 error |
| O5, O6, O7 | inject content alien to the corpus | 9/9 error |

**O1 lands with Tier 1, not with its own tier.** Corruption and paraphrase
misses are technicalities; fabrication, mislabelling and alien content are
errors. O1 is therefore the only operator producing production-like defects.

### 15.3 Verification of the raters' reasoning

The raters' discriminator was *corruption of a real id* vs *fabrication*. It is
mechanically checkable, and the check is unambiguous — edit distance to the real
corpus is **bimodal with nothing in between**:

| | items | min edit distance to a real review id |
|---|---|---|
| Tier-1 `missing_evidence_id` | 3 | **1–2** (corruption) |
| O1 injected | 4 | **1** (corruption) |
| O2 injected | 4 | **20** (fabrication) |

Rater A was right on **11/11**, rater B on **9/11**. B's two errors (I10, I27)
came from searching *the sheet* for a near-neighbour rather than the corpus: on
those two items the source id was not cited in any other item, so B saw no
neighbour and inferred fabrication. Both disagreements resolve in A's favour,
confirmed independently by `inject_defects._apply_o1`, which deletes exactly one
character from a real resolving id.

⚠ **Instrument limitation to fix before any reuse:** the sheet gives the rater no
way to test for a near-neighbour. A future sheet should either include the
corpus id list or pre-compute the nearest-real-id distance as a stated fact.

**Stray-citation ratios** (`misaligned_aspect` vs O3), within the *flagged*
pattern:

| | mismatching citations |
|---|---|
| Real `misaligned_aspect` | 1/27 and 1/33 — **~3%** |
| Injected O3 | 13/13, 7/7, 3/3 — **100%** |

### 15.4 ⚠ The finding: `untraceable_recommendation` is a precision failure

Six of the 11 Tier-1 defects are `untraceable_recommendation`, and both raters
independently called them **checker false negatives**. That is confirmed.

`supervision._measure_strategy` scores an issue against upstream with
`difflib.SequenceMatcher` — a **character-level** ratio — against
`TRACE_SIMILARITY = 0.35`.

| | lexical score (what the check uses) | content-word overlap |
|---|---|---|
| Real defects (6 Tier-1 items) | **0.23 – 0.35** | 0.08 – 0.44 |
| Injected O5 (alien content) | **0.21 – 0.28** | **0.00, all three** |

**The lexical bands overlap completely.** The check cannot separate
"Negative ambience." from an upstream pattern reading *"the restaurant's
ambience is often described negatively"* (0.23, fails) from "till float count
skipped" against a staff-attitude complaint (0.21, also fails). Content-word
overlap separates them perfectly on this sample.

⚠ **One honest caveat.** I14's third issue ("Excessive customer wait times.")
has a best content-word overlap of **0.08** — that dump appears to carry no
strong wait-time upstream item, so that single issue may be genuinely
untraceable. Two of its three map cleanly; the raters' blanket "all three" is
slightly generous.

### 15.5 Consequences — three, and none of them are cosmetic

1. **9 of 11 production defects are checker false positives with a diagnosed
   cause** (6 paraphrase misses, 3 single-character id corruptions where the
   real evidence exists). The other 2 are ~1-in-30 stray citations.
2. **Fixing the matcher shrinks the Tier-1 bank.** Content-word overlap
   separates the sample perfectly, but re-running `defect_bank.py` afterwards
   would likely take the bank from 11 toward ~2–5 — and Tier 1 is both the
   replay tier and the realism anchor. **Measure this before deciding.**
3. **Conference paper #1 is under review and this touches its numbers.** Its
   retry counts embed this false-positive rate, uncharacterised. Whether that is
   a note to the chairs, a camera-ready limitation, or a journal-paper finding is
   a **supervisor decision** — see `PHASE0_MEMO.md` §11.

### 15.6 What this does to the repair study

- **The Tier-1 realism anchor anchors in the opposite direction.** Tier 2 minus
  O1 is markedly *more severe* than anything the supervisor catches in
  production, so the headline repair rate **cannot be read as a production
  repair rate**. State this in the design, do not concede it in review.
- **Do not pool O1 with O2–O7.** Report O1 as the production-like cell and the
  rest as the severe cell. The audit is the evidence that justifies the split.
- The estimand is narrowed, not invalidated: repair of *human-recognisable*
  injected defects remains a well-posed and measurable quantity.


---

## 16. Delivered numbers after the D11b collection (2026-08-26)

**Supersedes every figure in §5, §6 and §15 computed over 20 dumps.** The 8
extra Phase-A dumps D11b approved were collected on 2026-08-26 in observe mode.
Everything below is what a script printed, not a projection.

### 16.1 The collection

8 of 8 completed, ~49 minutes, `mode=observe`, `status=complete`, no skipped
agents, and **`loaded_review_count == expected_review_count` on all 8** — no
truncation. Two transient 503s on the first business self-recovered.

⚠ **The 503 business contributes zero defects, correctly.** Honey Baked Ham
Company recorded `status_error=True` at `reasoning_agent` (excluded: `api_error`)
and its `report_agent` entry is the downstream **cascade** (excluded). Identical
in shape to Scarpetta in the original 20. The bank's existing rules handled it
with no intervention.

⚠ **Second serving epoch.** The original 20 ran 2026-08-03, these on 2026-08-26,
and the checkpoint does not record the model. §14.1 already covers this — all
arms for one defect run in one session at trial time — so it does not confound,
but it belongs in the methods section.

### 16.2 Predicted vs delivered

| Quantity | predicted | **delivered** |
|---|---|---|
| Dumps | 28 | **28** |
| Tier-2 ceiling (N) | ≈143 | **142** |
| Yield per dump | 5.1 | **5.07** |
| Core trials | ≈1,180 | **1,167** |
| Replay fidelity | — | **159 facts, 0 mismatches** |

Arms allocate **A1 426 · A2 426 · A0 213 · A3 102**; the order invariant holds.
Per-operator applicability is now **O1 24 · O2 24 · O3 22 · O4 23 · O5 20 ·
O6 26 · O7 26 · O8 26**, 191 across all eight, **142** with a repair endpoint.

### 16.3 Tier 1 grew, and grew in its worst class

| | before | **after** |
|---|---|---|
| Retry observations | 15 | **19** |
| Excluded `api_error` | 3 | **4** |
| Cascades | 1 | **2** |
| **Usable defects** | 11 | **13** |
| By stage | strategy 6, reasoning 5 | **strategy 8, reasoning 5** |
| Distinct cells / businesses | 5 / 4 | **7 / 6** |

The clustering improvement is real and welcome — the old cluster bootstrap
over-rejected at 0.086 against a nominal 0.05 on 5 cells.

⚠ **But both new defects are `untraceable_recommendation`, taking that class to
8 of 13.** §15.4 showed that is precisely the class the trace matcher gets wrong.
**The bank grew in proportion to its least trustworthy class**, which strengthens
`PHASE0_MEMO.md` §11 rather than weakening it.

### 16.4 ⚠ NEW — the matcher is wrong in the OTHER direction too

`tests/test_inject.py::test_corpus_margin_is_reported_not_assumed` is a tripwire
on how close the injected O5 corpus issues come to tracing. **It fired.**

Worst-case `difflib` similarity across 28 dumps is **0.444** — *above* the 0.35
trace threshold, not merely near it — and **16 pairs now sit at or above
threshold**. The worst offender:

| injected issue | upstream candidate | difflib | content-word overlap |
|---|---|---|---|
| `uniform size profile absent` | `Unpleasant or undesirable atmosphere` | **0.444** | **0.00** |

That injected string is **D13 item I28**, which *both* blinded raters called an
error, noting it has no connection to any upstream content. Content-word overlap
agrees at 0.00. The character matcher scores it 0.444 and would call it traceable.

**So §15.4's finding generalises: the matcher misses real paraphrases AND matches
unrelated strings.** Both failures have the same cause — it compares characters,
not content.

The study is **not** silently broken: `_o5_issue` stops selecting an
over-threshold issue and O5's applicability absorbs it (hence O5's 20, the
lowest of the six). But the margin the tripwire guarded is gone.

⚠ **Do not "fix" this by editing `CORPUS_ISSUES`.** D13 rated those exact
strings; changing them severs the audit from the operators it audited.

### 16.5 Status of the power gate

Recomputed at the delivered N=142, r=3, `--sims 20000`, seed 42:

| | power | w/ occasion | MDE | **MDE w/ occasion** |
|---|---|---|---|---|
| 142 x r=3 | 0.912 | 0.875 | 10.2 pp | **10.9 pp** |

**PASS — 10.9 pp against D11b's 12 pp threshold, margin 1.1 pp**, under the
shared-occasion effect the design will actually face. At N=102 the MDE was
12.6 pp, i.e. *above* the threshold, which is what made the pre-registration
incoherent. It is coherent now.

The prediction reproduced: 0.883 / 10.8 pp predicted against 0.875 / 10.9 pp
delivered, both inside the estimator's own error (power ±0.01, MDE ±0.3 pp).
Per §14's trap 35, that is reproduction, not drift.

⚠ **The PASS is provisional.** N=142 was computed through the same broken
matcher: `applicable()` rejects O5 bases via
`no_corpus_issue_below_trace_threshold` and
`base_not_clean:untraceable_recommendation`, both routed through
`TRACE_SIMILARITY`. **O5 contributes 20 of the 142**, and the direction of a fix
is genuinely uncertain — fewer falsely-unclean bases pushes O5 up, fewer
genuinely non-tracing corpus issues pushes it down. With only 1.1 pp of margin
this is not comfortable slack. §16.6 bounds it.

### 16.6 O5 sensitivity — the power gate survives the matcher fix

§16.5's PASS was provisional because N=142 is computed through the matcher
§15.4 and §16.4 show to be broken. **O5 contributes 20 of the 142**, so the
exposure is bounded by O5 going to zero (N=122) or growing modestly. Swept at
`--sims 20000`, seed 42, over a range deliberately wider than that:

| defects | r=3 power w/ occ | **r=3 MDE w/ occ** | margin vs X = 12 pp |
|---|---|---|---|
| **120** (worse than losing O5 entirely) | 0.823 | **11.7 pp** | 0.3 pp |
| 130 | 0.845 | **11.3 pp** | 0.7 pp |
| **142 (delivered)** | 0.874 | **10.8 pp** | 1.2 pp |
| 150 | 0.895 | **10.6 pp** | 1.4 pp |

**The gate holds across the entire plausible range.** Even at N=120 — below the
worst case of O5 vanishing completely — the MDE stays under the 12 pp threshold.
**The pre-registration remains coherent however §11 is decided**, so fixing the
matcher does not force a re-plan.

⚠ **One honest qualification.** At N=120 the margin is **0.3 pp**, which is the
same size as the MDE's own Monte Carlo error. At the bottom of the range the
gate "clears" only within noise. If a matcher fix takes N below ~130, the
contingency is **r=4**, which buys MDE ≤ 10.4 pp everywhere in this range at the
cost of more trials — and that decision can be made *after* §11, without redoing
anything already run.

⚠ **Do not read 10.8 pp here against 10.9 pp in §16.5 as a correction.** Same
seed, but a different `--defects` list draws a different RNG stream; the gap is
0.1 pp against a ±0.3 pp error. Trap 35 again.

---

## 17. Q1 and Q2 decided — the matcher, and paper #1 (2026-09-14)

`PHASE0_MEMO.md` §11 asked two questions. **Q2 was answered directly. Q1 was
measured first and decided on the result**, as the memo recommended. Reproduce,
from `backend/`:

```
venv/Scripts/python.exe scripts/analysis/matcher_shrinkage.py
```

Pinned by `tests/test_matcher_shrinkage.py` — one test per premise of D22.

### 17.1 D23 — paper #1: a journal-paper finding

Paper #1 stands as submitted, with no note to the chairs. The trace-matcher
defect, its diagnosis and its measured consequences are reported in the journal
paper as a finding about the supervisor paper #1 describes. Paper #1's retry
counts are not restated anywhere as "corrected" numbers; the journal paper gives
the false-alarm rate that sits inside them (§17.2).

### 17.2 What the measurement found

The content matcher is word-level Jaccard over content words — the tokeniser of
`verify_claim3.py`, i.e. the statistic §15.4 already reported — at 0.10.

| | shipped: `difflib` ≥ 0.35 | content: Jaccard ≥ 0.10 |
|---|---|---|
| **Tier-1 usable defects** | 13 | **6** |
| of which strategy (`untraceable_recommendation`) | 8 | **1** |
| of which reasoning (matcher not involved) | 5 | 5 |
| observe-mode strategy outputs flagged (Phase A + repetitions) | 8 of 49 | 1 of 49 |
| issues flagged, of 297 | 13 | 1 |
| flags the shipped matcher did not raise | — | **0** |
| frozen O5 alien issue called *traceable*, issue × base | **6 of 168** | 0 of 168 |
| O5 applicable bases → Tier-2 N | 20 → 142 | 25 → 147 |

Four results carry the decision.

1. **Every issue the shipped check flagged in production shares content words
   with upstream** — containment 0.25–1.00 across all 13. Twelve of the 13 trace
   under the content matcher. The thirteenth, *"Excessive customer wait times."*
   in D13 item I14 (Jaccard 0.08), is the one issue §15.4 already singled out as
   possibly genuinely untraceable. The production flags are false alarms, and
   the single exception is the one the audit predicted.
2. **The shrinkage is 13 → 5–6, and it does not hinge on the threshold** — for
   every content threshold that raises no new flags. Lenient matchers
   (containment > 0, Jaccard ≥ 0.05) give 5; Jaccard ≥ 0.10 gives 6. Stricter
   ones are worse than the shipped check in the other direction: containment ≥
   0.34 raises 3 new flagged stages and ≥ 0.50 raises 11, on real paraphrases.
   The memo forecast ~2–5. **The floor of 5 is the reasoning-stage defects,
   which never consult the matcher — and D13 rated all 6 survivors
   technicalities.** Under the fix, Tier 1 holds no defect a human called an
   error.
3. **The bug does not reach the study's manipulation.** All 20 O5 bases are
   clean under the content matcher as well, and none of the 60 injected O5
   issues (seeds 0, 1, 42) shares a single content word with upstream. The
   trigger and the A1 feedback text are therefore identical under either matcher.
4. **It does reach the study's measurement.** `score_repair.score` decides
   whether O5's check still fires by re-running the production check on the
   regenerated output. That check flags 8 of 49 *correct* observe-mode strategy
   outputs — the best available estimate of how often a correct regeneration in
   the O5 cell (20 of the 142 defects in the pooled primary) would score
   `unrepaired`, in every arm. In the other direction it calls alien content
   traceable in 6 of 168 issue × base pairs. (§16.4's "16 pairs" counts issue ×
   *candidate*; it is the same 6 issue × base pairs.)

**Why Jaccard ≥ 0.10 and not the lenient matchers.** Containment > 0 and
Jaccard ≥ 0.05 each trace one alien pair: *"uniform size profile absent"*
against *"…portion size…"* on the single shared word "size" (Jaccard 0.06).
0.10 is the only threshold tested that is right in both error directions. **It
was chosen on pre-study calibration data, before any trial outcome exists** —
the same standing as the D3c churn floors — and is disclosed as chosen that way,
with the lenient matchers reported as sensitivity.

### 17.3 D22 — keep the supervisor, correct the measurement

1. **The production supervisor is unchanged for the study** — `supervision.py`
   and its offline twin `eval/tier1_checks.py`. The bug does not reach the
   manipulation (finding 3). Q2 keeps paper #1 as submitted, so the system under
   study stays the system paper #1 describes. The replay gate (159/0), N = 142
   and the 1,167-trial plan all stay valid. And a production threshold fitted on
   13 flagged issues is too thin to ship.
2. **The scorer is corrected where the bug reaches the outcome.** O5's "check
   still fires" is decided by the content matcher; the production verdict is
   logged beside it and reported as a secondary. `PREREGISTRATION.md` §2.3.
3. **Tier 1 is reported both ways** — 13 under the shipped check, 6 under the
   content matcher — and its strategy-class defects are described as checker
   false alarms, not as repair targets. The realism ladder's replayed-real rung
   (§5) is 5–6 defects, all rated technicalities, so it is descriptive only.
4. **The production fix is deferred, not declined:** after the study, as a
   versioned change with the replay facts re-baselined. The journal paper reports
   the defect, the diagnosis and the measured effect of the fix.

### 17.4 ⛔ What this opens before the freeze tag

`PREREGISTRATION.md` §11 item 5 — two tasks, in order.

1. **Build** the O5 content trace in `score_repair.py`, with the production
   verdict kept as a logged secondary, and tests.
2. **Calibrate O5's two other character-level comparisons in the scorer** —
   `_item_restored` (pre- vs post-injection issue ≥ 0.35) and the `action`
   identity anchor — which carry the same paraphrase exposure. D3d measured
   exact-match rates of ≈ 0 across identical runs, so it is likely material.
   Calibrate on repetition pairs the way D3c did, then decide. ⚠ **Leave the churn
   metric's matcher alone:** the D3c floors were calibrated with it, and changing
   it would silently invalidate them.

### 17.5 D24 — item 5 closed: O5's anchor on content words, restoration unchanged

Calibrated on the repetition runs, the only pre-study data in which the same
business is regenerated from the same inputs. `category` cannot serve as a
ground-truth key — 0 of 24 outputs have unique categories ("operations" alone
appears 72 times) — so pairing is at **business** level: an upstream-stable
same-business rerun should find counterparts, and a cross-business pair should
mostly not. The scorer's O5 decision was replayed exactly: locate the host by
`action`, then test restoration on `issue`, with the check assumed passing.

| anchor | restoration | same-business re-draw: repaired / replaced / deleted | cross-business: repaired / deleted |
|---|---|---|---|
| lexical ≥ 0.35 (shipped) | lexical ≥ 0.35 | 24% / 6% / **70%** | 10% / 81% |
| Jaccard ≥ 0.10 | lexical ≥ 0.35 | 73% / 20% / 7% | 52% / 9% |
| **Jaccard ≥ 0.20** | **lexical ≥ 0.35** | **68% / 14% / 17%** | **41% / 31%** |
| Jaccard ≥ 0.30 | lexical ≥ 0.35 | 51% / 10% / 39% | 21% / 61% |

Recommendation counts barely move between stable reruns — identical in 11 of 13
pairs, mean difference 0.15 — so a `deleted` in a same-business re-draw is almost
always false.

1. **Anchor → content Jaccard ≥ 0.20.** The rule was stated before the choice:
   the lowest false-deletion rate among matchers whose within-output ambiguity is
   no worse than the shipped matcher's (3%). The shipped anchor scores 70% of an
   unperturbed re-draw `deleted`, and the error is placement-linked — A3 re-draws
   at P0, while A1/A2 see the artifact at P1 and can copy it — so it would have
   biased the A2-vs-A3 test rather than added noise. Jaccard ≥ 0.10 fails the
   ambiguity rule (40%); ≥ 0.30 still deletes 39%.
2. **Restoration stays on the production matcher.** Under the chosen anchor it
   separates same-business from cross-business best: 68% vs 41%, a 27 pp gap,
   against 18 pp for Jaccard ≥ 0.20 and 22 pp for ≥ 0.30. No calibration supports
   switching it.
3. **O5's repaired/replaced line is weak under every matcher tested** — a
   different restaurant's recommendation "restores" 41% of the time, because
   recommendation issues are generic. Two sensitivity analyses are therefore
   pre-registered (`PREREGISTRATION.md` §3 item 8): the pooled primary without
   O5 (N = 122), and O5 with `repaired` ∪ `replaced` as success.
4. **The reasoning operators are not exposed.** Best-match location on
   `description` finds 97% of patterns in a re-draw under the shipped matcher, so
   O1–O4 keep it. (The 0.33 churn floor measures one-to-one matching, which is a
   different and stricter rule.)

Built: `content_match.ANCHOR_JACCARD`, `score_repair.CONTENT_ANCHORED = {"O5"}`,
and `anchor_matcher` logged on every trial. Tests pin both the reworded-action
case and that deletion is still detected.

### 17.6 ⛔ NEW — A3 at P0 is not a floor for injected defects (open)

Found while calibrating §17.5 and **confirmed in the code, not inferred.** A3 is
the original prompt with nothing added and exists only at P0 (D9b,
`arms.UNDEFINED_CELLS`). At P0, `arms.build_messages` leaves the injected output
out of the context entirely (D10), and `_regenerate` builds the stage input from
the base state's pinned upstream. **So an A3 trial is a fresh, clean
regeneration of a stage whose synthetic defect the model has never seen.**

The A3 prediction ("near zero or negative", §5 of the pre-registration) and
`power.py`'s `p(A3) = 0.05` come from Self-Debug Table 3b and Huang's intrinsic
rows — work on **self-generated** errors, which a temperature-0 re-draw tends to
reproduce. An injected error it cannot reproduce.

Estimated without an API call by `scripts/analysis/a3_redraw.py` (pinned by
`tests/test_a3_redraw.py`): inject into one repetition run, and score an
independent repetition of the same business as the re-draw, with the study's own
scorer.

| operator | O1 | O2 | O3 | O5 | O6 | O7 | O4 (D19 cell) |
|---|---|---|---|---|---|---|---|
| A3 scores `repaired` | 29% | 26% | 5% | 45% | **100%** | **100%** | **93%** |

**Pooled over the N = 142 mix: A3 repairs ≈ 53%.** `power.py` assumes 5%, A2 33%
and A1 45%. Two limits, in opposite directions of trust:

- **O6/O7 are exact by construction** — an invented corpus item cannot appear in
  a draw that never saw it. Those 52 of 142 defects put a **37% floor** under
  pooled A3 that does not depend on the approximation at all.
- **The reasoning-operator figures are low, not high.** Repetition runs
  regenerate the analysis stage too, so a reasoning "re-draw" sits on different
  analysis output from its base, which inflates `unrepaired`. O3's 91% is mostly
  that.

**What it touches.** The A1 − A2 primary does **not** move: both arms run at P1.
But four pre-registered things rest on the wrong assumption:

1. **Confirmatory test 3, A2 vs A3** — predicted A2 > A3 by 28 pp, likely to come
   out reversed, for a mechanical reason rather than a behavioural one.
2. **The §5 A3 prediction**, and `power.py`'s A2-vs-A3 power.
3. **The pre-committed negative result** — "if A1 ≈ A3, that is a publishable
   finding against the self-correction literature" — could be triggered by this
   artifact and reported as a headline.
4. **D19's cell, O4 × {A1, A3}** — A3 repairs frequency ~93% by re-drawing, so it
   is no floor there either.

**The decision this needs, before the freeze.** The options:

- **(a) Re-role A3 as a regeneration baseline.** Keep the arm and its 102 trials,
  but for Tier 2 describe it as what a fresh draw does to an injected defect;
  move A2 vs A3 from confirmatory to secondary (Holm over two tests); withdraw the
  near-zero prediction and the negative-result clause for Tier 2. No new wording,
  no code change. Cheapest.
- **(b) Add the control test 3 actually needs: artifact shown, no rejection.**
  A new arm at P1 that re-presents the injected output and asks for the stage
  again with no judgement attached. A2 against that arm isolates the rejection
  signal with the artifact held fixed — which is what "the bare trigger" means
  once the defect is injected. Needs new frozen wording in `arms.py`, a power
  assumption with no literature behind it, and roughly A3's trial count. A3 at P0
  can stay as the descriptive baseline from (a), or be dropped.
- **(c) Keep everything as it is.** Rejected: the prediction and the power
  assumption are mechanically wrong, and a pre-registration that knowingly
  freezes them is worse than none.

### 17.7 D25 — A3 re-roled as a regeneration baseline (author, 2026-09-14)

Option (a) of §17.6, adopted. `PREREGISTRATION.md` §11 item 6 records it, and the
pre-registration was frozen at the annotated tag `prereg-freeze` the same day.

1. **A3 is a regeneration baseline, not a floor.** The arm, its wording, its P0
   placement and its 102 trials are unchanged; only its interpretation changes.
2. **The confirmatory set is the single A1-vs-A2 McNemar test, at α = 0.05.**
3. **A2 vs A3 moves to secondary**, read as *re-presenting the defective output
   with a contentless rejection versus regenerating from scratch*.
4. **The §5 A3 prediction is corrected** and the pre-committed negative result
   ("if A1 ≈ A3 … headline") is withdrawn for injected defects.
5. **D19 reads A1 against overwrite**, with A3 beside it as what regeneration
   alone gives. §7's "O4 × {A1, A3}, P1" contradicted the code — A3 is defined
   only at P0 — and now says so.

⚠ **One consequence went a step past option (a) as §17.6 worded it.** Option (a)
said "Holm over two tests": Cochran's Q plus A1 vs A2. But Q is an omnibus over
the matched arms, A3 among them, so an A3 that mechanically scores ≈ 53% would
make Q reject for the same artifact that disqualified test 3. **Q therefore moves
to secondary as well, leaving one confirmatory test.** That also repairs a
mismatch nobody had noticed: `power.py` computes every MDE at an unadjusted
α = 0.05 (`ALPHA = 0.05`, no Holm), so under the three-test Holm set the primary
test would have faced a stricter threshold than its power was computed for.

**What this supersedes in this plan:** D4's "exactly three confirmatory tests"
(and its differing list, which already disagreed with the pre-registration); the
"Exactly three confirmatory tests under Holm" sentence in §8; and the A3 row of
the §13.3 prediction table. The pre-registration wins where they disagree.
