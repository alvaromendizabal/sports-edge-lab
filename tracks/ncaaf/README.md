# Sports Edge Lab · NCAA football

**Latest verified aggregate milestone — V013, October 31, 2026:** [completed native research and matched-market results](../../docs/fbs/V013_NATIVE_RESEARCH_2026-10-31.md). The owner run completed 70 new estimator units (24 optimizer starts, 46 closed-form ridge solves). All six matched 2024/2025 target-season panels were worse than the market reference; MARKET remains unchanged. Current selections and private model artifacts are not published.

[Current dated aggregate](../../docs/fbs/v013-native-research-2026-10-31.json) · [FBS evidence index](../../docs/fbs/README.md)

## Earlier V061 state — preserved as dated history

**Verified state at V061, October 17, 2026:** college V048R1 remains accepted; V061 made no college fits. V060 native boosters and fresh FBS-only linear controls did not qualify a replacement. V062 prepares L1 margin/total fits on the frozen 60 fields; target rows remain FBS-versus-FBS and inherited FCS opponent context is disclosed.

Twelve of 14 selected official-school secondary representations now validate; two historical gaps remain. Original ESPN-source repairs remain zero. Fifteen newer finals have exact boxes but no newly captured drive summaries after V061's first robots request returned HTTP 403 and stopped the provider. Prepared V062 names 17 independent official sources: at most 14 HTML drive closures plus three PDF text-only captures, capped at 40 requests / 100 MB and zero ESPN or paid-provider calls. No V062 outcome is claimed.

[Historical model card](../../docs/MODEL_CARD.md) · [Data readiness](../../docs/DATA_READINESS.md) · [Feature strategy](../../docs/FEATURE_STRATEGY.md) · [V061 actual evidence](../../docs/status/football_v061/README.md) · [Prepared V062](../../docs/status/football_v062/README.md)

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

