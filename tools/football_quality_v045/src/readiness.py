"""V042: cached football identity repair, conservative time gates and new games."""
import argparse, collections, concurrent.futures, csv, datetime as dt, gzip, hashlib
import io, json, re, sys, threading, time, unicodedata, unittest, urllib.error, urllib.parse, urllib.request, uuid, zipfile
from pathlib import Path
from zoneinfo import ZoneInfo
from unittest import mock
import football_refresh as fr
import ngs_avail, nfl_current

BUCKET=fr.BUCKET
VERSION='sports-edge-lab-football-readiness-v042'
def pack(v):return json.dumps(v,sort_keys=True,separators=(',',':'),default=str).encode()
def sha(b):return hashlib.sha256(b).hexdigest()
def stamp():return dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds').replace('+00:00','Z')
def embedded(name):
    with zipfile.ZipFile(sys.argv[0]) as z:return z.read(name)
def clean(v):return re.sub(r'[^a-z0-9]','',unicodedata.normalize('NFKD',str(v or '')).encode('ascii','ignore').decode().lower())
def number(v):
    v=str(v).strip().lstrip('#')
    return str(int(v)) if re.fullmatch(r'\d+',v) else None
def available_before(available_at,prediction_at,kickoff):
    if not all((available_at,prediction_at,kickoff)):return False
    return fr.instant(available_at)<=fr.instant(prediction_at)<fr.instant(kickoff)
def later(*values):return max(values,key=fr.instant)
def aliases(raw):
    rows=[r for r in csv.DictReader(io.StringIO(raw.decode())) if r['season']=='2026']
    if len(rows)!=32 or len({r['team'] for r in rows})!=32:raise ValueError('2026_team_mapping_scope')
    choices=collections.defaultdict(set)
    for r in rows:
        for k in ('team','nfl','espn','pfr','pfflabel','fo','full'):
            if r[k]:choices[r[k].upper()].add(r['team'])
    if any(len(s)!=1 for s in choices.values()):raise ValueError('ambiguous_team_alias')
    return {k:next(iter(s)) for k,s in choices.items()}
def team(v,mapping):return mapping.get(str(v).upper(),str(v))

def nfl_identities(rosters,snaps,ngs,mapping,available_at):
    fixed=[dict(r,team=team(r['team'],mapping)) for r in rosters]
    ngs_out={};counts={}
    for kind,rows in ngs.items():
        normalized=[dict(r,team_abbr=team(r.get('team_abbr'),mapping)) for r in rows]
        joined,c=fr.join_ngs(normalized,fixed)
        for r in joined:r.update(known_available_at=available_at,availability_basis='max_actual_input_retrieval_times',original_publication_time=None)
        ngs_out[kind]=joined;counts[kind]=c
    joined,c=fr.join_snaps([dict(r,team=team(r['team'],mapping)) for r in snaps],fixed)
    cross=collections.defaultdict(set)
    for r in fixed:
        if r['pfr_id'] not in fr.NULLS and r['gsis_id'] not in fr.NULLS:cross[r['pfr_id']].add(r['gsis_id'])
    identity_counts=collections.Counter()
    for r in joined:
        method='same_week_team_pfr' if r.get('gsis_id') else 'unresolved'
        candidates=cross[r['pfr_player_id']]
        if not r.get('gsis_id') and len(candidates)==1:
            r['gsis_id']=next(iter(candidates));method='unique_2026_pfr_gsis_crosswalk_membership_unverified'
        elif not r.get('gsis_id') and len(candidates)>1:method='ambiguous_pfr_gsis'
        identity_counts[method]+=1
        r.update(identity_method=method,known_available_at=available_at,original_publication_time=None,own_game_pregame_eligible=False)
    return joined,ngs_out,dict(snaps_same_week=c,snap_identity_counts=dict(identity_counts),ngs=counts)

def college_join(rows,roster,games,observed,roster_observed):
    index=collections.defaultdict(dict)
    for p in roster:
        n=number(p.get('jersey'));name=clean(str(p.get('firstName',''))+' '+str(p.get('lastName','')))
        if n is not None and name and p.get('id') is not None:index[(clean(p.get('team')),name,n)][str(p['id'])]=p
    out=[];counter=collections.Counter();gates=collections.Counter();team_names=sorted({p.get('team','') for p in roster})
    for r in rows:
        r=dict(r);candidates=index[(clean(r['team']),clean(r['player_name']),number(r['jersey']))]
        method='exact_normalized_team_name_jersey_unique' if len(candidates)==1 else 'ambiguous' if candidates else 'unmatched'
        r['player_id']=next(iter(candidates)) if len(candidates)==1 else None
        r['identity_method']=method;counter[method]+=1
        opponent=clean(re.sub(r'^(?:at|vs\.?)\s+','',r['opponent'],flags=re.I))
        matched=[]
        for g in games:
            a,b=clean(g.get('homeTeam')),clean(g.get('awayTeam'))
            if {a,b}!={clean(r['team']),opponent}:continue
            date=fr.instant(g['startDate']).astimezone(ZoneInfo('America/New_York')).date().isoformat()
            if date==r['game_date']:matched.append(g)
        kickoff=matched[0]['startDate'] if len(matched)==1 else None
        at=later(observed,roster_observed)
        gate='observed_before_kickoff' if available_before(at,at,kickoff) else 'not_pregame_at_capture' if kickoff else 'game_unresolved'
        gates[gate]+=1
        r.update(known_available_at=at,source_observed_at=observed,original_publication_time=None,source_publication_time=None,historical_point_in_time_approved=False,matched_game_id=matched[0]['id'] if len(matched)==1 else None,kickoff=kickoff,reported_game_time_gate=gate,report_date_matching_timezone='America/New_York',model_ready=False)
        out.append(r)
    return out,dict(rows=len(out),identity_counts=dict(counter),time_gate_counts=dict(gates),unmatched_teams=sorted({r['team'] for r in out if not any(clean(r['team'])==clean(t) for t in team_names)}),unmatched_examples=[{k:r[k] for k in ('team','player_name','jersey','game_date')} for r in out if r['identity_method']=='unmatched'][:20])

class Http:
    def __init__(self,key):self.key=key;self.calls=collections.Counter();self.last={};self.blocked=set();self.bytes=0;self.opener=urllib.request.build_opener(nfl_current.NoRedirect)
    def get(self,url,provider='public',cap=20*1024**2):
        host=urllib.parse.urlsplit(url).hostname
        expected={'cfbd':'api.collegefootballdata.com','public':'raw.githubusercontent.com'}
        if provider not in expected or host!=expected[provider]:raise ValueError('source_not_allowlisted')
        if provider in self.blocked:raise RuntimeError('provider_stopped')
        if self.calls['cfbd']>=16 and provider=='cfbd':raise RuntimeError('finite_cfbd_bound')
        if self.calls['public']>=2 and provider=='public':raise RuntimeError('finite_public_bound')
        wait=max(0,self.last.get(provider,-1e12)+1-time.monotonic())
        if wait:time.sleep(wait)
        self.last[provider]=time.monotonic();self.calls[provider]+=1
        headers={'User-Agent':nfl_current.UA,'Accept':'application/json,text/csv'}
        if provider=='cfbd':headers['Authorization']='Bearer '+self.key
        try:
            with self.opener.open(urllib.request.Request(url,headers=headers),timeout=60) as r:
                b=r.read(cap+1);h={k:r.headers.get(k) for k in ('Date','ETag','Last-Modified')}
            self.bytes+=len(b)
            if len(b)>cap:raise ValueError('response_size_bound')
            return b,h
        except urllib.error.HTTPError as e:
            code=e.code
            if code in (401,402,403,429):self.blocked.add(provider)
            e.close();raise RuntimeError('provider_http_'+str(code))

class Store(fr.Store):
    def verified(self,key,digest=None,compressed=False):
        b=self.get(key)
        if b is None:raise ValueError('missing_input:'+key)
        raw=gzip.decompress(b) if compressed else b
        if digest and sha(raw)!=digest:raise ValueError('input_hash_mismatch:'+key)
        return raw

def run():
    cfg=json.loads(embedded('config.json'));s=Store();started=time.monotonic();at=stamp()
    run_id=dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:10]
    prefix='shared/acquisition/football-readiness/'+run_id+'/'
    report=dict(version=VERSION,run_id=run_id,started_at=at,status='running',results={},failures=[],planned_stages=5,processed_stages=0,application_runtime_limit_seconds=None,odds_credits=0,cbbd_requests=0)
    lock=threading.Lock();stop=threading.Event()
    def beat():
        while not stop.wait(20):
            with lock:r=json.loads(pack(report))
            r.update(at=stamp(),remaining_stages=5-r['processed_stages'],elapsed_seconds=round(time.monotonic()-started,2),estimated_application_compute_usd=round((time.monotonic()-started)*.461/3600,6))
            s.put(prefix+'progress.json',pack(r));print(pack(dict(event='HEARTBEAT',**{k:r[k] for k in ('at','remaining_stages','elapsed_seconds','estimated_application_compute_usd')})).decode(),flush=True)
    threading.Thread(target=beat,daemon=True).start()
    def save_rows(track,family,rows):
        b=gzip.compress(b''.join(pack(r)+b'\n' for r in rows),mtime=0);key='tracks/'+track+'/derived/'+family+'/'+run_id+'/rows.jsonl.gz';s.put(key,b,'application/gzip');return dict(key=key,rows=len(rows),bytes=len(b),sha256=sha(b))
    def stage(name,fn):
        try:r=fn()
        except Exception as e:r=dict(status='failed',error_type=type(e).__name__,reason=str(e)[:240]);report['failures'].append(dict(stage=name,**r))
        with lock:report['results'][name]=r;report['processed_stages']+=1
        print(pack(dict(event='STAGE_FINISHED',stage=name,at=stamp(),status=r.get('status','completed'))).decode(),flush=True)
    previous=json.loads(s.verified(cfg['prior_refresh_report']))
    src={r['kind']:r for r in previous['results']};mapping=aliases(embedded('team_alias_source.csv'))
    rosters=fr.csv_rows(s.verified(src['weekly_rosters']['raw_key'],src['weekly_rosters']['sha256']))
    snaps=fr.csv_rows(s.verified(src['snap_counts']['raw_key'],src['snap_counts']['sha256']))
    ngs={}
    for x in cfg.get('ngs',[]):ngs[x['name']]=fr.csv_rows(s.verified(x['key'],x['digest'].split(':')[1]))
    observed=later(src['weekly_rosters']['captured_at'],src['snap_counts']['captured_at'],cfg['team_alias_source']['observed_at'])
    def identities():
        snapout,ngsout,counts=nfl_identities(rosters,snaps,ngs,mapping,observed)
        outputs=[save_rows('nfl','snaps-identity-v042',snapout)]+[save_rows('nfl',k.replace('.csv.gz','')+'-identity-v042',r) for k,r in ngsout.items()]
        return dict(status='completed',counts=counts,outputs=outputs,unmatched_snap_examples=[{k:r.get(k) for k in ('team','week','player','pfr_player_id','identity_method')} for r in snapout if not r.get('gsis_id')][:30],team_aliases={k:v for k,v in mapping.items() if k!=v},historical_point_in_time_approved=False)
    stage('nfl_identity',identities)
    roster_spec=cfg['cfbd_roster'];college_roster=json.loads(s.verified(roster_spec['raw_key'],roster_spec['sha256'],True))
    game_spec=next(r for r in cfg['cfbd_previous'] if r['request']['endpoint']=='/games')
    old_games=json.loads(s.verified(game_spec['raw_key'],game_spec['sha256'],True));games=old_games
    http=None
    def fresh_games():
        nonlocal games,http
        import boto3
        from botocore.config import Config
        key=boto3.client('ssm',region_name='us-west-2',config=Config(retries={'total_max_attempts':3,'mode':'standard'})).get_parameter(Name='/sports-edge-lab/shared/cfbd/key',WithDecryption=True)['Parameter']['Value']
        http=Http(key)
        b,h=http.get('https://api.collegefootballdata.com/games?year=2026&seasonType=both&classification=fbs','cfbd')
        candidate=json.loads(b)
        if not isinstance(candidate,list) or not candidate or not {'id','startDate','completed','homeTeam','awayTeam'}<=set(candidate[0]):raise ValueError('cfbd_games_schema')
        games=candidate;digest=sha(b);key='tracks/ncaaf/raw/cfbd/objects/'+digest[:2]+'/'+digest+'.json.gz';s.put(key,gzip.compress(b,mtime=0),'application/gzip')
        receipt=dict(key=key,sha256=digest,observed_at=stamp(),headers=h,rows=len(games));s.put(prefix+'games_receipt.json',pack(receipt))
        old={str(g['id']) for g in old_games if g.get('completed') is True}
        new=[g for g in games if g.get('completed') is True and str(g['id']) not in old]
        windows=sorted({(g['week'],g['seasonType']) for g in new})
        if len(windows)>3:raise ValueError('unexpected_completed_game_delta')
        details=[]
        for week,kind in windows:
            for endpoint in ('/plays','/drives','/games/teams','/games/players','/stats/game/advanced'):
                params={'year':2026,'week':week,'seasonType':kind}
                if endpoint in ('/plays','/drives'):params['classification']='fbs'
                bb,hh=http.get('https://api.collegefootballdata.com'+endpoint+'?'+urllib.parse.urlencode(params),'cfbd',cap=64*1024**2)
                data=json.loads(bb);digest=sha(bb);key='tracks/ncaaf/raw/cfbd/objects/'+digest[:2]+'/'+digest+'.json.gz';s.put(key,gzip.compress(bb,mtime=0),'application/gzip')
                details.append(dict(endpoint=endpoint,params=params,key=key,sha256=digest,observed_at=stamp(),rows=len(data) if isinstance(data,list) else None))
        today=dt.datetime.now(ZoneInfo('America/Los_Angeles')).date().isoformat()
        upcoming=[dict(id=g['id'],home=g['homeTeam'],away=g['awayTeam'],kickoff=g['startDate'],completed=g['completed']) for g in games if fr.instant(g['startDate']).astimezone(ZoneInfo('America/Los_Angeles')).date().isoformat()==today]
        return dict(status='completed',schedule=receipt,new_completed_games=len(new),new_completed_ids=[g['id'] for g in new],detail_captures=details,tonight_games=upcoming,source_requests=dict(http.calls),all_preexisting_detail_caches_preserved=True)
    stage('new_ncaaf_games',fresh_games)
    def college():
        out={}
        for spec in cfg['availability']:
            rows=[json.loads(l) for l in gzip.decompress(s.verified(spec['key'])).splitlines() if l]
            joined,audit=college_join(rows,college_roster,games,spec['observed_at'],roster_spec['retrieved_at'])
            out[spec['conference']]=dict(audit=audit,output=save_rows('ncaaf',clean(spec['conference'])+'-availability-identity-v042',joined))
        return dict(status='completed',conferences=out,roster_rows=len(college_roster),original_publication_times_unavailable=True)
    stage('college_identity_and_time',college)
    def nfl_games():
        nonlocal http
        if http is None:http=Http(None)
        b,h=http.get('https://raw.githubusercontent.com/nflverse/nfldata/master/data/games.csv')
        schedule=list(csv.DictReader(io.StringIO(b.decode('utf-8-sig'))));current=[g for g in schedule if g['season']=='2026']
        if not current:raise ValueError('nfl_schedule_schema')
        key='tracks/nfl/raw/nfldata/games/'+sha(b)+'/games.csv';s.put(key,b,'text/csv')
        pbp=fr.csv_rows(s.verified(cfg['nfl_pbp']['key'],cfg['nfl_pbp']['sha256']))
        expected={g['game_id'] for g in current if g.get('result') not in ('','NA','NaN',None)};have={r['game_id'] for r in pbp}
        return dict(status='completed',schedule_key=key,schedule_observed_at=stamp(),schedule_sha256=sha(b),pbp_cache_verified=True,pbp_source_hash_rechecked=cfg['nfl_pbp']['release_rechecked_at'],completed_schedule_games=len(expected),pbp_games=len(have),missing_completed_games=sorted(expected-have),pbp_rows=len(pbp),historical_point_in_time_approved=False)
    stage('nfl_game_freshness',nfl_games)
    def injuries():
        st=nfl_current.Store(BUCKET,'us-west-2');fetch=nfl_current.Fetcher(2,10*1024**2,float('inf'))
        rep=dict(run_id=run_id,capture_vintage=dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:00Z'),evidence=[])
        raw,receipt=nfl_current.capture(st,fetch,'https://www.nfl.com/injuries/league/2026/reg6','injuries',rep)
        rows,bad=ngs_avail.nfl_rows(raw)
        for r in rows:r.update(known_available_at=receipt['captured_at'],original_publication_time=None)
        return dict(status='completed',receipt=receipt,robots_evidence=rep['evidence'],source_requests=fetch.calls,rows=len(rows),rejected=len(bad),output=save_rows('nfl','injuries-current-v042',rows),publication_time_unverified=True)
    stage('nfl_injury_refresh',injuries)
    stop.set();report.update(finished_at=stamp(),status='completed_with_gaps' if not report['failures'] else 'partial_failure',remaining_stages=5-report['processed_stages'],elapsed_seconds=round(time.monotonic()-started,2),cfbd_requests=http.calls['cfbd'] if http else 0,public_requests=http.calls['public'] if http else 0,provider_blocks=sorted(http.blocked) if http else [],historical_training_approval=False)
    s.put(prefix+'report.json',pack(report));s.put(prefix+'progress.json',pack(report));s.put(prefix+'config.json',pack(cfg))
    out=Path('/opt/ml/processing/output');out.mkdir(parents=True,exist_ok=True);name='sports_edge_lab_football_readiness_return_'+run_id+'.zip'
    with zipfile.ZipFile(out/name,'w',zipfile.ZIP_DEFLATED) as z:
        z.writestr('report.json',pack(report));z.writestr('config.json',pack(cfg));z.writestr('resume.json',pack(dict(run_id=run_id,finished_stages=[k for k,v in report['results'].items() if v.get('status')=='completed'],failed_stages=report['failures'],never_repeat_completed_source_calls=True)))
    s.put(prefix+name,(out/name).read_bytes(),'application/zip');print(pack(dict(event='FINISHED',run_id=run_id,status=report['status'],failures=len(report['failures']),remaining=report['remaining_stages'],return_zip=name)).decode(),flush=True)
    return 1 if report['failures'] else 0

class Tests(unittest.TestCase):
    def test_available_after_prediction_rejected(self):self.assertFalse(available_before('2026-10-16T22:00Z','2026-10-16T21:00Z','2026-10-17T21:00Z'))
    def test_available_at_prediction_before_kickoff(self):self.assertTrue(available_before('2026-10-16T22:00Z','2026-10-16T22:00Z','2026-10-17T21:00Z'))
    def test_postkickoff_rejected(self):self.assertFalse(available_before('2026-10-16T22:00Z','2026-10-17T22:00Z','2026-10-17T21:00Z'))
    def test_naive_timestamp_rejected(self):
        with self.assertRaises(ValueError):available_before('2026-10-16T22:00','2026-10-16T22:00Z','2026-10-17T21:00Z')
    def test_unknown_time_rejected(self):self.assertFalse(available_before(None,'2026-10-16T22:00Z','2026-10-17T21:00Z'))
    def test_number_not_imputed(self):self.assertIsNone(number(None));self.assertEqual(number('#00'),'0')
    def test_source_block_stops_before_http(self):
        f=Http('test');f.blocked.add('cfbd')
        with self.assertRaisesRegex(RuntimeError,'provider_stopped'):f.get('https://api.collegefootballdata.com/games','cfbd')
        self.assertEqual(sum(f.calls.values()),0)
    def test_wrong_host_never_receives_credential(self):
        f=Http('test')
        with self.assertRaises(ValueError):f.get('https://example.org/games','cfbd')
        self.assertEqual(sum(f.calls.values()),0)
    def test_verified_alias_recovers_exact_ngs(self):
        roster=[dict(season='2026',week='1',team='LA',game_type='REG',gsis_id='g',pfr_id='p')]
        ngs={'pass':[dict(season='2026',week='1',team_abbr='LAR',season_type='REG',player_gsis_id='g')]}
        _,out,c=nfl_identities(roster,[],ngs,{'LAR':'LA'},'2026-10-16T22:00Z')
        self.assertEqual(c['ngs']['pass']['matched_exact_week_team_gsis'],1)
    def test_global_id_does_not_claim_week_membership(self):
        r=[dict(season='2026',week='1',team='LA',game_type='REG',gsis_id='g',pfr_id='p')]
        s=[dict(season='2026',week='2',team='LA',game_type='REG',pfr_player_id='p')]
        o,_,_=nfl_identities(r,s,{}, {},'2026-10-16T22:00Z');self.assertEqual(o[0]['gsis_id'],'g');self.assertEqual(o[0]['roster_join_status'],'unmatched');self.assertFalse(o[0]['own_game_pregame_eligible'])
    def test_ambiguous_global_id_not_guessed(self):
        r=[dict(season='2026',week='1',team='LA',game_type='REG',gsis_id=g,pfr_id='p') for g in ('g','h')]
        s=[dict(season='2026',week='2',team='LA',game_type='REG',pfr_player_id='p')]
        o,_,_=nfl_identities(r,s,{}, {},'2026-10-16T22:00Z');self.assertIsNone(o[0]['gsis_id'])
    def test_college_matching_requires_jersey_and_unique_id(self):
        row=dict(team='Texas',player_name='A. Smith',jersey='7',game_date='2026-10-17',opponent='vs. Other')
        roster=[dict(team='Texas',firstName='A',lastName='Smith',jersey=7,id=1)]
        o,c=college_join([row],roster,[],'2026-10-16T22:00Z','2026-10-16T20:00Z');self.assertEqual(o[0]['player_id'],'1');self.assertEqual(o[0]['reported_game_time_gate'],'game_unresolved')
        roster.append(dict(roster[0],id=2));o,c=college_join([row],roster,[],'2026-10-16T22:00Z','2026-10-16T20:00Z');self.assertIsNone(o[0]['player_id'])
    def test_college_missing_status_preserved(self):
        r=dict(team='Texas',player_name='A Smith',jersey='7',game_date='2026-10-17',opponent='vs. Other',statuses={'game_day':None})
        o,_=college_join([r],[],[],'2026-10-16T22:00Z','2026-10-16T20:00Z');self.assertIsNone(o[0]['statuses']['game_day'])

def main():
    p=argparse.ArgumentParser();p.add_argument('--self-test',action='store_true');args=p.parse_args()
    suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromTestCase(c) for c in (Tests,fr.Tests,ngs_avail.Tests,nfl_current.Tests))
    r=unittest.TextTestRunner(verbosity=2).run(suite)
    if not r.wasSuccessful():return 1
    print(pack(dict(event='SELF_TEST_PASS',tests=r.testsRun,at=stamp(),version=VERSION)).decode(),flush=True)
    return 0 if args.self_test else run()
if __name__=='__main__':sys.exit(main())
