"""Authentic failure status cannot rewrite retained selected research evidence."""
import copy
import hashlib
import json
import re
import unittest
from pathlib import Path
from selected_review_n075 import HEALTH, render

HERE = Path(__file__).resolve().parent

class N074FailureContinuity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = (HERE / 'selected_forecasts_n073.json').read_bytes()
        cls.data = json.loads(cls.original)
        cls.health = json.loads((HERE / HEALTH).read_bytes())
        cls.page = (HERE / 'season_review_n075.html').read_text()

    def test_saved_page_exactly_reopens(self):
        self.assertEqual(self.page, render(self.original, self.health))

    def test_original_payload_is_unchanged(self):
        marker = '<script id="selected-data" type="application/json">'
        start = self.page.index(marker) + len(marker)
        end = self.page.index('</script>', start)
        self.assertEqual(json.loads(self.page[start:end]), self.data)
        self.assertEqual(hashlib.sha256(self.original).hexdigest(), self.health['retained_forecasts']['sha256'])

    def test_all_games_roles_and_outputs_retained(self):
        self.assertEqual(len(self.data['games']), 272)
        self.assertEqual(len(self.data['selected_historical_roles']), 27)
        rows = sum(len(t['current_forecasts']) for g in self.data['games'] for t in g['targets'].values())
        self.assertEqual(rows, 772)
        self.assertEqual(self.health['retained_forecasts']['future_games'], 112)

    def test_known_zeros_are_not_missing_totals(self):
        self.assertTrue(self.health['counts_known'])
        for key in ('new_fits', 'new_native_fits', 'new_meta_fits', 'new_forecasts'):
            self.assertEqual(self.health[key], 0)
        self.assertIn('Zero new fits and zero new forecasts', self.page)
        self.assertIn('Latest execution: N074 blocked', self.page)

    def test_missing_or_fabricated_count_is_rejected(self):
        for value in (None, 1):
            h = copy.deepcopy(self.health)
            h['new_fits'] = value
            with self.assertRaisesRegex(ValueError, 'KNOWN_ZERO_FAILURE_RECEIPTS_REQUIRED'):
                render(self.original, h)

    def test_no_reissue_or_promotion(self):
        self.assertFalse(self.health['automatic_promotion'])
        self.assertFalse(self.health['owner_research_acceptance'])
        self.assertFalse(self.health['retained_forecasts']['reissued'])
        self.assertFalse(self.health['new_release']['owner_executed'])
        for key in ('new_fit_credit', 'new_inference_credit', 'new_issue_credit'):
            self.assertEqual(self.health['retained_forecasts'][key], 0)

    def test_mutation_promotion_and_reissue_are_blocked(self):
        with self.assertRaisesRegex(ValueError, 'RETAINED_FORECAST_BYTES_CHANGED'):
            render(self.original + b' ', self.health)
        for key in ('automatic_promotion', 'original_predictions_changed'):
            h = copy.deepcopy(self.health)
            h[key] = True
            with self.assertRaisesRegex(ValueError, 'CANNOT_PROMOTE_OR_REISSUE'):
                render(self.original, h)

    def test_source_capture_is_not_admitted_science(self):
        s = self.health['source_activity']
        self.assertEqual(s['kalshi_rows'] + s['polymarket_rows'], s['normalized_market_rows'])
        self.assertEqual(s['qualified_current_winner_probabilities'], 0)
        self.assertEqual(s['earlier_game_response_studies_executed'], 0)
        self.assertFalse(self.health['cpu_contract']['scientific_fit_concurrency_proved'])

    def test_failure_text_is_escaped(self):
        h = copy.deepcopy(self.health)
        h['failures'][0]['effect'] = '</section><script>unsafe()</script>'
        self.assertNotIn('</section><script>unsafe()</script>', render(self.original, h))

    def test_health_has_no_private_payload(self):
        s = json.dumps(self.health)
        for token in ('recipe_id', 's3://', 'api_key', '/home/sagemaker-user', 'sagemaker-sports-edge-lab'):
            self.assertNotIn(token, s)
        self.assertIsNone(re.search(r'(?<![A-Za-z0-9])[0-9]{12}(?![A-Za-z0-9])', s))
        self.assertFalse(self.health['publication']['raw_provider_values_included'])
        self.assertFalse(self.health['publication']['website_deployed'])

if __name__ == '__main__':
    unittest.main()
