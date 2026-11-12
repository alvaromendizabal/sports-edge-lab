"""Rebuild the V9 display from the unchanged, already-public B077 evidence."""
import hashlib
import json
from pathlib import Path
import sys

import v9_publication

ROOT = Path(__file__).parent
PINS = {
    'latest_research_outputs.json': '9e6795387c1e64bc6265da04bdd9d4e9fd0fb9860007da7b465549752542149b',
    'b078_recovered_b077_evidence.json': '74dd8d0632e9efeb1885b410b7c2f5a82129ba5b41f3e2e70114a4aa0e824c1b',
    'b077_historical_peaks_and_gates.json': '65edad6d038b898b384aa6907070c48180798c7b95404fe00c2952f53d368e85',
}
# This lifecycle describes the selected B077 evidence, which was merged before
# the V9 display code. The current display PR/commit has its own GitHub receipt.
LIFECYCLE = {
    'artifact_scope': 'CACHED_B077_SELECTED_OUTPUT_EVIDENCE',
    'prepared': {'verified': True, 'status': 'AUTHENTICATED_B077_DERIVED_EXPORT'},
    'committed': {'verified': True, 'status': 'B077_PUBLIC_EVIDENCE_COMMITTED',
                  'commit_sha': 'ca97aaa8364b5fcf97b0b0593d45c7fe1c9e0e1f',
                  'url': 'https://github.com/alvaromendizabal/sports-edge-lab/pull/249'},
    'merged': {'verified': True, 'status': 'B077_PUBLIC_EVIDENCE_MERGED',
               'commit_sha': '9cd75587d769c68cd3a845bd6efa4400693f67f5',
               'tree_sha': '66e7220ec36cc3053a5d54aa9b82147fa77e2a89',
               'url': 'https://github.com/alvaromendizabal/sports-edge-lab/pull/249'},
    'deployed': {'verified': False, 'status': 'NO_CONFIGURED_GITHUB_PAGES_NO_VERIFIED_EXTERNAL_DEPLOYMENT'},
}


def build(check=False):
    sources = {}
    for name, expected in PINS.items():
        body = (ROOT / name).read_bytes()
        if hashlib.sha256(body).hexdigest() != expected:
            raise ValueError('V9_CACHED_EVIDENCE_CHANGED_REVIEW_NEW_OWNER_EVIDENCE_FIRST:' + name)
        sources[name] = json.loads(body)
    public = sources['latest_research_outputs.json']
    metrics = sources['b078_recovered_b077_evidence.json']
    current = (ROOT / 'latest_research_outputs.html').read_text()
    files, receipt = v9_publication.publication_payloads(public, None, metrics, current, LIFECYCLE)
    for name, body in files.items():
        if check:
            if (ROOT / name).read_bytes() != body:
                raise ValueError('V9_SAVED_DISPLAY_STALE:' + name)
        else:
            (ROOT / name).write_bytes(body)
    return {'status': 'PASS' if check else 'BUILT', **receipt,
        'source_inputs': PINS, 'new_owner_execution_claim': False,
        'files': {name: {'bytes': len(body), 'sha256': hashlib.sha256(body).hexdigest()} for name, body in files.items()}}


if __name__ == '__main__':
    print(json.dumps(build('--check' in sys.argv), sort_keys=True))
