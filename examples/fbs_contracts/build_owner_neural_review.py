"""Project authenticated original owner neural results for the FBS dashboard.

This performs no fitting or prediction. Public per-game values are rounded only
after matching the unrounded original, official identity and original clocks.
"""
from pathlib import Path
import argparse
import gzip
import json
from examples.fbs_contracts.build_three_season_review import physical, display_target, EVIDENCE

ROOT = Path(__file__).resolve().parents[2]
PINS = {
    'V041_NEURAL_PUBLIC_COMPARISON_CORRECTED.json': (233764, '4778e6ff9de935889ed7211a65591627e4121571468dd9abdb8bd43143d04472'),
    'V041_NEURAL_GAME_PROJECTIONS.json.gz': (1136733, 'a99b7d1e9caa42685eb2ffa1a741fe9bfc67def1e762f1366beda1b1fa747e09'),
    'V041_OWNER_NEURAL_PREDICTIONS.json.gz': (3628384, 'c10517ab687da78d202c5d32ab20ef5f315026f2645214cdc03593bd963617c7'),
}
ALIASES = {'pytorch':'v041_pytorch','tensorflow':'v041_tensorflow',
           'fixed_equal_blend':'v041_neural_fixed_equal_blend'}
DISPLAY = {'v041_pytorch':'PyTorch · original owner',
           'v041_tensorflow':'TensorFlow · original owner',
           'v041_neural_fixed_equal_blend':'Neural fixed blend · original owner'}


def build(source, output):
    source, output = Path(source), Path(output)
    bodies, pins = {}, []
    for name, expected in PINS.items():
        bodies[name], identity = physical(source/name, expected)
        pins.append(identity)
    comparison = json.loads(bodies['V041_NEURAL_PUBLIC_COMPARISON_CORRECTED.json'])
    compact = json.loads(gzip.decompress(bodies['V041_NEURAL_GAME_PROJECTIONS.json.gz']))
    original = json.loads(gzip.decompress(bodies['V041_OWNER_NEURAL_PREDICTIONS.json.gz']))
    fixtures = json.loads((output/'three-season.json').read_text())
    baseline = json.loads((output/'development-2026.json').read_text())
    games = {r['id']:r for r in fixtures['rows']}
    assert comparison['evidence_class'] == compact['evidence_class'] == EVIDENCE
    assert comparison['source_input_identity_sha256'] == compact['source_input_identity_sha256'] == baseline['input_identity_sha256']
    for record in (comparison, compact):
        assert all(record[k] is False for k in ('forecast_issued','historical_availability_proved','promotion_allowed'))
        assert record['source_predictions_physical'] == {k:pins[2][k] for k in ('bytes','sha256')}
    assert comparison['registered_workload_complete'] and compact['missing_eligible_target_outputs'] == []
    raw = {}
    for row in original:
        key = (row['game_id'], ALIASES[row['family']], row['target'])
        assert key not in raw and row['evidence_class'] == EVIDENCE
        assert row['forecast_issued'] is False and row['historical_availability_proved'] is False
        raw[key] = row
    rows, clocks = [], []
    for row in compact['games']:
        g = games[row['game_id']]
        assert g['kickoff_exact'] and row['id'] == g['id']
        assert (row['season'],row['home_id'],row['away_id'],row['kickoff'],row['cutoff']) == (g['season'],g['home_id'],g['away_id'],g['kickoff'],g['cutoff'])
        assert set(row['models']) == set(ALIASES.values())
        out = {'id':g['id'],'season':g['season'],'kickoff':g['kickoff'],'cutoff':g['cutoff'],'models':{}}
        for family, model in row['models'].items():
            assert set(model['targets']) == {'winner','margin','total'}
            assert model['forecast_issued'] is False and model['historical_availability_proved'] is False
            targets = {}
            for target, value in model['targets'].items():
                saved = raw[(g['id'],family,target)]
                assert (saved['home_id'],saved['away_id'],saved['kickoff_utc'],saved['reconstructed_cutoff_utc']) == (g['home_id'],g['away_id'],g['kickoff'],g['cutoff'])
                for field in ('prediction','computed_at_utc','interval80','interval95'):
                    assert saved.get(field) == value.get(field), (g['id'],family,target,field)
                targets[target] = display_target(saved)
                clocks.append(saved['computed_at_utc'])
            out['models'][family] = targets
        rows.append(out)
    assert len(rows) == len({r['id'] for r in rows}) == 2403
    assert len(raw) == sum(len(m) for r in rows for m in r['models'].values()) == 21627
    assert comparison['counts']['original_owner_prediction_outputs'] == len(raw)
    metrics = {str(s['season']):s['metrics'] for s in comparison['seasons']}
    metrics.update({p['period']:p['metrics'] for p in comparison['periods']})
    for cohort, records in metrics.items():
        for row in records:
            assert row['games'] > 0 and len(row['exact_game_ids_sha256']) == 64
            assert row.get('promotion_allowed') is False
            if row['family'] in DISPLAY: row['display_name'] = DISPLAY[row['family']]
        assert {r['family'] for r in records if r['family'] in DISPLAY} == set(DISPLAY)
    _, fixture_pin = physical(output/'three-season.json')
    report = {'schema':'sports-edge-lab.fbs-owner-neural-study.v041',
              'evidence_class':EVIDENCE,'forecast_issued':False,'historical_availability_proved':False,'promotion_allowed':False,
              'generated_at':comparison['generated_at'],'sources':pins,'canonical_fixture_projection':fixture_pin,
              'source_input_identity_sha256':comparison['source_input_identity_sha256'],
              'default_selection_unchanged':'V038 fixed_equal_blend','registered_workload_complete':True,
              'counts':comparison['counts'],'original_computation_first':min(clocks),'original_computation_last':max(clocks),
              'current_reporting_new_fits':0,'current_reporting_new_predictions':0,'current_reporting_provider_requests':0,
              'seasons':[{k:v for k,v in s.items() if k!='metrics'} for s in comparison['seasons']],
              'periods':[{k:v for k,v in p.items() if k!='metrics'} for p in comparison['periods']],
              'limitations':[
                  'Original owner results are retrospective development; input possession and pregame issuance remain unproved.',
                  'No neural variant improves every target and season. On 2026, PyTorch probability losses are lower but point MAE is higher than the retained baseline; no family or blend is promoted.',
                  'CatBoost keeps three missing winner outputs. Differences require identical target-specific game cohorts.',
                  'Schedule, observed outcomes, provider coverage and source acquisition clocks are unchanged.',
                  'No qualified exact-line cover output is present; a point interval does not establish cover probability.'],
              'target_coverage':{str(season):{family:{target:sum(r['season']==season and target in r['models'][family] for r in rows) for target in ('winner','margin','total')} for family in DISPLAY} for season in (2024,2025,2026)},
              'metrics':metrics,'rows':rows}
    text = json.dumps(report, separators=(',',':'), sort_keys=True)
    for forbidden in ('s3://','fit_identity_sha256','model_state_sha256','source_reference','api_key','feature_names','calibration_game_ids','/workspace/','model_parameters','wrapper_sha256'):
        assert forbidden not in text, forbidden
    (output/'owner-neural-study.json').write_text(text+'\n')
    (output/'owner-neural-study-data.js').write_text('window.FBS_OWNER_NEURAL_STUDY='+text+';\n')
    return report


if __name__ == '__main__':
    p = argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--output',default=str(ROOT/'docs/fbs'));a=p.parse_args()
    result=build(a.source,a.output)
    print(json.dumps({k:result[k] for k in ('counts','original_computation_first','original_computation_last','target_coverage')}))
