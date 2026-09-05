# Matchweek 3 — remaining seven forecasts (retrospective, unscored)

Generated at **2026-09-05T15:26:08Z**, after these fixtures had started.
These are **retrospective frozen-post-MW2 estimates**, not forecasts published before kickoff.

The original Elo state through 31 August and the unchanged post-MW1 Poisson mapping are reused.
No MW3 result or live match information was read or used. No Elo update, model refit, outcome
evaluation, accuracy calculation or goal-error calculation was performed for this supplement.
The existing three prospective forecasts and all result-tracker files remain unchanged.

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

Times are Europe/Prague. O2.5 and BTTS show the YES probability; the parenthesized pick is
Over/Under or Yes/No according to the more probable side. Exactly 50% means no pick.
Goals H–A are model-implied expectations, not post-match shot-based xG.

## Scope and provenance

- [Seven forecast rows: CSV](forecast.csv) · [JSON](forecast.json)
- [Frozen-state and no-evaluation manifest](manifest.json)
- [Original three prospective forecasts](../README.md)

The selected information cutoff is **2026-09-01T11:23:47Z**, the pinned fixture
source revision time. It describes the information used, not when this calculation was created.
The Elo results end on 31 August, and the mapping training data end on 24 August.
The actual generation timestamp above is not backdated.

The original source is the pinned
[OpenFootball ledger](https://github.com/openfootball/england/blob/0690446f794fde748ea4b994244def699c6a65b2/2026-27/1-premierleague.txt).
The local frozen audit commitment is `e448da3b0987a0adbbcba16220ac1ec8a469d9e60c425a54b89a0cbd4c48cf5c`.
Replaying that state reproduces the three original MW3 forecasts exactly.
Full Elo ratings and fitted coefficients remain local.

The original release plus this supplement covers **10 unique fixtures: 3 prospective + 7
retrospective**. The supplement is deliberately kept outside the result tracker and has status
`not_evaluated_by_user_request`. No MW3 performance claim is made.

Validate the published bytes, identities, probabilities and tables (not match outcomes) with
`python -m epl_probability_lab.matchday_three_supplement --root .`.

Fixture facts remain OpenFootball CC0-1.0. Derived forecasts are CC BY 4.0, attributed to
Adam Luboš Polanský. Original code and documentation are MIT licensed.
