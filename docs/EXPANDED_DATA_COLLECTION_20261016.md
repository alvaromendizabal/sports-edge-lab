# Expanded original-source collection — 16 October 2026

This milestone extends the five Sports Edge Lab tracks inside the existing
repository, SageMaker space and private data lake. Stored-object inventories,
API capture counters and source coverage are separate measures.

## Verified archive growth

The corrected content scan at **19:23:51–19:24:43 UTC / 12:23–12:24 p.m.
Pacific** measured **71,181 raw content files / 14,393,519,871 stored bytes**.
That is 25,112 files and 1,970,180,812 bytes above the earlier frozen baseline.
All raw objects were classified; metadata and duplicate legacy archives were
excluded. The earlier v023 classifier omitted one 151,579-byte RDS standings
fallback; v025 matches the downloader's supported formats and includes it.
The exact prior report and correction evidence are retained.

| Content type | Files | Stored bytes |
| --- | ---: | ---: |
| original availability pdf | 24 | 1,186,137 |
| original forecast field | 888 | 1,200,723,801 |
| original weather json | 1,438 | 4,264,881 |
| paid payload | 63,499 | 2,403,616,369 |
| provider canary | 6 | 52,895 |
| public archive | 5,326 | 10,783,675,788 |

[Full inventory](status/content_inventory_20261016T1924Z.json) ·
[AWS inventory test evidence](status/content_inventory_v025_test_logs_20261016.json).
The scan is an interval while collectors are active; later API capture counters
must not be added to these stored-byte or object totals.

## Workstreams

| Workstream | Scope | Bound |
| --- | --- | --- |
| Historical NOAA forecasts v020 | Eligible completed 2024-season NCAA football games, including January 2025 postseason; original forecast grids | 2 GB new source bodies; 6,000 HTTP requests; 7,200 Processing seconds |
| College shooting continuation v024 | Conference-filtered team/player season shooting summaries with positive-data gates | 3,000 statistics HTTP reservations; zero odds credits; 2,400 Processing seconds |
| American Conference availability v022 | Published report images discovered from actual men's and women's daily report pages | Scheduled for the source's permitted visit window; not yet acquired |
| Raw-content census v025 | Paginated S3 object metadata for explicitly classified raw content | 1,000 listing pages; 300 Processing seconds; no source API calls |

The existing game-market/statistics and player-prop collectors continue their
previous bounded runs. Their limits are not reset. New acquisition avoids their
endpoints and resumes existing historical caches with hash checks.

The NOAA expansion reuses the October 12 pilot and retains both precipitation
accumulation intervals. Grids are shared across games. Their count does not
describe venue-level weather series; extraction at stadium coordinates and
historical release-availability checks remain outstanding. A 2 GB limit can
stop the expansion before all eligible games have weather coverage.

The first shooting continuation v021 was stopped after the initial observation
of 300 successful HTTP responses all returning empty lists. Its final frozen
receipt audit counted **580 empty responses and zero nonempty responses**;
requests completed between the observation and AWS stop settlement. These are
coverage observations, not 580 acquired shooting datasets. V024 preserves those
caches, prioritizes conference-filtered requests, and passed both cached 2026
and fresh 2024 positive Duke/ACC record gates. Its 34 AWS self-tests passed.
At **19:28:52 UTC**, v024 had **30 nonempty/positive responses, 2,384 observed
records, zero empty responses, and zero failed requests**. Shooting summaries
remain retrospective aggregates and are not approved pregame features.

[Stopped-run intervention](status/shooting_intervention_20261016.json) ·
[V024 test and canary proof](status/shooting24_test_and_canary_evidence_20261016.json) ·
[V024 runtime and final empty-response audit](status/shooting24_progress_20261016T1929Z.json).

American Conference availability extends original injury/participation evidence
to NCAA men and women. The source permits visits from 01:00 to 06:45 UTC. The
collector is scheduled for **17 October at 01:05 UTC / 16 October at 6:05 p.m.
Pacific**. Scheduling is not a completed download: no report images are counted
before capture. The target list is sparse; it does not establish full conference
or NCAA historical coverage. Discovery pages and robots evidence remain
separate from raw report images.

## Live acquisition snapshot and execution ledger

The game/statistics continuation's **19:26:12 UTC** report recorded **17,362
captures**: 14,006 odds and 3,356 college-basketball responses, with zero failed
requests. The player-prop continuation's **19:27:18 UTC** report recorded
**12,808 captures and 1,700 failed requests**. Failed requests remain visible;
previously inspected samples were missing-event responses, which does not
classify every failure in this later count.

At the latest NOAA progress observation, **164 of 440 forecast pairs** had been
processed, **1,344,565,401 source bytes** downloaded, and zero errors recorded.
The plan maps shared forecasts to **3,631 eligible cached historical game
records**; this is not 3,631 separate grid files or complete venue weather
series. The 2 GB bound may leave unfinished pairs. These runtime counts and
uncompressed HTTP bytes overlap the earlier storage census and are never added
to its total.

The verified one-time NCAA schedule is enabled for 01:05 UTC on October 17.
The outside-window preflight passed all 23 tests, captured zero source bytes,
and emitted its deferred report and unique return ZIP. Scheduled acquisition
is not counted as an execution or as downloaded report images.

The cumulative ledger contains **29 actual Processing executions**: **15
Completed, nine Failed, one intentionally Stopped, and four InProgress**. It
retains all failed history and classifies the direct ESPN access rejection as a
valid negative source-access result separately from acquired data. The
reported interval estimates are **$1.604636 completed**, **$0.082103 failed**,
**$0.054439 stopped**, and **$1.023516 running elapsed** at their observations.
These are compute estimates, not a billing statement; Studio, storage, requests,
subscriptions, and unreported provisioning/shutdown remain excluded. The
scheduled future run is excluded from execution counts.

[Live progress](status/live_progress_20261016T1928Z.json) ·
[AWS job states](status/job_statuses_20261016T1928Z.json) ·
[Cumulative ledger](status/execution_ledger_20261016T1929Z.json) ·
[Verified schedule and preflight](status/ncaa_schedule_verified_20261016.json).

## Data still required for the research program

- Complete measured event, sportsbook, market and pregame-checkpoint coverage;
  preserve missing-event responses and distinguish them from retryable failures.
- Deeper availability vintages and reliable team/player/game identity links,
  including NCAA women's reports and lineup/participation gaps.
- Complete play, shot, lineup and substitution coverage where sources support
  it; validate response semantics and empty historical partitions.
- Historical forecasts across seasons, venue-point extraction and roof/domain
  checks, with publication timing distinct from initialization and valid time.
- Verified access to full player/ball trajectories, body-pose observations and
  aligned video. Public aggregate tracking tables do not establish that access.

Raw acquisition supports the planned score-distribution, player-usage and
possession-sequence models. Training still requires identity, temporal,
coverage and settlement gates followed by frozen chronological evaluation.
No amount of downloaded data alone establishes frontier predictive results.
