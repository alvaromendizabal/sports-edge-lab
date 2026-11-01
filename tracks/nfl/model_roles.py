"""Credential-free comparison contracts. All demonstration values are invented."""
from __future__ import annotations
import hashlib
import json
import math
from typing import Iterable, Mapping


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


if __name__ == '__main__':
    print(json.dumps(invented_demo(), indent=2, sort_keys=True))
