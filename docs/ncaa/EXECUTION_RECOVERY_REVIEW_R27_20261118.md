# NCAA basketball: R27 stopped on expired price evidence

The owner attempt began at **November 17, 2026, 6:56 p.m. Pacific** (`2026-11-18T02:56:12.094187+00:00`). This is a dated, verified partial-return review. The R26 review and all earlier attempt rows remain unchanged.

[Execution dashboard](execution.html) · [Exact current public report](execution_status.json) · [Preserved R26 review](EXECUTION_RECOVERY_REVIEW_20261118.md) · [Preserved model comparison](three_seasons.html)

## What stopped the attempt

R27 stopped before scientific fitting because the saved instance-price evidence had expired. The genuine quote was observed at `2026-11-11T02:36:39.054419+00:00`; its seven-day validity window ended at `2026-11-18T02:36:39.054419+00:00`, about twenty minutes before launch. The price preflight recorded `B060_PRICE_EVIDENCE_STALE_OR_FUTURE` and did not establish a usable current rate.

The owner then recorded the status `WORK_BUDGET_DEFERRED_PARTIAL_WORK_PRESERVED` and error `B057_WORK_BUDGET_EXHAUSTED`. Those recorded values are preserved. **They do not establish that the USD 200 compute guard was consumed.** The identified cause was expired price evidence; current cost remains unknown. The public data uses `null` for cost, with no invented zero-dollar estimate or inferred invoice.

## The partial return was preserved and verified

The **58,805,077-byte R27 return archive** passed full member reads, CRC checks and exact manifest closure: **52 payloads verified**. Its partial status remains distinct from scientific completion.

| Evidence | SHA-256 |
|---|---|
| R27 partial return | `45ac375264849a50271db7778a9d1fa83ae04e4b77f9798d6cf2581f16489156` |
| R27 exact return manifest | `65b493fba4990cbd4344880e937a8019b621b9d4c799707681a391ed6da9fec7` |

Continuation must resolve this return and any newer authenticated durable work again at launch. The new partial archive does not erase earlier R26 receipts, recovered R25 progress, older returns or completed scientific artifacts. It is not authority to start the entire study again.

## What was actually measured

| Measure | R27 observation |
|---|---:|
| Matching startup cases reused | 1,074 |
| Fresh startup cases executed | 0 |
| Startup receipt lookup | 0.065111245 seconds |
| Owner elapsed time | 2.633409874 seconds |
| Parent CPU time | 2.228032 seconds |
| Completed-child CPU time | 0 seconds |
| Recorded stages completed | 0 |
| Requested workers / scientific peak | 24 / 0 |
| New target / calibration / residual fits | 0 / 0 / 0 |
| Current-consumer verified target-fit reuse | 0 |
| Current cost | Unknown |
| Current cache, fresh-storage and pressure-wait measurements | Not reported |

Startup reuse is measured owner evidence: those 1,074 cases were not rerun in this attempt. Neither startup checks nor parent CPU count as optimizer work. The return did not include the prior storage-read report, so R26's storage measurements are retained only in their dated row and review. Missing measurements remain unknown rather than becoming zero.

The table now contains **eight audited attempts across six run identities**. Its seven earlier rows remain unchanged. The **11 new physical target fits** still belong to the earlier R22 first attempt; they are not duplicated or reassigned to R27. Historical checkpoint accesses are separate reuse counts and do not become additional unique models.

## What remains unproved

R27 did not enter the scientific queue, produce new forecasts, rescore a champion or complete the conditional three-minute scientific occupancy gate. The displayed failed R22 throughput interval remains historical evidence. Requesting 24 workers does not prove that 24 workers fitted models.

The next execution needs verified current price evidence and a finite compute-cost guard even when its optional wall-time limit is disabled. R28's price and budget-entry repair is being prepared and checked; this report claims no R28 owner execution or scientific improvement. The continuation must preserve exact-identity startup and scientific checkpoints, resume missing eligible work, and separately measure preparation, fit CPU, useful completions and queue supply.

## Scientific and publication boundaries

Men's and women's evaluations and champion registries remain separate. The declared 2024–25 and 2025–26 seasons select models; completed 2026–27 outcomes retain zero selection weight. Prior test exposure stays disclosed. Changing validation-score ratios does not reweight training rows or refit estimators.

This NCAA-only draft source update preserves all numerical scientific comparison data and prior dated snapshots. It publishes sanitized aggregate evidence, not private execution packages, active recipes, raw provider data or cloud paths. It performs zero owner runs, fits, source retrievals or forecast issues. A source review, merge and website deployment remain separate events; deployment has not been verified.
