# NCAA basketball: actual B059 recovery and prepared B060

**The latest authenticated NCAA owner result is B059. B060 is a new continuation package awaiting owner execution.** This report covers men and women only. It records recovered results and substantive tested engineering without claiming new model performance from preparation.

## What the last owner run actually did

B059 ran from 2026-11-11 00:18:12 UTC to 02:29:48 UTC: **7,895.838 seconds, or 2 hours 11 minutes 36 seconds**. It committed **107 target-estimator fits, 17 scalar calibrations, and 36 empirical-residual fits**, and reused **108 historical target fits**. Its compact checkpoint evidence closes 232 new physical commits and 340 distinct indexed contracts. Recovery reads six bounded index objects totaling 348,874 bytes; importing the evidence itself earns zero new-fit credit.

Nine stages completed. The injury challenger stage stopped after **5,217.029 seconds**; seven later stages were not entered. The terminal condition was a latched I/O admission deferral. The recorded transient I/O pressure lasted approximately 15 seconds, even though the resource report showed 48 effective CPUs and a twelve-CPU project ceiling. Parent and completed-child CPU usage averaged approximately **0.81 cores** over the owner run. A twelve-CPU ceiling did not establish twelve concurrent estimator fits.

The new full-model frozen frontier was not reached. B059 issued **zero new current forecasts** and established **zero new promotions**. Completed fits and all earlier evidence remain recoverable.

## Current game coverage and forecast status

The authenticated report, observed at **2026-11-11 00:40:01 UTC**, contains **2,512 official game records**: 1,268 men’s and 1,244 women’s. Every record has `NO_ELIGIBLE_MODEL_ISSUE`. The canonical current source stream and exact reconciled source matches both contain zero games. Of the official records, 2,426 lack a verified exact source identity/time match and 86 lack an exact official tip time. Seven league-date responses have schema or identity gaps, retaining seven rejected source records; the qualified official denominator remains incomplete. These are not seven missing HTTP responses.

[Observed games and explicit forecast gaps](../data/ncaa_observed_games_b059.csv) preserves every supplied official record, its saved schedule/result fields, report time and missingness reason. Selected probability, margin and total fields remain empty. This is an observed schedule and source-gap export; it is not complete current-season coverage, a complete future schedule, or a set of newly issued forecasts. Earlier immutable forecast archives remain preserved privately; their record counts must not be called distinct games.

The source investigation traced the ESPN stop to an actual 20-second request timeout. Its unknown-status stop was inherited through subsequent releases without a new ESPN dispatch. B060 authenticates the original timeout receipt and permits one durably recorded recovery transition. It preserves every new failure and the separate Kalshi and CBBD HTTP 429 stops. A later recovered quote never gains an earlier observation clock.

## The remembered approximately 0.40 model

The stronger complete-model evidence was not invalidated by the newer 0.63–0.67 scores. Those weak results came from home-only and individual-feature controls in an incomplete research tranche.

Saved original frozen T−60 reconstruction evidence remains:

| Metric | Men, 329 games | Women, 345 games |
|---|---:|---:|
| Winner log loss | 0.412659 | 0.319149 |
| Winner Brier | 0.132882 | 0.100796 |
| Winner accuracy | 80.5471% | 85.2174% |
| Margin MAE | 10.834309 | 12.778114 |
| Margin RMSE | 13.839465 | 16.510206 |
| Total MAE | 14.055000 | 14.555540 |
| Total RMSE | 17.560432 | 18.166328 |

A separate **265-game men’s Polymarket international** cohort retains model log loss **0.399023**, versus market **0.346741**. Saved accuracy is **82.2642% versus 81.6981%**. Under that report’s half-credit tie rule the values correspond to **218 versus 216.5 accuracy credits**, not integer counts of correctly picked winners. This is not Kalshi. No authenticated numeric matched Kalshi winner cohort has been recovered.

These are saved exposed reconstructions, not a fresh rescore through November 11 and not independently confirmed originally issued performance. They may explain the remembered .40 result, but do not uniquely identify the remembered model. A different population can change log loss even when the estimator is unchanged. Probability and accuracy champions can also differ: a small direction-count advantage need not produce better probabilities.

## Completed-season research

The actual B059 return also preserves the **108 reused historical estimator jobs**, covering nine recipes per target, league and completed season. Their best reported values are:

| Population | Games | Accuracy | Log loss | Brier | Margin MAE / RMSE | Total MAE / RMSE |
|---|---:|---:|---:|---:|---:|---:|
| Men, 2024–25 | 5,758 | 0.726989 | 0.521482 | 0.176453 | 8.97903 / 11.48461 | 12.92947 / 16.52037 |
| Men, 2025–26 | 5,749 | 0.720125 | 0.523887 | 0.177840 | 9.16262 / 11.60028 | 13.68786 / 17.26882 |
| Women, 2024–25 | 5,280 | 0.768939 | 0.452119 | 0.150416 | 9.69140 / 12.24010 | 12.57928 / 15.92630 |
| Women, 2025–26 | 5,621 | 0.768013 | 0.454737 | 0.151069 | 9.67134 / 12.27099 | 12.59792 / 15.99313 |

Each metric can select a different recipe. Equal reported support does not by itself prove identical paired game IDs. These are exposed frozen-policy results, with no new fit or promotion credit. The old B003 engine’s completed-season scores are absent from these reports; the table does not substitute a different model for it.

The accuracy leaders report zero probability ties. Their exact metric-derived correct/incorrect counts are **4,186 / 1,572** and **4,140 / 1,609** for men in 2024–25 and 2025–26, and **4,060 / 1,220** and **4,317 / 1,304** for women. These are derived from the saved metric and explicit tie count, not newly rescored game-ledger comparisons and not matched Kalshi comparisons.

Earlier full-model pooled 2024–25 and 2025–26 evidence retains men’s log loss **0.522683**, margin MAE **9.071597**, and total MAE **13.308369** on 11,507 games. Women’s saved probability/margin leader retains log loss **0.453469** and margin MAE **9.681862** on 10,901 games; the separate total leader retains total MAE **12.588942** on that support. These pooled exposed selections are not independent per-season confirmation.

The incomplete B058 margin subset retains the following separate season minima:

| Population | Games | Lowest observed MAE | Lowest observed RMSE |
|---|---:|---:|---:|
| Men, 2024–25 | 5,758 | 9.001643 | 11.520400 |
| Men, 2025–26 | 5,749 | 9.163751 | 11.588117 |
| Women, 2024–25 | 5,280 | 9.687545 | 12.237956 |
| Women, 2025–26 | 5,621 | 9.633023 | 12.236289 |

Minima can belong to different recipes across metrics and seasons. They are not new champion promotions. Original issued, retrospective replay and genuinely future-issued rows remain separately scored. The new comparison writer also separates integer correct/incorrect/no-direction counts from tie-adjusted accuracy, and compares providers only on genuinely equivalent targets and cutoffs.

## What B060 changes

- Restores the actual B059 committed work and preserves all seven protected earlier scientific identities and the complete earlier source bytes.
- Removes the forced one-worker path and the lock held throughout parent estimator execution. Independent parent fits and spawned native fits share the measured whole-project ceiling, with native threads controlled.
- Adds reciprocal atomic leasing with the authenticated FBS coordinator. Acceptance evidence shows twelve NCAA and twelve FBS reservations remain disjoint and foreign reservations survive NCAA cleanup. Other sports’ separate coordinator implementations were not independently audited in this preparation.
- Waits cooperatively through transient I/O pressure, while retaining stop, budget, memory and integrity gates.
- Removes the arbitrary elapsed research cutoff. Finite registered work, genuine source gates, safe resource admission and the verified $200 monetary guard remain controlling.
- Compares all **26 full baseline recipes / 104 gender-season contexts**, followed by **66 grouped diagnostic recipes / 264 contexts**. Diagnostic findings cannot silently enlarge champion selection authority.
- Advances **eight unresolved materialized scalar features** using verified completion receipts. It permits **192 new selected rolling fit admissions**; exact reuse does not consume that allowance.
- Refreshes selected current forecasts immediately after baseline selection. Selected rolling work precedes optional later studies.
- Reuses source-population scans and batches exact per-row feature hashing while retaining identical scientific hashes. A synthetic hashing benchmark improved 2.0956 seconds to 0.01712 seconds for 256 × 123 cells; this is a hashing-only fixture result, not AWS or end-to-end speedup.

The twelve-callback and process concurrency tests establish scheduler behavior. **Real twelve-estimator AWS overlap, throughput, speedup and ETA remain unmeasured until the owner runs B060.** The public on-demand host quote was separately verified at $2.57/hour; B059’s owner pricing call was denied. Approximately $5.64 is therefore an elapsed whole-host estimate, not an invoice or exclusive NCAA attribution.

## Promotion and historical market-path limits

Winner accuracy, log loss, Brier, margin MAE/RMSE, total MAE/RMSE, cover probability and joint distribution roles remain distinct. B060 selection qualifies a candidate for registered research replay and prospective collection; it does not grant independent confirmation or automatic production promotion. Missing same-candidate season/cohort comparisons remain missing.

B059 did not reach the R13–R20 market-response studies. This evidence does not establish authentic opening/first-two-possession/period-boundary/2:00 tick coverage for DraftKings, Kalshi or either Polymarket product. The old checkpoint matrix remains an explicit unreevaluated inventory; it is not a completed coverage claim. New tests preserve target-game live-path invariance and source-clock exclusions. Qualified earlier-game paths may be tested when actually available; missing paths cannot be filled with invented zero moves or fabricated historical prices.

## Publication status and provenance

This update publishes aggregate results, selected-role availability and every supplied official game’s source-gap disposition. It publishes no private source package, model body, active recipe, raw provider/tick array, credential or private cloud location. It creates no betting interface.

The exact owner-return digest and machine-readable count/coverage evidence are in [B059_ACTUAL_B060_PREPARED.json](B059_ACTUAL_B060_PREPARED.json). Earlier [B058 evidence](B058_ACTUAL_B059_PREPARED.md) remains historical. A new authenticated B060 owner return is required before replacing these availability states with new predictions or declaring a new champion.
