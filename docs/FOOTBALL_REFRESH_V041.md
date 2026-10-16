# Football refresh and NGS joins — October 16, 2026

V041 completed at **22:22:53 UTC (3:22:53 p.m. Pacific)**. Its nine selected
tasks were processed with zero request failures and zero remaining tasks.
The recorded application result is `completed_with_gaps`, because the SEC
export was quarantined and some exact player-ID joins remain unmatched.
AWS `Completed` is not a claim of complete sports or season coverage.

## Downloaded and derived

| Dataset | Saved coverage | Freshness and limitations |
| --- | --- | --- |
| 2026 NFL snaps | 7,463 player-game rows, 80 regular-season games, 32 teams | Upstream October 16, 11:04 UTC; 93 rows in available Week 6 game. Game-set completeness is not separately asserted by this run. |
| 2026 weekly rosters | 15,327 rows, 32 teams; 2,279 Week 6 rows | Upstream October 16, 12:22 UTC; seven rows lack GSIS IDs. |
| 2026 depth charts | 659,277 archived snapshot rows; 2,305 latest rows, 32 teams | Latest source snapshot October 16, 12:16:59 UTC; five latest rows lack GSIS IDs. Snapshot load time is not original publication time. |
| ACC availability | 801 rows, 64 team-games, 17 teams | 177 rows / 14 team-games for October 16–18; zero rejected/duplicate identities. Parsed the existing raw table after independently verifying its nine headers. |
| Public NFL Next Gen Stats | Existing 27,613 passing/rushing/receiving rows from 2016–2026 retained | All three upstream hashes unchanged. Reused verified S3 copies; zero repeat NGS downloads. These are player-week/season summaries, not full player/ball trajectories. |
| FTN 2026 charting | Existing 175,862-byte Parquet retained | Upstream October 14 revision unchanged; verified cached hash, no repeat download. |

The three newly downloaded NFL assets total **13,447,614 bytes**. Independent
public requests use three workers with at most two starts per second. The paid
odds job retains its independent one-request-per-second policy. V041 made
**three public asset requests, zero paid-provider requests and zero subscription
credit use**. Neither CBBD nor any other college-statistics endpoint was called.

### Exact identity joins

Only current 2026 REG rows with positive weeks were selected from NGS for the
new roster joins. Counts below do not describe all 27,613 historical rows.

| Join | Exact matches | Unmatched | Total |
| --- | ---: | ---: | ---: |
| NGS passing → same season/week/team/GSIS roster | 158 | 5 | 163 |
| NGS receiving → same season/week/team/GSIS roster | 356 | 13 | 369 |
| NGS rushing → same season/week/team/GSIS roster | 153 | 7 | 160 |
| Snaps → same season/week/team/PFR ID → GSIS roster | 6,075 | 1,388 | 7,463 |

Unmatched records are retained with explicit join status. Names were not
fuzzily matched and ambiguous identities were not guessed. Resolving the
remaining identities and validating feature timestamps are still required
before claiming these tables are ready for historical evaluation.

## SEC recovery after V041

V041 correctly preserved the original export as raw-only: it declared 301
rows but contained 453. A second automated narrative claimed 241. Both summary
counts were rejected. At **22:24:23 UTC**, direct read-only DOM extraction of
the visible official SEC archive counted exactly **453 nine-cell rows**.

Column and chunk hashes located 254 em-dash substitutions and one transcription
error: row 374 (zero-based) rendered `Shamurad Umarov`, while the export read
`Shamourad Umarov`. After restoring the observed values, the entire canonical
table matched the direct DOM SHA-256:

`9d5c60c2249b1c6404d86b5d8263c485eb04b66db1664574024828ec686bae21`

Canonicalization uses compact UTF-8 JSON arrays and removes only the leading
`#` from the Number column. All other canonical cells match rendered text.
The SHA implementation passed the standard `abc` known-answer test. The
separate recovery utility passed eight offline tests, verifies the original
S3 raw hash and full DOM parity, and leaves the original export and V041 report
unchanged.

The verified SEC dataset has **453 rows, 66 team-games and all 16 teams**, with
**127 rows across 14 team-games for October 16–18**, zero rejected rows and zero
duplicate identities. It is saved in the canonical bucket under:

- `tracks/ncaaf/raw/sec-availability-rendered/verified/20261016T222423Z/capture.json.gz`
- `tracks/ncaaf/derived/sec-availability/20261016T222423Z/rows.jsonl.gz`
- `shared/acquisition/sec-verification/20261016T222423Z/`

This is the rendered current archive, not original report PDFs or a certified
complete historical season. Missing statuses stay null. Original publication
times and player identity joins remain unverified. The recovery utility itself
made zero provider calls; the earlier browser capture/verification is separate.
No additional SageMaker job was launched for this cached-data recovery.

## Execution proof

- Job: `sports-edge-lab-football-refresh-20261016-v041`, `us-west-2`.
- Run: `20261016T222233Z-3d51c4585a`.
- AWS start/end: `22:21:59.856` / `22:22:53.325 UTC`.
- **46 tests passed locally in the deployed artifact and again inside AWS
  before runtime credentials/network.** Runtime logs confirm all nine tasks.
- Existing bucket, execution role, image and one `ml.m5.2xlarge` instance;
  no IAM changes. No application timer; existing AWS maximum 432,000 seconds.
- Artifact: 32,910 bytes; SHA-256
  `d5c023c1957585781c52dc3f727715a07bbe39f3710272adef748c5fd019178e`.
- Artifact key:
  `infrastructure/code/football-refresh-20261016-v041/sports_edge_lab_football_refresh_v041_20261016.pyz`.
- Report prefix:
  `shared/acquisition/football-refresh/20261016T222233Z-3d51c4585a/`.
- Exactly one V041 return ZIP: 5,787 bytes; SHA-256
  `89bfed21a193dbef9916eebc15367414a09743043432f9a535ab1b70bbf39ca3`.
  Its `report.json` was read and compared with the S3 report. All 16 referenced
  raw/derived object keys were checked in S3.
- Separate SEC recovery checkpoint ZIP: 15,399 bytes; SHA-256
  `1b20ad31a3bbd9a5d2357fe3d3470bc274332d51e213bb7900d4c048b3ab9e3d`.
  All five recovery outputs were uploaded and their S3 size/ETag verified.
- The AWS-reported 53.469-second processing interval implies approximately
  **$0.00685 compute** at the previously verified $0.461/hour rate. This is an
  interval estimate, excluding S3, discovery tooling and unreported service
  overhead, not a reconciled bill. Source API credits used: zero.

## Still downloading

V039 is unchanged and running. At **22:29:33 UTC**, it had saved **3,673 of 4,696**
missing historical NCAAF US game-price checkpoints, leaving **1,023**. Its frozen
NFL checkpoint plan had no uncached requests. It recorded zero final failures,
two retryable incidents, **110,190 known odds credits** and a 60-credit unknown
charge reserve. The last provider header showed 2,105,046 account credits
remaining. These are subscription allowance counters, not dollar charges.
V039 keeps its 200,000-credit ceiling, live reserve and provider-denial stops.
There is no short application timer. Its existing monitor remains enabled;
no replacement job or additional automation was created.

## What is next

1. Finish V039 and reconcile its final selected-queue count and timestamp
   coverage. New current games are separate from that frozen historical plan.
2. Use the saved NFL/NCAAF play-by-play now to build dated baseline datasets;
   resolve the exact-ID gaps above and validate pregame information times.
3. Capture final weekend availability revisions and subsequently published
   games. Existing six-hour current odds/statistics and American availability
   schedules are retained; they do not refresh every football source.
4. Full player/ball tracking and aligned video remain an access/license gap.
   Public NGS summaries do not grant access to underlying trajectories. No new
   SkillCorner/Genius reply was found in today's targeted mailbox check at
   22:17 UTC. No license/subscription purchase or outreach was performed.
5. NBA/NCAAM/NCAAW have substantial archives, but their historical odds,
   availability and detailed statistics need separate coverage audits. CBBD
   remains stopped after rate limiting; it was not resumed. ACB is excluded.

The prior full inventory remains **93,319 raw content files / 17.26 GB as of
20:36–20:37 UTC**. It predates these additions and is not relabeled as a fresh
total. Data volume does not establish complete coverage or predictive quality.

Sources: [nflverse release assets](https://github.com/nflverse/nflverse-data/releases),
[nflverse update schedule](https://nflreadr.nflverse.com/articles/nflverse_data_schedule.html),
[official SEC archive](https://www.secsports.com/fbreports-archive).

Machine-readable evidence is under `docs/status/football_refresh_v041/` and
`docs/status/sec_verification_20261016/`. Collector code and tests are under
`tools/football_refresh_v041/`.
