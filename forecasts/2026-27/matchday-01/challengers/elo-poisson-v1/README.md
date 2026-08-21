# Exploratory Elo–Poisson challenger

> Timestamped model forecast—not a result, betting advice, or evidence of profit.

All ten fixtures were still unstarted when this challenger was generated at
`2026-08-21T14:01:17Z` from information available by `2026-08-21T14:01:16Z`. Every row is marked
`prospective_pre_match_challenger`. The model was designed after reviewing the shape of the
original Dynamic Dixon–Coles v1 forecast, so it is an exploratory challenger rather than a
preregistered champion. Exact-score diversity was neither a training nor a selection objective.

The frozen chronological OOS comparison produced the decision label
`ELO_CHALLENGER_VALID_RESEARCH_SIGNAL`: the challenger-minus-incumbent joint log-score delta was
`-0.020033` on 3,800 paired matches, with a match-date bootstrap 95% interval of
`[-0.030655, -0.009289]` and improvement in 7 of 10 seasons. Lower is better. This does not
automatically promote the challenger, and the original v1 forecast remains the incumbent release.
The full sanitized aggregate evidence is in [evaluation_summary.json](evaluation_summary.json).

Private history, per-match OOS evidence, fitted coefficients, and Elo team state are not
distributed. The aggregate evidence and the post-lambda probability derivation are auditable:
the public validator reconstructs the finite independent-Poisson matrix from each published pair
of goal intensities and checks H/D/A, top-three scorelines, and omitted tail mass.

## Forecast

<!-- challenger-table:start -->
| Kickoff (Europe/London) | Fixture | Home | Draw | Away | Expected goals λ (H–A) | Top 3 scorelines | Model | Status |
| --- | --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| 2026-08-21 20:00 | Arsenal — Coventry City | 75.9% | 15.2% | 8.9% | 2.51–0.74 | 2–0 (12.2%); 3–0 (10.2%); 1–0 (9.7%) | `fixed-elo-neutral-reentry-poisson-v1` | `prospective_pre_match_challenger` |
| 2026-08-22 12:30 | Hull City — Manchester United | 24.0% | 24.2% | 51.8% | 1.06–1.68 | 1–1 (11.5%); 0–1 (10.8%); 1–2 (9.7%) | `fixed-elo-neutral-reentry-poisson-v1` | `prospective_pre_match_challenger` |
| 2026-08-22 15:00 | Everton — Crystal Palace | 43.9% | 25.5% | 30.6% | 1.50–1.21 | 1–1 (12.1%); 1–0 (10.0%); 2–1 (9.1%) | `fixed-elo-neutral-reentry-poisson-v1` | `prospective_pre_match_challenger` |
| 2026-08-22 15:00 | Ipswich Town — Sunderland | 34.1% | 25.8% | 40.1% | 1.28–1.41 | 1–1 (12.3%); 0–1 (9.6%); 1–0 (8.7%) | `fixed-elo-neutral-reentry-poisson-v1` | `prospective_pre_match_challenger` |
| 2026-08-22 15:00 | Nottingham Forest — Leeds United | 46.0% | 25.2% | 28.8% | 1.55–1.17 | 1–1 (12.0%); 1–0 (10.2%); 2–1 (9.3%) | `fixed-elo-neutral-reentry-poisson-v1` | `prospective_pre_match_challenger` |
| 2026-08-22 17:30 | Brentford — Tottenham Hotspur | 52.2% | 24.0% | 23.8% | 1.70–1.07 | 1–1 (11.4%); 1–0 (10.6%); 2–1 (9.7%) | `fixed-elo-neutral-reentry-poisson-v1` | `prospective_pre_match_challenger` |
| 2026-08-23 14:00 | Brighton & Hove Albion — Aston Villa | 38.0% | 25.9% | 36.1% | 1.36–1.32 | 1–1 (12.3%); 1–0 (9.3%); 0–1 (9.0%) | `fixed-elo-neutral-reentry-poisson-v1` | `prospective_pre_match_challenger` |
| 2026-08-23 14:00 | Manchester City — AFC Bournemouth | 56.8% | 22.8% | 20.4% | 1.83–1.00 | 1–0 (10.8%); 1–1 (10.8%); 2–0 (9.9%) | `fixed-elo-neutral-reentry-poisson-v1` | `prospective_pre_match_challenger` |
| 2026-08-23 16:30 | Newcastle United — Liverpool | 34.8% | 25.9% | 39.3% | 1.29–1.39 | 1–1 (12.3%); 0–1 (9.5%); 1–0 (8.8%) | `fixed-elo-neutral-reentry-poisson-v1` | `prospective_pre_match_challenger` |
| 2026-08-24 20:00 | Fulham — Chelsea | 40.8% | 25.8% | 33.4% | 1.43–1.27 | 1–1 (12.2%); 1–0 (9.7%); 2–1 (8.7%) | `fixed-elo-neutral-reentry-poisson-v1` | `prospective_pre_match_challenger` |
<!-- challenger-table:end -->

## Side-by-side with the immutable v1 forecast

These are descriptive differences between two timestamped public forecasts, not evidence that one
individual fixture prediction is better.

| Fixture | Dynamic DC v1 H/D/A | Elo–Poisson H/D/A | Dynamic DC λ (H–A) | Elo–Poisson λ (H–A) |
| --- | --- | --- | ---: | ---: |
| Arsenal — Coventry City | 66.3% / 22.0% / 11.7% | 75.9% / 15.2% / 8.9% | 1.99–0.63 | 2.51–0.74 |
| Hull City — Manchester United | 26.5% / 25.5% / 48.0% | 24.0% / 24.2% / 51.8% | 1.20–1.74 | 1.06–1.68 |
| Everton — Crystal Palace | 44.8% / 28.4% / 26.8% | 43.9% / 25.5% / 30.6% | 1.43–1.02 | 1.50–1.21 |
| Ipswich Town — Sunderland | 39.1% / 29.1% / 31.8% | 34.1% / 25.8% / 40.1% | 1.29–1.13 | 1.28–1.41 |
| Nottingham Forest — Leeds United | 45.4% / 27.8% / 26.9% | 46.0% / 25.2% / 28.8% | 1.49–1.06 | 1.55–1.17 |
| Brentford — Tottenham Hotspur | 50.5% / 25.8% / 23.7% | 52.2% / 24.0% / 23.8% | 1.72–1.06 | 1.70–1.07 |
| Brighton & Hove Albion — Aston Villa | 40.0% / 27.4% / 32.5% | 38.0% / 25.9% / 36.1% | 1.45–1.26 | 1.36–1.32 |
| Manchester City — AFC Bournemouth | 55.8% / 24.6% / 19.6% | 56.8% / 22.8% / 20.4% | 1.84–0.94 | 1.83–1.00 |
| Newcastle United — Liverpool | 36.8% / 24.9% / 38.3% | 34.8% / 25.9% / 39.3% | 1.61–1.65 | 1.29–1.39 |
| Fulham — Chelsea | 38.7% / 29.0% / 32.3% | 40.8% / 25.8% / 33.4% | 1.30–1.15 | 1.43–1.27 |

See the full-precision [JSON](forecast.json), [CSV](forecast.csv), [coverage](coverage.json),
[methodology](../../../../../docs/elo_poisson_challenger.md), and [provenance](provenance.md).
Fixture facts use the same revision-pinned OpenFootball CC0 ledger as v1. Adam Luboš Polanský
licenses the derived challenger forecast dataset under CC BY 4.0. Original code and documentation
remain MIT licensed.

Independent research project; not affiliated with or endorsed by the Premier League or its clubs.
