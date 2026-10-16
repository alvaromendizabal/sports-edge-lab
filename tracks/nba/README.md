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

**Current phase:** source acquisition and audit. No trained-model performance claim.
