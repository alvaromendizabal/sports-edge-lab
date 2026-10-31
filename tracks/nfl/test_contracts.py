"""Negative contracts and reproducible public evidence; standard library only."""
import copy
import json
import tempfile
import unittest
from pathlib import Path

import contracts


class AccountingTests(unittest.TestCase):
    def setUp(self):
        self.rows = [
            {"game_id": "A", "season": 2024, "phase": "REG", "date": "2024-09-01", "home_score": 20, "away_score": 17},
            {"game_id": "B", "season": 2024, "phase": "POST", "date": "2025-01-12", "home_score": 31, "away_score": 24},
            {"game_id": "T", "season": 2024, "phase": "REG", "date": "2024-11-01", "home_score": 17, "away_score": 17},
            {"game_id": "F", "season": 2026, "phase": "REG", "home_score": None, "away_score": None},
            {"game_id": "C", "season": 2022, "phase": "REG", "home_score": None, "away_score": None, "canceled": True},
        ]

    def test_outer_universe_retains_postseason_and_missing_predictions(self):
        result = contracts.reconcile_games(self.rows, ["A"], season=2024, target="win")
        self.assertEqual((result["accounted"], result["regular"], result["postseason"]), (3, 2, 1))
        self.assertEqual(result["missing_prediction"], 1)
        self.assertEqual(next(r["status"] for r in result["rows"] if r["game_id"] == "B"), "SCORED_WITHOUT_PREDICTION")

    def test_tie_is_accounted_and_point_target_eligibility_is_independent(self):
        win = contracts.reconcile_games(self.rows, ["A", "T"], season=2024, target="win")
        for target in ("margin", "total"):
            points = contracts.reconcile_games(self.rows, ["A", "T"], season=2024, target=target)
            self.assertEqual(points["accounted"], win["accounted"])
            self.assertEqual(points["ties"], 1)
            self.assertEqual(points["eligible"], win["eligible"] + 1)
            self.assertEqual(points["predicted_eligible"], 2)

    def test_unplayed_and_canceled_are_not_missing_scored_evaluations(self):
        future = contracts.reconcile_games(self.rows, [], season=2026, target="win")
        canceled = contracts.reconcile_games(self.rows, [], season=2022, target="total")
        self.assertEqual((future["unplayed"], future["missing_prediction"]), (1, 0))
        self.assertEqual((canceled["canceled"], canceled["scored"], canceled["missing_prediction"]), (1, 0, 0))

    def test_duplicate_or_unknown_identities_cannot_make_coverage_look_complete(self):
        with self.assertRaisesRegex(ValueError, "Duplicate schedule"):
            contracts.reconcile_games(self.rows + [self.rows[0]], [], season=2024, target="win")
        with self.assertRaisesRegex(ValueError, "Duplicate prediction"):
            contracts.reconcile_games(self.rows, ["A", "A"], season=2024, target="win")
        with self.assertRaisesRegex(ValueError, "outside schedule"):
            contracts.reconcile_games(self.rows, ["UNKNOWN"], season=2024, target="win")

    def test_partial_nonfinite_negative_and_invented_cancel_scores_rejected(self):
        for changes in ({"away_score": None}, {"home_score": float("nan")}, {"home_score": -1}, {"canceled": True}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                contracts.reconcile_games([{**self.rows[0], **changes}], [], season=2024, target="win")

    def test_inputs_are_not_mutated(self):
        original = copy.deepcopy(self.rows)
        contracts.reconcile_games(self.rows, ["A"], season=2024, target="margin")
        self.assertEqual(self.rows, original)


class CoordinatorTests(unittest.TestCase):
    def setUp(self):
        self.contract = {"schema": "sports-edge-lab.workspace-layout.v1", "layout_version": 1,
            "project_directories": sorted(contracts.PROJECTS),
            "required_project_subdirectories": sorted(contracts.SUBDIRECTORIES),
            "organization_lock": ".existing-coordinator.lock", "other_project_state": {"keep": True}}

    def test_filename_and_order_do_not_replace_semantic_admission(self):
        for name in ("workspace_layout.json", "workspace_layout_manifest.json"):
            value = copy.deepcopy(self.contract)
            value["project_directories"].reverse()
            result = contracts.admit_coordinator(value, filename=name)
            self.assertEqual(result["status"], "RECOGNIZED_REQUIRES_ACTUAL_LOCK")
            self.assertEqual(result["advertised_lock"], self.contract["organization_lock"])
            self.assertFalse(result["mutation_allowed"])

    def test_unknown_schema_layout_or_lock_is_preserved_and_deferred(self):
        for changes in ({"schema": "unknown"}, {"layout_version": 2}, {"layout_version": True},
                        {"project_directories": ["nfl"]}, {"organization_lock": "../other.lock"},
                        {"project_directories": [["nfl"], "nba", "ncaa_fbs", "ncaa_basketball"]},
                        {"required_project_subdirectories": [[], "config", "data", "runs", "notebooks", "reports", "releases", "archive"]}):
            value = {**self.contract, **changes}; before = copy.deepcopy(value)
            result = contracts.admit_coordinator(value, filename="workspace_layout.json")
            self.assertTrue(result["status"].startswith("DEFERRED"))
            self.assertFalse(result["mutation_allowed"])
            self.assertEqual(value, before)

    def test_successful_parse_preserves_unknown_fields_and_grants_no_mutation(self):
        before = copy.deepcopy(self.contract)
        result = contracts.admit_coordinator(self.contract, filename="other_name.json")
        self.assertEqual(self.contract, before)
        self.assertFalse(result["mutation_allowed"])
        self.assertIn("actual advertised lock", result["next_gate"])


class PublicEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((contracts.HERE / "evidence.json").read_text())

    def test_complete_public_aggregate_closure_and_generated_page(self):
        receipt = contracts.validate_evidence(self.data)
        self.assertEqual((receipt["prediction_tables"], receipt["metric_scalars"], receipt["game_identities"]), (316, 948, 7549))
        self.assertFalse(receipt["private_training_reproduced"])
        self.assertTrue(contracts.build_review(check=True)["generated_page_matches"])

    def test_equal_size_different_games_are_rejected(self):
        challenger = self.data["rows"][0]
        market = {**challenger, "metrics": challenger["market_metrics"], "cohort_sha256": "0" * 64}
        with self.assertRaisesRegex(ValueError, "cohort_sha256"):
            contracts.compare_panel(challenger, market)

    def test_protocol_target_and_season_cannot_be_pooled(self):
        challenger = self.data["rows"][0]
        for key, value in (("season", 2026), ("target", "other"), ("policy", "different"), ("games", 285)):
            with self.subTest(key=key), self.assertRaises(ValueError):
                contracts.compare_panel(challenger, {**challenger, "metrics": challenger["market_metrics"], key: value})

    def test_monitoring_never_authorizes_ranking_or_promotion(self):
        for row in self.data["rows"]:
            result = contracts.compare_panel(row, {**row, "metrics": row["market_metrics"]})
            self.assertFalse(result["promotion_authorized"])
            if row["season"] == 2026:
                self.assertFalse(result["ranking_permitted"])

    def test_tampered_count_identity_nonfinite_or_private_field_is_rejected(self):
        variants = []
        value = copy.deepcopy(self.data); value["rows"][0]["games"] = 285; variants.append(value)
        value = copy.deepcopy(self.data); value["rows"].append(copy.deepcopy(value["rows"][0])); variants.append(value)
        value = copy.deepcopy(self.data); value["rows"][0]["metrics"]["mae"] = float("nan"); variants.append(value)
        value = copy.deepcopy(self.data); value["private_path"] = "/home/owner/private-input"; variants.append(value)
        for value in variants:
            with self.subTest(index=variants.index(value)), self.assertRaises(ValueError):
                contracts.validate_evidence(value)

    def test_known_season_denominators_do_not_become_full_prediction_counts(self):
        seasons = {row["season"]: row for row in self.data["seasons"]}
        self.assertEqual((seasons[2024]["accounted"], seasons[2024]["retained"]), (285, 280))
        self.assertEqual((seasons[2025]["accounted"], seasons[2025]["retained"]), (285, 277))
        self.assertEqual((seasons[2022]["canceled"], seasons[2026]["future_postseason_expected"]), (1, 13))
        self.assertEqual(sum(row["absent_both_saved_tables"] for row in self.data["gap_counts"] if row["season"] < 2026), 22)


class WeeklyEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((contracts.HERE / "evidence.json").read_text())
        self.weekly = self.data["weekly_review"]
        self.seasons = {row["season"]: row for row in self.data["seasons"]}

    def test_complete_nfl_week_and_provider_slot_closure(self):
        before = copy.deepcopy(self.weekly)
        receipt = contracts.validate_weekly_review(self.weekly, self.seasons)
        self.assertEqual((receipt["season_week_slots"], receipt["provider_week_slots"]), (66, 330))
        self.assertEqual(self.weekly, before)
        for season in (2024, 2025):
            rows = [row for row in self.weekly["weeks"] if row["season"] == season]
            self.assertEqual(sum(r["games_scheduled"] for r in rows if r["nfl_week"].isdigit()), 272)
            self.assertEqual(sum(r["games_scheduled"] for r in rows if not r["nfl_week"].isdigit()), 13)

    def test_future_postseason_is_format_only_not_missing_completed_games(self):
        rows = [r for r in self.weekly["weeks"] if r["season"] == 2026]
        future = [r for r in rows if not r["nfl_week"].isdigit()]
        self.assertEqual(sum(r["expected_postseason_games_by_format"] for r in future), 13)
        self.assertEqual(sum(r["games_scheduled"] for r in future), 0)
        self.assertEqual(sum(r["unplayed_from_capture"] for r in rows), 165)
        self.assertTrue(all(r["schedule_status"] == "NO_CAPTURED_MATCHUPS_NO_IDS_INVENTED" for r in future))

    def test_saved_availability_remains_distinct_from_issued_forecasts(self):
        for year, expected in ((2024, 280), (2025, 277), (2026, 77)):
            rows = [r for r in self.weekly["weeks"] if r["season"] == year]
            self.assertEqual(sum(r["saved_win_binary"] for r in rows), expected)
            self.assertTrue(all(r["forecast_issued_verified"] is None for r in rows))
        self.weekly["weeks"][0]["forecast_issued_verified"] = 0
        with self.assertRaisesRegex(ValueError, "Unknown forecasts"):
            contracts.validate_weekly_review(self.weekly, self.seasons)

    def test_unknown_provider_coverage_cannot_inherit_market_or_zero_returns(self):
        self.assertEqual({r["provider"] for r in self.weekly["provider_weeks"]}, set(contracts.PROVIDERS))
        for field, value in (("matched_games", 0), ("roi", 0.0), ("brier", 0.2), ("quote_status", "VERIFIED")):
            sample = copy.deepcopy(self.weekly); sample["provider_weeks"][0][field] = value
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, "Unknown provider"):
                contracts.validate_weekly_review(sample, self.seasons)

    def test_duplicate_missing_or_calendar_week_identity_is_rejected(self):
        for table in ("weeks", "provider_weeks"):
            sample = copy.deepcopy(self.weekly); sample[table][-1] = copy.deepcopy(sample[table][0])
            with self.subTest(table=table), self.assertRaisesRegex(ValueError, "Duplicate"):
                contracts.validate_weekly_review(sample, self.seasons)
        self.weekly["weeks"][0]["nfl_week"] = "2024-W36"
        with self.assertRaisesRegex(ValueError, "unsupported NFL"):
            contracts.validate_weekly_review(self.weekly, self.seasons)

    def test_tie_as_binary_loss_and_unplayed_as_scored_are_rejected(self):
        tied = next(i for i,r in enumerate(self.weekly["weeks"]) if r["ties"])
        sample = copy.deepcopy(self.weekly)
        sample["weeks"][tied]["saved_win_binary"] = sample["weeks"][tied]["games_scored"]
        with self.assertRaisesRegex(ValueError, "eligibility"):
            contracts.validate_weekly_review(sample, self.seasons)
        future = next(i for i,r in enumerate(self.weekly["weeks"]) if r["unplayed_from_capture"])
        self.weekly["weeks"][future]["games_scored"] += 1
        with self.assertRaisesRegex(ValueError, "status closure"):
            contracts.validate_weekly_review(self.weekly, self.seasons)

    def test_historical_disk_failure_is_not_live_or_completed_owner_work(self):
        contracts.validate_owner_attempt(self.data)
        storage = self.data["n008_owner_attempt"]["storage"]
        self.assertEqual(storage["research_reserve_bytes"] - storage["available_bytes"], 833953792)
        for section, key, value in (("storage", "live_observation", True), ("attempt", "new_n004_fits", 0),
                                    ("attempt", "owner_cleanup_verified", True)):
            sample = copy.deepcopy(self.data)
            target = sample["n008_owner_attempt"]["storage"] if section == "storage" else sample["n008_owner_attempt"]
            target[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                contracts.validate_owner_attempt(sample)
        self.data["next_owner_execution"]["verified"] = True
        with self.assertRaisesRegex(ValueError, "Pending owner"):
            contracts.validate_owner_attempt(self.data)

    def test_private_fields_and_invented_economic_values_are_rejected(self):
        for key, value in (("settled_profit", 0.0), ("clv", 0.0), ("private_path", "/tmp/private")):
            sample = copy.deepcopy(self.data); sample["weekly_review"]["weeks"][0][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                contracts.validate_evidence(sample)


class DemoReentryTests(unittest.TestCase):
    def test_fresh_and_resumed_demo_preserves_identity_and_mtime(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "demo.json"
            created = contracts.demo(output=path)
            before = (path.read_bytes(), path.stat().st_mtime_ns)
            resumed = contracts.demo(output=path)
            self.assertEqual(created["status"], "CREATED")
            self.assertEqual(resumed["status"], "REUSED")
            self.assertEqual(resumed["new_work_units"], 0)
            self.assertEqual(created["artifact_sha256"], resumed["artifact_sha256"])
            self.assertEqual(before, (path.read_bytes(), path.stat().st_mtime_ns))
            self.assertTrue(json.loads(path.read_text())["synthetic"])

    def test_corrupt_prior_artifact_is_preserved_and_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "demo.json"
            contracts.demo(output=path)
            value = json.loads(path.read_text()); value["win"]["missing_prediction"] = 0
            path.write_text(json.dumps(value)); before = path.read_bytes()
            with self.assertRaisesRegex(ValueError, "changed or corrupted"):
                contracts.demo(output=path)
            self.assertEqual(path.read_bytes(), before)


class InformationTimeTests(unittest.TestCase):
    def setUp(self):
        self.cases = contracts.temporal_demo_cases()["cases"]
        self.complete = next(row["arguments"] for row in self.cases
                             if row["scenario"] == "complete" and row["decision_hours_before"] == 1)

    def test_later_source_boundary_is_insufficient_not_proved_future_use(self):
        row = next(row for row in self.cases if row["scenario"] == "origin_bound" and row["decision_hours_before"] == 1)
        audit = row["audit"]
        self.assertEqual(audit["status"], "NOT_ESTABLISHED_FOR_POLICY")
        self.assertEqual(audit["checks"]["source_bound"], "INSUFFICIENT_FOR_EARLIER_POLICY")
        self.assertEqual(audit["checks"]["model_availability"], "UNVERIFIED")
        self.assertFalse(audit["known_late_input_or_label"])
        self.assertFalse(audit["actual_fit_time_inferred_from_source_cutoff"])
        self.assertFalse(audit["source_timestamp_rewritten"])

    def test_complete_invented_evidence_can_pass_without_claiming_real_forecast(self):
        result = contracts.audit_information_time(**self.complete)
        self.assertEqual(result["status"], "DEMO_ADMISSIBLE")
        self.assertTrue(result["synthetic"])
        self.assertFalse(result["real_forecast_issued"])

    def test_explicit_earlier_decision_cannot_be_relaxed_to_the_day_before(self):
        result = contracts.audit_information_time(**{**self.complete, "decision_at": "2025-10-31T18:00:00Z"})
        self.assertEqual(result["effective_policy_at"], "2025-10-31T18:00:00+00:00")
        self.assertEqual(result["status"], "NOT_ESTABLISHED_FOR_POLICY")
        self.assertTrue(result["known_late_input_or_label"])

    def test_source_bound_and_input_equality_fail_strict_information_rule(self):
        for field in ("source_training_cutoff_at", "latest_input_available_at", "latest_label_available_at"):
            with self.subTest(field=field):
                result = contracts.audit_information_time(**{**self.complete, field: "2025-11-01T18:00:00Z"})
                self.assertEqual(result["status"], "NOT_ESTABLISHED_FOR_POLICY")

    def test_completion_is_separate_and_can_be_available_exactly_at_policy(self):
        at_policy = {**self.complete, "model_completed_at": "2025-11-01T18:00:00Z"}
        self.assertEqual(contracts.audit_information_time(**at_policy)["status"], "DEMO_ADMISSIBLE")
        after = {**self.complete, "model_completed_at": "2025-11-01T18:00:01Z"}
        result = contracts.audit_information_time(**after)
        self.assertEqual(result["checks"]["model_availability"], "COMPLETED_AFTER_POLICY")
        self.assertEqual(result["checks"]["source_bound"], "STRICTLY_BEFORE_POLICY")
        self.assertFalse(result["known_late_input_or_label"])

    def test_known_late_input_or_label_is_distinct_from_insufficient_bound(self):
        for key in ("latest_input_available_at", "latest_label_available_at"):
            with self.subTest(key=key):
                result = contracts.audit_information_time(**{**self.complete, key: "2025-11-01T19:00:00Z"})
                self.assertTrue(result["known_late_input_or_label"])
                self.assertEqual(result["checks"]["source_bound"], "STRICTLY_BEFORE_POLICY")

    def test_missing_clock_never_gets_inferred_from_a_different_clock(self):
        for key in ("source_training_cutoff_at", "latest_input_available_at", "latest_label_available_at", "model_completed_at"):
            with self.subTest(key=key):
                result = contracts.audit_information_time(**{**self.complete, key: None})
                self.assertEqual(result["status"], "NOT_ESTABLISHED_FOR_POLICY")
                self.assertIsNone(result["source_clocks"][key])

    def test_timezone_equivalent_instants_have_identical_admission(self):
        equivalent = {**self.complete, "model_completed_at": "2025-11-01T10:30:00-07:00"}
        first = contracts.audit_information_time(**self.complete)
        second = contracts.audit_information_time(**equivalent)
        self.assertEqual(first["checks"], second["checks"])
        self.assertEqual(first["effective_policy_at"], second["effective_policy_at"])
        self.assertEqual(second["source_clocks"]["model_completed_at"], equivalent["model_completed_at"])

    def test_naive_malformed_or_nonpregame_clock_rejected(self):
        for clock in ("2025-11-01", "2025-11-01T17:00:00", "bad-clock", 0):
            with self.subTest(clock=clock), self.assertRaises(ValueError):
                contracts.audit_information_time(**{**self.complete, "model_completed_at": clock})
        with self.assertRaisesRegex(ValueError, "precede kickoff"):
            contracts.audit_information_time(**{**self.complete, "decision_at": self.complete["kickoff_at"]})

    def test_audit_preserves_inputs_and_committed_case_results_are_executable(self):
        original = copy.deepcopy(self.complete)
        contracts.audit_information_time(**self.complete)
        self.assertEqual(original, self.complete)
        self.assertEqual(len(self.cases), 12)
        data = json.loads((contracts.HERE / "evidence.json").read_text())
        self.assertEqual(data["information_time_demo"], contracts.temporal_demo_cases())
        data["information_time_demo"]["cases"][0]["audit"]["status"] = "DEMO_ADMISSIBLE"
        with self.assertRaisesRegex(ValueError, "timing audit"):
            contracts.validate_evidence(data)


class OwnerRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((contracts.HERE / "evidence.json").read_text())

    def test_authenticated_recovery_does_not_claim_completed_new_science(self):
        contracts.validate_owner_attempt(self.data)
        attempt = self.data["n009_owner_attempt"]
        self.assertEqual(attempt["tests"]["inherited"] + attempt["tests"]["n009"], 909)
        self.assertEqual(attempt["completed_n004_job_receipts"], 0)
        self.assertIsNone(attempt["new_n004_fits"])
        self.assertEqual(self.data["owner_latest_success"], "N006")

    def test_allocated_recovery_is_not_logical_compression_or_shared_delta(self):
        recovery = self.data["n009_owner_attempt"]["storage_recovery"]
        reclaimed = recovery["attributed_allocated_bytes_reclaimed"]
        self.assertEqual(reclaimed, 15383494656)
        self.assertNotEqual(reclaimed, recovery["source_logical_bytes"] - recovery["archive_logical_bytes"])
        self.assertNotEqual(reclaimed, recovery["observed_shared_available_after_bytes"] - recovery["observed_shared_available_before_bytes"])
        for key, value in (("attributed_allocated_bytes_reclaimed", reclaimed + 4096),
                           ("independent_full_decompression_verified", False)):
            sample = copy.deepcopy(self.data); sample["n009_owner_attempt"]["storage_recovery"][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                contracts.validate_owner_attempt(sample)

    def test_missing_fit_measurements_and_dated_capacity_stay_unknown(self):
        for section, key, value in (("attempt", "new_n004_fits", 0),
                                    ("storage", "live_observation", True),
                                    ("storage", "new_execution_allocated_bytes", 0),
                                    ("storage", "shared_free_space_is_exclusively_nfl", True)):
            sample = copy.deepcopy(self.data)
            target = sample["n009_owner_attempt"] if section == "attempt" else sample["n009_owner_attempt"]["storage_final"]
            target[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                contracts.validate_owner_attempt(sample)

    def test_failure_diagnostic_preserves_all_previously_authenticated_results(self):
        before = copy.deepcopy(self.data)
        receipt = contracts.preserved_result_receipt(self.data)
        self.assertEqual(receipt["status"], "ACCEPTED_RESULTS_PRESERVED")
        self.assertEqual((receipt["model_panels"], receipt["metric_scalars"], receipt["season_week_slots"], receipt["provider_week_states"]),
                         (316, 948, 66, 330))
        self.assertFalse(receipt["latest_diagnostic_replaces_results"])
        self.assertEqual(self.data, before)

    def test_changed_or_empty_fallback_cannot_replace_valid_previous_panels(self):
        for changes in ({"rows": []}, {"rows": self.data["rows"][:-1]},
                        {"weekly_review": {**self.data["weekly_review"], "weeks": []}}):
            with self.subTest(changes=list(changes)), self.assertRaisesRegex(ValueError, "Preserved"):
                contracts.preserved_result_receipt({**self.data, **changes})


class LatestOwnerBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.data=json.loads((contracts.HERE / "evidence.json").read_text())

    def test_latest_disk_failure_keeps_prior_results_and_null_stage_counts(self):
        contracts.validate_evidence(self.data)
        self.assertEqual(contracts.preserved_result_receipt(self.data)["latest_attempt"], "N010")

    def test_earlier_cleanup_cannot_be_counted_again(self):
        self.data["n010_owner_attempt"]["new_reclamation_bytes"]=15383494656
        with self.assertRaisesRegex(ValueError,"reclamation"):
            contracts.validate_owner_attempt(self.data)

    def test_preparation_cannot_claim_owner_retirement(self):
        self.data["n011_preparation"]["new_owner_reclamation_bytes"]=2527780864
        with self.assertRaisesRegex(ValueError,"Preparation"):
            contracts.validate_owner_attempt(self.data)

    def test_snapshot_duplication_cannot_inflate_outcomes(self):
        self.data["execution_outcomes"]["rows"].append({"release":"N003","outcome":"SUCCESS_RESEARCH"})
        with self.assertRaisesRegex(ValueError,"Deduplicated"):
            contracts.validate_owner_attempt(self.data)


class FeatureConsumerParityTests(unittest.TestCase):
    def setUp(self):
        self.reference = contracts.invented_feature_view()
        self.candidate = copy.deepcopy(self.reference)

    def test_identical_invented_view_passes_without_owner_migration_claim(self):
        receipt = contracts.compare_feature_consumers(self.reference, self.candidate)
        self.assertEqual(receipt["status"], "EXACT_SUPPLIED_VIEW_PARITY")
        self.assertEqual((receipt["rows"], receipt["columns"]), (2, 2))
        self.assertTrue(receipt["synthetic_example"])
        self.assertFalse(receipt["full_owner_migration_verified"])

    def test_physical_row_order_does_not_change_keyed_semantics(self):
        self.candidate["rows"].reverse()
        self.assertEqual(contracts.feature_view_identity(self.reference),
                         contracts.feature_view_identity(self.candidate))

    def test_equal_rows_and_columns_do_not_hide_a_changed_value(self):
        self.candidate["rows"][0]["values"][0] = 9.5
        with self.assertRaisesRegex(ValueError, "semantics differ"):
            contracts.compare_feature_consumers(self.reference, self.candidate)

    def test_missingness_is_not_zero(self):
        self.candidate["rows"][1]["values"][0] = 0.0
        with self.assertRaisesRegex(ValueError, "semantics differ"):
            contracts.compare_feature_consumers(self.reference, self.candidate)

    def test_ordered_model_columns_cannot_be_silently_reordered(self):
        self.candidate["columns"].reverse()
        for row in self.candidate["rows"]:
            row["values"].reverse()
        with self.assertRaisesRegex(ValueError, "semantics differ"):
            contracts.compare_feature_consumers(self.reference, self.candidate)

    def test_fold_dataset_and_transform_identity_cannot_change(self):
        for key in ("fold_id", "dataset_version", "transform_version"):
            candidate = copy.deepcopy(self.reference)
            candidate[key] = "different-invented-identity"
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, "semantics differ"):
                contracts.compare_feature_consumers(self.reference, candidate)

    def test_changed_availability_clock_fails_parity(self):
        self.candidate["rows"][0]["available_at"] = "2025-01-01T00:00:01Z"
        with self.assertRaisesRegex(ValueError, "semantics differ"):
            contracts.compare_feature_consumers(self.reference, self.candidate)

    def test_timezone_equivalent_clocks_match(self):
        self.candidate["rows"][0]["available_at"] = "2024-12-31T16:00:00-08:00"
        contracts.compare_feature_consumers(self.reference, self.candidate)

    def test_repeated_event_and_column_names_are_rejected(self):
        self.candidate["rows"].append(copy.deepcopy(self.candidate["rows"][0]))
        with self.assertRaisesRegex(ValueError, "event identity"):
            contracts.feature_view_identity(self.candidate)
        self.candidate = copy.deepcopy(self.reference)
        self.candidate["columns"][1]["name"] = self.candidate["columns"][0]["name"]
        with self.assertRaisesRegex(ValueError, "Duplicate feature columns"):
            contracts.feature_view_identity(self.candidate)

    def test_nonfinite_boolean_as_numeric_and_wrong_width_rejected(self):
        for value in (float("nan"), float("inf"), True, "1.5"):
            candidate = copy.deepcopy(self.reference)
            candidate["rows"][0]["values"][0] = value
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, "dtype"):
                contracts.feature_view_identity(candidate)
        self.candidate["rows"][0]["values"].append(3)
        with self.assertRaisesRegex(ValueError, "ordered columns"):
            contracts.feature_view_identity(self.candidate)

    def test_namespace_and_naive_clocks_are_rejected(self):
        self.candidate["project"] = "nba"
        with self.assertRaisesRegex(ValueError, "namespace"):
            contracts.feature_view_identity(self.candidate)
        self.candidate = copy.deepcopy(self.reference)
        self.candidate["rows"][0]["available_at"] = "2025-01-01T00:00:00"
        with self.assertRaisesRegex(ValueError, "timezone"):
            contracts.feature_view_identity(self.candidate)

    def test_inputs_unchanged_and_demo_carries_qualified_parity(self):
        original = copy.deepcopy(self.reference)
        contracts.compare_feature_consumers(self.reference, self.candidate)
        self.assertEqual(self.reference, original)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "demo.json"
            contracts.demo(output=path)
            output = json.loads(path.read_text())
            self.assertEqual(output["schema"], "sports-edge-lab.nfl.demo.v3")
            self.assertFalse(output["feature_consumer_parity"]["full_owner_migration_verified"])


class SharedMaintenanceBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((contracts.HERE / "evidence.json").read_text())

    def test_shared_maintenance_does_not_alter_nfl_outcomes_or_results(self):
        contracts.validate_evidence(self.data)
        self.assertEqual(self.data["execution_outcomes"]["authenticated_invocations"], 6)
        self.assertEqual(self.data["next_owner_execution"], {"release": "N012", "verified": False})
        self.assertEqual(contracts.preserved_result_receipt(self.data)["metric_scalars"], 948)

    def test_cleanup_cannot_be_credited_as_science_or_feature_migration(self):
        for key, value in (("nfl_scientific_success_credit", 1),
                           ("feature_consumer_parity_established_by_cleanup", True)):
            data = copy.deepcopy(self.data)
            data["latest_shared_maintenance"][key] = value
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, "Shared maintenance"):
                contracts.validate_owner_attempt(data)

    def test_completed_cleanup_cannot_restart_or_restore_sprawl(self):
        for key in ("global_cleanup_to_repeat", "restore_full_legacy_roots", "whole_workspace_cleanup_claimed"):
            data = copy.deepcopy(self.data); data["latest_shared_maintenance"][key] = True
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, "Completed scoped cleanup"):
                contracts.validate_owner_attempt(data)

    def test_catalog_records_cannot_become_feature_columns(self):
        self.data["latest_shared_maintenance"]["catalog_records_are_engineered_columns"] = True
        with self.assertRaisesRegex(ValueError, "Catalog members"):
            contracts.validate_owner_attempt(self.data)

    def test_dated_storage_cannot_become_live_or_nfl_exclusive(self):
        for key in ("live_observation", "current_storage_measured", "shared_change_attributed_exclusively_to_nfl"):
            data = copy.deepcopy(self.data); data["latest_shared_maintenance"]["storage"][key] = True
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, "Uploaded shared snapshot"):
                contracts.validate_owner_attempt(data)

    def test_preparation_cannot_become_owner_science(self):
        for key, value in (("owner_executed", True), ("new_owner_fits", 126),
                           ("owner_feature_consumer_parity_verified", True),
                           ("owner_scientific_improvement_verified", True)):
            data = copy.deepcopy(self.data); data["n012_preparation"][key] = value
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, "N012 preparation"):
                contracts.validate_owner_attempt(data)

    def test_current_season_cannot_become_fit_or_selection_data(self):
        for key, value in (("current_season_estimator_fit_excluded", False),
                           ("current_season_adaptive_selection", True), ("fold_specific_fitted_transforms", False)):
            data = copy.deepcopy(self.data); data["n012_preparation"][key] = value
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, "Current-season"):
                contracts.validate_owner_attempt(data)

    def test_schedule_observation_cannot_become_quotes_or_paper_economics(self):
        for key, value in (("qualified_forecasts", 1), ("verified_provider_quotes", 1),
                           ("frozen_historical_rows_modified", True)):
            data = copy.deepcopy(self.data); data["official_schedule_observation"][key] = value
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, "Public schedule observation"):
                contracts.validate_owner_attempt(data)
        for key in ("actual_last_week_pnl", "reconstructed_last_week_pnl", "paper_remaining_budget"):
            data = copy.deepcopy(self.data); data["official_schedule_observation"][key] = 0
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, "Unverified issued history"):
                contracts.validate_owner_attempt(data)


if __name__ == "__main__":
    unittest.main()
