"""Prepare an exact-commit FBS site, retaining all committed FBS public assets.

This writes a local static export only. It performs no Site operation, source
request, model fit, policy promotion or publication. Every input is an immutable
Git object within docs/fbs; no private workspace or provider cache is traversed.
"""
from __future__ import annotations
import argparse
import hashlib
import html
import importlib.util
import json
from pathlib import Path
import posixpath
import re
import subprocess
from urllib.parse import urlsplit

ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
REPOSITORY='https://github.com/alvaromendizabal/sports-edge-lab'
ALLOWED_SUFFIXES={'.html','.css','.js','.json','.csv','.md','.gz','.svg','.png','.jpg','.webp'}


def require(condition,message):
    if not condition:raise ValueError(message)


def committed(commit,path):
    return subprocess.check_output(['git','show',f'{commit}:{path}'],cwd=ROOT)


def module(path,name):
    spec=importlib.util.spec_from_file_location(name,path)
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value


def export(commit,output):
    require(re.fullmatch('[0-9a-f]{40}',commit),'Full exact source commit required')
    subprocess.run(['git','cat-file','-e',commit+'^{commit}'],cwd=ROOT,check=True)
    output=Path(output).resolve()
    require(not output.exists() or not any(output.iterdir()),'Static export destination must be empty')
    for name in ('export_site.py','build_review.py','template.html.in','public_shapes.json'):
        path='examples/fbs_contracts/v116/'+name
        require(committed(commit,path)==(ROOT/path).read_bytes(),'Exporter helper differs from exact source commit: '+path)
    review=module(HERE/'build_review.py','fbs_v116_public_review_export')
    data_raw=committed(commit,'docs/fbs/v116/data/review.json')
    data=json.loads(data_raw);body=committed(commit,'docs/fbs/v116/index.html')
    require(review.render(data)==body,'Committed dashboard differs from committed bounded evidence')
    names=subprocess.check_output(['git','ls-tree','-r','--name-only',commit,'docs/fbs'],cwd=ROOT,text=True).splitlines()
    require(bool(names) and all(name.startswith('docs/fbs/') for name in names),'FBS public tree required')
    require(all(Path(name).suffix in ALLOWED_SUFFIXES or Path(name).name=='.nojekyll' for name in names),
            'Unrecognized public artifact type; review explicit export scope')
    sources=set(names)
    def navigation(target,source):
        u=urlsplit(html.unescape(target))
        if u.scheme or u.netloc:
            return target.replace(REPOSITORY+'/tree/main/',REPOSITORY+'/tree/'+commit+'/')
        if not u.path:return target
        path=posixpath.normpath(posixpath.join(posixpath.dirname(source),u.path))
        if path in sources:return target
        # Preserve relative links to repository prose at this exact commit.
        require(not path.startswith(('../','/')),'Navigation escaped repository')
        subprocess.run(['git','cat-file','-e',f'{commit}:{path}'],cwd=ROOT,check=True,stdout=subprocess.DEVNULL)
        return REPOSITORY+'/blob/'+commit+'/'+path+('#'+u.fragment if u.fragment else '')
    output.mkdir(parents=True,exist_ok=True);records=[]
    for source in names:
        name=source.removeprefix('docs/fbs/');raw=committed(commit,source)
        if name.endswith('.html'):
            text=raw.decode()
            text=re.sub(r'href="([^"]+)"',lambda m:'href="'+navigation(m.group(1),source)+'"',text)
            raw=text.encode()
        target=output/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
        records.append({'name':name,'source_path':source,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
    # Keep the former root page accessible; all other dated routes stay intact.
    prior=(output/'index.html').read_bytes();(output/'retained-index-before-v116.html').write_bytes(prior)
    records.append({'name':'retained-index-before-v116.html','source_path':'docs/fbs/index.html',
                    'bytes':len(prior),'sha256':hashlib.sha256(prior).hexdigest()})
    home=(output/'v116/index.html').read_text()
    # V116 self-contained runtime has only section anchors and absolute outgoing
    # links; rebasing it to root does not change any data or runtime dependency.
    require(not re.search(r'(?:href|src)="(?!#|https?://|data:)[^"]+"',home),'V116 root rebase requires self-contained navigation')
    (output/'index.html').write_text(home)
    records=[r for r in records if r['name']!='index.html']
    records.append({'name':'index.html','source_path':'docs/fbs/v116/index.html',
                    'bytes':len(home.encode()),'sha256':hashlib.sha256(home.encode()).hexdigest()})
    current=data.get('current_diagnostic')
    manifest={'schema':'fbs.v116.exact-commit-static-export.v1','canonical_repository':REPOSITORY,
        'source_commit_sha':commit,'primary_dashboard_source':'docs/fbs/v116/index.html',
        'previous_homepage_retained_at':'retained-index-before-v116.html',
        'publication_status':'STATIC_EXPORT_PREPARED_NO_DEPLOYMENT_PERFORMED',
        'owner_runs_started':0,'new_model_fits':0,'new_provider_calls':0,'production_model_promoted':False,
        'public_files':records,'source_json_sha256':hashlib.sha256(data_raw).hexdigest(),
        'evidence_prepared_at':data['prepared_at_utc'],'latest_owner_execution':data['execution'],
        'retained_scientific_snapshot':data['snapshot'],'selection':data['selection'],
        'current_diagnostic':{key:current[key] for key in (
            'status','source_as_of_utc','snapshot_as_of_utc','market_source_as_of_utc','game_count',
            'completed_games','weekly_games','weekly_complete_policy_games','weekly_missing_policy_games',
            'inference_status','expected_cells','available_cells','new_model_fits','new_calibrator_fits',
            'all_bookmaker_labels','all_bookmaker_observed_rows','all_bookmaker_qualified_rows')} if current else None}
    (output/'published-snapshot.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
    for record in records:
        raw=(output/record['name']).read_bytes()
        require(len(raw)==record['bytes'] and hashlib.sha256(raw).hexdigest()==record['sha256'],
                'Export readback integrity failed: '+record['name'])
    return {'status':'VERIFIED_STATIC_EXPORT_PREPARED','source_commit':commit,
            'public_assets':len(records),'output':str(output),'new_model_fits':0,
            'new_provider_calls':0,'website_deployed':False,'other_owner_files_changed':False}


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--commit',required=True);parser.add_argument('--output',required=True)
    args=parser.parse_args();print(json.dumps(export(args.commit,args.output),sort_keys=True))
