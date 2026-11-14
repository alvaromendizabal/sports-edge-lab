"""Validate the dated public projection without executing private owner science."""
import json
import re
import unittest
from datetime import datetime
from pathlib import Path


SITE = Path(__file__).resolve().parents[1] / "docs/fbs/v074"


def read(name):
    return json.loads((SITE / name).read_text(encoding="utf-8"))


class PublicV074(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.summary = read("data/summary.json")
        cls.weighted = read("data/season_skill.json")
        cls.aliases = {x["code"] for x in cls.summary["selected_models"]}
        cls.games = {}
        for year in (2024, 2025, 2026):
            source = read(f"data/games_{year}.json")
            cls.games[year] = [dict(zip(source["columns"], row)) for row in source["rows"]]

    def test_dated_inventory_and_missing_results_are_complete(self):
        self.assertEqual(self.summary["source_as_of"], "2026-11-13T23:31:35Z")
        self.assertEqual(self.summary["total_games"], 2742)
        self.assertEqual(sum(map(len, self.games.values())), 2742)
        self.assertEqual(len({g["id"] for rows in self.games.values() for g in rows}), 2742)
        for year, total, final in [(2024, 920, 919), (2025, 934, 934), (2026, 888, 693)]:
            rows = self.games[year]
            self.assertEqual(len(rows), total)
            self.assertEqual(sum(g["status"] == "FINAL" for g in rows), final)
            self.assertEqual(self.summary["season_census"][str(year)]["pending_or_upcoming"], total - final)
            for row in rows:
                if row["status"] == "FINAL":
                    self.assertIsNotNone(row["home_score"])
                    self.assertIsNotNone(row["away_score"])
        self.assertEqual(sum(g["status"] == "KICKOFF_TBD" for g in self.games[2026]), 54)

    def test_review_does_not_claim_new_science(self):
        self.assertEqual(self.summary["new_fits"], 0)
        self.assertEqual(self.summary["new_forecasts"], 0)
        self.assertFalse(self.summary["fresh_source_acquisition"])
        self.assertFalse(self.summary["all_current_season_claim"])
        self.assertEqual(self.summary["execution"]["verified_new_owner_fits"], 0)
        self.assertEqual(self.weighted["new_model_fits"], 0)
        self.assertEqual(self.weighted["new_predictions"], 0)
        self.assertIn("V11.1", self.summary["policy_research"])
        self.assertIn("No automatic promotion", self.summary["promotion"])

    def test_selected_aliases_and_all_lazy_detail_references(self):
        self.assertEqual(self.aliases, {f"M{i:02}" for i in range(1, 13)})
        detail_cache = {}
        for rows in self.games.values():
            for game in rows:
                file = game["detail"]
                self.assertRegex(file, r"^data/detail_202[456]_\d{2}\.json$")
                if file not in detail_cache:
                    detail_cache[file] = read(file)
                self.assertIn(game["id"], detail_cache[file]["games"])
                for value in game["display"].values():
                    if value is None:
                        continue
                    self.assertIn(value["model"], self.aliases)
                    if value["timing"] in {"ORIGINAL_ISSUED", "FUTURE_ISSUED"}:
                        self.assertIsNotNone(value["issued"])
                        self.assertLess(datetime.fromisoformat(value["issued"].replace("Z", "+00:00")),
                                        datetime.fromisoformat(game["kickoff"].replace("Z", "+00:00")))
        self.assertEqual(len(detail_cache), 48)
        for detail in detail_cache.values():
            for game in detail["games"].values():
                for row in game["rows"]:
                    self.assertIn(row[0], self.aliases)

    def test_weighted_views_keep_identical_cohorts_and_uncertainty(self):
        comparisons = self.weighted["comparisons"]
        self.assertEqual({(c["target"], c["window"]) for c in comparisons},
                         {(t, w) for t in ("winner", "margin", "total") for w in ("full", "elapsed")})
        profiles = {p["id"] for p in self.weighted["profiles"]}
        self.assertEqual(profiles, {"primary", "current", "equal", "stability"})
        negatives = 0
        for comparison in comparisons:
            self.assertEqual(set(comparison["seasons"]), {"2024", "2025", "2026"})
            for support in comparison["seasons"].values():
                self.assertGreater(support["n"], 0)
                self.assertLessEqual(support["n"], support["window_final_denominator"])
                self.assertLessEqual(support["window_final_denominator"], support["official_final_denominator"])
                self.assertGreater(support["week_blocks"], 1)
            self.assertEqual({r["profile"] for r in comparison["rows"]}, profiles)
            for row in comparison["rows"]:
                self.assertEqual(set(row["season_skill"]), {"2024", "2025", "2026"})
                self.assertLessEqual(row["family_minimum_skill"], row["weighted_skill"])
                self.assertLessEqual(row["weighted_skill"], row["family_maximum_skill"])
                for key in ("conditional_ci95", "adjusted_interval"):
                    if row[key] is not None:
                        self.assertEqual(len(row[key]), 2)
                        self.assertLessEqual(*row[key])
                negatives += row["negative_candidates"]
        self.assertGreater(negatives, 0)
        self.assertIn("later reconstructions", " ".join(self.weighted["limitations"]))

    def test_market_and_original_issue_evidence_are_not_invented(self):
        self.assertEqual(self.summary["qualified_provider_cells"], 0)
        self.assertTrue(all(p["qualified"] == 0 for p in self.summary["providers"]))
        self.assertEqual(self.weighted["qualified_provider_rows"], 0)
        self.assertEqual(self.weighted["authenticated_margin_residual_rows"], 2)
        self.assertEqual(self.summary["timing_games"]["ORIGINAL_ISSUED"], 2)
        html = (SITE / "index.html").read_text()
        self.assertIn("0 / 2 correct", html)
        self.assertIn("No authenticated Circa", html)

    def test_public_files_exclude_runtime_and_private_locations(self):
        forbidden = re.compile(r"s3://|arn:aws:|/home/sagemaker-user|/workspace/|AKIA[0-9A-Z]{16}|BEGIN (?:RSA |EC )?PRIVATE KEY")
        for path in SITE.rglob("*"):
            if not path.is_file():
                continue
            self.assertNotIn(path.suffix, {".pyz", ".zip", ".pkl", ".joblib", ".parquet", ".pt", ".onnx"})
            text = path.read_text(encoding="utf-8")
            self.assertIsNone(forbidden.search(text), path.name)
            if path.suffix == ".json":
                json.loads(text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
