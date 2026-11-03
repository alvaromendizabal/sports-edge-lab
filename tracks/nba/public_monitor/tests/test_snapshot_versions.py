"""Negative cases for input drift without rewriting immutable issues."""
from copy import deepcopy
import unittest

from tracks.nba.public_monitor.snapshot_versions import (
    append_snapshots, input_version_drift, invented_snapshot, select_issued_view,
    validate_snapshot, verify_same_input_oracle, walkthrough,
)


class SnapshotVersions(unittest.TestCase):
    def setUp(self):
        self.old = invented_snapshot()
        self.new = invented_snapshot(snapshot_id="toy-new", feature_version="toy-source-b",
                                     kind="RECONSTRUCTION", generated_at="2035-11-02T12:00:00Z",
                                     prediction=0.62)

    def test_new_source_version_appends_without_rewriting_original(self):
        rows = append_snapshots([self.old], [self.new])
        self.assertEqual(len(rows), 2)
        self.assertEqual(self.old["prediction"], 0.7)
        self.assertEqual(select_issued_view(rows, policy="LAST_BEFORE_CUTOFF"), [self.old])

    def test_exact_duplicate_is_reuse_not_a_new_issue(self):
        self.assertEqual(len(append_snapshots([self.old], [deepcopy(self.old)])), 1)

    def test_changed_probability_under_same_identity_is_rejected(self):
        bad = dict(self.old, prediction=0.62)
        with self.assertRaisesRegex(ValueError, "immutable"):
            append_snapshots([self.old], [bad])

    def test_changed_feature_version_under_same_identity_is_rejected(self):
        bad = dict(self.old, feature_version="toy-source-b")
        with self.assertRaisesRegex(ValueError, "immutable"):
            append_snapshots([self.old], [bad])

    def test_output_cannot_mutate_the_original_input(self):
        rows = append_snapshots([self.old], [])
        rows[0]["prediction"] = 0.1
        self.assertEqual(self.old["prediction"], 0.7)

    def test_drift_is_a_diagnostic_not_a_retroactive_forecast(self):
        result = input_version_drift(self.old, self.new)
        self.assertAlmostEqual(result["prediction_delta"], -0.08)
        self.assertTrue(result["same_fitted_model"])
        self.assertFalse(result["same_feature_version"])
        self.assertFalse(result["overwrites_original"])
        self.assertEqual(result["prospective_credit"], 0)

    def test_wrong_event_cannot_be_reported_as_input_drift(self):
        with self.assertRaisesRegex(ValueError, "comparison question"):
            input_version_drift(self.old, dict(self.new, event="another-toy-game"))

    def test_post_game_reconstruction_cannot_be_relabelled_as_issued(self):
        with self.assertRaisesRegex(ValueError, "late reconstruction"):
            validate_snapshot(dict(self.new, kind="ISSUED"))

    def test_same_input_oracle_still_uses_strict_absolute_tolerance(self):
        close = dict(self.old, prediction=0.7 + 5e-13)
        far = dict(self.old, prediction=0.7 + 2e-12)
        self.assertTrue(verify_same_input_oracle(self.old, close))
        with self.assertRaisesRegex(ValueError, "tolerance"):
            verify_same_input_oracle(self.old, far)

    def test_different_source_versions_cannot_be_an_oracle_comparison(self):
        with self.assertRaisesRegex(ValueError, "same input version"):
            verify_same_input_oracle(self.old, self.new)

    def test_first_and_last_policies_select_only_pre_cutoff_issues(self):
        later = invented_snapshot(snapshot_id="toy-next-issue", feature_version="toy-source-c",
                                  generated_at="2035-11-01T19:00:00Z", prediction=0.68)
        rows = [self.old, self.new, later]
        self.assertEqual(select_issued_view(rows, policy="FIRST_BEFORE_CUTOFF"), [self.old])
        self.assertEqual(select_issued_view(rows, policy="LAST_BEFORE_CUTOFF"), [later])
        self.assertEqual(len(append_snapshots([], rows)), 3)

    def test_best_after_result_is_not_an_issue_policy(self):
        with self.assertRaisesRegex(ValueError, "time-only"):
            select_issued_view([self.old], policy="BEST_AFTER_RESULT")

    def test_same_clock_ambiguity_is_not_broken_by_model_score(self):
        duplicate_clock = dict(self.old, snapshot_id="different-id", prediction=0.6)
        with self.assertRaisesRegex(ValueError, "same-clock"):
            select_issued_view([self.old, duplicate_clock], policy="LAST_BEFORE_CUTOFF")

    def test_different_horizons_remain_separate_questions(self):
        h120 = dict(self.old, snapshot_id="toy-h120", cutoff_at="2035-11-01T18:00:00Z",
                    horizon_minutes=120)
        self.assertEqual(len(select_issued_view([self.old, h120], policy="LAST_BEFORE_CUTOFF")), 2)

    def test_all_three_objectives_preserve_distinct_rows(self):
        margin = invented_snapshot(target="margin", prediction=-5)
        total = invented_snapshot(target="total", prediction=220)
        self.assertEqual(len(append_snapshots([], [self.old, margin, total])), 3)

    def test_unknown_side_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "ordered side"):
            validate_snapshot(dict(self.old, side="away"))

    def test_unknown_target_cannot_match_a_missing_side(self):
        with self.assertRaisesRegex(ValueError, "objective"):
            validate_snapshot(dict(self.old, target="profit", side=None))

    def test_invalid_numeric_predictions_are_rejected(self):
        for p in (float("nan"), float("inf"), -0.1, 1.1, True):
            with self.subTest(p=p), self.assertRaises(ValueError):
                validate_snapshot(dict(self.old, prediction=p))

    def test_negative_total_is_rejected(self):
        with self.assertRaises(ValueError):
            validate_snapshot(invented_snapshot(target="total", prediction=-2))

    def test_unknown_fields_cannot_smuggle_an_unreviewed_outcome(self):
        with self.assertRaisesRegex(ValueError, "allowlisted"):
            validate_snapshot(dict(self.old, actual_home_win=1))

    def test_real_data_label_is_not_supported_by_public_fixture_module(self):
        with self.assertRaisesRegex(ValueError, "invented"):
            validate_snapshot(dict(self.old, data_kind="REAL"))

    def test_naive_clock_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "timezone"):
            validate_snapshot(dict(self.old, generated_at="2035-11-01T18:00:00"))

    def test_source_possessed_after_prediction_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "not possessed"):
            validate_snapshot(dict(self.old, source_possessed_at="2035-11-01T18:30:00Z"))

    def test_mismatched_cutoff_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "horizon and cutoff"):
            validate_snapshot(dict(self.old, horizon_minutes=120))

    def test_reconstruction_only_archive_has_no_issued_view(self):
        self.assertEqual(select_issued_view([self.new], policy="LAST_BEFORE_CUTOFF"), [])

    def test_walkthrough_is_zero_network_zero_real_fit(self):
        result = walkthrough()
        self.assertEqual(result["archived_versions"], 2)
        self.assertEqual(result["issued_view_rows"], 1)
        self.assertTrue(result["original_probability_unchanged"])
        self.assertEqual(result["new_real_fits"], 0)
        self.assertEqual(result["provider_requests"], 0)


if __name__ == "__main__":
    unittest.main()
