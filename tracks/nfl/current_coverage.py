"""Validate sanitized all-game coverage without accepting private owner science."""
import hashlib
import json
import math
import re
from pathlib import Path
from market_clock import instant, reference_clock, HORIZON_LABELS
from public_snapshot import FORBIDDEN

HERE = Path(__file__).resolve().parent
PROVIDERS = {"DraftKings", "Kalshi", "Polymarket"}
ALLOWED = {'$': ['active_providers',
       'all_games',
       'as_of',
       'coverage',
       'default_timezone',
       'disagreements',
       'horizons',
       'limitations',
       'model_sets',
       'owner_run_status',
       'provenance',
       'schema',
       'season_metrics',
       'summary',
       'weekly_metrics'],
 '$.provenance': ['accepted_scientific_reentry',
                  'inventory_capsule_sha256',
                  'normalized_source_sha256',
                  'owner_return_authenticated',
                  'owner_return_bytes',
                  'owner_return_sha256',
                  'owner_status',
                  'report_derivation'],
 '$.summary': ['accepted_scientific_reentry',
               'actual_owner_issue_rows',
               'actual_owner_issued_games',
               'actual_selected_issue_games',
               'actual_selected_issue_rows',
               'completed_games',
               'completed_non_ties',
               'current_week',
               'current_week_book_games',
               'current_week_games',
               'kalshi_T1_T2_completed_games',
               'last_completed_week',
               'last_completed_week_games',
               'latest_pregame_observations',
               'new_local_fits',
               'new_local_forecasts',
               'new_owner_fits',
               'polymarket_T1_T2_completed_games',
               'schedule_games',
               'source_refreshed_in_derivation'],
 '$.summary.current_week_book_games': ['DraftKings', 'Polymarket'],
 '$.model_sets[]': ['id', 'label'],
 '$.horizons[]': ['id', 'label'],
 '$.all_games[]': ['actual',
                   'away',
                   'completed',
                   'forecasts',
                   'game_id',
                   'home',
                   'kickoff_los_angeles',
                   'kickoff_utc',
                   'providers',
                   'season',
                   'week'],
 '$.all_games[].actual': ['away_score', 'home_margin', 'home_score', 'total', 'winner'],
 '$.all_games[].forecasts[]': ['actual_issue_at',
                               'away_score_center',
                               'bet_decision',
                               'correct',
                               'fit_completed',
                               'full_pipeline_selection_qualified',
                               'home_margin',
                               'home_score_center',
                               'home_win_probability',
                               'horizon',
                               'issue_class',
                               'model_id',
                               'model_label',
                               'origin',
                               'pick',
                               'pick_probability',
                               'source_asof',
                               'stake',
                               'total',
                               'unavailable_reason'],
 '$.all_games[].providers[]': ['acquired_at',
                               'availability_status',
                               'comparison_rule',
                               'correct',
                               'derived_pick',
                               'horizon',
                               'max_age_seconds',
                               'metric_eligible',
                               'pair_clock_skew_seconds',
                               'provider',
                               'quote_age_seconds',
                               'quote_at',
                               'quote_clock_kind',
                               'unavailable_reason'],
 '$.weekly_metrics[]': ['cohort_sha256',
                        'comparison_rule',
                        'horizon',
                        'model_id',
                        'model_metrics',
                        'provider',
                        'provider_metrics',
                        'qualification',
                        'season',
                        'target',
                        'week'],
 '$.weekly_metrics[].model_metrics': ['accuracy',
                                      'bias',
                                      'brier',
                                      'correct',
                                      'crps',
                                      'distribution_reason',
                                      'ece_10',
                                      'games',
                                      'interval_coverage',
                                      'interval_width',
                                      'log_loss',
                                      'mae',
                                      'rmse',
                                      'roc_auc'],
 '$.weekly_metrics[].provider_metrics': ['accuracy',
                                         'bias',
                                         'brier',
                                         'correct',
                                         'crps',
                                         'distribution_reason',
                                         'ece_10',
                                         'games',
                                         'interval_coverage',
                                         'interval_width',
                                         'log_loss',
                                         'mae',
                                         'rmse',
                                         'roc_auc'],
 '$.season_metrics[]': ['cohort_sha256',
                        'comparison_rule',
                        'horizon',
                        'model_id',
                        'model_metrics',
                        'provider',
                        'provider_metrics',
                        'qualification',
                        'season',
                        'target',
                        'week'],
 '$.season_metrics[].model_metrics': ['accuracy',
                                      'bias',
                                      'brier',
                                      'correct',
                                      'crps',
                                      'distribution_reason',
                                      'ece_10',
                                      'games',
                                      'interval_coverage',
                                      'interval_width',
                                      'log_loss',
                                      'mae',
                                      'rmse',
                                      'roc_auc'],
 '$.season_metrics[].provider_metrics': ['accuracy',
                                         'bias',
                                         'brier',
                                         'correct',
                                         'crps',
                                         'distribution_reason',
                                         'ece_10',
                                         'games',
                                         'interval_coverage',
                                         'interval_width',
                                         'log_loss',
                                         'mae',
                                         'rmse',
                                         'roc_auc'],
 '$.disagreements[]': ['actual_winner',
                       'game_id',
                       'horizon',
                       'model_pick',
                       'model_probability_in_50s',
                       'model_right',
                       'model_set_id',
                       'provider',
                       'provider_comparison_rule',
                       'provider_pick',
                       'provider_right',
                       'season',
                       'week'],
 '$.coverage[]': ['age_le_300_seconds',
                  'age_le_3600_seconds',
                  'age_le_60_seconds',
                  'both_contract_games',
                  'exact_cutoff_games',
                  'horizon',
                  'max_age_seconds',
                  'max_clock_skew_seconds',
                  'median_age_seconds',
                  'provider',
                  'season']}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def disclose(value, path='$', key=''):
    if isinstance(value, dict):
        require(path in ALLOWED and set(value) <= set(ALLOWED[path]), 'Unknown public fields at ' + path)
        for k, v in value.items():
            disclose(v, path + '.' + k, k)
    elif isinstance(value, list):
        for v in value:
            disclose(v, path + '[]', key)
    elif isinstance(value, str):
        require(not FORBIDDEN.search(value), 'Private material in public coverage')
    elif type(value) in (int, float):
        require(math.isfinite(value), 'Nonfinite public value')
        if key in ('home_win_probability', 'pick_probability'):
            require(0 <= value <= 1 and abs(value * 1000 - round(value * 1000)) < 1e-7, 'Model display probability must be rounded')
    else:
        require(value is None or type(value) is bool, 'Unsupported public value')


def validate_coverage(data):
    require(set(data) == set(ALLOWED['$']), 'Incomplete coverage export')
    disclose(data)
    require(data['schema'] == 'sports-edge-lab.nfl.public-coverage.n035.v1', 'Unknown coverage schema')
    require(data['owner_run_status'] == 'FAILED', 'Incomplete owner run cannot become accepted')
    p = data['provenance']
    require(p['owner_return_authenticated'] is True and p['accepted_scientific_reentry'] is False, 'Authentication and science acceptance differ')
    require(p['owner_return_sha256'] == 'c437c2862be9fda797087b8a9aff44db9dba03198a5fac3083392170b5a3fdfd' and p['owner_return_bytes'] == 67_531_904, 'Owner return identity differs')
    s = data['summary']
    require(s['new_local_fits'] == s['new_local_forecasts'] == s['new_owner_fits'] == 0, 'This report does not establish new fits or local issues')
    require(s['source_refreshed_in_derivation'] is False, 'Reanalysis cannot claim source refresh')
    require(set(data['active_providers']) == PROVIDERS and len(data['active_providers']) == 3, 'Provider boundary differs')
    require({h['id'] for h in data['horizons']} == set(HORIZON_LABELS) and len(data['horizons']) == 4, 'Market reference missing')
    games = data['all_games']
    ids = {g['game_id']: g for g in games}
    require(len(games) == len(ids) == s['schedule_games'] == 272, 'Schedule coverage incomplete or duplicated')
    require(sum(g['completed'] for g in games) == s['completed_games'] == 121, 'Completed census differs')
    require(sum(g['week'] == 9 for g in games) == s['current_week_games'] == 15, 'Current week census differs')
    require(sum(g['week'] == 8 for g in games) == s['last_completed_week_games'] == 14, 'Last week census differs')
    require(sum(g['completed'] and g['actual']['winner'] != 'TIE' for g in games) == s['completed_non_ties'] == 120, 'Non-tie census differs')
    models = {m['id']: m['label'] for m in data['model_sets']}
    require(len(models) == len(data['model_sets']) == 12, 'Model streams missing or duplicated')
    expected_disagreements = set()
    latest_count = 0
    for g in games:
        require(g['season'] == 2026 and 1 <= g['week'] <= 18, 'Schedule phase differs')
        require(instant(g['kickoff_utc']) == instant(g['kickoff_los_angeles']), 'Timezone conversion changes event')
        a = g['actual']
        require(bool(a) == g['completed'], 'Outcome and completion disagree')
        if a:
            require(all(type(a[k]) in (int, float) and a[k] >= 0 and a[k] == int(a[k]) for k in ('home_score', 'away_score')), 'Invalid actual score')
            winner = g['home'] if a['home_score'] > a['away_score'] else g['away'] if a['away_score'] > a['home_score'] else 'TIE'
            require(a['winner'] == winner and a['home_margin'] == a['home_score'] - a['away_score'] and a['total'] == a['home_score'] + a['away_score'], 'Outcome arithmetic differs')
        fs = {f['model_id']: f for f in g['forecasts']}
        require(len(fs) == len(g['forecasts']) and set(fs) <= set(models), 'Duplicate or unknown model stream')
        require('original_frozen' in fs, 'Missing original stream must stay explicit')
        for f in fs.values():
            require(f['model_label'] == models[f['model_id']], 'Model identity switched')
            require(f['stake'] == 0 and f['bet_decision'] == 'NO BET' and f['full_pipeline_selection_qualified'] is False, 'Unsupported execution qualification')
            kind = f['issue_class']
            if kind == 'UNAVAILABLE':
                require(f['unavailable_reason'] and all(f[k] is None for k in ('pick', 'home_win_probability', 'home_margin', 'total', 'actual_issue_at')), 'Missing forecast manufactured')
            elif kind in ('RECONSTRUCTED_NOT_ORIGINAL_ISSUED', 'SAVED_OR_RECONSTRUCTED_NOT_ORIGINAL_ISSUED'):
                require(f['actual_issue_at'] is None, 'Reconstruction backdated as issue')
            else:
                require(kind in ('EARLY_FORWARD_RESEARCH_ISSUE', 'T1_RESEARCH_ACTUAL_ISSUE'), 'Unknown issue class')
                issued = instant(f['actual_issue_at'])
                require(instant(f['source_asof']) <= issued < instant(g['kickoff_utc']), 'Actual issue violates source or kickoff clock')
                require(issued <= instant(data['as_of']), 'Issue after public snapshot')
                if f['fit_completed']:
                    require(instant(f['fit_completed']) <= issued, 'Model completed after its issue')
            if f['pick']:
                require(f['pick'] in (g['home'], g['away']) and f['home_win_probability'] is not None, 'Invalid model direction')
                expected = f['home_win_probability'] if f['pick'] == g['home'] else 1 - f['home_win_probability']
                require(abs(expected - f['pick_probability']) < .00101 and f['pick_probability'] >= .4995, 'Pick probability differs')
                require(f['correct'] == (f['pick'] == a['winner']) if a and a['winner'] != 'TIE' else f['correct'] is None, 'Model result differs')
            if all(f[k] is not None for k in ('home_score_center', 'away_score_center', 'home_margin', 'total')):
                require(abs(f['home_score_center'] + f['away_score_center'] - f['total']) <= .11 and abs(f['home_score_center'] - f['away_score_center'] - f['home_margin']) <= .11, 'Rounded score centers differ')
        ps = {(r['provider'], r['horizon']): r for r in g['providers']}
        require(len(ps) == len(g['providers']) == 12 and set(ps) == {(p, h) for p in PROVIDERS for h in HORIZON_LABELS}, 'Every provider/horizon state must remain visible')
        for r in ps.values():
            if r['derived_pick']:
                require(r['derived_pick'] in (g['home'], g['away']), 'Invalid provider direction')
                require(r['correct'] == (r['derived_pick'] == a['winner']) if a and a['winner'] != 'TIE' else r['correct'] is None, 'Provider result differs')
                if r['quote_at']:
                    reference_clock(kickoff=g['kickoff_utc'], quote_at=r['quote_at'], acquired_at=r['acquired_at'], horizon=r['horizon'])
                else:
                    require(r['provider'] == 'DraftKings' and r['comparison_rule'] == 'SAVED_HISTORICAL_REFERENCE' and r['quote_clock_kind'] == 'ABSENT_FROM_COMPACT_REFERENCE', 'Unrecorded quote clock invented')
                latest_count += r['horizon'] == 'LATEST_PREGAME'
            else:
                require(r['unavailable_reason'] and r['correct'] is None and r['metric_eligible'] is False, 'Provider missingness concealed')
            if a and a['winner'] != 'TIE' and r['derived_pick'] and r['metric_eligible']:
                for f in fs.values():
                    if f['pick'] and f['pick'] != r['derived_pick'] and f['horizon'] == r['horizon']:
                        expected_disagreements.add((g['game_id'], f['model_id'], r['provider'], r['horizon']))
    require(latest_count == s['latest_pregame_observations'] == 0, 'Unacquired latest pregame reference invented')
    actual_disagreements = set()
    for r in data['disagreements']:
        key = r['game_id'], r['model_set_id'], r['provider'], r['horizon']
        require(key not in actual_disagreements, 'Duplicate disagreement')
        actual_disagreements.add(key)
        g = ids[r['game_id']]
        f = next(f for f in g['forecasts'] if f['model_id'] == r['model_set_id'])
        pr = next(p for p in g['providers'] if (p['provider'], p['horizon']) == (r['provider'], r['horizon']))
        require(r['model_pick'] == f['pick'] and r['provider_pick'] == pr['derived_pick'] and r['actual_winner'] == g['actual']['winner'], 'Disagreement join differs')
        require(r['model_right'] == f['correct'] and r['provider_right'] == pr['correct'] and r['model_right'] != r['provider_right'], 'Disagreement outcome differs')
    require(actual_disagreements == expected_disagreements, 'Disagreement wins or losses omitted')
    for r in data['season_metrics'] + data['weekly_metrics']:
        require(r['provider'] in PROVIDERS and r['model_id'] in models and r['season'] in (2024, 2025, 2026), 'Unknown comparison cell')
        require(re.fullmatch('[0-9a-f]{64}', r['cohort_sha256']), 'Missing exact comparison cohort')
        a, b = r['model_metrics'], r['provider_metrics']
        require(a['games'] == b['games'] > 0, 'Unequal provider/model cohorts')
        for m in (a, b):
            if r['target'] == 'win':
                require(abs(m['accuracy'] - m['correct'] / m['games']) < 1e-7, 'Accuracy differs from correct count')
                require(m['log_loss'] >= 0 and 0 <= m['brier'] <= 1, 'Invalid probability loss')
            else:
                require(r['target'] in ('margin', 'total') and m['mae'] >= 0 and m['rmse'] + 1e-7 >= m['mae'], 'Invalid point-target metric')
    return {'current_coverage_status': 'PUBLIC_DERIVED_COVERAGE_VALIDATED', 'current_schedule_games': len(games), 'current_completed_games': 121, 'current_disagreement_pairs': len(actual_disagreements), 'private_training_reproduced': False, 'owner_pipeline_accepted': False}


def load_coverage():
    raw = (HERE / 'current_coverage.json').read_bytes()
    data = json.loads(raw)
    return data, {**validate_coverage(data), 'current_coverage_sha256': hashlib.sha256(raw).hexdigest()}


if __name__ == '__main__':
    print(json.dumps(load_coverage()[1], sort_keys=True))
