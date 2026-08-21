from __future__ import annotations

import random
from dataclasses import FrozenInstanceError

import pytest

from epl_probability_lab.features.chronological import (
    CHRONOLOGICAL_FEATURE_ALLOWLIST,
    MODEL_FEATURE_DENYLIST,
    ChronologicalConfig,
    build_chronological_features,
)


def _matches() -> list[dict[str, object]]:
    base = {
        "competition": "Fictional Test League",
        "season": "Cycle-One",
    }
    return [
        dict(
            base,
            fixture_id="f1",
            event_time="2030-01-01T15:00:00+00:00",
            home_team="Aster",
            away_team="Beacon",
            home_goals=2,
            away_goals=0,
        ),
        dict(
            base,
            fixture_id="f2",
            event_time="2030-01-01T18:00:00+00:00",
            home_team="Cinder",
            away_team="Dapple",
            home_goals=1,
            away_goals=1,
        ),
        dict(
            base,
            fixture_id="f3",
            event_time="2030-01-08T15:00:00+00:00",
            home_team="Beacon",
            away_team="Cinder",
            home_goals=0,
            away_goals=3,
        ),
        dict(
            base,
            fixture_id="f4",
            event_time="2030-01-08T18:00:00+00:00",
            home_team="Dapple",
            away_team="Aster",
            home_goals=1,
            away_goals=2,
        ),
        dict(
            base,
            fixture_id="f5",
            event_time="2030-01-15T15:00:00+00:00",
            home_team="Aster",
            away_team="Cinder",
            home_goals=1,
            away_goals=0,
        ),
        dict(
            base,
            season="Cycle-Two",
            fixture_id="f6",
            event_time="2030-08-01T15:00:00+00:00",
            home_team="Cinder",
            away_team="Aster",
            home_goals=0,
            away_goals=0,
        ),
    ]


def _signature(rows: list[object]) -> list[tuple[str, dict[str, float]]]:
    return [(row.fixture_id, dict(row.features)) for row in rows]  # type: ignore[attr-defined]


def test_row_order_and_temporal_result_invariance_is_non_vacuous() -> None:
    source = _matches()
    shuffled = list(source)
    random.Random(42).shuffle(shuffled)
    baseline = build_chronological_features(source)
    assert _signature(baseline) == _signature(build_chronological_features(shuffled))

    mutated = [dict(row) for row in source]
    mutated[2]["home_goals"] = 9
    changed = build_chronological_features(mutated)
    assert _signature(baseline[:4]) == _signature(changed[:4])
    assert _signature(baseline[4:]) != _signature(changed[4:])
    assert len({row.event_time.date() for row in baseline}) >= 4
    assert len({row.season for row in baseline}) == 2


def test_same_date_is_frozen_and_targets_are_never_features() -> None:
    rows = build_chronological_features(_matches())
    assert rows[0].features["home_cold_start"] == 1.0
    assert rows[1].features["home_cold_start"] == 1.0
    assert rows[2].features["home_points_last_3"] == 0.0
    assert MODEL_FEATURE_DENYLIST.isdisjoint(CHRONOLOGICAL_FEATURE_ALLOWLIST)


def test_ambiguous_same_date_team_fails_closed() -> None:
    bad = _matches()
    bad[1]["home_team"] = "Aster"
    with pytest.raises(ValueError, match="ambiguous same-date schedule"):
        build_chronological_features(bad)


def test_provider_fields_fail_closed() -> None:
    bad = _matches()
    bad[0]["provider_identifier"] = "not-public"
    with pytest.raises(ValueError, match="publication-unsafe"):
        build_chronological_features(bad)


def test_sporting_ties_share_rank_and_renames_do_not_change_numbers() -> None:
    rows = build_chronological_features(_matches())
    assert rows[2].features["away_table_rank"] == rows[3].features["home_table_rank"]
    renamed_source = []
    names = {"Aster": "Zulu", "Beacon": "Yankee", "Cinder": "Xray", "Dapple": "Whiskey"}
    for source in _matches():
        renamed = dict(source)
        renamed["home_team"] = names[str(source["home_team"])]
        renamed["away_team"] = names[str(source["away_team"])]
        renamed_source.append(renamed)
    assert [dict(row.features) for row in rows] == [
        dict(row.features) for row in build_chronological_features(renamed_source)
    ]


def test_window_counts_distinguish_one_observation_from_five() -> None:
    rows = build_chronological_features(_matches())
    assert rows[2].features["home_points_last_5_count"] == 1.0
    assert rows[2].features["home_points_last_5_available"] == 1.0
    assert rows[-1].features["away_points_last_5_count"] > 1.0
    assert "home_promoted_or_new" not in rows[0].features
    assert rows[0].features["home_limited_observed_history"] == 1.0


@pytest.mark.parametrize("bad_value", [float("nan"), float("inf"), -1, 1.5, True])
def test_counts_fail_closed(bad_value: object) -> None:
    rows = _matches()
    rows[0]["home_goals"] = bad_value
    with pytest.raises(ValueError):
        build_chronological_features(rows)


@pytest.mark.parametrize(
    "config",
    [
        ChronologicalConfig(matches_per_team=0),
        ChronologicalConfig(limited_history_threshold=-1),
        ChronologicalConfig(ratio_epsilon=float("nan")),
        ChronologicalConfig(ratio_epsilon=float("inf")),
    ],
)
def test_invalid_configuration_fails_closed(config: ChronologicalConfig) -> None:
    with pytest.raises(ValueError):
        build_chronological_features(_matches(), config=config)


def test_rows_and_feature_mappings_are_immutable() -> None:
    row = build_chronological_features(_matches())[0]
    with pytest.raises(TypeError):
        row.features["home_cold_start"] = 0.0  # type: ignore[index]
    with pytest.raises(FrozenInstanceError):
        row.fixture_id = "changed"  # type: ignore[misc]


def test_empty_and_normalization_colliding_keys_fail_closed() -> None:
    empty = _matches()
    empty[0]["home_team"] = "  "
    with pytest.raises(ValueError, match="nonempty"):
        build_chronological_features(empty)
    collision = _matches()
    collision[2]["home_team"] = " Beacon"
    with pytest.raises(ValueError, match="normalization collision"):
        build_chronological_features(collision)
