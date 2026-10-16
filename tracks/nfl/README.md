# Sports Edge Lab · NFL

Quarterback-adjusted team strength, EPA-based matchups, calibrated win probabilities, point margins and game totals.

This track lives in the shared [Sports Edge Lab](../../README.md) repository and `sports-edge-lab-dev` workspace. Its private archive prefix is `tracks/nfl/` in the central data lake.

## Model sequence

1. Regularized win-probability classifier.
2. Opponent-adjusted team and QB ratings.
3. Joint score and margin distributions.
4. Usage-conditioned player props after the game-level audit.

## Feature families

- Rolling EPA and success rates.
- Quarterback availability and prior performance.
- Opponent-adjusted offense and defense.
- Rest, travel and forecast weather.

## Source scope

- nflverse schedules, play-by-play, rosters and statistics.
- official injury reports and archived weather forecasts.
- The Odds API historical moneylines, spreads and totals.

These are acquisition and research targets, not assertions of complete coverage. The source/season audit determines which observations may enter each experiment.

## Temporal boundary

Realized starters, observed game weather and final statistics are labels or postgame records unless a separate pre-decision source establishes availability.

## Acceptance criteria

Apply the [shared research protocol](../../docs/RESEARCH_PROTOCOL.md). Establish sport-specific identity mappings and source coverage before feature development. A market backtest requires an actual bookmaker quote and a recorded availability time. Track quality with log loss, Brier score, calibration and distribution coverage, then separately assess simulated market returns, closing-line value and uncertainty.

**Current phase:** source acquisition and audit. No trained-model performance claim.
