# Read-only drive-clock adjudication

This public package exposes the **pure diagnostic method and 49 synthetic tests** from V066. It uses the Python standard library only. It contains no credentials, provider data, private configuration, data locations, artifact pins, saved models or acquisition code. It does not fit models or issue forecasts.

`source_adjudication.py` examines malformed regulation end periods using an integer clock equation and unique immediately adjacent drive numbers. It preserves original rows and records source observation separately from unknown publication time. Boundary ambiguity, missing neighbors, conflicting chronology, duplicate identities, invalid clocks, halftime crossings and overtime remain explicit. Unsupported drive-result labels are never inferred from scores or neighbors.

A corroborated clock candidate is **derived research evidence**, not an authoritative source correction. The method performs zero source corrections and zero model-feature insertions. It does not establish canonical game completion, FBS target eligibility, equality with another provider or permission to serve a model. Those checks remain separate.

Use Python 3.12 and run `python -m unittest discover -s modeling/football_v066 -p '*_tests.py' -v` from the repository root. No dependencies need to be installed. CI verifies the exact 49-test count and blocks socket connections during the suite. `fixture_inputs()` supplies entirely synthetic drives; passing these tests does not verify private-data results or an owner execution.

The private V066 owner artifact includes additional cached-data parity, fixed linear-model evaluation, runtime accounting and reporting. Those integrations and the FBS fallback estimator are intentionally absent from this public method package.

[V066 preparation and evidence](../../docs/status/football_v066/README.md) · [V065 compatibility and settlement methods](../football_v065/README.md).
