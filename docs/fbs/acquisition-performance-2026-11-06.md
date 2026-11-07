# Acquisition performance, recovery and honest qualification

[Research frontier](frontier.html) · [Aggregate evidence](frontier-review.json) · [Invented executable example](../../examples/fbs_contracts/acquisition_qualification.py)

**V036 has a dated running-log observation, not a completed owner return. V037 preparation must preserve that owner and qualify faster work before full dispatch.** No new model fit, forecast issue or betting edge follows from this engineering review.

## What the actual observation establishes

The supplied execution log contains 3,876 parseable events. Its latest observation is November 6, 2026 at **3:59:22 PM Pacific** (23:59:22 UTC), later than the 23:50 snapshot quoted in the request.

| Observed quantity | Dated log value | Qualification |
|---|---:|---|
| Registered contracts in the active stage | 79,240 | One stage, not the full project |
| Contracts reported complete | 25,318 | Each needs independent recovery authentication |
| Remaining contracts | 53,922 | At that observation only |
| Failed contracts | 0 | Does not authenticate unfinished work |
| Cumulative contracts per second | 2.33944 | Stage counter divided by elapsed time |
| Native HTTP attempts at the last heartbeat | 29,882 | Different clock and denominator from contracts |
| Fresh verified native requests | 29,881 | One fewer than HTTP attempts |
| Native sink PUT calls / readbacks | 59,767 / 59,765 | Excludes other store and reader accounting |
| Whole-owner return / terminal exit | Unavailable | Neither is invented |

The exact original history assessment remains preserved for recovery. Later publication and fresh source observations retain their own clocks. The log does not provide per-request latency quantiles, complete provider-specific request rates or allocated cost per verified contract.

V035 remains the last authenticated **completed diagnostic** owner return. It failed before collection because a required predecessor release was omitted from an admission allowlist. V034's earlier disk-headroom deferral remains a separate failure. A newer running observation does not rewrite those outcomes.

## Source-level findings

The inspected source contains both ordinary batch history acquisition and a repaired grouped minute/history implementation. Batching is present. The executed durable recovery adapter, however, intentionally invokes the grouped engine with a single contract. That caller structure explains one-ticker calls to a batch endpoint; endpoint shape alone does not prove a fallback, an archive route or incompatible timestamps.

The actual transport repeats the provider interval table, independently of the runtime defaults. Editing a default table without changing the dispatch path would leave the limit intact. The configured Kalshi and US-market rates are conservative local policies; they do not demonstrate account-specific entitlement. Any higher rate requires provider- and access-mode-specific authority and a measured error/cooldown response.

A provider in-flight ticket remains occupied through HTTP, compression, local receipt work and canonical object persistence/readback. Those stages need separate bounded admission: release a provider connection after the complete response is drained, while retaining memory and storage capacity until the original bytes and receipt are durably verified. Request success, canonical object persistence, selector replay and a completed contract remain different milestones.

The two-GiB per-worker reserve is a conservative estimate based on worst-case raw and decoded copies. Replacing it safely requires bounded bodies and queues, measured peak memory and explicit parsing/persistence budgets. Increasing the configured worker count alone is not a memory proof. HTTP connection reuse likewise requires bounded sockets, complete draining or closure, certificate checks and the same allowlisted read-only source scope.

## Independent recovery sample

A bounded canonical-object review checked eight completed historical units. All eight passed the original selector, cutoff, row, ordered-dependency and interval-proof checks using twenty original source dependencies. Forty raw/receipt reads and eight history-commit reads supported that review; offline replay made zero provider calls. These are verified inherited units with **zero new completion credit**, not certification of the complete workload.

A separate 24-receipt shard sample contains thirteen live Kalshi batch requests, all with one ticker, one archived Kalshi request, nine US-market requests and one Global-market request. Each sampled receipt records HTTP 200 and one transport attempt. This deliberately bounded sample corroborates the source routing but is not a workload-wide batch or fallback estimate. Request paths and original response bodies remain private.

## Pressure is intermittent

The audit contains 419 heartbeats and 210 detailed resource snapshots. Seventeen samples apply an I/O-pressure reduction, including five severe samples; thirteen defer for memory headroom. Admitted I/O capacity ranges from zero to eight. During the 21:00 UTC hour, no sample reports an I/O-pressure reduction even though low and zero capacities occur. Memory pressure and co-running workloads therefore matter separately.

These are sample frequencies, not a continuous duration estimate. Low CPU is not a health certificate. NFL, NBA, NCAA basketball and unrelated work remain protected, and a successor must remeasure resources before scheduling. GPU visibility is not established by these observations.

## Recovery must remain exact

Historical recovery first authenticates each original receipt and compressed/decoded body, then replays the selector and interval proof without provider access. A completed raw request is reusable evidence for an unfinished reduction, not automatic proof that the reduction has already completed.

The executed checkpoint identity binds historical contract inputs, source closure and the full cutoff state. The legacy literal assessment-equality shortcut is not the active adapter. An already-past contract can retain the same fingerprint at a later assessment when every cutoff field is unchanged; crossing a previously future cutoff changes the state. The original assessment still remains the recovery authority, and new current observations must be separate.

A shared multi-item response can preserve individual contract identities. Compatible batches must use the same provider/access mode, route, period and exact window, and obey response-size limits. Valid members need not repeat merely because another member is absent. Duplicate or unexpected identities remain a quarantine condition; empty data cannot substitute for a missing or rejected response. All original attempts and negative findings remain retained.

## A real, bounded public protocol probe

At November 6, 4:16 PM Pacific (November 7, 00:16 UTC), three local anonymous read-only requests returned HTTP 200 under a maximum dispatch allowance of two requests per second. Two requests contained one ticker each; a genuine batch contained sixteen and returned all sixteen. Both original single-request candle arrays matched their corresponding batch arrays. There were no retries.

| Request | Requested / returned tickers | Observed HTTP seconds | New verified contracts |
|---|---:|---:|---:|
| First single request; cold connection | 1 / 1 | 7.975829 | 0 |
| Second single request; reused connection | 1 / 1 | 0.034753 | 0 |
| Genuine batch; reused connection | 16 / 16 | 0.047804 | 0 |

This demonstrates protocol compatibility and preservation of the paired original values. It is **not an end-to-end contract-throughput benchmark**: complete earlier-history recovery, canonical per-contract commit/readback and fresh SageMaker resource admission are outside this timed scope. Cold/warm differences and three requests cannot establish a sustainable speedup, a higher account entitlement or the ten-contract-per-second target. Original provider bytes remain private.

## Full-workload qualification

The target is **at least ten verified contracts per second**. It is not a guaranteed rate. A qualified benchmark must include completed canonical commit/readback and independent reduction verification, not just HTTP responses or an in-memory loop.

| Required measurement | Meaning |
|---|---|
| Verified contracts/second | Durable, independently accepted units divided by measured elapsed time |
| Requests/second and tickers/request | Provider load and batching effectiveness, kept separate |
| S3 operations/contract | Includes the actual source, receipt and reduction persistence boundary |
| p50/p95 latency and 429/5xx responses | Observed request timing and provider stress |
| CPU, RAM and I/O pressure | Fresh shared-instance resource admission |
| Cost/verified contract | Only attributed cost; unknown allocation stays unavailable |
| 8/16/24/32 worker configurations | Inspected when safe; larger pools are not presumed faster |

**Current full-workload decision: NO GO.** A qualified production rate has not been established. Existing V036 ownership remains protected, and V037 must authenticate a recovery boundary and pass its bounded provider-and-storage qualification before full dispatch. This status will be updated only from actual measured evidence; local fixture rates cannot fill it.

The public [qualification implementation](../../examples/fbs_contracts/acquisition_qualification.py) and [failure tests](../../examples/fbs_contracts/tests/test_acquisition_qualification.py) use invented inputs. They demonstrate batch identity, selective retry and admission rules without network access, private cloud identifiers, production recipes or real market payloads. The existing 622-game replay, negative path/availability studies, complete 888-game report and zero-stake decision remain unchanged by this performance work.
