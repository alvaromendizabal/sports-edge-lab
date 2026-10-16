# Sports Edge Lab

**Latest update:** v011 is terminal. The user-authorized continuous football completion job v039 has launched; the short v038 restart is superseded. [Scope, safeguards and runtime evidence](docs/FOOTBALL_FINISH_V039.md). ACB remains deleted.


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

## Fresh football data captured this turn

| Source | Verified content | Actual data recency |
| --- | --- | --- |
| NFL public play-by-play | 14,031 rows, 80 games; all 80 completed games in the current schedule have PBP; no unmatched game IDs | Game dates through October 15, 2026; downloaded at 20:34 UTC October 16 |
| Direct CFBD FBS plays and drives | 22,151 plays and 2,888 drives across 124 completed games in Weeks 5–7; every completed FBS schedule game in those windows has plays, drives, team/player box and advanced-stat rows | Latest covered kickoff October 16, 00:00 UTC, corresponding to Thursday evening in the US; downloaded 20:31–20:32 UTC |
| Current game markets | 24 NFL, 74 NCAAF and 46 NBA events with outcomes; 32 populated player-prop responses across these tracks | Fresh observation 20:22–20:23 UTC; provider quote times remain distinct |
| Big Ten football availability | 715 normalized player-status rows across 64 team-games; 154 rows across 14 team-games for October 16–17 | Public rendered archive observed October 16; source publication timestamps unavailable |
| NFL official roster/injury pages | All 32 team roster pages, plus Week 6 injury and schedule pages | Earlier same-day capture; structured extraction and report-time audit remain pending |

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
Player identity joins and historical point-in-time eligibility remain unverified.
SEC discovery did not yield downloadable report links; it is still a gap.

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
- **Historical v011 stop requested after repeated CBBD HTTP 429:** AWS still reported Stopping at 20:44 UTC. At the preserved
  20:35:20 UTC checkpoint it had 37,443 captures, 70 final request failures and
  351 retry incidents. The checkpoint is not a final stop-time count. Existing
  successful payloads and indexes remain available.
- **Odds-only v037 failed before provider calls:** its worker role lacks
  SageMaker DescribeProcessingJob permission. Zero API requests/credits were
  consumed, and its return ZIP was saved. V038 removes this worker-side
  management API call and instead requires an embedded control-plane receipt
  proving v011 has terminated. V038 is prepared, not launched while v011 is
  still Stopping. Its limits are no college-statistics requests, one source
  request per second, 200,000-credit ceiling, 30-minute application limit and
  35-minute AWS limit. It requires v011 to be terminal, checks the live quota
  reserve and stops its provider on 401/402/403/429. Its budget fits within the
  unused v011 odds ceiling. No resumed historical acquisition is claimed until a successful runtime
  receipt exists.

A bounded follow-up is enabled for **2, 3 and 4 p.m. Pacific today** to verify
AWS termination and launch at most one v038 odds-only job, then check its
result. It does not restart CBBD. This is a scheduled follow-up, not a claim
that the historical restart is already running.

The existing six-hour current snapshot schedule remains configured, with its
first scheduled execution at **October 17, 03:05 UTC (8:05 p.m. Pacific today)**.
It refreshes current odds/stats; it does not continuously refresh every raw
football play or conference report. The American Conference availability
one-off remains scheduled for **October 17, 01:05 UTC (6:05 p.m. Pacific)**;
future captures are not counted as downloaded. This turn did not change either
schedule or create a new data subscription.

The next priorities are validated NFL/NCAAF prediction tables, broader current
availability, missing historical prices, and licensed in-scope tracking/video.
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




