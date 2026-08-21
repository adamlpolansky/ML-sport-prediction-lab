from __future__ import annotations

from epl_probability_lab.publication import inspect_paths


def test_safe_synthetic_artifact_is_accepted() -> None:
    content = b"fixture_id,home_team,away_team\nfictional-1,Aster,Beacon\n"
    assert inspect_paths([("demo/synthetic_fixtures.csv", content)]) == []


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
