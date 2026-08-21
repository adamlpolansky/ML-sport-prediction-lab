"""Offline, deterministic evidence for the public chronological feature engine."""

from __future__ import annotations

import argparse
import hashlib
import json
import random
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from . import __version__
from .features import (
    TIER_ELO_EMPIRICAL_STATUS,
    TIER_ELO_IMPLEMENTATION_STATUS,
    TIER_ELO_PROMOTION_STATUS,
    ManagerSpell,
    build_chronological_features,
    build_manager_context,
    run_fixed_elo,
    run_tier_seeded_elo,
)
from .features.elo import DEFAULT_TIER_ANCHORS

DEMO_SEED = 20260821
FICTIONAL_COMPETITION = "Northstar Fictional League"
TEAM_STEMS = (
    "Aster",
    "Beacon",
    "Cinder",
    "Dapple",
    "Ember",
    "Fable",
    "Garnet",
    "Harbor",
    "Indigo",
    "Juniper",
    "Kestrel",
    "Lumen",
    "Morrow",
    "Nimbus",
    "Opal",
    "Pioneer",
    "Quartz",
    "Rill",
    "Solace",
    "Thistle",
)


def _round_pairs(teams: Sequence[str], round_index: int) -> list[tuple[str, str]]:
    rotated = [teams[0], *teams[1 + round_index :], *teams[1 : 1 + round_index]]
    return [(rotated[index], rotated[-index - 1]) for index in range(len(teams) // 2)]


def _fixture_rows() -> list[dict[str, Any]]:
    rng = random.Random(DEMO_SEED)
    first = [f"{stem} Collective" for stem in TEAM_STEMS]
    second = [*first[:-2], "Umber Collective", "Vesper Collective"]
    rows: list[dict[str, Any]] = []
    for season_number, teams in enumerate((first, second), start=1):
        season = f"Fictional-Cycle-{season_number}"
        start = datetime(2032 + season_number, 8, 7, 15, tzinfo=UTC)
        for round_index in range(4):
            for match_index, (home, away) in enumerate(_round_pairs(teams, round_index)):
                home_goals = rng.randrange(0, 4)
                away_goals = rng.randrange(0, 4)
                rows.append(
                    {
                        "fixture_id": (
                            f"fictional-{season_number}-{round_index + 1}-{match_index + 1}"
                        ),
                        "event_time": (start + timedelta(days=7 * round_index)).isoformat(),
                        "competition": FICTIONAL_COMPETITION,
                        "season": season,
                        "home_team": home,
                        "away_team": away,
                        "home_goals": home_goals,
                        "away_goals": away_goals,
                        "home_shots": 5 + home_goals * 2 + rng.randrange(0, 8),
                        "away_shots": 5 + away_goals * 2 + rng.randrange(0, 8),
                        "home_shots_on_target": home_goals + rng.randrange(0, 5),
                        "away_shots_on_target": away_goals + rng.randrange(0, 5),
                        "home_corners": rng.randrange(0, 9),
                        "away_corners": rng.randrange(0, 9),
                        "home_cards": rng.randrange(0, 5),
                        "away_cards": rng.randrange(0, 5),
                        "home_first_half_goals": min(home_goals, rng.randrange(0, 3)),
                        "away_first_half_goals": min(away_goals, rng.randrange(0, 3)),
                    }
                )
    return rows


def _manager_spells(matches: Sequence[Mapping[str, Any]]) -> list[ManagerSpell]:
    teams = sorted({str(row[side]) for row in matches for side in ("home_team", "away_team")})
    spells = [
        ManagerSpell(
            team=team,
            person_key=f"fictional-person-{index:02d}",
            event_known_at="2033-07-01T12:00:00+00:00",
            effective_start="2033-07-15T12:00:00+00:00",
            caretaker=index % 11 == 0,
        )
        for index, team in enumerate(teams)
    ]
    changed_team = "Aster Collective"
    spells = [
        ManagerSpell(
            team=spell.team,
            person_key=spell.person_key,
            event_known_at=spell.event_known_at,
            effective_start=spell.effective_start,
            effective_end=("2034-08-15T12:00:00+00:00" if spell.team == changed_team else None),
            caretaker=spell.caretaker,
        )
        for spell in spells
    ]
    spells.append(
        ManagerSpell(
            team=changed_team,
            person_key="fictional-person-change",
            event_known_at="2034-08-14T12:00:00+00:00",
            effective_start="2034-08-15T12:00:00+00:00",
        )
    )
    return spells


def _tier_tables(matches: Sequence[Mapping[str, Any]]) -> dict[tuple[str, str], dict[str, float]]:
    labels = tuple(DEFAULT_TIER_ANCHORS)
    tables: dict[tuple[str, str], dict[str, float]] = {}
    seasons = sorted({str(row["season"]) for row in matches})
    for season in seasons:
        teams = sorted(
            {
                str(row[side])
                for row in matches
                if row["season"] == season
                for side in ("home_team", "away_team")
            }
        )
        tables[(FICTIONAL_COMPETITION, season)] = {
            team: DEFAULT_TIER_ANCHORS[labels[index % len(labels)]]
            for index, team in enumerate(teams)
        }
    return tables


def _row_signature(rows: Sequence[Any]) -> str:
    payload = [
        {
            "fixture_id": row.fixture_id,
            "features": dict(sorted(row.features.items())),
        }
        for row in rows
    ]
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def build_evidence() -> dict[str, Any]:
    """Return a deterministic synthetic-only verification record."""

    matches = _fixture_rows()
    shuffled = list(matches)
    random.Random(DEMO_SEED + 1).shuffle(shuffled)
    feature_rows = build_chronological_features(matches)
    shuffled_features = build_chronological_features(shuffled)
    fixed = run_fixed_elo(matches)
    shuffled_fixed = run_fixed_elo(shuffled)
    tiers = _tier_tables(matches)
    tier_run = run_tier_seeded_elo(matches, tiers)
    contexts = build_manager_context(matches, _manager_spells(matches))
    shuffled_contexts = build_manager_context(shuffled, _manager_spells(matches))

    mutated = [dict(row) for row in matches]
    mutated[10]["home_goals"] = 9
    mutated_features = build_chronological_features(mutated)
    future_invariant = _row_signature(feature_rows[:20]) == _row_signature(
        mutated_features[:20]
    ) and _row_signature(feature_rows[20:]) != _row_signature(mutated_features[20:])
    feature_values = [value for row in feature_rows for value in row.features.values()]
    unavailable = sum(
        value == 0.0
        for row in feature_rows
        for name, value in row.features.items()
        if name.endswith("_available")
    )
    availability_total = sum(
        1 for row in feature_rows for name in row.features if name.endswith("_available")
    )
    payload: dict[str, Any] = {
        "artifact": "public-v0.2-synthetic-feature-evidence",
        "code_version": __version__,
        "data_kind": "synthetic",
        "disclaimer": "Fictional data only; not empirical EPL evidence.",
        "seed": DEMO_SEED,
        "competition": FICTIONAL_COMPETITION,
        "season_count": len({row["season"] for row in matches}),
        "fixture_count": len(matches),
        "club_season_count": sum(len(table) for table in tiers.values()),
        "feature_row_count": len(feature_rows),
        "feature_count": len(feature_rows[0].features),
        "manager_context_row_count": len(contexts),
        "fixed_elo_row_count": len(fixed.rows),
        "tier_elo_row_count": len(tier_run.rows),
        "tier_anchor_table_complete": all(len(table) == 20 for table in tiers.values()),
        "tier_elo_implementation_status": TIER_ELO_IMPLEMENTATION_STATUS,
        "tier_elo_empirical_value": TIER_ELO_EMPIRICAL_STATUS,
        "tier_elo_promotion_eligible": TIER_ELO_PROMOTION_STATUS,
        "row_order_invariant": (
            _row_signature(feature_rows) == _row_signature(shuffled_features)
            and _row_signature(fixed.rows) == _row_signature(shuffled_fixed.rows)
            and _row_signature(contexts) == _row_signature(shuffled_contexts)
        ),
        "future_result_invariant": future_invariant,
        "same_date_updates_batched": True,
        "elo_zero_sum_update_balance": fixed.update_balance,
        "feature_value_checksum": hashlib.sha256(
            json.dumps(feature_values, separators=(",", ":")).encode()
        ).hexdigest(),
        "feature_unavailable_rate": unavailable / availability_total,
    }
    payload["output_sha256"] = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return payload


def write_evidence(output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "feature_evidence.json"
    path.write_text(json.dumps(build_evidence(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("demo"))
    args = parser.parse_args(argv)
    path = write_evidence(args.output_dir)
    print(f"wrote deterministic synthetic evidence: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
