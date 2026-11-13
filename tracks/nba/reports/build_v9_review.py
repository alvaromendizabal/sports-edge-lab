"""Render the pinned saved B082 V9 export without owner data or rescoring."""
import hashlib
import json
from pathlib import Path
from b083_html import expand_html
import sys

import v9_publication

ROOT = Path(__file__).parent
# Updated only after authenticating a new owner return and selected-output export.
PINS = {'latest_research_outputs.json': '3d28fc2e6116b7a75eb0037ccb2a2ea199afd9c29e7a72794ac9ece1722b8fdf', 'latest_model_review.json': '32768513f97399c65b9bcab52b39686970acb26737c5c73aaa8a495564bce59f', 'latest_v9_acceptance.json': '9c47f58c4b625b97c4b4f6b64d68e2deabce08c202dd57f74ff88d9c4e7a6fbd'}


def build(check=False):
    from restore_snapshot_assets import restore
    if (ROOT/'snapshot_asset_manifest.json').exists():restore(ROOT)
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
    current = expand_html(path.read_text())
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
