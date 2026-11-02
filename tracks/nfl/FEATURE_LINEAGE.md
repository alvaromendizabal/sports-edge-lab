# Feature admission includes upstream fitted models

A statistic can describe a completed game and still depend on an undocumented
model. Excluding the current game's result from a rolling feature is necessary,
but does not prove that an upstream teacher was trained before the cutoff.

`feature_lineage.py` evaluates an explicit dependency graph. Each node binds an
exact SHA-256 and an asserted availability clock. A fitted node additionally
declares its latest training-label availability. Missing clocks, unavailable
parents, dependency cycles and future labels block the affected selected
feature. Valid independent features remain usable.

This makes a count-only ablation possible without claiming that one negative
result invalidates an entire feature family. It also prevents a blend from
silently inheriting an unqualified teacher through a distant dependency.

Run the deterministic metadata example and tests without credentials or data:

```bash
python tracks/nfl/feature_lineage.py
python -m unittest discover -s tracks/nfl -p 'test_feature_lineage.py'
```

The example admits a count-based feature and blocks a derived feature whose
teacher lacks training lineage. Fixtures are invented; passing tests establish
engineering behavior, not sports forecasting accuracy or betting profit.

## Integration contract

Supply the full dependency graph, including preprocessing, calibration,
embeddings and nuisance models. Keep target-specific training/fold identities
in the parent artifact metadata. Verify every hash and availability statement
against source receipts before calling this function. The function validates
the supplied metadata; it does not read source objects, prove clock honesty,
authenticate bytes or infer missing training bounds.

Availability at the decision cutoff is allowed for an observed source. A fitted
node's training labels must be strictly earlier than the cutoff, and must not
postdate that fitted artifact's own availability. Timezone-aware clocks are
normalized to UTC. Every dependency must also be available no later than its
child artifact, even when both precede the forecast cutoff. A historical reconstructed clock must be labeled outside this
contract; it cannot become proof of an original pregame issue.

Persist the full result, including rejected dependencies and the ordered
identity/hash closure. Correct missing lineage with new immutable evidence;
never rewrite old issue clocks or treat portable replay as native execution.

This module adds admission checks only. It performs no training, acquisition,
selection, promotion, staking or orders. No private model weights, feature
recipes, licensed feed bodies or private cloud identifiers are published.
