"""Public failure reporting must preserve actual science, populations and privacy."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('fbs_v101_public_review', ROOT / 'examples/fbs_contracts/v101/build_review.py')
review = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(review)


class RecoveryPublicEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(review.DATA.read_bytes())

    def rejected(self, mutate, message):
        changed = copy.deepcopy(self.data)
        mutate(changed)
        with self.assertRaisesRegex(ValueError, message):
            review.validate(changed)

    def test_complete_preexisting_readme_is_preserved(self):
        raw = (ROOT / 'docs/fbs/README.md').read_bytes()
        if raw.startswith(b'<!-- FBS_V117_SPREAD_TOTALS_START -->\n'):
            self.assertEqual(raw.count(b'<!-- FBS_V117_SPREAD_TOTALS_END -->\n\n'), 1)
            raw = raw.split(b'<!-- FBS_V117_SPREAD_TOTALS_END -->\n\n', 1)[1]
        if raw.startswith(b'<!-- FBS_V116_SELECTED_REVIEW_START -->\n'):
            self.assertEqual(raw.count(b'<!-- FBS_V116_SELECTED_REVIEW_END -->\n\n'), 1)
            raw = raw.split(b'<!-- FBS_V116_SELECTED_REVIEW_END -->\n\n', 1)[1]
        start = b'<!-- FBS_V101_PREPARATION_START -->\n'
        end = b'<!-- FBS_V101_PREPARATION_END -->\n\n'
        self.assertTrue(raw.startswith(start))
        self.assertEqual(1, raw.count(start))
        self.assertEqual(1, raw.count(end))
        prior = raw.split(end, 1)[1]
        self.assertEqual(78532, len(prior))
        self.assertEqual('24080dc3b65f7b172130861ec3795c2fb2279a0b09c21cdcc8e1e9411c2db498',
                         hashlib.sha256(prior).hexdigest())

    def test_deterministic_page_and_exact_embedded_digest(self):
        actual = review.OUTPUT.read_bytes()
        self.assertEqual(review.render(self.data), actual)
        text = actual.decode()
        payload = re.search(r'<script id="report-data" type="application/json">(.*?)</script>', text, re.S).group(1)
        expected = re.search(r"expected='([a-f0-9]{64})'", text).group(1)
        self.assertEqual(hashlib.sha256(payload.encode()).hexdigest(), expected)
        self.assertEqual(json.loads(payload), self.data)

    def test_public_field_boundary_is_closed_at_every_nested_mapping(self):
        for change in (
            lambda d: d.update(private_payload='hidden'),
            lambda d: d['next_release'].update(exact_recipe='hidden'),
            lambda d: d['latest_attempt']['return'].update(private_location='hidden'),
        ):
            self.rejected(change, 'Unexpected public fields')
        self.rejected(lambda d: d['limits'].append('s3://private-bucket/payload'), 'Private or out-of-scope')

    def test_verified_return_cannot_convert_failed_execution_to_success(self):
        self.rejected(lambda d: d['latest_attempt'].update(child_exit_code=0), 'failed owner execution')
        self.rejected(lambda d: d['latest_attempt'].update(operational_status='SUCCESS'), 'Failure cannot become success')
        self.rejected(lambda d: d['latest_attempt']['return'].update(owner_execution_successful=True), 'cannot relabel owner failure')

    def test_v098_and_v099_completed_successes_are_not_reclassified(self):
        self.rejected(lambda d: d['preserved_science'][0].update(operational_status='FAILED'), 'cannot be relabeled')
        self.rejected(lambda d: d['preserved_science'][0].update(fit_jobs=0), 'fit accounting')
        self.rejected(lambda d: d['preserved_science'][1].update(new_scoring_tasks=0), 'scoring retained')

    def test_unreached_science_cannot_receive_completed_work_credit(self):
        self.rejected(lambda d: d['latest_attempt'].update(new_model_fits=765), 'Unreached science')
        self.rejected(lambda d: d['latest_attempt'].update(reused_fit_admissions_this_attempt=1125), 'Unreached science')
        self.rejected(lambda d: d['latest_attempt'].update(fit_counts_complete=True), 'accounting remains incomplete')

    def test_census_refresh_does_not_expand_old_evaluation_denominators(self):
        self.rejected(lambda d: d['model_evaluation'].update(completed_cohorts=[919,934,757]), 'Census cannot rewrite')
        self.rejected(lambda d: d['model_evaluation'].update(new_census_games_scored_by_v100=2), 'Census cannot rewrite')
        self.rejected(lambda d: d['latest_attempt']['source_refresh'].update(full_census_certified=True), 'cannot prove census')

    def test_source_calls_remain_distinct_from_science_and_market_calls(self):
        self.rejected(lambda d: d['latest_attempt']['source_refresh'].update(provider_calls=0), 'source refresh accounting')
        self.rejected(lambda d: d['latest_attempt']['source_refresh'].update(new_paid_market_calls=2), 'source refresh accounting')

    def test_selection_training_and_prior_exposure_are_preserved(self):
        self.rejected(lambda d: d['model_evaluation'].update(test_used_for_selection=True), 'selection leakage')
        self.rejected(lambda d: d['model_evaluation'].update(training_season_reweighting=True), 'selection leakage')
        self.rejected(lambda d: d['model_evaluation'].update(test_previously_exposed=False), 'Validation/test')

    def test_configured_workers_and_custody_cpu_are_not_scientific_acceptance(self):
        self.rejected(lambda d: d['performance'].update(sustained_scientific_capacity_pass=True), 'cannot prove scientific CPU')
        self.rejected(lambda d: d['performance'].update(recovery_cpu_cores=36), 'Recovery actual CPU')
        self.rejected(lambda d: d['next_release'].update(sustained_scientific_capacity_pass=True), 'not an acceptance result')

    def test_preparation_is_not_an_execution_or_production_promotion(self):
        self.rejected(lambda d: d['next_release'].update(owner_execution_started=True), 'Preparation is not execution')
        self.rejected(lambda d: d['publication'].update(website_deployment_claimed=True), 'cannot execute or deploy')
        self.rejected(lambda d: d['publication'].update(production_promoted=True), 'cannot execute or deploy')

    def test_prepared_release_needs_a_final_pin_and_validation_evidence(self):
        def unpinned(d):
            d['next_release'].update(prepared_complete=True, status='PREPARED_NOT_EXECUTED', canonical_sha256=None)
        self.rejected(unpinned, 'pin missing')
        def unchecked(d):
            d['next_release'].update(prepared_complete=True, status='PREPARED_NOT_EXECUTED', canonical_bytes=100, canonical_sha256='a'*64, validation_evidence=[])
        self.rejected(unchecked, 'preparation evidence required')

    def test_child_snapshot_cannot_become_fully_completed_science(self):
        self.rejected(lambda d: d['attempt_stages'][1].update(status='Authenticated completed'), 'Failed stage remains visible')
        self.rejected(lambda d: d.update(stage_snapshot_scope='FINAL_ALL_STAGES_COMPLETE'), 'cannot claim final supervisor')
        self.rejected(lambda d: d['attempt_stages'].pop(), 'manifest completeness')


if __name__ == '__main__':
    unittest.main(verbosity=2)
