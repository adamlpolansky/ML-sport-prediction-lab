# EPL Probability Forecasting Lab

## Latest: Matchweek 3 and results through Matchweek 2

The [Matchweek 3 release](forecasts/2026-27/matchday-03/challengers/elo-poisson-v1-post-mw2/README.md)
uses Elo updated after all ten MW2 results and the frozen post-MW1 Poisson mapping.
Three fixtures still have prospective forecasts; seven had passed kickoff at generation.

<!-- matchday3-table:start -->
| Kickoff (Prague) | Fixture | Home | Draw | Away | H/D/A pick | Goals H–A | O2.5 | BTTS | Modal |
| --- | --- | ---: | ---: | ---: | --- | ---: | ---: | ---: | --- |
| 2026-09-05 18:30 | Hull City — Aston Villa | 30.8% | 25.3% | 43.9% | Away | 1.22–1.51 | 51.4% (Over) | 55.0% (Yes) | 1–1 (12.0%) |
| 2026-09-06 15:00 | Everton — Manchester United | 37.4% | 25.8% | 36.9% | Home | 1.36–1.35 | 50.9% (Over) | 55.1% (Yes) | 1–1 (12.2%) |
| 2026-09-06 17:30 | Arsenal — Chelsea | 62.9% | 20.9% | 16.2% | Home | 2.00–0.90 | 55.4% (Over) | 51.4% (Yes) | 1–0 (11.0%) |
<!-- matchday3-table:end -->

### Remaining seven — retrospective estimates, not evaluated

The [seven-row supplement](forecasts/2026-27/matchday-03/challengers/elo-poisson-v1-post-mw2/retrospective/README.md)
uses exactly the same frozen post-MW2 state. It was generated after kickoff, is explicitly
retrospective, and has **not been evaluated**. No MW3 results or live scores were used.
Together the releases cover all ten fixtures; the original three prospective forecasts stay unchanged.

<!-- mw3-retrospective-table:start -->
| Kickoff (Prague) | Fixture | Home | Draw | Away | H/D/A pick | Goals H–A | O2.5 | BTTS | Modal |
| --- | --- | ---: | ---: | ---: | --- | ---: | ---: | ---: | --- |
| 2026-09-04 21:00 | Ipswich Town — Liverpool | 26.6% | 24.6% | 48.8% | Away | 1.14–1.63 | 52.2% (Over) | 54.6% (Yes) | 1–1 (11.7%) |
| 2026-09-05 13:30 | Newcastle United — AFC Bournemouth | 42.6% | 25.5% | 31.8% | Home | 1.48–1.24 | 51.0% (Over) | 54.8% (Yes) | 1–1 (12.1%) |
| 2026-09-05 16:00 | Nottingham Forest — Tottenham Hotspur | 52.2% | 24.0% | 23.8% | Home | 1.70–1.07 | 52.3% (Over) | 53.7% (Yes) | 1–1 (11.4%) |
| 2026-09-05 16:00 | Manchester City — Coventry City | 76.8% | 14.9% | 8.3% | Home | 2.52–0.71 | 62.6% (Over) | 46.7% (No) | 2–0 (12.6%) |
| 2026-09-05 16:00 | Brighton & Hove Albion — Leeds United | 50.4% | 24.4% | 25.2% | Home | 1.66–1.10 | 52.0% (Over) | 53.9% (Yes) | 1–1 (11.6%) |
| 2026-09-05 16:00 | Brentford — Sunderland | 50.5% | 24.4% | 25.1% | Home | 1.66–1.10 | 52.0% (Over) | 53.9% (Yes) | 1–1 (11.6%) |
| 2026-09-05 16:00 | Fulham — Crystal Palace | 46.5% | 25.1% | 28.4% | Home | 1.56–1.17 | 51.4% (Over) | 54.5% (Yes) | 1–1 (11.9%) |
<!-- mw3-retrospective-table:end -->

The result statistics below still cover MW1–2 only. No MW3 scoring is added to the tracker.

Times are Europe/Prague. The H/D/A pick is the highest-probability outcome in every match,
including a draw when it ranks first; there is no confidence threshold for this metric.
For **Over/Under 2.5** and **BTTS Yes/No** separately, pick the more probable side:
above 50% means Over or Yes; below 50% means Under or No. A correct Under or No counts as a win.
Only a probability of exactly 50% means no bet, not a losing bet.
The [MW1–2 tracker](forecasts/2026-27/tracking/README.md) has every selection and denominator:

| Model | Period | H/D/A correct / all forecasts | Over/Under 2.5 correct / picks | BTTS Yes/No correct / picks | Goal MAE per team |
| --- | --- | ---: | ---: | ---: | ---: |
| Dynamic Dixon–Coles | MW1 | 6 / 10 (60%) | 6 / 10 (60%) | 5 / 10 (50%) | 0.890 goals |
| Elo–Poisson | MW1 | 5 / 10 (50%) | 7 / 10 (70%) | 5 / 10 (50%) | 0.926 goals |
| Elo–Poisson | MW2 | 5 / 10 (50%) | 4 / 10 (40%) | 6 / 10 (60%) | 1.031 goals |
| Elo–Poisson | MW1–2 combined | 10 / 20 (50%) | 11 / 20 (55%) | 11 / 20 (55%) | 0.979 goals |

All ten matches were predicted in each available model-round. None of the historical goal-market
probabilities equals 50%, so both goal markets also have ten picks per available model-round.
Goal MAE measures the average absolute difference between model-implied expected goals and
actual goals for each team. Across both rounds, Elo's average miss was **0.979 goals per team**;
actual scoring exceeded its expectation by **0.166 goals per team** on average.
These are forecast-goal deviations, not comparisons with observed post-match shot-based xG.

Dixon–Coles had no published MW2 forecast, so its available result is MW1-only. Goal markets
are retrospective derivations from original frozen forecasts: published lambdas for Elo and an
exact verified replay of the original DC artifact. The rule was requested on 5 September and
was not pre-registered. Profit and ROI require actual accepted odds and stakes; these are only
descriptive hit rates on small, partly different samples.
See the [MW2 result CSV pack](forecasts/2026-27/matchday-02/results/README.md) and
[cumulative CSV](forecasts/2026-27/tracking/cumulative_performance.csv).

[![synthetic quality gates](https://github.com/adamlpolansky/ML-sport-prediction-lab/actions/workflows/ci.yml/badge.svg)](https://github.com/adamlpolansky/ML-sport-prediction-lab/actions/workflows/ci.yml)

Leakage-safe pre-match football forecasting components with chronological features, fixed and
caller-seeded Elo, and explicit point-in-time manager context. The public demos are deterministic,
fictional, credential-free, and fully offline. Same-date fixtures always use one frozen pre-match
state, so caller row order cannot create within-day leakage.

```bash
python -m pip install -e ".[dev]" && python -m epl_probability_lab.feature_demo --output-dir demo
```

See the committed [synthetic feature evidence](demo/feature_evidence.json). It demonstrates software
invariants only and is not evidence of real-world forecasting performance.

| Component | Public status | Claim boundary |
| --- | --- | --- |
| Independent-Poisson demo | Available | Synthetic demonstration |
| Chronological feature engine | Implemented and tested | No real rows redistributed |
| Fixed internal Elo | Implemented and tested | Synthetic invariants only |
| Manager context | Generic adapter implemented | No public coverage/performance claim |
| Referee context | Not included | No reliable point-in-time publication timestamps |
| Tier-seeded Elo | Implemented and synthetic-only | Empirical value not evaluated |
| Private feature candidate | Not promoted | Dynamic DC incumbent retained |

The feature-engineering candidate was not promoted; the dynamic Dixon–Coles incumbent was retained.
Tier-seeded Elo is implemented and synthetically verified but was not empirically evaluated and is
not promotion eligible.

## What v0.2 provides

- Pure chronological form, venue, rest, congestion, table, match-stat, scoring-phase, ratio,
  cold-start, and availability features.
- Fixed Elo defaults: rating scale 400, home advantage 60, K 20, no goal-margin term, and batched
  same-date updates.
- Generic tier-seeded Elo using complete caller-supplied 20-club anchors, centering, continuity, and
  fail-closed validation. No real club-season tier assignments are included.
- Generic manager tenure, matches-in-charge, 1/3/5-match transition, caretaker, and availability
  features from caller-supplied event timestamps. Person identity is never model eligible.
- Invariance tests and deterministic fictional multi-season evidence.

Referee context is excluded from the primary implementation because historical assignment
publication timestamps are unavailable. Train-only feature selection is also excluded from this
release. No downloader, data client, source cache, or real fitted artifact is included.

## Reproduce locally

Python 3.12 is the release validation target.

```bash
python -m venv .venv
python -m pip install -e ".[dev]"
python -m pip check
python -m pytest -q
python -m ruff check .
python -m ruff format --check .
python -m epl_probability_lab.demo --output-dir demo-v01
python -m epl_probability_lab.feature_demo --output-dir demo-v02
python scripts/validate_forecast_release.py --root .
python -m epl_probability_lab.publication --root .
```

The original independent-Poisson synthetic demo remains available through
`python -m epl_probability_lab.demo`. Both demos run without network access. Offline execution does
not by itself promise identical bytes across operating systems or plotting stacks; byte-level
determinism is claimed only within a supported platform and dependency set.

Read [the feature contract](docs/feature_engine.md),
[publication scope](docs/publication_scope.md), [model card](MODEL_CARD.md), and
[data provenance and licences](docs/data_provenance_and_licenses.md) before adapting the code.

## Licence

Original code and documentation are MIT licensed under the copyright of Adam Luboš Polanský. The
licence grants no rights to third-party datasets, services, logos, marks, or other provider content.

## EPL 2026/27 Matchweek 1 forecast

> Timestamped model forecast—not a result or betting advice. Generated
> `2026-08-21T12:06:03Z` from information available by `2026-08-21T12:04:19Z` using the retained
> Dynamic Dixon–Coles incumbent.

<!-- forecast-table:start -->
| Kickoff (Europe/London) | Fixture | Home | Draw | Away | Highest H/D/A | xG (H–A) | Modal score |
| --- | --- | ---: | ---: | ---: | --- | ---: | ---: |
| 2026-08-21 20:00 | Arsenal — Coventry City | 66.3% | 22.0% | 11.7% | Home | 1.99–0.63 | 2–0 (14.4%) |
| 2026-08-22 12:30 | Hull City — Manchester United | 26.5% | 25.5% | 48.0% | Away | 1.20–1.74 | 1–1 (11.6%) |
| 2026-08-22 15:00 | Everton — Crystal Palace | 44.8% | 28.4% | 26.8% | Home | 1.43–1.02 | 1–1 (13.2%) |
| 2026-08-22 15:00 | Ipswich Town — Sunderland | 39.1% | 29.1% | 31.8% | Home | 1.29–1.13 | 1–1 (13.6%) |
| 2026-08-22 15:00 | Nottingham Forest — Leeds United | 45.4% | 27.8% | 26.9% | Home | 1.49–1.06 | 1–1 (12.9%) |
| 2026-08-22 17:30 | Brentford — Tottenham Hotspur | 50.5% | 25.8% | 23.7% | Home | 1.72–1.06 | 1–1 (11.9%) |
| 2026-08-23 14:00 | Brighton & Hove Albion — Aston Villa | 40.0% | 27.4% | 32.5% | Home | 1.45–1.26 | 1–1 (12.8%) |
| 2026-08-23 14:00 | Manchester City — AFC Bournemouth | 55.8% | 24.6% | 19.6% | Home | 1.84–0.94 | 1–1 (11.3%) |
| 2026-08-23 16:30 | Newcastle United — Liverpool | 36.8% | 24.9% | 38.3% | Away | 1.61–1.65 | 1–1 (10.7%) |
| 2026-08-24 20:00 | Fulham — Chelsea | 38.7% | 29.0% | 32.3% | Home | 1.30–1.15 | 1–1 (13.6%) |
<!-- forecast-table:end -->

Download the full-precision [JSON](forecasts/2026-27/matchday-01/forecast.json) or
[CSV](forecasts/2026-27/matchday-01/forecast.csv), and read the
[forecast notes](forecasts/2026-27/matchday-01/README.md),
[methodology](docs/forecast_methodology.md), and [provenance](docs/forecast_provenance.md).
Fixture facts are revision-pinned OpenFootball CC0 data; the derived forecast dataset is CC BY 4.0
with attribution to Adam Luboš Polanský. The private fitted artifact and historical rows are not
distributed. The v0.2 feature candidate was not promoted and did not drive this forecast.

## Exploratory Elo–Poisson challenger

An append-only [Elo–Poisson challenger pack](forecasts/2026-27/matchday-01/challengers/elo-poisson-v1/README.md)
now sits beside the immutable Dynamic Dixon–Coles v1 forecast. It was designed after reviewing the
shape of v1, did not optimize exact-score diversity, and is not automatically promoted. Its frozen
paired OOS evidence is favorable enough for the label `ELO_CHALLENGER_VALID_RESEARCH_SIGNAL`, while
v1 remains the incumbent release. Private history, match-level OOS rows, fitted coefficients, and
Elo state are not distributed.

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

The published lambdas reproduce every listed probability through a validated independent-Poisson
matrix. This remains research output, not betting advice or a profitability claim.

## EPL 2026/27 Matchweek 2 Elo–Poisson update

The [Matchweek 2 update pack](forecasts/2026-27/matchday-02/challengers/elo-poisson-v1-post-mw1/README.md)
uses all ten completed Matchweek 1 results to update fixed Elo and refit the unchanged
independent-Poisson mapping. It contains ten timestamped pre-match forecasts generated before the
first Matchweek 2 kickoff. This is an exploratory post-matchweek update, not a promoted champion,
and no claim is made that a ten-match refit improves predictive performance.

<!-- matchday2-table:start -->
| Kickoff (London) | Fixture | H | D | A | Pick | λ H–A | O2.5 | BTTS | Modal |
| --- | --- | ---: | ---: | ---: | --- | ---: | ---: | ---: | ---: |
| 2026-08-28 20:00 | Crystal Palace — Manchester City | 25.5% | 24.3% | 50.1% | Away | 1.11–1.66 | 52.5% | 54.5% | 1–1 (11.5%) |
| 2026-08-29 12:30 | Liverpool — Nottingham Forest | 57.5% | 22.6% | 19.9% | Home | 1.84–0.98 | 53.7% | 52.7% | 1–0 (10.9%) |
| 2026-08-29 15:00 | AFC Bournemouth — Everton | 51.4% | 24.2% | 24.4% | Home | 1.68–1.08 | 52.2% | 53.8% | 1–1 (11.5%) |
| 2026-08-29 15:00 | Coventry City — Hull City | 44.0% | 25.4% | 30.6% | Home | 1.51–1.21 | 51.1% | 54.7% | 1–1 (12.0%) |
| 2026-08-29 17:30 | Tottenham Hotspur — Newcastle United | 37.3% | 25.8% | 36.9% | Home | 1.36–1.35 | 50.9% | 55.1% | 1–1 (12.2%) |
| 2026-08-30 14:00 | Chelsea — Brighton & Hove Albion | 45.5% | 25.2% | 29.3% | Home | 1.54–1.19 | 51.3% | 54.6% | 1–1 (12.0%) |
| 2026-08-30 14:00 | Leeds United — Brentford | 41.3% | 25.6% | 33.1% | Home | 1.45–1.27 | 51.0% | 54.9% | 1–1 (12.2%) |
| 2026-08-30 14:00 | Sunderland — Fulham | 43.5% | 25.4% | 31.1% | Home | 1.49–1.22 | 51.1% | 54.8% | 1–1 (12.1%) |
| 2026-08-30 16:30 | Manchester United — Ipswich Town | 64.0% | 20.5% | 15.5% | Home | 2.04–0.89 | 55.9% | 51.1% | 2–0 (11.2%) |
| 2026-08-31 20:00 | Aston Villa — Arsenal | 32.3% | 25.5% | 42.2% | Away | 1.25–1.47 | 51.2% | 55.0% | 1–1 (12.1%) |
<!-- matchday2-table:end -->

O2.5 and BTTS are exact independent-Poisson derivatives of the published lambdas, included for
model inspection rather than betting advice.

Full-precision [JSON](forecasts/2026-27/matchday-02/challengers/elo-poisson-v1-post-mw1/forecast.json),
[CSV](forecasts/2026-27/matchday-02/challengers/elo-poisson-v1-post-mw1/forecast.csv), and
[provenance](forecasts/2026-27/matchday-02/challengers/elo-poisson-v1-post-mw1/provenance.md) are
available. Private coefficients, Elo state, and training rows remain undistributed.

## Results tracker

Matchweek 1 is now closed in a reproducible [results pack](forecasts/2026-27/matchday-01/results/README.md)
with fixture CSV, per-match model scores, aggregate CSV, JSON, and pinned CC0 provenance. The
append-only [season tracker](forecasts/2026-27/tracking/README.md) compares both model families using
common H/D/A log loss, Brier score, top-1 accuracy, and goal MAE. Missing or pending forecasts stay
explicitly unavailable and are never encoded as zero.

Independent research project; not affiliated with or endorsed by the Premier League or its clubs.
