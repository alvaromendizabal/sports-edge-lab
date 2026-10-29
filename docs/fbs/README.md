# NCAA FBS: an independent research branch

[Project](../../README.md) · [FBS dashboard](index.html) · [Aggregate evidence](evidence.json) · [Invented reproducer](../../examples/fbs_contracts/README.md) · [Notebook](../../notebooks/fbs_branch_review.ipynb)

## The earlier V135 execution failed before science

The supplied V135 owner return reports `FAILED` during its precredential source-contract tests. A required earlier prompt was preserved inside an archive while an inherited test still looked for its original root path. All 56 return payloads and 1,723 embedded source payloads match their hashes, but byte integrity did not establish semantic dependency closure. Of 3,239 executed tests, one errored. The run produced zero new estimator fits and zero new fit attempts.

V134 remains the last completed scientific release in the inherited evidence. The recent FBS sequence contains **18 completed fits across 19 attempts**: twelve pooling fits across thirteen attempts plus six explicitly FBS-tagged calibration/innovation fits. This is a league-tagged subset, not an arbitrary division of a combined NFL/FBS count and not an all-project lifetime total.

Eight 2024/2025 MARKET and retained-minimax scorecards were independently recomputed from saved game-level prediction rows. Their reported metrics match exactly. V134 innovation scorecards and completed status are carried from the supplied prior audit; the full V134 owner archive was not attached to this branch's preparation. That distinction remains explicit in the aggregate evidence.

## The negative result matters

On 740 matched 2024 games, MARKET log loss is 0.554096; orthogonal innovation is 0.555551. On 748 matched 2025 games, MARKET log loss is 0.538547; innovation is 0.539946. Lower loss is better. Calibration improves 2025 to 0.537568 but regresses slightly in 2024 to 0.554364. No learned replacement qualified across both seasons.

The 301-game 2026 monitoring panel shows lower descriptive innovation loss, but it has already been exposed and cannot select models, calibrators, feature families or thresholds. Repeated historical examination also means 2024/2025 are not untouched holdouts. Operational MARKET remains selected; the FBS paper policy retains all $100 as cash. No realized profit, orders or fills are claimed.

## Prepared work is not completed work

FBS001 registers 203 intended estimator units: 183 core units plus 20 chronological cross-fit pool/gate units. It is a separate FBS-only owner program with independent ledgers and derived outputs. No FBS001 owner completion is claimed at preparation. Each executed unit must supply exact code and data identities, chronology, model state, convergence, paired metrics and timing.

The program's research plan has no elapsed-time or dollar stop. Durable checkpoints preserve productive work and support resumed stages. Actual provider quotas, terms, disk and memory safety, and transaction authorization still apply. Stored originals must be reconciled across shared project scopes before any missing paid snapshot can justify acquisition. A new source request is not a substitute for repairing lost normalization.

The prepared owner acquisition primitive supports exact historical requests only after a closed shared catalog proves the gap, a conditional shared reservation succeeds, the catalog is checked again, and current entitlement and quota are verified. **New paid live requests are disabled until a shared live capture-slot coordinator exists.** Different live capture timestamps could otherwise create different reservation keys for concurrent requests. Verified completed live originals remain reusable, and unresolved prior dispatches never authorize an automatic replacement purchase. The current runtime selects no proven missing target and reports `READY_BUT_NO_PROVEN_GAPS`; it does not dispatch a provider request.

## Public engineering contribution

The [standard-library example](../../examples/fbs_contracts/core.py) uses invented events to make four failure boundaries reproducible: FBS population/identity, actual source timing, atomic fit reentry, and complete shared-source content closure. It performs three synthetic fits, then reenters with zero new fits. Its tests alter clocks, labels, identities and saved bytes to verify rejection and preserve failed attempts.

The example contains no paid raw observations, individual forecasts, private source locations or credentials. It does not make provider requests, claim a sports edge, or alter the NFL and basketball research programs. [The dashboard](index.html) displays actual inherited aggregates separately from executable invented results.

## Runtime compatibility repair

[The v002 repair note](runtime-repair.md) explains the reproduced LightGBM warning, named prediction schema, version-specific regression matrix, and owner-progress boundary. The original evidence page remains a record of the first independent release.

## Pretraining source recovery

A later independent FBS attempt passed 122 tests, then entered shared-source inventory. At the returned audit snapshot, it had zero saved estimator completions or optimizer-start receipts. The replacement correctly declined to overlap its live writer. The elapsed stage-entry interval does not establish a deadlock. A further owner release is prepared; no new scientific result is claimed.

[The recovery example](pretraining-recovery.md) demonstrates explicit phase/work eligibility and an inactive SQLite checkpoint under its existing writer lock. Tests use a real local child and hot rollback journal, preserve the original bytes, and recover only a separate copy. No process signals, provider requests or private owner locations are included. The owner program schedules pinned-input science before broad source reconciliation; actual completion still requires its returned evidence.

## Process-handle portability

A subsequent recovery attempt refused before signaling because its Python build omitted at least one pidfd wrapper. That attribute check did not establish whether the running Linux interface was available. The [compatibility adapter and explanation](pidfd-compatibility.md) demonstrate per-operation Python/libc selection, an own-process signal-zero probe, exact errno reporting and descriptor cleanup. Tests remove the Python wrappers and exercise the exported libc path with local child processes. Operational errors do not trigger backend switching, and the adapter contains no numeric-PID signaling fallback. Target identity, ownership and application recovery eligibility remain separate caller obligations.

