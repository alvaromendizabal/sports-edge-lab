#!/usr/bin/env python3
"""Bounded original current NFL injury, roster, and schedule snapshots."""
import argparse
import datetime as dt
import gzip
import hashlib
from html import unescape
from html.parser import HTMLParser
import io
import json
from pathlib import Path
import re
import sys
import tempfile
import time
import unittest
from unittest import mock
import urllib.error
import urllib.parse
import urllib.request
import uuid
import zipfile

UTC=dt.timezone.utc
UA='SportsEdgeLabResearch/1.3 (+https://github.com/alvaromendizabal/sports-edge-lab)'
HOST='www.nfl.com'
ORIGIN='https://'+HOST
BASE='tracks/nfl/raw/nfl-official-current/'
ACQ='shared/acquisition/nfl-official-current/'
SEEDS=[
 {'url':'https://www.nfl.com/injuries/league/2026/reg6','kind':'injuries','observed_by':'Official NFL current Week 6 injury page; public search and direct HTTP 200 on 2026-10-16'},
 {'url':'https://www.nfl.com/schedules/2026/by-week/week-6','kind':'schedule','observed_by':'Exact current-week URL from public official NFL search result on 2026-10-16'},
 {'url':'https://www.nfl.com/teams/','kind':'directory','observed_by':'Official NFL team directory public search result on 2026-10-16'}]

def utc(): return dt.datetime.now(UTC).isoformat(timespec='seconds').replace('+00:00','Z')
def pack(x): return json.dumps(x,sort_keys=True,separators=(',',':')).encode()
def sha(x): return hashlib.sha256(x).hexdigest()

def permitted_url(url,kind=None):
    p=urllib.parse.urlsplit(url)
    if p.scheme!='https' or p.netloc!=HOST or p.query or p.fragment: return False
    patterns={'robots':r'/robots\.txt','directory':r'/teams/',
              'profile':r'/teams/[a-z0-9-]+/','roster':r'/teams/[a-z0-9-]+/roster/?',
              'injuries':r'/injuries/league/2026/reg6',
              'schedule':r'/schedules/2026/by-week/week-6'}
    return any(re.fullmatch(v,p.path) for k,v in patterns.items() if kind is None or kind==k)

class Links(HTMLParser):
    def __init__(self,source):
        super().__init__();self.source=source;self.profiles=set();self.rosters=set()
    def handle_starttag(self,tag,attrs):
        if tag!='a': return
        for key,value in attrs:
            if key!='href' or not value: continue
            url=urllib.parse.urljoin(self.source,unescape(value))
            if permitted_url(url,'profile'): self.profiles.add(url)
            if permitted_url(url,'roster'): self.rosters.add(url)

def validate_html(raw,kind):
    text=raw.decode('utf-8',errors='replace')
    if len(raw)<100 or not re.search(r'<(?:!doctype|html)\b',text,re.I):
        raise ValueError('not_html')
    title=re.search(r'<title[^>]*>(.*?)</title>',text,re.I|re.S)
    title=unescape(re.sub('<[^>]+>',' ',title.group(1))).strip() if title else ''
    if re.search(r'access denied|verify you are human|request rejected|captcha',title,re.I):
        raise ValueError('source_challenge_document')
    needed={'injuries':('injur','2026'),'roster':('roster','2026'),
            'schedule':('schedule','2026'),'directory':('team',),'profile':('nfl',)}[kind]
    if not title or not all(x in title.lower() for x in needed):
        raise ValueError('html_title_scope_mismatch:'+title[:80])
    if kind in ('injuries','roster') and '<table' not in text.lower():
        raise ValueError('required_table_missing')
    return {'html_title':title,'table_count':len(re.findall(r'<table\b',text,re.I))}

class BoundedStop(Exception): pass
class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl): return None

class Fetcher:
    def __init__(self,max_calls,max_bytes,deadline):
        self.max_calls=max_calls;self.max_bytes=max_bytes;self.deadline=deadline
        self.calls=0;self.bytes=0;self.last=-1e12;self.robots=None;self.blocked=False
        self.opener=urllib.request.build_opener(NoRedirect)
    def raw(self,url,delay=1.,maximum=4*1024*1024):
        if not permitted_url(url): raise ValueError('source_not_allowlisted')
        if self.blocked: raise BoundedStop('source_access_suspended')
        pause=max(0.,self.last+max(1.,delay)-time.monotonic())
        if self.calls>=self.max_calls or self.bytes+maximum>self.max_bytes or time.monotonic()+pause+20>=self.deadline:
            raise BoundedStop('request_byte_or_runtime_bound')
        if pause: time.sleep(pause)
        self.last=time.monotonic();self.calls+=1
        try:
            with self.opener.open(urllib.request.Request(url,headers={'User-Agent':UA,'Accept':'text/html,text/plain'}),timeout=15) as r:
                raw=r.read(maximum);self.bytes+=len(raw)
                if len(raw)==maximum: raise ValueError('response_at_size_limit')
                return raw,{k.lower():v for k,v in r.headers.items()}
        except urllib.error.HTTPError as e:
            if e.code in (401,403,429): self.blocked=True
            e.close();raise
    def get(self,url,store,report):
        if self.robots is None:
            raw,headers=self.raw(ORIGIN+'/robots.txt',maximum=512*1024)
            policy=raw.decode('utf8',errors='replace');validate_robots(policy)
            self.robots=policy
            report['evidence'].append(store.archive(ORIGIN+'/robots.txt','robots',raw,headers,report['run_id'],report['capture_vintage']))
        allowed,delay=robots_policy(self.robots,url)
        if not allowed: raise BoundedStop('robots_disallowed:'+url)
        return self.raw(url,delay)

class Store:
    def __init__(self,bucket,region):
        import boto3
        from botocore.config import Config
        self.bucket=bucket
        self.s3=boto3.client('s3',region_name=region,config=Config(retries={'total_max_attempts':3,'mode':'adaptive'},connect_timeout=5,read_timeout=20))
    def get(self,key):
        try:
            with self.s3.get_object(Bucket=self.bucket,Key=key)['Body'] as body:return body.read()
        except self.s3.exceptions.NoSuchKey:return None
    def put(self,key,raw,content_type='application/json'):
        self.s3.upload_fileobj(io.BytesIO(raw),self.bucket,key,ExtraArgs={'ContentType':content_type,'ServerSideEncryption':'AES256'})
    def archive(self,url,kind,raw,headers,run_id,vintage,discovered_from=None):
        digest=sha(raw);is_data=kind in ('injuries','roster','schedule')
        key=(BASE+'objects/'+digest+'.html.gz') if is_data else (ACQ+'evidence/objects/'+digest+'.txt.gz')
        self.put(key,gzip.compress(raw,mtime=0),'application/gzip')
        return {'url':url,'kind':kind,'raw_key':key,'sha256':digest,'bytes':len(raw),'run_id':run_id,
                'captured_at':utc(),'capture_vintage':vintage,'source_last_modified':headers.get('last-modified'),
                'source_http_date':headers.get('date'),'source_etag':headers.get('etag'),
                'discovered_from':discovered_from,'historical_available_at':None,
                'point_in_time_approved':False,'status':'downloaded'}

def capture(store,fetcher,url,kind,report,discovered_from=None):
    if not permitted_url(url,kind):raise ValueError('source_or_kind_not_allowlisted')
    ident={'url':url,'kind':kind,'capture_vintage':report['capture_vintage']}
    index=BASE+'request-index/'+sha(pack(ident))+'.json'
    cached=store.get(index)
    if cached:
        receipt=json.loads(cached)
        if any(receipt.get(k)!=v for k,v in ident.items()):raise ValueError('cache_identity_mismatch')
        body=store.get(receipt['raw_key'])
        if body is None:raise ValueError('cached_body_missing')
        raw=gzip.decompress(body)
        if sha(raw)!=receipt['sha256']:raise ValueError('cached_body_hash_mismatch')
        validate_html(raw,kind)
        return raw,dict(receipt,status='reused')
    raw,headers=fetcher.get(url,store,report)
    markers=validate_html(raw,kind)
    receipt=store.archive(url,kind,raw,headers,report['run_id'],report['capture_vintage'],discovered_from)
    receipt.update(markers);store.put(index,pack(receipt))
    return raw,receipt

def run(args):
    start=time.monotonic();run_id=dt.datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:10]
    store=Store(args.bucket,args.region);fetch=Fetcher(args.max_requests,args.max_bytes,start+args.max_seconds-30)
    report={'run_id':run_id,'version':'sports-edge-lab-nfl-current-v027','started_at':utc(),'status':'running',
            'capture_vintage':dt.datetime.now(UTC).strftime('%Y-%m-%dT%H:00Z'),'captured':[],'evidence':[],
            'errors':[],'discovery':[],'bounds':{'seconds':args.max_seconds,'requests':args.max_requests,'bytes':args.max_bytes,'teams':32},
            'source_seeds':SEEDS,'point_in_time_approved':False,'historical_available_at':None,
            'scope':'Original current NFL Week 6 injuries, current-week schedule, and roster pages discovered through official team links.',
            'limitations':['Acquisition time is distinct from publication, injury-event, transaction or game time.',
                           'Raw HTML captured; player/game tables and dates require validated extraction.',
                           'No claim of complete historical injury/roster coverage or validated prediction-time features.',
                           'Current source pages can change within an hourly capture vintage.']}
    prefix=ACQ+run_id+'/';beat=start
    def heartbeat(force=False):
        nonlocal beat
        if force or time.monotonic()-beat>=20:
            beat=time.monotonic();report.update(requests=fetch.calls,source_bytes=fetch.bytes,elapsed_seconds=round(beat-start,2))
            store.put(prefix+'progress.json',pack(report))
            print(json.dumps({'timestamp':utc(),'event':'HEARTBEAT','run_id':run_id,'requests':fetch.calls,'bytes':fetch.bytes,
                              'data_pages':len(report['captured']),'rosters':sum(x['kind']=='roster' for x in report['captured']),
                              'teams_remaining':max(0,report.get('planned_teams',0)-report.get('processed_teams',0)),
                              'estimated_compute_usd':round((beat-start)*args.hourly_usd/3600,6)}),flush=True)
    def acquire(url,kind,source=None):
        raw,receipt=capture(store,fetch,url,kind,report,source)
        report['captured' if kind in ('injuries','roster','schedule') else 'evidence'].append(receipt)
        heartbeat();return raw,receipt
    try:
        heartbeat(True)
        directory=None
        for seed in SEEDS:
            try:
                raw,receipt=acquire(seed['url'],seed['kind'],seed['observed_by'])
                if seed['kind']=='directory':directory=(raw,receipt)
            except (urllib.error.URLError,TimeoutError,ValueError) as e:
                report['errors'].append({'url':seed['url'],'kind':seed['kind'],'error':type(e).__name__,'reason':str(e)[:180]})
                if fetch.blocked:raise BoundedStop('source_access_suspended')
        if directory is not None:
            p=Links(SEEDS[2]['url']);p.feed(directory[0].decode('utf8','replace'))
            teams=sorted(p.profiles)
            if not teams or len(teams)>32:raise ValueError('team_directory_count_outside_1_to_32')
            report.update(planned_teams=len(teams),processed_teams=0)
            for team in teams:
                try:
                    raw,receipt=acquire(team,'profile',{'url':SEEDS[2]['url'],'sha256':directory[1]['sha256']})
                    p=Links(team);p.feed(raw.decode('utf8','replace'))
                    rosters=sorted(x for x in p.rosters if urllib.parse.urlsplit(x).path.rstrip('/').rsplit('/',1)[0] == urllib.parse.urlsplit(team).path.rstrip('/'))
                    if len(rosters)!=1:raise ValueError('expected_one_observed_same_team_roster_link')
                    report['discovery'].append({'profile':team,'roster':rosters[0],'profile_sha256':receipt['sha256']})
                    acquire(rosters[0],'roster',{'url':team,'sha256':receipt['sha256']})
                except (urllib.error.URLError,TimeoutError,ValueError) as e:
                    report['errors'].append({'url':team,'kind':'team_roster','error':type(e).__name__,'reason':str(e)[:180]})
                    if fetch.blocked:raise BoundedStop('source_access_suspended')
                report['processed_teams']+=1;heartbeat()
        report['status']='discovered_scope_processed'
    except BoundedStop as e:report.update(status='bounded_stop',stop_reason=str(e))
    except Exception as e:
        report['status']='failed';report['errors'].append({'stage':'top_level','error':type(e).__name__,'reason':str(e)[:200]})
    report.update(finished_at=utc(),requests=fetch.calls,source_bytes=fetch.bytes,elapsed_seconds=round(time.monotonic()-start,2))
    report['downloaded_data_pages']=sum(x['status']=='downloaded' for x in report['captured'])
    report['reused_data_pages']=sum(x['status']=='reused' for x in report['captured'])
    report['roster_pages']=sum(x['kind']=='roster' for x in report['captured'])
    report['selected_scope_complete']=report['status']=='discovered_scope_processed' and not report['errors'] and report['roster_pages']==32 and {x['kind'] for x in report['captured']}=={'injuries','schedule','roster'}
    report['estimated_compute_usd']=round(report['elapsed_seconds']*args.hourly_usd/3600,6)
    report['cost_scope']='Application runtime only; excludes startup/shutdown, S3 storage and requests.'
    out=Path(args.output_dir);out.mkdir(parents=True,exist_ok=True);path=out/('sports_edge_lab_nfl_current_return_'+run_id+'.zip')
    with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
        z.writestr('report.json',pack(report));z.writestr('resume.json',pack({'bucket':args.bucket,'hourly_cache_reusable':True,'capture_vintage':report['capture_vintage']}))
    store.put(prefix+'report.json',pack(report));store.put(prefix+path.name,path.read_bytes(),'application/zip')
    print(json.dumps({'timestamp':utc(),'event':'FINISHED','run_id':run_id,'status':report['status'],
                      'data_pages':len(report['captured']),'rosters':report['roster_pages'],'report_key':prefix+'report.json','return_zip':str(path)}),flush=True)
    return 0 if report['status'] in ('discovered_scope_processed','bounded_stop') and not report['errors'] else 2

class Tests(unittest.TestCase):
    def test_only_exact_official_paths(self):
        for seed in SEEDS:self.assertTrue(permitted_url(seed['url'],seed['kind']))
        for u in ['https://amp.nfl.com/teams/','https://www.nfl.com:443/teams/','https://www.nfl.com/teams/?x=1','http://www.nfl.com/teams/','https://www.nfl.com/teams/#x']:
            self.assertFalse(permitted_url(u))
    def test_no_constructed_roster_urls(self):
        p=Links(ORIGIN+'/teams/a/');p.feed('<a href="/teams/a/">A</a><a href="/teams/a/stats">Stats</a>')
        self.assertEqual(p.rosters,set())
    def test_observed_links_only(self):
        p=Links(ORIGIN+'/teams/a/');p.feed('<a href="/teams/a/roster">Roster</a><a href="https://evil.test/teams/b/roster">Bad</a>')
        self.assertEqual(p.rosters,{ORIGIN+'/teams/a/roster'})
    def test_roster_html_scope_and_challenge(self):
        good=b'<html><head><title>Example 2026 Player Roster | NFL.com</title></head><body><table><tr><td>Example</td></tr></table></body></html>'
        self.assertEqual(validate_html(good,'roster')['table_count'],1)
        for bad in [good.replace(b'2026',b'2025'),good.replace(b'<table',b'<div'),good.replace(b'Example 2026 Player Roster | NFL.com',b'Access Denied')]:
            with self.assertRaises(ValueError):validate_html(bad,'roster')
    def test_robots_document_gate(self):
        validate_robots('User-agent: *\nDisallow: /admin/')
        with self.assertRaises(ValueError):validate_robots('<html><body>Challenge</body></html>')
    def test_robots_disallow_and_longer_delay(self):
        allowed,delay=robots_policy('User-agent: *\nDisallow: /teams/\nCrawl-delay: 5',ORIGIN+'/teams/')
        self.assertFalse(allowed);self.assertEqual(delay,5)
    def test_byte_bound_before_http(self):
        f=Fetcher(100,5,time.monotonic()+100)
        with self.assertRaises(BoundedStop):f.raw(ORIGIN+'/teams/')
        self.assertEqual(f.calls,0)
    def test_call_bound_before_http(self):
        f=Fetcher(0,50000000,time.monotonic()+100)
        with self.assertRaises(BoundedStop):f.raw(ORIGIN+'/teams/')
        self.assertEqual(f.calls,0)
    def test_source_403_stops_next_call(self):
        class Opener:
            calls=0
            def open(self,*a,**kw):
                self.calls+=1;raise urllib.error.HTTPError(ORIGIN+'/teams/',403,'Forbidden',{},None)
        f=Fetcher(100,50000000,time.monotonic()+100);f.opener=Opener()
        with self.assertRaises(urllib.error.HTTPError):f.raw(ORIGIN+'/teams/')
        with self.assertRaises(BoundedStop):f.raw(ORIGIN+'/teams/')
        self.assertEqual(f.opener.calls,1)
    def test_hourly_vintage_changes_identity(self):
        a={'url':SEEDS[0]['url'],'kind':'injuries','capture_vintage':'2026-10-16T19:00Z'}
        self.assertNotEqual(sha(pack(a)),sha(pack(dict(a,capture_vintage='2026-10-16T20:00Z'))))
    def test_cached_body_hash_failure(self):
        class Fake:
            def get(self,k):
                if '/request-index/' in k:return pack({'url':SEEDS[0]['url'],'kind':'injuries','capture_vintage':'v','raw_key':'body','sha256':'bad'})
                return gzip.compress(b'body')
        with self.assertRaisesRegex(ValueError,'cached_body_hash_mismatch'):
            capture(Fake(),None,SEEDS[0]['url'],'injuries',{'capture_vintage':'v'})
    def test_cache_identity_mismatch(self):
        class Fake:
            def get(self,k):return pack({'url':'wrong'})
        with self.assertRaisesRegex(ValueError,'cache_identity_mismatch'):
            capture(Fake(),None,SEEDS[0]['url'],'injuries',{'capture_vintage':'v'})
    def test_pacing_honors_policy_after_robots(self):
        class Response:
            headers={}
            def __enter__(self):return self
            def __exit__(self,*args):pass
            def read(self,*args):return b'ok'
        class Opener:
            def open(self,*a,**kw):return Response()
        f=Fetcher(100,50000000,1000);f.opener=Opener();f.last=10
        with mock.patch.object(time,'monotonic',return_value=12),mock.patch.object(time,'sleep') as pause:
            f.raw(ORIGIN+'/teams/',delay=5)
        pause.assert_called_once_with(3)
    def test_run_one_zip_and_same_vintage_resume(self):
        def html(title,content):return ('<html><head><title>'+title+'</title></head><body>'+content+'</body></html>').encode()
        profile=ORIGIN+'/teams/example/';roster=profile+'roster'
        fixtures={SEEDS[0]['url']:html('2026 NFL Injury Report','<table><tr><td>Report</td></tr></table>'),
                  SEEDS[1]['url']:html('2026 NFL Schedule','<p>Published current schedule snapshot.</p>'),
                  SEEDS[2]['url']:html('Official NFL Teams','<a href="/teams/example/">Team directory entry</a>'),
                  profile:html('Example | NFL.com','<a href="/teams/example/roster">Roster link</a>'),
                  roster:html('Example 2026 Player Roster | NFL.com','<table><tr><td>Roster</td></tr></table>')}
        class MemoryStore(Store):
            def __init__(self):self.data={}
            def get(self,key):return self.data.get(key)
            def put(self,key,raw,content_type='application/json'):self.data[key]=raw
        class FakeFetcher:
            def __init__(self,*args):self.calls=0;self.bytes=0;self.blocked=False
            def get(self,url,store,report):
                raw=fixtures[url];self.calls+=1;self.bytes+=len(raw);return raw,{}
        store=MemoryStore()
        with tempfile.TemporaryDirectory() as temp:
            args=argparse.Namespace(bucket='test',region='test',max_requests=120,max_bytes=50000000,max_seconds=600,hourly_usd=.461,output_dir=temp)
            with mock.patch.object(sys.modules[__name__],'Store',return_value=store),mock.patch.object(sys.modules[__name__],'Fetcher',FakeFetcher),mock.patch('builtins.print'):
                self.assertEqual(run(args),0)
                self.assertEqual(len(list(Path(temp).glob('*.zip'))),1)
                self.assertEqual(run(args),0)
            paths=list(Path(temp).glob('*.zip'));self.assertEqual(len(paths),2)
            reports=[json.loads(v) for k,v in store.data.items() if k.endswith('/report.json')]
            self.assertEqual(len(reports),2)
            self.assertEqual(sorted(r['downloaded_data_pages'] for r in reports),[0,3])
            self.assertEqual(sorted(r['requests'] for r in reports),[0,5])
            self.assertTrue(all(r['roster_pages']==1 and not r['selected_scope_complete'] for r in reports))
            with zipfile.ZipFile(paths[0]) as z:self.assertEqual(set(z.namelist()),{'report.json','resume.json'})

def main():
    p=argparse.ArgumentParser();p.add_argument('--bucket',default='sagemaker-sports-edge-lab-560403859723-us-west-2');p.add_argument('--region',default='us-west-2')
    p.add_argument('--max-seconds',type=int,default=600);p.add_argument('--max-requests',type=int,default=120);p.add_argument('--max-bytes',type=int,default=50000000)
    p.add_argument('--hourly-usd',type=float,default=.461);p.add_argument('--output-dir',default='/opt/ml/processing/output');p.add_argument('--self-test',action='store_true');a=p.parse_args()
    if not(90<=a.max_seconds<=600 and 1<=a.max_requests<=120 and 1000000<=a.max_bytes<=50000000):p.error('bounds exceed collector envelope')
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
    if not result.wasSuccessful():return 1
    print(json.dumps({'timestamp':utc(),'event':'SELF_TEST_PASSED','tests':result.testsRun}),flush=True)
    return 0 if a.self_test else run(a)

def robots_policy(text, url, agent=UA):
    """Longest-match robots rules, including wildcard/query and end anchors."""
    groups, agents, rules = [], [], []
    def finish():
        if agents:
            groups.append((agents[:], rules[:]))
    for line in text.splitlines():
        line = line.split('#', 1)[0].strip()
        if ':' not in line:
            continue
        key, value = [s.strip() for s in line.split(':', 1)]
        key = key.lower()
        if key == 'user-agent':
            if rules:
                finish(); agents, rules = [], []
            agents.append(value.lower())
        elif agents and key in ('allow', 'disallow', 'crawl-delay'):
            rules.append((key, value))
    finish()
    matches = [(max((len(a) for a in names if a != '*' and a in agent.lower()), default=0), rs)
               for names, rs in groups if '*' in names or any(a in agent.lower() for a in names)]
    longest = max((n for n, _ in matches), default=-1)
    selected = [r for n, rs in matches if n == longest for r in rs]
    p = urllib.parse.urlsplit(url)
    target = p.path + ('?' + p.query if p.query else '')
    decisions, delay = [], 1.0
    for kind, pattern in selected:
        if kind == 'crawl-delay':
            try: delay = max(delay, float(pattern))
            except ValueError: pass
        elif pattern:
            end = pattern.endswith('$')
            body = pattern[:-1] if end else pattern
            regex = '^' + re.escape(body).replace(r'\*', '.*') + ('$' if end else '')
            if re.search(regex, target):
                decisions.append((len(body.replace('*', '')), kind == 'allow'))
    return (max(decisions, default=(0, True))[1], delay)

def validate_robots(text):
    if re.search(r'<\s*(?:html|!doctype|body)\b', text, re.I) or not re.search(
            r'^\s*user-agent\s*:\s*\S+', text, re.I | re.M):
        raise ValueError('invalid_robots_document')


if __name__=='__main__':sys.exit(main())
