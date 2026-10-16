# Bounded current-data schedule

Deployed and enabled. AWS `CreateRole`, `PutRolePolicy`, `CreateSchedule`, and `GetSchedule` all succeeded. The schedule was created and its configuration read back at **2026-10-16 19:53:27 UTC**. Its first scheduled invocation is still in the future and has not yet been verified.

The deployed configuration matches `create_current_role.json`, `put_current_role_policy.json`, and `create_current_schedule.json`. The verified target uses `infrastructure/code/current-20261016-v026/sports_edge_lab_current_v026_20261016.pyz`. The bound artifact is 20,902 bytes with SHA-256 `43d0e7c256dd71066430793672db31049d7689b0c034e35b32d8b26b1f731a52`.

The collector includes a fresh free-event quota-header check, dynamic outstanding historical commitments, a 100,000-credit remaining reserve floor, atomic per-run budgets, and a conditional 1,200-second S3 lease under `shared/control/current-acquisition/v026-active.json` to stop overlapping collectors. These controls were reported review-cleared by the collector workstream. The separate manual acquisition execution does not establish that the future scheduled invocation has succeeded.

IAM simulations passed eight cases: intended create/tag/pass-role allowed; wrong prefix, GPU type, excessive runtime, wrong workstream tag, expired execution, and alternate role rejected. Full simulation evidence is preserved in `policy_simulation_evidence.json`.

The schedule uses the existing `sports-edge-lab-ingestion` group and a separately scoped `SportsEdgeLabCurrentSchedulerRole`. The NCAA availability one-time schedule and its exact-job role remain separate and unchanged.

- Cadence: `cron(5 3,9,15,21 * * ? *)`, interpreted in UTC.
- Start boundary: 2026-10-17 03:00 UTC.
- First trigger: 2026-10-17 03:05 UTC (October 16, 8:05 PM America/Los_Angeles).
- Final possible trigger: 2026-11-15 21:05 UTC.
- End boundary: 2026-11-16 03:04:59 UTC.
- Total scheduled slots: 120. No flexible window and no delivery retries.
- Per-run limits: 500 odds credits, 100 statistics calls, 600 application seconds, 900 AWS seconds, one `ml.m5.2xlarge`.
- Scheduled acquisition ceiling: 60,000 odds credits and 12,000 statistics calls. These limits exclude the separately launched manual canary and existing historical backfills.
- Maximum reported job-runtime compute at the previously verified $0.461/hour: $13.83 across 120 runs, excluding startup/billing effects, S3 operations and storage, provider subscriptions, and other infrastructure.
- `ActionAfterCompletion: DELETE`; no schedule persists beyond the fixed end boundary. The dedicated IAM role persists but its permissions also expire at that end boundary.

## Unique names

The direct universal SageMaker target can use `sports-edge-lab-current-<aws.scheduler.execution-id>` in `ProcessingJobName`. AWS documents substitution of this context attribute in target Input and says it is unique for each attempted target invocation. AWS's example `d32c5kddcf5bb8c3` produces a valid 39-character name; a 36-character UUID produces 59 characters, below SageMaker's maximum of 63. The documentation does not explicitly contract the execution ID character set or maximum length; invalid future IDs would fail SageMaker validation and would not start compute. Zero retries avoids a second newly named job from Scheduler retry delivery. This has not yet been verified through an actual scheduled invocation.

## Deployment controls and remaining verification

1. The exact uploaded artifact and reviewed CLI arguments are bound in the deployed target.
2. The target sets the 500-credit and 100-statistics-call limits, the 100,000-credit reserve floor, four workers, and the 600-second application limit.
3. The IAM simulation and the successful creation/readback evidence verify the resource permissions and configuration; they do not prove future delivery or collection success.
4. The first scheduled run still requires verification of target delivery, substituted processing job name, collector self-tests, quota/lease checks, and resulting capture report.

## Primary source evidence

- https://docs.aws.amazon.com/scheduler/latest/UserGuide/managing-schedule-context-attributes.html
- https://docs.aws.amazon.com/scheduler/latest/UserGuide/managing-targets-universal.html
- https://docs.aws.amazon.com/scheduler/latest/UserGuide/cross-service-confused-deputy-prevention.html
- https://docs.aws.amazon.com/scheduler/latest/APIReference/API_CreateSchedule.html
- https://docs.aws.amazon.com/scheduler/latest/APIReference/API_RetryPolicy.html
- https://docs.aws.amazon.com/sagemaker/latest/APIReference/API_CreateProcessingJob.html
- https://servicereference.us-east-1.amazonaws.com/v1/sagemaker/sagemaker.json
- https://servicereference.us-east-1.amazonaws.com/v1/iam/iam.json

Verified existing resources: NCAA one-off remains enabled for 2026-10-17 01:05 UTC, with zero retries, automatic deletion, and the correct v022 source prefix. Its role has no attached managed policies and only the exact v022 inline permissions. No existing role or schedule needs to be broadened.
