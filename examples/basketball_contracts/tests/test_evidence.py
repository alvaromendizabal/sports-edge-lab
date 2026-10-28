"""Integrity checks on aggregate evidence; no private data or estimator needed."""
from copy import deepcopy
import unittest

from examples.basketball_contracts.evidence import load_evidence, selected_season_rows, validate_evidence


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.value = load_evidence()

    def test_export_separates_owner_work_from_inspection(self):
        self.assertEqual(self.value["owner_execution"]["completed_native_fit_units"], 60)
        self.assertEqual(self.value["owner_execution"]["cumulative_basketball_native_units"], 232)
        self.assertEqual(len(selected_season_rows(self.value)), 6)
        self.assertEqual(len(selected_season_rows(self.value, 1440)), 6)

    def test_current_season_cannot_select_models(self):
        self.value["evaluation"]["current_outcomes_used_for_selection_or_fitting"] = True
        with self.assertRaisesRegex(ValueError, "protected monitoring"):
            validate_evidence(self.value)

    def test_fit_components_must_reconcile(self):
        self.value["owner_execution"]["fit_units_by_kind"]["classifier"] += 1
        with self.assertRaisesRegex(ValueError, "fit accounting"):
            validate_evidence(self.value)

    def test_different_event_cohort_cannot_be_compared(self):
        self.value["tracks"][0]["season_scorecards"][0]["event_cohort_sha256"] = "changed"
        with self.assertRaisesRegex(ValueError, "cohort identity"):
            validate_evidence(self.value)

    def test_accuracy_and_pick_counts_must_agree(self):
        self.value["tracks"][0]["season_scorecards"][0]["correct"] += 1
        with self.assertRaisesRegex(ValueError, "outcome accounting"):
            validate_evidence(self.value)

    def test_nonfinite_metric_rejected(self):
        self.value["tracks"][0]["season_scorecards"][0]["log_loss"] = float("nan")
        with self.assertRaisesRegex(ValueError, "nonfinite"):
            validate_evidence(self.value)

    def test_early_outlook_is_not_a_lock_forecast(self):
        self.value["owner_execution"]["forecast_kind"] = "T60_lock_forecast"
        with self.assertRaisesRegex(ValueError, "early outlooks"):
            validate_evidence(self.value)

    def test_research_does_not_create_profit(self):
        self.value["owner_execution"]["profit"] = 0.0
        with self.assertRaisesRegex(ValueError, "invented execution or profit"):
            validate_evidence(self.value)

    def test_private_export_boundary_rejected(self):
        self.value["publication_boundary"]["individual_predictions_included"] = True
        with self.assertRaisesRegex(ValueError, "private records"):
            validate_evidence(self.value)

    def test_scopes_cannot_be_pooled_or_duplicated(self):
        self.value["tracks"].append(deepcopy(self.value["tracks"][0]))
        with self.assertRaisesRegex(ValueError, "league and horizon"):
            validate_evidence(self.value)

    def test_predecessor_aliases_do_not_add_unique_fits(self):
        self.value["owner_execution"]["cumulative_basketball_native_units"] += 156
        with self.assertRaisesRegex(ValueError, "predecessor reuse"):
            validate_evidence(self.value)

    def test_reuse_count_must_match_manifests(self):
        self.value["owner_execution"]["imported_predecessor_units"] -= 1
        with self.assertRaisesRegex(ValueError, "predecessor reuse"):
            validate_evidence(self.value)

    def test_cumulative_budget_cannot_reset(self):
        self.value["owner_execution"]["remaining_work_seconds_at_return_snapshot"] = 4500
        with self.assertRaisesRegex(ValueError, "cumulative budget"):
            validate_evidence(self.value)

    def test_calibration_chart_cannot_omit_scored_games(self):
        self.value["tracks"][0]["season_scorecards"][0]["calibration_bins"][0]["n"] += 1
        with self.assertRaisesRegex(ValueError, "calibration bins"):
            validate_evidence(self.value)

    def test_calibration_chart_must_match_ece(self):
        self.value["tracks"][0]["season_scorecards"][0]["calibration_bins"][0]["observed_rate"] += .1
        with self.assertRaisesRegex(ValueError, "calibration plot"):
            validate_evidence(self.value)

    def test_pooled_metrics_must_equal_season_weighted_results(self):
        self.value["tracks"][0]["selections"][0]["leaderboard"][0]["log_loss"] += .01
        with self.assertRaisesRegex(ValueError, "pooled leaderboard"):
            validate_evidence(self.value)

    def test_paired_intervals_cannot_use_current_season(self):
        self.value["tracks"][0]["paired_control_comparisons"][0]["season"] = 2027
        with self.assertRaisesRegex(ValueError, "protected monitoring"):
            validate_evidence(self.value)

    def test_prospective_pending_rows_must_reconcile(self):
        self.value["owner_execution"]["prior_pending_rows"] -= 1
        with self.assertRaisesRegex(ValueError, "pending-row"):
            validate_evidence(self.value)


if __name__ == "__main__":
    unittest.main()
