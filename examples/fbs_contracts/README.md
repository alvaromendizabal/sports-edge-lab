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
