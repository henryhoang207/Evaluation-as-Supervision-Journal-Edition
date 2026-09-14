> # HISTORICAL — do not act on this file
>
> **Written 2026-08-02/03, before any run executed, to produce the *conference*
> paper. That paper is finished and under review.** Re-checked 2026-09-02.
>
> **Start at [`NEXT_SESSION.md`](NEXT_SESSION.md)**, then `JOURNAL_PLAN.md`
> (authoritative) and `PREREGISTRATION.md` (the analysis document that must be
> committed before the first trial).
>
> Three statements below are **wrong**, not merely stale. Each is corrected in
> place where it appears:
>
> | Section | Claim | Truth |
> |---|---|---|
> | 1.3 | "`docs/paper/` is gitignored — never pushed" | **False, and dangerous.** `docs/paper/` is **tracked**; only build artefacts are ignored. Acting on this leaves the paper and the paid-for study dumps uncommitted. |
> | 1.1 | write via the scratchpad and `cp` into place | Superseded — use the **8.3 short path** for `Read`/`Write`/`Edit`. |
> | 10 | "token accounting does not exist anywhere in `app/`" | False. `BaseAgent.total_tokens_used` exists; see `JOURNAL_PLAN.md` B1. |
>
> Obsolete sections: **§2** (`main.tex` is complete, not "drafted except
> §5–§6"), **§5** (the study ran), **§7** (its opening prompt tells a new
> session to restructure a finished paper — do not run it), and §10's blocking
> item.
>
> Still worth reading: **§6** (traps), **§8** (page budget, though it predates
> the written §5–§6 and understates the overrun), and the findings in **§9–§10**,
> which record how the sample and the database were fixed.

# Paper Work — Session Handoff

**Written:** 2026-08-02 · **For:** starting the paper in a fresh chat session
**Read this first.** It is self-contained: a new session does **not** need to
re-read the repository to continue. Doing so costs several dollars and adds
nothing the plan does not already carry.

---

## 1. Environment gotchas — read before touching any file

These cost real time to rediscover. All three are confirmed, not theoretical.

### 1.1 The repo path has a Unicode split (most important)

The path contains `Tài liệu`, which exists on disk in **two different Unicode
normalizations** (NFC and NFD). They print identically but Windows treats them
as **two separate directories**.

- **Bash** (`cwd`, relative paths) resolves to the tree **git tracks**. Correct.
- **Read / Write / Edit tools** with absolute paths resolve to a **parallel
  tree**. Wrong.

**Symptom:** `Write` reports "File created successfully", but the file is
invisible to `ls`, `git status`, and Explorer. Earlier in this project, `Read`
also failed on `README.md` even though it plainly exists.

**Workaround — superseded 2026-09-02.** The scratchpad-then-`cp` dance below
still works, but it is no longer necessary. Use the **8.3 short path** for
`Read`/`Write`/`Edit`; it resolves to the tracked tree:

```
C:\Users\hoanh\OneDrive\TAILIU~1\CSMATE~1\COS30018\Project\COS300~1.1_M\...
```

Bash with repo-relative paths also works. Verify with `git status --short`
rather than trusting a Write success message. The original three-step
workaround, kept for reference:

1. `Write` the file into the scratchpad (its path is pure ASCII, so no split).
2. `cp` it into place with **Bash**, using a **relative** path.
3. Verify with `ls -la docs/paper/` — never trust the Write success message.

### 1.2 Bash heredocs and apostrophes — overstated, but real

The Bash tool wraps commands in `bash -c '...'`, so a single quote inside a
heredoc body terminates the command early
(`unexpected EOF while looking for matching '`). Writing prose that contains
`don't`, `paper's`, `Cohen's` **will** break.

Route prose through a Python script file in the scratchpad instead of a heredoc,
or use only double quotes in `python -c` invocations.

### 1.3 WRONG — `docs/paper/` is TRACKED

**Corrected 2026-09-02, verified with `git check-ignore` and `git ls-files`.**

The original text claimed `.gitignore:64` ignored `docs/paper/` and that the
files "stay local and are never pushed, by explicit request". **That is false.**
`docs/paper/` is tracked; `.gitignore` ignores only build artefacts inside it
(`*.bak`, `*.aux`, `*.log`, `*.out`, `*.synctex.gz`).

This matters right now: **nothing from 2026-08-25 onward is committed**, and
that includes 8 Phase-A dumps which cost real API budget and exist in exactly
one place. A session that believed this section would leave them uncommitted.
See `NEXT_SESSION.md` §11 for the manifest and the commit-first instruction.

---

## 2. Current state of `docs/paper/`

| File | Status | Notes |
|---|---|---|
| `CHAPTER_PLAN.md` | **PARTLY SUPERSEDED** | §1, §2, §4, §5, §6 current (positioning, insights, evidence ledger, open decisions). **§3 is stale** — it is the original 6-page/7-chapter spec; a warning banner at the top says so. The live section skeleton is §3 of *this* file |
| `references.bib` | **CURRENT** | 22 entries, LNCS/BibTeX. **Not independently verified** — see CHAPTER_PLAN §5 D4. Note `sokolova2009` and `zhang2015` are now uncited |
| `main.tex` | **DRAFTED except §5–§6** | 8 sections, 8 tables, 2 figures. Sections 1, 2, 3, 4, 7, 8 have full prose (2026-08-03). §5 Method and §6 Results are still `\PH{}` scaffolds |
| `main.tex.bak` | rollback | The 7-section skeleton as it stood before the 2026-08-03 restructure |

**Not in the repo, required to compile:** `llncs.cls` and `splncs04.bst` from
Springer's LNCS author kit. Download and place beside `main.tex`.

```bash
pdflatex main && bibtex main && pdflatex main && pdflatex main
```

---

## 3. Section skeleton (DONE — recorded for reference)

Restructured 2026-08-03. All 8 sections, 8 tables and 2 figures exist in
`main.tex`. Budgets below are the *original* allocation; see section 8 for the
measured overrun against them.

**Section skeleton:**

1. Introduction `[1.0 pg]`
2. Background and Related Work `[1.5 pg]`
3. System and the Derivability Property `[1.0 pg]`
4. The Supervision Layer `[2.25 pg]`
5. Method `[1.5 pg]`
6. Results `[2.25 pg]`
7. Discussion, Limitations, Threats to Validity `[1.0 pg]`
8. Conclusion `[0.5 pg]`

**Tables and figures to scaffold:**

| Ref | Where | Content |
|---|---|---|
| Table 1 | §2 | Related-work positioning: who decides routing / what the feedback signal is / inter-stage vs single-generation verification |
| Table 2 | §4.2 | Stage to checks mapping |
| Table 3 | §4.6 | 22 failure-mode scenarios mapped to the defect classes each closes |
| Table 4 | §5.2 | Business sample strata |
| Table 5 | §5.5 | Measures classified by circularity |
| Table 6 | §6.1 | Defect incidence by check type |
| Table 7 | §6.3 | Retry outcomes |
| Table 8 | §6.4 | Token and latency cost |
| Figure 1 | §4.1 | Hub cycle — **a working TikZ draft already exists in `main.tex`; keep it** |
| Figure 2 | §6.2 | Defect rate vs review count |

Preserve from the existing `main.tex`: the LNCS preamble, the `\PH{}` grey
placeholder macro and `\NUM{}` red-unfilled-number macro, the draft-notes
toggle, and the TikZ Figure 1.

---

## 4. Decisions already locked

| Decision | Value |
|---|---|
| Track / sub-area | Track 1; **NLP and Multimodal AI** recommended (D1, not formally confirmed) |
| Paper anchor | The deterministic supervision layer (`backend/app/core/supervision.py` + hub graph) |
| Evidence strategy | Multi-business **observe-first** two-phase study (~20 businesses, ~26 runs) |
| Page budget | 11 pages **excluding** references |
| Format | Springer LNCS, single column |
| Authorship | **Deferred** (D5) — does not block writing §3–§5 |

---

## 5. What blocks the Results section

§6 cannot be written until the study runs. Four build items, then two run
phases — full detail in `CHAPTER_PLAN.md` §4 (Evidence Ledger):

1. Observe mode — measure but always proceed (~15 lines in `graph.orchestrator_node`)
2. `--business-id` selection in `run_pipeline.py` (~5 lines)
3. Stratified business sampler against `yelp.db`
4. Batch runner with checkpoint/resume (~120 lines)

Then Phase A (all businesses, observe) and Phase B (only businesses with a
retry-triggering defect, enforce). Roughly 1.5–2 h unattended, ~1.5 M tokens.
**Rate limits, not cost, are the binding constraint** — ~300 LLM calls.

**Sections 1–5, 7 and 8 do not depend on any of this.** Write them first.

---

## 6. Traps — do not do these

- **Do not** reuse `backend/out/` vs `backend/out_hub/` as a before/after pair.
  They ran on **different providers** (Gemini vs Groq/Llama), so the diff
  confounds supervision with model change.
- **Do not** use the pre-hub commit as the supervision-off arm. That is the old
  linear-chain graph — it confounds supervision with graph shape. Use observe mode.
- **Do not** claim novelty for multi-agent role decomposition, ABSA, the
  7-aspect taxonomy, LLM-as-judge, or Pydantic-validated output. All are prior
  art. See `CHAPTER_PLAN.md` §1.
- **Do not** bury a low retry-repair rate. It is the more interesting finding
  and directly tests Insight I3.
- **Never cut** the circularity paragraph (§7). The supervisor shares check
  logic with the offline evaluator by design, so a consistency-check improvement
  is near-tautological. Naming that ourselves is worth more than the result it costs.

---

## 7. OBSOLETE — suggested opening prompt (2026-08-03)

**Do not run this.** It instructs a new session to restructure `main.tex` into
a scaffold. The paper is finished and under review. Kept as a record only.

> Read `docs/paper/HANDOFF.md` and `docs/paper/CHAPTER_PLAN.md` (sections 3 and 7
> especially). Do not explore the rest of the repository — the plan is
> self-contained. Then restructure `docs/paper/main.tex` from its current
> 7-section, 8-page form into the 8-section, 11-page structure the plan
> specifies, scaffolding all 8 tables and 2 figures. Note the Unicode path
> gotcha in HANDOFF section 1: write via the scratchpad and copy into place with
> Bash, then verify with `ls`.

After that, the highest-value writing order is §4 (Supervision Layer) → §3
(Derivability) → §2 (Related Work), since all three draw on code and documents
that already exist and none waits on the study runs.

---

## 8. Page budget — measured, and currently over

Measured 2026-08-03 with `scratchpad/budget.py` (LNCS single column,
460 words per full body page; float sizes estimated).

| Section | Prose words | Est. pages | Budget | Ratio |
|---|---:|---:|---:|---|
| 1 Introduction | 522 | 1.13 | 1.00 | 1.13x |
| 2 Related Work | 547 | 1.47 | 1.50 | ok |
| 3 Derivability | 640 | 1.39 | 1.00 | 1.39x |
| 4 Supervision Layer | 1168 | 3.54 | 2.25 | **1.57x** |
| 5 Method | — | (0.51) | 1.50 | not written |
| 6 Results | — | (1.11) | 2.25 | not written |
| 7 Discussion | 574 | 1.25 | 1.00 | 1.25x |
| 8 Conclusion | 232 | 0.50 | 0.50 | ok |

**Written sections total 9.29 pg against a 7.25 pg budget.** Projected full
paper once §5 and §6 are written to their budgets: **~13.0 pages against 11**.

Two trim passes have already been applied (the drafts started ~39% over; the
second pass returned only ~85 words, so the prose is now dense). Closing the
remaining ~2 pages means cutting *content*, not wording. Options, best first:

1. **Drop Table 3** (unit-test scenarios, ~0.32 pg). The paper itself argues
   these tests establish little about real incidence — two sentences carry it.
2. **Fold §3.1** (pipeline description, ~0.35 pg) into §5.1 Testbed, where the
   dataset is described anyway. Keep §3.2–§3.3, which carry the argument.
3. **Compress §2 further** — `CHAPTER_PLAN.md` §3 already flags it as the most
   compressible section, and Table 1 does much of its work.
4. **Confirm the 11-page limit is real** for the target venue before cutting
   anything load-bearing.

Do **not** close the gap out of §4: it is the paper's core and already the most
heavily trimmed section. Never cut the circularity paragraph in §7.

---

## 9. What was found while drafting (2026-08-03)

Two errors inherited from the plan, both fixed in `main.tex`:

1. **Insight I1 was imprecise.** It states each stage consumes *only the
   previous stage's output*. The code disagrees: `ReportGeneratorInput` carries
   `analysis_summary`, `reasoning_summary` **and** `recommendations`, and
   `_measure_report` checks containment against both reasoning and strategy.
   The report stage reads three upstream stages. Derivability survives — every
   claim still traces to *some* upstream state — but the property is
   **closure, not linearity**, and §3.2 now states it that way. Fix this in
   `CHAPTER_PLAN.md` §2 I1 as well.
2. **The "22 failure-mode scenarios" count is wrong.** `test_supervision.py`
   defines **23** test functions, 2 of which are routing utilities, so the
   defensible figure is **21 failure modes plus 2 routing tests**. Table 3 and
   a `\PH{}` note in §4.6 record this.

---

## 10. Study build items — DONE (2026-08-03), with three findings

All four `[BUILD]` items from `CHAPTER_PLAN.md` §4 exist and are verified.
`tests/test_supervision.py` still passes 23/23.

| Item | Where | Notes |
|---|---|---|
| Observe mode | `app/core/graph.py` | `SUPERVISION_MODE=observe`. Records every non-proceed verdict to `state["observations"]`; downgrades `retry` to `proceed`; **skips** the frequency overwrite so the arm is genuinely unsupervised. `halt` still honoured (only `insufficient_data` is reachable). |
| `--business-id` | `run_pipeline.py`, `app/data/loader.py` | New `loader.get_business()`; bypasses fuzzy name search. |
| Stratified sampler | `scripts/sample_businesses.py` | Counts from the `reviews` table, not `businesses.review_count`. Seeded tie-break. `--category` filter. |
| Batch runner | `scripts/run_study.py` | JSONL checkpoint with `fsync`, resume-by-skip, per-business dumps in the layout `tier1_checks.run_all()` consumes, `--dry-run`. |
| *(added)* Category backfill | `scripts/add_categories.py` | See finding 1. |

### Finding 1 — yelp.db was never filtered to restaurants (fixed)
`build_db.py` ingests every business and drops the `categories` field, so the
DB held all 150,346 businesses: hotels, car dealers, visitor centres. The first
sample drew "Virginia City Visitor Center" and "Reedman Toll Chrysler Dodge
Jeep RAM". Running the restaurant-specific seven-aspect taxonomy over those
would generate aspect-misalignment and untraceable-recommendation detections
that are **domain-mismatch artefacts, not grounding defects**, inflating the
paper's headline number. `scripts/add_categories.py` backfills the column;
the sampler now filters to `Restaurants` by default. **52,268 of 150,346
qualify — 65% of the original pool was invalid.**

### Finding 2 — Insight I7 is wrong for this paper
FINDINGS F1 measured the review-count distribution over **all** businesses.
The paper is about restaurants, and their distribution is materially different:

| | p10 | p25 | p50 | p75 | p90 |
|---|---:|---:|---:|---:|---:|
| All businesses (F1, quoted in the paper) | 6 | 8 | 15 | 38 | 101 |
| **Restaurants only (correct for this paper)** | **7** | **14** | **34** | **92** | **214** |

The median restaurant carries **34** reviews, not 15. This weakens — and
partly inverts — the rhetorical force of I7: with `LOW_CONFIDENCE_N=30`, the
median restaurant now sits *above* the low-confidence threshold rather than
below it. **Fix before drafting §5.2**, and fix the last paragraph of §8, which
currently says "the median business in this dataset carries fifteen reviews".

### Finding 3 — the review cap flattens the top two strata
`MAX_REVIEWS=100`, so the p75 (92) and p90 (214) strata both analyse ~92–100
reviews and are not distinguishable in the results. Either raise
`MAX_REVIEWS` (more tokens per run) or choose percentiles below the cap.
Decide before running Phase A, since it changes what Figure 2 can show.

### Still blocking Table 8 — the diagnosis was WRONG

The original text read: *"Token accounting does not exist anywhere in `app/`."*
**It does.** `BaseAgent.total_tokens_used` and `reset_token_usage()` exist, and
`eval/harness.py` already uses them correctly. `total_tokens` is null in the
study runs only because `scripts/run_study.py` hard-codes it, under a comment
repeating this same false claim. See `JOURNAL_PLAN.md` B1.

### Commands
```
python scripts/add_categories.py                       # once
python scripts/sample_businesses.py --out out_study/sample.json
python scripts/run_study.py --phase A --dry-run        # no LLM calls
python scripts/run_study.py --phase A                  # Phase A
python scripts/run_study.py --phase B                  # Phase B
```
