# Frontier-relevant acquisition priorities — 16 October 2026

This is a source and research gap inventory, not a claim that all records are present or that predictive performance is frontier-level. The existing family inventory in `docs/status/archive-family-coverage_20261016.json` already contains substantial play-by-play, shots, lineup/stint, roster, schedule, charting, aggregate tracking, and market history. Repeating those downloads has lower value than closing measured gaps and proving what was available before each prediction.

## What is obtainable now

| Priority | Additional information | Concrete acquisition and acceptance |
| --- | --- | --- |
| 1 | Complete pregame prices and player prop observations at defined cutoffs | Continue existing paid request indexes. Measure nonempty, timestamp-valid coverage by event, sport, season, market, book and cutoff. Kickoff revisions and bookmaker updates after the decision cutoff must remain in an audit table and out of pregame features. |
| 2 | Public injury/availability revisions and effective-dated participants | Preserve discovered official reports and current roster/depth-chart snapshots as immutable vintages. Official NCAA availability reporting began as a 2026 tournament pilot for men and women; do not infer all-season or older historical reporting. Original NBA injury PDF capture has begun, but a seed PDF is not season coverage. |
| 3 | Original historical football weather model fields | The new bounded NOAA HRRR collector reads original public archive objects for cached completed games on 2024-10-12. It archives surface GRIB messages for five variable families and the source index, with hashes, model initialization, forecast lead, valid hour, source object metadata and game/venue selectors. This is an original forecast archive, not point-ready or point-in-time-approved data. |
| 4 | Missing basketball possession, substitution and lineup coverage | Existing sources already supply many of these tables. Complete the missing CBBD requests and validate source schema, game coverage, player identities and lineup conservation. Independently audit women's source coverage rather than assuming men's paid endpoints cover women. |
| 5 | Women's original schedule, boxes and availability evidence | NCAA's official women's statistics pages and tournament availability policy establish legitimate source targets. A tested Casablanca daily-scoreboard URL returned 404, so no working new original women’s feed is claimed. Obtain a supported provider export where public originals are unavailable; Sportradar documents a separate NCAAWB product. |
| 6 | Derived contextual information | Build rest, travel, time-zone changes, schedule congestion and opponent-adjusted usage from reconciled existing schedules, venues, rosters and plays. These do not need another bulk season download. Keep observed match results separate from pregame available information. |

## NOAA HRRR pilot: exact scope

- Public NOAA archive: `https://noaa-hrrr-bdp-pds.s3.amazonaws.com/`. The official AWS Open Data registry describes hourly 3-km HRRR data, a historical archive since 2014, and public reuse with attribution. The first canary index for run 2024-10-12 12 UTC, lead 6 hours, returned HTTP 200 and valid records.
- Actual object discovery: the collector obtains a public S3 listing for each cycle prefix and requires both original GRIB and `.idx` objects to be present. A verified public listing returned 98 objects for the canary surface cycle, including 49 GRIB/index pairs. This is stored in `NOAA_HRRR_LAYOUT_EVIDENCE.json`; the collector does not rely on the outdated layout example in the linked README.
- Game selectors: existing hash-verified CFBD `/games` 2024 and `/venues` payloads, vintage 2026-10-16. Only completed, confirmed-time games on UTC 2024-10-12 in the mainland US domain are selected. Known domes are excluded. Unknown roof status remains explicitly unverified.
- Initialization: floor the game start minus nine hours to a whole UTC hour. Valid hour is the first whole hour at or after kickoff, usually lead 9 or 10. Forecast fields cover the CONUS grid and are shared among same-cycle/lead games; venue point extraction comes later.
- Fields: temperature at 2 m, U and V winds at 10 m, surface gust and surface accumulated precipitation. The original index text preserves accumulation period. The verified NOAA file contains both run-to-valid cumulative precipitation and a one-hour precipitation interval; V019 preserves each as a distinct field with explicit start/end forecast hours. Later engineering must not confuse these totals.
- Integrity: range responses must be HTTP 206 with exact numeric Content-Range and known total source size; selected messages must have GRIB2 framing, correct embedded length and final marker. A 200 response to a range request is closed without reading a full model file. HTTP 401/403/429 suspends the source. Original object ETags are used for conditional range requests.
- Bounds: at most 250,000,000 response-body bytes, 500 source HTTP requests, 600 application seconds; AWS processing allowance 900 seconds. No source retries. One compact uniquely named return ZIP. Fifteen automatic self-tests run before AWS/data activity, with timestamped progress and resumable cache indexes.
- Historical availability remains unknown. Model initialization and archive Last-Modified are not release timestamps. The nine-hour buffer is a conservative selection heuristic, not proof of contemporaneous availability. GRIB decoding, nearest-grid validation, model version handling, roof interpretation, weather direction/stadium orientation, and historical availability checks remain separate acceptance gates.

## Full tracking is a distinct data product

The downloaded NFL NGS summaries and NBA tracking summary tables do **not** establish possession of full player/ball trajectories, body pose, or complete event-to-video alignment. We should describe their granularity exactly.

- NFL Football Operations' public Big Data Bowl repository explicitly retains one 2017 tracking game, plus matching player, play and game tables. Larger competition releases have their own scope and terms. This pilot is not added again here, and existing separate Big Data Bowl work is not silently copied into Sports Edge Lab.
- NBA states that its official tracking data feed integrates into Second Spectrum's analytics engine used by NBA teams. Public player-tracking summaries are separate from raw optical coordinates. NBA/AWS Inside the Game provides advanced public metrics; raw tracking access is not established by that announcement.
- Genius Sports publicly offers official NFL/NCAA data products, including Next Gen Stats and NCAA coverage; Sportradar documents a separate women's NCAA basketball API. Neither provider's complete export is evidenced in our current archive or confirmed current entitlements. Exact historical coverage, field granularity, allowed ML use, and export terms must be verified with the provider before claiming access. This is not a claim that a particular new subscription is mandatory or automatically sufficient.

## Historical forecast caveat

Open-Meteo's Single Runs API is promising, but its documentation explicitly separates initialization from public availability and identifies early ECMWF material as hindcasts. Do not relabel a stitched historical forecast series, reanalysis, or subsequently generated hindcast as the forecast a bettor could have seen at a historical cutoff. Direct archived operational model fields reduce that ambiguity, while source distribution timing still requires validation.

## Primary source evidence

1. NOAA HRRR archive, licensing and public bucket: <https://registry.opendata.aws/noaa-hrrr-pds/>.
2. NOAA's public HRRR access announcement: <https://www.noaa.gov/information-technology/open-data-dissemination/news/noaa-open-data-office-hours-high-resolution-rapid-refresh-hrrr>.
3. Open-Meteo individual forecast runs and release lag/hindcast caveats: <https://open-meteo.com/en/docs/single-runs-api>.
4. NCAA March 4, 2026 men's/women's tournament availability policy: <https://www.ncaa.org/news/media-center-ncaa-releases-penalty-and-process-details-for-march-madness-player-availability-reports/>.
5. Official NCAA women's statistics and records: <https://www.ncaa.org/championships/statistics-and-records/womens-basketball/>.
6. NFL Football Operations' public tracking release: <https://github.com/nfl-football-ops/Big-Data-Bowl>.
7. NBA/Second Spectrum official partnership and tracking integration: <https://pr.nba.com/nba-genius-sports-second-spectrum-expanded-partnership/>.
8. NBA/AWS public advanced-metric initiative: <https://www.nba.com/news/nba-aws-partnership>.
9. Genius Sports official data product description: <https://www.geniussports.com/engage/official-sports-data-api/>.
10. Sportradar's separate NCAAWB integration documentation: <https://developer.sportradar.com/basketball/docs/ncaawb-ig-overview>.

## Research priorities after acquisition

The credible advanced projects are calibrated joint score distributions, player minutes/snaps and usage distributions, possession/play sequence models, player interaction models and market-aware forecast comparisons. They require reconciled identities, frozen chronological splits, measured missingness, prediction-time feature eligibility, independent holdout evaluation and calibration against market-only, rating and strong boosting baselines. More architectural complexity and larger byte counts do not establish an edge.

## Runtime correction

The v017 pilot passed eleven self-tests but stopped before source requests because its historical CFBD game-cache lookup incorrectly included the daily vintage. V018 matches the paid collector: completed 2024-season game requests use an empty vintage, while reference `/venues` and current-season requests retain the daily capture vintage. The exact existing 2024 game receipt was verified read-only (3,801 returned records); two regression tests now cover the historical key and reference/current-season vintage distinction. No paid API requests were made for this repair.

The v018 pilot passed thirteen self-tests and reused the correct game/venue caches. It captured 29 original listing/index documents (308,432 bytes), but rejected all 18 planned forecast pairs before GRIB capture because real NOAA indexes contain two distinct APCP accumulation intervals. V019 preserves both intervals with explicit semantics, validates the forecast lead, and adds two tests using the actual complete NOAA index. Prior metadata captures remain reusable; raw weather field success is reported only after a runtime receipt verifies it.
