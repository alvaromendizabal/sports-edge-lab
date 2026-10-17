# V057 independent return audit and prior nonlinear inventory

No real-data fitting, network, AWS calls, source edits or external mutations were performed. `audit_v057.py` independently recomputes the returned metrics and writes full-precision evidence to `v057_audit_metrics.json`; `prior_nonlinear_inventory.json` contains the exact 24 earlier tree-fit records and source-artifact bindings.

## Execution outcome

**SUCCESS / VALID_NEGATIVE_OR_INCONCLUSIVE.** V057 completed all four stages and **24/24 real fits**, with no accepted-model replacement, no production promotion and no task eligible for the prospective trial under its frozen gates.

- Started **2026-10-17 21:34:09.909067 UTC**, finished **21:35:36.995486 UTC**.
- Elapsed **87.089 seconds**. Estimated compute **$0.011709**, assuming $0.484/hour, excluding startup/idle, EBS/S3 and request charges.
- Zero baseline refits, sports-provider requests, odds credits, CFBD or CBBD requests.
- **88 present manifest files** pass exact byte count and SHA-256. **108 omitted manifest files** are AWS-only items; their contents are not independently verified by this compact-return audit.
- **575 independent arithmetic/selection checks pass**, including proper scores, discrimination, calibration error, point metrics, paired blocked CIs, development and exposed decision gates, interval coverage/width/score and exact market joins.
- Returned prediction tables: **1,705 validation game/task rows** and **1,948 exposed/monitor game/task rows**. Each row contains both experimental arms and the accepted-model reference.
- Updated verified-minimum ledger: **16 accepted / 12 failed / 2 stopped executions; 6 accepted modeling runs / 1 failed modeling run / 210 completed real fits**.

## What was tested

The baseline is the unchanged NFL V047 16-feature model. The continuity control adds 12 features (six per team) describing prior passer presence, dominant passer share, recent switching, history volume, recency and missingness. The 36-feature QB-values arm adds eight rate features (four per team): completion rate, net yards per non-scramble dropback, sack rate and interception rate.

The player is the last released prior-game dominant passer, not a confirmed upcoming starter. Features use up to eight prior appearances within 365 days and 100-dropback shrinkage to an expanding prior league mean. Historical publication timestamps remain unknown; kickoff +24-hour release and target kickoff −24-hour cutoff are explicit assumptions.

V057 is a regularized-linear feature ablation, not a neural network, a fully Bayesian player model or a causal QB-quality estimate.

## Development 2022–2023

Primary loss is log loss for win, MAE in points for margin/total. Lower is better.

| Task | N | Accepted V047 | Continuity control | QB values | QB vs accepted | QB vs control |
|---|---:|---:|---:|---:|---:|---:|
| Win | 567 | 0.642625 | 0.644785 | 0.654096 | +1.7850% | +1.4439% |
| Margin | 569 | 9.728097 | 9.643538 | 9.712899 | −0.1562% | +0.7192% |
| Total | 569 | 10.881346 | 10.831149 | 10.809332 | −0.6618% | −0.2014% |

No task achieved the required 1% improvement against both accepted and continuity controls. All candidate-versus-accepted development confidence intervals cross zero. Win deteriorated versus continuity; its paired interval is +0.000765 to +0.018260 log loss. The framework correctly declines promotion.

## Exposed 2024–2025

| Task | N | Accepted V047 | Continuity control | QB values | QB vs accepted | QB vs control |
|---|---:|---:|---:|---:|---:|---:|
| Win | 569 | 0.629830 | 0.637079 | 0.632309 | +0.3935% | −0.7488% |
| Margin | 570 | 10.198375 | 10.231769 | 10.184909 | −0.1320% | −0.4580% |
| Total | 570 | 10.332147 | 10.217872 | 10.204592 | **−1.2345%** | −0.1300% |

The most encouraging signal is total-points MAE: a 0.1276-point reduction versus the accepted model. However, the continuity control explains most of that improvement, leaving only 0.0133 points attributable to the added rate features. Both intervals cross zero:

- Total versus accepted: **−0.261712 to +0.007661 points**.
- Total versus continuity: **−0.126992 to +0.102501 points**.

This is a weak research signal, not an accepted gain. The development gates failed before viewing this exposed period, and the result does not justify retrospective gate changes.

The win metrics show a useful trade-off rather than a contradiction:

| Exposed win metric | Accepted | Continuity | QB values |
|---|---:|---:|---:|
| Log loss ↓ | 0.629830 | 0.637079 | 0.632309 |
| Brier ↓ | 0.220274 | 0.221178 | **0.218774** |
| ROC AUC ↑ | 0.694158 | 0.694892 | **0.701174** |
| Accuracy ↑ | **64.675%** | 64.148% | 64.148% |
| ECE10 ↓ | **0.023591** | 0.034597 | 0.041083 |

Brier and AUC improve while log loss and ECE deteriorate. The added representation can improve average squared probability error/ranking without improving the more tail-sensitive log score. This is why selection should retain multiple complementary metrics and a predeclared primary target, not choose whichever metric happens to look best afterward.

## Same-game market comparison

The earlier full-cohort figures must not be mixed with these smaller market-covered cohorts. Market snapshots also occur later than the −24-hour QB feature cutoff, so this is a tougher, unmatched-horizon benchmark rather than a clean same-information market test.

| Exposed task | N | Accepted V047 | QB values | Later market |
|---|---:|---:|---:|---:|
| Win log loss | 458 | 0.626621 | 0.624883 | **0.599903** |
| Margin MAE | 459 | 10.261325 | 10.268955 | **9.821351** |
| Total MAE | 459 | 10.298856 | 10.156380 | **10.036492** |

The QB arm remains worse than market for all three tasks. No ROI, closing-line-value, executable-price advantage or betting claim follows from these results.

## 2026 monitoring and intervals

The full 2026 cohort has 79 non-tie win games and 80 point-prediction games. There are only six season-week blocks; uncertainty bounds are correctly unavailable rather than asserted from insufficient blocks.

| Task | Accepted | QB values | QB relative change |
|---|---:|---:|---:|
| Win log loss | 0.656959 | 0.656440 | −0.0790% |
| Margin MAE | 9.898554 | 10.028860 | +1.3164% |
| Total MAE | 11.980695 | 12.054533 | +0.6163% |

The exposed total improvement does not repeat in this small monitoring sample. That limits enthusiasm but does not itself prove universal failure.

QB-values exposed interval diagnostics, using only prior 2022–2023 forward residuals:

| Task | 80% nominal coverage / width | 90% nominal coverage / width |
|---|---:|---:|
| Margin | **77.54% / 32.69 points** | **88.07% / 43.33 points** |
| Total | **81.40% / 33.60 points** | **90.35% / 44.29 points** |

Margin intervals under-cover. The empirical residual method explicitly has no guaranteed coverage under drift and is not a full conditional score distribution. Keep this as an actual observed limitation; do not describe the uncertainty output as fully calibrated.

## Data and implementation findings

- The source audit covers **498,285 PBP rows**, **207,337 identified non-scramble dropbacks**, **2,841 games** and **5,682 team-games**. Scrambles are excluded by definition; eight team-games have tied/no unique dominant passers and are left unknown.
- This is existing data being converted into an audited feature panel, not a fresh provider download. Both college feature rows and accepted NFL feature columns remain unchanged.
- No arithmetic, alignment or promotion-logic defect was found in this return. The previously noted durable-fit-budget and reporting-counter issues are fixed in the returned source.
- Missing historical publication times, 28 college games without any valid drive representation, nine college availability identity rows, confirmed upcoming QB status, full tracking/video access and fresh availability observations remain separate open issues.
- The current experiment closes this fixed QB-rate proxy as a promotion candidate. Keep the validated panel for future controlled representation tests; a negative model result does not invalidate correct source data.

## Previous nonlinear models: exact evidence

There have already been **24 actual histogram-gradient-boosting fits**: 12 in V047 on 16 foundation features and 12 in V048R1 on 60 opponent-adjusted features. Each count is two sports × three tasks × two chronological development seasons. All were development trials; no histogram model was selected for the exposed/monitor refits.

The actual PYZ SHA-256 values match those in the accepted return arguments. Both source artifacts specify:

`max_iter=100, max_leaf_nodes=15, max_depth=5, min_samples_leaf=30, learning_rate=0.05, l2_regularization=5.0, max_bins=63, early_stopping=False`.

Classifier for win, regressor for margin/total; seeds **4701** for V047 and **4801** for V048R1. No randomized internal early-stopping split. Exact per-fold records, Brier scores and feature lists are in `prior_nonlinear_inventory.json`.

Pooled 2022–2023 losses:

| Track/task | V047 linear, 16 features | V047 tree, 16 features | V048 adjusted linear, 60 features | V048 adjusted tree, 60 features |
|---|---:|---:|---:|---:|
| NFL win | 0.642625 | 0.664903 | 0.659755 | 0.646914 |
| NFL margin | 9.728097 | 9.977345 | 9.829839 | 9.844504 |
| NFL total | 10.881346 | 10.994865 | 10.918329 | 10.833009 |
| NCAAF win | 0.531640 | 0.535912 | **0.510625** | 0.530834 |
| NCAAF margin | 13.597322 | 13.634279 | **13.097950** | 13.430105 |
| NCAAF total | 13.496605 | 13.516445 | **13.082389** | 13.258503 |

The adjusted NFL tree's total loss is about 0.444% below accepted V047, below the frozen 1% threshold; it did not qualify. The college adjusted linear model clearly outperformed the tested tree. This evidence supports saying **one modest boosted-tree specification has been tested**, not that nonlinear modeling has been exhausted. No neural-model execution is evidenced by these accepted runs or V057.

## Decisive next experiment recommendation

1. **Test nonlinear capacity under a fixed feature comparison.** A regularized small neural MLP and a materially distinct, predeclared nonlinear tree/residual model are reasonable hypotheses. Use identical data/feature sets across those arms, training-only scaling, chronological train/evaluation, and cached same-feature linear controls where available. Do not confound adding QB features with changing the estimator.
2. **Reuse the completed tree trials.** Do not rerun the identical 60-feature HistGradientBoosting specification. Include its cached development predictions in the comparison. If introducing a new tree family/specification, state the mechanism it changes instead of an unstructured sweep.
3. **Match capacity to the effective sample size.** These game-level NFL training sets are roughly 1,600–2,800 observations and college several thousand, not hundreds of thousands of independent games. Millions of play rows do not become independent game-level labels. A compact regularized MLP is a fair neural baseline; a large transformer is not justified by this table alone.
4. **Keep time and uncertainty honest.** The existing seasons remain exposed; a winning retrospective challenger still requires frozen predictions on later outcomes. Do not optimize on market subsets or choose metrics post hoc. A neural positive result should later survive seed stability and calibration checks before promotion.
5. **Use a distributional/dynamic objective for the next substantive family, not complexity as a goal.** Partial pooling of offense/defense across teams and time, or a coherent score distribution, addresses sparse schedules, nonstationarity and win/margin/total consistency. Raw tracking/video access is not required for such work. Current QB rates are descriptive and do not replace confirmed pregame availability.

The best research interpretation is: core data is sufficient for controlled team-level model development; the current rates add limited useful signal, accepted models still trail the market, and a disciplined nonlinear comparison is warranted without claiming a breakthrough in advance.
