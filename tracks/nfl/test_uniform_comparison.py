import copy
import math
import unittest

from uniform_comparison import compare_fixed_cohort, cohort_digest, invented_inputs


class UniformComparisonTests(unittest.TestCase):
    def setUp(self):
        self.contract, self.games, self.models, self.refs = invented_inputs()

    def run_comparison(self):
        return compare_fixed_cohort(self.contract, self.games, self.models, self.refs)

    def make_points(self, target='margin'):
        self.contract.update(target=target, orientation='HOME_MINUS_AWAY' if target == 'margin' else 'TOTAL', value_basis='POINT_CENTER')
        for i, game in enumerate(self.games):
            game.update(actual=[7, 3, 3, 0][i], line=3)
        for rows in (self.models, self.refs):
            for row in rows:
                row.update({k: self.contract[k] for k in ('target', 'orientation', 'value_basis')})
                row.update(line=3, value=3)
        for row, value in zip(self.models, [5, 4, 3, 2]):
            row['value'] = value

    def test_complete_winner_2x2_and_net_accuracy(self):
        result = self.run_comparison()
        d = result['explicit_matched_subset']['diagnostics']
        self.assertEqual([d[k] for k in ('BOTH_RIGHT','MODEL_ONLY_RIGHT','REFERENCE_ONLY_RIGHT','NEITHER_RIGHT')], [1,1,1,1])
        self.assertEqual(d['disagreements'], 2)
        self.assertEqual(d['net_extra_correct'], 0)
        self.assertEqual(d['accuracy_delta'], 0)
        self.assertEqual(result['headline_scores']['model']['accuracy'], .5)

    def test_independent_probability_arithmetic(self):
        scores = self.run_comparison()['headline_scores']
        self.assertAlmostEqual(scores['model']['log_loss'], (-math.log(.7)-math.log(.3))/2)
        self.assertAlmostEqual(scores['model']['brier'], (.09+.49)/2)
        self.assertIsNone(scores['model']['mae'])

    def test_missing_provider_cannot_shrink_headline(self):
        original = self.run_comparison()
        self.refs.pop()
        result = self.run_comparison()
        self.assertEqual(result['fixed_n'], 4)
        self.assertEqual(result['matched_n'], 3)
        self.assertEqual(result['fixed_cohort_sha256'], original['fixed_cohort_sha256'])
        self.assertIsNone(result['headline_scores'])
        self.assertEqual(result['coverage'], .75)
        self.assertNotEqual(result['explicit_matched_subset']['cohort_sha256'], original['fixed_cohort_sha256'])

    def test_no_provider_is_unknown_not_zero(self):
        self.refs = []
        result = self.run_comparison()
        self.assertIsNone(result['headline_scores'])
        self.assertIsNone(result['explicit_matched_subset']['scores']['reference']['accuracy'])
        self.assertEqual(len(result['ledger']), 4)

    def test_missing_model_is_symmetric(self):
        self.models.pop()
        self.assertEqual(self.run_comparison()['matched_n'], 3)

    def test_event_membership_not_just_count_is_pinned(self):
        self.contract['game_ids'][-1] = 'different'
        with self.assertRaises(ValueError): self.run_comparison()

    def test_reordered_rows_keep_cohort_and_scores(self):
        original = self.run_comparison()
        self.games.reverse(); self.models.reverse(); self.refs.reverse()
        self.assertEqual(self.run_comparison(), original)

    def test_duplicate_membership_is_rejected(self):
        with self.assertRaises(ValueError): cohort_digest(['x', 'x'])

    def test_unknown_and_duplicate_rows_rejected(self):
        for field in ('games', 'models', 'refs'):
            with self.subTest(field=field):
                self.setUp(); getattr(self, field).append(copy.deepcopy(getattr(self, field)[0]))
                with self.assertRaises(ValueError): self.run_comparison()
        self.setUp(); self.refs[0]['game_id'] = 'unknown'
        with self.assertRaises(ValueError): self.run_comparison()

    def test_changed_target_orientation_settlement_and_basis_rejected(self):
        for key, value in [('target','total'),('orientation','AWAY'),('settlement','REGULATION_ONLY'),('value_basis','ENTRY_PAYOUT')]:
            with self.subTest(key=key):
                self.setUp(); self.refs[0][key] = value
                with self.assertRaises(ValueError): self.run_comparison()

    def test_different_cutoff_is_rejected(self):
        self.refs[0]['decision_at'] = '2026-09-09T21:00:00Z'
        with self.assertRaises(ValueError): self.run_comparison()

    def test_equivalent_timezone_cutoffs_match(self):
        self.refs[0]['decision_at'] = '2026-09-09T13:00:00-07:00'
        self.assertEqual(self.run_comparison()['matched_n'], 4)

    def test_late_source_or_possession_remains_visible_unscored(self):
        self.refs[0].update(source_at='2026-09-09T21:00:00Z', available_at='2026-09-09T22:00:00Z')
        result = self.run_comparison()
        self.assertEqual(result['matched_n'], 3)
        self.assertEqual(result['ledger'][0]['state'], 'INFORMATION_AFTER_CUTOFF')

    def test_reconstruction_time_does_not_become_original_issue(self):
        row = self.run_comparison()['ledger'][0]
        self.assertTrue(row['model_created_after_decision'])
        self.assertEqual(row['model_clocks']['created_at'], self.models[0]['created_at'])
        self.assertEqual(row['classification'], 'DECLARED_REPLAY_NOT_ORIGINAL_ISSUED_BET')

    def test_impossible_or_naive_clocks_rejected(self):
        for key, value in [('source_at','2026-09-09T19:30:00Z'),('created_at','2026-09-09T18:30:00Z'),('available_at','2026-09-09T19:00:00')]:
            with self.subTest(key=key):
                self.setUp(); self.refs[0][key] = value
                with self.assertRaises(ValueError): self.run_comparison()

    def test_tie_or_pending_outcome_retained_without_binary_loss(self):
        self.games[0]['actual'] = None
        result = self.run_comparison()
        self.assertEqual(result['census_n'], 4)
        self.assertEqual(result['matched_n'], 3)
        self.assertEqual(result['ledger'][0]['state'], 'NO_ELIGIBLE_OUTCOME')

    def test_full_census_outside_fixed_cohort_survives(self):
        self.games.append(dict(game_id='invented-future', week='REG_03', actual=None, decision_at='2026-10-01T20:00:00Z'))
        result = self.run_comparison()
        self.assertEqual(result['census_n'], 5)
        self.assertEqual(result['fixed_n'], 4)
        self.assertEqual(result['weekly'][-1]['matched_n'], 0)

    def test_half_probability_has_declared_deterministic_direction(self):
        self.models[0]['value'] = .5
        self.refs[0]['value'] = .4
        self.assertEqual(self.run_comparison()['ledger'][0]['correctness'], 'REFERENCE_ONLY_RIGHT')

    def test_invalid_probability_rejected(self):
        for value in (True, float('nan'), float('inf'), -0.1, 1.1):
            with self.subTest(value=value):
                self.models[0]['value'] = value
                with self.assertRaises(ValueError): self.run_comparison()

    def test_points_have_mae_rmse_not_probability_metrics(self):
        for target in ('margin','total'):
            with self.subTest(target=target):
                self.setUp(); self.make_points(target)
                score = self.run_comparison()['headline_scores']['model']
                self.assertEqual(score['mae'], 1.25)
                self.assertEqual(score['rmse'], 1.5)
                self.assertIsNone(score['log_loss']); self.assertIsNone(score['accuracy'])

    def test_point_closeness_is_distinct_from_line_correctness(self):
        self.make_points()
        result = self.run_comparison()
        d = result['explicit_matched_subset']['diagnostics']
        self.assertEqual(d['absolute_error_wins'], {'MODEL':2,'REFERENCE':1,'EQUAL':1})
        self.assertEqual(d['model_line_direction']['RIGHT'], 2)
        self.assertEqual(d['model_line_direction']['PUSH'], 1)
        self.assertEqual(d['model_line_direction']['NO_DIRECTION'], 1)
        self.assertEqual(d['model_line_direction']['directional_accuracy'], 1)

    def test_reference_at_own_line_has_no_direction_not_fifty_percent(self):
        self.make_points()
        d = self.run_comparison()['explicit_matched_subset']['diagnostics']['reference_line_direction']
        self.assertEqual(d['NO_DIRECTION'], 4)
        self.assertIsNone(d['directional_accuracy'])

    def test_different_lines_are_not_one_binary_target(self):
        self.make_points(); self.refs[0]['line'] = 3.5
        with self.assertRaises(ValueError): self.run_comparison()

    def test_no_line_still_allows_point_errors(self):
        self.make_points()
        for row in self.games+self.models+self.refs: row['line'] = None
        result = self.run_comparison()
        self.assertEqual(result['headline_scores']['model']['mae'], 1.25)
        self.assertEqual(result['explicit_matched_subset']['diagnostics']['model_line_direction']['NO_LINE'], 4)

    def test_weekly_counts_sum_to_season(self):
        r = self.run_comparison()
        self.assertEqual(sum(w['matched_n'] for w in r['weekly']),r['matched_n'])
        self.assertEqual(sum(w['diagnostics']['MODEL_ONLY_RIGHT'] for w in r['weekly']),1)

    def test_no_fit_selection_promotion_or_profit_claim(self):
        r = self.run_comparison()
        self.assertFalse(r['selection_performed']); self.assertFalse(r['promotion_permitted'])
        self.assertIsNone(r['actual_pnl']); self.assertIsNone(r['roi']); self.assertEqual(r['actual_orders'],0)


if __name__ == '__main__':
    unittest.main()
