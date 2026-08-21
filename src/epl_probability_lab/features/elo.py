"""Deterministic fixed and caller-seeded Elo ratings."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from math import exp
from typing import Any

TIER_ELO_IMPLEMENTATION_STATUS = "IMPLEMENTED_AND_SYNTHETICALLY_VERIFIED"
TIER_ELO_EMPIRICAL_STATUS = "NOT_EVALUATED"
TIER_ELO_PROMOTION_STATUS = False

DEFAULT_TIER_ANCHORS: Mapping[str, float] = {
    "UCL": 1600.0,
    "UEL": 1560.0,
    "UECL": 1530.0,
    "NON_EUROPEAN_TOP_10": 1510.0,
    "NON_EUROPEAN_11_17": 1470.0,
    "PROMOTED_OR_RETURNING": 1420.0,
}


@dataclass(frozen=True)
class EloConfig:
    rating_scale: float = 400.0
    home_advantage: float = 60.0
    k_factor: float = 20.0
    base_rating: float = 1500.0


@dataclass(frozen=True)
class TierSeedConfig:
    base_rating: float = 1500.0
    continuing_weight: float = 0.75
    club_count: int = 20


DEFAULT_ELO_CONFIG = EloConfig()
DEFAULT_TIER_CONFIG = TierSeedConfig()


@dataclass(frozen=True)
class EloFeatureRow:
    fixture_id: str
    event_time: datetime
    competition: str
    season: str
    home_team: str
    away_team: str
    home_rating: float
    away_rating: float
    rating_difference: float
    expected_home_score: float

    @property
    def features(self) -> Mapping[str, float]:
        return {
            "elo_home_rating": self.home_rating,
            "elo_away_rating": self.away_rating,
            "elo_rating_difference": self.rating_difference,
            "elo_expected_home_score": self.expected_home_score,
        }


@dataclass(frozen=True)
class EloRun:
    rows: tuple[EloFeatureRow, ...]
    final_ratings: Mapping[tuple[str, str], float]
    update_balance: float


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


def expected_home_score(home: float, away: float, config: EloConfig = DEFAULT_ELO_CONFIG) -> float:
    """Return the standard logistic Elo expectation including home advantage."""

    if config.rating_scale <= 0:
        raise ValueError("rating_scale must be positive")
    exponent = (away - home - config.home_advantage) / config.rating_scale
    return 1.0 / (1.0 + exp(exponent * 2.302585092994046))


def _actual_score(row: Mapping[str, Any]) -> float:
    home = row.get("home_goals")
    away = row.get("away_goals")
    if isinstance(home, bool) or isinstance(away, bool):
        raise ValueError("goals must be numeric")
    if not isinstance(home, (int, float)) or not isinstance(away, (int, float)):
        raise ValueError("completed rows require numeric goals")
    return 1.0 if home > away else 0.5 if home == away else 0.0


def _prepare(matches: Iterable[Mapping[str, Any]]) -> list[tuple[datetime, Mapping[str, Any]]]:
    rows: list[tuple[datetime, Mapping[str, Any]]] = []
    ids: set[str] = set()
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
    for row in matches:
        missing = required - row.keys()
        if missing:
            raise ValueError(f"missing required fields: {', '.join(sorted(missing))}")
        fixture_id = str(row["fixture_id"])
        if fixture_id in ids:
            raise ValueError(f"duplicate fixture_id: {fixture_id}")
        if row["home_team"] == row["away_team"]:
            raise ValueError("home_team and away_team must differ")
        ids.add(fixture_id)
        rows.append((_parse_time(row["event_time"]), row))
    rows.sort(key=lambda item: (item[0].date(), str(item[1]["fixture_id"])))
    return rows


def _run(
    matches: Iterable[Mapping[str, Any]],
    *,
    initial_by_season: Mapping[tuple[str, str], Mapping[str, float]] | None,
    config: EloConfig,
) -> EloRun:
    if config.k_factor <= 0:
        raise ValueError("k_factor must be positive")
    prepared = _prepare(matches)
    ratings: dict[tuple[str, str], float] = {}
    initialized_seasons: set[tuple[str, str]] = set()
    rows: list[EloFeatureRow] = []
    update_balance = 0.0
    cursor = 0
    while cursor < len(prepared):
        date = prepared[cursor][0].date()
        end = cursor
        while end < len(prepared) and prepared[end][0].date() == date:
            end += 1
        batch = prepared[cursor:end]
        seen: set[tuple[str, str]] = set()
        pending: list[tuple[tuple[str, str], float]] = []
        for event_time, row in batch:
            competition = str(row["competition"])
            season = str(row["season"])
            season_key = (competition, season)
            if season_key not in initialized_seasons:
                for team, rating in (initial_by_season or {}).get(season_key, {}).items():
                    ratings[(competition, str(team))] = float(rating)
                initialized_seasons.add(season_key)
            home = str(row["home_team"])
            away = str(row["away_team"])
            for team in (home, away):
                key = (competition, team)
                if key in seen:
                    raise ValueError(
                        f"ambiguous same-date schedule for {competition}/{team}/{date}"
                    )
                seen.add(key)
                ratings.setdefault(key, config.base_rating)
            home_rating = ratings[(competition, home)]
            away_rating = ratings[(competition, away)]
            expected = expected_home_score(home_rating, away_rating, config)
            delta = config.k_factor * (_actual_score(row) - expected)
            pending.extend([((competition, home), delta), ((competition, away), -delta)])
            update_balance += delta - delta
            rows.append(
                EloFeatureRow(
                    fixture_id=str(row["fixture_id"]),
                    event_time=event_time,
                    competition=competition,
                    season=season,
                    home_team=home,
                    away_team=away,
                    home_rating=home_rating,
                    away_rating=away_rating,
                    rating_difference=home_rating - away_rating,
                    expected_home_score=expected,
                )
            )
        for key, delta in pending:
            ratings[key] += delta
        cursor = end
    return EloRun(rows=tuple(rows), final_ratings=ratings, update_balance=update_balance)


def run_fixed_elo(
    matches: Iterable[Mapping[str, Any]],
    *,
    initial_ratings: Mapping[tuple[str, str], Mapping[str, float]] | None = None,
    config: EloConfig = DEFAULT_ELO_CONFIG,
) -> EloRun:
    """Run fixed Elo with frozen same-date updates."""

    return _run(matches, initial_by_season=initial_ratings, config=config)


def center_anchors(
    raw_anchors: Mapping[str, float], config: TierSeedConfig = DEFAULT_TIER_CONFIG
) -> dict[str, float]:
    """Center a complete caller-provided preseason table on the base rating."""

    if config.club_count != 20:
        raise ValueError("public tier Elo requires an exact 20-club table")
    if len(raw_anchors) != config.club_count:
        raise ValueError(f"tier anchor table must contain exactly {config.club_count} clubs")
    if len(set(raw_anchors)) != config.club_count:
        raise ValueError("tier anchor table contains duplicate clubs")
    mean = sum(float(value) for value in raw_anchors.values()) / config.club_count
    return {
        str(team): config.base_rating + float(anchor) - mean for team, anchor in raw_anchors.items()
    }


def anchors_from_tiers(
    tiers: Mapping[str, str],
    *,
    anchor_scale: Mapping[str, float] = DEFAULT_TIER_ANCHORS,
    config: TierSeedConfig = DEFAULT_TIER_CONFIG,
) -> dict[str, float]:
    """Resolve generic caller tier labels, then center the complete table."""

    unknown = sorted({tier for tier in tiers.values() if tier not in anchor_scale})
    if unknown:
        raise ValueError(f"unknown tier labels: {', '.join(unknown)}")
    return center_anchors({team: anchor_scale[tier] for team, tier in tiers.items()}, config)


def tier_season_start(
    centered_anchors: Mapping[str, float],
    previous_end: Mapping[str, float] | None = None,
    *,
    config: TierSeedConfig = DEFAULT_TIER_CONFIG,
) -> dict[str, float]:
    """Blend returning clubs with anchors and recenter the provisional table."""

    centered = center_anchors(centered_anchors, config)
    previous = previous_end or {}
    provisional = {
        team: (
            config.continuing_weight * float(previous[team])
            + (1.0 - config.continuing_weight) * anchor
            if team in previous
            else anchor
        )
        for team, anchor in centered.items()
    }
    mean = sum(provisional.values()) / config.club_count
    return {team: config.base_rating + value - mean for team, value in provisional.items()}


def run_tier_seeded_elo(
    matches: Iterable[Mapping[str, Any]],
    preseason_anchors: Mapping[tuple[str, str], Mapping[str, float]],
    *,
    config: EloConfig = DEFAULT_ELO_CONFIG,
    tier_config: TierSeedConfig = DEFAULT_TIER_CONFIG,
) -> EloRun:
    """Run Elo from complete, generic caller-supplied season anchor tables."""

    prepared = _prepare(matches)
    source_rows = [row for _, row in prepared]
    season_order: list[tuple[str, str]] = []
    season_teams: dict[tuple[str, str], set[str]] = {}
    for _, row in prepared:
        key = (str(row["competition"]), str(row["season"]))
        if key not in season_teams:
            season_order.append(key)
            season_teams[key] = set()
        season_teams[key].update((str(row["home_team"]), str(row["away_team"])))
    starts: dict[tuple[str, str], Mapping[str, float]] = {}
    previous_by_competition: dict[str, dict[str, float]] = {}
    for season_key in season_order:
        raw = preseason_anchors.get(season_key)
        if raw is None:
            raise ValueError(f"missing tier anchor table for {season_key}")
        if len(raw) != tier_config.club_count or not season_teams[season_key].issubset(raw):
            raise ValueError(f"tier anchor table is incomplete for {season_key}")
        competition = season_key[0]
        starts[season_key] = tier_season_start(
            center_anchors(raw, tier_config),
            previous_by_competition.get(competition),
            config=tier_config,
        )
        season_rows = [
            row for _, row in prepared if season_key == (row["competition"], row["season"])
        ]
        partial = _run(
            season_rows,
            initial_by_season={season_key: starts[season_key]},
            config=config,
        )
        previous_by_competition[competition] = {
            team: rating
            for (comp, team), rating in partial.final_ratings.items()
            if comp == competition
        }
    return _run(source_rows, initial_by_season=starts, config=config)
