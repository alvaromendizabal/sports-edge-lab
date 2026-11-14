"""Validate the dated public projection without executing private owner science."""
import json
import re
import unittest
from datetime import datetime
from pathlib import Path


SITE = Path(__file__).resolve().parents[1] / "docs/fbs/v076"


def read(name):
    return json.loads((SITE / name).read_text(encoding="utf-8"))


class PublicV076(unittest.TestCase):
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
        self.assertEqual(self.summary["source_as_of"], "2026-11-14T04:57:50Z")
        self.assertEqual(self.summary["total_games"], 2742)
        self.assertEqual(sum(map(len, self.games.values())), 2742)
        self.assertEqual(len({g["id"] for rows in self.games.values() for g in rows}), 2742)
        for year, total, final in [(2024, 920, 919), (2025, 934, 934), (2026, 888, 694)]:
            rows = self.games[year]
            self.assertEqual(len(rows), total)
            self.assertEqual(sum(g["status"] == "FINAL" for g in rows), final)
            self.assertEqual(self.summary["season_census"][str(year)]["pending_or_upcoming"], total - final)
            for row in rows:
                if row["status"] == "FINAL":
                    self.assertIsNotNone(row["home_score"])
                    self.assertIsNotNone(row["away_score"])
        self.assertEqual(sum(g["status"] == "KICKOFF_TBD" for g in self.games[2026]), 54)

    def test_owner_work_is_reported_without_claiming_new_publication_science(self):
        self.assertEqual(self.summary["new_fits"], 0)
        self.assertEqual(self.summary["new_forecasts"], 3588)
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
        self.assertEqual(self.weighted["authenticated_margin_residual_rows"], 3)
        self.assertEqual(self.summary["timing_games"]["ORIGINAL_ISSUED"], 5)
        html = (SITE / "index.html").read_text()
        self.assertIn("0 / 3 correct", html)
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


    def test_refit_coverage_retains_all_pending_and_missing_fixtures(self):
        value = read("data/refits.json")
        self.assertEqual(value["coverage"], {"pending_games":194, "games_with_refit_outputs":138,
            "missing_games":56, "kickoff_tbd":54, "prepared_rows":0, "issued_rows":3588})
        self.assertEqual(len(value["games"]), 194)
        self.assertEqual(len({g["id"] for g in value["games"]}), 194)
        self.assertEqual(sum(g["missing_reason"] is not None for g in value["games"]), 56)
        self.assertEqual(len(value["families"]), 10)
        self.assertEqual(sum(f["verified_fit_states"] for f in value["families"]), 26)
        self.assertEqual(self.summary["execution"]["verified_reused_fit_states"], 26)
        self.assertEqual(sum(g["issued_rows"] for g in value["games"]), 3588)
        self.assertEqual(sum(g["latest_issued"] is not None for g in value["games"]), 138)
        self.assertFalse(self.summary["publication_review"]["v076_owner_execution_claimed"])
        self.assertEqual(self.summary["execution"]["verified_new_owner_calibrators"], 0)
        self.assertTrue(self.summary["execution"]["independent_terminal_exit_verified"])

    def test_prepared_values_and_candidate_identities_are_not_public(self):
        value = read("data/refits.json")
        self.assertTrue(value["public_values_withheld"])
        self.assertTrue(all(set(r)=={"game","family","target","prepared","issued"} for r in value["rows"]))
        raw = json.dumps(value)
        for forbidden in ('"value"', '"prediction"', '"model_id"', '"model_code"', '"raw_probability"', '"interval80"', '"state_sha256"'):
            self.assertNotIn(forbidden, raw)
        self.assertEqual(self.summary["execution"]["new_refit_forecasts_added_by_dashboard"], 0)
        self.assertIn("values remain private", (SITE/"index.html").read_text())


if __name__ == "__main__":
    unittest.main(verbosity=2)
