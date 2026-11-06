"""Export the current NFL review and preserve the complete dated prior review."""
import argparse,hashlib,json,pathlib,re,subprocess
from urllib.parse import urlsplit,unquote
from build_review_n050 import build,validate
from export_site_n049 import build_projection
HERE=pathlib.Path(__file__).resolve().parent
ROOT=HERE.parents[1]
REPO='https://github.com/alvaromendizabal/sports-edge-lab'


def projection(current,history,readiness,commit):
    if not re.fullmatch('[0-9a-f]{40}',commit):raise ValueError('Exact canonical commit required')
    def link(m):
        target=m.group(1);parsed=urlsplit(target)
        if parsed.scheme or parsed.netloc or target.startswith('#'):return m.group(0)
        if parsed.path=='review.html':return 'href="history.html'+('#'+parsed.fragment if parsed.fragment else '')+'"'
        path=(HERE/unquote(parsed.path)).resolve()
        if not path.is_relative_to(ROOT) or not path.is_file():raise ValueError('Unresolved public link: '+target)
        relative=path.relative_to(ROOT).as_posix()
        prefix=('https://raw.githubusercontent.com/alvaromendizabal/sports-edge-lab/' if path.suffix in ['.csv','.json'] else REPO+'/blob/')
        return 'href="'+prefix+commit+'/'+relative+('#'+parsed.fragment if parsed.fragment else '')+'"'
    current=re.sub(r'href="([^"]+)"',link,current)
    current=current.replace('Canonical source and dated reports are preserved in the NFL repository.',
        'Canonical commit: <a href="'+REPO+'/commit/'+commit+'">'+commit+'</a>. <a href="provenance.json">Publication provenance</a>.')
    history,unused=build_projection(history,readiness,commit)
    history=history.replace('href="./#','href="history.html#').replace('href="./"','href="history.html"')
    banner='<aside aria-label="Historical snapshot" style="padding:18px;background:#fff1d8;color:#39260b;text-align:center"><strong>Historical view through N048 and the then-prepared N049 continuation.</strong> Later actual N049 evidence supersedes the preparation status below. <a href="index.html" style="color:#175442">Open the current N049 actual / N050 prepared review →</a></aside>'
    history=re.sub(r'(<body[^>]*>)',lambda m:m.group(1)+banner,history,count=1)
    return current,history


def export(output,commit):
    inputs=['review_n050.html','current_review_n050.json','review_n050.template.html',
            'build_review_n050.py','export_site_n050.py','export_site_n049.py',
            'review.html','readiness_n049.json']
    pins={}
    for name in inputs:
        path=HERE/name;raw=path.read_bytes()
        canonical=subprocess.check_output(['git','show',commit+':'+path.relative_to(ROOT).as_posix()],cwd=ROOT)
        if raw!=canonical:raise ValueError('Uncommitted publication input: '+name)
        pins[name]={'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
    data=validate(json.loads((HERE/'current_review_n050.json').read_text()))
    current=(HERE/'review_n050.html').read_text()
    if current!=build(data):raise ValueError('Generated review drift')
    current,history=projection(current,(HERE/'review.html').read_text(),json.loads((HERE/'readiness_n049.json').read_text()),commit)
    output.mkdir(parents=True,exist_ok=True)
    files={'index.html':current,'history.html':history}
    for name,value in files.items():(output/name).write_text(value)
    provenance={'role':'public_static_publication_mirror','canonical_repository':REPO,
                'canonical_commit':commit,'research_state':'N049 actual partial; N050 prepared, not owner-executed',
                'evidence_as_of':data['as_of'],'canonical_inputs':pins,
                'hosted_files':{name:{'bytes':len(value.encode()),'sha256':hashlib.sha256(value.encode()).hexdigest()} for name,value in files.items()},
                'transformations':['Pin public links to the canonical commit','Preserve the complete historical review on history.html','Label superseded preparation state as historical','Add canonical publication provenance'],
                'private_model_bodies':'not included','licensed_raw_data':'not included'}
    (output/'provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
    return provenance

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--commit',required=True);p.add_argument('--output',required=True,type=pathlib.Path);a=p.parse_args();print(json.dumps(export(a.output,a.commit),indent=2))
