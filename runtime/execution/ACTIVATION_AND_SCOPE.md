# Permanent project logging: executable activation and current evidence

The shared implementation is reused byte for byte from repository commit
`f20b5cc070ff45e661b84907fa7e4f735d62c8ec`. Its SHA-256 is
`4cd17825265aa0839392482c3387c94e8cfbf65a57874b4a3d427b028565ca5b`.
`sports_edge_live_runner.py` adds an actual command-line entry point for each of
`nfl`, `fbs`, `nba`, and `ncaa_basketball` without selecting or rewriting the
owner's private executable.

Each invocation creates an exclusive new directory at
`ROOT/projects/PROJECT/logs/RUN_ID/` containing `LIVE_EXECUTION.log`,
`LIVE_EXECUTION.jsonl`, and the terminal `LIVE_EXECUTION_RECEIPT.json`.
An existing run directory is rejected before launching the child. Prior bytes
are preserved. The default heartbeat interval is ten seconds; the CLI accepts
only ten through fifteen seconds. The process observer is independent of the
child workload and continues during blocked or silent work. Child stdout and
stderr are captured, including partial lines. The terminal receipt records
measured cadence, logging health, actual exit status and signal forwarding.

Pass the exact existing owner command after `--`. The following is an interface
example, not a replacement owner command or evidence that a private release was
installed:

```sh
python sports_edge_live_runner.py --project nfl --root /path/to/sports-edge-lab --release ACTUAL_RELEASE -- python /path/to/existing_owner.pyz
```

The other selectors are `fbs`, `nba`, and `ncaa_basketball`. Release identity and
the actual child command remain caller supplied. The supervisor performs no
cloud request, provider purchase, data migration, CPU reservation, model fit,
checkpoint alteration, or private executable replacement itself. The child
retains its existing scientific, resource, cost and cloud authorization gates.

The child gets `SEL_EXECUTION_PROGRESS_PATH`, invocation ID, invocation origin
and log-prefix variables. A cooperating Python child can import
`publish_progress` from `sports_edge_live_runner` (with this module directory on
its import path) and publish its actual current-run measurements. The helper
binds the producer PID, start time, boot identity and current timestamp. Caller
data cannot override the envelope. The observer accepts only the registered
child's current invocation. Unreported quantities remain null with an explicit
reason: CPU activity is never a substitute for fit, throughput, cache, S3,
checkpoint or cost evidence. A private launcher that delegates progress to
another producer needs an explicit authenticated integration; this wrapper does
not guess which descendant owns a progress file.

SIGTERM, SIGINT and SIGHUP received by the wrapper are forwarded only to the
exact direct child created by that invocation. Handlers only queue signals; a
separate relay serializes forwarding against child reaping to prevent PID reuse
races. The child remains responsible for its own descendants and graceful
checkpoint policy. There is no automatic kill after a stall. A child that
ignores a signal continues to be observed. The wrapper writes its receipt before
reproducing a child's POSIX signal exit; a normal nonzero child exit remains
nonzero and is never changed to success by logging.

## Evidence boundary by project

| Project | Authenticated source and activation evidence available here |
|---|---|
| NCAA basketball | The exact R6 owner source and return are local and authenticated. R7 integrates logging in its prepared executable; owner activation requires the next actual return. |
| NBA | The current repository records actual B081 owner logging and prepared B082 use of the same shared logger. The private B082 executable is not present in the repository or this NCAA return. No replacement was made by this work. |
| NFL | Initial pinned evidence is actual N083 and prepared N084. The later main commit `150921430215422df86316e79e68f19b3a170d50` adds the N084 bootstrap failure trace and public N085 `sel_live_logging.py` adapter using the same unchanged shared logger. Those changes and their tests are retained. Private executable bytes and production activation are not verified here. |
| FBS | Current repository evidence is partial actual V055 and prepared V056. Private executable bytes are not present; this tested explicit supervisor is available, while production integration is not verified. |

Nine focused tests exercise real local child processes, all four project
selectors, simultaneous ten-second observations, exact nonzero/signal exits,
scoped forwarding with an unrelated process left alive, current-bound progress,
missing commands, traversal rejection and prior-log preservation. These are
engineering tests with invented observations and no sports data. They establish
no scientific fit count, twelve-core sports utilization, owner-host throughput,
paid-source reduction, private runner installation, or full-season forecast
coverage.
