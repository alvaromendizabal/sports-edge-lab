# Data freshness and access — current update

**Latest update, October 16 at 20:59 UTC:** ACB data and its collector have been deleted. V011 remains Stopping; v038 has not launched. [Current backlog, removal evidence and collection endpoint](DOWNLOAD_CLOSEOUT_20261016.md) supersede older status observations below.

## Fresh football data captured this turn

| Source | Verified content | Actual data recency |
| --- | --- | --- |
| NFL public play-by-play | 14,031 rows, 80 games; all 80 completed games in the current schedule have PBP; no unmatched game IDs | Game dates through October 15, 2026; downloaded at 20:34 UTC October 16 |
| Direct CFBD FBS plays and drives | 22,151 plays and 2,888 drives across 124 completed games in Weeks 5–7; every completed FBS schedule game in those windows has plays, drives, team/player box and advanced-stat rows | Latest covered kickoff October 16, 00:00 UTC, corresponding to Thursday evening in the US; downloaded 20:31–20:32 UTC |
| Current game markets | 24 NFL, 74 NCAAF and 46 NBA events with outcomes; 32 populated player-prop responses across these tracks | Fresh observation 20:22–20:23 UTC; provider quote times remain distinct |
| Big Ten football availability | 715 normalized player-status rows across 64 team-games; 154 rows across 14 team-games for October 16–17 | Public rendered archive observed October 16; source publication timestamps unavailable |
| NFL official roster/injury pages | All 32 team roster pages, plus Week 6 injury and schedule pages | Earlier same-day capture; structured extraction and report-time audit remain pending |

The CFBD job made 21 subscription-quota requests, with no failures, and also
captured current player usage and three weekly game-weather responses. The
current odds/statistics snapshot made 58 successful captures using 178 odds
credits and 12 statistics requests; five responses were empty. NCAA men's and
women's current odds remained empty. These counters represent subscription
allowances, not separately purchased API calls or dollar charges.

The Big Ten capture is a **rendered-page extraction**, not an original PDF or
an archive of verified publication-time versions. Four rows with ambiguous
missing columns were preserved in raw extraction and quarantined from the
normalized table. A missing game-day status stays null, never "available".
Player identity joins and historical point-in-time eligibility remain unverified.
SEC discovery did not yield downloadable report links; it is still a gap.

CFBD game-box endpoints also returned non-FBS games; they are retained in raw
responses but excluded from the 124-game FBS coverage denominator. Matching
game IDs proves game representation, not that every play or nested player
statistic is complete. Fresh postgame statistics are not pregame features for
their own games.

## Continuations and completed backfills

- **Weather v030 completed:** all 440 planned forecast initialization/lead
  pairs for the selected 2024 football scope are processed; 1,037 new GRIB
  fields were downloaded. The final inventory has 2,640 forecast fields and
  1,438 NWS JSON objects. This is not all historical weather or a validated
  venue-level feature table.
- **Shooting v032 completed:** 336 new responses and 958 cache reuses processed
  all 1,294 planned queries. Across that plan, 1,256 responses had records,
  38 were empty and 88,554 summary rows were observed. Zero planned queries
  remain; those totals include reused data.
- **Historical v011 stop requested after repeated CBBD HTTP 429:** AWS still reported Stopping at 20:44 UTC. At the preserved
  20:35:20 UTC checkpoint it had 37,443 captures, 70 final request failures and
  351 retry incidents. The checkpoint is not a final stop-time count. Existing
  successful payloads and indexes remain available.
- **Odds-only v037 failed before provider calls:** its worker role lacks
  SageMaker DescribeProcessingJob permission. Zero API requests/credits were
  consumed, and its return ZIP was saved. V038 removes this worker-side
  management API call and instead requires an embedded control-plane receipt
  proving v011 has terminated. V038 is prepared, not launched while v011 is
  still Stopping. Its limits are no college-statistics requests, one source
  request per second, 200,000-credit ceiling, 30-minute application limit and
  35-minute AWS limit. It requires v011 to be terminal, checks the live quota
  reserve and stops its provider on 401/402/403/429. Its budget fits within the
  unused v011 odds ceiling. No resumed historical acquisition is claimed until a successful runtime
  receipt exists.

A bounded follow-up is enabled for **2, 3 and 4 p.m. Pacific today** to verify
AWS termination and launch at most one v038 odds-only job, then check its
result. It does not restart CBBD. This is a scheduled follow-up, not a claim
that the historical restart is already running.

The existing six-hour current snapshot schedule remains configured, with its
first scheduled execution at **October 17, 03:05 UTC (8:05 p.m. Pacific today)**.
It refreshes current odds/stats; it does not continuously refresh every raw
football play or conference report. The American Conference availability
one-off remains scheduled for **October 17, 01:05 UTC (6:05 p.m. Pacific)**;
future captures are not counted as downloaded. This turn did not change either
schedule or create a new data subscription.

## What we still need, in priority order

1. **Prediction-time football tables:** reconcile team/player/game identities,
   validate every play schema, and join only prior-game performance to upcoming
   games. Build dated NFL/NCAAF evaluation sets before claiming a usable edge.
2. **Reliable current availability:** original NFL and NCAA report versions,
   publication timestamps, quarterback/depth-chart changes and cross-conference
   coverage. The Big Ten extraction is useful partial coverage; SEC and other
   conferences remain open. Archive final game-day updates when published.
3. **Historical market gaps:** finish missing game-price checkpoints and audit
   quote times and kickoff revisions. The odds-only continuation preserves
   existing request indexes. CBBD details are paused after rate limiting.
4. **Tracking and aligned video for the five target sports:** vendor access,
   export scope, history/current latency and modeling rights are still
   unconfirmed. Previous SkillCorner/Genius inquiries are recorded; a targeted mailbox check at 20:43 UTC found no new replies from those
   provider domains today. No new license was purchased. ACB is out of scope.
5. **Basketball-specific gaps:** complete CBBD plays/lineups/substitutions after
   the provider limit clears; current NBA injury versions; women's current
   schedules, availability and market coverage. Shooting's specified recovery
   plan is complete, not every possible historical query.
6. **Weather feature readiness:** extract venue values from archived forecast
   fields and verify historical availability times before using them in backtests.

We have substantial data for initial NFL/NCAAF baselines. Frontier modeling
still requires stronger identity, sequence, availability and temporal
validation; download volume alone does not establish frontier performance.

[Exact current inventory and evidence](FOOTBALL_READINESS_20261016.md).
