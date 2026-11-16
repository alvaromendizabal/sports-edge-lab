"""Publish verified model/provider aggregates without private game arrays."""
from __future__ import annotations
import copy
import hashlib
import json
import math
from project_equal_population import public_alias

METRICS = ('accuracy','brier','log_loss','mae','rmse','crps')


def validate_public(value, equal_population):
    def private(node):
        if isinstance(node,dict):
            if {'model_id','recipe_id','event_id','event_ids','source_path','source_url','raw_payload','feature_names'}.intersection(node):
                raise ValueError('Private paired payload')
            for child in node.values(): private(child)
        elif isinstance(node,list):
            for child in node: private(child)
        elif isinstance(node,str) and any(t in node for t in ('s3://','arn:aws:','/home/','/workspace/','nba:espn:event:')):
            raise ValueError('Private paired payload')
    private(value)
    if (value.get('schema')!='sel.nba.public_model_market_comparison.v1' or value.get('provider')!='DraftKings'
            or value.get('automatic_promotion') is not False or value.get('settlement_or_roi_claim') is not False
            or value.get('current_test_previously_exposed') is not True):
        raise ValueError('Unsupported public paired policy')
    for group in value['groups']:
        refs=[g for g in equal_population['groups'] if
              (g['season'],g['phase'],g['target'],g['horizon_minutes'],g['evidence_track'])==
              (group['season'],group['phase'],group['target'],group['horizon_minutes'],group['evidence_track'])]
        if len(refs)!=1 or refs[0]['required_games']!=group['required_games'] or refs[0]['population_sha256']!=group['population_sha256']:
            raise ValueError('Public paired required population mismatch')
        required=group['required_games'];candidates={m['alias']:m for m in refs[0]['models']}
        if {m['alias'] for m in group['models']}!=set(candidates) or len(group['models'])!=len(candidates):
            raise ValueError('Public paired required candidates omitted or duplicated')
        if group['market_games']+group['missing_market_games']!=required:
            raise ValueError('Public paired market denominator mismatch')
        for model in group['models']:
            if (model['model_games']+model['missing_model_games']!=required
                    or model['market_games']!=group['market_games'] or model['missing_market_games']!=group['missing_market_games']
                    or not 0<=model['paired_games']<=min(model['model_games'],model['market_games'])):
                raise ValueError('Public paired model denominator mismatch')
            complete=bool(model['paired_games']==required and candidates[model['alias']]['full_population_complete'])
            if complete!=model['full_population_complete']:
                raise ValueError('False public full-population paired score')
            if not complete and (model['full_model_metrics'] is not None or model['full_market_metrics'] is not None):
                raise ValueError('Partial paired metrics presented as full')
        if group['all_required_candidates_complete']!=all(m['full_population_complete'] for m in group['models']):
            raise ValueError('Public full-population comparison status mismatch')
        diagnostic=group['common_diagnostic']
        if diagnostic['games']+diagnostic['missing_required_games']!=required:
            raise ValueError('Public diagnostic reduced denominator')
        known={m['alias'] for m in diagnostic['models']};excluded={m['alias'] for m in diagnostic['excluded_candidates']}
        if not (known|excluded).issubset(candidates) or known&excluded:
            raise ValueError('Public diagnostic candidate membership mismatch')
    return copy.deepcopy(value)


def scores(value, expected_games):
    if value is None:
        return None
    if value.get('games') != expected_games:
        raise ValueError('Paired model and market metric denominators differ')
    result = {k:value[k] for k in METRICS if k in value}
    for item in result.values():
        if item is not None and (not isinstance(item,(float,int)) or not math.isfinite(item) or item < 0):
            raise ValueError('Invalid paired metric')
    return result


def project(raw, *, expected_sha256, equal_population):
    if hashlib.sha256(raw).hexdigest() != expected_sha256:
        raise ValueError('Paired private source fingerprint mismatch')
    source = json.loads(raw)
    if (source.get('schema') != 'sel.nba.b089.model_market_fixed_population_comparison.v1'
            or source.get('automatic_promotion') is not False or source.get('settlement_or_roi_claim') is not False
            or source.get('current_test_previously_exposed') is not True or source.get('provider') != 'DraftKings'):
        raise ValueError('Unsupported paired comparison policy')
    groups=[]
    for group in source['groups']:
        if group['headline_denominator_reduced'] is not False or group['champion_selection_allowed'] is not False:
            raise ValueError('Paired subset cannot replace the required population or select a champion')
        matching = [g for g in equal_population['groups'] if
                    (g['season'],g['phase'],g['target'],g['horizon_minutes'],g['evidence_track']) ==
                    (group['season'],group['phase'],group['objective'],group['horizon_minutes'],group['evidence_class'])]
        if len(matching) != 1:
            raise ValueError('Paired group absent from required model scoreboard')
        reference = matching[0]
        required = group['required_population_count']
        if required != reference['required_games'] or group['population_sha256'] != reference['population_sha256']:
            raise ValueError('Paired group changed the required population')
        candidates = {m['alias']:m for m in reference['models']}
        rows=[]
        for model in group['full_population_models']:
            alias=public_alias(model['model_id'])
            if model['public_alias'] != alias or alias not in candidates:
                raise ValueError('Paired candidate identity mismatch')
            if model['model_game_count'] + model['missing_model_games'] != required or model['market_game_count'] + model['missing_market_games'] != required:
                raise ValueError('Paired coverage denominator mismatch')
            complete = bool(model['model_game_count']==required and model['market_game_count']==required
                            and model['paired_game_count']==required and model['paired_population_sha256']==group['population_sha256']
                            and candidates[alias]['full_population_complete'])
            if complete != model['full_population_eligible']:
                raise ValueError('False full-population paired qualification')
            if not complete and (model['full_population_model_metrics'] is not None or model['full_population_market_metrics'] is not None):
                raise ValueError('Partial paired evidence cannot have full metrics')
            rows.append({'alias':alias,'label':candidates[alias]['label'],'feature_count':candidates[alias]['feature_count'],
                         'model_games':model['model_game_count'],'market_games':model['market_game_count'],
                         'paired_games':model['paired_game_count'],'missing_model_games':model['missing_model_games'],
                         'missing_market_games':model['missing_market_games'],'full_population_complete':complete,
                         'full_model_metrics':scores(model['full_population_model_metrics'],required),
                         'full_market_metrics':scores(model['full_population_market_metrics'],required)})
        if {r['alias'] for r in rows} != set(candidates):
            raise ValueError('Paired table omitted required candidates')
        diagnostic = group['common_coverage_diagnostic']
        n=diagnostic['games']
        if n+diagnostic['missing_required_games'] != required or diagnostic['same_game_ids_for_every_displayed_model_and_market'] is not True:
            raise ValueError('Shared diagnostic population not proved')
        diagnostics=[]
        for model in diagnostic['models']:
            alias=public_alias(model['model_id'])
            if model['public_alias'] != alias or alias not in candidates:
                raise ValueError('Diagnostic candidate identity mismatch')
            uncertainty={}
            for metric,u in model['paired_uncertainty'].items():
                if metric not in METRICS or u['games']!=n or u['exploratory_exposed_test'] is not True:
                    raise ValueError('Uncertainty changed its cohort or exposure')
                uncertainty[metric]={k:copy.deepcopy(u[k]) for k in
                    ('method','clusters','iterations','lower_95','upper_95','model_minus_market','direction',
                     'few_clusters_limit','multiple_comparison_adjusted') if k in u}
            diagnostics.append({'alias':alias,'label':candidates[alias]['label'],
                                'metrics':scores(model['model_metrics'],n),'uncertainty':uncertainty})
        excluded = [public_alias(identity) for identity in diagnostic['required_models_without_any_admissible_rows']]
        if not set(excluded).issubset(candidates) or set(excluded).intersection(r['alias'] for r in diagnostics):
            raise ValueError('Diagnostic excluded-model labels conflict')
        groups.append({'season':group['season'],'phase':group['phase'],'target':group['objective'],
                       'horizon_minutes':group['horizon_minutes'],'evidence_track':group['evidence_class'],
                       'required_games':required,'population_sha256':group['population_sha256'],
                       'market_games':group['market_game_count'],'missing_market_games':group['market_missing_game_count'],
                       'all_required_candidates_complete':group['all_required_models_and_market_complete'],
                       'models':rows,
                       'common_diagnostic':{'games':n,'missing_required_games':required-n,'population_sha256':diagnostic['population_sha256'],
                           'market_metrics':scores(diagnostic['market_metrics'],n),'models':diagnostics,
                           'excluded_candidates':[{'alias':a,'label':candidates[a]['label']} for a in excluded],
                           'scope':'IDENTICAL_AVAILABLE_GAMES_EXPLORATORY_ONLY_NO_CHAMPION_SELECTION'}})
    result={'schema':'sel.nba.public_model_market_comparison.v1','as_of_utc':source['as_of_utc'],
            'source_receipt_sha256':expected_sha256,'provider':'DraftKings',
            'normalized_quotes_sha256':source['source_receipts']['markets']['pin']['sha256'],
            'current_test_previously_exposed':True,'automatic_promotion':False,'settlement_or_roi_claim':False,
            'groups':groups}
    text=json.dumps(result)
    if any(word in text for word in ('"model_id"','"event_id"','"recipe_id"','s3://','/home/','/workspace/')):
        raise ValueError('Private paired data in public projection')
    return validate_public(result,equal_population)
