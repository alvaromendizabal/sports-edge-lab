# Current Sports Edge Lab snapshot v026

**Deployed schedule update — October 16, 22:48 UTC:** The existing schedule now uses [v043](../current_snapshot_v043/README.md). CBBD is disabled both in planning and direct calls after the provider rate limit. The original v026 source and execution history below are retained; do not deploy its unpaused CBBD worker. V043 passed 32 tests and preserves the existing cadence, budgets, lease and end date. [Read-back evidence](../../docs/status/current_snapshot_v043/schedule_change.json).

This finite AWS acquisition captures current observations for near-term work.
It does not reuse historical observations as if they were live. Every request
has a capture vintage containing a UTC observation timestamp and unique run ID;
raw payloads remain immutable and content-addressed.

The run requests current US moneyline/spread/total odds and live/upcoming event
metadata across NFL, NBA, NCAAF, NCAAM and NCAAW. It additionally requests six
player-prop markets for at most 12 upcoming events per supported track (NFL,
NBA, NCAAF and NCAAM), prioritizing the next seven days. Events that start while
the run is working are skipped for pregame props. A current snapshot is not a
continuous market tape or an execution recommendation.

CFBD receives one fresh current-season games/calendar/roster capture, team and
player season summaries, advanced team summaries, and available current-week
box scores. Calendar rows identify the current week. CBBD receives current
season teams and three 15-day upcoming schedule slices; large slices are split
at the documented 3,000-game response cap. No offseason basketball statistics
are requested. The CBBD statistical feed is for men; women's current odds are
separate. Actual returned event dates and rows determine coverage, not the
requested season label.

The safety envelope is 500 odds credits, 100 statistics calls, 600 application
seconds and 900 recommended SageMaker seconds. Four workers share two HTTP
requests per second; retries consume the same budgets. Credentials exist only
inside AWS, retrieved from the existing SSM SecureStrings.

Before paid odds calls, a documented free event lookup must supply a current
remaining-credit header. The run subtracts the outstanding budget commitments
from the known v011 and v014 historical runs, its own 500-credit bound, and a
100,000-credit reserve floor. Missing quota evidence stops current paid odds.
Finished historical summaries contribute no outstanding commitment. Statistics
remain separately bounded. This is a conservative gate over known project jobs,
not an account-wide ledger for unrelated external API use.

A shared S3 lease prevents overlapping current collectors. Creation uses
IfNoneMatch; expired takeover and release use matching ETags. The lease expires
after 1,200 seconds, beyond the 900-second AWS job bound. A failed conditional
release leaves the expiry intact and never unconditionally deletes another
owner's lease. An SDK lacking conditional-write support fails before provider
HTTP. Authentication, permission, quota and rate denials stop that provider.

Reports at `shared/acquisition/current/<run-id>/` include capture timestamps,
event dates, bookmaker quote times, empty/nonempty responses, events with actual
market outcomes, usage headers, cost estimates and a freshness audit. Exactly
one unique return ZIP contains receipts, failures, summary and that audit.
Thirty self-tests run on AWS before credentials or downloading. These gates
do not approve current/postgame statistics as historical pregame features.

Primary documentation checked 2026-10-16:

- https://the-odds-api.com/liveapi/guides/v4/
- https://api.collegefootballdata.com/api/games
- https://api.collegefootballdata.com/api/stats
- https://api.collegefootballdata.com/api/teams
- https://api.collegebasketballdata.com/api/games
- https://api.collegebasketballdata.com/api/teams
- https://docs.aws.amazon.com/boto3/latest/reference/services/s3/client/put_object.html

This isolated engine adds a current-cost override and current report prefix;
previous historical collectors remain unchanged.

## Verified first execution

AWS run `20261016T195042Z-de7c4fb55a` passed all 30 tests and finished at
2026-10-16 19:51:39 UTC with 58 captures, zero failures, and 39,917,293 raw
response bytes. Usage was 176 odds credits and 12 statistics calls. The
conditional lease was released with its matching ETag.

| Current game markets | Events with outcomes |
| --- | ---: |
| NFL | 24 |
| NBA | 46 |
| NCAAF | 73 |
| NCAAM | 0 |
| NCAAW | 0 |

Of 36 current prop responses, 31 contained outcomes: NFL 12/12, NBA 8/12 and
NCAAF 11/12. No NCAAM prop events were available in the selected window.
These counts describe returned snapshots, not complete bookmaker coverage.

CFBD returned 3,679 current-season game rows, including 1,937 marked completed
and 1,738 future scheduled games; the response also included 31,479 roster rows
and 134,672 player-statistic rows. Statistic rows are not unique players.

CBBD returned 365 team rows. The upcoming schedule slices contained 701 and
634 rows spanning November 1–29, 2026; the October 16–31 slice was empty. These
are future schedules observed in October, not completed 2026–27 game data.
Inclusive slice boundaries require game-ID deduplication before combining rows.

The AWS receipt did not record exact boto3/botocore package versions. The
execution used the configured SageMaker scikit-learn image and verified real
conditional S3 writes. CI installs boto3 for offline mocked ClientError/lease
tests; CI success is separate from the recorded AWS acquisition evidence.

