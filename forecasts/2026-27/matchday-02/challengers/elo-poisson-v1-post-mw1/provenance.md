# Matchweek 2 update provenance

## Fixture and result reconciliation

- Repository: `openfootball/england`
- Commit: `836b1947fa4089c86b6064f821eee7de926a7a3f`
- File: `2026-27/1-premierleague.txt`
- Git blob: `fffa0b4626672b9e1e7aaea60554bc0ae8b1a363`
- Download SHA-256: `0c552804d8b93cf6e0fb27ea46dc2af67829c815f8445b84c6eebf94c4bedbc0`
- Pinned source: https://github.com/openfootball/england/blob/836b1947fa4089c86b6064f821eee7de926a7a3f/2026-27/1-premierleague.txt
- Licence: CC0-1.0

The initial manual result and schedule check was independently reconciled to this exact CC0
revision before publication. The pinned file contains all ten completed Matchweek 1 scores and all
ten Matchweek 2 fixture identities and kickoff times used here.

## Model update boundary

- Model: `fixed-elo-neutral-reentry-poisson-v1-post-mw1-refit`
- Role: `exploratory_post_matchweek_update`
- Training rows before update: 6,080
- Training rows after update: 6,090
- Training maximum before update: `2026-05-24`
- Training maximum after update: `2026-08-24`
- Elo: base 1500, K=20, rating scale 400, 60-point home update advantage, no goal-margin term
- Poisson: fixed log-linear Elo-gap mapping, decay 0.006/day, independent score distribution
- Private generation commitment SHA-256: `d96ee65cad8ed945af7a6a25522d6897827f41f2549647744b1fc542b4bc821c`
- Promotion performed: false

No hyperparameter, feature-family, calibration, or exact-score-diversity search was performed after
Matchweek 1. The coefficients and complete Elo state remain private. The public lambdas are enough
to reconstruct each released probability and top scoreline exactly.

## Public artifacts

- Information cutoff: `2026-08-28T16:28:10Z`
- Generated at: `2026-08-28T16:28:10Z`
- Coverage: 10 of 10, all generated before kickoff
- Forecast JSON SHA-256: `058751f13dcb68865c5b9599563839379c5151ace5ccf4c307a69ca4b687b5cb`
- Forecast CSV SHA-256: `f15747ecee72099fa9437fc1d78369c2b698a2079bdfe8181bec000af1781735`
- Coverage SHA-256: `3d268e29596fc7abd0b7e1534bb98a392bed5b066f28ca8251911dd176929dd2`

The derived forecast dataset is licensed by Adam Luboš Polanský under CC BY 4.0. Original code and
documentation remain MIT licensed. No private training rows or provider payloads are distributed.
