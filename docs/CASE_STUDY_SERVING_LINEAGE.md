# Case study: the selected policy must be the served policy

[Project](../README.md) · [Audited V126 receipt](evidence/2026-10-27-v126-execution.json) · [Executable public mechanism](../examples/review_lab/serving_lineage.py)

## Problem and consequence

Historical selection has little operational value if current inference or the financial ledger silently uses a different family. A model with a historical training cutoff may still have been fitted or selected later. Calling its earlier saved forecasts "historically selected" would change the meaning of the evidence after outcomes were known.

V126 addressed this identity gap. The owner run now records one frozen selection identity, verifies the selected serving rule and carries that identity into the authoritative native-week ledger. It preserves earlier research forecasts without relabelling their historical selection status.

## What actually executed

The owner return passed all 669 member pins, source-archive identity and 2,595 owner tests. The worker completed in 450.646 seconds with zero new fits. It retained the earlier fitted bank, issued 83 raw MARKET references and kept 7,908 model research forecasts separate.

No learned policy qualified. Both leagues used their deterministic benchmark fallback. The ledger covers 32 native league-week records and 1,160 schedule rows, with no strict eligible forecast games and unavailable historical profit. These are different counts and different claims.

## Public reconstruction of the invariant

The public mechanism uses immutable typed identities and explicitly zoned clocks. Its verifier requires:

- Identical league, policy identifier, rule-content hash and policy kind in selection, issue and ledger.
- The same frozen selection digest at every stage.
- Historical selection seasons strictly before the forward monitoring season.
- Selection availability no later than issue availability, and issue availability no later than ledger creation.
- No retrospective substitution of exposed forecasts or invented earlier policy creation.
- Separate accounting for benchmark references and learned-model predictions.

Adversarial tests change a hash while retaining a display name, swap the ledger's policy, add a forward outcome season, move availability after issuance and count benchmark rows as learned predictions. Each fails closed. A second validator reconciles the allowlisted public V126 receipt and rejects accidental individual forecasts, private weights, extra cloud paths, invented profit and inconsistent resource counts.

The digest comparison does not prove that a private source file was authentic, nor does a matching lineage certify calibration or tradability. Those claims need their own evidence. The public receipt supplies audit identities and aggregates; private source bytes remain outside this repository.

## Why this is an engineering improvement

A single chain of identity removes an ambiguity that test counts alone cannot resolve. It also makes failures legible: a good model can fail availability, an admissible forecast can fail execution evidence, and a completed run can produce a negative scientific result. The code and user-facing report preserve those distinctions.

The measured bottlenecks were owner tests and shared input preparation, rather than fitting in this zero-fit release. The public explorer therefore shows actual stage durations alongside the lineage clocks without treating elapsed seconds as publication times. Future performance work must preserve the same output identities and information boundaries.

## What remains unproved

V126 established the intended correction in an owner execution. It did not establish a new predictive model, an independently confirmed gain, a qualified learned champion, historical profit or a live wagering opportunity. V127 research is a separate, pending experiment. Public synthetic test success and locally prepared repository changes do not establish hosted CI or a merged publication.
