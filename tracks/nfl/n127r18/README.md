# NFL N127R18 — verified partial return

[Interactive evidence review](index.html) · [Execution and coverage aggregates](status.json) · [Selected annual metrics](selected_metrics.json) · [NFL track](../README.md)

**The latest inspected owner return is sealed and `PARTIAL_RESUMABLE`.** This update reports the actual R18 execution, which began on November 18, 2026 at 4:02:37 PM Pacific. It supersedes the earlier preparation-only status. The current scientific pointer and matching native post-seal receipt identify the same verified logical return; this publication read those records and did not independently rehash the entire archive.

## What completed

The owner ledger records **17 completed, 5 reused, 4 partial and 2 deferred stages**. Forecast preservation, validation selection, dashboard generation, current market comparisons and Circa policy processing completed as stages. Stage completion does not establish complete scientific acceptance or newly qualified forecasts. The complete stage ledger is represented in the interactive review.

R18 reused **31,806 verified fold groups** and made **zero new scientific estimator calls**. The requested worker ceiling was **36**; there is no measured sustained scientific occupancy claim for this reuse execution. The preceding R17 fitting evidence reported 24 overlapping fit processes and a peak of approximately 22.44 logical core equivalents. Its later I/O admission refusal is recorded separately and is not evidence of forecast corruption or proof that another workload alone caused the pressure.

The pre-seal owner summary reports 14,361.71 seconds elapsed and an estimated **USD 10.25** in running compute. This estimate excludes later sealing and is not an AWS invoice. No production promotion occurred.

## Selection and denominators

The selected-metric export preserves **641 saved nomination rows**, including **132 primary 50/50 rows** and the four sensitivity ratios 40/60, 30/70, 20/80 and 10/90. Public role aliases replace private recipe identifiers. Exact annual metrics, eligible denominators, cohort hashes, co-leader counts and missing-test states remain available in the JSON and browser review.

The registered census contains 285 games in each validation season, 2024 and 2025, and 150 completed 2026 games. Each target's eligible denominator may differ, for example for tied winner outcomes; compare its saved denominator and cohort hash rather than assuming every metric has the full census. **90 of the 132 primary nomination rows still have a missing full-cohort test regrade.** Missing values remain null, and all tied validation nominees remain visible. The page does not choose among them using 2026 results.

Validation ratios select among saved annual metrics. The execution summary reports no use of these weights in training and zero test labels used for selection. Previously inspected 2026 outcomes remain development-exposed. Source and fitted-layer ancestry acceptance remain incomplete, so the displayed selections are **validation nominations from a partial campaign**, not fully accepted production champions.

The public update does not issue a new current forecast or Circa card. Earlier published issues retain their original dates, clocks and qualifications. Current official line verification and original issue evidence are still required before claiming a newly qualified five-game card.

## Source admission

| Proposed historical group | Current result | Admissible rows |
|---|---|---:|
| Drive | Requires owner evidence: content-bound rights and authenticated feature matrix missing | 0 |
| Injury and replacement | Requires owner evidence: content-bound rights and authenticated feature matrix missing | 0 |
| Market response | Requires owner evidence: content-bound rights and authenticated feature matrix missing | 0 |

The coverage table retains all 42 source/year/horizon cells across 2020–2026 and T120/T60, distinguishing retained objects and rows from admitted team rows and both-team game coverage. These results concern the three proposed historical frontier groups, not every NFL input or every market source. Current snapshots do not establish historical predecision availability. No rights, timestamps, source rows or missing predictions are manufactured.

## Engineering qualification and local storage

The earlier preparation passed **946 native engineering tests, with zero failures, errors or skips**. That historical qualification is separate from this owner execution and from this publication's own tests.

Two typed local Parquet copies passed equivalence checks. Bounded full-column reader measurements show both the benefit and the cost:

| Dataset | Shape | CSV median | Parquet median | CSV reader RSS | Parquet reader RSS |
|---|---:|---:|---:|---:|---:|
| Historical schedule | 7,548 × 46 | 36.47 ms | 11.94 ms | 21.60 MiB | 91.74 MiB |
| Evaluation calendar | 842 × 11 | 1.58 ms | 2.87 ms | 21.48 MiB | 86.87 MiB |

The schedule read was approximately 3.05 times faster; the small calendar read was slower. Reader RSS includes runtime overhead. These measurements do not prove a whole-campaign speedup or completion of the entire legacy migration. Model data remains local to the owner's execution environment.

## Failure and work accounting

The reconciled ledger, including the observed R18 execution, contains 32 attributable builds across 18 named revisions, 13 recorded owner entries, 11 verified partial returns, two identified owner recovery/completion failures and one separate pre-owner launch failure. That is 14 scoped attempts, not 32 failed owner runs. The recorded scientific estimator-call total remains 81,552; R18 adds no new fit credit. **Zero fully complete V13 returns are established.**

## Public scope and verification

The public files contain saved aggregates, opaque evidence hashes and generic rendering code. Private receipts, exact feature recipes, model bodies, source payloads, execution archives and private storage addresses remain outside this repository. Evidence hashes identify private authenticated records and are not public download links. See the [publication boundary](../../../docs/PUBLICATION_BOUNDARY.md).

The page embeds the two JSON files and works without network requests. Rebuild and verify it from the repository root:

```bash
python tracks/nfl/n127r18/build_review.py
python tracks/nfl/n127r18/build_review.py --check
python -m unittest discover -s tracks/nfl/n127r18 -p 'test_*.py' -v
node tracks/nfl/n127r18/browser_review.cjs
```

The browser check uses the same Playwright setup as the NFL evidence-review workflow. It exercises the public page separately from the owner's private dashboard, whose native browser-interaction check was unavailable. A GitHub source merge does not deploy the separately hosted website or refresh providers, research or forecasts.
