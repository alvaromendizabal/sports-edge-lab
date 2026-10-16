#!/usr/bin/env python3
"""Bounded Sports Edge Lab NWS continuation from verified prior acquisition evidence.

No paid API calls, ESPN requests, historical URL guessing, or access bypasses.
Venue coordinates are read from the existing CFBD S3 cache. Current forecasts
are prospective observations, never evidence of past forecast availability.
"""
import argparse
import concurrent.futures
from contextlib import redirect_stdout
import threading
import tempfile
from unittest.mock import patch
import datetime as dt
import gzip
import hashlib
import io
import json
from pathlib import Path
import sys
import time
import unittest
import urllib.error
import urllib.parse
import urllib.request
import uuid
import zipfile

UTC = dt.timezone.utc
UA = 'SportsEdgeLabResearch/1.1 (+https://github.com/alvaromendizabal/sports-edge-lab)'


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
        self.rate_lock = threading.Lock()
        self.capture_locks = {}
        self.capture_lock_guard = threading.Lock()

    def get(self, url, accept='application/geo+json'):
        host = urllib.parse.urlsplit(url).hostname
        with self.rate_lock:
            if host in self.blocked:
                raise BoundedStop('source_suspended:' + host)
            if self.calls >= self.limit or time.monotonic() + 15 >= self.deadline:
                raise BoundedStop('request_or_runtime_bound')
            delay = max(0., self.next_call - time.monotonic())
            if delay:
                time.sleep(delay)
            if time.monotonic() + 15 >= self.deadline:
                raise BoundedStop('runtime_bound')
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
                with self.rate_lock:
                    self.blocked.add(host)
                raise BoundedStop('provider_http_' + str(status) + '_suspended:' + host) from None
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
    value = json.loads(raw)
    if not isinstance(value, dict) or not isinstance(value.get('properties'), dict):
        raise ValueError('invalid_nws_geojson')
    return value


def capture_unlocked(store, fetcher, url, kind, vintage, run_id):
    if not valid_url(url, kind):
        raise ValueError('source_url_outside_allowlist')
    source = 'nws'
    base = 'shared/raw/nws/'
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
    raw, headers = fetcher.get(url, 'application/geo+json')
    data = validate_payload(raw, kind)
    digest = sha(raw)
    raw_key = base + 'objects/' + digest + '.json.gz'
    retrieved = utc()
    receipt = {'url': url, 'source': source, 'capture_vintage': vintage, 'run_id': run_id,
               'raw_key': raw_key, 'sha256': digest, 'bytes': len(raw), 'retrieved_at': retrieved,
               'upstream_last_modified': headers.get('last-modified'),
               'upstream_http_date': headers.get('date'), 'historical_available_at': None,
               'status': 'downloaded'}
    props = data['properties']
    receipt['forecast_generated_at'] = props.get('generatedAt')
    receipt['forecast_update_time'] = props.get('updateTime')
    receipt['forecast_valid_times'] = props.get('validTimes')
    receipt['observed_available_at'] = retrieved
    receipt['pregame_use'] = 'Only for decisions after observed_available_at; final acceptance also checks game/roof/time joins.'
    store.put(raw_key, gzip.compress(raw, compresslevel=6, mtime=0), 'application/gzip')
    store.put(idx, pack(receipt))
    return data, receipt


def capture(store, fetcher, url, kind, vintage, run_id):
    if fetcher is None:
        return capture_unlocked(store, fetcher, url, kind, vintage, run_id)
    key = (url, vintage)
    with fetcher.capture_lock_guard:
        lock = fetcher.capture_locks.setdefault(key, threading.Lock())
    with lock:
        return capture_unlocked(store, fetcher, url, kind, vintage, run_id)


def venue_identity(v):
    return (str(v.get('id')), round(float(v['latitude']), 4), round(float(v['longitude']), 4))


def continuation_plan(venues, prior):
    """Only successful prior forecast captures count; failures stay in the queue."""
    if not isinstance(prior, dict) or not isinstance(prior.get('venues'), list):
        raise ValueError('prior_report_schema_invalid')
    receipts = {r['raw_key']: r for r in prior.get('receipts', []) + prior.get('prior_successful_receipts', [])
                if r.get('source') == 'nws' and r.get('observed_available_at')
                and r.get('sha256') and r.get('raw_key')}
    successes = {}
    failures = set()
    for v in prior.get('prior_successful_venues', []) + prior['venues']:
        identity = venue_identity(v)
        if (v.get('status') == 'captured' and v.get('forecast_periods', 0) > 0
                and v.get('forecast_raw_key') in receipts):
            successes[identity] = dict(v)
        else:
            failures.add(identity)
    skipped = [successes[venue_identity(v)] for v in venues if venue_identity(v) in successes]
    selected = [v for v in venues if venue_identity(v) not in successes]
    selected.sort(key=lambda v: venue_identity(v) not in failures)
    return selected, skipped, failures


def reused_prior_point(store, prior, url):
    """Reuse static point metadata while retaining its original observation times."""
    for receipt in reversed(prior.get('receipts', [])):
        if receipt.get('url') == url and receipt.get('source') == 'nws':
            archived = store.get(receipt['raw_key'])
            if archived is None:
                raise ValueError('prior_point_archive_missing')
            raw = gzip.decompress(archived)
            if sha(raw) != receipt['sha256']:
                raise ValueError('prior_point_hash_mismatch')
            return validate_payload(raw, 'nws'), {**receipt, 'status': 'reused_prior_static_point'}
    return None


def run(args):
    started = time.monotonic()
    run_id = dt.datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid.uuid4().hex[:10]
    stamp = dt.datetime.now(UTC).strftime('%Y-%m-%dT%H')
    store = Store(args.bucket, args.region)
    fetcher = Fetcher(args.max_requests, started + args.max_seconds - 35)
    prefix = 'shared/acquisition/weather-continuation/' + run_id + '/'
    report = {'run_id': run_id, 'started_at': utc(), 'status': 'running', 'receipts': [],
              'errors': [], 'venues': [], 'prior_successful_venues': [],
              'capture_vintage': stamp, 'complete_historical_coverage': False,
              'prior_report_key': args.prior_report_key,
              'bounds': {'requests': args.max_requests, 'seconds': args.max_seconds,
                         'venues': args.max_venues, 'workers': args.workers, 'requests_per_second': 2},
              'scope': 'Resume current NWS hourly forecasts across cached US outdoor CFBD venues.',
              'gaps': ['Prior successful venues retain their original vintage and are not refreshed.',
                       'Forecast snapshots are prospective and are not historical weather backfill.',
                       'Venue inventory includes non-FBS venues; all 728 are not necessarily active games.',
                       'Roof status and game-to-venue joins still need validation.']}
    last_beat = started
    def heartbeat(force=False):
        nonlocal last_beat
        if force or time.monotonic() - last_beat >= 20:
            last_beat = time.monotonic()
            report['requests'] = fetcher.calls
            report['elapsed_seconds'] = round(last_beat - started, 2)
            store.put(prefix + 'progress.json', pack(report))
            print(json.dumps({'timestamp': utc(), 'event': 'HEARTBEAT', 'run_id': run_id,
                  'requests': fetcher.calls, 'captures': len(report['receipts']),
                  'prior_successful_skipped': len(report['prior_successful_venues']),
                  'venues_processed': len(report['venues']),
                  'venues_remaining': report.get('planned_venues', 0) - len(report['venues']),
                  'elapsed_seconds': report['elapsed_seconds'],
                  'estimated_compute_usd': round(report['elapsed_seconds'] / 3600 * args.hourly_usd, 6)}), flush=True)
    try:
        prior_raw = store.get(args.prior_report_key)
        if prior_raw is None:
            raise ValueError('prior_report_missing')
        prior = json.loads(prior_raw)
        report['prior_report_sha256'] = sha(prior_raw)
        report['prior_run_id'] = prior.get('run_id')
        rows, lineage = store.cached_cfbd('/venues', {}, args.cfbd_vintage)
        report['venue_input'] = lineage
        if rows is None:
            raise ValueError('existing_venue_cache_missing')
        all_venues = venues_from(rows)
        games, game_lineage = store.cached_cfbd('/games', {'year': 2026, 'seasonType': 'both'}, args.cfbd_vintage)
        report['games_priority_input'] = game_lineage
        all_venues, upcoming_count = prioritize(all_venues, games)
        selected, skipped, failed = continuation_plan(all_venues, prior)
        report['eligible_venues'] = len(all_venues)
        report['upcoming_venue_ids_in_cache'] = upcoming_count
        report['prior_successful_venues'] = skipped
        prior_keys = {v['forecast_raw_key'] for v in skipped}
        report['prior_successful_receipts'] = list({r['raw_key']: r for r in
            prior.get('receipts', []) + prior.get('prior_successful_receipts', [])
            if r.get('raw_key') in prior_keys}.values())
        report['remaining_eligible_before_run'] = len(selected)
        selected = selected[:args.max_venues]
        report['planned_venues'] = len(selected)
        report['retry_prior_failed_venues'] = [v['id'] for v in selected if venue_identity(v) in failed]
        heartbeat(True)
        def acquire(venue):
            entry, receipts = {**venue, 'status': 'pending'}, []
            try:
                if time.monotonic() + 20 >= fetcher.deadline:
                    raise BoundedStop('runtime_bound')
                url = f"https://api.weather.gov/points/{venue['latitude']},{venue['longitude']}"
                point_result = reused_prior_point(store, prior, url)
                point, receipt = point_result or capture(store, fetcher, url, 'nws', stamp, run_id)
                receipts.append(receipt)
                forecast_url = point['properties'].get('forecastHourly')
                if not forecast_url or not valid_url(forecast_url, 'nws'):
                    raise ValueError('valid_hourly_forecast_url_missing')
                forecast, receipt = capture(store, fetcher, forecast_url, 'nws', stamp, run_id)
                periods = forecast['properties'].get('periods')
                if not isinstance(periods, list) or not periods:
                    raise ValueError('nonempty_hourly_forecast_periods_missing')
                receipts.append(receipt)
                entry.update(status='captured', forecast_raw_key=receipt['raw_key'],
                             forecast_periods=len(periods), observed_available_at=receipt['observed_available_at'],
                             forecast_capture_vintage=receipt['capture_vintage'])
            except BoundedStop as exc:
                entry.update(status='bounded_stop', reason=str(exc))
            except (urllib.error.URLError, TimeoutError, ValueError) as exc:
                entry.update(status='failed', reason=type(exc).__name__)
            return entry, receipts
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
            pending = {pool.submit(acquire, venue): venue for venue in selected}
            for future in concurrent.futures.as_completed(pending):
                if future.cancelled():
                    continue
                entry, receipts = future.result()
                report['venues'].append(entry)
                report['receipts'].extend(receipts)
                if entry['status'] == 'failed':
                    report['errors'].append({'venue_id': entry['id'], 'reason': entry['reason']})
                elif entry['status'] == 'bounded_stop':
                    report['status'] = 'bounded_stop'
                    for other in pending:
                        other.cancel()
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
        report['reused'] = sum(x['status'].startswith('reused') for x in report['receipts'])
        report['successful_forecast_venues'] = sum(v['status'] == 'captured' for v in report['venues'])
        report['combined_successful_forecast_venues'] = report['successful_forecast_venues'] + len(report['prior_successful_venues'])
        report['remaining_eligible_after_run'] = report.get('eligible_venues', 0) - report['combined_successful_forecast_venues']
        report['raw_bytes'] = sum(x['bytes'] for x in report['receipts'] if x['status'] == 'downloaded')
        report['planned_scope_complete'] = (report['status'] == 'planned_scope_processed' and
             report['successful_forecast_venues'] == report.get('planned_venues', 0) and not report['errors'])
        output = Path(args.output_dir)
        output.mkdir(parents=True, exist_ok=True)
        path = output / ('sports_edge_lab_weather_continuation_return_' + run_id + '.zip')
        with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as bundle:
            bundle.writestr('report.json', pack(report))
            bundle.writestr('resume.json', pack({'capture_vintage': stamp, 'cfbd_vintage': args.cfbd_vintage,
                'bucket': args.bucket, 'prior_report_key': args.prior_report_key,
                'new_report_key': prefix + 'report.json', 'request_indexes_reusable': True,
                'prior_successful_venue_snapshots_are_older_and_not_refreshed': True}))
        store.put(prefix + 'report.json', pack(report))
        store.put(prefix + path.name, path.read_bytes(), 'application/zip')
        print(json.dumps({'timestamp': utc(), 'event': 'FINISHED', 'run_id': run_id,
              'status': report['status'], 'downloaded': report['downloaded'],
              'successful_forecast_venues': report['successful_forecast_venues'],
              'combined_successful_forecast_venues': report['combined_successful_forecast_venues'],
              'remaining_eligible_after_run': report['remaining_eligible_after_run'],
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

    def test_venue_filter_and_dedup(self):
        base = {'id': 1, 'countryCode': 'US', 'latitude': 34., 'longitude': -118., 'dome': False}
        rows = [base, dict(base, id=2), dict(base, id=3, latitude=35., dome=True),
                dict(base, id=4, latitude=999.), dict(base, id=5, countryCode='GB')]
        self.assertEqual([x['id'] for x in venues_from(rows)], [1])

    def test_json_validation(self):
        validate_payload(pack({'properties': {'periods': []}}), 'nws')
        for raw in (b'<html>denied</html>', b'[]'):
            with self.assertRaises(ValueError):
                validate_payload(raw, 'nws')

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

    def test_skip_119_successes_retry_failed_and_plan_remaining_609(self):
        venues = [{'id': i, 'latitude': 30 + i / 10000, 'longitude': -100.} for i in range(728)]
        prior = {'venues': [{**v, 'status': 'captured', 'forecast_raw_key': 'raw/' + str(v['id']),
                            'forecast_periods': 156} for v in venues[:119]],
                 'receipts': [{'source': 'nws', 'raw_key': 'raw/' + str(i), 'sha256': 'abc',
                               'observed_available_at': '2026-10-16T18:20:00Z'} for i in range(119)]}
        prior['venues'].append({**venues[500], 'status': 'failed', 'reason': 'URLError'})
        pending, skipped, failed = continuation_plan(venues, prior)
        self.assertEqual(len(skipped), 119)
        self.assertEqual(len(pending), 609)
        self.assertEqual(pending[0]['id'], 500)
        self.assertFalse(set(v['id'] for v in pending) & set(range(119)))

    def test_failed_or_unproven_success_is_never_skipped(self):
        v = {'id': 1, 'latitude': 34, 'longitude': -118}
        prior = {'venues': [{**v, 'status': 'captured', 'forecast_periods': 156,
                            'forecast_raw_key': 'missing'}], 'receipts': []}
        pending, skipped, failed = continuation_plan([v], prior)
        self.assertEqual(pending, [v])
        self.assertFalse(skipped)

    def test_success_lineage_survives_second_continuation(self):
        v = {'id': 1, 'latitude': 34, 'longitude': -118, 'status': 'captured',
             'forecast_periods': 156, 'forecast_raw_key': 'old'}
        prior = {'venues': [], 'prior_successful_venues': [v], 'receipts': [],
                 'prior_successful_receipts': [{'source': 'nws', 'raw_key': 'old',
                     'sha256': 'abc', 'observed_available_at': '2026-10-16T18:20:00Z'}]}
        pending, skipped, failed = continuation_plan([v], prior)
        self.assertFalse(pending)
        self.assertEqual(skipped, [v])

    def test_reuse_preserves_immutable_observation_timestamp(self):
        url = 'https://api.weather.gov/points/34,-118'
        raw = pack({'properties': {'forecastHourly': 'https://api.weather.gov/gridpoints/LOX/1,1/forecast/hourly'}})
        receipt = {'url': url, 'source': 'nws', 'raw_key': 'raw', 'sha256': sha(raw),
                   'observed_available_at': '2026-10-16T18:20:00Z',
                   'retrieved_at': '2026-10-16T18:20:00Z', 'capture_vintage': '2026-10-16T18',
                   'status': 'downloaded'}
        class Fake:
            def get(self, key):
                return gzip.compress(raw) if key == 'raw' else pack(receipt)
        prior = {'receipts': [dict(receipt)]}
        point, reused = reused_prior_point(Fake(), prior, url)
        self.assertEqual(reused['retrieved_at'], receipt['retrieved_at'])
        self.assertEqual(reused['observed_available_at'], receipt['observed_available_at'])
        self.assertEqual(reused['capture_vintage'], receipt['capture_vintage'])
        self.assertEqual(prior['receipts'][0], receipt)
        point, cached = capture(Fake(), None, url, 'nws', '2026-10-16T18', 'new-run')
        self.assertEqual(cached['observed_available_at'], receipt['observed_available_at'])

    def test_source_denial_stops_immediately_without_retry(self):
        for code in (401, 403, 429):
            fetcher = Fetcher(20, time.monotonic() + 100)
            class Denied:
                def open(self, request, timeout):
                    raise urllib.error.HTTPError(request.full_url, code, 'denied', {}, None)
            fetcher.opener = Denied()
            with self.assertRaises(BoundedStop):
                fetcher.get('https://api.weather.gov/points/34,-118')
            self.assertEqual(fetcher.calls, 1)
            with self.assertRaises(BoundedStop):
                fetcher.get('https://api.weather.gov/points/35,-118')
            self.assertEqual(fetcher.calls, 1)

    def test_full_run_skips_prior_and_emits_one_complete_return(self):
        venues = [{'id': i, 'countryCode': 'US', 'latitude': 34 + i / 100.,
                   'longitude': -118., 'dome': False} for i in range(3)]
        prior_receipt = {'source': 'nws', 'raw_key': 'old/forecast', 'sha256': 'oldhash',
                         'observed_available_at': '2026-10-16T18:20:00Z'}
        prior = {'run_id': 'prior', 'receipts': [prior_receipt], 'venues': [
            {**venues[0], 'status': 'captured', 'forecast_periods': 156,
             'forecast_raw_key': 'old/forecast'}, {**venues[1], 'status': 'failed'}]}
        class FakeStore:
            data = {'prior/report.json': pack(prior)}
            def __init__(self, bucket, region):
                pass
            def get(self, key):
                return self.data.get(key)
            def put(self, key, raw, content_type='application/json'):
                self.data[key] = raw
            def cached_cfbd(self, endpoint, params, vintage):
                return (venues if endpoint == '/venues' else []), {'status': 'verified_reused'}
        class FakeFetcher(Fetcher):
            def get(self, url, accept='application/geo+json'):
                with self.rate_lock:
                    self.calls += 1
                if '/points/' in url:
                    grid = '1,1' if '34.01,' in url else '2,2'
                    return pack({'properties': {'forecastHourly':
                        'https://api.weather.gov/gridpoints/LOX/' + grid + '/forecast/hourly'}}), {}
                return pack({'properties': {'periods': [{'number': 1}]}}), {}
        with tempfile.TemporaryDirectory() as out:
            args = argparse.Namespace(bucket='unused', region='us-west-2', max_requests=1500,
                max_seconds=1200, max_venues=728, workers=2, hourly_usd=.461,
                cfbd_vintage='2026-10-16', prior_report_key='prior/report.json', output_dir=out)
            with patch.dict(globals(), {'Store': FakeStore, 'Fetcher': FakeFetcher}), redirect_stdout(io.StringIO()):
                self.assertEqual(run(args), 0)
            paths = list(Path(out).glob('*.zip'))
            self.assertEqual(len(paths), 1)
            with zipfile.ZipFile(paths[0]) as bundle:
                result = json.loads(bundle.read('report.json'))
            self.assertTrue(result['planned_scope_complete'])
            self.assertEqual(result['combined_successful_forecast_venues'], 3)
            self.assertEqual(result['requests'], 4)
            self.assertEqual(result['remaining_eligible_after_run'], 0)
            self.assertEqual(result['retry_prior_failed_venues'], [1])
            self.assertEqual(result['prior_successful_receipts'], [prior_receipt])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--bucket', default='sagemaker-sports-edge-lab-560403859723-us-west-2')
    parser.add_argument('--region', default='us-west-2')
    parser.add_argument('--cfbd-vintage', default='2026-10-16')
    parser.add_argument('--max-requests', type=int, default=1500)
    parser.add_argument('--max-seconds', type=int, default=1200)
    parser.add_argument('--max-venues', type=int, default=728)
    parser.add_argument('--workers', type=int, default=4)
    parser.add_argument('--prior-report-key', default='shared/acquisition/original-enrichment/20261016T182059Z-5f05a0d4d3/report.json')
    parser.add_argument('--hourly-usd', type=float, default=.461)
    parser.add_argument('--output-dir', default='/opt/ml/processing/output')
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
    if not result.wasSuccessful():
        return 3
    if args.self_test:
        return 0
    if not (1 <= args.max_requests <= 1500 and 60 <= args.max_seconds <= 1200 and 1 <= args.max_venues <= 728 and 1 <= args.workers <= 4):
        parser.error('Bounds require requests 1..1500, seconds 60..1200, venues 1..728, workers 1..4')
    return run(args)


if __name__ == '__main__':
    sys.exit(main())
