# Run queue — post-core experiments

**Created 2026-10-07.** The working list for the remaining runs, advanced one step
at a time by a self-paced loop: *finish → verify → commit → build the next →
amend → commit → launch → verify the first row → wait*. This file is the loop's
state. `NEXT_SESSION.md` §0 is still the map; `PREREGISTRATION.md` §0.1 is still
where every design decision is filed, **before** its run.

## Rules every step follows

1. **Amend before you spend.** A new step's design is filed as a dated
   `PREREGISTRATION.md` §0.1 amendment, committed **and pushed** before its
   first trial. It states which results already existed when it was written.
2. **Production defaults stay put.** Any new parameter defaults to production
   behaviour, and the core plan must still print 1,167 trials.
3. **Build gate:** new tests, full suite green (`pytest -m "not integration"`),
   `--plan-only` checked, first live defect inspected before walking away.
4. **Verify gate** after each run: complete checkpoint (planned rows and trials),
   one session per defect, offline re-score agrees 100 %, analysis written with
   `--json`, then commit + push data and analysis.
5. **Runs:** `LLM_DISABLE_FALLBACK=1`, detached via `Start-Process`, logs in
   `%TEMP%`. A dead run is resumed (resume skips whole defects; it never
   re-runs a `status_error`). Three dead runs in a row → stop and ask.
6. **Budget guard:** before launching, sum `total_tokens` over every checkpoint.
   If spent + projected > **55 M tokens** (≈ $137 if every token were billed at
   the output rate), stop and ask. Budget: $150.
7. **Blocked = stop and ask.** Never guess a decision the author owns.

## Queue

| # | Step | Status | Notes |
|---|---|---|---|
| Q1 | **Placement pass** (§0.1 A5) — `--cell placement` → `T2P` | ✅ done 2026-10-07 22:47, verified | 540 trials. Verify, then `repair_analysis.py --cell placement` (reports with/without `attempts_made > 1`; P0 report-stage schema retries are concentrated) |
| Q2 | **O1 severity sweep** (§0.1 A6) — `--cell severity` → `T2S` | ▶ running (started 22:47) | 144 trials. Verify, then `--cell severity` |
| Q3 | **Warm resampling** (plan D2, "REQUIRED"; §0.1 A7 filed) — `--cell warm` → `T2W` | 🔧 built, suite 387 green, pushed; launches after Q2 | Defaults below. Needs a temperature parameter threaded through `BaseAgent` with default 0 |
| Q4 | **Downstream propagation** (plan D12; §0.1 A8 to file) | ⬜ to build | Re-run the stages downstream of each retried output from the persisted `downstream_state`; endpoint fixed in the amendment before running. The prereg §3 item 6 put global success out of scope, so this is exploratory by amendment |
| Q5 | **Tier-1 replay** (prereg §3 item 5; §0.1 A9 to file) | ⬜ to build | 13 real defects × {A1, A2, A3} at P0 (A0 undefined at P0, D9b) × r = 3 = 117 trials. Judged by the same checks (plan §5 Tier 1, item 2), descriptive only (MDE ≈ 31 pp) |
| Q6 | **Second model — C7** (plan D5b) | ⛔ **blocked on the author** | Needs: model by name, size, quantisation, seed, runtime version; local (hardware?) or hosted. The loop stops here if unanswered |

### Q3 defaults (to be filed as A7 — the author may change them before launch)

- **Temperature 1.0.** D2 cites Tyen §4(d), which needed temperature 1 to force
  a different step; it is also Gemini's default sampling temperature.
- **Defects:** the placement subset (45, one-third per-operator stride), so the
  warm cells stratify exactly like the placement cells.
- **Cells, one session per defect, r = 3:** A1@P1 and A2@P1 at T = 0 (in-session
  comparators, as for C1 and placement) and A1@P1, A2@P1, A3@P0 at T = 1.0 →
  15 trials per defect, **675 trials**.
- **Reads:** A1 − A2 at T = 1 beside T = 0 (two gaps with CIs); share of retried
  outputs byte-identical to the clean output at each temperature (the ceiling
  mechanism); A3 best-of-k (k = 1..3) at T = 1 against A1 single-shot, with
  tokens per arm (the Olausson equal-budget baseline).

## Log

- 2026-10-07 — queue created; Q1 running, Q2 chained behind it.
- 2026-10-07 23:45 — **Q1 verified**: 71/71 rows, 540/540 trials (1 `status_error`), 45/45 defects in one session, offline re-score 539/539, descriptors identical. A1 repair P0 94.1 %, P1 97.8 %, P2 97.8 %, P3 97.0 %; P1−P2 0.0 pp [−4.4, +4.4], P1−P3 +0.7 pp, P3−P2 −0.7 pp, P1−P0 +3.7 pp [−1.5, +9.6]. §5 prediction P1 ≫ P3 ≈ P2: **P3 ≈ P2 holds, P1 ≫ P2/P3 does not** (ceiling). All 16 report-stage defects needed a schema retry at P0 (50 of 52 multi-attempt trials); without them P0 = 90.8 % on 29 defects. Collateral P0 38 % vs P1 1 %. Drift of re-run P1 vs core: 97 % same class, 81 % byte-identical.
- 2026-10-07 23:50 — **Q3 built**: `BaseAgent.temperature` (class default 0, written to the call log), `--cell warm` (45 defects, 675 trials, 270 at T=0 / 405 at T=1), `repair_analysis.py --cell warm` (gaps, byte-identity, best-of-k, tokens). §0.1 A7 filed with both readings fixed. Fast tests 51 pass; core plan still 1,167.
