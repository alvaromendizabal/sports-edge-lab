# NCAA R29 execution and recovery review

**Evidence checked:** November 18, 2026, Pacific.  
**Latest actual outcome:** verified partial return; scientific campaign incomplete.  
**Next preparation:** R30 engineering and installation verified. No R30 owner execution is credited.

R29 reached a later source-publication step and stopped before new scientific fitting. It reused **1,219 startup cases and 108 historical target checkpoints**. It committed **zero new target, scalar-calibration or empirical-residual fits**, launched **zero scientific workers**, and did not establish the requested 12–24-worker throughput. The return archive and all **219 payloads** passed full integrity verification.

## What actually happened

Four recorded stages completed, including the historical study that reused existing target checkpoints. The later incremental source stage recorded 294 chunks before resource admission deferred its publication path. The recorded error was `V7_BOUNDED_IO_PRESSURE`, with `MEMORY_FULL_PRESSURE` present in the current resource sample.

The terminal sample measured 42.37% memory full-pressure and 42.72% I/O full-pressure over its ten-second averages. Available RAM was 81,163,436,032 bytes, and the resource plan reported 80,735,543,296 bytes available for I/O. Available memory and measured memory-stall pressure describe different conditions. The bounded publication wait was 15.15 seconds. This evidence establishes a live pressure deferral; it does not establish an out-of-memory kill, a failed estimator or consumption of the USD 200 compute guard.

The R29 failure is distinct from the earlier R28 stale recovery deadline. R28's original dated snapshot and review remain preserved. The R29 dashboard does not copy that older cause forward.

| Observation | R29 evidence | Interpretation |
| --- | ---: | --- |
| Matching startup cases reused | 1,219 | Zero fresh startup cases; receipt lookup took 0.046 seconds |
| Historical target checkpoints reused | 108 | Authenticated access to saved models; not new estimators |
| Current-consumer target-fit reuse | 0 | Separate from historical checkpoint recovery |
| New target / scalar / residual fits | 0 / 0 / 0 | No new committed typed fits |
| Requested / peak scientific workers | 24 / 0 | Settings did not become scientific dispatch |
| Peak ready scientific tasks | 0 | The source prerequisite stopped dispatch |
| Owner wall time | 1,738.07 seconds | About 29 minutes, including recovery and source work |
| Parent CPU / completed-child CPU | 1,291.07 / 0 seconds | Parent work is not fit-worker CPU |
| Owner CPU peak, performance ledger | 1.30 cores | Its own observation scope |
| Owner CPU peak, independent sampler | 1.59 cores | A different sampling interval; zero useful scientific-worker CPU |
| Estimated shared-instance wall cost | USD 1.24 | Verified rate times measured wall interval; not an invoice or exclusive project charge |

The scientific occupancy gate was not run on eligible scientific work. The page retains the earlier R22 failed scientific interval as dated historical evidence. Neither the new owner-CPU measurements nor engineering tests establish a current 75%-occupancy pass.

## Source work that must survive continuation

The source pipeline recorded **294 chunks, 2,821,813 chunk rows and 4,932,251,561 logical bytes** before the deferral. The collector held **3,187,384 outcome rows** and **510 completed capture partitions out of 122,177 planned**. These counters describe different stages. They do not prove complete source history, new forecasts, fitting or that every recorded source row has qualified pregame clocks and rights.

Storage telemetry separately recorded 2,085 verified cache reads totaling 2,985,729,188 bytes and 1,513 fresh storage readbacks totaling 5,393,041,268 bytes. Fresh readbacks include publication verification. They are not counts of paid provider requests and must not be converted into provider credits or new model counts.

The next execution should recover exact committed source partitions and model receipts, resume only incomplete tasks, and preserve independent useful work when a source-dependent branch remains blocked. A repeated stage heading must not cause a complete source history to be fetched, normalized or fitted again.

## What remains pending

The verified R30 preparation addresses the failing source-publication boundary with exact snapshot shards and bounded recovery. A source pressure deferral can preserve committed shards and return control to ordinary admission for eligible independent work. Resource and cost guards still apply, and this capability does not prove that scientific workers have run. Existing scientific recipes, completed-fit identities and the independent CPU monitor remain preserved. Its verified preparation and installation remain separate from the eventual user-run campaign. The interactive report contains exact public-safe source, engineering, installation and readiness evidence digests.

The registered scientific program still needs real execution: missing supported V12 basketball feature groups and controlled ablations, appropriate model families, earlier-origin calibration support, forward scalar calibrations and empirical residual distributions, validation-only champion qualification, frozen test reporting, and completed/upcoming forecasts. A registration or implemented method does not prove that any of these tasks completed.

NCAA men and women retain separate populations and champion registries. Validation remains 2024–25 and 2025–26; completed 2026–27 games remain the test report. The 50/50 primary and four sensitivity ratios change annual evaluation aggregation only. They do not change training weights or refit estimators. Missing source histories stay visible, and no new full-population champion or complete historical coverage is asserted.

## R30 preparation and installation verification

The exact canonical replacement passed **1,277 engineering checks**, all executed in that verification: 1,255 startup cases, 12 R30 compatibility cases, 9 validation-supply cases and 1 exact legacy-identity case. Failures, errors and skips were all zero. The package remained unchanged during the gate. These are engineering fixtures; no owner scientific occupancy pass or new fitted model is credited.

Installation then reused **1,255 matching startup cases with zero fresh cases**. The installed files passed full readback verification, and the latest actual return remained the R29 partial return. No R30 owner run, sports-provider request, new fit or process termination occurred during installation. The user still launches the owner campaign.

| Verified artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| Canonical source | 60,221,397 | `efdb132ee0687f9d8da805cdc0395021ceb3abd1229fe82429074e394e254d61` |
| Engineering gate | 45,561 | `77ecab5cb53bba2802a4797fd6411a1169b80649abfb425a61400f73485bf1a2` |
| Installation receipt | 10,635 | `3c1b1be76ed68bc0d6f3aecfcbc30da2db7fad19c0a29b7af0eb0f088b231236` |
| Readiness receipt | 8,586 | `3e8df5e6bf2b3963c0c98e751a3156c80c11ea13213ba8e3e25efad89a84cd71` |

## Continuation and evidence boundary

At the user's launch, resolve the newest verified return and any newer durable task commits again. Reuse exact completed work; use new scientific identities only where the actual inputs, feature recipe, fold, horizon or fitted components change. Keep resource, cost, interruption and atomic-return guards active.

The verified R29 logical-return SHA-256 is:

`2701766810d4b8e0409509a3796f694bd9d105180ec4b76c2a623bece6c6d792`

Its exact return-manifest SHA-256 is:

`0eacb3c560226ba818454aa048ea1ffe840bb8886fc4da1f48a6d918c0cd2cfd`

This page exposes sanitized observations and evidence digests. Private execution packages, storage locations, model bodies, source payloads and active recipes remain outside the public report. Preparing or committing dashboard source is not deployment, a new forecast, scientific completion or a successful owner execution.
