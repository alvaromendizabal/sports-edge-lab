# FBS actual V096 results and V097 continuation

[Open the self-contained report](index.html) · [Download the bounded evidence](data/status.json) · [Preserved earlier history](../v093/)

## What actually finished

The authenticated V096 invocation `20261118T174548Z-4a5cc95a05-fbs096` finished with child and supervisor exit codes **0**. The supervisor published a verified, resumable **partial** return. All **936 registered jobs** completed: 624 validation jobs were reused, and 312 frozen-test jobs added 312 base-model fits plus 312 calibrator fits. No fit failed. This is one operationally finished invocation; the broader V13 program remains incomplete.

The scoped attempt tally is six historical operational failures, one operationally finished invocation with partial science, and zero fully V13-complete runs. The report uses the final supervisor closure, preserving the earlier child snapshot as an earlier phase rather than treating its pending-publication state as the final outcome.

Prediction accounting remains separate from games and fits: 547,872 new model-callback rows; 229,488 materialized blend rows, not all novel; 1,846,464 scored campaign inventory rows, including reuse/rescoring; and 1,934,256 forecast inventory rows, including ungraded rows.

## Results and their limits

The report shows nine objective-specific validation leaders for winner accuracy/Brier/log loss, margin MAE/RMSE/CRPS, and total MAE/RMSE/CRPS. Their actual annual metrics retain full known completed-game denominators: **2024: 919/919, 2025: 934/934, 2026: 755/755**. One additional archived 2024 row remains ungraded. Every one of the 1,105 recorded policy/target combinations scores all 755 known completed 2026 games.

The declared primary validation score uses equal annual weights. The four sensitivity ratios use the same predictions; no training-row weighting, prediction changes or refitting is implied. The selector shows each ratio's saved objective winner, and the rank table preserves the primary policies' sensitivity ranks. 2026 is reporting only. The report retains previously exposed frozen-reconstruction labels; it does not claim pristine test evidence or production eligibility.

All 133 pending games remain in the denominator. Retained pending predictions cover 123/133 games for 288 market policies and 93/133 for 109 core policies. The frozen contexts retain ten pending feature gaps per target. Full official and postseason census completeness is still unproven.

The market section preserves 162 T-120 completed-game coverage cells across 18 bookmakers/products, three targets and three seasons. DraftKings, native Kalshi, Polymarket Global and Polymarket US retain distinct routes. Qualified feature/reference coverage, original availability and predictive benchmark qualification are separate. Missing native exchange histories, route rights and clock-valid observations remain visible; no benchmark score or price is invented.

## What the CPU evidence says

Actual fitting used 17 worker processes within the requested ceiling of 24, with one native thread per worker. The saved qualifying window spans **180.078 seconds** and passes at **87.0095% preparation-plus-optimizer occupancy** and **79.8297% optimizer-only occupancy**, both relative to the 17 admitted workers. Its 418 completions include calibrators. The final exhausted-queue observation is conditional and does not erase this earlier pass.

The 390.366-second fitting dispatch recorded 5,512.199 optimizer CPU seconds, 372.466 preparation CPU seconds and 578.558 other worker-callback CPU seconds. Subsequent coordinator scoring recorded **267.657 elapsed seconds / 255.872 CPU seconds**. Retained-policy grading recorded 59.306 elapsed seconds / 57.991 CPU seconds. The visualization divides process CPU by each phase's elapsed time; it does not equate that average with simultaneous process count.

The full supervised invocation lasted 2,014.501 seconds. Its compute estimate is **USD 1.438130** through the recorded final measurement, not an invoice. Subphase estimates must not be added to it. The USD 200 guard remains independent of an unlimited wall-time setting.

## Prepared next work

V097 prepares a finite 306-job XGBoost/CatBoost source-ablation tranche: 17 sources × three targets × three seasons × two families. These comprise 204 validation jobs and 102 frozen-test jobs. The latter may fit estimators and calibrators on locked pre-test labels before 2026 inference. New fits depend on exact reusable checkpoints; no fit count is promised in advance. The successor preserves the 936 completed identities and resolves the latest durable checkpoint at launch.

Parallel checkpointed scoring addresses the observed serial grading phase. The prepared worker target is 12, with a hard configured ceiling of 24. An offline serialization comparison reduced the inspected V096 summary from 131,276,993 to 137,541 bytes by removing duplicated inline ledgers while preserving full immutable stage/input pins and accountability. This is a comparison on an existing summary, not a prediction of the next total scientific return size. This source review makes no new owner-run throughput claim. The 49,593,647-byte canonical is installed and native-verified after 24 offline engineering checks, its packaged native self-test and read-only admission of all 306 jobs. The native probe projects 24 workers, leaves 937 checkpoint files unchanged, and performs no preparation dispatch, model deserialization, research, fitting or scoring. The projection is rechecked at launch and is not a measured V097 throughput result. The canonical digest and native evidence pins are included in the public JSON.

The continuation is T-120. Primary T-60 remains blocked until separate clock-valid contexts and an evaluated fitting/inference path are bound. Other horizons, a full source/family factorial, learned blend weights/distributions, historical market movement, native exchange history, official census proof, and the wider football/injury/frontier feature program remain explicit unfinished branches. Preparation launches no research, retrieves no provider data and stops no predecessor.

## Compact custody and publication

The actual verified control ZIP is **88,491,826 bytes**, with SHA-256 `5053219efea41c7adf7d1aff30e91fb15069dc049339388a4a13f1d912acf475`. Separate new scientific payloads total **1,676,955,059 bytes**. The return references **35,483,901,513 inherited bytes** without recopying them. A 512 MiB transport-part limit is not a total science cap.

This directory contains only a bounded public projection, a deterministic self-contained HTML page and this explanation. Private model identities, exact recipes/weights, native/cloud paths, licensed arrays, execution packages, support correspondence and complete candidate forecast grids remain outside GitHub. Source pins identify inspected artifacts without granting redistribution rights or access to them.

The source change is unmerged. Website publication and production model promotion are separate actions. No other sport, custom source URL, or dated v093 report is changed.

## Focused verification

```sh
python examples/fbs_contracts/v097/build_review.py --check
python tests/test_fbs_v097_public.py
node tests/fbs_v097_browser.test.cjs
```

The browser check renders desktop/mobile, source/offline views; checks every validation ratio and market coverage selector; verifies keyboard controls and exact evidence download; checks overflow and network independence; and rejects modified embedded data. It retains two screenshots and a small receipt. These are engineering checks, not owner research executions, scientific fits or CPU acceptance measurements.
