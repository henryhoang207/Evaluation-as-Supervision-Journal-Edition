# Citation check — JSS draft

Newest run first. Run 3 (2026-10-16, evening) re-ran everything on Run 2's files and is short. Run 2 (2026-10-16) is the full pass. Run 1 (2026-10-09) follows it, unchanged apart from heading levels.

## Run 3 — 2026-10-16, 21:50 (re-run on the Run 2 files)

**Run:** `/ars-citation-check`, third pass, started minutes after Run 2's addendum. **Scope and target style:** as Run 2. **Changed:** this report only. **Not touched:** every `.tex` and `.bib` file, `README.md` and `docs/paper/main.tex`.

### R3.1 Result

Nothing in the draft changed between Run 2 and this run except my own two edits (the download date in `declarations.tex` and the comment above the `yelpdataset` entry). So every check was re-run on the current files and agrees with Run 2. One new finding (item 1 below) comes from a check that Runs 1 and 2 did not have: whether a work is cited where it is named.

| Check | Result |
|---|---|
| Keys against `references.bib` and `main.aux` | 31 of 31 cited; 0 undefined, 0 uncited; 61 cite commands, 68 cited keys |
| Cite-bearing sentences against `HEAD` | 2 differ: the Tyen sentence (Run 2) and the data-statement sentence, now extended with the download date. The cited claims did not change |
| Entry hygiene, ordering, style | no gaps or hygiene issues; no multi-key cite out of order; no nested `\citet`, subject `\citep`, doubled year, numeric cite or typed author–year; no cite in the abstract or highlights |
| Crossref, 18 DOIs | 18 agree; no correction or retraction notice |
| doi.org, DataCite, arXiv | 21 of 21 DOIs resolve; 3 of 3 DataCite records agree; 10 of 10 arXiv records agree. Versions unchanged since Run 2 (Chen v2, Tsui v3) |
| Published versions of the 3 preprints; COLM 2026 | none found; the Tier-C works are unchanged |
| Yelp page | HTTP 200 |
| Build | fresh scratch copy, `pdflatex`, `bibtex`, `pdflatex` ×3: 23 pages, 0 undefined citations or references, the same 7 BibTeX "empty pages" warnings. `main.bbl` identical to Run 2's final build |
| Self-citation, currency | 10.3 % of uses (7 of 68); 90 % of sources from 2021 or later; 3 sources 10 or more years old |

### R3.2 New: a work named without its citation

**1. `03-system.tex:125–127` attributes a principle to the conference version with no citation at that point.** "The conference version stated the principle behind this design (a quantity the checker can compute should not be asked of the model) but had no counterfactual for it." The attribution is accurate: `docs/paper/main.tex` says "any quantity the checker can compute should not be asked of the model", in its Recompute-and-Overwrite subsection. The conference paper is cited at `03-system.tex:10`, 115 lines earlier. Suggested: `The conference version~\citep{hoang2026eas} stated…`. `06-discussion.tex:115` is the same case (Run 2 item 8). Not edited: it adds a citation to your prose.

How it was found: 17 typed mentions of 28 named works (AutoGen, Reflexion, MAS-FIRE, "conference version" and so on) were each checked for a cite of the same key within 260 characters. Twelve have one. Of the other five, two are a heading and a pointer to the revisions subsection (`01-introduction.tex:125, 137`), two are the attributions above, and one is the Defects4J `\TODO`. No name stands next to another work's cite.

### R3.3 Status of everything else

Items 1 to 9 of §R2.4 stand as written; none has changed. The two PDFs in the journal folder are still untracked and not ignored (§R2.8). The full-text pass of §R2.8 was not repeated, since no source changed.

---

## Run 2 — 2026-10-16

**Run:** `/ars-citation-check` (academic-paper skill, `citation-check` mode), second pass.
**Scope:** `docs/paper/journal/`: every `\cite*` in `main.tex`, `macros.tex`, `sections/` and `figures/` (14 files), against `references.bib`.
**Target style:** Elsevier author–year (`elsarticle-harv.bst`, natbib), as in Run 1. The skill's APA rules ("&", hanging indent, DOI as a URL) do not apply; the style file fixes the in-text and list forms.
**Changed:** `references.bib` only, and only how entries print (§R2.3). **Not touched:** every `.tex` file, `README.md`, and `docs/paper/main.tex` (conference paper #1, under review).

### R2.1 Result

The reference list holds up. All 31 keys resolve and every entry is cited. All 21 DOIs resolve, and every record I could fetch (18 Crossref, 3 DataCite, 10 arXiv, 1 PMLR page) still agrees with its entry. No retraction or correction notice was found for any of them. One citation was added since Run 1 (`tyen2024`, in the discussion).

I changed seven entries in `references.bib`, all in how they print. One sentence in §2 should be reworded (item 1 below). Everything else is what Run 1 left open, with today's status.

| Metric | Run 1 (2026-10-09) | Run 2 (2026-10-16) |
|---|---|---|
| In-text citation uses, counted per cited key | 67 (38 `\citep`, 29 `\citet`) | 68 (39, 29): one new use, `tyen2024` |
| Cite commands | not recorded | 61 (32 `\citep`, 29 `\citet`); 4 `\citep` carry several keys |
| Distinct sources cited | 31 | 31 |
| Entries in `references.bib` | 31 | 31 |
| Cited but undefined | 0 | 0 |
| Defined but never cited | 0 | 0 |
| Multi-key cites out of order | 0 | 0 |
| Entries with a DOI | 21 | 21 (18 Crossref, 3 DataCite) |
| Entries without a DOI | 10 | 10 (7 ICLR/COLM, the PMLR paper, the dataset, the unpublished manuscript; none has one) |
| Entries whose title or authors differ from the version of record | 4, fixed | 0 |
| Entries whose printed form needed a fix | not checked | 7, fixed (§R2.3) |
| Claims whose wording blurs the source | 3, rewritten | 1, flagged (item 1) |
| Self-citation | 10.4 % of uses, 3.2 % of sources | 10.3 % of uses (7 of 68), 3.2 % of sources; limit 15 % |
| Sources from 2021 or later | 90 % (28/31) | 90 % |
| Sources 10 or more years old | 3 | 3 (runtime verification 2009, mutants vs real faults 2014, chaos engineering 2016) |
| Retraction or correction notices | none | none |
| Build | 46 pages, single column | 23 pages, two column; 0 undefined citations or references |

### R2.2 How it was checked

| Check | Source or method | Result |
|---|---|---|
| Keys | Regex over the 14 `.tex` files (`\cite`, `\citet`, `\citep`, `\citealp`, `\citeauthor`, `\nocite` and starred forms) against the 31 keys in `references.bib` and against the `\citation` lines in `main.aux` | 0 undefined, 0 uncited, no key cited only inside a `\TODO`; `.aux` and sources agree both ways. `python check_draft.py` agrees |
| What changed since Run 1 | Every cite-bearing sentence compared with `HEAD` (`3906449`); then all 61 cite sentences re-read against Run 1's claim table | 1 sentence is new (`06-discussion.tex:50`, `tyen2024`); none removed or reworded. `02-related-work.tex` is unchanged since 2026-10-09, and so was `references.bib` until the edits in §R2.3. Run 1's rewrites are all still in place |
| Crossref | REST API by DOI for the 18 non-arXiv DOIs. Title, author family names, venue, pages, year, volume and issue compared in code | all 18 agree |
| Notices | Crossref `filter=updates:<DOI>` for each of the 18 | none (corrections, retractions and expressions of concern all absent) |
| DOI resolution | doi.org handle API, all 21 DOIs | 21 of 21 resolve |
| DataCite | The 3 arXiv DOIs: title and creators | agree (Chen v2, Arimbur v1, Jia v1) |
| arXiv | API for the 10 entries with an arXiv id: title, author list, version, comment, `journal_ref`, DOI | agree; none carries a `journal_ref` or DOI. Chen is at v2 (2026-07-31) and Tsui at v3 (2026-08-02), both as in Run 1 |
| Venues of arXiv-only entries | arXiv comments (CRITIC, Olausson, Huang: ICLR 2024; Tsui: COLM 2026). ICLR 2024 pages found by search for MetaGPT (oral) and Self-Debug. Microsoft Research and AG2 list AutoGen at COLM 2024 | consistent with the entries; Tsui see item 6 |
| ICML 2025 paper | `proceedings.mlr.press/v267/huang25ay`: title, nine authors, pp. 26202–26226 | agree |
| Published versions | Crossref title search and a web search for MAS-FIRE, Role Relabeling, Arimbur and Tsui | none found (items 2, 6) |
| Headline numbers | arXiv abstracts re-read: Tsui, Chen (v1 and v2), Arimbur, Jia | agree, except the unit in item 1 |
| Claims about the conference paper | Whitespace-normalised search of `docs/paper/main.tex`, read-only | §R2.5 |
| In-text labels | `main.bbl` | "et al." for the 27 entries with three or more authors, "A and B" for Leucker and Schallhart, a bare surname for Arimbur and Tsui, "Yelp Inc." for the corporate author. No author–year collisions |
| Cite usage | Scripted: `\citet` inside parentheses, `\citep` as a sentence subject, a year typed after `\citet`, numeric `[n]` cites, hand-typed author–year strings, cites in the abstract or highlights | none (the one `[7]` hit is `\newcommand{\fprow}[7]` in `forest.tex`) |
| Citation density | Prose cue scan of §1, §2, §6–§8 for literature-style claims without a cite | one paragraph (`08-conclusion.tex:29`, the engineering recommendations: the paper's own conclusions, no cite needed). Longest cite group: 4 keys |
| Build | Scratch copy outside the repo: `pdflatex`, `bibtex`, `pdflatex` ×3, then the same again after the §R2.3 fix | 23 pages, 0 undefined citations or references. 7 BibTeX "empty pages" warnings (ICLR/COLM), as in Run 1. Before the fix, `main.bbl` was identical to the one in this folder |
| Not available | DBLP and OpenReview (bot checks, as in Run 1; not worked around). Semantic Scholar (rate-limited in Run 1; not retried). The 14 reading-list PDFs were not re-read: the sentences that cite them are unchanged and so are the source versions | |

### R2.3 Corrections made

`references.bib` only. No author, year, venue, page or DOI changed. The style lower-cases a title after its first word, so a name has to sit in braces to keep its capitals. The file already protected `{AutoGen}`, `{MetaGPT}`, `{CAMEL}`, `{ChatDev}`, `{CRITIC}`, `{G-Eval}`, `{MT-Bench}`, `{AgentChaos}` and `{MAS-FIRE}`. These were the gaps.

| Key | Printed before | Printed after | Why |
|---|---|---|---|
| `arimbur2026` | "How many tries does it take? iterative self-repair in LLM code generation…" | "…take? Iterative self-repair…" | The style lower-cases the word after the question mark. `{I}terative` protects it |
| `huang2025resilience` | "…(ICML), PMLR. pp. 26202–26226." | "…(ICML), PMLR 267, pp. 26202–26226." | For `inproceedings` the style prints `publisher` with a full stop before "pp." and never prints `volume` or `series`. Volume 267 is now in the booktitle, as the NeurIPS volumes were in Run 1 |
| `selfrefine` | "Self-refine: …" | "Self-Refine: …" | method name |
| `zhang2023selfedit` | "Self-edit: …" | "Self-Edit: …" | method name |
| `tsui2026scbench` | "Self-correction bench: …" | "Self-Correction Bench: …" | benchmark name |
| `mtbench` | "…MT-Bench and chatbot arena" | "…MT-Bench and Chatbot Arena" | platform name |
| `yelpdataset` | "Yelp open dataset" | "Yelp Open Dataset" | dataset name |

The header comment of `references.bib` now records this re-check. A rebuild of the scratch copy changed exactly these seven `\bibitem`s and added no warning. The `main.pdf` and `main.bbl` in this folder predate the fix and will refresh on your next build.

### R2.4 Flagged for review (not changed)

**1. A figure is called a "gap" that the source defines as a ratio.** `02-related-work.tex:82–86` reads: "models correct the external error far more often (an average gap of 64.5 % over 14 models). Appending a contentless continuation cue ("Wait") closes 89.3 % of that gap." Tsui defines the Self-Correction Blind Spot as one minus the ratio of the correction rate on the model's own error to the correction rate on the identical external error. So 64.5 % is a relative shortfall averaged over 14 models. Read as percentage points, "gap" overstates it, and the abstract calls it the blind spot throughout. Run 1 marked this ✓ because the numbers are right; the unit was not pinned down. Suggested wording: "…and finds that models correct the external error far more often: over 14 models, the rate of correcting their own error is on average 64.5 % lower in relative terms. Appending a contentless continuation cue ("Wait") reduces that blind spot by 89.3 %." The sentence at `01-introduction.tex:40–42` ("closes most of the gap") is a fair summary and can stay. I did not edit it: it is a claim, not formatting.

**2. Three preprints are still unpublished** (Run 1 item 2). MAS-FIRE (arXiv v1 only, 2026-02-23), Role Relabeling (v2, 2026-07-31) and Arimbur (v1, 2026-04-12). None has a `journal_ref` or DOI on arXiv, none matches by title in Crossref (best similarity 0.59), and a web search for each returns only the arXiv record and mirrors. Role Relabeling changed between versions: v1 was titled "…LLMs Correct Others but Not Themselves" with 13 model–domain cells (10 of 13 at p < 0.001), and v2 has the current title and 12 combinations (10 of 12). The entry and §2.2 follow v2. Re-check the version and the status the week you submit.

**3. The two models are named but not cited** (the README tracks this). The hosted model is `gemini-2.5-flash` (`macros.tex:30`). The second is Qwen2.5-7B-Instruct in `Q4_K_M` quantisation, served by Ollama 0.40.3 (`04-design.tex:477–481`; five mentions in all). If you add citations, both sources exist: the Gemini 2.5 report (arXiv 2507.06261; the record lists 3,435 authors, so cite as "Comanici, Gheorghe and others") and the Qwen2.5 Technical Report (arXiv 2412.15115; "Qwen" plus 43 named authors). I did not add them: an entry nothing cites breaks the zero-orphan rule, and the decision is yours. Verify each against its source first, as for every other entry.

**4. Yelp dataset: the year looks wrong, and the download date is still open** (Run 1 item 4). `https://business.yelp.com/data/resources/open-dataset/` answers HTTP 200 today and is the address in the entry. The page gives no release year, but it does give counts: 6,990,280 reviews and 150,346 businesses. A read-only query of the local index `backend/data/processed/yelp.db` finds exactly 150,346 businesses and 6,990,280 reviews, dated 2005-02-16 to 2022-01-19. So the study used the release Yelp still distributes, and its data end in January 2022. That points to a 2022 release; nothing on the page or in the data supports `year = {2024}`. Your call; not edited. The download date cannot be recovered from the repo: `backend/data/raw/` no longer holds the files (last modified 2026-09-14), `yelp.db` is dated 2026-08-03 and the sample files beside it 2026-06-13. That suggests early June 2026 or before, but it is an inference, not a record. Put the date in the data statement (`declarations.tex`). *Update, same day:* you gave the date, 18 May 2026, and it is now in the data statement (§R2.8). The year is still open.

**5. `hoang2026eas` is still "Manuscript under review", cited 7 times** (Run 1 item 1). Unchanged. Elsevier's guide discourages unpublished results; replace the entry once the conference decision is known.

**6. `tsui2026scbench`: COLM 2026 rests on the author's word** (Run 1 item 5). The venue comes from the arXiv comment ("Accepted to COLM 2026", v3, 2026-08-02) and the PDF header read in Run 1. I found no COLM 2026 programme or proceedings entry. The only other listing was on the NeurIPS 2025 site under "Self-Correction Bench: Revealing the Self-Correction Blind Spot in LLMs"; I did not open it, so I do not know which track it was. There is no ordinal, page range or DOI to add yet.

**7. The Tier-C placeholders in §2 name real works** (Run 1 item 6). The three `\TODO` blocks (`02-related-work.tex:41, 129, 155`) are still unread, so they stay `\TODO`. The identifiers in them are right:

| Work | What exists |
|---|---|
| AgentSpec | arXiv 2503.18666; ICSE 2026, pp. 2938–2950, DOI 10.1145/3744916.3764546 (Crossref confirms; Wang, Poskitt, Sun) |
| "Reason Less, Verify More" | arXiv 2607.07405 v2, posted 2026-07-08, three authors; no venue yet |
| AgenTracer | arXiv 2509.03312 v2, six authors; no venue on the record |
| Who&When | arXiv 2505.00212 v3, comment "camera-ready"; confirm the venue from the proceedings |
| Defects4J | Crossref 10.1145/2610384.2628055; ISSTA 2014, pp. 437–440; Just, Jalali, Ernst |

When Defects4J is added it will also be "Just et al. (2014)", like `just2014mutants`. natbib should print 2014a and 2014b; check the first build after adding it, and never type the year by hand next to either.

**8. Two direct quotations of the conference paper carry no locator.** `06-discussion.tex:116` ("an accepted claim may inherit an upstream error") and `06-discussion.tex:143–145` (the temperature-zero sentence). Both match `docs/paper/main.tex` word for word. The first has no citation macro at the point of quotation ("The conference version noted that…"). The second drops the source's italic on *content*, and the source sentence continues after "outcome" with a dash, while the draft closes the quotation with a full stop. All cosmetic. Once the conference paper has page numbers, add `\citep[p.~N]{hoang2026eas}` to each.

**9. Optional, not an error.** The exact McNemar test and the percentile bootstrap are named without a citation. They are textbook procedures and JSS does not require one. Add a reference only if a reviewer asks.

Unchanged from Run 1 and not repeated: item 3 (Role Relabeling's "10 of 12" is before multiplicity correction; 9 of 12 after Holm–Bonferroni, so consider adding the qualifier), item 7 (the ICLR, COLM and PMLR entries have no DOI or page numbers; none exists) and item 8 (papers checked against abstracts rather than read in full).

**Left alone on purpose.**
- DOI links print as `doi:10.…` and point at `http://dx.doi.org/`; arXiv links use `http://arxiv.org/abs/`. Both come from the style file's fallback macros and both redirect. Elsevier restyles at proof.
- The reference list puts Chen et al. (2026) before Chen et al. (2024). The style orders same-surname first authors by initial (K. before X.), which is correct.
- The 7 BibTeX "empty pages" warnings: those proceedings have no page numbers.

### R2.5 Claim fidelity: what changed since Run 1

✓ means the source supports the sentence as written. Every row of Run 1 §5 not listed here stands: the sentences are unchanged and the source versions are the same.

| Source | What the draft says | Checked against | |
|---|---|---|---|
| Tyen et al. | New, `06-discussion.tex:50`: models that cannot find their reasoning errors can correct many of them once told where they are | The finding Run 1 verified for the §1 sentence (Table 6). The second half of the sentence, "the second model behaved that way", is the paper's own result and outside this check | ✓ |
| Tsui | §2.2 "average gap of 64.5 %"; §1 "closes most of the gap" | v3 abstract and the paper's definition of the blind spot | §2.2: see item 1. §1: ✓ (89.3 % reduction) |
| Chen et al. | §2.2 "23 to 93 points, significantly in 10 of 12" | v2 abstract: "23 to 93 percentage points, significant in 10 of 12 experimental settings" | ✓ (see Run 1 item 3) |
| Arimbur | §2.2 "most of the gain from iterated repair arrives in the first round or two" | Abstract: "Most gains concentrate in the first two rounds" | ✓ |
| Jia et al. | §2.3 "15 types of fault through prompts, intercepted outputs and message routing" | Abstract: 15 fault types; prompt modification, response rewriting, message routing | ✓ |
| `hoang2026eas`, five claims | §1: introduced the supervisor, the derivability property, and the measurements of defect incidence and instability. §6.6: 35 % of runs and 20 %; a "Recompute-and-Overwrite" subsection exists; "the enforcing arm produced one retry". §7: derivability fails for retrieval, tools and memory | `docs/paper/main.tex`, read-only: contribution list; "35 % of runs" and "20 % of runs"; the subsection; "Phase B fired a single retry across five businesses"; "a retrieval result, a tool call, … memory from an earlier run" | ✓ |
| `hoang2026eas`, workloads | `04-design.tex:64`: the first twenty, five per stratum, are the workloads of the conference study | The conference paper says "20 businesses". "Five per stratum" is a property of this paper's sampling design, not something `main.tex` states | ✓ for 20 |

### R2.6 Reference ledger

Order as in the reference list. "Checked" is what the entry was compared with on 2026-10-16. "Uses" counts cited keys.

| Key | Cited as | Entry | Checked | Uses |
|---|---|---|---|---|
| `arimbur2026` | Arimbur (2026) | arXiv 2604.10508 v1 | DataCite, arXiv | 4 |
| `basiri2016chaos` | Basiri et al. (2016) | IEEE Software 33(3), 35–41 | Crossref | 1 |
| `cemri2025mast` | Cemri et al. (2025) | NeurIPS 38, 135676–135729 | Crossref | 3 |
| `chen2026rolerelabel` | Chen et al. (2026) | arXiv 2606.05976 v2 | DataCite, arXiv | 4 |
| `chen2024selfdebug` | Chen et al. (2024) | ICLR 2024 | arXiv; ICLR page via search | 4 |
| `critic` | Gou et al. (2024) | ICLR 2024 | arXiv ("ICLR 2024") | 1 |
| `guo2024survey` | Guo et al. (2024) | IJCAI-24, 8048–8057 | Crossref | 1 |
| `hoang2026eas` | Hoang et al. (2026) | unpublished | `docs/paper/main.tex` | 7 |
| `metagpt` | Hong et al. (2024) | ICLR 2024 (oral) | arXiv; ICLR page via search | 1 |
| `huang2024cannot` | Huang et al. (2024) | ICLR 2024 | arXiv ("ICLR 2024") | 3 |
| `huang2025resilience` | Huang et al. (2025) | ICML 2025, PMLR 267, 26202–26226 | PMLR page | 1 |
| `jia2026masfire` | Jia et al. (2026) | arXiv 2602.19843 v1 | DataCite, arXiv | 1 |
| `just2014mutants` | Just et al. (2014) | FSE 2014, 654–665 | Crossref | 3 |
| `kamoi2024` | Kamoi et al. (2024) | TACL 12, 1417–1440 | Crossref | 3 |
| `leucker2009rv` | Leucker and Schallhart (2009) | JLAP 78(5), 293–303 | Crossref | 2 |
| `camel` | Li et al. (2023) | NeurIPS 36, 51991–52008 | Crossref | 1 |
| `geval` | Liu et al. (2023) | EMNLP 2023, 2511–2522 | Crossref | 1 |
| `selfrefine` | Madaan et al. (2023) | NeurIPS 36, 46534–46594 | Crossref | 1 |
| `olausson2024selfrepair` | Olausson et al. (2024) | ICLR 2024 | arXiv ("Accepted to ICLR 2024") | 5 |
| `pan2024survey` | Pan et al. (2024) | TACL 12, 484–506 | Crossref | 1 |
| `selfpreference` | Panickssery et al. (2024) | NeurIPS 37, 68772–68802 | Crossref | 1 |
| `chatdev` | Qian et al. (2024) | ACL 2024, 15174–15186 | Crossref | 1 |
| `reflexion` | Shinn et al. (2023) | NeurIPS 36, 8634–8652 | Crossref | 1 |
| `tan2026agentchaos` | Tan et al. (2026) | ASE 2026, 1780–1792 | Crossref | 3 |
| `tsui2026scbench` | Tsui (2026) | COLM 2026 | arXiv v3 comment only (item 6) | 5 |
| `tyen2024` | Tyen et al. (2024) | Findings of ACL 2024, 13894–13908 | Crossref | 3 |
| `positionbias` | Wang et al. (2024) | ACL 2024, 9440–9450 | Crossref | 1 |
| `autogen` | Wu et al. (2024) | COLM 2024 | arXiv; Microsoft Research and AG2 listings; camera-ready title read in Run 1 | 1 |
| `yelpdataset` | Yelp Inc. (2024) | dataset | URL answers HTTP 200; year unverified (item 4) | 2 |
| `zhang2023selfedit` | Zhang et al. (2023) | ACL 2023, 769–787 | Crossref | 1 |
| `mtbench` | Zheng et al. (2023) | NeurIPS 36, 46595–46623 | Crossref | 1 |

The reference list itself is generated by BibTeX from the corrected `references.bib` (`main.bbl`); it is not reproduced here.

### R2.7 Re-running

Run `/ars-citation-check` again the week you submit, and settle items 2 and 6 first: those change by themselves. The quick local part is `python check_draft.py`, which reports missing citations and dangling references. This run's throwaway scripts live in the session scratchpad, not in the repo.

### R2.8 Addendum, same day: full texts and the Yelp date

**Yelp.** You gave the download date, 18 May 2026. The data statement (`sections/declarations.tex`) now says the copy used was downloaded on 18 May 2026, and the TODO comment above the `yelpdataset` entry is resolved. The entry's `year = {2024}` is still your call (item 4). I did not put the release's counts into the paper: the draft takes every number from `RESULTS.md` or committed outputs, and these come from a one-off query.

**Full texts.** At your request, 14 free PDFs went into `../Reading List/Citation_check/`, with file names prefixed by the bib key. You added Leucker & Schallhart (the publisher's PDF) and AutoGen arXiv v2. The AutoGen file is byte-identical to `Citation_check/autogen_arXiv2308.08155.pdf`. With these, the 15 sources that Run 1 checked against abstracts only, or read without keeping a copy, were checked against their full text (text extracted with `pdftotext`, passages located by search, then read). All 15 support the sentences that cite them, so Run 1 item 8 is closed. Pages below are PDF pages; the passages are paraphrased.

| Source | What the draft says | Full text | |
|---|---|---|---|
| Leucker & Schallhart | §1: output must be checked against a specification while the pipeline runs, "and doing something about them". §2.1: runtime verification checks a running system against a specification | p. 2 (journal p. 294): defines runtime verification as checking whether a run of the system satisfies or violates a correctness property. p. 7 (p. 299): because monitoring happens during execution, faults can be acted on before they become failures | ✓. Acting on a violation is the paper's extension of runtime verification (its §5, runtime reflection). The core definition only detects |
| AutoGen (arXiv v2) | §2.1: role-specialised agents; AutoGen routes turns through a manager that is itself a language model | p. 5: the built-in GroupChatManager picks the next speaker dynamically and broadcasts its reply. p. 9: speaker selection uses a role-play prompt to the model | ✓ |
| MetaGPT | role-specialised agents | p. 1–2: standard operating procedures encoded as prompts; roles such as product manager, architect and engineer along an assembly line | ✓ |
| CAMEL | role-specialised agents | p. 1–3: a role-playing framework in which an AI user instructs an AI assistant, each with a role (a stock trader and a Python programmer in the running example) | ✓ |
| ChatDev | role-specialised agents | p. 1–3: CEO, CTO, programmer, reviewer and tester agents; a chat chain splits each phase into subtasks | ✓ |
| Guo et al. | efficient coordination of many agents is named as an open problem | p. 8: efficient coordination is listed among the challenges that grow with the number of agents | ✓ |
| G-Eval | a language model as judge can assess any output | p. 1: LLM-based metrics need no human reference, so they apply to new tasks | ✓ |
| MT-Bench | same sentence | p. 1: strong LLMs used as judges of open-ended answers | ✓ |
| Wang et al. | verdicts depend on the order in which candidates are presented | p. 2: swapping the order of the two candidates can reverse the verdict | ✓ |
| Panickssery et al. | judges favour their own generations | p. 2: GPT-3.5 Turbo, GPT-4 and Llama 2 rate their own summaries above other models' and humans' | ✓ (arXiv v1; the entry cites the NeurIPS version) |
| CRITIC | critique grounded in tools corrects better than introspection | p. 2: self-correction without external feedback helps little or hurts. The no-tool ablation trails CRITIC in the result tables | ✓ |
| Self-Refine | the model critiques and revises its own output | p. 1: one LLM drafts, gives feedback on its own draft and refines it, iteratively | ✓ |
| Reflexion | a verbal reflection on failure is carried into later attempts | p. 1: the agent writes a reflection on the task feedback and keeps it in an episodic memory for later trials | ✓ |
| Pan et al. (TACL) | own feedback is constrained by the model's limitations; recent work draws feedback from trained models, code interpreters and search engines | "Models/Tools as Feedback" (p. 9): self-generated feedback is limited by the model's own weaknesses, so recent work turns to external tools, naming those three | ✓ |
| Basiri et al. (arXiv) | chaos engineering of production services | p. 1–2: chaos engineering experiments on a live distributed system to gain confidence that it survives turbulent production conditions; Netflix injects failures into its production system | ✓ (arXiv preprint; the entry cites IEEE Software) |

**AutoGen's title.** arXiv v2 ends "…Multi-Agent Conversation". The entry ends "Conversations", from the COLM camera-ready that Run 1 read. The COLM record on OpenReview (`BAakY1hNKS`, as indexed by papers.cool) also has the plural. No change.

**Two PDFs sit untracked inside the repo.** `docs/paper/journal/1-s2.0-S1567832608000775-main.pdf` (Elsevier's PDF) and `docs/paper/journal/2308.08155v2.pdf` are not covered by `.gitignore`, so `git add .` would commit them. Keep publisher PDFs out of git: move the first to `../Reading List/`, and delete the second, which duplicates `Citation_check/autogen_arXiv2308.08155.pdf`.

---

## Run 1 — 2026-10-09 (archived; unchanged apart from heading levels)

**Run:** 2026-10-09, `/ars-citation-check` (academic-paper skill, `citation-check` mode).
**Scope:** `docs/paper/journal/` — every `\cite*` in `main.tex` and `sections/`, against `references.bib`.
**Target style:** Elsevier author–year (`elsarticle-harv.bst`, natbib). JSS accepts any consistent style at submission and applies its own at proof.
**Not touched:** `docs/paper/main.tex` (conference paper #1, under review).

The build is clean after the fixes: 46 pages, no undefined citations, no overfull boxes. BibTeX prints 7 "empty pages" warnings, for the ICLR and COLM entries. Those proceedings have no page numbers.

### 1. Summary

| Metric | Before | After |
|---|---|---|
| In-text citation uses | 67 (38 `\citep`, 29 `\citet`) | 67 |
| Distinct sources cited | 31 | 31 |
| Entries in `references.bib` | 40 | 31 |
| Cited but undefined | 0 | 0 |
| Defined but never cited | 9 | 0 (removed) |
| Multi-key cites out of alphabetical order | 3 | 0 |
| Cited entries with a DOI | 6 | 21 (18 Crossref DOIs, each re-fetched and compared with the revised entry; 3 arXiv DOIs, which resolve in DataCite) |
| Cited entries still without a DOI | 25 | 10 (7 ICLR/COLM papers, the PMLR paper, the dataset, the unpublished manuscript; none of these has one) |
| Reference entries that cited a preprint although a published version exists | 4 | 0 |
| Entries whose title or author list differed between the cited version and the version of record | 4 (`pan2024survey`, `reflexion`, `positionbias`, `autogen`) | 0 |
| Claims attributed to a source that the source does not support | 3 | 0 (rewritten) |
| Self-citation | 10.4 % of uses, 3.2 % of sources | unchanged (limit 15 %) |
| Sources from 2021 or later | 90 % (28/31) | unchanged |
| Sources over 10 years old | 3 | unchanged; all foundational (runtime verification 2009, mutants vs real faults 2014, chaos engineering 2016) |
| Retraction or correction notices | none found | none found |

### 2. How it was checked

| Check | Source |
|---|---|
| Title, authors, year, venue, volume, pages and DOI of the 18 entries that have a Crossref DOI | Crossref REST API, fetched by DOI; a second pass after the edits compared the revised `.bib` against fresh records (title, pages, year, DOI, authors: all agree) |
| arXiv IDs, titles, author lists, posting dates, "accepted at" comments | arXiv API (17 IDs by `id_list`, the rest by title search) |
| Published versions of preprints | Crossref title search, the arXiv record's `journal_ref`/comment fields, web search |
| ICML 2025 pages and author names | `proceedings.mlr.press/v267/huang25ay` |
| MetaGPT at ICLR 2024 | ICLR 2024 proceedings page (via search) |
| AutoGen at COLM 2024 | camera-ready PDF hosted by Microsoft Research ("Published as a conference paper at COLM 2024") |
| Pan et al. (TACL) text | ACL Anthology PDF `2024.tacl-1.27` |
| Claim fidelity | Text of 17 papers: the 14 PDFs in `../Reading List` plus Guo et al., the AutoGen camera-ready and the TACL version of Pan et al., all searched for the figures and phrases the draft attributes to them; abstracts for the rest |
| Quotations of the conference paper | `docs/paper/main.tex`, read-only |
| Retraction screening | Crossref `update-to`/`updated-by` fields on all 18 records: no notice on any |

**Not available.** DBLP and OpenReview put up bot checks, and Semantic Scholar rate-limited me. I did not try to get around any of them. Their roles were covered by the sources above.

### 3. Corrections made

#### 3.1 `references.bib`

| Key | Was | Now | Evidence |
|---|---|---|---|
| `positionbias` | arXiv preprint, 10 authors | **ACL 2024**, 11 authors (adds Lingpeng Kong), pp. 9440–9450, DOI | Crossref `10.18653/v1/2024.acl-long.511` |
| `selfpreference` | arXiv preprint | **NeurIPS 2024**, pp. 68772–68802, DOI | Crossref `10.52202/079017-2197` |
| `guo2024survey` | arXiv preprint | **IJCAI 2024**, pp. 8048–8057, DOI | Crossref `10.24963/ijcai.2024/890` |
| `autogen` | arXiv preprint, 2023 | **COLM 2024** (the in-text year changes from 2023 to 2024). The camera-ready title ends "Conversations" | camera-ready PDF header |
| `pan2024survey` | Title "…Diverse *Self-Correction* Strategies" (the arXiv title), no volume or pages | TACL title "…Diverse *Automated Correction* Strategies", vol. 12, pp. 484–506, DOI | Crossref `10.1162/tacl_a_00660` |
| `reflexion` | 6 authors (arXiv v4 list) | **5 authors** as in the NeurIPS 2023 proceedings (Edward Berman is on the arXiv version only), pp. 8634–8652, DOI | Crossref `10.52202/075280-0377` |
| `leucker2009rv`, `basiri2016chaos` | "metadata from memory" warnings | verified: title, authors, volume, issue, pages, DOI all correct | Crossref |
| `just2014mutants` | no pages | pp. 654–665 | Crossref |
| `zhang2023selfedit` | no pages | pp. 769–787; booktitle completed with "(Volume 1: Long Papers)" | Crossref |
| `tan2026agentchaos` | no pages | pp. 1780–1792 | Crossref |
| `huang2025resilience` | no pages; author "Jen-tse" | pp. 26202–26226, PMLR; "Jen-Tse" | PMLR page |
| `chatdev`, `geval`, `tyen2024`, `camel`, `selfrefine`, `mtbench`, `cemri2025mast` | no DOI (some no pages) | DOI and pages added | Crossref |
| `chen2026rolerelabel`, `arimbur2026`, `jia2026masfire` | `arXiv preprint arXiv:…` in the title field, no DOI | `arXiv preprint` plus the arXiv DOI, as the JSS guide asks (the three DOIs resolve in DataCite) | JSS guide, "Preprint references" |
| ICLR/COLM entries (`metagpt`, `critic`, `olausson2024selfrepair`, `huang2024cannot`, `chen2024selfdebug`, `tsui2026scbench`) | `note = {arXiv:…}` printed as "ArXiv:…"; two ICLR spellings | `eprint` field (prints "arXiv:…" as a link); one spelling for ICLR 2024 | `.bbl` |
| `guo2024survey`, `positionbias`, `selfpreference`, `autogen` (`@article` with `journal = arXiv…`) | rendered with a stray space before the full stop | proper `@inproceedings` | `.bbl` |
| NeurIPS entries | `volume` field, which this style does not print | volume folded into the booktitle ("…Systems 36") | `.bbl` |
| `yelpdataset` | `yelp.com/dataset`, which now redirects; no access date | `business.yelp.com/data/resources/open-dataset/`, "Accessed 9 October 2026" | HTTP check, JSS guide on web references |
| 9 uncited entries | `semeval2014`, `simmering2023`, `wu2024absa`, `niimi2024`, `cot`, `react`, `malik2024`, `sokolova2009`, `zhang2015` (the conference paper's sentiment-analysis and reasoning references) | removed. They are still in `../references.bib` | zero-orphan rule |

#### 3.2 Prose

| Where | Was | Now | Why |
|---|---|---|---|
| §2.1, first paragraph | "Multi-agent frameworks coordinate their agents through a manager that is itself a language model \[AutoGen, MetaGPT, CAMEL, ChatDev]" | "…divide a task among role-specialised language-model agents \[…], and some, AutoGen among them, route turns through a manager that is itself a language model" | Only AutoGen has an LLM-driven manager (`GroupChatManager`, speaker chosen by a role-play prompt). MetaGPT uses SOPs on an assembly line, CAMEL a role-play pair, ChatDev a chat chain |
| §2.1 | "Coordination and control are named as open problems" \[Guo et al.] | "Efficient coordination of many agents is named as an open problem" | The survey names "efficient agent coordination" among the complexities of scaling up. It does not name control |
| §2.2 | "Pan et al. conclude that the quality of the feedback, more than the number of rounds, determines whether correction helps" | "…observe that when a model produces its own feedback, the quality of that feedback is constrained by the model's limitations, and that recent work therefore draws feedback from external tools such as trained models, code interpreters and search engines" | The TACL text has the second statement and no version of the first |
| §2.3 | Huang et al. 2025: "the two injection methods are not exchangeable" | "Corrupting a profile also degrades performance more than corrupting messages, so the two injection methods are not interchangeable" | The paper's finding is a difference in severity (AutoTransform −12.45 vs AutoInject −8.83 averaged) |
| §2.3 | AgentChaos: "finds injection position decisive for pipeline architectures" | "finds that injection position matters most for pipeline architectures" | The paper's wording |
| §6.6, item 1 | A quotation of the conference paper in quotation marks that was not verbatim (it dropped "that" and ", not the act of retrying,") | verbatim, from `main.tex` lines 337–339 | A quotation has to be exact |
| §2.1 and §6.2 | Three multi-key cites out of order | alphabetical, as Elsevier's guide specifies and as the reference list is ordered | `\citep{metagpt,camel,chatdev,autogen}`, `\citep{geval,mtbench}`, `\citep{chen2024selfdebug,chen2026rolerelabel,tsui2026scbench}` |

### 4. Flagged for review (not changed)

| # | Item | Suggested action |
|---|---|---|
| 1 | **`hoang2026eas`, the conference paper, is cited 7 times as "Manuscript under review".** Elsevier's guide discourages references to unpublished results and says that, if kept, the date should read "unpublished results". | Part of author decision 2 (extension declaration and timing). Once the conference decision is known, replace with the published entry. Until then keep it and say so in the cover letter. |
| 2 | **Three preprints are still unpublished** (MAS-FIRE `2602.19843`, Role Relabeling `2606.05976` v2, Arimbur `2604.10508`). I found no published version on 2026-10-09. | Re-check the week you submit. If one has appeared, switch to the published version, as the JSS guide asks. |
| 3 | **Role Relabeling: "significantly in 10 of 12 model–domain combinations"** is the abstract's figure, before multiplicity correction. The paper also reports 9 of 12 after Holm–Bonferroni. | Consider adding "(9 of 12 after Holm–Bonferroni correction)". |
| 4 | **Yelp dataset:** the reference now has a page-access date, but JSS also wants the date the data were downloaded, and the dataset page gives no version or year (the entry says 2024). | Put the download date in the data statement; confirm the year. |
| 5 | **COLM 2026 (`tsui2026scbench`)** has no proceedings ordinal, pages or DOI yet. | Add them when the proceedings appear. |
| 6 | **Tier-C placeholders in §2** (AgentSpec, "Reason Less, Verify More", AgenTracer, Who&When, Defects4J). They are `\TODO` blocks, not citations, because the papers were not read. | Read, then cite, as the README already says. |
| 7 | **ICLR/COLM/PMLR entries have no DOI** and no page numbers (BibTeX "empty pages" ×7). None exists. | Nothing to do. Elsevier may ask at proof. |
| 8 | **Not read in full:** Leucker and Schallhart 2009 and Basiri et al. 2016 (title, authors, venue and pages verified; the claims attached to them are a textbook definition and a title-level description); MT-Bench, G-Eval, Self-Refine, Reflexion, CRITIC, CAMEL, MetaGPT, ChatDev and the two evaluator-bias papers (claims checked against abstracts only). | The claims attached to them are one-line characterisations that the abstracts support. |

### 5. Claim fidelity

✓ means the source supports the sentence as written (after the edits in §3.2).

| Source | What the draft says | Checked against | |
|---|---|---|---|
| Olausson et al. | human vs model explanations: 33.3 % → 52.6 % on 40 failing programs; repairs must be compared with i.i.d. resampling at equal budget | PDF, Table 1; the 20 tasks are 14/3/3 intro/interview/competition | ✓ |
| Tyen et al. | given the error location, backtracking corrects 18–44 pp of incorrect traces; a random location about halves the gain | PDF, Table 6 (+18.04 to +43.92 vs +5.16 to +21.57) | ✓ |
| Chen et al. (Self-Debug) | least informative feedback keeps most of the gain; without execution it can fall below baseline | PDF, Tables 2–3 (MBPP/Codex 61.4 → 57.6) | ✓ |
| Tsui | 64.5 % blind spot over 14 models; "Wait" closes 89.3 % | PDF | ✓ |
| Chen et al. 2026 | 23–93 points; significant in 10 of 12 combinations | PDF (v2) | ✓ (see item 3) |
| Huang et al. 2024 | no gain without oracle labels; feedback prompts can carry task information | PDF | ✓ |
| Kamoi et al. | external verifier is a fair setting; feedback generation is the bottleneck; analyse feedback quality | PDF | ✓ |
| Zhang et al. (Self-Edit) | a second editing round can hurt | PDF (hurts on APPS-test, slight gain on APPS-dev) | ✓ |
| Arimbur | most gain in the first two rounds; run-to-run variation on a hosted API | PDF | ✓ |
| Cemri et al. | 14 modes in 3 categories; verifiers perform only superficial checks; failures occur in successful runs too | PDF (taxonomy, the FM-3 discussion, Appendix J.1) | ✓ |
| Huang et al. 2025 | linear degrades most, hierarchical least; method severity differs | PDF (−23.7 / −10.5 / −5.5) | ✓ (edited) |
| Jia et al. (MAS-FIRE) | 15 fault types; prompt, response and routing injection; detection vs resolution vs success | PDF | ✓ |
| Tan et al. (AgentChaos) | 65 configurations; untriggered tasks filtered; neither diagnosis kind exceeds 56 %; position matters most for pipelines; silent failures 21.8–65.7 % | PDF | ✓ (edited) |
| Just et al. | 357 faults; 73 % coupled; mutant detection correlates with fault detection beyond coverage; repair left open | PDF | ✓ |
| Pan et al. | feedback quality | TACL PDF | ✓ only after the rewrite |
| Guo et al. | coordination | survey text | ✓ only after the rewrite |
| AutoGen, MetaGPT, CAMEL, ChatDev | role-specialised agents; an LLM manager in AutoGen | AutoGen PDF; the other abstracts | ✓ only after the rewrite |
| `hoang2026eas` | derivability fails for retrieval, tools, memory; quotation of the temperature-0 sentence; "an accepted claim may inherit an upstream error" | `main.tex` lines 199–222, 337–339, 801, 810 | ✓ |

### 6. Finding about the conference paper (`docs/paper/main.tex`, not edited)

The journal draft inherited three statements from the conference paper's related work (lines 126–148), and the same checks apply there:

1. Guo et al. "name coordination and control as open problems". Only coordination is supported.
2. "A coordinating manager is standard — but what it decides on is, in every case, a language model's judgement, because the manager is itself an agent." This generalises from AutoGen to MetaGPT, CAMEL and ChatDev, which do not use a manager of that kind.
3. "Pan et al. conclude that feedback quality, not the number of rounds, determines whether self-correction helps." The TACL text does not say this.

These are for the conference version's next revision opportunity. Nothing here affects its results.

### 7. Re-running

The checks used throwaway scripts that live in the session scratchpad, not in the repo. To redo the pass before submission, run `/ars-citation-check` again. The quick local part is `python check_draft.py`, which reports missing citations and dangling references.
