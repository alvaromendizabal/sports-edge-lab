"""Failure-injection worker: no real sports data or scientific fitting."""
from __future__ import annotations
import argparse
import fcntl
import gzip
import hashlib
import json
import os
from pathlib import Path
import sys
import time
from sports_edge_live import atomic_json, process_identity, utc


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=('stall', 'crash'), required=True)
    parser.add_argument('--root', required=True)
    args = parser.parse_args(); root = Path(args.root)
    origin = json.loads(os.environ['SEL_EXECUTION_ORIGIN_JSON'])
    base = {'schema': 'sel.nba.b078.progress.v1',
            'invocation_id': os.environ['SEL_EXECUTION_INVOCATION_ID'],
            'invocation_origin': origin, 'producer_identity': process_identity(os.getpid()),
            'stage': 1, 'total_stages': 2, 'stage_name': 'LIVE_LOG_FAILURE_INJECTION',
            'substage': args.mode, 'status': 'RUNNING_FIXTURE',
            'completed': 0, 'total': 1, 'remaining': 1, 'work_unit': 'fixture_transform',
            'completed_tasks': 0, 'remaining_tasks': 1, 'successes': 0, 'failures': 0,
            'invocation_fit_counts': {'new': 0, 'reused': 0, 'failed': 0},
            'native': {'real_estimator_fit_returns': 0, 'failed_native_calls': 0,
                       'observed_active_native_fit_workers': 0},
            'allocated_cpu_tokens': 1, 'cpu_project_cap': 1,
            'workers': {'active': 1, 'target': 1},
            'model_families': [], 'training_progress': 'NO_SPORTS_FITS_IN_ENGINEERING_FIXTURE',
            'evaluation_results': None, 'champion_changes': [],
            'checkpoint_locations': [str(root/'fixture_completed.json')],
            's3': {'get_calls': 0, 'bytes': 0, 'scope': 'ENGINEERING_FIXTURE_NO_NETWORK'},
            'cache': {'hits': 0, 'misses': 0, 'scope': 'ENGINEERING_FIXTURE_NO_SOURCE_CACHE'},
            'cost': {'status': 'LOCAL_TEST_NO_AWS_OWNER_EXECUTION', 'actual_billed_cost_usd': None}}
    atomic_json(root/'PROGRESS.json', {**base, 'at_utc': utc()})
    print('FIXTURE_CHILD_READY='+str(os.getpid()), flush=True)
    sys.stdout.write('UNTERMINATED_STDOUT_VISIBLE'); sys.stdout.flush()
    sys.stderr.write('STDERR_VISIBLE_DURING_EXECUTION\n'); sys.stderr.flush()
    if args.mode == 'crash':
        time.sleep(27)
        raise RuntimeError('DELIBERATE_CHILD_FAILURE_FOR_LOGGING_VERIFICATION')
    with (root/'held.lock').open('rb') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        body = gzip.compress(b'fixture-work-only\n'*65536, mtime=0)
        (root/'fixture_output.gz').write_bytes(body)
        atomic_json(root/'fixture_completed.json', {'bytes': len(body),
                    'sha256': hashlib.sha256(body).hexdigest(), 'actual_sports_fits': 0})
    atomic_json(root/'PROGRESS.json', {**base, 'at_utc': utc(), 'completed': 1,
        'completed_tasks': 1, 'successes': 1, 'remaining_tasks': 0, 'remaining': 0,
        'status': 'FIXTURE_COMPLETED', 'substage': 'checkpoint_saved'})
    print('\nFIXTURE_TRANSFORM_COMPLETED=1', flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
