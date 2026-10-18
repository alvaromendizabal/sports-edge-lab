# Feature strategy and framework status


## Current evidence — V064 complete, V065 prepared

V064 finished at **2026-10-18 01:27:39 UTC**, issued **six immutable NFL forecast records for two games**, and retained **186 abstentions** (36 NFL and 150 FBS). The independent actual-return audit passed 3,937 checks; 356 runtime tests passed. Genuine NFL schedule observation and exact feature reconstruction enabled issuance. No outcome had matured at audit, so no prospective model-quality claim is established. Zero real fits and zero promotions preserve the 386-fit research history.

**Current minimum tally:** 23 accepted / 12 failed / two stopped execution runs; modeling 11 accepted / one failed. [Actual V064 evidence](status/football_v064/README.md).

The primary FBS drive vintage remains October 16, 18:15:25 UTC. Fresh canonical scores cannot refresh that separate input. A read-only comparison of owned CFBD caches found 2,888 drives across 124 games; **110 games** pass strict whole-game validation, of which **81 match** all primary metrics and **29 disagree**. Fourteen games remain quarantined after 19 invalid eligible rows. This is not equivalent full 455-game coverage, and no model input was replaced.

**V065 is tested and prepared, not executed:** one bounded existing-subscription CFBD drive request, strict source compatibility diagnostics, append-only settlement of already-issued forecasts, and an explicit dependency/readiness report. It makes no new model fits or forecasts. It reuses V064's canonical snapshot; later games absent from that snapshot remain archived raw and cannot enter normalized features until a separately verified canonical refresh. The final package passed 495 offline tests, failure/resume and idempotency checks. [V065 preparation](status/football_v065/README.md).

Earlier experiment sections retain their dated results. Neither V064 issuance nor V065 preparation changes the negative boosting/neural experiment conclusions or establishes betting readiness.

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
| LightGBM | V060 completed 24 L2/native fits; V062 completed 16 L1 point fits | V062 NFL totals qualified on development but failed exposed evaluation; no promotion. |
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

## Completed V062 objective alignment and next evidence work

V062 completed 16 LightGBM L1 point fits on exact V060 features, version 4.7.0, all seeds 6001 and unchanged non-objective settings. It reused accepted, same-scope linear and same-feature L2 controls. NFL totals passed development but failed exposed evaluation; no task qualifies for promotion. L1 is a conditional-median functional, not an expected score or scoring distribution. [Actual result](status/football_v062/README.md).

V063 is an engineering continuation with zero new research fits or provider calls: provable cached repairs, accepted-model serving parity, and immutable prospective shadow forecasts or explicit abstentions. Feature availability must precede decision time; source capture alone does not make a record eligible. No exposed-data feature selection or objective sweep is justified by V062's small isolated gains.

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

V060 also verified four semantic changes among six NFL downloads and reconciled 15 cached FBS finals against team/player boxes. Boxes alone do not establish current drive/PBP coverage. V061 captured zero current summaries after a persisted ESPN robots HTTP 403. V062 then captured 16 independent official sources and validated 13 current drive representations. Four selected gaps remain; both downloaded PDFs failed exact identity parsing, so zero verified PDF-text-only identities are claimed. Its ledger used 33 public attempts and no paid calls. Historical FCS records remain declared context; no standalone FCS acquisition or modeling effort is part of this strategy.

## Framework documentation

Official references checked October 17, 2026: [XGBoost](https://xgboost.readthedocs.io/en/stable/), [LightGBM](https://lightgbm.readthedocs.io/en/stable/), [CatBoost](https://catboost.ai/docs/en/), [PyTorch](https://docs.pytorch.org/docs/stable/index.html) and [TensorFlow/Keras](https://www.tensorflow.org/api_docs/python/tf/keras). These document capabilities; they do not establish installed versions, completed project experiments or expected sports performance.
