# V064 — reconstruct existing model inputs

This public method rebuilds the existing NFL 16-feature and FBS 60-feature definitions from observed canonical schedules and compatible drive statistics. It replays the frozen feature definitions before applying current results. Reconstruction and existing-model inference perform zero model fits.

The offline suite has 26 reconstruction tests and 43 serving tests. The serving fixtures train four tiny synthetic estimators and four scalers solely to test serialization and inference. They do not establish football performance or verify an AWS execution.

```bash
python -m pip install -r modeling/football_v064/requirements.txt
PYTHONPATH=modeling/football_v064 python -m unittest fresh_feature_tests prospective_tests -v
```

Use Python 3.12 on Linux or another POSIX environment. The test data are generated locally; no credentials or provider requests are needed.

`reconstruct_features` accepts frozen feature rows, historical paired drive statistics, observed current canonical games, optional compatible current drive statistics, per-sport observation receipts, and an explicit reconstruction time. `replay_frozen_features` verifies that the historical definitions reproduce the frozen feature values. `issue_forecasts` applies freshness, availability, scope and issuance-deadline gates to existing models and writes an application append-only ledger.

New observations retain their actual capture times. Rebuilding a feature table does not freshen an old source. Results obey a conservative kickoff-plus-24-hour release convention; unknown original publication times remain unknown. New FBS targets are FBS-versus-FBS, while inherited FBS/FCS prior-opponent context stays explicit. Newly released games with missing compatible drive statistics make affected efficiency state unavailable, including later opponent-adjusted updates. An official chart with similarly named metrics does not establish compatibility with the original drive definitions.

FBS schedule freshness and primary efficiency freshness are checked separately. A recent score or schedule capture does not verify that the current-season primary drive data remain unchanged. FBS efficiency readiness requires its own genuine observation or verified equivalence receipt; absent that evidence, the system abstains. Original source capture time is distinct from later aggregation and feature-rebuild times.

The package includes synthetic fixtures and generic integration adapters. It contains no private models, source contracts, raw captures, source pins, provider collector, or deployment configuration. Load serialized models only from trusted owners; a hash check alone does not make an untrusted pickle safe.

See the [V064 status record](../../docs/status/football_v064/README.md) for preparation and execution evidence. Historical feature replay and synthetic tests do not promote a model or establish historical publication-time accuracy.
