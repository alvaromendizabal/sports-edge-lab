"""Public display contract for a separately verified schedule-revision mapping.

This verifies the sanitized presentation. Private physical-source replay is a
separate audit. It performs no acquisition, fitting, or historical rescoring.
"""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re

from current_source_overlay import validate_overlay
from market_clock import instant
from point_markets import require, scalar

HERE = Path(__file__).resolve().parent
ROOT_FIELDS = {'schema', 'as_of', 'capture_state', 'owner_pipeline_accepted',
               'winner_rows', 'point_rows', 'event_mapping', 'source_integrity',
               'limitations', 'new_provider_requests', 'new_paid_calls',
               'new_fits', 'new_issues', 'prior_overlay_modified'}
MAPPING_FIELDS = {'game_id', 'home_team', 'away_team', 'provider_kickoff_utc',
                  'canonical_kickoff_utc', 'mapping_observed_at',
                  'official_revision_verified_at', 'revision_first_publication_at',
                  'mapping_basis', 'source_quote_at', 'source_acquired_at'}
INTEGRITY_FIELDS = {'gzip_sha256', 'payload_sha256', 'receipt_sha256',
                    'source_outcomes_replayed', 'unique_game_count'}


def validate_reschedule(data, coverage, original_overlay):
    require(set(data) == ROOT_FIELDS, 'Unknown or missing schedule-reference fields')
    require(data['schema'] == 'sports-edge-lab.nfl.public.schedule-revision-reference.v1',
            'Unknown schedule-reference schema')
    require(data['capture_state'] == 'LATEST_AUTHENTICATED_OWNER_CAPTURE_RECOVERED_BY_EXACT_SCHEDULE_REVISION',
            'A recovered source must not be presented as a new capture')
    require(data['owner_pipeline_accepted'] is False and data['prior_overlay_modified'] is False,
            'Mapping is neither owner acceptance nor an old-payload mutation')
    for field in ('new_provider_requests', 'new_paid_calls', 'new_fits', 'new_issues'):
        require(type(data[field]) is int and data[field] == 0, 'No new acquisition or model credit')
    mapping, integrity = data['event_mapping'], data['source_integrity']
    require(set(mapping) == MAPPING_FIELDS and set(integrity) == INTEGRITY_FIELDS,
            'Unknown nested mapping or source fields')
    for value in mapping.values():
        scalar(value)
    for value in integrity.values():
        scalar(value)
    require(integrity['source_outcomes_replayed'] == 6 and integrity['unique_game_count'] == 1,
            'Mapping source must close six outcomes for one exact event')
    require(all(re.fullmatch('[0-9a-f]{64}', integrity[k]) for k in
                ('gzip_sha256', 'payload_sha256', 'receipt_sha256')), 'Invalid source digest')
    require(mapping['game_id'] == '2026_09_LV_SF' and mapping['home_team'] == 'SF'
            and mapping['away_team'] == 'LV', 'Mapping is not the approved ordered event')
    game = next(g for g in coverage['all_games'] if g['game_id'] == mapping['game_id'])
    require(not game['completed'] and game['home'] == mapping['home_team'] and
            game['away'] == mapping['away_team'], 'Upcoming event binding changed')
    require(instant(mapping['canonical_kickoff_utc']) == instant(game['kickoff_utc']),
            'Canonical kickoff no longer matches inventory')
    require((instant(mapping['canonical_kickoff_utc']) -
             instant(mapping['provider_kickoff_utc'])).total_seconds() == 1200,
            'This mapping is not a general kickoff tolerance')
    quote, capture, mapped = [instant(mapping[k]) for k in
        ('source_quote_at', 'source_acquired_at', 'mapping_observed_at')]
    as_of = instant(data['as_of'])
    require(quote <= capture <= mapped <= as_of < instant(game['kickoff_utc']),
            'A mapping clock cannot replace the genuine source clock')
    require(instant(mapping['official_revision_verified_at']) <= mapped,
            'Mapping precedes its official schedule verification')
    require(mapping['revision_first_publication_at'] is None,
            'Unknown first publication cannot be manufactured')
    require(isinstance(data['limitations'], list) and len(data['limitations']) >= 3,
            'Missing recovered-reference limitations')
    for value in data['limitations']:
        scalar(value)
    require(len(data['winner_rows']) == 1 and len(data['point_rows']) == 2,
            'Exactly one winner and two point references are permitted')
    combined = deepcopy(original_overlay)
    combined['as_of'] = data['as_of']
    for key in ('winner_rows', 'point_rows'):
        for row in data[key]:
            require(row['game_id'] == mapping['game_id'] and row['provider'] == 'DraftKings'
                    and row['horizon'] == 'LATEST_OBSERVED' and row['metric_eligible'] is False,
                    'Recovered mapping cannot enter historical metrics or another event')
            require(instant(row['quote_at']) == quote and instant(row['acquired_at']) == capture,
                    'Displayed source clocks differ from authenticated mapping')
        combined[key] = [r for r in combined[key] if not
                         (r['game_id'] == mapping['game_id'] and r['provider'] == 'DraftKings')] + data[key]
    for row in combined['coverage']:
        if row['provider'] == 'DraftKings':
            row['available_games'] = 15
    validate_overlay(combined, coverage)
    return {'schedule_reference_status': 'PUBLIC_EXACT_EVENT_RECOVERY_VALIDATED',
            'schedule_reference_rows': 3, 'schedule_reference_games': 1,
            'schedule_reference_new_requests': 0, 'schedule_reference_new_fits': 0,
            'schedule_reference_historical_metrics_changed': False,
            'combined_current_reference_coverage': combined['coverage']}


def load_reschedule(coverage, original_overlay):
    path = HERE / 'reschedule_reference.json'
    data = json.loads(path.read_text())
    return data, {**validate_reschedule(data, coverage, original_overlay),
                  'schedule_reference_sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
