from __future__ import annotations

import json
from pathlib import Path

import pytest

from epl_probability_lab.matchday_update_release import (
    CSV_PATH,
    JSON_PATH,
    MatchdayUpdateReleaseError,
    load_json_rows,
    validate_release_tree,
)
from epl_probability_lab.publication import inspect_paths

ROOT = Path(__file__).resolve().parents[1]


def test_committed_mw2_update_pack_is_valid_and_cross_format_consistent() -> None:
    rows = validate_release_tree(ROOT)
    assert len(rows) == 10
    assert {row["matchday"] for row in rows} == {2}
    assert all(row["artifact_status"] == "exploratory_post_matchweek_update" for row in rows)


def test_publication_guard_accepts_allowlisted_mw2_machine_artifacts() -> None:
    for path in (JSON_PATH, CSV_PATH):
        assert inspect_paths([(path.as_posix(), (ROOT / path).read_bytes())]) == []


def test_mw2_update_fails_if_probability_is_changed() -> None:
    payload = json.loads((ROOT / JSON_PATH).read_text(encoding="utf-8"))
    payload[0]["p_home"] += 0.01
    with pytest.raises(MatchdayUpdateReleaseError, match="probabilities"):
        load_json_rows((json.dumps(payload) + "\n").encode())


def test_mw2_update_contains_no_private_state_or_coefficients() -> None:
    content = (ROOT / JSON_PATH).read_text(encoding="utf-8").lower()
    for forbidden in ("alpha_home", "beta_home", "final_elo_state", "elo_home"):
        assert forbidden not in content
