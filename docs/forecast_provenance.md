# Forecast provenance

## Fixture ledger

- Repository: `openfootball/england`
- Commit: `afc118c3314171ef0b2cbb43ea0144ca3ebaf0b9`
- File: `2026-27/1-premierleague.txt`
- Git blob: `0df224ccbfef00d8dcc0545466af5c5bcddc4cc3`
- Download SHA-256: `ec7f37c90517fe8d697bff0e8be9ce87d2bb54e11c67c0883c5bf5c955aa9e91`
- Pinned [source file](https://github.com/openfootball/england/blob/afc118c3314171ef0b2cbb43ea0144ca3ebaf0b9/2026-27/1-premierleague.txt)
- Licence file at the same commit: Git blob `670154e3538863b2d9891fd5483160fbdfc89164`,
  SHA-256 `36ffd9dc085d529a7e60e1276d73ae5a030b020313e6c5408593a6ae2af39673`,
  [CC0-1.0 text](https://github.com/openfootball/england/blob/afc118c3314171ef0b2cbb43ea0144ca3ebaf0b9/LICENSE.md)

The downloaded bytes, blob identity, and licence hash were independently verified before parsing.
No Premier League website content was scraped or redistributed. The frozen release specification
labels the displayed source clock values as BST; the UTC values are the corresponding IANA
`Europe/London` conversions. The bare OpenFootball text file does not itself carry a timezone
field, so this interpretation is explicit rather than implied source metadata.

## Model and run commitment

- Public model label: `Dynamic Dixon–Coles incumbent`
- Public model ID: `dynamic-dixon-coles-incumbent-2026-27-v1`
- Source-code commitment: `555a2382f34e721cbc7790963c0c0b6b6e099c55`
- Frozen artifact file SHA-256: `098b7fcbcffc0c218e417d886dea399d4d89e790fc0314084f02be1f087e9761`
- Frozen artifact content commitment: `62990a66c59263d0f7ea053bf89a10c881fd1c97483e5992475fafac74abef19`
- Training-manifest commitment: `ca2c1bfcc79185b620301e6af96da2b8c6b555f2f29d58abaffa4fee8de68855`
- Training rows: `6080`
- Training-data cutoff: `2026-05-24`
- Information cutoff: `2026-08-21T12:04:19Z`
- Generated at: `2026-08-21T12:06:03Z`
- Sanitized run ID: `epl-2026-27-mw01-dynamic-dc-incumbent-20260821t120603z`
- Forecast JSON SHA-256: `de5075834b6e6c6a873df6de6f3eb53ad0e71ee756b20c5e18ac1143658a571b`
- Forecast CSV SHA-256: `0758a47cdb3702afad0c382e9730ca8d1964b9afce59232444d8a9920e5b979b`

The artifact and its licensed/private historical training rows are not distributed. Two independent
runs from the same frozen inputs produced byte-identical JSON, CSV, and private run manifests. The
public repository therefore reproduces validation and presentation of the released probabilities,
but cannot reproduce their exact generation from raw history.

## Rights and independence

OpenFootball fixture facts remain CC0-1.0. Adam Luboš Polanský licenses the derived forecast dataset
under CC BY 4.0. Original repository code and documentation remain MIT licensed; MIT does not
relicense fixture facts or the forecast dataset.

Independent research project; not affiliated with or endorsed by the Premier League or its clubs.
