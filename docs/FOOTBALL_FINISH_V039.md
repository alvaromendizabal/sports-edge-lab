# Continuous football completion v039 — October 16, 2026

**Verified terminal outcome — October 16, 22:51 UTC:** AWS `Completed`, ProcessingEndTime `2026-10-16T22:47:02.416Z`. The frozen selected queue is complete: 4,696/4,696 successful NCAAF historical US game-price requests, zero final failures and zero remaining. Receipt identities exactly match the frozen plan. Two retryable incidents consumed a conservative 60-credit unknown-charge reserve; known usage is 140,880 existing subscription credits. Final account header: 2,074,356 remaining. One 574,596-byte return ZIP passed CRC and receipt/plan validation (SHA-256 `144f02c84a974172cf21cdf76df7b525abcea4cbc0c7a6ccff432b4b88af0f3b`). The processing interval is 5,529.085 seconds, approximately $0.708 at the recorded $0.461/hour rate, excluding S3 and subscription costs. No restart occurred. [Terminal and independent receipt verification](status/football_finish_v039/). Older progress observations below are historical.


**Latest observation — October 16, 22:29:34 UTC:** AWS `InProgress`; S3 heartbeat at 22:29:33 reports 3,673/4,696 captured, 1,023 remaining, zero final failures, two retryable incidents, 110,190 known odds credits and 60 unknown-charge reserve credits. Last account header: 2,105,046 credits remaining. No terminal outcome or final ZIP yet. V039 was not changed or restarted. [Raw observation](status/football_refresh_v041/odds_observation.json).

The user authorized the next necessary downloads without short application runtime windows. V039 replaces the prepared v038 restart. V038 was never launched and must not be launched by the old follow-up.

## Scope and endpoint

Run one finite queue of missing NFL/NCAAF historical US moneyline, spread and total checkpoints. Keep the original event-derived horizons (72 hours, 24 hours, 6 hours, 15 minutes) and v011 cutoff `2026-10-16T18:10:06Z`. Reconcile successful request-index keys before source access. The preserved checkpoint suggested 4,697 missing NCAAF requests and zero NFL requests; runtime cache reconciliation is authoritative.

Refresh only the current official NFL Week 6 injury report, at most one data request plus robots policy, with the existing hourly cache and HTML/source checks. Already acquired roster pages, schedule, recent plays, weather and shooting are not reacquired. Keep the recent Big Ten capture and the existing American Conference release-window schedule; unpublished reports cannot be pulled early.

No basketball historical requests, exhaustive player props, college-statistics requests, ACB data, new vendor subscriptions, licenses or outreach are included. All five project tracks remain configured; this acquisition milestone focuses on immediate football readiness.

## Execution controls

- Application runtime cutoff: **none**. The process exits when the selected queue finishes or a real quota/provider/access/error condition stops it.
- AWS account maximum processing runtime: **432,000 seconds (five days)**. This service constraint is not an expected job duration. The first request at the API-wide maximum of 777,600 seconds was rejected before creating any job; no quota increase was requested. The corrected request uses the account maximum.
- Existing odds subscription ceiling: **200,000 credits**, zero CFBD/CBBD calls. One authenticated source request/second. No additional API purchase.
- Require at least the full 200,000-credit run ceiling plus a 100,000-credit reserve before bulk work; check the reserve on later response headers as well. Stop on provider authentication/access denial or HTTP 429.
- Existing `SportsEdgeLabProcessingRole`, canonical bucket and one `ml.m5.2xlarge` with 30 GB. No permission expansion.
- **62 local self-tests passed** before runtime AWS credentials or source HTTP. Tests also execute first inside AWS.
- Real embedded predecessor receipt: v011 Stopped with ProcessingEndTime `2026-10-16T20:49:04.439000+00:00`, observed by the AWS connector at 21:08:55 UTC. No worker management-plane permission needed.
- SHA-256: `bccdc8e2c87269bfae01c8e8d25a85e374df8b3c455cdf095716cd806dd48769`; artifact 43,343 bytes.
- Launch succeeded at **21:14:08 UTC** as `sports-edge-lab-football-finish-20261016-v039` after exact-name/overlap checks. AWS reported InProgress at 21:14:50 UTC; this alone is not proof of source captures.

There is exactly one uniquely named return ZIP, `sports_edge_lab_football_return_<run_id>.zip`, with summary, receipts, failures, frozen plan, availability report and resume state. S3 progress every 30 seconds records processed/remaining requests, failures, quota and estimated compute. Runtime evidence below distinguishes launch, download activity and completion.

The previous short-restart follow-up is repurposed to **monitor v039 only** and disable itself after recording a terminal outcome. It cannot launch v038 or another job. Existing current-snapshot and American Conference schedules remain unchanged.

At the verified rate of $0.461/instance-hour, compute depends on actual elapsed runtime. A 4,697-request queue has a rate-limit floor around 78 minutes; storage, network latency and source responses add time. The five-day AWS ceiling is not a forecast or a charge for five days. S3 storage/requests and source subscription credits are separate from compute.

## Evidence

- [Artifact and source hashes](status/build_v039_20261016.json)
- [Local test log](status/v039_local_tests_20261016.txt)
- [Launch request](status/football39_job_request.json) and [successful launch receipt](status/football39_launch_20261016.json)
- [Service-limit rejection before launch](status/football39_service_limit_incident.json)
- [Embedded predecessor receipt](https://github.com/alvaromendizabal/sports-edge-lab/blob/b247d233fee72734c868e07e24b4de67704e2a2a/tools/football_finish_v039/src/predecessor_terminal.json)

## Verified running captures — 21:17 UTC

AWS runtime passed all **62 tests**, then started run `20261016T211526Z-92ef3be742` at 21:15:27 UTC. The live quota check passed with 2,215,236 credits remaining against a required 300,000.

The frozen plan contains **4,696 NCAAF price checkpoints and zero NFL checkpoints**, nominally 140,880 credits. Its requested timestamps span August 31, 2020–October 20, 2023: newer requested checkpoints already have successful cache indexes. The fresh index reconciliation removes one more request than the earlier progress-derived estimate.

At the saved 21:17:27 UTC checkpoint: **77 successful historical captures, zero failed requests, 4,619 remaining**, 2,310 known credits used, zero college-statistics calls. One separate quota-preflight response is not counted as a historical price capture. The current NFL Week 6 injury report was successfully downloaded at 21:15:39 UTC (28 HTML tables, 394,522 source bytes); publication-time and structured player validation remain pending.

S3 evidence: `shared/acquisition/paid/20261016T211526Z-92ef3be742/` contains the frozen plan, availability receipt and active progress. The final summary and unique return ZIP are expected only after the process ends. No completion is claimed yet.

- [Runtime test/heartbeat evidence](status/football39_runtime_log_evidence.json)
- [Verified S3 progress and availability receipt](status/football39_progress_20261016T2117Z.json)

## Verified progress update — 21:56 UTC

AWS re-described this job as InProgress at 2026-10-16T21:56:33Z with ProcessingStartTime 21:14:53.331 UTC. The saved 21:56:17 UTC progress has **1,822/4,696 historical price checkpoints captured, 2,874 remaining, zero failed requests**, and 54,660 known subscription credits used. No terminal outcome is claimed. [Saved progress](status/football39_progress_20261016T2156Z.json).

A separate user-authorized public NGS/availability job v040 has completed. It did not alter this job's scope, pacing, quota controls or execution. See [actual v040 results](NGS_AVAILABILITY_V040.md).

