from __future__ import annotations

from pathlib import Path

from epl_probability_lab.demo import DEFAULT_DEMO_CONFIG
from epl_probability_lab.publication import inspect_paths
from epl_probability_lab.synthetic import generate_fixtures


def _fixture_csv_bytes() -> bytes:
    import csv
    import io

    from epl_probability_lab.synthetic import FIELDNAMES

    handle = io.StringIO(newline="")
    writer = csv.DictWriter(handle, fieldnames=FIELDNAMES, lineterminator="\n")
    writer.writeheader()
    writer.writerows(
        generate_fixtures(DEFAULT_DEMO_CONFIG["seed"], DEFAULT_DEMO_CONFIG["fixture_rows"])
    )
    return handle.getvalue().encode()


def test_safe_synthetic_artifact_is_accepted() -> None:
    assert inspect_paths([("demo/synthetic_fixtures.csv", _fixture_csv_bytes())]) == []


def test_dc_market_supplement_cannot_be_replaced_or_expanded() -> None:
    path = "forecasts/2026-27/tracking/dc_mw1_goal_markets.json"
    content = (Path(__file__).resolve().parents[1] / path).read_bytes()
    assert inspect_paths([(path, content)]) == []
    assert inspect_paths([(path, content + b" ")])


def test_real_row_disguised_as_approved_synthetic_fixture_is_rejected() -> None:
    content = (
        b"fixture_id,match_date,home_team,away_team,home_goals,away_goals,result,"
        b"data_kind,disclaimer\nreal-1,2026-08-21,Arsenal,Chelsea,0,0,D,synthetic,fictional\n"
    )
    reasons = {
        violation.reason for violation in inspect_paths([("demo/synthetic_fixtures.csv", content)])
    }
    assert "approved synthetic artifact failed semantic regeneration" in reasons


def test_source_cache_and_unapproved_match_rows_are_rejected() -> None:
    content = b'{"provider_id":"real-1","home_team":"Real A","outcome":"H"}'
    violations = inspect_paths([("data/provider/cache.json", content)])
    reasons = {violation.reason for violation in violations}
    assert "forbidden cache, source-data, credential, or private-artifact path" in reasons
    assert "real-person, competition-source, or provider row signature" in reasons
    assert "unapproved match, outcome, or probability data" in reasons


def test_credentials_and_local_paths_are_rejected() -> None:
    token = "gh" + "p_" + "A" * 36
    content = f"token={token}\npath=C:\\Users\\someone\\file".encode()
    reasons = {violation.reason for violation in inspect_paths([("notes.txt", content)])}
    assert "credential-like token" in reasons
    assert "local user path" in reasons


def test_linux_user_path_and_hostname_are_rejected() -> None:
    content = b"output=/" + b"home/researcher/results host" + b"name=private-laptop"
    reasons = {violation.reason for violation in inspect_paths([("notes.txt", content)])}
    assert "local user path" in reasons
    assert "local hostname" in reasons
