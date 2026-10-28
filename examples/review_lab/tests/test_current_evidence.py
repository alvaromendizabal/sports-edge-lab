"""Reject invalid public evidence without exposing individual observations."""
import copy
import json
import unittest
from examples.review_lab.build_current_review import SOURCE, validate_evidence, render


class CurrentEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = SOURCE.read_bytes()
        cls.data = json.loads(cls.raw)

    def changed(self):
        return copy.deepcopy(self.data)

    def test_complete_export(self):
        self.assertEqual(validate_evidence(self.data), {"rows": 9756, "panels": 57, "venue_rows": 1586, "forward_selection": False})

    def test_forward_selection_is_rejected(self):
        data = self.changed(); data["selection_boundary"]["forward_model_selection"] = True
        with self.assertRaisesRegex(ValueError, "monitoring only"): validate_evidence(data)

    def test_forward_training_season_is_rejected(self):
        data = self.changed(); data["selection_boundary"]["historical_selection_seasons"].append(2026)
        with self.assertRaisesRegex(ValueError, "forward season"): validate_evidence(data)

    def test_historical_profit_is_not_invented(self):
        data = self.changed(); data["historical_profit"] = 42
        with self.assertRaisesRegex(ValueError, "profit evidence"): validate_evidence(data)

    def test_individual_forecast_field_is_rejected(self):
        data = self.changed(); data["rows"][0]["event_id"] = "private-example"
        with self.assertRaisesRegex(ValueError, "unexpected aggregate"): validate_evidence(data)

    def test_inconsistent_cohort_denominator_is_rejected(self):
        data = self.changed(); row = data["rows"][0]; row["games"] += 1; row["incorrect"] += 1
        with self.assertRaisesRegex(ValueError, "conflicting sample sizes"): validate_evidence(data)

    def test_forward_panel_cannot_be_relabelled_historical(self):
        data = self.changed(); next(row for row in data["rows"] if row["purpose"] == "FORWARD_MONITORING_ONLY")["purpose"] = "DEVELOPMENT_OR_HISTORICAL_EVALUATION"
        with self.assertRaisesRegex(ValueError, "monitoring boundary"): validate_evidence(data)

    def test_duplicate_model_is_rejected(self):
        data = self.changed(); data["rows"].append(data["rows"][0].copy())
        with self.assertRaisesRegex(ValueError, "duplicate model"): validate_evidence(data)

    def test_nan_is_rejected(self):
        data = self.changed(); data["rows"][0]["win_logloss"] = float("nan")
        with self.assertRaisesRegex(ValueError, "non-finite"): validate_evidence(data)

    def test_pick_counts_reconcile(self):
        data = self.changed(); data["rows"][0]["correct"] += 1
        with self.assertRaisesRegex(ValueError, "pick counts"): validate_evidence(data)

    def test_failed_gate_cannot_be_promoted(self):
        data = self.changed(); data["decisions"]["nfl"]["automatic_promotion"] = True
        with self.assertRaisesRegex(ValueError, "negative gate"): validate_evidence(data)

    def test_script_termination_in_label_is_safely_encoded(self):
        data = self.changed(); data["rows"][0]["label"] = "</script><script>alert(1)</script>"
        page, _ = render(data, self.raw)
        self.assertNotIn("</script><script>alert(1)", page)
        self.assertIn("\\u003c/script>", page)

    def test_root_observations_are_rejected(self):
        data = self.changed(); data["raw_observations"] = []
        with self.assertRaisesRegex(ValueError, "top-level field"): validate_evidence(data)

    def test_venue_event_detail_is_rejected(self):
        data = self.changed(); data["venue_rows"][0]["event_id"] = "private-example"
        with self.assertRaisesRegex(ValueError, "venue or comparison"): validate_evidence(data)

    def test_private_comparison_recipe_is_rejected(self):
        data = self.changed(); data["comparisons"][0]["fitted_weights"] = [1.0]
        with self.assertRaisesRegex(ValueError, "venue or comparison"): validate_evidence(data)

    def test_owner_summary_cannot_silently_drift(self):
        data = self.changed(); data["owner"]["new_fits"] = 999
        with self.assertRaisesRegex(ValueError, "owner snapshot"): validate_evidence(data)

    def test_historical_gate_cannot_be_relabelled_successful(self):
        data = self.changed(); data["decisions"]["nfl"]["historical_candidate_gate"] = True
        with self.assertRaisesRegex(ValueError, "negative gate"): validate_evidence(data)

    def test_deterministic_generation(self):
        self.assertEqual(render(self.data, self.raw), render(self.data, self.raw))


if __name__ == "__main__": unittest.main()
