# When one blocked fold stopped useful research

[Project](../README.md) · [Basketball dashboard](basketball/index.html) · [Sanitized execution evidence](evidence/2026-10-28-basketball-b008-execution.json) · [Executable continuation](../examples/basketball_contracts/continuation.py) · [Tests](../examples/basketball_contracts/tests/test_continuation.py)

B008 executed on October 28, 2026 and returned `BLOCKED_DATA_CONTRACT`. It produced useful forecast output, but its research stage never reached a fit. The review found a control-flow problem: preparation validated every fold before admitting any model work, and the first fold's insufficient calibration support aborted preparation for all the later folds. Separately, acquisition correctly stopped at an incomplete archive inventory. These findings come from the authenticated owner return summarized in the [aggregate evidence](evidence/2026-10-28-basketball-b008-execution.json).

## What actually ran

| Observed B008 result | Verified aggregate |
|---|---:|
| New real model fits / new fit attempts | 0 / 0 |
| Cumulative real estimator units | 238 |
| New public source requests | 8 |
| Paid provider requests / credits charged or reserved | 0 / 0 |
| Additional forecast versions | 110 |
| Total archived forecast versions / unique games | 440 / 61 |
| Settled forecast versions / actual orders | 0 / 0 |

Both original research and included-credit approvals were recorded. Their existence did not bypass the acquisition gates. Incomplete inventory blocked the paid stage before a provider credential or probe was necessary, so this run did not verify live subscription entitlement or remaining provider quota. Zero charged credits is an observed execution fact; it is not evidence of unlimited future allowance. [Execution evidence](evidence/2026-10-28-basketball-b008-execution.json)

The 110 new forecast versions cover the same 61 game identities already represented in the archive. They increase the version count from 330 to 440 without increasing the game count. None is settled at this snapshot, so no prospective accuracy or profit is established. B003 remains the latest fully completed real modeling release; B004 added six units before its earlier request-limit stop. The retained [full league leaderboards](BASKETBALL_RESULTS.md) and [interactive comparison panels](basketball/index.html) remain available.

## Isolate support failures without changing the experiment

A support failure describes a particular fold under a particular registered partition. It does not establish that all other folds lack support. The continuation processes fold preflight independently, records the blocked fold, and allows other eligible folds to reach their own next stage.

The [public implementation](../examples/basketball_contracts/continuation.py) demonstrates this with invented counts: one fold has seven calibration rows against a fixed minimum of ten, while two other folds have sufficient support. The minimum stays unchanged. The output records one blocked fold and two eligible preflights; it claims no fit, model improvement or owner execution. The tests also prove that a changed cohort identity or corrupt input propagates as an error instead of being swallowed as another support failure.

A revised calibration partition needs a distinct registered experiment identity. It cannot silently replace the partition of a previously registered experiment or be counted as its completion. Current-season outcomes remain excluded from recipe selection, and historical validation cohorts remain explicit. Eligibility alone does not establish that subsequent feature checks, resource admission, fitting or evaluation will succeed.

## Keep the original authority and original budget baseline

A release change must not create a fresh allowance. The new continuation receipt retains the original authorization and the counter values recorded before that authorization window began. The exact authenticated source and return identities remain part of the private evidence chain. The public example uses invented identities and independently supplied expected receipt pins; hashing a caller-supplied object does not by itself establish owner consent.

The distinction is concrete in the example. An original archive window begins after three pages and permits twelve additional pages. Its absolute ceiling is fifteen. After eleven pages have been consumed, a continuation has four pages left. Resetting the baseline to eleven would incorrectly turn the same twelve-page allowance into a ceiling of twenty-three. The tests reject that reset, changed limits, changed source identity, missing paid approval and missing cumulative counters.

The actual B008 approved cumulative ceilings were 8,100 active seconds and 168 public requests. The returned snapshot records 56 cumulative public requests and a maximum measured active floor of 4,839.774 seconds. It also contains an open finalization reservation through 5,017.770 seconds. That reservation is not measured spend. Without an exact matching live closing receipt, the conservative carry leaves approximately 3,082.230 seconds before later work is charged. The global active-time and public-request ceilings did not cause the observed stop. [Resource evidence](evidence/2026-10-28-basketball-b008-execution.json)

An exact live closure can resolve the reservation before continuation adopts its floor. Once a conservative floor has been adopted, a later lower receipt cannot refund it. Matching requires the same source, invocation, attempt and valid closing state; a vaguely similar receipt is insufficient. The public numeric helper illustrates the monotonic arithmetic, while the private evidence verifier remains responsible for authenticating those identities and clocks. No additional B009 allowance is granted.

## Preserve the reason a gap remains

The [existing recovery planner](HISTORICAL_ODDS_RECOVERY.md) now attaches provenance to each event/cutoff/market/region cell: the declared inventory-scope pin, canonical binding receipt, required query identity and any matching captured-response receipts. It distinguishes three cases: usable archived evidence; a captured query without an eligible observation; and a query not found in the declared inventory.

These categories support different actions. A valid cached observation can be reused. An empty or stale captured response retains its content and receipt pins, remains uncovered, and does not justify buying the same exact historical response again on every restart. A query missing from the inspected inventory remains a scoped absence, subject to entitlement, quota, approval, timing and shared-account coordination before any real dispatch. No category proves that a bookmaker never offered the game.

The durable quota journal reserves a request and its maximum credit cost before dispatch could occur. If the process loses the response, reopening retains both charges. A verified zero-credit completion releases the credit reservation while retaining the consumed HTTP request. A repeated completion preserves the original receipt; a conflicting completion fails. The new continuation walkthrough exercises this existing journal rather than replacing it with a second independent budget.

## Reproduce the engineering evidence

Run from the repository root with Python 3.11 or 3.12 on POSIX. No credentials, network access or external dependencies are needed for these checks.

```bash
python -m unittest discover -s examples/basketball_contracts/tests -p test_continuation.py -v
python -m unittest discover -s examples/basketball_contracts/tests -p test_recovery_plan.py -v
python -m examples.basketball_contracts.continuation
python -m examples.basketball_contracts.recovery_plan
python -m examples.basketball_contracts.build_basketball_dashboard --check
node examples/basketball_contracts/tests/test_dashboard.cjs
```

The basketball dashboard keeps all 235 saved scorecards, 24 populated comparison panels and 120 overlap specifications. Historical winners remain confined to their exact comparison population, and the current-season monitoring panel never ranks models by outcomes. The prior B006 recovery snapshot remains visible with its historical budget context; B008 appears as the latest authenticated execution. Football and March Madness material is unchanged.

B009 owner execution remains pending. Local tests establish the behavior of these invented contracts and the consistency of the published aggregate report. They do not establish recovered provider data, a completed real model batch, a better forecast or profitable execution. The portfolio assessment remains 8.5/10 because the new engineering evidence does not establish additional predictive or economic qualification.
