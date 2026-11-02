# Learn from past mistakes without changing the past

A rolling model may use an earlier game's result after that result becomes
available. It cannot use the target game's result, a later correction, or an
in-sample prediction disguised as an out-of-fold error. A new update policy
also cannot rewrite the evidence class of an old frozen experiment.

The [standard-library example](rolling_chronology.py) checks these boundaries
using **invented events, times and values only**. It trains no estimator, calls
no provider, performs no selection, and places no order. Passing its declared
metadata does not authenticate private source bodies, fitted models, issue
ledgers or scientific performance.

```bash
python tracks/nfl/rolling_chronology.py
python -m unittest discover -s tracks/nfl -p 'test_rolling_chronology.py' -v
```

## Two policies with separate identities

| Policy | Admissible training labels | What remains unchanged |
|---|---|---|
| Frozen historical | Historical-season labels available strictly before the origin | Original model, cohort, cutoff and forecast records |
| Separately registered rolling experiment | Historical and earlier current-season labels available strictly before the origin | Original frozen experiment and prohibition on monitoring-based recipe selection or promotion |

The example fixes one fit origin for a complete declared league week: two hours
before its earliest kickoff. It keeps official season, phase and week together;
an ISO calendar week is not a substitute. Labels arriving at the boundary are
excluded under this strict convention. Missing availability is unknown, not a
zero label or an assumed publication date. The exact week membership and policy
have separate hashes.

Two hours is a **new horizon declaration**, not an edit to older day-before
results. Fitted preprocessing, calibration, blends and thresholds need the same
historical isolation in a real study. The caller must supply a genuine complete
week and accurate clocks; this demonstrator does not discover league schedules.

## Error feedback uses earlier, matured OOF predictions

The example admits a prior residual only when:

- Its prediction belongs to the same target and an earlier forward origin.
- The prior event is absent from the declared training event IDs.
- Prior training labels and features precede that prediction's information boundary.
- The result was available strictly before the new origin.
- It is outside the target week and permitted by the update policy.

For an admitted row, it reports the model residual, reference residual and signed
model-reference disagreement. These are candidate feature inputs, not evidence
that a particular feature improves forecasts. A model's own fitted training
errors cannot substitute for forward out-of-fold residuals. Winner, margin and
total records stay separate. No player distribution, cover probability or
profitable betting rule is inferred from point errors.

The tests change future outcomes and show that admitted feedback remains
unchanged. They also reject duplicate events, same-week feedback, self-training,
late prior information and missing result clocks. These checks demonstrate
engineering behavior; upstream nested-lineage verification remains necessary.

## Creation time is different from information time

Rebuilding a prediction today from historical inputs does not make it an issued
historical pick. The forecast classifier preserves actual model completion,
input availability, creation, issue and observation clocks. It distinguishes:

- Declarations that predate the policy's registration.
- Reconstructions created at or after the event began.
- Late pregame monitoring and inputs outside the registered horizon.
- Timely pregame declarations that still require separate durable issue proof.

An issue exactly at the declared cutoff may use only inputs strictly earlier
than it. A prediction made earlier is an early issue under that policy, not
proof that inputs were refreshed at the later cutoff. Original source
publication and possession clocks must be verified by the actual consumer;
kickoff-plus-delay proxies cannot establish historical possession.

## What this contribution does not establish

It supplies no real predictive score, model promotion, market outperformance or
actual P&L. Historical and current-season observations already inspected remain
exposed. A real rolling experiment needs timestamped registration, frozen recipe
selection, complete game accounting, same-cohort provider scores, uncertainty
and truly future confirmation. Original frozen results remain available next
to separately labeled new reconstructions.
