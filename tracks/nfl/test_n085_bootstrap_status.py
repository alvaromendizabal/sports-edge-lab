"""A failed startup cannot rewrite scientific evidence or invent identity."""
from pathlib import Path
import hashlib
import json
import unittest


ROOT = Path(__file__).resolve().parent


class BootstrapEvidence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.value = json.loads((ROOT / '2026-11-13-n084-bootstrap-mismatch.json').read_bytes())

    def test_unknown_owner_hash_is_not_guessed_from_trace(self):
        failed = self.value['failed_invocation']
        self.assertIsNone(failed['actual_owner_package_sha256'])
        self.assertFalse(failed['actual_owner_package_identity_proven'])
        self.assertNotEqual(failed['observed_entrypoint_lineage'],
                            failed['expected_delivery_entrypoint_lineage'])

    def test_failed_authentication_has_no_scientific_or_market_credit(self):
        failed = self.value['failed_invocation']
        self.assertEqual(failed['stage'], 'PACKAGE_AUTHENTICATION')
        self.assertFalse(failed['scientific_execution_reached'])
        self.assertEqual((failed['new_fits'], failed['new_forecasts'], failed['new_paid_calls']), (0, 0, 0))
        self.assertFalse(self.value['new_n085_owner_fits_claimed'])
        self.assertFalse(self.value['owner_execution_acceptance'])
        self.assertFalse(self.value['real_twelve_core_utilization_claimed'])

    def test_resource_confirmation_is_not_misreported_as_failure(self):
        failed = self.value['failed_invocation']
        self.assertTrue(failed['initial_resource_confirmation_recovered'])
        self.assertTrue(failed['authentication_lease_released'])
        self.assertEqual(failed['error'], 'Executable physical identity differs')

    def test_saved_forecasts_are_exactly_preserved(self):
        preserved = self.value['preservation']
        self.assertEqual(hashlib.sha256((ROOT / preserved['selected_forecast_file']).read_bytes()).hexdigest(),
                         preserved['selected_forecast_sha256'])
        self.assertFalse(preserved['previous_results_relabelled'])
        self.assertFalse(preserved['new_current_season_selection'])
        self.assertFalse(preserved['dashboard_or_provider_refresh_performed'])
        self.assertFalse(preserved['existing_model_cache_reset'])
        self.assertEqual(preserved['latest_authenticated_scientific_owner_run'], 'N083')


if __name__ == '__main__':
    unittest.main()
