from __future__ import annotations

import csv
import io
import json
from pathlib import Path

import pytest

from epl_probability_lab.publication import inspect_paths
from epl_probability_lab.results_tracker import (
    CHALLENGER_FORECAST_PATH,
    INCUMBENT_FORECAST_PATH,
    MODEL_SCORES_CSV_PATH,
    MODEL_SUMMARY_CSV_PATH,
    MW2_CHALLENGER_FORECAST_PATH,
    RESULTS_CSV_PATH,
    RESULTS_JSON_PATH,
    RESULTS_PROVENANCE_PATH,
    RESULTS_README_PATH,
    TRACKER_CSV_PATH,
    TRACKER_JSON_PATH,
    TRACKER_README_PATH,
    ResultsTrackerError,
    validate_release_contents,
    validate_release_tree,
)

ROOT = Path(__file__).resolve().parents[1]
ALL_PATHS = (
    INCUMBENT_FORECAST_PATH,
    CHALLENGER_FORECAST_PATH,
    MW2_CHALLENGER_FORECAST_PATH,
    RESULTS_CSV_PATH,
    MODEL_SCORES_CSV_PATH,
    MODEL_SUMMARY_CSV_PATH,
    RESULTS_JSON_PATH,
    RESULTS_README_PATH,
    RESULTS_PROVENANCE_PATH,
    TRACKER_CSV_PATH,
    TRACKER_JSON_PATH,
    TRACKER_README_PATH,
)


def test_committed_results_pack_and_tracker_reproduce() -> None:
    regenerated = validate_release_tree(ROOT)
    assert len(regenerated) == 6

    payload = json.loads((ROOT / RESULTS_JSON_PATH).read_text(encoding="utf-8"))
    assert len(payload["results"]) == 10
    assert len(payload["model_scores"]) == 20
    summaries = {row["model_family"]: row for row in payload["model_summary"]}
    assert summaries["dynamic-dixon-coles"]["hda_top1_accuracy"] == 0.6
    assert summaries["elo-poisson"]["hda_top1_accuracy"] == 0.5
    assert summaries["elo-poisson"]["hda_log_loss"] == pytest.approx(0.947534657838)


def test_tracker_preserves_pending_and_not_released_as_null() -> None:
    payload = json.loads((ROOT / TRACKER_JSON_PATH).read_text(encoding="utf-8"))
    mw2 = [row for row in payload["rows"] if row["matchweek"] == 2]
    assert {row["result_status"] for row in mw2} == {"pending", "not_applicable"}
    assert all(row["hda_log_loss"] is None for row in mw2)
    assert sum(row["fixtures_forecast"] for row in mw2) == 10


def test_tracker_csv_has_four_explicit_model_matchweek_rows() -> None:
    rows = list(csv.DictReader(io.StringIO((ROOT / TRACKER_CSV_PATH).read_text(encoding="utf-8"))))
    assert len(rows) == 4
    assert {(row["matchweek"], row["model_family"]) for row in rows} == {
        ("1", "dynamic-dixon-coles"),
        ("1", "elo-poisson"),
        ("2", "dynamic-dixon-coles"),
        ("2", "elo-poisson"),
    }


def test_results_pack_rejects_a_changed_metric() -> None:
    contents = {path: (ROOT / path).read_bytes() for path in ALL_PATHS}
    contents[MODEL_SUMMARY_CSV_PATH] = contents[MODEL_SUMMARY_CSV_PATH].replace(
        b"0.949651401679", b"0.100000000000", 1
    )
    with pytest.raises(ResultsTrackerError, match="does not reproduce"):
        validate_release_contents(contents)


def test_publication_guard_accepts_exact_result_and_tracker_artifacts() -> None:
    for path in (
        RESULTS_CSV_PATH,
        MODEL_SCORES_CSV_PATH,
        MODEL_SUMMARY_CSV_PATH,
        RESULTS_JSON_PATH,
        TRACKER_CSV_PATH,
        TRACKER_JSON_PATH,
    ):
        assert inspect_paths([(path.as_posix(), (ROOT / path).read_bytes())]) == []
