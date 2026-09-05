from __future__ import annotations

import csv
import hashlib
import io
import json
import math
from pathlib import Path

import pytest

from epl_probability_lab.publication import inspect_paths
from epl_probability_lab.results_tracker import (
    BETTING_SELECTIONS_CSV_PATH,
    CUMULATIVE_CSV_PATH,
    DC_SOURCE_PATH,
    GOAL_DEVIATIONS_CSV_PATH,
    INCUMBENT_FORECAST_PATH,
    MODEL_SCORES_CSV_PATH,
    MODEL_SUMMARY_CSV_PATH,
    MW2_MODEL_SCORES_CSV_PATH,
    MW2_MODEL_SUMMARY_CSV_PATH,
    MW2_RESULTS_CSV_PATH,
    MW2_RESULTS_JSON_PATH,
    MW2_RESULTS_README_PATH,
    RESULTS_CSV_PATH,
    RESULTS_JSON_PATH,
    TRACKER_CSV_PATH,
    TRACKER_JSON_PATH,
    TRACKER_README_PATH,
    ResultsTrackerError,
    build_cumulative,
    goal_deviations,
    poisson_markets,
    required_release_paths,
    score_goal_markets,
    score_market_decision,
    score_model,
    summarize_goals,
    summarize_markets,
    validate_dc_supplement,
    validate_release_contents,
    validate_release_tree,
)

ROOT = Path(__file__).resolve().parents[1]
MARKETS = ("over_2_5", "btts")


def _contents() -> dict[Path, bytes]:
    return {path: (ROOT / path).read_bytes() for path in required_release_paths()}


def _fixture(p_home: float = 0.6, home_goals: int = 1, away_goals: int = 0) -> tuple[dict, dict]:
    forecast = {
        "fixture_key": "test-1",
        "home_team": "Home",
        "away_team": "Away",
        "model_id": "test-model",
        "model_family": "elo-poisson",
        "p_home": p_home,
        "p_draw": 0.25,
        "p_away": 0.75 - p_home,
        "expected_home_goals": 1.4,
        "expected_away_goals": 1.1,
    }
    result = {
        "fixture_key": "test-1",
        "home_team": "Home",
        "away_team": "Away",
        "home_goals": home_goals,
        "away_goals": away_goals,
        "outcome": "H" if home_goals > away_goals else "A" if home_goals < away_goals else "D",
    }
    return forecast, result


def _incumbent_rows() -> tuple[bytes, list[dict]]:
    content = (ROOT / INCUMBENT_FORECAST_PATH).read_bytes()
    rows = []
    for original in json.loads(content):
        rows.append(
            {
                **original,
                "model_family": "dynamic-dixon-coles",
                "p_home": original["p_home_win"],
                "p_away": original["p_away_win"],
            }
        )
    return content, rows


def test_committed_results_pack_and_tracker_reproduce() -> None:
    regenerated = validate_release_tree(ROOT)
    assert len(regenerated) == 16
    payload = json.loads((ROOT / MW2_RESULTS_JSON_PATH).read_bytes())
    assert len(payload["results"]) == len(payload["model_scores"]) == 10
    assert sum(row["home_goals"] + row["away_goals"] for row in payload["results"]) == 32
    assert payload["model_summary"][0]["hda_top1_accuracy"] == 0.5
    assert payload["model_summary"][0]["hda_log_loss"] == pytest.approx(1.006697406993)


@pytest.mark.parametrize(
    "path,sha256",
    [
        (RESULTS_JSON_PATH, "90b57bdc6ea90e792650ffc645bff5e4b4f2ed578a7a3d889c66f9fd84bb4f44"),
        (RESULTS_CSV_PATH, "23b40f4c9d7307c26085d65cd0702d51695fe97950567fd52082f88719be8c17"),
        (MODEL_SCORES_CSV_PATH, "040df39a97dc0072220c4964ac1f79531fce9950d5eab3c98f62b2898f66e229"),
        (
            MODEL_SUMMARY_CSV_PATH,
            "51793bc2cf56391276b0b29e0dba2db69014292bb4cd66c9e0b4ecf5e30fb1ad",
        ),
    ],
)
def test_mw1_machine_artifacts_remain_byte_identical(path: Path, sha256: str) -> None:
    assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == sha256


def test_hda_scores_every_fixture_even_when_maximum_probability_is_below_half() -> None:
    forecast, result = _fixture(0.4)
    score = score_model([forecast], [result])[0]
    assert score["predicted_outcome"] == "H"
    assert score["top1_correct"] == 1
    assert score["hda_log_loss"] == pytest.approx(-math.log(0.4))
    assert score["hda_brier_score"] == pytest.approx((0.4 - 1) ** 2 + 0.25**2 + 0.35**2)


def test_hda_ties_keep_documented_h_d_a_order() -> None:
    forecast, result = _fixture(0.4, 1, 1)
    forecast.update(p_draw=0.4, p_away=0.2)
    score = score_model([forecast], [result])[0]
    assert score["predicted_outcome"] == "H"
    assert score["top1_correct"] == 0


@pytest.mark.parametrize(
    "probability, selected, predicted_yes, won",
    [(0.4999999999999, 1, False, 0), (0.5, 0, None, None), (0.5000000000001, 1, True, 1)],
)
def test_binary_market_threshold_uses_strict_source_precision(
    probability: float, selected: int, predicted_yes: bool | None, won: int | None
) -> None:
    decision = score_market_decision(probability, True)
    assert decision["p_yes"] == 0.5
    assert decision["selected"] == selected
    assert decision["predicted_yes"] == predicted_yes
    assert decision["won"] == won


def test_binary_no_prediction_can_win_and_lose() -> None:
    won = score_market_decision(0.25, False)
    lost = score_market_decision(0.25, True)
    assert won["selected"] == lost["selected"] == 1
    assert won["predicted_yes"] is False
    assert lost["predicted_yes"] is False
    assert won["p_selected"] == lost["p_selected"] == 0.75
    assert won["won"] == 1
    assert lost["won"] == 0


def test_no_bet_does_not_become_a_successful_no_selection() -> None:
    decisions = [{"market": market, **score_market_decision(0.5, False)} for market in MARKETS]
    summary = summarize_markets(decisions)
    for market in MARKETS:
        assert summary[f"{market}_available"] == 1
        assert summary[f"{market}_selected"] == summary[f"{market}_won"] == 0
        assert summary[f"{market}_lost"] == 0
        assert summary[f"{market}_hit_rate"] is None
        assert summary[f"{market}_coverage"] == 0
        assert summarize_markets([])[f"{market}_coverage"] is None


def test_goal_market_probabilities_follow_independent_poisson_distribution() -> None:
    actual = poisson_markets(1.4, 1.1)
    assert actual["over_2_5"] == pytest.approx(1 - math.exp(-2.5) * (1 + 2.5 + 2.5**2 / 2))
    assert actual["btts"] == pytest.approx((1 - math.exp(-1.4)) * (1 - math.exp(-1.1)))
    assert poisson_markets(0.0, 0.0) == {"over_2_5": 0.0, "btts": 0.0}


def test_goal_markets_are_separate_and_use_correct_scoreline_events() -> None:
    forecast, result = _fixture(home_goals=3, away_goals=0)
    forecast.update(expected_home_goals=2.0, expected_away_goals=2.0)
    decisions = score_goal_markets([forecast], [result], 1)
    by_market = {row["market"]: row for row in decisions}
    assert set(by_market) == set(MARKETS)
    assert by_market["over_2_5"]["observed_yes"] == 1
    assert by_market["over_2_5"]["selected"] == by_market["over_2_5"]["won"] == 1
    assert by_market["over_2_5"]["selection"] == "OVER"
    assert by_market["btts"]["observed_yes"] == 0
    assert by_market["btts"]["selected"] == 1
    assert by_market["btts"]["won"] == 0
    assert by_market["btts"]["selection"] == "BTTS_YES"
    summary = summarize_markets(decisions)
    assert summary["over_2_5_hit_rate"] == 1
    assert summary["btts_hit_rate"] == 0
    assert "bet_hit_rate" not in summary


@pytest.mark.parametrize("goals,over,btts", [((1, 1), 0, 1), ((0, 2), 0, 0), ((2, 1), 1, 1)])
def test_market_observations_use_over_two_and_both_teams_positive(
    goals: tuple[int, int], over: int, btts: int
) -> None:
    forecast, result = _fixture(home_goals=goals[0], away_goals=goals[1])
    decisions = {row["market"]: row for row in score_goal_markets([forecast], [result], 1)}
    assert decisions["over_2_5"]["observed_yes"] == over
    assert decisions["btts"]["observed_yes"] == btts


def test_dc_probabilities_require_verified_supplement_not_poisson_approximation() -> None:
    forecast, result = _fixture()
    forecast["model_family"] = "dynamic-dixon-coles"
    with pytest.raises(ResultsTrackerError):
        score_goal_markets([forecast], [result], 1)


def test_dc_supplement_is_pinned_and_uses_original_model_probabilities() -> None:
    content = (ROOT / DC_SOURCE_PATH).read_bytes()
    assert hashlib.sha256(content).hexdigest() == (
        "41c1c1c129be9d9e4e43fff18a4ee478f9f49f7547b3561d63a49853dcadcd98"
    )
    incumbent_content, incumbent_rows = _incumbent_rows()
    supplement = validate_dc_supplement(content, incumbent_content, incumbent_rows)
    forecast = incumbent_rows[0]
    result = {
        "fixture_key": forecast["fixture_key"],
        "home_team": forecast["home_team"],
        "away_team": forecast["away_team"],
        "home_goals": 3,
        "away_goals": 0,
        "outcome": "H",
    }
    decisions = {
        row["market"]: row
        for row in score_goal_markets([forecast], [result], 1, dc_markets=supplement)
    }
    assert decisions["over_2_5"]["p_yes"] == pytest.approx(0.4869158525101465)
    assert decisions["btts"]["p_yes"] == pytest.approx(0.4079529847668176)
    assert decisions["over_2_5"]["selection"] == "UNDER"
    assert decisions["over_2_5"]["won"] == 0
    assert decisions["btts"]["selection"] == "BTTS_NO"
    assert decisions["btts"]["won"] == 1
    assert all(row["selected"] == 1 for row in decisions.values())


def test_dc_supplement_rejects_tampering_and_different_original_forecast() -> None:
    content = (ROOT / DC_SOURCE_PATH).read_bytes()
    incumbent_content, incumbent_rows = _incumbent_rows()
    for supplement, original in (
        (content + b" ", incumbent_content),
        (content, incumbent_content + b" "),
    ):
        with pytest.raises(ResultsTrackerError):
            validate_dc_supplement(supplement, original, incumbent_rows)


def test_dc_supplement_rejects_fixture_identity_mismatch() -> None:
    content = (ROOT / DC_SOURCE_PATH).read_bytes()
    incumbent_content, incumbent_rows = _incumbent_rows()
    incumbent_rows[0]["away_team"] = "Different away team"
    with pytest.raises(ResultsTrackerError):
        validate_dc_supplement(content, incumbent_content, incumbent_rows)


def test_goal_errors_distinguish_absolute_error_bias_and_total_goal_error() -> None:
    forecast, result = _fixture(home_goals=3, away_goals=0)
    first = goal_deviations([forecast], [result], 1)
    assert first[0]["home_error"] == pytest.approx(1.6)
    assert first[0]["away_error"] == pytest.approx(-1.1)
    assert first[0]["goal_mae"] == pytest.approx((1.6 + 1.1) / 2)
    assert first[0]["goal_bias"] == pytest.approx((1.6 - 1.1) / 2)
    assert first[0]["total_goals_mae"] == pytest.approx(0.5)
    forecast, result = _fixture(home_goals=0, away_goals=2)
    forecast.update(expected_home_goals=1.0, expected_away_goals=1.0)
    second = goal_deviations([forecast], [result], 2)
    assert second[0]["goal_mae"] == 1
    assert second[0]["goal_bias"] == 0
    assert second[0]["total_goals_mae"] == 0
    summary = summarize_goals(first + second)
    assert summary["goal_mae"] == pytest.approx(1.175)
    assert summary["goal_bias"] == pytest.approx(0.125)
    assert summary["total_goals_mae"] == pytest.approx(0.25)


def test_cumulative_metrics_pool_counts_with_markets_kept_separate() -> None:
    scores, decisions, deviations = [], [], []
    # BTTS: one win in week 1; three losses in week 2. Pooling gives 1/4, not 1/2.
    # All four Over 2.5 selections win and must not be pooled with BTTS.
    for family in ("elo-poisson", "dynamic-dixon-coles"):
        for idx, goals in enumerate(((2, 1), (0, 3), (0, 3), (0, 3))):
            week = 1 if idx == 0 else 2
            forecast, result = _fixture(home_goals=goals[0], away_goals=goals[1])
            forecast.update(
                fixture_key=str(idx),
                model_family=family,
                expected_home_goals=2.0,
                expected_away_goals=2.0,
            )
            result["fixture_key"] = str(idx)
            scores.extend(score_model([forecast], [result]))
            deviations.extend(goal_deviations([forecast], [result], week))
            decisions.extend(
                {
                    "matchweek": week,
                    "model_family": family,
                    "model_id": forecast["model_id"],
                    "fixture_key": str(idx),
                    "market": market,
                    **score_market_decision(0.7, market == "over_2_5" or idx == 0),
                }
                for market in MARKETS
            )
    for row in build_cumulative(scores, decisions, deviations):
        assert row["fixtures_scored"] == 4
        assert row["hda_top1_accuracy"] == 0.25
        assert row["hda_log_loss"] == pytest.approx((-math.log(0.6) - 3 * math.log(0.15)) / 4)
        assert row["over_2_5_selected"] == row["btts_selected"] == 4
        assert row["over_2_5_won"] == 4
        assert row["over_2_5_hit_rate"] == 1
        assert row["btts_won"] == 1
        assert row["btts_lost"] == 3
        assert row["btts_hit_rate"] == 0.25
        assert row["goal_mae"] == 1.25
        assert row["goal_bias"] == -0.5
        assert row["total_goals_mae"] == 1


def test_released_counts_preserve_three_independent_scorecards() -> None:
    payload = json.loads((ROOT / TRACKER_JSON_PATH).read_bytes())
    completed = [row for row in payload["rows"] if row["result_status"] == "scored"]
    assert [row["hda_top1_accuracy"] for row in completed] == [0.6, 0.5, 0.5]
    assert [(row["over_2_5_selected"], row["over_2_5_won"]) for row in completed] == [
        (10, 6),
        (10, 7),
        (10, 4),
    ]
    assert [(row["btts_selected"], row["btts_won"]) for row in completed] == [
        (10, 5),
        (10, 5),
        (10, 6),
    ]
    cumulative = {row["model_family"]: row for row in payload["cumulative"]}
    assert len(cumulative) == 2
    assert cumulative["elo-poisson"]["over_2_5_hit_rate"] == 0.55
    assert cumulative["elo-poisson"]["btts_hit_rate"] == 0.55
    assert cumulative["elo-poisson"]["fixtures_scored"] == 20
    assert cumulative["dynamic-dixon-coles"]["fixtures_scored"] == 10
    assert len(payload["market_decisions"]) == 60
    assert len(payload["goal_deviations"]) == 30


def test_tracker_preserves_unreleased_and_pending_metrics_as_null() -> None:
    payload = json.loads((ROOT / TRACKER_JSON_PATH).read_bytes())
    rows = {(row["matchweek"], row["model_family"]): row for row in payload["rows"]}
    assert len(rows) == 6
    assert rows[2, "elo-poisson"]["result_status"] == "scored"
    assert rows[2, "elo-poisson"]["fixtures_scored"] == 10
    assert rows[3, "elo-poisson"]["result_status"] == "pending"
    assert rows[3, "elo-poisson"]["fixtures_forecast"] == 3
    for week in (2, 3):
        row = rows[week, "dynamic-dixon-coles"]
        assert row["forecast_status"] == "not_released"
        assert row["fixtures_forecast"] == row["fixtures_scored"] == 0
    metrics = (
        "hda_log_loss",
        "hda_brier_score",
        "hda_top1_accuracy",
        "goal_mae",
        "goal_bias",
        "total_goals_mae",
        *(f"{market}_{field}" for market in MARKETS for field in ("selected", "won", "hit_rate")),
    )
    for row in rows.values():
        if row["result_status"] != "scored":
            assert all(row[field] is None for field in metrics)


def test_tracker_csv_has_explicit_unavailable_values_and_six_release_rows() -> None:
    rows = list(csv.DictReader(io.StringIO((ROOT / TRACKER_CSV_PATH).read_text(encoding="utf-8"))))
    assert len(rows) == 6
    assert {(row["matchweek"], row["model_family"]) for row in rows} == {
        (str(week), family)
        for week in (1, 2, 3)
        for family in ("dynamic-dixon-coles", "elo-poisson")
    }
    assert all(
        row[f"{market}_hit_rate"] == ""
        for row in rows
        if row["result_status"] != "scored"
        for market in MARKETS
    )


@pytest.mark.parametrize(
    "path",
    [
        MODEL_SUMMARY_CSV_PATH,
        MW2_RESULTS_CSV_PATH,
        MW2_RESULTS_JSON_PATH,
        MW2_RESULTS_README_PATH,
        TRACKER_CSV_PATH,
        TRACKER_JSON_PATH,
        TRACKER_README_PATH,
        BETTING_SELECTIONS_CSV_PATH,
        CUMULATIVE_CSV_PATH,
        GOAL_DEVIATIONS_CSV_PATH,
    ],
)
def test_results_or_metric_tampering_is_rejected(path: Path) -> None:
    contents = _contents()
    contents[path] = contents[path] + b"modified\n"
    with pytest.raises(ResultsTrackerError, match="does not reproduce"):
        validate_release_contents(contents)


def test_tracker_rejects_missing_mw2_pack() -> None:
    contents = _contents()
    del contents[MW2_RESULTS_JSON_PATH]
    with pytest.raises(ResultsTrackerError, match="files are missing"):
        validate_release_contents(contents)


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -0.1, 1.1])
def test_invalid_binary_probabilities_cannot_enter_market_metrics(value: float) -> None:
    with pytest.raises(ResultsTrackerError):
        score_market_decision(value, True)


def test_duplicate_or_mismatched_results_cannot_be_scored() -> None:
    forecast, result = _fixture()
    with pytest.raises(ResultsTrackerError, match="unique"):
        score_goal_markets([forecast], [result, result], 1)
    result["outcome"] = "A"
    with pytest.raises(ResultsTrackerError, match="inconsistent"):
        score_goal_markets([forecast], [result], 1)


def test_publication_guard_accepts_exact_result_and_tracker_artifacts() -> None:
    for path in (
        RESULTS_CSV_PATH,
        MODEL_SCORES_CSV_PATH,
        MODEL_SUMMARY_CSV_PATH,
        RESULTS_JSON_PATH,
        MW2_RESULTS_CSV_PATH,
        MW2_MODEL_SCORES_CSV_PATH,
        MW2_MODEL_SUMMARY_CSV_PATH,
        MW2_RESULTS_JSON_PATH,
        TRACKER_CSV_PATH,
        TRACKER_JSON_PATH,
        BETTING_SELECTIONS_CSV_PATH,
        CUMULATIVE_CSV_PATH,
        GOAL_DEVIATIONS_CSV_PATH,
        DC_SOURCE_PATH,
    ):
        assert inspect_paths([(path.as_posix(), (ROOT / path).read_bytes())]) == []
