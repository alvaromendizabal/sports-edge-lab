"""Public accounting contract for a completed study inside a partial continuation."""
import hashlib, json, math
from pathlib import Path
from point_markets import require
HERE=Path(__file__).parent
OWNER='a6ff83679e7e8f995951f34990c6ea01d8d2b8bbc948eebbe6853968d1b51293'
def validate_owner_study(d):
 require(d['schema']=='sports-edge-lab.nfl.owner-study.n043.v1' and d['owner_return_sha256']==OWNER,'Owner identity differs')
 require(d['owner_status']=='PARTIAL_OWNER_CONTINUATION_REPAIR_REQUIRED' and d['owner_research_acceptance'] is False,'A completed arm cannot promote the complete pipeline')
 require(d['completed_historical_cells']==d['declared_historical_cells']==d['families']*d['rooted_feature_blocks']*d['targets']*d['evaluation_seasons']==1152,'Declared grid closure differs')
 require(d['new_native_fits']==d['historical_native_fits']+d['additional_unique_rolling_native_fits']==1605,'Unique native accounting differs')
 require(d['rolling_jobs_completed']-d['rolling_exact_annual_identity_reuses']==d['additional_unique_rolling_native_fits']==453,'Reused rolling identities cannot count as new')
 require(d['new_total_fits']==d['new_native_fits']+d['new_stack_fits']==1614,'Native and stack accounting differs')
 require(d['new_stack_fits']==9 and d['native_failures']==d['blocked_cells']==d['protected_original_refits']==0,'Failure or original-refit accounting differs')
 require(d['new_designation_forecasts']==d['new_fresh_current_rolling_rows']==d['final_hour_qualified_cards']==0,'Reconstructions cannot become new issues or recommendations')
 require(d['actual_other_target_rows']==d['actual_other_distinct_games']*3*2==174,'Target rows cannot become distinct games')
 require(d['automatic_promotion'] is False and d['selected_recipes_pre2024'] is True and d['old_metrics_rewritten'] is False,'Selection or promotion boundary differs')
 require(d['global_fastest_claimed'] is False and d['cost_usd'] is None,'Unsupported speed or cost claim')
 require(d['injury_report_teams']==26 and d['injury_team_slots']==30 and set(d['injury_missing_teams'])=={'BUF','CHI','MIN','SEA'},'Unknown reports cannot become healthy teams')
 require(len(d['selected_metrics'])==6,'Missing selected target/period')
 seen=set()
 for r in d['selected_metrics']:
  key=(r['target'],r['period']);require(key not in seen,'Duplicate selected cohort');seen.add(key)
  require(r['model_family']=='ExtraTrees' and r['games']>0,'Unsupported selected model or empty metric')
  for k in ('log_loss','brier','mae'):
   require(r[k] is None or (type(r[k]) in (float,int) and math.isfinite(r[k]) and r[k]>=0),'Invalid metric')
  require((r['target']=='winner')==(r['mae'] is None),'Winner and point metrics cannot be substituted')
 require(len(d['limitations'])>=6 and d['current_sources_all_latest_claimed'] is False,'Material limitations omitted')
 return {'n043_owner_study_validation':'PASS','n043_new_native_fits':1605,'n043_new_stack_fits':9,'n043_historical_cells':1152,'n043_new_designation_issues':0,'n043_overall_accepted':False}
def load_owner_study():
 p=HERE/'owner_study_n043.json';d=json.loads(p.read_text());return d,{**validate_owner_study(d),'n043_owner_study_sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
