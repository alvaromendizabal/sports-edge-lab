# Model card — NFL and NCAAF

Evidence cutoff: **October 17, 2026, 22:06:37 UTC**, V058 return. [Overview](../README.md) · [Data](DATA_READINESS.md) · [Roadmap](RESEARCH_ROADMAP.md)

## Intended use and accepted models

These models support retrospective sports forecasting research and prospective experiment preparation. They are not approved live wagering systems. No profitability, causal player value, full-distribution accuracy or market-beating performance is established.

| Track | Accepted version | Targets / family | Inputs |
| --- | --- | --- | --- |
| NFL | V047 | Home win given no tie: regularized logistic regression. Home-minus-away margin and total: ridge regression. | 16 team-history features. |
| NCAAF | V048R1 | The same three targets and families. | 60 features, including opponent-adjusted drive efficiency. |

The foundation includes Elo, recent points scored/allowed, recent margin and total, games of history, rest, venue and season information. College adds four efficiency-history coverage fields and 40 raw/opponent-adjusted home/away offense/defense measures: yards/play, TDs/drive, turnovers/drive, plays/drive and yards/drive. Some foundation FBS indicators are constant in the NFL population.

Regularization is fixed (`C=1` for logistic, `alpha=20` for ridge); scaling is fitted only inside the training partition. Current point predictions are not cover/over probabilities or a joint score distribution.

## Complexity already tested

Histogram gradient boosting is not absent from the project: **at least 24 verified early real fits** evaluated it across V047/V048R1. This is a verified early subset, not an exhaustive count of boosting fits across later experiments. Development win log loss favored the linear models: NFL 0.642625 versus HGB 0.664903; college adjusted features 0.510625 versus HGB 0.530834. This evidence rejected those particular configurations, not the entire boosting family.

**V058 completed 36 real fits:** 12 NFL HGB fits on the 36-feature QB representation and 24 MLP fits across NFL (36 features) and NCAAF (60 features). HGB used 100 boosting iterations, at most 15 leaves and depth five. The MLP used 32- and 16-unit tanh hidden layers, fixed 200 Adam epochs and training-only input/target scaling. This single-seed benchmark did not use random validation or early stopping. No college HGB was refitted.

All nine candidate/task development qualifications failed; no model was promoted. Every reported MLP completed its 200 epochs. A completed but poor experiment is negative evidence, not proof that the model family is fundamentally unsuitable.

## V058 results on the relevant college scope

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

V057 development folds evaluate 2022 after training through 2021 and 2023 after training through 2022. The exposed 2024–2025 evaluation trains through 2023. The 2026 monitoring fold trains through 2025. Model coefficients are fixed within each fold; declared released history updates between games.

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
| Prediction intervals | 80%/90% coverage, width and interval score; no automatic coverage guarantee under temporal drift. |
| Stability | Predeclared season, venue, prior-history coverage and college matchup slices, paired losses, block counts and uncertainty. Sparse groups do not support promotion claims. |
| Full predictive distribution | CRPS becomes relevant after a valid distribution is implemented. |
| Economic decisions | Separate future executable-price protocol with costs, settlement, no-action rules, CLV, ROI, turnover and drawdown. Not established here. |

## Material limitations

- Source archives may be revised; original publication timestamps are often unknown. The 24-hour release assumption is retrospective, not verified historical availability.
- Last-observed quarterback identity is not a confirmed upcoming starter; injuries, benchings and transfers can invalidate the proxy.
- Earlier college training and market tables include FBS plus opponents. Future forecast/evaluation scope is FBS versus FBS; historical FCS context is retained without new standalone FCS work.
- Accepted college models do not contain a validated college player-history layer.
- Market and model information horizons are not always matched.
- Tracking/video access and permitted ML use are not confirmed.
- No held-out prospective test, serving SLO, ongoing calibration monitoring or live wagering approval exists.

Source records: [latest V058 execution](status/football_v058/summary.json), [V058 metrics](status/football_v058/metrics.json), [preserved V057 evidence](status/football_v057/summary.json) and [scorecard evidence](demo/evidence.json). The owner return archives contain fuller prediction-level diagnostics and model manifests; public aggregate evidence does not replace them.


## Next hypothesis: V059, not yet executed

A fixed dynamic-versus-static joint Gaussian model will represent team offense/defense states and derive win, margin and total outputs. The planned comparison is 16 joint fits across two arms, two tracks and four folds; this is not 48 independent fit attempts. The NFL dynamic-strength literature, including [Glickman and Stern (1998)](https://www.tandfonline.com/doi/abs/10.1080/01621459.1998.10474084), motivates changing latent team strength. The proposed offense/defense and joint-output design is an extension inspired by that work, not an exact reproduction or a transferred performance claim.

V059 must first validate FBS scope and the prepared overtime-order repair. A local counterfactual does not establish a completed AWS repair or a better model. Accepted checkpoints and predictions remain preserved.
