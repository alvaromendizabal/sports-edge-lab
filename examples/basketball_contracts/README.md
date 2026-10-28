# Executable basketball contracts

[Project](../../README.md) · [Study](../../docs/BASKETBALL_FOUNDATION.md) · [Real aggregate evidence](../../docs/evidence/2026-10-27-basketball-b003.json) · [Notebook](../../notebooks/basketball_review.ipynb) · [Contracts](contracts.py) · [Tests](tests/test_contracts.py)

This small, standard-library example makes the basketball extension's information-time and identity rules inspectable. It covers NBA, NCAA Division I men's basketball and NCAA Division I women's basketball separately. Every input and numerical result in the walkthrough is invented. It performs zero model fits, network calls, paid requests or orders.

## Owner execution status

B001 failed before modeling and B002 completed the first 172 native estimator units. B003 then completed 60 new units, imported 156 exact compatible predecessor units and evaluated controlled opponent-adjustment representations. The cumulative unique count is 232. College proper scores improved while calibration weaknesses remained; expanded MARKET comparisons still established no qualified advantage. B003 checked 110 prior immutable forecasts, all pending, and issued 110 later versions for the same 61 games. [B004 subsequently executed and stopped at the public-request ceiling](../../docs/BASKETBALL_B004_EXECUTION.md), adding six real units without promoting a challenger; cumulative basketball units are now 238. The latest fully completed real modeling release remains B003. These facts are separate from the invented examples below.

## Run the example

From the repository root, use Python 3.11 or later:

```bash
python -m unittest discover -s examples/basketball_contracts/tests -v
python -m examples.basketball_contracts --output /tmp/basketball-contracts.json
python -m examples.basketball_contracts.evidence --check-results
```

The command writes and reopens a small JSON report. It demonstrates correctly matched Brier scoring on explicitly invented probabilities; it does not reproduce a private model or report basketball predictive performance. The test suite needs no external dependencies or credentials.

The separate [evidence module](evidence.py) validates the committed real aggregate export: fit accounting, protected-season boundaries, exact aggregate cohort identity, finite metrics and honest forecast status. It checks that the generated [league tables](../../docs/BASKETBALL_RESULTS.md) agree with that export. It loads no estimator and performs no fitting or inference. The export is an inspectable audit summary, not a substitute for private raw observations.

## Executed basketball notebook

The [notebook](../../notebooks/basketball_review.ipynb) displays the real aggregate season results, three native inline Plotly figures covering controlled contrasts, calibration and matched coverage, with an SVG fallback, and the invented contract walkthrough in a separate section. It makes zero model fits and network calls. Its executor saves, reopens and verifies a cell after the figure. A public CI job repeats separate-kernel execution.

```bash
python -m pip install -r examples/basketball_contracts/notebook-requirements.txt
python -m examples.basketball_contracts.execute_notebook --output /tmp/basketball-review.ipynb
```

No individual forecasts, team/event IDs, active feature formulas, private source paths or fitted assets appear in the notebook or aggregate export.

## What is demonstrated

| Contract | Executable behavior |
|---|---|
| Identity | League, provider, entity kind and native ID form the key; names cannot replace identities |
| Scope | NBA, NCAA men and NCAA women remain distinct namespaces and comparison cohorts |
| Calendar | Start and ending years are explicit; timezone-free times are rejected |
| Event type | Regular season, postseason, unverified and excluded games remain labeled |
| Source evidence | Publication, first observation, revision and retrieval are separate clocks |
| Research tiers | An explicit historical release assumption stays reconstructed research |
| Selection | The declared historical validation plan excludes 2026–27 outcomes from recipe selection |
| MARKET | Snapshot and quote-update times must precede the same cutoff and pass freshness |
| Matched comparison | Event IDs, target, decision cutoff and observed outcome must agree |
| Financial interpretation | Profit remains unavailable without execution and settlement evidence |

The primary walkthrough uses T−60 minutes; the same game contract also supports an explicitly requested T−24-hour cutoff. The quote example rejects a thirty-minute-old quote even when it was freshly downloaded. An after-cutoff snapshot is also rejected.

The source example intentionally lacks publication evidence. It remains unknown under a strict information-time rule. Adding a declared earlier release assumption creates a research cohort, with that label intact. A repeated download never manufactures an earlier publication or observation.

## Limits of this example

This is a public contract demonstration, not the production pipeline. It does not implement acquisition entitlements, a canonical NCAA denominator, real team aliases, possession features, calibration, model training, forecast issuance or sportsbook execution. The private owner workflow must provide evidence for those stages. An official classification is still needed before an exceptional NBA competition or uncertain NCAA opponent belongs to a primary cohort.

The score fixture deliberately assigns slightly different invented probabilities to two comparators. Their resulting numerical ordering demonstrates the scoring API only. It is not an experiment, an improvement claim or evidence of market advantage.

## Aggregate evidence checks

The default aggregate export is B003; the immutable B002 export remains available for review. Validation reconciles new fits, predecessor imports and cumulative unique units; verifies per-season cohort identity and pooled scoring; and checks the calibration bins used in the notebook. Negative tests reject reused units counted as new work, a reset cumulative budget, mismatched game cohorts, altered chart totals and current-season selection leakage. Generated Markdown tables must exactly match the committed export in CI.

