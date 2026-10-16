# Original NOAA HRRR: 2024 football-season expansion

The v020 collector expands the successful October 12, 2024 pilot to every
eligible game in the already downloaded CFBD 2024 season cache. It includes
January 2025 postseason games. Known domes, uncertain kickoff times, incomplete
games, and venues outside the continental United States remain excluded.
The verified CFBD request receipt supplies season lineage, and conflicting
per-game season metadata is rejected. The run reports selected games, exclusion
counts, and distinct forecast initialization/valid-time pairs before downloading.

The original NOAA files are shared continental forecast grids. Multiple games
can refer to the same grid. Temperature, 10-meter wind components, gusts, and
both available precipitation accumulation intervals are archived with exact
initialization, lead, interval, range, ETag, and content hashes.

The previous pilot's original-source fields are reused through the unchanged
URL/range/ETag cache identity. Cached bytes are verified against their recorded
hash before reuse. A source-byte budget exhaustion is a resumable bounded stop,
not evidence that the entire season is complete.

## Authorized run

Artifact: `sports_edge_lab_noaa_hrrr_v020_20261016.pyz`

Arguments: `--season 2024 --full-season --max-games 0 --max-bytes 2000000000
--max-requests 6000 --max-seconds 6900 --cfbd-vintage 2026-10-16
--hourly-usd 0.461`

The AWS processing stop is 7,200 seconds. The application enforces a maximum
of 2,000,000,000 newly downloaded source bytes and 6,000 HTTP requests, with
requests spaced at least half a second apart. No paid API calls or secrets are
used. All 21 self-tests must pass in AWS before cache reads and acquisition.
One unique return ZIP, a full plan, progress snapshots, and a final report are
written to the canonical project bucket.

## Remaining work

This run archives original grid messages; it does not extract venue points.
Historical public release timestamps have not been established. Model
initialization and archive modification timestamps are not substituted for
publication evidence. Forecasts remain unapproved for prediction-time features
until point extraction, venue/roof checks, and temporal-availability validation.

Source documentation: https://registry.opendata.aws/noaa-hrrr-pds/

See `hrrr_artifact_manifest_v020.json` for the executable and source hashes,
argument array, envelope, and validation state.
