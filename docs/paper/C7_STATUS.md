# C7 execution status — 2026-10-12

**The full experiment is running; no final estimate has been reported.**

- Local runtime: Qwen2.5-7B-Instruct Q4_K_M, Ollama 0.40.3, RTX 5060 Ti 16 GB,
  i7-14700KF and 32 GB RAM. The model is entirely on GPU; loaded size 6.6 GB,
  total observed GPU use about 8.3 GB. Context 32768, output cap 4096,
  seed 20261012, temperature 0, one request at a time.
- Original G2 **failed**: 8/10 repeated prompts were byte-identical; all ten
  token-count calibrations passed. [A11](C7_A11.md) records the switch from
  single draws to three repetitions before any final data.
- Schema pilot **passed**: 8/10 trials valid on their first call. The two
  failures hit the output cap and the context guard on schema correction.
  Preflight data remain separate from final estimates.
- Final plan: **138 defects, 930 trials** (414 A1, 414 A2, 102 A3), plus
  26 inapplicable and four context-excluded checkpoint rows. All arms of a
  defect execute contiguously in one session. The frozen Gemini core remains
  1167 trials. **426 offline tests pass**, 13 integration tests deselected.
- Final data: `backend/out_study/T2L/`; `run_header.json` records the frozen
  plan and runtime, `session.json` records the launch and design commit.
  The first six-trial block reproduced all six scores and measurements, with
  matching raw hashes/token counts, the expected model and one session.
- Local log: `backend/.venv/c7/full.stdout.log`; failures are in
  `full.stderr.log`. The launcher prevents idle sleep while it runs.
- Code, amendments and gate data were pushed before collection to branch
  **`codex/c7-local-replication`**, commit `37ee2e0` at launch. Because the copied
  repository's Git metadata lacks modification rights, publishing uses a
  separate writable checkout at `%LOCALAPPDATA%/CodexC7/research-checkout`.
  Existing journal drafts and unrelated local changes are preserved.

After completion: verify the entire checkpoint using `scripts/verify_c7.py`,
then analyse with `scripts/analysis/repair_analysis.py --cell c7`. Report the
schema-failure sensitivity, O1/severe split and paired Gemini comparison, then
publish data and update `RESULTS.md`. Local inference incurs **no API fees**;
its tokens are separate from the charged Gemini budget. The draft's C7
placeholders must await these verified results.

This machine uses the fresh `backend/.venv/Scripts/python.exe`; the copied
`backend/venv/` points to an absent installation from the former computer.
