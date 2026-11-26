"""Falsify public claims while preserving private and historical boundaries."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import unittest

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location('v099_public',ROOT/'examples/fbs_contracts/v099/build_review.py')
BUILD=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(BUILD)
DATA=json.loads(BUILD.DATA.read_text())

class PublicV099(unittest.TestCase):
    def reject(self,fn):
        value=copy.deepcopy(DATA);fn(value)
        with self.assertRaises((ValueError,KeyError,TypeError)):BUILD.validate(value)

    def test_deterministic_embedded_exact_projection(self):
        raw=BUILD.render(DATA)
        self.assertEqual(raw,BUILD.OUTPUT.read_bytes());self.assertEqual(raw,BUILD.render(copy.deepcopy(DATA)))
        payload=re.search(rb'<script id="report-data" type="application/json">(.*?)</script>',raw,re.S).group(1)
        self.assertEqual(json.loads(payload),DATA)
        self.assertIn(hashlib.sha256(payload).hexdigest().encode(),raw)
        self.assertNotIn(b'fetch(',raw)

    def test_success_is_operational_and_science_remains_partial(self):
        self.reject(lambda d:d['execution'].update(scientific_complete=True))
        self.reject(lambda d:d['execution'].update(new_operational_failures=1))
        self.reject(lambda d:d['execution'].update(child_exit_code=2))

    def test_fit_reuse_and_calibration_counts_are_distinct(self):
        self.reject(lambda d:d['execution'].update(new_model_fits=1125))
        self.reject(lambda d:d['execution'].update(new_model_fits=2226))
        self.reject(lambda d:d['execution'].update(reused_fit_states=0))

    def test_old_horizon_is_preserved(self):
        self.reject(lambda d:d['execution'].update(earlier_horizon_minutes=60))
        self.reject(lambda d:d['selection'].update(horizon_minutes=120))

    def test_selection_rejects_test_labels_and_training_weights(self):
        self.reject(lambda d:d['selection'].update(test_used_for_selection=True))
        self.reject(lambda d:d['selection'].update(season_training_weights=True))
        self.reject(lambda d:d['selection'].update(sensitivity_refits=1))
        self.reject(lambda d:d['selection']['leaders'][0].update(selection_score=d['selection']['leaders'][0]['annual_values'][2]))

    def test_full_observed_denominators_cannot_be_shrunk(self):
        self.reject(lambda d:d['selection']['leaders'][0].update(scored_n=[919,934,754]))
        self.reject(lambda d:d['population'].update(official_population_complete=True))
        self.reject(lambda d:d['population'].update(postseason_completeness_proven=True))

    def test_fixed_candidate_scores_cannot_change_across_profiles(self):
        candidate=next(r for r in DATA['selection']['leaders'] if sum(x['policy_alias']==r['policy_alias'] and x['metric']==r['metric'] and x['target']==r['target'] for x in DATA['selection']['leaders'])>1)
        def change(d):
            row=next(r for r in d['selection']['leaders']if r==candidate);row['annual_values'][2]+=1
        self.reject(change)

    def test_real_sustained_window_is_current_and_measured(self):
        self.reject(lambda d:d['cpu']['windows'][0].update(representative_seconds=179))
        self.reject(lambda d:d['cpu']['windows'][0].update(useful_worker_cpu_occupancy=.5))
        self.reject(lambda d:d['cpu'].update(prior_run_pass_transferred=True))
        self.reject(lambda d:d['cpu'].update(descriptive_average_is_sustained_gate=True))

    def test_source_missing_cells_and_providers_remain_visible(self):
        self.reject(lambda d:d['sources'].update(explicit_missing_grid_cells=0))
        self.reject(lambda d:d['sources'].update(coverage_is_scored_benchmark=True))
        self.reject(lambda d:d['sources']['providers'][1].update(status='READY'))
        self.reject(lambda d:d['sources']['coverage'][0].update(rows=1))

    def test_storage_scopes_and_cost_guard_cannot_change(self):
        self.reject(lambda d:d['storage'].update(new_uploaded_payload_bytes=d['storage']['control_zip_bytes']))
        self.reject(lambda d:d['storage'].update(aggregate_science_cap=512*1024*1024))
        self.reject(lambda d:d['cost'].update(estimate_is_invoice=True))
        self.reject(lambda d:d['cost'].update(wall_zero_waives_guard=True))

    def test_next_preparation_is_unexecuted_and_not_repeated_fitting(self):
        self.reject(lambda d:d['next_preparation'].update(owner_runs_launched=1))
        self.reject(lambda d:d['next_preparation'].update(planned_new_estimator_fits=600))
        self.reject(lambda d:d['next_preparation'].update(current_runtime_acceptance='PASS'))
        self.reject(lambda d:d['next_preparation'].update(prior_cpu_pass_transferred=True))

    def test_prepared_release_claim_requires_native_identity(self):
        self.reject(lambda d:d['next_preparation'].update(status='PREPARED_NOT_EXECUTED',native_verified=False))

    def test_private_fields_nested_or_top_level_are_rejected(self):
        self.reject(lambda d:d.update(private_payload={}))
        self.reject(lambda d:d['selection']['leaders'][0].update(private_recipe='hidden'))
        self.reject(lambda d:d['next_preparation'].update(planned_scope='/home/private/owner'))
        self.reject(lambda d:d['sources']['providers'][0].update(raw_quotes=[]))

    def test_publication_cannot_become_deployment_or_other_owner(self):
        self.reject(lambda d:d.update(owner='NBA'))
        self.reject(lambda d:d['publication'].update(website_deployed=True))
        self.reject(lambda d:d['publication'].update(production_promoted=True))

    def test_embedded_data_cannot_close_script(self):
        changed=copy.deepcopy(DATA);changed['next_preparation']['planned_scope']='</script><img src=x onerror=alert(1)>'
        raw=BUILD.render(changed)
        self.assertNotIn(b'</script><img',raw)
        payload=re.search(rb'<script id="report-data" type="application/json">(.*?)</script>',raw,re.S).group(1)
        self.assertEqual(json.loads(payload)['next_preparation']['planned_scope'],changed['next_preparation']['planned_scope'])

    def test_previous_landing_and_all_v098_assets_are_byte_preserved(self):
        landing=(ROOT/'docs/fbs/README.md').read_bytes();start=b'<!-- FBS_V099_ACTUAL_RETURN_START -->\n';end=b'<!-- FBS_V099_ACTUAL_RETURN_END -->\n\n'
        if landing.startswith(b'<!-- FBS_V117_SPREAD_TOTALS_START -->\n'):
            self.assertEqual(landing.count(b'<!-- FBS_V117_SPREAD_TOTALS_END -->\n\n'), 1)
            landing = landing.split(b'<!-- FBS_V117_SPREAD_TOTALS_END -->\n\n', 1)[1]
        if landing.startswith(b'<!-- FBS_V116_SELECTED_REVIEW_START -->\n'):
            self.assertEqual(landing.count(b'<!-- FBS_V116_SELECTED_REVIEW_END -->\n\n'), 1)
            landing = landing.split(b'<!-- FBS_V116_SELECTED_REVIEW_END -->\n\n', 1)[1]
        if landing.startswith(b'<!-- FBS_V101_PREPARATION_START -->\n'):
            self.assertEqual(landing.count(b'<!-- FBS_V101_PREPARATION_END -->\n\n'),1)
            landing=landing.split(b'<!-- FBS_V101_PREPARATION_END -->\n\n',1)[1]
        self.assertTrue(landing.startswith(start));self.assertEqual(1,landing.count(start));self.assertEqual(1,landing.count(end))
        self.assertEqual(hashlib.sha256(landing.split(end,1)[1]).hexdigest(),'42e6c8c6ad6275928c4c60f431c664aa82e5d1529a596ea4083898da795bccb6')
        expected=json.loads((ROOT/'examples/fbs_contracts/v099/preserved_v098_assets.json').read_text())
        for path,digest in expected.items():
            with self.subTest(path=path):self.assertEqual(digest,hashlib.sha256((ROOT/path).read_bytes()).hexdigest())

if __name__=='__main__':unittest.main(verbosity=2)
