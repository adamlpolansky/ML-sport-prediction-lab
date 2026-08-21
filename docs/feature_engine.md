# Chronological feature contract

The v0.2 engine accepts completed, timestamped fixture mappings and returns immutable rows whose
identifiers are separate from the numerical `features` mapping. Input is sorted deterministically.
Every UTC calendar date forms a frozen batch: all pre-match rows are emitted before any result from
that date updates form, table, schedule, statistics, or Elo state.

Required fixture fields are `fixture_id`, timezone-aware `event_time`, `competition`, `season`,
`home_team`, `away_team`, `home_goals`, and `away_goals`. Optional numeric statistics are shots,
shots on target, corners, cards, and first-half goals for both sides. Missing optional history emits
zero plus an explicit availability flag; it is never silently forward-filled.

The fixed Elo defaults are scale 400, home advantage 60, K 20, base 1500, and no goal-margin term.
Tier-seeded Elo accepts a complete caller-provided 20-club numeric anchor table for each season,
centers it on 1500, blends returning clubs 75/25 with their previous end rating, and recenters the
final starts. Incomplete tables fail closed. No real tier assignment ships in the repository.

Manager context is a separate generic transform. Each spell carries an opaque person key,
`event_known_at`, `effective_start`, optional `effective_end`, and caretaker flag. Only tenure,
prior matches in charge, 1/3/5-match transition flags, caretaker status, and availability are
model-eligible. Same-day ambiguity and overlapping eligible spells fail closed.
