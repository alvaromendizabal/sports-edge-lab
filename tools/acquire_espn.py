#!/usr/bin/env python3
"""Sports Edge Lab: original ESPN response capture; never historical PIT evidence.

Public website JSON endpoints are undocumented and coverage is empirical. This
runner respects HTTP denial/rate limits and robots rules, captures provenance,
and explicitly does not declare historical completeness from a nonempty result.
"""
import argparse
import calendar
import concurrent.futures
import datetime as dt
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
import uuid
import zipfile

BASE = 'https://site.api.espn.com'
TRACKS = {
    'nfl': ('football', 'nfl', 1999, None),
    'nba': ('basketball', 'nba', 2002, None),
    'ncaaf': ('football', 'college-football', 2001, '80'),
    'ncaam': ('basketball', 'mens-college-basketball', 2002, '50'),
    'ncaaw': ('basketball', 'womens-college-basketball', 2002, '50'),
}
UA = 'SportsEdgeLabResearch/1.0 (+https://github.com/alvaromendizabal/sports-edge-lab)'
PIT_WARNING = ('Retrieved retrospectively: results, present-day injury/roster/odds '
               'fields are not evidence of their historical availability. '
               'Do not join as pregame features without independently proven '
               'publication/available-at timestamps.')


def utc():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def digest(body):
    return hashlib.sha256(body).hexdigest()


def jsonbytes(obj):
    return json.dumps(obj, sort_keys=True, separators=(',', ':')).encode()


def endpoint(track, kind, **params):
    sport, league, _, group = TRACKS[track]
    if kind == 'scoreboard' and group:
        params['groups'] = group
    return BASE + '/apis/site/v2/sports/' + sport + '/' + league + '/' + kind + '?' + urllib.parse.urlencode(params)


def split_range(start, end):
    middle = start + (end - start) // 2
    return [(start, middle), (middle + dt.timedelta(days=1), end)]


def events_from(data, start, end):
    if not isinstance(data, dict) or not isinstance(data.get('events'), list):
        raise ValueError('scoreboard is missing events array')
    good, outside = [], 0
    for event in data['events']:
        day = dt.date.fromisoformat(event['date'][:10])
        if start <= day <= end:
            if not str(event.get('id', '')).isdigit():
                raise ValueError('event identifier invalid')
            good.append(event)
        else:
            outside += 1
    return good, outside


class Halt(Exception):
    pass


class Fetcher:
    def __init__(self, deadline, rps):
        self.deadline, self.interval = deadline, 1.0 / rps
        self.lock = threading.Lock()
        self.next = 0.0
        self.calls = 0
        self.denied = False
        self.robot = None
        self.access = 'unchecked'

    def throttle(self):
        with self.lock:
            if self.denied:
                raise Halt('HTTP access denied; source suspended')
            wait = max(0, self.next - time.monotonic())
            if time.monotonic() + wait >= self.deadline:
                raise Halt('runtime bound reached')
            self.next = max(self.next, time.monotonic()) + self.interval
        if wait:
            time.sleep(wait)

    def request(self, url, robots=False):
        if self.robot and not self.robot.can_fetch(UA, url):
            raise Halt('robots.txt disallows requested endpoint')
        for attempt in range(3):
            self.throttle()
            try:
                request = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept': 'application/json' if not robots else 'text/plain'})
                with urllib.request.urlopen(request, timeout=20) as response:
                    if urllib.parse.urlsplit(response.url).hostname != 'site.api.espn.com':
                        raise Halt('unexpected cross-host redirect')
                    body = response.read(30 * 1024 * 1024 + 1)
                    if len(body) > 30 * 1024 * 1024:
                        raise ValueError('response exceeds 30 MiB bound')
                    with self.lock:
                        self.calls += 1
                    return body, dict(response.headers)
            except urllib.error.HTTPError as error:
                if robots and error.code == 404:
                    return b'', {}
                if error.code in (401, 403):
                    self.denied = True
                    raise Halt('HTTP access denied; no bypass attempted') from error
                if error.code == 429:
                    with self.lock:
                        self.next = max(self.next, time.monotonic() + min(60, int(error.headers.get('Retry-After', '30'))))
                elif error.code not in (500, 502, 503, 504):
                    raise
                if attempt == 2:
                    raise
            except (TimeoutError, urllib.error.URLError):
                if attempt == 2:
                    raise
        raise RuntimeError('unreachable')

    def access_check(self):
        body, _ = self.request(BASE + '/robots.txt', robots=True)
        if body:
            if b'<html' in body.lower():
                raise Halt('robots response is HTML; access policy unverified')
            self.robot = urllib.robotparser.RobotFileParser()
            self.robot.parse(body.decode('utf-8', 'replace').splitlines())
            delay = self.robot.crawl_delay(UA) or self.robot.crawl_delay('*')
            if delay:
                self.interval = max(self.interval, float(delay))
            self.access = 'robots_observed_no_bypass'
        else:
            self.access = 'robots_not_published_http404'


class Store:
    def __init__(self, bucket, prefix, region):
        import boto3
        from botocore.config import Config
        self.s3 = boto3.client('s3', region_name=region, config=Config(retries={'total_max_attempts': 4, 'mode': 'adaptive'}, connect_timeout=5, read_timeout=30, max_pool_connections=12))
        self.bucket, self.prefix = bucket, prefix.strip('/')
        self.keys = set()
        for track in TRACKS:
            for page in self.s3.get_paginator('list_objects_v2').paginate(Bucket=bucket, Prefix=f'{self.prefix}/{track}/raw/espn/'):
                self.keys.update(obj['Key'] for obj in page.get('Contents', []))
        self.lock = threading.Lock()

    def get(self, key):
        with self.s3.get_object(Bucket=self.bucket, Key=key)['Body'] as body:
            return gzip.decompress(body.read())

    def put(self, key, body, metadata=None):
        self.s3.upload_fileobj(io.BytesIO(body), self.bucket, key,
                              ExtraArgs={'ServerSideEncryption': 'AES256', 'ContentType': 'application/gzip' if key.endswith('.gz') else 'application/json', 'Metadata': metadata or {}})
        with self.lock:
            self.keys.add(key)


def capture(fetcher, store, url, key, cached=True, validator=None):
    if cached and key in store.keys:
        raw = store.get(key)
        data = json.loads(raw)
        if validator:
            validator(data)
        return data, {'key': key, 'url': url, 'status': 'reused', 'sha256': digest(raw), 'bytes': len(raw)}
    raw, headers = fetcher.request(url)
    data = json.loads(raw)
    if validator:
        validator(data)
    receipt = {'key': key, 'url': url, 'status': 'downloaded', 'sha256': digest(raw), 'bytes': len(raw), 'retrieved_at': utc(), 'upstream_last_modified': headers.get('Last-Modified'), 'historical_available_at': None}
    packed = gzip.compress(raw, compresslevel=6, mtime=0)
    store.put(key, packed, {'sha256': receipt['sha256'], 'retrieved-at': receipt['retrieved_at'], 'source-url': url})
    return data, receipt


def run(args):
    started = time.monotonic()
    deadline = started + args.max_seconds - 45
    run_id = dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid.uuid4().hex[:8]
    today = dt.datetime.now(dt.timezone.utc).date()
    store = Store(args.bucket, args.prefix, args.region)
    fetcher = Fetcher(deadline, args.rps)
    report = {'run_id': run_id, 'started_at': utc(), 'pit_warning': PIT_WARNING, 'source': BASE, 'tracks': {}, 'errors': [], 'coverage_complete': False, 'status': 'running', 'query_scope': 'Division I college basketball; FBS college football; complete coverage not assumed', 'runtime_limit_seconds': args.max_seconds, 'summary_limit': args.max_summaries}
    receipts = []
    events = {track: {} for track in args.tracks}
    heartbeat_stop = threading.Event()

    def heartbeat():
        while not heartbeat_stop.wait(30):
            print(json.dumps({'at': utc(), 'event': 'HEARTBEAT', 'elapsed_seconds': round(time.monotonic() - started), 'http_successes': fetcher.calls, 'receipts': len(receipts), 'events_discovered': {k: len(v) for k, v in events.items()}}), flush=True)

    threading.Thread(target=heartbeat, daemon=True).start()
    try:
        fetcher.access_check()
        # Full-year requests reduce discovery cost. Any apparent truncation splits
        # the interval recursively; single-day saturation is explicitly unresolved.
        years = list(range(today.year, args.start_year - 1, -1))
        for year in years:
            for track in args.tracks:
                if year < TRACKS[track][2]:
                    continue
                start, end = dt.date(year, 1, 1), min(dt.date(year, 12, 31), today)
                pending = [(start, end)]
                while pending:
                    if time.monotonic() >= min(deadline, started + args.discovery_seconds):
                        raise Halt('discovery budget reached; continue with discovered events')
                    first, last = pending.pop(0)
                    dates = first.strftime('%Y%m%d') + '-' + last.strftime('%Y%m%d')
                    url = endpoint(track, 'scoreboard', dates=dates, limit=1000)
                    vintage = 'stable' if last < today - dt.timedelta(days=2) else run_id
                    key = f'{store.prefix}/{track}/raw/espn/scoreboards/{dates}/{vintage}.json.gz'
                    try:
                        data, receipt = capture(fetcher, store, url, key, validator=lambda value: events_from(value, first, last))
                        good, outside = events_from(data, first, last)
                        receipt.update(track=track, kind='scoreboard', events=len(good), outside_range=outside)
                        receipts.append(receipt)
                        for event in good:
                            events[track][str(event['id'])] = event
                        # Outside-range events reveal ignored dates. Split then flag
                        # unresolved single-day responses; never claim completeness.
                        count = len(data['events'])
                        total = data.get('count', data.get('total', count))
                        reported_limit = data.get('limit', 1000)
                        truncated = count >= 950 or (isinstance(total, int) and total > count) or (isinstance(reported_limit, int) and reported_limit > 0 and count >= reported_limit) or outside > 0
                        if truncated and first < last:
                            pending[0:0] = split_range(first, last)
                        elif truncated:
                            report['errors'].append({'track': track, 'dates': dates, 'type': 'possible_truncation_or_ignored_date'})
                    except Halt:
                        raise
                    except (ValueError, urllib.error.URLError, TimeoutError, KeyError) as error:
                        report['errors'].append({'track': track, 'url': url, 'type': type(error).__name__})
        report['discovery_status'] = 'planned_queries_finished_completeness_unproven'
    except Halt as error:
        report['discovery_status'] = str(error)

    def summary_key(track, event):
        complete = bool(event.get('status', {}).get('type', {}).get('completed'))
        old = dt.date.fromisoformat(event['date'][:10]) < today - dt.timedelta(days=2)
        vintage = 'completed' if complete and old else 'vintages/' + run_id
        return f'{store.prefix}/{track}/raw/espn/summaries/{vintage}/{event["id"]}.json.gz', vintage == 'completed'

    def summary_valid(data):
        if not isinstance(data, dict) or not data.get('header'):
            raise ValueError('summary is missing header')

    def summary_task(item):
        track, event = item
        event_id = str(event['id'])
        key, stable = summary_key(track, event)
        url = endpoint(track, 'summary', event=event_id)
        if stable and key in store.keys:
            return {'track': track, 'event_id': event_id, 'kind': 'summary', 'key': key, 'url': url, 'status': 'reused'}
        try:
            data, receipt = capture(fetcher, store, url, key, validator=summary_valid)
            receipt.update(track=track, event_id=event_id, kind='summary', has_boxscore=bool(data.get('boxscore')), has_plays=bool(data.get('plays') or data.get('drives')), historical_available_at=None)
            return receipt
        except (Halt, ValueError, urllib.error.URLError, TimeoutError) as error:
            return {'track': track, 'event_id': event_id, 'kind': 'summary', 'status': 'error', 'type': type(error).__name__, 'reason': str(error)[:160]}

    # Round-robin tracks so basketball volume cannot starve football or women.
    queues = {}
    for track, items in events.items():
        queue = []
        for event in sorted(items.values(), key=lambda e: e['date'], reverse=True):
            key, stable = summary_key(track, event)
            if stable and key in store.keys:
                receipts.append({'track': track, 'event_id': event['id'], 'kind': 'summary', 'key': key, 'status': 'reused'})
            else:
                queue.append(event)
        queues[track] = queue
    picked = []
    while any(queues.values()) and len(picked) < args.max_summaries:
        for track in args.tracks:
            if queues[track] and len(picked) < args.max_summaries:
                picked.append((track, queues[track].pop(0)))
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        pending = set()
        source = iter(picked)
        exhausted = False
        while (not exhausted or pending) and time.monotonic() < deadline and not fetcher.denied:
            while len(pending) < 8 and not exhausted:
                item = next(source, None)
                if item is None:
                    exhausted = True
                    break
                pending.add(executor.submit(summary_task, item))
            if pending:
                done, pending = concurrent.futures.wait(pending, timeout=1, return_when=concurrent.futures.FIRST_COMPLETED)
                for future in done:
                    receipts.append(future.result())
        for future in pending:
            receipts.append(future.result())
    heartbeat_stop.set()
    for track in args.tracks:
        records = [r for r in receipts if r.get('track') == track]
        report['tracks'][track] = {'events_discovered': len(events[track]), 'summary_downloaded': sum(r['status'] == 'downloaded' and r['kind'] == 'summary' for r in records), 'summary_reused': sum(r['status'] == 'reused' and r['kind'] == 'summary' for r in records), 'summary_errors': sum(r['status'] == 'error' for r in records), 'scoreboard_responses': sum(r['kind'] == 'scoreboard' for r in records)}
    report.update(finished_at=utc(), elapsed_seconds=round(time.monotonic() - started, 2), http_successes=fetcher.calls, access_check=fetcher.access, status='partial' if report['errors'] or any(r['status'] == 'error' for r in receipts) else 'bounded_capture_complete', historical_available_at=None)
    if fetcher.denied:
        report['status'] = 'source_access_blocked'
    elif not receipts:
        report['status'] = 'no_data_captured'
    report['remaining_discovered_events'] = max(0, sum(len(x) for x in events.values()) - sum(r['kind'] == 'summary' and r['status'] != 'error' for r in receipts))
    # One report bundle, with raw source data retained only in private S3.
    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    path = output / f'sports_edge_lab_espn_return_{run_id}.zip'
    with zipfile.ZipFile(path, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr('report.json', json.dumps(report, indent=2))
        archive.writestr('receipts.jsonl', ''.join(json.dumps(r) + '\n' for r in receipts))
        archive.writestr('event_manifest.json', json.dumps(events))
    store.s3.upload_file(str(path), args.bucket, f'shared/acquisition/espn/{run_id}/{path.name}', ExtraArgs={'ServerSideEncryption': 'AES256', 'ContentType': 'application/zip'})
    store.put(f'shared/acquisition/espn/{run_id}/report.json', jsonbytes(report))
    print(json.dumps(report, indent=2), flush=True)
    return 0 if any(r['status'] in ('downloaded', 'reused') for r in receipts) else 2


def selftest():
    assert endpoint('ncaaw', 'scoreboard', dates='20260101', limit=1000).endswith('dates=20260101&limit=1000&groups=50')
    first, last = dt.date(2025, 1, 1), dt.date(2025, 1, 31)
    split = split_range(first, last)
    assert split[0][0] == first and split[1][1] == last and split[0][1] + dt.timedelta(days=1) == split[1][0]
    good, outside = events_from({'events': [{'id': '1', 'date': '2025-01-04T00:00Z'}, {'id': '2', 'date': '2025-02-01T00:00Z'}]}, first, last)
    assert len(good) == 1 and outside == 1
    assert gzip.decompress(gzip.compress(b'raw response', mtime=0)) == b'raw response'
    assert digest(b'a') == hashlib.sha256(b'a').hexdigest()
    assert len(TRACKS) == 5
    print(json.dumps({'event': 'SELFTEST', 'checks': 6, 'passed': True}), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bucket', default='sagemaker-sports-edge-lab-560403859723-us-west-2')
    parser.add_argument('--prefix', default='tracks')
    parser.add_argument('--region', default='us-west-2')
    parser.add_argument('--tracks', nargs='+', choices=list(TRACKS), default=list(TRACKS))
    parser.add_argument('--start-year', type=int, default=1999)
    parser.add_argument('--max-seconds', type=int, default=3300)
    parser.add_argument('--discovery-seconds', type=int, default=1200)
    parser.add_argument('--max-summaries', type=int, default=6000)
    parser.add_argument('--rps', type=float, default=2.0)
    parser.add_argument('--output-dir', default='/opt/ml/processing/output')
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    if not 0 < args.rps <= 2 or not 60 <= args.max_seconds <= 3600 or not 0 <= args.max_summaries <= 6000:
        parser.error('rps <= 2, runtime 60..3600, summaries 0..6000 required')
    selftest()
    if args.self_test:
        return 0
    try:
        return run(args)
    except Exception as error:
        # Fatal AWS/configuration errors must fail the job rather than claim success.
        print(json.dumps({'event': 'FATAL', 'type': type(error).__name__, 'message': str(error)[:300]}), flush=True)
        output = Path(args.output_dir)
        output.mkdir(parents=True, exist_ok=True)
        # If the normal return already exists, preserve it instead of a second ZIP.
        if not list(output.glob('sports_edge_lab_espn_return_*.zip')):
            run_id = dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid.uuid4().hex[:8]
            with zipfile.ZipFile(output / f'sports_edge_lab_espn_return_{run_id}.zip', 'w', compression=zipfile.ZIP_DEFLATED) as archive:
                archive.writestr('report.json', json.dumps({'status': 'fatal', 'at': utc(), 'error_type': type(error).__name__, 'error': str(error)[:300], 'coverage_complete': False, 'pit_warning': PIT_WARNING}))
        return 1


if __name__ == '__main__':
    sys.exit(main())
