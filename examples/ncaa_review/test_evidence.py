"""Check the actual sanitized export and its rendered review contract."""
import copy
import json
import math
from pathlib import Path
import re
import unittest
from unittest.mock import patch

import build_dashboard


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

    def test_failed_attempt_has_no_new_science_or_provider_scores(self):
        for data in self.exports.values():
            attempt = data['current_owner_attempt']
            for key in ('new_real_target_fits', 'new_calibration_fits', 'new_source_refreshes', 'new_prediction_rows', 'new_prospective_issues', 'new_orders', 'scientific_credit_from_subsequent_readback'):
                self.assertEqual(attempt[key], 0)
            self.assertTrue(attempt['original_monitoring_unchanged'])
            self.assertEqual([p['name'] for p in data['providers']], ['Kalshi', 'Polymarket', 'DraftKings'])
            for provider in data['providers']:
                for key in ('current_log_loss', 'current_matched_games', 'hypothetical_ROI'):
                    self.assertIsNone(provider[key])
            self.assertFalse(data['market_advantage']['demonstrated'])
            self.assertIsNone(data['market_advantage']['realized_betting_profit'])

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
            self.assertNotRegex(output, r'__(?:TITLE|EVIDENCE|LEAGUE|SIBLING|SIBLING_LABEL)__')
            if path.parent.name in self.exports:
                embedded = re.search(r'<script type="application/json" id="evidence">(.*?)</script>', output, re.S)
                self.assertIsNotNone(embedded)
                self.assertEqual(json.loads(embedded.group(1)), self.exports[path.parent.name])

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
