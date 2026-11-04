"""Disclosure, matched-cohort and resolved-example failures must fail closed."""
import copy
import json
import unittest
from datetime import datetime, timedelta
from pathlib import Path

import public_snapshot


class PublicSnapshotTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((Path(__file__).parent / 'current_evidence.json').read_text())

    def reject(self, mutation):
        mutation(self.data)
        with self.assertRaises(ValueError):
            public_snapshot.validate_snapshot(self.data)

    def test_committed_public_csv_and_json_reconcile(self):
        data, receipt = public_snapshot.load_snapshot()
        self.assertEqual(receipt['resolved_examples'], 28)
        self.assertFalse(receipt['private_training_reproduced'])
        self.assertEqual(data['cohorts']['source_finals'], 121)
        self.assertEqual(data['cohorts']['scored_finals'], 120)

    def test_nested_paid_quote_is_rejected_not_ignored(self):
        self.reject(lambda d: d['disagreement_examples'][0].update(raw_quote={'bid': 42, 'ask': 44}))

    def test_private_recipe_field_is_rejected_not_ignored(self):
        self.reject(lambda d: d['models'][0].update(recipe_id='private-production-recipe'))

    def test_private_source_location_in_free_text_is_rejected(self):
        self.reject(lambda d: d['limitations'].append('Source s3://private-bucket/private-object'))

    def test_signed_cloud_url_in_free_text_is_rejected(self):
        self.reject(lambda d: d['limitations'].append('https://example.com/object?X-Amz-Signature=1234'))

    def test_unresolved_game_cannot_be_published_as_example(self):
        self.reject(lambda d: d['disagreement_examples'][0].update(home_score=None))

    def test_future_game_cannot_be_published_as_resolved_example(self):
        self.reject(lambda d: d['disagreement_examples'][0].update(kickoff_utc=(datetime.fromisoformat(d['as_of'])+timedelta(days=1)).isoformat()))

    def test_changing_the_actual_winner_fails(self):
        self.reject(lambda d: d['disagreement_examples'][0].update(actual_winner='NOT_A_TEAM'))

    def test_removing_a_lost_disagreement_fails(self):
        self.reject(lambda d: d['disagreement_examples'].pop(0))

    def test_duplicate_game_for_same_model_fails(self):
        self.reject(lambda d: d['disagreement_examples'].append(copy.deepcopy(d['disagreement_examples'][0])))

    def test_unrounded_probability_fails(self):
        self.reject(lambda d: d['disagreement_examples'][0].update(model_pick_probability_percent=64.2345))

    def test_omitted_required_metric_fails(self):
        self.reject(lambda d: d['models'][0].pop('log_loss'))

    def test_nonfinite_metric_fails(self):
        self.reject(lambda d: d['models'][0].update(log_loss=float('nan')))

    def test_provider_cohort_substitution_fails(self):
        self.reject(lambda d: d['common_provider_metrics'][1].update(cohort_sha256='0'*64))

    def test_late_issue_cannot_keep_t1_claim(self):
        self.reject(lambda d: d['resolved_forecast_example'].update(issued_at_utc=d['resolved_forecast_example']['kickoff_utc']))

    def test_stale_count_cannot_change_accuracy(self):
        self.reject(lambda d: d['models'][0].update(correct=78))

    def test_unverified_promotion_cannot_be_claimed(self):
        self.reject(lambda d: d['uncertainty'].update(advantage_supported=True))

    def test_restored_fit_cannot_be_added_to_new_fit_total(self):
        self.reject(lambda d: d['execution'].update(new_owner_fits=1161))

    def test_archived_provider_coverage_has_its_real_snapshot_date(self):
        template = (Path(__file__).parent / 'review.template.html').read_text()
        section = template.split('id="current-providers"', 1)[1].split('</section>', 1)[0]
        self.assertIn('data-snapshot="N033"', section)
        self.assertIn('data-as-of="' + self.data['as_of'] + '"', section)
        self.assertIn('Superseded provider coverage', section)
        self.assertIn('href="#latest-coverage"', section)

    def test_preserved_new_fit_counts_are_attributed_to_n033(self):
        template = (Path(__file__).parent / 'review.template.html').read_text()
        execution = template.split("get('current-execution').innerHTML=", 1)[1].split("\n", 1)[0]
        self.assertIn('Prior accepted N033 execution', execution)
        self.assertIn('That N033 execution added', execution)
        self.assertNotIn('This execution added', execution)


if __name__ == '__main__':
    unittest.main()
