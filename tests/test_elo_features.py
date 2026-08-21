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
    run_fixed_elo,
    run_tier_seeded_elo,
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
    changed = [dict(row) for row in matches]
    changed[-1]["home_goals"] = 99
    assert _features(run_fixed_elo(matches)) == _features(run_fixed_elo(changed))


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
