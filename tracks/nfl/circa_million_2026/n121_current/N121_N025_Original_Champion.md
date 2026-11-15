# NFL N025 retained paper models across 715 games

The N025 winner model picked **92 of 144 decisive 2026 games** correctly (63.89%). Its margin error averaged **9.86 points** and its total error averaged **10.89 points** across all 145 finals through November 15 at 21:29 UTC. Of those 145 games, 24 have a verified pregame forecast from the retained recipe family. The other 121 use later historical reconstructions. The original issue ledger identifies the model and weights that produced each of the 24.

## Winner probabilities

Both models estimate the away team's chance of winning given a decisive game. One 2025 tie and one 2026 tie are excluded. Lower Brier score and log loss indicate more accurate probabilities. The N121 comparator is the recent-score opponent-adjusted ridge model, registered as `n121_opponent_ridge_recent`.

| Season | Decisive games | N025 correct | N025 Brier | N025 log loss | N121 correct | N121 Brier | N121 log loss |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2024 | 285 | 193 (67.72%) | 0.212923 | 0.615875 | 191 (67.02%) | 0.216805 | 0.623573 |
| 2025 | 284 | 187 (65.85%) | 0.218665 | 0.625929 | 180 (63.38%) | 0.223138 | 0.636015 |
| 2026 | 144 | 92 (63.89%) | 0.221951 | 0.633178 | 89 (61.81%) | 0.223387 | 0.636725 |

N025 recorded the lower loss on all three annual comparisons. N025's 2024 and 2025 forecasts came from retrospective weekly reconstructions, with historical result-publication times represented by proxies. The primary N121 validation and test leaderboard uses its registered evidence requirements. This historical comparison carries no promotion decision.

## N025 point forecasts

Margin means away score minus home score. Totals come from their own scoring model. MAE is the average absolute error in points. RMSE gives larger misses more weight.

| Season | Games | Margin MAE | Margin RMSE | Total MAE | Total RMSE |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2024 | 285 | 10.0564 | 13.0532 | 9.8258 | 12.7257 |
| 2025 | 285 | 10.0002 | 12.8111 | 10.6491 | 13.4573 |
| 2026 | 145 | 9.8558 | 12.4335 | 10.8858 | 13.5462 |

On the 144 current-season games with a paired DraftKings total, N025's mean absolute error was 10.8401 points and DraftKings' was 10.4375. Los Angeles at Washington in Week 9 lacks the matched quote. This comparison includes historical price vintages and quotes already held at forecast issuance. The evidence records which clocks were observed.

## What is in the 2026 totals

| Games | Forecast evidence |
| --- | --- |
| First 120 | Archived N025 weekly reconstructions. Philadelphia at Washington was the 120th final. |
| Next 16 | N025 issued all three forecasts on November 2 at 17:00 UTC, before Chicago at Seattle and all 15 Week 9 games. The winner model went 14/16, with Brier 0.160869. Margin and total MAE were 9.8812 and 10.9733. |
| Eight Week 10 finals on November 15 | The N106 release issued winner and margin forecasts under N024 on November 14 at 22:50 UTC. N025 retained those exact seven-component parent recipes. The N108 release issued a strict N025 total refit on November 15 at 00:32 UTC. The winner model went 5/8, margin MAE was 11.8213 and total MAE was 6.2871. |
| Washington at the New York Giants in Week 10 | Later weekly reconstructions. The archived inputs use a source-clock proxy and the issue times are empty. The total was 44.12 against a final of 45. |

N025's retained winner and margin blend combines recent team scoring, two team-strength forecasts, three forecasts from team counts and team-strength/count combinations, and a correction learned from prior out-of-fold errors. The total blend has six components. Three reuse protected parent predictions. The other three estimate corrections using ridge regression and boosted trees. The underlying design includes 201 direct fields, 30 earlier-error features and 111 context features, including confidence, rest, opponent strength, pace and pass tendency.

The pre-2024 matched selection retained N025's winner, margin and total paper recipes. The market remained the recorded incumbent. The N026 candidates and the later N108 winner-market blend have their own model identities.

[Season metrics in CSV](N121_N025_Original_Champion.csv) · [Source hashes, case classifications and forecasts in JSON](N121_N025_Original_Champion.json)
