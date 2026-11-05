"""Separate issued challenger cards; never overwrite original model streams."""
import hashlib,json,math,re
from pathlib import Path
from datetime import timedelta
from market_clock import instant
from point_markets import require,scalar
HERE=Path(__file__).resolve().parent
MODEL_ID='experimental_injury_n041'
ROOT_FIELDS={'schema','owner_return_sha256','source_member_sha256','as_of','new_selected_forward_fits','restored_selected_forward_fits','new_issue_target_rows','historical_metrics_changed','owner_pipeline_accepted','cards','limitations','source_census','changes_since_n040'}
CARD_FIELDS={'game_id','model_id','model_label','origin','pick','pick_probability','home_win_probability','home_margin','total','home_score_center','away_score_center','actual_issue_at','source_asof','base_feature_asof_at','injury_cutoff_at','injury_observed_at','fit_completed','horizon','issue_class','full_pipeline_selection_qualified','final_hour_qualified_card','injury_inputs_verified','injury_report_status','injury_source_report_team_count','injury_source_excluded_rows','announced_starter_verified','reserve_status_verified','target_feature_views','margin_interval','total_interval','correct','unavailable_reason'}
NESTED={'injury_source_report_team_count','target_feature_views','margin_interval','total_interval'}
VIEWS={'winner':'matched_base_no_direct_injury_fields','margin':'injury_augmented_with_unknown_report_flags','total':'injury_augmented_with_unknown_report_flags'}

def validate_injury_refresh(data,coverage):
 require(set(data)==ROOT_FIELDS,'Unknown experimental issue fields')
 require(data['schema']=='sports-edge-lab.nfl.injury-refresh.n041.v1','Unknown experimental issue schema')
 require(data['owner_return_sha256']=='144da21ccb8cc133ff68cd9a5e8c048629c4c016ba8ba1e4758a21330ef2541c'and data['source_member_sha256']=='b036fe864604aba2a02c5e2fe81cf3d95fe5cfcb75ff5ca0bbc6dfa348582320','Issued evidence identity differs')
 require(data['as_of']=='2026-11-05T02:26:17.945056+00:00','Exact owner issue clock differs')
 require(type(data['new_selected_forward_fits'])is int and data['new_selected_forward_fits']==0 and data['restored_selected_forward_fits']==3 and data['new_issue_target_rows']==87 and data['historical_metrics_changed']is False and data['owner_pipeline_accepted']is False,'Prior fitted challenger is not an accepted production model')
 for key in ROOT_FIELDS-{'cards','limitations','source_census','changes_since_n040'}:scalar(data[key])
 require(isinstance(data['limitations'],list)and len(data['limitations'])>=6,'Missing issue limitations')
 for value in data['limitations']:scalar(value)
 require(isinstance(data['cards'],list)and len(data['cards'])==29,'Exact issue population is29games')
 games={g['game_id']:g for g in coverage['all_games']};seen=set();partial=0
 for r in data['cards']:
  require(set(r)==CARD_FIELDS,'Unknown experimental card field')
  for k,v in r.items():
   if k not in NESTED:scalar(v)
  gid=r['game_id'];require(gid in games and gid not in seen,'Unknown/duplicate experimental game');seen.add(gid);g=games[gid]
  require(not g['completed']and g['actual']is None and g['week']in(9,10),'Completed or unrelated game cannot receive this early issue')
  require(r['model_id']==MODEL_ID and r['model_label']=='Latest injury refresh'and r['origin']=='registered_pre2024_recipe_reused_owner_fit','Experimental role changed')
  require(r['correct']is None and r['unavailable_reason']is None,'No invented result or unavailable state')
  for k in ('full_pipeline_selection_qualified','final_hour_qualified_card','injury_inputs_verified','announced_starter_verified','reserve_status_verified'):require(r[k]is False,'Unverified readiness/starter/IR cannot be promoted')
  require(r['horizon']=='EARLY_BEFORE_T2'and r['issue_class']=='EARLY_FORWARD_RESEARCH_ISSUE','An early issue cannot become a final-hour recommendation')
  require(r['base_feature_asof_at']=='2026-11-04T01:52:35.279297+00:00' and r['injury_cutoff_at']=='2026-11-05T02:25:58.436720+00:00','A fresh injury clock cannot refresh retained base features')
  issued=instant(r['actual_issue_at']);cut=instant(r['injury_cutoff_at']);require(instant(r['source_asof'])==instant(r['base_feature_asof_at'])<=cut<=issued==instant(data['as_of'])<instant(g['kickoff_utc'])-timedelta(hours=2),'Base/injury/issue/kickoff clocks differ')
  require(instant(r['fit_completed'])<=issued,'Fit completes after issue')
  p=r['home_win_probability'];require(type(p)in(int,float)and math.isfinite(p)and 0<=p<=1 and abs(p*1000-round(p*1000))<1e-7,'Rounded probability required')
  require(r['pick']==(g['home']if p>=.5 else g['away'])and abs(r['pick_probability']-max(p,1-p))<1e-7,'Pick/probability/team binding differs')
  for k in ('home_margin','total','home_score_center','away_score_center'):
   v=r[k];require(type(v)in(int,float)and math.isfinite(v)and abs(v*10-round(v*10))<1e-7,'Rounded finite point center required')
  require(abs(r['home_score_center']+r['away_score_center']-r['total'])<=.11 and abs(r['home_score_center']-r['away_score_center']-r['home_margin'])<=.11,'Derived score centers fail rounding reconciliation')
  teams=r['injury_source_report_team_count'];require(isinstance(teams,dict)and set(teams)=={g['home'],g['away']}and all(type(n)is int and n>=0 for n in teams.values()),'Report counts need exact event teams')
  require(r['injury_source_excluded_rows']==0,'No invented exclusion reconciliation')
  if any(teams.values()):
   require(g['week']==9 and r['injury_report_status']=='PARTIAL_LISTED_REPORTS','Listed reports cannot become complete coverage')
   require(r['injury_observed_at'] is not None and instant(r['injury_observed_at'])<=cut,'Observed injury clock crosses cutoff');partial+=1
  else:require(r['injury_observed_at'] is None and r['injury_report_status']=='NO_CURRENT_REPORTS_ADMITTED','Missing reports cannot become healthy or complete')
  require(instant(r['fit_completed'])<instant('2026-11-05T00:00:00Z'),'Restored fit cannot be a new current-cycle fit')
  require(r['target_feature_views']==VIEWS,'Winner and point injury views must remain distinct')
  for target,fields in [('margin',{'lower','upper','nominal_coverage'}),('total',{'lower','upper','interval_note'})]:
   interval=r[target+'_interval'];require(isinstance(interval,dict)and set(interval)==fields,'Unknown reference interval fields')
   for v in interval.values():scalar(v)
   require(all(type(interval[k])in(int,float)and math.isfinite(interval[k])for k in('lower','upper'))and interval['lower']<interval['upper'],'Invalid reference interval')
   if target=='margin':require(interval['nominal_coverage']==.8,'Registered nominal interval differs')
   else:require(interval['interval_note']=='Fixed pre-2024 residual quantiles; no coverage guarantee','Interval qualification differs')
 require(data['source_census']=={'listed_rows':266,'admitted_rows':266,'excluded_identity_rows':0,'team_sections':26,'team_slots':30,'both_team_report_games':12,'one_team_report_games':2,'no_team_report_games':1,'missing_teams':['BUF','CHI','MIN','SEA'],'full_roster_coverage':False,'announced_starter_verified':False,'reserve_status_verified':False},'Partial source census cannot be promoted')
 require(data['changes_since_n040']=={'winner':0,'margin':1,'total':1,'new_fits':0},'Changed issue values cannot become new fits')
 counts=[r['injury_source_report_team_count'] for r in data['cards'] if games[r['game_id']]['week']==9]
 require(sum(sum(x.values()) for x in counts)==266 and sum(all(x.values()) for x in counts)==12,'Listed report counts do not reconcile')
 require(partial==14,'Exact partial injury-source cohort differs')
 require(sum(games[k]['week']==9 for k in seen)==15 and sum(games[k]['week']==10 for k in seen)==14,'Exact issued week cohort differs')
 return {'injury_n041_status':'PUBLIC_SEPARATE_EARLY_REFRESH_VALIDATED','injury_n041_games':29,'injury_n041_target_rows':87,'injury_n041_prior_selected_forward_fits':3,'injury_n041_current_publication_new_fits':0,'injury_n041_owner_new_issue_rows':87,'injury_n041_owner_pipeline_accepted':False,'injury_n041_partial_report_games':14,'injury_n041_unknown_report_games':15}

def load_injury_refresh(coverage):
 p=HERE/'injury_refresh_n041.json';data=json.loads(p.read_text());return data,{**validate_injury_refresh(data,coverage),'injury_n041_sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
