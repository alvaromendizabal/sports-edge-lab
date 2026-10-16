"""Public NGS refresh and official football availability acquisition."""
import argparse, collections, concurrent.futures, csv, datetime as dt, gzip, hashlib
import io, json, re, signal, sys, threading, time, unittest, urllib.error, urllib.request, urllib.parse, uuid, zipfile
from html.parser import HTMLParser
from pathlib import Path
from unittest import mock
import nfl_current
BUCKET='sagemaker-sports-edge-lab-560403859723-us-west-2'
VERSION='sports-edge-lab-ngs-availability-v040'
OUTPUT='/opt/ml/processing/output'
HEAD=['Team','Date','Opponent','Number','Player','Initial Status','Update 1 Status','Update 2 Status','Game Day Status']
STATUSES={'Available','Probable','Questionable','Doubtful','Out','Game Time Decision','Exempt'}
def stamp():return dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds').replace('+00:00','Z')
def pack(x):return json.dumps(x,sort_keys=True,separators=(',',':'),default=str).encode()
def sha(x):return hashlib.sha256(x).hexdigest()
def emit(event,**kw):print(pack(dict(event=event,timestamp=stamp(),**kw)).decode(),flush=True)
def embedded(name):
    with zipfile.ZipFile(sys.argv[0]) as z:return json.loads(z.read(name))
def valid_asset(a):
    if not re.fullmatch(r'ngs_(passing|receiving|rushing)\.csv\.gz',a['name']):raise ValueError('unexpected_asset_name')
    if a['url']!='https://github.com/nflverse/nflverse-data/releases/download/nextgen_stats/'+a['name']:raise ValueError('unexpected_asset_url')
    if not re.fullmatch(r'sha256:[a-f0-9]{64}',a.get('digest','')) or not 0<a['size']<8*1024**2:raise ValueError('invalid_asset_metadata')
def audit_ngs(raw):
    with gzip.GzipFile(fileobj=io.BytesIO(raw)) as f:decoded=f.read(32*1024**2+1)
    if len(decoded)>32*1024**2:raise ValueError('decoded_csv_too_large')
    reader=csv.DictReader(io.StringIO(decoded.decode('utf-8-sig')))
    if not {'season','season_type','week','player_gsis_id','player_display_name'}<=set(reader.fieldnames or []):raise ValueError('ngs_schema_changed')
    rows=list(reader)
    if not rows:raise ValueError('empty_ngs')
    counts=collections.Counter();ids=collections.Counter()
    for r in rows:
        y,w=int(r['season']),int(r['week']);t=r['season_type']
        if not 2016<=y<=2026 or not 0<=w<=23 or t not in ('REG','POST'):raise ValueError('invalid_ngs_season_week')
        counts[(y,t,w)]+=1;ids[(y,t,w,r['player_gsis_id'],r.get('team_abbr'))]+=1
    current={w:n for (y,t,w),n in counts.items() if y==2026 and t=='REG' and w>0}
    return dict(rows=len(rows),season_min=min(k[0] for k in counts),season_max=max(k[0] for k in counts),
      current_regular_week_counts=current,latest_current_regular_week=max(current,default=None),
      missing_player_ids=sum(r['player_gsis_id'] in ('','NA') for r in rows),duplicate_identity_rows=sum(n-1 for n in ids.values() if n>1),
      season_type_week_counts=[dict(season=y,season_type=t,week=w,rows=n) for (y,t,w),n in sorted(counts.items())],
      granularity='Player-week and season aggregates, not tracking trajectories',all_games_or_players_complete=False,historical_point_in_time_approved=False)
def availability_rows(text):
    lines=[l for l in text.splitlines() if l.startswith('|')]
    if not lines or [x.strip() for x in lines[0].strip('|').split('|')]!=HEAD:raise ValueError('missing_or_changed_headers')
    rows=[];bad=[]
    for line in lines[2:]:
        c=[x.strip() for x in line.strip('|').split('|')]
        try:
            if len(c)!=9:raise ValueError('column_count')
            date=None
            for fmt in ('%a, %b %d, %Y','%m/%d/%y'):
                try:date=dt.datetime.strptime(c[1],fmt).date().isoformat();break
                except ValueError:pass
            if not date or not date.startswith('2026-'):raise ValueError('date_scope')
            statuses=[None if v in ('','-','—') else v for v in c[5:]]
            if any(v is not None and v not in STATUSES for v in statuses):raise ValueError('unknown_status')
            rows.append(dict(team=c[0],game_date=date,opponent=c[2],jersey=c[3],player_name=c[4],
              statuses=dict(zip(('initial','update_1','update_2','game_day'),statuses)),player_id=None,source_publication_time=None,historical_point_in_time_approved=False))
        except ValueError as e:bad.append(dict(line=line,reason=str(e)))
    return rows,bad
class Tables(HTMLParser):
    def __init__(self):super().__init__();self.tables=[];self.table=None;self.row=None;self.cell=None;self.heading=None;self.context=''
    def handle_starttag(self,t,a):
        if re.fullmatch('h[1-6]',t):self.heading=[]
        if t=='table':self.table=dict(context=self.context,rows=[])
        if t=='tr' and self.table is not None:self.row=[]
        if t in ('th','td') and self.row is not None:self.cell=[]
    def handle_data(self,x):
        if self.cell is not None:self.cell.append(x)
        if self.heading is not None:self.heading.append(x)
    def handle_endtag(self,t):
        if re.fullmatch('h[1-6]',t) and self.heading is not None:self.context=' '.join(' '.join(self.heading).split());self.heading=None
        if t in ('th','td') and self.cell is not None:self.row.append(' '.join(' '.join(self.cell).split()));self.cell=None
        if t=='tr' and self.row is not None:self.table['rows'].append(self.row);self.row=None
        if t=='table' and self.table is not None:self.tables.append(self.table);self.table=None
def nfl_rows(raw):
    p=Tables();p.feed(raw.decode('utf8','replace'));rows=[];bad=[]
    for i,t in enumerate(p.tables):
        if not t['rows']:continue
        if t['rows'][0]!=['Player','Position','Injuries','Practice Status','Game Status']:bad.append(dict(table=i,reason='headers'));continue
        for r in t['rows'][1:]:
            if len(r)!=5 or not r[0]:bad.append(dict(table=i,reason='row_shape',cells=r));continue
            rows.append(dict(zip(('player_name','position','injuries','practice_status','game_status'),[x or None for x in r]),
              table_index=i,heading_context=t['context'],player_id=None,historical_point_in_time_approved=False))
    if not rows:raise ValueError('no_valid_nfl_rows')
    return rows,bad
class Redirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,url):
        p=urllib.parse.urlsplit(url)
        if p.scheme!='https' or p.hostname not in ('github.com','release-assets.githubusercontent.com','objects.githubusercontent.com'):raise ValueError('unexpected_redirect')
        return super().redirect_request(req,fp,code,msg,headers,url)
class Fetch:
    def __init__(self):self.lock=threading.Lock();self.last=-1e12;self.calls=0;self.bytes=0;self.blocked=False;self.opener=urllib.request.build_opener(Redirect)
    def get(self,a):
        valid_asset(a)
        with self.lock:
            if self.blocked:raise RuntimeError('source_suspended')
            if self.calls>=3:raise ValueError('finite_queue_exceeded')
            pause=max(0,self.last+.5-time.monotonic())
            if pause:time.sleep(pause)
            self.last=time.monotonic();self.calls+=1
        try:
            with self.opener.open(urllib.request.Request(a['url'],headers={'User-Agent':nfl_current.UA}),timeout=30) as r:
                raw=r.read(a['size']+1);headers={k:r.headers.get(k) for k in ('ETag','Last-Modified','Date')}
            with self.lock:self.bytes+=len(raw)
            if len(raw)!=a['size'] or 'sha256:'+sha(raw)!=a['digest']:raise ValueError('asset_integrity_mismatch')
            return raw,headers
        except urllib.error.HTTPError as e:
            with self.lock:
                if e.code in (401,403,429):self.blocked=True
            code=e.code;e.close();raise RuntimeError('source_http_'+str(code))
def run():
    sources=embedded('sources.json');seeds=embedded('availability_seeds.json')
    run_id=dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:10];started=time.monotonic()
    store=nfl_current.Store(BUCKET,'us-west-2');fetch=Fetch();lock=threading.Lock();stop=threading.Event()
    prefix='shared/acquisition/ngs-availability/'+run_id+'/'
    report=dict(run_id=run_id,version=VERSION,started_at=stamp(),status='running',planned=4+len(seeds),processed=0,results=[],failures=[],
      paid_provider_calls=0,subscription_credits=0,application_runtime_limit_seconds=None,discovery_gaps=sources['gaps'],
      optimizations=['Concurrent independent public assets, source pacing and hash cache','No duplicate format variants or paid source overlap','Existing NFL source guards; explicit missing-value and schema checks'])
    def record(x):
        with lock:report['results'].append(x);report['processed']+=1
        emit('CAPTURE',run_id=run_id,kind=x['kind'],status=x['status'],name=x.get('name'),rows=x.get('rows',x.get('coverage',{}).get('rows')))
    def beat():
        while not stop.wait(20):
            with lock:r=json.loads(pack(report))
            r.update(timestamp=stamp(),remaining=r['planned']-r['processed'],elapsed_seconds=round(time.monotonic()-started,2))
            store.put(prefix+'progress.json',pack(r));emit('HEARTBEAT',run_id=run_id,processed=r['processed'],remaining=r['remaining'])
    heartbeat=threading.Thread(target=beat,daemon=True);heartbeat.start()
    def ngs(a):
        valid_asset(a);digest=a['digest'].split(':')[1];key='tracks/nfl/raw/nflverse/nextgen_stats/'+digest+'/'+a['name']
        raw=store.get(key);status='reused_verified';headers={}
        if raw is None:raw,headers=fetch.get(a);status='downloaded'
        if len(raw)!=a['size'] or sha(raw)!=digest:raise ValueError('cached_asset_integrity')
        coverage=audit_ngs(raw)
        if status=='downloaded':store.put(key,raw,'application/gzip')
        receipt=dict(kind='ngs',name=a['name'],status=status,raw_key=key,bytes=len(raw),sha256=digest,source_url=a['url'],
          source_updated_at=a['updated_at'],source_asset_id=a['id'],captured_at=stamp(),headers=headers,coverage=coverage,
          lineage='nflverse compilation of NFL NGS summaries; not original tracking')
        store.put(prefix+a['name']+'.receipt.json',pack(receipt));record(receipt)
    def nfl():
        r=dict(run_id=run_id,capture_vintage=stamp(),evidence=[]);f=nfl_current.Fetcher(2,9000000,float('inf'))
        raw,receipt=nfl_current.capture(store,f,nfl_current.SEEDS[0]['url'],'injuries',r);rows,bad=nfl_rows(raw)
        key='tracks/nfl/derived/nfl-official-injuries/'+run_id+'/rows.jsonl.gz'
        store.put(key,gzip.compress(b'\n'.join(pack(dict(x,captured_at=receipt['captured_at'],raw_key=receipt['raw_key'])) for x in rows)+b'\n',mtime=0),'application/gzip')
        record(dict(kind='nfl_injuries',status='captured_and_extracted',receipt=receipt,rows=len(rows),rejected=bad,derived_key=key,
          source_requests=f.calls,source_publication_time=None,player_identity_join_validated=False))
    def ncaa(seed):
        raw=seed['extracted_markdown'].encode();digest=sha(raw);conf=seed['conference'].lower().replace(' ','')
        key='tracks/ncaaf/raw/'+conf+'-availability-rendered/objects/'+digest+'.md.gz';cached=store.get(key)
        if cached is None:store.put(key,gzip.compress(raw,mtime=0),'application/gzip')
        elif sha(gzip.decompress(cached))!=digest:raise ValueError('rendered_cache_integrity')
        result={k:v for k,v in seed.items() if k!='extracted_markdown'}
        result.update(kind='ncaa_availability',status='raw_only',raw_key=key,sha256=digest,raw_bytes=len(raw),historical_point_in_time_approved=False)
        try:rows,bad=availability_rows(seed['extracted_markdown'])
        except ValueError as e:result['normalization_blocker']=str(e);record(result);return
        key2='tracks/ncaaf/derived/'+conf+'-availability/'+run_id+'/rows.jsonl.gz'
        store.put(key2,gzip.compress(b'\n'.join(pack(dict(x,observed_at=seed['observed_at'],source_url=seed['source_url'],raw_key=key)) for x in rows)+b'\n',mtime=0),'application/gzip')
        current=[x for x in rows if '2026-10-16'<=x['game_date']<='2026-10-18']
        result.update(status='captured_and_extracted',rows=len(rows),rejected=bad,derived_key=key2,
          first_game_date=min((x['game_date'] for x in rows),default=None),last_game_date=max((x['game_date'] for x in rows),default=None),
          team_games=len({(x['team'],x['opponent'],x['game_date']) for x in rows}),current_weekend_rows=len(current),
          current_weekend_team_games=len({(x['team'],x['opponent'],x['game_date']) for x in current}),player_identity_join_validated=False)
        record(result)
    def guarded(name,fn,*args):
        try:fn(*args)
        except Exception as e:
            with lock:report['processed']+=1;report['failures'].append(dict(task=name,type=type(e).__name__,reason=str(e)[:250]))
            emit('TASK_FAILED',task=name,type=type(e).__name__,reason=str(e)[:250])
    try:
        store.put(prefix+'sources.json',pack(sources));store.put(prefix+'progress.json',pack(report));emit('START',run_id=run_id,planned=report['planned'])
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            jobs=[pool.submit(guarded,a['name'],ngs,a) for a in sources['assets']]+[pool.submit(guarded,'nfl_injuries',nfl)]
            for job in jobs:job.result()
        for seed in seeds:guarded(seed['conference'],ncaa,seed)
        report['status']='completed_with_gaps' if report['failures'] or any(x['status']=='raw_only' for x in report['results']) else 'selected_capture_complete'
    finally:
        stop.set();heartbeat.join(timeout=5);report.update(finished_at=stamp(),elapsed_seconds=round(time.monotonic()-started,2),ngs_source_requests=fetch.calls,ngs_downloaded_bytes=fetch.bytes,remaining=report['planned']-report['processed'])
        report['estimated_application_compute_usd']=round(report['elapsed_seconds']*.461/3600,6);report['cost_excludes']='Startup, shutdown, S3 storage and requests'
        store.put(prefix+'report.json',pack(report));out=Path(OUTPUT);out.mkdir(parents=True,exist_ok=True)
        path=out/('sports_edge_lab_ngs_availability_return_'+run_id+'.zip')
        with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
            z.writestr('report.json',pack(report));z.writestr('sources.json',pack(sources));z.writestr('resume.json',pack(dict(reuse_verified_hash_objects=True,failed_tasks=report['failures'])))
        store.put(prefix+path.name,path.read_bytes(),'application/zip')
        emit('FINISHED',run_id=run_id,status=report['status'],report_key=prefix+'report.json',return_zip=path.name,remaining=report['remaining'],failed_tasks=len(report['failures']))
    return 1 if report['failures'] else 0
class Tests(unittest.TestCase):
    def asset(self):return dict(name='ngs_passing.csv.gz',url='https://github.com/nflverse/nflverse-data/releases/download/nextgen_stats/ngs_passing.csv.gz',digest='sha256:'+'a'*64,size=100)
    def test_source_scope(self):
        valid_asset(self.asset())
        for k,v in [('name','acb.csv.gz'),('url','https://example.com'),('digest',''),('size',9000000)]:
            with self.assertRaises(ValueError):valid_asset(dict(self.asset(),**{k:v}))
    def test_ngs_schema(self):
        with self.assertRaises(ValueError):audit_ngs(gzip.compress(b'x,y\n1,2\n'))
    def test_ngs_current_and_aggregate(self):
        raw=gzip.compress(b'season,season_type,week,player_gsis_id,player_display_name\n2026,REG,6,p,Player\n2026,REG,0,p,Player\n')
        r=audit_ngs(raw);self.assertEqual(r['latest_current_regular_week'],6);self.assertEqual(r['current_regular_week_counts'],{6:1})
    def test_ngs_future_rejected(self):
        with self.assertRaises(ValueError):audit_ngs(gzip.compress(b'season,season_type,week,player_gsis_id,player_display_name\n2027,REG,1,p,P\n'))
    def table(self,r):return '| '+' | '.join(HEAD)+' |\n| '+' | '.join(['---']*9)+' |\n| '+r+' |\n'
    def test_missing_status(self):
        r,b=availability_rows(self.table('A | Sat, Oct 17, 2026 | vs. B | #1 | P | Out | - | - | -'))
        self.assertIsNone(r[0]['statuses']['game_day']);self.assertEqual(b,[])
    def test_ambiguous_columns(self):
        r,b=availability_rows(self.table('A | Sat, Oct 17, 2026 | vs. B | #1 | P | Out | - | -'));self.assertEqual(r,[]);self.assertEqual(len(b),1)
    def test_missing_headers(self):
        with self.assertRaises(ValueError):availability_rows('| | | | | | | | | |\n')
    def test_nfl_empty_status(self):
        raw=b'<h3>Bears</h3><table><tr><th>Player</th><th>Position</th><th>Injuries</th><th>Practice Status</th><th>Game Status</th></tr><tr><td>A</td><td>QB</td><td></td><td>Full</td><td></td></tr></table>'
        r,b=nfl_rows(raw);self.assertIsNone(r[0]['game_status']);self.assertEqual(r[0]['heading_context'],'Bears')
    def test_redirect_rejected(self):
        with self.assertRaises(ValueError):Redirect().redirect_request(None,None,302,'',{},'https://example.com/x')
    def test_rate_denial_stops(self):
        f=Fetch()
        with mock.patch.object(f.opener,'open',side_effect=urllib.error.HTTPError('https://github.com',429,'limit',{},None)) as op:
            with self.assertRaisesRegex(RuntimeError,'429'):f.get(self.asset())
            with self.assertRaisesRegex(RuntimeError,'suspended'):f.get(self.asset())
            self.assertEqual(op.call_count,1)
    def test_integrity_and_pacing(self):
        a=self.asset();raw=b'x'*100;a['digest']='sha256:'+sha(raw)
        class R:
            headers={}
            def __enter__(self):return self
            def __exit__(self,*a):pass
            def read(self,n):return raw
        f=Fetch();f.last=10
        with mock.patch.object(f.opener,'open',return_value=R()),mock.patch.object(time,'monotonic',return_value=10),mock.patch.object(time,'sleep') as s:
            self.assertEqual(f.get(a)[0],raw);s.assert_called_once_with(.5)
    def test_complete_run_cache_and_unique_return(self):
        import tempfile
        raw=gzip.compress(b'season,season_type,week,player_gsis_id,player_display_name\n2026,REG,6,p,Player\n')
        assets=[]
        for stat in ('passing','receiving','rushing'):
            a=self.asset();a.update(name='ngs_'+stat+'.csv.gz',size=len(raw),digest='sha256:'+sha(raw),id=1,updated_at='2026-10-16T12:00:00Z')
            a['url']='https://github.com/nflverse/nflverse-data/releases/download/nextgen_stats/'+a['name'];assets.append(a)
        class Store:
            def __init__(self):self.data={}
            def get(self,k):return self.data.get(k)
            def put(self,k,v,*args):self.data[k]=v
        class FetchFixture(Fetch):
            def get(self,a):self.calls+=1;self.bytes+=len(raw);return raw,{}
        nfl=b'<h3>Bears</h3><table><tr><th>Player</th><th>Position</th><th>Injuries</th><th>Practice Status</th><th>Game Status</th></tr><tr><td>A</td><td>QB</td><td></td><td>Full</td><td></td></tr></table>'
        seed=dict(conference='Big 12',source_url='https://app.hdintelligence.com/',observed_at='2026-10-16T21:00:00Z',extracted_markdown=self.table('A | Sat, Oct 17, 2026 | vs. B | #1 | P | Out | - | - | -'))
        seeds=[seed,dict(seed,conference='ACC',extracted_markdown='| | | | | | | | | |\n')]
        store=Store()
        with tempfile.TemporaryDirectory() as folder,mock.patch.object(sys.modules[__name__],'OUTPUT',folder),mock.patch.object(sys.modules[__name__],'embedded',side_effect=lambda n:dict(assets=assets,gaps=[]) if n=='sources.json' else seeds),mock.patch.object(nfl_current,'Store',return_value=store),mock.patch.object(sys.modules[__name__],'Fetch',FetchFixture),mock.patch.object(nfl_current,'capture',return_value=(nfl,dict(raw_key='test',captured_at=stamp()))),mock.patch('builtins.print'):
            self.assertEqual(run(),0);self.assertEqual(len(list(Path(folder).glob('*.zip'))),1)
            self.assertEqual(run(),0);self.assertEqual(len(list(Path(folder).glob('*.zip'))),2)
        reports=[json.loads(v) for k,v in store.data.items() if k.endswith('/report.json')]
        self.assertEqual(sorted(r['ngs_source_requests'] for r in reports),[0,3])
        self.assertTrue(all(r['processed']==6 and r['remaining']==0 and not r['failures'] and r['status']=='completed_with_gaps' for r in reports))
        self.assertTrue(all(len([x for x in r['results'] if x['status']=='raw_only'])==1 for r in reports))

def main():
    p=argparse.ArgumentParser();p.add_argument('--self-test',action='store_true');args=p.parse_args()
    suite=unittest.TestSuite([unittest.defaultTestLoader.loadTestsFromTestCase(Tests),unittest.defaultTestLoader.loadTestsFromTestCase(nfl_current.Tests)])
    r=unittest.TextTestRunner(verbosity=2).run(suite)
    if not r.wasSuccessful():return 1
    emit('SELF_TEST_PASS',tests=r.testsRun,version=VERSION)
    return 0 if args.self_test else run()
if __name__=='__main__':raise SystemExit(main())
