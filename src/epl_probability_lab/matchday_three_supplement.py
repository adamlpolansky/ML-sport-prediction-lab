"""Validate the unscored retrospective MW3 supplement, never evaluate outcomes."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections.abc import Mapping
from datetime import datetime
from pathlib import Path

from . import matchday_three_release as parent

DIRECTORY = parent.DIRECTORY / "retrospective"
JSON_PATH = DIRECTORY / "forecast.json"
CSV_PATH = DIRECTORY / "forecast.csv"
MANIFEST_PATH = DIRECTORY / "manifest.json"
README_PATH = DIRECTORY / "README.md"
STATUS = "retrospective_frozen_post_mw2_unscored"
FORECAST_ID = parent.FORECAST_ID + "-retrospective-supplement"
GENERATED_AT = "2026-09-05T15:26:08Z"
INFORMATION_CUTOFF = "2026-09-01T11:23:47Z"
TABLE_START = "<!-- mw3-retrospective-table:start -->"
TABLE_END = "<!-- mw3-retrospective-table:end -->"
HASHES = {
    JSON_PATH: "8a67ab9461d909987650e01071afdd41b2e1b851c1fbd2b4707238a82c5c09ca",
    CSV_PATH: "6ca8d7987a074fb03fa106a34868b5ce054acf272a193d806a71ae6c2d052076",
    MANIFEST_PATH: "ee149bee868d06fa95b8137ab8ef2ec5da8dc43bb0daa13b2783b63079a3fb53",
}
FIXTURE_KEYS = tuple(f"epl-mw03-{index:02}" for index in range(1, 8))


class SupplementError(ValueError):
    """The supplement is not the approved frozen-state, unscored release."""


def validate_rows(rows: object) -> list[dict]:
    if not isinstance(rows, list) or len(rows) != 7:
        raise SupplementError("exactly seven retrospective rows required")
    if any(not isinstance(row, dict) or tuple(row) != parent.FORECAST_FIELDS for row in rows):
        raise SupplementError("forecast-only schema required; results and metrics are forbidden")
    if tuple(row["fixture_key"] for row in rows) != FIXTURE_KEYS:
        raise SupplementError("supplement fixture coverage changed")
    for row in rows:
        if (
            row["forecast_id"] != FORECAST_ID
            or row["model_id"] != parent.MODEL_ID
            or row["artifact_status"] != STATUS
            or row["generated_at_utc"] != GENERATED_AT
            or row["information_cutoff_utc"] != INFORMATION_CUTOFF
            or (row["competition"], row["season"], row["matchday"], row["timezone"])
            != ("EPL", "2026-27", 3, "Europe/London")
        ):
            raise SupplementError("retrospective identity or actual generation timestamp changed")
        kickoff, home, away = parent.FIXTURES[row["fixture_key"]]
        if (row["kickoff_utc"], row["home_team"], row["away_team"]) != (kickoff, home, away):
            raise SupplementError("fixture identity mismatch")
        if not INFORMATION_CUTOFF < kickoff <= GENERATED_AT:
            raise SupplementError("frozen information must precede kickoff, generation follows it")
        local = datetime.fromisoformat(row["kickoff_local"])
        if local != parent._utc(kickoff) or local.utcoffset().total_seconds() != 3600:
            raise SupplementError("London kickoff mismatch")
        for side, team in (("home", home), ("away", away)):
            flag = row[f"{side}_neutral_reentry"]
            if type(flag) is not bool or flag != (
                team in ("Hull City", "Coventry City", "Ipswich Town")
            ):
                raise SupplementError("frozen neutral-reentry identity changed")
        for field in ("lambda_home", "lambda_away"):
            value = row[field]
            if (
                type(value) not in (int, float)
                or not math.isfinite(value)
                or not 0.05 <= value <= 6
            ):
                raise SupplementError("invalid goal expectation")
        expected = parent.poisson_outputs(row["lambda_home"], row["lambda_away"])
        over, btts = parent.coherent_markets(row["lambda_home"], row["lambda_away"])
        expected.update(p_over_2_5=over, p_btts=btts)
        for field in ("p_home", "p_draw", "p_away", "p_over_2_5", "p_btts", "tail_mass"):
            value = row[field]
            if (
                type(value) not in (int, float)
                or not math.isfinite(value)
                or not math.isclose(value, expected[field], rel_tol=0, abs_tol=1e-12)
            ):
                raise SupplementError("coherent probability mismatch")
        if type(row["score_max"]) is not int or row["score_max"] != expected["score_max"]:
            raise SupplementError("score-grid mismatch")
        if not isinstance(row["top_scorelines"], list) or len(row["top_scorelines"]) != 3:
            raise SupplementError("top-scoreline schema mismatch")
        for actual, wanted in zip(row["top_scorelines"], expected["top_scorelines"], strict=True):
            if (
                not isinstance(actual, dict)
                or set(actual) != set(wanted)
                or any(actual[k] != wanted[k] for k in ("home_goals", "away_goals"))
                or not math.isclose(
                    actual["probability"], wanted["probability"], rel_tol=0, abs_tol=1e-12
                )
            ):
                raise SupplementError("coherent scoreline mismatch")
        for market in ("over_2_5", "btts"):
            if type(row[f"{market}_selected"]) is not bool or row[f"{market}_selected"] != (
                row[f"p_{market}"] != 0.5
            ):
                raise SupplementError("both-sided market selection mismatch")
    return rows


def required_paths() -> tuple[Path, ...]:
    return (
        JSON_PATH,
        CSV_PATH,
        MANIFEST_PATH,
        README_PATH,
        parent.JSON_PATH,
        parent.COVERAGE_PATH,
        parent.UPDATE_PATH,
        parent.ROOT_README_PATH,
    )


def validate_contents(contents: Mapping[str | Path, bytes]) -> list[dict]:
    items = {Path(path): value for path, value in contents.items()}
    if any(path not in items for path in required_paths()):
        raise SupplementError("retrospective supplement or parent evidence missing")
    for path, digest in HASHES.items():
        if hashlib.sha256(items[path]).hexdigest() != digest:
            raise SupplementError("frozen retrospective supplement bytes changed")
    for path in (parent.JSON_PATH, parent.COVERAGE_PATH, parent.UPDATE_PATH):
        if hashlib.sha256(items[path]).hexdigest() != parent.PUBLIC_ARTIFACT_SHA256[path]:
            raise SupplementError("original prospective evidence changed")
    rows = validate_rows(json.loads(items[JSON_PATH]))
    if parent.csv_bytes(rows) != items[CSV_PATH]:
        raise SupplementError("retrospective CSV/JSON mismatch")
    original = json.loads(items[parent.JSON_PATH])
    keys = {row["fixture_key"] for row in rows}
    original_keys = {row["fixture_key"] for row in original}
    excluded = {
        row["fixture_key"] for row in json.loads(items[parent.COVERAGE_PATH]) if not row["included"]
    }
    if keys != excluded or keys & original_keys or keys | original_keys != set(parent.FIXTURES):
        raise SupplementError("original plus supplement must cover ten unique fixtures")
    manifest = json.loads(items[MANIFEST_PATH])
    parent_update = json.loads(items[parent.UPDATE_PATH])
    if (
        manifest["evaluation_performed"] is not False
        or manifest["evaluation_status"] != "not_evaluated_by_user_request"
        or manifest["mw3_results_used"] != 0
        or manifest["model_refit_performed"] is not False
        or manifest["elo_update_performed"] is not False
        or manifest["frozen_local_audit_sha256"] != parent_update["local_audit_sha256"]
        or manifest["parent_forecast_sha256"] != parent.PUBLIC_ARTIFACT_SHA256[parent.JSON_PATH]
        or manifest["generated_at_utc"] != GENERATED_AT
        or manifest["information_cutoff_utc"] != INFORMATION_CUTOFF
    ):
        raise SupplementError("inference-only frozen-state contract changed")
    for path in (README_PATH, parent.ROOT_README_PATH):
        document = items[path].decode().replace("\r\n", "\n")
        if (
            document.count(TABLE_START) != 1
            or document.count(TABLE_END) != 1
            or document.split(TABLE_START)[1].split(TABLE_END)[0].strip()
            != parent.render_table(rows)
        ):
            raise SupplementError("retrospective README table mismatch")
    return rows


def validate_tree(root: Path) -> list[dict]:
    return validate_contents({path: (root / path).read_bytes() for path in required_paths()})


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    rows = validate_tree(args.root)
    print(f"Retrospective supplement: PASS ({len(rows)} forecasts, no outcome evaluation)")


if __name__ == "__main__":
    main()
