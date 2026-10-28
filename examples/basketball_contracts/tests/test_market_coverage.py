"""Guard scientific meaning as well as public aggregate arithmetic."""
import copy
import json
import unittest
from examples.basketball_contracts.evidence_market_coverage import EVIDENCE, validate


class CoverageEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(EVIDENCE.read_text())

    def test_accepted_aggregates_recompute(self):
        result = validate(self.data)
        self.assertEqual(result['standardizations'], 15)
        self.assertEqual(result['supported_strata'], 194)

    def test_forward_outcomes_rejected(self):
        self.data['historical_years'].append(2027)
        with self.assertRaisesRegex(ValueError, 'current outcomes'):
            validate(self.data)

    def test_nba_control_cannot_be_relabelled_combined(self):
        self.data['baseline_by_league']['nba'] = 'basketball_combined'
        with self.assertRaisesRegex(ValueError, 'league control identity'):
            validate(self.data)

    def test_pooled_gap_cannot_replace_same_year_gap(self):
        rows = self.data['year_coverage']
        get = lambda year, covered: next(r for r in rows if r['league'] == 'ncaam' and r['year'] == year and r['covered'] == covered)
        self.data['ncaam_2026_raw_gap']['covered_minus_uncovered_delta'] = get('pooled', 1)['delta_mean'] - get('pooled', 0)['delta_mean']
        with self.assertRaisesRegex(ValueError, 'same-year gap'):
            validate(self.data)

    def test_fabricated_prior_covered_panel_rejected(self):
        row = copy.deepcopy(next(r for r in self.data['year_coverage'] if r['league'] == 'ncaam' and r['year'] == 2026 and r['covered'] == 1))
        row['year'] = 2025
        self.data['year_coverage'].append(row)
        with self.assertRaisesRegex(ValueError, 'no men 2025'):
            validate(self.data)

    def test_support_loss_cannot_be_hidden(self):
        next(s for s in self.data['standardizations'] if s['spec'] == 'probability_month_game_type')['uncovered_retention'] = 1.0
        with self.assertRaisesRegex(ValueError, 'uncovered_retention'):
            validate(self.data)

    def test_equal_stratum_weights_cannot_replace_observed_weights(self):
        self.data['supported_strata'][0]['covered_weight'] = 0.2
        with self.assertRaisesRegex(ValueError, 'covered stratum weight'):
            validate(self.data)

    def test_unsupported_stratum_rejected(self):
        self.data['supported_strata'][0]['supported'] = False
        with self.assertRaisesRegex(ValueError, 'unsupported stratum'):
            validate(self.data)

    def test_open_reservation_cannot_be_counted_as_available_work(self):
        owner = self.data['owner_recovery']
        owner['conservative_available_work_seconds'] = owner['work_ceiling_seconds'] - owner['measured_active_floor_seconds']
        with self.assertRaisesRegex(ValueError, 'open reservation remainder'):
            validate(self.data)

    def test_recovery_does_not_change_modeling_status(self):
        self.data['owner_recovery']['latest_completed_real_modeling_release'] = 'B005'
        with self.assertRaisesRegex(ValueError, 'preserve modeling release status'):
            validate(self.data)

    def test_future_registry_is_not_authorization(self):
        self.data['next_research']['extra_training_authorized'] = True
        with self.assertRaisesRegex(ValueError, 'explicit budget approval'):
            validate(self.data)


if __name__ == '__main__':
    unittest.main()
