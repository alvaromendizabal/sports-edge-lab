"""Add the independently recovered N054 owner evidence without rewriting its carrier."""
import copy,datetime,gzip,hashlib,json,pathlib
HERE=pathlib.Path(__file__).resolve().parent
ARMS=['football_support_control','passing_qb_interaction','running_personnel_interaction','combined_personnel_interaction']
MARKET_ARMS=['combined_market_support','combined_market_content']
LABELS={'football_support_control':'Football support control','passing_qb_interaction':'Quarterback and passing interactions','running_personnel_interaction':'Running and personnel interactions','combined_personnel_interaction':'Combined football interactions','combined_market_support':'Market support · 80 columns','combined_market_content':'Market content · 96 columns'}

def instant(s):return datetime.datetime.fromisoformat(s.replace('Z','+00:00'))
def load_recovery():return json.loads(gzip.decompress((HERE/'n054_actual_recovery_n055.json.gz').read_bytes()))

def validate_recovery(r):
 s=r['summary'];ledger=r['market_cutoff_ledger']
 if (s['cutoff_jobs'],s['completed_cutoff_jobs'],s['new_native_fits'],s['reused_cutoff_jobs'],s['support_blocked_cutoff_jobs'])!=(318,216,102,114,102):raise ValueError('N054 actual market job/state accounting')
 if (len(ledger),sum(x['optimizer_started_this_attempt'] and not x['exact_state_reused'] for x in ledger),sum(x['exact_state_reused'] for x in ledger))!=(216,102,114):raise ValueError('N054 state ledger closure')
 if (len(r['market_per_game']),len(r['market_metrics']),len(r['market_comparisons']),len(r['owner_raw_issues']),len(r['owner_long_range_issues']))!=(4221,9,6,336,1464):raise ValueError('N054 actual output closure')
 if len([x for x in r['market_per_game'] if x['arm'] in MARKET_ARMS])!=448:raise ValueError('N054 reconstructed output count')
 if len([x for x in r['market_per_game'] if x['arm']=='unchanged_frozen201_mean'])!=3773:raise ValueError('N054 unchanged baseline')
 if any(x['holm_full_family_p']!=1 or x['confirmatory_significance_claim'] for x in r['market_comparisons']):raise ValueError('N054 negative inferential result preserved')
 if s['pre2024_market_selection_claimed'] or s['automatic_promotion'] or s['current_season_recipe_selection']:raise ValueError('N054 selection boundary')
 for x in ledger:
  if instant(x['maximum_training_label_available_at'])>=instant(x['cutoff']):raise ValueError('N054 earlier-label timing')
 for x in r['owner_raw_issues']+r['owner_long_range_issues']:
  if instant(x['actual_issue_at_utc'])>=instant(x['kickoff_utc']):raise ValueError('N054 real issue precedes game')
  if instant(x['maximum_training_label_available_at'])>=instant(x['decision_cutoff_at']):raise ValueError('N054 issue earlier-label timing')
 for key,expected in [('owner_component_issues',336),('owner_conditional_issues',97)]:
  if len(r[key])!=expected:raise ValueError('N054 component issue output closure')
 for x in r['owner_component_issues']:
  if not instant(x['maximum_training_label_available_at'])<instant(x['base_feature_asof_at_utc'])<=instant(x['actual_issue_at_utc'])<instant(x['kickoff_utc']):raise ValueError('N054 component label/source/issue timing')
  if instant(x['model_fit_completed_at_utc'])>instant(x['actual_issue_at_utc']):raise ValueError('N054 component completed model timing')
 for x in r['owner_conditional_issues']:
  if not instant(x['parent_feature_asof_at_utc'])<=instant(x['parent_point_issue_at_utc'])<=instant(x['actual_issue_at_utc'])<instant(x['kickoff_utc']):raise ValueError('N054 conditional real issue timing')
  less=x['orientation']=='HOME_MARGIN_STRICTLY_LESS_THAN'; p=x['probability_below_threshold'] if less else x['probability_above_threshold']
  if abs(p-x['probability_of_observed_margin_predicate'])>1e-12 or abs(p/(1-x['probability_equal_threshold'])-x['conditional_cover_probability_unequal'])>1e-12:raise ValueError('N054 conditional orientation preserved')
  if x['historical_evaluation_qualified'] or x['calibration_validated'] or x['automatic_promotion']:raise ValueError('N054 conditional unvalidated boundary')
 if len({(x['component_role'],x['game_id'],x['target']) for x in r['owner_component_issues']})!=336:raise ValueError('N054 component unique target output')
 return r

def enrich(original):
 if 'n054_actual_recovery' in original:return original
 r=validate_recovery(load_recovery());d=copy.deepcopy(original);games={g['game_id']:g for g in d['games']}
 old_rows={(x['game_id'],x['lane_id'],x['target']):x for x in original['model_rows']}
 lookup={(x['game_id'],x['arm'],x['target']):x for x in r['market_per_game'] if x['arm'] in MARKET_ARMS}
 near={(x['game_id'],x['arm'],x['target']):x for x in r['owner_raw_issues']}
 far={(x['game_id'],x['arm'],x['target']):x for x in r['owner_long_range_issues']}
 def row(g,lane,target,record,kind,arm):
  x={'game_id':g['game_id'],'lane_id':lane,'target':target,'value':None,'available':False,'eligible':False,'reason':'No registered numerical output for this game, arm and target in the recovered N054 study.','classification':kind,'issued_at':None,'feature_asof':None,'fit_completed_at':None,'actual_issue_eligible':False,'precise_source_value':True,'completed':g['completed'],'horizon':'SOURCE_TIME_RECONSTRUCTION' if arm in MARKET_ARMS else 'CURRENT_KNOWLEDGE_OWNER_ISSUE','actual':g['actual']['home_margin' if target=='margin' else 'total'] if g['actual'] and target!='win' else None,'training_original_possession_claimed':False,'automatic_promotion':False}
  if not record:
   x['reason']='Registered market arm lacks sufficient earlier source content or target support at this cutoff; no prediction is invented.' if g['completed'] and arm in MARKET_ARMS else 'This N054 role did not issue a numerical output for this game; other retained roles and dated reasons remain inspectable.'
   return x
  x.update(value=record['prediction'],available=True,eligible=bool(g['completed'] and arm in MARKET_ARMS),issued_at=record.get('actual_issue_at_utc'),feature_asof=record.get('source_feature_asof_at_utc') or record.get('decision_cutoff_at'),maximum_training_label_available_at=record.get('maximum_training_label_available_at'),classification=kind)
  if arm in MARKET_ARMS:
   x.update(reason='Retrospective source-time reconstruction with earlier-only labels and train-only transformations; historical source publication and original possession are unverified. Descriptive current-season score only.',actual=record.get('actual'),new_owner_issue_credit=0)
  else:
   previous=old_rows.get((g['game_id'],'n053r1_issued_'+arm,target),{})
   x.update(fit_started_at=previous.get('fit_started_at'),fit_completed_at=record.get('model_completed_at_utc') or previous.get('fit_completed_at'),actual_issue_eligible=True,new_owner_issue_credit=1,new_review_issue_credit=0,new_native_fit_credit=0,issue_origin='N054_OWNER',near_term_T1_equivalence_claimed=False,source_age_seconds=(instant(record['actual_issue_at_utc'])-instant(x['feature_asof'])).total_seconds(),reason='Actual N054 owner issue using retained fitted football states and its recorded feature clock; not a claim of event-specific T1 equivalence or validated long-horizon accuracy.')
   if kind=='LONG_RANGE_CURRENT_KNOWLEDGE_OUTLOOK':x.update(horizon='CURRENT_KNOWLEDGE_LONG_RANGE',horizon_days_at_issue=record.get('horizon_days'),long_horizon_accuracy_validated=False,current_injury_persistence_assumed=False,unplayed_intervening_results_assumed=False,future_injury_status='EVENT_SPECIFIC_REPORTS_UNAVAILABLE_NO_CURRENT_INJURY_CARRY_FORWARD')
  if target=='win':x.update(pick=g['home'] if x['value']>=.5 else g['away'],pick_probability=max(x['value'],1-x['value']),actual=record.get('actual'))
  return x
 for arm in MARKET_ARMS+ARMS:
  ismarket=arm in MARKET_ARMS;lid='n054_market_'+arm if ismarket else 'n054_issued_'+arm;source=lookup if ismarket else near
  kind='HISTORICAL_SOURCE_TIME_RECONSTRUCTION' if ismarket else 'ACTUAL_N054_OWNER_CURRENT_KNOWLEDGE_ISSUE'
  d['lanes'].append({'id':lid,'label':'N054 recovered · '+LABELS[arm],'classification':kind,'qualification':('Separate fixed 80/96-column market study. No pre-2024 source support or selection claim; all six adjusted paired tests are negative. Historical original possession remains unverified.' if ismarket else 'Actual N054 owner issue on 28 nearer future games, using retained raw football states. Earlier labels and real issue clocks retained; event-specific T1 equivalence is not claimed.'),'available_games':len({k[0] for k in source if k[1]==arm})})
  for g in d['games']:
   for target in ['win','margin','total']:d['model_rows'].append(row(g,lid,target,source.get((g['game_id'],arm,target)),kind,arm))
 # The current N054 long-range view is versioned to its recovered owner issue.
 # The original review issues remain intact in their original array and gzip carrier.
 for lane in d['lanes']:
  if lane['id'].startswith('n054_outlook_'):
   lane.update(label=lane['label'].replace('N054 long-range outlook','N054 owner long-range outlook'),classification='LONG_RANGE_CURRENT_KNOWLEDGE_OUTLOOK',qualification='Actual N054 owner issue on 122 later future games at its recorded November 7 clock; 12 retained states, zero new fits. Earlier review issues are preserved separately. Event-specific future injuries and intervening results are not assumed. Long-horizon accuracy is unvalidated.')
 for i,x in enumerate(d['model_rows']):
  if x['lane_id'].startswith('n054_outlook_') and x['available']:
   arm=x['lane_id'].removeprefix('n054_outlook_');d['model_rows'][i]=row(games[x['game_id']],x['lane_id'],x['target'],far[(x['game_id'],arm,x['target'])],'LONG_RANGE_CURRENT_KNOWLEDGE_OUTLOOK',arm)
 for role,label in [('original','Original champion · older base source'),('shadow','Shadow blend · older base source'),('fresh','Fresh rolling component'),('designation','Current designation component')]:
  lid='n054_component_'+role;lookup_component={(x['game_id'],x['target']):x for x in r['owner_component_issues'] if x['component_role']==role}
  d['lanes'].append({'id':lid,'label':'N054 owner · '+label,'classification':'ACTUAL_N054_OWNER_COMPONENT_ISSUE','available_games':28,'qualification':'Actual N054 owner issue. The original and shadow components retain the November 4 base-source clock; current rolling and designation sources have their recorded November 7 clocks. No automatic promotion or historical cohort replacement.'})
  for g in d['games']:
   for target in ['win','margin','total']:
    record=lookup_component.get((g['game_id'],target));x=row(g,lid,target,None,'ACTUAL_N054_OWNER_COMPONENT_ISSUE',role)
    if record:
     x.update(value=record['prediction'],available=True,eligible=False,issued_at=record['actual_issue_at_utc'],feature_asof=record['base_feature_asof_at_utc'],fit_started_at=record.get('model_fit_started_at_utc'),fit_completed_at=record['model_fit_completed_at_utc'],maximum_training_label_available_at=record['maximum_training_label_available_at'],classification=record['classification'],actual_issue_eligible=True,new_owner_issue_credit=1,new_native_fit_credit=0,issue_origin='N054_OWNER',source_age_seconds=(instant(record['actual_issue_at_utc'])-instant(record['base_feature_asof_at_utc'])).total_seconds(),component_role=role,reason='Actual N054 owner component output with original source, model and issue clocks preserved; no historical horizon replacement or automatic promotion.',injury_feature_cutoff_at=record.get('injury_feature_cutoff_at'),designation_feature_cutoff_at=record.get('designation_feature_cutoff_at'))
     if target=='win':x.update(pick=g['home'] if x['value']>=.5 else g['away'],pick_probability=max(x['value'],1-x['value']))
    d['model_rows'].append(x)
 normal_conditionals=[]
 for x in r['owner_conditional_issues']:
  normal_conditionals.append({'game_id':x['game_id'],'provider':{'draftkings':'DraftKings','kalshi':'Kalshi','polymarket':'Polymarket'}[x['provider']],'threshold':x['threshold'],'orientation':x['orientation'],'probability_above':x['probability_above_threshold'],'probability_below':x['probability_below_threshold'],'probability_equal':x['probability_equal_threshold'],'probability_of_predicate':x['probability_of_observed_margin_predicate'],'probability_given_not_equal':x['conditional_cover_probability_unequal'],'issued_at':x['actual_issue_at_utc'],'classification':x['classification'],'issue_origin':'N054_OWNER','conditional_schema':x['conditional_cover_probability_schema'],'distribution_family':x['distribution_family'],'source_observed_at':x['observed_at_utc'],'provider_quote_at':x['quote_at_utc'],'parent_point_issued_at':x['parent_point_issue_at_utc'],'parent_feature_asof':x['parent_feature_asof_at_utc'],'calibration_validated':False,'historical_evaluation_qualified':False,'automatic_promotion':False,'original_fields':x})
 d['n054_owner_component_issues']=r['owner_component_issues'];d['n054_owner_conditional_issues']=normal_conditionals
 for metric in r['market_metrics']:
  x=dict(metric);x.update(identity=metric['arm'],group='Recovered N054 fixed market study · full available cohort',horizon='RETROSPECTIVE_SOURCE_TIME',qualification='Unpaired available cohort; use the separate exact paired comparison for baseline deltas. Current-season descriptive result, no selection or promotion.');d['all_model_metrics'].append(x)
 d['n054_actual_recovery']=r['summary'];d['n054_market_per_game']=r['market_per_game'];d['n054_market_metrics']=r['market_metrics'];d['n054_market_comparisons']=r['market_comparisons'];d['n054_market_cutoff_ledger']=r['market_cutoff_ledger'];d['n054_market_numerical_diagnostics']=r['market_numerical_diagnostics'];d['n054_market_blocked_rows']=r['market_blocked_rows'];d['n054_owner_raw_issues']=r['owner_raw_issues'];d['n054_owner_long_range_issues']=r['owner_long_range_issues']
 d['n054_recovery_projection_sha256']=hashlib.sha256((HERE/'n054_actual_recovery_n055.json.gz').read_bytes()).hexdigest()
 if len(d['lanes'])!=73 or len(d['model_rows'])!=59568 or sum(x['available'] for x in d['model_rows'])!=10041:raise ValueError('N055 recovered complete role grid')
 return d
