# FBS V100 failure and V101 preparation review

[Interactive review](index.html) · [Bounded evidence JSON](data/status.json) · [Successful V099 research](../v099/completed/README.md)

## Actual V100 outcome

V100 failed during checkpoint recovery. The observed child and supervisor exits were both **2**. Recovery stopped at **28,513 / 44,841 units** with the explicit guard `COMMITTED_CHECKPOINT_RECOVERY_NOT_READY; NO_COMPLETED_WORK_RESTART`.

The supervisor completed durable publication of a verified, resumable return. Its integrity does not convert the failed owner execution into success:

- **73,426,500 bytes**, one ZIP part below the 512 MiB per-part limit.
- SHA-256 **a6601bf92b9c971cd4f7bc38a0650553efed378afc54492ab9db729c942297dd**.
- Scientific status **SAFE_PARTIAL_FAILURE_V13**.
- Zero new estimator fits, calibrator fits and scoring tasks. Scientific dispatch was not reached, and fit accounting remains explicitly incomplete.

The owner result and this public source preparation are separate events. Publishing this review starts no owner execution, provider retrieval, forecast issue or production deployment.

## Completed science remains preserved

V098 remains an operational success: **1,125 fitting jobs, 1,113 new model fits, 12 reused fits, zero fitting failures and 1,113 reported calibrators**. V099 remains an operational success: **600 completed forecast/uncertainty tasks**, 100 additional policies, 273,200 new forecast rows and 260,800 completed-game score rows, with no new base-model fits.

These completed campaigns remain scientifically partial because broader V13 research is unfinished. V100's failure does not rewrite their outcomes. Its unreached scientific-admission counters are not evidence that completed predecessor files were lost.

### Census observations and evaluation populations

V100 made **two authorized CFBD current-census calls** and zero paid market calls. It observed **888 current-season games, 757 completed games and two newly finalized games**. The postseason response was empty, so complete season/postseason coverage remains unproven.

The latest completed model comparison remains V099 on identical observed completed cohorts of **919 games in 2024, 934 in 2025 and 755 in 2026**. V100 did not score the two new finals. Older metrics retain their original denominators and evidence clocks.

2024 and 2025 remain validation seasons. The separately locked 2026 season remains previously exposed test reporting. Evaluation ratios of 50/50, 40/60, 30/70, 20/80 and 10/90 do not change estimator training, sampling, loss weights or base forecasts. No current-season outcome selects a champion or calibrator.

## Measured operations

| V100 operation | Wall seconds | Process CPU seconds | Average CPU-core equivalents |
|---|---:|---:|---:|
| Launch recovery | 728.248 | 768.539 | 1.055 |
| Final checkpoint custody | 56.965 | 73.644 | 1.293 |

Custody processed **6,085 receipts, 553,994 descriptors, 169,455 unique path pins and 59,973 physical dependencies**, reusing 5,414 collection records. It retained the working final parallel verifier and modified zero scientific checkpoints.

These are operational recovery/custody measurements. The configured 36-worker ceiling provides no scientific occupancy result because scientific dispatch was not reached. No three-minute / 75% sustained scientific CPU acceptance is claimed.

## V101 preparation state

**Preparation is in progress. No V101 owner execution has started.** The private executable pin and final acceptance evidence are pending in this draft. The prepared release must reauthenticate the newest durable checkpoint at launch and reuse all authenticated completed science before entering missing or newly registered work.

The finite inherited continuation includes 765 pending source-ablation fitting jobs, split into 510 validation jobs and 255 frozen-test jobs, with 1,530 scoring partitions and 1,530 source-missingness stress partitions. These are planned units, not completed scientific work. V101 also prepares 12 logical census streams and 126 fixed residual-shape policies, with 378 forecast tasks, 378 paired-uncertainty tasks and 1,134 metric comparisons. The distribution extension reuses base estimators; at most 756 distinct residual-parameter fits are registered before exact-identity reuse. The combined T60 comparison has a maximum of 1,570 policies if all eligible branches complete. These additional tasks remain pending owner execution and final preparation acceptance.

The runtime accepts explicit 12, 24 or 36 worker ceilings, bounds native threads, measures scientific PIDs and useful CPU, and keeps the occupancy gate conditional on sufficient eligible independent work. It must never repeat completed fits solely to demonstrate utilization.

## Stage and scope interpretation

The public review includes all 21 numbered V100 stages from the archived child snapshot. Recovery is failed, scientific stages remain pending, and finalization stages reflect that snapshot's timing. The later supervisor return verification and observed exits are recorded separately. A child snapshot taken before closure is not rewritten to fabricate full scientific completion.

The outstanding-work table retains the full census, comparable new-game forecasts, missing source-ablation research, qualified native exchange histories, historical market continuity, remaining football feature producers and separate production publication.

## Reproduce this public review

```bash
python examples/fbs_contracts/v101/build_review.py --check
python tests/test_fbs_v101_public.py
node tests/fbs_v101_browser.test.cjs
```

The semantic tests reject private fields, altered predecessor outcomes, a failed execution relabeled as success, census-expanded metric denominators, test-label selection, unearned fitting/reuse credit, fabricated scientific CPU acceptance, premature executable pins and an invented completed stage manifest. The browser suite checks served/offline desktop/mobile rendering, actual keyboard controls, exact source-byte JSON downloads, visible coverage limits and rejection of corrupted or scientifically false evidence.

Local deterministic generation and the 12 semantic tests have passed during draft preparation. Local browser execution is blocked by the environment's Chromium socket restriction; no local browser pass is claimed. Exact-head hosted validation remains required before merge. Source publication is separate from website deployment.

## Publication boundary

This review contains bounded aggregate FBS evidence only. Owner executables, private handoffs and returns, fitted-state bodies, exact feature transforms, licensed raw feeds, private cloud identifiers and new unissued forecast grids remain excluded. Earlier dated FBS assets and every other sport remain unchanged.
