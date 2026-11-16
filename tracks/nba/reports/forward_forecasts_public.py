"""Selected original NBA issues only; no candidate grid, refit or rescoring."""
import copy
import datetime as dt
import gzip
import hashlib
import json
import math
import re
from pathlib import Path

SCHEMA = 'sel.nba.b089.public_original_forecast_update.v1'
SCHEMA_V2 = 'sel.nba.public_original_forecast_update.v2'
REUSED_JOURNAL_PROOF = 'REUSED_PINNED_ISSUER_CONTENT_PROOF_NOT_NEW_JOURNAL_BODY_READBACK'
FULL_JOURNAL_PROOF = 'FULL_CURRENT_JOURNAL_AND_ENGINE_READBACK'
ROW_KEYS = {'game_id','home_team','away_team','scheduled_start_utc','phase','target','horizon_minutes','roles','model_alias','issue_id','prediction','home_win_probability','prediction_intervals','issued_at_utc','source_asof_utc','training_cutoff_utc','actual_lead_minutes','source_age_seconds_at_issue','issue_horizon_class'}

def stamp(value):
    if not isinstance(value,str): raise ValueError('Missing issue clock')
    result=dt.datetime.fromisoformat(value.replace('Z','+00:00'))
    if result.tzinfo is None: raise ValueError('Naive issue clock')
    return result

def alias(identity):
    return 'candidate-'+hashlib.sha256(('nba-public-v1\0'+identity).encode()).hexdigest()[:12]

def read_export_rows(path):
    """Bounded decode of the authenticated large forecasts array."""
    decoder=json.JSONDecoder()
    with gzip.open(path,'rt',encoding='utf-8') as handle:
        buffer=''
        while True:
            chunk=handle.read(65536)
            if not chunk: raise ValueError('Missing forecast array')
            buffer+=chunk
            found=re.search(r'"forecasts"\s*:\s*\[',buffer)
            if found:
                buffer=buffer[found.end():];break
            if len(buffer)>2_000_000: raise ValueError('Unexpected forecast header size')
        while True:
            buffer=buffer.lstrip()
            if buffer.startswith(']'): return
            if buffer.startswith(','): buffer=buffer[1:].lstrip()
            try:
                row,end=decoder.raw_decode(buffer)
            except json.JSONDecodeError:
                chunk=handle.read(65536)
                if not chunk: raise ValueError('Truncated forecast array')
                buffer+=chunk;continue
            if not isinstance(row,dict): raise ValueError('Invalid forecast row')
            yield row
            buffer=buffer[end:]

def role_names(row,champions):
    proof=row.get('selected_role_proof',{})
    if proof.get('new_champion_promotion') is not False or proof.get('current_full_population_validation_complete_claimed') is not False:
        raise ValueError('Selection proof cannot promote or qualify current test')
    roles=[]
    for saved in proof.get('preserved_prior_selected_roles',[]):
        if saved['recipe_id']!=row['recipe_id'] or saved['phase']!=row['phase'] or saved['objective']!=row['objective']:
            raise ValueError('Selected recipe/role mismatch')
        if saved.get('automatic_production_promotion') is not False or saved.get('current_outcomes_used_for_selection') is not False:
            raise ValueError('Current test used to select role')
        name=f"{saved['phase']}_{saved['objective']}_{saved['metric']}_t{row['horizon_minutes']}"
        published=champions.get(name)
        if not published or published['selected_metric']!=saved['metric']:
            raise ValueError('Selected role was not previously published')
        if published['phase']!=row['phase'] or published['target']!=row['objective'] or published['horizon_minutes']!=row['horizon_minutes']:
            raise ValueError('Published role scope changed')
        metric=saved['metric'];old=published['pooled_metrics'].get(metric);new=saved.get('scores',{}).get(metric)
        if not isinstance(old,(int,float)) or not isinstance(new,(int,float)) or abs(old-new)>0.000001:
            raise ValueError('Preserved validation role score changed')
        recipe=saved.get('recipe',{})
        expected_h=recipe.get('horizon_minutes')
        if expected_h is None:
            match=re.search(r'_T(60|120)(?:$|_)',recipe.get('cohort_id',''))
            expected_h=int(match.group(1)) if match else None
        if expected_h!=row['horizon_minutes']: raise ValueError('Saved role horizon changed')
        roles.append(name)
    if not roles or {champions[r]['selected_metric'] for r in roles}!=set(row['metric_roles']):
        raise ValueError('Incomplete selected role proof')
    return sorted(set(roles))

def project_export(path,execution,base,expected_sha256,execution_checkpoint='B089'):
    path=Path(path)
    with path.open('rb') as f: actual=hashlib.file_digest(f,'sha256').hexdigest()
    if actual!=expected_sha256 or execution['export']['pin']['sha256']!=actual or path.stat().st_size!=execution['export']['pin']['bytes']:
        raise ValueError('Forecast export content pin mismatch')
    summary=execution['summary']
    if execution.get('status')=='VERIFIED_ACTUAL_NEW_FORECAST_EXPORT':
        verified_at=execution['completed_at_utc']
    elif (summary.get('schema')=='sel.nba.b089.actual_new_issued_forecasts.v2'
            and summary.get('status')=='VERIFIED_ACTUAL_ISSUES_WITH_EXPLICIT_HORIZON_CLASSES'
            and summary.get('original_models_mutated_by_export')==0
            and summary.get('forecast_distribution_values_invented')==0
            and (summary.get('journal_rows_full_readback')==0 or
                 (summary.get('journal_rows_full_readback')==summary.get('new_forecast_rows')
                  and summary.get('verification',{}).get('full_report_and_forecast_content_id_proofs') is True))
            and execution.get('source_execution_references')):
        verified_at=summary['exported_at_utc']
    else:
        raise ValueError('Export not verified')
    if summary['automatic_promotions']!=0 or summary['historical_test_backscore'] or summary['public_candidate_grid_authorized']:
        raise ValueError('Export scope would change selection or test')
    journal_proof=FULL_JOURNAL_PROOF if summary.get('journal_rows_full_readback')==summary.get('new_forecast_rows') else REUSED_JOURNAL_PROOF
    rows=[];bindings={};ids=set()
    for source in read_export_rows(path):
        if not source.get('original_live_issue_verified') or not source.get('new_current_inference_verified') or source.get('synthetic_fixture'):
            raise ValueError('Not an authenticated original issue')
        if journal_proof==FULL_JOURNAL_PROOF and (source.get('journal_proof_basis')!=FULL_JOURNAL_PROOF or source.get('original_journal_body_reverified_in_export') is not True):
            raise ValueError('Full journal readback is not proved for each issue')
        for key in ['automatic_production_promotion','current_outcomes_selected_recipe','historical_test_backscore','independent_historical_validation_claim','nominal_T60_T120_issue_claim','new_distribution_inferred_by_export','public_candidate_grid_authorized']:
            if source.get(key) is not False: raise ValueError('Invalid forward issue qualification: '+key)
        roles=role_names(source,base['champions']);model_alias=alias(source['recipe_id'])
        if source['public_model_alias']!=model_alias: raise ValueError('Model alias mismatch')
        for role in roles:
            if role in bindings and bindings[role]!=model_alias: raise ValueError('Role silently reselected')
            bindings[role]=model_alias
        if source['forecast_id'] in ids: raise ValueError('Duplicate original forecast')
        ids.add(source['forecast_id']);game=source['canonical_game']
        if game['official_game_id']!=source['official_game_id'] or stamp(game['start_utc'])!=stamp(source['start_utc']): raise ValueError('Export game identity changed')
        if source['actual_issue_horizon_class']!=source['issue_horizon_class']: raise ValueError('Issue horizon reclassified')
        rows.append({'game_id':source['official_game_id'],'home_team':game['home'],'away_team':game['away'],'scheduled_start_utc':source['start_utc'],'phase':source['phase'],'target':source['objective'],'horizon_minutes':source['horizon_minutes'],'roles':roles,'model_alias':model_alias,'issue_id':'issue-'+hashlib.sha256(('nba-public-issue-v1\0'+source['forecast_id']).encode()).hexdigest()[:24],**{k:source[k] for k in ['prediction','home_win_probability','issued_at_utc','source_asof_utc','training_cutoff_utc','actual_lead_minutes','source_age_seconds_at_issue','issue_horizon_class']},'prediction_intervals':source.get('prediction_intervals')})
    if len(rows)!=summary['new_forecast_rows'] or len({r['game_id'] for r in rows})!=summary['distinct_games'] or len({r['model_alias'] for r in rows})!=summary['distinct_selected_recipe_ids']:
        raise ValueError('Forecast export census mismatch')
    value={'schema':SCHEMA,'source_export_sha256':actual,'export_verified_at_utc':verified_at,'original_journal_proof':journal_proof,'automatic_promotions':0,'historical_test_backscore':False,'new_fits_in_projection':0,'source_reported_unique_new_fits':summary['new_unique_fitted_snapshot_ids'],'role_bindings':dict(sorted(bindings.items())),'rows':sorted(rows,key=lambda r:(r['game_id'],r['horizon_minutes'],r['target'],r['model_alias']))}
    if execution_checkpoint != 'B089':
        value.update(schema=SCHEMA_V2,execution_checkpoint=execution_checkpoint)
    validate_public(value,base)
    return value

def validate_public(value,base):
    allowed={'schema','source_export_sha256','export_verified_at_utc','original_journal_proof','automatic_promotions','historical_test_backscore','new_fits_in_projection','source_reported_unique_new_fits','role_bindings','rows'}
    if value.get('schema')==SCHEMA_V2:
        allowed.add('execution_checkpoint')
        if not isinstance(value.get('execution_checkpoint'),str) or not re.fullmatch(r'B[0-9]{3}(?:-[A-Z0-9]+)*',value['execution_checkpoint']):
            raise ValueError('Invalid public execution checkpoint')
    if set(value)!=allowed or value['schema'] not in (SCHEMA,SCHEMA_V2): raise ValueError('Unapproved public forward schema')
    if value['automatic_promotions']!=0 or value['historical_test_backscore'] or value['new_fits_in_projection']!=0: raise ValueError('Forward publication cannot alter science')
    if not re.fullmatch('[0-9a-f]{64}',value['source_export_sha256']) or value['original_journal_proof'] not in (REUSED_JOURNAL_PROOF,FULL_JOURNAL_PROOF): raise ValueError('Invalid public proof reference')
    if not isinstance(value['source_reported_unique_new_fits'],int) or value['source_reported_unique_new_fits']<0: raise ValueError('Invalid fit count')
    for role,model_alias in value['role_bindings'].items():
        if role not in base['champions'] or not isinstance(model_alias,str) or not re.fullmatch('candidate-[0-9a-f]{12}',model_alias): raise ValueError('Unapproved selected role alias')
    encoded=json.dumps(value)
    for forbidden in ['recipe_id','/home/','s3://','nba:espn:','model_lineage','training_event_ids','member_families']:
        if forbidden in encoded: raise ValueError('Private forecast material')
    games={g['game_id']:g for g in base['games']};seen=set();cells=set()
    for row in value['rows']:
        if set(row)!=ROW_KEYS: raise ValueError('Unapproved public forecast fields')
        game=games.get(row['game_id'])
        if not game or game['home_team']!=row['home_team'] or game['away_team']!=row['away_team'] or game['phase']!=row['phase'] or stamp(game['scheduled_start_utc'])!=stamp(row['scheduled_start_utc']): raise ValueError('Forecast game identity mismatch')
        issued,source,training,start=map(stamp,[row['issued_at_utc'],row['source_asof_utc'],row['training_cutoff_utc'],row['scheduled_start_utc']])
        if source>issued or training>issued or issued>=start: raise ValueError('Forecast issue/source/training clock invalid')
        lead=(start-issued).total_seconds()/60
        if abs(lead-row['actual_lead_minutes'])>1e-6 or abs((issued-source).total_seconds()-row['source_age_seconds_at_issue'])>1e-5: raise ValueError('Forecast age or lead changed')
        cls=row['issue_horizon_class'];h=row['horizon_minutes']
        if h not in (60,120) or cls not in ('EARLY_OUTLOOK','LATE') or (cls=='EARLY_OUTLOOK' and lead<=h) or (cls=='LATE' and lead>=h): raise ValueError('Nominal horizon qualification invented')
        if not isinstance(row['prediction'],(int,float)) or not math.isfinite(row['prediction']): raise ValueError('Invalid prediction')
        if row['target']=='winner' and (not 0<=row['prediction']<=1 or row['home_win_probability']!=row['prediction']): raise ValueError('Winner probability mismatch')
        if row['issue_id'] in seen: raise ValueError('Duplicate original issue')
        seen.add(row['issue_id'])
        if not row['roles']: raise ValueError('Candidate grid without selected role')
        for role in row['roles']:
            old=base['champions'].get(role);cell=(row['game_id'],role)
            if not old or old['target']!=row['target'] or old['phase']!=row['phase'] or old['horizon_minutes']!=h or value['role_bindings'].get(role)!=row['model_alias']: raise ValueError('Selected public role binding mismatch')
            if cell in cells: raise ValueError('Duplicate selected-role forecast')
            cells.add(cell)
        for bounds in (row['prediction_intervals'] or {}).values():
            if len(bounds)!=2 or not all(isinstance(x,(int,float)) and math.isfinite(x) for x in bounds) or bounds[0]>bounds[1]: raise ValueError('Invalid original interval')
    return value

def apply_public(base,value):
    validate_public(value,base)
    checkpoint=value.get('execution_checkpoint','B089')
    games={g['game_id']:g for g in base['games']};scheduled={g['game_id'] for g in base['games'] if g['phase']=='regular' and g['status']=='SCHEDULED'}
    for row in value['rows']:
        for role in row['roles']:
            old=games[row['game_id']]['forecasts'].get(role)
            if old and stamp(old['issued_at_utc'])>=stamp(row['issued_at_utc']):
                raise ValueError('New projection would overwrite newer issue')
    if base.get('forward_forecast_update'):
        base.setdefault('forward_forecast_update_history',[]).append(copy.deepcopy(base['forward_forecast_update']))
    new_games=set();superseded=0;role_counts={};classes={};first=None;last=None
    for row in value['rows']:
        game=games[row['game_id']];new_games.add(row['game_id']);classes[row['issue_horizon_class']]=classes.get(row['issue_horizon_class'],0)+1
        first=min(first,row['issued_at_utc']) if first else row['issued_at_utc'];last=max(last,row['issued_at_utc']) if last else row['issued_at_utc']
        for role in row['roles']:
            old=game['forecasts'].get(role)
            if old and stamp(old['issued_at_utc'])>=stamp(row['issued_at_utc']): raise ValueError('New projection would overwrite newer issue')
            if old:
                game.setdefault('original_issue_history',{}).setdefault(role,[]).append(copy.deepcopy(old));superseded+=1
            forecast={k:copy.deepcopy(row[k]) for k in ['prediction','home_win_probability','prediction_intervals','issued_at_utc','source_asof_utc','training_cutoff_utc','actual_lead_minutes','source_age_seconds_at_issue','issue_horizon_class','model_alias','issue_id']}
            forecast.update(family=base['champions'][role]['family'],scheduled_start_at_issue_utc=row['scheduled_start_utc'],execution_checkpoint=checkpoint,original_pregame_issue=True,nominal_horizon_qualified=False)
            game['forecasts'][role]=forecast
            role_counts[role]=role_counts.get(role,0)+int(row['game_id'] in scheduled)
    remaining=scheduled-new_games;old_only={gid for gid in remaining if games[gid]['forecasts']};missing=remaining-old_only
    required_roles={role for role,meta in base['champions'].items() if meta['phase']=='regular'}
    new_role_counts={gid:sum(games[gid]['forecasts'].get(role,{}).get('execution_checkpoint')==checkpoint for role in required_roles) for gid in scheduled}
    all_new=sum(n==len(required_roles) for n in new_role_counts.values())
    partial_new=sum(0<n<len(required_roles) for n in new_role_counts.values())
    missing_role_cells=sum(role not in games[gid]['forecasts'] for gid in scheduled for role in required_roles)
    older_role_cells=sum(role in games[gid]['forecasts'] and games[gid]['forecasts'][role].get('execution_checkpoint')!=checkpoint for gid in scheduled for role in required_roles)
    base['forward_forecast_update']={'schema':SCHEMA,'source_export_sha256':value['source_export_sha256'],'export_verified_at_utc':value['export_verified_at_utc'],'source_reported_unique_new_fits':value['source_reported_unique_new_fits'],'new_original_issue_rows':len(value['rows']),'new_distinct_games':len(new_games),'new_selected_recipes':len(set(value['role_bindings'].values())),'new_selected_role_views':sum(len(r['roles']) for r in value['rows']),'actual_issue_classes':classes,'nominal_window_issues':0,'scheduled_regular_games':len(scheduled),'scheduled_games_with_new_issues':len(scheduled&new_games),'scheduled_games_only_older_issues':len(old_only),'scheduled_games_missing_any_issue':len(missing),'older_only_game_ids':sorted(old_only),'missing_issue_game_ids':sorted(missing),'scheduled_coverage_by_role':dict(sorted(role_counts.items())),'superseded_selected_role_issues_preserved':superseded,'first_issue_at_utc':first,'latest_issue_at_utc':last,'automatic_promotions':0,'historical_test_scores_changed':False,'original_journal_proof':value['original_journal_proof']}
    if last and stamp(last)>stamp(base['latest_original_issue_at_utc']):base['latest_original_issue_at_utc']=last
    base['forward_forecast_update'].update(required_regular_roles_per_game=len(required_roles),scheduled_games_all_roles_new=all_new,scheduled_games_partly_updated=partial_new,scheduled_selected_role_cells_missing=missing_role_cells,scheduled_selected_role_cells_retaining_older_issues=older_role_cells)
    if value['schema']==SCHEMA_V2:
        base['forward_forecast_update'].update(schema=SCHEMA_V2,execution_checkpoint=checkpoint)
    return base['forward_forecast_update']
