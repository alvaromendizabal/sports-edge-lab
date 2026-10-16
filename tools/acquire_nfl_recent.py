"""Refresh current-season NFL public PBP and audit coverage against schedules."""
import argparse
import csv
import datetime as dt
import gzip
import hashlib
import io
import json
from pathlib import Path
import threading
import time
import unittest
import urllib.parse
import urllib.request
import uuid
import zipfile

BUCKET='sagemaker-sports-edge-lab-560403859723-us-west-2'
API='https://api.github.com/repos/nflverse/nflverse-data'
SCHEDULE='https://raw.githubusercontent.com/nflverse/nfldata/master/data/games.csv'


def stamp():return dt.datetime.now(dt.timezone.utc).isoformat()
def packed(x):return json.dumps(x,sort_keys=True,default=str).encode()
def emit(event,**kw):print(packed(dict(at=stamp(),event=event,**kw)).decode(),flush=True)


def choose(assets,year):
    names=['play_by_play_'+str(year)+'.csv.gz','play_by_play_'+str(year)+'.csv']
    candidates={a['name']:a for a in assets if a.get('name') in names}
    for n in names:
        if n in candidates:
            a=candidates[n]
            if not a['browser_download_url'].startswith('https://github.com/nflverse/nflverse-data/releases/download/pbp/'):
                raise ValueError('Unexpected release asset URL')
            return a
    raise ValueError('Current NFL season PBP asset not published')


def rows(data,name):
    if name.endswith('.gz'):data=gzip.decompress(data)
    if len(data)>200*1024**2:raise ValueError('Decoded CSV bound exceeded')
    return list(csv.DictReader(io.StringIO(data.decode('utf-8-sig'))))


def audit(pbp,schedule,year,today):
    counts={}
    dates=set();weeks=set();missing=0
    for r in pbp:
        if not r.get('game_id'):missing+=1;continue
        counts[r['game_id']]=counts.get(r['game_id'],0)+1
        if r.get('game_date'):dates.add(r['game_date'])
        if r.get('week'):weeks.add(r['week'])
    current=[g for g in schedule if g.get('season')==str(year)]
    expected={g['game_id']:g for g in current if g.get('result') not in ('','NA','NaN',None) and g.get('gameday','9999')<=today}
    missing_games=sorted(set(expected)-set(counts))
    return {'pbp_rows':len(pbp),'pbp_distinct_games':len(counts),'pbp_rows_missing_game_id':missing,
        'latest_pbp_game_date':max(dates) if dates else None,'earliest_pbp_game_date':min(dates) if dates else None,
        'weeks':sorted(weeks,key=int),'scheduled_current_season_games':len(current),
        'completed_schedule_games':len(expected),'completed_games_missing_pbp':missing_games,
        'unmatched_pbp_game_ids':sorted(set(counts)-{g['game_id'] for g in current}),
        'latest_completed_schedule_game_date':max((g['gameday'] for g in expected.values()),default=None),
        'all_completed_schedule_games_have_pbp':not missing_games,'row_completeness_verified':False,
        'point_in_time_approved':False}


class Tests(unittest.TestCase):
    def test_asset_is_observed_and_current(self):
        a={'name':'play_by_play_2026.csv.gz','browser_download_url':'https://github.com/nflverse/nflverse-data/releases/download/pbp/a'}
        self.assertEqual(choose([a],2026),a)
        with self.assertRaises(ValueError):choose([a],2025)
        with self.assertRaises(ValueError):choose([dict(a,browser_download_url='https://example.com/a')],2026)
    def test_schedule_missing_not_row_count(self):
        games=[{'season':'2026','game_id':'a','gameday':'2026-10-15','result':'3'},{'season':'2026','game_id':'b','gameday':'2026-10-15','result':'0'},{'season':'2026','game_id':'c','gameday':'2026-10-17','result':''}]
        r=audit([{'game_id':'a','game_date':'2026-10-15','week':'6'}]*2,games,2026,'2026-10-16')
        self.assertEqual(r['completed_games_missing_pbp'],['b']);self.assertEqual(r['completed_schedule_games'],2)
        self.assertFalse(r['row_completeness_verified'])
    def test_compressed_csv(self):
        self.assertEqual(rows(gzip.compress(b'a,b\n1,2\n'),'a.csv.gz'),[{'a':'1','b':'2'}])


def main():
    p=argparse.ArgumentParser();p.add_argument('--self-test',action='store_true');a=p.parse_args()
    r=unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
    if not r.wasSuccessful():return 1
    emit('SELF_TEST_PASS',tests=r.testsRun)
    if a.self_test:return 0
    import boto3
    from botocore.config import Config
    s3=boto3.client('s3',region_name='us-west-2',config=Config(retries={'max_attempts':4,'mode':'adaptive'},connect_timeout=10,read_timeout=60))
    started=time.monotonic();run=dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:10]
    report={'run_id':run,'version':'v035','started_at':stamp(),'status':'running','requests':0,'downloaded_bytes':0,'receipts':[],
        'bounds':{'max_source_requests':8,'max_transfer_bytes':150*1024**2,'max_seconds':360},
        'scope':'Current NFL season public PBP and schedule, immutable source observations'}
    prefix='shared/acquisition/nfl-recent/'+run+'/'
    def put(key,data,kind='application/json'):
        s3.put_object(Bucket=BUCKET,Key=key,Body=data,ContentType=kind,ServerSideEncryption='AES256')
    stop=threading.Event()
    def heartbeat():
        while not stop.wait(30):emit('HEARTBEAT',run_id=run,requests=report['requests'],downloaded_bytes=report['downloaded_bytes'],elapsed=time.monotonic()-started)
    threading.Thread(target=heartbeat,daemon=True).start()
    def fetch(url,cap):
        if report['requests']>=8 or time.monotonic()-started>=360:raise RuntimeError('Execution budget reached')
        host=urllib.parse.urlsplit(url).hostname
        if host not in ('api.github.com','github.com','raw.githubusercontent.com'):raise ValueError('Unapproved source')
        report['requests']+=1
        with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'SportsEdgeLab/1.0 research archive'}),timeout=45) as response:
            data=response.read(min(cap,150*1024**2-report['downloaded_bytes'])+1)
            headers={k:response.headers.get(k) for k in ('Last-Modified','ETag','Content-Type')}
        report['downloaded_bytes']+=len(data)
        if len(data)>cap or report['downloaded_bytes']>150*1024**2:raise ValueError('Transfer bound exceeded')
        return data,headers
    def archive(data,name,provider,family,source,metadata):
        sha=hashlib.sha256(data).hexdigest();key='tracks/nfl/raw/'+provider+'/'+family+'/'+sha+'/'+name
        put(key,data,'application/octet-stream')
        receipt=dict(metadata,raw_key=key,source_url=source,sha256=sha,bytes=len(data),retrieved_at=stamp(),point_in_time_approved=False)
        put(key+'.receipt.json',packed(receipt));report['receipts'].append(receipt)
    try:
        year=dt.datetime.now(dt.timezone.utc).year
        release=json.loads(fetch(API+'/releases/tags/pbp',4*1024**2)[0]);assets=[]
        for page in range(1,5):
            batch=json.loads(fetch(API+'/releases/'+str(release['id'])+'/assets?per_page=100&page='+str(page),4*1024**2)[0]);assets.extend(batch)
            if len(batch)<100:break
        else:raise ValueError('Release asset pagination incomplete')
        asset=choose(assets,year);data,headers=fetch(asset['browser_download_url'],100*1024**2)
        if len(data)!=asset['size']:raise ValueError('Asset size mismatch')
        digest=asset.get('digest')
        if digest and digest!='sha256:'+hashlib.sha256(data).hexdigest():raise ValueError('Asset digest mismatch')
        pbp=rows(data,asset['name'])
        if not pbp or not {'game_id','game_date','week'}<=set(pbp[0]):raise ValueError('PBP schema unavailable')
        archive(data,asset['name'],'nflverse','pbp',asset['browser_download_url'],{'source_updated_at':asset['updated_at'],'source_asset_id':asset['id'],'http_headers':headers,'lineage':'nflverse community statistical compilation'})
        data,headers=fetch(SCHEDULE,10*1024**2);schedule=rows(data,'games.csv')
        if not schedule or not {'game_id','season','result','gameday'}<=set(schedule[0]):raise ValueError('Schedule schema unavailable')
        archive(data,'games.csv','nfldata','games',SCHEDULE,{'http_headers':headers,'lineage':'nflverse nfldata community schedule'})
        report['coverage']=audit(pbp,schedule,year,dt.datetime.now(dt.timezone.utc).date().isoformat())
        report['status']='completed'
    except Exception as exc:
        report.update(status='failed',error_type=type(exc).__name__,error=str(exc)[:300])
    finally:
        stop.set();report.update(finished_at=stamp(),elapsed_seconds=round(time.monotonic()-started,2))
        report['estimated_application_compute_usd']=round(report['elapsed_seconds']/3600*.461,4)
        report['cost_excludes']='Provisioning, shutdown, S3 storage and requests'
        put(prefix+'report.json',packed(report))
        out=Path('/opt/ml/processing/output');out.mkdir(parents=True,exist_ok=True)
        z=out/('sports_edge_lab_nfl_recent_return_'+run+'.zip')
        with zipfile.ZipFile(z,'w',zipfile.ZIP_DEFLATED) as f:f.writestr('report.json',packed(report))
        put(prefix+z.name,z.read_bytes(),'application/zip')
        emit('FINISHED',run_id=run,status=report['status'],coverage=report.get('coverage'),report_key=prefix+'report.json')
    return 0 if report['status']=='completed' else 1


if __name__=='__main__':raise SystemExit(main())
