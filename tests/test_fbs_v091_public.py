"""Evidence-contradiction and publication checks for the compact FBS review."""
import copy
import importlib.util
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("fbs_v091_review", ROOT / "examples/fbs_contracts/v091/build_review.py")
REVIEW = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(REVIEW)
DATA = json.loads((ROOT / "docs/fbs/v091/data/status.json").read_text())


class ExecutionReview(unittest.TestCase):
    def rejects(self, section, key, value):
        modified = copy.deepcopy(DATA)
        modified[section][key] = value
        with self.assertRaises(ValueError):
            REVIEW.render(modified)

    def test_saved_attempt_and_prior_science_stay_separate(self):
        self.assertEqual(DATA["latest_attempt"]["recorded_base_fits"], 0)
        self.assertEqual(DATA["latest_attempt"]["operational_failures"], 1)
        self.assertFalse(DATA["latest_attempt"]["fit_count_complete"])
        self.assertEqual(DATA["retained_science"]["base_fits"], 90)
        self.assertEqual(DATA["retained_science"]["policy_target_identities"], 397)
        self.assertEqual([x["games"] for x in DATA["retained_science"]["cohorts"]], [919, 934, 752])

    def test_saved_page_matches_deterministic_complete_input(self):
        expected = REVIEW.render(DATA)
        self.assertEqual(expected, REVIEW.render(copy.deepcopy(DATA)))
        self.assertEqual(expected, (ROOT / "docs/fbs/v091/index.html").read_bytes())
        embedded = re.search(rb'<script id="report-data" type="application/json">(.*?)</script>', expected, re.S).group(1)
        self.assertEqual(json.loads(embedded), DATA)

    def test_does_not_duplicate_candidate_or_game_arrays(self):
        self.assertNotIn("models", DATA)
        self.assertNotIn("games", DATA)
        self.assertLess(len(REVIEW.render(DATA)), 100_000)

    def test_failed_attempt_cannot_become_success(self):
        self.rejects("latest_attempt", "successful", 1)

    def test_cannot_claim_model_stage_completion_without_registration(self):
        self.rejects("latest_attempt", "completed_model_jobs", 1)

    def test_no_invented_optimizer_acceptance(self):
        self.rejects("latest_attempt", "optimizer_occupancy_accepted", True)
        self.rejects("prepared", "measured_optimizer_cores", 24)

    def test_preparation_cannot_claim_new_science(self):
        for field in ("owner_executions", "new_scientific_fits", "provider_retrievals"):
            self.rejects("prepared", field, 1)

    def test_selection_cannot_use_test_outcomes(self):
        self.rejects("selection", "test_used_for_selection", True)
        self.rejects("selection", "season_training_weights_used", True)
        self.rejects("selection", "previous_test_exposure", False)

    def test_report_does_not_claim_deployment_or_issue(self):
        self.rejects("publication", "website_deployed", True)
        self.rejects("publication", "new_numerical_forecasts_published", True)

    def test_private_and_unknown_fields_are_rejected(self):
        self.rejects("latest_attempt", "summary", "Internal s3://private-owner/data")
        self.rejects("latest_attempt", "summary", "/home/sagemaker-user/private")
        modified = copy.deepcopy(DATA)
        modified["unissued_forecasts"] = [{"home_probability": .9}]
        with self.assertRaises(ValueError):
            REVIEW.render(modified)

    def test_invalid_archive_part_capacity_fails(self):
        self.rejects("storage", "latest_return_parts", 1)
        self.rejects("storage", "part_max_bytes", 1024)

    def test_cost_guard_cannot_be_waived(self):
        self.rejects("prepared", "unlimited_wall_waives_cost_guard", True)
        self.rejects("latest_attempt", "cost_is_invoice", True)

    def test_verify_before_reuse_and_pointer_commit_required(self):
        self.rejects("recovery", "verify_dependencies_before_reuse", False)
        self.rejects("recovery", "actual_pointer_only_after_integrity", False)
        self.rejects("recovery", "aggregate_science_cap", 536870912)

    def test_prepared_branch_and_phase_counts_remain_consistent(self):
        self.rejects("prepared", "validation_jobs", 623)
        modified = copy.deepcopy(DATA)
        modified["prepared"]["branches"][0]["jobs"] = 1
        with self.assertRaises(ValueError):
            REVIEW.render(modified)

    def test_html_embedded_data_cannot_break_out(self):
        modified = copy.deepcopy(DATA)
        modified["latest_attempt"]["summary"] = "</script><img src=x onerror=alert(1)>"
        body = REVIEW.render(modified)
        self.assertNotIn(b"</script><img", body)
        embedded = re.search(rb'<script id="report-data" type="application/json">(.*?)</script>', body, re.S).group(1)
        self.assertEqual(json.loads(embedded)["latest_attempt"]["summary"], modified["latest_attempt"]["summary"])

    def test_nonfinite_or_negative_costs_fail(self):
        for value in (float("nan"), float("inf"), -1):
            self.rejects("latest_attempt", "estimated_full_host_cost_usd", value)

    def test_prepared_completion_requires_measured_sizes(self):
        modified = copy.deepcopy(DATA)
        modified["prepared"].update(status="PREPARED_NOT_EXECUTED", executable_bytes=None, prepared_report_zip_bytes=None)
        with self.assertRaises(ValueError):
            REVIEW.render(modified)

    def test_reported_incident_cannot_invent_an_operator_exit_or_lifetime_tally(self):
        self.rejects("launch_incident", "operator_exit_code", 2)
        self.rejects("launch_incident", "lifetime_failure_total", 91)

    def test_isolated_reproduction_cannot_become_owner_science(self):
        for field in ("isolated_child_launches", "isolated_model_fits", "isolated_aws_calls"):
            self.rejects("launch_incident", field, 1)
        self.rejects("launch_incident", "new_reported_successes", 1)

    def test_new_incident_does_not_rewrite_last_verified_return(self):
        self.assertEqual(DATA["launch_incident"]["release"], "V091")
        self.assertEqual(DATA["launch_incident"]["isolated_return_code"], 2)
        self.assertEqual(DATA["latest_attempt"]["release"], "V090")
        self.assertEqual(DATA["retained_science"]["release"], "V089")
        self.assertEqual(DATA["launch_incident"]["new_reported_failures"], 1)

    def test_review_zip_measurement_scope_cannot_imply_unmeasured_size(self):
        self.rejects("prepared", "review_zip_measurement_status", "MEASURED")
        self.rejects("prepared", "prepared_report_zip_bytes", 64000)

    def test_scoped_count_cannot_duplicate_or_omit_owner_attempts(self):
        self.assertEqual(DATA["launch_incident"]["verified_failed_launches"], 2)
        self.assertEqual(DATA["launch_incident"]["scoped_failed_launches"], 3)
        self.assertEqual(DATA["launch_incident"]["scoped_releases"], ["V090", "V091"])
        self.rejects("launch_incident", "scoped_failed_launches", 4)
        self.rejects("launch_incident", "verified_failed_launches", 1)

    def test_repair_status_cannot_disagree_with_prepared_release(self):
        self.rejects("launch_incident", "next_release", "V091")
        self.rejects("launch_incident", "repair_status", "OWNER_RESEARCH_COMPLETE")


if __name__ == "__main__":
    unittest.main()

