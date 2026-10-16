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

Fresh current odds and statistics were captured at **19:50–19:51 UTC**. The
58-response run returned game markets for **24 NFL, 46 NBA and 73 NCAA football
events**, plus 31 populated prop responses across those tracks. NCAA men's and
women's current odds were empty at this observation. Fresh CFBD season data and
CBBD November schedules are stored; actual returned dates and empty partitions
are recorded in the [freshness report](docs/DATA_FRESHNESS_AND_ACCESS_20261016.md).

A verified recurring schedule now refreshes current data **every six hours**,
starting **tonight at 8:05 p.m. Pacific / October 17, 03:05 UTC**. Its fixed
one-month ceiling is 60,000 odds credits and 12,000 statistics calls, with
per-run bounds, quota reserve and overlap prevention. This is an enabled
schedule; the first future scheduled execution has not yet run.

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


Nonbinding tracking/video access inquiries were sent to **SkillCorner and
Genius Sports**. Neither request establishes a paid license or delivered
commercial feed. League-wide NFL/NBA/NCAA trajectories and aligned video remain
access gaps. The [access record](docs/TRACKING_AND_VIDEO_ACCESS_20261016.md)
distinguishes raw trajectories, provider annotations and video rights.

The separate American Conference availability capture remains scheduled for
**6:05 p.m. Pacific today / October 17, 01:05 UTC**, within the source's access
window. Future scheduled images are not counted as downloaded.

- [Latest content inventory](docs/status/content_inventory_20261016T2003Z.json) · [freshness, current coverage and access](docs/DATA_FRESHNESS_AND_ACCESS_20261016.md)
- [Data coverage and remaining gaps](docs/DATA_COVERAGE_AND_NEXT_ACQUISITION.md)
- [Earlier expanded acquisition milestone](docs/EXPANDED_DATA_COLLECTION_20261016.md)
- [Shared research protocol](docs/RESEARCH_PROTOCOL.md)
- [Exact deployed source versions and hashes](docs/EXECUTION_SOURCE_VERSIONS.md)
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




