# NCAA basketball: execution, preserved work and recovery

Evidence snapshot: November 17, 2026, 2:49 p.m. Pacific. This is an execution review, not a new scientific result or a live status feed.

[Execution dashboard](execution.html) · [Exact public report](execution_status.json) · [Preserved three-season comparison](three_seasons.html)

## A newer execution was missing from the published pointer

R25 ran after the last published R24 return. It completed four of twenty scientific stages, then stopped during incremental source refresh when a source capture could not complete its required persistence/readback. Packaging subsequently failed because a verified owner resource lease was unavailable within the bounded wait. The terminal status was `RETURN_PACKAGING_FAILED_RESUMABLE`.

The published return pointer correctly continued to identify R24: it must not advance to an unverified archive. But reading that pointer alone missed the newer R25 run. Continuation also needs to inspect newer durable owner journals and unfinished packaging, authenticate their saved work, and recover the newest valid state.

A subsequent read-only recovery copy verified **411 payloads and 198 journal entries** from R25. Its SHA-256 is `385a3a7a6d2ea86c062dccfa8acdc3dd8b2a445168a6edeb38a02dc34aed5c96`. This recovery performed zero new owner executions and zero scientific fits. It is a verified copy of failed-execution evidence; it does not retroactively make the original return publication successful.

The last original published return remains the R24 retry, SHA-256 `9853bda9c8fe96e00cea2a6b23b13aa078747e90399fe4a2eb77a49fa5aa4e0e`, with all 104 payloads verified. Archive integrity and scientific completion are separate states.

## What repeated, and what did not

The scoped six-attempt history comprises R22 first/retry, R23, R24 first/retry and R25. The first R22 attempt preserved **11 newly committed physical target-estimator fits** before parent progress publication failed. The later listed attempts each recorded zero new target fits. This is not a project-lifetime census.

R23 and R25 each authenticated **108 historical target checkpoints** for reuse. Those accesses must not be added together and described as 216 unique models or new fits. The available evidence does not show later failed attempts repeating those target optimizations.

There was repeated engineering cost. The first R24 startup ran 867 prerequisite cases in 263.17 seconds. Its retry reused the matching test receipt in 0.064 seconds, but repeated recovery still failed at the same missing-wrapper requirement. R25 ran 955 fresh prerequisite cases in 294.12 seconds under its new code identity, then passed the older wrapper barrier and reached source work. Preparation checks and repeated integrity work consume resources even when they create no new model.

R25's owner summary recorded 840.30 elapsed seconds, before failed packaging; terminal status elapsed was 905.00 seconds. Its recorded parent CPU was 756.83 seconds and completed-child CPU was 0.65 seconds. The saved shared-instance wall-cost estimate was about $0.60, not an invoice or an exclusive fitting cost. R25 made zero new target, scalar-calibration or empirical-residual fits. Its incremental scoreboard stage reached 21 of 34 units before the source persistence stop.

## The throughput problem is still an acceptance requirement

The earlier R22 measured scientific interval lasted 182.98 seconds and reported 4.23% of selected capacity, below the 75% threshold. Ready depth peaked at one and simultaneous workers at five. No later 12–24-core NCAA scientific success is established by these records.

The next owner execution must keep enough admissible work ready, bound preparation memory and native threads, and distinguish preparation, fitting, scoring and packaging CPU. With sufficient eligible work, useful scientific occupancy must reach at least 75% of admitted capacity over 180 seconds with durable completions. Package tests or synthetic queue fixtures cannot pass that gate on behalf of a future run.

## Scientific and publication limits

Men's and women's populations and champion registries remain independent. Annual 2024–25 and 2025–26 validation metrics select with the declared 50/50 primary rule and the other four sensitivity ratios. Changing a score ratio does not reweight training rows or refit models. Completed 2026–27 games retain zero selection weight, and prior test exposure cannot be erased.

The existing game, forecast, comparison and model-score assets are unchanged. Their dated coverage and qualification limits remain visible. This update supplies no new full-population champion, current forecast, provider comparison or completed-season certificate.

The public projection contains sanitized execution counts, scientific limits and evidence digests. Owner packages, raw licensed responses, active model bodies, exact feature transforms and private cloud locations remain private. Source publication and website deployment are separate events; deployment is not claimed here.
