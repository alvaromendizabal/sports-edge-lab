# Shooting continuation v024: recover useful conference coverage

The v021 runtime exposed an acquisition-priority error: its first 300 verified
HTTP 200 responses were all empty arrays. v010 had already captured the recent
conference summaries, so v021 worked through hundreds of conference-less team
selectors before reaching earlier seasons. Sample empty selectors included
Pacific Lutheran, Franklin, Widener, Puget Sound, and Christian Brothers.
This was not evidence of a request-parameter defect: the exact 2026 ACC cached
requests contain 18 team rows and 235 player rows. Empty captures stay cached;
they are coverage observations, not newly acquired shooting records.

v024 makes four changes:

1. Snapshot the stopped v021 per-request receipts using the AWS SDK and retain
   that audit both in S3 and the one v024 return ZIP. The audit separates empty
   and nonempty responses, response bytes, and distinct raw hashes.
2. Verify positive cached 2026 Duke shooting within both ACC responses before
   any new provider acquisition. This includes raw SHA-256 verification.
3. Plan only missing conference-filtered summaries across all supported seasons.
   Conference-less team requests are counted as deferred pending independent
   coverage evidence. Valid empty caches are never invalidated or replayed.
4. Before bulk acquisition, require positive Duke shooting records from both
   2024 ACC endpoint canaries. Existing per-request caches are accepted after
   hash verification; either empty or invalid canary stops the run.

Scope remains the two direct CBBD shooting-summary endpoints, with documented
seasons 2003 and 2006–2027. No plays, lineups, substitutions, odds, or new source
discovery are requested. All 34 self-tests execute before credentials and
acquisition inside AWS. Raw captures stay private and retain exact identities.

Bounds are reduced to 3,000 statistics calls, 2,100 application seconds,
2,400 recommended SageMaker seconds, four workers, and two shared HTTP
requests per second. Retries consume the same budget. Provider 401/402/403/429
disables further requests, including queued calls; pre-HTTP cancellations do
not consume a call. Credentials remain runtime-only SSM SecureStrings.

Reports explicitly distinguish HTTP captures, empty responses, nonempty
responses, positive shooting-data responses, and rows observed, including
per-season counts. End-of-season summaries remain retrospective data, not
approved pregame features. Missing teams and source completeness remain open.

Primary references checked 2026-10-16:

- https://api.collegebasketballdata.com/api/stats
- https://api.collegebasketballdata.com/data-availability

The exact executed v021 source and artifact are preserved separately.
