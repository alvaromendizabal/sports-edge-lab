"""Verify public FBS populations and publication boundaries, without owner work."""
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import unittest

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
