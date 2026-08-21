from __future__ import annotations

import pytest

from epl_probability_lab.features.context import ManagerSpell, build_manager_context


def _match(event_time: str = "2030-02-10T15:00:00+00:00") -> dict[str, str]:
    return {
        "fixture_id": "fictional-fixture",
        "event_time": event_time,
        "home_team": "Aster",
        "away_team": "Beacon",
    }


def test_unknown_is_explicitly_unavailable() -> None:
    row = build_manager_context([_match()], [])[0]
    assert row.features["home_manager_available"] == 0.0
    assert row.features["away_manager_available"] == 0.0


def test_known_spell_is_prior_only_and_identity_is_not_a_feature() -> None:
    spell = ManagerSpell(
        team="Aster",
        person_key="fictional-person",
        event_known_at="2030-01-01T12:00:00+00:00",
        effective_start="2030-01-02T12:00:00+00:00",
        caretaker=True,
    )
    row = build_manager_context([_match()], [spell])[0]
    assert row.features["home_manager_available"] == 1.0
    assert row.features["home_manager_caretaker"] == 1.0
    assert row.features["home_manager_tenure_days"] == pytest.approx(39.125)
    assert row.features["away_manager_available"] == 0.0
    assert all("person" not in name and "identity" not in name for name in row.features)


def test_same_day_effective_record_fails_closed() -> None:
    spell = ManagerSpell(
        team="Aster",
        person_key="fictional-person",
        event_known_at="2030-02-09T12:00:00+00:00",
        effective_start="2030-02-10T09:00:00+00:00",
    )
    with pytest.raises(ValueError, match="ambiguous same-day"):
        build_manager_context([_match()], [spell])


def test_later_event_mutation_cannot_change_prior_rows() -> None:
    base = ManagerSpell(
        team="Aster",
        person_key="fictional-one",
        event_known_at="2030-01-01T12:00:00+00:00",
        effective_start="2030-01-02T12:00:00+00:00",
        effective_end="2030-02-20T12:00:00+00:00",
    )
    future_one = ManagerSpell(
        team="Aster",
        person_key="fictional-two",
        event_known_at="2030-03-01T12:00:00+00:00",
        effective_start="2030-03-02T12:00:00+00:00",
    )
    future_two = ManagerSpell(
        team="Aster",
        person_key="fictional-three",
        event_known_at="2030-04-01T12:00:00+00:00",
        effective_start="2030-04-02T12:00:00+00:00",
    )
    first = build_manager_context([_match()], [base, future_one])[0]
    second = build_manager_context([_match()], [base, future_two])[0]
    assert first.features == second.features


def test_home_and_away_tenure_matches_and_same_date_batch_are_prior_only() -> None:
    matches = [
        {
            "fixture_id": "past-a",
            "event_time": "2030-02-01T15:00:00+00:00",
            "home_team": "Aster",
            "away_team": "Cinder",
        },
        {
            "fixture_id": "past-b",
            "event_time": "2030-02-01T18:00:00+00:00",
            "home_team": "Beacon",
            "away_team": "Dapple",
        },
        _match(),
    ]
    spells = [
        ManagerSpell(
            team=team,
            person_key=f"person-{team}",
            event_known_at="2030-01-01T00:00:00+00:00",
            effective_start="2030-01-02T00:00:00+00:00",
        )
        for team in ("Aster", "Beacon", "Cinder", "Dapple")
    ]
    rows = build_manager_context(matches, spells)
    assert rows[0].features["home_manager_matches_in_charge"] == 0.0
    assert rows[1].features["home_manager_matches_in_charge"] == 0.0
    assert rows[2].features["home_manager_matches_in_charge"] == 1.0
    assert rows[2].features["away_manager_matches_in_charge"] == 1.0


def test_spell_end_overlap_and_invalid_interval_fail_closed() -> None:
    ended = ManagerSpell(
        team="Aster",
        person_key="former",
        event_known_at="2030-01-01T00:00:00+00:00",
        effective_start="2030-01-02T00:00:00+00:00",
        effective_end="2030-02-01T00:00:00+00:00",
    )
    assert build_manager_context([_match()], [ended])[0].features["home_manager_available"] == 0.0
    overlapping = ManagerSpell(
        team="Aster",
        person_key="overlap",
        event_known_at="2030-01-10T00:00:00+00:00",
        effective_start="2030-01-20T00:00:00+00:00",
    )
    with pytest.raises(ValueError, match="overlapping"):
        build_manager_context([_match()], [ended, overlapping])
    bad_interval = ManagerSpell(
        team="Aster",
        person_key="bad-interval",
        event_known_at="2030-01-01T00:00:00+00:00",
        effective_start="2030-01-02T00:00:00+00:00",
        effective_end="2030-01-01T00:00:00+00:00",
    )
    with pytest.raises(ValueError, match="end must follow start"):
        build_manager_context([_match()], [bad_interval])


def test_context_mappings_are_immutable_and_key_collisions_fail_closed() -> None:
    row = build_manager_context([_match()], [])[0]
    with pytest.raises(TypeError):
        row.features["home_manager_available"] = 1.0  # type: ignore[index]
    matches = [_match(), {**_match("2030-02-17T15:00:00+00:00"), "fixture_id": "two"}]
    matches[1]["home_team"] = " Aster"
    with pytest.raises(ValueError, match="normalization collision"):
        build_manager_context(matches, [])
