"""Check the actual sanitized export and its rendered review contract."""
import copy
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
            a = data['current_owner_attempt']
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
            d = data['observed_inventory']
            self.assertEqual((d['candidate_games'], d['observed_finals'], d['last_week']['candidate_games'], d['this_week']['candidate_games']), expected[league])
            self.assertEqual(d['candidate_games'], d['last_week']['candidate_games'] + d['this_week']['candidate_games'])
            self.assertEqual(d['snapshot_at'], '2026-11-03T00:48:42+00:00')
            self.assertFalse(d['official_inventory_reconciled'])
            self.assertFalse(d['all_official_games_covered'])
            self.assertEqual(d['authenticated_current_issues'], 0)

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
            self.assertNotRegex(output, r'__(?:TITLE|EVIDENCE|PROGRESS_DEMO|PREFLIGHT_DEMO|LEAGUE|SIBLING|SIBLING_LABEL)__')
            if path.parent.name in self.exports:
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

    def test_export_validation_rejects_provider_scope_and_cohort_mutation(self):
        for mutation in ('provider', 'cohort'):
            corrupted = copy.deepcopy(self.exports['ncaam'])
            if mutation == 'provider':
                corrupted['providers'][0]['name'] = 'invented-unregistered-provider'
            else:
                corrupted['models'][0]['panels']['pooled']['N'] += 1
            with patch.object(Path, 'read_text', return_value=json.dumps(corrupted)):
                with self.assertRaises(ValueError):
                    build_dashboard.evidence('ncaam')


if __name__ == '__main__':
    unittest.main()
