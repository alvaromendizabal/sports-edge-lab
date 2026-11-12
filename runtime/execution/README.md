# Shared live execution logging

[NBA execution evidence](../../tracks/nba/reports/latest_execution_review.json) · [Public/private boundary](../../docs/PUBLICATION_BOUNDARY.md)

Every Sports Edge Lab runner must write a separate, continuously readable execution `.log` and a machine-readable `.jsonl` stream. This directory publishes the actual generic framework used by the replacement NBA B079 runner. NFL, FBS, NBA, NCAA basketball and other named projects can use the same implementation. Publication of this module does not establish that previously deployed non-NBA executables have been retrofitted.

The standard-library implementation runs on Linux, uses process identity and append-only files, and requires no scientific library or cloud credential for local use. It does not train a model, generate observations or infer scientific progress from CPU usage. Its cloud sink accepts an existing caller-owned client; it does not create credentials, change infrastructure, list historical objects or download data.

## Permanent runner contract

- Start a distinct log prefix and invocation identity before launching any substantial child work. Preserve prior log bytes across failures or restarts. Read the human stream with `tail -F`.
- Emit and flush status independently of the workload at a default 10-second cadence, with a maximum configured interval of 15 seconds. Record the measured maximum interval and fail the interval gate if it exceeds 15 seconds. A blocked child must not prevent observations.
- Capture child stdout and stderr, including partial output without a newline. Preserve exit status, exceptions, diagnostic evidence and checkpoint locations. A child-registration log-write failure keeps the actual child bound and enters the supervisor drain loop, so an observer failure does not abandon the process.
- Protect the envelope identity from callback data. Validate invocation, origin, boot, process ID and process start time before accepting a progress document. A foreign or stale document supplies no accepted progress.
- Report UTC, elapsed time, stage, completed and remaining work, throughput and ETA when the current workload reports them. Missing values remain null with an explicit reason.
- Report observed process CPU, memory, disk availability, reserved cores and active workers separately. Concurrent scientific fits and completed, reused or failed fits come from current bound workload evidence; reservations and CPU samples never manufacture fit counts.
- Preserve current bound model families, training events, evaluation aggregates, champion changes, transfer/cache counters and cost estimates when reported. An estimate is not an actual bill. Costs or workload measurements that are not reported remain unavailable.
- Detect unchanged progress after the configured stall interval and emit process-tree, wait-state and Python stack diagnostics. Logger observations must continue while the child is blocked or failing.
- Periodically checkpoint bounded compressed increments through the injected sink. The default interval is 300 seconds and the minimum is 30 seconds. Reuse prior acknowledged offsets, cap chunk size and retain local bytes after failures. A returned ETag is not a SHA-256 checksum.
- Capture a stable, read-back-verified log prefix for a return artifact. Authenticate the current invocation and sequence order, and exclude an incomplete JSONL tail. Events after the captured prefix remain in the live external files; the snapshot states that limitation explicitly.

The interval receipt is an observed engineering result. No userspace logger can guarantee scheduled execution during a stopped host, kernel stall or storage failure. The runner must retain and expose failed interval or checkpoint gates instead of claiming uninterrupted logging.

## Minimal integration

Use a caller-selected project directory and an original invocation identity. The example below only demonstrates supervision of an existing command; it creates no scientific task or cloud resource.

```python
from pathlib import Path
import subprocess

from sports_edge_live import LiveExecutionLog

prefix = Path("project-logs") / "execution-unique-invocation"
with LiveExecutionLog(prefix, project="nba", release="example", interval=10) as log:
    child = subprocess.Popen(
        ["python", "existing_project_runner.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=log.environment(),
    )
    exit_code = log.supervise(child)
    receipt = log.receipt()
```

The module directory must be on the import path. Production wrappers also bind their progress document to the actual producer identity and connect their existing transfer, resource and scientific-event counters. `project_measurements` documents the accepted state fields. `update_state` accepts current workload state; unknown quantities should remain absent or null. Retain the execution exit code separately from logging verification.

`IncrementalLogCheckpoint` accepts an injected `put` function. `S3LogSink` can adapt an already authorized, bounded-timeout client and caller-selected destination. Its request and byte counters describe SDK calls and supplied bodies, not unobserved internal retry traffic. Unit tests use a fake sink only and perform no cloud request.

## Verification

Run the generic regression suite from the repository root:

```sh
python -m unittest discover -s runtime/execution -p 'test_sports_edge_live.py' -v
python runtime/execution/verify_live_execution.py
```

The tests execute real local child processes and check identity protection, active-writer exclusion, restarts, no-newline output, stopped progress, failed children, observer errors, bounded incremental checkpoint recovery, checksum rejection and safe log snapshots. They use invented observations and temporary files. Their process activity and mock transfers are not NBA fits or owner-cloud throughput.

The separate live acceptance script runs a 33-second lock-blocked child and a 27-second failing child concurrently. It observes the actual human log with `tail -F`, checks simultaneous JSONL growth, captures both streams, verifies the child in process samples and enforces maximum heartbeat gaps of 15 seconds at the real ten-second setting. This is a failure-injection test, not a synthetic CPU load benchmark or sports fit. Temporary local evidence is written beneath the module directory.

The existing public-review workflow runs these tests on Python 3.11 and 3.12. The NBA report has a separate source-preservation validator and hosted desktop/mobile/offline browser check. Exact-head CI, a repository merge, an owner execution and a deployed website remain different evidence states.
