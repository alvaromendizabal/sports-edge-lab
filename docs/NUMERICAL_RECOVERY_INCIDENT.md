# V130: preserve partial work when the numerical solver stops

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

V131 is the next prepared recovery release. Its implementation and synthetic checks are preparation evidence. Only the subsequent actual owner return can establish accepted reuse, newly completed fits, the full historical study, new forecasts and end-to-end recovery. The failed V130 run remains failed even if its successor succeeds.
