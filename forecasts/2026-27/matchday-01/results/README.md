# Matchweek 1 results and model scorecard

This release pack closes all 10/10 Matchweek 1 fixtures against the two forecasts that were
published before kickoff. It contains fixture results, per-fixture model scores, aggregate model
scores, and a full-precision JSON equivalent.

## Results

| Fixture | Result | H/D/A | Dixon–Coles pick | Elo–Poisson pick |
| --- | ---: | ---: | ---: | ---: |
| Arsenal — Coventry City | 3–0 | H | H ✓ | H ✓ |
| Hull City — Manchester United | 2–0 | H | A ✗ | A ✗ |
| Everton — Crystal Palace | 2–0 | H | H ✓ | H ✓ |
| Ipswich Town — Sunderland | 2–1 | H | H ✓ | A ✗ |
| Nottingham Forest — Leeds United | 0–1 | A | H ✗ | H ✗ |
| Brentford — Tottenham Hotspur | 3–0 | H | H ✓ | H ✓ |
| Brighton & Hove Albion — Aston Villa | 4–0 | H | H ✓ | H ✓ |
| Manchester City — AFC Bournemouth | 2–1 | H | H ✓ | H ✓ |
| Newcastle United — Liverpool | 2–2 | D | A ✗ | A ✗ |
| Fulham — Chelsea | 2–3 | A | H ✗ | H ✗ |

## Model scorecard

| Model | H/D/A log loss ↓ | H/D/A Brier ↓ | Top-1 accuracy ↑ | Goal MAE ↓ |
| --- | ---: | ---: | ---: | ---: |
| Dynamic Dixon–Coles incumbent | 0.9497 | **0.5583** | **60%** | **0.890** |
| Elo–Poisson challenger | **0.9475** | 0.5615 | 50% | 0.926 |

Lower is better for log loss, Brier score, and goal MAE; higher is better for accuracy. Multiclass
Brier is the unscaled sum of squared errors across H, D, and A. Goal MAE averages the absolute
errors of the two published team goal expectations. The ten-match sample produces a split verdict:
Elo has marginally lower log loss, while the incumbent leads the other three displayed metrics.
This is descriptive tracking, not promotion evidence or a profitability claim.

Files:

- [fixture results](results.csv)
- [per-fixture scores](model_scores.csv)
- [aggregate model scores](model_summary.csv)
- [full JSON pack](results.json)
- [source and calculation provenance](provenance.md)

The result facts come from a revision-pinned OpenFootball CC0 ledger. The derived scorecard is
licensed CC BY 4.0 with attribution to Adam Luboš Polanský. The original forecast artifacts remain
immutable.
