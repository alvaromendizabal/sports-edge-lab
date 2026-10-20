# Football validation V046 — October 16, 2026

AWS confirmed `Completed` with processing end time **2026-10-16T23:25:14.369000+00:00**. The application completed three stages with zero failed cache requests and zero remaining selected requests. This is a completed validation/acquisition run with explicit modeling gaps, not full training-data approval.

## Actual results

- Audited **4,696/4,696** v039 historical NCAAF request receipts. Download acquisition was already complete; no historical odds call was made.
- Read **4,589 unique cached objects / 90,545,756 compressed bytes**. Grouping identical object keys avoided 107 redundant S3 reads. Eight S3 read workers do not increase provider request rates.
- Examined **8,014,295 market observations / 16,028,590 outcome entries** across repeated snapshots. **453,268 markets were rejected** by the supported-market, price/line and event/time checks; 7,561,027 passed those checks only. These are repeated observations, not independent games or guaranteed usable features.
- Built a **3,885-event** provider-ID registry: **1,674** IDs have multiple kickoff times and **20** have team-name/pair revisions. Canonical game/season/settlement reconciliation remains required.
- **17 responses were more than ten minutes older than requested**, including 15 over an hour. The largest snapshot gap was **300,900 seconds (83 hours 35 minutes)**. The lag bands are preserved in independent verification. Do not relabel the requested time as the actual snapshot time or treat stale prices as fresh.
- Saved **374 current NFL injury rows** at **23:23:06 UTC**, including **14 changed rows** versus the previous capture; zero parser rejects. Original publication times and player IDs remain unverified.
- Preserved the Friday Washington–Purdue DOM subset observed at **23:16:06 UTC**: 20 source rows, **19 valid uniquely joined pregame candidates**, one missing-jersey quarantine. The full displayed archive had 719 rows. The valid subset had zero changed statuses and zero final game-day statuses; it is not counted as 19 new unique records.
- Rechecked eight public release assets and skipped unchanged payloads: **23,412,405 bytes** of unnecessary downloading avoided.

Reason counts overlap: event already started at request time 396,700; bookmaker update at/after kickoff 338,337; market update at/after kickoff 338,314; unsupported market 47,876; invalid decimal price 22,896; inconsistent totals 7. Unsupported markets are outside this parser's selected three-market schema, not necessarily erroneous provider data.

## Execution, bounds and verification

Job: `sports-edge-lab-football-validation-20261016-23-v046`. Existing bucket, execution role, image and one `ml.m5.2xlarge` instance were reused. No IAM changes, subscriptions, outreach or license acceptance. The exact job name did not exist and no overlapping project job was active before launch. No short application timer; a finite cache/acquisition queue terminated normally. Provider requests were limited to two NFL public URLs, at one request/second or a longer robots interval. HTTP 401/402/403/429 stops persist in the shared weekend ledger.

**95 offline tests passed before runtime credentials/network, and all 95 passed again in AWS.** They include full embedded-entrypoint execution, unique ZIP output, deduplicated cache reads, corruption recording, timestamp/market rejection and the prior identity/acquisition regressions. Heartbeats recorded progress; there were zero heartbeat errors. Zero odds subscription credits, zero CFBD calls and zero CBBD calls. Supplemental weekend CFBD usage remains 0/160.

Artifact: `sports_edge_lab_football_validation_v046.pyz`, 52,523 bytes. SHA-256 `c446805946e764f44610d4fed05a7a49453dcc968362be87f175d6830f047c3b`. Exact sources are in [tools/football_validation_v046](https://github.com/alvaromendizabal/sports-edge-lab/tree/b247d233fee72734c868e07e24b4de67704e2a2a/tools/football_validation_v046).

One unique return ZIP exists at `s3://sagemaker-sports-edge-lab-560403859723-us-west-2/shared/acquisition/football-validation/20261016T232304Z-954fca0a08/sports_edge_lab_football_validation_return_20261016T232304Z-954fca0a08.zip`: **3,845 bytes**, SHA-256 `453703dd19806c86b7e7d0034a14c4822416bf74abfbfe72ab2a63de3ab0420f`. ZIP integrity and equality to the saved report were verified. All 4,696 unique manifest IDs and both market/rejection counters were independently recomputed from the saved manifest.

The AWS processing interval was **168.771 seconds**, approximately **$0.021612** at the previously recorded $0.461/hour rate. This excludes S3, provisioning/shutdown outside that interval and existing subscriptions; it is not an invoice.

## Current inventory and next work

The completed paginated inventory observation through 23:30 UTC counted **101,035 raw content files / 17,392,985,532 bytes (17.39 GB)**. It excludes receipts, indexes, code, derived tables, legacy duplicates and ACB. All new source paths are classified, including the verified SEC DOM capture. Counts include overlapping source revisions and do not imply model eligibility. The ACB canonical raw prefix is empty.

Start core NFL/NCAAF model development now; finish canonical game joins, prediction-time feature tables and chronological evaluation before trusting results. Older cached football odds blocks still require equivalent validation. The weekend collector continues with newly published games and availability; full tracking/video access is a separate unconfirmed workstream. [Concrete modeling plan](FOOTBALL_MODELING_START.md).

[Terminal/log/ZIP/audit evidence](status/football_validation_v046/) · [Inventory evidence](status/content_inventory_20261016T2330Z.json) · [Prior identity repair](FOOTBALL_QUALITY_V045.md)
