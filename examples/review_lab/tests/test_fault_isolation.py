import unittest
from examples.review_lab.fault_isolation import pipeline, reference_slate, walkthrough, clock


class FaultIsolationTests(unittest.TestCase):
    def setUp(self):
        self.policy = {"id": "invented-frozen-market-v1", "type": "MARKET_REFERENCE", "historical_qualification": "NO_LEARNED_QUALIFIER"}
        self.rows = [{"game": "Invented Amber vs Indigo", "market_probability": 0.57, "observed_at": "2030-01-01T12:00:00Z", "kickoff": "2030-01-01T15:00:00Z"}]
        self.now = "2030-01-01T12:05:00Z"

    def serve(self):
        return reference_slate(self.rows, decision_time=self.now, policy=self.policy)

    def test_research_failure_still_serves(self):
        r = walkthrough()
        self.assertEqual(r["research"]["status"], "FAILED")
        self.assertEqual(r["serving"]["status"], "SERVED")
        self.assertEqual(len(r["serving"]["forecasts"]), 2)

    def test_research_completion_cannot_change_serving(self):
        self.assertEqual(walkthrough()["serving"], walkthrough("research_complete")["serving"])

    def test_stale_reference_fails_independently(self):
        r = walkthrough("stale_reference")
        self.assertEqual(r["research"]["status"], "FAILED")
        self.assertEqual(r["serving"]["status"], "BLOCKED")
        self.assertEqual(r["serving"]["forecasts"], [])

    def test_future_reference_fails(self):
        self.assertEqual(walkthrough("future_reference")["serving"]["status"], "BLOCKED")

    def test_all_scenarios_are_unfunded_invented_not_orders(self):
        for name in ("research_failure", "research_complete", "stale_reference", "future_reference"):
            x = walkthrough(name)
            self.assertEqual(x["evidence"], "INVENTED_OFFLINE_DEMONSTRATION")
            self.assertEqual(x["execution"]["status"], "NOT_ELIGIBLE")
            self.assertEqual(x["execution"]["actual_orders"], 0)
            self.assertEqual(x["execution"]["paper_stake"], 0)
            self.assertIsNone(x["execution"]["profit"])
            self.assertEqual(x["serving"]["fresh_real_forecasts"], 0)

    def test_outcomes_rejected(self):
        self.rows[0]["outcome"] = 1
        with self.assertRaises(ValueError): self.serve()

    def test_started_game_rejected(self):
        self.rows[0]["kickoff"] = self.now
        with self.assertRaises(ValueError): self.serve()

    def test_invalid_probabilities_rejected(self):
        for p in (0, 1, -0.1, 1.1, True, float("nan"), float("inf"), "0.57"):
            self.rows[0]["market_probability"] = p
            with self.assertRaises(ValueError): self.serve()

    def test_bad_reference_does_not_erase_research_receipt(self):
        self.rows[0]["market_probability"] = float("nan")
        result = pipeline(lambda: {"status": "COMPLETED"}, self.rows, decision_time=self.now, policy=self.policy)
        self.assertEqual(result["research"]["status"], "COMPLETED")
        self.assertEqual(result["serving"]["status"], "BLOCKED")
        self.assertEqual(result["execution"]["status"], "NOT_ELIGIBLE")

    def test_duplicate_game_rejected(self):
        self.rows *= 2
        with self.assertRaises(ValueError): self.serve()

    def test_empty_slate_rejected(self):
        self.rows = []
        with self.assertRaises(ValueError): self.serve()

    def test_unknown_policy_rejected(self):
        self.policy["type"] = "NEW_RESEARCH_WINNER"
        with self.assertRaises(ValueError): self.serve()

    def test_utc_required(self):
        for value in ("2030-01-01T12:00:00", "2030-01-01T12:00:00+02:00", None):
            with self.assertRaises(ValueError): clock(value)

    def test_research_cannot_mutate_reference_inputs(self):
        expected = self.serve()
        def corrupt():
            self.rows[0]["market_probability"] = 0.9
            self.policy["type"] = "NEW_RESEARCH_WINNER"
            raise ArithmeticError("private exception text should never be exported")
        result = pipeline(corrupt, self.rows, decision_time=self.now, policy=self.policy)
        self.assertEqual(result["serving"], expected)
        self.assertNotIn("private exception", str(result))

    def test_incomplete_research_receipt_is_failure(self):
        result = pipeline(lambda: {"status": "PENDING"}, self.rows, decision_time=self.now, policy=self.policy)
        self.assertEqual(result["research"]["status"], "FAILED")
        self.assertEqual(result["serving"]["status"], "SERVED")

    def test_research_system_exit_not_swallowed(self):
        def stop(): raise SystemExit(1)
        with self.assertRaises(SystemExit): pipeline(stop, self.rows, decision_time=self.now, policy=self.policy)

    def test_unknown_scenario(self):
        with self.assertRaises(ValueError): walkthrough("unspecified")
