"""Scientific display boundaries and additive page preservation."""
import copy
import hashlib
import json
from pathlib import Path
import re
import unittest
import b063r2_dashboard as dashboard

class EvidenceBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payload = dashboard.load_payload()

    def test_exact_public_source_bytes_and_downloads(self):
        output = dashboard.evidence_outputs()
        for name, expected in dashboard.SOURCE_PINS.items():
            body = output[dashboard.ROOT / "docs/ncaa/data" / name].encode()
            self.assertEqual(hashlib.sha256(body).hexdigest(), expected)
        html = output[dashboard.ROOT / "docs/ncaa/b063r2.html"]
        data = json.loads(re.search(r'<script id="b063r2-data" type="application/json">(.*?)</script>', html, re.S).group(1))
        self.assertEqual(data, self.payload)
        self.assertNotIn("__B063R2_DATA__", html)

    def test_refuses_current_replay_relabeling_and_fictitious_owner_execution(self):
        payload = copy.deepcopy(self.payload)
        payload["science"]["current_observed_replay_leaders"][0]["evaluation_mode"] = "prospective"
        with self.assertRaisesRegex(ValueError, "relabeled"):
            dashboard.validate(payload)
        payload = copy.deepcopy(self.payload)
        payload["execution"]["continuation"]["owner_parallelism_proven"] = True
        with self.assertRaisesRegex(ValueError, "prepared|Prepared"):
            dashboard.validate(payload)

    def test_refuses_wrong_leader_and_changed_original_forecast(self):
        payload = copy.deepcopy(self.payload)
        payload["science"]["historical_per_season_leaders"][0]["value"] += 0.01
        with self.assertRaisesRegex(ValueError, "exact candidate"):
            dashboard.validate(payload)

    def test_latest_r2_preserves_prior_return_and_excludes_probe_credit(self):
        execution = self.payload["execution"]
        self.assertEqual(execution["latest_actual_owner"]["release"], "B063R2")
        self.assertEqual(execution["prior_actual_owner"]["release"], "B063R1")
        self.assertEqual(execution["latest_actual_owner"]["tests_passed"], 3766)
        self.assertEqual(execution["latest_actual_owner"]["peak_scientific_workers"], 0)
        payload = copy.deepcopy(self.payload)
        payload["execution"]["latest_actual_owner"]["probe_utilization_is_not_scientific_parallelism"] = False
        with self.assertRaisesRegex(ValueError, "Probe"):
            dashboard.validate(payload)
        payload = copy.deepcopy(self.payload)
        payload["late"]["rows"][0]["original_actual"] = 1
        with self.assertRaisesRegex(ValueError, "actual field"):
            dashboard.validate(payload)

    def test_banner_preserves_existing_body_and_is_idempotent(self):
        original = '<!doctype html><html><body><main><section id="preserved">old data</section></main></body></html>'
        once = dashboard.render_banner(original)
        self.assertEqual(once.replace(dashboard.BANNER, ""), original)
        self.assertEqual(dashboard.render_banner(once), once)
        self.assertEqual(once.count(dashboard.START), 1)
        self.assertIn('href="b063r2.html"', once)

    def test_actual_landing_preserves_the_complete_prior_page(self):
        page = (dashboard.ROOT / "docs/ncaa/index.html").read_text()
        self.assertEqual(page.count(dashboard.BANNER), 1)
        previous = page.replace(dashboard.BANNER, "")
        git_blob = b"blob " + str(len(previous.encode())).encode() + b"\0" + previous.encode()
        self.assertEqual(hashlib.sha1(git_blob).hexdigest(),
                         "ac6ba71d80e444de82d799c64f5b5387c02b501b")
        self.assertEqual(dashboard.render_banner(previous), page)

    def test_publishing_checks_both_retained_history_and_companion(self):
        from unittest.mock import patch
        import build_dashboard
        sentinel = dashboard.ROOT / "retained-full-history.html"
        with patch.object(build_dashboard, "outputs", return_value={sentinel: "retained"}):
            output = build_dashboard.publication_outputs()
        self.assertEqual(output[sentinel], "retained")
        self.assertEqual(output[dashboard.ROOT / "docs/ncaa/b063r2.html"], dashboard.render_page())
        for name in dashboard.SOURCE_PINS:
            self.assertIn(dashboard.ROOT / "docs/ncaa/data" / name, output)

    def test_preserves_full_historical_and_separate_original_populations(self):
        science = self.payload["science"]
        self.assertEqual(len(science["historical_per_season_candidate_metrics"]), 164)
        self.assertEqual(len(science["historical_per_season_leaders"]), 28)
        self.assertEqual(len(science["historical_pooled_leaders"]), 14)
        self.assertEqual(len(science["current_observed_replay_leaders"]), 14)
        self.assertEqual(len(self.payload["early"]["groups"]), 6)
        self.assertEqual(len(self.payload["late"]["groups"]), 11)
        self.assertEqual(len(self.payload["late"]["rows"]), 46)

if __name__ == "__main__":
    unittest.main()

