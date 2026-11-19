# FBS V099 — completed additive research

[Interactive evidence report](index.html) · [Exact public evidence JSON](data/status.json) · [Preserved preparation snapshot](../README.md)

V099 completed its finite distribution and uncertainty study on November 18, 2026 at 6:33 p.m. Pacific. The supervisor observed exit 0, verified the compact return and dependency closure, and finished durable publication. This is an actual completed owner execution. The broader V13 scientific program remains partial and resumable.

## What completed

The campaign preserved all 1,125 authenticated V098 fitting jobs and evaluated 100 new forecast distribution policies. It completed 200 validation tasks, 100 separately locked test tasks and 300 paired uncertainty tasks, with zero scoring failures. It made no new estimator, calibrator or optimizer fits. The total T60 research population now includes 934 policies: 834 preserved policies and 100 additions.

Selection uses annual 2024 and 2025 validation metrics at 50/50 by default, with four sensitivity profiles. The 2026 test remains outside selection. Every displayed leader covers the same 919, 934 and 755 completed observed games. The official full census and postseason completeness are not certified. These results remain previously exposed reconstructions; neither this report nor the GitHub publication promotes a production model.

## Validation-selected scientific results

One of nine primary objective leaders changes: a probability ensemble now leads winner accuracy. Its 50/50 validation accuracy is **75.2151%**, compared with **75.1703%** for the prior leader, a descriptive gain of **0.0448 percentage points**. The other eight primary leaders are retained. Across all five validation-weight profiles, six of 45 selections change: accuracy under each profile and margin CRPS under 40/60.

The table reports each primary leader's own annual metrics on the same full observed completed-game cohorts. Accuracy is higher-is-better; all other displayed losses are lower-is-better. The final column is the equal-weight mean of the two annual validation metrics, not a pooled-game score. The 2026 column does not affect selection. Display rounding does not change the exact JSON evidence or ranking.

| Objective | Public alias | Coarse family | 2024 validation, n=919 | 2025 validation, n=934 | 2026 exposed test, n=755 | Primary 50/50 score |
|---|---|---|---:|---:|---:|---:|
| Winner accuracy | T60 research 14 | Probability ensemble | 73.4494% | 76.9807% | 74.4371% | 75.2151% |
| Winner brier | T60 research 12 | CatBoost | 0.175444 | 0.166885 | 0.167910 | 0.171164 |
| Winner log loss | T60 research 04 | LightGBM | 0.525080 | 0.495952 | 0.486584 | 0.510516 |
| Margin MAE | T60 research 05 | CatBoost | 12.598548 | 12.960609 | 12.877682 | 12.779579 |
| Margin RMSE | T60 research 13 | Fixed ensemble | 16.883919 | 15.840149 | 16.247981 | 16.362034 |
| Margin CRPS | T60 research 01 | LightGBM | 9.567506 | 8.946641 | 9.159990 | 9.257073 |
| Total MAE | T60 research 09 | PyTorch | 12.560400 | 12.432704 | 12.831181 | 12.496552 |
| Total RMSE | T60 research 09 | PyTorch | 15.961302 | 15.461898 | 15.972036 | 15.711600 |
| Total CRPS | T60 research 06 | CatBoost | 8.938501 | 8.867994 | 9.015806 | 8.903247 |

**Uncertainty does not establish an improvement.** Across 900 paired objective comparisons with 4,096 bootstrap replicates each, none favors a new candidate at Holm-adjusted p < 0.05; 373 comparisons show worse performance at that threshold. All three annual accuracy intervals for the new primary accuracy leader cross zero, with adjusted p-values of 1.0. These exploratory comparisons are conditional on the existing validation-selected reference and do not establish prospective performance.

## Remaining scientific work

The independent complete-season census and postseason classification are uncertified. Ten upcoming games still have unresolved kickoff clocks or incomplete component forecasts. Native Kalshi and Polymarket input adapters, historical market continuity, and broader injury, play, drive, weather and feature-producer work remain unfinished. The inherited source grid contains **62,956 qualified cells, 348,794 missing cells and 621 cells outside feature history**, across 17 admitted bookmaker slots. Source cells are not unique games. DraftKings coverage and the three blocked exchange products remain separately disclosed in the evidence report.

## What the runtime evidence means

The invocation admitted 36 workers. Actual mean scientific CPU differs by phase and is shown directly in the report; worker counts are not substituted for used cores. Each scoring queue finished in under eight seconds, so the 180-second / 75% occupancy gate was not applicable and was not marked passed.

Checkpoint custody took 211.29 seconds, compared with 1,930.13 seconds in V098, while handling 6,085 rather than 5,485 receipts. This is an observed cross-run comparison, not a controlled scaling benchmark. The existing parallel verifier was preserved. New payload uploads were 65,668,678 bytes, and the verified control ZIP was 72,561,442 bytes. Inherited logical payload references are not a measurement of physical cloud occupancy.

The final authenticated supervisor manifest completed or reused all 16 numbered stages. Earlier immutable snapshots retain their earlier packaging/publication state. A separate duplicate launch was refused while the successful invocation was active; it did not overwrite the verified return and is not counted as a failed research execution.

## Reproduce the bounded public report

```sh
python examples/fbs_contracts/v099/completed/build_review.py --check
python tests/test_fbs_v099_completed_public.py
node tests/fbs_v099_completed_browser.test.cjs
```

The deterministic generator rejects private projection fields, incomplete contender denominators, test-based selection and unsupported scientific/CPU claims. Browser checks exercise all objective/profile filters, source filters, keyboard controls, exact JSON download, served and offline rendering, mobile overflow, external-request boundaries and integrity-error handling. Hosted CI and local validation remain distinct evidence.

The page uses public aggregate metrics and opaque policy aliases. It contains no private owner packages, cloud/account paths, credentials, model bodies, exact feature recipes, candidate forecast grids or raw licensed feeds. No research is executed and no source prices are refreshed by publishing these files. GitHub source publication and hosted website deployment remain separate actions.
