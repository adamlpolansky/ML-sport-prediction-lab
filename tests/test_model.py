from __future__ import annotations

import pytest

from epl_probability_lab.model import SyntheticPoissonModel


def test_probabilities_are_coherent() -> None:
    rows = [
        {
            "home_team": "Amber Owls",
            "away_team": "Azure Rovers",
            "home_goals": "2",
            "away_goals": "1",
        },
        {
            "home_team": "Azure Rovers",
            "away_team": "Amber Owls",
            "home_goals": "0",
            "away_goals": "0",
        },
        {
            "home_team": "Amber Owls",
            "away_team": "Azure Rovers",
            "home_goals": "1",
            "away_goals": "2",
        },
    ]
    probabilities = SyntheticPoissonModel.fit(rows).probabilities("Amber Owls", "Azure Rovers")
    assert set(probabilities) == {"home_win", "draw", "away_win"}
    assert sum(probabilities.values()) == pytest.approx(1.0)
    assert all(0.0 <= value <= 1.0 for value in probabilities.values())


def test_empty_training_window_is_rejected() -> None:
    with pytest.raises(ValueError, match="at least one"):
        SyntheticPoissonModel.fit([])
