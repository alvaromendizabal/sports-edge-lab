# V065 — current FBS source comparison and forecast accounting

**Completed October 18, 2026, 02:02:55 UTC.** Four stages succeeded, 495 runtime tests passed and an independent actual-return audit passed 2,743 checks. V065 made one confirmed CFBD request, zero real fits, zero new forecasts and zero model promotions. [Sanitized actual execution](actual_execution.json).

## What was captured and validated

The successful current-season response contains **11,405 source records across 489 games**. Strict normalization retains **393 games / 786 team rows: 291 FBS-versus-FBS games and 102 declared opponent-context games**. The intermediate 475-game normalizer count precedes whole-game quarantine and is not accepted coverage.

| Against the complete primary reference | All declared games | Strict FBS games |
| --- | ---: | ---: |
| Required reference inventory | 455 | 336 |
| Exact metric matches | 308 | 226 |
| Unequal metrics | 81 | 61 |
| Missing accepted comparisons | 66 | 49 |

All 49 missing strict-FBS comparisons are represented in the source but quarantined; they are **not missing downloads**. In total, 99 invalid rows affect 82 games: 31 backward-period rows and 68 invalid eligible drive/team/result rows. Entire affected games remain excluded. A further 324 rows across 14 games remain in raw captures because the unchanged canonical schedule did not mark those games completed. Four additional strict-FBS games have independently normalized metrics.

**No model inputs were replaced. FBS60 remains blocked.** A fresh source capture does not prove semantic equivalence, complete canonical coverage or historical pregame information availability. Source publication remains unknown.

## Preserved forecasts and execution evidence

The original 192-record ledger remains byte-identical: six issued NFL records for two games and 186 abstentions. All six issued records are pending. No outcomes matured, so there are no new prospective scores. Actual original leads remain distinct from the minimum issuance cutoff; individual forecast values are not published here.

The report executed six code cells and retained verified Plotly MIME and HTML. The unique return had 215 CRC-clean members. Actual runtime was 61.951 seconds; estimated active compute was $0.008329 at the assumed $0.484/hour, excluding idle/startup, storage and request charges. Browser inspection and verified billing are not claimed.

Verified minimum tally: **24 accepted / 12 failed / two stopped executions**; modeling **11 accepted / one failed**; **386 completed real fits**. Accepted execution means the declared work completed, not that a model improved.

## Preserved preparation and next decision

[Original preparation receipt](preparation.json) and [earlier owned-cache comparison](owned_source_comparison.json) retain their pre-execution observations. Their 110-game retained overlap is historical and superseded for current-source coverage by the actual result above.

[V066 preparation](../football_v066/README.md) tests a score/schedule-based 16-feature strict-FBS fallback while adjudicating cached source inconsistencies. It permits no provider calls or new live forecasts. [Public pure methods](../../../modeling/football_v065/README.md) · [Model card](../../MODEL_CARD.md).
