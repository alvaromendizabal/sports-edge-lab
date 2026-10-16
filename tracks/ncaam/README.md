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

**Current phase:** source acquisition and audit. No trained-model performance claim.
