"""Validate an immutable, source-only addendum against preserved public evidence.

No provider access, model fitting, or historical rescoring takes place here.
Private physical-source verification is a separate audit, not reproduced by this
public presentation validator.
"""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re

from current_source_overlay import choose_latest_reference, validate_overlay
from market_clock import instant
from point_markets import require, scalar

HERE = Path(__file__).resolve().parent
ROOT_FIELDS = {'schema', 'as_of', 'capture_state', 'owner_pipeline_accepted',
               'owner_return_sha256', 'source_run_status', 'source_run_finished_at',
               'winner_rows', 'point_rows', 'combined_week9_coverage',
               'new_model_fits', 'new_forecast_issues', 'historical_metrics_changed',
               'selection_rule', 'limitations'}


def merged_references(original, schedule, recovery):
    """Merge usable observations by source clock; preserve the original objects."""
    combined = deepcopy(original)
    combined['as_of'] = recovery['as_of']
    for name, signal in [('winner_rows', 'derived_pick'), ('point_rows', 'line')]:
        def identity(row):
            return (row['game_id'], row['provider'], row.get('target', 'winner'))
        indexed = {identity(r): r for r in combined[name]}
        for addition in (schedule, recovery):
            seen = set()
            for row in addition[name]:
                key = identity(row)
                require(key not in seen, 'Duplicate addendum reference')
                seen.add(key)
                require(key in indexed, 'Addendum event/provider/target is outside the preserved inventory')
                indexed[key] = choose_latest_reference(indexed[key], row, signal)
        combined[name] = list(indexed.values())
    combined['coverage'] = deepcopy(recovery['combined_week9_coverage'])
    return combined


def validate_source_recovery(data, coverage, original, schedule):
    require(set(data) == ROOT_FIELDS, 'Unknown or missing source-recovery fields')
    require(data['schema'] == 'sports-edge-lab.nfl.source-recovery-addendum.n036.v1',
            'Unknown source-recovery schema')
    require(data['capture_state'] == 'ACTUAL_SOURCE_ONLY_PARTIAL_RETURN'
            and data['owner_pipeline_accepted'] is False,
            'Source-only return is not owner research acceptance')
    require(re.fullmatch('[0-9a-f]{64}', data['owner_return_sha256']) is not None,
            'Invalid physical owner-return digest')
    require(data['source_run_status'] == 'PARTIAL_SOURCE_BATCH_LIMIT',
            'Source-only budget stop must remain explicit')
    require(data['historical_metrics_changed'] is False, 'No historical rescoring from source recovery')
    for field in ('new_model_fits', 'new_forecast_issues'):
        require(type(data[field]) is int and data[field] == 0,
                'Source-only acquisition cannot claim a fit or forecast issue')
    for key in ROOT_FIELDS - {'winner_rows', 'point_rows', 'combined_week9_coverage', 'limitations'}:
        scalar(data[key])
    require(isinstance(data['limitations'], list) and len(data['limitations']) >= 4,
            'Missing source-only limitations')
    for value in data['limitations']:
        scalar(value)
    require('outcome' in data['selection_rule'].lower(), 'Selection must be outcome independent')
    require(instant(data['as_of']) <= instant(data['source_run_finished_at']),
            'Acquisition cannot follow source-run completion')
    require(len(data['winner_rows']) == 3 and len(data['point_rows']) == 10,
            'Recovery must close its declared three winner and ten point references')
    # Validate every addendum row even if its clock would lose a merge. Otherwise
    # malformed stale observations could be hidden by a later valid source.
    provisional = deepcopy(original)
    provisional['as_of'] = data['as_of']
    for name in ('winner_rows', 'point_rows'):
        ids = {(r['game_id'], r['provider'], r.get('target', 'winner')): r
               for r in provisional[name]}
        seen = set()
        for row in data[name]:
            key = (row['game_id'], row['provider'], row.get('target', 'winner'))
            require(key in ids and key not in seen, 'Unknown or duplicate recovery cell')
            seen.add(key)
            ids[key] = row
        provisional[name] = list(ids.values())
    for row in provisional['coverage']:
        rows = provisional['winner_rows'] if row['target'] == 'winner' else provisional['point_rows']
        signal = 'derived_pick' if row['target'] == 'winner' else 'line'
        row['available_games'] = sum(r['provider'] == row['provider']
            and r.get('target', 'winner') == row['target'] and r[signal] is not None for r in rows)
    validate_overlay(provisional, coverage)
    combined = merged_references(original, schedule, data)
    validate_overlay(combined, coverage)
    return {'source_recovery_status': 'PUBLIC_SOURCE_ONLY_ADDENDUM_VALIDATED',
            'source_recovery_rows': 13, 'source_recovery_new_fits': 0,
            'source_recovery_new_issues': 0, 'source_recovery_historical_metrics_changed': False,
            'source_recovery_combined_week9_coverage': combined['coverage']}


def load_source_recovery(coverage, original, schedule):
    path = HERE / 'source_recovery_n036.json'
    data = json.loads(path.read_text())
    return data, {**validate_source_recovery(data, coverage, original, schedule),
                  'source_recovery_sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
