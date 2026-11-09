"""Validate and render the bounded NFL public contract, without private inputs."""
import argparse,base64,collections,datetime,gzip,json,math,pathlib,re
HERE=pathlib.Path(__file__).resolve().parent
SCHEMA='nfl.public.n059.bounded-evidence.v1'
TOP={'schema','publication_cycle','observed_at','snapshot','counts','identity_notes','games','provider_horizons','scoreboards','issued_cards','cohorts','rolling_policy','frontier_feature_status','distribution_scoreboards','source_summary','source_historical_coverage','active_research_status','reason_catalog','public_scope','qualifications'}
GAME={'game_id','week','home','away','kickoff_utc','completed','phase','result','timing_status','model_coverage','source_coverage'}
MODEL={'target','roles','with_value','actual_issue','eligible_in_original_cohort','no_authenticated_value'}
SOURCE={'provider','target','horizons'}
CELL={'horizon','status','quote_clock_present','capture_clock_present','pregame_possession_established','reason_code','reason','quote_at','captured_at'}
SCORE={'public_model_id','study','season','target','horizon','qualification','provider','games','mae','rmse','bias','crps','log_loss','brier','accuracy','correct','roc_auc','ece_10_fixed_bins','coverage_90','mean_width_90','r2','median_absolute_error'}
CARD={'game_id','role','pick','pick_probability','home_probability','home_margin','total_points','projected_home_points','projected_away_points','issue_at','source_as_of','model_completed_at','classification','qualification','uncertainty_status','conditional_status'}
PROVIDERS={'DraftKings','Kalshi','Polymarket'};TARGETS={'win','margin','total'}
FORBIDDEN=re.compile(r's3://|arn:aws:|X-Amz-|/workspace/|/home/|sagemaker|component_bindings|model_sha256|recipe_sha256|feature_columns|best_params|learning_rate|private_s3|access_token|secret_key|chatgpt\.com/c/|@gmail\.com',re.I)
RETIRED=re.compile(r'(?<![A-Za-z])(?:bets?|betting|wagers?|wagering|bankroll|parlays?|stakes?|staking)(?![A-Za-z])',re.I)
def only(row,allowed,label):
 if not isinstance(row,dict) or set(row)-allowed:raise ValueError('Unexpected public '+label+' field')
def instant(s):
 t=datetime.datetime.fromisoformat(s.replace('Z','+00:00'))
 if t.tzinfo is None:raise ValueError('Public clock timezone')
 return t
def validate_retained(d,actual_cycle='N058'):
 only(d,TOP,'root')
 if d['schema']!=SCHEMA:raise ValueError('Public schema')
 nested={
 'snapshot':'as_of games completed decisive ties remaining in_progress halftime live scheduled status remaining_does_not_mean_all_kickoffs_are_in_the_future',
 'counts':'games teams private_model_roles private_model_cells private_provider_cells provider_horizons season_metric_rows distribution_metric_rows actual_latest_issue_rows actual_latest_issue_games actual_latest_native_fits actual_latest_meta_fits synthetic_smoke_operations protected_raw_states latest_reused_raw_states latest_reused_cutoff_jobs publication_new_fits publication_new_issues',
 'rolling_policy':'status original_fixed_control_preserved initial_selector annual_examples per_game_fit meta_layers history_classification issue_classes actual_new_V4_owner_fits actual_new_V4_owner_issues automatic_promotion',
 'frontier_feature_status':'status proposed implemented materialized preflight_passed admitted evaluated promoted blocked portable_synthetic_tests_passed implemented_by_source qualification',
 'source_summary':'status logical_inputs distinct_body_pins normalized_rows representative_normalized_rows alternate_curve_normalized_rows recovered_history_normalized_rows normalized_rows_by_provider scope_games derived_target_cells observed_target_cells current_captures_before_kickoff current_captures_after_kickoff curve_points curve_points_with_complete_pair curve_pairs_with_different_clocks curve_inventory_cells retained_restored_historical_rows historical_winner_rows historical_point_rows capture_clock_min capture_clock_max quote_clock_min quote_clock_max quote_clock_missing_rows every_known_quote_not_after_capture source_only_predictive_credit probability_side_clocks_bound_to_used_rows new_provider_requests frozen_horizon_records_modified all_current_provider_coverage_claimed all_history_complete',
 'active_research_status':'status new_issue_roles first_blocker next_action top_level_fit_total top_level_issue_total top_level_null_reason no_promotion',
 'public_scope':'complete_game_inventory equal_provider_status_inventory aggregate_scoreboards_anonymized bounded_already_issued_cards complete_candidate_predictions_included active_recipes_included raw_provider_payloads_included private_full_reports_preserved description'}
 for key,fields in nested.items():only(d[key],set(fields.split()),key)
 for r in d['rolling_policy']['annual_examples']:only(r,{'evaluation_season','initial_selection_seasons'},'selector example')
 for r in d['active_research_status']['new_issue_roles']:only(r,{'role','rows','games'},'actual issue role')
 only(d['frontier_feature_status'].get('implemented_by_source',{}),{'pbp','team_stats','compact72'},'implemented source categories')
 for r in d['cohorts']:only(r,{'label','count','denominator','reason','excluded_games'},'cohort')
 for r in d['identity_notes']:only(r,{'code','label'},'identity note')
 for r in d['reason_catalog']:only(r,{'code','meaning'},'reason catalogue')
 for r in d['source_historical_coverage']:only(r,{'season','provider','target','available_games','total_completed_games'},'historical source coverage')
 only(d['source_summary']['normalized_rows_by_provider'],{'kalshi','polymarket','draftkings'},'normalized provider count')

 games=d['games'];index={g['game_id']:g for g in games};teams=collections.Counter(t for g in games for t in (g['home'],g['away']))
 if len(games)!=272 or len(index)!=272 or len(teams)!=32 or set(teams.values())!={17}:raise ValueError('All games and teams')
 counts=d['counts'];snap=d['snapshot']
 if (sum(g['completed'] for g in games),sum(not g['completed'] for g in games))!=(snap['completed'],snap['remaining']):raise ValueError('Dated schedule denominator')
 if any(g['phase'] not in {'STATUS_FINAL','STATUS_IN_PROGRESS','STATUS_HALFTIME','STATUS_SCHEDULED'} for g in games):raise ValueError('Unsupported phase needs explicit review')
 if any(sum(g['phase']==phase for g in games)!=snap[field] for phase,field in [('STATUS_FINAL','completed'),('STATUS_IN_PROGRESS','in_progress'),('STATUS_HALFTIME','halftime'),('STATUS_SCHEDULED','scheduled')]) or snap['live']!=snap['in_progress']+snap['halftime'] or snap['completed']+snap['live']+snap['scheduled']!=272:raise ValueError('Dated phase inventory')
 if {x['code']:x['label'] for x in d['identity_notes']}!={'LA':'Los Angeles Rams','LAC':'Los Angeles Chargers'}:raise ValueError('Legacy Rams identity')
 for gid,away,home in [('2026_08_CHI_SEA',34,17),('2026_09_JAX_BAL',33,10),('2026_09_CIN_ATL',34,17)]:
  g=index[gid]
  if not g['completed'] or (g['result']['away_score'],g['result']['home_score'])!=(away,home):raise ValueError('Protected completed game')
 horizons=d['provider_horizons']
 if len(horizons)!=len(set(horizons)) or len(horizons)!=counts['provider_horizons']:raise ValueError('Horizon closure')
 cells=0
 for g in games:
  only(g,GAME,'game');instant(g['kickoff_utc'])
  if g['completed']!=(g['result'] is not None):raise ValueError('Unsupported result')
  if g['result']:
   only(g['result'],{'home_score','away_score','home_margin','total'},'result');r=g['result']
   if r['home_margin']!=r['home_score']-r['away_score'] or r['total']!=r['home_score']+r['away_score']:raise ValueError('Result arithmetic')
  if {r['target'] for r in g['model_coverage']}!=TARGETS or len(g['model_coverage'])!=3:raise ValueError('All model targets')
  for r in g['model_coverage']:
   only(r,MODEL,'model coverage')
   if r['roles']!=counts['private_model_roles'] or r['with_value']+r['no_authenticated_value']!=r['roles']:raise ValueError('Precise role inventory')
   if not 0<=r['actual_issue']<=r['with_value'] or not 0<=r['eligible_in_original_cohort']<=r['with_value']:raise ValueError('Model evidence bounds')
  if {(r['provider'],r['target']) for r in g['source_coverage']}!={(p,t) for p in PROVIDERS for t in TARGETS} or len(g['source_coverage'])!=9:raise ValueError('Equal provider target inventory')
  for r in g['source_coverage']:
   only(r,SOURCE,'source coverage')
   if [x['horizon'] for x in r['horizons']]!=horizons:raise ValueError('Equal source horizon inventory')
   for cell in r['horizons']:
    only(cell,CELL,'source status');cells+=1
    if any(type(cell[k]) is not bool for k in ('quote_clock_present','capture_clock_present','pregame_possession_established')):raise ValueError('Source clock type')
    if cell['status'] not in {'MATCHED_COHORT_REFERENCE','SOURCE_ONLY_REFERENCE','NO_AUTHENTICATED_REFERENCE','CONDITIONAL_SOURCE_REFERENCE'}:raise ValueError('Source evidence class')
    if cell['status']=='NO_AUTHENTICATED_REFERENCE' and cell['pregame_possession_established']:raise ValueError('No invented source possession')
 if cells!=counts['private_provider_cells'] or counts['private_model_cells']!=272*3*counts['private_model_roles']:raise ValueError('Full inventory reconciliation')
 if len(d['scoreboards'])!=counts['season_metric_rows'] or not {2024,2025,2026}.issubset({r['season'] for r in d['scoreboards']}):raise ValueError('All three-season metrics')
 for r in d['scoreboards']:
  only(r,SCORE,'scoreboard')
  if r['target'] not in TARGETS:raise ValueError('Normalized public target')
  if not re.fullmatch(r'Model \d{3}',r['public_model_id']):raise ValueError('Anonymous aggregate identity')
  if any(isinstance(v,float) and not math.isfinite(v) for v in r.values()):raise ValueError('Non-finite aggregate')
 if not 0<len(d['issued_cards'])<=8 or len({r['game_id'] for r in d['issued_cards']})!=len(d['issued_cards']):raise ValueError('Bounded issued-card exception')
 for c in d['issued_cards']:
  only(c,CARD,'issued card');g=index[c['game_id']];cutoff=instant(g['kickoff_utc'])-datetime.timedelta(hours=1)
  if not instant(c['source_as_of'])<=instant(c['issue_at'])<cutoff:raise ValueError('Card source/issue chronology')
  if c['model_completed_at'] and not instant(c['model_completed_at'])<=instant(c['issue_at']):raise ValueError('Card model chronology')
  if abs(c['pick_probability']-max(c['home_probability'],1-c['home_probability']))>.00011:raise ValueError('Derived probability')
  if abs(c['projected_home_points']+c['projected_away_points']-c['total_points'])>.02:raise ValueError('Projected score arithmetic')
 if len(d['distribution_scoreboards'])!=counts['distribution_metric_rows'] or len({(r['public_variant_id'],r['season'],r['target']) for r in d['distribution_scoreboards']})!=len(d['distribution_scoreboards']):raise ValueError('All distribution metrics')
 for r in d['distribution_scoreboards']:
  only(r,{'public_variant_id','season','target','games','mean_crps','mean_wis','mean_log_score','mean_covered_90','mean_width_90','mean_negative_total_mass','maximum_negative_total_mass','qualification'},'distribution aggregate')
  if not re.fullmatch(r'Distribution \d{2}',r['public_variant_id']):raise ValueError('Anonymous distribution identity')
 if counts['actual_latest_issue_rows']!=sum(r['rows'] for r in d['active_research_status']['new_issue_roles']):raise ValueError('Issue role reconciliation')
 if (counts['actual_latest_native_fits'],counts['actual_latest_meta_fits'])!=((6,0) if actual_cycle=='N061' else (27,0)) or any(counts[k] for k in ('publication_new_fits','publication_new_issues')):raise ValueError('Exact independently audited fits and zero publication credit')
 expected_issue_total=None if actual_cycle in {'N060','N061'} else 2286
 expected_status='N061_V5_BLOCKED_N062_REPAIR_PREPARED' if actual_cycle=='N061' else 'N060_V5_BLOCKED_N061_REPAIR_PREPARED' if actual_cycle=='N060' else 'N058_ATTEMPT_BLOCKED_N059_PREPARED'
 if d['active_research_status']['top_level_fit_total'] is not None or d['active_research_status']['top_level_issue_total']!=expected_issue_total:raise ValueError('Original partial aggregate counters')
 if d['rolling_policy']['status']!=expected_status or d['rolling_policy']['actual_new_V4_owner_fits'] or d['rolling_policy']['actual_new_V4_owner_issues']:raise ValueError('Prepared methodology status')
 f=d['frontier_feature_status']
 if f['status']!=expected_status or f['proposed']!=f['implemented']+f['blocked'] or sum(f['implemented_by_source'].values())!=f['implemented']:raise ValueError('Prepared feature inventory reconciliation')
 if any(f[k] for k in ('materialized','preflight_passed','admitted','evaluated','promoted')):raise ValueError('No owner feature admission from synthetic tests')
 if d['source_summary']['source_only_predictive_credit'] or d['source_summary']['frozen_horizon_records_modified']:raise ValueError('Source-only boundary')
 if d['public_scope']['complete_candidate_predictions_included'] or d['public_scope']['active_recipes_included'] or d['public_scope']['raw_provider_payloads_included']:raise ValueError('Public/private boundary')
 raw=json.dumps(d,ensure_ascii=False,allow_nan=False)
 if FORBIDDEN.search(raw) or RETIRED.search(raw):raise ValueError('Private or transaction-language payload')
 return d
def validate(d):
 if d.get('schema')=='nfl.public.n062.bounded-evidence.v1':
  from n062_public_contract import validate_n062
  only(d,TOP|{'n060_owner_status','n061_owner_status','n062_owner_status','v5_scope','provider_capabilities'},'N062 root')
  retained={k:v for k,v in d.items() if k not in {'n060_owner_status','n061_owner_status','n062_owner_status','v5_scope','provider_capabilities'}}
  retained=dict(retained,schema=SCHEMA,publication_cycle='N059')
  validate_retained(retained,actual_cycle='N061')
  validate_n062(d,only,instant)
  raw=json.dumps(d,ensure_ascii=False,allow_nan=False)
  if FORBIDDEN.search(raw) or RETIRED.search(raw):raise ValueError('Private or transaction-language N062 payload')
  return d
 if d.get('schema')=='nfl.public.n061.bounded-evidence.v1':
  from v5_public_contract import validate_additions
  from n061_public_contract import validate_n061
  only(d,TOP|{'n060_owner_status','n061_owner_status','v5_scope','provider_capabilities'},'N061 root')
  retained={k:v for k,v in d.items() if k not in {'n060_owner_status','n061_owner_status','v5_scope','provider_capabilities'}}
  retained=dict(retained,schema=SCHEMA,publication_cycle='N059')
  validate_retained(retained,actual_cycle='N060')
  validate_additions(d,only,instant)
  validate_n061(d,only,instant)
  raw=json.dumps(d,ensure_ascii=False,allow_nan=False)
  if FORBIDDEN.search(raw) or RETIRED.search(raw):raise ValueError('Private or transaction-language N061 payload')
  return d
 if d.get('schema')=='nfl.public.n060.bounded-evidence.v1':
  from v5_public_contract import validate_additions
  only(d,TOP|{'n060_owner_status','v5_scope'},'N060 root')
  retained={k:v for k,v in d.items() if k not in {'n060_owner_status','v5_scope'}}
  retained=dict(retained,schema=SCHEMA,publication_cycle='N059')
  validate_retained(retained)
  validate_additions(d,only,instant)
  raw=json.dumps(d,ensure_ascii=False,allow_nan=False)
  if FORBIDDEN.search(raw) or RETIRED.search(raw):raise ValueError('Private or transaction-language V5 payload')
  return d
 return validate_retained(d)
def pack(d):return gzip.compress(json.dumps(d,separators=(',',':'),ensure_ascii=False).encode(),compresslevel=9,mtime=0)
def load(path=HERE/'public_projection_n062.json.gz'):return validate(json.loads(gzip.decompress(path.read_bytes())))
def build(d):
 validate(d);s=(HERE/('season_review_n054.template.html' if d['schema']=='nfl.public.n062.bounded-evidence.v1' else 'season_review_n061.template.html')).read_text()
 if FORBIDDEN.search(s) or RETIRED.search(s):raise ValueError('Public template boundary')
 return s.replace('__PUBLIC_GZIP_BASE64__',base64.b64encode(pack(d)).decode())
def main():
 p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args();body=build(load());out=HERE/'season_review_n054.html'
 if a.check:
  if out.read_text()!=body:raise SystemExit('Public render differs from reviewed projection')
  print('N062 bounded public content, V5 exposure and complete inventory: PASS')
 else:out.write_text(body)
if __name__=='__main__':main()
