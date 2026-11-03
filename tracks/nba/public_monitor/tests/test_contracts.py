"""Failure-oriented tests with invented data; no production model inference."""
import copy
import json
import math
from pathlib import Path
import unittest

from tracks.nba.public_monitor.contracts import (
    admit_forecast, eligible_update_results, frozen_parameters_unchanged,
    issue_union, match_products, merge_results, number, owner_accounting,
    paper_decision, score_issues, timestamp, walkthrough,
)

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures.json"


class TemporalContracts(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(FIXTURES.read_text())
        self.issue = copy.deepcopy(self.data["issues"][0])
        self.final = copy.deepcopy(self.data["previous_results"][0])

    def test_explicit_timezone_normalizes_without_host_assumptions(self):
        self.assertEqual(timestamp("2035-11-01T12:00:00-07:00"), timestamp("2035-11-01T19:00:00Z"))
        for value in ("2035-11-01T19:00:00", "not-a-clock", None):
            with self.subTest(value=value), self.assertRaises(ValueError):
                timestamp(value)

    def test_missing_and_nonfinite_observations_rejected(self):
        for value in (None, True, "0.5", math.inf, math.nan):
            with self.subTest(value=value), self.assertRaises(ValueError):
                number(value)

    def test_invented_issue_at_cutoff_is_accepted(self):
        self.assertEqual(admit_forecast(self.issue)["issue_timing"], "AT_DECLARED_CUTOFF")

    def test_early_issue_does_not_gain_true_horizon_identity(self):
        self.issue["issued_at"] = "2035-11-01T18:30:00Z"
        self.assertEqual(admit_forecast(self.issue)["issue_timing"], "EARLY_OUTLOOK")

    def test_post_cutoff_issue_rejected(self):
        self.issue["issued_at"] = "2035-11-01T19:00:01Z"
        with self.assertRaisesRegex(ValueError, "late issue"):
            admit_forecast(self.issue)

    def test_revised_source_not_possessed_before_issue_rejected(self):
        self.issue["source_possessed_at"] = "2035-11-01T19:01:00Z"
        with self.assertRaisesRegex(ValueError, "not possessed"):
            admit_forecast(self.issue)

    def test_publication_clock_cannot_be_later_than_possession(self):
        self.issue["source_published_at"] = "2035-11-01T18:06:00Z"
        with self.assertRaisesRegex(ValueError, "not possessed"):
            admit_forecast(self.issue)

    def test_horizon_mismatch_rejected(self):
        self.issue["horizon_minutes"] = 120
        with self.assertRaisesRegex(ValueError, "declared horizon"):
            admit_forecast(self.issue)

    def test_actual_data_never_enters_public_fixture_demo(self):
        self.issue["data_kind"] = "ACTUAL"
        with self.assertRaisesRegex(ValueError, "invented data only"):
            admit_forecast(self.issue)

    def test_probability_bounds_and_booleans_rejected(self):
        for value in (-0.01, 1.01, True, math.nan):
            row = dict(self.issue, probability=value)
            with self.subTest(value=value), self.assertRaises(ValueError):
                admit_forecast(row)

    def test_frozen_control_is_not_overwritten_by_a_rolling_update(self):
        self.assertTrue(frozen_parameters_unchanged({"toy": 1}, {"toy": 1}))
        with self.assertRaisesRegex(ValueError, "parameters changed"):
            frozen_parameters_unchanged({"toy": 1}, {"toy": 2})

    def test_update_uses_strictly_prior_observed_finals(self):
        self.assertEqual(eligible_update_results([self.final], self.final["possessed_at"]), [])
        self.assertEqual(len(eligible_update_results([self.final], "2035-11-01T23:05:01Z")), 1)

    def test_completed_game_without_final_possession_is_not_training_data(self):
        self.assertEqual(eligible_update_results([self.final], "2035-11-01T23:04:59Z"), [])


class ImmutableAccounting(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(FIXTURES.read_text())
        self.issue = copy.deepcopy(self.data["issues"][0])
        self.final = copy.deepcopy(self.data["previous_results"][0])

    def test_refresh_retains_older_loss_missing_from_fresh_response(self):
        rows = merge_results(self.data["previous_results"], self.data["fresh_results"])
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["home_win"], 0)

    def test_noop_result_refresh_adds_no_outcomes(self):
        self.assertEqual(merge_results([self.final], [self.final]), [self.final])

    def test_later_redownload_does_not_rewrite_actual_first_possession(self):
        later = dict(self.final, possessed_at="2035-11-02T00:00:00Z")
        self.assertEqual(merge_results([self.final], [later]), [self.final])

    def test_conflicting_final_is_not_silently_selected(self):
        with self.assertRaisesRegex(ValueError, "versioned correction"):
            merge_results([self.final], [dict(self.final, home_win=1)])

    def test_incomplete_final_cannot_erase_prior_final(self):
        with self.assertRaisesRegex(ValueError, "official final"):
            merge_results([self.final], [dict(self.final, official_final=False)])

    def test_unchanged_issue_reuse_does_not_add_a_new_issue(self):
        self.assertEqual(issue_union([self.issue], [self.issue]), [self.issue])

    def test_same_issue_id_with_changed_probability_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "immutable issue"):
            issue_union([self.issue], [dict(self.issue, probability=0.6)])

    def test_new_issue_version_is_preserved_but_not_silently_rescored(self):
        version = dict(self.issue, issue_id="invented-revision-2", probability=0.6)
        union = issue_union([self.issue], [version])
        self.assertEqual(len(union), 2)
        with self.assertRaisesRegex(ValueError, "predeclared issue policy"):
            score_issues(union, [self.final], "2035-11-03T00:00:00Z")

    def test_incomplete_owner_preserves_completed_work_without_success(self):
        result = owner_accounting(3, ["a", "b", "c"], 2, False)
        self.assertEqual(result["completed"], 3)
        self.assertEqual(result["owner_status"], "FAILED_OR_PARTIAL")
        self.assertEqual(result["new_credit_on_reuse"], 0)

    def test_zero_exit_does_not_substitute_for_publication_verification(self):
        self.assertEqual(owner_accounting(1, ["a"], 0, False)["owner_status"], "FAILED_OR_PARTIAL")

    def test_unknown_exit_is_not_success(self):
        self.assertEqual(owner_accounting(1, ["a"], None, True)["owner_status"], "FAILED_OR_PARTIAL")

    def test_completed_owner_requires_all_work_and_readback(self):
        self.assertEqual(owner_accounting(1, ["a"], 0, True)["owner_status"], "COMPLETED")

    def test_duplicate_work_cannot_inflate_a_completion_count(self):
        with self.assertRaisesRegex(ValueError, "duplicate"):
            owner_accounting(2, ["a", "a"], 0, True)


class EvaluationContracts(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(FIXTURES.read_text())
        self.issue = self.data["issues"][0]
        self.final = self.data["previous_results"][0]
        self.product = {"event": "invented-01", "side": "home", "target": "winner", "line": None,
                        "horizon_minutes": 60, "settlement": "includes-overtime", "product": "binary-winner",
                        "cutoff_at": "2035-11-01T19:00:00Z"}
        self.quote = dict(self.product, quoted_at="2035-11-01T18:58:00Z", possessed_at="2035-11-01T18:59:00Z")

    def test_known_hand_calculated_loss_is_preserved(self):
        metrics = score_issues([self.issue], [self.final], "2035-11-02T00:00:00Z")["metrics"][0]
        self.assertEqual(metrics["correct"], 0)
        self.assertAlmostEqual(metrics["brier"], 0.49)
        self.assertAlmostEqual(metrics["log_loss"], -math.log(0.3))

    def test_no_result_returns_no_score_not_zero_loss(self):
        self.assertEqual(score_issues([self.issue], [], "2035-11-02T00:00:00Z")["metrics"], [])

    def test_result_not_yet_possessed_is_not_scored(self):
        self.assertEqual(score_issues([self.issue], [self.final], "2035-11-01T23:04:00Z")["metrics"], [])

    def test_outcome_cannot_be_known_before_tip(self):
        result = dict(self.final, published_at="2035-11-01T19:01:00Z")
        with self.assertRaisesRegex(ValueError, "predate"):
            score_issues([self.issue], [result], "2035-11-02T00:00:00Z")

    def test_equivalent_product_and_pregame_clocks_match(self):
        self.assertTrue(match_products(self.product, self.quote))

    def test_each_identity_dimension_must_match(self):
        changes = {"event": "invented-02", "side": "away", "target": "total", "line": 220.5,
                   "horizon_minutes": 120, "settlement": "regulation-only", "product": "player-prop"}
        for key, value in changes.items():
            with self.subTest(key=key):
                self.assertFalse(match_products(self.product, dict(self.quote, **{key: value})))

    def test_quote_published_before_cutoff_but_downloaded_later_does_not_match(self):
        self.assertFalse(match_products(self.product, dict(self.quote, possessed_at="2035-11-01T19:00:01Z")))

    def test_impossible_quote_clock_order_rejected(self):
        with self.assertRaisesRegex(ValueError, "impossible quote"):
            match_products(self.product, dict(self.quote, quoted_at="2035-11-01T19:00:00Z"))

    def test_unknown_pnl_is_not_reported_as_zero(self):
        result = paper_decision(probability=0.9)
        self.assertEqual(result["decision"], "NO BET")
        self.assertIsNone(result["historical_pnl"])
        self.assertIsNone(result["unit_expected_value"])
        self.assertEqual(result["allocation"], 0)

    def test_invented_expected_value_is_arithmetic_not_a_stake(self):
        result = paper_decision(probability=0.6, decimal_odds=2, fees=0.02,
                                executable_depth=1, settlement_verified=True)
        self.assertAlmostEqual(result["unit_expected_value"], 0.18)
        self.assertEqual(result["allocation"], 0)
        self.assertIsNone(result["historical_pnl"])

    def test_zero_depth_prevents_executable_ev(self):
        result = paper_decision(probability=0.9, decimal_odds=2, fees=0,
                                executable_depth=0, settlement_verified=True)
        self.assertEqual(result["decision"], "NO BET")
        self.assertIsNone(result["unit_expected_value"])

    def test_walkthrough_distinguishes_toy_tracks_and_retains_loss(self):
        result = walkthrough()
        self.assertEqual(result["data_kind"], "INVENTED")
        self.assertEqual(result["real_fits"], 0)
        self.assertEqual(result["network_requests"], 0)
        self.assertTrue(result["loss_preserved_after_refresh"])
        self.assertEqual(result["qualified_union_finals"], 2)
        self.assertEqual(result["eligible_update_outcomes"], 1)
        self.assertEqual({r["track"] for r in result["toy_scores"]["metrics"]}, {"frozen", "rolling"})


if __name__ == "__main__":
    unittest.main()
