"""Credential-free comparison contracts. All demonstration values are invented."""
from __future__ import annotations
import hashlib
import json
import math
import re
from typing import Iterable, Mapping


def reporting_inventory(expected: Iterable[Mapping], reported: Iterable[Mapping], *,
                        monitoring_season: int = 2026) -> dict:
    """Account for declared retained models before comparing any supplied scores.

    This checks a caller's explicit inventory, not the completeness of private
    storage. Digests describe declared identities; this helper reads no bodies.
    No role, missing score or exact alias grants selection/promotion permission.
    """
    roles = {'MARKET_REFERENCE', 'FROZEN_CANDIDATE', 'WEEKLY_UPDATED', 'UNRESOLVED'}
    policies = {'PRIOR_SEASONS_ONLY', 'USES_CURRENT_SEASON_LABELS', 'NOT_APPLICABLE', 'UNKNOWN'}
    if not isinstance(monitoring_season, int) or isinstance(monitoring_season, bool):
        raise ValueError('Monitoring season must be an integer')

    def indexed(items, label):
        result = {}
        for item in items:
            row = dict(item)
            model, season = row.get('model_id'), row.get('season')
            if not isinstance(model, str) or not model.strip():
                raise ValueError('Model identity must be a nonempty string')
            if not isinstance(season, int) or isinstance(season, bool):
                raise ValueError('Season must be an integer')
            key = (season, model)
            if key in result:
                raise ValueError('Duplicate ' + label + ' model-season identity')
            result[key] = row
        return result

    inventory, rows = indexed(expected, 'expected'), indexed(reported, 'reported')
    if not inventory:
        raise ValueError('An explicit nonempty expected inventory is required')
    if set(rows) - set(inventory):
        raise ValueError('Reported model-season identity is outside the expected inventory')
    output, groups, unverified_aliases = [], {}, []
    identity_fields = ('prediction_vector_sha256', 'cohort_sha256', 'reference_sha256')
    for key, declaration in sorted(inventory.items()):
        season, model = key
        role, policy = declaration.get('role'), declaration.get('training_policy')
        if role not in roles or policy not in policies:
            raise ValueError('Explicit recognized role and training policy are required')
        if role == 'MARKET_REFERENCE' and policy != 'NOT_APPLICABLE':
            raise ValueError('A MARKET reference has no model training policy')
        row = rows.get(key)
        loss = row.get('primary_loss') if row is not None else None
        if loss is not None and (isinstance(loss, bool) or not isinstance(loss, (int, float))
                                 or not math.isfinite(loss) or loss < 0):
            raise ValueError('Loss must be finite and nonnegative, or missing')
        state = ('MISSING_REPORT_ROW' if row is None else
                 'REPORTED_NO_AUTHENTICATED_SCORE' if loss is None else 'REPORTED_SCORE')
        record = {'model_id': model, 'season': season, 'role': role,
                  'training_policy': policy, 'report_state': state, 'primary_loss': loss,
                  'monitoring_only': season == monitoring_season,
                  'current_policy_ineligible': season == monitoring_season and policy == 'USES_CURRENT_SEASON_LABELS'}
        output.append(record)
        if row is not None:
            for field in identity_fields:
                if field in row and (not isinstance(row[field], str) or not re.fullmatch('[0-9a-f]{64}', row[field])):
                    raise ValueError('A supplied identity digest must be lowercase SHA-256')
        if row is None or loss is None or not all(field in row for field in identity_fields) or not isinstance(row.get('target'), str) or not row['target']:
            unverified_aliases.append({'season': season, 'model_id': model})
        else:
            signature = (season, row['target'], *(row[field] for field in identity_fields))
            groups.setdefault(signature, []).append(model)
    aliases = [{'season': signature[0], 'target': signature[1],
                **dict(zip(identity_fields, signature[2:])), 'model_ids': sorted(models)}
               for signature, models in sorted(groups.items()) if len(models) > 1]
    return {'fixture': True, 'expected_model_season_rows': len(inventory),
            'reported_model_season_rows': len(rows), 'rows': output,
            'all_expected_rows_reported': set(inventory) == set(rows),
            'missing_report_rows': [r for r in output if r['report_state'] == 'MISSING_REPORT_ROW'],
            'reported_without_score': [r for r in output if r['report_state'] == 'REPORTED_NO_AUTHENTICATED_SCORE'],
            'declared_exact_alias_groups': aliases,
            'distinct_complete_declared_prediction_identities': len(groups),
            'alias_identity_not_established': unverified_aliases,
            'identity_bodies_authenticated_by_this_helper': False,
            'full_private_storage_inventory_authenticated': False,
            'scores_compared_or_ranked': False, 'selected_champion': None,
            'selection_permitted': False, 'promotion_permitted': False,
            'new_fits': 0, 'new_forecast_issues': 0, 'actual_orders': 0}


def cohort_identity(game_ids: Iterable[str]) -> str:
    games = list(game_ids)
    if not games or len(games) != len(set(games)) or any(not isinstance(x, str) or not x for x in games):
        raise ValueError('A nonempty unique game census is required')
    return hashlib.sha256(json.dumps(sorted(games), separators=(',', ':')).encode()).hexdigest()


def comparison_roles(rows: Iterable[Mapping], *, monitoring_season: int = 2026) -> dict:
    """Describe existing score rows without selecting, fitting, or promoting a model.

    Each row describes one model on the same explicit games and reference values.
    A missing challenger remains missing. A historical minimum is descriptive.
    The returned scores are not forecast probabilities or expected betting profit.
    """
    rows = [dict(r) for r in rows]
    if not rows:
        raise ValueError('No authenticated comparison rows supplied')
    ids = [r['model_id'] for r in rows]
    if len(ids) != len(set(ids)):
        raise ValueError('Duplicate model row')
    seasons = {r['season'] for r in rows}
    if len(seasons) != 1:
        raise ValueError('Compare one season at a time')
    reference = None
    for r in rows:
        if not isinstance(r['season'], int) or isinstance(r['season'], bool):
            raise ValueError('Season must be an integer')
        ids_for_row = r['game_ids']
        digest = cohort_identity(ids_for_row)
        market_values = r['market_reference_by_game']
        if set(market_values) != set(ids_for_row):
            raise ValueError('Reference values must cover the exact game census')
        if any(isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x) for x in market_values.values()):
            raise ValueError('Reference values must be finite')
        signature = (digest, tuple(sorted(market_values.items())))
        if reference is not None and signature != reference:
            raise ValueError('Models do not share identical games and reference values')
        reference = signature
        loss = r.get('primary_loss')
        if loss is not None and (isinstance(loss, bool) or not isinstance(loss, (int, float)) or not math.isfinite(loss) or loss < 0):
            raise ValueError('Loss must be finite and nonnegative, or missing')
    season = next(iter(seasons))
    eligible = [r for r in rows if r.get('primary_loss') is not None]
    minimum = None
    if season != monitoring_season and eligible:
        value = min(r['primary_loss'] for r in eligible)
        minimum = {'role': 'RETROSPECTIVE_PRIMARY_LOSS_MINIMUM_NOT_A_SELECTED_CHAMPION',
                   'model_ids': sorted(r['model_id'] for r in eligible if r['primary_loss'] == value),
                   'primary_loss': value, 'promotion_permitted': False,
                   'winner_adjusted_interval': False}
    return {'fixture': True, 'season': season, 'cohort_sha256': reference[0],
            'games': len(rows[0]['game_ids']), 'rows': [
                {'model_id': r['model_id'], 'primary_loss': r.get('primary_loss'),
                 'status': 'NO_AUTHENTICATED_MODEL_ROWS_IN_THIS_COMPARISON' if r.get('primary_loss') is None else 'FROZEN_CANDIDATE_SCORE_NOT_SELECTION'}
                for r in rows],
            'retrospective_minimum': minimum, 'selected_champion': None,
            'selection_permitted': False, 'monitoring_only': season == monitoring_season,
            'new_fits': 0, 'actual_orders': 0}


def invented_demo() -> dict:
    # Tiny artificial example; no provider, team, model recipe, or private data.
    common = {'season': 2025, 'game_ids': ['invented-A', 'invented-B'],
              'market_reference_by_game': {'invented-A': 0.4, 'invented-B': 0.6}}
    return comparison_roles([{**common, 'model_id': 'candidate-A', 'primary_loss': 0.65},
                             {**common, 'model_id': 'candidate-B', 'primary_loss': 0.62},
                             {**common, 'model_id': 'unrun-challenger', 'primary_loss': None}])


def invented_inventory_demo() -> dict:
    expected = [{'model_id': name, 'season': 2026, 'role': role, 'training_policy': policy}
        for name, role, policy in [('invented-reference', 'MARKET_REFERENCE', 'NOT_APPLICABLE'),
            ('invented-frozen', 'FROZEN_CANDIDATE', 'PRIOR_SEASONS_ONLY'),
            ('invented-weekly', 'WEEKLY_UPDATED', 'USES_CURRENT_SEASON_LABELS'),
            ('invented-retained', 'UNRESOLVED', 'UNKNOWN')]]
    reported = [{'model_id': name, 'season': 2026, 'primary_loss': loss}
        for name, loss in [('invented-reference', .7), ('invented-frozen', .65), ('invented-weekly', None)]]
    return reporting_inventory(expected, reported)


if __name__ == '__main__':
    print(json.dumps({'comparison': invented_demo(), 'inventory': invented_inventory_demo()}, indent=2, sort_keys=True))

