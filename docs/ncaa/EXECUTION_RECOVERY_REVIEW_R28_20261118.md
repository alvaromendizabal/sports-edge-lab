# NCAA basketball: R28 recovery stop and verified R29 preparation

This dated review supersedes the current execution banner while preserving the earlier R27, R26 and R25 reviews. The latest **actual owner execution is R28**. Its partial return passed full archive, payload-size, SHA-256 and CRC verification: 132 payloads, archive digest `36c2b6fa93b4d01e24815ee47386e5c7a604756dfaf3560529ac51b13e84f780`. The separate manifest digest is `681fe1fbf752d07b56948ed5b304892b3bef99172bd6482b5686fcc1f9986a8d`.

## What happened

R28 stopped during saved-source authentication with `RESOURCE_DEFERRED_PARTIAL_WORK_PRESERVED`. An initial memory-pressure observation started the configured two-minute recovery wait. The timer remained armed during productive recovery and expired before another read, even though the final resource plan reported no pressure reasons.

The first recorded pressure wait began at 04:58:47.774 UTC on November 18. The deadline stop occurred at 05:00:53.640 UTC. Between those events, 82 verified cache reads succeeded. The final memory full-pressure measure was zero, with 82,178,412,544 bytes of available RAM and 53,981,847,552 bytes available for admitted I/O. The evidence does not establish an out-of-memory kill, an external process kill or a failed estimator.

The 120-second bound came from the configured two-minute recovery setting. It was separate from the disabled owner wall limit and the USD 200 compute guard. It is not a measurement of 120 seconds of continuous memory pressure. The inherited launch-wide timer could expire after the pressure that originally armed it had cleared.

The R28 price verification succeeded. This failure is therefore different from R27's expired-price preflight. The measured shared-instance estimate was about USD 0.15; it is not an invoice or a project-exclusive allocation. The cost observation covers 203.323 seconds and the final owner summary reports 203.602 seconds. Both clocks remain explicit in the public JSON.

## What was reused and what still cost time

R28 reused 1,102 matching startup cases in 0.066 seconds, with zero fresh startup cases. All 50 predecessor archive requests were durable-cache hits: 2,819,356,013 compressed bytes were reused and no predecessor recompression or durable ancestor eviction occurred. Separately, a small in-memory byte cache evicted 50 entries. Those are different caches and different observations.

Recovery still inspected archives and fingerprinted 6,142,295,143 ancestor input bytes. It consumed 136.850 parent CPU seconds and zero completed-child CPU seconds. The owner recorded 83 verified storage-cache reads totaling 533,794,468 bytes and three small full storage readbacks totaling 2,589 bytes. These readbacks are not additional source-provider downloads.

The run requested 24 workers but measured zero scientific workers, zero ready scientific tasks, zero new target fits, zero calibration fits, zero residual fits and zero new forecasts. The real-work occupancy gate remained pending. Cached startup checks, package engineering and parent authentication CPU do not establish 12–24-core scientific throughput.

The audit now covers **nine owner invocations, seven run identities and zero completed campaigns**. Eleven earlier R22 physical target-fit commits remain preserved. Historical receipt references and repeated checkpoint accesses are not additional fitted models.

## R29 preparation and scientific limits

R29 is prepared and installed with verified source bytes. Its final native packaged engineering gate passed **1,242 test executions**, with zero failures, errors or skips: 1,219 startup tests, 13 compatibility tests, nine supply tests and one heavyweight-reuse test. The gate receipt digest is `53edd7bbd87d57d616adf0e7e511125035e170256a3bdb88abab8cbb71e0ebb2`. An earlier engineering attempt exposed a test-fixture resource-loading error; that failed attempt remains separate from the corrected final passing result. Native installation then reused all 1,219 matching startup cases with zero fresh cases.

The canonical package contains 59,641,046 bytes with digest `604e1403e1565a333bfd57978c5315bf93499bde680d90ea3a6a96e021442257`. Installed source bytes, the installation receipt and the preparation record passed complete integrity readback. The installation receipt digest is `29e9ed762751e9940b6be7ced388f69049009ccf2369cdd101c5d1146e0496a2`. These are preparation and engineering results: **zero R29 owner executions and zero new owner fits** are claimed at this observation. No scientific occupancy pass or completed campaign follows from package verification.

The implemented workflow includes forward validation calibration and empirical residual distributions, evidence-based objective-specific champion selection, causal V12 feature materialization and ablations, and locked completed/upcoming inference. These stages still require owner execution and eligible evidence; this dashboard does not invent their scientific results.

At owner launch, resolve the newest verified return and newer durable checkpoints again. Preserve exact completed fit and prediction identities, cache genuine paid-source captures, and continue only unfinished eligible work. Current resource admission and the compute cost guard remain active.

Men and women retain separate populations and registries. Annual 2024–25 and 2025–26 validation metrics select candidates, with 50/50 primary and the declared sensitivity ratios. Changing score ratios does not refit estimators or reweight training seasons. Completed 2026–27 games remain descriptive exposed test evidence; upcoming games have no outcome labels. No current full-population champion or scientific improvement is invented by this dashboard.

## Publication boundary

This is an NCAA-only draft-source review. Scientific comparison values, earlier dated snapshots, original forecast evidence and other sports are preserved. The page performs zero owner executions, fits, provider requests or forecast issuances. Source review, native package verification, owner execution and website deployment are distinct events. Private execution packages, storage addresses, model bodies, active transforms, source payloads and support correspondence remain outside this public report.
