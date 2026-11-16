# Pre-registration — injected-defect repair study

**Status: FROZEN 2026-09-14 at the annotated git tag `prereg-freeze`.** All six
§11 items are closed. From here a change is a dated amendment under §0, and any
result it touches is reported as exploratory. No trial ran before the tag.

**The last item closed was §11 item 6 (2026-09-14): A3 is re-roled as a
regeneration baseline, and the confirmatory set is now the single A1-vs-A2
test** (§2, §2.1).

**Amendments A1–A15 are recorded in §0.1.** A1–A14 do not move the
core's confirmatory test. A15 specifies a separate prospective replication on
new model-specific bases; its repair trials require the pre-trial completion
note and the separate `prereg-fl-freeze` tag. **The core ran 2026-10-05 → 07**
(1,167 trials, 1,149 usable).

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
without them. **They are recorded as authored positions, confirmed by the author on
2026-09-14** (§11) — and changeable after the freeze only as a dated §0 amendment.
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

### 0.1 Amendments after the freeze

One line per amendment, dated, stating what changed and what it touches. The
freeze tag `prereg-freeze` (commit `5f78d21`) remains the reference point: this
section records every divergence from it.

| # | Date | Change | Status of anything it touches |
|---|---|---|---|
| **A1** | **2026-09-20** | **The C1 constraint-complete prompt is written, and factor C is wired into the runner.** Nothing above changes. | Exploratory — as §2.1 already had it |
| **A2** | **2026-10-07** | **The D19 pass is wired** (`--cell d19`): the trigger gate inverted to `proceed_with_warning` for O4 only, and A1 fed production's own `frequency_corrected` flags. | Exploratory — as §7 already had it |
| **A3** | **2026-10-07** | **The C1 cell runs as its own pass** (`--cell c1`), its C0 comparators re-run in the same session: 37 defects, 444 trials. | Exploratory; the re-run C0 cells also measure serving drift |
| **A4** | **2026-10-07** | **The confirmatory analysis code is written; one interim budget look is disclosed.** No rule changes. | None — records how §2–§4 were implemented |
| **A5** | **2026-10-07** | **The placement pass is wired** (`--cell placement`): A1 × {P0, P1, P2, P3}, r = 3, on a one-third per-operator stride — 45 defects, 540 trials — with P1 re-run in-session. | Exploratory — as §2.1 already had it; the §5 prediction is unchanged |
| **A6** | **2026-10-07** | **The O1 severity sweep is defined and wired** (`--cell severity`): level 2 = every resolving evidence id of the targeted pattern corrupted; A1 at P1, r = 3, all 24 O1 defects, both levels in-session — 144 trials. | Exploratory — as §2.1 already had it |
| **A7** | **2026-10-07** | **The warm-resample cell (plan D2) is wired** (`--cell warm`): temperature 1.0 on the placement subset — A1/A2 at 0 and 1.0, A3 at 1.0, r = 3, 675 trials. Designed after the ceiling was seen; both readings fixed below. | Exploratory |
| **A8** | **2026-10-08** | **The Tier-1 replay is wired** (`run_tier1_replay.py`): 13 real defects × {A1, A2, A3} at P0 × r = 3 = 117 trials, judged by the supervisor's own checks, intervals over cells. | Descriptive only — as plan §5 had it; serves §3 item 5 |
| **A9** | **2026-10-08** | **Downstream propagation (plan D12) is wired** (`run_downstream.py`), endpoint (b) chosen by the author: 90 defects × {clean ×2, unrepaired, A1, A2}, downstream stages once each through the production nodes; E1 accepted, E2 planted issue in the report (O5), E3 divergence vs an in-session noise floor. Brings into scope what §1 and §3 item 6 left out. | Exploratory |
| **A10** | **2026-10-12** | **C7 local replication is defined and wired**: Qwen2.5-7B-Instruct Q4_K_M, Ollama 0.40.3, RTX 5060 Ti 16 GB, 32k context, seed 20261012, temperature 0, output cap 4096. A1/A2 first draw over 142 defects, a second draw on a 1/6 operator stride (22), A3 on the frozen quarter stride (34): 362 trials before context exclusions. G1–G4 and the full protocol/readings are fixed in [`C7_PROTOCOL.md`](C7_PROTOCOL.md) before preflight; exact digest/provenance and passed gates are committed before final trials. | Exploratory; Gemini bases and all existing results remain fixed |
| **A11** | **2026-10-12** | **C7's original G2 failed (8/10 byte-identical; token calibration 10/10).** Before G4 or final data, use three repetitions per arm and defect-level means: 954 trials before context exclusions, 930 after. Preserve the failed G2 data; bit identity becomes a measured outcome, with calibration, context and schema reliability still gating collection. Full specification: [`C7_A11.md`](C7_A11.md). | Exploratory; no final A10 trial ran; runtime variability is disclosed |
| **A12** | **2026-11-01** | **Thinking-budget sweep on Gemini 2.5 Flash** (`--cell thinking` → `out_study/T2T`): 45 defects, 1,224 trials across `reasoning_effort` ∈ {`none`, `low`, `medium`, `high`}, dose-response trend test, exact copy contrast, repair decomposition. | Exploratory; core remains frozen |
| **A13** | **2026-11-13** | **S2 — the A0 ceiling is completed on `gemini-2.5-flash` before its withdrawal (1 Dec 2026).** `--cell a0fill` → `out_study/T2A0`: A0@P1 r = 3 on the 71 core defects the frozen A0 stride skipped, plus an in-session A1@P1 r = 1 anchor — 284 trials. `--cell thinking_a0` → `out_study/T2TA0`: on the 45 T2T defects, A0@P1 r = 3 and the A1@P1 r = 1 anchor at `reasoning_effort` `none` and `high` — 360 trials. Readings, including the case A1 ≥ A0 in restoration, fixed below. *Note 2026-11-14, after the data:* the share of the gap closed is not applicable when A0 − A2 lies wholly below 0 (S2b `none`); see the note at the end of A13. | Exploratory; cross-session joins to T2 and T2T are labelled as such; core and T2T untouched |
| **A14** | **2026-11-13** | **S3 — the real-defect bank is enlarged by harvest (Option H).** Phase A (observe) on 56 fresh businesses in two stratified batches of 28 into `out_study/H/A`; stop after Batch 1 if the pooled bank (T1 + T1H) reaches ≥ 18 business × stage cells; replay into `out_study/T1H` with the A8 design. T1, T1H and pooled reported side by side; one two-sided cell-cluster bootstrap test on A2 − A1 acceptance iff the pooled bank has ≥ 15 cells. | Descriptive, plus at most one test fixed here; T1 (A8) untouched |
| **A15** | **2026-11-16** | **S5 — prospective Flash-Lite replication, preparation protocol.** `flashlite_bases` collects the original 28 businesses into `out_study/FL/A` on `gemini-3.5-flash-lite`; `flashlite` → `out_study/T2FL` remains blocked until actual N_FL, power/MDE, determinism measurement, prospective readings and source/data hashes are recorded and tagged `prereg-fl-freeze`. Full A0/A1/A2@P1, r = 3; A3@P0 on the quarter stride. `flashlite_determinism` → `out_study/FL/determinism` measures ten prompt pairs before the final freeze; its dated rule is below. | Separate prospective exact-restoration test under I5; no repair trial before final freeze; core and T2T unchanged |

**A1 — the C1 cell, in full.**

*What existed at the freeze.* The B8 audit had run and is a passing gate:
`prompt_audit.py` adjudicated **5 of 5** obligations the supervisor asserts in
its retry feedback as stated in **no** stage prompt, and
`out_study/prompt_audit.json` records them. D8 permits either folding those into
a constraint-complete prompt **or recording the delta**; the delta was recorded,
which is why the audit never blocked a trial. What did not exist was the C1
prompt text itself, or any way for the runner to run the cell — the frozen plan
is 1,167 trials, all of them C0 under a label that was never written down
because it was the only condition.

*What this amendment adds.* The wording (`scripts/arms.py`, `C1_PREAMBLE` and
`C1_CONSTRAINTS`, printed verbatim by `python scripts/arms.py` and reproduced in
the appendix) and the wiring (`--c1` on `run_injection_study.py`).

*Why it is still exploratory, and was before this amendment.* D8c: detecting the
interaction has power **0.109–0.300** at sample sizes the Tier-2 ceiling puts out
of reach by a factor of three. §2.1 therefore already listed the C1 cell among
the exploratory analyses, and §5 already pre-recorded the prediction that the
interaction is undetectable and that the cell is reported **as two gaps with
CIs, never as a test**. This amendment does not move the cell between
categories; it makes an exploratory cell runnable. The confirmatory set is
unchanged and remains the single McNemar A1-vs-A2 at α = 0.05 (§2.1).

*What it does not touch.* The primary contrast, the outcome dichotomy, the
blocking, the exclusions, the split rule, the power gate, and the core's size.
`--c1` is **off by default** precisely so that the frozen core cannot move by
accident, and `test_the_frozen_core_is_unchanged_when_the_c1_cell_is_not_asked_for`
pins it at 1,167 C0 trials.

*Two files on §8's frozen list did change, and that is the point of filing this.*
`arms.py` gains the C1 wording and an `apply_condition` that is a no-op under
C0; `run_injection_study.py` gains the condition dimension, the `--c1` flag, and
a `condition` field on every trial row. Both changes are **additive**: with the
flag off, `build_plan` returns the same defects carrying the same cells, and
`test_adding_the_c1_cell_leaves_the_core_cells_byte_identical` asserts the core
cells are unchanged element for element when the flag is on. The scorer,
`content_match.py`, `inject_defects.py` and `power.py` are untouched. Two
invariants were **widened** rather than relaxed: `verify_order` now keys
contiguity on (condition, arm), because the C1 cell legitimately re-runs A1 and
A2, and it gained a check that a C1 cell holding only one arm is an error — a
half-populated cell yields no C0-vs-C1 contrast for that defect. Both new
failure modes have tests.

*The design, restated so this section stands alone.*

- **C0** is the production stage prompt. **C1** is that same prompt with the
  stage's own supervisor obligations spliced in ahead of its closing output
  instruction. Nothing else differs — same turns, same roles, same arm text.
- **One shared C0 base** (D8b option (ii)): both conditions inject into the
  identical base output, and only the retry prompt varies. The claim the cell
  licenses is therefore about **stating the constraints at retry time**, not
  about a constraint-complete pipeline. The paper must say so.
- **Crossed with {A1, A2} only** (D8d), at r = 3, on a stratified subset.
- Each clause restates the audit's `supervisor_asserts` field — the *obligation*
  — and never a retry string, which carries this defect's measured facts and is
  A1's manipulation. The **frequency** check is deliberately excluded: it
  resolves to `proceed_with_warning`, never to `retry`, so it never reaches an
  A1 feedback string, and stating it would give C1 information A1 does not have.

*Realised size, pinned here because it is not D8d's round number.* The subset is
selected by the same per-operator stride the arm subsets use, so that the
condition cannot fall in a block and confound itself with operator. Six
independent floors cost three defects against D8d's 40:

| | D8d as approved | Realised at N = 142 |
|---|---|---|
| Defects | 40 | **37** (6/6/6/5/7/7 across O1/O2/O3/O5/O6/O7) |
| Trials | ≈240 | **222** = 37 × {A1, A2} × r = 3 |

37 was preferred to a fraction tuned until it read 40: stratification is worth
more than the round number, and the cell is reported as an estimate with a CI,
where three defects move the interval by about 4%. `--plan-only --c1` prints
both numbers, and a test pins them — if the bank grows, this table must move
with it.

**A2 — the D19 pass is wired (2026-10-07).**

*What §7 already fixed.* The cell (O4 × {A1 at P1, A3 at P0}, r = 3), its size
(23 defects ≈ 138 trials), its sequencing (after the core) and both readings of
its result. §7 also said it is "a new A1 instantiation for a check that produces
no `retry_feedback` in production", to be logged as a dated addendum. This is
that addendum.

*What this amendment adds.* `run_injection_study.py --cell d19`, into its own
checkpoint `out_study/T2D19`. Two pieces of wiring had no specification and are
fixed here, before the pass runs:

- **The trigger gate is inverted for this pass only.** D20's trigger gate
  requires `retry`; O4 never reaches it — production returns
  `proceed_with_warning` and overwrites the value. The D19 gate therefore
  requires `proceed_with_warning`, which is the state whose overwrite the cell
  measures. Injection validity (D20 gate 2) is unchanged. All 23 applicable
  defects clear both gates.
- **What A1 receives.** `d19_decision()` takes the decision's own
  `frequency_corrected:{aspect}:{claimed}->{recomputed}` flags — the measured
  facts `supervision.py` already emits — joins them with ` | ` (how production
  joins retry problems) and hands them to the unchanged production template.
  Nothing else is added: no prose, no new wording. Production's `decide()` is not
  modified; the routing exists only in the runner, and the trial row records
  production's own verdict (`pre_verdict: proceed_with_warning`) beside the
  routed feedback.

*What it does not touch.* The core, the confirmatory test, the scorer (its O4
path was built 2026-09-08), `inject_defects.py`, `arms.py`. Tests pin the core at
1,167 trials with `--cell core`, the D19 plan at 23 defects / 138 trials with A1
at P1 and A3 at P0, and the feedback routing.

**A3 — the C1 cell runs as its own pass, with its C0 comparators re-run beside
it (2026-10-07; author's decision).**

*Why A1's wiring could not be used as written.* A1 attached the C1 cells to
the core defects, to run in the same pass. The core ran without `--c1`
(2026-10-05 → 07), as the plan sequenced it. After that, `--c1` cannot produce
the cell correctly: into `T2` it skips every C1 defect as already done, and into
a fresh directory it re-runs all 1,167 core trials as well. More importantly,
C1 run alone would be compared with C0 trials from a different session days
earlier, which §14.1 forbids for any within-defect contrast.

*What this amendment does.* `--cell c1` runs the **same 37 defects** `--c1`
selects (same stride, pinned by a test), each carrying **{A1, A2} under C0 and
then under C1**, r = 3, in one session per defect: **444 trials** into
`out_study/T2C1`. The C0-vs-C1 contrast is computed from this pass alone, so it
is matched within a session as §14.1 requires. The re-run C0 cells are not
pooled with the core's; compared against the core's C0 cells for the same
defects, they are a **test-retest measurement of serving drift**, reported as
such (exploratory).

*Status.* Exploratory, as A1 had it: two gaps with CIs (C0: A1 − A2; C1: A1 −
A2), never a test. Nothing confirmatory changes.

**A4 — the confirmatory analysis code, and one interim look (2026-10-07).**

`scripts/analysis/repair_analysis.py` implements §2–§4 and §6. It was written
after the core finished, transcribing rules this document fixed, and tested on
synthetic rows (`tests/test_repair_analysis.py`) before it read real data; its
SHA-256 is written into every output. One interim look happened during the core:
on 2026-10-05, after 12 of 142 defects, outcome counts and per-trial token
usage were inspected **to check the budget**. Nothing about the design, the
stopping point or the analysis changed as a result, and the run continued to
completion. It is disclosed so a reader does not have to take that on trust.

**What the core, D19 and C1 results were when A5 and A6 were written.** Both
amendments were filed after those three cells had run (core A1 ≈ 95 %, A2 ≈ 94 %,
at ceiling; D19 A1 100 %; C1 gaps both −1.8 pp). They are recorded here so that
nobody has to wonder whether the two cells below were designed to escape the
ceiling: their size and arms follow the plan's §6.2 grid, which predates every
result, and the one parameter the plan left undefined — O1's second severity
level — was chosen by the author between two candidates fixed before either
was run (below). Neither cell changes the confirmatory test.

**A5 — the placement pass (2026-10-07).**

*What the plan fixed before the freeze.* JOURNAL_PLAN §6.2: "Placement: A1 ×
{P0, P2}, r = 3, a third of the set", plus "(optional) P3 exploratory: A1, r =
3". D9 defines the four levels; §14.5 pinned P3's wording (`arms.P3_MARKER`,
frozen 2026-08-25). §5 above recorded the prediction **P1 ≫ P3 ≈ P2, with P0
reported separately**. The live smoke test ran A1 at P0, P2 and P3 on
2026-09-14.

*What this amendment fixes.*

- **All four levels, P3 included.** P3 was optional in the plan but §5 makes a
  prediction about it, and an unrun predicted cell is worse than a run one.
- **P1 is re-run inside the pass.** The core's P1 trials ran days earlier in
  other sessions; §14.1 forbids within-defect contrasts across sessions, and the
  C1 pass measured that drift is real (96 % same outcome class, 83 %
  byte-identical). This follows the author's A3 decision for the identical
  problem. The re-run P1 cells also give a second drift measurement.
- **The subset** is "a third of the set" by the same per-operator stride as
  every other subset (`_in_subset`, fraction 1/3): **45 defects**
  (8/8/7/6/8/8 across O1/O2/O3/O5/O6/O7) × 4 levels × r = 3 = **540 trials**,
  into `out_study/T2P`.
- **A1 only**, as the plan sized it. The "placement × arm interaction" §2.1
  lists is therefore **not estimable** from this cell; the paper says so rather
  than borrowing A2 from the core across sessions.

*Analysis* (`repair_analysis.py --cell placement`): A1 repair rate per level
with defect-bootstrap CIs, and the paired within-defect contrasts P1 − P2,
P1 − P3, P3 − P2 (the prediction) and P1 − P0. Estimates with CIs; the exact
McNemar printed beside each is descriptive.

**A6 — the O1 severity sweep (2026-10-07; levels and arms chosen by the author).**

*What the plan fixed before the freeze.* JOURNAL_PLAN §6.2: "Severity sweep: O1
two levels × a third of the set, r = 3, P1, ~100". The two levels were never
defined, and `_apply_o1` had no severity parameter: it drops one character from
one resolving evidence id of one pattern.

*The decision.* Two candidates were put to the author before either was built
or run: (a) **extent** — every resolving evidence id of the targeted pattern
loses one character, so per-id damage is unchanged and the pattern keeps no
valid support; (b) **depth** — 11 of the single id's 22 characters dropped,
which the supervisor's check reports exactly as it reports level 1. **The author
chose (a).** It also chose **A1 only** over A1 and A2.

*How it is built.* `inject(..., severity=2)` runs the frozen O1 operator first
and then, from the same random stream, corrupts every remaining resolving id of
the same pattern. **Level 1 is untouched**: on all 1,167 core trials the
modified injector reproduces the stored descriptor exactly, and a test pins
level 1 byte for byte. Level 2 always contains level 1's corruption, leaves the
pattern with no resolving id, and clears both D20 gates on 24/24 O1 defects —
checked in `build_plan`, so a defect enters only if **both** levels pass. The
scorer is unchanged: O1 restoration already compares the pattern's whole
evidence-id set.

*Size.* **All 24 O1 defects** × {level 1, level 2} × A1 at P1 × r = 3 =
**144 trials**, both levels in one session per defect, into `out_study/T2S`.
"A third of the set" in the plan cannot apply to one operator's 24 defects and
still yield "~100"; the plan's ~100 was all O1 defects at the time (17) × two
levels × r = 3, which is what this realises at 24.

*Analysis* (`repair_analysis.py --cell severity`): A1 repair rate at each level
with CIs and the paired level 1 − level 2 contrast; the re-run level 1 cells
are compared with the core's O1 A1 trials as a drift measurement.

**A7 — the warm-resample cell (2026-10-07).**

*What existed before the freeze.* Plan D2 marks "the warm-resample subset
(temperature > 0)" **REQUIRED**: it carries the Olausson equal-budget comparison,
"the first thing a testing venue asks about A3". It was never built — `BaseAgent`
hard-coded temperature 0 — and `PHASE0_MEMO.md` §7 item 3 asked for a choice
(build, drop or defer) that was still open at the freeze. This document did not
mention it. `PUBLICATION_STRATEGY.md` lists it in the "run first" set.

*What existed when this was written — stated because it matters.* The core
(null at ceiling), D19, C1 and placement (A1 at 94–98 % at every placement) had
run, and the core had shown **why** it sits at ceiling: 68 % of A1, 53 % of A2
and 45 % of A3 retries reproduce the clean pre-injection output byte for byte —
at temperature 0 the model re-derives its original answer. **This cell was
designed after seeing that**, and its first read tests that explanation. It is
exploratory and cannot be anything else.

*Design.*

- **Temperature 1.0.** D2 cites Tyen §4(d), which needed temperature 1 to force
  a different step; it is also the provider's default sampling temperature.
- **Defects:** the placement subset — 45 defects, one-third per-operator
  stride — so the cell stratifies exactly as A5 did.
- **Cells, one session per defect, r = 3:** A1@P1 and A2@P1 at temperature 0 (the
  in-session comparators, as for C1 and placement), A1@P1 and A2@P1 at 1.0, and
  A3@P0 at 1.0 → 15 trials per defect, **675 trials** into `out_study/T2W`.
- **How it is built.** `BaseAgent.temperature` is a class attribute defaulting
  to 0, read by `_create` and written to the call log. Production never sets
  it; the runner sets it on each trial's own freshly constructed agent. Tests
  pin the class default at 0 and the core plan at 1,167 temperature-0 trials.

*Reads, fixed before the pass runs* (`repair_analysis.py --cell warm`):

1. **The mechanism.** The share of retries byte-identical to the clean output,
   per (arm, temperature).
2. **The contrast.** A1 − A2 at temperature 1 beside the in-session gap at 0,
   both with CIs, and their difference with a CI — two gaps, never a test.
3. **The equal-budget baseline.** A3's best-of-k (k = 1..3, in repetition order)
   at temperature 1 against A1's single shot at 0, with mean tokens per trial,
   so a best-of-k costs k × A3's tokens.
4. Every estimate also without `attempts_made > 1` trials (§4).

*Interpretation, fixed both ways.* **If** the byte-identity share falls at
temperature 1 while repair stays near ceiling and A1 − A2 stays near zero, the
core's null is not an artefact of verbatim re-derivation: the defects are easy
for this model however it samples. **If** repair falls at temperature 1 and the
A1 − A2 gap opens, the core's null was a temperature-0 artefact, and the paper
says so in those words.

**A8 — the Tier-1 replay (2026-10-08).**

*What existed before the freeze.* §3 item 5 pre-specifies "stratification by
defect origin (replayed-real vs synthetic)", which needs trials on the real,
production-caught defects. Plan §5 (Tier 1) fixed the design: placement **P0**
(D10 — the defect really was the model's own and the production retry really is
blind to it), arms {A0, A1, A2, A3}, r = 3, "repair judged at that stage by the
same checks", **descriptive only** (MDE ≈ 31 pp; "no hypothesis test may be run
on Tier 1"). No runner existed.

*What this amendment fixes.*

- **The bank:** the 13 usable entries of `analysis/defect_bank.py` (8
  `untraceable_recommendation` at strategy, 3 `missing_evidence_id` and 2
  `misaligned_aspect` at reasoning) in 7 business × stage cells. A defect runs
  only if replaying its dump reproduces the recorded retry exactly — verdict,
  fired classes and feedback string. **All 13 do.**
- **Arms A1, A2, A3 at P0, r = 3 → 117 trials** into `out_study/T1`. A0 cannot
  run at P0 (D9b), so the plan's 132 realises as 117. A1 at P0 *is* the
  production retry.
- **Outcome.** No clean reference exists for a real defect, so there is no
  replacement value. A retried output is **accepted** when no retry-level class
  fires on it; **target resolved** when none of the originally fired classes
  does. For the trace class, D22's content-word trace is reported beside the
  production verdict. Also reported: how often a retry returns the original
  defective output unchanged.
- **Intervals resample business × stage cells**, never defects (§2.2). No
  p-values.
- **A caveat recorded before the run:** D13's blinded raters called **0 of 11**
  of these defects an error — most are checker false positives (§15 of the
  plan). This cell therefore measures what the production retry *does*, not
  whether it repairs a real fault.

*Runner:* `scripts/run_tier1_replay.py` (fallback disabled, one session per
defect, resume by whole defect, `status_error` excluded, same row fields as the
Tier-2 runner). *Analysis:* `repair_analysis.py --cell tier1`.

**A9 — downstream propagation (2026-10-08; endpoint chosen by the author).**

*What existed before the freeze.* Plan D12 moved downstream propagation in scope
and made the runner persist each retried output with enough state to re-run the
later stages; `PUBLICATION_STRATEGY.md` names it the journal's thesis —
*defect-level repair does not equal pipeline-level improvement* (MAST App. J).
This document said the opposite in §1 and §3 item 6 ("run-level utility is out
of scope", "global success S is out of scope"). **This amendment brings it in, as
exploratory.** No endpoint was ever fixed; the author chose one on 2026-10-08
from three put to them: (a) supervisor verdicts only, **(b) verdicts plus a
no-repair baseline plus divergence from the clean pipeline**, (c) an LLM judge
(out of scope per the plan). **(b).**

*What existed when this was written.* Every other cell had run: the core (null
at ceiling), D19, C1, placement, severity, warm and the Tier-1 replay.

*Design.* Every core defect with a downstream stage — O1, O2, O3 (reasoning)
and O5 (strategy): **90 defects**. O6/O7 are report-stage and have none. For each
defect, in one session, the downstream stages are re-run from five starting
points: the **clean** output twice (the second run is the in-session noise
floor), the **unrepaired** injected output (the no-repair baseline), and the
core's retried output for **A1** and **A2** at repetition 0 (the first executed,
fixed before any downstream result). Each downstream stage runs **once** through
the production node at temperature 0 and is measured and judged by the
supervisor, never retried — observe mode, as Phase A ran. **447 conditions, 796
calls**, into `out_study/T2D`; 3 arm outputs are missing because the core trial
was a `status_error`, and are counted.

*Endpoints.*

- **E1 accepted** — every downstream stage passes the supervisor (no `retry`
  or `halt`).
- **E2 (O5 only)** — the planted recommendation issue survives into the final
  report (content-word Jaccard ≥ 0.20 against any report recommendation, the
  D24 identity threshold).
- **E3 divergence** — the share of the clean run's final-report claims (root
  causes and recommendation issues) with no content-word partner (Jaccard ≥
  0.20, greedy one-to-one) in the condition's final report, read against the
  clean-vs-clean divergence of the same defect.

Contrasts, paired within defect with defect-bootstrap CIs: unrepaired − clean,
A1 − unrepaired, A2 − unrepaired, A1 − A2, A1 − clean for E1; each condition −
noise floor, A1 − unrepaired and A1 − A2 for E3. Also the coupling table: the
core's defect-level outcome for that repetition against E1.

*Readings, fixed before the pass runs.*

1. **The defect propagates silently** if the unrepaired runs are accepted about
   as often as the clean ones while their reports diverge beyond the noise
   floor: the supervisor's checks are local and do not see an upstream defect
   once it has been built upon.
2. **Repair restores the pipeline** if A1 and A2 bring E3 back to the noise
   floor where the unrepaired run diverges.
3. **The defect is absorbed** if the unrepaired runs do not diverge beyond the
   noise floor either: repair then buys groundedness at the defective stage and
   nothing visible downstream — "runtime verification buys groundedness, not
   utility".

*Runner:* `scripts/run_downstream.py`. *Analysis:* `repair_analysis.py --cell
downstream`.

**A12 — the within-weights thinking-budget sweep on Gemini 2.5 Flash (2026-11-01).**

*Status: Approved by supervisor (Option A) following upstream HTTP 404 endpoint rejection on gemini-2.5-flash-lite; wired and ready to run.*

*What existed before this amendment.* The core (T2, Gemini 2.5 Flash, 1,167 trials),
D19, C1, placement (T2P), severity (T2S), warm (T2W), Tier-1 (T1), downstream
(T2D, 447 conditions), and C7 (T2L, Qwen2.5-7B, 930 trials) had all run. The
supervisor feedback (2026-10-30) established that:
1. Exact restoration (P(exact copy)) differs between Gemini (+14.6 pp [+8.2, +21.3],
   p=0.0013) and Qwen (+2.7 pp [-4.0, +9.5], p=0.463);
2. Downstream E3 report churn is driven almost entirely by reasoning-stage
   rewrites (16.65 % vs 4.16 % copy, against 2.6 % noise floor);
3. Search difficulty scales with review count (14 -> 34 -> 92 -> 214) for reasoning
   operators (O1, O2, O3) while report-stage controls (O5, O6, O7) remain flat.
To test whether test-time compute (thinking budget) modulates feedback utility
and copy-and-correct restoration without the confounding factors of cross-model
architecture or tokenization changes, this amendment implements a within-weights
thinking-budget sweep on the primary model `gemini-2.5-flash`.

*Design.*
- **Model & runtime:** `gemini-2.5-flash` accessed via Google's OpenAI-compatible
  endpoint with explicit `reasoning_effort` parameterized per request, `temperature = 0`,
  `LLM_DISABLE_FALLBACK=1`, identical 45 defects from the placement 1/3 per-operator
  stride across the 28 Gemini bases, one session per defect (defect-outer loop), r = 3.
- **Thinking budgets & efforts:**
  Four levels spanning 0 to 24,576 tokens:
  - `none`: 0 tokens
  - `low`: 1,024 tokens
  - `medium`: 8,192 tokens
  - `high`: 24,576 tokens
- **Arms & trials (1,224 trials total):**
  - 45 defects selected via 1/3 per-operator stride (`PLACEMENT_FRACTION = 1/3`).
  - Arms A1 and A2 across all 45 defects: 45 defects × 2 arms × 4 efforts × 3 reps = 1,080 trials
    (540 A1, 540 A2).
  - Arm A3 at P0 on the 1/3 subset of those defects (12 defects = 2 defects per operator
    across all 6 operators): 12 defects × 1 arm × 4 efforts × 3 reps = 144 trials.
  - Total trials: 1,224 trials (exactly 306 trials per reasoning effort: 306 none, 306 low,
    306 medium, 306 high).
- **Output directory:** `backend/out_study/T2T/checkpoint.jsonl`.
- **Budget guard:** Projecting ~17.4 M tokens (1,224 trials × ~14.2k tokens/trial).
  Spent ~53.1 M + projected ~17.4 M = ~70.5 M < 75 M ceiling in `RUN_QUEUE.md`.

*Prospective Readouts & Hypotheses (fixed before collection):*
1. **Dose-response trend test:** OLS slope of A1 − A2 repair gap against effort rank
   (0..3) and against log-budget (−log2(1 + budget_e)), tested with cluster bootstrap 95 % CI
   over defects. Tests whether additional reasoning tokens substitute for informative
   feedback (narrowing A1 − A2) or amplify feedback utilisation (widening A1 − A2).
2. **Level-specific repair rates and within-effort contrasts:** Evaluated for each
   effort level e ∈ {none, low, medium, high} (A1@e − A2@e) with defect-bootstrap CIs.
3. **Cross-effort contrasts against high baseline:** A1@e − A1@high and A2@e − A2@high
   to measure diminishing returns in test-time compute for structured repair.
4. **Prospective test of P(exact copy) contrast & 4-way decomposition:** Unconditional
   contrast P(exact copy) A1 − A2 and full 4-way decomposition (repaired_copy,
   repaired_rewrite, replaced_or_deleted, unrepaired) across effort levels to determine
   whether extended thinking promotes copy-and-correct or generative rewrite.
5. **Serving drift:** Comparison of in-pass unthought / baseline runs vs frozen core
   for the same 45 defects.
6. **Token & latency calibration:** Empirical thinking tokens (completion_tokens −
   prompt_tokens) and wall-clock latency recorded per trial row and aggregated by effort level.

*Runner:* `backend/scripts/run_injection_study.py --cell thinking`.
*Analysis:* `backend/scripts/analysis/repair_analysis.py --cell thinking`.

**A13 — completing the A0 ceiling (S2a `a0fill`, S2b `thinking_a0`) (2026-11-13).**

*Why now.* The provider announced on 3 November 2026 that `gemini-2.5-flash` is
withdrawn on 1 December 2026. These are the last trials that can be run on the
study's model. The supervisor's request (2026-11-13, item 2): A0 on all 142
defects, and A0 at `none` and `high` in the sweep, because the +23.7 pp
restoration gap has no ceiling to compare against.

*What existed when this was written.* Every cell through A12 had run and been
analysed. The numbers this amendment is written against:

- Core (T2): A0 ran on 71 of 142 defects (213 trials, 209 usable; `ARM_FRACTION`
  stride 0.5 per operator). A1/A0 repair ratio **0.96 [0.92, 1.00]** on those 71.
  Exact restoration (canonical-JSON identity to the clean output, all trials):
  **A0 71.3 % (149/209), A1 68.4 % (288/421), A2 53.5 % (223/417)**. The A0
  stride covered 1 of the 5 O1 defects at p90.
- Sweep (T2T): exact restoration A1 **80.7 %** vs A2 **57.0 %** at `none`
  (+23.7 pp [+12.6, +36.3], McNemar p = 0.00098); A1 60.7 % vs A2 50.4 % at
  `high` (+10.4 pp [−3.0, +23.0], p = 0.30). Binary repair 100 % at `none`.
- A 1-call live smoke on 2026-11-13 returned `served_model = gemini-2.5-flash`,
  no fallback.

*Design — S2a, `--cell a0fill` → `out_study/T2A0`.*

- **Defects:** every core defect for which the core's A0 stride
  (`_in_subset(op_index, 0.5)`, per-operator index, the core's `build_plan`
  order, D20 gates and injection seed 0) is false: **71 defects**, the exact
  complement of the core's 71 A0 defects (pinned by
  `test_a0fill_is_the_exact_complement_of_the_core_a0_stride`).
- **Cells, one session per defect, in this order:** A0@P1 × r = 3, then A1@P1 ×
  r = 1 (the in-session anchor, author decision I3). C0, temperature 0,
  `reasoning_effort` omitted (provider default, as the core). **284 trials**
  (213 A0 + 71 A1).

*Design — S2b, `--cell thinking_a0` → `out_study/T2TA0`.*

- **Defects:** the same 45 defects as T2T (placement one-third per-operator
  stride); verified identical to T2T's runnable set in the plan test.
- **Cells, one session per defect, arm-major:** A0@P1 r = 3 at `none` then
  `high`, then the A1@P1 r = 1 anchor at `none` then `high`. **360 trials**
  (270 A0 + 90 A1; 180 per effort). `low` and `medium` are not run.

*Runtime, both cells.* Model pinned in code: `agent._model` and
`agent._fallback_model` = `gemini-2.5-flash` inside `_regenerate`, and
`OPENAI_MODEL` / `OPENAI_FALLBACK_MODEL` = `gemini-2.5-flash` with
`LLM_DISABLE_FALLBACK=1` set by the runner before any agent exists. Order of
operations: `--plan-only` → `--dry-run` → this amendment committed → live run
(S2a, then S2b). Exclusions as §4 (`status_error`, fallback fired); resume by
whole defect.

*Verification gate.* Complete checkpoint (97 rows / 284 trials; 71 rows / 360
trials); one `session_id` per defect; every trial's `served_models` equal to
`["gemini-2.5-flash"]`; offline re-score agrees with the live score on every
trial.

*Readouts, fixed before any A0 trial runs.* Analysis:
`repair_analysis.py --cell a0fill` (joins T2 + T2A0 on `defect_id`) and
`--cell thinking_a0` (joins T2T + T2TA0 on `defect_id` and effort). The r = 1
anchor is analysed under its own arm name and is never pooled into the 3-rep A1.

S2a:
1. A1/A0 repair ratio over all 142 defects (A0 pooled from T2 and T2A0; A1 from
   T2), beside the existing in-session 71-defect ratio; and the in-session
   anchor/A0 ratio and anchor − A0 contrast on the 71 new defects.
2. A0 repair and A0 exact restoration by operator and by review-count stratum
   (all five O1 p90 defects now carry A0).
3. A0, A1 and A2 exact restoration over 142 defects with defect-bootstrap CIs;
   contrasts A1 − A0, A0 − A2, A1 − A2.
4. Drift: anchor A1 against the core's A1 rep 0 on the same 71 defects
   (outcome class and byte identity), and their restoration rates side by side.

S2b, at each of `none` and `high`:
1. A0 exact restoration (defect-level mean, defect cluster-bootstrap 95 % CI).
2. A0 − A1 and A0 − A2 in exact restoration (A1, A2 from T2T, cross-session),
   with bootstrap CIs; anchor − A0 within session beside the cross-session
   A1 − A0.
3. **Share of the gap closed**, (A1 − A2)/(A0 − A2), reported **only if** the
   95 % CI of A0 − A2 excludes 0; otherwise withheld and the reason printed.
4. A0 repair at both levels (expected near 100 %; reported, not tested).
5. Drift: anchor A1 against T2T A1 rep 0 at the same effort.

*Readings, fixed now (applied to A1 − A0 in exact restoration, per effort in
S2b and pooled in S2a).*

- **Ceiling.** A1 − A0 < 0 and its 95 % CI lies below 0: A0 sets a restoration
  ceiling, and the A1 − A2 gap is read as A1 approaching it; the share of the
  gap closed (if reported) says how far.
- **A2 below the task level.** A1 − A0 ≥ 0 by the point estimate: A0 is a repair
  ceiling by design but not a restoration ceiling. Measured facts restore at
  least as often as a direct correction request, and the +23.7 pp is read as A2
  falling below the correction-task level, not as A1 approaching a ceiling.
  (The core already leans this way: A0 71.3 % vs A1 68.4 %.)
- **Indeterminate.** A1 − A0 < 0 with a CI that includes 0: neither reading is
  claimed; the estimate is reported.

*Session caveat.* Every A0 trial runs in a later session than the T2/T2T arms it
is compared to. That is the one exception to within-session matching in the
study and is stated wherever a cross-session contrast is printed. The anchor
measures the drift directly; the within-session anchor − A0 contrast is reported
beside every cross-session one. No test in this amendment is confirmatory, and
the core's RQ1 test is unchanged.

*Cost (logged, uncapped per I7).* From measured means (T2: A0 11.75 k, A1
14.27 k tokens/trial; T2T: A1 7.8 k at `none`, 10.1 k at `high`, used for A0 at
the same effort): S2a ≈ 3.5 M, S2b ≈ 3.2 M, **≈ 6.7 M tokens**.

*Code.* `run_injection_study.py --cell a0fill | thinking_a0`;
`repair_analysis.py --cell a0fill | thinking_a0`; tests in
`tests/test_run_injection_study.py` and `tests/test_repair_analysis.py`. Script
hashes are recorded in the amendment commit message.

*Note on the share of the gap closed (2026-11-14, written after the S2a and S2b
data were seen).* S2b readout 3 assumed that A0 sits above A2, so that A0 − A2
is a gap A1 can close part of. It does not say what to do when A0 sits *below*
A2. At `none` it does:

| Exact restoration at `none` (45 defects) | |
|---|---|
| A0 | 38.5 % |
| A1 | 80.7 % |
| A2 | 57.0 % |
| A0 − A2 | −18.5 pp [−31.1, −7.4] |
| A1 − A2 | +23.7 pp |

The CI of A0 − A2 excludes 0, so the rule as filed reports the ratio:
(A1 − A2)/(A0 − A2) = **−1.28 [−3.90, −0.51]**. A negative share has no
"gap closed" meaning, because there is no gap from A2 up to A0. The A13 reading
at `none` is already *A2 below the task level*, under which the share is not
interpreted.

The rule is therefore clarified as follows. The share is reported only when the
CI of A0 − A2 lies wholly **above** 0.
- When the CI lies wholly below 0, the share is recorded as **not applicable
  (A0 below A2)**. Its value under the literal rule is kept in `analysis.json`
  and in this note, but not in a results table.
- When the CI includes 0, the share is withheld, as before.
- In every case A0 − A2 and A1 − A2 are reported with their CIs, so withholding
  the ratio removes no information.
- A share above 1 means A1 restores more often than A0, not that it "closes"
  more than the whole gap. S2a's pooled share is 1.24 [0.74, 2.50].

What this changes:
- It touches one descriptive line (S2b `none`). The `high` share stays withheld
  (CI of A0 − A2 includes 0), and S2a's share stays reported.
- No reading changes: both efforts and S2a read *A2 below the task level*.
- No test is affected, and the core and T2T are untouched.

Code: `repair_analysis.share_of_gap` (test
`test_share_of_gap_is_not_applicable_when_a0_is_below_a2`).

**A14 — the real-defect bank, Option H (harvest) (2026-11-13).**

*Decision.* The supervisor asked (2026-11-13, item 3) for an explicit choice
between harvesting more real defects and limiting the claims to what 13 allow.
The author chose **harvest (H)** on 2026-11-13 (I2), with the rules below (I6).

*What existed when this was written.* T1 (A8): 13 usable real defects in 7
business × stage cells across 6 businesses (8 `untraceable_recommendation`, 3
`missing_evidence_id`, 2 `misaligned_aspect`), from 53 observe-mode runs (6
defects from the 28 Phase-A runs, 7 from the 25 repetition runs in `R`).
Acceptance after the retry: A1 28.2 %, A2 76.9 %, A3 25.6 % (descriptive). D13's
blinded raters judged 9 of 11 audited bank defects checker false positives.

*Businesses.* `sample_businesses.py --per-stratum 21 --seed 20260803` (84
businesses, 21 per stratum, every one at its stratum's target count: 14 / 34 /
92 / 214 reviews) minus the 28 of `out_study/sample.json`, which are verified to
be the first 7 of each stratum (prefix-stable). The 56 fresh businesses are
split in draw order into **Batch 1** (the next 7 per stratum, 28) and **Batch 2**
(the following 7 per stratum, 28): `out_study/H/sample_batch1.json`,
`sample_batch2.json` (full draw: `sample_superset_ps21.json`). No business is
added or removed by hand. (Batch 2's p25 includes "Ghost Party Haunted Tours",
which Yelp lists under Restaurants; it stays, by the no-hand-picking rule.)

*Harvest.* `MAX_REVIEW_SAMPLE=500 python scripts/run_study.py --phase A --sample
out_study/H/sample_batch1.json --out out_study/H --model gemini-2.5-flash`
(the `--model` flag pins primary and fallback and sets
`LLM_DISABLE_FALLBACK=1`); p90 businesses load all 214 reviews. Then
`analysis/defect_bank.py --root out_study/H`, and the A8 replay gate (a defect
runs only if replaying its dump reproduces the recorded retry exactly).

*Stopping rule (checks cell count only, before any T1H trial).* After Batch 1,
count distinct business × stage cells in the pooled usable bank (T1's 7 + H's).
**≥ 18 → stop harvesting.** Otherwise run Batch 2 the same way and stop there
regardless of yield (hard cap: 56 new businesses). Outcomes are never looked at
before the stop decision.

*Replay.* `run_tier1_replay.py --root out_study/H --out out_study/T1H --model
gemini-2.5-flash`: the A8 design unchanged — A1, A2, A3 at P0, r = 3, judged by
the supervisor's own checks, one session per defect.

*Reporting, fixed now.* The primary RQ3 table shows **T1** (13 defects / 7
cells), **T1H**, and **Pooled (T1 + T1H)** side by side, plus a **single-pass
sensitivity (A + H)** that drops the defects found only in `R`'s repeated runs.
For each: acceptance by arm, target-resolved by arm, clean-check pass rate, the
A2 − A1 and A1 − A3 acceptance differences with **cell-cluster** bootstrap 95 %
CIs (resampling business × stage cells, never defects).

*The one test.* **Iff the pooled bank has ≥ 15 distinct cells**, one two-sided
cell-cluster bootstrap test of A2 − A1 acceptance on the pooled bank, α = 0.05:
rejects iff the percentile 95 % CI excludes 0; the two-sided bootstrap p
(2 × the smaller tail share at 0) is reported. Below 15 cells no p-value is
reported, citing the small-cluster Type I inflation (§4.7 of the paper). No
other test is run on Tier 1.

*Cost (logged, uncapped per I7).* Phase A ≈ 41 k tokens per business (1.16 M
per batch); replay ≈ 318 k tokens per defect (T1: 4.13 M for 13). At the
Phase-A yield (~0.21 cells per business): ≈ 1.2–2.3 M harvest + ≈ 3.8 M replay,
**≈ 5–6 M tokens**.

*Known limit, recorded before the harvest.* A larger bank still contains what
`gemini-2.5-flash` gets wrong and what the checks flag, so it raises N without
fixing class coverage or checker precision.

*Code still to write before the first T1H trial* (committed and hashed then):
the pooled / A + H / cell-count stopping report and the ≥ 15-cell test in
`repair_analysis.py --cell tier1` (currently single-checkpoint).

*Code written 2026-11-14, before any T1H trial:* `repair_analysis.py
--cell tier1_pooled` (`--checkpoint` T1, `--t1h-checkpoint` T1H). The T1 column
reproduces `out_study/T1/analysis.json` exactly. Three operational definitions
the text above left open, fixed here before any T1H outcome exists:

- **Clean-check pass** means the supervisor's verdict on the retried output is
  `proceed`: no check fires at any level. *Accepted* also counts
  `proceed_with_warning`, so the clean-check rate is never above acceptance.
  On T1: A1 23.1 %, A2 64.1 %, A3 25.6 %.
- **A + H** means defects whose bank source label is `A`, that is Phase-A dumps
  from `out_study/A` and `out_study/H/A`. It drops the `rep*` sources of
  `out_study/R`. On T1 that leaves 6 defects in 6 cells.
- **The ≥ 15-cell gate** counts the pooled cells that carry an A2 − A1
  difference, meaning at least one usable A1 trial and one usable A2 trial. It
  is the same count as the bank's cells unless a cell's trials all error. The
  analysis refuses to run if a defect appears in both T1 and T1H, or if one
  business × stage pair appears under two cell labels.

**A15 — S5 Flash-Lite replication: preparation protocol (2026-11-16).**

*Scope and prior knowledge.* The author approved this two-stage filing on
2026-11-16. The Gemini 2.5 Flash core, exploratory restoration results, C7,
A12, A13 and A14 outcomes already exist. In particular, the restoration rates
used for planning (about 0.68 for A1 and 0.53 for A2) are historical core
observations. S5.0's model-availability smoke calls also already exist
(`SUPERVISOR_FEEDBACK_2026-11-13.md` §8). No S5 own bases, determinism pairs or
repair trials exist when this entry is written. N_FL and its MDE are unknown;
the 142-defect fixture is not this study's denominator.

This is an independently prospective replication on fresh, model-specific
outputs, as approved in I4/I5. Its single primary test is the limited exception
to §0's exploratory status for post-core amendments: it does not reclassify a
historical result or change the original core test. All other S5 contrasts are
exploratory. The core (1,167 trials) and T2T (1,224) stay frozen.

*Stage 1: bases, before any collection call.* Commit and push this preparation
protocol and tested runner before collection, using the author's git go-ahead.
Only `flashlite_bases` is released from preparation-only status; all normal
`cell.py` gates still apply. A live launch requires the author's run approval.
The trial cell `flashlite` stays `preparing=True`. Use `cell.py` for preflight,
launch, status and verification, never a direct live runner command.

- **Model:** `gemini-3.5-flash-lite`; temperature 0;
  `reasoning_effort=None` (omit the argument, never the string `none`). Pin
  `agent._model`, `agent._fallback_model`, `OPENAI_MODEL` and
  `OPENAI_FALLBACK_MODEL` to that model, and `LLM_DISABLE_FALLBACK=1`.
  Verify every served-model record, including the base dumps; no mixed-model
  or fallback base is admitted.
- **Bases:** Phase A, observe mode, on exactly the original 28 businesses in
  `out_study/sample.json`, into `out_study/FL/A`. `MAX_REVIEW_SAMPLE=500`,
  `RANDOM_SEED=42`, seven businesses each at 14/34/92/214 loaded reviews.
  No `--sample-size 100`, `--allow-cap`, replacement businesses, original-model
  dump substitution or outcome-selected removal. Preserve all raw rows/dumps,
  errors, token accounting, model IDs and review-seed metadata.
- **Base check:** complete fixed-sample coverage; correct dump types and
  primary/fallback provenance; observe-mode summaries and checkpoint rows;
  full review counts and seed 42. An absent or incomplete base collection is
  a failed gate, not N_FL = 0.

*Stage 2: pre-trial completion and freeze.* After base verification, build the
new model's injection plan using the unchanged applicability, injection-validity
and trigger gates (D20). Record attempted/applicable/valid/triggering and
runnable denominators by operator and the exact N_FL. Injection seed is 0;
report the A3 stride count Q_FL and total `9 * N_FL + 3 * Q_FL` trials.

Measure ten real prompts twice as in C7 G2, retaining both raw responses,
prompt identifiers/hashes, model IDs, usage and errors. Identity is a measured
outcome, not a gate; r = 3 regardless. The dedicated collector, its deterministic
prompt-selection rule and `cell.py` registration must be implemented, tested
and committed before those calibration calls; calibration responses never
enter repair-trial denominators or choose later defects/arms. Report incomplete
or invalid pairs explicitly rather than silently replacing them.

Run `analysis/power.py --flashlite-defects N_FL` on the actual gated N_FL.
Simulate r = 3 and the complete joint replication criterion below, including
strict defect-majority exact McNemar and the defect-mean bootstrap CI. Planning
uses marginal A1/A2 probabilities 0.68/0.53, the half-size effect 0.605/0.53,
and the null 0.53/0.53. Record the logistic-normal defect SD (default 1),
shared-occasion SD (default 0), seed 20260803, simulation/bootstrap counts,
Monte Carlo uncertainty, joint power and the 80%-joint-power MDE. These are
assumptions, not Flash-Lite observations. If the MDE exceeds about 15 pp or
cannot reach the target, the author decides whether to add bases **before**
freezing; extra repetitions do not replace that decision. Any sample expansion
requires a dated prospective specification and an updated base validator.

Append a dated completion note here with the plan/denominators, N_FL, power
JSON and MDE, determinism report, the prospective conditional A0-ceiling /
dissociation prediction, runtime/dependency versions, and final code/data
SHA256s. Record that prediction without inspecting repair-trial A0/A1/A2
outcomes. Include the completion note and trial-cell release in one final
commit, push it, then tag that commit `prereg-fl-freeze` and push the tag before
the first repair trial. `cell.py` checks the tag's commit is on the upstream
branch and that tagged sources/bases are unchanged. This initial entry is
**not** that freeze.

*Repair design, fixed now.* One session per defect, defect-outer execution,
C0 prompts, temperature 0, no reasoning-effort override. A0, A1 and A2 at P1
on **every** runnable own-base defect, each r = 3. A3 at P0, r = 3, on the
existing quarter per-operator stride (no outcome-selected subset). Operators
and checks retain their existing definitions; O1/O2/O3 stay separate and O5–O7
are flat controls. Output goes only to `out_study/T2FL`.

*Primary outcome and one test.* Exact restoration is canonical-JSON identity
(sorted keys, invariant whitespace) of the retried stage output to the model's
own clean pre-injection output, unconditioned on repair success. Retain the
frozen per-trial losses (§2.4): exclude `status_error` and mixed-model trials;
count losses; a contrast needs at least one usable repetition in each arm.
A successful S5 trial with the wrong model is a provenance failure. For the
McNemar dichotomy, restoration requires strictly more than half of that arm's
usable repetitions (a 1–1 tie scores 0; one usable repetition scores itself).
Never treat the repetitions as independent McNemar pairs.

For each paired defect, average usable restoration repetitions per arm, then
average the A1 − A2 differences over defects. Report its two-sided percentile
95% **defect-cluster** bootstrap CI (10,000 resamples, seed 20260803), plus
**two-sided exact McNemar**, α = 0.05, on the defect-majority discordances.
Report dropped defects and the observed repetition counts. **Replicated iff**
A1 − A2 > 0, that two-sided CI excludes 0, **and** McNemar p < 0.05; otherwise
report **not replicated** with the estimate and interval. Multi-attempt trials
remain included, with the same contrast reported after excluding them as a
sensitivity. There is no interim outcome-based stopping or extra confirmatory
test, and no modification to the core's RQ1 test.

*Exploratory reporting.* A1 − A2 repair; A1/A0 repair and restoration with
intervals (undefined denominators are reported, not assigned a number);
restoration A1 − A0 and A0 − A2; three-/four-way decomposition; results by
operator and review-count stratum; A3 regeneration and identity summaries.
The restoration-type, repair-type, both or neither reading and conditional
ceiling-based prediction are fixed in the pre-trial completion note. They
remain exploratory and cannot change the primary criterion. Model and bases
change together, so an observed difference cannot be attributed to either
alone.

*Initial analysis/provenance code, tested before collection.* These are the
preparation hashes; the final freeze records all relevant sources and bases.

| File (relative to `backend/`) | SHA256 |
|---|---|
| `scripts/analysis/repair_analysis.py` | `2ee0047911b5b200243308f0d8a619b06832744056db0cc0706469e4519484bf` |
| `scripts/analysis/power.py` | `195f41f867d20073c273757748e8b8c359fbe072cdfee6d4275fa27ad6aeee1c` |
| `scripts/flashlite_protocol.py` | `04e3562f1a38e1417aac4144439043cadefb1d6e3d3e613b122d76d7c85bedb6` |

The complete offline suite passed 640 tests (13 integration tests deselected)
on 2026-11-16; synthetic rows cover wrong-model/truncated bases, loss rules,
reverse-direction effects and full-A0 allocation. The 28-business dry run made
no model calls. After the initial A15/base-only release edit, the focused
gate/provenance suite passed **60 tests** (2026-11-16). The final protocol
release remains subject to its gates.

*Budget.* No cap (I7). Initial base estimate **3,863,781 tokens** = half of
H's measured 7,727,562 tokens for 56 businesses. This is a 2.5-Flash usage
proxy, not measured Flash-Lite cost. Before each live cell, sum actual usage
over all checkpoints and log that cell's exact numerical estimate in
`RUN_QUEUE.md`; log actuals after verification. Calibration and repair totals
are still unknown. The initial repair forecast is
`(9 * N_FL + 3 * Q_FL) * 14,000` tokens and must be replaced by a numerical
estimate once the plan exists. No token cap or obsolete 41 k/business
assumption is introduced.

**A15 preparation note — fixed determinism selection and collector
(2026-11-16, before any calibration call).**

The author launched own-base collection under committed/pushed `7ccda0d`.
No Flash-Lite determinism response or repair-trial outcome exists when this
rule is written. `flashlite_determinism` was registered in `cell.py` under
A15 / `gemini-3.5-flash-lite` before its collector was written. Live collection remains
blocked until the code, this rule and the numerical estimate are
committed/pushed. Use `cell.py` for its preflight, launch, status and verify.

- Render the real **A1@P1, C0** retry prompt for every runnable defect in the
  verified own-base plan, with injection seed 0. Call the production stage's
  stateless `build_prompt` and `arms.build_messages`; planning opens no HTTP
  client. There is no calibration subset based on repair outcomes.
- As in C7, use an operator round-robin. Sort each operator's candidates by
  decreasing **UTF-8 byte length of the canonical serialized message list**
  (JSON sorted keys, compact separators, Unicode preserved), then by defect ID
  ascending. Visit operators in ascending name order, taking the first
  remaining candidate with an unseen message SHA256. Continue until exactly
  **ten distinct real prompts** are chosen. Below ten, the plan fails rather
  than substituting another design. This uses byte length rather than C7's
  local-runtime token counter; the hosted provider has no such local counter.
- Send each chosen message list **twice**, contiguously within a prompt pair:
  **20 logical requests** in total. Pin both environment and agent primary /
  fallback names to `gemini-3.5-flash-lite`, fallback disabled, temperature 0,
  reasoning effort omitted (`None`). Disable SDK transport retries for this
  measurement (`max_retries=0`); do not issue schema-correction calls or
  postprocess the returned text.
- Preserve the manifest (base fingerprint, prompt IDs/hashes/lengths, source
  hashes, Python/OpenAI/httpx versions), raw text, requested/served model,
  session ID, status and token usage for every request. Compare the two raw
  texts, and separately their canonical JSON-object identities. Report the
  successful-pair and JSON-valid-pair denominators, errors and invalid JSON.
  Do not compare these responses with the clean output, score repair, or use
  them to choose hypotheses, arms, defects or the conditional prediction.
- Identity and JSON validity are **reported, not gated**; r = 3 regardless.
  A request error is retained and never automatically replaced. A wrong
  served model, changed prompt/base/runtime manifest, duplicate completion,
  a dry-run receipt or a pair split across sessions fails provenance. An
  interrupted request/pair is preserved for inspection rather than silently
  reissued. Each slot is durably marked started before it is sent, then its
  receipt is appended; started rows carry no tokens and the complete receipt
  contributes its usage once. The shared checkpoint's `trials` field contains
  measurement receipts only, never repair-trial observations.
- `cell.py verify flashlite_determinism` writes an identity-only
  `analysis.json`; a repeat verification reproduces it. The final A15
  completion note records this report, N_FL/power/MDE, the prospective
  dissociation reading and final hashes before `prereg-fl-freeze`. The repair
  cell remains closed until then. No new confirmatory test is added here.

**A15 planning completion — verified bases, N and power (2026-11-16;
before calibration or repair outcomes).**

Own bases completed under `7ccda0d`: **28/28 businesses**, all Phase-A observe,
seed 42, seven each at 14/34/92/214 reviews, `gemini-3.5-flash-lite` only,
zero fallback. `cell.py verify flashlite_bases` passed; the full provenance
validator passed (base SHA256 `ebb7147a9397d4a01685f12d8ad6228df1c22c4ec17f7ec54026acad64f90218`).
Actual usage: **2,603,688 tokens, 503 calls**, against the prospectively logged
3,863,781-token estimate. Three businesses carry a would-be retry. This is
base-incidence metadata, not an injected repair result.

The own-base plan gate (`cell.check_plan`) passes. Across six operators there
are **168 attempted defect slots**, **157 applicable**, **157 valid injections**,
**157 triggering** and **157 runnable**; the eleven inapplicable slots are
retained and counted. Validity is over applicable defects; triggering is over
valid injections. No operator gate or applicability rule changed.

| Operator | Attempted | Applicable / valid / triggering / runnable | Trials |
|---|---:|---:|---:|
| O1 | 28 | 26 / 26 / 26 / 26 | 252 |
| O2 | 28 | 26 / 26 / 26 / 26 | 252 |
| O3 | 28 | 25 / 25 / 25 / 25 | 243 |
| O5 | 28 | 26 / 26 / 26 / 26 | 252 |
| O6 | 28 | 27 / 27 / 27 / 27 | 261 |
| O7 | 28 | 27 / 27 / 27 / 27 | 261 |

Thus **N_FL = 157**, Q_FL = 36 quarter-stride A3 defects, and
**1,521 planned trials**: A0/A1/A2 471 each, A3 108. The original core plan
still prints **1,167**. Full denominators, allocation, base fingerprint and
prompt-selection manifest are in `out_study/FL/plan.json`.

`power.json` uses seed 20260803, r = 3, 2,000 simulations and 1,000 bootstrap
resamples per simulated dataset, defect SD 1 and shared-occasion SD 0. These
are planning assumptions. At historical marginal rates 0.68/0.53, joint power
is **0.977** (MC SE 0.00335); at 0.605/0.53 it is **0.4545** (MC SE 0.01113).
Under 0.53/0.53 the directional joint false-positive rate is 0.013 (MC SE
0.00253). The estimated **80%-joint-power MDE is 10.65 pp**, below the about
15 pp decision threshold, so the fixed original 28-business sample proceeds.
The final analysis still uses **10,000**, not 1,000, bootstrap resamples.
These are simulated power figures, not observed replication results.

*Prospective exploratory prediction and reading, fixed before calibration.*
Treat A0 as an empirical regeneration benchmark. Use the existing two-sided
95% defect-bootstrap CI for the **A1/A0 repair ratio** to condition the
prediction: if it contains 1 (no established separation from the benchmark),
predict a **restoration-type** pattern; if its upper endpoint is below 1
(A1 leaves measurable headroom below A0), predict **repair-type or both**.
If the ratio is undefined or its CI lies wholly above 1, the ceiling premise
has no support for this prediction; report that explicitly. A CI containing
1 does not establish equivalence or a ceiling. Report absolute arm rates and
all ratio intervals alongside this heuristic.

For the descriptive pattern label, a positive repair effect means the A1 − A2
repair CI has a lower endpoint above 0; a positive restoration effect means
the corresponding unconditional-restoration CI does. Label restoration-type,
repair-type, both or neither by those two indicators; report reverse effects
with their signed estimates. These labels are exploratory, add no confirmatory
test and never substitute for I5's three-part replication criterion. A failed
prediction is reported. No causal or double-dissociation claim follows from
the label, and no prediction is chosen from the calibration responses.

*Remaining collection and budget.* The fixed ten-prompt measurement has
20 requests, prospectively estimated at **520,402 tokens**. Rule:
`max(20*14000, ceil(1.25*sum(prompt_UTF8_bytes + own_clean_output_UTF8_bytes
across the 20 requests)/3))`. This is a byte-to-token heuristic and output-size
proxy, with a margin, not measured calibration usage or a spending cap.
The initial repair forecast is **21,294,000 tokens** = 1,521 × 14,000.
Actual spent total after bases is **84,499,571 tokens**. Log actual measurement
usage after verification and the numerical repair estimate before launch.

No calibration request or repair trial has run. The raw-response collector and
this completed selection/budget specification must be committed/pushed before
the measurement. Its working-tree release is for measurement only. The
repair cell stays preparation-only. Its final freeze gate now also requires
the tagged plan, power report, measurement checkpoint/manifest/analysis and
unchanged runtime/prompt sources. The final A15 freeze note and
`prereg-fl-freeze` remain pending the measurement; this note is not that tag.

**A15 pre-trial completion — ready for the freeze (2026-11-16).**

The original preparation protocol preceded all own-base collection
(`7ccda0d`). The author committed/pushed the bases, plan/power and prospective
measurement/prediction rule as `5f12198` before the first calibration request.
No main repair trial exists when this completion note is written; the
`out_study/T2FL/checkpoint.jsonl` file is absent.

*Determinism measurement, completed and verified.* Ten preselected real A1@P1,
C0 prompts, two requests each, **20/20 successful responses** exclusively from
`gemini-3.5-flash-lite`, temperature 0 and reasoning effort omitted. SDK
transport retries were disabled for this measurement. `cell.py verify
flashlite_determinism` passes: all prompt/base/runtime provenance agrees,
no pair spans sessions, no duplicate request completion and no invalid JSON.
**Raw identity is 8/10 pairs; canonical JSON identity is 8/10 pairs** (both
have ten valid-pair denominators). These compare the two responses to one
another, without scoring repair or restoration against clean references.
The measurement is descriptive; **r = 3 remains fixed** as specified before
these requests. There is no outcome-selected replacement or new test.

Actual calibration usage: **409,450 tokens**, versus the prospective estimate
520,402. The report is `out_study/FL/determinism/analysis.json`; raw responses
and receipts are retained in its checkpoint, with the fixed prompt/source
manifest. The stage-runtime package snapshot is `runtime.json` in that same
directory: Python **3.14.3**, OpenAI **2.41.0**, httpx **0.28.1**, and all
installed package versions. Primary repair runs retain the production SDK /
schema-retry handling, record every returned call and `attempts_made`, and
apply the already specified losses and sensitivity; the calibration's raw
single-call path does not redefine a repair trial.

*Frozen design.* The planning completion above is unchanged: original 28
businesses, all 2,478 sampled reviews retained, cap 500 and review seed 42;
all own bases from Flash-Lite only, no fallback. Base fingerprint
`ebb7147a9397d4a01685f12d8ad6228df1c22c4ec17f7ec54026acad64f90218`.
**N_FL=157**, **Q_FL=36**, **1,521 planned trials**: A0/A1/A2 at P1,
471 each; A3 at P0 on the fixed quarter stride, 108. C0, injection seed 0,
one session per defect, defect-outer execution, r=3; no new bases. Model and
both fallback names remain `gemini-3.5-flash-lite`, fallback disabled,
temperature 0, `reasoning_effort=None` (omitted, never the string `none`).
The documented power assumptions and estimated **10.65 pp** MDE stand.

The one primary outcome remains unconditional canonical-JSON exact
restoration to each model-owned clean output. Point estimate and the
10,000-resample, two-sided 95% defect-cluster percentile CI use paired
defect-level repetition means, seed 20260803. The two-sided **exact McNemar**
test at alpha 0.05 uses strict majority of usable repetitions per defect,
with the recorded loss/tie rules. Replicated iff A1−A2 > 0, its CI excludes 0
and exact McNemar p < 0.05; otherwise report not replicated with the estimate.
The single-call sensitivity and all secondary/conditional readings above
remain exploratory and unchanged from `5f12198`, before calibration. No
calibration response is used to choose that prediction or alter this design.

*Budget and release.* Exact total spent across checkpoints before the main
run is **84,909,021 tokens**. Main-run estimate remains **21,294,000 tokens**
(1,521 × 14,000; a planning proxy, no cap). The pre-launch cell gate logs this
estimate and the exact spent total; verified actual usage is logged afterward.
Core T2 (1,167) and T2T (1,224) remain unchanged.

Include this note, the measurement data/runtime snapshot and the `flashlite`
release flag in **one commit**, push it, then create/push the annotated
**`prereg-fl-freeze` tag on that commit** before the first main trial. The
working-tree release is still blocked by the missing tag and uncommitted
protocol. The gate requires tagged plan/power/measurement artifacts and
unchanged sources/bases, including the content matcher. Run only through
`cell.py` preflight/launch/status/verify. Final release validation is recorded
in `RUN_QUEUE.md` and the run ledger before the author's commit/tag.

*SHA256s at completion (paths relative to `backend/`).* The tag itself pins
this document; no self-referential document hash is embedded. The base
fingerprint above covers the full fixed sample and every base dump.

| File | SHA256 |
|---|---|
| `scripts/cell.py` | `6f0b9f47bb2ad875200bbb680406fbf0586b62597c363d4f13bf4845db175b36` |
| `scripts/run_injection_study.py` | `5f132144c6a2b180ff6724d55c3d103b34b77075ec37fe8d2fec354f1d5de58f` |
| `scripts/run_study.py` | `0a146d047297f1076428803969d36aaa1a8728fdad7c11b2370b2c61eac023d5` |
| `scripts/flashlite_protocol.py` | `04e3562f1a38e1417aac4144439043cadefb1d6e3d3e613b122d76d7c85bedb6` |
| `scripts/flashlite_determinism.py` | `4aa21a3ee0b6272c10a7c5362d39d3c3902c702c32350403c819e8a7aad894a0` |
| `scripts/analysis/repair_analysis.py` | `2ee0047911b5b200243308f0d8a619b06832744056db0cc0706469e4519484bf` |
| `scripts/analysis/power.py` | `195f41f867d20073c273757748e8b8c359fbe072cdfee6d4275fa27ad6aeee1c` |
| `scripts/analysis/score_repair.py` | `e8dab89ad29663089724f228a502d0e7c61c4122ceab320fbda4bfd71c101303` |
| `scripts/analysis/content_match.py` | `e6570a147701a406735aeb537b18270fb9d505f6fee3c9912a5dfe0c62927dcf` |
| `scripts/arms.py` | `41e2468d016f4e5d19050c987723a32de5c391187c06ced1861d36d54a8aef7f` |
| `scripts/inject_defects.py` | `52159f714a5849795a8ce613c0fd04ed531b5d735deab9748759b03a294e2213` |
| `app/agents/base_agent.py` | `d6bdfdc4ef2c95884dd021eff43953f94f3b3691412fb1951c7cd6d6ea073a19` |
| `app/agents/reasoning_agent.py` | `7ec3186aa22c230a32f90739d9752d96ef96fbb92bc5cc6ed3a02eaad97e9b39` |
| `app/agents/strategy_agent.py` | `1de73754c71f1b01d44d9456a1874eb8ae5c4d5192539f8e615fa4affa7852be` |
| `app/agents/report_agent.py` | `740070b35cf96e97f2abbf42b359af547833c241be8e5ef3eaa35fb5dfb031ab` |
| `app/core/nodes.py` | `dc7463e783295d3d7430f4ead6c66960533c8249529c3e13d7843de5a859d925` |
| `app/core/supervision.py` | `858f736ef6d8c13aa0869adc33cf086a1b4c24042f17b4122cd77e9f65027452` |
| `app/core/llm_config.py` | `c5a6593fa3cbf8dbe8aa410d65e066babf85f7ce95058b861e04d5f662ccc608` |
| `app/schemas/contracts.py` | `b63e651918ccdfe6cfa576a4e7d310abc0fa774c953f909260e1f258142205be` |
| `app/data/loader.py` | `8564c0c2d2d2f201a5fc3c0d31fd92d654421363ffaeedb87c95e9c8d4c0512b` |
| `out_study/sample.json` | `495787eac5b2df00ecf75dd48fb9d2c1f17424605013f7c0dd8f1833f5b85410` |
| `out_study/FL/A/checkpoint.jsonl` | `02f4b2adb30a1e0375875135eb7cb45e58ee18e8ec9a50324ce4b94b5eaad54c` |
| `out_study/FL/plan.json` | `7a20b5513ae45c16d869f7855ed6fda6184ddb17efd205165f481be118f8745f` |
| `out_study/FL/power.json` | `9e0ea8ecd5c4f4d1005736a65106ed66842f9c44916fefb10b9aa5e646d48c96` |
| `out_study/FL/determinism/checkpoint.jsonl` | `b468e79f5c926354b85ef90254c0793d855ade305e1809e7b8879f27172945f3` |
| `out_study/FL/determinism/manifest.json` | `bbf29f28cf9f2a73eda35ba5f3abc9043db3b24ace4b49b51aeca80fe1171e9d` |
| `out_study/FL/determinism/analysis.json` | `9b42975480bcc33a1de6f8aebe94790b0f4c5879b89e47473c2b9bc4ecd50099` |
| `out_study/FL/determinism/runtime.json` | `36e4cb2c38bf744bc84860f28682ecaebd2d9da3511289b46d3cb54b4b6cd2f2` |

*Final release validation (2026-11-16, before the commit/tag).* Focused
release/provenance suite: **74 passed**. The full cell-preflight test gate:
**655 passed, 13 integration tests deselected, 1 existing warning** (351.21 s).
Its own-model dry run passed **168/168 rows, 1,521/1,521 trials**, one session
per defect; the original core plan remains 1,167. Repeat measurement
verification reproduces its stored analysis. All hashes above and the frozen
checkpoint hashes were checked again. The full preflight remains held on the
missing tag, pending protocol commit and this session's SDK/proxy limitation;
launch from the normal terminal after the author's commit/tag/push. No main
trial has run.

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
| A3 | the original prompt again, nothing added — defined only at P0, where the injected output is absent | **regeneration baseline** (§11 item 6): what a fresh draw that never saw the defect scores. **Not a floor** for injected defects |

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

### 2.1 Confirmatory test — exactly one

**Exact McNemar, A1 vs A2** — feedback content — at α = 0.05, on the
dichotomised outcome (§2.3).

⚠ **The primary reported quantity is the estimate, not this test** (D4f):
A1 − A2 as a difference in rates with a 95% cluster-bootstrap CI over defect
blocks. The test is reported alongside it.

**Why one, when this section named three until 2026-09-14** (§11 item 6). The
other two were Cochran's Q, an omnibus over the matched arms, and McNemar A2 vs
A3, "the bare trigger". **Both rested on A3 being a near-zero floor, and for
injected defects it is not one.** A3 exists only at P0, where the injected
output never enters the context, so it regenerates a clean output and is
estimated to score ≈ 53% `repaired` (O6/O7 100% by construction) against the 5%
`power.py` assumed. A2 vs A3 would therefore come out reversed for a mechanical
reason, and an omnibus that spans A3 would reject for the same reason. Both move
to §3 item 9 as secondary, reinterpreted. With one confirmatory test there is no
multiplicity to correct — which also makes the test consistent with `power.py`:
every MDE in §6 was computed at an unadjusted α = 0.05, whereas a Holm-adjusted
A1-vs-A2 test would have faced a stricter threshold than its power assumed.

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
the C1 constraint-completeness cell (built 2026-09-20; §0.1 A1), the severity
sweep, per-operator rates, the collateral comparison, best-of-k curves, and the
D19 counterfactual (§7).

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

**The confirmatory test runs on the strict dichotomy `repaired` vs everything
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

**For O5, "the injected check still fires" is decided by a content-word trace,
not by the production matcher** (§11 item 5, D22). The production check
(`difflib` ≥ 0.35) flags 8 of 49 *correct* observe-mode strategy outputs, so
scoring O5 with it would score correct regenerations `unrepaired` at a
comparable rate in every arm. The scorer uses content-word Jaccard ≥ 0.10
against the same upstream candidates; the production verdict is logged beside it
and reported as a secondary, with containment > 0 and Jaccard ≥ 0.05 as
sensitivity. The threshold was fixed on pre-study calibration data, before any
trial outcome existed (`JOURNAL_PLAN.md` §17.2). **The production supervisor
itself is unchanged**: the O5 bases, the injected issue, the trigger and the A1
feedback were measured to be identical under both matchers.

**O5's identity anchor (`action`) is matched on content words too** — Jaccard ≥
0.20 (D24). In an unperturbed re-draw the production matcher failed to locate
70% of recommendations and so would score them `deleted`, an error tied to
placement: A3 re-draws at P0, while A1/A2 see the artifact at P1 and can copy
it. The threshold follows a rule stated before it was chosen — the lowest
false-deletion rate among matchers no more ambiguous within an output than the
production one. **Restoration (`issue`) stays on the production matcher:**
calibration found no matcher that separates a restored issue from a different
one better (`JOURNAL_PLAN.md` §17.5).

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
3. **A3 by stratum — descriptive** (§11 item 6): what a fresh draw scores, per
   operator, beside A1 and A2. Self-Edit's prediction that the A3 share of A1
   changes with defect difficulty was about self-generated errors and is not
   tested here.
4. Per-class repair rates, with the directional prediction recorded in §5.
5. Stratification by defect origin (replayed-real vs synthetic) and by stage.
6. The two-stage chain *did the output change at all → did the targeted defect
   resolve* (MAS-FIRE's O/L decomposition; global success S is out of scope).
7. Terminal supervisor verdict per trial. If A1 repairs more defects without
   shifting the run-level verdict distribution, **that is a finding** (the one
   MAST predicts), not a failure.
8. **O5 sensitivity (D24).** Recommendation issues are generic enough that no
   string matcher cleanly separates a restored issue from a different one — a
   different restaurant's recommendation "restores" 41% of the time under the
   scorer. So the primary A1 − A2 estimate is also reported **without O5**
   (N = 122), and O5's rate is also reported with `repaired` ∪ `replaced` as
   success. Both are reported whatever they show.
9. **A2 vs A3, and Cochran's Q across the arms — secondary since 2026-09-14**
   (§11 item 6). Reported with exact p-values and CIs and no correction, and read
   as *does re-presenting the defective output with a contentless rejection beat
   regenerating from scratch without it* — never as the effect of a bare
   trigger. Neither supports a headline claim.

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
| **A2** | **≈ 33%** — derived as 70% of A1's gain over a 5% floor. The number is kept because the primary MDE is computed at it; the floor it was derived from does not hold for A3 here (§11 item 6) | Self-Debug Simple rows, median 70% across seven model × benchmark settings |
| A3 | **not a floor:** ≈ 100% on O6/O7 by construction; ≈ 53% pooled over the N = 142 mix (an estimate that understates the reasoning operators) | `scripts/analysis/a3_redraw.py`, §11 item 6. The earlier "near zero" came from Self-Debug Table 3b and Huang's intrinsic rows — self-generated errors, which a re-draw reproduces |
| Class ordering | referential (O1/O2) > structural (O3, O6–O8) > semantic (O5) | — |
| Placement | **P1 ≫ P3 ≈ P2**; P0 reported separately, not folded into the ordering | Role Relabeling §4.3 |
| C1 interaction | **undetectable** — power 0.109–0.300 at N unreachable by a factor of three | D8c; reported as two gaps with CIs, never as a test |

~~**Pre-committed negative result.** If A1 ≈ A3 — feedback content adds nothing
over a bare re-draw — that is a publishable finding against the self-correction
literature's assumptions, and it is reported as the headline.~~

**Withdrawn 2026-09-14** (§11 item 6). For injected defects, A1 ≈ A3 would be the
expected consequence of A3 regenerating a clean output, not evidence against the
self-correction literature, so it cannot be a pre-committed headline. What still
makes a null informative is the estimate: A1 − A2 with its CI (§2, D4f).

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

O4 × {A1 at P1, A3 at P0 — the only placement A3 is defined at}, r = 3,
**23 applicable defects ≈ 138 trials** (measured
2026-09-02, `inject_defects.py --matrix`), about **+10% on top of the ≈1,420
core + C1**. Frequency divergence is resolved by recompute-and-overwrite in
production (§4.5) and never reaches a retry; this cell routes it to retry
deliberately, outside the production path, to measure what the overwrite bought.
**Not pooled into the primary contrast** — O4 carries `ENDPOINT["O4"] =
"warn_level"`, so it is excluded from `REPAIR_OPERATORS` in code and cannot leak
into N = 142 by accident.

**A3 in this cell is a regeneration baseline, not a floor** (§11 item 6). A fresh
draw never sees the injected frequency and was estimated to repair it ≈ 93% of
the time. So the counterfactual is read as **A1 against overwrite** — what
routing the divergence to measured-fact feedback costs next to an exact, zero-call
correction — and in both readings below, "retry" means A1. A3 is reported beside
it as what regeneration alone gives.

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
  collateral metric, the churn floors, the O4 path added for §7, and O5's
  content-word check and anchor (§2.3). Tested in `tests/test_score_repair.py`.
- `backend/scripts/analysis/content_match.py` — the tokeniser and the two
  calibrated thresholds, `TRACE_JACCARD = 0.10` and `ANCHOR_JACCARD = 0.20`.
- `backend/scripts/inject_defects.py` — operators and `verify_injection`.
- `backend/scripts/run_injection_study.py` — iteration order, **the D20 gates in
  `build_plan`**, the two denominators in `plan_summary`, checkpointing, the
  exclusions. **28 tests**, plus 12 added 2026-09-20 for the C1 cell (§0.1 A1),
  which is off unless `--c1` is passed.
- `backend/scripts/analysis/power.py` — the MDEs quoted above.
- `backend/scripts/arms.py` — `AUTHORED_WORDING`, frozen 2026-08-25; extended 2026-09-20 by §0.1 A1 with `C1_PREAMBLE` and `C1_CONSTRAINTS` (the C1 cell's wording, which D8 requires be published verbatim).

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
- **The supervisor is not always right** (§15.4; measured 2026-09-14, §17 of
  the plan). `untraceable_recommendation` compares characters, not content.
  Every one of the 13 production issues it flagged shares content words with
  upstream — 8 of 49 observe-mode strategy outputs, false alarms under every
  content matcher that raises no new flags — and it calls injected alien content
  traceable in 6 of 168 issue × base pairs. ⚠ **This file previously said the
  study "does not depend on the checker's production precision". That was wrong
  for O5:** the bug does not reach O5's manipulation, but it does reach its
  scoring, which is why §2.3 corrects the scorer. The study keeps the production
  supervisor as shipped — it is the system paper #1 describes — and the paper
  states the finding rather than letting a reviewer find it.

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
| Q1 measured and decided (D22); Q2 decided — journal-paper finding (D23) | 2026-09-14 |
| §11 item 5 built — O5 trace (D22) and anchor (D24) on content words | 2026-09-14 |
| §11 items 1, 2, 4 confirmed by the author (pool · D19 after the core · majority) | 2026-09-14 |
| §11 item 6 opened — A3 at P0 re-draws a clean output | 2026-09-14 |
| §11 item 6 decided — A3 re-roled as a regeneration baseline; confirmatory set reduced to A1 vs A2 | 2026-09-14 |
| **This document frozen — annotated tag `prereg-freeze`** | **2026-09-14** |
| Live 7-cell smoke test passed, 7/7 | 2026-09-14 |
| §0.1 A1 — C1 prompt written and wired | 2026-09-20 |
| **First core trial** | **2026-10-05** |
| Interim budget look after 12 defects (§0.1 A4) | 2026-10-05 |
| **Core complete — 1,167 trials, 1,149 usable, 18 `status_error`** | **2026-10-07** |
| Confirmatory analysis code written and run (§0.1 A4) | 2026-10-07 |
| §0.1 A2 and A3 — D19 and C1 passes wired, committed and pushed (`4d03268`) before either ran | 2026-10-07 |
| **D19 pass complete — 138 trials, all usable** | **2026-10-07** |
| **C1 pass complete — 444 trials, all usable** | **2026-10-07** |
| §0.1 A5 and A6 — placement pass and O1 severity sweep defined and wired, committed and pushed before either ran | 2026-10-07 |
| **Placement pass complete — 540 trials, 539 usable** | **2026-10-07** |
| **Severity sweep complete — 144 trials, all usable** | **2026-10-08** |
| §0.1 A7 — warm-resample cell wired, committed and pushed before it ran | 2026-10-07 |
| **Warm-resample cell complete — 675 trials, all usable** | **2026-10-08** |
| §0.1 A8 — Tier-1 replay wired, committed and pushed before it ran | 2026-10-08 |
| **Tier-1 replay complete — 117 trials, all usable** | **2026-10-08** |
| §0.1 A9 — downstream propagation wired (endpoint (b), author's choice), committed and pushed before it ran | 2026-10-08 |
| **Downstream propagation complete — 447 conditions, all usable** | **2026-10-08** |
| §0.1 A10 and A11 — C7 local replication defined, wired and calibrated | 2026-10-12 |
| **C7 local replication complete — 930 trials, 929 usable** | **2026-10-12** |
| §0.1 A12 — Thinking-budget sweep on Gemini 2.5 Flash defined and wired | 2026-11-01 |

---

## 11. The items that blocked the freeze — all six closed

Items 1–4 closed **2026-09-08**; items 5 and 6 closed **2026-09-14**. Three were decisions and are recorded in the
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
| 5 | **From Q1 (2026-09-14):** does the trace-matcher bug reach the study? | **Not the manipulation; yes the measurement.** Built: O5's check on content-word Jaccard ≥ 0.10 (D22), O5's `action` anchor on Jaccard ≥ 0.20 (D24); restoration kept on the production matcher, which calibrated best. O5 sensitivity analyses pre-registered. | §2.3, §3 item 8, plan §17.2–17.5 |
| 6 | **From item 5 (2026-09-14):** is A3 a floor for *injected* defects? | **No — measured; A3 re-roled (author, 2026-09-14).** A3 exists only at P0, where the injected output never enters the context (D10), so it regenerates a clean output: ≈ 53% `repaired` estimated, O6/O7 100% by construction, against the 5% `power.py` assumed. A3 is now a regeneration baseline. The confirmatory set is the single A1-vs-A2 test; A2 vs A3 and Cochran's Q move to secondary; the §5 A3 prediction is corrected and the pre-committed negative result withdrawn; D19 reads A1 against overwrite. **Rejected:** an added artifact-shown, no-rejection arm (new frozen wording, no literature behind its power assumption), and freezing as is. | §2, §2.1, §3 items 3 and 9, §5, §7, plan §17.6–17.7 |

**Items 1, 2 and 4 were confirmed by the author on 2026-09-14**, as recorded
above: pool the contrast; D19 in scope, run after the core; majority.

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
freeze tag** and thereafter only as a dated §0 amendment. **Q1 and Q2 were answered by the author on
2026-09-14** (`JOURNAL_PLAN.md` §17). Q2: paper #1 stands as submitted and the
matcher defect is a journal-paper finding. Q1 was measured before it was
decided, and **the measurement overturned the premise this paragraph was written
on** — that Q1 does not touch the analysis. It does: the production matcher does
not reach the study's manipulation, but it does reach O5's measurement. That is
item 5.

**What the closing changed in the numbers: nothing.** That was not the expected
outcome and it is worth stating plainly. The D20 gates were wired expecting them
to remove defects and eat into a 1.1 pp margin. They removed none — injection
success 142/142, trigger 142/142, stable across seeds 0, 1, 42 and 20260803.
The gates are therefore a **standing guarantee rather than a filter on this
bank**: they will catch a future operator, base or supervisor change that breaks
the assumption, and they convert an assumption the design was resting on into a
measured number. They are reported as exactly that, and never as a validation
step that "passed" in a way implying it discriminated.
