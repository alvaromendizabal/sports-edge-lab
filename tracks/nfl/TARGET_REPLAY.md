# Different targets, fixed recipes, complete monitoring

A winner model need not be the best margin or total model. A current-season
leaderboard also cannot choose a policy that is supposed to have been fixed
before that season. This standard-library example evaluates one explicit
historically selected recipe per target, while retaining every supplied census
game and every missing week.

Run from the repository root:

```bash
python tracks/nfl/target_replay.py
python -m unittest discover -s tracks/nfl -p 'test_*.py' -v
```

The demonstration is invented. It makes no provider requests, trains no model,
issues no prediction or order, and claims no NFL edge. The caller supplies a
target-specific model identity, prior-two-season selection declaration, receipt
digest and monitoring census. Declared digests and training policy are not
authentication of private bodies or complete nested training lineage.

## Questions the metrics answer

| Target | Measures | Interpretation |
|---|---|---|
| Conditional non-tie winner | Accuracy, log loss, Brier score | Accuracy counts correct sides; log loss and Brier also assess confidence. A confident wrong pick can hurt probability quality without changing accuracy. |
| Home minus away margin | MAE and RMSE | Errors in predicted point margin; neither metric alone gives a cover probability at a sportsbook line. |
| Combined total | MAE and RMSE | Errors in predicted combined points; a point estimate alone is not an over/under distribution. |

Winner accuracy chooses home at probability 0.5 or above. NFL ties remain in the
census but outside this explicitly conditional binary score. A tied final can
still be scored for margin and total if that target has a valid prediction.
MARKET is scored on exactly the same admitted games as the model. Negative
model-minus-MARKET loss differences are improvements; positive accuracy
differences are improvements. These differences are descriptive, with no
confidence interval, multiple-comparison correction or promotion claim.

## Chronology stays visible

The contract rejects current-season selection/training policy declarations,
different recipe identities, duplicate events, non-finite values and unknown
clocks. Per-row training-season declarations must match the selected recipe;
model creation cannot precede training-label availability, and prediction
creation cannot precede its model or source availability. Source and latest-label clocks must strictly precede both the declared
decision and the day-before boundary. Rows that fail that boundary stay in the
ledger with an explicit exclusion state. The complete source graph still needs
independent authentication; passing this helper is not full leakage certification.

Actual selection, model-creation and prediction-creation clocks are retained.
Late reconstruction never becomes a historical issued prediction. Every result
is labeled `RECONSTRUCTED_MONITORING_REPLAY_NOT_ORIGINAL_ISSUE`, even if all its
declared clocks precede kickoff. Original issue and settlement ledgers are
separate evidence. Missing model or matched-MARKET rows are not filled with zero;
future, postponed and canceled events do not enter realized scores.

No current-season ranking is performed. No aggregate historical minimum is
automatically promoted. Actual P&L and ROI remain unknown: this example has no
original allocation, instrument payoff, fee, quote or settlement ledger.

## What this adds to the existing examples

The [model-role inventory](MODEL_ROLES.md) accounts for saved candidates and
declared aliases. This helper consumes an explicit recipe for one target and
then builds full-census matched scorecards. The [paper scenarios](PAPER_SCENARIOS.md)
explain complete payoff arithmetic separately. Combining those contracts does
not supply missing model, source, quote or position evidence.
