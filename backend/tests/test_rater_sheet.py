"""Tests for the defect-bank audit instrument (D13).

The instrument's whole value is that a rater cannot tell which items are real
defects and which were injected. That is a property of a generated file, so it
is testable, and it is the one thing here worth guarding: a leak would not raise
an error, it would quietly turn the audit into a formality.
"""

import csv
import importlib.util
import json
import sys
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parent.parent
STUDY_ROOT = BACKEND / "out_study"


def _load(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, BACKEND / relative)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


rater_sheet = _load("rater_sheet", "scripts/analysis/rater_sheet.py")
inject_defects = _load("inject_defects", "scripts/inject_defects.py")

def _usable_tier1() -> int:
    """Usable natural defects in the CURRENT bank -- the sheet's Tier-1 half."""
    bank = json.loads((STUDY_ROOT / "defect_bank.json").read_text(encoding="utf-8"))
    return sum(1 for e in bank.get("entries", []) if e.get("usable"))


needs_bank = pytest.mark.skipif(
    not (STUDY_ROOT / "defect_bank.json").exists(),
    reason="needs backend/out_study/defect_bank.json",
)


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    out = tmp_path_factory.mktemp("audit")
    rc = rater_sheet.build(str(STUDY_ROOT), str(out))
    assert rc == 0
    return out


# ── the sample ────────────────────────────────────────────────────────────────


@needs_bank
def test_the_sheet_is_the_whole_tier1_bank_plus_a_tier2_sample(built):
    key = json.loads((built / "key.json").read_text(encoding="utf-8"))["key"]
    tiers = [v["tier"] for v in key.values()]
    # Derived, not hard-coded: the sheet is DEFINED as every usable Tier-1
    # defect plus TIER2_SAMPLE injections, and the bank grows when Phase-A
    # dumps are added (11 -> 13 on 2026-08-26). Pinning 31 made this test fail
    # for the one reason that is not a defect.
    # ⚠ The COMPLETED D13 audit in out_study/audit/ is a 31-item sheet over the
    # 11-defect bank and must NOT be rebuilt; its 2 newest defects are unrated.
    assert tiers.count("tier1") == _usable_tier1(), "every usable natural defect must be rated"
    assert tiers.count("tier2") == rater_sheet.TIER2_SAMPLE
    assert len(key) == _usable_tier1() + rater_sheet.TIER2_SAMPLE


@needs_bank
def test_every_repair_operator_is_represented(built):
    """Round-robin sampling, so no operator's realism goes unrated."""
    key = json.loads((built / "key.json").read_text(encoding="utf-8"))["key"]
    sampled = {v["label"] for v in key.values() if v["tier"] == "tier2"}
    assert sampled == set(inject_defects.REPAIR_OPERATORS)


@needs_bank
def test_the_build_is_reproducible_from_its_seed(tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    rater_sheet.build(str(STUDY_ROOT), str(a))
    rater_sheet.build(str(STUDY_ROOT), str(b))
    assert (a / "rating_sheet.md").read_text(encoding="utf-8") == \
           (b / "rating_sheet.md").read_text(encoding="utf-8")


@needs_bank
def test_a_different_seed_gives_a_different_order(tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    rater_sheet.build(str(STUDY_ROOT), str(a), seed=1)
    rater_sheet.build(str(STUDY_ROOT), str(b), seed=2)
    assert (a / "rating_sheet.md").read_text(encoding="utf-8") != \
           (b / "rating_sheet.md").read_text(encoding="utf-8")


# ── blinding ──────────────────────────────────────────────────────────────────


def _items_only(built):
    """The rated items, with the rubric stripped.

    The rubric legitimately uses the word "injected" -- it is how the rater is
    told not to open the key. It is the ITEMS that must give nothing away, so
    that is what the leak guards read.
    """
    sheet = (built / "rating_sheet.md").read_text(encoding="utf-8")
    head, _, items = sheet.partition("\n---\n")
    assert "## I01" in items and "## I01" not in head
    return items


@needs_bank
def test_no_item_says_whether_it_is_real_or_injected(built):
    """The guard that matters. A leak here makes agreement meaningless."""
    items = _items_only(built)
    for leak in ("tier1", "tier2", "injected", "synthetic", "defect_bank",
                 "operator", "check_class", "supervisor"):
        assert leak not in items, f"a rating item leaks {leak!r}"


@needs_bank
def test_no_item_names_an_operator(built):
    items = _items_only(built)
    for op in inject_defects.OPERATORS:
        assert f" {op} " not in items and f"({op})" not in items, f"an item names {op}"


@needs_bank
def test_no_item_carries_a_defect_id_from_the_key(built):
    """defect ids encode phase, business and stage in one string."""
    key = json.loads((built / "key.json").read_text(encoding="utf-8"))["key"]
    items = _items_only(built)
    for entry in key.values():
        assert entry["source"] not in items, f"an item carries {entry['source']}"


@needs_bank
def test_the_key_is_written_separately_from_the_sheet(built):
    """It has to exist -- it just must not be in the rater's hands."""
    key = json.loads((built / "key.json").read_text(encoding="utf-8"))
    assert key["n_items"] == _usable_tier1() + rater_sheet.TIER2_SAMPLE
    assert set(key["key"]["I01"]) == {"tier", "label", "source"}
    sheet = (built / "rating_sheet.md").read_text(encoding="utf-8")
    assert "key.json" in sheet, "the sheet must tell the rater not to open it"


@needs_bank
def test_the_csv_has_one_blank_row_per_item(built):
    with open(built / "rating_sheet.csv", encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    n = _usable_tier1() + rater_sheet.TIER2_SAMPLE
    assert [r["item_id"] for r in rows] == [f"I{i:02d}" for i in range(1, n + 1)]
    assert all(r["rating"] == "" for r in rows)


# ── scoring ───────────────────────────────────────────────────────────────────


def _sheet(path, ratings):
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["item_id", "rating", "note"])
        for i, r in enumerate(ratings, 1):
            w.writerow([f"I{i:02d}", r, ""])


def test_kappa_is_one_when_the_raters_agree_and_both_use_two_categories():
    pairs = [("E", "E")] * 6 + [("T", "T")] * 4
    assert rater_sheet.kappa(pairs) == pytest.approx(1.0)


def test_kappa_matches_a_worked_example():
    """6 EE, 2 TT, 1 ET, 1 TE: po=0.80, pe=0.58, kappa=0.22/0.42."""
    pairs = [("E", "E")] * 6 + [("T", "T")] * 2 + [("E", "T"), ("T", "E")]
    assert rater_sheet.kappa(pairs) == pytest.approx(0.22 / 0.42, abs=1e-6)


def test_kappa_is_not_a_number_when_a_rater_never_varies():
    """Both raters saying E to everything is not perfect agreement, it is no
    information. Returning 1.0 there would be the flattering answer."""
    assert rater_sheet.kappa([("E", "E")] * 10) != rater_sheet.kappa(
        [("E", "E")] * 6 + [("T", "T")] * 4)
    value = rater_sheet.kappa([("E", "E")] * 10)
    assert value != value, "expected NaN for a degenerate table"


def test_score_excludes_u_and_says_so(tmp_path, capsys):
    a, b = tmp_path / "a.csv", tmp_path / "b.csv"
    _sheet(a, ["E", "E", "U", "T"])
    _sheet(b, ["E", "T", "E", "T"])

    rc = rater_sheet.score(str(tmp_path), str(a), str(b), n_boot=200)
    out = capsys.readouterr().out

    assert rc == 0
    assert "items rated by both  : 4" in out
    assert "excluded as U        : 1" in out
    assert "kappa computed on    : 3" in out
    assert "I03" in out, "the excluded item must be named"


def test_score_reports_disagreements_with_their_notes(tmp_path, capsys):
    a, b = tmp_path / "a.csv", tmp_path / "b.csv"
    with open(a, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["item_id", "rating", "note"])
        w.writerow(["I01", "E", "cites a review that does not exist"])
        w.writerow(["I02", "T", ""])
    _sheet(b, ["T", "T"])

    rater_sheet.score(str(tmp_path), str(a), str(b), n_boot=200)
    out = capsys.readouterr().out

    assert "disagreements (1)" in out
    assert "I01: A=E B=T" in out
    assert "cites a review that does not exist" in out


def test_score_refuses_an_unrecognised_rating(tmp_path, capsys):
    a, b = tmp_path / "a.csv", tmp_path / "b.csv"
    _sheet(a, ["E", "YES"])
    _sheet(b, ["E", "T"])
    assert rater_sheet.score(str(tmp_path), str(a), str(b), n_boot=10) == 1
    assert "unrecognised ratings" in capsys.readouterr().out


def test_score_needs_items_both_raters_actually_rated(tmp_path, capsys):
    a, b = tmp_path / "a.csv", tmp_path / "b.csv"
    _sheet(a, ["E", ""])
    _sheet(b, ["", "T"])
    assert rater_sheet.score(str(tmp_path), str(a), str(b), n_boot=10) == 1
    assert "no items rated by both raters" in capsys.readouterr().out


# ── fidelity: the item must be the whole defect ───────────────────────────────


@needs_bank
def test_a_multi_pattern_defect_renders_every_offending_pattern(built):
    """One banked defect spans six patterns.

    An earlier build re-derived "the first pattern with a problem" and showed
    one of them, which puts a materially easier question to the rater: one bad
    citation reads as a slip, six reads as a systematically ungrounded output.
    """
    bank = json.loads((STUDY_ROOT / "defect_bank.json").read_text(encoding="utf-8"))
    key = json.loads((built / "key.json").read_text(encoding="utf-8"))["key"]
    sheet = (built / "rating_sheet.md").read_text(encoding="utf-8")

    worst = max(
        (e for e in bank["entries"]
         if e.get("usable") and "missing_evidence_id" in (e.get("classes") or [])),
        key=lambda e: sum(1 for p in (e.get("facts") or {}).get("patterns", [])
                          if p.get("missing_evidence_ids")),
    )
    flagged = [p for p in worst["facts"]["patterns"] if p.get("missing_evidence_ids")]
    assert len(flagged) > 1, "fixture assumption: some defect spans several patterns"

    item_id = next(k for k, v in key.items() if v["source"] == worst["defect_id"])
    body = sheet.split(f"## {item_id}\n", 1)[1].split("\n## ", 1)[0]

    for pattern in flagged:
        for bad_id in pattern["missing_evidence_ids"]:
            assert bad_id in body, f"{item_id} omits unresolvable id {bad_id}"
    assert f"Across {len(flagged)} patterns" in body


@needs_bank
def test_every_tier1_item_reports_exactly_the_recorded_ids(built):
    """The rendered fact must equal the measurement, not a recomputation."""
    bank = json.loads((STUDY_ROOT / "defect_bank.json").read_text(encoding="utf-8"))
    key = json.loads((built / "key.json").read_text(encoding="utf-8"))["key"]
    sheet = (built / "rating_sheet.md").read_text(encoding="utf-8")
    by_source = {v["source"]: k for k, v in key.items()}

    checked = 0
    for entry in bank["entries"]:
        if not entry.get("usable") or entry["defect_id"] not in by_source:
            continue
        item_id = by_source[entry["defect_id"]]
        body = sheet.split(f"## {item_id}\n", 1)[1].split("\n## ", 1)[0]
        for pattern in (entry.get("facts") or {}).get("patterns", []):
            for bad_id in pattern.get("missing_evidence_ids", []):
                assert bad_id in body, f"{item_id} omits {bad_id}"
                checked += 1
    assert checked, "no missing-evidence ids were checked"


@needs_bank
def test_an_injected_item_shows_the_pattern_the_operator_touched(built):
    """Not whichever pattern happens to trip the check first in the base."""
    key = json.loads((built / "key.json").read_text(encoding="utf-8"))["key"]
    sheet = (built / "rating_sheet.md").read_text(encoding="utf-8")

    for item_id, meta in key.items():
        if meta["tier"] != "tier2" or meta["label"] not in ("O1", "O2"):
            continue
        dump_name, op = meta["source"].rsplit(":", 1)
        dump_dir = str(STUDY_ROOT / "A" / dump_name)
        base = inject_defects.state_from_dump(dump_dir)
        injected, descriptor = inject_defects.inject(op, base, seed=0)
        planted = descriptor.target.get("after") or descriptor.target.get("added_evidence_id")
        body = sheet.split(f"## {item_id}\n", 1)[1].split("\n## ", 1)[0]
        assert str(planted) in body, f"{item_id} does not show the injected id"
        return
    pytest.skip("no O1/O2 item in this sample")
