"""Check the headline directly against frozen sources, independently of the tracker."""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SEASON = ROOT / "forecasts/2026-27"


def _observations(week: int, *, dc: bool = False) -> list[dict]:
    directory = SEASON / f"matchday-0{week}"
    forecast = directory / "forecast.json"
    if not dc:
        model = "elo-poisson-v1" if week == 1 else "elo-poisson-v1-post-mw1"
        forecast = directory / "challengers" / model / "forecast.json"
    rows = json.loads(forecast.read_bytes())
    with (directory / "results/results.csv").open(encoding="utf-8", newline="") as handle:
        outcomes = {row["fixture_key"]: row for row in csv.DictReader(handle)}
    supplement = json.loads((SEASON / "tracking/dc_mw1_goal_markets.json").read_bytes())
    dc_markets = {row["fixture_key"]: row for row in supplement["markets"]}
    observations = []
    for row in rows:
        actual = outcomes[row["fixture_key"]]
        hg, ag = int(actual["home_goals"]), int(actual["away_goals"])
        h = row["expected_home_goals"] if dc else row["lambda_home"]
        a = row["expected_away_goals"] if dc else row["lambda_away"]
        probs = (
            row["p_home_win"] if dc else row["p_home"],
            row["p_draw"],
            row["p_away_win"] if dc else row["p_away"],
        )
        predicted = "HDA"[probs.index(max(probs))]
        over = 1 - math.exp(-h - a) * (1 + h + a + (h + a) ** 2 / 2)
        btts = (1 - math.exp(-h)) * (1 - math.exp(-a))
        if dc:
            over, btts = (dc_markets[row["fixture_key"]][k] for k in ("p_over_2_5", "p_btts"))
        observations.append(
            {
                "correct": predicted == actual["outcome"],
                "over_selected": over != 0.5,
                "over_won": (hg + ag > 2) == (over > 0.5),
                "btts_selected": btts != 0.5,
                "btts_won": (hg > 0 and ag > 0) == (btts > 0.5),
                "mae": (abs(hg - h) + abs(ag - a)) / 2,
                "bias": (hg + ag - h - a) / 2,
            }
        )
    return observations


def _ratio(won: int, count: int) -> str:
    percentage = f"{100 * won / count:.1f}".removesuffix(".0")
    return f"{won} / {count} ({percentage}%)"


@pytest.mark.parametrize("dc,weeks", [(True, (1,)), (False, (1,)), (False, (2,)), (False, (1, 2))])
def test_readme_separates_all_fixture_picks_from_each_selected_market(dc, weeks):
    rows = [row for week in weeks for row in _observations(week, dc=dc)]
    model = "Dynamic Dixon–Coles" if dc else "Elo–Poisson"
    period = f"MW{weeks[0]}" if len(weeks) == 1 else "MW1–2 combined"
    cells = [model, period, _ratio(sum(row["correct"] for row in rows), len(rows))]
    for market in ("over", "btts"):
        selected = [row for row in rows if row[f"{market}_selected"]]
        cells.append(_ratio(sum(row[f"{market}_won"] for row in selected), len(selected)))
    cells.append(f"{sum(row['mae'] for row in rows) / len(rows):.3f} goals")
    assert "| " + " | ".join(cells) + " |" in (ROOT / "README.md").read_text(encoding="utf-8")


def test_readme_describes_goal_bias_with_the_correct_sign_and_unit():
    rows = _observations(1) + _observations(2)
    bias = sum(row["bias"] for row in rows) / len(rows)
    assert bias > 0
    assert f"expectation by **{bias:.3f} goals per team**" in (ROOT / "README.md").read_text(
        encoding="utf-8"
    )
