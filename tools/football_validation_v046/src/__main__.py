"""V046: cached historical odds time audit and Friday availability vintage.

No paid-provider credentials or requests. S3 object reuse is deduplicated before
eight parallel reads. Timestamp candidates are not an approved training dataset.
"""
import argparse, collections, concurrent.futures, copy, datetime as dt, gzip, io
import json, math, re, sys, threading, time, unittest, urllib.error, uuid, zipfile
from pathlib import Path
from unittest import mock
import readiness as rd
import football_refresh as fr
import quality, ngs_avail, nfl_current

pack,sha,stamp=fr.pack,fr.sha,fr.stamp
VERSION='sports-edge-lab-football-validation-v046'
OUTPUT='/opt/ml/processing/output'
CONTROL='shared/acquisition/football-weekend-20261016/control.json'

def moment(v):
    try:return fr.instant(v)
    except (ValueError,TypeError,AttributeError):return None

def finite(v):return isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(v)

def select_receipts(receipts,plan,expected):
    chosen=[r for r in receipts if r.get('purpose')=='football_historical_game_prices']
    wanted=collections.Counter((p['track'],p['target']) for p in plan)
    got=collections.Counter((r['request']['track'],r['request']['params']['date']) for r in chosen)
    if len(chosen)!=expected or got!=wanted:raise ValueError('selected_queue_mismatch')
    if len({r['request_id'] for r in chosen})!=len(chosen):raise ValueError('duplicate_request_identity')
    for r in chosen:
        q=r['request'];p=q['params']
        if r['status']!=200 or q['provider']!='odds' or q['track']!='ncaaf' or q['endpoint']!='/v4/historical/sports/americanfootball_ncaaf/odds':raise ValueError('receipt_scope')
        if p['markets']!='h2h,spreads,totals' or p['regions']!='us' or p['oddsFormat']!='decimal':raise ValueError('market_scope')
        if not re.fullmatch(r'tracks/ncaaf/raw/the-odds-api/objects/[0-9a-f]{2}/[0-9a-f]{64}\.json\.gz',r['raw_key']):raise ValueError('raw_key_scope')
    return chosen

def market_reasons(event,book,market,requested,snapshot):
    reasons=[];kick=moment(event.get('commence_time'))
    if not event.get('id') or event.get('sport_key')!='americanfootball_ncaaf':reasons.append('event_identity_or_sport')
    if not kick:reasons.append('kickoff_missing_or_invalid')
    elif kick<=requested:reasons.append('event_started_by_request')
    if snapshot is None:reasons.append('snapshot_missing_or_invalid')
    elif snapshot>requested:reasons.append('snapshot_after_request')
    b=moment(book.get('last_update'));m=moment(market.get('last_update'))
    if not b:reasons.append('book_update_missing_or_invalid')
    if market.get('last_update') is not None and m is None:reasons.append('market_update_invalid')
    for label,t in [('book',b),('market',m)]:
        if t and snapshot and t>snapshot:reasons.append(label+'_update_after_snapshot')
        if t and t>requested:reasons.append(label+'_update_after_request')
        if t and kick and t>=kick:reasons.append(label+'_update_at_or_after_kickoff')
    key=market.get('key');out=market.get('outcomes',[])
    if key not in ('h2h','spreads','totals'):reasons.append('unsupported_market')
    expected={'Over','Under'} if key=='totals' else {event.get('home_team'),event.get('away_team')}
    if len(out)!=2 or len(expected)!=2 or {x.get('name') for x in out}!=expected:reasons.append('incomplete_or_wrong_outcomes')
    if not all(finite(x.get('price')) and x['price']>1 for x in out):reasons.append('invalid_decimal_price')
    if key in ('spreads','totals'):
        points=[x.get('point') for x in out]
        if len(points)!=2 or not all(finite(p) for p in points):reasons.append('invalid_line')
        elif key=='spreads' and abs(sum(points))>1e-8:reasons.append('noncomplementary_spread')
        elif key=='totals' and (points[0]!=points[1] or points[0]<0):reasons.append('inconsistent_total')
    return sorted(set(reasons))

def audit_body(body,receipt):
    requested=moment(receipt['request']['params']['date'])
    if requested is None:raise ValueError('requested_time_invalid')
    if not isinstance(body,dict) or not isinstance(body.get('data'),list):raise ValueError('historical_response_schema')
    snapshot=moment(body.get('timestamp'));counts=collections.Counter();reasons=collections.Counter();examples=[];identities=collections.Counter()
    events=[]
    for e in body['data']:
        if not isinstance(e,dict):raise ValueError('event_schema')
        events.append(dict(event_id=e.get('id'),home_team=e.get('home_team'),away_team=e.get('away_team'),commence_time=e.get('commence_time')))
        for b in e.get('bookmakers',[]):
            for m in b.get('markets',[]):
                identities[(e.get('id'),b.get('key'),m.get('key'))]+=1
    for e in body['data']:
        for b in e.get('bookmakers',[]):
            for m in b.get('markets',[]):
                bad=market_reasons(e,b,m,requested,snapshot)
                if not b.get('key'):bad.append('bookmaker_identity_missing')
                if identities[(e.get('id'),b.get('key'),m.get('key'))]>1:bad.append('duplicate_event_book_market')
                counts['markets']+=1;counts['outcomes']+=len(m.get('outcomes',[]))
                counts['rejected_markets' if bad else 'timestamp_candidate_markets']+=1
                if bad:
                    reasons.update(set(bad))
                    if len(examples)<3:examples.append(dict(event_id=e.get('id'),bookmaker=b.get('key'),market=m.get('key'),reasons=sorted(set(bad))))
    return dict(request_id=receipt['request_id'],raw_key=receipt['raw_key'],raw_sha256=receipt['sha256'],requested_at=receipt['request']['params']['date'],snapshot_at=body.get('timestamp'),snapshot_lag_seconds=(requested-snapshot).total_seconds() if snapshot else None,events=len(events),counts=dict(counts),rejection_reasons=dict(reasons),rejected_examples=examples,requires_canonical_game_and_kickoff_revision_join=True,historical_training_approved=False),events

def summarize_audit(rows,failures,expected,object_count,events):
    counts=collections.Counter();reasons=collections.Counter()
    for r in rows:counts.update(r['counts']);reasons.update(r['rejection_reasons'])
    lags=[r['snapshot_lag_seconds'] for r in rows if r['snapshot_lag_seconds'] is not None]
    return dict(planned_requests=expected,audited_requests=len(rows),failed_requests=len(failures),remaining_requests=expected-len(rows)-len(failures),unique_source_objects=object_count,deduplicated_s3_reads_saved=expected-object_count,counts=dict(counts),rejection_reasons=dict(reasons),requests_with_rejected_markets=sum(bool(r['counts'].get('rejected_markets')) for r in rows),requests_without_markets=sum(not r['counts'].get('markets') for r in rows),snapshot_lag_min_seconds=min(lags,default=None),snapshot_lag_max_seconds=max(lags,default=None),unique_provider_event_ids=len(events),provider_event_ids_with_kickoff_revisions=sum(len(x['commence_times'])>1 for x in events.values()),provider_event_ids_with_team_revisions=sum(len(x['team_pairs'])>1 for x in events.values()),scope='Only v039 acquired NCAAF checkpoints; not all cached NFL/NCAAF history',historical_training_approved=False)

def save_rows(store,run_id,track,family,rows):
    raw=gzip.compress(b''.join(pack(r)+b'\n' for r in rows),mtime=0);key='tracks/'+track+'/derived/'+family+'/'+run_id+'/rows.jsonl.gz'
    store.put(key,raw,'application/gzip');return dict(key=key,rows=len(rows),bytes=len(raw),sha256=sha(raw))

def cached_odds(store,cfg,run_id,progress):
    receipts=json.loads(store.verified(cfg['odds_receipts']['key'],cfg['odds_receipts']['sha256']))
    plan=json.loads(store.verified(cfg['odds_plan']['key'],cfg['odds_plan']['sha256']))
    chosen=select_receipts(receipts,plan,cfg['expected_odds_requests']);groups=collections.defaultdict(list)
    for r in chosen:groups[r['raw_key']].append(r)
    if len(groups)!=cfg['expected_odds_objects']:raise ValueError('unique_object_count_changed')
    rows=[];failures=[];events={};compressed_bytes=0
    def worker(item):
        key,rs=item;blob=store.verified(key);raw=gzip.decompress(blob);digest=sha(raw)
        if any(r['sha256']!=digest or r['bytes']!=len(raw) for r in rs):raise ValueError('raw_integrity')
        body=json.loads(raw);return [audit_body(body,r) for r in rs],len(blob)
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        futures={pool.submit(worker,item):item for item in groups.items()}
        for f in concurrent.futures.as_completed(futures):
            key,rs=futures[f]
            try:
                audited,amount=f.result();compressed_bytes+=amount
                for row,ev in audited:
                    rows.append(row)
                    for e in ev:
                        eid=e['event_id'];v=events.setdefault(eid,dict(commence_times=set(),team_pairs=set()))
                        v['commence_times'].add(e['commence_time']);v['team_pairs'].add((e['home_team'],e['away_team']))
            except Exception as e:failures.extend(dict(request_id=r['request_id'],raw_key=key,error=type(e).__name__+':'+str(e)[:160]) for r in rs)
            progress(dict(processed_requests=len(rows)+len(failures),successful_requests=len(rows),failed_requests=len(failures),remaining_requests=len(chosen)-len(rows)-len(failures)))
    rows.sort(key=lambda x:x['request_id']);audit=summarize_audit(rows,failures,len(chosen),len(groups),events)
    registry=[dict(event_id=k,commence_times=sorted(v['commence_times'],key=str),team_pairs=sorted(v['team_pairs'],key=str),canonical_game_id=None,kickoff_revision_review_required=len(v['commence_times'])>1,historical_training_approved=False) for k,v in sorted(events.items(),key=lambda x:str(x[0]))]
    return dict(audit=audit,compressed_bytes_read=compressed_bytes,manifest=save_rows(store,run_id,'ncaaf','odds-time-audit-v046',rows),event_registry=save_rows(store,run_id,'ncaaf','odds-event-registry-v046',registry),failures=failures)

def friday(store,cfg,run_id,progress):
    seed=json.loads(rd.embedded('friday_bigten.json'))
    if sha(pack(seed['rows']))!=cfg['friday_rows_sha256'] or seed['headers']!=ngs_avail.HEAD or len(seed['rows'])!=seed['row_count']:raise ValueError('dom_seed_integrity')
    raw=pack(seed);rawkey='tracks/ncaaf/raw/official-availability/bigten/dom/'+sha(raw)+'.json';store.put(rawkey,raw)
    rows,parse_bad=fr.sec_rows(seed)
    roster=json.loads(store.verified(cfg['college_roster']['raw_key'],cfg['college_roster']['sha256'],compressed=True))
    games=json.loads(store.verified(cfg['college_schedule']['key'],cfg['college_schedule']['sha256'],compressed=True))
    joined,identity=rd.college_join(rows,roster,games,seed['observed_at'],cfg['college_roster']['retrieved_at'])
    good,bad,quality_audit=quality.availability_quality(joined,stamp())
    old=[json.loads(l) for l in gzip.decompress(store.verified(cfg['prior_bigten']['key'],cfg['prior_bigten']['sha256'])).splitlines() if l]
    def ident(r):return tuple(r.get(k) for k in ('team','game_date','opponent','jersey','player_name'))
    index={ident(r):r for r in old};changed=sum(ident(r) not in index or r['statuses']!=index[ident(r)]['statuses'] for r in good)
    return dict(source_url=seed['source_url'],observed_at=seed['observed_at'],scope=seed['scope'],full_dom_row_count=seed['total_dom_rows'],captured_subset_rows=len(seed['rows']),canonical_subset_sha256=cfg['friday_rows_sha256'],raw_key=rawkey,raw_sha256=sha(raw),identity_audit=identity,quality_audit=quality_audit,changed_valid_rows_vs_prior=changed,game_day_statuses_present=sum(r['statuses']['game_day'] is not None for r in good),valid=save_rows(store,run_id,'ncaaf','bigten-friday-availability-v046',good),quarantine=save_rows(store,run_id,'ncaaf','bigten-friday-quarantine-v046',bad+parse_bad),historical_training_approved=False)

class PublicFetch(nfl_current.Fetcher):
    def raw(self,*args,**kwargs):
        try:return super().raw(*args,**kwargs)
        except urllib.error.HTTPError as e:
            if e.code in (401,402,403,429):self.blocked=True
            raise

def injuries(store,cfg,run_id,progress):
    control=json.loads(store.verified(CONTROL))
    if control.get('provider_blocks',{}).get('nfl_official'):raise ValueError('nfl_provider_previously_stopped')
    st=nfl_current.Store(fr.BUCKET,'us-west-2');fetch=PublicFetch(2,10*1024**2,float('inf'))
    rep=dict(run_id=run_id,capture_vintage=dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:00Z'),evidence=[])
    try:raw,receipt=nfl_current.capture(st,fetch,'https://www.nfl.com/injuries/league/2026/reg6','injuries',rep)
    except Exception as e:
        progress(dict(nfl_source_requests=fetch.calls,nfl_provider_blocked=fetch.blocked))
        if fetch.blocked:control_update(store,dict(nfl_official='V046 provider-denial stop; do not retry on later passes'))
        raise
    rows,bad=ngs_avail.nfl_rows(raw)
    for r in rows:r.update(known_available_at=receipt['captured_at'],original_publication_time=None)
    prior=cfg['prior_nfl_injury']
    oldraw=store.verified(prior['raw_key'],prior['sha256'],compressed=True);old,_=ngs_avail.nfl_rows(oldraw)
    # Compare source fields, excluding our new observation timestamp.
    oldset={pack(r) for r in old};changed=sum(pack({k:v for k,v in r.items() if k not in ('known_available_at','original_publication_time')}) not in oldset for r in rows)
    progress(dict(nfl_source_requests=fetch.calls,nfl_provider_blocked=fetch.blocked))
    return dict(receipt=receipt,robots_evidence=rep['evidence'],source_requests=fetch.calls,rows=len(rows),rejected=len(bad),changed_rows_vs_prior=changed,output=save_rows(store,run_id,'nfl','injuries-current-v046',rows),publication_time_unverified=True)

def control_update(store,blocks=None,run_record=None):
    from botocore.exceptions import ClientError
    for attempt in range(3):
        response=store.s3.get_object(Bucket=fr.BUCKET,Key=CONTROL)
        with response['Body'] as b:control=json.loads(b.read())
        control.setdefault('provider_blocks',{}).update(blocks or {})
        if run_record and not any(x.get('run_id')==run_record['run_id'] for x in control.setdefault('runs',[])):control['runs'].append(run_record)
        try:
            store.s3.put_object(Bucket=fr.BUCKET,Key=CONTROL,Body=pack(control),IfMatch=response['ETag'],ContentType='application/json',ServerSideEncryption='AES256');return
        except ClientError as e:
            if e.response.get('ResponseMetadata',{}).get('HTTPStatusCode')!=412:raise
    raise RuntimeError('control_ledger_concurrent_update_conflict')

def run():
    cfg=json.loads(rd.embedded('config.json'));store=rd.Store();started=time.monotonic()
    run_id=dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:10];prefix='shared/acquisition/football-validation/'+run_id+'/'
    report=dict(version=VERSION,run_id=run_id,started_at=stamp(),status='running',results={},failures=[],planned_stages=3,processed_stages=0,planned_odds_requests=cfg['expected_odds_requests'],processed_requests=0,remaining_requests=cfg['expected_odds_requests'],odds_credits=0,cfbd_requests=0,cbbd_requests=0,nfl_source_requests=0,application_runtime_limit_seconds=None)
    lock=threading.Lock();stop=threading.Event();heartbeat_errors=[]
    def progress(values):
        with lock:report.update(values)
    def beat():
        while not stop.wait(20):
            try:
                with lock:p=copy.deepcopy(report)
                p.update(at=stamp(),elapsed_seconds=round(time.monotonic()-started,2));store.put(prefix+'progress.json',pack(p));print(pack(dict(event='HEARTBEAT',at=p['at'],processed=p['processed_requests'],remaining=p['remaining_requests'])).decode(),flush=True)
            except Exception as e:heartbeat_errors.append(type(e).__name__)
    thread=threading.Thread(target=beat,daemon=True);thread.start()
    try:
        # Availability first, so a large cache audit cannot delay preserving it.
        for name,fn in [('friday_bigten',friday),('nfl_injuries',injuries),('cached_odds_time_audit',cached_odds)]:
            try:
                value=fn(store,cfg,run_id,progress)
                with lock:
                    report['results'][name]=value;report['processed_stages']+=1
                    if value.get('failures'):report['failures'].append(dict(stage=name,failed_requests=len(value['failures'])))
                print(pack(dict(event='STAGE_FINISHED',stage=name,at=stamp())).decode(),flush=True)
            except Exception as e:
                with lock:report['failures'].append(dict(stage=name,error_type=type(e).__name__,reason=str(e)[:200]))
    finally:
        stop.set();thread.join(timeout=65)
        report.update(finished_at=stamp(),remaining_stages=3-report['processed_stages'],elapsed_seconds=round(time.monotonic()-started,2),heartbeat_errors=heartbeat_errors,status='partial_failure' if report['failures'] else 'completed_with_explicit_gaps')
        try:control_update(store,run_record=dict(run_id=run_id,job_name=cfg['job_name'],finished_at=report['finished_at'],cfbd_attempts=0,odds_credits=0,cbbd_requests=0,nfl_source_requests=report['nfl_source_requests'],report_key=prefix+'report.json',status=report['status']))
        except Exception as e:report['failures'].append(dict(stage='control_ledger',error_type=type(e).__name__,reason=str(e)[:200]));report['status']='partial_failure'
        store.put(prefix+'report.json',pack(report));store.put(prefix+'progress.json',pack(report));store.put(prefix+'config.json',pack(cfg))
        out=Path(OUTPUT);out.mkdir(parents=True,exist_ok=True);name='sports_edge_lab_football_validation_return_'+run_id+'.zip'
        with zipfile.ZipFile(out/name,'w',zipfile.ZIP_DEFLATED) as z:
            z.writestr('report.json',pack(report));z.writestr('config.json',pack(cfg));z.writestr('resume.json',pack(dict(reuse_successful_cache=True,failed_stages=report['failures'],paid_provider_requests=0)))
        store.put(prefix+name,(out/name).read_bytes(),'application/zip');print(pack(dict(event='FINISHED',run_id=run_id,status=report['status'],return_zip=name)).decode(),flush=True)
    return 1 if report['failures'] else 0

class Tests(unittest.TestCase):
    def event(self):return dict(id='e',sport_key='americanfootball_ncaaf',home_team='A',away_team='B',commence_time='2026-10-17T00:00Z')
    def book(self):return dict(key='b',last_update='2026-10-16T20:00Z')
    def market(self):return dict(key='h2h',last_update='2026-10-16T20:00Z',outcomes=[dict(name='A',price=1.9),dict(name='B',price=1.9)])
    def reasons(self,e=None,b=None,m=None,s='2026-10-16T20:00Z'):return market_reasons(e or self.event(),b or self.book(),m or self.market(),moment('2026-10-16T21:00Z'),moment(s))
    def test_valid_times(self):self.assertEqual(self.reasons(),[])
    def test_snapshot_after_request(self):self.assertIn('snapshot_after_request',self.reasons(s='2026-10-16T22:00Z'))
    def test_snapshot_missing(self):self.assertIn('snapshot_missing_or_invalid',self.reasons(s=''))
    def test_book_after_snapshot(self):self.assertIn('book_update_after_snapshot',self.reasons(b=dict(self.book(),last_update='2026-10-16T20:01Z')))
    def test_market_after_request(self):self.assertIn('market_update_after_request',self.reasons(m=dict(self.market(),last_update='2026-10-16T22:00Z')))
    def test_started_game(self):self.assertIn('event_started_by_request',self.reasons(e=dict(self.event(),commence_time='2026-10-16T21:00Z')))
    def test_naive_time(self):self.assertIsNone(moment('2026-10-16T20:00'))
    def test_missing_book_time(self):self.assertIn('book_update_missing_or_invalid',self.reasons(b=dict(self.book(),last_update=None)))
    def test_market_missing_time_falls_back_to_book(self):m=self.market();del m['last_update'];self.assertEqual(self.reasons(m=m),[])
    def test_bad_price(self):m=self.market();m['outcomes'][0]['price']=float('nan');self.assertIn('invalid_decimal_price',self.reasons(m=m))
    def test_invalid_outcomes(self):m=self.market();m['outcomes'][1]['name']='A';self.assertIn('incomplete_or_wrong_outcomes',self.reasons(m=m))
    def test_bad_spread_pair(self):m=self.market();m['key']='spreads';m['outcomes'][0]['point']=3;m['outcomes'][1]['point']=3;self.assertIn('noncomplementary_spread',self.reasons(m=m))
    def test_good_spread_pair(self):m=self.market();m['key']='spreads';m['outcomes'][0]['point']=3;m['outcomes'][1]['point']=-3;self.assertEqual(self.reasons(m=m),[])
    def test_bad_total_pair(self):m=dict(key='totals',outcomes=[dict(name='Over',price=1.9,point=40),dict(name='Under',price=1.9,point=41)]);self.assertIn('inconsistent_total',self.reasons(m=m))
    def test_duplicate_market_rejected(self):
        e=self.event();b=self.book();b['markets']=[self.market(),self.market()];e['bookmakers']=[b]
        r=dict(request_id='r',raw_key='k',sha256='h',request=dict(params=dict(date='2026-10-16T21:00Z')))
        a,_=audit_body(dict(timestamp='2026-10-16T20:00Z',data=[e]),r)
        self.assertEqual(a['counts']['rejected_markets'],2)
    def test_quarantine_missing_jersey(self):
        good,bad,a=quality.availability_quality([dict(jersey='',player_name='CJ Christian')],stamp());self.assertFalse(good);self.assertEqual(len(bad),1)
    def test_402_stops_provider(self):
        f=PublicFetch(2,10**7,float('inf'))
        with mock.patch.object(nfl_current.Fetcher,'raw',side_effect=urllib.error.HTTPError('x',402,'denied',{},None)):
            with self.assertRaises(urllib.error.HTTPError):f.raw('x')
        self.assertTrue(f.blocked)
    def test_summary_keeps_failures_and_scope(self):
        a=summarize_audit([],['failure'],2,2,{})
        self.assertEqual(a['remaining_requests'],1);self.assertFalse(a['historical_training_approved'])
    def test_cached_audit_reuses_duplicate_objects(self):
        e=self.event();b=self.book();b['markets']=[self.market()];e['bookmakers']=[b]
        body=pack(dict(timestamp='2026-10-16T20:00Z',data=[e]));digest=sha(body);key='tracks/ncaaf/raw/the-odds-api/objects/'+digest[:2]+'/'+digest+'.json.gz'
        receipts=[];plan=[]
        for i,date in enumerate(['2026-10-16T21:00Z','2026-10-16T22:00Z']):
            receipts.append(dict(request_id=str(i),purpose='football_historical_game_prices',status=200,bytes=len(body),sha256=digest,raw_key=key,request=dict(track='ncaaf',provider='odds',endpoint='/v4/historical/sports/americanfootball_ncaaf/odds',params=dict(date=date,markets='h2h,spreads,totals',regions='us',oddsFormat='decimal'))))
            plan.append(dict(track='ncaaf',target=date))
        class Memory(rd.Store):
            def __init__(self):self.data={'receipts':pack(receipts),'plan':pack(plan),key:gzip.compress(body)};self.reads=collections.Counter()
            def get(self,k):self.reads[k]+=1;return self.data[k]
            def put(self,k,v,*args):self.data[k]=v
        store=Memory();cfg=dict(odds_receipts=dict(key='receipts',sha256=sha(pack(receipts))),odds_plan=dict(key='plan',sha256=sha(pack(plan))),expected_odds_requests=2,expected_odds_objects=1)
        r=cached_odds(store,cfg,'test',lambda _:None)
        self.assertEqual(store.reads[key],1);self.assertEqual(r['audit']['audited_requests'],2);self.assertEqual(r['audit']['counts']['timestamp_candidate_markets'],2);self.assertFalse(r['failures'])
    def test_corrupt_cache_is_recorded_not_approved(self):
        r=dict(request_id='r',purpose='football_historical_game_prices',status=200,bytes=1,sha256='a'*64,raw_key='tracks/ncaaf/raw/the-odds-api/objects/aa/'+'a'*64+'.json.gz',request=dict(track='ncaaf',provider='odds',endpoint='/v4/historical/sports/americanfootball_ncaaf/odds',params=dict(date='2026-10-16T21:00Z',markets='h2h,spreads,totals',regions='us',oddsFormat='decimal')))
        plan=[dict(track='ncaaf',target='2026-10-16T21:00Z')];data={'r':pack([r]),'p':pack(plan),r['raw_key']:gzip.compress(b'wrong')}
        class Memory(rd.Store):
            def __init__(self):pass
            def get(self,k):return data[k]
            def put(self,k,v,*args):data[k]=v
        result=cached_odds(Memory(),dict(odds_receipts=dict(key='r',sha256=sha(data['r'])),odds_plan=dict(key='p',sha256=sha(data['p'])),expected_odds_requests=1,expected_odds_objects=1),'test',lambda _:None)
        self.assertEqual(result['audit']['failed_requests'],1);self.assertEqual(result['audit']['audited_requests'],0)
    def test_real_embedded_entrypoint_and_unique_zip(self):
        import tempfile
        class Memory:
            def __init__(self):self.data={}
            def put(self,k,v,*args):self.data[k]=v
        store=Memory();real=json.loads(rd.embedded('config.json'));mod=sys.modules[__name__]
        with tempfile.TemporaryDirectory() as tmp:
            fixture=Path(tmp)/'fixture.pyz'
            with zipfile.ZipFile(fixture,'w') as z:z.writestr('config.json',pack(real))
            with mock.patch.object(sys,'argv',[str(fixture)]),mock.patch.object(rd,'Store',return_value=store),mock.patch.object(mod,'OUTPUT',tmp),mock.patch.object(mod,'friday',return_value={}),mock.patch.object(mod,'injuries',return_value={}),mock.patch.object(mod,'cached_odds',return_value={}),mock.patch.object(mod,'control_update'),mock.patch('builtins.print'):
                self.assertEqual(run(),0)
            files=list(Path(tmp).glob('*.zip'));self.assertEqual(len(files),1)
            with zipfile.ZipFile(files[0]) as z:self.assertIsNone(z.testzip());self.assertEqual(set(z.namelist()),{'report.json','config.json','resume.json'})

def main():
    p=argparse.ArgumentParser();p.add_argument('--self-test',action='store_true');args=p.parse_args()
    suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromTestCase(c) for c in (Tests,quality.Tests,rd.Tests,fr.Tests,ngs_avail.Tests,nfl_current.Tests))
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():return 1
    print(pack(dict(event='SELF_TEST_PASS',tests=result.testsRun,version=VERSION,at=stamp())).decode(),flush=True)
    return 0 if args.self_test else run()
if __name__=='__main__':sys.exit(main())
