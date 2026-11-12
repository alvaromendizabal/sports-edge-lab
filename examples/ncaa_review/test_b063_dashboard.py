"""Behavioral checks for exact source preservation and the B063 public view."""
import copy
from datetime import datetime
import json
import re
import unittest
import b063_dashboard

class B063PublicEvidence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data, cls.raw = b063_dashboard.load_payload()
        cls.sources = b063_dashboard.pinned_sources()

    def test_original_byte_identities_are_required(self):
        self.assertEqual(len(self.sources), 4)
        self.assertEqual(self.data["source_commit"], b063_dashboard.SOURCE_COMMIT)

    def test_every_source_record_and_all_issue_records_survive(self):
        data = self.data
        self.assertEqual(len(data["games"]), 3457)
        self.assertEqual(len(data["issued_archive"]["records"]), 96)
        self.assertEqual(sum(r[0] == "ncaam" for r in data["games"]), 1800)
        self.assertEqual(sum(r[0] == "ncaaw" for r in data["games"]), 1657)
        self.assertEqual(sum(r[11] is not None for r in data["games"]), 814)
        self.assertEqual(sum(r[14] is not None for r in data["games"]), 30)

    def test_unissued_future_values_stay_blank(self):
        future = [r for r in self.data["games"] if r[10] == "PRIVATE_UNISSUED_FUTURE_PREVIEW_NOT_PUBLISHED"]
        self.assertEqual(len(future), 1139)
        self.assertTrue(all(all(v is None for v in row[11:17]) for row in future))

    def test_two_original_time_conflicts_remain_unbound(self):
        def timestamp(value):
            return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
        keys = {(r[0],r[1],timestamp(r[2])) for r in self.data["games"] if r[2]}
        archive = self.data["issued_archive"]["records"]
        unbound = [r for r in archive if (r["league"],r["event_id"],timestamp(r["event_time"])) not in keys]
        self.assertEqual(len(unbound), 6)
        self.assertEqual(len({r["event_id"] for r in unbound}), 2)
        self.assertTrue(all(r["actual"] is None for r in unbound))
        self.assertTrue(all(timestamp(r["issued_at"]) <= timestamp(r["cutoff_time"]) < timestamp(r["event_time"]) for r in archive))

    def test_forecast_and_clock_mutations_are_rejected(self):
        for field, value in ((14,0.999999),(2,"2020-01-01T00:00:00Z")):
            changed=copy.deepcopy(self.data); changed["games"][0][field]=value
            with self.assertRaises(ValueError):
                b063_dashboard.validate(changed,self.sources)
        changed=copy.deepcopy(self.data);changed["issued_archive"]["records"][0]["issued_at"]="2030-01-01T00:00:00Z"
        with self.assertRaises(ValueError):
            b063_dashboard.validate(changed,self.sources)

    def test_publication_does_not_claim_fits_issues_or_promotion(self):
        for key in ("new_owner_fits","new_issued_forecasts","promotions"):
            changed=copy.deepcopy(self.data);changed["execution"][key]=1
            with self.assertRaises(ValueError):
                b063_dashboard.validate(changed,self.sources)
        self.assertFalse(self.data["execution"]["parallelism_verified"])

    def test_missing_markets_and_role_selection_remain_explicit(self):
        self.assertEqual(self.data["market"]["qualified_current_kalshi_pairs"],0)
        self.assertEqual(self.data["market"]["saved_polymarket"]["games"],265)
        self.assertEqual(len(self.data["roles"]["selected_roles"]),6)
        self.assertEqual(len(self.data["requested_roles"]),7)
        self.assertFalse(self.data["complete_official_universe"])

    def test_public_projection_excludes_private_runtime_fields(self):
        raw=self.raw.lower()
        for marker in ("s3://","sagemaker-user","access_key","secret_key","api_key","s3_bucket","checkpoint_path","model_weights","feature_columns"):
            self.assertNotIn(marker,raw)

    def test_self_contained_renderer_preserves_legacy_and_json(self):
        page=b063_dashboard.render("<html><body><main><p>dated scientific evidence</p></main></body></html>")
        self.assertIn("dated scientific evidence",page)
        embedded=re.search(r'<script id="b063-data" type="application/json">(.*?)</script>',page,re.S)
        self.assertEqual(json.loads(embedded.group(1)),self.data)
        self.assertNotRegex(page,r"<script[^>]+src=")
        self.assertNotIn("__B063_",page)

if __name__ == "__main__":
    unittest.main()
