# NCAA R19: verified partial work, failed scientific utilization

The R19 execution ended with **`UTILIZATION_ACCEPTANCE_FAILED_PARTIAL_WORK_PRESERVED`**. Its completed return was published on November 16, 2026 at **2:38:29 p.m. Pacific (22:38:29 UTC)**. The return archive and embedded source passed full verification: 302 payload members plus the payload manifest, for 303 ZIP members in total.

The [three-season comparison](three_seasons.html) retains its dated **R18 population, metrics and status assets**. R19 did not complete a replacement all-model population scoreboard. This review adds the verified execution and source-coverage facts without combining different cohorts or selecting a new champion. [Download the aggregate R19 status](R19_EXECUTION_STATUS.json).

## What R19 actually completed

| Work | Verified result |
|---|---:|
| New committed target-model fits | 49 |
| Current-model target fits within that total | 36 |
| Strict champion-refit target fits within that total | 13 |
| New scalar calibration fits | 8 |
| New empirical residual fits | 24 |
| Current target checkpoint reuses | 54 |
| Historical target checkpoint reuses | 108 |
| Unclassified committed model artifacts | 0 |
| Completed optimizer outputs awaiting publication recovery | 2 |
| Optimizer failures in the reported strict batch | 0 |
| Worker publication failures in that batch | 2 |
| Automatic promotions | 0 |

The target, calibration and residual counts measure different work and remain separate. Reused checkpoints are not new fits. The two unpublished worker outputs are excluded from the 49 committed target fits.

R19 also preserved **780 durably pre-cutoff forecast rows across 21 games**, comprising 11 men's games and 10 women's games. These are multiple recipes, targets and tracks per game. All 120 distinct forecast records have matching full-object readback receipts, with durable commits between 1:57:48 and 2:13:39 p.m. Pacific. This does not establish complete upcoming-season coverage. This public status report contains no per-game forecasts or private candidate grid.

## Why the utilization gate failed

The strict-refit pipeline proposed 52 contexts, prepared 15 fit tasks and durably completed 13 fit contexts. Its reported remaining queue contained 39 contexts. Despite dispatch capacity of 12, the ready queue peaked at **one task**, and only **two worker processes** were observed fitting concurrently.

The actual acceptance measurement covered 181.97 seconds. Average process-tree CPU use was **1.237 core equivalents**, or **10.31% of the requested 12-core capacity**, against the required 75%. Average useful worker CPU was 0.581 core equivalents. The measured bottleneck was **`PREPARATION_READY_WORK_SHORTAGE`**. Idle reservations and overlapping parent callbacks do not count as scientific worker utilization.

At the acceptance snapshot, the parent had spent approximately 182 seconds preparing fits and 57 seconds publishing them. By final strict-batch reporting, those cumulative times were approximately 205 and 73 seconds. These two timing snapshots have different endpoints.

A separate memory-pressure latch then blocked the publication path for two already-finished workers. The final traceback was **`V7_IO_DEFERRAL_ALREADY_LATCHED`**. The same latch prevented full-population materialization. The expected remote checkpoint records and content-addressed model prefixes for those two outputs were absent in a bounded read-only check. Retained local worker outputs must be authenticated at the replacement's launch, then recovered and published before deciding whether any refit is necessary.

The repair therefore needs both bounded parallel preparation and reliable draining of already-completed work under fresh resource checks. A prepared replacement or successful engineering test does not establish scientific utilization success. The actual workload must demonstrate it.

## What source data is ready

| Source or program | Verified R19 status | Remaining limitation |
|---|---|---|
| Odds API refresh | 3 HTTP calls, 6 plan credits, 171 raw outcomes and 44 new canonical quote rows | The refresh covered two current DraftKings NCAA sport snapshots; it was not broad-book or historical-season acquisition. |
| Earlier validation-season market history | No new historical quote refresh for 2024–25 or 2025–26 | Complete historical coverage is unproven. |
| DraftKings, Kalshi and Polymarket comparison | Zero qualified settled pairs in the returned current comparison | Stored observations are not proof of matched game, contract, clock and settlement coverage for every game. |
| CollegeBasketballData | Paused after provider HTTP 429; zero new calls | Resumption requires new provider-access evidence. |
| V12 basketball feature program | Ten feature groups registered; cached schema audit progressed | Zero newly materialized features, feature vectors, completed ablations or target fits; source rights and revision clocks remain unqualified. |

DraftKings, Kalshi and Polymarket are **comparison-only** under the current owner policy. Other relevant Odds API books can support the feature program only after source rights, availability clocks, provider exclusions and cohort coverage are verified. This status update does not retrospectively certify existing model inputs under that new exclusion policy.

## The comparison and promotion boundary

**2024–25 and 2025–26 are the validation seasons. The 2026–27 season has zero model-selection weight.** Current-season results remain test and monitoring evidence. They have already been viewed, so this review does not describe them as a pristine untouched holdout.

R19's separate original-model reconstruction report contains 637 completed men's games and 655 women's games. It lacks the corresponding complete current-model roster and therefore cannot replace the dated R18 population table or be mixed with earlier scores as a new same-game leaderboard. The complete required model roster still has no qualified common full-population score.

All R18 population, metric and status data, together with the preserved R17 route and shared status objects, remain unchanged. Publication of this review performs zero fits, issues zero forecasts, makes zero provider calls and promotes no model.
