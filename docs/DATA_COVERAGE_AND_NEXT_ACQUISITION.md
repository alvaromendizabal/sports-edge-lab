# Downloaded data and next acquisition priorities

## Latest measured content inventory

**85,417 raw content files / 17.24 GB are verified in the shared archive.**
The content-only S3 scan ran on **October 16, 20:02:52–20:03:45 UTC**.
It counted **17,241,530,808 stored bytes**, excluding receipts, request indexes,
source discovery, code, return bundles and duplicate legacy archives. All raw
objects were classified. Live collectors wrote during the paginated scan;
this is an observation window, not an atomic snapshot.

| Track | Stored content files | Stored content GB |
| --- | ---: | ---: |
| NFL | 11,564 | 0.808 |
| NBA | 20,688 | 1.936 |
| NCAA football | 20,914 | 3.165 |
| NCAA men's basketball | 22,572 | 5.139 |
| NCAA women's basketball | 5,726 | 2.495 |
| Shared weather and external tracking research | 3,953 | 3.699 |

The archive grew by **14,236 files / 2.85 GB** since the
19:24 UTC scan, and by **39,348 files / 4.82 GB** since the
18:10 UTC baseline. File counts are not unique games, API captures, complete
seasons or approved training rows; source families and revisions can overlap.
Stored bytes are separate from uncompressed response-byte counters.

[Exact inventory](status/content_inventory_20261016T2003Z.json) · [current data and source-time matrix](DATA_FRESHNESS_AND_ACCESS_20261016.md) · [tracking/video access](TRACKING_AND_VIDEO_ACCESS_20261016.md).

Current odds have populated NFL, NBA and NCAA football responses. NCAA men's
and women's current odds returned empty arrays at the 19:50 UTC observation.
The current men's schedule response has November games; that does not fill
women's statistics or availability gaps. An enabled six-hour schedule captures
future current vintages, while historical backfills remain separate.

The measured archive contains **5,326 public archive files**, **76,074 paid
payload files**, six provider canaries, **24 original NBA injury PDFs**, **34
original NFL pages**, **1,438 NWS JSON files**, **2,483 NOAA forecast fields**,
and **32 SkillCorner ACB research files**. The ACB sample covers ten historical
Spanish league games with original trajectories, provider event annotations
and identity metadata; it adds no NBA/NCAA tracking or raw video.

The NFL current capture now includes all **32 team rosters** plus Week 6 injury
and schedule pages, after a targeted two-roster recovery. Extraction and
publication-time validation remain pending. The broader historical gap run
continues. College shooting reached **958 positive responses / 71,593 summary
rows** before its runtime bound; a bounded replay is now active, reusing those
958 responses and adding two new captures in its first observed heartbeat.
The NOAA continuation also remains active at the recorded metadata check.


The original baseline and filename-year coverage below remain preserved as
dated observations; they are not the current storage total.

Verified against the canonical private S3 archive on **16 October 2026, 18:09–18:11 UTC**. Counts below exclude acquisition receipts, request indexes, audit files, return ZIPs, and the duplicate legacy NFL archive.

## Frozen starting inventory

**At the stated inventory timestamp, 46,069 raw content files occupy 12,423,339,059 bytes (12.42 GB)**. This comprises 5,307 public archive files (10.74 GB), 40,756 hash-addressed paid API payloads, and six provider canaries. File counts are not unique games, rows, or model-ready examples. Public files overlap across source families; paid bodies are deduplicated by content within their storage namespace.

| Track | Public archive files | Paid payload files | Canaries | Total stored bytes |
| --- | ---: | ---: | ---: | ---: |
| NFL | 815 | 8,654 | 1 | 790,993,575 |
| NBA | 2,909 | 9,309 | 1 | 1,901,669,120 |
| NCAA football | 668 | 12,050 | 1 | 3,056,998,619 |
| NCAA men's basketball | 466 | 9,169 | 2 | 4,186,861,010 |
| NCAA women's basketball | 449 | 1,574 | 1 | 2,486,816,735 |

The paid payloads include 36,248 odds bodies, 2,360 CollegeFootballData bodies, and 2,148 CollegeBasketballData bodies. The three initial paid jobs recorded **46,765 successful response captures** across **48,108 HTTP calls**. Response captures and content files differ because repeated responses can have identical bodies; neither is a count of independent games.

## Statistical coverage already acquired

Years in this table are **observed filename years**, not a certification that every season is nonempty, every game is present, or every column is valid. A forthcoming season can already have schedule or roster files. Full family-level counts and exact year tokens are in [the machine-readable family inventory](status/archive-family-coverage_20261016.json).

| Track | Main archived families and observed filename years |
| --- | --- |
| NFL | Play-by-play and rosters 1999–2026; weekly rosters 2002–2026; depth charts 2001–2026; injuries 2009–2026; snaps 2012–2026; participation 2016–2025; FTN charting 2022–2026; player/team statistics, schedules, NGS summaries, draft, combine, contracts and trades. |
| NBA | NBA Stats play-by-play, shots and game lineups 1997–2026; aggregate lineups 2008–2026; matchup tables 2018–2026; ESPN play-by-play/shots 2002–2026; boxes, rosters, usage/tracking summaries and identity crosswalks. Current injury/depth-chart snapshots carry 2027 filenames, not historical injury publication series. |
| NCAA football | ESPN play-by-play/drives/boxes/rosters 2004–2026; NCAA play-by-play and statistical files 2013–2026; cfbfastR play-by-play 2014–2026; recruiting 2002–2026 and portal summaries 2015–2026. Direct CFBD requests cover the planned 2000–2026 season range, subject to source availability. |
| NCAA men | NCAA play-by-play, possessions, lineups, matchup stints, rosters and boxes 2010–2026; NCAA shots 2019–2026. ESPN play-by-play/shot filenames include 2003 and 2006–2026; 2004–2005 are absent in those families. Direct CBBD historical pulls remain incomplete. |
| NCAA women | NCAA play-by-play, possessions, lineups, matchup stints, rosters and boxes 2010–2026; NCAA shots 2019–2026; ESPN play-by-play/shots/boxes 2004–2026. Certain other ESPN season-statistics families lack 2024–2025 files. Availability and paid coverage need their own audit. |

NFL's initial 815 files and the four-sport public batch's 4,492 files remain preserved. The public batch passed byte-integrity checks for every cataloged asset. It is a community-compiled statistical archive with explicit lineage, not independently collected original-source history. We independently own the acquisition and modeling code; upstream data rights and attribution remain intact.

## Where the first paid runs stopped

| Workstream | Final result | Remaining gap |
| --- | --- | --- |
| Historical game markets and college statistics | 33,279 captures: 27,923 odds + 2,693 CFBD + 2,663 CBBD. All 9,811 planned daily odds census requests processed. | Runtime bound reached. Only 18,263 of 63,686 initially planned event checkpoints processed; later event discoveries can change the denominator. CBBD daily play history remains incomplete. |
| Player props | 12,583 captured responses; 9,438 nonempty; 4,826,353 returned outcome entries across repeated markets and snapshots. | 500,000-credit bound reached after 499,930 known credits. 67,949 tasks remained pending in its last dynamic plan. NCAA women's props are not included. |
| CBBD shooting recovery | 903 captured responses; 965 HTTP calls including retries. | Runtime bound reached; 12 failed requests recorded. It recovered part of a 9,864-query initial plan, with older-season cached selectors still incomplete. |
| Direct ESPN collection | Zero captures. | Access was denied; collection stopped without bypass. This gap remains explicit. |

Initial paid usage was **1,337,530 known odds credits** and **6,371 college-statistics HTTP calls**, plus 120 odds credits conservatively reserved for unknown charges. The provider's last observed account-level odds header showed 1,337,680 used, including the earlier canary. These are historical run receipts, not a live quota promise.

The prop audit found 6,608 quote-update inconsistencies, 4,650 kickoff revisions, 1,228 missing-event responses and 51 responses that were not pregame relative to the returned kickoff. Categories can overlap. Only **1,737 responses** passed the initial nonempty timestamp checks; that is not full model-feature approval. Raw capture volume must not conceal this limitation.

## Data that matters next

| Priority | What to acquire or establish | Research enabled |
| --- | --- | --- |
| 1 | Resume missing game-price checkpoints, CBBD play history and high-value prop slices using verified caches; reconcile every odds event against canonical schedules and settlements. | Honest comparisons against prices available at the actual prediction time. |
| 2 | Original injury/availability reports with publication timestamps and revisions; preserve current captures as immutable vintages. | Expected minutes, snaps, usage and lineup distributions before a game. |
| 3 | Stable player/team/game identities and effective-dated roster, transfer and depth-chart changes. | Player-adjusted forecasts and longitudinal models without incorrect joins. |
| 4 | Original play/shot/lineup sequences where permitted, plus completeness and source-column audits of existing archives. | Independently engineered possession and play representations, rotation models and player interaction models. |
| 5 | Venue metadata and weather forecasts with issue time, valid time and horizon; separate actual weather from forecasts. | Weather-adjusted football forecasts without retrospective leakage. |
| 6 | Explicit NCAA women's schedule, player availability and odds coverage measurements. | A credible women's track whose evaluation matches the narrower market history. |

Downloading more data is one part of the research program. The next acceptance gates are source-level schemas, nonempty-season/game coverage, duplicate resolution, timestamp validity, and prediction-time joins. Only then can rolling out-of-time experiments compare calibrated baselines with richer sequence, player and market models. The repository does not yet claim frontier predictive performance or a demonstrated betting advantage.

## Execution evidence

All 14 earlier Processing executions are terminal: eight AWS `Completed`, six `Failed`. Completed denotes execution status, not complete data coverage. Their reported start/end intervals imply **$1.448240 for completed jobs and $0.040885 for failed jobs** at the recorded instance rates. Provisioning/shutdown outside those intervals, the temporary Studio backup app, storage, requests and subscriptions are excluded; this is not a billing statement.

See the [latest operational snapshot](status/operational-status_20261016T1810Z.json), [raw content inventory](status/raw_inventory_20261016.json), and [cumulative execution ledger](status/execution-ledger_20261016T1810Z.json). Later launches are recorded separately so this completed-run snapshot remains reproducible.

## Subsequent acquisition milestone

The starting content scan above remains frozen. A public refresh added 19 revisions while reusing 4,473 verified assets. New bounded work now adds missing game-price and player-prop checkpoints, college basketball plays/lineups/substitutions, official NBA injury PDFs, current NWS forecast vintages and an original NOAA historical forecast-field pilot. See the [dated runtime, quota and launch evidence](FRONTIER_ACQUISITION_20261016.md) for actual progress and failures, and the [frontier source priorities](FRONTIER_DATA_PRIORITIES_20261016.md) for public sources, unconfirmed tracking access and acceptance gates. These additions are not silently folded into the earlier byte or file counts.


