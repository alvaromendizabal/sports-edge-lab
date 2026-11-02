import copy
import math
import unittest

from settlement_distribution import invented_inputs, settlement_probabilities, score_outcome


class SettlementDistributionTests(unittest.TestCase):
    def setUp(self):
        self.d, self.i = invented_inputs()

    def map(self):
        return settlement_probabilities(self.d, self.i)

    def test_independent_three_state_arithmetic(self):
        result = score_outcome(self.d, self.i, 7)
        self.assertEqual(result['probabilities'], {'WIN': .7, 'PUSH': .1, 'LOSS': .2})
        self.assertAlmostEqual(result['log_loss_3state'], -math.log(.7))
        self.assertAlmostEqual(result['brier_3state'], .09 + .01 + .04)
        self.assertAlmostEqual(result['conditional_win_given_no_push'], 7/9)
        self.assertAlmostEqual(result['conditional_binary_log_loss'], -math.log(7/9))
        self.assertAlmostEqual(result['conditional_binary_brier'], 4/81)
        self.assertTrue(result['unique_mode_correct'])

    def test_push_is_scored_and_excluded_only_from_conditional_loss(self):
        result = score_outcome(self.d, self.i, 3)
        self.assertEqual(result['actual_state'], 'PUSH')
        self.assertAlmostEqual(result['log_loss_3state'], -math.log(.1))
        self.assertAlmostEqual(result['brier_3state'], .49 + .81 + .04)
        self.assertIsNone(result['conditional_binary_log_loss'])
        self.assertIsNone(result['conditional_binary_brier'])

    def test_away_reverses_win_loss_and_preserves_push(self):
        home = score_outcome(self.d, self.i, 7)
        self.i['side'] = 'AWAY'
        away = score_outcome(self.d, self.i, 7)
        self.assertEqual(away['probabilities'], {'WIN': .2, 'PUSH': .1, 'LOSS': .7})
        self.assertEqual(away['actual_state'], 'LOSS')
        self.assertAlmostEqual(home['log_loss_3state'], away['log_loss_3state'])
        self.assertAlmostEqual(home['brier_3state'], away['brier_3state'])

    def test_half_point_line_has_no_push(self):
        self.i['threshold'] = 3.5
        self.assertEqual(self.map()['probabilities']['PUSH'], 0)
        self.assertEqual(score_outcome(self.d, self.i, 3)['actual_state'], 'LOSS')

    def test_total_over_under_and_zero_total(self):
        self.d['target'] = self.i['target'] = 'total'
        self.d['support'] = [{'points': 0, 'probability': .2}, {'points': 44, 'probability': .3}, {'points': 47, 'probability': .5}]
        self.i.update(side='OVER', threshold=44)
        self.assertEqual(self.map()['probabilities'], {'WIN': .5, 'PUSH': .3, 'LOSS': .2})
        self.i['side'] = 'UNDER'
        self.assertEqual(self.map()['probabilities'], {'WIN': .2, 'PUSH': .3, 'LOSS': .5})
        with self.assertRaises(ValueError): score_outcome(self.d, self.i, -1)
        self.d['support'][0]['points'] = -1
        with self.assertRaises(ValueError): self.map()

    def test_no_point_center_to_probability_conversion(self):
        self.d['support'] = []
        self.d['point_center'] = 3.2
        with self.assertRaises(ValueError): self.map()

    def test_same_mean_can_have_different_cover_probability(self):
        self.i['threshold'] = 0
        self.d['support'] = [{'points': -1, 'probability': .5}, {'points': 1, 'probability': .5}]
        first = self.map()['probabilities']['WIN']
        self.d['support'] = [{'points': -3, 'probability': .25}, {'points': 1, 'probability': .75}]
        second = self.map()['probabilities']['WIN']
        self.assertEqual((first, second), (.5, .75))

    def test_impossible_outcome_is_infinite_not_clipped(self):
        self.d['support'] = [{'points': 7, 'probability': 1}]
        result = score_outcome(self.d, self.i, -7)
        self.assertEqual(result['log_loss_3state'], math.inf)
        self.assertEqual(result['brier_3state'], 2)
        self.assertEqual(result['conditional_binary_log_loss'], math.inf)

    def test_all_push_distribution_has_no_conditional_probability(self):
        self.d['support'] = [{'points': 3, 'probability': 1}]
        result = score_outcome(self.d, self.i, 3)
        self.assertIsNone(result['conditional_win_given_no_push'])
        self.assertEqual(result['log_loss_3state'], 0)
        self.assertEqual(result['brier_3state'], 0)

    def test_rare_positive_loss_mass_does_not_cancel_to_zero(self):
        self.d['support'] = [{'points': -7, 'probability': 1e-20}, {'points': 7, 'probability': 1.0}]
        result = score_outcome(self.d, self.i, -7)
        self.assertTrue(math.isfinite(result['conditional_binary_log_loss']))
        self.assertAlmostEqual(result['conditional_binary_log_loss'], -math.log(1e-20))
        self.assertAlmostEqual(result['conditional_binary_log_loss'], result['log_loss_3state'])

    def test_tied_mode_abstains(self):
        self.d['support'] = [{'points': -7, 'probability': .5}, {'points': 7, 'probability': .5}]
        self.assertIsNone(score_outcome(self.d, self.i, 7)['unique_mode_correct'])

    def test_missing_actual_retains_forecast(self):
        result = score_outcome(self.d, self.i, None)
        self.assertEqual(result['scoring_status'], 'MISSING_OUTCOME')
        self.assertIsNone(result['log_loss_3state'])
        self.assertEqual(result['probabilities']['WIN'], .7)

    def test_wrong_events_targets_settlement_and_cutoff_rejected(self):
        for key, value in [('event_id', 'another-game'), ('target', 'total'), ('settlement_id', 'REGULATION_ONLY'), ('decision_at', '2026-09-10T23:00:00Z'), ('kickoff_at', '2026-09-11T01:00:00Z')]:
            with self.subTest(key=key):
                self.setUp(); self.i[key] = value
                with self.assertRaises(ValueError): self.map()

    def test_timezone_equivalent_clock_accepted(self):
        self.i['decision_at'] = '2026-09-10T15:00:00-07:00'
        self.assertTrue(self.map()['original_issue_claim'])

    def test_timezone_free_and_at_kickoff_cutoff_rejected(self):
        self.d['decision_at'] = '2026-09-10T22:00:00'
        with self.assertRaises(ValueError): self.map()
        self.setUp(); self.d['decision_at'] = self.i['decision_at'] = self.d['kickoff_at']
        with self.assertRaises(ValueError): self.map()

    def test_source_leakage_and_label_boundary_rejected(self):
        self.d['source_asof'] = '2026-09-10T22:01:00Z'
        with self.assertRaises(ValueError): self.map()
        self.setUp(); self.d['labels_available_through'] = self.d['decision_at']
        with self.assertRaises(ValueError): self.map()

    def test_labels_after_model_impossible(self):
        self.d['labels_available_through'] = '2026-09-10T20:31:00Z'
        with self.assertRaises(ValueError): self.map()

    def test_late_computation_cannot_be_original_issue(self):
        self.d['computed_at'] = self.d['issued_at'] = '2026-09-10T23:00:00Z'
        with self.assertRaises(ValueError): self.map()

    def test_issue_before_computation_rejected(self):
        self.d['issued_at'] = '2026-09-10T20:59:00Z'
        with self.assertRaises(ValueError): self.map()

    def test_late_reconstruction_preserves_qualification(self):
        self.d.update(evidence_class='RECONSTRUCTION', issued_at=None, source_available_at='2026-09-12T00:00:00Z', model_available_at='2026-09-12T01:00:00Z', computed_at='2026-09-12T02:00:00Z')
        result = self.map()
        self.assertFalse(result['original_issue_claim'])
        self.assertTrue(result['late_source_possession'])
        self.assertTrue(result['late_model_availability'])
        self.assertIsNone(result['actual_profit'])
        self.d['issued_at'] = self.d['computed_at']
        with self.assertRaises(ValueError): self.map()

    def test_reconstruction_cannot_admit_future_source(self):
        self.d.update(evidence_class='RECONSTRUCTION', issued_at=None, source_asof='2026-09-11T01:00:00Z', source_available_at='2026-09-12T00:00:00Z', computed_at='2026-09-12T02:00:00Z')
        with self.assertRaises(ValueError): self.map()

    def test_malformed_distribution_values_rejected(self):
        for value in (True, float('nan'), float('inf'), -0.1, 1.1, '0.2'):
            with self.subTest(value=value):
                self.setUp(); self.d['support'][0]['probability'] = value
                with self.assertRaises(ValueError): self.map()
        self.setUp(); self.d['support'][0]['points'] = 1.5
        with self.assertRaises(ValueError): self.map()

    def test_mass_and_duplicate_points_rejected(self):
        self.d['support'][0]['probability'] = .3
        with self.assertRaises(ValueError): self.map()
        self.setUp(); self.d['support'].append({'points': -7, 'probability': 0})
        with self.assertRaises(ValueError): self.map()

    def test_tiny_mass_rounding_is_explicit(self):
        self.d['support'][0]['probability'] += 2e-13
        result = self.map()
        self.assertTrue(result['roundoff_mass_normalized'])
        self.assertAlmostEqual(math.fsum(result['probabilities'].values()), 1)

    def test_quarter_line_unsupported_and_wrong_side_rejected(self):
        for key, value in [('threshold', 3.25), ('side', 'OVER'), ('equality_rule', 'PUSH_COUNTS_LOSS')]:
            with self.subTest(key=key):
                self.setUp(); self.i[key] = value
                with self.assertRaises(ValueError): self.map()

    def test_exact_declarations_are_pinned_and_not_mutated(self):
        before = copy.deepcopy((self.d, self.i))
        result = self.map()
        self.assertEqual(before, (self.d, self.i))
        self.d['source_id'] = 'another-source'
        self.assertNotEqual(result['distribution_sha256'], self.map()['distribution_sha256'])
        self.assertEqual(result['instrument_sha256'], self.map()['instrument_sha256'])


if __name__ == '__main__':
    unittest.main()
