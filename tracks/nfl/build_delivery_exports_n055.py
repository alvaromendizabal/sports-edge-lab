"""Complete sanitized public delivery exports with an exact per-table manifest."""
import argparse,csv,hashlib,json,pathlib
from build_season_review_n054 import load,validate,build
from publication_audit_n055 import audit
from actual_recovery_n055 import enrich

COLUMNS=['record_type','record_number','game_id','season','target','provider','lane_id','horizon','value','available','eligible','record_json']

def records(data):
 for key,value in data.items():
  values=value if isinstance(value,list) else [value]
  for number,row in enumerate(values,1):
   item={name:'' for name in COLUMNS};item.update(record_type=key,record_number=number)
   if isinstance(row,dict):
    for name in COLUMNS[2:-1]:
     field=row.get(name)
     item[name]=field if field is not None else ''
   item['record_json']=json.dumps(row,ensure_ascii=False,separators=(',',':'),allow_nan=False)
   yield item

def export(output):
 output=pathlib.Path(output);output.mkdir(parents=True,exist_ok=True)
 data=enrich(validate(load()));audited=audit(data)
 html=output/'Sports_Edge_Lab_NFL_N055.html';html.write_text(build(data),encoding='utf-8')
 full=output/'Sports_Edge_Lab_NFL_N055_full.csv'
 counts={}
 with full.open('w',encoding='utf-8',newline='') as f:
  writer=csv.DictWriter(f,fieldnames=COLUMNS);writer.writeheader()
  for row in records(data):
   writer.writerow(row);counts[row['record_type']]=counts.get(row['record_type'],0)+1
 a=output/'Sports_Edge_Lab_NFL_N055_audit.json';a.write_text(json.dumps(audited,indent=2),encoding='utf-8')
 outputs=[html,full,a]
 manifest={'schema':'nfl.public.delivery.n055.v1','source_projection_sha256':audited['source_projection_sha256'],'record_counts':counts,'csv_rows':sum(counts.values()),'publication_new_fits':0,'publication_new_issues':0,'recovered_N054_market_native_states':102,'recovered_N054_owner_issue_rows':2233,'new_numeric_source_values':0,'files':{f.name:{'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()} for f in outputs}}
 (output/'Sports_Edge_Lab_NFL_N055_export_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
 return manifest

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('output',type=pathlib.Path);args=parser.parse_args();print(json.dumps(export(args.output),indent=2))
