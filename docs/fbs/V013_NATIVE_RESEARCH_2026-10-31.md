# FBS V013: completed native research, no promotion

**Verified owner milestone: October 31, 2026 (Pacific).** This dated update reports an authenticated completed execution, not a prepared package or a synthetic test. The new market-free native models were **worse than the matched DraftKings reference on all six target-season panels**. MARKET remains the production authority. This useful negative result is not a betting-edge claim.

[Aggregate JSON](v013-native-research-2026-10-31.json) · [FBS evidence landing page](README.md) · [Public/private boundary](../PUBLICATION_BOUNDARY.md) · [Credential-free invented reproducer](../../examples/fbs_contracts/README.md)

## What actually completed

The owner execution completed with exit code 0. Its recorded research-work interval was **109.5 seconds**, before later report generation, archive finalization and persistence. This is not the full terminal-command duration, a full rebuild time, or a general performance benchmark.

| Accounting item | Actual count / state |
|---|---:|
| New estimator units | 70 |
| Optimizer starts | 24 |
| Closed-form ridge solves | 46 |
| Reused estimator units counted as new | 0 |
| Inherited registered research units, kept separate | 203 |
| Production replacement | None — MARKET retained |
| Current-season labels used for fitting or selection | 0 |
| Real orders / realized ROI | 0 / not established |

The inherited 203-unit registration/lineage is not being presented as 203 new completed fits. Earlier prepared and failed releases remain recorded as such. This publication does not replace the older 18-fit/19-attempt branch subset with a misleading lifetime total.

## Matched historical comparison

Each row compares the native model and market on the **same eligible games** within that target, season and provider. Market observations require a complete same-snapshot pair at or before T−1 hour; winner probabilities use proportional inverse-decimal no-vig normalization. Lower Brier, log loss, MAE and RMSE are better. Different target coverage means the cohort sizes legitimately differ.

### Game winner

| Season | Matched games | Native Brier | Market Brier | Native log loss | Market log loss | Δ Brier: native − market |
|---|---:|---:|---:|---:|---:|---:|
| 2024 | 690 | 0.218259 | 0.178166 | 0.622713 | 0.527891 | +0.040093 |
| 2025 | 724 | 0.199745 | 0.168430 | 0.583193 | 0.503893 | +0.031316 |

### Home margin and game total

| Target | Season | Matched games | Native MAE | Market MAE | Native RMSE | Market RMSE |
|---|---|---:|---:|---:|---:|---:|
| Home margin | 2024 | 750 | 15.0660 | 11.9993 | 18.8484 | 15.3514 |
| Game total | 2024 | 749 | 13.0157 | 12.6088 | 16.4984 | 16.1505 |
| Home margin | 2025 | 774 | 13.8269 | 11.7791 | 17.5552 | 14.9195 |
| Game total | 2025 | 774 | 13.2319 | 12.4432 | 16.3787 | 15.4582 |

The machine-readable aggregate retains full-precision metrics and paired differences. These cohorts do **not** overwrite the earlier 740/748-game MARKET/innovation panels; they are separate declared comparisons. No current-season matched-market result is asserted in this milestone.

## Chronology and limitations

Candidate selection used seasons through **2023**. Models used for the current forecasting origin were trained only through **2025**. The 2024/2025 panels are permanently development-exposed; repeated historical review cannot turn them back into untouched holdouts. Historical calibration used chronological out-of-fold predictions, but selection and calibration did not have an independent calibration holdout.

These models and market panels were reconstructed after the historical games. Strict contemporaneous games in the published comparisons are **zero**. Historical no-vig probability comparison is informative, but it does not establish that a price was executable for an account, that a strategy was actually wagered, or that prospective calibration and value have been demonstrated. Margin and total point errors are not cover/over probability calibration or ROI. No live selections, individual predictions, private artifacts, weights or recipes are published here.

## Data admission and incremental compatibility

The run reused the authenticated parent analytical overlay instead of rebuilding the retired local bulk database.

| Admission/reuse item | Evidence |
|---|---:|
| Input selection-price observations | 24,320,371 |
| Admitted for reconstructed research | 7,196,533 |
| Not admitted to research | 17,123,838 |
| Strict contemporaneous observations | 0 |
| Complete paired historical quotes | 4,461 |
| Source groups reused | 372 |
| Fresh representative consumer partitions checked | 22 |
| Fresh complete original-observation pass | No — prior authenticated complete pass reused |
| Local bulk source materialization | 0 bytes |
| Retired SQLite writer restarted | No |

“Not admitted” is the complement of the admitted set, including monitoring and other ineligible observations; it is **not** a claim that all 17.1 million rows are identity failures. The 22 fresh consumer checks are representative checks, **not a new full scan**. This milestone does not claim complete season/provider census coverage or loosen identity, ordered-team, clock or qualification gates.

## What changes and what does not

The advance is a completed native-model research result with exact unit accounting and successful incremental consumer access. The scientific decision is to retain MARKET: all six comparisons reject a claim of superiority for this native model. The next milestone must test a separately registered improvement using permitted historical selection data, preserve the exposed-panel labels, and authenticate its actual return before claiming completion or promotion.

This note is the latest dated aggregate milestone. [Earlier FBS evidence](evidence.json), notebooks, synthetic demonstrations and older release pages remain immutable historical context; their earlier “current” descriptions should be read at their recorded dates.

