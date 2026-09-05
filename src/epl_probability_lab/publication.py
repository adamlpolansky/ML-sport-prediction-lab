"""Fail-closed checks for the synthetic-only public distribution boundary."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import subprocess
import tarfile
import zipfile
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

AUTHOR_IDENTITY = "Adam Luboš Polanský"
_SKIP_PARTS = {
    ".git",
    ".venv",
    "venv",
    "build",
    "dist",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
}
_FORBIDDEN_SUFFIXES = {
    ".bundle",
    ".db",
    ".joblib",
    ".onnx",
    ".parquet",
    ".pkl",
    ".sqlite",
    ".sqlite3",
    ".tsv",
    ".xlsx",
    ".zip",
}
_FORBIDDEN_PARTS = {
    "acceptance_records",
    "api_cache",
    "checkpoints",
    "credentials",
    "data/provider",
    "data/raw",
    "data/interim",
    "data/processed",
    "private",
    "provider_payloads",
    "snapshots",
}
_SAFE_DATA = {
    "demo/aggregate_report.json",
    "demo/evidence.json",
    "demo/feature_evidence.json",
    "demo/prediction_example.json",
    "demo/synthetic_fixtures.csv",
    "demo/synthetic_model.json",
}
_FORECAST_DATA = {
    "forecasts/2026-27/matchday-01/forecast.csv",
    "forecasts/2026-27/matchday-01/forecast.json",
}
_CHALLENGER_DATA = {
    "forecasts/2026-27/matchday-01/challengers/elo-poisson-v1/coverage.json",
    "forecasts/2026-27/matchday-01/challengers/elo-poisson-v1/evaluation_summary.json",
    "forecasts/2026-27/matchday-01/challengers/elo-poisson-v1/forecast.csv",
    "forecasts/2026-27/matchday-01/challengers/elo-poisson-v1/forecast.json",
}
_MATCHDAY2_UPDATE_DATA = {
    "forecasts/2026-27/matchday-02/challengers/elo-poisson-v1-post-mw1/coverage.json",
    "forecasts/2026-27/matchday-02/challengers/elo-poisson-v1-post-mw1/forecast.csv",
    "forecasts/2026-27/matchday-02/challengers/elo-poisson-v1-post-mw1/forecast.json",
}
_RESULTS_TRACKER_DATA = {
    "forecasts/2026-27/matchday-01/results/model_scores.csv",
    "forecasts/2026-27/matchday-01/results/model_summary.csv",
    "forecasts/2026-27/matchday-01/results/results.csv",
    "forecasts/2026-27/matchday-01/results/results.json",
    "forecasts/2026-27/tracking/model_performance.csv",
    "forecasts/2026-27/tracking/model_performance.json",
    "forecasts/2026-27/matchday-02/results/results.csv",
    "forecasts/2026-27/matchday-02/results/results.json",
    "forecasts/2026-27/matchday-02/results/model_scores.csv",
    "forecasts/2026-27/matchday-02/results/model_summary.csv",
    "forecasts/2026-27/tracking/betting_selections.csv",
    "forecasts/2026-27/tracking/cumulative_performance.csv",
    "forecasts/2026-27/tracking/dc_mw1_goal_markets.json",
    "forecasts/2026-27/tracking/goal_deviations.csv",
}
_MATCHDAY3_DATA = {
    "forecasts/2026-27/matchday-03/challengers/elo-poisson-v1-post-mw2/forecast.json",
    "forecasts/2026-27/matchday-03/challengers/elo-poisson-v1-post-mw2/forecast.csv",
    "forecasts/2026-27/matchday-03/challengers/elo-poisson-v1-post-mw2/coverage.json",
    "forecasts/2026-27/matchday-03/challengers/elo-poisson-v1-post-mw2/update.json",
}
_APPROVED_DATA = (
    _SAFE_DATA
    | _FORECAST_DATA
    | _CHALLENGER_DATA
    | _MATCHDAY2_UPDATE_DATA
    | _RESULTS_TRACKER_DATA
    | _MATCHDAY3_DATA
)
_TEXT_SUFFIXES = {
    "",
    ".cff",
    ".csv",
    ".ini",
    ".json",
    ".md",
    ".py",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
}


@dataclass(frozen=True)
class PublicationViolation:
    path: str
    reason: str


def _normalized(path: str | Path) -> str:
    normalized = PurePosixPath(str(path).replace("\\", "/")).as_posix()
    return normalized[2:] if normalized.startswith("./") else normalized.lstrip("/")


def _path_findings(path: str) -> list[str]:
    lowered = path.lower()
    findings = []
    suffix = PurePosixPath(lowered).suffix
    if suffix in _FORBIDDEN_SUFFIXES:
        findings.append(f"forbidden artifact suffix {suffix}")
    if any(part in lowered for part in _FORBIDDEN_PARTS):
        findings.append("forbidden cache, source-data, credential, or private-artifact path")
    if suffix in {".csv", ".tsv", ".parquet", ".xlsx"} and path not in _APPROVED_DATA:
        findings.append("data file is not an explicitly approved synthetic artifact")
    return findings


def _text_findings(path: str, text: str) -> list[str]:
    findings = []
    lowered = text.lower()
    forbidden_fragments = (
        "ml-sport-prediction-lab-" + "archive",
        "feat/" + "prediction-lab",
        "wikimedia_" + "managers",
        "wikipedia" + "/uefa",
    )
    if any(fragment in lowered for fragment in forbidden_fragments):
        findings.append("private repository, branch, or source-acquisition identifier")
    if re.search(r"[a-zA-Z]:[\\/]Users[\\/]", text):
        findings.append("local user path")
    if re.search(r"/(?:home|Users)/[A-Za-z0-9._-]+/", text):
        findings.append("local user path")
    if re.search(r"(?i)\b(?:host|hostname)\s*[:=]\s*['\"]?[A-Za-z0-9._-]{4,}", text):
        findings.append("local hostname")
    secret_prefixes = ("gh" + "p_", "github_" + "pat_", "sk" + "-proj-")
    if any(prefix in text for prefix in secret_prefixes):
        findings.append("credential-like token")
    if re.search(r"(?i)(password|secret|token|api[_-]?key)\s*[:=]\s*['\"][^'\"]{8,}", text):
        findings.append("credential-like assignment")
    if re.search(r"(?i)\bPR\s*#\d+\b", text):
        findings.append("pull-request identifier")
    data_suffix = PurePosixPath(path).suffix.lower()
    if data_suffix in {".csv", ".json", ".tsv"}:
        real_row_fields = (
            "manager_name",
            "referee_name",
            "uefa_club",
            "provider_id",
            "source_url",
        )
        if any(field in lowered for field in real_row_fields):
            findings.append("real-person, competition-source, or provider row signature")
        if path not in _APPROVED_DATA and any(
            field in lowered
            for field in ("home_team", "away_team", "home_goals", "probabilities", "outcome")
        ):
            findings.append("unapproved match, outcome, or probability data")
    return findings


def _synthetic_artifact_findings(path: str, text: str) -> list[str]:
    if path not in _SAFE_DATA:
        return []
    try:
        from .demo import DEFAULT_DEMO_CONFIG
        from .feature_demo import FICTIONAL_COMPETITION
        from .model import DISCLAIMER
        from .synthetic import TEAMS, generate_fixtures

        if path == "demo/synthetic_fixtures.csv":
            actual = list(csv.DictReader(io.StringIO(text)))
            expected = generate_fixtures(
                seed=DEFAULT_DEMO_CONFIG["seed"],
                row_count=DEFAULT_DEMO_CONFIG["fixture_rows"],
            )
            valid = actual == expected
        else:
            payload = json.loads(text)
            if path == "demo/synthetic_model.json":
                valid = (
                    payload.get("training_data_kind") == "synthetic"
                    and payload.get("disclaimer") == DISCLAIMER
                    and set(payload.get("team_attack", {})) == set(TEAMS)
                    and set(payload.get("team_defence", {})) == set(TEAMS)
                )
            elif path == "demo/prediction_example.json":
                valid = (
                    payload.get("fixture_id") == "SYN-EXAMPLE"
                    and payload.get("home_team") in TEAMS
                    and payload.get("away_team") in TEAMS
                    and payload.get("disclaimer") == DISCLAIMER
                )
            elif path == "demo/aggregate_report.json":
                valid = (
                    payload.get("split") == "chronological synthetic holdout"
                    and payload.get("disclaimer") == DISCLAIMER
                )
            elif path == "demo/evidence.json":
                valid = (
                    payload.get("seed") == DEFAULT_DEMO_CONFIG["seed"]
                    and payload.get("network_requests") == 0
                    and payload.get("synthetic_fixture_rows") == DEFAULT_DEMO_CONFIG["fixture_rows"]
                    and payload.get("disclaimer") == DISCLAIMER
                )
            else:
                valid = (
                    payload.get("artifact") == "public-v0.2-synthetic-feature-evidence"
                    and payload.get("data_kind") == "synthetic"
                    and payload.get("competition") == FICTIONAL_COMPETITION
                    and payload.get("disclaimer")
                    == "Fictional data only; not empirical EPL evidence."
                )
    except (csv.Error, json.JSONDecodeError, TypeError, ValueError):
        valid = False
    return [] if valid else ["approved synthetic artifact failed semantic regeneration"]


def _forecast_artifact_findings(path: str, content: bytes) -> list[str]:
    if path not in _FORECAST_DATA:
        return []
    from .forecast_release import ForecastReleaseError, load_csv_rows, load_json_rows

    try:
        if path.endswith(".csv"):
            load_csv_rows(content)
        else:
            load_json_rows(content)
    except ForecastReleaseError:
        return ["approved forecast artifact failed semantic validation"]
    return []


def _forecast_pack_findings(items: Iterable[tuple[str, bytes]]) -> list[PublicationViolation]:
    by_path = {_normalized(path): content for path, content in items}
    if not any(path in by_path for path in _FORECAST_DATA):
        return []
    from .forecast_release import ForecastReleaseError, validate_release_contents

    try:
        validate_release_contents(by_path)
    except ForecastReleaseError as exc:
        return [PublicationViolation("forecasts/2026-27/matchday-01", str(exc))]
    return []


def _challenger_artifact_findings(path: str, content: bytes) -> list[str]:
    if path not in _CHALLENGER_DATA:
        return []
    from .challenger_release import (
        ChallengerReleaseError,
        load_csv_rows,
        load_json_rows,
        validate_coverage,
        validate_evaluation,
    )

    try:
        if path.endswith("forecast.csv"):
            load_csv_rows(content)
        elif path.endswith("forecast.json"):
            load_json_rows(content)
        elif path.endswith("coverage.json"):
            payload = json.loads(content.decode("utf-8"))
            included = [
                {"fixture_key": row["fixture_key"]}
                for row in payload
                if isinstance(row, dict) and row.get("included") is True
            ]
            validate_coverage(payload, included)
        else:
            validate_evaluation(json.loads(content.decode("utf-8")))
    except (ChallengerReleaseError, UnicodeDecodeError, json.JSONDecodeError, TypeError, KeyError):
        return ["approved challenger artifact failed semantic validation"]
    return []


def _challenger_pack_findings(
    items: Iterable[tuple[str, bytes]],
) -> list[PublicationViolation]:
    by_path = {_normalized(path): content for path, content in items}
    if not any(path in by_path for path in _CHALLENGER_DATA):
        return []
    from .challenger_release import ChallengerReleaseError, validate_release_contents

    try:
        validate_release_contents(by_path)
    except (ChallengerReleaseError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return [
            PublicationViolation(
                "forecasts/2026-27/matchday-01/challengers/elo-poisson-v1", str(exc)
            )
        ]
    return []


def _matchday2_update_artifact_findings(path: str, content: bytes) -> list[str]:
    if path not in _MATCHDAY2_UPDATE_DATA:
        return []
    from .matchday_update_release import (
        MatchdayUpdateReleaseError,
        load_csv_rows,
        load_json_rows,
        validate_coverage,
    )

    try:
        if path.endswith("forecast.csv"):
            load_csv_rows(content)
        elif path.endswith("forecast.json"):
            load_json_rows(content)
        else:
            payload = json.loads(content.decode("utf-8"))
            included = [
                {"fixture_key": row["fixture_key"]}
                for row in payload
                if isinstance(row, dict) and row.get("included") is True
            ]
            validate_coverage(payload, included)
    except (
        MatchdayUpdateReleaseError,
        UnicodeDecodeError,
        json.JSONDecodeError,
        TypeError,
        KeyError,
    ):
        return ["approved MW2 update artifact failed semantic validation"]
    return []


def _matchday2_update_pack_findings(
    items: Iterable[tuple[str, bytes]],
) -> list[PublicationViolation]:
    by_path = {_normalized(path): content for path, content in items}
    if not any(path in by_path for path in _MATCHDAY2_UPDATE_DATA):
        return []
    from .matchday_update_release import MatchdayUpdateReleaseError, validate_release_contents

    try:
        validate_release_contents(by_path)
    except (MatchdayUpdateReleaseError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return [
            PublicationViolation(
                "forecasts/2026-27/matchday-02/challengers/elo-poisson-v1-post-mw1",
                str(exc),
            )
        ]
    return []


def _results_tracker_pack_findings(
    items: Iterable[tuple[str, bytes]],
) -> list[PublicationViolation]:
    by_path = {_normalized(path): content for path, content in items}
    if not any(path in by_path for path in _RESULTS_TRACKER_DATA):
        return []
    from .results_tracker import ResultsTrackerError, validate_release_contents

    try:
        validate_release_contents(by_path)
    except (ResultsTrackerError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return [
            PublicationViolation(
                "forecasts/2026-27/matchday-01/results",
                str(exc),
            )
        ]
    return []


def inspect_paths(items: Iterable[tuple[str, bytes]]) -> list[PublicationViolation]:
    """Inspect normalized paths and their bytes without trusting file extensions."""

    violations: list[PublicationViolation] = []
    for raw_path, content in items:
        path = _normalized(raw_path)
        if path in _MATCHDAY3_DATA:
            from .matchday_three_release import PUBLIC_ARTIFACT_SHA256

            if hashlib.sha256(content).hexdigest() != PUBLIC_ARTIFACT_SHA256.get(Path(path)):
                violations.append(PublicationViolation(path, "immutable MW3 artifact changed"))
        if path == "forecasts/2026-27/tracking/dc_mw1_goal_markets.json" and (
            hashlib.sha256(content).hexdigest()
            != "41c1c1c129be9d9e4e43fff18a4ee478f9f49f7547b3561d63a49853dcadcd98"
        ):
            violations.append(PublicationViolation(path, "frozen DC market supplement changed"))
        violations.extend(PublicationViolation(path, reason) for reason in _path_findings(path))
        suffix = PurePosixPath(path).suffix.lower()
        if suffix in _TEXT_SUFFIXES:
            try:
                text = content.decode("utf-8")
            except UnicodeDecodeError:
                violations.append(PublicationViolation(path, "non-UTF-8 text-like file"))
            else:
                violations.extend(
                    PublicationViolation(path, reason) for reason in _text_findings(path, text)
                )
                violations.extend(
                    PublicationViolation(path, reason)
                    for reason in _synthetic_artifact_findings(path, text)
                )
        violations.extend(
            PublicationViolation(path, reason)
            for reason in _forecast_artifact_findings(path, content)
        )
        violations.extend(
            PublicationViolation(path, reason)
            for reason in _challenger_artifact_findings(path, content)
        )
        violations.extend(
            PublicationViolation(path, reason)
            for reason in _matchday2_update_artifact_findings(path, content)
        )
    return violations


def _matchday3_pack_findings(items: Iterable[tuple[str, bytes]]) -> list[PublicationViolation]:
    by_path = {_normalized(path): content for path, content in items}
    if not any(path in by_path for path in _MATCHDAY3_DATA):
        return []
    from .matchday_three_release import MatchdayThreeError, validate_release_contents

    try:
        validate_release_contents(by_path)
    except (MatchdayThreeError, UnicodeDecodeError, ValueError, KeyError, TypeError) as exc:
        return [PublicationViolation("forecasts/2026-27/matchday-03", str(exc))]
    return []


def scan_tree(root: Path, *, require_identity: bool = True) -> list[PublicationViolation]:
    """Scan every non-ignored project file, including untracked candidate files."""

    root = root.resolve()
    items: list[tuple[str, bytes]] = []
    violations: list[PublicationViolation] = []
    command = [
        "git",
        "-c",
        f"safe.directory={root.as_posix()}",
        "-C",
        str(root),
        "ls-files",
        "--cached",
        "--others",
        "--exclude-standard",
        "-z",
    ]
    listed = subprocess.run(command, capture_output=True, check=False)
    relatives = (
        [Path(value.decode()) for value in listed.stdout.split(b"\0") if value]
        if listed.returncode == 0
        else [path.relative_to(root) for path in root.rglob("*")]
    )
    listed_paths = {relative.as_posix() for relative in relatives}
    release_paths = (
        _FORECAST_DATA
        | _CHALLENGER_DATA
        | _MATCHDAY2_UPDATE_DATA
        | _RESULTS_TRACKER_DATA
        | _MATCHDAY3_DATA
    )
    for release_path in sorted(release_paths):
        if release_path not in listed_paths and (root / release_path).is_file():
            relatives.append(Path(release_path))
            listed_paths.add(release_path)
    for relative in sorted(relatives):
        if any(part in _SKIP_PARTS for part in relative.parts):
            continue
        path = root / relative
        normalized = _normalized(relative)
        if path.is_symlink():
            violations.append(PublicationViolation(normalized, "symbolic links are not permitted"))
        elif path.is_file():
            items.append((normalized, path.read_bytes()))
    violations.extend(inspect_paths(items))
    violations.extend(_forecast_pack_findings(items))
    violations.extend(_challenger_pack_findings(items))
    violations.extend(_matchday2_update_pack_findings(items))
    violations.extend(_results_tracker_pack_findings(items))
    violations.extend(_matchday3_pack_findings(items))
    if require_identity:
        required = ("README.md", "LICENSE", "pyproject.toml", "CITATION.cff")
        by_path = {path: content for path, content in items}
        for path in required:
            if path not in by_path:
                violations.append(
                    PublicationViolation(path, "required publication surface missing")
                )
            elif AUTHOR_IDENTITY not in by_path[path].decode("utf-8", errors="replace"):
                violations.append(PublicationViolation(path, "canonical author identity missing"))
        license_text = by_path.get("LICENSE", b"").decode("utf-8", errors="replace")
        if "MIT License" not in license_text or "Copyright" not in license_text:
            violations.append(PublicationViolation("LICENSE", "MIT licence notice incomplete"))
    return violations


def scan_archive(path: Path) -> list[PublicationViolation]:
    """Inspect wheel/sdist members without extracting them."""

    items: list[tuple[str, bytes]] = []
    if not path.is_file():
        return [PublicationViolation(str(path), "distribution archive does not exist")]
    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as archive:
            for info in archive.infolist():
                if not info.is_dir():
                    items.append((_archive_member_path(info.filename), archive.read(info)))
    elif tarfile.is_tarfile(path):
        with tarfile.open(path) as archive:
            for member in archive.getmembers():
                if member.isfile():
                    handle = archive.extractfile(member)
                    if handle is not None:
                        items.append((_archive_member_path(member.name), handle.read()))
    else:
        return [PublicationViolation(str(path), "unsupported distribution archive")]
    violations = inspect_paths(items)
    violations.extend(_forecast_pack_findings(items))
    violations.extend(_challenger_pack_findings(items))
    violations.extend(_matchday2_update_pack_findings(items))
    violations.extend(_results_tracker_pack_findings(items))
    violations.extend(_matchday3_pack_findings(items))
    return violations


def _archive_member_path(path: str) -> str:
    parts = PurePosixPath(path).parts
    if len(parts) > 1 and parts[0].startswith("epl_probability_forecasting_lab-"):
        return PurePosixPath(*parts[1:]).as_posix()
    return path


def _print(violations: Sequence[PublicationViolation]) -> None:
    for violation in violations:
        print(f"{violation.path}: {violation.reason}")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--archive", type=Path, action="append", default=[])
    args = parser.parse_args(argv)
    violations = scan_tree(args.root)
    for archive in args.archive:
        violations.extend(scan_archive(archive))
    if violations:
        _print(violations)
        return 1
    print("publication guard: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
