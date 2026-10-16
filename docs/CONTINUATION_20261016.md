# Acquisition continuation — 16 October 2026

**Verified at 18:20 UTC:** v011 and v012 are InProgress; v013 is Completed. The cumulative ledger now has nine Completed, six Failed, and two InProgress jobs.

This continuation preserves successful cached work from the first milestone. Its frozen starting inventory is 46,069 raw content files / 12.42 GB, recorded separately from later downloads.

## New execution scope

| Job | Scope | Bound |
| --- | --- | --- |
| `sports-edge-lab-gap-backfill-20261016-v011` | Missing game-market checkpoints across all five tracks; remaining CBBD play history; current documented college basketball lineup and substitution history. Historical props are deferred this batch. | 1,600,000 additional odds credits, 30,000 college-statistics calls, 14,100 application seconds and 14,400 Processing seconds. |
| `sports-edge-lab-original-context-20261016-v012` | Original current NWS forecast vintages for cached US college venues and one explicitly discovered official NBA injury PDF; source-access results remain explicit. | 300 public requests and 900 Processing seconds; exact source scope and result are in its manifest and receipt. |
| `sports-edge-lab-public-delta-20261016-v013` | Rediscover selected public release assets and acquire new or changed revisions. Reuse unchanged verified files in the existing archive. | Four workers, 3 GiB new downloads, 900 application seconds and 1,200 Processing seconds. |

Each job uses `ml.m5.2xlarge`, with an observed Processing rate of $0.461 per hour. The configured Processing runtime ceilings imply approximately **$2.1129** combined compute if all three consume the full interval. This is a runtime estimate, not a billing cap, and excludes provisioning, storage, requests and subscriptions. API ceilings are not claims of consumption.

Read [launch evidence](status/continuation_launches_20261016.json) for actual job states, creation times, artifacts and final snapshots. A planned row alone does not establish that a job launched or completed. Each executable runs offline guards before acquisition and writes resumable evidence and a compact return bundle.

## Public delta result

The public delta data phase finished at **18:15:42 UTC** with all byte-integrity checks passed: 19 new immutable revisions, 44,710,821 bytes downloaded, 4,473 existing files reused, zero failed/deferred/unattempted assets. The current logical catalog remains 4,492 assets, now totaling 10,016,647,217 bytes. Old revisions remain retained. AWS subsequently confirmed completion at **18:15:58 UTC**; the compact [result receipt](status/public_delta_summary_20261016.json) records both data completion and job completion.

The original-context collector is an access and provenance milestone. Its single NBA seed report does not establish historical injury coverage, and current NWS forecasts cannot fill past forecast vintages.

## Why this scope

The existing statistics archive is broad. The most immediate gaps are odds observations at usable decision times, original player availability vintages, incomplete college basketball play history, and reliable identities. This batch adds missing data and source context while retaining earlier acquisitions. It does not rerun completed model experiments or present newly downloaded data as validated model features.

The first prop batch exposed substantial quote-time and kickoff inconsistencies. New prop credit spending is deferred while the repair path is investigated. More raw prop volume would not fix that eligibility problem by itself.
