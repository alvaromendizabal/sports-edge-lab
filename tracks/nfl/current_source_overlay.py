"""Validate separately recovered current-market references without promoting research.

The public checker verifies the presentation contract. Private checkpoint custody
and source authentication remain separate evidence; this module performs no I/O
against providers and never changes model predictions or historical evaluations.
"""
import hashlib
import json
from pathlib import Path

from market_clock import instant
from point_markets import ROW_FIELDS as POINT_FIELDS, scalar, require

HERE = Path(__file__).resolve().parent
SCHEMA = 'sports-edge-lab.nfl.current-source-overlay.n035b.v1'
STATE = 'PARTIAL_OWNER_SOURCE_CHECKPOINT_RECOVERY'
OBSERVATION_ONLY = 'OBSERVATION_TIME_ONLY_PROVIDER_QUOTE_CLOCK_UNKNOWN'
ROOT_FIELDS = {'schema', 'as_of', 'capture_state', 'owner_pipeline_accepted',
               'provenance', 'limitations', 'selection_rule', 'winner_rows',
               'point_rows', 'coverage'}
WINNER_FIELDS = {'game_id', 'provider', 'horizon', 'derived_pick', 'p_home',
                 'quote_at', 'acquired_at', 'quote_clock_kind',
                 'availability_status', 'unavailable_reason', 'metric_eligible'}
PROVIDERS = {'DraftKings', 'Kalshi', 'Polymarket'}


def reference_time(row):
    if row.get('quote_at'):
        return instant(row['quote_at'])
    if row.get('quote_clock_kind') == OBSERVATION_ONLY and row.get('acquired_at'):
        return instant(row['acquired_at'])
    return None


def choose_latest_reference(base, recovered, signal):
    """A missing/newer-empty capture never erases an existing usable reference."""
    if recovered is None:
        return base
    if recovered.get(signal) is None:
        return base if base and base.get(signal) is not None else recovered
    if not base or base.get(signal) is None:
        return recovered
    old_time, new_time = reference_time(base), reference_time(recovered)
    if new_time is None:
        return base
    return recovered if old_time is None or new_time >= old_time else base


def _clocks(row, game, as_of):
    acquisition = instant(row['acquired_at']) if row['acquired_at'] else None
    quote = instant(row['quote_at']) if row['quote_at'] else None
    require(acquisition is not None, 'Current reference lacks an actual capture time')
    require(acquisition < instant(game['kickoff_utc']), 'Current capture is not pregame')
    require(acquisition <= as_of, 'Capture occurs after the overlay observation')
    if quote is None:
        require(row['provider'] == 'Kalshi' and row['quote_clock_kind'] == OBSERVATION_ONLY,
                'Missing provider quote time needs the explicit Kalshi observation-only definition')
    else:
        require(row['quote_clock_kind'] != OBSERVATION_ONLY,
                'An observation time cannot be relabeled a provider quote timestamp')
        require(quote <= acquisition, 'Provider quote cannot follow its capture')


def validate_overlay(data, coverage):
    require(set(data) == ROOT_FIELDS, 'Unknown or missing public overlay fields')
    require(data['schema'] == SCHEMA, 'Unknown current-source overlay schema')
    require(data['capture_state'] == STATE and data['owner_pipeline_accepted'] is False,
            'Partial source checkpoints are not completed owner acceptance')
    require(isinstance(data['provenance'], str), 'Provenance must be a public summary')
    require(isinstance(data['limitations'], list) and data['limitations'], 'Missing source limitations')
    for key in ROOT_FIELDS - {'winner_rows', 'point_rows', 'coverage', 'limitations'}:
        scalar(data[key])
    for value in data['limitations']:
        scalar(value)
    require('outcome' in data['selection_rule'].lower(), 'Selection must disclose outcome independence')
    as_of = instant(data['as_of'])
    games = {g['game_id']: g for g in coverage['all_games'] if g['week'] == 9 and not g['completed']}
    require(len(games) == 15, 'Overlay must bind to the preserved 15-game current week')
    seen = set()
    counts = {(p, t): 0 for p in PROVIDERS for t in ('winner', 'margin', 'total')}
    for target, rows, fields in [('winner', data['winner_rows'], WINNER_FIELDS),
                                 ('point', data['point_rows'], POINT_FIELDS)]:
        require(isinstance(rows, list), 'Overlay rows must be an array')
        for row in rows:
            require(set(row) == fields, 'Unknown or missing public reference fields')
            for value in row.values():
                scalar(value)
            require(row['game_id'] in games and row['provider'] in PROVIDERS,
                    'Reference is outside the canonical current-week game/provider set')
            require(row['horizon'] == 'LATEST_OBSERVED' and row['metric_eligible'] is False,
                    'Partial current source recovery cannot enter an earlier horizon or paired metric')
            t = target if target == 'winner' else row['target']
            require(t in ('winner', 'margin', 'total'), 'Unknown overlay target')
            key = (row['game_id'], row['provider'], t)
            require(key not in seen, 'Duplicate current reference')
            seen.add(key)
            game = games[row['game_id']]
            available = row['derived_pick'] is not None if t == 'winner' else row['line'] is not None
            if t == 'winner':
                if available:
                    require(row['availability_status'] == 'OBSERVED_WINNER_REFERENCE', 'Unqualified winner reference promoted')
                    require(row['derived_pick'] in (game['home'], game['away']), 'Winner direction is not an event team')
                    p = row['p_home']
                    require(type(p) in (int, float) and 0 <= p <= 1 and abs(p * 1000 - round(p * 1000)) < 1e-7,
                            'Winner proxy must be a rounded probability')
                    require((p > .5 and row['derived_pick'] == game['home']) or
                            (p < .5 and row['derived_pick'] == game['away']), 'Winner proxy and direction disagree')
                else:
                    require(row['availability_status'] == 'NO_QUALIFIED_CURRENT_REFERENCE' and bool(row['unavailable_reason']),
                            'Missing winner needs an explicit evidence reason')
                    require(row['p_home'] is None, 'Unqualified winner cannot display a probability')
            else:
                require(row['point_estimate'] is None, 'A threshold cannot become a score projection')
                require(row['semantics'] in ('THRESHOLD_CONTRACT_NOT_POINT_PROJECTION', 'QUOTED_LINE_NOT_POINT_PROJECTION'),
                        'Point references must retain threshold semantics')
                for field in ('contract_count', 'source_observation_count', 'parsed_contract_count'):
                    require(type(row[field]) is int and row[field] >= 0, 'Invalid point source count')
                require(row['parsed_contract_count'] <= row['contract_count'] <= row['source_observation_count'],
                        'Contract counts exceed source observations')
                if available:
                    require(row['availability_status'] in ('OBSERVED_THRESHOLD_CONTRACT', 'OBSERVED_QUOTED_LINE'),
                            'Unqualified point reference promoted')
                    require(row['parsed_contract_count'] > 0, 'No parsed source supports a point reference')
                    require(row['predicate_variable'] == ('home_margin' if t == 'margin' else 'total'),
                            'Point reference orientation changed')
                    require(row['operator'] in ('>', '>=', '<', '<=') and bool(row['predicate']), 'Unknown point payoff condition')
                    require(row['line_min'] <= row['line'] <= row['line_max'], 'Point reference lies outside source range')
                    probability = row['observed_probability']
                    if probability is None:
                        require(row['provider'] == 'DraftKings' and row['semantics'] == 'QUOTED_LINE_NOT_POINT_PROJECTION',
                                'A threshold probability cannot disappear silently')
                    else:
                        require(type(probability) in (int, float) and 0 <= probability <= 1 and
                                abs(probability * 1000 - round(probability * 1000)) < 1e-7, 'Unrounded or invalid threshold probability')
                else:
                    require(row['availability_status'] == 'NO_QUALIFIED_CURRENT_REFERENCE' and bool(row['reason']),
                            'Missing point reference needs an explicit evidence reason')
                    require(all(row[k] is None for k in ('predicate', 'operator', 'observed_probability')),
                            'Missing source cannot invent a predicate or probability')
                require(row['cutoff_at'] is None, 'Current observation is not an earlier prediction cutoff')
            if available:
                _clocks(row, game, as_of)
                counts[(row['provider'], t)] += 1
    require(seen == {(gid, p, t) for gid in games for p in PROVIDERS for t in ('winner', 'margin', 'total')},
            'Every current game/provider/target needs an available row or specific missing reason')
    declared = set()
    for row in data['coverage']:
        require(set(row) == {'provider', 'target', 'available_games', 'total_games'}, 'Unknown coverage fields')
        key = (row['provider'], row['target'])
        require(key in counts and key not in declared, 'Duplicate or unknown coverage target')
        declared.add(key)
        require(row['available_games'] == counts[key] and row['total_games'] == len(games), 'Coverage denominator or numerator differs from rows')
    require(declared == set(counts), 'Coverage census is incomplete')
    return {'current_source_overlay_status': 'PUBLIC_PARTIAL_SOURCE_REFERENCES_VALIDATED',
            'current_source_overlay_games': len(games), 'current_source_overlay_rows': len(seen),
            'current_source_overlay_completed_owner_acceptance': False,
            'current_source_overlay_model_forecasts_changed': False,
            'current_source_overlay_new_review_provider_requests': 0,
            'current_source_overlay_coverage': data['coverage']}


def load_overlay(coverage):
    path = HERE / 'current_source_overlay.json'
    data = json.loads(path.read_text())
    return data, {**validate_overlay(data, coverage), 'current_source_overlay_sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
