# Prepared odds-only restart

V037 failed before provider access because its role has no SageMaker management
permissions. Its saved return is `shared/acquisition/paid/20261016T204029Z-1fac91dda7/`.
V038 uses the control-plane observation as an embedded, immutable receipt;
it does not expand worker permissions. The 38 mandatory tests passed locally.

Before deployment, use AWS DescribeProcessingJob to verify
`sports-edge-lab-gap-backfill-20261016-v011` is terminal and has
ProcessingEndTime. Until then, do not launch a replacement. Preserve the exact
returned job name/status/end time and observed_at in `predecessor_terminal.json`.
Package that file with the four source modules in `tools/odds_only_v038/src/`.
Run the PYZ self-tests, record SHA-256 and upload to the canonical private bucket
under `infrastructure/code/odds-only-20261016-v038/`.

Deploy one Processing job `sports-edge-lab-odds-only-20261016-v038` with the
existing SportsEdgeLabProcessingRole, scikit-learn 1.9-0 image in us-west-2,
one ml.m5.2xlarge, 30GB and 2100-second runtime. Before creating, verify that
this exact job does not already exist. The application caps itself at 1800
seconds and 200,000 odds credits, and makes no CFBD/CBBD requests. It verifies
the current account reserve, paces to one source request per second, reuses
successful request indexes and disables the provider after rate/access denial.

Verify runtime tests, quota gate and positive captures. Publish the actual
execution/result evidence, including any failure or bounded stop. Do not call
this prepared code an active or completed download. No additional subscription
or license purchase is part of this restart.

A bounded follow-up is enabled for 2, 3 and 4 p.m. Pacific on October 16, 2026, to perform the guarded restart and verify its outcome. It must not duplicate an existing v038 job.
