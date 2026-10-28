# Sports Edge Lab · NBA

Player-minute and usage distributions, rotation-aware game forecasts, pace, spreads and totals.

This track lives in the shared [Sports Edge Lab](../../README.md) repository and `sports-edge-lab-dev` workspace. Its private archive prefix is `tracks/nba/` in the central data lake.

## Model sequence

1. Player minutes and availability distributions.
2. Lineup-adjusted usage and rate models.
3. Correlated player-stat simulations.
4. Game score and margin distributions.

## Feature families

- Recent minutes and rotations.
- Lineup combinations and role changes.
- Pace and possession efficiency.
- Schedule density, rest and travel.

## Source scope

- NBA/ESPN source interfaces and audited public play-by-play and box-score archives.
- The Odds API historical moneylines, spreads and totals.

These are acquisition and research targets, not assertions of complete coverage. The source/season audit determines which observations may enter each experiment.

## Temporal boundary

Final starting lineups, actual minutes and late injury updates must not enter a forecast produced before they were available. Player props require a separate event-market backfill.

## Acceptance criteria

Apply the [shared research protocol](../../docs/RESEARCH_PROTOCOL.md). Establish sport-specific identity mappings and source coverage before feature development. A market backtest requires an actual bookmaker quote and a recorded availability time. Track quality with log loss, Brier score, calibration and distribution coverage, then separately assess simulated market returns, closing-line value and uncertainty.

Current phase: controlled B003 historical experiments completed; source timing, MARKET training support and prospective confirmation remain incomplete.

## B003 basketball evidence

NBA added 19 new estimator units and retained the 15-predictor regularized strength probability model: pooled historical log loss 0.607468 across 2,497 games. The new adjusted and rich arms do not beat it. The selected point head is a separate Ridge model, with total bias still +2.66 points in ending 2026. Matched T−60 MARKET cohorts expanded to nine ending-2025 and 16 ending-2026 games; no advantage is established. The 41 upcoming games have later-version early outlooks, no qualified current prices and no settled prospective scores at the snapshot.

Read the [basketball study](../../docs/BASKETBALL_FOUNDATION.md), [generated league leaderboards](../../docs/BASKETBALL_RESULTS.md), [model card](../../docs/BASKETBALL_MODEL_CARD.md) and [executed notebook](../../notebooks/basketball_review.ipynb). The [public contracts](../../examples/basketball_contracts/README.md) use invented fixtures separate from actual aggregate results. B002 evidence and B001’s pre-modeling failure remain preserved. [B004 executed but stopped at its public-request ceiling](../../docs/BASKETBALL_B004_EXECUTION.md); no challenger was promoted, and B003 remains the latest fully completed real modeling release.
