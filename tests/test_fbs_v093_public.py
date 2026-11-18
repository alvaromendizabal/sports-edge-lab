"""Reject scientific, pricing and publication contradictions in V093 readiness."""
import copy
from datetime import datetime
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("fbs_v093_review", ROOT / "examples/fbs_contracts/v093/build_review.py")
REVIEW = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(REVIEW)
DATA = json.loads((ROOT / "docs/fbs/v093/data/status.json").read_text())


class V093Readiness(unittest.TestCase):
    def rejects(self, section, key, value):
        d = copy.deepcopy(DATA)
        d[section][key] = value
        with self.assertRaises(ValueError):
            REVIEW.render(d)

    def test_deterministic_self_contained_complete_evidence(self):
        rendered = REVIEW.render(DATA)
        self.assertEqual(rendered, REVIEW.render(copy.deepcopy(DATA)))
        self.assertEqual(rendered, (ROOT / "docs/fbs/v093/index.html").read_bytes())
        embedded = re.search(rb'<script id="report-data" type="application/json">(.*?)</script>', rendered, re.S).group(1)
        self.assertEqual(json.loads(embedded), DATA)
        self.assertLess(len(rendered), 75_000)
        self.assertNotIn(b"circa", rendered.lower())
        self.assertNotRegex(rendered.decode(), r'<script[^>]+src=|<link[^>]+stylesheet')

    def test_prepared_software_cannot_become_scientific_execution(self):
        for key in ("owner_executions", "scientific_fits", "provider_retrievals"):
            self.rejects("prepared", key, 1)
        self.rejects("prepared", "status", "SCIENTIFICALLY_COMPLETE")
        self.rejects("prepared", "measured_optimizer_cores", 24)

    def test_release_sealing_requires_canonical_and_native_evidence(self):
        d = copy.deepcopy(DATA)
        d["prepared"].update(status="PREPARED_NOT_EXECUTED", canonical_verified=False)
        with self.assertRaises(ValueError):
            REVIEW.render(d)

    def test_future_test_outcomes_cannot_select_or_reweight_training(self):
        for field in ("test_used_for_selection", "season_training_weights_used"):
            self.rejects("selection", field, True)
        self.rejects("selection", "prior_test_exposure", False)
        self.rejects("selection", "primary_weights", [.2, .8])

    def test_current_census_remains_unmeasured_until_launch(self):
        self.rejects("population", "fresh_current_test_games", 752)
        self.rejects("retained", "current_as_of_claim", True)
        self.rejects("population", "resolved_again_at_launch", False)

    def test_conditional_validation_is_not_full_test_completion(self):
        for field in ("conditional_stage_complete", "conditional_full_current_test_reporting_complete", "conditional_champion_eligible"):
            self.rejects("population", field, True)
        self.rejects("population", "conditional_current_test_blocked_jobs", 0)

    def test_changed_validation_identity_cannot_be_admitted(self):
        self.rejects("population", "validation_identity_required", False)
        self.rejects("population", "full_current_population_required", False)

    def test_empty_admitted_queue_requires_failure_exit(self):
        self.rejects("population", "no_admission_operational_failure", False)
        self.rejects("population", "no_admission_required_exit_code", 0)

    def test_campaign_preserves_complete_registration(self):
        self.assertEqual(DATA["campaign"]["registered_jobs"], DATA["campaign"]["validation_jobs"] + DATA["campaign"]["frozen_test_jobs"])
        self.rejects("campaign", "registered_jobs", 624)
        self.rejects("campaign", "frozen_test_jobs", 0)

    def test_price_read_cannot_renew_cache_or_change_permissions(self):
        self.rejects("pricing", "cached_clock_renews_on_reuse", True)
        self.rejects("pricing", "permissions_changed", True)
        self.rejects("pricing", "cache_age_limit_seconds", 172800)
        self.rejects("pricing", "account_and_app_check_required", False)

    def test_price_source_is_bounded_verified_and_not_invoice(self):
        self.rejects("pricing", "public_redirects_allowed", True)
        self.rejects("pricing", "public_region_max_bytes", 100_000_000)
        self.rejects("pricing", "native_public_source_verified", False)
        self.rejects("pricing", "rate_is_invoice", True)
        self.rejects("pricing", "official_documentation_url", "https://example.com/")
        for value in (-1, 0, float("inf"), float("nan"), True):
            self.rejects("pricing", "rate_usd_per_full_host_hour", value)

    def test_cost_wall_and_worker_contract_remain_intact(self):
        self.rejects("campaign", "cost_guard_usd", 0)
        self.rejects("campaign", "wall_time_waives_cost_guard", True)
        self.rejects("campaign", "worker_ceiling", 48)
        self.rejects("verification", "scientific_occupancy_gate", "PASS")

    def test_publication_cannot_claim_deployment_promotion_or_issuance(self):
        for field in ("website_deployed", "production_promoted", "new_forecasts_published"):
            self.rejects("publication", field, True)

    def test_recovery_cannot_discard_work_or_lower_science_size(self):
        for field in ("reuse_completed_task_identities", "resolve_latest_actual_return_at_launch", "actual_pointer_after_integrity_only", "partial_status_preserved"):
            self.rejects("recovery", field, False)
        self.rejects("recovery", "aggregate_science_cap", 536870912)

    def test_unknown_private_and_out_of_scope_content_rejected(self):
        d = copy.deepcopy(DATA)
        d["model_weights"] = [1, 2]
        with self.assertRaises(ValueError):
            REVIEW.render(d)
        for text in ("s3://private/path", "/home/sagemaker-user/private", "Circa"):
            self.rejects("pricing", "source", text)

    def test_scoped_failures_cannot_be_counted_again(self):
        self.rejects("recovery", "scoped_failed_attempts", 4)
        self.rejects("recovery", "scoped_successful_attempts", 1)
        self.assertEqual(DATA["recovery"]["scoped_failed_releases"], ["V090", "V091"])

    def test_actual_attempts_cannot_be_conflated(self):
        d = copy.deepcopy(DATA)
        d["attempts"]["second"]["run_id"] = d["attempts"]["first"]["run_id"]
        with self.assertRaises(ValueError):
            REVIEW.render(d)
        self.rejects("attempts", "scoped_failed_attempts", 6)
        self.rejects("attempts", "scoped_successful_attempts", 1)
        self.rejects("attempts", "scoped_active_attempts", 1)

    def test_verified_partial_failure_is_not_successful_or_active(self):
        for key, value in (("child_exit_observed", False), ("child_exit_code", 0), ("status", "COMPLETED"), ("new_model_fits", 459), ("pending_validation_jobs", 0), ("blocked_test_jobs", 0)):
            d = copy.deepcopy(DATA)
            d["attempts"]["first"][key] = value
            with self.assertRaises(ValueError):
                REVIEW.render(d)
        self.rejects("attempts", "latest_actual_return_refreshed", False)

    def test_return_integrity_does_not_imply_scientific_success(self):
        for key in ("owner_execution_successful", "scientific_complete"):
            self.rejects("verified_return", key, True)
        self.rejects("verified_return", "partial_or_resumable", False)
        self.rejects("verified_return", "integrity_verified", False)

    def test_control_zip_is_separate_from_scientific_payloads(self):
        self.rejects("verified_return", "new_payload_uploaded_bytes", DATA["verified_return"]["control_zip_bytes"])
        self.rejects("verified_return", "inherited_payload_bytes_not_recopied", 0)
        self.rejects("verified_return", "aggregate_science_cap", 536870912)

    def test_prediction_rows_cannot_become_unique_games_or_new_issue(self):
        for key in ("prediction_rows_are_games", "new_original_issue_claimed", "full_current_population_champion_eligible"):
            d=copy.deepcopy(DATA)
            d["attempts"]["first"][key]=True
            with self.assertRaises(ValueError):
                REVIEW.render(d)

    def test_failed_admission_has_its_own_observed_exit_and_no_fits(self):
        for key, value in (("child_exit_code", 0), ("new_model_fits", 458), ("phase", "MODEL_FITTING"), ("primary_errno", 0), ("actual_return_pointer_advanced", True)):
            d = copy.deepcopy(DATA)
            d["attempts"]["second"][key] = value
            with self.assertRaises(ValueError):
                REVIEW.render(d)

    def test_preparation_clock_precedes_actual_owner_execution(self):
        self.rejects("prepared", "snapshot_at", DATA["attempts"]["observed_at"])
        d = copy.deepcopy(DATA)
        d["attempts"]["second"]["exit_observed_at"] = d["prepared"]["snapshot_at"]
        with self.assertRaises(ValueError):
            REVIEW.render(d)

    def test_observed_occupancy_keeps_sixteen_worker_denominator(self):
        for key, value in (("required_gate_status", "CPU_ACCEPTANCE_FAILED"), ("extra_optimizer_status", "PASS_REAL_WORK"), ("minimum_fraction", .7), ("denominator_workers", 24), ("full_24_worker_occupancy_claimed", True), ("overall_fit_throughput_acceptance_claimed", True), ("synthetic_or_reserved_load_counted", True)):
            d = copy.deepcopy(DATA)
            d["attempts"]["occupancy"][key] = value
            with self.assertRaises(ValueError):
                REVIEW.render(d)

    def test_memory_policy_explains_capacity_without_peak_claim(self):
        memory = DATA["attempts"]["memory"]
        self.assertEqual(memory["budget_bytes"] // (memory["resident_bytes_per_worker"] + memory["transient_bytes_per_worker"]), 16)
        for key, value in (("admitted_workers", 24), ("arbitrary_reserved_cores", 1), ("estimates_are_measured_peak_bounds", True)):
            d = copy.deepcopy(DATA)
            d["attempts"]["memory"][key] = value
            with self.assertRaises(ValueError):
                REVIEW.render(d)

    def test_repair_cannot_claim_delivery_without_native_and_canonical_proof(self):
        d = copy.deepcopy(DATA)
        d["replacement"].update(status="PREPARED_NOT_EXECUTED", native_verified=False)
        with self.assertRaises(ValueError):
            REVIEW.render(d)
        self.rejects("replacement", "owner_executions", 1)
        self.rejects("replacement", "active_run_restart_authorized", True)
        self.rejects("replacement", "required_useful_gate_preserved", False)
        self.rejects("replacement", "extra_optimizer_gate_can_abort", True)
        self.rejects("replacement", "optimizer_telemetry_retained", False)
        self.rejects("replacement", "owner_lock_refusal_child_exit", 0)

    def test_original_readme_suffix_is_preserved(self):
        text = (ROOT / "docs/fbs/README.md").read_text()
        marker = "<!-- FBS_V093_READINESS_END -->\n\n"
        self.assertIn(marker, text)
        suffix = text.split(marker, 1)[1].encode()
        self.assertEqual(hashlib.sha256(suffix).hexdigest(), "1cd9a51c0bca1e0626a50d1ab59f5ff2b1c9e56e2e2c6453553cab4217723318")

    def test_native_validation_completion_does_not_advance_portable_custody(self):
        a = DATA["current_attempt"]
        self.assertEqual(a["native_completed_validation_jobs"], 624)
        self.assertEqual(DATA["attempts"]["first"]["completed_validation_jobs"], 470)
        for key in ("portable_return_integrity_verified", "actual_return_pointer_advanced", "full_scientific_complete",
                    "full_current_test_reporting_complete", "full_current_population_champion_eligible"):
            self.rejects("current_attempt", key, True)
        self.rejects("current_attempt", "latest_verified_return_release", "V095")

    def test_observed_delivery_failure_overrides_provisional_scientific_success(self):
        self.assertEqual(DATA["current_attempt"]["science_stage_exit_code"], 0)
        self.rejects("current_attempt", "child_exit_code", 0)
        self.rejects("current_attempt", "supervisor_status", "COMPLETED")
        self.rejects("current_attempt", "delivery_error", None)
        self.rejects("current_attempt", "scoped_successful_attempts", 1)
        self.rejects("current_attempt", "failed_fits", 154)

    def test_latest_tally_counts_new_authenticated_attempt_exactly_once(self):
        self.assertEqual(DATA["current_attempt"]["scoped_failed_attempts"], DATA["attempts"]["scoped_failed_attempts"] + 1)
        for n in (5, 7):
            self.rejects("current_attempt", "scoped_failed_attempts", n)
        self.rejects("current_attempt", "scoped_active_attempts", 1)
        self.rejects("current_attempt", "run_id", DATA["attempts"]["first"]["run_id"])

    def test_native_branch_totals_distinguish_new_and_checkpoint_work(self):
        branches = DATA["current_attempt"]["branch_counts"]
        self.assertEqual(sum(b["new_base_fits"] for b in branches), 154)
        self.assertEqual(sum(b["checkpoint_reused_jobs"] for b in branches), 470)
        self.assertEqual(sum(b["completed_validation_jobs"] for b in branches), 624)
        self.rejects("current_attempt", "blocked_test_jobs", 0)
        self.rejects("current_attempt", "checkpoint_reused_jobs", 0)
        d = copy.deepcopy(DATA)
        d["current_attempt"]["branch_counts"][0]["new_base_fits"] = 204
        with self.assertRaises(ValueError):
            REVIEW.render(d)

    def test_current_observed_census_preserves_unknown_completeness_and_older_cohorts(self):
        self.assertEqual(DATA["current_census"]["completed_games"] + DATA["current_census"]["pending_games"], 888)
        for key in ("official_population_complete_proven", "full_current_test_metrics_available"):
            self.rejects("current_census", key, True)
        self.rejects("current_census", "completed_games", 752)
        self.rejects("current_census", "rows_removed_for_model_coverage", 3)
        self.rejects("current_census", "source_as_of_is_inspection_clock", False)

    def test_short_work_queue_cannot_claim_sustained_occupancy(self):
        self.rejects("current_attempt", "sustained_occupancy_pass_claimed", True)
        self.rejects("current_attempt", "required_gate_status", "PASS_REAL_WORK")
        self.rejects("current_attempt", "selected_worker_capacity", 24)
        self.rejects("current_attempt", "estimate_is_invoice", True)

    def test_new_preparation_requires_native_proof_and_cannot_rewrite_actual_return(self):
        for key in ("owner_executions", "scientific_fits", "provider_retrievals"):
            self.rejects("next_preparation", key, 1)
        for key in ("process_or_predecessor_restarted", "latest_return_pointer_changed_by_preparation"):
            self.rejects("next_preparation", key, True)
        d = copy.deepcopy(DATA)
        d["next_preparation"].update(status="PREPARED_NOT_EXECUTED", native_verified=False)
        with self.assertRaises(ValueError):
            REVIEW.render(d)

    def test_native_inspection_and_preparation_keep_ordered_clocks(self):
        self.rejects("current_attempt", "started_at", DATA["prepared"]["snapshot_at"])
        self.rejects("current_attempt", "child_exit_observed_at", "2026-11-18T08:00:00Z")
        self.rejects("current_census", "observed_at", DATA["prepared"]["snapshot_at"])

    def test_planned_fit_and_rescore_scope_preserves_pretest_components(self):
        for key, value in (("status", "COMPLETED"), ("training_through_season", 2026),
                           ("test_labels_only_for_grading", False), ("same_game_identities_required", False),
                           ("validation_lock_reused", False), ("proof_created_owner_runs", 1)):
            self.rejects("next_research", key, value)

    def test_retained_pending_gaps_cannot_be_claimed_as_complete_forecasts(self):
        plan = DATA["next_research"]
        self.assertEqual(sum(g["policies"] for g in plan["retained_pending_coverage_groups"]), 397)
        self.assertEqual(plan["pending_games"], 133)
        for i in (0, 1):
            d = copy.deepcopy(DATA)
            d["next_research"]["retained_pending_coverage_groups"][i]["covered_pending_games"] = 133
            with self.assertRaises(ValueError):
                REVIEW.render(d)
        self.rejects("next_research", "pending_feature_gaps_per_frozen_target_context", 0)
        self.rejects("next_research", "full_population_completeness_claimed", True)

    def test_prepared_context_proof_has_its_own_clock_and_pin(self):
        self.rejects("next_research", "context_proof_at", DATA["current_attempt"]["observed_at"])
        d = copy.deepcopy(DATA)
        d["verification"]["evidence"] = [x for x in d["verification"]["evidence"] if x["sha256"] != d["next_research"]["context_proof_sha256"]]
        with self.assertRaises(ValueError):
            REVIEW.render(d)


if __name__ == "__main__":
    unittest.main()
