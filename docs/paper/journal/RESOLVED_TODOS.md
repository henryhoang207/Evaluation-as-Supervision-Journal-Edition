# Resolved TODOs — JSS journal draft

Log of the session of 2026-10-23 that closed the open `\TODO`s in this draft.
Each entry gives what was open, what changed, where the decision came from, and
how the change was checked before moving on.

**The author's answers, 2026-10-23** (the decisions every entry below rests on):

- The author list is **Huu Hoan Hoang and Manh Toan Nguyen** only.
- Conference paper #1 was **accepted at EAI FISAT 2026** and is **not yet
  published**.
- The repository **becomes public when the journal paper is submitted**.
- **No funding.**
- **The author ran C7**, with no generative-AI support.

Starting point: `python check_draft.py` reported **10** open `\TODO`s (the
README said 13; three had already been closed by an earlier session). Two more
TODOs sat in source comments, which the checker does not count. **End point: 0
open `\TODO`, 0 `\CSEVEN`; the PDF builds with no undefined reference and no
overfull line** (§11).

### Summary

| # | Open item | File | Resolution | Entry |
|---|---|---|---|---|
| 1 | Defects4J citation | `02-related-work.tex`, `references.bib` | added, verified on Crossref and the abstract | §1 |
| 2 | Author list, D5 (comment TODO) | `main.tex` | Hoang (corresponding) and Nguyen | §2 |
| 3 | CRediT statement | `declarations.tex` | roles assigned | §3 |
| 4 | Competing interests, "confirm for every author" | `declarations.tex` | standard statement kept | §3 |
| 5 | Funding, "confirm; who paid for the API" | `declarations.tex` | no funding | §3 |
| 6 | Acknowledgements | `declarations.tex` | the three conference co-authors and the second rater | §3 |
| 7 | Extension declaration, D2 | `01-introduction.tex` | accepted at EAI FISAT 2026 | §4 |
| 8 | `hoang2026eas` entry (comment TODO) | `references.bib` | `@inproceedings`, "In press" | §4 |
| 9 | Conference implications, D3 | `06-discussion.tex` | journal findings, per the 2026-09-14 precedent | §5 |
| 10 | Data availability, D4 | `declarations.tex` | public GitHub repository; no review text in it | §6 |
| 11 | Generative-AI declaration | `declarations.tex` | wrong C7 claim removed; Claude Code use still declared | §7 |
| 12 | Summary note under the abstract | `main.tex` | closed | §8 |

Also closed: five open items from `CITATION_CHECK.md` (§9). Status lines were
synced in the journal README, the paper plan, NEXT_SESSION, CLAUDE.md and the
session memory (§10). **What the author still has to do or confirm is collected
in §12.**

---

## 1. Defects4J citation — `sections/02-related-work.tex`

**Was open:** `\TODO{Consider one citation to Defects4J (Just et al., ISSTA
2014) ...; not yet in the bibliography.}`

**Changed:**
- `02-related-work.tex`, §2.4 "Synthetic faults as proxies for real ones": two
  sentences before the `just2014mutants` sentence. "Testing studies commonly
  used hand-seeded faults and mutants in place of real bugs, which are hard to
  extract and reproduce. Defects4J (Just et al., 2014) was built to make real
  faults available for controlled studies." The `\TODO` is deleted.
- `references.bib`: new entry `just2014defects4j`, placed after
  `just2014mutants`, with a verification comment.

**Source check:**
- Crossref `10.1145/2610384.2628055`: title, the three authors (Just, Jalali,
  Ernst), *Proceedings of the 2014 International Symposium on Software Testing
  and Analysis*, pp. 437–440. All match the entry.
- Abstract read at the ACM DL and in the authors' PDF. It says hand-seeded
  faults or mutants are "commonly used as a substitute" because real bugs are
  hard to extract and reproduce, and that Defects4J provides real bugs for
  reproducible studies. The title says "to enable controlled testing studies".
  Both new sentences say no more than that.
- Crossref also shows `just2014mutants` (FSE 2014) citing Defects4J, so the two
  works are correctly placed side by side.

**Review:**
- `check_draft.py`: TODO 10 → 9; missing citations none; 36 of 36 entries cited.
- Reread the paragraph and changed a repeated "long" ("long before … had long
  used") to "commonly used", the abstract's own wording.
- The two Just et al. (2014) entries must print as 2014a and 2014b. Checked
  in the builds of §4 and §11: they do.

---

## 2. Author list and corresponding author (D5) — `main.tex`

**Was open:** the `TODO (D5 ...)` comment above the author block. The block
still carried the five conference authors as a default.

**Changed:**
- Title page: **Huu Hoan Hoang** (corresponding author,
  `105732188@student.swin.edu.au`) and **Manh Toan Nguyen**, both at the
  existing affiliation (Swinburne Vietnam, FPT University, Hanoi). Pham, Tran
  and Nam Khanh Nguyen are removed.
- The comment above the block now records the decision and its date, and
  keeps the CAUL note.
- The header comment "conference paper #1, under review" now reads "accepted
  at EAI FISAT 2026, not yet published".

**Decision source:** the author, 2026-10-23 ("Author list contain only Hoan and
Toan"). The corresponding author was not named in the answer, so Hoang stays
corresponding author, as in the draft and the conference paper.

**Kept on purpose:** the `hoang2026eas` bib entry still lists all five
authors. It cites the conference paper, and that paper has five authors
(checked against `../main.tex`).

**Review:**
- Searched every `.tex`, `.bib` and `.txt` file for the three removed names.
  The only hits are in the `hoang2026eas` entry, which is correct.
- No sentence in the draft says "five authors", "one of us" or "co-authors".

---

## 3. CRediT, competing interests, funding, acknowledgements — `sections/declarations.tex`

**Was open:** four `\TODO`s: the CRediT roles, "confirm for every author",
"confirm; state who paid for the model API usage", and "Thank the two raters
... if they are not authors, and anyone else who helped".

**Changed:**
- **CRediT.** Hoang: Conceptualization, Methodology, Software, Validation,
  Formal analysis, Investigation, Data curation, Writing – original draft,
  Writing – review & editing, Visualization, Project administration.
  Nguyen: Supervision, Writing – review & editing.
- **Competing interest.** The standard Elsevier sentence is kept; the `\TODO`
  is deleted.
- **Funding.** The standard "did not receive any specific grant" sentence is
  kept. The author said "No funding". API costs the author paid personally
  are not funding.
- **Acknowledgements.** Thanks Pham, Tran and Nam Khanh Nguyen, who built the
  original pipeline with the first author as the COS30018 Intelligent Systems
  group project and co-authored the conference version. Also thanks the
  independent rater who, with the first author, rated the blinded audit sheet
  (§4.3).
- The header comment of the file no longer calls every block a draft.

**Decision source:** the author's answers (author list, "No funding"). The
rater facts come from `backend/out_study/audit/BRIEFING.md`. It is addressed to
rater 1, the author running the audit ("You are rater 1 ... you fill in
`rating_a.csv`"). Rater 2 is an outsider, not to be told the pipeline has a
supervisor. So only rater 2 is thanked, and that rater's name is not in the
repository.

**Review:**
- Checked that the label `sec:design-operators` (04-design.tex line 78)
  contains the rater paragraph (line 139).
- Checked the unit name, "COS30018 Intelligent Systems", against `CLAUDE.md`.
- `check_draft.py`: TODO 9 → 5.

**For the author to confirm** (written as defaults, without a `\TODO`):
- The CRediT roles, especially Nguyen's. Every listed author must at least
  have reviewed and approved the manuscript.
- That neither author has a competing interest.
- The rater's name, if they agree to be named. The sentence works without it.
- §4.3 says "two raters independently judged a blinded sheet" without saying
  one was the first author. The acknowledgement now says so. Consider stating
  it in §4.3 or §7 as well.

---

## 4. Conference-version declaration and its citation (D2) — `sections/01-introduction.tex`, `references.bib`

**Was open:** the intro `\TODO{Extension declaration ... decide whether to
submit before or after its decision, then finalise this paragraph and the
hoang2026eas entry}`, and the bib comment `% TODO: update when conference
paper #1 is decided`.

**Changed:**
- **Intro, "Relation to the conference version".** The `\TODO` is gone. The
  paragraph now opens "This article extends the conference paper accepted at
  EAI FISAT 2026 (Hoang et al., 2026), which introduced …". The rest of the
  paragraph (what is summarised, what is new) was already right and is
  unchanged.
- **`hoang2026eas`** changes from `@unpublished`, "Manuscript under review" to
  `@inproceedings`. Booktitle: *Proceedings of the EAI FPT International
  Conference on Intelligent Systems and Advanced Technologies (FISAT 2026)*.
  Note "In press". Elsevier's guide reserves "in press" for accepted work, so
  this also closes citation-check item R2.4-5 (the guide discourages
  "unpublished results").
- **Two attributions that had no citation now have one** (citation check
  R3.2-1 and the first half of R2.4-8): `03-system.tex` §3.4 "The conference
  version (Hoang et al., 2026) stated the principle …", and
  `06-discussion.tex` §6.4 "The conference version (Hoang et al., 2026)
  noted that 'an accepted claim may inherit an upstream error'". An extended
  version should cite its earlier paper wherever it relies on it.

**Decision source:** the author, 2026-10-23 (accepted at EAI FISAT 2026, not
yet published). Acceptance settles D2's timing question. JOURNAL_PAPER_PLAN §2
item 2 worried about the article being "under consideration elsewhere" while
#1 was still under review. That no longer applies. The conference's official
name and proceedings series come from `fisat.eai-conferences.org/2026` and the
FPT University conference page, both read 2026-10-23.

**Review:**
- Scratch build (`latexmk`): 23 pages, 0 undefined citations or references.
  The reference prints as "Hoang, H.H., …, 2026. Evaluation as supervision: …,
  in: Proceedings of the EAI FPT International Conference on Intelligent
  Systems and Advanced Technologies (FISAT 2026). In press."
- natbib now prints the two Just et al. entries as **2014a** (Defects4J) and
  **2014b** (mutants). No year is typed by hand next to either.
- Reread the intro sentence. The first version, "the conference paper of
  Hoang et al. (2026), accepted at …, which …", read awkwardly, so it now
  reads "the conference paper accepted at EAI FISAT 2026 (Hoang et al.,
  2026), which …".
- `check_draft.py`: TODO 5 → 4.

**Not done, and why:**
- The paper is **not on the EAI FISAT 2026 accepted-papers page**. That page
  lists the main track only, so the acceptance was likely in a later track. Check
  the entry's title and author list against the camera-ready version.
- Series, publisher, pages and DOI cannot be added until the volume is out.
  The two quotations in §6 of the conference paper still need page locators
  then (R2.4-8, second half).
- ⚠ **Camera-ready deadline.** The site lists camera-ready deadlines of 29 and
  30 October 2026 for its later tracks. If the camera-ready changes the claims
  that §6.6 revises (incidence and instability, retry repair), §6.6 must be
  updated to match. See §5.

---

## 5. Revisions to the conference version (D3) — `sections/06-discussion.tex`

**Was open:** `\TODO{Author decision 3 ...: confirm that items 2 and 4 are
treated as journal findings, following the precedent set for the matcher
defect on 2026-09-14, and not as a note to the conference chairs.}`

**Changed:** the `\TODO` becomes a LaTeX comment recording the decision. §6.6
itself is unchanged: items 2 (incidence and instability are rates of
supervisor flags) and 4 (retry repair) stay in the journal as its own
findings.

**Decision source:** the author's instruction to resolve every open item,
applied by following the precedent the author set on 2026-09-14 (Q2: the matcher
defect is a journal finding, not a note to the chairs). That was also the
recommendation in the plan the author was shown. The answers of 2026-10-23
did not cover D3 directly, so it is listed under "to confirm" below.

**Review:** reread items 1–4 against the TODO's wording. Items 2 and 4 are the
incidence/instability and retry-repair items. `check_draft.py`: TODO 4 → 3.

**For the author:** the accepted paper's camera-ready deadline (29 or 30
October 2026 for the later tracks) is the one chance to correct items 2 and 4
in the conference paper itself. If you do, §6.6 must quote the published
wording, and an item the camera-ready already fixed should leave the list. The
comment in the source says so.

---

## 6. Data availability (D4) — `sections/declarations.tex`

**Was open:** `\TODO{Author decision 4 ... fill in the repository URL and an
archived DOI (e.g. Zenodo). Check the Yelp Open Dataset terms before
redistributing stage outputs derived from reviews. ... consider opting in.}`
and the placeholder "[repository URL, archived as DOI]".

**Changed:** the statement now names the public repository,
`https://github.com/Hahhahahaadsa/Evaluation-as-Supervision-Journal-Edition`
(the `origin` remote of this checkout). It now says what the records contain
("the pipeline's own outputs together with the Yelp business names and the
business and review identifiers they refer to, but no review text"), and that
the Yelp Open Dataset itself is not redistributed. The DOI placeholder is
gone. JSS's Option C is "deposit and cite", and a public repository meets it.
The `\TODO` becomes a comment that records the decision and the check.

**Decision source:** the author, 2026-10-23 ("Repo will be public after I
submitted").

**What was checked before writing "no review text"**:
- Every tracked file under `backend/out_study/` (346 files): the analysis
  dumps hold `review_id`, sentiment and aspect labels only. Every string over
  300 characters in the trial records (T1–T2W, T2L, C7 preflight) is a
  pipeline output (patterns, recommendations, summaries), never a review. The
  downstream stages never see review text, so their outputs cannot quote it.
- `audit/rating_sheet.md` shows outputs and review ids, not reviews.
- `git grep` over the whole repository for Yelp review records (`useful`,
  `funny`, `cool`, `"text":`) finds only invented test fixtures (`abc123`,
  `r1`).
- `backend/data/raw/` is empty and gitignored; the processed SQLite index is
  gitignored.

**Review:** reread the statement against those checks. The first version
said only "Yelp business and review identifiers". The pipeline outputs and
judge records also name the businesses ("Greek Cafe Grill"), so the sentence
now mentions business names. `check_draft.py`: TODO 3 → 2.

**⚠ For the author before the repository goes public** (not resolvable in the
draft):
- **Yelp Dataset Terms of Use** (version of 7 July 2023, the one Yelp serves
  today). §3 says that **before any public presentation or publication** of
  results that involve the Data, you must submit your findings to Yelp for
  review. Yelp then approves within five business days. This applies to the
  FISAT presentation (25–27 November 2026) and to this paper. §4.A and §4.D
  forbid distributing or sharing "any of the Data", and §5 makes derivative
  works Yelp's property. The repository holds no review text, but it does hold
  Yelp business names, business and review ids and per-review labels. Whether
  that counts as "the Data" is a question for Yelp, not one the draft can settle.
  Sending the findings under §3 is also the natural place to ask.
- **Push first.** Everything, including this session, was committed locally
  on 2026-10-25, but nothing has been pushed. Local `main` is ahead of
  `origin`. "Every trial record … available" is true of the remote only after
  the push.
- **Do not commit** the untracked `1-s2.0-S1567832608000775-main.pdf` (a
  publisher's PDF), `2308.08155v2.pdf`, or the two `journal*.zip` archives.
- Checked: no API-key pattern (`sk-…`, `AIza…`) anywhere in the git history,
  and `.env` is not tracked.
- Optional: archive a tagged snapshot on Zenodo and add its DOI. A GitHub URL
  can change, a DOI cannot. Opting in to the JSS Open Science badge is a
  choice in the submission system.

---

## 7. Generative-AI declaration — `sections/declarations.tex`

**Was open:** `\TODO{Required by Elsevier ... The second-model cell was set
up, run and analysed on 2026-10-12 by an autonomous AI coding agent ... (the
name suggests OpenAI Codex -- confirm) ... Rewrite to match what happened.}`

**Changed:** the `\TODO` is deleted. Its claim about C7 was wrong: **the author
ran C7 with no generative-AI support** (author, 2026-10-23). The declaration
never mentioned C7, so it needed no rewording. It still declares what is true and
what Elsevier requires: Claude, through Claude Code, was used to draft and
revise the manuscript text, tables and LaTeX source, and to help write and test
the study's software and analysis scripts. A source comment records the
correction.

**Why the Claude Code sentence stays:** this manuscript was drafted with Claude
Code. The commit that added the draft (`3906449`) and the C7 merge (`99e9e98`)
both carry a `Co-Authored-By: Claude` trailer. Elsevier's policy
requires that use to be declared. Saying no AI tool was used would be a false
declaration. The author's "no GenAI supported" is read as applying to C7.

**Review:** reread the declaration against Elsevier's template wording ("used
[tool] in order to [reason]. After using this tool, the authors reviewed and
edited ..."). It matches. `check_draft.py`: TODO 2 → 1.

**FYI:** the C7 work sits on a git branch named `codex/c7-local-replication`,
which a reader of the public repository may take to mean OpenAI Codex. The name
does not affect the declaration.

---

## 8. Summary note on the title page — `main.tex`

**Was open:** the visible `\TODO{Draft of 2026-10-08 ... Open before
submission: author list ...; the conference-version declaration ...; data
availability; the Tier-C citations ...; and the generative-AI declaration.}`
printed under the abstract.

**Changed:** the `\TODO` becomes a LaTeX comment saying the items it listed
were closed on 2026-10-23 and pointing here. Each listed item is closed in
§1–§7 above. The Tier-C citations other than Defects4J had already been
closed by an earlier session; `check_draft.py` found no Tier-C `\TODO` left
in §2.

**Review:** `check_draft.py`: **TODO 1 → 0, C7 0**; missing citations none;
dangling references none; 36 of 36 entries cited. A `grep` for `\TODO{` and
`\CSEVEN{` finds only the two lines in `main.tex`'s header comment that
document the macros.

---

## 9. Open items from `CITATION_CHECK.md` that this session also closed

These were not `\TODO`s, but they were flagged in the draft's own
verification record as waiting on the author, and two of them sit in entries
this session touched anyway.

| Item | What it was | Resolution | Checked against |
|---|---|---|---|
| R2.4-5 | `hoang2026eas` cited as "Manuscript under review" | "In press", EAI FISAT 2026 (§4) | author's answer; conference site |
| R3.2-1 and R2.4-8 (first half) | the conference version named without a citation (`03-system.tex` §3.4, `06-discussion.tex` §6.4) | `\citep{hoang2026eas}` added at both points (§4) | the citation check's own suggestion |
| R2.4-7 | Defects4J would make the two Just et al. (2014) entries collide | natbib prints 2014a and 2014b; no year typed by hand (§4 review) | scratch build `main.bbl` |
| R2.4-4 | `yelpdataset` had `year = {2024}`, which nothing supported | `year = {2022}`; access date now 23 October 2026; comment records why | the dataset page, re-read 2026-10-23: 6,990,280 reviews and 150,346 businesses, the counts of the local index, whose reviews end 2022-01-19 |
| R2.4-1 | Tsui's 64.5 % called "an average gap", which reads as percentage points | "Its self-correction blind spot, one minus the ratio of the internal to the external correction rate, averages 64.5 % across 14 models. Appending … 'Wait' reduces that blind spot by 89.3 %." (`02-related-work.tex` §2.2) | arXiv 2507.02778v3: abstract, eq. (1) and §4.1 ("The blind spot averages 64.5%") |

**Review:** the first rewording of R2.4-1 said "a relative shortfall rather
than a difference in percentage points". It was correct but clumsy, so it was
replaced with the definition itself, verified against eq. (1). The intro's
summary ("closes most of the gap", `01-introduction.tex`) was judged fair by
the citation check and is unchanged.

**Left open on purpose** (they need the author or a later date):
- R2.4-2: recheck the three unrefereed preprints (MAS-FIRE, Role Relabeling,
  Arimbur) **the week you submit**.
- R2.4-3: whether to cite the two models (Gemini 2.5 report, Qwen2.5 report).
  It is optional, and an uncited entry would break the zero-orphan rule.
- R2.4-6: Tsui's COLM 2026 venue rests on the arXiv comment until the
  proceedings appear.
- R2.4-8 (second half): page locators for the two quotations of the conference
  paper, once it has page numbers.
- R2.4-9: optional citations for McNemar and the bootstrap.

---

## 10. Status lines brought up to date

Each of these described the TODOs as open or the conference paper as under
review:

| File | Change |
|---|---|
| `journal/README.md` | status paragraph; "Do not edit `../main.tex`" line (now: accepted, not yet published); files table (36 sources; this file); the "Two exceptions" paragraph, which the earlier session had already closed (canonical-JSON identity in `T2/analysis.json`, 50 tests pass); the `\TODO` section, rewritten as "all closed"; checklist item 1 ticked; new item "confirm the defaults" |
| `../JOURNAL_PAPER_PLAN.md` §2 | heading "✅ all answered 2026-10-23", plus the answers above the original questions, which are kept as asked |
| `../NEXT_SESSION.md` | dated update block at the top |
| `CLAUDE.md` (repository root) | "submitted and under review" → "accepted at EAI FISAT 2026, not yet published" |
| `main.tex` header comment | "conference paper #1, under review" → accepted (§2) |
| Session memory | new note with the answers; the overview's claim that "a Codex agent" made the C7 commits is corrected, because the author ran C7 |

Not edited: `CITATION_CHECK.md` (a dated record of past runs; §9 here says
which of its items are now closed), `docs/paper/main.tex` (the conference
paper, never edited), and `PUBLICATION_STRATEGY.md` (historical reasoning).

---

## 11. Final review

- `python check_draft.py`: abstract 248 words (limit 250); 5 highlights, all
  ≤ 85 characters; **C7 0, TODO 0**; missing citations none; dangling
  references none; **36 of 36** entries cited.
- Fresh scratch build (`latexmk -pdf`, copy outside OneDrive): **23 pages, 0
  undefined or multiply defined references, 0 overfull boxes**. BibTeX gives
  9 "empty pages" warnings, all for entries that have no page numbers; the new
  one is `hoang2026eas`, which is in press.
- Every edited passage was reread in the source after the last change. The
  rewraps in §2.2, §3.4 and §6.4 left no line of mine over 82 characters. The
  three slightly longer lines left in those files were there before.
- `tests/test_repair_analysis.py`: 50 passed (the earlier session's
  byte-identity work, which the README now describes as done).
- Searched the draft for the removed authors' names (only the conference
  entry, correctly) and for "under review" (none left in the draft).
- Mistakes caught in review and fixed: two wrong section numbers in this file
  (§3.5 → §3.4, §6.3 → §6.4); a claim here that the README records the use of
  Claude Code (it does not; the commit trailers do); a repeated word in the
  Defects4J sentence; two clumsy first drafts (the intro sentence, the Tsui
  sentence); and a gendered pronoun for the author in the session memory.

---

## 12. What the author still has to do or confirm

**Confirm the defaults written in this session:**
1. CRediT roles (§3), especially Manh Toan Nguyen's.
2. No competing interest for either author (§3).
3. Hoang as corresponding author (§2). The CAUL waiver depends on that
   author's affiliation: Elsevier must read it as Swinburne University of
   Technology. The affiliation line says "Swinburne Vietnam, FPT University",
   so check it is recognised, and submit from the `@student.swin.edu.au`
   address.
4. D3 (§5): journal findings, the precedent applied for you.
5. The `hoang2026eas` title and authors against the FISAT camera-ready (§4).
6. The acknowledgement says the first author was one of the two raters. §4.3
   does not say so. Consider adding it there (§3).

**Before the repository goes public (§6):**
7. Yelp Dataset Terms §3: submit the findings to Yelp before the FISAT
   presentation and before this paper is published, and ask whether business
   names, ids and per-review labels may be shared (§4.A, §4.D, §5).
8. Push. Everything up to and including this session was committed locally
   on 2026-10-25 at your request, but local `main` is ahead of `origin` and
   nothing has been pushed.
9. Do not commit the publisher PDF, the arXiv PDF or the two `journal*.zip`
   files.
10. Optional: Zenodo snapshot with a DOI; opt in to JSS's Open Science badge.

**Time-sensitive:**
11. The FISAT camera-ready closes on 29 or 30 October 2026. If it changes the
    claims §6.6 revises, update §6.6 (§5).
12. The week you submit: re-run `/ars-citation-check` for the three preprints
    (R2.4-2) and the FISAT entry (§9).

**Not a `\TODO`, still open:**
13. Length: about 43 single-column pages against JSS's encouraged 36. Trim
    about 7 pages or justify the length in the cover letter. Candidate cuts are
    in the README checklist.
14. Vitae, cover letter (extension declaration, length if needed), optional
    graphical abstract (README checklist).
