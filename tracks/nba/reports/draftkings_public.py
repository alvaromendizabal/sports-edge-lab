"""Minimal analytical display from verified DraftKings normalization receipts.

The normalizer output remains private. This module projects a selected set of
analytical UI values; the download projection retains aggregate coverage only.
It performs no acquisition, model scoring, trade, settlement or promotion.
"""
from __future__ import annotations

import copy
import hashlib
import json
import math
from collections import Counter
from datetime import datetime, timedelta

SCHEMA = 'sel.nba.draftkings_analytical_ui.v1'
RIGHTS = 'OWNER_AUTHORIZED_PRIVATE_RESEARCH_AND_ANALYTICAL_UI'
TARGETS = ('winner', 'margin', 'total')
QUOTE_FIELDS = ('home_win_probability', 'home_spread_line', 'away_spread_line',
                'market_home_minus_away', 'total_line', 'home_decimal_price',
                'away_decimal_price', 'over_decimal_price', 'under_decimal_price', 'overround')


def moment(value):
    if not isinstance(value, str):
        raise ValueError('DraftKings clock missing')
    result = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if result.utcoffset() is None:
        raise ValueError('DraftKings clock lacks timezone')
    return result


def finite(value):
    return isinstance(value, (float, int)) and not isinstance(value, bool) and math.isfinite(value)


def project_normalized(raw, *, expected_sha256, games, required_game_ids):
    """Read one exact normalized snapshot and keep its declared population.

    Every normalized row is checked again against the dashboard's authoritative
    game identity. A failed or missing row never acquires displayed quote values.
    Required games without a capture stay in the coverage denominator.
    """
    if hashlib.sha256(raw).hexdigest() != expected_sha256:
        raise ValueError('DraftKings normalized input fingerprint mismatch')
    source = json.loads(raw)
    if source.get('schema') != 'sel.nba.b089.market_analytical_projection.v1':
        raise ValueError('DraftKings normalized input schema mismatch')
    if source.get('raw_provider_export_authorized') is not False:
        raise ValueError('DraftKings raw export permission is not established')
    by_game = {g['game_id']: g for g in games}
    required = set(required_game_ids)
    if len(required) != len(required_game_ids) or not required:
        raise ValueError('DraftKings required population must be nonempty and unique')
    if not required.issubset(by_game):
        raise ValueError('DraftKings required population is absent from game inventory')
    projected, seen = [], set()
    for row in source.get('rows', []):
        game_id = row.get('official_game_id')
        target, horizon = row.get('target'), row.get('horizon_minutes')
        if target not in TARGETS or horizon not in (60, 120, None):
            raise ValueError('DraftKings target or horizon unsupported')
        if game_id not in by_game:
            raise ValueError('DraftKings game is absent from public inventory')
        game = by_game[game_id]
        if (row.get('home'), row.get('away'), moment(row.get('start_utc'))) != (
                game.get('home_team'), game.get('away_team'), moment(game.get('scheduled_start_utc'))):
            raise ValueError('DraftKings exact game identity mismatch')
        key = (game_id, target, horizon)
        if key in seen:
            raise ValueError('DraftKings duplicate game target horizon')
        seen.add(key)
        historical = horizon is not None
        if historical and game_id not in required:
            raise ValueError('DraftKings historical row outside required population')
        if row.get('source') != 'DraftKings' or row.get('source_provider') != 'THE_ODDS_API':
            raise ValueError('DraftKings provider mismatch')
        if row.get('raw_download_authorized') is not False or row.get('original_issued_evidence') is not False:
            raise ValueError('DraftKings unsupported export or original-issue claim')
        display = row.get('public_analytical_display_eligible') is True
        comparable = row.get('comparison_eligible') is True
        if comparable and (not historical or not display):
            raise ValueError('DraftKings current or unqualified row cannot enter backtest')
        if display:
            if row.get('source_rights_status') != RIGHTS:
                raise ValueError('DraftKings analytical rights unqualified')
            status = 'QUALIFIED_HISTORICAL_REFERENCE' if historical else 'QUALIFIED_CURRENT_REFERENCE'
            if row.get('status') != status or comparable != historical:
                raise ValueError('DraftKings qualification flags conflict')
            quote, retrieved, tip = map(moment, (row.get('source_quote_time'), row.get('retrieved_at'), row.get('start_utc')))
            provider_tip = moment(row.get('provider_start_utc') or row['start_utc'])
            if provider_tip != tip:
                binding = row.get('exact_identity_binding') or {}
                if (row.get('official_forecast_cutoff_unchanged') is not True
                        or binding.get('official_game_id') != game_id
                        or binding.get('home') != row.get('home') or binding.get('away') != row.get('away')
                        or moment(binding.get('official_start_utc')) != tip
                        or moment(binding.get('provider_start_utc')) != provider_tip
                        or binding.get('payload_sha256') != row.get('source_payload_sha256')
                        or binding.get('receipt_sha256') != row.get('receipt_sha256')):
                    raise ValueError('DraftKings provider start revision lacks exact binding')
            if historical:
                snapshot, cutoff = map(moment, (row.get('archive_snapshot_time'), row.get('forecast_cutoff')))
                if not quote <= snapshot <= cutoff < tip or snapshot > retrieved or cutoff != tip - timedelta(minutes=horizon):
                    raise ValueError('DraftKings historical source clock invalid')
            elif not quote <= retrieved < tip:
                raise ValueError('DraftKings current capture is not pregame')
            if target in ('winner', 'margin'):
                prices = (row.get('home_decimal_price'), row.get('away_decimal_price'))
            else:
                prices = (row.get('over_decimal_price'), row.get('under_decimal_price'))
            if not all(finite(p) and p > 1 for p in prices):
                raise ValueError('DraftKings paired prices invalid')
            if target == 'winner':
                value = row.get('home_win_probability')
                expected = (1 / prices[0]) / (1 / prices[0] + 1 / prices[1])
                if not finite(value) or not 0 <= value <= 1 or abs(value - expected) > 1e-12:
                    raise ValueError('DraftKings winner normalization invalid')
            elif target == 'margin':
                home, away, implied = (row.get(k) for k in ('home_spread_line', 'away_spread_line', 'market_home_minus_away'))
                if not all(finite(v) for v in (home, away, implied)) or abs(home + away) > 1e-10 or abs(home + implied) > 1e-10:
                    raise ValueError('DraftKings spread orientation invalid')
            elif not finite(row.get('total_line')) or row['total_line'] <= 0:
                raise ValueError('DraftKings total threshold invalid')
        if not isinstance(row.get('reasons', []), list) or not all(isinstance(r, str) for r in row.get('reasons', [])):
            raise ValueError('DraftKings reason metadata invalid')
        item = {'game_id': game_id, 'target': target, 'horizon_minutes': horizon,
                'status': row.get('status'), 'reasons': list(row.get('reasons', [])),
                'historical_comparison_qualified': comparable, 'analytical_display_qualified': display,
                'evidence_class': 'RETROSPECTIVE_PROVIDER_ARCHIVE' if historical else 'CURRENT_CAPTURE_REFERENCE',
                'source_quote_time': row.get('source_quote_time'),
                'archive_snapshot_time': row.get('archive_snapshot_time'),
                'retrieved_at': row.get('retrieved_at'), 'forecast_cutoff': row.get('forecast_cutoff'),
                'official_start_utc': row.get('official_start_utc') or row.get('start_utc'),
                'provider_start_utc': row.get('provider_start_utc') or row.get('start_utc'),
                'start_revision_seconds': (moment(row.get('provider_start_utc') or row['start_utc']) - moment(row['start_utc'])).total_seconds(),
                'quote_age_seconds_at_cutoff': row.get('quote_age_seconds_at_cutoff'),
                'settlement_qualified': False, 'original_issued_evidence': False,
                'market_push_probability': None,
                'probability_method': 'PAIRED_DECIMAL_INVERSE_PROPORTIONAL_NORMALIZATION' if display and target == 'winner' else None,
                'line_interpretation': 'SPREAD_THRESHOLD_NOT_DISTRIBUTION_MEAN' if target == 'margin' else 'TOTAL_THRESHOLD_NOT_DISTRIBUTION_MEAN' if target == 'total' else None}
        item.update({key: row.get(key) if display else None for key in QUOTE_FIELDS})
        for value in [*item.values(), *item['reasons']]:
            if isinstance(value, str) and any(token in value.lower() for token in ('s3://', 'arn:aws:', '/home/', '/workspace/', 'apikey=', 'api_key=')):
                raise ValueError('DraftKings private source data in projection')
        projected.append(item)
    coverage = []
    for horizon in (60, 120):
        for target in TARGETS:
            group = [r for r in projected if r['target'] == target and r['horizon_minutes'] == horizon]
            qualified = {r['game_id'] for r in group if r['historical_comparison_qualified']}
            coverage.append({'season': '2026-27', 'phase': 'regular', 'target': target,
                             'horizon_minutes': horizon, 'required_games': len(required),
                             'captured_game_slots': len(group), 'qualified_games': len(qualified),
                             'missing_or_unqualified_games': len(required - qualified),
                             'full_population_market_coverage': required == qualified,
                             'failure_reasons': dict(sorted(Counter(reason for r in group for reason in r['reasons']).items()))})
    clocks = [r['retrieved_at'] for r in projected if r['retrieved_at']]
    current_games = {r['game_id'] for r in projected if r['analytical_display_qualified'] and r['horizon_minutes'] is None}
    scheduled_games = {g['game_id'] for g in games if g.get('phase') == 'regular' and g.get('status') == 'SCHEDULED'}
    return {'schema': SCHEMA, 'source_normalized_sha256': expected_sha256,
            'observed_at_utc': max(clocks, key=moment) if clocks else None,
            'required_population_games': len(required), 'coverage': coverage,
            'qualified_historical_target_slots': sum(r['historical_comparison_qualified'] for r in projected),
            'qualified_current_reference_slots': sum(r['analytical_display_qualified'] and r['horizon_minutes'] is None for r in projected),
            'qualified_current_reference_games': len(current_games),
            'known_scheduled_regular_games': len(scheduled_games),
            'scheduled_games_without_qualified_current_quotes': len(scheduled_games-current_games),
            'historical_start_revision_game_horizon_slots': len({(r['game_id'],r['horizon_minutes']) for r in projected
                if r['historical_comparison_qualified'] and r['start_revision_seconds'] != 0}),
            'captures_normalized': source.get('captures_normalized', 0),
            'capture_failure_count': len(source.get('capture_failures', [])),
            'rows': sorted(projected, key=lambda r: (r['game_id'], r['target'], r['horizon_minutes'] or 0)),
            'rights': {'analytical_ui_permitted': True, 'bulk_provider_download_permitted': False,
                       'scope': 'DRAFTKINGS_VIA_THE_ODDS_API_ONLY'},
            'comparison_scope': 'REGISTERED_HORIZON_REFERENCES; MODEL_PAIRING_AND_FULL_POPULATION_READINESS_SEPARATE',
            'complete_season_market_comparison': False, 'automatic_promotion': False}


def download_projection(value):
    """The user download contains analytical summaries, never the quote table."""
    result = copy.deepcopy(value)
    if 'draftkings_analytical' in result:
        market = result['draftkings_analytical']
        market.pop('rows', None)
        market['provider_quote_rows_excluded_from_download'] = True
    return result
