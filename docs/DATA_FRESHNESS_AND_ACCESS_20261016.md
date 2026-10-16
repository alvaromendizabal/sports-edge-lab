# Data freshness and tracking access — 16 October 2026

A new download timestamp does not make a historical observation current. This
report keeps three clocks separate: when Sports Edge Lab captured a response,
when the source published or updated it, and when the underlying game, report,
or forecast is valid. An S3 modification timestamp is storage evidence only.

## Latest current-provider snapshot

The v026 AWS run passed 30 tests, then captured **58 responses** from
**19:50:43–19:51:39 UTC** on October 16: 53 nonempty responses and five empty
arrays, with zero request failures. Usage was **176 odds credits and 12 college
statistics calls**. The lease was released with its matching ETag. The
[aggregate freshness summary](status/current26_freshness_summary_20261016.json)
contains no raw prices, player records or event identities.

| Current track | Games with moneyline/spread/total outcomes | Of those, upcoming within seven days | Prop responses with outcomes / captured | Actual event-time range in game-odds response (UTC) |
| --- | ---: | ---: | ---: | --- |
| NFL | 24 | 14 | 12 / 12 | October 18, 13:30 – October 25, 20:25 |
| NBA | 46 | 16 | 8 / 12 | October 20, 19:00 – December 26, 03:30 |
| NCAA football | 73 | 59 | 11 / 12 | October 16, 23:30 – October 25, 02:00 |
| NCAA men | 0 | 0 | No eligible events returned | Empty current odds and event arrays |
| NCAA women | 0 | 0 | Not included in prop scope | Empty current odds and event arrays |

The table describes the returned snapshot, not permanent market coverage. The
36 prop responses include five event objects with no offered outcomes; those
are not called populated prop markets. The 143 game-market events and 31
populated prop responses overlap and must not be added as unique games.
Across priced game and prop responses, observed quote-update times ranged from
**19:46:28 to 19:50:59 UTC**. Their audit recorded zero missing update times and
zero quote updates after retrieval. This checks recorded timestamps, not
bookmaker executability, independent accuracy or feature approval.

Current CFBD returned **3,679 game rows**, including 1,937 with a true completion
flag and 1,738 scheduled after retrieval. Their game dates range from August 27
to December 12, 2026. The response also included 31,479 roster rows, 8,655 team
season-stat rows, 134,672 player season-stat rows, 138 advanced team rows and
seven current-week box-score rows in each of two endpoints. These are endpoint
row counts, not unique players or independent examples. The newest completed
game or statistics publication time was not established by this summary.

Current CBBD returned 365 team rows and three upcoming-schedule slices with
**0, 701 and 634 rows**. The nonempty slices contain game dates from November 1
to November 29, 2026. Slice boundaries can overlap, so 1,335 returned rows are
not asserted to be 1,335 distinct games. Its statistical feed covers the men's
track; it does not establish current NCAA women's statistics coverage.

## Freshness matrix

| Source family | Latest verified retrieval evidence | Actual event/report/valid time established | Gap or boundary |
| --- | --- | --- | --- |
| Current odds and limited props | October 16, 19:50:43–19:51:06 UTC | Returned game dates and quote times above | College men's/women's current odds empty at this observation; limited prop sample |
| Current CFBD/CBBD | October 16, 19:51:06–19:51:39 UTC | Actual CFBD and CBBD game-date ranges above | Latest stats publication and newest completed-game time not verified |
| Historical odds/props and shooting | Historical continuations have separately timestamped progress/final receipts | Historical request windows and retrospective season summaries | A new retrieval does not make old observations current |
| Original NFL pages | October 16, 19:48:33–19:59:23 UTC, including targeted resume | Validated 2026 Week 6 injury/schedule titles and 2026 roster titles | 34 pages: injury + schedule + all 32 rosters; report publication/player tables not yet extracted |
| Public statistical archives | Delta finished October 16, 18:15:58 UTC | Filename-year observations retained in the coverage report | Latest actual game inside every file not audited; upstream revisions can overlap |
| Original NBA availability | Batch finished October 16, 18:42:51 UTC | Sparse URL dates through April 25, 2026 | 24 PDFs; PDF-internal publication extraction pending; no current complete feed |
| American Conference availability | Scheduled for October 17, 01:05 UTC | No acquisition from the future run yet | Scheduled images are not downloaded data |
| NWS hourly forecasts | All 728 selected venues captured by October 16, 18:54:32 UTC | Issue/update and valid-hour fields preserved in raw responses | Newest valid-hour range not aggregated here; roof/location joins pending |
| NOAA original forecast grids | v020 finished October 16, 19:35:07 UTC; v030 resume separately launched | Selected 2024-season initialization/lead/valid-hour coordinates | Initialization and storage timestamps do not prove historical release time; venue extraction pending |
| SkillCorner ACB research tracking | AWS capture October 16, 19:52:58–19:54:51 UTC; 32 raw files / 394,736,881 bytes | Ten Liga ACB games, October 11, 2025 – May 29, 2026 | External research sample; no NBA/NCAA or raw-video coverage |
| Commercial league-wide tracking/video | SkillCorner inquiry and Genius Sports form submitted October 16 | No delivered licensed dataset | Provider response, scope, price and rights remain pending |

Capture, source publication/update, and game/report/forecast-valid time are
separate clocks. Where a report does not expose an inspected payload maximum,
the newest actual game/report time remains **not verified**. A requested season
or filename year alone is not proof of current data or complete coverage.

## Original-source and research boundaries

The NFL runs now store 34 report/roster/schedule HTML data pages: Week 6 injury
and schedule pages plus all 32 team rosters. V031 passed 17 AWS tests, verified
30 prior roster bodies and recovered two missing observed links at19:59 UTC
with zero errors. Original capture times remain unchanged for reused pages. Team
directories, profile discovery pages, robots files and other discovery evidence
are stored separately. Counts of HTML pages are not player records.

The completed SkillCorner ACB sample contains ten original compressed trajectory
files, 21 game/event/catalog JSON files and one identity CSV, totaling 32 raw
files and 394,736,881 stored bytes. Its acquisition passed 16 AWS tests and
reported zero errors or remaining assets. It separates trajectory files, game metadata
and provider-generated event annotations, and identity aliases. Source README,
license, data dictionaries and retrieval receipts are preserved as evidence and
excluded from raw-content totals. This source supplies a limited external
basketball research sample; it does not establish access to NBA or NCAA
trajectories, full seasons, or raw video. Usage follows the observed source
license and any provider restrictions documented in its acquisition record.

Access outreach, a provider reply, an enabled API account and an acquired
tracking dataset are different statuses. Paid or commercial tracking remains
unacquired until delivery and permitted scope are verified. No requested access
is reported as data already held.

## Historical continuation results

The v014 historical prop continuation reached its 500,000-credit bound after
**499,840 known credits**, storing 16,296 successful response captures and
recording 2,057 failed requests. Its final dynamic plan retained 51,624 pending
requests. Quote/kickoff temporal issues remain explicitly audited; successful
HTTP retrieval does not approve the data for historical features.

The corrected v024 shooting run stopped at its runtime bound at **20:01:52 UTC**
with **958 positive nonempty responses / 71,593 observed summary rows**, zero
empty responses and zero failed requests. It made 962 statistics calls,
including four retry incidents, and retained 336 of its 1,294 planned requests.
These are retrospective team/player season-shooting summaries, not per-shot
trajectories or coordinates. The original stopped v021 audit still records
580 empty responses after the initial 300-response detection checkpoint.

The broader v011 gap run had **26,730 captured responses at 19:59 UTC**,
including college play/lineup/substitution responses and historical odds. These
run counters overlap the raw-content inventory and must not be added to it.
[Continuation evidence](status/live_progress_20261016T1959Z.json),
[final shooting report](status/shooting24_final_20261016.json) and
[final prop report](status/props_final_20261016.json) retain the distinct bounds.

The v032 replay uses the unchanged v024 artifact with a smaller envelope:
500 statistics calls, 1,200 application seconds and 1,500 AWS seconds. All
34 AWS tests passed at 20:05:55 UTC. Its 20:06:26 heartbeat verified 958 reused
responses and **two new captures**, with 334 requests still pending and zero
unsuccessful responses. The 960 nonempty response observations and 71,737 rows
in that heartbeat include reused data. They are not 960 new downloads.
[Replay evidence](status/shooting32_tests_and_progress_20261016.json).

The NOAA v030 resume reuses the exact v020 artifact and verified caches under
another 2 GB source-byte bound. Its progress remains separate from the 20:03
storage inventory. Source grids still need venue extraction and historical
publication-time checks. No further inventory refresh is implied by later
runtime heartbeats.

## Automatic refresh and acquisition limits

A recurring current-data schedule was created and read back as **ENABLED** at
19:53:27 UTC. It runs at 03:05, 09:05, 15:05 and 21:05 UTC, starting **October
17 at 03:05 UTC (October 16 at 8:05 p.m. Pacific)**, and expires November 16.
Its 120 possible runs are limited to 500 odds credits, 100 statistics calls and
900 AWS runtime seconds each: at most 60,000 scheduled odds credits and 12,000
statistics calls across the configured month. These are ceilings, not usage.
The manual snapshot consumed 176 credits and 12 statistics calls separately.

The exact artifact, input, lease and quota-reserve controls are recorded in
[the verified schedule](status/current_schedule_verified_20261016.json) and
[deployment configuration](../infrastructure/current_snapshot_schedule/RECURRING_PLAN.md).
Creation does not prove the first future scheduled invocation has run.
The separate American Conference availability capture remains scheduled at
01:05 UTC on October 17, within its permitted source window.

## Next acceptance checks

- Audit event/report/forecast time ranges inside the actual payloads, with
  empty partitions and lag explicit by sport and source.
- Join teams, players, games and reports using stable identities; retain
  ambiguity and unavailable matches rather than forcing joins.
- Keep source publication and quote timestamps separate from retrieval time;
  approve features only when information availability is established.
- Validate trajectories and event synchronization before using the tracking
  sample for sequence or interaction research.

The acquisition program supports more advanced models, but data volume and
source recency do not establish predictive performance. The evaluation remains
chronological, calibrated and compared with statistical and market baselines.
