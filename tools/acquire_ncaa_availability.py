#!/usr/bin/env python3
"""Bounded original American Conference availability image acquisition.

Eight observed official pages; no enumeration, no NCAA/HDI wall bypass.
Raw images remain unavailable as historical model features pending timestamps,
OCR, identity joins and pregame cutoff verification.
"""
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
import struct
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
import zlib

UTC = dt.timezone.utc
UA = 'SportsEdgeLabResearch/1.3 (+https://github.com/alvaromendizabal/sports-edge-lab)'
HOST = 'theamerican.org'
OBSERVED_VISIT_RULE = 'User-agent: *\nVisit-time: 0100-0645'
PREFIX = 'shared/acquisition/ncaa-availability/'
BASES = {t: 'tracks/' + t + '/raw/american-availability/' for t in ('ncaam', 'ncaaw')}


def utc():
    return dt.datetime.now(UTC).isoformat(timespec='seconds').replace('+00:00', 'Z')


def pack(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':')).encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def is_page(url):
    p = urllib.parse.urlsplit(url)
    return (p.scheme == 'https' and p.netloc == HOST and not p.query and not p.fragment
            and re.fullmatch(r'/sports/2026/\d{1,2}/\d{1,2}/[mw]bb_pa_\d{4,6}\.aspx', p.path) is not None)


def is_report(url):
    p = urllib.parse.urlsplit(url)
    if p.scheme != 'https' or p.netloc != HOST or p.fragment or p.path != '/common/controls/image_handler.aspx':
        return False
    q = urllib.parse.parse_qs(p.query, keep_blank_values=True)
    return (set(q) == {'thumb_id', 'image_path'} and q['thumb_id'] == ['0']
            and len(q['image_path']) == 1 and re.fullmatch(
                r'/images/2026/\d{1,2}/\d{1,2}/[mw]bb_pa_\d{4,6}(?:_\d+)?\.png', q['image_path'][0]) is not None)


def report_track(url):
    q = urllib.parse.parse_qs(urllib.parse.urlsplit(url).query)
    return 'ncaaw' if q['image_path'][0].rsplit('/', 1)[-1].startswith('wbb_') else 'ncaam'


class Links(HTMLParser):
    def __init__(self, source):
        super().__init__()
        self.source, self.reports = source, set()

    def handle_starttag(self, tag, attrs):
        if tag != 'img': return
        for key, value in attrs:
            if key == 'src' and value:
                url = urllib.parse.urljoin(self.source, unescape(value))
                if is_report(url): self.reports.add(url)


def robots_rules(text, agent=UA):
    groups, agents, rules = [], [], []
    def finish():
        if agents: groups.append((agents[:], rules[:]))
    for line in text.splitlines():
        line = line.split('#', 1)[0].strip()
        if ':' not in line: continue
        key, value = [s.strip() for s in line.split(':', 1)]
        key = key.lower()
        if key == 'user-agent':
            if rules:
                finish(); agents, rules = [], []
            agents.append(value.lower())
        elif agents and key in ('allow', 'disallow', 'crawl-delay', 'visit-time'):
            rules.append((key, value))
    finish()
    matches = [(max((len(a) for a in names if a != '*' and a in agent.lower()), default=0), rs)
               for names, rs in groups if '*' in names or any(a in agent.lower() for a in names)]
    longest = max((n for n, _ in matches), default=-1)
    return [r for n, rs in matches if n == longest for r in rs]


def robots_policy(text, url, agent=UA):
    selected = robots_rules(text, agent)
    p = urllib.parse.urlsplit(url)
    target = p.path + ('?' + p.query if p.query else '')
    decisions, delay = [], 5.0
    for kind, pattern in selected:
        if kind == 'crawl-delay':
            try: delay = max(delay, float(pattern))
            except ValueError: pass
        elif kind in ('allow', 'disallow') and pattern:
            end = pattern.endswith('$')
            body = pattern[:-1] if end else pattern
            regex = '^' + re.escape(body).replace(r'\*', '.*') + ('$' if end else '')
            if re.search(regex, target): decisions.append((len(body.replace('*', '')), kind == 'allow'))
    return max(decisions, default=(0, True))[1], delay


def visit_time_policy(text, now=None):
    """Honor optional historical robots Visit-time using its GMT/UTC convention.

    The source does not state a timezone; this convention is recorded explicitly.
    Malformed/ambiguous windows fail closed. End is exclusive.
    """
    now = now or dt.datetime.now(UTC)
    minute = now.astimezone(UTC).hour * 60 + now.astimezone(UTC).minute
    windows = [v for k, v in robots_rules(text) if k == 'visit-time']
    allowed = not windows
    for window in windows:
        m = re.fullmatch(r'(\d{2})(\d{2})-(\d{2})(\d{2})', window)
        if not m: raise ValueError('malformed_visit_time')
        sh, sm, eh, em = map(int, m.groups())
        if sh > 23 or eh > 23 or sm > 59 or em > 59: raise ValueError('malformed_visit_time')
        start, end = sh * 60 + sm, eh * 60 + em
        if start == end: raise ValueError('ambiguous_visit_time')
        inside = start <= minute < end if start < end else minute >= start or minute < end
        allowed = allowed or inside
    return allowed, {'windows': windows, 'timezone_convention': 'UTC/GMT; source does not state timezone',
                     'observed_utc': now.isoformat(), 'end_exclusive': True}


def validate_robots(text):
    if re.search(r'<\s*(?:html|!doctype|body)\b', text, re.I) or not re.search(
            r'^\s*user-agent\s*:\s*\S+', text, re.I | re.M):
        raise ValueError('invalid_robots_document')


def validate_png(raw):
    if not raw.startswith(b'\x89PNG\r\n\x1a\n'): raise ValueError('not_png')
    offset, kinds, dims = 8, [], None
    while offset < len(raw):
        if offset + 12 > len(raw): raise ValueError('png_truncated')
        size = struct.unpack('>I', raw[offset:offset + 4])[0]
        kind = raw[offset + 4:offset + 8]
        end = offset + 12 + size
        if end > len(raw): raise ValueError('png_truncated_chunk')
        data = raw[offset + 8:offset + 8 + size]
        crc = struct.unpack('>I', raw[offset + 8 + size:end])[0]
        if zlib.crc32(kind + data) & 0xffffffff != crc: raise ValueError('png_crc_mismatch')
        if not kinds:
            if kind != b'IHDR' or size != 13: raise ValueError('png_missing_ihdr')
            dims = struct.unpack('>II', data[:8])
            if not all(100 <= d <= 20000 for d in dims): raise ValueError('png_dimensions_out_of_range')
        kinds.append(kind); offset = end
        if kind == b'IEND':
            if size or offset != len(raw): raise ValueError('png_invalid_iend')
            break
    if not kinds or kinds[-1] != b'IEND' or b'IDAT' not in kinds: raise ValueError('png_incomplete')
    return {'width': dims[0], 'height': dims[1], 'crc_checked': True}


class BoundedStop(Exception):
    pass


class DeferredWindow(BoundedStop):
    pass


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl): return None


class Fetcher:
    def __init__(self, limit, deadline, max_bytes):
        self.limit, self.deadline, self.max_bytes = limit, deadline, max_bytes
        self.calls, self.bytes, self.last = 0, 0, -1e12
        self.blocked, self.robots = False, None
        self.clock_utc = lambda: dt.datetime.now(UTC)
        self.opener = urllib.request.build_opener(NoRedirect)

    def raw(self, url, delay=5.):
        if not visit_time_policy(OBSERVED_VISIT_RULE, self.clock_utc())[0]:
            raise DeferredWindow('outside_previously_observed_visit_time_no_http')
        if not (is_page(url) or is_report(url) or url == 'https://' + HOST + '/robots.txt'):
            raise ValueError('source_not_allowlisted')
        if self.blocked: raise BoundedStop('source_suspended')
        pause = max(0., self.last + max(5., delay) - time.monotonic())
        remain = min(12 * 1024 * 1024, self.max_bytes - self.bytes)
        if self.calls >= self.limit or remain < 1 or time.monotonic() + pause + 20 >= self.deadline:
            raise BoundedStop('request_runtime_or_byte_bound')
        if pause: time.sleep(pause)
        if (not visit_time_policy(OBSERVED_VISIT_RULE, self.clock_utc())[0]
                or (self.robots is not None and not visit_time_policy(self.robots, self.clock_utc())[0])):
            raise DeferredWindow('visit_time_closed_while_pacing_no_http')
        self.calls += 1; self.last = time.monotonic()
        try:
            with self.opener.open(urllib.request.Request(url, headers={'User-Agent': UA, 'Accept': '*/*'}), timeout=15) as res:
                declared = res.headers.get('Content-Length')
                if declared and int(declared) > remain: raise BoundedStop('declared_response_exceeds_byte_budget')
                raw = res.read(remain + 1)
                self.bytes += len(raw)
                if len(raw) > remain: raise BoundedStop('response_exceeds_byte_budget')
                return raw, {k.lower(): v for k, v in res.headers.items()}
        except urllib.error.HTTPError as exc:
            if exc.code in (401, 403, 429): self.blocked = True
            exc.close(); raise

    def get(self, url, store, report):
        if self.robots is None:
            robots_url = 'https://' + HOST + '/robots.txt'
            try:
                raw, headers = self.raw(robots_url)
                text = raw.decode('utf-8', errors='replace'); validate_robots(text)
                report['evidence'].append(store.capture(robots_url, raw, headers, report['run_id'], 'robots'))
                self.robots = text
            except DeferredWindow:
                raise
            except Exception:
                self.blocked = True; raise
        allowed, delay = robots_policy(self.robots, url)
        if not allowed: raise BoundedStop('robots_disallowed')
        in_window, window = visit_time_policy(self.robots, self.clock_utc())
        report['source_visit_window'] = window
        if not in_window: raise DeferredWindow('outside_published_visit_time')
        return self.raw(url, delay)


class Store:
    def __init__(self, bucket, region):
        import boto3
        from botocore.config import Config
        self.bucket = bucket
        self.s3 = boto3.client('s3', region_name=region, config=Config(
            retries={'total_max_attempts': 3, 'mode': 'adaptive'}, connect_timeout=5, read_timeout=20))

    def get(self, key):
        with self.s3.get_object(Bucket=self.bucket, Key=key)['Body'] as body: return body.read()

    def put(self, key, raw, content_type='application/json'):
        self.s3.upload_fileobj(io.BytesIO(raw), self.bucket, key, ExtraArgs={
            'ContentType': content_type, 'ServerSideEncryption': 'AES256'})

    def cached(self):
        existing, count = {}, 0
        for base in BASES.values():
            for page in self.s3.get_paginator('list_objects_v2').paginate(Bucket=self.bucket, Prefix=base + 'url-index/'):
                for obj in page.get('Contents', []):
                    count += 1
                    if count > 500: raise ValueError('source_index_bound')
                    if obj['Key'].endswith('.json'):
                        r = json.loads(self.get(obj['Key']))
                        if is_report(r.get('url', '')) and r.get('raw_key') and r.get('sha256'):
                            existing[r['url']] = r
        return existing

    def capture(self, url, raw, headers, run_id, kind, track=None):
        digest, stamp = sha(raw), utc()
        base = BASES[track] if kind == 'png' else PREFIX + 'evidence/'
        key = base + 'objects/' + digest + ('.png.gz' if kind == 'png' else '.txt.gz')
        self.put(key, gzip.compress(raw, compresslevel=6, mtime=0), 'application/gzip')
        return {'url': url, 'raw_key': key, 'sha256': digest, 'bytes': len(raw), 'captured_at': stamp,
                'run_id': run_id, 'kind': kind, 'track': track, 'status': 'downloaded',
                'upstream_last_modified': headers.get('last-modified'), 'upstream_http_date': headers.get('date'),
                'historical_available_at': None, 'point_in_time_approved': False}


def load_seeds():
    if zipfile.is_zipfile(sys.argv[0]):
        with zipfile.ZipFile(sys.argv[0]) as z: return json.loads(z.read('ncaa_availability_seeds.json'))
    return json.loads(Path(__file__).with_name('ncaa_availability_seeds.json').read_text())


def run(args):
    started = time.monotonic()
    run_id = dt.datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid.uuid4().hex[:10]
    store = Store(args.bucket, args.region)
    fetcher = Fetcher(args.max_requests, started + args.max_seconds - 30, args.max_bytes)
    report = {'run_id': run_id, 'started_at': utc(), 'status': 'running', 'receipts': [], 'evidence': [],
              'errors': [], 'pending': [], 'historical_coverage_complete': False, 'point_in_time_approved': False,
              'tests': {'passed': True, 'count': 23}, 'conference': 'American Conference',
              'preflight_visit_window': {'windows': ['0100-0645'], 'timezone': 'UTC/GMT',
                  'source': 'Previously observed official robots.txt; honored before any HTTP, then refreshed inside window.',
                  'directive_reference': 'https://www.conman.org/people/spc/robots2.html'},
              'scope': 'Eight observed official daily pages: six men and two women, January–March 2026; sparse sample.',
              'bounds': {'requests': args.max_requests, 'seconds': args.max_seconds, 'bytes': args.max_bytes},
              'blocked_other_sources': {'ncaa_national': 'PAReports robot verification wall; not bypassed',
                                        'conference_usa': '/documents/ disallowed by robots; no alternative-host substitution'}}
    prefix = PREFIX + run_id + '/'
    def progress():
        report.update(updated_at=utc(), requests=fetcher.calls, http_bytes=fetcher.bytes,
                      elapsed_seconds=round(time.monotonic() - started, 3), source_suspended=fetcher.blocked)
        report['estimated_compute_usd'] = round(report['elapsed_seconds'] / 3600 * args.hourly_usd, 6)
        for status in ('downloaded', 'reused'):
            report[status + '_images'] = sum(r['status'] == status for r in report['receipts'])
        store.put(prefix + 'progress.json', pack(report))
        print(json.dumps({k: report[k] for k in ('updated_at', 'status', 'requests', 'downloaded_images',
                     'reused_images', 'http_bytes', 'elapsed_seconds', 'estimated_compute_usd')}), flush=True)
    existing = store.cached()
    seeds = load_seeds()
    if len(seeds) > 30 or any(not is_page(x['url']) for x in seeds): raise ValueError('invalid_page_seed_scope')
    for i, page in enumerate(seeds):
        url = page['url']
        try:
            raw, headers = fetcher.get(url, store, report)
            text = raw.decode('utf-8', errors='replace')
            if 'Player Availability Report' not in text or re.search('verify that you.re not a robot', text, re.I):
                raise ValueError('unexpected_landing_or_challenge')
            evidence = store.capture(url, raw, headers, run_id, 'landing', page['track'])
            evidence['discovery'] = page['discovery']; report['evidence'].append(evidence)
            links = Links(url); links.feed(text)
            if not 1 <= len(links.reports) <= 4: raise ValueError('unexpected_report_image_count')
            for image_url in sorted(links.reports):
                if report_track(image_url) != page['track']: raise ValueError('track_mismatch')
                discovery = {'method': 'original_img_src', 'source': url, 'source_sha256': evidence['sha256'],
                             'observed_at': evidence['captured_at']}
                if image_url in existing:
                    receipt = existing[image_url]
                    cached = gzip.decompress(store.get(receipt['raw_key']))
                    if sha(cached) != receipt['sha256']: raise ValueError('cache_sha256_mismatch')
                    validate_png(cached)
                    report['receipts'].append({**receipt, 'status': 'reused', 'discovery': discovery})
                    continue
                image_bytes, image_headers = fetcher.get(image_url, store, report)
                validation = validate_png(image_bytes)
                receipt = store.capture(image_url, image_bytes, image_headers, run_id, 'png', page['track'])
                receipt.update(discovery=discovery, image_validation=validation,
                               validation_required='OCR; verify report vintage/timezone; resolve player/game IDs and pregame cutoff.')
                store.put(BASES[page['track']] + 'url-index/' + sha(image_url.encode()) + '.json', pack(receipt))
                existing[image_url] = receipt; report['receipts'].append(receipt)
        except BoundedStop as exc:
            if isinstance(exc, DeferredWindow): report['deferred_source_window'] = True
            report['pending'].extend(x['url'] for x in seeds[i:])
            report['errors'].append({'url': url, 'error': type(exc).__name__, 'reason': str(exc)})
            break
        except Exception as exc:
            report['errors'].append({'url': url, 'error': type(exc).__name__, 'http_status': getattr(exc, 'code', None),
                                     'reason': str(exc)[:240]})
            report['pending'].append(url)
            if fetcher.blocked:
                report['pending'].extend(x['url'] for x in seeds[i + 1:]); break
        progress()
    report['pending'] = sorted(set(report['pending']))
    report['status'] = ('deferred_source_window' if report.get('deferred_source_window') else
                        ('completed_observed_pages' if not report['pending'] else 'partial'))
    report['completed_at'] = utc(); progress()
    store.put(prefix + 'report.json', pack(report))
    out = Path(args.output_dir); out.mkdir(parents=True, exist_ok=True)
    target = out / ('sports_edge_lab_ncaa_availability_' + run_id + '_return.zip')
    with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('report.json', pack(report))
        z.writestr('resume.json', pack({'pending_pages': report['pending'], 'source_bases': BASES}))
        z.writestr('provenance_seeds.json', pack(seeds))
    store.put(prefix + target.name, target.read_bytes(), 'application/zip')
    print(json.dumps({'report_key': prefix + 'report.json', 'return_zip': str(target),
                      'return_sha256': sha(target.read_bytes())}), flush=True)
    return 0 if report['status'] in ('completed_observed_pages', 'deferred_source_window') else 2


PAGE = 'https://theamerican.org/sports/2026/3/14/wbb_pa_031426.aspx'
IMAGE = 'https://theamerican.org/common/controls/image_handler.aspx?thumb_id=0&image_path=/images/2026/3/14/wbb_pa_031426.png'


def png_fixture():
    def chunk(k, d): return struct.pack('>I', len(d)) + k + d + struct.pack('>I', zlib.crc32(k + d) & 0xffffffff)
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', 100, 100, 8, 2, 0, 0, 0))
            + chunk(b'IDAT', zlib.compress((b'\x00' + b'\x00' * 300) * 100)) + chunk(b'IEND', b''))


class Tests(unittest.TestCase):
    def test_page(self): self.assertTrue(is_page(PAGE))
    def test_only_report_src(self):
        p = Links(PAGE); p.feed('<img src="' + IMAGE.replace('&', '&amp;') + '"><img src="/images/logo.png">')
        self.assertEqual(p.reports, {IMAGE})
    def test_direct_image_rejected(self): self.assertFalse(is_report('https://theamerican.org/images/2026/3/14/wbb_pa_031426.png'))
    def test_external_rejected(self): self.assertFalse(is_report(IMAGE.replace('theamerican.org', 'theamerican.org.evil.test')))
    def test_unexpected_query_rejected(self): self.assertFalse(is_report(IMAGE + '&secret=1'))
    def test_robots_restrictions(self):
        txt = 'User-agent: *\nDisallow: /images/\nDisallow: /documents/\nAllow: /\nCrawl-delay: 5'
        self.assertTrue(robots_policy(txt, IMAGE)[0]); self.assertFalse(robots_policy(txt, 'https://theamerican.org/documents/a.pdf')[0])
    def test_robots_wildcards(self): self.assertFalse(robots_policy('User-agent: *\nDisallow: /*?*', IMAGE)[0])
    def test_robots_invalid(self):
        with self.assertRaises(ValueError): validate_robots('<html>robot</html>')
    def test_png_valid(self): self.assertEqual(validate_png(png_fixture())['width'], 100)
    def test_png_bad_crc(self):
        with self.assertRaises(ValueError): validate_png(png_fixture()[:-5] + b'abcde')
    def test_png_truncated(self):
        with self.assertRaises(ValueError): validate_png(png_fixture()[:-12])
    def test_html_not_png(self):
        with self.assertRaises(ValueError): validate_png(b'<html>denied</html>')
    def test_denial_stops_host(self):
        f = Fetcher(20, time.monotonic() + 100, 10000); f.opener = mock.Mock()
        f.clock_utc = lambda: dt.datetime(2026, 10, 17, 2, 0, tzinfo=UTC)
        f.opener.open.side_effect = urllib.error.HTTPError(PAGE, 403, 'Forbidden', {}, None)
        with self.assertRaises(urllib.error.HTTPError): f.raw(PAGE)
        with self.assertRaises(BoundedStop): f.raw(PAGE)
        self.assertEqual(f.opener.open.call_count, 1)
    def test_declared_byte_bound(self):
        f = Fetcher(20, time.monotonic() + 100, 100); f.opener = mock.Mock()
        f.clock_utc = lambda: dt.datetime(2026, 10, 17, 2, 0, tzinfo=UTC)
        response = io.BytesIO(b'abcdef'); response.headers = {'Content-Length': '101'}
        f.opener.open.return_value = response
        with self.assertRaises(BoundedStop): f.raw(PAGE)
        self.assertEqual(f.bytes, 0)
    def test_spacing(self):
        clock, calls = [10.], []
        def response(*a, **kw):
            calls.append(clock[0]); r = io.BytesIO(b'ok'); r.headers = {}; return r
        f = Fetcher(20, 500, 10000); f.opener = mock.Mock(); f.opener.open.side_effect = response
        f.clock_utc = lambda: dt.datetime(2026, 10, 17, 2, 0, tzinfo=UTC)
        with mock.patch.object(time, 'monotonic', side_effect=lambda: clock[0]), mock.patch.object(time, 'sleep', side_effect=lambda s: clock.__setitem__(0, clock[0] + s)):
            f.raw(PAGE); f.raw(PAGE, 8.)
        self.assertEqual(calls, [10., 18.])
    def test_full_capture_and_reuse_single_return_per_run(self):
        objects, index, fetches = {}, {}, []
        class MemoryStore:
            def __init__(self, *a): pass
            def get(self, key): return objects[key]
            def put(self, key, raw, content_type='application/json'):
                objects[key] = raw
                if '/url-index/' in key:
                    receipt = json.loads(raw); index[receipt['url']] = receipt
            def cached(self): return dict(index)
            capture = Store.capture
        class FakeFetcher:
            def __init__(self, *a): self.calls, self.bytes, self.blocked = 0, 0, False
            def get(self, url, store, report):
                fetches.append(url); self.calls += 1
                raw = (b'Player Availability Report <img src="' + IMAGE.encode() + b'">') if url == PAGE else png_fixture()
                self.bytes += len(raw); return raw, {}
        with tempfile.TemporaryDirectory() as tmp:
            args = argparse.Namespace(bucket='test', region='test', max_requests=200, max_seconds=600,
                                      max_bytes=100000000, hourly_usd=.461, output_dir=tmp)
            with mock.patch.object(sys.modules[__name__], 'Store', MemoryStore), mock.patch.object(sys.modules[__name__], 'Fetcher', FakeFetcher), mock.patch.object(sys.modules[__name__], 'load_seeds', return_value=[{'url': PAGE, 'track': 'ncaaw', 'discovery': {'method': 'fixture'}}]), mock.patch('builtins.print'):
                self.assertEqual(run(args), 0)
                self.assertEqual(run(args), 0)
            bundles = list(Path(tmp).glob('*_return.zip'))
            self.assertEqual(len(bundles), 2)
            self.assertEqual(fetches.count(IMAGE), 1)
            counts = []
            for bundle in bundles:
                with zipfile.ZipFile(bundle) as z:
                    report = json.loads(z.read('report.json'))
                    counts.append((report['downloaded_images'], report['reused_images']))
                    self.assertFalse(report['point_in_time_approved'])
            self.assertEqual(sorted(counts), [(0, 1), (1, 0)])
    def test_cli_bounds(self):
        validate_bounds(argparse.Namespace(max_seconds=600, max_requests=200, max_bytes=100000000))
        with self.assertRaises(ValueError):
            validate_bounds(argparse.Namespace(max_seconds=601, max_requests=200, max_bytes=100000000))
    def test_visit_time_boundaries(self):
        text = 'User-agent: *\nVisit-time: 0100-0645'
        for hour, minute, expected in [(0, 59, False), (1, 0, True), (6, 44, True), (6, 45, False)]:
            self.assertEqual(visit_time_policy(text, dt.datetime(2026, 10, 17, hour, minute, tzinfo=UTC))[0], expected)
    def test_visit_time_overnight(self):
        text = 'User-agent: *\nVisit-time: 2300-0200'
        self.assertTrue(visit_time_policy(text, dt.datetime(2026, 10, 17, 1, 0, tzinfo=UTC))[0])
        self.assertFalse(visit_time_policy(text, dt.datetime(2026, 10, 17, 12, 0, tzinfo=UTC))[0])
    def test_visit_time_malformed(self):
        for value in ('2500-2600', '0100-0100', 'not-a-window'):
            with self.assertRaises(ValueError): visit_time_policy('User-agent: *\nVisit-time: ' + value)
    def test_observed_window_prevents_all_http(self):
        f = Fetcher(20, time.monotonic() + 100, 10000); f.opener = mock.Mock()
        f.clock_utc = lambda: dt.datetime(2026, 10, 17, 12, 0, tzinfo=UTC)
        with self.assertRaises(DeferredWindow): f.raw('https://' + HOST + '/robots.txt')
        with self.assertRaises(DeferredWindow): f.raw(PAGE)
        self.assertEqual(f.opener.open.call_count, 0)
        self.assertEqual(f.calls, 0)
    def test_visit_time_multiple_windows_are_union(self):
        text = 'User-agent: *\nVisit-time: 0100-0200\nVisit-time: 0400-0500'
        for hour, expected in [(1, True), (3, False), (4, True)]:
            self.assertEqual(visit_time_policy(text, dt.datetime(2026, 10, 17, hour, 30, tzinfo=UTC))[0], expected)
    def test_visit_window_rechecked_after_pacing(self):
        clock = [10.]
        stamp = [dt.datetime(2026, 10, 17, 6, 44, 59, tzinfo=UTC)]
        f = Fetcher(20, 500, 10000); f.opener = mock.Mock(); f.last = 10.
        f.clock_utc = lambda: stamp[0]
        def sleep(seconds):
            clock[0] += seconds; stamp[0] += dt.timedelta(seconds=seconds)
        with mock.patch.object(time, 'monotonic', side_effect=lambda: clock[0]), mock.patch.object(time, 'sleep', side_effect=sleep):
            with self.assertRaises(DeferredWindow): f.raw(PAGE)
        self.assertEqual(f.opener.open.call_count, 0)
        self.assertEqual(f.calls, 0)


def validate_bounds(a):
    if not (90 <= a.max_seconds <= 600 and 1 <= a.max_requests <= 200 and 1 <= a.max_bytes <= 100_000_000):
        raise ValueError('bound_out_of_range')


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--bucket', default='sagemaker-sports-edge-lab-560403859723-us-west-2')
    p.add_argument('--region', default='us-west-2')
    p.add_argument('--max-seconds', type=int, default=600)
    p.add_argument('--max-requests', type=int, default=200)
    p.add_argument('--max-bytes', type=int, default=100_000_000)
    p.add_argument('--hourly-usd', type=float, default=.461)
    p.add_argument('--output-dir', default='/opt/ml/processing/output')
    p.add_argument('--self-test', action='store_true')
    a = p.parse_args()
    validate_bounds(a)
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
    if not result.wasSuccessful(): return 2
    print(json.dumps({'event': 'SELF_TEST_PASSED', 'tests': result.testsRun, 'at': utc()}), flush=True)
    if a.self_test: return 0
    return run(a)


if __name__ == '__main__':
    sys.exit(main())
