import copy
import unittest
from examples.basketball_contracts.build_basketball_dashboard import load_evidence, validate


class DashboardEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.data = load_evidence()

    def test_all_panels_and_sensitivities_present(self):
        self.assertEqual(validate(self.data)['scorecards'], 235)
        self.assertEqual(validate(self.data)['populated_panels'], 24)

    def test_market_cannot_join_full_cohort(self):
        row = next(r for r in self.data['models']['rows'] if r['recipe'] == 'MARKET_raw')
        row['cohort'] = 'full_basketball'
        with self.assertRaises(ValueError):
            validate(self.data)

    def test_current_season_cannot_be_relabelled_historical(self):
        row = next(r for r in self.data['models']['rows'] if r['year'] == 2027)
        row['monitoring_only'] = False
        with self.assertRaisesRegex(ValueError, 'monitoring boundary'):
            validate(self.data)

    def test_support_retention_cannot_be_inflated(self):
        row = next(r for r in self.data['overlap']['overlap_sensitivities'] if r['status'] == 'estimated_on_common_support' and r['uncovered_retention'] < 1)
        row['uncovered_retention'] = 1
        with self.assertRaisesRegex(ValueError, 'support retention'):
            validate(self.data)

    def test_both_block_sensitivities_required(self):
        row = next(r for r in self.data['overlap']['overlap_sensitivities'] if r['status'] == 'estimated_on_common_support')
        del row['intervals']['14']
        with self.assertRaisesRegex(ValueError, 'both calendar-block'):
            validate(self.data)

    def test_recovery_does_not_authorize_training(self):
        self.data['recovery']['resources']['additional_budget_authorized'] = True
        with self.assertRaisesRegex(ValueError, 'budget or reservation'):
            validate(self.data)

    def test_no_invented_settlement(self):
        self.data['recovery']['forecasts']['new_settlement_check'] = True
        with self.assertRaisesRegex(ValueError, 'inventing settlement'):
            validate(self.data)


if __name__ == '__main__':
    unittest.main()
