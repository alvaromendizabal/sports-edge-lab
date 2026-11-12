# NFL selected model card · N072 actual return

[Latest all-game selected forecasts](season_review_n076.html) · [Owner evidence](2026-11-11-n072-actual-n073-prepared.json) · [Prior model card](CURRENT_MODEL_CARD_N072_SNAPSHOT.md)

**Latest execution: N075 returned resumable after resource admission was refused, with known zero fits, forecasts and paid calls.** No newer selection or promotion supersedes the scorecards below. [Actual execution status](2026-11-11-n075-actual-n076-continuation.json). The 772 selected N072 rows and original issue clocks remain intact.

**N072 retains 18 metric/horizon-specific primary selections and nine operational fallback roles. No independent production promotion is established.** The verified completed phases contain at least 69 new fits; original whole-run counters remain null after the final refresh failed. The selected display contains 772 already-issued rows for 112 confirmed future games.

Every table row follows the same selected candidate across 2024 and 2025. Objectives and historical horizons are separate; a days-ahead current issue is not relabeled as a one-hour or two-hour forecast.

## Historical comparison: 1 hour(s) before kickoff

| Selected objective | Public alias | 2024 | 2025 | Pooled | Games |
|---|---|---:|---:|---:|---:|
| Winner accuracy | Selected model 1 | 71.93% | 63.73% | 67.84% | 569 |
| Winner log loss | Selected model 3 | 0.605012 | 0.638486 | 0.621719 | 569 |
| Winner Brier | Selected model 3 | 0.207684 | 0.223769 | 0.215712 | 569 |
| Point margin MAE | Selected model 5 | 10.008260 | 10.018003 | 10.013132 | 570 |
| Point margin RMSE | Selected model 5 | 13.057690 | 12.800020 | 12.929497 | 570 |
| Point margin marginal CRPS | Selected model 5 | 7.283699 | 7.199146 | 7.241423 | 570 |
| Total points MAE | Selected model 9 | 9.955067 | 10.729888 | 10.342478 | 570 |
| Total points RMSE | Selected model 9 | 12.900565 | 13.488984 | 13.198054 | 570 |
| Total points marginal CRPS | Selected model 12 | 7.285066 | 7.606911 | 7.445988 | 570 |

## Historical comparison: 2 hour(s) before kickoff

| Selected objective | Public alias | 2024 | 2025 | Pooled | Games |
|---|---|---:|---:|---:|---:|
| Winner accuracy | Selected model 2 | 69.12% | 65.49% | 67.31% | 569 |
| Winner log loss | Selected model 4 | 0.620667 | 0.616461 | 0.618568 | 569 |
| Winner Brier | Selected model 4 | 0.215025 | 0.214361 | 0.214694 | 569 |
| Point margin MAE | Selected model 6 | 9.960953 | 10.076034 | 10.018494 | 570 |
| Point margin RMSE | Selected model 7 | 13.016251 | 12.807722 | 12.912407 | 570 |
| Point margin marginal CRPS | Selected model 8 | 7.303503 | 7.198659 | 7.251081 | 570 |
| Total points MAE | Selected model 10 | 9.870659 | 10.635246 | 10.252952 | 570 |
| Total points RMSE | Selected model 11 | 12.752940 | 13.425951 | 13.093771 | 570 |
| Total points marginal CRPS | Selected model 13 | 7.151308 | 7.607862 | 7.379585 | 570 |

Winner support is 285 games in 2024 and 284 in 2025; one tie is excluded. Point targets retain 285 games each season. Selection and repeated research expose these completed seasons. The results support forward shadow monitoring; no independent confirmation or automatic promotion is claimed. Marginal CRPS does not establish joint-score quality or calibrated cover probabilities.

## Distinct recovered original accuracy and probability leaders

A follow-up review aggregated **72 saved annual scorecards from 24 original variants** without fitting or inferring a model. Under the original annual rolling-origin policy, each variant uses its state fitted through 2023 for the 280 saved 2024 games and its state fitted through 2024 for the 277 saved 2025 games. The combined cohort has **557 games**; it is different from the 569-game newer winner-selection cohort above.

| Best objective among the 24 saved original variants | Original model | 2024: 280 games | 2025: 277 games | Combined: 557 games |
|---|---|---:|---:|---:|
| Winner accuracy | Torch AB | 200/280 (71.43%) | 188/277 (67.87%) | **388/557 (69.66%)** |
| Probability log loss | Torch B | 0.578881 | 0.612150 | **0.595426** |
| Probability Brier | Torch B | 0.196388 | 0.212976 | **0.204637** |

TF AB has **387/557 correct, 0.595542 log loss and 0.204919 Brier** under the same annual fit-origin policy. It is a strong comparator, but Torch AB has the highest saved combined accuracy and Torch B has the lowest saved combined log loss and Brier. The objective-specific leaders must not be collapsed into one universal champion. The matched-subset table below remains the valid old-versus-new comparison; unequal full cohorts are not ranked against each other.

On the separate **77-game archived 2026 cohort**, original **TF A** has the lowest saved log loss (**0.641820**) and Brier (**0.225116**) among the 24 variants, with **50/77 correct**, tied for the highest accuracy. This is a **post-hoc descriptive ranking of already-exposed outcomes**, not a current-season selection, complete 136-game score or newly issued result. The archived 2026 ranking does not choose the next forward model or alter existing forecasts.

These recovered results are winner-head metrics only. They do not establish new original-model margin, total, cover or joint-score leaders. Full historical source-clock auditing remains pending, original issuance is not established by saved predictions alone, and **no promotion is authorized by this aggregation**.

## Earlier models are preserved and compared

The owner reviewed **144 original fitted states, 28,512 saved prediction rows and 192 scorecards**. Of 384 attempted old-versus-new comparisons, **144 have exact matched game, target and information-cutoff cohorts; 240 are non-comparable**. These are exposed descriptive replay results with a full source-clock audit still pending. Recovery is not new training or proof of original issuance.

| Saved older model / fit origin | Season | Matched games | Older log loss | New one-hour probability selection, same games | Older / new correct |
|---|---:|---:|---:|---:|---:|
| TF AB / through 2023 | 2024 | 280 | 0.581692 | 0.606415 | 201 / 199 |
| TF AB / through 2024 | 2025 | 277 | 0.609542 | 0.641206 | 186 / 176 |
| Torch B / through 2023 | 2024 | 280 | 0.578881 | 0.606415 | 199 / 199 |
| Torch B / through 2024 | 2025 | 277 | 0.612150 | 0.641206 | 186 / 176 |

Those older models remain serious candidates: on these saved matched cohorts they have lower log loss than the new one-hour selection. Torch B’s original rolling-origin **0.595426 over 557 games** remains separate from the fixed-through-2023 **0.598780** result. Neither becomes a current-season champion solely from these exposed comparisons.

The archived 2026 Torch B replay remains **0.649255 log loss, 49/77 correct**; TF AB is **0.662046, 47/77**. These are 77-game replay cohorts, not all 136 completed 2026 games. A qualified 15-game early snapshot has **0.456838 log loss, 13/15 correct**. An exact approximately **0.40 full-season NFL result has not been authenticated**; the remembered result remains unresolved rather than discarded.

The saved **119-game Kalshi panel** still has **79 correct for the accuracy combination versus 76 for Kalshi**; its model log loss is 0.646823. The probability combination has **77 correct / 0.629080 log loss**; Kalshi's saved one-hour/two-hour values are 0.644579/0.644377. Event, target, horizon, non-tie and exposure qualifications remain. N072 does not establish a fresh full-season Kalshi comparison.

Current issues and missing-role reasons retain their original clocks. Current-season outcomes do not select these historical roles. Authentic earlier-game market paths can be candidate inputs only when fully available before the later game's cutoff; target-game live data cannot change its own pregame model or forecast. R13–R20 remain unexecuted source-gated studies.


## Promotion decision and current-season gaps

**No production promotion is established.** Better saved scores make a model a serious research finalist, not an automatically validated deployment. The registered evaluation requires:

| Gate | Required evidence | Current status |
|---|---|---|
| Identity and availability | Matched games, target, settlement, horizon, fit population and authentic information cutoffs | Partial; full original-model source-clock qualification remains pending |
| Historical comparison | Nested chronological selection, prior-origin OOF calibration/stacking and paired errors against the fixed incumbent | Exposed 2024/2025 development evidence is retained; it is not untouched confirmation |
| Uncertainty and stability | Predeclared support, season/week clustering, multiplicity control, calibration and stability checks | N072's 478 paired Holm comparisons yielded zero adjusted p-values below 0.05; no independent promotion is established |
| Forward confirmation | Unchanged precommitted policy evaluated on genuinely newly issued games after registration | Full current-season former-champion evidence is incomplete; exposed 2026 replays cannot supply this gate |
| Operational quality | Full-denominator coverage, source-gap truth, reproducible state, resource cost and rollback criteria | N075 deferred before model dispatch; N076 owner validation remains pending |

There is no universal log-loss or MAE number that bypasses these gates. Any new practical improvement threshold and minimum support must be registered before examining the confirmation cohort.

| Evidence requested | Available support | Limitation |
|---|---|---|
| Current-season selected champions | 136 completed games in the saved census | No complete newly evaluated champion/former-champion scorecard; 16 completed games lack the required original pregame vectors |
| Recovered original variants | Archived 77-game 2026 cohort | Exposed partial replay; not full-season or originally issued evidence |
| Kalshi comparison | Archived 119-game matched panel | Retained target, horizon and non-tie qualifications; not a refreshed complete-season comparison |
| DraftKings comparison | Source captures and qualified historical subsets only | Complete matched winner/margin/cover/total evaluation is not established |
| Polymarket comparison | Source captures and coverage diagnostics | Complete comparable target/horizon evaluation is not established |

The best saved original 2026 variant is displayed descriptively and does not select the next forward model. A missing primary champion issue is never filled with an operational fallback under the primary label.
