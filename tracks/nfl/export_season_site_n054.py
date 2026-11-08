"""Publish only the exact tested NFL commit and preserve every dated archive."""
import argparse,hashlib,json,pathlib,re,subprocess
from urllib.parse import urlsplit,unquote
from build_season_review_n054 import build,validate,load
from export_season_site_n053r1 import projection as previous_season_projection,archive_previous
HERE=pathlib.Path(__file__).resolve().parent;ROOT=HERE.parents[1]
REPO='https://github.com/alvaromendizabal/sports-edge-lab'

def projection(current,commit):
 if not re.fullmatch('[0-9a-f]{40}',commit):raise ValueError('Exact canonical commit required')
 def link(m):
  target=m.group(1);parsed=urlsplit(target)
  if parsed.scheme or parsed.netloc or target.startswith('#'):return m.group(0)
  maps={'review.html':'history.html','review_n053.html':'previous.html','season_review_n053r1.html':'prepared-archive.html'}
  if parsed.path in maps:return 'href="'+maps[parsed.path]+('#'+parsed.fragment if parsed.fragment else '')+'"'
  path=(HERE/unquote(parsed.path)).resolve()
  if not path.is_relative_to(ROOT) or not path.is_file():raise ValueError('Unresolved public link: '+target)
  relative=path.relative_to(ROOT).as_posix();prefix=('https://raw.githubusercontent.com/alvaromendizabal/sports-edge-lab/' if path.suffix in ['.csv','.json'] else REPO+'/blob/')
  return 'href="'+prefix+commit+'/'+relative+('#'+parsed.fragment if parsed.fragment else '')+'"'
 sections=re.split(r'(<script\b[^>]*>.*?</script\s*>)',current,flags=re.I|re.S)
 current=''.join(part if index%2 else re.sub(r'href="([^"]+)"',link,part) for index,part in enumerate(sections))
 return current.replace('Canonical source and dated reports are preserved in the NFL repository.','Canonical commit: <a href="'+REPO+'/commit/'+commit+'">'+commit+'</a>. <a href="provenance.json">Publication provenance</a>.')

def export(output,commit):
 inputs=['actual_n056_n057.py','n056_actual_results_n057.json.gz','publication_audit_n057.py','build_delivery_exports_n057.py','test_actual_n056_n057.py','ACTUAL_N056_RESULTS_N057.md','actual_n055_n056.py','n055_actual_results_n056.json.gz','publication_audit_n056.py','build_delivery_exports_n056.py','test_actual_n055_n056.py','ACTUAL_N055_RESULTS_N056.md','season_review_n054.html','current_season_n054.json.gz','season_review_n054.template.html','build_season_review_n054.py','export_season_site_n054.py','test_season_review_n054.py','browser_season_n054.cjs','browser_test.cjs','README.md','SEASON_REVIEW_N054.md','publication_audit_n055.py','PUBLICATION_AUDIT_N055.md','actual_recovery_n055.py','n054_actual_recovery_n055.json.gz','test_actual_recovery_n055.py','ACTUAL_N054_RECOVERY_N055.md','build_delivery_exports_n055.py','test_publication_audit_n055.py','season_review_n053r1.html','current_season_n053r1.json.gz','export_season_site_n053r1.py','review_n053.html','current_review_n053.json','export_site_n053.py','export_site_n050.py','export_site_n049.py','review.html','readiness_n049.json']
 pins={}
 for name in inputs:
  path=HERE/name;raw=path.read_bytes();canonical=subprocess.check_output(['git','show',commit+':'+path.relative_to(ROOT).as_posix()],cwd=ROOT)
  if raw!=canonical:raise ValueError('Uncommitted publication input: '+name)
  pins[name]={'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
 from actual_n056_n057 import enrich
 data=enrich(validate(load()));current=(HERE/'season_review_n054.html').read_text()
 if current!=build(data):raise ValueError('Generated season review drift')
 current=projection(current,commit)
 prepared=previous_season_projection((HERE/'season_review_n053r1.html').read_text(),commit)
 previous,history=archive_previous((HERE/'review_n053.html').read_text(),(HERE/'review.html').read_text(),json.loads((HERE/'readiness_n049.json').read_text()),commit)
 banner='<aside aria-label="Historical snapshot" style="padding:18px;background:#fff1d8;color:#39260b;text-align:center"><strong>Dated archive. Actual N056 and retained earlier science are in the current view.</strong> <a href="index.html" style="color:#175442">Open all 272 games and actual N056 evidence →</a></aside>'
 files={'index.html':current,'prepared-archive.html':prepared,'previous.html':previous,'history.html':history}
 for name in ['prepared-archive.html','previous.html','history.html']:files[name]=re.sub(r'(<body[^>]*>)',lambda m:m.group(1)+banner,files[name],count=1)
 output.mkdir(parents=True,exist_ok=True)
 for name,value in files.items():(output/name).write_text(value)
 provenance={'role':'public_static_publication_mirror','canonical_repository':REPO,'canonical_commit':commit,'research_state':'Actual partial N056: 21 native states (7 current origin and 14 retrospective), 0 new meta fits, 21 optimizer starts/returns/durable commits, 2,683 owner issue rows, 450 frozen-selected future targets and 6 separate retrospective rows. Final census failed on postseason WC token. Owner 122-final snapshot retained; dated official CIN 34–ATL 17 append gives 123 finals. All prior N055/N054 studies and negative results preserved; N057 prepared, no automatic promotion.','evidence_as_of':data['as_of'],'canonical_inputs':pins,'hosted_files':{name:{'bytes':len(value.encode()),'sha256':hashlib.sha256(value.encode()).hexdigest()} for name,value in files.items()},'transformations':['Complete272-game schedule with display-only routing to existing frozen-selected roles','Dated official result append preserves the owner schedule snapshot','Distinct actual owner jobs,states,reuse,issue and source counts','Equal provider event inventory with explicit dated horizons','Full raw,scale and model metric exports','Exact canonical source links','Earlier pages retained as dated archives','Original raw/source/model/issue evidence unchanged'],'retained_N053R1_native_states':3432,'retained_N053R1_scale_states':70,'retained_N053R1_owner_issue_rows':754,'actual_N055_native_states':1378,'actual_N055_meta_states':45,'actual_N055_owner_issue_rows':168,'actual_N055_new_family_future_issues':0,'actual_N056_native_states':21,'actual_N056_meta_states':0,'actual_N056_owner_issue_rows':2683,'actual_N056_family_future_issue_rows':450,'actual_N056_retrospective_rows':6,'owner_schedule_snapshot':data['owner_n056_schedule_snapshot'],'display_schedule_snapshot':data['display_schedule_snapshot'],'n055_overlay_sha256':pins['n055_actual_results_n056.json.gz']['sha256'],'n056_overlay_sha256':pins['n056_actual_results_n057.json.gz']['sha256'],'active_status_revision':1,'next_owner_cycle':'N057','next_owner_execution_status':'PREPARED_NOT_OWNER_EXECUTED','unresolved_N054_family_starts':3,'completed_N054_family_fit_credit':0,'new_audit_fits':0,'new_audit_issues':0,'recovered_N054_market_native_states':102,'recovered_N054_owner_issue_rows':2233,'private_model_bodies':'not included','licensed_raw_data':'not included'}
 (output/'provenance.json').write_text(json.dumps(provenance,indent=2)+'\n');return provenance
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--commit',required=True);p.add_argument('--output',required=True,type=pathlib.Path);a=p.parse_args();print(json.dumps(export(a.output,a.commit),indent=2))
