"""Finite public football refresh, availability recovery and identity audits."""
import argparse, collections, concurrent.futures, csv, datetime as dt, gzip, hashlib
import io, json, re, sys, threading, time, unittest, urllib.error, urllib.request, uuid, zipfile
from pathlib import Path
from unittest import mock
import ngs_avail

BUCKET='sagemaker-sports-edge-lab-560403859723-us-west-2'
OUTPUT='/opt/ml/processing/output'
VERSION='sports-edge-lab-football-refresh-v041'
FAMILIES={'snap_counts':'snap_counts_2026.csv.gz','weekly_rosters':'roster_weekly_2026.csv.gz','depth_charts':'depth_charts_2026.csv.gz'}
NULLS={'','NA','NaN','null','None'}

def stamp():return dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds').replace('+00:00','Z')
def pack(x):return json.dumps(x,sort_keys=True,separators=(',',':'),default=str).encode()
def sha(x):return hashlib.sha256(x).hexdigest()
def emit(event,**kw):print(pack(dict(event=event,timestamp=stamp(),**kw)).decode(),flush=True)
def embedded(name):
    with zipfile.ZipFile(sys.argv[0]) as z:return json.loads(z.read(name))
def instant(x):
    v=dt.datetime.fromisoformat(x.replace('Z','+00:00'))
    if v.tzinfo is None:raise ValueError('timestamp_timezone_missing')
    return v.astimezone(dt.timezone.utc)
def valid_asset(a):
    if a.get('family') not in FAMILIES or a.get('name')!=FAMILIES[a['family']]:raise ValueError('asset_scope')
    if a['url']!='https://github.com/nflverse/nflverse-data/releases/download/'+a['family']+'/'+a['name']:raise ValueError('asset_url')
    if not re.fullmatch(r'sha256:[0-9a-f]{64}',a.get('digest','')) or not 0<a['size']<=20*1024**2:raise ValueError('asset_metadata')
def csv_rows(raw):
    with gzip.GzipFile(fileobj=io.BytesIO(raw)) as f:decoded=f.read(100*1024**2+1)
    if len(decoded)>100*1024**2:raise ValueError('decoded_csv_bound')
    reader=csv.DictReader(io.StringIO(decoded.decode('utf-8-sig')));rows=list(reader)
    if not rows or any(None in r for r in rows):raise ValueError('empty_or_ragged_csv')
    return rows
def require(rows,fields):
    if not rows or not set(fields)<=set(rows[0]):raise ValueError('schema_changed:'+','.join(fields))
def audit(family,rows,observed_at):
    if family=='depth_charts':
        require(rows,['dt','team','player_name','gsis_id','pos_slot','pos_rank'])
        latest={};times=[]
        for x in rows:
            t=instant(x['dt'])
            if t>instant(observed_at) or t.year!=2026:raise ValueError('depth_timestamp_scope')
            if not x['team']:raise ValueError('depth_team_missing')
            latest[x['team']]=max(t,latest.get(x['team'],t));times.append(t)
        selected=[x for x in rows if instant(x['dt'])==latest[x['team']]]
        identities=collections.Counter((x['dt'],x['team'],x['gsis_id'],x.get('pos_grp_id'),x.get('pos_id'),x['pos_slot'],x['pos_rank']) for x in rows)
        return dict(rows=len(rows),teams=len(latest),earliest_snapshot=min(times).isoformat(),latest_snapshot=max(times).isoformat(),latest_snapshot_rows=len(selected),latest_snapshot_missing_gsis=sum(x['gsis_id'] in NULLS for x in selected),duplicate_identity_rows=sum(n-1 for n in identities.values() if n>1),source_snapshot_not_original_publication_time=True,historical_point_in_time_approved=False),selected
    required=['season','week','team','game_type']+(['game_id','pfr_player_id','offense_snaps','defense_snaps','st_snaps'] if family=='snap_counts' else ['gsis_id','pfr_id','full_name'])
    require(rows,required)
    if any(x['season']!='2026' or not 0<=int(x['week'])<=23 for x in rows):raise ValueError('season_week_scope')
    regular=[x for x in rows if x['game_type']=='REG'];weeks=collections.Counter(int(x['week']) for x in regular)
    if not regular:raise ValueError('no_regular_season_records')
    latest=max(weeks,default=None);selected=[x for x in regular if int(x['week'])==latest]
    result=dict(rows=len(rows),regular_rows=len(regular),regular_week_counts=dict(sorted(weeks.items())),latest_regular_week=latest,latest_regular_week_rows=len(selected),teams=len({x['team'] for x in regular}),historical_point_in_time_approved=False)
    if family=='snap_counts':
        if any(float(x[k])<0 for x in rows for k in ('offense_snaps','defense_snaps','st_snaps')):raise ValueError('negative_snaps')
        ids=collections.Counter((x['game_id'],x['team'],x['pfr_player_id']) for x in rows)
        result.update(regular_games=len({x['game_id'] for x in regular}),missing_player_ids=sum(x['pfr_player_id'] in NULLS for x in rows),duplicate_identity_rows=sum(n-1 for n in ids.values() if n>1),all_completed_games_verified=False)
    else:
        ids=collections.Counter((x['season'],x['week'],x['game_type'],x['team'],x['gsis_id']) for x in rows)
        result.update(missing_gsis_ids=sum(x['gsis_id'] in NULLS for x in rows),duplicate_identity_rows=sum(n-1 for n in ids.values() if n>1))
    return result,selected
def acc_rows(text,evidence):
    if evidence.get('headers')!=ngs_avail.HEAD or not evidence.get('browser_run_url','').startswith('https://agent.tinyfish.ai/runs/'):raise ValueError('unverified_headers')
    lines=[x for x in text.splitlines() if x.startswith('|')]
    if len(lines)<3:raise ValueError('no_table')
    old=[x.strip() for x in lines[0].strip('|').split('|')]
    if old not in (ngs_avail.HEAD,['']*9):raise ValueError('unexpected_extracted_headers')
    lines[0]='| '+' | '.join(evidence['headers'])+' |'
    return ngs_avail.availability_rows('\n'.join(lines))
def sec_rows(seed):
    if seed['headers']!=ngs_avail.HEAD or seed['row_count']!=len(seed['rows']):raise ValueError('sec_schema_or_count')
    if any(len(row)!=9 or any('|' in x or '\n' in x for x in row) for row in seed['rows']):raise ValueError('sec_row_shape')
    text='| '+' | '.join(seed['headers'])+' |\n| '+' | '.join(['---']*9)+' |\n'
    text+='\n'.join('| '+' | '.join(row)+' |' for row in seed['rows'])
    return ngs_avail.availability_rows(text)
def availability_summary(rows,bad):
    current=[r for r in rows if '2026-10-16'<=r['game_date']<='2026-10-18']
    ids=collections.Counter((r['team'],r['game_date'],r['opponent'],r['jersey'],r['player_name']) for r in rows)
    return dict(rows=len(rows),rejected_rows=len(bad),teams=len({r['team'] for r in rows}),team_games=len({(r['team'],r['game_date'],r['opponent']) for r in rows}),current_weekend_rows=len(current),current_weekend_team_games=len({(r['team'],r['game_date'],r['opponent']) for r in current}),first_game_date=min((r['game_date'] for r in rows),default=None),last_game_date=max((r['game_date'] for r in rows),default=None),duplicate_identity_rows=sum(n-1 for n in ids.values() if n>1),historical_point_in_time_approved=False,player_identity_join_validated=False)
def roster_indexes(rows):
    gsis=collections.defaultdict(set);pfr=collections.defaultdict(set)
    for r in rows:
        if r['game_type']!='REG' or r['gsis_id'] in NULLS:continue
        k=(r['season'],r['week'],r['team']);gsis[k].add(r['gsis_id'])
        if r['pfr_id'] not in NULLS:pfr[k+(r['pfr_id'],)].add(r['gsis_id'])
    return gsis,pfr
def join_ngs(rows,rosters):
    gsis,_=roster_indexes(rosters);result=[];c=collections.Counter()
    for x in rows:
        if x['season']!='2026' or x['season_type']!='REG' or int(x['week'])<=0:continue
        k=(x['season'],x['week'],x['team_abbr']);matched=x['player_gsis_id'] not in NULLS and x['player_gsis_id'] in gsis[k]
        status='matched_exact_week_team_gsis' if matched else 'unmatched';c[status]+=1
        result.append(dict(x,roster_join_status=status,historical_point_in_time_approved=False))
    return result,dict(c)
def join_snaps(rows,rosters):
    _,pfr=roster_indexes(rosters);out=[];counts=collections.Counter()
    for x in rows:
        if x['game_type']!='REG':continue
        candidates=pfr[(x['season'],x['week'],x['team'],x['pfr_player_id'])] if x['pfr_player_id'] not in NULLS else set()
        status='matched_exact_week_team_pfr' if len(candidates)==1 else 'ambiguous' if len(candidates)>1 else 'unmatched'
        counts[status]+=1;out.append(dict(x,gsis_id=next(iter(candidates)) if len(candidates)==1 else None,roster_join_status=status,historical_point_in_time_approved=False))
    return out,dict(counts)

class Store:
    def __init__(self):
        import boto3
        from botocore.config import Config
        self.s3=boto3.client('s3',region_name='us-west-2',config=Config(retries={'total_max_attempts':3,'mode':'standard'},connect_timeout=10,read_timeout=60,max_pool_connections=8))
    def get(self,key):
        try:r=self.s3.get_object(Bucket=BUCKET,Key=key)
        except self.s3.exceptions.NoSuchKey:return None
        with r['Body'] as body:return body.read()
    def put(self,key,data,kind='application/json'):
        self.s3.put_object(Bucket=BUCKET,Key=key,Body=data,ContentType=kind,ServerSideEncryption='AES256')

class Fetch:
    def __init__(self):self.lock=threading.Lock();self.last=-1e12;self.calls=0;self.bytes=0;self.blocked=False;self.opener=urllib.request.build_opener(ngs_avail.Redirect)
    def get(self,a):
        valid_asset(a)
        with self.lock:
            if self.blocked:raise RuntimeError('source_suspended')
            if self.calls>=3:raise ValueError('finite_queue_exceeded')
            pause=max(0,self.last+.5-time.monotonic())
            if pause:time.sleep(pause)
            self.last=time.monotonic();self.calls+=1
        try:
            with self.opener.open(urllib.request.Request(a['url'],headers={'User-Agent':'SportsEdgeLabResearch/1.4 (+https://github.com/alvaromendizabal/sports-edge-lab)'}),timeout=60) as r:
                raw=r.read(a['size']+1);headers={k:r.headers.get(k) for k in ('ETag','Last-Modified','Date')}
            with self.lock:self.bytes+=len(raw)
            if len(raw)!=a['size'] or 'sha256:'+sha(raw)!=a['digest']:raise ValueError('asset_integrity')
            return raw,headers
        except urllib.error.HTTPError as e:
            with self.lock:
                if e.code in (401,402,403,429):self.blocked=True
            code=e.code;e.close();raise RuntimeError('source_http_'+str(code))
def required_raw(store,key,digest):
    raw=store.get(key)
    if raw is None or sha(raw)!=digest:raise ValueError('required_cache_missing_or_corrupt:'+key)
    return raw
def run():
    config=embedded('config.json');sec=embedded('sec_seed.json')
    for a in config['assets']:valid_asset(a)
    if {a['family'] for a in config['assets']}!=set(FAMILIES) or len(config['assets'])!=3:raise ValueError('asset_plan_scope')
    if config['paid_provider_requests']!=0:raise ValueError('paid_scope_forbidden')
    started=time.monotonic();run_id=dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:10]
    store=Store();fetch=Fetch();stop=threading.Event();lock=threading.Lock();cache={}
    prefix='shared/acquisition/football-refresh/'+run_id+'/'
    report=dict(version=VERSION,run_id=run_id,status='running',started_at=stamp(),planned=9,processed=0,results=[],failures=[],subscription_credits=0,paid_provider_requests=0,application_runtime_limit_seconds=None)
    def progress():
        with lock:r=json.loads(pack(report))
        r.update(timestamp=stamp(),remaining=r['planned']-r['processed'],elapsed_seconds=round(time.monotonic()-started,2),source_requests=fetch.calls,estimated_application_compute_usd=round((time.monotonic()-started)*.461/3600,6))
        store.put(prefix+'progress.json',pack(r));return r
    def heartbeat():
        while not stop.wait(20):
            r=progress();emit('HEARTBEAT',processed=r['processed'],remaining=r['remaining'],elapsed_seconds=r['elapsed_seconds'],estimated_compute_usd=r['estimated_application_compute_usd'])
    def record(r):
        with lock:report['results'].append(r);report['processed']+=1
        emit('CAPTURE',kind=r['kind'],status=r['status'],rows=r.get('coverage',{}).get('rows'))
    def guarded(name,fn,*args):
        try:fn(*args)
        except Exception as e:
            with lock:report['processed']+=1;report['failures'].append(dict(task=name,type=type(e).__name__,reason=str(e)[:300]))
            emit('TASK_FAILED',task=name,type=type(e).__name__,reason=str(e)[:300])
    def derived(kind,rows):
        key='tracks/'+('ncaaf' if kind in ('acc-availability','sec-availability') else 'nfl')+'/derived/'+kind+'/'+run_id+'/rows.jsonl.gz'
        store.put(key,gzip.compress(b'\n'.join(pack(r) for r in rows)+b'\n',mtime=0),'application/gzip');return key
    def asset(a):
        key='tracks/nfl/raw/nflverse/'+a['family']+'/'+a['digest'].split(':')[1]+'/'+a['name'];raw=store.get(key);headers={};status='reused_verified'
        if raw is None:raw,headers=fetch.get(a);status='downloaded'
        if len(raw)!=a['size'] or 'sha256:'+sha(raw)!=a['digest']:raise ValueError('cache_integrity')
        if status=='downloaded':store.put(key,raw,'application/gzip')
        store.put(prefix+a['name']+'.receipt.json',pack(dict(raw_key=key,sha256=sha(raw),bytes=len(raw),source_url=a['url'],source_updated_at=a['source_updated_at'],captured_at=stamp(),status=status)))
        rows=csv_rows(raw);coverage,current=audit(a['family'],rows,stamp())
        current_key=derived(a['family']+'-current',[dict(x,captured_at=stamp(),source_raw_key=key,historical_point_in_time_approved=False) for x in current])
        with lock:cache[a['family']]=rows
        record(dict(kind=a['family'],status=status,raw_key=key,sha256=sha(raw),bytes=len(raw),coverage=coverage,current_rows_key=current_key,source_url=a['url'],source_updated_at=a['source_updated_at'],captured_at=stamp(),headers=headers,lineage='nflverse community compilation'))
    def acc():
        c=config['acc'];gz=store.get(c['raw_key'])
        if gz is None:raise ValueError('missing_acc_cache')
        raw=gzip.decompress(gz)
        if sha(raw)!=c['sha256']:raise ValueError('acc_cache_integrity')
        rows,bad=acc_rows(raw.decode(),c['header_evidence'])
        k=derived('acc-availability',[dict(x,observed_at=c['observed_at'],raw_key=c['raw_key'],source_url=c['source_url']) for x in rows])
        record(dict(kind='acc_availability',status='parsed_existing_capture',raw_key=c['raw_key'],derived_key=k,coverage=availability_summary(rows,bad),rejected=bad,header_evidence=c['header_evidence'],source_publication_time=None))
    def sec_capture():
        raw=pack(sec);key='tracks/ncaaf/raw/sec-availability-rendered/objects/'+sha(raw)+'.json.gz'
        old=store.get(key)
        if old is None:store.put(key,gzip.compress(raw,mtime=0),'application/gzip')
        elif gzip.decompress(old)!=raw:raise ValueError('sec_cache_integrity')
        try:rows,bad=sec_rows(sec)
        except ValueError as error:
            record(dict(kind='sec_availability',status='raw_only_quarantined',raw_key=key,sha256=sha(raw),exported_rows=len(sec.get('rows',[])),declared_row_count=sec.get('row_count'),normalization_blocker=str(error),export_complete=False,export_claimed_complete=sec.get('complete'),method='Public browser-rendered table export; unresolved count discrepancy'))
            return
        k=derived('sec-availability',[dict(x,observed_at=sec['observed_at'],raw_key=key,source_url=sec['source_url']) for x in rows])
        record(dict(kind='sec_availability',status='captured_rendered_table',raw_key=key,derived_key=k,sha256=sha(raw),coverage=availability_summary(rows,bad),rejected=bad,export_complete=sec['complete'],export_limitations=sec['limitations'],source_publication_time=None,method='Public browser-rendered DOM table export, not original PDF'))
    def ngs(a):
        raw=required_raw(store,a['key'],a['digest'].split(':')[1]);rows=csv_rows(raw)
        joined,counts=join_ngs(rows,cache['weekly_rosters']);k=derived(a['name'].split('.')[0]+'-roster-joined',joined)
        record(dict(kind=a['name'],status='reused_verified_and_joined',raw_key=a['key'],derived_key=k,coverage=dict(rows=len(rows),current_regular_rows=len(joined),roster_join_counts=counts,historical_point_in_time_approved=False),source_updated_at=a['source_updated_at'],new_source_requests=0))
    def links():
        joined,counts=join_snaps(cache['snap_counts'],cache['weekly_rosters']);k=derived('snaps-roster-joined',joined)
        c=config['retained_ftn'];raw=required_raw(store,c['key'],c['sha256'])
        if len(raw)!=c['size']:raise ValueError('ftn_size')
        record(dict(kind='snap_identity_and_ftn_cache',status='joined_and_reused',derived_key=k,coverage=dict(rows=len(joined),roster_join_counts=counts,historical_point_in_time_approved=False),ftn=dict(c,source_requests=0,status='unchanged_verified_cached')))
    beat=threading.Thread(target=heartbeat,daemon=True);beat.start()
    try:
        progress();store.put(prefix+'config.json',pack(config));emit('START',run_id=run_id,planned=9)
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
            fs=[pool.submit(guarded,a['family'],asset,a) for a in config['assets']]
            for future in fs:future.result()
        guarded('acc',acc);guarded('sec',sec_capture)
        for a in config['ngs']:guarded(a['name'],ngs,a)
        guarded('identity',links)
        has_gap=bool(report['failures']) or any(x.get('coverage',{}).get('rejected_rows',0)>0 or x.get('export_complete') is False for x in report['results'])
        report['status']='completed_with_gaps' if has_gap else 'selected_capture_complete'
    finally:
        stop.set();beat.join(timeout=5)
        report.update(finished_at=stamp(),elapsed_seconds=round(time.monotonic()-started,2),source_requests=fetch.calls,source_downloaded_bytes=fetch.bytes,remaining=report['planned']-report['processed'],estimated_application_compute_usd=round((time.monotonic()-started)*.461/3600,6),cost_excludes='Startup/shutdown, S3 requests/storage and discovery tooling',full_source_coverage_claimed=False)
        store.put(prefix+'report.json',pack(report));progress()
        out=Path(OUTPUT);out.mkdir(parents=True,exist_ok=True);path=out/('sports_edge_lab_football_refresh_return_'+run_id+'.zip')
        with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
            z.writestr('report.json',pack(report));z.writestr('config.json',pack(config));z.writestr('resume.json',pack(dict(failed_tasks=report['failures'],hash_cache_required=True)))
        store.put(prefix+path.name,path.read_bytes(),'application/zip');emit('FINISHED',run_id=run_id,status=report['status'],processed=report['processed'],remaining=report['remaining'],failures=len(report['failures']),return_zip=path.name)
    return 1 if report['failures'] else 0

class Tests(unittest.TestCase):
    def roster(self):return dict(season='2026',week='6',team='CHI',game_type='REG',gsis_id='00-1',pfr_id='p1',full_name='Player')
    def snap(self):return dict(season='2026',week='6',team='CHI',game_type='REG',pfr_player_id='p1',game_id='2026_06_CHI_GB',offense_snaps='10',defense_snaps='0',st_snaps='2')
    def asset(self):return dict(family='snap_counts',name=FAMILIES['snap_counts'],url='https://github.com/nflverse/nflverse-data/releases/download/snap_counts/'+FAMILIES['snap_counts'],size=100,digest='sha256:'+'a'*64)
    def test_scope(self):
        valid_asset(self.asset())
        for k,v in [('family','acb'),('url','https://example.com/data'),('name','snap_counts_2025.csv.gz'),('size',25*1024**2)]:
            with self.assertRaises(ValueError):valid_asset(dict(self.asset(),**{k:v}))
    def test_missing_column(self):
        with self.assertRaises(ValueError):audit('weekly_rosters',[{'x':1}],stamp())
    def test_season_scope(self):
        with self.assertRaises(ValueError):audit('weekly_rosters',[dict(self.roster(),season='2025')],stamp())
    def test_preseason_not_current(self):
        r,current=audit('weekly_rosters',[self.roster(),dict(self.roster(),game_type='PRE',week='20')],stamp())
        self.assertEqual(r['latest_regular_week'],6);self.assertEqual(len(current),1)
    def test_bad_snap_count(self):
        with self.assertRaises(ValueError):audit('snap_counts',[dict(self.snap(),offense_snaps='-1')],stamp())
    def test_depth_time_scope(self):
        x=dict(dt='2026-10-17T12:00:00Z',team='CHI',gsis_id='p',player_name='P',pos_slot='1',pos_rank='1')
        with self.assertRaises(ValueError):audit('depth_charts',[x],'2026-10-16T22:00:00Z')
        with self.assertRaises(ValueError):instant('2026-10-16T12:00:00')
    def test_latest_per_team(self):
        rows=[dict(dt=t,team=team,gsis_id='p',player_name='P',pos_slot='1',pos_rank='1') for t,team in [('2026-10-15T12:00:00Z','CHI'),('2026-10-16T12:00:00Z','CHI'),('2026-10-15T12:00:00Z','GB')]]
        a,current=audit('depth_charts',rows,'2026-10-16T22:00:00Z');self.assertEqual(len(current),2)
    def test_acc_requires_header_evidence(self):
        with self.assertRaises(ValueError):acc_rows('anything',{'headers':ngs_avail.HEAD})
    def test_acc_blank_headers_restore_and_preserve_null(self):
        text='| '+' | '.join(['']*9)+' |\n| '+' | '.join(['---']*9)+' |\n| A | Sat, Oct 17, 2026 | vs. B | #1 | P | Out | Out | - | - |'
        rows,bad=acc_rows(text,dict(headers=ngs_avail.HEAD,browser_run_url='https://agent.tinyfish.ai/runs/test'))
        self.assertEqual(len(rows),1);self.assertEqual(bad,[]);self.assertIsNone(rows[0]['statuses']['game_day'])
    def test_sec_count_mismatch(self):
        with self.assertRaises(ValueError):sec_rows(dict(headers=ngs_avail.HEAD,row_count=2,rows=[]))
    def test_join_uses_team_and_week(self):
        x=dict(season='2026',week='6',team_abbr='CHI',player_gsis_id='00-1',season_type='REG')
        _,a=join_ngs([x,dict(x,week='5'),dict(x,team_abbr='GB')],[self.roster()]);self.assertEqual(a,{'matched_exact_week_team_gsis':1,'unmatched':2})
    def test_ambiguous_pfr_not_guessed(self):
        rows,c=join_snaps([self.snap()],[self.roster(),dict(self.roster(),gsis_id='00-2')]);self.assertEqual(c,{'ambiguous':1});self.assertIsNone(rows[0]['gsis_id'])
    def test_missing_id_not_matched(self):
        rows,c=join_snaps([dict(self.snap(),pfr_player_id='')],[dict(self.roster(),pfr_id='')]);self.assertEqual(c,{'unmatched':1})
    def test_provider_denial_no_retry(self):
        f=Fetch()
        with mock.patch.object(f.opener,'open',side_effect=urllib.error.HTTPError('https://github.com',429,'limit',{},None)) as op:
            with self.assertRaisesRegex(RuntimeError,'429'):f.get(self.asset())
            with self.assertRaisesRegex(RuntimeError,'suspended'):f.get(self.asset())
            self.assertEqual(op.call_count,1)
    def test_corrupt_cache_stops(self):
        with self.assertRaisesRegex(ValueError,'corrupt'):required_raw(mock.Mock(get=lambda k:b'bad'),'key','a'*64)
    def test_csv_ragged(self):
        with self.assertRaises(ValueError):csv_rows(gzip.compress(b'a,b\n1,2,3\n'))
    def test_complete_runtime_cache_and_return_bundle(self):
        import tempfile
        def encode(rows):
            buf=io.StringIO();w=csv.DictWriter(buf,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows);return gzip.compress(buf.getvalue().encode())
        depth=dict(dt='2026-10-16T12:00:00Z',team='CHI',gsis_id='00-1',player_name='Player',pos_slot='1',pos_rank='1')
        raw={family:encode([row]) for family,row in [('snap_counts',self.snap()),('weekly_rosters',self.roster()),('depth_charts',depth)]}
        assets=[dict(family=family,name=name,url='https://github.com/nflverse/nflverse-data/releases/download/'+family+'/'+name,size=len(raw[family]),digest='sha256:'+sha(raw[family]),source_updated_at='2026-10-16T12:00:00Z') for family,name in FAMILIES.items()]
        ngsraw=encode([dict(season='2026',week='6',season_type='REG',team_abbr='CHI',player_gsis_id='00-1',player_display_name='Player')])
        ngs=[dict(name='ngs_'+family+'.csv.gz',key=family,digest='sha256:'+sha(ngsraw),source_updated_at='2026-10-16T12:00:00Z') for family in ['passing','rushing','receiving']]
        acc='| '+' | '.join(['']*9)+' |\n| '+' | '.join(['---']*9)+' |\n| A | Sat, Oct 17, 2026 | vs. B | #1 | P | Out | Out | - | - |'
        config=dict(assets=assets,ngs=ngs,paid_provider_requests=0,acc=dict(raw_key='acc',sha256=sha(acc.encode()),observed_at='2026-10-16T12:00:00Z',source_url='https://app.hdintelligence.com/',header_evidence=dict(headers=ngs_avail.HEAD,browser_run_url='https://agent.tinyfish.ai/runs/test')),retained_ftn=dict(key='ftn',sha256=sha(b'ftn'),size=3))
        sec=dict(headers=ngs_avail.HEAD,rows=[['A','Sat, Oct 17, 2026','vs. B','#1','P','Out','Out','-','-']],row_count=1,complete=True,limitations='',observed_at='2026-10-16T12:00:00Z',source_url='https://app.hdintelligence.com/')
        class Memory:
            def __init__(self):self.data={**{x['key']:ngsraw for x in ngs},'acc':gzip.compress(acc.encode()),'ftn':b'ftn'}
            def get(self,k):return self.data.get(k)
            def put(self,k,v,*args):self.data[k]=v
        class FakeFetch(Fetch):
            def get(self,a):self.calls+=1;self.bytes+=len(raw[a['family']]);return raw[a['family']],{}
        store=Memory()
        with tempfile.TemporaryDirectory() as tmp,mock.patch.object(sys.modules[__name__],'OUTPUT',tmp),mock.patch.object(sys.modules[__name__],'Store',return_value=store),mock.patch.object(sys.modules[__name__],'Fetch',FakeFetch),mock.patch.object(sys.modules[__name__],'embedded',side_effect=lambda name:config if name=='config.json' else sec),mock.patch('builtins.print'):
            self.assertEqual(run(),0);self.assertEqual(run(),0)
            paths=list(Path(tmp).glob('*.zip'));self.assertEqual(len(paths),2)
            for path in paths:
                with zipfile.ZipFile(path) as z:self.assertEqual(set(z.namelist()),{'report.json','config.json','resume.json'});self.assertIsNone(z.testzip())
        reports=[json.loads(v) for k,v in store.data.items() if k.endswith('/report.json')]
        self.assertEqual(sorted(x['source_requests'] for x in reports),[0,3])
        self.assertTrue(all(x['processed']==9 and x['remaining']==0 and not x['failures'] for x in reports))
        self.assertTrue(all(x['application_runtime_limit_seconds'] is None and x['paid_provider_requests']==0 for x in reports))

def main():
    p=argparse.ArgumentParser();p.add_argument('--self-test',action='store_true');args=p.parse_args()
    suite=unittest.TestSuite([unittest.defaultTestLoader.loadTestsFromTestCase(Tests),unittest.defaultTestLoader.loadTestsFromTestCase(ngs_avail.Tests),unittest.defaultTestLoader.loadTestsFromTestCase(ngs_avail.nfl_current.Tests)])
    r=unittest.TextTestRunner(verbosity=2).run(suite)
    if not r.wasSuccessful():return 1
    emit('SELF_TEST_PASS',tests=r.testsRun,version=VERSION)
    return 0 if args.self_test else run()
if __name__=='__main__':sys.exit(main())
