# Sports Edge Lab

**Football forecasting research with auditable data, controlled experiments and honest market comparisons.**

Sports Edge Lab develops NFL and NCAA football win probabilities, point-margin forecasts and game-total forecasts. The project connects source acquisition, player identity, historical feature construction, model evaluation and recoverable AWS execution. Basketball tracks share the infrastructure; football is the current modeling focus.

**Verified through October 17, 2026 · V057:** 210 completed real model fits; accepted NFL and NCAAF baselines; no demonstrated market advantage or production promotion. The latest quarterback experiment completed correctly and did not pass its qualification gates. Negative results are retained as research evidence.

[Model card](docs/MODEL_CARD.md) · [Data readiness](docs/DATA_READINESS.md) · [Architecture](docs/ARCHITECTURE.md) · [Research roadmap](docs/RESEARCH_ROADMAP.md) · [Evidence scorecard](docs/demo/index.html)

## A two-minute review

| Reviewer question | Evidence |
| --- | --- |
| What is being predicted? | Home win conditional on no tie, home-minus-away margin, and combined points; separate models for NFL and NCAAF. |
| What is currently accepted? | NFL V047: 16 team-history features. NCAAF V048R1: 60 team-history and opponent-adjusted drive features. Regularized logistic/ridge models. |
| Is the history substantial? | The audited NFL modeling slice contains **498,285 play-by-play rows across 2016–2026**, covering 2,841 completed games. The previously highlighted 14,031 rows were only the current-season slice. The wider raw archive spans NFL **1999–2026** and ESPN college **2004–2026**, with **3.23 million** records in the latest selected annual ESPN files. These are raw source records, not deduplicated validated plays. |
| Why not just use a larger model? | Histogram gradient boosting was already evaluated in at least 24 verified early fits and did not replace the linear baselines. A fixed nonlinear benchmark with small neural networks is the next experiment. |
| What prevents overstated results? | Chronological fitting, exact same-game comparisons, training-only preprocessing, paired uncertainty, data-time caveats and explicit records of repeatedly examined evaluation seasons. |
| What is reproducible publicly? | Source, tests, execution contracts and sanitized evidence. Private/licensed raw data and credentials stay outside Git. Public fixtures test behavior; they do not reproduce private-data scores. |

## Results, not just downloads

The accepted models have predictive signal, but the available market benchmark remains stronger on the comparable 2024–2025 games.

| Track / task | Accepted model | Market benchmark | Metric; lower is better |
| --- | ---: | ---: | --- |
| NFL win | 0.6266 | 0.5999 | Log loss |
| NFL margin | 10.2613 | 9.8214 | MAE, points |
| NFL total | 10.2989 | 10.0365 | MAE, points |
| NCAAF win | 0.5490 | 0.5233 | Log loss |
| NCAAF margin | 13.0344 | 12.1228 | MAE, points |
| NCAAF total | 12.9051 | 12.4764 | MAE, points |

These are matched-price cohorts, not all historical games. Market quote horizons differ from some feature cutoffs; these results do not establish executable value. [Cohorts, Brier scores, uncertainty and limitations](docs/MODEL_CARD.md).

**Latest experiment — V057:** adding historical quarterback performance reduced exposed NFL total MAE from 10.3321 to 10.2046, but the continuity-only control already achieved 10.2179. The incremental effect was small, uncertainty included zero, and development gates failed. No task was promoted. The full-history cohort here differs from the matched-market table above.

## Engineering that supports the research

- **Data contracts:** pinned object hashes, schemas, exact game/team/player IDs, explicit coverage denominators and quarantined ambiguity.
- **Information contracts:** event, observation, publication and decision time remain distinct. Unknown historical publication timestamps stay unknown.
- **Controlled learning:** fixed folds and model configurations, ablations, cached baseline predictions and bounded real-fit accounting.
- **Recoverable execution:** one self-contained Python archive, offline gates before credentials, checkpoints, heartbeats, failure classification and one unique return bundle.
- **Broader evaluation:** log loss, Brier, calibration, AUC, MAE, RMSE, bias, tail errors, interval coverage/width and paired uncertainty.
- **Resource discipline:** reuse successful caches, separate provider quotas from AWS compute, and preserve failed attempts rather than silently restarting.

## What is ready—and what is not

Core team-level research is ready. NFL quarterback histories are auditable research features; they are **not confirmed future starters**. NCAAF has 28 games without any valid drive representation and nine unresolved availability rows. Historical information-time verification, final pregame availability and tracking/video entitlement remain open. No live wagering readiness or profitability claim is made.

The five-sport raw archive measured 101,035 in-scope content files / 17.39 GB at October 16, 23:30 UTC. This dated storage inventory is not a count of unique games, training rows or current model-ready examples. [Original inventory evidence](docs/status/content_inventory_20261016T2330Z.json).

## Review paths

| Focus | Start here |
| --- | --- |
| Modeling and experimental reasoning | [Model card](docs/MODEL_CARD.md) → [research roadmap](docs/RESEARCH_ROADMAP.md) |
| Data engineering and provenance | [Data readiness](docs/DATA_READINESS.md) → [source catalog](docs/DATA_CATALOG.md) |
| Systems and reliability | [Architecture](docs/ARCHITECTURE.md) → [V058 source and fixture](modeling/football_v058/README.md) |
| Portfolio presentation | [Static evidence scorecard](docs/demo/index.html) → [review rubric](docs/REPOSITORY_REVIEW.md) |
| Historical acquisition decisions | [Preserved pre-modeling README](docs/history/README_PRE_MODELING_20261017.md) → [execution source versions](docs/EXECUTION_SOURCE_VERSIONS.md) |

The HTML scorecard is an offline, self-contained document. Open the downloaded file in a browser; GitHub's source viewer does not execute it. No live scores, betting recommendations or fabricated forecasts appear in the demo.

## Scope and boundaries

One repository, one `sports-edge-lab-dev` SageMaker space, one canonical private data lake in `us-west-2`. Tracks: [NFL](tracks/nfl/README.md), [NBA](tracks/nba/README.md), [NCAAF](tracks/ncaaf/README.md), [NCAAM](tracks/ncaam/README.md) and [NCAAW](tracks/ncaaw/README.md). ACB is excluded; CBBD remains stopped. Historical track plans and acquisition receipts retain their original dates and are superseded by the current model and readiness cards where they differ.

This repository demonstrates end-to-end forecasting research and engineering. It does not redistribute restricted source records, claim ownership of upstream data, equate public statistical summaries with tracking trajectories, or present retrospective results as prospective validation.
