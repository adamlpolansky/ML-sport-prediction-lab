from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import pytest

from epl_probability_lab.challenger_release import (
    COVERAGE_PATH,
    CSV_PATH,
    EVALUATION_PATH,
    JSON_PATH,
    PROVENANCE_PATH,
    README_PATH,
    ROOT_README_PATH,
    ChallengerReleaseError,
    load_json_rows,
    validate_coverage,
    validate_evaluation,
    validate_forecast_rows,
    validate_release_tree,
)
from epl_probability_lab.publication import inspect_paths

ROOT = Path(__file__).resolve().parents[1]


def _rows() -> list[dict[str, object]]:
    return json.loads((ROOT / JSON_PATH).read_text(encoding="utf-8"))


def _evaluation() -> dict[str, object]:
    return json.loads((ROOT / EVALUATION_PATH).read_text(encoding="utf-8"))


def test_committed_challenger_pack_is_exact_and_cross_format_consistent() -> None:
    rows = validate_release_tree(ROOT)
    assert len(rows) == 10
    assert {row["artifact_status"] for row in rows} == {"prospective_pre_match_challenger"}
    assert {row["information_cutoff_utc"] for row in rows} == {"2026-08-21T14:01:16Z"}
    assert {row["generated_at_utc"] for row in rows} == {"2026-08-21T14:01:17Z"}
    expected = {
        JSON_PATH: "7cfff5b6821d508be069e96546fed0276b1efd898a0cecfd5682132ceec7532e",
        CSV_PATH: "cfaba9ec9c31115f5ce5d17ed96ddeebc38aaa363656988e9a8e3ab2cebfeacb",
        COVERAGE_PATH: "c09ed1fe6436717eb87b9dba4e11cab9774e12ab36bcf85f5783103ef4413ca8",
        EVALUATION_PATH: "da81f7d361e9d1b388a220562d0e8d6c986388b224efa8c792e1addcab54bc41",
    }
    assert {
        path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest() for path in expected
    } == expected


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("p_home", float("nan"), "finite"),
        ("lambda_home", float("inf"), "finite"),
        ("lambda_away", -0.1, "bounds"),
        ("score_max", 6.5, "integer"),
    ],
)
def test_nonfinite_negative_and_fractional_values_fail_closed(
    field: str, value: object, message: str
) -> None:
    rows = _rows()
    rows[0][field] = value
    with pytest.raises(ChallengerReleaseError, match=message):
        validate_forecast_rows(rows)


def test_fractional_scoreline_fails_closed() -> None:
    rows = _rows()
    rows[0]["top_scorelines"][0]["home_goals"] = 1.5
    with pytest.raises(ChallengerReleaseError, match="integer"):
        validate_forecast_rows(rows)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("p_draw", 0.2),
        ("lambda_home", 1.5),
        ("tail_mass", 0.0),
        ("score_max", 30),
    ],
)
def test_published_lambda_derivations_fail_when_tampered(field: str, value: object) -> None:
    rows = _rows()
    rows[0][field] = value
    if field == "p_draw":
        rows[0]["p_home"] = 1.0 - float(value) - float(rows[0]["p_away"])
    with pytest.raises(ChallengerReleaseError, match="mismatch|grid"):
        validate_forecast_rows(rows)


def test_top_three_recomputation_fails_when_tampered() -> None:
    rows = _rows()
    rows[0]["top_scorelines"][0]["probability"] = 0.5
    with pytest.raises(ChallengerReleaseError, match="top scoreline"):
        validate_forecast_rows(rows)


def test_included_row_must_be_prospective() -> None:
    rows = _rows()
    rows[0]["generated_at_utc"] = rows[0]["kickoff_utc"]
    with pytest.raises(ChallengerReleaseError, match="prospective"):
        validate_forecast_rows(rows)


def test_coverage_reason_cannot_carry_a_result() -> None:
    coverage = json.loads((ROOT / COVERAGE_PATH).read_text(encoding="utf-8"))
    coverage[0]["result"] = "disguised"
    with pytest.raises(ChallengerReleaseError, match="schema"):
        validate_coverage(coverage, _rows())


def test_readme_table_must_be_machine_derived(tmp_path: Path) -> None:
    release = tmp_path / "release"
    for relative in (
        JSON_PATH,
        CSV_PATH,
        COVERAGE_PATH,
        EVALUATION_PATH,
        README_PATH,
        PROVENANCE_PATH,
        ROOT_README_PATH,
    ):
        destination = release / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, destination)
    readme = release / README_PATH
    readme.write_text(
        readme.read_text(encoding="utf-8").replace("75.9%", "99.9%", 1),
        encoding="utf-8",
    )
    with pytest.raises(ChallengerReleaseError, match="table does not match"):
        validate_release_tree(release)


@pytest.mark.parametrize(
    "forbidden",
    ["provider_id", "result", "odds_home", "fitted_coefficients", "rating_map"],
)
def test_disguised_private_or_raw_field_fails_on_allowlisted_forecast(
    forbidden: str,
) -> None:
    rows = _rows()
    rows[0][forbidden] = "disguised"
    content = (json.dumps(rows, ensure_ascii=False) + "\n").encode()
    reasons = {violation.reason for violation in inspect_paths([(JSON_PATH.as_posix(), content)])}
    assert "approved challenger artifact failed semantic validation" in reasons


@pytest.mark.parametrize(
    "forbidden",
    ["fitted_coefficients", "rating_map", "provider_data", "odds_home", "fixture_key"],
)
def test_evaluation_rejects_fitted_state(forbidden: str) -> None:
    evaluation = _evaluation()
    evaluation["pooled"][forbidden] = {"club": 1.0}
    with pytest.raises(ChallengerReleaseError, match="forbidden"):
        validate_evaluation(evaluation)


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -float("inf")])
def test_evaluation_rejects_nonfinite_aggregate(value: float) -> None:
    evaluation = _evaluation()
    evaluation["pooled"]["joint_log_score_challenger"] = value
    with pytest.raises(ChallengerReleaseError, match="non-finite"):
        validate_evaluation(evaluation)


def test_evaluation_rejects_private_path() -> None:
    evaluation = _evaluation()
    evaluation["pooled"]["note"] = "reports/private/evidence.json"
    with pytest.raises(ChallengerReleaseError, match="private path"):
        validate_evaluation(evaluation)


def test_publication_guard_validates_all_allowlisted_challenger_data() -> None:
    for path in (JSON_PATH, CSV_PATH, COVERAGE_PATH, EVALUATION_PATH):
        assert inspect_paths([(path.as_posix(), (ROOT / path).read_bytes())]) == []


def test_json_schema_order_is_canonical() -> None:
    rows = load_json_rows((ROOT / JSON_PATH).read_bytes())
    changed = [{"fixture_key": row["fixture_key"], **row} for row in rows]
    with pytest.raises(ChallengerReleaseError, match="exact challenger schema"):
        validate_forecast_rows(changed)
