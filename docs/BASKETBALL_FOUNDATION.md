# Basketball: controlled college gains, MARKET advantage still unresolved

[Project](../README.md) · [Model card](BASKETBALL_MODEL_CARD.md) · [League leaderboards](BASKETBALL_RESULTS.md) · [B003 aggregate](evidence/2026-10-27-basketball-b003.json) · [Executed notebook](../notebooks/basketball_review.ipynb) · [Public contracts](../examples/basketball_contracts/README.md)

B003 completed actual NBA, NCAA men's and NCAA women's owner execution on October 27, 2026, Pacific time. Adding opponent-adjusted information improved both college historical validation seasons on identical games. The earlier strength model remained best for NBA. Expanded sportsbook coverage made the MARKET comparison more informative and exposed the remaining chronological training gap. No basketball track established a qualified MARKET advantage, an executable trading opportunity or prospective profit.

This study follows B002's first completed real modeling run and the preserved B001 ingestion failure. It separates genuine owner computation, imported estimator reuse, reconstruction assumptions, historical model selection and immutable prospective forecasts. The public export contains aggregate evidence; the private observations and active models are not distributed.

## What the controlled experiment established

B003 added ten opponent-adjusted predictors and three T−60 arms: a 25-predictor strength-plus-adjustment logistic model, a 63-predictor rich logistic model, and a 63-predictor rich LightGBM model. It compared them with exact earlier controls. The audit found no changed probability, point prediction, target or cutoff among the prior B002 control rows across all six league/horizon tracks.

| League | Previous probability selection | B003 historical selection | Prior pooled log loss | B003 pooled log loss | Change |
|---|---|---|---:|---:|---:|
| NBA | Strength logistic, 15 predictors | Same strength logistic | 0.607468 | 0.607468 | 0.000000 |
| NCAA men | Combined logistic, 53 predictors | Rich combined logistic, 63 predictors | 0.532072 | **0.525415** | −0.006657 |
| NCAA women | Combined logistic, 53 predictors | Rich combined logistic, 63 predictors | 0.465183 | **0.457143** | −0.008040 |

For men, the rich-logistic improvement against the earlier combined control has a descriptive paired 95% seven-day-block interval of [−0.009748, −0.003626] across 11,507 games. For women it is [−0.011341, −0.005301] across 10,901 games. Both seasons improve in each college league. NBA's added representation does not beat its previous 15-predictor selection across 2,497 games.

Those intervals summarize selected development evidence. Both historical folds have been examined during research; neither is an untouched confirmation. Temporal blocks preserve local dependence but do not fully address repeated-team and longer-range dependence. No multiple-testing correction or prospective superiority is implied.

Better proper scores also did not mean every diagnostic improved. College pooled fixed-bin calibration error increased from 0.013393 to 0.014288 for men and from 0.019232 to 0.023450 for women. Women's correct-pick count fell in 2025 despite better log loss and Brier score. These limitations belong in the model decision, not in a footnote hidden from the leaderboard.

## Exact chronology and distinct targets

The first fold trains through the season ending 2024 and validates in 2025. The second trains through 2025 and validates in 2026. Calibration uses a later chronological partition inside the allowed training period. Historical results select probability and point recipes separately; final recipes fit eligible history through 2026. The season ending 2027 never selects features, hyperparameters, calibration, ensemble weights or champions.

Released current-season observations may update team histories under the frozen policy. Their use for monitoring does not turn retrospective outputs into forecasts that existed before a game. T−60 is primary. T−24h retains its own data cutoff, selection, scores and matched MARKET cohort; the new B003 arms were evaluated only at T−60.

The point heads remain shared Ridge margin and total regressors. A classifier label such as LightGBM or CatBoost does not identify the score regressor. B003's NBA point selection reduces 2025 total bias from about +2.32 to +1.84 points, but 2026 bias remains about +2.66. A point estimate is not a predictive score distribution or an interval with verified coverage.

## Larger MARKET cohorts expose the real bottleneck

The B003 implementation admitted already-owned eligible bookmaker responses that had been unnecessarily limited by a request-planning cap. It did not lower freshness, identity or chronology requirements and made no paid acquisitions. Bound archived rows expanded from 5,392 to 55,069 and bound events from 333 to 3,104. Actual model-matched validation samples are smaller and must be counted separately from source eligibility.

| League | B002 T−60 matched games: 2025 / 2026 | B003 T−60 matched games: 2025 / 2026 | B003 eligible earlier training rows: first / second fold |
|---|---:|---:|---:|
| NBA | 7 / 6 | 9 / 16 | 6 / 15 |
| NCAA men | 0 / 118 | 0 / 1,143 | 0 / 0 |
| NCAA women | 23 / 13 | 149 / 143 | 0 / 149 |

The learned MARKET-only and integrated classifiers still cannot meet the declared minimum training support. A large 2026 validation cohort does not supply training observations from 2024 or 2025. No threshold was relaxed to manufacture a fitted arm.

The full-cohort men's rich selection has log loss 0.577570 on its 1,143 matched 2026 games, versus MARKET's 0.567127: an observed loss to MARKET. Women's rich model is worse than MARKET in 2025 and better in 2026, with both per-season paired intervals crossing zero. NBA's samples remain sparse and its seasonal comparisons disagree. The [generated tables](BASKETBALL_RESULTS.md) show every league and horizon without comparing scores from different sets of games.

Kalshi, Polymarket US and international Polymarket remain distinct benchmark venues. B003 admitted zero historical exchange events and zero executable contemporaneous exchange quotes. A displayed probability is not a timestamped order book or an executable price. Contract direction, settlement rules, quote clocks, fees, liquidity and depth must be verified before an exchange comparison or paper execution scenario is qualified. There is no basketball bankroll or order policy in this release.

## Data and availability remain limiting

All 70 inspected statistical assets still lack independently established original historical publication clocks. Completed model tracks therefore use a labeled 24-hour reconstructed release assumption; frozen 48-hour sensitivity remains separate. Retrieval times do not establish historical availability, and no strict point-in-time basketball performance claim is admitted.

| League | Eligible historical targets | Complete valid box pairs | Important unresolved limitation |
|---|---:|---:|---|
| NBA | 13,933 | 7,264 | Older rebound-definition conflicts and partial paired boxes |
| NCAA men | 59,844 | 59,710 | Historical Division I membership remains a research proxy |
| NCAA women | 57,256 | 53,394 | Early missing box coverage, especially season ending 2016 |

These are provider-covered eligible schedules, not certified league-wide or Division I universes. The 33 cataloged player-box assets are discovery evidence; B003 does not establish an exact player-level modeling join. Injuries, projected rotations, transfers, coaching changes and replacement-value signals remain unvalidated basketball inputs. Their absence limits both the strength of a forecast and the interpretation of its uncertainty.

## Reuse changed the cost of the experiment

| Computation | B002 | B003 | Interpretation |
|---|---:|---:|---|
| New real native estimator units | 172 | 60 | Distinct completed units, not independent scientific discoveries |
| Imported prior estimator units | 0 | 156 | Exact compatible input/dependency signatures and byte hashes |
| Native fitting time | 58.46 s | 23.07 s | Most execution time was elsewhere |
| Historical feature preparation | 528.35 s | 513.50 s | Full-history construction remains substantial |
| Frozen 48-hour sensitivity preparation/inference | 267.86 s | 121.51 s | Restricted output targets reduced work |
| Final upcoming feature preparation/inference | 525.00 s | 142.60 s | Current-only output materialization reduced work |
| Total additional active time through returned snapshot | 28.63 min | 22.10 min | Different workloads; not a controlled hardware benchmark |

B003's 216 current-release manifests contain 60 new units and 156 imported aliases. The cumulative unique basketball count is 232, not 388. Six other distinct units were reused within the invocation; 180 reuse events are not 180 additional models. The audit verified all 216 checkpoint signatures and weights, 156 predecessor identities and 80 frozen bundles without executing a model locally.

The latest returned cumulative active-time floor is 3,571.02 seconds under the unchanged 4,500-second work ceiling, leaving 928.98 seconds before a separate 180-second finalization allowance. Later compatible live receipts can increase the floor. Predecessor totals overlap, so adding them would double-count work. The new prospective reconciliation stage took about 205 seconds, making another clear efficiency target before additional owner experiments.

The owner software gate passed 327 tests. Its saved research notebook contains four executed code cells and two native Plotly outputs, with save/reopen and later-cell checks. The return audit verified 11,617 member hashes and 55 report links. These software and transport checks support trustworthy operations; they do not establish predictive superiority.

## Genuine prospective evidence starts with preserved forecasts

B003 checked the exact 110 B002-issued rows and found all pending, none quarantined and none settled at its observation time. It issued 110 later-version rows for the same 61 distinct future games: 41 NBA, eight men's and 12 women's games. Counting forecast versions as new independent games would be wrong.

All rows remain early outlooks before their declared T−60 or T−24h locks, with no qualified fresh MARKET probability and NO_BET status. Issue clocks are captured after inference and rechecked against model/input availability and tipoff. Earlier probabilities are immutable. There were zero paid acquisitions and zero orders, while prospective proper scores and profit remain unavailable.

## How this complements the wider portfolio

Sports Edge Lab's NFL/FBS research provides shared provenance, temporal evaluation and recovery engineering. Basketball tests those contracts on different season calendars, team identities, score structures and source gaps. The separate March Madness Mania project supplies candidate reusable archives and research lessons; its competition results, tournament assumptions and selected methods are not automatically basketball regular-season validation.

The [public notebook](../notebooks/basketball_review.ipynb) reads only aggregate exports, visualizes controlled contrasts, calibration and matched coverage, and runs invented contract checks in a separate section. The validator regenerates the tables and checks exact cohort identity, pooled arithmetic, calibration-bin totals and reuse accounting. Neither the notebook nor CI fits a private model. Full private-model retraining remains outside the public publication boundary.

[B004 executed on October 28 and stopped at the public-request ceiling](BASKETBALL_B004_EXECUTION.md). It completed six historical league/horizon scopes and six new score-correction units before the stop. None of the three challenger programs earned promotion. Its stopped status, unchanged incumbents, uncertainty diagnostics and accounting are recorded separately; B003 remains the latest fully completed real modeling release.

## Saved MARKET coverage investigation

B005 completed evidence recovery with zero new fits, inference, source requests or forecasts; B003 remains the latest fully completed real modeling release. The [new same-season cohort study](BASKETBALL_MARKET_COVERAGE.md) separates year confounding, baseline probability, calendar composition and common-support loss. Its [executed notebook](../notebooks/basketball_market_coverage.ipynb) presents descriptive uncertainty and retention together. No independent MARKET advantage, promotion or additional budget is established.

