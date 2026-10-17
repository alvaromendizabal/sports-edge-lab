# Model card — NFL and NCAAF

Evidence cutoff: **October 17, 2026, 23:08:14 UTC**, V060 return. [Overview](../README.md) · [Data](DATA_READINESS.md) · [Roadmap](RESEARCH_ROADMAP.md)

## Intended use and accepted models

These models support retrospective sports forecasting research and prospective experiment preparation. They are not approved live wagering systems. No profitability, causal player value, full-distribution accuracy or market-beating performance is established.

| Track | Accepted version | Targets / family | Inputs |
| --- | --- | --- | --- |
| NFL | V047 | Home win given no tie: regularized logistic regression. Home-minus-away margin and total: ridge regression. | 16 team-history features. |
| NCAAF | V048R1 | The same three targets and families. | 60 features, including opponent-adjusted drive efficiency. |

The foundation includes Elo, recent points scored/allowed, recent margin and total, games of history, rest, venue and season information. College adds four efficiency-history coverage fields and 40 raw/opponent-adjusted home/away offense/defense measures: yards/play, TDs/drive, turnovers/drive, plays/drive and yards/drive. Some foundation FBS indicators are constant in the NFL population.

Regularization is fixed (`C=1` for logistic, `alpha=20` for ridge); scaling is fitted only inside the training partition. Current point predictions are not cover/over probabilities or a joint score distribution.

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

Source records: [latest V060 execution](status/football_v060/summary.json), [V060 metrics](status/football_v060/metrics.json), [preserved V059 execution](status/football_v059/summary.json), [V059 metrics](status/football_v059/metrics.json), [preserved V058 execution](status/football_v058/summary.json), [V058 metrics](status/football_v058/metrics.json), [preserved V057 evidence](status/football_v057/summary.json) and [scorecard evidence](demo/evidence.json). The owner return archives contain fuller prediction-level diagnostics and model manifests; public aggregate evidence does not replace them.


## Next decision

Keep NFL V047 and college V048R1 as accepted research references. The tested V060 native configurations did not qualify; a new library is not the next information mechanism. V061 is prepared, not executed: four cached FBS parser cases, plus a separate public ESPN capture for 15 current finals capped at 40 public attempts and zero paid calls. Two additional historical representations are locally verified (12/14 locally; accepted AWS remains 10/14). The NFL representation has 52 features, with 24 planned linear/XGBoost fits. The [public method and 23 no-fit tests](../modeling/football_v061/README.md) verify construction, not predictive quality.

[Feature strategy](FEATURE_STRATEGY.md) prioritizes football mechanism, decision-time validity, conservative denominators and matched controls. Tracking/video, sequence and larger neural methods remain contingent on useful data and a testable hypothesis. No breakthrough, prospective edge or production promotion is established.
