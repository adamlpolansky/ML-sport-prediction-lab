# EPL Probability Forecasting Lab

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

Independent research project; not affiliated with or endorsed by the Premier League or its clubs.
