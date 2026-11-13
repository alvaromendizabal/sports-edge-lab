"""Saved B081 facts, immutable selected outputs and B082 engineering boundaries."""
import copy
import hashlib
import json
from pathlib import Path
import re
import unittest

import build_execution_review as subject

ROOT=Path(__file__).parent

class ExecutionReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.value=json.loads((ROOT/'latest_execution_review.json').read_bytes())
        cls.public=json.loads((ROOT/'latest_research_outputs.json').read_bytes())
        cls.body=(ROOT/'latest_research_outputs.html').read_text()

    def rejected(self,edit,reason):
        value=copy.deepcopy(self.value);edit(value)
        with self.assertRaisesRegex(ValueError,reason):subject.validate(value)

    def test_actual_partial_run_and_short_native_fit_are_recorded(self):
        subject.validate(self.value)
        run=self.value['latest_owner_execution'];runtime=self.value['observed_runtime']
        self.assertEqual((run['release'],run['new_confirmed_scientific_fits'],run['new_forecasts'],run['exit_code']),('B081',1,5,2))
        self.assertEqual(runtime['peak_concurrent_scientific_fits'],1)
        self.assertEqual(runtime['peak_concurrent_native_fits_at_heartbeat_samples'],0)
        self.assertAlmostEqual(runtime['native_fit_exact_intervals']['native_fit_elapsed_seconds_sum'],2.21192068)
        self.assertFalse(runtime['twelve_core_scientific_utilization_proven'])

    def test_twelve_reserved_cores_or_transport_peak_cannot_claim_native_parallelism(self):
        self.rejected(lambda x:x['observed_runtime'].update(peak_concurrent_scientific_fits=12),'RESERVATION_IS_NOT_UTILIZATION')
        self.rejected(lambda x:x['observed_runtime'].update(twelve_core_scientific_utilization_proven=True),'RESERVATION_IS_NOT_UTILIZATION')
        obs=self.value['observed_runtime']
        self.assertEqual(obs['one_reserved_core_samples'],178);self.assertEqual(obs['twelve_reserved_core_samples'],2)
        self.assertAlmostEqual(obs['time_weighted_cpu_cores'],.8395186076897229)
        self.assertAlmostEqual(obs['peak_cpu_cores'],7.950013631756633)
        self.assertEqual(obs['transport_benchmark']['new_estimator_fits'],0)

    def test_publication_does_not_invent_work_or_rewrite_issue_clock(self):
        self.rejected(lambda x:x['latest_owner_execution'].update(new_confirmed_scientific_fits=12),'UNSUPPORTED_PROGRESS')
        self.rejected(lambda x:x['science_preservation'].update(publication_new_fits=1),'PUBLICATION_IS_NOT_SCIENCE')
        self.rejected(lambda x:x['science_preservation'].update(latest_original_issue_at_utc='2099-01-01T00:00:00Z'),'ORIGINAL_ISSUE_CLOCK')
        self.assertEqual(self.public['latest_forecast_issue_at_utc'],self.value['science_preservation']['latest_original_issue_at_utc'])

    def test_source_pins_and_exact_prior_snapshot_are_preserved(self):
        for name,pin in subject.SOURCE_PINS.items():
            self.assertEqual(hashlib.sha256((ROOT/name).read_bytes()).hexdigest(),pin,name)
        prior=json.loads((ROOT/'history/b081_prepared_execution_review.json').read_bytes())
        self.assertEqual(prior['latest_owner_execution']['release'],'B080')
        self.assertEqual(prior['replacement_engineering']['release'],'B081')
        self.assertEqual(prior['latest_owner_execution']['new_confirmed_scientific_fits'],0)

    def test_history_retains_superseded_selections_and_all_shared_objects(self):
        prior=json.loads((ROOT/'history/b077_recovered_selected_outputs.json').read_bytes())
        common=prior['issues'].keys()&self.public['issues'].keys()
        self.assertEqual(len(common),2700)
        self.assertEqual(len(prior['issues'].keys()-self.public['issues'].keys()),5)
        self.assertEqual(len(self.public['issues'].keys()-prior['issues'].keys()),5)
        for key in common:self.assertEqual(prior['issues'][key],self.public['issues'][key],key)
        self.assertEqual(prior['champions'],self.public['champions'])
        self.assertEqual(set(prior['games']),set(self.public['games']))

    def test_logger_cadence_and_successful_work_stall_are_distinct(self):
        log=self.value['live_logging']
        self.assertEqual(log['heartbeat_samples'],249);self.assertEqual(log['health_errors'],[])
        self.assertLess(log['maximum_gap_seconds'],15)
        self.assertEqual(log['observed_stall_diagnostics'],2)
        self.assertEqual(log['reproduced_false_positive_stall_diagnostics'],1)
        self.assertEqual((log['false_positive_successful_s3_gets_before'],log['false_positive_successful_s3_gets_after']),(16,5618))
        self.assertTrue(log['unobserved_progress_diagnostic_preserved'])

    def test_s3_sink_scopes_and_same_run_warm_cache_are_not_whole_pipeline_claims(self):
        log=self.value['live_logging'];cache=self.value['cache_evidence']
        self.assertEqual(log['s3_checkpoints']['scope'],'LOG_CHECKPOINT_SINK_ONLY')
        self.assertEqual(cache['measurements']['s3_gets_completed'],7970)
        self.assertFalse(cache['measurements']['all_pipeline_S3_calls_instrumented'])
        self.assertFalse(cache['repeat_read_gate']['new_owner_invocation_claim'])
        self.assertTrue(cache['repeat_read_gate']['second_pass_network_disabled'])
        self.rejected(lambda x:x['cache_evidence']['measurements'].update(all_pipeline_S3_calls_instrumented=True),'CACHE_SCOPE_CHANGED')
        self.rejected(lambda x:x['cache_evidence']['repeat_read_gate'].update(new_owner_invocation_claim=True),'WARM_CACHE_SCOPE_CHANGED')

    def test_actual_admissions_do_not_support_a_resource_denial_claim(self):
        admission=self.value['resource_admission']
        self.assertEqual(admission['exact_stage_admission_statuses'],{'ADMITTED_EXACT_THREADS':119})
        self.assertEqual(admission['native_threads_requested_counts'],{'1':114,'2':3,'3':2})
        self.assertEqual(admission['resource_deferred_stages'],{})
        self.rejected(lambda x:x['resource_admission'].update(resource_deferred_stages={'fabricated':1}),'RESOURCE_DENIAL_NOT_OBSERVED')

    def test_capacity_repair_preserves_scope_and_report_bytes(self):
        cap=self.value['capacity_failures'];budget=self.value['replacement_engineering']['budget_verification']
        self.assertGreater(cap['bound_after_first_fit_bytes'],cap['original_scientific_support_allowance_bytes'])
        self.assertLess(cap['actual_final_support_bytes'],cap['original_scientific_support_allowance_bytes'])
        self.assertEqual(budget['selected_files'],91718)
        self.assertEqual(budget['physical_files_decoded_and_original_sha256_verified']+budget['external_description_count'],91718)
        self.assertTrue(budget['all_report_original_bytes_preserved'])
        self.assertTrue(budget['conditional_on_live_verified_ancestor_graph'])
        self.assertFalse(budget['full_owner_ancestor_readback_claimed'])
        self.rejected(lambda x:x['replacement_engineering']['budget_verification'].update(full_owner_ancestor_readback_claimed=True),'SAVED_ENGINEERING_SCOPE_CHANGED')

    def test_current_clocks_and_saved_model_rows_have_no_automatic_promotion(self):
        model=json.loads((ROOT/'latest_model_review.json').read_bytes())
        self.assertEqual(model['release'],'B081');self.assertEqual(model['exporter_release'],'B082')
        self.assertEqual(len(model['metric_rows']),392)
        self.assertTrue(all(row['promotion_allowed'] is False for row in model['metric_rows']))
        self.assertEqual(model['publication_new_metric_scoring'],0)
        self.assertEqual(model['latest_original_issue_at_utc'],self.public['latest_forecast_issue_at_utc'])

    def test_deployed_other_sports_and_b082_owner_fits_are_not_inferred(self):
        self.rejected(lambda x:x['replacement_engineering'].update(owner_execution_completed=True),'NO_UNOBSERVED_OWNER_OR_CROSS_SPORT_DEPLOYMENT')
        self.rejected(lambda x:x['replacement_engineering'].update(all_deployed_sports_retrofitted=True),'NO_UNOBSERVED_OWNER_OR_CROSS_SPORT_DEPLOYMENT')
        self.assertFalse(self.value['publication']['website_deployment_verified'])

    def test_private_fields_and_cost_as_invoice_fail_closed(self):
        self.rejected(lambda x:x.update(private_note='s3://invented-private'),'PRIVATE_FIELD_OR_PATH')
        self.rejected(lambda x:x.update(recipe_id='invented-private'),'PRIVATE_FIELD_OR_PATH')
        self.rejected(lambda x:x['cost_evidence'].update(actual_billed_cost_usd=1.77),'ESTIMATE_IS_NOT_INVOICE')

    def test_shared_logger_pin_is_the_published_standalone_file(self):
        path=ROOT.parents[2]/'runtime/execution/sports_edge_live.py'
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),self.value['replacement_engineering']['shared_logging_module_sha256'])
        self.assertNotIn('from b082_runtime import',path.read_text())
        self.assertIn('class ProgressObservation:',path.read_text())

    def test_real_ten_second_acceptance_is_bound_to_current_shared_logger(self):
        fixed=self.value['replacement_engineering'];live=fixed['live_logging_acceptance']
        self.assertEqual(live['status'],'PASS')
        self.assertEqual(live['source_pins']['sports_edge_live.py']['sha256'],fixed['shared_logging_module_sha256'])
        self.assertTrue(live['sources_unchanged_through_test'])
        self.assertEqual({row['mode'] for row in live['cases']},{'stall','crash'})
        for row in live['cases']:
            self.assertEqual(row['heartbeat_interval_seconds'],10)
            self.assertLess(row['observed_max_gap_seconds'],15)
            self.assertGreater(row['tail_F_heartbeats_observed_while_child_alive'],0)
            self.assertGreater(row['human_log_growth_observations'],0)
            self.assertGreater(row['jsonl_growth_observations'],0)
            self.assertEqual(row['actual_NBA_fits'],0)
            self.assertFalse(row['actual_AWS_owner_execution'])
        self.assertEqual(next(row['child_returncode'] for row in live['cases'] if row['mode']=='crash'),1)

    def test_duplicate_unclosed_or_changed_base_page_is_rejected(self):
        with self.assertRaisesRegex(ValueError,'DUPLICATE_OR_UNCLOSED'):subject.strip_review(subject.BEGIN)
        with self.assertRaisesRegex(ValueError,'DUPLICATE_OR_UNCLOSED'):subject.strip_review(self.body+subject.BEGIN+subject.END)
        with self.assertRaisesRegex(ValueError,'BASE_DISPLAY_CHANGED'):subject.attach(self.body+'unexpected',self.value)

    def test_exact_package_and_deterministic_html_are_required_for_completion(self):
        package=self.value['replacement_engineering']['package_verification']
        self.assertEqual(package['status'],'PASS')
        self.assertEqual(package['passed'],package['packaged_tests'])
        self.assertEqual(subject.build(check=True)['status'],'PASS')
        self.assertEqual(subject.attach(self.body,self.value),self.body)
        embedded=re.search(r'<script id="nba-execution-data" type="application/json">(.*?)</script>',self.body,re.S)
        self.assertEqual(json.loads(embedded.group(1)),self.value)
        self.assertEqual(hashlib.sha256(subject.strip_review(self.body).encode()).hexdigest(),subject.BASE_DISPLAY_SHA256)

if __name__=='__main__':unittest.main()
