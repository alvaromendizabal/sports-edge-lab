# Sports Edge Lab · NCAA football

[**Open the browser dashboard →**](https://sports-edge-lab-fbs.alv-mendizabal.chatgpt.site) · [Recovery and 2026 coverage](https://sports-edge-lab-fbs.alv-mendizabal.chatgpt.site/recovery.html)


## Verified recovery review — November 5, 2026

[**Explore all 167 retained models and 358 scorecards →**](https://sports-edge-lab-fbs.alv-mendizabal.chatgpt.site/models.html) · [Machine-readable registry](../../docs/fbs/model-registry.json) · [Recovery audit](../../docs/fbs/recovery-review.json)

The latest authenticated owner attempt is **V031, exit 2**, before source collection. Its predecessor guard counted the current launcher/worker family as another owner. No new fits, provider requests, rolling fits, or genuine forecasts came from that attempt. The previous V026 study retains **297 learned-state receipts: 100 new fits and 197 verified reuses**; it is separate from V024's 723-fit study. V033 is the next recovery release, prepared locally and not represented as a completed SageMaker run.

The current retained schedule has **888 observed 2026 games: 627 completed and 261 uncompleted** at its November 5 05:18 UTC capture. Week 14 is absent from that inventory; independent full-season completeness is not proved. The original replay remains **622 games**, 465 correct, log loss **0.5133276378**. New final scores do not create missing predictions. The separate reported 301-game log loss of 0.4655188082 is not substituted for the main cohort and was not independently reproduced in this recovery.

A new independent audit rescored all 48 retained candidates on 1,806 forward-validation games from 2022–2023: **144 target scorecards and 624 numerical comparisons passed**, maximum difference 1.11e-16. This adds zero fits and changes no champion. The model registry exposes all supplied V021, V023, V024 and V026 historical scorecards, source hashes, population hashes, unavailable metrics and development-exposure status. This is a count of retained model identities, not all-time training runs. The recovered V032 preparation verifies 82/173 feature coordinates; 91 coordinates and all 18 teacher-state proofs remain unresolved.

The 2026 replay and recovered market panels are retrospective. Same model/provider information cutoffs are not proved. A quoted midpoint, line or median bracket is not an executable offer; no broad market-beating or profitable edge is established. Injury research separates timestamp-qualified future observations from timing-uncertified historical archives. Unknown availability is never encoded as a healthy roster.

New local injury research tested four fixed alternatives on 154 training and 129 later 2025 games. There are 12 distinct candidate-target models and 24 local fit executions across two preparation invocations. Adding listed-absence features worsened winner log loss from 0.549204 to 0.600443; margin and total MAE also worsened. Missing historical report clocks keep this an exposed, timing-uncertified association study with no promotion. The dashboard provides every alternative and its exact cohort hashes. A separate rounded public-data comparison now puts all four venues and the model on 482 identical latest-pre-kickoff games; all four market references have lower log loss than the model.

### Earlier reports, retained as dated history


**Latest owner attempt — V025, November 3, 2026: partial.** It preserved 197 committed fits, one failed forward attempt and 99 final learned states not attempted. V024 remains the last completed owner study. [Inspect the recovery demonstration, all nine replay weeks and three-provider source coverage](../../docs/fbs/recovery.html).


**Latest verified study — V024, November 3, 2026:** 723 fresh fits, a preserved negative result, and zero live forecast issues. The registered challenger has worse winner log loss than V023 on both exposed historical seasons. Seven fixed comparisons share exact identities and labels on 918 games in 2024 and 934 in 2025; all 12 displayed metrics were independently recomputed. Current raw feature-value reconstruction remains unverified and live issue stays blocked.

[Interactive FBS evidence](../../docs/fbs/index.html) · [Current model card](MODEL_CARD.md) · [Dated verification](../../docs/fbs/V024_REVIEW_2026-11-03.md) · [Public aggregate JSON](../../docs/fbs/V024_AGGREGATE_2026-11-03.json) · [Executed notebook](../../notebooks/fbs_branch_review.ipynb) · [Run the invented example](../../examples/fbs_contracts/README.md)

**Earlier verified aggregate milestone — V013, October 31, 2026:** [completed native research and matched-market results](../../docs/fbs/V013_NATIVE_RESEARCH_2026-10-31.md). The owner run completed 70 new estimator units (24 optimizer starts, 46 closed-form ridge solves). All six matched 2024/2025 target-season panels were worse than the market reference; MARKET remains unchanged. Current selections and private model artifacts are not published.

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


