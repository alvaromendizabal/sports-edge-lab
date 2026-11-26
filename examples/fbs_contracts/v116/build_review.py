"""Render the bounded FBS selected-output report; no research or publication."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
DATA = ROOT / 'docs/fbs/v116/data/review.json'
OUTPUT = ROOT / 'docs/fbs/v116/index.html'
ROOT_KEYS = {'schema', 'owner', 'prepared_at_utc', 'week', 'snapshot', 'execution', 'selection',
             'publication', 'policies', 'metrics', 'sensitivity', 'providers', 'games', 'provenance'}
GAME_KEYS = {'game_id', 'season', 'home', 'away', 'kickoff_utc', 'date_pacific',
             'nominal_cutoff_utc', 'completed_at_snapshot', 'actual_margin', 'actual_total',
             'selected', 'covered_policies', 'home_score', 'away_score'}
CELL_KEYS = {'value', 'coverage', 'gap', 'all_market_sources_absent', 'prior_fallback',
             'fit_completed_at', 'original_issued', 'forecast_issued', 'evidence_class',
             'interval80', 'interval95'}
FRESH_CELL_KEYS = CELL_KEYS | {'snapshot_as_of', 'source_observed_at',
    'inference_generated_at', 'snapshot_kind', 'available_information_through',
    'actual_preview_information_cutoff','feature_matrix_as_of','feature_source_observed_at',
    'market_source_observed_at','market_input_mode','market_source_book_count',
    'early_horizon_has_validation_evaluation','canonical_t60_feature_qualified',
    'original_t60_scorecard_not_validation_of_this_preview'}
PROFILES = ['50/50', '40/60', '30/70', '20/80', '10/90']
SHAPES = json.loads((HERE / 'public_shapes.json').read_text())


def require(condition, message):
    if not condition:
        raise ValueError(message)


def validate(data):
    def boundary(value, location='$'):
        if isinstance(value, dict):
            require(sorted(value) in SHAPES.get(location, []), 'Unexpected public fields: ' + location)
            for key, item in value.items():
                boundary(item, location + '.' + key)
        elif isinstance(value, list):
            for item in value:
                boundary(item, location + '[]')
    boundary(data)
    require(ROOT_KEYS <= set(data) and set(data) - ROOT_KEYS <= {'current_diagnostic','current_test_diagnostic'}, 'Unexpected public root fields')
    require(data['owner'] == 'FBS' and data['schema'] == 'fbs.v116.public-selected-review.v1', 'FBS owner schema')
    text = json.dumps(data, ensure_ascii=False)
    require(not re.search(r's3://|/home/|/workspace/|sagemaker|arn:aws|api[_-]?key|secret[_-]?key|circa|feature_names|raw_quotes|model_id|source_parquet|\.pyz', text, re.I), 'Private or out-of-scope field')
    execution = data['execution']
    require(execution['version'] == 'V115' and execution['status'] == 'FAILED_BEFORE_CURRENT_CENSUS_AND_FITTING', 'V115 failure preserved')
    require(execution['failure_reason'] == 'another_current_collector_has_active_lease', 'Observed lease failure preserved')
    require(execution['child_exit_code'] == 2 and execution['owner_executions_failed'] == 1 and execution['owner_executions_successful'] == 0, 'Failed owner execution cannot become success')
    require(all(execution[key] == 0 for key in ('new_model_fits', 'new_calibrator_fits', 'new_scoring_tasks', 'new_current_census_calls')), 'No unearned new science')
    require(execution['return_status'] == 'VERIFIED_PARTIAL_RESUMABLE' and execution['return_bytes'] == 157555474 and execution['return_sha256'] == 'e1db587858f222425c76978b5fb2a9224589a9d53eb468d68b658c849378226e', 'Verified return identity')
    require(not execution['scientific_occupancy_measured'] and not execution['estimate_is_invoice'], 'CPU and cost qualifications')
    selection = data['selection']
    require(selection['validation_seasons'] == [2024, 2025] and selection['test_season'] == 2026, 'Fixed season roles')
    require(selection['primary_profile'] == '50/50' and selection['test_previously_exposed'], 'Primary profile and prior exposure')
    require(not any(selection[key] for key in ('test_used_for_selection', 'training_season_reweighting', 'ratio_changes_refit_estimators', 'historical_original_issue_certified', 'full_v13_program_complete')), 'Scientific boundaries')
    require(data['publication']['owner_run_started_by_page'] is False and data['publication']['production_model_promoted'] is False and data['publication']['new_model_fits_by_page'] == 0, 'Report cannot execute or promote')
    require(data['snapshot']['new_inference'] is False and data['snapshot']['forecast_refresh_performed'] is False and data['snapshot']['market_snapshot_refreshed'] is False, 'Dated source cannot become refresh')
    require(set(data['policies']) == {f'P{i:02d}' for i in range(1, 9)}, 'Eight selected policies')
    ids = set()
    for game in data['games']:
        require(set(game) == GAME_KEYS and game['season'] == 2026, 'Closed public game fields')
        require(game['game_id'] not in ids, 'Duplicate season game')
        ids.add(game['game_id'])
        require(set(game['selected']) == set(data['policies']), 'Keep missing selected policy cells')
        count = 0
        for alias, cell in game['selected'].items():
            require(set(cell) == CELL_KEYS, 'Closed selected output fields')
            value = cell['value']
            require((value is None) == (cell['coverage'] == 'missing'), 'Missing values stay null')
            require(cell['original_issued'] in (False, None) and cell['forecast_issued'] in (False, None), 'Saved reconstruction earns no issue credit')
            if value is not None:
                require(cell['original_issued'] is False and cell['forecast_issued'] is False, 'Stored values retain explicit unissued state')
            require(cell['evidence_class'] == 'V13_FROZEN_RECONSTRUCTION', 'Retained evidence class')
            if value is not None:
                count += 1
                require(isinstance(value, (int, float)), 'Numeric selected output')
                if data['policies'][alias]['target'] == 'winner':
                    require(0 <= value <= 1 and round(value, 4) == value, 'Rounded probability')
                else:
                    require(round(value, 1) == value, 'Rounded point output')
            if cell['prior_fallback']:
                require(cell['all_market_sources_absent'] is True, 'Prior fallback source absence')
        require(game['covered_policies'] == count, 'Correct policy coverage')
        if game['home_score'] is not None:
            require(game['home_score'] - game['away_score'] == game['actual_margin'] and game['home_score'] + game['away_score'] == game['actual_total'], 'Observed score arithmetic')
    week = [g for g in data['games'] if data['week']['start_pacific'] <= g['date_pacific'] <= data['week']['end_pacific']]
    snapshot = data['snapshot']
    require(len(ids) == snapshot['game_count'] and len(week) == snapshot['weekly_games'], 'Unshrunk game populations')
    require(sum(g['completed_at_snapshot'] for g in data['games']) == snapshot['completed_games'], 'Completed denominator')
    require(sum(g['covered_policies'] == 8 for g in week) == snapshot['weekly_complete_policy_games'], 'Weekly complete coverage')
    require(sum(g['covered_policies'] < 8 for g in week) == snapshot['weekly_missing_policy_games'], 'Weekly gaps retained')
    require(len(data['metrics']) == len(data['sensitivity']) == 9, 'Nine objective roles')
    for metric in data['metrics']:
        require([v['season'] for v in metric['annual']] == [2024, 2025, 2026], 'All three annual scores')
        require([v['scored_n'] for v in metric['annual']] == [919, 934, 822], 'Dated metric populations remain unchanged')
        require(all(v['expected_n'] == v['scored_n'] and v['missing_n'] == 0 for v in metric['annual']), 'Selected metrics use full observed populations')
        require(abs((metric['annual'][0]['value'] + metric['annual'][1]['value']) / 2 - metric['selection_score']) < 1e-10, 'Evaluation-only primary mean')
    for row in data['sensitivity']:
        require(set(row['profiles']) == set(PROFILES), 'All sensitivity profiles')
        require(row['profiles']['50/50']['winner'] == row['primary_policy'] and row['profiles']['50/50']['primary_rank'] == 1, 'Primary winner identity')
    require(data['providers']['current_week_qualified_quotes'] is None, 'No fabricated current quotes')
    require(data['providers']['status'] == 'DATED_RETAINED_EVIDENCE_NO_CURRENT_REFRESH', 'Retained market evidence remains dated')
    for row in data['providers']['rows']:
        require(row['paired_n'] + row['missing_n'] == row['expected_n'], 'Provider denominator and gaps')
        if row['provider'] != 'draftkings':
            require(row['paired_n'] == 0 and row['metrics'] == {}, 'Retained exchange qualification gaps')
    require(all(re.fullmatch('[a-f0-9]{64}', x['sha256']) for x in data['provenance']), 'Source evidence fingerprints')
    if 'current_diagnostic' in data:
        current = data['current_diagnostic']
        require(current['status'] in ('FRESH_SOURCE_AND_SELECTED_INFERENCE', 'FRESH_SOURCE_ONLY'), 'Known current diagnostic status')
        require(current['status'] != 'FRESH_SOURCE_AND_SELECTED_INFERENCE' or current['native_exact_component_parity_passed'] is True, 'Native original-state parity required before new inference display')
        require(current['new_model_fits'] == current['new_calibrator_fits'] == 0, 'Frozen inference cannot claim new fits')
        require(current['current_census_calls'] == current['current_game_refresh_calls'] + current['full_census_additional_calls'], 'Distinct source acquisitions counted once')
        require(not any(current[key] for key in ('owner_campaign_launched','nominal_t60_original_issue','forecast_issued','historical_metrics_recomputed')), 'Diagnostic boundaries')
        require(current['all_bookmaker_observed_rows'] >= current['all_bookmaker_qualified_rows'] >= len(current['market_rows']), 'Qualified market counts')
        require(current['bookmaker_inventory_labels'] == len({r['bookmaker'] for r in current['market_coverage']})
                and current['all_bookmaker_labels'] + current['zero_qualified_bookmaker_labels'] == current['bookmaker_inventory_labels'], 'Bookmaker inventory gaps retained')
        require(sum(current['source_quarantine_reasons'].values()) == current['source_quarantined_rows'], 'Quarantine reason counts retained')
        current_ids = set()
        available = 0
        for game in current['games']:
            require(set(game) == GAME_KEYS and game['season'] == 2026 and game['game_id'] not in current_ids, 'Fresh full game population')
            current_ids.add(game['game_id'])
            require(set(game['selected']) == set(data['policies']), 'Every fresh selected cell remains visible')
            count = 0
            for alias, cell in game['selected'].items():
                require(set(cell) == FRESH_CELL_KEYS, 'Closed fresh selected output fields')
                value = cell['value']
                require((value is None) == (cell['coverage'] == 'missing'), 'Fresh missing cells stay null')
                require(cell['original_issued'] is False and cell['forecast_issued'] is False, 'Early snapshots earn no issue credit')
                require(cell['evidence_class'] == 'FROZEN_MODEL_DIAGNOSTIC_SNAPSHOT', 'Fresh inference separated from old metrics')
                if value is not None:
                    count += 1
                    require(isinstance(value, (int, float)), 'Fresh numeric selected output')
                    if data['policies'][alias]['target'] == 'winner':
                        require(0 <= value <= 1 and round(value,4) == value, 'Fresh rounded probability')
                    else:
                        require(round(value,1) == value, 'Fresh rounded point output')
                    require(cell['inference_generated_at'] is not None and cell['snapshot_as_of'] is not None, 'Fresh inference clocks required')
                if cell['prior_fallback']:
                    require(cell['all_market_sources_absent'] is True, 'Fresh fallback absence retained')
                if cell['market_input_mode'] == 'CURRENT_PREGAME_QUOTES_AT_ACTUAL_PREVIEW_CLOCK':
                    require(cell['early_horizon_has_validation_evaluation'] is False and cell['canonical_t60_feature_qualified'] is False
                            and cell['original_t60_scorecard_not_validation_of_this_preview'] is True, 'Early market horizon must remain unvalidated')
            require(game['covered_policies'] == count, 'Fresh per-game policy coverage')
            available += count
            if game['home_score'] is not None:
                require(game['home_score'] - game['away_score'] == game['actual_margin'] and game['home_score'] + game['away_score'] == game['actual_total'], 'Fresh observed score arithmetic')
        week = [g for g in current['games'] if data['week']['start_pacific'] <= g['date_pacific'] <= data['week']['end_pacific']]
        require(current['game_count'] == len(current_ids) and current['expected_cells'] == len(current_ids)*8 and current['available_cells'] == available, 'Fresh full policy population')
        require(current['completed_games'] == sum(g['completed_at_snapshot'] for g in current['games']), 'Fresh census completed count')
        require(current['weekly_games'] == len(week) and current['weekly_complete_policy_games'] == sum(g['covered_policies'] == 8 for g in week) and current['weekly_missing_policy_games'] == sum(g['covered_policies'] < 8 for g in week), 'Fresh weekly denominators')
        early = current['early_market_preview']
        if early:
            require(early['early_horizon_has_validation_evaluation'] is False and early['nominal_t60_qualification_changed'] is False
                    and early['selection_or_historical_scores_updated'] is False, 'Separate early preview cannot inherit historical validation')
        for row in current['market_rows']:
            require(row['bookmaker'] in ('draftkings','kalshi','polymarket','polymarket_us','polymarket_global'), 'Requested public reference providers')
            require(row['strict_t60_model_input_qualified'] is False and row['horizon'] == 'CURRENT_OBSERVATION_NOT_CANONICAL_T60', 'Current references never become T60 modeling evidence')
            require(row['qualified'] is True or row['value'] is None, 'Unqualified benchmark value stays blank')
            require(row['observed_at'] is not None and row['quote_at'] is not None, 'Distinct benchmark clocks')
        require(sum(r['received_rows'] for r in current['market_coverage']) == current['all_bookmaker_observed_rows'] and sum(r['qualified_rows'] for r in current['market_coverage']) == current['all_bookmaker_qualified_rows'], 'All-source coverage totals')
        for row in current['market_coverage']:
            if row['bookmaker'] in ('draftkings','kalshi','polymarket','polymarket_us','polymarket_global'):
                qualified = [r for r in current['market_rows'] if r['bookmaker'] == row['bookmaker'] and r['target'] == row['target'] and r['qualified']]
                require(len(qualified) == row['qualified_rows'] and len({r['game_id'] for r in qualified}) == row['qualified_games'], 'Measured requested-provider distinct games')
                require(len({r['game_id'] for r in qualified} & {g['game_id'] for g in week}) == row['qualified_week_games'], 'Measured current-week provider games')
    if 'current_test_diagnostic' in data:
        scores=data['current_test_diagnostic']
        require('current_diagnostic' in data and scores['completed_games']==data['current_diagnostic']['completed_games'], 'New test diagnostic census binding')
        require(not any(scores[k] for k in ('retained_original_cards_changed','test_used_for_selection','new_selection','original_issued'))
                and scores['prior_test_exposure_disclosed'] is True, 'New test diagnostic cannot select or overwrite')
        require(all(scores[k]==0 for k in ('new_model_fits','new_calibrator_fits','new_residual_distribution_fits','new_forecasts','source_provider_calls')), 'Report-only diagnostic work')
        require(len(scores['objectives'])==scores['selected_objectives']==len(data['metrics']) and scores['selected_policies']==len(data['policies']), 'All already selected diagnostic objectives')
        require({(r['policy'],r['target'],r['metric']) for r in scores['objectives']}=={(r['policy'],r['target'],r['metric']) for r in data['metrics']}, 'Diagnostic selection identities unchanged')
        for row in scores['objectives']:
            require(row['selected_using_2026'] is False and row['expected_n']==scores['completed_games']
                    and row['scored_n']+row['missing_n']==row['expected_n'], 'Complete new test denominators')
        require(scores['scored_policy_game_rows']==scores['completed_games']*scores['selected_policies'], 'Completed policy-game score accounting')
        require(scores['upcoming_preview_rows_excluded']==(data['current_diagnostic']['game_count']-scores['completed_games'])*scores['selected_policies'], 'Upcoming previews excluded from grading')


def render(data):
    validate(data)
    payload = json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(',', ':')).replace('<', '\\u003c')
    digest = hashlib.sha256(payload.encode()).hexdigest()
    return (HERE / 'template.html.in').read_text().replace('@@PAYLOAD@@', payload).replace('@@SHA256@@', digest).encode()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--data', type=Path, default=DATA)
    parser.add_argument('--output', type=Path, default=OUTPUT)
    args = parser.parse_args()
    body = render(json.loads(args.data.read_text()))
    if args.check:
        require(args.output.read_bytes() == body, 'Generated report differs from verified source')
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_bytes(body)
    print(json.dumps({'status': 'PASS', 'bytes': len(body), 'sha256': hashlib.sha256(body).hexdigest(), 'new_fits': 0, 'published': False}))


if __name__ == '__main__':
    main()
