# Injury reports at a pregame cutoff

This credential-free example uses invented teams, players, reports and clocks. It demonstrates how to select injury information for a declared pregame horizon. It makes no statement about a live game, a fitted injury model, forecast accuracy or profit.

Run from the repository root:

```bash
python -m tracks.nba.public_monitor.injury_asof
python -m unittest discover -s tracks/nba/public_monitor/tests -p 'test_injury_asof.py' -v
```

## Selection rules

| View | Eligible publication clock | Eligible possession clock | Meaning |
|---|---|---|---|
| T120 | At or before tip minus 120 minutes | At or before the same cutoff | Information actually held at that boundary |
| T60 | At or before tip minus 60 minutes | At or before the same cutoff | A separate, later boundary |
| Latest before tip | Strictly before tip | Strictly before tip | The latest eligible pregame snapshot; no claim of a T60 issue |
| Publication reconstruction | Same boundary for the chosen horizon | Preserved, but not used to claim historical possession | A retrospective reconstruction that may use a report acquired later |

A report retains its publication clock and actual possession clock. A later download cannot establish earlier possession. Missing possession time is an explicit gap. Timezone offsets are required and compared in UTC.

Selection matches the exact event and team, then chooses a whole team report. Players absent from the selected report do not inherit their older status. An unsubmitted report, unknown submission state, incomplete parse, unknown player status, or conflicting reports at one publication clock blocks admitted player rows. None means healthy. Even a submitted report with no listed players provides no assertion about a specifically requested player.

Statuses remain categorical. The example does not convert Questionable or Doubtful into absence probabilities and does not turn a contract probability into a point adjustment. It coalesces exact report repeats and rejects changed content under an immutable report identity.

## Four preregistered experiment arms

| Arm | Purpose | Example execution state |
|---|---|---|
| Fixed baseline | Retain an unchanged control | Registered, not executed |
| Injury only | Evaluate the information in injury inputs | Blocked until causal inputs are available |
| Baseline plus injury | Measure incremental value on the same games | Blocked until causal inputs are available |
| Injury interactions | Test injury combinations and replacement context | Blocked until causal inputs are available |

The generic protocol fixes prior-season chronological recipe selection and a weekly refit cadence. Preprocessing, calibration and label availability must satisfy the training origin. Current-season outcomes cannot select a challenger or revise earlier forecasts. Minutes, player contributions and replacement context need their own causal evidence before an impact feature can be computed. Registration and feature preparation earn no fit or forecast credit.

This module only defines and tests these contracts. It performs zero downloads, fits, issued forecasts or orders. Actual source collection, provider rights, PDF parsing, player resolution, model design, evaluation and deployment remain separate work.

## Validation

The synthetic tests cover distinct horizons, inclusive cutoff and exclusive tip boundaries, late possession, unknown clocks, unsubmitted and incomplete reports, absence without health inference, immutable identity conflicts, exact event/team matching and four arms without fitting. Existing public monitoring evidence and metrics are unchanged.
