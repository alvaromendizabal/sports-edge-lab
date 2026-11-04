"""Validate display of a later genuine issue without changing prior evidence."""
import hashlib
import json
from pathlib import Path
import re
from datetime import timedelta

from market_clock import instant
from point_markets import require, scalar

HERE = Path(__file__).resolve().parent
ROOT_FIELDS = {'schema', 'owner_return_sha256', 'source_member_sha256', 'as_of',
               'new_fits', 'owner_pipeline_accepted', 'cards', 'limitations'}
CARD_FIELDS = {'game_id', 'model_id', 'model_label', 'origin', 'pick',
               'pick_probability', 'home_win_probability', 'home_margin', 'total',
               'home_score_center', 'away_score_center', 'actual_issue_at',
               'source_asof', 'fit_completed', 'horizon', 'issue_class',
               'full_pipeline_selection_qualified', 'injury_inputs_verified',
               'correct', 'unavailable_reason'}


def choose_primary_issue(game, previous, issued):
    if game['completed'] or issued is None:
        return previous
    if previous.get('model_id') != issued['model_id']:
        return previous
    prior_time = previous.get('actual_issue_at')
    return issued if not prior_time or instant(issued['actual_issue_at']) > instant(prior_time) else previous


def validate_primary_issue(data, coverage):
    require(set(data) == ROOT_FIELDS, 'Unknown primary-issue fields')
    require(data['schema'] == 'sports-edge-lab.nfl.preserved-primary-issue-addendum.n037.v1',
            'Unknown issue schema')
    require(data['owner_pipeline_accepted'] is False and type(data['new_fits']) is int
            and data['new_fits'] == 0, 'An early issue is not a newly fitted or accepted model')
    require(all(re.fullmatch('[0-9a-f]{64}', data[k]) for k in
            ('owner_return_sha256', 'source_member_sha256')), 'Invalid issue custody digest')
    for k in ROOT_FIELDS - {'cards', 'limitations'}:
        scalar(data[k])
    require(isinstance(data['limitations'], list) and len(data['limitations']) >= 4,
            'Missing issue limitations')
    for item in data['limitations']:
        scalar(item)
    require(isinstance(data['cards'], list) and len(data['cards']) == 29, 'Declared issue has 29 games')
    games = {g['game_id']: g for g in coverage['all_games']}
    seen = set()
    for card in data['cards']:
        require(set(card) == CARD_FIELDS, 'Unknown or missing primary card fields')
        for value in card.values():
            scalar(value)
        gid = card['game_id']
        require(gid in games and gid not in seen, 'Unknown or duplicate primary game')
        seen.add(gid)
        game = games[gid]
        require(not game['completed'] and game['actual'] is None, 'Completed game cannot receive a new display issue')
        require(card['model_id'] == 'preserved_primary_refresh'
                and card['origin'] == 'saved_heads_with_current_parent_refresh',
                'Issue belongs only to the preserved-primary stream')
        require(card['correct'] is None and card['unavailable_reason'] is None
                and card['fit_completed'] is None, 'No invented outcome, unavailable state or new fit clock')
        require(card['full_pipeline_selection_qualified'] is False
                and card['injury_inputs_verified'] is False, 'Unverified issue qualification cannot be promoted')
        require(card['horizon'] == 'EARLY_BEFORE_T2'
                and card['issue_class'] == 'EARLY_FORWARD_RESEARCH_ISSUE', 'Early issue cannot be relabeled final-hour')
        require(instant(card['source_asof']) <= instant(card['actual_issue_at']) == instant(data['as_of'])
                < instant(game['kickoff_utc']) - timedelta(hours=2), 'Source/issue/early-kickoff clocks differ')
        p = card['home_win_probability']
        require(type(p) in (int, float) and 0 <= p <= 1 and abs(p*1000-round(p*1000)) < 1e-7,
                'Home probability must be rounded and finite')
        require(card['pick'] == (game['home'] if p >= .5 else game['away']), 'Pick contradicts probability/team binding')
        require(abs(card['pick_probability'] - max(p, 1-p)) < 1e-7, 'Picked-side probability differs')
        for name in ('home_margin', 'total', 'home_score_center', 'away_score_center'):
            require(type(card[name]) in (int, float) and abs(card[name]*10-round(card[name]*10)) < 1e-7,
                    'Point centers must be rounded')
        require(abs(card['home_score_center']+card['away_score_center']-card['total']) <= .11
                and abs(card['home_score_center']-card['away_score_center']-card['home_margin']) <= .11,
                'Score centers do not reconcile within display rounding')
    return {'primary_issue_status': 'PUBLIC_EARLY_ISSUE_ADDENDUM_VALIDATED',
            'primary_issue_games': 29, 'primary_issue_new_fits': 0,
            'primary_issue_historical_metrics_changed': False,
            'primary_issue_injury_inputs_verified': False}


def load_primary_issue(coverage):
    path = HERE / 'primary_issue_n035.json'
    data = json.loads(path.read_text())
    return data, {**validate_primary_issue(data, coverage),
                  'primary_issue_sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
