# Defect-bank audit (D13) — instructions for the two raters

Built 2026-08-26 by `scripts/analysis/rater_sheet.py --build`, seed 20260826.
31 items, order randomised. **Do not rebuild this sheet** — the item order and
the blinding assignment are fixed, and rebuilding after anyone has started
invalidates their sheet.

## Why this exists

The defect bank is defined by the detector that found it, so validating it with
that same detector proves nothing. This audit breaks the circularity by
splitting the construct in two:

- **Groundedness** — is the fact the check reported actually true of the output?
  Machine-checkable, already verified exhaustively. **Not what you are rating.**
- **Meaningfulness** — would a competent analyst call this an error? Judgement.
  **This is what you are rating**, and it needs two independent humans.

## What to do

1. Read `rating_sheet.md`. The rubric is at the top; read it before item I01.
2. Fill in **your own** CSV — rater A uses `rating_a.csv`, rater B uses
   `rating_b.csv`. One letter per item in the `rating` column: `E`, `T` or `U`.
3. Add a note whenever you hesitate. The letters make disagreements countable;
   the notes make them useful.
4. **Do not discuss any item with the other rater** until both CSVs are filled
   and saved.
5. **Do not open `key.json`.** It records which items are real defects and which
   were injected. Reading it ends the blinding and voids the audit.

Roughly an hour. Rate in the order given — it is already randomised.

## Use U sparingly

`U` items are excluded from the agreement statistic entirely. With only 31
items, a high U rate leaves too few pairs to say anything: a dry run with 18 U
items returned a 95% CI of [0.00, 1.00], which is no answer at all. If you can
form a judgement from what is shown, record it and note your reservation
instead. A high U rate is itself a finding about the instrument — but it is a
finding bought at the cost of the result.

## When both sheets are back

From `backend/`:

```
venv/Scripts/python.exe scripts/analysis/rater_sheet.py \
    --score out_study/audit --a out_study/audit/rating_a.csv \
    --b out_study/audit/rating_b.csv
```

This reports raw agreement, Cohen's kappa with a bootstrap CI, every
disagreement with both notes, and — only then — the unblinded tier breakdown.

⚠ **Kappa is undefined, not 1.0, if both raters use a single category.** That is
deliberate: a table with one occupied cell carries no information. Report the CI,
or report raw agreement and n.

## Sequencing — this is the one hard constraint in the study

**This rating must be finished before any core trial results exist.** Once
results are on disk, nobody in the project is blind, and the audit cannot be
redone. It does not block dump collection or the live smoke test; it blocks
nothing except being left too late.
