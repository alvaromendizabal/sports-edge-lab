"""Public NCAA V11 continuity, information-time and operational status gates.

These tests inspect saved public evidence. They perform no fitting, source
acquisition, owner execution or forecast generation.
"""
import base64
from datetime import datetime
import gzip
import hashlib
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[2]
PAGE = ROOT / "docs/ncaa/v11.html"
STATUS = ROOT / "docs/ncaa/v11_1_execution_status.json"


def read_public():
    page = PAGE.read_text(encoding="utf-8")
    packed = re.search(
        r'<script id="v10-data" type="application/octet-stream">(.*?)</script>',
        page, re.S).group(1)
    evidence = json.loads(gzip.decompress(base64.b64decode(packed)))
    operational = json.loads(re.search(
        r'<script id="v11-execution-data" type="application/json">(.*?)</script>',
        page, re.S).group(1))
    return page, packed, evidence, operational


class PublicEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.page, cls.packed, cls.evidence, cls.operational = read_public()

    def test_recovered_scientific_payload_and_status_identity(self):
        self.assertEqual(hashlib.sha256(self.packed.encode()).hexdigest(),
                         self.operational["preserved_scientific_payload_sha256"])
        self.assertEqual(self.operational, json.loads(STATUS.read_text()))
        self.assertEqual(len(self.evidence["v11_pairs"]), 512)
        self.assertEqual(len(self.evidence["v11_comparable_week_leaders"]), 48)
        self.assertEqual(len(self.evidence["models"]), 336)

    def test_updated_partition_accounting_does_not_double_count(self):
        e = self.operational
        self.assertEqual(e["latest_partition_rows"],
                         e["initial_partition_rows"] - e["initial_current_partition_rows"]
                         + e["refreshed_current_partition_rows"])
        self.assertFalse(e["checkpoint_references_are_fits"])
        self.assertEqual(e["verified_reused_fit_credit"], 0)

    def test_no_new_execution_or_fit_credit_from_publication(self):
        e = self.operational
        self.assertFalse(e["new_owner_execution_verified"])
        for key in ["new_owner_fits", "new_owner_inference",
                    "new_owner_issued_forecasts", "automatic_promotions"]:
            self.assertEqual(e[key], 0)
        self.assertEqual(e["delivery_policy"]["owner_execution_of_new_transport"],
                         "NOT_YET_OBSERVED")
        self.assertIn("in preparation", self.page)

    def test_benchmark_is_measured_scoring_without_fit_claim(self):
        b = self.operational["benchmark"]
        self.assertFalse(b["synthetic_work"])
        self.assertEqual(b["unique_tasks"], 18)
        self.assertEqual(b["peak_workers"], 12)
        self.assertEqual([x["layout"] for x in b["layouts"]],
                         ["1x1", "4x1", "8x1", "12x1"])
        for row in b["layouts"]:
            self.assertAlmostEqual(row["speedup"],
                                   b["layouts"][0]["wall_seconds"] / row["wall_seconds"],
                                   places=7)
        self.assertIn("not a fitting benchmark", b["thread_schedule_limit"])

    def test_transport_limit_is_per_physical_part(self):
        p = self.operational["delivery_policy"]
        self.assertEqual(p["maximum_physical_part_bytes"], 512 << 20)
        self.assertFalse(p["aggregate_transport_size_is_science_admission_gate"])

    def test_new_uncertainty_supplement_retains_negative_and_null_results(self):
        s = self.operational["historical_uncertainty_supplement"]
        self.assertEqual(s["historical_partitions"], 12)
        self.assertEqual(s["interval_rows"], 336)
        self.assertEqual(s["bootstrap_replicates"], 149999)
        self.assertEqual(s["directions"],
                         {"POSITIVE": 9, "NEGATIVE": 15, "INCLUDES_ZERO": 312})
        self.assertEqual(sum(s["directions"].values()), s["interval_rows"])
        self.assertEqual(s["self_baseline_controls_in_interval_rows"], 28)
        self.assertEqual(s["negative_controls_passed"], s["negative_controls_total"])
        self.assertEqual(s["negative_controls_total"], 40)
        self.assertLess(s["point_estimates_max_absolute_reproduction_error"], 1e-14)
        self.assertTrue(s["cohorts_and_game_counts_reproduced"])
        self.assertIsNone(s["weighted_champion"])
        self.assertFalse(s["new_market_evidence"])
        self.assertEqual(s["new_model_fits"], 0)
        self.assertEqual(s["new_model_inference"], 0)
        self.assertEqual(s["new_issued_forecasts"], 0)
        self.assertEqual(s["promotions"], 0)
        for key, label in [("positive", "POSITIVE"), ("negative", "NEGATIVE"),
                           ("includes_zero", "INCLUDES_ZERO")]:
            self.assertEqual(sum(r[key] for r in s["by_competition_season"]),
                             s["directions"][label])

    def test_weighted_and_market_claims_remain_withheld(self):
        d = self.evidence
        self.assertEqual(d["v11_weighting"]["complete_three_season_candidates"], 0)
        self.assertEqual(d["v11_weighting"]["status"],
                         "WEIGHTED_RANK_WITHHELD_MISSING_EXACT_RECIPE_LINEAGE")
        self.assertTrue(all(p["games"] == 0 for p in d["providers"]))
        self.assertTrue(all(not p["automatic_promotion"] for p in d["v11_pairs"]))
        self.assertTrue(all(u["bonferroni_family_95_interval"] is None
                            for p in d["v11_pairs"] for u in p["uncertainty"].values()))

    def test_future_unissued_values_remain_withheld(self):
        d = self.evidence
        self.assertEqual(d["public_projection"]["future_unissued_numeric_forecasts_published"], 0)
        self.assertEqual(d["public_projection"]["future_forecast_cells_withheld"], 2793)
        asof = datetime.fromisoformat(d["analysis_asof"].replace("Z", "+00:00"))
        checked = 0
        for game in d["games"]:
            stamp = game.get("event_time")
            if not stamp:
                continue
            event = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
            if event > asof:
                for forecast in game["forecasts"].values():
                    if forecast is not None:
                        self.assertIn(forecast["evidence_class"],
                                      ["ORIGINAL_ISSUED", "FUTURE_ISSUED"])
                checked += 1
        self.assertGreater(checked, 0)

    def test_no_private_cloud_or_runtime_material(self):
        public = self.page + json.dumps(self.evidence) + json.dumps(self.operational)
        for forbidden in ["s3://", "arn:aws:", "/home/sagemaker-user", ".pyz",
                          "aws_secret_access_key", "B032_RETRAINED_", '"feature_columns":',
                          '"hyperparameters":', '"model_weights":']:
            self.assertNotIn(forbidden, public)
        self.assertFalse(self.evidence["complete_current_season"])
        self.assertFalse(self.evidence["complete_upcoming_schedule"])


if __name__ == "__main__":
    unittest.main()
