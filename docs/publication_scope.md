# Public v0.2 and forecast scope

This is a curated additive software release, not a research-data release. It contains the generic
chronological feature engine, fixed Elo, generic tier-seeded Elo, manager context, fictional demos,
tests, documentation, and a fail-closed publication guard.

Referee context is **Not included** because reliable assignment-publication timestamps are absent.
Train-only feature selection is also excluded. No source acquisition code, real mapping, real event
row, real fitted artifact, credential, cache, or season assignment is part of the release.

The repaired v0.2 feature base is synthetic-only. This stacked tree adds one narrow, explicit
exception: the EPL 2026/27 Matchweek 1 fixture identities/kickoffs, sanitized derived probabilities,
and the ten final scores from a pinned OpenFootball CC0 ledger. The result pack and season tracker
contain only those final scores plus deterministic metrics calculated from already-public pre-match
forecasts. They add no odds, raw feature, provider row, person timeline, source cache, Elo state,
coefficient, or fitted artifact. Older commits reachable in this public repository contain only
safe, non-reconstructive aggregate summaries; they contain no real source rows, per-fixture
predictions, or fitted model artifacts.

The feature candidate was not promoted and the dynamic Dixon–Coles incumbent was retained. This
decision is reported without detailed research aggregates. Tier-seeded Elo did not reach empirical
evaluation; its public claim is limited to implementation and synthetic verification.

The forecast exception uses the retained Dynamic Dixon–Coles incumbent. The public feature
candidate remains unpromoted and did not drive the forecast. The fixture facts are pinned
OpenFootball CC0 data; Adam's forecast dataset and derived scorecards are CC BY 4.0. The publication
guard permits only the exact release paths and schemas, semantically regenerates the result metrics,
and rejects unapproved results, live fields, odds, provider fields, raw features, private material,
and fitted parameters.

The 5 September update explicitly includes MW2 results and MW1–2 threshold statistics at the
named result/tracker paths, plus the partial prospective MW3 release under
`forecasts/2026-27/matchday-03/challengers/elo-poisson-v1-post-mw2`.
Its ten-fixture coverage file identifies seven already-started fixtures without attaching
retrospective predictions. The updated Elo ratings and frozen model coefficients are local
artifacts; only the forecast and aggregate update manifest are published.
The exact tracker path `dc_mw1_goal_markets.json` adds ten derived goal-market probabilities
from a hash-verified replay of the original MW1 artifact, explicitly labelled retrospective.
`goal_deviations.csv` compares original model expectations against final goals; it contains
no observed shot-based xG or new feature rows. Neither supplement modifies the original MW1 pack.
