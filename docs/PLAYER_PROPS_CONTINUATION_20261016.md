# Player-prop continuation v014

This bounded AWS acquisition run resumes historical US-bookmaker player props
for NFL, NBA, NCAA football and NCAA men's basketball. It uses the existing
event inventories and performs zero paid discovery requests.

- Maximum new odds credits: 500,000 shared across all four worker threads.
- Application runtime: 6,900 seconds; SageMaker maximum runtime: 7,200 seconds.
- Markets: six documented player-prop markets per sport; checkpoints at
  24 hours, six hours and 15 minutes before the cached event start.
- Required completed source runs: original v006 paid backfill and v008 props.
- Optional additional event source: v011 game-market continuation.
- Successful request identities and old event-specific 404s are seeded before
  paid requests begin. A 403 disables the odds provider for subsequent requests.
  Cached successful payloads are skipped rather than read and re-audited.
- Keys are resolved only inside the deployed AWS application; no key values are
  packaged, logged or included in request identities.

Each new response receives a separate quote audit. Response-wide defects such
as a mismatched event, future snapshot or post-start query block all outcomes.
A late bookmaker market or malformed outcome blocks only the affected quotes.
The audit indexes passing and structurally rejected outcomes in the immutable
raw response. Kickoff revisions remain visible. Passing recorded-time and
structure checks does **not** approve any feature or prove historical market
availability. Participant mapping, schedule provenance and settlement checks
remain necessary.

The artifact runs 30 self-tests automatically before AWS client construction
and ingestion. It emits 30-second heartbeats with credit reservations, costs,
progress and remaining requests. Per-request receipts, a resumable state and
exactly one uniquely named return ZIP are written to the canonical S3 bucket.

Runtime evidence must come from AWS. The build manifest records syntax
verification separately from the AWS self-test and acquisition results.
