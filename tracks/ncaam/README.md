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

Current phase: controlled B003 historical experiments completed; source timing, MARKET training support and prospective confirmation remain incomplete.

## B003 basketball evidence

NCAA men added 19 new estimator units. Rich combined logistic with 63 predictors improved both historical seasons and reduced pooled log loss from 0.532072 to 0.525415 across 11,507 games. The paired descriptive block interval favors the new representation, but fixed-bin calibration error increased. On 1,143 matched ending-2026 games its log loss is 0.577570 versus MARKET's 0.567127. Earlier matched training support remains zero; no learned MARKET or integrated classifier qualified. Eight upcoming games retain early outlooks with no qualified current prices or settled prospective scores.

Read the [basketball study](../../docs/BASKETBALL_FOUNDATION.md), [generated league leaderboards](../../docs/BASKETBALL_RESULTS.md), [model card](../../docs/BASKETBALL_MODEL_CARD.md) and [executed notebook](../../notebooks/basketball_review.ipynb). The [public contracts](../../examples/basketball_contracts/README.md) use invented fixtures separate from actual aggregate results. B002 evidence and B001’s pre-modeling failure remain preserved. B004 owner execution is pending.
