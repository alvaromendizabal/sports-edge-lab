# Preserve exact inputs through numerical replay

A replay can permit a tiny numerical difference in a model output while
accidentally requiring exact equality for every feature derived from that output.
Those two requirements conflict. A one-ULP change in a baseline can legitimately
change its product with an unchanged input, even though both computations satisfy
the same formula.

The [standard-library example](dependent_replay.py) demonstrates a narrow
validation boundary:

1. Authenticate the original bytes with an independently trusted SHA-256 pin.
2. Match source, event, model and cutoff declarations, plus independent fields,
   exactly. A numerical tolerance cannot waive a changed label or source.
3. Check the baseline with the caller's predeclared numerical tolerance.
4. Check each derived field against its exact formula using its own baseline.
5. Return the unchanged original bytes for subsequent exact training-input hashes.

Run from the repository root:

```bash
python tracks/nfl/dependent_replay.py
python -m unittest discover -s tracks/nfl -p 'test_dependent_replay.py' -v
```

The demo uses invented values and two elementary formulas. It changes one
floating-point ULP, shows why an ordinary exact derived-field comparison fails,
and preserves the original input bytes. Tests refuse changed independent values,
incorrect formulas, duplicate JSON keys, wrong hashes, non-finite numbers and
differences at the exclusive tolerance boundary. No fitting, network requests,
forecast issues or orders occur.

## What this does and does not establish

Exact byte identity and numerical equivalence answer different questions. Neither
should silently replace the other. The retained bytes stay exact; the numerical
comparison receives a separate receipt. The caller must establish the tolerance
before inspecting the discrepancy and authenticate every required upstream
model, source, runtime and dependency. This small example checks declarations;
it does not prove that the declared computation actually ran or that its clocks
are true.

The design follows a real replay-boundary repair, but the original owner failure
did not retain the differing values. Therefore its precise numerical cause
remains unproved. Passing these fixtures or a local real-input replay cannot
establish acceptance on the owner runtime. That requires the exact owner return,
all required stage/output receipts and the later completion receipt. Completed
models must remain preserved while the failed reporting or replay stage is
repaired; they do not earn new fit credit.
