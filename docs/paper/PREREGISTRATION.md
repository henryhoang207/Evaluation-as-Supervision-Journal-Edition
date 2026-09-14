# Pre-registration — injected-defect repair study

**Status: all four §11 blocking items closed 2026-09-08. First committed
2026-09-14 for safekeeping — NOT yet frozen. The freeze is the annotated git
tag `prereg-freeze`; no trial may run before that tag exists.**

Why a tag, and not "the commit that adds it" (this header's wording until
2026-09-14): the file had to be committed and pushed while the `PHASE0_MEMO.md`
Q1 matcher decision was still being measured, because the same commit carries
paid-for study data that existed on one disk. **Committing is not freezing.** Q1
can change code this document freezes (§8) and the O5 applicability inside
N = 142 (§6), so the freeze waits for it. A tag also names the freeze point
unambiguously; "the commit that adds it" stops being checkable the moment the
file is edited again.

The three decisions were taken by the author on 2026-09-08 with the supervisor's
questions (`PHASE0_MEMO.md` §11–§12) outstanding, because each is a choice that
becomes illegitimate the moment a result exists and the study cannot start
without them. **They are recorded as authored positions, open to supervisor
override up to the freeze tag** — after it, only as a dated §0 amendment.
Each states its reason before its consequence, and where a power number happens
to favour the chosen option that is noted as a *consequence*, never as the
ground.

Drafted in response to supervisor point 4 (D21, `JOURNAL_PLAN.md` §3.7):
*pre-specify measured-fact vs generic rejection as the primary comparison,
before seeing results.*

---

## 0. Why this file exists separately

The substance below was already decided and is scattered across
`JOURNAL_PLAN.md` — §6.2 names the primary contrast, D4f pre-registers
estimation with a CI, D11b freezes the split rule, §8 fixes the confirmatory
tests, §13.3 records directional predictions. That is not a pre-registration.
A pre-registration is one short document, frozen at a stated moment, that a
reader can check the analysis against without re-reading a 1,600-line plan
carrying its own correction banners.

**Freeze condition.** This file is committed with a dated hash **before the
first trial runs**. A pre-registration that is not in version control before
data collection is not one. As of drafting, **zero trials have run**: the only
API calls this study has spent are the **8 Phase-A dumps collected on
2026-08-26** under D11b, which took the injection base from 20 dumps to 28. The
other 20 predate the study and were collected for the conference paper.

**Amendment rule.** Anything below may be changed *before* the freeze, freely.
After the freeze it may be changed only by an appended, dated amendment stating
what changed and why, and any result it touches is reported as exploratory.

**Where this file and `JOURNAL_PLAN.md` disagree, this file wins** for anything
it covers. The plan remains authoritative for everything else.

---

## 1. The estimand, stated in one sentence

For a defect injected into a clean pipeline stage output and presented to the
production agent as an artifact under review, **does the content of the
supervisor's feedback change whether the regenerated output is correct?**

Three things that sentence deliberately excludes:

- **Not run-level utility.** The unit is the defect, not the run. `repaired`
  does not mean the run became good (§14.4, MAST App. J). Run-level verdicts
  are logged and reported; no claim rests on them.
- **Not repair-in-place.** The retried stage regenerates its whole output
  rather than editing the faulty artifact (D17). The construct is
  *regenerate-under-measured-feedback*. The paper says "repair by
  regeneration" throughout.
- **Not a production repair rate.** The D13 audit (§15) established that Tier 2
  minus O1 is markedly *more severe* than anything the supervisor catches in
  production. The headline rate is a repair rate for human-recognisable
  injected defects and is never described as anything else.

---

## 2. Primary comparison — fixed before any result exists

**A1 − A2: measured-fact feedback minus generic rejection.**

| Arm | What the model receives | Role |
|---|---|---|
| **A1** | the production `_SUPERVISOR_FEEDBACK_PROMPT`, carrying the measured fact that triggered the verdict | primary |
| **A2** | the same template with the measured facts removed — an authoritative but contentless rejection | primary |
| A0 | the defect framed as a fresh correction task, no retry language | capability ceiling, bounds A1 |
| A3 | the original prompt again, nothing added | floor; isolates the trigger from its content |

Arm wording was frozen on 2026-08-25 in `backend/scripts/arms.py`
(`AUTHORED_WORDING`), before this file and before any trial.

**Why this contrast and not another.** The two literatures make opposite
predictions and disagree *only* here. Olausson (feedback quality binds; human
feedback lifted repair 33.3% → 52.6%) predicts A1 ≫ A2. SC-Bench (a contentless
"Wait" closes 89.3% of the gap) predicts A2 ≈ A1. Both agree about A0, A1 and
A3. The experiment adjudicates between them; that is its reason to exist.

**Reported as an estimate, not a test (D4f).** A1 − A2 as a difference in
proportions with a **95% cluster-bootstrap CI over defect blocks**, half-width
≈ 7.1 pp at N = 142. A null then says something — "3 pp, 95% CI [−5, 11]"
excludes large effects — rather than being indistinguishable from insufficient
power.

**The contrast is estimated over all six repair operators — decided 2026-09-08,
§11 item 1.**

> **Pool for the contrast. Never pool the rates.** The primary A1 − A2 estimate
> runs over all six repair operators, N = 142. The absolute repair rates are
> reported separately for O1 and for the severe cell and are **never** pooled
> (§3 item 1). The **O1 × arm interaction is a pre-specified secondary analysis
> reported unconditionally, with CIs, whatever it shows** (§3 item 1a).

The reason is the estimand, not the arithmetic. §15.6 — the D13 audit's finding
that O1 is the only production-like operator and O2–O7 are more severe than
anything production catches — is a statement about **external validity of an
absolute rate**: it says our repair rate is not a production repair rate. That
binds the rate, and §1 and §3 already refuse to pool it. A1 − A2 is a different
quantity: a claim about whether feedback *content* changes the outcome, which is
what Olausson and SC-Bench actually disagree about, and neither literature
frames its claim as holding only inside a severity band. There is no principled
reason to estimate it in the severe cell alone.

**The honest cost, stated rather than buried.** Pooling estimates the contrast
over a mixture whose operator composition we chose. If the effect differs by
severity, the pooled number is a mixture-weighted average and not a quantity in
the world. That is exactly why the interaction is promoted to a **named
secondary reported unconditionally** rather than a subgroup analysis run if the
primary disappoints: the severe-cell contrast appears beside the pooled one in
the same table, in every version of the paper, so a reader can price the pooling
assumption without taking our word for it.

⚠ **What did *not* decide this.** Pooling also happens to keep the power margin
at 1.1 pp where the severe cell at r = 3 leaves 0.1 pp (§11 item 1's table).
That is a **consequence** and is recorded as one. Had the principled reading
gone the other way, the answer would have been the severe cell at **r = 4**
(MDE 10.5 pp, ~944 trials on A1/A2 alone) — never the severe cell at r = 3, and
never a smaller X.

### 2.1 Confirmatory tests — exactly three, under Holm

1. Cochran's Q, omnibus over the matched arms within a defect, on the
   dichotomised outcome (§2.3).
2. Exact McNemar, **A1 vs A2** — feedback content.
3. Exact McNemar, **A2 vs A3** — the bare trigger.

⚠ **The primary reported quantity is the estimate, not these tests** (D4f):
A1 − A2 as a difference in rates with a 95% cluster-bootstrap CI over defect
blocks. The three tests are reported under Holm alongside it.

**How the per-defect dichotomy is formed from r = 3 repetitions — decided
2026-09-08, §11 item 4.**

> Within each (defect, arm), the defect scores **`repaired` iff strictly more
> than half of its completed repetitions scored `repaired`** on the strict
> dichotomy of §2.3. That is **majority**: 2 of 3, or 3 of 3.

Three properties made this the choice rather than a coin-flip between three
candidates:

- **It is the dichotomous analogue of the estimator the primary already uses.**
  §2.4 averages the r repetitions into one rate per (defect, arm); majority is
  that same rate thresholded at 0.5. Any other rule would mean the CI and the
  confirmatory test are answering different questions about the same data.
- **`any-of-3` was rejected as measuring best-of-k.** It scores a defect
  repaired if one repetition in three succeeded, which rewards *variance*
  rather than repair and inflates every arm — including A3, whose whole role is
  to be a floor. Best-of-k curves remain in the exploratory set (§2.1), where
  that is the intended reading.
- **`unanimity` was rejected as the same error mirrored.** It penalises
  variance rather than rewarding it, deflates every arm, and would make the
  test strictly less powerful than the estimate it accompanies.

**Ties, when a repetition is lost.** "Strictly more than half of *completed*
repetitions" resolves r = 2 splits (1–1) to **not repaired**. This is
conservative, and it is safe rather than merely cautious: the design is matched,
so the rule applies to both arms of every pair and cannot move a contrast in a
known direction. A defect with r = 1 in an arm scores that repetition. A defect
with zero completed repetitions in either primary arm is dropped from that
contrast and counted (§2.4).

**`deleted` counts against `repaired`** at the repetition level (§2.3, D18)
before the majority is taken — the dichotomy is applied first, the aggregation
second, never the reverse.

`power.py` independently rules out the obvious wrong answer — McNemar over every
(defect, repetition) pair, which treats repetitions of one defect as independent
and over-rejects at 0.086 — so this could not be left to whoever writes the
analysis script.

Everything else in the analysis is **exploratory** and is labelled so in the
paper. This includes: the placement effects, the placement × arm interaction,
the C1 constraint-completeness cell, the severity sweep, per-operator rates,
the collateral comparison, best-of-k curves, and the D19 counterfactual (§7).

### 2.2 Blocking

Blocked on defect identity throughout. All arms for one defect execute
contiguously in a single session (§14.1) so they share one serving stack; the
runner enforces this and `verify_order()` fails the run if the loop is ever
rewritten arm-outer. Tier-1 observations nest inside their business × stage
cell rather than counting as independent blocks (§8).

### 2.3 Outcome — the 4-class multinomial and the dichotomy

Outcome is `{repaired, replaced, deleted, unrepaired}` crossed with a binary
collateral flag (D3b as amended by D18). The classes are decided in a fixed
order, which is what makes them mutually exclusive:

1. the injected check still fires → **`unrepaired`**
2. the item is gone, for an operator whose clean output had it → **`deleted`**
3. the item is back to its pre-injection value → **`repaired`**
4. otherwise → **`replaced`**

**The confirmatory tests run on the strict dichotomy `repaired` vs everything
else.** In particular **`deleted` counts against repair**: deleting the item the
supervisor complained about is evasion, and scoring it as success would let
"drop the pattern you were asked about" register as a supervisor win. For the
insertion operators O6/O7 the position is reversed and consistent — removing an
invented item *is* the repair, so those trials score `repaired` and `deleted` is
structurally unreachable for them.

Two boundaries, chosen rather than stumbled into:

- **Success is replacement value, not descriptor disappearance** (§13.5). A
  fabricated evidence id swapped for a *different* fabricated-but-resolving id
  scores `replaced`. The check passes; the output is still wrong.
- **An emptied evidence list is `replaced`, not `deleted`.** The pattern is
  still asserted, now with no support at all — a wrong value, not a missing
  item.

Deletion is decided by **identity, not index**: retry regenerates, so positions
move. Each substitution operator anchors on a field it does not touch
(`description` for O1/O2/O3, `action` for O5).

### 2.4 The analysis unit, and what a lost trial costs

**The unit is the defect, not the trial.** `power.py` fixes this and the
analysis must match it: within each (defect, arm) the r = 3 repetitions are
**averaged**, giving one rate per arm per defect; the contrast is the mean of
the per-defect differences; the CI comes from a **bootstrap that resamples
whole defects**, which is what keeps repeated observations of one defect from
counting as independent evidence.

Consequences for the exclusions in §4, none of which were stated until this
document forced the question:

- **A lost trial does not lose the defect.** It leaves that (defect, arm) cell
  averaged over 2 reps instead of 3 — noisier, still usable. The simulation
  assumes balanced cells, so heavy imbalance would make its MDE optimistic;
  **report the distribution of reps-per-cell** alongside the estimate.
- **A defect enters the primary contrast only if it has ≥ 1 usable repetition
  in both A1 and A2.** Otherwise it contributes no difference and is dropped
  from that contrast and counted. Same rule per contrast for A2 vs A3.
- **The D20 gates operate per defect, not per trial** — they run on the
  injected output before any arm executes, so they remove a defect from every
  arm at once and cannot break the matching. The provider-failure and
  fallback exclusions are per trial and can, which is why the rule above is
  needed.

### 2.5 Collateral

A second dimension, never a class. Measured as semantic set-overlap against the
**pre-injection** output, above the churn floor an unperturbed pipeline already
produces at temperature 0 (D3c, measured not chosen: 0.07 / 0.33 / 0.29 / 0.23
by item class). **The injected item is excluded from the computation**, so the
outcome class and the collateral flag cannot be raised by the same event.
Report-stage items were never calibrated; those trials are marked
`collateral_measurable: false` and are excluded from the collateral denominator
rather than defaulted to "no damage".

⚠ **Stated limit.** Excluding the injected item leaves the rate over n−1 items
against floors calibrated over n. That is the correct estimator for the
non-injected population — both estimate a per-item loss probability — but the
flag's resolution is 1/(n−1), so on a small base one lost item can land either
side of a floor (measured: a 4-pattern base losing one unrelated pattern scores
0.333 against a 0.33 floor, where the full-list rate is 0.250). The design is
matched, so this touches the *absolute* collateral rate's resolution and never
the between-arm comparison. Per-operator item counts are reported beside the
rate.

---

## 3. Secondary, pre-specified

Pre-specified means: named here, before results, with its interpretation fixed.
It does **not** mean confirmatory — none of these carry a Holm correction and
none supports a headline claim.

1. **O1 vs the severe operators.** Per §15.6, the D13 audit found O1 (single-
   character corruption of a *real* id) lands with the production-caught
   defects, while O2/O3/O5/O6/O7 (fabrication, mislabelling, alien content) are
   markedly more severe than anything production catches. **Absolute repair
   rates are reported separately for the two cells and are never pooled.** The
   *contrast* is pooled — §2, decided 2026-09-08.

   - **(1a) The O1 × arm interaction, reported unconditionally.** The A1 − A2
     contrast estimated inside the severe cell (N = 118) and inside O1
     (N = 24), each with a cluster-bootstrap CI, printed beside the pooled
     primary in the same table **whatever they show** — not run only if the
     primary disappoints, and not omitted if they agree with it. This is the
     price of the pooling decision made visible; the O1 cell is small and its
     CI will be wide, and that is reported rather than smoothed. No Holm
     correction: it is secondary and supports no headline claim.

2. **A1/A0 ratio** with a cluster-bootstrap CI — how much of the model's
   capability ceiling the production feedback recovers. A0 is a ceiling, not a
   cost-matched competitor; calls per arm are disclosed.
3. **A3 share of A1 by stratum**, not pooled — Self-Edit predicts the gap
   widens on harder defects.
4. Per-class repair rates, with the directional prediction recorded in §5.
5. Stratification by defect origin (replayed-real vs synthetic) and by stage.
6. The two-stage chain *did the output change at all → did the targeted defect
   resolve* (MAS-FIRE's O/L decomposition; global success S is out of scope).
7. Terminal supervisor verdict per trial. If A1 repairs more defects without
   shifting the run-level verdict distribution, **that is a finding** (the one
   MAST predicts), not a failure.

---

## 4. Exclusions — fixed in advance, with their denominators

Every exclusion below is counted and reported. None is applied after seeing an
outcome.

| Exclusion | Rule | Denominator effect |
|---|---|---|
| **Injection not verified** (D20) | `verify_injection` says the target check did not fire, or an *additional* retry-level class appeared that was not in the base | removed at plan time, before any call; counted as **injection success rate** |
| **Not triggered** (D20, deciding §14.3) | the supervisor's verdict on the injected output is not `retry` | removed from the denominator, reported as a **separate count** — never scored `unrepaired`; see below |
| **Provider failure** | `status_error` on the retried output | pre-registered exclusion; the trial has no interpretation under any arm |
| **Fallback fired** | a call served by the fallback model (`LLM_DISABLE_FALLBACK=1` makes it an error rather than a silent failover) | discarded and logged; it breaks the matched comparison |

**Why untriggered defects are dropped rather than scored `unrepaired`.** If no
retry fires, no feedback of any kind reaches the model, so A1, A2 and A3 are the
same condition. Scoring such a trial would score the arms on a comparison that
does not exist. This follows AgentChaos §4.4, and it is the choice §14.3 left
open until D20.

**A `status_error` trial is never re-run until it succeeds.** That would be
resampling on the outcome. Resume re-runs a defect only after a harness
exception, which is a bug, not data.

**Schema-correction contamination.** A trial whose first call fails schema
validation is silently re-issued with the model's own invalid output in an
assistant turn — a P2-like condition inside what was meant to be a P0 or P1
trial. `attempts_made` is logged per trial. **Trials with `attempts_made > 1`
are analysed separately, not excluded**, and the primary estimate is reported
both with and without them.

---

## 5. Directional predictions, recorded before results

| Quantity | Prediction | Basis |
|---|---|---|
| A0 ceiling | high | neither literature disputes the underlying capability |
| **A1** | high; single-retry repair ≈ **45%** | Arimbur §V.E assertion-error class — *not* ~70%; the power calculation runs off 45% |
| **A2** | **≈70% of A1's gain over A3** | Self-Debug Simple rows, median 70% across seven model × benchmark settings |
| A3 | near zero or negative | Self-Debug Table 3b; Huang intrinsic rows |
| Class ordering | referential (O1/O2) > structural (O3, O6–O8) > semantic (O5) | — |
| Placement | **P1 ≫ P3 ≈ P2**; P0 reported separately, not folded into the ordering | Role Relabeling §4.3 |
| C1 interaction | **undetectable** — power 0.109–0.300 at N unreachable by a factor of three | D8c; reported as two gaps with CIs, never as a test |

**Pre-committed negative result.** If A1 ≈ A3 — feedback content adds nothing
over a bare re-draw — that is a publishable finding against the self-correction
literature's assumptions, and it is reported as the headline. The three-arm
design is declared here so that this is a result rather than an excuse.

---

## 6. The split rule (D11b), restated

The repair study may branch into a separate conference paper **iff the A1 − A2
point estimate is ≥ 12 pp AND its 95% CI excludes zero.**

X = 12 pp was fixed *before* the sample was sized, and the sample was then grown
to clear it: at N = 102 the MDE was 12.6 pp with the occasion effect — above the
threshold — and rather than lower X, eight more Phase-A dumps were collected,
taking N to 142 and the MDE to 10.9 pp. **Lowering X after seeing what the
design can detect is exactly the move this document exists to prevent.**

Power, for the record, at the delivered N = 142, r = 3 (`power.py --sims 20000
--defects 142 --seed 42`): **0.875 with the occasion effect, MDE 10.9 pp,
margin 1.1 pp.** Without the occasion effect, power 0.912 and MDE 10.2 pp; the
occasion column is the honest one, because §14.1 forces all arms for one defect
into a single session.

**Re-run 2026-09-08 after the D20 gates were wired, and it reproduced to the
digit** — 0.912 / 0.875 / 10.2 pp / 10.9 pp. That is a confirmation, not a
coincidence: the gates removed no defects, so the input to the calculation
never changed. It is recorded as a re-run rather than a carry-over because §6's
own instruction was to recompute, and an unchanged number that was actually
recomputed is a different claim from one that was assumed to still hold.

⚠ **That margin is thin and had two claims on it.** The O5 matcher fix (§16.6)
is bounded — the MDE stays under 12 pp even past losing O5 entirely. The second
claim is now discharged.

✅ **The D20 gates ran, 2026-09-08, and took nothing.** Injection success
**142/142 (1.00)**, trigger **142/142 (1.00)**, stable across seeds 0, 1, 42 and
20260803; `--plan-only` still reports **1,167 trials** at A1 426 / A2 426 /
A0 213 / A3 102. **N stays 142, so the power figure above stands as computed and
is not a projection.** Contingency if a later change takes N below ~130 remains
**r = 4**, never a smaller X.

⚠ **Do not read 100% as a strong result.** `applicable()` already encodes most
of what the gate re-checks, so on this bank the gate is a guarantee rather than
a discriminator. Its value is prospective — it fails loudly if an operator, a
base or a supervisor threshold changes — and it turns an assumption the whole
design rested on into a reported number. Both rates are reported with their
denominators either way.

---

## 7. The overwrite counterfactual (D19)

**In scope — decided 2026-09-08, §11 item 2. Exploratory, sequenced last, with
its interpretation fixed both ways.**

> **Yes, it runs — after the core, on a confirmed budget, and never in place of
> any part of the core.** It is pre-registered here, before any result exists,
> which is the only thing that makes it legitimate: deciding to add a cell after
> seeing core results would not be, and neither would quietly dropping it if the
> core comes out well.

O4 × {A1, A3}, P1, r = 3, **23 applicable defects ≈ 138 trials** (measured
2026-09-02, `inject_defects.py --matrix`), about **+10% on top of the ≈1,420
core + C1**. Frequency divergence is resolved by recompute-and-overwrite in
production (§4.5) and never reaches a retry; this cell routes it to retry
deliberately, outside the production path, to measure what the overwrite bought.
**Not pooled into the primary contrast** — O4 carries `ENDPOINT["O4"] =
"warn_level"`, so it is excluded from `REPAIR_OPERATORS` in code and cannot leak
into N = 142 by accident.

**Why in scope.** Conference §4.5 asserts a design principle — *any quantity the
checker can compute should not be asked of the model* — and **neither paper
contains a counterfactual for it.** §6.7 illustrates the principle; nothing
tests it. This cell is the test, it is the cheapest of the four supervisor
points, and the operator it revives is the only one in the grid with real
observed parameterisation (27 natural `frequency_corrected` observations).

**Why sequenced last, and what that is not.** It is ordered behind the core
because it exercises a scorer path that had never run, not because it is
optional. Sequencing is not a conditional: if the budget cannot cover it, the
paper reports the cell as **pre-registered and unrun**, with this section as the
record. What it must never become is a cell that runs only when the core result
makes it comfortable.

**Prerequisite, built 2026-09-08.** The scorer's O4 path is now under D18:
`IDENTITY_ANCHOR["O4"] = "description"` (the field `_apply_o4` leaves alone —
it mutates `frequency` only), `"O4"` added to `CAN_DELETE` but **not** to
`CAN_REPLACE`. Dropping the pattern rather than making a frequency claim is
evasion and scores `deleted`; a frequency within tolerance of the recomputed
value is correct by construction, so O4 has no passes-but-wrong-value mode and
would score every genuine repair as `replaced` if it were in `CAN_REPLACE`.
This is the divergence for which D18 named the two sets separately.

⚠ **Wiring it exposed a third gap D19's specification did not name:** `_hosts()`
mapped no item list for O4, so the anchor alone would have left `_base_host`
returning `None` and `deleted` structurally unreachable — the operator would
have kept scoring `repaired` for a dropped pattern, which is precisely the D18
bug. Fixed, with a test that fails on the old behaviour.

Both readings are fixed here, before the cell runs:

- If retry repairs frequency at a rate well below 1.0, or repairs it at cost in
  collateral churn, the overwrite decision was a **correctness** decision and
  §4.5's general principle is supported by measurement rather than assertion.
- **If retry repairs frequency at ~100% with no collateral churn, the overwrite
  decision was a cost optimisation, not a correctness one, and the paper says
  so.** The general principle then rests on the zero-call argument alone.

---

## 8. Analysis code, frozen with this document

The scorer and the gates are code, not prose, and they are frozen at the same
commit:

- `backend/scripts/analysis/score_repair.py` — the 4-class outcome, the
  collateral metric, the churn floors, and the O4 path added for §7. **27 tests.**
- `backend/scripts/inject_defects.py` — operators and `verify_injection`.
- `backend/scripts/run_injection_study.py` — iteration order, **the D20 gates in
  `build_plan`**, the two denominators in `plan_summary`, checkpointing, the
  exclusions. **28 tests.**
- `backend/scripts/analysis/power.py` — the MDEs quoted above.
- `backend/scripts/arms.py` — `AUTHORED_WORDING`, frozen 2026-08-25.

**The gates live in `build_plan`, not `run()`, and that placement is part of the
specification.** Both are pure `measure()`/`decide()` at zero API cost, so a
defect that fails one must leave the plan *before* any of its arms is paid for
and must be visible in `--plan-only`. Checking at execution time would mean
discovering a dead defect after buying its trials, and would let the two
denominators drift from the plan the analysis is read against.

A change to any of these after the freeze is an amendment under §0.

---

## 9. What this design does not remove

Recorded here so that no reviewer has to discover them:

- **A1 confounds *specific* with *correct*** (D14). There is no
  specific-but-wrong feedback arm, so the claim is about feedback **content**,
  not specificity.
- **One model, one provider, one pipeline, one domain** (D15).
- **The checks are shallow by design** (D16) — id resolution, set membership,
  `difflib` ≥ 0.35, exact containment. That determinism is the thesis.
- **The supervisor is not always right** (§15.4). The D13 audit found
  `untraceable_recommendation` to be a precision failure: 9 of 11 real
  production defects are checker false positives with a diagnosed cause. The
  repair study measures repair of *injected* defects and does not depend on the
  checker's production precision — but the paper states the finding rather than
  letting a reviewer find it.

---

## 10. Timestamps

| Event | Date |
|---|---|
| Arm wording frozen (`arms.py`) | 2026-08-25 |
| Phase-A collection complete (28 dumps, N = 142) | 2026-08-26 |
| D13 defect-bank audit executed | 2026-08-26 |
| Supervisor methodology review (D18–D21) | 2026-09-02 |
| `deleted` class implemented, suite 257 → 266 | 2026-09-02 |
| D20 gates wired; both pass 142/142; N unchanged | 2026-09-08 |
| D19 scorer path built (O4 anchor, `CAN_DELETE`, `_hosts`) | 2026-09-08 |
| §11 items 1, 2 and 4 decided | 2026-09-08 |
| First committed and pushed — safekeeping, **not** the freeze | 2026-09-14 |
| **This document frozen — annotated tag `prereg-freeze`** | *after the Q1 matcher decision* |
| **First trial** | *not yet run* |

⚠ **The row above is the gate on every row below it.** Zero trials have run.
The first spend after the freeze is the 7-cell live smoke test
(`tests/test_injection_seam_live.py -m integration`, 7–21 calls), which is the
first LLM call this study will have made.

---

## 11. ✅ CLOSED — the four items that blocked the freeze

All four closed **2026-09-08**. Three were decisions and are recorded in the
sections they govern; one was a build task and is in the code. This section is
kept as the record of what was open, what was chosen, and what was rejected —
deleting it would erase the evidence that the choices were made before any
result existed.

| # | Item | Resolution | Where it lives |
|---|---|---|---|
| 1 | Primary contrast: pooled, or severe cell only? | **Pool for the contrast, never pool the rates.** N = 142. The O1 × arm interaction becomes a secondary reported unconditionally. | §2, §3 item 1a |
| 2 | Is D19 (the overwrite counterfactual) in scope? | **Yes** — exploratory, sequenced after the core, pre-registered now so that adding it later could not be. Its scorer prerequisite is built. | §7 |
| 3 | The D20 gates are specified but not wired | **Wired** into `build_plan`, with two counters against two denominators. Both gates pass **142/142**; N does not move. | §4, §6, §8 |
| 4 | How is the per-defect dichotomy formed from r = 3? | **Majority** — strictly more than half of completed repetitions. `any-of-3` and `unanimity` rejected, with reasons. | §2.1 |

**Item 1's arithmetic, kept because §2 cites it.** These are the options that
were on the table when the pooling decision was made, so that a reader can see
the rejected ones rather than take the choice on trust
(`power.py --defects 118 --sims 6000 --seed 42`; coarser than the 20,000-sim
runs quoted in §6, so read to two significant figures):

| Primary cell | N | r | MDE w/ occasion | vs X = 12 pp |
|---|---|---|---|---|
| **Pooled — chosen** | **142** | **3** | **10.9 pp** | margin 1.1 pp ✅ |
| Severe only (O1 excluded) | 118 | 3 | 11.9 pp | margin 0.1 pp ⚠ |
| Severe only | 118 | 4 | 10.5 pp | margin 1.5 pp ✅, ~944 trials on A1/A2 alone |

The middle row is the one the design must never end up in: it is the
incoherent state — an MDE above the threshold it is required to clear — that
D11b's eight extra dumps were collected to escape. Had the estimand argument
favoured the severe cell, the answer was row three, not row two.

**Who decided, and what that means.** Items 1, 2 and 4 went to the supervisor as
`PHASE0_MEMO.md` Q3, Q4 and Q5 and were **decided by the author on 2026-09-08
without waiting for the answers**, because each is a choice that cannot
legitimately be made once a result exists and the study cannot begin without
them. They are authored positions, **open to supervisor override up to the
freeze tag** and thereafter only as a dated §0 amendment. The two questions
that are genuinely not the author's to answer — Q1, whether to fix the
`untraceable_recommendation` matcher now, and Q2, what to tell the conference
chairs about a paper under review — are **not** in this list and remain open;
neither blocks the freeze, because neither touches the analysis this document
specifies.

**What the closing changed in the numbers: nothing.** That was not the expected
outcome and it is worth stating plainly. The D20 gates were wired expecting them
to remove defects and eat into a 1.1 pp margin. They removed none — injection
success 142/142, trigger 142/142, stable across seeds 0, 1, 42 and 20260803.
The gates are therefore a **standing guarantee rather than a filter on this
bank**: they will catch a future operator, base or supervisor change that breaks
the assumption, and they convert an assumption the design was resting on into a
measured number. They are reported as exactly that, and never as a validation
step that "passed" in a way implying it discriminated.
