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
| V058 nonlinear benchmark | Do fixed nonlinear models extract useful interactions from existing features? | Prepared; no actual V058 result yet. | Owner execution required before any performance claim. |

## Immediate next experiment: V058

Four compatible workstreams: input/evidence validation, fixed family benchmarks, chronological comparison with cached references, and an executed research report with a next-decision record.

- **NFL:** histogram gradient boosting and a small multilayer perceptron on V057's 36-feature QB table. Compare against accepted team-only predictions and the same-feature linear QB reference, so a gain can be attributed more carefully.
- **NCAAF:** a small multilayer perceptron on the accepted 60-feature table. Preserve the previously completed college HGB result instead of repeating that configuration.
- **Scope:** three tasks × four chronological folds × three track/family combinations = **36 maximum new real fits**. No new source requests or accepted-baseline refits.
- **Interpretation:** 2022/2023 development, exposed 2024/2025 diagnostics and 2026 monitoring remain previously examined evidence. Family comparison is not a fresh prospective validation.
- **Gate:** the frozen executable specification controls acceptance. Do not choose a family from the exposed period, retune a failed result, or claim production readiness from a retrospective improvement.

The frozen implementation and fixture instructions live in [modeling/football_v058](../modeling/football_v058/README.md). This document describes the research question; executable tests/configuration define exact parameters and stop conditions.

## After the benchmark

| Result | Next action |
| --- | --- |
| Nonlinear family improves reliably under the declared gates | Freeze it for a prospective, forward-recorded trial. Confirm feature availability and monitor calibration/coverage. |
| Nonlinear family fails | Treat complexity as an unsuccessful intervention on this representation. Prioritize new information or a different representation. |
| Poor QB identity or lineup coverage dominates errors | Improve prospective starter/availability observations; do not infer historical starters from target outcomes. |
| Team-strength drift dominates errors | Test a bounded dynamic offense/defense model with opponent adjustment and explicit state uncertainty. |
| Full score distribution becomes the target | Design a joint or distributional model, then add CRPS, interval scores and dependence diagnostics. |
| Tracking/video access is confirmed | Verify license, population, alignment and target relevance before any multimodal or sequence project. |

Advanced architectures should follow a verified mechanism: sequence models for ordered events, graph models for interaction structure, hierarchical models for sparse changing players, or multimodal models for aligned video and trajectories. None is currently an accepted Sports Edge Lab model.

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
