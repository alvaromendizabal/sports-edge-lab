"""Behavior tests using invented data only; never optimizer fits."""
import copy
import unittest
from model_roles import cohort_identity, comparison_roles, invented_demo, reporting_inventory


class ReportingInventoryTests(unittest.TestCase):
    def inventory(self):
        return [{'model_id': name, 'season': 2026, 'role': role, 'training_policy': policy}
                for name, role, policy in [('market', 'MARKET_REFERENCE', 'NOT_APPLICABLE'),
                    ('frozen', 'FROZEN_CANDIDATE', 'PRIOR_SEASONS_ONLY'),
                    ('weekly', 'WEEKLY_UPDATED', 'USES_CURRENT_SEASON_LABELS')]]

    def row(self, name='frozen', loss=.6):
        return {'model_id': name, 'season': 2026, 'primary_loss': loss,
                'target': 'win', 'prediction_vector_sha256': 'a'*64,
                'cohort_sha256': 'b'*64, 'reference_sha256': 'c'*64}

    def test_missing_report_is_separate_from_reported_missing_score(self):
        result = reporting_inventory(self.inventory(), [self.row(), self.row('weekly', None)])
        self.assertEqual([r['model_id'] for r in result['missing_report_rows']], ['market'])
        self.assertEqual([r['model_id'] for r in result['reported_without_score']], ['weekly'])
        self.assertIsNone(result['missing_report_rows'][0]['primary_loss'])
        self.assertFalse(result['all_expected_rows_reported'])

    def test_roles_and_policy_are_declared_without_selection(self):
        result = reporting_inventory(self.inventory(), [self.row('weekly', .1)])
        weekly = next(r for r in result['rows'] if r['model_id'] == 'weekly')
        self.assertEqual(weekly['role'], 'WEEKLY_UPDATED')
        self.assertTrue(weekly['current_policy_ineligible'])
        self.assertTrue(weekly['monitoring_only'])
        self.assertIsNone(result['selected_champion'])
        self.assertFalse(result['scores_compared_or_ranked'])
        self.assertFalse(result['promotion_permitted'])

    def test_exact_aliases_do_not_become_independent_models(self):
        result = reporting_inventory(self.inventory(), [self.row(name) for name in ['market', 'frozen', 'weekly']])
        self.assertTrue(result['all_expected_rows_reported'])
        self.assertEqual(result['declared_exact_alias_groups'][0]['model_ids'], ['frozen', 'market', 'weekly'])
        self.assertEqual(result['distinct_complete_declared_prediction_identities'], 1)
        self.assertFalse(result['identity_bodies_authenticated_by_this_helper'])

    def test_equal_vectors_without_matching_cohort_or_reference_are_not_aliases(self):
        for field in ['cohort_sha256', 'reference_sha256', 'target']:
            rows = [self.row(), self.row('weekly')]
            rows[1][field] = 'd'*64 if field.endswith('sha256') else 'margin'
            self.assertEqual(reporting_inventory(self.inventory(), rows)['declared_exact_alias_groups'], [])

    def test_incomplete_alias_identity_stays_unknown(self):
        row = self.row(); del row['reference_sha256']
        result = reporting_inventory(self.inventory(), [row])
        self.assertEqual(result['distinct_complete_declared_prediction_identities'], 0)
        self.assertEqual(len(result['alias_identity_not_established']), 3)

    def test_declared_inventory_is_not_proof_of_storage_completeness(self):
        result = reporting_inventory(self.inventory(), [])
        self.assertFalse(result['full_private_storage_inventory_authenticated'])
        self.assertEqual(len(result['missing_report_rows']), 3)

    def test_unexpected_or_duplicate_identity_rejected(self):
        with self.assertRaises(ValueError): reporting_inventory(self.inventory(), [self.row('extra')])
        with self.assertRaises(ValueError): reporting_inventory(self.inventory(), [self.row(), self.row()])
        with self.assertRaises(ValueError): reporting_inventory(self.inventory()*2, [])

    def test_unknown_explicit_role_is_retained(self):
        declaration = self.inventory(); declaration[1].update(role='UNRESOLVED', training_policy='UNKNOWN')
        result = reporting_inventory(declaration, [self.row()])
        self.assertEqual(next(r for r in result['rows'] if r['model_id']=='frozen')['role'], 'UNRESOLVED')

    def test_missing_or_invalid_role_policy_rejected(self):
        for field, value in [('role', None), ('role', 'champion'), ('training_policy', 'fitted_today')]:
            declaration = self.inventory(); declaration[1][field] = value
            with self.subTest(field=field, value=value), self.assertRaises(ValueError): reporting_inventory(declaration, [])
        declaration = self.inventory(); declaration[0]['training_policy'] = 'PRIOR_SEASONS_ONLY'
        with self.assertRaises(ValueError): reporting_inventory(declaration, [])

    def test_invalid_losses_and_digests_rejected(self):
        for value in [True, float('nan'), float('inf'), -1]:
            with self.subTest(value=value), self.assertRaises(ValueError): reporting_inventory(self.inventory(), [self.row(loss=value)])
        row = self.row(); row['cohort_sha256'] = 'unverified'
        with self.assertRaises(ValueError): reporting_inventory(self.inventory(), [row])

    def test_invalid_identity_or_empty_inventory_rejected(self):
        with self.assertRaises(ValueError): reporting_inventory([], [])
        for field, value in [('model_id', ''), ('model_id', 1), ('season', True)]:
            declaration = self.inventory(); declaration[0][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError): reporting_inventory(declaration, [])
        with self.assertRaises(ValueError): reporting_inventory(self.inventory(), [], monitoring_season=True)

    def test_order_does_not_change_coverage(self):
        rows = [self.row(), self.row('weekly')]
        self.assertEqual(reporting_inventory(self.inventory(), rows), reporting_inventory(reversed(self.inventory()), reversed(rows)))

    def test_historical_policy_does_not_create_current_exclusion_or_promotion(self):
        inventory = self.inventory(); rows = [self.row('weekly')]
        for r in inventory + rows: r['season'] = 2025
        result = reporting_inventory(inventory, rows)
        self.assertFalse(any(r['current_policy_ineligible'] for r in result['rows']))
        self.assertFalse(result['selection_permitted'])
        self.assertEqual((result['new_fits'], result['new_forecast_issues'], result['actual_orders']), (0, 0, 0))


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

