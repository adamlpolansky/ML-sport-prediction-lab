from __future__ import annotations

from epl_probability_lab.feature_demo import build_evidence, write_evidence


def test_evidence_is_deterministic_and_synthetic(tmp_path) -> None:
    first = tmp_path / "one"
    second = tmp_path / "two"
    assert write_evidence(first).read_bytes() == write_evidence(second).read_bytes()
    evidence = build_evidence()
    assert evidence["data_kind"] == "synthetic"
    assert evidence["tier_anchor_table_complete"] is True
    assert evidence["row_order_invariant"] is True
    assert evidence["future_result_invariant"] is True
    assert evidence["elo_zero_sum_update_balance"] == 0.0
