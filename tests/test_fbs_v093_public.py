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
        self.assertLess(len(rendered), 60_000)
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

    def test_original_readme_suffix_is_preserved(self):
        text = (ROOT / "docs/fbs/README.md").read_text()
        marker = "<!-- FBS_V093_READINESS_END -->\n\n"
        self.assertIn(marker, text)
        suffix = text.split(marker, 1)[1].encode()
        self.assertEqual(hashlib.sha256(suffix).hexdigest(), "1cd9a51c0bca1e0626a50d1ab59f5ff2b1c9e56e2e2c6453553cab4217723318")


if __name__ == "__main__":
    unittest.main()
