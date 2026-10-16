# Sports Edge Lab

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

**71,181 raw content files / 14.39 GB are verified in the shared archive.**
The corrected content-only S3 scan ran on **16 October 2026, 19:23:51–19:24:43
UTC (12:23–12:24 p.m. Pacific)**. It counted 14,393,519,871 stored bytes and
excluded request indexes, receipts, source listings, audit files, return
bundles and duplicate legacy data. All raw objects were classified.

| Track | Stored content files | Stored content GB |
| --- | ---: | ---: |
| NFL | 11,442 | 0.805 |
| NBA | 17,684 | 1.925 |
| NCAA football | 18,091 | 3.139 |
| NCAA men's basketball | 17,470 | 4.827 |
| NCAA women's basketball | 4,168 | 2.492 |
| Shared weather | 2,326 | 1.205 |

The archive contains **5,326 public archive files**, **63,499 paid payload
files**, six provider canaries, **24 original NBA injury PDFs**, **1,438 NWS
point/forecast JSON files**, and **888 original NOAA forecast fields**. Public
archives are community-compiled source assets with attribution; original
source captures retain their own provenance. Public source families and
revisions can overlap, and content-addressed responses can serve multiple
requests. File counts do not establish unique games, complete seasons or
approved training rows.

Compared with the earlier 18:10 UTC baseline, the measured archive grew by
**25,112 files / 1.97 GB**. Active collectors continued writing during this
52-second paginated scan, so it records an observation window rather than an
atomic snapshot. Subsequent API capture counters are reported separately.

The source program now spans historical odds and props, play-by-play,
possessions, shots, lineups, substitutions, rosters, schedules, availability
reports and weather. Coverage remains uneven. The 728 eligible cached football
venues have a current NWS forecast vintage; historical NOAA grids still need
venue extraction and publication-time checks. Full player/ball trajectories
and aligned video are not established by aggregate tracking summaries.

A one-time American Conference availability collector is **scheduled for
6:05 p.m. Pacific on October 16 / 01:05 UTC on October 17**. Its AWS preflight
passed 23 tests and correctly made zero source requests outside the permitted
visit window. Scheduled NCAA reports are not counted as downloaded data.

The college-shooting continuation was corrected when its first 300 HTTP
successes were empty. The final stopped-run audit counted **580 empty responses
and zero nonempty responses**; additional requests finished before the stop
settled. The corrected v024 run passed 34 AWS tests and its positive-data gates.
At **19:28:52 UTC**, it had acquired **30 nonempty shooting responses containing
2,384 observed records**, with zero empty responses or failures. These are
retrospective season-summary records, not individual shot trajectories.

At the **19:26–19:28 UTC** runtime check, the game/statistics continuation had
captured **17,362 responses** and the prop continuation **12,808 responses**;
both remained active. The NOAA season expansion had processed **164 of 440
forecast pairs**, downloaded **1.344 GB of source bodies**, and recorded zero
errors. Those live counters overlap the stored inventory and are not added to
its totals. [Expanded acquisition, failures and runtime evidence](docs/EXPANDED_DATA_COLLECTION_20261016.md).

- [Latest content inventory](docs/status/content_inventory_20261016T1924Z.json) · [inventory method and counting correction](docs/RAW_CONTENT_INVENTORY_20261016.md)
- [Data coverage and remaining gaps](docs/DATA_COVERAGE_AND_NEXT_ACQUISITION.md)
- [Frontier-relevant source priorities](docs/FRONTIER_DATA_PRIORITIES_20261016.md)
- [Earlier acquisition milestone](docs/FRONTIER_ACQUISITION_20261016.md)
- [Shared research protocol](docs/RESEARCH_PROTOCOL.md)
- [Deployed source versions and hashes](docs/EXECUTION_SOURCE_VERSIONS.md)
- [Verified one-repository consolidation](docs/CONSOLIDATION_20261016.md)
- [Machine-readable five-track configuration](config/tracks.json)

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



