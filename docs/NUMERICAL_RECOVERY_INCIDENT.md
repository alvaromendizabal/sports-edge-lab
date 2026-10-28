# V130–V132: preserve failures and verify eventual recovery

[Project](../README.md) · [Actual failure receipt](evidence/2026-10-28-v130-execution.json) · [Synthetic example](../examples/review_lab/numerical_recovery.py) · [Tests](../examples/review_lab/tests/test_numerical_recovery.py) · [Last completed research](CONSTRAINED_ENSEMBLE_FINDINGS.md)

V130 failed during the historical ensemble study after six completed real fits and seven attempts. All 2,916 owner checks had passed. The seventh attempt reported “Positive directional derivative for linesearch”; the runtime rejected that attempt and preserved the six completed artifacts. It did not complete the 24-fit experiment, issue new current forecasts or produce a new qualification decision.

## What is established

| Evidence | Actual result | Interpretation |
|---|---|---|
| Owner execution | Failed in historical model fitting | Engineering/numerical failure, not a completed negative modeling experiment |
| Completed units / attempts | 6 / 7 | Six real completed units remain prior work; an attempted unit is not a completed fit |
| Owner software checks | 2,916 passed | This test population did not expose the subsequent numerical failure |
| Worker / supervisor duration | 214.742 / 252.924 seconds | Observed partial-work costs, not the runtime of the complete planned program |
| Peak process-tree memory | 4.106 GB | Measured maximum before the failure |
| New forecasts / orders / promotions | 0 / 0 / 0 | Earlier immutable forecasts and MARKET policy retain their original identities |
| New historical qualification | Not completed | The retained V129 result remains: no learned challenger qualified |

The solver message alone does not prove that the objective is infeasible, that its current iterate is accurate, or that the modeling hypothesis lacks predictive value. Suppressing the exception, accepting an arbitrary feasible point or calling a fallback a completed experiment would each lose information needed by the next run.

## Separate three questions

1. Did an algorithm stop successfully according to its own termination code?
2. Does independently computed numerical evidence support the candidate for the declared mathematical problem?
3. Does the completed historical experiment support predictive qualification against MARKET?

The third question is never answered by the first two. Current-season outcomes remain excluded from feature, calibration, ensemble and champion selection. A numerical repair cannot turn exposed historical research into independent confirmation.

## A public example with invented inputs

Run `python -m examples.review_lab.numerical_recovery` from the repository root. The standard-library example minimizes an invented strictly convex diagonal quadratic on a nonnegative unit-budget simplex. It exposes a candidate's primal violation and a convex linearization gap. The public certificate computes exactly on the finite binary inputs with rational arithmetic, then rounds the reported gap upward. Projection computes its threshold exactly and rounds coordinates toward zero; it has no unbounded floating-point correction loop. For this explicit objective and domain, that gap bounds the distance in objective value from the global optimum.

A synthetic solver “success” at a poor point is rejected. A finite, feasible, near-optimal candidate retains the separate original solver status rather than rewriting it. A deterministic projected-gradient demonstration has a hard iteration limit and returns an incomplete status when that limit is reached. The example's tolerance is a numerical certificate tolerance, not a threshold for useful predictive improvement.

This is not the private football objective, a reproduction of the private solver, or proof that V130 has been repaired on owner data. The certificate depends on the stated convexity and domain assumptions. It does not certify a nonconvex model, data chronology, probability calibration or economic value. Authentication of real input receipts remains external to this educational code.

## Carry partial work forward honestly

The companion accounting example keeps imported completions, new attempts, new completions and failures separate. It rejects duplicate attempts, changed input signatures under one unit identity, modified completion identities and an attempt to count imported work as newly fitted. Prior receipts are unchanged. Reuse requires an exact compatible input and artifact contract; a changed research definition requires a new unit identity.

V131 subsequently executed and also failed. It retained the six V130 accepted units and added seven accepted units in eight attempts. Six new completions used an optimizer; one was a mathematically certified zero-call endpoint. The former failed FBS unit completed on its remaining retry. A later NFL candidate reported `xtol` success but its independent bound, 3.305585687570622e-8, did not establish the unchanged 2e-8 tolerance. This does not prove actual suboptimality is above the limit. The failed payload was not accepted.

All 2,968 owner software checks passed; the research remained incomplete and current serving was not reached. Thirteen units now survive across 15 cumulative attempts, with 11 units incomplete. The [V131 aggregate](evidence/2026-10-28-v131-execution.json) and [dashboard](dashboard/index.html) preserve these distinctions. Saved diagnostic arithmetic was independently checked; the protected training design and rejected candidate were not reconstructed. V132 subsequently completed the remaining 11 units; the verified update follows below. The [fault-isolation example](FAULT_ISOLATION.md) demonstrates a separate serving path on invented inputs; it is not evidence that actual V132 owner serving succeeded.


## V132: actual numerical completion, no predictive promotion

The authenticated V132 owner completed 11 additional units in 11 attempts, using ten optimizer calls and one certified zero-call endpoint. The full registered family now has 24 accepted units / 26 attempts, with both earlier failures intact. All 3,025 owner checks and four required notebook checks passed.

The independent audit replayed 22 saved certificate calculations exactly. Maximum newly accepted guarded gap was 1.3883729284283598e-8, within the unchanged 2e-8 limit. These are newly computed iterates. The discarded failed V131 candidate was not recovered or retroactively accepted. Exact saved-diagnostic replay is conditional on those quantities; protected rowwise derivatives and original feature arrays were not regenerated.

All four predictive qualification gates failed. Reference forecasting nevertheless completed before research, with 83 selected MARKET games, and financial reporting completed with zero qualified executions. [The V132 aggregate](evidence/2026-10-28-v132-execution.json) and [recoverable stage example](RECOVERABLE_OPERATIONS.md) make these independent outcomes inspectable. V133 remains pending on the owner environment.
