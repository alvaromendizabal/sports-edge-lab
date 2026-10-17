# Sports Edge Lab · NFL

**Current verified state — V060, October 17, 2026:** NFL V047 remains accepted. Native XGBoost/LightGBM/CatBoost fits completed on the 16-feature representation; no candidate/task qualified. The next planned V061 question is early-down pass/run neutral-situation history, with 52 features and 24 planned linear/XGBoost fits; it has not executed. The [public feature method](../../modeling/football_v061/README.md) supplies 23 offline checks and no model fits.

The current refresh downloaded six assets and verified four semantic changes. Revised PBP remains 14,031 rows / 80 games with no added game IDs. Audited history remains 498,285 rows across 2016–2026; the broader archive spans 1999–2026.

[Current model card](../../docs/MODEL_CARD.md) · [Data readiness](../../docs/DATA_READINESS.md) · [Feature strategy](../../docs/FEATURE_STRATEGY.md) · [V060 actual evidence](../../docs/status/football_v060/README.md)

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
