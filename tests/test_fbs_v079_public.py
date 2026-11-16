"""Verify public FBS populations and publication boundaries, without owner work."""
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import unittest
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
SITE = Path(os.environ.get("FBS_V079_SITE", ROOT / "docs/fbs/v079"))

def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

class PublicV079(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((SITE / "data/review.json").read_text())
        cls.games = json.loads(gzip.decompress((SITE / "data/games.json.gz").read_bytes()))["games"]
        cls.full = cls.data["full_population"]

    def test_validation_test_contract_never_auto_promotes(self):
        c = self.data["population_contract"]
        self.assertEqual(c["validation_seasons"], [2024, 2025])
        self.assertEqual(c["test_season"], 2026)
        self.assertFalse(self.data["promotion"])
        self.assertFalse(self.full["promotion"])
        self.assertFalse(self.full["test_untouched"])

    def test_all_game_inventory_has_unique_identities_and_exact_denominators(self):
        self.assertEqual(len(self.games), len({(g["season"], g["id"]) for g in self.games}))
        self.assertEqual({g["season"] for g in self.games}, {2024, 2025, 2026})
        for p in self.full["populations"]:
            finals = sorted(g["id"] for g in self.games if g["season"] == p["season"] and g["status"] == "final")
            self.assertEqual(len(finals), p["expected_game_count"])
            if p["cohort_sha256"]:
                self.assertEqual(digest(finals), p["cohort_sha256"])

    def test_every_scorecard_declares_the_fixed_population(self):
        population = {p["season"]: p for p in self.full["populations"]}
        identities = set()
        for r in self.full["scorecards"]:
            key = (r["model_alias"], r["target"], r["season"], r["evidence_class"])
            self.assertNotIn(key, identities); identities.add(key)
            self.assertEqual(r["expected_n"], r["scored_n"] + r["missing_n"])
            if r["complete_coverage"]:
                self.assertEqual(r["scored_n"], population[r["season"]]["expected_game_count"])
                self.assertEqual(r["cohort_sha256"], population[r["season"]]["cohort_sha256"])
                self.assertTrue(r["same_population"])
            else:
                self.assertFalse(r["eligible_for_ranking"])
                self.assertEqual(r["metrics"], {})

    def test_pending_report_has_no_invented_score(self):
        if self.full["state"] == "AWAITING_OWNER_FULL_POPULATION_REPORT":
            self.assertEqual(self.full["scorecards"], [])
            self.assertEqual(self.full["models"], [])
            self.assertIn("pending", (SITE / "index.html").read_text().lower())

    def test_all_provider_products_targets_and_missing_cells_remain(self):
        expected = {"draftkings", "kalshi", "polymarket_global", "polymarket_us"}
        for g in self.games:
            self.assertEqual(set(g["providers"]), expected)
            for cells in g["providers"].values():
                self.assertEqual(set(cells), {"winner", "margin", "total"})
                for cell in cells.values():
                    if cell and cell.get("value") is not None:
                        self.assertTrue(cell["display_eligible"])
                        self.assertTrue(cell["identity_matched_reference"])
                        self.assertTrue(cell["observed_reference"])
                        self.assertTrue(cell["quote_time"])
                        self.assertTrue(cell["observation_time"])

    def test_paired_statistics_keep_population_and_uncertainty_limits(self):
        population = {p["season"]: p for p in self.full["populations"]}
        for r in self.full.get("paired_comparisons", []):
            self.assertEqual(r["n"], population[r["season"]]["expected_game_count"])
            self.assertEqual(r["cohort_sha256"], population[r["season"]]["cohort_sha256"])
            self.assertFalse(r["multiplicity_adjusted"])
            self.assertFalse(r["team_dependence_validated"])
            self.assertFalse(r["promotion"])
        for r in self.full.get("descriptive_weighted_skill", []):
            self.assertFalse(r["used_for_nomination"])
            self.assertFalse(r["promotion"])

    def test_preserved_blocked_models_are_visible_without_fake_metrics(self):
        for r in self.full.get("preserved_roster_coverage", {}).get("records", []):
            self.assertTrue(r["model_alias"])
            self.assertNotIn("model_id", r)
            for c in r["season_cells"]:
                self.assertLessEqual(c["scored_n"], c["expected_n"])
                if c["complete_coverage"]:
                    self.assertEqual(c["scored_n"], c["expected_n"])

    def test_receipt_binds_every_declared_asset(self):
        receipt = json.loads((SITE / "BUILD_RECEIPT.json").read_text())
        self.assertEqual(receipt["game_count"], len(self.games))
        self.assertEqual(receipt["scorecard_count"], len(self.full["scorecards"]))
        self.assertEqual(receipt["new_science_by_publication"], 0)
        for entry in receipt["files"]:
            raw = (SITE / entry["path"]).read_bytes()
            self.assertEqual((len(raw), hashlib.sha256(raw).hexdigest()), (entry["bytes"], entry["sha256"]))

    def test_derived_provider_values_keep_source_evidence_separate(self):
        for g in self.games:
            for field in ("current_provider_coverage", "historical_provider_coverage"):
                for provider, targets in g.get(field, {}).items():
                    for target, cell in targets.items():
                        self.assertNotIn("provider_event_id", cell)
                        self.assertNotIn("source_receipt_sha256", cell)
                        if cell.get("display_value") is not None:
                            self.assertEqual((provider, target), ("draftkings", "winner"))
                            self.assertTrue(cell["display_eligible"])
                            self.assertTrue(cell["predictive_baseline_qualified"])
                            self.assertTrue(cell["quote_time"])
                            self.assertTrue(cell["observation_time"])
                            self.assertGreaterEqual(cell["display_value"], 0)
                            self.assertLessEqual(cell["display_value"], 1)
                        if field == "historical_provider_coverage":
                            self.assertFalse(cell["historical_source_possession_proven"])

    def test_market_diagnostics_never_change_model_population(self):
        report = self.data.get("market_comparison", {})
        cohorts = {(c["season"], c["provider"], c["target"]): c for c in report.get("provider_cohorts", [])}
        population = {p["season"]: p for p in self.full["populations"]}
        for c in cohorts.values():
            self.assertEqual(c["expected_n"], population[c["season"]]["expected_game_count"])
            self.assertEqual(c["full_population_cohort_sha256"], population[c["season"]]["cohort_sha256"])
            self.assertEqual(c["paired_n"] + c["missing_market_n"], c["expected_n"])
        for r in report.get("scorecards", []):
            c = cohorts[(r["season"], r["provider"], r["target"])]
            self.assertEqual(r["paired_cohort_sha256"], c["paired_cohort_sha256"])
            self.assertEqual(r["paired_n"], c["paired_n"])
            self.assertFalse(r["used_for_nomination"])
            if r["model_complete_on_provider_cohort"]:
                self.assertEqual(r["model_scored_n"], c["paired_n"])
            else:
                self.assertEqual(r["model_metrics"], {})

    def test_v080_current_forecasts_are_separate_from_earlier_issues(self):
        current = self.data["current_execution"]
        self.assertEqual((self.data["execution_version"], self.data["report_version"]), ("V080", "V079"))
        self.assertEqual(self.data["prior_execution"]["version"], "V078")
        future = [g for g in self.games if g["season"] == 2026 and g["status"] == "pending"]
        self.assertEqual(len(future), current["timed_future_games"])
        self.assertEqual(current["covered_timed_future_games"], len(future))
        self.assertEqual(current["verified_current_base_issue_records"], sum(g["issued_rows"] for g in future))
        self.assertEqual(current["verified_current_base_issue_records"], current["base_recipe_target_count"] * len(future))
        self.assertEqual(current["verified_current_derived_issue_records"], current["derived_recipe_target_count"] * len(future))
        self.assertEqual(current["verified_current_total_issue_records"], current["verified_current_base_issue_records"] + current["verified_current_derived_issue_records"])
        self.assertEqual(self.data["forecast_coverage"]["total_current_forecast_rows"], current["verified_current_total_issue_records"])
        self.assertFalse(current["private_candidate_grid_published"])
        self.assertTrue(current["fit_calls_do_not_establish_novel_models"])
        self.assertEqual(current["avoidable_duplicate_base_fit_calls"], current["base_fit_calls"])
        self.assertIn("were avoidable", current["duplicate_fit_disclosure"])
        self.assertFalse(current["promotion"])
        dt = lambda value: datetime.fromisoformat(value.replace("Z", "+00:00"))
        seen = 0
        for game in future:
            for target in ("winner", "margin", "total"):
                cell = game["audit_model"][target]
                self.assertIsNotNone(cell["value"])
                self.assertEqual(cell["issue_time"], current["base_issue_at"])
                self.assertLessEqual(dt(cell["information_cutoff"]), dt(cell["fit_completed_at"]))
                self.assertLessEqual(dt(cell["fit_completed_at"]), dt(cell["prepared_at"]))
                self.assertLessEqual(dt(cell["prepared_at"]), dt(cell["issue_time"]))
                self.assertLess(dt(cell["issue_time"]), dt(cell["requested_horizon_cutoff"]))
                seen += 1
        self.assertEqual(seen, current["selected_public_forecast_cells"])

    def test_negative_market_finding_is_supported_on_every_fixed_cohort(self):
        rows = [r for r in self.data["market_comparison"]["scorecards"] if r["provider"] == "draftkings" and r["target"] == "winner"]
        self.assertEqual({r["season"] for r in rows}, {2024, 2025, 2026})
        for row in rows:
            self.assertEqual(row["status"], "SAME_PROVIDER_COHORT_COMPARED")
            self.assertGreater(row["delta_model_minus_market"]["log_loss"], 0)
            self.assertGreater(row["delta_model_minus_market"]["brier"], 0)
            self.assertLess(row["delta_model_minus_market"]["accuracy"], 0)
            self.assertFalse(row["used_for_nomination"])
        self.assertIn("all 11", self.data["current_execution"]["same_provider_cohort_finding"])

    def test_public_scope_and_non_owner_preservation(self):
        forbidden = re.compile(r's3://|arn:aws:|/home/sagemaker-user|/workspace/|AKIA[0-9A-Z]{16}|BEGIN (?:RSA |EC )?PRIVATE KEY|"(?:original_model_id|model_id|fit_id|model_state_sha256|state_sha256|coefficients|feature_names|prediction_records)"')
        for path in SITE.rglob("*"):
            if not path.is_file(): continue
            self.assertNotIn(path.suffix, {".pyz", ".zip", ".parquet", ".pkl", ".pt", ".onnx"})
            raw = gzip.decompress(path.read_bytes()) if path.suffix == ".gz" else path.read_bytes()
            self.assertIsNone(forbidden.search(raw.decode()), path.name)
            self.assertNotIn(("cir" + "ca").encode(), raw.lower())

if __name__ == "__main__":
    unittest.main(verbosity=2)
