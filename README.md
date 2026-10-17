# Sports Edge Lab

**Football forecasting research with auditable data, controlled experiments and honest market comparisons.**

Sports Edge Lab develops NFL and NCAA football win probabilities, point-margin forecasts and game-total forecasts. The project connects source acquisition, player identity, historical feature construction, model evaluation and recoverable AWS execution. Basketball tracks share the infrastructure; football is the current modeling focus.

**Verified through October 17, 2026 · V059:** 262 completed real model fits; eight accepted FBS data repairs; 14 FBS drive gaps remain. The latest static/dynamic score-state benchmark completed all 16 joint fits. None of its six task development qualifications passed. Accepted NFL/NCAAF baselines remain unchanged; no market advantage or production promotion is established.

**College scope:** future forecasts and headline evaluation target **FBS versus FBS**. Historical FBS/FCS games remain archived and may provide declared opponent context; no standalone FCS acquisition or modeling work is planned.

[Model card](docs/MODEL_CARD.md) · [Data readiness](docs/DATA_READINESS.md) · [Architecture](docs/ARCHITECTURE.md) · [Research roadmap](docs/RESEARCH_ROADMAP.md) · [V059 completed evidence](docs/status/football_v059/README.md) · [Evidence scorecard](docs/demo/index.html)

## A two-minute review

| Reviewer question | Evidence |
| --- | --- |
| What is being predicted? | Home win conditional on no tie, home-minus-away margin, and combined points; separate models for NFL and NCAAF. |
| What is currently accepted? | NFL V047: 16 team-history features. NCAAF V048R1: 60 team-history and opponent-adjusted drive features. Regularized logistic/ridge models. |
| Is the history substantial? | The audited NFL modeling slice contains **498,285 play-by-play rows across 2016–2026**, covering 2,841 completed games. The previously highlighted 14,031 rows were only the current-season slice. The wider raw archive spans NFL **1999–2026** and ESPN college **2004–2026**, with **3.23 million** records in the latest selected annual ESPN files. These are raw source records, not deduplicated validated plays. |
| Why not just use a larger model? | V058 completed HGB/MLP tests; V059 tested dynamic score states. Neither qualified a replacement. Named frameworks and prioritized predictive information are distinguished in the [feature strategy](docs/FEATURE_STRATEGY.md). |
| What prevents overstated results? | Chronological fitting, exact same-game comparisons, training-only preprocessing, paired uncertainty, data-time caveats and explicit records of repeatedly examined evaluation seasons. |
| What is reproducible publicly? | Source, tests, execution contracts and sanitized evidence. Private/licensed raw data and credentials stay outside Git. Public fixtures test behavior; they do not reproduce private-data scores. |

## Results, not just downloads

V059 tested joint Gaussian offense/defense states against a static control and accepted forecasts. Its 2024–2025 periods are exposed retrospective evaluation, not untouched tests. Lower is better.

| Track / task | Accepted linear | Static state | Dynamic state | Metric |
| --- | ---: | ---: | ---: | --- |
| NFL win | 0.6298 | 0.6613 | **0.6286** | Log loss; 569 games |
| NFL margin | 10.1984 | 10.7081 | **10.1421** | MAE, points; 570 games |
| NFL total | **10.3321** | 10.6131 | 10.3333 | MAE, points; 570 games |
| FBS vs FBS win | **0.5547** | 0.6268 | 0.5651 | Log loss; 1,606 games |
| FBS vs FBS margin | **12.8198** | 14.4742 | 12.9829 | MAE, points; 1,606 games |
| FBS vs FBS total | 13.0939 | 13.5964 | **12.8622** | MAE, points; 1,606 games |

The FBS total gain was **1.77%** on exposed seasons. Its development paired 95% difference interval **[-0.2922, +0.0355] points** crossed zero, and 2026 monitoring MAE was slightly worse than accepted (12.5993 versus 12.5775). It is an exploratory lead, not a qualified replacement. All six development qualifications failed.

V059 college candidates trained and evaluated only FBS-versus-FBS. The accepted college reference retains its earlier mixed FBS/opponent training. Native Gaussian CRPS, NLL and interval width/coverage are now reported; they reveal broad intervals and nonzero negative-score probability. [Full model card](docs/MODEL_CARD.md) · [Exact V059 metrics](docs/status/football_v059/metrics.json) · [Prior HGB/MLP results](docs/status/football_v058/README.md).

## Engineering that supports the research

- **Data contracts:** pinned object hashes, schemas, exact game/team/player IDs, explicit coverage denominators and quarantined ambiguity.
- **Information contracts:** event, observation, publication and decision time remain distinct. Unknown historical publication timestamps stay unknown.
- **Controlled learning:** fixed folds and model configurations, ablations, cached baseline predictions and bounded real-fit accounting.
- **Recoverable execution:** one self-contained Python archive, offline gates before credentials, checkpoints, heartbeats, failure classification and one unique return bundle.
- **Broader evaluation:** log loss, Brier, calibration, AUC, MAE, RMSE, bias, tail errors, interval coverage/width and paired uncertainty.
- **Resource discipline:** reuse successful caches, separate provider quotas from AWS compute, and preserve failed attempts rather than silently restarting.

## What is ready—and what is not

Core team-level research is ready. NFL quarterback histories are auditable research features; they are **not confirmed future starters**. The audited FBS-versus-FBS canonical scope has **7,898 completed games**, with **7,895** in the frozen feature table. A newer existing capture contains **15 further FBS finals** with team/player boxes; their drive/PBP readiness remains to be checked. Frozen predictions are preserved.

V059 runtime verification accepted **eight of 22 in-scope drive repairs**; **14 remain** (six absent alternate-source games, five unknown positive-play results and three current source updates). Five of the 14 now have locally validated official-school secondary captures staged for V060; runtime acceptance remains pending. Six historical mixed FBS/FCS gaps are retained separately and are not new repair targets. Nine previously unresolved college availability rows, historical publication-time verification, final pregame availability and tracking/video entitlement remain open.

**Next — V060, prepared:** investigate the 14 FBS gaps and changed current NFL assets; then compare native XGBoost/LightGBM/CatBoost with fixed, equivalent-cohort controls (84 planned new fits). Captured updates stay separate from frozen experiment inputs. No V060 result is claimed. Predictive priorities remain decision-time team strength, expected QB/lineup, role-weighted availability and situation-aware efficiency. [Feature priorities and framework status](docs/FEATURE_STRATEGY.md). No live wagering readiness or profitability claim is made.

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
