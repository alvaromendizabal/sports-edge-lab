#!/usr/bin/env python3
"""Rebuild the immutable v015 weather continuation PYZ from its sibling source.

Repository usage:
  python3 tools/build_weather_continuation.py --output-dir dist
  python3 dist/sports_edge_lab_weather_continuation_v015_20261016.pyz --self-test

This writes the artifact and build manifest; it performs no cloud or provider calls.
"""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, default=Path(__file__).with_name('acquire_weather_continuation.py'))
    parser.add_argument('--output-dir', type=Path, default=Path('dist'))
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    artifact = args.output_dir / 'sports_edge_lab_weather_continuation_v015_20261016.pyz'
    source = args.source.read_bytes()
    with zipfile.ZipFile(artifact, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
        info = zipfile.ZipInfo('__main__.py', (2026, 10, 16, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        bundle.writestr(info, source)
    manifest = {
        'run_family': 'sports-edge-lab-weather-continuation', 'version': 'v015',
        'artifact': str(artifact), 'artifact_sha256': hashlib.sha256(artifact.read_bytes()).hexdigest(),
        'artifact_bytes': artifact.stat().st_size, 'source': str(args.source),
        'source_sha256': hashlib.sha256(source).hexdigest(), 'self_tests': 12,
        'python_dependencies': 'standard library + boto3/botocore already present in SageMaker image',
        'prior_report_key': 'shared/acquisition/original-enrichment/20261016T182059Z-5f05a0d4d3/report.json',
        'expected_prior_eligible': 728, 'expected_prior_successful_skipped': 119,
        'expected_remaining_target': 609,
        'bounds': {'max_requests': 1500, 'max_seconds': 1200, 'max_venues': 728, 'workers': 4,
                   'requests_per_second': 2, 'recommended_aws_max_runtime_seconds': 1500},
        'entrypoint': ['python3', '-u', '/opt/ml/processing/input/code/' + artifact.name],
        'output_prefix': 'shared/acquisition/weather-continuation/{run_id}/',
        'outputs': 'one uniquely named return ZIP per execution, plus report.json/progress.json in S3',
        'cost_estimate_runtime_usd': 1200 / 3600 * .461,
        'cost_exclusions': ['boot', 'shutdown', 'S3 requests', 'S3 storage'],
        'safety': 'On HTTP 401/403/429 the NWS host is suspended immediately; no retries or alternate hosts. Prior successful venues retain original timestamp and are skipped.'}
    (args.output_dir / 'build_manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps({'artifact': str(artifact), 'sha256': manifest['artifact_sha256'],
                      'bytes': manifest['artifact_bytes']}))


if __name__ == '__main__':
    main()
