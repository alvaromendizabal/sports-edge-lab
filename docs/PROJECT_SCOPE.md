# Maintained source and reproducible review

This active project separates three surfaces: current acquisition, scientific
verification, and immutable records of earlier executions. Only the first two
require working launch code in the current checkout.

The [current review guide](REVIEW_GUIDE.md) and [credential-free example](../examples/review_lab/README.md) provide an updated entry point. The current public aggregate snapshot includes completed V118; the older source implementations below retain their original scientific scope.

## Active components

| Path | Responsibility |
|---|---|
| `examples/review_lab/` | Credential-free synthetic training, exact-cohort scoring, temporal guards and verified reentry |
| `notebooks/engineering_review.ipynb` | Executed public review; synthetic outputs and real-run aggregates kept separate |
| `docs/evidence/`, `docs/review/` | Sanitized aggregate export and generated offline evidence explorer |
| `tools/*.py` | Provider clients, quotas, source validation, inventory and recovery; each client keeps its offline guards |
| `tools/current_snapshot_v043/` | Source snapshot corresponding to the currently scheduled AWS collector; preserved unchanged |
| `modeling/football_v058` through `modeling/football_v066` | Executable scientific controls, validation and recovery tests for the published modeling evidence |
| `docs/status/` | Original sanitized acceptance/rejection and preparation records; not a list of deployed models |
| `catalog/`, `config/`, `tracks/` | Source/identity catalog and five-track acquisition scope |

A model family's presence in verification code does not imply promotion. Consult
[the model card](MODEL_CARD.md) for accepted references and exact comparison scope.
Necessary comparison controls stay because the final decision depends on them.

## Run an isolated fitting demonstration

For the exact dependencies and supported Python version, follow the
[V066 README](../modeling/football_v066/README.md). That version's tests exercise
strict-FBS fallback, interruption, verified state reuse and publication identity.
The [V058 demonstration](../modeling/football_v058/README.md) provides a smaller
chronological fitting example. Both use synthetic input; no provider credentials,
private source data or running AWS space are needed.

All nine retained modeling jobs now run on each pull request. The acquisition gate
checks every surviving client and the active current-snapshot package offline.
Repository hygiene checks local document/notebook file links and rejects temporary
runtime/cache files. Scientific result gates have not been relaxed to achieve a
cleaner directory.

## Historical source and active AWS

Superseded packaged collector versions are available at the immutable commit links
in [execution provenance](EXECUTION_SOURCE_VERSIONS.md), not copied into new archive
folders. The original S3 source snapshots, scheduled processing configuration,
private data lake and experiment checkpoints are outside this GitHub pruning and
remain untouched. The obsolete v026 schedule-rendering helper is retired; this
publication does not recreate or update AWS infrastructure.

The repository's latest published modeling evidence may lag private AWS execution.
Dated results remain dated. Do not use an old README as permission to reopen a
rejected recipe, overwrite an accepted artifact or issue a new forecast.
