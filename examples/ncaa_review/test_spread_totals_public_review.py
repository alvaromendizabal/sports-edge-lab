"""Protect the public NCAA review's evidence boundary and full dated population."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import base64
import gzip
import hashlib
import json
import re
import unittest


ROOT = Path(__file__).resolve().parents[2]
PAGE = ROOT / 'docs/ncaa/spread_totals.html'


class PublicSpreadTotalsReview(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = PAGE.read_text()
        encoded = re.search(r'<script id="board-data"[^>]*>(.*?)</script>', cls.html, re.S).group(1)
        cls.payload = gzip.decompress(base64.b64decode(encoded, validate=True))
        cls.data = json.loads(cls.payload)
        cls.summary = json.loads((PAGE.parent / 'spread_totals_latest.json').read_text())

    def test_preserved_entire_original_public_game_projection(self):
        games = self.data['games']
        self.assertEqual(len(games), 3910)
        self.assertEqual(len({g['event_id'] for g in games}), 3910)
        canonical = json.dumps(games, sort_keys=True, separators=(',', ':')).encode()
        self.assertEqual(hashlib.sha256(canonical).hexdigest(), '93517097ba01cc9956b77d2e133f3e445ac3c05be8d50ae0846fa5a2c7c5ca50')

    def test_week_uses_pacific_event_dates_and_separate_leagues(self):
        def local_day(s):
            return datetime.fromisoformat(s.replace('Z', '+00:00')).astimezone(ZoneInfo('America/Los_Angeles')).date().isoformat()
        games = [g for g in self.data['games'] if '2026-11-23' <= local_day(g['event_time']) <= '2026-11-29']
        self.assertEqual(len(games), 735)
        self.assertEqual(sum(g['league'] == 'ncaam' for g in games), 363)
        self.assertEqual(sum(g['league'] == 'ncaaw' for g in games), 372)
        self.assertEqual(local_day('2026-11-23T02:00:00Z'), '2026-11-22')
        self.assertEqual(local_day('2026-11-30T02:00:00Z'), '2026-11-29')
        self.assertFalse(self.data['current_review']['week_official_completeness'])

    def test_unavailable_forecasts_are_never_zero_filled_or_ranked(self):
        for g in self.data['games']:
            for key in ('predicted_winner', 'calibrated_win_probability', 'expected_home_minus_away_margin', 'expected_total', 'preferred_spread_side', 'preferred_total_side'):
                self.assertIsNone(g[key])
            self.assertTrue(g['missing_inputs'])
        self.assertFalse(self.data['scientific_state']['target_achieved'])
        self.assertIsNone(self.data['scientific_state']['qualified_spread_totals_metrics'])

    def test_current_failure_replaces_only_execution_status(self):
        r = self.data['owner_return']
        self.assertEqual(r['status'], 'FAILED_PARTIAL_WORK_PRESERVED')
        self.assertEqual(r['sha256'], '987b853e807a598dd53a7472f72f647953d9abf381b6ea67b519c17fc087e9fc')
        self.assertEqual(r['new_owner_fits'], 0)
        self.assertEqual(r['previously_completed_stages_reused'], 4)
        self.assertEqual(r['new_science_stages_completed'], 0)
        self.assertEqual(r['failure']['message'], 'COMPATIBLE_COORDINATOR_LOCK_TIMEOUT')
        self.assertEqual(self.data['previous_verified_return']['sha256'], '5ddcffad4e92a6ddea183c3e6e339ca9820d5ca9a84cb290e4bc7b34d9b6f9b7')
        self.assertNotIn('No R52 owner research run has launched', self.html)
        self.assertNotIn('newer failure is awaiting', self.html)

    def test_summary_roundtrip_and_private_boundary(self):
        self.assertEqual(self.summary['public_projection_sha256'], hashlib.sha256(self.payload).hexdigest())
        self.assertEqual(self.data['native_menus'], [])
        self.assertEqual(self.data['public_native_contract_rows'], 0)
        self.assertFalse(self.data['private_credentials_included'])
        text = self.payload.decode()
        for forbidden in ('s3://', '/home/sagemaker-user', 'sagemaker-sports-edge-lab-', 'BEGIN PRIVATE KEY', 'AKIA'):
            self.assertNotIn(forbidden, text)
        self.assertEqual(self.summary['owner_return'], self.data['owner_return'])


if __name__ == '__main__':
    unittest.main()
