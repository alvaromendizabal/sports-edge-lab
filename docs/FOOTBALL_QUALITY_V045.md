# Football identity and availability quality — v045

AWS `sports-edge-lab-football-quality-20261016-v045` completed at **2026-10-16 23:03:26.455 UTC**, after starting at 23:02:33.034 UTC. All three selected stages finished with zero failed stages; all 74 offline tests also passed in the actual AWS image before credentials/network. The application remains `completed_with_explicit_gaps` because unresolved identities and historical publication times are not invented.

## Identity results

| NFL measure | Verified result |
| --- | ---: |
| Current-season snap rows | 7,463 |
| Unique player IDs with same-week/team GSIS roster membership | 7,445 |
| Newly resolved through exact published PFR–GSIS crosswalk | 1,374 |
| Previous verified IDs retained | 6,071 |
| Conflicting crosswalk mappings removed from matched output | 4 |
| Other unresolved rows | 14 |
| Total still unresolved | 18 |

The remaining rows concern Alec Anderson, Cody White, CJ Okoye and four Peter Woods rows with conflicting PFR–GSIS mappings. Exact identities remain null until independent evidence resolves these source discrepancies. No fuzzy name matching or silent overwrite was used. V042 had already resolved all **692 current NGS summary rows** by exact team/week/GSIS joins.

The single new public download was nflverse's `players.csv.gz`: **24,854 player records, 2,501,827 bytes**, SHA-256 `78ccdebe065a691b3a11b2a8920726680af6f7393789da385dcdef51b0be0a47`. Current release metadata supplied expected size/hash; both were checked before use. The NFL roster and snap sources were reused from their verified private cache. Zero odds credits, CFBD calls and CBBD calls were used.

| College conference | Valid rows | Exact unique player IDs | Unresolved | Quarantined |
| --- | ---: | ---: | ---: | ---: |
| ACC | 800 | 750 | 50 | 1 |
| Big 12 | 434 | 429 | 5 | 0 |
| Big Ten | 715 | 677 | 38 | 0 |
| SEC | 453 | 450 | 3 | 0 |
| Total | 2,402 | 2,306 | 96 | 1 |

The ACC archive had one shifted September 19 row with a player name in the jersey column and `Out` in the name column. Its original raw data is preserved; the row is quarantined from the valid table. Missing report statuses remain null. The 528 rows with both exact player IDs and an observation before their reported kickoff are **prospective candidates**, not a completed prediction dataset. Current source archives do not prove historical publication times, and model-ready/historical-approval flags remain false.

## Failure and correction retained

V044 failed at 22:56:41.374 UTC before AWS clients, provider calls or raw downloads. Its 73 tests passed, but the entrypoint double-decoded an embedded JSON configuration; no final return ZIP was produced. V045 reads embedded bytes consistently and adds a full real-zip configuration/cache/runtime regression, including the final single-ZIP output. The failed source, logs, processing interval and estimated cost are retained separately, not replaced by this success.

V045 produced one unique **3,000-byte** ZIP with SHA-256 `b657c8a81bd3810f84a8cca3741013bddbc98134d1d6ff5cf1c001fad89a730c`; CRC and report equality were independently verified. All ten saved raw/derived output sizes were checked against S3. Run prefix: `shared/acquisition/football-quality/20261016T230312Z-4dd577ff91/`. Full table bodies remain private; sanitized evidence is in [the v045 status directory](status/football_quality_v045/).

Remaining modeling work is explicit: resolve 18 NFL snap rows and 96 college availability rows, verify original report publication times where possible, audit historical bookmaker timestamps/kickoff revisions, and construct prediction-time joins and out-of-time evaluation datasets. The selected football odds download queue is complete; these are quality and modeling gates, not undisclosed download backlog. [Weekend capture playbook](FOOTBALL_WEEKEND_REFRESH_20261016.md).
