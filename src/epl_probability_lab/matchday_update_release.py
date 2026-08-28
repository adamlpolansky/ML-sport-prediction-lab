"""Validation for the EPL MW2 post-MW1 Elo-Poisson update release."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .challenger_release import CSV_FIELDS, FORECAST_FIELDS, poisson_outputs

DIRECTORY = Path("forecasts/2026-27/matchday-02/challengers/elo-poisson-v1-post-mw1")
JSON_PATH = DIRECTORY / "forecast.json"
CSV_PATH = DIRECTORY / "forecast.csv"
COVERAGE_PATH = DIRECTORY / "coverage.json"
README_PATH = DIRECTORY / "README.md"
PROVENANCE_PATH = DIRECTORY / "provenance.md"
ROOT_README_PATH = Path("README.md")

MODEL_ID = "fixed-elo-neutral-reentry-poisson-v1-post-mw1-refit"
ARTIFACT_STATUS = "exploratory_post_matchweek_update"
FORECAST_ID = "epl-2026-27-mw02-elo-poisson-v1-post-mw1"
COVERAGE_FIELDS = tuple(
    sorted(("fixture_key", "home_team", "away_team", "kickoff_utc", "included", "reason"))
)
FIXTURES = {
    "epl-mw02-01": (
        "2026-08-28T20:00:00+01:00",
        "2026-08-28T19:00:00Z",
        "Crystal Palace",
        "Manchester City",
    ),
    "epl-mw02-02": (
        "2026-08-29T12:30:00+01:00",
        "2026-08-29T11:30:00Z",
        "Liverpool",
        "Nottingham Forest",
    ),
    "epl-mw02-03": (
        "2026-08-29T15:00:00+01:00",
        "2026-08-29T14:00:00Z",
        "AFC Bournemouth",
        "Everton",
    ),
    "epl-mw02-04": (
        "2026-08-29T15:00:00+01:00",
        "2026-08-29T14:00:00Z",
        "Coventry City",
        "Hull City",
    ),
    "epl-mw02-05": (
        "2026-08-29T17:30:00+01:00",
        "2026-08-29T16:30:00Z",
        "Tottenham Hotspur",
        "Newcastle United",
    ),
    "epl-mw02-06": (
        "2026-08-30T14:00:00+01:00",
        "2026-08-30T13:00:00Z",
        "Chelsea",
        "Brighton & Hove Albion",
    ),
    "epl-mw02-07": (
        "2026-08-30T14:00:00+01:00",
        "2026-08-30T13:00:00Z",
        "Leeds United",
        "Brentford",
    ),
    "epl-mw02-08": (
        "2026-08-30T14:00:00+01:00",
        "2026-08-30T13:00:00Z",
        "Sunderland",
        "Fulham",
    ),
    "epl-mw02-09": (
        "2026-08-30T16:30:00+01:00",
        "2026-08-30T15:30:00Z",
        "Manchester United",
        "Ipswich Town",
    ),
    "epl-mw02-10": (
        "2026-08-31T20:00:00+01:00",
        "2026-08-31T19:00:00Z",
        "Aston Villa",
        "Arsenal",
    ),
}
PUBLIC_ARTIFACT_SHA256 = {
    JSON_PATH: "058751f13dcb68865c5b9599563839379c5151ace5ccf4c307a69ca4b687b5cb",
    CSV_PATH: "f15747ecee72099fa9437fc1d78369c2b698a2079bdfe8181bec000af1781735",
    COVERAGE_PATH: "3d268e29596fc7abd0b7e1534bb98a392bed5b066f28ca8251911dd176929dd2",
}
TABLE_START = "<!-- matchday2-table:start -->"
TABLE_END = "<!-- matchday2-table:end -->"


class MatchdayUpdateReleaseError(ValueError):
    """Raised when the public MW2 update pack violates its narrow contract."""


def _finite(value: object, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise MatchdayUpdateReleaseError(f"{field} must be numeric")
    result = float(value)
    if not math.isfinite(result):
        raise MatchdayUpdateReleaseError(f"{field} must be finite")
    return result


def _integer(value: object, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise MatchdayUpdateReleaseError(f"{field} must be a non-negative integer")
    return value


def _utc(value: object, field: str) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise MatchdayUpdateReleaseError(f"{field} must be an explicit UTC timestamp")
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)
    except ValueError as exc:
        raise MatchdayUpdateReleaseError(f"{field} is invalid") from exc


def validate_forecast_rows(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list) or len(value) != 10:
        raise MatchdayUpdateReleaseError("MW2 update forecast must contain exactly ten rows")
    rows: list[dict[str, Any]] = []
    for index, raw in enumerate(value):
        if not isinstance(raw, dict) or tuple(raw) != FORECAST_FIELDS:
            raise MatchdayUpdateReleaseError(f"row {index} does not have the exact schema")
        row = dict(raw)
        key = row["fixture_key"]
        if key not in FIXTURES:
            raise MatchdayUpdateReleaseError(f"row {index} has an unknown fixture")
        identity = (
            row["kickoff_local"],
            row["kickoff_utc"],
            row["home_team"],
            row["away_team"],
        )
        if identity != FIXTURES[key]:
            raise MatchdayUpdateReleaseError(f"row {index} fixture identity changed")
        if (
            row["competition"] != "EPL"
            or row["season"] != "2026-27"
            or row["matchday"] != 2
            or row["timezone"] != "Europe/London"
        ):
            raise MatchdayUpdateReleaseError(f"row {index} competition contract changed")
        if (
            row["forecast_id"] != FORECAST_ID
            or row["model_id"] != MODEL_ID
            or row["artifact_status"] != ARTIFACT_STATUS
        ):
            raise MatchdayUpdateReleaseError(f"row {index} model/release identity changed")
        probabilities = [_finite(row[field], field) for field in ("p_home", "p_draw", "p_away")]
        if any(not 0.0 <= probability <= 1.0 for probability in probabilities) or not math.isclose(
            math.fsum(probabilities), 1.0, abs_tol=1e-12
        ):
            raise MatchdayUpdateReleaseError(f"row {index} probabilities are invalid")
        lambdas = [_finite(row[field], field) for field in ("lambda_home", "lambda_away")]
        if any(not 0.05 <= intensity <= 6.0 for intensity in lambdas):
            raise MatchdayUpdateReleaseError(f"row {index} lambda is outside frozen bounds")
        if not isinstance(row["home_neutral_reentry"], bool) or not isinstance(
            row["away_neutral_reentry"], bool
        ):
            raise MatchdayUpdateReleaseError(f"row {index} reentry flags must be boolean")
        cutoff = _utc(row["information_cutoff_utc"], "information_cutoff_utc")
        generated = _utc(row["generated_at_utc"], "generated_at_utc")
        kickoff = _utc(row["kickoff_utc"], "kickoff_utc")
        if cutoff > generated or generated >= kickoff:
            raise MatchdayUpdateReleaseError(f"row {index} is not prospective")
        recomputed = poisson_outputs(*lambdas)
        for field in ("p_home", "p_draw", "p_away", "tail_mass"):
            if not math.isclose(
                _finite(row[field], field), float(recomputed[field]), rel_tol=0.0, abs_tol=1e-12
            ):
                raise MatchdayUpdateReleaseError(f"row {index} published-lambda mismatch")
        if _integer(row["score_max"], "score_max") != recomputed["score_max"]:
            raise MatchdayUpdateReleaseError(f"row {index} score grid mismatch")
        top = row["top_scorelines"]
        if not isinstance(top, list) or len(top) != 3:
            raise MatchdayUpdateReleaseError(f"row {index} needs three scorelines")
        for actual, expected in zip(top, recomputed["top_scorelines"], strict=True):
            if not isinstance(actual, dict) or tuple(actual) != (
                "away_goals",
                "home_goals",
                "probability",
            ):
                raise MatchdayUpdateReleaseError(f"row {index} scoreline schema changed")
            if (
                _integer(actual["home_goals"], "home_goals") != expected["home_goals"]
                or _integer(actual["away_goals"], "away_goals") != expected["away_goals"]
                or not math.isclose(
                    _finite(actual["probability"], "scoreline probability"),
                    expected["probability"],
                    rel_tol=0.0,
                    abs_tol=1e-12,
                )
            ):
                raise MatchdayUpdateReleaseError(f"row {index} scoreline mismatch")
        rows.append(row)
    if {row["fixture_key"] for row in rows} != set(FIXTURES):
        raise MatchdayUpdateReleaseError("MW2 update has duplicate or missing fixtures")
    for field in ("forecast_id", "information_cutoff_utc", "generated_at_utc"):
        if len({row[field] for row in rows}) != 1:
            raise MatchdayUpdateReleaseError(f"rows do not share one {field}")
    return rows


def load_json_rows(content: bytes) -> list[dict[str, Any]]:
    try:
        value = json.loads(content.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise MatchdayUpdateReleaseError("MW2 update JSON is invalid") from exc
    return validate_forecast_rows(value)


def load_csv_rows(content: bytes) -> list[dict[str, Any]]:
    try:
        reader = csv.DictReader(io.StringIO(content.decode("utf-8")))
        if tuple(reader.fieldnames or ()) != CSV_FIELDS:
            raise MatchdayUpdateReleaseError("MW2 update CSV schema changed")
        rows: list[dict[str, Any]] = []
        for raw in reader:
            row: dict[str, Any] = {
                key: raw[key]
                for key in FORECAST_FIELDS
                if key
                not in {
                    "top_scorelines",
                    "matchday",
                    "score_max",
                    "home_neutral_reentry",
                    "away_neutral_reentry",
                }
            }
            row["matchday"] = int(raw["matchday"])
            row["score_max"] = int(raw["score_max"])
            for field in ("p_home", "p_draw", "p_away", "lambda_home", "lambda_away", "tail_mass"):
                row[field] = float(raw[field])
            for field in ("home_neutral_reentry", "away_neutral_reentry"):
                if raw[field] not in {"true", "false"}:
                    raise MatchdayUpdateReleaseError(f"CSV {field} must be true or false")
                row[field] = raw[field] == "true"
            row["top_scorelines"] = [
                {
                    "away_goals": int(raw[f"top_{position}_away_goals"]),
                    "home_goals": int(raw[f"top_{position}_home_goals"]),
                    "probability": float(raw[f"top_{position}_probability"]),
                }
                for position in range(1, 4)
            ]
            rows.append({key: row[key] for key in FORECAST_FIELDS})
    except (UnicodeDecodeError, csv.Error, KeyError, TypeError, ValueError) as exc:
        raise MatchdayUpdateReleaseError("MW2 update CSV is invalid") from exc
    return validate_forecast_rows(rows)


def validate_coverage(value: object, forecasts: Sequence[Mapping[str, Any]]) -> None:
    if not isinstance(value, list) or len(value) != 10:
        raise MatchdayUpdateReleaseError("coverage must contain exactly ten rows")
    rows = []
    for raw in value:
        if not isinstance(raw, dict) or tuple(raw) != COVERAGE_FIELDS:
            raise MatchdayUpdateReleaseError("coverage row schema changed")
        row = dict(raw)
        key = row["fixture_key"]
        if (
            key not in FIXTURES
            or (
                row["kickoff_utc"],
                row["home_team"],
                row["away_team"],
            )
            != FIXTURES[key][1:]
        ):
            raise MatchdayUpdateReleaseError("coverage fixture identity changed")
        if row["included"] is not True or row["reason"] is not None:
            raise MatchdayUpdateReleaseError("coverage must mark every fixture included")
        rows.append(row)
    if {row["fixture_key"] for row in rows} != {row["fixture_key"] for row in forecasts}:
        raise MatchdayUpdateReleaseError("coverage and forecast differ")


def market_probabilities(lambda_home: float, lambda_away: float) -> tuple[float, float]:
    """Return exact independent-Poisson Over 2.5 and BTTS probabilities."""

    total = lambda_home + lambda_away
    p_under_2_5 = math.exp(-total) * (1.0 + total + total**2 / 2.0)
    p_over_2_5 = 1.0 - p_under_2_5
    p_btts = 1.0 - math.exp(-lambda_home) - math.exp(-lambda_away) + math.exp(-total)
    return p_over_2_5, p_btts


def render_table(rows: Sequence[Mapping[str, Any]]) -> str:
    """Render the reader-facing MW2 forecast table from full-precision rows."""

    lines = [
        "| Kickoff (London) | Fixture | H | D | A | Pick | λ H–A | O2.5 | BTTS | Modal |",
        "| --- | --- | ---: | ---: | ---: | --- | ---: | ---: | ---: | ---: |",
    ]
    labels = {"p_home": "Home", "p_draw": "Draw", "p_away": "Away"}
    for row in rows:
        pick = max(labels, key=lambda field: float(row[field]))
        over, btts = market_probabilities(float(row["lambda_home"]), float(row["lambda_away"]))
        modal = row["top_scorelines"][0]
        lines.append(
            f"| {str(row['kickoff_local'])[:16].replace('T', ' ')} | "
            f"{row['home_team']} — {row['away_team']} | {float(row['p_home']):.1%} | "
            f"{float(row['p_draw']):.1%} | {float(row['p_away']):.1%} | {labels[pick]} | "
            f"{float(row['lambda_home']):.2f}–{float(row['lambda_away']):.2f} | "
            f"{over:.1%} | {btts:.1%} | "
            f"{modal['home_goals']}–{modal['away_goals']} ({float(modal['probability']):.1%}) |"
        )
    return "\n".join(lines)


def _table_block(document: str) -> str:
    if document.count(TABLE_START) != 1 or document.count(TABLE_END) != 1:
        raise MatchdayUpdateReleaseError("MW2 table markers are missing or duplicated")
    block = document.split(TABLE_START, 1)[1].split(TABLE_END, 1)[0]
    return "\n".join(block.splitlines()).strip()


def validate_release_contents(contents: Mapping[str | Path, bytes]) -> list[dict[str, Any]]:
    normalized = {Path(path).as_posix(): value for path, value in contents.items()}
    required = {
        path.as_posix()
        for path in (*PUBLIC_ARTIFACT_SHA256, README_PATH, PROVENANCE_PATH, ROOT_README_PATH)
    }
    if not required.issubset(normalized):
        raise MatchdayUpdateReleaseError("MW2 update pack is incomplete")
    for path, expected in PUBLIC_ARTIFACT_SHA256.items():
        if hashlib.sha256(normalized[path.as_posix()]).hexdigest() != expected:
            raise MatchdayUpdateReleaseError(f"immutable artifact changed: {path.as_posix()}")
    json_rows = load_json_rows(normalized[JSON_PATH.as_posix()])
    csv_rows = load_csv_rows(normalized[CSV_PATH.as_posix()])
    if json_rows != csv_rows:
        raise MatchdayUpdateReleaseError("JSON and CSV forecasts differ")
    try:
        coverage = json.loads(normalized[COVERAGE_PATH.as_posix()].decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise MatchdayUpdateReleaseError("coverage JSON is invalid") from exc
    validate_coverage(coverage, json_rows)
    readme = normalized[README_PATH.as_posix()].decode("utf-8")
    root_readme = normalized[ROOT_README_PATH.as_posix()].decode("utf-8")
    provenance = normalized[PROVENANCE_PATH.as_posix()].decode("utf-8")
    if ARTIFACT_STATUS not in readme or "not a promoted champion" not in readme.lower():
        raise MatchdayUpdateReleaseError("claim boundary missing from release README")
    if ARTIFACT_STATUS not in provenance or "promotion performed: false" not in provenance.lower():
        raise MatchdayUpdateReleaseError("claim boundary missing from provenance")
    expected_table = render_table(json_rows)
    for path, document in ((README_PATH, readme), (ROOT_README_PATH, root_readme)):
        if _table_block(document) != expected_table:
            raise MatchdayUpdateReleaseError(f"{path.as_posix()} table does not match machine rows")
    return json_rows


def validate_release_tree(root: Path) -> list[dict[str, Any]]:
    paths = (*PUBLIC_ARTIFACT_SHA256, README_PATH, PROVENANCE_PATH, ROOT_README_PATH)
    return validate_release_contents({path: (root / path).read_bytes() for path in paths})


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    rows = validate_release_tree(args.root.resolve())
    print(f"MW2 update release validation: PASS ({len(rows)} prospective rows)")


if __name__ == "__main__":
    main()
