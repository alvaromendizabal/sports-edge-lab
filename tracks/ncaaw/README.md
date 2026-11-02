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

A retained earlier gradient model scored Brier **0.175054** and log loss **0.512560** on the same 260 games. Its stronger descriptive result also did not establish a statistically resolved MARKET advantage. The newest batch is not automatically the best retained model.

Two other calibration variants improved Brier slightly while worsening log loss because exact endpoint probabilities encountered losses. Those negative results remain in the record; favorable Brier alone does not qualify the calibrator.

### Evidence and next work

The accepted B030 owner-return digest is `842c299af8d177b289cc12568c8eb2faaac0a3598427d513156983f409aeabd9`. The new private study is prepared research only; there is no claimed successor execution or improved score. Private runtime packages, per-game records, feature transformations, weights, provider responses and execution handoffs remain outside this public repository.

The March tournament Brier records near 0.1028 and 0.1034 use different populations. They are not all-season baselines or reproduced NCAA recipes. The original serving recipe and its runtime, numerical, source-time and prospective-issuance gates remain unchanged.

See the [publication boundary](../../docs/PUBLICATION_BOUNDARY.md) for the distinction between inspectable aggregate evidence and privately reproducible research.
