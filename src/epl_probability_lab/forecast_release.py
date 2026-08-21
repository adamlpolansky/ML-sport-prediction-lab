"""Validation for the narrow EPL 2026/27 Matchweek 1 forecast release."""

from __future__ import annotations

import csv
import io
import json
import math
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

FORECAST_DIRECTORY = Path("forecasts/2026-27/matchday-01")
JSON_PATH = FORECAST_DIRECTORY / "forecast.json"
CSV_PATH = FORECAST_DIRECTORY / "forecast.csv"
README_PATH = FORECAST_DIRECTORY / "README.md"
ROOT_README_PATH = Path("README.md")

FIELDS = (
    "forecast_id",
    "fixture_key",
    "competition",
    "season",
    "matchday",
    "kickoff_local",
    "timezone",
    "kickoff_utc",
    "home_team",
    "away_team",
    "p_home_win",
    "p_draw",
    "p_away_win",
    "expected_home_goals",
    "expected_away_goals",
    "modal_home_goals",
    "modal_away_goals",
    "modal_score_probability",
    "tail_mass",
    "generated_at_utc",
    "information_cutoff_utc",
    "training_data_cutoff",
    "model_id",
    "protocol_version",
    "artifact_status",
)

FIXTURES = {
    "epl-mw01-01": (
        "2026-08-21T20:00:00+01:00",
        "2026-08-21T19:00:00Z",
        "Arsenal",
        "Coventry City",
    ),
    "epl-mw01-02": (
        "2026-08-22T12:30:00+01:00",
        "2026-08-22T11:30:00Z",
        "Hull City",
        "Manchester United",
    ),
    "epl-mw01-03": (
        "2026-08-22T15:00:00+01:00",
        "2026-08-22T14:00:00Z",
        "Everton",
        "Crystal Palace",
    ),
    "epl-mw01-04": (
        "2026-08-22T15:00:00+01:00",
        "2026-08-22T14:00:00Z",
        "Ipswich Town",
        "Sunderland",
    ),
    "epl-mw01-05": (
        "2026-08-22T15:00:00+01:00",
        "2026-08-22T14:00:00Z",
        "Nottingham Forest",
        "Leeds United",
    ),
    "epl-mw01-06": (
        "2026-08-22T17:30:00+01:00",
        "2026-08-22T16:30:00Z",
        "Brentford",
        "Tottenham Hotspur",
    ),
    "epl-mw01-07": (
        "2026-08-23T14:00:00+01:00",
        "2026-08-23T13:00:00Z",
        "Brighton & Hove Albion",
        "Aston Villa",
    ),
    "epl-mw01-08": (
        "2026-08-23T14:00:00+01:00",
        "2026-08-23T13:00:00Z",
        "Manchester City",
        "AFC Bournemouth",
    ),
    "epl-mw01-09": (
        "2026-08-23T16:30:00+01:00",
        "2026-08-23T15:30:00Z",
        "Newcastle United",
        "Liverpool",
    ),
    "epl-mw01-10": (
        "2026-08-24T20:00:00+01:00",
        "2026-08-24T19:00:00Z",
        "Fulham",
        "Chelsea",
    ),
}

_FLOAT_FIELDS = {
    "p_home_win",
    "p_draw",
    "p_away_win",
    "expected_home_goals",
    "expected_away_goals",
    "modal_score_probability",
    "tail_mass",
}
_INTEGER_FIELDS = {"matchday", "modal_home_goals", "modal_away_goals"}
_TABLE_START = "<!-- forecast-table:start -->"
_TABLE_END = "<!-- forecast-table:end -->"


class ForecastReleaseError(ValueError):
    """Raised when the public forecast pack violates its frozen contract."""


def _finite_number(value: object, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ForecastReleaseError(f"{field} must be numeric")
    result = float(value)
    if not math.isfinite(result):
        raise ForecastReleaseError(f"{field} must be finite")
    return result


def _parse_utc(value: object, field: str) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise ForecastReleaseError(f"{field} must be an explicit UTC timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ForecastReleaseError(f"{field} is invalid") from exc
    return parsed.astimezone(UTC)


def validate_rows(rows: object) -> list[dict[str, Any]]:
    """Validate and return the exact ten canonical machine rows."""

    if not isinstance(rows, list) or len(rows) != 10:
        raise ForecastReleaseError("forecast must contain exactly ten rows")
    normalized: list[dict[str, Any]] = []
    for index, raw in enumerate(rows):
        if not isinstance(raw, dict) or tuple(raw) != FIELDS:
            raise ForecastReleaseError(f"row {index} does not have the exact canonical schema")
        row = dict(raw)
        fixture_key = row["fixture_key"]
        if fixture_key not in FIXTURES:
            raise ForecastReleaseError(f"row {index} has an unknown fixture_key")
        expected = FIXTURES[fixture_key]
        actual = (
            row["kickoff_local"],
            row["kickoff_utc"],
            row["home_team"],
            row["away_team"],
        )
        if actual != expected:
            raise ForecastReleaseError(f"row {index} fixture identity or kickoff is invalid")
        if row["timezone"] != "Europe/London":
            raise ForecastReleaseError(f"row {index} timezone is invalid")
        if row["competition"] != "EPL" or row["season"] != "2026-27":
            raise ForecastReleaseError(f"row {index} competition or season is invalid")
        if row["matchday"] != 1:
            raise ForecastReleaseError(f"row {index} matchday is invalid")
        probabilities = [
            _finite_number(row[field], field)
            for field in (
                "p_home_win",
                "p_draw",
                "p_away_win",
            )
        ]
        if any(value < 0.0 or value > 1.0 for value in probabilities):
            raise ForecastReleaseError(f"row {index} probability is outside [0, 1]")
        if abs(math.fsum(probabilities) - 1.0) > 1e-12:
            raise ForecastReleaseError(f"row {index} H/D/A probabilities do not sum to one")
        for field in ("expected_home_goals", "expected_away_goals"):
            if _finite_number(row[field], field) < 0.0:
                raise ForecastReleaseError(f"row {index} expected goals must be non-negative")
        for field in ("modal_home_goals", "modal_away_goals"):
            value = row[field]
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ForecastReleaseError(f"row {index} modal goals must be non-negative integers")
        modal_probability = _finite_number(row["modal_score_probability"], "modal score")
        tail_mass = _finite_number(row["tail_mass"], "tail mass")
        if not 0.0 <= modal_probability <= 1.0 or not 0.0 <= tail_mass < 0.001:
            raise ForecastReleaseError(f"row {index} score probability or tail mass is invalid")
        generated = _parse_utc(row["generated_at_utc"], "generated_at_utc")
        cutoff = _parse_utc(row["information_cutoff_utc"], "information_cutoff_utc")
        kickoff = _parse_utc(row["kickoff_utc"], "kickoff_utc")
        if cutoff > generated or generated >= kickoff:
            raise ForecastReleaseError(f"row {index} is not a prospective pre-match forecast")
        if row["training_data_cutoff"] != "2026-05-24":
            raise ForecastReleaseError(f"row {index} training cutoff is invalid")
        if row["model_id"] != "dynamic-dixon-coles-incumbent-2026-27-v1":
            raise ForecastReleaseError(f"row {index} model_id is invalid")
        if row["protocol_version"] != "epl-mw1-forecast/v1":
            raise ForecastReleaseError(f"row {index} protocol_version is invalid")
        if row["artifact_status"] != "prospective_pre_match":
            raise ForecastReleaseError(f"row {index} artifact_status is invalid")
        normalized.append(row)
    if set(row["fixture_key"] for row in normalized) != set(FIXTURES):
        raise ForecastReleaseError("forecast has duplicate or missing fixture identities")
    singleton_fields = ("forecast_id", "generated_at_utc", "information_cutoff_utc")
    for field in singleton_fields:
        if len({row[field] for row in normalized}) != 1:
            raise ForecastReleaseError(f"forecast rows do not share one {field}")
    return normalized


def load_json_rows(content: bytes) -> list[dict[str, Any]]:
    try:
        payload = json.loads(content.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ForecastReleaseError("forecast JSON is not valid UTF-8 JSON") from exc
    return validate_rows(payload)


def load_csv_rows(content: bytes) -> list[dict[str, Any]]:
    try:
        reader = csv.DictReader(io.StringIO(content.decode("utf-8")))
        if tuple(reader.fieldnames or ()) != FIELDS:
            raise ForecastReleaseError("forecast CSV does not have the exact canonical schema")
        rows: list[dict[str, Any]] = []
        for raw in reader:
            if None in raw:
                raise ForecastReleaseError("forecast CSV contains extra columns")
            row: dict[str, Any] = dict(raw)
            for field in _FLOAT_FIELDS:
                row[field] = float(row[field])
            for field in _INTEGER_FIELDS:
                row[field] = int(row[field])
            rows.append(row)
    except (UnicodeDecodeError, csv.Error, TypeError, ValueError) as exc:
        raise ForecastReleaseError("forecast CSV is invalid") from exc
    return validate_rows(rows)


def render_markdown_table(rows: Sequence[Mapping[str, Any]]) -> str:
    lines = [
        "| Kickoff (Europe/London) | Fixture | Home | Draw | Away | Highest H/D/A | "
        "xG (H–A) | Modal score |",
        "| --- | --- | ---: | ---: | ---: | --- | ---: | ---: |",
    ]
    labels = ("Home", "Draw", "Away")
    for row in rows:
        probabilities = (
            float(row["p_home_win"]),
            float(row["p_draw"]),
            float(row["p_away_win"]),
        )
        highest = labels[max(range(3), key=probabilities.__getitem__)]
        lines.append(
            f"| {str(row['kickoff_local'])[:16].replace('T', ' ')} | "
            f"{row['home_team']} — {row['away_team']} | {probabilities[0]:.1%} | "
            f"{probabilities[1]:.1%} | {probabilities[2]:.1%} | {highest} | "
            f"{float(row['expected_home_goals']):.2f}–"
            f"{float(row['expected_away_goals']):.2f} | {row['modal_home_goals']}–"
            f"{row['modal_away_goals']} ({float(row['modal_score_probability']):.1%}) |"
        )
    return "\n".join(lines)


def _table_block(document: str) -> str:
    if document.count(_TABLE_START) != 1 or document.count(_TABLE_END) != 1:
        raise ForecastReleaseError("forecast README table markers are missing or duplicated")
    block = document.split(_TABLE_START, 1)[1].split(_TABLE_END, 1)[0]
    return "\n".join(block.splitlines()).strip()


def validate_release_tree(root: Path) -> list[dict[str, Any]]:
    items = {
        path.as_posix(): (root / path).read_bytes()
        for path in (JSON_PATH, CSV_PATH, README_PATH, ROOT_README_PATH)
    }
    return validate_release_contents(items)


def validate_release_contents(items: Mapping[str, bytes]) -> list[dict[str, Any]]:
    required = (JSON_PATH, CSV_PATH, README_PATH, ROOT_README_PATH)
    missing = [path.as_posix() for path in required if path.as_posix() not in items]
    if missing:
        raise ForecastReleaseError(f"forecast release files are missing: {', '.join(missing)}")
    json_rows = load_json_rows(items[JSON_PATH.as_posix()])
    csv_rows = load_csv_rows(items[CSV_PATH.as_posix()])
    if json_rows != csv_rows:
        raise ForecastReleaseError("forecast JSON and CSV rows differ")
    expected_table = render_markdown_table(json_rows)
    for relative in (README_PATH, ROOT_README_PATH):
        try:
            document = items[relative.as_posix()].decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ForecastReleaseError(f"{relative.as_posix()} is not UTF-8") from exc
        if _table_block(document) != expected_table:
            raise ForecastReleaseError(f"{relative.as_posix()} table does not match machine rows")
    return json_rows
