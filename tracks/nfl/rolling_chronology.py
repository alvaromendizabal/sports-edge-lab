"""Declared weekly-origin and residual-feedback checks; all demo data invented.

This example neither fits a model nor authenticates a real source or issue
ledger. Passing declarations is necessary, never sufficient, for a live claim.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import json
import math


def clock(value):
    if not isinstance(value, str):
        raise ValueError('A timezone-aware clock is required')
    result = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if result.tzinfo is None or result.utcoffset() is None:
        raise ValueError('A timezone-aware clock is required')
    return result.astimezone(timezone.utc)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def validate_policy(policy):
    if policy['mode'] not in ('FROZEN_HISTORICAL', 'SEPARATE_ROLLING_EXPERIMENT'):
        raise ValueError('Unknown update policy')
    if not isinstance(policy['policy_id'], str) or not policy['policy_id'].strip():
        raise ValueError('Policy identity required')
    if type(policy['horizon_hours']) is not int or policy['horizon_hours'] <= 0:
        raise ValueError('Positive integer information horizon required')
    if type(policy['historical_last_season']) is not int:
        raise ValueError('Historical season boundary required')
    if policy['selection_uses_monitored_outcomes'] is not False:
        raise ValueError('Monitored outcomes cannot select recipes')
    if policy['promotion_permitted'] is not False:
        raise ValueError('This example grants no promotion permission')
    clock(policy['registered_at'])


def weekly_origin(policy, games):
    """One declared league week, not ISO week, with a strict label boundary."""
    validate_policy(policy)
    if not games:
        raise ValueError('A nonempty declared week is required')
    ids = [g['game_id'] for g in games]
    if len(ids) != len(set(ids)):
        raise ValueError('Duplicate game in week')
    if len({(g['season'], g['phase'], g['week']) for g in games}) != 1:
        raise ValueError('Different official weeks cannot share this origin')
    cutoff = min(clock(g['kickoff']) for g in games) - timedelta(hours=policy['horizon_hours'])
    result = {'policy_id': policy['policy_id'], 'policy_sha256': digest(policy),
            'fit_information_before': cutoff.isoformat(), 'game_ids': sorted(ids),
            'week_membership_sha256': digest(sorted(ids)),
            'historical_reconstruction': clock(policy['registered_at']) >= cutoff}
    result['origin_sha256'] = digest(result)
    return result


def validate_origin(policy, origin):
    validate_policy(policy)
    if origin.get('origin_sha256') != digest({k:v for k,v in origin.items() if k!='origin_sha256'}):
        raise ValueError('Declared origin body changed')
    if origin['policy_sha256'] != digest(policy) or origin['policy_id'] != policy['policy_id']:
        raise ValueError('Origin belongs to a different policy')
    ids = origin['game_ids']
    if not ids or len(ids) != len(set(ids)) or origin['week_membership_sha256'] != digest(sorted(ids)):
        raise ValueError('Declared origin membership changed')
    clock(origin['fit_information_before'])


def admitted_training_labels(policy, origin, labels):
    """Return eligible IDs and every exclusion; never infer a missing clock."""
    validate_origin(policy, origin)
    boundary = clock(origin['fit_information_before'])
    seen = set(); admitted = []; excluded = []
    for label in labels:
        game = label['game_id']
        if game in seen:
            raise ValueError('Duplicate training label')
        seen.add(game)
        if game in origin['game_ids']:
            reason = 'EVALUATION_EVENT_IS_NOT_A_TRAINING_LABEL'
        elif label.get('available_at') is None:
            reason = 'LABEL_AVAILABILITY_MISSING'
        elif clock(label['available_at']) >= boundary:
            reason = 'LABEL_NOT_AVAILABLE_STRICTLY_BEFORE_ORIGIN'
        elif (policy['mode'] == 'FROZEN_HISTORICAL'
              and label['season'] > policy['historical_last_season']):
            reason = 'CURRENT_LABEL_EXCLUDED_BY_FROZEN_POLICY'
        else:
            admitted.append(game); continue
        excluded.append({'game_id': game, 'reason': reason})
    return {'admitted_game_ids': sorted(admitted),
            'excluded': sorted(excluded, key=lambda x: x['game_id']),
            'new_fits': 0, 'selection_performed': False}


def matured_feedback(policy, origin, target, rows):
    """Prior OOF residuals only; availability and disjointness are declarations.

    No residual from the target week, an in-sample prediction, or an unresolved
    result can become an error-feedback feature at this origin.
    """
    validate_origin(policy, origin)
    if target not in ('winner', 'margin', 'total'):
        raise ValueError('Unknown target')
    before = clock(origin['fit_information_before']); selected = []; excluded = []; seen = set()
    for row in rows:
        game = row['game_id']
        if game in seen:
            raise ValueError('Duplicate feedback event')
        seen.add(game)
        reason = None
        if row['target'] != target:
            reason = 'DIFFERENT_TARGET'
        elif game in origin['game_ids']:
            reason = 'CURRENT_WEEK_FEEDBACK_FORBIDDEN'
        elif row['prediction_kind'] != 'FORWARD_OOF' or game in row['training_game_ids']:
            reason = 'NOT_FORWARD_OUT_OF_FOLD'
        elif row.get('outcome_available_at') is None:
            reason = 'UNRESOLVED_OUTCOME_CLOCK'
        elif clock(row['outcome_available_at']) >= before:
            reason = 'OUTCOME_NOT_MATURE_AT_ORIGIN'
        elif clock(row['prior_information_before']) >= before:
            reason = 'PREDICTION_ORIGIN_NOT_EARLIER'
        elif clock(row['latest_training_label_at']) >= clock(row['prior_information_before']):
            reason = 'PRIOR_FIT_USED_LATE_LABEL'
        elif clock(row['latest_feature_available_at']) >= clock(row['prior_information_before']):
            reason = 'PRIOR_FEATURE_WAS_LATE'
        elif clock(row['prior_information_before']) > clock(row['kickoff']) - timedelta(hours=policy['horizon_hours']):
            reason = 'PRIOR_HORIZON_TOO_LATE'
        elif (policy['mode'] == 'FROZEN_HISTORICAL'
              and row['season'] > policy['historical_last_season']):
            reason = 'CURRENT_RESIDUAL_EXCLUDED_BY_FROZEN_POLICY'
        if reason:
            excluded.append({'game_id': game, 'reason': reason}); continue
        values = [row[k] for k in ('actual', 'prediction', 'reference')]
        if any(type(v) not in (int, float) or not math.isfinite(v) for v in values):
            raise ValueError('Finite target values are required')
        if target == 'winner' and (row['actual'] not in (0, 1) or any(not 0 <= v <= 1 for v in values[1:])):
            raise ValueError('Conditional non-tie winner values are required')
        if clock(row['outcome_available_at']) < clock(row['kickoff']):
            raise ValueError('Outcome predates the event')
        selected.append({'game_id': game, 'model_residual': row['actual'] - row['prediction'],
                         'reference_residual': row['actual'] - row['reference'],
                         'signed_disagreement': row['prediction'] - row['reference'],
                         'evidence_class': 'DECLARED_OOF_RECONSTRUCTION_NO_ORIGINAL_ISSUE_CLAIM'})
    return {'rows': sorted(selected, key=lambda x: x['game_id']),
            'excluded': sorted(excluded, key=lambda x: x['game_id']),
            'target': target, 'new_fits': 0, 'promotion_permitted': False}


def classify_forecast(policy, row):
    """Distinguish reconstructed, late and timely declarations without backdating."""
    validate_policy(policy)
    if row['policy_id'] != policy['policy_id']:
        raise ValueError('Forecast policy differs')
    kickoff = clock(row['kickoff']); cutoff = kickoff - timedelta(hours=policy['horizon_hours'])
    created = clock(row['created_at']); issued = clock(row['issued_at']); observed = clock(row['observed_at'])
    if not created <= issued <= observed:
        raise ValueError('Actual creation, issue and observation clocks are inconsistent')
    if clock(row['model_completed_at']) > created:
        raise ValueError('Prediction predates its fitted model')
    if clock(row['latest_input_available_at']) > created:
        raise ValueError('Prediction predates an input')
    if clock(policy['registered_at']) > issued:
        return 'RECONSTRUCTION_BEFORE_POLICY_REGISTRATION'
    if created >= kickoff or issued >= kickoff:
        return 'RECONSTRUCTED_AFTER_EVENT_START'
    if clock(row['latest_input_available_at']) >= cutoff:
        return 'INPUT_OUTSIDE_STRICT_REGISTERED_HORIZON'
    if created > cutoff or issued > cutoff:
        return 'LATE_PREGAME_MONITORING'
    return 'DECLARED_TIMELY_PREGAME_REQUIRES_DURABLE_ISSUE_PROOF'


def invented_inputs():
    policy = dict(policy_id='invented-rolling-t2-v1', mode='SEPARATE_ROLLING_EXPERIMENT',
                  horizon_hours=2, historical_last_season=2030, registered_at='2031-08-01T00:00:00Z',
                  selection_uses_monitored_outcomes=False, promotion_permitted=False)
    games = [dict(game_id='invented-week2-a', season=2031, phase='REG', week=2, kickoff='2031-09-14T17:00:00Z')]
    labels = [dict(game_id='invented-week1', season=2031, available_at='2031-09-08T17:00:00Z')]
    feedback = [dict(game_id='invented-week1', season=2031, target='winner', prediction_kind='FORWARD_OOF',
                     training_game_ids=['invented-earlier-season'], kickoff='2031-09-07T17:00:00Z',
                     prior_information_before='2031-09-07T15:00:00Z', latest_training_label_at='2031-01-01T00:00:00Z',
                     latest_feature_available_at='2031-09-07T14:59:00Z', outcome_available_at='2031-09-08T17:00:00Z',
                     actual=1, prediction=.7, reference=.6)]
    return policy, games, labels, feedback


def demo():
    policy, games, labels, feedback = invented_inputs(); origin = weekly_origin(policy, games)
    return {'evidence_class': 'INVENTED_ENGINEERING_DEMONSTRATION', 'origin': origin,
            'training': admitted_training_labels(policy, origin, labels),
            'feedback': matured_feedback(policy, origin, 'winner', feedback),
            'actual_orders': 0, 'scientific_performance_claimed': False}


if __name__ == '__main__':
    print(json.dumps(demo(), indent=2))
