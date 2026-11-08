"""Publish a bounded derived view of authenticated new observations.

Original forecast assets are read-only. Metrics are copied at full precision
from the independent evaluator; rounded browser values never rescore them.
"""
from pathlib import Path
import argparse
import hashlib
import json

ROOT=Path(__file__).resolve().parents[2]
PINS={
    'FBS_V045_CURRENT_CAPTURE_OVERLAY.json':(1938135,'35083c31411b8e40d53bf157a14b4f115a0967e35d67539970646f3167a61b74'),
    'FBS_V045_CURRENT_MODEL_COMPARISON.json':(2538154,'f9fe0d105b2211c5746fa08b1123cf5603e70ddf30e07b548a59a35dd4b54271'),
}

ORIGINALS=('complete-season.json','complete-data.js','complete-history.js','development-2026.json',
           'development-data.js','three-season.json','three-season-data.js','optional-study.json',
           'optional-study-data.js','catboost-study.json','catboost-study-data.js','source-health-v040.json',
           'owner-neural-study.json','owner-neural-study-data.js','current-capture.json','current-capture-data.js','current-capture-v043.json','current-capture-v043-data.js','current-capture-v044.json','current-capture-v044-data.js','changed-input-study-v044.json','changed-input-study-v044-data.js')
ALIASES={'v039_fixed_equal_blend':'v039_fixed_equal_optional_blend',
         'v041_fixed_equal_blend':'v041_neural_fixed_equal_blend'}
METRIC_FIELDS=('family','display_name','study','target','games','exact_game_ids_sha256','accuracy','correct_winners',
               'log_loss','brier','ece_10_equal_width','roc_auc','calibration_bins','mae','rmse','bias','empirical_crps',
               'crps_observations','interval80_coverage','interval95_coverage','interval80_mean_width',
               'interval95_mean_width','interval80_observations','interval95_observations','cover_eligible_games',
               'cover_evaluation_nonpush_games','cover_metric_status','reference_common_game_ids_sha256',
               'reference_common_games','promotion_allowed')


def physical(path):
    body=path.read_bytes()
    return body,{'file':path.name,'bytes':len(body),'sha256':hashlib.sha256(body).hexdigest()}


def metric(row):
    out={k:row[k] for k in METRIC_FIELDS if k in row}
    out['family']=ALIASES.get(out['family'],out['family'])
    assert out['games']>0 and len(out['exact_game_ids_sha256'])==64 and out['promotion_allowed'] is False
    for key in ('paired_model_metrics','paired_reference_metrics'):
        if row.get(key):out[key]=metric(row[key])
    return out


def build(source,output):
    source,output=Path(source),Path(output)
    inputs={};pins=[]
    for name,expected in PINS.items():
        body,pin=physical(source/name)
        assert (pin['bytes'],pin['sha256'])==expected,name
        inputs[name]=json.loads(body);pins.append(pin)
    capture=inputs['FBS_V045_CURRENT_CAPTURE_OVERLAY.json'];evaluation=inputs['FBS_V045_CURRENT_MODEL_COMPARISON.json']
    assert capture['source_capture_physical']==evaluation['source_capture_physical']
    assert capture['new_model_fits']==capture['new_predictions_created']==0
    assert evaluation['new_model_fits']==evaluation['new_predictions_created']==0
    assert evaluation['forecast_issued'] is False and evaluation['promotion_allowed'] is False
    original=json.loads((output/'three-season.json').read_text());games={r['id']:r for r in original['rows']}
    rows=[]
    for row in capture['rows']:
        prior=games[row['id']]
        identity=('id','season','home_id','away_id','kickoff','kickoff_exact','reported_kickoff')
        assert tuple(row[k] for k in identity)==tuple(prior[k] for k in identity),row['id']
        if row['kickoff_exact']:
            assert row['unchanged_binding'] is True and row['binding_status']=='EXACT_UNCHANGED_ID_ORDERED_TEAMS_AND_KICKOFF'
        else:
            assert row['unchanged_binding'] is False and row['binding_status']=='UNCHANGED_TBD_FIXTURE_EXACT_KICKOFF_UNRESOLVED'
        out={k:row[k] for k in identity}
        out.update(completed=row['completed'],home_score=row['home_points'],away_score=row['away_points'],
                   observed_at=row['result_observed_at'],source_observed_at=row['source_observed_at'],newly_observed=row['newly_observed'])
        if out['completed']:
            assert all(isinstance(out[k],int) and out[k]>=0 for k in ('home_score','away_score'))
        rows.append(out)
    assert len(rows)==len({r['id'] for r in rows})==2742 and {r['id'] for r in rows}==set(games)
    metrics={key:[metric(row) for row in value['metrics']] for key,value in evaluation['periods'].items()}
    assert all(len(value)==35 for value in metrics.values())
    events=[];clock_qualified=post_kickoff=0
    for event in capture['draftkings']['events']:
        bound=event['id'] is not None
        if bound:
            g=games[event['id']]
            assert g['kickoff_exact'] and g['kickoff']==event['kickoff']
        targets={}
        for name,native,field in [('winner','h2h','home_probability'),('margin','spreads','market_home_margin'),('total','totals','total_points')]:
            source_target=event['targets'].get(native)
            if source_target is None:
                targets[name]={'value':None,'reason':'Target not captured'};continue
            clock_qualified+=source_target['source_clock_status']=='SOURCE_CLOCKS_QUALIFIED_IDENTITY_STILL_REQUIRED'
            post_kickoff+='CURRENT_OBSERVATION_NOT_PREGAME' in source_target['source_clock_reasons']
            value=source_target.get(field)
            if not bound:assert value is None
            targets[name]={'value':round(value,4 if name=='winner' else 2) if value is not None else None,
                           'reason':'No exact official game binding' if not bound else 'Captured derived reference' if value is not None else 'No derived value',
                           'quote_at':source_target['quote_time'],'captured_at':source_target['observed_at'],
                           'source_available_by_t120':source_target['source_available_by_t120'],
                           'source_available_by_t60':source_target['source_available_by_t60'],
                           'captured_before_kickoff':source_target['captured_before_kickoff'],
                           'strict_model_input_eligible':False}
        early=any(t.get('source_available_by_t120') for t in targets.values())
        before=any(t.get('captured_before_kickoff') for t in targets.values())
        events.append({'id':event['id'],'matchup':event['away']+' at '+event['home'],
                       'kickoff':event['kickoff'],'captured_at':event['observed_at'],'quote_at':event['quote_time'],
                       'targets':targets,'status_text':('Exact official game association; ' if bound else 'Official identity not admitted; ')+('observed before kickoff' if before else 'observed after kickoff'),
                       'model_cutoff_status':'Source available by T−120; historical input qualification unproved' if early else 'No admitted original input-cutoff match',
                       'historical_possession_proved':False,'qualified_cover_probability':None})
    assert clock_qualified+post_kickoff==capture['draftkings']['target_rows']
    assert len(events)==capture['draftkings']['event_count']
    originals=[]
    for name in ORIGINALS:
        _,pin=physical(output/name);originals.append({'path':'docs/fbs/'+name,'bytes':pin['bytes'],'sha256':pin['sha256']})
    d=capture['draftkings']
    report={'schema':'sports-edge-lab.fbs-current-capture.v045','sources':pins,
            'capture':{'observed_at':capture['source_observed_at'],'completed_at':capture['capture_completed_at'],
                       'draftkings_observed_at':d['source_observed_at'],'evaluated_at':evaluation['generated_at'],
                       'source_capture_physical':capture['source_capture_physical']},
            'counts':{**capture['counts'],'new_fixture_ids':0,'changed_fixture_identities':0},
            'delta_basis':capture['delta_basis'],
            'original_prediction_records':evaluation['original_prediction_records'],
            'new_outcome_evaluation_records':evaluation['new_outcome_evaluation_records'],
            'new_fits':0,'new_predictions':0,'new_provider_requests':0,'forecast_issued':False,'promotion_allowed':False,
            'default_selection_unchanged':'V038 fixed_equal_blend','qualified_cover_outputs':0,
            'original_public_assets':originals,'rows':rows,'metrics':metrics,
            'draftkings':{'summary':f"DraftKings captured {d['target_rows']} target observations across {d['event_count']} events. {d['exact_display_bound_events']} events ({d['exact_display_bound_target_rows']} targets) have exact registered-name, ordered-team and kickoff associations. The other {d['event_count']-d['exact_display_bound_events']} events remain unbound, with values withheld. {d['source_available_t120_exact_identity_rows']} matched rows were observed by T−120; none establishes a qualified model input or cover output.",
                          'event_count':d['event_count'],'target_rows':d['target_rows'],'source_clock_qualified_rows':clock_qualified,
                          'post_kickoff_rows':post_kickoff,'exact_game_events':d['exact_display_bound_events'],
                          'exact_game_target_rows':d['exact_display_bound_target_rows'],
                          'source_available_t120_exact_identity_rows':d['source_available_t120_exact_identity_rows'],
                          'source_available_t60_exact_identity_rows':d['source_available_t60_exact_identity_rows'],
                          'events':events}}
    text=json.dumps(report,separators=(',',':'),sort_keys=True)
    for forbidden in ('s3://','api_key','event_id','fit_identity_sha256','feature_names','model_parameters','raw_body','/workspace/','decimal_price','actual_game_ids'):
        assert forbidden not in text,forbidden
    (output/'current-capture-v045.json').write_text(text+'\n')
    (output/'current-capture-v045-data.js').write_text('window.FBS_CURRENT_CAPTURE_V045='+text+';\n')
    return {k:report[k] for k in ('counts','new_outcome_evaluation_records','original_prediction_records')}


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--source',required=True);parser.add_argument('--output',default=str(ROOT/'docs/fbs'))
    args=parser.parse_args();print(json.dumps(build(args.source,args.output),sort_keys=True))
