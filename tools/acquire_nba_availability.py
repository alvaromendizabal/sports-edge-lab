#!/usr/bin/env python3
"""Capture original NBA injury PDFs with observed links, provenance and bounds.

Only actual discovered URLs are requested. Historical timestamps are not approved
as model features until the report header, timezone and game joins are validated.
"""
import argparse
import datetime as dt
import gzip
import hashlib
from html import unescape
from html.parser import HTMLParser
import importlib.resources
import io
import json
from pathlib import Path
import re
import sys
import time
import unittest
from unittest import mock
import urllib.error
import urllib.parse
import urllib.request
import uuid
import zipfile

UTC = dt.timezone.utc
UA = 'SportsEdgeLabResearch/1.2 (+https://github.com/alvaromendizabal/sports-edge-lab)'
LANDING = 'https://official.nba.com/nba-injury-report-2025-26-season/'
BASE = 'tracks/nba/raw/nba-official-injuries/'
PDF_PATH = re.compile(r'/referee/injury/Injury-Report_\d{4}-\d{2}-\d{2}_\d{2}(?:_\d{2})?[AP]M\.pdf')


def utc():
    return dt.datetime.now(UTC).isoformat(timespec='seconds').replace('+00:00', 'Z')


def pack(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':')).encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def is_report(url):
    p = urllib.parse.urlsplit(url)
    return (p.scheme == 'https' and p.netloc == 'ak-static.cms.nba.com'
            and not p.query and not p.fragment and bool(PDF_PATH.fullmatch(p.path)))


class Links(HTMLParser):
    def __init__(self, source):
        super().__init__()
        self.source, self.reports, self.pages = source, set(), set()

    def handle_starttag(self, tag, attrs):
        for key, value in attrs:
            if key not in ('href', 'src') or not value:
                continue
            url = urllib.parse.urljoin(self.source, unescape(value))
            if is_report(url):
                self.reports.add(url)
            p = urllib.parse.urlsplit(url)
            if (tag == 'a' and p.scheme == 'https' and p.netloc == 'official.nba.com'
                    and not p.query and not p.fragment and re.fullmatch(
                        r'/nba-injury-report-\d{4}-\d{2}-season/?', p.path)):
                self.pages.add(url)


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


def validate_bounds(args):
    for name, low, high in [('max_seconds', 90, 600), ('max_requests', 1, 300),
                            ('max_reports', 1, 250), ('max_pages', 1, 4)]:
        if not low <= getattr(args, name) <= high:
            raise ValueError('bounds:' + name + ':' + str(low) + '..' + str(high))


class BoundedStop(Exception):
    pass


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class Fetcher:
    def __init__(self, requests, deadline):
        self.limit, self.deadline, self.calls = requests, deadline, 0
        self.blocked, self.robots, self.last = set(), {}, {}
        self.opener = urllib.request.build_opener(NoRedirect)

    def raw(self, url, delay=1.0):
        p = urllib.parse.urlsplit(url)
        host = p.hostname
        if p.scheme != 'https' or p.netloc not in ('official.nba.com', 'ak-static.cms.nba.com'):
            raise ValueError('source_not_allowlisted')
        if host in self.blocked:
            raise BoundedStop('source_suspended:' + host)
        pause = max(0., self.last.get(host, -1e12) + max(1., delay) - time.monotonic())
        if self.calls >= self.limit or time.monotonic() + pause + 18 >= self.deadline:
            raise BoundedStop('request_or_runtime_bound')
        if pause: time.sleep(pause)
        self.calls += 1
        self.last[host] = time.monotonic()
        req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept': '*/*'})
        try:
            with self.opener.open(req, timeout=15) as res:
                raw = res.read(12 * 1024 * 1024 + 1)
                if len(raw) > 12 * 1024 * 1024:
                    raise ValueError('response_over_12MiB')
                return raw, {k.lower(): v for k, v in res.headers.items()}
        except urllib.error.HTTPError as exc:
            if exc.code in (401, 403, 429): self.blocked.add(host)
            exc.close()
            raise

    def get(self, url, store, report):
        host = urllib.parse.urlsplit(url).hostname
        if host not in self.robots:
            robots_url = 'https://' + host + '/robots.txt'
            try:
                body, headers = self.raw(robots_url)
                text = body.decode('utf-8', errors='replace')
                validate_robots(text)
                receipt = store.capture_bytes(robots_url, body, headers, report['run_id'], 'robots')
                report['evidence'].append(receipt)
                self.robots[host] = text
            except Exception:
                self.blocked.add(host)
                raise
        allowed, delay = robots_policy(self.robots[host], url)
        if not allowed:
            raise BoundedStop('robots_disallowed:' + url)
        return self.raw(url, delay)


class Store:
    def __init__(self, bucket, region):
        import boto3
        from botocore.config import Config
        self.bucket = bucket
        self.s3 = boto3.client('s3', region_name=region, config=Config(
            retries={'total_max_attempts': 3, 'mode': 'adaptive'}, connect_timeout=5, read_timeout=20))

    def get(self, key):
        with self.s3.get_object(Bucket=self.bucket, Key=key)['Body'] as body:
            return body.read()

    def put(self, key, raw, content_type='application/json'):
        self.s3.upload_fileobj(io.BytesIO(raw), self.bucket, key, ExtraArgs={
            'ContentType': content_type, 'ServerSideEncryption': 'AES256'})

    def cached(self):
        """Read only this small source's index receipts; never load raw corpus."""
        existing, count = {}, 0
        for prefix in (BASE + 'request-index/', BASE + 'url-index/'):
            for page in self.s3.get_paginator('list_objects_v2').paginate(Bucket=self.bucket, Prefix=prefix):
                for obj in page.get('Contents', []):
                    count += 1
                    if count > 10000: raise ValueError('source_index_limit')
                    if not obj['Key'].endswith('.json'): continue
                    item = json.loads(self.get(obj['Key']))
                    if is_report(item.get('url', '')) and item.get('raw_key'):
                        existing[item['url']] = item
        return existing

    def capture_bytes(self, url, raw, headers, run_id, kind):
        digest, stamp = sha(raw), utc()
        base = BASE if kind == 'pdf' else 'shared/acquisition/nba-availability/evidence/'
        raw_key = base + 'objects/' + digest + ('.pdf.gz' if kind == 'pdf' else '.txt.gz')
        self.put(raw_key, gzip.compress(raw, compresslevel=6, mtime=0), 'application/gzip')
        return {'url': url, 'raw_key': raw_key, 'sha256': digest, 'bytes': len(raw),
                'captured_at': stamp, 'run_id': run_id, 'kind': kind,
                'upstream_last_modified': headers.get('last-modified'),
                'upstream_http_date': headers.get('date'), 'historical_available_at': None,
                'status': 'downloaded', 'point_in_time_approved': False}


def load_seeds():
    if zipfile.is_zipfile(sys.argv[0]):
        with zipfile.ZipFile(sys.argv[0]) as z:
            return json.loads(z.read('nba_report_seeds.json'))
    return json.loads(Path(__file__).with_name('nba_report_seeds.json').read_text())


def validate_pdf(raw):
    if not raw.startswith(b'%PDF-') or b'%%EOF' not in raw[-4096:]:
        raise ValueError('invalid_pdf_framing')


def run(args):
    started = time.monotonic()
    run_id = dt.datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid.uuid4().hex[:10]
    store, fetcher = Store(args.bucket, args.region), Fetcher(args.max_requests, started + args.max_seconds - 30)
    report = {'run_id': run_id, 'started_at': utc(), 'status': 'running', 'receipts': [],
              'evidence': [], 'errors': [], 'pending': [], 'historical_coverage_complete': False,
              'point_in_time_approved': False, 'tests': {'passed': True, 'count': 13},
              'bounds': {'requests': args.max_requests, 'seconds': args.max_seconds,
                         'reports': args.max_reports, 'pages': args.max_pages},
              'scope': 'Published official links and observed search-result URLs only; no filename enumeration.'}
    prefix = 'shared/acquisition/nba-availability/' + run_id + '/'
    def progress():
        report['updated_at'] = utc()
        report['requests'] = fetcher.calls
        report['elapsed_seconds'] = round(time.monotonic() - started, 3)
        report['estimated_compute_usd'] = round(report['elapsed_seconds'] / 3600 * args.hourly_usd, 6)
        report['downloaded_pdfs'] = sum(x['status'] == 'downloaded' for x in report['receipts'])
        report['reused_pdfs'] = sum(x['status'] == 'reused' for x in report['receipts'])
        report['blocked_hosts'] = sorted(fetcher.blocked)
        store.put(prefix + 'progress.json', pack(report))
        print(json.dumps({k: report[k] for k in ('updated_at', 'status', 'requests', 'downloaded_pdfs',
                                                'reused_pdfs', 'elapsed_seconds', 'estimated_compute_usd')}), flush=True)
    existing = store.cached()
    seeds = {x['url']: x['discovery'] for x in load_seeds() if is_report(x['url'])}
    queue, seen = [LANDING], set()
    while queue and len(seen) < args.max_pages:
        url = queue.pop(0)
        if url in seen: continue
        seen.add(url)
        try:
            raw, headers = fetcher.get(url, store, report)
            evidence = store.capture_bytes(url, raw, headers, run_id, 'landing')
            report['evidence'].append(evidence)
            parser = Links(url); parser.feed(raw.decode('utf-8', errors='replace'))
            for pdf in parser.reports:
                seeds.setdefault(pdf, {'method': 'official_page_link', 'source': url,
                                       'source_sha256': evidence['sha256'], 'observed_at': evidence['captured_at']})
            queue.extend(sorted(parser.pages - seen))
        except Exception as exc:
            report['errors'].append({'url': url, 'stage': 'discovery', 'error': type(exc).__name__,
                                     'http_status': getattr(exc, 'code', None), 'reason': str(exc)[:240]})
        progress()
    report['discovered_report_urls'] = len(seeds)
    report['landing_pages_processed'] = len(seen)
    ordered = sorted(seeds, reverse=True)
    for i, url in enumerate(ordered[:args.max_reports]):
        if url in existing:
            report['receipts'].append({**existing[url], 'status': 'reused', 'discovery': seeds[url]})
            continue
        try:
            raw, headers = fetcher.get(url, store, report)
            validate_pdf(raw)
            receipt = store.capture_bytes(url, raw, headers, run_id, 'pdf')
            receipt.update(discovery=seeds[url], published_timestamp_candidate=url.rsplit('/', 1)[-1],
                           validation_required='Extract header timestamp; resolve Eastern timezone; join game and cutoff.')
            store.put(BASE + 'url-index/' + sha(url.encode()) + '.json', pack(receipt))
            existing[url] = receipt
            report['receipts'].append(receipt)
        except BoundedStop as exc:
            report['pending'].extend(ordered[i:])
            report['errors'].append({'url': url, 'stage': 'capture', 'error': type(exc).__name__, 'reason': str(exc)})
            break
        except Exception as exc:
            report['errors'].append({'url': url, 'stage': 'capture', 'error': type(exc).__name__,
                                     'http_status': getattr(exc, 'code', None), 'reason': str(exc)[:240]})
        if (i + 1) % 5 == 0: progress()
    report['pending'] = sorted(set(report['pending'] + ordered[args.max_reports:]))
    report['status'] = 'completed_discovered_set' if not report['pending'] and not any(
        x['stage'] == 'capture' for x in report['errors']) else 'partial'
    report['completed_at'] = utc()
    report['next_gap'] = 'No complete historical public index was present in the observed landing HTML. Search-indexed PDFs are a sparse sample.'
    progress()
    store.put(prefix + 'report.json', pack(report))
    out = Path(args.output_dir); out.mkdir(parents=True, exist_ok=True)
    target = out / ('sports_edge_lab_nba_availability_' + run_id + '_return.zip')
    with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('report.json', pack(report))
        z.writestr('resume.json', pack({'pending_urls': report['pending'], 'source_url_index_prefix': BASE + 'url-index/'}))
        z.writestr('provenance.json', pack(seeds))
    store.put(prefix + target.name, target.read_bytes(), 'application/zip')
    print(json.dumps({'report_key': prefix + 'report.json', 'return_zip': str(target),
                      'return_sha256': sha(target.read_bytes())}), flush=True)
    return 0


class Tests(unittest.TestCase):
    def test_current_report(self):
        self.assertTrue(is_report('https://ak-static.cms.nba.com/referee/injury/Injury-Report_2026-03-04_04_45AM.pdf'))
    def test_old_report(self):
        self.assertTrue(is_report('https://ak-static.cms.nba.com/referee/injury/Injury-Report_2023-02-09_05PM.pdf'))
    def test_external_rejected(self):
        self.assertFalse(is_report('https://ak-static.cms.nba.com.evil.test/referee/injury/Injury-Report_2023-02-09_05PM.pdf'))
    def test_query_rejected(self):
        self.assertFalse(is_report('https://ak-static.cms.nba.com/referee/injury/Injury-Report_2023-02-09_05PM.pdf?x=1'))
    def test_pdf_validation(self):
        validate_pdf(b'%PDF-1.4\nbody\n%%EOF')
        with self.assertRaises(ValueError): validate_pdf(b'<html>denied</html>')
    def test_robots_query_wildcard(self):
        self.assertFalse(robots_policy('User-agent: *\nDisallow: /*?*', 'https://official.nba.com/x?q=1')[0])
    def test_robots_allow_specific(self):
        text = 'User-agent: *\nDisallow: /wp-admin/\nAllow: /wp-admin/admin-ajax.php\nCrawl-Delay: 2'
        self.assertEqual(robots_policy(text, 'https://official.nba.com/wp-admin/admin-ajax.php'), (True, 2.0))
    def test_robots_specific_group(self):
        text = 'User-agent: *\nDisallow: /\nUser-agent: SportsEdgeLabResearch\nAllow: /'
        self.assertTrue(robots_policy(text, LANDING)[0])
    def test_link_extraction(self):
        p = Links(LANDING)
        p.feed('<a href="https://ak-static.cms.nba.com/referee/injury/Injury-Report_2023-02-09_05PM.pdf">report</a>')
        self.assertEqual(len(p.reports), 1)
    def test_invalid_robots(self):
        with self.assertRaises(ValueError): validate_robots('<html>robot challenge</html>')
        with self.assertRaises(ValueError): validate_robots('')
        validate_robots('User-agent: *\nDisallow: /private/')
    def test_http_denial_suspends_next_request(self):
        f = Fetcher(20, time.monotonic() + 500)
        f.opener = mock.Mock()
        f.opener.open.side_effect = urllib.error.HTTPError(LANDING, 403, 'Forbidden', {}, None)
        with self.assertRaises(urllib.error.HTTPError): f.raw(LANDING)
        with self.assertRaises(BoundedStop): f.raw(LANDING)
        self.assertEqual(f.opener.open.call_count, 1)
    def test_delay_applies_after_learning_robots(self):
        clock = [10.0]
        calls = []
        def sleep(seconds): clock[0] += seconds
        def response(*args, **kwargs):
            calls.append(clock[0]); res = io.BytesIO(b'ok'); res.headers = {}; return res
        f = Fetcher(20, 500); f.opener = mock.Mock(); f.opener.open.side_effect = response
        with mock.patch.object(time, 'monotonic', side_effect=lambda: clock[0]), mock.patch.object(time, 'sleep', side_effect=sleep):
            f.raw(LANDING)
            f.raw(LANDING, delay=2)
        self.assertEqual(calls, [10.0, 12.0])
    def test_cli_bounds(self):
        args = argparse.Namespace(max_seconds=600, max_requests=300, max_reports=250, max_pages=4)
        validate_bounds(args)
        args.max_requests = 301
        with self.assertRaises(ValueError): validate_bounds(args)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--bucket', default='sagemaker-sports-edge-lab-560403859723-us-west-2')
    parser.add_argument('--region', default='us-west-2')
    parser.add_argument('--max-seconds', type=int, default=600)
    parser.add_argument('--max-requests', type=int, default=300)
    parser.add_argument('--max-reports', type=int, default=250)
    parser.add_argument('--max-pages', type=int, default=4)
    parser.add_argument('--hourly-usd', type=float, default=.461)
    parser.add_argument('--output-dir', default='/opt/ml/processing/output')
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    validate_bounds(args)
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
    if not result.wasSuccessful(): return 2
    if args.self_test: return 0
    return run(args)


if __name__ == '__main__':
    sys.exit(main())
