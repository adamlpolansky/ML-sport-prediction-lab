# Model card

## Overview

The public project contains an independent-Poisson teaching demo and a v0.2 chronological feature
engine. Both execute offline on deterministic fictional fixtures. Adam Luboš Polanský authors the
distributed code and synthetic examples.

## Intended uses

- Learning how score models imply coherent home/draw/away probabilities.
- Studying point-in-time feature construction and frozen same-date state updates.
- Testing fixed and caller-seeded Elo mechanics with synthetic invariants.
- Reviewing explicit missingness, uncertainty, evidence, and publication controls.

## Claim boundary

The committed artifacts demonstrate reproducibility and software invariants only. They do not
establish external validity, deployability, profitability, a betting edge, or superior forecasting
performance. Tier-seeded Elo is implemented but not empirically evaluated and is not promotion
eligible. The feature-engineering candidate was not promoted; the dynamic Dixon–Coles incumbent was
retained.

## Leakage controls

- Feature state is computed only from events strictly before each match cutoff.
- All fixtures on one date are emitted from frozen state and updated as a batch.
- Manager spells require distinct knowledge and effective timestamps.
- Unknown context remains unavailable rather than being forward-filled.
- Outcome and identity columns never enter the model feature mapping.
- Row-order and future-mutation invariants are executable tests.

## Limitations

The synthetic schedule is deliberately small and fictional. Referee context is **Not included**,
and the primary implementation omits train-only feature selection. Real competitions can have postponements,
ambiguous timestamps, format changes, sparse history, identity changes, and distribution shift.
Fail-closed validation can therefore reject inputs that lack an adequate point-in-time contract.

## Prohibited uses

Do not use the synthetic model or evidence for betting, financial decisions, eligibility,
discipline, player safety, or any consequential decision. Do not represent it as real-performance
evidence.
