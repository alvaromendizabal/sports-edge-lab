"""Validate curated spread/total references without inventing score projections.

This public contract checks the display boundary. It does not authenticate private
provider originals, derive a complete distribution or reproduce model training.
"""
import hashlib
import json
import math
from datetime import timedelta
from pathlib import Path

from market_clock import instant
from public_snapshot import FORBIDDEN

HERE = Path(__file__).resolve().parent
SCHEMA = 'sports-edge-lab.nfl.point-markets.n035a.v1'
ROOT_FIELDS = {'schema', 'as_of', 'provenance', 'selection_rule', 'limitations', 'rows'}
ROW_FIELDS = {'game_id', 'provider', 'target', 'horizon', 'contract_count',
              'source_observation_count', 'parsed_contract_count', 'line_min',
              'line_max', 'metric_eligible', 'point_estimate', 'semantics',
              'availability_status', 'predicate', 'predicate_variable', 'operator',
              'line', 'observed_probability', 'quote_at', 'acquired_at', 'cutoff_at',
              'quote_clock_kind', 'quote_age_seconds', 'reason', 'line_semantics',
              'settlement_note'}
PROVIDERS = {'DraftKings', 'Kalshi', 'Polymarket'}
HORIZONS = {'T1', 'T2', 'LATEST_PREGAME', 'LATEST_OBSERVED'}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def scalar(value):
    if isinstance(value, str):
        require(not FORBIDDEN.search(value), 'Private source or recipe in point display')
    elif type(value) in (int, float):
        require(math.isfinite(value), 'Nonfinite point display value')
    else:
        require(value is None or type(value) is bool, 'Nested source payload is not public')


def validate_point_markets(data, coverage):
    require(set(data) == ROOT_FIELDS, 'Unknown or missing public point fields')
    require(data['schema'] == SCHEMA, 'Unknown point-display schema')
    require(isinstance(data['limitations'], list), 'Missing point limitations')
    for field in ROOT_FIELDS - {'rows', 'limitations'}:
        scalar(data[field])
    for value in data['limitations']:
        scalar(value)
    instant(data['as_of'])
    require('outcome' in data['selection_rule'].lower(), 'Selection rule must disclose outcome independence')
    games = {g['game_id']: g for g in coverage['all_games']}
    seen = set()
    available = set()
    saved = set()
    for row in data['rows']:
        require(set(row) == ROW_FIELDS, 'Unknown or missing point-contract fields')
        for value in row.values():
            scalar(value)
        key = tuple(row[k] for k in ('game_id', 'provider', 'target', 'horizon'))
        require(key not in seen, 'Duplicate representative point reference')
        seen.add(key)
        require(row['game_id'] in games, 'Point event absent from the canonical inventory')
        require(row['provider'] in PROVIDERS and row['target'] in ('margin', 'total') and row['horizon'] in HORIZONS, 'Unknown point target, provider or horizon')
        require(row['metric_eligible'] is False and row['point_estimate'] is None, 'A quoted threshold cannot become a mean-score prediction or paired metric')
        require(row['semantics'] in ('THRESHOLD_CONTRACT_NOT_POINT_PROJECTION', 'QUOTED_LINE_NOT_POINT_PROJECTION'), 'Missing line-versus-projection distinction')
        for field in ('contract_count', 'source_observation_count', 'parsed_contract_count'):
            require(type(row[field]) is int and row[field] >= 0, 'Invalid source count')
        require(row['parsed_contract_count'] <= row['contract_count'] <= row['source_observation_count'], 'Contracts and quote observations have different denominators')
        if row['line'] is None:
            require(all(row[f] is None for f in ('predicate', 'operator', 'observed_probability')), 'Unparsed capture cannot invent a predicate or probability')
            require(bool(row['reason']), 'Unavailable representative needs a reason')
            continue
        require(row['contract_count'] > 0 and row['parsed_contract_count'] > 0, 'No source contract supports the displayed line')
        require(row['predicate_variable'] == ('home_margin' if row['target'] == 'margin' else 'total'), 'Margin must retain canonical home orientation')
        require(row['operator'] in ('>', '>=', '<', '<='), 'Unknown settlement predicate')
        require(isinstance(row['predicate'], str) and bool(row['predicate']), 'Missing readable predicate')
        require(row['line_min'] <= row['line'] <= row['line_max'], 'Representative line lies outside captured range')
        probability = row['observed_probability']
        if probability is not None:
            require(0 <= probability <= 1 and abs(probability * 1000 - round(probability * 1000)) < 1e-7, 'Observed display probability must be rounded')
        else:
            require(row['provider'] == 'DraftKings' and row['semantics'] == 'QUOTED_LINE_NOT_POINT_PROJECTION', 'A threshold probability cannot disappear silently')
        game = games[row['game_id']]
        kickoff = instant(game['kickoff_utc'])
        if row['availability_status'] == 'SAVED_LINE_REFERENCE_CLOCK_UNAVAILABLE':
            require(row['provider'] == 'DraftKings' and row['horizon'] == 'T2' and game['completed'], 'Unknown saved-line origin')
            require(row['semantics'] == 'QUOTED_LINE_NOT_POINT_PROJECTION' and probability is None, 'Saved line is not a probability')
            require(all(row[f] is None for f in ('quote_at', 'acquired_at', 'cutoff_at', 'quote_age_seconds')), 'Unverified source clocks cannot be manufactured')
            require(row['quote_clock_kind'] == 'ABSENT_FROM_COMPACT_REFERENCE', 'Saved line needs explicit unavailable-clock label')
            saved.add(key)
            continue
        quote = instant(row['quote_at']) if row['quote_at'] else None
        acquisition = instant(row['acquired_at']) if row['acquired_at'] else None
        cutoff = instant(row['cutoff_at']) if row['cutoff_at'] else None
        if row['horizon'] in ('T1', 'T2'):
            require(game['completed'], 'Historical point cutoff requires a completed game')
            require(cutoff == kickoff - timedelta(hours=int(row['horizon'][1])), 'Point reference cutoff differs from event clock')
            require(quote is not None and quote <= cutoff, 'Later or unverified quote cannot enter historical point display')
        elif row['horizon'] == 'LATEST_OBSERVED':
            require(not game['completed'], 'Current upcoming book cannot be reused as historical pregame')
            require(quote is not None and acquisition is not None and quote <= acquisition < kickoff, 'Current reference needs genuine pregame observation clocks')
        else:
            require(quote is not None and quote < kickoff, 'Latest-pregame quote must be strictly before kickoff')
        require(acquisition is not None and quote <= acquisition, 'Acquisition cannot precede the quoted observation')
        require(row['quote_age_seconds'] is None or row['quote_age_seconds'] >= 0, 'Negative quote age')
        if cutoff is not None:
            require(row['quote_age_seconds'] is not None, 'Historical cutoff age is not known')
            require(abs((cutoff - quote).total_seconds() - row['quote_age_seconds']) < 1.01, 'Quote age differs from its actual reference cutoff')
        available.add(key)
    finals = {g['game_id'] for g in games.values() if g['completed']}
    for target in ('margin', 'total'):
        for horizon in ('T1', 'T2'):
            require({k[0] for k in available if k[1:] == ('Kalshi', target, horizon)} == finals, 'Captured Kalshi final-game thresholds cannot disappear')
    require(not any(k[3] == 'LATEST_PREGAME' for k in available), 'This recovery cannot invent a new latest-pregame acquisition')
    return {'point_display_status': 'PUBLIC_THRESHOLD_REFERENCES_VALIDATED',
            'point_display_rows': len(seen), 'point_display_available_rows': len(available),
            'point_display_saved_line_clock_unavailable_rows': len(saved),
            'point_display_new_fits': 0, 'point_display_new_forecasts': 0,
            'point_display_new_provider_acquisition': False}


def load_point_markets(coverage=None):
    if coverage is None:
        from current_coverage import load_coverage
        coverage = load_coverage()[0]
    body = (HERE / 'point_markets.json').read_bytes()
    data = json.loads(body)
    return data, {**validate_point_markets(data, coverage), 'point_display_sha256': hashlib.sha256(body).hexdigest()}


if __name__ == '__main__':
    print(json.dumps(load_point_markets()[1], sort_keys=True))
