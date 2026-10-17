# Sports Edge Lab · NCAA football

**Current verified state — V058, October 17, 2026:** NCAAF V048R1 remains the accepted 60-feature team-history/opponent-adjusted-drive logistic/ridge baseline. V058 completed 12 college MLP fits and no college HGB refits; all three MLP tasks failed qualification.

Future college forecasts and evaluation target **FBS versus FBS**. The canonical scope has 7,898 completed games, of which 7,895 are in the frozen table. Eight of 22 in-scope drive gaps have a locally verified repair awaiting V059 AWS execution; 14 would then remain. Six historical mixed FBS/FCS context gaps are deferred. Existing FCS history is preserved without standalone FCS work.

V058's FBS-only exposed win log loss was 0.554682 for the accepted reference versus 1.039290 for MLP over 1,606 games. These are subgroup scores, not a newly trained FBS-only model. V059 is a prepared repair/dynamic-state experiment, not an achieved result.

[Current model card](../../docs/MODEL_CARD.md) · [Data readiness](../../docs/DATA_READINESS.md) · [Research roadmap](../../docs/RESEARCH_ROADMAP.md) · [V058 evidence](../../docs/status/football_v058/summary.json) · [V059 local preparation](../../docs/status/football_v059/local_data_preparation.json)

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
