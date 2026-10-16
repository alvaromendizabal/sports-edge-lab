"""V044: verified player crosswalk and malformed availability quarantine."""
import argparse, collections, datetime as dt, gzip, io, json, re, sys, threading, time, unittest, urllib.error, urllib.request, uuid, zipfile
from pathlib import Path
from unittest import mock
import readiness as rd
import football_refresh as fr
import ngs_avail, nfl_current

pack,sha,stamp=fr.pack,fr.sha,fr.stamp
VERSION='sports-edge-lab-football-quality-v044'
URL='https://github.com/nflverse/nflverse-data/releases/download/players/players.csv.gz'
NULLS=fr.NULLS
def asset_valid(a):
    if a.get('url')!=URL or a.get('name')!='players.csv.gz':raise ValueError('source_scope')
    if not re.fullmatch(r'sha256:[0-9a-f]{64}',a.get('digest','')) or not 0<a.get('size',0)<=10*1024**2:raise ValueError('asset_metadata')
def integrity(raw,a):
    if len(raw)!=a['size'] or 'sha256:'+sha(raw)!=a['digest']:raise ValueError('asset_integrity')
class Fetch:
    def __init__(self):self.calls=0;self.blocked=False;self.opener=urllib.request.build_opener(ngs_avail.Redirect)
    def get(self,a):
        asset_valid(a)
        if self.blocked:raise RuntimeError('provider_stopped')
        if self.calls>=1:raise RuntimeError('finite_source_queue_exhausted')
        self.calls+=1
        try:
            with self.opener.open(urllib.request.Request(a['url'],headers={'User-Agent':nfl_current.UA}),timeout=60) as r:
                b=r.read(a['size']+1);h={k:r.headers.get(k) for k in ('Date','ETag','Last-Modified')}
            integrity(b,a);return b,h
        except urllib.error.HTTPError as e:
            code=e.code;e.close()
            if code in (401,402,403,429):self.blocked=True
            raise RuntimeError('provider_http_'+str(code))
def player_index(players):
    fr.require(players,['gsis_id','pfr_id','display_name'])
    index=collections.defaultdict(set)
    for p in players:
        if p['pfr_id'] not in NULLS and p['gsis_id'] not in NULLS:index[p['pfr_id']].add(p['gsis_id'])
    return index
def snap_join(snaps,players,rosters,mapping,observed):
    index=player_index(players);members=collections.defaultdict(set)
    for r in rosters:
        if r.get('game_type')=='REG' and r.get('season')=='2026' and r.get('gsis_id') not in NULLS:
            members[(r['season'],r['week'],rd.team(r['team'],mapping))].add(r['gsis_id'])
    out=[];counts=collections.Counter();membership=collections.Counter()
    for original in snaps:
        r=dict(original);old=r.get('gsis_id');ids=index[r.get('pfr_player_id')]
        if old:
            method='prior_verified_identity'
            if ids and old not in ids:method='conflicting_crosswalk';r['gsis_id']=None
        elif len(ids)==1:r['gsis_id']=next(iter(ids));method='unique_authoritative_crosswalk_pfr_gsis'
        else:method='ambiguous_crosswalk' if ids else 'unresolved'
        status='same_week_team_gsis_confirmed' if r.get('gsis_id') in members[(r['season'],r['week'],rd.team(r['team'],mapping))] else 'unverified'
        r.update(identity_method=method,roster_membership_status=status,known_available_at=rd.later(r['known_available_at'],observed),original_publication_time=None,historical_point_in_time_approved=False,own_game_pregame_eligible=False)
        counts[method]+=1;membership[status]+=1;out.append(r)
    return out,dict(rows=len(out),matched=sum(bool(r.get('gsis_id')) for r in out),unresolved=sum(not r.get('gsis_id') for r in out),identity_methods=dict(counts),roster_membership=dict(membership),unresolved_examples=[{k:r.get(k) for k in ('player','pfr_player_id','team','week','identity_method')} for r in out if not r.get('gsis_id')][:40])
STATUS_NAMES={'out','doubtful','questionable','probable','available','unavailable','gamedecision','gametimedecision'}
def availability_quality(rows,checked_at):
    valid=[];bad=[];counts=collections.Counter()
    for i,source in enumerate(rows):
        r=dict(source);reasons=[]
        if rd.number(r.get('jersey')) is None:reasons.append('invalid_jersey')
        if not r.get('player_name') or rd.clean(r.get('player_name')) in STATUS_NAMES:reasons.append('invalid_player_name')
        if reasons:bad.append(dict(source_row=i,reasons=reasons,row=r));continue
        r.update(quality_checked_at=checked_at,source_row=i,structural_validation='passed',prospective_identity_time_candidate=bool(r.get('player_id')) and r.get('reported_game_time_gate')=='observed_before_kickoff',historical_point_in_time_approved=False,model_ready=False)
        counts[r.get('identity_method','missing')]+=1;valid.append(r)
    return valid,bad,dict(input_rows=len(rows),valid_rows=len(valid),quarantined_rows=len(bad),identity_counts=dict(counts),prospective_identity_time_candidates=sum(r['prospective_identity_time_candidate'] for r in valid),model_ready=False,historical_point_in_time_approved=False)
def run():
    cfg=json.loads(fr.embedded('config.json'));asset_valid(cfg['players_asset'])
    store=rd.Store();fetch=Fetch();started=time.monotonic();run_id=dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:10]
    prefix='shared/acquisition/football-quality/'+run_id+'/'
    report=dict(version=VERSION,run_id=run_id,started_at=stamp(),status='running',results={},failures=[],planned_stages=3,processed_stages=0,application_runtime_limit_seconds=None,odds_credits=0,cfbd_requests=0,cbbd_requests=0)
    stop=threading.Event()
    def beat():
        while not stop.wait(20):
            p=dict(report,at=stamp(),elapsed_seconds=round(time.monotonic()-started,2));store.put(prefix+'progress.json',pack(p));print(pack(dict(event='HEARTBEAT',at=p['at'],processed=report['processed_stages'])).decode(),flush=True)
    threading.Thread(target=beat,daemon=True).start()
    def save(track,family,rows):
        raw=gzip.compress(b''.join(pack(r)+b'\n' for r in rows),mtime=0);key='tracks/'+track+'/derived/'+family+'/'+run_id+'/rows.jsonl.gz';store.put(key,raw,'application/gzip');return dict(key=key,rows=len(rows),bytes=len(raw),sha256=sha(raw))
    def stage(name,value):
        report['results'][name]=value;report['processed_stages']+=1;print(pack(dict(event='STAGE_FINISHED',stage=name,at=stamp())).decode(),flush=True)
    try:
        a=cfg['players_asset'];key='tracks/nfl/raw/nflverse/players/'+a['digest'].split(':')[1]+'/'+a['name'];raw=store.get(key);headers={};status='reused_verified'
        if raw is None:raw,headers=fetch.get(a);store.put(key,raw,'application/gzip');status='downloaded'
        integrity(raw,a);players=fr.csv_rows(raw);player_index(players);observed=stamp()
        stage('players_crosswalk',dict(status=status,raw_key=key,bytes=len(raw),sha256=sha(raw),rows=len(players),captured_or_reverified_at=observed,source_url=a['url'],headers=headers))
        source=cfg['snap_input'];snaps=[json.loads(l) for l in gzip.decompress(store.verified(source['key'],source['sha256'])).splitlines() if l]
        prior=json.loads(store.verified(cfg['prior_refresh_report']));roster_src=next(r for r in prior['results'] if r['kind']=='weekly_rosters')
        rosters=fr.csv_rows(store.verified(roster_src['raw_key'],roster_src['sha256']));mapping=rd.aliases(fr.embedded('team_alias_source.csv'))
        rows,audit=snap_join(snaps,players,rosters,mapping,observed)
        stage('snap_identity',dict(audit=audit,output=save('nfl','snaps-identity-v044',rows),source_input=source))
        college={}
        for conference,src in cfg['availability_inputs'].items():
            rows=[json.loads(l) for l in gzip.decompress(store.verified(src['key'],src['sha256'])).splitlines() if l]
            good,bad,audit=availability_quality(rows,stamp());family=rd.clean(conference)+'-availability-quality-v044'
            college[conference]=dict(audit=audit,valid=save('ncaaf',family,good),quarantine=save('ncaaf',family+'-quarantine',bad),source_input=src)
        stage('college_quality',dict(conferences=college))
    except Exception as e:report['failures'].append(dict(error_type=type(e).__name__,reason=str(e)[:250]))
    finally:
        stop.set();report.update(finished_at=stamp(),remaining_stages=3-report['processed_stages'],source_requests=fetch.calls,provider_stopped=fetch.blocked,elapsed_seconds=round(time.monotonic()-started,2),status='partial_failure' if report['failures'] else 'completed_with_explicit_gaps')
        store.put(prefix+'report.json',pack(report));store.put(prefix+'progress.json',pack(report));store.put(prefix+'config.json',pack(cfg))
        out=Path('/opt/ml/processing/output');out.mkdir(parents=True,exist_ok=True);name='sports_edge_lab_football_quality_return_'+run_id+'.zip'
        with zipfile.ZipFile(out/name,'w',zipfile.ZIP_DEFLATED) as z:
            z.writestr('report.json',pack(report));z.writestr('config.json',pack(cfg));z.writestr('resume.json',pack(dict(reuse_successful_cache=True,failures=report['failures'])))
        store.put(prefix+name,(out/name).read_bytes(),'application/zip');print(pack(dict(event='FINISHED',run_id=run_id,failures=len(report['failures']),return_zip=name)).decode(),flush=True)
    return 1 if report['failures'] else 0

class Tests(unittest.TestCase):
    def snap(self):return dict(season='2026',week='1',team='CHI',pfr_player_id='p',gsis_id=None,known_available_at='2026-10-16T20:00Z')
    def player(self):return dict(pfr_id='p',gsis_id='g',display_name='Player')
    def row(self):return dict(jersey='#7',player_name='A Smith',player_id='7',reported_game_time_gate='observed_before_kickoff',identity_method='exact',statuses={'game_day':None})
    def test_exact_crosswalk_recovers(self):
        rows,a=snap_join([self.snap()],[self.player()],[],{},'2026-10-16T22:00Z');self.assertEqual(a['matched'],1);self.assertEqual(rows[0]['gsis_id'],'g')
    def test_ambiguous_crosswalk_never_guessed(self):
        rows,a=snap_join([self.snap()],[self.player(),dict(self.player(),gsis_id='h')],[],{},'2026-10-16T22:00Z');self.assertEqual(a['unresolved'],1)
    def test_conflict_quarantined(self):
        rows,a=snap_join([dict(self.snap(),gsis_id='h')],[self.player()],[],{},'2026-10-16T22:00Z');self.assertIsNone(rows[0]['gsis_id']);self.assertEqual(rows[0]['identity_method'],'conflicting_crosswalk')
    def test_prior_identity_retained_without_crosswalk(self):
        rows,a=snap_join([dict(self.snap(),pfr_player_id='x',gsis_id='h')],[self.player()],[],{},'2026-10-16T22:00Z');self.assertEqual(rows[0]['gsis_id'],'h')
    def test_identity_does_not_prove_membership(self):
        rows,a=snap_join([self.snap()],[self.player()],[],{},'2026-10-16T22:00Z');self.assertEqual(rows[0]['roster_membership_status'],'unverified');self.assertFalse(rows[0]['own_game_pregame_eligible'])
    def test_exact_week_membership(self):
        roster=[dict(season='2026',week='1',team='CHI',gsis_id='g',game_type='REG')];rows,a=snap_join([self.snap()],[self.player()],roster,{},'2026-10-16T22:00Z');self.assertEqual(rows[0]['roster_membership_status'],'same_week_team_gsis_confirmed')
    def test_information_time_not_backdated(self):
        rows,a=snap_join([self.snap()],[self.player()],[],{},'2026-10-16T22:00Z');self.assertEqual(rows[0]['known_available_at'],'2026-10-16T22:00Z');self.assertFalse(rows[0]['historical_point_in_time_approved'])
    def test_shifted_acc_row_rejected(self):
        good,bad,a=availability_quality([dict(self.row(),jersey='Kris Hughes',player_name='Out')],stamp());self.assertFalse(good);self.assertEqual(len(bad),1);self.assertEqual(bad[0]['reasons'],['invalid_jersey','invalid_player_name'])
    def test_valid_null_status_preserved(self):
        good,bad,a=availability_quality([self.row()],stamp());self.assertIsNone(good[0]['statuses']['game_day']);self.assertTrue(good[0]['prospective_identity_time_candidate']);self.assertFalse(good[0]['model_ready'])
    def test_unresolved_not_candidate(self):
        good,bad,a=availability_quality([dict(self.row(),player_id=None)],stamp());self.assertFalse(good[0]['prospective_identity_time_candidate'])
    def test_old_capture_not_candidate(self):
        good,bad,a=availability_quality([dict(self.row(),reported_game_time_gate='not_pregame_at_capture')],stamp());self.assertFalse(good[0]['prospective_identity_time_candidate'])
    def test_asset_scope(self):
        with self.assertRaises(ValueError):asset_valid(dict(url='https://example.com',name='players.csv.gz'))
    def test_denial_stops(self):
        f=Fetch();f.blocked=True;a=dict(url=URL,name='players.csv.gz',digest='sha256:'+'a'*64,size=1)
        with self.assertRaisesRegex(RuntimeError,'provider_stopped'):f.get(a)
        self.assertEqual(f.calls,0)
    def test_corrupt_asset_rejected(self):
        with self.assertRaises(ValueError):integrity(b'x',dict(size=1,digest='sha256:'+'a'*64))

def main():
    p=argparse.ArgumentParser();p.add_argument('--self-test',action='store_true');args=p.parse_args()
    suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromTestCase(c) for c in (Tests,rd.Tests,fr.Tests,ngs_avail.Tests,nfl_current.Tests))
    r=unittest.TextTestRunner(verbosity=2).run(suite)
    if not r.wasSuccessful():return 1
    print(pack(dict(event='SELF_TEST_PASS',tests=r.testsRun,version=VERSION,at=stamp())).decode(),flush=True)
    return 0 if args.self_test else run()
if __name__=='__main__':sys.exit(main())
