# Frontier-relevant acquisition milestone — 16 October 2026

The frozen content inventory remains **46,069 files / 12,423,339,059 bytes**, measured at 18:09–18:11 UTC. The results below are later acquisitions and must not be added to that byte total: API response bytes are uncompressed and repeated bodies may deduplicate in storage. Counts are not unique games, player observations or approved features.

## Verified additions and running work

At the **18:56:05 UTC** check, the continuing game/statistics collector had captured **8,984 additional responses**: 7,328 game-market snapshots and 1,656 college basketball responses. Zero failures were recorded in that collector. Its remaining request plan is still larger than this execution's runtime and credit allowance.

The new player-prop continuation had captured **3,735 additional responses** across NFL, NBA, NCAA football and NCAA men. It starts from successful request and historical 404 caches; it makes no paid event-discovery requests. Its quote audit separates response-wide defects from individual market/outcome defects, preserving usable candidate quotes alongside explicit rejection reasons. At the latest snapshot it also recorded 602 failed requests; a separately inspected sample containing one per sport returned event-missing HTTP 404s. This sample does not classify every failure. Candidate outcomes passing structural and recorded-time checks are repeated quote entries, not independent bets, and **no feature is approved** by this audit. Player identities, actual kickoff provenance, settlement and genuine historical availability still require validation.

The official NBA availability collector completed its discovered set: **23 new original PDFs plus one reused PDF**, from 24 observed URLs across 2019–2026. This is a sparse historical sample. AWS received HTTP 403 from the official landing-page host and suspended that host. The separately allowed NBA static host supplied the already-discovered PDFs. No blocked-host retry or synthetic filename enumeration occurred; historical completeness remains false.

The NWS continuation completed the **609 remaining eligible venues**, preserving the original 119 successful forecasts. The selected CFBD venue inventory now has forecasts for **728 of 728 eligible venues**, with 1,201 new responses, 17 reused responses and zero errors in the continuation. The list includes non-FBS venues and is not a count of upcoming games. Current forecast vintages cannot substitute for historical forecasts.

[Latest runtime receipt](status/frontier_runtime_20261016T1856Z.json) · [NBA completion and earlier quote audit](status/frontier_runtime_20261016T1846Z.json) · [initial launches and AWS test evidence](status/frontier_launches_initial_20261016.json).

The corrected NOAA HRRR pilot completed its selected data scope: **108 original GRIB fields / 133,123,035 bytes**, with all **18 forecast-cycle/lead pairs** complete and zero errors. These are six field records across five variable families per forecast pair; the two precipitation accumulation intervals remain separate. The shared CONUS grid forecasts correspond to 253 selected historical game records, **not 253 separate forecast files or validated venue-point series**. Twenty-nine verified listing/index records were reused. Grid decoding, venue extraction and historical public-availability checks remain outstanding; `point_in_time_approved` is false.

At the **18:56:49 UTC AWS check**, NBA availability and NWS continuation were Completed; game/statistics and player props remained InProgress. NOAA v019 had completed its application data report but AWS still reported InProgress while finalizing. V018 is recorded as Failed. [Final job-status supplement](status/frontier_job_status_20261016T1856Z.json) · [AWS NOAA/weather test and completion logs](status/final_noaa_weather_logs_20261016.json).

## Execution bounds

| Workstream | Scope | Maximum allowance |
| --- | --- | --- |
| Existing game/statistics continuation v011 | Five-sport historical game markets and missing CBBD plays, lineups and substitutions | 1,600,000 additional odds credits; 30,000 statistics calls; 14,400 Processing seconds |
| Player-prop continuation v014 | Six documented markets per supported sport; 24-hour, 6-hour and 15-minute checkpoints; no NCAA women's props | 500,000 additional odds credits; 7,200 Processing seconds |
| NWS continuation v015 | Current hourly forecasts for the uncollected cached venues | 1,500 requests; 1,200 application seconds; 1,500 Processing seconds |
| NBA availability v016 | Published and observed NBA PDF links | 300 requests; 250 reports; 600 application seconds; 720 Processing seconds |
| Original NOAA HRRR v019 | Bounded 2024-10-12 original forecast-field pilot | 250 MB response bodies; 500 requests; 600 application seconds; 900 Processing seconds |

The prior v017 NOAA launch failed before source HTTP requests because the historical CFBD cache descriptor used a current-data vintage. The exact failed source is retained. V018 fixed the cache identity but then captured only 29 listing/index records and rejected all 18 forecast pairs because its parser expected one precipitation accumulation period. V019 preserves both precipitation intervals separately, embeds an actual NOAA index fixture, and adds regression guards. The historical CFBD payload is reused without another paid call. See [source versions](EXECUTION_SOURCE_VERSIONS.md) and [the frontier source inventory](FRONTIER_DATA_PRIORITIES_20261016.md) for the correction and forecast interpretation.

The paid launch gate observed enough remaining account quota to cover both active jobs' maximum outstanding credit reservations, with **1,562,380 credits remaining after those reservations** at its observation time. This is a dated gate, not a promise about current quota. [Quota evidence](status/odds_quota_gate_20261016T1837Z.json).

At the recorded $0.461 per hour Processing rate, the four new corrected collectors' maximum configured intervals total approximately **$1.3215**. The failed v017 reported interval adds approximately $0.0069; v018 execution is recorded in the later job-status supplement. The previously running v011 interval is separate. The [18:45 cumulative ledger](status/execution-ledger_20261016T1845Z.json) is preserved as a dated snapshot and predates v018/v019; use the later launch and status supplements for those executions. These estimates exclude unreported provisioning/shutdown, S3 storage and requests, transfer, subscriptions and API credits; they are not billing caps.

## Acceptance remains separate from collection

The source program prioritizes measured odds/prop gaps, original availability vintages, original operational forecast fields and women's coverage. Full player/ball trajectories, body pose and aligned video are not established by the existing aggregate tracking tables. The [primary-source priority inventory](FRONTIER_DATA_PRIORITIES_20261016.md) distinguishes public/paid access already working from unconfirmed provider entitlements.

The project must pass schema, identity, completeness, temporal and settlement checks before any model claims. Planned research includes joint score distributions, player usage and availability distributions, and play/possession sequence models, compared using frozen chronological splits against calibrated statistical and market baselines. The acquisition volume does not establish frontier predictive performance.
