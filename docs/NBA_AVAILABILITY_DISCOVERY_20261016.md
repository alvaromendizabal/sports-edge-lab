# NBA availability acquisition: published-link expansion

The acquisition is an original-source collection from NBA-owned URLs. It is a sparse historical sample, not a complete availability archive and not an approved prediction-time feature table.

## Source investigation

- The [official 2025–26 injury page](https://official.nba.com/nba-injury-report-2025-26-season/) returned HTTP 200 and 117,149 bytes during investigation on 2026-10-16. Its `post-injury` content container was empty; the page described reporting rules but exposed no report index.
- A publicly linked [2022–23 page](https://official.nba.com/nba-injury-report-2022-23-season/) redirects to that same current landing page. It did not establish a separate historical archive.
- The official site's linked application JavaScript contained no injury-report archive endpoint. Analytics and unrelated endpoints were excluded.
- The [official site robots policy](https://official.nba.com/robots.txt) and [NBA static-host robots policy](https://ak-static.cms.nba.com/robots.txt) specified a one-second crawl delay and restrictions on administrative paths and query strings. The collector fetches and validates each policy before retrieving content; wildcard rules and longer declared delays are enforced.
- Public search returned 24 exact NBA injury PDF URLs across 2019–2026. The seed catalog stores these observed URLs and the search queries. No unobserved date/time filenames are synthesized or enumerated.

## Acquisition contract

The self-contained PYZ includes the source and seed catalog. It checks 13 tests before any AWS/source acquisition, follows up to four observed season-page links, and retrieves at most 250 discovered PDFs under a 300-request/600-second application ceiling. HTTP 401, 403 or 429 suspends the affected host; redirects are recorded without automatically following them. HTML masquerading as robots content fails closed.

Existing NBA source-specific receipt indexes are reused. The process does not read the general corpus. Raw PDFs and discovery evidence use content-addressed gzip object keys; the run writes provenance, capture timestamps, hashes, progress, a final report, and one return ZIP. No API credentials are used.

The first landing page has no report links, so this run is expected to add up to 23 PDFs beyond the earlier one-PDF pilot if all URLs are accessible. Actual captured/reused/blocked counts come from its AWS report, not this plan.

## Modeling gates still required

Extract each report's own timestamp and timezone, reconcile players and games, and validate that the injury status was available before the chosen prediction cutoff. Historical filenames before 2025 can omit minutes even when the PDF header includes them. A filename is therefore a discovery clue, not an availability timestamp. Historical completeness remains false until an auditable index or licensed historical availability source establishes the missing dates and revisions.

This collector does not retry the previously denied ESPN or NBA live-scoreboard feeds.
