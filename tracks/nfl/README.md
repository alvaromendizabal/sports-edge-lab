# Sports Edge Lab · NFL

**Current verified state — V061, October 17, 2026:** NFL V047 remains accepted. All 24 situation-feature linear/XGBoost fits completed on 52 fields; none of six candidate/task combinations qualified. The [public feature method](../../modeling/football_v061/README.md) remains a no-fit construction demo, separate from actual performance. V062 is prepared, not executed: a fixed L1 margin/total comparison on the original 16 fields, with cached references and no win-model refit.

The current refresh downloaded six assets and verified four semantic changes. Revised PBP remains 14,031 rows / 80 games with no added game IDs. Audited history remains 498,285 rows across 2016–2026; the broader archive spans 1999–2026.

[Current model card](../../docs/MODEL_CARD.md) · [Data readiness](../../docs/DATA_READINESS.md) · [Feature strategy](../../docs/FEATURE_STRATEGY.md) · [V061 actual evidence](../../docs/status/football_v061/README.md) · [Prepared V062](../../docs/status/football_v062/README.md)

<details>
<summary>Original acquisition-stage research plan — retained as history</summary>

The original plan below records intended feature families and model directions. It does not describe the complete accepted implementation; current cards above supersede its phase and coverage statements.

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

</details>
