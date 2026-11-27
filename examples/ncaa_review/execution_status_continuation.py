"""Validate public continuation evidence without granting owner-run credit.

This aggregate-only schema separates an actual failed owner invocation, isolated
engineering recovery, and a bounded authentic scientific fitting catalog.
"""
from copy import deepcopy
from datetime import datetime
import json
import math
import re


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _numbers(values, *, integer=False):
    return all(type(x) is int and x >= 0 if integer else
               type(x) in (int, float) and math.isfinite(x) and x >= 0 for x in values)


def _pin(value):
    return (isinstance(value, dict) and set(value) == {'bytes', 'sha256'}
            and type(value['bytes']) is int and value['bytes'] > 0
            and isinstance(value['sha256'], str) and re.fullmatch('[0-9a-f]{64}', value['sha256']))


def validate_continuation_v7(data, prior, *, top_keys, current_keys, forbidden, cost_basis):
    extra = {'audit_scope', 'source_recovery_evidence', 'source_task_reconciliation',
             'offline_source_recovery_acceptance', 'bounded_scientific_acceptance', 'next_preparation',
             'stage_resumption_acceptance'}
    _require(set(data) == top_keys | extra, 'Unexpected continuation execution fields')
    _require(data['owner'] == 'NCAA basketball' and not forbidden.search(json.dumps(data, allow_nan=False)),
             'Private or other-owner content')
    observed_at = datetime.fromisoformat(data['observed_at'])
    _require(observed_at.tzinfo is not None, 'Timezone-aware evidence clock required')
    publication = data['publication']
    _require(set(publication) == set(prior['publication'])
             and publication['source_state'] in {'PREPARED', 'COMMITTED'}
             and publication['deployment_verified'] is False
             and all(publication[k] == 0 for k in ('owner_runs', 'new_fits', 'new_forecasts', 'provider_requests')),
             'Publishing a dashboard does not fit models, run research or deploy a site')
    observed, verified = data['latest_observed_attempt'], data['latest_verified_return']
    _require(set(observed) == set(prior['latest_observed_attempt']) and observed['release'] == 'R31'
             and observed['status'] == 'FAILED_RESUMABLE' and observed['return_published'] is True
             and observed['evidence_class'] == 'FULL_ARCHIVE_VERIFIED'
             and set(verified) == set(prior['latest_verified_return']) and verified['release'] == 'R31'
             and verified['integrity'] == 'FULL_ARCHIVE_VERIFIED' and verified['payloads_verified'] == 222
             and verified['sha256'] == '82d55450655d8017074b6689adcd38a455207930992af232cbf78d12ac11f28d',
             'The actual R31 failure needs its own exact verified partial return')
    rows = data['attempts']
    _require(isinstance(rows, list) and rows[:-1] == prior['attempts']
             and len({r['id'] for r in rows}) == len(rows), 'Preserve every earlier audited owner attempt')
    last = rows[-1]
    _require(set(last) == set(prior['attempts'][-1]) and last['id'] == 'r31' and last['release'] == 'R31'
             and last['outcome'] == 'FAILED_RESUMABLE' and last['phase'] == 'BEFORE_FIT'
             and last['return_published'] is True, 'R31 did not become a completed owner campaign')
    scope = data['audit_scope']
    _require(set(scope) == set(prior['audit_scope']) and scope['audited_attempts'] == len(rows) == 12
             and scope['distinct_run_ids'] == 10 and scope['completed_campaigns'] == 0,
             'Bounded acceptance is separate from owner-attempt and completed-campaign counts')
    c = data['current_execution']
    _require(set(c) == current_keys | {'failure', 'historical_checkpoint_reuses'}
             and c['release'] == 'R31' and c['phase'] == 'BEFORE_FIT' and c['return_published'] is True
             and c['scientific_gate'] == 'PENDING_REAL_ELIGIBLE_WORK' and c['scientific_gate_executed'] is False
             and c['cost_basis'] == cost_basis and c['pressure_reason'] == 'IO_MEMORY_POOL_LANES_BUSY'
             and c['pressure_wait_seconds'] == 16.428095466006198, 'R31 stopped before scientific dispatch')
    counters = ('recorded_stages_completed', 'requested_workers', 'peak_scientific_workers', 'maximum_ready_depth',
                'new_target_fits', 'new_calibration_fits', 'new_residual_fits', 'verified_reused_target_fits',
                'historical_checkpoint_reuses', 'fresh_startup_tests', 'reused_startup_tests', 'cache_reads',
                'cache_bytes', 'fresh_storage_reads', 'fresh_storage_bytes')
    _require(_numbers([c[k] for k in counters], integer=True), 'Counters need nonnegative integers')
    _require(all(c[k] == 0 for k in ('peak_scientific_workers', 'maximum_ready_depth', 'new_target_fits',
             'new_calibration_fits', 'new_residual_fits', 'verified_reused_target_fits', 'fresh_startup_tests'))
             and c['historical_checkpoint_reuses'] == 108 and c['reused_startup_tests'] == 1284
             and c['requested_workers'] == 24 and c['recorded_stages_completed'] == 4
             and all(c[k] == last[k] for k in ('fresh_startup_tests', 'reused_startup_tests', 'new_target_fits',
                                              'historical_checkpoint_reuses'))
             and c['owner_elapsed_seconds'] == last['elapsed_seconds'], 'Historical reuse is not new or current-consumer fitting')
    _require(_numbers([c[k] for k in ('startup_seconds', 'owner_elapsed_seconds', 'parent_cpu_seconds',
             'completed_child_cpu_seconds', 'estimated_instance_wall_cost_usd')]) and c['completed_child_cpu_seconds'] == 0,
             'R31 recorded finite measurements and zero completed-child fitting CPU')
    clocks = [datetime.fromisoformat(c[k]) for k in ('started_at', 'completed_at')]
    _require(all(t.tzinfo is not None for t in clocks) and clocks[0] <= clocks[1] <= observed_at,
             'R31 clocks must remain ordered and timezone-aware')
    expected_failure = deepcopy(prior['current_execution']['failure'])
    expected_failure.update(recorded_error='V7_IO_DEFERRAL_ALREADY_LATCHED',
        classification='OWN_PENDING_IO_TOKEN_WAIT_LATCHED_AS_GLOBAL_STORAGE_FATAL',
        diagnosis_status='RECORDED_LATCH_AND_CONTROLLED_OLD_CODE_REPLAY_VERIFIED')
    _require(c['failure'] == expected_failure, 'R31 admission failure cannot inherit the R30 clock diagnosis')
    e = data['source_recovery_evidence']
    _require(set(e) == set(prior['clock_recovery_evidence']), 'Unexpected source recovery measurements')
    numeric = set(e) - {'recorded_source_refresh_complete', 'price_verification_succeeded', 'note'}
    _require(_numbers([e[k] for k in numeric]) and e['historical_checkpoints_verified'] == 108
             and e['current_consumer_target_reuses'] == 0 and e['recorded_source_refresh_complete'] is False
             and e['useful_scientific_worker_cores'] == 0 and e['price_verification_succeeded'] is True
             and 0 < e['owner_mean_cores_independent_sampler'] <= e['owner_peak_cores_independent_sampler'] < 12
             and 0 < e['owner_peak_cores_performance_ledger'] < 12
             and 0 < e['independent_measurement_seconds'] <= c['owner_elapsed_seconds']
             and 0 < e['estimated_cost_wall_seconds'] <= c['owner_elapsed_seconds'] and e['rate_usd_per_hour'] > 0
             and math.isclose(c['estimated_instance_wall_cost_usd'],
                 e['estimated_cost_wall_seconds'] * e['rate_usd_per_hour'] / 3600, abs_tol=1e-6),
             'Measured owner recovery CPU, costs and zero scientific workers have different scopes')
    source = data['source_task_reconciliation']
    _require(source == {'ancestor_receipts_not_counted_as_current_tasks': 2, 'authenticated_committed_responses': 6,
        'authenticated_pending_captured_responses': 1, 'committed_responses_missing_local_marker': 2,
        'displayed_completed': 4, 'displayed_remaining': 28, 'distinct_response_tasks_proven_recoverable': 7,
        'fresh_current_snapshot_credit_from_dated_reuse': 0, 'original_clocks_preserved': True,
        'planned': 32, 'remaining_without_R31_response_proof': 25},
        'Displayed task progress overlaps committed and pending response receipts')
    offline = data['offline_source_recovery_acceptance']
    exact_offline = {'additional_pending_capture_published_in_local_test':1,'committed_tasks_recovered':6,
        'corrupt_authentic_pending_spool_rejected':True,'corrupt_normalized_result_rejected':True,
        'current_AWS_objects_written':0,'duplicate_raw_publications_for_committed_tasks':0,
        'local_timings_are_not_AWS_research_throughput':True,'new_observation_partitions_completed':1,
        'owner_campaigns':0,'prior_observation_partitions_reused':2,'provider_requests':0,'scientific_fits':0,
        'scope':'AUTHENTIC_PRESERVED_INPUTS_IN_ISOLATED_MEMORY_STORAGE_AND_TEMPORARY_LOCAL_SPOOL',
        'warm_normalized_tasks_reused':6,'warm_normalizer_invocations':0}
    _require(set(offline) == set(exact_offline) | {'acceptance_report_sha256','local_cold_seconds','local_warm_seconds'}
             and all(offline[k] == v and type(offline[k]) is type(v) for k,v in exact_offline.items())
             and re.fullmatch('[0-9a-f]{64}', str(offline['acceptance_report_sha256']))
             and _numbers([offline['local_cold_seconds'], offline['local_warm_seconds']]),
             'Isolated source replay did not refetch providers or publish real remote objects')
    restart = data['stage_resumption_acceptance']
    _require(set(restart) == {'scope','status','engineering_tests','engineering_failures','report_sha256',
        'stage11_restart','actual_runner_fixture','mid_stage_restart','changed_input','corruption_rejected',
        'owner_campaigns','new_scientific_fits','authentic_owner_stage_adoption_status','authentic_native_recovery'}
        and restart['scope'] == 'ISOLATED_ENGINEERING_RESTART_FIXTURES' and restart['status'] == 'PASS'
        and restart['engineering_tests'] == 95 and restart['engineering_failures'] == 0
        and re.fullmatch('[0-9a-f]{64}', str(restart['report_sha256']))
        and restart['stage11_restart'] == {'completed_stages_reused':10,'new_stages_completed':1,'invalidated_stages':0,'repeated_prior_callbacks':0}
        and restart['actual_runner_fixture'] == {'completed_stages_reused':14,'new_stages_completed':0,'invalidated_stages':0,'deliberately_reinterrupted_stage11':True}
        and restart['mid_stage_restart'] == {'completed_tasks_reused':2,'new_tasks_completed':1,'pending_tasks':0}
        and restart['changed_input'] == {'source_and_dependent_stages_invalidated':2,'independent_stages_reused':1}
        and restart['corruption_rejected'] is True and restart['owner_campaigns'] == 0 and restart['new_scientific_fits'] == 0
        and restart['authentic_owner_stage_adoption_status'] == 'SEPARATELY_VERIFIED_NATIVE_RECOVERY',
        'Restart engineering is not authentic owner-stage completion or scientific fitting')
    native=restart['authentic_native_recovery']
    native_expected={'status':'VERIFIED_AUTHENTIC_R31_THREE_STAGE_COLD_ADOPTION_AND_WARM_RESTART',
        'report_sha256':'ad2416584c31d135ffa84c4c1fdba258b50a8ba00cdd233b5cad1e73ae07b1f4',
        'completed_stages_reused':3,'new_stages_completed':0,'invalidated_completed_stages':0,
        'repeated_compute_callbacks':0,'historical_estimator_checkpoints_preserved':108,'prediction_rows_preserved':806688,
        'verified_local_object_reuses':28,'remote_receipt_reads':3,'remote_receipt_bytes':19449,
        'warm_restart_seconds':10.380767031994765,'provider_requests':0,'owner_campaigns':0,
        'new_estimator_fits':0,'new_calibration_fits':0}
    _require(native==native_expected,'Authentic stage resumption preserves prior work without refitting')
    a = data['bounded_scientific_acceptance']
    exact = {'status':'COMPLETED_FINITE_ACCEPTANCE_CATALOG','scope':'SEPARATE_FROM_OWNER_CAMPAIGN',
        'report_sha256':'3c83b5dafdd18661fce17e5fecbc1af75d6a1ba54e7225203540cd26f324b9a9',
        'owner_campaigns':0,'full_research_campaign_complete':False,'champion_promotions':0,'provider_requests':0,
        'test_rows_used':0,'synthetic_workload_used':False,'requested_worker_hard_ceiling':36,'normal_minimum_target':12,
        'native_threads_per_process':1,'planned_tasks':36,'verified_tasks_completed':36,'new_physical_fits_completed':36,
        'reused_completed_tasks':0,'failed_tasks':0,'remaining_tasks':0,'verified_output_checkpoints':36,
        'family_counts':{'hist_gradient_boosting':12,'extra_trees':12,'xgboost':12},
        'prior_linear_components_verified_unchanged':11,'historical_checkpoint_reuses_separate':108,
        'peak_real_estimator_kernel_overlap':21,'peak_worker_processes':22,
        'kernel_measurement_scope':'REGISTERED_PREPROCESSING_FIT_INFERENCE_AND_LOCAL_PERSISTENCE_NOT_OPTIMIZER_ONLY',
        'cost_basis':cost_basis,'occupancy_gate_status':'CONDITIONAL_INSUFFICIENT_INDEPENDENT_FIT_WORK',
        'sustained_180_second_75_percent_gate_certified':False,
        'overlap_of_at_least_12_real_estimator_kernels_observed':True,
        'overlap_of_24_or_36_real_estimator_kernels_observed':False}
    measured = {'peak_sampled_owner_core_equivalents','kernel_cpu_seconds','kernel_measurement_span_seconds',
        'kernel_average_core_equivalents','wall_seconds','estimated_full_instance_wall_cost_usd','verified_rate_usd_per_hour'}
    _require(set(a) == set(exact) | measured | {'started_at','completed_at','limiting_factor','note'}
             and all(a[k] == v and type(a[k]) is type(v) for k,v in exact.items())
             and _numbers([a[k] for k in measured]) and 12 <= a['peak_sampled_owner_core_equivalents'] < 36
             and 0 < a['kernel_measurement_span_seconds'] <= a['wall_seconds']
             and math.isclose(a['kernel_average_core_equivalents'], a['kernel_cpu_seconds']/a['kernel_measurement_span_seconds'], abs_tol=1e-6)
             and math.isclose(a['estimated_full_instance_wall_cost_usd'], a['wall_seconds']*a['verified_rate_usd_per_hour']/3600, abs_tol=1e-6)
             and isinstance(a['limiting_factor'], str) and len(a['limiting_factor']) > 40,
             'Actual bounded fits, observed overlap and the uncertified sustained gate must remain distinct')
    fit_clocks = [datetime.fromisoformat(a[k].replace('Z','+00:00')) for k in ('started_at','completed_at')]
    _require(all(t.tzinfo is not None for t in fit_clocks) and clocks[1] < fit_clocks[0] < fit_clocks[1] <= observed_at,
             'Bounded acceptance happened after the failed owner invocation')
    p = data['preserved_work']
    _require(set(p) == set(prior['preserved_work']) and p['duplicate_fits_proven'] is False
             and p['all_repeated_work_eliminated'] is False
             and p['new_target_fits_in_audited_attempts'] == sum(r['new_target_fits'] or 0 for r in rows) == 11,
             'Do not add historical checkpoint accesses or separate bounded fits to owner-attempt totals')
    _require(data['science_contract'] == prior['science_contract'], 'V13 scientific and exposure constraints remain intact')
    _require({k:v for k,v in data['throughput'].items() if k not in {'note','next_run_rule'}}
             == {k:v for k,v in prior['throughput'].items() if k not in {'note','next_run_rule'}},
             'Historical failed throughput remains dated evidence')
    n = data['next_preparation']
    _require(set(n) == set(prior['next_preparation']) and n['release'] == 'R32'
             and n['status'] in {'IN_PROGRESS','PREPARED_VERIFIED'} and n['owner_executions'] == 0
             and n['science_completion_claimed'] is False and len(n['stages']) == 4
             and all(set(s) == {'name','status'} for s in n['stages']),
             'R32 release preparation is separate from bounded acceptance and owner research')
    if n['status'] == 'IN_PROGRESS':
        _require(n['canonical_gate_passed'] is False and n['upload_verified'] is False
                 and all(n[k] is None for k in ('engineering_tests','engineering_failures','engineering_evidence_sha256','verified_delivery'))
                 and all(s['status'] == 'IN_PROGRESS' for s in n['stages']),
                 'Final canonical verification and installation must not inherit prior success')
    else:
        delivery=n['verified_delivery']; pins={'canonical_source','engineering_gate','installation_receipt','ready_receipt'}
        _require(n['canonical_gate_passed'] is True and n['upload_verified'] is True
                 and type(n['engineering_tests']) is int and n['engineering_tests'] > 0 and n['engineering_failures'] == 0
                 and isinstance(delivery,dict) and set(delivery) == pins | {'installed_at','startup_cases_reused','startup_cases_executed','owner_executions','new_scientific_fits'}
                 and all(_pin(delivery[k]) for k in pins)
                 and delivery['engineering_gate']['sha256'] == n['engineering_evidence_sha256']
                 and all(delivery[k]['sha256'] != prior['next_preparation']['verified_delivery'][k]['sha256']
                         for k in ('canonical_source','engineering_gate'))
                 and delivery['canonical_source']['sha256'] != '9ae3d267c1be2809c5097b7152a0abf341a68c68511d84cf34428b37999be561'
                 and delivery['canonical_source']['sha256'] != 'c047f770885e9c654ed50eefd221a74f09f3bde03b4631b8d6b6e3c3b052fc3b'
                 and delivery['owner_executions'] == 0 and delivery['new_scientific_fits'] == 0
                 and _numbers([delivery['startup_cases_reused'],delivery['startup_cases_executed']], integer=True)
                 and all(s['status'] == 'IMPLEMENTED_OWNER_EXECUTION_PENDING' for s in n['stages']),
                 'R32 needs its own completed final gate and verified installation; neither creates the 36 separate fits')
        _require(datetime.fromisoformat(delivery['installed_at']).tzinfo is not None,
                 'Verified installation retains its own timezone-aware clock')
    for record in data['evidence']:
        _require(set(record) == {'label','scope','sha256'} and re.fullmatch('[0-9a-f]{64}', str(record['sha256'])),
                 'Only scoped public evidence digests may be published')
    return deepcopy(data)
