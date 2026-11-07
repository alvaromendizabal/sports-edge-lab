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

The [preserved V024 explorer](../../docs/fbs/research.html) reads the versioned [V024 aggregate](../../docs/fbs/V024_AGGREGATE_2026-11-03.json). `public_release.py` requires the complete seven-comparison/two-season grid, consistent cohort commitments, exact count-to-accuracy closure, finite metrics, fit accounting, distinct game-market/prop counts and approved fields. Unknown nested fields fail closed. These checks validate published facts; they do not authenticate unpublished records from the hashes alone.

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

## All-game season explorer and independent market clocks

[Current dashboard](../../docs/fbs/index.html) retains the full observed inventory with left-joined provider evidence. [The clock selector](market_time.py) separates a source observation at a historical cutoff from proof of actual historical possession. It rejects late prices/captures, incompatible products, ambiguous equal-time values and candles that extend beyond a cutoff. An authenticated snapshot captured before a boundary proves availability at capture even when an individual quote clock is absent; this does not prove the latest tick or admit a model feature. Future cutoff windows remain pending. [Adversarial tests](tests/test_market_time.py) preserve valid zeros and all unmatched games.

The sanitized report contains public game facts and explicitly authorized rounded analytical outputs. It has no raw feeds, private recipes, source credentials or model bodies. [Publication scope](../../docs/PUBLICATION_BOUNDARY.md#fbs-all-game-analytical-report-november-3-extension). Public values do not establish full private retraining reproducibility.

```bash
python -m examples.fbs_contracts.build_season_review --check
node examples/fbs_contracts/tests/test_season_logic.cjs
python -m unittest discover -s examples/fbs_contracts/tests -v
```

The separate CI browser test exercises all 888-game inventory views, current/last-week windows, provider switches, exact historical disagreement count, keyboard dialog, CSV analysis download, responsive layouts and an all-888-row no-script fallback. It rejects external requests and browser errors. These checks perform zero owner model fits.

The [static projector](export_site.py) reads an exact Git commit, exports only the public asset allowlist, rewrites repository navigation to that commit and checks that every relative asset is present. Its manifest binds the hosted bytes to the source and evidence clocks. CI runs this projection without publishing or refreshing data; deployment is a separate operation.

The current native point view derives no single final-score estimate from a 50% midpoint. Supported lower and upper threshold bounds retain separate availability clocks; tests reject later support at an earlier cutoff, keep one-sided bounds and flag contradictory intervals. The actual wide-book counterexample remains in expanded diagnostics. Historical price-only proxy cohorts are unchanged.

The final historical-reference refresh verifies 72 named/pooled cohort identities. Earlier-query actual quotes remain valid at later windows, while historical native point proxies retain their exact registered window. Explicit equivalent sportsbook labels resolve only on equal value/time ties; conflicting values and incompatible settlements remain rejected. The all-data explorer preserves 533 latest DraftKings winner records, including eight legacy-only records outside the newly acquired 525-game panel.

The expanded public report uses a lossless reference-column transport: column names occur once, and every original value and clock is reconstructed before validation and rendering. `season_transport.unpack` restores ordinary reference objects; the browser has the equivalent decoder. This keeps the complete report within delivery limits without deleting games, references, failures or outcomes. The standalone HTML still makes zero external data requests and retains all 888 no-script rows.

## November 4 source refresh and incremental visibility

The source-only inventory now retains all 2,742 observed 2024–2026 games, including 624 completed 2026 results. The original 622-game replay, prior references, weekly scorecards and historical matched metrics are unchanged; the two additional completed results have no invented model forecast. `source_progress.py` validates the separate inventory and the dated execution-log stage counters. Every source row remains in the no-JavaScript fallback. A processed source pass can contain failed requests and is not a completed owner result or complete market coverage.

The latest source refresh adds 180 independently reconstructed DraftKings references and 660 native references. Native point products have no invented scalar score: verified probability-band bounds are displayed separately. Their November 4 capture clocks are not a claim of continuously refreshed prices or finalized future cutoffs. The public export contains only sanitized analytical observations, not raw provider payloads.

`availability_reference_at` and the separate latest-supported-pregame display choose the latest eligible observation across source-timestamped history and capture-only snapshots. Historical records retrieved later remain valid descriptive source evidence, not proof of earlier model possession. The original `reference_at` selector and its benchmark panels are preserved. Same-clock value or bound conflicts, reversed/crossing intervals, later-than-assessment captures and TBD kickoff qualification are tested explicitly.

```bash
node examples/fbs_contracts/tests/test_latest_available_logic.cjs
node --test examples/fbs_contracts/tests/test_source_progress.cjs
python -m unittest examples.fbs_contracts.tests.test_market_availability examples.fbs_contracts.tests.test_source_progress -v
```

No source display change performs a model fit, bypasses the unresolved raw-to-feature reconstruction gate, creates an issued forecast, or authorizes a trade.

## Interrupted work without fabricated success

The [November 4 operations note](../../docs/fbs/operations-2026-11-04.md) preserves V029's actual failed handoff and distinguishes V030's locally tested preparation from an owner result. The new [interrupted-work example](interrupted_work.py) uses only invented bytes and standard-library code. It distinguishes a live process from a reused PID, preserves diagnostic failures, rejects incomplete inventories and conflicting observations, authenticates exact dependencies and replays each accepted derived value. Recovery does not require pretending that the whole prior run succeeded.

```bash
python -m examples.fbs_contracts.interrupted_work
python -m unittest examples.fbs_contracts.tests.test_interrupted_work -v
```

These are engineering fixtures, not real market observations, successful remote recovery or new football-model fits. Hashes identify unchanged bytes; source authenticity, writer ownership and distribution rights remain separate requirements.

## Later November 4 evidence: current-only captures and visible gaps

The later authenticated collection attempt acquired data and then failed during reporting. Its dated [operations record](../../docs/fbs/operations-2026-11-04.md) preserves that failure; it is not described as successful full acquisition. Independent original-value replay now supports 2,742 official 2024–2026 game rows and 627 completed 2026 results, while preserving every one of the 622 original retrospective model outputs and the previous probability, margin, total and matched-market scorecards. The earlier 624-result snapshot and its qualifications above remain a historical record.

The new display appends 191 rounded DraftKings references and 546 native product records to the 23,911 previously published references. All 63 current-week games remain visible. A separate 567-slot native grid covers each game, the three distinct native providers and winner/margin/total targets. The current-only view has usable winner probabilities for Kalshi 56, Polymarket Global 57 and Polymarket US 52 games. Supported median intervals cover margin/total on 57/57, 57/57 and 50/52 games respectively. These intervals describe quoted medians with an excluded lower threshold and included upper threshold, not expected scores or genuine model forecasts.

The complete grid explicitly retains 21 absent products, 45 after-kickoff-only captures, two unusable winner products and four inconsistent US threshold curves. Missing latest products do not silently fall back to older snapshots. Older observations remain archived and available in their separately qualified historical views. Original native capture clocks are November 4, 9:24–9:28 PM Pacific; the later verification clock is not substituted for them. Individual quote timestamps and latest-pre-kickoff history completeness remain unproved.

`native_current_snapshot.py` requires exact game/provider/product closure and consistent rounded values, clocks and missing states. Its invented tests reject missing/duplicate/foreign slots, fabricated clocks, changed values, scalar-for-median substitution and model-admission claims. The JavaScript selector isolates `CURRENT_SNAPSHOT_ONLY` rows from T120, T60 and both historical pregame selectors. No new model fit, rolling forecast, wager, fee, fill or profit follows from this display update.

## Required releases and partial completion receipts

The November 6 [owner audit](../../docs/fbs/execution-2026-11-06.md) identifies a predecessor release omitted from the actual invocation's allowlist. The credential-free [handoff receipt example](handoff_receipts.py) uses invented releases and payloads to demonstrate a single registry shared by seed validation and receipt admission. Required older releases cannot disappear when a new one is added; duplicate source registrations, changed bytes, conflicting run identities and invalid completion chronology fail validation.

A partial handoff diagnostic preserves zero-work evidence without claiming writer ownership or successful collection. A later partial collector preserves its completed source-unit count without becoming a full success. A recorded diagnostic integer and an independently observed child-process exit are separate fields. The subprocess regression demonstrates that ignoring `main()`'s returned integer produces process exit 0, while `raise SystemExit(main())` propagates the returned status. Missing process status remains unknown.

```bash
python -m examples.fbs_contracts.handoff_receipts
python -m unittest examples.fbs_contracts.tests.test_handoff_receipts -v
```

These are standard-library engineering fixtures, not production owner execution, source authentication by a trusted third party, model fitting or remote process control. The verifier grants no new writer lease. An unchanged content hash alone cannot establish source authenticity, acquisition rights, historical availability or a betting edge.

## November 6 running-owner and acquisition qualification review

The later [acquisition audit](../../docs/fbs/acquisition-performance-2026-11-06.md) distinguishes a running V036 log snapshot from a completed owner return. The latest supplied observation records 25,318 of 79,240 contracts processed successfully according to the log, at 2.33944 contracts per second; per-unit recovery still requires original evidence authentication. Intermittent I/O pressure and independent memory limits are visible. A grouped provider API exists, but the executed caller supplies one contract per group.

The [credential-free qualification example](acquisition_qualification.py) uses invented identities to plan compatible batches without changing windows, retain valid members when others are missing, and reject ambiguous identity sets. A performance gate separates verified-contract throughput, requests, tickers, storage operations and attributed cost. Active owners, stale resources, missing provider authority, errors, integrity failures and synthetic-only timing block full-workload admission. Passing a bounded sample does not guarantee future speed.

```bash
python -m unittest examples.fbs_contracts.tests.test_acquisition_qualification -v
```

The target of ten verified contracts per second is not represented by the invented test timings. The example cannot contact a provider, change ownership, access private data, fit a football model or place an order. Production handoffs and raw evidence remain private.
