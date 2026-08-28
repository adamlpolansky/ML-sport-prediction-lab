# Matchweek 1 result and scorecard provenance

## Result source

- Repository: `openfootball/england`
- Commit: `836b1947fa4089c86b6064f821eee7de926a7a3f`
- Path: `2026-27/1-premierleague.txt`
- Git blob: `fffa0b4626672b9e1e7aaea60554bc0ae8b1a363`
- Download SHA-256: `0c552804d8b93cf6e0fb27ea46dc2af67829c815f8445b84c6eebf94c4bedbc0`
- Licence: CC0-1.0
- Result data through: `2026-08-24`

The pinned source is [OpenFootball's EPL 2026/27 ledger](https://github.com/openfootball/england/blob/836b1947fa4089c86b6064f821eee7de926a7a3f/2026-27/1-premierleague.txt).
Only the ten Matchweek 1 fixture identities and final scores are redistributed here.

## Forecast inputs

The calculations consume the committed, timestamped pre-match artifacts without changing them:

- `../forecast.json` — Dynamic Dixon–Coles incumbent
- `../challengers/elo-poisson-v1/forecast.json` — Elo–Poisson challenger

For each fixture and model, H/D/A log loss is `-ln(p_actual)`. Multiclass Brier score is
`(p_H-y_H)^2 + (p_D-y_D)^2 + (p_A-y_A)^2`. Top-1 accuracy compares the largest published H/D/A
probability with the actual outcome. Goal MAE is the mean of the absolute home- and away-goal
expectation errors. Aggregates are unweighted means across the ten fixtures.

`python -m epl_probability_lab.results_tracker --root .` independently regenerates every machine
artifact from the two immutable MW1 forecasts, the published MW2 forecast status, and the pinned
result constants before comparing bytes.
