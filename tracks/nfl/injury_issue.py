"""Separate issued challenger cards; never overwrite original model streams."""
import hashlib,json,math,re
from pathlib import Path
from datetime import timedelta
from market_clock import instant
from point_markets import require,scalar
HERE=Path(__file__).resolve().parent
MODEL_ID='experimental_injury_issue'
ROOT_FIELDS={'schema','owner_return_sha256','source_member_sha256','as_of','new_selected_forward_fits','owner_pipeline_accepted','cards','limitations'}
CARD_FIELDS={'game_id','model_id','model_label','origin','pick','pick_probability','home_win_probability','home_margin','total','home_score_center','away_score_center','actual_issue_at','source_asof','base_feature_asof_at','injury_cutoff_at','injury_observed_at','fit_completed','horizon','issue_class','full_pipeline_selection_qualified','final_hour_qualified_card','injury_inputs_verified','injury_report_status','injury_source_report_team_count','injury_source_excluded_rows','announced_starter_verified','reserve_status_verified','target_feature_views','margin_interval','total_interval','correct','unavailable_reason'}
NESTED={'injury_source_report_team_count','target_feature_views','margin_interval','total_interval'}
VIEWS={'winner':'matched_base_no_direct_injury_fields','margin':'injury_augmented_with_unknown_report_flags','total':'injury_augmented_with_unknown_report_flags'}

def validate_injury_issue(data,coverage):
 require(set(data)==ROOT_FIELDS,'Unknown experimental issue fields')
 require(data['schema']=='sports-edge-lab.nfl.experimental-injury-issued-addendum.n038.v1','Unknown experimental issue schema')
 require(data['owner_return_sha256']=='e50b34a54f4f1b5304a7c454c6dfc0ede181e068ff0791c268bf65a248d60507'and data['source_member_sha256']=='81aafebaf6eee8c28b9c976f76f17ae299b05d2d7c99f23e3ac019d8a523a06d','Issued evidence identity differs')
 require(type(data['new_selected_forward_fits'])is int and data['new_selected_forward_fits']==3 and data['owner_pipeline_accepted']is False,'Prior fitted challenger is not an accepted production model')
 for key in ROOT_FIELDS-{'cards','limitations'}:scalar(data[key])
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
  require(r['model_id']==MODEL_ID and r['model_label']=='Experimental injury-era issue'and r['origin']=='registered_pre2024_recipe_new_owner_fit','Experimental role changed')
  require(r['correct']is None and r['unavailable_reason']is None,'No invented result or unavailable state')
  for k in ('full_pipeline_selection_qualified','final_hour_qualified_card','injury_inputs_verified','announced_starter_verified','reserve_status_verified'):require(r[k]is False,'Unverified readiness/starter/IR cannot be promoted')
  require(r['horizon']=='EARLY_BEFORE_T2'and r['issue_class']=='EARLY_FORWARD_RESEARCH_ISSUE','An early issue cannot become a final-hour recommendation')
  issued=instant(r['actual_issue_at']);cut=instant(r['injury_cutoff_at']);require(instant(r['source_asof'])==instant(r['base_feature_asof_at'])<=cut<=issued==instant(data['as_of'])<instant(g['kickoff_utc'])-timedelta(hours=2),'Base/injury/issue/kickoff clocks differ')
  require(instant(r['fit_completed'])<=issued,'Fit completes after issue')
  p=r['home_win_probability'];require(type(p)in(int,float)and math.isfinite(p)and 0<=p<=1 and abs(p*1000-round(p*1000))<1e-7,'Rounded probability required')
  require(r['pick']==(g['home']if p>=.5 else g['away'])and abs(r['pick_probability']-max(p,1-p))<1e-7,'Pick/probability/team binding differs')
  for k in ('home_margin','total','home_score_center','away_score_center'):
   v=r[k];require(type(v)in(int,float)and math.isfinite(v)and abs(v*10-round(v*10))<1e-7,'Rounded finite point center required')
  require(abs(r['home_score_center']+r['away_score_center']-r['total'])<=.11 and abs(r['home_score_center']-r['away_score_center']-r['home_margin'])<=.11,'Derived score centers fail rounding reconciliation')
  teams=r['injury_source_report_team_count'];require(isinstance(teams,dict)and set(teams)=={g['home'],g['away']}and all(type(n)is int and n>=0 for n in teams.values()),'Report counts need exact event teams')
  if gid=='2026_09_JAX_BAL':
   require(teams=={'BAL':9,'JAX':5}and r['injury_source_excluded_rows']==14 and r['injury_report_status']=='PARTIAL_LISTED_REPORTS','Partial Ravens/Jaguars report coverage changed')
   require(r['injury_observed_at']is not None and instant(r['injury_observed_at'])<=cut,'Observed injury clock crosses cutoff');partial+=1
  else:require(not any(teams.values())and r['injury_source_excluded_rows']is None and r['injury_observed_at']is None and r['injury_report_status']=='NO_CURRENT_REPORTS_ADMITTED','Missing reports cannot become healthy or complete')
  require(r['target_feature_views']==VIEWS,'Winner and point injury views must remain distinct')
  for target,fields in [('margin',{'lower','upper','nominal_coverage'}),('total',{'lower','upper','interval_note'})]:
   interval=r[target+'_interval'];require(isinstance(interval,dict)and set(interval)==fields,'Unknown reference interval fields')
   for v in interval.values():scalar(v)
   require(all(type(interval[k])in(int,float)and math.isfinite(interval[k])for k in('lower','upper'))and interval['lower']<interval['upper'],'Invalid reference interval')
   if target=='margin':require(interval['nominal_coverage']==.8,'Registered nominal interval differs')
   else:require(interval['interval_note']=='Fixed pre-2024 residual quantiles; no coverage guarantee','Interval qualification differs')
 require(partial==1,'Exact partial injury-source cohort differs')
 require(sum(games[k]['week']==9 for k in seen)==15 and sum(games[k]['week']==10 for k in seen)==14,'Exact issued week cohort differs')
 return {'experimental_issue_status':'PUBLIC_SEPARATE_EARLY_CHALLENGER_VALIDATED','experimental_issue_games':29,'experimental_issue_target_rows':87,'experimental_issue_prior_selected_forward_fits':3,'experimental_issue_current_publication_new_fits':0,'experimental_issue_current_publication_new_forecasts':0,'experimental_issue_owner_pipeline_accepted':False,'experimental_issue_partial_report_games':1,'experimental_issue_unknown_report_games':28}

def load_injury_issue(coverage):
 p=HERE/'injury_issue_n037.json';data=json.loads(p.read_text());return data,{**validate_injury_issue(data,coverage),'experimental_issue_sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
