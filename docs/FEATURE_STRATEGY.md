# Feature strategy and framework status

[Project overview](../README.md) · [Model card](MODEL_CARD.md) · [Data readiness](DATA_READINESS.md) · [Research roadmap](RESEARCH_ROADMAP.md)

The forecasting target is NFL and **FBS-versus-FBS** win probability, point margin and game total. The most useful next feature is one that contributes information available at the actual decision time, remains reliable across seasons and improves a controlled comparison. An additional library or more columns is not automatically new information.

## What has actually been implemented

| Method / framework | Verified project status | Interpretation |
| --- | --- | --- |
| scikit-learn logistic regression / ridge | Accepted NFL V047 and NCAAF V048R1 research references | Interpretable, regularized baselines; no demonstrated market advantage. |
| scikit-learn histogram gradient boosting | 36 verified fits: 24 early V047/V048R1 and 12 V058 | These tested configurations did not qualify a replacement. This is not an XGBoost, LightGBM or CatBoost execution. |
| scikit-learn multilayer perceptron | V058 completed 24 NFL/NCAAF neural fits; exact FBS evaluation slices retained | A real neural network, but neither PyTorch nor TensorFlow was used. The fixed configurations performed poorly. |
| NumPy/SciPy Gaussian team-state filter | V059 completed 16 joint fits | Static/dynamic offense-defense research; all six task development gates failed. |
| XGBoost | V060 completed 24 and V061 completed 12 native CPU fits | No candidate/task qualified under the fixed representation and gates. |
| LightGBM | V060 completed 24 native CPU fits | No candidate/task qualified. |
| CatBoost | V060 completed 24 native CPU fits | No candidate/task qualified; the numerical benchmark did not test a new categorical representation. |
| PyTorch | No verified execution yet | Candidate framework for an explicit neural mechanism, with regularization and validation controls. |
| TensorFlow | No verified execution yet | Alternative framework, not independent evidence of a better model. |

Boosting implementations differ in tree construction, categorical handling and regularization; they must not be relabeled as interchangeable completed work. Neural frameworks likewise provide software capabilities, not proof of superior forecasts. A framework benchmark must report exact versions, architecture/objective, preprocessing, stopping rules, seeds, resource use and results on the same games.

## Prioritized information and representations

This is a research priority order, not an assertion that every candidate feature is already available or predictive.

| Priority | Feature family | Football mechanism | Current evidence and required gate |
| --- | --- | --- | --- |
| 1 | Timely opponent-adjusted offense/defense and pace | Separates team strength from opponent difficulty and scoring opportunity. | Existing game/drive history supports this. V059's FBS total result is encouraging on exposed seasons but failed development uncertainty. Test richer representations only with frozen controls. |
| 2 | Confirmed starter / QB participation uncertainty | A different expected quarterback can change offensive efficiency and uncertainty. | Last-observed QB history exists; upcoming starter and report timing remain unverified. Represent uncertainty, never infer the starter from the target game's actual plays. |
| 3 | Availability weighted by expected role and replacement | Missing high-snap players should matter differently from unused roster players. | Snap/roster identities and availability captures exist unevenly. Exact player/team/season joins and pre-decision publication/observation are prerequisites. |
| 4 | Situation-aware efficiency | Early-down success, explosive plays, pressure/sack tendency, red-zone conversion and possession efficiency can separate mechanisms hidden by final scores. | Derive from exact cached PBP with documented denominators and opponent adjustment. Upstream EPA/CPOE model vintages must be known before historical use. No full-season aggregate may contain its target. |
| 5 | Roster continuity and college transitions | Transfers, recruiting, coaching changes and graduation may explain preseason and early-season changes. | Requires season-specific membership, effective dates and conservative sparse-team priors. Current rosters cannot stand in for earlier information. |
| 6 | Decision-time environment and scheduling | Rest, travel, venue/roof, wind and temperature forecasts can affect pace, efficiency and totals. | Rest/venue basics exist. Forecast vintages, location matching and roof status require validation; realized weather is not a pregame forecast. |
| 7 | Timestamped market information | Prices summarize information held by other forecasters and market participants. | Existing odds provide a benchmark and possible declared market-aware inputs. Exact horizon, margin removal and executable-price availability must be stated; the closed V056 blend is not silently reopened. |
| Conditional | Tracking trajectories and aligned video | Spatial interactions may support coverage, route, pressure and separation models. | Access, alignment and permitted use remain unconfirmed. They are not necessary for the next tabular/state experiment. |

The order may change after a new error analysis. Record the reason for the change; do not turn it into a search for whichever feature looks strongest on an already-exposed evaluation period.

## What the recent experiments taught us

- **V057:** QB continuity explained most of the observed total-point gain; extra rate features did not pass the full comparison against that control.
- **V058:** additional tabular capacity did not fix the representation. The tested neural models had worse probability and point errors; poor generalization is observed, while a causal diagnosis such as overfitting needs learning curves and further diagnostics.
- **V059:** changing latent team strength improved over the static state control. FBS total MAE also improved on exposed 2024–2025, but the development uncertainty gate failed. Preserve this as an exploratory lead, not a promoted model.
- **V060:** native XGBoost, LightGBM and CatBoost did not qualify against accepted and matched linear references. Small exposed CatBoost gains were insufficient; native libraries do not substitute for new information.
- **V061:** 24 situation-feature fits completed; all six candidate/task development decisions failed. Some new inputs influence predictions, but that did not establish incremental accuracy. The 2026 linear win improvement is small-sample monitoring evidence, not a promotion.

## Next bounded hypothesis: V062 loss alignment, prepared

V061's 52-feature neutral-situation representation has now been tested. The [public feature method](../modeling/football_v061/README.md) still provides construction tests, while the separate [actual result](status/football_v061/README.md) records 24 completed fits and no qualification. Close that fixed branch without selecting a favorable exposed feature subset.

V062 changes only LightGBM's point-loss objective from L2 to L1, keeping exact V060 16-field NFL / 60-field FBS inputs, version 4.7.0, all seeds 6001 and the remaining configuration. It prepares **16 margin/total fits** and reuses accepted, same-scope linear and same-feature L2 controls. Win models are unchanged. L1 targets a conditional median for MAE evaluation, not expected points, a score distribution or profitability. The objective mismatch is a hypothesis to test, not an established explanation of earlier failure.

**V062 is prepared, not executed.** It includes no feature/objective grid or extra reference fits. The declared gain, paired-uncertainty, RMSE and development-stability gates remain binding. [Prepared scope](status/football_v062/README.md).

V060/V061 grouped permutation used 2023 development data only. Correlated feature groups can substitute; sensitivity is not causal player/team value or a universal ranking of future predictive information. Upcoming starter and availability observations remain potentially useful but require exact identity and trustworthy pre-decision timestamps.

## Required experiment design

1. Fix the cohort, target, decision horizon, accepted reference and baseline with equivalent features.
2. Add one declared information/representation change or a bounded family comparison; record what is actually new.
3. Fit preprocessing, imputation, category vocabularies and any feature selection inside each training partition.
4. Use chronological validation; do not let generic random validation or automatic early stopping leak future structure.
5. Report log loss and Brier for win probabilities; MAE, RMSE and bias for points; calibration and appropriate distribution metrics; paired uncertainty and subgroup coverage.
6. Preserve all attempts and negative findings. Previously exposed historical seasons are not untouched tests.
7. Require a frozen forward-recorded trial before claiming a deployable edge. Source-time validity and predictive quality are separate gates.

## Data repair versus predictive improvement

V059 accepted eight regulation-drive repairs. V060 captured all 14 selected official-school pages and validated ten secondary representations. V061 added two validated cached representations; two remain unaccepted. Original ESPN-source repairs from this secondary-source work remain zero. Newly captured data was not inserted into the frozen native benchmark, so source validation cannot explain an artificial model gain.

V060 also verified four semantic changes among six NFL downloads and reconciled 15 cached FBS finals against team/player boxes. Boxes alone do not establish current drive/PBP coverage. V061 captured zero current summaries after a persisted ESPN robots HTTP 403. Prepared V062 instead names 17 independent official targets: at most 14 HTML drive closures and three PDF text-only captures, capped at 40 requests / 100 MB, zero ESPN or paid-provider use. Historical FCS records remain declared context; no standalone FCS acquisition or modeling effort is part of this strategy.

## Framework documentation

Official references checked October 17, 2026: [XGBoost](https://xgboost.readthedocs.io/en/stable/), [LightGBM](https://lightgbm.readthedocs.io/en/stable/), [CatBoost](https://catboost.ai/docs/en/), [PyTorch](https://docs.pytorch.org/docs/stable/index.html) and [TensorFlow/Keras](https://www.tensorflow.org/api_docs/python/tf/keras). These document capabilities; they do not establish installed versions, completed project experiments or expected sports performance.
