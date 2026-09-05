# Matchweek 2 · results and Elo–Poisson scorecard

**10/10 fixtures completed.** [Result provenance](provenance.md) · [Original Elo forecast](../challengers/elo-poisson-v1-post-mw1/README.md).

**32 goals**, 3 home wins, 3 draws and 4 away wins.

**H/D/A uses the highest-probability outcome for all 10 fixtures**, without a threshold: **5 / 10 correct (50.0%)**.

| Goal market | Probability-available fixtures | Side >50% selected | Wins / selected | Hit rate | Coverage |
| --- | ---: | ---: | ---: | ---: | ---: |
| Over / Under 2.5 | 10 | 10 | 4 / 10 | 40.0% | 100.0% |
| BTTS YES / NO | 10 | 10 | 6 / 10 | 60.0% | 100.0% |

Over 2.5 requires at least three goals; BTTS YES requires both teams to score. Choose YES above 50% or NO below 50%, whose complementary probability exceeds 50%. A correct Under 2.5 or BTTS NO pick also wins. Exactly 50% is no selection.

| Fixture | Actual | Expected goals H–A | H/D/A pick | Correct |
| --- | ---: | ---: | --- | --- |
| Crystal Palace – Manchester City | 1–4 | 1.115–1.662 | A | Yes |
| Liverpool – Nottingham Forest | 2–2 | 1.842–0.984 | H | No |
| AFC Bournemouth – Everton | 1–1 | 1.684–1.081 | H | No |
| Coventry City – Hull City | 0–1 | 1.506–1.214 | H | No |
| Tottenham Hotspur – Newcastle United | 0–2 | 1.360–1.350 | H | No |
| Chelsea – Brighton & Hove Albion | 4–3 | 1.541–1.185 | H | Yes |
| Leeds United – Brentford | 1–1 | 1.445–1.267 | H | No |
| Sunderland – Fulham | 1–0 | 1.495–1.224 | H | Yes |
| Manchester United – Ipswich Town | 5–2 | 2.035–0.886 | H | Yes |
| Aston Villa – Arsenal | 0–1 | 1.254–1.470 | A | Yes |

Team-goal MAE: **1.031**; mean signed bias (actual minus expected): **+0.220 goals/team**; total-goal MAE: **1.910**. The expectations are model-implied goal means, not shot-based xG.

H/D/A log loss: **1.0067**; Brier: **0.6043**. Lower is better. Brier sums the three squared H/D/A errors (0–2 scale).

Market probabilities are retrospectively derived from original frozen lambdas using the unbounded independent-Poisson convention stated in the original forecast table. The user specified this diagnostic rule on 5 September 2026, after these matches. It was not pre-registered. No odds or stakes means no ROI or profit estimate. DC has no MW2 forecast and remains not_released.

[Results CSV](results.csv) · [Model scores CSV](model_scores.csv) · [Summary CSV](model_summary.csv) · [Full JSON](results.json) · [Market decisions](../../tracking/betting_selections.csv) · [Goal deviations](../../tracking/goal_deviations.csv) · [Season tracker](../../tracking/README.md)
