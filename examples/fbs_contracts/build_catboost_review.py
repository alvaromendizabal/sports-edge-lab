"""Publish an authenticated CatBoost display projection without refitting.

Every displayed target is matched to the full-precision saved original and the
existing official fixture identity. Aggregate metrics retain their precision.
"""
from pathlib import Path
import argparse
import gzip
import json
from examples.fbs_contracts.build_three_season_review import physical, display_target, EVIDENCE

ROOT = Path(__file__).resolve().parents[2]
PINS = {
    'V040_CATBOOST_PUBLIC_COMPARISON.json': (105082, '819d0fb707fe61b9f736b98678426c92311e31072a4ae7bfa37f879b9f0d6286'),
    'V040_CATBOOST_GAME_PROJECTIONS.json.gz': (400921, 'bd30ca4be28403d815a5073b222601b63887659366aad28e545796cb8c8764d1'),
    'ALL_KNOWN_KICKOFF_PREDICTIONS.json.gz': (1558721, 'cdc95f875ac39336a994262ce14b6a0fd6db79a7da6bf8976d60a8718a171a11'),
}
ALIASES = {'catboost': 'v040_catboost'}


def build(source, output):
    source, output = Path(source), Path(output)
    assert len(PINS) == 3, 'Completed study physical pins are required'
    bodies, pins = {}, []
    for name, expected in PINS.items():
        body, pin = physical(source/name, expected)
        bodies[name] = body
        pins.append(pin)
    comparison = json.loads(bodies['V040_CATBOOST_PUBLIC_COMPARISON.json'])
    compact = json.loads(gzip.decompress(bodies['V040_CATBOOST_GAME_PROJECTIONS.json.gz']))
    raw = json.loads(gzip.decompress(bodies['ALL_KNOWN_KICKOFF_PREDICTIONS.json.gz']))
    canonical = json.loads((output/'three-season.json').read_text())
    prior = json.loads((output/'development-2026.json').read_text())
    optional = json.loads((output/'optional-study.json').read_text())
    games = {r['id']: r for r in canonical['rows']}
    assert compact['source_report_physical'] == {'bytes': pins[0]['bytes'], 'sha256': pins[0]['sha256']}
    assert comparison['evidence_class'] == compact['evidence_class'] == EVIDENCE
    assert comparison['source_input_identity_sha256'] == prior['input_identity_sha256'] == compact['source_input_identity_sha256']
    assert not comparison['forecast_issued'] and not comparison['promotion_allowed']
    records = {}
    for row in raw:
        key = (row['game_id'], ALIASES[row['family']], row['target'])
        assert key not in records and not row['forecast_issued'] and not row['historical_availability_proved']
        assert row['evidence_class'] == EVIDENCE
        records[key] = row
    rows = []
    for row in compact['games']:
        g = games[row['game_id']]
        assert (row['season'],row['home_id'],row['away_id'],row['kickoff_utc'],row['reconstructed_cutoff_utc']) == (g['season'],g['home_id'],g['away_id'],g['kickoff'],g['cutoff'])
        o = {'id': g['id'], 'season': g['season'], 'kickoff': g['kickoff'], 'cutoff': g['cutoff'], 'models': {}}
        for family, model in row['models'].items():
            assert family == 'v040_catboost' and model['cover_probability'] is None
            targets = {}
            for target, value in model['targets'].items():
                original = records[(g['id'],family,target)]
                assert original['prediction'] == value['prediction']
                assert (original['home_id'],original['away_id'],original['kickoff_utc'],original['reconstructed_cutoff_utc']) == (g['home_id'],g['away_id'],g['kickoff'],g['cutoff'])
                for field in ('interval80','interval95'):
                    if field in value:
                        assert original.get(field) == value[field]
                targets[target] = display_target(original)
            assert targets and set(targets) <= {'winner','margin','total'}
            o['models'][family] = targets
        assert set(o['models']) == {'v040_catboost'}
        absent = {'winner','margin','total'}-set(o['models']['v040_catboost'])
        assert set(row['models']['v040_catboost'].get('missing_targets',{})) == absent
        o['missing_targets'] = {target: 'Winner state missing after interrupted computation; point estimates retained' for target in absent}
        assert all(row['models']['v040_catboost']['missing_targets'][target]=='PENDING_FIT_RECOVERY_REQUIRED' for target in absent)
        rows.append(o)
    assert 0 < len(rows) == len({r['id'] for r in rows}) <= 2403
    assert len(records) == sum(len(r['models']['v040_catboost']) for r in rows) == comparison['counts']['new_prediction_outputs']
    metrics = {str(s['season']): s['metrics'] for s in comparison['seasons']}
    metrics.update({p['period']: p['metrics'] for p in comparison['periods']})
    max_baseline_roundoff = 0.0
    def equivalent(a,b):
        nonlocal max_baseline_roundoff
        if type(a) is float and isinstance(b,(int,float)):
            error=abs(a-b);max_baseline_roundoff=max(max_baseline_roundoff,error)
            return error <= 1e-12
        if isinstance(a,list) and isinstance(b,list):
            return len(a)==len(b) and all(equivalent(x,y) for x,y in zip(a,b))
        if isinstance(a,dict) and isinstance(b,dict):
            return set(a)==set(b) and all(equivalent(a[k],b[k]) for k in a)
        return a==b
    for cohort, values in metrics.items():
        assert all(m['games'] > 0 and m['exact_game_ids_sha256'] for m in values)
        originals = {(m['family'],m['target']):m for m in optional['metrics'].get(cohort,[])}
        for m in values:
            if m.get('study') in ('V038','V039') and (m['family'],m['target']) in originals:
                original = originals[(m['family'],m['target'])]
                if (m['games'],m['exact_game_ids_sha256']) != (original['games'],original['exact_game_ids_sha256']):
                    continue  # A separately rescored exact common subset keeps its own denominator.
                for key, value in original.items():
                    if key in ('family','display_name','source_family','study'):
                        continue
                    if key in m:
                        assert equivalent(value,m[key]), (cohort,m['family'],key)
                    # Preserve the original full-precision value on an identical
                    # cohort after numerical replay, including saved bins.
                    m[key] = value
    _, baseline_pin = physical(output/'development-2026.json')
    _, optional_pin = physical(output/'optional-study.json')
    _, fixture_pin = physical(output/'three-season.json')
    gap_fields=('game_id','season','target','kickoff_utc','status')
    gaps=[{key:r[key] for key in gap_fields} for r in comparison['pending_output_gaps']]
    assert {(r['game_id'],r['target']) for r in gaps} == {(r['id'],t) for r in rows for t in r['missing_targets']}
    allowed_resources=('attempt02_exact_peak_bytes','attempt02_peak_exceeded_process_cap','attempt04_actual_exit','attempt04_unmatched_intent_preserved','cost_limitation','cpu_threads','dollar_cost','fit_concurrency','maximum_resident_model_states_after_resume','new_source_refreshes','new_sports_provider_requests','original_memory_reserve_bytes','original_process_cap_bytes','s3_requests_by_science','sum_completed_fit_wall_seconds')
    resources={key:comparison['resources'][key] for key in allowed_resources}
    resources['attempt05_actual_exit']={key:comparison['resources']['attempt05_actual_exit'][key] for key in ('actual_interpreter_exit','elapsed_seconds','started_at','finished_at','observer')}
    libraries={key:value['version'] for key,value in comparison['implementation']['required_distribution_records'].items()}
    report = {'schema':'sports-edge-lab.fbs-catboost-study.v040', 'evidence_class':EVIDENCE,
              'forecast_issued':False,'historical_availability_proved':False,'promotion_allowed':False,
              'generated_at':comparison['generated_at'],'source_input_identity_sha256':comparison['source_input_identity_sha256'],
              'sources':pins,'retained_baseline_sources':[baseline_pin,optional_pin],'canonical_fixture_projection':fixture_pin,
              'default_selection_unchanged':'V038 fixed_equal_blend','counts':comparison['counts'],
              'libraries':libraries,'resources':resources,'registered_workload_complete':comparison['registered_workload_complete'],'pending_output_gaps':gaps,'baseline_original_full_precision_sources':comparison['baseline_original_full_precision_sources'],
              'unexecuted_families':comparison['unexecuted_families'],'limitations':comparison['limitations'],
              'seasons':[{**{k:v for k,v in s.items() if k not in ('metrics','missing_target_outputs')},'missing_target_outputs':[r for r in gaps if r['season']==s['season']]} for s in comparison['seasons']],
              'retained_same_cohort_metric_max_replay_roundoff':max_baseline_roundoff,'metrics':metrics,'target_coverage':{str(season):{target:sum(r['season']==season and target in r['models']['v040_catboost'] for r in rows) for target in ('winner','margin','total')} for season in (2024,2025,2026)},'rows':rows}
    text = json.dumps(report,separators=(',',':'),sort_keys=True)
    for forbidden in ['s3://','model_state_sha256','fit_identity_sha256','source_reference','api_key','feature_names','calibration_game_ids','/workspace/','child_pid','model_parameters','wrapper_sha256']:
        assert forbidden not in text, forbidden
    (output/'catboost-study.json').write_text(text+'\n')
    (output/'catboost-study-data.js').write_text('window.FBS_CATBOOST_STUDY='+text+';\n')
    return report


if __name__ == '__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--output',default=str(ROOT/'docs/fbs'));a=p.parse_args()
    r=build(a.source,a.output)
    print(json.dumps({'counts':r['counts'],'sources':r['sources'],'seasons':r['seasons']}))
