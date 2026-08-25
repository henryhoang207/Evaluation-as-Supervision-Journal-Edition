# START HERE — next session

**Rewritten:** 2026-08-24. Supersedes the 2026-08-04 version, which described
production of the conference paper. **That paper is finished.** The active work
is now the journal extension.

Where this file disagrees with `JOURNAL_PLAN.md`, **`JOURNAL_PLAN.md` wins** —
it is the authoritative plan. This file is the map.

---

## 1. Status

**Branch `journal/build-b1-b3-and-plan-corrections`, not merged to main.**
134 tests pass, working tree clean.

| Track | State |
|---|---|
| Conference paper #1 | **Submitted, under review.** `main.tex` + `references.bib` recovered and tracked; structurally verified. Nothing to do but wait — except one cheap, time-sensitive item: email the chairs about an extended-version route *while* it is in review. |
| Journal / repair study | **Instrumented and analysed. No trial has run.** Not one LLM call has been made toward this study. |

**Build: 4 of 8 items done.** B1 (token accounting), B1b (served-model
provenance), B2 (fallback control), B3 (replay entry point) — plus the
defect-bank inventory, and two analyses that were not in the plan but turned
out to be prerequisites (power, churn). **B4–B8 are not started.**

**Gates currently green** — re-run both before trusting anything below:

```bash
venv/Scripts/python.exe scripts/replay_stage.py --verify out_study
```

135 recorded facts reproduced exactly, 0 mismatches, no dataset needed.

**Three findings that changed the design**, all reproducible from committed
scripts (§8):

1. **The Tier-1 defect bank is 11, not 15**, over **two stages**, in 5 clusters.
   Three entries are API 503s; the only report-stage entry is a cascade of one
   of them. MDE ≈ 31 pp and the cluster bootstrap over-rejects, so **Tier 1
   cannot support inference at all** — realism anchor only.
2. **The Tier-2 core must run at placement P1** (D10), not the production
   placement, or the injected defect never enters the model's context.
3. **The grid as specified has 0.30 power** for the effect the literature
   predicts (D4d). Fixing it needs both primary arms at all 160 defects with
   r=3 — and **160 is a hard ceiling**, set by the 20 Phase-A dumps.

Plus one that kills a planned cell: **the D8 constraint-completeness
interaction is undetectable at any affordable size** (0.19 power at 160/160
defects). It is now an estimate, not a test (D8c).

**Next action: the Phase-0 memo.** It does not exist. §3 of the plan is now
restructured and ready to be turned into one; four decisions in it are open
questions for the supervisor (§4 below).

---

## 2. Read in this order

1. **`JOURNAL_PLAN.md` §3 first** — the decision table, restructured 2026-08-24
   from chronological into functional order (D1–D17 in six groups). **⛔ marks
   the seven blockers; ❓ marks the four open questions.** Read that, and you
   have the design.

   Then the rest of the plan (~1,050 lines). It grew by accretion: **§13 and
   §14 amend earlier sections**, so where §5/§6 and §13/§14 disagree, the later
   section wins. **Exception:** the 2026-08-24 passes (banners at the top of the
   file) **edited §3/§4/§5/§6/§8 in place** — those are current, not superseded,
   and they are the parts checked against the repository and against
   simulation rather than against the literature.
2. **`PUBLICATION_STRATEGY.md`** — how many papers this becomes, what is left
   for the journal if the repair study splits off, whether either claim is
   significant enough, and the constraints that follow from #1 being in review.
   Short, and it decides things §12 of the plan could not.
3. This file, for traps and do-not-redo items.

⚠ **`READING_PROMPTS.md` no longer exists** — it is in neither copy of the repo
and was never committed. The Tier-A/Tier-B extraction prompts are lost; the
extractions themselves survive at `..\Reading List\` (§3). Rebuild the prompts
from those extractions if Tier C needs them.

Do **not** re-explore the repository first. Do **not** re-read the papers —
the extractions already exist (§3).

---

## 3. Where everything lives — including outside the repo

| What | Path | On GitHub? |
|---|---|---|
| Journal plan | `docs/paper/JOURNAL_PLAN.md` | **Yes** (tracked 2026-08-24) |
| Publication strategy (split decision, venues) | `docs/paper/PUBLICATION_STRATEGY.md` | **Yes** |
| Conference paper source | `docs/paper/main.tex`, `references.bib` | **Yes** (rescued 2026-08-24) |
| **Tier A extraction (5 papers)** | `..\Reading List\Tier_A\Tier_A_extraction.md` | **No — outside the repo** |
| **Tier B extractions (9 papers)** | `..\Reading List\Tier_B\related_work_tierB_triad.md` and `related_work_B-III.md` | **No — outside the repo** |
| Paper PDFs | `..\Reading List\Tier_A\` and `Tier_B\` | No |
| Study dumps (251 stage JSONs) | `backend/out_study/*/*/` | **Yes** |
| Study checkpoints (`observations[]`) | `backend/out_study/**/checkpoint.jsonl` | **Yes** (was ignored until 2026-08-24) |
| Defect bank (generated) | `backend/out_study/defect_bank.json` | Yes |
| Supervision layer | `backend/app/core/supervision.py` | Yes |
| Reading prompts | *gone* — see §2 | — |

⚠ **The "gitignored on purpose" note that used to sit here was wrong and has
been removed.** `docs/paper/` has been tracked since the journal-edition switch,
and `git status` is clean because the work is *committed*, not because it is
ignored. The remote is
`https://github.com/Hahhahahaadsa/Evaluation-as-Supervision-Journal-Edition.git`.

⚠ **Two physical repo directories exist.** `Tài liệu` appears on disk in two
Unicode normalisations (NFD and NFC) and they render identically in every
listing. The **NFD** one holds the git repo, `Reading List/`, `venv/` and the
dataset. The **NFC** one is a stray shadow with no `.git`; until 2026-08-24 it
held the only copy of the conference paper source. If a file you are certain you
wrote is missing, look there before rewriting it. It should be deleted once
confirmed empty of anything unique.

⚠ **Data-loss inversion, now fixed.** `.gitignore`'s blanket `*.jsonl` rule
meant the repository tracked the `.bak` files recording *failed* runs while
ignoring every `checkpoint.jsonl` — the `observations[]` behind every paper
number and the entire defect bank, ~143 KB, on one disk only. A negation rule
(`!backend/out_study/**/*.jsonl`) now tracks them.

---

## 4. Journal extension — the design

Goal: measure whether feedback-injected retry **repairs** a detected defect —
the quantity the conference paper honestly could not measure. ⚠ Say **"repair by
regeneration"**: the retried stage regenerates its whole output rather than
editing the faulty artifact (D17).

- **Two tiers.** Tier 1 replays real defects captured on disk (**11 usable,
  2 stages, descriptive only**); Tier 2 applies synthetic operators to clean
  outputs and **carries every rate and the stage comparison**.
- **Four arms.** A0 capability ceiling · A1 measured-fact feedback (production
  path) · A2 generic rejection · A3 bare re-draw (a determinism floor at
  temperature 0, not resampling).
- **Placement — four levels (D9).** **P0** artifact absent (production;
  Tier-1 default) · **P1** user-turn artifact (**Tier-2 default, D10**) ·
  **P2** assistant-turn · **P3** exploratory. ⚠ **Not fully crossed** — A0 × P0
  and A3 × P1 are structurally undefined (D9b).
- **Analysis.** Three confirmatory tests under Holm; Cochran's Q on the
  **dichotomised** outcome (it is a binary test); A1/A0 ratio by **cluster
  bootstrap**, not delta method; outcome is a **3-class multinomial crossed with
  a binary collateral flag** (the original four classes were not mutually
  exclusive). **Pre-register as estimation, not NHST** (D4f).
- **Venue.** EMSE regular track for the journal; ASE and the ESEM registered
  report are live conference options. All deadlines cited are **unverified**.

### Next actions, in order

1. ⛔ **Resolve D12 — it blocks B7, and B7 blocks every trial.** If downstream
   propagation is in scope (`PUBLICATION_STRATEGY.md` §5 argues it must be, or
   the journal has no thesis left after a split), the runner must persist the
   full retried output **plus enough state to re-run downstream stages later**.
   Nearly free on the first pass; a full ~1,400-trial re-run to recover.
2. **Write the Phase-0 memo** from `JOURNAL_PLAN` §3 and get sign-off on
   **D1–D17**. Seven are ⛔ blockers. **Four are genuinely open and are what the
   memo must ask:**
   - **D8b** — does the C1 cell regenerate its base output, or inject into a C0
     base and vary only the retry prompt? (Recommendation: the latter.)
   - **D5b** — which local model, quantisation and seed? Currently a placeholder,
     and C7's reproducibility claim depends on it.
   - **D11b** — the split threshold X. (Proposed: ≥ 12 pp *and* CI excludes 0 —
     it falls out of the power analysis rather than being chosen after the fact.)
   - **D13** — who is the second rater for the defect-bank audit? An LLM cannot
     be: it wrote the classifier that defines the bank. Recommended split —
     verify *groundedness* programmatically, have the supervisor rate
     *meaningfulness* over a much smaller set.
3. Build **B4–B8** with their golden gates: the §13.5 replacement-value scorer
   test, and the collateral metric rebuilt on the D3c per-item-class thresholds.
4. Run the core: A0/A1/A2/A3 at **P1** across three stages, **plus C1**, **plus
   the warm-resample subset**, at **r=3** if 0.80 power is the target.
   Tier 1 (132 trials at P0) is the realism anchor and gets **no hypothesis
   test**. Budget is now ~1,320–1,460 trials, up from ~980 — ⚠ **check the API
   budget first**: `out_study/B/checkpoint.credit-depleted.jsonl.bak` records a
   cost ceiling being hit once already.
5. **Then** branch on the result (D11/D11b).

Two things to chase in parallel, both cheap and both time-sensitive:
**the ESEM registered-report cycle dates** (they outrank the whole venue table
and would change §10 — and a registered report is the only format that rewards
this project's strongest asset, its design work, *before* results exist), and
**an email to the #1 chairs about an extended-version route** — worth doing
while #1 is in review, not after.

---

## 5. Blocking issue: D8 (read before building anything)

The A1 feedback **discloses constraints the stage prompts never state**.
Verified 2026-08-24 against the code: `supervision.py`'s retry strings assert
that evidence IDs must resolve, aspects must align, recommendations must trace
upstream, and the report must only restate upstream — **none of which appears in
`reasoning_agent.py`, `strategy_agent.py`, or `report_agent.py`'s system
prompts.**

So an A1 > A2 result would be partly prompt-completeness, not feedback
specificity. Two independent sources say this invalidates the contrast: Huang et
al. (ICLR 2024) §5, and Kamoi et al. (TACL 2024) Table 7's Required row.

**Recommended fix (D8b):** add a constraint-completeness factor — C0 production
prompt, C1 prompt stating all supervisor obligations — crossed with A1/A2 on a
Tier-2 subset (~160 calls, already in the §6 budget). Pre-specify the C1 text and
publish it verbatim. Full options in §13.2.

---

## 6. Do not redo / do not reintroduce

**From the conference paper (still binding):**

1. **Derivability is closure, not linearity.** The report stage reads analysis,
   reasoning *and* strategy.
2. **Restaurant distribution ≠ all-business.** Restaurants only (n=52,268):
   p10=7, p25=14, p50=34, p75=92, p90=214. **Never quote 6/8/15/38/101.**
3. **21 failure modes, not 22** (23 tests; 2 are routing utilities).
4. **Latency overhead is not +0.2%** — that compared single runs and sits inside
   the noise floor.
5. **"Defects don't recur" was wrong** — it conflated "no retry fired" with "no
   defect occurred".
6. **`gemini-2.5-pro` 404s** ("no longer available to new users"). The judge used
   `gemini-3.1-pro-preview`.
7. **Do not delete the quarantined files.** They record failures deliberately:
   `out_study/B/checkpoint.credit-depleted.jsonl.bak` and
   `out_study/judge/results.contaminated.jsonl.bak`.

**New, from the 2026-08-24 literature pass:**

8. **Citation metadata was wrong three times** — always verify venue and status
   in the PDF, never from a web-search snippet. Corrected: Self-Correction Bench
   is **COLM 2026** (not NeurIPS 2025); AgentChaos is **ASE 2026, peer-reviewed**
   (not a preprint); the "Self-Correction Illusion" file is really *Role
   Relabeling Gates Explicit Error Flagging in LLMs* (arXiv 2606.05976v2).
9. **Do not cite MAS-FIRE's ">40%" abstract figure** — no derivation was found in
   its results.
10. **Do not quote any MAST category percentage** until the denominator is
    established — three mutually inconsistent sets appear in that paper.
11. **The Tier-1 defect bank is 11 usable defects over two stages** — reasoning
    5, strategy 6, **report 0, analysis 0** — in **5 business × stage cells
    across 4 businesses**. There are 15 retry-triggering observations, but
    **three are Gemini 503 `status_error` retries** and the **only**
    report-stage entry is a cascade of one of them (its upstream reasoning stage
    503'd, strategy emitted nothing, and the report agent invented content to
    fill the gap — a different estimand, reported separately). Earlier counts of
    "15" and "12" were both wrong. Regenerate with
    `python scripts/analysis/defect_bank.py`; `tests/test_replay.py` pins the
    numbers so a stale plan fails the suite.
12. **Runner iteration order must be `for defect: for arm: for repetition:`** —
    never arm-outer, or arm gets confounded with serving epoch (§14.1).

**New, from the 2026-08-24 code-review, power and self-review passes:**

13. **Do not re-derive the defect bank by hand.** `scripts/analysis/defect_bank.py`
    encodes every exclusion rule and `tests/test_replay.py` pins its numbers, so
    a stale plan fails the suite. Same for the replay gate.
14. **Closed-form power formulas do not apply here** — arms are matched within
    defect, reps nest inside (defect, arm), Tier-1 defects cluster. Use
    `scripts/analysis/power.py`. And remember the **shared-occasion effect**:
    §14.1 forces all arms for one defect into one session, which raises
    arm-to-arm correlation and *costs* power. Ignoring it overstates everything.
15. **160 defects is a hard ceiling** (8 operators × 20 Phase-A dumps). Once the
    sample is exhausted, **r is the only lever** — and reps and blocks buy power
    about equally here, contrary to the usual advice.
16. **Never measure a "baseline" on data from a different serving epoch.** The
    old no-injection control used the recorded Phase-A verdict from weeks
    earlier — confounded by exactly the drift §14.1 exists to prevent (D5c).
17. **Measure churn under the condition the experiment will actually face.** The
    first collateral estimate (37% at the strategy stage) was confounded:
    repetition runs regenerate every stage, but a replay trial pins upstream
    from the dump. Conditioning on stable upstream gives 23%.
18. **The analysis scripts do not share a working directory.** `tally.py`,
    `rep_tally.py`, `rep_verdict.py`, `audit.py`, `check_tex.py` run from the
    **repo root**; `defect_bank.py`, `churn.py`, `power.py`, `replay_stage.py`
    run from **`backend/`**. §8 has the exact commands.
19. **Verify venue deadlines against official CFPs.** Every date in
    `PUBLICATION_STRATEGY.md` §8 arrived second-hand and is unverified — in a
    project whose own §14.9 records citation metadata being wrong three times
    from precisely that sourcing.

---

## 7. Environment traps (all verified this session)

- **The repo path contains `Tài liệu` in two Unicode normalisations.** Absolute
  paths typed with precomposed characters silently miss. **Use the 8.3 short
  path for Read/Write/Edit:**
  `C:\Users\hoanh\OneDrive\TAILIU~1\CSMATE~1\COS30018\Project\COS300~1.1_M\...`
  Bash with paths relative to the repo root also works.
- **Long bash heredocs fail on apostrophes.** A short one survives; a
  several-hundred-line markdown body does not (`unexpected EOF while looking for
  matching '`). Use the `Write` tool for prose, or a `python - <<'PYEOF'`
  heredoc, which is reliable.
- **The Bash working directory persists** between calls and does *not* always
  reset to the repo root — a bare `cd docs/paper` failed because the shell was
  already there. Prefer `cd "$(git rev-parse --show-toplevel)"` at the start of
  each call.
- Long runs go in the background; every runner checkpoints and resumes.
- Transient Gemini 503s are common at volume; `--sleep 5` helps.

---

## 8. Reproduce any conference number

All read-only, no API cost. ⚠ **The scripts do not share a working directory** —
verified 2026-08-24, and an earlier version of this section was wrong about it.
`tally.py`, `rep_tally.py`, `rep_verdict.py`, `audit.py` and `check_tex.py`
hard-code repo-root-relative paths (`backend/out_study/…`, `docs/paper/…`) and
**must run from the repo root**. The journal-extension scripts take
`--root`/`--dump-dir` arguments and run from `backend/`.

From the **repo root**:

```bash
backend/venv/Scripts/python.exe backend/scripts/analysis/tally.py
```

Also `rep_verdict.py` (recurrence), `audit.py` (latency, input identity,
stability), `check_tex.py` (braces, refs, citations, placeholders) — same cwd.

From **`backend/`**, for the journal extension — read-only and dataset-free:

```bash
venv/Scripts/python.exe scripts/analysis/defect_bank.py --out out_study/defect_bank.json
```

```bash
venv/Scripts/python.exe scripts/replay_stage.py --verify out_study
```

```bash
venv/Scripts/python.exe scripts/analysis/power.py
```

```bash
venv/Scripts/python.exe scripts/analysis/churn.py
```

`power.py` answers D4d (simulation-based; closed-form McNemar does not apply).
`churn.py` answers D3c by measuring the unperturbed pipeline's own churn from
the repetition sub-study — the floor a collateral threshold has to clear.

Inspect one banked defect with
`scripts/replay_stage.py --dump-dir <dump> --stage <stage>`.

Re-running an *experiment* needs `MAX_REVIEW_SAMPLE=214` in the environment —
`loader.MAX_REVIEWS` is read at import, so `--sample-size` alone cannot lift the
cap and the runner refuses to start without it. That guard is deliberate.

---

## 9. Verification state at this handoff

- Tier A: 5/5 read · Tier B: 9/9 read · **Tier C: 0/11, still outstanding**
- Defect bank: **re-verified and encoded in code** — 11 usable, 1 cascade,
  3 API errors, from 15 retry observations (`scripts/analysis/defect_bank.py`)
- Replay fidelity gate: **PASS** — 135 recorded facts reproduced exactly,
  0 mismatches, 45 analysis-stage observations skipped as unverifiable
- Test suite: **134 pass**, 6 integration deselected
- Defect bank **cross-validates exactly against the pre-existing `tally.py`** on
  Phase A (0 unresolvable evidence IDs, 1 misaligned aspect, 3 untraceable
  recommendations) — two independently written implementations, same answer.
  `tally.py` had already excluded `status_error`, so the repository's own
  analysis code encoded the 503 exclusion all along; only the plan's prose was
  wrong. **Cross-validate against existing scripts before building a new one.**
- Power analysis (D4d) and collateral calibration (D3c) are **computed and
  committed** — `scripts/analysis/power.py`, `scripts/analysis/churn.py`. Both
  read-only, both dataset-free.
- `total_tokens` is null in all 45 runs, but **B1 was never a real gap** —
  `BaseAgent.total_tokens_used` and `eval/harness.py` already did this;
  `run_study.py` simply hard-coded `total_tokens=None`. Now fixed, so any token
  figure must come from a **fresh** run — the 45 on disk cannot be back-filled.
- Conference paper #1: **submitted, under review.** `main.tex` verified
  structurally sound
  (`check_tex.py`: braces balanced, 0 placeholders, 0 dangling refs, 0 missing
  citations). It was recovered from the NFC shadow directory on 2026-08-24 and
  is now tracked. `check_tex.py` itself had a false-positive brace bug — fixed.
- **Not verified:** no trial has run, no operator exists, no scorer exists, no
  memo is written. B4–B8 are unbuilt.

## 10. Known documentation drift (pre-existing, unfixed)

`README.md` §6/§9 still describe the *old* failure-only orchestrator
("retry, skip, or halt decisions after stage failure") and list Tier 1 as not
enforced at runtime. The hub supervisor superseded that. The code and
`docs/FINDINGS_2026-07-16.md` F7 are correct; the README is stale. Not fixed
here because it is outside the journal work — but do not trust README §6/§9.
