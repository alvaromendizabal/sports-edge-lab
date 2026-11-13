"""Sanitized V9 coverage and execution evidence, without fits or rescoring.

This generic display module consumes saved selected outputs and explicit owner
receipts. It never opens a source ledger, changes an original issue, computes a
sport metric, infers a result, or ranks incomparable model cohorts.
"""
from __future__ import annotations

from collections import Counter
import datetime as dt
import hashlib
import html
import json
import math
import re

SCHEMA = 'sports-edge-lab.nba.v9-publication.v1'
PUBLIC_FILENAME = 'latest_v9_acceptance.json'
BEGIN = '<!-- NBA V9 ACCEPTANCE BEGIN -->'
END = '<!-- NBA V9 ACCEPTANCE END -->'
WINDOWS = ('FULL_CURRENT_SEASON', 'LAST_1_WEEK', 'LAST_2_WEEKS', 'LAST_4_WEEKS')
TRACKS = (
    'FROZEN_HISTORICAL_SELECTED', 'CURRENT_FIXED_STATE_REPLAY',
    'NEW_SEASON_FROZEN_REFRESH', 'PRESERVED_SEASON_FROZEN_ARRAY',
    'PRESERVED_WEEKLY_CURRENT_ARRAY', 'ORIGINAL_ISSUED_ROLLING',
)
METRICS = ('accuracy', 'log_loss', 'brier', 'mae', 'rmse', 'ece_10_bins', 'ece_10_fixed_bins',
           'crps', 'weighted_interval_score', 'interval_50_coverage',
           'interval_80_coverage', 'interval_90_coverage')
RECEIPTS = ('V9_cache', 'V9_parallel', 'V9_acceptance', 'V9_science', 'V9_layout')
NUMERIC_FIELDS = {
    'elapsed_seconds', 'fit_wall_seconds', 'wall_seconds', 'heartbeat_max_gap_seconds',
    'heartbeat_interval_seconds', 'configured_workers', 'active_workers',
    'configured_native_threads', 'observed_native_fit_peak', 'native_fit_peak',
    'native_fit_workers_peak', 'native_cpu_equivalents_peak', 'cpu_equivalents_peak',
    'actual_native_fit_workers_peak', 'actual_cpu_equivalents_peak',
    'ready_queue_depth', 'peak_ready_queue_depth', 'completed_native_fits',
    'new_estimator_fits', 'reused_estimator_fits', 'new_calibration_fits',
    'new_preprocessor_fits', 'completed_fits', 'fit_count', 'failed_fits',
    'fits_per_minute', 'fits_per_second', 'measured_speedup',
    'local_cache_hits', 'cache_hits', 'cache_misses', 'local_bytes_reused',
    'downloaded_bytes', 'full_get_requests', 'unjustified_full_get_requests',
    'paid_requests', 'duplicate_paid_requests', 'avoided_paid_requests',
    'immutable_historical_byte_reuse_ratio', 'historical_byte_reuse_ratio',
    'immutable_bytes_required', 'immutable_bytes_reused', 'saved_seconds',
    'startup_seconds', 'manifest_seconds', 'cache_lookup_seconds',
    'normalization_seconds', 'feature_seconds', 'fit_seconds', 'evaluation_seconds',
    'publication_seconds', 'return_seconds', 'physical_bytes', 'member_count',
    'part_count', 'maximum_part_bytes', 'maximum_return_bytes', 'workers',
    'native_threads_per_worker', 'cpu_lease', 'sample_count', 'scored_games',
    'completed_games', 'missing_games', 'full_game_denominator',
    'local_reused_bytes', 's3_bytes', 's3_gets', 'failed_reads', 'byte_hit_fraction',
    'unique_content_objects', 'physical_cached_bytes', 'maximum_cached_bytes', 'source_count',
    'real_estimator_fit_returns', 'synthetic_estimator_fit_returns', 'failed_native_calls',
    'calibrator_fit_returns', 'observed_peak_concurrent_native_fits',
    'peak_concurrent_native_fits', 'seconds_with_native_fit_overlap',
    'native_fit_process_cpu_seconds', 'native_fit_elapsed_seconds_sum',
    'mean_cpu_equivalents_per_native_call', 'p50_native_fit_seconds', 'p95_native_fit_seconds',
    'observed_active_native_fit_workers', 'unqualified_clock_intervals',
    's3_objects_copied_moved_deleted', 'total_bytes', 'used_bytes', 'free_bytes',
    'heartbeat_target_seconds', 'observed_heartbeat_samples', 'used_cpu_equivalents',
    'requested_cpus', 'granted_cpus', 'real_new_native_fits', 'peak_reserved_tokens',
    'new_native_fits_per_hour', 'pending', 'completed', 'failed', 'running',
    's3_get_attempts', 's3_gets_completed', 'local_cache_bytes', 'cache_hit_byte_ratio',
    'requested_workers', 'native_threads_per_task', 'requested_cpu_tokens', 'new_native_fits',
    'reused_tasks', 'native_process_cpu_seconds', 'registered_unique_tasks',
    'repeated_completed_fits_for_benchmark', 'throughput_ratio_vs_1x1',
    's3_transfer_seconds', 'files_hashed', 'bytes_hashed',
    'verified_unchanged_files_reused', 'verified_unchanged_bytes_reused',
    'contexts', 'rows', 'bytes_read', 'historical_full_S3_GETs',
    'repeated_label_adapter_calls', 'native_model_or_preprocessor_fits',
    'newly_materialized_contexts', 'exact_archive_readbacks_reused',
    'unique_archive_proof_reuses', 'verified_virtual_bytes_covered_by_reused_archive_proofs',
    'original_file_pins_compared', 'baseline_rebuilds_avoided',
    'lazy_object_decodes_actually_requested', 'archive_hits', 'archive_misses',
    'archive_invalidated', 'archive_proofs_completed', 'baseline_hits',
    'baseline_misses', 'baseline_invalidated', 'baseline_proofs_completed',
    'cache_writes_deferred_for_storage', 'maximum_cached_proof_bytes',
    'cached_decoded_object_bytes', 'real_estimator_fits', 'head_calls',
    'exact_key_list_calls', 'client_preparation_failures', 'source_body_gets',
    'broad_historical_listings',
}
BOOLEAN_FIELDS = {
    'owner_run_completed', 'acceptance_passed', 'measured', 'rerun_measured',
    'byte_reuse_verified', 'no_unjustified_full_gets', 'no_duplicate_paid_requests',
    'native_fit_observed', 'heartbeat_requirement_met', 'all_games_accounted_for',
    'synthetic_only', 'configuration_only', 'original_issues_unchanged',
    'exact_tree_verified', 'render_verified', 'reopen_verified',
    'all_pipeline_s3_calls_instrumented', 'automatic_eviction_permitted',
    'etag_used_as_sha256', 'source_rights_or_clock_eligibility_changed',
    'independent_cache_instance', 'new_owner_invocation_claim',
    'second_pass_network_disabled', 'parsing_or_model_speedup_claimed',
    'configured_workers_or_wrapper_overlap_used_as_native_fit_evidence',
    'scientific_commit_counts_are_separate_from_returned_native_fits',
    'owner_AWS_execution_verified', 'active_cpu_coordinator_moved_or_forked',
    'ncaa_men_women_separate_one_owner', 'physical_legacy_models_relocated',
    'preflight_no_progress_escalated', 'training_wallclock_deadline_applied',
    'synthetic_fixture', 'owner_benchmark_complete', 'complete_provenance',
    'configured_workers_used_as_observed_concurrency',
    'different_scientific_tasks_are_not_repeated_timing_trials',
    'all_pipeline_S3_calls_instrumented', 'uninstrumented_S3_calls_reported_as_zero',
    'expected_pins_remain_upstream_authority', 'unchanged_stat_reuse_is_not_fresh_full_byte_hash',
    'source_clocks_and_exact_values_preserved', 'original_authenticated_adapter_completed',
    'automatic_eviction_or_resize', 'first_use_full_exact_reconstruction_required',
    'complete_dependency_stat_guards_required', 'unchanged_verifier_and_runtime_required',
    'source_file_pins_still_compared', 'current_full_decode_claimed_for_reuse',
    'old_scientific_files_modified', 'new_source_clocks_assumed',
}
CODE_FIELDS = {'status', 'scope', 'evidence_class', 'measurement_class', 'reason',
               'exception_reason', 'workload_class', 'benchmark_kind', 'architecture', 'activity_class', 'timing_scope',
               'cache_status', 'verification', 'format', 'measurement_phase', 'elapsed_seconds_scope'}
# These source qualifiers contain punctuation. Copy only their exact known
# literals so their important limits survive without admitting arbitrary text.
QUALIFIED_RECEIPT_TEXT = {
    'reused_byte_counter_scope': {'UNIQUE_REUSED_ARCHIVE_INDEX_ORIGINAL_BYTES; MAY_INCLUDE_SHARED_EXTERNAL_FILES; NOT_PHYSICAL_IO_SAVED'},
    'transfer_byte_scope': {'COMPLETE_FETCHED_BODIES; FAILED_PARTIAL_TRANSFER_BYTES_UNOBSERVED'},
    'call_count_scope': {'SDK_METHOD_INVOCATIONS_INCLUDING_FAILURES; HTTP_RETRIES_NOT_INFERRED'},
}
CACHE_RECEIPT_BLOCKS = ('authenticated_context_cache', 'verified_file_cache',
    'transport_proof_cache', 'finalizer_transport_proof_cache',
    'finalizer_verified_file_cache', 'source_version_refresh')
CLOCK_FIELDS = {'started_at_utc', 'finished_at_utc', 'observed_at_utc',
                'training_cutoff_utc', 'actual_materialized_at_utc'}
NEXT_ACTION = {
    'OFFICIAL_MATCHUP_NOT_ASSIGNED': 'Refresh the official schedule in the owner run; retain the unresolved row.',
    'OFFICIAL_PHASE_NOT_ADMITTED_TO_REGISTERED_MODEL_TARGETS': 'Retain this official game and qualify a separate phase policy before forecasting it.',
    'OFFICIAL_TARGET_NOT_ADMITTED_AT_SOURCE': 'Audit the saved target eligibility in the owner run.',
    'NO_ACTIVE_CHAMPION_FOR_TARGET_HORIZON': 'Restore or register an admissible target/horizon role in the owner run.',
    'NO_ORIGINAL_ISSUE_FOR_CURRENT_CHAMPION': 'Issue an admissible current-role forecast before a future tip; keep missing past issues explicit.',
    'NO_RECOVERED_ORIGINAL_PREGAME_FORECAST': 'Recover an authenticated original issue, or publish future issues with true clocks; label any replay separately.',
    'SOME_CURRENT_ROLE_ISSUES_MISSING': 'Recover the missing selected roles or issue their next eligible future forecasts.',
    'AVAILABLE_ORIGINAL_ISSUES': 'Preserve the original issue values and clocks.',
}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def fail(reason):
    raise ValueError('V9_PUBLICATION_' + reason)


def count(value):
    if type(value) is not int or value < 0:
        fail('NONNEGATIVE_INTEGER_REQUIRED')
    return value


def number(value):
    if type(value) not in (int, float) or not math.isfinite(value):
        fail('FINITE_SAVED_NUMBER_REQUIRED')
    return value


def code(value):
    return value if isinstance(value, str) and re.fullmatch(r'[A-Z][A-Z0-9_]{0,110}', value) else 'SOURCE_STATUS_UNAVAILABLE'


def clock(value):
    if value is None:
        return None
    if not isinstance(value, str):
        fail('SOURCE_CLOCK_REQUIRED')
    try:
        parsed = dt.datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError:
        fail('SOURCE_CLOCK_REQUIRED')
    if parsed.tzinfo is None:
        fail('SOURCE_CLOCK_REQUIRED')
    return value


def safe_id(value):
    if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,96}', value):
        fail('PUBLIC_ID_REQUIRED')
    return value


def safe_roles(value):
    if not isinstance(value, str) or len(value) > 4096:
        fail('PUBLIC_ROLE_ALIAS_REQUIRED')
    return ', '.join(safe_id(part) for part in value.split(', '))


def _scalar_receipt(source):
    """Only typed allowlisted aggregates; private paths and recipes are dropped."""
    out = {}
    for key in sorted(NUMERIC_FIELDS & source.keys()):
        if source[key] is not None:
            out[key] = number(source[key])
    for key in sorted(BOOLEAN_FIELDS & source.keys()):
        if type(source[key]) is not bool:
            fail('BOOLEAN_RECEIPT_REQUIRED')
        out[key] = source[key]
    for key in sorted(CODE_FIELDS & source.keys()):
        out[key] = code(source[key])
    for key in sorted(CLOCK_FIELDS & source.keys()):
        out[key] = clock(source[key])
    for key, allowed in QUALIFIED_RECEIPT_TEXT.items():
        if key in source:
            out[key] = source[key] if isinstance(source[key], str) and source[key] in allowed else 'SOURCE_STATUS_UNAVAILABLE'
    if source.get('layout') is not None:
        if source['layout'] not in ('1x1', '4x1', '8x1', '12x1', '6x2', '4x3', '3x4'):
            fail('REGISTERED_PUBLIC_BENCHMARK_LAYOUT_REQUIRED')
        out['layout'] = source['layout']
    return out


def receipt_view(name, source):
    if source is None:
        return {'section': name, 'source_present': False, 'status': 'OWNER_RUN_EVIDENCE_NOT_SUPPLIED',
                'verified_acceptance_claim': False, 'measurements': {}, 'benchmarks': []}
    if not isinstance(source, dict):
        fail('RECEIPT_OBJECT_REQUIRED')
    result = {'section': name, 'source_present': True, 'status': code(source.get('status')),
              'verified_acceptance_claim': False, 'measurements': _scalar_receipt(source), 'benchmarks': []}
    # A source's explicit pass is displayed as its claim, not independently
    # reclassified as measured native work by a renderer.
    result['source_acceptance_claim'] = source.get('acceptance_passed') is True
    for row in source.get('benchmarks', source.get('configurations', [])):
        if not isinstance(row, dict) or len(result['benchmarks']) >= 100:
            fail('BOUNDED_BENCHMARK_OBJECT_REQUIRED')
        result['benchmarks'].append(_scalar_receipt(row))
    result['speedups'] = [_scalar_receipt(row) for row in source.get('speedups', [])[:100]]
    for field in ('measurements', 'summary', 'counts', 'timings', 'native_fit_summary', 'cache_summary',
                  'second_pass', 'native_overlap', 'estimator_method_overlap', 'neural_loop_overlap', 'storage', 'native', 'latest_heartbeat', 'repeat_read_gate') + CACHE_RECEIPT_BLOCKS:
        if isinstance(source.get(field), dict):
            # Version-refresh failures contain private locators, while the
            # similarly named runtime field is a numeric queue counter.
            scalars = source[field] if field != 'source_version_refresh' else {k:v for k,v in source[field].items() if k != 'failed'}
            result[field] = _scalar_receipt(scalars)
            if field == 'latest_heartbeat':
                result[field]['queue'] = _scalar_receipt(source[field].get('queue') or {})
                result[field]['underutilization_reason_codes'] = [code(x) for x in source[field].get('underutilization_reason_codes', [])][:100]
            if field == 'repeat_read_gate' and isinstance(source[field].get('second_pass'), dict):
                result[field]['second_pass'] = _scalar_receipt(source[field]['second_pass'])
    return result


def publication_lifecycle(source=None):
    source = source or {}
    result = {}
    for stage in ('prepared', 'committed', 'merged', 'deployed'):
        item = source.get(stage) or {}
        if not isinstance(item, dict):
            fail('LIFECYCLE_OBJECT_REQUIRED')
        verified = item.get('verified') is True
        out = {'verified': verified, 'status': code(item.get('status', 'NOT_VERIFIED'))}
        if item.get('observed_at_utc') is not None:
            out['observed_at_utc'] = clock(item['observed_at_utc'])
        for key in ('commit_sha', 'tree_sha', 'artifact_sha256'):
            if item.get(key) is not None:
                if not isinstance(item[key], str) or not re.fullmatch(r'[a-f0-9]{40}|[a-f0-9]{64}', item[key]):
                    fail('PUBLICATION_DIGEST_REQUIRED')
                out[key] = item[key]
        if item.get('url') is not None:
            if not isinstance(item['url'], str) or not re.fullmatch(r'https://(?:github\.com|raw\.githubusercontent\.com)/alvaromendizabal/sports-edge-lab/[^\s<>"\']+', item['url']):
                fail('ESTABLISHED_PUBLIC_REPOSITORY_URL_REQUIRED')
            out['url'] = item['url']
        if verified and stage in ('committed', 'merged') and 'commit_sha' not in out:
            fail('COMMIT_EVIDENCE_REQUIRED')
        if verified and stage == 'deployed' and ('artifact_sha256' not in out or 'url' not in out):
            fail('DEPLOYMENT_EVIDENCE_REQUIRED')
        result[stage] = out
    result['source_publication_is_website_deployment'] = False
    return result


def _actual(game):
    result = game.get('result_observation')
    if not result:
        return {'status': 'NO_SOURCE_BOUND_FINAL_SCORE_IN_SELECTED_EXPORT', 'home_points': None, 'away_points': None}
    if not isinstance(result, dict):
        fail('RESULT_OBJECT_REQUIRED')
    return {'status': code(result.get('status')), 'home_points': count(result['home_points']),
            'away_points': count(result['away_points']),
            'ended_at_utc': clock(result.get('ended_at_utc')),
            'observed_at_utc': clock(result.get('observed_at_utc')),
            'available_at_utc': clock(result.get('available_at_utc')),
            'evidence_class': code(result.get('evidence_track')),
            'new_score_calculation': False}


def game_inventory(public):
    games = public.get('games') or {}
    coverage = public.get('game_coverage') or {}
    if not isinstance(games, dict) or set(games) != set(coverage):
        fail('EVERY_OBSERVED_GAME_REQUIRES_COVERAGE')
    if len(games) > 10000:
        fail('GAME_BOUND_EXCEEDED')
    groups = public.get('role_groups') or {}
    views = {}
    for item in public.get('role_views') or []:
        key = (item.get('game_id'), item.get('champion_role'))
        if key in views:
            fail('DUPLICATE_GAME_ROLE_VIEW')
        views[key] = item
    issues = public.get('issues') or {}
    rows = []
    for gid, game in sorted(games.items()):
        safe_id(gid)
        cov = coverage[gid]
        expected = set(groups.get(cov.get('applicable_role_group'), []))
        available = set(cov.get('current_role_ids_available') or [])
        declared_missing = cov.get('current_role_ids_missing')
        missing = expected if declared_missing == 'ALL_APPLICABLE_ROLES' else set(declared_missing or [])
        if available & missing or available | missing != expected:
            fail('GAME_ROLE_DENOMINATOR_DOES_NOT_CLOSE')
        cells = []
        for target in ('winner', 'margin', 'total'):
            for horizon in (60, 120):
                source = (cov.get('target_horizon') or {}).get(f'{target}_T{horizon}')
                if not isinstance(source, dict):
                    fail('SIX_TARGET_HORIZON_CELLS_REQUIRED')
                need = count(source.get('expected_roles'))
                present = count(source.get('current_roles_available'))
                if present > need:
                    fail('AVAILABLE_ROLES_EXCEED_DENOMINATOR')
                status = code(source.get('status'))
                cells.append({'target': target, 'horizon_minutes': horizon, 'expected_roles': need,
                              'current_roles_available': present, 'missing_roles': need - present,
                              'status': status})
        if sum(x['expected_roles'] for x in cells) != len(expected) or sum(x['current_roles_available'] for x in cells) != len(available):
            fail('GAME_TARGET_ROLE_DENOMINATOR_MISMATCH')
        refs = []
        for role in sorted(available):
            item = views.get((gid, role))
            if item is None or item.get('current_issue_ref') not in issues:
                fail('AVAILABLE_ROLE_REQUIRES_ORIGINAL_ISSUE')
            issue_ref = item['current_issue_ref']; issue = issues[issue_ref]
            if issue.get('game_id') != gid or issue.get('original_pregame_issue') is not True:
                fail('ORIGINAL_ISSUE_IDENTITY_REQUIRED')
            ref = {'role_alias': safe_id(role), 'issue_ref': safe_id(issue_ref),
                   'target': issue['target'], 'horizon_minutes': issue['horizon_minutes'],
                   'prediction': number(issue['prediction']),
                   'issued_at_utc': clock(issue.get('issued_at_utc')),
                   'source_asof_utc': clock(issue.get('source_asof_utc')),
                   'actual_lead_minutes': number(issue['actual_lead_minutes']),
                   'issue_horizon_class': code(issue.get('issue_horizon_class')),
                   'source_age_seconds_at_issue': number(issue['source_age_seconds_at_issue']),
                   'uncertainty_status': 'ORIGINAL_ISSUED_INTERVALS' if issue.get('prediction_intervals') else 'NO_ORIGINAL_INTERVAL_IN_SELECTED_ISSUE'}
            if issue.get('prediction_intervals'):
                intervals = {}
                for level in ('50', '80', '90'):
                    if level in issue['prediction_intervals']:
                        interval = issue['prediction_intervals'][level]
                        if not isinstance(interval, list) or len(interval) != 2 or number(interval[0]) > number(interval[1]):
                            fail('ORDERED_ORIGINAL_INTERVAL_REQUIRED')
                        intervals[level] = list(interval)
                ref['prediction_intervals'] = intervals
            refs.append(ref)
        rows.append({'game_id': gid, 'season': game.get('season'), 'phase': game.get('phase'),
                     'current_official_inventory_member': game.get('schedule_membership', 'CANONICAL_OFFICIAL') == 'CANONICAL_OFFICIAL',
                     'home_team': safe_id(game['home_team']) if game.get('home_team') else None,
                     'away_team': safe_id(game['away_team']) if game.get('away_team') else None,
                     'scheduled_start_utc': clock(game.get('scheduled_start_utc')),
                     'last_confirmed_status': code(game.get('last_confirmed_status')),
                     'last_confirmed_status_asof_utc': clock(game.get('last_confirmed_status_asof_utc')),
                     'schedule_source_asof_utc': clock(game.get('schedule_source_asof_utc')),
                     'tip_time_relation_at_report': code(game.get('tip_time_relation_at_report')),
                     'identity_status': code(game.get('identity_status')),
                     'expected_current_roles': len(expected), 'available_current_roles': len(available),
                     'missing_current_roles': sorted(missing), 'target_horizon': cells,
                     'selected_original_issues': refs, 'actual': _actual(game),
                     'joint_home_away_score_center_status': 'NO_COHERENT_JOINT_SCORE_CENTER_ADMITTED',
                     'per_game_error_status': 'NO_SAVED_PER_GAME_ERROR_EXPORT_SUPPLIED'})
    return rows


def _saved_window_rows(science):
    rows = []
    for item in science.get('window_metrics', []):
        if not isinstance(item, dict) or len(rows) >= 10000:
            fail('BOUNDED_WINDOW_METRICS_REQUIRED')
        if item.get('window') not in WINDOWS or item.get('evidence_track') not in TRACKS:
            fail('WINDOW_POLICY_REQUIRED')
        if item.get('target') not in ('winner', 'margin', 'total') or item.get('horizon_minutes') not in (60, 120):
            fail('WINDOW_TARGET_HORIZON_REQUIRED')
        total = count(item['completed_game_denominator']); scored = count(item['scored_games'])
        missing = count(item['missing_games'])
        if scored + missing != total:
            fail('WINDOW_DENOMINATOR_CLOSURE_REQUIRED')
        metrics = {key: round(number(value), 6) for key, value in (item.get('metrics') or {}).items() if key in METRICS and value is not None}
        rows.append({'window': item['window'], 'evidence_track': item['evidence_track'],
                     'role_alias': safe_id(item['role_alias']), 'target': item['target'],
                     'horizon_minutes': item['horizon_minutes'], 'scored_games': scored,
                     'completed_game_denominator': total, 'missing_games': missing,
                     'metrics': metrics, 'status': code(item.get('status')),
                     'window_start_utc': clock(item.get('window_start_utc')),
                     'window_end_utc': clock(item.get('window_end_utc')),
                     'selection_or_promotion_allowed': False})
    return rows


def build_v9_review(public, owner=None, model_review=None, lifecycle=None):
    before = canonical(public)
    owner = owner or {}; model_review = model_review or {}
    games = game_inventory(public)
    schedule = public.get('schedule_observation') or {}
    regular = sum(game['phase'] == 'regular' and game['current_official_inventory_member'] for game in games)
    expected = schedule.get('regular_season_expected_full_count')
    missing_slots = schedule.get('regular_season_not_observed_count')
    if expected is not None and missing_slots is not None and regular + count(missing_slots) != count(expected):
        fail('FULL_REGULAR_DENOMINATOR_DOES_NOT_CLOSE')
    source_count = (public.get('coverage') or {}).get('official_schedule_games')
    official_count = sum(game['current_official_inventory_member'] for game in games)
    if source_count is not None and count(source_count) != official_count:
        fail('SOURCE_OBSERVED_GAME_COUNT_MISMATCH')
    windows = _saved_window_rows(owner.get('V9_science') or {})
    window_coverage = []
    for track in TRACKS:
        for window in WINDOWS:
            matches = [row for row in windows if row['window'] == window and row['evidence_track'] == track]
            window_coverage.append({'evidence_track': track, 'window': window,
                'saved_metric_rows': len(matches),
                'status': 'SAVED_OWNER_WINDOW_METRICS' if matches else 'NO_SAVED_OWNER_WINDOW_METRICS',
                'full_current_season_best_claim': False,
                'ranking_status': 'EXACT_COMMON_GAME_COHORT_AND_UNCERTAINTY_REQUIRED'})
    metric_rows = model_review.get('metric_rows') or []
    aliases = {'FROZEN_HISTORICAL': 'FROZEN_HISTORICAL_SELECTED', 'SAVED_SEASON_FROZEN_ARRAY': 'PRESERVED_SEASON_FROZEN_ARRAY', 'SAVED_WEEKLY_CURRENT_ARRAY': 'PRESERVED_WEEKLY_CURRENT_ARRAY'}
    diagnostics = []
    for index, row in enumerate(metric_rows):
        diagnostics.append({'source_index': index, 'season': row.get('season'),
            'evidence_track': aliases.get(row.get('evidence_track'), row.get('evidence_track')),
            'role_alias': safe_roles(row['role_alias']), 'target': row.get('target'),
            'horizon_minutes': row.get('horizon_minutes'), 'scored_games': row.get('scored_games'),
            'completed_game_denominator': row.get('completed_game_denominator'),
            'metrics': {key: number(value) for key, value in (row.get('metrics') or {}).items()
                        if key in METRICS and value is not None},
            'training_cutoff_utc': clock(row.get('training_cutoff_utc')),
            'actual_materialized_at_utc': clock(row.get('actual_materialized_at_utc')),
            'promotion_allowed': False})
    policy_rows = []
    for track in TRACKS:
        subset = [row for row in metric_rows if aliases.get(row.get('evidence_track'), row.get('evidence_track')) == track]
        policy_rows.append({'evidence_track': track, 'saved_metric_rows': len(subset),
                           'status': 'SAVED_METRICS_AVAILABLE' if subset else 'NO_SAVED_METRICS_IN_THIS_EXPORT',
                           'original_issue_evidence': track == 'ORIGINAL_ISSUED_ROLLING',
                           'automatic_promotion': False})
    issues = public.get('issues') or {}
    result = {'schema': SCHEMA, 'rule_version': 'V9_2026_11_12',
        'evidence_as_of_utc': clock(public.get('evidence_as_of_utc')),
        'latest_original_issue_at_utc': clock(public.get('latest_forecast_issue_at_utc')),
        'selected_output_sha256': hashlib.sha256(before + b'\n').hexdigest(),
        'original_issues_sha256': hashlib.sha256(canonical(issues)).hexdigest(),
        'publication_new_fits': 0, 'publication_new_inference': 0, 'publication_new_metric_scoring': 0,
        'original_issues_modified': False, 'automatic_promotions': 0,
        'coverage': {'observed_games': len(games), 'current_official_inventory_games': official_count,
            'retained_original_issue_only_games': len(games) - official_count,
            'regular_observed_games': regular,
            'regular_full_season_denominator': expected, 'unobserved_regular_slots': missing_slots,
            'future_full_schedule_complete': schedule.get('future_full_schedule_complete') is True,
            'observed_inventory_reconciled': True, 'full_season_completion_claim': False,
            'all_target_horizon_cells': sum(len(g['target_horizon']) for g in games),
            'expected_current_role_cells': sum(g['expected_current_roles'] for g in games),
            'available_current_role_cells': sum(g['available_current_roles'] for g in games),
            'missing_current_role_cells': sum(len(g['missing_current_roles']) for g in games),
            'future_tips_at_evidence_snapshot': sum(g['tip_time_relation_at_report'] == 'FUTURE_TIP' for g in games),
            'row_backed_status_counts': dict(sorted(Counter(g['last_confirmed_status'] for g in games).items())),
            'games_with_source_bound_final_score': sum(g['actual']['status'] == 'FINAL' for g in games),
            'missingness_next_action': 'Owner refresh must reconcile all official identities and remaining schedule slots, then produce admissible selected forecasts with real clocks.'},
        'schedule_observation': {key: schedule.get(key) for key in ('owner_release', 'snapshot_started_at_utc', 'snapshot_finished_at_utc', 'earliest_individual_source_clock', 'latest_individual_source_clock')},
        'game_rows': games, 'missing_reason_next_owner_actions': NEXT_ACTION,
        'model_policy_coverage': policy_rows,
        'saved_metric_diagnostics': diagnostics,
        'window_metric_rows': windows, 'window_coverage': window_coverage,
        'metric_uncertainty_status': 'SAVED_MODEL_SCORES_DO_NOT_ESTABLISH_PAIRED_CONFIDENCE_INTERVALS',
        'runtime_receipts': [receipt_view(key, owner.get(key)) for key in RECEIPTS],
        'publication_lifecycle': publication_lifecycle(lifecycle),
        'publication_lifecycle_scope': code((lifecycle or {}).get('artifact_scope', 'CURRENT_OWNER_EXPORT')),
        'limitations': [
            'Every observed game is present; unobserved official schedule slots have no invented identity.',
            'An upcoming tip is relative to the evidence snapshot, not the reader current time.',
            'Home and away actual points are copied from source-bound finals; absent per-game errors are not rescored from rounded predictions.',
            'Independent margin and total forecasts do not establish a coherent joint home/away score forecast.',
            'Old selected, former replay, refreshed season-frozen, saved weekly and original-issued evidence remain separate.',
            'Equal game counts do not establish an exact common-game comparison; no full-season best or worst claim is inferred.',
            'Configured workers and synthetic benchmarks do not prove actual concurrent native fits or cache acceptance.',
            'Source publication, hosted validation and website deployment are independently evidenced states.',
        ]}
    if canonical(public) != before:
        fail('ORIGINAL_SELECTED_OUTPUT_CHANGED')
    validate(result)
    return result


def validate(value):
    if value.get('schema') != SCHEMA or value.get('original_issues_modified') is not False:
        fail('SCHEMA_OR_IMMUTABILITY')
    for key in ('publication_new_fits', 'publication_new_inference', 'publication_new_metric_scoring', 'automatic_promotions'):
        if value.get(key) != 0:
            fail('DISPLAY_ONLY_BOUNDARY')
    ids = [row['game_id'] for row in value['game_rows']]
    if len(ids) != len(set(ids)) or len(ids) != value['coverage']['observed_games']:
        fail('GAME_ID_RECONCILIATION')
    body = canonical(value).decode()
    for forbidden in ('recipe_id', 'feature_names', 's3://', '/home/', '/workspace/', 'api_key', 'apiKey', 'PRIVATE KEY'):
        if forbidden in body:
            fail('PRIVATE_FIELD_OR_PATH')
    return True


def render_section(value):
    validate(value)
    embedded = canonical(value).decode().replace('<', '\\u003c')
    return BEGIN + '''
<section id="nba-v9-review" aria-labelledby="nba-v9-title">
<style>#nba-v9-review{margin:24px 0;padding:20px;border:1px solid #bdced5;border-radius:8px;background:#f4f8fb}#nba-v9-review .scroll{overflow:auto;max-height:440px}#nba-v9-review td{overflow-wrap:anywhere}#nba-v9-review summary{cursor:pointer}#nba-v9-review .cards{display:flex;flex-wrap:wrap;gap:12px}#nba-v9-review .card{flex:1 1 180px;min-width:0}#nba-v9-review table{width:100%}#nba-v9-review p{overflow-wrap:anywhere}</style>
<h2 id="nba-v9-title">Complete observed-game coverage and V9 execution evidence</h2>
<p>Evidence snapshot: <strong id="nba-v9-clock"></strong>. Latest authentic original issue: <strong id="nba-v9-issue-clock"></strong>. This is a saved analytical snapshot. Publication itself performs no model fit, inference or metric scoring.</p>
<div id="nba-v9-cards" class="cards"></div>
<p id="nba-v9-denominator"></p>
<p><a href="latest_v9_acceptance.json">Download every observed game, selected original issue, missing role and acceptance state</a> · <a href="#forecast-rows">Inspect all game predictions and original intervals</a></p>
<h3>Old, refreshed and rolling model evidence</h3>
<div class="scroll"><table id="nba-v9-policy"><thead><tr><th>Evidence policy</th><th>Saved metric rows</th><th>Evidence state</th><th>Original issue evidence</th></tr></thead><tbody></tbody></table></div>
<p>Former and selected roles remain in the saved model tables. A newly materialized season-frozen state is retrospective unless a forecast was actually issued before the game. No policy in this panel is automatically promoted.</p>
<details><summary>Saved calibration, distribution scores and actual model clocks</summary><p>ECE fields retain their original binning names. Calibration and prediction-interval coverage are different quantities. Missing clocks remain unavailable; a logical training cutoff never establishes an earlier model materialization time.</p><div class="scroll"><table id="nba-v9-diagnostics"><thead><tr><th>Season / policy / role</th><th>Scored / denominator</th><th>ECE · 10 bins</th><th>ECE · fixed bins</th><th>CRPS</th><th>Weighted interval score</th><th>Logical cutoff</th><th>Actual materialization</th></tr></thead><tbody></tbody></table></div></details>
<h3>Full-season and recent-window qualification</h3>
<p>A best or worst current-season claim requires the exact common completed-game cohort, missing-game reconciliation and uncertainty. Saved subset metrics are available in their own model panels; they do not establish a full-season ranking.</p>
<div class="scroll"><table id="nba-v9-windows"><thead><tr><th>Evidence policy</th><th>Window</th><th>Saved window rows</th><th>Status / ranking qualification</th></tr></thead><tbody></tbody></table></div>
<h3>Actual outcomes, uncertainty and forecast gaps</h3>
<p>Source-bound final scores and original issued intervals are retained. Missing coherent home/away score centers, per-game errors, probability calibration intervals and matched venue evidence remain unavailable. Independent point heads are not combined into a new score forecast; winner contract prices do not establish an expected margin or total.</p>
<details id="nba-v9-game-details"><summary>Observed games and exact missing-role counts</summary>
<label>Game state <select id="nba-v9-game-state"><option value="all">All observed games</option><option value="FINAL">Final</option><option value="LIVE">Live as observed</option><option value="SCHEDULED">Scheduled</option><option value="TBD">Unresolved</option><option value="missing">Missing selected roles</option><option value="future">Future tip at evidence time</option></select></label>
<p id="nba-v9-game-count" aria-live="polite"></p><div class="scroll"><table id="nba-v9-games"><thead><tr><th>Game / teams</th><th>Saved status</th><th>Scheduled start / status clock</th><th>Available / required roles</th><th>Actual home / away points</th><th>Missing targets or qualification</th></tr></thead><tbody></tbody></table></div>
</details>
<h3>Cache, native-fit concurrency and measured throughput</h3>
<p>These cells copy explicit owner receipts. Configured workers, a synthetic fixture or a planned cache are not actual reuse or native-fit measurements. Missing receipts remain unverified; runtime acceptance is not inferred by this renderer.</p>
<div class="scroll"><table id="nba-v9-runtime"><thead><tr><th>Receipt</th><th>Source status</th><th>Saved measured aggregates</th></tr></thead><tbody></tbody></table></div>
<h3>Prepared, committed, merged and deployed</h3>
<p>Recorded artifact scope: <strong id="nba-v9-publication-scope"></strong>. These states refer to that evidence artifact, not a prediction refresh or a later code change. A repository merge and a hosted browser test do not establish a deployed website. The report is a standalone GitHub artifact unless an exact deployment receipt is available.</p>
<div class="scroll"><table id="nba-v9-publication"><thead><tr><th>State</th><th>Verified</th><th>Evidence</th></tr></thead><tbody></tbody></table></div>
<details><summary>Scope and missing-evidence limits</summary><ul id="nba-v9-limits"></ul></details>
<script id="nba-v9-data" type="application/json">''' + embedded + '''</script>
<script>(()=>{'use strict';const R=JSON.parse(document.getElementById('nba-v9-data').textContent),q=id=>document.getElementById(id),e=x=>String(x??'Unavailable').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])),w=x=>String(x??'Unavailable').replaceAll('_',' '),cells=a=>a.map(v=>'<td>'+e(v)+'</td>').join('');
q('nba-v9-clock').textContent=R.evidence_as_of_utc??'Unavailable';q('nba-v9-issue-clock').textContent=R.latest_original_issue_at_utc??'Unavailable';const C=R.coverage;
q('nba-v9-cards').innerHTML=[[C.observed_games,'observed games'],[C.available_current_role_cells+' / '+C.expected_current_role_cells,'selected-role forecast cells'],[C.missing_current_role_cells,'missing selected-role cells'],[C.games_with_source_bound_final_score,'source-bound final scores']].map(([n,l])=>'<div class="card"><strong>'+e(n)+'</strong><p>'+e(l)+'</p></div>').join('');
q('nba-v9-denominator').textContent='Regular-season observed identities: '+C.regular_observed_games+' / '+(C.regular_full_season_denominator??'unverified')+'. Unobserved regular-season slots: '+(C.unobserved_regular_slots??'unverified')+'. Full future schedule complete: '+C.future_full_schedule_complete+'. '+C.future_tips_at_evidence_snapshot+' future tips at the saved evidence time. No identity is invented for an unobserved slot.';
q('nba-v9-policy').tBodies[0].innerHTML=R.model_policy_coverage.map(r=>'<tr>'+cells([w(r.evidence_track),r.saved_metric_rows,w(r.status),r.original_issue_evidence?'Only authenticated pregame issues':'No'])+'</tr>').join('');
q('nba-v9-diagnostics').tBodies[0].innerHTML=R.saved_metric_diagnostics.map(r=>'<tr data-source-index="'+r.source_index+'">'+cells([r.season+' / '+w(r.evidence_track)+' / '+w(r.role_alias),(r.scored_games??'Unavailable')+' / '+(r.completed_game_denominator??'Unavailable'),...['ece_10_bins','ece_10_fixed_bins','crps','weighted_interval_score'].map(k=>typeof r.metrics[k]==='number'?r.metrics[k].toFixed(6):'Unavailable'),r.training_cutoff_utc,r.actual_materialized_at_utc])+'</tr>').join('');
q('nba-v9-windows').tBodies[0].innerHTML=R.window_coverage.map(r=>'<tr>'+cells([w(r.evidence_track),w(r.window),r.saved_metric_rows,w(r.status)+'; '+w(r.ranking_status)])+'</tr>').join('');
function draw(){const filter=q('nba-v9-game-state').value,rows=R.game_rows.filter(r=>filter==='all'||filter==='missing'&&r.missing_current_roles.length>0||filter==='future'&&r.tip_time_relation_at_report==='FUTURE_TIP'||r.last_confirmed_status===filter);q('nba-v9-game-count').textContent=rows.length+' observed games; all matching rows are available in this scrollable table and the complete JSON export.';q('nba-v9-games').tBodies[0].innerHTML=rows.map(r=>'<tr data-game-id="'+e(r.game_id)+'">'+cells([r.game_id+' / '+(r.away_team??'TBD')+' at '+(r.home_team??'TBD'),w(r.last_confirmed_status),(r.scheduled_start_utc??'Unavailable')+' / '+(r.last_confirmed_status_asof_utc??'Unavailable'),r.available_current_roles+' / '+r.expected_current_roles,(r.actual.home_points??'Unavailable')+' / '+(r.actual.away_points??'Unavailable'),[...new Set(r.target_horizon.filter(c=>c.missing_roles>0||c.expected_roles===0).map(c=>c.target+' T'+c.horizon_minutes+': '+w(c.status)))].join('; ')||'All applicable original issues available'])+'</tr>').join('');window.NBA_V9_DISPLAY_STATE={games:rows.length,filter};}
function measured(r){const values=[];function walk(x,prefix){for(const [k,v]of Object.entries(x??{})){if(v&&typeof v==='object')walk(v,prefix+w(k)+' / ');else values.push(prefix+w(k)+': '+(v??'Unavailable'));}}for(const key of ['measurements','native','latest_heartbeat','summary','counts','timings','cache_summary','second_pass','repeat_read_gate','benchmarks','speedups','storage','authenticated_context_cache','verified_file_cache','transport_proof_cache','finalizer_transport_proof_cache','finalizer_verified_file_cache','source_version_refresh'])if(r[key])walk(r[key],key==='measurements'?'':w(key)+' / ');return values.join('; ')||'No saved owner measurement; unverified';}
q('nba-v9-runtime').tBodies[0].innerHTML=R.runtime_receipts.map(r=>'<tr>'+cells([r.section,w(r.status),measured(r)])+'</tr>').join('');
q('nba-v9-publication').tBodies[0].innerHTML=Object.entries(R.publication_lifecycle).filter(([k])=>k!=='source_publication_is_website_deployment').map(([k,v])=>'<tr>'+cells([w(k),v.verified?'Yes':'No',w(v.status)+(v.commit_sha?' / '+v.commit_sha:'')+(v.url?' / '+v.url:'')])+'</tr>').join('');
q('nba-v9-publication-scope').textContent=w(R.publication_lifecycle_scope);
q('nba-v9-limits').innerHTML=R.limitations.map(v=>'<li>'+e(v)+'</li>').join('');q('nba-v9-game-state').addEventListener('change',draw);draw();})();</script>
</section>
''' + END + '\n'


def attach_review(base_html, review):
    clean = re.sub(re.escape(BEGIN) + r'.*?' + re.escape(END) + r'\n?', '', base_html, flags=re.S)
    if clean.count('</main>') != 1:
        fail('UNIQUE_MAIN_INSERTION_POINT_REQUIRED')
    return clean.replace('</main>', render_section(review) + '</main>', 1)


def publication_payloads(public, owner, model_review, base_html, lifecycle=None):
    review = build_v9_review(public, owner, model_review, lifecycle)
    return {PUBLIC_FILENAME: canonical(review) + b'\n',
            'latest_research_outputs.html': attach_review(base_html, review).encode()}, {
                'schema': SCHEMA, 'observed_games': review['coverage']['observed_games'],
                'original_selected_json_sha256': review['selected_output_sha256'],
                'new_fits': 0, 'new_inference': 0, 'new_metric_scoring': 0,
                'original_issue_clocks_modified': False}
