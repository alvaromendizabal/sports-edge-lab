# Weekend football refresh — October 17, 2026, 03 UTC

The existing v043 current collector completed at **03:07:50.939 UTC (October 16, 8:07:50 p.m. Pacific)**. This pass inspected and verified it; **no additional AWS job or paid-provider request was launched**.

## Verified acquisition

- **54/54 HTTP requests succeeded, zero failed requests**, with 32 runtime tests passing before runtime acquisition. One successful cache was reused. The selected requests finished; this is not a declaration that every football dataset or future game is complete.
- **46 odds requests used 181 existing subscription credits**, within the collector's 500-credit bound. The provider reported 2,074,175 credits remaining after capture.
- **Eight CFBD requests**, within the existing collector's separate 100-call bound; **zero CBBD**. These are not supplemental weekend calls: the supplemental ledger stays **0/160**, with zero supplemental odds credits.
- Saved 14 NFL and 22 NCAAF responses (14 odds plus eight CFBD for NCAAF). The pre-existing five-track collector also saved 14 NBA and two responses each for NCAAM/NCAAW. The four college-basketball responses were empty lists, not complete statistical coverage. No scope was added in this pass.
- Verified all **52 distinct raw object keys** exist (3,288,852 compressed bytes). The 54 receipts total 38,371,640 uncompressed response bytes; these are overlapping observations, not newly unique records.
- Exactly one return ZIP: **42,989 bytes**, SHA-256 `efa12d8f3738c92c9c2fb28090ab3cd4a4d48a9cfd0f6d65a8619b6ce4e07e2d`. CRC passed, its summary equals S3, and its failures list is empty. All 54 unique request receipts are HTTP 200. Independently verified the schedule and both weekly box payload hashes, byte sizes and row counts.

Job: `sports-edge-lab-current-1c6ad2e5-dcee-4b8e-859a-9c5aae2a43d9`. S3 run prefix: `shared/acquisition/current/20261017T030650Z-eabc362b3a/`. Existing bucket, role and one ml.m5.2xlarge were unchanged. No replacement or duplicate acquisition was started.

## What is still pending

The saved **03:07:15 UTC** schedule contains **888 FBS games** after filtering classifications; its full 3,679-row response is not an FBS-only denominator. Week 7 has 62 FBS games, **seven marked completed**, and both weekly team/player box responses cover those exact seven game IDs. The remaining 55 are future or not confirmed complete, not 55 failed downloads.

The source still marked **Memphis–Tulane, Washington–Purdue and App State–Coastal Carolina incomplete**, with null final scores. None appears in the seven saved weekly box responses. This describes that capture's state, not a live assertion that the games remain underway. Final Friday play/drive/game payloads remain pending confirmed provider publication; the fresh six-hour captures were reused instead of polling again.

All eight selected public NFL PBP/NGS/roster/snap/depth/player release assets remain hash/size-identical. No duplicate payloads were downloaded. Public NGS still consists of statistical summaries, not full tracking.

The directly rendered Big Ten archive at **03:47:02 UTC** contained **719 rows**, including **20 Friday rows**. The displayed date format changed; after date-only normalization the Friday hash equals the prior capture. **Zero status changes and zero final game-day statuses**. The missing-jersey quarantine is retained. This observation is after kickoff; unknown publication remains null and cannot be backdated. Other conference final versions and verified 2026 American football availability remain explicit gaps. No new NFL injury vintage was downloaded in this pass; v049 remains the latest saved injury observation.

Existing SkillCorner/Genius inquiry checks found no new substantive access response. No licenses, subscriptions, outreach or access changes occurred.

## Continuation

Reuse this successful current capture. Do not restart its exact job or any completed historical job. Keep the supplemental provider-stop ledger intact. Continue the existing weekend follow-up for newly confirmed games and actual changed availability; it is not yet the final Monday pass.

[Verification and source observations](status/football_weekend_20261017_03/verification.json) · [AWS terminal receipt](status/football_weekend_20261017_03/aws_terminal.json) · [Weekend playbook](FOOTBALL_WEEKEND_REFRESH_20261016.md)
