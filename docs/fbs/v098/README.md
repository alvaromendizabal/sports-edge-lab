# FBS V098 review: verified V097 ablations and primary T-60 preparation

[Interactive report](index.html) · [Exact public evidence](data/status.json) · [FBS research history](../README.md) · [Preserved V096 / prepared V097 report](../v097/README.md)

## Actual result

The authenticated V097 invocation `20261118T194552Z-3788012f0c-fbs097` finished with child and supervisor exit **0**, a verified resumable return, and scientifically partial status. Its **306/306** registered source-ablation jobs completed: **204 validation and 102 frozen-test jobs**, **294 new base fits**, **294 calibrator fits**, **12 exact fitted states reused**, and **zero failed fits**. The earlier **936 completed frontier jobs** were preserved without redispatch.

The new XGBoost and CatBoost ablations added **204 policy variants**, bringing the comparison to **1,309 policies**. **None of the nine primary validation leaders changed. All 45 winners across the five weighting profiles and their validation values are unchanged from the preceding V096 return.** Negative or inconclusive comparative results remain part of the scientific evidence.

The scoped historical tally is six operationally failed attempts, two operational finishes with scientifically partial returns, and zero established full-V13 completions. The current partial finish adds no operational crash.

## Saved validation leaders

These are dated **T-120 exposed frozen reconstructions**, with annual completed-game denominators **919 / 934 / 755**. Selection uses 2024/2025 only, with 50/50 primary and 40/60, 30/70, 20/80, 10/90 sensitivity profiles. Sensitivity changes annual score aggregation only; it does not refit, change training-row weights or use 2026 outcomes to select a winner. The interactive report exposes all five profiles and the saved ranks of the primary policies.

| Objective | Family | 2024 validation | 2025 validation | 50/50 score | 2026 report |
| --- | --- | ---: | ---: | ---: | ---: |
| Winner accuracy | CatBoost | 0.746463547334 | 0.764453961456 | 0.755458754395 | 0.74701986755 |
| Winner Brier | LightGBM | 0.171695967295 | 0.162554530828 | 0.167125249062 | 0.162195153209 |
| Winner log loss | LightGBM | 0.511541401718 | 0.488720673551 | 0.500131037634 | 0.486724962116 |
| Margin MAE | LightGBM | 12.8091547038 | 12.242272686 | 12.5257136949 | 12.6943247976 |
| Margin RMSE | LightGBM | 16.2162145732 | 15.5627541488 | 15.889484361 | 15.9717033539 |
| Margin CRPS | Extra Trees | 9.25822548817 | 8.74997871668 | 9.00410210243 | 9.0043821699 |
| Total MAE | CatBoost | 12.5299652958 | 12.4652538633 | 12.4976095795 | 12.8342069215 |
| Total RMSE | CatBoost | 15.9552454117 | 15.4455355174 | 15.7003904646 | 15.9339728356 |
| Total CRPS | CatBoost | 8.98641758167 | 8.83912537408 | 8.91277147787 | 8.99276897179 |

The evidence JSON retains full-precision values. Accuracy is a proportion; other winner scores are losses. Point errors and CRPS retain their saved target units. Coarse feature groups and raw/calibrated variants are visible without publishing exact private recipes.

The report also shows the validation-selected best new XGBoost and CatBoost representative for every objective, its full-comparison rank, its 2026 reporting value and the saved all-source-absent stress score for the same candidate. These stress results do not select a replacement on 2026 or establish a universal fallback claim.

## Measured CPU and grading

| Scope | Validation | Frozen test |
| --- | ---: | ---: |
| Dispatch wall seconds | 48.162312069 | 30.366388188 |
| Admitted worker capacity | 24 | 24 |
| Distinct observed fit PIDs | 24 | 24 |
| Peak concurrent fits | 19 | 22 |
| Peak concurrent preparations | 24 | 24 |
| Optimizer CPU seconds | 264.905704494 | 162.757726509 |
| Preparation CPU seconds | 309.627054924 | 180.297342657 |

Both phases completed before the required 180-second interval, exhausted their registered queues and saved no earlier acceptance pass. The current result is **conditional insufficient independent work**, not a sustained utilization pass. V096's earlier qualifying window is not transferred to V097. A 24-PID inventory is not a claim of 24 concurrent fits, and all process-tree CPU is not optimizer CPU.

Parallel scoring completed **612 tasks** in three batches. Their wall times total **22.662062412 seconds**, with **79.263980156 worker CPU seconds**. The outer coordinator scoring interval was **22.699701164 seconds**, with **7.63539255 coordinator CPU seconds**. The prior 1,105 policies were verified and reused without new scoring tasks or forecast-partition decoding. Scoring is not counted as fitting.

The final supervisor observation records **1,487.751901189 seconds** and an estimated whole-host cost of **USD 1.0620895516821498**, measured at **2026-11-18 20:10:39.535331 UTC**. This estimate is not an invoice. The saved **USD 0.5574225929777527** science-stage estimate has an earlier scope and is not the final whole-invocation cost. Subphase costs are already inside the whole-invocation estimate.

## Source and population limits

The current source stage reused **13,378 qualified shards** with zero new conversions, normalized-row decoding or source bytes read from that cache. It retains **483/483** completed current qualification jobs. The **859/859** historical jobs were reused, while historical qualification and source-history completeness remain explicitly incomplete. This invocation made two official census calls and zero new paid-odds or market-provider requests.

The inspected current source matrix contains **2,970 rows, 18 products and 11 horizons**. The interactive source view compares T-60 and T-120 across 2024/2025/2026 without changing the completed-game denominators. At T-60, DraftKings feature-qualified winner/margin/total coverage is **782/858/856 of 919** in 2024, **799/855/855 of 934** in 2025, and **531/610/610 of 755** in 2026. Native Kalshi, Polymarket Global and Polymarket US have zero qualified feature cells in this grid. All shown predictive-baseline and strict-original-availability counts remain zero. These are source-coverage counts, not benchmark scores, original-possession proof or an executed T-60 model.

The fixture manifest retains 920 observed rows in 2024, 934 in 2025 and 888 in 2026. Its completed counts are 919, 934 and 755; 133 current fixtures remain pending. Ten current fixtures have unresolved kickoff times, and the frozen contexts retain ten pending feature gaps per target. An empty postseason response does not certify a complete official census. All 1,309 policies cover the known 755 completed games, while full official-population and V13 completion claims remain unproved.

## Next preparation

Installed and native-verified; owner execution pending.

The finite **primary T-60** plan contains **1,125 registered jobs**: 189 baseline, 306 source-ablation, 252 football-group, 252 market-component and 126 interaction jobs. It plans 750 raw/calibrated policy variants and 84 fixed blends. Planned jobs are not promised new fits: exact verified work is reused when applicable. The dated T-120 comparison remains unchanged.

Completion of that finite job set and campaign-level CPU acceptance are separate results. The prepared runner reports **T60_CAMPAIGN_RUNTIME_ACCEPTANCE** explicitly. Without an authenticated current-work interval of at least **180 seconds** and at least **75% useful CPU occupancy**, whole-campaign acceptance remains **UNVERIFIED**. Adding the durations of shorter family waves cannot establish a pass. This preparation supplies no observed T-60 runtime result and does not reclassify the dated V097 CPU evidence.

The target remains 12 scientific workers, with a hard ceiling of 24 under safe shared admission. The runner must resolve the latest verified state again at owner launch. Preparing this source starts no owner execution, fitting or provider retrieval.

## Return, history and publication

The actual control ZIP is **67,412,404 bytes**, SHA-256 `ce205076a0c894e230170343a10d1af68254ff30c7c676f9dda3b55f26f38cf8`. Separate newly uploaded payload bytes total **219,206,439**, while **37,689,243,727 inherited bytes** were not recopied. The control ZIP is not all scientific storage, and 512 MiB is a per-transport-part limit, not a campaign cap.

The actual run-summary record decreased from **131,276,993 bytes in V096** to **138,960 bytes in V097**. This is a summary-record comparison; full pinned records remain available for resumption, and it is not a claim about total scientific storage.

This report is an additive FBS-only source review. The complete previous landing content and dated V097/V093 assets remain preserved. It contains no owner execution packages, raw licensed arrays, complete candidate forecast grids, private recipes or weights, private cloud paths, or outreach material. Source publication, website deployment, owner execution and production promotion remain separate. This review is unmerged and undeployed.

## Verification

The deterministic generator and offline contract tests verify evidence consistency, temporal selection, honest short-work CPU status, source denominators, preparation boundaries and historical preservation. The browser test exercises actual desktop/mobile and source/offline rendering, selectors, keyboard controls, exact downloads, corruption rejection and page overflow. Local and hosted execution receipts remain separate; including a test in source is not a claim that it has run.
