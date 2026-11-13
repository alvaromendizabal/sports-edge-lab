"""Reject unsupported work, scope substitutions and mutation of saved outputs."""
import copy
import hashlib
import json
from pathlib import Path
import unittest
import build_execution_review as subject
from b083_html import expand_html
ROOT=Path(__file__).parent
class ExecutionReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.value=json.loads((ROOT/'latest_execution_review.json').read_bytes())
        cls.public=json.loads((ROOT/'latest_research_outputs.json').read_bytes())
    def rejected(self,edit,reason):
        value=copy.deepcopy(self.value);edit(value)
        with self.assertRaisesRegex(ValueError,reason):subject.validate(value)
    def test_actual_fit_and_issuance_scopes_are_separate(self):
        subject.validate(self.value);run=self.value['latest_owner_execution']
        self.assertEqual(sum(run['native_fit_breakdown'].values()),318)
        self.assertEqual(self.public['newest_owner_execution']['new_estimator_fits'],28)
        self.assertEqual(self.public['newest_owner_execution']['new_forecasts'],13860)
        self.assertEqual(run['new_forecast_distinct_games'],985)
    def test_native_overlap_is_not_reserved_or_sampled_workers(self):
        obs=self.value['observed_runtime'];self.assertEqual(obs['peak_concurrent_scientific_fits'],6)
        self.assertEqual(obs['peak_concurrent_native_fits_at_heartbeat_samples'],0)
        self.assertAlmostEqual(obs['native_fit_exact_intervals']['native_fit_elapsed_seconds_sum'],58.588487549)
        self.rejected(lambda x:x['observed_runtime'].update(twelve_core_scientific_utilization_proven=True),'RESERVATION_IS_NOT_UTILIZATION')
        self.rejected(lambda x:x['observed_runtime'].update(peak_concurrent_scientific_fits=12),'RESERVATION_IS_NOT_UTILIZATION')
    def test_publication_cannot_invent_work_or_new_clocks(self):
        self.rejected(lambda x:x['latest_owner_execution'].update(new_confirmed_scientific_fits=0),'UNSUPPORTED_PROGRESS')
        self.rejected(lambda x:x['science_preservation'].update(publication_new_fits=1),'PUBLICATION_IS_NOT_SCIENCE')
        self.rejected(lambda x:x['science_preservation'].update(latest_original_issue_at_utc='2099-01-01T00:00:00Z'),'ORIGINAL_ISSUE_CLOCK')
        self.assertEqual(self.public['latest_forecast_issue_at_utc'],self.value['science_preservation']['latest_original_issue_at_utc'])
    def test_current_public_pins_match_actual_files(self):
        for name,pin in subject.SOURCE_PINS.items():self.assertEqual(hashlib.sha256((ROOT/name).read_bytes()).hexdigest(),pin,name)
    def test_prior_issues_and_metric_roles_remain_exact(self):
        prior=json.loads((ROOT/'history/b081_selected_outputs.json').read_bytes());audit=json.loads((ROOT/'selected_issue_preservation.json').read_bytes())
        common=prior['issues'].keys()&self.public['issues'].keys()
        self.assertEqual(len(common),264);self.assertEqual(audit['unchanged_shared_selected_issues'],264)
        self.assertEqual(len(prior['issues'].keys()-self.public['issues'].keys()),2441)
        self.assertEqual(len(self.public['issues'].keys()-prior['issues'].keys()),13790)
        for key in common:self.assertEqual(prior['issues'][key],self.public['issues'][key],key)
        self.assertEqual(prior['champions'],self.public['champions']);self.assertEqual(set(prior['games']),set(self.public['games']))
    def test_prior_execution_and_model_history_retained(self):
        history=json.loads((ROOT/'history/b082_prepared_execution_review.json').read_bytes())
        self.assertEqual(history['latest_owner_execution']['release'],'B081');self.assertEqual(history['replacement_engineering']['release'],'B082')
        model=json.loads((ROOT/'history/b081_model_review.json').read_bytes());self.assertEqual(model['release'],'B081')
    def test_log_heartbeat_cadence_and_identity_refusals_honest(self):
        log=self.value['live_logging'];self.assertEqual(log['heartbeat_samples'],570);self.assertLess(log['maximum_gap_seconds'],15)
        self.assertEqual(log['startup_stale_origin_refusals'],1);self.assertFalse(log['identity_guards_bypassed'])
        self.assertEqual(log['internal_progress_jsonl_bytes'],1030619902)
    def test_scope_limited_cache_and_transfers_not_whole_pipeline(self):
        self.rejected(lambda x:x['cache_evidence'].update(all_pipeline_S3_calls_instrumented=True),'CACHE_SCOPE_CHANGED')
        self.rejected(lambda x:x['cache_evidence']['file_pin_operations'].update(unique_file_count_claim=True),'CACHE_OPERATIONS')
        self.assertEqual(self.value['live_logging']['s3_checkpoints']['scope'],'LOG_CHECKPOINT_SINK_ONLY')
    def test_new_forecasts_are_not_complete_future_schedule(self):
        science=self.value['science_preservation'];self.assertEqual(science['coverage']['official_future_tips_at_report'],1033)
        self.assertEqual(science['coverage']['official_games_without_original_issues'],269)
        self.assertFalse(science['full_future_schedule_complete'])
        self.rejected(lambda x:x['science_preservation'].update(full_future_schedule_complete=True),'MISSING_SCHEDULE_SCOPE_CHANGED')
    def test_saved_artifact_benchmarks_keep_byte_and_scope_proofs(self):
        fixed=self.value['replacement_engineering'];self.assertTrue(fixed['saved_artifact_engineering']['issue_inventory']['same_selected_file_pins'])
        self.rejected(lambda x:x['replacement_engineering']['saved_artifact_engineering']['report_seal'].update(full_owner_inventory_speedup_claim=True),'SAVED_ENGINEERING_SCOPE_CHANGED')
    def test_no_new_owner_run_other_sport_retrofit_or_deployment(self):
        self.rejected(lambda x:x['replacement_engineering'].update(owner_execution_completed=True),'NO_UNOBSERVED_OWNER_OR_CROSS_SPORT_DEPLOYMENT')
        self.rejected(lambda x:x['replacement_engineering'].update(all_deployed_sports_retrofitted=True),'NO_UNOBSERVED_OWNER_OR_CROSS_SPORT_DEPLOYMENT')
        self.assertFalse(self.value['publication']['website_deployment_verified'])
    def test_saved_models_pairs_and_venues_are_non_promoting(self):
        model=json.loads((ROOT/'latest_model_review.json').read_bytes());self.assertEqual(model['release'],'B082')
        self.assertEqual((len(model['metric_rows']),len(model['model_pairs']),len(model['venue_comparisons'])),(392,66,105))
        self.assertTrue(all(row['promotion_allowed'] is False for row in model['metric_rows']))
    def test_fit_documents_do_not_authenticate_omitted_model_bodies(self):
        self.rejected(lambda x:x['native_document_authentication'].update(omitted_model_bodies_authenticated_by_this_audit=True),'FIT_DOCUMENTS_ARE_NOT_MODEL_BODIES')

    def test_lossless_deterministic_display_and_data(self):
        page=(ROOT/'latest_research_outputs.html').read_text();expanded=expand_html(page)
        self.assertEqual(subject.attach(expanded,self.value),expanded)
        self.assertEqual(subject.build(check=True)['status'],'PASS')
        self.assertIn('318 native estimator fits',expanded)
if __name__=='__main__':unittest.main()
