"""Behavioral checks for generic finite score laws; all data are invented."""
import math
import unittest

from examples.review_lab.distribution import DiscreteScoreLaw, demonstration, logsumexp, mixture


class DistributionTests(unittest.TestCase):
    def law(self):
        return DiscreteScoreLaw.from_log_weights([(2, 1, math.log(.6)), (1, 2, math.log(.3)), (1, 1, math.log(.1))])

    def test_normalizes_arbitrary_log_weights(self):
        law = DiscreteScoreLaw.from_log_weights([(0, 0, 1000.), (1, 0, 1001.)])
        self.assertAlmostEqual(sum(law.outcome_probabilities().values()), 1)

    def test_joint_score_is_probability_mass_not_density(self):
        self.assertAlmostEqual(self.law().joint_nll(2, 1), -math.log(.6))

    def test_missing_outcome_is_infinite_loss(self):
        self.assertEqual(self.law().joint_nll(9, 9), math.inf)

    def test_conditional_win_removes_ties(self):
        self.assertAlmostEqual(math.exp(self.law().conditional_win_logs()[0]), 2/3)
        self.assertAlmostEqual(self.law().outcome_probabilities()['home'], .6)

    def test_tie_only_law_rejects_binary_conditioning(self):
        law = DiscreteScoreLaw.from_log_weights([(1, 1, 0.)])
        with self.assertRaisesRegex(ValueError, 'zero mass'): law.conditional_win_logs()

    def test_impossible_win_has_infinite_binary_loss(self):
        law = DiscreteScoreLaw.from_log_weights([(0, 1, 0.)])
        self.assertEqual(law.conditional_win_nll(True), math.inf)

    def test_tiny_mass_is_not_clipped_before_scoring(self):
        law = DiscreteScoreLaw.from_log_weights([(1, 0, 0.), (0, 1, -1000.)])
        self.assertEqual(law.outcome_probabilities()['away'], 0.)
        self.assertEqual(law.conditional_win_nll(False), 1000.)

    def test_mixture_keeps_tiny_mass_for_likelihood(self):
        law = DiscreteScoreLaw.from_log_weights([(1, 0, 0.), (0, 1, -1000.)])
        self.assertAlmostEqual(mixture([law, law], [.5, .5]).conditional_win_nll(False), 1000.)

    def test_mixture_union_support(self):
        a = DiscreteScoreLaw.from_log_weights([(1, 0, 0.)]); b = DiscreteScoreLaw.from_log_weights([(0, 1, 0.)])
        self.assertAlmostEqual(mixture([a, b], [.25, .75]).outcome_probabilities()['home'], .25)

    def test_conditioning_is_after_mixing(self):
        result = demonstration()
        self.assertAlmostEqual(result['mixture_then_condition_home'], .275/.7)
        self.assertNotAlmostEqual(result['mixture_then_condition_home'], result['incorrect_average_of_conditional_home'])

    def test_contract_expected_payout_includes_tie_rule(self):
        self.assertAlmostEqual(self.law().expected_settlement(home_payout=1, away_payout=0, tie_payout=.5), .65)

    def test_contract_payout_rejects_outside_unit_interval(self):
        with self.assertRaises(ValueError): self.law().expected_settlement(home_payout=2, away_payout=0, tie_payout=0)

    def test_crps_point_mass_equals_absolute_error(self):
        law = DiscreteScoreLaw.from_log_weights([(4, 2, 0.)])
        self.assertEqual(law.marginal_crps(0, 1), 3)
        self.assertEqual(law.marginal_crps(1, 2), 0)

    def test_crps_known_two_point_law(self):
        law = DiscreteScoreLaw.from_log_weights([(0, 0, 0.), (2, 0, 0.)])
        self.assertAlmostEqual(law.marginal_crps(0, 1), .5)

    def test_law_is_immutable_after_creation(self):
        source = {(1, 0): 0.}; law = DiscreteScoreLaw(source); source[(1, 0)] = -2.
        self.assertEqual(law.log_mass[(1, 0)], 0.)
        with self.assertRaises(TypeError): law.log_mass[(1, 0)] = -2.

    def test_duplicate_pair_rejected(self):
        with self.assertRaisesRegex(ValueError, 'duplicate'): DiscreteScoreLaw.from_log_weights([(0, 0, 0.), (0, 0, 0.)])

    def test_empty_support_rejected(self):
        with self.assertRaisesRegex(ValueError, 'empty'): DiscreteScoreLaw.from_log_weights([])

    def test_unnormalized_law_rejected(self):
        with self.assertRaisesRegex(ValueError, 'normalized'): DiscreteScoreLaw({(0, 0): .1})

    def test_noninteger_support_rejected(self):
        with self.assertRaisesRegex(ValueError, 'integer'): DiscreteScoreLaw({(.5, 0): 0.})

    def test_invalid_mixture_weights_rejected(self):
        for weights in ([1.,1.], [-.5,1.5], [float('nan'), 0.], [.5]):
            with self.assertRaises(ValueError): mixture([self.law(),self.law()], weights)

    def test_logsumexp_empty_and_nonfinite(self):
        self.assertEqual(logsumexp([]), -math.inf)
        self.assertEqual(logsumexp([-math.inf, -math.inf]), -math.inf)
        for value in (math.inf, math.nan):
            with self.assertRaises(ValueError): logsumexp([value])

    def test_demo_does_not_claim_private_model_reproduction(self):
        self.assertFalse(demonstration()['real_football_performance'])
        self.assertFalse(demonstration()['purchase_price_and_fees_included'])


if __name__ == '__main__': unittest.main()
