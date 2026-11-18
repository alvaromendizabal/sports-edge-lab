"""Build the NBA recovery/validation review from public aggregate evidence only."""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
FORBIDDEN_KEYS = {'recipe_id','model_id','feature_names','feature_values','feature_columns',
 'ordered_features','transforms','hyperparameters','calibration_parameters','model_weights',
 'raw_payload','raw_record','credentials','access_token','account_id','source_path','private_path',
 'player_id','event_id','game_id','predictions','prediction_rows','private_alias_map'}
FORBIDDEN_TEXT = ('circa','s3://','arn:aws:','/home/','/workspace/','nba:espn:event:',
 'aws_access_key','sagemaker-sports-edge-lab-','.pyz','AKIA')
OBJECTIVES = {'winner_accuracy','winner_log_loss','winner_brier','margin_mae','margin_rmse',
 'total_mae','total_rmse'}
POLICIES = {'50/50':(.5,.5),'40/60':(.4,.6),'30/70':(.3,.7),'20/80':(.2,.8),'10/90':(.1,.9)}

def require(condition, message):
 if not condition: raise ValueError(message)

def validate(value):
 def visit(node):
  if isinstance(node,dict):
   require(not FORBIDDEN_KEYS.intersection(node),'Private payload field')
   if 'public_model_alias' in node:
    require(re.fullmatch(r'NBA-R\d{3}',node['public_model_alias']) is not None,'Private model identity')
   for child in node.values():visit(child)
  elif isinstance(node,list):
   for child in node:visit(child)
  elif isinstance(node,str):
   require(not any(s.lower() in node.lower() for s in FORBIDDEN_TEXT),'Private or wrong-sport payload content')
  elif isinstance(node,float):require(math.isfinite(node),'Nonfinite metric')
 visit(value)
 require(value['schema']=='sports_edge_lab.nba.b096.review_public.v1' and value['owner']=='NBA','Wrong public schema')
 sel=value['selection']
 require(sel['validation_seasons']==['2024-25','2025-26'] and sel['test_season']=='2026-27','Season split changed')
 require(sel['primary_policy']=='50/50','Primary selection policy changed')
 require(sel['test_outcomes_used_for_selection'] is False and sel['season_training_row_reweighting'] is False,'Test selection or training reweighting claim')
 require(sel['full_season_champions_certified']==0 and sel['automatic_promotions']==0,'Unsupported champion promotion claim')
 require(sel['strict_historical_point_in_time_qualified'] is False,'Unsupported historical qualification')
 pops={p['season']:p for p in value['populations']}
 require(set(pops)=={'2024-25','2025-26','2026-27'},'Missing season population')
 for season,n in [('2024-25',1314),('2025-26',1315),('2026-27',205)]:
  p=pops[season]
  require(p['completed_games']==n and p['regular_games']+p['playoff_games']==n,'Changed declared population')
  require(p['full_season_census_verified'] is False and p['unknown_missing_count'] is None,'Unknown full-season gaps relabeled complete')
  require(re.fullmatch('[a-f0-9]{64}',p['population_sha256']) is not None,'Invalid population hash')
 roles=value['objective_leaders']
 require({(r['objective'],r['horizon_minutes']) for r in roles}=={(o,h) for o in OBJECTIVES for h in (60,120)} and len(roles)==14,'Missing or duplicate objective role')
 for role in roles:
  require(role['selection_uses_test_outcomes'] is False,'Test selection claim')
  require(len(role['annual_metrics'])==3,'Missing annual metric')
  annual={a['season']:a for a in role['annual_metrics']}
  require(set(annual)==set(pops),'Missing annual season')
  for season,a in annual.items():
   require(a['games']==a['required_games']==pops[season]['completed_games'] and a['population_sha256']==pops[season]['population_sha256'],'Inconsistent metric population')
   require(isinstance(a['value'],(int,float)) and math.isfinite(a['value']),'Missing or invalid annual metric')
  is_rmse=role['objective'].endswith('_rmse')
  require(role['saved_score_aggregation']==('Root weighted annual MSE' if is_rmse else 'Weighted annual metric'),'RMSE aggregation mislabeled')
  require(role['v13_rmse_policy_satisfied']==(not is_rmse),'Unsupported RMSE policy qualification')
  expected=math.sqrt(.5*annual['2024-25']['value']**2+.5*annual['2025-26']['value']**2) if is_rmse else .5*annual['2024-25']['value']+.5*annual['2025-26']['value']
  require(math.isclose(role['selection_score'],expected,rel_tol=1e-12,abs_tol=1e-12),'Selection score differs from annual validation metrics')
 weights=value['weight_sensitivity']
 require(len(weights)==70 and len({(r['policy'],r['objective'],r['horizon_minutes']) for r in weights})==70,'Incomplete sensitivity grid')
 for r in weights:
  require(r['policy'] in POLICIES and r['objective'] in OBJECTIVES and r['horizon_minutes'] in (60,120),'Invalid sensitivity identity')
  earlier,later=POLICIES[r['policy']]
  require((r['earlier_validation_weight'],r['later_validation_weight'])==(earlier,later),'Invalid sensitivity weights')
  require(r['estimator_refits']==0 and r['predictions_changed'] is False,'Selection sensitivity refitted models')
  require(set(r['leader_annual_values'])=={'2024-25','2025-26'},'Test outcomes present in sensitivity score')
  is_rmse=r['objective'].endswith('_rmse')
  require(r['saved_score_aggregation']==('Root weighted annual MSE' if is_rmse else 'Weighted annual metric'),'Sensitivity RMSE aggregation mislabeled')
  expected=math.sqrt(earlier*r['leader_annual_values']['2024-25']**2+later*r['leader_annual_values']['2025-26']**2) if is_rmse else earlier*r['leader_annual_values']['2024-25']+later*r['leader_annual_values']['2025-26']
  require(math.isclose(r['leader_score'],expected,rel_tol=1e-12,abs_tol=1e-12),'Sensitivity score inconsistent with validation')
  require(r['primary_leader_still_tied_for_first']==(r['primary_leader_rank']==1),'Sensitivity rank disagreement')
 b=value['latest_completed_recovery']
 require(b['release']=='B094' and b['execution_complete'] is True and b['research_program_complete'] is False,'Recovery relabeled complete program')
 require(b['new_estimator_fits']==b['new_calibration_fits']==b['new_provider_requests']==0,'Recovery mislabeled new fitting or retrieval')
 require(b['preserved_base_states']==1644 and b['preserved_prediction_variants']==3300,'Changed preserved science count')
 require(b['uncertainty_completed']==3300 and b['uncertainty_new']+b['uncertainty_reused']==3300 and b['uncertainty_failed']==b['uncertainty_unadmitted']==0,'Uncertainty accounting mismatch')
 require(b['measured_full_capacity_passes']==0,'Unsupported full-capacity pass')
 require(b['original_models_modified'] is False and b['selection_or_population_changed'] is False,'Recovery changed original science')
 require(b['physical_parts']==7 and b['logical_archive_bytes']==3258435177 and b['maximum_part_bytes']<=512*1024*1024,'Incorrect return representation')
 require(b['actual_invoiced_cost_usd'] is None,'Estimated cost relabeled invoice')
 attempts=value['latest_owner_executions']
 require(len(attempts)==2 and [a['attempt'] for a in attempts]==[1,2],'B095 attempt accounting mismatch')
 for a in attempts:
  require(a['release']=='B095' and a['status']=='PARTIAL_RESUMABLE' and a['execution_complete'] is False,'Failed owner execution relabeled complete')
  require(a['failure_stage']=='INITIALIZING' and a['scientific_work_admitted'] is False,'Initialization failure relabeled research')
  require(a['new_estimator_fits'] is None and a['new_calibration_fits'] is None and a['fit_counts_complete'] is False,'Unavailable fit counters replaced with inferred values')
  require(a['new_provider_requests']==0 and a['actual_invoiced_cost_usd'] is None,'Failed attempt creates retrieval or invoice claim')
  require(re.fullmatch('[a-f0-9]{64}',a['report_sha256']) is not None,'Invalid failure report hash')
  require(a['exit_code']==2,'Failed owner exit changed')
 latest=value['latest_verified_return']
 require(latest['release']=='B095' and latest['attempt']==2 and latest['status']=='PARTIAL_RESUMABLE' and latest['execution_complete'] is False,'Verified return relabeled successful execution')
 require(latest['logical_archive_bytes']==19057377 and latest['physical_parts']==1 and latest['payload_count']==16 and latest['physical_representation']=='Single ZIP','Latest return representation mismatch')
 require(latest['logical_archive_sha256']=='45df8f1b2581191cdef27ae2f11ed0dbb421f52ea0cd48957aff929859289f39' and latest['full_archive_and_payload_readback_verified'] is True,'Latest return verification mismatch')
 require(latest['registered_new_estimator_checkpoints']==latest['registered_new_calibration_checkpoints']==0 and latest['preserved_prior_continuation_references'] is True,'Failed attempt changed checkpoint accounting')
 prior=value['prior_execution']
 require(prior['uncertainty_completed']+prior['uncertainty_unadmitted']+prior['uncertainty_failed']==prior['uncertainty_requested'],'Prior uncertainty accounting mismatch')
 require(prior['physical_return_sealed'] is False and prior['exit_code']==2,'Prior failed sealing relabeled success')
 prepared=value['prepared_successor']
 require(prepared['release']=='B096','Successor identity changed')
 require(prepared['owner_execution_started'] is False and prepared['new_research_fits']==prepared['new_forecasts']==prepared['new_source_requests']==0,'Preparation mislabeled owner execution')
 sources=value['sources']
 require(sources['all_relevant_data_acquired'] is False and sources['live_data'] is False,'Unsupported complete/live source claim')
 require(sources['bookmakers_catalogued']==len(sources['bookmaker_counts']),'Bookmaker catalog count mismatch')
 require(sources['bookmakers_with_any_qualified_cell']==sum(b['qualified']>0 for b in sources['bookmaker_counts']),'Bookmaker coverage count mismatch')
 for c in sources['named_provider_coverage']:
  require(c['source'] in ('draftkings','kalshi','polymarket_international','polymarket_us'),'Unexpected named comparison source')
  require(c['qualified_n']+c['missing_n']==c['population_n'],'Source missingness denominator mismatch')
  require(0<=c['archive_replay_n']<=c['qualified_n'] and 0<=c['current_capture_n']<=c['qualified_n'],'Source evidence class mismatch')
 require(value['publication']['research_executions_during_preparation']==value['publication']['model_fits_during_preparation']==value['publication']['provider_requests_during_preparation']==0,'Publication creates research claim')
 return value

def build(root=ROOT):
 value=validate(json.loads((root/'b095_review.json').read_text()))
 raw=json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).replace('<','\\u003c')
 template=(root/'b095_review.template.html').read_text()
 require(template.count('__B095_PUBLIC_JSON__')==1,'Missing unique data slot')
 result=template.replace('__B095_PUBLIC_JSON__',raw).encode()
 require(b'fetch(' not in result and b'<script src' not in result,'Remote dependency in offline report')
 return result

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args()
 data=build();target=ROOT/'b095_review.html'
 if args.check:
  require(target.read_bytes()==data,'Generated review differs from public evidence/template')
  print('B095 deterministic public review verified')
 else:
  target.write_bytes(data);print('B095 aggregate review generated; no model or source execution')

if __name__=='__main__':main()
