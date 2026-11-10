"""Deterministic public evidence checks, including negative scope mutations."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import unittest

from examples.fbs_contracts.actual_owner_status import validate

ROOT = Path(__file__).resolve().parents[3]
DOCS = ROOT / 'docs/fbs'


class ActualOwnerStatusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((DOCS / 'actual-owner-v055.json').read_text())

    def mutated(self, section, key, value):
        copy = deepcopy(self.data)
        copy[section][key] = value
        return copy

    def test_authenticated_partial_counts(self):
        validate(self.data)
        self.assertEqual(self.data['frozen_comparison']['completed_cases'], 36)
        self.assertEqual(self.data['frozen_comparison']['registered_cases'], 5858)
        self.assertEqual(self.data['frozen_comparison']['remaining_cases'], 5822)
        self.assertEqual(self.data['execution']['new_base_fits'], 36)
        self.assertEqual(self.data['execution']['new_scalar_prediction_outputs'], 33336)

    def test_does_not_coerce_unknown_forecasts_or_exit_to_zero(self):
        for key in ('new_genuine_forecasts', 'outer_shell_exit'):
            with self.subTest(key=key), self.assertRaises(ValueError):
                validate(self.mutated('execution', key, 0))

    def test_rejects_task_visits_used_as_completed_cases(self):
        with self.assertRaisesRegex(ValueError, 'accounting'):
            validate(self.mutated('frozen_comparison', 'completed_cases', 100))

    def test_rejects_bool_and_negative_counts(self):
        for value in (True, -1, 36.0):
            with self.subTest(value=value), self.assertRaises(ValueError):
                validate(self.mutated('frozen_comparison', 'completed_cases', value))

    def test_rejects_unknown_private_nested_fields(self):
        for section in ('execution', 'frozen_comparison', 'prepared_successor'):
            with self.subTest(section=section), self.assertRaisesRegex(ValueError, 'public fields'):
                validate(self.mutated(section, 'feature_columns', ['invented_private_name']))

    def test_rejects_completion_or_live_speed_claim(self):
        for section, key in (('execution', 'full_research_complete'), ('execution', 'live_throughput_benchmark'), ('frozen_comparison', 'global_comparison_complete')):
            with self.subTest(key=key), self.assertRaises(ValueError):
                validate(self.mutated(section, key, True))

    def test_rejects_missing_fixture_clock_coverage(self):
        with self.assertRaisesRegex(ValueError, 'kickoff coverage'):
            validate(self.mutated('current_capture', 'unresolved_exact_kickoffs', 0))

    def test_capture_cannot_redate_prior_metric(self):
        with self.assertRaisesRegex(ValueError, 'redated'):
            validate(self.mutated('preserved_evidence', 'negative_mixture_computed_at', self.data['current_capture']['completed_at']))

    def test_rejects_preparation_as_execution(self):
        with self.assertRaises(ValueError):
            validate(self.mutated('prepared_successor', 'owner_execution_observed', True))

    def test_rejects_budget_expansion_past_frozen_limit(self):
        with self.assertRaisesRegex(ValueError, 'budget hierarchy'):
            validate(self.mutated('prepared_successor', 'study_maximum_starts', 37))

    def test_rejects_publication_fit_credit(self):
        with self.assertRaises(ValueError):
            validate(self.mutated('publication', 'new_model_fits', 36))

    def test_json_and_browser_loader_are_identical(self):
        text = (DOCS / 'actual-owner-v055-data.js').read_text()
        self.assertEqual(json.loads(text.split(' = ', 1)[1].removesuffix(';\n')), self.data)

    def test_existing_forecast_and_negative_evidence_bytes_are_preserved(self):
        pins = json.loads(Path(__file__).with_name('v056_preserved_evidence_pins.json').read_text())
        for name, expected in pins.items():
            with self.subTest(name=name):
                self.assertEqual(hashlib.sha256((DOCS / name).read_bytes()).hexdigest(), expected)

    def test_static_entry_page_explains_unknowns_and_preserves_game_controls(self):
        text = (DOCS / 'current.html').read_text()
        for value in ('id="actual-owner-v055"', 'id="prepared-v056"', 'unknown (null)', '5,822', '33,336', '211 matched games', 'current-evidence-v054.js', 'id="game-rows"', 'id="source-clock"'):
            self.assertIn(value, text)
        self.assertNotRegex(text, r'<(?:button|input|select)[^>]*(?:stake|bankroll|wager|place.bet)')

    def test_no_private_location_or_recipe_in_public_payload(self):
        encoded = json.dumps(self.data)
        self.assertIsNone(re.search(r's3://|arn:aws:|/home/sagemaker|\.pyz|candidate_grid|feature_columns|"bucket"|"account_id"', encoded))


if __name__ == '__main__':
    unittest.main()
