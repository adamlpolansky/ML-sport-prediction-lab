"""Synthetic holdout metrics and calibration plotting."""

from __future__ import annotations

import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
from matplotlib import pyplot as plt  # noqa: E402

from .model import DISCLAIMER, SyntheticPoissonModel

LABELS = ("H", "D", "A")
PROBABILITY_KEYS = ("home_win", "draw", "away_win")


def evaluate(model: SyntheticPoissonModel, rows: list[dict[str, str]]) -> dict[str, object]:
    log_losses: list[float] = []
    brier_scores: list[float] = []
    correct = 0
    observations: list[tuple[float, int]] = []

    for row in rows:
        probabilities = model.probabilities(row["home_team"], row["away_team"])
        ordered = [probabilities[key] for key in PROBABILITY_KEYS]
        actual = row["result"]
        actual_index = LABELS.index(actual)
        predicted_label = LABELS[max(range(3), key=ordered.__getitem__)]
        log_losses.append(-math.log(max(ordered[actual_index], 1e-15)))
        brier_scores.append(
            sum(
                (probability - float(index == actual_index)) ** 2
                for index, probability in enumerate(ordered)
            )
        )
        correct += int(predicted_label == actual)
        observations.extend(
            (probability, int(index == actual_index)) for index, probability in enumerate(ordered)
        )

    bins = calibration_bins(observations)
    ece = sum(
        item["count"] * abs(item["mean_probability"] - item["empirical_frequency"]) for item in bins
    ) / len(observations)
    return {
        "accuracy": correct / len(rows),
        "brier_score": sum(brier_scores) / len(brier_scores),
        "calibration_bins": bins,
        "disclaimer": DISCLAIMER,
        "ece": ece,
        "evaluation_rows": len(rows),
        "log_loss": sum(log_losses) / len(log_losses),
        "split": "chronological synthetic holdout",
    }


def calibration_bins(observations: list[tuple[float, int]]) -> list[dict[str, float | int | str]]:
    edges = tuple(step / 10 for step in range(11))
    bins: list[dict[str, float | int | str]] = []
    for lower, upper in zip(edges[:-1], edges[1:], strict=True):
        selected = [
            item
            for item in observations
            if lower <= item[0] < upper or upper == 1.0 and item[0] == 1.0
        ]
        if not selected:
            continue
        bins.append(
            {
                "bin": f"[{lower:.1f}, {upper:.1f}{']' if upper == 1.0 else ')'}",
                "count": len(selected),
                "mean_probability": sum(item[0] for item in selected) / len(selected),
                "empirical_frequency": sum(item[1] for item in selected) / len(selected),
            }
        )
    return bins


def plot_reliability(
    path: Path,
    bins: list[dict[str, float | int | str]],
    evaluation_rows: int,
) -> None:
    predicted = [float(item["mean_probability"]) for item in bins]
    observed = [float(item["empirical_frequency"]) for item in bins]
    counts = [int(item["count"]) for item in bins]

    fig, ax = plt.subplots(figsize=(7.2, 5.2), dpi=140)
    fig.patch.set_facecolor("#FFFFFF")
    ax.set_facecolor("#FAFBFC")
    ax.plot(
        [0, 1],
        [0, 1],
        color="#374151",
        linestyle="--",
        linewidth=1.5,
        label="Ideal calibration",
    )
    ax.plot(
        predicted,
        observed,
        color="#2563EB",
        marker="o",
        markerfacecolor="#FFFFFF",
        markeredgecolor="#1D4ED8",
        markeredgewidth=1.8,
        linewidth=2.2,
        label="Synthetic holdout",
    )
    for x_value, y_value, count in zip(predicted, observed, counts, strict=True):
        ax.annotate(
            f"n={count}",
            (x_value, y_value),
            xytext=(6, 7),
            textcoords="offset points",
            fontsize=8,
            color="#374151",
        )
    ax.set(
        xlim=(0, 1),
        ylim=(0, 1),
        xlabel="Mean predicted probability",
        ylabel="Empirical frequency",
    )
    fig.suptitle(
        "Synthetic H/D/A calibration reliability",
        x=0.11,
        y=0.97,
        ha="left",
        fontsize=15,
        color="#111827",
    )
    fig.text(
        0.11,
        0.915,
        "Fixed probability bins · "
        f"{evaluation_rows} holdout fixtures · {evaluation_rows * 3} class observations",
        fontsize=9,
        color="#4B5563",
    )
    ax.grid(color="#D1D5DB", linewidth=0.7, alpha=0.7)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False, loc="lower right")
    fig.text(0.11, 0.01, DISCLAIMER, fontsize=8, color="#4B5563")
    fig.tight_layout(rect=(0, 0.04, 1, 0.88))
    fig.savefig(path, metadata={"Software": "epl-probability-forecasting-lab"})
    plt.close(fig)
