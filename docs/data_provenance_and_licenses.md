# Data provenance and licences

## Committed material

All committed fixtures, club names, person keys, dates, scores, tier inputs, and evidence outputs are
fictional and authored by Adam Luboš Polanský. They are generated from fixed seeds and exist only to
exercise deterministic software behavior.

The repaired v0.2 feature base is synthetic-only. This stacked forecast tree adds only the narrow
real-fixture/derived-probability exception documented below. Older reachable public history contains
safe, non-reconstructive aggregates, but no real event rows, per-fixture predictions, or fitted
model artifacts.

## Matchweek 1 forecast exception

The ten fixture identities and kickoffs come from `openfootball/england` commit
`afc118c3314171ef0b2cbb43ea0144ca3ebaf0b9`, file `2026-27/1-premierleague.txt`, under CC0-1.0.
The source blob and downloaded bytes are pinned in [forecast provenance](forecast_provenance.md).
Only those facts and Adam's derived probabilities are redistributed; no upstream page payload,
result, logo, mark, graphic, prose, or provider identifier is included.

Adam Luboš Polanský licenses the machine forecast dataset under CC BY 4.0. The fitted model artifact
and licensed/private historical inputs remain outside the public repository, so exact probability
generation is not publicly reproducible.

## Material not redistributed

This repository redistributes no Football-Data rows, odds, caches, or response payloads. It
redistributes no Wikimedia-derived manager spell, tier table, page content, or payload. It contains
no real fitted model, per-fixture real prediction, real club mapping, source adapter, or downloader.

Except for the forecast exception above, if a user independently adapts the interfaces to external data, that user is responsible for
obtaining lawful access, following every applicable licence and service term, retaining required
attribution, and preventing restricted inputs or derived artifacts from entering version control.

## Licence boundary

The top-level MIT licence covers repository code and Adam-authored documentation. It grants no
rights to third-party datasets, services, trademarks, club marks, photographs, or other content and
does not relicense the CC0 fixture facts or CC BY 4.0 forecast dataset.

Recorded release hashes are computed from canonical Git blobs or downloaded release bytes, not
from a checkout whose line endings may have been rewritten by platform-specific Git settings.
Offline execution is a network-independence property, not a cross-platform byte-determinism claim;
byte equality is asserted only for the same supported platform and pinned dependency set.
