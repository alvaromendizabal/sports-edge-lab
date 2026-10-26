# Model card — current research bank

Publication date: October 25, 2026. [Project](../README.md) · [All evidence](CURRENT_EVIDENCE.md) · [Historical model card](MODEL_CARD.md)

## Intended use

NFL and FBS probabilistic forecasting research, controlled model comparison and prospective evaluation. The public materials support engineering review. No verified profitable wagering system, automatic promotion or externally established state-of-the-art ranking is claimed.

## Targets and model families

| Family | Role | Public disclosure |
|---|---|---|
| Regularized linear models | Historical standalone baselines and teacher/reference models | Earlier dated implementations are retained |
| Learned MARKET models | Learn from bookmaker quotes and their structure | Distinct from football-feature models |
| LightGBM and XGBoost | Native nonlinear football-plus-MARKET systems | Current aggregate scores and method class |
| PyTorch and TensorFlow | Group/context representations and joint neural systems | Current aggregate scores and method class |
| Fixed ensembles | Combine declared model systems | Aggregate outcomes; no post-hoc serving-weight change |

The primary winner target is home win conditional on a non-tied result. Point margin and total models are distinct outputs. Point predictions are not calibrated cover/over probabilities or a complete joint score distribution. Contract-specific decisions require the model target and the contract's tie, void and settlement rules to agree.

## Evaluation

The public export includes 2024–25 and 2025–26 fixed-origin cohorts, a separate 2025–26 annual-origin comparison, and 2026–27 monitoring. Exact games and labels match within each row. Different update policies and target cohorts must not be pooled as interchangeable estimates.

Log loss is primary; Brier is a secondary proper score. Accuracy and AUC are reported as different properties. The strongest retained reference can differ by metric. Historical panels have been repeatedly examined, and retained leaders are selected descriptive references. Current monitoring is not an untouched confirmation set.

The current NFL monitor has 77 games across six weekly blocks, below the study's minimum for a weekly-block interval. FBS has 301 games across eight blocks. The new FBS challenger's log-loss difference against MARKET has a 95% interval crossing zero. Both latest historical challenger gates failed. Positive subthreshold effects remain recorded.

## Current outcome

The retained current NFL and FBS references have lower monitoring log loss than raw MARKET. The latest joint challenger improves all four corresponding NFL framework controls in current monitoring but does not surpass the strongest retained reference. FBS effects are smaller and less consistent. V118 serves saved models and adds no real fits, so its operational success is not a new model-quality gain.

## Data and failure modes

Potential limitations include sparse independent game outcomes, correlated inputs, incomplete pregame availability clocks, source revisions, missing enrichment, stale pricing, regime changes, small current-season blocks and repeated model selection. A large play count is not a large number of independent game labels. Synthetic test success does not establish real-data predictive validity.

Current source inventory and unresolved identity/time conflicts are in [the evidence report](CURRENT_EVIDENCE.md#data-and-operational-readiness). Every feature family must state whether it is collected, admitted, implemented, evaluated and serving-ready; these are different states.

## Publication and deployment status

The current exact feature recipes, fitted assets, individual forecasts and live decision configuration are private. The [public example](../examples/review_lab/README.md) is a deliberately separate synthetic system. V118 emitted research probabilities but admitted zero paper actions or real wagers. Fresh inputs, contract-target alignment and independent prospective evidence remain necessary for economic validation.
