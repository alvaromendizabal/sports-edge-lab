# NCAA FBS · fixture coverage, forecast clocks and model evidence

[**Open the FBS game center →**](https://sports-edge-lab-fbs.alv-mendizabal.chatgpt.site) · [Latest observation and research-status metadata](observation-status-v046.json) · [Latest evaluated 683-game snapshot](current-capture-v045.json) · [V4 method and publication boundary](PUBLICATION_BOUNDARY_V4.md) · [Exact V045 README history](README-history-v045.md)

## Current state · V046

The dashboard accounts for **all 2,742 identified fixtures** across 2024, 2025 and 2026. The authenticated 2026 result observation at **2026-11-08T19:34:42Z (November 8, 11:34 AM PST)** contains **685 observed finals**. All **63 dated current-week games** and **56 previous-week games** have observed finals. The separate upcoming Pacific week, **November 9–15**, has **53 identified exact-kickoff fixtures**, with no observed finals at this capture. These are dated observations, not live scores. The source capture began at 19:34:40Z and completed at 19:35:24Z. [Exact observations and clocks](observation-status-v046.json).

The new capture adds **two finals** relative to the prior 683/61 snapshot and resolves **three previously TBD kickoffs**. It does not change official game IDs or ordered teams. There are now **2,646 exact kickoffs and 96 unresolved kickoffs**. Resolved times create new fixture epochs with predictions pending; no older forecast is rebound.

| Season | Identified fixtures | Original baseline forecast games | Current explicit output gap |
|---|---:|---:|---|
| 2024 | 920 | 679 | 240 early-history gaps and one unresolved kickoff |
| 2025 | 934 | 934 | No missing baseline targets in this identified inventory |
| 2026 | 888 | 790 | 95 unresolved kickoffs plus three newly resolved fixture epochs awaiting predictions |
| Total | 2,742 | 2,403 | 240 history gaps, 96 unresolved kickoffs and three new prediction identities pending |

The newly resolved games are **Purdue at Iowa (401858519, November 15 00:30 UTC)**, **Massachusetts at Toledo (401866463, November 12 00:30 UTC)** and **Central Michigan at Buffalo (401866469, November 19 00:30 UTC)**. The owner originally labeled these as fixture revisions; the correction preserves that label and identifies each as a TBD resolution. Two fall in the upcoming Pacific week. The original 99-TBD inventory remains selectable unchanged. [Metadata and epoch status](observation-status-v046.json).

## What changed in the dashboard

The default all-season view retains all 888 current-season fixtures. Previous, dated current and upcoming Pacific weeks are separate controls. Their full fixture denominators remain visible while team, result, target, computation-time or provider filters narrow the display. Each small weekly scope fits on one page; cumulative views retain bounded 30-game pages. A shareable URL and filtered CSV preserve the selected state.

Game cards and the compact table retain available legacy winner, home/winner probability, home margin, total and saved 80%/95% intervals. New **forecast-age and original lead-time labels** explain whether a displayed value was a long-range saved outlook, a nearer-origin snapshot, computed after its game, or lacks sufficient clock evidence. Age is measured against the dated capture, never the browser's current clock. An unissued snapshot is never relabeled as an issued forecast.

Game details now also show the **latest private research availability and clocks** for the separate 105-game changed-input study. Its new numerical grid remains private under V4; the existing public numerical controls are preserved byte for byte. The target/status table carries safe family names, computation time, registered target cutoff, original horizon and training/calibration availability. A future registered cutoff is not a claim that future information was available at computation.

## Six independent observation snapshots

| Observation | 2026 finals | Dated current-week finals | Source |
|---|---:|---:|---|
| November 6 original | 629 | 7 | [Original inventory](complete-season.json) |
| November 7, 2:23 PM PST | 647 | 25 | [V042 capture](current-capture.json) |
| November 7, 5:08 PM PST | 667 | 45 | [V043 capture](current-capture-v043.json) |
| November 7, 7:17 PM PST | 670 | 48 | [V044 capture](current-capture-v044.json) |
| November 7, 10:27 PM PST | 683 | 61 | [V045 evaluated capture](current-capture-v045.json) |
| November 8, 11:34 AM PST | 685 | 63 | [V046 observation and status](observation-status-v046.json) |

**Latest result coverage and latest evaluated coverage are different.** The original full-precision 683-game/61-current-week metrics remain dated at their earlier observation. Evaluation of the two new finals awaits an admitted owner execution. V046 reporting performs **zero new fits, forecasts or scientific evaluations**. It never computes a headline score from rounded public values. Older evaluations and their exact target/game cohorts remain selectable.

## Recovered owner work and retained model families

The authenticated V045 owner completed **23 base fits and seven calibrations**, producing **3,360 new private outputs on 105 changed-input games** across nine families and three fixed blends. This is actual earlier owner work, not a V046 refit. All 23 original states and standalone fit receipts were authenticated; no local estimator was restored or trained. Original results and timing records remain intact. The owner completed 15 current-source requests and zero native-history provider requests, then deferred further work at the original sustained resource-pressure admission gate; this was not simply a free-RAM claim. [Whitelisted research-status metadata](observation-status-v046.json).

Across retained studies there are **5,970 base fits, 1,836 calibrations and 91,270 saved target outputs**. These counts preserve successful work and do not turn outputs into issues or prove model quality. The prior **84,102 original outputs** and **3,808 earlier changed-input outputs** remain separate from the 3,360 newly recovered outputs. The original 2,403-game universe is unchanged; the new study is a later version for 105 of those games. It contains **51 of the 53 upcoming-week fixtures**; the two newly resolved fixtures require new target identities.

| Family | Winner / probability | Margin / total | Evidence status |
|---|---|---|---|
| Logistic regression | Executed | Outside family scope | Original and separate changed-input owner studies |
| Linear regression and ridge | Outside family scope | Executed | Original and separate changed-input owner studies |
| Extra Trees and histogram gradient boosting | Classifiers executed | Regressors executed | Original and separate changed-input owner studies |
| XGBoost and LightGBM | Classifiers executed | Regressors executed | Original and separate changed-input owner studies |
| CatBoost | Executed with three protected missing 2026 winner outputs | Regressors executed | Separate retained candidate; protected pending work not forced to refit |
| PyTorch and TensorFlow | Owner classifiers executed | Owner regressors executed | Original neural and separate changed-input studies |
| Fixed blends and calibration | Separate fixed presets and dated held-out calibration | Fixed point blends; saved intervals on individual regressors | Saved reconstruction controls; no automatic champion promotion |

Retained original counts are **V038 2,497 base + 681 calibrations / 33,642 outputs**, **V039 1,362 + 454 / 21,627**, **CatBoost 680 + 226 / 7,206**, and **original owner neural 1,362 + 454 / 21,627**. The separate first changed-input study retains **46 + 14 / 3,808**. CatBoost winner gaps remain **401858225, 401858226 and 401856811**; their point targets remain available. No completed unchanged study is repeated to increase counts. [Original study assets](three-season.json) · [Earlier changed-input study](changed-input-study-v044.json).

The original retrospective replay remains **622 games, 465 correct winners and log loss 0.5133276378012555**, separate from issuance and the other model families. The independent 301-game claim is not authenticated by this dashboard. [Retained replay](complete-season.json).

## V4 methodology and evidence classes

The selected fixed blend is a **legacy comparison control**, not an automatic permanent production champion. A candidate recipe, selection policy, fitted snapshot and issued forecast are distinct records. V4 prepares registered prior-season window comparisons and nested rolling origins: every origin may use only admitted earlier labels and features, with earlier-origin calibration and combination evidence. A changed admitted input requires a compatible new snapshot; an exact compatible state is reused. Feature refresh, parameter refit, calibration retention and new issue creation remain separate.

| Evaluation class | Current state |
|---|---|
| Original frozen issued | Zero independently authenticated issues represented here |
| Historical rolling reconstruction | Saved fixed-recipe chronological controls and separate changed-input studies; nested rolling selection not established by those controls |
| Genuine future-issued rolling | Prepared owner methodology; no authenticated future-issued record produced by this publication |
| Source-only reference | Four separate providers with their own identity, product, clock and missingness qualifications |

Long-range outlooks preserve their original horizons and need a later admitted refresh as kickoff approaches. Current results cannot retroactively repair earlier training or authorize an unregistered recipe change. Historical development remains exposed development. [Full scoped V4 method and publication boundary](PUBLICATION_BOUNDARY_V4.md).

## Metrics and four-provider comparison

Available scorecards retain accuracy, log loss, Brier, calibration error, ROC AUC and saved reliability bins for winner probabilities; MAE, RMSE, bias, empirical CRPS, interval coverage and width for points where recorded. Missing scores are unavailable, never zero. Exact target/game cohort hashes and already recorded paired comparisons preserve CatBoost's smaller winner cohort. Earlier current/previous/cumulative/historical cohorts remain distinct. The separate first changed-input study retains its dated 12-game/384-target evaluation; those scored outputs were computed at or after their reconstructed cutoff. [Stored evaluation](changed-input-evaluation-v045.json).

DraftKings, Kalshi, Polymarket US and Polymarket Global remain separate throughout the reference ledger and three-season coverage matrix. The older retained winner references have **600 / 708 / 680 / 702 values** among 888 fixtures before join qualification. The exact-common descriptive cohorts remain **479 / 481 / 482 games** at T−120 / T−60 / latest pre-kickoff. They use rounded historical inputs and do not prove a matching forecast cutoff. The retained replay trails all four references on that diagnostic; no unfavorable finding is removed. [Common-game evidence](common-game-review.json).

The newest authenticated capture contains **201 DraftKings target observations across 67 events**. Exact registered ordered-team and kickoff checks bind **33 events / 99 target rows** for display association; all 99 original observations were available by T−120 and T−60. These metadata associations do not prove historical model-input eligibility, fees, depth, liquidity or qualified cover. [Newest association and cutoff metadata](market-status-v046.json). The earlier evaluated capture separately retains **11 exact events / 33 target rows**, with 33 exact rows available by T−120 and T−60. Its **81 raw source-clock checks** are a different denominator and must not be labeled exact qualified rows. [Earlier exact associations](current-capture-v045.json) · [Newest metadata](observation-status-v046.json).

Full 2024/2025 provider matrices remain incomplete. Fees, depth and liquidity lack qualified evidence in this public report. Source-only lines and median-support intervals are not expected scores. **Qualified exact-line cover probabilities remain zero** in all three seasons. **Authenticated pregame issues remain zero.** An interval or point estimate never substitutes for an admitted signed-line/product/settlement/cutoff/distribution join.

## Feature readiness and missingness

The V4 registry contains **246 proposed feature contracts**, with **zero newly materialized, admitted or evaluated definitions** in this cycle. Proposal counts are not implementation, model performance or promotion evidence. Exact active feature recipes remain private.

| Group | Retained evidence | Next qualification requirement |
|---|---|---|
| Outcome history | Existing chronological studies and separate changed-input snapshots | Original availability and rolling-origin policy qualification |
| AP / Coaches / CFP and ratings | Source contracts reviewed; separate editions and explicit missingness proposed | Canonical team/edition binding, original publication/possession clock and exact historical vintage |
| Coaching / temporal encoding transfer | Source methodology reviewed without changing basketball | Football-specific identities, effective and known-at clocks, strictly earlier labels and origin-fitted transformations |
| Market levels, paths and interactions | Older RAW73/path studies, including negative findings | Provider/product/cutoff coverage, original selectors and historical possession |
| Injury / availability | Dated records plus older timing-uncertified negative study | Chronological player/team binding; no inferred historical contribution |
| Player role and replacement quality | Requested scope remains unqualified | Qualified starter, snap expectation, contribution and replacement evidence |
| Weather, travel and context | Proposed V4 contracts | Source/time/unit and historical-vintage admission before evaluation |

AP, Coaches and CFP are distinct sources. An unlisted team is not automatically rank 26, and vote points are not win probabilities. A public API range does not establish authenticated entitlement or historical availability. The 257/312 path cohort stays separate from 115/125 availability/path. Current rosters or cumulative usage do not prove historical injuries, expected snaps or replacement quality.

## Verification and remaining next action

All existing public numerical/source assets are pinned and preserved. FBS changes are restricted to `docs/fbs` and `examples/fbs_contracts`; other projects and shared policy files remain unchanged. Tests cover dated Pacific week boundaries, future and missing clocks, strict fixture epochs, historical snapshot stability, public/private field exclusion, all-game coverage, keyboard/mobile/browser states and downloads. Export uses the exact merged source and publishes an asset SHA/byte manifest to the existing Site.

The next owner action is the admitted V4 rolling cycle: materialize qualified inputs, register the three new fixture epochs, produce required nearer-origin snapshots and independent issue evidence, evaluate the newly observed outcomes and resume bounded source recovery. Production acquisition performance remains **NO_GO** until the required owner-side benchmark qualifies. A dated public dashboard does not establish live ownership, complete provider archives or production speed.
