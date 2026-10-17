# Model card — NFL and NCAAF

Evidence cutoff: **October 17, 2026, 21:35:36 UTC**, V057 return. [Overview](../README.md) · [Data](DATA_READINESS.md) · [Roadmap](RESEARCH_ROADMAP.md)

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

No neural-network experiment has completed as of this cutoff. V058 is the next fixed benchmark: NFL HGB and a small multilayer perceptron on the 36-feature QB representation, plus a college MLP on the accepted 60-feature table. It is prepared work, not a new achieved score or accepted model. Existing college HGB evidence is reused rather than refitted.

## Evaluation design and exposure

V057 development folds evaluate 2022 after training through 2021 and 2023 after training through 2022. The exposed 2024–2025 evaluation trains through 2023. The 2026 monitoring fold trains through 2025. Model coefficients are fixed within each fold; declared released history updates between games.

All these evaluation periods have been examined across experiments. A new version does not create a new untouched test. Confidence intervals are descriptive paired season-week bootstraps, not a correction for repeated model selection. Fewer than eight blocks means no asserted interval. A future prospective protocol must be frozen before a confirmatory claim.

## Accepted models against the available market

2024–2025 paired-price cohorts; lower is better for log loss, Brier and MAE.

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

## V057: historical quarterback ablation

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
- FBS plus opponents is the college scope; this is not a complete all-division football database.
- Accepted college models do not contain a validated college player-history layer.
- Market and model information horizons are not always matched.
- Tracking/video access and permitted ML use are not confirmed.
- No held-out prospective test, serving SLO, ongoing calibration monitoring or live wagering approval exists.

Source records: [sanitized V057 execution evidence](status/football_v057/summary.json), [metrics](status/football_v057/metrics.json) and [scorecard evidence](demo/evidence.json). The owner return archives contain fuller prediction-level diagnostics and model manifests; public aggregate evidence does not replace them.
