#!/usr/bin/env python3
"""List canonical raw content without reading payloads or request receipts.

This is a measured storage census, not a complete-season or unique-game census.
The paginated scan has an explicit time window while collectors may be writing.
"""
import argparse
import collections
import datetime as dt
import hashlib
import io
import json
from pathlib import Path
import re
import sys
import time
import unittest
import uuid
import zipfile

TRACKS = ('nfl', 'nba', 'ncaaf', 'ncaam', 'ncaaw')
PAID = ('the-odds-api', 'cfbd', 'cbbd')
PUBLIC = ('nflverse', 'nfldata', 'sportsdataverse')
BUCKET = 'sagemaker-sports-edge-lab-560403859723-us-west-2'


def utc():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z')


def pack(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode()


def classify(key):
    """Return (track, provider, content type, family), exclusion, or unknown."""
    parts = key.split('/')
    if key.endswith('/'):
        return None, 'directory_marker'
    if key.endswith('.receipt.json') or any(p in parts for p in ('request-index', 'url-index', 'receipts', 'failures', 'audit', 'audits', 'legacy')):
        return None, 'receipt_index_audit_or_legacy'
    if key.endswith(('.zip', '.pyz', '.py')):
        return None, 'code_or_return_bundle'
    if len(parts) >= 5 and parts[0] == 'tracks' and parts[1] in TRACKS and parts[2] == 'raw':
        track, provider = parts[1], parts[3]
        if provider in PUBLIC and key.endswith(('.parquet', '.csv', '.csv.gz', '.rds', '.json', '.json.gz')):
            family = parts[4] if len(parts) > 5 else provider
            return (track, provider, 'public_archive', family), None
        if provider in PAID and parts[4] == 'objects' and key.endswith('.json.gz'):
            return (track, provider, 'paid_payload', 'content_addressed_response'), None
        if provider == 'paid' and 'canary' in key and key.endswith(('.json.gz', '.json')):
            return (track, provider, 'provider_canary', 'canary'), None
        if provider == 'nba-official-injuries' and parts[4] == 'objects' and key.endswith('.pdf.gz'):
            return (track, provider, 'original_availability_pdf', 'published_report'), None
        if track in ('ncaam', 'ncaaw') and provider == 'american-availability' and parts[4] == 'objects' and key.endswith('.png.gz'):
            return (track, provider, 'original_availability_image', 'published_report'), None
        if track == 'nfl' and provider == 'nfl-official-current' and parts[4] == 'objects' and key.endswith('.html.gz'):
            return (track, provider, 'original_current_nfl_html', 'injury_roster_schedule_pages'), None
        return None, 'unclassified_raw'
    if key.startswith('shared/raw/nws/objects/') and key.endswith('.json.gz'):
        return ('shared', 'nws', 'original_weather_json', 'point_metadata_and_hourly_forecasts'), None
    if key.startswith('shared/raw/noaa-hrrr-original/objects/'):
        if key.endswith('.grib2'):
            return ('shared', 'noaa-hrrr-original', 'original_forecast_field', 'grib2_field'), None
        if key.endswith(('.idx.gz', '.xml.gz')):
            return None, 'source_listing_or_index_metadata'
    if key.startswith('shared/raw/skillcorner-acb-research/objects/'):
        if key.endswith('.jsonl.gz'):
            return ('shared', 'skillcorner-acb-research', 'tracking_trajectory_jsonl', 'acb_research_trajectories'), None
        if key.endswith('.json'):
            return ('shared', 'skillcorner-acb-research', 'tracking_dataset_json', 'game_metadata_and_provider_event_annotations'), None
        if key.endswith('.csv'):
            return ('shared', 'skillcorner-acb-research', 'tracking_identity_csv', 'provider_player_aliases'), None
    if key.startswith('shared/raw/'):
        return None, 'unclassified_raw'
    return None, 'outside_raw_scope'


def counter():
    return {'objects': 0, 'stored_bytes': 0}


def add(target, size):
    if not isinstance(size, int) or size < 0:
        raise ValueError('invalid_stored_object_size')
    target['objects'] += 1
    target['stored_bytes'] += size


class Census:
    def __init__(self):
        self.total = counter()
        self.tracks = collections.defaultdict(counter)
        self.types = collections.defaultdict(counter)
        self.sources = collections.defaultdict(counter)
        self.families = collections.defaultdict(counter)
        self.excluded = collections.defaultdict(counter)
        self.unknown_examples = []
        self.last_modified_min = None
        self.last_modified_max = None
        self.digest = hashlib.sha256()
        self.listed = 0
        self.listed_bytes = 0

    def observe(self, obj):
        key, size = obj['Key'], obj['Size']
        group, reason = classify(key)
        self.listed += 1
        self.listed_bytes += size
        if group is None:
            add(self.excluded[reason], size)
            if reason == 'unclassified_raw' and len(self.unknown_examples) < 20:
                self.unknown_examples.append(key)
            return
        track, provider, kind, family = group
        for target in (self.total, self.tracks[track], self.types[kind], self.sources[track+'/'+provider], self.families[track+'/'+provider+'/'+family]):
            add(target, size)
        modified = obj.get('LastModified')
        modified = modified.isoformat() if hasattr(modified, 'isoformat') else str(modified or '')
        if modified:
            self.last_modified_min = min(self.last_modified_min or modified, modified)
            self.last_modified_max = max(self.last_modified_max or modified, modified)
        self.digest.update(pack([key, size, modified]) + b'\n')

    def result(self):
        assert self.total['objects'] == sum(t['objects'] for t in self.tracks.values())
        assert self.total['stored_bytes'] == sum(t['stored_bytes'] for t in self.types.values())
        assert self.listed == self.total['objects'] + sum(t['objects'] for t in self.excluded.values())
        assert self.listed_bytes == self.total['stored_bytes'] + sum(t['stored_bytes'] for t in self.excluded.values())
        return {'total': self.total, 'by_track': dict(self.tracks), 'by_content_type': dict(self.types),
                'by_track_source': dict(self.sources), 'by_track_source_family': dict(self.families),
                'excluded_within_listed_prefixes': dict(self.excluded), 'unclassified_raw_examples': self.unknown_examples,
                'listed_objects': self.listed, 'listed_stored_bytes': self.listed_bytes,
                'included_listing_sha256': self.digest.hexdigest(),
                'included_last_modified_min': self.last_modified_min, 'included_last_modified_max': self.last_modified_max}


def scan(s3, bucket, deadline, max_pages, beat):
    census, windows, pages = Census(), [], 0
    complete = True
    reason = None
    for prefix in ('tracks/', 'shared/raw/'):
        started = utc()
        prefix_pages = 0
        for page in s3.get_paginator('list_objects_v2').paginate(Bucket=bucket, Prefix=prefix, PaginationConfig={'PageSize': 1000}):
            pages += 1
            prefix_pages += 1
            for obj in page.get('Contents', []):
                census.observe(obj)
            beat(census, pages, prefix)
            if time.monotonic() >= deadline or pages >= max_pages:
                complete, reason = False, 'runtime_or_page_budget'
                break
        windows.append({'prefix': prefix, 'started_at': started, 'finished_at': utc(), 'pages': prefix_pages})
        if not complete:
            break
    return dict(census.result(), listing_completed=complete, bound_reason=reason, prefix_windows=windows, pages=pages)


def run(args):
    import boto3
    from botocore.config import Config
    started = time.monotonic()
    run_id = dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid.uuid4().hex[:10]
    prefix = 'shared/acquisition/content-inventory/' + run_id + '/'
    report = {'schema_version': 'sports-edge-lab-content-inventory-v1', 'run_id': run_id, 'scan_started_at': utc(),
              'bucket': args.bucket, 'region': args.region, 'point_in_time_atomic_snapshot': False,
              'scope': 'Current S3 objects under tracks/ and shared/raw/; explicit raw-content whitelist only.',
              'interpretation': ['Object counts are not unique games, API captures, rows, seasons or approved features.',
                'Paid response bodies are content-addressed within provider and sport namespaces; public families and revisions may overlap.',
                'Stored compressed bytes are not comparable to uncompressed response-byte counters.',
                'NOAA listing/index metadata is excluded; NWS point metadata is included with forecast JSON responses.',
                'SkillCorner ACB research files are a separate transfer-research source, not NBA or NCAA trajectory coverage; provider event annotations and game metadata remain separate from trajectory files.',
                'NFL original HTML is archived page content; its count is not extracted player/game rows or approved feature coverage.',
                'Live collectors may write during this paginated scan; this report measures an interval, not a transactionally frozen instant.',
                'Objects outside listed prefixes, including duplicate legacy backups, acquisition reports and code, are outside this census.'],
              'limits': {'application_seconds': args.max_seconds, 'max_listing_pages': args.max_pages}, 'status': 'running'}
    s3 = boto3.client('s3', region_name=args.region, config=Config(retries={'mode': 'standard', 'total_max_attempts': 4}, connect_timeout=5, read_timeout=20))
    last_beat = [0.0]
    def put(key, payload, kind='application/json'):
        s3.upload_fileobj(io.BytesIO(payload), args.bucket, key, ExtraArgs={'ContentType': kind, 'ServerSideEncryption': 'AES256'})
    def beat(census, pages, current):
        now = time.monotonic()
        if now-last_beat[0] < 20:
            return
        last_beat[0] = now
        value = {'timestamp': utc(), 'event': 'HEARTBEAT', 'run_id': run_id, 'pages': pages, 'prefix': current,
                 'listed_objects': census.listed, 'included_objects': census.total['objects'],
                 'included_stored_bytes': census.total['stored_bytes'], 'elapsed_seconds': round(now-started, 2),
                 'estimated_compute_usd': round((now-started)*args.hourly_usd/3600, 6)}
        put(prefix+'progress.json', pack(value))
        print(json.dumps(value), flush=True)
    try:
        report.update(scan(s3, args.bucket, started+args.max_seconds-25, args.max_pages, beat))
        report['status'] = 'completed' if report['listing_completed'] else 'bounded_partial'
    except Exception as exc:
        report.update(status='failed', error_type=type(exc).__name__, error=str(exc)[:240])
    report.update(scan_finished_at=utc(), elapsed_seconds=round(time.monotonic()-started, 2))
    report['estimated_compute_usd'] = round(report['elapsed_seconds']*args.hourly_usd/3600, 6)
    report['cost_scope'] = 'Application interval only; Processing provisioning/shutdown, S3 requests and storage excluded.'
    output = Path(args.output_dir); output.mkdir(parents=True, exist_ok=True)
    path = output/('sports_edge_lab_content_inventory_return_'+run_id+'.zip')
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as archive:
        archive.writestr('report.json', pack(report))
        archive.writestr('resume.json', pack({'report_key': prefix+'report.json', 'resumable': False,
                                             'reason': 'A later census begins a new explicit observation window.'}))
    put(prefix+'report.json', pack(report))
    put(prefix+path.name, path.read_bytes(), 'application/zip')
    print(json.dumps({'timestamp': utc(), 'event': 'FINISHED', 'run_id': run_id, 'status': report['status'],
                      'total': report.get('total'), 'report_key': prefix+'report.json', 'return_key': prefix+path.name}), flush=True)
    return 0 if report['status']=='completed' else 2


class Tests(unittest.TestCase):
    def test_public_formats(self):
        for provider, name in [('nflverse', 'pbp/year.parquet'), ('nfldata', 'data/games.csv'), ('sportsdataverse', 'shots/hash/shots.parquet')]:
            self.assertEqual(classify('tracks/nfl/raw/'+provider+'/'+name)[0][2], 'public_archive')
    def test_receipts_excluded(self):
        self.assertIsNone(classify('tracks/nba/raw/sportsdataverse/a.parquet.receipt.json')[0])
    def test_public_fallback_formats(self):
        for name in ('standings_2005.rds', 'data.json', 'data.json.gz'):
            self.assertEqual(classify('tracks/ncaaw/raw/sportsdataverse/espn_womens_college_basketball_standings/hash/'+name)[0][2], 'public_archive')
    def test_failure_receipts_excluded(self):
        self.assertIsNone(classify('tracks/nba/raw/the-odds-api/failures/run/request.json')[0])
    def test_paid_content(self):
        for provider in PAID:
            self.assertEqual(classify('tracks/ncaam/raw/'+provider+'/objects/ab/a.json.gz')[0][2], 'paid_payload')
    def test_request_index_excluded(self):
        self.assertIsNone(classify('tracks/ncaaf/raw/cfbd/request-index/a.json')[0])
    def test_canaries(self):
        self.assertEqual(classify('tracks/ncaam/raw/paid/cbbd/canary_20260301.json')[0][2], 'provider_canary')
    def test_official_pdf(self):
        self.assertEqual(classify('tracks/nba/raw/nba-official-injuries/objects/a.pdf.gz')[0][2], 'original_availability_pdf')
    def test_american_images_only(self):
        for track in ('ncaam', 'ncaaw'):
            self.assertEqual(classify('tracks/'+track+'/raw/american-availability/objects/a.png.gz')[0][2], 'original_availability_image')
            self.assertIsNone(classify('tracks/'+track+'/raw/american-availability/url-index/a.json')[0])
        self.assertIsNone(classify('shared/acquisition/ncaa-availability/evidence/objects/a.txt.gz')[0])
    def test_nfl_current_html(self):
        self.assertEqual(classify('tracks/nfl/raw/nfl-official-current/objects/a.html.gz')[0][2], 'original_current_nfl_html')
        self.assertIsNone(classify('tracks/nfl/raw/nfl-official-current/request-index/a.json')[0])
        self.assertIsNone(classify('shared/acquisition/nfl-official-current/evidence/objects/a.txt.gz')[0])
    def test_acb_trajectories(self):
        self.assertEqual(classify('shared/raw/skillcorner-acb-research/objects/a.jsonl.gz')[0][2], 'tracking_trajectory_jsonl')
        self.assertIsNone(classify('shared/raw/skillcorner-acb-research/objects/a.zip')[0])
    def test_acb_metadata_separate(self):
        self.assertEqual(classify('shared/raw/skillcorner-acb-research/objects/a.json')[0][2], 'tracking_dataset_json')
        self.assertEqual(classify('shared/raw/skillcorner-acb-research/objects/a.csv')[0][2], 'tracking_identity_csv')
    def test_acb_evidence_excluded(self):
        self.assertIsNone(classify('shared/raw/skillcorner-acb-research/url-index/a.json')[0])
        self.assertIsNone(classify('shared/acquisition/open-tracking/evidence/objects/a.json')[0])
    def test_noaa_field_vs_metadata(self):
        self.assertEqual(classify('shared/raw/noaa-hrrr-original/objects/a.grib2')[0][2], 'original_forecast_field')
        for ext in ('.idx.gz', '.xml.gz'):
            self.assertEqual(classify('shared/raw/noaa-hrrr-original/objects/a'+ext)[1], 'source_listing_or_index_metadata')
    def test_nws(self):
        self.assertEqual(classify('shared/raw/nws/objects/a.json.gz')[0][2], 'original_weather_json')
    def test_unknown_not_inflated(self):
        self.assertEqual(classify('tracks/nba/raw/unknown/file.csv')[1], 'unclassified_raw')
    def test_non_content_excluded(self):
        for key in ('legacy/tracks/nfl/raw/nflverse/pbp/a.parquet', 'shared/acquisition/return.zip', 'tracks/nfl/README.md'):
            self.assertIsNone(classify(key)[0])
    def test_exact_aggregation(self):
        c = Census()
        c.observe({'Key': 'tracks/nfl/raw/nflverse/pbp/a.parquet', 'Size': 5})
        c.observe({'Key': 'tracks/nba/raw/the-odds-api/objects/a.json.gz', 'Size': 7})
        c.observe({'Key': 'shared/raw/noaa-hrrr-original/objects/a.idx.gz', 'Size': 3})
        r = c.result()
        self.assertEqual(r['total'], {'objects': 2, 'stored_bytes': 12})
        self.assertEqual(r['listed_stored_bytes'], 15)
    def test_pagination_and_window(self):
        class Fake:
            def get_paginator(self, operation):
                assert operation == 'list_objects_v2'
                return self
            def paginate(self, **kwargs):
                if kwargs['Prefix']=='tracks/':
                    yield {'Contents': [{'Key': 'tracks/nfl/raw/nflverse/a.parquet', 'Size': 10}]}
                    yield {'Contents': [{'Key': 'tracks/nfl/raw/nflverse/a.parquet.receipt.json', 'Size': 2}]}
                else:
                    yield {'Contents': [{'Key': 'shared/raw/noaa-hrrr-original/objects/a.grib2', 'Size': 20}]}
        r = scan(Fake(), 'b', time.monotonic()+30, 50, lambda *args: None)
        self.assertEqual(r['total'], {'objects': 2, 'stored_bytes': 30})
        self.assertEqual(r['pages'], 3); self.assertTrue(r['listing_completed'])
        r = scan(Fake(), 'b', time.monotonic()+30, 1, lambda *args: None)
        self.assertFalse(r['listing_completed'])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--bucket', default=BUCKET)
    parser.add_argument('--region', default='us-west-2')
    parser.add_argument('--max-seconds', type=int, default=240)
    parser.add_argument('--max-pages', type=int, default=1000)
    parser.add_argument('--hourly-usd', type=float, default=.461)
    parser.add_argument('--output-dir', default='/opt/ml/processing/output')
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    if args.bucket != BUCKET or args.region != 'us-west-2' or not (30 < args.max_seconds <= 240 and 0 < args.max_pages <= 1000):
        parser.error('inventory envelope invalid')
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
    if not result.wasSuccessful():
        return 1
    print(json.dumps({'timestamp': utc(), 'event': 'SELF_TEST_PASSED', 'tests': result.testsRun}), flush=True)
    return 0 if args.self_test else run(args)


if __name__ == '__main__':
    sys.exit(main())
