"""Reproduce and validate the public EPL 2026/27 model-results tracker."""

from __future__ import annotations

import argparse
import csv
import hashlib
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
MW3_CHALLENGER_FORECAST_PATH = Path(
    "forecasts/2026-27/matchday-03/challengers/elo-poisson-v1-post-mw2/forecast.json"
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
BETTING_SELECTIONS_CSV_PATH = TRACKING_DIRECTORY / "betting_selections.csv"
CUMULATIVE_CSV_PATH = TRACKING_DIRECTORY / "cumulative_performance.csv"
GOAL_DEVIATIONS_CSV_PATH = TRACKING_DIRECTORY / "goal_deviations.csv"
DC_SOURCE_PATH = TRACKING_DIRECTORY / "dc_mw1_goal_markets.json"
DC_SOURCE_SHA256 = "41c1c1c129be9d9e4e43fff18a4ee478f9f49f7547b3561d63a49853dcadcd98"
MW2_RESULTS_DIRECTORY = Path("forecasts/2026-27/matchday-02/results")
MW2_RESULTS_CSV_PATH = MW2_RESULTS_DIRECTORY / "results.csv"
MW2_MODEL_SCORES_CSV_PATH = MW2_RESULTS_DIRECTORY / "model_scores.csv"
MW2_MODEL_SUMMARY_CSV_PATH = MW2_RESULTS_DIRECTORY / "model_summary.csv"
MW2_RESULTS_JSON_PATH = MW2_RESULTS_DIRECTORY / "results.json"
MW2_RESULTS_README_PATH = MW2_RESULTS_DIRECTORY / "README.md"
MW2_RESULTS_PROVENANCE_PATH = MW2_RESULTS_DIRECTORY / "provenance.md"

MW2_RESULT_SOURCE = {
    "repository": "openfootball/england",
    "commit": "0690446f794fde748ea4b994244def699c6a65b2",
    "path": "2026-27/1-premierleague.txt",
    "blob": "dec39f0aa20d4ea5653ecfe4257bc7910c00e0eb",
    "download_sha256": "10d40e1e7a17e90b64973b83fe2ea78c672819372a186fe87a80b17f4c7c575a",
    "license": "CC0-1.0",
    "data_as_of": "2026-09-01",
}
THRESHOLD_RULE = {
    "threshold": 0.5,
    "comparison": "strictly_greater_than",
    "markets": ["over_2_5", "btts"],
    "selection": "YES when P(YES) > 0.5; NO when P(YES) < 0.5; no selection at exactly 0.5",
    "hda_rule": "highest-probability H/D/A outcome for ALL fixtures, without a threshold",
    "probability_precision": "selection at full precision; p_yes export rounded to 12 decimals",
    "rule_specified_on": "2026-09-05",
    "evaluation_status": "retrospective_user_rule_not_preregistered",
    "profitability": "unavailable_without_odds_and_stakes",
}

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
MATCHWEEK_2_RESULTS = (
    ("epl-mw02-01", "Crystal Palace", "Manchester City", 1, 4),
    ("epl-mw02-02", "Liverpool", "Nottingham Forest", 2, 2),
    ("epl-mw02-03", "AFC Bournemouth", "Everton", 1, 1),
    ("epl-mw02-04", "Coventry City", "Hull City", 0, 1),
    ("epl-mw02-05", "Tottenham Hotspur", "Newcastle United", 0, 2),
    ("epl-mw02-06", "Chelsea", "Brighton & Hove Albion", 4, 3),
    ("epl-mw02-07", "Leeds United", "Brentford", 1, 1),
    ("epl-mw02-08", "Sunderland", "Fulham", 1, 0),
    ("epl-mw02-09", "Manchester United", "Ipswich Town", 5, 2),
    ("epl-mw02-10", "Aston Villa", "Arsenal", 0, 1),
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
MARKET_FIELDS = tuple(
    f"{market}_{field}"
    for market in ("over_2_5", "btts")
    for field in ("available", "selected", "won", "lost", "hit_rate", "coverage")
)
EXTRA_METRIC_FIELDS = ("hda_correct", "goal_bias", "total_goals_mae", *MARKET_FIELDS)
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
    *EXTRA_METRIC_FIELDS,
)
BETTING_FIELDS = (
    "season",
    "matchweek",
    "fixture_key",
    "model_family",
    "model_id",
    "home_team",
    "away_team",
    "market",
    "p_yes",
    "p_selected",
    "predicted_yes",
    "selection",
    "observed_yes",
    "selected",
    "won",
    "probability_method",
    "retrospectively_derived",
)
CUMULATIVE_FIELDS = (
    "season",
    "model_family",
    "model_ids",
    "matchweeks_scored",
    "fixtures_scored",
    "hda_log_loss",
    "hda_brier_score",
    "hda_top1_accuracy",
    "goal_mae",
    *EXTRA_METRIC_FIELDS,
)
GOAL_DEVIATION_FIELDS = (
    "season",
    "matchweek",
    "fixture_key",
    "model_family",
    "model_id",
    "home_team",
    "away_team",
    "home_goals",
    "away_goals",
    "expected_home_goals",
    "expected_away_goals",
    "home_error",
    "away_error",
    "home_absolute_error",
    "away_absolute_error",
    "actual_total_goals",
    "expected_total_goals",
    "total_goal_error",
    "goal_mae",
    "goal_bias",
    "total_goals_mae",
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


def _load_forecasts(
    content: bytes, *, challenger: bool, expected_count: int = 10
) -> list[dict[str, Any]]:
    try:
        rows = json.loads(content.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ResultsTrackerError("forecast JSON is invalid") from exc
    if not isinstance(rows, list) or len(rows) != expected_count:
        raise ResultsTrackerError(f"forecast must contain {expected_count} rows")
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
    if len({row["fixture_key"] for row in normalized}) != expected_count:
        raise ResultsTrackerError("forecast fixture keys are not unique")
    return normalized


def build_results(
    incumbent_rows: Sequence[Mapping[str, Any]],
    result_contract: Sequence[tuple[str, str, str, int, int]] = MATCHWEEK_1_RESULTS,
) -> list[dict[str, Any]]:
    forecasts = {str(row["fixture_key"]): row for row in incumbent_rows}
    rows = []
    for fixture_key, home_team, away_team, home_goals, away_goals in result_contract:
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
    if len(by_key) != len(forecasts) or len({row["fixture_key"] for row in results}) != len(
        results
    ):
        raise ResultsTrackerError("model and result fixture keys must be unique")
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
        home_goals, away_goals = result["home_goals"], result["away_goals"]
        if (
            isinstance(home_goals, bool)
            or isinstance(away_goals, bool)
            or not isinstance(home_goals, int)
            or not isinstance(away_goals, int)
            or min(home_goals, away_goals) < 0
            or actual != _outcome(home_goals, away_goals)
        ):
            raise ResultsTrackerError("result score and outcome are inconsistent")
        if any(
            not math.isfinite(float(forecast[field])) or float(forecast[field]) < 0
            for field in ("expected_home_goals", "expected_away_goals")
        ):
            raise ResultsTrackerError("goal expectations must be finite and nonnegative")
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


def summarize_model(rows: Sequence[Mapping[str, Any]], matchweek: int = 1) -> dict[str, Any]:
    if len(rows) != 10:
        raise ResultsTrackerError("model summary requires ten scored fixtures")
    model_ids = {str(row["model_id"]) for row in rows}
    families = {str(row["model_family"]) for row in rows}
    if len(model_ids) != 1 or len(families) != 1:
        raise ResultsTrackerError("model summary rows do not share one identity")
    count = len(rows)
    return {
        "season": "2026-27",
        "matchweek": matchweek,
        "model_family": next(iter(families)),
        "model_id": next(iter(model_ids)),
        "fixtures_scored": count,
        "hda_log_loss": _round(math.fsum(float(row["hda_log_loss"]) for row in rows) / count),
        "hda_brier_score": _round(math.fsum(float(row["hda_brier_score"]) for row in rows) / count),
        "hda_top1_accuracy": _round(math.fsum(int(row["top1_correct"]) for row in rows) / count),
        "goal_mae": _round(math.fsum(float(row["goal_mae"]) for row in rows) / count),
    }


def validate_dc_supplement(
    content: bytes, incumbent_content: bytes, incumbent_rows: Sequence[Mapping[str, Any]]
) -> dict[str, dict[str, Any]]:
    """Accept only the audited frozen-artifact replay, bound to the original forecast."""
    if hashlib.sha256(content).hexdigest() != DC_SOURCE_SHA256:
        raise ResultsTrackerError("DC supplement SHA-256 does not match the verified replay")
    payload = json.loads(content)
    if payload["original_forecast_sha256"] != hashlib.sha256(incumbent_content).hexdigest():
        raise ResultsTrackerError("DC supplement is bound to a different original forecast")
    rows = {row["fixture_key"]: row for row in payload["markets"]}
    if len(rows) != 10 or set(rows) != {row["fixture_key"] for row in incumbent_rows}:
        raise ResultsTrackerError("DC supplement fixture coverage differs")
    for forecast in incumbent_rows:
        row = rows[forecast["fixture_key"]]
        if (row["home_team"], row["away_team"]) != (forecast["home_team"], forecast["away_team"]):
            raise ResultsTrackerError("DC supplement fixture identities differ")
        for field in ("p_over_2_5", "p_btts"):
            if not math.isfinite(row[field]) or not 0 <= row[field] <= 1:
                raise ResultsTrackerError("DC supplement probability is invalid")
    return rows


def poisson_markets(lambda_home: float, lambda_away: float) -> dict[str, float]:
    """Unbounded independent-Poisson convention used in the original Elo MW2 table."""
    if any(not math.isfinite(value) or value < 0 for value in (lambda_home, lambda_away)):
        raise ResultsTrackerError("Poisson goal expectations must be finite and nonnegative")
    total = lambda_home + lambda_away
    return {
        "over_2_5": 1.0 - math.exp(-total) * (1.0 + total + total * total / 2.0),
        "btts": (1.0 - math.exp(-lambda_home)) * (1.0 - math.exp(-lambda_away)),
    }


def score_market_decision(probability: float, observed_yes: bool) -> dict[str, Any]:
    if not math.isfinite(probability) or not 0 <= probability <= 1:
        raise ResultsTrackerError("market probability must be finite and within [0, 1]")
    selected = probability != THRESHOLD_RULE["threshold"]
    predicted_yes = probability > THRESHOLD_RULE["threshold"] if selected else None
    return {
        "p_yes": _round(probability),
        "p_selected": _round(max(probability, 1.0 - probability)) if selected else None,
        "predicted_yes": predicted_yes,
        "selected": int(selected),
        "won": int(observed_yes == predicted_yes) if selected else None,
    }


def score_goal_markets(
    forecasts: Sequence[Mapping[str, Any]],
    results: Sequence[Mapping[str, Any]],
    matchweek: int,
    dc_markets: Mapping[str, Mapping[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    score_model(forecasts, results)  # Validate identities, result outcomes and model inputs.
    by_key = {str(row["fixture_key"]): row for row in forecasts}
    rows = []
    for result in results:
        forecast = by_key[str(result["fixture_key"])]
        if forecast["model_family"] == "elo-poisson":
            probabilities = poisson_markets(
                float(forecast["expected_home_goals"]), float(forecast["expected_away_goals"])
            )
            method = "retrospective_original_lambdas_unbounded_independent_poisson"
        elif forecast["model_family"] == "dynamic-dixon-coles":
            if dc_markets is None or forecast["fixture_key"] not in dc_markets:
                raise ResultsTrackerError(
                    "DC goal markets require the verified frozen-artifact replay"
                )
            dc_row = dc_markets[forecast["fixture_key"]]
            if (dc_row["home_team"], dc_row["away_team"]) != (
                forecast["home_team"],
                forecast["away_team"],
            ):
                raise ResultsTrackerError("DC goal market fixture identities differ")
            probabilities = {"over_2_5": dc_row["p_over_2_5"], "btts": dc_row["p_btts"]}
            method = "retrospective_verified_frozen_dixon_coles_artifact_replay"
        else:
            raise ResultsTrackerError("unknown model family for goal markets")
        for market, probability in probabilities.items():
            observed = (
                result["home_goals"] + result["away_goals"] >= 3
                if market == "over_2_5"
                else result["home_goals"] > 0 and result["away_goals"] > 0
            )
            decision = score_market_decision(float(probability), observed)
            selection = None
            if decision["selected"]:
                labels = ("OVER", "UNDER") if market == "over_2_5" else ("BTTS_YES", "BTTS_NO")
                selection = labels[0 if decision["predicted_yes"] else 1]
            rows.append(
                {
                    "season": "2026-27",
                    "matchweek": matchweek,
                    "fixture_key": forecast["fixture_key"],
                    "model_family": forecast["model_family"],
                    "model_id": forecast["model_id"],
                    "home_team": forecast["home_team"],
                    "away_team": forecast["away_team"],
                    "market": market,
                    **decision,
                    "selection": selection,
                    "observed_yes": int(observed),
                    "probability_method": method,
                    "retrospectively_derived": True,
                }
            )
    return rows


def summarize_markets(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    summary = {}
    for market in ("over_2_5", "btts"):
        market_rows = [row for row in rows if row["market"] == market]
        selected = sum(int(row["selected"]) for row in market_rows)
        won = sum(int(row["won"]) for row in market_rows if row["selected"])
        summary.update(
            {
                f"{market}_available": len(market_rows),
                f"{market}_selected": selected,
                f"{market}_won": won,
                f"{market}_lost": selected - won,
                f"{market}_hit_rate": _round(won / selected) if selected else None,
                f"{market}_coverage": _round(selected / len(market_rows)) if market_rows else None,
            }
        )
    return summary


def goal_deviations(
    forecasts: Sequence[Mapping[str, Any]], results: Sequence[Mapping[str, Any]], matchweek: int
) -> list[dict[str, Any]]:
    score_model(forecasts, results)
    by_key = {row["fixture_key"]: row for row in forecasts}
    rows = []
    for result in results:
        forecast = by_key[result["fixture_key"]]
        home_error = result["home_goals"] - float(forecast["expected_home_goals"])
        away_error = result["away_goals"] - float(forecast["expected_away_goals"])
        rows.append(
            {
                "season": "2026-27",
                "matchweek": matchweek,
                "fixture_key": result["fixture_key"],
                "model_family": forecast["model_family"],
                "model_id": forecast["model_id"],
                "home_team": result["home_team"],
                "away_team": result["away_team"],
                "home_goals": result["home_goals"],
                "away_goals": result["away_goals"],
                "expected_home_goals": float(forecast["expected_home_goals"]),
                "expected_away_goals": float(forecast["expected_away_goals"]),
                "home_error": home_error,
                "away_error": away_error,
                "home_absolute_error": abs(home_error),
                "away_absolute_error": abs(away_error),
                "actual_total_goals": result["home_goals"] + result["away_goals"],
                "expected_total_goals": float(forecast["expected_home_goals"])
                + float(forecast["expected_away_goals"]),
                "total_goal_error": home_error + away_error,
                "goal_mae": (abs(home_error) + abs(away_error)) / 2,
                "goal_bias": (home_error + away_error) / 2,
                "total_goals_mae": abs(home_error + away_error),
            }
        )
    return rows


def summarize_goals(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    return {
        field: _round(math.fsum(float(row[field]) for row in rows) / len(rows)) if rows else None
        for field in ("goal_mae", "goal_bias", "total_goals_mae")
    }


def build_cumulative(
    scores: Sequence[Mapping[str, Any]],
    bets: Sequence[Mapping[str, Any]],
    deviations: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Pool fixture-level observations; never average matchweek hit rates."""
    rows = []
    for family in ("dynamic-dixon-coles", "elo-poisson"):
        model_scores = [row for row in scores if row["model_family"] == family]
        model_bets = [row for row in bets if row["model_family"] == family]
        count = len(model_scores)
        rows.append(
            {
                "season": "2026-27",
                "model_family": family,
                "model_ids": " | ".join(sorted({str(row["model_id"]) for row in model_scores})),
                "matchweeks_scored": len({row["matchweek"] for row in model_bets}),
                "fixtures_scored": count,
                "hda_log_loss": _round(
                    math.fsum(float(r["hda_log_loss"]) for r in model_scores) / count
                ),
                "hda_brier_score": _round(
                    math.fsum(float(r["hda_brier_score"]) for r in model_scores) / count
                ),
                "hda_top1_accuracy": _round(
                    sum(int(r["top1_correct"]) for r in model_scores) / count
                ),
                "hda_correct": sum(int(r["top1_correct"]) for r in model_scores),
                **summarize_goals([r for r in deviations if r["model_family"] == family]),
                **summarize_markets(model_bets),
            }
        )
    return rows


def build_tracker(
    summaries: Sequence[Mapping[str, Any]],
    bets: Sequence[Mapping[str, Any]],
    mw3_challenger_rows: Sequence[Mapping[str, Any]],
    deviations: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    expected = {(1, "dynamic-dixon-coles"), (1, "elo-poisson"), (2, "elo-poisson")}
    by_week_family = {(row["matchweek"], row["model_family"]): row for row in summaries}
    if set(by_week_family) != expected or len(summaries) != len(expected):
        raise ResultsTrackerError("tracker requires exactly the three published MW1/MW2 releases")
    if {row["fixture_key"] for row in mw3_challenger_rows} != {
        "epl-mw03-08",
        "epl-mw03-09",
        "epl-mw03-10",
    } or len(mw3_challenger_rows) != 3:
        raise ResultsTrackerError("MW3 tracker requires the three still-prospective fixtures")
    rows = []
    for matchweek in (1, 2, 3):
        for family in ("dynamic-dixon-coles", "elo-poisson"):
            summary = by_week_family.get((matchweek, family))
            if summary is not None:
                model_bets = [
                    r for r in bets if (r["matchweek"], r["model_family"]) == (matchweek, family)
                ]
                rows.append(
                    {
                        **{field: summary[field] for field in MODEL_SUMMARY_FIELDS},
                        "forecast_status": "published_pre_match",
                        "result_status": "scored",
                        "fixtures_forecast": summary["fixtures_scored"],
                        "hda_correct": round(
                            summary["hda_top1_accuracy"] * summary["fixtures_scored"]
                        ),
                        **summarize_goals(
                            [
                                r
                                for r in deviations
                                if (r["matchweek"], r["model_family"]) == (matchweek, family)
                            ]
                        ),
                        **summarize_markets(model_bets),
                    }
                )
            else:
                prospective = family == "elo-poisson"
                rows.append(
                    {
                        "season": "2026-27",
                        "matchweek": matchweek,
                        "model_family": family,
                        "model_id": mw3_challenger_rows[0]["model_id"]
                        if prospective
                        else "dynamic-dixon-coles-incumbent-2026-27-v1",
                        "forecast_status": "published_pre_match_partial"
                        if prospective
                        else "not_released",
                        "result_status": "pending" if prospective else "not_applicable",
                        "fixtures_forecast": len(mw3_challenger_rows) if prospective else 0,
                        "fixtures_scored": 0,
                        **dict.fromkeys((*MODEL_SUMMARY_FIELDS[5:], *EXTRA_METRIC_FIELDS)),
                    }
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


def _name(family: str) -> str:
    return "Dynamic Dixon–Coles" if family == "dynamic-dixon-coles" else "Elo–Poisson"


def _percent(value: float | None) -> str:
    return "—" if value is None else f"{value:.1%}"


def _number(value: float | None, precision: int = 4) -> str:
    return "—" if value is None else f"{value:.{precision}f}"


def render_tracker(
    tracker: Sequence[Mapping[str, Any]],
    cumulative: Sequence[Mapping[str, Any]],
) -> bytes:
    completed = [row for row in tracker if row["result_status"] == "scored"]
    comparison = [(f"MW{row['matchweek']}", row) for row in completed]
    comparison.extend(
        ("MW1 only" if row["matchweeks_scored"] == 1 else "MW1–2", row) for row in cumulative
    )
    lines = [
        "# EPL 2026/27 · model tracker after Matchweek 2",
        "",
        "Results through **31 August 2026**. All original forecasts remain unchanged.",
        "",
        "## Match outcome · all forecasts",
        "",
        "For H/D/A, the pick is the outcome with the highest probability for **every fixture**, "
        "with **no 50% threshold**. H means home win, D draw and A away win.",
        "",
        "| Period | Model | Correct / all forecasts | Accuracy |",
        "| --- | --- | ---: | ---: |",
    ]
    for period, row in comparison:
        lines.append(
            f"| {period} | {_name(row['model_family'])} | "
            f"{row['hda_correct']} / {row['fixtures_scored']} | "
            f"{_percent(row['hda_top1_accuracy'])} |"
        )
    lines.extend(
        [
            "",
            "**Example:** Elo–Poisson made 10 predictions in MW1 and got 5 of the "
            "10 H/D/A outcomes right: **50% accuracy**. Goal-market selections below have "
            "their own denominators and do not remove any H/D/A predictions.",
            "",
            "## Goal markets · choose the side with probability > 50%",
            "",
            "**Over 2.5** means at least three goals; **Under 2.5** means zero, one or two. "
            "**BTTS YES** means both teams score; **BTTS NO** means at least one does not. "
            "Each market is evaluated separately: choose YES if P(YES) > 50% and NO if "
            "P(YES) < 50%, because P(NO) = 1 − P(YES) then exceeds 50%. "
            "Exactly 50% is no selection. Correct NO picks count as wins. "
            "Hit rate = wins / selected bets. "
            "Coverage = selected / probability-available fixtures.",
            "",
            "| Period | Model | Market | Available fixtures | Selected | Wins / selected | "
            "Hit rate | Coverage |",
            "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for period, row in comparison:
        for market, label in (("over_2_5", "Over / Under 2.5"), ("btts", "BTTS YES / NO")):
            lines.append(
                f"| {period} | {_name(row['model_family'])} | {label} | "
                f"{row[f'{market}_available']} | {row[f'{market}_selected']} | "
                f"{row[f'{market}_won']} / {row[f'{market}_selected']} | "
                f"{_percent(row[f'{market}_hit_rate'])} | "
                f"{_percent(row[f'{market}_coverage'])} |"
            )
    lines.extend(
        [
            "",
            "For example, Elo MW1 BTTS makes **10 picks**: nine YES and one NO. "
            "Four YES picks and the NO pick were right, for **5 / 10 = 50%**. "
            "Over/Under and BTTS rates are never pooled: both can refer to "
            "the same fixture and are correlated.",
            "",
            "The rule was specified retrospectively on **5 September 2026** and was "
            "**not pre-registered**. Elo markets are retrospectively derived from the "
            "original frozen goal expectations using the unbounded independent-Poisson "
            "convention stated in the original MW2 forecast table. DC MW1 markets come "
            "from a verified replay of the original frozen Dixon–Coles artifact; the replay "
            "exactly matched all original H/D/A, goal-expectation, modal and tail outputs. "
            "Its original matrix convention is retained; no independent-Poisson approximation "
            "is applied to DC. The retrospective market probabilities are not a record "
            "of newly discovered pre-match publications. See the "
            "[DC replay commitments](dc_mw1_goal_markets.json).",
            "",
            "No odds or stakes were recorded, so hit rate does not determine ROI or profit. "
            "These small samples are descriptive. DC has MW1 only; Elo's MW1–2 aggregate "
            "combines the original and post-MW1-refit releases and covers twice as many fixtures.",
            "",
            "## Expected goals versus actual goals",
            "",
            "These are **model-implied expected goals**, not observed shot-based xG. "
            "Team-goal MAE averages the absolute home and away goal errors. "
            "Signed bias is **actual minus expected**, averaged per team: a positive number "
            "means more goals were scored than predicted. Total-goal MAE compares the "
            "sum of both expectations with the actual match total.",
            "",
            "| Period | Model | Team-goal MAE ↓ | Signed bias / team | Total-goal MAE ↓ |",
            "| --- | --- | ---: | ---: | ---: |",
        ]
    )
    for period, row in comparison:
        lines.append(
            f"| {period} | {_name(row['model_family'])} | {row['goal_mae']:.3f} | "
            f"{row['goal_bias']:+.3f} | {row['total_goals_mae']:.3f} |"
        )
    lines.extend(
        [
            "",
            "## Release coverage and probability scores",
            "",
            "Lower is better for log loss and Brier.",
            "",
            "| MW | Model | Forecast status | Results | Scored / forecast | Log loss ↓ | Brier ↓ |",
            "| ---: | --- | --- | --- | ---: | ---: | ---: |",
        ]
    )
    for row in tracker:
        lines.append(
            f"| {row['matchweek']} | {_name(row['model_family'])} | "
            f"{row['forecast_status']} | {row['result_status']} | "
            f"{row['fixtures_scored']} / {row['fixtures_forecast']} | "
            f"{_number(row['hda_log_loss'])} | {_number(row['hda_brier_score'])} |"
        )
    lines.extend(
        [
            "",
            "DC MW2 and MW3 are not_released. MW3 Elo is pending for the **three remaining "
            "prospective fixtures**; the seven fixtures whose kickoff had already passed "
            "are excluded. Empty CSV cells and JSON null mean unavailable, not zero. "
            "With no selections, a market's hit rate is null.",
            "",
            "## Downloads and methodology",
            "",
            "- [Per-matchweek CSV](model_performance.csv) · "
            "[Full tracker JSON](model_performance.json)",
            "- [Per-fixture Over 2.5 and BTTS decisions](betting_selections.csv)",
            "- [Expected versus actual goal deviations](goal_deviations.csv)",
            "- [Cumulative metrics](cumulative_performance.csv)",
            "- [Immutable MW1 pack](../matchday-01/results/README.md) · "
            "[MW2 results pack](../matchday-02/results/README.md)",
            "",
            "Log loss = mean −ln(probability of the observed H/D/A result). Brier = mean "
            "sum of squared errors across H, D and A (range 0–2, no division by three). "
            "H/D/A ties follow H, D, A order. Cumulative statistics pool fixture-level scores "
            "and counts, not weekly hit rates. Market selection uses full derived precision "
            "before display rounding; exported p_yes is rounded to 12 decimal places. "
            "All market and goal-deviation calculations are available "
            "per fixture in the downloads.",
            "",
            "Run python -m epl_probability_lab.results_tracker --root . to regenerate in memory "
            "and verify every derived artifact. Add --write to reproduce the files. "
            "The original MW1 package remains byte-identical.",
            "",
        ]
    )
    return "\n".join(lines).encode("utf-8")


def render_mw2_results(
    results: Sequence[Mapping[str, Any]],
    summary: Mapping[str, Any],
    bets: Sequence[Mapping[str, Any]],
    deviations: Sequence[Mapping[str, Any]],
    scores: Sequence[Mapping[str, Any]],
) -> bytes:
    markets = summarize_markets(bets)
    goals_summary = summarize_goals(deviations)
    home_wins = sum(row["outcome"] == "H" for row in results)
    draws = sum(row["outcome"] == "D" for row in results)
    goals = sum(row["home_goals"] + row["away_goals"] for row in results)
    lines = [
        "# Matchweek 2 · results and Elo–Poisson scorecard",
        "",
        "**10/10 fixtures completed.** [Result provenance](provenance.md) · "
        "[Original Elo forecast](../challengers/elo-poisson-v1-post-mw1/README.md).",
        "",
        f"**{goals} goals**, {home_wins} home wins, {draws} draws and "
        f"{len(results) - home_wins - draws} away wins.",
        "",
        "**H/D/A uses the highest-probability outcome for all 10 fixtures**, without "
        f"a threshold: **{sum(row['top1_correct'] for row in scores)} / 10 correct "
        f"({_percent(summary['hda_top1_accuracy'])})**.",
        "",
        "| Goal market | Probability-available fixtures | Side >50% selected | Wins / selected | "
        "Hit rate | Coverage |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for market, label in (("over_2_5", "Over / Under 2.5"), ("btts", "BTTS YES / NO")):
        lines.append(
            f"| {label} | {markets[f'{market}_available']} | {markets[f'{market}_selected']} | "
            f"{markets[f'{market}_won']} / {markets[f'{market}_selected']} | "
            f"{_percent(markets[f'{market}_hit_rate'])} | "
            f"{_percent(markets[f'{market}_coverage'])} |"
        )
    lines.extend(
        [
            "",
            "Over 2.5 requires at least three goals; BTTS YES requires both teams to score. "
            "Choose YES above 50% or NO below 50%, whose complementary probability exceeds "
            "50%. A correct Under 2.5 or BTTS NO pick also wins. Exactly 50% is no selection.",
            "",
            "| Fixture | Actual | Expected goals H–A | H/D/A pick | Correct |",
            "| --- | ---: | ---: | --- | --- |",
        ]
    )
    by_key = {row["fixture_key"]: row for row in scores}
    for result in results:
        score = by_key[result["fixture_key"]]
        lines.append(
            f"| {result['home_team']} – {result['away_team']} | "
            f"{result['home_goals']}–{result['away_goals']} | "
            f"{score['expected_home_goals']:.3f}–{score['expected_away_goals']:.3f} | "
            f"{score['predicted_outcome']} | {'Yes' if score['top1_correct'] else 'No'} |"
        )
    lines.extend(
        [
            "",
            f"Team-goal MAE: **{goals_summary['goal_mae']:.3f}**; mean signed bias "
            f"(actual minus expected): **{goals_summary['goal_bias']:+.3f} goals/team**; "
            f"total-goal MAE: **{goals_summary['total_goals_mae']:.3f}**. "
            "The expectations are model-implied goal means, not shot-based xG.",
            "",
            f"H/D/A log loss: **{summary['hda_log_loss']:.4f}**; "
            f"Brier: **{summary['hda_brier_score']:.4f}**. Lower is better. Brier sums "
            "the three squared H/D/A errors (0–2 scale).",
            "",
            "Market probabilities are retrospectively derived from original frozen lambdas "
            "using the unbounded independent-Poisson convention stated in the original forecast "
            "table. The user specified this diagnostic rule on 5 September 2026, after these "
            "matches. It was not pre-registered. "
            "No odds or stakes means no ROI or profit estimate. "
            "DC has no MW2 forecast and remains not_released.",
            "",
            "[Results CSV](results.csv) · [Model scores CSV](model_scores.csv) · "
            "[Summary CSV](model_summary.csv) · [Full JSON](results.json) · "
            "[Market decisions](../../tracking/betting_selections.csv) · "
            "[Goal deviations](../../tracking/goal_deviations.csv) · "
            "[Season tracker](../../tracking/README.md)",
            "",
        ]
    )
    return "\n".join(lines).encode("utf-8")


def render_mw2_provenance() -> bytes:
    source = MW2_RESULT_SOURCE
    return (
        "# Matchweek 2 result provenance\n\n"
        f"Source: [OpenFootball / England](https://github.com/{source['repository']}/blob/"
        f"{source['commit']}/{source['path']}). License: **CC0-1.0**.\n\n"
        f"- Commit: `{source['commit']}`\n"
        f"- Path: `{source['path']}`\n"
        f"- Git blob: `{source['blob']}`\n"
        f"- Download SHA-256: `{source['download_sha256']}`\n"
        f"- Source snapshot date: `{source['data_as_of']}`\n\n"
        "Ten completed Matchweek 2 scorelines are bound to canonical fixture identities "
        "and kickoff timestamps in the already-published forecast. The result contract is "
        "checked by `epl_probability_lab.results_tracker`; CSV, JSON, metrics and tables "
        "reproduce deterministically from the original forecast "
        "and this pinned result contract.\n\n"
        "The historical MW1 results pack and every pre-match forecast remain unchanged. "
        "The >50% more-likely-side rule for Over/Under 2.5 and BTTS YES/NO was specified "
        "by the user on 5 September 2026 after "
        "MW1 and MW2, so the analysis is retrospective, not pre-registered. No odds, "
        "stakes, ROI or profit are supplied or inferred. H/D/A accuracy scores the "
        "highest-probability outcome for every fixture without a threshold. Elo goal markets "
        "use the unbounded independent-Poisson convention from original frozen lambdas.\n"
    ).encode()


def expected_artifacts(
    incumbent_content: bytes,
    challenger_content: bytes,
    mw2_challenger_content: bytes,
    mw3_challenger_content: bytes,
    dc_supplement_content: bytes,
) -> dict[Path, bytes]:
    incumbent = _load_forecasts(incumbent_content, challenger=False)
    challenger = _load_forecasts(challenger_content, challenger=True)
    mw2_challenger = _load_forecasts(mw2_challenger_content, challenger=True)
    mw3_challenger = _load_forecasts(mw3_challenger_content, challenger=True, expected_count=3)
    dc_markets = validate_dc_supplement(dc_supplement_content, incumbent_content, incumbent)
    results = build_results(incumbent)
    incumbent_scores = score_model(incumbent, results)
    challenger_scores = score_model(challenger, results)
    scores = incumbent_scores + challenger_scores
    summaries = [summarize_model(incumbent_scores), summarize_model(challenger_scores)]
    mw2_results = build_results(mw2_challenger, MATCHWEEK_2_RESULTS)
    mw2_scores = score_model(mw2_challenger, mw2_results)
    mw2_summary = summarize_model(mw2_scores, matchweek=2)
    bets = (
        score_goal_markets(incumbent, results, 1, dc_markets)
        + score_goal_markets(challenger, results, 1)
        + score_goal_markets(mw2_challenger, mw2_results, 2)
    )
    deviations = (
        goal_deviations(incumbent, results, 1)
        + goal_deviations(challenger, results, 1)
        + goal_deviations(mw2_challenger, mw2_results, 2)
    )
    tracker = build_tracker([*summaries, mw2_summary], bets, mw3_challenger, deviations)
    cumulative = build_cumulative(scores + mw2_scores, bets, deviations)
    mw2_bets = [row for row in bets if row["matchweek"] == 2]
    mw2_deviations = [row for row in deviations if row["matchweek"] == 2]
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
        "schema_version": "epl-model-performance-tracker/v3",
        "competition": "EPL",
        "season": "2026-27",
        "results_through_matchweek": 2,
        "threshold_rule": THRESHOLD_RULE,
        "metric_definitions": {
            **results_payload["metric_definitions"],
            "goal_bias": (
                "mean actual-minus-expected goal error per team; positive means underprediction"
            ),
            "total_goals_mae": "mean absolute error of expected match-total goals",
            "market_hit_rate": (
                "correct YES or NO picks / selected picks for each market; null if none selected"
            ),
            "market_coverage": "selected YES or NO picks / fixtures with market probabilities",
        },
        "rows": tracker,
        "cumulative": cumulative,
        "market_decisions": bets,
        "goal_deviations": deviations,
        "market_provenance": {
            "dc_supplement_path": DC_SOURCE_PATH.as_posix(),
            "dc_supplement_sha256": DC_SOURCE_SHA256,
            "elo_method": "original frozen lambdas; unbounded independent Poisson",
            "historical_market_analysis_status": "retrospectively_derived_not_preregistered",
        },
    }
    mw2_payload = {
        "schema_version": "epl-model-results/v2",
        "competition": "EPL",
        "season": "2026-27",
        "matchweek": 2,
        "result_source": MW2_RESULT_SOURCE,
        "metric_definitions": tracker_payload["metric_definitions"],
        "results": mw2_results,
        "model_scores": mw2_scores,
        "model_summary": [mw2_summary],
        "threshold_rule": THRESHOLD_RULE,
        "market_decisions": mw2_bets,
        "market_summary": summarize_markets(mw2_bets),
        "goal_deviations": mw2_deviations,
        "goal_summary": summarize_goals(mw2_deviations),
        "unavailable_model_families": {"dynamic-dixon-coles": "not_released"},
    }
    return {
        RESULTS_CSV_PATH: _csv_bytes(results, RESULT_FIELDS),
        MODEL_SCORES_CSV_PATH: _csv_bytes(scores, MODEL_SCORE_FIELDS),
        MODEL_SUMMARY_CSV_PATH: _csv_bytes(summaries, MODEL_SUMMARY_FIELDS),
        RESULTS_JSON_PATH: _json_bytes(results_payload),
        TRACKER_CSV_PATH: _csv_bytes(tracker, TRACKER_FIELDS),
        TRACKER_JSON_PATH: _json_bytes(tracker_payload),
        TRACKER_README_PATH: render_tracker(tracker, cumulative),
        BETTING_SELECTIONS_CSV_PATH: _csv_bytes(bets, BETTING_FIELDS),
        CUMULATIVE_CSV_PATH: _csv_bytes(cumulative, CUMULATIVE_FIELDS),
        GOAL_DEVIATIONS_CSV_PATH: _csv_bytes(deviations, GOAL_DEVIATION_FIELDS),
        MW2_RESULTS_CSV_PATH: _csv_bytes(mw2_results, RESULT_FIELDS),
        MW2_MODEL_SCORES_CSV_PATH: _csv_bytes(mw2_scores, MODEL_SCORE_FIELDS),
        MW2_MODEL_SUMMARY_CSV_PATH: _csv_bytes([mw2_summary], MODEL_SUMMARY_FIELDS),
        MW2_RESULTS_JSON_PATH: _json_bytes(mw2_payload),
        MW2_RESULTS_README_PATH: render_mw2_results(
            mw2_results, mw2_summary, mw2_bets, mw2_deviations, mw2_scores
        ),
        MW2_RESULTS_PROVENANCE_PATH: render_mw2_provenance(),
    }


def source_paths() -> tuple[Path, ...]:
    return (
        INCUMBENT_FORECAST_PATH,
        CHALLENGER_FORECAST_PATH,
        MW2_CHALLENGER_FORECAST_PATH,
        MW3_CHALLENGER_FORECAST_PATH,
        DC_SOURCE_PATH,
    )


def required_release_paths() -> tuple[Path, ...]:
    return (
        *source_paths(),
        RESULTS_CSV_PATH,
        MODEL_SCORES_CSV_PATH,
        MODEL_SUMMARY_CSV_PATH,
        RESULTS_JSON_PATH,
        RESULTS_README_PATH,
        RESULTS_PROVENANCE_PATH,
        TRACKER_CSV_PATH,
        TRACKER_JSON_PATH,
        TRACKER_README_PATH,
        BETTING_SELECTIONS_CSV_PATH,
        CUMULATIVE_CSV_PATH,
        GOAL_DEVIATIONS_CSV_PATH,
        MW2_RESULTS_CSV_PATH,
        MW2_MODEL_SCORES_CSV_PATH,
        MW2_MODEL_SUMMARY_CSV_PATH,
        MW2_RESULTS_JSON_PATH,
        MW2_RESULTS_README_PATH,
        MW2_RESULTS_PROVENANCE_PATH,
    )


def validate_release_contents(contents: Mapping[str | Path, bytes]) -> dict[Path, bytes]:
    normalized = {Path(path).as_posix(): value for path, value in contents.items()}
    missing = [
        path.as_posix() for path in required_release_paths() if path.as_posix() not in normalized
    ]
    if missing:
        raise ResultsTrackerError(f"results tracker files are missing: {', '.join(missing)}")
    expected = expected_artifacts(*(normalized[path.as_posix()] for path in source_paths()))
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
    return validate_release_contents(
        {path: (root / path).read_bytes() for path in required_release_paths()}
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--write", action="store_true", help="Reproduce approved derived artifacts")
    args = parser.parse_args()
    if args.write:
        artifacts = expected_artifacts(
            *((args.root / path).read_bytes() for path in source_paths())
        )
        for path, content in artifacts.items():
            target = args.root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            if not target.exists() or target.read_bytes() != content:
                target.write_bytes(content)
    artifacts = validate_release_tree(args.root.resolve())
    print(f"results tracker validation: PASS ({len(artifacts)} regenerated artifacts)")


if __name__ == "__main__":
    main()
