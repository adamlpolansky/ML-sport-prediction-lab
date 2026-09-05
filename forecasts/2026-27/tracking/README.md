# EPL 2026/27 · model tracker after Matchweek 2

Results through **31 August 2026**. All original forecasts remain unchanged.

## Match outcome · all forecasts

For H/D/A, the pick is the outcome with the highest probability for **every fixture**, with **no 50% threshold**. H means home win, D draw and A away win.

| Period | Model | Correct / all forecasts | Accuracy |
| --- | --- | ---: | ---: |
| MW1 | Dynamic Dixon–Coles | 6 / 10 | 60.0% |
| MW1 | Elo–Poisson | 5 / 10 | 50.0% |
| MW2 | Elo–Poisson | 5 / 10 | 50.0% |
| MW1 only | Dynamic Dixon–Coles | 6 / 10 | 60.0% |
| MW1–2 | Elo–Poisson | 10 / 20 | 50.0% |

**Example:** Elo–Poisson made 10 predictions in MW1 and got 5 of the 10 H/D/A outcomes right: **50% accuracy**. Goal-market selections below have their own denominators and do not remove any H/D/A predictions.

## Goal markets · choose the side with probability > 50%

**Over 2.5** means at least three goals; **Under 2.5** means zero, one or two. **BTTS YES** means both teams score; **BTTS NO** means at least one does not. Each market is evaluated separately: choose YES if P(YES) > 50% and NO if P(YES) < 50%, because P(NO) = 1 − P(YES) then exceeds 50%. Exactly 50% is no selection. Correct NO picks count as wins. Hit rate = wins / selected bets. Coverage = selected / probability-available fixtures.

| Period | Model | Market | Available fixtures | Selected | Wins / selected | Hit rate | Coverage |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| MW1 | Dynamic Dixon–Coles | Over / Under 2.5 | 10 | 10 | 6 / 10 | 60.0% | 100.0% |
| MW1 | Dynamic Dixon–Coles | BTTS YES / NO | 10 | 10 | 5 / 10 | 50.0% | 100.0% |
| MW1 | Elo–Poisson | Over / Under 2.5 | 10 | 10 | 7 / 10 | 70.0% | 100.0% |
| MW1 | Elo–Poisson | BTTS YES / NO | 10 | 10 | 5 / 10 | 50.0% | 100.0% |
| MW2 | Elo–Poisson | Over / Under 2.5 | 10 | 10 | 4 / 10 | 40.0% | 100.0% |
| MW2 | Elo–Poisson | BTTS YES / NO | 10 | 10 | 6 / 10 | 60.0% | 100.0% |
| MW1 only | Dynamic Dixon–Coles | Over / Under 2.5 | 10 | 10 | 6 / 10 | 60.0% | 100.0% |
| MW1 only | Dynamic Dixon–Coles | BTTS YES / NO | 10 | 10 | 5 / 10 | 50.0% | 100.0% |
| MW1–2 | Elo–Poisson | Over / Under 2.5 | 20 | 20 | 11 / 20 | 55.0% | 100.0% |
| MW1–2 | Elo–Poisson | BTTS YES / NO | 20 | 20 | 11 / 20 | 55.0% | 100.0% |

For example, Elo MW1 BTTS makes **10 picks**: nine YES and one NO. Four YES picks and the NO pick were right, for **5 / 10 = 50%**. Over/Under and BTTS rates are never pooled: both can refer to the same fixture and are correlated.

The rule was specified retrospectively on **5 September 2026** and was **not pre-registered**. Elo markets are retrospectively derived from the original frozen goal expectations using the unbounded independent-Poisson convention stated in the original MW2 forecast table. DC MW1 markets come from a verified replay of the original frozen Dixon–Coles artifact; the replay exactly matched all original H/D/A, goal-expectation, modal and tail outputs. Its original matrix convention is retained; no independent-Poisson approximation is applied to DC. The retrospective market probabilities are not a record of newly discovered pre-match publications. See the [DC replay commitments](dc_mw1_goal_markets.json).

No odds or stakes were recorded, so hit rate does not determine ROI or profit. These small samples are descriptive. DC has MW1 only; Elo's MW1–2 aggregate combines the original and post-MW1-refit releases and covers twice as many fixtures.

## Expected goals versus actual goals

These are **model-implied expected goals**, not observed shot-based xG. Team-goal MAE averages the absolute home and away goal errors. Signed bias is **actual minus expected**, averaged per team: a positive number means more goals were scored than predicted. Total-goal MAE compares the sum of both expectations with the actual match total.

| Period | Model | Team-goal MAE ↓ | Signed bias / team | Total-goal MAE ↓ |
| --- | --- | ---: | ---: | ---: |
| MW1 | Dynamic Dixon–Coles | 0.890 | +0.151 | 0.892 |
| MW1 | Elo–Poisson | 0.926 | +0.111 | 0.907 |
| MW2 | Elo–Poisson | 1.031 | +0.220 | 1.910 |
| MW1 only | Dynamic Dixon–Coles | 0.890 | +0.151 | 0.892 |
| MW1–2 | Elo–Poisson | 0.979 | +0.166 | 1.408 |

## Release coverage and probability scores

Lower is better for log loss and Brier.

| MW | Model | Forecast status | Results | Scored / forecast | Log loss ↓ | Brier ↓ |
| ---: | --- | --- | --- | ---: | ---: | ---: |
| 1 | Dynamic Dixon–Coles | published_pre_match | scored | 10 / 10 | 0.9497 | 0.5583 |
| 1 | Elo–Poisson | published_pre_match | scored | 10 / 10 | 0.9475 | 0.5615 |
| 2 | Dynamic Dixon–Coles | not_released | not_applicable | 0 / 0 | — | — |
| 2 | Elo–Poisson | published_pre_match | scored | 10 / 10 | 1.0067 | 0.6043 |
| 3 | Dynamic Dixon–Coles | not_released | not_applicable | 0 / 0 | — | — |
| 3 | Elo–Poisson | published_pre_match_partial | pending | 0 / 3 | — | — |

DC MW2 and MW3 are not_released. MW3 Elo is pending for the **three remaining prospective fixtures**; the seven fixtures whose kickoff had already passed are excluded. Empty CSV cells and JSON null mean unavailable, not zero. With no selections, a market's hit rate is null.

## Downloads and methodology

- [Per-matchweek CSV](model_performance.csv) · [Full tracker JSON](model_performance.json)
- [Per-fixture Over 2.5 and BTTS decisions](betting_selections.csv)
- [Expected versus actual goal deviations](goal_deviations.csv)
- [Cumulative metrics](cumulative_performance.csv)
- [Immutable MW1 pack](../matchday-01/results/README.md) · [MW2 results pack](../matchday-02/results/README.md)

Log loss = mean −ln(probability of the observed H/D/A result). Brier = mean sum of squared errors across H, D and A (range 0–2, no division by three). H/D/A ties follow H, D, A order. Cumulative statistics pool fixture-level scores and counts, not weekly hit rates. Market selection uses full derived precision before display rounding; exported p_yes is rounded to 12 decimal places. All market and goal-deviation calculations are available per fixture in the downloads.

Run python -m epl_probability_lab.results_tracker --root . to regenerate in memory and verify every derived artifact. Add --write to reproduce the files. The original MW1 package remains byte-identical.
