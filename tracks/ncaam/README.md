# Sports Edge Lab · NCAA men's basketball

Possession efficiency, tempo, player availability and calibrated game-margin distributions across regular-season and tournament play.

This track lives in the shared [Sports Edge Lab](../../README.md) repository and `sports-edge-lab-dev` workspace. Its private archive prefix is `tracks/ncaam/` in the central data lake.

## Model sequence

1. Opponent-adjusted possession ratings.
2. Point-margin and total distributions.
3. Calibrated win-probability ensemble.
4. Tournament simulations driven by game-level distributions.

## Feature families

- Offensive and defensive efficiency.
- Tempo and shot profile.
- Player roles and roster continuity.
- Rest, venue and schedule strength.

## Source scope

- CollegeBasketballData games, plays, player/team statistics and rosters.
- audited ESPN/NCAA and public archive interfaces.
- The Odds API historical moneylines, spreads and totals.

These are acquisition and research targets, not assertions of complete coverage. The source/season audit determines which observations may enter each experiment.

## Temporal boundary

CollegeBasketballData season labels use ending years. Post-tournament ratings and retrospectively corrected injury data require explicit vintage checks. Existing March Madness research remains a separate project.

## Acceptance criteria

Apply the [shared research protocol](../../docs/RESEARCH_PROTOCOL.md). Establish sport-specific identity mappings and source coverage before feature development. A market backtest requires an actual bookmaker quote and a recorded availability time. Track quality with log loss, Brier score, calibration and distribution coverage, then separately assess simulated market returns, closing-line value and uncertainty.

Current phase: B030 historical research and exact-cohort analysis completed; provider completeness and prospective forecast qualification remain unresolved.

## B003 basketball evidence

NCAA men added 19 new estimator units. Rich combined logistic with 63 predictors improved both historical seasons and reduced pooled log loss from 0.532072 to 0.525415 across 11,507 games. The paired descriptive block interval favors the new representation, but fixed-bin calibration error increased. On 1,143 matched ending-2026 games its log loss is 0.577570 versus MARKET's 0.567127. Earlier matched training support remains zero; no learned MARKET or integrated classifier qualified. Eight upcoming games retain early outlooks with no qualified current prices or settled prospective scores.

Read the [basketball study](../../docs/BASKETBALL_FOUNDATION.md), [generated league leaderboards](../../docs/BASKETBALL_RESULTS.md), [model card](../../docs/BASKETBALL_MODEL_CARD.md) and [executed notebook](../../notebooks/basketball_review.ipynb). The [public contracts](../../examples/basketball_contracts/README.md) use invented fixtures separate from actual aggregate results. B002 evidence and B001’s pre-modeling failure remain preserved. [B004 executed but stopped at its public-request ceiling](../../docs/BASKETBALL_B004_EXECUTION.md); no challenger was promoted, and B003 remained the latest fully completed real modeling release at that stage. The verified follow-up below records the later historical research.

## Verified B030 follow-up — November 2, 2026 UTC

The independently authenticated B030 owner return completed 32 earlier-origin winner fits and 40 scalar calibration fits across the two separate NCAA tracks, with 141 fresh owner fixture tests. Those counts are split evenly by sex. No current-season forecast, promotion or order was issued. Independent full-byte verification covered the final return and all 436 declared checkpoint objects.

The historical review combines 94 retained recipes and 22,408 represented games across the two tracks. Its 1,487,164 model/game rows repeat games across recipes; they are not 1,487,164 independent games. Full-source, exact common-population and matched MARKET comparisons retain separate denominators. The 22,426-game feature census leaves 18 cases without a supplied prediction; their exact exclusion reasons were not established by the compact evidence.

### One measurement contract

Winner comparisons use natural-log loss, Brier score on the original probabilities, accuracy with half credit at probability 0.5, calibration bias and fixed-bin calibration. Probability ties produce no directional pick. Margin and total predictions use MAE and RMSE in points. Every paired comparison uses the same games, targets and reference observations. Historical evaluation is development-exposed reconstruction, not a record of prospectively issued picks or untouched confirmation.

MARKET is the inherited qualified bookmaker-consensus source. It is separate from each named provider and from the later stored median-consensus definition. No historical named-provider comparison or historical spread/total settlement is inferred from that consensus. Winner accuracy, probabilistic scores and executable economic value answer different questions.

The current observation snapshot is November 2 at 05:17 UTC. Stored odds remain observations from November 1 at about 21:07 UTC. Public scoreboard monitoring did not refresh the odds feed. Provider completeness, current model-provider disagreement wins, profit, ROI and closing-line value remain unestablished. CollegeBasketballData's rate-limit pause remains in force.

### Men's matched historical result

On 1,633 matched games from the season ending in 2026, the fixed B029 linear model scored Brier **0.200258**, natural-log loss **0.581203** and accuracy **68.28%**. MARKET scored **0.195786**, **0.570362** and **67.18%**, respectively. The model made more correct directional picks while assigning worse probabilities by both proper scoring rules. Its directional disagreements contained **62 model-right / MARKET-wrong** outcomes and **44 reverse** outcomes; these are reconstructed historical comparisons, not wagers.

A B030 calibrated variant improved this model comparison to Brier **0.199150** and log loss **0.578396**, still worse than MARKET on those metrics. There is no inherited matched men's MARKET cohort for the season ending in 2025. Missing quotes are not zero market performance.

### Evidence and next work

The accepted B030 owner-return digest is `842c299af8d177b289cc12568c8eb2faaac0a3598427d513156983f409aeabd9`. The new private study is prepared research only; there is no claimed successor execution or improved score. Private runtime packages, per-game records, feature transformations, weights, provider responses and execution handoffs remain outside this public repository.

The March tournament Brier records near 0.1028 and 0.1034 use different populations. They are not all-season baselines or reproduced NCAA recipes. The original serving recipe and its runtime, numerical, source-time and prospective-issuance gates remain unchanged.

See the [publication boundary](../../docs/PUBLICATION_BOUNDARY.md) for the distinction between inspectable aggregate evidence and privately reproducible research.
