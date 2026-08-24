# Journal Extension Plan — Injected-Defect Repair Study

**Written:** 2026-08-24 · **Amended:** 2026-08-24 after the Tier-A reading and Tier B in full — 9/9 read (see §13, §14)
(extraction: `..\Reading List\Tier_A\Tier_A_extraction.md`) — D1 reversed,
arm set extended, statistics refined · **Status:** proposed, not yet agreed with supervisor
**Relationship to other docs:** the conference paper is finished
(`main.tex`, see `NEXT_SESSION.md`). This plan covers the journal extension
only. Where it cites conference results it cites them as fixed.

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

| # | Decision | Recommendation |
|---|---|---|
| D1 | Context placement of the defective output | **REVERSED 2026-08-24.** Default A1 = **production-faithful**: measured-fact feedback in the user turn, defective output **not** shown as the model's own prior turn (matches deployed `_with_feedback`). SC-Bench measured this exact manipulation — identical error, assistant vs user turn — and found a 64.5% blind spot across 14 models (62.8% non-math): assistant-turn attribution *suppresses* correction. All eight of Olausson's repair prompts independently use user-turn framing. Placement becomes measured factor P on a Tier-2 subset: **P1** = defective output added to the user turn as an artifact under review; **P2** = defective output as the model's own assistant turn; optional **P3** = P2 + correction marker ("Wait", which closes 89.3% of the gap via a near-independent pathway). |
| D2 | Arms | **A0** = capability ceiling (NEW — SC-Bench's external condition): the same defect presented to the same agent as a fresh user-turn correction task, no retry framing; bounds what any feedback can achieve, and the headline becomes the A1/A0 ratio. **A1** = measured-fact feedback (production `_SUPERVISOR_FEEDBACK_PROMPT`); **A2** = generic rejection, no specifics; **A3** = bare re-draw — **declared** as measuring prompt determinism at temperature 0, not resampling (Tyen §4(d): they needed temperature 1 and up to 8 loops to force a *different* step); optional warm-resample subset (temp > 0) carries the Olausson budget comparison. No-injection control = the recorded clean Phase-A verdict of every output injected into (a design property; state it). Best-of-k curves still free from A3 repetitions. |
| D3 | Success criterion (frozen before runs) | Supervisor verdict on the retried output is `proceed`/`proceed_with_warning` **and** the injected defect's descriptor no longer fires. Outcome taxonomy: `repaired_clean` / `replaced` (different retry-triggering defect) / `unrepaired` / `collateral` (defect fixed, but non-defective items materially changed). |
| D4 | Primary endpoint | Matched tuples per defect (same defect under every arm) → **Cochran's Q** omnibus; planned **exact-McNemar** contrasts **A1 vs A2** (feedback content) and **A2 vs A3** (bare retry trigger); headline = **A1/A0 ratio** with delta-method CI (SC-Bench Eq. 1 pattern), absolute rates alongside; Wilson CIs on all proportions; **block on defect identity** (replaying one defect across arms makes trials matched, not independent — naive CIs would be too narrow); outcome is a **multinomial** over the four classes, never collapsed; **never pool replayed-real with synthetic in a headline**. Tier 2 provides precision; Tier 1 provides realism; Just-style coupling licenses reading Tier-2 rates. Pre-register: publish whatever the sign is. |
| D5 | Models | Hosted: `gemini-2.5-flash` pinned, **fallback disabled during trials** (a silent `gemini-3.5-flash` failover contaminates arms). Local: one open-weights instruct model via the existing Ollama profile, greedy decoding. |
| D6 | Injection scope | Reasoning, strategy, report stages only — their defects are item-level. Analysis-stage defects (contradiction *rate*) are distributional and upstream of the replay bank; excluded, stated in limitations. |
| D7 | Venue | **Recommendation: EMSE (Empirical Software Engineering, Springer), regular track** — not a special issue. Rationale and alternatives in §12. Confirm with supervisor; check first whether the conference offers an extended-version route (§12.3). |

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

## 4. Phase 1 — instrumentation and harness (~2–3 focused days)

All build items anchor to existing code; golden tests gate each one.

| # | Item | Where / how |
|---|---|---|
| B1 | Token accounting per stage | `BaseAgent._record_usage` already accumulates `total_tokens_used`; snapshot it around each trial call in the new runner. Also record per-call `model` served. |
| B2 | Fallback control | New env flag (e.g. `LLM_DISABLE_FALLBACK=1`) consumed in `BaseAgent._call_llm`; a trial where fallback fired is discarded and logged. |
| B3 | **Replay entry point** — `scripts/replay_stage.py` | Reconstruct `PipelineState`: reviews via `loader.get_business` + seeded `load_reviews` (`MAX_REVIEW_SAMPLE=214` env, same seed — reproducibility is already a passed Tier-1b property); stage outputs from the dump JSONs (`analysis.json`, `reasoning.json`, `strategy.json`, `report.json`). Then run one supervision cycle: stage node (from `nodes.py`, so prompts are the production ones) → `supervision.measure` → `decide`. **Golden test:** replaying every clean Phase-A dump must reproduce the recorded `observations[].facts` from `checkpoint.jsonl` exactly. |
| B4 | **Injection operators** — `scripts/inject_defects.py` | Table below. Deterministic given seed; each application records a ground-truth descriptor for scoring. **O5–O7 insertion content comes from a fixed corpus frozen to disk — generated once, never regenerated per run.** Log per-operator applicability (an operator with nothing to corrupt is recorded, not silently skipped) and an injection success rate. |
| B5 | Arms + placement | A0 = fresh-task correction framing (new prompt template, no retry language). A1 = production `_SUPERVISOR_FEEDBACK_PROMPT`, defective output absent. A2 = fixed generic-rejection string. A3 = plain re-call. P1 = A1 + defective output in the **user** turn as an artifact under review; P2 = A1 + defective output via an optional `prior_output` **assistant** turn; P3 (optional) = P2 + correction marker. |
| B6 | Outcome scorer — `scripts/analysis/score_repair.py` | Classifies each trial into D3's taxonomy from (pre-injection output, injected output, retried output, descriptor). Pure Python, unit-tested. Collateral = any added/removed/altered pattern-or-recommendation beyond the injected one. Emits per-operator applicable-trials denominators. **Must score the replacement *value*, not the disappearance of the original defect** — a swapped-but-still-wrong ID or a differently-wrong frequency is `replaced`, not `repaired`. Golden test for this case required before any trial (§13.5). |
| B8 | **A1 template information-equivalence audit + C1 prompt variant** | Blocks all trials. Diff every supervisor feedback string against the stage system prompt; where the feedback discloses a constraint the prompt omits (all four checked cases do — §13.1), either fold it into a pre-registered constraint-complete prompt C1 or record the delta. Publish C1 verbatim in an appendix. |
| B7 | Batch runner — `scripts/run_injection_study.py` | Clone the `run_study.py` pattern: JSONL checkpoint with fsync, resume-by-skip, `--dry-run`, backoff on 429/503, `status_error` exclusion carried over verbatim. **Iteration order is `for defect: for arm: for repetition:` — never arm-outer.** All arms for one defect must execute contiguously in one session or the matched pairing is confounded with serving epoch (§14.1). Checkpoint granularity = defect, not trial. Record session id + served model snapshot per call; log the terminal supervisor verdict per trial (§14.4) and pre/post facts for **all** checks, not only the injected one (§14.6). |

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
| O8 metadata mismatch | trusted metadata | perturb `business_name` / `sample_size` |

---

## 5. Phase 2 — Tier 1: natural-defect replay

1. **Inventory first** — `scripts/analysis/defect_bank.py` scans
   `out_study/A/checkpoint.jsonl` + `out_study/R/rep*/` for retry-triggering
   observations. **Verified 2026-08-24 against the dumps: 15 stage-level
   instances — 6 from Phase A, 9 from the repetition study** (not 7+8 as
   originally estimated; the headline was right, the split was not).
   ⚠ **Shape is worse than the count.** All 15 fall on the *same 5 businesses*
   (Red Lobster, Izzo's, Nomzilla!, Ameristar, Scarpetta), and stage coverage is
   badly unbalanced: reasoning 7, strategy 6, **report 2, analysis 0**. So the
   Tier-1 arm cannot support a per-stage repair rate for the report stage, and
   stage stratification within Tier 1 is descriptive only — Tier 2 must carry
   the stage comparison. Say this rather than reporting a 15-instance rate as
   though it were 15 independent workloads.
   ⚠ **This also weakens the Just-style coupling argument** (§13, D-real
   "sufficiency" half). Just et al. earned their 73% coupling figure on 357
   isolated real faults; a coupling check over 5 businesses is descriptive, not
   inferential. Report it as descriptive, and let the **necessity** argument
   (SC-Bench §3.1 — injection is what identifies the estimand) plus the realism
   ladder carry the D-real defense. Promising a coupling result at this n and
   then reporting a ratio over 5 workloads is the weakest move available. Each entry: (business, stage, class,
   dump path). **If the bank is < 10, raise repetitions to r=5 and lean harder
   on Tier 2.**
2. Design: every instance × arms {A0, A1, A2, A3} × r=3 → ~180 trials, one LLM
   call each (the retried stage only — repair is judged at that stage by the
   same checks; downstream re-runs are out of scope).
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

| Grid | Trials |
|---|---|
| Core: 8 operators × 20 businesses × A1 × r=2 | 320 |
| Arm ablation: 8 × 5 businesses × {A0, A2, A3} × r=2 | 240 |
| Placement: 8 × 5 × {P1 user-turn artifact, P2 assistant-turn} × r=2 | 160 |
| Severity sweeps: O4 three levels + O1 two levels × 10 businesses × r=2 | ~100 |
| **D8 constraint-completeness (§13.2b): 8 × 5 × {A1,A2} × C1 prompt × r=2** | 160 |
| *(optional)* P3 exploratory cell: 8 × 5 × r=2 | 80 |
| **Total** | **~980 core; ~1,060 with P3** |

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

- Omnibus: **Cochran's Q** over the matched arms per defect; planned
  **exact-McNemar** contrasts A1-vs-A2 (feedback content) and A2-vs-A3 (bare
  trigger); headline = **A1/A0 ratio** with delta-method CI, absolute rates
  alongside; block on defect identity throughout.
- Outcome reported as a **multinomial** over the four classes, plus the two-stage
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
- Placement effect (C5) — stage-level blind-spot test. Pre-registered: **P1 ≫ P3 ≈ P2** (§13.3).
- **Placement × arm interaction**: predicted A1−A2 larger at P2 than at P1; report it, do not average over placement (§13.6).
- **A0 call-count disclosure** — state calls per arm; A0 is a ceiling, not a cost-matched competitor (Huang §4).
- Collateral rate per arm — does feedback cause *less* collateral than a
  re-draw? Plausible and novel either way.
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
| 2 | **Phase-0 memo → supervisor sign-off on D1–D8** (D8 is new and blocks trials) | ⬜ next |
| 2–3 | Build B1–B8 + golden tests (incl. replay-fidelity gate and the §13.5 replacement-value test); defect-bank inventory | ⬜ |
| 3 | Tier 1 runs (~180 trials) + preliminary analysis → go/no-go | ⬜ |
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
- **Contamination.** Fallback-served calls: discard and log (B2). Never mix.
- **Scope creep.** Downstream-propagation measurement, judge re-runs on
  repaired reports, and the warn-level frequency sub-experiment are explicitly
  out of scope unless weeks 5–6 are free.
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
