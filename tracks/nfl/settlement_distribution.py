"""Score a declared discrete game distribution at an exact settlement line.

No distributions are learned here. Inputs are declarations, not authenticated
source bodies. The executable example is invented; it is not a betting result.
"""
from __future__ import annotations

from datetime import datetime
import hashlib
import json
import math


STATES = ('WIN', 'PUSH', 'LOSS')


def _text(value, label):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(label + ' must be nonempty text')
    return value


def _number(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError('A finite number is required')
    return float(value)


def _time(value):
    result = datetime.fromisoformat(_text(value, 'Clock').replace('Z', '+00:00'))
    if result.tzinfo is None:
        raise ValueError('Timezone is required')
    return result


def _integer(value):
    result = _number(value)
    if not result.is_integer():
        raise ValueError('Discrete game support must use integer points')
    return int(result)


def _sha(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def settlement_probabilities(distribution, instrument):
    """Bind an integer PMF to a declared game, target, line and rules version.

    Margin means home minus away. A HOME threshold of 3 is the home -3
    instrument; an AWAY threshold of 3 is its complementary away +3 side.
    Totals use OVER/UNDER. Equality returns the stake under the supported
    REFUND_AT_EQUALITY contract. Other settlements need a different adapter.
    """
    for key in ('event_id', 'target', 'settlement_id'):
        if _text(distribution[key], key) != _text(instrument[key], key):
            raise ValueError('Distribution/instrument mismatch: ' + key)
    target = distribution['target']
    if target not in ('margin', 'total'):
        raise ValueError('Only full game margin and total PMFs are supported')
    _text(distribution['model_id'], 'Model identity')
    _text(distribution['source_id'], 'Source identity')
    _text(instrument['instrument_id'], 'Instrument identity')
    if instrument['equality_rule'] != 'REFUND_AT_EQUALITY':
        raise ValueError('Unsupported equality settlement')
    cutoff = _time(distribution['decision_at'])
    if cutoff != _time(instrument['decision_at']):
        raise ValueError('Decision clocks differ')
    kickoff = _time(distribution['kickoff_at'])
    if kickoff != _time(instrument['kickoff_at']) or cutoff >= kickoff:
        raise ValueError('A matching strictly pregame decision is required')
    source = _time(distribution['source_asof'])
    available = _time(distribution['source_available_at'])
    computed = _time(distribution['computed_at'])
    model_available = _time(distribution['model_available_at'])
    labels = _time(distribution['labels_available_through'])
    if source > cutoff or labels >= cutoff:
        raise ValueError('Source or training labels cross the declared decision cutoff')
    if not source <= available <= computed or model_available > computed or labels > model_available:
        raise ValueError('Impossible source/model/computation chronology')
    kind = distribution['evidence_class']
    issued = distribution.get('issued_at')
    if kind == 'ORIGINAL_ISSUED_DECLARATION':
        if issued is None or not computed <= _time(issued) <= cutoff:
            raise ValueError('Original issue must follow computation and precede cutoff')
        if available > cutoff or model_available > cutoff:
            raise ValueError('Original issue requires sources and model available at cutoff')
    elif kind == 'RECONSTRUCTION':
        if issued is not None:
            raise ValueError('A reconstruction cannot acquire an original issue clock')
    else:
        raise ValueError('Unknown evidence class')
    side = instrument['side']
    positive_side, negative_side = ('HOME', 'AWAY') if target == 'margin' else ('OVER', 'UNDER')
    if side not in (positive_side, negative_side):
        raise ValueError('Side does not match target orientation')
    threshold = _number(instrument['threshold'])
    if not (2 * threshold).is_integer() or (target == 'total' and threshold < 0):
        raise ValueError('An integer or half-integer game line is required')
    support = distribution['support']
    if not isinstance(support, list) or not support:
        raise ValueError('A nonempty explicit PMF is required, not a point center')
    points, weights = [], []
    for row in support:
        point, probability = _integer(row['points']), _number(row['probability'])
        if probability < 0 or probability > 1 or (target == 'total' and point < 0):
            raise ValueError('Invalid support or probability')
        points.append(point); weights.append(probability)
    if len(set(points)) != len(points):
        raise ValueError('Duplicate support point')
    mass = math.fsum(weights)
    if not math.isclose(mass, 1.0, abs_tol=1e-12, rel_tol=0):
        raise ValueError('PMF mass must sum to one within 1e-12')
    sign = 1 if side == positive_side else -1
    buckets = {state: [] for state in STATES}
    for point, weight in zip(points, weights):
        delta = sign * (point - threshold)
        state = 'WIN' if delta > 0 else 'LOSS' if delta < 0 else 'PUSH'
        buckets[state].append(weight / mass)
    probabilities = {state: math.fsum(buckets[state]) for state in STATES}
    nonpush = probabilities['WIN'] + probabilities['LOSS']
    return {
        'schema': 'nfl.declared-settlement-pmf.v1',
        'event_id': distribution['event_id'], 'model_id': distribution['model_id'],
        'instrument_id': instrument['instrument_id'], 'target': target,
        'settlement_id': instrument['settlement_id'], 'side': side,
        'threshold': threshold, 'decision_at': distribution['decision_at'],
        'evidence_class': kind, 'original_issue_claim': kind == 'ORIGINAL_ISSUED_DECLARATION',
        'late_source_possession': available > cutoff, 'late_model_availability': model_available > cutoff,
        'probabilities': probabilities,
        'conditional_win_given_no_push': probabilities['WIN'] / nonpush if nonpush else None,
        'input_mass': mass, 'roundoff_mass_normalized': mass != 1.0,
        'distribution_sha256': _sha(distribution), 'instrument_sha256': _sha(instrument),
        'source_authentication': 'CALLER_RESPONSIBILITY',
        'actual_profit': None, 'promotion_permission': False, 'order': None,
    }


def score_outcome(distribution, instrument, actual_points):
    """Proper three-state losses; conditional binary losses exclude pushes.

    Brier is the SUM over three categories (range 0..2), not divided by three.
    Exact impossible outcomes have infinite log loss: no hidden clipping.
    Multiclass accuracy uses a unique mode only; a tied mode is abstention.
    """
    mapped = settlement_probabilities(distribution, instrument)
    if actual_points is None:
        return dict(mapped, actual_state=None, log_loss_3state=None, brier_3state=None,
                    conditional_binary_log_loss=None, conditional_binary_brier=None,
                    unique_mode_correct=None, scoring_status='MISSING_OUTCOME')
    actual = _integer(actual_points)
    if mapped['target'] == 'total' and actual < 0:
        raise ValueError('Total points cannot be negative')
    sign = 1 if mapped['side'] in ('HOME', 'OVER') else -1
    delta = sign * (actual - mapped['threshold'])
    state = 'WIN' if delta > 0 else 'LOSS' if delta < 0 else 'PUSH'
    probabilities = mapped['probabilities']
    likelihood = probabilities[state]
    loss = -math.log(likelihood) if likelihood else math.inf
    brier = math.fsum((probabilities[s] - (s == state)) ** 2 for s in STATES)
    q = mapped['conditional_win_given_no_push']
    binary_loss = binary_brier = None
    if state != 'PUSH' and q is not None:
        event_probability = q if state == 'WIN' else 1 - q
        binary_loss = -math.log(event_probability) if event_probability else math.inf
        binary_brier = (q - (state == 'WIN')) ** 2
    modes = [s for s in STATES if probabilities[s] == max(probabilities.values())]
    return dict(mapped, actual_state=state, log_loss_3state=loss, brier_3state=brier,
                conditional_binary_log_loss=binary_loss, conditional_binary_brier=binary_brier,
                unique_mode_correct=(modes[0] == state) if len(modes) == 1 else None,
                scoring_status='SCORED', log_loss_clipping=None)


def invented_inputs():
    distribution = {
        'event_id': 'invented-game', 'target': 'margin', 'settlement_id': 'FULL_GAME_OVERTIME_V1',
        'model_id': 'invented-pmf', 'source_id': 'invented-source',
        'decision_at': '2026-09-10T22:00:00Z', 'kickoff_at': '2026-09-11T00:00:00Z',
        'source_asof': '2026-09-10T20:00:00Z', 'source_available_at': '2026-09-10T20:01:00Z',
        'model_available_at': '2026-09-10T20:30:00Z', 'labels_available_through': '2026-09-09T00:00:00Z',
        'computed_at': '2026-09-10T21:00:00Z', 'issued_at': '2026-09-10T21:01:00Z',
        'evidence_class': 'ORIGINAL_ISSUED_DECLARATION',
        'support': [{'points': -7, 'probability': .2}, {'points': 3, 'probability': .1}, {'points': 7, 'probability': .7}],
    }
    instrument = {key: distribution[key] for key in ('event_id', 'target', 'settlement_id', 'decision_at', 'kickoff_at')}
    instrument.update(instrument_id='invented-home-minus-three', side='HOME', threshold=3, equality_rule='REFUND_AT_EQUALITY')
    return distribution, instrument


if __name__ == '__main__':
    distribution, instrument = invented_inputs()
    print(json.dumps({'fixture': 'INVENTED_NOT_SPORTS_EVIDENCE', 'result': score_outcome(distribution, instrument, 3)}, indent=2, allow_nan=False))
