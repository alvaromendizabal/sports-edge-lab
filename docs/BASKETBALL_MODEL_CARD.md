# Model card — B002 basketball research

Publication date: October 27, 2026, Pacific time. [Project](../README.md) · [Study](BASKETBALL_FOUNDATION.md) · [Results](BASKETBALL_RESULTS.md) · [Aggregate evidence](evidence/2026-10-27-basketball-b002.json)

## Intended use and current status

Separate NBA, NCAA men's and NCAA women's historical prediction research and prospective monitoring. B002 is the first completed real basketball modeling run after the preserved B001 ingestion failure. No MARKET advantage, execution policy, profitable wagering record or production service guarantee is established.

The public evidence contains aggregate scores and engineering contracts. Exact active feature transforms, parameters, fitted weights and individual forecasts remain private. The credential-free example fits no model; its invented probabilities demonstrate contract behavior only.

## Targets and model families

| Family | Probability model | Predictor count | B002 execution |
|---|---|---:|---|
| Historical prior | Historical outcome baseline | Baseline | Evaluated |
| Elo | Chronological rating baseline | Baseline | Evaluated |
| Strength | Regularized logistic classifier with chronological calibration | 15 | Evaluated; NBA full-cohort selection |
| Style | Regularized logistic classifier with chronological calibration | 25 | Evaluated |
| Combined basketball | Regularized logistic classifier with chronological calibration | 53 | Evaluated; both college full-cohort selections |
| LightGBM, XGBoost, CatBoost | Native boosted classifiers with chronological calibration | 53 | Evaluated at T−60 |
| Learned MARKET-only | Declared MARKET classifier | 3 planned | Blocked by insufficient matched training history |
| Integrated MARKET plus basketball | Declared integrated classifier | 56 planned | Blocked by insufficient matched training history |

The winner target is the completed game's home-win outcome. The point head predicts margin and total using shared regularized Ridge regressors, then derives home and away points coherently. Negative or otherwise impossible issued scores are rejected rather than clipped. A boosted probability classifier does not imply a boosted score estimator; the shared Ridge head is labeled separately in the export.

Point estimates do not provide game-level prediction intervals, a full joint score distribution, cover/over probabilities or contract settlement probabilities. Those capabilities remain unavailable for basketball.

## Chronology and calibration

The declared historical folds train through the season ending 2024 and validate in ending 2025, then train through ending 2025 and validate in ending 2026. Calibration uses a later chronological training partition and excludes labels unavailable before its cutoff. Probability and point recipes are selected separately from historical evidence. Final fitted recipes use eligible history through ending 2026.

The season ending 2027 is excluded from selecting, tuning, ranking, calibrating or fitting model parameters. Already released current-season outcomes may update pregame histories for later games under the frozen feature policy. The resulting monitoring observations remain labeled according to whether a forecast actually existed before the game.

Completed historical tracks are reconstructed research: original publication evidence is unavailable, the primary release assumption is 24 hours, and a frozen 48-hour delay sensitivity is separate. T−60 is primary, T−24h secondary. Model selection exposes both historical validation seasons; results and paired uncertainty are descriptive, with no untouched confirmation claim.

## Results and comparator limitations

The [league tables](BASKETBALL_RESULTS.md) show per-season game counts, proper scores, accuracy, calibration error and point errors. On the pooled 2025–2026 full basketball cohorts, selected T−60 log loss was 0.607468 for NBA strength, 0.532072 for NCAA men's combined representation and 0.465183 for NCAA women's combined representation.

Those scores cannot be compared against MARKET's metrics on different games. The much smaller exact matched cohorts are disclosed separately. Neither the sparse NBA/women's comparisons nor NCAA men's single-season 118-game observation satisfies the historical qualification conditions. Learned MARKET-only and integrated training remain blocked. No model is promoted as a proven MARKET improvement.

## Data limitations and failure modes

Historical NBA advanced-box coverage is reduced by inconsistent rebound definitions. College schedules use a provisional membership/opponent protocol; neutral venues, identity changes and non-Division-I opponents need explicit treatment. Provider-covered schedules are not an authoritative league-wide denominator. Women's box and player coverage cannot be inferred from men's availability.

Additional risks include evolving team composition, changing roles, small market cohorts, unknown original publication clocks, stale odds, calibration shift and dependence across games involving the same teams. Player availability, rotations, transfers, coaching histories, learned player graphs and temporal encoders are not implemented basketball inputs in this release. Raw source completeness is different from eligible feature support.

## Issuance and deployment design

The admitted output is an immutable research forecast with a source cutoff, model availability time, actual issue time, named probability and point recipes, and explicit uncertainty limitations. B002's 110 output rows span 61 games and are early outlooks before their designated locks. No contemporaneously qualified MARKET probability was present. There were no settled prospective forecasts at the issue snapshot.

Serving depends on verified input revisions and an unchanged historical selection boundary. Native estimator fingerprints, byte hashes and atomic checkpoints protect reusable work. The execution carries predecessor runtime and request counters forward and writes diagnostics on failure or resource stops. This is a bounded owner-run workflow; a continuously deployed service, service-level objectives and automated betting are not demonstrated.

Actual orders are outside this release. Informational exchange comparisons require separate verified event, side, cutoff and settlement bindings, which remain unavailable. Profit is null, not zero realized profit.

## Next release

B003 owner execution is pending. Planned improvements address cached MARKET enumeration, verified source/checkpoint reuse, repeated feature preparation and prospective evaluation. Any new model or feature family must retain the frozen chronology, match its comparator's exact cohort, disclose both historical seasons and preserve unsuccessful results.
