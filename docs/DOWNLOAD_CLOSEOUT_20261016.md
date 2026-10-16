# Download status and finite collection scope — October 16, 2026

AWS verified at **20:59:34 UTC / 1:59 p.m. Pacific**: the only nonterminal Sports Edge Lab acquisition job is historical backfill v011, still **Stopping** after the 20:36 UTC stop request. AWS has not supplied ProcessingEndTime. Its latest saved application progress is **20:48:56 UTC** and did not advance between the two checks in this update. Continued transfers after that checkpoint are unverified. Odds-only v038 does not exist and must not launch until the predecessor is terminal. No CBBD restart is authorized by this update.

The latest content census remains **93,319 in-scope raw files / 17,259,029,672 bytes**, measured 20:36–20:37 UTC. It already excluded ACB. This is a measured archive observation, not a count of unique games or a current atomic storage total.

| Collection | Captured or processed | Work remaining in that specific plan |
| --- | --- | --- |
| Current NFL play-by-play | 14,031 plays, all 80 completed schedule games through October 15 | 0 missing completed game IDs at capture |
| Recent NCAAF FBS detail | 124 completed games, 22,151 plays and 2,888 drives in Weeks 5–7 | 0 missing game IDs in these windows; nested record completeness still needs validation |
| Selected weather backfill | 440 forecast initialization/lead pairs | 0 planned pairs |
| College shooting recovery | 1,294 queries processed, including 958 cache reuses | 0 planned queries; 38 valid-empty responses |
| Historical game odds v011 | 31,554 of 75,481 missing checkpoint requests processed successfully (41.8%) | **43,927 requests** at the 20:48:56 checkpoint |
| CBBD plays/lineups/substitutions v011 | 10,760 of 40,294 requests processed, 10,524 successful | **29,534 unprocessed + 236 failed**; stop requested after rate limiting |
| Historical player props v014 | Run ended at its authorized credit cap | **51,624 pending** in its saved plan; no continuation running |

These denominators are different datasets and request plans. They cannot be combined into a meaningful overall completion percentage. The complete planned jobs do not establish every possible season/source is collected.

Historical odds remainder by track can be reconciled from v011's planned counts and per-track capture counters, subtracting one new daily census per track and the 10,524 CBBD captures from NCAAM: NFL 0, NCAAW 0, NCAAF **4,697**, NBA **11,692**, NCAAM **27,538**. These are inferred checkpoint remainders, not a new request-index census. V038 must rebuild its missing set from successful indexes before issuing requests.

The authorized v038 follow-up is capped at 200,000 subscription credits, 1 request/second and 1,800 application seconds, with zero college-statistics requests. It cannot finish 43,927 requests in one run: the rate limit alone implies roughly **12.2 hours** for that full remainder, before storage/network overhead, provider restrictions and quota checks. No completion ETA is promised while AWS termination and provider availability are unresolved.

## ACB removal

Removed **124 S3 objects/versions totaling 395,102,517 bytes**: all ACB raw payloads, URL indexes, acquisition evidence/reports/return ZIP, and the v029 executable. Post-delete listing verified zero current objects, versions, delete markers and multipart uploads at all three dedicated prefixes. The dedicated CloudWatch log stream was also deleted and verified absent. The current repository removes its collector, manifest, license, dedicated receipts and CI invocation. Local dedicated source/sample copies are removed. Earlier Git history and mixed audit totals are retained as historical records; no ACB data remains an active project input.

## Recommended endpoint for broad collection

Use the existing archive now for NFL/NCAAF baseline development. Freeze expansion of historical acquisition to explicit missing game/market records needed by a defined evaluation set. Do not make all basketball lineups, all historical props or vendor tracking prerequisites for the first football model.

Recommended next download priority:

1. **Current NFL/NCAAF availability and roster changes:** original report versions when released, quarterback/depth-chart changes, publication/retrieval timestamps and stable player IDs. Existing 32-team NFL pages and partial Big Ten coverage are starting points; SEC and other conference coverage remain gaps. Validate existing pages before requesting duplicates.
2. **Missing NCAAF game odds for the selected football evaluation period**, starting with the 4,697-checkpoint remainder after a fresh cache reconciliation. NFL's v011 checkpoint plan is already processed. The existing bounded v038 continuation remains unchanged; this recommendation does not silently enlarge its limits or claim it will finish the football subset.
3. **New-game updates only:** odds quotes before kickoff, final availability, then completed-game play-by-play/boxes. Future reports and games cannot be downloaded ahead of publication. Existing six-hour current snapshots and the American Conference one-off are future updates, not unfinished historical downloads.

After those items, concentrate on identity joins, deduplication, timestamp validation, venue-level weather extraction and dated train/test tables. Those are data preparation tasks, not reasons to keep buying or downloading more data. NBA/NCAAM/NCAAW remain supported tracks; their optional historical enrichment is separately tracked. Tracking and aligned-video access for the five tracks remains unverified and is not a prerequisite for the initial football baselines.

## Evidence

- [Fresh AWS status and saved progress](status/download_observation_20261016T2059Z.json)
- [ACB removal verification](status/acb_removal_20261016.json)
- [Football content and limits](FOOTBALL_READINESS_20261016.md)
- [Guarded odds-only continuation](ODDS_RESUME_V038.md)
- [Historical props final receipt](status/props_final_20261016.json)
