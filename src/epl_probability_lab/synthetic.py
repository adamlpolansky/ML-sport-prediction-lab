"""Deterministic generation of fictional football fixtures."""

from __future__ import annotations

import csv
import math
import random
from datetime import date, timedelta
from pathlib import Path

from .model import DISCLAIMER

TEAMS = (
    "Amber Owls",
    "Azure Rovers",
    "Copper Comets",
    "Golden Kites",
    "Ivory Foxes",
    "Jade Harriers",
    "Silver Pines",
    "Violet Sparks",
)

_SYNTHETIC_STRENGTH = {
    team: strength
    for team, strength in zip(TEAMS, (-0.55, -0.35, -0.15, 0.0, 0.1, 0.25, 0.4, 0.55), strict=True)
}

FIELDNAMES = (
    "fixture_id",
    "match_date",
    "home_team",
    "away_team",
    "home_goals",
    "away_goals",
    "result",
    "data_kind",
    "disclaimer",
)


def _poisson_sample(rng: random.Random, rate: float) -> int:
    threshold = math.exp(-rate)
    product = 1.0
    value = -1
    while product > threshold:
        value += 1
        product *= rng.random()
    return value


def generate_fixtures(seed: int, row_count: int) -> list[dict[str, str]]:
    """Generate ordered fictional fixtures with deterministic synthetic outcomes."""
    if row_count < 1:
        raise ValueError("row_count must be positive")
    rng = random.Random(seed)
    ordered_pairs = [(home, away) for home in TEAMS for away in TEAMS if home != away]
    rows: list[dict[str, str]] = []
    start = date(2032, 1, 3)
    for index in range(row_count):
        home, away = ordered_pairs[index % len(ordered_pairs)]
        strength_gap = _SYNTHETIC_STRENGTH[home] - _SYNTHETIC_STRENGTH[away]
        home_rate = math.exp(0.28 + 0.32 * strength_gap)
        away_rate = math.exp(-0.03 - 0.28 * strength_gap)
        home_goals = _poisson_sample(rng, home_rate)
        away_goals = _poisson_sample(rng, away_rate)
        result = "H" if home_goals > away_goals else "D" if home_goals == away_goals else "A"
        rows.append(
            {
                "fixture_id": f"SYN-{index + 1:04d}",
                "match_date": (start + timedelta(days=index)).isoformat(),
                "home_team": home,
                "away_team": away,
                "home_goals": str(home_goals),
                "away_goals": str(away_goals),
                "result": result,
                "data_kind": "synthetic",
                "disclaimer": DISCLAIMER,
            }
        )
    return rows


def write_fixtures(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
