#!/usr/bin/env python3
"""Render a sanitized, frozen-model Circa snapshot without fitting or networking."""
from __future__ import annotations
import argparse
import hashlib
import gzip
import copy
import html
import json
import os
from pathlib import Path
import tempfile

HERE=Path(__file__).resolve().parent
TOP_FIELDS={'schema','release','generated_at_utc','source_cutoff_utc','current_board','model_views','champions','gaps','source_evidence','no_fit_receipt','adapter_execution','owner','phase','new_fits','automatic_promotion','contest_objective','oot_card_rankings','champion_status','actual_entry_receipts','actual_entry_claim','probability_warning','selection_warning','model_inventory','model_inventory_summary','history_asset','independent_target_forecasts'}
FORBIDDEN_KEYS={'raw_response','raw_payload','credentials','secret','token','authorization','private_path','local_path','cache_path','input_path','source_path','artifact_path','model_weights','features','feature_matrix'}

def public_payload(value):
    if not isinstance(value,dict):raise ValueError('Circa payload must be an object')
    def check(v):
        if isinstance(v,dict):
            for k,x in v.items():
                if k.lower() in FORBIDDEN_KEYS:raise ValueError('Private field in public payload: '+k)
                check(x)
        elif isinstance(v,list):
            for x in v:check(x)
        elif isinstance(v,str) and any(t in v for t in ('/home/','/workspace/','s3://','AKIA','ASIA')):
            raise ValueError('Private path or credential pattern in public payload')
    data={k:v for k,v in value.items() if k in TOP_FIELDS}
    check(data)
    if not isinstance(data.get('model_views'),list):raise ValueError('Missing model views')
    if not isinstance(data.get('current_board'),dict):raise ValueError('Missing current board')
    return data

def encode(data):
    return json.dumps(data,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).replace('&','\\u0026').replace('<','\\u003c').replace('>','\\u003e')

def noscript(data):
    e=lambda x:html.escape(str(x if x is not None else 'Unavailable'))
    board=data.get('current_board',{})
    rows=''.join('<tr><td>'+e(g.get('game_id'))+'</td><td>'+e(g.get('away',g.get('away_team')))+' @ '+e(g.get('home',g.get('home_team')))+'</td><td>'+e(g.get('home_spread'))+'</td><td>'+e(g.get('kickoff_utc'))+'</td></tr>' for g in board.get('games',[]))
    return '<h2>Full official board</h2><p>Cover probabilities and expected points require authenticated distributions; no outright-to-cover substitution.</p><div class="table-wrap"><table><thead><tr><th>Game</th><th>Matchup</th><th>Home spread</th><th>Kickoff</th></tr></thead><tbody>'+rows+'</tbody></table></div><h3>Missing evidence</h3><ul>'+''.join('<li>'+e(g if isinstance(g,str) else json.dumps(g))+'</li>' for g in data.get('gaps',[]))+'</ul>'

def render(data,template,script):
    data=public_payload(data)
    return template.replace('__NOSCRIPT__',noscript(data)).replace('__CIRCA_SCRIPT__',script).replace('__CIRCA_DATA__',encode(data)).encode('utf-8')

def atomic(path,raw):
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():
        if path.read_bytes()==raw:return
        raise FileExistsError('Refusing to overwrite an existing different dashboard asset: '+path.name)
    fd,name=tempfile.mkstemp(prefix='.'+path.name+'.',dir=path.parent)
    try:
        with os.fdopen(fd,'wb') as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
        try:os.link(name,path)
        except FileExistsError:
            if path.read_bytes()!=raw:raise
        dirfd=os.open(path.parent,os.O_RDONLY)
        try:os.fsync(dirfd)
        finally:os.close(dirfd)
    finally:
        Path(name).unlink(missing_ok=True)

def prepare_circa_dashboard(payload_path,output_dir):
    path=Path(payload_path);out=Path(output_dir)
    data=public_payload(json.loads(path.read_text()))
    data=copy.deepcopy(data)
    history={v['model_id']:v['history'] for v in data['model_views']}
    history_raw=encode(history).encode()
    history_gz=gzip.compress(history_raw,compresslevel=6,mtime=0)
    for v in data['model_views']:
        v['history']={'deferred':True,'available_rows':len(v['history'].get('drilldowns',[])),'drilldowns':[]}
    data['history_asset']={'path':'history.json.gz','sha256':hashlib.sha256(history_gz).hexdigest(),'bytes':len(history_gz),'decoded_bytes':len(history_raw),'decoded_sha256':hashlib.sha256(history_raw).hexdigest(),'model_histories':len(history)}
    raw=render(data,(HERE/'site_template_n089.html.in').read_text(),(HERE/'current_n089.js').read_text())
    encoded=(encode(data)+'\n').encode()
    assets={'index.html':raw,'evidence.json':encoded,'history.json.gz':history_gz,'archive/index.html':(HERE/'index.html').read_bytes()}
    receipt={'schema':'sports-edge.circa-publication.v1','release':'N089','state':'PREPARED_NOT_DEPLOYED','new_fits':0,'new_source_calls':0,'source_payload_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'public_payload_sha256':hashlib.sha256(encoded).hexdigest(),'board_games':len(data['current_board'].get('games',[])),'model_views':len(data['model_views']),'assets':{n:{'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)} for n,b in assets.items()}}
    for name,blob in assets.items():atomic(out/name,blob)
    atomic(out/'publication.json',(json.dumps(receipt,indent=2,sort_keys=True)+'\n').encode())
    return receipt

def main():
    p=argparse.ArgumentParser();p.add_argument('payload');p.add_argument('output');args=p.parse_args();print(json.dumps(prepare_circa_dashboard(args.payload,args.output),indent=2))
if __name__=='__main__':main()
