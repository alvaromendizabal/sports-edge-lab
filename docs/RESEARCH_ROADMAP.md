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
| V060 source gaps and native boosting | Can verified source updates and controlled native boosters add value? | Prepared workstream; no V060 real result yet. | Freeze source/model boundaries and compare equivalent cohorts. |

## Immediate next experiment: V060

Four bounded workstreams address data quality and predictive modeling separately:

1. **Finite source capture:** investigate the 14 remaining FBS gaps through official school sources and changed current NFL assets. Reuse exact successful and existing six-hour captures. Shared provider-denial and HTTP-attempt records prevent repeated denied access. No CFBD, CBBD or odds acquisition belongs to this workstream.
2. **Source validation:** preserve received bytes, identity/provenance, observation/publication distinction and strict parsing. Unknown outcomes remain quarantined. New data is staged separately and does not retroactively mutate frozen model inputs.
3. **Equivalent-cohort native boosting:** 72 planned XGBoost/LightGBM/CatBoost fits across NFL 16-feature and college 60-feature representations, plus 12 freshly fitted FBS-only linear controls: **84 new fits**. NFL accepted-control predictions are reused. Fixed settings, no hyperparameter sweep and no automatic early stopping. New college training/evaluation rows are FBS-versus-FBS; existing declared opponent-context histories may still contain earlier FCS opponents.
4. **Complete evidence:** chronological task metrics, paired uncertainty, development-only grouped permutation importance, readiness and a reproducible research notebook. A permutation diagnostic is not causal feature importance.

The [V060 public scientific core](../modeling/football_v060/README.md) exposes native adapters and synthetic-only tests. The owner executes the full artifact in the existing AWS environment. Preparation is not execution; no V060 model score, data-repair success or hosted test result is claimed here. The 14-gap queue comprises six absent alternate-source games, five unknown positive-play drive outcomes and three current source updates. The six historical FBS/FCS context gaps remain deferred. Five targets have locally verified official-school secondary captures staged for runtime verification; they are not repairs to the original ESPN source or an accepted V060 outcome.

[Feature priorities and framework registry](FEATURE_STRATEGY.md) explain why reliable decision-time information matters more than a library name. XGBoost, LightGBM and CatBoost have no verified project result yet. PyTorch/TensorFlow are frameworks, not architectures; a larger network without a new information mechanism is not the current priority.

## Lessons retained from V059

V059 runtime-verified eight FBS repairs, preserving 33 explicit overtime rows and frozen accepted features. Sixteen static/dynamic joint Gaussian fits then completed. The dynamic state model improved over the static control, but no task passed all development requirements against accepted predictions.

The FBS total's 1.77% exposed gain is an exploratory lead. Development paired uncertainty crossed zero, and 2026 monitoring was slightly worse. Do not reopen the identical specification through unbounded tuning. The joint model now supplies actual Gaussian CRPS/NLL and interval diagnostics; broad overcoverage and negative-score mass remain explicit limitations.

The method was inspired by [Glickman and Stern (1998)](https://www.tandfonline.com/doi/abs/10.1080/01621459.1998.10474084), not an exact reproduction. [V059 actual evidence](status/football_v059/README.md), [public state core](../modeling/football_v059/README.md) and [V058 nonlinear results](status/football_v058/README.md) remain reviewable.

## Subsequent decisions

| Evidence | Next action |
| --- | --- |
| A new candidate passes frozen development gates | Freeze a prospective forward-recorded trial; passing retrospectively does not establish a deployable edge. |
| Native boosters fail on equivalent representations | Retain accepted references and close the fixed configurations. Prefer new verified information over more unbounded capacity. |
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
