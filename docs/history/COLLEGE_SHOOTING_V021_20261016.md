# College shooting continuation v021

This bounded AWS run continues the 500-second v010 shooting recovery, which
captured 903 team/player summaries, recorded 12 failed requests, and still had
nine seasons waiting for the main collector's team-stat source cache. The main
collector subsequently finished all 25 team-stat season requests. This runner
loads those existing source caches, verifies their hashes, builds a frozen plan,
and requests only missing shooting breakdowns. It never repeats the main
collector's plays, lineups, substitutions, or odds work.

The scope is `/stats/team/shooting/season` and
`/stats/player/shooting/season`, with a season and one conference/team filter.
Seasons 2004 and 2005 are excluded because the provider documents no underlying
shooting plays. The remaining source scope is 2003 and 2006–2027. A returned
empty list records missing coverage; it does not establish zero shooting.
Shot coordinates are delivered inside the separate play-by-play workload,
not by these season-summary operations.

Existing successful v010 request identities are seeded from its immutable
receipt list. The per-request S3 index also checks for successful captures from
any other run before an API call. Historical identities remain stable; the
current season uses the same daily-vintage policy as previous collectors.
Unavailable source caches remain explicitly pending; no paid discovery is used.

Limits: 10,000 statistics HTTP call reservations; zero odds credits; 6,900
application seconds; 7,200 recommended SageMaker seconds; four workers; a shared
two-request-per-second limiter. Every retry consumes the same call budget.
HTTP 401/402/403/429 disables CBBD for this run. API credentials are retrieved
from the existing SSM SecureString inside AWS and never included in output.
No new credentials or subscriptions are created.

The PYZ runs its test gate before any credentials or acquisition. It preserves
immutable raw captures, per-request receipts and indexes, a frozen shooting
plan, 30-second progress/cost heartbeats, and exactly one uniquely named return
ZIP. The return contains summaries, receipts, and failures; private raw payloads
stay in S3. Source and runtime verification are separate: local compilation
checks syntax; AWS performs all self-tests and live acquisition.

Season shooting summaries are retrospective postgame aggregates. They are not
approved for pregame features. Conference filters, sparse historical records,
missing shooter attribution, and source response limits still require coverage
assessment before modeling.

Primary references checked on 2026-10-16:

- https://api.collegebasketballdata.com/api/stats
- https://api.collegebasketballdata.com/data-availability

The acquisition role, canonical region, bucket, project, and shared development
space remain those of `sports-edge-lab`.
