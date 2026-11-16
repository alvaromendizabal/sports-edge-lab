"""Verify public FBS populations and publication boundaries, without owner work."""
import gzip
import hashlib
import json
import math
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
        cls.nominees = json.loads((SITE / "data/validation-nominees.json").read_text())

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
            for provider in ("kalshi", "polymarket_global", "polymarket_us"):
                for cell in g.get("providers", {}).get(provider, {}).values():
                    self.assertTrue(not cell or cell.get("value") is None)
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

    def test_all_54_current_draftkings_values_keep_their_own_snapshot_clocks(self):
        dt = lambda value: datetime.fromisoformat(value.replace("Z", "+00:00"))
        captured = dt(self.data["current_source_coverage"]["evaluated_at"])
        displayed = []
        for game in self.games:
            current = game.get("current_provider_coverage", {}).get("draftkings", {}).get("winner", {})
            if not current.get("display_eligible"):
                continue
            self.assertEqual((game["season"], game["status"]), (2026, "pending"))
            self.assertTrue(current["reference_present"])
            self.assertTrue(current["predictive_baseline_qualified"])
            self.assertIsInstance(current["display_value"], (int, float))
            self.assertLessEqual(dt(current["quote_time"]), dt(current["observation_time"]))
            self.assertLessEqual(dt(current["observation_time"]), captured)
            self.assertGreaterEqual((dt(game["kickoff"]) - dt(current["observation_time"])).total_seconds(), 7200)
            displayed.append(current)
        self.assertEqual(len(displayed), 54)
        self.assertEqual(len(displayed), self.data["current_source_coverage"]["displayed_probability_cells"])
        # Fixture refresh and provider capture are different events with separate clocks.
        self.assertGreater(captured, dt(self.data["fixture_source_as_of"]))

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

    def test_v080r1_current_forecasts_are_separate_from_earlier_issues(self):
        current = self.data["current_execution"]
        self.assertEqual((self.data["execution_version"], self.data["report_version"]), ("V080R1", "V079"))
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
        dated = self.data["previous_execution_audits"][0]
        self.assertEqual((dated["version"], dated["base_fit_calls"], dated["avoidable_duplicate_base_fit_calls"]), ("V080", 26, 26))
        self.assertIn("were avoidable", dated["disclosure"])
        self.assertTrue(dated["current_execution_counts_unchanged"])
        self.assertEqual(current["verified_current_base_issue_records"], current["new_base_issue_records"] + current["reused_base_issue_records"])
        self.assertEqual(current["verified_current_derived_issue_records"], current["new_derived_issue_records"] + current["reused_derived_issue_records"])
        milestone = current["secondary_feature_milestone"]
        self.assertEqual(milestone["team_context_rows"], 2 * milestone["pending_games"])
        self.assertEqual(milestone["eligible_future_team_rows"], 2 * len(future))
        self.assertFalse(milestone["feature_ablation_performed"])
        self.assertFalse(milestone["metric_improvement_claimed"])
        self.assertIn("V078 predecessor", self.data["prior_execution"]["summary"])
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

    def test_additional_12_study_targets_cover_the_identical_three_populations(self):
        report = self.data["current_study"]
        self.assertEqual(report["state"], "CORRECTED_T120_RESEARCH_RECONSTRUCTION_ATTACHED")
        self.assertEqual(len(report["rows"]), 12)
        self.assertEqual(len(report["original_rows"]), 12)
        self.assertEqual(sum(r["role"] == "negative_control" for r in report["rows"]), 3)
        self.assertEqual({r["alias"] for r in report["rows"]}, {prefix + f"{i:02d}" for prefix in ("RW", "RM", "RT") for i in range(1, 5)})
        populations = {p["season"]: p for p in self.full["populations"]}
        for lane in ("rows", "original_rows"):
            for row in report[lane]:
                self.assertFalse(row["nomination_eligible"])
                self.assertFalse(row["promotion"])
                self.assertEqual(row["corrected_t120_gate_passed"], lane == "rows")
                self.assertEqual({c["season"] for c in row["season_cards"]}, {2024, 2025, 2026})
                for card in row["season_cards"]:
                    self.assertEqual((card["n"], card["cohort_sha256"]), (populations[card["season"]]["expected_game_count"], populations[card["season"]]["cohort_sha256"]))
                    self.assertTrue(all(isinstance(value, (int, float)) and math.isfinite(value) for value in card["metrics"].values()))
        self.assertFalse(report["ranking_allowed"])
        self.assertFalse(report["nomination_allowed"])
        self.assertFalse(report["test_untouched"])
        self.assertTrue(report["primary35_scorecards_unchanged"])
        self.assertEqual(len(self.full["models"]), 35)
        self.assertEqual(len(self.full["scorecards"]), 105)

    def test_study_validation_pool_excludes_test_and_pools_squared_rmse(self):
        for row in self.data["current_study"]["rows"] + self.data["current_study"]["original_rows"]:
            cards = [c for c in row["season_cards"] if c["season"] in (2024, 2025)]
            n = sum(c["n"] for c in cards)
            self.assertEqual(row["validation_n"], n)
            self.assertEqual(n, 1853)
            for metric, value in row["validation_metrics"].items():
                expected = math.sqrt(sum(c["n"] * c["metrics"][metric] ** 2 for c in cards) / n) if metric == "rmse" else sum(c["n"] * c["metrics"][metric] for c in cards) / n
                self.assertAlmostEqual(value, expected, places=12)

    def test_routing_repair_retains_original_defects_and_no_fit_claim(self):
        report = self.data["current_study"]
        defects = report["original_timing_defects"]
        self.assertEqual(defects["origin_after_target_t120"]["unique_games_by_season"], {"2024": 20, "2025": 2, "2026": 2})
        self.assertEqual(defects["calibration_label_unavailable_at_t120"]["unique_games_by_season"], {"2024": 10, "2025": 2, "2026": 2})
        self.assertEqual(defects["training_label_unavailable_at_t120"]["prediction_rows"], 0)
        work = report["work_counts"]
        self.assertEqual(work["changed_historical_rows"], 288)
        self.assertEqual(work["changed_historical_games"], 24)
        self.assertEqual(work["new_inference_rows"] + work["reused_inference_rows"], 288)
        self.assertEqual(work["new_model_fits"], 0)
        self.assertEqual(work["new_calibrator_fits"], 0)
        self.assertEqual(work["new_genuine_forecasts"], 0)
        self.assertIn("proxy", report["qualification_summary"])
        self.assertIn("unproved", report["source_availability"])

    def test_current_calibration_change_is_separate_from_previous_avoidable_fits(self):
        audit = self.data["current_calibration_audit"]
        self.assertEqual((audit["version"], audit["new_base_fits"], audit["reused_base_estimators"], audit["new_winner_calibrator_fits"]), ("V080R1", 0, 26, 8))
        self.assertEqual((audit["calibration_rows_before"], audit["calibration_rows_after"], audit["newly_eligible_owned_rows"], audit["removed_calibration_rows"]), (160, 161, 3, 2))
        self.assertTrue(audit["common_calibration_values_unchanged"])
        self.assertEqual(audit["avoidable_new_base_fits"], 0)
        self.assertEqual(self.data["previous_execution_audits"][0]["avoidable_duplicate_base_fit_calls"], 26)

    def test_research_market_comparison_uses_exact_primary_provider_cohorts(self):
        report = self.data["research_market_comparison"]
        self.assertFalse(report["used_for_nomination"])
        self.assertFalse(report["promotion"])
        self.assertEqual(len(report["scorecards"]), 12)
        cohorts = {c["season"]: c for c in self.data["market_comparison"]["provider_cohorts"] if c["provider"] == "draftkings" and c["target"] == "winner"}
        self.assertEqual({(r["alias"], r["season"]) for r in report["scorecards"]}, {(alias, season) for alias in ("RW01", "RW02", "RW03", "RW04") for season in (2024, 2025, 2026)})
        for row in report["scorecards"]:
            cohort = cohorts[row["season"]]
            self.assertEqual((row["expected_n"], row["paired_n"], row["paired_cohort_sha256"]), (cohort["expected_n"], cohort["paired_n"], cohort["paired_cohort_sha256"]))
            self.assertEqual(row["role"], "negative_control" if row["alias"] == "RW04" else "challenger")
            self.assertFalse(row["used_for_nomination"])
            self.assertFalse(row["promotion"])
            for metric in ("accuracy", "log_loss", "brier"):
                self.assertAlmostEqual(row["market_metrics"][metric], cohort["market_metrics"][metric], places=12)
                self.assertAlmostEqual(row["delta_model_minus_market"][metric], row["model_metrics"][metric] - row["market_metrics"][metric], places=12)

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

    def test_selected_validation_roles_use_only_prior_seasons_and_keep_current_clocks(self):
        p = self.nominees
        self.assertEqual(p["selection_seasons"], [2024, 2025])
        self.assertFalse(p["test_outcomes_used_for_selection"])
        self.assertTrue(p["protocol_previously_exposed_to_test"])
        self.assertIsNone(p["selection_time"])
        self.assertIn("not retained", p["selection_time_basis"])
        expected = {"winner_probability": "W08", "winner_accuracy": "W02", "margin_mae": "M09", "margin_rmse": "M09", "total_mae": "T09", "total_rmse": "T09"}
        self.assertEqual({key: role["model_alias"] for key, role in p["roles"].items()}, expected)
        games = {f'{g["season"]}/{g["id"]}': g for g in self.games}
        timed = {key for key, g in games.items() if g["season"] == 2026 and g["status"] == "pending"}
        self.assertEqual(set(p["forecasts"]), timed)
        self.assertEqual(len(timed), 86)
        dt = lambda value: datetime.fromisoformat(value.replace("Z", "+00:00"))
        for key, outputs in p["forecasts"].items():
            self.assertEqual(set(outputs), {"W08", "W02", "M09", "T09"})
            for alias, cell in outputs.items():
                self.assertEqual(cell["model_alias"], alias)
                self.assertFalse(cell["evaluation_state_matches"])
                self.assertIn("recipe and chronological protocol", cell["evaluation_state_note"])
                self.assertFalse(cell["promotion"])
                self.assertEqual(cell["timing_label"], "FUTURE_ISSUED")
                self.assertIsNone(cell["selection_time"])
                self.assertEqual(cell["nomination_report_completed_at"], p["nomination_report_completed_at"])
                clocks = [dt(cell[name]) for name in ("information_cutoff", "fit_completed_at", "prepared_at", "issue_time", "requested_horizon_cutoff")]
                self.assertEqual(clocks, sorted(clocks))
                self.assertLess(clocks[-2], clocks[-1])
                self.assertLess(clocks[-1], dt(games[key]["kickoff"]))
                self.assertEqual(cell["value"], round(cell["value"], 4 if cell["target"] == "winner" else 1))
        self.assertEqual(sum(len(v) for v in p["forecasts"].values()), 344)
        self.assertEqual(p["objective_display_cell_count"], 516)
        self.assertEqual((p["new_model_fits"], p["new_forecast_issues"], p["new_source_calls"]), (0, 0, 0))
        self.assertFalse(p["promotion"])

    def test_unmeasured_exchange_references_preserve_zero_qualified_and_legacy_holdings(self):
        for scope in ("current", "historical"):
            measurements = self.nominees["reference_measurements"][scope]
            self.assertEqual(set(measurements), {"kalshi", "polymarket_global", "polymarket_us"})
            for provider, metadata in measurements.items():
                self.assertEqual(metadata["state"], "not_measured")
                self.assertIn("not measured", metadata["reason"])
                self.assertIn("Earlier archived references remain", metadata["reason"])
                cells = [c for g in self.games for c in g.get(scope + "_provider_coverage", {}).get(provider, {}).values()]
                self.assertTrue(cells)
                self.assertTrue(all(not c["predictive_baseline_qualified"] for c in cells))
        self.assertTrue(any((g["providers"]["kalshi"]["winner"] or {}).get("observed_reference") for g in self.games))

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

