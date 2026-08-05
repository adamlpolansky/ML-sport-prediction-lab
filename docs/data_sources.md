# Data sources

## Committed public data

Every fixture used by the runnable public demo is generated locally from `configs/synthetic_demo.json`.
Team names are fictional, fixture identifiers use a synthetic namespace, dates are invented, and
scores are sampled deterministically from synthetic latent strengths. The generated CSV is not a
sample of a provider response.

## Private historical evaluation

A separate private evaluation used Football-Data.co.uk source data. This repository publishes only
non-reconstructive aggregate metrics: 5,700 development matches, 380 OOS matches, and model-level
scores. It does not redistribute match rows, predictions, odds, URLs tied to extracts, file hashes,
provider identifiers, mappings, or trained parameters. Consequently the public clone cannot
reproduce those exact historical figures.

## Optional local sources

Users may implement local provider adapters under their own account and terms. They are responsible
for credentials, lawful access, attribution, retention, and deletion. Downloaded payloads and all
derived private artifacts must remain outside version control. Football-data.org attribution is
required when its service is used.

> Synthetic demonstration — not evidence of real-world predictive performance.
