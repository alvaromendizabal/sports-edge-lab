"""Add authenticated N055 outcomes while preserving every earlier public carrier."""
import collections,copy,datetime,gzip,hashlib,json,pathlib,re
from actual_recovery_n055 import enrich as enrich_n054,LEGACY_COUNTERS
HERE=pathlib.Path(__file__).resolve().parent
FAMILY_NAMES={'linear':'Linear regression / logistic classifier','ridge':'Regularized logistic regression / ridge','extratrees':'Extra Trees','histgb':'Histogram gradient boosting','xgboost':'XGBoost','lightgbm':'LightGBM','catboost':'CatBoost','torch_mlp':'PyTorch neural classifier / regressor','tensorflow_mlp':'TensorFlow neural classifier / regressor'}
ARMS={'football_support_control':'football support','combined_personnel_interaction':'combined football'}
META_NAMES={'fixed_equal_blend':'Fixed equal blend','oof_convex_blend':'Earlier-only OOF convex blend','oof_stack':'Earlier-only OOF stack','oof_calibration':'Earlier-only OOF calibration','unchanged_frozen201_mean':'Unchanged frozen baseline'}
def instant(s):return datetime.datetime.fromisoformat(s.replace('Z','+00:00'))
def label(model):
 if model in META_NAMES:return META_NAMES[model]
 family,arm=model.split('::');return FAMILY_NAMES[family]+' · '+ARMS[arm]
def load_overlay():return json.loads(gzip.decompress((HERE/'n055_actual_results_n056.json.gz').read_bytes()))

def validate_overlay(r):
 s=r['summary'];native=sum(v['native_states'] for v in s['family_native_counts'].values());starts=sum(v['new_native_starts'] for v in s['family_native_counts'].values())
 if s['new_native_fits']!=native or native!=starts:raise ValueError('N055 native family state accounting')
 meta=sum(s[k] for k in ['new_oof_blend_fits','new_oof_stack_fits','new_oof_calibration_fits'])
 if s['new_meta_fits']!=meta or any(s[k]!=native+meta for k in ['new_optimizer_starts','new_optimizer_returns','new_durable_state_commits']):raise ValueError('N055 native/meta starts returns commits')
 ledger=r['cutoff_ledger']
 if len(ledger)!=s['cutoff_job_rows'] or sum(x['status']=='COMPLETE' for x in ledger)!=s['completed_cutoff_jobs'] or sum(x['new_optimizer_start'] is False for x in ledger)!=s['reused_cutoff_jobs']:raise ValueError('N055 cutoff jobs are not fit counts')
 if sum(x['new_optimizer_start'] is True for x in ledger)!=native:raise ValueError('N055 public start ledger')
 if len(r['annual_predictions'])+len(r['selected_event_predictions'])!=s['historical_prediction_rows']:raise ValueError('N055 historical prediction closure')
 for key,count in [('season_metrics','season_metric_rows'),('weekly_metrics','weekly_metric_rows'),('paired_comparisons','paired_comparison_rows'),('calibration_bins','calibration_bin_rows'),('nested_checks','nested_check_rows')]:
  if len(r[key])!=s[count]:raise ValueError('N055 output closure '+key)
 if s['automatic_promotion'] or s['current_season_recipe_selection'] or s['recorded_future_issue_rows'] or s['new_four_lane_raw_issues'] or s['source_only_predictive_credit']:raise ValueError('N055 selection or new-issue boundary')
 if any(s[k] is not None for k in ['top_level_new_fits','top_level_new_native_fits','top_level_new_forecasts']) or s['owner_research_acceptance']:raise ValueError('N055 partial owner totals must remain null')
 expected=collections.defaultdict(set);actual=collections.defaultdict(set)
 for x in r['annual_predictions']:
  if x['season'] in [2022,2023]:
   actual[x['model'],x['target']].add(x['game_id'])
   if x['model']=='unchanged_frozen201_mean':expected[x['target']].add(x['game_id'])
  if x.get('maximum_training_label_available_at') and instant(x['maximum_training_label_available_at'])>=instant(x['decision_cutoff_at']):raise ValueError('N055 earlier-only training labels')
  if x['new_issue_credit'] or x['future']:raise ValueError('N055 reconstruction is not an issue')
 for (model,target),ids in actual.items():
  if ids!=expected[target]:raise ValueError('N055 identical full 2022/23 cohorts')
 if r['selection']['selection_seasons']!=[2022,2023] or not r['selection']['unchanged_baseline_eligible'] or r['selection']['current_season_selection'] or r['selection']['automatic_promotion']:raise ValueError('N055 frozen selection boundary')
 issues=r['owner_component_issues']
 if len(issues)!=s['verified_owner_issue_rows'] or len({(x['component_role'],x['game_id'],x['target']) for x in issues})!=len(issues):raise ValueError('N055 actual component issue closure')
 for x in issues:
  cutoff=instant(x['kickoff_utc'])-datetime.timedelta(hours=1)
  if not instant(x['maximum_training_label_available_at'])<instant(x['base_feature_asof_at_utc'])<=instant(x['actual_issue_at_utc'])<cutoff:raise ValueError('N055 actual source/label/issue clocks')
  if instant(x['model_fit_completed_at_utc'])>instant(x['actual_issue_at_utc']) or x['new_native_fit_credit'] or x['final_hour_qualified_card']:raise ValueError('N055 retained model issue qualification')
 return r

def enrich(data):
 if 'n055_actual_results' in data:return validate_active_status(data)
 original=enrich_n054(data);r=validate_overlay(load_overlay());d=copy.deepcopy(original);s=r['summary'];games={g['game_id']:g for g in d['games']}
 d['original_n055_publication_snapshot']={k:copy.deepcopy(original[k]) for k in ['family_status','capabilities','future_game_forecast_coverage','next','active_accounting','current_provider_counts']}
 d['original_n055_publication_snapshot'].update(status='DATED_N055_PREPARATION_REPLACED_BY_ACTUAL_OWNER_RESULTS',original_base_as_of=original['as_of'])
 def add_lane(lid,title,qualification,lookup,issue=False):
  lane={'id':lid,'label':title,'qualification':qualification,'classification':'ACTUAL_N055_FROZEN_MODEL_EARLY_ISSUE' if issue else 'ACTUAL_N055_RECONSTRUCTED_RESEARCH','new_fit_credit_this_review':0,'registered_or_retained_game_rows':len(games),'structural_absence_reason':'The complete event inventory is retained when this role lacks an authenticated numerical output.'}
  new=[]
  for game in d['games']:
   for target in ['win','margin','total']:
    rec=lookup.get((game['game_id'],target));reason=('No N055 component issue exists for this game and target; original source and issue histories remain separately retained.' if issue else 'No N055 family future issue was produced because the fresh core source stage failed; older dated football issues remain in their separate lanes.')
    if game['completed'] and not issue:reason=('The N055 family study used its frozen 120-point / 119-winner input after source refresh failed. This additional final belongs to the separate two-game causal append and is not backfilled into that frozen study.' if game['game_id'] in s['current_family_excluded_games'] else 'This target is outside this registered N055 model role; no missing probability or point value is synthesized.')
    row={'game_id':game['game_id'],'lane_id':lid,'target':target,'value':None,'available':False,'eligible':False,'reason':reason,'classification':lane['classification'],'issued_at':None,'feature_asof':None,'fit_completed_at':None,'actual_issue_eligible':False,'precise_source_value':False,'completed':game['completed'],'horizon':'ACTUAL_EARLY_ISSUE' if issue else 'REGISTERED_RECONSTRUCTION_CUTOFF','actual':None,'correct':None,'absolute_error':None}
    if rec:
     row.update(value=rec['prediction'],available=True,eligible=game['completed'] and not issue,classification=rec['classification'],actual=rec.get('actual'),reason=qualification)
     if issue:row.update(issued_at=rec['actual_issue_at_utc'],feature_asof=rec['base_feature_asof_at_utc'],fit_completed_at=rec['model_fit_completed_at_utc'],fit_started_at=rec['model_fit_started_at_utc'],maximum_training_label_available_at=rec['maximum_training_label_available_at'],actual_issue_eligible=True,issue_origin='N055_OWNER',new_owner_issue_credit=1,new_native_fit_credit=0,source_age_seconds=rec['source_age_seconds'],injury_reports_qualified=rec['injury_reports_qualified'],injury_feature_cutoff_at=rec['injury_feature_cutoff_at'],final_hour_qualified_card=False)
     else:row.update(feature_asof=rec['decision_cutoff_at'],fit_completed_at=rec.get('model_completed_at_utc'),maximum_training_label_available_at=rec.get('maximum_training_label_available_at'),policy=rec['policy'],historical_source_possession_verified=rec.get('historical_source_possession_verified'),historical_source_publication_verified=rec.get('historical_source_publication_verified'),new_owner_issue_credit=0,new_native_fit_credit=0)
     if target=='win':
      row.update(pick=game['home'] if row['value']>=.5 else game['away'],pick_probability=max(row['value'],1-row['value']))
      if row['eligible'] and row['actual'] is not None:row['correct']=(row['value']>=.5)==bool(row['actual'])
     elif row['eligible'] and row['actual'] is not None:row['absolute_error']=abs(row['value']-row['actual'])
    new.append(row)
  lane.update(available_games=len({x['game_id'] for x in new if x['available']}),completed_available_games=len({x['game_id'] for x in new if x['available'] and x['completed']}),actual_earlier_issue_games=len({x['game_id'] for x in new if x['actual_issue_eligible']}));d['lanes'].append(lane);d['model_rows'].extend(new)
 annual_models=sorted({x['model'] for x in r['annual_predictions']})
 for model in annual_models:
  lid='n055_annual_'+model.replace('::','_');lookup={(x['game_id'],x['target']):x for x in r['annual_predictions'] if x['model']==model and x['season']==2026}
  add_lane(lid,'N055 annual · '+label(model),'Annual forward out-of-fold reconstruction under the unchanged N055 family study. Earlier-only labels and train-only transformations do not establish original historical source possession or publication. The frozen 2026 cohort is 120 point / 119 winner games; later results do not select the procedure.',lookup)
 selected={(x['game_id'],x['target']):x for x in r['selected_event_predictions'] if x['season']==2026}
 add_lane('n055_selected_event','N055 frozen selection · event reconstruction','The procedure was selected on identical complete 2022/23 cohorts including the unchanged baseline, then frozen before 2024–2026 event reconstruction. Winner/total use the selected OOF stack; margin uses the selected CatBoost support arm. This is historical reconstruction, not an original pregame issue or automatic promotion.',selected)
 for role in ['original','shadow']:
  lookup={(x['game_id'],x['target']):x for x in r['owner_component_issues'] if x['component_role']==role}
  add_lane('n055_component_'+role,'N055 owner · '+role+' frozen-model issue','Actual N055 early research issue from retained models. The base football source remains November 4, 2026; the newer issue timestamp does not imply a refreshed model source. Per-event injury qualification is explicit. No new native fit, final-hour qualification or automatic promotion.',lookup,True)
 for metric in r['season_metrics']:
  row=dict(metric);row.update(identity=metric['model'],group='N055 selected per-event rolling reconstruction' if metric['policy']=='selected_per_event_rolling' else 'N055 annual all-family forward OOF',horizon='REGISTERED_RECONSTRUCTION_CUTOFF',qualification='Identical 2022/23 selection cohorts; later periods are exposed descriptive monitoring. The 2026 family cohort is 120 point/119 winner games. Original source publication/possession is unverified.');d['all_model_metrics'].append(row)
 d.update(n055_actual_results=s,n055_selection_summary=r['selection'],n055_family_per_game=r['annual_predictions']+r['selected_event_predictions'],n055_family_season_metrics=r['season_metrics'],n055_family_weekly_metrics=r['weekly_metrics'],n055_family_comparisons=r['paired_comparisons'],n055_family_nested_checks=r['nested_checks'],n055_family_calibration_bins=r['calibration_bins'],n055_family_cutoff_ledger=r['cutoff_ledger'],n055_family_support_gaps=r['support_gaps'],n055_family_inventory=r['family_inventory'],n055_owner_component_issues=r['owner_component_issues'])
 source=r['current_source'];d['n055_source_capture_summary']=source['summary'];d['n055_current_provider_rows']=source['provider_rows'];d['n055_current_provider_counts']=source['current_provider_counts'];d['n055_source_schedule_reconciliation']=source['schedule_reconciliation'];d['provider_horizons'].append('N055_CURRENT_CAPTURE')
 lookup={(x['game_id'],x['provider'],x['target']):x for x in source['provider_rows']}
 for g in d['games']:
  for provider in ['DraftKings','Kalshi','Polymarket']:
   for target in ['win','margin','total']:
    row=lookup.get((g['game_id'],provider,target))
    if row is None:row={'game_id':g['game_id'],'provider':provider,'target':target,'horizon':'N055_CURRENT_CAPTURE','value':None,'available':False,'eligible':False,'reason':'Completed game: retain the separately dated historical horizons; the N055 current source capture does not replace those observations.' if g['completed'] else 'This later scheduled game is outside the bounded 28-game N055 current source capture. Its event and every provider target remain in the inventory.','classification':'OUTSIDE_N055_CURRENT_CAPTURE','quote_at':None,'acquired_at':None,'completed':g['completed'],'source_only_predictive_credit':0,'complete_midpoint_probability':False,'one_sided_known_threshold':False}
    d['provider_rows'].append(copy.deepcopy(row))
 d['current_provider_counts']=copy.deepcopy(source['current_provider_counts'])
 d['n055_public_projection_sha256']=hashlib.sha256((HERE/'n055_actual_results_n056.json.gz').read_bytes()).hexdigest()
 return refresh_active_status(d,original)

def refresh_active_status(d,original):
 for row in d['family_status']:
  if row.get('retained_prior_evidence'):row['retained_prior_evidence']='Dated original N054 preparation: '+row['retained_prior_evidence']
 d['qualifications']=['For the retained N053R1 four-arm study: '+q if 'Selected winner remains' in q else q for q in d['qualifications']]
 s=d['n055_actual_results'];counts=s['family_native_counts'];name_map={'Linear regression':'linear','Logistic regression / ridge':'ridge','Extra Trees':'extratrees','Histogram gradient boosting':'histgb','XGBoost classifier / regressor':'xgboost','LightGBM classifier / regressor':'lightgbm','CatBoost classifier / regressor':'catboost','PyTorch classifier / regressor':'torch_mlp','TensorFlow classifier / regressor':'tensorflow_mlp'}
 # Retain existing family labels where possible, mapping backend evidence explicitly.
 for row in d['family_status']:
  family=next((backend for title,backend in name_map.items() if row['family']==title),None)
  if family is None:
   family=next((k for k,v in FAMILY_NAMES.items() if k.split('_')[0].lower() in row['family'].lower()),None)
  if row['family']=='Ensembles, blends and probability calibration':
   row.update(status='ACTUAL_N055_META_COMPLETED_NO_PROMOTION',status_label='45 actual N055 meta states',n055_status='ACTUAL_SUPPORTED_RESULTS_PRESERVED',n055_native_states=0,n055_meta_states=s['new_meta_fits'],n054_legacy_start_quarantined=False,evidence='15 earlier-only OOF convex blends, 15 stacks and 15 calibrations completed with exact model-state and durable receipts. Fixed equal blending has no fitted-state credit. Full 2022/23 selection includes the unchanged baseline; later results do not authorize promotion.')
   continue
  if family not in counts:raise ValueError('Unmapped active family '+row['family'])
  c=counts[family];q=c['quarantined_legacy_starts'];row.update(backend=family,status='ACTUAL_N055_NATIVE_RESULTS_PRESERVED',status_label=f"{c['native_states']} actual N055 native states",n055_status='ACTUAL_SUPPORTED_RESULTS_PRESERVED',n055_native_states=c['native_states'],n055_meta_states=0,n054_legacy_start_quarantined=bool(q),evidence=f"{c['native_states']} new native states completed {c['completed_cutoff_jobs']} cutoff jobs; {c['reused_cutoff_jobs']} jobs reused exact inputs. "+('One unresolved prior 2021 support-control winner start was quarantined without another optimization. ' if q else '')+'The complete 2022/23 selection cohort and later frozen monitoring remain separate; synthetic admission is not counted as a scientific fit.')
 near=d['n054_owner_raw_issues'];far=d['n054_owner_long_range_issues'];issues=d['n055_owner_component_issues'];old=d['n054_actual_recovery']['independently_recovered_owner_issue_rows']
 d['future_game_forecast_coverage']={'scope':'RETAINED_N054_AND_ACTUAL_N055_OWNER_ISSUES','scheduled_future_games':sum(not g['completed'] for g in d['games']),'owner_nearer_game_issue_games':len({x['game_id'] for x in near}),'owner_long_range_outlook_games':len({x['game_id'] for x in far}),'covered_future_games':len({x['game_id'] for x in near+far}),'owner_issue_rows':old+len(issues),'retained_N054_owner_issue_rows':old,'actual_N055_owner_issue_rows':len(issues),'actual_N055_original_issue_rows':sum(x['component_role']=='original' for x in issues),'actual_N055_shadow_issue_rows':sum(x['component_role']=='shadow' for x in issues),'new_N055_four_lane_raw_issues':0,'new_N055_family_future_issues':0,'owner_raw_nearer_issue_rows':len(near),'owner_long_range_issue_rows':len(far),'owner_component_issue_rows':len(d['n054_owner_component_issues'])+len(issues),'owner_conditional_issue_rows':len(d['n054_owner_conditional_issues']),'N055_base_source_as_of':s['original_shadow_base_source_as_of'],'new_raw_fits_for_owner_issues':0,'original_review_rows_in_owner_total':0,'near_term_T1_equivalence_claimed':False,'long_horizon_accuracy_validated':False}
 for c in d['capabilities']:
  name=c['name']
  if name=='Complete season and versioned models':c.update(evidence=f"{len(d['games'])} games with all {len(d['lanes'])} retained, reconstructed or issued roles. Every missing target has a specific evidence reason.",evidence_counts={'games':len(d['games']),'model_roles':len(d['lanes'])})
  elif name=='Actual rolling research issues':c.update(status_label='N054 retained; N055 frozen-model issues',evidence=f"{old:,} actual N054 owner rows remain dated. N055 adds {len(issues)} original/shadow early issues across 28 games, with the November 4 base source and per-event injury qualification preserved.",limit='N055 produced zero new four-lane raw or family future issues. New timestamps do not imply fresh model sources.',evidence_counts={'retained_N054_owner_issue_rows':old,'actual_N055_owner_issue_rows':len(issues),'new_N055_four_lane_raw_issues':0})
  elif name=='Three-provider reference alignment':c.update(status_label='New N055 source capture audited',evidence=f"{d['n055_source_capture_summary']['normalized_rows']} captured normalized rows support {d['n055_source_capture_summary']['observed_target_cells']} derived current target references across 28 future games. Every provider receives the same complete grid.",limit='This separate capture horizon is source-only. Kalshi quote clocks remain unrecorded; actual capture times are retained. No historical scoring horizon or model feature is replaced.',evidence_counts={'normalized_rows':d['n055_source_capture_summary']['normalized_rows'],'derived_target_values':d['n055_source_capture_summary']['observed_target_cells'],'source_only_predictive_credit':0})
  elif name=='Current football issues':c.update(status_label='Retained N054 four-lane issues',evidence=f'{len(near)} actual N054 raw issue rows cover 28 nearer games in four arms and three targets. N055 produced zero new four-lane issues because source refresh failed.',limit='N054 clocks remain unchanged. The 122 later games keep their separate dated owner outlooks; future injuries and intervening outcomes are not assumed.')
  elif name=='Every future game has a dated outlook':c.update(status_label='150 games retain dated owner forecasts',evidence=f"The {len(far):,} N054 owner outlook rows cover 122 later games, alongside 28 nearer games. N055 adds 168 original/shadow early issues on the same 28 nearer games, not new long-range forecasts.",limit='The prior N054 forecast coverage remains complete as a dated snapshot. N055 fresh core-source refresh failed. Long-horizon accuracy and exact event-specific horizon equivalence remain unvalidated.')
  elif name=='Verified rolling football models':c['status_label']='Retained N053R1 raw states'
 d['capabilities'].append({'name':'Broad family and OOF meta research','status':'ACTUAL_N055_RESULTS_PRESERVED','status_label':f"{s['new_native_fits']:,} native + {s['new_meta_fits']} meta states",'evidence':f"Nine native families produced {s['historical_prediction_rows']:,} historical rows, {s['season_metric_rows']} seasonal metrics and {s['paired_comparison_rows']} paired comparisons. Complete 2022/23 selection includes the unchanged baseline; winner/total select OOF stack and margin selects CatBoost support.",'limit':'All three selected 2026 paired intervals include zero and adjusted probabilities are 1.0. The two adjusted adverse annual Torch findings are retained. No automatic promotion or newly issued family forecast.','evidence_counts':{'native_states':s['new_native_fits'],'meta_states':s['new_meta_fits'],'historical_rows':s['historical_prediction_rows'],'season_metrics':s['season_metric_rows'],'paired_comparisons':s['paired_comparison_rows']}})
 d['next']={'cycle':'N056','status':'PREPARED_NOT_OWNER_EXECUTED','actual_owner_results':0,'title':'N056 repairs the verified source routing and reuses completed N055 models.','paragraphs':['Authenticate the actual N055 return and exact later external completion. Preserve every completed family/native/meta state, all prior negative studies, the six controls and the three quarantined legacy starts. Reuse exact input identities; do not repeat completed optimization.','Apply the tested source-routing repair with the existing private source boundary intact. Fresh future issues require real source, model and issue clocks before the registered cutoff. Previous N054 forecasts and N055 frozen-source component issues remain immutable.','If exact refreshed inputs are admitted, evaluate the separate two-game retrospective supplement for CHI/SEA and JAX/BAL under frozen 2022/23 choices. Preserve the original 105,075 family rows and 120/119 current cohort; a supplement creates zero historical issue credit.','N056 is prepared. Its source recovery, model reuse, fresh issue production and compact actual return need owner execution before results can be credited. No current-season recipe selection or automatic promotion.']}
 d['active_accounting']={'scope':'N056_REVIEW_PUBLICATION_ONLY','retained_N053R1':copy.deepcopy(original['active_accounting']['retained_N053R1']),'retained_N054':copy.deepcopy(original['active_accounting']['recovered_N054']),'actual_N055':{'status':s['owner_status'],'native_states':s['new_native_fits'],'meta_states':s['new_meta_fits'],'optimizer_starts':s['new_optimizer_starts'],'optimizer_returns':s['new_optimizer_returns'],'durable_commits':s['new_durable_state_commits'],'owner_issue_rows':len(issues),'new_four_lane_raw_issues':0,'new_family_future_issues':0,'global_fit_total':None,'global_issue_total':None,'quarantined_legacy_starts':s['unresolved_optimizer_states']},'N056':{'status':'PREPARED_NOT_OWNER_EXECUTED','new_native_fits':0,'new_meta_fits':0,'new_owner_issues':0,'new_source_requests':0}}
 for key in LEGACY_COUNTERS:d[key]=0
 d['n056_active_status_revision']=1
 return validate_active_status(d)

def validate_active_status(d):
 s=d['n055_actual_results'];f=d['future_game_forecast_coverage'];c={x['name']:x for x in d['capabilities']}
 if len(d['model_rows'])!=len(d['games'])*len(d['lanes'])*3 or len({(r['game_id'],r['lane_id'],r['target']) for r in d['model_rows']})!=len(d['model_rows']):raise ValueError('N056 complete all-model grid')
 if len(d['provider_rows'])!=len(d['games'])*3*3*len(d['provider_horizons']) or len({(r['game_id'],r['provider'],r['target'],r['horizon']) for r in d['provider_rows']})!=len(d['provider_rows']):raise ValueError('N056 equal provider grid')
 if sum(x['n055_native_states'] for x in d['family_status'])!=s['new_native_fits'] or sum(x['n055_meta_states'] for x in d['family_status'])!=s['new_meta_fits'] or sum(x['n054_legacy_start_quarantined'] for x in d['family_status'])!=s['unresolved_optimizer_states']:raise ValueError('N056 active family accounting')
 if any(x['n055_status']!='ACTUAL_SUPPORTED_RESULTS_PRESERVED' or 'PREPARED' in x['status'] for x in d['family_status']):raise ValueError('N056 stale family label')
 if f['actual_N055_owner_issue_rows']!=len(d['n055_owner_component_issues']) or f['owner_issue_rows']!=f['retained_N054_owner_issue_rows']+f['actual_N055_owner_issue_rows'] or f['covered_future_games']!=150:raise ValueError('N056 future issue accounting')
 if c['Complete season and versioned models']['evidence_counts']!={'games':len(d['games']),'model_roles':len(d['lanes'])}:raise ValueError('N056 active role capability')
 if c['Broad family and OOF meta research']['evidence_counts']['native_states']!=s['new_native_fits'] or c['Broad family and OOF meta research']['evidence_counts']['meta_states']!=s['new_meta_fits']:raise ValueError('N056 active family capability')
 if d['next']['cycle']!='N056' or d['next']['status']!='PREPARED_NOT_OWNER_EXECUTED' or d['next']['actual_owner_results']:raise ValueError('N056 next continuation status')
 if any(d[k] for k in LEGACY_COUNTERS) or d['active_accounting']['scope']!='N056_REVIEW_PUBLICATION_ONLY':raise ValueError('N056 publication accounting scope')
 if d['active_accounting']['actual_N055']['native_states']!=s['new_native_fits'] or d['active_accounting']['actual_N055']['owner_issue_rows']!=len(d['n055_owner_component_issues']):raise ValueError('N056 actual owner accounting')
 new=[r for r in d['provider_rows'] if r['horizon']=='N055_CURRENT_CAPTURE']
 if any(r['eligible'] or r['source_only_predictive_credit'] for r in new):raise ValueError('N056 source-only predictive boundary')
 if sum(r['available'] for r in new)!=d['n055_source_capture_summary']['observed_target_cells']:raise ValueError('N056 source-value count')
 for r in d['model_rows']:
  if r['lane_id'].startswith('n055_') and r['available'] and r.get('actual_issue_eligible'):
   if instant(r['issued_at'])>=instant(next(g['kickoff_utc'] for g in d['games'] if g['game_id']==r['game_id'])):raise ValueError('N056 issue game chronology')
 return d
