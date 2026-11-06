"""Publish the failed attempt and prepared repair without redating prior science."""
import argparse,hashlib,json,pathlib,subprocess
from build_review_n051 import build,validate,retained
from export_site_n050 import projection as prior_projection
HERE=pathlib.Path(__file__).resolve().parent
ROOT=HERE.parents[1]
REPO='https://github.com/alvaromendizabal/sports-edge-lab'


def projection(current,history,readiness,commit):
    current,history=prior_projection(current,history,readiness,commit)
    history=history.replace('Later actual N049 evidence supersedes the preparation status below.','Later actual N049 and N050 evidence supersedes the preparation status below.')
    history=history.replace('Open the current N049 actual / N050 prepared review','Open the current N050 actual / N051 prepared review')
    return current,history


def export(output,commit):
    inputs=['review_n051.html','current_review_n051.json','review_n051.template.html',
            'build_review_n051.py','export_site_n051.py','export_site_n050.py','export_site_n049.py',
            'build_review_n050.py','current_review_n050.json','review.html','readiness_n049.json',
            'parent_contract.py','test_parent_contract.py','N051_RESEARCH_UPDATE.md']
    pins={}
    for name in inputs:
        path=HERE/name;raw=path.read_bytes()
        canonical=subprocess.check_output(['git','show',commit+':'+path.relative_to(ROOT).as_posix()],cwd=ROOT)
        if raw!=canonical:raise ValueError('Uncommitted publication input: '+name)
        pins[name]={'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
    review=validate(json.loads((HERE/'current_review_n051.json').read_text()));current=(HERE/'review_n051.html').read_text()
    if current!=build(review):raise ValueError('Generated review drift')
    current,history=projection(current,(HERE/'review.html').read_text(),json.loads((HERE/'readiness_n049.json').read_text()),commit)
    output.mkdir(parents=True,exist_ok=True);files={'index.html':current,'history.html':history}
    for name,value in files.items():(output/name).write_text(value)
    provenance={'role':'public_static_publication_mirror','canonical_repository':REPO,'canonical_commit':commit,
                'research_state':'N050 actual failed with zero new science; N051 prepared, not owner-executed; N049 scientific snapshot preserved',
                'evidence_as_of':retained()[1]['as_of'],'latest_owner_attempt_finished_at':review['latest_owner_attempt']['finished_at'],
                'canonical_inputs':pins,'hosted_files':{name:{'bytes':len(value.encode()),'sha256':hashlib.sha256(value.encode()).hexdigest()} for name,value in files.items()},
                'transformations':['Pin public links to the exact canonical commit','Preserve the complete historical review on history.html','Preserve the exact retained scientific object','Separate latest execution, retained evidence and next preparation','Add canonical publication provenance'],
                'private_model_bodies':'not included','licensed_raw_data':'not included'}
    (output/'provenance.json').write_text(json.dumps(provenance,indent=2)+'\n');return provenance


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--commit',required=True);p.add_argument('--output',required=True,type=pathlib.Path);a=p.parse_args();print(json.dumps(export(a.output,a.commit),indent=2))
