# NCAA evidence review

[Project](../../README.md) · [Men's track](../../tracks/ncaam/README.md) · [Women's track](../../tracks/ncaaw/README.md) · [Publication boundary](../../docs/PUBLICATION_BOUNDARY.md)

This example makes the **evaluation contract** executable without credentials, data subscriptions or a machine-learning environment. It also generates the college basketball review pages from committed, sanitized aggregate evidence. The invented demonstration and the real historical aggregates remain separate: the example does not reproduce the private models or claim a betting record.

## Run the example

Python 3.11 or newer; standard library only:

```sh
python examples/ncaa_review/contracts.py --demo
python -m unittest discover -s examples/ncaa_review -p 'test_*.py' -v
python examples/ncaa_review/build_dashboard.py --check
```

The demo creates deterministic invented history, fits a three-intercept baseline at a chronological origin, and scores completed invented events separately by league, target and provider. Its result includes missing comparisons and both winning and losing directional disagreements. A pure payoff function demonstrates how explicit executable prices and fees affect an invented one-unit decision. It has no placement API and emits **zero orders**. Fixture fee values are not estimates of any provider's real fees.

The browser check exercises generated pages in real Chromium at desktop and mobile widths, every objective/window selector, all clock scenarios and keyboard navigation. It rejects JavaScript errors, unexpected external requests and page overflow. CI uses its separately pinned Playwright installation:

```sh
PLAYWRIGHT_MODULE_DIR=/path/to/playwright \
  node examples/ncaa_review/test_dashboard_browser.cjs
```

## What the real historical evidence says

The latest accepted historical population covers 2024–25 and 2025–26: **11,507 men's games** and **10,901 women's games**. These are represented games in an exact shared prediction cohort, not a claim of all official games. The models were selected after those seasons had been evaluated. The resulting scores are **development-exposed retrospective evidence**, not an untouched final test or prospectively issued performance.

| Objective | Men's pooled selection | Women's pooled selection |
|---|---:|---:|
| Minimum natural log loss | 0.523274 | 0.454618 |
| Minimum Brier score | 0.177371 | 0.151127 |
| Maximum winner accuracy | 72.35% | 77.01% |
| Minimum margin MAE, points | 9.075180 | 9.686569 |
| Minimum margin RMSE, points | 11.551616 | 12.273463 |
| Minimum total MAE, points | 13.336419 | 12.643371 |
| Minimum total RMSE, points | 16.941556 | 16.011293 |

Each row may select a different model. The women's log-loss and Brier selections are almost numerically identical but remain distinct. Public IDs identify the reported selections without disclosing exact private recipes. When the page switches seasons it keeps the same pooled-selected model; it does not select a different seasonal winner. The sanitized source tables are [men's evidence](../../tracks/ncaam/evidence.json) and [women's evidence](../../tracks/ncaaw/evidence.json).

Historical feature availability uses a declared 24-hour release assumption, which is weaker than independently proven historical publication. The one-hour evaluation horizon does not erase that limitation. Newly obtained information must never be moved backward to an earlier prediction cutoff.

### Probability and point error use different measurements

Winner comparisons use natural-log loss with the same clipping constant (`1e-15`), Brier score on the unmodified probability, and accuracy awarding half credit at probability `0.5`. Ties make no directional pick. Calibration bias is mean predicted probability minus observed frequency. The ten-bin reliability plot exposes bin support; ECE is the support-weighted absolute bin error, and ROC AUC uses average ranks for ties. ECE can hide differences within bins, while AUC does not measure probability calibration.

Margin means home points minus away points. Totals include both teams and overtime. MAE measures average absolute error; RMSE penalizes large misses more strongly; signed bias is predicted minus actual points. A margin-direction tie receives half credit. Total-point forecasts alone cannot establish over/under accuracy: the line, push rule and decision are required. A point forecast does not provide a calibrated spread-cover probability.

### The uncertainty is descriptive

The probability and accuracy selections are compared on exactly matching events, ordered teams, prediction clocks and outcomes. The report resamples whole local-calendar weeks **within each season**, with replacement, 2,000 times using a fixed seed. It sums game losses in each resample and divides by that resample's game count. It does not give each week equal weight regardless of its number of games.

| Probability selection minus accuracy selection | Men | Women |
|---|---:|---:|
| Log-loss difference | −0.005184 | −0.002887 |
| Descriptive 95% interval | [−0.006486, −0.003840] | [−0.005578, −0.000172] |
| Accuracy difference, percentage points | −0.0695 | −0.3257 |
| Descriptive 95% interval, percentage points | [−0.4308, +0.2912] | [−0.7948, +0.0640] |

The probability selections have lower historical proper-score losses. Both accuracy-difference intervals cross zero. These are selection-exposed intervals with no adjustment for the model search; they do not establish future superiority. Resampling weeks also does not eliminate dependence that persists across weeks or seasons. The private per-game inputs are not published, so the public aggregate tables allow inspection of these conclusions, not an independent reconstruction of the bootstrap.

## Current-season status and provider scope

The November 3 B032 owner attempt stopped at parent-data restoration. It performed **zero new real target fits, calibration fits, source refreshes, predictions or prospective issues**. The 250 passing invented-fixture tests are software evidence, not model training. A subsequent independent full-byte return readback established durability; it did not change the failed execution into a successful scientific run. The accepted historical work and original frozen-monitoring record remain preserved.

The active comparison scope is **Kalshi, Polymarket and DraftKings**. Missing current-season paired coverage, log loss and ROI remain `null`/unavailable. Neither a high winner accuracy nor a low historical log loss demonstrates an executable economic edge. The public example compares model and reference on the exact same provider-specific population, preserving target, horizon, ordered teams, settlement, quote availability and outcome-release clocks. It deliberately refuses to merge evaluation tracks or substitute one provider's population for another's.

Frozen-original evaluation, rolling reconstruction, and genuinely issued prospective forecasts remain separate. A reconstruction can use an auditable historical information set; it cannot claim an earlier issuance time. A real prospective issue must be created with the model and features already available, within the declared one-to-two-hour horizon. Retraining on more released data can help or harm; it must earn its result in a separately reported chronological evaluation.

## A concrete boundary failure and its regression test

The failed owner code entered a streaming-body context manager and then called a wrapper-specific iterator on the returned object. That context manager returned the raw HTTP reader. The earlier test double inherited a stream whose context manager returned itself, so it did not represent the production interface boundary.

`verified_read` demonstrates a portable correction: retain the actual wrapper, call its ordinary bounded `read`, verify the complete byte count and SHA-256, and close that wrapper in `finally`. A regression double deliberately returns a *different* object from `__enter__`; the test proves that readback no longer depends on the context return value. Separate negative tests reject truncated, oversized and corrupt content and verify closure after failure. This public test exercises the failure class; it is not evidence that the replacement owner workload has already run successfully.

## Review map

| File | What can be inspected |
|---|---|
| [contracts.py](contracts.py) | Information clocks, exact identity pairing, separate metrics, invented baseline, explicit-fee payoff and stream verification |
| [test_contracts.py](test_contracts.py) | Future-outcome poisoning, equal-boundary exclusion, reordered identities, missing coverage, mixed-track rejection, stream-interface failures |
| [test_evidence.py](test_evidence.py) | Cohort closure, metric aggregation, calibration support, fixed selections, missing-value preservation and deterministic page generation |
| [build_dashboard.py](build_dashboard.py) | Deterministic, dependency-free rendering from aggregate JSON |
| [test_dashboard_browser.cjs](test_dashboard_browser.cjs) | Real desktop/mobile browser events, accessibility hooks, keyboard controls and offline rendering |

The accepted historical and failed current owner-return digests are included in the public evidence JSON. Raw provider records, private object locations, complete prediction archives, execution handoffs, exact active features and model parameters remain outside this publication. Nothing here changes the repository's existing rights or publication policy.
