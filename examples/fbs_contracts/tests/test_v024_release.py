from copy import deepcopy
import json
import unittest
from examples.fbs_contracts.public_release import release, validate_release


class PublicReleaseContractTests(unittest.TestCase):
    def setUp(self):
        self.data = release()

    def test_completed_research_does_not_claim_live_issues_or_profit(self):
        self.assertEqual(self.data["execution"]["fresh_completed_fits"], 723)
        self.assertEqual(self.data["exposure"]["prospective_forecasts_issued"], 0)
        self.assertFalse(self.data["exposure"]["live_feature_values_recomputed"])
        self.assertEqual(len(self.data["panels"]), 14)
        self.assertNotIn("profit", json.dumps(self.data))

    def test_negative_winner_result_is_preserved_in_both_seasons(self):
        for year in (2024, 2025):
            rows = {r["model"]: r for r in self.data["panels"] if r["season"] == year}
            self.assertGreater(rows["registered-challenger"]["metrics"]["winner_logloss"],
                               rows["previous-study"]["metrics"]["winner_logloss"])

    def test_missing_duplicate_and_unknown_panels_are_rejected(self):
        for mutate in (lambda d: d["panels"].pop(),
                       lambda d: d["panels"].append(deepcopy(d["panels"][0])),
                       lambda d: d["panels"][0].update(model="undocumented")):
            data = deepcopy(self.data)
            mutate(data)
            with self.assertRaises(ValueError):
                validate_release(data)

    def test_unknown_fields_are_rejected_at_every_public_boundary(self):
        locations = [(), ("exposure",), ("execution",), ("verification",), ("source_scope",), ("pairing",),
                     ("pairing", "seasons", 0),
                     ("models", 0), ("panels", 0), ("panels", 0, "metrics"), ("intervals", 0)]
        for path in locations:
            data = deepcopy(self.data)
            target = data
            for part in path:
                target = target[part]
            target["individual_predictions"] = []
            with self.subTest(path=path), self.assertRaisesRegex(ValueError, "public fields"):
                validate_release(data)

    def test_missing_metrics_are_not_rendered_as_zero(self):
        for value in (None, float("nan"), float("inf")):
            data = deepcopy(self.data)
            data["panels"][0]["metrics"]["winner_brier"] = value
            with self.assertRaises(ValueError):
                validate_release(data)

    def test_count_and_accuracy_drift_fail(self):
        for key, value in (("games", 917), ("games", 918.0)):
            data = deepcopy(self.data)
            data["panels"][0][key] = value
            with self.assertRaises(ValueError):
                validate_release(data)
        data = deepcopy(self.data)
        data["panels"][0]["metrics"]["winner_correct"] += 1
        with self.assertRaisesRegex(ValueError, "accuracy"):
            validate_release(data)

    def test_equal_denominator_cannot_mask_different_cohort_commitment(self):
        data = deepcopy(self.data)
        data["panels"][0]["cohort_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "cohort commitment"):
            validate_release(data)

    def test_source_market_scopes_close_without_double_counting_props(self):
        scope = self.data["source_scope"]
        self.assertEqual((scope["upcoming_strict_7_days"], scope["upcoming_extended_schedule"]), (63, 68))
        self.assertEqual(scope["quote_rows_all"], 2039 + 129)
        self.assertEqual(scope["quote_rows_game_markets"], 2006 + 33)
        data = deepcopy(self.data)
        data["source_scope"]["quote_rows_game_markets"] = 2168
        with self.assertRaises(ValueError):
            validate_release(data)

    def test_fit_receipt_and_interval_closure_fail_closed(self):
        for section, key, value in (("execution", "fresh_completed_fits", 724),
                                    ("verification", "completion_sha256", "missing"),
                                    ("verification", "completion_after_research", False),
                                    ("exposure", "prospective_forecasts_issued", 1)):
            data = deepcopy(self.data)
            data[section][key] = value
            with self.assertRaises(ValueError):
                validate_release(data)
        data = deepcopy(self.data)
        data["intervals"][0]["covered"] += 1
        with self.assertRaisesRegex(ValueError, "coverage"):
            validate_release(data)

    def test_private_paths_and_active_recipe_names_reject(self):
        for private in ("s3://private/source", "/workspace/private", "v024_full_private_recipe"):
            data = deepcopy(self.data)
            data["limitations"].append(private)
            with self.assertRaisesRegex(ValueError, "publication"):
                validate_release(data)


if __name__ == "__main__":
    unittest.main()
