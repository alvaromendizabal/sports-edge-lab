#!/usr/bin/env python3
"""SkillCorner ACB research sample, pinned source objects with bounded streaming.

The original provider owns the tracking and derived events. This is separate
from NBA/NCAA tracks; no video, full league history, or pregame features claimed.
"""
import argparse
import csv
import datetime as dt
import gzip
import hashlib
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

UTC = dt.timezone.utc
UA = 'SportsEdgeLabResearch/1.4 (+https://github.com/alvaromendizabal/sports-edge-lab)'
BASE = 'shared/raw/skillcorner-acb-research/'
PREFIX = 'shared/acquisition/open-tracking/'
HOSTS = {'raw.githubusercontent.com', 'media.githubusercontent.com'}


def utc(): return dt.datetime.now(UTC).isoformat(timespec='seconds').replace('+00:00', 'Z')
def pack(x): return json.dumps(x, sort_keys=True, separators=(',', ':')).encode()
def sha(raw): return hashlib.sha256(raw).hexdigest()


def load_manifest():
    if zipfile.is_zipfile(sys.argv[0]):
        with zipfile.ZipFile(sys.argv[0]) as z: return json.loads(z.read('source_manifest.json'))
    return json.loads(Path(__file__).with_name('source_manifest.json').read_text())


def load_license():
    if zipfile.is_zipfile(sys.argv[0]):
        with zipfile.ZipFile(sys.argv[0]) as z: return z.read('UPSTREAM_LICENSE.txt')
    return Path(__file__).with_name('UPSTREAM_LICENSE.txt').read_bytes()


def validate_manifest(m):
    if not re.fullmatch('[0-9a-f]{40}', m['commit']): raise ValueError('invalid_commit')
    if m['league'] != 'Spanish Liga ACB' or m['raw_video_included']: raise ValueError('invalid_scope')
    if not 1 <= len(m['games']) <= 10 or len(set(m['games'])) != len(m['games']): raise ValueError('invalid_games')
    if m['license']['identifier'] != 'MIT' or not m['license'].get('sha256'): raise ValueError('missing_license')
    if len(m['assets']) > 70 or sum(a['size'] for a in m['assets']) > 600_000_000: raise ValueError('manifest_budget')
    paths = set()
    for a in m['assets']:
        if a['path'] in paths or '..' in a['path'].split('/'): raise ValueError('duplicate_or_unsafe_path')
        paths.add(a['path'])
        p = urllib.parse.urlsplit(a['url'])
        base = '/media/' if a['kind'] == 'tracking' else '/'
        expected = base + 'SkillCorner/opendata-basketball/' + m['commit'] + '/' + a['path']
        expected_host = 'media.githubusercontent.com' if a['kind'] == 'tracking' else 'raw.githubusercontent.com'
        if p.scheme != 'https' or p.netloc != expected_host or p.path != expected or p.query or p.fragment:
            raise ValueError('unobserved_source_or_commit')
        if a.get('game_id') is not None and a['game_id'] not in m['games']: raise ValueError('extra_game')
        if a['size'] < 1 or a['size'] > 70_000_000: raise ValueError('per_file_size_bound')
        if not re.fullmatch('[0-9a-f]{40}', a['git_blob_sha1']): raise ValueError('missing_git_blob')
        if a['kind'] == 'tracking' and not re.fullmatch('[0-9a-f]{64}', a.get('lfs_sha256', '')):
            raise ValueError('missing_lfs_sha256')
    if not {'LICENSE', 'README.md', 'data/matches.json', 'data/player_id_aliases.csv'} <= paths:
        raise ValueError('missing_required_provenance')
    for game in m['games']:
        if {a['kind'] for a in m['assets'] if a.get('game_id') == game} != {'tracking', 'events', 'game_metadata'}:
            raise ValueError('incomplete_game_manifest')


def robots_policy(text, url):
    groups, agents, rules = [], [], []
    def finish():
        if agents: groups.append((agents[:], rules[:]))
    for line in text.splitlines():
        line = line.split('#', 1)[0].strip()
        if ':' not in line: continue
        key, val = [s.strip() for s in line.split(':', 1)]; key = key.lower()
        if key == 'user-agent':
            if rules: finish(); agents, rules = [], []
            agents.append(val.lower())
        elif agents and key in ('allow', 'disallow', 'crawl-delay'): rules.append((key, val))
    finish()
    matches = [(max((len(a) for a in names if a != '*' and a in UA.lower()), default=0), rs)
               for names, rs in groups if '*' in names or any(a in UA.lower() for a in names)]
    longest = max((n for n, _ in matches), default=-1)
    selected = [r for n, rs in matches if n == longest for r in rs]
    p = urllib.parse.urlsplit(url); target = p.path + ('?' + p.query if p.query else '')
    decisions, delay = [], 1.
    for kind, pattern in selected:
        if kind == 'crawl-delay':
            try: delay = max(delay, float(pattern))
            except ValueError: raise ValueError('invalid_crawl_delay')
        elif pattern:
            end = pattern.endswith('$'); body = pattern[:-1] if end else pattern
            if re.search('^' + re.escape(body).replace(r'\*', '.*') + ('$' if end else ''), target):
                decisions.append((len(body.replace('*', '')), kind == 'allow'))
    return max(decisions, default=(0, True))[1], delay


class BoundedStop(Exception): pass


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl): return None


class Fetcher:
    def __init__(self, m, deadline, max_bytes, max_requests):
        self.allowed = {a['url'] for a in m['assets']}
        self.allowed.update('https://' + h + '/robots.txt' for h in HOSTS)
        self.deadline, self.max_bytes, self.max_requests = deadline, max_bytes, max_requests
        self.bytes, self.calls, self.last = 0, 0, {}
        self.blocked, self.robots = set(), {}
        self.opener = urllib.request.build_opener(NoRedirect)
        self.beat = lambda: None

    def fetch(self, url, path, expected_size=None, delay=1.):
        if url not in self.allowed: raise ValueError('url_not_observed_in_pinned_manifest')
        host = urllib.parse.urlsplit(url).hostname
        if host in self.blocked: raise BoundedStop('source_suspended:' + host)
        pause = max(0., self.last.get(host, -1e12) + delay - time.monotonic())
        remaining = self.max_bytes - self.bytes
        if (self.calls >= self.max_requests or time.monotonic() + pause + 35 >= self.deadline
                or remaining < 1 or (expected_size is not None and expected_size > remaining)):
            raise BoundedStop('request_time_or_byte_bound')
        if pause: time.sleep(pause)
        self.calls += 1; self.last[host] = time.monotonic()
        try:
            with self.opener.open(urllib.request.Request(url, headers={'User-Agent': UA, 'Accept-Encoding': 'identity'}), timeout=30) as res:
                declared = res.headers.get('Content-Length')
                limit = expected_size if expected_size is not None else min(100_000, remaining)
                if declared and int(declared) > limit: raise ValueError('declared_size_exceeds_expected')
                count, last_beat = 0, time.monotonic()
                with path.open('wb') as out:
                    while True:
                        if time.monotonic() >= self.deadline: raise BoundedStop('download_runtime_bound')
                        chunk = res.read(min(65536, limit - count + 1))
                        if not chunk: break
                        count += len(chunk); self.bytes += len(chunk)
                        if count > limit or self.bytes > self.max_bytes: raise BoundedStop('streaming_byte_bound')
                        out.write(chunk)
                        if time.monotonic() - last_beat >= 25:
                            self.beat(); last_beat = time.monotonic()
                if expected_size is not None and count != expected_size: raise ValueError('truncated_or_unexpected_size')
                return {k.lower(): v for k, v in res.headers.items()}
        except urllib.error.HTTPError as e:
            if e.code in (401, 403, 429): self.blocked.add(host)
            e.close(); raise

    def get(self, asset, path, report, store):
        host = urllib.parse.urlsplit(asset['url']).hostname
        if host not in self.robots:
            url = 'https://' + host + '/robots.txt'
            robots_path = path.with_suffix('.robots')
            try:
                headers = self.fetch(url, robots_path)
                text = robots_path.read_text(errors='replace')
                if re.search(r'<\s*(?:html|!doctype)', text, re.I) or not re.search(r'^\s*User-agent\s*:', text, re.I | re.M):
                    raise ValueError('invalid_robots_response')
                digest = sha(robots_path.read_bytes()); key = PREFIX + 'evidence/objects/' + digest + '.robots.txt'
                store.upload(robots_path, key, 'text/plain')
                report['robots'].append({'url': url, 'status': 200, 'raw_key': key, 'sha256': digest, 'captured_at': utc()})
                self.robots[host] = text
            except urllib.error.HTTPError as e:
                if e.code not in (404, 410): self.blocked.add(host); raise
                # RFC9309: unavailable robots (404/410) supplies no restrictions.
                report['robots'].append({'url': url, 'status': e.code, 'captured_at': utc(), 'interpretation': 'robots unavailable; no published directives'})
                self.robots[host] = 'User-agent: *\nAllow: /'
            except Exception:
                self.blocked.add(host); raise
        allowed, delay = robots_policy(self.robots[host], asset['url'])
        if not allowed: raise BoundedStop('robots_disallowed')
        return self.fetch(asset['url'], path, asset['size'], delay)


def file_hashes(path):
    size = path.stat().st_size
    h256, hgit = hashlib.sha256(), hashlib.sha1(('blob ' + str(size) + '\0').encode())
    with path.open('rb') as f:
        while True:
            chunk = f.read(1 << 20)
            if not chunk: break
            h256.update(chunk); hgit.update(chunk)
    return {'sha256': h256.hexdigest(), 'git_blob_sha1': hgit.hexdigest(), 'bytes': size}


def validate_asset(path, asset, deadline, beat):
    hashes = file_hashes(path)
    if hashes['bytes'] != asset['size']: raise ValueError('source_size_mismatch')
    if asset['kind'] == 'tracking':
        if hashes['sha256'] != asset['lfs_sha256']: raise ValueError('lfs_sha256_mismatch')
    elif hashes['git_blob_sha1'] != asset['git_blob_sha1']: raise ValueError('git_blob_sha1_mismatch')
    result = dict(hashes)
    if asset['kind'] == 'tracking':
        count, active, player_points, detected, prior, decoded, last_beat = 0, 0, 0, 0, -1, 0, time.monotonic()
        with gzip.open(path, 'rb') as f:
            while True:
                if time.monotonic() >= deadline: raise BoundedStop('validation_runtime_bound')
                line = f.readline(1_000_001)
                if not line: break
                decoded += len(line)
                if len(line) > 1_000_000 or decoded > 1_500_000_000: raise ValueError('decoded_tracking_bound')
                row = json.loads(line)
                if (not isinstance(row, dict) or not isinstance(row.get('frameIdx'), int)
                        or row['frameIdx'] <= prior or not isinstance(row.get('homePlayers'), list)
                        or not isinstance(row.get('awayPlayers'), list) or not isinstance(row.get('ball'), dict)):
                    raise ValueError('tracking_frame_schema')
                prior = row['frameIdx']; count += 1
                players = row['homePlayers'] + row['awayPlayers']; active += bool(players)
                for player in players:
                    if not isinstance(player, dict) or len(player.get('xyz', [])) != 3 or 'playerId' not in player:
                        raise ValueError('tracking_player_schema')
                    player_points += 1; detected += player.get('isDetected') == 1
                if count > 300_000: raise ValueError('tracking_frame_bound')
                if time.monotonic() - last_beat >= 25: beat(); last_beat = time.monotonic()
        if not count or not active: raise ValueError('empty_tracking')
        result.update(frames=count, frames_with_players=active, player_points=player_points,
                      detected_player_points=detected, decoded_bytes=decoded, full_gzip_crc_checked=True)
    elif asset['path'].endswith('.json'):
        data = json.loads(path.read_bytes())
        if not isinstance(data, (dict, list)) or not data: raise ValueError('empty_or_invalid_json')
        if asset['kind'] == 'events':
            if not isinstance(data, dict) or not any(isinstance(x, list) for x in data.values()): raise ValueError('events_schema')
            result['event_family_rows'] = {k: len(v) for k, v in data.items() if isinstance(v, list)}
        elif asset['kind'] == 'game_metadata':
            if (not isinstance(data, dict) or data.get('gameId') != asset.get('game_id')
                    or data.get('competitionName') != 'Liga ACB' or data.get('seasonName') != '2025-2026'):
                raise ValueError('game_metadata_identity_or_league_mismatch')
            result['event_date_utc'] = data.get('date')
            result['provider_processing_timestamps'] = {k: v for k, v in data.items() if k.endswith('LastProcessingDate')}
    elif asset['path'].endswith('.csv'):
        with path.open(newline='', encoding='utf-8-sig') as f:
            rows = list(csv.reader(f))
            if len(rows) < 2: raise ValueError('empty_csv')
            result['rows_including_header'] = len(rows)
    return result


class Store:
    def __init__(self, bucket, region):
        import boto3
        from botocore.config import Config
        self.bucket = bucket
        self.s3 = boto3.client('s3', region_name=region, config=Config(
            retries={'mode': 'adaptive', 'total_max_attempts': 3}, connect_timeout=5, read_timeout=30))
    def put(self, key, raw, content_type='application/json'):
        self.s3.upload_fileobj(io.BytesIO(raw), self.bucket, key, ExtraArgs={'ContentType': content_type, 'ServerSideEncryption': 'AES256'})
    def upload(self, path, key, content_type):
        self.s3.upload_file(str(path), self.bucket, key, ExtraArgs={'ContentType': content_type, 'ServerSideEncryption': 'AES256'})
    def download(self, key, path): self.s3.download_file(self.bucket, key, str(path))
    def cached(self):
        records = {}
        for page in self.s3.get_paginator('list_objects_v2').paginate(Bucket=self.bucket, Prefix=BASE + 'url-index/'):
            for obj in page.get('Contents', []):
                if len(records) >= 200: raise ValueError('cache_index_bound')
                if not obj['Key'].endswith('.json'): continue
                with self.s3.get_object(Bucket=self.bucket, Key=obj['Key'])['Body'] as body: r = json.load(body)
                if r.get('source_path') and r.get('raw_key') and r.get('sha256'): records[(r.get('commit'), r['source_path'])] = r
        return records


def run(args):
    started = time.monotonic(); deadline = started + args.max_seconds - 45
    m = load_manifest(); validate_manifest(m)
    run_id = dt.datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid.uuid4().hex[:10]
    prefix = PREFIX + run_id + '/'
    store = Store(args.bucket, args.region)
    fetcher = Fetcher(m, deadline, args.max_bytes, args.max_requests)
    report = {'run_id': run_id, 'started_at': utc(), 'status': 'running', 'receipts': [], 'errors': [],
              'pending_paths': [], 'robots': [], 'commit': m['commit'], 'league': m['league'], 'season': m['season'],
              'planned_games': m['games'], 'raw_video_included': False, 'point_in_time_approved': False,
              'tests': {'passed': True, 'count': len(unittest.defaultTestLoader.getTestCaseNames(Tests))}, 'source_ownership': m['ownership'], 'license': m['license'],
              'bounds': {'seconds': args.max_seconds, 'http_bytes': args.max_bytes, 'http_requests': args.max_requests},
              'coverage': 'Ten ACB research games; not NBA, NCAA, league-wide tracking, or model performance evidence.'}
    def progress():
        report.update(updated_at=utc(), http_requests=fetcher.calls, http_bytes=fetcher.bytes,
                      elapsed_seconds=round(time.monotonic() - started, 3), blocked_hosts=sorted(fetcher.blocked))
        report['estimated_compute_usd'] = round(report['elapsed_seconds'] * args.hourly_usd / 3600, 6)
        report['downloaded_raw_files'] = sum(r['kind'] != 'evidence' and r['status'] == 'downloaded' for r in report['receipts'])
        report['reused_raw_files'] = sum(r['kind'] != 'evidence' and r['status'] == 'reused' for r in report['receipts'])
        report['tracking_games'] = sorted(r['game_id'] for r in report['receipts'] if r['kind'] == 'tracking')
        report['raw_stored_bytes'] = sum(r['bytes'] for r in report['receipts'] if r['kind'] != 'evidence')
        report['remaining_assets'] = len(m['assets']) - len(report['receipts'])
        store.put(prefix + 'progress.json', pack(report))
        print(json.dumps({k: report[k] for k in ('updated_at', 'status', 'downloaded_raw_files', 'reused_raw_files',
                    'http_bytes', 'remaining_assets', 'elapsed_seconds', 'estimated_compute_usd')}), flush=True)
    fetcher.beat = progress
    assets = sorted(m['assets'], key=lambda a: (0 if a['path'] == 'LICENSE' else 1 if a['path'] == 'README.md' else 2 if a['kind'] == 'evidence' else 3, a['path']))
    existing = store.cached(); licensed = False
    out = Path(args.output_dir); out.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='sports-edge-tracking-') as work:
        for i, a in enumerate(assets):
            path = Path(work) / ('asset' + ('.jsonl.gz' if a['kind'] == 'tracking' else Path(a['path']).suffix))
            report['current_asset'] = a['path']; progress()
            try:
                if a['kind'] != 'evidence' and not licensed: raise ValueError('license_gate_not_passed')
                prior = existing.get((m['commit'], a['path']))
                if prior:
                    store.download(prior['raw_key'], path)
                    validation = validate_asset(path, a, deadline, progress)
                    if validation['sha256'] != prior['sha256']: raise ValueError('cached_sha256_mismatch')
                    receipt = {**prior, 'status': 'reused', 'validation': validation}
                else:
                    headers = fetcher.get(a, path, report, store)
                    validation = validate_asset(path, a, deadline, progress)
                    digest = validation['sha256']
                    ext = '.jsonl.gz' if a['kind'] == 'tracking' else Path(a['path']).suffix or '.txt'
                    base = PREFIX + 'evidence/' if a['kind'] == 'evidence' else BASE
                    key = base + 'objects/' + digest + ext
                    mime = 'application/gzip' if a['kind'] == 'tracking' else 'application/json' if ext == '.json' else 'text/plain'
                    store.upload(path, key, mime)
                    receipt = {'source_url': a['url'], 'source_path': a['path'], 'commit': m['commit'],
                               'raw_key': key, 'sha256': digest, 'bytes': validation['bytes'], 'kind': a['kind'],
                               'game_id': a.get('game_id'), 'captured_at': utc(), 'run_id': run_id, 'status': 'downloaded',
                               'source_manifest_observed_at': m['observed_at'], 'source_git_blob_sha1': a['git_blob_sha1'],
                               'source_lfs_sha256': a.get('lfs_sha256'), 'upstream_last_modified': headers.get('last-modified'),
                               'validation': validation, 'league': m['league'], 'point_in_time_approved': False,
                               'license_sha256': m['license']['sha256'], 'attribution': 'SkillCorner'}
                    store.put(BASE + 'url-index/' + sha((m['commit'] + ':' + a['path']).encode()) + '.json', pack(receipt))
                if a['path'] == 'LICENSE':
                    if receipt['sha256'] != m['license']['sha256']: raise ValueError('license_hash_gate')
                    licensed = True
                report['receipts'].append(receipt)
            except Exception as exc:
                report['errors'].append({'source_path': a['path'], 'error': type(exc).__name__,
                                         'http_status': getattr(exc, 'code', None), 'reason': str(exc)[:240]})
                report['pending_paths'] = [x['path'] for x in assets[i:]]
                break
            finally:
                if path.exists(): path.unlink()
            progress()
    report['status'] = 'completed_pinned_sample' if not report['pending_paths'] else 'partial'
    report['completed_at'] = utc(); progress()
    store.put(prefix + 'report.json', pack(report))
    target = out / ('sports_edge_lab_open_tracking_' + run_id + '_return.zip')
    with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('report.json', pack(report)); z.writestr('source_manifest.json', pack(m))
        z.writestr('resume.json', pack({'pending_paths': report['pending_paths'], 'commit': m['commit'], 'index_prefix': BASE + 'url-index/'}))
        z.writestr('ATTRIBUTION.txt', 'Original data and provider-derived events: SkillCorner. Preserve the pinned MIT license and README. ACB sample only. No video included.\n')
        z.writestr('UPSTREAM_LICENSE.txt', load_license())
    store.upload(target, prefix + target.name, 'application/zip')
    print(json.dumps({'event': 'RETURN_READY', 'report_key': prefix + 'report.json', 'return_key': prefix + target.name,
                      'return_sha256': sha(target.read_bytes())}), flush=True)
    return 0 if report['status'] == 'completed_pinned_sample' else 2


def fixture_asset(path, raw, kind='dataset_metadata'):
    path.write_bytes(raw); h = file_hashes(path)
    return {'path': 'x.jsonl.gz' if kind == 'tracking' else 'x.json', 'size': len(raw), 'kind': kind,
            'git_blob_sha1': h['git_blob_sha1'], 'lfs_sha256': h['sha256']}


class Tests(unittest.TestCase):
    def test_manifest(self):
        m = load_manifest(); validate_manifest(m)
        self.assertEqual(sha(load_license()), m['license']['sha256'])
    def test_manifest_extra_game(self):
        m = load_manifest(); m['games'].append(999999)
        with self.assertRaises(ValueError): validate_manifest(m)
    def test_manifest_url_tamper(self):
        m = load_manifest(); m['assets'][0]['url'] += '?token=x'
        with self.assertRaises(ValueError): validate_manifest(m)
    def test_manifest_missing_lfs_sha(self):
        m = load_manifest(); next(a for a in m['assets'] if a['kind'] == 'tracking')['lfs_sha256'] = 'x'
        with self.assertRaises(ValueError): validate_manifest(m)
    def test_git_blob_hash(self):
        with tempfile.TemporaryDirectory() as t:
            p = Path(t) / 'x'; p.write_bytes(b'hello\n')
            self.assertEqual(file_hashes(p)['git_blob_sha1'], 'ce013625030ba8dba906f756967f9e9ca394464a')
    def test_lfs_pointer_rejected_as_tracking(self):
        with tempfile.TemporaryDirectory() as t:
            p = Path(t) / 'x'; a = fixture_asset(p, b'version https://git-lfs.github.com/spec/v1\n', 'tracking')
            with self.assertRaises((ValueError, gzip.BadGzipFile)): validate_asset(p, a, time.monotonic() + 20, lambda: None)
    def test_gzip_full_tracking(self):
        with tempfile.TemporaryDirectory() as t:
            p = Path(t) / 'x'; row = {'frameIdx': 1, 'homePlayers': [{'xyz': [0, 0, 0], 'playerId': 7, 'isDetected': 1}], 'awayPlayers': [], 'ball': {}}
            a = fixture_asset(p, gzip.compress(pack(row) + b'\n'), 'tracking')
            result = validate_asset(p, a, time.monotonic() + 20, lambda: None)
            self.assertEqual(result['frames'], 1); self.assertTrue(result['full_gzip_crc_checked'])
    def test_gzip_truncated(self):
        with tempfile.TemporaryDirectory() as t:
            p = Path(t) / 'x'; a = fixture_asset(p, gzip.compress(b'{}\n')[:-4], 'tracking')
            with self.assertRaises((ValueError, EOFError)): validate_asset(p, a, time.monotonic() + 20, lambda: None)
    def test_robots_longest_rule(self):
        self.assertTrue(robots_policy('User-agent: *\nDisallow: /a/\nAllow: /a/b', 'https://raw.githubusercontent.com/a/b')[0])
    def test_robots_deny(self):
        self.assertFalse(robots_policy('User-agent: *\nDisallow: /', 'https://raw.githubusercontent.com/a')[0])
    def test_http_denial_suspends(self):
        m = load_manifest(); f = Fetcher(m, time.monotonic() + 100, 600000000, 100); f.opener = mock.Mock()
        url = m['assets'][0]['url']; f.opener.open.side_effect = urllib.error.HTTPError(url, 403, 'denied', {}, None)
        with tempfile.TemporaryDirectory() as t:
            with self.assertRaises(urllib.error.HTTPError): f.fetch(url, Path(t) / 'x')
            with self.assertRaises(BoundedStop): f.fetch(url, Path(t) / 'x')
            self.assertEqual(f.opener.open.call_count, 1)
    def test_streaming_budget(self):
        m = load_manifest(); f = Fetcher(m, time.monotonic() + 100, 5, 100); f.opener = mock.Mock()
        r = io.BytesIO(b'abcdef'); r.headers = {}; f.opener.open.return_value = r
        with tempfile.TemporaryDirectory() as t:
            with self.assertRaises(BoundedStop): f.fetch(m['assets'][0]['url'], Path(t) / 'x')
            self.assertLessEqual(f.bytes, 6)
    def test_bounds(self):
        validate_bounds(argparse.Namespace(max_seconds=1200, max_bytes=600000000, max_requests=100))
        with self.assertRaises(ValueError): validate_bounds(argparse.Namespace(max_seconds=1201, max_bytes=600000000, max_requests=100))
    def test_changed_source_hash(self):
        with tempfile.TemporaryDirectory() as t:
            p = Path(t) / 'x'; a = fixture_asset(p, b'{"a":1}'); a['git_blob_sha1'] = '0' * 40
            with self.assertRaises(ValueError): validate_asset(p, a, time.monotonic() + 20, lambda: None)
    def test_metadata_wrong_league(self):
        with tempfile.TemporaryDirectory() as t:
            p = Path(t) / 'x'; a = fixture_asset(p, b'{"gameId":1,"competitionName":"NBA","seasonName":"2025-2026"}', 'game_metadata'); a['game_id'] = 1
            with self.assertRaises(ValueError): validate_asset(p, a, time.monotonic() + 20, lambda: None)
    def test_full_run_one_bundle_scope_and_reuse(self):
        m = load_manifest(); objects, records, fetched = {}, {}, []
        class MemoryStore:
            def __init__(self, *a): pass
            def put(self, key, raw, content_type='application/json'):
                objects[key] = raw
                if '/url-index/' in key:
                    r = json.loads(raw); records[(r['commit'], r['source_path'])] = r
            def upload(self, path, key, mime): objects[key] = path.read_bytes()
            def download(self, key, path): path.write_bytes(objects[key])
            def cached(self): return dict(records)
        class FakeFetcher:
            def __init__(self, *a): self.calls, self.bytes, self.blocked = 0, 0, set()
            def get(self, a, path, report, store):
                self.calls += 1; fetched.append(a['path']); path.write_bytes(a['path'].encode()); self.bytes += path.stat().st_size
                return {}
        def fake_validation(path, a, deadline, beat):
            return {'sha256': m['license']['sha256'] if a['path'] == 'LICENSE' else sha(path.read_bytes()), 'bytes': path.stat().st_size}
        with tempfile.TemporaryDirectory() as tmp:
            a = argparse.Namespace(bucket='test', region='test', max_seconds=1200, max_bytes=600000000, max_requests=100, hourly_usd=.461, output_dir=tmp)
            with mock.patch.object(sys.modules[__name__], 'Store', MemoryStore), mock.patch.object(sys.modules[__name__], 'Fetcher', FakeFetcher), mock.patch.object(sys.modules[__name__], 'validate_asset', side_effect=fake_validation), mock.patch('builtins.print'):
                self.assertEqual(run(a), 0); self.assertEqual(run(a), 0)
            bundles = list(Path(tmp).glob('*_return.zip')); self.assertEqual(len(bundles), 2)
            self.assertEqual(len(fetched), 60)
            totals = []
            for bundle in bundles:
                with zipfile.ZipFile(bundle) as z: r = json.loads(z.read('report.json'))
                self.assertEqual(len(r['tracking_games']), 10); self.assertFalse(r['raw_video_included']); self.assertFalse(r['point_in_time_approved'])
                totals.append((r['downloaded_raw_files'], r['reused_raw_files']))
            self.assertEqual(sorted(totals), [(0, 32), (32, 0)])


def validate_bounds(a):
    if not (90 <= a.max_seconds <= 1200 and 1 <= a.max_bytes <= 600000000 and 1 <= a.max_requests <= 100):
        raise ValueError('bounds_out_of_range')


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--bucket', default='sagemaker-sports-edge-lab-560403859723-us-west-2')
    p.add_argument('--region', default='us-west-2')
    p.add_argument('--max-seconds', type=int, default=1200)
    p.add_argument('--max-bytes', type=int, default=600000000)
    p.add_argument('--max-requests', type=int, default=100)
    p.add_argument('--hourly-usd', type=float, default=.461)
    p.add_argument('--output-dir', default='/opt/ml/processing/output')
    p.add_argument('--self-test', action='store_true')
    a = p.parse_args(); validate_bounds(a)
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
    if not result.wasSuccessful(): return 2
    print(json.dumps({'event': 'SELF_TEST_PASSED', 'tests': result.testsRun, 'at': utc()}), flush=True)
    if a.self_test: return 0
    return run(a)


if __name__ == '__main__':
    sys.exit(main())
