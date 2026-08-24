# START HERE — next session

**Rewritten:** 2026-08-24. Supersedes the 2026-08-04 version, which described
production of the conference paper. **That paper is finished.** The active work
is now the journal extension.

Where this file disagrees with `JOURNAL_PLAN.md`, **`JOURNAL_PLAN.md` wins** —
it is the authoritative plan. This file is the map.

---

## 1. One-line status

Conference paper #1: **submitted, under review** (confirmed 2026-08-24) — so
the dual-submission and 30%-rule constraints in `PUBLICATION_STRATEGY.md` §6 are
now live. Journal extension: **planned, fully read, build started**. All 14
Tier-A + Tier-B papers are read and folded into the plan.

**Open strategic question, now documented:** the repair study may ship as its
own conference paper before the journal. **Decided not to decide yet** — the
conference core and the journal core are the same experiment, so build and run
first, then branch on the result (D11). See `PUBLICATION_STRATEGY.md`.

Since the 2026-08-24 code-review pass: **B1/B1b/B2/B3 and the defect-bank
inventory are built and tested** (133 tests pass), the **replay fidelity gate
passes** (135 recorded facts reproduced exactly, 0 mismatches), and the design
is *not* fully frozen — **D9 and D10 are new and both block trials**, alongside
D8. The Phase-0 supervisor memo still does not exist. That memo is the next
action.

---

## 2. Read in this order

1. **`JOURNAL_PLAN.md`** — the plan (~975 lines). It grew by accretion:
   **§13 and §14 amend earlier sections**, so where §3/§5/§6 and §13/§14
   disagree, the later section wins. **Exception:** the 2026-08-24 code-review
   pass (banner at the top of the file) **edited §3/§4/§5/§6/§8 in place** —
   those sections are current, not superseded. Its changes are the ones checked
   against the repository rather than the literature.
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

## 4. Journal extension — the frozen design

Goal: measure whether feedback-injected retry **repairs** a detected defect —
the quantity the conference paper honestly could not measure.

- **Two tiers.** Tier 1 replays real defects captured on disk; Tier 2 applies
  8 synthetic operators (one per supervisor check class) to clean outputs.
- **Four arms.** A0 capability ceiling · A1 measured-fact feedback (production
  path) · A2 generic rejection · A3 bare re-draw.
- **Placement factor — four levels (D9).** **P0** defective output *absent*
  (the production path; Tier-1 default) · P1 user-turn artifact (**Tier-2
  default, D10**) · P2 assistant-turn · P3 (exploratory) P2 + correction marker.
- **Analysis.** Matched per defect: Cochran's Q omnibus, exact McNemar for
  A1-vs-A2 and A2-vs-A3, A1/A0 ratio with delta-method CI, block on defect
  identity, multinomial over four outcome classes, stratify by origin and stage.
- **Venue.** EMSE regular track (§12). ASE is a live alternative — AgentChaos
  (ASE 2026) proves the SE community takes agent-fault-injection work.

### Next actions, in order

1. **Resolve D12 — it blocks B7 and nothing else can start after it.** If
   downstream propagation is in scope (and `PUBLICATION_STRATEGY.md` §5 argues
   it must be, or the journal has no thesis left after a split), the runner has
   to persist the full retried output and enough state to re-run downstream
   stages later. Nearly free on the first pass; a full re-run to recover
   afterwards.
2. **Write the Phase-0 memo** and get supervisor sign-off on **D1–D12**. Three
   block every trial: **D8** (constraint completeness, §5 below), **D9**
   (placement has four levels, and the production one was unnamed), **D10** (the
   Tier-2 core must run at P1 or every arm hits ceiling — `JOURNAL_PLAN` §6.1).
   **D8 goes in the conference core, not the journal** — deferring it breaks the
   contrast the paper leads with.
3. Build **B4–B8** with the golden gates (the §13.5 replacement-value scorer
   test; the redefined collateral metric). B1/B1b/B2/B3 are done and their gate
   passes — re-run it any time with
   `python scripts/replay_stage.py --verify out_study`.
4. Run the core: A0/A1/A2/A3 at P1 across three stages, **plus C1**, **plus the
   warm-resample subset**. Tier 1 (**132** trials at P0) is the realism anchor →
   go/no-go → Tier 2 (~980 calls at P1, ~3 nights).
5. **Then** branch on the result (D11): A1 ≫ A2 → splittable; A1 ≈ A2 → do not
   split.

Two things to chase in parallel, both cheap and both time-sensitive:
**the ESEM registered-report cycle dates** (they outrank the whole venue table
and would change §10), and **an email to the #1 chairs about an
extended-version route** — worth doing while #1 is in review, not after.

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

For the journal extension, both read-only and dataset-free:

```bash
venv/Scripts/python.exe scripts/analysis/defect_bank.py --out out_study/defect_bank.json
```

```bash
venv/Scripts/python.exe scripts/replay_stage.py --verify out_study
```

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
- Test suite: **133 pass**, 6 integration deselected
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
