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
| V059 FBS repair and dynamic teams | Does changing latent offense/defense improve joint forecasts beyond a static control? | Prepared; 16 joint fits planned, no V059 result yet. | Runtime-verify scope/repair, then evaluate the frozen comparison. |

## Immediate next experiment: V059

Four compatible workstreams: validate the FBS-only target and cached regulation-drive repair; fit fixed static/dynamic joint Gaussian team models; compare chronologically with accepted predictions; and produce complete uncertainty/readiness evidence.

- **Scope:** NFL plus FBS-versus-FBS prediction/evaluation. Preserve historical FCS opponent context without new standalone FCS work.
- **Data work:** verify eight locally recovered FBS games (16 team rows) in owner runtime. This would reduce in-scope drive gaps from 22 to 14; six historical mixed-context gaps are deferred. Three newer FBS finals remain absent from the frozen feature table.
- **Model question:** compare changing team offense/defense states with a static control. Each joint fit produces win, margin and total outputs; the planned queue is **16 joint fits = two arms × two tracks × four folds**, not 48 separate fits.
- **Research basis:** [Glickman and Stern (1998)](https://www.tandfonline.com/doi/abs/10.1080/01621459.1998.10474084) motivates dynamic latent strength for NFL forecasts. The offense/defense joint-output model is an inspired extension, not an exact replication or a performance transfer.
- **Evidence standard:** retain exposed-season labels, same-game controls, model uncertainty and proper scores. A candidate that fails development cannot be rescued by a favorable exposed result.

No V059 execution, accepted-model replacement, provider acquisition or fully resolved data state is claimed. The [local preparation evidence](status/football_v059/local_data_preparation.json) and current source/feature hashes remain distinct from a future AWS return. [Prepared V059 public core](../modeling/football_v059/README.md) and [completed V058 implementation](../modeling/football_v058/README.md) are retained for reproducibility.

## After the benchmark

| Result | Next action |
| --- | --- |
| Dynamic model improves reliably under the declared gates | Freeze it for a prospective, forward-recorded trial. Confirm feature availability and monitor calibration/coverage. |
| Dynamic model fails | Retain the static/accepted references and close the fixed dynamic specification. Prioritize verified information or a materially different representation. |
| Poor QB identity or lineup coverage dominates errors | Improve prospective starter/availability observations; do not infer historical starters from target outcomes. |
| Team-strength drift dominates errors | Test a bounded dynamic offense/defense model with opponent adjustment and explicit state uncertainty. |
| Full score distribution becomes the target | Design a joint or distributional model, then add CRPS, interval scores and dependence diagnostics. |
| Tracking/video access is confirmed | Verify license, population, alignment and target relevance before any multimodal or sequence project. |

Advanced architectures should follow a verified mechanism: sequence models for ordered events, graph models for interaction structure, hierarchical models for sparse changing players, or multimodal models for aligned video and trajectories. Neural networks and HGB have now been tested but were not promoted. Full hierarchical, sequence, graph and multimodal models remain unimplemented or access-blocked.

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
