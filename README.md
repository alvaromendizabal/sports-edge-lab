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

**The shared archive contains 46,069 raw content files / 12.42 GB**, verified by content-only S3 inventory on **16 October 2026, 18:09–18:11 UTC**. Receipt files, request indexes, audit files and the duplicate legacy archive are excluded.

| Track | Public archive files | Paid payload files | Stored content GB |
| --- | ---: | ---: | ---: |
| NFL | 815 | 8,654 | 0.791 |
| NBA | 2,909 | 9,309 | 1.902 |
| NCAA football | 668 | 12,050 | 3.057 |
| NCAA men's basketball | 466 | 9,169 | 4.187 |
| NCAA women's basketball | 449 | 1,574 | 2.487 |

The total also includes six provider canary files. Public files can overlap across source families, and hash-addressed paid payloads can serve multiple requests. These are file counts, not unique games or approved training examples.

- **Public archive:** all 5,307 files are retained, including the original 815 NFL files. The new 4,492-file batch passed byte-integrity checks in full.
- **Paid acquisition:** initial runs captured 46,765 responses, including 40,506 odds responses and 6,259 college-statistics responses. The daily odds census processed all 9,811 planned requests; event checkpoints, CBBD plays, player props and shooting recovery still have gaps.
- **Initial jobs:** all earlier jobs are terminal. Game/statistics and shooting runs stopped at their runtime bounds; props stopped at its credit bound. Cached successful work is retained for continuation.
- **Timestamp quality:** only 1,737 prop responses passed the initial nonempty timestamp checks. Full prediction-time eligibility remains a separate acceptance gate.
- **Direct ESPN:** zero captures, stopped on source-access denial without bypass.

**Two continuation jobs are now running in AWS:** missing game-market/college-basketball history and original weather/availability context. The next incremental public pass has completed: **19 new source revisions / 44.71 MB**, **4,473 verified files reused**, and zero failed assets. Prior revisions remain preserved; this does not represent 19 new dataset families. [Continuation scope and launch evidence](docs/CONTINUATION_20261016.md).

[Read the data coverage and next acquisition priorities](docs/DATA_COVERAGE_AND_NEXT_ACQUISITION.md). It maps actual archived families and observed filename years to the remaining source, identity, availability and timestamp gaps.

- [Latest completed-run snapshot](docs/status/operational-status_20261016T1810Z.json) · [content-only inventory](docs/status/raw_inventory_20261016.json)
- [Cumulative execution and cost ledger](docs/status/execution-ledger_20261016T1820Z.json)
- [Family and filename-year inventory](docs/status/archive-family-coverage_20261016.json)
- [Paid acquisition scope, budgets and tests](docs/PAID_ACQUISITION.md)
- [Deployed source versions and hashes](docs/EXECUTION_SOURCE_VERSIONS.md)
- [Public archive source inventory](docs/SOURCE_INVENTORY_20261016.md)
- [Direct original-source capture](docs/ORIGINAL_SOURCE_CAPTURE.md)
- [Shared research protocol](docs/RESEARCH_PROTOCOL.md)
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

