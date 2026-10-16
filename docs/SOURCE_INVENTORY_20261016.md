# Public historical statistics acquisition

Sports Edge Lab keeps all five sport tracks in one repository and one SageMaker space. This runner adds NBA, NCAA football, NCAA men's basketball, and NCAA women's basketball to the existing NFL archive. It does not download the already-acquired NFL files again.

## Source and lineage

The active release store is [sportsdataverse/sportsdataverse-data](https://github.com/sportsdataverse/sportsdataverse-data). The old `hoopR-data` and `wehoop-data` repositories are archival; the live releases moved. The upstream organization's [status page](https://sportsdataverse.org/status) documents producer health and freshness.

| Track | Public archive families selected | Original upstream |
|---|---|---|
| NBA | `espn_nba_*`, `nba_stats_*`, team crosswalk/group reference | ESPN NBA; NBA Stats |
| NCAA football | Basic `espn_cfb_*` schedules, PBP, boxes, drives, rosters, injuries, participants and betting; `ncaa_mfb_*` statistical files; CFBD PBP; recruiting/portal/reference files | ESPN; NCAA; CollegeFootballData |
| NCAA men | `espn_mens_college_basketball_*`, basic `ncaa_mbb_*`, injury/reference snapshots | ESPN men's college basketball; NCAA |
| NCAA women | `espn_womens_college_basketball_*`, basic `ncaa_wbb_*`, injury/reference snapshots | ESPN women's college basketball; NCAA |

The runner inventories real GitHub release metadata at execution time and downloads only listed assets. It does not manufacture historical filenames or assume that every season exists. It retains one encoding per asset stem, preferring Parquet over CSV/JSON/RDS. Each selected source URL, asset ID, size, SHA-256 when supplied, and update timestamp is pinned in the run manifest.

These are **community-compiled statistical archives**, not observations independently collected by Sports Edge Lab from original websites. Their original source and SportsDataverse lineage remain explicit. We own the acquisition code and subsequent independently developed transformations; upstream data rights remain with their holders. Raw source files stay private in S3. The upstream repository's README displays CC BY 4.0 for its data; source-specific rights and attribution still apply. Public repository artifacts contain acquisition code, source documentation, and nonsecret manifests rather than raw licensed payloads.

Third-party trained models, RAPM outputs, engineered rolling windows, ratings, prediction/forecast tables, and named feature datasets are excluded. Some play-by-play archives can contain upstream computed columns; archival possession does not approve those columns as owner-developed features. Feature eligibility is decided during a later column-level audit. Original ESPN HTTP captures are acquired by the separate direct-source workflow.

## Verification and resumability

Each payload must match its listed byte count and any supplied GitHub SHA-256 digest. Parquet assets must have valid framing; JSON must parse. HTML error pages cannot pass as CSV/JSON data. Successful files receive a local SHA-256, encrypted S3 object, and acquisition receipt. Immutable content-hash paths preserve source revisions. A repeated run uses S3 HEAD metadata and upstream identity to reuse verified existing objects.

Default execution bounds are four source download workers, one hour, and 30 GiB transferred. Source retries are bounded. Heartbeats record progress, remaining assets, elapsed time, transferred bytes, and estimated processing compute cost. Final run reports distinguish downloaded, reused, failed, deferred, and not-attempted assets. Any incomplete acquisition returns a nonzero status while preserving successfully archived objects and a return ZIP.

The gate proves downloaded byte integrity. It does **not** prove complete seasons, correct schemas, nonduplicated events, reliable historical injury vintages, or availability at a pregame decision time. In particular, final box scores, postgame PBP, and retrospective season totals cannot be joined directly onto predictions for the same game. Injury snapshots need their capture dates; schedules and odds need event-time normalization. Those checks remain subsequent acceptance gates.

## Execution

The processing image needs Python 3.10+ and boto3. Run the script with `--bucket sagemaker-sports-edge-lab-560403859723-us-west-2 --sport all --prefix tracks`. An optional `--manifest` accepts a local pinned list, including the prior v004 asset schema. Without it, discovery is live and complete for supported tags.

Files land under `tracks/{sport}/raw/sportsdataverse/`, catalogs under `tracks/{sport}/catalogs/`, and run evidence under `tracks/{sport}/acquisition-runs/`. Automatic self-tests run before any network operation. `--self-test` runs only those tests and exits.

Historical scope is established from the actual manifests and per-season audit, never from a marketing claim. NBA ESPN loader documentation advertises a 2002-forward archive, while NBA Stats and NCAA sources have different ranges; current schedule files can include upcoming seasons before statistics exist.
