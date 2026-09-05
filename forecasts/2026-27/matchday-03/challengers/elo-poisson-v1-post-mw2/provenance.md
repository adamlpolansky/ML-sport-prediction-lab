# Matchweek 3 provenance

## Source

OpenFootball, CC0-1.0:
[revision-pinned 2026/27 ledger](https://github.com/openfootball/england/blob/0690446f794fde748ea4b994244def699c6a65b2/2026-27/1-premierleague.txt).

- Commit: `0690446f794fde748ea4b994244def699c6a65b2` (1 September 2026).
- Git blob: `dec39f0aa20d4ea5653ecfe4257bc7910c00e0eb`.
- Source bytes SHA-256: `10d40e1e7a17e90b64973b83fe2ea78c672819372a186fe87a80b17f4c7c575a`.
- Refreshed and verified on 5 September 2026.
- Forecast generated at `2026-09-05T14:20:10Z`.

## Model lineage

Parent local MW2 audit SHA-256:
`d96ee65cad8ed945af7a6a25522d6897827f41f2549647744b1fc542b4bc821c`.

New local audit SHA-256: `e448da3b0987a0adbbcba16220ac1ec8a469d9e60c425a54b89a0cbd4c48cf5c`.

The parent saved Elo ratings and mapping reproduced all ten immutable MW2 H/D/A probabilities
and lambdas within 1e-12 before this update. Only Elo changes here. Ten MW2 outcomes were applied
with K=20, home-update advantage=60, scale=400, zero-sum updates and frozen same-date batches.
Twenty team ratings were updated. No MW3 result, live score, current-match feature or closing
odds was used. The mapping remains trained on 6,090 rows through 24 August; the state advances
through 31 August. No refit or parameter search was run.

Public model ID: `fixed-elo-neutral-reentry-poisson-v1-post-mw1-refit-post-mw2-elo`.
Artifact status: `exploratory_post_matchweek_elo_update`.
Promotion performed: false.

The complete rating state, fitted coefficients and local audit are retained locally.
Only the sanitized forecast and an aggregate update manifest are distributed.

## Reproduction

`python -m epl_probability_lab.matchday_three_release --root .` checks pinned bytes,
fixture identities, generation-before-kickoff, all ten coverage rows, CSV/JSON parity,
the coherent score distribution and README tables. Exact model generation depends on the
local frozen mapping and Elo artifact; those inputs are not part of the public distribution.
