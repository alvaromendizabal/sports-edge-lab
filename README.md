# Sports Edge Lab

**Football forecasting research with auditable data, controlled experiments and honest market comparisons.**

Sports Edge Lab develops NFL and NCAA football win probabilities, point-margin forecasts and game-total forecasts. The project connects source acquisition, player identity, historical feature construction, model evaluation and recoverable AWS execution. Basketball tracks share the infrastructure; football is the current modeling focus.

**Verified through October 17, 2026 · V060:** 346 completed real model fits; 10 of 14 selected FBS gaps now have validated official-school secondary representations, with four remaining. The native XGBoost/LightGBM/CatBoost benchmark completed 84 fits including fresh FBS linear controls. None of 18 candidate/task combinations qualified. Accepted NFL/NCAAF baselines remain unchanged; no market advantage or production promotion is established.

**College scope:** future forecasts and headline evaluation target **FBS versus FBS**. Historical FBS/FCS games remain archived and may provide declared opponent context; no standalone FCS acquisition or modeling work is planned.

[Model card](docs/MODEL_CARD.md) · [Data readiness](docs/DATA_READINESS.md) · [Architecture](docs/ARCHITECTURE.md) · [Research roadmap](docs/RESEARCH_ROADMAP.md) · [V060 completed evidence](docs/status/football_v060/README.md) · [Evidence scorecard](docs/demo/index.html)

## A two-minute review

| Reviewer question | Evidence |
| --- | --- |
| What is being predicted? | Home win conditional on no tie, home-minus-away margin, and combined points; separate models for NFL and NCAAF. |
| What is currently accepted? | NFL V047: 16 team-history features. NCAAF V048R1: 60 team-history and opponent-adjusted drive features. Regularized logistic/ridge models. |
| Is the history substantial? | The audited NFL modeling slice contains **498,285 play-by-play rows across 2016–2026**, covering 2,841 completed games. The previously highlighted 14,031 rows were only the current-season slice. The wider raw archive spans NFL **1999–2026** and ESPN college **2004–2026**, with **3.23 million** records in the latest selected annual ESPN files. These are raw source records, not deduplicated validated plays. |
| Why not just use a larger model? | V058 tested HGB/MLP, V059 dynamic score states and V060 native XGBoost/LightGBM/CatBoost. None qualified a replacement. Named frameworks and prioritized predictive information are distinguished in the [feature strategy](docs/FEATURE_STRATEGY.md). |
| What prevents overstated results? | Chronological fitting, exact same-game comparisons, training-only preprocessing, paired uncertainty, data-time caveats and explicit records of repeatedly examined evaluation seasons. |
| What is reproducible publicly? | Source, tests, execution contracts and sanitized evidence. Private/licensed raw data and credentials stay outside Git. Public fixtures test behavior; they do not reproduce private-data scores. |

## Results, not just downloads

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

Core team-level research is ready. NFL quarterback histories are auditable research features; they are **not confirmed future starters**. The audited FBS-versus-FBS canonical scope has **7,898 completed games**, with **7,895** in the frozen feature table. A newer existing capture contains **15 further FBS finals** with team/player boxes; their drive/PBP readiness remains to be checked. Frozen predictions are preserved.

V059 accepted eight regulation-drive repairs. V060 then validated official-school secondary representations for **10 of the remaining 14 selected games**. **Four remain** for parser/representation work; original ESPN-source gaps are not relabeled repaired. Six historical FBS/FCS context gaps remain deferred. Nine unresolved college availability rows, historical publication-time verification, upcoming starter availability and tracking/video entitlement remain open.

V060 also downloaded six changed NFL assets and confirmed four content changes; the refreshed current PBP still has 14,031 rows / 80 games, with no additional game IDs. The existing current college capture's 15 newer finals have exact team/player box checks; PBP/drive readiness remains separate. Inherited readiness counters were corrected from [authoritative capture evidence](docs/status/football_v060/acquisition_completion.json).

**Next — V061, prepared, not executed:** validate four cached FBS parser cases and capture public ESPN coverage for 15 newly final FBS games (at most 40 public attempts; zero paid calls). Two historical secondary representations are verified locally, bringing local coverage to 12/14; the accepted AWS result remains 10/14. Test NFL early-down pass/run history using 52 features and fixed linear/XGBoost controls (24 planned fits). [Public method and 23 no-fit tests](modeling/football_v061/README.md) · [Feature priorities](docs/FEATURE_STRATEGY.md). No live wagering readiness or profitability claim is made.


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
