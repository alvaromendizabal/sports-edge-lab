"""Independent preservation checks for the B076 review of the B075 owner run."""
import hashlib
import json
import os
from pathlib import Path
import unittest

ROOT = Path(os.environ.get('NBA_SNAPSHOT_TEST_DIR', Path(__file__).parent))


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


class B075OwnerEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((ROOT / 'latest_research_outputs.json').read_bytes())
        cls.audit = json.loads((ROOT / 'b076_owner_evidence.json').read_bytes())

    def test_original_forecasts_roles_and_denominators_preserve_prior_public_bytes(self):
        # Digests independently captured from public base 40ebb0c9, before the
        # owner review. A failed later execution cannot silently issue values.
        expected = {
            'issues': 'cab529d0821d88a31f1d07a3680a0d7c26bdb1a756c6a2db6aee9d778f5a55b9',
            'champions': '394ae440d187669569524d224fa5b7d8c742b8be7918b57cf3fbcf03faaa2bd2',
            'role_views': '14f4cd8d7512a51909223cfa6dd7d1fb275c411d41f499f7042f80e81d380f55',
            'game_coverage': 'f6e9fb6194d2ddf1bd506679e5e52d998d86b7219d6d8c6e5d5567b103aa4333',
            'forecast_inventory_game_ids': '02fd22a4b03cd18213a4055623f6bfdb29746ef0bd63a9329071ef9a98db3c93',
        }
        for name, pin in expected.items():
            with self.subTest(name=name):
                self.assertEqual(digest(self.data[name]), pin)

    def test_latest_failed_execution_cannot_receive_older_fit_and_issue_counts(self):
        owner = self.data['newest_owner_execution']
        self.assertEqual(owner['release'], 'B075')
        self.assertEqual(owner['observed_exit_code'], 3)
        self.assertEqual(owner['new_estimator_fits'], 0)
        self.assertEqual(owner['new_forecasts'], 0)
        self.assertEqual(owner['observed_peak_concurrent_model_fits'], 0)
        self.assertEqual(self.data['latest_original_issue_owner_release'], 'B074')
        self.assertEqual(self.audit['outcome'], owner)
        admission = self.audit['failure_evidence']['research_admission']
        self.assertEqual(admission['baseline_bytes'] - admission['allowance_bytes'], 1840671)
        self.assertEqual(admission['attempted_new_fit_admissions'], 0)
        self.assertEqual(admission['failed_new_model_tasks'], 0)

    def test_later_observed_final_does_not_rewrite_earlier_schedule_or_forecast_clock(self):
        game = self.data['games']['0022600216']
        self.assertEqual((game['away_team'], game['home_team']), ('OKC', 'POR'))
        self.assertEqual(game['source_status'], 'SCHEDULED')
        self.assertEqual(game['schedule_source_asof_utc'], '2026-11-11T03:08:57.068583+00:00')
        self.assertEqual(game['last_confirmed_status'], 'FINAL')
        result = game['result_observation']
        self.assertEqual((result['away_points'], result['home_points']), (103, 123))
        self.assertEqual(result['observed_at_utc'], '2026-11-11T17:55:42.066367+00:00')
        self.assertFalse(result['new_score_calculation'])
        self.assertFalse(result['original_historical_possession_claim'])
        self.assertEqual(self.data['result_observation_recovery']['result_rows_attached'], 40)
        self.assertEqual(self.data['coverage']['official_games_by_latest_row_backed_status'], {'FINAL': 227, 'SCHEDULED': 1040, 'TBD': 7})
        self.assertEqual(self.data['coverage']['latest_row_and_source_aggregate_difference'], {})

    def test_review_does_not_claim_missing_owner_source_bodies_or_new_predictions(self):
        review = self.audit['public_snapshot']
        self.assertFalse(review['owner_B075_full_schedule_body_physically_available'])
        self.assertFalse(review['owner_B075_publication_body_physically_available'])
        self.assertFalse(review['exact_owner_export_reconstruction_claim'])
        self.assertFalse(review['new_fitting_inference_acquisition_or_metric_rescoring_in_publication'])
        self.assertEqual(review['official_game_denominator'], 1274)
        self.assertEqual(review['official_games_without_original_issues'], 1117)


if __name__ == '__main__':
    unittest.main()
