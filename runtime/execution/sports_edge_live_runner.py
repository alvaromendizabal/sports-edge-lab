"""Standalone, project-scoped live supervision of an explicitly supplied command.

This launcher does not choose a private runner, acquire data, reserve CPUs, or
infer fits. A cooperating child may publish current measurements to the exact
path in SEL_EXECUTION_PROGRESS_PATH using publish_progress().
"""
from __future__ import annotations

import argparse
import copy
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import threading
import time
import uuid

from sports_edge_live import (LiveExecutionLog, atomic_json, boot_id,
                             process_identity, project_measurements, utc)

PROJECTS = ('nfl', 'fbs', 'nba', 'ncaa_basketball')
PROGRESS_ENV = 'SEL_EXECUTION_PROGRESS_PATH'


class _ReadableLiveLog(LiveExecutionLog):
    """Expose observed descendant PIDs in both human and structured streams."""
    @staticmethod
    def _human(row):
        text = LiveExecutionLog._human(row)
        if row['event'] == 'HEARTBEAT':
            observer_pid = (row.get('producer_identity') or {}).get('pid')
            processes = row['data'].get('process_tree', {}).get('processes', [])
            observed = [{k: process.get(k) for k in ('pid', 'parent_pid', 'start_ticks', 'state')}
                        for process in processes if process.get('pid') != observer_pid]
            text += ('\n  observed_child_processes='+json.dumps(observed, sort_keys=True)
                     +' | observed descendants are not inferred scientific fit workers')
        return text


def publish_progress(measurements, *, environment=None):
    """Publish actual child measurements with an unforgeable-by-state envelope.

    Unknown fields should be absent or null. Fit counters must come from actual
    current-run evidence. This helper makes no model or billing inference.
    """
    env = os.environ if environment is None else environment
    path = Path(env[PROGRESS_ENV])
    identity = process_identity(os.getpid())
    if identity is None:
        raise RuntimeError('LIVE_PROGRESS_PRODUCER_IDENTITY_UNAVAILABLE')
    state = copy.deepcopy(dict(measurements))
    state.update({'schema': 'sports-edge-lab.bound-progress.v1',
                  'invocation_id': env['SEL_EXECUTION_INVOCATION_ID'],
                  'invocation_origin': json.loads(env['SEL_EXECUTION_ORIGIN_JSON']),
                  'producer_identity': identity, 'at_utc': utc()})
    return atomic_json(path, state)


class _TrackedChild:
    """Serialize reaping and signal forwarding for this exact direct child.

    No other code receives the underlying Popen handle. With the reaping lock
    held, a child observed alive cannot have its PID recycled before os.kill:
    an exited child remains our unreaped child until a guarded poll/wait.
    This avoids numeric-PID races without requiring optional pidfd bindings.
    """
    def __init__(self, command, environment):
        self._lock = threading.RLock()
        self._process = subprocess.Popen(command, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, env=environment, start_new_session=True)

    @property
    def pid(self):
        return self._process.pid

    @property
    def stdout(self):
        return self._process.stdout

    @property
    def stderr(self):
        return self._process.stderr

    @property
    def returncode(self):
        return self._process.returncode

    def poll(self):
        with self._lock:
            return self._process.poll()

    def wait(self):
        with self._lock:
            return self._process.wait()

    def forward_signal(self, number):
        with self._lock:
            if self._process.poll() is not None:
                return False
            try:
                os.kill(self.pid, number)
            except ProcessLookupError:
                return False
            return True

    def close_pipes(self):
        for stream in (self.stdout, self.stderr):
            if stream is not None:
                stream.close()


class _SignalRelay:
    """Signal handlers only append; forwarding never runs inside a handler."""
    def __init__(self, logger):
        self.logger = logger
        self.pending = []
        self.observed = []
        self.old_handlers = {}
        self.stop = threading.Event()
        self.child = None
        self.thread = None

    def __enter__(self):
        for number in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
            self.old_handlers[number] = signal.getsignal(number)
            signal.signal(number, self._handler)
        self.thread = threading.Thread(target=self._loop,
                                       name='sel-exact-child-signal-relay', daemon=True)
        self.thread.start()
        return self

    def _handler(self, number, frame):
        self.pending.append(number)

    def _loop(self):
        while not self.stop.wait(.05):
            if self.child is None:
                continue
            while self.pending:
                number = self.pending.pop(0)
                sent = self.child.forward_signal(number)
                receipt = {'signal': number, 'forwarded': sent,
                           'child_pid': self.child.pid,
                           'scope': 'THIS_INVOCATION_DIRECT_CHILD_ONLY',
                           'unrelated_processes_signaled': 0}
                self.observed.append(receipt)
                self.logger._safe_event('SUPERVISOR_SIGNAL_OBSERVED', **receipt)

    def __exit__(self, *args):
        self.stop.set()
        self.thread.join(timeout=2)
        for number, handler in self.old_handlers.items():
            signal.signal(number, handler)


def _run_directory(root, project, run_id):
    if not re.fullmatch(r'[A-Za-z0-9_.-]{1,128}', run_id) or run_id in ('.', '..'):
        raise ValueError('INVALID_RUN_ID')
    base = Path(root).absolute()
    directory = base / 'projects' / project / 'logs' / run_id
    if any(path.is_symlink() for path in (directory, *directory.parents)):
        raise ValueError('LIVE_RUN_SYMLINK_PATH_REJECTED')
    directory.parent.mkdir(parents=True, exist_ok=True)
    directory.mkdir(mode=0o700, exist_ok=False)
    return directory


def run_command(command, *, root, project, release, run_id=None, interval=10.,
                stall_seconds=120., console=None):
    """Supervise one explicit command; return its exact subprocess returncode."""
    if project not in PROJECTS:
        raise ValueError('UNKNOWN_PROJECT')
    if not command:
        raise ValueError('EXPLICIT_CHILD_COMMAND_REQUIRED')
    if not 10. <= float(interval) <= 15.:
        raise ValueError('LIVE_INTERVAL_MUST_BE_10_TO_15_SECONDS')
    run_id = run_id or time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())+'_'+uuid.uuid4().hex[:12]
    directory = _run_directory(root, project, run_id)
    origin = {'schema': 'sports-edge-lab.invocation-origin.v1', 'at_utc': utc(),
              'monotonic_seconds': time.monotonic(), 'boot_id': boot_id()}
    prefix = directory / 'LIVE_EXECUTION'
    progress = directory / 'LIVE_PROGRESS.json'
    child = None
    error = None
    returncode = None
    signals = []
    logger = _ReadableLiveLog(prefix, project=project, release=release,
        invocation_id=run_id, invocation_origin=origin, interval=interval,
        stall_seconds=stall_seconds, console=console)
    with logger:
        logger.update_state({'stage_name': 'CHILD_STARTING', 'status': 'STARTING',
            'training_progress': 'AWAITING_CURRENT_BOUND_CHILD_MEASUREMENTS',
            'eta_uncertainty': 'NO_CURRENT_BOUND_WORK_DENOMINATOR_OR_RATE',
            'cost': {'status': 'NO_CURRENT_BOUND_WORKLOAD_COST_REPORTED',
                     'actual_billed_cost_usd': None}})
        with _SignalRelay(logger) as relay:
            environment = logger.environment()
            environment[PROGRESS_ENV] = str(progress)
            try:
                child = _TrackedChild(command, environment)
            except OSError as exc:
                error = {'type': type(exc).__name__, 'message': str(exc)}
                returncode = 127 if isinstance(exc, FileNotFoundError) else 126
                logger._safe_event('CHILD_LAUNCH_FAILED', error=error,
                                   returncode=returncode, command_arguments_logged=False)
            else:
                relay.child = child
                # A very short command may exit before registration. The shared
                # supervisor records that case and preserves its output/exit.
                identity = process_identity(child.pid)
                if identity is not None:
                    logger.bind_progress(progress, identity)
                logger.update_state({'stage_name': 'CHILD_RUNNING', 'status': 'RUNNING'})
                try:
                    returncode = logger.supervise(child)
                finally:
                    child.close_pipes()
                logger.update_state({'status': 'CHILD_EXIT_OBSERVED'})
        signals = list(relay.observed)
    receipt = {'schema': 'sports-edge-lab.generic-supervisor-receipt.v1',
               'project': project, 'release': release, 'run_id': run_id,
               'run_directory': str(directory), 'child_returncode': returncode,
               'child_signal': -returncode if returncode is not None and returncode < 0 else None,
               'launch_error': error, 'signals': signals,
               'signal_forwarding_scope': 'THIS_INVOCATION_DIRECT_CHILD_ONLY',
               'unrelated_processes_signaled': 0,
               'command_arguments_logged': False,
               'live_log': logger.receipt(),
               'last_bound_workload_measurements': project_measurements(logger.state),
               'scientific_progress_inferred_from_process_activity': False,
               'supervisor_cloud_requests': 0,
               'private_runner_automatically_replaced': False,
               'all_deployed_projects_activated': False}
    atomic_json(directory/'LIVE_EXECUTION_RECEIPT.json', receipt)
    return returncode, receipt


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', choices=PROJECTS, required=True)
    parser.add_argument('--root', required=True, help='Existing Sports Edge Lab project root')
    parser.add_argument('--release', required=True, help='Actual child release identity')
    parser.add_argument('--run-id')
    parser.add_argument('--interval', type=float, default=10.)
    parser.add_argument('--stall-seconds', type=float, default=120.)
    parser.add_argument('command', nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    command = args.command[1:] if args.command[:1] == ['--'] else args.command
    if not command:
        parser.error('an explicit existing child command is required after --')
    try:
        code, receipt = run_command(command, root=args.root, project=args.project,
            release=args.release, run_id=args.run_id, interval=args.interval,
            stall_seconds=args.stall_seconds, console=sys.stdout)
    except (ValueError, FileExistsError) as exc:
        parser.error(str(exc))
    print('LIVE_EXECUTION_RECEIPT='+str(Path(receipt['run_directory'])/'LIVE_EXECUTION_RECEIPT.json'), flush=True)
    if code < 0:
        # Save/flush the receipt first, then retain POSIX signal-exit semantics.
        number = -code
        if number not in (signal.SIGKILL, signal.SIGSTOP):
            signal.signal(number, signal.SIG_DFL)
        os.kill(os.getpid(), number)
        return 128 + number
    return code


if __name__ == '__main__':
    raise SystemExit(main())
