"""CLI for the deterministic synthetic forecasting demonstration."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from .evaluation import evaluate, plot_reliability
from .model import DISCLAIMER, SyntheticPoissonModel
from .synthetic import generate_fixtures, write_fixtures

DEFAULT_DEMO_CONFIG = {
    "code_version": "0.1.0",
    "evaluation_rows": 32,
    "fixture_rows": 96,
    "max_goals": 10,
    "seed": 20260805,
    "training_rows": 64,
}


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode()


def _write_json(path: Path, value: Any) -> None:
    path.write_bytes(_json_bytes(value))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _code_sha256(package_dir: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(package_dir.rglob("*.py")):
        digest.update(path.relative_to(package_dir).as_posix().encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def run_demo(output_dir: Path, config_path: Path | None = None) -> dict[str, Any]:
    if config_path is None:
        config = dict(DEFAULT_DEMO_CONFIG)
    else:
        config = json.loads(config_path.read_text(encoding="utf-8"))
    output_dir.mkdir(parents=True, exist_ok=True)

    rows = generate_fixtures(seed=config["seed"], row_count=config["fixture_rows"])
    training = rows[: config["training_rows"]]
    holdout = rows[config["training_rows"] :]
    model = SyntheticPoissonModel.fit(training, max_goals=config["max_goals"])
    example_home = "Amber Owls"
    example_away = "Violet Sparks"
    example_home_goals, example_away_goals = model.expected_goals(example_home, example_away)
    probabilities = model.probabilities(example_home, example_away)

    fixture_path = output_dir / "synthetic_fixtures.csv"
    model_path = output_dir / "synthetic_model.json"
    example_path = output_dir / "prediction_example.json"
    report_path = output_dir / "aggregate_report.json"
    report_markdown_path = output_dir / "aggregate_report.md"
    plot_path = output_dir / "calibration_reliability.png"

    write_fixtures(fixture_path, rows)
    _write_json(model_path, model.to_dict())
    _write_json(
        example_path,
        {
            "away_team": example_away,
            "disclaimer": DISCLAIMER,
            "expected_away_goals": example_away_goals,
            "expected_home_goals": example_home_goals,
            "fixture_id": "SYN-EXAMPLE",
            "home_team": example_home,
            "probabilities": probabilities,
        },
    )
    report = evaluate(model, holdout)
    _write_json(report_path, report)
    report_markdown_path.write_text(
        "# Synthetic holdout report\n\n"
        f"> {DISCLAIMER}\n\n"
        f"- Evaluation fixtures: {report['evaluation_rows']}\n"
        f"- Log loss: {report['log_loss']:.6f}\n"
        f"- Brier score: {report['brier_score']:.6f}\n"
        f"- Accuracy: {report['accuracy']:.6f}\n"
        f"- ECE: {report['ece']:.6f}\n",
        encoding="utf-8",
        newline="\n",
    )
    plot_reliability(plot_path, report["calibration_bins"], len(holdout))

    generated_paths = (
        fixture_path,
        model_path,
        example_path,
        report_path,
        report_markdown_path,
        plot_path,
    )
    evidence = {
        "code_sha256": _code_sha256(Path(__file__).resolve().parent),
        "code_version": config["code_version"],
        "config_sha256": hashlib.sha256(_json_bytes(config)).hexdigest(),
        "disclaimer": DISCLAIMER,
        "evaluation_rows": len(holdout),
        "generated_sha256": {path.name: _sha256(path) for path in generated_paths},
        "network_requests": 0,
        "seed": config["seed"],
        "synthetic_fixture_rows": len(rows),
        "training_rows": len(training),
    }
    _write_json(output_dir / "evidence.json", evidence)
    return evidence


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("demo"))
    parser.add_argument("--config", type=Path)
    args = parser.parse_args()
    evidence = run_demo(args.output_dir, args.config)
    print(
        f"Synthetic demo complete: {evidence['synthetic_fixture_rows']} fixtures, "
        "network requests: 0"
    )


if __name__ == "__main__":
    main()
