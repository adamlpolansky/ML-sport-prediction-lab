"""Deterministic fixed and caller-seeded Elo ratings."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from math import exp, fsum, isfinite, log
from types import MappingProxyType
from typing import Any
from unicodedata import normalize

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
        return MappingProxyType(
            {
                "elo_home_rating": self.home_rating,
                "elo_away_rating": self.away_rating,
                "elo_rating_difference": self.rating_difference,
                "elo_expected_home_score": self.expected_home_score,
            }
        )


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

    _validate_elo_config(config)
    home_rating = _finite_number(home, "home rating")
    away_rating = _finite_number(away, "away rating")
    exponent = (
        (away_rating - home_rating - float(config.home_advantage))
        / float(config.rating_scale)
        * log(10.0)
    )
    if exponent >= 0.0:
        inverse = exp(-exponent)
        return inverse / (1.0 + inverse)
    return 1.0 / (1.0 + exp(exponent))


def _finite_number(value: object, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field} must be numeric")
    result = float(value)
    if not isfinite(result):
        raise ValueError(f"{field} must be finite")
    return result


def _normalized_key(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field} must be a string")
    result = normalize("NFKC", value).strip()
    if not result:
        raise ValueError(f"{field} must be nonempty after normalization")
    return result


def _validate_elo_config(config: EloConfig) -> None:
    scale = _finite_number(config.rating_scale, "rating_scale")
    _finite_number(config.home_advantage, "home_advantage")
    k_factor = _finite_number(config.k_factor, "k_factor")
    _finite_number(config.base_rating, "base_rating")
    if scale <= 0:
        raise ValueError("rating_scale must be positive")
    if k_factor <= 0:
        raise ValueError("k_factor must be positive")


def _validate_tier_config(config: TierSeedConfig) -> None:
    _finite_number(config.base_rating, "tier base_rating")
    weight = _finite_number(config.continuing_weight, "continuing_weight")
    if not 0.0 <= weight <= 1.0:
        raise ValueError("continuing_weight must be between zero and one")
    if isinstance(config.club_count, bool) or not isinstance(config.club_count, int):
        raise ValueError("club_count must be an integer")
    if config.club_count != 20:
        raise ValueError("public tier Elo requires an exact 20-club table")


def _normalized_ratings(values: Mapping[str, float], field: str) -> dict[str, float]:
    result: dict[str, float] = {}
    raw_by_folded: dict[str, str] = {}
    for raw_team, raw_rating in values.items():
        team = _normalized_key(raw_team, f"{field} team")
        folded = team.casefold()
        previous = raw_by_folded.setdefault(folded, raw_team)
        if previous != raw_team:
            raise ValueError(f"{field} team normalization collision")
        result[team] = _finite_number(raw_rating, f"{field} rating for {team}")
    return result


def _normalized_season_tables(
    values: Mapping[tuple[str, str], Mapping[str, float]] | None,
    field: str,
) -> dict[tuple[str, str], dict[str, float]]:
    result: dict[tuple[str, str], dict[str, float]] = {}
    raw_by_folded: dict[tuple[str, str], tuple[str, str]] = {}
    for raw_key, table in (values or {}).items():
        if not isinstance(raw_key, tuple) or len(raw_key) != 2:
            raise ValueError(f"{field} keys must be (competition, season) tuples")
        competition = _normalized_key(raw_key[0], f"{field} competition")
        season = _normalized_key(raw_key[1], f"{field} season")
        folded = (competition.casefold(), season.casefold())
        previous = raw_by_folded.setdefault(folded, raw_key)
        if previous != raw_key:
            raise ValueError(f"{field} season normalization collision")
        result[(competition, season)] = _normalized_ratings(table, field)
    return result


def _actual_score(row: Mapping[str, Any]) -> float:
    home = _finite_number(row.get("home_goals"), "home_goals")
    away = _finite_number(row.get("away_goals"), "away_goals")
    if home < 0 or away < 0 or not home.is_integer() or not away.is_integer():
        raise ValueError("goals must be non-negative whole numbers")
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
    key_registry: dict[tuple[str, str], str] = {}
    for row in matches:
        missing = required - row.keys()
        if missing:
            raise ValueError(f"missing required fields: {', '.join(sorted(missing))}")
        normalized = dict(row)
        for field in ("fixture_id", "competition", "season", "home_team", "away_team"):
            raw = row[field]
            value = _normalized_key(raw, field)
            registry_field = "team" if field in {"home_team", "away_team"} else field
            collision_key = (registry_field, value.casefold())
            previous = key_registry.setdefault(collision_key, raw)
            if previous != raw:
                raise ValueError(f"{field} normalization collision")
            normalized[field] = value
        fixture_id = normalized["fixture_id"]
        if fixture_id in ids:
            raise ValueError(f"duplicate fixture_id: {fixture_id}")
        if normalized["home_team"].casefold() == normalized["away_team"].casefold():
            raise ValueError("home_team and away_team must differ")
        _actual_score(normalized)
        ids.add(fixture_id)
        rows.append((_parse_time(normalized["event_time"]), normalized))
    rows.sort(key=lambda item: (item[0].date(), str(item[1]["fixture_id"])))
    return rows


def _run(
    matches: Iterable[Mapping[str, Any]],
    *,
    initial_by_season: Mapping[tuple[str, str], Mapping[str, float]] | None,
    config: EloConfig,
) -> EloRun:
    _validate_elo_config(config)
    prepared = _prepare(matches)
    initial_tables = _normalized_season_tables(initial_by_season, "initial")
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
                seeded = initial_tables.get(season_key, {})
                for team, rating in seeded.items():
                    ratings[(competition, team)] = rating
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
        update_balance += fsum(delta for _, delta in pending)
        cursor = end
    return EloRun(
        rows=tuple(rows),
        final_ratings=MappingProxyType(dict(ratings)),
        update_balance=update_balance,
    )


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

    _validate_tier_config(config)
    if len(raw_anchors) != config.club_count:
        raise ValueError(f"tier anchor table must contain exactly {config.club_count} clubs")
    anchors = _normalized_ratings(raw_anchors, "tier anchor")
    if len(anchors) != config.club_count:
        raise ValueError("tier anchor table contains normalized duplicate clubs")
    mean = fsum(anchors.values()) / config.club_count
    return {team: float(config.base_rating) + anchor - mean for team, anchor in anchors.items()}


def anchors_from_tiers(
    tiers: Mapping[str, str],
    *,
    anchor_scale: Mapping[str, float] = DEFAULT_TIER_ANCHORS,
    config: TierSeedConfig = DEFAULT_TIER_CONFIG,
) -> dict[str, float]:
    """Resolve generic caller tier labels, then center the complete table."""

    _validate_tier_config(config)
    scale = _normalized_ratings(anchor_scale, "tier scale")
    resolved: dict[str, float] = {}
    raw_by_folded: dict[str, str] = {}
    unknown: set[str] = set()
    for raw_team, raw_tier in tiers.items():
        team = _normalized_key(raw_team, "tier team")
        folded = team.casefold()
        previous = raw_by_folded.setdefault(folded, raw_team)
        if previous != raw_team:
            raise ValueError("tier team normalization collision")
        tier = _normalized_key(raw_tier, "tier label")
        if tier not in scale:
            unknown.add(tier)
        else:
            resolved[team] = scale[tier]
    if unknown:
        raise ValueError(f"unknown tier labels: {', '.join(sorted(unknown))}")
    return center_anchors(resolved, config)


def tier_season_start(
    centered_anchors: Mapping[str, float],
    previous_end: Mapping[str, float] | None = None,
    *,
    config: TierSeedConfig = DEFAULT_TIER_CONFIG,
) -> dict[str, float]:
    """Blend returning clubs with anchors and recenter the provisional table."""

    _validate_tier_config(config)
    centered = center_anchors(centered_anchors, config)
    previous = _normalized_ratings(previous_end or {}, "previous end")
    provisional = {
        team: (
            config.continuing_weight * float(previous[team])
            + (1.0 - config.continuing_weight) * anchor
            if team in previous
            else anchor
        )
        for team, anchor in centered.items()
    }
    mean = fsum(provisional.values()) / config.club_count
    return {team: config.base_rating + value - mean for team, value in provisional.items()}


def run_tier_seeded_elo(
    matches: Iterable[Mapping[str, Any]],
    preseason_anchors: Mapping[tuple[str, str], Mapping[str, float]],
    *,
    config: EloConfig = DEFAULT_ELO_CONFIG,
    tier_config: TierSeedConfig = DEFAULT_TIER_CONFIG,
) -> EloRun:
    """Run Elo from complete, generic caller-supplied season anchor tables."""

    _validate_elo_config(config)
    _validate_tier_config(tier_config)
    prepared = _prepare(matches)
    normalized_preseason = _normalized_season_tables(preseason_anchors, "preseason anchor")
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
        raw = normalized_preseason.get(season_key)
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
