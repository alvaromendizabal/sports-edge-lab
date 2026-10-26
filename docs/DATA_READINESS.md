> Historical source-readiness lineage. Current verified inventory and remaining conflicts are summarized in [the October 25 evidence report](CURRENT_EVIDENCE.md#data-and-operational-readiness). The dated observations below are preserved.

# Data readiness — scope, history and remaining gaps


## Current evidence — V065 complete, V066 prepared

V065 finished at **2026-10-18 02:02:55 UTC** after one confirmed CFBD capture: **11,405 source rows across 489 games**. Strict validation retains **393 games: 291 FBS versus FBS and 102 declared opponent-context games**. Against all 455 primary games, **308 match, 81 disagree and 66 lack accepted comparisons**. The 49 missing strict-FBS comparisons are quarantined source games, not missing downloads. No model inputs were replaced; FBS60 remains blocked.

**99 invalid rows affect 82 quarantined games**. Another 324 source rows across 14 games are retained raw but excluded by the unchanged canonical completion snapshot. New source observation, canonical completion and model-input freshness remain separate contracts. [Actual V065 evidence](status/football_v065/README.md).

All six previously issued NFL forecast records remain pending for two games; 186 abstentions are preserved. V065 made zero real fits, new forecasts or promotions. **495 runtime tests and 2,743 independent audit checks passed.** The verified minimum tally is **24 accepted / 12 failed / two stopped executions; 11 accepted / one failed modeling runs; 386 completed real fits**.

**V066 is prepared, not executed:** cached source-clock adjudication, exact FBS16 reconstruction/readiness, 12 fixed linear fits against cached strict-FBS60 controls, and coverage/uncertainty evidence. It permits **zero provider calls and zero new live forecasts**. A frozen 1% operational noninferiority margin must pass development and exposed evaluation with sufficient paired-block support; no automatic promotion. Final package verification remains pending. [V066 preparation](status/football_v066/README.md).

Earlier sections preserve their dated observations. Neither a successful capture nor prepared fallback establishes prospective skill or wagering readiness.

[Overview](../README.md) · [Model card](MODEL_CARD.md) · [Architecture](ARCHITECTURE.md)

## Target scope and preserved V059–V062 coverage observations

The current V065 counts above supersede older coverage states in the table below. Future college forecasts and headline evaluation are **FBS versus FBS**. The historical FBS/FCS archive remains available as explicitly declared opponent context; no standalone FCS prediction, acquisition or repair work is planned. Prior mixed-cohort counts below remain historical coverage evidence and are not relabeled FBS-only.

| Preserved V059–V062 scope / representation state | Count | Status |
| --- | ---: | --- |
| Prior audited canonical completed FBS-vs-FBS games | 7,898 | Dated canonical snapshot, not silently relabeled current |
| FBS-vs-FBS games in frozen model table | 7,895 | Accepted features/predictions preserved |
| Current-season finals in reused current capture | 354 | 15 additional finals beyond prior current-season canonical 339 |
| V059 accepted overtime-order repairs | 8 games / 16 team rows | Runtime verified; 33 explicit overtime rows retained separately |
| V060 selected official-school sources captured | 14 / 14 | All selected source captures succeeded |
| V061 validated secondary representations | 12 / 14 | Two additional cached records validated at runtime; separate source semantics |
| Selected historical games still without validated secondary representation | 2 | Temple–UConn and Boise State–SDSU |
| Original ESPN-source gaps repaired by V060–V062 | 0 | All 14 original-source gaps remain; secondary sources stay distinct |
| V062 current official-source captures | 16 / 17 sources | Includes historical sources; capture is not validation |
| V062 current validated secondary drive representations | 13 / 15 current games | 26 team rows / 262 regulation drives |
| V062 selected remaining drive gaps | 4 | Two current plus two historical; denominators remain separate |
| Historical FBS/FCS context gaps | 6 | Deferred; no standalone FCS work |

The eight V059 repairs corrected regulation-drive auditing order. V060 then validated ten official-school secondary representations among the remaining 14 cases. Accepted model features and source bytes remain unchanged; secondary-source interchangeability is still unapproved. Do not subtract those ten and claim the original ESPN source is repaired.

V061 replayed the four previously captured cases and runtime-validated two more secondary representations, Syracuse–Purdue and Texas–UTSA, bringing accepted coverage to **12/14**. Temple–UConn and Boise State–SDSU remain. This cache-only repair made no new source request and did not alter frozen features.

V061's separate 15-game current drive queue made **one robots request**, received **HTTP 403**, saved the host stop and captured **zero current summaries**. All 15 remained unvalidated at that V061 observation. No ESPN retry or alternate access-path bypass is authorized by the next plan.

**V062 has now completed.** Its independent official-school queue captured 16/17 sources and validated 13 of the 15 current games, producing 26 team rows and 262 normalized regulation drives. The prior historical secondary coverage remains 12/14. Four selected gaps remain: LSU–Mississippi State and Boise State–SDSU PDFs failed exact quarter-score identity parsing; Rutgers–Maryland HTML retained a clock conflict; Temple–UConn's PDF host returned robots 403 before any body request. Two PDFs have extracted text but **zero verified PDF-text-only identities**. No denied source is retried or bypassed. [Actual scope and evidence](status/football_v062/README.md).

The existing six-hour college capture observed **October 17, 2026, 21:07:13 UTC** contains 354 current-season FBS finals, including 15 beyond the earlier canonical snapshot. V060 reconciled exact final scores against team/player boxes for all 15, with zero new CFBD requests. This does **not** verify current PBP/drive completeness or alter frozen historical predictions.

[Actual V062 acquisition outcome](status/football_v062/acquisition_completion.json) · [Preserved V061 acquisition outcome](status/football_v061/acquisition_completion.json) · [Preserved V060 outcome](status/football_v060/acquisition_completion.json) · [V059 accepted repair](status/football_v059/repair_completion.json).

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
| V061 current drive queue | One robots HTTP 403; zero captures at that dated observation |
| V062 official-source capture | October 18, 2026, 00:08:01–00:15:40 UTC; 16 captures, 13 validated current games |
| V062 conservative feature availability | October 18, 2026, 16:02–17:34 UTC for the 13 new representations; none eligible at run completion |

The four NFL semantic changes were PBP, weekly rosters, depth charts and player mapping. NGS passing/rushing changed compressed bytes but not normalized content; snap counts and NGS receiving reused unchanged cached digests. These are source revisions, not six new NFL games.

V060 recorded **32 public HTTP attempts**, 30 successful responses/redirects and two robots-file 404 responses. No new 401/402/403/429 provider denial occurred. CFBD requests, CBBD requests and odds credits were zero; the prior CBBD stop remains. The request count includes policy checks/redirects and does not equal downloaded dataset count.

V061 subsequently recorded one failed robots-policy request and retained the provider denial. Its models completed while acquisition remained blocked; these are separate outcomes. Paid-provider usage remained zero.

V062 recorded 33 public attempts: 30 HTTP 200 responses, two robots 404 allowances and one new robots 403 stop. Successful capture, exact validation and model-feature eligibility are separate states. The four remaining drive gaps are explicit; no current captures were inserted into the frozen benchmark.

These observation dates do not establish unknown original publication timestamps. New source captures remain separate from frozen benchmark features and do not produce live forecasts automatically.

## Information-time constraints

Historical archives may contain later corrections. Unknown publication timestamps stay null. A retrospective 24-hour outcome-release assumption does not establish strict historical point-in-time eligibility. Current injury reports, postgame usage and a target game's actual starter are not valid historical pregame features for that same game.

Availability values retain missing and ambiguous states. Missing game-day status is never relabeled “available.” A verified 2026 American Conference football availability source remains a gap; the known 2025 archive and basketball-seeded one-off do not resolve it.

The nine unresolved college availability rows represent **three players**, and **none of those rows satisfies the examined 24-hour pregame eligibility gate**. Correcting an ID alone would not make these rows valid historical pregame features.

## Highest-value next work

1. Resolve exact cached Rutgers–Maryland HTML and downloaded-PDF parser issues without new source calls or weakened identity/clock rules; keep unavailable hosts blocked.
2. Verify accepted-model serving reproduces frozen retrospective predictions before prospective use.
3. Write prospective shadow forecasts or explicit abstentions before the decision time, preserving source/model identities and eligibility. Cached captures are not eligible merely because they exist.
4. Preserve forward-only information vintages and a frozen evaluation contract; no new research fit or promoted model is part of V063.
5. Keep exact availability joins, future starter observations and tracking/video rights as distinct unconfirmed inputs. These gaps do not require another broad download or model sweep.
