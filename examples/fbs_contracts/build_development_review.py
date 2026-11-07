"""Whitelist the sealed V038 development reconstruction; never create forecasts."""
from pathlib import Path
import argparse, collections, datetime, gzip, hashlib, json, math
ROOT=Path(__file__).resolve().parents[2]
EVIDENCE='RETROSPECTIVE_DEVELOPMENT_TIMING_UNCERTIFIED'

def physical(path):
    b=path.read_bytes();return {'file':path.name,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}

def build(source, output):
    source=Path(source);output=Path(output)
    prediction=source/'full2026_resume/FULL2026_PREDICTIONS.json.gz'
    summary=source/'full2026_resume/FULL2026_RESULTS.json'
    historical=source/'COMPLETE_SCIENTIFIC_RESULTS.json'
    current=source/'current_week/CURRENT_WEEK_RESULTS.json'
    dataset=source/'RETAINED_INPUT_DATASET.json.gz'
    rows=json.load(gzip.open(prediction,'rt'));s=json.loads(summary.read_text());h=json.loads(historical.read_text());c=json.loads(current.read_text());inputs=json.load(gzip.open(dataset,'rt'))
    assert h['evidence_class']==EVIDENCE and h['forecast_issued'] is False and h['historical_availability_proved'] is False and h['promotion_allowed'] is False
    seasons={str(x['season']):x for x in h['seasons']}
    cumulative=dict(h['unique_fit_accounting'])
    cumulative.update(compatible_fit_state_reuses=sum(x['reused_fit_states'] for x in h['run_metrics'].values()), target_outputs=sum(x['output_count'] for x in h['seasons']), games_with_predictions=sum(x['games_with_all_available_predictions'] for x in h['seasons']))
    coverage=[{'season':x['season'],'identified':x['identified_games'],'predicted':x['games_with_all_available_predictions'],'observed_evaluation_games':sorted({m['games'] for m in x['metrics']}),'insufficient_history':len(x['known_kickoff_without_predictions']),'exact_kickoff_unresolved':len(x['TBD_records'])} for x in h['seasons']]
    assert s['status']=='BOUNDED_REGISTERED_WORK_COMPLETE' and s['target_games_requested']==790
    original=json.loads((output/'complete-season.json').read_text())
    games={r[0]:dict(zip(original['columns'],r)) for r in original['rows']}
    ir={r['game_id']:r for r in inputs['rows'] if r['season']==2026}
    output_rows={};families=collections.defaultdict(set)
    keys=('prediction','computed_at_utc','train_rows','calibration_rows')
    for r in rows:
        gid=r['official_game_id'];g=games[gid];i=ir[gid]
        assert r['game_id']==gid and r['season']==2026
        assert r['evidence_class']==EVIDENCE and r['forecast_issued'] is False and r['historical_availability_proved'] is False
        assert (r['home_id'],r['away_id'],r['kickoff_utc'])==(i['home_id'],i['away_id'],g['kickoff'])
        assert (i['home_team'],i['away_team'])==(g['home'],g['away'])
        assert r['reconstructed_cutoff_utc']==i['cutoff_utc']<r['kickoff_utc']
        assert math.isfinite(r['prediction'])
        if r['target']=='winner':assert 0<=r['prediction']<=1
        o=output_rows.setdefault(gid,{'id':gid,'kickoff':r['kickoff_utc'],'cutoff':r['reconstructed_cutoff_utc'],'models':{}})
        family=o['models'].setdefault(r['family'],{})
        assert r['target'] not in family
        family[r['target']]={k:r[k] for k in keys if k in r}
        if r['family']=='fixed_equal_blend':family[r['target']].update(blend_members=r['blend_members'],blend_weights=r['blend_weights'])
        families[r['family']].add(r['target'])
    assert len(output_rows)==790 and all(set(x['models']['fixed_equal_blend'])=={'winner','margin','total'} for x in output_rows.values())
    assert sum(games[k]['period']=='current' for k in output_rows)==63
    missing=[{'id':gid,'reason':'EXACT_KICKOFF_UNRESOLVED'} for gid in games if gid not in output_rows]
    assert len(missing)==98
    report={'schema':'sports-edge-lab.fbs-development-review.v038','evidence_class':EVIDENCE,
        'forecast_issued':False,'historical_availability_proved':False,'promotion_allowed':False,
        'schedule_observed_at':original['source_observed_at'],'computed_at':s['finished_at'],'registered_at':s['registered_at'],
        'default_family':'fixed_equal_blend','default_policy':'Fixed equal weights specified before evaluation; no score-selected weights.',
        'feature_count':inputs['feature_count'],'source_clock_policy':inputs['source_clock_policy'],
        'input_identity_sha256':s['source_input_identity_sha256'],'invocation_id':s['invocation_id'],
        'sources':[physical(p) for p in (prediction,summary,historical,current,dataset)],
        'counts':{'identified':888,'predicted':790,'current_week':63,'kickoff_unresolved':98,'observed_outcomes':629},
        'resume_work':{k:s[k] for k in ('new_base_fits','new_calibration_fits','reused_fit_states','failed_fits','elapsed_seconds','cpu_seconds','maxrss_kib','provider_requests','s3_requests')},
        'scientific_results_generated_at':h['generated_at'],'cumulative_work':cumulative,'season_coverage':coverage,
        'families':{k:sorted(v) for k,v in families.items()},'rows':list(output_rows.values()),'unresolved':missing,
        'metrics':{'2026':s['metrics'],'current_week':c['metrics'],'2024':seasons['2024']['metrics'],'2025':seasons['2025']['metrics']},
        'metric_note':'Development reconstruction only. 2024 has 679 predicted games and 678 observed evaluation outcomes; 240 early games lack admitted history and one has unresolved kickoff. 2025 covers all 934 identified games and outcomes. 2026 covers all 790 exact-kickoff games and 629 observed outcomes, with 98 kickoff-unresolved fixtures. Current week has only seven observed outcomes. Compare exact cohort IDs; no champion improvement claim.'}
    text=json.dumps(report,separators=(',',':'),sort_keys=True)
    (output/'development-2026.json').write_text(text+'\n')
    (output/'development-data.js').write_text('window.FBS_DEVELOPMENT_STUDY='+text+';\n')
    return report
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--output',default=str(ROOT/'docs/fbs'));a=p.parse_args();r=build(a.source,a.output);print(json.dumps({'counts':r['counts'],'resume_work':r['resume_work'],'sources':r['sources']}))
