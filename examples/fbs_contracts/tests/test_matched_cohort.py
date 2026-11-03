import dataclasses
import math
import unittest
from examples.fbs_contracts.matched_cohort import (
    Forecast, cohort_commitment, invented_comparison, pool_additive, score_matched,
)


class MatchedCohortTests(unittest.TestCase):
    def test_two_event_winner_scores_match_hand_calculation(self):
        result = score_matched(invented_comparison())
        reference, challenger = result
        self.assertAlmostEqual(reference["metrics"]["logloss"], -(math.log(.8) + math.log(.7)) / 2)
        self.assertAlmostEqual(reference["metrics"]["brier"], (.2 ** 2 + .3 ** 2) / 2)
        self.assertEqual(reference["metrics"]["correct"], 2)
        self.assertEqual(reference["cohort_sha256"], challenger["cohort_sha256"])

    def test_points_error_sign_and_rmse_match_hand_calculation(self):
        models = invented_comparison()
        for key, rows in models.items():
            models[key] = [dataclasses.replace(r, target="margin", actual=y, prediction=p)
                           for r, y, p in zip(rows, (7, -3), (10, -4))]
        score = score_matched(models)[0]["metrics"]
        self.assertEqual(score["mae"], 2)
        self.assertEqual(score["bias"], 1)
        self.assertAlmostEqual(score["rmse"], math.sqrt(5))

    def test_equal_count_different_identity_is_rejected(self):
        models = invented_comparison()
        models["invented-challenger"][0] = dataclasses.replace(models["invented-challenger"][0], event="different")
        with self.assertRaisesRegex(ValueError, "exact event identities"):
            score_matched(models)

    def test_intersection_and_duplicate_cohorts_are_rejected(self):
        for duplicate in (False, True):
            models = invented_comparison()
            models["invented-challenger"] = [models["invented-challenger"][0]] * (2 if duplicate else 1)
            with self.assertRaises(ValueError):
                score_matched(models)

    def test_paired_label_and_kickoff_drift_are_rejected(self):
        for changes in ({"actual": 0}, {"kickoff": "2024-10-01T19:00:00Z"}):
            models = invented_comparison()
            models["invented-challenger"][0] = dataclasses.replace(models["invented-challenger"][0], **changes)
            with self.assertRaisesRegex(ValueError, "paired labels"):
                score_matched(models)

    def test_future_naive_nonfinite_and_out_of_range_records_are_rejected(self):
        for changes in ({"issued_at": "2024-10-01T18:00:00Z"}, {"issued_at": "2024-10-01T17:00:00"},
                        {"prediction": float("nan")}, {"prediction": 1.01}, {"actual": .5}):
            models = invented_comparison()
            models["invented-challenger"][0] = dataclasses.replace(models["invented-challenger"][0], **changes)
            with self.assertRaises(ValueError):
                score_matched(models)

    def test_commitment_is_order_independent_and_label_sensitive(self):
        rows = invented_comparison()["invented-reference"]
        self.assertEqual(cohort_commitment(rows), cohort_commitment(list(reversed(rows))))
        changed = [dataclasses.replace(rows[0], actual=0), rows[1]]
        self.assertNotEqual(cohort_commitment(rows), cohort_commitment(changed))

    def test_unequal_sample_pooling_uses_sufficient_statistics(self):
        panels = [{"games": 1, "metrics": {"mae": 2, "rmse": 2}},
                  {"games": 3, "metrics": {"mae": 6, "rmse": 6}}]
        self.assertEqual(pool_additive(panels, "mae"), 5)
        self.assertAlmostEqual(pool_additive(panels, "rmse"), math.sqrt(28))
        self.assertNotEqual(pool_additive(panels, "rmse"), 5)

    def test_ece_mcc_and_missing_values_are_not_fabricated_from_averages(self):
        for metric in ("ece", "mcc", "not-recorded"):
            with self.assertRaises(ValueError):
                pool_additive([{"games": 2, "metrics": {metric: .1}}], metric)
        with self.assertRaises(ValueError):
            pool_additive([{"games": 2, "metrics": {"mae": None}}], "mae")

    def test_aggregate_output_contains_no_individual_prediction(self):
        for panel in score_matched(invented_comparison()):
            self.assertEqual(set(panel), {"model", "season", "target", "games", "cohort_sha256", "metrics"})


if __name__ == "__main__":
    unittest.main()
