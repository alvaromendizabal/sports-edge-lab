"""Project a later evaluation without rewriting the saved 119-game forecasts.

Only authenticated full-precision metrics and their exact matched baselines are
copied. The public rounded prediction asset is used for identity/timing checks,
never to calculate a score or fit a model.
"""
from pathlib import Path
import argparse
import hashlib
import json
from examples.fbs_contracts.build_current_capture_v045_review import metric, physical, ALIASES

ROOT=Path(__file__).resolve().parents[2]
NAME='FBS_V045_REFRESH_MODEL_COMPARISON.json'
EXPECTED=(608461,'0dea0e430cac38e2ec61ded3270d16cd3bd05cba5dc3aac8c4c1a4ac0bfd1418')


def build(source,output):
    source,output=Path(source),Path(output)
    body,pin=physical(source/NAME)
    assert (pin['bytes'],pin['sha256'])==EXPECTED
    original=json.loads((output/'changed-input-study-v044.json').read_text())
    latest=json.loads((output/'current-capture-v045.json').read_text())
    data=json.loads(body)
    assert data['source_capture_physical']==latest['capture']['source_capture_physical']
    counts=data['counts']
    assert (counts['original_base_fits'],counts['original_calibration_fits'],counts['original_prediction_outputs'],counts['registered_games'])==(46,14,3808,119)
    assert (counts['new_local_fits'],counts['new_local_prediction_outputs'],counts['genuine_issues'],counts['qualified_cover_probabilities'])==(0,0,0,0)
    capture={r['id']:r for r in latest['rows']}
    scored=[r for r in original['rows'] if capture[r['id']]['completed']]
    assert len(scored)==counts['scored_games']==12
    assert sum(len(m) for r in scored for m in r['models'].values())==counts['new_result_evaluation_records']==384
    assert all(v['computed_before_cutoff'] is False for r in scored for m in r['models'].values() for v in m.values())
    metrics={};coverage={};baseline_counts={}
    for period,value in data['periods'].items():
        rows=[];baselines={}
        coverage[period]={k:value[k] for k in ('identified_games','observed_completed','registered_target_games','coverage_status','exact_game_ids_sha256','registered_target_ids_sha256')}
        for row in value['metrics']:
            projected=metric(row)
            assert projected['family'].startswith('v043_refresh_') and projected['games']==12
            projected['exact_common_comparisons']=[]
            for pair in row['exact_common_comparisons']:
                model,reference=metric(pair['model_metrics']),metric(pair['reference_metrics'])
                assert model['family']==projected['family'] and model['target']==reference['target']==projected['target']
                assert pair['common_games']==model['games']==reference['games']==12
                assert pair['exact_game_ids_sha256']==model['exact_game_ids_sha256']==reference['exact_game_ids_sha256']==projected['exact_game_ids_sha256']
                reference_family=ALIASES.get(pair['reference_family'],pair['reference_family'])
                assert reference_family==reference['family']
                item={'comparison':pair['comparison'],'common_games':pair['common_games'],'exact_game_ids_sha256':pair['exact_game_ids_sha256'],'reference_family':reference_family,'model_metrics':model,'reference_metrics':reference}
                projected['exact_common_comparisons'].append(item)
                key=(reference['family'],reference['target'],reference['exact_game_ids_sha256'])
                if key in baselines:assert baselines[key]==reference
                else:baselines[key]=reference
            rows.append(projected)
        for row in baselines.values():
            rows.append({**row,'study':'RETAINED_BASELINE_EXACT_REFRESH_COHORT','display_name':'Original '+row['family'].replace('_',' ')})
        assert len({(r['family'],r['target']) for r in rows})==len(rows)
        baseline_counts[period]=len(baselines);metrics[period]=rows
    assert all(len(metrics[p])==64 for p in ('2026','cumulative','current_week','newly_observed'))
    assert all(metrics[p]==[] for p in ('2024','2025','previous_week'))
    _,original_pin=physical(output/'changed-input-study-v044.json')
    report={'schema':'sports-edge-lab.fbs-refresh-evaluation.v045','sources':[pin,original_pin],
            'generated_at':data['generated_at'],'source_capture_physical':data['source_capture_physical'],
            'evidence_class':'RETROSPECTIVE_DEVELOPMENT_TIMING_UNCERTIFIED','forecast_issued':False,
            'historical_availability_proved':False,'promotion_allowed':False,'default_selection_unchanged':'V038 fixed_equal_blend',
            'new_fits':0,'new_predictions':0,'new_provider_requests':0,'counts':counts,'coverage':coverage,
            'scored_refresh_outputs_before_cutoff':0,'scored_refresh_outputs_at_or_after_cutoff':384,
            'baseline_metric_rows_by_period':baseline_counts,'metrics':metrics,
            'interpretation':'The 12 scored refresh games all use outputs computed at or after their reconstructed cutoff. Their 384 evaluations are descriptive reconstruction results, not authenticated issues. The other 107 registered targets remain unscored. Original baseline rows are copied from exact matched comparisons and are not counted as new forecasts.'}
    text=json.dumps(report,separators=(',',':'),sort_keys=True)
    for forbidden in ('s3://','api_key','fit_identity_sha256','feature_names','model_parameters','raw_body','/workspace/','actual_game_ids','source_input_identity'):
        assert forbidden not in text,forbidden
    (output/'changed-input-evaluation-v045.json').write_text(text+'\n')
    (output/'changed-input-evaluation-v045-data.js').write_text('window.FBS_REFRESH_EVALUATION_V045='+text+';\n')
    return {'counts':counts,'baseline_metric_rows_by_period':baseline_counts,'public_bytes':len(text.encode())+1}


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--source',required=True);parser.add_argument('--output',default=str(ROOT/'docs/fbs'))
    args=parser.parse_args();print(json.dumps(build(args.source,args.output),sort_keys=True))
