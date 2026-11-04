"""Adversarial display tests, not provider authentication or model research."""
from copy import deepcopy
import json
from pathlib import Path
import unittest

from reschedule_reference import validate_reschedule

HERE = Path(__file__).resolve().parent


class RescheduleReferenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.coverage = json.loads((HERE / 'current_coverage.json').read_text())
        cls.original = json.loads((HERE / 'current_source_overlay.json').read_text())
        cls.reference = json.loads((HERE / 'reschedule_reference.json').read_text())

    def check(self, value):
        return validate_reschedule(value, self.coverage, self.original)

    def test_complete_source_recovery_does_not_mutate_prior_data(self):
        before = deepcopy(self.original)
        receipt = self.check(self.reference)
        self.assertEqual(self.original, before)
        self.assertEqual([r['available_games'] for r in receipt['combined_current_reference_coverage']
                          if r['provider'] == 'DraftKings'], [15, 15, 15])
        self.assertFalse(receipt['schedule_reference_historical_metrics_changed'])

    def test_mapping_time_cannot_relabel_old_quote(self):
        x = deepcopy(self.reference)
        x['winner_rows'][0]['quote_at'] = x['event_mapping']['mapping_observed_at']
        with self.assertRaisesRegex(ValueError, 'source clocks'):
            self.check(x)

    def test_no_historical_reentry(self):
        for horizon in ('T1', 'T2', 'LATEST_PREGAME'):
            x = deepcopy(self.reference)
            x['winner_rows'][0]['horizon'] = horizon
            with self.subTest(horizon=horizon), self.assertRaises(ValueError):
                self.check(x)

    def test_no_current_capture_credit(self):
        x = deepcopy(self.reference)
        x['new_provider_requests'] = 1
        with self.assertRaises(ValueError):
            self.check(x)

    def test_other_event_or_generic_time_tolerance_rejected(self):
        for field, value in (('game_id', '2026_09_JAX_BAL'),
                             ('provider_kickoff_utc', '2026-11-08T21:00:00Z'),
                             ('home_team', 'LV')):
            x = deepcopy(self.reference)
            x['event_mapping'][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.check(x)

    def test_unknown_revision_publication_remains_unknown(self):
        x = deepcopy(self.reference)
        x['event_mapping']['revision_first_publication_at'] = x['as_of']
        with self.assertRaises(ValueError):
            self.check(x)

    def test_no_mean_point_projection(self):
        x = deepcopy(self.reference)
        x['point_rows'][0]['point_estimate'] = x['point_rows'][0]['line']
        with self.assertRaises(ValueError):
            self.check(x)

    def test_nested_private_field_rejected(self):
        x = deepcopy(self.reference)
        x['source_integrity']['private_source'] = 'not-public'
        with self.assertRaises(ValueError):
            self.check(x)


if __name__ == '__main__':
    unittest.main()
