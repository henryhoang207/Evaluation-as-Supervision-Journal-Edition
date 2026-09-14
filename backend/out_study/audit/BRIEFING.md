# How to brief rater 2

You are rater 1. This file is for you, not for him. Send him the message in §2
and the two files in §1 — nothing else.

## 1. What to send, and what not to

**Send exactly two files:**

- `rating_sheet.md`
- `rating_b.csv` (his sheet — you fill in `rating_a.csv`)

**Do not send, show, or describe:**

- `key.json` — it is the answer sheet.
- `README.md` or this file — they discuss kappa, injection and sample size.
- Anything from the repository: the scripts, the plan, the paper. He should not
  know the pipeline has a supervisor, what its checks look for, or that this
  audit exists to validate a defect bank.

He needs no software, no repository access and no dataset. The sheet is
self-contained; a text editor and a spreadsheet are enough.

## 2. The message — send this roughly as written

> I need about an hour of independent judgement on a set of 31 short items, for
> a study I am writing up.
>
> Each item shows something an automated text-analysis pipeline wrote, the
> material it was given to work from, and a factual discrepancy between the two
> that has already been verified — you do not need to check it, and you do not
> need the original source material.
>
> The only question is whether that discrepancy amounts to a real error, or is
> a technicality that a careful human reviewer would let stand. The sheet
> explains the three answers at the top. Read that part before item 1.
>
> Four things matter more than speed:
>
> 1. Work alone. Do not ask me what I think about any item, and I will not tell
>    you, until both our sheets are finished. That independence is the whole
>    point of the exercise — if we converge by talking, the number I compute
>    from it is worthless.
> 2. Put a short note whenever you hesitate, especially when you nearly chose
>    the other letter. The disagreements are the interesting part, and the notes
>    are what make them interpretable.
> 3. Use "cannot judge" sparingly. Items answered that way get dropped, and
>    there are only 31 to begin with. If you can form a view from what is shown,
>    record it and put your reservation in the note instead.
> 4. There is no right answer I am hoping for, and no proportion you should be
>    aiming for. Some of these may well be technicalities. If you think most of
>    them are, say so — that is a result, not a failure.
>
> Fill in the `rating` column of the CSV — one letter per row, `E`, `T` or `U`
> — and send it back.

## 3. Your own discipline as rater 1

- **Rate your own sheet without discussing anything with him**, from the same
  `rating_sheet.md` he has. You wrote the pipeline, so you cannot be blind to
  the system — but you can be blind to which items are real and which were
  injected, and that is the blinding this audit actually needs.
- **Do not open `key.json`** until both CSVs are filled and saved. Not to check
  one item, not to settle a doubt.
- **If he asks a question mid-rating, answer only about format** — how to record
  an answer, what a column means. If he asks anything about an item, about what
  a stage was supposed to do, or whether he is reading it right, the answer is
  "use your judgement and put it in the note". Answering it makes your judgement
  part of his rating, and the two sheets stop being independent.

## 4. When both sheets are back

From `backend/`:

```
venv/Scripts/python.exe scripts/analysis/rater_sheet.py \
    --score out_study/audit --a out_study/audit/rating_a.csv \
    --b out_study/audit/rating_b.csv
```

Then work through the disagreements together, with the notes, and record how
each was resolved — the resolution is reportable, and reviewers ask for it.

⚠ **Do all of this before any core trial results exist.** Once they do, neither
of you is blind, and the audit cannot be run again.
