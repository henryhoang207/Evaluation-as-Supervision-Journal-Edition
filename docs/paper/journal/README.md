# Journal paper — JSS draft

**Working title:** *Does Measured Feedback Repair Defects in LLM Pipelines? A
Pre-registered Fault-Injection Study of Deterministic Runtime Supervision*

**Target:** Journal of Systems and Software (Elsevier), regular paper — the
author's venue decision of 2026-10-08 (`../JOURNAL_PAPER_PLAN.md` §1).

**Status (2026-10-23): full draft, no placeholder open.** Every section is
written from `../RESULTS.md`, `../PREREGISTRATION.md` and the committed
`analysis.json` files. The second model (C7) was filled in on 2026-10-13 from
`backend/out_study/T2L/` (see "Second model" below); no `\CSEVEN` placeholder
remains. Every `\TODO` — the author decisions and the pre-submission items —
was closed on 2026-10-23; `RESOLVED_TODOS.md` records each decision, its
source and how it was checked, and lists what the author should still confirm.
The PDF builds cleanly, with no overfull lines, no undefined references and no
missing citations.

⛔ **Do not edit `../main.tex`** — that is conference paper #1, accepted at
EAI FISAT 2026 and not yet published.
Section 3 here describes the same system in **new** text. Keep it that way,
because Elsevier runs a similarity check against prior publications.

---

## Build and check

**Layout (2026-10-16):** Elsevier's final `5p` two-column format, with 10pt
body text and 9pt references. The title, abstract, main-text tables and forest
plot span both columns; the appendix table fits in one column. The compiled
PDF is 23 pages, including references and the appendix. The paper's wording,
results and open placeholders are unchanged by the layout conversion.

From `docs/paper/journal/`:

```
latexmk -pdf main.tex          # -> main.pdf (gitignored, like all build output)
python check_draft.py          # word count, highlights, placeholders, cites/refs
```

If `latexmk` is unavailable (MiKTeX also needs Perl for it), build directly:

```
pdflatex -interaction=nonstopmode -halt-on-error main.tex
bibtex main
pdflatex -interaction=nonstopmode -halt-on-error main.tex
pdflatex -interaction=nonstopmode -halt-on-error main.tex
```

`check_draft.py` reports:
- the abstract's word count against JSS's limit of 250 (248 on 2026-10-13,
  with the second-model sentence in);
- the highlights against JSS's limits of 3–5 bullets and 85 characters each;
- every open `\CSEVEN` / `\TODO`, per file;
- missing citations and dangling references.

To print without placeholders (e.g. for a word count), set
`\showplaceholdersfalse` in `macros.tex`. **Never submit that way.** A
placeholder must be resolved, not hidden.

## Files

| File | What it holds |
|---|---|
| `main.tex` | `elsarticle` (`final,5p,twocolumn,authoryear`), front matter, section inputs |
| `macros.tex` | `\CSEVEN`, `\TODO`, notation (`\arm`, `\op`, `\ci`), float settings, `prompttext` |
| `sections/00-abstract.tex` … `08-conclusion.tex` | the paper |
| `sections/declarations.tex` | CRediT, competing interests, funding, data statement, **generative-AI declaration** (JSS requires one before the references) |
| `sections/appendix.tex` | verbatim arm, placement and C1 wording (from `backend/scripts/arms.py`) |
| `figures/forest.tex` | Fig. 1, TikZ forest plot; its header lists the source of every value |
| `references.bib` | the 36 cited sources, each checked against Crossref, arXiv or the venue (31 on 2026-10-09; the later additions on the date in their comment), with a provenance comment where it matters |
| `CITATION_CHECK.md` | the citation audits (2026-10-09 and 2026-10-16): corrections, items flagged for review, claim-fidelity table |
| `RESOLVED_TODOS.md` | how each `\TODO` was closed on 2026-10-23, from the author's answers, and what is left for the author to confirm |
| `highlights.txt` | JSS highlights, submitted as a separate file |
| `check_draft.py` | the checks above |

## Where every number comes from

All of them come from committed data, through committed scripts, with no model
calls. The headers of `sections/05-results.tex` and `figures/forest.tex` name
the `analysis.json` behind each block. The second model's numbers come from
`T2L/analysis.json` (`repair_analysis.py --cell c7`, re-run 2026-10-13 and
identical to the committed file), `C7_preflight_r3/gates.json` and
`T2L/verification.json`; all 47 figures in the text were checked against them
mechanically.

**The two former exceptions are closed** (2026-10-20, by an earlier
session). The core's byte-identity shares and its
distinct-outputs-per-cell shares are now written by
`repair_analysis.py --cell core` to `T2/analysis.json` (`exploratory.
identical_to_clean`: A1 288/421, A2 223/417, A3 46/102;
`exploratory.distinct_outputs_per_cell`), comparing outputs as **canonical
JSON**, and `tests/test_repair_analysis.py` covers them (50 passed on
2026-10-23). §5.3 says once that "byte for byte" means canonical-JSON identity.

## Second model (C7) — filled 2026-10-13

C7 ran on 2026-10-12 (branch `codex/c7-local-replication`, merged into `main`
2026-10-13): Qwen2.5-7B-Instruct Q4_K_M on Ollama 0.40.3, 930 trials, 929
usable, amendments A10 and A11 (`../C7_STATUS.md`). Every `\CSEVEN` location is
filled: abstract, §1 (findings bullet 1, the cell list, contribution 2), §4.1
RQ6, §4.7 (Table 3 row and a "Second model" cell entry), §4.8 (execution,
verification, losses), §4.9 (Table 4 rows A10 **and A11**, and a fourth
disclosure for the failed G2 gate), §5.8 (written in full, with Table 10),
Fig. 1 (data row), §6.1, §6.7, §7, §8 and `highlights.txt`.

**The result changed the story, so some text outside the placeholders was
reframed — review these first:**
- C7 does **not** reproduce the ceiling: A1 72.9 %, A2 66.2 %, gap +6.8 pp
  [+0.5, +13.3], but McNemar p = 0.052 and the first repetition alone crosses
  zero. It is reported as exploratory evidence and a hypothesis, never a finding.
- Bold findings bullet 1 now reads "Feedback content does not change repair
  *at the ceiling*"; the §6.2 heading changed from "Placement, not wording, is
  the design lever" to "Placement is the design lever the production retry
  lacks"; the abstract's last sentence says "more than wording" instead of
  "rather than wording"; the conclusion's engineering lesson adds "beyond
  naming what failed"; §5.1 no longer says every interval in Fig. 1 includes
  zero (C7's does not).
- §6.1 offers a mechanism, marked as interpretation: without the measured fact
  Qwen left the defect in place in 26 % of retries (8 % with it), the
  localisation effect of Tyen et al. — already cited in §1 for that claim.
- C7's A3 (38.2 %) is declared **not interpretable**: every trial is scored
  against the *Gemini* clean output, which a fresh Qwen draw cannot reproduce
  (0 % identical, 100 % collateral, 0 % on reasoning). §5.8 and §7 say so.
- Neither model is cited (the draft never cited Gemini either). If you add a
  model citation, add both (the Gemini 2.5 and Qwen2.5 technical reports) and
  verify each against its source first, as for every other entry.
- C7 added about 4 pages (main text now ends on p. 43; it ended on p. 39).

### `\TODO` — all closed 2026-10-23

None is open. The four author decisions of `../JOURNAL_PAPER_PLAN.md` §2 were
answered by the author on 2026-10-23, and the pre-submission `\TODO`s were
closed from those answers. **`RESOLVED_TODOS.md` has the detail**, one entry
per item:

1. **Author list (D5):** Huu Hoan Hoang (corresponding) and Manh Toan Nguyen.
   The other three conference authors are thanked in the Acknowledgements.
   **The corresponding author's affiliation alone decides the CAUL–Elsevier
   APC waiver.** It must be Swinburne University of Technology, and the
   manuscript must be submitted from an institutional email.
2. **Extension declaration (D2):** conference #1 was accepted at EAI FISAT
   2026, not yet published. `hoang2026eas` is cited "In press".
3. **Conference #1 implications (D3):** §6.6 items 2 and 4 stay journal
   findings. If the FISAT camera-ready changes those claims, §6.6 must follow.
4. **Data availability (D4):** the GitHub repository is made public at
   submission. The records hold no review text. ⚠ Read
   `RESOLVED_TODOS.md` §6 before making the repository public: the Yelp
   terms ask for findings to be sent to Yelp before publication, and local
   `main` is not yet pushed.

The pre-submission items (Defects4J, CRediT, competing interests, funding,
acknowledgements, the generative-AI declaration, the summary note) are closed
too. The byte-identity script and the Yelp download date had already been
closed by earlier sessions. The other Tier-C citations were already in.

## Pre-submission checklist

- [x] `python check_draft.py` shows **0** open C7 and TODO placeholders. (C7: 0
  since 2026-10-13; TODO: 0 since 2026-10-23.)
- [ ] Confirm the defaults listed under "For the author to confirm" in
  `RESOLVED_TODOS.md` (CRediT roles, competing interests, the rater's name,
  the conference entry against the camera-ready).
- [x] `/ars-citation-check` run 2026-10-09; report in `CITATION_CHECK.md`
  (31 sources verified, 4 moved to their published versions, 3 unsupported
  claims rewritten). Done: the two entries written from memory, the page
  ranges, Pan et al.'s volume, and the venue comments on `positionbias` and
  `selfpreference`.
- [ ] Run it once more the week you submit, because the three remaining
  preprints (MAS-FIRE, Role Relabeling, Arimbur) may have been published by
  then. The other open items are in `CITATION_CHECK.md`, section 4.
- [ ] **Length.** The current two-column PDF is 23 pages including references
  and the appendix (2026-10-16). Before reformatting, the main text ran to about
  43 pages in the 12pt preprint layout (39 before C7; the whole PDF was 50
  pages). Assess the venue's page guidance in its requested layout; converting
  to two columns does not shorten the text. JSS encourages fewer than
  36 single-column pages, or an explanation in the submission. Either trim
  about 7 pages or justify the length in the cover letter. Candidate cuts: fold
  §4.7's prose into Table 3; tighten §2.2; merge §6.5 into §5.6; shorten the
  "Second model" entry in §4.7, which partly repeats §5.8.
- [ ] Vitae, at most 100 words per author, as JSS asks.
- [ ] Graphical abstract (optional).
- [ ] Cover letter: the extension declaration, the length justification if
  needed, and opting in to the JSS Open Science Initiative.
- [ ] An internal review pass (`/ars-reviewer`). `/ars-disclosure` can draft the
  AI statement.
