"""Actual recovery, failed science gate, and exact historical preservation."""
from pathlib import Path
import copy
import hashlib
import json
import re
import unittest
from unittest.mock import patch
import b063r6_status as status

ROOT=Path(__file__).resolve().parents[2]
DOC=ROOT/'docs/ncaa'
EX=ROOT/'examples/ncaa_review'
R6_BROWSER_LINE=b"    counts.b063r6Status = await require('./test_b063r6_status_browser.cjs').verifyR6(browser, path.join(root, 'docs/ncaa/b063r6.html'));\n"


def blob(body):
    return hashlib.sha1(b'blob '+str(len(body)).encode()+b'\0'+body).hexdigest()


class B063R6PublicStatus(unittest.TestCase):
    def setUp(self):
        self.data=status.load_payload()

    def test_actual_owner_failure_has_zero_scientific_attempts(self):
        actual=self.data['latest_actual_owner']
        self.assertEqual((actual['release'],actual['status'],actual['new_owner_fits']),
                         ('B063R5','FAILED_PARTIAL_WORK_PRESERVED',0))
        self.assertEqual(actual['failure_code'],'B032_FRESH_PACKAGE_TESTS_FAILED')
        self.assertEqual((actual['unique_startup_cases'],actual['passed_startup_cases'],
                          actual['errored_startup_cases'],actual['subtest_error_events']),(116,115,1,3))
        self.assertEqual(actual['new_scientific_fit_attempts'],0)
        self.assertEqual(actual['failed_scientific_fits'],0)
        self.assertFalse(actual['full_scientific_run_completed'])

    def test_old_owner_recovery_is_now_evidenced_with_scoped_safety(self):
        recovery=self.data['actual_recovery']
        self.assertTrue(recovery['old_worker_exit_verified'])
        self.assertTrue(recovery['registered_frontend_exit_verified'])
        self.assertTrue(recovery['exact_old_lease_released'])
        self.assertTrue(recovery['foreign_lease_records_unchanged'])
        self.assertTrue(recovery['canonical_locks_acquired_before_new_worker'])
        self.assertEqual(recovery['foreign_process_signals'],0)
        self.assertEqual(recovery['lock_files_deleted'],0)
        self.assertFalse(recovery['numeric_PID_signal_fallback'])
        self.assertTrue(recovery['forced_shutdown'])

    def test_observed_environment_is_precise_and_not_a_kernel_failure(self):
        recovery=self.data['actual_recovery']
        self.assertEqual(recovery['observed_python_version'],'3.12.15')
        self.assertFalse(recovery['observed_python_pidfd_open'])
        self.assertFalse(recovery['observed_python_pidfd_send_signal'])
        self.assertEqual(recovery['actual_backend'],'libc.pidfd_open + libc.pidfd_send_signal')
        self.assertTrue(recovery['kernel_capability_was_exercised'])

    def test_true_observer_prefix_and_fixture_preflight_keep_zero_science(self):
        observer=self.data['actual_observer']; cost=self.data['preflight_cost']
        self.assertEqual(observer['application_ledger_peak_CPU_equivalents'],0.6913211502831491)
        self.assertEqual(observer['independent_watchdog_peak_CPU_equivalents'],0.8239929701863001)
        self.assertNotIn('worker_peak_CPU_equivalents',observer)
        self.assertEqual(observer['included_samples'],5)
        self.assertEqual(len(observer['intervals_seconds']),4)
        self.assertTrue(all(9.9<n<10.1 for n in observer['intervals_seconds']))
        self.assertTrue(observer['is_return_preparation_prefix'])
        self.assertFalse(observer['complete_terminal_log_claimed'])
        self.assertFalse(observer['twelve_core_scientific_acceptance_proven'])
        self.assertEqual(cost['native_fixture_cases'],26)
        self.assertEqual(cost['native_fixture_real_sports_credit'],0)
        self.assertEqual(cost['native_fixture_cached_cases'],0)
        self.assertTrue(cost['cost_scope_excludes_prelaunch_recovery'])
        self.assertFalse(cost['cost_is_invoice_or_exclusive_project_cost'])

    def test_original_landing_and_dated_companions_are_exactly_preserved(self):
        pins=self.data['source_attribution']['preserved_git_blobs']
        body=(DOC/'index.html').read_text()
        self.assertEqual(body.count(status.START),1)
        self.assertEqual(blob(status.strip_banner(body).encode()),pins['docs/ncaa/index.html'])
        for name in ('docs/ncaa/b063r5.html','docs/ncaa/data/B063R5_PUBLIC_STATUS.json',
                     'docs/ncaa/b063r4.html','docs/ncaa/data/B063R4_PUBLIC_STATUS.json'):
            self.assertEqual(blob((ROOT/name).read_bytes()),pins[name])

    def test_old_readme_and_browser_bytes_survive_one_new_layer(self):
        pins=self.data['source_attribution']['preserved_git_blobs']
        body=(EX/'README.md').read_bytes()
        self.assertTrue(body.startswith(b'<!-- B063R6_STATUS_START -->'))
        self.assertEqual(body.count(b'<!-- B063R6_STATUS_END -->\n\n'),1)
        self.assertEqual(blob(body.split(b'<!-- B063R6_STATUS_END -->\n\n',1)[1]),pins['examples/ncaa_review/README.md'])
        body=(EX/'test_dashboard_browser.cjs').read_bytes()
        self.assertEqual(body.count(R6_BROWSER_LINE),1)
        self.assertEqual(blob(body.replace(R6_BROWSER_LINE,b'')),pins['examples/ncaa_review/test_dashboard_browser.cjs'])

    def test_exact_render_and_offline_download_data(self):
        body=(DOC/'b063r6.html').read_text()
        match=re.search(r'<script id="b063r6-data" type="application/json">(.*?)</script>',body,re.S)
        self.assertIsNotNone(match)
        self.assertEqual(json.loads(match.group(1)),self.data)
        self.assertEqual(json.loads((DOC/'data/B063R6_PUBLIC_STATUS.json').read_text()),self.data)
        self.assertEqual(body,status.render_page())
        self.assertNotIn('__B063R6_',body)
        self.assertIn('new Blob([exact]',body)
        self.assertIn('zero scientific-fit credit',body)
        landing=(DOC/'index.html').read_text()
        self.assertEqual(status.render_banner(landing),landing)
        self.assertEqual(status.status_outputs({DOC/'index.html':status.strip_banner(landing)})[DOC/'index.html'],landing)

    def test_preserved_prior_fits_and_seven_metrics_remain_qualified(self):
        saved=self.data['preserved_evidence']; metrics=self.data['metric_policy']
        self.assertEqual((saved['authenticated_prior_target_fits'],saved['exact_content_objects_reverified']),(22,134))
        self.assertEqual(saved['new_fit_credit_for_preservation'],0)
        self.assertEqual(saved['model_deserializations_in_review'],0)
        self.assertTrue(saved['scientific_runtime_compatibility_still_required'])
        self.assertEqual(metrics['metrics'],['accuracy','log_loss','brier','margin_mae','margin_rmse','total_mae','total_rmse'])
        self.assertIsNone(metrics['new_scores'])
        self.assertFalse(metrics['current_season_complete'])
        self.assertFalse(metrics['provider_refresh_performed'])
        self.assertFalse(self.data['prepared_continuation']['owner_execution_verified'])
        self.assertFalse(self.data['publication']['website_deployment_verified'])

    def test_mutations_cannot_upgrade_science_or_rewrite_observation(self):
        changes=[('latest_actual_owner','new_owner_fits',22),('latest_actual_owner','new_scientific_fit_attempts',26),
                 ('latest_actual_owner','errored_startup_cases',3),('actual_recovery','old_worker_exit_verified',False),
                 ('actual_recovery','foreign_process_signals',1),('actual_recovery','observed_python_version','3.11'),
                 ('actual_recovery','observed_python_pidfd_open',True),('actual_observer','included_samples',6),
                 ('actual_observer','twelve_core_scientific_acceptance_proven',True),
                 ('preserved_evidence','new_fit_credit_for_preservation',22),
                 ('prepared_continuation','owner_execution_verified',True),('metric_policy','new_scores',{'accuracy':1})]
        for category,key,value in changes:
            changed=copy.deepcopy(self.data);changed[category][key]=value
            with self.subTest(category=category,key=key),patch.object(status.json,'loads',return_value=changed):
                with self.assertRaises(ValueError):status.load_payload()

    def test_public_files_exclude_private_runtime_and_model_data(self):
        body=(DOC/'b063r6.html').read_text()+(DOC/'data/B063R6_PUBLIC_STATUS.json').read_text()+status.BANNER
        for forbidden in [r'arn:aws:',r's3://',r'/home/sagemaker',r'AKIA[A-Z0-9]{16}',r'ASIA[A-Z0-9]{16}',
                          r'BEGIN (?:RSA |OPENSSH )?PRIVATE KEY',r'\b(?:worker_pid|frontend_pid|account_id|model_body)\b',
                          r'\.pyz(?:\b|["\'])']:
            self.assertIsNone(re.search(forbidden,body),forbidden)


if __name__=='__main__':
    unittest.main()
