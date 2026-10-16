# Operational evidence

These are timestamped snapshots, not a live dashboard. Continuing AWS jobs may have advanced since capture.

- [Operational status — 2026-10-16 01:00:21 UTC](operational-status_20261016.json)
- [Cumulative execution and cost ledger](execution-ledger_20261016.json)

## Completed public archive collection

The public runner verified **4,492 of 4,492 cataloged files**, totaling **10,016,351,940 bytes**. The final report recorded zero failed, deferred or unattempted assets. This accepts archive byte integrity only; source/season coverage, schema quality and historical pregame availability remain separate gates.

| Track | Assets | Verified source bytes |
| --- | ---: | ---: |
| NBA | 2,909 | 1,863,460,773 |
| NCAA football | 668 | 2,604,738,211 |
| NCAA men's basketball | 466 | 3,064,443,411 |
| NCAA women's basketball | 449 | 2,483,709,545 |
| Total | 4,492 | 10,016,351,940 |

The report completed at 00:58:35 UTC. At the final AWS read, the Processing job still reported `InProgress` while finishing. A successful data-acceptance report and an AWS terminal job status are different facts.

The original NFL archive separately contains 815 pinned assets totaling 722,613,027 bytes. Consolidation verified 1,663 objects including duplicate legacy copies; that migration object count does not inflate the unique dataset inventory.

## Paid work in progress

At approximately 01:00 UTC:

| Stream | Successful captures | Recorded request failures | State |
| --- | ---: | ---: | --- |
| Game markets and college statistics | 8,766 | 34 | Running |
| Player props | 2,945 | 222 | Running |
| Targeted shooting recovery | 46 | 0 | Running |

The base stream includes 6,349 odds captures and 2,417 college-statistics captures. The original unfiltered shooting requests account for the recorded CBBD parameter errors; the targeted job is now filling those gaps using cached source seasons. Recovery is not complete.

The props audit recorded 1,169,351 returned market outcomes across books, players, markets and snapshots. These are not unique bets or players. Of 3,167 audited requests, 2,488 were nonempty and 986 had internally consistent recorded times. Missing events, kickoff revisions and quote updates after the selected cutoff are flagged. Even internally consistent responses still require participant, settlement and source-availability review.

Provider usage headers are account-level and observed at different times by concurrent jobs. Allocate usage from each run's per-request accounting; do not add account-level header totals across runs. The base/props/recovery budgets are respectively 1,000,000 odds credits plus 15,000 statistics calls; 500,000 additional odds credits; and 2,000 additional statistics calls.

The direct ESPN job returned zero captures and exited after HTTP access denial. Its AWS job is classified as failed, and its compact report preserves the reason. No access-control bypass was attempted. Secondary public archives and direct college-data APIs remain separately identified sources.

## Cumulative execution ledger

The final snapshot includes **4 completed, 6 failed and 4 in-progress Processing jobs**, including earlier NFL setup attempts. The four in-progress statuses consist of the public job finishing and three paid streams. Repaired failures remain visible.

Reported-interval compute estimates are **$0.032423 for completed jobs** and **$0.040885 for failed jobs**. They are not billed totals. Running jobs, provisioning/shutdown outside the reported interval, the temporary backup app, storage, API requests and final billing reconciliation remain unallocated.

The five new acquisition jobs' configured runtime limits imply a combined compute estimate of **$2.88125** at their verified $0.461/hour `ml.m5.2xlarge` rate. This is a runtime-bound estimate, not a bill or hard account spending cap. Earlier `ml.m7i.2xlarge` runs use their separate $0.48384 rate. Subscription charges are separate from compute spend.

## Remaining gates

Complete source/season coverage, field quality, identity reconciliation, historical availability, leakage-safe features, trained forecasts and validated market performance remain subsequent milestones. Acquisition success does not establish a betting edge.
