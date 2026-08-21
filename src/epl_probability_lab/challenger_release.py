"""Validation for the exploratory EPL MW1 Elo-Poisson challenger release."""

from __future__ import annotations

import argparse
import csv
import io
import json
import math
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .forecast_release import FIXTURES

DIRECTORY = Path("forecasts/2026-27/matchday-01/challengers/elo-poisson-v1")
JSON_PATH = DIRECTORY / "forecast.json"
CSV_PATH = DIRECTORY / "forecast.csv"
COVERAGE_PATH = DIRECTORY / "coverage.json"
EVALUATION_PATH = DIRECTORY / "evaluation_summary.json"
README_PATH = DIRECTORY / "README.md"
PROVENANCE_PATH = DIRECTORY / "provenance.md"
ROOT_README_PATH = Path("README.md")

MODEL_ID = "fixed-elo-neutral-reentry-poisson-v1"
ARTIFACT_STATUS = "prospective_pre_match_challenger"
FORECAST_FIELDS = tuple(
    sorted(
        (
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
            "model_id",
            "artifact_status",
            "information_cutoff_utc",
            "generated_at_utc",
            "p_home",
            "p_draw",
            "p_away",
            "lambda_home",
            "lambda_away",
            "top_scorelines",
            "tail_mass",
            "score_max",
            "home_neutral_reentry",
            "away_neutral_reentry",
        )
    )
)
CSV_FIELDS = (
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
    "model_id",
    "artifact_status",
    "information_cutoff_utc",
    "generated_at_utc",
    "p_home",
    "p_draw",
    "p_away",
    "lambda_home",
    "lambda_away",
    "top_1_home_goals",
    "top_1_away_goals",
    "top_1_probability",
    "top_2_home_goals",
    "top_2_away_goals",
    "top_2_probability",
    "top_3_home_goals",
    "top_3_away_goals",
    "top_3_probability",
    "tail_mass",
    "score_max",
    "home_neutral_reentry",
    "away_neutral_reentry",
)
COVERAGE_FIELDS = tuple(
    sorted(("fixture_key", "home_team", "away_team", "kickoff_utc", "included", "reason"))
)
TABLE_START = "<!-- challenger-table:start -->"
TABLE_END = "<!-- challenger-table:end -->"
PRIVATE_ARTIFACT_SHA256 = "2988fad1be3bd6d5b97aa03155f9e91dd62fa9b717cbbc91ae2bd85a0b6ceaca"
EFFECTIVE_PROTOCOL_SHA256 = "2d8fa02cf6b5e456a983c085761419536d8f832e1864bdf0cd52c346957cac12"
PRIVATE_CODE_COMMIT = "43c4be27754787418aaa4539be0e37647eb1e8ae"
SOURCE_SHA256 = "fa11cf7d253feb60ba163945c75088bcd6da35a34f82e12dcaab4618651c12f6"
INCUMBENT_OOS_SHA256 = "a103633895b0b1716e80a41551366e375f8e2142b40489d1e03c7f1c8c8f0ad0"
PROTOCOL_HASHES = {
    "base_protocol_sha256": "b7e5365f8b0af44b62c0d236ee222375638a5587abb284dd9d47a3814332e9ad",
    "amendment_sha256": "aa0f1883a1eddb05d296ab96b5e318884708e10dda69f9327f836c14a549da74",
    "effective_protocol_sha256": EFFECTIVE_PROTOCOL_SHA256,
}


class ChallengerReleaseError(ValueError):
    """Raised when the public challenger pack violates its narrow contract."""


def _finite(value: object, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ChallengerReleaseError(f"{field} must be numeric")
    result = float(value)
    if not math.isfinite(result):
        raise ChallengerReleaseError(f"{field} must be finite")
    return result


def _integer(value: object, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ChallengerReleaseError(f"{field} must be a non-negative integer")
    return value


def _utc(value: object, field: str) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise ChallengerReleaseError(f"{field} must be an explicit UTC timestamp")
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)
    except ValueError as exc:
        raise ChallengerReleaseError(f"{field} is invalid") from exc


def poisson_outputs(lambda_home: float, lambda_away: float) -> dict[str, Any]:
    if not all(math.isfinite(value) and value > 0.0 for value in (lambda_home, lambda_away)):
        raise ChallengerReleaseError("published lambdas must be finite and positive")
    maximum = 0
    home_pmf = [math.exp(-lambda_home)]
    away_pmf = [math.exp(-lambda_away)]
    tail = 1.0 - math.fsum(home_pmf) * math.fsum(away_pmf)
    while tail >= 0.001 and maximum < 30:
        maximum += 1
        home_pmf.append(home_pmf[-1] * lambda_home / maximum)
        away_pmf.append(away_pmf[-1] * lambda_away / maximum)
        tail = max(0.0, 1.0 - math.fsum(home_pmf) * math.fsum(away_pmf))
    if tail >= 0.001:
        raise ChallengerReleaseError("published lambdas cannot satisfy the score-grid tail gate")
    cells = [
        (home_pmf[home] * away_pmf[away], home, away)
        for home in range(maximum + 1)
        for away in range(maximum + 1)
    ]
    captured = math.fsum(probability for probability, _home, _away in cells)
    normalized = [(probability / captured, home, away) for probability, home, away in cells]
    p_home = math.fsum(p for p, home, away in normalized if home > away)
    p_draw = math.fsum(p for p, home, away in normalized if home == away)
    p_away = math.fsum(p for p, home, away in normalized if home < away)
    normalized.sort(key=lambda value: (-value[0], value[1], value[2]))
    top = [
        {"away_goals": away, "home_goals": home, "probability": probability}
        for probability, home, away in normalized[:3]
    ]
    return {
        "p_home": p_home,
        "p_draw": p_draw,
        "p_away": p_away,
        "top_scorelines": top,
        "tail_mass": tail,
        "score_max": maximum,
    }


def validate_forecast_rows(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list) or not 0 < len(value) <= 10:
        raise ChallengerReleaseError("challenger forecast must contain one to ten rows")
    rows: list[dict[str, Any]] = []
    for index, raw in enumerate(value):
        if not isinstance(raw, dict) or tuple(raw) != FORECAST_FIELDS:
            raise ChallengerReleaseError(f"row {index} does not have the exact challenger schema")
        row = dict(raw)
        key = row["fixture_key"]
        if key not in FIXTURES:
            raise ChallengerReleaseError(f"row {index} has an unknown fixture")
        if (
            row["kickoff_local"],
            row["kickoff_utc"],
            row["home_team"],
            row["away_team"],
        ) != FIXTURES[key]:
            raise ChallengerReleaseError(f"row {index} fixture identity or kickoff changed")
        if row["competition"] != "EPL" or row["season"] != "2026-27" or row["matchday"] != 1:
            raise ChallengerReleaseError(f"row {index} competition contract changed")
        if row["timezone"] != "Europe/London" or row["model_id"] != MODEL_ID:
            raise ChallengerReleaseError(f"row {index} timezone or model contract changed")
        if row["artifact_status"] != ARTIFACT_STATUS:
            raise ChallengerReleaseError(f"row {index} artifact status changed")
        if not isinstance(row["forecast_id"], str) or not row["forecast_id"]:
            raise ChallengerReleaseError(f"row {index} forecast_id is invalid")
        probabilities = [_finite(row[field], field) for field in ("p_home", "p_draw", "p_away")]
        if any(not 0.0 <= probability <= 1.0 for probability in probabilities):
            raise ChallengerReleaseError(f"row {index} probability is outside [0, 1]")
        if not math.isclose(math.fsum(probabilities), 1.0, abs_tol=1e-12):
            raise ChallengerReleaseError(f"row {index} probabilities do not sum to one")
        lambdas = [_finite(row[field], field) for field in ("lambda_home", "lambda_away")]
        if any(not 0.05 <= intensity <= 6.0 for intensity in lambdas):
            raise ChallengerReleaseError(f"row {index} lambda is outside frozen bounds")
        if not isinstance(row["home_neutral_reentry"], bool) or not isinstance(
            row["away_neutral_reentry"], bool
        ):
            raise ChallengerReleaseError(f"row {index} neutral-reentry flags must be boolean")
        cutoff = _utc(row["information_cutoff_utc"], "information_cutoff_utc")
        generated = _utc(row["generated_at_utc"], "generated_at_utc")
        kickoff = _utc(row["kickoff_utc"], "kickoff_utc")
        if cutoff > generated or generated >= kickoff:
            raise ChallengerReleaseError(f"row {index} is not prospective")
        recomputed = poisson_outputs(*lambdas)
        for field in ("p_home", "p_draw", "p_away", "tail_mass"):
            if not math.isclose(
                _finite(row[field], field), float(recomputed[field]), rel_tol=0.0, abs_tol=1e-12
            ):
                raise ChallengerReleaseError(f"row {index} published-lambda {field} mismatch")
        if _integer(row["score_max"], "score_max") != recomputed["score_max"]:
            raise ChallengerReleaseError(f"row {index} score grid mismatch")
        top = row["top_scorelines"]
        if not isinstance(top, list) or len(top) != 3:
            raise ChallengerReleaseError(f"row {index} must contain exactly three scorelines")
        for position, (actual, expected) in enumerate(
            zip(top, recomputed["top_scorelines"], strict=True)
        ):
            if not isinstance(actual, dict) or tuple(actual) != (
                "away_goals",
                "home_goals",
                "probability",
            ):
                raise ChallengerReleaseError(f"row {index} top scoreline {position} schema changed")
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
                raise ChallengerReleaseError(f"row {index} top scoreline {position} mismatch")
        rows.append(row)
    if len({row["fixture_key"] for row in rows}) != len(rows):
        raise ChallengerReleaseError("challenger forecast contains duplicate fixtures")
    for field in ("forecast_id", "information_cutoff_utc", "generated_at_utc"):
        if len({row[field] for row in rows}) != 1:
            raise ChallengerReleaseError(f"challenger rows do not share one {field}")
    return rows


def load_json_rows(content: bytes) -> list[dict[str, Any]]:
    try:
        value = json.loads(content.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ChallengerReleaseError("challenger JSON is invalid") from exc
    return validate_forecast_rows(value)


def load_csv_rows(content: bytes) -> list[dict[str, Any]]:
    try:
        reader = csv.DictReader(io.StringIO(content.decode("utf-8")))
        if tuple(reader.fieldnames or ()) != CSV_FIELDS:
            raise ChallengerReleaseError("challenger CSV schema changed")
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
                    raise ChallengerReleaseError(f"CSV {field} must be true or false")
                row[field] = raw[field] == "true"
            row["top_scorelines"] = [
                {
                    "away_goals": int(raw[f"top_{position}_away_goals"]),
                    "home_goals": int(raw[f"top_{position}_home_goals"]),
                    "probability": float(raw[f"top_{position}_probability"]),
                }
                for position in range(1, 4)
            ]
            row = {key: row[key] for key in FORECAST_FIELDS}
            rows.append(row)
    except (UnicodeDecodeError, csv.Error, KeyError, TypeError, ValueError) as exc:
        raise ChallengerReleaseError("challenger CSV is invalid") from exc
    return validate_forecast_rows(rows)


def validate_coverage(value: object, included: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    if not isinstance(value, list) or len(value) != 10:
        raise ChallengerReleaseError("coverage must contain exactly ten fixtures")
    rows: list[dict[str, Any]] = []
    for raw in value:
        if not isinstance(raw, dict) or tuple(raw) != COVERAGE_FIELDS:
            raise ChallengerReleaseError("coverage row schema changed")
        row = dict(raw)
        key = row["fixture_key"]
        if key not in FIXTURES or (row["kickoff_utc"], row["home_team"], row["away_team"]) != (
            FIXTURES[key][1],
            FIXTURES[key][2],
            FIXTURES[key][3],
        ):
            raise ChallengerReleaseError("coverage fixture identity changed")
        if not isinstance(row["included"], bool):
            raise ChallengerReleaseError("coverage included flag must be boolean")
        expected_reason = None if row["included"] else "not_generated_after_kickoff"
        if row["reason"] != expected_reason:
            raise ChallengerReleaseError("coverage reason is invalid")
        rows.append(row)
    if {row["fixture_key"] for row in rows} != set(FIXTURES):
        raise ChallengerReleaseError("coverage has duplicate or missing fixture identities")
    included_keys = {row["fixture_key"] for row in included}
    if included_keys != {row["fixture_key"] for row in rows if row["included"]}:
        raise ChallengerReleaseError("coverage and forecast inclusion differ")
    return rows


def validate_evaluation(value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ChallengerReleaseError("evaluation summary must be an object")
    required = {
        "schema_version",
        "model_id",
        "decision_label",
        "promotion_performed",
        "paired_rows",
        "paired_seasons",
        "positive_seasons",
        "pooled",
        "per_season",
        "paired_date_bootstrap",
        "lambda_calibration_bins",
        "technical_gates",
        "claim_boundary",
        "descriptive_stress_2025_26",
        "protocol_sha256",
        "protocol_hashes",
        "source_sha256",
        "incumbent_oos_sha256",
    }
    if set(value) != required:
        raise ChallengerReleaseError("evaluation summary schema changed")
    if (
        value["schema_version"] != "elo-poisson-challenger-evaluation/v1"
        or value["model_id"] != MODEL_ID
    ):
        raise ChallengerReleaseError("evaluation model/schema changed")
    if (
        value["decision_label"]
        not in {
            "ELO_CHALLENGER_VALID_NOT_PROMOTED",
            "ELO_CHALLENGER_VALID_RESEARCH_SIGNAL",
        }
        or value["promotion_performed"] is not False
    ):
        raise ChallengerReleaseError("evaluation decision or promotion boundary changed")
    if value["paired_rows"] != 3800 or value["paired_seasons"] != 10:
        raise ChallengerReleaseError("evaluation paired denominator changed")
    per_season = value["per_season"]
    if (
        not isinstance(per_season, list)
        or len(per_season) != 10
        or any(not isinstance(row, dict) or row.get("rows") != 380 for row in per_season)
    ):
        raise ChallengerReleaseError("evaluation per-season denominator changed")
    if value["protocol_sha256"] != EFFECTIVE_PROTOCOL_SHA256:
        raise ChallengerReleaseError("evaluation protocol commitment changed")
    if value["protocol_hashes"] != PROTOCOL_HASHES:
        raise ChallengerReleaseError("evaluation protocol hash set changed")
    if (
        value["source_sha256"] != SOURCE_SHA256
        or value["incumbent_oos_sha256"] != INCUMBENT_OOS_SHA256
    ):
        raise ChallengerReleaseError("evaluation source commitment changed")
    if value["positive_seasons"] != 7:
        raise ChallengerReleaseError("evaluation robustness count changed")
    if value["claim_boundary"] != {
        "designed_after_reviewing_v1_forecast_shape": True,
        "exact_score_diversity_selection_objective": False,
        "promotion_automatic": False,
        "role": "exploratory_challenger",
    }:
        raise ChallengerReleaseError("evaluation claim boundary changed")
    if not isinstance(value["technical_gates"], dict) or not all(
        gate is True for gate in value["technical_gates"].values()
    ):
        raise ChallengerReleaseError("evaluation technical gate is not true")
    forbidden = {
        "coefficients",
        "fitted_coefficients",
        "final_elo_state",
        "rating_map",
        "ratings",
        "provider_id",
        "source_url",
        "result",
        "home_goals",
        "away_goals",
        "match_id",
        "fixture_key",
        "home_team",
        "away_team",
        "kickoff_utc",
    }
    _reject_forbidden_keys(value, forbidden)
    return dict(value)


def _reject_forbidden_keys(value: object, forbidden: set[str]) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            lowered_key = str(key).lower()
            if lowered_key in forbidden or lowered_key.startswith(
                ("provider_", "odds_", "fitted_", "rating_")
            ):
                raise ChallengerReleaseError(
                    f"evaluation contains forbidden private/raw field: {key}"
                )
            _reject_forbidden_keys(child, forbidden)
    elif isinstance(value, list):
        for child in value:
            _reject_forbidden_keys(child, forbidden)
    elif isinstance(value, str):
        lowered = value.lower().replace("\\", "/")
        if any(
            segment in f"/{lowered.lstrip('/')}"
            for segment in ("/reports/private/", "/data/processed/", "/models/")
        ):
            raise ChallengerReleaseError("evaluation contains a private path")
    elif isinstance(value, float) and not math.isfinite(value):
        raise ChallengerReleaseError("evaluation contains a non-finite number")


def render_table(rows: Sequence[Mapping[str, Any]]) -> str:
    lines = [
        "| Kickoff (Europe/London) | Fixture | Home | Draw | Away | "
        "Expected goals λ (H–A) | Top 3 scorelines | Model | Status |",
        "| --- | --- | ---: | ---: | ---: | ---: | --- | --- | --- |",
    ]
    for row in rows:
        top = "; ".join(
            f"{score['home_goals']}–{score['away_goals']} ({float(score['probability']):.1%})"
            for score in row["top_scorelines"]
        )
        lines.append(
            f"| {str(row['kickoff_local'])[:16].replace('T', ' ')} | "
            f"{row['home_team']} — {row['away_team']} | {float(row['p_home']):.1%} | "
            f"{float(row['p_draw']):.1%} | {float(row['p_away']):.1%} | "
            f"{float(row['lambda_home']):.2f}–{float(row['lambda_away']):.2f} | {top} | "
            f"`{row['model_id']}` | `{row['artifact_status']}` |"
        )
    return "\n".join(lines)


def _table_block(document: str) -> str:
    if document.count(TABLE_START) != 1 or document.count(TABLE_END) != 1:
        raise ChallengerReleaseError("challenger README table markers are missing or duplicated")
    block = document.split(TABLE_START, 1)[1].split(TABLE_END, 1)[0]
    return "\n".join(block.splitlines()).strip()


def validate_release_contents(items: Mapping[str, bytes]) -> list[dict[str, Any]]:
    required = (
        JSON_PATH,
        CSV_PATH,
        COVERAGE_PATH,
        EVALUATION_PATH,
        README_PATH,
        PROVENANCE_PATH,
        ROOT_README_PATH,
    )
    missing = [path.as_posix() for path in required if path.as_posix() not in items]
    if missing:
        raise ChallengerReleaseError(f"challenger release files are missing: {', '.join(missing)}")
    json_rows = load_json_rows(items[JSON_PATH.as_posix()])
    csv_rows = load_csv_rows(items[CSV_PATH.as_posix()])
    if json_rows != csv_rows:
        raise ChallengerReleaseError("challenger JSON and CSV rows differ")
    coverage = json.loads(items[COVERAGE_PATH.as_posix()].decode("utf-8"))
    validate_coverage(coverage, json_rows)
    evaluation = json.loads(items[EVALUATION_PATH.as_posix()].decode("utf-8"))
    validate_evaluation(evaluation)
    expected_table = render_table(json_rows)
    for path in (README_PATH, ROOT_README_PATH):
        if _table_block(items[path.as_posix()].decode("utf-8")) != expected_table:
            raise ChallengerReleaseError(f"{path.as_posix()} table does not match machine rows")
    provenance = items[PROVENANCE_PATH.as_posix()].decode("utf-8")
    for commitment in (PRIVATE_ARTIFACT_SHA256, EFFECTIVE_PROTOCOL_SHA256, PRIVATE_CODE_COMMIT):
        if commitment not in provenance:
            raise ChallengerReleaseError("challenger provenance commitment is missing")
    return json_rows


def validate_release_tree(root: Path) -> list[dict[str, Any]]:
    paths = (
        JSON_PATH,
        CSV_PATH,
        COVERAGE_PATH,
        EVALUATION_PATH,
        README_PATH,
        PROVENANCE_PATH,
        ROOT_README_PATH,
    )
    return validate_release_contents(
        {path.as_posix(): (root / path).read_bytes() for path in paths}
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate the public Elo-Poisson challenger pack")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    rows = validate_release_tree(args.root.resolve())
    print(f"challenger release validation: PASS ({len(rows)} prospective rows)")
