# Paid data acquisition

`acquire_paid_data.py` runs in the Sports Edge Lab AWS environment in `us-west-2`.
It starts three concurrent workstreams: five-sport odds, college football, and
men's college basketball. Provider keys are resolved only inside the runtime from
SSM SecureString parameters. Keys, authenticated URLs, HTTP error bodies, and raw
exception messages are never logged or placed in the public repository.

## Scope

| Track | Paid source | Initial coverage strategy |
| --- | --- | --- |
| NFL | The Odds API | Daily historical census from June 6, 2020; event-derived checkpoints |
| NBA | The Odds API | Daily historical census from June 27, 2020; event-derived checkpoints |
| NCAA football | The Odds API + CFBD | Odds from June 6, 2020; statistics from 2000 |
| NCAA men | The Odds API + CBBD | Odds from November 16, 2020; statistics from ending-year season 2003 |
| NCAA women | The Odds API | Odds from November 12, 2024; statistics acquired by the public-source runner |

Historical odds requests use US bookmakers and `h2h,spreads,totals`. The first
phase samples 12:00 UTC each day, interleaving sports and prioritizing recent
dates. It discovers events and kickoff timestamps. The second phase requests
deduplicated timestamps 72 hours, 24 hours, 6 hours, and 15 minutes before those
kickoffs. Neither phase proves that every historical game or bookmaker has
coverage. Schedule revisions, bookmaker timestamps, and returned snapshot age
must be audited before a betting backtest uses the archive.

CFBD acquisition includes annual games, lines, records, rankings, team/player
statistics, advanced statistics, ratings, PPA, recruiting, transfers, draft,
rosters, talent, coaches, and player usage/returning information, then weekly
plays, drives, team/player game statistics, and advanced game statistics.

CBBD acquisition includes annual statistics, shooting, ratings, rankings,
rosters, recruiting, transfers, and draft information. Games, team/player box
scores, and historical lines use monthly date slices with recursive splitting
when an API cap is reached. Daily plays and recent game lineups/substitutions
follow within the available budget. CBBD applies to the men's track.

## Bounded operation and accounting

Default limits are 1,000,000 Odds API credits, 15,000 combined CFBD/CBBD calls,
and 6,900 seconds. The processing job should have a 7,200-second AWS runtime
limit. These are per-execution budgets; launch one acquisition execution at a
time. The program rejects larger limits for this milestone.

The Odds API usage headers reconcile a conservative 30-credit reservation per
request. Missing usage headers retain the reservation. A shared, synchronized
counter bounds college-statistics calls. HTTP authentication failures stop that
provider, and endpoint-specific access errors are recorded. Every execution
runs its offline test gate before accessing AWS.

Thirty-second heartbeats include progress, usage, and estimated compute cost.
The estimate excludes subscriptions, S3 storage, and API request charges.
Raw response objects use content hashes, gzip, and private server-side-encrypted
S3 storage. Request receipts retain sanitized parameters, retrieval time,
response hashes, row counts, and usage headers. Completed historical requests
are reused from the remote cache; current-season data receives daily captures.
Failed responses never create a success cache entry.

One compact return ZIP is produced per execution. Authoritative metadata is at
`shared/acquisition/paid/<run_id>/`, with raw data under
`tracks/<track>/raw/<provider>/`.

## Data restrictions and remaining gates

Raw paid datasets remain private. Acquisition does not grant redistribution
rights. Final ratings, postgame statistics, realized weather, and historical
corrections are not automatically pregame features. Timestamped feature
construction and season-by-season completeness audits are separate gates.

The base runner does not acquire player props; the companion runner below handles
that separate bounded workload. Other bookmaker regions, a complete intraday
quote tape, feature training and proven market advantage are not delivered by
these acquisition runs. Empty responses and HTTP success are recorded without claiming full
data coverage.

## Verification

The v002 runner includes 15 offline self-tests. Three additional integration tests
exercise successful archival and remote-cache replay, hash mismatch rejection,
provider authentication failure, and credential exclusion. They use synthetic
credentials and in-memory fake services; production network and AWS validation
occur in the actual processing job.

The launched v001 source is preserved as
[`tools/history/acquire_paid_data_v001_launched.py`](../tools/history/acquire_paid_data_v001_launched.py).
See [execution source versions](EXECUTION_SOURCE_VERSIONS.md) for exact hashes.
Its nonblocking CBBD shooting-stat requests omitted a required conference/team
selector. V002 recovers those requests using distinct conferences from archived
team-season statistics, with team-level fallback for unaffiliated teams. It
reuses successful archived requests. No running job was altered.

## Additional player-prop runner

`acquire_player_props.py` imports `acquire_paid_data.py`; deploy those two files
together. It reads the existing `discovered-events.json` and refreshes it while
the base archive grows. It never calls a paid event-discovery endpoint.

The additional run reserves no more than 500,000 credits across all four supported
tracks, with a 6,900-second application limit. It attempts 24-hour, 6-hour, and
15-minute checkpoints from May 3, 2023 at 05:30 UTC onward. Latest games are
prioritized with leagues interleaved. The six-market request reserves 60 credits
for one US bookmaker region and reconciles the actual unique returned-market
charge from provider headers.

Football requests passing yards, passing TDs, rushing yards, receiving yards,
receptions, and anytime TDs. Basketball requests points, rebounds, assists,
threes, blocks, and steals. The league/market combinations are documented by
The Odds API, but this does not guarantee every market existed historically for
every event. NCAA women's player props are excluded.

Every response also receives an audit of event identity, kickoff revisions,
snapshot time, quote-update times, and returned market/outcome counts. Even
consistent timestamps do not replace participant mapping, settlements, and
availability audits. It includes 19 automatic tests (15 shared plus 4 props).

Official references:

- https://the-odds-api.com/liveapi/guides/v4/
- https://the-odds-api.com/historical-odds-data/
- https://api.collegefootballdata.com/api/games
- https://api.collegefootballdata.com/api/plays
- https://api.collegebasketballdata.com/data-availability
- https://api.collegebasketballdata.com/api/games
- https://api.collegebasketballdata.com/api/plays

## Targeted shooting-stat recovery

[`recover_shooting.py`](../tools/recover_shooting.py) fills the optional CBBD shooting-stat gaps caused by the original unfiltered season requests. It imports the current v002 base collector and derives conference/team selectors from team-season responses already cached in S3. It does not repeat paid discovery or redownload the successful base archive.

The runner is restricted to the team/player season shooting endpoints, at most 2,000 additional statistics calls, 500 application seconds and four workers. The corresponding Processing runtime ceiling is 600 seconds. Missing source seasons remain pending while the base job progresses; current-season cache identity includes its capture day. Eighteen automatic tests cover the shared base and recovery-specific limits, selector deduplication and cache identities.

A submitted recovery job is not evidence that every failed query has been filled. Its actual capture counts and any remaining gaps belong in the operational ledger after execution.
