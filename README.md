# Sports Edge Lab

**Football forecasting research with auditable data, controlled experiments and honest market comparisons.**

Sports Edge Lab develops NFL and NCAA football win probabilities, point-margin forecasts and game-total forecasts. The project connects source acquisition, player identity, historical feature construction, model evaluation and recoverable AWS execution. Basketball tracks share the infrastructure; football is the current modeling focus.

**Verified through October 18, 2026 · V063:** **386 completed real fits**; **22 accepted / 12 failed / two stopped executions**. V063 repaired three cached games, verified 1,247 saved-model predictions and recorded 195 freshness/deadline abstentions, with zero live forecasts. All 15 selected current repair games and 13/14 historical repair games are represented; one denied-source gap remains. **V064 is prepared for current-input reconstruction and prospective shadow inference; it has not executed on AWS.**

**College scope:** future forecasts and headline evaluation target **FBS versus FBS**. Historical FBS/FCS games remain archived and may provide declared opponent context; no standalone FCS acquisition or modeling work is planned.

[Model card](docs/MODEL_CARD.md) · [Data readiness](docs/DATA_READINESS.md) · [Architecture](docs/ARCHITECTURE.md) · [Research roadmap](docs/RESEARCH_ROADMAP.md) · [V063 completed evidence](docs/status/football_v063/README.md) · [Evidence scorecard](docs/demo/index.html)

## A two-minute review

| Reviewer question | Evidence |
| --- | --- |
| What is being predicted? | Home win conditional on no tie, home-minus-away margin, and combined points; separate models for NFL and NCAAF. |
| What is currently accepted? | NFL V047: 16 team-history features. NCAAF V048R1: 60 team-history and opponent-adjusted drive features. Regularized logistic/ridge models. |
| Is the history substantial? | The audited NFL modeling slice contains **498,285 play-by-play rows across 2016–2026**, covering 2,841 completed games. The previously highlighted 14,031 rows were only the current-season slice. The wider raw archive spans NFL **1999–2026** and ESPN college **2004–2026**, with **3.23 million** records in the latest selected annual ESPN files. These are raw source records, not deduplicated validated plays. |
| Why not just use a larger model? | V058 tested HGB/MLP, V059 dynamic states, V060 native boosters and V061 NFL situation features. None qualified a replacement. Named frameworks and prioritized predictive information are distinguished in the [feature strategy](docs/FEATURE_STRATEGY.md). |
| What prevents overstated results? | Chronological fitting, exact same-game comparisons, training-only preprocessing, paired uncertainty, data-time caveats and explicit records of repeatedly examined evaluation seasons. |
| What is reproducible publicly? | Source, tests, execution contracts and sanitized evidence. Private/licensed raw data and credentials stay outside Git. Public fixtures test behavior; they do not reproduce private-data scores. |

## Latest controlled result

V062 held the features, library version, seeds and controls fixed while changing LightGBM's point objective from L2 to L1. The forecasts estimate conditional medians. Lower MAE is better.

| Task / period | Games | Accepted | Matched L2 | L1 candidate |
| --- | ---: | ---: | ---: | ---: |
| NFL total, development 2022–2023 | 569 | 10.881346 | 10.864426 | 10.715334 |
| NFL total, exposed 2024–2025 | 570 | 10.332147 | 10.416418 | 10.436805 |
| NFL margin, exposed 2024–2025 | 570 | 10.198375 | 10.155027 | 10.118940 |
| FBS total, exposed 2024–2025 | 1,606 | 13.093919 | 13.117648 | 13.057386 |

NFL totals passed all development rules but worsened on exposed data. The other small exposed gains did not satisfy the declared rules. **One development qualification, zero exposed qualifications, zero promotions.** These are repeatedly examined retrospective seasons. [Full V062 tables and acquisition outcome](docs/status/football_v062/README.md).

## Preserved V061 results

V061 added neutral-situation passing/rushing histories to the NFL inputs. The resulting 52-feature linear/XGBoost models completed all 24 fits; all six development decisions failed. Exposed 2024–2025 results are below; lower is better.

| NFL task | Games | Accepted | New linear | XGBoost |
| --- | ---: | ---: | ---: | ---: |
| Win log loss | 569 | 0.629830 | 0.635270 | 0.632613 |
| Win Brier | 569 | 0.220274 | 0.222847 | 0.220771 |
| Margin MAE | 570 | 10.198375 | 10.200384 | 10.165203 |
| Total MAE | 570 | 10.332147 | 10.351248 | 10.521609 |

The 0.33% XGBoost margin improvement is below the requirement and its interval crosses zero. The favorable 2026 linear win observation has only 79 games / six blocks and failed earlier qualification. **No promotion or market advantage is established.** [Exact V061 evidence](docs/status/football_v061/README.md).

### Preserved V060 comparison

V060 compared native boosters on fixed features and identical target cohorts. College includes a fresh FBS-only linear control; the older accepted college reference retains mixed-cohort training. These 2024–2025 seasons are exposed retrospective evaluation. Lower is better.

| Track / task | Accepted | Matched linear | XGBoost | LightGBM | CatBoost |
| --- | ---: | ---: | ---: | ---: | ---: |
| NFL win log loss | 0.629830 | 0.629830 | 0.632433 | 0.631679 | 0.627749 |
| NFL margin MAE | 10.198375 | 10.198375 | 10.163072 | 10.155027 | 10.141178 |
| NFL total MAE | 10.332147 | 10.332147 | 10.470488 | 10.416418 | 10.447318 |
| FBS win log loss | 0.554682 | 0.555883 | 0.568727 | 0.567087 | 0.572301 |
| FBS margin MAE | 12.819829 | 12.868194 | 13.205397 | 13.193786 | 13.285842 |
| FBS total MAE | 13.093919 | 13.094981 | 13.139566 | 13.117648 | 13.079862 |

NFL win has 569 games; NFL point targets 570; FBS targets 1,606. Small isolated gains did not pass the frozen development requirements. **Zero of 18 candidate/task combinations qualified**. This is negative evidence about the fixed configurations and representation, not a guarantee that another library or larger architecture will help.

[Full model card, Brier and uncertainty](docs/MODEL_CARD.md) · [Exact V060 metrics](docs/status/football_v060/metrics.json) · [Earlier state/distribution experiment](docs/status/football_v059/README.md).

## Engineering that supports the research

- **Data contracts:** pinned object hashes, schemas, exact game/team/player IDs, explicit coverage denominators and quarantined ambiguity.
- **Information contracts:** event, observation, publication and decision time remain distinct. Unknown historical publication timestamps stay unknown.
- **Controlled learning:** fixed folds and model configurations, ablations, cached baseline predictions and bounded real-fit accounting.
- **Recoverable execution:** one self-contained Python archive, offline gates before credentials, checkpoints, heartbeats, failure classification and one unique return bundle.
- **Broader evaluation:** log loss, Brier, calibration, AUC, MAE, RMSE, bias, tail errors, interval coverage/width and paired uncertainty.
- **Resource discipline:** reuse successful caches, separate provider quotas from AWS compute, and preserve failed attempts rather than silently restarting.

## What is ready—and what is not

Core team-level research is ready. NFL quarterback histories are auditable research features; they are **not confirmed future starters**. The audited FBS-versus-FBS canonical scope has **7,898 completed games**, with **7,895** in the frozen feature table. A newer existing capture contains **15 further FBS finals** with team/player boxes; 13 now have validated secondary drive representations; two remain. This does not establish complete PBP coverage. Frozen predictions are preserved.

V059 accepted eight regulation-drive repairs. V060 validated 10 selected official-school secondary representations; V061 validated two more from caches. **12/14 are now validated and two remain**; original ESPN-source gaps are not relabeled repaired. Six historical FBS/FCS context gaps remain deferred. Nine unresolved college availability rows, historical publication-time verification, upcoming starter availability and tracking/video entitlement remain open.

V060 also downloaded six changed NFL assets and confirmed four content changes; the refreshed current PBP still has 14,031 rows / 80 games, with no additional game IDs. The existing current college capture's 15 newer finals have exact team/player box checks; V061 captured zero of those 15 current summaries after the persisted ESPN denial. V062 used independent official-school sources and validated 13/15 current drive representations, with two remaining. The original provider stop and source-specific gaps remain. Inherited V060 readiness counters were corrected from [authoritative capture evidence](docs/status/football_v060/acquisition_completion.json).

**Next — V063, in preparation:** repair the remaining provable cached parser issues, verify serving parity for the accepted models, and record prospective shadow forecasts or explicit abstentions in an immutable ledger. This is an engineering step with **zero new research fits and zero provider calls**, not a new model promotion. New current features are conservatively available only from October 18, 16:02–17:34 UTC and require source/feature-contract validation before use. [Actual V062 evidence](docs/status/football_v062/README.md) · [Feature priorities](docs/FEATURE_STRATEGY.md).


The five-sport raw archive measured 101,035 in-scope content files / 17.39 GB at October 16, 23:30 UTC. This dated storage inventory is not a count of unique games, training rows or current model-ready examples. [Original inventory evidence](docs/status/content_inventory_20261016T2330Z.json).

## Review paths

| Focus | Start here |
| --- | --- |
| Modeling and experimental reasoning | [Model card](docs/MODEL_CARD.md) → [research roadmap](docs/RESEARCH_ROADMAP.md) |
| Data engineering and provenance | [Data readiness](docs/DATA_READINESS.md) → [source catalog](docs/DATA_CATALOG.md) |
| Systems and reliability | [Architecture](docs/ARCHITECTURE.md) → [V060 native booster core](modeling/football_v060/README.md) / [V059 state core](modeling/football_v059/README.md) / [V058 benchmark](modeling/football_v058/README.md) |
| Portfolio presentation | [Static evidence scorecard](docs/demo/index.html) → [review rubric](docs/REPOSITORY_REVIEW.md) |
| Historical acquisition decisions | [Preserved pre-modeling README](docs/history/README_PRE_MODELING_20261017.md) → [execution source versions](docs/EXECUTION_SOURCE_VERSIONS.md) |

The HTML scorecard is an offline, self-contained document. Open the downloaded file in a browser; GitHub's source viewer does not execute it. No live scores, betting recommendations or fabricated forecasts appear in the demo.

## Scope and boundaries

One repository, one `sports-edge-lab-dev` SageMaker space, one canonical private data lake in `us-west-2`. Tracks: [NFL](tracks/nfl/README.md), [NBA](tracks/nba/README.md), [NCAAF](tracks/ncaaf/README.md), [NCAAM](tracks/ncaam/README.md) and [NCAAW](tracks/ncaaw/README.md). ACB is excluded; CBBD remains stopped. Historical track plans and acquisition receipts retain their original dates and are superseded by the current model and readiness cards where they differ.

This repository demonstrates end-to-end forecasting research and engineering. It does not redistribute restricted source records, claim ownership of upstream data, equate public statistical summaries with tracking trajectories, or present retrospective results as prospective validation.
