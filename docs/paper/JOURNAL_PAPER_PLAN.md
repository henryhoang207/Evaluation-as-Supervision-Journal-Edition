# Journal paper — writing plan

**Written 2026-10-08** for the next session. **No journal text exists yet.** The
numbers come from **`RESULTS.md`** and nowhere else; the design and every
deviation from it from **`PREREGISTRATION.md`** (frozen at tag `prereg-freeze`,
amendments §0.1 A1–A9, A10 to come with C7).

⛔ **Do not edit `docs/paper/main.tex`.** It is conference paper #1, under
review. The journal paper is a new document.

---

## 1. Decisions taken

| Decision | State |
|---|---|
| Vehicle | ✅ **Journal only** — author, 2026-10-08. No conference split: the pre-registered split rule was not met, and `PUBLICATION_STRATEGY.md`'s null branch says journal, not split |
| Venue | ✅ **JSS (Journal of Systems and Software, Elsevier), regular paper** — **author, 2026-10-08**, replacing EMSE. JSS's scope lists "Software Engineering for AI systems" and explicitly welcomes negative results; single-anonymised review; Elsevier `elsarticle` template, author–year references. **Open access is free for a Swinburne-affiliated corresponding author** under the CAUL–Elsevier agreement (hybrid journal, APC waived, uncapped; articles accepted 2026-01-01 → 2029-12-31; corresponding author must submit from an institutional email — confirmed in CAUL's title finder 2026-10-08). Fallback order: IST (Elsevier, also APC-waived), then EMSE (Springer, APC-waived under the CAUL–Springer agreement) |
| Second model | C7 is the last experiment (`C7_RUNBOOK.md`). The paper should **wait for it** — D15 (one model) is the main threat to a null result |

## 2. Author decisions still open (each blocks a specific part)

1. **Authorship (D5).** Conference #1 lists five authors (Hoang, Pham, Tran,
   Nguyen, and the supervisor Dr. Nguyen Manh Toan). Decide the journal author
   list before the title page.
2. **Extension declaration and timing.** Declare the conference version and
   cite it (≈ 30 % new material is comfortably met — the whole repair study is
   new). JSS's submission declaration requires that the article is "not under
   consideration for publication elsewhere"; the journal paper is a different
   article, but its system description overlaps conference #1, which is still
   under review. Decide whether to submit before or after conference #1's
   decision; `PUBLICATION_STRATEGY.md` §6 covers the dual-submission
   constraints. The draft carries a placeholder declaration in §1.
3. **Conference #1 implications.** Two findings bear on the supervisor that
   paper describes (see §6 below). Q2 (2026-09-14) set the precedent: the
   matcher defect is a **journal finding**, not a note to the chairs. Confirm
   the same treatment for the Tier-1 and downstream findings.
4. **Data availability.** The repository
   (`github.com/Hahhahahaadsa/Evaluation-as-Supervision-Journal-Edition`) —
   public at submission, or an archived snapshot (e.g. Zenodo) of tag
   `prereg-freeze` plus the result commits?

## 3. Template and build

- JSS uses Elsevier's **`elsarticle`** class with author–year references
  (`elsarticle-harv.bst`). **Both are installed in MiKTeX, and so is `natbib`**
  (checked 2026-10-08 with `kpsewhich`; this section's earlier "natbib is not
  installed" was true for the EMSE plan's environment and is no longer).
- JSS requirements (guide for authors, read 2026-10-08): abstract ≤ 250 words;
  1–7 keywords; **highlights**, 3–5 bullets of ≤ 85 characters, as a separate
  file named with "highlights"; full papers encouraged under 36 pages
  single-column; numbered sections; CRediT statement; data statement (research
  data Option C: deposit and cite, or explain); declaration of competing
  interests; funding statement; and a **"Declaration of generative AI and
  AI-assisted technologies in the manuscript preparation process"** section
  before the references whenever AI tools were used — this draft was written
  with Claude Code, so the section is mandatory.
- Build: `latexmk -pdf main.tex` in `docs/paper/journal/` (MiKTeX `pdflatex`,
  `bibtex`, `latexmk` are present).
- Put the paper in **`docs/paper/journal/`**: `main.tex`, one file per section,
  and its own `references.bib` started as a copy of the conference one.

## 4. Working titles (pick one)

- *Does Measured Feedback Repair LLM Pipeline Defects? A Pre-registered
  Fault-Injection Study of Deterministic Runtime Supervision*
- *Evaluation as Supervision, Revisited: Repair, Propagation and the Limits of
  Local Verification in a Multi-Agent LLM Pipeline*

## 5. Research questions (draft)

| RQ | Question | Evidence (`RESULTS.md`) |
|---|---|---|
| RQ1 | Does the **content** of supervisor feedback (measured facts vs a generic rejection) change whether a retried stage repairs an injected defect? *Confirmatory.* | §2: null at ceiling, +0.7 pp [−2.9, +4.3], p = 0.75; robust to all O5 matchers |
| RQ2 | **Why** does repair succeed — what do the artifact (placement), sampling (temperature), defect extent (severity) and constraint disclosure (C1) contribute? | §4–5: copy-and-correct; placement, warm, severity, C1 |
| RQ3 | What does the **production retry** do on **real**, production-caught defects, and how do they differ from injected ones? | §5: Tier-1 (A1 28.2 % accepted), defect origin (98.5 % vs 28.2 %) |
| RQ4 | Does stage-level repair become **pipeline-level** improvement? | §5: downstream propagation (silent propagation; partial restoration; the report check rewards propagation) |
| RQ5 | What does **recompute-and-overwrite** buy over a retry? | §5: D19 — a cost optimisation, not a correctness decision |
| (RQ6) | Do the answers hold on a **second model**? | C7 — pending |

## 6. What the paper must reconcile with conference #1

These are the places where the journal results revise claims in `main.tex`;
each needs an explicit sentence, not silence:

1. **"At temperature zero an unchanged prompt returns an unchanged answer, so
   the content of that feedback, not the act of retrying, is what can change the
   outcome"** (conference §4.4). The journal shows both halves need qualifying:
   temperature 0 is not reproducible across sessions on a hosted API (C1 drift:
   83 % byte-identical; 27 % of core A1 cells give two distinct outputs), and with
   the artifact in view the *content* of the feedback does not matter (A1 ≈ A2).
2. **Defect incidence (35 %) and instability (20 %).** The D13 audit found 9 of
   the 11 Tier-1 defects to be checker false positives (paraphrase misses of the
   difflib trace matcher, single-character id corruptions with the real evidence
   present). C6 now gives the rates: the production trace matcher flags 5.0 % of
   grounded recommendation issues. State the incidence with this correction.
3. **Recompute-and-overwrite** (conference §4.5) asserted a principle with no
   counterfactual; D19 now measures it.
4. The conference's own retry-repair result (`main.tex` section *"Does
   Feedback-Injected Retry Repair the Defect?"*) — read it and reconcile it with
   the Tier-1 replay before writing RQ3.

## 7. Section outline and sources

| § | Section | Source | Key content |
|---|---|---|---|
| 1 | Introduction | `RESULTS.md` §2, this plan §5 | runtime supervision of LLM pipelines; the open question (does measured feedback repair?); RQs; contributions; extension declaration |
| 2 | Background and related work | `JOURNAL_PLAN.md` §2 reading tables; extractions in `../Reading List/Tier_A`, `Tier_B` (outside the repo) | self-correction (Olausson, Huang, Self-Debug, SC-Bench, Kamoi), fault injection in multi-agent systems (MAS-FIRE, AgentChaos), failure taxonomies (MAST), mutants vs real faults (Just et al.), runtime verification |
| 3 | The system and its supervisor | `main.tex` §3–4 (condense and cite) | staged pipeline, derivability, measure/decide, the checks, retry feedback, overwrite |
| 4 | Study design | `PREREGISTRATION.md` §1–§8, §0.1 A1–A9 | estimand; operators O1–O8 and the D20 gates; arms A0–A3; placements P0–P3; outcome taxonomy and scoring (D18, D22, D24); confirmatory test; exploratory cells; execution (model, temperature 0, sessions, fallback off); exclusions; **a deviations table** listing A1–A9 and the disclosed interim look |
| 5 | Results | `RESULTS.md` §1–§7 | RQ1–RQ5, then calibration (C6, coupling) |
| 6 | Discussion | `RESULTS.md` §4, §5, §7 | copy-and-correct; repair ≠ pipeline improvement; local verification rewards fidelity to upstream; matcher false positives dominate the production retry; overwrite as a cost optimisation; design recommendations for runtime supervisors |
| 7 | Threats to validity | `JOURNAL_PLAN.md` D14–D16, §15; `PREREGISTRATION.md` §9 | construct (injected defects at ceiling; scoring; matcher), internal (serving drift, sessions, interim look, amendments filed after earlier results), external (one model until C7, one domain, one pipeline), conclusion (a null with a CI; many exploratory intervals) |
| 8 | Conclusion | — | — |
| — | Data availability, declarations | `RESULTS.md` §1 (commits), tag `prereg-freeze` | conference-version declaration; LLM-use disclosure (Springer policy) — `/ars-disclosure` can draft it |

## 8. Tables and figures

| # | Content | Source |
|---|---|---|
| T1 | Cells run: defects, trials, usable, commit | `RESULTS.md` §1 |
| T2 | Confirmatory result, with/without multi-attempt, O5 sensitivity | `out_study/T2/analysis.json`, `T2/o5_sensitivity.json` |
| T3 | §5 predictions vs results | `RESULTS.md` §3 |
| T4 | Mechanism: placement, warm, severity, C1 | `T2P`, `T2W`, `T2S`, `T2C1` `analysis.json` |
| T5 | Tier-1 replay and defect origin | `T1/analysis.json`, `out_study/secondary_extra.json` |
| T6 | Downstream propagation (E1–E3), the O5 cross-tab, coupling | `T2D/analysis.json` |
| F1 | Pipeline and supervisor | `Evaluation_as_Supervision.drawio` (conference figure; redraw if reused) |
| F2 | Forest plot of every contrast with its CI | the `analysis.json` files |
| F3 | C6 detection curves (frequency step; trace matcher on grounded vs foreign) | `secondary_extra.json` |

Every number is regenerated by `backend/scripts/analysis/repair_analysis.py
--cell <cell>` and `secondary_extra.py` (no API calls).

## 9. References

`docs/paper/references.bib` holds only the conference keys (autogen, metagpt,
camel, chatdev, guo2024survey, selfrefine, reflexion, critic, pan2024survey,
mtbench, geval, positionbias, selfpreference, semeval2014, simmering2023,
wu2024absa, niimi2024, cot, react, malik2024, sokolova2009, zhang2015,
yelpdataset). The journal needs the repair and fault-injection literature in
`JOURNAL_PLAN.md` §2 (identifiers recorded there). ⚠ The plan records citation
metadata going wrong **three times** from second-hand sourcing: take metadata
from the papers themselves, and run **`/ars-citation-check`** before submission.

## 10. Suggested order for the writing session

✅ **2026-10-09: steps 2–4 are done — a full first draft for JSS is in
`journal/`** (see `journal/README.md` for the placeholder inventory and the
pre-submission checklist). Still open: step 1's author decisions, step 5, and
step 6 (C7).

1. Settle §2's author decisions 1 and 2; download the template (§3).
2. Outline (`/ars-outline` can produce an outline with an evidence map).
3. Draft **Study design** and **Results** first — they are fully determined by
   `PREREGISTRATION.md` and `RESULTS.md`.
4. Then Introduction and Discussion; then Related work after the literature pass;
   then Threats.
5. Citation check, an internal review pass (`/ars-reviewer`), the disclosure.
6. Fold in C7 when it lands (RQ6, T2-style table, threats update).
