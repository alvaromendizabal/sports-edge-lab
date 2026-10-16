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

**Acquisition is active; model performance has not yet been established.** The initial NFL catalog contains 815 pinned public assets (722,613,027 bytes), previously verified in the private NFL archive. That work and its Git history are preserved. Consolidation has verified 1,663 prior objects (1,451,136,208 bytes) in the central data lake, including metadata and duplicate legacy captures. These object counts do not represent additional unique NFL datasets. The six old project buckets were retired after the archive verification.

A bounded paid-data backfill has started in AWS for all five sports: historical moneylines, spreads and totals, plus CollegeFootballData and CollegeBasketballData statistics. At the **2026-10-16 00:53:30 UTC** snapshot, three acquisition jobs were running: public archive expansion, game-level odds/college statistics, and historical player props. The direct ESPN job stopped on source-access denial with zero captures. The archived [operational status](docs/status/operational-status_20261016.json) and [execution/cost ledger](docs/status/execution-ledger_20261016.json) distinguish completed work, active runs and failures. Successful requests and stored files are not evidence that every source, season, field or pregame timestamp is complete.

| Workstream | Observed progress at the snapshot | State |
| --- | --- | --- |
| Public statistics | 4,492 assets cataloged; 2,643 processed; 817,475,475 bytes downloaded | Running; incomplete |
| Game odds and college statistics | 5,554 captures; 3,329,493,477 uncompressed response bytes | Running; 22 optional shooting-query errors recorded |
| Player props | 872 captures; 434,453 market outcomes across returned responses | Running; timestamp and kickoff issues flagged |
| Direct ESPN capture | 0 captures | Access blocked; stopped without bypass |

These measures describe requests and files, not unique games or model-ready examples. Payload bytes and compressed archive sizes are different measures; they are not summed into a headline dataset size. [Read the snapshot interpretation](docs/status/README.md).

- [Paid acquisition scope, budgets and tests](docs/PAID_ACQUISITION.md)
- [Deployed source versions and hashes](docs/EXECUTION_SOURCE_VERSIONS.md)
- [Public archive source inventory](docs/SOURCE_INVENTORY_20261016.md)
- [Direct original-source capture](docs/ORIGINAL_SOURCE_CAPTURE.md)
- [Shared research and acceptance protocol](docs/RESEARCH_PROTOCOL.md)
- [Verified consolidation record](docs/CONSOLIDATION_20261016.md)
- [Machine-readable track configuration](config/tracks.json)
- [Preserved original NFL setup](docs/history/NFL_SETUP_20261015.md)
- [Original NFL asset manifest](catalog/public_asset_manifest_20261015.json)

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
