"""Fail-closed checks for the synthetic-only public distribution boundary."""

from __future__ import annotations

import argparse
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
    if suffix in {".csv", ".tsv", ".parquet", ".xlsx"} and path not in _SAFE_DATA:
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
        if path not in _SAFE_DATA and any(
            field in lowered
            for field in ("home_team", "away_team", "home_goals", "probabilities", "outcome")
        ):
            findings.append("unapproved match, outcome, or probability data")
    return findings


def inspect_paths(items: Iterable[tuple[str, bytes]]) -> list[PublicationViolation]:
    """Inspect normalized paths and their bytes without trusting file extensions."""

    violations: list[PublicationViolation] = []
    for raw_path, content in items:
        path = _normalized(raw_path)
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
    return violations


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
    return inspect_paths(items)


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
