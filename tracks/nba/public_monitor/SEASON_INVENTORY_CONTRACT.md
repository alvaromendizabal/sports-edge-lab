# NBA season inventory admission

`season_inventory_contract.py` makes the supplied official inventory the source
of dashboard membership. An event remains visible when a forecast, a final, or
a provider product is unavailable. Future events, exhibitions, unresolved
phases, and rescheduled events retain their original fields. Duplicate official
identities require explicit reconciliation before display.

The contract attaches model and provider records without choosing a champion,
averaging probabilities, inventing point predictions, or changing original
clocks. It distinguishes issued records, retrospective reconstructions, and
early outlooks; genuine T60/T120 records must meet their declared cutoff. A
missing model field needs a concrete reason. Cover probabilities require the
exact home spread line. US and international Polymarket, DraftKings, and Kalshi
remain separate. Archival sources are retained separately.

Provider metadata alone cannot count as observed coverage. Every observed
product requires a finite value, its representation, an acquisition clock, and
an original-versus-later-retrieval label. A refusal remains in the output with
its reason and leaves the corresponding product coverage gap open.

This contract proves membership closure against the **supplied** inventory. It
does not establish that an external official inventory is complete or current;
the result explicitly leaves that assertion false. Provider and model coverage
also remain evidence claims that require upstream raw-body and causal-input
authentication. No private data, model state, credentials, deployment identity,
historical performance result, or live provider request is included.

Run the synthetic contract tests from this directory:

```text
PYTHONPATH=. python3 -B -m unittest discover -s tests -v
```
