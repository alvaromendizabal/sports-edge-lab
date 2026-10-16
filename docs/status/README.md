# Operational evidence

The JSON files in this directory are **timestamped snapshots**, not a live dashboard. Continuing AWS jobs may have advanced since capture.

- [Operational status — 2026-10-16 00:53:30 UTC](operational-status_20261016.json)
- [Execution and cost ledger — same snapshot](execution-ledger_20261016.json)

## Interpreting acquisition counts

The initial NFL archive has 815 pinned assets totaling 722,613,027 bytes. The consolidation separately verified 1,663 objects including duplicate legacy copies, so its object count must not inflate the unique dataset inventory.

Public acquisition had cataloged 4,492 release assets totaling 10,016,351,940 source bytes. At 00:53:20 UTC, 2,643 assets had been processed and 817,475,475 bytes downloaded. Processed does not mean every file was successfully acquired; final receipts classify downloaded, reused, failed, deferred and unattempted units.

The paid base runner reported 5,554 captures and 3,329,493,477 raw, uncompressed response bytes at 00:52:46 UTC. It had used 120,930 known odds credits and 1,545 college-statistics calls. Its 22 optional CBBD shooting-query errors remain distinct from successful captures; the corrected current source does not retroactively repair a running v001 execution.

The props runner reported 872 captures and 32,813,782 uncompressed response bytes at 00:52:41 UTC. Audits counted 434,453 returned market outcomes, which can repeat across books, players, markets and snapshots; they are not 434,453 unique bets or players. Of 922 audited requests, 824 were nonempty and 409 had nonempty responses with internally consistent recorded times. Missing events, kickoff revisions and quote updates after the selected cutoff are explicitly flagged. Even the 409 consistent responses still require participant, settlement and source-availability review.

Provider usage headers are account-level and were observed at different times by concurrent jobs. Use each run's reconciled per-request accounting to allocate its usage; do not add provider account totals across runs.

## Access denial

The direct ESPN job returned zero captures and exited after HTTP access denial. Its AWS job is classified as failed, and its compact report preserves the reason. No access-control bypass was attempted. Secondary public archives and direct college-data APIs remain separately identified sources.

## Execution ledger

The snapshot includes 4 completed, 6 failed and 3 running project Processing jobs, including earlier NFL setup attempts. Counts must not hide repaired failures or treat an in-progress run as successful.

Reported-interval compute estimates are $0.032423 for completed jobs and $0.040885 for failed jobs. These are **not billed totals**. Running jobs, provisioning/shutdown outside the reported processing interval, the temporary backup app, storage, API requests and final billing reconciliation remain unallocated.

The verified rate used for new `ml.m5.2xlarge` Processing jobs is $0.461 per hour. Earlier `ml.m7i.2xlarge` runs use their separate $0.48384 rate. Subscription charges are not compute spend.

## Remaining gates

Complete source/season coverage, field quality, identity reconciliation, historical availability, leakage-safe features, trained forecasts and validated market performance remain subsequent milestones. Current raw data must not be presented as a proven betting edge.
