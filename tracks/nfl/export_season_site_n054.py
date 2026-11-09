"""Export only the exact tested bounded NFL public projection to the existing Site."""
import argparse,hashlib,json,pathlib,re,subprocess
from urllib.parse import urlsplit,unquote
from build_season_review_n054 import build,load
HERE=pathlib.Path(__file__).resolve().parent;ROOT=HERE.parents[1]
REPO='https://github.com/alvaromendizabal/sports-edge-lab'
def projection(current,commit):
 if not re.fullmatch('[0-9a-f]{40}',commit):raise ValueError('Exact canonical commit required')
 def link(m):
  target=m.group(1);u=urlsplit(target)
  if u.scheme or u.netloc or target.startswith('#'):return m.group(0)
  p=(HERE/unquote(u.path)).resolve()
  if not p.is_relative_to(ROOT) or not p.is_file():raise ValueError('Unresolved bounded public link')
  rel=p.relative_to(ROOT).as_posix();prefix='https://raw.githubusercontent.com/alvaromendizabal/sports-edge-lab/' if p.name.endswith(('.json','.json.gz')) else REPO+'/blob/'
  return 'href="'+prefix+commit+'/'+rel+'"'
 parts=re.split(r'(<script\b[^>]*>.*?</script\s*>)',current,flags=re.I|re.S)
 current=''.join(s if i%2 else re.sub(r'href="([^"]+)"',link,s) for i,s in enumerate(parts))
 return current.replace('Canonical source and dated reports are preserved in the NFL repository.','Canonical commit: <a href="'+REPO+'/commit/'+commit+'">'+commit+'</a>. <a href="provenance.json">Publication provenance</a>.')
def validate_output_directory(output):
 if output.exists():
  for item in output.iterdir():
   if item.name not in {'index.html','provenance.json'} or not item.is_file() or item.is_symlink():raise ValueError('Unexpected hosted output; bounded Site must contain only index and provenance')
def export(output,commit):
 validate_output_directory(output)
 names=['public_projection_n059.json.gz','public_projection_n060.json.gz','public_projection_n061.json.gz','n061_public_contract.py','test_public_n061.py','N061_REVIEW.md','v5_public_contract.py','test_v5_public_n060.py','V5_COMPARISON_N060.md','season_review_n054.html','season_review_n054.template.html','build_season_review_n054.py','export_season_site_n054.py','test_public_season_n059.py','browser_season_n054.cjs','browser_test.cjs','README.md','CURRENT_MODEL_CARD.md','CURRENT_METHODOLOGY.md','PUBLIC_BOUNDARY_N059.md'];pins={}
 for name in names:
  p=HERE/name;b=p.read_bytes();canonical=subprocess.check_output(['git','show',commit+':'+p.relative_to(ROOT).as_posix()],cwd=ROOT)
  if b!=canonical:raise ValueError('Uncommitted publication input '+name)
  pins[name]={'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
 data=load();current=(HERE/'season_review_n054.html').read_text()
 if current!=build(data):raise ValueError('Public page drift')
 body=projection(current,commit);output.mkdir(parents=True,exist_ok=True);(output/'index.html').write_text(body)
 provenance={'schema':'nfl.public.n061.site-provenance.v1','role':'bounded_public_static_snapshot','canonical_repository':REPO,'canonical_commit':commit,'canonical_inputs':pins,'hosted_files':{'index.html':{'bytes':len(body.encode()),'sha256':hashlib.sha256(body.encode()).hexdigest()}},'evidence_as_of':data['observed_at'],'schedule_snapshot':data['snapshot'],'evidence_counts':data['counts'],'public_boundary':data['public_scope'],'actual_latest_owner_status':data['n061_owner_status']['status'],'actual_latest_owner_cycle':'N060','latest_scientific_cycle':'N060','v5_prepared_status':data['v5_scope']['status'],'v5_new_owner_fits':0,'v5_new_owner_issues':0,'next_owner_cycle':'N061','next_owner_execution_status':'PREPARED_NOT_OWNER_EXECUTED','original_complete_private_carriers_preserved':True,'git_history_rewritten':False,'source_only_predictive_credit':0,'new_publication_fits':0,'new_publication_issues':0,'automatic_promotion':False}
 (output/'provenance.json').write_text(json.dumps(provenance,indent=2)+'\n');return provenance
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--commit',required=True);p.add_argument('--output',required=True,type=pathlib.Path);a=p.parse_args();print(json.dumps(export(a.output,a.commit),indent=2))
