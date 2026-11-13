"""Authenticated failure, exact history preservation, and public data limits."""
from pathlib import Path
import copy
import hashlib
import json
import re
import unittest
from unittest.mock import patch
import b063r5_status as status
from b063r6_status import strip_banner as strip_r6_only
from b063r7_status import strip_banner as strip_r7_only
from b063r8_status import strip_banner as strip_r8_only
from b063r9_status import strip_banner as strip_r9_banner
def strip_r8_banner(body):return strip_r8_only(strip_r9_banner(body))
def strip_r7_banner(body):return strip_r7_only(strip_r8_banner(body))
def strip_r6_banner(body):return strip_r6_only(strip_r7_banner(body))
ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / 'docs/ncaa'
EX = ROOT / 'examples/ncaa_review'
R5_BROWSER_LINE = b"    counts.b063r5Status = await require('./test_b063r5_status_browser.cjs').verifyR5(browser, path.join(root, 'docs/ncaa/b063r5.html'));\n"

def git_blob(body):
    return hashlib.sha1(b'blob ' + str(len(body)).encode() + b'\0' + body).hexdigest()

class B063R5PublicStatus(unittest.TestCase):
    def setUp(self):
        self.data = status.load_payload()

    def test_latest_owner_is_failed_with_zero_new_fits(self):
        actual = self.data['latest_actual_owner']
        self.assertEqual((actual['release'], actual['status'], actual['new_owner_fits']), ('B063R4', 'PREFLIGHT_FAILED', 0))
        self.assertEqual(actual['failure_stage'], 'PRELAUNCH_RECOVERY_BEFORE_NEW_WORKER')
        self.assertFalse(actual['old_R3_shutdown_verified'])
        self.assertFalse(actual['referenced_recovery_diagnostic_in_attached_return'])
        self.assertFalse(actual['whole_scientific_run_completed'])

    def test_binding_failure_does_not_invent_owner_environment_or_kernel_failure(self):
        actual = self.data['latest_actual_owner']
        self.assertTrue(actual['missing_python_pidfd_binding'])
        for key in ('specific_missing_binding','owner_python_version','owner_kernel_version','owner_libc_version','failure_clock_verified'):
            self.assertIsNone(actual[key])
        self.assertFalse(actual['kernel_pidfd_support_tested_by_failed_code'])
        self.assertEqual(actual['return_filename_time_utc'], '2026-11-13T01:33:34Z')
        self.assertFalse(actual['return_filename_time_is_failure_time'])

    def test_prior_22_and_134_are_preserved_without_new_fit_credit(self):
        saved = self.data['preserved_evidence']; prepared = self.data['prepared_continuation']
        self.assertEqual((saved['authenticated_prior_target_fits'], saved['exact_content_objects_reverified']), (22, 134))
        self.assertEqual(saved['new_fit_credit_for_preservation'], 0)
        self.assertEqual(saved['model_deserializations_in_review'], 0)
        self.assertTrue(saved['scientific_runtime_compatibility_still_required'])
        self.assertFalse(prepared['owner_execution_verified'])
        self.assertFalse(prepared['owner_environment_verified'])
        self.assertEqual(prepared['new_preparation_scientific_fits'], 0)
        self.assertFalse(prepared['engineering_tests_are_scientific_performance'])

    def test_all_prior_landing_bytes_and_r4_companion_are_unchanged(self):
        pins = self.data['source_attribution']['preserved_git_blobs']
        body = strip_r6_banner((DOC / 'index.html').read_text())
        self.assertEqual(body.count(status.START), 1)
        self.assertEqual(git_blob(status.strip_banner(body).encode()), pins['docs/ncaa/index.html'])
        for name in ('docs/ncaa/b063r4.html', 'docs/ncaa/data/B063R4_PUBLIC_STATUS.json'):
            self.assertEqual(git_blob((ROOT / name).read_bytes()), pins[name])

    def test_prior_readme_and_browser_contract_are_unchanged(self):
        pins = self.data['source_attribution']['preserved_git_blobs']
        body = (EX / 'README.md').read_bytes().split(b'<!-- B063R6_STATUS_END -->\n\n',1)[1]
        self.assertTrue(body.startswith(b'<!-- B063R5_STATUS_START -->'))
        self.assertEqual(body.count(b'<!-- B063R5_STATUS_END -->\n\n'), 1)
        self.assertEqual(git_blob(body.split(b'<!-- B063R5_STATUS_END -->\n\n', 1)[1]), pins['examples/ncaa_review/README.md'])
        body = (EX / 'test_dashboard_browser.cjs').read_bytes().replace(b"    counts.b063r9Status = await require('./test_b063r9_status_browser.cjs').verifyR9(browser, path.join(root, 'docs/ncaa/b063r9.html'));\n",b'').replace(b"    counts.b063r8Status = await require('./test_b063r8_status_browser.cjs').verifyR8(browser, path.join(root, 'docs/ncaa/b063r8.html'));\n",b'').replace(b"    counts.b063r7Status = await require('./test_b063r7_status_browser.cjs').verifyR7(browser, path.join(root, 'docs/ncaa/b063r7.html'));\n",b'').replace(b"    counts.b063r6Status = await require('./test_b063r6_status_browser.cjs').verifyR6(browser, path.join(root, 'docs/ncaa/b063r6.html'));\n",b'')
        self.assertEqual(body.count(R5_BROWSER_LINE), 1)
        self.assertEqual(git_blob(body.replace(R5_BROWSER_LINE, b'')), pins['examples/ncaa_review/test_dashboard_browser.cjs'])

    def test_exact_generation_and_downloadable_payload(self):
        page = (DOC / 'b063r5.html').read_text()
        embedded = re.search(r'<script id="b063r5-data" type="application/json">(.*?)</script>', page, re.S)
        self.assertIsNotNone(embedded)
        self.assertEqual(json.loads(embedded.group(1)), self.data)
        self.assertEqual(json.loads((DOC / 'data/B063R5_PUBLIC_STATUS.json').read_text()), self.data)
        self.assertEqual(page, status.render_page())
        self.assertNotIn('__B063R5_', page)
        self.assertIn('new Blob([exact]', page)
        self.assertIn('The return does not identify the individual missing binding', page)
        self.assertIn('filename timestamp, not a verified failure completion time', page)
        landing = strip_r6_banner((DOC / 'index.html').read_text())
        self.assertEqual(status.render_banner(landing), landing)
        self.assertEqual(status.status_outputs({DOC / 'index.html':status.strip_banner(landing)})[DOC / 'index.html'], landing)

    def test_seven_metrics_quotes_and_coverage_do_not_gain_new_evidence(self):
        metrics = self.data['metric_policy']
        self.assertEqual(metrics['metrics'], ['accuracy','log_loss','brier','margin_mae','margin_rmse','total_mae','total_rmse'])
        self.assertIsNone(metrics['new_scores'])
        for key in ('current_season_complete','rolling_or_original_issue_promotion','missing_quotes_fabricated','twelve_core_scientific_acceptance_proven','provider_refresh_performed'):
            self.assertFalse(metrics[key])
        self.assertFalse(self.data['publication']['source_publication_is_deployment'])
        self.assertFalse(self.data['publication']['website_deployment_verified'])

    def test_mutations_cannot_promote_failure_or_guess_environment(self):
        changes = [('latest_actual_owner','new_owner_fits',22),('latest_actual_owner','old_R3_shutdown_verified',True),('latest_actual_owner','owner_python_version','3.11'),('latest_actual_owner','kernel_pidfd_support_tested_by_failed_code',True),('latest_actual_owner','return_filename_time_is_failure_time',True),('preserved_evidence','new_fit_credit_for_preservation',22),('prepared_continuation','owner_execution_verified',True),('metric_policy','new_scores',{'accuracy':1}),('metric_policy','current_season_complete',True)]
        for category, key, value in changes:
            changed = copy.deepcopy(self.data); changed[category][key] = value
            with self.subTest(category=category,key=key), patch.object(status.json,'loads',return_value=changed):
                with self.assertRaises(ValueError): status.load_payload()

    def test_new_public_material_has_no_private_runtime_cloud_or_model_data(self):
        body = (DOC / 'b063r5.html').read_text() + (DOC / 'data/B063R5_PUBLIC_STATUS.json').read_text() + status.BANNER
        for forbidden in [r'arn:aws:',r's3://',r'/home/sagemaker',r'AKIA[A-Z0-9]{16}',r'ASIA[A-Z0-9]{16}',r'BEGIN (?:RSA |OPENSSH )?PRIVATE KEY',r'\b(?:worker_pid|frontend_pid|account_id|model_body)\b',r'\.pyz(?:\b|["\'])']:
            self.assertIsNone(re.search(forbidden, body), forbidden)

if __name__ == '__main__':
    unittest.main()
