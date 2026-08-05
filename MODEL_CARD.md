# Model card

## Model overview

The public demo estimates smoothed fictional-team attack and defence rates from a chronological
synthetic training window, forms an independent Poisson score distribution, and derives coherent
home/draw/away probabilities. It is intentionally small, auditable, and offline.

## Intended uses

- Learning how goal distributions imply mutually consistent match probabilities.
- Exercising a deterministic, CLI-first forecasting and evaluation pipeline.
- Reviewing calibration, uncertainty, artifact evidence, and leakage controls.

## Prohibited uses

Do not use the synthetic model for betting, financial decisions, player safety, eligibility,
discipline, or any consequential decision. Do not present the demo as evidence of real-world
predictive performance, profitability, ROI, or an edge.

## Public synthetic demo

The demo uses 96 generated fixtures among eight fictional teams. The first 64 rows are the training
window and the last 32 are a chronological holdout. Its artifact contains only rates learned from
fictional synthetic teams. It has no real team coefficients or provider identifiers.

## Private historical scope

Separate private work used 5,700 development matches and 380 OOS lockbox matches. Only aggregate
metrics are published. No source rows, per-match predictions, provider mappings, real-data model
artifacts, or evidence hashes are distributed.

## Uncertainty and calibration

The reliability plot compares predicted probabilities with empirical synthetic frequencies across
fixed bins and includes the ideal-calibration reference. With only 32 holdout matches, calibration
estimates are noisy and illustrative. Tail probability beyond the displayed score grid is
renormalized, and this approximation is recorded in the artifact.

## Leakage controls

- Training and evaluation use a chronological split, never a random final split.
- Holdout outcomes do not enter parameter fitting.
- The example prediction is created from the frozen synthetic artifact.
- No odds, provider snapshot, or current-match result is used as a feature.

## Missing context and failure modes

The model omits team strength, injuries, line-ups, travel, promotions, tactics, schedule congestion,
market information, and regime changes. Independent Poisson goals may understate score dependence.
Synthetic fitted rates do not represent real teams. Sparse calibration bins may be unstable. Data from a real
competition can drift and can fail provider coverage or identity checks.

## Historical non-promotion decision

The private candidate-minus-historical log-loss estimate was -0.035993 with a precommitted interval
of [-0.072155, 0.001383]. Because the interval crossed zero, the candidate was not promoted and the
historical-frequency fallback was retained.

> Synthetic demonstration — not evidence of real-world predictive performance.
