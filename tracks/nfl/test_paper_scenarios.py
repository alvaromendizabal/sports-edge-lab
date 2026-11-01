"""Payoff, missing evidence and clock-boundary tests using invented inputs."""
from decimal import Decimal as D
import unittest

import paper_scenarios as ps


class PaperScenarioTests(unittest.TestCase):
    def test_american_prices_and_returned_stake(self):
        self.assertEqual(ps.decimal_odds(150), D("2.5"))
        self.assertEqual(ps.decimal_odds(-200), D("1.5"))
        result = ps.straight_bet(100, -200, ".7", tie_rule="refund")
        self.assertEqual(result["win_net_profit"], 50)
        self.assertEqual(result["win_gross_payout_before_fee"], 150)
        self.assertEqual(result["loss_net_profit"], -100)

    def test_nonfinite_boolean_and_malformed_prices_rejected(self):
        for value in (True, None, "NaN", "Infinity", 0, 50, -99, "bad"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                ps.decimal_odds(value)

    def test_pair_removes_margin_once(self):
        result = ps.no_vig_pair(-110, -110)
        self.assertEqual(result["first_conditional_non_tie"], D(".5"))
        self.assertEqual(result["second_conditional_non_tie"], D(".5"))
        self.assertGreater(result["quoted_probability_sum"], 1)

    def test_unknown_tie_mass_keeps_unconditional_fields_unknown(self):
        result = ps.straight_bet(100, 100, ".6", tie_rule="refund")
        self.assertEqual(result["conditional_non_tie_ev"], 20)
        self.assertIsNone(result["unconditional_ev"])
        self.assertIsNone(result["unconditional_win_probability"])

    def test_full_distribution_refund_and_loss_are_different(self):
        refund = ps.straight_bet(100, 100, ".6", tie_rule="refund", tie_probability=".1")
        loss = ps.straight_bet(100, 100, ".6", tie_rule="loss", tie_probability=".1")
        self.assertEqual(refund["unconditional_win_probability"], D(".54"))
        self.assertEqual(refund["unconditional_ev"], 18)
        self.assertEqual(loss["unconditional_ev"], 8)

    def test_fee_is_charged_exactly_once_in_every_state(self):
        result = ps.straight_bet(100, 100, ".6", tie_rule="refund", tie_probability=".1", fixed_fee=2)
        self.assertEqual(result["unconditional_ev"], 16)
        self.assertEqual(result["tie_net_profit"], -2)

    def test_invalid_probability_money_and_rule_rejected(self):
        for kwargs in ({"conditional_win":"1.1"}, {"tie_probability":"-.1"},
                       {"stake":-1}, {"fixed_fee":-1}, {"tie_rule":"unknown"}):
            args = dict(stake=100, american=-200, conditional_win=".7", tie_rule="refund")
            args.update(kwargs)
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                ps.straight_bet(**args)

    def test_zero_probability_and_certain_tie_endpoints(self):
        result = ps.straight_bet(100, 100, 0, tie_rule="refund", tie_probability=1)
        self.assertEqual(result["unconditional_ev"], 0)
        self.assertEqual(result["conditional_non_tie_ev"], -100)

    def test_unknown_budget_is_not_reset_to_four_hundred(self):
        result = ps.budget(400, None, 400)
        self.assertIsNone(result["remaining"])
        self.assertEqual(result["new_proposed_stake"], 0)

    def test_known_budget_uses_all_providers_week_total(self):
        self.assertEqual(ps.budget(400, 275, 200)["new_proposed_stake"], 125)
        self.assertEqual(ps.budget(400, 450, 100)["new_proposed_stake"], 0)

    def test_budget_rejects_negative_or_nonfinite_values(self):
        for args in ((-1, 0, 0), (400, -1, 10), (400, 0, -1), (400, "NaN", 10)):
            with self.subTest(args=args), self.assertRaises(ValueError):
                ps.budget(*args)

    def test_quote_time_cannot_backdate_actual_issue(self):
        result = ps.issue_classification(kickoff="2026-11-02T20:00:00Z",
            source_available="2026-11-01T10:00:00Z", acquired="2026-11-01T21:00:00Z",
            issued="2026-11-01T21:01:00Z")
        self.assertEqual(result, "LATE_MONITORING")

    def test_exact_cutoff_is_temporal_eligibility_only(self):
        result = ps.issue_classification(kickoff="2026-11-02T20:00:00Z",
            source_available="2026-11-01T18:00:00Z", acquired="2026-11-01T19:00:00Z",
            issued="2026-11-01T20:00:00Z")
        self.assertEqual(result, "T24_TIME_BOUNDARY_MET_ONLY")

    def test_post_kickoff_and_invalid_order(self):
        args = dict(kickoff="2026-11-02T20:00:00Z", source_available="2026-11-01T18:00:00Z",
                    acquired="2026-11-01T19:00:00Z", issued="2026-11-02T20:00:00Z")
        self.assertEqual(ps.issue_classification(**args), "POST_START_ILLUSTRATION")
        args["issued"] = "2026-11-01T18:30:00Z"
        with self.assertRaises(ValueError):
            ps.issue_classification(**args)
        with self.assertRaises(ValueError):
            ps.clock("2026-11-01T18:30:00")

    def test_scenario_dollars_need_no_independence_assumption(self):
        positions = [{"id":"a", "win_net_profit":50, "loss_net_profit":-100},
                     {"id":"b", "win_net_profit":150, "loss_net_profit":-100}]
        results = ps.win_loss_scenarios(positions)
        self.assertEqual([r["net_profit"] for r in results], [200, -50, 50, -200])
        self.assertTrue(all(r["scenario_probability"] is None for r in results))
        with self.assertRaises(ValueError):
            ps.win_loss_scenarios(positions + [positions[0]])

    def test_invented_demo_is_deterministic_and_not_an_allocation(self):
        self.assertEqual(ps.demo(), ps.demo())
        self.assertEqual(len(ps.demo()["win_loss_only_scenarios"]), 16)
        self.assertEqual(ps.demo()["actual_proposed_allocation"]["new_proposed_stake"], 0)
        self.assertEqual(ps.demo()["actual_orders"], 0)


if __name__ == "__main__":
    unittest.main()
