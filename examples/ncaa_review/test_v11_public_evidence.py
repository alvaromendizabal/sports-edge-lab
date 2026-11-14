"""Public NCAA V11 continuity, information-time and operational status gates.

These tests inspect saved public evidence. They perform no fitting, source
acquisition, owner execution or forecast generation.
"""
import base64
from datetime import datetime
import gzip
import hashlib
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[2]
PAGE = ROOT / "docs/ncaa/v11.html"
STATUS = ROOT / "docs/ncaa/v11_1_execution_status.json"


def read_public():
    page = PAGE.read_text(encoding="utf-8")
    packed = re.search(
        r'<script id="v10-data" type="application/octet-stream">(.*?)</script>',
        page, re.S).group(1)
    evidence = json.loads(gzip.decompress(base64.b64decode(packed)))
    operational = json.loads(re.search(
        r'<script id="v11-execution-data" type="application/json">(.*?)</script>',
        page, re.S).group(1))
    return page, packed, evidence, operational


class PublicEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.page, cls.packed, cls.evidence, cls.operational = read_public()

    def test_recovered_scientific_payload_and_status_identity(self):
        self.assertEqual(hashlib.sha256(self.packed.encode()).hexdigest(),
                         self.operational["preserved_scientific_payload_sha256"])
        self.assertEqual(self.operational, json.loads(STATUS.read_text()))
        self.assertEqual(len(self.evidence["v11_pairs"]), 512)
        self.assertEqual(len(self.evidence["v11_comparable_week_leaders"]), 48)
        self.assertEqual(len(self.evidence["models"]), 336)

    def test_updated_partition_accounting_does_not_double_count(self):
        e = self.operational
        self.assertEqual(e["latest_partition_rows"],
                         e["initial_partition_rows"] - e["initial_current_partition_rows"]
                         + e["refreshed_current_partition_rows"])
        self.assertFalse(e["checkpoint_references_are_fits"])
        self.assertEqual(e["verified_reused_fit_credit"], 0)

    def test_deferred_actual_execution_does_not_create_fit_credit(self):
        e = self.operational
        self.assertTrue(e["new_owner_execution_verified"])
        self.assertEqual(e["latest_authenticated_owner_status"],
                         "RESOURCE_DEFERRED_PARTIAL_WORK_PRESERVED")
        for key in ["new_owner_fits", "new_owner_inference",
                    "new_owner_issued_forecasts", "automatic_promotions"]:
            self.assertEqual(e[key], 0)
        run = e["latest_owner_execution"]
        self.assertEqual(run["release"], "B063R12")
        self.assertEqual(run["failed_owner_attempts"], 0)
        self.assertEqual(run["resource_deferred_owner_attempts"], 1)
        self.assertEqual(run["distinct_recorded_errors"], 1)
        self.assertEqual(run["peak_scientific_workers"], 0)
        self.assertAlmostEqual(run["elapsed_seconds"], 1837.8370001469993)
        self.assertFalse(e["next_release"]["owner_execution_verified"])
        self.assertFalse(e["new_scientific_results_this_update"])
        self.assertIn("Latest owner execution stopped before fitting", self.page)
        self.assertIsNone(run["uncommitted_optimizer_attempts"])

    def test_existing_parent_defect_is_not_physical_capacity_shortage(self):
        run = self.operational["latest_owner_execution"]
        a = run["admission"]
        self.assertEqual(a["observations"], 115)
        self.assertEqual(a["measured_capacity_admitted_observations"], 114)
        self.assertAlmostEqual(a["wait_seconds"], 120.00011544599874)
        self.assertFalse(a["final_new_admissions_allowed"])
        self.assertFalse(a["final_draining"])
        self.assertEqual(a["final_reserved_cpus"], 1)
        self.assertEqual(a["final_admission_ceiling"], 1)
        self.assertEqual(a["final_active_fit_slots"], 0)
        self.assertGreater(a["final_available_cpu_cores"], 47)
        self.assertGreater(a["final_free_disk_bytes"], 500_000_000_000)
        self.assertEqual(run["peak_granted_cpus"], 1)
        self.assertFalse(run["actual_12_core_fitting_verified"])
        self.assertIn("existing parent", self.page)

    def test_acquisition_counts_do_not_claim_forecasts(self):
        r = self.operational["latest_owner_execution"]["source_refresh"]
        self.assertTrue(r["completed"])
        self.assertEqual(r["canonical_games"], 2502)
        self.assertEqual(r["canonical_final_games"], 1482)
        self.assertEqual(r["canonical_upcoming_games"], 1016)
        self.assertEqual(r["canonical_games_with_saved_forecast"], 0)
        self.assertEqual(r["weekly_display_rows"], 3429)
        self.assertEqual(r["weekly_rows_without_win_margin_and_total_predictions"], 3429)
        self.assertEqual(r["next_week_rows_without_win_margin_and_total_predictions"], 1001)
        self.assertFalse(r["complete_official_universe"])
        self.assertTrue(r["source_refresh_is_not_training"])

    def test_incomplete_next_release_is_not_a_ready_runner(self):
        r = self.operational["next_release"]
        self.assertEqual(r["release"], "B063R13")
        self.assertTrue(r["status"].startswith("UNRELEASED_"))
        self.assertFalse(r["owner_execution_verified"])
        self.assertFalse(r["packaged_runner_verified"])
        self.assertFalse(r["acquisition_adapter_implemented"])
        self.assertEqual(r["actual_owner_runs_observed"], 0)
        self.assertEqual(r["new_model_fits"], 0)
        self.assertEqual(r["new_issued_forecasts"], 0)
        self.assertEqual(r["local_validation"]["cases_executed"], 47)
        self.assertEqual(r["local_validation"]["passed"], 46)
        self.assertEqual(r["local_validation"]["errors"], 1)
        self.assertFalse(r["local_validation"]["complete_suite_pass"])
        self.assertIn("R13 is unreleased; validation is incomplete", self.page)

    def test_prior_local_checks_did_not_prove_owner_completion(self):
        r = self.operational["prior_release_validation"]
        self.assertEqual(r["release"], "B063R12")
        self.assertEqual(r["local_validation"]["status"], "PASSED")
        self.assertEqual(r["local_validation"]["production_fit_credit_from_local_checks"], 0)
        self.assertIn("Historical R12 local release validation", self.page)
        v = r["local_validation"]
        c = v["final_packaged_counts"]
        self.assertEqual(c["startup"]["passed"], 318)
        self.assertEqual(c["startup"]["errors"] + c["startup"]["failures"] + c["startup"]["skipped"], 0)
        self.assertEqual(c["warm_validation"]["executed_cases"], 0)
        self.assertEqual(c["warm_validation"]["verified_reused_validation_cases"], 318)
        self.assertEqual(c["native_bridge"]["passed"], 54)
        self.assertEqual(c["physical_transport"]["passed"], 16)
        self.assertEqual([(x["serialized_zip_bytes"], x["physical_parts"]) for x in v["physical_archive_boundaries"]],
                         [(536870911, 1), (536870912, 1), (536870913, 2), (2150629376, 5)])
        self.assertEqual(v["initial_transport_attempt"]["errors"], 1)
        self.assertFalse(v["initial_transport_attempt"]["included_in_actual_owner_run_count"])
        self.assertEqual(v["authentic_historical_candidate_validation"]["verified_reused_fit_credit"], 0)
        self.assertTrue(v["separate_suites_may_overlap_do_not_sum"])

    def test_complete_transport_does_not_claim_complete_science(self):
        r = self.operational["latest_owner_execution"]["return"]
        self.assertTrue(r["zip_integrity_verified"])
        self.assertEqual(r["declared_payloads_verified"], 239)
        self.assertTrue(r["complete_declared_payloads_verified"])
        self.assertEqual(r["indexed_local_evidence_objects"], 65)
        self.assertEqual(r["exact_indexed_bodies_in_download"], 65)
        self.assertEqual(r["bytes"], 83145771)
        self.assertEqual(r["manifest_bytes"], 39979)
        self.assertEqual(r["scientific_status"], "PARTIAL")
        self.assertEqual(r["s3_persistence"], "VERIFIED_ALL_PHYSICAL_RETURN_BYTES")
        self.assertEqual(r["return_s3_put_calls"], 2)
        self.assertEqual(r["return_s3_get_calls"], 2)
        self.assertEqual(r["return_s3_uploaded_bytes"], 83185750)
        self.assertEqual(r["return_s3_readback_bytes"], 83185750)
        self.assertIsNone(r["whole_run_s3_calls"])
        self.assertIsNone(r["whole_run_s3_bytes"])
        previous = self.operational["previous_owner_execution"]
        self.assertEqual(previous["release"], "B063R11")
        self.assertEqual(previous["return"]["exact_indexed_bodies_in_download"], 0)
        self.assertEqual(previous["return"]["s3_persistence"], "NOT_ATTEMPTED")

    def test_selected_run_tally_is_not_a_lifetime_or_model_count(self):
        t = self.operational["selected_execution_tally"]
        self.assertEqual(t["actual_owner_runs"], 15)
        tally_html = re.search(r'<p id="execution-tally">(.*?)</p>', self.page, re.S).group(1)
        self.assertIn("15 actual owner runs", tally_html)
        self.assertIn("2 completed with coverage gaps, 9 failed", tally_html)
        self.assertEqual(t["completed_with_coverage_gaps"] + t["failed"] +
                         t["resource_deferred"], t["actual_owner_runs"])
        self.assertEqual(t["recent_runs"], 4)
        self.assertEqual(t["recent_completed_frozen_scoring"], 1)
        self.assertEqual(t["recent_failed"], 2)
        self.assertEqual(t["recent_resource_deferred"], 1)
        self.assertEqual(t["resource_deferred"], 4)
        self.assertEqual(t["unsuccessful_or_deferred"], 13)
        self.assertEqual(t["completed_with_coverage_gaps"], 2)
        self.assertEqual(t["failed"], 9)
        self.assertEqual(t["earlier_two_returns"]["historical_new_target_fits"], 173)
        self.assertEqual(t["earlier_two_returns"]["new_fits_credited_to_this_update"], 0)
        self.assertEqual(t["recent_new_target_fits"], 0)
        self.assertIsNone(t["lifetime_runs"])
        self.assertIsNone(t["lifetime_failures"])
        self.assertTrue(self.operational["historical_uncertainty_reused_this_update"])

    def test_benchmark_is_measured_scoring_without_fit_claim(self):
        b = self.operational["benchmark"]
        self.assertFalse(b["synthetic_work"])
        self.assertEqual(b["unique_tasks"], 18)
        self.assertEqual(b["peak_workers"], 12)
        self.assertEqual([x["layout"] for x in b["layouts"]],
                         ["1x1", "4x1", "8x1", "12x1"])
        for row in b["layouts"]:
            self.assertAlmostEqual(row["speedup"],
                                   b["layouts"][0]["wall_seconds"] / row["wall_seconds"],
                                   places=7)
        self.assertIn("not a fitting benchmark", b["thread_schedule_limit"])

    def test_transport_limit_is_per_physical_part(self):
        p = self.operational["delivery_policy"]
        self.assertEqual(p["maximum_physical_part_bytes"], 512 << 20)
        self.assertFalse(p["aggregate_transport_size_is_science_admission_gate"])

    def test_new_uncertainty_supplement_retains_negative_and_null_results(self):
        s = self.operational["historical_uncertainty_supplement"]
        self.assertEqual(s["historical_partitions"], 12)
        self.assertEqual(s["interval_rows"], 336)
        self.assertEqual(s["bootstrap_replicates"], 149999)
        self.assertEqual(s["directions"],
                         {"POSITIVE": 9, "NEGATIVE": 15, "INCLUDES_ZERO": 312})
        self.assertEqual(sum(s["directions"].values()), s["interval_rows"])
        self.assertEqual(s["self_baseline_controls_in_interval_rows"], 28)
        self.assertEqual(s["negative_controls_passed"], s["negative_controls_total"])
        self.assertEqual(s["negative_controls_total"], 40)
        self.assertLess(s["point_estimates_max_absolute_reproduction_error"], 1e-14)
        self.assertTrue(s["cohorts_and_game_counts_reproduced"])
        self.assertIsNone(s["weighted_champion"])
        self.assertFalse(s["new_market_evidence"])
        self.assertEqual(s["new_model_fits"], 0)
        self.assertEqual(s["new_model_inference"], 0)
        self.assertEqual(s["new_issued_forecasts"], 0)
        self.assertEqual(s["promotions"], 0)
        for key, label in [("positive", "POSITIVE"), ("negative", "NEGATIVE"),
                           ("includes_zero", "INCLUDES_ZERO")]:
            self.assertEqual(sum(r[key] for r in s["by_competition_season"]),
                             s["directions"][label])

    def test_weighted_and_market_claims_remain_withheld(self):
        d = self.evidence
        self.assertEqual(d["v11_weighting"]["complete_three_season_candidates"], 0)
        self.assertEqual(d["v11_weighting"]["status"],
                         "WEIGHTED_RANK_WITHHELD_MISSING_EXACT_RECIPE_LINEAGE")
        self.assertTrue(all(p["games"] == 0 for p in d["providers"]))
        self.assertTrue(all(not p["automatic_promotion"] for p in d["v11_pairs"]))
        self.assertTrue(all(u["bonferroni_family_95_interval"] is None
                            for p in d["v11_pairs"] for u in p["uncertainty"].values()))

    def test_future_unissued_values_remain_withheld(self):
        d = self.evidence
        self.assertEqual(d["public_projection"]["future_unissued_numeric_forecasts_published"], 0)
        self.assertEqual(d["public_projection"]["future_forecast_cells_withheld"], 2793)
        asof = datetime.fromisoformat(d["analysis_asof"].replace("Z", "+00:00"))
        checked = 0
        for game in d["games"]:
            stamp = game.get("event_time")
            if not stamp:
                continue
            event = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
            if event > asof:
                for forecast in game["forecasts"].values():
                    if forecast is not None:
                        self.assertIn(forecast["evidence_class"],
                                      ["ORIGINAL_ISSUED", "FUTURE_ISSUED"])
                checked += 1
        self.assertGreater(checked, 0)

    def test_no_private_cloud_or_runtime_material(self):
        public = self.page + json.dumps(self.evidence) + json.dumps(self.operational)
        for forbidden in ["s3://", "arn:aws:", "/home/sagemaker-user", ".pyz",
                          "aws_secret_access_key", "B032_RETRAINED_", '"feature_columns":',
                          '"hyperparameters":', '"model_weights":']:
            self.assertNotIn(forbidden, public)
        self.assertFalse(self.evidence["complete_current_season"])
        self.assertFalse(self.evidence["complete_upcoming_schedule"])


class PublicObservedCensusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.canonical = json.loads((ROOT / "docs/ncaa/v11_r12_canonical_games.json").read_text())
        cls.unresolved = json.loads((ROOT / "docs/ncaa/v11_r12_unresolved_inventory.json").read_text())
        cls.page, _, _, cls.operational = read_public()
        cls.columns = ["league", "event_id", "away_team", "home_team", "event_time",
                       "time_precision", "status", "inventory_kind", "missing_reasons",
                       "away_score", "home_score"]

    def rows(self, data):
        return [dict(zip(data["columns"], row)) for row in data["rows"]]

    def test_canonical_counts_and_unique_public_event_ids(self):
        rows = self.rows(self.canonical)
        self.assertEqual(self.canonical["row_count"], 2502)
        self.assertEqual(len(rows), 2502)
        self.assertEqual(len({(r["league"], r["event_id"]) for r in rows}), 2502)
        self.assertEqual({r["inventory_kind"] for r in rows}, {"CANONICAL_ACQUISITION_GAME"})
        self.assertEqual(self.canonical["census_counts"], self.unresolved["census_counts"])
        self.assertFalse(self.canonical["complete_official_universe"])
        self.assertFalse(self.unresolved["complete_official_universe"])

    def test_unresolved_records_are_retained_without_unique_game_claim(self):
        from collections import Counter
        rows = self.rows(self.unresolved)
        self.assertEqual(len(rows), 22020)
        self.assertEqual(Counter(r["inventory_kind"] for r in rows),
                         {"UNRESOLVED_OFFICIAL_RECORD": 903,
                          "UNRESOLVED_PROVIDER_SCHEDULE_RECORD": 21117})
        self.assertEqual(len(rows) + self.canonical["row_count"], 24522)
        overlap = [r for r in rows if r["event_id"] == "ncaam:ncaa:contest:6661200"]
        self.assertEqual(len(overlap), 2)
        self.assertEqual(len({r["inventory_kind"] for r in overlap}), 2)
        self.assertFalse(self.operational["latest_public_observed_census"]["unresolved_rows_are_unique_games"])

    def test_status_totals_do_not_relabel_in_progress_as_future_start(self):
        from collections import Counter
        counts = Counter(r["status"] for r in self.rows(self.canonical))
        self.assertEqual(counts, {"final": 1482, "scheduled": 1013,
                                 "in_progress": 3, "source_status_unqualified": 4})
        self.assertEqual(counts["scheduled"] + counts["in_progress"], 1016)
        self.assertIn("it is not a count of future starts", self.page)
        self.assertIn("complete official season universe has not been verified", self.page)
        for data in [self.canonical, self.unresolved]:
            self.assertEqual(data["report_asof"], "2026-11-14T05:23:59.250627+00:00")

    def test_public_projection_has_only_approved_fields_and_public_ids(self):
        allowed_top = {"schema", "release", "report_asof", "season", "complete_official_universe",
                       "census_counts", "columns", "forecast_status", "scope", "inventory_scope", "row_count", "rows"}
        reasons = {"NO_EXACT_CANONICAL_OFFICIAL_RECONCILIATION", "NO_QUALIFIED_SAVED_FORECAST",
                   "SCHEDULE_RECORD_NOT_BOUND_TO_MODEL_INPUTS", "NO_QUALIFIED_ISSUED_FORECAST"}
        for data in [self.canonical, self.unresolved]:
            self.assertEqual(set(data), allowed_top)
            self.assertEqual(data["columns"], self.columns)
            self.assertTrue(all(len(row) == len(self.columns) for row in data["rows"]))
            for row in self.rows(data):
                self.assertRegex(row["event_id"], r"^ncaa[mw]:(?:ncaa:contest|espn:event):\d+$")
                self.assertLessEqual(set(row["missing_reasons"]), reasons)
            text = json.dumps(data)
            for forbidden in ["s3://", "arn:aws:", "/home/sagemaker-user", "source_row_sha256",
                              "source_version_id", "source_input_pins", "available_at", "source_sha256",
                              "feature_columns", "hyperparameters", "model_weights", "apiKey", "X-Amz-", '"forecasts":']:
                self.assertNotIn(forbidden, text)
            self.assertIsNone(re.search(r"\b[0-9a-f]{64}\b", text))

    def test_only_canonical_finals_have_public_scores_and_no_forecasts(self):
        canonical = self.rows(self.canonical)
        self.assertEqual(sum(r["away_score"] is not None for r in canonical), 1482)
        for row in canonical + self.rows(self.unresolved):
            present = row["away_score"] is not None or row["home_score"] is not None
            if present:
                self.assertEqual(row["inventory_kind"], "CANONICAL_ACQUISITION_GAME")
                self.assertEqual(row["status"], "final")
                self.assertIsInstance(row["away_score"], (int, float))
                self.assertIsInstance(row["home_score"], (int, float))
            self.assertTrue(row["missing_reasons"])
        self.assertEqual(self.canonical["census_counts"]["canonical_games_with_saved_forecast"], 0)
        self.assertFalse(self.operational["latest_public_observed_census"]["source_refresh_or_science_performed_by_publication"])

    def test_public_assets_and_static_fallback_keep_asof_and_missingness(self):
        self.assertIn('<section id="latest-census"', self.page)
        self.assertLess(self.page.index('<section id="latest-census"'), self.page.index('<section id="leaders"'))
        self.assertIn('<noscript>', self.page)
        for filename in ["v11_r12_canonical_games.json", "v11_r12_unresolved_inventory.json"]:
            self.assertIn(f'href="{filename}" download', self.page)
            self.assertTrue((PAGE.parent / filename).is_file())
        self.assertIn("No qualified saved forecast", self.page)
        self.assertIn("preserved model comparisons", self.page)
        self.assertEqual(self.operational["latest_public_observed_census"]["report_asof"], self.canonical["report_asof"])


if __name__ == "__main__":
    unittest.main()
