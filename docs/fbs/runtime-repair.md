# FBS execution repair: named predictions and visible progress

An owner reported a terminal filled with LightGBM feature-name warnings and no
normal progress messages. The supplied excerpt contained neither a traceback nor
an exit status. It cannot establish whether training stopped or how many owner
fits completed.

## Reproduction and cause

The private v001 prediction path used NumPy arrays consistently. LightGBM 4.6.0
nevertheless exposes generated feature names, which newer scikit-learn checks
against the unnamed prediction input. A local reproduction with LightGBM 4.6.0
and scikit-learn 1.8.0 emitted the reported warning on four prediction calls.
The earlier preparation environment used LightGBM 4.7.0 and did not reproduce
that behavior. The difference is documented in
[upstream issue 6798](https://github.com/lightgbm-org/LightGBM/issues/6798).

The replacement gives the transformed LightGBM matrix stable names at fitting
and prediction, validates feature order, and exercises both the classifier and
regressor after serialization. The repair does not globally suppress warnings
or require upgrading the owner's environment. Unknown or altered schemas fail
explicitly.

## Public regression

`examples/fbs_contracts/named_predictions.py` is an invented-data example of the
same named-matrix contract. It trains one classifier and one regressor, treats
the reported warning as an error, verifies identical cold predictions, and
demonstrates safe selection of reordered input columns. Negative tests reject
missing, duplicate, nonfinite, or incompatible features. It makes zero owner-fit
claims and contains no private source data or forecast records.

```bash
python -m examples.fbs_contracts.named_predictions
python -m unittest examples.fbs_contracts.tests.test_named_predictions -v
```

The dedicated workflow exercises LightGBM 4.6.0 and 4.7.0 under Python 3.11 and
3.12. Its first step requires native imports, so missing dependencies cannot make
the compatibility workflow pass through skipped tests.

## Owner execution contract

The private replacement also adds flushed startup and stage messages, durable
heartbeat and fit-progress records, retained redacted failure tracebacks, and a
read-only audit of prior FBS runs. It checks for an active previous writer before
starting another execution. Prior model bytes and counts are preserved, but are
not silently claimed as completed work under a different source identity.
Reentry using the identical replacement executable remains checkpointed.

This repair preserves the registered 203 possible scientific estimator units,
the historical and monitoring boundaries, MARKET as operational reference, and
the qualified FBS all-cash paper book. It is an engineering correction; it does
not establish a predictive gain or a completed owner research execution.
