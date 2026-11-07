import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[3]
BODY = (ROOT/'docs/fbs/source-health-v040.json').read_bytes()
D = json.loads(BODY)


class SourceHealthTests(unittest.TestCase):
    def test_exact_authenticated_public_projection(self):
        self.assertEqual(len(BODY),4044)
        self.assertEqual(hashlib.sha256(BODY).hexdigest(),'5457a0832ac79f1bce6f1d0ee9044d3cbc371912024618b5b62eeb479b2a2a70')
        self.assertTrue(D['canonical_return_verified'])
        self.assertFalse(D['return_is_full'])
        self.assertFalse(D['observed_state_is_live'])
        self.assertFalse(D['independently_observed_owner_OS_exit'])

    def test_contracts_rows_and_empty_registration_stay_distinct(self):
        totals=D['native_contract_units']
        self.assertEqual(sum(w['registered'] for w in D['waves']),141424)
        self.assertEqual(sum(w['reported_complete'] for w in D['waves']),60620)
        self.assertEqual(sum(w['reported_failed'] for w in D['waves']),80804)
        self.assertEqual(totals['registered'],totals['producer_reported_complete']+totals['producer_reported_failed'])
        for w in D['waves']:
            self.assertEqual(w['registered'],w['reported_complete']+w['reported_failed'])
        self.assertEqual(sum(D['native_provider_failure_counts'].values()),80804)
        empty=[w for w in D['waves'] if w['empty_registration']]
        self.assertEqual([(w['season'],w['wave']) for w in empty],[(2024,'alternates')])
        self.assertEqual(D['cutoff_row_statuses']['history_read_failed'],242412)

    def test_reported_success_cannot_become_coverage_or_performance(self):
        self.assertIsNone(D['native_contract_units']['independently_verified_total_successes'])
        self.assertEqual(D['native_contract_units']['new_independently_verified_successes_in_this_audit'],0)
        self.assertFalse(D['provider_coverage_expansion_credited'])
        self.assertEqual(D['full_workload_performance'],'NO_GO')
        self.assertEqual(D['public_schedule_capture_unchanged'],'2026-11-06T20:28:52Z')
        self.assertFalse(D['sampled_original_failure_findings']['http_403_or_429_cause_established_by_samples'])
        for forbidden in ['s3://','bucket','secret','api_key','raw_body','player_name']:
            self.assertNotIn(forbidden,BODY.decode().lower())
