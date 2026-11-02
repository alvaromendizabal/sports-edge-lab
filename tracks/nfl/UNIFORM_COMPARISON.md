# One comparison contract, explicit disagreement results

A provider with fewer historical observations must not silently change the
headline model-versus-reference cohort. The standard-library
[uniform comparison example](uniform_comparison.py) pins the exact event
membership, keeps the full census visible, and reports an incomplete provider
intersection separately. The same number of games is insufficient: their
identities must match.

Run from the repository root:

```bash
python tracks/nfl/uniform_comparison.py
python -m unittest discover -s tracks/nfl -p 'test_uniform_comparison.py' -v
```

Every demonstration event, probability and result is **invented**. This example
has no provider requests, production model weights, training, orders or real
profit. It consumes declarations; independent source-body authentication and
upstream model-lineage verification remain the caller's responsibility.

## Consistency is defined by the target

| Declared target | Consistent score | Separate diagnostic |
|---|---|---|
| Home winner conditional on no tie | Log loss, Brier and accuracy on the same games | Both right, model only right, reference only right, neither right |
| Home-minus-away margin | MAE and RMSE in points | Absolute-error wins and direction relative to one exact line |
| Game total | MAE and RMSE in points | Absolute-error wins and direction relative to one exact line |

All observations must bind to their declared model or reference series and matching orientation, settlement, value basis,
decision cutoff and, for point-direction diagnostics, threshold. The probability
conversion method belongs in the upstream reference declaration: a two-sided
sportsbook normalization, an exchange ask and a contract midpoint are different
objects. An entry payout or an individual player threshold is not a game-winner
probability. Different thresholds define different binary targets. The example
rejects mixed declarations rather than assigning them one misleading score.

Winner accuracy uses `p >= 0.5` for home, with that equality rule stated in the
output. Probability losses clip only for numerical log evaluation at `1e-15`;
Brier and accuracy use the original values. Missing or ineligible outcomes stay
in the census with `actual=None`; a tie never becomes a binary loss.

## A missing provider row cannot revise the headline

The caller supplies an independently fixed event list and its SHA-256 membership
digest. Complete support produces headline scores. Incomplete support leaves
headline scores null and exposes a separately named matched subset, with its own
digest, denominator and coverage. Adding a provider never mutates another
comparison's contract or hides games with missing observations.

Weekly rows retain weeks without supported forecasts. They expose matched-subset
scores and disagreement counts without pretending to have complete support.
The example does not estimate confidence intervals or promote models. Paired
uncertainty, registration, multiplicity and minimum cluster support belong to
the governing scientific study.

## Where a model was right and the reference was wrong

The game ledger keeps four mutually exclusive winner states. On one exact
cohort:

`net extra correct = model-only right - reference-only right`

`accuracy difference = net extra correct / matched games`

The invented complete example has one game in each of the four states. Thus
both sides pick two of four correctly, they disagree twice, and neither gains a
net correct pick. Both the wins and the reversals remain available for review.

Point predictions answer a different question. A model can be closer to the
final margin without a valid cover probability. The separate line diagnostic
counts right/wrong direction, pushes, no line and no direction. A reference
center exactly equal to its own line has **no direction**, not a 50% accuracy
score and not a loss. Pushes and no-direction rows do not enter directional
accuracy. Neither point closeness nor directional accuracy establishes payout,
expected value or a profitable wager.

## Preserve the clocks and the evidence class

Source and possession clocks must not exceed the declared cutoff; the boundary
is inclusive in this standalone contract. A caller using a strict boundary
must admit rows under that stricter rule before calling this example. Actual
value creation time may be later for a declared reconstruction, and remains
visible. That is not an original pregame issue. Impossible creation/source
ordering and timezone-free clocks are rejected.

The output always labels itself a declared replay, with no selection or
promotion permission, no order, and unknown actual P&L and ROI. Determining
whether a historical betting edge existed additionally requires a frozen
decision policy, qualified out-of-time forecasts, original matching prices,
entry/settlement rules, fees and actual stake or paper-allocation records.
