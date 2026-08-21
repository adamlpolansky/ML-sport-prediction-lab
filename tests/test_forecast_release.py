from __future__ import annotations

import copy
import json
import shutil
from pathlib import Path

import pytest

from epl_probability_lab.forecast_release import (
    CSV_PATH,
    JSON_PATH,
    ForecastReleaseError,
    load_json_rows,
    validate_release_tree,
    validate_rows,
)
from epl_probability_lab.publication import inspect_paths

ROOT = Path(__file__).resolve().parents[1]


def _rows() -> list[dict[str, object]]:
    return json.loads((ROOT / JSON_PATH).read_text(encoding="utf-8"))


def test_committed_forecast_pack_is_exact_and_cross_format_consistent() -> None:
    rows = validate_release_tree(ROOT)
    assert len(rows) == 10
    assert {row["artifact_status"] for row in rows} == {"prospective_pre_match"}
    assert {row["information_cutoff_utc"] for row in rows} == {"2026-08-21T12:04:19Z"}
    assert inspect_paths([(JSON_PATH.as_posix(), (ROOT / JSON_PATH).read_bytes())]) == []
    assert inspect_paths([(CSV_PATH.as_posix(), (ROOT / CSV_PATH).read_bytes())]) == []


@pytest.mark.parametrize("forbidden", ["provider_id", "home_goals", "result", "odds_home"])
def test_disguised_raw_provider_result_or_odds_field_fails_on_allowlisted_path(
    forbidden: str,
) -> None:
    rows = _rows()
    rows[0][forbidden] = "disguised"
    content = (json.dumps(rows, ensure_ascii=False) + "\n").encode()
    reasons = {violation.reason for violation in inspect_paths([(JSON_PATH.as_posix(), content)])}
    assert "approved forecast artifact failed semantic validation" in reasons


def test_probability_time_fixture_and_duplicate_gates_fail_closed() -> None:
    rows = _rows()
    invalid_probability = copy.deepcopy(rows)
    invalid_probability[0]["p_home_win"] = float("nan")
    with pytest.raises(ForecastReleaseError, match="finite"):
        validate_rows(invalid_probability)
    invalid_cutoff = copy.deepcopy(rows)
    invalid_cutoff[0]["generated_at_utc"] = "2026-08-21T19:00:00Z"
    with pytest.raises(ForecastReleaseError, match="prospective"):
        validate_rows(invalid_cutoff)
    duplicate = copy.deepcopy(rows)
    duplicate[1]["fixture_key"] = duplicate[0]["fixture_key"]
    with pytest.raises(ForecastReleaseError, match="fixture identity|duplicate"):
        validate_rows(duplicate)


def test_readme_table_must_be_derived_from_machine_rows(tmp_path: Path) -> None:
    release = tmp_path / "release"
    for relative in (JSON_PATH, CSV_PATH, Path("forecasts/2026-27/matchday-01/README.md")):
        destination = release / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, destination)
    shutil.copy2(ROOT / "README.md", release / "README.md")
    readme = release / "forecasts" / "2026-27" / "matchday-01" / "README.md"
    readme.write_text(
        readme.read_text(encoding="utf-8").replace("66.3%", "99.9%", 1),
        encoding="utf-8",
    )
    with pytest.raises(ForecastReleaseError, match="table does not match"):
        validate_release_tree(release)


def test_readme_tables_accept_platform_line_endings(tmp_path: Path) -> None:
    release = tmp_path / "release"
    for relative in (
        JSON_PATH,
        CSV_PATH,
        Path("forecasts/2026-27/matchday-01/README.md"),
        Path("README.md"),
    ):
        destination = release / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, destination)
    for relative in (Path("forecasts/2026-27/matchday-01/README.md"), Path("README.md")):
        path = release / relative
        document = path.read_text(encoding="utf-8")
        path.write_bytes(document.replace("\n", "\r\n").encode("utf-8"))

    assert len(validate_release_tree(release)) == 10


def test_json_schema_order_is_canonical() -> None:
    rows = load_json_rows((ROOT / JSON_PATH).read_bytes())
    changed = [{"fixture_key": row["fixture_key"], **row} for row in rows]
    with pytest.raises(ForecastReleaseError, match="canonical schema"):
        validate_rows(changed)
