"""Deterministically render the bounded, credential-free V097 evidence review."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / 'docs/fbs/v098/data/status.json'
OUTPUT = ROOT / 'docs/fbs/v098/index.html'
TEMPLATE = Path(__file__).with_name('template.html.in')
PROFILES = ['50/50','40/60','30/70','20/80','10/90']
OBJECTIVES = [('winner','accuracy'),('winner','brier'),('winner','log_loss'),
              ('margin','mae'),('margin','rmse'),('margin','crps'),
              ('total','mae'),('total','rmse'),('total','crps')]
ROOT_KEYS = set('schema owner as_of publication execution cpu cost selection population sources storage remaining_work next_preparation evidence'.split())


def require(condition, message):
    if not condition:
        raise ValueError(message)


def finite(value):
    return type(value) in (int,float) and math.isfinite(value)


def close(a,b):
    return finite(a) and finite(b) and math.isclose(a,b,rel_tol=1e-12,abs_tol=1e-12)


def validate(d):
    require(type(d) is dict and set(d)==ROOT_KEYS,'Unknown or missing projection fields')
    require(d['schema']=='fbs.public.actual-and-continuation.v098' and d['owner']=='FBS','Wrong report identity')
    raw=json.dumps(d,ensure_ascii=False,allow_nan=False)
    require(not re.search(r's3://|/home/|sagemaker|arn:aws|api[_-]?key|secret[_-]?key|circa|model_id|game_id|owner_relative_path',raw,re.I),'Private or out-of-scope material')
    require(d['publication']=={'source_only':True,'merged':False,'website_deployed':False,'production_promoted':False},'Source preparation is not deployment')
    a,c,s,p,n=(d[k] for k in ['execution','cpu','selection','population','next_preparation'])
    require(a['release']=='V097' and a['run_id']=='20261118T194552Z-3788012f0c-fbs097','Wrong actual invocation')
    require(a['child_exit_code']==a['supervisor_exit_code']==0 and a['supervisor_status']=='VERIFIED_RETURN_PUBLICATION_FINISHED','Preserve authenticated supervisor closure')
    require(a['operationally_finished'] is True and a['return_integrity_verified'] is True and a['resumable'] is True and a['scientific_complete'] is False,'Operational completion and scientific completion differ')
    require(a['registered_jobs']==a['completed_jobs']==306 and a['validation_jobs']==204 and a['frozen_test_jobs']==102,'Finite job counts do not close')
    require(a['new_model_fits']==a['new_calibrator_fits']==294 and a['reused_fit_states']==12 and a['reused_whole_jobs']==0 and a['failed_fits']==0,'New fits, calibrators and exact fitted-state reuse differ')
    require(a['new_policy_count']==204 and a['new_prediction_rows']==557328 and a['new_scored_prediction_rows']==532032 and a['new_blend_rows']==0,'Preserve current prediction accounting')
    require(a['retained_frontier_jobs']==936 and a['retained_frontier_jobs_dispatched']==0 and a['retained_market_jobs']==432 and a['retained_core_jobs']==150 and a['inherited_policies_reused_without_scoring']==1105,'Completed predecessor work must remain preserved')
    require((a['historical_failed_attempts'],a['operationally_finished_attempts'],a['fully_v13_complete_attempts'])==(6,2,0),'Count this partial operational finish once')
    require(len(c['phases'])==2 and c['hard_ceiling']==24 and c['distinct_fit_processes_across_phases']==48,'PID count is not simultaneous concurrency')
    require(c['required_interval_seconds']==180 and c['current_sustained_pass'] is False and c['prior_run_pass_transferred'] is False,'No sustained current-invocation acceptance pass exists')
    require(c['current_gate_status']=='CONDITIONAL_INSUFFICIENT_INDEPENDENT_WORK' and c['optimizer_short_work_reason']=='READY_FIT_INTERVAL_SHORTER_THAN_180_SECONDS','Short-work conditional gate must remain explicit')
    expected=[('JOINT_VALIDATION',204,192,19,48.16231206899829),('JOINT_FROZEN_TEST',102,102,22,30.366388187998382)]
    for phase,(name,jobs,fits,peak,wall) in zip(c['phases'],expected):
        require(phase['name']==name and phase['completed_jobs']==jobs and phase['new_model_fits']==phase['new_calibrator_fits']==fits,'Phase identity or work counts changed')
        require(phase['requested_workers']==phase['admitted_workers']==phase['hard_ceiling']==phase['observed_fit_processes']==24 and phase['native_threads_per_worker']==1,'Admission is separate from observed concurrent fitting')
        require(phase['max_concurrent_fits']==peak and phase['max_concurrent_preparations']==24 and close(phase['dispatch_wall_seconds'],wall),'Preserve measured concurrency and elapsed time')
        require(phase['dispatch_wall_seconds']<180 and phase['remaining_jobs']==0 and phase['saved_prior_pass'] is None and phase['saved_optimizer_prior_pass'] is None,'An exhausted short queue cannot become a sustained pass')
        require(phase['useful_gate_status']=='CONDITIONAL_INSUFFICIENT_INDEPENDENT_WORK' and phase['optimizer_gate_status']=='CONDITIONAL_INSUFFICIENT_READY_FIT_WORK','Current phase gate status changed')
        for key,value in phase.items():
            if key.endswith('_seconds'):
                require(finite(value) and value>=0,'Invalid measured CPU or wall time')
        require(phase['optimizer_cpu_seconds']<phase['owner_tree_cpu_seconds'] and phase['preparation_pending_with_idle_slots_seconds']<=phase['preparation_not_ready_seconds'],'CPU and queue scopes differ')
    require(c['queue_not_ready_includes_busy_preparation'] is True and c['last_phase_label_does_not_extend_fit_time'] is True,'Stale heartbeat and queue metadata need their real scope')
    score=c['scoring']
    require(score['completed_tasks']==612 and score['inherited_policies_reused_without_scoring']==1105 and score['optimizer_occupancy_claimed'] is False,'Scoring is not fitting or all-new inherited work')
    require(close(score['worker_cpu_seconds'],79.263980156) and close(score['batch_wall_seconds_sum'],22.66206241200416) and close(score['coordinator_wall_seconds'],22.69970116400509),'Keep scoring worker CPU and coordinator elapsed time separate')
    require(d['cost']['invoice'] is False and d['cost']['guard_usd']==200 and d['cost']['wall_zero_waives_guard'] is False,'Estimate and budget scope changed')
    require(close(d['cost']['estimated_full_host_usd'],1.0620895516821498) and close(d['cost']['whole_invocation_wall_seconds'],1487.7519011890035),'Use the final observed whole-invocation measurement')
    require(d['cost']['science_stage_estimate_usd']<d['cost']['estimated_full_host_usd'],'Interim science cost is not final closure cost')
    require(s['seasons']==[2024,2025] and s['test_season']==2026 and s['primary_profile']=='50/50' and s['profiles']==PROFILES and s['horizon_minutes']==120,'Keep the original T-120 comparison and validation contract')
    for field in ['test_used_for_selection','season_training_weights','sensitivity_changes_predictions','promotion','full_population_champion_eligible']:
        require(s[field] is False,'Selection, sensitivity, exposure or promotion boundary changed')
    require(s['sensitivity_refits']==0 and s['test_previously_exposed'] is True and s['evidence_class']=='V13_FROZEN_RECONSTRUCTION','These are exposed frozen reconstructions')
    require(s['leader_identity_changes_from_v096']==0 and s['selection_values_unchanged_from_v096'] is True and s['all_policy_count']==1309 and s['new_policy_count']==204,'New work does not imply a new selected leader')
    require(len(s['leaders'])==45 and {(x['profile'],x['target'],x['metric']) for x in s['leaders']}=={(w,t,m) for w in PROFILES for t,m in OBJECTIVES},'Five profiles and nine objectives are required')
    primary={(x['target'],x['metric']):x for x in s['leaders'] if x['profile']=='50/50'}
    for x in s['leaders']:
        require(x['expected_n']==x['scored_n']==[919,934,755] and len(x['annual_values'])==3,'Preserve full known annual denominators')
        require(all(finite(v) and v>=0 for v in x['annual_values']),'Invalid annual metric')
        weight=int(x['profile'].split('/')[0])/100
        require(close(x['selection_score'],weight*x['annual_values'][0]+(1-weight)*x['annual_values'][1]),'Selection uses weighted annual validation metrics only')
        default=primary[x['target'],x['metric']]
        require(type(x['primary_policy_rank']) is int and x['primary_policy_rank']>=1 and x['same_as_predecessor_profile_leader'] is True,'Leader continuity and sensitivity ranks must remain explicit')
        require(x['same_policy_as_primary']==(x['policy_alias']==default['policy_alias']),'Alias identity mismatch')
        if x['same_policy_as_primary']:
            require(x['annual_values']==default['annual_values'],'Sensitivity cannot change a fixed candidate prediction score')
    require(len(s['new_family_best'])==18 and {(x['family'],x['target'],x['metric']) for x in s['new_family_best']}=={(f,t,m) for f in ['XGBoost','CatBoost'] for t,m in OBJECTIVES},'Show both new families on all objectives')
    for row in s['new_family_best']:
        require(row['expected_n']==[919,934,755] and row['primary_rank']>1,'New source ablations did not replace the saved leader')
        require(close(row['selection_score'],sum(row['annual_values'][:2])/2),'New-family representative selection uses validation only')
        require(close(row['all_source_absent_validation_score'],sum(row['all_source_absent_annual_values'][:2])/2),'Source-removal stress uses the same validation aggregation')
    require(p['completed_test_games']==755 and p['pending_test_games']==133 and p['test_policy_count']==p['test_policies_with_full_known_completed_coverage']==1309,'The known completed-game population cannot shrink')
    require(p['official_population_complete'] is False and p['postseason_completeness_proven'] is False and p['full_current_test_reporting_complete'] is False and p['game_rows_removed_for_coverage']==0,'Known-population coverage is not complete official census or full-program reporting')
    require(p['frozen_context_pending_feature_gaps_per_target']==10 and p['current_unresolved_kickoff_count']==10,'Upcoming gaps must remain visible')
    src=d['sources']
    require(src['new_cfbd_calls']==2 and src['new_paid_odds_calls']==src['new_market_provider_requests']==0,'Official census calls differ from odds-provider calls')
    require(src['qualified_current_shards']==src['current_shards_reused']==13378 and src['current_new_shard_conversions']==src['current_normalized_rows_decoded']==src['current_source_bytes_read']==0,'Producer inventory is not current-invocation decoding work')
    require(src['coverage_is_scored_benchmark'] is False and src['historical_possession_created'] is False,'Coverage does not establish predictive benchmarking or original possession')
    require(len(src['historical_t60'])==12 and {x['season'] for x in src['historical_t60']}=={2020,2021,2022,2023},'Historical T-60 coverage cannot become 2024/2025 validation coverage')
    require(src['current_t60_coverage_status']=='VERIFIED_SOURCE_COUNTS_ONLY_NOT_MODEL_ACCEPTANCE' and len(src['completed_horizon_coverage'])==324,'Current source coverage is not a T-60 model result')
    require(len(src['bookmakers'])==18 and len(src['horizons'])==11,'Keep all observed source products and horizons')
    seen=set()
    for row in src['completed_horizon_coverage']:
        key=(row['bookmaker'],row['source_route'],row['season'],row['target'],row['horizon'])
        require(key not in seen,'Duplicate source cell');seen.add(key)
        require(row['horizon'] in ['T60m','T2h'] and row['expected_n']=={2024:919,2025:934,2026:755}[row['season']],'Source coverage cannot shrink the full-game denominator')
        for field in ['feature_qualified_n','reference_n','predictive_baseline_qualified_n','strict_original_availability_qualified_n']:
            require(type(row[field]) is int and 0<=row[field]<=row['expected_n'],'Invalid source coverage count')
        require(row['predictive_baseline_qualified_n']==row['strict_original_availability_qualified_n']==0,'Do not invent provider grading or original possession')
    require(sum(x['horizon']=='T60m' for x in src['completed_horizon_coverage'])==162,'T-60 source subset identity changed')
    st=d['storage']
    require(st['control_zip_bytes']==67412404 and st['new_uploaded_payload_bytes']==219206439 and st['inherited_payload_bytes_not_recopied']==37689243727,'Control ZIP and external payload storage have different scopes')
    require(st['current_run_summary_bytes']==138960 and st['previous_v096_run_summary_bytes']==131276993,'Summary record reduction must use observed bytes')
    require(st['aggregate_science_cap'] is None and st['part_limit_bytes']==512*1024*1024 and st['is_all_scientific_storage'] is False and st['large_unchanged_payloads_repacked'] is False,'Transport part size is not a science budget')
    require(n['release']=='V098' and n['status'] in {'SCOPE_PENDING','IN_PREPARATION','PREPARED_NOT_EXECUTED'},'Unexpected next-preparation status')
    require(n['owner_runs_launched']==n['new_model_fits']==n['provider_retrievals']==n['predecessors_stopped']==0,'This preparation performs no owner execution')
    require(n['target_workers']==12 and n['worker_ceiling']==24 and n['reuse_completed_work'] is True and n['resolves_latest_at_launch'] is True,'Preserve finite continuation and launch-time recovery')
    require(n['horizon_minutes']==60 and n['planned_jobs']==1125 and n['planned_raw_calibrated_policies']==750 and n['planned_fixed_blend_policies']==84 and n['planned_jobs_are_new_fit_promise'] is False,'The T-60 plan is separate from actual T-120 results and new-fit counts')
    require([x['jobs'] for x in n['branches']]==[189,306,252,252,126] and sum(x['jobs'] for x in n['branches'])==1125,'Finite planned branch counts do not close')
    gate=n['campaign_runtime_acceptance']
    require(gate['record']=='T60_CAMPAIGN_RUNTIME_ACCEPTANCE' and gate['current_acceptance']=='UNVERIFIED' and gate['status_without_qualified_window']=='UNVERIFIED_WHOLE_CAMPAIGN_NO_QUALIFIED_180S_WINDOW','Prepared T-60 work has no observed whole-campaign CPU acceptance')
    require(gate['required_representative_seconds']==180 and gate['required_minimum_useful_occupancy']==0.75 and gate['requires_authenticated_current_work_window'] is True,'Campaign acceptance requires a genuine current-work window at the unchanged threshold')
    require(gate['owner_execution_observed'] is False and gate['finite_job_completion_is_cpu_acceptance'] is False and gate['summed_short_waves_establish_pass'] is False and gate['dated_v097_measurements_reclassified'] is False,'Finite job completion and summed short waves cannot establish campaign acceptance or alter dated V097 evidence')
    if n['status']=='PREPARED_NOT_EXECUTED':
        require(n['native_verified'] is True and type(n['canonical_bytes']) is int and n['canonical_bytes']>0 and re.fullmatch('[a-f0-9]{64}',n['canonical_sha256'] or '') and n['native_verified_at'] and n['planned_scope'],'Prepared claim requires sealed native evidence')
    else:
        require(n['native_verified'] is False and n['canonical_bytes'] is None and n['canonical_sha256'] is None and n['native_verified_at'] is None,'Pending preparation cannot claim a sealed executable')
    require(len(d['remaining_work'])>=9 and all(x['status'] in {'BLOCKED','DEFERRED','UNPROVEN','NEXT_FINITE_TRANCHE'} for x in d['remaining_work']),'Unfinished scientific branches must remain visible')
    require(len(d['evidence'])>=10 and all(type(x['bytes']) is int and x['bytes']>0 and re.fullmatch('[a-f0-9]{64}',x['sha256']) for x in d['evidence']),'Missing physical evidence pins')
    return d


def render(data):
    validate(data)
    payload=json.dumps(data,ensure_ascii=False,allow_nan=False,separators=(',',':')).replace('<','\\u003c')
    digest=hashlib.sha256(payload.encode()).hexdigest()
    return TEMPLATE.read_text().replace('__DATA_SHA256__',digest).replace('__DATA__',payload).encode()


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args()
    output=render(json.loads(DATA.read_text()))
    if args.check:
        require(OUTPUT.read_bytes()==output,'Committed HTML differs from exact evidence projection')
    else:
        OUTPUT.parent.mkdir(parents=True,exist_ok=True);OUTPUT.write_bytes(output)
    print(json.dumps({'status':'PASS','bytes':len(output),'sha256':hashlib.sha256(output).hexdigest(),'owner_executions':0}))


if __name__=='__main__':
    main()
