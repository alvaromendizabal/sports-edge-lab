#!/usr/bin/env python3
"""Render sanitized NBA recovery evidence; no science, providers or deployment."""
from __future__ import annotations
import argparse
import base64
import copy
import html
import json
import math
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
SOURCE = HERE / 'b105_execution_status.json'
OUTPUT = HERE / 'b105_execution_status.html'
STYLE = '\n:root{color-scheme:light;--ink:#172f3a;--muted:#536771;--line:#d1dfdd;--paper:#f2f5f1;--teal:#0c655b;--amber:#875015}*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--paper);color:var(--ink);font:16px/1.6 system-ui,sans-serif}a{color:var(--teal);text-underline-offset:.18em}a:focus-visible,summary:focus-visible{outline:3px solid #e6a641;outline-offset:4px}main{width:min(1120px,100%);padding:42px 28px 62px;margin:auto}header{border-top:5px solid var(--teal);padding-top:24px}.eyebrow{font-size:.76rem;letter-spacing:.14em;font-weight:800;color:var(--teal)}h1{max-width:900px;font-size:clamp(2.2rem,5vw,3.5rem);line-height:1.08;letter-spacing:-.045em;margin:18px 0}h2{font-size:1.6rem;letter-spacing:-.025em;line-height:1.2;margin:0 0 15px}h3{font-size:1rem;margin:0 0 6px}p{margin:10px 0 16px}.lead{font-size:1.12rem;max-width:900px;color:#36505a}.meta,.muted{font-size:.88rem;color:var(--muted)}nav{display:flex;flex-wrap:wrap;gap:10px 22px;margin:25px 0 28px}nav a{font-weight:650}.notice{padding:18px 20px;background:#fff3df;border-left:5px solid var(--amber);margin:22px 0}.cards{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;margin:24px 0}.card{padding:19px;background:white;border:1px solid var(--line);border-radius:8px;min-width:0}.number{font-size:2rem;font-weight:780;letter-spacing:-.035em;line-height:1.15}.caption{font-size:.86rem;color:var(--muted);margin-top:9px}section{background:white;border:1px solid var(--line);border-radius:10px;margin:18px 0;padding:27px;scroll-margin-top:18px}.badge{display:inline-block;font-size:.72rem;font-weight:800;letter-spacing:.05em;padding:4px 10px;border-radius:99px;margin-bottom:13px;background:#e2efe9;color:var(--teal)}.badge.pending{background:#fff0d0;color:var(--amber)}.columns{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:24px}.columns>*{min-width:0}.metric{font-size:1.9rem;font-weight:770;letter-spacing:-.04em}.note{padding:14px 17px;background:#eef4f0;border-radius:6px}.progress-row{border-top:1px solid var(--line);padding:17px 0}.progress-head{display:flex;justify-content:space-between;gap:12px}.progress-head strong{font-size:1.1rem}.progress-row progress{display:block;width:100%;height:14px;accent-color:var(--teal);margin:10px 0}.progress-row p{margin:0;font-size:.9rem;color:var(--muted)}.policy{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;margin:20px 0}.policy div{padding:17px;background:#eff5f1;border-radius:7px;min-width:0}.policy strong{display:block;font-size:1.7rem;line-height:1.15}.policy span{font-size:.84rem;color:var(--muted)}.identity{border-top:1px solid var(--line);padding:14px 0;display:grid;gap:5px}.identity span{font-size:.85rem}.identity code{font-size:.74rem;overflow-wrap:anywhere}.table-wrap{width:100%;margin:18px 0}table{width:100%;border-collapse:collapse;text-align:left;font-size:.91rem}caption{text-align:left;font-weight:700;margin-bottom:10px}th,td{padding:12px 10px;border-bottom:1px solid var(--line);vertical-align:top}thead th{color:var(--muted);font-size:.8rem;letter-spacing:.03em}.requirements{list-style:none;margin:20px 0 0;padding:0}.requirements li{border-top:1px solid var(--line);padding:17px 0}.requirements li div{display:flex;align-items:baseline;justify-content:space-between;gap:12px}.state{font-size:.72rem;text-transform:uppercase;letter-spacing:.03em;color:var(--amber)}.requirements p{margin:6px 0 0;color:var(--muted);font-size:.93rem}.sources{list-style:none;padding:0}.sources li{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:4px 15px;border-top:1px solid var(--line);padding:13px 0;font-size:.88rem}.sources code{grid-column:1/-1;overflow-wrap:anywhere;color:var(--muted);font-size:.74rem}.download{display:inline-block;color:white;background:var(--teal);padding:11px 18px;border-radius:6px;font-weight:750;text-decoration:none;margin:12px 0}details{border-top:1px solid var(--line);padding-top:14px;margin-top:18px}summary{cursor:pointer;font-weight:700}code,#prepared-status,.notice strong,.note strong{overflow-wrap:anywhere}footer{padding-top:18px;font-size:.87rem;color:var(--muted)}@media(max-width:650px){main{padding:24px 18px 44px}section{padding:20px}.cards{grid-template-columns:repeat(2,minmax(0,1fr))}.number{font-size:1.7rem}.columns,.policy{grid-template-columns:1fr;gap:12px}.policy div{display:flex;align-items:baseline;gap:15px}.policy strong{min-width:2.2rem}.lead{font-size:1.02rem}.progress-head,.requirements li div{display:block}.progress-head>span{display:block;margin-top:3px}caption{display:block;width:100%}.state{display:block;margin-top:4px}.sources li{grid-template-columns:1fr}.sources span{font-size:.8rem}table,thead,tbody,tr,th,td{display:block}thead{display:none}tr{border-top:1px solid var(--line);padding:10px 0}td,th{border:0;padding:5px 0}td::before{content:attr(data-label) ": ";font-weight:650}tbody th{font-size:1rem}.metric{font-size:1.65rem}}@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}}\n'


def valid_pin(value):
    return (isinstance(value, dict) and set(value) == {'bytes', 'sha256'}
        and type(value['bytes']) is int and value['bytes'] > 0
        and re.fullmatch('[0-9a-f]{64}', str(value['sha256'])) is not None)


def validate(data):
    expected_keys = {'schema', 'owner', 'observed_date_utc', 'actual_B104', 'incident',
        'cpu', 'B105_preparation', 'native_verification', 'recovered_frozen_test', 'owner_request', 'comparison', 'point_comparison', 'repair_scope',
        'requirements_still_open', 'publication', 'evidence'}
    if set(data) != expected_keys or data['owner'] != 'NBA' or data['schema'] != 'sel.nba.public_execution_status.b105.v1':
        raise ValueError('Only the scoped NBA aggregate schema is allowed')
    actual = data['actual_B104']
    required = {'owner_executions_observed': 1, 'execution_complete': False,
        'full_v13_complete': False, 'verified_final_return_published': False,
        'owner_exact_exit_code': None, 'owner_exact_signal': None,
        'registered_fit_tasks': 240, 'successful_model_recipes': 225,
        'new_estimator_fits': 201, 'new_calibration_fits': 201,
        'reused_estimator_fits': 24, 'reused_calibration_fits': 24,
        'failed_model_recipes': 15, 'pytorch_interop_failures': 13,
        'tensorflow_serialization_parity_failures': 2, 'context_tasks_reused': 30,
        'validation_tasks': 225, 'validation_scored_variants': 450,
        'new_validation_ledgers': 402, 'reused_validation_ledgers': 48,
        'current_run_s3_box_frozen_test_task_receipts': 0, 'reused_original_distribution_fits': 320,
        'new_residual_distribution_fits': 0, 'registry_bodies_verified': 975,
        'native_artifact_references_verified': 6291, 'unique_content_hashes': 5607,
        'actual_invoiced_usd': None, 'nba_allocated_cost_usd': None,
        'unique_s3_payloads_full_get_sha_verified': 5607, 'unique_s3_payload_bytes_verified': 2683086355,
        's3_payload_missing': 0, 's3_payload_unknown': 0, 's3_payload_mismatches': 0}
    if actual != required:
        raise ValueError('Preserve audited successes, failures, reuse and unknown owner exit status')
    recovered = data['recovered_frozen_test']
    if (recovered['local_verified_base_results'] != 46 or recovered['local_verified_prediction_ledgers'] != 92
            or recovered['earlier_cached_base_results'] != 24 or recovered['new_B104_base_inference_results'] != 22
            or recovered['B104_local_completion_records'] != 23
            or recovered['B104_new_prediction_ledgers'] != 44 or recovered['B104_reused_prediction_ledgers'] != 2
            or recovered['completed_game_rows'] != 210 or recovered['forecast_population_rows'] != 1200
            or recovered['remaining_original_225_base_test_inferences_at_most'] != 179
            or recovered['additional_failed_neural_replacements_at_most'] != 15
            or recovered['identity_hash_schema_and_population_verified'] is not True
            or recovered['all_four_new_total_leaders_test_pending'] is not True
            or recovered['audit_new_fits'] != 0 or recovered['audit_new_predictions'] != 0
            or recovered['frozen_test_stage_complete']):
        raise ValueError('Recovered local test results are distinct from missing registry closures and remaining work')
    backup = recovered['immutable_backup']
    if (backup['status'] not in ('PENDING','FULL_GET_SHA_VERIFIED')
            or backup['source_payload_files'] != 161 or backup['source_payload_bytes'] != 14719711
            or backup['canonical_owner_pointer_writes'] != 0
            or (backup['status'] == 'PENDING' and backup['verification_evidence'] is not None)
            or (backup['status'] == 'FULL_GET_SHA_VERIFIED' and not valid_pin(backup['verification_evidence']))):
        raise ValueError('Local output verification and immutable remote backup need separate evidence')
    inc = data['incident']
    if (inc['selection_lock_bytes'] != 1141248706 or inc['frozen_test_workers_admitted'] != 36
            or inc['oom_kill_before'] != 0 or inc['oom_kill_after'] != 15
            or inc['identified_frozen_test_workers_sigkilled'] != 13
            or inc['owner_oom_victim_attribution'] != 'INFERENCE_EXACT_OWNER_EXIT_STATUS_UNAVAILABLE'
            or inc['fixed_180_second_timeout_established'] or inc['lightgbm_fit_failure_caused_incident']
            or inc['root_cgroup_peak_bytes'] != 97784340480 or inc['host_physical_memory_bytes'] != 99615150080):
        raise ValueError('Observed memory mechanism does not supply the missing owner exit signal')
    cpu = data['cpu']
    if (not math.isclose(cpu['base_fit_peak_measured_cores'], 32.2775324707236)
            or not math.isclose(cpu['validation_peak_measured_cores'], 29.44683110253298)
            or cpu['base_fit_active_workers_at_peak'] != 35 or cpu['validation_active_workers_at_peak'] != 32
            or cpu['sustained_180_second_occupancy_gate'] != 'NOT_ESTABLISHED_FROM_PEAK_SAMPLES'
            or cpu['peak_is_sustained_acceptance'] or cpu['configured_workers_are_measured_busy_cores']):
        raise ValueError('Real peak CPU and sustained scientific acceptance are separate')
    if data['owner_request'] != {'normal_scientific_worker_target': 12, 'requested_cores': 36,
        'explicit_max_workers': 36, 'native_threads_per_independent_fit': 1,
        'safe_shared_capacity_required': True, 'compute_guard_usd': 200,
        'wall_minutes': 0, 'wall_zero_waives_cost_guard': False}:
        raise ValueError('Retain shared-resource admission, explicit worker ceiling and cost guard')
    prep = data['B105_preparation']
    allowed = {'PREPARATION_IN_PROGRESS', 'BUILD_TESTED', 'VERIFIED_DELIVERY_NATIVE_PENDING',
        'DELIVERY_AND_NATIVE_INSTALL_VERIFIED'}
    if prep['status'] not in allowed:
        raise ValueError('Unsupported preparation status')
    if any(prep[x] != 0 for x in ('new_owner_executions', 'new_estimator_fits',
            'new_calibration_fits', 'new_residual_distribution_fits')) or prep['full_v13_complete']:
        raise ValueError('Preparing B105 is not owner science')
    for field in ('canonical_executable', 'verification_evidence', 'engineering_evidence'):
        if prep[field] is not None and not valid_pin(prep[field]):
            raise ValueError('Prepared evidence needs exact byte and SHA256 pins')
    if prep['delivery_full_body_readback_verified']:
        if (prep['status'] not in {'VERIFIED_DELIVERY_NATIVE_PENDING', 'DELIVERY_AND_NATIVE_INSTALL_VERIFIED'}
                or prep['canonical_executable'] is None or prep['verification_evidence'] is None):
            raise ValueError('Private delivery requires its own complete-byte proof')
    elif prep['status'].startswith(('VERIFIED_DELIVERY', 'DELIVERY_AND')) or prep['verification_evidence'] is not None:
        raise ValueError('Do not claim unverified delivery')
    if prep['native_installation_verified'] != (prep['status'] == 'DELIVERY_AND_NATIVE_INSTALL_VERIFIED'):
        raise ValueError('Native installation requires explicit verified status')
    native = data['native_verification']
    if (native['scope'] != 'BOUNDED_EXISTING_MODEL_APPLICATION_AND_ISOLATED_PUBLICATION'
            or native['status'] != 'PASS_REPRESENTATIVE_ENGINEERING_CHECKS'
            or native['selected_existing_models'] != 12 or native['completed_existing_model_tasks'] != 12
            or native['engineering_fixture_optimizer_calls'] != 4
            or native['frozen_test_inference_calls'] != 12 or native['model_states_preserved'] != 225
            or native['worker_rss_peak_bytes'] != 4889866240
            or any(native[x] != 0 for x in ('failed_tasks','missing_tasks','new_owner_scientific_fits',
                'new_owner_calibration_fits','owner_research_executions','warm_repeat_inference_calls'))
            or native['sustained_180_second_75_percent_gate'] != 'NOT_EVALUATED_SHORT_WORKLOAD'
            or native['worker_count_is_measured_core_count'] or native['full_research_run_launched'] or native['full_v13_complete']):
        raise ValueError('Bounded native proof does not establish sustained cores or owner campaign completion')
    archive_test = native['archive_self_test']
    if (archive_test['result'] != 'PASS' or archive_test['tests_run'] != 60
            or archive_test['failures'] != 0 or archive_test['errors'] != 0
            or archive_test['owner_research_executions'] != 0
            or archive_test['includes_full_pyarrow_point_replay_case'] is not True
            or not valid_pin(archive_test['executable_pin'])
            or archive_test['executable_pin'] != prep['canonical_executable']):
        raise ValueError('Native archive checks must bind the exact prepared executable and remain separate from science')
    ready = native['launch_readiness']
    if (ready['status'] != 'READY_FOR_OWNER_LAUNCH' or ready['successful_gates'] != 9
            or ready['failed_gates'] != 0 or ready['not_run_gates'] != 0
            or ready['owner_research_dispatches'] != 0 or ready['owner_execution_started']
            or ready['must_resolve_latest_checkpoint_again_at_owner_launch'] is not True):
        raise ValueError('Read-only launch readiness is distinct from execution and must be rechecked at launch')
    phases = native['phase_measurements']
    if len(phases) != 3 or {r['phase'] for r in phases} != {
        'FROZEN_TEST_AUTHORIZED_INFERENCE','HISTORICAL_CALIBRATION_SERIALIZATION_PARITY','VALIDATION_REPLAY_COMPARE_WITH_B104'}:
        raise ValueError('Retain all three independently measured application phases')
    for phase in phases:
        if (phase['actual_operations'] != 12 or phase['distinct_worker_pids'] != 12
                or phase['peak_overlapping_real_native_prediction_calls'] != 12
                or phase['all_observed_native_pools_one_thread'] is not True
                or not 0 < phase['native_call_window_seconds'] < 1
                or not 0 < phase['measured_average_cores_during_call_window'] < 12
                or not math.isclose(phase['measured_average_cores_during_call_window'],
                    phase['sum_native_process_cpu_seconds']/phase['native_call_window_seconds'],rel_tol=1e-12)):
            raise ValueError('Twelve overlapping workers are distinct from measured CPU and window length')
    if native['real_s3_publication'] != {'status':'PASS','isolated_child_cases':3,
        'case_types':['EXIT_2_WITHOUT_FINAL_RETURN','OWNED_CHILD_SIGKILL','NORMAL_VERIFIED_PARTIAL_RETURN'],
        'full_get_sha_verified_objects':35,'canonical_owner_pointer_writes':0,
        'owner_research_executions':0,'scientific_fits':0,'namespace_isolated':True,
        'S3_responses_mocked':False,'normal_partial_duplicate_abnormal_return':False}:
        raise ValueError('The real-S3 publication fixture must stay isolated and distinct from science')
    c = data['comparison']
    if (c['scope'] != '320_PRESERVED_DISTRIBUTION_HEAD_REPLAYS_ONLY'
            or c['evaluation_rows'] != [1321, 1322, 210] or c['historical_B100_rows'] != [1314, 1315, 210]
            or not c['same_manifest_membership_verified_for_320_heads'] or not c['original_state_pins_unchanged']
            or c['missing_predictions_in_these_cohorts'] != 0
            or c['fresh_all_completed_test_census_verified'] or c['independent_full_season_census_verified']
            or c['same_population_all_contenders_complete'] or c['full_season_champions_qualified']
            or c['test_outcomes_select_models'] or not c['prior_test_exposure_preserved']
            or c['sensitivity_changes_fit_or_predictions'] or c['primary_weights'] != [.5, .5]
            or c['selection_ratios'] != [[.5,.5],[.4,.6],[.3,.7],[.2,.8],[.1,.9]]
            or c['metric'] != 'CRPS' or not c['lower_is_better'] or len(c['rows']) != 4):
        raise ValueError('Preserved-head comparison does not complete the all-contender census')
    for row in c['rows']:
        if (row['candidates_in_role'] != 80 or row['horizon_minutes'] not in (60, 120)
                or row['target'] not in ('margin', 'total') or row['method'] != 'gaussian'
                or row['distinct_sensitivity_leaders'] != (1 if row['target'] == 'margin' else 3)
                or not all(math.isfinite(row[k]) and row[k] > 0 for k in
                    ('crps_2024', 'crps_2025', 'crps_2026', 'validation_50_50'))
                or not math.isclose(row['validation_50_50'], (row['crps_2024'] + row['crps_2025']) / 2)):
            raise ValueError('CRPS values retain validation-only aggregation and honest role scope')
    point = data['point_comparison']
    if (point['scope'] != 'PRESERVED_BASELINE_AND_B104_BOX_VALIDATION'
            or point['baseline_variants'] != 5808 or point['box_validation_variants'] != 450
            or point['negative_controls_excluded_from_rankings'] != 24
            or point['ranked_validation_variants'] != 6234 or point['validation_rows'] != [1321,1322]
            or point['baseline_test_rows'] != 210 or point['baseline_metric_cells_verified'] != 52272
            or point['baseline_nonempty_metric_cells_verified'] != 40656
            or point['box_validation_manifest_membership_verified'] is not True
            or any(point[x] for x in ('all_box_test_results_complete','independent_full_season_census_verified',
                'all_contender_test_comparison_complete','test_outcomes_select_models','predictions_or_fits_changed_by_comparison'))
            or point['primary_weights'] != [.5,.5]
            or point['rmse_aggregation'] != 'RECOMBINE_PHASE_SQUARED_RMSE_BY_ROW_COUNT_THEN_SQRT; ANNUAL_SCORES_WEIGHTED_50_50'):
        raise ValueError('Point comparison must retain its exact validation and incomplete-test scope')
    expected_roles = {(target,horizon,metric) for horizon in (60,120) for target in ('margin','total','winner')
        for metric in (('log_loss','brier','accuracy') if target == 'winner' else ('rmse','mae'))}
    role_counts = {('margin',60):1031,('margin',120):1023,('total',60):1021,
        ('total',120):1025,('winner',60):1069,('winner',120):1065}
    if len(point['rows']) != 14 or {(r['target'],r['horizon_minutes'],r['objective']) for r in point['rows']} != expected_roles:
        raise ValueError('All fourteen objective/horizon leaders must remain visible')
    for row in point['rows']:
        box = row['origin'] == 'B104_BOX_VALIDATION'
        if (row['origin'] not in ('PRESERVED_BASELINE','B104_BOX_VALIDATION')
                or box != (row['target'] == 'total')
                or row['family'] not in ('B095_FIXED_CONVEX_BLEND','catboost','sklearn_extra_trees')
                or row['higher_is_better'] != (row['objective'] == 'accuracy')
                or row['ranked_variants_in_role'] != role_counts[row['target'],row['horizon_minutes']]
                or not all(type(row[k]) in (int,float) and math.isfinite(row[k]) and row[k] > 0
                    for k in ('metric_2024','metric_2025','validation_50_50'))
                or not math.isclose(row['validation_50_50'],(row['metric_2024']+row['metric_2025'])/2,rel_tol=1e-12)):
            raise ValueError('Objective leaders require exact annual validation aggregation')
        if box:
            if row['metric_2026'] is not None or row['test_status'] != 'PENDING_AUTHENTICATED_BOX_TEST_COMPLETION':
                raise ValueError('Missing box test results cannot be invented')
        elif (row['test_status'] != 'AUTHENTICATED_210_ROW_REPLAY' or type(row['metric_2026']) not in (int,float)
                or not math.isfinite(row['metric_2026']) or row['metric_2026'] <= 0):
            raise ValueError('Preserved test metrics require authenticated snapshot scope')
    if len(data['requirements_still_open']) != 6 or any(x['status'] != 'UNFINISHED' for x in data['requirements_still_open']):
        raise ValueError('Required unresolved work remains visible')
    if data['publication'] != {'draft_pr': 392, 'source_review_only': True, 'merged': False,
        'website_deployed': False, 'automatic_champion_promotions': 0,
        'new_public_forecast_values': 0, 'private_runtime_or_raw_provider_data_published': False}:
        raise ValueError('Source review does not authorize promotion or deployment')
    if len(data['evidence']) < 7 or any(not valid_pin({k:row[k] for k in ('bytes','sha256')})
            or set(row) != {'label','bytes','sha256'} for row in data['evidence']):
        raise ValueError('Each aggregate evidence source needs an exact digest')
    raw = json.dumps(data, sort_keys=True)
    if any(token in raw.lower() for token in ('s3://', '/home/', '/workspace/', 'arn:aws:',
        'candidate_id', 'feature_names', 'api_key', 'access_key', 'circa')):
        raise ValueError('Private paths, recipes, credentials and other-sport content are excluded')
    return data


def render(data):
    validate(data)
    e = lambda x: html.escape(str(x), quote=True)
    source = json.dumps(data, indent=2, ensure_ascii=False) + '\n'
    encoded = base64.b64encode(source.encode()).decode()
    embedded = source.replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')
    prep = data['B105_preparation']
    status_label = {'PREPARATION_IN_PROGRESS':'Repair implementation and validation are in progress.',
        'BUILD_TESTED':'The corrected build has engineering evidence; private delivery remains unverified.',
        'VERIFIED_DELIVERY_NATIVE_PENDING':'Private delivery passed full readback; native installation remains pending.',
        'DELIVERY_AND_NATIVE_INSTALL_VERIFIED':'Private delivery and native installation passed complete-byte verification.'}[prep['status']]
    identity = ''.join('<div class="identity"><strong>'+e(label)+'</strong><span>'+str(prep[key]['bytes'])+' bytes</span><code>'+e(prep[key]['sha256'])+'</code></div>'
        for key,label in [('canonical_executable','Prepared canonical executable'),('verification_evidence','Delivery verification evidence'),('engineering_evidence','Engineering evidence')]
        if prep[key] is not None)
    requirements = ''.join('<li><div><strong>'+e(x['name'])+'</strong><span class="state">'+e(x['status'])+'</span></div><p>'+e(x['detail'])+'</p></li>' for x in data['requirements_still_open'])
    sources = ''.join('<li><strong>'+e(x['label'])+'</strong><span>'+format(x['bytes'],',')+' bytes</span><code>'+e(x['sha256'])+'</code></li>'for x in data['evidence'])
    repairs = ''.join('<li>'+e(x)+'</li>'for x in data['repair_scope'])
    backup_label = ('The immutable backup passed full GET and SHA-256 verification without changing canonical owner pointers.'
        if data['recovered_frozen_test']['immutable_backup']['status'] == 'FULL_GET_SHA_VERIFIED'
        else 'The verified local payloads await the separate immutable remote-backup proof; canonical owner pointers remain unchanged.')
    rows = ''
    for row in data['comparison']['rows']:
        family = 'Linear + Gaussian' if row['family'] == 'sklearn_linear' else 'Extra Trees + Gaussian'
        values = [row['target'].title()+' · '+str(row['horizon_minutes'])+' min',family,
            f"{row['crps_2024']:.4f}",f"{row['crps_2025']:.4f}",f"{row['validation_50_50']:.4f}",f"{row['crps_2026']:.4f}"]
        labels = ['Role','Family','2024–25','2025–26','50/50 validation','2026–27 test']
        rows += '<tr>'+''.join('<td data-label="'+e(label)+'">'+e(value)+'</td>'for label,value in zip(labels,values))+'</tr>'
    native_rows = ''
    phase_names = {'FROZEN_TEST_AUTHORIZED_INFERENCE':'Frozen-test application',
        'HISTORICAL_CALIBRATION_SERIALIZATION_PARITY':'Saved calibration parity',
        'VALIDATION_REPLAY_COMPARE_WITH_B104':'Validation replay'}
    for phase in data['native_verification']['phase_measurements']:
        values = [phase_names[phase['phase']], '12 / 12', '1',
            f"{phase['measured_average_cores_during_call_window']:.4f}",
            f"{phase['native_call_window_seconds']:.4f}", '12']
        labels = ['Phase','PIDs / overlap','Native threads','Measured cores','Call window (s)','Completed calls']
        native_rows += '<tr>'+''.join('<td data-label="'+e(label)+'">'+e(value)+'</td>' for label,value in zip(labels,values))+'</tr>'
    point_rows = ''
    for row in data['point_comparison']['rows']:
        family = {'B095_FIXED_CONVEX_BLEND':'Preserved fixed blend','catboost':'CatBoost',
            'sklearn_extra_trees':'Extra Trees'}[row['family']]
        metric = {'rmse':'RMSE ↓','mae':'MAE ↓','log_loss':'Log loss ↓','brier':'Brier ↓','accuracy':'Accuracy ↑'}[row['objective']]
        score = lambda value: 'Pending' if value is None else f'{value:.6f}'
        values = [row['target'].title()+' · '+str(row['horizon_minutes'])+' min',metric,family,
            score(row['metric_2024']),score(row['metric_2025']),score(row['validation_50_50']),score(row['metric_2026'])]
        labels = ['Role','Objective','Family','2024–25','2025–26','50/50 validation','2026–27 test']
        point_rows += '<tr>'+''.join('<td data-label="'+e(label)+'">'+e(value)+'</td>' for label,value in zip(labels,values))+'</tr>'
    return '''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="NBA B104 recovery evidence and B105 preparation, with audited task accounting and bounded scientific claims."><title>NBA B105 · Recovery and remaining research</title><style>'''+STYLE+'''</style></head><body><main>
<header><div class="eyebrow">SPORTS EDGE LAB / NBA · NOVEMBER 19, 2026</div><h1>B104 stopped.<br>Completed science is preserved.</h1><p class="lead">The recovery audit identifies the memory failure, separates successful recipes from failed task records, and carries verified work into B105 preparation.</p><p class="meta">Draft source review · NBA only · Owner executes the research run</p></header>
<nav aria-label="Review sections"><a href="#work">Recovered work</a><a href="#incident">Failure evidence</a><a href="#cpu">Measured CPU</a><a href="#point-comparison">Point comparisons</a><a href="#comparison">Distribution comparison</a><a href="#prepared">B105 readiness</a><a href="#remaining">Remaining work</a></nav>
<div class="notice"><strong>No verified B104 final return was published.</strong> Checkpoint and artifact audits preserve completed science. B105 has zero owner executions; preparation and engineering tests do not complete the research campaign.</div>
<div class="cards" aria-label="Audited B104 research counts"><div class="card"><div class="number">201 + 201</div><div class="caption">New estimators + calibrators</div></div><div class="card"><div class="number">24 pairs</div><div class="caption">Existing estimators + calibrators reused</div></div><div class="card"><div class="number">15</div><div class="caption">Failed model recipes, recorded separately</div></div><div class="card"><div class="number">320</div><div class="caption">Original distribution heads reapplied</div></div></div>
<section id="work"><span class="badge">B104 · VERIFIED RECOVERY COUNTS</span><h2>Task receipts preserve the actual results</h2><div class="progress-row"><div class="progress-head"><strong>225 / 240 successful model recipes</strong><span>15 failed recipes remain explicit</span></div><progress max="240" value="225" aria-label="Successful model recipes">225 of240</progress><p>The 240 task records are not 240 successful fits. Successful recipes comprise 201 newly fitted pairs and 24 reused pairs.</p></div>
<div class="columns"><div><h3>Validation and context</h3><p><strong>225 validation tasks · 450 scored variants</strong><br>402 new validation ledgers and 48 reused ledgers. All 30 context tasks reused existing work.</p></div><div><h3>Original distributions</h3><p><strong>320 original state pins unchanged</strong><br>All 320 heads were reapplied. Zero new residual-distribution fits were needed for this reuse.</p></div></div>
<details id="receipt-detail"><summary>What the audit verifies</summary><p>975 registry bodies were independently retrieved and SHA-verified. The native audit verified 6,291 local artifact references. All 5,607 unique S3 payloads—2,683,086,355 bytes—passed full GET and SHA-256 verification, with zero missing, unknown or mismatched objects. Integrity checks, successful scientific outputs and failed recipes have separate counts.</p><p>Thirteen PyTorch recipes failed during interop-thread initialization. Two TensorFlow recipes failed serialization-parity checks. Their partial task receipts remain failures. Current-run S3 box frozen-test task registry closures remain absent. A separate content audit recovered 46 saved base-model test results and 92 raw/calibrated ledgers.</p></details><div id="recovered-test"><h3>Saved frozen-test outputs are recovered</h3><p><strong>46 verified base-model results and 92 prediction ledgers</strong> share the 210 completed-game test snapshot and 1,200-game forecast population. They comprise 24 earlier cached results and 22 new B104 inference results. The 23 B104 local completion records include 44 new ledgers and two reused ledgers, with zero new fits.</p><p>All 161 recovered payload files total <strong>14,719,711 bytes</strong>. '''+e(backup_label)+'''</p><p><strong>At most 179 original base-model test inferences remain</strong>, plus successful replacements for up to 15 failed neural recipes. All four new CatBoost total-point validation leaders still lack test results; the audit does not manufacture those results or change the validation ranks.</p></div><p class="note">The monetary guard is a spending ceiling. Actual invoiced cost and NBA cost allocation remain unknown.</p></section>
<section id="incident"><span class="badge pending">OBSERVED MEMORY FAILURE</span><h2>A large selection lock was decoded in every test worker</h2><div class="policy"><div><strong>1.141 GB</strong><span>1,141,248,706-byte selection lock</span></div><div><strong>36</strong><span>Admitted frozen-test readers</span></div><div><strong>0 → 15</strong><span>Observed OOM-kill counter</span></div></div><p>The lock repeated tied-model memberships across ranking rows. Frozen-test tasks independently read and decoded the entire object despite a nominal one-GiB reservation per worker. Shared memory usage peaked at <strong>97.784 GB</strong> against <strong>99.615 GB</strong> of physical memory.</p><p>CloudWatch records <strong>13 identified frozen-test workers terminated by SIGKILL</strong>. The independent observer found the owner absent at <strong>19:27:29 UTC</strong>. Surviving prediction workers were orphaned.</p><p class="note" id="cause-limitation"><strong>The owner's exact exit status was not retained.</strong> The memory amplification, OOM event and worker SIGKILLs are evidenced; attributing the owner itself to an OOM kill remains an inference. No fixed three-minute timeout or LightGBM training defect was established for this incident.</p></section>
<section id="cpu"><h2>B104 performed real concurrent scientific work</h2><div class="columns"><div><h3>Base fitting</h3><div class="metric">32.2775 cores</div><p>Measured peak with 35 active fit workers.</p></div><div><h3>Validation scoring</h3><div class="metric">29.4468 cores</div><p>Measured peak with 32 active scoring workers.</p></div></div><p class="note">Peak samples do not establish the sustained 180-second / 75%-occupancy gate. B105 must measure useful worker PIDs, CPU, queue depth, memory and durable completions with enough ready work.</p><div class="policy"><div><strong>12</strong><span>Normal scientific worker target</span></div><div><strong>36</strong><span>Requested cores and hard worker ceiling</span></div><div><strong>1</strong><span>Native thread per independent fit</span></div></div><p>12–36 useful cores remain conditional on safe shared CPU, memory and I/O capacity. The explicit 36-worker maximum is a hard ceiling. Unlimited wall time does not waive the <strong>USD 200 compute guard</strong>.</p></section>
<section id="point-comparison"><span class="badge">IDENTICAL VALIDATION POPULATIONS</span><h2>Point and winner models can now be compared fairly</h2><p>The audit covers <strong>5,808 preserved baseline variants and 450 box-feature variants</strong> on the same 1,321 / 1,322 validation games. The declared comparison excludes 24 negative-control variants from rankings, leaving 6,234 ranked variants across target/horizon roles.</p><div class="columns"><div><h3>Margins and winner probabilities</h3><p>Preserved models retain the primary margin and winner-objective leads. The table selects each role using 50/50 annual validation scores; test scores do not choose the leaders.</p></div><div><h3>Total points</h3><p>CatBoost box-feature variants lead all four total-point MAE/RMSE roles on validation. <strong>Their 2026–27 test metrics remain pending</strong>; native worker activity does not substitute for authenticated completed results.</p></div></div>
<details id="point-detail"><summary>Show all 14 objective leaders</summary><div class="table-wrap"><table><caption>50/50 validation leaders; higher accuracy is better, all other displayed metrics are lower-is-better</caption><thead><tr><th>Role</th><th>Objective</th><th>Family</th><th>2024–25</th><th>2025–26</th><th>50/50 validation</th><th>2026–27 test</th></tr></thead><tbody>'''+point_rows+'''</tbody></table></div></details><p class="note">Preserved test metrics use the same authenticated 210-game snapshot. All 52,272 preserved metric cells were checked against their season/phase populations; the 40,656 nonempty cells have zero missing predictions or labels. Box validation ledgers were checked independently. Annual RMSE is reconstructed from count-weighted phase squared errors before annual 50/50 averaging. This is a descriptive comparison, not a promotion or independent full-season qualification.</p></section>
<section id="comparison"><h2>The 320 preserved heads now share the expanded evaluation rows</h2><p>Each role compares 80 preserved distribution candidates on exactly <strong>1,321 games in 2024–25</strong>, <strong>1,322 in 2025–26</strong>, and <strong>210 in the frozen 2026–27 test snapshot</strong>. Game-ID manifest hashes agree; these cohorts have zero missing predictions. The table shows the lowest 50/50 validation CRPS within each role. Lower CRPS is better.</p>
<div class="table-wrap"><table><caption>Validation-selected descriptive leaders among preserved heads; no champion promotion</caption><thead><tr><th>Role</th><th>Family</th><th>2024–25</th><th>2025–26</th><th>50/50 validation</th><th>2026–27 test</th></tr></thead><tbody>'''+rows+'''</tbody></table></div>
<details id="selection-detail"><summary>Population, sensitivity and test-exposure limits</summary><p>These are qualified replays of original fitted states. The earlier B100 comparison used 1,314 / 1,315 / 210 rows. An inherited population-qualification field still carried the older counts; this review uses the audited metric rows and manifest hashes instead of that stale label.</p><p>The primary ratio is 50/50. Sensitivities use 40/60, 30/70, 20/80 and 10/90 without refitting or changing base predictions. Margin leaders remain the same across all five ratios; each total role has three distinct sensitivity leaders.</p><p>2026–27 outcomes are reporting-only and cannot select models, calibrators, residual heads or blends. Previously inspected test outcomes remain exposed. The 210-game snapshot is not a fresh all-completed-game census.</p></details><p class="note">This completes the declared same-manifest comparison for the 320 preserved heads. Independent full-season qualification and the all-contender comparison remain unfinished. No full-season champion is certified.</p></section>
<section id="prepared"><span class="badge pending">B105 · PREPARATION</span><h2>Preserve valid states; repair the failing boundaries</h2><p id="prepared-status">'''+e(prep['status'])+'''</p><p id="delivery-qualification">'''+e(status_label)+'''</p><p><strong>All nine read-only native launch-readiness gates passed</strong>, with zero failed or unrun gates and zero research dispatches. The installed canonical archive and immutable remote copy both passed complete-byte verification. The owner launch must resolve the latest durable checkpoint and current resource availability again.</p><p><strong>Zero B105 owner executions and zero new owner fits are credited.</strong> The owner will execute the prepared research campaign.</p><ul>'''+repairs+'''</ul>'''+identity+'''<p class="note">A small outer observer can record a child crash and verify a compact resumable diagnostic return. It cannot guarantee publication if the observer or whole instance is killed, or persistent storage fails. Existing durable task receipts remain the recovery authority.</p></section>
<section id="native-verification"><span class="badge">BOUNDED NATIVE VERIFICATION</span><h2>Twelve existing models ran concurrently</h2><p><strong>60 native archive regression tests passed</strong>, with zero failures or errors, including exact prior point-checkpoint identities and zero repeated inference. Those tests bind the prepared executable above and do not constitute an owner campaign.</p><p>The representative native check completed <strong>12 existing-model tasks, with 12 overlapping native model calls</strong>, zero failed or missing tasks, and one native thread per observed backend pool. It made 12 frozen-test applications and <strong>zero repeated frozen-test calls on warm resume</strong>. All 225 previously completed model states remained preserved.</p><div class="table-wrap"><table><caption>Actual model-call windows; worker overlap and CPU utilization are separate measurements</caption><thead><tr><th>Phase</th><th>PIDs / overlap</th><th>Native threads</th><th>Measured cores</th><th>Call window (s)</th><th>Completed calls</th></tr></thead><tbody>'''+native_rows+'''</tbody></table></div><p>Peak combined worker RSS was <strong>4,889,866,240 bytes</strong>. The observed call windows averaged <strong>4.1753–4.6783 cores</strong> over <strong>0.1161–0.2669 seconds</strong>. Twelve overlapping workers are not twelve measured busy cores.</p><p class="note"><strong>The sustained 180-second / 75%-occupancy gate was not evaluated.</strong> The representative workload was too short. Zero new owner estimator or calibration fits are credited. Four separate engineering-fixture optimizer calls are recorded as engineering work.</p><h3>Native crash and compact-publication check</h3><p>Three isolated child cases passed: exit 2 without a final return, an owned child killed by SIGKILL, and a normal verified partial return. The check used actual S3 responses in an isolated engineering namespace; <strong>35 objects passed full GET and SHA-256 verification</strong>. It made zero canonical owner-pointer writes and zero scientific fits. Normal partial completion did not create a duplicate abnormal return.</p><p>These checks establish representative recovery and publication behavior. The full owner research run, its sustained CPU acceptance and its verified final return remain pending.</p></section>
<section id="remaining"><h2>What the next execution must finish</h2><p>Reuse the 225 valid model recipes and all 320 original distribution heads. Reconcile the actual task graph before admitting missing work; do not carry forward the old count of 216 missing base fits.</p><ul class="requirements">'''+requirements+'''</ul></section>
<section id="evidence"><h2>Inspect the aggregate evidence</h2><a class="download" id="download-evidence" href="data:application/json;base64,'''+encoded+'''" download="nba-b105-recovery-evidence.json">Download exact aggregate evidence</a><ul class="sources">'''+sources+'''</ul><p class="note">Draft PR392 remains unmerged. No website deployment, new public per-game forecast values or champion promotion is established. Private runtime code, feature recipes, model weights, raw licensed data and storage locations are excluded.</p></section>
<footer><a href="../README.md">NBA research archive</a> · <a href="b104_execution_status.html">Preserved B104 preparation</a> · <a href="b103_execution_status.md">Preserved B103 execution</a><p>November 19, 2026 · Source review only. Other owners remain unchanged.</p></footer>
<script type="application/json" id="aggregate-evidence">'''+embedded+'''</script></main></body></html>\n'''


def self_test(data):
    cases = [
        ('actual_B104','s3_payload_unknown',1),('actual_B104','new_estimator_fits',240),('actual_B104','successful_model_recipes',240),
        ('actual_B104','failed_model_recipes',0),('actual_B104','reused_estimator_fits',0),
        ('actual_B104','owner_exact_exit_code',137),('actual_B104','owner_exact_signal',9),
        ('actual_B104','verified_final_return_published',True),('actual_B104','reused_original_distribution_fits',0),
        ('actual_B104','current_run_s3_box_frozen_test_task_receipts',225),('actual_B104','full_v13_complete',True),
        ('recovered_frozen_test','local_verified_base_results',0),
        ('recovered_frozen_test','local_verified_prediction_ledgers',450),
        ('recovered_frozen_test','remaining_original_225_base_test_inferences_at_most',225),
        ('recovered_frozen_test','all_four_new_total_leaders_test_pending',False),
        ('recovered_frozen_test','frozen_test_stage_complete',True),
        ('incident','fixed_180_second_timeout_established',True),('incident','lightgbm_fit_failure_caused_incident',True),
        ('incident','owner_oom_victim_attribution','OBSERVED_OWNER_SIGKILL'),
        ('cpu','peak_is_sustained_acceptance',True),('cpu','configured_workers_are_measured_busy_cores',True),
        ('B105_preparation','new_owner_executions',1),('B105_preparation','new_estimator_fits',1),
        ('B105_preparation','status','DELIVERED_AND_FULL_RESEARCH_COMPLETE'),
        ('native_verification','worker_count_is_measured_core_count',True),
        ('native_verification','sustained_180_second_75_percent_gate','PASS'),
        ('native_verification','new_owner_scientific_fits',12),
        ('native_verification','owner_research_executions',1),
        ('native_verification','warm_repeat_inference_calls',12),
        ('native_verification','engineering_fixture_optimizer_calls',0),
        ('owner_request','wall_zero_waives_cost_guard',True),('owner_request','explicit_max_workers',48),
        ('comparison','test_outcomes_select_models',True),('comparison','fresh_all_completed_test_census_verified',True),
        ('comparison','full_season_champions_qualified',True),('comparison','evaluation_rows',[1314,1315,210]),
        ('comparison','sensitivity_changes_fit_or_predictions',True),
        ('point_comparison','all_box_test_results_complete',True),
        ('point_comparison','all_contender_test_comparison_complete',True),
        ('point_comparison','test_outcomes_select_models',True),
        ('point_comparison','predictions_or_fits_changed_by_comparison',True),
        ('point_comparison','ranked_validation_variants',6258),
        ('point_comparison','validation_rows',[1314,1315]),('publication','website_deployed',True),
        ('publication','automatic_champion_promotions',1)]
    rejected = 0
    for section,key,value in cases:
        changed = copy.deepcopy(data);changed[section][key] = value
        try:validate(changed)
        except (ValueError,TypeError):rejected += 1
        else:raise AssertionError('Unsupported claim admitted: '+section+'.'+key)
    changed = copy.deepcopy(data);changed['repair_scope'].append('/home/private/model.json')
    try:validate(changed)
    except ValueError:rejected += 1
    else:raise AssertionError('Private path admitted')
    changed = copy.deepcopy(data);changed['comparison']['rows'][0]['validation_50_50'] += 1
    try:validate(changed)
    except ValueError:rejected += 1
    else:raise AssertionError('Invalid validation aggregate admitted')
    for key,value in [('metric_2026',18.1),('validation_50_50',1.0),('higher_is_better',True)]:
        changed = copy.deepcopy(data);changed['point_comparison']['rows'][4][key] = value
        try:validate(changed)
        except (ValueError,TypeError):rejected += 1
        else:raise AssertionError('Invalid point comparison admitted: '+key)
    for section,key,value in [('phase_measurements','measured_average_cores_during_call_window',12),
            ('real_s3_publication','canonical_owner_pointer_writes',1)]:
        changed = copy.deepcopy(data)
        target = changed['native_verification'][section]
        if isinstance(target,list):target = target[0]
        target[key] = value
        try:validate(changed)
        except (ValueError,TypeError):rejected += 1
        else:raise AssertionError('Invalid native proof admitted: '+key)
    return rejected


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--check',action='store_true');p.add_argument('--self-test',action='store_true')
    args = p.parse_args();data = json.loads(SOURCE.read_text());expected = render(data)
    if args.check:
        if not OUTPUT.is_file() or OUTPUT.read_text() != expected:raise SystemExit('B105 HTML is stale')
    else:OUTPUT.write_text(expected)
    rejected = self_test(data) if args.self_test else 0
    print(json.dumps({'status':'PASS','unsupported_claims_rejected':rejected,'owner_executions':0,
        'new_owner_fits':0,'deployment_performed':False}))


if __name__ == '__main__':
    main()
