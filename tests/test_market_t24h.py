"""Public-safety regression for the intentionally invalid auth sentinel."""

TEST_AUTH_SENTINEL = "invalid-test-sentinel"


def test_auth_sentinel_is_unmistakably_invalid_and_low_entropy() -> None:
    assert TEST_AUTH_SENTINEL == "invalid-test-sentinel"
    assert "." not in TEST_AUTH_SENTINEL
    assert len(set(TEST_AUTH_SENTINEL)) < 16
