# Sports Edge Lab

**Football forecasting research with auditable data, controlled experiments and honest market comparisons.**

Sports Edge Lab develops NFL and NCAA football win probabilities, point-margin forecasts and game-total forecasts. The project connects source acquisition, player identity, historical feature construction, model evaluation and recoverable AWS execution. Basketball tracks share the infrastructure; football is the current modeling focus.

**Verified through October 17, 2026 · V058:** 246 completed real model fits; accepted NFL and NCAAF baselines; no demonstrated market advantage or production promotion. The nonlinear benchmark completed all 36 fits, including 24 neural-network fits. None of its nine candidate/task combinations passed qualification. Negative results are retained as research evidence.

**College scope:** future forecasts and headline evaluation target **FBS versus FBS**. Historical FBS/FCS games remain archived and may provide declared opponent context; no standalone FCS acquisition or modeling work is planned.

[Model card](docs/MODEL_CARD.md) · [Data readiness](docs/DATA_READINESS.md) · [Architecture](docs/ARCHITECTURE.md) · [Research roadmap](docs/RESEARCH_ROADMAP.md) · [V058 completed evidence](docs/status/football_v058/README.md) · [Evidence scorecard](docs/demo/index.html)

## A two-minute review

| Reviewer question | Evidence |
| --- | --- |
| What is being predicted? | Home win conditional on no tie, home-minus-away margin, and combined points; separate models for NFL and NCAAF. |
| What is currently accepted? | NFL V047: 16 team-history features. NCAAF V048R1: 60 team-history and opponent-adjusted drive features. Regularized logistic/ridge models. |
| Is the history substantial? | The audited NFL modeling slice contains **498,285 play-by-play rows across 2016–2026**, covering 2,841 completed games. The previously highlighted 14,031 rows were only the current-season slice. The wider raw archive spans NFL **1999–2026** and ESPN college **2004–2026**, with **3.23 million** records in the latest selected annual ESPN files. These are raw source records, not deduplicated validated plays. |
| Why not just use a larger model? | V058 added 12 histogram-boosting and 24 small-neural-network fits. All nine candidate/task qualifications failed. More capacity did not improve these fixed representations reliably. |
| What prevents overstated results? | Chronological fitting, exact same-game comparisons, training-only preprocessing, paired uncertainty, data-time caveats and explicit records of repeatedly examined evaluation seasons. |
| What is reproducible publicly? | Source, tests, execution contracts and sanitized evidence. Private/licensed raw data and credentials stay outside Git. Public fixtures test behavior; they do not reproduce private-data scores. |

## Results, not just downloads

V058 tested fixed histogram gradient boosting (HGB) and a small multilayer perceptron (MLP), reusing accepted predictions. The 2024–2025 periods below are exposed retrospective evaluation, not untouched tests. Lower is better.

| Track / task | Accepted linear | HGB | MLP | Metric |
| --- | ---: | ---: | ---: | --- |
| NFL win | **0.6298** | 0.6309 | 1.1478 | Log loss; 569 games |
| NFL margin | 10.1984 | **10.1315** | 13.4098 | MAE, points; 570 games |
| NFL total | **10.3321** | 10.3919 | 14.4034 | MAE, points; 570 games |
| FBS vs FBS win | **0.5547** | Not refitted | 1.0393 | Log loss; 1,606 games |
| FBS vs FBS margin | **12.8198** | Not refitted | 15.6696 | MAE, points; 1,606 games |
| FBS vs FBS total | **13.0939** | Not refitted | 15.6920 | MAE, points; 1,606 games |

The small NFL margin gain was **0.0669 points / 0.66%**, with a paired 95% difference interval spanning zero. It failed the declared threshold and development gates. The MLP configurations performed materially worse. This rejects these tested configurations, not neural networks or boosting as whole fields.

The FBS-only rows are exact subgroups of the existing college forecasts; they are **not a new FBS-only model fit**. Prior market comparisons use separate quote-matched cohorts and horizons. [Full model card, Brier scores and limitations](docs/MODEL_CARD.md) · [V058 verified evidence](docs/status/football_v058/summary.json).

## Engineering that supports the research

- **Data contracts:** pinned object hashes, schemas, exact game/team/player IDs, explicit coverage denominators and quarantined ambiguity.
- **Information contracts:** event, observation, publication and decision time remain distinct. Unknown historical publication timestamps stay unknown.
- **Controlled learning:** fixed folds and model configurations, ablations, cached baseline predictions and bounded real-fit accounting.
- **Recoverable execution:** one self-contained Python archive, offline gates before credentials, checkpoints, heartbeats, failure classification and one unique return bundle.
- **Broader evaluation:** log loss, Brier, calibration, AUC, MAE, RMSE, bias, tail errors, interval coverage/width and paired uncertainty.
- **Resource discipline:** reuse successful caches, separate provider quotas from AWS compute, and preserve failed attempts rather than silently restarting.

## What is ready—and what is not

Core team-level research is ready. NFL quarterback histories are auditable research features; they are **not confirmed future starters**. The FBS-versus-FBS canonical scope has **7,898 completed games**, with **7,895** in the frozen feature table and three recent finals still missing there.

Of **22 in-scope drive gaps**, eight have a locally verified overtime-ordering repair prepared for V059. AWS integration is pending; **14 would remain after that repair**. Six historical mixed FBS/FCS gaps are retained separately and are not new repair targets. Nine previously unresolved college availability rows, historical publication-time verification, final pregame availability and tracking/video entitlement remain open.

**Next — V059:** cached FBS scope/repair validation and a controlled dynamic-versus-static joint Gaussian team offense/defense benchmark. Sixteen planned joint fits each generate win, margin and total outputs. It has not executed. No live wagering readiness or profitability claim is made.

The five-sport raw archive measured 101,035 in-scope content files / 17.39 GB at October 16, 23:30 UTC. This dated storage inventory is not a count of unique games, training rows or current model-ready examples. [Original inventory evidence](docs/status/content_inventory_20261016T2330Z.json).

## Review paths

| Focus | Start here |
| --- | --- |
| Modeling and experimental reasoning | [Model card](docs/MODEL_CARD.md) → [research roadmap](docs/RESEARCH_ROADMAP.md) |
| Data engineering and provenance | [Data readiness](docs/DATA_READINESS.md) → [source catalog](docs/DATA_CATALOG.md) |
| Systems and reliability | [Architecture](docs/ARCHITECTURE.md) → [V059 state core](modeling/football_v059/README.md) / [completed V058 benchmark](modeling/football_v058/README.md) |
| Portfolio presentation | [Static evidence scorecard](docs/demo/index.html) → [review rubric](docs/REPOSITORY_REVIEW.md) |
| Historical acquisition decisions | [Preserved pre-modeling README](docs/history/README_PRE_MODELING_20261017.md) → [execution source versions](docs/EXECUTION_SOURCE_VERSIONS.md) |

The HTML scorecard is an offline, self-contained document. Open the downloaded file in a browser; GitHub's source viewer does not execute it. No live scores, betting recommendations or fabricated forecasts appear in the demo.

## Scope and boundaries

One repository, one `sports-edge-lab-dev` SageMaker space, one canonical private data lake in `us-west-2`. Tracks: [NFL](tracks/nfl/README.md), [NBA](tracks/nba/README.md), [NCAAF](tracks/ncaaf/README.md), [NCAAM](tracks/ncaam/README.md) and [NCAAW](tracks/ncaaw/README.md). ACB is excluded; CBBD remains stopped. Historical track plans and acquisition receipts retain their original dates and are superseded by the current model and readiness cards where they differ.

This repository demonstrates end-to-end forecasting research and engineering. It does not redistribute restricted source records, claim ownership of upstream data, equate public statistical summaries with tracking trajectories, or present retrospective results as prospective validation.
