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
| Referee context | Optional retrospective sensitivity | Not primary/promotion evidence |
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
python -m epl_probability_lab.publication --root .
```

The original independent-Poisson synthetic demo remains available through
`python -m epl_probability_lab.demo`. Both demos run without network access.

Read [the feature contract](docs/feature_engine.md),
[publication scope](docs/publication_scope.md), [model card](MODEL_CARD.md), and
[data provenance and licences](docs/data_provenance_and_licenses.md) before adapting the code.

## Licence

Original code and documentation are MIT licensed under the copyright of Adam Luboš Polanský. The
licence grants no rights to third-party datasets, services, logos, marks, or other provider content.
