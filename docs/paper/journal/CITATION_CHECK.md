# Citation check — JSS draft

**Run:** 2026-10-09, `/ars-citation-check` (academic-paper skill, `citation-check` mode).
**Scope:** `docs/paper/journal/` — every `\cite*` in `main.tex` and `sections/`, against `references.bib`.
**Target style:** Elsevier author–year (`elsarticle-harv.bst`, natbib). JSS accepts any consistent style at submission and applies its own at proof.
**Not touched:** `docs/paper/main.tex` (conference paper #1, under review).

The build is clean after the fixes: 46 pages, no undefined citations, no overfull boxes. BibTeX prints 7 "empty pages" warnings, for the ICLR and COLM entries. Those proceedings have no page numbers.

## 1. Summary

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

## 2. How it was checked

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

## 3. Corrections made

### 3.1 `references.bib`

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

### 3.2 Prose

| Where | Was | Now | Why |
|---|---|---|---|
| §2.1, first paragraph | "Multi-agent frameworks coordinate their agents through a manager that is itself a language model \[AutoGen, MetaGPT, CAMEL, ChatDev]" | "…divide a task among role-specialised language-model agents \[…], and some, AutoGen among them, route turns through a manager that is itself a language model" | Only AutoGen has an LLM-driven manager (`GroupChatManager`, speaker chosen by a role-play prompt). MetaGPT uses SOPs on an assembly line, CAMEL a role-play pair, ChatDev a chat chain |
| §2.1 | "Coordination and control are named as open problems" \[Guo et al.] | "Efficient coordination of many agents is named as an open problem" | The survey names "efficient agent coordination" among the complexities of scaling up. It does not name control |
| §2.2 | "Pan et al. conclude that the quality of the feedback, more than the number of rounds, determines whether correction helps" | "…observe that when a model produces its own feedback, the quality of that feedback is constrained by the model's limitations, and that recent work therefore draws feedback from external tools such as trained models, code interpreters and search engines" | The TACL text has the second statement and no version of the first |
| §2.3 | Huang et al. 2025: "the two injection methods are not exchangeable" | "Corrupting a profile also degrades performance more than corrupting messages, so the two injection methods are not interchangeable" | The paper's finding is a difference in severity (AutoTransform −12.45 vs AutoInject −8.83 averaged) |
| §2.3 | AgentChaos: "finds injection position decisive for pipeline architectures" | "finds that injection position matters most for pipeline architectures" | The paper's wording |
| §6.6, item 1 | A quotation of the conference paper in quotation marks that was not verbatim (it dropped "that" and ", not the act of retrying,") | verbatim, from `main.tex` lines 337–339 | A quotation has to be exact |
| §2.1 and §6.2 | Three multi-key cites out of order | alphabetical, as Elsevier's guide specifies and as the reference list is ordered | `\citep{metagpt,camel,chatdev,autogen}`, `\citep{geval,mtbench}`, `\citep{chen2024selfdebug,chen2026rolerelabel,tsui2026scbench}` |

## 4. Flagged for review (not changed)

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

## 5. Claim fidelity

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

## 6. Finding about the conference paper (`docs/paper/main.tex`, not edited)

The journal draft inherited three statements from the conference paper's related work (lines 126–148), and the same checks apply there:

1. Guo et al. "name coordination and control as open problems". Only coordination is supported.
2. "A coordinating manager is standard — but what it decides on is, in every case, a language model's judgement, because the manager is itself an agent." This generalises from AutoGen to MetaGPT, CAMEL and ChatDev, which do not use a manager of that kind.
3. "Pan et al. conclude that feedback quality, not the number of rounds, determines whether self-correction helps." The TACL text does not say this.

These are for the conference version's next revision opportunity. Nothing here affects its results.

## 7. Re-running

The checks used throwaway scripts that live in the session scratchpad, not in the repo. To redo the pass before submission, run `/ars-citation-check` again. The quick local part is `python check_draft.py`, which reports missing citations and dangling references.
