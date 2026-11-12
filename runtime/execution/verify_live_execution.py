"""Real 10-second logging acceptance with blocked and crashed subprocesses."""
from __future__ import annotations
import concurrent.futures
import datetime as dt
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time
from sports_edge_live import LiveExecutionLog, atomic_json, boot_id, utc


def pin(path):
    body = Path(path).read_bytes()
    return {'bytes': len(body), 'sha256': hashlib.sha256(body).hexdigest()}


def run_case(directory, mode):
    directory.mkdir(parents=True, exist_ok=False)
    prefix = directory/'execution'; lock = None; unlocker = None
    origin = {'schema': 'sel.nba.invocation_clock.v1', 'at_utc': utc(),
              'monotonic_seconds': time.monotonic(), 'boot_id': boot_id()}
    if mode == 'stall':
        lock = (directory/'held.lock').open('wb')
        fcntl.flock(lock, fcntl.LOCK_EX)
        unlocker = threading.Timer(33, lambda: fcntl.flock(lock, fcntl.LOCK_UN))
    growth = []; tail_events = []; tail = None; tail_thread = None
    monitor_stop = threading.Event()
    with LiveExecutionLog(prefix, project='nba', release='B079_LOGGING_FIXTURE',
            invocation_id='live-'+mode, invocation_origin=origin,
            interval=10., stall_seconds=20.) as logger:
        child = subprocess.Popen([sys.executable, '-u', str(Path(__file__).with_name('live_fixture_worker.py')),
                                  '--mode', mode, '--root', str(directory)],
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=logger.environment())
        identity = logger.set_child(child.pid); logger.bind_progress(directory/'PROGRESS.json', identity)
        # Observe the same named file with real tail -F while the child is alive.
        tail = subprocess.Popen(['tail', '-n', '+1', '-F', str(prefix)+'.log'],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        def tail_reader():
            for line in tail.stdout:
                if ' HEARTBEAT ' in line:
                    tail_events.append({'observed_at_utc': utc(), 'child_running': child.poll() is None,
                                        'line': line.strip()})
        tail_thread = threading.Thread(target=tail_reader, daemon=True); tail_thread.start()
        def observe_growth():
            while not monitor_stop.wait(.25):
                growth.append({'monotonic': time.monotonic(), 'child_running': child.poll() is None,
                               'log_bytes': logger.paths['log'].stat().st_size,
                               'jsonl_bytes': logger.paths['jsonl'].stat().st_size})
        watcher = threading.Thread(target=observe_growth); watcher.start()
        if unlocker: unlocker.start()
        try:
            code = logger.supervise(child)
            snapshot = logger.snapshot(directory/'return_snapshot')
        finally:
            monitor_stop.set(); watcher.join()
            if unlocker: unlocker.join()
            if lock: lock.close()
            child.stdout.close(); child.stderr.close()
            tail.terminate(); tail.wait(timeout=3); tail_thread.join(timeout=3)
            tail.stdout.close(); tail.stderr.close()
        receipt = logger.receipt()
    rows = [json.loads(x) for x in logger.paths['jsonl'].read_text().splitlines()]
    beats = [r for r in rows if r['event'] == 'HEARTBEAT']
    gaps = [(dt.datetime.fromisoformat(b['at_utc'].replace('Z', '+00:00'))-
             dt.datetime.fromisoformat(a['at_utc'].replace('Z', '+00:00'))).total_seconds()
            for a, b in zip(beats, beats[1:])]
    stalls = [r for r in rows if r['event'] == 'STALLED_PROGRESS_DIAGNOSTIC']
    out = [r for r in rows if r['event'] == 'PROCESS_OUTPUT']
    text = logger.paths['log'].read_text()
    alive_growth = [x for x in growth if x['child_running']]
    observed_changes = sum(a['log_bytes'] != b['log_bytes'] and a['jsonl_bytes'] != b['jsonl_bytes']
                           for a, b in zip(alive_growth, alive_growth[1:]))
    assert gaps and max(gaps) <= 15., gaps
    assert len([x for x in tail_events if x['child_running']]) >= 2
    assert observed_changes >= (3 if mode == 'stall' else 2), observed_changes
    assert 'UNTERMINATED_STDOUT_VISIBLE' in text and 'STDERR_VISIBLE_DURING_EXECUTION' in text
    assert receipt['health_errors'] == [], receipt
    alive_child_samples = [r for r in beats if any(p['pid'] == child.pid and
                           p['start_ticks'] == identity['start_ticks']
                           for p in r['data']['process_tree']['processes'])]
    assert len(alive_child_samples) >= 2, 'REGISTERED_CHILD_MISSING_FROM_ACTUAL_PROCESS_SAMPLES'
    if mode == 'stall':
        assert code == 0 and stalls
        assert (directory/'fixture_completed.json').is_file()
        assert 'FIXTURE_TRANSFORM_COMPLETED=1' in text
    else:
        assert code != 0
        assert 'DELIBERATE_CHILD_FAILURE_FOR_LOGGING_VERIFICATION' in text
        assert any(r['event'] == 'CHILD_EXITED' and r['data']['status'] == 'FAILED' for r in rows)
    return {'mode': mode, 'status': 'PASS', 'child_returncode': code,
            'heartbeat_interval_seconds': 10., 'heartbeat_samples': len(beats),
            'observed_max_gap_seconds': max(gaps), 'gap_seconds': gaps,
            'tail_F_heartbeats_observed_while_child_alive': len([x for x in tail_events if x['child_running']]),
            'simultaneous_human_and_JSONL_growth_observations': observed_changes,
            'registered_child_observed_in_process_samples': len(alive_child_samples),
            'stall_diagnostic_count': len(stalls), 'fixture_stall_threshold_seconds': 20.,
            'production_default_stall_threshold_seconds': 120.,
            'process_wait_channels': sorted({p.get('wait_channel') for r in beats
                 for p in r['data']['process_tree']['processes'] if p.get('wait_channel')}),
            'captured_streams': sorted({r['data']['stream'] for r in out}),
            'log_pin': pin(logger.paths['log']), 'jsonl_pin': pin(logger.paths['jsonl']),
            'snapshot': snapshot, 'live_receipt': logger.receipt(),
            'actual_NBA_fits': 0, 'actual_AWS_owner_execution': False,
            'synthetic_CPU_probe_performed': False}


def main():
    root = Path(__file__).parent/'live_evidence'/time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())
    started = time.monotonic()
    source_pins = {name: pin(Path(__file__).parent/name) for name in
                   ('sports_edge_live.py', 'live_fixture_worker.py', 'verify_live_execution.py')}
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(run_case, root/mode, mode) for mode in ('stall', 'crash')]
        results = [f.result() for f in futures]
    assert source_pins == {name: pin(Path(__file__).parent/name) for name in source_pins}, 'SOURCE_CHANGED_DURING_LIVE_TEST'
    receipt = {'schema': 'sports-edge-lab.live-log-acceptance.v1', 'status': 'PASS',
               'elapsed_seconds': time.monotonic()-started, 'cases': results,
               'source_pins': source_pins, 'sources_unchanged_through_test': True,
               'evidence_scope': 'REAL_OS_CHILDREN_AND_TAIL_F; FAILURE_INJECTION_ONLY; NOT_OWNER_SCIENTIFIC_UTILIZATION'}
    atomic_json(root/'LIVE_ACCEPTANCE.json', receipt)
    atomic_json(Path(__file__).parent/'LATEST_LIVE_ACCEPTANCE.json', receipt)
    print(json.dumps({'status': receipt['status'], 'elapsed_seconds': receipt['elapsed_seconds'],
                      'receipt': str(root/'LIVE_ACCEPTANCE.json'),
                      'cases': [{k: x[k] for k in ('mode', 'heartbeat_samples', 'observed_max_gap_seconds',
                         'tail_F_heartbeats_observed_while_child_alive', 'stall_diagnostic_count')} for x in results]}, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
