# Interrupted acquisition: recover evidence without claiming success

[FBS evidence](index.html) · [Reproducible engineering example](../../examples/fbs_contracts/interrupted_work.py) · [Tests](../../examples/fbs_contracts/tests/test_interrupted_work.py)

This is a dated operations note for November 4, 2026 Pacific. It does not refresh the dashboard's data or change any model score.

## What actually happened

The V029 FBS owner produced an authenticated **exit-2 diagnostic**, not a successful acquisition run. It reached the queued predecessor handoff, but the prior acquisition owner no longer had a live process and had not supplied the independently stored completion required by that handoff policy. V029 therefore did not start its collector: it made **zero new provider requests, zero model fits and zero forecast issues**.

The diagnostic was checked against its actual bytes, archive closure, executed-source identity, separate terminal evidence and later independent completion. Its return SHA-256 is `d2d39365e40be6139ae80627bdf3f18c7944ba1a679a0c6c23e98f4e1338fa9c`. A digest identifies the reviewed private artifact; it does not make the full private execution reproducible from this public page.

The failure exposed a genuine engineering gap: requiring whole-run completion before considering any independently committed partial work conflates **an unfinished owner** with **unusable source evidence**. A missing normal-completion record must neither erase valid checkpoints nor become fabricated success.

## What is prepared, and what remains unproved

V030 adds a separately labeled interrupted-owner recovery path. Local tests cover exact process identity, missing completion, duplicate and conflicting observations, damaged dependencies, partial index loss, controlled cancellation and bounded resource admission. Recovery metadata and raw-value verification are distinct: an indexed candidate does not count as recovered until its actual bytes and dependencies authenticate. Original acquisition clocks remain unchanged.

**V030 is locally prepared and tested at this note's publication time; no V030 owner result or remote recovery count is claimed.** The next actual execution must supply its own evidence. A local software test is not a new scientific fit, a provider capture, an issued forecast or an established speedup on the shared instance.

The completed historical science is retained separately from interrupted acquisition. Original-model monitoring and rolling-model admission are not changed by recovery. Genuine new forecast issuance and rolling refits remain blocked until the outstanding raw-to-feature numerical reconstruction, teacher states, exact identities and causal cutoffs are independently verified. No betting edge, orders, stakes or profit are added by this operations repair.

## Inspect the contract without private infrastructure

The new [standard-library example](../../examples/fbs_contracts/interrupted_work.py) uses invented payloads only. It demonstrates how to preserve an active owner, distinguish diagnostic completion, recover independent complete units, reject corrupt or conflicting dependencies and independently replay a derived value.

```bash
python -m examples.fbs_contracts.interrupted_work
python -m unittest examples.fbs_contracts.tests.test_interrupted_work -v
```

The example does not use cloud credentials, provider data or private model logic. It does not implement a production distributed lock or authenticate an external provider from a hash. Those are explicit boundaries, not implied guarantees.

Collection and prediction remain separate: the latest supported pregame market observations can be acquired and displayed with their actual clocks without rewriting an earlier model's information set. Missing observations stay visible. Publishing this note or passing CI does not prove hosted deployment, complete market coverage, successful remote recovery or an improved model.
