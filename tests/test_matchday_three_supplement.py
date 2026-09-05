"""Regression tests for publication without any third-round outcome evaluation."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from epl_probability_lab import matchday_three_release as parent
from epl_probability_lab import matchday_three_supplement as supplement
from epl_probability_lab.publication import inspect_paths, scan_tree

ROOT = Path(__file__).resolve().parents[1]
ORIGINAL_HASHES = {
    "forecasts/2026-27/matchday-03/challengers/elo-poisson-v1-post-mw2/forecast.json": (
        "9b80445f7f8a25874f19cdb35850a8312e5dcc8557e6e6324ae0fc6302e80243"
    ),
    "forecasts/2026-27/tracking/betting_selections.csv": (
        "14d24e6de48a3413fa08c0bb5e1aa54bf8fbc83d3bbb3348a0d2981353a8d1f9"
    ),
    "forecasts/2026-27/tracking/goal_deviations.csv": (
        "ae3257c2ddf69c4991c08e3bae12f0ba9cc92e0043fe5f432f45985d3a900e4a"
    ),
    "forecasts/2026-27/matchday-03/challengers/elo-poisson-v1-post-mw2/coverage.json": (
        "f49a0137df0d0211e018b08479f4d7ac9782dae7e264daabb4fc18595bca301f"
    ),
    "forecasts/2026-27/matchday-03/challengers/elo-poisson-v1-post-mw2/update.json": (
        "1743d78336cc304fbd2809de3fee7d735ac1654e8111feb521685a3a069b331e"
    ),
    "forecasts/2026-27/tracking/model_performance.csv": (
        "17ad96b83b2948bc4f8f17bce083c3e8650f57f0872459e6e728a60a76f3839b"
    ),
    "forecasts/2026-27/tracking/dc_mw1_goal_markets.json": (
        "41c1c1c129be9d9e4e43fff18a4ee478f9f49f7547b3561d63a49853dcadcd98"
    ),
    "forecasts/2026-27/tracking/model_performance.json": (
        "c69439ec1d1de91e908eab652a33a4d9226832b8760b7fc5c5be1444663f16ec"
    ),
    "forecasts/2026-27/matchday-03/challengers/elo-poisson-v1-post-mw2/forecast.csv": (
        "57ff33607450f3fbf77cd0701d23bec2ded43fcd62623a4c3bcffb20acb85316"
    ),
    "forecasts/2026-27/tracking/cumulative_performance.csv": (
        "429db712af49e50eb9647e2cf5b5b050a93bd872c28c62fe0222cd8df973e409"
    ),
}


def _rows():
    return json.loads((ROOT / supplement.JSON_PATH).read_bytes())


def _contents():
    return {path: (ROOT / path).read_bytes() for path in supplement.required_paths()}


def test_seven_retrospective_rows_complete_ten_unique_fixtures_without_scoring():
    rows = supplement.validate_tree(ROOT)
    original = parent.validate_release_tree(ROOT)
    assert len(rows) == 7 and len(original) == 3
    assert len({row["fixture_key"] for row in rows + original}) == 10
    assert all(row["artifact_status"] == supplement.STATUS for row in rows)
    manifest = json.loads((ROOT / supplement.MANIFEST_PATH).read_bytes())
    assert manifest["evaluation_performed"] is False
    assert manifest["mw3_results_used"] == 0
    assert manifest["model_refit_performed"] is False
    assert manifest["elo_update_performed"] is False
    assert manifest["evaluation_status"] == "not_evaluated_by_user_request"


def test_original_forecasts_and_every_machine_tracker_file_stay_byte_identical():
    for path, expected in ORIGINAL_HASHES.items():
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == expected, path


def test_retrospective_rows_are_never_accepted_as_original_prospective_predictions():
    with pytest.raises(parent.MatchdayThreeError):
        parent.validate_rows(_rows())


@pytest.mark.parametrize(
    "field,value",
    [
        ("generated_at_utc", "2026-09-01T11:23:47Z"),
        ("information_cutoff_utc", "2026-09-05T15:00:00Z"),
        ("artifact_status", parent.STATUS),
        ("model_id", "another-model"),
        ("away_team", "Another Club"),
        ("p_home", 0.99),
        ("p_over_2_5", 0.99),
        ("p_btts", float("nan")),
        ("lambda_home", -1),
        ("home_neutral_reentry", True),
        ("btts_selected", False),
    ],
)
def test_changed_state_identity_timestamp_or_probability_fails(field, value):
    rows = _rows()
    rows[1][field] = value
    with pytest.raises(supplement.SupplementError):
        supplement.validate_rows(rows)


@pytest.mark.parametrize(
    "field", ["actual_home_goals", "actual_outcome", "accuracy", "hda_log_loss"]
)
def test_results_and_performance_fields_are_forbidden(field):
    rows = _rows()
    rows[0][field] = 1
    with pytest.raises(supplement.SupplementError, match="forecast-only schema"):
        supplement.validate_rows(rows)


def test_individual_artifact_guard_rejects_changed_bytes():
    for path in supplement.HASHES:
        content = (ROOT / path).read_bytes()
        assert not inspect_paths([(str(path), content)])
        assert inspect_paths([(str(path), content + b" ")])


def test_full_publication_guard_accepts_only_complete_consistent_release():
    assert scan_tree(ROOT) == []
    contents = _contents()
    del contents[supplement.CSV_PATH]
    with pytest.raises(supplement.SupplementError, match="missing"):
        supplement.validate_contents(contents)


def test_crlf_markdown_is_portable_but_table_changes_are_rejected():
    contents = _contents()
    for path in (supplement.README_PATH, parent.ROOT_README_PATH):
        contents[path] = contents[path].replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
    assert len(supplement.validate_contents(contents)) == 7
    contents[supplement.README_PATH] = contents[supplement.README_PATH].replace(
        b"H/D/A pick", b"Wrong pick"
    )
    with pytest.raises(supplement.SupplementError, match="table mismatch"):
        supplement.validate_contents(contents)


def test_parent_manifest_cannot_be_changed_to_imply_a_new_elo_update():
    contents = _contents()
    contents[parent.UPDATE_PATH] += b" "
    with pytest.raises(supplement.SupplementError, match="original prospective"):
        supplement.validate_contents(contents)
