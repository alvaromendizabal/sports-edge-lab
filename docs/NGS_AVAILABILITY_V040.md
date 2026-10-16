# NGS and football availability v040 — October 16, 2026

The user authorized public NGS acquisition and continued relevant football downloads. This finite public-source job completed alongside the existing v039 odds backfill; it did not restart or modify v039, resume college-statistics requests, buy access, send outreach or change IAM.

## Verified outcome

AWS job `sports-edge-lab-ngs-availability-20261016-v040` is **Completed**, with ProcessingStartTime `2026-10-16T21:53:02.153000+00:00` and ProcessingEndTime `2026-10-16T21:53:55.742000+00:00`. The application outcome is **completed_with_gaps**: all six selected tasks were processed, zero tasks failed and zero selected tasks remain, but ACC normalization is blocked. AWS completion does not establish full source coverage.

| Dataset | Captured records | Verified coverage and limits |
| --- | ---: | --- |
| NGS passing | 6,133 | 2016–2026; 2026 Week 6 has 2 player records |
| NGS rushing | 6,262 | 2016–2026; 2026 Week 6 has 2 player records |
| NGS receiving | 15,218 | 2016–2026; 2026 Week 6 has 5 player records |
| Official NFL Week 6 injuries | 358 | 28 source tables; zero rejected rows |
| Big 12 football availability archive | 434 | 50 team-games, September 12–October 17; 90 rows across 12 team-games for October 16–18; zero rejected rows |
| ACC football availability archive | Raw extraction only | 83,874 UTF-8 bytes; missing column headers prevent reliable normalization |

The three NGS assets contain **27,613 rows** and **1,953,411 compressed bytes**, with zero missing player IDs and zero duplicate identities under `(season, season_type, week, player_gsis_id, team_abbr)`. These are player-week/season summaries compiled by nflverse, not player/ball trajectories. Published source assets were updated October 16 at 12:02 UTC and captured at 21:53 UTC. Week 6 is ongoing: the available Week 6 rows do not imply a complete week or coverage of every player. Old parquet vintages remain preserved; one compressed CSV per fresh asset was selected for a standard-library row audit without downloading every equivalent format.

The NFL source title explicitly identifies 2026 Week 6. Big 12 and ACC are preserved public rendered archive extractions from embedded pages linked by the conferences, not original PDFs or publication-time archives. Missing statuses remain null. Source publication timestamps, player identity joins and historical point-in-time eligibility remain unverified. SEC discovery returned a landing page without report links; an additional Big Ten discovery URL was blocked and was not bypassed. The earlier valid Big Ten capture remains available. ACC headers must be recovered from a verified source before assigning meanings to its columns.

## Execution and integrity

- **29 offline tests passed locally and inside AWS before runtime credentials/source network.** CloudWatch records the tests before START and the six successful task outcomes before FINISHED.
- Exactly three public NGS requests; two NFL requests including robots policy. Zero paid-provider calls and zero subscription credits. Rendered NCAA pages were obtained during discovery and embedded as frozen inputs.
- Concurrent independent public assets; GitHub request starts paced at no more than 2/second; NFL policy and pacing retained; no provider-denial retries. This does not change the running odds job's 1/second setting.
- Release sizes and SHA-256 digests matched; hash-addressed cache reuse remains enabled. All nine expected raw/derived/bundle S3 objects were independently checked with HeadObject.
- One unique return ZIP was listed and downloaded for CRC/member/content verification. Its report exactly matches S3 report.json. ZIP SHA-256: `a4b7755cee4b37a222a05e40478afb23034ae61b0f33f0b3021b42ffe2ea6094`.
- Existing canonical bucket/role; one `ml.m5.2xlarge`, 30 GB. No application timer; AWS account maximum 432,000 seconds. Actual AWS reported processing interval: **53.589 seconds**, about **$0.006862** at $0.461/hour. This estimate excludes other billed services, storage/requests and unreported startup/shutdown; it is not a billing statement.

Artifact: `infrastructure/code/ngs-availability-20261016-v040/sports_edge_lab_ngs_availability_v040_20261016.pyz`, 31,658 bytes, SHA-256 `966bff81ccf28c48a5fe5071accf77f7f53d9197631537b5d8b64a9ece22a658`.

Run evidence and the return ZIP are under `s3://sagemaker-sports-edge-lab-560403859723-us-west-2/shared/acquisition/ngs-availability/20261016T215339Z-af3efcca00/`. Raw/derived object keys and per-season/week counts are in the [final report](status/ngs_availability_v040_report.json).

## Separate football odds backfill

AWS v039 remained InProgress when observed at **2026-10-16T21:56:33.110915+00:00**. Its saved progress timestamp is **2026-10-16T21:56:17Z**: **1,822 / 4,696 captured, 2,874 remaining, zero failed requests**; 54,660 existing subscription credits used, 2,160,576 remaining in the account, zero college-statistics requests. The recent pace is about 44 snapshots/minute, suggesting roughly another 65 minutes at that observation, conditional on source/network behavior. This queue is historical NCAAF h2h/spreads/totals checkpoints; the selected NFL checkpoints were already cached. It is not a count of games or a denominator for all five sports.

The existing v039 monitor remains enabled. V038 remains superseded and unlaunched. ACB remains deleted and is excluded from all acquisitions.

## What remains useful next

1. Let v039 finish its frozen queue, then validate its final failures, quota and unique return ZIP.
2. Build and validate NFL/NCAAF game/player joins and prediction-time tables from current plays, rosters, NGS, availability, prices and forecasts. Raw acquisition alone is not model readiness.
3. Recover verified ACC column labels and actual SEC/current conference reports; retain the already configured American release-window capture. Add only information actually published.
4. Reconcile the specific NBA/NCAAM/NCAAW core historical-price/statistical gaps against current caches and provider access before any new bulk job. No CBBD restart or new paid basketball batch occurred here.
5. Full tracking and aligned video remain separate, unverified-access datasets. Public NGS summary acquisition does not unlock them. Exhaustive historical props and unrelated leagues are not required for the immediate football core milestone.

The last full in-scope raw inventory was 93,319 files / 17.26 GB at 20:36–20:37 UTC, before these new captures and continued v039 writes. File counts include overlapping families/vintages and are not unique games. Once the finite core backfills and validation are done, use incremental freshness updates rather than repeatedly downloading all history.

## Evidence

- [Terminal AWS, runtime tests and S3 object verification](status/ngs_availability_v040_runtime.json)
- [Final report with coverage](status/ngs_availability_v040_report.json)
- [Return ZIP verification](status/ngs_availability_v040_return_verification.json)
- [Source discovery](status/ngs_availability_v040_discovery.json) and [frozen input manifest](status/ngs_availability_v040_seed_manifest.json)
- [Artifact manifest](status/ngs_availability_v040_artifact.json) and [local tests](status/ngs_availability_v040_local_tests.txt)
- [v039 live progress observation](status/football39_progress_20261016T2156Z.json)
