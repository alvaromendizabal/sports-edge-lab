# NCAA FBS · complete fixture inventory and recorded forecasts

[**Open the FBS game center →**](https://sports-edge-lab-fbs.alv-mendizabal.chatgpt.site) · [Latest results and full-precision evaluation](current-capture-v045.json) · [Latest evaluation of the separate changed-input study](changed-input-evaluation-v045.json) · [Preserved release history through V044](README-history-v044.md)

## Current state · V045

The dashboard accounts for **all 2,742 identified fixtures** in 2024, 2025 and 2026. Every selected game remains in the inventory even when a model or provider target is unavailable. The default remains the original V038 fixed equal blend. Publication creates **zero fits, calibrations, predictions or provider requests**. It adds an authenticated result/evaluation view and interface improvements; it does not establish live freshness or historical forecast issuance.

| Season | Identified fixtures | Baseline projection games | Explicit output gaps |
|---|---:|---:|---|
| 2024 | 920 | 679 | 240 early-history gaps and one unresolved kickoff |
| 2025 | 934 | 934 | No missing baseline targets in the identified inventory |
| 2026 | 888 | 790 | 98 unresolved exact kickoffs |
| Total | 2,742 | 2,403 | 240 history gaps and 99 unresolved kickoffs |

The source capture began **2026-11-08T06:27:42Z** and completed **2026-11-08T06:28:11Z**. It contains **683 observed 2026 finals**, including **61 of 63 current-week games** and **56 of 56 previous-week games**. The newest delta is **13 finals** relative to the immediately preceding capture, and **54** relative to the original November 6 snapshot. Official IDs, ordered teams, exact kickoffs and unresolved placeholders remain unchanged. Publication and model-computation clocks remain separate from these observations. [Source and metric pins](current-capture-v045.json).

The separate owner observation at **2026-11-08 07:21:42 UTC (November 7, 11:21 PM PST)** preserved a compact partial return. It reused the 3,808 saved changed-input outputs, completed 15 current-source requests and made zero native-history provider requests, then stopped when its original memory reserve was unavailable. This dated owner work is separate from publication and is not a live ownership statement.

### Five result snapshots, without replacing original forecasts

| Result observation | Observed 2026 finals | Current-week finals | Preserved report |
|---|---:|---:|---|
| November 6 original | 629 | 7 | [Original inventory](complete-season.json) |
| November 7, 2:23 PM PST | 647 | 25 | [V042 capture](current-capture.json) |
| November 7, 5:08 PM PST | 667 | 45 | [V043 capture](current-capture-v043.json) |
| November 7, 7:17 PM PST | 670 | 48 | [V044 capture](current-capture-v044.json) |
| Latest authenticated capture | 683 | 61 | [V045 capture](current-capture-v045.json) |

All **84,102 original model outputs** and **3,808 separate changed-input outputs** remain intact: **87,910 saved target records**, without changing the game population. The 22 pre-existing numeric/source assets are preserved byte for byte. The latest full-precision evaluation adds **455 outcome evaluations of unchanged original forecasts**. Earlier evaluation snapshots remain independently selectable. Headlines are copied from the authenticated full-precision evaluator; rounded browser values never rescore them.

## Find every game, target and evidence gap

The page opens with all **888 current-season games**, with the dated current Pacific week first. Current-week and previous-week views display all **63 / 56 games on one page**; full-season views use bounded 30-game pages. Game cards and the compact table show the winner, home/winner probability, home margin, total points and saved 80%/95% point intervals. An unavailable target states its reason. A saved margin cannot conceal a missing winner.

The full-period summary retains its complete fixture denominator while team, result, output, timing and reference filters narrow the visible list. **Compare this period** opens the stored evaluation for that period and result snapshot, rather than rescoring an arbitrary search subset. Per-game details compare all **26 saved model views**: 13 original reconstruction views, 12 separate changed-input views and the original 622-game replay.

New V045 controls make the remaining gaps directly inspectable:

- **Output computation time** distinguishes all saved targets before the reconstructed cutoff, a target at or after cutoff, unverified clocks, and no saved output. Exact original UTC fractions are preserved in the comparison; equality is at the cutoff. Missing or conflicting clocks stay unverified. These labels do not authenticate historical input possession or pregame issuance.
- **Retained reference target and coverage** find an available or missing winner probability, margin line/interval or total line/interval for the selected provider. Historical matrices not imported into the public report remain explicitly unavailable. The separate newest DraftKings capture never silently replaces the older four-provider references.
- **Shared view links and CSVs** retain these filters and evidence statuses. CSVs include computation status, target clock counts, selected provider/target availability, original intervals and source clocks. Clear filters preserves the chosen season, period, model and provider.
- **Every-family accounting** uses one selected fixture inventory, with declared winner-only/point-only scopes and disjoint complete, partial and absent groups. Selecting a family never fits or promotes it.

## Separate changed-input study and its current evaluation

The original owner completed **46 base fits and 14 calibrations**, producing **3,808 outputs on 119 registered 2026 games** across nine families and three fixed blends. **14 registered games** are in the dated current Pacific week; **105 are later**. There are no registered previous-week or 2024/2025 targets. The V044 run reused the saved outputs; V045 reporting does not repeat any completed fit. [Original immutable forecast projection](changed-input-study-v044.json).

In the latest capture, **12 of 119 registered games** have observed finals; the current-week scope has **12 of 14**. **All 384 newly scored refresh outputs were computed at or after their reconstructed cutoff.** Their scores remain descriptive reconstruction results. The evaluation panel derives availability from the recorded target/cohort counts. A pending or unsupported metric remains unavailable, never zero. The original V044 evaluation with zero observed finals is retained as a separate study snapshot. [Latest full-precision refresh evaluation](changed-input-evaluation-v045.json).

The study keeps its original 38-outcome training delta and two acquisition epochs. Later finals only evaluate those unchanged forecasts. **3,360 outputs were computed before their reconstructed cutoff and 448 at or after it**. Before-cutoff computation alone does not establish qualified historical sources or issuance. CatBoost's protected work was not refitted. No current-season parameter, blend, default or champion selection is made from these scores.

## Executed models and targets

| Family | Winner / probability | Margin / total | Retained evidence |
|---|---|---|---|
| Logistic regression | Executed | Outside declared family scope | V038 original; separate changed-input reconstruction |
| Linear regression and ridge | Outside declared family scope | Executed | V038 original; separate changed-input reconstruction |
| Extra Trees and histogram gradient boosting | Classifiers executed | Regressors executed | V038 original; separate changed-input reconstruction |
| XGBoost and LightGBM | Classifiers executed | Regressors executed | V039 original; separate changed-input reconstruction |
| CatBoost | Classifier executed with three protected missing 2026 winner outputs | Regressors executed | Separate V040 candidate; no forced repeat of pending state |
| PyTorch and TensorFlow | Original owner classifiers executed | Original owner regressors executed | V041 recovered study; separate changed-input reconstruction |
| Fixed blends and calibration | Separate fixed presets and chronological held-out calibration | Fixed point blends; saved residual intervals on individual regressors | Defaults unchanged; no score-based promotion |

V038 retains **2,497 base fits + 681 calibrations / 33,642 outputs**. V039 retains **1,362 + 454 / 21,627 outputs**. CatBoost retains **680 + 226 / 7,206 outputs**. The original owner neural study retains **1,362 + 454 / 21,627 outputs**. These are existing completed work, not new V045 fits. The three CatBoost winner gaps are official IDs **401858225, 401858226 and 401856811**; their point estimates remain present. All 63 current-week baseline games have winner/probability, margin and total outputs.

[Original three-season projections](three-season.json) · [V038 study](development-2026.json) · [V039 study](optional-study.json) · [CatBoost study](catboost-study.json) · [Owner neural study](owner-neural-study.json).

### Metrics and comparison rules

The model panel exposes accuracy, log loss, Brier, calibration error and ROC AUC for winner probabilities; MAE, RMSE, bias, empirical CRPS, interval coverage and widths for point targets where saved. Stored calibration bins and full-precision metric CSVs remain available. Empty metrics never receive a zero. Complete all-season, 2026 cumulative, previous-week, current-week and newly observed cohorts remain distinct.

Displayed model differences require the same target, game count and exact game-ID cohort. **Recorded paired common games** uses the independently stored matched model/baseline metrics when a family's missing targets reduce its cohort. CatBoost's winner comparison therefore keeps its smaller common cohort. Descriptive current-season differences, including unfavorable results, do not qualify a model for promotion.

The separate original replay remains **622 games, 465 correct winners, log loss 0.5133276378012555**. It is not a genuine issuance record. The separate 301-game claim is not authenticated by this dashboard. [Original retained replay and metadata](complete-season.json).

## Four providers, products and missingness

DraftKings, Kalshi, Polymarket US and Polymarket Global are separate throughout the game ledger, historical coverage matrix and exact-common-game comparison. The original retained winner references have **600 / 708 / 680 / 702 numeric values**, respectively, among 888 current-season fixtures before join qualifications. A quote's presence does not certify historical possession or a compatible forecast cutoff. The two prior kickoff-revision quarantines remain excluded from inappropriate joins.

The latest DraftKings capture has **87 target observations across 30 source events**: **81 pass source-clock checks**, and **6 are after kickoff**. Exact registered-name, ordered-team and kickoff checks admit **11 events / 33 target rows** for display; other event values remain withheld. **33 exact rows** were available by T−120 and **33 by T−60. These counts do not establish historical model-input eligibility. [Latest capture evidence](current-capture-v045.json).

The 2024/2025 public provider matrices remain incomplete. Product, quote type, source/cutoff clock and missingness are shown where retained; fees, depth and liquidity still lack qualified public evidence. Point lines and quoted median-support intervals are not expected-score forecasts. The older four-provider winner comparisons retain exact 479 / 481 / 482-game cohorts at T−120 / T−60 / latest pre-kickoff. All four references had lower log loss than the separate retained replay on those descriptive cohorts; rounded inputs and unproved matching forecast cutoffs prevent a model-selection claim. [Preserved common-game comparison](common-game-review.json).

**Qualified exact-line cover probabilities remain zero**, across all families. A saved point interval never substitutes for the exact signed line, product, settlement, cutoff and conditional-distribution evidence required for that target. **Authenticated pregame issues remain zero.**

## Feature evidence and remaining qualification

| Feature group | Evidence retained | Remaining gap |
|---|---|---|
| Outcome history | 145-feature chronological original studies; changed-input reconstruction kept separate | Retrospective availability proxies do not prove historical possession |
| Provider probabilities, signed lines and threshold paths | Distinct providers, exact game/cutoff metadata and older path studies | Incomplete historical matrices and strict availability qualification |
| Market path interactions | Original 33-fit study and 11 training-only standardizers; negative results retained | 257/312 path and 115/125 availability/path cohorts stay separate |
| Fees, depth, liquidity and account entitlement | Explicit missingness | No inferred entitlement or unsupported numeric fill |
| Injury and availability chronology | Dated records and older negative timing-uncertified study | No qualified historical 2024/2025 injury cohort or admitted injury-adjusted forecast established here |
| Player contribution, expected snaps, starters and replacements | No completed contribution model represented | Required player-role and contribution evidence remains unqualified |

Historical recovery activity or aggregate producer completion counts do not automatically expand the public quote matrix. The original [partial V036 source-health report](source-health-v040.json) remains dated evidence with its own failure denominators. Acquisition speed and production readiness require separate owner-side measurements. This interface makes gaps visible rather than implying complete underlying research inputs.

## Verification and preserved evidence

The FBS-only tests cover original-asset preservation, identity/result snapshot isolation, target-specific missingness, precise saved-clock boundaries, invalid/conflicting clock rejection, exact matched metrics, CSVs and responsive game/filter flows. The public exporter reads an exact Git commit, uses an explicit asset allowlist and records each published file's byte count and SHA-256. GitHub exact-head CI, canonical merge, native Site source and deployment receipts, and independent served-body readback are recorded separately in the private publication ledger. A deployment receipt alone is not independent verification of every served asset.

This README is the current guide. The complete prior README is preserved **byte for byte** in [README-history-v044.md](README-history-v044.md); its dated results retain their original scope. Existing successful studies, negative studies, failed attempts, source clocks and all original numeric assets remain intact. Other sports and shared workflows are unchanged by this FBS-only update.
