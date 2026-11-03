# Sports Edge Lab · NCAA women's basketball

[Project](../../README.md) · [Interactive evidence source](index.html) · [Methodology and runnable example](../../examples/ncaa_review/README.md) · [Separate men's track](../ncaam/README.md)

## Current review — November 3, 2026 UTC

The accepted historical evidence compares objective-specific models on **10,901 exact shared games** across 2024–25 and 2025–26. The latest B032 owner attempt then failed at parent-data restoration: **zero new real fits, source refreshes, forecasts or prospective issues**. The failed return and prior accepted research remain preserved. A later independent full-byte return readback established durability without adding scientific credit.

### One fixed selection for each objective

| Evaluation window | Exact games | Best log loss | Same model's Brier | Best accuracy | Best margin MAE | Best total MAE |
|---|---:|---:|---:|---:|---:|---:|
| 2024–25 | 5,280 | 0.452535 | 0.150583 | 77.46% | 9.691 | 12.625 |
| 2025–26 | 5,621 | 0.456575 | 0.151638 | 76.59% | 9.682 | 12.660 |
| Both seasons | 10,901 | 0.454618 | 0.151127 | 77.01% | 9.687 | 12.643 |

The log-loss, accuracy, margin and total columns may use different models. Each is selected on the pooled historical cohort and stays fixed when the window changes. The interactive view also separates Brier and RMSE leaders and displays reliability bins, calibration error, AUC, signed point bias and the exact game counts. The [sanitized aggregate JSON](evidence.json) contains the full precision and qualifications; public model IDs keep exact active recipes private.

These historical seasons are **development-exposed**: they contributed to model selection after evaluation. They are not untouched confirmation or a record of prospectively issued picks. Availability relies on a declared 24-hour historical release assumption; official-season completeness is not established. Probability ties receive half accuracy credit and no directional pick; point errors are in basketball points including overtime.

### Probability quality and winner accuracy are different objectives

The log-loss selection minus the accuracy selection has pooled log-loss difference **-0.002887**, with descriptive week-block interval **[-0.005578, -0.000172]**. Its accuracy difference is **-0.3257 percentage points**, with interval **[-0.7948, +0.0640]**. The latter crosses zero.

These 2,000 resamples retain whole weeks within seasons and identical games for the two selections. They are not adjusted for the prior model search or dependence across weeks. A descriptive historical difference does not establish future advantage or profitability.

### Original monitoring, rolling research and provider comparisons

Frozen-original parameters and actual issue timestamps remain unchanged. Rolling reconstruction must use only labels and features released strictly before each training or prediction cutoff, and must remain separate from the original model's season record. More recent training data does not guarantee better future predictions.

The active provider scope is **Kalshi, Polymarket and DraftKings only**. Current-season matched comparisons, executable-price replay, ROI and market edge remain **unavailable**, not zero. Every comparison requires the same event, ordered teams, horizon, target and settlement, plus qualified quote clocks. The failed attempt did not reach these stages. Passing software fixtures never supplies missing game or quote evidence.

### Reproducible public engineering

The new [credential-free example](../../examples/ncaa_review/README.md) implements exact population pairing, information-clock validation, separate winner/margin/total metrics, an invented chronological baseline, explicit-fee payoff math and complete streamed-byte verification. Negative tests cover future-label poisoning, equal boundaries, wrong settlements, incompatible identities, missing coverage, mixed evaluation tracks and the actual stream-context failure class. Generated pages are checked against the exact aggregate JSON; real browser tests exercise every objective/window state at desktop and mobile widths.

No private model bodies, exact active features, licensed responses, individual forecast archives or execution handoffs are published. The [publication boundary](../../docs/PUBLICATION_BOUNDARY.md) remains in force. The accepted historical return digest is `df98ed0758c29deaed943355349833ab0aeaa23a79693b5efc027e835075e4da`; the failed current return digest is `ae14d708cf85615c1c9c57a7891db85261a5b1632ecd70349730bf2dde51d9b0`.

<details>
<summary>Earlier published track history — preserved as dated evidence through B030</summary>

The narrative below is the earlier November 2 track snapshot. Its acquisition targets, inherited reference definitions and run-status statements describe that date, not the active three-provider scope or latest execution above.

# Sports Edge Lab · NCAA women's basketball

Player-adjusted team strength, possession efficiency, tempo and roster continuity with explicit separation between long statistical history and shorter odds history.

This track lives in the shared [Sports Edge Lab](../../README.md) repository and `sports-edge-lab-dev` workspace. Its private archive prefix is `tracks/ncaaw/` in the central data lake.

## Model sequence

1. Hierarchical team and player ratings.
2. Point-margin and total distributions.
3. Calibrated win-probability classifier.
4. Tournament simulations.

## Feature families

- Possession efficiency and tempo.
- Player role and availability.
- Roster continuity and matchup depth.
- Venue, rest and schedule strength.

## Source scope

- audited ESPN/NCAA interfaces and wehoop/sportsdataverse public archives.
- The Odds API historical moneylines, spreads and totals.

These are acquisition and research targets, not assertions of complete coverage. The source/season audit determines which observations may enter each experiment.

## Temporal boundary

Market evaluation begins only where timestamped quotes are actually present; the planned provider starting date is November 12, 2024. Older statistics do not create older market quotes.

## Acceptance criteria

Apply the [shared research protocol](../../docs/RESEARCH_PROTOCOL.md). Establish sport-specific identity mappings and source coverage before feature development. A market backtest requires an actual bookmaker quote and a recorded availability time. Track quality with log loss, Brier score, calibration and distribution coverage, then separately assess simulated market returns, closing-line value and uncertainty.

Current phase: B030 historical research and exact-cohort analysis completed; provider completeness and prospective forecast qualification remain unresolved.

## B003 basketball evidence

NCAA women added 22 new estimator units, including three changed final T−24h selection units. Rich combined logistic with 63 predictors improved both T−60 historical seasons and reduced pooled log loss from 0.465183 to 0.457143 across 10,901 games. Fixed-bin calibration worsened overall, and 2025 correct picks fell. The expanded T−60 MARKET cohorts contain 149 ending-2025 and 143 ending-2026 games; seasonal differences change sign and both paired intervals include zero. Twelve upcoming games retain early outlooks, no qualified current prices and no settled prospective scores at the snapshot.

Read the [basketball study](../../docs/BASKETBALL_FOUNDATION.md), [generated league leaderboards](../../docs/BASKETBALL_RESULTS.md), [model card](../../docs/BASKETBALL_MODEL_CARD.md) and [executed notebook](../../notebooks/basketball_review.ipynb). The [public contracts](../../examples/basketball_contracts/README.md) use invented fixtures separate from actual aggregate results. B002 evidence and B001’s pre-modeling failure remain preserved. [B004 executed but stopped at its public-request ceiling](../../docs/BASKETBALL_B004_EXECUTION.md); no challenger was promoted, and B003 remained the latest fully completed real modeling release at that stage. The verified follow-up below records the later historical research.

## Verified B030 follow-up — November 2, 2026 UTC

The independently authenticated B030 owner return completed 32 earlier-origin winner fits and 40 scalar calibration fits across the two separate NCAA tracks, with 141 fresh owner fixture tests. Those counts are split evenly by sex. No current-season forecast, promotion or order was issued. Independent full-byte verification covered the final return and all 436 declared checkpoint objects.

The historical review combines 94 retained recipes and 22,408 represented games across the two tracks. Its 1,487,164 model/game rows repeat games across recipes; they are not 1,487,164 independent games. Full-source, exact common-population and matched MARKET comparisons retain separate denominators. The 22,426-game feature census leaves 18 cases without a supplied prediction; their exact exclusion reasons were not established by the compact evidence.

### One measurement contract

Winner comparisons use natural-log loss, Brier score on the original probabilities, accuracy with half credit at probability 0.5, calibration bias and fixed-bin calibration. Probability ties produce no directional pick. Margin and total predictions use MAE and RMSE in points. Every paired comparison uses the same games, targets and reference observations. Historical evaluation is development-exposed reconstruction, not a record of prospectively issued picks or untouched confirmation.

MARKET is the inherited qualified bookmaker-consensus source. It is separate from each named provider and from the later stored median-consensus definition. No historical named-provider comparison or historical spread/total settlement is inferred from that consensus. Winner accuracy, probabilistic scores and executable economic value answer different questions.

The current observation snapshot is November 2 at 05:17 UTC. Stored odds remain observations from November 1 at about 21:07 UTC. Public scoreboard monitoring did not refresh the odds feed. Provider completeness, current model-provider disagreement wins, profit, ROI and closing-line value remain unestablished. CollegeBasketballData's rate-limit pause remains in force.

### Women's matched historical result

The inherited MARKET populations contain **235 games** from the season ending in 2025 and **260 games** from the season ending in 2026. In the latter cohort, one B030 calibrated variant scored Brier **0.178195**, natural-log loss **0.518839** and accuracy **71.54%**, versus MARKET's **0.178801**, **0.523213** and **70.38%**. The Brier difference was about **−0.000606**, with descriptive block interval **[−0.007442, +0.005911]**. The interval includes zero.

A retained earlier gradient model scored Brier **0.175054** and log loss **0.512560** on the same 260 games. Its Brier interval includes zero. Its descriptive log-loss interval favors the retained model: the model-minus-MARKET difference is about −0.010653, with interval [−0.026373, −0.000947]. Prior exposure and unadjusted multiple comparisons prevent a confirmatory or prospective profitability claim. The newest batch is not automatically the best retained model.

Two other calibration variants improved Brier slightly while worsening log loss because exact endpoint probabilities encountered losses. Those negative results remain in the record; favorable Brier alone does not qualify the calibrator.

### Evidence and next work

The accepted B030 owner-return digest is `842c299af8d177b289cc12568c8eb2faaac0a3598427d513156983f409aeabd9`. The new private study is prepared research only; there is no claimed successor execution or improved score. Private runtime packages, per-game records, feature transformations, weights, provider responses and execution handoffs remain outside this public repository.

The March tournament Brier records near 0.1028 and 0.1034 use different populations. They are not all-season baselines or reproduced NCAA recipes. The original serving recipe and its runtime, numerical, source-time and prospective-issuance gates remain unchanged.

See the [publication boundary](../../docs/PUBLICATION_BOUNDARY.md) for the distinction between inspectable aggregate evidence and privately reproducible research.

</details>
