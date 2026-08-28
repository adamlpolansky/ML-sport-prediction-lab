"""Reproduce and validate the public EPL 2026/27 model-results tracker."""

from __future__ import annotations

import argparse
import csv
import io
import json
import math
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

INCUMBENT_FORECAST_PATH = Path("forecasts/2026-27/matchday-01/forecast.json")
CHALLENGER_FORECAST_PATH = Path(
    "forecasts/2026-27/matchday-01/challengers/elo-poisson-v1/forecast.json"
)
MW2_CHALLENGER_FORECAST_PATH = Path(
    "forecasts/2026-27/matchday-02/challengers/elo-poisson-v1-post-mw1/forecast.json"
)
RESULTS_DIRECTORY = Path("forecasts/2026-27/matchday-01/results")
RESULTS_CSV_PATH = RESULTS_DIRECTORY / "results.csv"
MODEL_SCORES_CSV_PATH = RESULTS_DIRECTORY / "model_scores.csv"
MODEL_SUMMARY_CSV_PATH = RESULTS_DIRECTORY / "model_summary.csv"
RESULTS_JSON_PATH = RESULTS_DIRECTORY / "results.json"
RESULTS_README_PATH = RESULTS_DIRECTORY / "README.md"
RESULTS_PROVENANCE_PATH = RESULTS_DIRECTORY / "provenance.md"
TRACKING_DIRECTORY = Path("forecasts/2026-27/tracking")
TRACKER_CSV_PATH = TRACKING_DIRECTORY / "model_performance.csv"
TRACKER_JSON_PATH = TRACKING_DIRECTORY / "model_performance.json"
TRACKER_README_PATH = TRACKING_DIRECTORY / "README.md"

RESULT_SOURCE = {
    "repository": "openfootball/england",
    "commit": "836b1947fa4089c86b6064f821eee7de926a7a3f",
    "path": "2026-27/1-premierleague.txt",
    "blob": "fffa0b4626672b9e1e7aaea60554bc0ae8b1a363",
    "download_sha256": "0c552804d8b93cf6e0fb27ea46dc2af67829c815f8445b84c6eebf94c4bedbc0",
    "license": "CC0-1.0",
    "data_as_of": "2026-08-24",
}

MATCHWEEK_1_RESULTS = (
    ("epl-mw01-01", "Arsenal", "Coventry City", 3, 0),
    ("epl-mw01-02", "Hull City", "Manchester United", 2, 0),
    ("epl-mw01-03", "Everton", "Crystal Palace", 2, 0),
    ("epl-mw01-04", "Ipswich Town", "Sunderland", 2, 1),
    ("epl-mw01-05", "Nottingham Forest", "Leeds United", 0, 1),
    ("epl-mw01-06", "Brentford", "Tottenham Hotspur", 3, 0),
    ("epl-mw01-07", "Brighton & Hove Albion", "Aston Villa", 4, 0),
    ("epl-mw01-08", "Manchester City", "AFC Bournemouth", 2, 1),
    ("epl-mw01-09", "Newcastle United", "Liverpool", 2, 2),
    ("epl-mw01-10", "Fulham", "Chelsea", 2, 3),
)

RESULT_FIELDS = (
    "fixture_key",
    "kickoff_utc",
    "home_team",
    "away_team",
    "home_goals",
    "away_goals",
    "outcome",
)
MODEL_SCORE_FIELDS = (
    "fixture_key",
    "model_family",
    "model_id",
    "actual_outcome",
    "predicted_outcome",
    "p_home",
    "p_draw",
    "p_away",
    "p_actual",
    "hda_log_loss",
    "hda_brier_score",
    "top1_correct",
    "expected_home_goals",
    "expected_away_goals",
    "goal_mae",
)
MODEL_SUMMARY_FIELDS = (
    "season",
    "matchweek",
    "model_family",
    "model_id",
    "fixtures_scored",
    "hda_log_loss",
    "hda_brier_score",
    "hda_top1_accuracy",
    "goal_mae",
)
TRACKER_FIELDS = (
    "season",
    "matchweek",
    "model_family",
    "model_id",
    "forecast_status",
    "result_status",
    "fixtures_forecast",
    "fixtures_scored",
    "hda_log_loss",
    "hda_brier_score",
    "hda_top1_accuracy",
    "goal_mae",
)


class ResultsTrackerError(ValueError):
    """Raised when the public results pack or tracker is inconsistent."""


def _outcome(home_goals: int, away_goals: int) -> str:
    if home_goals > away_goals:
        return "H"
    if home_goals < away_goals:
        return "A"
    return "D"


def _round(value: float) -> float:
    return round(value, 12)


def _load_forecasts(content: bytes, *, challenger: bool) -> list[dict[str, Any]]:
    try:
        rows = json.loads(content.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ResultsTrackerError("forecast JSON is invalid") from exc
    if not isinstance(rows, list) or len(rows) != 10:
        raise ResultsTrackerError("each scored forecast must contain ten rows")
    normalized = []
    for row in rows:
        if not isinstance(row, dict):
            raise ResultsTrackerError("forecast rows must be objects")
        try:
            normalized.append(
                {
                    "fixture_key": row["fixture_key"],
                    "kickoff_utc": row["kickoff_utc"],
                    "home_team": row["home_team"],
                    "away_team": row["away_team"],
                    "model_id": row["model_id"],
                    "model_family": "elo-poisson" if challenger else "dynamic-dixon-coles",
                    "p_home": float(row["p_home"] if challenger else row["p_home_win"]),
                    "p_draw": float(row["p_draw"]),
                    "p_away": float(row["p_away"] if challenger else row["p_away_win"]),
                    "expected_home_goals": float(
                        row["lambda_home"] if challenger else row["expected_home_goals"]
                    ),
                    "expected_away_goals": float(
                        row["lambda_away"] if challenger else row["expected_away_goals"]
                    ),
                }
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ResultsTrackerError("forecast row cannot be normalized") from exc
    if len({row["fixture_key"] for row in normalized}) != 10:
        raise ResultsTrackerError("forecast fixture keys are not unique")
    return normalized


def build_results(incumbent_rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    forecasts = {str(row["fixture_key"]): row for row in incumbent_rows}
    rows = []
    for fixture_key, home_team, away_team, home_goals, away_goals in MATCHWEEK_1_RESULTS:
        forecast = forecasts.get(fixture_key)
        if forecast is None or (
            forecast["home_team"],
            forecast["away_team"],
        ) != (home_team, away_team):
            raise ResultsTrackerError("result and forecast fixture identities differ")
        rows.append(
            {
                "fixture_key": fixture_key,
                "kickoff_utc": forecast["kickoff_utc"],
                "home_team": home_team,
                "away_team": away_team,
                "home_goals": home_goals,
                "away_goals": away_goals,
                "outcome": _outcome(home_goals, away_goals),
            }
        )
    return rows


def score_model(
    forecasts: Sequence[Mapping[str, Any]],
    results: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    by_key = {str(row["fixture_key"]): row for row in forecasts}
    scored = []
    for result in results:
        forecast = by_key.get(str(result["fixture_key"]))
        if forecast is None or (
            forecast["home_team"],
            forecast["away_team"],
        ) != (result["home_team"], result["away_team"]):
            raise ResultsTrackerError("model and result fixture identities differ")
        probabilities = {
            "H": float(forecast["p_home"]),
            "D": float(forecast["p_draw"]),
            "A": float(forecast["p_away"]),
        }
        if any(not math.isfinite(value) or value <= 0.0 for value in probabilities.values()):
            raise ResultsTrackerError("model probabilities must be finite and positive")
        if not math.isclose(math.fsum(probabilities.values()), 1.0, abs_tol=1e-12):
            raise ResultsTrackerError("model probabilities must sum to one")
        actual = str(result["outcome"])
        predicted = max(("H", "D", "A"), key=probabilities.__getitem__)
        goal_mae = (
            abs(float(forecast["expected_home_goals"]) - int(result["home_goals"]))
            + abs(float(forecast["expected_away_goals"]) - int(result["away_goals"]))
        ) / 2.0
        scored.append(
            {
                "fixture_key": result["fixture_key"],
                "model_family": forecast["model_family"],
                "model_id": forecast["model_id"],
                "actual_outcome": actual,
                "predicted_outcome": predicted,
                "p_home": _round(probabilities["H"]),
                "p_draw": _round(probabilities["D"]),
                "p_away": _round(probabilities["A"]),
                "p_actual": _round(probabilities[actual]),
                "hda_log_loss": _round(-math.log(probabilities[actual])),
                "hda_brier_score": _round(
                    math.fsum(
                        (probability - float(outcome == actual)) ** 2
                        for outcome, probability in probabilities.items()
                    )
                ),
                "top1_correct": int(predicted == actual),
                "expected_home_goals": _round(float(forecast["expected_home_goals"])),
                "expected_away_goals": _round(float(forecast["expected_away_goals"])),
                "goal_mae": _round(goal_mae),
            }
        )
    return scored


def summarize_model(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    if len(rows) != 10:
        raise ResultsTrackerError("model summary requires ten scored fixtures")
    model_ids = {str(row["model_id"]) for row in rows}
    families = {str(row["model_family"]) for row in rows}
    if len(model_ids) != 1 or len(families) != 1:
        raise ResultsTrackerError("model summary rows do not share one identity")
    count = len(rows)
    return {
        "season": "2026-27",
        "matchweek": 1,
        "model_family": next(iter(families)),
        "model_id": next(iter(model_ids)),
        "fixtures_scored": count,
        "hda_log_loss": _round(math.fsum(float(row["hda_log_loss"]) for row in rows) / count),
        "hda_brier_score": _round(math.fsum(float(row["hda_brier_score"]) for row in rows) / count),
        "hda_top1_accuracy": _round(math.fsum(int(row["top1_correct"]) for row in rows) / count),
        "goal_mae": _round(math.fsum(float(row["goal_mae"]) for row in rows) / count),
    }


def build_tracker(
    summaries: Sequence[Mapping[str, Any]],
    mw2_challenger_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    if len(mw2_challenger_rows) != 10:
        raise ResultsTrackerError("MW2 tracker requires ten published challenger forecasts")
    by_family = {str(row["model_family"]): row for row in summaries}
    if set(by_family) != {"dynamic-dixon-coles", "elo-poisson"}:
        raise ResultsTrackerError("tracker requires both MW1 model families")
    rows = []
    for family in ("dynamic-dixon-coles", "elo-poisson"):
        summary = by_family[family]
        rows.append(
            {
                "season": "2026-27",
                "matchweek": 1,
                "model_family": family,
                "model_id": summary["model_id"],
                "forecast_status": "published_pre_match",
                "result_status": "scored",
                "fixtures_forecast": 10,
                "fixtures_scored": 10,
                "hda_log_loss": summary["hda_log_loss"],
                "hda_brier_score": summary["hda_brier_score"],
                "hda_top1_accuracy": summary["hda_top1_accuracy"],
                "goal_mae": summary["goal_mae"],
            }
        )
    rows.extend(
        (
            {
                "season": "2026-27",
                "matchweek": 2,
                "model_family": "dynamic-dixon-coles",
                "model_id": "dynamic-dixon-coles-incumbent-2026-27-v1",
                "forecast_status": "not_released",
                "result_status": "not_applicable",
                "fixtures_forecast": 0,
                "fixtures_scored": 0,
                "hda_log_loss": None,
                "hda_brier_score": None,
                "hda_top1_accuracy": None,
                "goal_mae": None,
            },
            {
                "season": "2026-27",
                "matchweek": 2,
                "model_family": "elo-poisson",
                "model_id": mw2_challenger_rows[0]["model_id"],
                "forecast_status": "published_pre_match",
                "result_status": "pending",
                "fixtures_forecast": 10,
                "fixtures_scored": 0,
                "hda_log_loss": None,
                "hda_brier_score": None,
                "hda_top1_accuracy": None,
                "goal_mae": None,
            },
        )
    )
    return rows


def _csv_bytes(rows: Sequence[Mapping[str, Any]], fields: Sequence[str]) -> bytes:
    handle = io.StringIO(newline="")
    writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return handle.getvalue().encode("utf-8")


def _json_bytes(value: object) -> bytes:
    return (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def expected_artifacts(
    incumbent_content: bytes,
    challenger_content: bytes,
    mw2_challenger_content: bytes,
) -> dict[Path, bytes]:
    incumbent = _load_forecasts(incumbent_content, challenger=False)
    challenger = _load_forecasts(challenger_content, challenger=True)
    mw2_challenger = _load_forecasts(mw2_challenger_content, challenger=True)
    results = build_results(incumbent)
    incumbent_scores = score_model(incumbent, results)
    challenger_scores = score_model(challenger, results)
    scores = incumbent_scores + challenger_scores
    summaries = [summarize_model(incumbent_scores), summarize_model(challenger_scores)]
    tracker = build_tracker(summaries, mw2_challenger)
    results_payload = {
        "schema_version": "epl-model-results/v1",
        "competition": "EPL",
        "season": "2026-27",
        "matchweek": 1,
        "result_source": RESULT_SOURCE,
        "metric_definitions": {
            "hda_log_loss": (
                "mean negative natural log probability assigned to the actual H/D/A outcome"
            ),
            "hda_brier_score": "mean sum of squared errors across H, D and A (lower is better)",
            "hda_top1_accuracy": "share where the highest-probability H/D/A outcome was correct",
            "goal_mae": "mean absolute error across the two team goal expectations",
        },
        "results": results,
        "model_scores": scores,
        "model_summary": summaries,
    }
    tracker_payload = {
        "schema_version": "epl-model-performance-tracker/v1",
        "competition": "EPL",
        "season": "2026-27",
        "rows": tracker,
    }
    return {
        RESULTS_CSV_PATH: _csv_bytes(results, RESULT_FIELDS),
        MODEL_SCORES_CSV_PATH: _csv_bytes(scores, MODEL_SCORE_FIELDS),
        MODEL_SUMMARY_CSV_PATH: _csv_bytes(summaries, MODEL_SUMMARY_FIELDS),
        RESULTS_JSON_PATH: _json_bytes(results_payload),
        TRACKER_CSV_PATH: _csv_bytes(tracker, TRACKER_FIELDS),
        TRACKER_JSON_PATH: _json_bytes(tracker_payload),
    }


def validate_release_contents(contents: Mapping[str | Path, bytes]) -> dict[Path, bytes]:
    normalized = {Path(path).as_posix(): value for path, value in contents.items()}
    source_paths = (
        INCUMBENT_FORECAST_PATH,
        CHALLENGER_FORECAST_PATH,
        MW2_CHALLENGER_FORECAST_PATH,
    )
    required_paths = (
        *source_paths,
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
    missing = [path.as_posix() for path in required_paths if path.as_posix() not in normalized]
    if missing:
        raise ResultsTrackerError(f"results tracker files are missing: {', '.join(missing)}")
    expected = expected_artifacts(*(normalized[path.as_posix()] for path in source_paths))
    for path, content in expected.items():
        if normalized[path.as_posix()] != content:
            raise ResultsTrackerError(f"derived artifact does not reproduce: {path.as_posix()}")
    result_readme = normalized[RESULTS_README_PATH.as_posix()].decode("utf-8")
    tracker_readme = normalized[TRACKER_README_PATH.as_posix()].decode("utf-8")
    provenance = normalized[RESULTS_PROVENANCE_PATH.as_posix()].decode("utf-8")
    if "Lower is better" not in result_readme or "10/10" not in result_readme:
        raise ResultsTrackerError("results README is missing metric interpretation or coverage")
    if "not_released" not in tracker_readme or "pending" not in tracker_readme:
        raise ResultsTrackerError("tracker README is missing explicit unavailable states")
    for commitment in (
        RESULT_SOURCE["commit"],
        RESULT_SOURCE["blob"],
        RESULT_SOURCE["download_sha256"],
    ):
        if commitment not in provenance:
            raise ResultsTrackerError("result provenance commitment is missing")
    return expected


def validate_release_tree(root: Path) -> dict[Path, bytes]:
    paths = (
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
    return validate_release_contents({path: (root / path).read_bytes() for path in paths})


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    artifacts = validate_release_tree(args.root.resolve())
    print(f"results tracker validation: PASS ({len(artifacts)} regenerated artifacts)")


if __name__ == "__main__":
    main()
