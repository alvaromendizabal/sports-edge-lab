# Existing-model serving and shadow ledger (V063)

Public inference and information-time checks, **prepared for owner execution**. No V063 AWS completion or live forecast result is claimed here.

`prospective.py` loads previously fitted models from a trusted owned manifest, checks their byte hashes and scikit-learn version before deserialization, and verifies inference against cached predictions. Serving performs **zero model fits and zero provider requests**. Loading is intended for owned artifacts whose manifest is already trusted; a hash from an arbitrary downloaded sidecar does not establish that trust.

The serving gate records forecasts or explicit abstentions. It requires a feature and canonical snapshot no older than 24 hours, exact game/team/kickoff identity, serving parity, available training labels and feature history, and coverage of newly released team results. Known result revisions, stale or missing inputs, and missed issue deadlines cause abstention. NFL issuance ends 24 hours before kickoff; FBS-versus-FBS issuance ends one hour before kickoff. Production timestamps come from the runtime clock, including a final check after inference. A new job timestamp cannot refresh an old source snapshot.

The finite queue covers at most 200 games in the next seven days. The local ledger is idempotent, hash chained, locked and written atomically; conflicting records fail. This is an application append-only guarantee, not tamper-proof storage or a public deployment.

Run the offline checks on Python 3.12 and a POSIX environment:

```bash
python -m pip install -r modeling/football_v063/requirements.txt
python -m unittest discover -s modeling/football_v063 -p '*_tests.py' -v
```

The **36 tests fit four tiny synthetic estimators** (two logistic regressions and two ridge regressions), plus their scalers, to exercise model serialization and inference. The serving functions themselves never fit models. The remaining tests exercise freshness, deadlines, abstention, parity, ledger integrity and replay. Synthetic checks do not establish football predictive quality or verify the private AWS workflow.

The public files contain reusable code and synthetic fixtures. `prepare_serving` additionally expects an owner-provided worker context, trusted contracts, pinned models and parquet inputs, plus an installed parquet engine. Those assets and the cache-repair raw sources are not included in this adapter. The separately prepared source repairs preserve source-specific drive-chart counts; they do not enter the frozen benchmark or imply complete play-by-play coverage.

[V063 preparation evidence](../../docs/status/football_v063/README.md) records the local cache repairs and 1,247 prediction parity comparisons. Neither result is a model promotion or prospective performance result.
