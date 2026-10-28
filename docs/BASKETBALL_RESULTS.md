# B003 basketball historical results

[Project](../README.md) · [Study](BASKETBALL_FOUNDATION.md) · [Model card](BASKETBALL_MODEL_CARD.md) · [B003 aggregate](evidence/2026-10-27-basketball-b003.json) · [Preserved B002 aggregate](evidence/2026-10-27-basketball-b002.json)

B003 completed actual owner execution. These are reconstructed results with a 24-hour statistical-release assumption; original historical publication clocks remain unverified. T−60 is primary and T−24h is separate. The 2025 and 2026 folds are development evidence after selection. Lower selected log loss does not establish an independent MARKET advantage.

## League leaderboards at T−60

All recipes within each league share identical games, outcomes and historical cutoffs. Every earlier B002 control probability, point estimate, outcome and cutoff matched exactly in the B003 audit. Predictor counts accompany learned-model names. The minimum pooled log loss is bolded as a numerical result, not a promotion claim.

### NBA

Games: 1,248 in ending 2025 and 1,249 in ending 2026. Historical probability selection: Strength logistic · 15. This is selected development performance.

| Probability model | 2025 log loss ↓ | 2026 log loss ↓ | 2025 Brier ↓ | 2026 Brier ↓ | Pooled log loss ↓ |
|---|---:|---:|---:|---:|---:|
| Strength logistic · 15 | 0.612542 | 0.602398 | 0.212630 | 0.207240 | **0.607468** |
| Combined LightGBM · 53 | 0.615663 | 0.600335 | 0.213592 | 0.206390 | 0.607996 |
| Rich combined logistic · 63 | 0.614207 | 0.601979 | 0.213281 | 0.207094 | 0.608091 |
| Strength + opponent adjustment · 25 | 0.613829 | 0.602782 | 0.213225 | 0.207398 | 0.608303 |
| Combined logistic · 53 | 0.614027 | 0.602893 | 0.213190 | 0.207519 | 0.608458 |
| Combined XGBoost · 53 | 0.615334 | 0.602017 | 0.213367 | 0.207059 | 0.608673 |
| Combined CatBoost · 53 | 0.613618 | 0.604264 | 0.212769 | 0.208086 | 0.608939 |
| Rich combined LightGBM · 63 | 0.615776 | 0.602757 | 0.213660 | 0.207447 | 0.609264 |
| Margin Elo | 0.622627 | 0.612096 | 0.216533 | 0.210980 | 0.617359 |
| Elo | 0.620090 | 0.615681 | 0.216119 | 0.213200 | 0.617885 |
| Style logistic · 25 | 0.619929 | 0.620885 | 0.215640 | 0.216015 | 0.620407 |
| Historical prior | 0.691406 | 0.687738 | 0.249119 | 0.247298 | 0.689571 |

### NCAA men

Games: 5,758 in ending 2025 and 5,749 in ending 2026. Historical probability selection: Rich combined logistic · 63. This is selected development performance.

| Probability model | 2025 log loss ↓ | 2026 log loss ↓ | 2025 Brier ↓ | 2026 Brier ↓ | Pooled log loss ↓ |
|---|---:|---:|---:|---:|---:|
| Rich combined logistic · 63 | 0.524171 | 0.526661 | 0.177207 | 0.178728 | **0.525415** |
| Strength + opponent adjustment · 25 | 0.525564 | 0.529125 | 0.177734 | 0.179759 | 0.527343 |
| Rich combined LightGBM · 63 | 0.525938 | 0.530295 | 0.177467 | 0.179810 | 0.528115 |
| Combined logistic · 53 | 0.530652 | 0.533493 | 0.179246 | 0.180642 | 0.532072 |
| Strength logistic · 15 | 0.532608 | 0.536842 | 0.179888 | 0.181919 | 0.534724 |
| Combined LightGBM · 53 | 0.533927 | 0.539100 | 0.180260 | 0.182619 | 0.536511 |
| Combined CatBoost · 53 | 0.534978 | 0.540770 | 0.180502 | 0.183091 | 0.537872 |
| Combined XGBoost · 53 | 0.535829 | 0.541036 | 0.180861 | 0.183200 | 0.538431 |
| Style logistic · 25 | 0.544359 | 0.543017 | 0.184889 | 0.184374 | 0.543688 |
| Margin Elo | 0.549636 | 0.554357 | 0.185861 | 0.188067 | 0.551995 |
| Elo | 0.577370 | 0.579176 | 0.196005 | 0.196933 | 0.578272 |
| Historical prior | 0.654637 | 0.655745 | 0.231030 | 0.231566 | 0.655191 |

### NCAA women

Games: 5,280 in ending 2025 and 5,621 in ending 2026. Historical probability selection: Rich combined logistic · 63. This is selected development performance.

| Probability model | 2025 log loss ↓ | 2026 log loss ↓ | 2025 Brier ↓ | 2026 Brier ↓ | Pooled log loss ↓ |
|---|---:|---:|---:|---:|---:|
| Rich combined logistic · 63 | 0.455769 | 0.458433 | 0.151592 | 0.152452 | **0.457143** |
| Strength + opponent adjustment · 25 | 0.458014 | 0.461574 | 0.152498 | 0.153540 | 0.459850 |
| Rich combined LightGBM · 63 | 0.461672 | 0.464640 | 0.153108 | 0.154186 | 0.463203 |
| Combined logistic · 53 | 0.462930 | 0.467299 | 0.153622 | 0.155838 | 0.465183 |
| Strength logistic · 15 | 0.466404 | 0.471605 | 0.154917 | 0.157457 | 0.469086 |
| Combined CatBoost · 53 | 0.471311 | 0.476958 | 0.156043 | 0.158465 | 0.474223 |
| Combined LightGBM · 53 | 0.471040 | 0.477436 | 0.156140 | 0.158732 | 0.474338 |
| Combined XGBoost · 53 | 0.472680 | 0.478943 | 0.156715 | 0.159305 | 0.475910 |
| Style logistic · 25 | 0.486213 | 0.484667 | 0.161825 | 0.161406 | 0.485416 |
| Margin Elo | 0.492140 | 0.499141 | 0.162765 | 0.165798 | 0.495750 |
| Elo | 0.538450 | 0.544951 | 0.179040 | 0.182152 | 0.541802 |
| Historical prior | 0.671204 | 0.675379 | 0.239115 | 0.241174 | 0.673357 |

## Controlled opponent-adjustment comparisons

Negative Δ favors B003. Each row compares the declared new architecture with its exact earlier control. Intervals use 300 paired seven-calendar-day block resamples. They are descriptive after development exposure, not multiplicity-adjusted or untouched confirmation. Additional prior-champion contrasts and per-season uncertainty remain in the export.

| League | B003 arm − B002 control | 2025 Δ log loss | 2026 Δ log loss | Pooled Δ log loss | Pooled descriptive 95% interval | Games / blocks |
|---|---|---:|---:|---:|---|---:|
| NBA | Strength + opponent adjustment · 25 − Strength logistic · 15 | +0.001286 | +0.000384 | +0.000835 | [-0.000030, +0.001803] | 2,497 / 69 |
| NBA | Rich combined logistic · 63 − Combined logistic · 53 | +0.000180 | -0.000913 | -0.000367 | [-0.001068, +0.000467] | 2,497 / 69 |
| NBA | Rich combined LightGBM · 63 − Combined LightGBM · 53 | +0.000113 | +0.002422 | +0.001268 | [-0.000115, +0.002711] | 2,497 / 69 |
| NCAA men | Strength + opponent adjustment · 25 − Strength logistic · 15 | -0.007044 | -0.007717 | -0.007381 | [-0.010681, -0.003917] | 11,507 / 46 |
| NCAA men | Rich combined logistic · 63 − Combined logistic · 53 | -0.006481 | -0.006832 | -0.006657 | [-0.009748, -0.003626] | 11,507 / 46 |
| NCAA men | Rich combined LightGBM · 63 − Combined LightGBM · 53 | -0.007989 | -0.008805 | -0.008397 | [-0.011778, -0.005271] | 11,507 / 46 |
| NCAA women | Strength + opponent adjustment · 25 − Strength logistic · 15 | -0.008390 | -0.010030 | -0.009236 | [-0.013374, -0.006058] | 10,901 / 44 |
| NCAA women | Rich combined logistic · 63 − Combined logistic · 53 | -0.007161 | -0.008866 | -0.008040 | [-0.011341, -0.005301] | 10,901 / 44 |
| NCAA women | Rich combined LightGBM · 63 − Combined LightGBM · 53 | -0.009368 | -0.012796 | -0.011136 | [-0.015249, -0.007690] | 10,901 / 44 |

The richer representation improves both college folds; NBA retains strength logistic. College pooled fixed-bin calibration error increases despite better proper scores: men 0.013393 → 0.014288 and women 0.019232 → 0.023450. The new historical selections are research candidates with a calibration weakness, not universally superior or MARKET-qualified champions.

## Selected probability and separately selected point-head diagnostics

Point estimates use Ridge margin and total regressors. Probability recipe names do not imply a different point architecture. These predictions do not provide game-level intervals or a calibrated joint score distribution.

| League | Season | Games | Correct / incorrect | Accuracy | Calibration error ↓ | Margin MAE / RMSE ↓ | Total MAE / RMSE ↓ | Total bias |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| NBA | 2025 | 1,248 | 811 / 437 | 64.98% | 0.030820 | 11.207 / 14.362 | 14.919 / 18.655 | +1.836 |
| NBA | 2026 | 1,249 | 846 / 403 | 67.73% | 0.030582 | 11.445 / 14.619 | 15.510 / 19.383 | +2.663 |
| NCAA men | 2025 | 5,758 | 4,168 / 1,590 | 72.39% | 0.014386 | 9.005 / 11.524 | 13.021 / 16.708 | -2.017 |
| NCAA men | 2026 | 5,749 | 4,138 / 1,611 | 71.98% | 0.023588 | 9.174 / 11.627 | 13.796 / 17.499 | -1.889 |
| NCAA women | 2025 | 5,280 | 4,022 / 1,258 | 76.17% | 0.024878 | 9.732 / 12.284 | 12.693 / 16.043 | +0.051 |
| NCAA women | 2026 | 5,621 | 4,286 / 1,335 | 76.25% | 0.022670 | 9.712 / 12.323 | 12.717 / 16.115 | +0.503 |

## Equivalent-game sportsbook MARKET comparisons

The basketball recipe is each full-cohort historical selection, evaluated on its exact MARKET-matched subset. Positive Δ means basketball log loss is worse. Unavailable means no admitted matched events. Larger recent validation cohorts do not create earlier training history.

| League | Horizon | Season | Matched games | Basketball log loss ↓ | Raw MARKET log loss ↓ | Δ basketball − MARKET |
|---|---:|---:|---:|---:|---:|---:|
| NBA | T−60m | 2025 | 9 | 0.603386 | 0.504146 | +0.099240 |
| NBA | T−60m | 2026 | 16 | 0.645276 | 0.656242 | -0.010966 |
| NBA | T−1440m | 2025 | 54 | 0.632887 | 0.592672 | +0.040214 |
| NBA | T−1440m | 2026 | 55 | 0.579081 | 0.581003 | -0.001922 |
| NCAA men | T−60m | 2025 | 0 | Unavailable | Unavailable | Unavailable |
| NCAA men | T−60m | 2026 | 1,143 | 0.577570 | 0.567127 | +0.010444 |
| NCAA men | T−1440m | 2025 | 0 | Unavailable | Unavailable | Unavailable |
| NCAA men | T−1440m | 2026 | 515 | 0.577081 | 0.567106 | +0.009975 |
| NCAA women | T−60m | 2025 | 149 | 0.430101 | 0.421845 | +0.008256 |
| NCAA women | T−60m | 2026 | 143 | 0.490909 | 0.501340 | -0.010431 |
| NCAA women | T−1440m | 2025 | 7 | 0.547079 | 0.613316 | -0.066237 |
| NCAA women | T−1440m | 2026 | 3 | 0.259975 | 0.195901 | +0.064073 |

Learned MARKET-only and integrated classifiers still lack the required chronological training support. No threshold was relaxed. No league establishes a qualified model advantage. Women’s T−60 rich logistic loses to MARKET in 2025 and improves in 2026; both paired intervals include zero. The enlarged men’s 2026 cohort still lacks an earlier validation-year comparison.

### Venue-separated exchange benchmark status

| Venue | Admitted historical events | Qualified executable current quotes | Status |
|---|---:|---:|---|
| Kalshi | 0 | 0 | Contract, timing and execution evidence incomplete |
| Polymarket US | 0 | 0 | Contract, timing and execution evidence incomplete |
| Polymarket international | 0 | 0 | Contract, timing and execution evidence incomplete |

Displayed page prices are not bid/ask histories or fills. Fees, depth, side direction, settlement and decision-time availability require separate evidence. No exchange trading backtest or basketball bankroll is admitted.

## T−24h remains a separate experiment

New opponent-adjustment arms were declared only for T−60. T−24h retains its earlier families; no T−60 improvement transfers to it.

| League | Season | Probability selection | Games | Log loss ↓ | Brier ↓ |
|---|---:|---|---:|---:|---:|
| NBA | 2025 | Strength logistic · 15 | 1,248 | 0.611916 | 0.212384 |
| NBA | 2026 | Strength logistic · 15 | 1,249 | 0.602852 | 0.207425 |
| NCAA men | 2025 | Combined logistic · 53 | 5,758 | 0.530536 | 0.179163 |
| NCAA men | 2026 | Combined logistic · 53 | 5,749 | 0.533917 | 0.180852 |
| NCAA women | 2025 | Combined logistic · 53 | 5,280 | 0.463813 | 0.153941 |
| NCAA women | 2026 | Combined logistic · 53 | 5,621 | 0.468392 | 0.156247 |

## Forward monitoring is separate from historical selection

B003 verified the exact 110 previously issued B002 rows: all pending, none quarantined or settled. It issued 110 additional rows spanning the same 61 distinct future games. These are later forecast versions, not 122 independent games. Every new row remains an early outlook before its declared lock, with zero qualified contemporary MARKET probabilities and NO_BET status. Prospective accuracy, proper scores and profit are unavailable until verified outcomes arrive. Current-season retrospective rows are excluded from selection and prospective claims.

## Reproducibility and limits

The public command checks cohort identities, calibration-bin arithmetic, pooled scoring, new-versus-reused unit accounting and the protected current-season boundary. It recreates these tables without private records or estimator execution. B003 has 60 new real estimator units, 156 byte-verified imported units and 232 cumulative unique basketball units. Its 22.10 active minutes are an observed owner result. [B004 subsequently executed and stopped at its public-request ceiling](BASKETBALL_B004_EXECUTION.md); no challenger was promoted, and B003 remains the latest fully completed real modeling release.
