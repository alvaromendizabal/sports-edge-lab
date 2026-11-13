"""Do not turn a failed owner invocation into false scientific completion."""
import base64
import copy
import hashlib
import json
import re
import unittest
from pathlib import Path
import execution_review_n087 as review

ROOT = Path(__file__).parent
VALUE = json.loads((ROOT/review.SOURCE).read_bytes())
FORECAST = (ROOT/VALUE['preserved_science']['selected_forecasts_file']).read_bytes()
AGGREGATE = (ROOT/VALUE['preserved_science']['aggregate_file']).read_bytes()


class FailedOwnerReviewTests(unittest.TestCase):
    def test_unknown_counts_are_not_verified_zeros(self):
        for key in ('new_fits', 'new_native_fits', 'new_meta_fits', 'new_forecasts'):
            value = copy.deepcopy(VALUE)
            value[key] = 0
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, 'UNKNOWN'):
                review.validate(value, FORECAST, AGGREGATE)

    def test_no_completion_claim_without_owner_evidence(self):
        for key in ('owner_research_acceptance', 'full_current_evidence_closure', 'completed_new_scientific_receipt', 'n087_owner_execution_claimed', 'automatic_promotion', 'source_refresh_claimed', 'website_deployment_claimed'):
            value = copy.deepcopy(VALUE)
            value[key] = True
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, 'UNSUPPORTED'):
                review.validate(value, FORECAST, AGGREGATE)

    def test_exact_preserved_scientific_bytes_and_clocks(self):
        review.validate(VALUE, FORECAST, AGGREGATE)
        source = json.loads(FORECAST)
        self.assertEqual(source['display_cutoff_utc'], VALUE['preserved_science']['display_cutoff_utc'])
        self.assertEqual(len(source['games']), 272)
        self.assertEqual(len(json.loads(AGGREGATE)['all_historical_cards']), 1530)
        for forecast, aggregate in ((FORECAST+b' ', AGGREGATE), (FORECAST, AGGREGATE+b' ')):
            with self.assertRaisesRegex(ValueError, 'PRESERVED_SCIENCE'):
                review.validate(VALUE, forecast, aggregate)

    def test_sanitized_public_boundary(self):
        body = json.dumps(VALUE) + review.panel()
        for forbidden in ('/home/', 's3://', 'recipe_id', 'feature_columns', 'model_weights', '560403859723'):
            self.assertNotIn(forbidden, body)
        self.assertIsNone(re.search(r'\b[0-9a-f]{24}\b', body))

    def test_failure_precedes_last_valid_scientific_snapshot(self):
        page = (ROOT/'season_review_n086.html').read_text()
        self.assertLess(page.index('id="latest-execution"'), page.index('id="latest-attempt"'))
        self.assertIn('New fit and forecast totals: unknown', page)
        self.assertIn('Unknown final counts are not verified zero totals', page)
        self.assertIn('physical live log streams are absent', page)

    def test_source_gets_do_not_hide_publication_readbacks(self):
        self.assertEqual(VALUE['cache']['source_gets'], 2)
        self.assertEqual(VALUE['cache']['separate_full_publication_readbacks'], 1367)
        self.assertIn('not total remote traffic', review.panel())

    def test_cpu_is_observed_failed_run_not_twelve_core_claim(self):
        self.assertLess(VALUE['mean_cpu_core_equivalents'], 1)
        self.assertEqual(VALUE['observed_optimizer_callbacks'], 0)
        self.assertIn('not twelve-core performance evidence or a speedup', review.panel())

    def test_failed_return_identity_cannot_be_substituted(self):
        value = copy.deepcopy(VALUE)
        value['owner_return_sha256'] = '0'*64
        with self.assertRaisesRegex(ValueError, 'IDENTITY'):
            review.validate(value, FORECAST, AGGREGATE)

    def test_download_is_self_contained_and_byte_exact_after_reopen(self):
        carrier = re.search(r'href="data:application/json;base64,([^"]+)"', review.panel())
        self.assertIsNotNone(carrier)
        self.assertEqual(base64.b64decode(carrier.group(1)), (ROOT/review.SOURCE).read_bytes())
