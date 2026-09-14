# Phase-0 memo — injected-defect repair study

**To:** supervisor · **From:** Hoang · **Date:** 2026-08-25
**Decision requested by:** before the first trial runs. Nothing below can be
revisited afterwards without breaking the pre-registration.

---

## 0. What this memo is

The journal extension is **built and not yet run**. Every script exists, every
gate passes, and no LLM call has been made toward the study.

**Updated 2026-08-26 — ✅ APPROVED.** Three questions are settled: **D11b** (§3)
keep X = 12 pp and grow the sample; **D8b** (§4) one shared C0 base; **D8d**
(§6b) run the C1 cell at 40 defects. The four positions in §7 are ratified.

**Study size as approved:** core ≈1,180 trials + C1 ≈240 = **≈1,420 trials
≈ 1,420–4,260 calls**, before the placement, severity and P3 cells.

**Two things approval did not settle**, and they are the live items:

1. **§5 (D5b) — the local model.** Still open. Not urgent: nothing before
   Phase 4 touches it. Urgent only if we take the ESEM registered-report route.
2. **§7 item 3 — the warm-resample subset.** ⚠ This one asks for a *choice*, not
   a ratification: D2 marks temperature > 0 REQUIRED and it is **not built**.
   Build it, drop it from D2, or defer it — "approved" does not pick one.

**§6 (D13) is ✅ COMPLETE** — executed 2026-08-26, two blinded human raters,
κ 0.870. ⚠ **It found a bug in our own supervisor rather than validating the
bank**, and that raises a new question: **§11**, which is now the most
time-sensitive item in this memo because paper #1 is in review.

⚠ Still nothing spent on the *study*. No dump collected, no trial run. The
audit cost no API calls and no dataset.

**Everything numeric in this memo is emitted by a script**, not typed. Section 9
lists the command that regenerates each figure. That discipline is not
decoration: this project has had citation metadata wrong three times from
second-hand sourcing, and the Tier-2 ceiling was wrong by 57 defects because
someone multiplied 8 by 20 in their head.

It cuts the other way too, and I want to be straight about it. The power figures
carried by hand into the plan turned out to be **right** when finally computed —
both MDEs reproduce exactly. The problem with them was never accuracy; it was
that nothing could re-emit them, so nobody could tell. They can now.

---

## 1. The study in one paragraph

The conference paper (submitted, under review) shows a deterministic supervisor
can *detect* defects in a four-stage LLM pipeline at zero LLM cost. It could not
honestly show that the retry it orders *repairs* them, because natural defects
are rare and uncontrolled. The extension fixes that by injecting known defects
into recorded clean stage outputs and replaying the stage under four different
retry prompts — **A0** a fresh correction task (capability ceiling), **A1** the
production measured-fact feedback, **A2** a contentless rejection, **A3** a bare
re-draw. The primary question is whether A1 beats A2: does the *content* of
measured feedback matter, or does any rejection do?

The literature makes opposite predictions, which is what makes it worth running.

---

## 2. Status — what exists

| | State |
|---|---|
| Tier-1 bank (real defects, replayed) | **13 usable, 2 stages, 7 clusters, 6 businesses** (11 / 5 clusters before the D11b collection; re-verified 2026-09-02) — **descriptive only**, MDE ≈ 31 pp. ⚠ **And see §11: the D13 audit found 9 of the original 11 to be checker false positives**, so this counts what the checker flagged, not what is real |
| Tier-2 injector | 8 operators, **102 defects with a repair endpoint** |
| Arms and placements | built; wording **frozen** 2026-08-25 |
| Outcome scorer | built; discriminates the replacement-value case |
| Batch runner | built and **wired** to live regeneration, 2026-08-25 |
| Trials run | **zero** |

**Gates, all green on 2026-08-26:** 257 tests pass (**266 as of 2026-09-02** —
D18 added 9); the replay-fidelity gate
reproduces 135 recorded facts with 0 mismatches; the injector cross-checks
against the supervisor on all 137 applicable injections; the prompt audit finds
5 of 5 supervisor constraints stated only in feedback; `--dry-run` executes the
entire runner and makes zero calls.

**Cost to run the core:** as the runner stands today, 822 trials × 1–3 calls =
822–2,466 calls. **After D11b (§3) the core is ≈1,180 trials ≈ 1,180–3,540
calls**, roughly 8–24 h of inference; with the C1 cell (§6b) and the additional
placement and severity cells the study is **≈1,700–6,000 calls**. A credit ceiling was hit once during the conference study
(`out_study/B/checkpoint.credit-depleted.jsonl.bak`), so this needs checking
against the budget before it starts, not during.

---

## 3. ✅ APPROVED (D11b) — keep the threshold, grow the sample

**Decided and approved 2026-08-26: option (a).** Keep **X = 12 pp with a 95% CI
excluding zero**, and collect **8 more Phase-A dumps** in observe mode to restore
the margin. The reasoning is below, kept for the record and for the
pre-registration.

It was a question about sample size disguised as a question about a threshold.

`PUBLICATION_STRATEGY.md` says the repair study ships as its own conference
paper if the A1 − A2 effect is large enough, and stays inside the journal
otherwise. The threshold X for "large enough" must be **≥ the minimum detectable
effect**, or the split would rest on an effect the design cannot reliably
detect. I proposed **X = 12 pp with a 95% CI excluding zero**.

**The problem:** at the sample as it stands the MDE is **11.9 pp** — a 0.1 pp
margin under a 12 pp threshold, which is no margin at all. And that is the
optimistic column. Section 14.1 forces all arms for one defect into a single
session, so they share that moment's serving stack and become *more* alike;
under that effect the MDE is **12.6 pp, above the threshold outright**. Either
way the rule "X ≥ MDE" is no longer satisfiable.

| Defects | r | Power | Power w/ occasion | MDE | MDE w/ occ |
|---|---|---|---|---|---|
| **102** (now) | 3 | 0.801 | **0.755** | **11.9 pp** | **12.6 pp** |
| **143** (+8 dumps) | 3 | 0.913 | **0.883** | 10.2 pp | 10.8 pp |

Monte Carlo estimates from `power.py --sims 20000` (seed 42; the MDE bisection runs at 6,666): power carries about **±0.01**, an MDE about **±0.3 pp**. Two significant figures is all that is real.

There are four ways out. Two are honest, one is not, and one is honest but
costs something other than money.

- **(a) Grow the sample — more defects.** Collect **8 more Phase-A dumps** in
  observe mode. Measured yield is 5.1 repair defects per dump, so N goes to
  ≈143, power to 0.883 *including* the occasion effect, and the MDE to 10.8 pp
  — a 1.2 pp margin under a 12 pp threshold, 1.8 pp without.
  ⚠ **The true cost is not the ~30–55 collection calls.** More defects means
  more trials: the core scales at ~2.75 arm-cells per defect per repetition, so
  102 → 143 defects takes the core from **822 to ≈1,180 trials**. Budget the
  collection *and* the ≈360 extra trials (≈360–1,080 calls). It is also the
  **only remaining step that needs the Yelp dataset**.
- **(b) Grow the sample — more repetitions.** Keep 102 defects, run **r=4**
  instead of r=3: MDE 11.2 pp with the occasion effect, ≈1,120 trials, no
  dataset, no collection step. **Almost exactly the same cost as (a) and a
  slightly worse MDE**, because repetitions of one defect are correlated and
  buy less than a new defect does. Worth stating explicitly so the choice is
  visible rather than assumed.
- **(c) Raise X to 13 pp.** This satisfies "X ≥ MDE" immediately, costs nothing,
  and moves in the *conservative* direction — it makes splitting harder, so it
  cannot be mistaken for fishing. Its cost is opportunity: a true 12 pp effect
  is a real, publishable, literature-adjudicating result that we would then
  decline to split, forfeiting the ~6-month conference route and the referee
  feedback that motivated splitting in the first place.
- **(d) Lower X.** Choosing the threshold after seeing what the design can
  detect is exactly what a pre-registration exists to prevent. I do not
  recommend it and would not want to defend it to a referee.

> **Chosen: (a), with (c) as the fallback if the budget will not stretch.**
> (a) buys the MDE margin *and* eight more workloads, which is the only option
> that also answers the "n is small and clustered" objection in
> `PUBLICATION_STRATEGY.md` §4. (b) costs the same for less — repetitions of one
> defect are correlated and a new defect is not, so per call the eighth dump
> beats the fourth repetition. (c) is free and defensible but trades away the
> split, and with it the ~6-month conference route and the referee feedback no
> co-author is supplying.

**What this commits us to.** X stays 12 pp and cannot move after the first trial
runs. The design is **N ≈ 143, r = 3**: power 0.883 and MDE 10.8 pp *including*
the occasion effect, a 1.2 pp margin. The MDE is re-checked against the real N
after collection — if the eight dumps under-yield, the margin is re-examined
**before** any trial, not after.

**What I need from you: two approvals, one small and one not.**

1. **~30–55 calls** to collect 8 Phase-A dumps. Small.
2. **The larger core those dumps imply — ≈1,180 trials rather than 822**,
   i.e. **≈1,180–3,540 calls**. This is the real bill, and an earlier draft of
   this memo wrongly called it negligible.

⚠ These must run in **observe mode**. Enforce mode fires retries and applies
frequency corrections, producing post-retry outputs that are not comparable
injection bases.

---

## 4. ✅ APPROVED (D8b) — one C0 base, shared by both conditions

**Decided and approved 2026-08-26: option (ii).** C0 and C1 use the **same**
injected base; only the retry prompt varies. The budget question it was hiding
is separate, in §6b, and is also settled.

**Background.** The supervisor's retry feedback discloses obligations that the
stage prompts never state — verified programmatically, **5 of 5**, by
`scripts/analysis/prompt_audit.py`. So an A1 > A2 result would be partly
*prompt completeness*, not *feedback specificity*. Two independent sources say
this invalidates the contrast if uncontrolled (Huang et al., ICLR 2024, §5;
Kamoi et al., TACL 2024, Table 7 "Required" row).

The control is a constraint-completeness factor: **C0** the production prompt,
**C1** a prompt that states every supervisor obligation up front, crossed with
A1/A2. C1's text is pre-registered and published verbatim.

**The question.** C1 changes the *stage* prompt, so the clean pre-injection
output would change under it too. Either:

- **(i) regenerate the base under C1** — clean identification, but it costs a
  full extra generation pass and produces bases that are not the ones every
  other cell uses; or
- **(ii) inject into a C0 base and vary only the retry prompt** — cheap, but the
  manipulation is retry-only and the paper must describe it that way.

> **Recommendation: (ii), on a validity argument before a cost one.**
> **(i) breaks the matched design.** Every comparison in this study is matched
> within a defect — that is what §14.1's session rule and D4b's blocking exist
> to protect. Under (ii), C0 and C1 see the *identical* injected base, so the
> C0-vs-C1 contrast is matched exactly like the arms are. Under (i) the two
> cells have different base outputs, and the difference-in-differences is then
> confounded with whatever C1 changed about the clean output — plausibly
> including making it *cleaner*, which is the very thing C1 is supposed to do.
> The cost argument agrees: D8c puts the interaction's power at **0.177** at
> 160/160 defects and **0.300** at 320/320, and neither N is reachable when the
> ceiling is 102. Option (i) buys clean identification of an effect that cannot
> be detected at any affordable size — and buys it by breaking the matching.
> Run C1 as an **estimate reported with a CI**, not a test, and say so.

⚠ **A budget question hides inside this one, and it deserves a separate answer.**
The C1 cell at 80 defects × {A1,A2} × r=3 is **≈480 trials** — **58% of the core
again** — for a quantity we have pre-declared we cannot test. Three positions:

- **Run it as specified.** Huang §5 and Kamoi's Table 7 "Required" row both say
  the A1-vs-A2 contrast is not a specificity claim without it. Publishing C1
  verbatim plus an estimate with a CI satisfies a *design* requirement even
  though it fails as a test.
- **Run it smaller** — 40 defects, ≈240 trials. Halves the cost, widens the CI
  by ~1.4×. Since it is an estimate either way, a wider CI is a smaller loss
  than it would be for a test.
- **Drop it and concede the confound in limitations.** Cheapest, and honest if
  stated plainly — but it hands a referee the exact objection two cited papers
  already raise, and "we knew and did not measure it" reads worse than "we
  measured it imprecisely".

**What this commits us to.** The paper claims *retry-time constraint
disclosure*, not a constraint-complete pipeline, and says so in the Method
section. The C1 cell buys **no extra generation pass** — it reuses the C0 base —
so its whole cost is retry trials. And D8c stands: C1 is reported as an
**estimate with a CI**, never as a test, with the interpretation pre-registered.

**What I need from you:** ratify (ii), or overturn it and fund (i).

---

## 5. ❓ STILL OPEN (D5b) — which local model, exactly?

C7 claims the supervision layer is reproducible on a local open-weights model,
which is the journal's strongest generalisation asset — it is the only answer to
"is this a property of the method or of `gemini-2.5-flash`?" (D15).

The plan currently says "one open-weights instruct model via the existing Ollama
profile". **That is a placeholder, not a decision**, and it will not survive a
referee: reproducibility claims need the model, parameter count, quantisation,
seed and runtime version named before the run, not chosen after it.

> **Recommendation:** pick one and pin all five in the pre-registration. I have
> no strong preference between candidates and would rather you choose on
> whatever you can vouch for, but I need the choice frozen before C7 runs.

Three things constrain the choice more than model quality does:

1. ⚠ **A seed is not determinism.** C7's selling point is a *bit-reproducible*
   headline — and specifically that **A3 (bare re-draw) comes back byte-identical**,
   which is what makes any A1 repair causally attributable to the feedback rather
   than to resampling. On a hosted API that is unprovable; locally it should be
   free. But llama.cpp-family runtimes can vary output with **batch size, thread
   count and GPU-offload layer count**, seed held fixed. So the pre-registration
   must pin those too, and the claim must be verified by running one stage twice
   and diffing — not assumed.
2. **The model has to survive the schema loop.** Every stage demands valid JSON
   against a Pydantic contract, and `MAX_RETRIES = 2`. A model that emits
   near-JSON burns both retries and returns `status: "error"`, which does not
   just cost calls — it removes the base from the study. Structured-output or
   grammar-constrained decoding matters more here than benchmark scores.
3. **It must be an archived, versioned artifact** — a specific published weight
   file with a checksum, not a rolling tag. A referee has to be able to obtain
   *exactly* it in two years.

**Concrete risk:** C7 needs a local Phase A that produces clean, schema-valid
output across 20 businesses. If the chosen model cannot do the reasoning task at
all, there is no base to inject into and C7 dies after the compute is spent.
**Proposal: gate it.** Run the chosen model on **two businesses** first, confirm
schema-valid output at all three stages and byte-identical output on a repeat
run, and only then commit to the full local Phase A. Costs an evening, no API.

**What I need:** a named model + quantisation, or permission to pick one and
record it as my choice — plus a yes to the two-business gate before the full
local run.

---

## 6. ✅ COMPLETE (D13) — the defect-bank audit, and what it found

> **Executed 2026-08-26. Two human raters, blinded, 31 items.** This section
> now reports a result. The original recommendation is kept below it, because
> the result only means something in light of the method that produced it.
>
> | | |
> |---|---|
> | Cohen's κ | **0.870**, 95% CI [0.674, 1.000] |
> | Raw agreement | **29/31**, with **0** `U` ratings |
> | Tier 1 — real defects | **0 of 11 called an error by both raters** |
> | Tier 2 — injected | **16 of 20 called an error by both** |
>
> ⚠ **The audit did not reassure us. It found the opposite of what it was set up
> to confirm.** Two blinded raters, independently and unanimously, judged every
> real defect the supervisor caught in production to be a technicality — and I
> then verified their reasoning mechanically against the corpus. It holds.
>
> **9 of the 11 are checker false positives with a diagnosed cause:** six are
> paraphrase misses by a character-level string matcher, three are
> single-character corruptions of ids whose real evidence is present. The
> remaining two are ~1-in-30 stray citations.
>
> Full results, verification and consequences: **`JOURNAL_PLAN.md` §15.**
> The decision this forces is **§11 of this memo.**

---

### The original recommendation, kept for the record

§5 of the plan requires the defect bank to be audited by two raters with
disagreements recorded. I am one person, and κ computed by one person is not
inter-rater agreement.

⚠ **An LLM is not a legitimate second rater here.** It wrote `defect_bank.py`,
which *defines* the bank; rating its own classifier's output reproduces the
circularity the audit exists to break.

> **Recommendation: split the construct.**
> - *Groundedness* is factual — is the evidence ID actually absent from the
>   analysis results? does the cited review actually lack that aspect? — and
>   should be **verified programmatically**. No rater needed, and it is stronger
>   than a human judgement because it is exhaustive.
> - *Meaningfulness* is judgement and needs a second human. That is **you**,
>   over a much smaller set: 11 Tier-1 defects, perhaps 20 sampled Tier-2
>   injections. Realistically under an hour.
>
> Reportable as: "groundedness verified programmatically; defect meaningfulness
> rated independently by two humans."

**Three things this needs to be worth doing**, none of which the plan currently
specifies:

1. **A written rubric, fixed before rating.** "Meaningful" is undefined as it
   stands, and κ over an undefined construct is a number without a referent. I
   propose a single binary judgement per item: *would a competent analyst
   reading this output call it an error, or is it a technicality of the check?*
   One sentence, decided in advance, applied to every item.
2. **Blinding.** You are an advisor on the work, so you are not a disinterested
   rater — normal in SE research, but cheap to strengthen. Present the items
   **shuffled, stripped of which operator produced them and whether they are
   Tier 1 or Tier 2**. Then agreement cannot be an artefact of knowing which
   items are supposed to be the real ones.
3. **Honest precision on κ.** 11 Tier-1 plus ~20 sampled Tier-2 is **31 items**.
   κ on 31 items carries a wide interval. Report it **with a CI, or report raw
   agreement and n** — do not report a bare κ as though it settled the question.

⚠ **One clarification so this is not oversold.** The programmatic half is
*verification*, not a second rating: it answers "does the check's premise
actually hold in the data?", which is an implementation question. It says
nothing about whether the defect is meaningful. The precedent for it working is
real — `defect_bank.py` and the older `tally.py` were written independently and
agree exactly on Phase A — but that is two implementations agreeing, not two
judges. The construct question is entirely the human half's job.

**What I need:** agreement to be rater 2 on ~31 blinded items against a
one-sentence rubric (realistically under an hour), or an alternative rater.

---

## 6b. ✅ APPROVED (D8d) — the C1 cell runs at 40 defects

**New on 2026-08-26.** Deciding D8b settled *which base* C1 uses. It did not
settle *how much of it to buy*, and that turns out to be the larger question.

As specified, C1 is 80 defects × {A1, A2} × r=3 = **≈480 trials**. Against a
core of ≈1,180 that is **another 40% of the study** — spent on a quantity D8c
has already declared untestable (interaction power 0.177 at 160/160 defects,
0.300 at 320/320, and the ceiling is ≈143).

| Option | Trials | What it buys | What it costs |
|---|---|---|---|
| As specified, 80 defects | ≈480 | the tightest CI on the disclosure estimate | 40% of the core again |
| **40 defects** | **≈240** | same estimate, CI ~1.4× wider | half as much |
| Drop it | 0 | nothing | hands a referee the objection two cited papers already raise |

> **✅ Decided 2026-08-26: 40 defects (≈240 trials).** Because D8c has already
> committed us to reporting C1 as an *estimate* rather than a test, a wider CI
> is a much smaller loss than it would be if we were trying to reject a null.
> Dropping it was rejected: *"we knew about the confound and did not measure
> it"* reads considerably worse than *"we measured it imprecisely and said so"*.

⚠ **Verify before this is funded.** The claim that the A1-vs-A2 contrast is
invalid without C1 rests on Huang et al. (ICLR 2024) §5 and Kamoi et al. (TACL
2024) Table 7, as summarised in our own reading extractions — **not** from a
re-reading of the papers. This project has had citation metadata wrong three
times from second-hand sourcing. Both claims should be checked in the PDFs
before C1's text goes into a pre-registration.

**Settled.** ≈240 trials, folded into the study total above.

---

## 7. Sign-off — ✅ ratified 2026-08-26, with one item still open

Items 1, 2 and 4 were positions to ratify or overturn, and are **ratified**.

⚠ **Item 3 is not settled by that.** It asks for a *choice*, not a
ratification: D2 marks the warm-resample subset REQUIRED and it is **not
built**. Build it, drop it from D2, or defer it — approval does not pick one,
and leaving it unanswered leaves a "REQUIRED" item unbuilt in a
pre-registration. **This, D5b (§5) and the new §11 are what is still
outstanding.** D13 (§6) is no longer among them — it is done.

1. **D12 — downstream propagation is in scope.** The runner persists the full
   retried stage output plus enough state to re-run downstream stages later, not
   just facts and a verdict. Recovering this afterwards means re-running all 822
   trials. It also **clears the dump's own strategy/report outputs** on a
   reasoning-stage trial: those were produced from the *pre-injection* output
   and are not that trial's downstream.

2. **Arm wording is frozen** (`scripts/arms.py`). Three strings were authored
   here rather than imported, each derived from a stated constraint, each pinned
   by a test. A1 is exempt — it *is* the production feedback template, imported,
   never re-typed.
   - **A0** — "Below is a draft answer to this task. Review it and produce the
     best answer you can to the original task. Return only valid JSON."
     Authorship is deliberately neutral: claiming another system produced it
     would bake an attribution claim into the *arm*, when attribution is what
     the *placement* factor manipulates.
   - **A2** — A1's own template with the measured facts removed and nothing else
     changed. Matching everything except the manipulated variable is what makes
     A1 vs A2 a content contrast rather than a wording contrast.
   - **P3 marker** — "The answer above contains an error." A statement, not an
     instruction; names no field, count or check, because a marker that
     discloses what is wrong becomes a weak A1.

   **If any of these should change, it must change now.** Changing wording after
   a trial runs breaks the pre-registration.

3. ⚠ **One plan requirement is not built, and I want that on the record rather
   than discovered later.** D2 marks the **warm-resample subset (temperature >
   0)** as "REQUIRED, not optional" — it carries the Olausson equal-budget
   comparison, which is the first thing a testing venue asks about A3. But
   `BaseAgent._create` hard-codes `temperature=0`, so **there is no way to run
   it today**. It needs a temperature parameter threaded through the call path
   and its own trial budget on top of the 822.

   Three ways forward, in the order I would rank them: build it and run it as a
   declared subset; drop it from D2 and concede the equal-budget comparison in
   limitations; or defer it to a follow-up and say so. **I have not chosen** —
   it changes the budget, so it is yours. What I have not done is quietly leave
   a "REQUIRED" item unbuilt.

4. **`JOURNAL_PLAN.md` was corrected on 2026-08-25**, before any data
   collection, which is when correcting a pre-registration is legitimate. The
   corrections replace hand-multiplied figures with script-emitted ones: the
   Tier-2 ceiling (160 → **102**), the arm allocation, the power table, the CI
   half-widths, the D8c interaction power, and the trial budget (~980 → **822**).
   Each edit is marked in place with its date and the command that regenerates
   it. Nothing was quietly rewritten.

---

## 8. What happens after you answer

In order, with a gate between each step. **D5b and D13 do not block steps 1–4**
— see the note after the list.

1. ✅ **Collect 8 Phase-A dumps — DONE 2026-08-26.** 8/8 ok, observe mode, no
   truncation. Delivered **N=142** (predicted ≈143), yield **5.07**/dump,
   **1,167** trials, replay **159 facts / 0 mismatches**. `JOURNAL_PLAN.md` §16.
2. ✅ **MDE re-checked against the delivered N — PASS.** At N=142, r=3:
   MDE **10.9 pp** with the shared-occasion effect against X = **12 pp**,
   margin **1.1 pp**. At N=102 it was 12.6 pp, i.e. above the threshold — the
   pre-registration was incoherent then and is coherent now.
   ✅ **No longer provisional.** N was computed through the matcher §11 is about,
   so I bounded it: swept 120–150 defects, the r=3 MDE stays under 12 pp across
   the whole range — including N=120, which is worse than O5 vanishing outright.
   **Deciding §11 either way does not force a re-plan** (§16.6). If a fix takes
   N below ~130 the margin thins to noise and the contingency is r=4, decidable
   afterwards.
3. **Smoke-test the live seam** — 7 cells, one per defined (arm, placement)
   shape, on one defect
   (`pytest tests/test_injection_seam_live.py -m integration`). *7–21 calls.*
   The only check a live call can make: that the assembled arm is accepted by
   the provider and returns schema-valid output.
4. **Run the core** — ≈1,180 trials, checkpointed and resumable, defect-outer so
   all arms for one defect share a session. *≈1,180–3,540 calls.* ⚠ Confirm the
   API budget first.
5. ✅ **Rate the defect bank (§6) — DONE 2026-08-26**, before any core result
   existed, so the blinding is intact and can no longer be lost. This step is
   discharged and does not need scheduling again.
6. **Run the C1 cell (§6b)** — 40 defects, ≈240 trials.
7. **Analyse**, then branch on the result per D11/D11b.
8. **Phase 4 / C7, the local replication (§5)** — needs D5b frozen by here.

Steps 1–3 cost under 80 calls between them. **Step 4 is the commitment.**

**On timing for the open questions.** D5b is genuinely deferrable: nothing
before step 8 touches the local model, so it can be settled while the core runs
— *unless* we take the ESEM registered-report route (D7), where the whole
protocol including C7 must be filed up front.

⚠ **D13 is no longer a timing question — it is done**, and it was done before
any core result existed, so the blinding held and can no longer be lost. What
replaced it as the urgent item is **§11**: the matcher bug it uncovered sits in
the critical path of the core run (it decides how large Tier 1 even is), and its
second half concerns a paper that is in review *now*.

---

## 9. Where each number comes from

All read-only. All but the first need no dataset. Run from `backend/`.

| Figure | Command |
|---|---|
| 102 defects, per-operator applicability, 5.1/dump yield | `python scripts/inject_defects.py --root out_study --matrix` |
| Power, MDE, occasion effect, interaction power | `python scripts/analysis/power.py --sims 20000` (§9; seed 42) |
| Trial count, arm allocation, order invariant (822 today, ≈1,180 after D11b) | `python scripts/run_injection_study.py --plan-only` |
| 11 Tier-1 defects, exclusions | `python scripts/analysis/defect_bank.py` |
| 135 facts replay exactly | `python scripts/replay_stage.py --verify out_study` |
| 5 of 5 constraints feedback-only | `python scripts/analysis/prompt_audit.py` |
| Collateral floors (0.07 / 0.33 / 0.29 / 0.23) | `python scripts/analysis/churn.py` |
| 266 tests (257 before D18, 2026-09-02) | `python -m pytest -m "not integration"` |

If any figure in this memo disagrees with what a command prints, **the command
is right** — tell me and I will fix the memo.

---

## 10. Two things I would rather you heard from me

- **Tier 1 cannot carry inference.** 11 defects over 5 clusters gives an MDE of
  ~31 pp, and the cluster bootstrap over-rejects at 0.086 against a nominal
  0.05. It is a realism anchor, reported descriptively, with no hypothesis test
  on it. I would rather say that now than be told it in review.
- **"Repair" here means repair by regeneration.** The retried stage regenerates
  its whole output rather than editing the faulty artifact. Putting the artifact
  in the model's context (P1) narrows that gap; it does not close it. The paper
  will say "repair by regeneration" throughout — overclaiming "self-repair"
  summons the referee who knows the self-correction literature.

---

## 11. ⛔ NEW QUESTION (2026-08-26) — the matcher bug, and paper #1

D13 was supposed to validate the defect bank. It invalidated most of it, and the
cause is a specific line of our own code. I need a decision on two things, and
the second one is time-sensitive because paper #1 is in review.

### What was found

`supervision._measure_strategy` decides whether a recommendation traces to
upstream using `difflib.SequenceMatcher` — a **character-level** similarity —
against `TRACE_SIMILARITY = 0.35`. Measured over the audited items:

| | lexical score (what the check uses) | content-word overlap |
|---|---|---|
| Real defects (6 Tier-1 items) | **0.23 – 0.35** | 0.08 – 0.44 |
| Injected O5 (alien content) | **0.21 – 0.28** | **0.00, all three** |

The bands overlap completely: the check scores *"Negative ambience."* against an
upstream pattern reading "the restaurant's ambience is often described
negatively" at **0.23**, and *"till float count skipped"* against a staff
complaint at **0.21**. It fails both. Content-word overlap separates them
perfectly on this sample.

### Question 1 — do I fix the matcher now, and what happens to Tier 1?

Fixing it is small. The consequence is not: `untraceable_recommendation` is
**8 of the 13** Tier-1 defects, so re-running `defect_bank.py` against a fixed
matcher would likely take the bank from 13 toward **~2–5**. Tier 1 is both the
replay tier and the realism anchor for the whole journal study.

⚠ **Corrected 2026-09-08.** This paragraph read "6 of the 11" — the figure from
the 20-dump bank, written before the D11b collection was folded in. The
regenerated `out_study/defect_bank.json` reads `genuine: 13` with
`untraceable_recommendation: 8`. The share the bug accounts for went **up**,
from 55% to **62%**, so the question below is asked against a larger
consequence, not a smaller one.

**My recommendation: measure the shrinkage before deciding anything.** It is
read-only, needs no dataset and no API calls. We should not choose between
"leave a known bug in the instrument" and "shrink the bank" while the size of
the second option is unknown.

### Question 2 — what do we tell the conference?

Paper #1 is **under review**, and its retry counts embed this false-positive
rate without characterising it. Three routes, and this is your call, not mine:

1. **Note to the chairs now**, while it is in review.
2. **Camera-ready limitation**, if it is accepted.
3. **Journal-paper finding**, and paper #1 stands as submitted.

I have no view on which is right procedurally. I do have one on the substance:
this is much better volunteered than discovered, and it is a genuinely good
result — "we audited our own supervisor, found its precision failure mode and
diagnosed the cause" is a stronger contribution than the repair study it came
out of.

### What it does to the repair study

Not fatal, but it narrows the claim, and the narrowing should be designed in
rather than conceded in review:

- Tier 2 minus O1 is **more severe** than anything the supervisor catches in
  production, so the headline repair rate is **not** a production repair rate.
- **O1 is the only production-like operator** — it corrupts a real id, and both
  raters rated it exactly as they rated the real defects. Report O1 separately
  from O2–O7 rather than pooling them.

### ✅ Answered 2026-09-14 — by the author

**Q2 — route 3.** Paper #1 stands as submitted; no note to the chairs. The
matcher defect is a journal-paper finding.

**Q1 — measured, then decided** (`JOURNAL_PLAN.md` §17; reproduce with
`scripts/analysis/matcher_shrinkage.py`, pinned by
`tests/test_matcher_shrinkage.py`):

- **Shrinkage: Tier 1 goes 13 → 6** under a content-word matcher (Jaccard ≥
  0.10), and to 5 under laxer ones. The floor of 5 is the reasoning-stage
  defects, which never consult the matcher. D13 rated all 6 survivors
  technicalities. The forecast above (~2–5) was about right.
- **Every one of the 13 production issues the shipped check flagged shares
  content words with upstream.** In the other direction, the shipped check calls
  the frozen alien O5 issues traceable in 6 of 168 issue × base pairs.
- **The bug does not reach the study's manipulation** — the O5 bases, the
  injected issue, the trigger and the feedback are identical under either
  matcher — **but it does reach the measurement**: O5 is scored by re-running
  the shipped check, which flags 8 of 49 *correct* observe-mode strategy outputs.

**Decision (D22):** the production supervisor stays as shipped for the study —
it is the system paper #1 describes — and the scorer's O5 trace is corrected.
The production fix comes after the study, as a versioned change. This opened one
pre-freeze item, `PREREGISTRATION.md` §11 item 5.

---

## 12. ⛔ NEW (2026-09-02) — your methodology review, and three decisions it created

Your four points are all adopted. They are recorded as **D18–D21** in
`JOURNAL_PLAN.md` §3.7, and they produced a document that did not exist before:
**`docs/paper/PREREGISTRATION.md`**. It is deliberately still a **DRAFT** — it
cannot be frozen until the questions below are answered.

**What is already done.** Point 1 (`deleted` as a fifth outcome class) is
**implemented and tested**. It was not a taxonomy refinement: the scorer was
labelling the same model behaviour two different ways depending on which
operator ran — dropping the flagged item scored `replaced` for O1/O2/O3/O5 and
`repaired` for O6/O7. Fixing it also surfaced two adjacent bugs (deletion was
being counted twice, once as the outcome and once as collateral damage; and the
churn function returned 100% for an empty list). Suite 257 → 266.

**What is not done.** Points 2 and 3 are specified but unbuilt. In particular
the injection-validity gate you asked for is *half* present already —
`verify_injection()` exists and does exactly the check you described, and
nothing ever calls it. That is now written down rather than assumed.

### Question 3 — is the primary contrast pooled, or estimated inside the severe cell?

**This one moves the power gate, and it is the reason the pre-registration is
not yet frozen.**

§15.6, from the D13 audit you already have, says do not pool O1 with O2–O7: O1
is the only production-like operator. Applied to the **absolute rates** that is
clearly right. Applied to the **contrast**, it drops N from 142 to 118, because
O1 carries 24 of the defects — and the design then stops clearing its own
threshold:

| Primary cell | N | r | MDE w/ occasion | vs X = 12 pp |
|---|---|---|---|---|
| Pooled (all repair operators) | 142 | 3 | 10.9 pp | margin 1.1 pp ✅ |
| Severe only (O1 excluded) | 118 | 3 | **11.9 pp** | margin 0.1 pp ⚠ |
| Severe only | 118 | 4 | 10.5 pp | margin 1.5 pp ✅ |

That middle row is exactly the incoherent state the eight extra dumps were
collected to escape — we would have spent that budget and landed back where we
started.

**My recommendation: pool for the contrast, split for the rates.** A1 − A2 is a
claim about feedback *content*, and I see no principled reason it must be
estimated only inside the severe cell; what §15.6 is protecting is the absolute
rate, which the pre-registration already refuses to pool. The alternative —
severe-cell contrast at r=4 — is defensible and costs roughly 944 trials on
A1/A2 alone.

### Question 4 — is the overwrite counterfactual (your point 2) in scope?

Your reframing of the inflated-frequency cell is, I think, the highest-value of
the four, and I want to say why rather than just agree. §4.5 of the conference
paper asserts a design principle — *any quantity the checker can compute should
not be asked of the model* — and **neither paper contains a counterfactual for
it**. §6.7 illustrates it; nothing tests it. Routing frequency divergence to
retry deliberately, outside the production path, measures what the overwrite
actually bought.

Cost is **~138 trials** (23 of the 28 dumps are applicable), and it needs no new
frozen wording — the supervisor already emits the measured fact as a string.

One thing I have written into the pre-registration so the cell cannot be read as
built to confirm a decision we already shipped: **if retry repairs frequency at
~100% with no collateral churn, then overwrite was a cost optimisation and not a
correctness one, and the paper says so.**

### Question 5 — how is the McNemar dichotomy formed from three repetitions?

Smaller, but genuinely undetermined, and I found it only by writing the
pre-registration out. `power.py` rules out the obvious answer — McNemar over
every (defect, repetition) pair treats repetitions of one defect as independent
and over-rejects at 0.086 — and nothing in the plan says what replaces it.
Majority, unanimity and any-of-3 are not equivalent.

**My recommendation: majority (≥2 of 3),** as the dichotomous analogue of the
rep-mean the primary CI is already built on. I have recorded it as a proposal
rather than a decision, because picking it after seeing three rates is the exact
move a pre-registration exists to prevent.

### What I am not asking you to decide

Wiring the two gates from point 3, and re-running `power.py` against whatever N
they leave. That is a build task, it is on me, and it must happen before the
pre-registration is frozen — the exclusion denominators and the 1.1 pp margin
both assume it.

### ✅ Answered 2026-09-14 — by the author

**Q3 — pool.** The primary A1 − A2 contrast runs over all six repair operators,
N = 142; absolute rates are never pooled; the O1 × arm interaction is reported
unconditionally.

**Q4 — yes, after the core.** D19 is in scope, run once the core is complete and
the budget is confirmed; reported as pre-registered and unrun if it cannot be.

**Q5 — majority.** Strictly more than half of completed repetitions.

⚠ **One new question came out of closing Q1, and it is not answered yet** —
`PREREGISTRATION.md` §11 item 6, `JOURNAL_PLAN.md` §17.6. A3 re-draws at P0, where
an injected defect is never in the context, so it is not a near-zero floor for
Tier 2 (estimated ≈ 53% repair). It blocks the freeze.
