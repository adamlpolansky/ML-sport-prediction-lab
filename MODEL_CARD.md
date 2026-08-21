# Model card

## Overview

The public project contains an independent-Poisson teaching demo, a v0.2 chronological feature
engine, an immutable EPL 2026/27 Matchweek 1 incumbent forecast, and an append-only exploratory
Elo–Poisson challenger pack. The demos and feature evidence
execute offline on deterministic fictional fixtures. The forecast pack is a narrow release of real
fixture identities and sanitized derived probabilities; its fitted artifact and historical rows are
not distributed. Adam Luboš Polanský authors the distributed code, synthetic examples, and forecast
dataset.

## Intended uses

- Learning how score models imply coherent home/draw/away probabilities.
- Studying point-in-time feature construction and frozen same-date state updates.
- Testing fixed and caller-seeded Elo mechanics with synthetic invariants.
- Reviewing explicit missingness, uncertainty, evidence, and publication controls.
- Inspecting one immutable, timestamped pre-match probability evidence pack.

## Claim boundary

The committed artifacts demonstrate reproducibility and software invariants only. They do not
establish external validity, deployability, profitability, a betting edge, or superior forecasting
performance. Tier-seeded Elo is implemented but not empirically evaluated and is not promotion
eligible. The feature-engineering candidate was not promoted; the dynamic Dixon–Coles incumbent was
retained.

The original Matchweek 1 pack uses the retained Dynamic Dixon–Coles incumbent, not the unpromoted
v0.2 feature candidate. The challenger was designed after reviewing the shape of that forecast and
was not trained or selected for exact-score diversity. Both packs contain ten prospective rows
generated before the first kickoff. The challenger has a favorable frozen paired OOS research
signal but is not automatically promoted. Neither pack is a result, betting advice, evidence of
profit, or a deployment claim.

## Leakage controls

- Feature state is computed only from events strictly before each match cutoff.
- All fixtures on one date are emitted from frozen state and updated as a batch.
- Manager spells require distinct knowledge and effective timestamps.
- Unknown context remains unavailable rather than being forward-filled.
- Outcome and identity columns never enter the model feature mapping.
- Row-order and future-mutation invariants are executable tests.
- The forecast uses one pre-kickoff information cutoff; Matchweek 1 outcomes, live state, news,
  lineups, injuries, managers, referees, tiers, markets, and odds are excluded.

## Limitations

The synthetic schedule is deliberately small and fictional. Referee context is **Not included**,
and the primary implementation omits train-only feature selection. Real competitions can have postponements,
ambiguous timestamps, format changes, sparse history, identity changes, and distribution shift.
Fail-closed validation can therefore reject inputs that lack an adequate point-in-time contract.
Exact forecast generation is not publicly reproducible because the licensed/private history and
fitted artifact are intentionally omitted. Coventry City, Hull City, and Ipswich Town use the
incumbent's uniform neutral promoted/unseen prior, which increases cold-start uncertainty.

## Prohibited uses

Do not use the synthetic model or evidence for betting, financial decisions, eligibility,
discipline, player safety, or any consequential decision. Do not represent it as real-performance
evidence.
