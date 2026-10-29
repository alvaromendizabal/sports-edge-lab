# NBA branch contracts

[NBA review](../../docs/nba/index.html) · [Experiment, model and source card](../../docs/NBA_RESEARCH_CARD.md) · [Contracts](contracts.py) · [Tests](tests/test_contracts.py) · [Actual aggregate receipt](../../docs/evidence/2026-10-29-nba-b009-audit.json)

This standard-library example makes NBA branch isolation, a controlled feature/window comparison, source timing and checkpoint accounting executable. **Every example input and artifact is invented.** It performs zero model fits, network requests, provider charges or orders. The separately committed aggregate receipt summarizes authenticated B009 owner evidence; running this example does not reproduce that private execution.

## Run it

From the repository root, use Python 3.11 or later:

```bash
python -m unittest discover -s examples/nba_branch/tests -v
python -m examples.nba_branch.contracts
python -m examples.nba_branch.build_review --check
```

No package installation, credentials or cloud access is needed. The walkthrough creates and removes only its own temporary invented files. It publishes one fixture completion, reopens the same journal, and shows that accepted reentry requires no new work. The counter is explicitly `completed_fixture_units`; real model fits remain zero.

## What the contracts establish

| Boundary | Demonstrated behavior |
|---|---|
| NBA identity | Exact league, provider, native event ID and season; NCAA and football identities are rejected |
| Full factorial | Incumbent/candidate features × original/revised windows, each in 2025 and 2026 |
| Common validation | One pinned invented validation cohort per season, shared by every arm; a changed cohort is rejected |
| Historical selection | Current and future seasons cannot enter the registered selection plan |
| Source timing | Both publication and first observation of the exact version must precede the decision cutoff |
| Revisions | A late revision is rejected even when an earlier version was available |
| Exact reuse | Experiment, input snapshot and code identity bind the journal; changed identities cannot adopt it |
| Completed-unit accounting | A matching completion receipt and intact artifact are required; interrupted starts are pending |
| Atomic publication | Complete bytes are linked into an immutable path; an interruption between artifact and receipt does not count a completion |
| Shared sources | Verified raw bytes are read without mutation; NBA derives its own output separately |

The **eight registered jobs are not eight fits**. Four arms across two historical seasons describe the primary comparison; a production job can contain multiple estimator components. The example supplies no private features, estimator implementations or real event records.

The tests exercise missing factorial cells, substituted validation populations, cross-league identities, late observations, invalid clocks, altered accepted artifacts, interrupted publication and exact reentry. They check resulting evidence, not just whether functions returned successfully.

## Timing and provenance limits

An observation's supplied publication and observation clocks are inputs to this demonstration. A hash proves byte agreement, not source rights or the truth of a timestamp. Production use needs independently verified source and observation receipts. A later re-download preserves the original observation clock; it cannot manufacture earlier availability.

The strict example admits a version only if it was both published and observed before cutoff. Historical data qualified under a documented release-lag assumption belong in a separate reconstructed-research tier. This example does not relabel reconstructed history as prospective knowledge.

## Reuse and shared acquisition limits

The fixture journal demonstrates one local writer. It is not an account-wide request lock, a provider client or a distributed transaction system. The real shared-source interface must coordinate exact source/sport/event/market/region/bookmaker/snapshot request identities, reserve charges before dispatch, keep unanswered attempts charged, and preserve raw response and billing receipts. Reusing verified bytes grants no new credit allowance or source rights.

NBA-derived checkpoints and selection decisions are independent of the NCAA branch. The example never writes another branch's results. A damaged accepted checkpoint fails verification; the example does not silently refit it, replace evidence or refund prior work.

## Public evidence and scope

B009 completed 10 new NBA native units. The authenticated lifetime NBA count is 85; the combined basketball count is 268. Predecessor aliases and replayed checkpoints are excluded from new-fit counts. No NBA challenger was promoted and no qualified MARKET advantage was established. The original failed B008 NBA partitions remain failed; the ten B009 units belong to a separately registered experiment.

B010-NBA real owner execution remains pending. The standalone [NBA review](../../docs/nba/index.html) is generated from the sanitized receipt and checked in CI. It leaves the existing 235 basketball scorecards, 120 overlap specifications, football evidence and NCAA evidence intact. The editorial portfolio assessment stays 8.5 → 8.5; the 9.9 target is not established by these public examples.
