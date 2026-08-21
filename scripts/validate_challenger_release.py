from __future__ import annotations

import argparse
from pathlib import Path

from epl_probability_lab.challenger_release import validate_release_tree


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate the public Elo-Poisson challenger pack")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    rows = validate_release_tree(args.root.resolve())
    print(f"challenger release validation: PASS ({len(rows)} prospective rows)")


if __name__ == "__main__":
    main()
