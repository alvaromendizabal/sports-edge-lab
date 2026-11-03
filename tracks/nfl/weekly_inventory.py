"""Fail-closed disclosure and chronology for public rounded NFL weekly outputs.

This checks output disclosure, complete event joins, missing streams, clocks and
provider counts. It does not reproduce or accept private training. Historical
reconstruction and original issues retain distinct identities.
"""
import hashlib
import json
import math
from datetime import datetime, timedelta
from pathlib import Path
from public_snapshot import FORBIDDEN

HERE = Path(__file__).resolve().parent
PROVIDERS = {'DraftKings', 'Kalshi', 'Polymarket'}
ALLOWED_FIELDS = {'$': ['active_providers',
       'as_of',
       'default_timezone',
       'inventory',
       'limitations',
       'model_sets',
       'notes',
       'periods',
       'provider_coverage',
       'schema',
       'season',
       'source_census',
       'summary',
       'week8',
       'week8_disagreements',
       'week8_metrics',
       'week9'],
 '$.source_census': ['completed_games',
                     'non_ties',
                     'observed_at',
                     'scheduled_games',
                     'source_refresh_completed_at',
                     'unstarted_games'],
 '$.periods': ['current_week', 'last_completed_week'],
 '$.model_sets[]': ['id', 'label', 'origin', 'qualification'],
 '$.week9[]': ['actual',
               'away',
               'forecasts',
               'game_id',
               'home',
               'kickoff_los_angeles',
               'kickoff_utc',
               'providers',
               'week'],
 '$.week9[].forecasts[]': ['actual_issue_at',
                           'away_score_center',
                           'before_T1',
                           'before_T2',
                           'bet_decision',
                           'bet_reason',
                           'correct',
                           'eligible_final_hour',
                           'fit_completed',
                           'full_pipeline_selection_qualified',
                           'home_margin',
                           'home_score_center',
                           'home_win_probability',
                           'horizon',
                           'issue_class',
                           'margin_error',
                           'model_label',
                           'model_set_id',
                           'origin',
                           'pick',
                           'pick_probability',
                           'score_centers_note',
                           'source_asof',
                           'stake',
                           'target_T1_at',
                           'target_T2_at',
                           'total',
                           'total_error',
                           'unavailable_reason'],
 '$.week9[].providers[]': ['correct',
                           'eligible_final_hour',
                           'execution_qualified',
                           'home_margin',
                           'home_win_probability',
                           'horizon',
                           'margin_error',
                           'pick',
                           'point_unavailable_reason',
                           'probability_definition',
                           'provider',
                           'quote_at',
                           'settlement_qualified',
                           'source_asof',
                           'total',
                           'total_error',
                           'unavailable_reason'],
 '$.provider_coverage': ['week8', 'week9'],
 '$.provider_coverage.week9': ['DraftKings', 'Kalshi', 'Polymarket'],
 '$.provider_coverage.week9.DraftKings': ['games',
                                          'horizon',
                                          'margin_covered',
                                          'total_covered',
                                          'winner_covered'],
 '$.provider_coverage.week9.Kalshi': ['games',
                                      'horizon',
                                      'margin_covered',
                                      'total_covered',
                                      'winner_covered'],
 '$.provider_coverage.week9.Polymarket': ['games',
                                          'horizon',
                                          'margin_covered',
                                          'total_covered',
                                          'winner_covered'],
 '$.provider_coverage.week8': ['DraftKings', 'Kalshi', 'Polymarket'],
 '$.provider_coverage.week8.DraftKings': ['games',
                                          'horizon',
                                          'margin_covered',
                                          'total_covered',
                                          'winner_covered'],
 '$.provider_coverage.week8.Kalshi': ['games',
                                      'horizon',
                                      'margin_covered',
                                      'total_covered',
                                      'winner_covered'],
 '$.provider_coverage.week8.Polymarket': ['games',
                                          'horizon',
                                          'margin_covered',
                                          'total_covered',
                                          'winner_covered'],
 '$.week8[]': ['actual',
               'away',
               'forecasts',
               'game_id',
               'home',
               'kickoff_los_angeles',
               'kickoff_utc',
               'outcome_observed_at',
               'providers',
               'week'],
 '$.week8[].actual': ['away_score', 'home_score', 'margin', 'total', 'winner'],
 '$.week8[].forecasts[]': ['actual_issue_at',
                           'away_score_center',
                           'before_T1',
                           'before_T2',
                           'bet_decision',
                           'bet_reason',
                           'correct',
                           'eligible_final_hour',
                           'fit_completed',
                           'full_pipeline_selection_qualified',
                           'historical_publication_verified',
                           'home_margin',
                           'home_score_center',
                           'home_win_probability',
                           'horizon',
                           'issue_class',
                           'margin_direction_correct_vs_DraftKings',
                           'margin_direction_result_vs_DraftKings',
                           'margin_direction_vs_DraftKings',
                           'margin_error',
                           'model_id',
                           'model_label',
                           'model_set_id',
                           'origin',
                           'pick',
                           'pick_probability',
                           'score_centers_note',
                           'source_asof',
                           'stake',
                           'total',
                           'total_direction_correct_vs_DraftKings',
                           'total_direction_result_vs_DraftKings',
                           'total_direction_vs_DraftKings',
                           'total_error',
                           'unavailable_reason',
                           'winner_error'],
 '$.week8[].providers[]': ['acquired_at',
                           'away_score_center',
                           'correct',
                           'execution_qualified',
                           'home_margin',
                           'home_score_center',
                           'home_win_probability',
                           'horizon',
                           'issue_at',
                           'margin_error',
                           'pick',
                           'pick_probability',
                           'point_unavailable_reason',
                           'probability_definition',
                           'provider',
                           'quote_at',
                           'source_asof',
                           'total',
                           'total_error',
                           'unavailable_reason',
                           'winner_error'],
 '$.inventory[]': ['DraftKings_T2_targets',
                   'Kalshi_T1_winner',
                   'Kalshi_T2_winner',
                   'Kalshi_historical_point_forecasts_available',
                   'Polymarket_matched_historical_available',
                   'away',
                   'away_score',
                   'completed',
                   'coverage_note',
                   'current_label_observed_at',
                   'feedback_T2_targets',
                   'game_id',
                   'home',
                   'home_score',
                   'kickoff_los_angeles',
                   'kickoff_utc',
                   'label_clock_note',
                   'legacy_frozen_vector_class',
                   'legacy_frozen_winner_saved_vector_available',
                   'original_N012_saved_margin_available',
                   'original_N012_saved_total_available',
                   'original_N012_saved_win_available',
                   'original_timely_issue_available',
                   'season',
                   'selected_annual_T2_targets',
                   'selected_event_T2_targets',
                   'selected_weekly_T2_targets',
                   'separate_genuine_T1_research_issue',
                   'source_observed_at',
                   'status',
                   'upcoming_issue_join',
                   'week',
                   'winner'],
 '$.inventory[].upcoming_issue_join': ['actual_issue_at',
                                       'eligible_final_hour',
                                       'issue_class',
                                       'model_set_ids'],
 '$.week8_metrics[]': ['accuracy',
                       'auc',
                       'bias',
                       'brier',
                       'correct',
                       'ece_10',
                       'games',
                       'horizon',
                       'interval_metrics',
                       'interval_unavailable_reason',
                       'log_loss',
                       'mae',
                       'model_id',
                       'qualification',
                       'rmse',
                       'season',
                       'target',
                       'week'],
 '$.week8_disagreements[]': ['actual_winner',
                             'away',
                             'game_id',
                             'home',
                             'horizon',
                             'model_id',
                             'model_minus_provider_home_probability',
                             'model_pick',
                             'model_pick_probability',
                             'model_probability_in_50s',
                             'model_won',
                             'provider',
                             'provider_pick',
                             'provider_won',
                             'qualification',
                             'week'],
 '$.summary': ['completed_games',
               'completed_non_ties',
               'data_refreshed_in_this_derivation',
               'legacy_frozen_current_saved_winner_games',
               'models_fitted_in_this_derivation',
               'original_N012_saved_current_winner_games',
               'previous_scoring_vectors_reused',
               'schedule_games',
               'source_observation_end',
               'source_observation_start',
               'upcoming_games',
               'week8_common_T2_games',
               'week8_schedule_games',
               'weekly_counts'],
 '$.summary.weekly_counts': ['1',
                             '10',
                             '11',
                             '12',
                             '13',
                             '14',
                             '15',
                             '16',
                             '17',
                             '18',
                             '2',
                             '3',
                             '4',
                             '5',
                             '6',
                             '7',
                             '8',
                             '9']}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def clock(value):
    result = datetime.fromisoformat(value.replace('Z', '+00:00'))
    require(result.tzinfo is not None, 'Clock lacks timezone')
    return result


def disclose(value, path='$', field=''):
    if isinstance(value, dict):
        require(path in ALLOWED_FIELDS, 'Unknown disclosure object: ' + path)
        require(set(value) <= set(ALLOWED_FIELDS[path]), 'Unknown disclosure fields: ' + path)
        for key, child in value.items():
            disclose(child, path + '.' + key, key)
    elif isinstance(value, list):
        for child in value:
            disclose(child, path + '[]', field)
    elif isinstance(value, str):
        require(not FORBIDDEN.search(value), 'Private material in public weekly data')
    elif isinstance(value, (int, float)) and not isinstance(value, bool):
        require(math.isfinite(value), 'Nonfinite public number')
        if field in ('home_win_probability', 'pick_probability', 'model_pick_probability'):
            require(0 <= value <= 1 and abs(value * 10000 - round(value * 10000)) < 1e-7, 'Probability must be bounded and rounded')
    else:
        require(value is None or isinstance(value, bool), 'Unsupported public value')


def validate_weekly(data):
    require(set(data) == set(ALLOWED_FIELDS['$']), 'Incomplete weekly export')
    disclose(data)
    require(data['schema'] == 'nfl.public-weekly-inventory.v1' and data['season'] == 2026, 'Unsupported weekly schema')
    require(set(data['active_providers']) == PROVIDERS and len(data['active_providers']) == 3, 'Active provider policy differs')
    census = data['source_census']
    inventory = data['inventory']
    require(len(inventory) == census['scheduled_games'] == 272, 'Schedule inventory incomplete')
    require(sum(x['completed'] for x in inventory) == census['completed_games'] == 121, 'Final census differs')
    require(census['scheduled_games'] - census['completed_games'] == census['unstarted_games'] == 151, 'Upcoming census differs')
    require(clock(census['observed_at']) <= clock(census['source_refresh_completed_at']) <= clock(data['as_of']), 'Source clock ordering differs')
    identities = {x['game_id']: x for x in inventory}
    require(len(identities) == len(inventory), 'Duplicate schedule event')
    sets = {x['id']: x for x in data['model_sets']}
    require(len(sets) == len(data['model_sets']) and len(sets) == 12, 'Model set inventory differs')
    for row in inventory:
        require(1 <= row['week'] <= 18 and row['season'] == 2026, 'Wrong schedule phase')
        require(clock(row['kickoff_utc']) == clock(row['kickoff_los_angeles']), 'Local kickoff translation differs')
        if row['completed']:
            require(type(row['home_score']) is int and type(row['away_score']) is int, 'Final missing score')
            expected = row['home'] if row['home_score'] > row['away_score'] else row['away'] if row['away_score'] > row['home_score'] else 'TIE'
            require(row['winner'] == expected, 'Inventory winner differs from score')
        else:
            require(row['home_score'] is None and row['away_score'] is None and row['winner'] is None, 'Unplayed event has outcome')
        issue = row['upcoming_issue_join']
        if issue:
            require(not row['completed'] and clock(issue['actual_issue_at']) < clock(row['kickoff_utc']) - timedelta(hours=2), 'Early issue is not pregame')
            require(issue['eligible_final_hour'] is False, 'Early issue relabeled final hour')
    for week in range(1, 19):
        require(sum(x['week'] == week for x in inventory) == data['summary']['weekly_counts'][str(week)], 'Weekly schedule count differs')
    expected_disagreements = set()
    for period, week, count in [('week8', 8, 14), ('week9', 9, 15)]:
        games = data[period]
        require(len(games) == count and len({g['game_id'] for g in games}) == count, 'Weekly event list incomplete or duplicated')
        require({g['game_id'] for g in games} == {g['game_id'] for g in inventory if g['week'] == week}, 'Weekly games differ from complete inventory')
        for game in games:
            identity = identities[game['game_id']]
            require(all(game[k] == identity[k] for k in ('week', 'home', 'away', 'kickoff_utc')), 'Weekly join changes event identity')
            actual = game['actual']
            require(bool(actual) == identity['completed'], 'Actual outcome and census disagree')
            if actual:
                require(actual['home_score'] == identity['home_score'] and actual['away_score'] == identity['away_score'] and actual['winner'] == identity['winner'], 'Final score differs across exports')
                require(actual['margin'] == actual['home_score'] - actual['away_score'] and actual['total'] == actual['home_score'] + actual['away_score'], 'Actual margin/total differs')
            forecasts = {f['model_set_id']: f for f in game['forecasts']}
            require(set(forecasts) == set(sets) and len(forecasts) == len(game['forecasts']), 'Missing or duplicated model stream')
            providers = {p['provider']: p for p in game['providers']}
            require(set(providers) == PROVIDERS and len(game['providers']) == 3, 'Missing or duplicated provider')
            for forecast in game['forecasts']:
                definition = sets[forecast['model_set_id']]
                require(forecast['model_label'] == definition['label'] and forecast['origin'] == definition['origin'], 'Model identity switched')
                require(forecast['bet_decision'] == 'NO BET' and forecast['stake'] == 0, 'Unqualified wager advice')
                require(forecast['eligible_final_hour'] is False and forecast['full_pipeline_selection_qualified'] is False, 'Unsupported qualification')
                if forecast['issue_class'] == 'UNAVAILABLE':
                    require(bool(forecast['unavailable_reason']) and all(forecast[k] is None for k in ('home_win_probability', 'home_margin', 'total', 'actual_issue_at')), 'Missingness concealed')
                elif forecast['issue_class'] in ('EARLY_FORWARD_RESEARCH_ISSUE', 'T1_RESEARCH_ACTUAL_ISSUE'):
                    issue = clock(forecast['actual_issue_at'])
                    hours = 2 if forecast['issue_class'] == 'EARLY_FORWARD_RESEARCH_ISSUE' else 1
                    require(clock(forecast['source_asof']) <= issue <= clock(game['kickoff_utc']) - timedelta(hours=hours), 'Issue violates its cutoff')
                    require(issue <= clock(data['as_of']), 'Issue later than snapshot')
                    if forecast['fit_completed']:
                        require(clock(forecast['fit_completed']) <= issue, 'Model completed after issue')
                    if not actual:
                        require(forecast['correct'] is None and forecast['margin_error'] is None and forecast['total_error'] is None, 'Upcoming outcome invented')
                else:
                    require(forecast['issue_class'] == 'RECONSTRUCTED_NOT_ORIGINAL_ISSUED' and forecast['actual_issue_at'] is None, 'Reconstruction mislabeled as issue')
            for prediction in game['forecasts'] + game['providers']:
                probability = prediction['home_win_probability']
                if probability is not None:
                    require(prediction['pick'] == (game['home'] if probability >= .5 else game['away']), 'Winner pick differs from probability')
                    if actual:
                        require(prediction['correct'] == (prediction['pick'] == actual['winner']), 'Prediction correctness differs')
                for field, actual_field, error in [('home_margin', 'margin', 'margin_error'), ('total', 'total', 'total_error')]:
                    if prediction.get(field) is not None and actual and prediction.get(error) is not None:
                        require(abs(prediction[field] - actual[actual_field] - prediction[error]) <= .11, 'Point error differs from result')
                if all(prediction.get(k) is not None for k in ('home_score_center', 'away_score_center', 'home_margin', 'total')):
                    require(abs(prediction['home_score_center'] + prediction['away_score_center'] - prediction['total']) <= .11 and abs(prediction['home_score_center'] - prediction['away_score_center'] - prediction['home_margin']) <= .11, 'Score centers differ from margin/total')
            for f in game['forecasts']:
                for p in game['providers']:
                    if f['pick'] and p['pick'] and f['pick'] != p['pick'] and f['horizon'] == p['horizon'] == 'T2':
                        expected_disagreements.add((game['game_id'], f['model_set_id'], p['provider']))
        for provider in PROVIDERS:
            panel = data['provider_coverage'][period][provider]
            require(panel['games'] == len(games), 'Provider denominator differs')
            for target, field in [('winner', 'home_win_probability'), ('margin', 'home_margin'), ('total', 'total')]:
                covered = sum(next(p for p in g['providers'] if p['provider'] == provider)[field] is not None for g in games)
                require(panel[target + '_covered'] == covered, 'Provider coverage count differs')
    actual_disagreements = set()
    for row in data['week8_disagreements']:
        key = row['game_id'], row['model_id'], row['provider']
        require(key not in actual_disagreements, 'Duplicate disagreement')
        actual_disagreements.add(key)
        require(row['model_won'] == (row['model_pick'] == row['actual_winner']) and row['provider_won'] == (row['provider_pick'] == row['actual_winner']) and row['model_won'] != row['provider_won'], 'Disagreement outcome differs')
    require(expected_disagreements == actual_disagreements, 'Disagreements do not close: wins and losses must both remain')
    return {'weekly_status': 'PUBLIC_WEEKLY_INVENTORY_VALIDATED', 'schedule_games': len(inventory), 'week8_games': 14, 'week9_games': 15, 'public_model_streams': len(sets), 'weekly_disagreements': len(actual_disagreements), 'private_training_reproduced': False}


def load_weekly():
    raw = (HERE / 'public_weekly_inventory.json').read_bytes()
    data = json.loads(raw)
    return data, {**validate_weekly(data), 'weekly_inventory_sha256': hashlib.sha256(raw).hexdigest()}


if __name__ == '__main__':
    print(json.dumps(load_weekly()[1], sort_keys=True))
