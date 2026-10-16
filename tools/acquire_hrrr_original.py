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
        # The verified CFBD /games request is a football season, not a calendar
        # year: January postseason belongs to the preceding fall season.
        if g.get('season') is not None and g.get('season') != season:
            skip('mismatched_season_metadata'); continue
        if not (dt.datetime(season, 7, 1, tzinfo=UTC) <= kickoff < min(now, dt.datetime(season+1, 7, 1, tzinfo=UTC))):
            skip('outside_requested_football_season'); continue
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
    # Zero explicitly selects the entire eligible cache without a row cap.
    if max_games:
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


def parse_index(raw, expected_run, expected_forecast_hour=None):
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
    seen = set()
    families = set()
    for i, row in enumerate(rows[:-1]):
        family = FIELDS.get((row['variable'], row['level']))
        if not family:
            continue
        description = row['forecast_description']
        if row['variable'] == 'APCP':
            interval = re.fullmatch(r'(\d+)-(\d+) hour acc fcst', description)
            if not interval:
                raise ValueError('precipitation_accumulation_interval_unrecognized')
            first, last = map(int, interval.groups())
            if first < 0 or first >= last:
                raise ValueError('invalid_precipitation_accumulation_interval')
            field = family + '_' + str(first) + '_' + str(last) + 'h'
            statistic = 'accumulation'
        else:
            lead = re.fullmatch(r'(\d+) hour fcst', description)
            if not lead:
                raise ValueError('instantaneous_forecast_interval_unrecognized')
            first = last = int(lead.group(1))
            field = family
            statistic = 'instantaneous'
        if expected_forecast_hour is not None and last != expected_forecast_hour:
            raise ValueError('field_forecast_hour_mismatch')
        if field in seen:
            raise ValueError('duplicate_forecast_field_interval')
        seen.add(field)
        families.add(family)
        initialization = parse_time(expected_run)
        chosen.append(dict(row, field=field, field_family=family,
                           statistic=statistic, forecast_hour_start=first, forecast_hour_end=last,
                           valid_start_utc=(initialization+dt.timedelta(hours=first)).isoformat(),
                           valid_end_utc=(initialization+dt.timedelta(hours=last)).isoformat(),
                           end=rows[i+1]['start']-1))
    if families != set(FIELDS.values()):
        raise ValueError('required_field_family_missing')
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
              'season_window':'July 1 inclusive through next July 1 exclusive; supplied season metadata must match',
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
                fields=parse_index(raw,pair['run_init_utc'],pair['forecast_hour'])
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


# Original NOAA index fixture, fetched 2026-10-16 from the public object
# hrrr.20241012/conus/hrrr.t14z.wrfsfcf10.grib2.idx.
REAL_NOAA_INDEX_FIXTURE = '1:0:d=2024101214:REFC:entire atmosphere:10 hour fcst:\n2:354671:d=2024101214:RETOP:cloud top:10 hour fcst:\n3:435156:d=2024101214:var discipline=0 center=7 local_table=1 parmcat=16 parm=201:entire atmosphere:10 hour fcst:\n4:815025:d=2024101214:VIL:entire atmosphere:10 hour fcst:\n5:1026371:d=2024101214:VIS:surface:10 hour fcst:\n6:2369637:d=2024101214:REFD:1000 m above ground:10 hour fcst:\n7:2517752:d=2024101214:REFD:4000 m above ground:10 hour fcst:\n8:2618381:d=2024101214:REFD:263 K level:10 hour fcst:\n9:2725862:d=2024101214:GUST:surface:10 hour fcst:\n10:3900744:d=2024101214:UGRD:250 mb:10 hour fcst:\n11:4646404:d=2024101214:VGRD:250 mb:10 hour fcst:\n12:5331836:d=2024101214:UGRD:300 mb:10 hour fcst:\n13:6075744:d=2024101214:VGRD:300 mb:10 hour fcst:\n14:6765296:d=2024101214:HGT:500 mb:10 hour fcst:\n15:7460754:d=2024101214:TMP:500 mb:10 hour fcst:\n16:8017852:d=2024101214:DPT:500 mb:10 hour fcst:\n17:9046389:d=2024101214:UGRD:500 mb:10 hour fcst:\n18:9639104:d=2024101214:VGRD:500 mb:10 hour fcst:\n19:10216045:d=2024101214:HGT:700 mb:10 hour fcst:\n20:10884329:d=2024101214:TMP:700 mb:10 hour fcst:\n21:11450041:d=2024101214:DPT:700 mb:10 hour fcst:\n22:12459691:d=2024101214:DZDT:700 mb:10 hour fcst:\n23:13364193:d=2024101214:UGRD:700 mb:10 hour fcst:\n24:13969820:d=2024101214:VGRD:700 mb:10 hour fcst:\n25:14567567:d=2024101214:HGT:850 mb:10 hour fcst:\n26:15258096:d=2024101214:TMP:850 mb:10 hour fcst:\n27:15833706:d=2024101214:DPT:850 mb:10 hour fcst:\n28:16974891:d=2024101214:UGRD:850 mb:10 hour fcst:\n29:17588703:d=2024101214:VGRD:850 mb:10 hour fcst:\n30:18187451:d=2024101214:TMP:925 mb:10 hour fcst:\n31:18770702:d=2024101214:DPT:925 mb:10 hour fcst:\n32:19918989:d=2024101214:UGRD:925 mb:10 hour fcst:\n33:20531248:d=2024101214:VGRD:925 mb:10 hour fcst:\n34:21130116:d=2024101214:TMP:1000 mb:10 hour fcst:\n35:21726636:d=2024101214:DPT:1000 mb:10 hour fcst:\n36:22883518:d=2024101214:UGRD:1000 mb:10 hour fcst:\n37:23507029:d=2024101214:VGRD:1000 mb:10 hour fcst:\n38:24105131:d=2024101214:MAXUVV:100-1000 mb above ground:9-10 hour max fcst:\n39:24891587:d=2024101214:MAXDVV:100-1000 mb above ground:9-10 hour max fcst:\n40:25615974:d=2024101214:DZDT:0.5-0.8 sigma layer:9-10 hour ave fcst:\n41:26271235:d=2024101214:MSLMA:mean sea level:10 hour fcst:\n42:26879222:d=2024101214:HGT:1000 mb:10 hour fcst:\n43:27552814:d=2024101214:MAXREF:1000 m above ground:9-10 hour max fcst:\n44:27745685:d=2024101214:REFD:263 K level:9-10 hour max fcst:\n45:27857479:d=2024101214:MXUPHL:5000-2000 m above ground:9-10 hour max fcst:\n46:27895488:d=2024101214:MNUPHL:5000-2000 m above ground:9-10 hour min fcst:\n47:27924044:d=2024101214:MXUPHL:2000-0 m above ground:9-10 hour max fcst:\n48:28226785:d=2024101214:MNUPHL:2000-0 m above ground:9-10 hour min fcst:\n49:28477265:d=2024101214:MXUPHL:3000-0 m above ground:9-10 hour max fcst:\n50:28564337:d=2024101214:MNUPHL:3000-0 m above ground:9-10 hour min fcst:\n51:28779384:d=2024101214:RELV:2000-0 m above ground:9-10 hour max fcst:\n52:31273316:d=2024101214:RELV:1000-0 m above ground:9-10 hour max fcst:\n53:34098788:d=2024101214:HAIL:entire atmosphere:9-10 hour max fcst:\n54:34203835:d=2024101214:HAIL:0.1 sigma level:9-10 hour max fcst:\n55:34220391:d=2024101214:HAIL:surface:9-10 hour max fcst:\n56:34221076:d=2024101214:TCOLG:entire atmosphere (considered as a single layer):9-10 hour max fcst:\n57:34235090:d=2024101214:LTNGSD:1 m above ground:10 hour fcst:\n58:34235438:d=2024101214:LTNGSD:2 m above ground:10 hour fcst:\n59:34265091:d=2024101214:LTNG:entire atmosphere:10 hour fcst:\n60:34274243:d=2024101214:UGRD:80 m above ground:10 hour fcst:\n61:35409395:d=2024101214:VGRD:80 m above ground:10 hour fcst:\n62:36511872:d=2024101214:PRES:surface:10 hour fcst:\n63:38004168:d=2024101214:HGT:surface:10 hour fcst:\n64:40157863:d=2024101214:TMP:surface:10 hour fcst:\n65:41408854:d=2024101214:ASNOW:surface:0-10 hour acc fcst:\n66:41451137:d=2024101214:MSTAV:0 m underground:10 hour fcst:\n67:42724921:d=2024101214:CNWAT:surface:10 hour fcst:\n68:42749790:d=2024101214:WEASD:surface:10 hour fcst:\n69:42754106:d=2024101214:SNOWC:surface:10 hour fcst:\n70:42758367:d=2024101214:SNOD:surface:10 hour fcst:\n71:42761633:d=2024101214:TMP:2 m above ground:10 hour fcst:\n72:43947861:d=2024101214:POT:2 m above ground:10 hour fcst:\n73:45020599:d=2024101214:SPFH:2 m above ground:10 hour fcst:\n74:46494307:d=2024101214:DPT:2 m above ground:10 hour fcst:\n75:47670001:d=2024101214:RH:2 m above ground:10 hour fcst:\n76:49147524:d=2024101214:MASSDEN:8 m above ground:10 hour fcst:\n77:49798358:d=2024101214:UGRD:10 m above ground:10 hour fcst:\n78:51941830:d=2024101214:VGRD:10 m above ground:10 hour fcst:\n79:54085302:d=2024101214:WIND:10 m above ground:9-10 hour max fcst:\n80:55232680:d=2024101214:MAXUW:10 m above ground:9-10 hour max fcst:\n81:56516214:d=2024101214:MAXVW:10 m above ground:9-10 hour max fcst:\n82:57753099:d=2024101214:CPOFP:surface:10 hour fcst:\n83:57799654:d=2024101214:PRATE:surface:10 hour fcst:\n84:57823680:d=2024101214:APCP:surface:0-10 hour acc fcst:\n85:58119893:d=2024101214:WEASD:surface:0-10 hour acc fcst:\n86:58153188:d=2024101214:FROZR:surface:0-10 hour acc fcst:\n87:58194612:d=2024101214:FRZR:surface:0-10 hour acc fcst:\n88:58205121:d=2024101214:SSRUN:surface:9-10 hour acc fcst:\n89:58207018:d=2024101214:BGRUN:surface:9-10 hour acc fcst:\n90:58207396:d=2024101214:APCP:surface:9-10 hour acc fcst:\n91:58334019:d=2024101214:WEASD:surface:9-10 hour acc fcst:\n92:58364163:d=2024101214:FROZR:surface:9-10 hour acc fcst:\n93:58387482:d=2024101214:CSNOW:surface:10 hour fcst:\n94:58391622:d=2024101214:CICEP:surface:10 hour fcst:\n95:58392021:d=2024101214:CFRZR:surface:10 hour fcst:\n96:58392957:d=2024101214:CRAIN:surface:10 hour fcst:\n97:58447199:d=2024101214:SFCR:surface:10 hour fcst:\n98:60345623:d=2024101214:FRICV:surface:10 hour fcst:\n99:61438648:d=2024101214:SHTFL:surface:10 hour fcst:\n100:62604639:d=2024101214:LHTFL:surface:10 hour fcst:\n101:63771410:d=2024101214:VEG:surface:10 hour fcst:\n102:65229023:d=2024101214:VEGMIN:surface:10 hour fcst:\n103:66345160:d=2024101214:VEGMAX:surface:10 hour fcst:\n104:67222094:d=2024101214:LAI:surface:10 hour fcst:\n105:68004558:d=2024101214:GFLUX:surface:10 hour fcst:\n106:68934968:d=2024101214:VGTYP:surface:10 hour fcst:\n107:69716147:d=2024101214:LFTX:500-1000 mb:10 hour fcst:\n108:70618776:d=2024101214:CAPE:surface:10 hour fcst:\n109:71016647:d=2024101214:CIN:surface:10 hour fcst:\n110:71581508:d=2024101214:PWAT:entire atmosphere (considered as a single layer):10 hour fcst:\n111:72502242:d=2024101214:AOTK:entire atmosphere (considered as a single layer):10 hour fcst:\n112:73235500:d=2024101214:COLMD:entire atmosphere (considered as a single layer):10 hour fcst:\n113:74160924:d=2024101214:TCOLW:entire atmosphere:10 hour fcst:\n114:75152767:d=2024101214:TCOLI:entire atmosphere:10 hour fcst:\n115:75988371:d=2024101214:TCDC:boundary layer cloud layer:10 hour fcst:\n116:76481064:d=2024101214:LCDC:low cloud layer:10 hour fcst:\n117:77024670:d=2024101214:MCDC:middle cloud layer:10 hour fcst:\n118:77251120:d=2024101214:HCDC:high cloud layer:10 hour fcst:\n119:77487007:d=2024101214:TCDC:entire atmosphere:10 hour fcst:\n120:78139432:d=2024101214:HGT:cloud ceiling:10 hour fcst:\n121:79228916:d=2024101214:HGT:cloud base:10 hour fcst:\n122:81176089:d=2024101214:PRES:cloud base:10 hour fcst:\n123:82069325:d=2024101214:PRES:cloud top:10 hour fcst:\n124:82626117:d=2024101214:HGT:cloud top:10 hour fcst:\n125:83601070:d=2024101214:ULWRF:top of atmosphere:10 hour fcst:\n126:85390539:d=2024101214:DSWRF:surface:10 hour fcst:\n127:86337343:d=2024101214:DLWRF:surface:10 hour fcst:\n128:88312086:d=2024101214:USWRF:surface:10 hour fcst:\n129:89074910:d=2024101214:ULWRF:surface:10 hour fcst:\n130:90703880:d=2024101214:CFNSF:surface:10 hour fcst:\n131:90712724:d=2024101214:VBDSF:surface:10 hour fcst:\n132:91538564:d=2024101214:VDDSF:surface:10 hour fcst:\n133:92471211:d=2024101214:USWRF:top of atmosphere:10 hour fcst:\n134:93480886:d=2024101214:HLCY:3000-0 m above ground:10 hour fcst:\n135:94634628:d=2024101214:HLCY:1000-0 m above ground:10 hour fcst:\n136:96498808:d=2024101214:USTM:0-6000 m above ground:10 hour fcst:\n137:97499922:d=2024101214:VSTM:0-6000 m above ground:10 hour fcst:\n138:98481887:d=2024101214:VUCSH:0-1000 m above ground:10 hour fcst:\n139:100863502:d=2024101214:VVCSH:0-1000 m above ground:10 hour fcst:\n140:103245117:d=2024101214:VUCSH:0-6000 m above ground:10 hour fcst:\n141:105864874:d=2024101214:VVCSH:0-6000 m above ground:10 hour fcst:\n142:108484631:d=2024101214:HGT:0C isotherm:10 hour fcst:\n143:110638388:d=2024101214:RH:0C isotherm:10 hour fcst:\n144:111310762:d=2024101214:PRES:0C isotherm:10 hour fcst:\n145:112004730:d=2024101214:HGT:highest tropospheric freezing level:10 hour fcst:\n146:112710380:d=2024101214:RH:highest tropospheric freezing level:10 hour fcst:\n147:113395695:d=2024101214:PRES:highest tropospheric freezing level:10 hour fcst:\n148:114079540:d=2024101214:HGT:263 K level:10 hour fcst:\n149:114758253:d=2024101214:HGT:253 K level:10 hour fcst:\n150:115389559:d=2024101214:4LFTX:180-0 mb above ground:10 hour fcst:\n151:116330982:d=2024101214:CAPE:180-0 mb above ground:10 hour fcst:\n152:116728284:d=2024101214:CIN:180-0 mb above ground:10 hour fcst:\n153:117272074:d=2024101214:HPBL:surface:10 hour fcst:\n154:120330972:d=2024101214:HGT:level of adiabatic condensation from sfc:10 hour fcst:\n155:123241070:d=2024101214:CAPE:90-0 mb above ground:10 hour fcst:\n156:123555051:d=2024101214:CIN:90-0 mb above ground:10 hour fcst:\n157:124042229:d=2024101214:CAPE:255-0 mb above ground:10 hour fcst:\n158:124457342:d=2024101214:CIN:255-0 mb above ground:10 hour fcst:\n159:125021499:d=2024101214:HGT:equilibrium level:10 hour fcst:\n160:127299311:d=2024101214:PLPL:255-0 mb above ground:10 hour fcst:\n161:128541325:d=2024101214:CAPE:0-3000 m above ground:10 hour fcst:\n162:129160321:d=2024101214:HGT:level of free convection:10 hour fcst:\n163:131865834:d=2024101214:EFHL:surface:10 hour fcst:\n164:132645819:d=2024101214:CANGLE:0-500 m above ground:10 hour fcst:\n165:134804009:d=2024101214:LAYTH:261 K level - 256 K level:10 hour fcst:\n166:135981738:d=2024101214:ESP:0-3000 m above ground:10 hour fcst:\n167:136590433:d=2024101214:RHPW:entire atmosphere:10 hour fcst:\n168:137709157:d=2024101214:LAND:surface:10 hour fcst:\n169:137759633:d=2024101214:ICEC:surface:10 hour fcst:\n170:137759866:d=2024101214:SBT123:top of atmosphere:10 hour fcst:\n171:139218633:d=2024101214:SBT124:top of atmosphere:10 hour fcst:\n172:140800483:d=2024101214:SBT113:top of atmosphere:10 hour fcst:\n173:142141282:d=2024101214:SBT114:top of atmosphere:10 hour fcst:\n'


class Tests(unittest.TestCase):
    def test_full_season_includes_january_postseason(self):
        g,v=self.fixture()
        g.update(season=2024,startDate='2025-01-10T19:30:00Z')
        plan,_,n=game_plan([g],[v],dt.datetime(2026,10,16,tzinfo=UTC),0,season=2024)
        self.assertEqual(n,1)
        self.assertEqual(plan[0]['games'][0]['kickoff_utc'],'2025-01-10T19:30:00+00:00')

    def test_full_season_rejects_prior_bowl_and_wrong_season(self):
        g,v=self.fixture()
        games=[dict(g,id=1,season=2024,startDate='2024-01-10T19:00:00Z'),
               dict(g,id=2,season=2025,startDate='2024-10-12T19:00:00Z')]
        plan,skipped,n=game_plan(games,[v],dt.datetime(2026,10,16,tzinfo=UTC),0,season=2024)
        self.assertEqual(n,0)
        self.assertEqual(skipped,{'outside_requested_football_season':1,'mismatched_season_metadata':1})

    def test_zero_game_cap_selects_every_eligible_game(self):
        g,v=self.fixture()
        games=[dict(g,id=i) for i in range(1201)]
        plan,_,n=game_plan(games,[v],dt.datetime(2026,10,16,tzinfo=UTC),0)
        self.assertEqual(n,1201)
        self.assertEqual(len(plan[0]['games']),1201)
        limited,_,count=game_plan(games,[v],dt.datetime(2026,10,16,tzinfo=UTC),400)
        self.assertEqual(count,400)

    def test_empty_date_selects_multiple_days(self):
        g,v=self.fixture()
        games=[g,dict(g,id=2,startDate='2026-10-11T19:30:00Z')]
        plan,_,n=game_plan(games,[v],dt.datetime(2026,10,16,tzinfo=UTC),0,game_date='')
        self.assertEqual(n,2)
        self.assertEqual(len(plan),2)
        plan,_,n=game_plan(games,[v],dt.datetime(2026,10,16,tzinfo=UTC),0,game_date='2026-10-10')
        self.assertEqual(n,1)

    def test_field_cache_identity_is_stable_across_runs(self):
        raw=b'GRIB'+b'\x00\x00\x00\x02'+(20).to_bytes(8,'big')+b'7777'
        url=BASE+'/hrrr.20241012/conus/hrrr.t14z.wrfsfcf10.grib2'
        ident={'url':url,'range_start':100,'range_end':119,'source_etag':'"same-etag"'}
        expected=PREFIX+'request-index/'+sha(pack(ident))+'.json'
        class FakeStore:
            calls=[]
            def get(self,key):
                self.calls.append(key)
                if key==expected:
                    return pack(dict(ident,raw_key='body',sha256=sha(raw),bytes=20,kind='grib2',run_id='old'))
                if key=='body': return raw
                raise AssertionError('unexpected cache identity')
        class NoFetch:
            def get(self,*args,**kwargs): raise AssertionError('captured source must not be fetched again')
        store=FakeStore()
        result,receipt=capture(store,NoFetch(),url,'grib2','new',100,119,'"same-etag"',1000)
        self.assertEqual(result,raw)
        self.assertEqual(receipt['run_id'],'old')
        self.assertEqual(receipt['status'],'reused')
        self.assertEqual(store.calls,[expected,'body'])

    def test_cached_field_corruption_stops_reuse(self):
        raw=b'GRIB'+b'\x00\x00\x00\x02'+(20).to_bytes(8,'big')+b'7777'
        class FakeStore:
            def get(self,key):
                return pack({'raw_key':'body','sha256':sha(raw),'bytes':20,'kind':'grib2'}) if 'request-index' in key else b'corrupted'
        with self.assertRaisesRegex(ValueError,'hrrr_cached_hash_mismatch'):
            capture(FakeStore(),None,BASE+'/x','grib2','new',0,19)

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
            description='9-10 hour acc fcst' if var=='APCP' else '10 hour fcst'
            lines.append(f'{i+1}:{i*100}:d=2026101010:{var}:{level}:{description}:')
        r=parse_index('\n'.join(lines).encode(),'2026-10-10T10:00:00+00:00')
        self.assertEqual(len(r),5); self.assertEqual(r[0]['end'],99)
        with self.assertRaises(ValueError): parse_index('\n'.join(lines).encode(),'2026-10-10T11:00:00+00:00')

    def test_real_noaa_duplicate_precipitation_intervals(self):
        raw=REAL_NOAA_INDEX_FIXTURE.encode('utf-8')
        records=parse_index(raw,'2024-10-12T14:00:00+00:00',10)
        self.assertEqual(len(records),6)
        rain=[r for r in records if r['variable']=='APCP']
        self.assertEqual([(r['forecast_hour_start'],r['forecast_hour_end']) for r in rain],[(0,10),(9,10)])
        self.assertEqual([r['start'] for r in rain],[57823680,58207396])
        self.assertEqual(len({r['field'] for r in rain}),2)
        self.assertTrue(all(r['statistic']=='accumulation' for r in rain))
        self.assertEqual(rain[0]['valid_start_utc'],'2024-10-12T14:00:00+00:00')
        self.assertEqual(rain[1]['valid_start_utc'],'2024-10-12T23:00:00+00:00')
        self.assertTrue(all(r['valid_end_utc']=='2024-10-13T00:00:00+00:00' for r in rain))

    def test_real_noaa_lead_and_duplicate_interval_gate(self):
        raw=REAL_NOAA_INDEX_FIXTURE.encode('utf-8')
        with self.assertRaises(ValueError): parse_index(raw,'2024-10-12T14:00:00+00:00',9)
        duplicate=REAL_NOAA_INDEX_FIXTURE.replace(':APCP:surface:9-10 hour acc fcst:',':APCP:surface:0-10 hour acc fcst:')
        with self.assertRaises(ValueError): parse_index(duplicate.encode(),'2024-10-12T14:00:00+00:00',10)

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
    p.add_argument('--full-season',action='store_true',help='Remove the pilot UTC date filter; combine with --max-games 0 for all eligible games')
    p.add_argument('--max-seconds',type=int,default=600)
    p.add_argument('--max-requests',type=int,default=500)
    p.add_argument('--max-bytes',type=int,default=250000000)
    p.add_argument('--max-games',type=int,default=400)
    p.add_argument('--hourly-usd',type=float,default=.461)
    p.add_argument('--output-dir',default='/opt/ml/processing/output')
    p.add_argument('--self-test',action='store_true')
    a=p.parse_args()
    if a.full_season:
        a.game_date=None
    if not 2014<=a.season<=2026 or (a.game_date and not re.fullmatch(r'\d{4}-\d{2}-\d{2}',a.game_date)):
        p.error('invalid season or UTC game date')
    if not (0<a.max_seconds<=6900 and 0<a.max_requests<=6000 and 0<a.max_bytes<=2000000000 and 0<=a.max_games<=20000):
        p.error('bounds exceed the authorized collector envelope')
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
    if not result.wasSuccessful(): return 1
    print(json.dumps({'timestamp':utc(),'event':'SELF_TEST_PASSED','tests':result.testsRun}),flush=True)
    return 0 if a.self_test else run(a)


if __name__=='__main__':
    sys.exit(main())
