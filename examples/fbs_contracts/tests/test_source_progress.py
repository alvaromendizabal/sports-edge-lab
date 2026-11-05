"""Invented, offline source-inventory fixtures; no owner research is executed."""
import copy
import json
import unittest

from examples.fbs_contracts.source_progress import (
    INVENTORY_SCHEMA, PROGRESS_SCHEMA, PROGRESS_SCHEMA_V2, render_payload, render_section,
    validate_inventory, validate_progress,
)


def fixture_inventory():
    rows = []
    for year in (2024, 2025, 2026):
        complete = year != 2026
        rows.append({"season": year, "phase": "regular", "week": 1,
                     "kickoff": f"{year}-09-01T18:00:00Z", "kickoff_tbd": False,
                     "home": f"Home {year}", "away": f"Away {year}", "population": "FBS_V_FBS",
                     "result_status": "COMPLETED_WITH_SCORES" if complete else "NOT_OBSERVED_COMPLETE",
                     "completed": complete, "home_points": 31 if complete else None,
                     "away_points": 14 if complete else None, "home_margin": 17 if complete else None,
                     "total_points": 45 if complete else None, "winner": f"Home {year}" if complete else None,
                     "source_at": "2026-11-04T18:14:00Z"})
    return {"schema": INVENTORY_SCHEMA, "verified_at": "2026-11-05T01:00:00Z",
            "source_capture_started_at": "2026-11-04T18:13:00Z", "source_capture_completed_at": "2026-11-04T18:17:00Z",
            "source": {"name": "CollegeFootballData", "url": "https://collegefootballdata.com/"},
            "verification": {"official_originals_replayed": 6, "total_originals_replayed": 6,
                             "physical_objects_reverified": 18, "official_game_values_reconstructed": 3,
                             "provider_calls_during_review": 0},
            "qualifications": {"all_source_rows_retained": True, "independent_universal_completeness_proven": False,
                               "historical_model_input_availability_proven": False, "forecast_outputs_in_this_inventory": 0,
                               "original_replay_cohort_games_unchanged": 622},
            "seasons": [{"season": row["season"], "games": 1, "completed": int(row["completed"]),
                         "not_observed_complete": int(not row["completed"]), "pure_fbs_games": 1, "fbs_involving_games": 0}
                        for row in rows], "rows": rows}


def fixture_progress():
    stage = {"season": 2026, "wave": "headline", "observed_at": "2026-11-04T19:08:00Z",
             "processed_contracts": 20, "registered_contracts": 20, "remaining_contracts": 0,
             "available_historical_cutoff_rows": 11, "failed_cutoff_rows": 2, "empty_history_cutoff_rows": 3,
             "registered_pass_processed": True, "all_reads_successful_claimed": False,
             "elapsed_seconds": 120.1, "stage_remaining_seconds_estimate": 0.0,
             "status": "REGISTERED_PASS_PROCESSED_NOT_FULL_SUCCESS"}
    partial = {**stage, "season": 2025, "processed_contracts": 3, "registered_contracts": 20,
               "remaining_contracts": 17, "registered_pass_processed": False, "status": "PARTIAL_LOG_PROGRESS",
               "stage_remaining_seconds_estimate": 900.0}
    absent = {**stage, "season": 2024, "wave": "alternates", "processed_contracts": None,
              "registered_contracts": None, "remaining_contracts": None, "registered_pass_processed": False,
              "available_historical_cutoff_rows": None, "failed_cutoff_rows": None, "empty_history_cutoff_rows": None,
              "elapsed_seconds": None, "stage_remaining_seconds_estimate": None,
              "status": "NO_PROGRESS_RECORD_IN_ATTACHED_LOG"}
    return {"schema": PROGRESS_SCHEMA, "log_snapshot_at": "2026-11-05T01:00:00Z",
            "evidence_class": "ATTACHED_EXECUTION_LOG_SNAPSHOT_NOT_LIVE_PROCESS",
            "owner_completion_observed": False, "current_process_liveness": "UNKNOWN_FROM_STATIC_LOG",
            "numerical_history_replay_complete": False, "stages": [stage, partial, absent],
            "latest_successor": {"release": "V028", "status": "RECOVERABLE_PREDECESSOR_WAIT_DIAGNOSTIC",
                                 "exit_code": 2, "elapsed_seconds": 600.1, "collector_started": False,
                                 "reason": "ACTIVE_FBS_PREDECESSOR_PRESERVED"},
            "review_owner_fits": 0, "review_issued_forecasts": 0, "review_orders": 0}


class SourceInventoryTests(unittest.TestCase):
    def test_all_seasons_and_missing_result_are_retained(self):
        doc = fixture_inventory()
        self.assertIs(validate_inventory(doc), doc)
        self.assertEqual(len(doc["rows"]), 3)
        self.assertEqual(doc["rows"][2]["home_points"], None)

    def test_dropped_game_fails_count_closure(self):
        doc = fixture_inventory(); doc["rows"].pop()
        with self.assertRaisesRegex(ValueError, "denominator"):
            validate_inventory(doc)

    def test_duplicate_ordered_identity_rejected(self):
        doc = fixture_inventory(); doc["rows"][1] = copy.deepcopy(doc["rows"][0])
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            validate_inventory(doc)

    def test_private_or_provider_identity_fields_are_rejected(self):
        for field in ("id", "game_id", "home_id", "source_reference", "raw_bid_array"):
            doc = fixture_inventory(); doc["rows"][0][field] = "not-public"
            with self.assertRaisesRegex(ValueError, "public inventory game field"):
                validate_inventory(doc)

    def test_private_cloud_location_in_team_name_rejected(self):
        doc = fixture_inventory(); doc["rows"][0]["home"] = "s3://private/example"
        doc["rows"][0]["winner"] = doc["rows"][0]["home"]
        with self.assertRaisesRegex(ValueError, "Private material"):
            validate_inventory(doc)

    def test_naive_source_clock_is_rejected(self):
        doc = fixture_inventory(); doc["rows"][0]["source_at"] = "2026-11-04T18:14:00"
        with self.assertRaisesRegex(ValueError, "Naive"):
            validate_inventory(doc)

    def test_changed_source_clock_cannot_be_newer_than_capture(self):
        doc = fixture_inventory(); doc["rows"][0]["source_at"] = "2026-11-05T00:00:00Z"
        with self.assertRaisesRegex(ValueError, "outside its authenticated capture"):
            validate_inventory(doc)

    def test_margin_total_and_winner_are_actual_score_consistent(self):
        for field, value in (("home_margin", -17), ("total_points", 46), ("winner", "Away 2024")):
            doc = fixture_inventory(); doc["rows"][0][field] = value
            with self.assertRaisesRegex(ValueError, "coherence"):
                validate_inventory(doc)

    def test_missing_final_cannot_be_filled_with_zero(self):
        doc = fixture_inventory(); doc["rows"][2]["home_points"] = 0
        with self.assertRaisesRegex(ValueError, "cannot be invented"):
            validate_inventory(doc)

    def test_source_inventory_cannot_claim_forecasts_or_pregame_availability(self):
        for field, value in (("forecast_outputs_in_this_inventory", 1),
                             ("historical_model_input_availability_proven", True),
                             ("independent_universal_completeness_proven", True)):
            doc = fixture_inventory(); doc["qualifications"][field] = value
            with self.assertRaisesRegex(ValueError, "cannot imply"):
                validate_inventory(doc)

    def test_render_has_every_static_row_and_separate_markers(self):
        output = render_section(fixture_inventory(), fixture_progress())
        self.assertEqual(output.count('data-source-row="'), 3)
        self.assertNotIn('data-game="', output)
        self.assertIn("not per-game historical model predictions", output)
        self.assertIn('role="status" aria-live="polite"', output)
        self.assertIn("Actual home margin", output)
        self.assertIn("Actual total", output)
        self.assertIn("Failed / empty cutoff rows", output)
        self.assertIn("2 / 3", output)
        self.assertIn("Every official source row is still included", output)

    def test_markup_is_escaped_in_table_and_inline_json(self):
        inventory = fixture_inventory(); inventory["rows"][2]["home"] = "</script><x & y>"
        output = render_section(inventory, fixture_progress())
        self.assertNotIn("</script><x & y>", output)
        self.assertIn("&lt;/script&gt;&lt;x &amp; y&gt;", output)
        self.assertIn("\\u003c/script\\u003e", output)
        decoded = json.loads(render_payload(inventory, fixture_progress()))
        self.assertEqual(decoded["inventory"]["rows"][2]["home"], "</script><x & y>")

    def test_payload_omission_for_separate_static_integration(self):
        output = render_section(fixture_inventory(), fixture_progress(), embed_data=False)
        self.assertNotIn('<script type="application/json"', output)


class SourceProgressTests(unittest.TestCase):
    def test_processed_with_failures_and_absent_progress_remain_explicit(self):
        doc = fixture_progress()
        self.assertIs(validate_progress(doc), doc)
        self.assertTrue(doc["stages"][0]["registered_pass_processed"])
        self.assertFalse(doc["stages"][0]["all_reads_successful_claimed"])
        self.assertIsNone(doc["stages"][2]["processed_contracts"])

    def test_processed_cannot_claim_all_reads_successful(self):
        doc = fixture_progress(); doc["stages"][0]["all_reads_successful_claimed"] = True
        with self.assertRaisesRegex(ValueError, "Processed does not imply"):
            validate_progress(doc)

    def test_absent_progress_cannot_become_zero_success(self):
        doc = fixture_progress(); doc["stages"][2]["registered_pass_processed"] = True
        with self.assertRaisesRegex(ValueError, "Absent stage progress"):
            validate_progress(doc)

    def test_partial_work_cannot_be_called_processed(self):
        doc = fixture_progress(); doc["stages"][1]["registered_pass_processed"] = True
        with self.assertRaisesRegex(ValueError, "processed/partial"):
            validate_progress(doc)

    def test_counter_closure_and_duplicate_stages(self):
        doc = fixture_progress(); doc["stages"][1]["remaining_contracts"] = 16
        with self.assertRaisesRegex(ValueError, "counter closure"):
            validate_progress(doc)
        doc = fixture_progress(); doc["stages"].append(copy.deepcopy(doc["stages"][0]))
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            validate_progress(doc)

    def test_static_log_cannot_be_live_monitor_or_full_return(self):
        for field, value in (("current_process_liveness", "RUNNING"),
                             ("owner_completion_observed", True), ("numerical_history_replay_complete", True)):
            doc = fixture_progress(); doc[field] = value
            with self.assertRaisesRegex(ValueError, "cannot claim live"):
                validate_progress(doc)

    def test_forecasts_fits_and_orders_are_not_credited(self):
        for field in ("review_owner_fits", "review_issued_forecasts", "review_orders"):
            doc = fixture_progress(); doc[field] = 1
            with self.assertRaisesRegex(ValueError, "not an owner fit"):
                validate_progress(doc)

    def test_exit_two_diagnostic_cannot_be_promoted_to_collection(self):
        for field, value in (("exit_code", 0), ("collector_started", True), ("elapsed_seconds", 1)):
            doc = fixture_progress(); doc["latest_successor"][field] = value
            with self.assertRaisesRegex(ValueError, "cannot become collection success"):
                validate_progress(doc)

    def test_future_stage_clock_is_rejected(self):
        doc = fixture_progress(); doc["stages"][0]["observed_at"] = "2026-11-05T02:00:00Z"
        with self.assertRaisesRegex(ValueError, "later than the observed log"):
            validate_progress(doc)


def fixture_progress_v2():
    """Invented counts exercising a collection failure, not an owner result."""
    doc = fixture_progress()
    doc["schema"] = PROGRESS_SCHEMA_V2
    doc["latest_successor"] = {
        "release": "V030", "status": "AUTHENTICATED_PARTIAL_ACQUISITION",
        "exit_code": 2, "elapsed_seconds": 100.5, "collector_started": True,
        "reason": "CATALOG_REPORT_SIZE_LIMIT_AND_ERROR_CALLBACK_COLLISION"}
    doc["acquisition"] = {
        "new_native_requests": 20, "new_current_requests": 3,
        "total_new_requests": 23, "in_call_reuses": 11,
        "prior_raw_pending": 17, "prior_failed_observations": 5,
        "prior_raw_verified_reused": 0, "derived_report_commits": 2,
        "source_refresh_seconds": 8.0, "whole_run_eta_seconds": None}
    return doc


class CollectionFailureProgressTests(unittest.TestCase):
    def test_actual_collection_failure_has_separate_accounting(self):
        doc = fixture_progress_v2()
        self.assertIs(validate_progress(doc), doc)
        text = render_section(fixture_inventory(), doc)
        self.assertIn("23 new requests", text)
        self.assertIn("11 within-run dependency reuses", text)
        self.assertIn("catalog was saved", text)
        self.assertNotIn("It began no collection", text)
        self.assertIn("interrupted predecessor", text)

    def test_reuse_or_commits_cannot_be_counted_as_new_requests(self):
        for extra in (11, 2):
            doc = fixture_progress_v2()
            doc["acquisition"]["total_new_requests"] += extra
            with self.assertRaisesRegex(ValueError, "double-count"):
                validate_progress(doc)

    def test_pending_metadata_cannot_become_verified_or_eta(self):
        for key, value in (("prior_raw_verified_reused", 1), ("whole_run_eta_seconds", 60)):
            doc = fixture_progress_v2(); doc["acquisition"][key] = value
            with self.assertRaisesRegex(ValueError, "Pending metadata"):
                validate_progress(doc)

    def test_v2_cannot_be_success_or_no_collection(self):
        for key, value in (("exit_code", 0), ("collector_started", False), ("release", "V031")):
            doc = fixture_progress_v2(); doc["latest_successor"][key] = value
            with self.assertRaisesRegex(ValueError, "failed collection"):
                validate_progress(doc)

    def test_v2_rejects_extra_private_fields_and_noninteger_counts(self):
        doc = fixture_progress_v2(); doc["acquisition"]["private_source"] = "hidden"
        with self.assertRaisesRegex(ValueError, "Unknown acquisition"):
            validate_progress(doc)
        for value in (-1, True, 1.5):
            doc = fixture_progress_v2(); doc["acquisition"]["in_call_reuses"] = value
            with self.assertRaisesRegex(ValueError, "accounting"):
                validate_progress(doc)


if __name__ == "__main__":
    unittest.main()
