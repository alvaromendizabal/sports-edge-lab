# Research roadmap — evidence before complexity

[Overview](../README.md) · [Models](MODEL_CARD.md) · [Data readiness](DATA_READINESS.md)

The objective is original, reproducible football forecasting with demonstrable incremental information. Model sophistication, download volume and retrospective score movement are not substitutes for that evidence.

## Relevant disciplines and their obligations

| Discipline | Concrete obligation in this project |
| --- | --- |
| Football analytics and player valuation | Use possession-, opponent- and player-aware representations with valid denominators. Separate last-observed participation from upcoming lineups. |
| Bayesian and hierarchical statistics | Pool sparse observations, retain sample sizes and model changing strength. Label fixed pseudocount shrinkage accurately. |
| Probabilistic forecasting | Evaluate proper scores, calibration, uncertainty and sharpness. Match point, interval and distribution metrics to actual outputs. |
| Temporal ML and experimental design | Train on the past, control ablations, lock development decisions and disclose evaluation exposure. |
| Sports-market econometrics | Compare information-matched prices and distinguish prediction quality, market calibration and executable economic value. |
| Causal inference | Avoid interpreting selected QB changes or injuries as randomized interventions. Prediction is not causal player value. |
| Decision science | Define horizon, utility, risk, coverage and abstention before claiming decision benefit. |
| Reliable ML and data engineering | Preserve exact identity, source lineage, time validity, compatible checkpoints and auditable failures. |

## Experiment ledger

| Branch | Question | Verified outcome | Decision |
| --- | --- | --- | --- |
| V047 NFL foundation | Can team history support interpretable forecasts? | Logistic/ridge baselines accepted; earlier HGB configuration did not replace them. | Keep reference predictions. |
| V048R1 college efficiency | Does opponent-adjusted drive history improve the foundation? | 60-feature linear models accepted; HGB configuration did not qualify. | Keep reference predictions. |
| V050 NGS | Do lagged public NGS summaries add useful signal? | Negative/inconclusive under tested representation. | Close exact branch; retain source data. |
| V055 recovered drives | Does the tested recovered-drive representation improve forecasts? | Negative/inconclusive. | Do not silently change accepted source semantics. |
| V056 market complement | Does combining our forecasts and market prices add value? | 48 completed fits; no task qualified. | Close fixed combination branch. |
| V057 QB history | Does historical QB performance add beyond continuity and team history? | 24 completed fits; all development gates failed. | No promotion; preserve histories for a materially different test. |
| V058 nonlinear benchmark | Do fixed nonlinear models extract useful interactions from existing features? | 36 completed fits; all nine candidate/task qualifications failed. | No promotion; close these fixed configurations. |
| V059 FBS repair and dynamic teams | Does changing latent offense/defense improve joint forecasts beyond a static control? | 16 joint fits complete; eight FBS repairs accepted; all six development qualifications failed. | Keep accepted references; preserve the exposed FBS-total lead without promotion. |
| V060 source gaps and native boosting | Can source updates and controlled native boosters add value? | 84 fits completed; all 18 candidate/task qualifications failed. Ten secondary sources validated; four selected cases remain. | Keep accepted references; prioritize new information and cached parser validation. |
| V061 neutral-situation NFL history | Do early-down pass/run histories add beyond accepted team features? | 24 fits complete; all six qualifications failed. Two cached repairs accepted; current capture stopped on HTTP 403. | Close the fixed branch; preserve accepted models and the provider stop. |
| V062 point-loss alignment | Does directly targeting the median improve MAE without unacceptable RMSE loss? | 16 fits complete; NFL total passes development but fails exposed evaluation. 13 current drive cases validate; four selected gaps remain. | No promotion; close the objective-only branch. |
| V063 serving and prospective record | Can accepted forecasts be served with exact parity and immutable pre-decision evidence? | In preparation; zero new research fits and provider calls planned. | Cache repairs, serving parity, shadow forecasts or explicit abstentions; no quality claim yet. |

## Immediate next work: V063 engineering continuation

V062 is complete: 16 controlled L1 fits, one development qualification, zero exposed qualifications, and no promoted replacement. Its 13 new current secondary drive cases are separate from the frozen model feature table and have conservative October 18, 16:02–17:34 UTC availability.

Four bounded workstreams now take priority:

1. Repair only provable cached parser issues, preserving quarantines and denied-provider controls.
2. Verify accepted-model serving parity against pinned historical inputs and predictions.
3. Record an immutable prospective shadow forecast or abstention with exact model, source, observation, decision and eligibility evidence. No late/backfilled forecast may count as prospective.
4. Execute and retain engineering evidence separately from model-quality results.

V063 is in preparation and plans **zero new research fits and zero provider calls**. These steps do not certify profitable deployment, exhaustive feed coverage or confirmed tracking/video rights. [Actual V062 outcome](status/football_v062/README.md) · [Feature strategy](FEATURE_STRATEGY.md).

## Lessons retained from V059

V059 runtime-verified eight FBS repairs, preserving 33 explicit overtime rows and frozen accepted features. Sixteen static/dynamic joint Gaussian fits then completed. The dynamic state model improved over the static control, but no task passed all development requirements against accepted predictions.

The FBS total's 1.77% exposed gain is an exploratory lead. Development paired uncertainty crossed zero, and 2026 monitoring was slightly worse. Do not reopen the identical specification through unbounded tuning. The joint model now supplies actual Gaussian CRPS/NLL and interval diagnostics; broad overcoverage and negative-score mass remain explicit limitations.

The method was inspired by [Glickman and Stern (1998)](https://www.tandfonline.com/doi/abs/10.1080/01621459.1998.10474084), not an exact reproduction. [V059 actual evidence](status/football_v059/README.md), [public state core](../modeling/football_v059/README.md) and [V058 nonlinear results](status/football_v058/README.md) remain reviewable.

## Subsequent decisions

| Evidence | Next action |
| --- | --- |
| A new candidate passes frozen development gates | Freeze a prospective forward-recorded trial; passing retrospectively does not establish a deployable edge. |
| Native boosters, situation features and objective-only branches fail — observed in V060–V062 | Keep accepted references; close those fixed branches. Build parity and prospective evidence before another claim of improvement. |
| Starter or availability uncertainty limits predictions | Capture prospective lineups with exact identity and pre-decision timestamps; never infer starters from target outcomes. |
| A distribution has poor calibration or unrealistic support | Investigate a predeclared scoring-process model with proper scoring rules and explicit dependence. |
| Tracking/video access is confirmed | Verify license, population, alignment and target relevance before a separate multimodal or sequence project. |

Sequence, graph, full hierarchical player and multimodal models remain unimplemented or access-blocked. The existence of a suitable architecture is a hypothesis, not evidence that it will improve this data regime.

## Research anchors

These primary sources guide mechanisms and validation; no published performance is transferred to this project.

- [Gneiting, Making and Evaluating Point Forecasts](https://arxiv.org/html/0912.0902v2): match the evaluation loss to the intended mean or quantile functional.
- [LightGBM 4.7.0 objectives](https://lightgbm.readthedocs.io/en/v4.7.0/Parameters.html): L1/MAE versus L2 objectives; no performance promise.
- [nflWAR](https://arxiv.org/abs/1802.00998): multilevel player analysis from public play-by-play and uncertainty estimation.
- [nflfastR guide](https://nflfastr.com/articles/beginners_guide.html): play-by-play fields and football-valid handling.
- [TrueSkill 2](https://www.microsoft.com/en-us/research/publication/trueskill-2-improved-bayesian-skill-rating-system/): hierarchical skill modeling inspiration, not a direct implementation claim.
- [Forecasting: Principles and Practice](https://otexts.com/fpp3/toolbox.html): forecast evaluation and temporal validation.
- [scikit-learn probability calibration](https://scikit-learn.org/stable/modules/calibration.html): proper scores versus calibration diagnostics.
- [Causal Inference: What If](https://miguelhernan.org/whatifbook): prediction versus intervention and selected processes.
- [Feast point-in-time joins](https://github.com/feast-dev/feast/blob/master/docs/getting-started/concepts/point-in-time-joins.md): feature availability at historical decisions.
- [The ML Test Score](https://research.google/pubs/the-ml-test-score-a-rubric-for-ml-production-readiness-and-technical-debt-reduction/): testable production-readiness gaps.
