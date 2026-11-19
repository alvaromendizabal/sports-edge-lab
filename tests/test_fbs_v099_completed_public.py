"""Public evidence must preserve population, selection, custody and publication limits."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('completed_v099_review', ROOT/'examples/fbs_contracts/v099/completed/build_review.py')
review = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(review)


class CompletedPublicEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(review.DATA.read_bytes())

    def rejected(self, mutate, message):
        changed = copy.deepcopy(self.data)
        mutate(changed)
        with self.assertRaisesRegex(ValueError, message):
            review.validate(changed)

    def test_exact_generated_page_and_embedded_digest(self):
        actual = review.OUTPUT.read_bytes()
        self.assertEqual(review.render(self.data), actual)
        text = actual.decode()
        payload = re.search(r'<script id="report-data" type="application/json">(.*?)</script>', text, re.S).group(1)
        expected = re.search(r"expected='([a-f0-9]{64})'", text).group(1)
        self.assertEqual(hashlib.sha256(payload.encode()).hexdigest(), expected)
        self.assertEqual(json.loads(payload), self.data)

    def test_new_private_fields_rejected_at_nested_boundaries(self):
        for mutate in (
            lambda d:d.update(private_payload='hidden'),
            lambda d:d['science']['leaders'][0].update(active_recipe='hidden'),
            lambda d:d['operations']['return'].update(owner_path='/home/owner/secret'),
        ):
            with self.subTest(mutate=mutate):
                self.rejected(mutate, 'Public projection fields changed')
        self.rejected(lambda d:d['science']['caveats'].append('s3://private-bucket/model'), 'Private or out-of-scope')

    def test_equal_contender_denominators_cannot_be_shrunk(self):
        def shrink(d):
            annual=d['science']['leaders'][0]['annual'][0]
            annual['expected_n']=annual['scored_n']=900
        self.rejected(shrink, 'populations cannot shrink')
        self.rejected(lambda d:d['science']['leaders'][0]['annual'][0].update(scored_n=918,missing_n=1), 'Incomplete contender')
        self.rejected(lambda d:d['science']['source_coverage']['coverage'][0].update(observed_n=797,all_sources_absent_n=0), 'Source denominator')

    def test_test_outcomes_cannot_change_selection_or_training(self):
        self.rejected(lambda d:d['science']['outcome'].update(test_used_for_selection=True), 'Test outcomes or training')
        self.rejected(lambda d:d['operations']['science'].update(test_outcomes_used_for_selection=True), 'Validation/test')
        self.rejected(lambda d:d['science']['outcome'].update(season_training_weights=True), 'Test outcomes or training')
        self.rejected(lambda d:d['science']['leaders'][0].update(validation_score=.5), '2024/2025 only')

    def test_changing_test_metric_alone_does_not_change_validation_score(self):
        changed=copy.deepcopy(self.data)
        matching=[r for r in changed['science']['leaders'] if r['target']=='winner' and r['objective']=='log_loss']
        before=[r['validation_score'] for r in matching]
        for row in matching:
            row['annual'][2]['metric'] += .01
        review.validate(changed)
        self.assertEqual(before,[r['validation_score'] for r in matching])
        self.assertNotEqual(review.render(changed),review.render(self.data))

    def test_sensitivity_cannot_change_same_policy_base_scores(self):
        def change(d):
            row=next(r for r in d['science']['leaders'] if r['profile']=='40/60' and r['objective']=='log_loss')
            row['annual'][0]['metric'] += .01
            row['validation_score']=.4*row['annual'][0]['metric']+.6*row['annual'][1]['metric']
        self.rejected(change, 'changed base predictions')

    def test_worker_count_is_not_sustained_cpu_or_fitted_work(self):
        self.rejected(lambda d:d['operations']['cpu'].update(full_capacity_pass=True), 'Admitted workers')
        self.rejected(lambda d:d['operations']['cpu']['pipelines'][0].update(mean_useful_scoring_cpu_cores=36), 'Actual CPU calculation')
        self.rejected(lambda d:d['operations']['science'].update(new_model_fits=600), 'Scoring cannot become fitting')

    def test_finite_completion_cannot_become_full_program_or_production(self):
        self.rejected(lambda d:d['operations'].update(full_v13_program_complete=True), 'full V13')
        self.rejected(lambda d:d['science']['population'][0].update(full_census_certified=True), 'Unproved official census')
        self.rejected(lambda d:d['publication'].update(model_promotion=True), 'Publication cannot promote')
        self.rejected(lambda d:d['publication'].update(website_deployment_claimed=True), 'Publication cannot promote')

    def test_payloads_and_supervisor_closure_preserve_real_units(self):
        self.rejected(lambda d:d['operations']['payloads'].update(completed_new_unique_payloads=3000), 'counters must reconcile')
        self.rejected(lambda d:d['operations']['stages'][-1].update(status='Pending'), 'Uncompleted stage')
        self.rejected(lambda d:d['operations']['return'].update(integrity_verified=False), 'Verified return')
        self.rejected(lambda d:d['operations']['separate_refused_attempt'].update(counted_as_owner_research_failure=True), 'Duplicate launch')

    def test_negative_findings_cannot_be_relabelled_as_improvements(self):
        self.rejected(lambda d:d['science']['uncertainty'].update(improved_comparisons_holm_p_below_0_05=1), 'Unsupported significance')
        self.rejected(lambda d:d['science']['uncertainty'].update(worse_comparisons_holm_p_below_0_05=0), 'negative findings')


if __name__ == '__main__':
    unittest.main(verbosity=2)
