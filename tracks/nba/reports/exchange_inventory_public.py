"""Public counts and game bindings from a bounded current exchange catalog.

Raw quotes, contract bodies, private source paths and provider identifiers stay
in the authenticated owner evidence. A partial catalog is not a market-absence
certificate or a historical model-versus-market comparison.
"""
from __future__ import annotations

import collections
import copy
import datetime as dt
import hashlib
import json

PROVIDERS = ('KALSHI', 'POLYMARKET_US', 'POLYMARKET_INTERNATIONAL')
SCHEMA = 'sel.nba.public_current_exchange_inventory.v1'
FLAGS = {'full_season_coverage': False, 'price_values_exported': False,
         'historical_quote_possession_claim': False,
         'all_market_offerings_known': False, 'comparison_qualified': False,
         'earlier_inventory_preserved': True}


def moment(value):
    date = dt.datetime.fromisoformat(value.replace('Z', '+00:00'))
    if date.tzinfo is None:
        raise ValueError('Exchange observation needs an explicit timezone')
    return date


def _game_map(games):
    result = {str(g['game_id']): g for g in games}
    if len(result) != len(games):
        raise ValueError('Exchange dashboard game population is not unique')
    return result


def validate_public(value, games, inventory_source_sha256):
    allowed = {'schema', 'source_execution_sha256', 'source_normalization_sha256',
        'game_inventory_source_sha256', 'observed_from_utc', 'observed_to_utc',
        'completed_regular_required', 'scheduled_regular_required', 'network_requests',
        'paid_calls', 'downloaded_bytes', 'new_fits', 'providers', 'rows', 'limitations', *FLAGS}
    if set(value) != allowed or value['schema'] != SCHEMA or any(value[k] != v for k,v in FLAGS.items()):
        raise ValueError('Current exchange inventory policy changed')
    if (value['game_inventory_source_sha256'] != inventory_source_sha256
            or value['network_requests'] > 3 or value['network_requests'] < 0
            or value['paid_calls'] != 0 or value['new_fits'] != 0):
        raise ValueError('Current exchange scope or acquisition changed')
    start, end = moment(value['observed_from_utc']), moment(value['observed_to_utc'])
    if start > end:
        raise ValueError('Exchange observation clocks reversed')
    by_game = _game_map(games)
    regular = [g for g in games if g['phase'] == 'regular']
    if (value['completed_regular_required'] != sum(g['status'] == 'FINAL' for g in regular)
            or value['scheduled_regular_required'] != sum(g['status'] == 'SCHEDULED' for g in regular)):
        raise ValueError('Exchange catalog reduced the required game population')
    row_keys = {'provider', 'game_id', 'phase', 'game_status', 'bound_observations',
        'observed_before_tip', 'observed_at_or_after_tip', 'observed_at_utc',
        'winner_contract_reference_rows', 'provider_quote_time_known', 'comparison_qualified',
        'price_values_exported'}
    seen = set(); grouped = collections.defaultdict(list)
    for row in value['rows']:
        key = row['provider'], row['game_id']
        game = by_game.get(row['game_id'])
        if (set(row) != row_keys or key in seen or row['provider'] not in PROVIDERS or not game
                or row['phase'] != game['phase'] or row['game_status'] != game['status']
                or row['provider_quote_time_known'] is not False
                or row['comparison_qualified'] is not False or row['price_values_exported'] is not False):
            raise ValueError('Invalid or private current exchange game row')
        for k in ('bound_observations', 'observed_before_tip', 'observed_at_or_after_tip', 'winner_contract_reference_rows'):
            if type(row[k]) is not int or row[k] < 0:
                raise ValueError('Invalid exchange observation count')
        if (row['bound_observations'] != row['observed_before_tip'] + row['observed_at_or_after_tip']
                or not start <= moment(row['observed_at_utc']) <= end
                or row['winner_contract_reference_rows'] > row['observed_before_tip']):
            raise ValueError('Current exchange observation arithmetic or clocks changed')
        seen.add(key); grouped[row['provider']].append(row)
    provider_keys = {'provider', 'observed_at_utc', 'status', 'observations', 'distinct_markets',
        'bound_games', 'bound_completed_regular_games', 'bound_scheduled_regular_games',
        'unbound_observations', 'winner_reference_rows', 'winner_reference_games',
        'strict_spread_total_contracts', 'winner_exclusions', 'spread_total_exclusions',
        'missing_game_offering_status', 'full_provider_coverage_claim'}
    if {p['provider'] for p in value['providers']} != set(PROVIDERS) or len(value['providers']) != len(PROVIDERS):
        raise ValueError('Current exchange provider missing')
    for p in value['providers']:
        rows = grouped[p['provider']]
        if (set(p) != provider_keys or p['full_provider_coverage_claim'] is not False
                or p['missing_game_offering_status'] != 'UNESTABLISHED'
                or p['strict_spread_total_contracts'] != 0
                or p['bound_games'] != len(rows)
                or p['bound_completed_regular_games'] != sum(r['phase']=='regular' and r['game_status']=='FINAL' for r in rows)
                or p['bound_scheduled_regular_games'] != sum(r['phase']=='regular' and r['game_status']=='SCHEDULED' for r in rows)
                or p['winner_reference_rows'] != sum(r['winner_contract_reference_rows'] for r in rows)
                or p['winner_reference_games'] != sum(r['winner_contract_reference_rows']>0 for r in rows)
                or p['observations'] != sum(r['bound_observations'] for r in rows) + p['unbound_observations']):
            raise ValueError('Current exchange aggregate does not reproduce')
        if not start <= moment(p['observed_at_utc']) <= end:
            raise ValueError('Provider observation clock outside its capture')
    return copy.deepcopy(value)


def project(execution_raw, execution_sha256, normalized_raw, normalized_sha256, inventory):
    if (hashlib.sha256(execution_raw).hexdigest() != execution_sha256
            or hashlib.sha256(normalized_raw).hexdigest() != normalized_sha256):
        raise ValueError('Current exchange source fingerprint mismatch')
    execution, source = json.loads(execution_raw), json.loads(normalized_raw)
    if (execution['schema'] != 'sel.nba.b090.bounded_current_exchange_catalog_execution.v1'
            or execution['status'] != 'BOUNDED_CURRENT_CATALOG_OBSERVATION_COMPLETE'
            or source['schema'] != 'sel.nba.b090.current_exchange_normalized.v1'
            or execution['normalization_reference']['pin'] != {'bytes':len(normalized_raw),'sha256':normalized_sha256}
            or execution['network_requests'] > 3 or execution['paid_calls'] != 0
            or execution['new_fits'] != 0 or execution['new_forecasts'] != 0
            or execution['old_source_mutations'] != 0 or execution['owner_pointer_mutations'] != 0
            or execution['full_source_coverage_claim'] is not False
            or execution['historical_tick_completion_claim'] is not False
            or execution['missing_games_proved_not_offered'] is not False
            or source['historical_possession_invented'] is not False
            or source['collection_reference'] != execution['collection_reference']
            or source['current_games_reference'] != execution['current_games_reference']):
        raise ValueError('Current exchange execution scope changed')
    if source['contracts']['contracts']:
        raise ValueError('New strict exchange contracts require their own approved display adapter')
    games = inventory['rows']; by_game = _game_map(games)
    grouped = collections.defaultdict(list); rows = []
    for observation in source['observations']:
        provider = observation['provider']; game_id = str(observation.get('game_id'))
        if provider not in PROVIDERS:
            raise ValueError('Unexpected current exchange provider')
        moment(observation['observed_at_utc'])
        if observation.get('strict_fair_market_eligible') is not False:
            raise ValueError('Current catalog observation acquired a false fair-price claim')
        if observation.get('game_id') is not None and game_id not in by_game:
            raise ValueError('New exchange binding outside the dashboard official game population')
        if game_id in by_game:
            grouped[provider, game_id].append(observation)
    winners = collections.Counter()
    for reference in source['winner_references']['rows']:
        key = reference['provider'], str(reference['official_game_id'])
        game = by_game.get(key[1])
        if (key not in grouped or not game
                or reference['provider_quote_updated_at_utc'] is not None
                or reference['provider_quote_age_unknown'] is not True
                or reference['metadata_update_is_quote_clock'] is not False
                or reference['fair_home_probability'] is not None
                or reference['no_vig_probability'] is not None
                or reference['admitted_to_model_features'] is not False
                or reference['evaluation_class'] != 'OBSERVED_PREGAME_CONTRACT_BOUND_BID_ASK_REFERENCE'
                or moment(reference['price_snapshot_observed_at_utc']) >= moment(game['scheduled_start_utc'])):
            raise ValueError('Current winner reference lost its source or clock qualification')
        winners[key] += 1
    for (provider, game_id), observations in sorted(grouped.items()):
        game = by_game[game_id]; tip = moment(game['scheduled_start_utc'])
        before = sum(moment(r['observed_at_utc']) < tip for r in observations)
        rows.append({'provider':provider,'game_id':game_id,'phase':game['phase'],
            'game_status':game['status'],'bound_observations':len(observations),
            'observed_before_tip':before,'observed_at_or_after_tip':len(observations)-before,
            'observed_at_utc':max(r['observed_at_utc'] for r in observations),
            'winner_contract_reference_rows':winners[provider,game_id],
            'provider_quote_time_known':False,'comparison_qualified':False,'price_values_exported':False})
    providers = []
    for saved in execution['provider_summary']:
        provider = saved['provider']; projected = [r for r in rows if r['provider']==provider]
        raw_rows = [r for r in source['observations'] if r['provider']==provider]
        statuses = [s for s in execution['provider_status'] if s['provider']==provider]
        if len(statuses)!=1 or len(saved['observation_clocks_utc'])!=1:
            raise ValueError('Current provider capture is not singular')
        if (saved['observations']!=len(raw_rows)
                or saved['distinct_markets']!=len({r['market_id']for r in raw_rows})
                or saved['bound_games']!=len(projected)
                or saved['unbound_observations']!=sum(r.get('game_id') is None for r in raw_rows)
                or saved['winner_reference_rows']!=sum(r['winner_contract_reference_rows']for r in projected)
                or saved['winner_reference_games']!=sum(r['winner_contract_reference_rows']>0 for r in projected)):
            raise ValueError('Exchange execution aggregates differ from actual normalized rows')
        providers.append({k:copy.deepcopy(saved[k]) for k in (
            'provider','observations','distinct_markets','bound_games','unbound_observations',
            'winner_reference_rows','winner_reference_games','strict_spread_total_contracts',
            'winner_exclusions','spread_total_exclusions','missing_game_offering_status','full_provider_coverage_claim')}
            | {'observed_at_utc':saved['observation_clocks_utc'][0],'status':statuses[0]['status'],
               'bound_completed_regular_games':sum(r['phase']=='regular'and r['game_status']=='FINAL'for r in projected),
               'bound_scheduled_regular_games':sum(r['phase']=='regular'and r['game_status']=='SCHEDULED'for r in projected)})
    clocks = [p['observed_at_utc']for p in providers]
    value = {'schema':SCHEMA,'source_execution_sha256':execution_sha256,
        'source_normalization_sha256':normalized_sha256,
        'game_inventory_source_sha256':inventory['source_snapshot_sha256'],
        'observed_from_utc':min(clocks),'observed_to_utc':max(clocks),
        'completed_regular_required':sum(g['phase']=='regular'and g['status']=='FINAL'for g in games),
        'scheduled_regular_required':sum(g['phase']=='regular'and g['status']=='SCHEDULED'for g in games),
        'network_requests':execution['network_requests'],'paid_calls':0,
        'downloaded_bytes':execution['downloaded_bytes'],'new_fits':0,
        'providers':providers,'rows':rows,**FLAGS,
        'limitations':[
            'One bounded catalog page per provider; pagination and complete offerings are not established.',
            'A missing bound record does not prove that a market was not offered.',
            'Current observations of completed games are not historical pregame quotes.',
            'Provider quote-update time is unknown; metadata update time is not substituted.',
            'Winner contract references retain private prices and do not establish a same-cutoff model comparison.',
            'Earlier November 15 observations remain preserved separately; no old quote, source clock or game binding is rewritten.',
        ]}
    return validate_public(value,games,inventory['source_snapshot_sha256'])
