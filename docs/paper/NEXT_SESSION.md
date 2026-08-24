# START HERE — next session

**Rewritten:** 2026-08-24. Supersedes the 2026-08-04 version, which described
production of the conference paper. **That paper is finished.** The active work
is now the journal extension.

Where this file disagrees with `JOURNAL_PLAN.md`, **`JOURNAL_PLAN.md` wins** —
it is the authoritative plan. This file is the map.

---

## 1. One-line status

Conference paper: **done**. Journal extension: **planned, fully read, not
started**. All 14 Tier-A + Tier-B papers are read and folded into the plan; the
design is frozen; **no code is written and the Phase-0 supervisor memo does not
exist yet.** That memo is the next action.

---

## 2. Read in this order

1. **`JOURNAL_PLAN.md`** — the plan (~790 lines). Note it grew by accretion:
   **§13 and §14 amend earlier sections**, so where §3/§5/§6 and §13/§14
   disagree, the later section wins. A consolidation pass is overdue.
2. `READING_PROMPTS.md` — the prompts used to extract the literature, Part I
   (Tier A, complete) and Part II (Tier B, complete). Reusable for Tier C.
3. This file, for traps and do-not-redo items.

Do **not** re-explore the repository first. Do **not** re-read the papers —
the extractions already exist (§3).

---

## 3. Where everything lives — including outside the repo

| What | Path | On GitHub? |
|---|---|---|
| Journal plan | `docs/paper/JOURNAL_PLAN.md` | **No** |
| Reading prompts | `docs/paper/READING_PROMPTS.md` | **No** |
| Conference paper source | `docs/paper/main.tex` (+ `main-submission-preview.pdf`) | **No** |
| **Tier A extraction (5 papers)** | `..\Reading List\Tier_A\Tier_A_extraction.md` | **No — outside the repo** |
| **Tier B extractions (9 papers)** | `..\Reading List\Tier_B\related_work_tierB_triad.md` and `related_work_B-III.md` | **No — outside the repo** |
| Paper PDFs | `..\Reading List\Tier_A\` and `Tier_B\` | No |
| Study data (Phase A/B, repetition, judge) | `backend/out_study/` | No (gitignored) |
| Supervision layer | `backend/app/core/supervision.py` | Yes |

⚠ **`docs/paper/` is gitignored on purpose.** `git status` is clean even after
heavy editing because every planning file is local-only. A session that clones
`https://github.com/Hahhahahaadsa/Evaluation-as-Supervision.git` gets the code
and none of the paper work. If you need this on another machine, copy
`docs/paper/` and `..\Reading List\` by hand.

---

## 4. Journal extension — the frozen design

Goal: measure whether feedback-injected retry **repairs** a detected defect —
the quantity the conference paper honestly could not measure.

- **Two tiers.** Tier 1 replays real defects captured on disk; Tier 2 applies
  8 synthetic operators (one per supervisor check class) to clean outputs.
- **Four arms.** A0 capability ceiling · A1 measured-fact feedback (production
  path) · A2 generic rejection · A3 bare re-draw.
- **Placement factor.** P1 user-turn artifact · P2 assistant-turn · P3
  (exploratory) P2 + correction marker.
- **Analysis.** Matched per defect: Cochran's Q omnibus, exact McNemar for
  A1-vs-A2 and A2-vs-A3, A1/A0 ratio with delta-method CI, block on defect
  identity, multinomial over four outcome classes, stratify by origin and stage.
- **Venue.** EMSE regular track (§12). ASE is a live alternative — AgentChaos
  (ASE 2026) proves the SE community takes agent-fault-injection work.

### Next actions, in order

1. **Write the Phase-0 memo** and get supervisor sign-off on **D1–D8**. D8 is
   new and **blocks every trial** — see §5 below.
2. Build B1–B8 with the golden gates (replay fidelity; the §13.5
   replacement-value scorer test).
3. Tier 1 (~180 trials) → go/no-go → Tier 2 (~980 calls, ~3 nights).

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
11. **The Tier-1 defect bank is 15 stage-level instances: 6 Phase A + 9
    repetition** (verified against the dumps; an earlier "7+8" was wrong). All 15
    fall on the same 5 businesses; stage coverage is reasoning 7, strategy 6,
    **report 2, analysis 0**.
12. **Runner iteration order must be `for defect: for arm: for repetition:`** —
    never arm-outer, or arm gets confounded with serving epoch (§14.1).

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

From `backend/`, venv active. Read-only, no API cost.

```bash
venv/Scripts/python.exe scripts/analysis/tally.py
```

Also: `rep_verdict.py` (recurrence), `audit.py` (latency, input identity,
stability), `check_tex.py` (braces, refs, citations, placeholders).

Re-running an *experiment* needs `MAX_REVIEW_SAMPLE=214` in the environment —
`loader.MAX_REVIEWS` is read at import, so `--sample-size` alone cannot lift the
cap and the runner refuses to start without it. That guard is deliberate.

---

## 9. Verification state at this handoff

- Tier A: 5/5 read · Tier B: 9/9 read · **Tier C: 0/11, still outstanding**
- Defect bank: **verified against the dumps** (15 instances, 5 businesses)
- `total_tokens` is **null in all 45 runs** — build item B1 is a real gap
- Conference paper: finished; `main.tex` is its source of truth
- **Not verified:** nothing in the journal plan has been executed. No trial has
  run, no operator exists, no memo is written.

## 10. Known documentation drift (pre-existing, unfixed)

`README.md` §6/§9 still describe the *old* failure-only orchestrator
("retry, skip, or halt decisions after stage failure") and list Tier 1 as not
enforced at runtime. The hub supervisor superseded that. The code and
`docs/FINDINGS_2026-07-16.md` F7 are correct; the README is stale. Not fixed
here because it is outside the journal work — but do not trust README §6/§9.
