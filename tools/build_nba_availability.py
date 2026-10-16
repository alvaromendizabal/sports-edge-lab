#!/usr/bin/env python3
"""Build the reviewed availability collector without network or AWS calls."""
import hashlib
import json
from pathlib import Path
import zipfile


def main():
    root = Path(__file__).resolve().parent
    target = root / 'sports_edge_lab_nba_availability_v016_20261016.pyz'
    inputs = [('__main__.py', root / 'acquire_nba_availability.py'),
              ('nba_report_seeds.json', root / 'nba_report_seeds.json')]
    with zipfile.ZipFile(target, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
        for name, source in inputs:
            info = zipfile.ZipInfo(name, date_time=(2026, 10, 16, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            bundle.writestr(info, source.read_bytes())
    manifest = {'artifact': target.name, 'bytes': target.stat().st_size,
                'sha256': hashlib.sha256(target.read_bytes()).hexdigest(),
                'tests': 13, 'seed_urls': len(json.loads(inputs[1][1].read_text())),
                'inputs': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for _, p in inputs},
                'self_test_command': 'python ' + target.name + ' --self-test',
                'suggested_aws_max_runtime_seconds': 720,
                'application_arguments': ['--max-seconds', '600', '--max-requests', '300',
                                          '--max-reports', '250', '--max-pages', '4'],
                'historical_coverage_complete': False, 'point_in_time_approved': False}
    (root / 'nba_availability_build_manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps(manifest))


if __name__ == '__main__':
    main()
