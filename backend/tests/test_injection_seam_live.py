"""One live trial through the wired regeneration seam (integration only).

Everything else about the seam is pinned without a network call: which prompt is
built, which payload the stage receives, what survives into the retried state.
The one thing those cannot show is that the assembled message list is *accepted*
by the provider and comes back schema-valid under a real arm.

It covers **every placement**, not just the P1 the core runs at. P2 and P3 put
the artifact in an *assistant* turn and then add a user turn after it, and P3
leaves two user turns adjacent -- shapes the production path never produces. If
a provider rejects one of them, it should surface here for a few cents rather
than 200 trials into an additional cell.

This is a smoke test, not a study trial. It writes nothing to ``out_study`` and
records nothing; it costs 1-3 calls per cell.

    cd backend
    python -m pytest tests/test_injection_seam_live.py -v -m integration

Skips automatically without OPENAI_API_KEY, and without the study dumps.
"""

import importlib.util
import os
import sys
from pathlib import Path

import pytest
from dotenv import load_dotenv

load_dotenv()

pytestmark = pytest.mark.integration

BACKEND = Path(__file__).resolve().parent.parent
STUDY_ROOT = BACKEND / "out_study"


def _load_module(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, BACKEND / relative)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


runner = _load_module("run_injection_study", "scripts/run_injection_study.py")
inject_defects = _load_module("inject_defects", "scripts/inject_defects.py")

needs_live = pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY") or not (STUDY_ROOT / "A").is_dir(),
    reason="needs OPENAI_API_KEY and backend/out_study/A",
)


@needs_live
@pytest.mark.parametrize("arm, placement", [
    ("A1", "P1"),   # the production path's own feedback, at the Tier-2 default
    ("A2", "P1"),   # the other half of the primary contrast
    ("A1", "P0"),   # artifact withheld -- the production placement
    ("A1", "P2"),   # artifact in an assistant turn
    ("A1", "P3"),   # assistant turn plus a marker, then the arm: two user turns
    ("A0", "P1"),   # no retry framing at all
    ("A3", "P0"),   # bare re-draw; the only cell A3 is defined in
])
def test_one_live_trial_returns_a_schema_valid_output(arm, placement):
    """One cell per defined shape, on a real reasoning-stage defect."""
    plan = [d for d in runner.build_plan(str(STUDY_ROOT))
            if d["runnable"] and inject_defects.STAGE[d["operator"]] == "reasoning_agent"]
    assert plan, "no applicable reasoning-stage defect"
    defect = plan[0]
    base = inject_defects.state_from_dump(defect["dump_dir"])
    injected, descriptor = inject_defects.inject(defect["operator"], base, seed=0)
    assert descriptor.applied

    row = runner.run_trial(defect, {"arm": arm, "placement": placement, "rep": 0},
                           base, injected, descriptor, "smoke", dry_run=False)

    assert row["status"] in ("ok", "status_error"), row.get("error_detail")
    if row["status"] == "status_error":
        pytest.skip("provider error during the smoke call, not a seam failure")

    # 1-3 calls, and the log must say which model actually served them (14.1).
    assert 1 <= row["attempts_made"] <= 3
    assert row["served_models"] and all(row["served_models"])
    # The scorer ran, which means the retried output validated against the
    # stage contract -- the arm's message list was accepted as a real prompt.
    # The class set comes from the scorer: a hand-typed set went stale once
    # already, when D18 added `deleted` and this line did not follow.
    assert row["outcome"]["outcome"] in runner.score_repair.OUTCOME_CLASSES
    assert isinstance(row["outcome"]["collateral"], bool)
    assert row["retried_output"] is not None
    # Downstream of the retried stage is cleared, never the stale dump values.
    assert row["downstream_state"]["strategy_output"] is None
    assert row["downstream_state"]["report_output"] is None
