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
        self.assertEqual(obs["one_reserved_core_samples"], 94)
        self.assertEqual(obs["twelve_reserved_core_samples"], 3)
        self.assertEqual(obs["matched_cpu_intervals"], 103)
        self.assertAlmostEqual(obs["peak_cpu_cores"], 11.701368980331605)
        self.assertEqual(obs['peak_work_class'], 'TRANSPORT_FINALIZATION_NOT_SCIENTIFIC_FITS')
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
        with self.assertRaisesRegex(ValueError, "NO_B081_OWNER_RUN"):
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
        self.assertEqual(package["packaged_tests"], 489)
        self.assertEqual(package["passed"], package["packaged_tests"])
        self.assertEqual(package["failures"] + package["errors"] + package["skipped"] + package["module_errors"], 0)
        self.assertRegex(package["exact_package_sha256"], r'^[0-9a-f]{64}$')
        self.assertNotEqual(package["exact_package_sha256"], self.data['latest_owner_execution']['executable_sha256'])
        self.assertFalse(package["owner_execution_performed"])
        self.assertEqual(package["post_test_source_cache_pyc_files"], 0)
        self.assertGreater(package["exact_package_bytes"], 118159084)
        self.assertLess(package["exact_package_bytes"], 512 << 20)
        self.assertEqual(package['original_B080_members_preserved'], 1147)
        self.assertEqual(package["embedded_lineage_verification"]["status"], "PASS")
        self.assertEqual(package["embedded_lineage_verification"]["AWS_operations"], 0)
        warm = package["warm_executable_local_review"]
        self.assertEqual(warm["execution_scope"], "PREPARED_REVIEW_ONLY_NON_AWS")
        self.assertFalse(warm["owner_AWS_execution"])
        self.assertEqual(warm["new_scientific_fits"], 0)
        self.assertEqual(warm["unchanged_source_member_identity_reuses"], package['package_members'])
        self.assertEqual(warm["source_members_freshly_rehashed"], 0)
        changed = copy.deepcopy(self.data)
        changed['replacement_engineering']['package_verification']['exact_package_sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'EXACT_PACKAGE_VERIFICATION_CHANGED'):
            review.validate(changed)

    def test_actual_log_health_and_transfer_scope_stay_separate_from_science(self):
        logging = self.data['live_logging']
        self.assertEqual(logging['heartbeat_samples'], 104)
        self.assertEqual(logging['health_errors'], [])
        self.assertAlmostEqual(logging['maximum_gap_seconds'], 10.612139867998849)
        self.assertTrue(logging['logging_success_is_not_model_success'])
        for key, value, error in (
            ('scope', 'WHOLE_PIPELINE', 'TRANSFER_SCOPE_CHANGED'),
            ('get_calls', 1, 'TRANSFER_SCOPE_CHANGED'),
            ('attempted_body_bytes', 0, 'TRANSFER_SCOPE_CHANGED'),
        ):
            changed = copy.deepcopy(self.data)
            changed['live_logging']['s3_checkpoints'][key] = value
            with self.assertRaisesRegex(ValueError, error): review.validate(changed)

    def test_missing_finalizer_hashes_remain_unknown_and_cost_remains_estimate(self):
        cache = self.data['cache_evidence']
        self.assertIsNone(cache['finalizer_hash_operations'])
        self.assertIsNone(cache['finalizer_bytes_hashed'])
        self.assertEqual(cache['parquet_operation'], 'VERIFIED_LOCAL_PARQUET_CONTEXT_REUSED')
        self.assertFalse(cache['whole_pipeline_s3_transfers_fully_instrumented'])
        self.assertIsNone(self.data['cost_evidence']['actual_billed_cost_usd'])
        changed = copy.deepcopy(self.data)
        changed['cache_evidence']['finalizer_hash_operations'] = 0
        with self.assertRaisesRegex(ValueError, 'CACHE_SCOPE_CHANGED'): review.validate(changed)
        changed = copy.deepcopy(self.data)
        changed['cost_evidence']['actual_billed_cost_usd'] = .292741
        with self.assertRaisesRegex(ValueError, 'COST_IS_NOT_INVOICE'): review.validate(changed)

    def test_prior_failure_review_remains_available_unchanged(self):
        previous_B080 = ROOT/'history/b080_prepared_execution_review.json'
        self.assertEqual(hashlib.sha256(previous_B080.read_bytes()).hexdigest(),
                         '430551e3b4f0c74cededad2e896602f0e467745b77d78c41f6866392ac722f25')
        prior = json.loads(previous_B080.read_bytes())
        self.assertEqual(prior['latest_owner_execution']['release'], 'B079')
        self.assertEqual(prior['replacement_engineering']['release'], 'B080')
        self.assertEqual(prior['science_preservation'], self.data['science_preservation'])
        previous = ROOT/'history/b079_prepared_execution_review.json'
        self.assertEqual(hashlib.sha256(previous.read_bytes()).hexdigest(),
                         'f77bb9272877112d71779f94e3d82b7b2af914e7c0c07fdd6b3ff87fbdbe8039')
        document = json.loads(previous.read_bytes())
        self.assertEqual(document['latest_owner_execution']['release'], 'B078')
        self.assertEqual(document['replacement_engineering']['release'], 'B079')
        self.assertEqual(document['latest_owner_execution']['return']['sha256'],
                         'fee168714d963992f71904c0ff46b161fcc2416a4432cf6e6bdf57963369448d')
        self.assertEqual(document['science_preservation'], self.data['science_preservation'])

    def test_preflight_objects_are_not_hidden_by_zero_frame_task_count(self):
        failure = self.data['capacity_failure']
        self.assertEqual(failure['files_physically_prepared'], 33977)
        self.assertEqual(failure['new_objects_compressed'], 61460)
        self.assertEqual(failure['frame_tasks_submitted'], 0)
        self.assertAlmostEqual(failure['preflight_seconds'], 595.8604437939994)
        self.assertGreater(failure['conservative_bound_bytes'], failure['scientific_allowance_bytes'])
        self.assertLess(failure['actual_final_scientific_support_bytes'], failure['scientific_allowance_bytes'])
        self.assertTrue(failure['zero_frame_tasks_did_not_mean_zero_object_compression'])
        changed = copy.deepcopy(self.data)
        changed['capacity_failure']['new_objects_compressed'] = 0
        with self.assertRaisesRegex(ValueError, 'ACTUAL_CAPACITY_FAILURE_CHANGED'):
            review.validate(changed)

    def test_metadata_replay_does_not_become_whole_run_speedup_or_new_science(self):
        proof = self.data['replacement_engineering']['budget_verification']
        self.assertEqual(proof['selected_files'], 76324)
        self.assertEqual(proof['inherited_files'], 76324)
        self.assertEqual(proof['complete_support_bound_bytes'], 36821661)
        self.assertTrue(proof['owner_current_source_and_full_ancestry_guards_still_required'])
        self.assertEqual(proof['declared_omissions_unchanged'], 2658)
        self.assertTrue(proof['actual_report_original_verifier_passed'])
        for field, value in (('controlled_end_to_end_speedup_established', True),
                             ('new_scientific_fits', 12), ('declared_omissions_unchanged', 0)):
            changed = copy.deepcopy(self.data)
            changed['replacement_engineering']['budget_verification'][field] = value
            with self.assertRaisesRegex(ValueError, 'METADATA_TEST_SCOPE_CHANGED'):
                review.validate(changed)

    def test_pending_package_receipt_cannot_pass_publish_check(self):
        from unittest import mock
        changed = copy.deepcopy(self.data)
        changed['replacement_engineering']['package_verification'] = {'status': 'FINAL_RECEIPT_PENDING'}
        path = ROOT/'latest_execution_review.json'; read = Path.read_bytes
        def substituted(p):
            return json.dumps(changed).encode() if p == path else read(p)
        with mock.patch.object(Path, 'read_bytes', substituted):
            with self.assertRaisesRegex(ValueError, 'FINAL_PACKAGE_RECEIPT_REQUIRED'):
                review.build(True)


if __name__ == "__main__":
    unittest.main()
