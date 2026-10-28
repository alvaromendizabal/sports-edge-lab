# B004 execution: useful negative results, resource stop

[Project](../README.md) · [B003 historical results](BASKETBALL_RESULTS.md) · [B004 aggregate](evidence/2026-10-28-basketball-b004.json)

B004 actually executed on October 28, 2026, Pacific time. All six reconstructed historical league/horizon scopes completed before optional exchange capture exhausted the public-request allowance. The owner return is **STOPPED**, not accepted. B003 remains the latest fully completed real modeling release.

Six shared score-correction units completed, bringing cumulative basketball real units from 232 to 238. The 216 predecessor aliases and 222 checkpoint files are reuse/accounting evidence; they are not 222 new fits. The run tally is two accepted, one failed and one stopped basketball execution.

No challenger earned promotion. NBA retains strength logistic; both college leagues retain rich combined logistic at T−60. The separate B003 point heads and T−24h recipes remain unchanged. Historical 2025/2026 seasons are development-exposed, and all statistical history uses the labeled reconstructed 24-hour assumption.

## Probability challengers

Lower log loss is better. Each challenger uses the exact incumbent cohort in each season. Both-season log-loss improvement, no Brier regression, calibration stability and the paired uncertainty gate remain required.

| League | Challenger | 2025 log loss | 2026 log loss | Pooled Δ vs incumbent | Descriptive 95% interval | Promoted |
|---|---|---:|---:|---:|---|---|
| NBA | Fixed probability blend | 0.613098 | 0.601878 | +0.000018 | [-0.000930, +0.001000] | No |
| NBA | Probability from margin | 0.613575 | 0.601047 | -0.000160 | [-0.001876, +0.001918] | No |
| NCAA men | Fixed probability blend | 0.526535 | 0.529941 | +0.002822 | [+0.001166, +0.004524] | No |
| NCAA men | Probability from margin | 0.525005 | 0.526192 | +0.000183 | [-0.000737, +0.001254] | No |
| NCAA women | Fixed probability blend | 0.458637 | 0.462357 | +0.003412 | [+0.002102, +0.004941] | No |
| NCAA women | Probability from margin | 0.455693 | 0.458786 | +0.000145 | [-0.000755, +0.001216] | No |

NBA probability-from-margin improves pooled log loss by only 0.000160, but worsens both log loss and Brier in 2025. The fixed blend worsens both college seasons. The men’s margin probability worsens 2025; the women’s version worsens 2025 Brier and 2026 log loss. Weights and thresholds were not retuned against these exposed results.

## Corrected point distributions

The combined margin/total squared-error improvement does not override a component regression. All three leagues fail the margin-RMSE requirement in 2025; women also fail it in 2026.

| League | 2025 margin RMSE, incumbent → correction | 2026 margin RMSE, incumbent → correction | Pooled Δ combined MSE | Descriptive 95% interval |
|---|---:|---:|---:|---|
| NBA | 14.362295 → 14.371788 | 14.619459 → 14.588584 | -2.157834 | [-12.535231, +8.406464] |
| NCAA men | 11.523712 → 11.529185 | 11.626915 → 11.624316 | -3.276340 | [-5.499998, -1.474748] |
| NCAA women | 12.283609 → 12.283819 | 12.323438 → 12.338619 | -0.510261 | [-1.221148, +0.156254] |

Men’s combined error interval excludes zero, yet its 2025 margin regression still prevents promotion. These are descriptive intervals from 300 paired seven-calendar-day block resamples, not untouched confirmation.

## Uncertainty remains reportable after rejection

Pooled diagnostics below describe the rejected corrected distributions, not approved uncertainty for issued forecasts. The aggregate also includes separate 2025/2026 results and home/away-point diagnostics. CRPS means were reaggregated from saved per-game values; the native residual arrays were not deserialized during the audit.

| League | Target | 80% coverage / width / interval score | 95% coverage / width / interval score | Mean saved CRPS |
|---|---|---:|---:|---:|
| NBA | margin | 79.62% / 35.819 / 51.620 | 95.71% / 58.879 / 70.509 | 8.097017 |
| NBA | total | 80.22% / 48.681 / 66.715 | 94.67% / 73.366 / 90.163 | 10.807282 |
| NCAA men | margin | 79.51% / 28.531 / 40.919 | 94.63% / 44.889 / 56.868 | 6.476734 |
| NCAA men | total | 79.03% / 41.599 / 59.992 | 94.71% / 65.655 / 82.634 | 9.507986 |
| NCAA women | margin | 79.15% / 30.807 / 43.521 | 94.77% / 48.312 / 59.134 | 6.912226 |
| NCAA women | total | 80.19% / 40.691 / 56.542 | 94.86% / 62.450 / 77.010 | 9.000970 |

## Forecasts, MARKET and execution limits

B004 issued 110 additional immutable early-outlook versions. B002/B003/B004 now preserve 330 versions in 18 files across 61 distinct games. They are not 330 independent games or named-horizon lock forecasts. The B004 prospective monitor checked the prior 220 versions: all pending, zero settled. Its 110 new versions were not yet scored by that monitor.

No qualified at-issue sportsbook comparison or game-level predictive uncertainty was admitted for the new issues. Fresh inputs contained 56 completed NBA games, but no new 56-game retrospective scorecard was produced. The earlier B003 52-game retrospective panel remains separate from genuine prospective evidence.

Sportsbook, Kalshi, Polymarket US and international Polymarket remain separate. No independent MARKET advantage, historical exchange trading backtest, order, fill, profit or basketball bankroll is established. Learned MARKET-only and integrated models retain the earlier-support minimums; no threshold was lowered.

The maximum verified cumulative active floor is 4,223.356267478 seconds against 4,500, leaving 276.643732522 seconds before any later matching live charge. All 48 public requests are consumed. The separate 180-second finalization reserve cannot fund research. The next bounded recovery may consolidate evidence without new fitting or public requests; fresh acquisition requires an explicitly approved allowance.

## Reproduce the public evidence checks

```bash
python -m examples.basketball_contracts.evidence_b004 --check
python -m unittest discover -s examples/basketball_contracts/tests -v
```

The private-return audit verified 11,670 manifest pins and CRC, native checkpoint hashes, the embedded source, saved notebooks and report links. Independent numerical checks compared 11,732 values across 684 scorecards, 496 interval rows and 248 CRPS aggregation rows; maximum absolute discrepancy was below 4.3×10⁻¹⁴. No private model fitting, inference or deserialization occurred during that audit. The public command validates aggregate arithmetic and regenerates this note; it does not claim to reproduce private training.

The public update contains sanitized aggregates and generic evidence checks. Raw source records, individual forecasts, active training code, fitted weights and cloud identifiers remain excluded. Portfolio assessment remains 8.5/10: stronger auditability does not establish independent predictive or trading performance.
