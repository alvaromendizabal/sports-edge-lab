"""Shared, append-only Sports Edge Lab execution observation.

Stdlib-only until an explicitly installed S3 sink is used. The logger observes
real processes; it neither launches research nor fabricates scientific counts.
Start it in the outer owner launcher, before physical source bootstrap. Child
work and network checkpoints never run on the heartbeat thread.
"""
from __future__ import annotations

import base64
import codecs
import copy
import datetime as dt
import fcntl
import gzip
import hashlib
import json
import math
import os
from pathlib import Path
import queue
import re
import selectors
import shutil
import stat
import sys
import tempfile
import threading
import time
import traceback
import uuid

# Keep the bootstrap logger self-contained: the owner bridge loads this
# manifest-pinned stdlib module before project siblings may be imported.
_SUCCESS_COUNTERS = frozenset((
    's3_gets_completed', 's3_bytes', 'local_cache_hits', 'local_reused_bytes',
    'files_hashed', 'bytes_hashed', 'verified_unchanged_files_reused',
    'verified_unchanged_bytes_reused', 'objects_verified', 'bytes_verified',
    'objects_read', 'bytes_read',
))
_STATE_COUNTERS = (
    'completed', 'remaining', 'total', 'completed_tasks', 'remaining_tasks',
    'successes', 'failures',
)


def _number(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    try:
        return value if math.isfinite(value) and value >= 0 else None
    except (OverflowError, TypeError, ValueError):
        return None


def _mapping(value):
    return value if isinstance(value, dict) else {}


def successful_work_counters(measurements):
    """Read bounded known scalar scopes without scanning detailed evidence.

    Scopes are retained separately: the same read may appear in both an S3
    source and its cache receipt, so these counters are deliberately not added.
    Attempts, retries, failures, CPU time, transfer duration, freshness and
    clock changes are not successful-work counters.
    """
    result = {}

    def accept(prefix, value):
        value = _mapping(value)
        for key in sorted(_SUCCESS_COUNTERS):
            number = _number(value.get(key))
            if number is not None:
                result[prefix + '.' + key] = number

    s3 = _mapping(measurements.get('s3'))
    accept('s3', s3)
    sources = _mapping(s3.get('instrumented_sources'))
    for name in sorted(sources)[:32]:
        accept('s3.instrumented_sources.' + str(name), sources[name])
    cache = _mapping(measurements.get('cache'))
    accept('cache', cache)
    verified = _mapping(cache.get('verified_file_cache'))
    accept('cache.verified_file_cache', _mapping(verified.get('counters')) or verified)
    sources = _mapping(cache.get('live_instrumented_cache_sources'))
    for name in sorted(sources)[:32]:
        source = _mapping(sources[name])
        accept('cache.live_instrumented_cache_sources.' + str(name), source.get('counters'))
    accept('local_io', measurements.get('local_io'))
    return result


class ProgressObservation:
    """Track task state, completed operational work and native returns apart."""

    def __init__(self, started):
        self.started = float(started)
        self.last_execution_progress = self.started
        self.last_native_completion = self.started
        self.signature = None
        self.counters = {}
        self.native_returns = None
        self.observations = 0
        self.last_observation = self.started

    def observe(self, measurements, now):
        now = float(now)
        if not math.isfinite(now) or now < self.last_observation:
            raise ValueError('B082_PROGRESS_CLOCK_MUST_BE_FINITE_AND_MONOTONIC')
        self.last_observation = now
        progress = _mapping(measurements.get('progress'))
        fits = _mapping(measurements.get('fits'))
        state = {
            'stage': measurements.get('stage'),
            'counts': {key: progress.get(key) for key in _STATE_COUNTERS},
            'fits': fits,
        }
        signature = json.dumps(state, sort_keys=True, separators=(',', ':'), allow_nan=False)
        state_changed = signature != self.signature
        self.signature = signature
        counters = successful_work_counters(measurements)
        advances = []
        resets = []
        for key, value in counters.items():
            previous = self.counters.get(key)
            # A first observation establishes a baseline. An old completed
            # receipt newly appearing in telemetry is not new work.
            if previous is not None and value > previous:
                advances.append({'scope': key, 'previous': previous,
                                 'current': value, 'delta': value - previous})
            elif previous is not None and value < previous:
                resets.append(key)
        self.counters = counters
        if state_changed or advances:
            self.last_execution_progress = now
        native = _number(fits.get('completed_native_fit_returns'))
        native_delta = None
        if native is not None and self.native_returns is not None:
            native_delta = native - self.native_returns
            if native_delta > 0:
                self.last_native_completion = now
            elif native_delta < 0:
                # A reset is explicitly visible; it cannot earn a completion.
                native_delta = None
        self.native_returns = native
        self.observations += 1
        return {
            'schema': 'sel.execution.progress_observation.b082.v1',
            'observations': self.observations,
            'execution_idle_seconds': max(0., now - self.last_execution_progress),
            'task_or_stage_state_changed': state_changed,
            'successful_work_counter_advance_observed': bool(advances),
            'successful_work_counter_advances': advances[:16],
            'successful_work_counter_advance_count': len(advances),
            'successful_work_counter_resets': resets[:16],
            'independent_counter_scopes_are_not_summed': True,
            'first_observation_is_baseline_only': True,
            'attempts_failures_clocks_and_cpu_are_not_successful_work': True,
            'native_fit_completion_idle_seconds': max(0., now - self.last_native_completion),
            'completed_native_fit_returns': native,
            'new_native_returns_observed_between_samples': native_delta,
            'operational_work_is_not_scientific_fit_progress': True,
        }


SCHEMA = 'sports-edge-lab.live-execution.v1'
IDENTITY_ENV = 'SEL_EXECUTION_INVOCATION_ID'
ORIGIN_ENV = 'SEL_EXECUTION_ORIGIN_JSON'
PROJECT_ENV = 'SEL_EXECUTION_PROJECT'
RELEASE_ENV = 'SEL_EXECUTION_RELEASE'
LOG_PREFIX_ENV = 'SEL_EXECUTION_LOG_PREFIX'
_SECRET = re.compile(r'(?i)(api[_-]?key|access[_-]?token|authorization|password|secret(?:_access_key)?|x-amz-security-token)')
_SECRET_TEXT = re.compile(r'(?i)((?:api[_-]?key|(?:access[_-]?)?token|authorization|password|aws_secret_access_key|x-amz-(?:security-token|signature|credential))\s*[=:]\s*)(?:Bearer\s+)?([^\s&;,]+)')


def utc():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec='microseconds').replace('+00:00', 'Z')


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')


def _clean(value, depth=0):
    if depth > 16:
        return {'telemetry_omitted_reason': 'MAXIMUM_NESTING_DEPTH'}
    if isinstance(value, dict):
        return {str(k): '[REDACTED]' if _SECRET.search(str(k)) else _clean(v, depth+1)
                for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_clean(x, depth+1) for x in value]
    if isinstance(value, str):
        return _SECRET_TEXT.sub(r'\1[REDACTED]', value).replace('\x00', '[NUL]')
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if value is None or isinstance(value, (int, float, bool)):
        return value
    return _clean(str(value), depth+1)


def boot_id():
    try:
        return Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    except OSError:
        return None


def process_identity(pid):
    try:
        body = (Path('/proc')/str(int(pid))/'stat').read_text()
        fields = body[body.rfind(')')+2:].split()
        return {'pid': int(pid), 'start_ticks': int(fields[19]), 'boot_id': boot_id()}
    except (OSError, ValueError, IndexError):
        return None


def _regular(path):
    path = Path(path)
    if path.is_symlink() or any(p.is_symlink() for p in path.parents):
        raise ValueError('LIVE_LOG_SYMLINK_PATH_REJECTED')
    if path.exists() and not stat.S_ISREG(path.stat().st_mode):
        raise ValueError('LIVE_LOG_REGULAR_FILE_REQUIRED')
    return path


def atomic_json(path, value):
    path = _regular(path); path.parent.mkdir(parents=True, exist_ok=True)
    body = canonical(_clean(value))+b'\n'
    fd, name = tempfile.mkstemp(prefix='.live-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(body); stream.flush(); os.fsync(stream.fileno())
        os.replace(name, path)
        fd = os.open(path.parent, os.O_RDONLY | getattr(os, 'O_DIRECTORY', 0))
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
    finally:
        if os.path.exists(name):
            os.unlink(name)
    return {'path': str(path), 'bytes': len(body), 'sha256': hashlib.sha256(body).hexdigest()}


def _file_pin(path):
    digest = hashlib.sha256(); size = 0
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1 << 20), b''):
            digest.update(block); size += len(block)
    return {'bytes': size, 'sha256': digest.hexdigest()}


def snapshot_log_prefix(prefix, destination, *, expected_invocation_id, expected_project):
    """Finalizer-safe immutable prefixes; never open or rotate a live writer.

    A JSONL record being appended at the cut is excluded until complete. Every
    copied record is validated; previous append sessions are preserved only
    before the current session and remain explicitly identified as history.
    Human/JSONL limits are independent observed byte offsets, not a claim that
    an active logger has closed. Physically reread copies before returning.
    """
    prefix = Path(prefix).absolute(); destdir = Path(destination).absolute()
    destdir.mkdir(parents=True, exist_ok=True)
    sources = {kind: _regular(str(prefix)+'.'+kind) for kind in ('log', 'jsonl')}
    limits = {}; identities = {}; started = utc(); files = {}
    for kind, source in sources.items():
        st = source.stat(); limits[kind] = st.st_size
        identities[kind] = (st.st_dev, st.st_ino)
    for kind, source in sources.items():
        dest = _regular(destdir/source.name)
        if dest.exists():
            raise FileExistsError('LIVE_LOG_SNAPSHOT_MUST_BE_NEW')
        copied = 0; last_newline = 0
        with source.open('rb') as inp, dest.open('xb+') as out:
            if (os.fstat(inp.fileno()).st_dev, os.fstat(inp.fileno()).st_ino) != identities[kind]:
                raise ValueError('LIVE_LOG_SOURCE_REPLACED_DURING_SNAPSHOT')
            while copied < limits[kind]:
                body = inp.read(min(1 << 20, limits[kind]-copied))
                if not body: raise IOError('LIVE_LOG_SOURCE_SHRANK_DURING_SNAPSHOT')
                where = body.rfind(b'\n')
                if where >= 0: last_newline = copied+where+1
                out.write(body); copied += len(body)
            clipped = 0
            if kind == 'jsonl' and last_newline < copied:
                clipped = copied-last_newline; out.truncate(last_newline); copied = last_newline
            out.flush(); os.fsync(out.fileno())
        st = source.stat()
        if (st.st_dev, st.st_ino) != identities[kind] or st.st_size < limits[kind]:
            raise ValueError('LIVE_LOG_SOURCE_REPLACED_OR_SHRANK_DURING_SNAPSHOT')
        files[kind] = {'path': str(dest), **_file_pin(dest),
                       'captured_source_limit_bytes': limits[kind],
                       'excluded_incomplete_tail_bytes': clipped, 'physical_readback_verified': True}
    sequences = {}; producers = {}; history = []; saw_current = False; rows = 0
    with Path(files['jsonl']['path']).open('rb') as stream:
        for line in stream:
            row = json.loads(line); rows += 1
            inv = row.get('invocation_id')
            if row.get('schema') != SCHEMA or row.get('project') != expected_project or not isinstance(inv, str):
                raise ValueError('LIVE_LOG_SNAPSHOT_ENVELOPE_MISMATCH')
            if inv != expected_invocation_id:
                if saw_current: raise ValueError('LIVE_LOG_FOREIGN_INVOCATION_AFTER_CURRENT_SESSION')
                if inv not in history: history.append(inv)
            else:
                saw_current = True
            expected_seq = sequences.get(inv, 0)+1
            if row.get('sequence') != expected_seq:
                raise ValueError('LIVE_LOG_SNAPSHOT_SEQUENCE_GAP_OR_RESTARTED_ID')
            identity = row.get('producer_identity')
            if not isinstance(identity, dict) or not all(k in identity for k in ('pid', 'start_ticks', 'boot_id')):
                raise ValueError('LIVE_LOG_SNAPSHOT_PRODUCER_IDENTITY_MISSING')
            if inv in producers and producers[inv] != identity:
                raise ValueError('LIVE_LOG_SNAPSHOT_PRODUCER_IDENTITY_CHANGED')
            if expected_seq == 1 and row.get('event') != 'EXECUTION_LOG_OPENED':
                raise ValueError('LIVE_LOG_SNAPSHOT_SESSION_HEADER_MISSING')
            producers[inv] = identity; sequences[inv] = expected_seq
    if not saw_current: raise ValueError('LIVE_LOG_SNAPSHOT_CURRENT_INVOCATION_ABSENT')
    receipt = {'schema': 'sports-edge-lab.log-snapshot.v1', 'at_utc': started,
               'completed_at_utc': utc(), 'invocation_id': expected_invocation_id,
               'project': expected_project, 'files': files, 'validated_jsonl_records': rows,
               'historical_append_session_ids': history,
               'snapshot_is_prefix_of_live_execution': True,
               'streams_captured_at_independent_file_offsets': True,
               'post_finalization_external_events_are_separate': True,
               'active_source_modified': False, 'physical_readback_verified': True}
    atomic_json(destdir/'LOG_SNAPSHOT.json', receipt)
    return receipt


def process_tree(root_pid, expected_identity=None, *, limit=512, registered_children=()):
    """Sample only the registered owner's descendants, with PID-reuse guards."""
    root = process_identity(root_pid)
    if root is None or (expected_identity and root != expected_identity):
        return {'status': 'ROOT_IDENTITY_GONE_OR_CHANGED', 'root_identity': root,
                'processes': [], 'partial': True, 'monotonic_seconds': time.monotonic()}
    pending = [int(root_pid)]; seen = set(); rows = []; errors = []
    hz = os.sysconf('SC_CLK_TCK'); page = os.sysconf('SC_PAGE_SIZE')
    while pending and len(seen) < limit:
        pid = pending.pop()
        if pid in seen:
            continue
        seen.add(pid); base = Path('/proc')/str(pid)
        try:
            content = (base/'stat').read_text(); fields = content[content.rfind(')')+2:].split()
            row = {'pid': pid, 'start_ticks': int(fields[19]), 'state': fields[0],
                   'parent_pid': int(fields[1]), 'user_seconds': int(fields[11])/hz,
                   'system_seconds': int(fields[12])/hz, 'threads': int(fields[17]),
                   'rss_bytes': max(0, int(fields[21]))*page,
                   'affinity_count': len(os.sched_getaffinity(pid))}
            try:
                row['wait_channel'] = (base/'wchan').read_text().strip()
            except OSError:
                row['wait_channel'] = None
            # A process can spawn from a non-main thread. Thread CPU is already
            # included in process stat, so do not add it a second time.
            task_dirs = list((base/'task').iterdir())
            if len(task_dirs) > 2048:
                errors.append({'pid': pid, 'reason': 'THREAD_CHILD_ENUMERATION_BOUNDED'})
            for task in task_dirs[:2048]:
                try:
                    pending.extend(int(x) for x in (task/'children').read_text().split())
                except (OSError, ValueError):
                    pass
            rows.append(row)
        except (OSError, ValueError, IndexError) as exc:
            errors.append({'pid': pid, 'reason': type(exc).__name__})
    fallback = False; inspected = 0
    missing_registered = [identity for identity in registered_children if identity and
                          identity.get('pid') not in seen and
                          process_identity(identity.get('pid', -1)) == identity]
    if missing_registered:
        # Some constrained /proc mounts expose an empty task/children file
        # while PID/stat remains usable. A known live child proves that the
        # link traversal is incomplete. Inspect bounded PPID metadata once,
        # retain only the authenticated root's descendants, and report scope.
        fallback = True; parents = {}
        entries = [x for x in Path('/proc').iterdir() if x.name.isdecimal()]
        if len(entries) > 8192:
            errors.append({'reason': 'PPID_FALLBACK_PROCESS_LIMIT_REACHED'})
        for entry in entries[:8192]:
            inspected += 1
            try:
                body = (entry/'stat').read_text(); fields = body[body.rfind(')')+2:].split()
                parents[int(entry.name)] = int(fields[1])
            except (OSError, ValueError, IndexError):
                continue
        allowed = {int(root_pid)}
        for _ in range(128):
            children = {pid for pid, parent in parents.items() if parent in allowed}
            newer = children-allowed
            if not newer: break
            allowed.update(newer)
        for pid in sorted(allowed-seen)[:max(0, limit-len(seen))]:
            identity = process_identity(pid)
            if identity is None: continue
            descendant = process_tree(pid, identity, limit=max(1, limit-len(seen)))
            for row in descendant['processes']:
                if row['pid'] not in seen and row['pid'] in allowed:
                    seen.add(row['pid']); rows.append(row)
        if allowed-seen:
            errors.append({'reason': 'OWNER_PROCESS_DISCOVERY_PARTIAL', 'missing_count': len(allowed-seen)})
        observed = {row['pid'] for row in rows}
        for identity in missing_registered:
            if identity['pid'] not in observed and process_identity(identity['pid']) == identity:
                errors.append({'pid': identity['pid'], 'reason': 'REGISTERED_CHILD_NOT_IN_BOUND_OWNER_TREE'})
    return {'status': 'OBSERVED', 'root_identity': root, 'processes': rows,
            'partial': bool(pending or errors), 'errors': errors,
            'bounded_ppid_discovery_fallback_used': fallback,
            'ppid_metadata_records_inspected': inspected,
            'retained_process_scope': 'EXACT_ROOT_AND_ITS_DESCENDANTS_ONLY',
            'monotonic_seconds': time.monotonic(), 'process_count': len(rows),
            'thread_count': sum(x['threads'] for x in rows),
            'rss_bytes': sum(x['rss_bytes'] for x in rows),
            'rss_basis': 'SUM_OF_LIVE_RSS_SHARED_PAGES_CAN_REPEAT',
            'short_lived_unobserved_children_excluded': True}


def _cpu_delta(before, current):
    if not before:
        return None
    elapsed = current['monotonic_seconds']-before['monotonic_seconds']
    if elapsed <= 0:
        return None
    old = {(r['pid'], r['start_ticks']): r for r in before['processes']}
    total = 0.; matched = 0
    for row in current['processes']:
        prior = old.get((row['pid'], row['start_ticks']))
        if prior:
            total += max(0., row['user_seconds']+row['system_seconds']-
                         prior['user_seconds']-prior['system_seconds'])
            matched += 1
    return {'used_core_equivalents': total/elapsed, 'cpu_seconds': total,
            'interval_seconds': elapsed, 'matched_process_identities': matched,
            'basis': 'MATCHED_PID_START_TICKS_USER_PLUS_SYSTEM_CPU_DELTA',
            'short_lived_unobserved_children_excluded': True}


def _host_resources(path):
    out = {}
    try:
        mem = {}
        for line in Path('/proc/meminfo').read_text().splitlines():
            key, value = line.split(':', 1)
            if key in ('MemTotal', 'MemAvailable', 'SwapFree', 'SwapTotal'):
                mem[key] = int(value.split()[0])*1024
        out['memory'] = mem
    except (OSError, ValueError):
        out['memory'] = {'status': 'PROC_MEMORY_NOT_AVAILABLE'}
    try:
        usage = shutil.disk_usage(path); fs = os.statvfs(path)
        out['disk'] = {'total_bytes': usage.total, 'used_bytes': usage.used,
                       'free_bytes': usage.free, 'free_inodes': fs.f_favail}
    except OSError:
        out['disk'] = {'status': 'DISK_OBSERVATION_FAILED'}
    return out


def _first(state, *keys):
    for key in keys:
        if key in state and state[key] is not None:
            return state[key]
    return None


def project_measurements(state):
    """Preserve measured values and explicit missingness; never infer fits."""
    workers = state.get('workers') or {}; lease = state.get('lease') or state.get('V7_resource_lease') or {}
    native = state.get('native') or {}; fits = state.get('invocation_fit_counts') or {}
    return {
        'stage': {k: state.get(k) for k in ('stage', 'total_stages', 'stage_name', 'substage', 'status')},
        'progress': {k: state.get(k) for k in ('completed', 'remaining', 'total', 'work_unit',
                     'completed_tasks', 'remaining_tasks', 'successes', 'failures',
                     'throughput_per_second', 'eta_seconds', 'eta_observed_rate_range_seconds',
                     'eta_uncertainty', 'checkpoint_locations')},
        'cpu': {'reserved_cores': _first(state, 'allocated_cpu_tokens', 'granted_cpus')
                    if _first(state, 'allocated_cpu_tokens', 'granted_cpus') is not None else lease.get('reserved_tokens'),
                'project_cap': state.get('cpu_project_cap'),
                'active_workers': workers.get('active', state.get('active_tasks')),
                'requested_workers': workers.get('target', lease.get('desired_workers'))},
        'fits': {'new': fits.get('new'), 'reused': fits.get('reused'), 'failed': fits.get('failed'),
                 'scope': fits.get('scope', 'CURRENT_BOUND_INVOCATION'),
                 'source_phase': fits.get('source_phase'),
                 'reported_counts': fits.get('reported_counts'),
                 'completed_native_fit_returns': native.get('real_estimator_fit_returns'),
                 'failed_native_calls': native.get('failed_native_calls'),
                 'concurrent_native_fits': native.get('observed_active_native_fit_workers'),
                 'counts_are_not_inferred_from_cpu_or_wrapper_tasks': True},
        'experiments': {'task_event': state.get('task_event'),
                        'active_task_details': state.get('active_task_details'),
                        'families': state.get('model_families'),
                        'training_progress': state.get('training_progress'),
                        'evaluation_results': state.get('evaluation_results'),
                        'champion_changes': state.get('champion_changes')},
        's3': state.get('s3'),
        'local_io': state.get('io_counters'),
        'cache': _first(state, 'cache', 'source_counters'),
        'cost': state.get('cost') or {
            'estimated_whole_instance_invocation_usd': state.get('invocation_whole_host_estimate_usd'),
            'status': state.get('cost_status', 'RATE_OR_COST_NOT_REPORTED'),
            'actual_billed_cost_usd': None},
        'null_reason': 'NOT_REPORTED_BY_CURRENT_BOUND_WORKLOAD; NOT_ZERO_OR_INFERRED',
    }


class LiveExecutionLog:
    def __init__(self, prefix, *, project, release, invocation_id=None,
                 invocation_origin=None, interval=10., root_pid=None,
                 progress_path=None, checkpoint_sink=None, checkpoint_interval=300.,
                 stall_seconds=120., console=None):
        if not 0 < float(interval) <= 15:
            raise ValueError('LIVE_LOG_HEARTBEAT_MUST_BE_AT_MOST_15_SECONDS')
        if float(checkpoint_interval) < 30:
            raise ValueError('LIVE_LOG_REMOTE_CHECKPOINT_MINIMUM_30_SECONDS')
        self.prefix = Path(prefix).absolute(); self.prefix.parent.mkdir(parents=True, exist_ok=True)
        self.project = str(project); self.release = str(release)
        if not re.fullmatch(r'[a-z][a-z0-9_]{0,63}', self.project):
            raise ValueError('LIVE_LOG_INVALID_PROJECT_SELECTOR')
        self.invocation_id = str(invocation_id or uuid.uuid4().hex)
        if not re.fullmatch(r'[A-Za-z0-9_.-]{1,128}', self.invocation_id):
            raise ValueError('LIVE_LOG_INVALID_INVOCATION_ID')
        self.origin = copy.deepcopy(invocation_origin)
        self.identity = process_identity(os.getpid())
        if self.identity is None:
            raise RuntimeError('LIVE_LOG_OWNER_IDENTITY_UNAVAILABLE')
        self.root_pid = int(root_pid or os.getpid()); self.root_identity = process_identity(self.root_pid)
        self.paths = {'log': _regular(str(self.prefix)+'.log'),
                      'jsonl': _regular(str(self.prefix)+'.jsonl')}
        self.state_path = _regular(str(self.prefix)+'.live.json')
        self.lock_path = _regular(str(self.prefix)+'.writer.lock')
        self.lock_fd = os.open(self.lock_path, os.O_RDWR | os.O_CREAT | getattr(os, 'O_NOFOLLOW', 0), 0o600)
        try:
            fcntl.flock(self.lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BaseException:
            os.close(self.lock_fd); raise RuntimeError('LIVE_LOG_PREFIX_ALREADY_HAS_ACTIVE_WRITER')
        self.streams = {}
        try:
            for kind, path in self.paths.items():
                fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND | getattr(os, 'O_NOFOLLOW', 0), 0o600)
                self.streams[kind] = os.fdopen(fd, 'ab', buffering=0)
        except BaseException:
            for stream in self.streams.values(): stream.close()
            os.close(self.lock_fd); raise
        self.previous_sizes = {k: p.stat().st_size for k, p in self.paths.items()}
        self.interval = float(interval); self.stall_seconds = float(stall_seconds)
        self.console = console; self.lock = threading.RLock(); self.stop = threading.Event()
        self.thread = None; self.closed = False; self.started = time.monotonic()
        self.seq = 0; self.samples = 0; self.last_beat = None; self.max_gap = 0.
        self.previous_process = None; self.state = {}; self.child = None
        self.child_exit_observed_at_utc = None
        self.progress_path = Path(progress_path) if progress_path else None
        self.expected_producer = None; self.last_progress_error = None
        self.progress_signature = None; self.last_progress = self.started; self.last_stall = None
        self.execution_progress = ProgressObservation(self.started)
        self.health_errors = []; self.checkpoint_sink = checkpoint_sink
        self.checkpoint_interval = float(checkpoint_interval)
        self.checkpoint_stop = threading.Event(); self.checkpoint_thread = None
        self.checkpoint_requests = queue.Queue(maxsize=1); self.checkpoint_results = queue.Queue()
        self.checkpoint_last = self.started; self.checkpoint_receipts = []
        self.event('EXECUTION_LOG_OPENED', previous_bytes=self.previous_sizes,
                   append_only=True, heartbeat_target_seconds=self.interval,
                   measurement_scope='OBSERVATION_ONLY; NOT_SCIENTIFIC_PROGRESS')

    def environment(self, base=None):
        env = dict(os.environ if base is None else base)
        env.update({IDENTITY_ENV: self.invocation_id, PROJECT_ENV: self.project,
                    RELEASE_ENV: self.release, LOG_PREFIX_ENV: str(self.prefix)})
        if self.origin is not None:
            env[ORIGIN_ENV] = canonical(self.origin).decode()
        env['PYTHONUNBUFFERED'] = '1'
        return env

    def __enter__(self):
        if self.thread is not None:
            raise RuntimeError('LIVE_LOG_ALREADY_STARTED')
        self.heartbeat(force=True)
        self.thread = threading.Thread(target=self._loop, name='sel-live-heartbeat', daemon=True)
        self.thread.start()
        if self.checkpoint_sink:
            self._start_checkpoint_worker()
        return self

    def __exit__(self, exc_type, exc, tb):
        if exc is not None:
            self._safe_event('EXECUTION_EXCEPTION', exception_type=type(exc).__name__,
                             message=str(exc), stack=[{'file': x.filename, 'line': x.lineno, 'function': x.name}
                                                     for x in traceback.extract_tb(tb)])
        self.close()

    def event(self, kind, **fields):
        with self.lock:
            if self.closed:
                raise RuntimeError('LIVE_LOG_ALREADY_CLOSED')
            self.seq += 1
            row = {'schema': SCHEMA, 'at_utc': utc(), 'event': str(kind),
                   'sequence': self.seq, 'invocation_id': self.invocation_id,
                   'invocation_origin': self.origin, 'project': self.project,
                   'release': self.release, 'producer_identity': self.identity,
                   'elapsed_seconds': time.monotonic()-self.started, 'data': _clean(fields)}
            body = canonical(row)+b'\n'; self.streams['jsonl'].write(body)
            text = self._human(row).encode('utf-8', 'replace')+b'\n'
            self.streams['log'].write(text)
            if self.console is not None:
                try:
                    self.console.write(text.decode()); self.console.flush()
                except (BrokenPipeError, OSError):
                    self.console = None
            return row

    @staticmethod
    def _human(row):
        head = f"[{row['at_utc']}] {row['release']} {row['project']} {row['event']} run={row['invocation_id']} elapsed={row['elapsed_seconds']:.3f}s"
        data = row['data']
        if row['event'] == 'PROCESS_OUTPUT':
            return head+f" stream={data['stream']} | "+data['text'].rstrip('\n')
        if row['event'] == 'HEARTBEAT':
            m = data['measurements']; stage = m['stage']; p = m['progress']; fits = m['fits']
            cpu = data.get('cpu_delta') or {}; c = m['cpu']; resource = data['resources']
            return (head+f" stage={stage.get('stage')}/{stage.get('total_stages')} {stage.get('stage_name')} substage={stage.get('substage')}"
                +f"\n  progress={p.get('completed')}/{p.get('total')} remaining={p.get('remaining')} rate={p.get('throughput_per_second')}/s ETA={p.get('eta_seconds')}s"
                +f" | CPU_used={cpu.get('used_core_equivalents')}c reserved={c.get('reserved_cores')} active_workers={c.get('active_workers')} concurrent_native_fits={fits.get('concurrent_native_fits')}"
                +f"\n  fits_new/reused/failed={fits.get('new')}/{fits.get('reused')}/{fits.get('failed')} scope={fits.get('scope')} native_returns={fits.get('completed_native_fit_returns')} reported_counts="+json.dumps(fits.get('reported_counts'), sort_keys=True)
                +f" | RSS={data['process_tree'].get('rss_bytes')} RAM_free={resource['memory'].get('MemAvailable')} disk_free={resource['disk'].get('free_bytes')}"
                +" PIDs="+json.dumps([p.get('pid') for p in data['process_tree'].get('processes', [])])
                +f" | source_age={data['progress_observation'].get('age_seconds')}s progress_idle={data['progress_idle_seconds']:.3f}s child={data.get('child_identity')}"
                +f" native_fit_completion_idle={data.get('native_fit_completion_idle_seconds')}s"
                +"\n  S3="+json.dumps(m['s3'], sort_keys=True)+" cache="+json.dumps(m['cache'], sort_keys=True)
                +" local_IO="+json.dumps(m['local_io'], sort_keys=True)
                +" cost="+json.dumps(m['cost'], sort_keys=True)
                +f"\n  tasks_completed/remaining={p.get('completed_tasks')}/{p.get('remaining_tasks')} successes/failures={p.get('successes')}/{p.get('failures')} checkpoints="
                +json.dumps(p.get('checkpoint_locations'), sort_keys=True)
                +" experiments="+json.dumps(m['experiments'], sort_keys=True)
                +" | missing measurements remain null (not zero)")
        return head+' | '+json.dumps(data, sort_keys=True, ensure_ascii=False)

    def capture_output(self, stream_name, text):
        return self.event('PROCESS_OUTPUT', stream=str(stream_name), text=str(text))

    def set_child(self, pid, identity=None):
        actual = process_identity(pid)
        if actual is None or (identity is not None and actual != identity):
            raise ValueError('LIVE_LOG_CHILD_IDENTITY_NOT_CURRENT')
        with self.lock:
            self.child = actual
        # Registration is also used immediately after Popen, before the caller
        # enters supervise. A failed diagnostic write must retain the exact
        # child identity and let supervision drain pipes/request safe recovery.
        self._safe_event('CHILD_REGISTERED', child_identity=actual)
        return actual

    def bind_progress(self, path, producer_identity=None):
        with self.lock:
            self.progress_path = Path(path)
            self.expected_producer = copy.deepcopy(producer_identity)

    def update_state(self, mapping):
        with self.lock:
            self.state.update(copy.deepcopy(mapping))

    def _read_progress(self):
        if self.progress_path is None:
            return {'status': 'NO_BOUND_PROGRESS_PATH', 'age_seconds': None}
        try:
            path = _regular(self.progress_path)
            if path.stat().st_size > 2 << 20:
                raise ValueError('PROGRESS_RECORD_OVER_2_MIB')
            row = json.loads(path.read_bytes())
            if row.get('invocation_id') != self.invocation_id:
                raise ValueError('PROGRESS_INVOCATION_ID_MISMATCH')
            if self.origin is not None and row.get('invocation_origin') != self.origin:
                raise ValueError('PROGRESS_ORIGIN_MISMATCH')
            producer = row.get('producer_identity')
            expected = self.expected_producer or self.child
            if not isinstance(producer, dict) or (expected is not None and producer != expected):
                raise ValueError('PROGRESS_PRODUCER_NOT_REGISTERED_CHILD')
            stamp = dt.datetime.fromisoformat(row['at_utc'].replace('Z', '+00:00'))
            age = (dt.datetime.now(dt.timezone.utc)-stamp).total_seconds()
            if age < -1:
                raise ValueError('PROGRESS_TIMESTAMP_IN_FUTURE')
            live_identity = process_identity(producer.get('pid', -1))
            after_exit = False
            if live_identity != producer:
                if expected is None or not self.child_exit_observed_at_utc:
                    raise ValueError('PROGRESS_PRODUCER_NOT_LIVE_EXACT_IDENTITY')
                ended = dt.datetime.fromisoformat(self.child_exit_observed_at_utc.replace('Z', '+00:00'))
                if stamp > ended:
                    raise ValueError('PROGRESS_TIMESTAMP_AFTER_OBSERVED_CHILD_EXIT')
                after_exit = True
            self.state.update(row)
            return {'status': 'CURRENT_INVOCATION_BOUND', 'age_seconds': max(0., age),
                    'stale': age > 3*self.interval, 'source_at_utc': row['at_utc'],
                    'preserved_exact_child_receipt_after_observed_exit': after_exit}
        except (OSError, ValueError, TypeError, KeyError) as exc:
            reason = type(exc).__name__+':'+str(exc)
            if reason != self.last_progress_error:
                self.event('PROGRESS_SOURCE_UNAVAILABLE', reason=reason,
                           prior_invocation_counts_adopted=False)
                self.last_progress_error = reason
            return {'status': 'BOUND_PROGRESS_NOT_AVAILABLE', 'reason': reason, 'age_seconds': None}

    def _loop(self):
        while not self.stop.wait(self.interval):
            try:
                self.heartbeat()
            except BaseException as exc:
                # Preserve an actionable logger error for supervisor health gates.
                self.health_errors.append({'at_utc': utc(), 'error_type': type(exc).__name__, 'error': str(exc)})
                try:
                    sys.__stderr__.write('LIVE_LOG_HEARTBEAT_FAILED='+type(exc).__name__+'\n'); sys.__stderr__.flush()
                except (OSError, AttributeError):
                    pass

    def heartbeat(self, *, force=False):
        del force
        with self.lock:
            observation = self._read_progress()
            current = process_tree(self.root_pid, self.root_identity,
                                   registered_children=(self.child, self.expected_producer))
            delta = _cpu_delta(self.previous_process, current); self.previous_process = current
            now = time.monotonic(); self.samples += 1
            if self.last_beat is not None:
                self.max_gap = max(self.max_gap, now-self.last_beat)
            self.last_beat = now
            measures = project_measurements(self.state)
            # B082 also observes successful transfer/cache/I/O counters. B081
            # reported a transfer stalled despite thousands of completed GETs.
            # Keep native-return inactivity distinct: these operational counters
            # never earn a scientific fit. Clocks, CPU, attempts and failure
            # retries alone still cannot suppress a stalled-work diagnostic.
            progress = self.execution_progress.observe(measures, now)
            self.progress_signature = self.execution_progress.signature.encode('utf-8')
            self.last_progress = self.execution_progress.last_execution_progress
            data = {'measurements': measures, 'resources': _host_resources(self.prefix.parent),
                    'process_tree': current, 'cpu_delta': delta, 'child_identity': self.child,
                    'progress_observation': observation, 'progress_idle_seconds': progress['execution_idle_seconds'],
                    'execution_progress_observation': progress,
                    'native_fit_completion_idle_seconds': progress['native_fit_completion_idle_seconds'],
                    'heartbeat_target_seconds': self.interval, 'heartbeat_observed_max_gap_seconds': self.max_gap,
                    'training_timeout_applied': False, 'logger_errors': copy.deepcopy(self.health_errors)}
            self.event('HEARTBEAT', **data)
            atomic_json(self.state_path, {'schema': SCHEMA, 'at_utc': utc(),
                        'invocation_id': self.invocation_id, 'owner_identity': self.identity,
                        'heartbeat_sequence': self.samples, 'heartbeat': data,
                        'log_paths': {k: str(p) for k, p in self.paths.items()}})
            idle = now-self.last_progress
            if idle >= self.stall_seconds and (self.last_stall is None or now-self.last_stall >= max(30., self.stall_seconds)):
                self.last_stall = now
                workload_identity = self.expected_producer or self.child
                stacks = self._thread_stacks()
                self.event('STALLED_PROGRESS_DIAGNOSTIC', idle_seconds=idle,
                    process_states=current, cpu_delta=delta, stage=measures['stage'],
                    active_tasks=measures['experiments']['active_task_details'],
                    # Retain the old field for readers, with an explicit scope.
                    # Python frames here are the logger's own frames, not those
                    # of its separately executing scientific workload child.
                    owner_thread_stacks=stacks, observer_thread_stacks=stacks,
                    thread_stack_scope='LOGGER_PROCESS_ONLY',
                    thread_stack_process_identity=self.identity,
                    workload_process_identity=workload_identity,
                    workload_python_stacks_observed=(workload_identity == self.identity),
                    workload_stack_unavailability_reason=(None if workload_identity == self.identity else
                        'SEPARATE_WORKLOAD_PROCESS; PYTHON_FRAMES_NOT_OBSERVED_BY_EXTERNAL_LOGGER'),
                    execution_progress_observation=progress,
                    recovery_actions=['PRESERVE_ATOMIC_CHECKPOINTS', 'INSPECT_WAIT_CHANNEL_AND_DEPENDENCY',
                                      'SUPERVISOR_REQUESTS_SAFE_BOUNDARY_RECOVERY_ONLY'],
                    automatic_signal_or_training_kill=False,
                    diagnostic_interpretation='NO_TASK_STAGE_OR_OBSERVED_SUCCESSFUL_WORK_ADVANCE; ACTIVE_COMPUTE_CAN_BE_LONG_RUNNING')
            self._drain_checkpoint_results()
            self.flush()
            if self.checkpoint_sink and now-self.checkpoint_last >= self.checkpoint_interval:
                self.request_checkpoint()
            return data

    @staticmethod
    def _thread_stacks():
        names = {x.ident: x.name for x in threading.enumerate()}
        return [{'thread_id': ident, 'name': names.get(ident),
                 'frames': [{'file': f.filename, 'line': f.lineno, 'function': f.name}
                            for f in traceback.extract_stack(frame)]}
                for ident, frame in sys._current_frames().items()]

    def flush(self):
        with self.lock:
            for stream in self.streams.values():
                stream.flush(); os.fsync(stream.fileno())

    def _observer_error(self, exc, phase):
        row = {'at_utc': utc(), 'phase': phase, 'error_type': type(exc).__name__,
               'message': _clean(str(exc))}
        self.health_errors.append(row)
        try:
            sys.__stderr__.write('LIVE_LOG_OBSERVER_ERROR='+json.dumps(row, sort_keys=True)+'\n')
            sys.__stderr__.flush()
        except (OSError, AttributeError):
            pass

    def _safe_event(self, kind, **fields):
        try:
            return self.event(kind, **fields)
        except (OSError, ValueError, RuntimeError) as exc:
            self._observer_error(exc, kind)
            if kind == 'PROCESS_OUTPUT':
                try:
                    sys.__stderr__.write(_clean(fields.get('text', ''))); sys.__stderr__.flush()
                except (OSError, AttributeError):
                    pass
            return None

    def supervise(self, child, *, on_line=None, on_tick=None, on_observer_error=None):
        """Drain pipes without waiting for newline; silence cannot stop logs.

        Pass binary PIPEs (preferred) or text PIPEs. A child-owned stdout buffer
        can hide unflushed user output; Python is launched with -u by the runner.
        Observer heartbeat continues independently of that buffer and of native
        fits. No process is terminated by this observer.
        """
        try:
            self.set_child(child.pid)
        except ValueError as exc:
            if child.poll() is None:
                self._observer_error(exc, 'REGISTER_LIVE_CHILD')
            else:
                self._safe_event('CHILD_EXITED_BEFORE_IDENTITY_OBSERVATION', child_pid=child.pid,
                                 observed_returncode=child.returncode)
        selector = selectors.DefaultSelector(); decoders = {}; buffers = {}
        for name in ('stdout', 'stderr'):
            stream = getattr(child, name, None)
            if stream is not None:
                os.set_blocking(stream.fileno(), False)
                selector.register(stream.fileno(), selectors.EVENT_READ, name)
                decoders[name] = codecs.getincrementaldecoder('utf-8')('replace'); buffers[name] = ''
        last_tick = float('-inf'); returncode = None; exit_seen = None; recovery_requested = False
        def deliver_line(line):
            if on_line:
                try: on_line(line)
                except Exception as exc: self._observer_error(exc, 'OUTPUT_CALLBACK')
        try:
            while selector.get_map() or child.poll() is None:
                now = time.monotonic()
                if on_tick and now-last_tick >= min(10., self.interval):
                    try:
                        state = on_tick({'at_utc': utc(), 'child_pid': child.pid,
                                         'child_identity': self.child, 'status': 'RUNNING' if child.poll() is None else 'EXITED',
                                         'elapsed_seconds': now-self.started})
                        if isinstance(state, dict): self.update_state(state)
                    except Exception as exc:
                        self._observer_error(exc, 'SUPERVISOR_TICK_CALLBACK')
                    last_tick = now
                if self.health_errors and not recovery_requested:
                    recovery_requested = True
                    # Never abandon a live child's pipes when its observer
                    # fails. Request a caller-defined safe stop, keep draining.
                    if on_observer_error:
                        try: on_observer_error(copy.deepcopy(self.health_errors))
                        except Exception as exc: self._observer_error(exc, 'SAFE_RECOVERY_CALLBACK')
                events = selector.select(timeout=min(.25, self.interval))
                for key, _ in events:
                    name = key.data
                    try: body = os.read(key.fd, 65536)
                    except BlockingIOError: continue
                    if not body:
                        selector.unregister(key.fd)
                        tail = decoders[name].decode(b'', final=True)
                        if buffers[name] or tail:
                            text = buffers[name]+tail
                            if tail:
                                self._safe_event('PROCESS_OUTPUT', stream=name, text=tail)
                            deliver_line(text)
                            buffers[name] = ''
                        continue
                    text = decoders[name].decode(body)
                    # Captured bytes are visible immediately, including output
                    # without a newline. Only parser callbacks wait for lines.
                    self._safe_event('PROCESS_OUTPUT', stream=name, text=text)
                    buffers[name] += text
                    while '\n' in buffers[name]:
                        line, buffers[name] = buffers[name].split('\n', 1)
                        deliver_line(line+'\n')
                    if len(buffers[name]) > 1 << 20:
                        self._safe_event('OUTPUT_LINE_PARSER_BOUND', stream=name, discarded_callback_chars=len(buffers[name]),
                                         raw_capture_preserved=True)
                        buffers[name] = ''
                returncode = child.poll()
                if returncode is not None:
                    if exit_seen is None:
                        exit_seen = now; self.child_exit_observed_at_utc = utc()
                    if selector.get_map() and now-exit_seen > 2:
                        self._safe_event('CHILD_PIPE_HELD_AFTER_EXIT', child_returncode=returncode,
                                         pending_streams=[v.data for v in selector.get_map().values()],
                                         descendant_killed=False)
                        break
            returncode = child.wait()
            if self.child_exit_observed_at_utc is None:
                self.child_exit_observed_at_utc = utc()
            self._safe_event('CHILD_EXITED', child_identity=self.child, returncode=returncode,
                             status='SUCCEEDED' if returncode == 0 else 'FAILED',
                             completed_scientific_fits_inferred=False)
            try: self.heartbeat(force=True)
            except Exception as exc: self._observer_error(exc, 'CHILD_EXIT_HEARTBEAT')
            return returncode
        finally:
            selector.close()
            try: self.flush()
            except Exception as exc: self._observer_error(exc, 'SUPERVISOR_FLUSH')

    def set_checkpoint_sink(self, sink):
        with self.lock:
            self.checkpoint_sink = sink
            if self.thread and self.checkpoint_thread is None:
                self._start_checkpoint_worker()

    def _start_checkpoint_worker(self):
        self.checkpoint_thread = threading.Thread(target=self._checkpoint_loop,
                                                  name='sel-log-checkpoint', daemon=True)
        self.checkpoint_thread.start()

    def request_checkpoint(self):
        if self.checkpoint_sink is None:
            return False
        self.flush()
        request = {'paths': {k: str(p) for k, p in self.paths.items()},
                   'limits': {k: p.stat().st_size for k, p in self.paths.items()},
                   'invocation_id': self.invocation_id, 'project': self.project,
                   'release': self.release, 'at_utc': utc()}
        try:
            self.checkpoint_requests.put_nowait(request)
            self.checkpoint_last = time.monotonic(); return True
        except queue.Full:
            return False

    def _checkpoint_loop(self):
        while not self.checkpoint_stop.is_set() or not self.checkpoint_requests.empty():
            try: request = self.checkpoint_requests.get(timeout=.25)
            except queue.Empty: continue
            try:
                result = self.checkpoint_sink(request)
                self.checkpoint_results.put({'status': 'CHECKPOINT_COMPLETED', 'receipt': result})
            except Exception as exc:
                self.checkpoint_results.put({'status': 'CHECKPOINT_FAILED_LOCAL_LOGS_PRESERVED',
                                              'error_type': type(exc).__name__, 'message': str(exc)})
            finally:
                self.checkpoint_requests.task_done()

    def _drain_checkpoint_results(self):
        while True:
            try: row = self.checkpoint_results.get_nowait()
            except queue.Empty: break
            self.checkpoint_receipts.append(row)
            self.event('LOG_REMOTE_CHECKPOINT', **row)

    def snapshot(self, destination):
        """Copy a sealed byte prefix while live output safely continues."""
        with self.lock:
            self.event('LOG_RETURN_SNAPSHOT', destination=str(destination), sealed_archive_rewrite=False)
            self.flush()
        return snapshot_log_prefix(self.prefix, destination,
            expected_invocation_id=self.invocation_id, expected_project=self.project)

    def receipt(self):
        return {'schema': 'sports-edge-lab.live-log-receipt.v1', 'invocation_id': self.invocation_id,
                'project': self.project, 'release': self.release, 'producer_identity': self.identity,
                'paths': {k: str(p) for k, p in self.paths.items()},
                'heartbeat_samples': self.samples, 'heartbeat_target_seconds': self.interval,
                'maximum_observed_heartbeat_gap_seconds': self.max_gap,
                'heartbeat_interval_gate': 'PASS' if self.samples >= 2 and self.max_gap <= 15 else 'NOT_ESTABLISHED' if self.samples < 2 else 'FAIL',
                'closed': self.closed, 'health_errors': copy.deepcopy(self.health_errors),
                'remote_checkpoints': copy.deepcopy(self.checkpoint_receipts),
                'checkpoint_worker_pending': bool(self.checkpoint_thread and self.checkpoint_thread.is_alive()),
                'scientific_fit_claim_from_logging_tests': False}

    def close(self):
        if self.closed: return
        self.stop.set()
        if self.thread:
            self.thread.join(timeout=self.interval+2)
            if self.thread.is_alive():
                raise RuntimeError('LIVE_LOG_HEARTBEAT_DID_NOT_STOP; SNAPSHOT_NOT_CLOSED')
        try:
            self._safe_event('EXECUTION_LOG_CLOSING', health_errors=self.health_errors)
            try: self.heartbeat(force=True)
            except Exception as exc: self._observer_error(exc, 'CLOSE_HEARTBEAT')
            try: self.request_checkpoint()
            except Exception as exc: self._observer_error(exc, 'CLOSE_CHECKPOINT')
            self.checkpoint_stop.set()
            if self.checkpoint_thread: self.checkpoint_thread.join(timeout=2)
            with self.lock:
                try: self._drain_checkpoint_results()
                except Exception as exc: self._observer_error(exc, 'CLOSE_CHECKPOINT_RECEIPTS')
                self._safe_event('EXECUTION_LOG_CLOSED', checkpoint_pending=bool(self.checkpoint_thread and self.checkpoint_thread.is_alive()),
                                 local_logs_preserved=True)
                try: self.flush()
                except Exception as exc: self._observer_error(exc, 'CLOSE_FLUSH')
        finally:
            with self.lock:
                self.closed = True
                for stream in self.streams.values(): stream.close()
                fcntl.flock(self.lock_fd, fcntl.LOCK_UN); os.close(self.lock_fd)


class IncrementalLogCheckpoint:
    """Immutable compressed log suffixes: no full-log upload every heartbeat.

    `put` receives (relative_key, bytes, metadata) and returns an authenticated
    upload receipt. Run this object only on the dedicated checkpoint thread.
    Local offsets advance after a successful upload; a failed attempt leaves
    the byte range pending. Object keys are deterministic, retries idempotent.
    """
    def __init__(self, directory, put, *, max_chunk_bytes=1 << 20):
        self.directory = Path(directory); self.directory.mkdir(parents=True, exist_ok=True)
        self.put = put; self.max_chunk = int(max_chunk_bytes)
        if not 4096 <= self.max_chunk <= 8 << 20: raise ValueError('INVALID_LOG_CHECKPOINT_CHUNK')
        self.state_path = self.directory/'CHECKPOINT_STATE.json'
        self.lock = threading.Lock()

    def __call__(self, request):
        with self.lock:
            state = json.loads(self.state_path.read_bytes()) if self.state_path.exists() else {'streams': {}, 'chunks': []}
            key_id = request['invocation_id']; uploaded = []; new_bytes = 0
            for kind, path_value in request['paths'].items():
                path = _regular(path_value); limit = int(request['limits'][kind])
                identity = [str(path.absolute()), path.stat().st_dev, path.stat().st_ino]
                # A resumed append file retains its offset even if the new
                # invocation ID changes. No old log prefix is uploaded again.
                stream_id = hashlib.sha256(canonical(identity)).hexdigest()+':'+kind
                entry = state['streams'].get(stream_id, {'offset': 0, 'identity': identity})
                if entry['identity'] != identity or path.stat().st_size < entry['offset']:
                    raise ValueError('LOG_CHECKPOINT_SOURCE_IDENTITY_CHANGED_OR_SHRANK')
                offset = int(entry['offset'])
                with path.open('rb') as stream:
                    stream.seek(offset)
                    while offset < limit:
                        body = stream.read(min(self.max_chunk, limit-offset))
                        if not body: raise IOError('LOG_CHECKPOINT_SOURCE_SHORT_READ')
                        compressed = gzip.compress(body, compresslevel=3, mtime=0)
                        sha = hashlib.sha256(compressed).hexdigest()
                        key = f"{key_id}/{kind}/{offset:016d}-{offset+len(body):016d}-{sha}.gz"
                        metadata = {'sha256': sha, 'source_sha256': hashlib.sha256(body).hexdigest(),
                                    'offset': str(offset), 'end': str(offset+len(body)), 'invocation_id': key_id}
                        result = self.put(key, compressed, metadata)
                        if not isinstance(result, dict) or result.get('status') not in ('PUT_CONFIRMED', 'EXACT_OBJECT_ALREADY_CONFIRMED'):
                            raise RuntimeError('LOG_CHECKPOINT_UPLOAD_NOT_CONFIRMED')
                        row = {'key': key, 'bytes': len(compressed), 'source_bytes': len(body),
                               'sha256': sha, 'offset': offset, 'end': offset+len(body), 'upload': result}
                        offset += len(body); new_bytes += len(compressed); uploaded.append(row)
                        state['chunks'].append(row)
                        state['streams'][stream_id] = {'offset': offset, 'identity': identity}
                        state['remote_manifest_pending'] = True
                        atomic_json(self.state_path, state)
            manifest_receipt = None
            if state.get('remote_manifest_pending'):
                # Durable S3 recovery needs an index as well as log chunks.
                # Publish an immutable manifest only when new suffix bytes
                # were committed; retrying a failed manifest never reuploads
                # the already acknowledged chunks.
                manifest = {'schema': 'sports-edge-lab.remote-log-checkpoint.v1',
                            'project': request['project'], 'invocation_id': key_id,
                            'chunks': state['chunks'],
                            'streams': state['streams'],
                            'previous_manifest': state.get('remote_manifest')}
                body = gzip.compress(canonical(manifest)+b'\n', compresslevel=3, mtime=0)
                sha = hashlib.sha256(body).hexdigest()
                manifest_key = f'{key_id}/manifests/{sha}.json.gz'
                result = self.put(manifest_key, body, {'sha256': sha, 'invocation_id': key_id,
                                                       'kind': 'log-checkpoint-manifest'})
                if not isinstance(result, dict) or result.get('status') not in ('PUT_CONFIRMED', 'EXACT_OBJECT_ALREADY_CONFIRMED'):
                    raise RuntimeError('LOG_CHECKPOINT_MANIFEST_UPLOAD_NOT_CONFIRMED')
                manifest_receipt = {'key': manifest_key, 'bytes': len(body), 'sha256': sha,
                                    'upload': result}
                state['remote_manifest'] = manifest_receipt
                state['remote_manifest_pending'] = False
                atomic_json(self.state_path, state)
            return {'schema': 'sports-edge-lab.incremental-log-checkpoint.v1',
                    'at_utc': utc(), 'invocation_id': key_id, 'new_chunks': uploaded,
                    'new_compressed_bytes': new_bytes, 'new_source_bytes': sum(x['source_bytes'] for x in uploaded),
                    'new_manifest': manifest_receipt,
                    'latest_remote_manifest': state.get('remote_manifest'),
                    'new_upload_body_bytes_including_manifest': new_bytes+(manifest_receipt or {}).get('bytes', 0),
                    'unchanged_suffix_uploads': 0, 'historical_log_full_downloads': 0,
                    'state_path': str(self.state_path)}


class S3LogSink:
    """Owner-role-only sink using an existing bounded-timeout S3 client.

    No client creation, credentials, bucket/infrastructure changes, listings or
    GETs. New keys are private caller-selected log prefixes. The caller must
    supply the existing owner bucket and policy-approved prefix.
    """
    def __init__(self, client, bucket, prefix):
        self.client = client; self.bucket = str(bucket); self.prefix = str(prefix).strip('/')
        if not self.bucket or not self.prefix or '..' in self.prefix.split('/'):
            raise ValueError('LOG_S3_EXPLICIT_BUCKET_PREFIX_REQUIRED')
        self.calls = 0; self.bytes = 0; self.seconds = 0.; self.failures = 0

    def __call__(self, key, body, metadata):
        start = time.monotonic(); self.calls += 1; self.bytes += len(body)
        try:
            # Same deterministic content key is safe to repeat after a lost
            # receipt. This writes identical bytes; it does not scan/download.
            response = self.client.put_object(Bucket=self.bucket, Key=self.prefix+'/'+key,
                Body=body, ContentType='application/gzip', Metadata=metadata,
                ChecksumSHA256=base64.b64encode(hashlib.sha256(body).digest()).decode())
            returned = response.get('ChecksumSHA256')
            wanted = base64.b64encode(hashlib.sha256(body).digest()).decode()
            if returned is not None and returned != wanted:
                raise ValueError('LOG_S3_CHECKSUM_RESPONSE_MISMATCH')
            return {'status': 'PUT_CONFIRMED', 'bytes': len(body),
                    'sha256': hashlib.sha256(body).hexdigest(),
                    'VersionId': response.get('VersionId'), 'ETag': response.get('ETag'),
                    'checksum_acknowledged': returned == wanted,
                    'etag_is_not_treated_as_sha256': True}
        except Exception:
            self.failures += 1
            raise
        finally:
            self.seconds += time.monotonic()-start

    def receipt(self):
        return {'put_calls': self.calls, 'attempted_body_bytes': self.bytes,
                'elapsed_seconds': self.seconds, 'failed_calls': self.failures,
                'get_calls': 0, 'list_calls': 0, 'scope': 'LOG_CHECKPOINT_SINK_ONLY',
                'request_count_basis': 'SDK_METHOD_INVOCATIONS', 'internal_HTTP_retry_attempts': None,
                'body_bytes_basis': 'BODY_BYTES_PER_SDK_INVOCATION; RETRY_NETWORK_BYTES_NOT_OBSERVED'}

