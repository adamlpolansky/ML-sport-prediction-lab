"""Generic manager context from caller-supplied, timestamped spell rows."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from types import MappingProxyType
from typing import Any
from unicodedata import normalize


def _parse_time(value: object, field: str) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str):
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    else:
        raise ValueError(f"{field} must be an ISO-8601 string or datetime")
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{field} must include a timezone")
    return parsed.astimezone(UTC)


@dataclass(frozen=True)
class ManagerSpell:
    team: str
    person_key: str
    event_known_at: datetime | str
    effective_start: datetime | str
    effective_end: datetime | str | None = None
    caretaker: bool = False


@dataclass(frozen=True)
class ManagerContextRow:
    fixture_id: str
    event_time: datetime
    home_team: str
    away_team: str
    features: Mapping[str, float]


def _normalized_key(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field} must be a string")
    key = normalize("NFKC", value).strip()
    if not key:
        raise ValueError(f"{field} must be nonempty after normalization")
    return key


def _register_key(
    value: object,
    field: str,
    registry: dict[tuple[str, str], str],
) -> str:
    key = _normalized_key(value, field)
    collision_key = (field, key.casefold())
    previous = registry.setdefault(collision_key, value)  # type: ignore[arg-type]
    if previous != value:
        raise ValueError(f"{field} normalization collision")
    return key


def _eligible_spell(
    spells: list[ManagerSpell], event_time: datetime, team: str
) -> tuple[ManagerSpell | None, datetime | None]:
    eligible: list[tuple[ManagerSpell, datetime]] = []
    for spell in spells:
        known = _parse_time(spell.event_known_at, "event_known_at")
        start = _parse_time(spell.effective_start, "effective_start")
        end = (
            _parse_time(spell.effective_end, "effective_end")
            if spell.effective_end is not None
            else None
        )
        if end is not None and end <= start:
            raise ValueError(f"manager spell end must follow start for {team}")
        if start.date() == event_time.date() or (
            known.date() == event_time.date() and start < event_time
        ):
            raise ValueError(f"ambiguous same-day manager record for {team}")
        if known < event_time and start < event_time and (end is None or event_time < end):
            eligible.append((spell, start))
    if len(eligible) > 1:
        raise ValueError(f"overlapping manager spells for {team}")
    return eligible[0] if eligible else (None, None)


def _side_features(
    team: str,
    event_time: datetime,
    spells: Mapping[str, list[ManagerSpell]],
    prior_times: Mapping[str, list[datetime]],
    prefix: str,
) -> dict[str, float]:
    spell, start = _eligible_spell(spells.get(team, []), event_time, team)
    if spell is None or start is None:
        return {
            f"{prefix}_manager_tenure_days": 0.0,
            f"{prefix}_manager_matches_in_charge": 0.0,
            f"{prefix}_new_manager_last_1": 0.0,
            f"{prefix}_new_manager_last_3": 0.0,
            f"{prefix}_new_manager_last_5": 0.0,
            f"{prefix}_manager_caretaker": 0.0,
            f"{prefix}_manager_available": 0.0,
        }
    matches = sum(start < prior < event_time for prior in prior_times.get(team, []))
    return {
        f"{prefix}_manager_tenure_days": (event_time - start).total_seconds() / 86400.0,
        f"{prefix}_manager_matches_in_charge": float(matches),
        f"{prefix}_new_manager_last_1": float(matches < 1),
        f"{prefix}_new_manager_last_3": float(matches < 3),
        f"{prefix}_new_manager_last_5": float(matches < 5),
        f"{prefix}_manager_caretaker": float(spell.caretaker),
        f"{prefix}_manager_available": 1.0,
    }


def build_manager_context(
    matches: Iterable[Mapping[str, Any]], spells: Iterable[ManagerSpell]
) -> list[ManagerContextRow]:
    """Create prior-only manager features; person identities remain metadata only."""

    spell_map: defaultdict[str, list[ManagerSpell]] = defaultdict(list)
    key_registry: dict[tuple[str, str], str] = {}
    for spell in spells:
        team = _register_key(spell.team, "team", key_registry)
        person_key = _register_key(spell.person_key, "person_key", key_registry)
        if not isinstance(spell.caretaker, bool):
            raise ValueError("caretaker must be boolean")
        known = _parse_time(spell.event_known_at, "event_known_at")
        start = _parse_time(spell.effective_start, "effective_start")
        end = (
            _parse_time(spell.effective_end, "effective_end")
            if spell.effective_end is not None
            else None
        )
        if end is not None and end <= start:
            raise ValueError(f"manager spell end must follow start for {team}")
        spell_map[team].append(
            ManagerSpell(
                team=team,
                person_key=person_key,
                event_known_at=known,
                effective_start=start,
                effective_end=end,
                caretaker=spell.caretaker,
            )
        )
    for team, team_spells in spell_map.items():
        team_spells.sort(key=lambda item: _parse_time(item.effective_start, "effective_start"))
        for previous, current in zip(team_spells, team_spells[1:], strict=False):
            previous_end = (
                _parse_time(previous.effective_end, "effective_end")
                if previous.effective_end is not None
                else None
            )
            current_start = _parse_time(current.effective_start, "effective_start")
            if previous_end is None or previous_end > current_start:
                raise ValueError(f"overlapping manager spells for {team}")
    rows: list[tuple[datetime, Mapping[str, Any]]] = []
    ids: set[str] = set()
    for row in matches:
        required = {"fixture_id", "event_time", "home_team", "away_team"}
        missing = required - row.keys()
        if missing:
            raise ValueError(f"missing required fields: {', '.join(sorted(missing))}")
        normalized = dict(row)
        for field in ("fixture_id", "home_team", "away_team"):
            registry_field = "team" if field in {"home_team", "away_team"} else field
            normalized[field] = _register_key(row[field], registry_field, key_registry)
        fixture_id = normalized["fixture_id"]
        if fixture_id in ids:
            raise ValueError(f"duplicate fixture_id: {fixture_id}")
        if normalized["home_team"].casefold() == normalized["away_team"].casefold():
            raise ValueError("home_team and away_team must differ")
        ids.add(fixture_id)
        rows.append((_parse_time(normalized["event_time"], "event_time"), normalized))
    rows.sort(key=lambda item: (item[0].date(), str(item[1]["fixture_id"])))

    prior_times: defaultdict[str, list[datetime]] = defaultdict(list)
    output: list[ManagerContextRow] = []
    cursor = 0
    while cursor < len(rows):
        date = rows[cursor][0].date()
        end = cursor
        while end < len(rows) and rows[end][0].date() == date:
            end += 1
        batch = rows[cursor:end]
        seen: set[str] = set()
        for event_time, row in batch:
            home = str(row["home_team"])
            away = str(row["away_team"])
            if home in seen or away in seen:
                raise ValueError(f"ambiguous same-date schedule on {date}")
            seen.update((home, away))
            features = _side_features(home, event_time, spell_map, prior_times, "home")
            features.update(_side_features(away, event_time, spell_map, prior_times, "away"))
            output.append(
                ManagerContextRow(
                    fixture_id=str(row["fixture_id"]),
                    event_time=event_time,
                    home_team=home,
                    away_team=away,
                    features=MappingProxyType(features),
                )
            )
        for event_time, row in batch:
            prior_times[str(row["home_team"])].append(event_time)
            prior_times[str(row["away_team"])].append(event_time)
        cursor = end
    return output
