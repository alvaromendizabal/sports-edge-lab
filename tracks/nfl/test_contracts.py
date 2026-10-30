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


if __name__ == "__main__":
    unittest.main()
