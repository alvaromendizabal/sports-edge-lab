> Historical publication through V065. For the October 25, 2026 research bank and current qualification boundaries, read the [current model card](MODEL_CARD_CURRENT.md). The dated content below is preserved as lineage.

# Model card — NFL and NCAAF


## Current evidence — V065 complete, V066 prepared

V065 finished at **2026-10-18 02:02:55 UTC** after one confirmed CFBD capture: **11,405 source rows across 489 games**. Strict validation retains **393 games: 291 FBS versus FBS and 102 declared opponent-context games**. Against all 455 primary games, **308 match, 81 disagree and 66 lack accepted comparisons**. The 49 missing strict-FBS comparisons are quarantined source games, not missing downloads. No model inputs were replaced; FBS60 remains blocked.

**99 invalid rows affect 82 quarantined games**. Another 324 source rows across 14 games are retained raw but excluded by the unchanged canonical completion snapshot. New source observation, canonical completion and model-input freshness remain separate contracts. [Actual V065 evidence](status/football_v065/README.md).

All six previously issued NFL forecast records remain pending for two games; 186 abstentions are preserved. V065 made zero real fits, new forecasts or promotions. **495 runtime tests and 2,743 independent audit checks passed.** The verified minimum tally is **24 accepted / 12 failed / two stopped executions; 11 accepted / one failed modeling runs; 386 completed real fits**.

**V066 is prepared, not executed:** cached source-clock adjudication, exact FBS16 reconstruction/readiness, 12 fixed linear fits against cached strict-FBS60 controls, and coverage/uncertainty evidence. It permits **zero provider calls and zero new live forecasts**. A frozen 1% operational noninferiority margin must pass development and exposed evaluation with sufficient paired-block support; no automatic promotion. Final package verification remains pending. [V066 preparation](status/football_v066/README.md).

Earlier sections preserve their dated observations. Neither a successful capture nor prepared fallback establishes prospective skill or wagering readiness.

Predictive-score cutoff: **October 18, 2026**, V062 return; operational/source evidence updated through V065. [Overview](../README.md) · [Data](DATA_READINESS.md) · [Roadmap](RESEARCH_ROADMAP.md)

## Intended use and accepted models

These models support retrospective sports forecasting research and prospective experiment preparation. They are not approved live wagering systems. No profitability, causal player value, full-distribution accuracy or market-beating performance is established.

| Track | Accepted version | Targets / family | Inputs |
| --- | --- | --- | --- |
| NFL | V047 | Home win given no tie: regularized logistic regression. Home-minus-away margin and total: ridge regression. | 16 team-history features. |
| NCAAF historical reference | V048R1 | Logistic/ridge; historically trained on mixed FBS/opponent targets. Retained for retrospective comparisons, not a strict-FBS deployment claim. | 60 features, including opponent-adjusted drive efficiency. |
| FBS versus FBS shadow control | V060 | Logistic/ridge trained only on FBS-versus-FBS targets. Unpromoted; current serving remains blocked by primary-drive freshness. | 60 features; declared prior-opponent context remains separate. |

The foundation includes Elo, recent points scored/allowed, recent margin and total, games of history, rest, venue and season information. College adds four efficiency-history coverage fields and 40 raw/opponent-adjusted home/away offense/defense measures: yards/play, TDs/drive, turnovers/drive, plays/drive and yards/drive. Some foundation FBS indicators are constant in the NFL population.

Regularization is fixed (`C=1` for logistic, `alpha=20` for ridge); scaling is fitted only inside the training partition. Current point predictions are not cover/over probabilities or a joint score distribution.

## V062 — completed objective-only point comparison

V062 completed **16 LightGBM L1 fits** on exact V060 inputs and target cohorts, with version 4.7.0, seeds 6001 and other parameters fixed. Every fit completed 200 iterations. Accepted, matched linear and L2 references were reused without refitting. No win model was fitted. These are conditional-median point forecasts, not expected scores or a distribution.

| Track | Task | Phase | Games | Accepted | Matched linear | L2 LightGBM | L1 LightGBM |
| --- | --- | --- | --- | --- | --- | --- | --- |
| NFL | margin | 2022–2023 development | 569 | 9.728097 | 9.728097 | 9.957677 | 9.824034 |
| NFL | margin | 2024–2025 exposed | 570 | 10.198375 | 10.198375 | 10.155027 | 10.118940 |
| NFL | margin | 2026 monitor | 80 | 9.898554 | 9.898554 | 9.958589 | 9.738635 |
| NFL | total | 2022–2023 development | 569 | 10.881346 | 10.881346 | 10.864426 | 10.715334 |
| NFL | total | 2024–2025 exposed | 570 | 10.332147 | 10.332147 | 10.416418 | 10.436805 |
| NFL | total | 2026 monitor | 80 | 11.980695 | 11.980695 | 12.389521 | 12.223035 |
| NCAAF | margin | 2022–2023 development | 1568 | 12.821899 | 12.829299 | 13.327795 | 13.227576 |
| NCAAF | margin | 2024–2025 exposed | 1606 | 12.819829 | 12.868194 | 13.193786 | 13.174680 |
| NCAAF | margin | 2026 monitor | 336 | 12.916027 | 12.924678 | 13.692153 | 13.747658 |
| NCAAF | total | 2022–2023 development | 1568 | 13.101301 | 13.113400 | 13.300096 | 13.294700 |
| NCAAF | total | 2024–2025 exposed | 1606 | 13.093919 | 13.094981 | 13.117648 | 13.057386 |
| NCAAF | total | 2026 monitor | 336 | 12.577538 | 12.610560 | 12.762425 | 12.705872 |

**NFL totals passed development; all four tasks failed exposed qualification. No model qualified for prospective advancement.** NFL-total development MAE improved 1.53% versus accepted, paired interval [−0.335385, −0.000286]; exposed MAE worsened 1.01%, interval [−0.059323, +0.273938]. The development upper bound is only barely negative and carries no multiplicity guarantee. NFL margin's 0.78% exposed gain and FBS total's 0.28% gain are below the declared threshold; their earlier gates also failed. Sparse 2026 gains cannot rescue a rejected branch.

All point scores, secondary diagnostics, empirical residual intervals and exhaustive subgroup counts recompute. No source/feature/label changes explain the controlled L1/L2 comparison. The audit verified **8,187 numerical/source checks**, 238 runtime tests and 16 real fits. Model/data success remains separate: 13 current secondary drive cases validated, while four selected gaps remain. [V062 summary](status/football_v062/summary.json) · [All scores and gates](status/football_v062/metrics.json).

## V061 — completed situation-feature experiment

V061 completed **24 NFL fits**: linear and XGBoost, three targets, four chronological origins, using the same 52 features. The new representation adds neutral early-down passing/rushing measures, opponent adjustment and coverage to the accepted 16 columns. It produced **zero qualified candidates**. No college model was fitted and accepted references are unchanged.

| NFL output / period | Games | Accepted | New linear | XGBoost |
| --- | ---: | ---: | ---: | ---: |
| Win log loss, development 2022–2023 | 567 | 0.642625 | 0.650862 | 0.646976 |
| Margin MAE, development 2022–2023 | 569 | 9.728097 | 9.788678 | 9.913976 |
| Total MAE, development 2022–2023 | 569 | 10.881346 | 10.964025 | 10.965131 |
| Win log loss, exposed 2024–2025 | 569 | 0.629830 | 0.635270 | 0.632613 |
| Win Brier, exposed 2024–2025 | 569 | 0.220274 | 0.222847 | 0.220771 |
| Margin MAE, exposed 2024–2025 | 570 | 10.198375 | 10.200384 | 10.165203 |
| Total MAE, exposed 2024–2025 | 570 | 10.332147 | 10.351248 | 10.521609 |
| Win log loss, monitoring 2026 | 79 | 0.656959 | 0.637836 | 0.666043 |

Every candidate has worse pooled development primary loss. The exposed XGBoost margin gain is 0.325%, with paired interval **[-0.220054, +0.151492] points**. XGBoost total is worse by 0.189462 points, interval **[+0.019987, +0.374905]**. The linear monitoring win gain has only six week blocks, so no interval is asserted; failed development remains binding.

Better ECE alone did not establish better probabilities: development linear ECE improved while Brier and AUC worsened. Permutation importance shows some new features affect predictions, not that they add reliable skill. Training trajectories and controlled learning curves are absent, so underfitting/overfitting causation remains unproved. V060/V061 XGBoost comparisons also change seeds as well as features.

Independent checks recomputed **11,411 numeric/logical assertions**, verified accepted prediction identity and retained unknown publication times. Present return artifacts were checked; 79 omitted manifest paths, including 72 model artifacts, remain unverified remotely. Runtime receipts record 295 tests and 12 synthetic fits, distinct from 24 real fits. [Actual summary](status/football_v061/summary.json) · [Exact metrics/gates](status/football_v061/metrics.json) · [Source stop and repairs](status/football_v061/acquisition_completion.json).

## V060 — completed native boosting with matched controls

V060 completed **84 fits**: 24 each for native XGBoost, LightGBM and CatBoost, plus 12 fresh college linear controls. NFL used the 16-feature accepted representation; FBS used 60 inherited team/drive features. New college target rows were FBS-versus-FBS, with declared prior-opponent context retained. The accepted college reference was mixed-cohort trained; the newly fitted linear control isolates that target-cohort change.

| Exposed 2024–2025 output | Games | Accepted | Matched linear | XGBoost | LightGBM | CatBoost |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| NFL win log loss | 569 | 0.629830 | 0.629830 | 0.632433 | 0.631679 | 0.627749 |
| NFL win Brier | 569 | 0.220274 | 0.220274 | 0.220500 | 0.220497 | 0.218489 |
| NFL margin MAE | 570 | 10.198375 | 10.198375 | 10.163072 | 10.155027 | 10.141178 |
| NFL total MAE | 570 | 10.332147 | 10.332147 | 10.470488 | 10.416418 | 10.447318 |
| FBS win log loss | 1,606 | 0.554682 | 0.555883 | 0.568727 | 0.567087 | 0.572301 |
| FBS win Brier | 1,606 | 0.189517 | 0.190069 | 0.193999 | 0.193494 | 0.195465 |
| FBS margin MAE | 1,606 | 12.819829 | 12.868194 | 13.205397 | 13.193786 | 13.285842 |
| FBS total MAE | 1,606 | 13.093919 | 13.094981 | 13.139566 | 13.117648 | 13.079862 |

**All 18 candidate/task development qualifications failed; no candidate qualified for prospective advancement.** A smaller exposed error is not sufficient: the fixed comparison requires meaningful gain, paired uncertainty and secondary/stability guards against both references. The benchmark did not use a configuration sweep or evaluation-driven early stopping. All 72 boosters completed 200 rounds.

NFL CatBoost win log loss improved only **0.33%** on exposed seasons; paired difference **[-0.012107, +0.008092]** spans zero. Brier improved to 0.218489 from 0.220274 while ECE worsened to 0.044289 from 0.023591, so different probability diagnostics tell different parts of the story. Its development loss was worse. NFL CatBoost margin improved 0.56% exposed with a zero-crossing interval; FBS CatBoost total improved only 0.11% exposed and worsened on development and 2026 monitoring.

These scores do not diagnose underfitting versus overfitting: the return lacks the training losses and learning curves needed for that distinction. The six NFL and seven FBS 2026 week blocks are too few for the declared paired-interval rule, so current-monitoring uncertainty remains unavailable rather than falsely precise.

The implementation now has actual native-library results: XGBoost CPU 3.4.1, LightGBM 4.7.0 and CatBoost 1.2.10 in the returned environment. PyTorch and TensorFlow remain unexecuted. None of these names supplies additional football information or guarantees improvement.

The audit passed **32,105 numerical checks**, 186 runtime tests and 84 fit records. Execution took **360.053 seconds**; estimated compute was **$0.048407** at the stated $0.484/hour rate, excluding startup/idle, storage and requests. This is not a total AWS bill.

The audit outcome is **PASS_WITH_REPORTING_ERRATA**: inherited readiness counters incorrectly retained zero calls, 14 remaining gaps and older freshness/feature descriptions. Authoritative runtime evidence records 32 public HTTP attempts, 10 secondary representations and four remaining selected cases. Model scores and accepted predictions were preserved; the original return was not edited. [Summary](status/football_v060/summary.json) · [Exact metrics](status/football_v060/metrics.json) · [Reporting corrections](status/football_v060/readiness_errata.json).

## Preserved V059 joint-score state experiment

V059 completed **16 joint fits**: two tracks × static/dynamic arms × four chronological partitions. Each fit emits win, margin and total outputs. Both state arms update from released earlier results; the static control has zero process drift, not zero posterior learning. Fixed Gaussian priors and observation assumptions are research choices, not fitted hyperparameter optimality.

| Exposed 2024–2025 output | Games | Accepted | Static | Dynamic |
| --- | ---: | ---: | ---: | ---: |
| NFL win log loss | 569 | 0.629830 | 0.661325 | 0.628622 |
| NFL win Brier | 569 | 0.220274 | 0.234728 | 0.219318 |
| NFL margin MAE | 570 | 10.198375 | 10.708147 | 10.142102 |
| NFL total MAE | 570 | 10.332147 | 10.613079 | 10.333307 |
| FBS vs FBS win log loss | 1,606 | 0.554682 | 0.626822 | 0.565083 |
| FBS vs FBS win Brier | 1,606 | 0.189517 | 0.219659 | 0.191477 |
| FBS vs FBS margin MAE | 1,606 | 12.819829 | 14.474232 | 12.982906 |
| FBS vs FBS total MAE | 1,606 | 13.093919 | 13.596402 | 12.862187 |

**No task qualified on development.** FBS total MAE improved 1.77% on the exposed cohort, with paired difference interval **[-0.439300, -0.036196] points**. The corresponding development interval was **[-0.292177, +0.035513]**; its uncertainty gate failed. The 2026 monitoring comparison also worsened slightly: dynamic **12.599326** versus accepted **12.577538**, 336 games. Exposed significance cannot override the frozen development decision.

College state models train and evaluate only FBS-versus-FBS; the accepted college reference was historically trained on mixed FBS/opponent rows. V059 accepted eight FBS regulation-drive repairs, but those secondary aggregates were **not inserted into model features**. It preserved accepted predictions and frozen targets.

### Distribution diagnostics are now actual evidence

| Dynamic total distribution, exposed 2024–2025 | NFL | FBS vs FBS |
| --- | ---: | ---: |
| Gaussian CRPS, lower better | 7.484517 | 9.288099 |
| Gaussian marginal NLL, lower better | 4.029242 | 4.261727 |
| Nominal 80% coverage, observed | 87.37% | 90.91% |
| 80% mean width, points | 40.7391 | 54.3274 |
| Nominal 95% coverage, observed | 97.37% | 99.00% |
| 95% mean width, points | 62.3051 | 83.0865 |

These broad, overcovering intervals do not establish well-calibrated uncertainty. Coverage must be interpreted with width, interval score, CRPS and NLL. The Gaussian model permits negative scores; mean upper bounds on either team being negative are **4.34% NFL / 8.08% FBS**, not exact joint probabilities. Scores are not silently truncated. Accepted point-only models have no implied comparable joint density.

Independent inspection passed **18,509 numerical checks**, 85 runtime tests, 16 input-cache hash checks and all 16 actual fits. The run took **47.568 seconds**; estimated compute was **$0.006395** at the stated $0.484/hour assumption, excluding startup/idle, storage and requests. No providers were called. [Actual summary](status/football_v059/summary.json) · [Exact scores, gates and distributions](status/football_v059/metrics.json) · [Repair completion](status/football_v059/repair_completion.json).

## Complexity already tested

Histogram gradient boosting is not absent from the project: **36 verified real fits** cover 24 early V047/V048R1 fits and 12 NFL V058 fits. Development win log loss favored the linear models: NFL 0.642625 versus HGB 0.664903; college adjusted features 0.510625 versus HGB 0.530834. This evidence rejected those particular configurations, not the entire boosting family.

**V058 completed 36 real fits:** 12 NFL HGB fits on the 36-feature QB representation and 24 MLP fits across NFL (36 features) and NCAAF (60 features). HGB used 100 boosting iterations, at most 15 leaves and depth five. The MLP used 32- and 16-unit tanh hidden layers, fixed 200 Adam epochs and training-only input/target scaling. This single-seed benchmark did not use random validation or early stopping. No college HGB was refitted.

All nine candidate/task development qualifications failed; no model was promoted. Every reported MLP completed its 200 epochs. A completed but poor experiment is negative evidence, not proof that the model family is fundamentally unsuitable.

## Preserved V058 nonlinear results

Future college predictions and headline evaluation target **FBS versus FBS**. The historical accepted college model was fitted on the prior FBS-plus-opponents cohort; the FBS rows below are retrospective subgroup scores of those existing predictions, not a newly trained FBS-only model. FCS archives are preserved as history/context without new standalone FCS work.

| Track / task | Games | Accepted linear | HGB | MLP |
| --- | ---: | ---: | ---: | ---: |
| NFL win log loss | 569 | 0.629830 | 0.630947 | 1.147814 |
| NFL win Brier | 569 | 0.220274 | 0.220787 | 0.319519 |
| NFL margin MAE | 570 | 10.198375 | 10.131508 | 13.409790 |
| NFL total MAE | 570 | 10.332147 | 10.391866 | 14.403435 |
| FBS vs FBS win log loss | 1,606 | 0.554682 | Not refitted | 1.039290 |
| FBS vs FBS win Brier | 1,606 | 0.189517 | Not refitted | 0.275091 |
| FBS vs FBS margin MAE | 1,606 | 12.819829 | Not refitted | 15.669553 |
| FBS vs FBS total MAE | 1,606 | 13.093919 | Not refitted | 15.691994 |

These are exposed 2024–2025 cohorts. NFL HGB margin improved 0.656% over the accepted baseline; its paired loss-difference interval **[-0.261356, +0.133838] points** includes zero. The MLP's much worse log loss and Brier show that the additional capacity did not yield better probability forecasts in this test.

Independent inspection verified **23,053 numerical checks**, 36 actual fits, 66 runtime tests and zero provider calls. V058 took 82.178 seconds; its estimated compute cost was $0.011048 using the assumed $0.484/hour rate, excluding startup/idle, storage and requests. [Execution evidence](status/football_v058/summary.json) · [Exact metrics and FBS-only slices](status/football_v058/metrics.json).

## Evaluation design and exposure

The repeated development folds evaluate 2022 after training through 2021 and 2023 after training through 2022. The exposed 2024–2025 evaluation trains through 2023. The 2026 monitoring fold trains through 2025. Model coefficients are fixed within each fold; declared released history updates between games.

All these evaluation periods have been examined across experiments. A new version does not create a new untouched test. Confidence intervals are descriptive paired season-week bootstraps, not a correction for repeated model selection. Fewer than eight blocks means no asserted interval. A future prospective protocol must be frozen before a confirmatory claim.

## Historical accepted-model market comparison

2024–2025 paired-price cohorts; lower is better for log loss, Brier and MAE. **The college market cohort below retains the earlier mixed FBS/opponent scope and must not be relabeled FBS-only.** Its denominator differs from the 1,606-game FBS-only table above.

| Track | Task | Games | Accepted | Market |
| --- | --- | ---: | ---: | ---: |
| NFL | Win log loss | 458 | 0.626621 | 0.599903 |
| NFL | Win Brier | 458 | 0.218831 | 0.206467 |
| NFL | Margin MAE | 459 | 10.261325 | 9.821351 |
| NFL | Total MAE | 459 | 10.298856 | 10.036492 |
| NCAAF | Win log loss | 1,293 | 0.548974 | 0.523313 |
| NCAAF | Win Brier | 1,293 | 0.186787 | 0.176105 |
| NCAAF | Margin MAE | 1,411 | 13.034424 | 12.122785 |
| NCAAF | Total MAE | 1,411 | 12.905078 | 12.476435 |

These benchmarks use available matched quotes; a consensus price need not be executable. NFL quotes are later than the 24-hour feature cutoff. Matched college quotes precede the nominal one-hour decision, while the actual consumed historical features predate those quotes under the retrospective release assumption. This is not a controlled comparison at identical information horizons. ROI, closing-line value and profit cannot be inferred from these metrics. Tie exclusions and differing source coverage explain differing task denominators.

## Preserved V057 evidence: historical quarterback ablation

V057 completed **24/24 fits**, zero provider calls and zero promotions. It built 6,963 player/team/game records from 207,337 identified non-scramble dropbacks. Eight tied dominant-passer cases remain unknown.

The 28-feature control adds historical QB presence, participation share, switch frequency, sample count, recency and missingness to the 16-feature baseline. The 36-feature arm adds completion rate, net yards/dropback, sack rate and interception rate for each side. Up to eight earlier appearances within 365 days feed fixed 100-dropback-equivalent shrinkage toward earlier league averages. This is not a fitted Bayesian hierarchy. Sack attribution requires an actual passer ID; the code does not guess it from the dominant quarterback.

**Full exposed 2024–2025 cohort**, distinct from the market-matched table:

| Task | Games | Accepted V047 | Continuity control | QB performance |
| --- | ---: | ---: | ---: | ---: |
| Win log loss | 569 | 0.629830 | 0.637079 | 0.632309 |
| Win Brier | 569 | 0.220274 | 0.221178 | 0.218774 |
| Margin MAE | 570 | 10.198375 | 10.231769 | 10.184909 |
| Total MAE | 570 | 10.332147 | 10.217872 | 10.204592 |

The total model improved 1.23% over the baseline but only 0.13% over continuity. Its mean-loss-difference 95% interval versus baseline was **[-0.261712, +0.007661] points** and versus continuity **[-0.126992, +0.102501]**. Both include zero. All three development qualifications failed. The exact representation is therefore a valid negative/inconclusive result, not a promotion.

The win model's lower Brier but higher log loss illustrates why metrics must be reported together: it improved squared probability error while worsening the primary score, which penalizes confident errors differently. A secondary improvement does not rescue a failed frozen primary gate.

## Metric contract

| Output / question | Report |
| --- | --- |
| Win probability | Log loss, Brier, same-cohort Brier skill against declared references, reliability bins/counts/uncertainty and probability bias; AUC and accuracy as secondary diagnostics. |
| Margin / total point accuracy | MAE, RMSE, median and 90th-percentile absolute error, signed bias. |
| Prediction intervals | Residual-calibrated interval coverage/width/score plus V059 native Gaussian 80%/95% diagnostics; no automatic coverage guarantee under temporal drift. |
| Stability | Predeclared season, venue, prior-history coverage and college matchup slices, paired losses, block counts and uncertainty. Sparse groups do not support promotion claims. |
| Full predictive distribution | V059 joint Gaussian NLL and marginal Gaussian CRPS/NLL; explicit support assumptions and negative-score mass. Accepted point-only references have no implied joint density. |
| Economic decisions | Separate future executable-price protocol with costs, settlement, no-action rules, CLV, ROI, turnover and drawdown. Not established here. |

## Material limitations

- Source archives may be revised; original publication timestamps are often unknown. The 24-hour release assumption is retrospective, not verified historical availability.
- Last-observed quarterback identity is not a confirmed upcoming starter; injuries, benchings and transfers can invalidate the proxy.
- Earlier college training and market tables include FBS plus opponents. Future forecast/evaluation scope is FBS versus FBS; historical FCS context is retained without new standalone FCS work.
- Accepted college models do not contain a validated college player-history layer.
- Market and model information horizons are not always matched.
- Tracking/video access and permitted ML use are not confirmed.
- No held-out prospective test, serving SLO, ongoing calibration monitoring or live wagering approval exists.

Source records: [latest V062 execution](status/football_v062/summary.json), [V062 metrics](status/football_v062/metrics.json), [preserved V061 execution](status/football_v061/summary.json), [V061 metrics](status/football_v061/metrics.json), [preserved V060 execution](status/football_v060/summary.json), [V060 metrics](status/football_v060/metrics.json), [preserved V059 execution](status/football_v059/summary.json), [V059 metrics](status/football_v059/metrics.json), [preserved V058 execution](status/football_v058/summary.json), [V058 metrics](status/football_v058/metrics.json), [preserved V057 evidence](status/football_v057/summary.json) and [scorecard evidence](demo/evidence.json). The owner return archives contain fuller prediction-level diagnostics and model manifests; public aggregate evidence does not replace them.


## Next decision — V066 operational fallback

Keep NFL V047 and historical college V048R1 as accepted references. V060's strict-FBS60 shadow controls remain unpromoted and freshness-blocked. V065's independent source normalization did not establish complete equivalence and made no model-input replacement. Six original NFL forecast records remain pending; there is no prospective score yet.

V066 prepares a **16-feature strict-FBS score/schedule model** against the cached 60-feature control. Twelve fixed logistic/ridge fits span three targets and four chronological origins. The hypothesis is reduced operational dependence on a stale/invalid drive feed with at most 1% primary-loss degradation under frozen same-game development/exposed and paired-block checks. The model still needs valid current canonical information. Zero provider calls, new forecasts or automatic promotions are permitted.

Final V066 verification is pending and no V066 real fits are counted. A passing experiment would be a candidate for a separately frozen prospective test. No retrospective result, source capture or passing serving test establishes live wagering readiness. [Prepared contract](status/football_v066/README.md).
