"""A small coherent score-distribution model for the synthetic demo."""

from __future__ import annotations

import math
from collections.abc import Iterable
from dataclasses import asdict, dataclass

DISCLAIMER = "Synthetic demonstration — not evidence of real-world predictive performance."


def _poisson_prob(rate: float, goals: int) -> float:
    return math.exp(-rate) * rate**goals / math.factorial(goals)


@dataclass(frozen=True)
class SyntheticPoissonModel:
    """Independent Poisson goals with synthetic-only, smoothed team rates."""

    mean_home_goals: float
    mean_away_goals: float
    team_attack: dict[str, float]
    team_defence: dict[str, float]
    training_rows: int
    max_goals: int = 10
    training_data_kind: str = "synthetic"
    disclaimer: str = DISCLAIMER

    @classmethod
    def fit(cls, rows: Iterable[dict[str, str]], max_goals: int = 10) -> SyntheticPoissonModel:
        materialized = list(rows)
        if not materialized:
            raise ValueError("at least one synthetic training row is required")
        home_total = sum(int(row["home_goals"]) for row in materialized)
        away_total = sum(int(row["away_goals"]) for row in materialized)
        teams = sorted(
            {row["home_team"] for row in materialized} | {row["away_team"] for row in materialized}
        )
        total_goals = home_total + away_total
        mean_team_goals = total_goals / (2 * len(materialized))
        prior_matches = 6
        attack: dict[str, float] = {}
        defence: dict[str, float] = {}
        for team in teams:
            team_rows = [
                row for row in materialized if row["home_team"] == team or row["away_team"] == team
            ]
            scored = sum(
                int(row["home_goals"] if row["home_team"] == team else row["away_goals"])
                for row in team_rows
            )
            conceded = sum(
                int(row["away_goals"] if row["home_team"] == team else row["home_goals"])
                for row in team_rows
            )
            denominator = len(team_rows) + prior_matches
            attack[team] = (scored + prior_matches * mean_team_goals) / denominator
            defence[team] = (conceded + prior_matches * mean_team_goals) / denominator
        return cls(
            mean_home_goals=home_total / len(materialized),
            mean_away_goals=away_total / len(materialized),
            team_attack=attack,
            team_defence=defence,
            training_rows=len(materialized),
            max_goals=max_goals,
        )

    def expected_goals(self, home_team: str, away_team: str) -> tuple[float, float]:
        if home_team not in self.team_attack or away_team not in self.team_attack:
            raise ValueError("both fictional teams must occur in the synthetic training window")
        baseline = (self.mean_home_goals + self.mean_away_goals) / 2
        home_rate = (
            self.mean_home_goals
            * self.team_attack[home_team]
            * self.team_defence[away_team]
            / baseline**2
        )
        away_rate = (
            self.mean_away_goals
            * self.team_attack[away_team]
            * self.team_defence[home_team]
            / baseline**2
        )
        return max(0.2, min(home_rate, 3.5)), max(0.2, min(away_rate, 3.5))

    def probabilities(self, home_team: str, away_team: str) -> dict[str, float]:
        home_rate, away_rate = self.expected_goals(home_team, away_team)
        home = draw = away = 0.0
        for home_goals in range(self.max_goals + 1):
            home_p = _poisson_prob(home_rate, home_goals)
            for away_goals in range(self.max_goals + 1):
                probability = home_p * _poisson_prob(away_rate, away_goals)
                if home_goals > away_goals:
                    home += probability
                elif home_goals == away_goals:
                    draw += probability
                else:
                    away += probability
        retained_mass = home + draw + away
        return {
            "home_win": home / retained_mass,
            "draw": draw / retained_mass,
            "away_win": away / retained_mass,
        }

    def to_dict(self) -> dict[str, object]:
        return asdict(self)
