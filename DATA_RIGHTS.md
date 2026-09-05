# Data rights and local-use contract

The MIT licence applies only to original software and documentation authored by Adam Luboš
Polanský. It does not grant rights to third-party datasets, services, logos, club marks,
photographs, or trademarks.

The repaired v0.2 feature base distributes deterministic fixtures for obviously fictional clubs,
fictional model outputs, and synthetic-only aggregate evidence. This stacked forecast release adds
one narrow exception: the ten EPL 2026/27 Matchweek 1 fixture identities/kickoffs from a pinned
OpenFootball CC0 source and Adam's sanitized derived pre-match probabilities for the immutable
incumbent and append-only exploratory challenger. A second, tightly scoped exception adds the ten
Matchweek 1 final scores from the same pinned OpenFootball CC0 ledger and Adam's reproducible
per-fixture and aggregate model scorecards. It contains no odds row, manager or referee timeline,
source cache, raw feature row, or fitted real model.

The fixture facts remain CC0-1.0/public domain. Adam Luboš Polanský licenses the incumbent and
challenger `forecast.json` and `forecast.csv` files under CC BY 4.0 with the attribution “EPL
2026/27 Matchweek 1 forecast, Adam Luboš Polanský, 2026.” MIT continues to cover only Adam-authored
code and documentation; it does not relicense the fixture facts or forecast datasets.

The final-score facts in `forecasts/2026-27/matchday-01/results/results.csv` remain CC0-1.0/public
domain. Adam licenses the derived model scorecards and season tracker under CC BY 4.0 with the
attribution “EPL 2026/27 model results tracker, Adam Luboš Polanský, 2026.”

Anyone adapting the software to external data must obtain that data independently, comply with the
applicable terms and licences, provide required attribution, and keep non-redistributable inputs and
derived artifacts outside version control.

See [docs/data_provenance_and_licenses.md](docs/data_provenance_and_licenses.md) for the release
boundary.

The September update extends these exact exceptions to ten MW2 final scores, the derived MW1–2
threshold-selection and cumulative scorecards, and the three prospective MW3 forecasts with a
ten-fixture coverage ledger. Source facts remain CC0-1.0; derived forecasts and scorecards are
CC BY 4.0, attributed to Adam Luboš Polanský. The MW3 update manifest contains only provenance
hashes and aggregate update metadata; fitted coefficients and full Elo state remain local.
The named tracker exception also includes `dc_mw1_goal_markets.json`: ten sanitized Over 2.5
and BTTS probabilities derived retrospectively from the original verified frozen Dixon–Coles
artifact, after exact replay of its published MW1 predictions. It is CC BY 4.0 under the same
attribution. Neither the frozen model nor its fitted parameters are redistributed.

The seven remaining MW3 estimates in the exact `retrospective` subdirectory of the MW3 release
are an additional user-requested forecast-only exception. They are CC BY 4.0 under the same
attribution, explicitly labelled retrospective and unscored. No MW3 results, model parameters,
updated ratings or new performance metrics are distributed in this supplement.
