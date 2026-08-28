# Matchweek 2 Elo–Poisson update

> Timestamped model forecast—not a result, betting advice, or evidence of profit.

All ten fixtures were unstarted when this forecast was generated at `2026-08-28T16:28:10Z`. Elo was
updated from the ten completed Matchweek 1 results using the frozen K=20, 60-point home-update
advantage, zero-sum, same-date-batch rules. The same independent-Poisson mapping was then refitted
on 6,090 EPL matches: the original 6,080 rows plus Matchweek 1. No model family, decay rate,
lambda bound, score-grid rule, or selection objective was tuned after seeing those results.

This is an `exploratory_post_matchweek_update`, not a promoted champion. The small ten-match update
can move fitted parameters materially and must not be interpreted as evidence that the revised
model is better. The historical-frequency production fallback and immutable Matchweek 1 releases
remain unchanged.

## Forecast

| Kickoff (Europe/London) | Fixture | Home | Draw | Away | λ (H–A) | Top 3 scorelines |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| 2026-08-28 20:00 | Crystal Palace — Manchester City | 25.5% | 24.3% | 50.1% | 1.11–1.66 | 1–1 (11.5%); 0–1 (10.3%); 1–2 (9.6%) |
| 2026-08-29 12:30 | Liverpool — Nottingham Forest | 57.5% | 22.6% | 19.9% | 1.84–0.98 | 1–0 (10.9%); 1–1 (10.7%); 2–0 (10.1%) |
| 2026-08-29 15:00 | AFC Bournemouth — Everton | 51.4% | 24.2% | 24.4% | 1.68–1.08 | 1–1 (11.5%); 1–0 (10.6%); 2–1 (9.7%) |
| 2026-08-29 15:00 | Coventry City — Hull City | 44.0% | 25.4% | 30.6% | 1.51–1.21 | 1–1 (12.0%); 1–0 (9.9%); 2–1 (9.1%) |
| 2026-08-29 17:30 | Tottenham Hotspur — Newcastle United | 37.3% | 25.8% | 36.9% | 1.36–1.35 | 1–1 (12.2%); 1–0 (9.0%); 0–1 (9.0%) |
| 2026-08-30 14:00 | Chelsea — Brighton & Hove Albion | 45.5% | 25.2% | 29.3% | 1.54–1.19 | 1–1 (12.0%); 1–0 (10.1%); 2–1 (9.2%) |
| 2026-08-30 14:00 | Leeds United — Brentford | 41.3% | 25.6% | 33.1% | 1.45–1.27 | 1–1 (12.2%); 1–0 (9.6%); 2–1 (8.8%) |
| 2026-08-30 14:00 | Sunderland — Fulham | 43.5% | 25.4% | 31.1% | 1.49–1.22 | 1–1 (12.1%); 1–0 (9.9%); 2–1 (9.0%) |
| 2026-08-30 16:30 | Manchester United — Ipswich Town | 64.0% | 20.5% | 15.5% | 2.04–0.89 | 2–0 (11.2%); 1–0 (11.0%); 2–1 (9.9%) |
| 2026-08-31 20:00 | Aston Villa — Arsenal | 32.3% | 25.5% | 42.2% | 1.25–1.47 | 1–1 (12.1%); 0–1 (9.6%); 1–2 (8.9%) |

The full-precision [JSON](forecast.json), [CSV](forecast.csv), [coverage](coverage.json), and
[provenance](provenance.md) are included. Published lambdas reproduce H/D/A and scoreline
probabilities through the independent-Poisson matrix. Private training rows, fitted coefficients,
and team Elo state are not distributed.

Fixture and Matchweek 1 result facts were reconciled to a revision-pinned OpenFootball CC0 ledger.
Adam Luboš Polanský licenses the derived forecast dataset under CC BY 4.0. Original code and
documentation remain MIT licensed.

Independent research project; not affiliated with or endorsed by the Premier League or its clubs.
