# Data readiness — scope, history and remaining gaps

[Overview](../README.md) · [Model card](MODEL_CARD.md) · [Architecture](ARCHITECTURE.md)

## Current target: NFL and FBS versus FBS

Future college forecasts and headline evaluation are **FBS versus FBS**. The historical FBS/FCS archive remains available as explicitly declared opponent context; no standalone FCS prediction, acquisition or repair work is planned. Prior mixed-cohort counts below remain historical coverage evidence and are not relabeled FBS-only.

| Current FBS scope / representation state | Count | Status |
| --- | ---: | --- |
| Prior audited canonical completed FBS-vs-FBS games | 7,898 | Dated canonical snapshot, not silently relabeled current |
| FBS-vs-FBS games in frozen model table | 7,895 | Accepted features/predictions preserved |
| Current-season finals in reused current capture | 354 | 15 additional finals beyond prior current-season canonical 339 |
| V059 accepted overtime-order repairs | 8 games / 16 team rows | Runtime verified; 33 explicit overtime rows retained separately |
| V060 selected official-school sources captured | 14 / 14 | All selected source captures succeeded |
| V061 validated secondary representations | 12 / 14 | Two additional cached records validated at runtime; separate source semantics |
| Selected historical games still without validated secondary representation | 2 | Temple–UConn and Boise State–SDSU |
| Original ESPN-source gaps repaired by V060/V061 | 0 | All 14 original-source gaps remain; secondary sources stay distinct |
| Historical FBS/FCS context gaps | 6 | Deferred; no standalone FCS work |

The eight V059 repairs corrected regulation-drive auditing order. V060 then validated ten official-school secondary representations among the remaining 14 cases. Accepted model features and source bytes remain unchanged; secondary-source interchangeability is still unapproved. Do not subtract those ten and claim the original ESPN source is repaired.

V061 replayed the four previously captured cases and runtime-validated two more secondary representations, Syracuse–Purdue and Texas–UTSA, bringing accepted coverage to **12/14**. Temple–UConn and Boise State–SDSU remain. This cache-only repair made no new source request and did not alter frozen features.

V061's separate 15-game current drive queue made **one robots request**, received **HTTP 403**, saved the host stop and captured **zero current summaries**. All 15 remain unvalidated for drive representation. No ESPN retry or alternate access-path bypass is authorized by the next plan.

**V062 is prepared, not executed.** Its independent official-school queue contains 17 FBS-versus-FBS targets: these 15 recent finals and the two historical gaps. Fourteen HTML targets can support at most 14 validated drive closures; three PDFs are text-only capture/extraction and cannot close drive gaps. Limits are **40 HTTP attempts / 100 MB**, including policy/redirect accounting, with zero ESPN, CFBD, CBBD or odds usage. [Prepared scope](status/football_v062/README.md).

The existing six-hour college capture observed **October 17, 2026, 21:07:13 UTC** contains 354 current-season FBS finals, including 15 beyond the earlier canonical snapshot. V060 reconciled exact final scores against team/player boxes for all 15, with zero new CFBD requests. This does **not** verify current PBP/drive completeness or alter frozen historical predictions.

[Actual V061 acquisition outcome](status/football_v061/acquisition_completion.json) · [Preserved V060 outcome](status/football_v060/acquisition_completion.json) · [V059 accepted repair](status/football_v059/repair_completion.json).

## Readiness reporting correction

Several inherited top-level fields in the V060 return were stale: they still reported zero provider calls, 14 unresolved representations and older source timestamps/feature descriptions. Authoritative acquisition, summary and current-capture evidence instead shows **32 public HTTP attempts, 10 validated secondary games and four selected cases remaining**. The accepted college models use 60 historical team/drive features; the prior score-state feature description does not describe V060.

The original return is preserved. The public [readiness errata](status/football_v060/readiness_errata.json) records each stored-versus-corrected value; the audit outcome is `PASS_WITH_REPORTING_ERRATA`. Download success, validated representation, frozen model coverage and prospective feature eligibility remain different states.

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

## Preserved broader historical holdings

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

In the prior mixed FBS/opponent scope, 28 college drive gaps comprised **eight absent, 17 invalid and three recent finals** awaiting representation. The current FBS-only breakdown and completed V059 repair are reported above. The prior mixed-cohort totals are preserved historical observations. There are **152 gaps in the original primary drive source**, of which 124 have separately validated alternatives. Those denominators must not be conflated. The accepted college model is unchanged; a recovered source is not automatically an interchangeable feature input.

The wider raw archive contains older and overlapping sources. Row counts from multiple college releases, direct captures and revisions must not be added and described as unique plays without an exact game/play reconciliation. A source/season inventory establishes stored coverage, not valid model-ready rows.

## Freshness and acquisition accounting

| Evidence | Last verified observation / outcome |
| --- | --- |
| NFL current refresh | Completed October 17, 2026, 23:07:22 UTC; six downloads, four semantic content changes |
| NFL current PBP | 14,031 rows / 80 game IDs after revision; no new game IDs in this capture |
| College current capture | Observed October 17, 2026, 21:07:13 UTC; 15 newer finals reconciled against exact team/player boxes |
| V061 modeling execution | Finished October 17, 2026, 23:42:25 UTC; 24 fits, frozen references preserved |
| V061 current drive queue | One robots HTTP 403; zero captures; all 15 current games remain open |

The four NFL semantic changes were PBP, weekly rosters, depth charts and player mapping. NGS passing/rushing changed compressed bytes but not normalized content; snap counts and NGS receiving reused unchanged cached digests. These are source revisions, not six new NFL games.

V060 recorded **32 public HTTP attempts**, 30 successful responses/redirects and two robots-file 404 responses. No new 401/402/403/429 provider denial occurred. CFBD requests, CBBD requests and odds credits were zero; the prior CBBD stop remains. The request count includes policy checks/redirects and does not equal downloaded dataset count.

V061 subsequently recorded one failed robots-policy request and retained the provider denial. Its models completed while acquisition remained blocked; these are separate outcomes. Paid-provider usage remained zero.

These observation dates do not establish unknown original publication timestamps. New source captures remain separate from frozen benchmark features and do not produce live forecasts automatically.

## Information-time constraints

Historical archives may contain later corrections. Unknown publication timestamps stay null. A retrospective 24-hour outcome-release assumption does not establish strict historical point-in-time eligibility. Current injury reports, postgame usage and a target game's actual starter are not valid historical pregame features for that same game.

Availability values retain missing and ambiguous states. Missing game-day status is never relabeled “available.” A verified 2026 American Conference football availability source remains a gap; the known 2025 archive and basketball-seeded one-off do not resolve it.

The nine unresolved college availability rows represent **three players**, and **none of those rows satisfies the examined 24-hour pregame eligibility gate**. Correcting an ID alone would not make these rows valid historical pregame features.

## Highest-value next work

1. Execute the prepared, finite official-source queue only within its declared scope; keep unsupported HTML/PDF records separate from validated drives.
2. Test the prepared L1-versus-L2 point objective with exact cached controls; do not reopen the failed V061 representation by exposed-period tuning.
3. Establish upcoming QB/starter and availability observations with exact identity and defensible decision timestamps.
4. Preserve forward-only information vintages and freeze a prospective evaluation contract before claiming deployable skill.
5. Confirm tracking/video rights before a method that depends on them. These are not prerequisites for the prepared cached-feature benchmark.

V061 completed 24 model fits, two cached secondary repairs and a bounded provider stop. V062 remains prepared, with **zero completed V062 real fits**. ACB remains excluded and CBBD stopped.

## Source evidence

[V061 summary](status/football_v061/summary.json) · [V062 preparation](status/football_v062/preparation.json) · [Preserved V060 summary](status/football_v060/summary.json) · [acquisition completion](status/football_v060/acquisition_completion.json) · [readiness corrections](status/football_v060/readiness_errata.json) · [V059 accepted repair](status/football_v059/repair_completion.json) · [scorecard data](demo/evidence.json) · [original content inventory](status/content_inventory_20261016T2330Z.json) · [source catalog](DATA_CATALOG.md) · [acquisition history](history/README_PRE_MODELING_20261017.md).
