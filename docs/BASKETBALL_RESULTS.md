# B002 basketball historical results

[Project](../README.md) · [Study](BASKETBALL_FOUNDATION.md) · [Model card](BASKETBALL_MODEL_CARD.md) · [Aggregate export](evidence/2026-10-27-basketball-b002.json)

These tables are generated from the audited aggregate export. All completed tracks use reconstructed research under a 24-hour historical release assumption. T−60 is primary; T−24h is separately retained in the export. No strict historical availability or MARKET-advantage claim is made.

## Separate league leaderboards at T−60

Each table is sorted by pooled 2025–2026 log loss, the declared historical selection criterion. The two seasons remain separate columns. Pooled results are selected development evidence. More favorable accuracy alone does not replace the primary proper-score selection. Every recipe within a league's full-cohort comparison shares its game IDs; the aggregate cohort digests are retained in the export.

### NBA

Games: 1,248 in ending 2025 and 1,249 in ending 2026. Selected probability recipe: Strength · regularized logistic; this selection is not an independent prospective win.

| Probability model | 2025 log loss ↓ | 2026 log loss ↓ | 2025 Brier ↓ | 2026 Brier ↓ | Pooled log loss ↓ |
|---|---:|---:|---:|---:|---:|
| Strength · regularized logistic | 0.612542 | 0.602398 | 0.212630 | 0.207240 | 0.607468 |
| Combined · LightGBM | 0.615663 | 0.600335 | 0.213592 | 0.206390 | 0.607996 |
| Combined · regularized logistic | 0.614027 | 0.602893 | 0.213190 | 0.207519 | 0.608458 |
| Combined · XGBoost | 0.615334 | 0.602017 | 0.213367 | 0.207059 | 0.608673 |
| Combined · CatBoost | 0.613618 | 0.604264 | 0.212769 | 0.208086 | 0.608939 |
| Elo | 0.620090 | 0.615681 | 0.216119 | 0.213200 | 0.617885 |
| Style · regularized logistic | 0.619929 | 0.620885 | 0.215640 | 0.216015 | 0.620407 |
| Historical prior | 0.691406 | 0.687738 | 0.249119 | 0.247298 | 0.689571 |

### NCAA men

Games: 5,758 in ending 2025 and 5,749 in ending 2026. Selected probability recipe: Combined · regularized logistic; this selection is not an independent prospective win.

| Probability model | 2025 log loss ↓ | 2026 log loss ↓ | 2025 Brier ↓ | 2026 Brier ↓ | Pooled log loss ↓ |
|---|---:|---:|---:|---:|---:|
| Combined · regularized logistic | 0.530652 | 0.533493 | 0.179246 | 0.180642 | 0.532072 |
| Strength · regularized logistic | 0.532608 | 0.536842 | 0.179888 | 0.181919 | 0.534724 |
| Combined · LightGBM | 0.533927 | 0.539100 | 0.180260 | 0.182619 | 0.536511 |
| Combined · CatBoost | 0.534978 | 0.540770 | 0.180502 | 0.183091 | 0.537872 |
| Combined · XGBoost | 0.535829 | 0.541036 | 0.180861 | 0.183200 | 0.538431 |
| Style · regularized logistic | 0.544359 | 0.543017 | 0.184889 | 0.184374 | 0.543688 |
| Elo | 0.577370 | 0.579176 | 0.196005 | 0.196933 | 0.578272 |
| Historical prior | 0.654637 | 0.655745 | 0.231030 | 0.231566 | 0.655191 |

### NCAA women

Games: 5,280 in ending 2025 and 5,621 in ending 2026. Selected probability recipe: Combined · regularized logistic; this selection is not an independent prospective win.

| Probability model | 2025 log loss ↓ | 2026 log loss ↓ | 2025 Brier ↓ | 2026 Brier ↓ | Pooled log loss ↓ |
|---|---:|---:|---:|---:|---:|
| Combined · regularized logistic | 0.462930 | 0.467299 | 0.153622 | 0.155838 | 0.465183 |
| Strength · regularized logistic | 0.466404 | 0.471605 | 0.154917 | 0.157457 | 0.469086 |
| Combined · CatBoost | 0.471311 | 0.476958 | 0.156043 | 0.158465 | 0.474223 |
| Combined · LightGBM | 0.471040 | 0.477436 | 0.156140 | 0.158732 | 0.474338 |
| Combined · XGBoost | 0.472680 | 0.478943 | 0.156715 | 0.159305 | 0.475910 |
| Style · regularized logistic | 0.486213 | 0.484667 | 0.161825 | 0.161406 | 0.485416 |
| Elo | 0.538450 | 0.544951 | 0.179040 | 0.182152 | 0.541802 |
| Historical prior | 0.671204 | 0.675379 | 0.239115 | 0.241174 | 0.673357 |

## Selected probability and point-head diagnostics

Point metrics below belong to the separately selected shared Ridge margin/total head, not to a CatBoost score regressor. The selection's probability and point recipes may differ. Home and away point errors, calibration bias, and every comparison model are retained in the JSON export.

| League | Season | Games | Correct / incorrect | Accuracy | Calibration error ↓ | Margin MAE / RMSE ↓ | Total MAE / RMSE ↓ |
|---|---:|---:|---:|---:|---:|---:|---:|
| NBA | 2025 | 1,248 | 811 / 437 | 64.98% | 0.030820 | 11.198 / 14.348 | 15.063 / 18.822 |
| NBA | 2026 | 1,249 | 846 / 403 | 67.73% | 0.030582 | 11.450 / 14.613 | 15.566 / 19.482 |
| NCAA men | 2025 | 5,758 | 4,157 / 1,601 | 72.20% | 0.014187 | 9.156 / 11.745 | 13.023 / 16.683 |
| NCAA men | 2026 | 5,749 | 4,121 / 1,628 | 71.68% | 0.020576 | 9.355 / 11.915 | 13.783 / 17.396 |
| NCAA women | 2025 | 5,280 | 4,036 / 1,244 | 76.44% | 0.016230 | 9.963 / 12.730 | 12.705 / 16.065 |
| NCAA women | 2026 | 5,621 | 4,263 / 1,358 | 75.84% | 0.023989 | 10.059 / 12.799 | 12.746 / 16.145 |

## Raw MARKET versus the selected basketball recipe on identical games

The basketball recipe here is the full-cohort historical selection, evaluated on the exact MARKET-matched subset. It is not a separately selected per-year winner. A blank comparison means no eligible matched events; it is never counted as a loss or abstention. Positive Δ means basketball log loss is worse than MARKET.

| League | Horizon | Season | Matched games | Basketball log loss ↓ | Raw MARKET log loss ↓ | Δ basketball − MARKET |
|---|---:|---:|---:|---:|---:|---:|
| NBA | T−60m | 2025 | 7 | 0.608742 | 0.494135 | +0.114607 |
| NBA | T−60m | 2026 | 6 | 0.578490 | 0.624363 | -0.045873 |
| NCAA men | T−60m | 2025 | 0 | Unavailable | Unavailable | Unavailable |
| NCAA men | T−60m | 2026 | 118 | 0.561269 | 0.563326 | -0.002056 |
| NCAA women | T−60m | 2025 | 23 | 0.414307 | 0.387688 | +0.026619 |
| NCAA women | T−60m | 2026 | 13 | 0.467567 | 0.442156 | +0.025412 |
| NBA | T−1440m | 2025 | 38 | 0.642175 | 0.614900 | +0.027275 |
| NBA | T−1440m | 2026 | 30 | 0.663036 | 0.684227 | -0.021191 |
| NCAA men | T−1440m | 2025 | 0 | Unavailable | Unavailable | Unavailable |
| NCAA men | T−1440m | 2026 | 69 | 0.567283 | 0.544718 | +0.022566 |
| NCAA women | T−1440m | 2025 | 2 | 0.326284 | 0.433288 | -0.107005 |
| NCAA women | T−1440m | 2026 | 2 | 0.306929 | 0.214307 | +0.092622 |

Learned MARKET-only and integrated MARKET/basketball classifiers did not fit: their eligible training cohorts were below the declared requirements. The result is unavailable, not a zero score. No league qualified a model advantage. The 2026 men's T−60 style-model result is exploratory: 118 games, 13 blocks, Δ log loss −0.006053 with a 95% block interval [−0.041032, 0.035094], and no matched 2025 cohort.

## Representation interactions and uncertainty

These contrasts compare the combined representation with its strength and style controls on the same full basketball games. Negative Δ favors the combined model. The seven-calendar-day block intervals are descriptive after model selection; repeated-team and longer-term dependence may remain. They do not establish superiority to MARKET.

| League | Contrast at T−60 | Games | Δ log loss | Descriptive 95% interval | Blocks |
|---|---|---:|---:|---|---:|
| NBA | Combined − Strength · regularized logistic | 2,497 | +0.000990 | [-0.000679, +0.002824] | 69 |
| NBA | Combined − Style · regularized logistic | 2,497 | -0.011949 | [-0.018660, -0.005659] | 69 |
| NCAA men | Combined − Strength · regularized logistic | 11,507 | -0.002652 | [-0.004052, -0.001301] | 46 |
| NCAA men | Combined − Style · regularized logistic | 11,507 | -0.011617 | [-0.015740, -0.008339] | 46 |
| NCAA women | Combined − Strength · regularized logistic | 10,901 | -0.003903 | [-0.005283, -0.002457] | 44 |
| NCAA women | Combined − Style · regularized logistic | 10,901 | -0.020233 | [-0.026421, -0.015060] | 44 |

## Forward monitoring

B002's 110 issued rows span 61 future games and are explicitly early outlooks before their named locks. Zero qualified current MARKET probabilities were present, and zero forecasted games had settled at issue. Prospective proper scores, accuracy and profit were unavailable. Retrospective 2027 monitoring is stored separately and cannot select model parameters. B003 owner execution and all proposed coverage/efficiency improvements remain pending.
