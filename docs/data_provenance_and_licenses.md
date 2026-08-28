# Data provenance and licences

## Committed material

Except for the narrowly enumerated forecast and result releases below, committed fixtures, club
names, person keys, dates, scores, tier inputs, and evidence outputs are fictional and authored by
Adam Luboš Polanský. They are generated from fixed seeds and exist only to exercise deterministic
software behavior.

The repaired v0.2 feature base is synthetic-only. This stacked forecast tree adds only the narrow
real-fixture/derived-probability exception and the result-scorecard exception documented below.
Older reachable public history contains safe, non-reconstructive aggregates but no fitted model
artifacts.

## Matchweek 1 forecast exception

The ten fixture identities and kickoffs come from `openfootball/england` commit
`afc118c3314171ef0b2cbb43ea0144ca3ebaf0b9`, file `2026-27/1-premierleague.txt`, under CC0-1.0.
The source blob and downloaded bytes are pinned in [forecast provenance](forecast_provenance.md).
Only those facts and Adam's derived probabilities are redistributed; no upstream page payload,
result, logo, mark, graphic, prose, or provider identifier is included.

Adam Luboš Polanský licenses the machine forecast dataset under CC BY 4.0. The fitted model artifact
and licensed/private historical inputs remain outside the public repository, so exact probability
generation is not publicly reproducible.

## Matchweek 1 result and scorecard exception

The ten final scores come from `openfootball/england` commit
`836b1947fa4089c86b6064f821eee7de926a7a3f`, file `2026-27/1-premierleague.txt`, under CC0-1.0.
The Git blob and downloaded bytes are pinned in the [result provenance](../forecasts/2026-27/matchday-01/results/provenance.md).
Only fixture identities, kickoffs, final scores, and deterministic metrics computed from the
already-public pre-match forecasts are redistributed.

The score facts remain CC0-1.0/public domain. Adam Luboš Polanský licenses the derived per-fixture
model scores, aggregate scorecard, and season tracker under CC BY 4.0. No source payload, odds,
private row, fitted coefficient, or Elo state is included.

## Material not redistributed

Outside the explicit forecast and result paths, this repository redistributes no Football-Data
rows, odds, caches, or response payloads. It redistributes no Wikimedia-derived manager spell, tier
table, page content, or payload. It contains no real fitted model, private club mapping, source
adapter, or downloader.

Except for the forecast exception above, if a user independently adapts the interfaces to external data, that user is responsible for
obtaining lawful access, following every applicable licence and service term, retaining required
attribution, and preventing restricted inputs or derived artifacts from entering version control.

## Licence boundary

The top-level MIT licence covers repository code and Adam-authored documentation. It grants no
rights to third-party datasets, services, trademarks, club marks, photographs, or other content and
does not relicense the CC0 fixture/result facts or CC BY 4.0 forecast and scorecard datasets.

Recorded release hashes are computed from canonical Git blobs or downloaded release bytes, not
from a checkout whose line endings may have been rewritten by platform-specific Git settings.
Offline execution is a network-independence property, not a cross-platform byte-determinism claim;
byte equality is asserted only for the same supported platform and pinned dependency set.
