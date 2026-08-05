# Data rights and local-use contract

The MIT licence in this project applies to original software and documentation authored by Adam
Polanský. It does **not** license third-party provider data, API services, logos, club badges,
photographs, or trademarks.

## What this project distributes

- Deterministically generated fixtures for fictional teams.
- A model artifact fitted only on those synthetic fixtures.
- Synthetic predictions, aggregate demo metrics, and a synthetic reliability plot.
- A compact set of non-reconstructive metrics from a private historical evaluation.

No third-party match-level dataset is distributed. No real football-data.org response, wrapper, or
snapshot is distributed. The public project contains no provider-derived team mapping, membership
registry, real fitted team parameter, live snapshot, prospective ledger, or acceptance record.

## Optional provider use

Provider adapters are optional local interfaces and are not needed for the offline demo. Users must
obtain their own credentials, comply with the provider's current terms, and keep downloaded data,
tokens, terms records, mappings, and generated private artifacts local and ignored. When the
football-data.org service is used, its required attribution must be displayed.

The empty `FOOTBALL_DATA_ORG_TOKEN` variable in `.env.example` is documentation only. The public
clone reproduces the synthetic demo; it does not reproduce the private historical evaluation.
