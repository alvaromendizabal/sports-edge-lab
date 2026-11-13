"""Per-run scope and earliest-bootstrap regression for the shared log adapter."""
from __future__ import annotations
import json
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import shutil
import threading
import time
import unittest
from unittest import mock

import sel_live_logging as bridge
from sports_edge_live import project_measurements


class AdapterTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.logs = []

    def tearDown(self):
        for log in self.logs:
            bridge.close(log)
        self.temp.cleanup()

    def new(self, project='nfl', **kwargs):
        log = bridge.new_run(self.root, project, **kwargs)
        self.logs.append(log)
        return log

    def rows(self, log):
        return [json.loads(line) for line in log.paths['jsonl'].read_text().splitlines()]

    def wait_state(self, log, key, expected):
        deadline = time.monotonic() + 2
        while time.monotonic() < deadline:
            with log.lock:
                if log.state.get(key) == expected:
                    return
            time.sleep(.005)
        self.fail('bridge did not deliver expected state')

    def test_four_projects_get_only_their_own_exact_per_run_files(self):
        for project in sorted(bridge.PROJECTS):
            log = self.new(project, run_id='known_'+project)
            root = self.root/'sports-edge-lab/projects'/project/'logs'/('known_'+project)
            self.assertEqual(log.paths, {'log': root/'LIVE_EXECUTION.log', 'jsonl': root/'LIVE_EXECUTION.jsonl'})
            self.assertTrue(log.paths['log'].is_file()); self.assertTrue(log.paths['jsonl'].is_file())
            first = self.rows(log)
            self.assertTrue(any(r['event']=='HEARTBEAT' for r in first))
            self.assertEqual({r['project'] for r in first}, {project})
            self.assertIsNone(log.state['cpu_project_cap'])
        self.assertEqual({p.name for p in (self.root/'sports-edge-lab/projects').iterdir()}, bridge.PROJECTS)

    def test_bad_selector_interval_and_path_are_rejected_before_other_project_writes(self):
        for project in ('ncaaf','../nba','NCAA','nfl/other'):
            with self.assertRaises(ValueError): bridge.new_run(self.root,project)
        for interval in (0,1,9.99,15.01,float('nan'),True):
            with self.assertRaises(ValueError): bridge.new_run(self.root,'nfl',flush_seconds=interval)
        for run_id in ('../old','.','/tmp/bad','bad/name'):
            with self.assertRaises(ValueError): bridge.new_run(self.root,'nfl',run_id=run_id)
        self.assertFalse((self.root/'sports-edge-lab').exists())

    def test_existing_run_and_symlink_are_never_reused(self):
        log = self.new(run_id='original')
        before = log.paths['jsonl'].read_bytes()
        with self.assertRaises(FileExistsError): self.new(run_id='original')
        self.assertEqual(log.paths['jsonl'].read_bytes(),before)
        alias = self.root/'alias';alias.symlink_to(self.root,target_is_directory=True)
        with self.assertRaises(ValueError): bridge.new_run(alias,'nba')

    def test_early_authentication_exception_subprocess_keeps_bootstrap_error_and_files(self):
        script = '''
from pathlib import Path
from sel_live_logging import new_run,error,close
import sys
log=new_run(Path(sys.argv[1]),'nfl',run_id='failed-before-owner-import')
try:
    raise ValueError('Executable physical identity differs api_key=keep-secret')
except Exception as exc:
    error(log,exc,phase='PACKAGE_IDENTITY_REJECTED')
    result=close(log,status='FAILED_AUTHENTICATION')
    assert result['closed'] and not result['adapter_close_pending_io']
    raise SystemExit(23)
'''
        env=dict(os.environ)
        env['PYTHONPATH']=str(Path(bridge.__file__).resolve().parent)+os.pathsep+env.get('PYTHONPATH','')
        run = subprocess.run([sys.executable,'-c',script,str(self.root)],capture_output=True,text=True,timeout=10,env=env)
        self.assertEqual(run.returncode,23,run.stderr)
        directory = self.root/'sports-edge-lab/projects/nfl/logs/failed-before-owner-import'
        rows = [json.loads(x) for x in (directory/'LIVE_EXECUTION.jsonl').read_text().splitlines()]
        self.assertTrue(any(r['event']=='EXECUTION_EXCEPTION' for r in rows))
        self.assertTrue(any(r['event']=='EXECUTION_LOG_CLOSED' for r in rows))
        body=(directory/'LIVE_EXECUTION.log').read_text()
        self.assertIn('physical identity differs',body);self.assertNotIn('keep-secret',body)
        self.assertTrue(all(r['data']['measurements']['fits']['new'] is None for r in rows if r['event']=='HEARTBEAT'))

    def test_metrics_are_scoped_snapshots_not_summed_or_inferred_from_cpu(self):
        log = self.new()
        event = {'schema':'owner.telemetry','stage_name':'FIT','counts':{'fits_new':8,'fits_reused':12},
            'new_native_fits':6,'new_meta_fits':2,'eta':{'status':'NO_COMPLETE_DENOMINATOR','total_remaining_eta_seconds':None},
            'remaining_by_family':{'ridge':2,'xgb':3},'s3_get_count':2,'s3_get_bytes':300,
            'cache_hits':11,'reused_local_bytes':5000,'running_compute_cost_usd':.42,
            'process_tree':{'measured_cpu_equivalents':999},'checkpoint_status':'PER_FIT_COMMITTED'}
        bridge.observe(log,event);self.wait_state(log,'stage_name','FIT')
        with log.lock: state=dict(log.state)
        measures=project_measurements(state)
        self.assertEqual(measures['fits']['new'],8);self.assertEqual(measures['fits']['reused'],12)
        self.assertIsNone(measures['fits']['completed_native_fit_returns'])
        self.assertEqual(measures['progress']['remaining_tasks'],5);self.assertIsNone(measures['progress']['eta_seconds'])
        self.assertEqual(measures['s3']['s3_get_count'],2);self.assertEqual(measures['cache']['cache_hits'],11)
        self.assertNotIn('process_tree',state)
        observed=bridge.normalize_event({'stage':'resource_admission_decision',
            'snapshot':{'elastic_project_limit':9,'per_project_ceiling':12}})
        self.assertEqual(observed['cpu_project_cap'],9)
        bridge.observe(log,{'stage_name':'NEXT_LANE','counts':{'fits_new':2,'fits_reused':1}})
        self.wait_state(log,'stage_name','NEXT_LANE')
        self.assertEqual(project_measurements(log.state)['fits']['new'],2)
        self.assertEqual(project_measurements(log.state)['experiments']['training_progress']['new_fit_credit_from_logging'],0)

    def test_active_native_and_meta_require_complete_callback_population(self):
        value=bridge.normalize_event({'observed_active_optimizer_calls':3,
            'active_optimizer_calls':[{'meta':False},{'meta':True},{'meta':False}],
            'optimizer_callback_counts':{'ENTERED':15,'RETURNED':14,'COMMITTED':13}})
        self.assertEqual(value['native']['observed_active_native_fit_workers'],2)
        self.assertEqual(value['training_progress']['observed_active_meta_fit_calls'],1)
        self.assertNotIn('real_estimator_fit_returns',value['native'])
        incomplete=bridge.normalize_event({'observed_active_optimizer_calls':12,'active_optimizer_calls':[{'meta':False}]})
        self.assertNotIn('native',incomplete)

    def test_observe_does_not_wait_on_shared_logger_io_or_lock(self):
        log=self.new();entered=threading.Event();release=threading.Event()
        original=log.update_state
        def blocked(value):
            entered.set();release.wait(5);return original(value)
        with mock.patch.object(log,'update_state',side_effect=blocked):
            bridge.observe(log,{'stage_name':'FIRST'})
            self.assertTrue(entered.wait(1))
            started=time.monotonic()
            for i in range(200):bridge.observe(log,{'stage_name':'FINAL','counts':{'fits_new':i}})
            self.assertLess(time.monotonic()-started,.5)
            with log._n085_observation_lock:
                self.assertLess(len(log._n085_pending_state),20)
            release.set()
        self.wait_state(log,'stage_name','FINAL')
        self.assertEqual(project_measurements(log.state)['fits']['new'],199)

    def test_concurrent_callbacks_leave_complete_json_lines_and_latest_state(self):
        log=self.new()
        threads=[threading.Thread(target=lambda n=n:[bridge.observe(log,{'stage_name':'FIT_'+str(n),'counts':{'fits_new':i}}) for i in range(30)]) for n in range(5)]
        for thread in threads:thread.start()
        for thread in threads:thread.join(timeout=2);self.assertFalse(thread.is_alive())
        receipt=bridge.close(log,status='FIXTURE_ONLY')
        rows=self.rows(log)
        self.assertTrue(receipt['closed']);self.assertEqual(receipt['normalized_source_events'],150)
        self.assertEqual([r['sequence'] for r in rows],list(range(1,len(rows)+1)))
        self.assertTrue(all(r['invocation_id']==log.invocation_id for r in rows))

    def test_background_error_is_not_silently_successful(self):
        log=self.new()
        with mock.patch.object(log,'update_state',side_effect=OSError('fake disk fault')):
            bridge.observe(log,{'stage_name':'FAIL'})
            deadline=time.monotonic()+1
            while not log.health_errors and time.monotonic()<deadline:time.sleep(.005)
            with self.assertRaisesRegex(RuntimeError,'OBSERVER_FAILED'):bridge.observe(log,{'stage_name':'AFTER'})
        receipt=bridge.close(log,status='FAILED_OBSERVER')
        self.assertTrue(receipt['health_errors'])

    def test_close_reports_pending_io_with_bounded_wait_then_recovers(self):
        log=self.new();release=threading.Event();entered=threading.Event();original=log.close
        def blocked_close():
            entered.set();release.wait(6);return original()
        with mock.patch.object(log,'close',side_effect=blocked_close):
            begin=time.monotonic();receipt=bridge.close(log,status='PENDING_IO_FIXTURE')
            self.assertLess(time.monotonic()-begin,3.5)
            self.assertTrue(entered.is_set());self.assertTrue(receipt['adapter_close_pending_io'])
            self.assertFalse(receipt['closed']);release.set()
            log._n085_close_worker.join(timeout=3)
        receipt=bridge.close(log,status='RECOVERED')
        self.assertTrue(receipt['closed']);self.assertFalse(receipt['adapter_close_pending_io'])

    def test_normal_periodic_heartbeat_is_ten_seconds_and_samples_real_process(self):
        log=self.new()
        child=subprocess.Popen([sys.executable,'-u','-c',
            "import sys,time;sys.stdout.write('PARTIAL_STDOUT_VISIBLE');sys.stdout.flush();time.sleep(31)"],
            stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        fsyncs=[];original_fsync=os.fsync
        stream_fds={name:stream.fileno() for name,stream in log.streams.items()}
        def record_fsync(fd):
            if fd in stream_fds.values():fsyncs.append({'at_monotonic':time.monotonic(),'fd':fd})
            return original_fsync(fd)
        try:
            with mock.patch('sports_edge_live.os.fsync',side_effect=record_fsync):
                self.assertEqual(log.supervise(child),0)
                receipt=bridge.close(log,status='LOGGING_FIXTURE_COMPLETE')
        finally:
            if child.poll() is None:child.terminate();child.wait(timeout=3)
            child.stdout.close();child.stderr.close()
        self.assertGreaterEqual(log.samples,4)
        beats=[r for r in self.rows(log) if r['event']=='HEARTBEAT']
        seen=[r for r in beats if any(p['pid']==child.pid for p in r['data']['process_tree']['processes'])]
        self.assertGreaterEqual(len(seen),3)
        gaps=[b['elapsed_seconds']-a['elapsed_seconds'] for a,b in zip(beats,beats[1:])]
        self.assertLessEqual(max(gaps),15)
        self.assertGreaterEqual(len(fsyncs),6)
        self.assertTrue(receipt['closed']);self.assertFalse(receipt['adapter_close_pending_io'])
        self.assertTrue(all(r['data']['measurements']['fits']['new'] is None for r in beats))
        self.assertIn('PARTIAL_STDOUT_VISIBLE',log.paths['log'].read_text())
        self.assertTrue(all(not r['data']['training_timeout_applied'] for r in beats))
        target=os.environ.get('N085_LIVE_CADENCE_RECEIPT')
        if target:
            target=Path(target);target.parent.mkdir(parents=True,exist_ok=True)
            copies={}
            for kind,path in log.paths.items():
                dest=target.parent/('N085_CADENCE_LIVE_EXECUTION.'+kind);shutil.copyfile(path,dest)
                copies[kind]={'path':str(dest),'bytes':dest.stat().st_size,
                    'sha256':hashlib.sha256(dest.read_bytes()).hexdigest()}
            value={'schema':'sports-edge.n085.actual-live-cadence.v1','status':'PASS',
                'requested_interval_seconds':10,'heartbeat_records':len(beats),
                'registered_child_observed_in_heartbeat_samples':len(seen),
                'heartbeat_gap_seconds':gaps,'min_observed_gap_seconds':min(gaps),
                'max_observed_gap_seconds':max(gaps),'actual_log_stream_fsync_calls':len(fsyncs),
                'stream_fsync_observations':fsyncs,'child_pid':child.pid,'child_returncode':child.returncode,
                'partial_stdout_captured':True,'actual_owner_scientific_fits':0,'synthetic_cpu_probe':False,
                'unreported_fits_remain_null':True,'closed_and_flushed':receipt['closed'],
                'project':'nfl','four_project_scope_test_separate':True,'files':copies,
                'claim_limit':'Real OS timing, child observation and physical log flush only; no owner fit or CPU-utilization acceptance.'}
            target.write_text(json.dumps(value,indent=2)+'\n')

    def test_final_snapshot_preserves_exact_names_and_is_immutable(self):
        log=self.new();bridge.observe(log,{'stage_name':'CHECKPOINT','checkpoint_status':'COMMITTED'})
        receipt=bridge.close(log,status='COMPLETE_ENGINEERING_FIXTURE')
        self.assertTrue(receipt['closed'])
        from sports_edge_live import snapshot_log_prefix
        snap=snapshot_log_prefix(log.prefix,self.root/'return-snapshot',
            expected_invocation_id=log.invocation_id,expected_project='nfl')
        self.assertEqual(snap['project'],'nfl')
        self.assertTrue((self.root/'return-snapshot').is_dir())


if __name__=='__main__':unittest.main()
