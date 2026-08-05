from __future__ import annotations

from epl_probability_lab.model import DISCLAIMER
from epl_probability_lab.synthetic import TEAMS, generate_fixtures


def test_fixture_generation_is_deterministic_and_fictional() -> None:
    first = generate_fixtures(seed=17, row_count=96)
    second = generate_fixtures(seed=17, row_count=96)
    assert first == second
    assert len(first) == 96
    assert {row["home_team"] for row in first} <= set(TEAMS)
    assert {row["away_team"] for row in first} <= set(TEAMS)
    assert all(row["fixture_id"].startswith("SYN-") for row in first)
    assert all(row["data_kind"] == "synthetic" for row in first)
    assert all(row["disclaimer"] == DISCLAIMER for row in first)


def test_invalid_row_count_is_rejected() -> None:
    try:
        generate_fixtures(seed=17, row_count=0)
    except ValueError as error:
        assert "positive" in str(error)
    else:
        raise AssertionError("zero rows should be rejected")
