"""Offline falsification checks for the bounded actual-return projection."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import unittest

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location('fbs_v098_review',ROOT/'examples/fbs_contracts/v098/build_review.py')
BUILD=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BUILD)
DATA=json.loads(BUILD.DATA.read_text())


class CurrentReturnContracts(unittest.TestCase):
    def reject(self,change):
        modified=copy.deepcopy(DATA)
        change(modified)
        with self.assertRaises((ValueError,KeyError,TypeError)):
            BUILD.validate(modified)

    def test_report_is_deterministic_self_contained_and_digest_bound(self):
        output=BUILD.render(DATA)
        self.assertEqual(output,BUILD.OUTPUT.read_bytes())
        self.assertEqual(output,BUILD.render(copy.deepcopy(DATA)))
        html=output.decode()
        embedded=re.search(r'<script id="report-data" type="application/json">(.*?)</script>',html,re.S).group(1)
        self.assertEqual(json.loads(embedded),DATA)
        self.assertIn("expected='"+hashlib.sha256(embedded.encode()).hexdigest()+"'",html)
        self.assertFalse(re.search(r'<(?:script|link|img)[^>]+(?:src|href)=["\']https?://',html))
        self.assertNotIn('fetch(',html)

    def test_operational_finish_cannot_hide_partial_science(self):
        self.reject(lambda d:d['execution'].update(scientific_complete=True))
        self.reject(lambda d:d['execution'].update(supervisor_exit_code=2))
        self.reject(lambda d:d['execution'].update(return_integrity_verified=False))

    def test_tally_does_not_count_a_partial_finish_as_another_crash(self):
        self.reject(lambda d:d['execution'].update(historical_failed_attempts=7))
        self.reject(lambda d:d['execution'].update(operationally_finished_attempts=1))
        self.reject(lambda d:d['execution'].update(fully_v13_complete_attempts=1))

    def test_fitted_state_reuse_and_calibrators_are_not_new_base_fits(self):
        self.reject(lambda d:d['execution'].update(new_model_fits=306))
        self.reject(lambda d:d['execution'].update(reused_whole_jobs=12))
        self.reject(lambda d:d['execution'].update(new_model_fits=588))

    def test_old_frontier_is_not_redispatched_or_recounted(self):
        self.reject(lambda d:d['execution'].update(retained_frontier_jobs_dispatched=936))
        self.reject(lambda d:d['cpu']['scoring'].update(inherited_policies_reused_without_scoring=0))

    def test_pid_inventory_cannot_become_measured_concurrency(self):
        self.reject(lambda d:d['cpu']['phases'][0].update(max_concurrent_fits=24))
        self.reject(lambda d:d['cpu']['phases'][1].update(max_concurrent_fits=48))

    def test_short_phases_cannot_gain_an_inherited_sustained_pass(self):
        self.reject(lambda d:d['cpu'].update(current_sustained_pass=True))
        self.reject(lambda d:d['cpu'].update(prior_run_pass_transferred=True))
        self.reject(lambda d:d['cpu']['phases'][0].update(saved_prior_pass={'status':'PASS_REAL_WORK'}))
        self.reject(lambda d:d['cpu']['phases'][1].update(dispatch_wall_seconds=180))

    def test_owner_tree_and_scoring_cpu_do_not_become_optimizer_cpu(self):
        self.reject(lambda d:d['cpu']['phases'][0].update(optimizer_cpu_seconds=d['cpu']['phases'][0]['owner_tree_cpu_seconds']))
        self.reject(lambda d:d['cpu']['scoring'].update(optimizer_occupancy_claimed=True))
        self.reject(lambda d:d['cpu']['scoring'].update(worker_cpu_seconds=d['cpu']['scoring']['coordinator_cpu_seconds']))

    def test_final_cost_uses_supervisor_observation_not_interim_science(self):
        self.reject(lambda d:d['cost'].update(estimated_full_host_usd=d['cost']['science_stage_estimate_usd']))
        self.reject(lambda d:d['cost'].update(invoice=True))
        self.reject(lambda d:d['cost'].update(wall_zero_waives_guard=True))

    def test_validation_selection_rejects_test_weighting_and_sensitivity_refits(self):
        self.reject(lambda d:d['selection'].update(test_used_for_selection=True))
        self.reject(lambda d:d['selection'].update(season_training_weights=True))
        self.reject(lambda d:d['selection'].update(sensitivity_refits=1))
        self.reject(lambda d:d['selection']['leaders'][0].update(selection_score=d['selection']['leaders'][0]['annual_values'][2]))

    def test_new_evidence_cannot_invent_a_replacement_leader(self):
        self.reject(lambda d:d['selection'].update(leader_identity_changes_from_v096=1))
        self.reject(lambda d:d['selection']['new_family_best'][0].update(primary_rank=1))
        self.reject(lambda d:d['selection']['new_family_best'][0].update(selection_score=d['selection']['new_family_best'][0]['annual_values'][2]))

    def test_all_source_absent_stress_keeps_its_validation_population(self):
        self.reject(lambda d:d['selection']['new_family_best'][0].update(expected_n=[100,100,100]))
        self.reject(lambda d:d['selection']['new_family_best'][0].update(all_source_absent_validation_score=0))

    def test_t120_results_cannot_be_relabeled_as_t60(self):
        self.reject(lambda d:d['selection'].update(horizon_minutes=60))
        self.reject(lambda d:d['sources'].update(current_t60_coverage_status='T60_MODEL_ACCEPTED'))

    def test_known_cohort_does_not_erase_official_or_pending_gaps(self):
        self.reject(lambda d:d['population'].update(official_population_complete=True))
        self.reject(lambda d:d['population'].update(frozen_context_pending_feature_gaps_per_target=0))
        self.reject(lambda d:d['selection']['leaders'][0].update(scored_n=[919,934,752]))
        self.reject(lambda d:d['selection'].update(test_previously_exposed=False))

    def test_source_cells_do_not_become_original_quotes_or_market_scores(self):
        self.reject(lambda d:d['sources'].update(coverage_is_scored_benchmark=True))
        self.reject(lambda d:d['sources']['completed_horizon_coverage'][0].update(strict_original_availability_qualified_n=1))
        self.reject(lambda d:d['sources']['completed_horizon_coverage'][0].update(expected_n=1))
        self.reject(lambda d:d['sources']['historical_t60'][0].update(season=2024))

    def test_producer_inventory_does_not_become_new_cache_decoding(self):
        self.reject(lambda d:d['sources'].update(current_normalized_rows_decoded=13378))
        self.reject(lambda d:d['sources'].update(new_market_provider_requests=2))

    def test_storage_and_preparation_boundaries_cannot_be_conflated(self):
        self.reject(lambda d:d['storage'].update(new_uploaded_payload_bytes=d['storage']['control_zip_bytes']))
        self.reject(lambda d:d['storage'].update(aggregate_science_cap=512*1024*1024))
        self.reject(lambda d:d['next_preparation'].update(owner_runs_launched=1))
        self.reject(lambda d:d['next_preparation'].update(status='PREPARED_NOT_EXECUTED',native_verified=False))
        self.reject(lambda d:d['next_preparation'].update(planned_jobs_are_new_fit_promise=True))
        self.reject(lambda d:d['next_preparation']['campaign_runtime_acceptance'].update(current_acceptance='PASS'))
        self.reject(lambda d:d['next_preparation']['campaign_runtime_acceptance'].update(finite_job_completion_is_cpu_acceptance=True))
        self.reject(lambda d:d['next_preparation']['campaign_runtime_acceptance'].update(summed_short_waves_establish_pass=True))
        self.reject(lambda d:d['next_preparation']['campaign_runtime_acceptance'].update(required_representative_seconds=179))
        self.reject(lambda d:d['next_preparation']['campaign_runtime_acceptance'].update(required_minimum_useful_occupancy=0.74))
        self.reject(lambda d:d['next_preparation']['campaign_runtime_acceptance'].update(dated_v097_measurements_reclassified=True))

    def test_private_fields_and_other_owner_changes_are_rejected(self):
        self.reject(lambda d:d.update(owner='NBA'))
        self.reject(lambda d:d.update(private_payload={}))
        self.reject(lambda d:d['execution'].update(owner_path='/home/private-owner/return'))
        self.reject(lambda d:d['publication'].update(website_deployed=True))

    def test_embedded_text_cannot_close_the_script(self):
        modified=copy.deepcopy(DATA)
        modified['next_preparation']['planned_scope']='</script><img src=x onerror=alert(1)>'
        html=BUILD.render(modified).decode()
        self.assertNotIn('</script><img',html)
        embedded=re.search(r'<script id="report-data" type="application/json">(.*?)</script>',html,re.S).group(1)
        self.assertEqual(json.loads(embedded)['next_preparation']['planned_scope'],modified['next_preparation']['planned_scope'])

    def test_complete_previous_landing_and_v097_assets_are_unchanged(self):
        landing=(ROOT/'docs/fbs/README.md').read_bytes()
        if landing.startswith(b'<!-- FBS_V101_PREPARATION_START -->\n'):
            self.assertEqual(landing.count(b'<!-- FBS_V101_PREPARATION_END -->\n\n'),1)
            landing=landing.split(b'<!-- FBS_V101_PREPARATION_END -->\n\n',1)[1]
        if landing.startswith(b'<!-- FBS_V099_ACTUAL_RETURN_START -->\n'):
            landing=landing.split(b'<!-- FBS_V099_ACTUAL_RETURN_END -->\n\n',1)[1]
        start=b'<!-- FBS_V098_ACTUAL_RETURN_START -->\n'
        end=b'<!-- FBS_V098_ACTUAL_RETURN_END -->\n\n'
        self.assertTrue(landing.startswith(start))
        self.assertEqual(landing.count(start),1);self.assertEqual(landing.count(end),1)
        self.assertEqual(hashlib.sha256(landing.split(end,1)[1]).hexdigest(),'adf8059ea165cb16c8169f9c74c92eed8997860670f039d0e6553a789857e0c5')
        pins={
            'docs/fbs/v097/README.md':'252fd6a74d8071c0012a28d8591c3c420064b7b57339fa5754a0ab4085646065',
            'docs/fbs/v097/data/status.json':'6658e36df677a8f3fce9a5c47740d95904405fb5b9529cbc23db3edbbddf26c0',
            'docs/fbs/v097/index.html':'dee6fd2f83c6bbcaa07527cb9ee7f6c177765e5268c42e493b5305366187e26d',
            'examples/fbs_contracts/v097/build_review.py':'ab476cfa1b11af20f552d2aa7ae78c5eded15a7484f969153dc1c8155bd27796',
            'examples/fbs_contracts/v097/template.html.in':'5df32c1110fe630ee10d74779fa11bcd9962a508894b15e725e16720a5356d17',
        }
        for name,digest in pins.items():
            with self.subTest(path=name):
                self.assertEqual(hashlib.sha256((ROOT/name).read_bytes()).hexdigest(),digest)


if __name__=='__main__':
    unittest.main(verbosity=2)
