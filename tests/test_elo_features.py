from __future__ import annotations

import math
import random

import pytest

from epl_probability_lab.features.elo import (
    TIER_ELO_EMPIRICAL_STATUS,
    TIER_ELO_IMPLEMENTATION_STATUS,
    TIER_ELO_PROMOTION_STATUS,
    EloConfig,
    TierSeedConfig,
    center_anchors,
    expected_home_score,
    run_fixed_elo,
    run_tier_seeded_elo,
    tier_season_start,
)


def _season() -> list[dict[str, object]]:
    rows = []
    teams = [f"Fictional-{index:02d}" for index in range(20)]
    for index in range(10):
        rows.append(
            {
                "fixture_id": f"fixture-{index:02d}",
                "event_time": "2031-09-01T15:00:00+00:00",
                "competition": "Fictional Test League",
                "season": "Cycle-One",
                "home_team": teams[index],
                "away_team": teams[-index - 1],
                "home_goals": index % 3,
                "away_goals": (index + 1) % 3,
            }
        )
    return rows


def _features(run: object) -> list[tuple[str, dict[str, float]]]:
    return [(row.fixture_id, dict(row.features)) for row in run.rows]  # type: ignore[attr-defined]


def test_fixed_defaults_batching_order_and_zero_sum() -> None:
    config = EloConfig()
    assert (config.rating_scale, config.home_advantage, config.k_factor) == (400.0, 60.0, 20.0)
    matches = _season()
    shuffled = list(matches)
    random.Random(9).shuffle(shuffled)
    run = run_fixed_elo(matches)
    assert _features(run) == _features(run_fixed_elo(shuffled))
    assert run.update_balance == 0.0
    assert math.isclose(sum(run.final_ratings.values()), 20 * 1500.0)
    assert all(row.home_rating == 1500.0 and row.away_rating == 1500.0 for row in run.rows)


def test_future_result_cannot_change_prior_elo_rows() -> None:
    matches = _season()
    matches.append(
        {
            **matches[0],
            "fixture_id": "later-fixture",
            "event_time": "2031-09-08T15:00:00+00:00",
            "home_team": matches[0]["away_team"],
            "away_team": matches[0]["home_team"],
        }
    )
    changed = [dict(row) for row in matches]
    changed[0]["home_goals"] = 9
    baseline = _features(run_fixed_elo(matches))
    mutated = _features(run_fixed_elo(changed))
    assert baseline[:-1] == mutated[:-1]
    assert baseline[-1] != mutated[-1]


def test_complete_centering_and_incomplete_failure() -> None:
    anchors = {f"Fictional-{index:02d}": 1400.0 + index * 10 for index in range(20)}
    centered = center_anchors(anchors)
    assert math.isclose(sum(centered.values()) / 20, 1500.0)
    with pytest.raises(ValueError, match="exactly 20"):
        center_anchors(dict(list(anchors.items())[:-1]))


def test_fixed_and_tier_paths_match_with_identical_anchors() -> None:
    matches = _season()
    season_key = ("Fictional Test League", "Cycle-One")
    teams = {str(row[side]) for row in matches for side in ("home_team", "away_team")}
    anchors = {team: 1500.0 for team in teams}
    fixed = run_fixed_elo(matches, initial_ratings={season_key: anchors})
    tier = run_tier_seeded_elo(matches, {season_key: anchors})
    assert _features(fixed) == _features(tier)
    assert TIER_ELO_IMPLEMENTATION_STATUS == "IMPLEMENTED_AND_SYNTHETICALLY_VERIFIED"
    assert TIER_ELO_EMPIRICAL_STATUS == "NOT_EVALUATED"
    assert TIER_ELO_PROMOTION_STATUS is False


def test_complete_anchor_table_accepts_a_partial_fixture_window() -> None:
    matches = _season()
    season_key = ("Fictional Test League", "Cycle-One")
    anchors = {f"Fictional-{index:02d}": 1500.0 for index in range(20)}
    assert len(run_tier_seeded_elo(matches[:1], {season_key: anchors}).rows) == 1
    with pytest.raises(ValueError, match="exact 20-club"):
        center_anchors(dict(list(anchors.items())[:-1]), TierSeedConfig(club_count=19))


def test_tier_continuity_blend_promoted_anchor_and_recentering_are_exact() -> None:
    anchors = {f"Fictional-{index:02d}": 1405.0 + index * 10 for index in range(20)}
    centered = center_anchors(anchors)
    returning = dict(list(centered.items())[:-1])
    previous = {team: rating + 40.0 for team, rating in returning.items()}
    actual = tier_season_start(centered, previous)
    provisional = {
        team: 0.75 * previous[team] + 0.25 * anchor if team in previous else anchor
        for team, anchor in centered.items()
    }
    recenter = sum(provisional.values()) / 20.0
    expected = {team: 1500.0 + rating - recenter for team, rating in provisional.items()}
    assert actual == pytest.approx(expected)
    promoted = "Fictional-19"
    assert provisional[promoted] == centered[promoted]
    assert math.isclose(sum(actual.values()), 20 * 1500.0)


@pytest.mark.parametrize(
    "config",
    [
        EloConfig(rating_scale=0),
        EloConfig(rating_scale=float("nan")),
        EloConfig(k_factor=-1),
        EloConfig(home_advantage=float("inf")),
        EloConfig(base_rating=float("nan")),
    ],
)
def test_invalid_elo_configuration_fails_closed(config: EloConfig) -> None:
    with pytest.raises(ValueError):
        run_fixed_elo(_season(), config=config)


@pytest.mark.parametrize("weight", [-0.1, 1.1, float("nan"), float("inf")])
def test_invalid_tier_weight_fails_closed(weight: float) -> None:
    anchors = {f"Fictional-{index:02d}": 1500.0 for index in range(20)}
    with pytest.raises(ValueError):
        center_anchors(anchors, TierSeedConfig(continuing_weight=weight))


@pytest.mark.parametrize("bad_value", [float("nan"), float("inf"), -1, 1.5, True])
def test_invalid_goals_never_become_losses(bad_value: object) -> None:
    rows = _season()
    rows[0]["home_goals"] = bad_value
    with pytest.raises(ValueError):
        run_fixed_elo(rows)


def test_stable_logistic_handles_extreme_finite_rating_gaps() -> None:
    assert expected_home_score(1e308, -1e308) == 1.0
    assert expected_home_score(-1e308, 1e308) == 0.0


def test_initial_ratings_and_outputs_are_finite_and_immutable() -> None:
    matches = _season()
    season_key = ("Fictional Test League", "Cycle-One")
    with pytest.raises(ValueError, match="finite"):
        run_fixed_elo(matches, initial_ratings={season_key: {"Fictional-00": float("nan")}})
    run = run_fixed_elo(matches)
    with pytest.raises(TypeError):
        run.final_ratings[("Fictional Test League", "Fictional-00")] = 0.0  # type: ignore[index]
    with pytest.raises(TypeError):
        run.rows[0].features["elo_home_rating"] = 0.0  # type: ignore[index]


def test_club_renaming_cannot_change_numeric_elo_features() -> None:
    matches = _season()
    renamed = []
    names = {f"Fictional-{index:02d}": f"Renamed-{19 - index:02d}" for index in range(20)}
    for row in matches:
        changed = dict(row)
        changed["home_team"] = names[str(row["home_team"])]
        changed["away_team"] = names[str(row["away_team"])]
        renamed.append(changed)
    assert [dict(row.features) for row in run_fixed_elo(matches).rows] == [
        dict(row.features) for row in run_fixed_elo(renamed).rows
    ]
