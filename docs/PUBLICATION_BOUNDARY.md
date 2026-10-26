# Public reproducibility and research confidentiality

[Project](../README.md) · [Public example](../examples/review_lab/README.md)

The repository exposes enough implementation to inspect engineering decisions without publishing the active research recipe or restricted observations.

| Public | Private or access-controlled |
|---|---|
| Information-time, identity and artifact contracts | Original licensed/private data and provider responses |
| Metric implementation and matched-cohort behavior | Immutable individual forecasts and current selections |
| Synthetic fitting and negative-case tests | Production weights, checkpoints and tuned configuration |
| Aggregate scores and their evaluation qualifications | Exact active feature transforms and representation parameters |
| Architecture, operational failure classes and source attribution | Credentials, account identifiers, private object paths and execution handoffs |
| Dated earlier public scientific implementations | New private runtime packages and complete continuation records |

## What is reproducible

The public synthetic example is executable without a provider subscription, AWS credentials or third-party ML libraries. Its generated events, training procedure, chronological split, scores and artifact identity are deterministic under the stated environment. Its tests verify meaningful failure cases. The evidence explorer is generated from the committed aggregate JSON export and checked for exact consistency.

The notebook executes the public example and displays the aggregate export in a separate section. No model is fitted to the real-run aggregate table. Synthetic metrics must never be cited as real football performance.

## What is inspectable but not fully reproducible here

Real NFL/FBS scorecards summarize audited private owner runs. The public export includes cohort sizes, evaluation policies, metrics, uncertainty limitations, source coverage and the owner-return digest. It does not include per-game probabilities or target records. Reviewers can inspect the conclusions and calculations permitted by those aggregates; independent full retraining is not available from this repository alone.

## Publication checks

Changes are reviewed for secrets, private account/object paths, runtime packages, individual forecasts, raw licensed records and active feature recipes. Generic method names and aggregate outcomes are not substitutes for those private materials. A historical public implementation remains a dated historical implementation; it must not be confused with the current private model.

This publication does not create a data redistribution entitlement or expand any source provider's terms. Source-specific usage rights continue to apply.
