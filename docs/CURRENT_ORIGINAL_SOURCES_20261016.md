# Current original-source snapshot acquisition

## Freshness already established

The public archive delta finished at 18:15:58 UTC on October 16, 2026. It added
19 changed source assets (44,710,821 bytes); these are revisions, not 19 new
datasets. Re-downloading that entire archive now would repeat completed work.

Current National Weather Service forecasts covered all 728 selected venues by
18:54:32 UTC. The v027 task does not repeat those captures within two hours.
The NOAA historical forecast expansion is a separate archive acquisition and
does not represent today's weather.

The official NBA injury-document batch finished at 18:42:51 UTC: 23 new PDFs
and one reused PDF, spread across a sparse historical sample. This is not a
current complete NBA injury feed. Its discovery request to `official.nba.com`
received HTTP 403 in AWS. This collector does not retry that host or use an
alternate hostname. No exact October 16 NBA injury PDF was observed in the
current research, so no timestamp-based filenames are generated.

## v027 current NFL scope

The new collector requests three observed official source URLs:

- https://www.nfl.com/injuries/league/2026/reg6
- https://www.nfl.com/schedules/2026/by-week/week-6
- https://www.nfl.com/teams/

The team directory provides actual team-profile links. Each profile must
provide an actual same-team roster link before that roster can be requested.
There is no constructed roster URL, historical date enumeration, or fallback
to another host. The maximum is one injury page, one current-week schedule
page, and 32 roster pages. Directory, profile, and robots documents are
discovery evidence rather than injury/roster/schedule dataset counts.

Direct research requests to the injury page and Denver team profile both
returned HTTP 200. These development-environment research canaries are not
included in AWS acquisition totals. Runtime outcomes are authoritative.

At runtime, the collector checks the official robots policy, waits at least
one second between requests (or longer if required), disables redirects,
and stops after 401, 403, or 429. It rejects unapproved paths, challenge pages,
wrong-season roster/report titles, and missing roster/injury tables.

Bounds: 600 application seconds, 720 AWS seconds, 120 source requests,
50,000,000 source bytes, and 32 teams. It uses no credentials or paid APIs.
Fourteen self-tests must pass in AWS before acquisition, including a mocked
complete run, exactly one return ZIP per run, and cache-aware same-vintage
resumption. The manifest contains the executable hash and argument array.

## Provenance and inventory

Raw report, roster, and schedule HTML is stored privately at
`tracks/nfl/raw/nfl-official-current/objects/{sha256}.html.gz`.
Directory/profile/robots evidence is stored separately at
`shared/acquisition/nfl-official-current/evidence/objects/{sha256}.txt.gz`.
Exact URL, document kind, and hourly UTC capture vintage identify request
receipts. Content hashes retain immutable bodies, including earlier versions
of mutable source pages. The final report, progress, and unique return ZIP
live under `shared/acquisition/nfl-official-current/{run_id}/`.

`captured_at` records acquisition. `capture_vintage` identifies the requested
hourly snapshot. Source `Last-Modified`, HTTP date, title, and table count are
recorded independently. These are not validated injury-event, transaction,
publication, or game timestamps. Player/game extraction and identity joins
remain pending, and `point_in_time_approved` stays false.

## Other investigated sources

The NBA's official 2026–27 schedule release links three schedule PDFs. Their
static-host `/wp-content/uploads/` path is disallowed by its current robots
policy, so the collector excludes those files. This is distinct from the
permitted NBA injury PDF path used previously.

The NCAA availability work remains separate: the previously prepared American
Conference sample is scheduled within its source's permitted access window.
No national NCAA report challenge or conference document restriction is bypassed.

Primary source references:

- https://www.nfl.com/robots.txt
- https://www.nfl.com/teams/denver-broncos/
- https://www.nfl.com/teams/kansas-city-chiefs/roster
- https://pr.nba.com/2026-27-nba-regular-season-schedule
- https://ak-static.cms.nba.com/robots.txt
- https://official.nba.com/referee-assignments/

Only source code and acquisition evidence summaries belong in the GitHub
publication. Raw source HTML remains in the canonical private data bucket.

## Verified AWS runtime result: October 16, 2026, 19:49:36 UTC

Run `20261016T194831Z-56b44f4abd` passed all 14 self-tests and archived 32
actual data pages: the injury report, current-week schedule, and 30 rosters.
The capture interval was 19:48:33–19:49:36 UTC. It reported zero errors but
correctly kept `selected_scope_complete=false` because 32 rosters were required.

Inspection of the hash-verified archived directory established the two missing
teams: Houston and Indianapolis. Their published profile hrefs omit a trailing
slash; v027's profile parser accepted only links with a trailing slash. Both
teams also have explicit trailing-slash profile links in the captured injury
page. This is a parser coverage gap, not evidence that their rosters are absent.

The separately prepared v031 resume accepts both observed href forms and uses
existing injury-page links when resolving equivalent forms. It verifies all
30 previously captured roster bodies and acquires only the missing teams,
retaining the original requested cache vintage and actual capture timestamps.
Its readiness does not establish that the two missing rosters have been acquired;
that outcome must be verified from its AWS run report.

## Verified targeted roster recovery — October 16, 19:59 UTC

V031 passed 17 AWS tests, verified all 30 previous roster bodies, and captured
the two missing roster pages using observed official links. The selected
current scope now contains **all 32 team rosters plus the Week 6 injury and
schedule pages: 34 data pages total**. The recovery made five source requests,
reported zero errors, and completed at 19:59:23 UTC. Reused pages retain their
original 19:48–19:49 UTC retrieval timestamps; only the two new roster pages
have the new capture time. Source and publication/game times remain distinct.
The original v027 parser and its partial outcome remain preserved.
