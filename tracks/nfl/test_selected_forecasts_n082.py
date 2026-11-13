"""A failed refresh cannot erase or re-date the last authenticated science."""
import copy
import hashlib
import json
from pathlib import Path
import unittest

import selected_review_n082 as review

ROOT = Path(__file__).parent


class N082FailurePublicationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = (ROOT / review.previous.FORECAST).read_bytes()
        cls.metrics = (ROOT / review.previous.HEALTH).read_bytes()
        cls.status = json.loads((ROOT / review.STATUS).read_bytes())

    def test_pacific_display_keeps_original_utc_clocks(self):
        self.assertEqual(review.pacific(self.status['finished_at']), 'November 12, 2026 at 17:57:18 Pacific (PST)')
        self.assertEqual(review.pacific(self.status['preserved_selected_snapshot_utc']), 'November 12, 2026 at 15:22:35 Pacific (PST)')
        page = review.render(self.raw, self.metrics, self.status)
        self.assertIn('November 12, 2026 Pacific', page)
        self.assertIn(self.status['finished_at'], page)

    def test_actual_failure_identity(self):
        self.assertEqual(self.status['owner_return'], {'bytes': 5741803, 'sha256': '48388737d5df24677f9da108616c4909b4df81dbcd7222d2a3ed26fbe70baee2'})
        self.assertEqual(self.status['owner_executable'], {'bytes': 424538313, 'sha256': '0ccdfbb08ca5d63a3fc0f414b3580e57b3a205c6c099dd74b5967672190d134d'})
        self.assertEqual(self.status['elapsed_seconds'], 112.95654879699941)
        self.assertEqual(self.status['invocation_started_at_utc'], '2026-11-13T01:55:25.298282+00:00')
        self.assertEqual(self.status['finished_at'], '2026-11-13T01:57:18.254825+00:00')
        review.validate(self.raw, self.metrics, self.status)

    def test_original_selected_source_is_unchanged(self):
        self.assertEqual(hashlib.sha256(self.raw).hexdigest(), '5fdcef74dc2eefaf6827257197977f47de7e202b18546cbdd14e8ea28e9edb84')
        self.assertEqual(hashlib.sha256(self.metrics).hexdigest(), '2b33b866319c9e309fddfda145b4662437a914916998b92945524243342e1ec8')

    def test_new_page_only_adds_failure_banner_to_original_page(self):
        page = review.render(self.raw, self.metrics, self.status)
        prior = (ROOT / 'season_review_n080.html').read_text()
        self.assertEqual(page.replace(review.banner(self.status), '', 1), prior)
        self.assertEqual(page, (ROOT / 'season_review_n082.html').read_text())
        self.assertIn('Prior valid selected snapshot: 2026-11-12T23:22:35.281084+00:00', page)

    def test_zero_attempt_work_cannot_replace_selected_rows(self):
        value = review.validate(self.raw, self.metrics, self.status)
        self.assertEqual(len(value['games']), 272)
        self.assertEqual(value['counts']['current_selected_rows'], 448)
        self.assertEqual(self.status['new_forecasts'], 0)

    def test_preserved_source_tamper_is_rejected(self):
        for raw, metrics in ((self.raw + b' ', self.metrics), (self.raw, self.metrics + b' ')):
            with self.assertRaisesRegex(ValueError, 'PRESERVED_SCIENCE_BYTES_CHANGED'):
                review.validate(raw, metrics, self.status)

    def test_invented_success_or_new_work_is_rejected(self):
        mutations = [('status', 'COMPLETE'), ('latest_attempt', 'N082')]
        mutations += [(k, 1) for k in ('new_fits', 'new_native_fits', 'new_meta_fits', 'new_forecasts', 'new_paid_calls')]
        mutations += [(k, True) for k in ('owner_research_acceptance', 'new_n082_owner_science_claimed', 'new_provider_refresh_claimed', 'automatic_promotion')]
        for key, value in mutations:
            status = copy.deepcopy(self.status); status[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                review.validate(self.raw, self.metrics, status)

    def test_retiming_or_empty_replacement_is_rejected(self):
        for key, value in (('preserved_selected_snapshot_utc', self.status['finished_at']), ('preserved_scientific_source', 'N080'), ('preserved_games', 0), ('preserved_selected_rows', 0), ('preserved_selected_games', 0)):
            status = copy.deepcopy(self.status); status[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                review.validate(self.raw, self.metrics, status)

    def test_public_failure_reason_excludes_private_runtime_details(self):
        body = json.dumps(self.status)
        for forbidden in ('/home/', 's3://', 'arn:aws:', 'n035.pyz', 'recipe_id', 'weights', 'feature_names', 'secret_key'):
            self.assertNotIn(forbidden, body)
        self.assertEqual(self.status['failure_reason'], 'Release mismatch between source writer and refresh collector')

    def test_bootstrap_paths_do_not_imply_zero_total_network_or_science(self):
        observed = self.status['bootstrap_observations']
        self.assertEqual(observed['embedded_runtime_carrier_s3_gets'], 0)
        self.assertEqual(observed['local_n079_s3_gets'], 0)
        self.assertEqual(observed['direct_older_ancestor_s3_gets'], 1)
        self.assertEqual(observed['direct_older_ancestor_s3_bytes'], 41774501)
        self.assertEqual(observed['isolated_import_preflight_seconds'], 33.10837140299918)
        self.assertEqual(observed['observed_optimizer_calls'], 0)
        self.assertIn('Separate measured bootstrap stages', observed['scope'])

    def test_prior_model_card_and_readme_are_preserved(self):
        old = (ROOT / 'README_N080_SNAPSHOT.md').read_text()
        self.assertIn('N079 took 84.07 minutes', old)
        card = (ROOT / 'CURRENT_MODEL_CARD.md').read_text()
        self.assertIn('# NFL selected model card · actual N079', card)
        self.assertIn('No N082 owner-run result', card)


if __name__ == '__main__':
    unittest.main()
