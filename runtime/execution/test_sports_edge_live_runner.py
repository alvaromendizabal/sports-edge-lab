"""Real local child checks for the explicit all-project supervisor CLI.

Invented child measurements are engineering fixtures, never sports fits.
"""
import concurrent.futures
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest

import sports_edge_live_runner as runner


class SupervisorCLI(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.module_dir = Path(runner.__file__).resolve().parent
        self.environment = dict(os.environ)
        self.environment['PYTHONPATH'] = str(self.module_dir)

    def command(self, script, project='nba', run_id='fixture', **kwargs):
        return [sys.executable, '-m', 'sports_edge_live_runner',
                '--project', project, '--root', str(self.root),
                '--release', 'INVENTED_ENGINEERING_FIXTURE', '--run-id', run_id,
                '--', sys.executable, '-u', '-c', script]

    def read_receipt(self, project='nba', run_id='fixture'):
        p = self.root/'projects'/project/'logs'/run_id
        return p, json.loads((p/'LIVE_EXECUTION_RECEIPT.json').read_text())

    def run_child(self, script, **kwargs):
        result = subprocess.run(self.command(script, **kwargs), env=self.environment,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=25)
        return result

    def test_all_projects_separate_literal_files_and_unknown_fits(self):
        for project in runner.PROJECTS:
            with self.subTest(project=project):
                result = self.run_child("import sys;sys.stdout.write('partial without newline');sys.stdout.flush()", project=project)
                self.assertEqual(result.returncode, 0, result.stderr)
                path, receipt = self.read_receipt(project)
                self.assertIn('partial without newline', (path/'LIVE_EXECUTION.log').read_text())
                rows = [json.loads(x) for x in (path/'LIVE_EXECUTION.jsonl').read_text().splitlines()]
                self.assertTrue(rows)
                self.assertTrue(all(row['project'] == project for row in rows))
                self.assertEqual(receipt['child_returncode'], 0)
                self.assertIsNone(receipt['last_bound_workload_measurements']['fits']['new'])
                self.assertIsNone(receipt['last_bound_workload_measurements']['fits']['concurrent_native_fits'])
                self.assertIsNone(receipt['last_bound_workload_measurements']['s3'])
                self.assertFalse(receipt['scientific_progress_inferred_from_process_activity'])
                self.assertFalse(receipt['all_deployed_projects_activated'])

    def test_child_failure_preserves_exact_exit_and_stderr(self):
        result = self.run_child("import sys;print('deliberate fixture failure',file=sys.stderr);sys.exit(7)")
        self.assertEqual(result.returncode, 7)
        path, receipt = self.read_receipt()
        self.assertEqual(receipt['child_returncode'], 7)
        self.assertIn('deliberate fixture failure', (path/'LIVE_EXECUTION.log').read_text())

    def test_child_signal_preserves_posix_exit(self):
        for number in (signal.SIGTERM, signal.SIGKILL):
            with self.subTest(number=number):
                run_id = 'signal'+str(number)
                result = self.run_child('import os;os.kill(os.getpid(),'+str(number)+')', run_id=run_id)
                self.assertEqual(result.returncode, -number, result.stderr)
                _, receipt = self.read_receipt(run_id=run_id)
                self.assertEqual(receipt['child_signal'], number)
                self.assertTrue(receipt['live_log']['closed'])

    def test_forwarded_term_reaches_only_exact_child(self):
        outsider = subprocess.Popen([sys.executable, '-c', 'import time;time.sleep(30)'])
        self.addCleanup(lambda: outsider.poll() is None and outsider.terminate())
        ready = self.root/'child_ready'
        script = ("import signal,time;from pathlib import Path;"
                  "signal.signal(signal.SIGTERM,lambda *args:exit(23));"
                  "Path("+repr(str(ready))+").write_text('ready');time.sleep(30)")
        supervisor = subprocess.Popen(self.command(script), env=self.environment,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.addCleanup(lambda: supervisor.poll() is None and supervisor.kill())
        deadline = time.monotonic()+8
        while not ready.exists() and supervisor.poll() is None and time.monotonic()<deadline:
            time.sleep(.02)
        self.assertTrue(ready.exists())
        supervisor.send_signal(signal.SIGTERM)
        stdout, stderr = supervisor.communicate(timeout=8)
        self.assertEqual(supervisor.returncode, 23, stderr)
        self.assertIsNone(outsider.poll())
        _, receipt = self.read_receipt()
        self.assertEqual(receipt['child_returncode'], 23)
        self.assertEqual(len(receipt['signals']), 1)
        self.assertTrue(receipt['signals'][0]['forwarded'])
        self.assertEqual(receipt['signals'][0]['unrelated_processes_signaled'], 0)
        outsider.terminate(); outsider.wait(timeout=3)

    def test_current_bound_progress_is_preserved_without_identity_override(self):
        script = ("from sports_edge_live_runner import publish_progress;"
                  "publish_progress({'invocation_id':'foreign','producer_identity':{},"
                  "'stage_name':'INVENTED_FIXTURE','completed':2,'remaining':3,'total':5,"
                  "'invocation_fit_counts':{'new':0,'reused':0,'failed':0},"
                  "'cache':{'hits':2,'scope':'INVENTED_TEST_COUNTERS'},"
                  "'eta_seconds':None});print('published')")
        result = self.run_child(script)
        self.assertEqual(result.returncode, 0, result.stderr)
        path, receipt = self.read_receipt()
        state = json.loads((path/'LIVE_PROGRESS.json').read_text())
        self.assertEqual(state['invocation_id'], 'fixture')
        self.assertIn('start_ticks', state['producer_identity'])
        self.assertEqual(receipt['last_bound_workload_measurements']['progress']['completed'], 2)
        self.assertIsNone(receipt['last_bound_workload_measurements']['progress']['eta_seconds'])
        self.assertEqual(receipt['last_bound_workload_measurements']['cache']['scope'], 'INVENTED_TEST_COUNTERS')

    def test_run_collision_does_not_change_prior_files(self):
        result = self.run_child("print('preserve original')")
        self.assertEqual(result.returncode, 0)
        path, _ = self.read_receipt()
        before = {x.name: hashlib.sha256(x.read_bytes()).hexdigest() for x in path.iterdir()}
        result = self.run_child("print('must not launch')")
        self.assertEqual(result.returncode, 2)
        after = {x.name: hashlib.sha256(x.read_bytes()).hexdigest() for x in path.iterdir()}
        self.assertEqual(before, after)

    def test_path_traversal_is_rejected_before_child(self):
        result = self.run_child("raise AssertionError('must not launch')", run_id='../../escaped')
        self.assertEqual(result.returncode, 2)
        self.assertFalse((self.root/'escaped').exists())

    def test_launch_failure_has_logged_receipt(self):
        command = self.command('unused')
        command = command[:command.index('--')+1]+[str(self.root/'missing_command')]
        result = subprocess.run(command, env=self.environment,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=8)
        self.assertEqual(result.returncode, 127)
        path, receipt = self.read_receipt()
        self.assertEqual(receipt['launch_error']['type'], 'FileNotFoundError')
        self.assertIn('CHILD_LAUNCH_FAILED', (path/'LIVE_EXECUTION.log').read_text())

    def test_real_ten_second_logging_continues_for_all_four_blocked_children(self):
        """Real waiting OS children; no CPU probe or scientific credit."""
        def one(project):
            return self.run_child("import time;time.sleep(11.1)", project=project, run_id='live')
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            results = list(pool.map(one, runner.PROJECTS))
        for project, result in zip(runner.PROJECTS, results):
            self.assertEqual(result.returncode, 0, result.stderr)
            path, receipt = self.read_receipt(project, 'live')
            rows = [json.loads(x) for x in (path/'LIVE_EXECUTION.jsonl').read_text().splitlines()]
            beats = [r for r in rows if r['event']=='HEARTBEAT']
            periodic = [r for r in beats if 9. <= r['elapsed_seconds'] <= 11.1]
            self.assertTrue(periodic, project)
            self.assertLessEqual(receipt['live_log']['maximum_observed_heartbeat_gap_seconds'], 15.)
            self.assertTrue(periodic[0]['data']['process_tree']['processes'])
            self.assertIsNone(periodic[0]['data']['measurements']['fits']['new'])
            self.assertIn('observed_child_processes=[{', (path/'LIVE_EXECUTION.log').read_text())


if __name__ == '__main__':
    unittest.main()
