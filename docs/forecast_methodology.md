# Forecast methodology

## Frozen model path

The release uses the retained Dynamic Dixon–Coles incumbent: a time-decayed attack/defence goal
model with a low-score Dixon–Coles adjustment and a frozen calibration layer. It loads a previously
fitted, externally trust-checked artifact; it does not select parameters, recalibrate, or refit for
this release. The v0.2 chronological, Elo, tier, and manager feature candidate was not promoted and
does not enter these predictions.

The pending-fixture inference input contains only the home and away canonical team keys and
training-derived promoted/unseen flags. It contains no future goals and applies no state update for
an unplayed fixture. Manager, referee, injury, lineup, tier, market, odds, and news inputs are
disabled. No Matchweek 1 result or post-cutoff information enters the artifact, state, calibration,
or manual adjustment.

## Cold start

Coventry City, Hull City, and Ipswich Town were absent from the EPL 2025/26 training-season
membership. The frozen incumbent therefore applies its precommitted neutral attack/defence prior to
all three through the promoted flag. This policy is training-only, uniform, and tested; no club was
hand-tuned for this panel.

## Probability output

The model emits finite positive home and away goal rates. A finite score grid expands until the
omitted independent-Poisson tail is below `0.001`, then the frozen low-score adjustment and H/D/A
calibration are applied. Machine H/D/A probabilities are stored at full precision and must sum to
one within `1e-12`. Expected goals are the calibrated model rates. The modal score and its
probability are taken from the score matrix; `tail_mass` records the residual outside its finite
grid.

The public validator checks the fixture set, schema, identities, time ordering, numeric ranges,
normalization, residual-mass bound, and exact JSON/CSV/README agreement. The modal-score/matrix
agreement was checked during private generation because the fitted matrix parameters are not
distributed.

## Interpretation

These are uncertain pre-match probabilities, not realized results, recommendations, stakes, odds,
profit estimates, or evidence of a betting edge. The highest H/D/A column merely identifies the
largest of three model probabilities.
