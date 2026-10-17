# Sports Edge Lab · NCAA football

**Current verified state — October 17, 2026:** NCAAF V048R1 remains the accepted 60-feature team-history/opponent-adjusted-drive logistic/ridge baseline. The canonical modeling scope contains 9,089 completed games; 9,061 have a valid primary or separately validated recovered drive representation. The remaining 28 gaps and nine unresolved availability rows are explicit. Raw ESPN college PBP spans 2004–2026; counts are stored file records, not a deduplicated all-source play total.

Next: the fixed V058 small-MLP benchmark on the accepted 60-feature table. Earlier college HGB evidence is retained. No college player-history model, neural result or market advantage is claimed.

[Current model card](../../docs/MODEL_CARD.md) · [Data readiness](../../docs/DATA_READINESS.md) · [Research roadmap](../../docs/RESEARCH_ROADMAP.md) · [V057 evidence](../../docs/status/football_v057/summary.json) · [V058 implementation](../../modeling/football_v058/README.md)

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
