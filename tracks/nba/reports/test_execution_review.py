"""Public aggregate and display regressions; no source fetch, model fit or scoring."""
import copy
import hashlib
import json
from pathlib import Path
import re
import unittest

import build_execution_review as review

ROOT = Path(__file__).resolve().parent


class ExecutionReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((ROOT / "latest_execution_review.json").read_bytes())
        cls.page = (ROOT / "latest_research_outputs.html").read_text()

    def test_saved_scientific_exports_are_byte_exact(self):
        for name, expected in review.SOURCE_PINS.items():
            self.assertEqual(hashlib.sha256((ROOT / name).read_bytes()).hexdigest(), expected, name)
        self.assertEqual(review.digest(review.strip_review(self.page).encode()), review.BASE_DISPLAY_SHA256)

    def test_deterministic_status_is_the_only_html_change(self):
        self.assertTrue(review.validate(self.data))
        self.assertEqual(review.attach(self.page, self.data), self.page)
        self.assertEqual(self.page.count(review.BEGIN), 1)
        embedded = re.search(r'<script id="nba-execution-data" type="application/json">(.*?)</script>', self.page, re.S)
        self.assertIsNotNone(embedded)
        self.assertEqual(json.loads(embedded[1]), self.data)
        self.assertEqual(review.build(True)["status"], "PASS")

    def test_actual_failure_keeps_zero_fits_and_unchanged_issue_clock(self):
        run = self.data["latest_owner_execution"]
        self.assertEqual(run["new_confirmed_scientific_fits"], 0)
        self.assertEqual(run["exit_code"], 2)
        self.assertEqual(run["return"]["payload_members_authenticated"], run["return"]["members"] - 1)
        self.assertEqual(sum(self.data["science_preservation"]["completed_task_release_counts"].values()), 2328)
        old = json.loads((ROOT / "latest_research_outputs.json").read_bytes())
        self.assertEqual(old["latest_forecast_issue_at_utc"], self.data["science_preservation"]["latest_original_issue_at_utc"])
        self.assertEqual(old["newest_owner_execution"]["release"], "B077")

    def test_measured_cpu_is_not_reservation(self):
        obs = self.data["observed_runtime"]
        self.assertAlmostEqual(obs["time_weighted_cpu_cores"], obs["matched_process_cpu_seconds"] / obs["sample_elapsed_seconds"], places=10)
        self.assertEqual(obs["peak_reserved_cores"], 12)
        self.assertLess(obs["peak_cpu_cores"], 2)
        self.assertEqual(obs["peak_concurrent_scientific_fits"], 0)
        self.assertFalse(obs["twelve_core_scientific_utilization_proven"])
        altered = copy.deepcopy(self.data)
        altered["observed_runtime"]["twelve_core_scientific_utilization_proven"] = True
        with self.assertRaisesRegex(ValueError, "RESERVATION_IS_NOT_UTILIZATION"):
            review.validate(altered)

    def test_clock_progress_and_owner_execution_cannot_be_upgraded(self):
        for field, value, error in [
            ("latest_original_issue_at_utc", "2026-11-12T22:25:21Z", "ORIGINAL_ISSUE_CLOCK"),
            ("publication_new_fits", 12, "PUBLICATION_IS_NOT_SCIENCE"),
            ("publication_new_forecasts", 1, "PUBLICATION_IS_NOT_SCIENCE"),
        ]:
            altered = copy.deepcopy(self.data)
            altered["science_preservation"][field] = value
            with self.assertRaisesRegex(ValueError, error):
                review.validate(altered)
        altered = copy.deepcopy(self.data)
        altered["replacement_engineering"]["owner_execution_completed"] = True
        with self.assertRaisesRegex(ValueError, "NO_B079_OWNER_RUN"):
            review.validate(altered)
        altered = copy.deepcopy(self.data)
        altered["replacement_engineering"]["all_deployed_sports_retrofitted"] = True
        with self.assertRaisesRegex(ValueError, "UNVERIFIED_CROSS_SPORT_DEPLOYMENT"):
            review.validate(altered)

    def test_return_digest_and_missingness_cannot_be_relabelled(self):
        altered = copy.deepcopy(self.data)
        altered["latest_owner_execution"]["return"]["sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "RETURN_PIN"):
            review.validate(altered)
        science = self.data["science_preservation"]
        self.assertEqual(science["available_selected_role_cells"] + science["missing_selected_role_cells"], science["selected_role_opportunities"])
        self.assertEqual(science["all_target_horizon_cells"], 6 * science["observed_games"])

    def test_private_path_and_unreviewed_display_changes_are_rejected(self):
        altered = copy.deepcopy(self.data)
        altered["private_path"] = "/home/invented-private-owner/fixture"
        with self.assertRaisesRegex(ValueError, "PRIVATE_FIELD_OR_PATH"):
            review.validate(altered)
        with self.assertRaisesRegex(ValueError, "BASE_DISPLAY_CHANGED"):
            review.attach(self.page.replace("Season coverage, issued forecasts", "Changed research"), self.data)
        with self.assertRaisesRegex(ValueError, "DUPLICATE_OR_UNCLOSED"):
            review.strip_review(self.page + review.BEGIN)

    def test_shared_runtime_source_pin_matches_published_module(self):
        runtime = ROOT.parents[2] / "runtime" / "execution" / "sports_edge_live.py"
        expected = self.data["replacement_engineering"]["logging_verification"]
        self.assertEqual(expected["status"], "PASS")
        self.assertEqual(hashlib.sha256(runtime.read_bytes()).hexdigest(), expected["module_sha256"])
        self.assertFalse(expected["actual_NBA_fits"])
        package = self.data["replacement_engineering"]["package_verification"]
        self.assertEqual(package["status"], "PASS")
        self.assertEqual(package["packaged_tests"], 338)
        self.assertEqual(package["passed"], 338)
        self.assertEqual(package["failures"] + package["errors"] + package["skipped"] + package["module_errors"], 0)
        self.assertEqual(package["exact_package_sha256"], "6938ded9c716d012b2007f39a244b5655a6752bb4d557ffaa2a95e8525be6094")
        self.assertFalse(package["owner_execution_performed"])


if __name__ == "__main__":
    unittest.main()
