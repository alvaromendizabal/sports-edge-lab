# Sports Edge Lab · NCAA football

**Current verified state — V060, October 17, 2026:** college V048R1 remains accepted. Native boosters and fresh FBS linear controls completed; no candidate/task qualified. New target rows are FBS-versus-FBS, while inherited history may include declared FCS opponent context.

Ten of 14 selected official-school sources now have validated secondary representations; four captured pages remain unaccepted. Original ESPN-source repairs remain zero. Fifteen newer cached FBS finals have exact team/player box checks, but current PBP/drive completeness is not established. V061 has not executed. Two additional historical representations are locally verified (12/14 locally; accepted AWS remains 10/14). Four historical parser cases use caches; a separate public ESPN capture for 15 current finals permits at most 40 public attempts with zero paid calls. Preparation made zero new source calls.

[Current model card](../../docs/MODEL_CARD.md) · [Data readiness](../../docs/DATA_READINESS.md) · [Feature strategy](../../docs/FEATURE_STRATEGY.md) · [V060 actual evidence](../../docs/status/football_v060/README.md)

<details>
<summary>Original acquisition-stage research plan — retained as history</summary>

The original plan below records intended feature families and model directions. It does not describe the complete accepted implementation; current cards above supersede its phase and coverage statements.

Opponent-adjusted play efficiency, quarterback and roster transitions, recruiting and schedule-aware margin forecasts.

This track lives in the shared [Sports Edge Lab](../../README.md) repository and `sports-edge-lab-dev` workspace. Its private archive prefix is `tracks/ncaaf/` in the central data lake.

## Model sequence

1. Hierarchical team offense and defense ratings.
2. Win-probability classifier.
3. Point-margin and total distributions.
4. Team and quarterback scenario models.

## Feature families

- Opponent-adjusted EPA/PPA.
- QB continuity and depth.
- Recruiting and transfers with publication dates.
- Coaching changes and schedule strength.

## Source scope

- CollegeFootballData games, plays, drives, statistics, rosters and ratings.
- audited public source archives.
- The Odds API historical moneylines, spreads and totals.

These are acquisition and research targets, not assertions of complete coverage. The source/season audit determines which observations may enter each experiment.

## Temporal boundary

End-of-season ratings, revised recruiting assessments and current rosters cannot stand in for the values available in a historical forecast week.

## Acceptance criteria

Apply the [shared research protocol](../../docs/RESEARCH_PROTOCOL.md). Establish sport-specific identity mappings and source coverage before feature development. A market backtest requires an actual bookmaker quote and a recorded availability time. Track quality with log loss, Brier score, calibration and distribution coverage, then separately assess simulated market returns, closing-line value and uncertainty.

**Current phase:** source acquisition and audit. No trained-model performance claim.

</details>
