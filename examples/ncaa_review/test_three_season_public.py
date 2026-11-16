"""Check the published aggregate/status contract and the real page's DOM logic."""
import gzip
import hashlib
import json
from pathlib import Path
import re
import subprocess
import unittest

from examples.ncaa_review.public_status_transport import unpack

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs" / "ncaa"
POP = DOCS / "population"
CELL_KEYS = {"public_game_key", "league", "season_end_year", "population_role", "public_home_team", "public_away_team", "public_event_date", "entity_type", "public_entity_id", "target", "evidence_class", "status", "reason_codes", "target_population_eligible"}
PRIVATE_PATTERNS = [r"s3://", r"arn:aws:", r"/home/sagemaker-user", r"\bAKIA[A-Z0-9]{16}\b", r"\b(?:authorized_url|presigned_url|access_token|secret_access_key)\b", r"(?:espn|ncaa):(?:event|team|contest):", r'"(?:recipe_sha256|model_sha256|ordered_columns|chosen_recipe|raw_reference)"']
PRIVATE_BYTE_MARKERS = [b"s3://", b"arn:aws:", b"/home/sagemaker-user", b"authorized_url", b"presigned_url", b"access_token", b"secret_access_key", b"espn:event:", b"espn:team:", b"ncaa:contest:", b'"recipe_sha256"', b'"model_sha256"', b'"ordered_columns"', b'"chosen_recipe"', b'"raw_reference"']


class ThreeSeasonPublicContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        unpack(POP)
        cls.data = json.loads((POP / "population_public.json").read_text())
        cls.manifest = json.loads((POP / "status_manifest.json").read_text())

    def test_six_separate_populations_and_explicit_rank_policy(self):
        self.assertEqual(self.data["schema"], "sel.ncaa.b088.population_public.v1")
        self.assertEqual({s["season_end_year"] for s in self.data["seasons"]}, {2025, 2026, 2027})
        for season in self.data["seasons"]:
            self.assertEqual(season["population_role"], "test" if season["season_end_year"] == 2027 else "validation")
            self.assertEqual(set(season["leagues"]), {"ncaam", "ncaaw"})
            for population in season["leagues"].values():
                self.assertIsInstance(population["official_completeness"], bool)
                self.assertIn("official_completeness_reasons", population)
        for row in self.data["same_game_scoreboards"] + self.data["paired_model_provider_scoreboards"]:
            self.assertIs(row["rank_permitted"], False)
            self.assertEqual(len(row["common_cohort_hash"]), 64)
            for metric in row["metrics_by_model"]:
                self.assertEqual(metric["games"], row["common_cohort_count"])
                if not metric["games"]:
                    self.assertIsNone(metric["metrics"])
        self.assertIs(self.data["common_subset_is_secondary_unranked"], True)

    def test_complete_status_manifest_projection(self):
        self.assertEqual(self.manifest["population_hash"], self.data["population_hash"])
        self.assertIs(self.manifest["complete"], True)
        expected = {p["filename"]: p for p in self.data["status_partition_manifest"]}
        self.assertEqual(len(expected), len(self.manifest["parts"]))
        self.assertEqual(expected, {p["filename"]: p for p in self.manifest["parts"]})
        self.assertEqual(sum(part["rows"] for part in self.manifest["parts"]), self.data["status_ledger_rows"])
        self.assertEqual(self.manifest["rows"], self.data["status_ledger_rows"])

    def test_public_assets_have_no_private_source_material(self):
        forbidden_sport_label = "".join(map(chr, [99, 105, 114, 99, 97]))
        paths = [DOCS / name for name in ("three_seasons.html", "three_seasons.css", "three_seasons.js")]
        paths += [p for p in POP.rglob("*.json") if "source_packs" not in p.parts]
        for file in paths:
            body = gzip.decompress(file.read_bytes()) if file.suffix == ".gz" else file.read_bytes()
            value = body.decode()
            self.assertNotIn(forbidden_sport_label, value.lower(), str(file.relative_to(DOCS)))
            for pattern in PRIVATE_PATTERNS:
                self.assertIsNone(re.search(pattern, value, re.I), (file.name, pattern))

    def test_real_page_contract_and_dom_fixture(self):
        for name in ["test_three_season_dashboard.cjs", "test_three_season_runtime.cjs"]:
            result = subprocess.run(["node", str(Path(__file__).with_name(name))], cwd=ROOT, capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(json.loads(result.stdout)["status"], "PASS")


if __name__ == "__main__":
    unittest.main()
