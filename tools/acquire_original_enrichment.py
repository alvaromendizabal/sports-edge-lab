#!/usr/bin/env python3
"""Bounded Sports Edge Lab original NWS snapshots and discovered NBA reports.

No paid API calls, ESPN requests, historical URL guessing, or access bypasses.
Venue coordinates are read from the existing CFBD S3 cache. Current forecasts
are prospective observations, never evidence of past forecast availability.
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
import urllib.robotparser
import uuid
import zipfile

UTC = dt.timezone.utc
UA = 'SportsEdgeLabResearch/1.1 (+https://github.com/alvaromendizabal/sports-edge-lab)'
NBA_SEEDS = [
    'https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-03-04_04_45AM.pdf',
]
SEED_DISCOVERY = 'https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-03-04_04_45AM.pdf (public search result, verified PDF on 2026-10-16)'


def utc():
    return dt.datetime.now(UTC).isoformat(timespec='seconds').replace('+00:00', 'Z')


def pack(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def cache_identity(endpoint, params, vintage):
    desc = {'provider': 'cfbd', 'track': 'ncaaf', 'endpoint': endpoint,
            'params': dict(sorted(params.items())), 'capture_vintage': vintage}
    return 'tracks/ncaaf/raw/cfbd/request-index/' + sha(pack(desc)) + '.json'


def valid_url(url, kind):
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme != 'https' or parsed.username or parsed.password or parsed.port or parsed.fragment:
        return False
    if kind == 'nws':
        return parsed.hostname == 'api.weather.gov' and not parsed.query and (
            parsed.path.startswith('/points/') or parsed.path.startswith('/gridpoints/'))
    if kind == 'pdf':
        return parsed.hostname == 'ak-static.cms.nba.com' and not parsed.query and bool(
            re.fullmatch(r'/referee/injury/Injury-Report_\d{4}-\d{2}-\d{2}_\d{2}_\d{2}[AP]M\.pdf', parsed.path))
    return False


def venues_from(rows):
    """Only documented venue coordinates; no geocoder or synthetic coordinates."""
    selected, seen = [], set()
    for row in rows if isinstance(rows, list) else []:
        if not isinstance(row, dict) or row.get('dome') is True:
            continue
        if str(row.get('countryCode', row.get('country_code', ''))).upper() not in ('US', 'USA'):
            continue
        try:
            lat, lon = float(row['latitude']), float(row['longitude'])
        except (KeyError, TypeError, ValueError):
            continue
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            continue
        point = (round(lat, 4), round(lon, 4))
        if point in seen:
            continue
        seen.add(point)
        selected.append({'id': row.get('id'), 'name': row.get('name'), 'latitude': point[0],
                         'longitude': point[1], 'dome': row.get('dome'),
                         'source': 'cached_cfbd_venues', 'roof_status_verified_for_game': False})
    return sorted(selected, key=lambda v: str(v.get('id', '')))


def prioritize(venues, games):
    now = dt.datetime.now(UTC)
    upcoming = {}
    for game in games if isinstance(games, list) else []:
        try:
            when = dt.datetime.fromisoformat(game['startDate'].replace('Z', '+00:00'))
            if now <= when <= now + dt.timedelta(days=14):
                vid = str(game['venueId'])
                upcoming[vid] = min(upcoming.get(vid, when), when)
        except (KeyError, TypeError, ValueError):
            continue
    return sorted(venues, key=lambda v: (str(v['id']) not in upcoming,
                  upcoming.get(str(v['id']), now + dt.timedelta(days=100)), str(v['id']))), len(upcoming)


class BoundedStop(Exception):
    pass


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class Fetcher:
    def __init__(self, max_requests, deadline):
        self.limit, self.deadline = max_requests, deadline
        self.calls, self.next_call, self.blocked = 0, 0., set()
        self.opener = urllib.request.build_opener(NoRedirect)

    def get(self, url, accept='application/geo+json'):
        host = urllib.parse.urlsplit(url).hostname
        if host in self.blocked:
            raise BoundedStop('source_suspended:' + host)
        if self.calls >= self.limit or time.monotonic() + 15 >= self.deadline:
            raise BoundedStop('request_or_runtime_bound')
        delay = max(0., self.next_call - time.monotonic())
        if delay:
            time.sleep(delay)
        self.calls += 1
        self.next_call = time.monotonic() + .5
        request = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept': accept})
        try:
            with self.opener.open(request, timeout=12) as response:
                raw = response.read(8 * 1024 * 1024 + 1)
                if len(raw) > 8 * 1024 * 1024:
                    raise ValueError('response_exceeds_8MiB')
                return raw, {k.lower(): v for k, v in response.headers.items()}
        except urllib.error.HTTPError as exc:
            status = exc.code
            exc.close()
            if status in (401, 403, 429):
                self.blocked.add(host)
            raise


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
        key = cache_identity(endpoint, params, vintage)
        raw = self.get(key)
        if raw is None:
            return None, {'request_index': key, 'status': 'missing'}
        receipt = json.loads(raw)
        payload = self.get(receipt['raw_key'])
        if payload is None:
            raise ValueError('cached_raw_missing')
        unpacked = gzip.decompress(payload)
        if sha(unpacked) != receipt['sha256']:
            raise ValueError('cached_raw_hash_mismatch')
        return json.loads(unpacked), {'request_index': key, 'raw_key': receipt['raw_key'],
                                     'sha256': receipt['sha256'], 'status': 'verified_reused'}


def validate_payload(raw, kind):
    if kind == 'pdf':
        if not raw.startswith(b'%PDF-') or b'%%EOF' not in raw[-4096:]:
            raise ValueError('invalid_pdf_framing')
        return None
    value = json.loads(raw)
    if not isinstance(value, dict) or not isinstance(value.get('properties'), dict):
        raise ValueError('invalid_nws_geojson')
    return value


def capture(store, fetcher, url, kind, vintage, run_id):
    if not valid_url(url, kind):
        raise ValueError('source_url_outside_allowlist')
    source = 'nws' if kind == 'nws' else 'nba-official-injuries'
    base = 'shared/raw/nws/' if kind == 'nws' else 'tracks/nba/raw/nba-official-injuries/'
    idx = base + 'request-index/' + sha(pack({'url': url, 'vintage': vintage})) + '.json'
    cached = store.get(idx)
    if cached:
        receipt = json.loads(cached)
        archived = store.get(receipt['raw_key'])
        if archived is None:
            raise ValueError('archive_missing')
        raw = gzip.decompress(archived)
        if sha(raw) != receipt['sha256']:
            raise ValueError('archive_hash_mismatch')
        return validate_payload(raw, kind), {**receipt, 'status': 'reused'}
    raw, headers = fetcher.get(url, 'application/pdf' if kind == 'pdf' else 'application/geo+json')
    data = validate_payload(raw, kind)
    digest = sha(raw)
    raw_key = base + 'objects/' + digest + ('.pdf.gz' if kind == 'pdf' else '.json.gz')
    retrieved = utc()
    receipt = {'url': url, 'source': source, 'capture_vintage': vintage, 'run_id': run_id,
               'raw_key': raw_key, 'sha256': digest, 'bytes': len(raw), 'retrieved_at': retrieved,
               'upstream_last_modified': headers.get('last-modified'),
               'upstream_http_date': headers.get('date'), 'historical_available_at': None,
               'status': 'downloaded'}
    if kind == 'nws':
        props = data['properties']
        receipt['forecast_generated_at'] = props.get('generatedAt')
        receipt['forecast_update_time'] = props.get('updateTime')
        receipt['forecast_valid_times'] = props.get('validTimes')
        receipt['observed_available_at'] = retrieved
        receipt['pregame_use'] = 'Only for decisions after observed_available_at; final acceptance also checks game/roof/time joins.'
    else:
        receipt['published_timestamp_candidate'] = urllib.parse.urlsplit(url).path.rsplit('/', 1)[-1]
        receipt['pregame_use'] = 'PDF filename timestamp requires extracted-header and timezone validation before historical use.'
    store.put(raw_key, gzip.compress(raw, compresslevel=6, mtime=0), 'application/gzip')
    store.put(idx, pack(receipt))
    return data, receipt


def run(args):
    started = time.monotonic()
    run_id = dt.datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid.uuid4().hex[:10]
    stamp = dt.datetime.now(UTC).strftime('%Y-%m-%dT%H')
    store = Store(args.bucket, args.region)
    fetcher = Fetcher(args.max_requests, started + args.max_seconds - 35)
    report = {'run_id': run_id, 'started_at': utc(), 'status': 'running', 'receipts': [],
              'errors': [], 'venues': [], 'complete_historical_coverage': False,
              'bounds': {'requests': args.max_requests, 'seconds': args.max_seconds, 'venues': args.max_venues},
              'scope': 'Original current NWS forecast vintages for cached US college venues and explicitly discovered NBA PDFs.',
              'gaps': ['No historical weather backfill or historical publication inference.',
                       'NBA seed is one discovered report; it does not establish season coverage.',
                       'NFL stadium crosswalk not yet supplied; these venues are from CFBD.',
                       'No SEC/HDI bulk access, ESPN retry, or denied NBA live-data requests.']}
    last_beat = started
    def heartbeat(force=False):
        nonlocal last_beat
        if force or time.monotonic() - last_beat >= 20:
            last_beat = time.monotonic()
            report['requests'] = fetcher.calls
            report['elapsed_seconds'] = round(last_beat - started, 2)
            store.put('shared/acquisition/original-enrichment/' + run_id + '/progress.json', pack(report))
            print(json.dumps({'timestamp': utc(), 'event': 'HEARTBEAT', 'run_id': run_id,
                              'requests': fetcher.calls, 'captures': len(report['receipts']),
                              'venues_processed': len(report['venues']), 'elapsed_seconds': report['elapsed_seconds'],
                              'estimated_compute_usd': round(report['elapsed_seconds'] / 3600 * args.hourly_usd, 6)}), flush=True)
    try:
        rows, lineage = store.cached_cfbd('/venues', {}, args.cfbd_vintage)
        report['venue_input'] = lineage
        if rows is None:
            report['errors'].append({'stage': 'venues', 'reason': 'existing_venue_cache_missing'})
            selected = []
        else:
            selected = venues_from(rows)
        games, game_lineage = store.cached_cfbd('/games', {'year': 2026, 'seasonType': 'both'}, args.cfbd_vintage)
        report['games_priority_input'] = game_lineage
        selected, upcoming_count = prioritize(selected, games)
        report['eligible_venues'] = len(selected)
        report['upcoming_venue_ids_in_cache'] = upcoming_count
        selected = selected[:args.max_venues]
        report['planned_venues'] = len(selected)
        # This host is independently published for official reports; never
        # substitute it for the denied NBA live scoreboard source.
        pdf_allowed = True
        robot = None
        try:
            robots_raw, _ = fetcher.get('https://ak-static.cms.nba.com/robots.txt', 'text/plain')
            if b'<html' in robots_raw.lower():
                raise ValueError('robots_policy_not_plain_text')
            robot = urllib.robotparser.RobotFileParser()
            robot.parse(robots_raw.decode('utf-8', 'replace').splitlines())
            report['nba_robots_sha256'] = sha(robots_raw)
        except urllib.error.HTTPError as exc:
            if exc.code != 404:
                pdf_allowed = False
                report['errors'].append({'source': 'nba-official-injuries', 'reason': 'robots_access_denied_or_unavailable', 'status': exc.code})
        except (urllib.error.URLError, TimeoutError, ValueError, BoundedStop) as exc:
            pdf_allowed = False
            report['errors'].append({'source': 'nba-official-injuries', 'reason': type(exc).__name__})
        for url in NBA_SEEDS:
            if not pdf_allowed:
                break
            if robot and (not robot.can_fetch(UA, url) or not robot.can_fetch('ChatGPT-User', url)):
                report['errors'].append({'source': 'nba-official-injuries', 'reason': 'robots_disallowed'})
                continue
            try:
                _, receipt = capture(store, fetcher, url, 'pdf', '', run_id)
                receipt['seed_discovery'] = SEED_DISCOVERY
                report['receipts'].append(receipt)
            except (urllib.error.URLError, TimeoutError, ValueError, BoundedStop) as exc:
                report['errors'].append({'source': 'nba-official-injuries', 'reason': type(exc).__name__})
        for venue in selected:
            entry = {**venue, 'status': 'pending'}
            try:
                url = f"https://api.weather.gov/points/{venue['latitude']},{venue['longitude']}"
                point, receipt = capture(store, fetcher, url, 'nws', stamp, run_id)
                report['receipts'].append(receipt)
                forecast_url = point['properties'].get('forecastHourly')
                if not forecast_url or not valid_url(forecast_url, 'nws'):
                    raise ValueError('valid_hourly_forecast_url_missing')
                forecast, receipt = capture(store, fetcher, forecast_url, 'nws', stamp, run_id)
                if not isinstance(forecast['properties'].get('periods'), list):
                    raise ValueError('hourly_forecast_periods_missing')
                report['receipts'].append(receipt)
                entry.update(status='captured', forecast_raw_key=receipt['raw_key'],
                             forecast_periods=len(forecast['properties']['periods']))
            except BoundedStop as exc:
                entry.update(status='bounded_stop', reason=str(exc))
                report['venues'].append(entry)
                report['status'] = 'bounded_stop'
                break
            except (urllib.error.URLError, TimeoutError, ValueError) as exc:
                entry.update(status='failed', reason=type(exc).__name__)
                report['errors'].append({'venue_id': venue['id'], 'reason': type(exc).__name__})
            report['venues'].append(entry)
            heartbeat()
        if report['status'] == 'running':
            report['status'] = 'planned_scope_processed'
    except Exception as exc:
        report['status'] = 'failed'
        report['errors'].append({'stage': 'top_level', 'reason': type(exc).__name__, 'detail': str(exc)[:180]})
    finally:
        report['finished_at'] = utc()
        report['requests'] = fetcher.calls
        report['elapsed_seconds'] = round(time.monotonic() - started, 2)
        report['estimated_compute_usd'] = round(report['elapsed_seconds'] / 3600 * args.hourly_usd, 6)
        report['cost_scope'] = 'Runtime estimate only; boot, shutdown, S3 storage and requests additional.'
        report['downloaded'] = sum(x['status'] == 'downloaded' for x in report['receipts'])
        report['reused'] = sum(x['status'] == 'reused' for x in report['receipts'])
        report['successful_forecast_venues'] = sum(v['status'] == 'captured' for v in report['venues'])
        report['raw_bytes'] = sum(x['bytes'] for x in report['receipts'] if x['status'] == 'downloaded')
        report['planned_scope_complete'] = (report['status'] == 'planned_scope_processed' and
             report['successful_forecast_venues'] == report.get('planned_venues', 0) and
             report['successful_forecast_venues'] > 0 and not report['errors'])
        output = Path(args.output_dir)
        output.mkdir(parents=True, exist_ok=True)
        path = output / ('sports_edge_lab_original_enrichment_return_' + run_id + '.zip')
        with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as bundle:
            bundle.writestr('report.json', pack(report))
            bundle.writestr('resume.json', pack({'cache_vintage': stamp, 'cfbd_vintage': args.cfbd_vintage,
                                               'bucket': args.bucket, 'request_indexes_reusable': True}))
        prefix = 'shared/acquisition/original-enrichment/' + run_id + '/'
        store.put(prefix + 'report.json', pack(report))
        store.put(prefix + path.name, path.read_bytes(), 'application/zip')
        print(json.dumps({'timestamp': utc(), 'event': 'FINISHED', 'run_id': run_id,
                          'status': report['status'], 'downloaded': report['downloaded'],
                          'successful_forecast_venues': report['successful_forecast_venues'],
                          'requests': fetcher.calls, 'return_zip': str(path), 'report_key': prefix + 'report.json'}), flush=True)
    return 0 if report['planned_scope_complete'] else 2


class Tests(unittest.TestCase):
    def test_cache_identity_matches_paid_collector(self):
        identity = {'provider': 'cfbd', 'track': 'ncaaf', 'endpoint': '/venues', 'params': {}, 'capture_vintage': '2026-10-16'}
        self.assertEqual(cache_identity('/venues', {}, '2026-10-16'), 'tracks/ncaaf/raw/cfbd/request-index/' + sha(pack(identity)) + '.json')

    def test_source_allowlist(self):
        self.assertTrue(valid_url('https://api.weather.gov/gridpoints/LOX/154,44/forecast/hourly', 'nws'))
        for url in ('https://api.weather.gov.evil.org/points/1,2', 'http://api.weather.gov/points/1,2',
                    'https://user@api.weather.gov/points/1,2', 'https://api.weather.gov/points/1,2?key=x'):
            self.assertFalse(valid_url(url, 'nws'))

    def test_only_discovered_pdf_shape(self):
        self.assertTrue(valid_url(NBA_SEEDS[0], 'pdf'))
        self.assertFalse(valid_url('https://cdn.nba.com/static/json/liveData/scoreboard/todaysScoreboard_00.json', 'pdf'))

    def test_venue_filter_and_dedup(self):
        base = {'id': 1, 'countryCode': 'US', 'latitude': 34., 'longitude': -118., 'dome': False}
        rows = [base, dict(base, id=2), dict(base, id=3, latitude=35., dome=True),
                dict(base, id=4, latitude=999.), dict(base, id=5, countryCode='GB')]
        self.assertEqual([x['id'] for x in venues_from(rows)], [1])

    def test_pdf_and_json_validation(self):
        validate_payload(b'%PDF-1.4\nhello\n%%EOF', 'pdf')
        validate_payload(pack({'properties': {'periods': []}}), 'nws')
        for raw, kind in ((b'<html>denied</html>', 'pdf'), (b'[]', 'nws')):
            with self.assertRaises(ValueError):
                validate_payload(raw, kind)

    def test_budget_before_network(self):
        fetcher = Fetcher(0, time.monotonic() + 100)
        with self.assertRaises(BoundedStop):
            fetcher.get('https://api.weather.gov/points/34,-118')
        self.assertEqual(fetcher.calls, 0)

    def test_cached_payload_is_verified(self):
        class Fake:
            def get(self, key):
                if 'request-index' in key:
                    return pack({'raw_key': 'raw', 'sha256': sha(b'wrong'), 'status': 'downloaded'})
                return gzip.compress(pack({'properties': {}}))
        with self.assertRaises(ValueError):
            capture(Fake(), None, 'https://api.weather.gov/points/34,-118', 'nws', 'x', 'run')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--bucket', default='sagemaker-sports-edge-lab-560403859723-us-west-2')
    parser.add_argument('--region', default='us-west-2')
    parser.add_argument('--cfbd-vintage', default='2026-10-16')
    parser.add_argument('--max-requests', type=int, default=300)
    parser.add_argument('--max-seconds', type=int, default=600)
    parser.add_argument('--max-venues', type=int, default=120)
    parser.add_argument('--hourly-usd', type=float, default=.461)
    parser.add_argument('--output-dir', default='/opt/ml/processing/output')
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
    if not result.wasSuccessful():
        return 3
    if args.self_test:
        return 0
    if not (1 <= args.max_requests <= 300 and 60 <= args.max_seconds <= 600 and 1 <= args.max_venues <= 120):
        parser.error('Bounds require requests 1..300, seconds 60..600, venues 1..120')
    return run(args)


if __name__ == '__main__':
    sys.exit(main())
