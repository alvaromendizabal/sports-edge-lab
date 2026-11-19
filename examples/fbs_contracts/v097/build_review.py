"""Build the credential-free FBS actual-return and continuation review."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / 'docs/fbs/v097/data/status.json'
OUTPUT = ROOT / 'docs/fbs/v097/index.html'
TEMPLATE = Path(__file__).with_name('template.html.in')
PROFILES = ['50/50', '40/60', '30/70', '20/80', '10/90']
OBJECTIVES = [('winner','accuracy'), ('winner','brier'), ('winner','log_loss'),
              ('margin','mae'), ('margin','rmse'), ('margin','crps'),
              ('total','mae'), ('total','rmse'), ('total','crps')]
ROOT_KEYS = set('schema owner as_of publication execution cpu cost selection population sources storage remaining_work next_preparation evidence'.split())


def require(condition, message):
    if not condition:
        raise ValueError(message)


def number(value):
    return type(value) in (int, float) and math.isfinite(value)


def validate(d):
    require(isinstance(d, dict) and set(d) == ROOT_KEYS, 'Unknown or missing public projection fields')
    require(d['schema'] == 'fbs.public.actual-and-continuation.v097' and d['owner'] == 'FBS', 'Wrong schema or owner')
    serialized = json.dumps(d, ensure_ascii=False, allow_nan=False)
    require(not re.search(r's3://|/home/|sagemaker|arn:aws|api[_-]?key|secret[_-]?key|circa|model_id|owner_relative_path', serialized, re.I), 'Private or out-of-scope material')
    require(d['publication'] == {'source_only':True,'merged':False,'website_deployed':False,'production_promoted':False}, 'Source review is not deployment')
    a, c, s, p, n = (d[k] for k in ('execution','cpu','selection','population','next_preparation'))
    require(a['release'] == 'V096' and a['run_id'] == '20261118T174548Z-4a5cc95a05-fbs096', 'Wrong actual attempt')
    require(a['child_exit_code'] == a['supervisor_exit_code'] == 0 and a['supervisor_status'] == 'VERIFIED_RETURN_PUBLICATION_FINISHED', 'Preserve observed closure')
    require(a['operationally_finished'] is True and a['return_integrity_verified'] is True and a['resumable'] is True and a['scientific_complete'] is False, 'Operational completion is not full science completion')
    require(a['completed_jobs'] == a['registered_jobs'] == 936 and a['reused_jobs'] == 624 and a['new_model_fits'] == a['new_calibrator_fits'] == a['registered_test_jobs_completed'] == 312 and a['failed_fits'] == 0, 'Completed, reused and newly fitted jobs must remain separate')
    require(sum(x['completed_jobs'] for x in a['branch_counts']) == 936 and sum(x['checkpoint_reused_jobs'] for x in a['branch_counts']) == 624 and sum(x['new_model_fits'] for x in a['branch_counts']) == sum(x['new_calibrator_fits'] for x in a['branch_counts']) == 312, 'Branch counts do not close')
    require(a['historical_failed_attempts'] == 6 and a['operationally_finished_attempts'] == 1 and a['fully_v13_complete_attempts'] == 0, 'Do not count this partial success as a new crash or completed program')
    require(a['scored_inventory_includes_reuse'] is True and a['materialized_blends_all_novel'] is False, 'Inventory and blend materialization are not all-new forecasts')
    require(a['new_callback_prediction_rows'] == 547872 and a['materialized_blend_rows'] == 229488 and a['scored_inventory_rows'] == 1846464 and a['forecast_inventory_rows'] == 1934256, 'Preserve saved forecast accounting')
    require(c['workers'] == c['observed_fit_processes'] == c['max_concurrent_fits'] == c['max_concurrent_preparations'] == c['useful_gate_workers'] == 17 and c['hard_ceiling'] == 24 and c['native_threads_per_worker'] == 1 and c['arbitrary_reserved_cores'] == 0, 'Admission and actual fit evidence differ')
    for key, value in c.items():
        if key.endswith(('_seconds','_fraction')):
            require(number(value) and value >= 0, 'Invalid measured CPU, time or fraction')
    require(c['useful_gate_status'] == c['optimizer_gate_status'] == 'PASS_REAL_WORK' and c['useful_gate_seconds'] >= 180 and 0.75 <= c['optimizer_gate_fraction'] <= c['useful_gate_fraction'] <= 1, 'Preserve the earlier qualifying real-work window')
    require(c['gate_includes_preparation'] is True and c['gate_completions_include_calibrators'] is True and c['optimizer_completions_in_gate'] == 418, 'Gate completions include models and calibrators')
    require(c['end_queue_status'] == 'CONDITIONAL_INSUFFICIENT_INDEPENDENT_WORK', 'An exhausted queue does not erase an earlier pass')
    require(c['legacy_not_ready_includes_busy_preparation'] is True and c['pending_preparation_with_idle_slots_seconds'] <= c['legacy_preparation_not_ready_seconds'], 'Queue wait definitions must remain distinct')
    require(c['optimizer_cpu_seconds'] > 12*c['dispatch_wall_seconds'] and c['scoring_cpu_seconds'] < 1.1*c['scoring_wall_seconds'], 'Do not interchange fit and serial-scoring CPU scopes')
    require(d['cost']['invoice'] is False and d['cost']['guard_usd'] == 200 and d['cost']['wall_zero_waives_guard'] is False, 'Estimate and cost guard need their correct scope')
    require(s['seasons'] == [2024,2025] and s['test_season'] == 2026 and s['profiles'] == PROFILES and s['primary_profile'] == '50/50' and s['horizon_minutes'] == 120, 'Preserve seasons, horizon and selection ratios')
    for field in ['test_used_for_selection','season_training_weights','sensitivity_changes_predictions','promotion','full_population_champion_eligible']:
        require(s[field] is False, 'Selection, fitting and promotion boundaries changed')
    require(s['sensitivity_refits'] == 0 and s['test_previously_exposed'] is True and s['evidence_class'] == 'V13_FROZEN_RECONSTRUCTION', 'No pristine-test or refit claim')
    require(len(s['leaders']) == 45 and {(x['profile'],x['target'],x['metric']) for x in s['leaders']} == {(w,t,m) for w in PROFILES for t,m in OBJECTIVES}, 'All five profiles and nine objectives are required')
    primary = {(x['target'],x['metric']):x for x in s['leaders'] if x['profile'] == '50/50'}
    for x in s['leaders']:
        require(x['expected_n'] == x['scored_n'] == [919,934,755] and len(x['annual_values']) == 3, 'Retain full eligible annual denominators')
        require(all(number(v) and v >= 0 for v in x['annual_values']), 'Invalid annual metric')
        if x['metric'] in {'accuracy','brier'}:
            require(all(v <= 1 for v in x['annual_values']), 'Probability metric out of range')
        w = int(x['profile'].split('/')[0])/100
        require(math.isclose(x['selection_score'],w*x['annual_values'][0]+(1-w)*x['annual_values'][1],rel_tol=1e-12,abs_tol=1e-12), 'Selection score must use only annual validation metrics')
        require(type(x['primary_policy_rank']) is int and x['primary_policy_rank'] >= 1, 'Missing sensitivity rank')
        default = primary[x['target'],x['metric']]
        require(x['same_policy_as_primary'] == (x['policy_alias'] == default['policy_alias']), 'Sensitivity identity mismatch')
        if x['same_policy_as_primary']:
            require(x['annual_values'] == default['annual_values'], 'Changing profile cannot change a fixed policy prediction score')
        if x['profile'] == '50/50':
            require(x['primary_policy_rank'] == 1, 'Primary leader must rank first')
    require(p['completed_test_games'] == 755 and p['pending_test_games'] == 133 and p['test_policy_count'] == p['test_policies_with_full_known_completed_coverage'] == 1105, 'Known population is not complete official census')
    require(p['official_population_complete'] is False and p['postseason_completeness_proven'] is False and p['game_rows_removed_for_coverage'] == 0 and p['retained_predictions_changed'] is False, 'Do not erase population or replay limitations')
    require(p['retained_pending_groups'] == [{'policies':288,'covered':123,'expected':133},{'policies':109,'covered':93,'expected':133}] and p['frozen_context_pending_feature_gaps_per_target'] == 10, 'Upcoming gaps cannot disappear')
    src = d['sources']; require(src['coverage_is_scored_benchmark'] is False and src['historical_possession_created'] is False, 'Source reference coverage is not predictive grading or historical possession')
    require(len(src['bookmakers']) == 18 and len(src['t120_completed_coverage']) == 162 and len(src['horizons']) == 11, 'Source grid is incomplete')
    seen = set()
    for row in src['t120_completed_coverage']:
        key = row['bookmaker'],row['source_route'],row['season'],row['target'];require(key not in seen, 'Duplicate market row');seen.add(key)
        require(row['expected_n'] == {2024:919,2025:934,2026:755}[row['season']], 'Source coverage shrank the denominator')
        for field in ['feature_qualified_n','reference_n','predictive_baseline_qualified_n','strict_original_availability_qualified_n']:
            require(type(row[field]) is int and 0 <= row[field] <= row['expected_n'], 'Invalid coverage count')
    st = d['storage'];require(st['control_zip_bytes'] == 88491826 and st['new_scientific_payload_bytes'] == 1676955059 and st['inherited_payload_bytes_not_recopied'] == 35483901513 and st['is_all_scientific_storage'] is False and st['aggregate_science_cap'] is None and st['part_limit_bytes'] == 512*1024*1024, 'Control ZIP is not all science storage')
    require(n['release'] == 'V097' and n['status'] in {'IN_PREPARATION','PREPARED_NOT_EXECUTED'}, 'Unknown successor preparation')
    require(n['owner_runs_launched'] == n['new_model_fits'] == n['provider_retrievals'] == n['predecessors_stopped'] == 0, 'Preparation is not an owner execution')
    require(n['target_workers'] == 12 and n['worker_ceiling'] == 24 and n['planned_source_jobs'] == 306 and n['planned_families'] == ['XGBoost','CatBoost'] and n['reuse_completed_registered_jobs'] == 936 and n['planned_jobs_are_new_fit_promise'] is False and n['parallel_checkpointed_scoring'] is True and n['resolves_latest_at_launch'] is True, 'Finite continuation and resume boundaries changed')
    require(n['summary_comparison'] == {'source_release':'V096','original_bytes':131276993,'reencoded_bytes':137541,'scope':'OFFLINE_SERIALIZATION_COMPARISON_ONLY','full_stage_pins_preserved':True,'future_total_return_size_claimed':False}, 'Serialization comparison is not a future total-return size claim')
    if n['status'] == 'IN_PREPARATION':
        require(n['native_verified'] is False and all(n[k] is None for k in ['canonical_bytes','canonical_sha256','native_verified_at','engineering_checks_passed']), 'Unsealed preparation cannot claim installation')
    else:
        require(n['native_verified'] is True and type(n['canonical_bytes']) is int and n['canonical_bytes'] > 0 and re.fullmatch('[a-f0-9]{64}',n['canonical_sha256'] or '') and n['native_verified_at'] and type(n['engineering_checks_passed']) is int and n['engineering_checks_passed'] > 0, 'Verified preparation requires sealed canonical evidence')
        require(n['native_admission'] == {'registered_jobs':306,'admitted_jobs':306,'validation_jobs':204,'frozen_test_jobs':102,'projected_workers':24,'projected_cpu_count':24,'checkpoint_receipts_verified_unchanged':937,'preparation_jobs_dispatched':0,'model_states_deserialized':0,'projection_only_not_measured_V097_scientific_occupancy':True}, 'Read-only admission is not measured scientific throughput')
    require(len(d['remaining_work']) >= 7 and all(x['status'] in {'UNPROVEN','NEXT_FINITE_TRANCHE','DEFERRED'} for x in d['remaining_work']), 'Unfinished program branches must remain visible')
    require(len(d['evidence']) >= 7 and all(re.fullmatch('[a-f0-9]{64}',x['sha256']) and type(x['bytes']) is int and x['bytes'] > 0 for x in d['evidence']), 'Missing source pins')
    return d


def render(data):
    validate(data)
    payload = json.dumps(data,ensure_ascii=False,allow_nan=False,separators=(',',':')).replace('<','\\u003c')
    sha = hashlib.sha256(payload.encode()).hexdigest()
    return TEMPLATE.read_text().replace('__DATA_SHA256__',sha).replace('__DATA__',payload).encode()


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args()
    output=render(json.loads(DATA.read_text()))
    if args.check:
        require(OUTPUT.read_bytes()==output,'Committed HTML differs from deterministic evidence projection')
    else:
        OUTPUT.parent.mkdir(parents=True,exist_ok=True);OUTPUT.write_bytes(output)
    print(json.dumps({'status':'PASS','bytes':len(output),'sha256':hashlib.sha256(output).hexdigest(),'owner_research_executions':0}))


if __name__=='__main__':
    main()
