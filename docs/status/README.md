# Operational evidence

The latest comparable content scan is [19:23:51–19:24:43 UTC](content_inventory_20261016T1924Z.json):
71,181 files / 14,393,519,871 stored bytes, with zero unclassified raw objects.
The [expanded collection record](../EXPANDED_DATA_COLLECTION_20261016.md) explains
current acquisition, the corrected shooting priority, and the verified one-time
NCAA schedule. Earlier snapshots below remain dated evidence.


Snapshots are timestamped evidence, not a live dashboard. The 18:10 UTC content scan excludes receipts, indexes, audits and duplicate legacy archives. The three completed paid-run summaries retain their original timestamps.

- [Frozen completed-run operational snapshot](operational-status_20261016T1810Z.json)
- [Raw content inventory](raw_inventory_20261016.json)
- [Archive family and filename-year inventory](archive-family-coverage_20261016.json)
- [Cumulative execution and cost ledger at 18:45 UTC](execution-ledger_20261016T1845Z.json)
- [Continued acquisition runtime at 18:56 UTC](frontier_runtime_20261016T1856Z.json)
- [Final AWS job-status supplement at 18:56 UTC](frontier_job_status_20261016T1856Z.json)
- [NBA completion and earlier quote audit](frontier_runtime_20261016T1846Z.json)
- [Frontier-relevant acquisition milestone](../FRONTIER_ACQUISITION_20261016.md)
- [Data coverage, limitations and next acquisition](../DATA_COVERAGE_AND_NEXT_ACQUISITION.md)

The earlier 01:00 UTC snapshots remain historical evidence. They described jobs that were active then; all 14 of those jobs are now terminal. AWS Completed does not mean every planned request finished: several collectors stopped normally at configured credit or runtime limits. New executions and bounds are documented in their own launch receipt.

Stored bytes measure content on S3. Captured response bytes measure uncompressed HTTP bodies and can repeat data; do not add them to stored archive sizes. Distinct payload files do not imply independent games or observations. Season years parsed from filenames do not certify nonempty or complete seasons.

The ledger estimates compute using reported Processing start/end intervals and the recorded instance rates. It separates completed and failed jobs and does not replace the AWS bill. Storage, requests, subscriptions and provisioning/shutdown outside those intervals remain excluded.

The 18:45 ledger predates NOAA v018 and v019. Later launch and final job-status supplements preserve those executions. The 18:56 NOAA report completes the selected data scope while AWS still reports InProgress during finalization. NBA and NWS jobs are Completed; both paid continuations remain InProgress.


## Current continuation evidence

- [Corrected content census at 19:24 UTC](content_inventory_20261016T1924Z.json)
- [Paid and NOAA progress at 19:26–19:28 UTC](live_progress_20261016T1928Z.json)
- [Positive shooting-data gates and AWS tests](shooting24_test_and_canary_evidence_20261016.json)
- [Shooting runtime and final stopped-run audit](shooting24_progress_20261016T1929Z.json)
- [Cumulative 29-execution ledger](execution_ledger_20261016T1929Z.json)
- [Verified future NCAA schedule and zero-request preflight](ncaa_schedule_verified_20261016.json)

The stopped shooting collector's detection checkpoint was 300 empty responses;
its frozen final receipt audit counted 580 empty and zero nonempty responses.
The corrected collector had 30 nonempty positive responses / 2,384 observed
records at 19:28:52 UTC. Original and corrected source versions are retained.
