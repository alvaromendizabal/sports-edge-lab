"""Invented clocks exercise publication without weakening causal evaluation."""
import unittest
from market_clock import reference_clock, comparison_role


class MarketClockTests(unittest.TestCase):
    def reference(self, horizon="T2", quote="2026-10-01T17:58:00Z", acquired="2026-11-03T23:00:00Z"):
        return reference_clock(kickoff="2026-10-01T20:00:00Z", quote_at=quote,
                               acquired_at=acquired, horizon=horizon)

    def test_real_prior_observation_does_not_need_exact_minute(self):
        r = self.reference()
        self.assertEqual(r["quote_age_at_cutoff_seconds"], 120)
        self.assertTrue(r["acquired_after_kickoff"])
        self.assertFalse(r["execution_qualified"])

    def test_latest_pregame_is_publishable_after_two_hour_boundary(self):
        self.assertEqual(self.reference("LATEST_PREGAME", "2026-10-01T19:59:30Z")["quote_age_at_cutoff_seconds"], 30)

    def test_later_quote_cannot_enter_earlier_evaluation(self):
        with self.assertRaisesRegex(ValueError, "later than"):
            self.reference("T2", "2026-10-01T19:59:30Z")

    def test_live_quote_cannot_be_pregame(self):
        for quote in ("2026-10-01T20:00:00Z", "2026-10-01T20:00:01Z"):
            with self.subTest(quote=quote), self.assertRaisesRegex(ValueError, "precede kickoff"):
                self.reference("LATEST_PREGAME", quote)

    def test_current_snapshot_must_be_observed_while_upcoming(self):
        with self.assertRaisesRegex(ValueError, "in-game"):
            self.reference("LATEST_OBSERVED", "2026-10-01T19:30:00Z")
        self.assertFalse(self.reference("LATEST_OBSERVED", "2026-10-01T19:30:00Z", "2026-10-01T19:30:04Z")["execution_qualified"])

    def test_future_quote_is_impossible(self):
        with self.assertRaisesRegex(ValueError, "after its acquisition"):
            self.reference("T2", "2026-10-01T17:59:00Z", "2026-10-01T17:58:00Z")

    def test_timezone_is_required(self):
        with self.assertRaisesRegex(ValueError, "timezone"):
            self.reference(quote="2026-10-01T17:58:00")

    def test_later_market_reference_is_not_same_time_comparison(self):
        for h in ("T1", "LATEST_PREGAME", "LATEST_OBSERVED"):
            r = comparison_role(model_horizon="T2", quote_horizon=h, issue_class="RECONSTRUCTED_NOT_ORIGINAL_ISSUED")
            self.assertFalse(r["same_cutoff"])
            self.assertFalse(r["original_issue"])
            self.assertIn("information times differ", r["role"])

    def test_reconstruction_never_becomes_original_issue(self):
        r = comparison_role(model_horizon="T2", quote_horizon="T2", issue_class="RECONSTRUCTED_NOT_ORIGINAL_ISSUED")
        self.assertTrue(r["same_cutoff"])
        self.assertEqual(r["role"], "Same-cutoff reconstruction")
        self.assertFalse(r["original_issue"])

    def test_unknown_horizon_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "Unknown"):
            self.reference("CLOSING_INVENTED")


if __name__ == "__main__":
    unittest.main()
