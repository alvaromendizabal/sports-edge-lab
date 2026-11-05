# Bounded acquisition and honest progress

This credential-free example demonstrates an operational research boundary:
current inventory and useful pregame references should reach evaluation before
an indefinitely expanding historical collection. All test values are invented.
It neither runs a provider collector nor changes the dated public NBA evidence.

The [implementation](work_progress.py) and [failure-case tests](tests/test_work_progress.py)
keep attempts, successful HTTP responses, verified new rows, covered games and
remaining work separate. An alive process or a successful empty response is not
evidence of newly recovered observations. Reusing verified bytes must not earn
new-row credit.

## Phase order

1. Account for every date and game in the current inventory, including explicit
   source failures and unresolved identities.
2. Spend a declared finite budget on priority pregame references.
3. Evaluate qualified model inputs and produce the current report. Retain every
   game even when a model or provider cell is unavailable.
4. Resume deeper historical pages and finer observations from the saved queue.

Budget exhaustion is an operational disposition. It does not mean that a source
has no data or that its historical coverage is complete. Acquisition eligibility
is independent of whether a row qualifies as a model feature. Later recovered
history can support a retrospective comparison while retaining its actual
retrieval clock.

## Telemetry contract

Each phase has a fresh snapshot. An old provider cooldown cannot silently carry
into a different phase. Cumulative counters must advance monotonically within
the same phase, and observations require distinct, timezone-aware clocks.
The example reports meaningful interval data progress only when verified rows
or covered games increase. Completed empty work can still reduce the backlog;
that is different from data gain.

An ETA is returned only for an enumerated queue whose discovery is exhausted,
whose work items have comparable cost, and whose measured completion rate is
positive. It is suppressed during cooldown. This conditional estimate is not a
forecast of unseen source availability, overall research completion or cost.

## Run

From the repository root:

```bash
python -m unittest discover -s tracks/nba/public_monitor/tests -p 'test_work_progress.py' -v
```

The existing NBA CI discovery also runs these tests. No cloud credentials,
network access, licensed observations, private configurations, model states,
actual forecast records or owner execution packages are involved.
