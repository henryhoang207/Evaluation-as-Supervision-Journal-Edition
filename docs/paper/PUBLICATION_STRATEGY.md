# Publication Strategy — one testbed, how many papers?

**Written:** 2026-08-24 · **Status:** decided where marked, open where marked ·
**Supersedes:** `JOURNAL_PLAN.md` §12 D7 as the *sole* venue decision — §12's
analysis still holds for the journal vehicle, but it assumed a single output.

This file answers three questions: whether to split the repair study into its
own conference paper, what is left for the journal if we do, and whether either
claim is significant enough to carry a paper.

---

## 1. Status of record

| Fact | Value |
|---|---|
| Conference paper #1 | **Submitted, under review** (confirmed 2026-08-24) |
| — its claims | evaluation-as-supervision pattern + derivability precondition; 35% defect incidence; defect instability |
| — authorship (D5) | resolved by submission |
| Journal extension | ⚠ **updated 2026-09-02.** **B1–B8 are all built, wired and tested** (266 tests) — the "B4–B8 unbuilt" row was true on 2026-08-24 and is not now |
| Repair result | ✅ **measured 2026-10-05 → 08.** Null at ceiling: A1 − A2 = +0.7 pp, 95 % CI [−2.9, +4.3], exact McNemar p = 0.75, N = 139. The split rule (≥ 12 pp and CI excluding zero) is **not met**, so the table's **null row applies**: do not split. The vehicle choice itself is the author's. Every cell except C7 has run — full record in `RESULTS.md` |
| Testbed | one pipeline, one domain (Yelp restaurant reviews), one model (`gemini-2.5-flash`), **28 workloads** (was 20; D11b collection, 2026-08-26) |
| Tier-1 natural defects | **13 usable**, 7 business × stage cells, 6 businesses. ⚠ **But see §15 of `JOURNAL_PLAN.md`: the D13 audit found 9 of the original 11 are checker false positives**, so this row counts what the checker flagged, not what is real. This materially weakens §4's "is the claim significant enough" argument — re-read that section against it |
| Tier-2 injection ceiling | **N = 142** repair-endpoint defects over 6 operators |
| Methodology review | **D18–D21** adopted 2026-09-02 (`JOURNAL_PLAN.md` §3.7); `PREREGISTRATION.md` **frozen 2026-09-14** at tag `prereg-freeze`, amendments §0.1 A1–A9 filed before each post-core cell ran |

---

## 2. The decision: do not decide yet — let the result choose the vehicle

**Decided.** The conference core and the journal core are the *same experiment*.
Nothing is wasted by building and running it before choosing a venue, and the
result itself is the best available evidence about which vehicle fits.

Run first: **A0/A1/A2/A3 at P1, three stages, plus the C1 constraint-complete
cell, plus the warm-resample subset.** Then branch:

| Outcome | Vehicle | Why |
|---|---|---|
| **A1 ≫ A2** (clean positive) | Splittable — conference #2 carries it, journal keeps C7 + downstream propagation | A positive repair result is self-contained and reads well at 10–12 pages |
| **A1 ≈ A2** (null) | **Do not split.** Registered report, or straight to the journal | A null needs the full apparatus — D8, placement, local runtime — to read as a finding rather than as underpowering. Split it and it reads as a failed experiment |

This branch is worth pre-registering alongside the statistical plan: it commits
us to publishing the null through the vehicle that can defend it, rather than
quietly reaching for a smaller venue when the sign disappoints.

---

## 3. Pros and cons of splitting

**For**

- **Time to output.** Journal cycles run 12–18 months; a conference lands in ~6.
- **Reviewer feedback we cannot otherwise buy.** No co-authors are stress-testing
  this design. Three referees on the repair experiment is worth more than another
  month of self-review.
- **Hedges model deprecation.** `gemini-2.5-pro` already 404-ed once. If
  `gemini-2.5-flash` goes the same way mid-journal, published hosted results are
  locked in and unpublished ones are stranded.
- **The result is self-contained** — given C1, "does measured feedback repair?"
  needs none of the ablations to be interpretable.
- **Forces scope discipline.** The plan is ~980 calls across six cell types; a
  conference core is a tighter and better experiment than the sprawl.

**Against**

- **Salami slicing.** Three publications from 20 businesses, one model, one
  domain. Each split sharpens the "what is actually new here?" question at the
  next stage.
- **The 30% rule compounds.** The journal would need 30%+ new material over
  *both* papers and must declare both.
- **The journal loses its headline** unless downstream propagation moves in
  (§5).
- **Writing cost is real** — 10–12 pages of new prose, related work and figures:
  2–3 weeks part-time that does not advance the journal.
- **#2's motivation leans on an unpublished paper** (§6). This is the newly
  binding one now that #1 is under review.
- **Fragments the strongest asset.** Deterministic verifier + measured repair +
  causal identification is more impressive as one argument than as three.

---

## 4. Is the claim significant enough?

**As a specialist / mid-tier conference paper: yes.** The gap statement holds —
MAS-FIRE measures propagation and diagnosis, AgentChaos measures failure
classes, AgenTracer does attribution; **none measures repair.** And A1-vs-A2
adjudicates between two published positions that predict opposite things
(Olausson: feedback quality binds → A1 ≫ A2; SC-Bench: a contentless trigger
closes 89.3% of the gap → A2 ≈ A1). A pre-registered experiment deciding between
two literatures is a contribution whichever way it lands. The supervisor also
occupies a rare category — feedback *correct by construction* — which Kamoi's
framework legitimises as fair-asymmetric external verification.

**As a top-tier paper (TOSEM / TSE / ICSE): no, not at current scale.** Three
objections we cannot answer with present data:

1. **One model, one provider, one pipeline, one domain.** "Is this a property of
   the method or of this model?" has no answer in our data. The C7 local arm is
   the cheapest partial fix.
2. **n is small and clustered.** 11 natural defects in 5 cells; Tier 2 is 20
   workloads of one domain. Adequate for a case study, fatal for generalisation.
3. **The checks are shallow by design.** ID resolution, set membership,
   `difflib` ≥ 0.35, exact string containment. That determinism is the *thesis*,
   but a referee will read it as string matching and ask whether the defects are
   correspondingly shallow. Frame it as a deliberate trade — zero LLM calls,
   correct by construction — or they will frame it for us.

**Precision requirement.** Because the retried stage regenerates rather than
edits, what we measure is *repair by regeneration under measured feedback*, not
*editing a faulty artifact*. P1 narrows the gap by putting the artifact in
context; it does not close it. Say "repair by regeneration" — overclaiming
"self-repair" summons the referee who knows the self-correction literature.

---

## 5. What is left for the journal — and the fix it needs

Sorting the residue honestly:

| Item | Carries a journal? |
|---|---|
| Placement P0/P1/P2/P3 | No — mechanism ablation |
| D8 constraint completeness | No — **and it belongs in the conference core**, see §7 |
| Severity → detection curves | No — calibration appendix (it is free, which is also why it is cheap) |
| Realism ladder / coupling | No — a validity argument, and ours covers 4 of 8 operators |
| Best-of-k under equal tokens | No — a required baseline, not a claim |
| **C7 local deterministic runtime** | **Yes** |
| **Downstream propagation** | **Yes — but currently out of scope (§11)** |

Five of seven are ablations. **A journal paper made of ablations on a result
published elsewhere is a weak journal paper.** That is the true cost of the
split, and it is payable only one way:

> **Move downstream propagation into journal scope now** — before B7 is written,
> because logging what it needs on the first pass is far cheaper than re-running
> ~980 trials for it later.

With it, the journal has a thesis rather than a list:

> **Defect-level repair does not equal pipeline-level improvement — and on a
> deterministic runtime we can show exactly why.**

Both halves are real claims. C7 gives causal attribution (bare retry is
bit-identical locally, so any repair in the feedback arm is attributable to
feedback content) and separates serving-stack drift from a genuine pipeline
property, which no amount of hosted-API work can do. Downstream propagation
tests MAST Appendix J's prediction that defect presence and run outcome are only
loosely coupled — and if repairing a defect does *not* improve the final report,
that says runtime verification buys groundedness, not utility. Those are
different products, and saying so is worth a journal paper.

---

## 6. Constraints now that conference #1 is under review

**Newly binding.** These were hypothetical while #1 was unsubmitted.

1. **Overlap declaration, not a hard block.** Dual-submission rules target the
   same or substantially overlapping *contribution*, not shared background. A new
   research question on the same testbed is normally acceptable — but #2 must
   declare #1 explicitly, cite it, and never present #1's results as its own
   contribution. Check the target venue's exact wording; CAIN states the
   requirement restrictively.
2. **#2's motivation would lean on an unpublished paper.** The natural framing —
   *"the conference version could not measure repair; here we do"* — cites a
   paper referees cannot read or verify. That materially weakens #2 until #1
   lands, and is an argument for waiting rather than racing.
3. **The 30% rule now has a fixed anchor.** #1 is the declared prior version. Any
   journal extension must clear 30% new material over it and say so; if #2
   exists, over both.
4. **If #1 is rejected**, the cleanest recovery is to fold the repair result into
   the resubmission rather than to run two parallel conference papers. Revisit
   this file at that point.
5. **Ask the #1 chairs about an extended-version route** (`JOURNAL_PLAN` §12.3).
   Many Springer conferences invite selected papers to an affiliated journal
   special issue. That is the cheapest possible path to the journal and costs one
   email. Do this while #1 is in review, not after.

---

## 7. Changes to make regardless of the split decision

These hold under every branch and should not wait for the venue choice.

1. **D8 moves into the conference core.** Deferring it breaks the very contrast
   the paper leads with: the A1 feedback discloses four constraints the stage
   prompts never state (verified against the code — `JOURNAL_PLAN` §13.1), so
   A1 > A2 is not a specificity result without C1. Two independent sources make
   this a required control — Huang et al. (ICLR 2024) §5, and Kamoi et al.
   (TACL 2024) Table 7, where it is a **Required** checklist row. The C1 cell is
   ~160 calls inside a ~980-call budget: roughly 16% more compute to keep the
   headline interpretable. Take it.
2. **Keep the warm-resample subset.** At temperature 0, A3 measures prompt
   determinism, not resampling (D2). Olausson's standard is best-of-n under equal
   budget, and at a testing venue that is the first question asked. Without the
   subset, A3 reads as a strawman baseline.
3. **State the realism ceiling plainly.** Tier 2 covers three stages; the natural
   defect anchor covers **two**. The report stage has zero natural defects — its
   operators O6/O7 lost their only instance to the cascade exclusion — so
   report-stage evidence is entirely synthetic and uncoupled, and the Just-style
   coupling check covers **4 of 8 operators**. A referee who recomputes the bank
   finds this in ten minutes.
4. **Adopt the sharper framing sentence**, whichever vehicle wins:
   > *We do not merely propose a supervisor; we measure whether its deterministic
   > feedback causes repair, against a capability ceiling and controlled retry
   > baselines.*
   This is strictly better than what `JOURNAL_PLAN` §1 currently leads with, and
   costs nothing.

---

## 8. Venue assessment

> ⚠ **Provenance of the dates below.** The ASE 2026 venue and DOI come from
> `JOURNAL_PLAN` §14.9, where they were checked against the paper. **Every
> deadline in the table was supplied second-hand and has NOT been verified
> against an official CFP.** Treat them as leads to confirm, not as facts, and
> re-check each on the venue's own page before planning around it — §14.9 is
> this project's own record of citation metadata being wrong three times from
> exactly this kind of sourcing.

`JOURNAL_PLAN` §12 recommended **EMSE regular track** and that still stands for
the journal vehicle. For a conference vehicle:

| Venue | Deadline | Assessment |
|---|---|---|
| **ASE 2027** | TBA | **The omission in every prior version of this analysis.** AgentChaos — agent fault injection — is **ASE 2026, peer-reviewed, DOI `10.1145/3832783.3837437`**. That is direct, one-year-prior evidence that this community accepts this exact kind of work, and §14.8 already calls it our reference class. Check dates first. |
| **ISSTA 2027** | 11 Jan 2027 | Realistic on time. The reframe (deterministic fault injection + runtime analysis for LLM pipelines) is plausible, but re-imports §12's direction problem: a testing venue asks what software artifact is under test, and "a restaurant review pipeline" is a soft answer. |
| **EASE 2027** | unpublished | Good fit — CORE A, empirical SE evaluation. Blocked on dates. |
| **CAIN 2027** | 30 Oct 2026 | Best topical fit, worst timing. **Not realistic** *(assessed 2026-08-24; B4–B8 have since been built and the scorer exists — the timing objection stands, the build objection does not)*: B4–B8 unbuilt, ~980 calls unrun, no scorer, and a fresh 10+2-page paper — nine weeks part-time. Also the venue most restrictive about concurrent submission (§6.1). |
| **ESEM Registered Reports** | check cycle | **Strategically the strongest option and absent from every prior recommendation.** Submit the *protocol*: design review arrives exactly when it is useful, and in-principle acceptance survives a null A1 ≈ A3. It is the only format that rewards design work before results exist — which is the strongest part of this project. |
| ICSE 2027 | closed (30 Jun 2026) | Main research track unavailable. |

---

## 9. Open items

- [ ] **Check the ESEM registered-report cycle dates.** This outranks the whole
      table above and changes `JOURNAL_PLAN` §10 if it lands.
- [ ] **Check ASE 2027 dates** once announced.
- [ ] **Email the #1 chairs** about an extended-version route (§6.5).
- [x] ~~Decide whether downstream propagation is logged by B7 from the first run
      (§5)~~ — ✅ **RESOLVED (D12).** `run_trial` persists `retried_output` plus a
      `downstream_state` sufficient to re-run the later stages, so propagation
      can be analysed without repeating a single trial.
- [ ] Revisit this file when #1's decision arrives.
