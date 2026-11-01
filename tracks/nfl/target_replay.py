"""Fixed-target, matched-cohort monitoring replay; demo data are invented.

This contract consumes explicit declarations. It does not authenticate a private
model, prove complete upstream lineage, select a champion, or issue a wager.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Iterable, Mapping


def _instant(value):
    if not isinstance(value, str):
        raise ValueError('An explicit timezone-aware clock is required')
    parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if parsed.tzinfo is None:
        raise ValueError('A timezone-aware clock is required')
    return parsed


def _number(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError('A finite numeric value is required')
    return float(value)


def _identity(value, label):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(label + ' must be a nonempty string')
    return value


def _metrics(rows, target, field):
    if not rows:
        return {'n': 0, 'log_loss': None, 'brier': None, 'accuracy': None,
                'mae': None, 'rmse': None}
    y, p = [r['actual'] for r in rows], [r[field] for r in rows]
    result = {'n': len(rows), 'log_loss': None, 'brier': None,
              'accuracy': None, 'mae': None, 'rmse': None}
    if target == 'winner':
        q = [min(1 - 1e-15, max(1e-15, x)) for x in p]
        result.update(log_loss=sum(-a * math.log(b) - (1-a) * math.log(1-b)
                                  for a, b in zip(y, q)) / len(y),
                      brier=sum((a-b)**2 for a, b in zip(y, p)) / len(y),
                      accuracy=sum(int(b >= .5) == a for a, b in zip(y, p)) / len(y))
    else:
        result.update(mae=sum(abs(a-b) for a, b in zip(y, p)) / len(y),
                      rmse=math.sqrt(sum((a-b)**2 for a, b in zip(y, p)) / len(y)))
    return result


def evaluate_target_replay(census: Iterable[Mapping], predictions: Iterable[Mapping],
                           selection: Mapping, *, monitoring_season: int = 2026) -> dict:
    """Score one declared target recipe and MARKET on identical admitted games.

    All census games survive, including ties, pending outcomes and missing rows.
    A decision/source boundary is checked, while actual model/prediction creation
    clocks remain visible. Every output is a reconstructed monitoring replay,
    never an original historical issue or a promotion receipt.
    """
    if isinstance(monitoring_season, bool) or not isinstance(monitoring_season, int):
        raise ValueError('Monitoring season must be an integer')
    target = selection.get('target')
    if target not in {'winner', 'margin', 'total'}:
        raise ValueError('One explicit winner, margin or total target is required')
    model = _identity(selection.get('model_id'), 'Model identity')
    if selection.get('selection_seasons') != [monitoring_season-2, monitoring_season-1]:
        raise ValueError('Selection must use the two prior seasons, never monitoring outcomes')
    if selection.get('training_policy') != 'PRIOR_SEASONS_ONLY':
        raise ValueError('Current-season fitting is not eligible for this replay policy')
    latest = selection.get('latest_training_label_season')
    if isinstance(latest, bool) or not isinstance(latest, int) or latest >= monitoring_season:
        raise ValueError('Training labels must precede the monitoring season')
    if not re.fullmatch('[0-9a-f]{64}', str(selection.get('selection_receipt_sha256', ''))):
        raise ValueError('An exact declared selection receipt digest is required')
    selected_at = _instant(selection.get('selected_at'))
    games, forecasts = {}, {}
    for raw in census:
        game = dict(raw)
        game_id = _identity(game.get('game_id'), 'Game identity')
        if game_id in games:
            raise ValueError('Duplicate census identity')
        if type(game.get('season')) is not int or game['season'] != monitoring_season:
            raise ValueError('Census must use the declared monitoring season')
        _identity(game.get('week'), 'Official week identity')
        _instant(game.get('kickoff_at'))
        if game.get('status') not in {'FINAL', 'SCHEDULED', 'POSTPONED', 'CANCELED'}:
            raise ValueError('An explicit event status is required')
        if game['status'] == 'FINAL':
            _number(game.get('home_score'))
            _number(game.get('away_score'))
            if game['home_score'] < 0 or game['away_score'] < 0:
                raise ValueError('Actual scores must be nonnegative')
        games[game_id] = game
    if not games:
        raise ValueError('A nonempty official census is required')
    for raw in predictions:
        row = dict(raw)
        key = row.get('game_id')
        if key not in games or key in forecasts:
            raise ValueError('Unknown or duplicate forecast identity')
        if row.get('target') != target or row.get('model_id') != model:
            raise ValueError('Forecast differs from the target-specific declared recipe')
        if (type(row.get('latest_training_label_season')) is not int
                or row['latest_training_label_season'] != latest):
            raise ValueError('Forecast training-season declaration differs from the selected recipe')
        for key_numeric in ('prediction', 'market_prediction'):
            value = _number(row.get(key_numeric))
            if target == 'winner' and not 0 <= value <= 1:
                raise ValueError('Winner probabilities must be between zero and one')
            if target == 'total' and value < 0:
                raise ValueError('Total predictions must be nonnegative')
        for key_clock in ('decision_at', 'source_available_at', 'latest_training_label_at',
                          'model_created_at', 'prediction_created_at'):
            _instant(row.get(key_clock))
        if _instant(row['model_created_at']) > _instant(row['prediction_created_at']):
            raise ValueError('A prediction cannot precede its model creation')
        if _instant(row['latest_training_label_at']) > _instant(row['model_created_at']):
            raise ValueError('A model cannot precede its latest training-label availability')
        if _instant(row['source_available_at']) > _instant(row['prediction_created_at']):
            raise ValueError('A prediction cannot precede its source availability')
        forecasts[row['game_id']] = row

    ledger, eligible = [], []
    for game_id, game in sorted(games.items()):
        row = forecasts.get(game_id)
        output = {'game_id': game_id, 'week': game['week'], 'target': target,
                  'model_id': model, 'status': game['status'], 'kickoff_at': game['kickoff_at'],
                  'classification': 'RECONSTRUCTED_MONITORING_REPLAY_NOT_ORIGINAL_ISSUE',
                  'state': None, 'actual': None, 'prediction': None, 'market_prediction': None,
                  'selection_after_kickoff': selected_at >= _instant(game['kickoff_at']),
                  'model_created_after_decision': None, 'prediction_created_after_decision': None}
        if row is None:
            output['state'] = 'MISSING_MODEL_OR_MATCHED_MARKET_ROW'
        else:
            for key in ('decision_at', 'source_available_at', 'latest_training_label_at',
                        'latest_training_label_season', 'model_created_at', 'prediction_created_at',
                        'prediction', 'market_prediction'):
                output[key] = row[key]
            decision = _instant(row['decision_at'])
            boundary = min(decision, _instant(game['kickoff_at']) - timedelta(hours=24))
            output['model_created_after_decision'] = _instant(row['model_created_at']) > decision
            output['prediction_created_after_decision'] = _instant(row['prediction_created_at']) > decision
            if any(_instant(row[k]) >= boundary for k in ('source_available_at', 'latest_training_label_at')):
                output['state'] = 'INFORMATION_BOUNDARY_NOT_ADMITTED'
            elif game['status'] != 'FINAL':
                output['state'] = 'NO_FINAL_OUTCOME'
            elif target == 'winner' and game['home_score'] == game['away_score']:
                output['state'] = 'TIE_OUTSIDE_CONDITIONAL_BINARY_SCORE'
            else:
                home, away = game['home_score'], game['away_score']
                output['actual'] = int(home > away) if target == 'winner' else home-away if target == 'margin' else home+away
                output['state'] = 'MATCHED_REPLAY_SCORE'
                eligible.append(output)
        ledger.append(output)

    def score(rows):
        ours, market = _metrics(rows, target, 'prediction'), _metrics(rows, target, 'market_prediction')
        return {'model': ours, 'market': market,
                'model_minus_market': {k: None if ours[k] is None else ours[k]-market[k]
                                       for k in ours if k != 'n'}}

    weeks = defaultdict(list)
    for row in ledger:
        weeks[row['week']].append(row)
    cohort = hashlib.sha256(json.dumps(sorted(r['game_id'] for r in eligible), separators=(',', ':')).encode()).hexdigest()
    return {'target': target, 'model_id': model, 'season': monitoring_season,
            'selection': dict(selection), 'census_games': len(games), 'matched_games': len(eligible),
            'matched_cohort_sha256': cohort, 'season_scores': score(eligible),
            'weekly': [{'week': week, 'census_games': len(rows),
                        **score([r for r in rows if r['state'] == 'MATCHED_REPLAY_SCORE'])}
                       for week, rows in sorted(weeks.items())],
            'ledger': ledger, 'accuracy_rule': 'Conditional non-tie home winner at p >= 0.5; equality chooses home',
            'point_errors_do_not_establish_cover_or_over_probabilities': True,
            'declarations_not_body_authenticated': True, 'complete_upstream_lineage_proved': False,
            'selection_performed': False, 'promotion_permitted': False,
            'new_fits': 0, 'new_forecast_issues': 0, 'actual_orders': 0,
            'actual_pnl': None, 'roi': None}


def invented_demo():
    selection = {'target': 'winner', 'model_id': 'invented-frozen-winner',
                 'selection_seasons': [2024, 2025], 'training_policy': 'PRIOR_SEASONS_ONLY',
                 'latest_training_label_season': 2025, 'selection_receipt_sha256': 'a'*64,
                 'selected_at': '2026-11-01T00:00:00Z'}
    census = [{'game_id': 'invented-A', 'week': 'REG_01', 'season': 2026,
               'kickoff_at': '2026-09-10T20:00:00Z', 'status': 'FINAL', 'home_score': 21, 'away_score': 14},
              {'game_id': 'invented-B', 'week': 'REG_02', 'season': 2026,
               'kickoff_at': '2026-09-17T20:00:00Z', 'status': 'FINAL', 'home_score': 14, 'away_score': 21}]
    predictions = [{'game_id': 'invented-A', 'target': 'winner', 'model_id': selection['model_id'],
                    'prediction': .7, 'market_prediction': .6,
                    'decision_at': '2026-09-09T20:00:00Z', 'source_available_at': '2026-09-09T19:00:00Z',
                    'latest_training_label_at': '2026-02-10T00:00:00Z',
                    'latest_training_label_season': 2025,
                    'model_created_at': '2026-10-01T00:00:00Z', 'prediction_created_at': '2026-11-01T00:00:00Z'}]
    return {'fixture': True, 'values_are_invented': True,
            'result': evaluate_target_replay(census, predictions, selection)}


if __name__ == '__main__':
    print(json.dumps(invented_demo(), indent=2, sort_keys=True))
