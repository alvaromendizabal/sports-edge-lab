"""Export exact committed N052 evidence while retaining both earlier views."""
import argparse,hashlib,json,pathlib,re,subprocess
from build_review_n053 import build,validate
from export_site_n050 import projection as prior_projection
HERE=pathlib.Path(__file__).resolve().parent;ROOT=HERE.parents[1]
REPO='https://github.com/alvaromendizabal/sports-edge-lab'


def projection(current,history,readiness,commit):
    current,history=prior_projection(current,history,readiness,commit)
    history=history.replace('Later actual N049 evidence supersedes the preparation status below.','Later actual N049, N050 and N052 evidence supersedes the preparation status below.')
    history=history.replace('Open the current N049 actual / N050 prepared review','Open the current N052 actual / N053 prepared review')
    current=current.replace(REPO+'/blob/'+commit+'/tracks/nfl/review_n052.html','previous.html')
    return current,history


def export(output,commit):
    inputs=['review_n052.html','current_review_n052.json','review_n052.template.html','build_review_n053.py','export_site_n052.py','test_current_review_n052.py','browser_current_n052.cjs','N052_RESEARCH_UPDATE.md','README.md','export_site_n050.py','export_site_n049.py','review.html','readiness_n049.json','review_n052.html','current_review_n052.json','review_n051.html','current_review_n051.json','current_review_n050.json']
    pins={}
    for name in inputs:
        path=HERE/name;raw=path.read_bytes();canonical=subprocess.check_output(['git','show',commit+':'+path.relative_to(ROOT).as_posix()],cwd=ROOT)
        if raw!=canonical:raise ValueError('Uncommitted publication input: '+name)
        pins[name]={'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
    data=validate(json.loads((HERE/'current_review_n053.json').read_text()));current=(HERE/'review_n053.html').read_text()
    if current!=build(data):raise ValueError('Generated review drift')
    readiness=json.loads((HERE/'readiness_n049.json').read_text());history=(HERE/'review.html').read_text()
    current,history=projection(current,history,readiness,commit)
    previous,_=prior_projection((HERE/'review_n052.html').read_text(),(HERE/'review.html').read_text(),readiness,commit)
    banner='<aside aria-label="Historical snapshot" style="padding:18px;background:#fff1d8;color:#39260b;text-align:center"><strong>Dated N051 completed study; its N052 preparation status is superseded.</strong> <a href="index.html" style="color:#175442">Open actual N052 results and N053 preparation →</a></aside>'
    previous=re.sub(r'(<body[^>]*>)',lambda m:m.group(1)+banner,previous,count=1)
    output.mkdir(parents=True,exist_ok=True);files={'index.html':current,'history.html':history,'previous.html':previous}
    for name,value in files.items():(output/name).write_text(value)
    provenance={'role':'public_static_publication_mirror','canonical_repository':REPO,'canonical_commit':commit,'research_state':'N052 actual:150 correction states,41,503 report rows,255 comparisons,0 native refits,418 issues; research acceptance false. Prior144/864 negative study reused. N053 prepared,not owner-executed.','evidence_as_of':data['as_of'],'canonical_inputs':pins,'hosted_files':{name:{'bytes':len(value.encode()),'sha256':hashlib.sha256(value.encode()).hexdigest()} for name,value in files.items()},'transformations':['Pin public links to the exact canonical commit','Preserve every historical embedded scientific object on history.html','Preserve dated N051 scientific objects on previous.html','Separate new, restored, source-only and synthetic counters','Expose selected rounded issue cards, complete provider gaps and negative aggregate results'],'private_model_bodies':'not included','licensed_raw_data':'not included'}
    (output/'provenance.json').write_text(json.dumps(provenance,indent=2)+'\n');return provenance


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--commit',required=True);p.add_argument('--output',required=True,type=pathlib.Path);a=p.parse_args();print(json.dumps(export(a.output,a.commit),indent=2))
