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
