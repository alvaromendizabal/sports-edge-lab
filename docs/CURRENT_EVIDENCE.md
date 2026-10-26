# Current research evidence — October 26, 2026

[Project](../README.md) · [Model card](MODEL_CARD_CURRENT.md) · [Aggregate export](evidence/2026-10-26.json) · [Offline explorer](review/index.html)

V119R1 completed the integrated football experiment: 96 new fits, 96 reused control cells, 192 total cells, and 24 new fits in each native framework. Both NFL and FBS historical qualification gates failed. The selected retained references remain ahead. This is a successfully executed negative result, not a breakthrough or a promotion.

The earlier [V119 failure](evidence/2026-10-26-execution.json) and [October 25 model publication](evidence/2026-10-25.json) remain preserved. The [new execution receipt](evidence/2026-10-26-v119r1-execution.json) distinguishes the corrected owner execution from its earlier synthetic preparation.

## Three campaigns and the complete joint comparison

Each cell is log loss / Brier; lower is better. C is compact football plus MARKET; L adds learned football representations; U adds direct football measurements; UL combines both additions. All six systems are evaluated on identical games within a row.

| Sport / campaign / policy | Games | MARKET | C | L | U | UL | Retained best by metric |
|---|---:|---:|---:|---:|---:|---:|---:|
| NFL 2024–2025 fixed | 280 | 0.590011 / 0.201418 | 0.586801 / 0.200220 | 0.585244 / 0.199270 | 0.587264 / 0.200296 | 0.587995 / 0.200815 | **0.575083** / **0.194627** |
| NFL 2025–2026 fixed | 277 | 0.611923 / 0.213133 | 0.612458 / 0.213486 | 0.613622 / 0.213887 | 0.614809 / 0.214423 | 0.615619 / 0.214723 | **0.606098** / **0.210736** |
| NFL 2025–2026 annual | 277 | 0.611923 / 0.213133 | 0.615797 / 0.214913 | 0.619893 / 0.216829 | 0.617426 / 0.215472 | 0.620113 / 0.216819 | **0.606098** / **0.210736** |
| NFL 2026–2027 monitoring | 77 | 0.660022 / 0.233301 | 0.654355 / 0.230954 | 0.647299 / 0.227659 | 0.647731 / 0.227945 | 0.654224 / 0.231141 | **0.624093** / **0.217288** |
| FBS 2024–2025 fixed | 740 | 0.554096 / 0.188631 | 0.555546 / 0.189181 | 0.555214 / 0.189198 | 0.557164 / 0.189922 | 0.556444 / 0.189721 | **0.552031** / **0.187554** |
| FBS 2025–2026 fixed | 748 | 0.538547 / 0.181678 | 0.538485 / 0.181870 | 0.538406 / 0.181856 | 0.538928 / 0.182109 | 0.539773 / 0.182477 | **0.536814** / **0.181086** |
| FBS 2025–2026 annual | 748 | 0.538547 / 0.181678 | 0.538650 / 0.182114 | 0.538061 / 0.181917 | 0.538551 / 0.182090 | 0.538394 / 0.182047 | **0.535618** / **0.180522** |
| FBS 2026–2027 monitoring | 301 | 0.474843 / 0.156153 | 0.473781 / 0.156244 | 0.473819 / 0.155894 | 0.473950 / 0.155902 | 0.475016 / 0.156573 | **0.465519** / **0.152630** |

The FBS 2024 retained Brier leader is a different LightGBM model: 0.187554. The interactive explorer selects the retained reference independently for each metric. Fixed heads train through 2023; annual 2025 heads generally train through 2024. The strongest annual NFL retained reference is still an older fixed MARKET model. Current monitoring has a separate origin and includes eligible non-tied games only through October 15, 2026.

These are exposed descriptive comparisons. The retained leaders are the strongest evaluated references within this project and cohort; external commercial systems lack aligned archived forecasts and are not ranked here.

## What the integration experiment answered

A four-arm comparison measures predictive complementarity using Loss(UL) − Loss(U) − Loss(L) + Loss(C). Negative values indicate that the combined loss reduction exceeds the sum of the isolated reductions on the chosen loss scale. They do not establish causality. See the [joint-evidence case study](CASE_STUDY_JOINT_EVIDENCE.md) for the outcome and a separate executable public demonstration.

Every estimable primary ensemble interaction interval crossed zero. NFL current monitoring has only six weekly blocks and therefore no interval under the declared eight-block support rule. The FBS current interaction is +0.001029 with interval [−0.006903, +0.007825]. More features did not produce established complementarity.

Current NFL UL log loss is 0.654224: better than MARKET's 0.660022, worse than the learned-only arm's 0.647299, and worse than the retained reference's 0.624093. Current FBS UL log loss is 0.475016, worse than MARKET's 0.474843 and the retained reference's 0.465519. The newest model is not automatically the best model.

## All four native implementations

The [aggregate export](evidence/2026-10-26.json) includes log loss, Brier, accuracy and AUC for LightGBM, XGBoost, PyTorch, TensorFlow, the equal-weight UL ensemble, controls and retained references in all eight panels. The [explorer](review/index.html) displays these framework results beside the complete factorial comparison with synchronized sport, campaign and metric selectors.

## What MARKET means

Raw MARKET is the median bookmaker consensus after paired proportional moneyline de-vig, using at least three common complete books. It is not an executable quote or necessarily a closing line. Learned MARKET models use quote values, missingness, bookmaker identity and archived price paths. Football-plus-MARKET models add the feature families listed in the explorer. Bookmakers' internal feature sets are unknown.

Kalshi is a separate contract venue with its own bid/ask, fees and settlement targets. Conditional non-tie game-win probabilities are not automatically the same quantity as contract payout probabilities. A forecasting score does not establish an executable betting edge.

## Data and serving outcomes

| Layer | Audited owner outcome | Remaining boundary |
|---|---|---|
| NFL finals/PBP | 106 finals with PBP coverage for all 106 | Enrichment covers 94 games; 12 gaps remain |
| FBS detailed summaries | 566/566 games; 100,687 plays, 13,242 drives | Two native drive records remain quarantined |
| FBS detailed boxes | 16,980 team-stat and 293,422 player-stat rows | Collected observations are not automatically historically eligible features |
| Kickoff conflicts | 17 conflicts corroborated and repaired under separate source clocks | No historical feature rows changed; present evidence does not prove historical publication |
| Current research issuance | 3,270 model rows across 52 unique games | Multiple model rows are not independent games |
| Price admission | Zero fresh eligible named quotes; zero paper actions or wagers | A 5.071-second final capture-to-issue interval did not repair old source observations |

Current pregame starter/participation, roster transitions, forecast weather vintages and coherent contract-specific outcome distributions remain research dependencies. Public NGS summaries are not full tracking data. Publication, observation, revision, release and decision clocks remain separate.

## Verification and reproducibility

The owner run passed 1,142 checks. Independent read-only rescoring matched all 3,230 scorecards / 12,920 scalar metrics to within 2.23e-16 and all 80 factorial point contrasts. No models were fitted or invoked during that audit. The public artifact contains aggregate projections and a synthetic evaluator, not private predictions or a reproduction of private training.

The [public/private boundary](PUBLICATION_BOUNDARY.md) and [historical paths](PROJECT_SCOPE.md) remain explicit. No automatic promotion, real wager, proven prospective profitability or global state-of-the-art claim follows from this publication.
