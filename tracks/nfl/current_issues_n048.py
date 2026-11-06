"""Validate rounded selected issues without exposing recipes or revising old scores."""
import hashlib,json,math
from pathlib import Path
from datetime import timedelta
from market_clock import instant
from point_markets import require
HERE=Path(__file__).resolve().parent
OWNER='a1dfad6f9a466fb721e01d1d5904146e81708c5bcab7df25b69b1bb7718bfda4'
ROOT={'schema','owner_return_sha256','owner_status','owner_pipeline_accepted','native_fit_counter_scope','new_native_fits','protected_original_refits','actual_target_rows','distinct_games','historical_metrics_changed','final_hour_qualified_cards','streams','source_census','research','remaining_gaps'}
STREAM={'id','label','role','source_member_sha256','new_native_fits','restored_selected_components','current_training_games','calibration_applied','actual_issue_at','target_rows','cards'}
CARD={'game_id','model_id','model_label','origin','pick','pick_probability','home_win_probability','home_margin','total','home_score_center','away_score_center','actual_issue_at','source_asof','base_feature_asof_at','injury_cutoff_at','injury_observed_at','fit_completed','maximum_label_available_at','horizon','issue_class','final_hour_qualified_card','automatic_promotion','calibration_applied','announced_starter_verified','reserve_status_verified','injury_source_report_team_count','current_training_games','correct','unavailable_reason'}
PINS={'original': ('2026-11-06T01:41:52.049550+00:00', 0, 3, 120, True, 'EARLY_FORWARD_RESEARCH_ISSUE'), 'shadow': ('2026-11-06T01:42:33.895006+00:00', 0, 5, 120, False, 'EARLY_FORWARD_RAW_SHADOW_ISSUE'), 'fresh': ('2026-11-06T01:43:41.380332+00:00', 0, 5, 121, False, 'EARLY_CURRENT_ROLLING_RAW_RESEARCH_ISSUE'), 'designation': ('2026-11-06T01:45:50.900533+00:00', 0, 3, 121, False, 'EARLY_CURRENT_DESIGNATION_RAW_RESEARCH_ISSUE')}
HASHES={'original': '19e7aaa93bba80fb9b29b669812d6753e8b3538bedb7e572ebee371ab73eb2d0', 'shadow': '5871401c5185d4df3cd17759e7527d1faac3fc06481dfd35fa664f05b98304d0', 'fresh': '71b518f2b6680dbbe09a7ff338c3e705f51a1c96c7408a9c00ab3eab85334f89', 'designation': '33f9302c7437f2ba7300a74e8cca63ab602fa82afd0ec5a878e9200e09f933ad'}
SOURCES={'original': '2026-11-04T01:52:35.279297+00:00', 'shadow': '2026-11-04T01:52:35.279297+00:00', 'fresh': '2026-11-06T01:42:49.297606+00:00', 'designation': '2026-11-06T01:45:11.780140+00:00'}
LABELS={'original': '2026-11-03T01:20:00+00:00', 'shadow': '2026-11-03T01:20:00+00:00', 'fresh': '2026-11-04T01:52:33.889207+00:00', 'designation': '2026-11-04T01:52:33.889207+00:00'}

def validate_current_issues(d,coverage):
 require(set(d)==ROOT and d['schema']=='sports-edge-lab.nfl.selected-current-issues.n048.v1','Unknown issue contract')
 require(d['owner_return_sha256']==OWNER,'Owner identity differs')
 require(d['owner_status']=='PARTIAL_OWNER_CONTINUATION_REPAIR_REQUIRED' and d['owner_pipeline_accepted'] is False,'Partial owner cannot become accepted')
 require(d['native_fit_counter_scope']=='CURRENT_ISSUE_MODELS_ONLY' and d['new_native_fits']==0 and d['protected_original_refits']==0 and d['actual_target_rows']==336 and d['distinct_games']==28,'Fit/row/game accounting differs')
 require(d['historical_metrics_changed'] is False and d['final_hour_qualified_cards']==0,'Historical rewrite or unsupported recommendation')
 require(d['source_census']=={'listed_rows': 238, 'team_sections': 24, 'team_slots': 28, 'missing_teams': ['BUF', 'CHI', 'MIN', 'SEA'], 'complete_roster_health': False},'Unknown injuries cannot become health')
 require(d['research']=={'previous_contribution_recipes_reused':960,'new_cross_version_recipes':0,'new_cross_version_native_fits':0,'cross_version_promotion_eligible':False,'cross_version_classification':'EXPLORATORY_COMPATIBILITY_RESEARCH'},'Exploratory study cannot be promoted')
 require(len(d['remaining_gaps'])>=5 and all(type(x)is str for x in d['remaining_gaps']),'Missing limitations')
 require(len(d['streams'])==4,'Exactly four newly issued streams')
 games={g['game_id']:g for g in coverage['all_games']};roles=set();cohorts=[]
 for stream in d['streams']:
  require(set(stream)==STREAM and stream['role'] in PINS and stream['role'] not in roles,'Unknown/duplicate stream');role=stream['role'];roles.add(role)
  at,new,reused,n,cal,classification=PINS[role]
  require((stream['actual_issue_at'],stream['new_native_fits'],stream['restored_selected_components'],stream['current_training_games'],stream['calibration_applied'])==(at,new,reused,n,cal),'Stream identity/accounting differs')
  require(stream['id']=='n048_'+role and stream['target_rows']==84 and len(stream['cards'])==28,'Stream population differs')
  require(stream['source_member_sha256']==HASHES[role],'Exact selected source identity differs')
  seen=set()
  for c in stream['cards']:
   require(set(c)==(CARD|{'designation_report_teams_known','designation_report_available_at','target_feature_counts'} if role=='designation' else CARD),'Private or unknown card field')
   gid=c['game_id'];require(gid in games and gid not in seen,'Unknown/duplicate event');seen.add(gid);g=games[gid]
   require(not g['completed'] and g['week'] in (9,10),'A completed event cannot be a new early issue')
   require(c['model_id']==stream['id'] and c['current_training_games']==n and c['calibration_applied'] is cal,'Card cannot borrow another stream')
   require(c['issue_class']==classification and c['horizon']=='EARLY_BEFORE_T2','Issue class differs')
   require(all(c[k] is False for k in ('final_hour_qualified_card','automatic_promotion','announced_starter_verified','reserve_status_verified')),'Unsupported readiness/role claim')
   require(c['correct'] is None and c['unavailable_reason'] is None,'No invented result')
   issue=instant(c['actual_issue_at']);source=instant(c['base_feature_asof_at']);injury=instant(c['injury_cutoff_at']);fit=instant(c['fit_completed']);label=instant(c['maximum_label_available_at'])
   require(issue==instant(at) and instant(c['source_asof'])==source and source<=injury<=issue<instant(g['kickoff_utc'])-timedelta(hours=2),'Source/issue/kickoff clocks differ')
   require(label<=fit<=issue,'Unavailable label or future fit')
   expected_source=SOURCES[role]
   require(c['base_feature_asof_at']==expected_source,'Injury refresh cannot refresh base clock')
   expected_label=LABELS[role]
   require(c['maximum_label_available_at']==expected_label,'Training-label identity differs')
   for k in ('home_win_probability','pick_probability','home_margin','total','home_score_center','away_score_center'):
    value=c[k];scale=1000 if 'probability' in k else 10
    require(type(value) in (int,float) and math.isfinite(value) and abs(value*scale-round(value*scale))<1e-7,'Finite rounded output required')
   p=c['home_win_probability'];require(0<=p<=1 and (p==.5 and c['pick'] in (g['home'],g['away']) or c['pick']==(g['home'] if p>.5 else g['away'])) and abs(c['pick_probability']-max(p,1-p))<1e-7,'Probability/team orientation differs')
   require(abs(c['home_score_center']+c['away_score_center']-c['total'])<=.11 and abs(c['home_score_center']-c['away_score_center']-c['home_margin'])<=.11,'Score centers fail reconciliation')
   counts=c['injury_source_report_team_count'];require(set(counts)=={g['home'],g['away']} and all(type(v)is int and v>=0 for v in counts.values()),'Report identity differs')
   if any(counts.values()):require(c['injury_observed_at'] is not None and instant(c['injury_observed_at'])<=injury,'Report later than injury boundary')
   else:require(c['injury_observed_at'] is None,'Unknown reports cannot get invented clock')
  if role=='designation':
   require(sum(all(c['designation_report_teams_known'].values()) for c in stream['cards'])==0,'Unknown designation coverage promoted')
   require(all(c['target_feature_counts']=={'win':308,'margin':386,'total':467} for c in stream['cards']),'Target feature scope changed')
  require(sum(games[g]['week']==9 for g in seen)==14 and '2026_09_JAX_BAL' not in seen,'Missing Week9 card');cohorts.append(seen)
 require(cohorts[0]==cohorts[1]==cohorts[2]==cohorts[3],'Streams must display exact common games')
 return {'n048_selected_issue_validation':'PASS','n048_new_native_fits':0,'n048_actual_target_rows':336,'n048_unique_games':28,'n048_current_training_games_by_stream':{'original':120,'shadow':120,'fresh':121,'designation':121},'n048_protected_refits':0,'n048_owner_accepted':False}

def load_current_issues(coverage):
 p=HERE/'current_issues_n048.json';d=json.loads(p.read_text());return d,{**validate_current_issues(d,coverage),'n048_selected_issues_sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
