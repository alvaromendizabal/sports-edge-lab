"""Check the recovered source's boundaries without changing old score cohorts."""
import hashlib
import json
import unittest
from datetime import datetime, timedelta
from pathlib import Path


class ChicagoRecoveryEvidenceTests(unittest.TestCase):
    def test_recovered_source_is_t1_only_and_never_a_new_forecast(self):
        path = Path(__file__).with_name("chicago_seattle_recovery_n042.json")
        body = path.read_bytes()
        self.assertEqual(hashlib.sha256(body).hexdigest(),
                         "1a2360be71a7a89fa8a86099fcfa10ae63df9b80b159a3b24b925b6007aa89c1")
        data = json.loads(body)
        kickoff = datetime.fromisoformat(data["kickoff_utc"])
        feature = datetime.fromisoformat(data["feature_cutoff_utc"])
        issue = datetime.fromisoformat(data["original_issue_utc"])
        label = datetime.fromisoformat(data["outcome_observed_utc"])
        self.assertLess(kickoff - timedelta(hours=2), feature)
        self.assertLessEqual(feature, issue)
        self.assertLessEqual(issue, kickoff - timedelta(hours=1))
        self.assertGreater(label, kickoff)
        self.assertEqual(data["eligible_horizons"], ["T1"])
        self.assertEqual(data["not_eligible_horizons"], ["T2"])
        self.assertEqual(data["new_fits"], 0)
        self.assertEqual(data["new_forecasts"], 0)
        self.assertFalse(data["historical_metrics_changed"])
        self.assertFalse(data["original_frozen_models_changed"])
        self.assertTrue(data["outcomes_blank_in_original_query"])
        self.assertLess(data["prior_owner_replay_max_absolute_difference"],
                        data["replay_tolerance"])


if __name__ == "__main__":
    unittest.main()
