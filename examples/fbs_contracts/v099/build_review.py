"""Render bounded public aggregates; never execute private owner research."""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[3]
DATA=ROOT/'docs/fbs/v099/data/status.json'
OUTPUT=ROOT/'docs/fbs/v099/index.html'
TEMPLATE=Path(__file__).with_name('template.html.in')
KEYS=json.loads(Path(__file__).with_name('projection_keys.json').read_text())
PROFILES=['50/50','40/60','30/70','20/80','10/90']
OBJECTIVES={('winner','accuracy'),('winner','brier'),('winner','log_loss'),
            ('margin','mae'),('margin','rmse'),('margin','crps'),('total','mae'),('total','rmse'),('total','crps')}

def require(value,message):
    if not value:raise ValueError(message)

def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
def close(a,b):return type(a)in(int,float) and type(b)in(int,float) and math.isclose(a,b,rel_tol=1e-12,abs_tol=1e-12)

def boundary(value,path='$'):
    if isinstance(value,dict):
        allowed=set(KEYS.get(path,[]))
        require(set(value)<=allowed,'Unknown public projection fields: '+path)
        if path!='$.sources.providers[]':require(set(value)==allowed,'Missing public projection fields: '+path)
        for key,child in value.items():boundary(child,path+'.'+key)
    elif isinstance(value,list):
        for child in value:boundary(child,path+'[]')
    elif isinstance(value,float):require(math.isfinite(value),'Nonfinite public value')

def validate(d):
    boundary(d)
    raw=json.dumps(d,ensure_ascii=False,allow_nan=False)
    require(not re.search(r's3://|/home/|sagemaker|arn:aws|api[_-]?key|secret[_-]?key|circa|model_id|game_id|owner_relative_path|feature_names|raw_quotes|\.pyz',raw,re.I),'Private or out-of-scope material')
    require(d['schema']=='fbs.public.actual-and-continuation.v099' and d['owner']=='FBS','Wrong owner or schema')
    require(d['publication']=={'source_only':True,'merged':False,'website_deployed':False,'production_promoted':False},'Source review is not deployment')
    a,s,c,p,n=d['execution'],d['selection'],d['cpu'],d['population'],d['next_preparation']
    require(a['release']=='V098' and a['run_id']=='20261118T223005Z-0b62e1bc39-fbs098','Wrong observed invocation')
    require(a['child_exit_code']==0 and a['supervisor_status']=='VERIFIED_RETURN_PUBLICATION_FINISHED','Wrong observed closure')
    require(a['operationally_finished'] and a['return_integrity_verified'] and a['resumable'] and a['scientific_complete'] is False,'Do not conflate operational and scientific completion')
    require((a['registered_jobs'],a['completed_jobs'],a['validation_jobs'],a['frozen_test_jobs'])==(1125,1125,750,375),'Wrong finite fitting counts')
    require((a['new_model_fits'],a['new_calibrator_fits'],a['reused_fit_states'],a['failed_fits'])==(1113,1113,12,0),'Fits/calibrators/reuse must remain distinct')
    require((a['new_policy_count'],a['raw_calibrated_policies'],a['fixed_blend_policies'])==(834,750,84),'Policy counts do not close')
    require((a['new_prediction_rows'],a['new_scored_prediction_rows'])==(2278488,2175072),'Wrong forecast/scoring counts')
    require(a['preserved_earlier_horizon_policies']==1309 and a['earlier_horizon_minutes']==120,'Older horizon must remain separate')
    require((a['new_operational_failures'],a['new_operational_finishes'],a['new_full_scientific_completions'])==(0,1,0),'V098 is not another operational failure')
    require(len(a['families'])==7 and sum(x['jobs']for x in a['branches'])==1125,'Seven-family campaign must reconcile')
    require(s['horizon_minutes']==60 and s['validation_seasons']==[2024,2025] and s['test_season']==2026,'Wrong science boundary')
    require(s['profiles']==PROFILES and s['primary_profile']=='50/50','Wrong declared selection profiles')
    require(s['evidence_class']=='V13_FROZEN_RECONSTRUCTION' and s['test_previously_exposed'] is True,'Reconstruction/exposure must be disclosed')
    for field in ('test_used_for_selection','season_training_weights','sensitivity_changes_predictions','original_issued','promotion','full_population_champion_eligible'):
        require(s[field] is False,'Forbidden scientific claim: '+field)
    require(s['sensitivity_refits']==0 and s['all_policy_count']==834,'Evaluation ratios cannot cause refitting')
    require(len(s['leaders'])==45 and {(r['profile'],r['target'],r['metric'])for r in s['leaders']}=={(q,t,m)for q in PROFILES for t,m in OBJECTIVES},'Missing objective/profile leader')
    primary={(r['target'],r['metric']):r for r in s['leaders']if r['profile']=='50/50'}
    seen={}
    for r in s['leaders']:
        require(r['expected_n']==r['scored_n']==[919,934,755],'Cohort denominators cannot shrink')
        require(re.fullmatch(r'T60 research \d{2}',r['policy_alias']) is not None,'Only opaque public aliases are allowed')
        require(len(r['annual_values'])==3 and all(type(v)in(int,float) and math.isfinite(v) and v>=0 for v in r['annual_values']),'Invalid annual metric')
        w=int(r['profile'].split('/')[0])/100
        require(close(r['selection_score'],w*r['annual_values'][0]+(1-w)*r['annual_values'][1]),'Test outcomes cannot select the leader')
        key=(r['policy_alias'],r['target'],r['metric'])
        require(key not in seen or seen[key]==r['annual_values'],'Fixed-candidate scores changed across profiles')
        seen[key]=r['annual_values']
        require(r['same_policy_as_primary']==(r['policy_alias']==primary[r['target'],r['metric']]['policy_alias']),'Alias continuity differs')
        require(type(r['primary_policy_rank']) is int and r['primary_policy_rank']>=1,'Invalid sensitivity rank')
    require(p['annual_completed']==[919,934,755] and p['annual_observed']==[920,934,888] and p['annual_pending']==[1,0,133],'Preserve observed population counts')
    require(p['test_policy_count']==p['test_policies_with_full_observed_completed_coverage']==834,'All policies use the observed completed cohort')
    for field in ('official_population_complete','postseason_completeness_proven','historical_postseason_labels_complete','full_current_test_reporting_complete'):
        require(p[field] is False,'Unproved full population/postseason claim')
    require(p['unresolved_upcoming_kickoffs']==10 and p['game_rows_removed_for_coverage']==0,'Upcoming gaps cannot be erased')
    require(c['release']=='V098' and c['hard_ceiling']==24 and c['current_sustained_pass'] is True and c['current_gate_status']=='PASS_AUTHENTICATED_REAL_180S_WINDOW','Preserve actual current-run CPU acceptance')
    require(c['prior_run_pass_transferred'] is False and c['descriptive_average_is_sustained_gate'] is False,'Means/prior passes cannot replace observed windows')
    require(c['required_interval_seconds']==180 and c['minimum_occupancy']==.75 and len(c['windows'])==2,'Changed sustained-window rule')
    for w in c['windows']:
        require(w['representative_seconds']>=180 and w['selected_worker_capacity']==24 and w['useful_worker_cpu_occupancy']>=.75 and w['real_fits_completed_in_window']>0,'Unqualified real-work pass')
        require(0<=w['fit_only_cpu_occupancy']<=w['useful_worker_cpu_occupancy']<=1.05,'Optimizer CPU cannot exceed useful CPU')
    costs=d['cost'];require(close(costs['estimated_compute_usd'],costs['elapsed_seconds_through_measurement']*costs['rate_usd_per_full_host_hour']/3600),'Cost rate/time mismatch')
    require(costs['estimate_is_invoice'] is False and costs['guard_usd']==200 and costs['wall_zero_waives_guard'] is False,'Cost protection or invoice claim changed')
    source=d['sources']
    require(source['qualified_grid_cells']+source['explicit_missing_grid_cells']+source['outside_feature_history_cells']==source['total_grid_cells']==412371,'Grid counts do not reconcile')
    require(source['qualified_grid_cells']==62956 and source['explicit_missing_grid_cells']==348794 and source['outside_feature_history_cells']==621,'Changed authenticated coverage')
    require(source['historical_possession_created'] is False and source['coverage_is_scored_benchmark'] is False,'Coverage does not prove original issues or benchmark quality')
    require(source['admitted_bookmaker_slots']==17 and source['unsupported_slots']==11 and len(source['coverage'])==9,'Incomplete source-coverage projection')
    for row in source['coverage']:
        require(row['rows']=={2024:920,2025:934,2026:888}[row['season']] and row['rows_with_any_qualified_t60_source']+row['all_sources_absent_rows']==row['rows'],'Source populations cannot shrink')
    require([x['name']for x in source['providers']]==['DraftKings','Kalshi','Polymarket Global','Polymarket US'],'Keep provider products separate')
    require(source['providers'][0]['qualified_grid_cells']==9122 and source['providers'][0]['qualified_pretest_grid_cells']==7371,'Wrong source cell counts')
    require(all(x['status']=='NATIVE_CONTRACT_ADAPTER_BLOCKED' for x in source['providers'][1:]),'Native contract gaps cannot become source admission')
    st=d['storage']
    require(st['control_zip_bytes']==72851201 and st['return_sha256']=='a74a9d1ed2d41dc81f442bdaae7e18e2911d5e8c88c146023970c027ba5baec4','Wrong verified return')
    require(st['new_uploaded_payload_bytes']==4614872404 and st['inherited_payload_bytes_not_recopied']==38322889879,'Compact ZIP is not all storage')
    require(st['aggregate_science_cap'] is None and st['part_limit_bytes']==512*1024*1024 and st['large_unchanged_payloads_repacked'] is False and st['verification_is_scientific_fitting'] is False,'Storage and work scopes changed')
    require(st['checkpoint_receipts']==5485 and st['physical_dependency_pins']==58005 and st['final_identity_verification_seconds']<st['checkpoint_collection_seconds'],'Preserve measured custody bottleneck')
    require(n['release']=='V099' and n['status'] in ('IN_PREPARATION','PREPARED_NOT_EXECUTED'),'Wrong next preparation')
    require(n['owner_runs_launched']==n['new_model_fits']==n['provider_retrievals']==n['predecessors_stopped']==0,'Preparation executes no owner science')
    require(n['target_workers']==12 and n['worker_ceiling']==36 and n['explicit_worker_limit_is_hard_ceiling'] is True,'Wrong worker admission contract')
    require(n['reuse_completed_work'] and n['resolves_latest_at_launch'] and n['new_work_is_scoring_not_optimizer_fitting'],'Completed fits must remain preserved')
    require((n['planned_forecast_policies'],n['planned_validation_forecast_tasks'],n['planned_test_forecast_tasks'],n['planned_uncertainty_tasks'],n['planned_objective_comparisons'])==(100,200,100,300,900),'Finite new scoring counts changed')
    require(n['planned_new_estimator_fits']==n['planned_new_calibrator_fits']==0,'Scoring is not new fitting')
    require(n['prior_cpu_pass_transferred'] is False and n['current_runtime_acceptance']=='NOT_EXECUTED' and n['required_representative_seconds']==180 and n['required_minimum_occupancy']==.75,'Preparation cannot claim future CPU acceptance')
    if n['status']=='PREPARED_NOT_EXECUTED':
        require(n['native_verified'] is True and type(n['canonical_bytes']) is int and n['canonical_bytes']>0 and re.fullmatch('[a-f0-9]{64}',n['canonical_sha256'] or '') and n['native_verified_at'],'Prepared claim requires native release verification')
    else:require(n['native_verified'] is False and n['canonical_bytes'] is None and n['canonical_sha256'] is None and n['native_verified_at'] is None,'Pending preparation cannot claim sealed release')
    require(len(d['evidence'])==10 and all(type(e['bytes'])is int and e['bytes']>0 and re.fullmatch('[a-f0-9]{64}',e['sha256'])for e in d['evidence']),'Evidence digest missing')
    return d

def render(data):
    validate(data)
    payload=json.dumps(data,ensure_ascii=False,separators=(',',':'),allow_nan=False).replace('<','\\u003c')
    digest=hashlib.sha256(payload.encode()).hexdigest()
    return TEMPLATE.read_text().replace('__DATA_SHA256__',digest).replace('__DATA__',payload).encode()

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args()
    raw=render(json.loads(DATA.read_text()))
    if args.check:require(OUTPUT.read_bytes()==raw,'HTML differs from exact projection')
    else:OUTPUT.parent.mkdir(parents=True,exist_ok=True);OUTPUT.write_bytes(raw)
    print(json.dumps({'status':'PASS','bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'owner_executions':0}))

if __name__=='__main__':main()
