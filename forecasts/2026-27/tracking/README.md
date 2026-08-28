# EPL 2026/27 model performance tracker

This append-only tracker shows whether each model family had a public pre-match forecast and, when
results are available, its common H/D/A and goal-expectation metrics.

| MW | Model family | Forecast | Results | Scored | Log loss ↓ | Brier ↓ | Accuracy ↑ | Goal MAE ↓ |
| ---: | --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | Dynamic Dixon–Coles | `published_pre_match` | `scored` | 10 | 0.9497 | **0.5583** | **60%** | **0.890** |
| 1 | Elo–Poisson | `published_pre_match` | `scored` | 10 | **0.9475** | 0.5615 | 50% | 0.926 |
| 2 | Dynamic Dixon–Coles | `not_released` | `not_applicable` | 0 | — | — | — | — |
| 2 | Elo–Poisson post-MW1 refit | `published_pre_match` | `pending` | 0/10 | — | — | — | — |

The Dynamic Dixon–Coles MW2 row stays explicitly `not_released`; no forecast is reconstructed after
kickoff. The Elo–Poisson row will be scored only after the full matchweek is complete. Empty metrics
in [CSV](model_performance.csv) and `null` metrics in [JSON](model_performance.json) represent these
known unavailable states, not zeros.

The completed Matchweek 1 fixture-level evidence and metric definitions are in the
[results pack](../matchday-01/results/README.md). Ten fixtures are far too few for model promotion,
betting, or profitability conclusions.
