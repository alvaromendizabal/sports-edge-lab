# Shared live execution logging

[NBA execution evidence](../../tracks/nba/reports/latest_execution_review.json) · [Public/private boundary](../../docs/PUBLICATION_BOUNDARY.md)

Every Sports Edge Lab runner must write a separate, continuously readable execution `.log` and a machine-readable `.jsonl` stream. This directory publishes the actual generic framework used by the replacement NBA B082 runner. NFL, FBS, NBA, NCAA basketball and other named projects can use the same implementation. Publication of this module does not establish that previously deployed non-NBA executables have been retrofitted.

The standard-library implementation runs on Linux, uses process identity and append-only files, and requires no scientific library or cloud credential for local use. It does not train a model, generate observations or infer scientific progress from CPU usage. Its cloud sink accepts an existing caller-owned client; it does not create credentials, change infrastructure, list historical objects or download data.

## Permanent runner contract

- Start a distinct log prefix and invocation identity before launching any substantial child work. Preserve prior log bytes across failures or restarts. Read the human stream with `tail -F`.
- Emit and flush status independently of the workload at a default 10-second cadence, with a maximum configured interval of 15 seconds. Record the measured maximum interval and fail the interval gate if it exceeds 15 seconds. A blocked child must not prevent observations.
- Capture child stdout and stderr, including partial output without a newline. Preserve exit status, exceptions, diagnostic evidence and checkpoint locations. A child-registration log-write failure keeps the actual child bound and enters the supervisor drain loop, so an observer failure does not abandon the process.
- Protect the envelope identity from callback data. Validate invocation, origin, boot, process ID and process start time before accepting a progress document. A foreign or stale document supplies no accepted progress.
- Report UTC, elapsed time, stage, completed and remaining work, throughput and ETA when the current workload reports them. Missing values remain null with an explicit reason.
- Report observed process CPU, memory, disk availability, reserved cores and active workers separately. Concurrent scientific fits and completed, reused or failed fits come from current bound workload evidence; reservations and CPU samples never manufacture fit counts.
- Preserve current bound model families, training events, evaluation aggregates, champion changes, transfer/cache counters and cost estimates when reported. An estimate is not an actual bill. Costs or workload measurements that are not reported remain unavailable.
- Detect unchanged progress after the configured stall interval using separate operational-work and native-fit-completion clocks. Successful cache reads, authenticated verification and completed S3 transfers can advance operational progress; attempts, failures, CPU changes, a newly visible historical receipt or a counter reset cannot. Overlapping scopes are never summed. Logger observations continue while the child is blocked or failing.
- Label Python stacks as `LOGGER_PROCESS_ONLY`. The observer stack does not establish the child Python stack. Keep child process identity, wait state and the explicit absence of observed child frames separate; preserve the legacy stack alias with the same scope label.
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

## Per-invocation bootstrap adapter

`sel_live_logging.py` uses the existing shared logger without changing its bytes. It creates the exact `LIVE_EXECUTION.log` and `LIVE_EXECUTION.jsonl` filenames under a new `sports-edge-lab/projects/<project>/logs/<invocation>/` directory. Its four selectors are `nfl`, `fbs`, `nba` and `ncaa_basketball`. Start it before package authentication so an immediate identity error has a durable diagnostic stream. A reused invocation directory, unsupported selector, aliased path or interval outside 10–15 seconds fails explicitly.

```python
from pathlib import Path
from sel_live_logging import new_run, observe, error, close

# Call before authenticating or importing the existing project runner.
log = new_run(Path("working-cache"), "fbs", release="integration", flush_seconds=10)
status = "FAILED"
try:
    observe(log, stage_name="PACKAGE_AUTHENTICATION")
    # Authenticate and run the existing runner here. Bind its trusted, current
    # workload callback to observe(log, event); preserve its scientific gates.
    status = "COMPLETED"
except BaseException as exc:
    error(log, exc)
    raise
finally:
    logging_receipt = close(log, status=status)
```

This is an integration skeleton; the comments do not perform authentication or scientific work. The adapter maps bounded, known scalar event fields and coalesces updates in memory so a slow log write does not hold a scientific callback behind the logger's filesystem lock. Worker CPU and identity observations remain the shared logger's own measurements. New, reused, native, meta and active optimizer counts retain their reported scopes; callback activity is not a completed fit. Cache and S3 snapshots are not added across overlapping lanes. Missing costs, progress denominators or ETAs remain unavailable. Inspect the returned receipt for interval failures, observer errors and a close still pending on I/O; an execution exit code does not override these conditions.

The adapter has NFL event aliases and accepts common explicit fields from other projects. A project must bind its actual producer and counters before those fields can be reported. The module and its four-selector tests do not rewrite existing FBS, NBA or NCAA executables, establish owner execution, reserve CPUs or authenticate any model result. The private delivery's pinned delegate wrapper is a separate integration; it may observe an explicitly selected existing executable but cannot supply counters that executable never reports. Every deployed integration still needs its own identity, failure-path and live-interval verification.

## Verification

Run the generic regression suite from the repository root:

```sh
python -m unittest discover -s runtime/execution -p 'test_sports_edge_live.py' -v
python -m unittest discover -s runtime/execution -p 'test_live_logging.py' -v
python runtime/execution/verify_live_execution.py
```

The 27-test suite includes nine new invented progress-counter and failed-child regressions. It executes real local child processes and checks identity protection, active-writer exclusion, restarts, no-newline output, stopped progress, failed children, observer errors, bounded incremental checkpoint recovery, checksum rejection and safe log snapshots. They use invented observations and temporary files. Their process activity and mock transfers are not NBA fits or owner-cloud throughput.

The adapter suite verifies all four project directories, earliest authentication failures, secret redaction, safe counters, concurrent callbacks, blocked observer I/O, observer errors and immutable snapshots. Its real 31-second child checks heartbeat spacing at the production ten-second interval, process samples, physical stream flush calls and partial stdout. Unreported model counts remain null. These observations establish logging behavior, not scientific fit concurrency or owner throughput.

The separate live acceptance script runs a 33-second lock-blocked child and a 27-second failing child concurrently. It observes the actual human log with `tail -F`, checks simultaneous JSONL growth, captures both streams, verifies the child in process samples and enforces maximum heartbeat gaps of 15 seconds at the real ten-second setting. This is a failure-injection test, not a synthetic CPU load benchmark or sports fit. Temporary local evidence is written beneath the module directory.

The existing public-review workflow runs these tests on Python 3.11 and 3.12. The NBA report has a separate source-preservation validator and hosted desktop/mobile/offline browser check. Exact-head CI, a repository merge, an owner execution and a deployed website remain different evidence states.

## Successful-work observation and native-fit evidence

`ProgressObservation` is part of this standalone module. The logger can be loaded as a manifest-pinned bridge before sibling modules become importable. No separate runtime helper is needed. Successful operational counters are compared within their own reported scopes; a newly appearing cumulative receipt establishes a baseline and does not retroactively establish progress in the current interval. Native returned-fit counters have an independent idle clock, so a long source transfer does not appear as ongoing model training.

The NBA B081 saved log contained one false stall while successful GETs increased from 16 to 5,618. The repaired comparison recognizes that observed transfer progress while keeping the native-fit idle clock unchanged. The public regression uses invented counters and a real local child that waits and exits with code 7. Private original telemetry stays outside this repository. The published NBA execution evidence reports the saved owner's actual measurements separately.
