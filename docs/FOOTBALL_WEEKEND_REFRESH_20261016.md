# Football weekend refresh — October 16–19, 2026

The authorized target is newly published NFL/NCAAF game data and final availability versions for this weekend. The selected historical odds queue is finished. No new historical odds expansion, ACB, CBBD, subscription purchase, outreach or IAM change is authorized by this refresh.

## Current baseline

- V039 completed all 4,696 selected missing NCAAF price checkpoints with zero failed requests. Do not restart it or launch superseded v038.
- V042 checked the schedule at October 16, 22:46–22:47 UTC: all 80 completed NFL games had PBP; no additional NCAAF game had finished since the previous capture. Friday Memphis–Tulane starts at 23:30 UTC; App State–Coastal Carolina and Washington–Purdue at 00:00 UTC October 17. Future games are not downloaded completed-game data.
- The three public NGS assets contain statistical summaries, not full tracking. Recheck release metadata and reuse unchanged hashes. V042 resolved all 692 current NGS rows against team/week/GSIS IDs.
- Read `FOOTBALL_READINESS_V042.md` and `FOOTBALL_QUALITY_V045.md` plus their actual S3 receipts for the latest identity/availability inputs. V045 supersedes structurally invalid availability rows; never silently restore a quarantined row.

## Capture windows and limits

The enabled supplemental follow-up checks for changes hourly during 06:15–22:15 Pacific through Monday October 19 at 06:15 Pacific, starting Friday at 16:15. Notify only meaningful new captures, completed validations or concrete blockers. These are observation opportunities; no guarantee is made that every provider publishes a final report at those times. Prioritize official pregame reports for games starting in the next two hours and persist postgame completions once published. Stop the supplemental follow-up after the final Monday result or an unrecoverable access blocker.

The existing six-hour AWS schedule remains the sole scheduled current odds collector. Its v043 target permanently disables CBBD until separate authorization and provider clearance. It retains the existing 500 odds-credit and 100 statistics-call bounds per run and ends November 16. The American Conference one-off at October 17, 01:05 UTC remains unchanged; inspect its outcome and reuse its captures.

Supplemental weekend runs have zero odds credits, zero CBBD calls, at most 16 CFBD requests per pass and at most 160 CFBD requests across this supplemental weekend series. Count all attempts, including errors, in durable receipts before another request; fail closed if cumulative usage cannot be established. At most one request per second per source, with longer robots/provider intervals honored. A 401/402/403/429 stops that provider across subsequent weekend passes; do not retry it simply because another scheduled pass started. No short application timer is added: each run terminates when its finite changed/new queue is done or a provider/budget stop occurs.

## Each pass

1. Read the current repository head, this playbook and latest actual evidence. Use AWS to inspect current scheduled/processing runs and S3 reports; if a relevant collector is active, inspect rather than overlap it. Preserve previous captures and outcomes. Never relaunch a completed job, v039/v038, or a failed provider request automatically.
2. Read official nflverse release metadata for current 2026 PBP, NGS, rosters, snaps, depth charts and players. Compare exact SHA-256/size to existing receipts. Download changed assets only, keeping immutable raw versions. Do not redownload unchanged historical seasons.
3. Compare a fresh CFBD FBS schedule to saved completed-game IDs and game state. Reuse the existing six-hour schedule capture when sufficiently fresh. Request plays, drives and team/player/advanced boxes only for newly completed or actually revised relevant current-week game windows. Reconcile returned game IDs to the FBS denominator; request completion is not schema completeness.
4. Preserve current official NFL injury/inactive/roster evidence and Big Ten, Big 12, ACC, SEC and American availability reports as actual observed vintages. Use published official links and obey robots/rate policies. Direct rendered tables must have counted rows and a canonical DOM/table hash; never trust a browser-agent narrative total. Original reports are preferable when available. Store rejected/ambiguous rows separately and retain null statuses.
5. Reuse tested v042/v045 identity and timestamp gates. Require unique exact IDs and correct team/week membership; do not guess fuzzy names. Distinguish source publication, observation, event kickoff, bookmaker update and prediction times. Original publication remains null when unverified. A current archive cannot establish a historical pregame feature. Postgame outcomes cannot describe their own game's pregame availability.
6. Build one self-contained PYZ for a concrete finite acquisition/validation queue. Run its entire offline suite before AWS credentials or provider network; hash it, upload it to the existing bucket, then verify the upload. Use only the existing role and 1 x ml.m5.2xlarge configuration. Use a deterministic date/hour job name and check exact prior existence before any CreateProcessingJob. Runtime tests precede secrets/network. Preserve successful-cache reuse, source-denial stops, heartbeat receipts and one unique return ZIP.
7. Verify AWS ProcessingEndTime, actual saved reports, counters, failed versus successful requests and ZIP integrity. Publish sanitized evidence through a non-forced expected-head commit. Do not commit private raw payloads, credentials or mailbox contents. Mark incomplete coverage explicitly and keep a durable supplemental CFBD call ledger.

Canonical bucket: `sagemaker-sports-edge-lab-560403859723-us-west-2`, region `us-west-2`; role: `SportsEdgeLabProcessingRole`. Source code and prior tests are in `tools/football_readiness_v042/`, `tools/football_quality_v045/`, `tools/football_refresh_v041/`, and `tools/current_snapshot_v043/`.

## Tracking access

Check only the existing SkillCorner/Genius inquiry threads for a substantive new entitlement or access offer. SkillCorner's automated response says it does not sell B2C; it is not a granted trial. Genius has no confirmed access yet. Do not resend outreach, accept a paid license, or download restricted video. If access is granted, verify allowed leagues/seasons, actual endpoints, player/ball fields, aligned-video delivery and modeling/betting/display permissions before using it. Record a concrete business-eligibility or contractual action for the user when one is actually required.

## Activation evidence

The finite schedule is enabled, with 42 hourly observation opportunities from Friday October 16 at 16:15 Pacific through Monday October 19 at 06:15 Pacific. [Schedule receipt](status/football_weekend_20261016/schedule.json). The S3 control ledger was created with `IfNoneMatch` and read back at 23:07 UTC: zero supplemental calls charged/reserved, CFBD total ceiling 160, zero odds credits and CBBD disabled. Future passes must update it conditionally using ETags; no reset is permitted. The completed v039 monitor was disabled after its terminal evidence commit.
