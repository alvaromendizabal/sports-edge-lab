# Downloaded data and next acquisition priorities

**Latest update — October 16:** The selected historical football odds queue is finished: 4,696/4,696 requests, zero final failures and zero remaining. V042 refreshed current football data and resolved 692/692 current NGS joins. V045 repaired NFL snap identities to 7,445/7,463; 18 remain unresolved. College structural validation retains 2,402 rows, of which 2,306 have exact unique player IDs; 1 malformed rows are quarantined. All 692 current NGS rows already have exact week/team/GSIS matches. Original publication-time gaps remain explicit. [Verified readiness](FOOTBALL_READINESS_V042.md). ACB remains deleted and CBBD paused.


**93,319 in-scope raw content files / 17.26 GB are verified in the shared archive.**
The content-only S3 scan ran on **October 16, 20:36:28–20:37:35 UTC**, counting
**17,259,029,672 stored bytes**. It excludes receipts, indexes, code, return
bundles, derived tables, legacy duplicates and the entire unrelated ACB prefix.
There are zero unclassified raw objects. Collectors wrote during the paginated
scan, so this is an observation window rather than an atomic snapshot.

| Track | Stored content files | Stored GB |
| --- | ---: | ---: |
| NFL | 11,579 | 0.816 |
| NBA | 22,962 | 1.945 |
| NCAA football | 22,178 | 3.191 |
| NCAA men's basketball | 26,796 | 5.296 |
| NCAA women's basketball | 5,726 | 2.495 |
| Shared weather | 4,078 | 3.517 |

The previous 20:03 UTC report included 32 ACB content files / 394,736,881 bytes.
Its comparable in-scope baseline is 85,385 files / 16,846,793,927 bytes. Growth
since that corrected baseline is **7,934 files / 412,235,745 bytes**. Historical
mixed inventory receipts remain historical observations. ACB raw data, dedicated
receipts and collector were deleted on October 16; the removal is verified separately.

File counts are not unique games, complete seasons or training examples.
Different revisions and statistical families can overlap.

## Current NFL and availability additions

V045 repaired NFL snap identities to 7,445/7,463; 18 remain unresolved. College structural validation retains 2,402 rows, of which 2,306 have exact unique player IDs; 1 malformed rows are quarantined. All 692 current NGS rows already have exact week/team/GSIS matches. Original publication-time gaps remain explicit.

V041 saved 7,463 current-season snap rows, 15,327 weekly-roster rows and 659,277 depth-chart snapshot rows. V042 verified all 80 completed NFL schedule games have PBP, retained 14,031 PBP rows and captured 374 official Week 6 injury rows at 22:47:04 UTC. The fresh FBS schedule contained no additional completed game at 22:46:51 UTC; Friday games had not started. The public NGS archive contains 27,613 summary rows from 2016–2026, not raw trajectories.

See [V042 evidence](FOOTBALL_READINESS_V042.md), [quality repair](FOOTBALL_QUALITY_V045.md) and [weekend refresh playbook](FOOTBALL_WEEKEND_REFRESH_20261016.md). Existing historical inventory totals below retain their stated observation time.

## Fresh football data captured this turn

| Source | Verified content | Actual data recency |
| --- | --- | --- |
| NFL public play-by-play | 14,031 rows, 80 games; all 80 completed games in the current schedule have PBP; no unmatched game IDs | Game dates through October 15, 2026; downloaded at 20:34 UTC October 16 |
| Direct CFBD FBS plays and drives | 22,151 plays and 2,888 drives across 124 completed games in Weeks 5–7; every completed FBS schedule game in those windows has plays, drives, team/player box and advanced-stat rows | Latest covered kickoff October 16, 00:00 UTC, corresponding to Thursday evening in the US; downloaded 20:31–20:32 UTC |
| Current game markets | 24 NFL, 74 NCAAF and 46 NBA events with outcomes; 32 populated player-prop responses across these tracks | Fresh observation 20:22–20:23 UTC; provider quote times remain distinct |
| Big Ten football availability | 715 normalized player-status rows across 64 team-games; 154 rows across 14 team-games for October 16–17 | Public rendered archive observed October 16; source publication timestamps unavailable |
| NFL official roster/injury pages | All 32 team roster pages, plus Week 6 injury and schedule pages | All 32 roster pages retained; V040 extracted 358 Week 6 injury rows at 21:53 UTC; report-time and identity audit remain pending |

The CFBD job made 21 subscription-quota requests, with no failures, and also
captured current player usage and three weekly game-weather responses. The
current odds/statistics snapshot made 58 successful captures using 178 odds
credits and 12 statistics requests; five responses were empty. NCAA men's and
women's current odds remained empty. These counters represent subscription
allowances, not separately purchased API calls or dollar charges.

The Big Ten capture is a **rendered-page extraction**, not an original PDF or
an archive of verified publication-time versions. Four rows with ambiguous
missing columns were preserved in raw extraction and quarantined from the
normalized table. A missing game-day status stays null, never "available".
V042 resolved 2,306 exact college player-ID joins; V045 applies structural quarantine. Historical point-in-time eligibility remains unverified.
SEC now has a directly DOM-verified current rendered archive: 453 rows, 66 team-games and all 16 teams; 127 rows / 14 team-games for October 16–18. ACC has 801 rows, including 177 for this weekend. Original report PDFs, publication times and unresolved player identities remain gaps; the V045 quality table supersedes the preliminary ACC normalized count.

CFBD game-box endpoints also returned non-FBS games; they are retained in raw
responses but excluded from the 124-game FBS coverage denominator. Matching
game IDs proves game representation, not that every play or nested player
statistic is complete. Fresh postgame statistics are not pregame features for
their own games.

## What we still need, in priority order

1. **Prediction-time football tables:** reconcile team/player/game identities,
   validate every play schema, and join only prior-game performance to upcoming
   games. Build dated NFL/NCAAF evaluation sets before claiming a usable edge.
2. **Reliable current availability:** original NFL and NCAA report versions,
   publication timestamps, quarterback/depth-chart changes and cross-conference
   coverage. Big Ten, Big 12, ACC and SEC rendered archives are saved; historical publication times, identity mapping and other conferences remain open. Archive final game-day updates when published.
3. **Historical market validation:** the selected football game-price queue is complete. Audit bookmaker quote times and kickoff revisions before using those prices in backtests. Basketball historical queues are separate; CBBD remains paused.
4. **Tracking and aligned video for the five target sports:** vendor access,
   export scope, history/current latency and modeling rights are still
   unconfirmed. Previous SkillCorner/Genius inquiries are recorded; a search including spam found SkillCorner's automated no-B2C acknowledgment but no granted access. Genius has no substantive access reply yet. No new license was purchased. ACB is out of scope.
5. **Basketball-specific gaps:** complete CBBD plays/lineups/substitutions after
   the provider limit clears; current NBA injury versions; women's current
   schedules, availability and market coverage. Shooting's specified recovery
   plan is complete, not every possible historical query.
6. **Weather feature readiness:** extract venue values from archived forecast
   fields and verify historical availability times before using them in backtests.

We have substantial data for initial NFL/NCAAF baselines. Frontier modeling
still requires stronger identity, sequence, availability and temporal
validation; download volume alone does not establish frontier performance.

[Detailed execution and evidence](FOOTBALL_READINESS_20261016.md).

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



