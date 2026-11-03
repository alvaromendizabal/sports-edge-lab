# Independent FBS chronology and recovery example

[Public FBS evidence](../../docs/fbs/index.html) · [Study notes](../../docs/fbs/README.md) · [Source](core.py) · [Tests](tests/test_fbs_contracts.py)

Run from the repository root with Python 3.11 or later on Linux. The example uses the standard library. It reads no credentials, accesses no network, spends no provider credits and sends no orders.

```bash
python -m examples.fbs_contracts --output /tmp/fbs-review
python -m examples.fbs_contracts --output /tmp/fbs-review
python -m unittest discover -s examples/fbs_contracts/tests -v
python -m examples.fbs_contracts.build_review --check
```

The first execution performs three genuine synthetic logistic fits. The second verifies their exact input and output identities and performs zero new fits. Synthetic fits are not owner sports-model results.

## What is demonstrated

- Each game belongs to the explicit FBS population when at least one participant is FBS; FBS–FCS opponents are retained. Unknown classifications, duplicate native IDs and unproved side changes fail validation.
- A target uses only prior game results whose availability and actual observation clocks are both before its 24-hour pregame cutoff. Same-game outcomes cannot enter that game's features. Published-but-unobserved market values are unavailable.
- The 2024 estimator uses 2023 examples; the 2025 estimator uses 2023–2024; the 2026 estimator uses 2023–2025. No 2026 outcome enters fitting or selection. Every evaluation pairs the market and model on the identical unique game cohort.
- A journal records a reservation before fitting and atomically saves the resulting model and receipt. Failures and interrupted attempts remain visible. Successful reentry checks content hashes and skips fitting. Changed inputs require a new unit identity.
- The source catalog requires every declared shared scope and all referenced raw bodies. Byte duplicates do not inflate content coverage. A captured empty response remains a captured request. Scoped absence never grants dispatch authority.

## Practical boundaries

All teams, outcomes, market probabilities and source receipts are invented. The fixed-step estimator is intentionally small; it reports its gradient and does not claim an independent optimum certificate. The example is a reproducible contract demonstration, not the production owner runner or a profitable betting strategy.

The filesystem lock uses Linux `flock`; distributed multi-host request coordination requires a separate shared-store lease and provider dispatch protocol. A valid content hash proves unchanged bytes, not provider authenticity. Original source authentication, licensing, complete account scope and current quota remain outside this credential-free example.

## Notebook

[The FBS review notebook](../../notebooks/fbs_branch_review.ipynb) separates actual aggregate evidence from the invented execution and asserts zero-fit reentry. Execute and reopen its rich outputs with:

```bash
python -m examples.fbs_contracts.execute_notebook --output /tmp/fbs-branch-review.ipynb
```


## V024: matched aggregates and explicit publication boundaries

The [current explorer](../../docs/fbs/index.html) reads the versioned [V024 aggregate](../../docs/fbs/V024_AGGREGATE_2026-11-03.json). `public_release.py` requires the complete seven-comparison/two-season grid, consistent cohort commitments, exact count-to-accuracy closure, finite metrics, fit accounting, distinct game-market/prop counts and approved fields. Unknown nested fields fail closed. These checks validate published facts; they do not authenticate unpublished records from the hashes alone.

`matched_cohort.py` is a generic, standard-library scorer demonstrated on two invented events. It requires identical event/season/target sets, matching labels and kickoff clocks, and a declared issue time before kickoff. It rejects duplicate records, invalid probability values, naive timestamps, equal-count identity substitutions and label drift. Declared timestamps are not independent proof of actual possession. The public contract does not reconstruct private live feature values.

```bash
python -m examples.fbs_contracts.public_release
python -m examples.fbs_contracts.matched_cohort
python -m unittest examples.fbs_contracts.tests.test_matched_cohort examples.fbs_contracts.tests.test_v024_release -v
```

Hand-calculated tests cover log loss, Brier score, accuracy, point error and bias. Unequal-size pooling uses count-weighted sufficient statistics; RMSE is reconstructed from squared error, while ECE and MCC reject aggregation from scalar averages. No per-game private forecast enters the public fixture or its output.

### Real browser verification

The FBS workflow installs pinned Playwright 1.56.1 and its matching Chromium. The test renders desktop and mobile layouts, checks every season/target/metric/reference state, verifies numeric values against the public JSON, exercises keyboard and failure scenarios, validates an aggregate CSV download, checks the no-JavaScript fallback, and rejects external network requests. Screenshots are retained as CI artifacts.

```bash
PLAYWRIGHT_MODULE_DIR=/path/to/playwright \
FBS_SCREENSHOTS=/tmp/fbs-screenshots \
node examples/fbs_contracts/tests/test_dashboard_browser.cjs
```

See the [model card](../../tracks/ncaaf/MODEL_CARD.md) for the three reproducibility tiers: public aggregate validation, invented engineering execution, and independently verified private research.


## Certified checkpoint recovery on invented problems

Run `python -m examples.fbs_contracts.certified_resume`. It reuses the shared exact rational convex certificate, rejects a false solver success, preserves two committed states, solves only the remaining invented unit and reenters with zero new solves. [Implementation](certified_resume.py) · [Tests](tests/test_certified_resume.py) · [Interactive explanation](../../docs/fbs/recovery.html). These fixtures do not expose or reproduce the private football objective.
