# Case study: protect the decision from the answer

[Overview](../README.md) · [Historical-selection contract](HISTORICAL_SELECTION_BOUNDARY.md) · [Current aggregate explorer](current/index.html)

## Problem

Football research produces many correlated comparisons: frameworks, feature families, origins, score targets and ensembles. An analyst who repeatedly inspects a current-season panel can implicitly choose a champion from its outcomes, even when each individual prediction was generated chronologically. Chronological prediction alone does not prevent selection leakage.

A second boundary appears at execution. A forecast and a historical midpoint are insufficient to reconstruct a purchase. Quote age, actual decision time, fees, contract payoff and available quantity matter. Rerunning selection after outcomes arrive turns a backtest into hindsight.

## Completed evidence

The completed V125 owner return records 20 new conditional-expert fits, 456 reused native comparison cells, 6 retained fusion fits and 2,523 passing owner checks. Both NFL and FBS historical qualification gates failed. No automatic promotion or actual wager occurred. The [aggregate export](evidence/2026-10-27-v125.json) retains scorecards and 180 exploratory paired expert comparisons rather than just selected favorable cells.

The new V4 boundary reserves 2026–2027 strictly for monitoring. Historical selection may use the declared 2023–2025 material under explicit fixed, annual or precommitted online protocols. Evidence already inspected remains exposed. This contract improves decision discipline; it cannot retroactively make an exposed result prospective.

## Public mechanism 1: historical selection

The educational [selection guard](../examples/review_lab/historical_selection.py) accepts a frozen candidate set, declared historical seasons, protocol, evidence clock and complete candidate-by-season panel. It rejects unknown candidates, forward seasons, missing panels, differing cohort identities, impossible sample sizes, non-finite metrics, labels unavailable at freeze time and training that reaches the evaluation season.

An intentionally simple illustrative qualification rule requires favorable historical proper scores and supplied paired uncertainty. It is unrelated to the private football selection recipe. The result binds the evidence to a content hash. Forward monitoring verifies that hash and preserves the selected identifier even if another candidate has a lower forward loss. Monitor rows remain in declared candidate order.

The supplied uncertainty is not manufactured by this guard. A complete research system must produce it from paired chronological observations with appropriate dependence and multiplicity controls. Existing public factorial tests demonstrate why a negative interaction contrast alone does not prove that the combined system beats MARKET.

## Public mechanism 2: outcome-free decisions

The [paper-decision ledger](../examples/review_lab/decision_replay.py) accepts a complete declared candidate universe, official league/season/week identity, a precommitted rule and a decision clock. It does not accept outcomes. Evidence available after the decision is rejected, even if it would have existed before kickoff.

The ledger validates forecasts, model availability, feature availability, quote timestamps, quote age, verified timestamps, unit payout probability, ask, fee and displayed depth. Integer contract quantities respect cost and a fixed slot allocation. Inadequate evidence, no credible edge or zero depth leaves cash unspent. The result records a paper displayed-depth scenario, not an actual fill or order.

A separate settlement function accepts only selected event payoffs. It verifies the immutable decision identity, preserves pending outcomes and reports final profit/ROI only after all selected positions settle. Identical ledger reentry is accepted; a changed existing record is rejected. This is an educational integrity mechanism, not a claim of hostile-filesystem protection or venue execution simulation.

## Why these mechanisms work together

Historical qualification protects model choice. Chronological forecasting protects information availability. A frozen decision ledger protects selection and stakes. Settlement protects financial accounting. Each boundary addresses a different opportunity for hindsight; passing only one is insufficient.

Conditional experts, interaction features and market-aware ensembles remain promising research mechanisms, but V125 did not qualify a new champion. More expressive models require stronger evidence, not weaker admission. Conversely, a clean decision record can produce a valid negative result: no admitted position, unspent cash and no fabricated profit.

## Trade-offs and limits

The public example favors explicit small dataclasses, standard-library arithmetic and readable rejection reasons. It uses invented inputs and illustrative rules. It does not ship private observations, model weights, tuning, current forecasts, a fee lookup service, a market connector or a production staking policy.

The aggregate explorer presents 57 exact panels with 9,756 model scorecards. It separates historical diagnostics from 2026 monitoring, keeps model order independent of forward outcomes and calculates historical numeric emphasis before text filtering. It does not infer statistical significance from the displayed minimum. Venue diagnostics remain separate because price target alignment and execution evidence are incomplete.

The tests exercise failure cases: forward-season injection, changed evidence, incomplete candidate universes, post-decision quotes, stale/unverified timestamps, budget/depth limits, partial settlement and altered ledgers. Public synthetic reproducibility, owner private validation, hosted CI and real-world profitability remain separate claims.
