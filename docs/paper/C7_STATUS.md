# C7 completed and verified — 2026-10-12

**All planned experiments are complete.** C7 collected **930/930 trials** on
**138 eligible defects** in about **4 h 34 min**, entirely on this PC, with no
cloud calls or API fees. **929 trials are usable**; one oversized schema
correction was blocked. Data/analysis commit: **`7188bb9`**, branch
`codex/c7-local-replication`. Design/gates were pushed before collection;
launch commit `37ee2e0`.

## Main result (exploratory)

*Source: `backend/out_study/T2L/analysis.json`, reproduced with
`scripts/analysis/repair_analysis.py --cell c7`.* The defect is the analysis
unit; estimates average usable repetitions within each defect/arm. A1 is
measured supervisor feedback at P1, A2 generic retry at P1, A3 regeneration
at P0 on the fixed quarter-stride subset.

| Arm | Valid / planned trials | Defects | Repair rate | Defect-bootstrap 95% CI |
|---|---|---|---|---|
| A1 | 414 / 414 | 138 | **72.9%** | [65.5%, 80.2%] |
| A2 | 413 / 414 | 138 | **66.2%** | [58.2%, 73.9%] |
| A3 | 102 / 102 | 34 | **38.2%** | [20.6%, 55.9%] |

**A1 − A2 = +6.8 pp [+0.5, +13.3]**, 138 paired defects, none lost.
137 pairs have 3/3 usable repetitions; one has 3/2. Majority repaired: A1
101/138, A2 91/138; discordant 16 versus 6, **exact McNemar p = 0.0525**.
The bootstrap estimates a mean contrast; McNemar tests a majority dichotomy.
Both are reported. **First-draw-only: +5.8 pp [−0.7, +12.4]**, 137 pairs,
p = 0.1338.

Both primary rates are below the pre-fixed 90% threshold: **the Gemini ceiling
does not replicate here**. A10's positive-interval and headroom readings
apply, with the borderline majority test and first-draw sensitivity limiting
the claim. This is suggestive exploratory evidence for feedback in this
model/runtime, not a new confirmatory result or proof of general benefit.

## Severity, operators and stages

| Group | A1 | A2 | A3 | A1 − A2, 95% CI |
|---|---|---|---|---|
| O1 (22 primary defects; 6 A3) | 39.4% | 47.0% | 0.0% | −7.6 pp [−25.8, +10.6], p = 1.0 |
| Severe (116 primary; 28 A3) | 79.3% | 69.8% | 46.4% | **+9.5 pp [+3.2, +16.4]**, p = 0.0127 |

O1's A3 exact defect-level interval is [0%, 45.9%]; the [0%, 0%] bootstrap
interval is degenerate with six all-zero defects. All planned subgroups:

| Operator | Primary defects | A1 | A2 | A3 (subset defects) |
|---|---|---|---|---|
| O1 | 22 | 39.4% | 47.0% | 0.0% (6) |
| O2 | 22 | 63.6% | 25.8% | 0.0% (6) |
| O3 | 22 | 72.7% | 56.1% | 0.0% (5) |
| O5 | 20 | 75.0% | 80.0% | 20.0% (5) |
| O6 | 26 | 92.3% | 92.3% | 100.0% (6) |
| O7 | 26 | 88.5% | 88.5% | 100.0% (6) |

| Stage | Primary defects | A1 | A2 | A3 (subset defects) |
|---|---|---|---|---|
| Reasoning | 66 | 58.6% | 42.9% | 0.0% (17) |
| Strategy | 20 | 75.0% | 80.0% | 20.0% (5) |
| Report | 52 | 90.4% | 90.4% | 100.0% (12) |

Subgroup observations are exploratory: reasoning has the larger contrast,
report arms tie, and strategy favours A2 descriptively.

## Failures, corrections and stability

- The sole final failure is **`YJ-sr_YVhnsZaBl-j9tjCg:O3`, A2, rep 0**.
  Its first response reached the 4096 output cap; correction required
  `54010 + 64 + 4096 > 32768` and was refused before inference. The wrapper
  labels it `api_error`/`provider_failure`; the actual cause is **output-cap
  followed by the context guard**, not a network outage.
- Counting it as unrepaired leaves rates and contrast unchanged because its
  other two A2 draws were already unrepaired; it restores 3/3 denominators.
  No trial was resampled. No valid A1 or A2 response needed schema correction.
- **36 valid A3 report trials needed a second schema call**. Removing them
  leaves A3 at **4.5%** on 22 defects; A1−A2 is unchanged.
- Complete A1 three-draw cells: **131/138 (94.9%)** identical raw call
  sequences, **136/138** same outcome. A2: **116/137 (84.7%)** identical
  sequences, **134/137** same outcome, versus 138 cells planned. Contiguous
  cached repetitions are not assumed independent.
- Original G2 **failed** (8/10 byte-identical pairs, 10/10 token calibrations).
  [A11](C7_A11.md) changed to r=3 before the schema pilot/final trials;
  the failed G2 is preserved, not relabelled. G4 passed 8/10 first-call valid.
  Both preflight directories are excluded from final estimates.

| Arm | Repaired | Replaced | Deleted | Unrepaired | Canonical JSON identical to clean Gemini output | Collateral on measurable trials |
|---|---|---|---|---|---|---|
| A1 | 302 | 65 | 15 | 32 | 174/414 (42.0%) | 27/258 (10.5%) |
| A2 | 274 | 27 | 5 | 107 | 163/413 (39.5%) | 39/257 (15.2%) |
| A3 | 39 | 4 | 39 | 20 | 0/102 (0.0%) | 66/66 (100.0%) |

Only repaired contributes to the repair rate; deletion/replacement are separate.
Mean valid-trial times: A1 **17.8 s**, A2 **17.6 s**, A3 **17.2 s**.
Valid trials used **7,361,433 local tokens**, excluding the capped failed
response; these are unbilled and separate from Gemini's budget.

## Paired comparison with Gemini

*Same eligible defects/arms; mean of usable repetitions on each side.*

| Arm | Matched defects | Local | Gemini | Local − Gemini, 95% CI |
|---|---|---|---|---|
| A1 | 137 | 72.7% | 96.8% | **−24.1 pp [−32.4, −16.1]** |
| A2 | 135 | 66.2% | 95.6% | **−29.4 pp [−37.5, −21.5]** |
| A3 | 34 | 38.2% | 92.2% | **−53.9 pp [−69.6, −38.2]** |

This is a **model-and-runtime comparison with Gemini-generated clean bases
held fixed**. Family, scale, quantisation, decoding and serving runtime are
bundled; causal contributions are not isolated and this is not an evaluation
of a wholly Qwen-generated pipeline. The frozen Gemini confirmatory result,
split rule and conference paper remain unchanged.

## Hardware, exclusions and verification

- Qwen2.5-7B-Instruct Q4_K_M, Ollama **0.40.3**, RTX **5060 Ti 16 GB**,
  i7-14700KF, 32 GB RAM, driver 591.86. Entire model on GPU (loaded 6.6 GB;
  observed total GPU use about 8.3 GB). **This PC has sufficient capacity.**
- Alias `qwen25-7b-c7`, digest
  `d7898812a651b04a1f9f4198a53d2374c07e71c0f35c5171a5d75b3bd4f5b10e`.
  Context 32768, output cap 4096, seed 20261012, temperature 0, one request
  at a time, flash attention, F16 cache. Exact provenance is in the header.
- 168 unique rows: **138 runnable**, 26 inapplicable, **four whole-defect
  context exclusions** (`gk3hzKydevLKZ2FVmJdt-A:O1/O2`,
  `o3hDZ2nv80tApZMNQw2aZA:O1/O2`). Allocation strides were preserved.
- `verification.json`: **929/929 offline scores and all post-facts agree**;
  **966 returned calls** have matching hashes/calibrated token counts,
  expected model and one session per defect. No detected prompt truncation.
  `completion.json` confirms unchanged runtime/source fingerprint.
- **426 offline tests passed**, 13 integration tests deselected before launch;
  core still 1167 trials. Production prompts, schemas and supervisor unchanged.
- Fresh Python: `backend/.venv/Scripts/python.exe`; copied `backend/venv/`
  is broken. Logs remain in `backend/.venv/c7/`.
- Publishing uses `%LOCALAPPDATA%/CodexC7/research-checkout` because the original
  Git metadata lacks modification rights. Existing drafts/unrelated edits are
  preserved; raw Yelp files and model weights are not committed.

**Next: update the journal draft's C7 placeholders and amendment record from
these verified results.** Do not edit conference `main.tex`.
