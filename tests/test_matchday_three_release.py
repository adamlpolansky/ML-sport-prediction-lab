from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from epl_probability_lab import matchday_three_release as release
from epl_probability_lab.publication import inspect_paths

ROOT = Path(__file__).resolve().parents[1]


def _rows():
    return json.loads((ROOT / release.JSON_PATH).read_bytes())


def test_release_has_three_prospective_forecasts_and_seven_time_exclusions():
    rows = release.validate_release_tree(ROOT)
    assert [row["fixture_key"] for row in rows] == ["epl-mw03-08", "epl-mw03-09", "epl-mw03-10"]
    assert all(row["over_2_5_selected"] and row["btts_selected"] for row in rows)
    assert "43.9% | Away" in release.render_table(rows)
    assert rows[2]["p_home"] == pytest.approx(0.6286081445268492, abs=1e-14)


def test_generation_at_kickoff_is_rejected():
    rows = _rows()
    rows[0]["generated_at_utc"] = rows[0]["kickoff_utc"]
    with pytest.raises(release.MatchdayThreeError, match="not prospective"):
        release.validate_rows(rows)


def test_table_labels_under_and_btts_no_when_their_opposites_are_below_half():
    row = _rows()[0]
    row.update(p_over_2_5=0.4, p_btts=0.3, over_2_5_selected=True, btts_selected=True)
    table = release.render_table([row])
    assert "40.0% (Under)" in table
    assert "30.0% (No)" in table


@pytest.mark.parametrize("field", ["p_home", "p_over_2_5", "p_btts", "tail_mass"])
def test_one_probability_cannot_drift_from_coherent_score_distribution(field):
    rows = _rows()
    rows[0][field] += 0.001
    with pytest.raises(release.MatchdayThreeError, match="distribution mismatch"):
        release.validate_rows(rows)


def test_fixture_identity_and_extra_private_fields_fail_closed():
    rows = _rows()
    rows[0]["away_team"] = "Arsenal"
    with pytest.raises(release.MatchdayThreeError, match="identity changed"):
        release.validate_rows(rows)
    rows = _rows()
    rows[0]["fitted_coefficients"] = {"alpha": 1}
    with pytest.raises(release.MatchdayThreeError, match="schema changed"):
        release.validate_rows(rows)


@pytest.mark.parametrize(
    "field,value",
    [
        ("elo_k_factor", 21),
        ("mw3_results_used", 1),
        ("included_fixtures", 10),
        ("elo_total_change", 1.0),
        ("model_refit_performed", True),
        ("source_fetched_at_utc", "2026-09-07T00:00:00Z"),
    ],
)
def test_update_manifest_protects_frozen_model_and_state_cutoffs(field, value):
    update = json.loads((ROOT / release.UPDATE_PATH).read_bytes())
    coverage = json.loads((ROOT / release.COVERAGE_PATH).read_bytes())
    update[field] = value
    with pytest.raises(release.MatchdayThreeError):
        release.validate_update(update, _rows(), coverage)


def test_table_and_machine_artifacts_are_checked_by_publication_guard():
    for path in release.PUBLIC_ARTIFACT_SHA256:
        content = (ROOT / path).read_bytes()
        assert inspect_paths([(path.as_posix(), content)]) == []
        assert inspect_paths([(path.as_posix(), content + b" ")])


def test_duplicate_rows_and_changed_selection_are_rejected():
    rows = _rows()
    rows[1] = copy.deepcopy(rows[0])
    with pytest.raises(release.MatchdayThreeError, match="duplicate"):
        release.validate_rows(rows)
    rows = _rows()
    rows[0]["over_2_5_selected"] = False
    with pytest.raises(release.MatchdayThreeError, match="threshold"):
        release.validate_rows(rows)
