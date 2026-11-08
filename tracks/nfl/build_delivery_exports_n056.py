"""Write complete public formats atomically and verify every CSV record."""
import argparse,csv,hashlib,json,pathlib,tempfile,os
from build_delivery_exports_n055 import records,COLUMNS
from build_season_review_n054 import load,validate,build,pack
from actual_n055_n056 import enrich
from publication_audit_n056 import audit
def pin(path):return {'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
def export(output):
 output=pathlib.Path(output);output.mkdir(parents=True,exist_ok=True);data=enrich(validate(load()));audited=audit(data)
 with tempfile.TemporaryDirectory(prefix='nfl-n056-export-',dir=output) as td:
  tmp=pathlib.Path(td);html=tmp/'Sports_Edge_Lab_NFL_N056.html';html.write_text(build(data),encoding='utf-8');full=tmp/'Sports_Edge_Lab_NFL_N056_full.csv';counts={}
  with full.open('w',encoding='utf-8',newline='') as f:
   w=csv.DictWriter(f,fieldnames=COLUMNS);w.writeheader()
   for row in records(data):w.writerow(row);counts[row['record_type']]=counts.get(row['record_type'],0)+1
  with full.open(encoding='utf-8',newline='') as f:
   reader=csv.DictReader(f)
   for expected in records(data):
    actual=next(reader)
    if json.loads(actual['record_json'])!=json.loads(expected['record_json']):raise ValueError('CSV full-field readback mismatch')
   if next(reader,None) is not None:raise ValueError('CSV unexpected trailing records')
  ap=tmp/'Sports_Edge_Lab_NFL_N056_audit.json';ap.write_text(json.dumps(audited,indent=2));files=[html,full,ap]
  for f in files:os.replace(f,output/f.name)
 carrier=output/'enriched_n056.json.gz';carrier.write_bytes(pack(data))
 manifest={'schema':'nfl.public.delivery.n056.v1','source_projection_sha256':audited['source_projection_sha256'],'n054_recovery_projection_sha256':data['n054_recovery_projection_sha256'],'n055_actual_projection_sha256':data['n055_public_projection_sha256'],'enriched_projection':pin(carrier),'record_counts':counts,'csv_rows':sum(counts.values()),'csv_full_record_readback':'PASS','publication_new_fits':0,'publication_new_issues':0,'actual_N055_native_states':data['n055_actual_results']['new_native_fits'],'actual_N055_meta_states':data['n055_actual_results']['new_meta_fits'],'actual_N055_owner_issue_rows':len(data['n055_owner_component_issues']),'files':{f.name:pin(output/f.name) for f in files}}
 (output/'Sports_Edge_Lab_NFL_N056_export_manifest.json').write_text(json.dumps(manifest,indent=2));return manifest
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('output',type=pathlib.Path);a=p.parse_args();print(json.dumps(export(a.output),indent=2))
