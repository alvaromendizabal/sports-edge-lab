"""Public accounting for completed injury research, separate from forecast promotion."""
import hashlib,json,math
from pathlib import Path
from point_markets import require
HERE=Path(__file__).parent

def validate_owner_study(d):
 require(set(d)=={'schema','owner_return_sha256','owner_status','study_status','owner_research_acceptance','first_error','families','rooted_feature_blocks','targets','evaluation_seasons','declared_historical_cells','completed_historical_cells','rolling_jobs_completed','restored_designation_native_identities','new_native_fits','new_stack_fits','new_total_fits','restored_all_fitted_identities','native_failures','rolling_failures','blocked_cells','protected_original_refits','new_designation_forecasts','actual_other_target_rows','actual_other_distinct_games','final_hour_qualified_cards','automatic_promotion','selected_recipes_pre2024','old_metrics_rewritten','summary_elapsed_seconds','study_elapsed_seconds','study_peak_process_rss_bytes','global_fastest_claimed','cost_usd','injury_report_teams','injury_team_slots','injury_missing_teams','selected_metrics','current_sources_all_latest_claimed','limitations'},'Public study field boundary differs')
 from current_issues_n045 import OWNER
 require(d['schema']=='sports-edge-lab.nfl.owner-study.n045.v1' and d['owner_return_sha256']==OWNER,'Owner identity differs')
 require(d['owner_status']=='OWNER_CONTINUATION_REPORTED_WITH_EXPLICIT_COVERAGE' and d['study_status']=='COMPLETE_ELIGIBLE_DESIGNATION_RECONSTRUCTION','Study completion status differs')
 require(d['owner_research_acceptance'] is False and d['first_error'] is None,'Completion is not pipeline acceptance')
 require(d['completed_historical_cells']==d['declared_historical_cells']==d['families']*d['rooted_feature_blocks']*d['targets']*d['evaluation_seasons']==1152,'Declared grid closure differs')
 require(d['new_native_fits']==1029 and d['new_stack_fits']==9 and d['new_total_fits']==1038,'Actual new fit accounting differs')
 require(d['restored_designation_native_identities']==576 and d['restored_all_fitted_identities']==3355 and d['rolling_jobs_completed']==462,'Restored identities or job counts cannot become new fits')
 require(all(d[k]==0 for k in ['native_failures','rolling_failures','blocked_cells','protected_original_refits','new_designation_forecasts','final_hour_qualified_cards']),'Failure, original-refit or issue count differs')
 require(d['actual_other_target_rows']==d['actual_other_distinct_games']*3*3==261,'Target rows cannot become independent games')
 require(all(d[k] is False for k in ['automatic_promotion','old_metrics_rewritten','global_fastest_claimed','current_sources_all_latest_claimed']) and d['selected_recipes_pre2024'] is True,'Selection, preservation or unsupported claim differs')
 require(d['cost_usd'] is None and d['study_peak_process_rss_bytes']==3478036480 and abs(d['study_elapsed_seconds']-1091.8568541309942)<1e-6 and abs(d['summary_elapsed_seconds']-2479.060324922)<1e-6,'Measured operations differ')
 require(d['injury_report_teams']==28 and d['injury_team_slots']==30 and d['injury_missing_teams']==['BUF','MIN'],'Unknown reports cannot become health')
 expected=[('winner','2024/25',569,.6252358785731975,.21742007829866491,385,None),('winner','2026',119,.6633111879120899,.23587125857433322,78,None),('margin','2024/25',570,None,None,None,10.004398419833311),('margin','2026',120,None,None,None,10.066062735604351),('total','2024/25',570,None,None,None,10.29893753676243),('total','2026',120,None,None,None,11.394802742062545)]
 require(len(d['selected_metrics'])==6,'Missing selected metric')
 for r,e in zip(d['selected_metrics'],expected):
  require(set(r)=={'target','period','model_family','games','log_loss','brier','correct','mae'} and r['model_family']=='ExtraTrees','Unknown metric fields or selected family')
  require(tuple(r[k] for k in ['target','period','games','log_loss','brier','correct','mae'])==e,'Metric cohort or value differs')
 require(len(d['limitations'])>=8 and all(type(x)is str for x in d['limitations']),'Missing material limitations')
 return {'n045_owner_study_validation':'PASS','n045_new_native_fits':1029,'n045_new_stack_fits':9,'n045_historical_cells':1152,'n045_new_designation_issues':0,'n045_overall_accepted':False}

def load_owner_study():
 p=HERE/'owner_study_n045.json';d=json.loads(p.read_text());return d,{**validate_owner_study(d),'n045_owner_study_sha256':hashlib.sha256(p.read_bytes()).hexdigest()}


def load_selected_metrics():
 p=HERE/'designation_metrics_n045.json';d=json.loads(p.read_text())
 require(set(d)=={'schema','owner_return_sha256','rows','automatic_promotion','original_metrics_modified','newly_issued_rows_from_this_study'},'Selected metrics boundary differs')
 require(hashlib.sha256(json.dumps(d,sort_keys=True,separators=(',',':')).encode()).hexdigest()=='48dabaed88d82a9fa92f64c3f5e65008e0c669cc748fd121297de392ade310b5','Selected metric identities or values differ')
 require(len(d['rows'])==27 and len({(r['origin'],r['target'],r['season'])for r in d['rows']})==27,'Origin/target/season grid differs')
 return d,{'n045_selected_origin_metric_rows':27,'n045_selected_metrics_sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
