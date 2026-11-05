"""Validate rounded selected issues without exposing recipes or revising old scores."""
import hashlib,json,math
from pathlib import Path
from datetime import timedelta
from market_clock import instant
from point_markets import require
HERE=Path(__file__).resolve().parent
OWNER='2694fdc3d04350d5c8003fd06de07c58e952042ae780ad2bc1f3435e423a793b'
ROOT={'schema','owner_return_sha256','owner_status','owner_pipeline_accepted','new_native_fits','protected_original_refits','actual_target_rows','distinct_games','historical_metrics_changed','final_hour_qualified_cards','streams','source_census','research','remaining_gaps'}
STREAM={'id','label','role','source_member_sha256','new_native_fits','restored_selected_components','current_training_games','calibration_applied','actual_issue_at','target_rows','cards'}
CARD={'game_id','model_id','model_label','origin','pick','pick_probability','home_win_probability','home_margin','total','home_score_center','away_score_center','actual_issue_at','source_asof','base_feature_asof_at','injury_cutoff_at','injury_observed_at','fit_completed','maximum_label_available_at','horizon','issue_class','final_hour_qualified_card','automatic_promotion','calibration_applied','announced_starter_verified','reserve_status_verified','injury_source_report_team_count','current_training_games','correct','unavailable_reason'}
PINS={'original': ('2026-11-05T22:23:55.247408+00:00', 0, 3, 120, True, 'EARLY_FORWARD_RESEARCH_ISSUE'), 'shadow': ('2026-11-05T22:24:36.908408+00:00', 0, 5, 120, False, 'EARLY_FORWARD_RAW_SHADOW_ISSUE'), 'fresh': ('2026-11-05T22:25:44.730761+00:00', 0, 5, 121, False, 'EARLY_CURRENT_ROLLING_RAW_RESEARCH_ISSUE'), 'designation': ('2026-11-05T22:28:10.772462+00:00', 3, 0, 121, False, 'EARLY_CURRENT_DESIGNATION_RAW_RESEARCH_ISSUE')}
HASHES={'original': 'ab58d366f9237ee0c0805394ab7ff7b4dd4b5415b43e9c1ec3500884a910740d', 'shadow': '076cb4a285b6ced3da35f9cb1778bb25d3af4f9aa74f831ad5981eafa3d4802a', 'fresh': 'f324f82317d0e89d1f4778271afd6ca3f48614a9ad5654510b732bf0fc7cc518', 'designation': 'cff3e904563c94f12188491d84643defadfeeb18dfc8a1a32b468a5232ff89cd'}
SOURCES={'original': '2026-11-04T01:52:35.279297+00:00', 'shadow': '2026-11-04T01:52:35.279297+00:00', 'fresh': '2026-11-05T22:24:52.229765+00:00', 'designation': '2026-11-05T22:27:20.551153+00:00'}
LABELS={'original': '2026-11-03T01:20:00+00:00', 'shadow': '2026-11-03T01:20:00+00:00', 'fresh': '2026-11-04T01:52:33.889207+00:00', 'designation': '2026-11-04T01:52:33.889207+00:00'}

def validate_current_issues(d,coverage):
 require(set(d)==ROOT and d['schema']=='sports-edge-lab.nfl.selected-current-issues.n046.v1','Unknown issue contract')
 require(d['owner_return_sha256']==OWNER,'Owner identity differs')
 require(d['owner_status']=='OWNER_CONTINUATION_REPORTED_WITH_EXPLICIT_COVERAGE' and d['owner_pipeline_accepted'] is False,'Partial owner cannot become accepted')
 require(d['new_native_fits']==3 and d['protected_original_refits']==0 and d['actual_target_rows']==348 and d['distinct_games']==29,'Fit/row/game accounting differs')
 require(d['historical_metrics_changed'] is False and d['final_hour_qualified_cards']==0,'Historical rewrite or unsupported recommendation')
 require(d['source_census']=={'listed_rows': 295, 'team_sections': 29, 'team_slots': 30, 'missing_teams': ['BUF'], 'complete_roster_health': False},'Unknown injuries cannot become health')
 require(d['research']=={'previous_contribution_recipes_reused':960,'new_cross_version_recipes':0,'new_cross_version_native_fits':0,'cross_version_promotion_eligible':False,'cross_version_classification':'EXPLORATORY_COMPATIBILITY_RESEARCH'},'Exploratory study cannot be promoted')
 require(len(d['remaining_gaps'])>=5 and all(type(x)is str for x in d['remaining_gaps']),'Missing limitations')
 require(len(d['streams'])==4,'Exactly four newly issued streams')
 games={g['game_id']:g for g in coverage['all_games']};roles=set();cohorts=[]
 for stream in d['streams']:
  require(set(stream)==STREAM and stream['role'] in PINS and stream['role'] not in roles,'Unknown/duplicate stream');role=stream['role'];roles.add(role)
  at,new,reused,n,cal,classification=PINS[role]
  require((stream['actual_issue_at'],stream['new_native_fits'],stream['restored_selected_components'],stream['current_training_games'],stream['calibration_applied'])==(at,new,reused,n,cal),'Stream identity/accounting differs')
  require(stream['id']=='n046_'+role and stream['target_rows']==87 and len(stream['cards'])==29,'Stream population differs')
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
   require(sum(all(c['designation_report_teams_known'].values()) for c in stream['cards'])==1,'Unknown designation coverage promoted')
   require(all(c['target_feature_counts']=={'win':308,'margin':386,'total':467} for c in stream['cards']),'Target feature scope changed')
  require(sum(games[g]['week']==9 for g in seen)==15,'Missing Week9 card');cohorts.append(seen)
 require(cohorts[0]==cohorts[1]==cohorts[2]==cohorts[3],'Streams must display exact common games')
 return {'n046_selected_issue_validation':'PASS','n046_new_native_fits':3,'n046_actual_target_rows':348,'n046_unique_games':29,'n046_current_training_games_by_stream':{'original':120,'shadow':120,'fresh':121,'designation':121},'n046_protected_refits':0,'n046_owner_accepted':False}

def load_current_issues(coverage):
 p=HERE/'current_issues_n046.json';d=json.loads(p.read_text());return d,{**validate_current_issues(d,coverage),'n046_selected_issues_sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
