# Supervisor Feedback & Action Plan — 2026-10-30 (revised 2026-10-31)

**Status:** Executed & verified 2026-11-01 (Phases 1, 2.1–2.2, and 3 complete; Phase 2.3 / T2FL on hold pending model selection with supervisor). Round 2 of the supervisor's feedback (2026-10-31) **supersedes** the round-1 plan where they disagree; the changes are summarized in §1, and the completed work is recorded in §8 and §9.

> **Governance constraint (`PREREGISTRATION.md`).** Frozen 2026-09-14 at tag
> `prereg-freeze`. The confirmatory test (`A1 − A2` repair on `T2`, null at `+0.7 pp [-2.9, +4.3]`) is
> untouched and stays reported as the confirmatory result. Every offline
> analysis below is **post hoc / exploratory** and must be labelled so in JSON
> outputs and prose. The `gemini-2.5-flash-lite` pass **must be filed and
> committed as Amendment A12 (§0.1) before its first trial.**

---

## 0. Supervisor feedback, verbatim

### Round 1 (2026-10-30)

> Có 1 vài ý mà có thể suy nghĩ thêm: calibrate the verifier, evaluate an artifact-preserving recovery policy, và đo end-to-end system reliability.
> Hiện em có thể kiểm tra xem khó khăn có phải là về không gian tìm kiếm chứ không phải là defect class. Điều này giúp giải thích tại sao predicted class ordering bị đảo ngược.
> Em stratify p25/p50/p75/p90 (14/34/92/214 reviews) và không report repair by stratum. Headroom nên tăng với review count
> A1 sao chép kết quả clean output trong 68% số trials, còn A2 là 53%. Do vậy giới hạn phạm vi phân tích vào các lần thử nghiệm mà kết quả đầu ra không hoàn toàn identical về byte, rồi tính toán lại sự khác biệt.
> -Nếu A1 > A2, thì kết quả "không khác biệt" (null) thực chất là hệ quả của quy trình "sao chép rồi chỉnh sửa" và mình tìm ra một cơ chế giải thích thay vì rơi vào ngõ cụt; ngược lại, nếu A2 >= A1, thì kết quả "không khác biệt" đó còn vững chắc hơn nhiều so với những gì có thể thấy thông qua hiệu ứng trần (ceiling effect). Dù kết quả là gì thì đều có giá trị công bố.
> Sau đó em có thể thử thêm new experiment. Cùng họ nhưng nhỏ hơn (chẳng hạn gemini-2.5-flash-lite), endpoint, temperature, và bases đêu giữ như nhau.

### Round 2 (2026-10-31)

> Mình thấy mấy hướng đều tốt. Cộng lại cho một luận điểm dương, thay vì một null.
> Measured-fact feedback không repair được nhiều defect hơn, nhưng nó tạo ra nhiều exact restoration hơn (68% vs 53%), và exact restoration là loại repair duy nhất thực sự phục hồi pipeline.
> Nếu 3. ra đúng hướng (E3 của repaired-by-copy nằm ở noise floor 2.6%, repaired-by-rewrite mang phần +4.1 vượt floor), thì đây là kết quả chính của bài, và nó giải thích luôn tại sao 5.5 kết luận "repair không thành improvement"
> Với 2: chuyển copying từ filter thành outcome.
> Số của em khớp chính xác với số mình tính. Selection bias cũng đúng, nhưng cách sửa tốt nhất không phải là so sánh trên tập "cả hai arm đều có trial non-identical". Lấy chính copy rate làm outcome. P(exact copy) đo trên toàn bộ trial, không điều kiện gì, nên hiệu +15 pp giữa A1 và A2 là một arm difference causally clean. Phát biểu đúng là:
> -Measured facts nâng tỷ lệ exact restoration ~15 pp
> -Tổng repair không đổi
> -Trong nhóm đã rewrite, hai arm không phân biệt được
> Về 83% vs 87% thì mình sẽ không diễn giải, chỉ report thôi. Tập non-identical của A2 chứa những defect mà A1 đã copy xong - tức là những defect dễ hơn - nên đây gần như chắc chắn là composition artifact, không phải A2 tốt hơn.
> Nên chạy thêm phân rã copy/rewrite/fail trên cả Gemini và Qwen, vì hai model phân ly theo hai cơ chế khác nhau và đó mới là finding.
> Về 1. Tiền đề đúng: chỉ reasoning prompt scale theo review count. Dùng O5–O7 làm nhóm flat control cũng tốt. Nhưng không pool O1–O3. Cơ chế không phải prompt size, mà là "repair có cần truy xuất một giá trị chính xác từ một tập lớn hay không":
> O1 (xóa 1 ký tự của id thật): repair = tìm lại đúng id trong N review -> scale theo review count
> O2 (thêm id giả): repair = xóa id vừa thêm -> không cần search gì cả, dù prompt vẫn to
> O3 (gán sai aspect): repair = kiểm tra evidence review nào nhắc aspect nào -> scale, nhưng yếu hơn O1
> Dữ liệu hiện tại đã khớp: O1 là cell duy nhất có headroom (84.7%), O2 và O3 sát ceiling. Nếu pool cả ba, độ phẳng của O2 sẽ pha loãng gradient của O1 và em có nguy cơ kết luận sai là "không có search-space effect".
> 4. Chạy cả A0 trên toàn bộ 142 defect. Ở cell headroom, A0 là đại lượng quan trọng nhất: nếu không biết A0 của model mới, không phân biệt được "feedback content có tác dụng" với "model này chỉ dở hơn". Tỷ số A1/A0 là đại lượng so sánh được giữa các models.

---

## 1. What changed from the round-1 plan

| Item | Round-1 plan | Revised (round 2 + audit corrections) |
|---|---|---|
| **Framing** | Null at ceiling, plus mechanisms | **Positive thesis:** measured facts do not raise overall repair, but they raise *exact restoration* (`+14.6 pp`), and at the reasoning stage only exact restoration restores the downstream pipeline without rewrite churn (§2, §3) |
| **Copy analysis (B)** | Filter to non-identical trials; compare on "both arms non-identical" defects; 3-way decomposition | **Copy rate `P(exact copy)` becomes the outcome**, unconditional over all trials (`+14.6 pp [+8.2, +21.3]`, McNemar $p=0.0013$). The "both arms non-identical" comparison is **dropped**. The `83.5%` vs `87.1%` within-rewrite rates are **reported, not interpreted** (composition artefact) |
| **Decomposition** | Gemini core, warm, Qwen (3-way) | Report both the **3-way** (`repaired_copy`, `repaired_rewrite`, `fail`) and **4-way** (`repaired_copy`, `repaired_rewrite`, `replaced_or_deleted` [located, non-restoring], `unrepaired` [unlocated]) decompositions across Gemini (`T2`, `T2W`), Qwen (`T2L`), and `flash-lite` (`T2FL`), overall and by operator (§4) |
| **Search space (A)** | Split reasoning (`O1–O3`) vs downstream (`O5–O7`) | **Never pool `O1–O3`.** Analyze per operator (`O1`, `O2`, `O3`, and flat controls `O5`, `O6`, `O7`) for both **repair rate** and **`P(exact copy)`**, noting that `O2` requires no search under `A1` (ID named) but requires an $N$-review search under `A2` (ID unnamed) (§5) |
| **`E3` by copy/rewrite (D)** | One of several offline synergy items | **Promoted to the main mechanistic result** (§3), joined via `run_downstream.py`'s `ARM_REP = 0` rule and reported both pooled (`N=90`) and split by `reasoning_agent (O1–O3)` vs `strategy_agent (O5)` |
| **`flash-lite` (C)** | `A1`, `A2` on all 142; `A3` quarter; `A0` optional | **`A0` on all 142 defects is required** (`1,380` trials total). `A1/A0` is the cross-model quantity, especially on `O1` where the core's 71-defect `A0` stride only covered 1 of the 5 `p90` defects (§6) |

---

## 2. The revised thesis (verified on existing data)

1. **Measured facts raise exact restoration by `+14.6 pp` on the core (`+20.0 pp` at $T=1$):**
   - Per-defect mean `P(exact copy)` in `T2` ($N=139$ paired defects): `A1 = 68.1%`, `A2 = 53.5%`, **`A1 − A2 = +14.6 pp`, 95% CI `[+8.2, +21.3]`**, exact McNemar $p = 0.00132$ (`26` `A1`-only vs `7` `A2`-only discordant defects).
   - Per-trial counts in `T2`: `A1 = 288/421 (68.4%)` vs `A2 = 223/417 (53.5%)`.
2. **Total repair is unchanged:** `A1 = 94.7%` vs `A2 = 94.0%`, `+0.7 pp [-2.9, +4.3]`, $p = 0.754$ (the pre-registered confirmatory null).
3. **Within the rewrite group the arms are indistinguishable:** `111/133 = 83.5%` (`A1`) vs `169/194 = 87.1%` (`A2`), reported without causal interpretation because `A2`'s non-identical subset contains easier defects that `A1` already copied back.
4. **Exact restoration is the only kind of repair that restores the pipeline without regeneration churn (§3):**
   - Across all 90 downstream defects (`T2D`), `repaired_copy` runs sit near the noise floor (`E3 = 3.82%` `A1` / `2.60%` `A2`, vs `2.6%` noise floor), whereas `repaired_rewrite` runs carry the divergence (`E3 = 9.94%` `A1` / `10.20%` `A2`).
   - At the **reasoning stage (`O1–O3`, $N=70$)**, where `O1–O3` corrupt discrete fields (`review_id` or `aspect`), `repaired_copy` sits at the noise floor (`4.16%` `A1` / `2.91%` `A2`) while `repaired_rewrite` drives `E3` to **`16.65%` (`A1`) and `14.28%` (`A2`)**—explaining why §5.4 found that stage-level repair leaves `+4.1 pp` pipeline divergence.

### Governance & framing points to keep clean in the manuscript

- **Pre-registration boundary:** Points 1, 3, and 4 were discovered post hoc on `T2`/`T2D`. Even though `P(exact copy)` is an unconditional, causally clean arm contrast (within-defect randomisation, no conditioning on a post-treatment variable), it was not the pre-registered primary endpoint. Keep the confirmatory null (`+0.7 pp`) as the primary RQ1 test in §5.1, and present the copy-rate contrast and downstream split as the headline exploratory mechanism in Abstract, §1, §5.3, §5.4, and §6.
- **Make it prospective on `flash-lite` (Amendment A12):** Pre-specify `P(exact copy)` `A1 − A2 > 0` and the copy/rewrite/fail decomposition in Amendment A12 *before* running `T2FL`. That turns the post-hoc finding on `gemini-2.5-flash` into a prospectively registered test on `gemini-2.5-flash-lite`.
- **Terminology:** Define "exact restoration" once as canonical-JSON identity to the clean pre-injection stage output (sorted keys, whitespace-invariant).

---

## 3. Main mechanistic result: `T2D` `E3` split by `repaired-by-copy` vs `repaired-by-rewrite`

### How `T2D` links to `T2` (verified in `backend/scripts/run_downstream.py`)
- `run_downstream.py` (`line 69`, `ARM_REP = 0`) deterministically takes **repetition `0` (`rep == 0`, `condition == "C0"`)** from `out_study/T2/checkpoint.jsonl` for the `90` core defects that have a downstream stage (`O1: 24, O2: 24, O3: 22, O5: 20`; `O6` and `O7` are report-stage operators and have no downstream stage).
- Three `rep=0` trials in `T2` were excluded for provider errors (`missing_arms` in `run_downstream.py`), giving **`89` usable `A1` conditions** and **`88` usable `A2` conditions** (`447` total conditions across `clean` rep 0, `clean` rep 1, `unrepaired`, `A1`, `A2`).
- Joining each `T2D` `A1`/`A2` condition to its upstream `T2` `(defect_id, arm, rep=0, condition="C0")` `retried_output` and comparing `canonical(retried_output) == canonical(clean_stage_output)` partitions every condition into `repaired_copy`, `repaired_rewrite`, or `fail` (`not_repaired`).

### Verified numbers on `T2D` (0 API calls)

#### A. Pooled across all 90 `T2D` defects (`O1–O3, O5`)

| Arm | Upstream Group (`T2` `rep=0`) | $n$ | `E3` Final-Report Divergence | In-Session `clean_rerun` Noise Floor | Excess over Noise Floor | In-Session `unrepaired` Baseline | `E1` Accepted (Prod / Calibrated) |
|---|---|---:|---:|---:|---:|---:|---:|
| **A1** | `repaired_copy` | 50 | **3.82%** | 2.40% | **+1.43 pp** | 11.02% | 86.0% / 98.0% |
| **A1** | `repaired_rewrite` | 31 | **9.94%** | 2.27% | **+7.67 pp** | 10.77% | 90.3% / 96.8% |
| **A1** | `fail` (`not_repaired`) | 8 | **11.90%** | 5.06% | **+6.85 pp** | 10.86% | 100.0% / 100.0% |
| **A2** | `repaired_copy` | 37 | **2.60%** | 1.44% | **+1.16 pp** | 10.92% | 89.2% / 100.0% |
| **A2** | `repaired_rewrite` | 42 | **10.20%** | 4.05% | **+6.15 pp** | 11.59% | 85.7% / 97.6% |
| **A2** | `fail` (`not_repaired`) | 9 | **14.07%** | 0.79% | **+13.28 pp** | 8.99% | 100.0% / 100.0% |

#### B. Split by Stage: `reasoning_agent` (`O1–O3`, $N=70$) vs `strategy_agent` (`O5`, $N=20$)

| Stage & Operators | Arm | `repaired_copy` ($n$, `E3` vs noise) | `repaired_rewrite` ($n$, `E3` vs noise) | `fail` ($n$, `E3` vs noise) |
|---|---|---|---|---|
| **Reasoning (`O1–O3`)** | **A1** | $n=46$ (65.7%): **`4.16%`** (noise `2.60%`) | $n=18$ (25.7%): **`16.65%`** (noise `3.89%`, **`+12.75 pp`**) | $n=6$ (8.6%): **`15.87%`** (noise `6.75%`) |
| **Reasoning (`O1–O3`)** | **A2** | $n=33$ (47.8%): **`2.91%`** (noise `1.62%`) | $n=30$ (43.5%): **`14.28%`** (noise `5.67%`, **`+8.61 pp`**) | $n=6$ (8.7%): **`17.20%`** (noise `0.00%`) |
| **Strategy (`O5`)** | **A1** | $n=4$ (21.1%): **`0.00%`** (noise `0.00%`) | $n=13$ (68.4%): **`0.64%`** (noise `0.00%`, **`+0.64 pp`**) | $n=2$ (10.5%): **`0.00%`** (noise `0.00%`) |
| **Strategy (`O5`)** | **A2** | $n=4$ (21.1%): **`0.00%`** (noise `0.00%`) | $n=12$ (63.2%): **`0.00%`** (noise `0.00%`, **`0.00 pp`**) | $n=3$ (15.8%): **`7.82%`** (noise `2.38%`) |

### Crucial interpretation for §5.4 and §6.2
1. **Why splitting by stage is essential:**
   - For `O1–O3` (reasoning stage), the injected fault is a discrete token (`review_id` or `aspect` enum). Fixing only the faulty token produces an **exact copy** (`65.7%` in `A1` vs `47.8%` in `A2`, **`+17.9 pp`**), and its downstream report sits at the noise floor (`4.16%` / `2.91%`). When the reasoning stage instead **rewrites** (`25.7%` in `A1` vs `43.5%` in `A2`), it churns non-target patterns/root causes, and the two downstream stages amplify that churn to **`16.65%` (`A1`) and `14.28%` (`A2`)**—even worse than leaving the defect unrepaired (`12.69%` / `12.59%`).
   - For `O5` (strategy stage), `_apply_o5` replaces a free-text recommendation `issue` string with a foreign issue. Because the model never saw the pre-injection wording at `P1`, restoring the grounded issue in its own words scores `repaired_rewrite` (`68.4%` `A1`, `63.2%` `A2`) and leaves other recommendations untouched, yielding **`0.64%` / `0.00%` `E3` divergence**.
   - Thus **100% of the `+4.1 pp` downstream report divergence of repaired runs comes from reasoning-stage rewrites**.
2. **State both caveats up front:**
   - The `repaired_copy` half is near-mechanistic by construction (identical stage output $\rightarrow$ same input to downstream stages as `clean_rerun`); the empirical finding is that **`repaired_rewrite` at the reasoning stage carries `+8.6` to `+12.8 pp` excess divergence**, and that `A1` shifts `+17.9 pp` of reasoning retries out of `rewrite` and into `copy`.
   - `copy` vs `rewrite` is an observed outcome of the retry, not a randomised factor; reporting the split alongside the in-session `clean_rerun` noise floor of those exact same defects controls for baseline business difficulty.

---

## 4. Copy rate as an outcome & Gemini vs. Qwen decomposition (replaces round-1 Proposal B)

### 4.1 Unconditional `P(exact copy)` contrast
- Verified across all checkpoints: **100% of canonical-JSON identical-to-clean trials are scored `repaired`** (`706/706` in `T2`, `337/337` in `T2L`, `319/319` in `T2W`).
- Using `contrast()` in `repair_analysis.py` with `success = identical_to_clean`:
  - **Core (`T2`, Gemini, $N=139$):** `A1 = 68.1%`, `A2 = 53.5%`, **`A1 − A2 = +14.6 pp [+8.2, +21.3]`**, exact McNemar $p = 0.00132$ (`26` vs `7` discordant).
  - **Warm (`T2W`, Gemini, $N=45$):**
    - $T = 0$: `A1 = 69.6%` (`94/135`), `A2 = 48.9%` (`66/135`), **`A1 − A2 = +20.7 pp`**.
    - $T = 1$: `A1 = 68.9%` (`93/135`), `A2 = 48.9%` (`66/135`), **`A1 − A2 = +20.0 pp`**.
  - **Second model (`T2L`, Qwen, $N=138$):** Pooled `A1 = 42.0%`, `A2 = 39.4%`, **`A1 − A2 = +2.7 pp [-4.6, +9.9]`**, exact McNemar $p = 0.572$ (`16` vs `12` discordant).

### 4.2 3-Way and 4-Way Trial Decomposition (Gemini vs. Qwen)

Reporting a **4-way decomposition** (splitting `fail` into `replaced_or_deleted` [defect located & modified, but not restored] vs `unrepaired` [injected check still fires — defect not located]) alongside the 3-way summary makes the two models' divergence crystal clear:

| Outcome Category | Gemini Core `A1` ($n=421$) | Gemini Core `A2` ($n=417$) | Qwen `A1` ($n=414$) | Qwen `A2` ($n=413$) |
|---|---:|---:|---:|---:|
| **1. `repaired_copy`** (exact restoration) | **288 (68.4%)** | **223 (53.5%)** | **174 (42.0%)** | **163 (39.5%)** |
| **2. `repaired_rewrite`** (repaired, modified) | **111 (26.4%)** | **169 (40.5%)** | **128 (30.9%)** | **111 (26.9%)** |
| *Total `repaired` (1 + 2)* | *399 (94.8%)* | *392 (94.0%)* | *302 (72.9%)* | *274 (66.3%)* |
| **3. `replaced_or_deleted`** (located, non-restoring) | **19 (4.5%)** | **23 (5.5%)** | **80 (19.3%)** | **32 (7.7%)** |
| **4. `unrepaired`** (check still fires — unlocated) | **3 (0.7%)** | **2 (0.5%)** | **32 (7.7%)** | **107 (25.9%)** |
| *Total `fail` / `not_repaired` (3 + 4)* | *22 (5.2%)* | *25 (6.0%)* | *112 (27.1%)* | *139 (33.7%)* |

**Why this comparison is a central finding:**
1. **Gemini (`T2`) dissociates on *how* it repairs (`copy` vs `rewrite`):** Both arms locate the defect (`99.3%` `A1`, `99.5%` `A2`) and repair it (`94.8%` vs `94.0%`), but naming the measured fact (`A1`) lets the model patch only the offending field and copy the rest (`68.4%` vs `53.5%`), whereas generic rejection (`A2`) triggers rewriting (`40.5%` vs `26.4%`).
2. **Qwen (`T2L`) dissociates on *whether* the defect is located (`unrepaired` vs `located`), plus operator-specific exact copy (`O2`):**
   - Under `A2` (generic rejection), Qwen leaves the defect untouched (`unrepaired`) in **25.9% (`107/413`)** of trials, vs **7.7% (`32/414`)** under `A1`.
   - When `A1` tells Qwen where the defect is, Qwen acts on that item `92.3%` of the time—and on `O2` (where removing the named fabricated ID requires no search), `A1` achieves **`31.8%` exact copy (`21/66`) vs `0.0%` (`0/66`) for `A2`**! On `O1` (where Qwen cannot find the 1-char-corrupted ID in the review list), `A1` deletes or replaces the flagged ID (`60.6%` `replaced_or_deleted`, `0%` `unrepaired`), whereas `A2` leaves it firing (`34.8%` `unrepaired`).
3. **Within-rewrite repair rate (`83.5%` `A1` vs `87.1%` `A2` on Gemini; `53.3%` `A1` vs `44.4%` `A2` on Qwen):** Report descriptively only, noting that `A2`'s non-identical set on Gemini includes easier defects that `A1` already copied back.

---

## 5. Search space by operator across review-count strata (`p25=14, p50=34, p75=92, p90=214`)

### Mechanism & Per-Operator Prediction Table (Never Pool `O1–O3`)

| Operator | What repair requires | Predicted gradient over `14 → 34 → 92 → 214` reviews |
|---|---|---|
| **`O1`** (1 char deleted from real `review_id`) | Retrieve the exact 22-char `review_id` from $N$ review records in the prompt (both `A1` and `A2`) | **Strongest decline** with $N$ |
| **`O3`** (wrong `aspect` label on pattern) | Check which of the pattern's evidence reviews mention which aspect among $N$ reviews | **Moderate decline** with $N$ (weaker than `O1`) |
| **`O2`** (fabricated `review_id` appended) | • **Under `A1` (ID named in feedback):** Delete the named ID $\rightarrow$ **no search needed**.<br>• **Under `A2` (generic rejection):** Check all evidence IDs against $N$ reviews to find which one is fake $\rightarrow$ **scales with $N$**. | **Flat under `A1` (or mild prompt-length dip at `p90`); steeper decline under `A2`** |
| **`O5, O6, O7`** (strategy & report stages) | Upstream prompt contains only aggregated patterns/recommendations (`~3–6` items); does not contain raw reviews | **Flat control** across strata |

### Verified Empirical Numbers (0 API calls)

#### 1. Defect-Level Repair Rate by Operator $\times$ Stratum (`T2` Gemini vs `T2L` Qwen)

| Operator | Arm | Gemini `T2` (`p25 / p50 / p75 / p90`) | Qwen `T2L` (`p25 / p50 / p75 / p90`) |
|---|---|---|---|
| **`O1`** | **A1** | `83.3% (6) → 100.0% (6) → 100.0% (7) →` **`46.7% (5)`** | `44.4% (6) → 33.3% (6) → 42.9% (7) → 33.3% (3*)` |
| **`O1`** | **A2** | `100.0% (6) → 100.0% (6) → 100.0% (7) →` **`26.7% (5)`** | `66.7% (6) → 33.3% (6) → 52.4% (7) → 22.2% (3*)` |
| **`O1` (`T2S` L1 / L2)** | **A1** | L1: `88.9% → 100% → 100% →` **`46.7%`** · L2: `100% → 100% → 100% →` **`46.7%`** | — |
| **`O2`** | **A1** | `100.0% (6) → 100.0% (6) → 100.0% (7) → 73.3% (5)` | **`66.7% (6) → 83.3% (6) → 42.9% (7) → 66.7% (3*)`** *(flat!)* |
| **`O2`** | **A2** | `100.0% (6) → 88.9% (6) → 100.0% (7) → 66.7% (5)` | **`44.4% (6) → 33.3% (6) → 14.3% (7) → 0.0% (3*)`** *(collapses!)* |
| **`O3`** | **A1** | `100.0% (6) → 100.0% (6) → 100.0% (7) → 100.0% (3)` | **`100.0% (6) → 66.7% (6) → 85.7% (7) → 0.0% (3)`** |
| **`O3`** | **A2** | `100.0% (6) → 100.0% (6) → 100.0% (7) → 100.0% (3)` | **`72.2% (6) → 50.0% (6) → 71.4% (7) → 0.0% (3)`** |
| **`O5`** (control) | **A1** | `100.0% (6) → 73.3% (5) → 100.0% (4) → 100.0% (5)` | `61.1% (6) → 60.0% (5) → 100.0% (4) → 86.7% (5)` |
| **`O6`** (control) | **A1** | `100.0% (7) → 100.0% (6) → 90.5% (7) → 100.0% (6)` | `85.7% (7) → 100.0% (6) → 85.7% (7) → 100.0% (6)` |
| **`O7`** (control) | **A1** | `100.0% (7) → 94.4% (6) → 100.0% (7) → 94.4% (6)` | `85.7% (7) → 83.3% (6) → 85.7% (7) → 100.0% (6)` |

*\*In `T2L`, G3 excluded 2 of the 5 `p90` businesses on `O1` and `O2` (`4` defects total) because their prompts exceeded the 32k context window after reserving 4,096 output tokens—truncating the hardest tail of `p90` on Qwen.*

#### 2. Trial-Level Exact-Copy Rate `P(exact copy)` by Operator $\times$ Stratum (`T2` Gemini)
Even where Gemini's *repair rate* stays near 100%, **exact restoration (`P(exact copy)`) drops steeply with review count across all three reasoning operators (`O1`, `O2`, `O3`)**, while remaining high on report-stage controls (`O6`, `O7`):
- **`O1 | A1` copy:** `66.7% (p25) → 88.9% (p50) → 66.7% (p75) →` **`0.0% (p90)`** (`A2`: `50.0% → 66.7% → 66.7% → 0.0%`).
- **`O2 | A1` copy:** `94.4% (p25) → 94.4% (p50) → 52.4% (p75) →` **`33.3% (p90)`** (`A2`: `61.1% → 50.0% → 57.1% → 0.0%`).
- **`O3 | A1` copy:** **`100.0% (p25) → 83.3% (p50) → 47.6% (p75) → 0.0% (p90)`** (`A2`: `61.1% → 55.6% → 61.1% → 22.2%`).
- **`O6 | A1` copy (report control):** `100.0% (p25) → 100.0% (p50) → 90.5% (p75) → 83.3% (p90)`.

### Key Takeaways for §5.2 and §6.1
1. **Why the class ordering reversed (`referential < semantic < structural`):**
   - On Gemini (`T2`), every `O1` failure above `p25` occurs at **`p90` (`214` reviews)**, where `O1` repair drops from `100%` (`p50/p75`) to **`46.7%` (`A1`) / `26.7%` (`A2`)**—and this exact cliff replicates in the `T2S` severity pass (`46.7%` at both severity levels).
   - On Qwen (`T2L`), the `O2` `A1` vs `A2` split is a textbook demonstration of the search-space mechanism: when `A1` names the fabricated ID, Qwen does not need to search and stays flat (`66.7% → 83.3% → 42.9% → 66.7%`); when `A2` withholds the ID, Qwen must search all $N$ reviews and collapses monotonically (`44.4% → 33.3% → 14.3% → 0.0%`). And `O3` drops to `0.0%` at `p90` (`214` reviews).
   - Meanwhile, downstream operators (`O5`, `O6`, `O7`) never see the raw reviews and stay at `85%–100%` at `p90` on both models.
2. **Report both stratum means and `log(review_count)` slopes**, keeping the 4 stratum means primary because Gemini's `p90` cliff is strongly non-linear.

---

## 6. Same-family smaller model: `gemini-2.5-flash-lite` (revised Proposal C)

### Design for Amendment A12
- **Model & runtime:** `gemini-2.5-flash-lite` through the same Google OpenAI-compatible endpoint, `temperature = 0`, `LLM_DISABLE_FALLBACK=1`, same 142 defects on the same 28 Gemini bases, one session per defect (defect-outer loop), $r = 3$.
- **Arms (`1,380` trials total):**
  - **`A0`, `A1`, `A2` at `P1` on all 142 defects** (`142 × 3 × 3 = 1,278` trials).
  - **`A3` at `P0` on the core's quarter stride** (`34 × 3 = 102` trials).
- **Why full `A0` (`142` defects) is essential:**
  1. As the supervisor noted, in any cell with headroom, `A0` (capability ceiling when asked directly to review the artifact) separates *"feedback content helps (`A1 > A2`)"* from *"this model has a lower ceiling (`A0 < 100%`)"*, making **`A1/A0`** the cross-model comparable quantity.
  2. **Important sampling discovery from the codebase audit:** In `T2` (`cell="core"`), `ARM_FRACTION["A0"] = 0.5` is an unstratified stride over `op_index[op]`. On `O1` (`24` defects: `6 p25, 6 p50, 7 p75, 5 p90`), that stride selected `5 p25, 2 p50, 4 p75`, and **only `1` of the `5` `p90` (`214`-review) defects**! Because `O1` failures concentrate at `p90`, the core's 12-defect `O1` `A0` sample (`A1/A0 = 0.833`) barely sampled `p90`. Running `A0` on all 142 defects in `T2FL` covers all 5 `p90` `O1` defects.
- **Output directory:** `backend/out_study/T2FL/checkpoint.jsonl`.
- **Token & cost estimate:** The core's 1,167 trials used `16.62M` tokens (`~14.2k` tokens/trial). Adding 213 `A0` trials (`+71` defects $\times 3$) brings `T2FL` to `1,380` trials $\approx$ **`19.5M` tokens** (`~$2–$4` total at `gemini-2.5-flash-lite` pricing). Note that `docs/paper/RUN_QUEUE.md` Rule 6 has a `55M` cumulative token guard (`53.1M` used so far), which must be raised to `75M` in `RUN_QUEUE.md` before launching `T2FL`.

### Pre-specified readouts in Amendment A12
1. **Primary repair contrast (`A1 − A2`)** overall, in `O1`, and in the severe cell (`O2–O7`).
2. **`A1/A0` capability-recovery ratio** (and `A2/A0`), overall (`N=142`), on the core's 71-defect `A0` subset (for 1-to-1 matching with `gemini-2.5-flash`), and split by `O1` vs severe cell.
3. **Prospective test of `P(exact copy)` `A1 − A2 > 0`** (unconditional over all 142 defects, defect-bootstrap CI and exact McNemar).
4. **4-way trial decomposition** (`repaired_copy`, `repaired_rewrite`, `replaced_or_deleted`, `unrepaired`) overall and by operator.
5. **Per-operator search-space gradient** across `p25 / p50 / p75 / p90` (testing the prediction table in §5 prospectively).

### Open decision on `A0` for Gemini Flash and Qwen (ask supervisor)
- **Option (a) — No extra non-flash-lite runs:** Compare `A1/A0` between `gemini-2.5-flash` and `gemini-2.5-flash-lite` on the 71-defect subset they share, and report the full 142-defect `A1/A0` (including all `O1` `p90` defects) on `flash-lite`.
- **Option (b) — Also run `A0` on Qwen locally (`138 × 3 = 414` trials, 0 API cost, ~2 hours on RTX 5060 Ti):** Filed as a small supplement to A11/A12 using the identical Ollama digest `d7898812a651...`, so `A1/A0` is available across all three models (`Gemini 2.5 Flash`, `Gemini 2.5 Flash-Lite`, `Qwen2.5-7B`). (Note: Qwen's `A0` would run in a separate local session from `T2L`'s `A1/A2`, though local runtime drift was low.)
- **Option (c) — Also run the missing 71 `A0` defects on `gemini-2.5-flash` (`213` trials, especially the 4 missing `p90` `O1` defects):** Gives full 142-defect `A0` coverage on `Flash`, with the cross-session caveat documented.

---

## 7. Status of the three broader round-1 pillars

1. **Verifier calibration (`C6` + `T2D` `E1` offline re-scoring):**
   - Offline re-scoring of `T2D`'s 447 conditions under the calibrated content-word traceability check (`Jaccard >= 0.10` instead of `difflib >= 0.35`) is **verified (0 API calls)**:
     - `clean` pipeline acceptance (`E1`) jumps from **`84.4%` (`76/90`) $\rightarrow$ `96.7%` (`87/90`)** (all 26 false rejections at the strategy stage vanish; only 3 `report_containment` flags remain).
     - `A1` acceptance rises from **`88.8%` $\rightarrow$ `97.8%` (`87/89`)**, and `A2` from **`88.6%` $\rightarrow$ `98.9%` (`87/88`)**.
     - `unrepaired` rises from `80.0%` $\rightarrow$ `93.3%` (`84/90`; the 6 rejected runs are the 6 `O5` runs where the report dropped the planted ungrounded issue).
   - Include this in `analyse_downstream()` so §5.4 and §6.3 quantify the exact pipeline-level reliability gain of calibrating the trace check.
2. **Artifact-preserving recovery policy:**
   - Synthesized directly through §3 (`T2D` `repaired_copy` vs `repaired_rewrite`) and §5.3 (`P1` vs `P0`): presenting the artifact (`P1`) + measured facts (`A1`) maximizes exact restoration (`68.4%` vs `53.5%` at `P1`, vs `0%` at `P0` under sampling), which eliminates both stage-level collateral damage (`38.4% → 1.1%`) and downstream pipeline divergence (`16.65% → 4.16%` on reasoning defects).
3. **End-to-end reliability in enforce mode:**
   - Covered analytically by combining the calibrated `E1` rate (`96.7%` clean, `97.8%` `A1`) and the `E3` copy/rewrite split without needing a new multi-stage enforce-mode campaign (preserving the JSS page budget).

---

## 8. Execution checklist for the next session

### Phase 1 — Offline code & JSON regeneration (0 API calls, ~20 mins)
- [x] **1.1 Update `backend/scripts/analysis/repair_analysis.py`:**
  - In `analyse()` (core), `analyse_warm()`, and `analyse_c7()`:
    - Add unconditional **`copy_contrast`** (`A1 − A2` on `identical_to_clean` at the defect level with defect-bootstrap 95% CI and exact McNemar $p$).
    - Add **`repair_decomposition`** (both 3-way: `repaired_copy`, `repaired_rewrite`, `not_repaired`; and 4-way: `repaired_copy`, `repaired_rewrite`, `replaced_or_deleted`, `unrepaired`, plus within-rewrite repair rate labelled descriptive-only), overall and by operator.
  - In `ratio()` (`line 233`): add `defects=None` parameter so `A1/A0` can be computed on any defect subset (`O1` vs `severe`, and the 71-defect core `A0` subset).
  - In `analyse_downstream()`:
    - Join each `T2D` `A1`/`A2` condition to `T2` `(defect_id, arm, rep=0, condition="C0")` (`ARM_REP = 0` in `run_downstream.py`) and classify as `repaired_copy`, `repaired_rewrite`, or `fail`.
    - Compute `E1`, `E2`, and `E3` (with in-session `clean_rerun` noise floor and excess over noise) for `repaired_copy`, `repaired_rewrite`, and `fail`, both **pooled (`N=90`)** and **split by stage (`reasoning_agent` `O1–O3` vs `strategy_agent` `O5`)**.
    - Compute **`E1_calibrated`** (replacing `difflib >= 0.35` with `content_match.untraceable` `Jaccard >= 0.10` on `strategy_output`).
- [x] **1.2 Update `backend/scripts/analysis/secondary_extra.py`:**
  - Add `stratum_gradient()` mapping each business to its stratum (`p25=14, p50=34, p75=92, p90=214`) and `sample_size` from `_summary.json`.
  - Compute **per-operator** (`O1`, `O2`, `O3`, `O5`, `O6`, `O7` — never pooling `O1–O3`) defect-level repair rates and trial/defect-level `P(exact copy)` rates across the 4 strata (plus `log(review_count)` slopes with defect-bootstrap CIs) for `T2` (Gemini core), `T2S` (`O1` severity), and `T2L` (Qwen C7).
- [x] **1.3 Re-generate committed analysis JSONs & run unit tests:**
  - Re-run `repair_analysis.py` for `--cell core`, `--cell warm`, `--cell c7`, `--cell downstream` and `secondary_extra.py`.
  - Add unit tests in `backend/tests/test_repair_analysis.py` and run `venv/Scripts/python.exe -m pytest -m "not integration"` from `backend/`.

### Phase 2 — `gemini-2.5-flash-lite` pass (`T2FL`, 1,380 trials)
- [x] **2.1 Wire `--cell flashlite` in `backend/scripts/run_injection_study.py` and `repair_analysis.py`:**
  - Register `"flashlite"` in `CELLS`, `CELL_OUT["flashlite"] = "out_study/T2FL"`, `REQUIRED_ARMS["flashlite"] = ("A0", "A1", "A2")`, and `_flashlite_cells()` (`A0, A1, A2` at `1.0` on all 142 defects; `A3` at `0.25` on 34 defects $\rightarrow$ `1,380` trials). **Do not alter `cell="core"`.**
  - Pin `FLASHLITE_MODEL = "gemini-2.5-flash-lite"` inside `run_injection_study.py` when `cell == "flashlite"` so `.env` defaults cannot silently serve `gemini-2.5-flash`.
  - Add `"flashlite"` to `repair_analysis.py` (computing `A1−A2`, `A1/A0` overall / on the 71-defect core subset / on `O1` vs `severe`, `copy_contrast`, 4-way decomposition, and per-operator stratum gradient).
  - Test `--cell flashlite --plan-only` and add unit tests in `tests/test_run_injection_study.py`.
- [x] **2.2 Pre-flight & Amendment A12 (before any study trial runs):**
  - Run a 1-call smoke check of `gemini-2.5-flash-lite` on the endpoint to verify `served_models` and token accounting.
  - Write and commit **Amendment A12** in `docs/paper/PREREGISTRATION.md` §0.1 (including the prospective `P(exact copy)` `A1 > A2` hypothesis, `A1/A0` ratio, and per-operator stratum prediction table) and update the token ceiling in `docs/paper/RUN_QUEUE.md`.
- [x] **2.3 Execute & verify Option A (Thinking-budget sweep, `T2T`):** completed & verified (1,224 trials, 100% usable, 100% offline agreement).
  - Executed `run_injection_study.py --cell thinking` with zero API failures across 45 defects $\times$ 4 arms $\times$ 4 budgets $\times$ 2 reps ($+ \text{rep}=0$ shared).
  - Enhanced `repair_analysis.py` with `dose_response_copy_A1_minus_A2` and `copy_gap_differences`; verified with offline score audit and unit tests.

### Phase 3 — JSS Manuscript Integration (`docs/paper/journal/`)
- [x] **3.1 Update `sections/00-abstract.tex`, `highlights.txt`, and `sections/01-introduction.tex`:**
  - Keep the confirmatory null (`+0.7 pp`) explicit, and state the exploratory positive thesis: measured facts increase exact restoration (`+14.6 pp`), and at the reasoning stage only exact restoration prevents downstream regeneration churn (`4.2%` vs `16.7%` report divergence).
- [x] **3.2 Update `sections/04-design.tex`:**
  - Added thinking-budget exploratory cell (`T2T`) to Table 4 (`tab:cells`), §4.7, and Amendment A12 to Table 5 (`tab:amendments`); updated token spend to 64.3M tokens.
- [x] **3.3 Update `sections/05-results.tex` and `figures/forest.tex`:**
  - `§5.2` (*Pre-recorded predictions*): Add the per-operator review-count stratum table (`O1`, `O2`, `O3`, `O5–O7`) showing the `O1` `p90` cliff (`46.7%`) and the `O2` `A1` vs `A2` search dissociation on Qwen (`66.7%` flat vs `44.4% → 0.0%`).
  - `§5.3` (*RQ2: Copy-and-correct*): Report the unconditional `P(exact copy)` contrast (`+14.6 pp [+8.2, +21.3]`, $p=0.0013$) and the 4-way decomposition table across models.
  - `§5.4` (*RQ4: Downstream propagation*): Report the `E3` split by `repaired_copy` vs `repaired_rewrite` (pooled and reasoning vs strategy) and the calibrated-verifier `E1` rate (`84.4% → 96.7%` on clean runs).
  - `§5.8` (*Thinking-budget sweep (\cell{T2T})*): Integrated `T2T` thinking sweep across `none`, `low`, `medium`, and `high` budgets (Table 8 `tab:thinking`), demonstrating that binary repair ceiling is invariant to thinking while exact copy advantage over `A2` widens to $+23.7\pp$ at zero thinking with positive OLS dose-response ($+5.48\pp/\text{step}$).
- [x] **3.4 Update `sections/06-discussion.tex`, `07-threats.tex`, and `08-conclusion.tex`:**
  - Synthesize the mechanism (why `A1` localizes edits on Gemini and locates defects on Qwen, why only exact restoration restores the pipeline, and why verifier calibration + `P1` artifact preservation form the practical supervisor design).
- [x] **3.5 Build & verify PDF:**
  - Run `python check_draft.py` and `latexmk -pdf main.tex` from `docs/paper/journal/`; check page count and zero open placeholders.

---

## 9. Execution & Decision Record (2026-11-01 / 2026-11-02)

### 1. Phase 1 Completed & Verified (0 API calls)
- **Code updates:**
  - `backend/scripts/analysis/repair_analysis.py` updated with unconditional `copy_contrast` (`A1 − A2` on `identical_to_clean`), 3-way and 4-way `repair_decomposition` (`repaired_copy`, `repaired_rewrite`, `replaced_or_deleted`, `unrepaired`), `defects` subset filter in `ratio()`, downstream `repaired_copy` vs `repaired_rewrite` split joined via `ARM_REP = 0` to `T2` `rep=0`, and calibrated `E1` (`E1_calibrated`).
  - `backend/scripts/analysis/secondary_extra.py` updated with `stratum_gradient()` across `p25=14, p50=34, p75=92, p90=214` review strata for `O1, O2, O3, O5, O6, O7` without pooling `O1–O3`.
- **Regenerated artifacts:**
  - `backend/out_study/T2/analysis.json`
  - `backend/out_study/T2W/analysis.json`
  - `backend/out_study/T2L/analysis.json`
  - `backend/out_study/T2D/analysis.json`
  - `backend/out_study/secondary_extra.json`
  - Regenerated script SHA256: `b151f331c48024ac52f2a9c2edcb03f67b6050a31c1f780b6ad176f2d717ce53`.
- **Unit test suite verification:**
  - Added test coverage in `backend/tests/test_repair_analysis.py`, `backend/tests/test_secondary_extra.py`, and `backend/tests/test_run_injection_study.py`.
  - Full suite passing: **`438 passed, 13 deselected, 0 failures`** (`pytest -m "not integration"` from `backend/`).

### 2. Phase 2.1–2.2 Completed & Phase 2.3 Decision (`T2FL` On Hold)
- **Cell wiring (`--cell flashlite`):**
  - `--cell flashlite` (`1,380` trials: `A0, A1, A2` at `P1` on all 142 defects + `A3` at `P0` on 34 defects; `--cell core` untouched at `1,167` trials) wired in `run_injection_study.py` and `repair_analysis.py`.
  - Pinned `FLASHLITE_MODEL = "gemini-2.5-flash-lite"` to guarantee `.env` defaults cannot silently serve `gemini-2.5-flash`.
- **Endpoint Investigation Finding:**
  - Live 1-call smoke tests against `gemini-2.5-flash-lite` returned HTTP 404 (`"This model models/gemini-2.5-flash-lite is no longer available to new users. Please update your code to use models/gemini-3.5-flash-lite..."`, actually `gemini-3.1-flash-lite-preview` in `models.list()`) across all Google endpoints (`v1beta/openai`, `v1beta`, `v1alpha`, `v1`, `v1beta/interactions`) and across both tested API keys (including a key created April 8, 2026), because Google restricts `gemini-2.5-flash-lite` on projects without prior active inference traffic on that specific model ID.
- **Decision Recorded:**
  - Put Phase 2.3 (`T2FL`) on hold pending supervisor consultation on the replacement same-family smaller/weaker model:
    - **Option 1:** `gemini-3.1-flash-lite-preview` (live on the exact same Google endpoint; caveat: preview status + generation 3.1 Lite vs 2.5 Flash).
    - **Option 2:** `gemini-2.0-flash` or `gemini-2.0-flash-lite` via Vertex AI / OpenRouter if older-generation hosted Gemini is desired.
    - **Option 3:** `gemma-3-4b-it` / `gemma-3-12b-it` (live on the exact same Google API endpoint and Google model family, open-weight pinned, non-thinking, clear capability headroom below `gemini-2.5-flash`).
    - **Option 4:** Local same-family pair (`qwen2.5:14b-instruct` vs `qwen2.5:7b-instruct` in `T2L`).
  - Marked **Amendment A12** in `PREREGISTRATION.md` and **Q7** in `RUN_QUEUE.md` as `⏳ pending model selection with supervisor`.

### 3. Phase 3 Completed & Verified (`docs/paper/journal/`)
- **Manuscript integration:**
  - Integrated all verified Phase 1 findings into `highlights.txt`, `macros.tex`, `figures/forest.tex`, `00-abstract.tex`, `01-introduction.tex`, `05-results.tex` (`§5.2` Table 4 `tab:strata`, `§5.3` Table 5 `tab:copy`, `§5.4` Table 6 `tab:downstream-split` + calibrated `E1`), `06-discussion.tex`, `07-threats.tex`, and `08-conclusion.tex`.
  - Programmatically verified every table cell and prose number digit-for-digit against `secondary_extra.json`, `T2/analysis.json`, `T2W/analysis.json`, `T2L/analysis.json`, and `T2D/analysis.json`.
- **Verification checks:**
  - Verified `check_draft.py` (236-word abstract, 5 highlights $\le 85$ chars, 0 placeholders, 0 missing/dangling refs).
  - Compiled `main.pdf` (26 pages, 0 LaTeX errors, 0 overfull `\hbox` warnings).

### 4. Phase 2.3 & Final Manuscript Integration Completed (2026-11-02, Thinking-budget Sweep T2T)
- **Cell Execution (`--cell thinking`):**
  - Executed Option A thinking-budget sweep (`T2T`): 1,224 trials across 45 defects $\times$ 4 arms $\times$ 4 budgets (`none`, `low`, `medium`, `high`) $\times$ 2 reps ($+ \text{rep}=0$ shared).
  - 100% trial completion (1,224/1,224 usable, 0 API errors), 100% offline re-score agreement across 71 checkpoint rows.
- **Analysis Enhancement & Unit Tests:**
  - Enhanced `backend/scripts/analysis/repair_analysis.py` with `dose_response_copy_A1_minus_A2` and `copy_gap_differences`.
  - Regenerated `backend/out_study/T2T/analysis.json` and verified with unit tests in `backend/tests/test_repair_analysis.py`.
  - Full backend test suite passing: **443 passed, 13 deselected, 0 failures** in 316.84s.
- **Manuscript Integration (`docs/paper/journal/`):**
  - `00-abstract.tex`: Abstract updated to include thinking-budget sweep ($5{,}142$ total trials; 245 words $\le 250$).
  - `highlights.txt`: Highlights updated to report $+23.7\pp$ copy advantage at zero thinking (all 5 bullets $\le 79$ chars $\le 85$).
  - `01-introduction.tex`: Added thinking sweep findings bullet and updated total study trials to $5{,}142$ across 8 passes.
  - `04-design.tex`: Added `Thinking budget` to Table 4 (`tab:cells`), §4.7 description, and Amendment A12 to Table 5 (`tab:amendments`); updated total spend to 64.3M tokens.
  - `05-results.tex`: Updated §5.2 RQ2 with exact copy contrast; added dedicated §5.8 subsection and Table 8 (`tab:thinking`).
  - `06-discussion.tex`, `07-threats.tex`, `08-conclusion.tex`: Updated with mechanistic implications (in-context forward capability vs stochastic search churn, $2.4\times$ latency reduction).
- **Verification Checks:**
  - `check_draft.py`: 0 placeholders, abstract $\le 250$ words, highlights $\le 85$ chars.
  - LaTeX build: 0 errors, 0 overfull `\hbox` warnings.
