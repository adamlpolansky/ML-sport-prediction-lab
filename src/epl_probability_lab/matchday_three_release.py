"""Validate the partial prospective MW3 release after the MW2 Elo update."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
from collections.abc import Mapping, Sequence
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from .challenger_release import CSV_FIELDS as BASE_CSV_FIELDS
from .challenger_release import FORECAST_FIELDS as BASE_FORECAST_FIELDS
from .challenger_release import poisson_outputs

DIRECTORY = Path("forecasts/2026-27/matchday-03/challengers/elo-poisson-v1-post-mw2")
JSON_PATH = DIRECTORY / "forecast.json"
CSV_PATH = DIRECTORY / "forecast.csv"
COVERAGE_PATH = DIRECTORY / "coverage.json"
UPDATE_PATH = DIRECTORY / "update.json"
README_PATH = DIRECTORY / "README.md"
PROVENANCE_PATH = DIRECTORY / "provenance.md"
ROOT_README_PATH = Path("README.md")
MODEL_ID = "fixed-elo-neutral-reentry-poisson-v1-post-mw1-refit-post-mw2-elo"
FORECAST_ID = "epl-2026-27-mw03-elo-poisson-v1-post-mw2"
STATUS = "exploratory_post_matchweek_elo_update"
EXTRA_FIELDS = ("p_over_2_5", "p_btts", "over_2_5_selected", "btts_selected")
FORECAST_FIELDS = tuple(sorted((*BASE_FORECAST_FIELDS, *EXTRA_FIELDS)))
CSV_FIELDS = (*BASE_CSV_FIELDS, *EXTRA_FIELDS)
TABLE_START = "<!-- matchday3-table:start -->"
TABLE_END = "<!-- matchday3-table:end -->"
SOURCE_COMMIT = "0690446f794fde748ea4b994244def699c6a65b2"
SOURCE_BLOB = "dec39f0aa20d4ea5653ecfe4257bc7910c00e0eb"
SOURCE_SHA256 = "10d40e1e7a17e90b64973b83fe2ea78c672819372a186fe87a80b17f4c7c575a"
UPDATE_FIELDS = {
    "schema_version",
    "generated_at_utc",
    "source_commit",
    "source_blob",
    "source_sha256",
    "source_fetched_at_utc",
    "source_license",
    "source_path",
    "prior_audit_sha256",
    "local_audit_sha256",
    "model_id",
    "model_refit_performed",
    "promotion_performed",
    "mapping_training_rows",
    "mapping_training_max_date",
    "elo_state_through",
    "elo_results_added",
    "elo_teams_updated",
    "elo_k_factor",
    "elo_home_advantage",
    "elo_rating_scale",
    "elo_total_change",
    "same_date_policy",
    "mw3_results_used",
    "included_fixtures",
    "excluded_after_kickoff",
}
FIXTURES = {
    "epl-mw03-01": ("2026-09-04T19:00:00Z", "Ipswich Town", "Liverpool"),
    "epl-mw03-02": ("2026-09-05T11:30:00Z", "Newcastle United", "AFC Bournemouth"),
    "epl-mw03-03": ("2026-09-05T14:00:00Z", "Nottingham Forest", "Tottenham Hotspur"),
    "epl-mw03-04": ("2026-09-05T14:00:00Z", "Manchester City", "Coventry City"),
    "epl-mw03-05": ("2026-09-05T14:00:00Z", "Brighton & Hove Albion", "Leeds United"),
    "epl-mw03-06": ("2026-09-05T14:00:00Z", "Brentford", "Sunderland"),
    "epl-mw03-07": ("2026-09-05T14:00:00Z", "Fulham", "Crystal Palace"),
    "epl-mw03-08": ("2026-09-05T16:30:00Z", "Hull City", "Aston Villa"),
    "epl-mw03-09": ("2026-09-06T13:00:00Z", "Everton", "Manchester United"),
    "epl-mw03-10": ("2026-09-06T15:30:00Z", "Arsenal", "Chelsea"),
}
PUBLIC_ARTIFACT_SHA256 = {
    JSON_PATH: "9b80445f7f8a25874f19cdb35850a8312e5dcc8557e6e6324ae0fc6302e80243",
    CSV_PATH: "57ff33607450f3fbf77cd0701d23bec2ded43fcd62623a4c3bcffb20acb85316",
    COVERAGE_PATH: "f49a0137df0d0211e018b08479f4d7ac9782dae7e264daabb4fc18595bca301f",
    UPDATE_PATH: "1743d78336cc304fbd2809de3fee7d735ac1654e8111feb521685a3a069b331e",
}


class MatchdayThreeError(ValueError):
    """A release field, source, timestamp or derived probability is inconsistent."""


def _utc(value: object) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise MatchdayThreeError("explicit UTC timestamp required")
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise MatchdayThreeError("invalid timestamp") from exc


def coherent_markets(home: float, away: float) -> tuple[float, float]:
    """Use the same normalized finite score grid as public H/D/A and scorelines."""
    output = poisson_outputs(home, away)
    maximum = int(output["score_max"])
    h = [math.exp(-home)]
    a = [math.exp(-away)]
    for goal in range(1, maximum + 1):
        h.append(h[-1] * home / goal)
        a.append(a[-1] * away / goal)
    total = math.fsum(h) * math.fsum(a)
    over = math.fsum(hg * ag for i, hg in enumerate(h) for j, ag in enumerate(a) if i + j > 2)
    btts = math.fsum(h[1:]) * math.fsum(a[1:])
    return over / total, btts / total


def validate_rows(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list) or not 0 < len(value) <= 10:
        raise MatchdayThreeError("expected one to ten prospective forecast rows")
    for row in value:
        if not isinstance(row, dict) or tuple(row) != FORECAST_FIELDS:
            raise MatchdayThreeError("forecast schema changed")
        key = row["fixture_key"]
        if (
            key not in FIXTURES
            or (row["kickoff_utc"], row["home_team"], row["away_team"]) != FIXTURES[key]
        ):
            raise MatchdayThreeError("fixture identity changed")
        if (row["model_id"], row["forecast_id"], row["artifact_status"]) != (
            MODEL_ID,
            FORECAST_ID,
            STATUS,
        ) or (row["competition"], row["season"], row["matchday"], row["timezone"]) != (
            "EPL",
            "2026-27",
            3,
            "Europe/London",
        ):
            raise MatchdayThreeError("release identity changed")
        cutoff, generated, kickoff = (
            _utc(row[field])
            for field in ("information_cutoff_utc", "generated_at_utc", "kickoff_utc")
        )
        if not cutoff <= generated < kickoff:
            raise MatchdayThreeError("forecast is not prospective")
        local = datetime.fromisoformat(row["kickoff_local"])
        if local != kickoff or local.utcoffset().total_seconds() != 3600:
            raise MatchdayThreeError("London kickoff is inconsistent")
        for field in (
            "home_neutral_reentry",
            "away_neutral_reentry",
            "over_2_5_selected",
            "btts_selected",
        ):
            if not isinstance(row[field], bool):
                raise MatchdayThreeError("flags must be boolean")
        for field in (
            "lambda_home",
            "lambda_away",
            "p_home",
            "p_draw",
            "p_away",
            "p_over_2_5",
            "p_btts",
            "tail_mass",
        ):
            if (
                isinstance(row[field], bool)
                or not isinstance(row[field], (int, float))
                or not math.isfinite(row[field])
            ):
                raise MatchdayThreeError("non-finite or non-numeric prediction")
        home, away = row["lambda_home"], row["lambda_away"]
        if not all(0.05 <= item <= 6.0 for item in (home, away)):
            raise MatchdayThreeError("lambda bounds violated")
        expected = poisson_outputs(home, away)
        over, btts = coherent_markets(home, away)
        expected.update(p_over_2_5=over, p_btts=btts)
        for field in ("p_home", "p_draw", "p_away", "p_over_2_5", "p_btts", "tail_mass"):
            if not math.isclose(row[field], expected[field], rel_tol=0, abs_tol=1e-12):
                raise MatchdayThreeError("coherent score distribution mismatch")
        if row["score_max"] != expected["score_max"] or isinstance(row["score_max"], bool):
            raise MatchdayThreeError("score grid mismatch")
        top = row["top_scorelines"]
        if not isinstance(top, list) or len(top) != 3:
            raise MatchdayThreeError("top scorelines missing")
        for actual, wanted in zip(top, expected["top_scorelines"], strict=True):
            if (
                set(actual) != set(wanted)
                or any(actual[k] != wanted[k] for k in ("home_goals", "away_goals"))
                or not math.isclose(
                    actual["probability"], wanted["probability"], rel_tol=0, abs_tol=1e-12
                )
            ):
                raise MatchdayThreeError("top scoreline mismatch")
        if any(
            row[f"{market}_selected"] != (row[f"p_{market}"] != 0.5)
            for market in ("over_2_5", "btts")
        ):
            raise MatchdayThreeError("strict threshold selection mismatch")
    if len({r["fixture_key"] for r in value}) != len(value):
        raise MatchdayThreeError("duplicate forecast fixture")
    if any(
        len({r[field] for r in value}) != 1
        for field in ("generated_at_utc", "information_cutoff_utc")
    ):
        raise MatchdayThreeError("inconsistent generation timestamp")
    return value


def csv_bytes(rows: Sequence[Mapping[str, Any]]) -> bytes:
    handle = io.StringIO(newline="")
    writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        flat = {k: v for k, v in row.items() if k != "top_scorelines"}
        for k, v in flat.items():
            if isinstance(v, bool):
                flat[k] = str(v).lower()
        for index, score in enumerate(row["top_scorelines"], 1):
            for field in ("home_goals", "away_goals", "probability"):
                flat[f"top_{index}_{field}"] = score[field]
        writer.writerow(flat)
    return handle.getvalue().encode()


def render_table(rows: Sequence[Mapping[str, Any]]) -> str:
    lines = [
        "| Kickoff (Prague) | Fixture | Home | Draw | Away | H/D/A pick | "
        "Goals H–A | O2.5 | BTTS | Modal |",
        "| --- | --- | ---: | ---: | ---: | --- | ---: | ---: | ---: | --- |",
    ]
    for row in rows:
        pick = max(("home", "draw", "away"), key=lambda k: row[f"p_{k}"])
        selected = pick.title()
        modal = row["top_scorelines"][0]
        over_pick = "Over" if row["p_over_2_5"] > 0.5 else "Under"
        btts_pick = "Yes" if row["p_btts"] > 0.5 else "No"
        if not row["over_2_5_selected"]:
            over_pick = "no bet"
        if not row["btts_selected"]:
            btts_pick = "no bet"
        prague = (_utc(row["kickoff_utc"]) + timedelta(hours=2)).strftime("%Y-%m-%d %H:%M")
        lines.append(
            f"| {prague} | {row['home_team']} — {row['away_team']} | "
            f"{row['p_home']:.1%} | {row['p_draw']:.1%} | {row['p_away']:.1%} | {selected} | "
            f"{row['lambda_home']:.2f}–{row['lambda_away']:.2f} | {row['p_over_2_5']:.1%} "
            f"({over_pick}) | {row['p_btts']:.1%} ({btts_pick}) | "
            f"{modal['home_goals']}–{modal['away_goals']} "
            f"({modal['probability']:.1%}) |"
        )
    return "\n".join(lines)


def validate_release_contents(contents: Mapping[str | Path, bytes]) -> list[dict[str, Any]]:
    items = {Path(k): v for k, v in contents.items()}
    required = (
        JSON_PATH,
        CSV_PATH,
        COVERAGE_PATH,
        UPDATE_PATH,
        README_PATH,
        PROVENANCE_PATH,
        ROOT_README_PATH,
    )
    if any(path not in items for path in required):
        raise MatchdayThreeError("MW3 pack is incomplete")
    if len(PUBLIC_ARTIFACT_SHA256) != 4:
        raise MatchdayThreeError("MW3 artifact hashes are not frozen")
    for path, digest in PUBLIC_ARTIFACT_SHA256.items():
        if hashlib.sha256(items[path]).hexdigest() != digest:
            raise MatchdayThreeError(f"immutable MW3 artifact changed: {path}")
    rows = validate_rows(json.loads(items[JSON_PATH]))
    if items[CSV_PATH] != csv_bytes(rows):
        raise MatchdayThreeError("CSV and JSON differ")
    coverage = json.loads(items[COVERAGE_PATH])
    generated = _utc(rows[0]["generated_at_utc"])
    expected_coverage = [
        {
            "fixture_key": key,
            "kickoff_utc": kickoff,
            "home_team": home,
            "away_team": away,
            "included": _utc(kickoff) > generated,
            "reason": None if _utc(kickoff) > generated else "kickoff_passed_before_generation",
        }
        for key, (kickoff, home, away) in FIXTURES.items()
    ]
    if coverage != expected_coverage or {r["fixture_key"] for r in rows} != {
        r["fixture_key"] for r in coverage if r["included"]
    }:
        raise MatchdayThreeError("coverage or time exclusion mismatch")
    update = json.loads(items[UPDATE_PATH])
    validate_update(update, rows, coverage)
    for path in (README_PATH, ROOT_README_PATH):
        document = items[path].decode()
        if (
            document.count(TABLE_START) != 1
            or document.count(TABLE_END) != 1
            or document.split(TABLE_START)[1].split(TABLE_END)[0].strip() != render_table(rows)
        ):
            raise MatchdayThreeError("MW3 README table differs from forecast")
    provenance = items[PROVENANCE_PATH].decode()
    if any(
        digest not in provenance
        for digest in (
            SOURCE_COMMIT,
            SOURCE_BLOB,
            SOURCE_SHA256,
            update["prior_audit_sha256"],
            update["local_audit_sha256"],
        )
    ):
        raise MatchdayThreeError("provenance commitment missing")
    return rows


def validate_update(
    update: object, rows: Sequence[Mapping[str, Any]], coverage: list[dict]
) -> None:
    if not isinstance(update, dict) or set(update) != UPDATE_FIELDS:
        raise MatchdayThreeError("update manifest schema changed")
    if (
        update["schema_version"] != "epl-mw03-elo-update-summary/v1"
        or update["model_id"] != MODEL_ID
    ):
        raise MatchdayThreeError("update manifest identity changed")
    generated = _utc(rows[0]["generated_at_utc"])
    cutoff = _utc(rows[0]["information_cutoff_utc"])
    if (
        _utc(update["generated_at_utc"]) != generated
        or _utc(update["source_fetched_at_utc"]) > cutoff
    ):
        raise MatchdayThreeError("update manifest timestamp mismatch")
    if update["included_fixtures"] != len(rows) or update["excluded_after_kickoff"] != len(
        coverage
    ) - len(rows):
        raise MatchdayThreeError("update manifest coverage mismatch")
    for field, expected in {
        "elo_results_added": 10,
        "elo_teams_updated": 20,
        "elo_k_factor": 20,
        "elo_home_advantage": 60,
        "elo_rating_scale": 400,
        "mw3_results_used": 0,
        "mapping_training_rows": 6090,
    }.items():
        if type(update[field]) is not int or update[field] != expected:
            raise MatchdayThreeError("frozen Elo update contract changed")
    if (
        isinstance(update["elo_total_change"], bool)
        or not isinstance(update["elo_total_change"], (float, int))
        or not math.isclose(update["elo_total_change"], 0, abs_tol=1e-10)
    ):
        raise MatchdayThreeError("Elo update is not zero sum")
    if (
        update["source_license"] != "CC0-1.0"
        or update["source_path"] != "2026-27/1-premierleague.txt"
        or update["same_date_policy"] != "frozen_batch_emit_then_update"
    ):
        raise MatchdayThreeError("source or batch contract changed")
    if (update["source_commit"], update["source_blob"], update["source_sha256"]) != (
        SOURCE_COMMIT,
        SOURCE_BLOB,
        SOURCE_SHA256,
    ):
        raise MatchdayThreeError("source provenance changed")
    if (
        update["model_refit_performed"] is not False
        or update["promotion_performed"] is not False
        or update["elo_results_added"] != 10
        or update["elo_state_through"] != "2026-08-31"
        or update["mapping_training_max_date"] != "2026-08-24"
    ):
        raise MatchdayThreeError("Elo-only update contract changed")


def validate_release_tree(root: Path) -> list[dict[str, Any]]:
    paths = (
        JSON_PATH,
        CSV_PATH,
        COVERAGE_PATH,
        UPDATE_PATH,
        README_PATH,
        PROVENANCE_PATH,
        ROOT_README_PATH,
    )
    return validate_release_contents({p: (root / p).read_bytes() for p in paths})


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    rows = validate_release_tree(args.root)
    print(f"MW3 release: PASS ({len(rows)}/10 prospective forecasts)")


if __name__ == "__main__":
    main()
