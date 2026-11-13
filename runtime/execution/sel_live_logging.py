"""Per-run NFL adapter for the already verified, shared Sports Edge live logger.

The underlying module is retained byte-for-byte from the shared runtime. This
bridge adds exact LIVE_EXECUTION filenames, selected-project scope and bounded
NFL event normalization. It observes; it never grants resources or earns fits.
"""
from __future__ import annotations

import datetime as dt
import math
import os
from pathlib import Path
import re
import threading
import uuid

from sports_edge_live import LiveExecutionLog, project_measurements

PROJECTS = frozenset(('nfl', 'fbs', 'nba', 'ncaa_basketball'))
SCHEMA = 'sports-edge-lab.n085.live-event-adapter.v1'
_RUN_ID = re.compile(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,127}')
_PHASE_NOISE = frozenset(('resource_admission_decision', 'cpu_lease_released',
    'N080_MEASURED_PROGRESS', 'N075_TRANSIENT_RESOURCE_RECOVERY', 'N080_LOG_HEARTBEAT'))


def _safe(path):
    path = Path(path).absolute()
    if '..' in path.parts or any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError('LIVE_LOG_PROJECT_PATH_ALIAS')
    return path


def _num(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    try:
        return value if math.isfinite(value) and value >= 0 else None
    except (OverflowError, TypeError, ValueError):
        return None


def _map(value):
    return value if isinstance(value, dict) else {}


def _text(value, limit=240):
    return value[:limit] if isinstance(value, str) else None


def _scalars(source, names):
    source = _map(source)
    return {name: _num(source[name]) for name in names
            if name in source and _num(source[name]) is not None}


def new_run(home, project, *, release='N085', run_id=None, flush_seconds=10.):
    """Commit earliest-bootstrap logs before importing the scientific owner.

    Every invocation gets its own directory, even on an authentication failure.
    Existing runs cannot be overwritten or silently appended by this adapter.
    No environment, other-project directory or AWS resource is modified.
    """
    if project not in PROJECTS:
        raise ValueError('LIVE_LOG_EXACT_PROJECT_SELECTOR_REQUIRED')
    if isinstance(flush_seconds, bool) or not 10 <= float(flush_seconds) <= 15:
        raise ValueError('LIVE_LOG_FLUSH_INTERVAL_MUST_BE_10_TO_15_SECONDS')
    root = _safe(home)
    identifier = run_id or (dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')
                            + '_' + str(os.getpid()) + '_' + uuid.uuid4().hex[:12])
    if not isinstance(identifier, str) or not _RUN_ID.fullmatch(identifier):
        raise ValueError('LIVE_LOG_INVALID_PER_RUN_ID')
    directory = _safe(root / 'sports-edge-lab' / 'projects' / project / 'logs' / identifier)
    directory.parent.mkdir(parents=True, exist_ok=True)
    directory.mkdir(exist_ok=False)
    _safe(directory)
    log = LiveExecutionLog(directory / 'LIVE_EXECUTION', project=project,
        release=release, invocation_id=identifier, interval=float(flush_seconds))
    log._n085_observation_lock = threading.RLock()
    log._n085_last_source_phase = None
    log._n085_events_received = 0
    log._n085_pending_state = {}
    log._n085_latest_training = {}
    log._n085_observer_stop = threading.Event()
    log._n085_observer_ready = threading.Event()
    log.update_state({'stage_name': 'BOOTSTRAP_BEFORE_PACKAGE_AUTHENTICATION',
        'status': 'STARTING', 'eta_uncertainty': 'UNKNOWN_UNTIL_WORK_DENOMINATOR_AND_RATE_ARE_REPORTED',
        'checkpoint_locations': [], 'cpu_project_cap': None,
        'cost': {'status': 'NO_VERIFIED_PRICE_NO_DOLLAR_CLAIM', 'actual_billed_cost_usd': None}})
    try:
        log.__enter__()
    except BaseException:
        log.close()
        raise
    log.event('PER_RUN_LIVE_LOG_READY', adapter_schema=SCHEMA,
        path_policy='SELECTED_PROJECT_ONLY', requested_flush_seconds=float(flush_seconds),
        package_authenticated=False, new_scientific_fit_credit=0)
    log.flush()
    log._n085_observer_thread = threading.Thread(target=_observation_loop, args=(log,),
        name='sel-n085-state-bridge', daemon=True)
    log._n085_observer_thread.start()
    return log


def normalize_event(event):
    """Map known scalar scopes; never sum unrelated snapshots or infer fits.

    A receipt/phase change may reset its reported counters. Counters are kept
    as the current source's snapshot, never accumulated as new scientific work.
    Nonselecting monitor, native/meta totals and optimizer callbacks retain
    distinct labels. Missing observations are unknown rather than zero.
    """
    event = _map(event)
    result = {}
    source_stage = _text(event.get('stage'))
    phase = _text(event.get('stage_name')) or _text(event.get('owner_stage'))
    if phase is None and source_stage not in _PHASE_NOISE:
        phase = source_stage
    if phase:
        result['stage_name'] = phase
    for key in ('stage', 'total_stages'):
        if _num(event.get(key)) is not None:
            result[key] = event[key]
    if _text(event.get('status')):
        result['status'] = _text(event['status'])

    progress = _map(event.get('progress'))
    for key in ('completed', 'remaining', 'total', 'completed_tasks', 'remaining_tasks',
                'successes', 'failures', 'throughput_per_second'):
        number = _num(event.get(key, progress.get(key)))
        if number is not None:
            result[key] = number
    unit = _text(event.get('work_unit', progress.get('unit')))
    if unit:
        result['work_unit'] = unit
    remaining = _map(event.get('remaining_by_family'))
    if remaining and len(remaining) <= 32:
        observed = [_num(v) for v in remaining.values()]
        if all(v is not None for v in observed):
            result['remaining_tasks'] = sum(observed)
    eta = _map(event.get('eta'))
    for source_key, target in (('eta_seconds', 'eta_seconds'),):
        if source_key in event:
            result[target] = _num(event[source_key])
    if eta:
        result['eta_seconds'] = _num(eta.get('total_remaining_eta_seconds', eta.get('seconds')))
        result['eta_uncertainty'] = _text(eta.get('status')) or 'SOURCE_ETA_NOT_SUPPORTED'
    counts = _map(event.get('counts'))
    if counts:
        result['invocation_fit_counts'] = {
            'new': _num(counts.get('fits_new')), 'reused': _num(counts.get('fits_reused')),
            'failed': _num(counts.get('fits_failed')),
        }
        for source, target in (('experiments_complete', 'successes'), ('experiments_failed', 'failures')):
            if _num(counts.get(source)) is not None:
                result[target] = counts[source]
    elif any(k in event for k in ('new_fits', 'reused_fits', 'failed_fits')):
        result['invocation_fit_counts'] = {
            'new': _num(event.get('new_fits')), 'reused': _num(event.get('reused_fits')),
            'failed': _num(event.get('failed_fits')),
        }
    explicit_fits = _map(event.get('invocation_fit_counts'))
    if explicit_fits:
        result['invocation_fit_counts'] = {k: _num(explicit_fits.get(k)) for k in ('new', 'reused', 'failed')}

    training = {'source_schema': _text(event.get('schema')), 'source_stage': source_stage,
        'counts_scope': 'CURRENT_SOURCE_SNAPSHOT_NOT_SUMMED_WITH_OTHER_LANES',
        'new_fit_credit_from_logging': 0}
    if 'invocation_fit_counts' in result:
        training['fit_counter_source'] = {'schema': _text(event.get('schema')),
            'stage': source_stage, 'observed_at_utc': _text(event.get('at_utc', event.get('observed_at_utc'))),
            'counts_are_current_source_snapshot_not_cross_lane_totals': True}
    separate_fits = _scalars(event, ('new_native_fits', 'new_meta_fits', 'new_model_fits',
        'reused_native_fits', 'reused_meta_fits', 'observed_active_optimizer_calls',
        'peak_observed_active_optimizer_calls'))
    if separate_fits:
        training['reported_fit_details'] = separate_fits
    callbacks = _scalars(event.get('optimizer_callback_counts'), ('ENTERED', 'RETURNED', 'COMMITTED', 'FAILED'))
    if callbacks:
        training['optimizer_callbacks_native_and_meta_combined'] = callbacks
    native = _scalars(event.get('native'), ('real_estimator_fit_returns', 'failed_native_calls',
        'observed_active_native_fit_workers'))
    active = event.get('active_optimizer_calls')
    if isinstance(active, list) and len(active) <= 128:
        declared = _num(event.get('observed_active_optimizer_calls'))
        if declared == len(active) and all(isinstance(v, dict) and isinstance(v.get('meta'), bool) for v in active):
            native['observed_active_native_fit_workers'] = sum(not v['meta'] for v in active)
            training['observed_active_meta_fit_calls'] = sum(v['meta'] for v in active)
    if native:
        result['native'] = native
    # The shared logger samples exact PIDs/RSS/CPU itself. Foreign snapshots are
    # diagnostic-only and never replace its process identity/CPU denominator.
    result['training_progress'] = training
    workers = _map(event.get('workers'))
    if workers:
        result['workers'] = _scalars(workers, ('active', 'target'))
    admission = _map(event.get('snapshot'))
    cap = _num(admission.get('elastic_project_limit', admission.get('per_project_ceiling')))
    if cap is not None:
        result['cpu_project_cap'] = cap
        result['training_progress']['observed_resource_cap_source'] = source_stage
    for source, target in (('allocated_cpu_tokens', 'allocated_cpu_tokens'),
                           ('granted_cpus', 'granted_cpus'), ('active_tasks', 'active_tasks')):
        if _num(event.get(source)) is not None:
            result[target] = event[source]

    cache_source = _map(event.get('cache')) or event
    cache = _scalars(cache_source, ('cache_hits', 'cache_misses', 'cache_hits_count', 'requests',
        'local_cache_hits', 'reused_local_bytes', 'local_reused_bytes', 'upstream_fetch_calls',
        'cache_hit_percent_by_bytes', 'cache_hit_percent_by_requests', 'source_body_bytes_read',
        'original_verifier_calls', 'singleflight_waits', 'dead_claims_recovered'))
    if cache:
        cache['scope'] = 'REPORTED_CURRENT_SOURCE_COUNTERS_NOT_ALL_OWNER_NETWORK'
        cache['source_stage'] = source_stage
        result['cache'] = cache
    s3_source = _map(event.get('s3')) or event
    s3 = _scalars(s3_source, ('s3_get_count', 's3_get_bytes', 's3_put_count',
        's3_gets_completed', 's3_bytes', 'get_calls', 'put_calls', 'list_calls'))
    if s3:
        s3['scope'] = 'REPORTED_CURRENT_SOURCE_COUNTERS_NOT_ALL_OWNER_NETWORK'
        s3['source_stage'] = source_stage
        result['s3'] = s3

    cost = _map(event.get('cost'))
    normalized_cost = _scalars(cost, ('compute_usd', 'api_usd', 'total_usd',
        'estimated_whole_instance_invocation_usd', 'compute_rate_usd_per_hour'))
    compute = _num(event.get('running_compute_cost_usd', event.get('running_compute_estimate_usd')))
    if compute is not None:
        normalized_cost['reported_compute_estimate_usd'] = compute
    paid = _num(event.get('new_paid_calls'))
    if paid is not None:
        normalized_cost['reported_new_paid_calls'] = paid
    status = _text(cost.get('status', event.get('cost_status')))
    if normalized_cost or status:
        normalized_cost['status'] = status or 'REPORTED_ESTIMATE_NOT_BILL'
        normalized_cost['actual_billed_cost_usd'] = None
        result['cost'] = normalized_cost
    checkpoint = _text(event.get('checkpoint_status'))
    if checkpoint:
        result['checkpoint_locations'] = [{'status': checkpoint}]
    paths = event.get('checkpoint_locations')
    if isinstance(paths, (list, tuple)):
        result['checkpoint_locations'] = [_text(p, 500) for p in paths[:16] if isinstance(p, str)]
    return result


def check(log):
    if log.health_errors:
        raise RuntimeError('LIVE_LOG_OBSERVER_FAILED; PRESERVE_LOGS_AND_CHECKPOINTS')
    if log.closed:
        raise RuntimeError('LIVE_LOG_ALREADY_CLOSED')


def observe(log, event=None, **fields):
    """Coalesce current state without waiting on the logger's filesystem lock.

    The inherited immutable owner-event capture remains the full event record.
    This live display retains latest known scalar fields, not one disk write
    per admission event. The bridge lock protects only small in-memory objects;
    no resource/store lock is acquired on the heartbeat or bridge threads.
    """
    if event is not None and fields:
        raise ValueError('LIVE_LOG_ONE_EVENT_MAPPING_REQUIRED')
    event = fields if event is None else event
    if not isinstance(event, dict):
        raise TypeError('LIVE_LOG_EVENT_MAPPING_REQUIRED')
    check(log)
    normalized = normalize_event(event)
    with log._n085_observation_lock:
        log._n085_events_received += 1
        log._n085_latest_training.update(normalized.get('training_progress', {}))
        normalized['training_progress'] = dict(log._n085_latest_training)
        log._n085_pending_state.update(normalized)
        log._n085_observer_ready.set()
    return normalized


def _observation_loop(log):
    while True:
        log._n085_observer_ready.wait(.25)
        with log._n085_observation_lock:
            mapping = log._n085_pending_state
            log._n085_pending_state = {}
            log._n085_observer_ready.clear()
            stopping = log._n085_observer_stop.is_set()
        # Crucially outside the bridge lock: inherited heartbeat may hold its
        # own log lock during filesystem sync, but model callbacks never wait.
        try:
            if mapping:
                log.update_state(mapping)
                phase = mapping.get('stage_name')
                if phase and phase != log._n085_last_source_phase:
                    log._n085_last_source_phase = phase
                    log.event('WORKLOAD_PHASE_CHANGED', stage_name=phase,
                        counts_are_current_snapshot_not_new_fit_credit=True)
        except BaseException as exc:
            log.health_errors.append({'phase': 'N085_STATE_BRIDGE',
                'error_type': type(exc).__name__, 'error': 'LIVE_STATE_BRIDGE_FAILED'})
            return
        if stopping:
            return


def error(log, exc, *, phase=None):
    if phase:
        log.update_state({'stage_name': _text(phase), 'status': 'FAILED'})
    else:
        log.update_state({'status': 'FAILED'})
    log.event('EXECUTION_EXCEPTION', exception_type=type(exc).__name__, message=str(exc)[:2000])
    log.flush()


def close(log, *, status='COMPLETED'):
    """Bound observer shutdown; explicitly report uninterruptible log I/O."""
    previous = getattr(log, '_n085_close_worker', None)
    if not log.closed and (previous is None or not previous.is_alive()):
        log._n085_observer_stop.set()
        log._n085_observer_ready.set()
        def finish():
            try:
                log._n085_observer_thread.join(timeout=1.)
                if log._n085_observer_thread.is_alive():
                    log.stop.set()
                    raise RuntimeError('LIVE_LOG_STATE_BRIDGE_CLOSE_PENDING_IO')
                log.update_state({'status': str(status)[:100]})
                log.event('EXECUTION_FINAL_STATUS', status=str(status)[:100],
                    normalized_source_events=log._n085_events_received,
                    new_scientific_fit_credit=0)
                log.close()
            except BaseException as exc:
                log.health_errors.append({'phase': 'N085_LOG_CLOSE',
                    'error_type': type(exc).__name__, 'error': 'LIVE_LOG_CLOSE_INCOMPLETE'})
        log._n085_close_worker = threading.Thread(target=finish, name='sel-n085-log-close', daemon=True)
        log._n085_close_worker.start()
    worker = getattr(log, '_n085_close_worker', None)
    if worker is not None:
        worker.join(timeout=2.)
    receipt = log.receipt()
    receipt['adapter_close_pending_io'] = bool(worker and worker.is_alive()) or not log.closed
    receipt['normalized_source_events'] = log._n085_events_received
    receipt['adapter_schema'] = SCHEMA
    return receipt
