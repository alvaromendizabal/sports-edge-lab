"""Guard the new original-issued scoreboard and immutable earlier report cohorts."""
import gzip,json
from pathlib import Path
from v5_public_contract import validate_additions
OWNER=set('cycle status started_at finished_at first_error_at native_starts optimizer_entries native_returns validated_returned_states durable_native_commits returned_uncommitted_states observed_meta_states issue_rows aggregate_fit_total aggregate_issue_total actual_V5_fit_returns actual_V5_issues monitor_evaluations monitor_games monitor_metric_rows monitor_input_rows monitor_unsupported_rows monitor_not_final_rows current_source_blocker historical_response_status independent_terminal_stdout_available'.split())
def validate_n062(data,only,instant):
 old=json.loads(gzip.decompress((Path(__file__).resolve().parent/'public_projection_n061.json.gz').read_bytes()))
 for key in('n060_owner_status','n061_owner_status','distribution_scoreboards','issued_cards'):
  if data[key]!=old[key]:raise ValueError('Earlier exact public evidence changed: '+key)
 if data['scoreboards'][:1289]!=old['scoreboards'] or data['cohorts'][:len(old['cohorts'])]!=old['cohorts']:raise ValueError('Original metric or cohort prefix changed')
 for g,prior in zip(data['games'],old['games'],strict=True):
  if g['game_id']!=prior['game_id']:raise ValueError('Game order/identity changed')
  for r,q in zip(g['source_coverage'],prior['source_coverage'],strict=True):
   if r['horizons'][:22]!=q['horizons']:raise ValueError('Old source horizons modified')
 owner=data['n062_owner_status'];only(owner,OWNER,'actual N061 owner status')
 if set(owner)!=OWNER or(owner['cycle'],owner['status'])!=('N061','PARTIAL_OWNER_CONTINUATION_REPAIR_REQUIRED'):raise ValueError('Exact partial owner state')
 if tuple(owner[k]for k in['native_starts','optimizer_entries','native_returns','validated_returned_states','durable_native_commits','returned_uncommitted_states','observed_meta_states','issue_rows','actual_V5_fit_returns','actual_V5_issues','monitor_evaluations','monitor_games','monitor_metric_rows','monitor_input_rows','monitor_unsupported_rows','monitor_not_final_rows'])!=(6,6,6,6,4,2,0,90,6,0,405,13,60,7380,180,6795):raise ValueError('Actual monitor/issue populations')
 if owner['aggregate_fit_total']is not None or owner['aggregate_issue_total']is not None:raise ValueError('Original aggregate nulls retained')
 if owner['independent_terminal_stdout_available']:raise ValueError('No invented terminal stdout')
 if not instant(owner['started_at'])<instant(owner['first_error_at'])<=instant(owner['finished_at']):raise ValueError('Exact owner chronology')
 if owner['current_source_blocker']!='TEAM_STATS_MISSING_2026_09_TB_CHI' or owner['historical_response_status']!='RESPONSE_MISSING_ORIGINAL_NULLS_PRESERVED':raise ValueError('Specific source/response gaps')
 c=data['counts']
 if tuple(c[k]for k in['private_model_roles','private_model_cells','provider_horizons','private_provider_cells','season_metric_rows','actual_latest_issue_rows'])!=(143,116688,25,61200,1349,90):raise ValueError('Current complete grid counts')
 sn=data['snapshot']
 if tuple(sn[k]for k in['completed','decisive','ties','scheduled','in_progress','remaining'])!=(135,134,1,137,0,137):raise ValueError('Actual source snapshot')
 for row in data['scoreboards'][1289:]:
  if row['study']!='N061 original-issued monitoring' or row['horizon']!='ACTUAL_CURRENT_ORIGIN_NOT_EXACT_T1' or not 1<=row['games']<=13:raise ValueError('Separate original-issued cohorts')
 if len(data['provider_capabilities'])!=5:raise ValueError('All provider capabilities accounted')
 for row in data['provider_capabilities']:
  only(row,{'provider','status','scope','reason'},'provider capability')
  if not row['reason']:raise ValueError('Explicit support reason')
 validate_additions(data,only,instant)
 return data
