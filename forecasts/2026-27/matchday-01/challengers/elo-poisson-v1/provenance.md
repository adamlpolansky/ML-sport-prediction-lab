# Elo–Poisson challenger provenance

## Fixture ledger

- Repository: `openfootball/england`
- Commit: `afc118c3314171ef0b2cbb43ea0144ca3ebaf0b9`
- File: `2026-27/1-premierleague.txt`
- Git blob: `0df224ccbfef00d8dcc0545466af5c5bcddc4cc3`
- Download SHA-256: `ec7f37c90517fe8d697bff0e8be9ce87d2bb54e11c67c0883c5bf5c955aa9e91`
- [Pinned source](https://github.com/openfootball/england/blob/afc118c3314171ef0b2cbb43ea0144ca3ebaf0b9/2026-27/1-premierleague.txt)
- Licence: CC0-1.0; blob `670154e3538863b2d9891fd5483160fbdfc89164`, SHA-256
  `36ffd9dc085d529a7e60e1276d73ae5a030b020313e6c5408593a6ae2af39673`

No new fixture source was fetched for this release. The already verified ledger is shared with the
immutable Dynamic Dixon–Coles v1 release.

## Frozen research commitments

- Model ID: `fixed-elo-neutral-reentry-poisson-v1`
- Private source-code commit: `43c4be27754787418aaa4539be0e37647eb1e8ae`
- Base protocol SHA-256: `b7e5365f8b0af44b62c0d236ee222375638a5587abb284dd9d47a3814332e9ad`
- Protocol amendment SHA-256: `aa0f1883a1eddb05d296ab96b5e318884708e10dda69f9327f836c14a549da74`
- Effective protocol SHA-256: `2d8fa02cf6b5e456a983c085761419536d8f832e1864bdf0cd52c346957cac12`
- Combined canonical source commitment: `fa11cf7d253feb60ba163945c75088bcd6da35a34f82e12dcaab4618651c12f6`
- Canonical development rows SHA-256: `648fa0ce99b222325cf6ca1bb82defb568ec008e735831b73b253f74669de84c`
- Descriptive 2025/26 stress rows SHA-256: `a6ca706f2e2ec5d8b4949f812af1dac581d2fb6f2607dd69541a8883bdf22e28`
- Incumbent paired OOS evidence SHA-256: `a103633895b0b1716e80a41551366e375f8e2142b40489d1e03c7f1c8c8f0ad0`
- Private fitted artifact SHA-256: `2988fad1be3bd6d5b97aa03155f9e91dd62fa9b717cbbc91ae2bd85a0b6ceaca`

The amendment binds the frozen model to the canonical v0.3 EPL row ledger after an initial run
failed closed on mismatched match identities. It records that failed run and changes no Elo,
Poisson, decay, clipping, bootstrap, or decision parameter.

## Forecast and public artifacts

- Training maximum: `2026-05-24`
- Information cutoff: `2026-08-21T14:01:16Z`
- Generated at: `2026-08-21T14:01:17Z`
- Coverage: 10 of 10 fixtures, all generated before kickoff
- Forecast JSON SHA-256: `7cfff5b6821d508be069e96546fed0276b1efd898a0cecfd5682132ceec7532e`
- Forecast CSV SHA-256: `cfaba9ec9c31115f5ce5d17ed96ddeebc38aaa363656988e9a8e3ab2cebfeacb`
- Coverage SHA-256: `c09ed1fe6436717eb87b9dba4e11cab9774e12ab36bcf85f5783103ef4413ca8`
- Evaluation summary SHA-256: `da81f7d361e9d1b388a220562d0e8d6c986388b224efa8c792e1addcab54bc41`
- Immutable v1 JSON SHA-256: `de5075834b6e6c6a873df6de6f3eb53ad0e71ee756b20c5e18ac1143658a571b`
- Immutable v1 CSV SHA-256: `0758a47cdb3702afad0c382e9730ca8d1964b9afce59232444d8a9920e5b979b`

Two private runs with identical frozen inputs and timestamps produced byte-identical machine
artifacts. Private historical rows, per-match OOS predictions, fitted coefficients, and Elo state
are intentionally absent. The public repository supports aggregate-evidence review and exact
reconstruction of post-lambda independent-Poisson probabilities, not end-to-end refitting.

Fixture facts remain CC0-1.0. Adam Luboš Polanský licenses the derived challenger forecast dataset
under CC BY 4.0. Original code and documentation remain MIT licensed.
