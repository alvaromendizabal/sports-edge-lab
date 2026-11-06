"""Check the actual sanitized export and its rendered review contract."""
import copy
import hashlib
import json
import math
from html.parser import HTMLParser
from pathlib import Path
import re
import unittest
from unittest.mock import patch

import build_dashboard
from progress import demo_scenarios
from preflight import demo_scenarios as preflight_scenarios


class EvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.exports = {league: build_dashboard.evidence(league)
                       for league in ('ncaam', 'ncaaw')}

    def test_exact_separate_population_counts(self):
        expected = {'ncaam': (5758, 5749), 'ncaaw': (5280, 5621)}
        for league, data in self.exports.items():
            self.assertEqual(data['league'], league)
            for model in data['models']:
                a, b = expected[league]
                self.assertEqual(model['panels']['2025']['N'], a)
                self.assertEqual(model['panels']['2026']['N'], b)
                self.assertEqual(model['panels']['pooled']['N'], a + b)

    def test_pooled_losses_are_game_weighted(self):
        for data in self.exports.values():
            for model in data['models']:
                pooled, a, b = (model['panels'][k] for k in ('pooled', '2025', '2026'))
                columns = ('LogLoss', 'Brier', 'Accuracy', 'CalibrationBias') if model['target'] == 'win' else ('MAE', 'Bias')
                for column in columns:
                    expected = (a[column] * a['N'] + b[column] * b['N']) / pooled['N']
                    self.assertAlmostEqual(pooled[column], expected, places=12)
                if model['target'] != 'win':
                    expected = math.sqrt((a['RMSE'] ** 2 * a['N'] + b['RMSE'] ** 2 * b['N']) / pooled['N'])
                    self.assertAlmostEqual(pooled['RMSE'], expected, places=12)

    def test_calibration_support_and_weighted_bias(self):
        for data in self.exports.values():
            for model in data['models']:
                if model['target'] != 'win':
                    continue
                for panel in model['panels'].values():
                    bins = panel['calibration_bins']
                    self.assertEqual(sum(b['N'] for b in bins), panel['N'])
                    self.assertEqual(len({b['bin'] for b in bins}), len(bins))
                    self.assertTrue(all(0 <= b['mean_probability'] <= 1 and 0 <= b['observed_rate'] <= 1 for b in bins))
                    bias = sum(b['N'] * (b['mean_probability'] - b['observed_rate']) for b in bins) / panel['N']
                    ece = sum(b['N'] * abs(b['mean_probability'] - b['observed_rate']) for b in bins) / panel['N']
                    self.assertAlmostEqual(panel['CalibrationBias'], bias, places=12)
                    self.assertAlmostEqual(panel['ECE10'], ece, places=12)

    def test_one_fixed_selection_per_objective(self):
        for data in self.exports.values():
            ids = [m['id'] for m in data['models']]
            self.assertEqual(len(ids), len(set(ids)))
            for target, metrics in {'win': ('LogLoss', 'Brier', 'Accuracy'), 'margin': ('MAE', 'RMSE'), 'total': ('MAE', 'RMSE')}.items():
                for metric in metrics:
                    selected = [m for m in data['models'] if m['target'] == target and metric in m['selected_for']]
                    self.assertEqual(len(selected), 1)
                    self.assertEqual(set(selected[0]['panels']), {'pooled', '2025', '2026'})
                    self.assertNotIn('2027', selected[0]['panels'])

    def test_uncertainty_matches_fixed_pair_and_is_qualified(self):
        for data in self.exports.values():
            t = data['objective_tradeoff']
            models = {m['id']: m for m in data['models']}
            a, b = models[t['left']]['panels']['pooled'], models[t['right']]['panels']['pooled']
            self.assertEqual(t['paired_games'], a['N'])
            self.assertEqual(a['N'], b['N'])
            for key, value in t['metrics'].items():
                self.assertAlmostEqual(value['difference'], a[key] - b[key], places=12)
                self.assertLessEqual(value['lower'], value['upper'])
            self.assertLess(t['metrics']['Accuracy']['lower'], 0)
            self.assertGreater(t['metrics']['Accuracy']['upper'], 0)
            self.assertTrue(t['selection_exposed'])
            self.assertFalse(t['multiple_comparison_adjustment'])
            self.assertFalse(t['causal_or_prospective_edge_claimed'])

    def test_partial_attempt_preserves_completed_science_and_missing_current_scores(self):
        for data in self.exports.values():
            attempt = next(a for a in data['owner_attempt_history'] if a['release'] == 'B033')
            self.assertEqual(attempt['release'], 'B033')
            self.assertEqual(attempt['status'], 'FAILED_PARTIAL_WORK_PRESERVED')
            self.assertEqual(attempt['run_scope'], 'NCAA_MEN_AND_WOMEN_COMBINED')
            self.assertEqual(attempt['new_real_target_fits'], 108)
            self.assertEqual(attempt['league_new_real_target_fits'], 54)
            self.assertEqual(attempt['reused_target_fits'], 0)
            self.assertEqual(attempt['completed_scientific_stages'], 3)
            self.assertEqual(attempt['attempted_scientific_stages'], 4)
            self.assertEqual([s['status'] for s in attempt['stages']], ['COMPLETED'] * 3 + ['FAILED'])
            self.assertEqual(attempt['study_target_fits_completed'], attempt['study_target_fits_registered'])
            for key in ('new_calibration_fits', 'new_source_refreshes', 'new_prediction_rows', 'new_prospective_issues', 'new_orders', 'scientific_credit_from_subsequent_readback'):
                self.assertEqual(attempt[key], 0)
            self.assertTrue(attempt['original_monitoring_unchanged'])
            self.assertEqual([p['name'] for p in data['providers']], ['Kalshi', 'Polymarket', 'DraftKings'])
            for provider in data['providers']:
                for key in ('current_log_loss', 'current_matched_games', 'hypothetical_ROI'):
                    self.assertIsNone(provider[key])
            self.assertFalse(data['market_advantage']['demonstrated'])
            self.assertIsNone(data['market_advantage']['realized_betting_profit'])

    def test_prior_failed_attempt_stays_in_history(self):
        for data in self.exports.values():
            old = data['owner_attempt_history'][0]
            self.assertEqual(old['release'], 'B032')
            self.assertEqual(old['new_real_target_fits'], 0)
            self.assertEqual(old['synthetic_tests_passed'], 250)
            self.assertEqual(data['provenance']['prior_failed_owner_return_sha256'], 'ae14d708cf85615c1c9c57a7891db85261a5b1632ecd70349730bf2dde51d9b0')

    def test_resource_clocks_are_separate_and_not_claimed_as_tree_peak(self):
        for data in self.exports.values():
            a = next(a for a in data['owner_attempt_history'] if a['release'] == 'B033')
            self.assertAlmostEqual(a['phase_seconds']['admission'], 4146.091564976001)
            self.assertAlmostEqual(a['phase_seconds']['science'], 1294.1799582330004)
            self.assertGreater(a['total_wall_seconds'], sum(a['phase_seconds'].values()))
            self.assertLess(a['total_wall_seconds'] - sum(a['phase_seconds'].values()), 2)
            self.assertFalse(a['simultaneous_process_tree_peak_measured'])

    def test_latest_preflight_outcomes_cannot_be_relabelled_as_science(self):
        for data in self.exports.values():
            a = next(x for x in data['owner_attempt_history'] if x['release'] == 'B035')
            self.assertEqual(a['release'], 'B035')
            self.assertEqual(a['status'], 'FAILED_PARTIAL_WORK_PRESERVED')
            self.assertEqual(a['failure_phase'], 'PREFLIGHT_BEFORE_SCIENCE')
            self.assertEqual((a['synthetic_tests_total'], a['synthetic_tests_passed'],
                a['synthetic_test_errors'], a['synthetic_tests_skipped']), (514, 510, 3, 1))
            self.assertEqual(a['synthetic_tests_total'], sum(a[k] for k in (
                'synthetic_tests_passed', 'synthetic_tests_failed', 'synthetic_test_errors', 'synthetic_tests_skipped')))
            for key in ('new_real_target_fits', 'reused_target_fits', 'new_source_refreshes',
                'new_provider_requests', 'new_prospective_issues', 'completed_scientific_stages', 'attempted_scientific_stages'):
                self.assertEqual(a[key], 0)
            self.assertIsNone(a['phase_seconds']['science'])
            self.assertEqual(a['planned_scientific_stages'], 12)
            self.assertEqual(a['admission']['workers_planned'], 7)
            self.assertEqual(a['admission']['foreign_processes_signaled'], 0)
            self.assertEqual(a['owner_post_close_verification'], 'not_persisted_by_owner')
            self.assertAlmostEqual(a['phase_seconds']['admission'], 1.0053939780009387)

    def test_inherited_inventory_is_dated_and_unreconciled(self):
        expected = {'ncaam': (437, 13, 2, 435), 'ncaaw': (419, 51, 1, 418)}
        for league, data in self.exports.items():
            d = next(x for x in data['inventory_history'] if x['snapshot_at'] == '2026-11-03T00:48:42+00:00')
            self.assertEqual((d['candidate_games'], d['observed_finals'], d['last_week']['candidate_games'], d['this_week']['candidate_games']), expected[league])
            self.assertEqual(d['candidate_games'], d['last_week']['candidate_games'] + d['this_week']['candidate_games'])
            self.assertEqual(d['snapshot_at'], '2026-11-03T00:48:42+00:00')
            self.assertFalse(d['official_inventory_reconciled'])
            self.assertFalse(d['all_official_games_covered'])
            self.assertEqual(d['authenticated_current_issues'], 0)

    def test_b036_workflow_completed_without_upgrading_reconstructions(self):
        for league, data in self.exports.items():
            a = next(x for x in data['owner_attempt_history'] if x['release'] == 'B036')
            self.assertEqual(a['release'], 'B036')
            self.assertEqual(a['completed_scientific_stages'], 12)
            self.assertEqual((a['synthetic_tests_passed'], a['synthetic_test_errors'], a['synthetic_tests_skipped']), (536, 0, 1))
            self.assertEqual((a['new_real_target_fits'], a['new_calibration_fits'], a['new_empirical_residual_fits'], a['reused_target_fits']), (65, 35, 0, 108))
            self.assertEqual(a['league_new_real_target_fits'], 50 if league == 'ncaam' else 15)
            self.assertEqual(a['new_prediction_rows'], 8100)
            self.assertEqual(a['new_prospective_issues'], 0)
            self.assertFalse(a['scientific_goal_complete'])
            self.assertEqual(a['owner_post_close_verification'], 'full_return_bytes_verified')
            self.assertEqual(a['admission']['workers_planned'], 7)
            self.assertEqual(a['admission']['foreign_processes_signaled'], 0)
            self.assertTrue(a['admission']['descendant_usage_measured'])
            self.assertTrue(a['admission']['raw_samples_preserved_in_private_evidence'])
            old_inventory = next(x for x in data['inventory_history'] if x['snapshot_at'] == '2026-11-04T18:32:51.950861+00:00')
            self.assertEqual(old_inventory['candidate_games'], 1103 if league == 'ncaam' else 1072)
            self.assertEqual(old_inventory['observed_finals'], 327 if league == 'ncaam' else 311)
            self.assertFalse(data['observed_inventory']['all_official_games_covered'])
            preserved = next(x for x in data['coverage_history'] if x['release'] == 'B040')
            self.assertEqual(preserved['current_coverage_gaps']['market_identity_unresolved'], 226042)
            self.assertIsNone(data['current_coverage_gaps']['official_denominator'])

    def test_private_viewer_has_no_upload_or_persistence_path(self):
        viewer = (build_dashboard.HERE / 'private_report.html.tmpl').read_text()
        self.assertIn("connect-src 'none'", viewer)
        self.assertIn('new FileReader()', viewer)
        self.assertIn('window_event_keys', viewer)
        self.assertIn('Unresolved identity', viewer)
        self.assertIn('No record for this game', viewer)
        for forbidden in ('fetch(', 'XMLHttpRequest', 'WebSocket(', 'sendBeacon(', 'localStorage', 'sessionStorage', 'indexedDB', '.innerHTML', 'eval('):
            self.assertNotIn(forbidden, viewer)
        self.assertIn('n.textContent=value', viewer)

    def test_b039_partial_run_keeps_real_fits_and_all_missing_coverage_explicit(self):
        for league, data in self.exports.items():
            attempt = next(x for x in data['owner_attempt_history'] if x['release']=='B039')
            self.assertEqual(attempt['release'], 'B039')
            self.assertEqual(attempt['status'], 'FAILED_PARTIAL_WORK_PRESERVED')
            self.assertEqual((attempt['completed_scientific_stages'], attempt['planned_scientific_stages']), (10, 13))
            self.assertEqual([x['status'] for x in attempt['stages']], ['COMPLETED']*10+['FAILED','NOT_STARTED','NOT_STARTED'])
            self.assertEqual((attempt['new_real_target_fits'], attempt['new_calibration_fits'], attempt['new_empirical_residual_fits']), (156,48,60))
            self.assertEqual(attempt['league_new_real_target_fits'], 96 if league=='ncaam' else 60)
            self.assertEqual(attempt['reused_target_fits'],108)
            self.assertEqual(attempt['new_prospective_issues'],0)
            inventory = next(x for x in data['inventory_history'] if x['snapshot_at'] == '2026-11-05T18:37:56.495943+00:00')
            self.assertEqual(inventory['candidate_games'],1439 if league=='ncaam' else 1377)
            self.assertEqual(inventory['observed_finals'],370 if league=='ncaam' else 368)
            self.assertFalse(data['observed_inventory']['all_official_games_covered'])
            self.assertEqual(data['current_coverage_gaps']['rejected_official_records'],4)
            self.assertFalse(attempt['scientific_goal_complete'])

    def test_b041_setup_failure_does_not_create_science_or_refresh_the_display(self):
        for data in self.exports.values():
            attempt = next(x for x in data['owner_attempt_history'] if x['release'] == 'B041')
            self.assertEqual(attempt['release'], 'B041')
            self.assertEqual(attempt['failure_phase'], 'PRE_SCIENCE_PREDECESSOR_SETUP')
            self.assertEqual(attempt['failure_code'], 'PROGRESS_COUNTER_WENT_BACKWARD')
            self.assertEqual((attempt['synthetic_tests_passed'], attempt['synthetic_tests_skipped'],
                              attempt['synthetic_test_errors']), (982, 1, 0))
            self.assertEqual((attempt['completed_scientific_stages'], attempt['attempted_scientific_stages'],
                              attempt['planned_scientific_stages']), (0, 0, 15))
            self.assertEqual(len(attempt['stages']), 15)
            self.assertTrue(all(s['status'] == 'NOT_STARTED' and s['seconds'] is None for s in attempt['stages']))
            self.assertIsNone(attempt['phase_seconds']['science'])
            self.assertAlmostEqual(attempt['phase_seconds']['setup'], 18.793449206990772)
            self.assertAlmostEqual(sum(v for v in attempt['phase_seconds'].values() if v is not None),
                                   attempt['total_wall_seconds'])
            for key in ('new_real_target_fits', 'new_calibration_fits', 'new_empirical_residual_fits',
                        'reused_target_fits', 'reused_native_target_fits', 'new_provider_requests',
                        'new_injury_requests', 'new_injury_fits', 'new_prediction_rows', 'new_prospective_issues'):
                self.assertEqual(attempt[key], 0)
            self.assertFalse(attempt['progress']['candidate_registrations_are_imports'])
            self.assertEqual(attempt['progress']['first_queue_registered_candidates'], 108)
            self.assertEqual(attempt['progress']['second_queue_registered_completions'], 0)
            inventory = next(x for x in data['inventory_history'] if x['snapshot_at'] == '2026-11-05T18:37:56.495943+00:00')
            self.assertEqual(inventory['authenticated_current_issues'], 0)

    def test_b040_attempt_and_its_actual_acquisition_survive_in_history(self):
        for data in self.exports.values():
            attempt = next(x for x in data['owner_attempt_history'] if x['release'] == 'B040')
            self.assertEqual((attempt['completed_scientific_stages'], attempt['planned_scientific_stages']), (6, 13))
            self.assertEqual(attempt['failure_class'], 'NoSuchKey')
            self.assertEqual(attempt['reused_target_fits'], 108)
            self.assertEqual(attempt['new_prediction_rows'], 3969)
            self.assertEqual(attempt['new_provider_requests'], 6351)
            self.assertEqual(attempt['new_real_target_fits'], 0)
            self.assertAlmostEqual(attempt['phase_seconds']['science'], 2490.3243649669894)
            preserved = next(x for x in data['coverage_history'] if x['release'] == 'B040')
            self.assertEqual(preserved['current_coverage_gaps']['market_observations'], 557737)

    def test_b042_partial_completion_preserves_distinct_fit_and_issue_credit(self):
        for league, data in self.exports.items():
            attempt = next(x for x in data['owner_attempt_history'] if x['release'] == 'B042')
            self.assertEqual(attempt['release'], 'B042')
            self.assertEqual(attempt['status'], 'FAILED_PARTIAL_WORK_PRESERVED')
            self.assertEqual(attempt['failure_code'], 'B041_BASE_DETERMINISTIC_BLEND_MISMATCH')
            self.assertEqual([s['status'] for s in attempt['stages']], ['COMPLETED'] * 9 + ['FAILED'] + ['NOT_STARTED'] * 5)
            self.assertEqual((attempt['new_real_target_fits'], attempt['new_calibration_fits'], attempt['new_empirical_residual_fits']), (102, 46, 24))
            self.assertEqual(attempt['league_new_real_target_fits'], 69 if league == 'ncaam' else 33)
            self.assertEqual((attempt['reused_target_fits'], attempt['reused_native_target_fits'], attempt['reused_native_scalar_fits']), (108, 12, 6))
            self.assertEqual((attempt['synthetic_tests_passed'], attempt['synthetic_tests_skipped'], attempt['synthetic_test_errors']), (1029, 1, 0))
            self.assertAlmostEqual(sum(attempt['phase_seconds'].values()), attempt['total_wall_seconds'])
            result = next(x for x in data['review_history'] if x['release'] == 'B042')['current_results_status']
            self.assertEqual((result['authenticated_issue_rows_both_leagues'], result['authenticated_issue_games_both_leagues']), (339, 5))
            self.assertEqual((result['authenticated_issue_rows_this_league'], result['authenticated_issue_games_this_league']), (132, 2) if league == 'ncaam' else (207, 3))
            self.assertEqual((result['new_issues_created_by_recovery'], result['new_fits_created_by_recovery']), (0, 0))
            self.assertEqual(result['original_as_issued_credit'], 0)
            self.assertTrue(result['recovery_preserved_original_issue_bytes'])
            self.assertIsNone(result['new_paired_metrics'])
            self.assertIsNone(result['new_model_winner'])
            self.assertFalse(data['current_reconstructed_comparison']['latest_owner_result'])

    def test_retained_provider_counts_and_capture_clocks_do_not_claim_complete_coverage(self):
        for league, data in self.exports.items():
            self.assertEqual([p['retained_observations_both_leagues'] for p in data['providers']], [561323, 161903, 266])
            self.assertEqual(sum(p['retained_observations_both_leagues'] for p in data['providers']), 723492)
            inventory = data['observed_inventory']
            self.assertEqual((inventory['candidate_games'], inventory['observed_finals']), (1439, 395) if league == 'ncaam' else (1379, 434))
            self.assertFalse(inventory['all_official_games_covered'])
            self.assertIsNone(data['current_coverage_gaps']['official_denominator'])
            self.assertEqual(data['freshness']['source_acquisition_completed_at'], '2026-11-06T02:14:03.087794+00:00')
            self.assertEqual(data['freshness']['retained_quote_time_range_utc']['maximum_utc'], '2026-11-06T02:11:54.749000+00:00')
            self.assertEqual(data['freshness']['retained_observation_acquisition_range_utc']['maximum_utc'], '2026-11-06T02:13:35.659420+00:00')
            for provider in data['providers']:
                for row in provider['numeric_display_coverage']:
                    self.assertEqual(row['denominator'], inventory['observed_finals'])
                    self.assertLessEqual(row['numeric_observation_rows'], row['denominator'])
                    self.assertLessEqual(row['semantics_verified_rows'], row['numeric_observation_rows'])

    def test_injury_clock_gaps_and_prepared_research_are_not_measured_gains(self):
        for data in self.exports.values():
            injury = data['injury_research']
            self.assertEqual(injury['bound_observations'] + injury['unresolved_observations'], 1320)
            self.assertEqual(injury['supported_source_availability_upper_bounds'] + injury['source_availability_upper_bound_unknown'], 1320)
            self.assertEqual(injury['historical_image_publication_unverified'] + injury['current_pdf_publication_unknown'], 1246)
            self.assertEqual(injury['historical_snapshot_versions_verified'], 0)
            self.assertEqual(injury['new_owner_injury_fits'], 0)
            self.assertFalse(injury['injury_improvement_measured'])
            self.assertFalse(injury['all_injuries_complete'])
            frontier = data['frontier_research']
            self.assertEqual(frontier['status'], 'NOT_REACHED_AFTER_INJURY_CHECKPOINT_FAILURE')
            self.assertEqual(frontier['new_model_fits'], 0)
            self.assertIsNone(frontier['measured_gain'])

    def test_historical_scores_and_selection_contract_are_unchanged(self):
        pins = {
            'ncaam': ('45351ee25d6eaa787f649964085a68292ea0a6c84c11346b5e95e16bd47b15b1', '94ffa143fb5ac5741a1912180fbc7a949e9b5d6d73db8647879a60aee8c94618'),
            'ncaaw': ('608f962efb925fa2df36fbe899be1123d914c017180be02c0fc4b4050ee7151b', '6b1e7d544535d1a44a03a22d80227881f4fa57e899e4dec23c6cfe5c0c21bd3b'),
        }
        for league, data in self.exports.items():
            for key, pin in zip(('models', 'objective_tradeoff'), pins[league]):
                self.assertEqual(hashlib.sha256(json.dumps(data[key], sort_keys=True, separators=(',', ':')).encode()).hexdigest(), pin)

    def test_current_pair_is_retrospective_and_preserves_opposing_metric_results(self):
        pair=self.exports['ncaam']['current_reconstructed_comparison']
        self.assertEqual(pair['paired_games'],122)
        self.assertFalse(pair['as_issued'])
        self.assertFalse(pair['current_outcomes_selected_model'])
        self.assertGreater(pair['model_metrics']['accuracy'],pair['provider_metrics']['accuracy'])
        self.assertGreater(pair['model_metrics']['log_loss'],pair['provider_metrics']['log_loss'])
        self.assertGreater(pair['model_metrics']['brier'],pair['provider_metrics']['brier'])
        self.assertEqual((pair['model_right_provider_wrong'],pair['provider_right_model_wrong']),(7,2))
        self.assertIsNone(pair['profit'])
        self.assertIsNone(pair['uncertainty_interval'])
        self.assertEqual(self.exports['ncaaw']['current_reconstructed_comparison']['status'],'NO_EXACT_PAIRED_COHORT_SUPPLIED')

    def test_b044_execution_is_separate_from_dated_b043_scientific_evidence(self):
        for data in self.exports.values():
            current = next(a for a in data['owner_attempt_history'] if a['release'] == 'B044')
            self.assertEqual(current['release'], 'B044')
            self.assertEqual((current['completed_scientific_stages'], current['attempted_scientific_stages'], current['planned_scientific_stages']), (0, 1, 16))
            self.assertEqual([s['status'] for s in current['stages']], ['FAILED'] + ['NOT_STARTED'] * 15)
            for key in ('new_real_target_fits', 'new_calibration_fits', 'new_empirical_residual_fits', 'new_injury_fits', 'new_prospective_issues', 'new_prediction_rows', 'new_provider_requests', 'reused_target_fits'):
                self.assertEqual(current[key], 0, key)
            self.assertEqual(current['failure_code'], 'UNSUPPORTED_PRODUCER_HANDOFF')
            self.assertEqual(current['delivery_status'], 'RETURN_FULL_READBACK_VERIFIED')
            self.assertAlmostEqual(sum(current['phase_seconds'].values()), current['total_wall_seconds'])
            readback = current['storage_readback']
            self.assertEqual((readback['chunks'], readback['observations'], readback['logical_bytes'], readback['new_full_storage_GETs']), (90, 723492, 1504058360, 182))
            self.assertFalse(readback['earlier_availability_credit'])
            self.assertTrue(readback['source_clocks_unchanged'])
            self.assertEqual(readback['new_provider_requests'], 0)
            self.assertEqual(data['prepared_execution']['release'], 'B046')
            self.assertFalse(data['prepared_execution']['owner_execution_observed'])
            self.assertEqual(data['prepared_execution']['new_scientific_credit'], 0)
            old = next(r for r in data['review_history'] if r['release'] == 'B043')
            self.assertEqual(data['freshness'], old['freshness'])
            self.assertEqual(data['current_results_status'], old['current_results_status'])
            self.assertEqual(data['latest_reconstructed_comparison']['model_metrics'], old['latest_reconstructed_comparison']['model_metrics'])
            self.assertEqual(data['latest_reconstructed_comparison']['provider_metrics'], old['latest_reconstructed_comparison']['provider_metrics'])
            self.assertEqual(build_dashboard.scientific_attempt(data)['release'], 'B043')

    def test_readback_preparation_and_duplicate_owner_cannot_gain_credit(self):
        for mutation in ('fit', 'readback_provider', 'readback_availability', 'readback_clock', 'prepared', 'duplicate_owner'):
            corrupted = copy.deepcopy(self.exports['ncaam'])
            if mutation == 'fit':
                corrupted['current_owner_attempt']['new_real_target_fits'] = 1
            elif mutation == 'readback_provider':
                build_dashboard.dated_readback(corrupted)['new_provider_requests'] = 182
            elif mutation == 'readback_availability':
                build_dashboard.dated_readback(corrupted)['earlier_availability_credit'] = True
            elif mutation == 'readback_clock':
                build_dashboard.dated_readback(corrupted)['source_clocks_unchanged'] = False
            elif mutation == 'prepared':
                corrupted['prepared_execution']['owner_execution_observed'] = True
            else:
                corrupted['owner_attempt_history'].append(copy.deepcopy(build_dashboard.scientific_attempt(corrupted)))
            with patch.object(Path, 'read_text', return_value=json.dumps(corrupted)):
                with self.assertRaises(ValueError):
                    build_dashboard.evidence('ncaam')

    def test_b045_unknown_work_is_not_zero_or_terminal_success(self):
        for data in self.exports.values():
            current = data['current_owner_attempt']
            self.assertEqual(current['release'], 'B045')
            self.assertEqual(current['status'], 'WORKER_EXITED_WITHOUT_TERMINAL_RETURN')
            self.assertEqual((current['completed_scientific_stages'], current['attempted_scientific_stages'], current['planned_scientific_stages']), (9, 10, 16))
            self.assertEqual([s['status'] for s in current['stages']], ['COMPLETED'] * 9 + ['FAILED'] + ['NOT_STARTED'] * 6)
            self.assertEqual(current['child_exit_code'], -9)
            for key in ('new_real_target_fits', 'new_calibration_fits', 'new_empirical_residual_fits', 'new_injury_fits', 'new_prospective_issues', 'completed_at', 'external_shell_exit_code', 'total_wall_seconds', 'cpu_seconds', 'owner_peak_rss_bytes', 'synthetic_tests_total'):
                self.assertIsNone(current[key], key)
            self.assertFalse(current['durable_return_verified'])
            self.assertFalse(current['out_of_memory_proved'])
            self.assertEqual(current['phase_seconds'], {'injury_stage': 1527.417660635})
            self.assertNotIn('storage_readback', current)
            self.assertEqual((data['b045_baseline_observation']['target_rows'], data['b045_baseline_observation']['browser_display_rows']), (87003, 47940))
            self.assertIsNone(data['b045_baseline_observation']['new_issue_credit'])
            self.assertEqual(data['older_dashboard_assertion']['status'], 'UNRESOLVED_OLDER_DASHBOARD_ASSERTION')
            self.assertFalse(data['older_dashboard_assertion']['exact_two_file_membership_verified'])

    def test_unproved_terminal_success_and_signal_cause_are_rejected(self):
        for key, value in [('completed_at', '2026-11-06T22:00:00Z'), ('external_shell_exit_code', 0), ('durable_return_verified', True), ('out_of_memory_proved', True), ('kill_cause', 'OOM')]:
            corrupted = copy.deepcopy(self.exports['ncaam'])
            corrupted['current_owner_attempt'][key] = value
            with self.subTest(key=key), patch.object(Path, 'read_text', return_value=json.dumps(corrupted)):
                with self.assertRaises(ValueError):
                    build_dashboard.evidence('ncaam')

    def test_spread_example_is_generated_from_executable_invented_contract(self):
        from spread_ats import demo
        for data in self.exports.values():
            self.assertFalse(data['ats_research']['real_ats_record_published'])
            self.assertIsNone(data['ats_research']['real_cover_probability_champion'])
            output = build_dashboard.render_track(data)
            embedded = re.search(r'<script type="application/json" id="spread-ats-evidence">(.*?)</script>', output, re.S)
            self.assertIsNotNone(embedded)
            self.assertEqual(json.loads(embedded.group(1)), demo())
            self.assertIn('A point margin or winner probability alone cannot supply it.', output)

    def test_b043_durable_reports_separate_new_and_inherited_issue_credit(self):
        for league, data in self.exports.items():
            a, r = build_dashboard.scientific_attempt(data), data['current_results_status']
            self.assertEqual(a['release'], 'B043')
            self.assertEqual((a['completed_scientific_stages'], a['attempted_scientific_stages'], a['planned_scientific_stages']), (9, 10, 16))
            self.assertEqual([x['status'] for x in a['stages']], ['COMPLETED'] * 9 + ['FAILED'] + ['NOT_STARTED'] * 6)
            self.assertEqual((a['new_real_target_fits'], a['new_calibration_fits'], a['new_empirical_residual_fits']), (101, 45, 24))
            self.assertEqual(a['league_new_real_target_fits'], 68 if league == 'ncaam' else 33)
            self.assertEqual((a['new_prospective_issues'], a['retained_prior_prospective_issues']), (0, 339))
            self.assertEqual((r['pre_study_target_rows'], r['pre_study_game_model_rows'], r['browser_display_rows']), (84195, 46525, 46529))
            self.assertEqual(sum(r['prediction_rows'].values()), a['new_prediction_rows'])
            self.assertEqual(a['new_prediction_rows'], 83856)
            self.assertEqual((r['independent_metric_panels_checked'], r['independent_metric_mismatches']), (944, 0))
            self.assertEqual(r['admitted_settled_issue_rows'], 0)
            self.assertEqual(data['current_coverage_gaps']['completed_status_records'], 830)
            self.assertEqual(data['current_coverage_gaps']['both_leagues_observed_finals'], 829)
            self.assertTrue(data['observed_inventory']['numeric_final_score_required'])
            self.assertAlmostEqual(sum(a['phase_seconds'].values()), a['total_wall_seconds'])
            self.assertEqual(data['injury_research']['new_semantic_injury_records'], 0)
            self.assertTrue(data['injury_research']['semantic_inventory_unchanged_excluding_capture_fields'])

    def test_new_129_game_pair_appends_to_preserved_122_game_evidence(self):
        d = self.exports['ncaam']; latest = d['latest_reconstructed_comparison']
        self.assertEqual((d['current_reconstructed_comparison']['paired_games'], latest['paired_games']), (122, 129))
        self.assertEqual(latest['cohort_sha256'], '1b6f46a326919243344214018fb5b5d10a66cdc94edf0a70722bb705ad400753')
        self.assertAlmostEqual(latest['model_metrics']['log_loss'], .34440721423736326)
        self.assertAlmostEqual(latest['provider_metrics']['log_loss'], .32122632357105746)
        self.assertGreater(latest['model_metrics']['accuracy'], latest['provider_metrics']['accuracy'])
        for metric in ('log_loss', 'brier'):
            self.assertGreater(latest['model_metrics'][metric], latest['provider_metrics'][metric])
        self.assertLess(latest['model_metrics']['auc'], latest['provider_metrics']['auc'])
        self.assertFalse(latest['as_issued'])
        self.assertFalse(latest['current_outcomes_selected_model'])
        self.assertEqual((latest['model_right_provider_wrong'], latest['provider_right_model_wrong']), (7, 2))
        self.assertEqual(latest['qualified_settled_bets'], 0)
        self.assertIsNone(latest['profit'])
        self.assertIsNone(latest['uncertainty_interval'])
        self.assertEqual(self.exports['ncaaw']['latest_reconstructed_comparison']['paired_games'], 0)
        self.assertIsNone(self.exports['ncaaw']['latest_reconstructed_comparison']['model_metrics'])
        self.assertNotEqual(latest['evidence_snapshot_at'], d['current_reconstructed_comparison']['evidence_snapshot_at'])

    def test_quote_display_is_distinct_from_forecast_eligibility(self):
        for data in self.exports.values():
            self.assertFalse(data['quote_display_contract']['model_required_to_display_quote'])
            polymarket = next(p for p in data['providers'] if p['name'] == 'Polymarket')
            self.assertEqual([p['name'] for p in polymarket['products']], ['International', 'US'])
            self.assertEqual(polymarket['products'][1]['status'], 'NOT_ACQUIRED_UNVERIFIED')

    def test_public_export_contains_aggregates_not_prediction_records(self):
        disallowed_keys = {'event_id', 'home_id', 'away_id', 'recipe', 'features', 'feature_columns', 'coefficients', 'weights', 's3_key', 'bucket', 'access_key', 'secret', 'predictions'}
        def inspect(value):
            if isinstance(value, dict):
                self.assertFalse(disallowed_keys & set(value))
                for item in value.values():
                    inspect(item)
            elif isinstance(value, list):
                for item in value:
                    inspect(item)
        for data in self.exports.values():
            inspect(data)
            self.assertFalse(data['evaluation']['individual_prediction_rows_published'])
            self.assertFalse(data['evaluation']['active_recipes_published'])
            self.assertNotIn('s3://', json.dumps(data))

    def test_generation_is_exact_and_embedded_json_is_unchanged(self):
        for path, output in build_dashboard.outputs().items():
            self.assertEqual(path.read_text(), output)
            self.assertNotRegex(output, r'__(?:TITLE|EVIDENCE|PROGRESS_DEMO|PREFLIGHT_DEMO|HANDOFF_DEMO|SPREAD_ATS_DEMO|LEAGUE|SIBLING|SIBLING_LABEL)__')
            if path.parent.name in self.exports:
                self.assertIn('NCAA evidence review · 06 November 2026 UTC', output)
                self.assertIn('Latest run stopped during injury research.', output)
                self.assertNotIn('Latest run stopped before science', output)
                self.assertNotIn('Latest run stopped during reporting', output)
                embedded = re.search(r'<script type="application/json" id="evidence">(.*?)</script>', output, re.S)
                self.assertIsNotNone(embedded)
                self.assertEqual(json.loads(embedded.group(1)), self.exports[path.parent.name])
                progress = re.search(r'<script type="application/json" id="progress-evidence">(.*?)</script>', output, re.S)
                self.assertIsNotNone(progress)
                self.assertEqual(json.loads(progress.group(1)), demo_scenarios())
                preflight = re.search(r'<script type="application/json" id="preflight-evidence">(.*?)</script>', output, re.S)
                self.assertIsNotNone(preflight)
                self.assertEqual(json.loads(preflight.group(1)), preflight_scenarios())

    def test_generated_pages_have_unique_dom_identities(self):
        class IdCollector(HTMLParser):
            def __init__(self):
                super().__init__()
                self.ids = []
            def handle_starttag(self, tag, attrs):
                self.ids.extend(value for key, value in attrs if key == 'id')
        for path, output in build_dashboard.outputs().items():
            parser = IdCollector()
            parser.feed(output)
            self.assertEqual(len(parser.ids), len(set(parser.ids)), str(path))

    def test_new_viewer_navigation_works_at_repository_and_hosted_roots(self):
        host = 'https://alvaro-ncaa-research-review.alv-mendizabal.chatgpt.site'
        for league in ('ncaam', 'ncaaw'):
            self.assertIn('href="' + host + '/private-report/index.html"', build_dashboard.render_track(self.exports[league]))
        viewer = (build_dashboard.HERE / 'private_report.html.tmpl').read_text()
        self.assertIn('href="' + host + '/tracks/ncaam/index.html"', viewer)
        self.assertIn('href="' + host + '/tracks/ncaaw/index.html"', viewer)

    def test_export_validation_rejects_provider_scope_and_cohort_mutation(self):
        for mutation in ('provider', 'cohort', 'stage', 'observation', 'issue_credit', 'issue_scope', 'capture_release', 'new_owner_issue', 'retained_issue', 'target_rows', 'display_rows', 'pair_profit', 'pair_clock'):
            corrupted = copy.deepcopy(self.exports['ncaam'])
            if mutation == 'provider':
                corrupted['providers'][0]['name'] = 'invented-unregistered-provider'
            elif mutation == 'cohort':
                corrupted['models'][0]['panels']['pooled']['N'] += 1
            elif mutation == 'stage':
                corrupted['current_owner_attempt']['stages'][9]['status'] = 'COMPLETED'
            elif mutation == 'observation':
                corrupted['providers'][0]['retained_observations_both_leagues'] += 1
            elif mutation == 'issue_credit':
                corrupted['current_results_status']['new_issues_created_by_recovery'] = 339
            elif mutation == 'issue_scope':
                corrupted['current_results_status']['authenticated_issue_rows_this_league'] += 1
            elif mutation == 'new_owner_issue':
                corrupted['current_owner_attempt']['new_prospective_issues'] = 339
            elif mutation == 'retained_issue':
                build_dashboard.scientific_attempt(corrupted)['retained_prior_prospective_issues'] = 0
            elif mutation == 'target_rows':
                corrupted['current_results_status']['pre_study_target_rows'] += 1
            elif mutation == 'display_rows':
                corrupted['current_results_status']['browser_display_rows'] += 1
            elif mutation == 'pair_profit':
                corrupted['latest_reconstructed_comparison']['profit'] = 1
            elif mutation == 'pair_clock':
                corrupted['latest_reconstructed_comparison']['evidence_snapshot_at'] = '2026-11-05T00:00:00Z'
            else:
                corrupted['freshness']['owner_release'] = 'B041'
            with patch.object(Path, 'read_text', return_value=json.dumps(corrupted)):
                with self.assertRaises(ValueError):
                    build_dashboard.evidence('ncaam')

    def test_landing_uses_current_evidence_and_rejects_mixed_league_snapshots(self):
        exports = list(self.exports.values())
        landing = build_dashboard.render_landing(exports)
        self.assertIn('B045: 9 of 16 stages completed; child exited without its terminal return.', landing)
        self.assertIn('723,492 market observations', landing)
        self.assertIn('339 existing research issue rows across 5 games', landing)
        self.assertNotIn('Latest owner stopped before science', landing)
        changed = copy.deepcopy(exports)
        changed[1]['observed_inventory']['candidate_games'] += 1
        with self.assertRaisesRegex(ValueError, 'source inventory closure'):
            build_dashboard.render_landing(changed)
        changed = copy.deepcopy(exports)
        changed[1]['current_owner_attempt']['release'] = 'B041'
        with self.assertRaisesRegex(ValueError, 'release disagreement'):
            build_dashboard.render_landing(changed)


if __name__ == '__main__':
    unittest.main()

