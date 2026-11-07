# NCAA FBS · every fixture, every recorded model target

[**Open the FBS season and model lab →**](https://sports-edge-lab-fbs.alv-mendizabal.chatgpt.site) · [Current page source](complete.html) · [Three-season game data](three-season.json) · [Full-precision V039 comparison](optional-study.json)

## Current review · V040

The existing dashboard accounts for **2,742 identified fixtures** across 2024, 2025 and 2026. **2,403 games have saved development projections**; 240 early-2024 fixtures lack admitted prior history and 99 exact kickoffs remain unresolved. All **790 known-kickoff 2026 games**, including all **63 current-week games**, have winner/probability, margin and total outputs in the retained fixed blend. These are dated reconstructed results; this publication does not refresh schedule, results or market quotes, and it does not authenticate historical pregame issuance.

### What is easier to inspect in V040

- **Every saved family for one game:** open a matchup to compare the original replay and all existing V038/V039 family outputs side by side, with winner probability, home margin, total, saved intervals and observed errors. Export that comparison as CSV. The default remains the original V038 fixed equal blend.
- **Derived score centers:** the comparison shows away/home centers from `(total − margin) / 2` and `(total + margin) / 2`. These may be fractional; negative unconstrained values remain visible. They are arithmetic from displayed point centers, not a new fitted target or a discrete predicted final score. Display errors never rescore headline metrics.
- **Target-specific coverage:** the selected game filters show separate counts for winner/probability, margin, total, saved interval pairs and qualified cover probability. A points-only family no longer looks like a complete winner model.
- **Exact-cohort differences:** compare recorded log loss or MAE against a chosen baseline only when target, game count and the exact game-ID hash agree. The interface preserves unfavorable differences and does not choose or promote a champion.
- **Saved calibration diagnostics:** inspect original full-precision reliability bins as a curve and a table. Families without stored bins are explicitly unavailable; no curve is regenerated from rounded public predictions. Both 80% and 95% interval widths are visible where recorded.
- **Full-precision metric export:** export the selected original metric rows, cohort identity, calibration bins and descriptive baseline differences. The export retains all recorded accuracy/log-loss/Brier/ECE/AUC and point-error/distribution fields, rather than the rounded cells shown on screen.

### Evidence that remains incomplete

DraftKings, Kalshi, Polymarket US and Polymarket Global retain separate identities and denominators. Their historical matrices and comparable quote clocks are not filled from an unverified owner log. **No qualified cover probability** is created without a matching signed line, product, settlement and cutoff. All 99 kickoff gaps and 240 prior-history gaps stay visible. Original V038/V039 forecasts, full-precision scores, defaults and negative findings are unchanged by this reporting work.

V038 retains **2,497 base fits + 681 calibrations and 33,642 outputs**. V039 adds **1,362 base fits + 454 calibrations and 21,627 outputs** on the same 2,403 games. The combined 55,269 outputs are not twice as many game identities. Publication itself performs no model fits or provider requests. New owner-return and scientific facts are admitted only through separately authenticated evidence; earlier dated notes below retain their original scope.

### Verification

The presentation's numeric failure tests reject missing point targets, unobserved outcomes, mismatched cohorts, absent metrics and inferred cover probabilities. Responsive browser tests cover all three seasons, the complete 63-game current week, model/target filters, stored-bin availability, per-game and metric CSVs, keyboard dialogs, and missing-output reasons. `examples/fbs_contracts/export_site.py` publishes an allowlisted exact Git source with per-file hashes; source publication and live served-byte verification are recorded separately in the private publication ledger.

## Preserved release notes

The following entries describe their original release and observation dates. Their older feature limitations do not override the current capability summary above. The immutable underlying model and provider artifacts remain separately accessible.

## V039 · all three seasons in the game center

The [existing FBS dashboard](complete.html) now exposes the same season inventory for game search, model views, details and CSV exports. Select 2024, 2025, 2026 or all three seasons. The default remains the complete identified 2026 schedule, with previous/current Pacific-week views. Provider coverage never removes a game.

| Season | Identified fixtures | Observed finals | Reconstructed games | Explicit gaps |
|---|---:|---:|---:|---|
| 2024 | 920 | 919 | 679 | 240 early fixtures lack admitted prior outcomes; one exact kickoff unresolved |
| 2025 | 934 | 934 | 934 | None in this retained identified cohort |
| 2026 | 888 | 629 | 790 | 98 exact kickoffs unresolved; all 63 current-week games have reconstructed values |
| **Total** | **2,742** | **2,482** | **2,403** | **240 prior-history gaps + 99 exact-kickoff gaps** |

[Download the sanitized three-season report](three-season.json). Winner probabilities, signed home margins, total centers and saved 80%/95% residual intervals are projected from authenticated original V038 outputs. Each detail panel keeps the model computation time, reconstructed cutoff and source capture separate. The fixed equal blend remains the preset default; it has no saved interval, and the interface does not invent one. Interval support and negative distribution findings remain visible. Numeric display is rounded; no headline metric is recalculated from display values.

The 99 unresolved kickoffs have `kickoff: null` and `kickoff_exact: false`; the original source placeholder is retained separately as `reported_kickoff`. Native weeks, two kickoff-revision quarantines, the Army–Navy week conflict and ten unbound championship slots keep their earlier meaning. The 2024 Robert Morris–Utah State placeholder is not presented as an authenticated 04:00 kickoff.

A twelve-row season/provider matrix makes projected and missing winner, margin and total references visible for DraftKings, Kalshi, Polymarket US and Polymarket Global separately. Quote/interval eligibility at T−60 is only a clock check. Historical possession, source entitlement, exact model-cutoff matching, fees, depth and liquidity require their own evidence. The 2024/2025 provider matrices are not imported into this public projection; their absence is not evidence that no product existed. Cover probabilities remain absent without a separately authenticated exact-line cohort.

This is **new reporting work that reuses the completed V038 scientific study**: 2,497 unique base fits, 681 calibrations, 1,232 compatible state reuses, 33,642 target outputs, and zero duplicate completed fit identities. V039's explorer itself performs zero fits and makes zero provider requests. Historical availability and genuine pregame issuance remain unproved; no automatic promotion or current-season selection follows.

### Newly executed V039 families

V039 completed **1,362 new XGBoost/LightGBM base fits and 454 calibrations**, producing **21,627 additional target outputs on the same 2,403 games**. Its full-cohort pass reused 24 compatible states from the earlier current-week pass. None of the original V038 scikit-learn fits were repeated. New classifiers, point regressors, held-out calibration and a fixed equal optional-family blend are selectable in the game center. The V038 fixed blend remains the default, with original values unchanged.

[Download the sanitized V039 study](optional-study.json). Its model comparison joins the original V038 baselines on exact cohort hashes and denominators. Per-game values are rounded displays; metrics retain the supplied full-precision calculations. The following rows describe the separately prespecified **V039 fixed equal optional-family blend**, with no score-based selection:

| Season | Observed games | Accuracy | Log loss | Brier | Margin MAE | Total MAE |
|---|---:|---:|---:|---:|---:|---:|
| 2024 | 678 | 0.6549 | 0.632021 | 0.220037 | 13.9362 | 13.4229 |
| 2025 | 934 | 0.7099 | 0.549703 | 0.186105 | 14.0713 | 13.1449 |
| 2026 | 629 | 0.7250 | 0.539265 | 0.181548 | 14.5565 | 13.2813 |

The new model study finished at **2026-11-07 03:41:02.446496 UTC**. It reused the sealed 145-feature outcome-history input and its declared 24-hour result-availability proxy; original acquisition clocks are not rewritten as earlier possession. The 2026 season is monitoring, and the seven current-week observed outcomes are too small to establish improvement. No new strict-qualified fit, genuine issue or champion promotion is claimed. Original 622-game replay metrics remain separate from the optional study's descriptive matched-subset comparison.

XGBoost CPU 3.4.1 and LightGBM 4.7.0 executed on one CPU thread. The science process measured about 672.01 seconds elapsed and 671.71 CPU seconds, with 390,708 KiB maximum process RSS. These are scientific-process measurements, not dashboard or full-workload acquisition benchmarks. Dollar cost is unavailable without a workspace rate; sports-provider refresh requests were zero. CatBoost, PyTorch and TensorFlow remain unexecuted because their dependencies were not admitted under the shared storage budget.

### Latest authenticated owner observation

The separate V038 owner observation at **2026-11-07 02:45:33.919003 UTC** deferred while V036 was active. It reused the 888/56/63 game reports and completed zero new fits, provider requests or recoveries. Its supervisor recorded worker exit 2; a separate parent-interpreter exit remains unproved. This is distinct from the newly completed local model study. Full-workload acquisition qualification remains **NO_GO**.

The generic projector `examples/fbs_contracts/build_three_season_review.py` authenticates the original prediction, result, input and fixture-source bytes before projecting permitted fields. It verifies exact official ID, ordered teams and kickoff for every admitted prediction; rejects duplicate targets, non-finite outputs, malformed intervals and unadmitted cover values; and excludes private feature arrays, model-state IDs and cloud paths. The earlier 2026 report and all original metrics remain unchanged.


The all-game view defaults to the preregistered fixed equal blend. It now includes 790 exact-kickoff 2026 games, including all 63 current-week games, with winner probability, winner, home margin and total points. All 888 identified games remain visible; 98 fixtures lack exact kickoff admission. The original 622-game replay remains separately selectable.

[Development forecast data](development-2026.json) is a whitelist projection of the completed local study, computed 2026-11-07T01:51:51.403891Z against the schedule observed 2026-11-06T20:28:52Z. The full-season resume added 214 base fits and 58 calibrations and reused 358 hash-verified states. Its 11,060 target predictions cover logistic, linear, ridge, Extra Trees, histogram gradient boosting and fixed equal blends. It used zero provider and S3 requests. XGBoost, LightGBM, CatBoost, PyTorch and TensorFlow dependencies were unavailable in this execution; adapters do not count as completed fits.

These are **RETROSPECTIVE_DEVELOPMENT_TIMING_UNCERTIFIED** results using 145 outcome-history features and retrospective event-time proxies. Historical availability, genuine pregame issuance and qualified improvement remain unproved. No current-season score-selected promotion occurred. The completed three-season study, reconciled 2026-11-07T02:03:38.667972Z, retains 2,497 unique base fits plus 681 calibrations (3,178 successful fits), 1,232 compatible state reuses and 33,642 target outputs across 2,403 games. No unchanged completed fit identity was duplicated. The dashboard presents 678 observed 2024 outcomes from 679 predicted games (240 early fixtures lack admitted history; one kickoff is unresolved), all 934 identified 2025 games and outcomes, the 629 observed 2026 outcomes, and the small seven-outcome current-week cohort. Each season exposes all 14 available family/target scorecards with its exact cohort identity. No cover probability is manufactured without an authenticated comparable line cohort.

The public build script validates exact official ID, ordered teams, kickoff, input cutoff, source bytes and hashes before projecting. Each source artifact is pinned in the development download. The earlier retained scorecards and provider comparisons remain separate.

## Earlier V038 reporting snapshot

### November 7 · V038 dated all-game review

[**Open the FBS season & model lab →**](https://sports-edge-lab-fbs.alv-mendizabal.chatgpt.site) · [Public page source](complete.html) · [All-game data](complete-season.json)

The main dashboard now opens on **all 888 identified 2026 fixtures**. It includes the complete cumulative capture, the 56-game previous Pacific week and the 63-game current Pacific week, team/ID search, result and model-coverage filters, native-week selection, pagination, downloadable data and keyboard-accessible game details. The active review uses analytical terminology throughout.

The latest authenticated schedule observation is **2026-11-06T20:28:52Z**, with capture completion at **20:29:25Z**. It contains **629 observed completions** and 259 fixtures without an observed final. This is a dated capture, not live state. The two additional finals relative to the older public snapshot are UTSA 29–60 Florida Atlantic and James Madison 54–23 Southern Miss. Seven current-week games were observed complete.

| Scope | Identified games | Observed complete | Retained model replays | Authenticated rolling issues |
|---|---:|---:|---:|---:|
| Cumulative 2026 | 888 | 629 | 622 | 0 |
| Previous Pacific week, Oct 26–Nov 1 | 56 | 56 | 56 | 0 |
| Current Pacific week, Nov 2–8 | 63 | 7 | 0 | 0 |

Every fixture has visible winner, probability, home-margin, cover-likelihood and total fields. **266 games still lack retained model projections**, and no qualified cover probability, prediction interval or injury-adjusted forecast is admitted. The page gives the reason for these missing outputs rather than silently dropping the game. A retrospective replay does not become a pregame issue through republication. The 622-game replay retains 465 correct winners and log loss 0.5133276378012555; the separate 301-game claim remains unauthenticated here.

### Four-provider comparisons and historical models

Each matchup exposes DraftKings, Kalshi, Polymarket US and Polymarket Global separately, with winner probabilities, point lines or supported median intervals, native statuses, quote/acquisition clocks, declared cutoff, interval end, product and identity status. Numeric winner-reference counts are 600, 708, 680 and 702, respectively. These counts include descriptive and quote-clock-unresolved references; they do not prove qualification or historical possession. Polymarket US margin/total support is retained as **52 intervals for each target**, not scalar expected scores. Fees, depth and liquidity are absent from this projection.

The comparison panel reuses the exact-common-game winner diagnostics for T−120 (479 games), T−60 (481) and latest pre-kickoff (482). All four providers have lower log loss than the retained model on those cohorts. Inputs were rounded to four decimals, the matching model prediction cutoff is unproven, and these diagnostics do not select a model. No metrics were regenerated from rounded values in V038.

The historical explorer exposes **167 retained identities and 358 scorecards** across 2024/2025, with separate exact cohort hashes, family filters and target views. Winner metrics include accuracy, log loss, Brier, ECE, MCC and ROC/PR AUC when recorded. Point targets include MAE, RMSE and bias when recorded. The source does not report cover metrics. Full historical per-game provider matrices and authenticated per-game rolling retraining/issuance remain incomplete and are explicitly marked.

The 33-fit market-path study, its 11 training-only standardizers, the negative timing-uncertified injury study, the 48-candidate audit and all retained model identities are reused. The 257/312 path cohort remains distinct from 115/125 availability/path. Requested classifier/regressor coverage for every named framework still requires linked fit receipts; generic family labels are not evidence that every requested implementation ran. No current-season tuning or automatic promotion occurred.

### Provenance, execution and publication

The public whitelist builder authenticates its private input at **22,685,842 bytes**, SHA-256 `93333d34a4f337cf436938717950173f8fd05f0b5d81eb8e58b85a33871c5ad0`, before projecting only allowed fields. Original source, provider quote, acquisition, model-report and publication clocks remain distinct. Both kickoff revisions are quarantined; Army–Navy's native week/calendar conflict and ten unbound championship slots remain metadata.

The supplied V037 owner observation deferred at the ownership gate while V036 was active. This dashboard change generated **zero provider requests, zero model fits and zero forecast issues**. Full-workload performance remains **NO_GO** until a qualified bounded owner benchmark measures new durable individual completions. V032's 91 unresolved coordinates and 18 teacher-state proofs remain open.

`examples/fbs_contracts/build_complete_review.py` builds the whitelisted report. `export_site.py` publishes only allowlisted files from an exact Git commit, maps `complete.html` to the existing Site's home page and records per-file source paths, byte counts and SHA-256 digests. The prior season page remains a dated archive. Public data tests check the fixture/period census, new finals, null preservation, quarantines, provider separation, interval semantics, model cohort integrity and private-field exclusion. The existing browser CI now also exercises the new desktop/mobile experience, filters, dialogs, CSV export and metrics panels.

## Earlier dated reports (retained history)

The entries below describe their original observation dates and are not current execution or current coverage claims.

## November 6 owner audit: V035 failed before resource admission

The actual **V035 invocation failed during predecessor handoff**. Its source requires V034 history, but the completion-probe allowlist omitted V034. The first stopping condition is therefore the version admission bug. No resource phase was reached and neither the full-research nor independent memory/S3 acquisition phase started. Source requests, new fits and forecast issues were all **zero**.

The uploaded 84,837,823-byte return, its exact embedded source, every member manifest, the separate terminal log and the independent external completion agree. They record **diagnostic status 2**. The original entrypoint does not independently establish the interpreter exit; that observation remains unavailable. V034's earlier disk deferral is preserved separately: 60 checks over 300.155903329 seconds, ending 1,770,766,336 bytes below the unchanged full-work threshold after verified temporary-copy reclamation.

The owner audit adds independent verification. It retains all 888 identified fixtures, the ten separate unbound championship slots, the 622-game retrospective replay, all earlier fits and negative findings, and the dated local availability features. It does not refresh source clocks or certify a new forecast. The next handoff is prepared code until a new actual return proves execution.

New local V036 preparation completed **four fresh official availability reads at 06:13 UTC**. All four bodies are byte-identical to the earlier capture, with zero new status or feature changes; the prior 108 changes remain preserved. Separately, an independent audit checked 905 original game-state objects and 1,256,960 fields with zero projection mismatches. Its 22 conservative recorded-state candidates are not a strict market-path cohort or historical-possession proof. Nine of 31 inherited strict-clock flags need revision review: five score decreases and four within-period clock increases. No new fits, predictions, forecast issues or new action authorizations occurred.

The [dated execution audit](https://github.com/alvaromendizabal/sports-edge-lab/blob/main/docs/fbs/execution-2026-11-06.md) links the exact public source/return commitments to the evidence limits. A new [invented registry and receipt example](https://github.com/alvaromendizabal/sports-edge-lab/blob/main/examples/fbs_contracts/handoff_receipts.py) demonstrates the admission regression, partial-result preservation and independently captured process exits without exposing private production code or data.

[**Open the latest FBS review →**](https://sports-edge-lab-fbs.alv-mendizabal.chatgpt.site/frontier.html)

## Retained V035 preparation: V034 resource deferral and current source features

[**Open the latest FBS review →**](https://sports-edge-lab-fbs.alv-mendizabal.chatgpt.site/frontier.html)

The actual V034 owner return is authenticated from its uploaded bytes, embedded source, complete member manifests, terminal log and independently read external completion. It performed **zero provider collection, fits or forecast issues**. Reclaiming ten exact temporary replicas removed **258,194,352 bytes**, but the final measured **6,546,800,640 free bytes** remained **1,770,766,336 bytes below** the unchanged research reserve plus work headroom. All 60 admission attempts deferred. No unrelated process was signalled. The next prepared runtime separates measured memory/S3 acquisition from full-work admission; preparation is not owner execution.

New local evidence consists of **four official availability captures**, 29 exactly matched games, 58 team reports and 6,625 player rows. Unique team/name/roster matches cover 6,499 rows; 55 unmatched names and 71 jersey conflicts remain visible. Report and roster positions agree for 6,421 rows, while 36 position-group conflicts stay unknown. Observed cumulative usage exists for 3,355 rows and is unavailable for 3,270; it is not expected snaps, starter designation or replacement value. The capture comparison records **108 status changes**. Capture, source-declared update and preparation clocks qualify **116 current team–cutoff feature rows** across T−120/T−60. No historical availability is inferred and no new model is fitted or promoted.

The Week 14 investigation documents **ten official championship event slots with unbound participants**, separately from the unchanged **888 identified fixtures**. All ten announcements were checked; six conferences also have successful original HTTP copies and four failed original fetches remain recorded. The retained Army–Navy native-week/calendar interval conflict is explicitly flagged. These slots are not fabricated game IDs or market matches.

The completed **33-fit historical market-path/availability experiment and 11 training-only standardizers are reused unchanged**. Its negative findings, 7,491 predictions and paired uncertainty remain visible. The 622-game retrospective replay, 48-candidate independent historical audit and 167-identity registry retain their original populations and evidence classes. Current-season labels choose no champion.

The browser review exposes the actual owner stop, current availability qualification, all ten official event-slot links, full game filters and the retained alternatives. Private source payloads, player-level records, active model recipes, cloud paths and executable handoffs remain private. Earlier dated evidence is preserved below.


## V034 evidence review - actual V033 acquisition and new frontier research

[**Latest acquisition, research and every observed game →**](https://sports-edge-lab-fbs.alv-mendizabal.chatgpt.site/frontier.html) · [Retained model registry](https://sports-edge-lab-fbs.alv-mendizabal.chatgpt.site/models.html)

V033 is now authenticated as an actual partial owner run. It recorded **669 source requests** (654 native-market and 15 CFBD/Odds), zero learned fits and zero forecast issues. The historical receipt scan checked **5,030 of 5,038** listed records before measured disk headroom fell **6,909,952 bytes below the preserved admission threshold**. Calling the closed-inventory installer on that unfinished scan caused the final exception. This was an admission deferral, not a physically full disk. The next runtime preserves the cause, resumes exact receipts, reuses the completed RAW73 study and lets independent acquisition continue.

All **2,742 official rows** across 2024-2026 were independently reconstructed from original current source bytes. The November 6, 2026 00:25 UTC snapshot retains **888 observed 2026 games: 627 completed, 261 uncompleted**. Two future kickoff revisions are preserved. Week 14 exists in the calendar but has no game rows; full-universe completeness is not claimed. The main 622-game retrospective replay remains unchanged: 465 correct, log loss 0.5133276378, no historical issuance.

The fresh DraftKings capture yields **188 exactly matched rows across 63 games**; 24 rows across eight events remain quarantined for kickoff conflicts. The complete current native grid contains **567 slots**. Informative pregame winner/margin/total coverage is Kalshi **57/57/57**, Polymarket Global **56/56/56**, and Polymarket US **51/52/52**. Native point values remain supported median intervals, with separate bound clocks; they are never converted into expected scores or executable prices. All **25,330** retained/new references and **1,425** retained provider/horizon winner disagreements remain in the private complete exports.

The public review includes all 888 observed games, the full previous 56-game week and current 63-game week, source clocks, period/provider filters, keyboard access and CSV export. The newly registered historical study completed **33 local predictive fits across 11 fixed variants**, plus 11 separately counted training-only standardizers, with zero failed fits. All 33 fitted states, 7,491 predictions, 121 metrics and 27 paired uncertainty comparisons were independently reproduced without refitting. The path cohort (257 train / 312 test) and availability/path cohort (115 train / 125 test) remain separate. All tested path additions worsened their matched controls; the full availability/path interaction also worsened all three losses. No season-2026 outcomes selected a model.

The fixed market inventory retained 3,682 successful responses from 3,743 HTTP calls, including all 61 rate-limit attempts and one unresolved request. Of 904 game-state captures, 324 passed a broad boundary-marker gate, 46 had monotone play clocks, and 31 also had complete clocks. Historical possession and full-game continuous coverage remain unproved. A separate official MAC extension adds 32 PDFs and 1,597 player rows; 161 of 171 team-report pages match 112 games, ten remain unresolved, and no positional or certified publication-time coverage is invented. The new rows did not alter either frozen study. These are local, exposed-2025 experiments, not SageMaker execution or historical forecast issuance. The earlier negative injury study was preserved without refitting.

The new page has explicit population, missingness, source-revision and export tests. The existing FBS browser workflow also exercises its desktop/mobile views, filters, keyboard access and downloads. Private source archives, model recipes, execution packages and cloud identifiers remain excluded. Earlier dated evidence is preserved below.

### Previous recovery review - retained as dated history


[**Open the browser dashboard →**](https://sports-edge-lab-fbs.alv-mendizabal.chatgpt.site) · [Recovery and 2026 coverage](https://sports-edge-lab-fbs.alv-mendizabal.chatgpt.site/recovery.html)


## Verified recovery review — November 5, 2026

[**Explore all 167 retained models and 358 scorecards →**](https://sports-edge-lab-fbs.alv-mendizabal.chatgpt.site/models.html) · [Machine-readable registry](model-registry.json) · [Recovery audit](recovery-review.json)

The latest authenticated owner attempt is **V031, exit 2**, before source collection. Its predecessor guard counted the current launcher/worker family as another owner. No new fits, provider requests, rolling fits, or genuine forecasts came from that attempt. The previous V026 study retains **297 learned-state receipts: 100 new fits and 197 verified reuses**; it is separate from V024's 723-fit study. V033 is the next recovery release, prepared locally and not represented as a completed SageMaker run.

The current retained schedule has **888 observed 2026 games: 627 completed and 261 uncompleted** at its November 5 05:18 UTC capture. Week 14 is absent from that inventory; independent full-season completeness is not proved. The original replay remains **622 games**, 465 correct, log loss **0.5133276378**. New final scores do not create missing predictions. The separate reported 301-game log loss of 0.4655188082 is not substituted for the main cohort and was not independently reproduced in this recovery.

A new independent audit rescored all 48 retained candidates on 1,806 forward-validation games from 2022–2023: **144 target scorecards and 624 numerical comparisons passed**, maximum difference 1.11e-16. This adds zero fits and changes no champion. The model registry exposes all supplied V021, V023, V024 and V026 historical scorecards, source hashes, population hashes, unavailable metrics and development-exposure status. This is a count of retained model identities, not all-time training runs. The recovered V032 preparation verifies 82/173 feature coordinates; 91 coordinates and all 18 teacher-state proofs remain unresolved.

The 2026 replay and recovered market panels are retrospective. Same model/provider information cutoffs are not proved. A quoted midpoint, line or median bracket is not an executable offer; no broad market-beating or profitable edge is established. Injury research separates timestamp-qualified future observations from timing-uncertified historical archives. Unknown availability is never encoded as a healthy roster.

New local injury research tested four fixed alternatives on 154 training and 129 later 2025 games. There are 12 distinct candidate-target models and 24 local fit executions across two preparation invocations. Adding listed-absence features worsened winner log loss from 0.549204 to 0.600443; margin and total MAE also worsened. Missing historical report clocks keep this an exposed, timing-uncertified association study with no promotion. The dashboard provides every alternative and its exact cohort hashes. A separate rounded public-data comparison now puts all four venues and the model on 482 identical latest-pre-kickoff games; all four market references have lower log loss than the model.

### Earlier reports, retained as dated history


## Current season explorer and completed V026 recovery

[All 888 observed games](index.html) · [Clock and coverage contract](SEASON_EXPLORER_2026-11-03.md) · [Current model card](../../tracks/ncaaf/MODEL_CARD.md)

The public explorer retains **888 observed FBS-involving games: 622 completed and 266 scheduled**, including all **63 games in the recorded November 2–8 Pacific calendar week**. Original replay, actual results, rounded provider references and rolling status remain separate. A missing market never drops a game. Last week’s 56 observed games produced 46 correct original replay winners; the full replay produced 465 correct out of 622.

V026 completed the registered recovery: **100 new learned fits plus 197 independently checked reused states, 297 committed states total**, in 70.212253 seconds. The V025 failure remains preserved below. V026 did not issue a new forecast or fit a rolling model. Mixed exposed historical results do not promote a champion.

The season view includes all nine native-week scorecards, original winner/margin/total outputs, final scores, full replay metrics and calibration bins. Market controls separate T−120, T−60, the latest stored observation strictly before kickoff, and the latest stored snapshot. Recovered historical data keeps its actual retrieval clock; an authenticated snapshot captured before a cutoff can qualify on its capture clock even when an individual quote timestamp is absent. Future cutoff windows remain pending. Polymarket US and Global are separate products.

**Preserved prior attempt — V025, November 3, 2026: partial.** It preserved 197 committed fits, one failed forward attempt and 99 final learned states not attempted. At that attempt, V024 was the last completed owner study. [Inspect the recovery demonstration, all nine replay weeks and three-provider source coverage](recovery.html).


## Preserved verified study — V024, November 3, 2026

[Historical interactive comparison](research.html) · [Model card](../../tracks/ncaaf/MODEL_CARD.md) · [Verification record](V024_REVIEW_2026-11-03.md) · [Aggregate JSON](V024_AGGREGATE_2026-11-03.json) · [Executed notebook](../../notebooks/fbs_branch_review.ipynb)

The owner run completed **723 fresh fits in 24 minutes 45 seconds**, with zero reused or failed units. Independent verification matched all seven fixed panels on exact identities, ordered teams and labels across **918 games in 2024 and 934 in 2025**, and recomputed all 12 displayed metrics within 10⁻¹². The registered challenger has worse winner log loss than V023 in both exposed historical seasons. **No promotion is claimed.** Current raw feature-value recomputation remains unverified, so this run issued zero genuine forecasts and made zero rolling refits.

The public explorer preserves this negative result, exposes target/metric/reference comparisons and aggregate-only exports, and links to a real executed notebook. The [invented cohort example](../../examples/fbs_contracts/matched_cohort.py) rejects equal-count mismatches and label drift. It is a software demonstrator, not a private sports-model reproduction. V024 is separate from the earlier market-comparison studies below; their cohorts are not pooled.

## Earlier verified milestone — V013, October 31, 2026

[Completed native research: exact matched-market comparisons](V013_NATIVE_RESEARCH_2026-10-31.md) · [Full-precision aggregate](v013-native-research-2026-10-31.json)

The authenticated owner run completed **70 new estimator units: 24 optimizer starts and 46 closed-form ridge solves**. Native models were worse than the market reference on all six 2024/2025 winner, margin and total panels. **MARKET is retained; no production promotion or realized ROI is claimed.** The inherited 203-unit research registration stays separate. Incremental S3-backed consumer access reused the previously admitted 7,196,533-observation reconstruction overlay and performed 22 fresh representative partition checks—not a fresh complete raw scan or a second admission count.

The sections, dashboard, notebook and legacy `evidence.json` below preserve earlier dated evidence. V013 is a separate authenticated milestone; it does not rewrite old failed/prepared states or substitute its different cohorts into historical scorecards.

## Historical branch evidence

[Project](../../README.md) · [FBS dashboard](index.html) · [Aggregate evidence](evidence.json) · [Invented reproducer](../../examples/fbs_contracts/README.md) · [Notebook](../../notebooks/fbs_branch_review.ipynb)

## The earlier V135 execution failed before science

The supplied V135 owner return reports `FAILED` during its precredential source-contract tests. A required earlier prompt was preserved inside an archive while an inherited test still looked for its original root path. All 56 return payloads and 1,723 embedded source payloads match their hashes, but byte integrity did not establish semantic dependency closure. Of 3,239 executed tests, one errored. The run produced zero new estimator fits and zero new fit attempts.

At the time of that earlier V135 audit, V134 remained the last completed scientific release in its inherited evidence. The recent FBS sequence contains **18 completed fits across 19 attempts**: twelve pooling fits across thirteen attempts plus six explicitly FBS-tagged calibration/innovation fits. This is a league-tagged subset, not an arbitrary division of a combined NFL/FBS count and not an all-project lifetime total.

Eight 2024/2025 MARKET and retained-minimax scorecards were independently recomputed from saved game-level prediction rows. Their reported metrics match exactly. V134 innovation scorecards and completed status are carried from the supplied prior audit; the full V134 owner archive was not attached to this branch's preparation. That distinction remains explicit in the aggregate evidence.

## The negative result matters

On 740 matched 2024 games, MARKET log loss is 0.554096; orthogonal innovation is 0.555551. On 748 matched 2025 games, MARKET log loss is 0.538547; innovation is 0.539946. Lower loss is better. Calibration improves 2025 to 0.537568 but regresses slightly in 2024 to 0.554364. No learned replacement qualified across both seasons.

The 301-game 2026 monitoring panel shows lower descriptive innovation loss, but it has already been exposed and cannot select models, calibrators, feature families or thresholds. Repeated historical examination also means 2024/2025 are not untouched holdouts. Operational MARKET remains selected. This remains a dated analytical record.

## Prepared work is not completed work

FBS001 registers 203 intended estimator units: 183 core units plus 20 chronological cross-fit pool/gate units. It is a separate FBS-only owner program with independent ledgers and derived outputs. No FBS001 owner completion is claimed at preparation. Each executed unit must supply exact code and data identities, chronology, model state, convergence, paired metrics and timing.

The program's research plan has no elapsed-time or dollar stop. Durable checkpoints preserve productive work and support resumed stages. Actual provider quotas, terms, disk and memory safety, and transaction authorization still apply. Stored originals must be reconciled across shared project scopes before any missing paid snapshot can justify acquisition. A new source request is not a substitute for repairing lost normalization.

The prepared owner acquisition primitive supports exact historical requests only after a closed shared catalog proves the gap, a conditional shared reservation succeeds, the catalog is checked again, and current entitlement and quota are verified. **New paid live requests are disabled until a shared live capture-slot coordinator exists.** Different live capture timestamps could otherwise create different reservation keys for concurrent requests. Verified completed live originals remain reusable, and unresolved prior dispatches never authorize an automatic replacement purchase. The current runtime selects no proven missing target and reports `READY_BUT_NO_PROVEN_GAPS`; it does not dispatch a provider request.

## Public engineering contribution

The [standard-library example](../../examples/fbs_contracts/core.py) uses invented events to make four failure boundaries reproducible: FBS population/identity, actual source timing, atomic fit reentry, and complete shared-source content closure. It performs three synthetic fits, then reenters with zero new fits. Its tests alter clocks, labels, identities and saved bytes to verify rejection and preserve failed attempts.

The example contains no paid raw observations, individual forecasts, private source locations or credentials. It does not make provider requests, claim a sports edge, or alter the NFL and basketball research programs. [The dashboard](index.html) displays actual inherited aggregates separately from executable invented results.

## Runtime compatibility repair

[The v002 repair note](runtime-repair.md) explains the reproduced LightGBM warning, named prediction schema, version-specific regression matrix, and owner-progress boundary. The original evidence page remains a record of the first independent release.

## Pretraining source recovery

A later independent FBS attempt passed 122 tests, then entered shared-source inventory. At the returned audit snapshot, it had zero saved estimator completions or optimizer-start receipts. The replacement correctly declined to overlap its live writer. The elapsed stage-entry interval does not establish a deadlock. A further owner release is prepared; no new scientific result is claimed.

[The recovery example](pretraining-recovery.md) demonstrates explicit phase/work eligibility and an inactive SQLite checkpoint under its existing writer lock. Tests use a real local child and hot rollback journal, preserve the original bytes, and recover only a separate copy. No process signals, provider requests or private owner locations are included. The owner program schedules pinned-input science before broad source reconciliation; actual completion still requires its returned evidence.

## Process-handle portability

A subsequent recovery attempt refused before signaling because its Python build omitted at least one pidfd wrapper. That attribute check did not establish whether the running Linux interface was available. The [compatibility adapter and explanation](pidfd-compatibility.md) demonstrate per-operation Python/libc selection, an own-process signal-zero probe, exact errno reporting and descriptor cleanup. Tests remove the Python wrappers and exercise the exported libc path with local child processes. Operational errors do not trigger backend switching, and the adapter contains no numeric-PID signaling fallback. Target identity, ownership and application recovery eligibility remain separate caller obligations.




