"""Validate the committed EPL Matchweek 1 forecast evidence pack."""

from __future__ import annotations

import argparse
from pathlib import Path

from epl_probability_lab.forecast_release import ForecastReleaseError, validate_release_tree


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    try:
        rows = validate_release_tree(args.root.resolve())
    except (ForecastReleaseError, OSError) as exc:
        print(f"forecast release validation: FAIL: {exc}")
        return 1
    print(f"forecast release validation: PASS ({len(rows)} prospective rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
