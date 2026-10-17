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
| V061 neutral-situation NFL history | Do early-down pass/run histories add beyond accepted team features? | Planned, not executed; 24 fits. | Validate denominators/timing and compare fixed linear/booster controls. |

## Immediate next experiment: V061, planned

The next bounded work pairs cached historical parser validation and a finite current public capture with a new football representation. It does not repeat the native-library comparison.

- **Historical data:** validate four cached FBS parser cases. Two additional representations are verified locally (12/14 locally), while accepted AWS coverage remains 10/14 until the owner return is accepted. Original ESPN-source repairs remain zero.
- **Current data:** capture public ESPN data for 15 newly final FBS games, with at most 40 public attempts and zero CFBD/CBBD/odds usage. Preparation made zero new source calls. Downloaded pages and team/player boxes alone do not establish usable drive/PBP rows.
- **NFL features:** construct lagged early-down pass/run histories in neutral situations, with explicit denominators and source-time assumptions. Separate play-selection context from player/team causality.
- **Models:** 24 planned NFL fits using linear and one fixed XGBoost arm on 52 features across three targets and four chronological folds. Preserve accepted references. The [public feature method](../modeling/football_v061/README.md) has 23 no-fit checks; this is not model-performance evidence.
- **Evidence:** matched-cohort log loss/Brier, MAE/RMSE, uncertainty, stability and information-time gates. No live edge or breakthrough claim follows from a more detailed feature representation.

V061 has not executed. [Feature strategy](FEATURE_STRATEGY.md) prioritizes useful football information over library names. V060 actual native-library execution is documented in its [completed evidence](status/football_v060/README.md) and [public core](../modeling/football_v060/README.md). PyTorch/TensorFlow remain unexecuted.

## Lessons retained from V059

V059 runtime-verified eight FBS repairs, preserving 33 explicit overtime rows and frozen accepted features. Sixteen static/dynamic joint Gaussian fits then completed. The dynamic state model improved over the static control, but no task passed all development requirements against accepted predictions.

The FBS total's 1.77% exposed gain is an exploratory lead. Development paired uncertainty crossed zero, and 2026 monitoring was slightly worse. Do not reopen the identical specification through unbounded tuning. The joint model now supplies actual Gaussian CRPS/NLL and interval diagnostics; broad overcoverage and negative-score mass remain explicit limitations.

The method was inspired by [Glickman and Stern (1998)](https://www.tandfonline.com/doi/abs/10.1080/01621459.1998.10474084), not an exact reproduction. [V059 actual evidence](status/football_v059/README.md), [public state core](../modeling/football_v059/README.md) and [V058 nonlinear results](status/football_v058/README.md) remain reviewable.

## Subsequent decisions

| Evidence | Next action |
| --- | --- |
| A new candidate passes frozen development gates | Freeze a prospective forward-recorded trial; passing retrospectively does not establish a deployable edge. |
| Native boosters fail on equivalent representations — observed in V060 | Retain accepted references and close the fixed configurations. Test a bounded new information mechanism. |
| Starter or availability uncertainty limits predictions | Capture prospective lineups with exact identity and pre-decision timestamps; never infer starters from target outcomes. |
| A distribution has poor calibration or unrealistic support | Investigate a predeclared scoring-process model with proper scoring rules and explicit dependence. |
| Tracking/video access is confirmed | Verify license, population, alignment and target relevance before a separate multimodal or sequence project. |

Sequence, graph, full hierarchical player and multimodal models remain unimplemented or access-blocked. The existence of a suitable architecture is a hypothesis, not evidence that it will improve this data regime.

## Research anchors

These primary sources guide mechanisms and validation; no published performance is transferred to this project.

- [nflWAR](https://arxiv.org/abs/1802.00998): multilevel player analysis from public play-by-play and uncertainty estimation.
- [nflfastR guide](https://nflfastr.com/articles/beginners_guide.html): play-by-play fields and football-valid handling.
- [TrueSkill 2](https://www.microsoft.com/en-us/research/publication/trueskill-2-improved-bayesian-skill-rating-system/): hierarchical skill modeling inspiration, not a direct implementation claim.
- [Forecasting: Principles and Practice](https://otexts.com/fpp3/toolbox.html): forecast evaluation and temporal validation.
- [scikit-learn probability calibration](https://scikit-learn.org/stable/modules/calibration.html): proper scores versus calibration diagnostics.
- [Causal Inference: What If](https://miguelhernan.org/whatifbook): prediction versus intervention and selected processes.
- [Feast point-in-time joins](https://github.com/feast-dev/feast/blob/master/docs/getting-started/concepts/point-in-time-joins.md): feature availability at historical decisions.
- [The ML Test Score](https://research.google/pubs/the-ml-test-score-a-rubric-for-ml-production-readiness-and-technical-debt-reduction/): testable production-readiness gaps.
