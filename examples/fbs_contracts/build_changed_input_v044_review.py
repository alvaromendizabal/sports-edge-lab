"""Whitelist the original V043 changed-input owner study without refitting it."""
from pathlib import Path
import argparse
import gzip
import json
from examples.fbs_contracts.build_three_season_review import physical, display_target, EVIDENCE

ROOT=Path(__file__).resolve().parents[2]
PINS={
 'FBS_V044_REFRESH_GAME_PROJECTIONS.json':(1686584,'8ced7cfa0ed6f67bdee67c29cc76b378be0b5cf065b68882766a57daddb567fa'),
 'FBS_V044_REFRESH_MODEL_COMPARISON.json':(6301,'8567b06d9efba0b9871bc962c9bc4d877755309e6201a5dbefc1c6947d4d999b'),
}
RAW_PIN=(1064598,'fba5dbf1e9811e852b73b647201c2b1e70cde5a80b7d3ec09b87c94657d81ff8')
DISPLAY={'extra_trees':'Extra Trees','hist_gradient_boosting':'Histogram boosting','lightgbm':'LightGBM','linear':'Linear · points only','logistic':'Logistic · winner only','pytorch':'PyTorch','ridge':'Ridge · points only','tensorflow':'TensorFlow','xgboost':'XGBoost','fixed_equal_blend/neural':'Neural fixed blend','fixed_equal_blend/optional_trees':'Optional-tree fixed blend','fixed_equal_blend/sklearn':'Scikit-learn fixed blend'}


def build(source,raw_path,output):
 source,output=Path(source),Path(output);data={};pins=[]
 for name,pin in PINS.items():
  body,verified=physical(source/name,pin);data[name]=json.loads(body);pins.append(verified)
 rawbody,rawpin=physical(Path(raw_path),RAW_PIN);original=json.loads(gzip.decompress(rawbody));pins.append(rawpin)
 compact=data['FBS_V044_REFRESH_GAME_PROJECTIONS.json'];comparison=data['FBS_V044_REFRESH_MODEL_COMPARISON.json']
 assert original['forecast_issued'] is False and original['promotion_allowed'] is False and original['original_default_replaced'] is False
 assert original['registered_workload_complete'] is True
 assert compact['source_input_identity']==comparison['source_input_identity']==original['input_identity_sha256']
 assert compact['source_report_physical']==comparison['source_report_physical']=={'bytes':RAW_PIN[0],'sha256':RAW_PIN[1]}
 for source_record in (compact,comparison):
  assert all(source_record['limits'][k] is False for k in ('forecast_issued','historical_availability_proved','promotion_allowed'))
 fixtures={r['id']:r for r in json.loads((output/'three-season.json').read_text())['rows']}
 latest={r['id']:r for r in json.loads((output/'current-capture-v044.json').read_text())['rows']}
 families=[{'id':f['id'],'source_family':f['source_family'],'label':DISPLAY[f['source_family']]+' · changed-input refresh'} for f in compact['families']]
 aliases={f['source_family']:f['id'] for f in families};assert len(aliases)==12
 raw={}
 for r in original['predictions']:
  key=(r['game_id'],aliases[r['family']],r['target']);assert key not in raw
  assert r['evidence_class']==EVIDENCE and r['forecast_issued'] is False and r['historical_availability_proved'] is False
  raw[key]=r
 rows=[];clocks=[];current=0
 for r in compact['games']:
  g=fixtures[r['id']];assert r['game_id']==g['id'] and g['kickoff_exact']
  assert tuple(r[k] for k in ('season','home_id','away_id','kickoff','cutoff'))==tuple(g[k] for k in ('season','home_id','away_id','kickoff','cutoff'))
  assert latest[g['id']]['completed'] is False and g['season']==2026
  current+=g['period']=='current'
  assert set(r['models'])==set(aliases.values())
  out={'id':g['id'],'season':g['season'],'kickoff':g['kickoff'],'cutoff':g['cutoff'],'models':{}}
  for family,model in r['models'].items():
   targets={}
   for target,value in model['targets'].items():
    saved=raw[(g['id'],family,target)]
    assert (saved['home_id'],saved['away_id'],saved['kickoff_utc'],saved['reconstructed_cutoff_utc'])==(g['home_id'],g['away_id'],g['kickoff'],g['cutoff'])
    for field in ('prediction','computed_at_utc','interval80','interval95'):assert value.get(field)==saved.get(field),(g['id'],family,target,field)
    targets[target]=display_target(saved)
    targets[target]['computed_before_cutoff']=value['computed_before_cutoff']
    for field in ('train_rows','calibration_rows'):
     if field in saved:targets[target][field]=saved[field]
    clocks.append(saved['computed_at_utc'])
   out['models'][family]=targets
  rows.append(out)
 assert len(rows)==len({r['id'] for r in rows})==119 and current==14
 assert len(raw)==sum(len(m) for r in rows for m in r['models'].values())==3808
 assert comparison['counts']['scored_games']==0
 assert all(not period['metrics'] and period['observed_completed']==0 for period in comparison['periods'].values())
 report={'schema':'sports-edge-lab.fbs-changed-input-study.v044','evidence_class':EVIDENCE,'forecast_issued':False,'historical_availability_proved':False,'promotion_allowed':False,
  'generated_at':comparison['generated_at'],'sources':pins,'counts':comparison['counts'],'default_selection_unchanged':'V038 fixed_equal_blend',
  'original_computation_first':min(clocks),'original_computation_last':max(clocks),'current_reporting_new_fits':0,'current_reporting_new_predictions':0,'current_reporting_provider_requests':0,
  'coverage':comparison['periods'],'metrics':{k:v['metrics'] for k,v in comparison['periods'].items()},'families':families,'rows':rows,
  'limitations':['119 registered 2026 targets: 14 current-week and 105 later games; no previous-week or historical targets.','No target has an observed final in the latest capture. All refresh performance metrics remain pending.','38 changed training outcomes retain two separate original acquisition clocks; older history retains the retrospective availability proxy limitation.','The newest three finals were not training inputs. No current-season model selection or promotion.','448 outputs were computed at or after their reconstructed cutoff; 3360 before. Neither group establishes genuine issuance.','CatBoost protected incomplete work remains separate and was not refitted.','No qualified cover output; fixed blends have no fabricated interval.']}
 text=json.dumps(report,separators=(',',':'),sort_keys=True)
 for forbidden in ('s3://','fit_identity_sha256','model_state_sha256','source_reference','api_key','feature_names','calibration_game_ids','/workspace/','model_parameters','actual_game_ids','raw_probability'):assert forbidden not in text,forbidden
 (output/'changed-input-study-v044.json').write_text(text+'\n');(output/'changed-input-study-v044-data.js').write_text('window.FBS_CHANGED_INPUT_STUDY='+text+';\n')
 return {k:report[k] for k in ('counts','original_computation_first','original_computation_last')}

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--original',required=True);p.add_argument('--output',default=str(ROOT/'docs/fbs'));a=p.parse_args();print(json.dumps(build(a.source,a.original,a.output),sort_keys=True))
