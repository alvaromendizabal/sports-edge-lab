# From a game distribution to one exact betting line

A predicted score margin of three points does not say how often a team covers
three points. Two distributions can have the same mean and different cover
probabilities. This standard-library example consumes an **explicit discrete
probability distribution**; it never invents one from a point forecast or a
market line.

```bash
python tracks/nfl/settlement_distribution.py
python -m unittest discover -s tracks/nfl -p 'test_settlement_distribution.py' -v
```

Every game, probability, source and clock in the runnable example is invented.
Passing these tests proves engineering behavior, not private model accuracy,
source authentication, provider availability, an issued wager or an edge.

## Bind the event, target, clock and settlement

Distribution and instrument declarations must match exact event, target,
decision cutoff, kickoff and settlement-version identity. Margin is always
**home minus away**: `HOME` at threshold 3 means home -3; `AWAY` at that same
threshold means away +3. Total points use `OVER` and `UNDER`.

Integer or half-integer thresholds are supported. Equality is a full stake
refund. Quarter lines, reduced-leg entries, ties-as-loss contracts and other
payoffs require their own adapters; this example rejects them. A matching
settlement identifier is a declaration, not a verification of provider rules.

Support consists of unique integer point values and nonnegative probabilities.
Total points cannot be negative. The mass must equal one within 1e-12; any
accepted rounding normalization is exposed. Sources and training-label clocks
cannot cross the declared decision boundary. A model cannot be available
before its last declared training labels, and computation cannot precede the
source's availability or model availability.

An original-issue declaration additionally requires model, source, computation
and issue by the cutoff. A reconstruction can have later possession, model
availability and computation, but never an original issue clock; those late
states remain explicit. External source-body, model-lineage and durable issue
authentication are still necessary. A string supplied by a caller is not that
authentication. Source as-of time can equal the cutoff; labels must be strictly
earlier. This module does not choose a T1/T2 policy for the caller.

## Keep pushes visible in proper probability scores

The example assigns probability to `WIN`, `PUSH` and `LOSS`. In its invented
home -3 case, those probabilities are 70%, 10% and 20%. The chance of winning
conditional on no push is 70/90 = 77.78%. That conditional figure is different
from the unconditional 70% chance of a winning settlement.

| Metric | Definition and denominator |
|---|---|
| Three-state log loss | Negative natural log probability of the actual win/push/loss; include every supported settled game, including pushes |
| Three-state Brier | Sum of squared errors across all three categories; range 0 to 2; no division by three |
| Conditional binary losses | Use win/(win+loss), only for actual non-push games with positive non-push mass |
| Unique-mode accuracy | Predict the single most probable settlement state; a tied mode abstains and needs a separate coverage count |

An outcome assigned exactly zero probability has infinite log loss. There is
no silent clipping. JSON exporters must represent that explicitly rather than
turning it into a finite improvement. Missing outcomes retain their forecast
and null scores. The module never silently reduces a headline cohort; aggregate
callers must retain the fixed census and matched membership using the separate
[uniform comparison contract](UNIFORM_COMPARISON.md).

Compare providers only when they refer to the same event, line, side, cutoff
and settlement rules. Different lines define different outcomes. Three-state
Brier must not be mixed with ordinary binary winner Brier. A market center
alone supplies neither a distribution nor these probability scores.

## Probabilities are not profit

Actual entry prices, complete payoff rules, fees, executable depth, available
budget and settlement records are separate inputs. The existing
[paper scenario contract](PAPER_SCENARIOS.md) illustrates state-contingent dollar
arithmetic. This module emits no expected-profit or realized-profit claim,
promotion permission or order. It has no network access, training, provider
credentials, production model weights or private feature recipes.
