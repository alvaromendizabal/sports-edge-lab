"""Publication-only regressions: no NBA model execution."""
import copy
import json
from pathlib import Path
import unittest
import build_recovery_status as subject

ROOT = Path(__file__).resolve().parent


class RecoveryStatusTests(unittest.TestCase):
    def setUp(self):
        self.value = json.loads((ROOT / 'recovery_status.json').read_text())

    def test_deterministic_page_and_original_source_clock(self):
        self.assertEqual(subject.render(self.value), (ROOT / 'recovery_status.html').read_text())
        self.assertEqual(self.value['saved_public_snapshot']['evidence_as_of_utc'], '2026-11-13T17:53:05.203284Z')

    def test_later_owner_calls_cannot_become_unique_models(self):
        changed = copy.deepcopy(self.value); changed['attempts'][1]['unique_model_count'] = 28
        with self.assertRaises(AssertionError): subject.validate(changed)

    def test_unexecuted_replacement_cannot_become_execution(self):
        changed = copy.deepcopy(self.value); changed['replacement']['owner_execution_observed'] = True
        with self.assertRaises(AssertionError): subject.validate(changed)

    def test_zero_science_rerun_cannot_inherit_earlier_fits(self):
        changed = copy.deepcopy(self.value); changed['attempts'][2]['native_estimator_fit_returns'] = 318
        with self.assertRaises(AssertionError): subject.validate(changed)

    def test_private_runtime_fields_rejected(self):
        changed = copy.deepcopy(self.value); changed['private_detail'] = '/home/example/model.pkl'
        with self.assertRaises(AssertionError): subject.validate(changed)

    def test_notice_does_not_create_science(self):
        changed = copy.deepcopy(self.value); changed['publication_effects']['new_forecasts'] = 1
        with self.assertRaises(AssertionError): subject.validate(changed)


if __name__ == '__main__': unittest.main(verbosity=2)
