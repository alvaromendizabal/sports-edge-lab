"""Render the pinned saved B081 V9 export without owner data or rescoring."""
import hashlib
import json
from pathlib import Path
import sys

import v9_publication

ROOT = Path(__file__).parent
# Updated only after authenticating a new owner return and selected-output export.
PINS = {'latest_research_outputs.json': '4fbcbaed8b46182a044ba11ad69a2c283d724e42a7a61819091c88ee02ed8087', 'latest_model_review.json': 'd71286315816a948ac2022ad80673c7b643ae1bbdb043a857ee92c5f1e0e3dd4', 'latest_v9_acceptance.json': '9731fe2af9d8a1e45f32fe4855f4d1ea24949e3b598f30cf2a4bcaa2beaa1f71'}


def build(check=False):
    saved = {}
    for name, expected in PINS.items():
        body = (ROOT / name).read_bytes()
        if hashlib.sha256(body).hexdigest() != expected:
            raise ValueError('V9_SAVED_EVIDENCE_CHANGED_REVIEW_NEW_OWNER_EVIDENCE_FIRST:' + name)
        saved[name] = json.loads(body)
    public = saved['latest_research_outputs.json']
    review = saved['latest_v9_acceptance.json']
    model = saved['latest_model_review.json']
    v9_publication.validate(review)
    if review['selected_output_sha256'] != PINS['latest_research_outputs.json']:
        raise ValueError('V9_SELECTED_OUTPUT_PIN_MISMATCH')
    if review['latest_original_issue_at_utc'] != public['latest_forecast_issue_at_utc']:
        raise ValueError('V9_ORIGINAL_ISSUE_CLOCK_CHANGED')
    if {row['game_id'] for row in review['game_rows']} != set(public['games']):
        raise ValueError('V9_GAME_IDENTITY_COVERAGE_CHANGED')
    for row in review['saved_metric_diagnostics']:
        source = model['metric_rows'][row['source_index']]
        if row['role_alias'] != source['role_alias'] or row['scored_games'] != source['scored_games']:
            raise ValueError('V9_METRIC_SOURCE_IDENTITY_CHANGED')
        if any(source['metrics'].get(key) != value for key, value in row['metrics'].items()):
            raise ValueError('V9_SAVED_METRIC_CHANGED')
    path = ROOT / 'latest_research_outputs.html'
    current = path.read_text()
    result = v9_publication.attach_review(current, review)
    if check and result != current:
        raise ValueError('V9_SAVED_DISPLAY_STALE')
    if not check:
        path.write_text(result)
    return {'status': 'PASS' if check else 'BUILT',
            'observed_games': review['coverage']['observed_games'],
            'saved_metric_rows': len(review['saved_metric_diagnostics']),
            'new_owner_execution_claim': False, 'new_fits': 0,
            'new_inference': 0, 'new_metric_scoring': 0,
            'source_inputs': PINS,
            'display_sha256': hashlib.sha256(result.encode()).hexdigest()}


if __name__ == '__main__':
    print(json.dumps(build('--check' in sys.argv), sort_keys=True))
