"""Add the independently recovered N054 owner evidence without rewriting its carrier."""
import copy,datetime,gzip,hashlib,json,pathlib
HERE=pathlib.Path(__file__).resolve().parent
ARMS=['football_support_control','passing_qb_interaction','running_personnel_interaction','combined_personnel_interaction']
MARKET_ARMS=['combined_market_support','combined_market_content']
LABELS={'football_support_control':'Football support control','passing_qb_interaction':'Quarterback and passing interactions','running_personnel_interaction':'Running and personnel interactions','combined_personnel_interaction':'Combined football interactions','combined_market_support':'Market support · 80 columns','combined_market_content':'Market content · 96 columns'}

def instant(s):return datetime.datetime.fromisoformat(s.replace('Z','+00:00'))
def load_recovery():return json.loads(gzip.decompress((HERE/'n054_actual_recovery_n055.json.gz').read_bytes()))

LEGACY_COUNTERS=['new_owner_fits','new_owner_issues','new_source_acquisitions','new_native_states','new_scale_states','new_correction_states','new_review_issue_rows']
UNRESOLVED_FAMILIES={'Logistic regression / ridge':'ridge','Extra Trees':'extratrees','Histogram gradient boosting':'histgb'}

def refresh_active_status(d,original):
 """Separate the actual recovery, retained snapshots and unexecuted continuation."""
 s=d['n054_actual_recovery'];near=d['n054_owner_raw_issues'];far=d['n054_owner_long_range_issues'];components=d['n054_owner_component_issues'];conditional=d['n054_owner_conditional_issues']
 ng={x['game_id'] for x in near};fg={x['game_id'] for x in far};total=len(near)+len(far)+len(components)+len(conditional)
 d['original_n054_preparation_snapshot']={'status':'DATED_ORIGINAL_SNAPSHOT_SUPERSEDED_BY_ACTUAL_N054_RECOVERY','as_of':original['as_of'],'owner_evidence_as_of':original['owner_evidence_as_of'],'review_outlook_issue_at':original['review_outlook_summary']['actual_issue_at_utc'],'family_status':copy.deepcopy(original['family_status']),'future_game_forecast_coverage':copy.deepcopy(original['future_game_forecast_coverage']),'capabilities':copy.deepcopy(original['capabilities']),'next':copy.deepcopy(original['next']),'legacy_counter_scope':'N053R1 owner results and earlier N054 review work; not N055 publication results','legacy_counters':{k:original[k] for k in LEGACY_COUNTERS}}
 for row in d['family_status']:
  family=row['family'];prior=row['evidence'];started=family in UNRESOLVED_FAMILIES
  row.update(retained_prior_evidence=prior,n054_start_recorded=started,n054_completed_family_fit_credit=0,n055_status='PREPARED_NOT_OWNER_EXECUTED')
  if started:
   backend=UNRESOLVED_FAMILIES[family]
   retained=(f"The {original['owner_execution']['unique_native_states']:,} completed raw football states remain N053R1 evidence. " if backend=='ridge' else 'Earlier fresh, designation, original and shadow components retain their separate identities. ' if backend=='extratrees' else '')
   row.update(status='N054_START_UNRESOLVED_N055_RECOVERY_PREPARED',status_label='N054 start unresolved; N055 recovery prepared',backend=backend,evidence=retained+'One N054 '+backend+' support-control winner STARTED record has no authenticated returned model or completed receipt. A start marker does not prove optimizer entry or completion. N055 local reconciliation is prepared; no completed family fit is credited.')
  elif family=='Ensembles, blends and probability calibration':
   row.update(status='RETAINED_COMPONENTS_NO_COMPLETED_N054_META_RESULT_N055_PREPARED',status_label='Retained components; no completed N054 meta result',evidence='Actual N054 original and shadow issues reuse their retained model roles. No completed new N054 ensemble, blend or calibration study is admitted. N055 continuation remains prepared; no automatic promotion.')
  else:
   row.update(status='NO_COMPLETED_N054_FAMILY_RESULT_N055_PREPARED',status_label='No completed N054 family result; N055 prepared',evidence=('Earlier family results, including retained negative injury studies, remain dated evidence. ' if family!='Linear regression' else '')+'No authenticated completed N054 broad-family result is admitted for this family. Synthetic runtime admission is a capability check, not a scientific fit. N055 continuation remains prepared.')
 d['future_game_forecast_coverage']={'scope':'ACTUAL_N054_OWNER_ISSUES','scheduled_future_games':sum(not g['completed'] for g in d['games']),'owner_nearer_game_issue_games':len(ng),'owner_long_range_outlook_games':len(fg),'covered_future_games':len(ng|fg),'owner_issue_rows':total,'owner_raw_nearer_issue_rows':len(near),'owner_long_range_issue_rows':len(far),'owner_component_issue_rows':len(components),'owner_conditional_issue_rows':len(conditional),'owner_component_rows_by_role':{role:sum(x['component_role']==role for x in components) for role in ['original','shadow','fresh','designation']},'new_raw_fits_for_owner_issues':0,'new_N055_owner_issues':0,'near_term_T1_equivalence_claimed':False,'long_horizon_accuracy_validated':False,'original_review_snapshot':'original_n054_preparation_snapshot','original_review_rows_in_owner_total':0}
 counts={
  'Complete season and versioned models':{'games':len(d['games']),'model_roles':len(d['lanes'])},
  'Actual rolling research issues':{'N054_owner_issue_rows':total,'component_rows':len(components),'conditional_rows':len(conditional)},
  'Current football issues':{'owner_raw_issue_rows':len(near),'nearer_games':len(ng),'new_raw_fits':0},
  'Fixed market context arms':{'native_states':s['new_native_fits'],'completed_cutoff_jobs':s['completed_cutoff_jobs'],'reused_jobs':s['reused_cutoff_jobs'],'support_blocked_jobs':s['support_blocked_cutoff_jobs'],'registered_jobs':s['cutoff_jobs']},
  'Every future game has a dated outlook':{'owner_long_range_issue_rows':len(far),'later_games':len(fg),'nearer_games':len(ng),'covered_future_games':len(ng|fg),'new_raw_fits':0}
 }
 for card in d['capabilities']:
  name=card['name']
  if name in counts:card['evidence_counts']=counts[name]
  if name=='Complete season and versioned models':card['evidence']=f"{len(d['games'])} games with all {len(d['lanes'])} retained, reconstructed or issued model roles; annual, weekly and event reconstructions remain separately selectable."
  elif name=='Actual rolling research issues':card.update(status_label='Actual N054 owner issues',evidence=f"{total:,} recovered N054 owner issue rows: {len(near)} nearer-game raw, {len(far):,} long-range, {len(components)} retained-component and {len(conditional)} conditional rows. Original source, model and issue clocks remain separate.",limit='These recovered N054 rows are not new N055 issues. Retained N053R1 issues and earlier review outlooks stay in dated history.')
  elif name=='Current football issues':card.update(status_label=f'{len(near)} N054 owner raw issue rows',evidence=f"Four arms × three targets × {len(ng)} nearer future games; source, model and actual N054 issue clocks verified. No new raw fit.",limit=f'The {len(fg)} later games have separate actual N054 owner long-range outlooks. Future injuries and intervening outcomes are not assumed; long-horizon accuracy is unvalidated.')
  elif name=='Fixed market context arms':card.update(status='ACTUAL_N054_RECOVERED_DESCRIPTIVE_STUDY',status_label=f"{s['new_native_fits']} completed market states",evidence=f"Two fixed 80 / 96-column arms with a shared 96-field missingness basis completed {s['completed_cutoff_jobs']} cutoff jobs: {s['new_native_fits']} native states plus {s['reused_cutoff_jobs']} exact reuses. {s['support_blocked_cutoff_jobs']} of {s['cutoff_jobs']} registered jobs remain support-blocked.",limit='No supported pre-2024 market selection cohort. All six adjusted paired tests remain negative; no promotion. The original 318 blocked jobs remain dated N053R1 evidence; source-only restoration earns zero predictive credit.')
  elif name=='Every future game has a dated outlook':card.update(status='ACTUAL_N054_OWNER_ISSUED_UNVALIDATED_LONG_RANGE',status_label=f'{len(fg)} owner outlook games · zero new fits',evidence=f"{len(far):,} actual N054 owner-issued rows cover {len(fg)} later games in four football lanes using 12 retained states. Together with {len(ng)} nearer games, all {len(ng|fg)} future games have dated owner forecasts. The earlier {len(original['review_long_range_issues']):,} review issues are preserved separately.",limit='Long-horizon accuracy and event-specific T1 equivalence are unvalidated. No future injury persistence, intervening result or unsupported conditional probability is invented.')
  elif name=='Position and line continuity frontier':card.update(status='RETAINED_FIXED_POSITION_INTERACTIONS',status_label='Retained clock-qualified position interactions',evidence='Fixed clock-qualified QB, RB/FB and OL status-count interactions are retained in the completed football arms, including the 60/72-column running and combined arms.',limit='Individual talent, lineup continuity, depth and injury causation remain unsupported. Reusing retained features creates no new state or predictive-performance credit.')
 d['next']={'cycle':'N055','status':'PREPARED_NOT_OWNER_EXECUTED','actual_owner_results':0,'title':'N055 reconciles the actual N054 partial and continues the unchanged registered study.','paragraphs':[
  'Authenticate the exact N054 diagnostic and recovered objects, preserve the 102 completed market states and 2,233 actual owner issue rows, and reuse completed N053R1 raw and scale states without refitting.',
  'Reconcile the three unresolved N054 histgb, ridge and Extra Trees starts against exact local model, state, marker and receipt bytes. Recover completed bytes without repeating optimization; otherwise preserve and quarantine the unresolved start. This N055 work is prepared, not executed.',
  'Continue the unchanged nine-family specification only with supported runtime capabilities, earlier-only labels, train-only transformations, complete 2022/23 comparisons and later-fold recipe freeze. Native worker isolation and measured headroom limits preserve other workloads. Synthetic capability checks are not scientific fits.',
  'Issue future outputs only at actual eligible clocks, retain source-only work and unsupported fields separately, and return an authenticated compact actual N055 owner package. No N055 owner result, current-season recipe selection or automatic promotion is claimed.'
 ]}
 d['active_accounting']={'scope':'N055_REVIEW_PUBLICATION_ONLY','retained_N053R1':{'raw_native_states':original['owner_execution']['unique_native_states'],'scale_states':original['owner_execution']['scale_states'],'owner_issue_rows':original['new_owner_issues']},'recovered_N054':{'market_native_states':s['new_native_fits'],'completed_market_cutoff_jobs':s['completed_cutoff_jobs'],'market_reused_jobs':s['reused_cutoff_jobs'],'market_support_blocked_jobs':s['support_blocked_cutoff_jobs'],'owner_issue_rows':total,'family_starts_unresolved':s['family_starts_unresolved'],'completed_family_fit_credit':s['completed_family_fit_credit']},'N055':{'status':'PREPARED_NOT_OWNER_EXECUTED','new_native_fits':0,'new_scale_fits':0,'new_correction_fits':0,'new_owner_issues':0,'new_numeric_source_values':0}}
 for key in LEGACY_COUNTERS:d[key]=0
 d['n055_active_status_revision']=1
 return validate_active_status(d)

def validate_active_status(d):
 """Reject stale active labels even when all retained scientific rows are present."""
 s=d['n054_actual_recovery'];f=d['future_game_forecast_coverage'];near=d['n054_owner_raw_issues'];far=d['n054_owner_long_range_issues'];components=d['n054_owner_component_issues'];conditional=d['n054_owner_conditional_issues']
 ng={x['game_id'] for x in near};fg={x['game_id'] for x in far};future={g['game_id'] for g in d['games'] if not g['completed']}
 if ng&fg or ng|fg!=future:raise ValueError('active future-game owner coverage')
 expected={'scheduled_future_games':len(future),'owner_nearer_game_issue_games':len(ng),'owner_long_range_outlook_games':len(fg),'covered_future_games':len(future),'owner_issue_rows':len(near)+len(far)+len(components)+len(conditional),'owner_raw_nearer_issue_rows':len(near),'owner_long_range_issue_rows':len(far),'owner_component_issue_rows':len(components),'owner_conditional_issue_rows':len(conditional),'original_review_rows_in_owner_total':0}
 if any(f.get(k)!=v for k,v in expected.items()) or f['scope']!='ACTUAL_N054_OWNER_ISSUES':raise ValueError('active future issue accounting')
 if f['owner_issue_rows']!=s['independently_recovered_owner_issue_rows']:raise ValueError('active owner issue summary closure')
 if {x['family'] for x in d['family_status'] if x['n054_start_recorded']}!=set(UNRESOLVED_FAMILIES) or sum(x['n054_start_recorded'] for x in d['family_status'])!=s['family_starts_unresolved']:raise ValueError('active unresolved family starts')
 if any(x['n054_completed_family_fit_credit'] or x['n055_status']!='PREPARED_NOT_OWNER_EXECUTED' or 'PREPARED_N054' in x['status'] for x in d['family_status']) or s['completed_family_fit_credit']:raise ValueError('active family completion credit')
 cards={x['name']:x for x in d['capabilities']};market=cards['Fixed market context arms']['evidence_counts']
 if market!={'native_states':s['new_native_fits'],'completed_cutoff_jobs':s['completed_cutoff_jobs'],'reused_jobs':s['reused_cutoff_jobs'],'support_blocked_jobs':s['support_blocked_cutoff_jobs'],'registered_jobs':s['cutoff_jobs']}:raise ValueError('active market capability accounting')
 if cards['Complete season and versioned models']['evidence_counts']!={'games':len(d['games']),'model_roles':len(d['lanes'])}:raise ValueError('active capability role count')
 if cards['Every future game has a dated outlook']['evidence_counts']!={'owner_long_range_issue_rows':len(far),'later_games':len(fg),'nearer_games':len(ng),'covered_future_games':len(future),'new_raw_fits':0}:raise ValueError('active outlook capability accounting')
 if d['next'].get('cycle')!='N055' or d['next']['status']!='PREPARED_NOT_OWNER_EXECUTED' or d['next']['actual_owner_results']:raise ValueError('active prepared continuation')
 if any(d[k] for k in LEGACY_COUNTERS) or d['active_accounting']['scope']!='N055_REVIEW_PUBLICATION_ONLY':raise ValueError('active publication counter scope')
 if d['active_accounting']['recovered_N054']['owner_issue_rows']!=expected['owner_issue_rows'] or d['active_accounting']['recovered_N054']['market_native_states']!=s['new_native_fits']:raise ValueError('active recovered counter scope')
 return d

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
 if 'n054_actual_recovery' in original:return validate_active_status(original)
 r=validate_recovery(load_recovery());d=copy.deepcopy(original);games={g['game_id']:g for g in d['games']}
 # Label retained historical gaps as dated snapshots; preserve the source carrier.
 for bridge in d['denominator_bridge']:
  if bridge['label']=='Polymarket minute-path support':
   bridge.update(label='Original minute-path support before Rams restoration',reason='Original snapshot: 113 of 121 registered games had minute paths; eight Rams event identities were unresolved then. All eight were subsequently restored, giving the separately listed 121/121 path inventory. Source-only support does not create predictive credit.')
  elif bridge['label']=='Restored Polymarket vs exact native T1 models':
   bridge.update(label='Restored Polymarket versus protected original native T1 benchmark',reason='The protected original benchmark contains 119 decisive games and excludes CHI/SEA and JAX/BAL. New standalone raw predictions cover all 121 decisive finals in a separate role; later provider observations are not substituted into their earlier model cutoffs.')
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
 return refresh_active_status(d,original)
