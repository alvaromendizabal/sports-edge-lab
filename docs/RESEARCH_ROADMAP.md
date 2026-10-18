# Research roadmap — evidence before complexity


## Current evidence — V065 complete, V066 prepared

V065 finished at **2026-10-18 02:02:55 UTC** after one confirmed CFBD capture: **11,405 source rows across 489 games**. Strict validation retains **393 games: 291 FBS versus FBS and 102 declared opponent-context games**. Against all 455 primary games, **308 match, 81 disagree and 66 lack accepted comparisons**. The 49 missing strict-FBS comparisons are quarantined source games, not missing downloads. No model inputs were replaced; FBS60 remains blocked.

**99 invalid rows affect 82 quarantined games**. Another 324 source rows across 14 games are retained raw but excluded by the unchanged canonical completion snapshot. New source observation, canonical completion and model-input freshness remain separate contracts. [Actual V065 evidence](status/football_v065/README.md).

All six previously issued NFL forecast records remain pending for two games; 186 abstentions are preserved. V065 made zero real fits, new forecasts or promotions. **495 runtime tests and 2,743 independent audit checks passed.** The verified minimum tally is **24 accepted / 12 failed / two stopped executions; 11 accepted / one failed modeling runs; 386 completed real fits**.

**V066 is prepared, not executed:** cached source-clock adjudication, exact FBS16 reconstruction/readiness, 12 fixed linear fits against cached strict-FBS60 controls, and coverage/uncertainty evidence. It permits **zero provider calls and zero new live forecasts**. A frozen 1% operational noninferiority margin must pass development and exposed evaluation with sufficient paired-block support; no automatic promotion. Final package verification remains pending. [V066 preparation](status/football_v066/README.md).

Earlier sections preserve their dated observations. Neither a successful capture nor prepared fallback establishes prospective skill or wagering readiness.

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
| V063 cached repair and serving | Are selected repairs and saved models reproducible? | Three cached repairs; 1,247 predictions reproduce; 195 stale-input abstentions. | Preserve successful repairs and exact parity. |
| V064 current reconstruction | Can genuine current inputs support eligible immutable issuance? | Six NFL forecast records issued for two games; 186 abstentions; zero fits. | Preserve original issuance; FBS drive freshness remains blocked. |
| V065 independent source comparison | Is a fresh CFBD feed compatible with the complete primary contract? | 393 normalized games; 308 exact primary matches, 81 disagreements, 66 missing comparisons. All six original NFL records remain pending. | No automatic input substitution; keep quarantine and source clocks. |
| V066 operational fallback | Can score/schedule features reduce drive-feed dependence with acceptable predictive risk? | Prepared only: 12 fixed linear fits, zero provider calls or new forecasts. | Frozen 1% noninferiority and coverage/readiness comparison; no automatic promotion. |

## Immediate next work: V066 operational fallback

V065 completed the authorized current capture, but source compatibility remains incomplete. Missing accepted FBS comparisons are quarantined data, not an invitation to repeat downloads. Four workstreams address validity and operational coverage:

1. Adjudicate cached clock/period inconsistencies without inventing authoritative corrections.
2. Verify exact FBS16 score/schedule feature parity and current readiness, separately from drive freshness.
3. Run at most 12 fixed strict-FBS linear fits on AWS against cached strict-FBS60 predictions, with training-only preprocessing and unchanged chronological origins.
4. Report matched primary/secondary scores, paired uncertainty, coverage and original-forecast accounting in an executed return.

The frozen 1% operational noninferiority margin must hold on pooled development and already-exposed evaluation, including the paired blocked upper bound with sufficient support. Exposed gains cannot rescue failed development. No provider calls, new live forecasts or automatic promotion. Final package checks and owner execution remain pending. [V066 preparation](status/football_v066/README.md).

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
