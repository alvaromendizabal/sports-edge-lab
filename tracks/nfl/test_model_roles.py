"""Behavior tests using invented data only; never optimizer fits."""
import copy
import unittest
from model_roles import cohort_identity, comparison_roles, invented_demo


class ModelRoleTests(unittest.TestCase):
    def rows(self):
        common = {'season': 2025, 'game_ids': ['A', 'B'], 'market_reference_by_game': {'A': 0.4, 'B': 0.6}}
        return [{**copy.deepcopy(common), 'model_id': 'a', 'primary_loss': .7},
                {**copy.deepcopy(common), 'model_id': 'b', 'primary_loss': .6}]

    def test_demo_minimum_is_never_selected(self):
        d = invented_demo()
        self.assertEqual(d['retrospective_minimum']['model_ids'], ['candidate-B'])
        self.assertIsNone(d['selected_champion'])
        self.assertFalse(d['selection_permitted'])
        self.assertFalse(d['retrospective_minimum']['winner_adjusted_interval'])

    def test_unknown_challenger_is_not_zero_loss(self):
        d = invented_demo()
        self.assertIsNone(d['rows'][2]['primary_loss'])
        self.assertEqual(d['rows'][2]['status'], 'NO_AUTHENTICATED_MODEL_ROWS_IN_THIS_COMPARISON')

    def test_monitoring_never_generates_minimum(self):
        rows = self.rows()
        for r in rows: r['season'] = 2026
        d = comparison_roles(rows)
        self.assertTrue(d['monitoring_only'])
        self.assertIsNone(d['retrospective_minimum'])

    def test_equal_counts_do_not_mean_equal_games(self):
        rows = self.rows(); rows[1]['game_ids'] = ['C', 'D']; rows[1]['market_reference_by_game'] = {'C': .4, 'D': .6}
        with self.assertRaisesRegex(ValueError, 'identical games'): comparison_roles(rows)

    def test_equal_average_reference_is_insufficient(self):
        rows = self.rows(); rows[1]['market_reference_by_game'] = {'A': .6, 'B': .4}
        with self.assertRaisesRegex(ValueError, 'reference values'): comparison_roles(rows)

    def test_game_order_is_irrelevant(self):
        self.assertEqual(cohort_identity(['A', 'B']), cohort_identity(['B', 'A']))
        rows = self.rows(); rows[1]['game_ids'].reverse()
        self.assertEqual(comparison_roles(rows)['games'], 2)

    def test_duplicate_games_rejected(self):
        with self.assertRaises(ValueError): cohort_identity(['A', 'A'])

    def test_missing_reference_rejected(self):
        rows = self.rows(); del rows[1]['market_reference_by_game']['A']
        with self.assertRaisesRegex(ValueError, 'exact game'): comparison_roles(rows)

    def test_nonfinite_or_negative_loss_rejected(self):
        for value in (float('nan'), float('inf'), -1, True):
            rows = self.rows(); rows[0]['primary_loss'] = value
            with self.subTest(value=value), self.assertRaises(ValueError): comparison_roles(rows)

    def test_nonfinite_reference_rejected(self):
        rows = self.rows(); rows[0]['market_reference_by_game']['A'] = float('nan')
        with self.assertRaises(ValueError): comparison_roles(rows)

    def test_tied_minima_preserve_all_ties(self):
        rows = self.rows(); rows[0]['primary_loss'] = .6
        self.assertEqual(comparison_roles(rows)['retrospective_minimum']['model_ids'], ['a', 'b'])

    def test_no_available_losses_stays_unknown(self):
        rows = self.rows()
        for r in rows: r['primary_loss'] = None
        self.assertIsNone(comparison_roles(rows)['retrospective_minimum'])

    def test_cross_season_pooling_rejected(self):
        rows = self.rows(); rows[1]['season'] = 2026
        with self.assertRaisesRegex(ValueError, 'one season'): comparison_roles(rows)

    def test_duplicate_models_rejected(self):
        rows = self.rows(); rows[1]['model_id'] = 'a'
        with self.assertRaisesRegex(ValueError, 'Duplicate model'): comparison_roles(rows)

    def test_empty_input_rejected(self):
        with self.assertRaises(ValueError): comparison_roles([])

    def test_zero_fits_and_orders(self):
        d = invented_demo(); self.assertEqual((d['new_fits'], d['actual_orders']), (0, 0))


if __name__ == '__main__': unittest.main()
