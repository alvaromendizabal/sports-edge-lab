# Source compatibility and immutable forecast settlement

This public package exposes **pure offline methods and synthetic fixtures** from the V065 preparation. It contains no credentials, licensed data, private configuration, data locations or saved models. It does not acquire provider data, fit models or issue forecasts.

- `drive_compatibility.py` validates exact identities, regulation-drive denominators, paired-game completeness and equality across five source metrics. The entire supplied primary inventory is required; a missing canonical game fails closed. Malformed eligible rows quarantine their complete game. A successful comparison remains review evidence rather than automatic model-input substitution.
- `settlement.py` validates immutable forecast chains, actual issuance lead times, observed final labels and conservative release. It appends settlement evidence without rewriting original predictions. Pending records and unsupported uncertainty stay explicit; small samples do not establish quality or profitability.
- The two test modules cover 39 compatibility cases and 50 settlement cases, with **zero model fits and zero provider calls**. `fixture_inputs()` in each module supplies entirely synthetic inputs.

Use Python 3.12 with the pinned `requirements.txt`; run unittest discovery over this directory. The CI job performs the same offline checks. Installation may reach a package index; the tests themselves do not fetch provider data.

The private owner artifact adds bounded acquisition, durable shared accounting and complete runtime packaging. Those integrations and access configuration are intentionally absent. Passing these public tests does not reproduce private-data scores or verify a live owner run.

[Prepared milestone](../../docs/status/football_v065/README.md) · [Actual preceding issuance](../../docs/status/football_v064/README.md).
