"""Pure chronological pre-match features with frozen same-date batches.

Rows are sorted internally, every feature is calculated from information strictly
before the fixture date, and state updates occur only after a complete date batch.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from math import isfinite
from types import MappingProxyType
from typing import Any
from unicodedata import normalize

MODEL_FEATURE_DENYLIST = frozenset(
    {
        "fixture_id",
        "event_time",
        "competition",
        "season",
        "home_team",
        "away_team",
        "home_goals",
        "away_goals",
        "outcome",
    }
)

_STATS = ("shots", "shots_on_target", "corners", "cards", "first_half_goals")
_WINDOWS = (3, 5)


@dataclass(frozen=True)
class ChronologicalConfig:
    """Competition assumptions and numerical guards."""

    matches_per_team: int = 38
    limited_history_threshold: int = 5
    ratio_epsilon: float = 1.0


DEFAULT_CHRONOLOGICAL_CONFIG = ChronologicalConfig()


@dataclass(frozen=True)
class FeatureRow:
    """Identifiers are metadata; only ``features`` is model eligible."""

    fixture_id: str
    event_time: datetime
    competition: str
    season: str
    home_team: str
    away_team: str
    features: Mapping[str, float]


@dataclass
class _TeamState:
    matches: list[dict[str, float]]
    venue_matches: dict[str, list[dict[str, float]]]
    last_played: datetime | None = None


def _parse_time(value: object) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str):
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    else:
        raise ValueError("event_time must be an ISO-8601 string or datetime")
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("event_time must include a timezone")
    return parsed.astimezone(UTC)


def _number(row: Mapping[str, Any], name: str, *, integral: bool = True) -> float | None:
    value = row.get(name)
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be numeric when supplied")
    result = float(value)
    if not isfinite(result):
        raise ValueError(f"{name} must be finite")
    if result < 0:
        raise ValueError(f"{name} must be non-negative")
    if integral and not result.is_integer():
        raise ValueError(f"{name} must be a whole-number count")
    return result


def _mean(history: list[dict[str, float]], key: str, window: int) -> tuple[float, int]:
    values = [item[key] for item in history[-window:] if key in item]
    return (sum(values) / len(values), len(values)) if values else (0.0, 0)


def _points(goals_for: float, goals_against: float) -> float:
    return 3.0 if goals_for > goals_against else 1.0 if goals_for == goals_against else 0.0


def _rank(table: Mapping[str, dict[str, float]], team: str) -> tuple[float, float, float]:
    if not table or team not in table:
        return 0.0, 0.0, 0.0
    entry = table[team]
    sporting_key = (entry["points"], entry["gf"] - entry["ga"], entry["gf"])
    rank = 1 + sum(
        (candidate["points"], candidate["gf"] - candidate["ga"], candidate["gf"]) > sporting_key
        for candidate in table.values()
    )
    return float(rank), entry["points"], entry["gf"] - entry["ga"]


def _normalized_key(
    value: object,
    field: str,
    registry: dict[tuple[str, str], str],
) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field} must be a string")
    key = normalize("NFKC", value).strip()
    if not key:
        raise ValueError(f"{field} must be nonempty after normalization")
    collision_key = (field, key.casefold())
    previous = registry.setdefault(collision_key, value)
    if previous != value:
        raise ValueError(f"{field} normalization collision: {previous!r} and {value!r}")
    return key


def _validate_config(config: ChronologicalConfig) -> None:
    if (
        isinstance(config.matches_per_team, bool)
        or not isinstance(config.matches_per_team, int)
        or config.matches_per_team <= 0
    ):
        raise ValueError("matches_per_team must be a positive integer")
    if (
        isinstance(config.limited_history_threshold, bool)
        or not isinstance(config.limited_history_threshold, int)
        or config.limited_history_threshold < 0
    ):
        raise ValueError("limited_history_threshold must be a non-negative integer")
    if (
        isinstance(config.ratio_epsilon, bool)
        or not isinstance(config.ratio_epsilon, (int, float))
        or not isfinite(float(config.ratio_epsilon))
        or config.ratio_epsilon <= 0
    ):
        raise ValueError("ratio_epsilon must be finite and positive")


def _validate_row(row: Mapping[str, Any]) -> None:
    required = {
        "fixture_id",
        "event_time",
        "competition",
        "season",
        "home_team",
        "away_team",
        "home_goals",
        "away_goals",
    }
    missing = sorted(required - row.keys())
    if missing:
        raise ValueError(f"missing required fields: {', '.join(missing)}")
    forbidden = {key for key in row if key.startswith(("future_", "provider_", "source_"))}
    if forbidden:
        raise ValueError(f"publication-unsafe input fields: {', '.join(sorted(forbidden))}")
    if row["home_team"] == row["away_team"]:
        raise ValueError("home_team and away_team must differ")


def _team_features(
    state: _TeamState,
    venue: str,
    event_time: datetime,
    prefix: str,
    prior_season_matches: int,
    config: ChronologicalConfig,
) -> dict[str, float]:
    result: dict[str, float] = {}
    for window in _WINDOWS:
        for key in ("points", "goals_for", "goals_against") + _STATS:
            value, count = _mean(state.matches, key, window)
            result[f"{prefix}_{key}_last_{window}"] = value
            result[f"{prefix}_{key}_last_{window}_available"] = float(count > 0)
            result[f"{prefix}_{key}_last_{window}_count"] = float(count)
        venue_points, venue_count = _mean(state.venue_matches[venue], "points", window)
        result[f"{prefix}_{venue}_points_last_{window}"] = venue_points
        result[f"{prefix}_{venue}_points_last_{window}_available"] = float(venue_count > 0)
        result[f"{prefix}_{venue}_points_last_{window}_count"] = float(venue_count)
        goals, goals_count = _mean(state.matches, "goals_for", window)
        first_half, phase_count = _mean(state.matches, "first_half_goals", window)
        result[f"{prefix}_first_half_goal_share_last_{window}"] = first_half / (
            goals + config.ratio_epsilon
        )
        share_count = min(goals_count, phase_count)
        result[f"{prefix}_first_half_goal_share_last_{window}_available"] = float(share_count > 0)
        result[f"{prefix}_first_half_goal_share_last_{window}_count"] = float(share_count)
    if state.last_played is None:
        result[f"{prefix}_rest_days"] = 0.0
        result[f"{prefix}_rest_days_available"] = 0.0
        result[f"{prefix}_congested_3d"] = 0.0
    else:
        rest = (event_time - state.last_played).total_seconds() / 86400.0
        if rest <= 0:
            raise ValueError("a team cannot play twice in a frozen date batch")
        result[f"{prefix}_rest_days"] = rest
        result[f"{prefix}_rest_days_available"] = 1.0
        result[f"{prefix}_congested_3d"] = float(rest <= 3.0)
    result[f"{prefix}_cold_start"] = float(len(state.matches) == 0)
    result[f"{prefix}_limited_observed_history"] = float(
        prior_season_matches < config.limited_history_threshold
    )
    return result


def _match_record(row: Mapping[str, Any], side: str) -> dict[str, float]:
    other = "away" if side == "home" else "home"
    goals_for = _number(row, f"{side}_goals", integral=True)
    goals_against = _number(row, f"{other}_goals", integral=True)
    if goals_for is None or goals_against is None:
        raise ValueError("completed rows require home_goals and away_goals")
    record = {
        "points": _points(goals_for, goals_against),
        "goals_for": goals_for,
        "goals_against": goals_against,
    }
    for stat in _STATS:
        value = _number(row, f"{side}_{stat}", integral=True)
        if value is not None:
            record[stat] = value
    return record


def build_chronological_features(
    matches: Iterable[Mapping[str, Any]],
    *,
    config: ChronologicalConfig = DEFAULT_CHRONOLOGICAL_CONFIG,
) -> list[FeatureRow]:
    """Build deterministic, prior-only features from completed fixture rows.

    The returned order is chronological and independent of caller row order. A
    club may appear at most once per competition and UTC date; ambiguity fails
    closed instead of imposing an arbitrary within-day order.
    """

    _validate_config(config)
    prepared: list[tuple[datetime, Mapping[str, Any]]] = []
    fixture_ids: set[str] = set()
    key_registry: dict[tuple[str, str], str] = {}
    for row in matches:
        _validate_row(row)
        normalized = dict(row)
        for field in ("fixture_id", "competition", "season", "home_team", "away_team"):
            registry_field = "team" if field in {"home_team", "away_team"} else field
            normalized[field] = _normalized_key(row[field], registry_field, key_registry)
        if normalized["home_team"].casefold() == normalized["away_team"].casefold():
            raise ValueError("home_team and away_team must differ")
        fixture_id = normalized["fixture_id"]
        if fixture_id in fixture_ids:
            raise ValueError(f"duplicate fixture_id: {fixture_id}")
        fixture_ids.add(fixture_id)
        _match_record(normalized, "home")
        _match_record(normalized, "away")
        prepared.append((_parse_time(normalized["event_time"]), normalized))
    prepared.sort(key=lambda item: (item[0].date(), str(item[1]["fixture_id"])))

    states: defaultdict[tuple[str, str], _TeamState] = defaultdict(
        lambda: _TeamState(matches=[], venue_matches={"home": [], "away": []})
    )
    tables: defaultdict[tuple[str, str], dict[str, dict[str, float]]] = defaultdict(dict)
    prior_season_counts: defaultdict[tuple[str, str, str], int] = defaultdict(int)
    output: list[FeatureRow] = []
    cursor = 0
    while cursor < len(prepared):
        batch_date = prepared[cursor][0].date()
        end = cursor
        while end < len(prepared) and prepared[end][0].date() == batch_date:
            end += 1
        batch = prepared[cursor:end]
        seen: set[tuple[str, str]] = set()
        for event_time, row in batch:
            competition = str(row["competition"])
            season = str(row["season"])
            home = str(row["home_team"])
            away = str(row["away_team"])
            for team in (home, away):
                key = (competition, team)
                if key in seen:
                    raise ValueError(
                        f"ambiguous same-date schedule for {competition}/{team}/{batch_date}"
                    )
                seen.add(key)
            features = {}
            features.update(
                _team_features(
                    states[(competition, home)],
                    "home",
                    event_time,
                    "home",
                    len(states[(competition, home)].matches),
                    config,
                )
            )
            features.update(
                _team_features(
                    states[(competition, away)],
                    "away",
                    event_time,
                    "away",
                    len(states[(competition, away)].matches),
                    config,
                )
            )
            table = tables[(competition, season)]
            home_rank, home_points, home_gd = _rank(table, home)
            away_rank, away_points, away_gd = _rank(table, away)
            played = max(
                prior_season_counts[(competition, season, home)],
                prior_season_counts[(competition, season, away)],
            )
            features.update(
                {
                    "season_progress": min(played / config.matches_per_team, 1.0),
                    "home_table_rank": home_rank,
                    "away_table_rank": away_rank,
                    "home_table_available": float(home in table),
                    "away_table_available": float(away in table),
                    "table_rank_gap": away_rank - home_rank,
                    "table_points_gap": home_points - away_points,
                    "table_goal_difference_gap": home_gd - away_gd,
                }
            )
            for window in _WINDOWS:
                home_gf = features[f"home_goals_for_last_{window}"]
                away_ga = features[f"away_goals_against_last_{window}"]
                features[f"attack_defence_ratio_last_{window}"] = (
                    home_gf + config.ratio_epsilon
                ) / (away_ga + config.ratio_epsilon)
            output.append(
                FeatureRow(
                    fixture_id=str(row["fixture_id"]),
                    event_time=event_time,
                    competition=competition,
                    season=season,
                    home_team=home,
                    away_team=away,
                    features=MappingProxyType(features),
                )
            )
        for event_time, row in batch:
            competition = str(row["competition"])
            season = str(row["season"])
            for side, venue in (("home", "home"), ("away", "away")):
                team = str(row[f"{side}_team"])
                state = states[(competition, team)]
                record = _match_record(row, side)
                state.matches.append(record)
                state.venue_matches[venue].append(record)
                state.last_played = event_time
                prior_season_counts[(competition, season, team)] += 1
                table = tables[(competition, season)]
                entry = table.setdefault(team, {"points": 0.0, "gf": 0.0, "ga": 0.0})
                entry["points"] += record["points"]
                entry["gf"] += record["goals_for"]
                entry["ga"] += record["goals_against"]
        cursor = end
    return output


CHRONOLOGICAL_FEATURE_ALLOWLIST = tuple(
    sorted(
        build_chronological_features(
            [
                {
                    "fixture_id": "schema-example",
                    "event_time": "2030-01-01T12:00:00+00:00",
                    "competition": "fictional",
                    "season": "example",
                    "home_team": "Alpha",
                    "away_team": "Beta",
                    "home_goals": 0,
                    "away_goals": 0,
                }
            ]
        )[0].features
    )
)
