from __future__ import annotations

import random

import pytest

from epl_probability_lab.features.chronological import (
    CHRONOLOGICAL_FEATURE_ALLOWLIST,
    MODEL_FEATURE_DENYLIST,
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
    ]


def _signature(rows: list[object]) -> list[tuple[str, dict[str, float]]]:
    return [(row.fixture_id, dict(row.features)) for row in rows]  # type: ignore[attr-defined]


def test_row_order_and_future_result_invariance() -> None:
    source = _matches()
    shuffled = list(source)
    random.Random(42).shuffle(shuffled)
    baseline = build_chronological_features(source)
    assert _signature(baseline) == _signature(build_chronological_features(shuffled))

    mutated = [dict(row) for row in source]
    mutated[-1]["home_goals"] = 99
    assert _signature(baseline) == _signature(build_chronological_features(mutated))


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
