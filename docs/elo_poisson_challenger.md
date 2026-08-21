# Elo–Poisson challenger methodology

The exploratory challenger maps a fixed chronological Elo signal to independent-Poisson home and
away goal intensities. It was specified after the shape of the original v1 forecast had been
reviewed; exact-score variety was not optimized and is not a selection metric.

## Fixed mechanics

Elo starts at 1500, uses scale 400, update home advantage 60, K-factor 20, and no goal-margin
multiplier. All matches on one date use a frozen pre-match state and update together afterward.
Teams present in the immediately preceding EPL season retain their end-of-season rating; every
other team re-enters uniformly at 1500. Aliases resolve to canonical team identities.

For pre-match ratings `R_home` and `R_away`, define
`d = (R_home - R_away) / 400`. The goal mapping is
`log(lambda_home) = alpha_home + beta_home * d` and
`log(lambda_away) = alpha_away - beta_away * d`, with both beta coefficients constrained to be
non-negative. Training observations use the frozen exponential age weight
`exp(-0.006 * age_days)`. Intensities must be finite and are bounded to `[0.05, 6]`, with every
clipping event counted.

The joint score distribution is independent Poisson (`rho = 0`) with no H/D/A temperature
calibration. The finite score grid expands deterministically until omitted mass is below `0.001`,
up to the frozen cap of 30 goals. H/D/A, Over 2.5, both-teams-to-score, and exact-score
probabilities all come from that same matrix. Top scorelines use full-precision probability and a
neutral `(home_goals, away_goals)` tie-break.

## Evaluation boundary

The chronological outer test covers ten seasons from 2015/16 through 2024/25, 380 matches per
season. Each mapping fit uses only completed rows strictly before its test season; within the test
season, Elo updates only after earlier completed date batches. Comparison with the retained Dynamic
Dixon–Coles incumbent is restricted to 3,800 identical paired match identities. The 2025/26 season
is reported only as descriptive stress evidence.

The primary metric is joint goal log score. Secondary metrics cover H/D/A log loss and Brier,
classwise reliability, goal MAE and lambda calibration, Over 2.5, both-teams-to-score,
neutral-reentry slices, tail mass, and clipping. Paired uncertainty uses 4,999 match-date bootstrap
replicates with seed `20260821`. The result is a research signal, not an automatic promotion.

Private history, match-level OOS rows, fitted coefficients, and final Elo state are not published.
See the challenger [release notes](../forecasts/2026-27/matchday-01/challengers/elo-poisson-v1/README.md)
and [provenance](../forecasts/2026-27/matchday-01/challengers/elo-poisson-v1/provenance.md).
