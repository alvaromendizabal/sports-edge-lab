#!/usr/bin/env python3
"""Archive bounded original NOAA HRRR forecast fields using verified cached games.

No point extraction and no historical availability approval are performed here.
A run's initialization is not its public release time. A nine-hour selection
buffer is a heuristic; historical delivery timestamps remain unknown.
"""
import argparse
import datetime as dt
import gzip
import hashlib
import io
import json
from pathlib import Path
import re
import sys
import time
import unittest
import urllib.error
import urllib.parse
import urllib.request
import uuid
import xml.etree.ElementTree as ET
import zipfile

UTC = dt.timezone.utc
HOST = 'noaa-hrrr-bdp-pds.s3.amazonaws.com'
BASE = 'https://' + HOST
PREFIX = 'shared/raw/noaa-hrrr-original/'
UA = 'SportsEdgeLabResearch/1.0 (+https://github.com/alvaromendizabal/sports-edge-lab)'
FIELDS = {('TMP','2 m above ground'): 'temperature_2m',
          ('UGRD','10 m above ground'): 'u_wind_10m',
          ('VGRD','10 m above ground'): 'v_wind_10m',
          ('GUST','surface'): 'surface_gust',
          ('APCP','surface'): 'surface_accumulated_precipitation'}


def utc():
    return dt.datetime.now(UTC).isoformat(timespec='seconds').replace('+00:00', 'Z')


def pack(x):
    return json.dumps(x, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode()


def sha(x):
    return hashlib.sha256(x).hexdigest()


def parse_time(x):
    value = dt.datetime.fromisoformat(str(x).replace('Z', '+00:00'))
    if value.tzinfo is None:
        raise ValueError('timezone_missing')
    return value.astimezone(UTC)


def game_plan(games, venues, now, max_games, buffer_hours=9, season=2026, game_date=None):
    venue_map = {str(v.get('id')): v for v in venues if isinstance(v, dict)}
    selected, skipped = [], {}
    def skip(reason):
        skipped[reason] = skipped.get(reason, 0) + 1
    for g in games:
        if not isinstance(g, dict) or g.get('completed') is not True:
            skip('not_confirmed_completed'); continue
        if g.get('startTimeTBD') is not False:
            skip('start_time_not_confirmed'); continue
        try:
            kickoff = parse_time(g['startDate'])
            v = venue_map[str(g['venueId'])]
            lat, lon = float(v['latitude']), float(v['longitude'])
        except (KeyError, ValueError, TypeError):
            skip('invalid_time_or_venue'); continue
        if not (dt.datetime(season, 1, 1, tzinfo=UTC) <= kickoff < min(now, dt.datetime(season+1, 1, 1, tzinfo=UTC))):
            skip('outside_requested_year'); continue
        if game_date and kickoff.strftime('%Y-%m-%d') != game_date:
            skip('outside_requested_utc_date'); continue
        # Restrict to mainland US model domain, with explicit US country tag.
        if str(v.get('countryCode', '')).upper() not in ('US', 'USA') or not (24 <= lat <= 50 and -125 <= lon <= -66):
            skip('outside_us_conus'); continue
        # Unknown roofs are retained as candidates but never approved for use.
        if v.get('dome') is True:
            skip('known_dome'); continue
        run = (kickoff - dt.timedelta(hours=buffer_hours)).replace(minute=0, second=0, microsecond=0)
        valid = kickoff.replace(minute=0, second=0, microsecond=0)
        if valid < kickoff:
            valid += dt.timedelta(hours=1)
        lead = int((valid-run).total_seconds() // 3600)
        selected.append({'game_id': g.get('id'), 'home_team': g.get('homeTeam'),
                         'away_team': g.get('awayTeam'), 'kickoff_utc': kickoff.isoformat(),
                         'venue_id': g['venueId'], 'venue_name': v.get('name'),
                         'latitude': lat, 'longitude': lon, 'dome': v.get('dome'),
                         'run_init_utc': run.isoformat(), 'valid_hour_utc': valid.isoformat(),
                         'forecast_hour': lead,
                         'run_key': 'hrrr.' + run.strftime('%Y%m%d') + '/conus/hrrr.t' + run.strftime('%H') + 'z.wrfsfcf' + str(lead).zfill(2) + '.grib2',
                         'historical_available_at': None, 'point_in_time_approved': False,
                         'roof_verified_for_game': False})
    selected.sort(key=lambda x: (x['kickoff_utc'], str(x['game_id'])), reverse=True)
    selected = selected[:max_games]
    pairs = {}
    for game in selected:
        pairs.setdefault(game['run_key'], {'run_key': game['run_key'], 'run_init_utc': game['run_init_utc'],
                                         'valid_hour_utc': game['valid_hour_utc'], 'forecast_hour': game['forecast_hour'],
                                         'games': []})['games'].append(game)
    return list(pairs.values()), skipped, len(selected)


def parse_listing(raw):
    root = ET.fromstring(raw)
    ns = {'s': 'http://s3.amazonaws.com/doc/2006-03-01/'}
    if root.findtext('s:IsTruncated', namespaces=ns) != 'false':
        raise ValueError('public_listing_truncated')
    return {e.findtext('s:Key', namespaces=ns): {
                'size': int(e.findtext('s:Size', namespaces=ns)),
                'etag': e.findtext('s:ETag', namespaces=ns),
                'last_modified': e.findtext('s:LastModified', namespaces=ns)}
            for e in root.findall('s:Contents', ns)}


def parse_index(raw, expected_run):
    rows = []
    for line in raw.decode('utf-8').splitlines():
        p = line.split(':')
        if len(p) < 6 or not p[0].isdigit() or not p[1].isdigit():
            raise ValueError('invalid_grib_index')
        if p[2] != 'd=' + parse_time(expected_run).strftime('%Y%m%d%H'):
            raise ValueError('index_initialization_mismatch')
        rows.append({'record': int(p[0]), 'start': int(p[1]), 'variable': p[3],
                     'level': p[4], 'forecast_description': p[5], 'index_line': line})
    if not rows or rows[0]['start'] != 0 or any(a['start'] >= b['start'] for a,b in zip(rows, rows[1:])):
        raise ValueError('nonmonotonic_grib_offsets')
    chosen = []
    for i, row in enumerate(rows[:-1]):
        match = FIELDS.get((row['variable'], row['level']))
        if match:
            chosen.append(dict(row, field=match, end=rows[i+1]['start']-1))
    if set(x['field'] for x in chosen) != set(FIELDS.values()) or len(chosen) != len(FIELDS):
        raise ValueError('required_field_set_not_unique_or_missing')
    return chosen


def validate_grib(raw):
    if len(raw) < 20 or raw[:4] != b'GRIB' or raw[7] != 2 or raw[-4:] != b'7777':
        raise ValueError('invalid_grib2_framing')
    if int.from_bytes(raw[8:16], 'big') != len(raw):
        raise ValueError('grib2_message_length_mismatch')


def validate_range(status, headers, start, end, raw, source_size=None):
    if status != 206:
        raise ValueError('source_did_not_honor_range')
    match = re.fullmatch(r'bytes (\d+)-(\d+)/(\d+)', headers.get('content-range', ''))
    if not match or tuple(map(int, match.groups()[:2])) != (start,end) or int(match.group(3)) <= end:
        raise ValueError('content_range_mismatch')
    if source_size is not None and int(match.group(3)) != source_size:
        raise ValueError('source_object_length_mismatch')
    if len(raw) != end-start+1:
        raise ValueError('range_length_mismatch')
    validate_grib(raw)


class BoundedStop(Exception):
    pass


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class Fetcher:
    def __init__(self, calls, bytes_limit, deadline):
        self.limit, self.byte_limit, self.deadline = calls, bytes_limit, deadline
        self.calls, self.bytes, self.blocked, self.next_time = 0, 0, False, 0.
        self.opener = urllib.request.build_opener(NoRedirect)

    def get(self, url, start=None, end=None, etag=None, source_size=None):
        parsed = urllib.parse.urlsplit(url)
        if parsed.scheme != 'https' or parsed.netloc != HOST or parsed.fragment:
            raise ValueError('source_origin_outside_allowlist')
        if self.blocked:
            raise BoundedStop('source_access_suspended')
        if self.calls >= self.limit or time.monotonic()+20 >= self.deadline:
            raise BoundedStop('request_or_runtime_bound')
        ranged = start is not None
        maximum = (end-start+1) if ranged else 1024*1024
        if maximum > 20*1024*1024 or self.bytes+maximum > self.byte_limit:
            raise BoundedStop('source_byte_bound')
        delay = max(0., self.next_time-time.monotonic())
        if delay:
            time.sleep(delay)
        self.next_time = time.monotonic()+.5
        self.calls += 1
        headers = {'User-Agent': UA, 'Accept': 'application/octet-stream'}
        if ranged:
            headers['Range'] = f'bytes={start}-{end}'
            if etag:
                headers['If-Match'] = etag
        try:
            with self.opener.open(urllib.request.Request(url, headers=headers), timeout=15) as response:
                h = {k.lower(): v for k,v in response.headers.items()}
                if ranged and response.status != 206:
                    raise ValueError('source_did_not_honor_range')
                raw = response.read(maximum)
                self.bytes += len(raw)
                if ranged:
                    validate_range(response.status, h, start, end, raw, source_size)
                elif len(raw) == maximum:
                    raise ValueError('metadata_response_at_limit')
                return raw, h
        except urllib.error.HTTPError as e:
            code = e.code
            e.close()
            if code in (401,403,429):
                self.blocked = True
            raise


def cfbd_cache_identity(endpoint, params, capture_day):
    # Match acquire_paid_data.Archive.stats_capture exactly for CFBD:
    # stable completed-season requests have no daily vintage; references and
    # current/future seasons use the day the provider capture was requested.
    year = params.get('year', params.get('season'))
    current_season = dt.date.fromisoformat(capture_day).year
    vintage = capture_day if year is None or year >= current_season else ''
    return {'provider':'cfbd','track':'ncaaf','endpoint':endpoint,
            'params':dict(sorted(params.items())),'capture_vintage':vintage}


def cfbd_cache_key(endpoint, params, capture_day):
    return 'tracks/ncaaf/raw/cfbd/request-index/' + sha(pack(cfbd_cache_identity(endpoint, params, capture_day))) + '.json'


class Store:
    def __init__(self, bucket, region):
        import boto3
        from botocore.config import Config
        self.bucket = bucket
        self.s3 = boto3.client('s3', region_name=region, config=Config(
            retries={'total_max_attempts': 3, 'mode': 'adaptive'}, connect_timeout=5, read_timeout=20))

    def get(self, key):
        try:
            with self.s3.get_object(Bucket=self.bucket, Key=key)['Body'] as body:
                return body.read()
        except self.s3.exceptions.NoSuchKey:
            return None

    def put(self, key, raw, content_type='application/json'):
        self.s3.upload_fileobj(io.BytesIO(raw), self.bucket, key, ExtraArgs={
            'ContentType': content_type, 'ServerSideEncryption': 'AES256'})

    def cached_cfbd(self, endpoint, params, vintage):
        desc = cfbd_cache_identity(endpoint, params, vintage)
        key = cfbd_cache_key(endpoint, params, vintage)
        idx = self.get(key)
        if idx is None:
            raise ValueError('missing_existing_cfbd_cache:' + endpoint)
        receipt = json.loads(idx)
        if receipt.get('status') != 200 or receipt.get('request') != desc:
            raise ValueError('existing_cfbd_receipt_descriptor_mismatch')
        body = self.get(receipt['raw_key'])
        if body is None:
            raise ValueError('existing_cfbd_body_missing')
        raw = gzip.decompress(body)
        if sha(raw) != receipt['sha256']:
            raise ValueError('existing_cfbd_body_hash_mismatch')
        data = json.loads(raw)
        if not isinstance(data, list):
            raise ValueError('existing_cfbd_schema_not_list')
        return data, {'request_index': key, 'raw_key':receipt['raw_key'], 'sha256':receipt['sha256']}


def capture(store, fetcher, url, kind, run_id, start=None, end=None, etag=None, source_size=None):
    ident = {'url':url,'range_start':start,'range_end':end,'source_etag':etag}
    index = PREFIX + 'request-index/' + sha(pack(ident)) + '.json'
    cached = store.get(index)
    if cached:
        receipt = json.loads(cached)
        body = store.get(receipt['raw_key'])
        if body is None:
            raise ValueError('hrrr_cached_body_missing')
        raw = gzip.decompress(body) if kind != 'grib2' else body
        if sha(raw) != receipt['sha256']:
            raise ValueError('hrrr_cached_hash_mismatch')
        if kind == 'grib2':
            validate_grib(raw)
        return raw, dict(receipt, status='reused')
    raw, headers = fetcher.get(url,start,end,etag,source_size)
    digest = sha(raw)
    suffix = '.grib2' if kind == 'grib2' else '.'+kind+'.gz'
    key = PREFIX + 'objects/' + digest + suffix
    receipt = dict(ident, source='NOAA HRRR operational archive', kind=kind,
                   retrieved_at=utc(), raw_key=key, sha256=digest, bytes=len(raw),
                   source_last_modified=headers.get('last-modified'),
                   response_etag=headers.get('etag'), content_range=headers.get('content-range'),
                   historical_available_at=None, point_in_time_approved=False,
                   run_id=run_id, status='downloaded')
    store.put(key,raw if kind=='grib2' else gzip.compress(raw,mtime=0),
              'application/octet-stream' if kind=='grib2' else 'application/gzip')
    store.put(index,pack(receipt))
    return raw,receipt


def run(args):
    started = time.monotonic()
    run_id = dt.datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:10]
    store = Store(args.bucket,args.region)
    fetcher = Fetcher(args.max_requests,args.max_bytes,started+args.max_seconds-35)
    prefix = 'shared/acquisition/noaa-hrrr-original/'+run_id+'/'
    report = {'run_id':run_id,'started_at':utc(),'status':'running','receipts':[],
              'forecasts':[],'errors':[],'historical_available_at':None,'point_in_time_approved':False,
              'scope':'Original CONUS surface GRIB fields for cached completed NCAAF games; no point extraction.',
              'requested_season':args.season,'requested_utc_game_date':args.game_date,
              'selection_buffer_hours':9,'selection_buffer_is_not_release_evidence':True,
              'bounds':{'bytes':args.max_bytes,'requests':args.max_requests,'seconds':args.max_seconds,'games':args.max_games},
              'source_documentation':'https://registry.opendata.aws/noaa-hrrr-pds/',
              'limitations':['Initialization is not publication time; source archive Last-Modified is not historical release proof.',
                             'Nine-hour pregame initialization buffer is a selection heuristic, not PIT approval.',
                             'One valid hour at/after kickoff; later work must extract venue points and validate model/domain/roof.',
                             'Full CONUS fields are shared among games; field-file counts are not unique game counts.']}
    beat=started
    def heartbeat(force=False):
        nonlocal beat
        if force or time.monotonic()-beat>=20:
            beat=time.monotonic()
            report.update(requests=fetcher.calls,source_bytes=fetcher.bytes,elapsed_seconds=round(beat-started,2))
            store.put(prefix+'progress.json',pack(report))
            print(json.dumps({'timestamp':utc(),'event':'HEARTBEAT','run_id':run_id,'requests':fetcher.calls,
                              'source_bytes':fetcher.bytes,'captures':len(report['receipts']),
                              'forecast_pairs_processed':len(report['forecasts']),
                              'forecast_pairs_remaining':max(0,report.get('planned_forecast_pairs',0)-len(report['forecasts'])),
                              'estimated_compute_usd':round((beat-started)*args.hourly_usd/3600,6)}),flush=True)
    try:
        games,report['games_input']=store.cached_cfbd('/games',{'year':args.season,'seasonType':'both'},args.cfbd_vintage)
        venues,report['venues_input']=store.cached_cfbd('/venues',{},args.cfbd_vintage)
        plan,report['skipped_games'],report['selected_games']=game_plan(games,venues,dt.datetime.now(UTC),args.max_games,season=args.season,game_date=args.game_date)
        report['planned_forecast_pairs']=len(plan)
        store.put(prefix+'plan.json',pack(plan))
        if not plan:
            raise ValueError('no_eligible_completed_games')
        heartbeat(True)
        listing_cache={}
        for pair in plan:
            entry=dict(pair,status='pending',fields=[])
            try:
                # Enumerate actual original public S3 objects; no alternate origin.
                key=pair['run_key']
                listing_prefix=key.rsplit('f',1)[0]+'f'
                if listing_prefix not in listing_cache:
                    url=BASE+'/?'+urllib.parse.urlencode({'list-type':'2','prefix':listing_prefix,'max-keys':1000})
                    raw,receipt=capture(store,fetcher,url,'xml',run_id)
                    report['receipts'].append(receipt)
                    listing_cache[listing_prefix]=parse_listing(raw)
                listing=listing_cache[listing_prefix]
                if key not in listing or key+'.idx' not in listing:
                    raise ValueError('requested_forecast_not_listed_by_source')
                raw,receipt=capture(store,fetcher,BASE+'/'+key+'.idx','idx',run_id,etag=listing[key+'.idx']['etag'])
                report['receipts'].append(receipt)
                entry['index_raw_key']=receipt['raw_key']
                fields=parse_index(raw,pair['run_init_utc'])
                entry['original_object_metadata']=listing[key]
                for field in fields:
                    if field['end']>=listing[key]['size']:
                        raise ValueError('range_outside_source_object')
                    raw,receipt=capture(store,fetcher,BASE+'/'+key,'grib2',run_id,field['start'],field['end'],listing[key]['etag'],listing[key]['size'])
                    report['receipts'].append(receipt)
                    entry['fields'].append(dict(field,raw_key=receipt['raw_key'],sha256=receipt['sha256'],bytes=receipt['bytes']))
                    heartbeat()
                entry['status']='captured'
            except BoundedStop as exc:
                entry.update(status='bounded_stop',reason=str(exc))
                report['forecasts'].append(entry)
                report['status']='bounded_stop'
                break
            except (urllib.error.URLError,TimeoutError,ValueError,ET.ParseError) as exc:
                entry.update(status='failed',reason=type(exc).__name__+':'+str(exc)[:120])
                report['errors'].append({'run_key':pair['run_key'],'reason':entry['reason']})
            report['forecasts'].append(entry)
            heartbeat()
        if report['status']=='running':
            report['status']='planned_scope_processed'
    except Exception as exc:
        report['status']='failed'
        report['errors'].append({'stage':'top_level','reason':type(exc).__name__+':'+str(exc)[:200]})
    report.update(finished_at=utc(),requests=fetcher.calls,source_bytes=fetcher.bytes,
                  elapsed_seconds=round(time.monotonic()-started,2))
    report['estimated_compute_usd']=round(report['elapsed_seconds']*args.hourly_usd/3600,6)
    report['cost_scope']='Runtime only; boot/shutdown, S3 storage, requests and data transfer additional.'
    report['downloaded']=sum(r['status']=='downloaded' for r in report['receipts'])
    report['reused']=sum(r['status']=='reused' for r in report['receipts'])
    report['grib_fields_downloaded']=sum(r['status']=='downloaded' and r['kind']=='grib2' for r in report['receipts'])
    report['complete_forecast_pairs']=sum(f['status']=='captured' for f in report['forecasts'])
    report['selected_scope_complete']=report['complete_forecast_pairs']==report.get('planned_forecast_pairs',-1) and not report['errors']
    output=Path(args.output_dir); output.mkdir(parents=True,exist_ok=True)
    path=output/('sports_edge_lab_hrrr_return_'+run_id+'.zip')
    with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
        z.writestr('report.json',pack(report))
        z.writestr('resume.json',pack({'bucket':args.bucket,'cfbd_vintage':args.cfbd_vintage,'season':args.season,'game_date':args.game_date,'request_indexes_reusable':True,
                                    'plan_key':prefix+'plan.json','point_in_time_approved':False}))
    store.put(prefix+'report.json',pack(report))
    store.put(prefix+path.name,path.read_bytes(),'application/zip')
    print(json.dumps({'timestamp':utc(),'event':'FINISHED','run_id':run_id,'status':report['status'],
                      'downloaded':report['downloaded'],'grib_fields_downloaded':report['grib_fields_downloaded'],
                      'complete_forecast_pairs':report['complete_forecast_pairs'],'source_bytes':fetcher.bytes,
                      'report_key':prefix+'report.json','return_zip':str(path)}),flush=True)
    # Hitting an explicit scope/cost bound is a successful resumable execution.
    return 0 if report['status'] in ('planned_scope_processed','bounded_stop') and not report['errors'] else 2


class Tests(unittest.TestCase):
    def test_historical_cfbd_cache_exact_observed_key(self):
        key=cfbd_cache_key('/games',{'year':2024,'seasonType':'both'},'2026-10-16')
        self.assertEqual(key,'tracks/ncaaf/raw/cfbd/request-index/8cf8578b55c87a3d8859b5e11dccd2e92f0646d2e05615ab64ed32b7cc8b8af2.json')
        self.assertEqual(cfbd_cache_identity('/games',{'year':2024,'seasonType':'both'},'2026-10-16')['capture_vintage'],'')

    def test_cfbd_reference_and_current_season_vintage(self):
        self.assertEqual(cfbd_cache_key('/venues',{},'2026-10-16'),'tracks/ncaaf/raw/cfbd/request-index/00eeb9dc08141ee23fe43845dbb8f37f275dadb485e4f7a6b501b228609847c2.json')
        self.assertEqual(cfbd_cache_identity('/games',{'year':2026,'seasonType':'both'},'2026-10-16')['capture_vintage'],'2026-10-16')
        self.assertEqual(cfbd_cache_identity('/venues',{},'2026-10-16')['capture_vintage'],'2026-10-16')

    def fixture(self):
        v={'id':1,'countryCode':'US','latitude':40,'longitude':-85,'dome':False,'name':'test'}
        g={'id':1,'completed':True,'startTimeTBD':False,'startDate':'2026-10-10T19:30:00Z','venueId':1}
        return g,v

    def test_buffer_and_valid_time(self):
        g,v=self.fixture(); plan,_,n=game_plan([g],[v],dt.datetime(2026,10,16,tzinfo=UTC),10)
        self.assertEqual(n,1); self.assertEqual(plan[0]['forecast_hour'],10)
        self.assertEqual(plan[0]['run_init_utc'],'2026-10-10T10:00:00+00:00')
        self.assertFalse(plan[0]['games'][0]['point_in_time_approved'])

    def test_duplicate_forecast_reuses_fields(self):
        g,v=self.fixture(); plan,_,n=game_plan([g,dict(g,id=2)],[v],dt.datetime(2026,10,16,tzinfo=UTC),10)
        self.assertEqual(len(plan),1); self.assertEqual(n,2)

    def test_bad_game_and_venue_excluded(self):
        g,v=self.fixture()
        for bad in (dict(g,completed=False),dict(g,startTimeTBD=True),dict(g,venueId=2),dict(g,startDate='2026-10-10T19:00:00')):
            self.assertFalse(game_plan([bad],[v],dt.datetime(2026,10,16,tzinfo=UTC),10)[0])
        for bad in (dict(v,dome=True),dict(v,countryCode='CA'),dict(v,longitude=0)):
            self.assertFalse(game_plan([g],[bad],dt.datetime(2026,10,16,tzinfo=UTC),10)[0])

    def test_index_fields_and_ranges(self):
        lines=[]
        for i,(var,level) in enumerate(list(FIELDS)+[('END','surface')]):
            lines.append(f'{i+1}:{i*100}:d=2026101010:{var}:{level}:10 hour fcst:')
        r=parse_index('\n'.join(lines).encode(),'2026-10-10T10:00:00+00:00')
        self.assertEqual(len(r),5); self.assertEqual(r[0]['end'],99)
        with self.assertRaises(ValueError): parse_index('\n'.join(lines).encode(),'2026-10-10T11:00:00+00:00')

    def test_listing_truncation(self):
        with self.assertRaises(ValueError): parse_listing(b'<ListBucketResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/"><IsTruncated>true</IsTruncated></ListBucketResult>')

    def test_grib_and_range_validation(self):
        raw=b'GRIB'+b'\x00\x00\x00\x02'+(20).to_bytes(8,'big')+b'7777'
        validate_range(206,{'content-range':'bytes 100-119/1000'},100,119,raw)
        for status,h in ((200,{'content-range':'bytes 100-119/1000'}),(206,{'content-range':'bytes 101-120/1000'})):
            with self.assertRaises(ValueError): validate_range(status,h,100,119,raw)
        for content_range in ('bytes 100-119/nonsense','bytes 100-119/1000 junk','bytes 100-119/119'):
            with self.assertRaises(ValueError): validate_range(206,{'content-range':content_range},100,119,raw)
        with self.assertRaises(ValueError): validate_range(206,{'content-range':'bytes 100-119/1000'},100,119,raw,1001)
        with self.assertRaises(ValueError): validate_grib(raw[:-1]+b'0')
        with self.assertRaises(ValueError): validate_grib(raw+b'0')

    def test_bound_before_network(self):
        f=Fetcher(500,10,time.monotonic()+100)
        with self.assertRaises(BoundedStop): f.get(BASE+'/x',0,19)
        self.assertEqual(f.calls,0)

    def test_source_suspension_before_network(self):
        f=Fetcher(500,1000000,time.monotonic()+100);f.blocked=True
        with self.assertRaises(BoundedStop): f.get(BASE+'/x')
        with self.assertRaises(ValueError): f.get('https://example.com/x')

    def test_ignored_range_never_reads_body(self):
        class Response:
            status=200
            headers={}
            read_called=False
            closed=False
            def __enter__(self): return self
            def __exit__(self,*args): self.closed=True
            def read(self,*args): self.read_called=True; raise AssertionError('must not read full object')
        response=Response()
        class Opener:
            def open(self,*args,**kwargs): return response
        f=Fetcher(500,250000000,time.monotonic()+100);f.opener=Opener()
        with self.assertRaises(ValueError): f.get(BASE+'/x',0,19)
        self.assertFalse(response.read_called);self.assertTrue(response.closed)
        self.assertEqual(f.bytes,0)

    def test_actual_403_blocks_next_network_call(self):
        class Opener:
            calls=0
            def open(self,*args,**kwargs):
                self.calls+=1
                raise urllib.error.HTTPError(BASE+'/x',403,'Forbidden',{},None)
        f=Fetcher(500,250000000,time.monotonic()+100);opener=Opener();f.opener=opener
        with self.assertRaises(urllib.error.HTTPError): f.get(BASE+'/x')
        with self.assertRaises(BoundedStop): f.get(BASE+'/y')
        self.assertEqual(opener.calls,1);self.assertTrue(f.blocked)

    def test_cache_reuse_hash_gate(self):
        raw=b'GRIB'+b'\x00\x00\x00\x02'+(20).to_bytes(8,'big')+b'7777'
        class Fake:
            def get(self,key):
                return pack({'raw_key':'body','sha256':sha(raw),'bytes':20,'kind':'grib2'}) if 'request-index' in key else raw
        result,receipt=capture(Fake(),None,BASE+'/x','grib2','test',0,19)
        self.assertEqual(result,raw); self.assertEqual(receipt['status'],'reused')


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--bucket',default='sagemaker-sports-edge-lab-560403859723-us-west-2')
    p.add_argument('--region',default='us-west-2')
    p.add_argument('--cfbd-vintage',default='2026-10-16')
    p.add_argument('--season',type=int,default=2024)
    p.add_argument('--game-date',default='2024-10-12')
    p.add_argument('--max-seconds',type=int,default=600)
    p.add_argument('--max-requests',type=int,default=500)
    p.add_argument('--max-bytes',type=int,default=250000000)
    p.add_argument('--max-games',type=int,default=400)
    p.add_argument('--hourly-usd',type=float,default=.461)
    p.add_argument('--output-dir',default='/opt/ml/processing/output')
    p.add_argument('--self-test',action='store_true')
    a=p.parse_args()
    if not 2014<=a.season<=2026 or (a.game_date and not re.fullmatch(r'\d{4}-\d{2}-\d{2}',a.game_date)):
        p.error('invalid season or UTC game date')
    if not (0<a.max_seconds<=600 and 0<a.max_requests<=500 and 0<a.max_bytes<=250000000 and 0<a.max_games<=1000):
        p.error('bounds exceed the authorized collector envelope')
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
    if not result.wasSuccessful(): return 1
    print(json.dumps({'timestamp':utc(),'event':'SELF_TEST_PASSED','tests':result.testsRun}),flush=True)
    return 0 if a.self_test else run(a)


if __name__=='__main__':
    sys.exit(main())
