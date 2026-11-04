# FBS all-game reporting and market clocks

[Open the published dashboard](https://sports-edge-lab-fbs.alv-mendizabal.chatgpt.site) · [Current model card](../../tracks/ncaaf/MODEL_CARD.md) · [Clock implementation](../../examples/fbs_contracts/market_time.py)

## What changed

The earlier public view exposed study aggregates and a dated V025 recovery snapshot. The current report adds all **888 observed 2026 games**, public game identities/results, rounded original-model replay outputs, separate rolling status and dated provider evidence. The full inventory remains present when a provider has no price. Team search, phase/native week, Pacific calendar week, provider, observation window and disagreement controls operate on that retained inventory.

The all-season table includes **622 completed and 266 scheduled games**, with **63 games in the recorded current Pacific week**. The prior complete calendar week contains 56 games and 46 correct replay winners. The full original replay contains 465 correct and 157 incorrect winner picks. These numbers refer to the authenticated source snapshot, not independently proven official-population completeness.

V026 is now a completed owner run: **100 new fits, 197 reused states, 297 committed states**, in 70.212253 seconds. The previous V025 failure remains available in the [dated recovery page](recovery.html), and all V024 historical work remains in [the historical explorer](research.html). A dashboard change performs zero owner fits.

The subsequent official schedule capture at **2026-11-03 23:34:51 UTC** confirms the same 888 identities and all 622 completed scores. The fresh DraftKings response contains **186 game-market records on 62 uniquely mapped current-week games**, captured at **23:34:50 UTC** with quote times retained separately. All 63 scheduled games remain visible. Automatic display uses the latest captured reference for scheduled games, even before future T−120/T−60 windows.

Native catalogs now join to **710 Kalshi, 711 Polymarket Global and 676 Polymarket US** observed season games. Catalog presence is not historical price coverage. In the 63-game current calendar week, captured numeric references cover **Kalshi 62 winner / 63 margin / 63 total**, **Polymarket Global 63 / 63 / 63**, and **Polymarket US 59 winner / 0 margin / 0 total**. US/global stay separate. These catalog midpoints have no individual quote timestamps and appear with their actual capture clocks in the current-snapshot view, and qualify on capture time for a later cutoff while the window remains pending until reached. Point-market values are the observed threshold closest to 50% probability, an explicitly labeled diagnostic center rather than a projected final score.

The frozen historical recovery snapshot, retrieved through **2026-11-04 00:11:43 UTC**, adds source-timed winner references on **591 completed Kalshi games, 598 completed Polymarket Global games and 572 completed Polymarket US games**. T−120, T−60 and strictly pregame records preserve their represented source clock and actual recovery clock. This is a partial acquisition wave, not continuous closing-price coverage or evidence that the model possessed these records before kickoff. All observations remain separate from original/rolling forecast admission.

## Four clocks answer different questions

| Clock or boundary | Meaning | Allowed interpretation |
|---|---|---|
| Schedule observed time | When the stored schedule/result response was observed | A dated inventory, with final status only as of that clock |
| Provider quote time | The event time attached to the represented price | Eligibility for a source-time benchmark at a chosen cutoff |
| Provider capture time | When the record was actually retrieved | Evidence of actual possession from that time onward |
| Forecast issue time | When an immutable forecast was actually issued | Prospective scoring, only when independently authenticated |

Historical backfill is valuable. Recovering an old price today does not make it a forecast issued yesterday or prove that the model used it. Conversely, incomplete model feature-value admission does not prohibit collecting or displaying a dated market observation. These are separate operations.

T−120 and T−60 compare observation clocks **at or before** their cutoffs. “Latest stored before kickoff” requires an observation or authenticated capture **strictly before** kickoff. “Latest stored observation” can include postgame information and is labeled accordingly. A catalog snapshot captured before the boundary can qualify on its actual capture clock even when the source omits an individual quote time. It is labeled **captured snapshot available by cutoff**, preserving `quote_at: null` and `clock_basis: retrieved_at`. Future windows show **latest known snapshot; cutoff pending** and are not final cutoff coverage. Valid source-timed historical records are preferred when available. Candle buckets extending past the boundary are rejected. “Latest stored” is bounded by the available archive; it does not assert continuous feed coverage or the last possible market tick.

## Identity and product matching

Every public game has one observed native game ID and ordered home/away identities. Provider observations enter a game only after a documented event mapping. Source-backed exact kickoff/ordered-school identity candidates remain labeled as candidates; a missing or disagreeing event is quarantined in the private audit. Equal-time conflicting values produce an explicit conflict rather than an arbitrary file-order winner.

DraftKings no-vig winner probabilities are derived from sportsbook outcomes. An offered home spread is negated to report the corresponding home-margin center. Prediction-market trades, candles and midpoint references retain distinct kinds. Spread and total ladder probabilities are not automatically point forecasts. Polymarket US and Global are separate products; coverage in one cannot fill the other.

The dashboard distinguishes provider records, numeric-reference games and games with timestamped references. Those counts do not imply qualified executable prices, verified fees/liquidity or a matched performance comparison. Source attribution appears in the dashboard footer. The [publication policy](../PUBLICATION_BOUNDARY.md#fbs-all-game-analytical-report-november-3-extension) permits the rounded analytical report and excludes raw provider feed arrays.

## Model and market evidence

The original 622-game replay has log loss **0.513328**, Brier **0.173252**, ROC AUC **0.769937**, margin MAE/RMSE **14.600/18.185** and total MAE/RMSE **13.093/16.290**. All nine native-week scorecards, calibration bins and complete replay metrics are exposed. The separate 301-game TF228 monitor remains separate.

On the archived matched DraftKings panel, the original model is worse: winner log loss **0.604359 versus 0.553191** on 192 games; margin MAE **14.325 versus 12.030** and total MAE **14.637 versus 13.329** on 199 games. All 40 winner disagreements remain inspectable, including 18 model wins and 22 DraftKings wins. The union of games having any archived target is not substituted for a target-specific denominator.

The completed V026 historical selection is mixed and does not promote a champion. 2024 and 2025 remain exposed diagnostics; no 2026 outcome tunes or selects. Annual coefficients remain fixed while admissible prior-game feature state may expand. Public per-game outputs are rounded; headline metrics preserve the original unrounded evidence.

## Reproducible checks and real limits

Run the renderer and independent generic contracts from the repository root:

```bash
python -m examples.fbs_contracts.build_season_review --check
python -m unittest discover -s examples/fbs_contracts/tests -v
node examples/fbs_contracts/tests/test_season_logic.cjs
```

CI also exercises the actual HTML in Chromium at desktop and mobile widths, real keyboard interaction, four provider selections, current/last-week windows, all historical winner disagreements, comparison CSV download and the complete 888-row no-script fallback. It rejects browser errors and external data requests. Public Python/JavaScript tests are software verification, not owner estimator fits or evidence of betting skill.

The report has zero admitted rolling forecasts and zero new genuine issues. The remaining raw-to-value feature implementation must pass independent numerical and causal checks before that changes. Data ingestion continues independently. No model, quote, price timestamp, game result, fee, fill, profit or statistical edge is invented to fill a blank. All current decisions remain **NO BET, $0 stake**.

The hosted site is a published snapshot of canonical GitHub source. Publishing the website does not refresh the underlying evidence. Exact source and capture clocks remain visible in the report.

## Recovered provider benchmarks

The complete frozen acquisition snapshot has **6,190 analytical game references** before public duplicate-current filtering. The public report reproduces **27 separate-method and 21 pooled provider/target/window panels** from full-precision owner model outputs and actual provider references. Every displayed cohort independently matches the sorted game-ID SHA-256 in its source scorecard.

| Latest stored strictly pregame winner cohort | Games | Original replay log loss | Provider log loss | Disagreements: model / provider correct |
|---|---:|---:|---:|---:|
| Kalshi | 591 | 0.508701 | 0.418094 | 43 / 76 |
| Polymarket Global | 598 | 0.514062 | 0.424407 | 43 / 78 |
| Polymarket US | 572 | 0.512559 | 0.432316 | 41 / 73 |

The original replay underperforms each recovered provider on these matched winner cohorts. This does not demonstrate a betting edge. The original replay lacks an authenticated issue clock, so equal model/market prediction timing is unproved; these remain descriptive retrospective comparisons. The dashboard includes all three cutoff panels, complete classification scores and native phase/week resampling intervals, keeping individual reference methods separate.

Partial point-ladder diagnostics use 12 Kalshi margin games, 11 Kalshi totals games and 27 Global games for each point target. Their thresholds are observed centers closest to 50% probability in the recovered ladder subset, not projected final scores. These one-week cohorts do not support resampling intervals. Current point centers use the fuller observed catalog; duplicate current rows derived from a smaller historical-recovery subset do not replace that catalog at the same capture clock. The private original wave and every row are preserved.

## Official identity repair after the frozen historical snapshot

The previously unmatched current-week UL Monroe–Arkansas State game is now joined through official team metadata and exact kickoff/ordered-team identity. The initial unsupported name substitution remains rejected. Verified official abbreviation and mascot metadata establishes the institutional identity bridge without fuzzy name matching or clock tolerance. Its original provider capture times remain unchanged. This restores current numeric coverage to all **63 Global games** for each target, **63 Kalshi point-reference games** and **62 Kalshi winner games**, and **59 US winner games**. The remaining Kalshi winner lacks a valid two-sided midpoint; US spread/total products are absent. The independently frozen historical comparison cohorts and model outputs are unchanged.
