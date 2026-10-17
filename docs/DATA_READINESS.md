# Data readiness — scope, history and remaining gaps

[Overview](../README.md) · [Model card](MODEL_CARD.md) · [Architecture](ARCHITECTURE.md)

## The play-by-play history is much larger than one season

The **14,031 NFL rows / 80 games** previously highlighted describe the **2026 slice only**. V057 audited 11 NFL seasons, 2016–2026, with **498,285 play-by-play rows / 2,841 completed games**. The broader raw archive includes NFL assets for **1999–2026**. College archives include **ESPN PBP for 2004–2026**, **cfbfastR for 2014–2026** and **NCAA PBP for 2013–2026**. Archive availability and an audited modeling cohort are separate claims.

| Season | PBP rows audited | Completed games | Identified non-scramble dropbacks |
| --- | ---: | ---: | ---: |
| 2016 | 47,651 | 267 | 20,292 |
| 2017 | 47,245 | 267 | 19,584 |
| 2018 | 47,109 | 267 | 19,825 |
| 2019 | 47,260 | 267 | 19,905 |
| 2020 | 47,705 | 269 | 20,184 |
| 2021 | 49,922 | 285 | 21,010 |
| 2022 | 49,434 | 284 | 20,393 |
| 2023 | 49,665 | 285 | 20,723 |
| 2024 | 49,492 | 285 | 20,007 |
| 2025 | 48,771 | 285 | 19,737 |
| 2026 snapshot | 14,031 | 80 | 5,677 |
| **Total** | **498,285** | **2,841** | **207,337** |

Raw PBP includes multiple event types; it is not a count of passing attempts. V057 separately excluded 9,606 scramble rows from its declared non-scramble QB rate representation. It retained eight ambiguous dominant-passer cases as unknown. The audited slice produced 6,963 player/team/game records.

## Broader raw coverage verified from AWS

An October 17, 2026, 21:38 UTC S3 listing verified these stored scopes. ETag-pinned Parquet metadata then counted the latest stored annual ESPN revisions without downloading entire files or calling a sports provider.

| Raw source | Annual coverage | Stored objects | Stored bytes | Record-count interpretation |
| --- | --- | ---: | ---: | --- |
| NFL nflverse PBP | 1999–2026 | 29 | 499,480,229 | 28 annual Parquets plus a revised 2026 CSV; revisions overlap. |
| ESPN college PBP | 2004–2026 | 24 | 1,110,096,615 | **3,233,114 records** across selected latest annual files; **1,586,956** in 2016–2026 and **78,642** in the selected 2026 file. |
| cfbfastR college PBP | 2014–2026 | 13 | 1,091,880,151 | Source presence verified; no deduplicated unique-play count claimed. |
| NCAA college PBP | 2013–2026 | 14 | 140,677,241 | Source presence verified; overlaps the other college sources. |

These are stored file records, including administrative events, not certified valid offensive plays or independent prediction examples. Do not sum overlapping sources into a unique total. The earlier **22,151 direct CFBD plays** described a selected current backfill, not the entire college history. [Exact listing and metadata evidence](status/pbp_coverage_verified_20261017.json).

## Readiness by asset

| Asset | Verified scope | Interpretation / remaining gap |
| --- | --- | --- |
| Canonical completed NFL games | 2,841 across 2016–2026 | Historical modeling scope, not all football history. |
| Canonical completed NCAAF games | 9,089 across 2016–2026 | FBS plus opponents, not every FCS game. |
| Valid college drive representation | 8,937 primary + 124 separately validated recovered = 9,061 games | 28 lack any valid representation; secondary-source interchangeability is not approved. |
| NFL PBP / QB history | 498,285 audited source rows; 207,337 eligible identified dropbacks | Upcoming starter identity remains unknown. |
| Selected historical odds queue | 4,696/4,696 selected requests complete | Completion of a selected queue, not all possible prices/markets. |
| Market matching | 12,123 accepted records; 12,119 paired predictions | 1,113 game/task coverage gaps; not an unfinished provider queue. |
| Public NGS | 27,613 statistical summary rows, 2016–2026; 692/692 current identity joins | These are not full tracking coordinates or synchronized video. |
| NFL snap / injury IDs | 7,463/7,463 snaps; 374/374 injury rows | Identity success does not verify historical report publication time. |
| College availability | 2,393/2,402 valid rows joined | Nine unresolved rows; one malformed ACC row quarantined separately. |
| Tracking and aligned video | No verified entitlement | Access, coverage, synchronization and permitted ML use remain unconfirmed. |

The 28 college drive gaps comprise **eight absent, 17 invalid and three recent finals** awaiting representation. There are **152 gaps in the original primary drive source**, of which 124 have separately validated alternatives. Those denominators must not be conflated. The accepted college model is unchanged; a recovered source is not automatically an interchangeable feature input.

The wider raw archive contains older and overlapping sources. Row counts from multiple college releases, direct captures and revisions must not be added and described as unique plays without an exact game/play reconciliation. A source/season inventory establishes stored coverage, not valid model-ready rows.

## Freshness

| Evidence | Last verified observation |
| --- | --- |
| NFL current modeling snapshot | October 16, 2026, 23:30:05 UTC; completed NFL game dates through October 15 |
| College current canonical snapshot | October 17, 2026, 15:07:26 UTC; three newer finals beyond the accepted feature table |
| V057 model execution | Finished October 17, 2026, 21:35:36 UTC; reused pinned caches, no new source calls |

These dates are observations, not universal source-publication timestamps. V057 did not download new games, make new live forecasts, or refresh current player availability.

## Information-time constraints

Historical archives may contain later corrections. Unknown publication timestamps stay null. A retrospective 24-hour outcome-release assumption does not establish strict historical point-in-time eligibility. Current injury reports, postgame usage and a target game's actual starter are not valid historical pregame features for that same game.

Availability values retain missing and ambiguous states. Missing game-day status is never relabeled “available.” A verified 2026 American Conference football availability source remains a gap; the known 2025 archive and basketball-seeded one-off do not resolve it.

## Highest-value repairs

1. Incorporate newly completed/revised games through the existing authorized freshness workflow, preserving versions and avoiding duplicate collectors.
2. Resolve the 28 drive gaps and nine availability rows with exact source-backed evidence; retain any unrecoverable cases explicitly.
3. Establish upcoming QB/starter and availability observations with defensible decision timestamps before live player-informed forecasts.
4. Collect forward-only information vintages and freeze a prospective evaluation contract before claiming deployable skill.
5. Confirm tracking/video rights before designing a method that depends on them. Tracking is not required for the next cache-only benchmark.

V058 is a **model-family experiment on existing data**, not an acquisition job or a declaration that these repairs are complete. ACB remains excluded and CBBD stopped.

## Source evidence

[V057 summary](status/football_v057/summary.json) · [scorecard data](demo/evidence.json) · [original content inventory](status/content_inventory_20261016T2330Z.json) · [source catalog](DATA_CATALOG.md) · [acquisition history](history/README_PRE_MODELING_20261017.md).
