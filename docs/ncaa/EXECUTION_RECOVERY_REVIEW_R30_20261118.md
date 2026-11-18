# NCAA R30 execution: failed historical-clock recovery, preserved work

Evidence date: November 18, 2026. This is a dated NCAA basketball review. Men’s and women’s scientific evaluations and champion registries remain separate.

**R30 actually ran and failed before new scientific fitting.** Its published pointer records `FAILED_RESUMABLE`; the owner summary records `FAILED_PARTIAL_WORK_PRESERVED`. The complete 77,236,704-byte archive and all 220 payloads passed exact-membership, size, SHA-256 and CRC verification. Integrity verification preserves that partial outcome; it does not turn the failure into completed research.

The current [execution dashboard](execution.html) and [exact public JSON](execution_status.json) reflect this actual R30 outcome. The earlier [R29 review](EXECUTION_RECOVERY_REVIEW_R29_20261118.md) remains unchanged historical evidence, including its then-current R30 preparation status.

## What R30 did

| Measure | Authenticated R30 observation | Interpretation |
| --- | ---: | --- |
| Matching startup cases reused | 1,255 | Zero fresh startup cases in this owner attempt |
| Historical target checkpoints authenticated | 108 | Access to saved work, not 108 new models |
| Current-consumer target-fit reuse | 0 | Separate counter from the historical checkpoint audit |
| New target, calibration and residual fits | 0 / 0 / 0 | No new scientific fitting committed |
| Requested / peak scientific workers | 24 / 0 | A worker setting did not become observed throughput |
| Peak ready scientific tasks | 0 | The run did not reach eligible fit dispatch |
| Recorded stages completed | 4 | Includes the historical target study completed by reuse |
| Owner wall time | 939.29 seconds | Authentication, recovery and preparation remain real work |
| Parent CPU / completed-child CPU | 632.60 / 0.00 seconds | Parent CPU is not estimator-worker CPU |
| Historical-study wall / parent CPU | 205.89 / 222.96 seconds | Authenticating reused artifacts still consumed resources |
| Failed incremental-source stage wall / CPU | 17.30 / 16.63 seconds | The clock-recovery failure stopped this stage |
| Verified cache reads / bytes | 823 / 2,538,410,651 | Storage cache observations, not provider requests |
| Fresh full storage readbacks / bytes | 32 / 64,211,528 | Storage I/O, not a source-backfill count |
| Shared-instance wall estimate | $0.67025 | $2.57/hour × 938.87 cost-observation seconds; not an invoice or exclusive project allocation |

The owner CPU peak was 1.23 core equivalents in the performance ledger and 1.40 in the independent sampler. These are different sampling scopes. Useful scientific-worker CPU was zero, and the scientific occupancy gate remained `PENDING_REAL_ELIGIBLE_WORK` with `actual_gate_executed=false`.

The existing utilization chart retains the earlier R22 scientific interval and its failed gate. Neither that chart nor the R30 parent CPU measurement establishes a successful 12–24-worker NCAA research run. R30 did not exhaust the configured USD 200 cost guard according to its verified-rate estimate; billed cost is not supplied by this return.

## Why this attempt failed

The traceback reports `B104_RESPONSE_HISTORICAL_ORIGINAL_CLOCKS` while recovering a previously completed scoreboard response. Its caller escalated that exception to `B032_EVIDENCE_STORAGE_STOP:espn:durable_pending_response_recovery`, stopping incremental source recovery before scientific dispatch.

An authentic isolated replay reproduced the exact failure using the original receipt chain and saved response. R25 captured the response on November 17. R29 adopted those bytes on November 18, correctly retaining the original observation clocks and predecessor receipt reference. R30 then incorrectly required the original observation to occur inside the later adopter’s execution window. A valid older capture cannot satisfy that comparison.

The raw response remained intact: 637,442 bytes, representing 33 provider events. The repaired request path recovered the exact bytes and original clocks, identified R25 as producer and R29 as adopter, and reused the same request on a warm replay. That engineering replay used no provider HTTP requests, owner campaigns or scientific fits. It does not establish full source coverage, model-ready rows or pregame availability for arbitrary snapshots.

This R30 failure is distinct from R29’s live memory-pressure stop. The dashboard does not copy R29’s pressure wait into R30, infer an out-of-memory kill, claim a failed estimator, or treat an intact response as requiring another provider download.

## R31 preparation and limits

R31 preparation is **PREPARED_VERIFIED**. Its frozen canonical source passed 1,318 native engineering checks with zero failures, errors or skips, and its installation passed exact native and storage readbacks. Installation reused 1,284 matching startup cases with zero fresh cases. The scoped clock component includes 21 engineering fixtures and one authentic isolated failure/recovery replay. A separate bounded native preparation replay admitted twelve threads and reused its warm preparation checkpoint; it is not a scientific fitting or three-minute occupancy result. Zero R31 owner campaigns or new scientific fits were launched. R30’s earlier preparation result remains separate historical evidence.

The replacement must authenticate the original producer through every exact referenced receipt, source and raw-response pin. It must preserve the original observation clocks through later adoptions. A clock gap cannot hide corrupted bytes, changed requests, rewritten clocks, or storage/access errors. Those integrity failures remain fatal.

When intact bytes genuinely lack qualified original clocks or producer provenance, the source response must retain explicit request-specific negative evidence. It must receive no model rows, successful-reuse or coverage credit; it must not trigger a provider retry or a provider-wide halt. Independent qualified requests may continue. The repair is restricted to the existing closed-date scoreboard recovery path; it does not relax current/future snapshot rules or authenticate missing historical market clocks by assumption.

Other retained work still needs user execution: exact champion and candidate recovery, common immutable game populations, missing source histories, registered feature and group-ablation branches, target estimators, calibrations, residual distributions, validation-safe blends, complete and upcoming forecasts, and separate DraftKings, Kalshi and Polymarket comparisons. The finite campaign must report completed, reused, failed, blocked and deferred branches. No complete new champion or full source population is asserted.

## What must be preserved at resume

The 108 historical checkpoint accesses are not new fits and must not be summed across retries as unique models. Eleven physical target-fit commits in the earlier audited R22 attempts remain the bounded audit’s new-fit total. The eleven audited invocations span nine run identities and zero completed campaigns; this is not a project-lifetime count.

Resolve the newest authenticated return and durable task journals again at user launch. Reuse exact completed fits and predictions when their data, recipe, temporal split, population and fitted-component identities match. Preserve paid source responses, normalized partitions and task commits. A repeated stage heading can mean authentication of existing work, but authentication still has CPU and wall cost. The evidence does not establish that every remaining preparation step is cached or that all repeated work has been eliminated.

Validation remains 2024–25 and 2025–26, with primary 50/50 annual scores and the declared four sensitivity ratios. Changing evaluation ratios must not refit estimators or alter training-row weights. Completed 2026–27 games remain test-only reporting, with zero selection weight and prior exposure disclosed. Men and women retain independent eligible populations and champion registries.

A user-run execution must still measure actual fit PIDs, CPU, ready depth, completions and starvation. The target remains 12 scientific workers, opportunistically up to 24 when safe, bounded by the explicit hard worker ceiling and native-thread limits. A conditional 75% occupancy check over three minutes requires enough real eligible work. Engineering tests, receipt hashing and synthetic queues cannot satisfy it.

## Publication and exact evidence

This is a prepared NCAA-only dashboard change. It performs zero owner runs, provider retrievals, scientific fits or new forecast issuance. GitHub review and website deployment are separate; production deployment is not verified. All earlier comparison rows and the landing-page scientific body remain preserved.

R30 archive SHA-256:

`0a98aebdc76da760da72c7af110289efecf48737b6eae7bb94ea55e95a530d55`

The public JSON lists the exact scoped integrity, summary, traceback and isolated engineering-replay digests. Private execution packages, source bodies, feature transforms, cache paths and recovery manifests remain outside this public projection.
