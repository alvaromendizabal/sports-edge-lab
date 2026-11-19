"""Guard real R33 failure/reuse evidence against false completion claims."""
from copy import deepcopy
from pathlib import Path
import base64
import hashlib
import json
import re
import unittest
import execution_latest as latest


class R33LatestExecutionTests(unittest.TestCase):
    def setUp(self):
        self.data = latest.load()

    def rejected(self, mutate):
        data = deepcopy(self.data)
        mutate(data)
        with self.assertRaises((ValueError,KeyError)):
            latest.validate(data)

    def test_automatic_internal_failure_does_not_become_user_stop_or_success(self):
        self.rejected(lambda d:d['failure'].update(user_requested_stop=True))
        self.rejected(lambda d:d['failure'].update(automatic_stop_reason='USER_REQUEST'))
        self.rejected(lambda d:d['tally'].update(successful_complete_owner_campaigns=1))
        self.assertEqual(self.data['execution']['recorded_terminal_status'],'INTERRUPTED_RESUMABLE')

    def test_receipt_integrity_does_not_certify_scientific_completion(self):
        self.rejected(lambda d:d['execution'].update(scientific_completeness='COMPLETE'))
        self.rejected(lambda d:d['execution'].update(return_sha256='0'*64))
        self.rejected(lambda d:d['source_progress'].update(full_source_coverage_certified=True))

    def test_source_work_cannot_become_worker_overlap_or_new_fits(self):
        self.rejected(lambda d:d['source_progress'].update(source_tasks_are_scientific_fits=True))
        self.rejected(lambda d:d['tally'].update(new_scientific_fits=209))
        self.rejected(lambda d:d['cpu'].update(peak_actual_scientific_workers=12))
        self.rejected(lambda d:d['cpu'].update(mean_owner_core_equivalents=36))

    def test_reused_stages_and_old_results_are_preserved_without_new_fit_credit(self):
        self.rejected(lambda d:d['tally'].update(reused_completed_stages=0))
        self.rejected(lambda d:d['tally'].update(new_scientific_fits=2))
        self.rejected(lambda d:d['tally'].update(historical_estimator_fits_reused=0))
        self.assertEqual(self.data['tally']['new_stage_completions'],1)

    def test_receipt_audit_keeps_failed_aliases_and_zero_owner_credit(self):
        self.rejected(lambda d:d['source_progress']['cache_receipt_verification'].update(distinct_successful_snapshot_ids=762))
        self.rejected(lambda d:d['source_progress']['cache_receipt_verification'].update(HTTP_422_alias_receipts=0))
        self.rejected(lambda d:d['source_progress']['cache_receipt_verification'].update(new_fits=209))
        self.rejected(lambda d:d['source_progress']['cache_receipt_verification'].update(full_source_coverage_certified=True))

    def test_prior_acceptance_is_immutable_and_not_current_throughput(self):
        self.rejected(lambda d:d['preserved_bounded_acceptance'].update(peak_real_estimator_kernel_overlap=36))
        self.rejected(lambda d:d['preserved_bounded_acceptance'].update(sustained_180_second_75_percent_gate_certified=True))

    def test_pending_r34_and_source_publication_receive_no_research_credit(self):
        self.rejected(lambda d:d['next_preparation'].update(owner_executions=1))
        self.rejected(lambda d:d['next_preparation'].update(status='PREPARED_VERIFIED',canonical_gate_passed=False))
        self.rejected(lambda d:d['publication'].update(deployment_verified=True))
        self.rejected(lambda d:d['publication'].update(new_fits=36))

    def test_new_bounded_fits_are_counted_without_overwriting_failed_owner(self):
        self.assertEqual(self.data['current_bounded_acceptance']['new_physical_fits_completed'],48)
        self.assertEqual(self.data['next_preparation']['new_scientific_fits'],48)
        self.assertEqual(self.data['tally']['new_scientific_fits'],0)
        self.assertEqual(self.data['next_preparation']['owner_executions'],0)
        self.rejected(lambda d:d['current_bounded_acceptance'].update(owner_runs=1))
        self.rejected(lambda d:d['next_preparation'].update(new_scientific_fits=0))
        self.rejected(lambda d:d['current_bounded_acceptance'].update(old_completed_units_refitted=48))

    def test_actual_worker_overlap_is_not_requested_capacity_certification(self):
        self.rejected(lambda d:d['current_bounded_acceptance'].update(peak_real_scientific_worker_overlap=36))
        self.rejected(lambda d:d['current_bounded_acceptance'].update(sustained_180_second_75_percent_gate_certified=True))
        self.rejected(lambda d:d['current_bounded_acceptance'].update(gate_eligible_seconds=182.02926496000146))
        self.rejected(lambda d:d['current_bounded_acceptance'].update(full_owner_campaign_complete=True))
        html=latest.render_panel()
        self.assertIn('48 / 48',html)
        self.assertIn('id="r34-bounded-worker-overlap">28',html)
        self.assertIn('The sustained 180-second capacity gate is not certified',html)
        self.assertIn('95.137 of 182.029',html)

    def test_separate_new_model_family_counts_do_not_promote_champions(self):
        self.rejected(lambda d:d['current_bounded_acceptance']['family_counts'].update(catboost=0))
        self.rejected(lambda d:d['current_bounded_acceptance'].update(champion_promotions=1))
        self.rejected(lambda d:d['current_bounded_acceptance'].update(test_rows_used=1))
        self.rejected(lambda d:d['current_bounded_acceptance'].update(cost_is_invoice=True))

    def test_native_engineering_is_exact_final_source_and_not_scientific_credit(self):
        engineering=self.data['next_preparation']['native_engineering']
        self.assertEqual(engineering['tests_run'],1572)
        self.assertEqual(engineering['new_scientific_fits'],0)
        self.assertIn('passed 1,572 native engineering tests',latest.render_panel())
        self.rejected(lambda d:d['next_preparation']['native_engineering'].update(new_scientific_fits=48))
        self.rejected(lambda d:d['next_preparation']['native_engineering'].update(tests_run=1569))
        self.rejected(lambda d:d['next_preparation']['native_engineering']['source'].update(sha256='1'*64))
        self.rejected(lambda d:d['next_preparation']['native_engineering'].update(report_sha256='2'*64))

    def test_test_season_and_private_boundary_remain_enforced(self):
        self.rejected(lambda d:d['science_contract'].update(test_selection_weight=.5))
        self.rejected(lambda d:d['failure'].update(explanation='s3://private/example'))
        self.rejected(lambda d:d.update(unknown_claim=True))

    def test_static_download_and_source_table_retain_exact_values(self):
        html = latest.render_panel()
        encoded=re.search(r'download="ncaa-latest-execution.json" href="data:application/json;base64,([^"]+)"',html).group(1)
        self.assertEqual(json.loads(base64.b64decode(encoded)),self.data)
        self.assertEqual(html.count('<tr>'),4)
        self.assertIn('0 fitting workers; mean owner CPU use was 0.884 cores',html)
        self.assertIn('209',html)
        self.assertIn('32 / 32',html)
        self.assertIn('not a requested user stop',html)

    def test_landing_replacement_keeps_historical_science_body_exact(self):
        from v12_public_status import strip_banner,render_banner
        index=Path(__file__).resolve().parents[2]/'docs/ncaa/index.html'
        body=strip_banner(index.read_text())
        self.assertEqual(hashlib.sha256(body.encode()).hexdigest(),'26fdce5b2c4ffd27debdcfda835d6a459e3f4a2de4edac9bf077d68e1bf3392a')
        self.assertEqual(strip_banner(render_banner(index.read_text())),body)

    def test_prepared_banner_can_replace_the_exact_pending_wrapper(self):
        import v12_public_status as public
        from unittest.mock import patch
        data = deepcopy(self.data)
        data['next_preparation'].update(status='PREPARED_VERIFIED',canonical_gate_passed=True,upload_verified=True,
            canonical_source=deepcopy(data['next_preparation']['native_engineering']['source']),
            installation_receipt_sha256='3'*64,
            native_acceptance={'report_sha256':'2'*64,'owner_dispatches':0,'provider_requests':0,'new_fits':0})
        original = '<main><article>Historical scientific body</article></main>'
        pending = original.replace('<main>','<main>'+public.PREVIOUS_R33_PREPARING_BANNER)
        with patch.object(public,'CURRENT_BANNER',latest.render_banner(data)):
            self.assertEqual(public.strip_banner(public.render_banner(pending)),original)


if __name__=='__main__':
    unittest.main()
