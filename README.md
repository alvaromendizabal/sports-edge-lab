# Sports Edge Lab

**Latest update — October 16:** The selected historical football odds queue is finished: 4,696/4,696 requests, zero final failures and zero remaining. V042 refreshed current football data and resolved 692/692 current NGS joins. V045 repaired NFL snap identities to 7,445/7,463; 18 remain unresolved. College structural validation retains 2,402 rows, of which 2,306 have exact unique player IDs; 1 malformed rows are quarantined. All 692 current NGS rows already have exact week/team/GSIS matches. Original publication-time gaps remain explicit. [Verified readiness](docs/FOOTBALL_READINESS_V042.md). ACB remains deleted and CBBD paused.


**Five sports. One reproducible forecasting and market-research platform.**

Sports Edge Lab develops calibrated probabilistic forecasts and evaluates them against timestamped sportsbook prices. The engineering emphasizes source provenance, information available at decision time, transparent baselines, and genuinely out-of-time evaluation.

The project has **one repository, one SageMaker development space, and one private data lake**. Each sport has a focused internal research track; ingestion, identity resolution, temporal validation and market evaluation share common infrastructure.

## Research tracks

| Track | Primary research focus | Workspace |
| --- | --- | --- |
| NFL | Quarterback-adjusted team strength, EPA-based matchups, calibrated win probabilities, point margins and game totals. | [`tracks/nfl`](tracks/nfl/README.md) |
| NBA | Player-minute and usage distributions, rotation-aware game forecasts, pace, spreads and totals. | [`tracks/nba`](tracks/nba/README.md) |
| NCAA football | Opponent-adjusted play efficiency, quarterback and roster transitions, recruiting and schedule-aware margin forecasts. | [`tracks/ncaaf`](tracks/ncaaf/README.md) |
| NCAA men's basketball | Possession efficiency, tempo, player availability and calibrated game-margin distributions across regular-season and tournament play. | [`tracks/ncaam`](tracks/ncaam/README.md) |
| NCAA women's basketball | Player-adjusted team strength, possession efficiency, tempo and roster continuity with explicit separation between long statistical history and shorter odds history. | [`tracks/ncaaw`](tracks/ncaaw/README.md) |

## Current execution status

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

See [V042 evidence](docs/FOOTBALL_READINESS_V042.md), [quality repair](docs/FOOTBALL_QUALITY_V045.md) and [weekend refresh playbook](docs/FOOTBALL_WEEKEND_REFRESH_20261016.md). Existing historical inventory totals below retain their stated observation time.

## Fresh football data captured this turn

| Source | Verified content | Actual data recency |
| --- | --- | --- |
| NFL public play-by-play | 14,031 rows, 80 games; all 80 completed games in the current schedule have PBP; no unmatched game IDs | Game dates through October 15, 2026; downloaded at 20:34 UTC October 16 |
| Direct CFBD FBS plays and drives | 22,151 plays and 2,888 drives across 124 completed games in Weeks 5–7; every completed FBS schedule game in those windows has plays, drives, team/player box and advanced-stat rows | Latest covered kickoff October 16, 00:00 UTC, corresponding to Thursday evening in the US; downloaded 20:31–20:32 UTC |
| Current game markets | 24 NFL, 74 NCAAF and 46 NBA events with outcomes; 32 populated player-prop responses across these tracks | Fresh observation 20:22–20:23 UTC; provider quote times remain distinct |
| Big Ten football availability | 715 normalized player-status rows across 64 team-games; 154 rows across 14 team-games for October 16–17 | Public rendered archive observed October 16; source publication timestamps unavailable |
| NFL official roster/injury pages | All 32 team roster pages, plus Week 6 injury and schedule pages | All 32 roster pages retained; v040 extracted 358 Week 6 injury rows at 21:53 UTC; identity/publication-time audit remains pending |

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

## Continuations and completed backfills

- **Weather v030 completed:** all 440 planned forecast initialization/lead
  pairs for the selected 2024 football scope are processed; 1,037 new GRIB
  fields were downloaded. The final inventory has 2,640 forecast fields and
  1,438 NWS JSON objects. This is not all historical weather or a validated
  venue-level feature table.
- **Shooting v032 completed:** 336 new responses and 958 cache reuses processed
  all 1,294 planned queries. Across that plan, 1,256 responses had records,
  38 were empty and 88,554 summary rows were observed. Zero planned queries
  remain; those totals include reused data.
- **Historical v011 stopped:** AWS confirmed terminal Stopped with ProcessingEndTime October 16, 20:49:04 UTC after CBBD rate-limit responses. CBBD is not resumed.
- **Odds-only v037 failed before provider calls:** its worker lacked a management-plane permission; no paid requests occurred. V038 was prepared but superseded and never launched.
- **Football v039 completed:** 4,696/4,696 selected missing NCAAF historical game-price requests; zero final failures, zero remaining, 140,880 known subscription credits plus 60 unknown-charge reserve credits. AWS end time 22:47:02 UTC. The selected NFL gap queue was already zero. [Scope, receipts and terminal evidence](docs/FOOTBALL_FINISH_V039.md).
- **NGS/availability v040 finished:** all six selected tasks processed; three current public NGS assets total 27,613 rows from 2016–2026, including the available Week 6 records. Also extracted 358 official NFL injury rows and 434 Big 12 availability rows. ACC was raw-only in V040; V041 verified the headers and normalized 801 rows. SEC was later verified separately against all 453 rendered rows. Zero paid API credits. [Terminal evidence and limitations](docs/NGS_AVAILABILITY_V040.md).

The v039 monitor is retired after the verified terminal outcome. The finite supplemental weekend follow-up acquires newly published NFL/NCAAF data only; it does not restart historical jobs.

The existing six-hour current snapshot schedule remains configured, with its
first scheduled execution at **October 17, 03:05 UTC (8:05 p.m. Pacific today)**.
It refreshes current odds/stats; it does not continuously refresh every raw
football play or conference report. The American Conference availability
one-off remains scheduled for **October 17, 01:05 UTC (6:05 p.m. Pacific)**;
future captures are not counted as downloaded. The six-hour schedule now targets tested v043 with CBBD disabled; its frequency, budgets and end date are unchanged. A supplemental finite weekend follow-up handles changed public football assets, new completed games and final availability reports. No new subscription was purchased.

The next priorities are validated NFL/NCAAF prediction tables, broader current
availability, historical quote-time auditing, and licensed in-scope tracking/video.
See [the current football readiness and gap report](docs/FOOTBALL_READINESS_20261016.md),
[data coverage](docs/DATA_COVERAGE_AND_NEXT_ACQUISITION.md), and
[source identities](docs/EXECUTION_SOURCE_VERSIONS.md).

## AWS workspace

| Resource | Canonical configuration |
| --- | --- |
| Region | `us-west-2` |
| SageMaker Studio space | `sports-edge-lab-dev` |
| Development instance | `ml.m7i.2xlarge` — 8 vCPUs, 32 GiB RAM |
| Development storage | 150 GiB EBS |
| Idle shutdown | 60 minutes |
| Private data lake | `s3://sagemaker-sports-edge-lab-560403859723-us-west-2/` |
| Sport archives | `tracks/{nfl,nba,ncaaf,ncaam,ncaaw}/` |
| Shared acquisition receipts | `shared/acquisition/` |

The space configuration is verified. Creating a space does not imply a running notebook application. Bounded SageMaker Processing jobs perform unattended acquisition. Compute costs for running jobs are tracked separately from subscription, storage and request costs.

[Open SageMaker Studio](https://0nrayepa6pujaiu.studio.us-west-2.sagemaker.aws/jupyterlab/default)

## Acquisition engineering

The shared [paid-data runner](tools/acquire_paid_data.py) resolves credentials only inside AWS from encrypted SSM parameters. It archives immutable, hashed raw responses and sanitized receipts; enforces shared provider budgets; emits heartbeats; and reuses completed historical requests after verifying the stored response hash. One compact return ZIP is generated per execution.

The [migration utility](tools/consolidate_archive.py) records the completed one-time consolidation: it copied previous archives and verified object size, metadata and content before recording success. Its source buckets have since been retired, so it is retained for historical reproducibility, not as a routine acquisition command. The original NFL acquisition and planning scripts remain available as historical implementations; their older default paths should not be used for new multi-sport runs.

Offline verification:

```bash
python tools/acquire_public_archives.py --self-test
python tools/acquire_espn.py --self-test
python tools/acquire_paid_data.py --self-test
python tools/acquire_player_props.py --self-test
python -m unittest discover -s tools -p 'test_paid_acquisition.py' -v
```

Operational acquisition runs use explicit runtime and provider budgets. The initial paid milestone permits at most 1,000,000 odds credits and 15,000 combined college-statistics calls, with a 7,200-second Processing-job runtime ceiling. The separate player-prop runner is capped at an additional 500,000 odds credits and uses event IDs already discovered by the base runner. A budget ceiling is not a claim that this allowance has already been consumed.

The [public archive runner](tools/acquire_public_archives.py) discovers actual SportsDataverse release assets for the four additional sports and preserves upstream lineage. The [direct ESPN collector](tools/acquire_espn.py) captures original responses separately. Community-compiled archives and direct original-source captures remain distinguishable in storage and provenance.

## Evaluation standard

1. Preserve raw source responses, hashes, request parameters and retrieval times.
2. Audit source, season, team, player, game and market coverage.
3. Build as-of features using only information available before each prediction.
4. Compare sport-only and market-aware models with transparent baselines.
5. Validate by rolling season and week, with training-only calibration.
6. Report probability quality, price availability and uncertainty before making market-performance claims.

Win prediction, spread/total distributions and market value are separate questions. Reference closing lines cannot represent prices available days earlier; realized weather cannot represent a pregame forecast; postgame player minutes cannot represent expected minutes.

## Repository and data boundaries

Code, configuration, tests, source catalogs and non-sensitive reports belong here. Raw data, API keys, private receipts containing licensed records and large model artifacts remain outside Git. Upstream attribution and usage conditions travel with each source. The project does not claim a demonstrated betting edge, complete player-prop coverage or a production forecasting system at this acquisition stage.

