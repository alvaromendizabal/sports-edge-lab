"""Authentic admission failure, exact preservation and honest logging scope."""
import copy
import hashlib
import json
from pathlib import Path
import re
import unittest
from unittest.mock import patch

import b063r7_status as status
from b063r8_status import strip_banner as strip_r8_banner

ROOT=Path(__file__).resolve().parents[2]
DOC=ROOT/'docs/ncaa'
EX=ROOT/'examples/ncaa_review'
R7_LINE=b"    counts.b063r7Status = await require('./test_b063r7_status_browser.cjs').verifyR7(browser, path.join(root, 'docs/ncaa/b063r7.html'));\n"


def blob(body):
    return hashlib.sha1(b'blob '+str(len(body)).encode()+b'\0'+body).hexdigest()


class B063R7PublicStatus(unittest.TestCase):
    def setUp(self):
        self.data=status.load_payload()

    def test_actual_admission_failure_has_no_scientific_work(self):
        actual=self.data['latest_actual_owner']
        self.assertEqual(actual['release'],'B063R6')
        self.assertEqual(actual['failure_code'],'V7_INITIAL_SHARED_LEASE_UNAVAILABLE')
        self.assertEqual(actual['worker_elapsed_seconds'],1.7489990870001293)
        self.assertFalse(actual['native_preflight_entered'])
        self.assertFalse(actual['selftests_entered'])
        self.assertEqual(actual['scientific_fit_attempts'],0)
        self.assertEqual(actual['new_forecasts'],0)

    def test_unready_cpu_and_measured_pressure_are_not_a_lease(self):
        actual=self.data['actual_admission']
        self.assertEqual(actual['io_full_avg10_percent'],20.14)
        self.assertFalse(actual['cpu_measurement_ready'])
        self.assertIsNone(actual['available_cpu_cores'])
        self.assertEqual(actual['reserved_cpus'],0)
        self.assertEqual(actual['shared_lease_rechecks_observed'],0)
        self.assertTrue(actual['initial_capacity_estimate_is_not_shared_reservation'])
        self.assertFalse(self.data['prepared_continuation']['resource_guards_relaxed'])

    def test_recovery_recheck_does_not_invent_new_process_control(self):
        actual=self.data['actual_recovery']
        self.assertEqual(actual['status'],'PRIOR_PINNED_R3_RECOVERY_REVERIFIED')
        self.assertTrue(actual['safe_to_launch'])
        self.assertEqual(actual['unique_old_exact_identities_rechecked_dead'],2)
        self.assertTrue(actual['boot_changed_from_old_R3'])
        self.assertEqual(actual['new_signals_sent'],0)
        self.assertFalse(actual['new_lease_releases_claimed'])

    def test_actual_single_sample_and_unused_cache_are_honest(self):
        observer=self.data['actual_observer']; cache=self.data['actual_cache_and_cost']
        self.assertEqual(observer['included_samples'],1)
        self.assertFalse(observer['heartbeat_interval_verified'])
        self.assertFalse(observer['literal_LIVE_EXECUTION_files_present'])
        self.assertEqual(cache['pre_science_S3_full_GETs_reported'],0)
        self.assertFalse(cache['persistent_history_cache_benchmark_exercised'])
        self.assertIsNone(cache['dollar_estimate'])

    def test_original_landing_and_every_dated_page_remain_exact(self):
        pins=self.data['source_attribution']['preserved_git_blobs']
        body=strip_r8_banner((DOC/'index.html').read_text())
        self.assertEqual(blob(status.strip_banner(body).encode()),pins['docs/ncaa/index.html'])
        for name in ('docs/ncaa/b063r6.html','docs/ncaa/data/B063R6_PUBLIC_STATUS.json',
                     'docs/ncaa/b063r5.html','docs/ncaa/data/B063R5_PUBLIC_STATUS.json',
                     'docs/ncaa/b063r4.html','docs/ncaa/data/B063R4_PUBLIC_STATUS.json'):
            self.assertEqual(blob((ROOT/name).read_bytes()),pins[name])
        body=(EX/'README.md').read_bytes().split(b'<!-- B063R8_STATUS_END -->\n\n',1)[1].split(b'<!-- B063R7_STATUS_END -->\n\n',1)[1]
        self.assertEqual(blob(body),pins['examples/ncaa_review/README.md'])
        body=(EX/'test_dashboard_browser.cjs').read_bytes().replace(b"    counts.b063r8Status = await require('./test_b063r8_status_browser.cjs').verifyR8(browser, path.join(root, 'docs/ncaa/b063r8.html'));\n",b'').replace(R7_LINE,b'')
        self.assertEqual(blob(body),pins['examples/ncaa_review/test_dashboard_browser.cjs'])

    def test_exact_shared_logger_and_verified_cli_sources(self):
        logs=self.data['shared_logging_engineering']; runtime=ROOT/'runtime/execution'
        for name,key in [('sports_edge_live_runner.py','generic_supervisor_source_sha256'),
                         ('test_sports_edge_live_runner.py','generic_supervisor_test_sha256')]:
            self.assertEqual(hashlib.sha256((runtime/name).read_bytes()).hexdigest(),logs[key])
        # This dated report records the R7 logger; later cross-project repairs may evolve current source.
        self.assertEqual(logs['reused_module_sha256'],'4cd17825265aa0839392482c3387c94e8cfbf65a57874b4a3d427b028565ca5b')
        self.assertEqual(self.data['source_attribution']['preserved_git_blobs']['runtime/execution/sports_edge_live.py'],'720407053e8e1cf9440095ff5821479caf975b12')
        self.assertIn('class LiveExecutionLog:',(runtime/'sports_edge_live.py').read_text())

    def test_four_project_local_logging_is_not_deployed_science(self):
        logs=self.data['shared_logging_engineering']
        self.assertEqual([x['project'] for x in logs['cases']],logs['projects'])
        self.assertTrue(all(9.9<x['maximum_gap_seconds']<=15 for x in logs['cases']))
        self.assertTrue(all(x['source_fits_remain_unknown'] for x in logs['cases']))
        self.assertFalse(logs['all_deployed_private_runners_modified'])
        self.assertFalse(logs['actual_cloud_owner_execution'])
        self.assertFalse(logs['synthetic_CPU_probe_performed'])
        self.assertEqual(logs['scientific_fit_credit'],0)
        self.assertFalse(self.data['prepared_continuation']['owner_execution_verified'])

    def test_exact_render_and_offline_download(self):
        body=(DOC/'b063r7.html').read_text()
        match=re.search(r'<script id="b063r7-data" type="application/json">(.*?)</script>',body,re.S)
        self.assertEqual(json.loads(match.group(1)),self.data)
        self.assertEqual(json.loads((DOC/'data/B063R7_PUBLIC_STATUS.json').read_text()),self.data)
        self.assertEqual(body,status.render_page())
        self.assertNotIn('__B063R7_',body)
        self.assertIn('new Blob([exact]',body)
        self.assertIn('zero scientific-fit credit',body)
        landing=strip_r8_banner((DOC/'index.html').read_text())
        self.assertEqual(status.render_banner(landing),landing)

    def test_mutations_cannot_upgrade_admission_logging_or_science(self):
        changes=[('latest_actual_owner','scientific_fit_attempts',1),
                 ('latest_actual_owner','native_preflight_entered',True),
                 ('actual_admission','cpu_measurement_ready',True),
                 ('actual_admission','pressure_was_proved_gone_in_actual_R6',True),
                 ('actual_recovery','new_signals_sent',1),
                 ('actual_observer','heartbeat_interval_verified',True),
                 ('actual_cache_and_cost','dollar_estimate',0.01),
                 ('preserved_evidence','new_fit_credit_for_preservation',22),
                 ('prepared_continuation','owner_execution_verified',True),
                 ('shared_logging_engineering','all_deployed_private_runners_modified',True),
                 ('shared_logging_engineering','scientific_fit_credit',4),
                 ('metric_policy','current_season_complete',True)]
        for category,key,value in changes:
            changed=copy.deepcopy(self.data);changed[category][key]=value
            with self.subTest(category=category,key=key),patch.object(status.json,'loads',return_value=changed):
                with self.assertRaises(ValueError):status.load_payload()

    def test_public_status_excludes_private_runtime_and_model_data(self):
        body=(DOC/'b063r7.html').read_text()+(DOC/'data/B063R7_PUBLIC_STATUS.json').read_text()+status.BANNER
        for forbidden in [r'arn:aws:',r's3://',r'/home/sagemaker',r'AKIA[A-Z0-9]{16}',r'ASIA[A-Z0-9]{16}',
                          r'BEGIN (?:RSA |OPENSSH )?PRIVATE KEY',r'\b(?:worker_pid|frontend_pid|account_id|model_body)\b',
                          r'\.pyz(?:\b|["\'])']:
            self.assertIsNone(re.search(forbidden,body),forbidden)


if __name__=='__main__':
    unittest.main()
