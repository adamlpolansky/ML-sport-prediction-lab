from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from epl_probability_lab.demo import run_demo
from epl_probability_lab.model import DISCLAIMER


def test_demo_emits_public_safe_evidence(tmp_path: Path) -> None:
    evidence = run_demo(tmp_path)
    assert evidence["network_requests"] == 0
    assert evidence["synthetic_fixture_rows"] == 96
    assert evidence["training_rows"] == 64
    assert evidence["evaluation_rows"] == 32
    assert evidence["disclaimer"] == DISCLAIMER
    assert len(evidence["generated_sha256"]) == 6

    with (tmp_path / "synthetic_fixtures.csv").open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 96

    example = json.loads((tmp_path / "prediction_example.json").read_text(encoding="utf-8"))
    assert sum(example["probabilities"].values()) == pytest.approx(1.0)
