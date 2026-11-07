# Sports Edge Lab · NBA

Reproducible NBA forecasts, complete released-game inventories, chronological model comparisons, and source-qualified market and player-availability research.

This NBA track belongs to the shared [Sports Edge Lab](../../README.md) repository. Its public material contains sanitized aggregate evidence and invented engineering examples. Actual game-level forecasts, feature recipes, model weights, source responses, full journals, and execution packages remain private.

## Current research — November 6, 2026 Pacific

**Model breadth is now measured.** B050 completed 156 estimator fits, 156 training-only calibration records, and nine separately journaled prior-season blend optimizations. The study used six matched training origins and richer basketball/context inputs while preserving all earlier completed fits. It trained logistic/Ridge, ordinary least squares, Extra Trees, histogram gradient boosting, XGBoost, LightGBM, CatBoost, native CPU PyTorch, and native CPU TensorFlow. Neural results that underperformed remain in the same score tables.

The independent real-data qualification passed 4,450 assertions, including numerical reload and inference for every one of the 156 serialized models. No model was refitted during validation. Summed model wall time was 201.687 seconds, summed CPU time 366.682 seconds, and peak measured process memory about 1.26 GB, with a two-thread cap. A measured disk-reserve interruption retained completed outputs; continuation reused them.

**The actual B050 owner advanced through eleven committed stages, then failed in report assembly.** Its 2,761 owner selftests all passed; stages 00–10 committed. Stage 11 failed because a second merge treated display-only placeholder labels as literal teams and duplicated four official IDs. Stages 12–15 did not execute. The original failure and clocks are retained. B051 preserves source identities through repeated merges and selectively reuses the already completed historical comparison output. A local qualification passed the recovered report inputs through typed checkpoint encoding, publication, independent readback, commit and reload; that is software evidence, not a completed B051 owner run.

### B051: controlled market-path and injury ablations

B051 completed **216 new estimator fits and 216 training-tail calibrations**, with no repeated B050 fit or historical forecast issue. Five registered basketball/market/path arms ran with two fixed estimator recipes, three chronological origins and separate T60/T120 partitions. A separate injury-status study used 202 historical training games, 46 calibration games and an exact 83-game next-season evaluation at each horizon. Its earlier-season cohort failed the minimum training-size gate, and no current injury cohort was invented.

The feature pipeline streamed **82,197,177 archive rows** in batches of at most 65,536, retaining 3,678,168 unique bounded observations. It produced 5,456 game/horizon rows across 2,729 games, combining 63 retained basketball inputs with 9 market covariates, 21 target pregame-path features and 110 earlier-game pregame-path lag features. These are pregame paths; unverified in-game state and end-time alignment still prevent a full causal in-game-path claim. Independent checks cover every feature row and all six chronological partitions.

The primary 180-estimator experiment took 235.8 seconds of wall time and 349.7 CPU seconds, with peak process RSS about 311 MB and a two-thread cap. Feature extraction took about 153 seconds with peak RSS about 789 MB. The extra 36 injury estimators are counted separately from that primary timing. Current-season results cannot tune recipes, select blend weights or promote a challenger.

[Download the B051 sanitized aggregate research scores](public_monitor/evidence-b051-market-injury.json). The private exports retain every registered arm, target, period, cutoff, calibration view and negative finding. On the same 1,212 regular-season games in 2025–26 at T60 (25 Pacific week blocks), the registered histogram gradient boosting winner arm improved from log loss **0.611475 with cutoff market features to 0.601728 with target pregame-path features**. The paired change was **−0.009747**, with a 95% week-block interval of **[−0.013738, −0.005347]**. Adding earlier-game pregame-path lags then worsened log loss to **0.615359**. The provider reference remained better at **0.568053** on that common cohort. An isolated feature gain does not establish overall provider superiority or a promoted model.

On the separate 83-game injury cohort over nine Pacific weeks, the logistic winner arm improved descriptively from **0.707603 to 0.660184** log loss, with paired change **−0.047418 [−0.083792, −0.013272]**. The histogram boosting injury gain was smaller and uncertain. Archived report publication is evidence of public availability; later retrieval does not establish that this project originally possessed those reports.

The registered Ridge market-total arm failed sharply: RMSE **77.2859**, versus **19.6696** for its basketball-only counterpart. A no-refit attribution reproduced the saved predictions to numerical precision. Nearly constant training quote-age features received very small fitted scales; later age shifts generated extreme contributions. The failure remains in the scorecard. Any clipping, age transformation or model change requires a new prior-data preregistration; B051 does not silently retune or replace this result.



### Three-season scientific scorecard

[Download the complete sanitized aggregate model scores](public_monitor/evidence-b050-models.json): all 576 metric rows across the two previous seasons and current monitoring sample, with season, target, horizon, model version, cohort size, track, calibration class, uncertainty-support counts, and selection restrictions. Winner metrics include accuracy, log loss, Brier, ROC-AUC and calibration; margin/total metrics include MAE, RMSE, bias and supported distribution diagnostics. Full regular seasons and postseason are separate.

The table below is the **2025–26 regular season, all 1,230 games, T60, season-frozen, calibrated retrospective reconstruction**. Historical periods were development-exposed. Preprocessing and calibration used training data; current-season outcomes did not select families, recipes or blend weights. These results are not historical forecast issues or a promoted leaderboard.

| Model version | Games | Accuracy | Log loss | Brier | ROC-AUC | ECE |
|---|---:|---:|---:|---:|---:|---:|
| B050/catboost | 1230 | 0.6935 | 0.596426 | 0.204515 | 0.7408 | 0.0231 |
| B050/extra_trees | 1230 | 0.6886 | 0.597888 | 0.204925 | 0.7389 | 0.0292 |
| B050/hist_gradient_boosting | 1230 | 0.6846 | 0.599427 | 0.205862 | 0.7353 | 0.0159 |
| B050/lightgbm | 1230 | 0.6846 | 0.598619 | 0.205457 | 0.7364 | 0.0187 |
| B050/logistic_ridge | 1230 | 0.6837 | 0.597362 | 0.204838 | 0.7410 | 0.0387 |
| B050/pytorch | 1230 | 0.6683 | 0.609178 | 0.210381 | 0.7241 | 0.0187 |
| B050/reused_B049_strength15_score25 | 1230 | 0.6894 | 0.597875 | 0.205003 | 0.7407 | 0.0313 |
| B050/tensorflow | 1230 | 0.6545 | 0.619486 | 0.215203 | 0.7095 | 0.0291 |
| B050/xgboost | 1230 | 0.6959 | 0.595671 | 0.204108 | 0.7417 | 0.0284 |
| B050/ensemble_fixed_uniform_calibrated | 1230 | 0.6919 | 0.597047 | 0.204765 | 0.7411 | 0.0361 |
| B050/ensemble_prior_oof_raw_components | 1230 | 0.6862 | 0.596853 | 0.204641 | 0.7413 | 0.0329 |

The fixed equal-weight total ensemble also improved descriptively on an exact legacy pairing: on the same 1,156 games, ordered teams, T60 boundaries and final labels, its RMSE was **19.193719**, versus **19.221416** for the retained B035 predictions on that same subset. MAE was **15.235265 versus 15.349016**. The MAE difference was −0.113751, with a paired 25-week 95% interval of **[−0.291676, +0.060594]**. The interval crosses zero; no promotion follows. B035's original 1,164-game RMSE of **19.2345356111** remains a different, unchanged denominator.

The original B050 model tables are monitoring on 123 verified regular-season finals at their study clock. The B051 display now has 130 verified finals at November 6, 9:14 p.m. Pacific, with two games still live. Later results are scored in separate derived tables; the original predictions and 123/125-game model/provider cohorts remain unchanged. More favorable current results cannot select a challenger or revise an earlier forecast. Whole-season NBA log loss near 0.45/0.46 has not been established.

## Complete released inventory and forecast classes

The private calendar-led dashboard retains 1,277 current-season display observations: 1,274 official entries plus three separately identified secondary observations. The official entries comprise 1,200 assigned regular matchups, six regular-season team/time placeholders, 67 preseason entries and one Cup championship placeholder. All 1,200 assigned regular matchups have saved model projections; the six unresolved regular entries stay visible. The released schedule still lacks 30 assigned regular matchup slots, including six published placeholders and 24 slots without assigned pairings. Missing provider prices never remove a game.

The private dashboard now opens on the current Pacific week, provides direct week selection and full-season navigation, and displays separate winner, signed margin-threshold and total-threshold references for all four venues. Selected-game exports include the actual chosen family, track, horizon and saved projection. The same event universe drives private tables, downloads and comparisons. Each row separates a genuine historical issue, a retrospective reconstruction and a present early outlook. Season-frozen and weekly rolling views preserve their own origins and game-specific T60/T120 cutoffs. Future early outlooks are not final pregame forecasts. The existing five genuine T60 forecasts remain a separate immutable cohort, including the loss.

The [public season inventory contract](public_monitor/SEASON_INVENTORY_CONTRACT.md) and its invented negative examples demonstrate membership, duplicate and missing-field gates without disclosing real private game rows.

## Provider and injury research

DraftKings, Kalshi, Polymarket US and Polymarket international remain four distinct source identities. Product discovery is independent of model eligibility. Full-game winner, signed spread and total products require exact event, side, line, horizon and settlement checks; a contract probability is not a point-margin or total-point mean. Opening, latest-before-tip, T60, T120 and closing observations retain separate clocks. Minute observations do not claim every tick.

The B051 derived current comparison retains all saved probabilities and adds 2,620 newly qualified pairs from five later finals, for **69,911 exact model/provider pairs**. It reports 584 current comparison groups with common-support counts and paired Pacific week-block intervals; the five-new-final-only cohort has one week and therefore no estimable week-block uncertainty. The unfavorable current winner result remains visible: weekly XGBoost at T60 scores LogLoss 0.618200 versus Kalshi midpoint 0.560944 on the same 130 games, with model-minus-provider paired 95% interval [0.004986, 0.081907]. This does not establish a model advantage.

B050 fixed a concrete US discovery gap: list responses supplied primary products, while the documented event-detail request exposes the remaining groups. An actual 601-product response validated one full-game winner, 33 full-game spreads and 31 full-game totals; 536 other-period or unsupported products were retained in raw evidence and excluded from these full-game comparisons. Discovery is not itself a qualified pregame comparison.

The injury recovery contains 139 verified report versions and 14,910 parsed observations. Every T60/T120 report cutoff for the 123 scored current-season finals has a recovered publication. Seventeen team-cutoff entries are explicitly omitted by the source; absence is not imputed as a healthy roster. Publication, update and later retrieval clocks are distinct. B051 additionally recovered 68 prior-season reports and the latest current report, with 8,065 parsed rows, and completed the bounded 83-game historical injury-status ablation described above. Thirty-two candidate historical report URLs returned HTTP 403 and remain explicit gaps. Printed publication times, including historical filenames whose hour differs from the printed half-hour, control admission. Neither the panel nor the ablation establishes first-news timing or original pregame project possession.

The frontier program covers opponent-adjusted basketball form, possessions and pace, rest/travel, replacement and rotation uncertainty, historical probability paths, control duration, volatility, reversals, cross-provider divergence and personnel reactions. A future game's model may use only earlier game paths and information available by its cutoff. Missing verified game-end, possession, lineup and archived publication evidence remains a concrete admission condition; additional feature names are not treated as completed causal tests.

## Reproducibility and access boundary

NBA keeps immutable action intent, returned output, checkpoint preparation, independent publication readback, committed completion and final acknowledgement separate. Complete operation outputs survive a later persistence failure; unresolved intent without authenticated output fails closed. Earlier failed owners and unfinished originals remain failed or unfinished. Cached file statistics alone cannot authenticate changed bytes.

The public [offline engineering example](public_monitor/README.md), [research protocol](../../docs/RESEARCH_PROTOCOL.md) and [publication boundary](../../docs/PUBLICATION_BOUNDARY.md) explain the reproducibility contract. Real runtime handoffs and data remain private. Active dashboard labels describe science and source comparisons; historical financial controls are retained privately.

The public browser dashboard below remains a **dated November 3 aggregate snapshot**. The new model metrics in this README and its JSON companion are newer; this change does not claim a public game-data refresh or a new owner completion.

<details>
<summary>Preserved earlier NBA snapshots and their original qualifications</summary>


Player-minute and usage distributions, rotation-aware game forecasts, pace, spreads and totals.

This track lives in the shared [Sports Edge Lab](../../README.md) repository. NBA owns its experiments, checkpoints and derived outputs. Shared raw evidence is read-only and must pass NBA-specific identity and timing checks before use.

## November 6 season inventory contract

The [new season inventory contract](public_monitor/SEASON_INVENTORY_CONTRACT.md) keeps every supplied official event in the display, including future games, exhibitions, unresolved phases and reschedules. Missing predictions and provider observations cannot remove a game. It requires explicit reasons for missing fields, separates frozen/rolling/issued evidence and all four active venue identities, and attaches spread-cover probabilities only to an exact line. Binary contract probabilities cannot masquerade as point-margin or total-point forecasts.

The implementation and its negative tests use invented inputs. They prove membership closure against the supplied inventory; they do not claim that an external schedule, provider history or model cohort is complete. Real current data, model recipes, weights, full forecast journals and execution handoffs remain in the owner-private research workspace. The public model snapshot below retains its original November 3 clock.

## Dated public model snapshot — November 3, 2026

**[Open the NBA evidence dashboard](https://sports-edge-lab-nba.alv-mendizabal.chatgpt.site)** — a public browser-viewable static site, not an HTML download. The published projection contains only reviewed aggregates and invented engineering examples; it is not a live prediction service.

The [November 3 public evidence monitor](../../docs/nba/monitor.html) reports the last fully admitted **94-game fixed-model diagnostic**, not 94 prospectively issued forecasts: B003 log loss **0.6472**, Brier **0.2290**, and accuracy **61/94**. Its owner finished November 2 at 6:57 p.m. Pacific. Historical seasons and actual pre-tip source-possession limitations remain explicit; the current season cannot select a challenger.

A prior completed historical study contains **654 fits**. A later historical branch completed another **366/366 fits**, but its overall owner **failed** when a source refresh omitted an older possessed final. The next refresh reused the 366 fits, performed **zero new estimator fits** and passed **758 software tests**, but failed on a reconstruction-version mismatch after inputs refreshed. Neither failed owner is upgraded. Completed work and original issues remain preserved. That dated capsule did not establish a qualified provider advantage. It contained no admitted rolling current-season output.

The [offline engineering example](public_monitor/README.md) demonstrates immutable forecast versions, source-version drift, qualified result unions, pre-update outcome possession, frozen/rolling separation, matched-product gates and truthful partial-owner accounting. All event-level examples are invented. Read the [current sanitized capsule](public_monitor/evidence-v2.json) and [preserved earlier capsule](public_monitor/evidence.json), run the negative tests, and inspect the accessible, progressively enhanced page; no credentials or private models are needed.

Active comparisons are **DraftKings, Kalshi and Polymarket**, with US and international Polymarket products kept separate. Zero admitted matched comparisons is not zero source coverage: raw historical provider coverage and both disagreement directions remain unevaluated in this public capsule. Removed provider scopes remain preserved in the earlier evidence rather than silently rewritten.

## Preserved October 29 research snapshot

The authenticated B009 owner return completed 10 new NBA native estimator units. The NBA lifetime ledger contains 85 unique units; the 268-unit combined basketball count includes other leagues. B009 did not promote an NBA challenger or establish a qualified MARKET advantage. Replayed checkpoints are excluded from new-fit counts.

[B010-NBA research](../../docs/NBA_RESEARCH_CARD.md) is prepared as an independent branch; real owner execution remains pending. Its primary comparison registers incumbent and candidate features under both original and revised training windows, across the same two historical validation seasons. Current-season outcomes cannot select a model.

Review the [NBA evidence view](../../docs/nba/index.html), [experiment/model/source card](../../docs/NBA_RESEARCH_CARD.md), [public aggregate receipt](../../docs/evidence/2026-10-29-nba-b009-audit.json) and [invented branch example](../../examples/nba_branch/README.md).

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
- The Odds API historical winner-price, spread and total references.

These are acquisition and research targets, not assertions of complete coverage. The source/season audit determines which observations may enter each experiment.

## Temporal boundary

Final starting lineups, actual minutes and late injury updates must not enter a forecast produced before they were available. Player props require a separate event-market backfill.

## Acceptance criteria

Apply the [shared research protocol](../../docs/RESEARCH_PROTOCOL.md). Establish sport-specific identity mappings and source coverage before feature development. A market backtest requires an actual bookmaker quote and a recorded availability time. Track quality with log loss, Brier score, calibration, point errors, distribution coverage and paired uncertainty.

At the preserved October 29 snapshot, B009 NBA research completed without promotion and independent B010-NBA research was pending. Source timing, MARKET training support and prospective confirmation remain incomplete. See the current verified status above for the newer evidence boundary.

## B003 basketball evidence

NBA added 19 new estimator units and retained the 15-predictor regularized strength probability model: pooled historical log loss 0.607468 across 2,497 games. The new adjusted and rich arms do not beat it. The selected point head is a separate Ridge model, with total bias still +2.66 points in ending 2026. Matched T−60 MARKET cohorts expanded to nine ending-2025 and 16 ending-2026 games; no advantage is established. The 41 upcoming games have later-version early outlooks, no qualified current prices and no settled prospective scores at the snapshot.

Read the [basketball study](../../docs/BASKETBALL_FOUNDATION.md), [generated league leaderboards](../../docs/BASKETBALL_RESULTS.md), [model card](../../docs/BASKETBALL_MODEL_CARD.md) and [executed notebook](../../notebooks/basketball_review.ipynb). The [public contracts](../../examples/basketball_contracts/README.md) use invented fixtures separate from actual aggregate results. B002 evidence and B001’s pre-modeling failure remain preserved. [B004 executed but stopped at its public-request ceiling](../../docs/BASKETBALL_B004_EXECUTION.md); no challenger was promoted. That dated B004 result is preserved; the authenticated B009 NBA follow-up is reported above.


</details>

