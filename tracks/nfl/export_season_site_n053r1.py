"""Export the exact complete-season commit and preserve dated research pages."""
import argparse,hashlib,json,pathlib,re,subprocess
from urllib.parse import urlsplit,unquote
from build_season_review_n053r1 import build,validate,load
from export_site_n053 import projection as previous_projection
HERE=pathlib.Path(__file__).resolve().parent;ROOT=HERE.parents[1]
REPO='https://github.com/alvaromendizabal/sports-edge-lab'

def projection(current,commit):
    if not re.fullmatch('[0-9a-f]{40}',commit):raise ValueError('Exact canonical commit required')
    def link(m):
        target=m.group(1);parsed=urlsplit(target)
        if parsed.scheme or parsed.netloc or target.startswith('#'):return m.group(0)
        if parsed.path=='review.html':return 'href="history.html'+('#'+parsed.fragment if parsed.fragment else '')+'"'
        if parsed.path=='review_n053.html':return 'href="previous.html'+('#'+parsed.fragment if parsed.fragment else '')+'"'
        path=(HERE/unquote(parsed.path)).resolve()
        if not path.is_relative_to(ROOT) or not path.is_file():raise ValueError('Unresolved public link: '+target)
        relative=path.relative_to(ROOT).as_posix();prefix=('https://raw.githubusercontent.com/alvaromendizabal/sports-edge-lab/' if path.suffix in ['.csv','.json'] else REPO+'/blob/')
        return 'href="'+prefix+commit+'/'+relative+('#'+parsed.fragment if parsed.fragment else '')+'"'
    current=re.sub(r'href="([^"]+)"',link,current)
    return current.replace('Canonical source and dated reports are preserved in the NFL repository.','Canonical commit: <a href="'+REPO+'/commit/'+commit+'">'+commit+'</a>. <a href="provenance.json">Publication provenance</a>.')

def export(output,commit):
    inputs=['season_review_n053r1.html','current_season_n053r1.json.gz','season_review_n053r1.template.html','build_season_review_n053r1.py','export_season_site_n053r1.py','test_season_review_n053r1.py','browser_season_n053r1.cjs','README.md','SEASON_REVIEW_N053R1.md','review_n053.html','current_review_n053.json','export_site_n053.py','export_site_n050.py','export_site_n049.py','review.html','readiness_n049.json']
    pins={}
    for name in inputs:
        path=HERE/name;raw=path.read_bytes();canonical=subprocess.check_output(['git','show',commit+':'+path.relative_to(ROOT).as_posix()],cwd=ROOT)
        if raw!=canonical:raise ValueError('Uncommitted publication input: '+name)
        pins[name]={'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
    data=validate(load());current=(HERE/'season_review_n053r1.html').read_text()
    if current!=build(data):raise ValueError('Generated season review drift')
    current=projection(current,commit)
    previous,history=previous_projection((HERE/'review_n053.html').read_text(),(HERE/'review.html').read_text(),json.loads((HERE/'readiness_n049.json').read_text()),commit)
    banner='<aside aria-label="Historical snapshot" style="padding:18px;background:#fff1d8;color:#39260b;text-align:center"><strong>Dated research archive. The complete current-season view is separate.</strong> <a href="index.html" style="color:#175442">Open all272games and actual N052 evidence →</a></aside>'
    previous=re.sub(r'(<body[^>]*>)',lambda m:m.group(1)+banner,previous,count=1)
    history=re.sub(r'(<body[^>]*>)',lambda m:m.group(1)+banner,history,count=1)
    output.mkdir(parents=True,exist_ok=True);files={'index.html':current,'previous.html':previous,'history.html':history}
    for name,value in files.items():(output/name).write_text(value)
    provenance={'role':'public_static_publication_mirror','canonical_repository':REPO,'canonical_commit':commit,'research_state':'Actual N052; complete272-game schedule/122finals/150future; N053R1prepared,not owner-executed. Original cohorts and source clocks preserved.','evidence_as_of':data['as_of'],'canonical_inputs':pins,'hosted_files':{name:{'bytes':len(value.encode()),'sha256':hashlib.sha256(value.encode()).hexdigest()} for name,value in files.items()},'transformations':['Complete schedule as active default','Equal provider event inventory and explicit horizons','Exact canonical source links','Retain earlier scientific views as dated archives','Original raw/source/model/issue evidence unchanged'],'new_owner_fits':0,'new_owner_issues':0,'new_source_acquisitions':0,'private_model_bodies':'not included','licensed_raw_data':'not included'}
    (output/'provenance.json').write_text(json.dumps(provenance,indent=2)+'\n');return provenance

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--commit',required=True);p.add_argument('--output',required=True,type=pathlib.Path);a=p.parse_args();print(json.dumps(export(a.output,a.commit),indent=2))
