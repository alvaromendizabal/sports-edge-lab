"""Admit six rounded current references without changing forecasts or metrics."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from current_source_overlay import validate_overlay
from source_recovery import merged_references
from point_markets import require

HERE = Path(__file__).resolve().parent

def load_current_n037(coverage, original, schedule, recovery):
    path = HERE / 'current_n037.json'
    data = json.loads(path.read_text())
    require(data['schema'] == 'sports-edge-lab.nfl.current-source-addendum.n037.v1', 'Unknown schema')
    require(data['owner_return_sha256'] == 'e50b34a54f4f1b5304a7c454c6dfc0ede181e068ff0791c268bf65a248d60507', 'Owner return differs')
    require(data['historical_metrics_changed'] is False and data['model_forecasts_changed'] is False, 'Source references cannot change metrics or forecasts')
    require(len(data['winner_rows']) == 2 and len(data['point_rows']) == 4, 'Missing declared references')
    expected = {'2026_09_TB_CHI', '2026_09_BUF_MIN'}
    for name in ('winner_rows', 'point_rows'):
        require({r['game_id'] for r in data[name]} == expected and all(r['provider'] == 'Polymarket' for r in data[name]), 'Unexpected source identity')
    combined = merged_references(original, schedule, recovery)
    for name in ('winner_rows', 'point_rows'):
        additions = {(r['game_id'], r['provider'], r.get('target','winner')): r for r in data[name]}
        require(len(additions) == len(data[name]), 'Duplicate source reference')
        combined[name] = [additions.get((r['game_id'],r['provider'],r.get('target','winner')), r) for r in combined[name]]
    combined['as_of'] = data['as_of']
    for c in combined['coverage']:
        rows = combined['winner_rows'] if c['target']=='winner' else combined['point_rows']
        signal = 'derived_pick' if c['target']=='winner' else 'line'
        c['available_games'] = sum(r['provider']==c['provider'] and r.get('target','winner')==c['target'] and r[signal] is not None for r in rows)
    validate_overlay(combined, coverage)
    result = deepcopy(recovery)
    result.update(schema='sports-edge-lab.nfl.combined-current-reference-view.n037.v1', capture_state='COMBINED_AUTHENTICATED_SOURCE_REFERENCES', owner_return_sha256=data['owner_return_sha256'], source_run_status='PARTIAL_SOURCE_BATCH_WITH_INJURY_STUDY_REPORTED', source_run_finished_at=None, as_of=data['as_of'], winner_rows=recovery['winner_rows'] + data['winner_rows'], point_rows=recovery['point_rows'] + data['point_rows'], combined_week9_coverage=combined['coverage'])
    result['limitations'] = data['limitations'] + ['This merged presentation retains earlier authenticated references; zero new_model_fits/new_forecast_issues here describe the display operation only, not the N037 owner study.']
    return result, {'n037_current_source_sha256':hashlib.sha256(path.read_bytes()).hexdigest(), 'n037_current_source_references':6, 'n037_current_source_model_changes':0}
