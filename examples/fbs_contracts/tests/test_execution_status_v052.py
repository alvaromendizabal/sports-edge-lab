"""Sanitized owner result and distinct source/evaluation-clock contracts."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT=Path(__file__).resolve().parents[3]


class ExecutionStatusV052Tests(unittest.TestCase):
    def setUp(self):
        self.report=json.loads((ROOT/'docs/fbs/execution-status-v052.json').read_text())

    def test_actual_owner_and_unexecuted_successor_are_distinct(self):
        self.assertEqual(self.report['owner_release'],'V051')
        self.assertEqual(self.report['prepared_successor']['release'],'V052')
        self.assertEqual(self.report['prepared_successor']['status'],'PREPARED_NOT_OWNER_EXECUTED')
        self.assertFalse(self.report['prepared_successor_execution_claimed'])
        self.assertEqual(self.report['worker_exit_observed'],2)
        self.assertEqual(self.report['supervisor_exit_observed'],2)
        self.assertFalse(self.report['outer_observer_shell_exit_independently_proved'])

    def test_no_new_science_or_source_clock_is_invented(self):
        for key in ('new_base_fits','new_calibration_fits','new_prediction_records','new_genuine_issues',
                    'new_feature_materializations','new_metric_evaluations','new_source_captures','provider_requests'):
            self.assertEqual(self.report[key],0,key)
        self.assertEqual(self.report['current_source_observed_at'],'2026-11-09T03:22:14Z')
        self.assertTrue(all(value=='NOT_REACHED'for value in self.report['scientific_stages'].values()))
        self.assertIsNone(self.report['exact_failed_resource_reason'])
        self.assertFalse(self.report['live_process_state_claimed'])

    def test_retained_original_counts_do_not_become_new_work(self):
        retained=self.report['retained_work']
        self.assertEqual(retained['successful_base_fits']+retained['successful_calibrators'],retained['successful_total'])
        self.assertEqual(retained['successful_total'],7850)
        self.assertEqual(retained['original_current_origin_issues'],108)
        self.assertEqual(retained['family_views'],216)
        self.assertTrue(retained['retained_work_is_not_new_V051_work'])
        self.assertEqual(retained['named_horizon_issues'],{'T1440':0,'T120':0,'T60':0})

    def test_original_v051_readme_and_old_status_are_preserved(self):
        old=(ROOT/'docs/fbs/README-history-v051.md').read_bytes()
        self.assertEqual(self.report['prior_readme'],{'bytes':len(old),'sha256':hashlib.sha256(old).hexdigest()})
        earlier=json.loads((ROOT/'docs/fbs/execution-status-v051.json').read_text())
        self.assertEqual(earlier['owner_release'],'V050')
        self.assertEqual(self.report['display_calendar'],earlier['display_calendar'])

    def test_public_projection_has_no_runtime_package_or_cloud_identifier(self):
        raw=json.dumps(self.report,sort_keys=True)
        for forbidden in ('s3://','arn:aws:','sagemaker-sports','/home/sagemaker-user/','/workspace/',
                          '.pyz','model_weights','feature_columns'):
            self.assertNotIn(forbidden,raw)
        data=(ROOT/'docs/fbs/execution-status-v052-data.js').read_text()
        self.assertEqual(json.loads(data.removeprefix('window.FBS_EXECUTION_STATUS_V052=').rstrip(';\n')),self.report)

    @unittest.skipUnless(shutil.which('node'),'Node is required for presentation contracts')
    def test_measured_tally_and_unknown_value_rendering(self):
        result=subprocess.run(['node','--test',str(Path(__file__).with_suffix('.cjs'))],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)


if __name__=='__main__':unittest.main()
