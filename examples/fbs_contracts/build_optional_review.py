"""Whitelist completed V039 optional-family outputs without refitting or rescoring."""
from pathlib import Path
import argparse
import gzip
import json
from examples.fbs_contracts.build_three_season_review import physical, display_target, EVIDENCE

ROOT = Path(__file__).resolve().parents[2]
PINS = {
    'V039_OPTIONAL_PUBLIC_COMPARISON.json': (54630, 'c81b7115c47d96998508a7edb6a027ae2a9ad944e210b04cfc888c06e2ea3331'),
    'V039_OPTIONAL_GAME_PROJECTIONS.json.gz': (946846, '15b778d500e2ee00531af34730918c566fcaed03b74925380831771d8473f6e0'),
    'ALL_KNOWN_KICKOFF_PREDICTIONS.json.gz': (3614832, 'f28d7999fb8ace6e24b973864acd87a3a1e257ce6b90490add2b9e26d5961fd2'),
}
ALIASES = {'xgboost': 'v039_xgboost', 'lightgbm': 'v039_lightgbm', 'fixed_equal_blend': 'v039_fixed_equal_optional_blend'}

def build(source, output):
    source, output = Path(source), Path(output)
    bodies, pins = {}, []
    for name, expected in PINS.items():
        body, pin = physical(source/name, expected); bodies[name] = body; pins.append(pin)
    comparison = json.loads(bodies['V039_OPTIONAL_PUBLIC_COMPARISON.json'])
    compact = json.loads(gzip.decompress(bodies['V039_OPTIONAL_GAME_PROJECTIONS.json.gz']))
    raw = json.loads(gzip.decompress(bodies['ALL_KNOWN_KICKOFF_PREDICTIONS.json.gz']))
    canonical = json.loads((output/'three-season.json').read_text())
    prior = json.loads((output/'development-2026.json').read_text())
    games = {r['id']: r for r in canonical['rows']}
    assert compact['source_report_physical'] == {'bytes': pins[0]['bytes'], 'sha256': pins[0]['sha256']}
    assert comparison['evidence_class'] == compact['evidence_class'] == EVIDENCE
    assert comparison['source_input_identity_sha256'] == prior['input_identity_sha256'] == compact['source_input_identity_sha256']
    assert comparison['forecast_issued'] is False and comparison['promotion_allowed'] is False
    assert comparison['counts']['unique_successful_new_base_fits'] == 1362
    assert comparison['counts']['successful_new_calibration_fits'] == 454
    records = {}
    for row in raw:
        key = (row['game_id'], ALIASES[row['family']], row['target'])
        assert key not in records and not row['forecast_issued'] and not row['historical_availability_proved']
        assert row['evidence_class'] == EVIDENCE
        records[key] = row
    assert len(records) == 21627
    rows = []
    for row in compact['games']:
        g = games[row['game_id']]
        assert (row['season'],row['home_id'],row['away_id'],row['kickoff_utc'],row['reconstructed_cutoff_utc']) == (g['season'],g['home_id'],g['away_id'],g['kickoff'],g['cutoff'])
        o = {'id': g['id'], 'season': g['season'], 'kickoff': g['kickoff'], 'cutoff': g['cutoff'], 'models': {}}
        for family, model in row['models'].items():
            assert family in ALIASES.values() and model['cover_probability'] is None
            targets = {}
            for target, value in model['targets'].items():
                original = records[(g['id'],family,target)]
                assert original['prediction'] == value['prediction']
                assert (original['home_id'],original['away_id'],original['kickoff_utc'],original['reconstructed_cutoff_utc']) == (g['home_id'],g['away_id'],g['kickoff'],g['cutoff'])
                targets[target] = display_target(original)
            assert set(targets) == {'winner','margin','total'}
            o['models'][family] = targets
        assert set(o['models']) == set(ALIASES.values())
        rows.append(o)
    assert len(rows) == len({r['id'] for r in rows}) == 2403
    metrics = {str(s['season']):s['metrics'] for s in comparison['seasons']}
    for season, values in metrics.items():
        baseline = {(m['family'],m['target']):m for m in prior['metrics'][season]}
        for m in values:
            if m['study'] == 'V038':
                original = baseline[(m['source_family'],m['target'])]
                for key, value in original.items():
                    if key == 'family':
                        continue
                    if key in m:
                        assert m[key] == value
                    else:
                        assert key == 'calibration_bins'
                        m[key] = value
    _, baseline_pin = physical(output/'development-2026.json')
    _, fixture_pin = physical(output/'three-season.json')
    for period in comparison['periods']:
        metrics[period['period']] = period['metrics']
    # The retained current-week scorecard is admitted only on the exact same
    # original cohort hash and denominator; do not rescore rounded values.
    current = metrics['current_week']
    cohort = {(m['exact_game_ids_sha256'],m['games']) for m in current}
    assert len(cohort) == 1
    for m in prior['metrics']['current_week']:
        assert (m['exact_game_ids_sha256'],m['games']) in cohort
        current.append({**m, 'family':'v038_'+m['family'], 'source_family':m['family'], 'study':'V038', 'display_name':'V038 '+m['family'].replace('_',' ')})
    report = {'schema':'sports-edge-lab.fbs-optional-study.v039','evidence_class':EVIDENCE,
              'forecast_issued':False,'historical_availability_proved':False,'promotion_allowed':False,
              'generated_at':comparison['generated_at'],'source_input_identity_sha256':comparison['source_input_identity_sha256'],
              'sources':pins,'retained_baseline_source':baseline_pin,'canonical_fixture_projection':fixture_pin,'default_selection_unchanged':'V038 fixed_equal_blend',
              'counts':comparison['counts'],'libraries':comparison['libraries'],'resources':comparison['resources'],
              'unexecuted_families':comparison['unexecuted_families'],'limitations':comparison['limitations'],
              'seasons':[{k:v for k,v in s.items() if k!='metrics'} for s in comparison['seasons']],
              'metrics':metrics,'retained622_descriptive_comparison':comparison['retained622_descriptive_comparison'],
              'rows':rows}
    text = json.dumps(report,separators=(',',':'),sort_keys=True)
    for forbidden in ['s3://','model_state_sha256','fit_identity_sha256','source_reference','api_key','feature_names','calibration_game_ids']:
        assert forbidden not in text
    (output/'optional-study.json').write_text(text+'\n')
    (output/'optional-study-data.js').write_text('window.FBS_OPTIONAL_STUDY='+text+';\n')
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--output',default=str(ROOT/'docs/fbs'));a=p.parse_args()
    r=build(a.source,a.output);print(json.dumps({'counts':r['counts'],'sources':r['sources'],'seasons':r['seasons']}))
