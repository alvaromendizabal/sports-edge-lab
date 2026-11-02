"""Fixed-cohort scores and directional disagreement on declared evidence.

The demo is invented. This module authenticates neither input bodies nor model
lineage, performs no selection, and never converts a replay into issued bets.
"""
from __future__ import annotations

import hashlib
import json
import math
from collections import Counter, defaultdict
from datetime import datetime


def _text(value, label):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(label + ' must be a nonempty string')
    return value


def _finite(value):
    if isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value):
        raise ValueError('A finite number is required')
    return float(value)


def _instant(value):
    value = _text(value, 'Clock')
    result = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if result.tzinfo is None:
        raise ValueError('Clocks must include their timezone')
    return result


def cohort_digest(game_ids):
    """Order-independent membership identity; duplicates are invalid."""
    ids = list(game_ids)
    for item in ids:
        _text(item, 'Game identity')
    if len(set(ids)) != len(ids):
        raise ValueError('Duplicate cohort identity')
    return hashlib.sha256(json.dumps(sorted(ids), separators=(',', ':')).encode()).hexdigest()


def _score(rows, target, field):
    result = dict(n=len(rows), log_loss=None, brier=None, accuracy=None, mae=None, rmse=None)
    if not rows:
        return result
    actual = [r['actual'] for r in rows]
    values = [r[field] for r in rows]
    if target == 'winner':
        clipped = [min(1-1e-15, max(1e-15, v)) for v in values]
        result.update(
            log_loss=sum(-y*math.log(p)-(1-y)*math.log1p(-p) for y, p in zip(actual, clipped))/len(rows),
            brier=sum((y-p)**2 for y, p in zip(actual, values))/len(rows),
            accuracy=sum((p >= .5) == bool(y) for y, p in zip(actual, values))/len(rows))
    else:
        result.update(mae=sum(abs(y-p) for y, p in zip(actual, values))/len(rows),
                      rmse=math.sqrt(sum((y-p)**2 for y, p in zip(actual, values))/len(rows)))
    return result


def _paired(rows, target):
    model = _score(rows, target, 'model')
    reference = _score(rows, target, 'reference')
    return {'model': model, 'reference': reference,
            'model_minus_reference': {k: None if model[k] is None else model[k]-reference[k]
                                      for k in model if k != 'n'}}


def _direction(value, line):
    return 'ABOVE' if value > line else 'BELOW' if value < line else 'NO_DIRECTION'


def _diagnostics(rows, target):
    if target == 'winner':
        counts = Counter(r['correctness'] for r in rows)
        return {**{k: counts[k] for k in ('BOTH_RIGHT', 'MODEL_ONLY_RIGHT', 'REFERENCE_ONLY_RIGHT', 'NEITHER_RIGHT')},
                'disagreements': counts['MODEL_ONLY_RIGHT'] + counts['REFERENCE_ONLY_RIGHT'],
                'net_extra_correct': counts['MODEL_ONLY_RIGHT'] - counts['REFERENCE_ONLY_RIGHT'],
                'accuracy_delta': (counts['MODEL_ONLY_RIGHT']-counts['REFERENCE_ONLY_RIGHT'])/len(rows) if rows else None}
    errors = Counter(r['closer_absolute_error'] for r in rows)
    result = {'absolute_error_wins': {k: errors[k] for k in ('MODEL', 'REFERENCE', 'EQUAL')}}
    for field in ('model', 'reference'):
        states = Counter(r[field+'_line_result'] for r in rows)
        n = states['RIGHT'] + states['WRONG']
        result[field+'_line_direction'] = {
            **{k: states[k] for k in ('RIGHT', 'WRONG', 'PUSH', 'NO_DIRECTION', 'NO_LINE')},
            'directional_accuracy': states['RIGHT']/n if n else None,
            'resolved_directional_n': n}
    return result


def compare_fixed_cohort(contract, census, model_rows, reference_rows):
    """Keep the headline cohort fixed; expose incomplete provider subsets separately.

    Each row declares the same target, orientation, settlement, and probability
    basis as the contract. Each census event supplies its exact decision clock
    and optional directional threshold. Unavailable/late values remain missing.
    Source/availability declarations are checked, not independently verified.
    """
    target = contract.get('target')
    if target not in {'winner', 'margin', 'total'}:
        raise ValueError('One winner, margin or total target is required')
    keys = ('target', 'orientation', 'settlement', 'value_basis')
    for key in keys:
        _text(contract.get(key), key)
    for key in ('model_id', 'reference_id'):
        _text(contract.get(key), key)
    expected = {'winner': ('HOME', 'CONDITIONAL_NON_TIE_PROBABILITY'),
                'margin': ('HOME_MINUS_AWAY', 'POINT_CENTER'),
                'total': ('TOTAL', 'POINT_CENTER')}[target]
    if (contract['orientation'], contract['value_basis']) != expected:
        raise ValueError('Target, orientation and value basis are incompatible')
    fixed = tuple(contract.get('game_ids', ()))
    if not fixed or cohort_digest(fixed) != contract.get('cohort_sha256'):
        raise ValueError('Fixed nonempty cohort digest is required')
    fixed_set = set(fixed)
    games = {}
    for raw in census:
        game = dict(raw)
        gid = _text(game.get('game_id'), 'Game identity')
        if gid in games:
            raise ValueError('Duplicate census game')
        _text(game.get('week'), 'Official week')
        _instant(game.get('decision_at'))
        if game.get('actual') is not None:
            actual = _finite(game['actual'])
            if target == 'winner' and actual not in (0, 1):
                raise ValueError('Conditional winner labels are binary; retain ties with actual=None')
            if target == 'total' and actual < 0:
                raise ValueError('A total cannot be negative')
        if game.get('line') is not None:
            _finite(game['line'])
        games[gid] = game
    if not fixed_set <= games.keys():
        raise ValueError('Fixed cohort contains a game absent from census')

    def index(rows, series_id):
        output = {}
        for raw in rows:
            row = dict(raw)
            gid = row.get('game_id')
            if gid not in games or gid in output:
                raise ValueError('Unknown or duplicate observation identity')
            if row.get('series_id') != series_id:
                raise ValueError('Observation belongs to a different model or reference series')
            if any(row.get(k) != contract[k] for k in keys):
                raise ValueError('Different target, orientation, settlement or value basis')
            if _instant(row.get('decision_at')) != _instant(games[gid]['decision_at']):
                raise ValueError('Different decision cutoff')
            value = _finite(row.get('value'))
            if target == 'winner' and not 0 <= value <= 1:
                raise ValueError('Probability outside [0,1]')
            if target == 'total' and value < 0:
                raise ValueError('A total cannot be negative')
            if target != 'winner' and row.get('line') != games[gid].get('line'):
                raise ValueError('Different directional line')
            source = _instant(row.get('source_at'))
            available = _instant(row.get('available_at'))
            if source > available:
                raise ValueError('Observation availability precedes its source clock')
            created = _instant(row.get('created_at'))
            if created < available:
                raise ValueError('Value creation precedes available inputs')
            row['late_information'] = max(source, available) > _instant(row['decision_at'])
            row['created_after_decision'] = created > _instant(row['decision_at'])
            output[gid] = row
        return output

    models = index(model_rows, contract['model_id'])
    references = index(reference_rows, contract['reference_id'])
    ledger, matched = [], []
    for gid, game in sorted(games.items()):
        m, r = models.get(gid), references.get(gid)
        row = {'game_id': gid, 'week': game['week'], 'in_fixed_cohort': gid in fixed_set,
               'actual': game.get('actual'), 'model': m['value'] if m else None,
               'reference': r['value'] if r else None,
               'model_created_after_decision': m['created_after_decision'] if m else None,
               'reference_created_after_decision': r['created_after_decision'] if r else None,
               'classification': 'DECLARED_REPLAY_NOT_ORIGINAL_ISSUED_BET'}
        for label, observation in (('model', m), ('reference', r)):
            row[label+'_clocks'] = ({k: observation[k] for k in
                ('decision_at', 'source_at', 'available_at', 'created_at')} if observation else None)
        if gid not in fixed_set:
            row['state'] = 'OUTSIDE_FIXED_COHORT'
        elif game.get('actual') is None:
            row['state'] = 'NO_ELIGIBLE_OUTCOME'
        elif m is None or r is None:
            row['state'] = 'MISSING_MODEL_OR_REFERENCE'
        elif m['late_information'] or r['late_information']:
            row['state'] = 'INFORMATION_AFTER_CUTOFF'
        else:
            row['state'] = 'MATCHED'
            if target == 'winner':
                a, b = (m['value'] >= .5) == bool(row['actual']), (r['value'] >= .5) == bool(row['actual'])
                row['correctness'] = 'BOTH_RIGHT' if a and b else 'MODEL_ONLY_RIGHT' if a else 'REFERENCE_ONLY_RIGHT' if b else 'NEITHER_RIGHT'
            else:
                em, er = abs(m['value']-row['actual']), abs(r['value']-row['actual'])
                row['closer_absolute_error'] = 'MODEL' if em < er else 'REFERENCE' if er < em else 'EQUAL'
                line = game.get('line')
                row['line'] = line
                for field in ('model', 'reference'):
                    direction = _direction(row[field], line) if line is not None else 'NO_LINE'
                    row[field+'_direction'] = direction
                    row[field+'_line_result'] = ('NO_LINE' if line is None else 'NO_DIRECTION' if direction == 'NO_DIRECTION'
                        else 'PUSH' if row['actual'] == line else 'RIGHT' if direction == _direction(row['actual'], line) else 'WRONG')
            matched.append(row)
        ledger.append(row)
    full = len(matched) == len(fixed)
    weeks = defaultdict(list)
    for row in ledger:
        weeks[row['week']].append(row)
    return {'target': target, 'model_id': contract['model_id'], 'reference_id': contract['reference_id'],
            'fixed_n': len(fixed), 'fixed_cohort_sha256': contract['cohort_sha256'],
            'census_n': len(games), 'matched_n': len(matched), 'coverage': len(matched)/len(fixed),
            'headline_state': 'COMPLETE_FIXED_COHORT' if full else 'INCOMPLETE_FIXED_COHORT',
            'headline_scores': _paired(matched, target) if full else None,
            'explicit_matched_subset': {'cohort_sha256': cohort_digest(r['game_id'] for r in matched),
                                      'scores': _paired(matched, target), 'diagnostics': _diagnostics(matched, target)},
            'weekly': [{'week': week, 'census_n': len(rows),
                        'fixed_n': sum(r['in_fixed_cohort'] for r in rows),
                        'matched_n': sum(r['state'] == 'MATCHED' for r in rows),
                        'matched_subset_scores': _paired([r for r in rows if r['state'] == 'MATCHED'], target),
                        'diagnostics': _diagnostics([r for r in rows if r['state'] == 'MATCHED'], target)}
                       for week, rows in sorted(weeks.items())],
            'ledger': ledger, 'probability_clipping_epsilon': 1e-15,
            'winner_equality_rule': 'p >= 0.5 chooses HOME',
            'point_directions_are_not_probabilities': True,
            'declarations_not_body_authenticated': True, 'selection_performed': False,
            'promotion_permitted': False, 'actual_pnl': None, 'roi': None, 'actual_orders': 0}


def invented_inputs():
    ids = ['invented-A', 'invented-B', 'invented-C', 'invented-D']
    contract = dict(target='winner', orientation='HOME', settlement='FULL_GAME_CONDITIONAL_NO_TIE',
                    value_basis='CONDITIONAL_NON_TIE_PROBABILITY', game_ids=ids, cohort_sha256=cohort_digest(ids),
                    model_id='invented-frozen-model', reference_id='invented-reference')
    census = [dict(game_id=g, week='REG_01' if i < 2 else 'REG_02', actual=i % 2,
                   decision_at='2026-09-09T20:00:00Z') for i, g in enumerate(ids)]
    def rows(values, series_id):
        return [dict(game_id=g, series_id=series_id, **{k: contract[k] for k in ('target','orientation','settlement','value_basis')},
                     decision_at=census[i]['decision_at'], value=v, source_at='2026-09-09T18:00:00Z',
                     available_at='2026-09-09T19:00:00Z', created_at='2026-11-01T00:00:00Z')
                for i, (g, v) in enumerate(zip(ids, values))]
    return contract, census, rows([.3, .7, .7, .3], contract['model_id']), rows([.7, .7, .3, .3], contract['reference_id'])


def invented_demo():
    inputs = invented_inputs()
    return {'fixture': True, 'values_are_invented': True,
            'complete': compare_fixed_cohort(*inputs),
            'missing_provider_row': compare_fixed_cohort(*inputs[:3], inputs[3][:-1])}


if __name__ == '__main__':
    print(json.dumps(invented_demo(), indent=2, sort_keys=True))
