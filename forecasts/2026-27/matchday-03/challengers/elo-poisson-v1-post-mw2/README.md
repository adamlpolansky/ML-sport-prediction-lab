# Matchweek 3 — Elo updated through Matchweek 2

Generated at `2026-09-05T14:20:10Z`. **3 of 10 fixtures have prospective forecasts.**
The other seven fixtures had passed their scheduled kickoff by generation time and are listed
in [coverage](coverage.json), with no retrospective probabilities.

The existing Elo–Poisson challenger uses Elo updated through **31 August 2026**, after all ten
Matchweek 2 results. K=20, home-update advantage=60, rating scale=400 and frozen date batches apply.
The post-MW1 Poisson mapping remains frozen: 6,090 training matches through 24 August 2026.
This release is an `exploratory_post_matchweek_elo_update`; promotion performed: false.

<!-- matchday3-table:start -->
| Kickoff (Prague) | Fixture | Home | Draw | Away | H/D/A pick | Goals H–A | O2.5 | BTTS | Modal |
| --- | --- | ---: | ---: | ---: | --- | ---: | ---: | ---: | --- |
| 2026-09-05 18:30 | Hull City — Aston Villa | 30.8% | 25.3% | 43.9% | Away | 1.22–1.51 | 51.4% (Over) | 55.0% (Yes) | 1–1 (12.0%) |
| 2026-09-06 15:00 | Everton — Manchester United | 37.4% | 25.8% | 36.9% | Home | 1.36–1.35 | 50.9% (Over) | 55.1% (Yes) | 1–1 (12.2%) |
| 2026-09-06 17:30 | Arsenal — Chelsea | 62.9% | 20.9% | 16.2% | Home | 2.00–0.90 | 55.4% (Over) | 51.4% (Yes) | 1–0 (11.0%) |
<!-- matchday3-table:end -->

All times above are Europe/Prague (CEST, UTC+2). The machine files also include UTC and London time.
Home/Draw/Away, Over 2.5, BTTS and scorelines come from the same normalized Poisson score grid.
The H/D/A pick is the highest-probability outcome for every fixture, with no confidence threshold.
For each goal market, pick the more probable side: Over/BTTS Yes above 50%, Under/BTTS No
below 50%, and no bet at exactly 50%, using unrounded probabilities. A correct Under or No
counts as a win. All three remaining fixtures select Over 2.5 and BTTS Yes.
Goals H–A are model-implied goal expectations, not observed post-match shot-based xG.

- [Forecast CSV](forecast.csv) · [Forecast JSON](forecast.json)
- [Complete fixture coverage](coverage.json)
- [Elo update manifest](update.json) · [Source and model provenance](provenance.md)
- [Results and threshold tracker for MW1–2](../../../tracking/README.md)

The seven omitted fixtures are Ipswich–Liverpool, Newcastle–Bournemouth, Forest–Tottenham,
Manchester City–Coventry, Brighton–Leeds, Brentford–Sunderland and Fulham–Crystal Palace.
Their results do not enter this forecast's Elo state or Poisson mapping.
A Dixon–Coles MW3 forecast has not been released.

Fixture/result facts: OpenFootball CC0. Derived forecast dataset: CC BY 4.0,
attributed to Adam Luboš Polanský. Code and documentation: MIT.
