"""Meaningful failure tests for real processes, with no owner NBA computation."""
from __future__ import annotations
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest import mock

from sports_edge_live import (LiveExecutionLog, IncrementalLogCheckpoint, S3LogSink,
    SCHEMA, atomic_json, process_identity, process_tree, snapshot_log_prefix, utc)


class LiveLogTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.root = Path(self.temp.name)
    def tearDown(self):
        self.temp.cleanup()
    def logger(self, **kw):
        return LiveExecutionLog(self.root/'execution', project='nba', release='B079_TEST',
                                interval=.1, **kw)
    def rows(self):
        return [json.loads(x) for x in (self.root/'execution.jsonl').read_text().splitlines()]

    def test_protected_envelope_and_secret_redaction(self):
        with self.logger(invocation_id='ours') as logger:
            logger.event('CALLBACK', schema='foreign.schema', invocation_id='foreign',
                         authorization='secret', text='https://example/?apiKey=hidden&normal=kept Authorization: Bearer hidden_bearer')
        row = next(x for x in self.rows() if x['event'] == 'CALLBACK')
        self.assertEqual(row['schema'], SCHEMA); self.assertEqual(row['invocation_id'], 'ours')
        self.assertEqual(row['data']['schema'], 'foreign.schema')
        text = (self.root/'execution.log').read_text()
        self.assertNotIn('hidden', text); self.assertNotIn('"secret"', text)
        self.assertNotIn('hidden_bearer', text)
        self.assertIn('normal=kept', text)

    def test_same_prefix_restart_preserves_exact_existing_bytes(self):
        with self.logger(invocation_id='first') as logger: logger.event('FIRST_RUN')
        first_log = (self.root/'execution.log').read_bytes()
        first_json = (self.root/'execution.jsonl').read_bytes()
        with self.logger(invocation_id='second') as logger: logger.event('SECOND_RUN')
        self.assertTrue((self.root/'execution.log').read_bytes().startswith(first_log))
        self.assertTrue((self.root/'execution.jsonl').read_bytes().startswith(first_json))
        self.assertEqual({r['invocation_id'] for r in self.rows()}, {'first', 'second'})

    def test_active_writer_lock_prevents_interleaving(self):
        with self.logger():
            with self.assertRaisesRegex(RuntimeError, 'ACTIVE_WRITER'):
                self.logger()

    def test_bound_progress_rejects_foreign_invocation_and_producer(self):
        p = self.root/'PROGRESS.json'; origin = {'test_origin': True}
        good = {'schema': 'sel.nba.b078.progress.v1', 'invocation_id': 'mine',
                'invocation_origin': origin, 'producer_identity': process_identity(os.getpid()),
                'at_utc': utc(), 'completed': 3, 'invocation_fit_counts': {'new': 0}}
        with self.logger(invocation_id='mine', invocation_origin=origin) as logger:
            logger.bind_progress(p, process_identity(os.getpid()))
            atomic_json(p, {**good, 'invocation_id': 'old', 'completed': 999})
            row = logger.heartbeat()
            self.assertEqual(row['progress_observation']['status'], 'BOUND_PROGRESS_NOT_AVAILABLE')
            self.assertIsNone(row['measurements']['progress']['completed'])
            atomic_json(p, {**good, 'producer_identity': {**good['producer_identity'], 'start_ticks': -1}})
            row = logger.heartbeat()
            self.assertEqual(row['progress_observation']['status'], 'BOUND_PROGRESS_NOT_AVAILABLE')
            atomic_json(p, good)
            row = logger.heartbeat()
            self.assertEqual(row['measurements']['progress']['completed'], 3)
            self.assertEqual(row['progress_observation']['status'], 'CURRENT_INVOCATION_BOUND')

    def test_no_newline_output_is_visible_while_child_running(self):
        with self.logger() as logger:
            child = subprocess.Popen([sys.executable, '-u', '-c',
                "import sys,time;sys.stdout.write('VISIBLE_WITHOUT_NEWLINE');sys.stdout.flush();time.sleep(.8)"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            observed = []
            def observer():
                time.sleep(.3)
                observed.append(child.poll() is None and 'VISIBLE_WITHOUT_NEWLINE' in (self.root/'execution.log').read_text())
            thread = threading.Thread(target=observer); thread.start()
            self.assertEqual(logger.supervise(child), 0); thread.join()
            child.stdout.close(); child.stderr.close()
        self.assertEqual(observed, [True])
        captured = ''.join(r['data']['text'] for r in self.rows() if r['event'] == 'PROCESS_OUTPUT')
        self.assertEqual(captured, 'VISIBLE_WITHOUT_NEWLINE')

    def test_empty_proc_child_links_fall_back_to_exact_owner_ppid_tree(self):
        child = subprocess.Popen([sys.executable, '-c', 'import time;time.sleep(2)'])
        original = Path.read_text
        def read_text(path, *args, **kwargs):
            if path.name == 'children' and str(path).startswith('/proc/'):
                return ''
            return original(path, *args, **kwargs)
        try:
            identity = process_identity(child.pid)
            with mock.patch.object(Path, 'read_text', read_text):
                sample = process_tree(os.getpid(), process_identity(os.getpid()),
                                      registered_children=(identity,))
            self.assertTrue(sample['bounded_ppid_discovery_fallback_used'])
            self.assertIn(child.pid, {r['pid'] for r in sample['processes']})
            self.assertEqual(sample['retained_process_scope'], 'EXACT_ROOT_AND_ITS_DESCENDANTS_ONLY')
        finally:
            child.terminate(); child.wait(timeout=3)

    def test_tick_callback_failure_does_not_abandon_child_or_pipe(self):
        with self.logger() as logger:
            child = subprocess.Popen([sys.executable, '-u', '-c',
                "import sys,time;print('started');time.sleep(.35);print('finished')"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            requests = []
            def bad_tick(row): raise ValueError('injected_tick_failure')
            self.assertEqual(logger.supervise(child, on_tick=bad_tick,
                on_observer_error=lambda errors: requests.append(errors)), 0)
            child.stdout.close(); child.stderr.close()
        self.assertEqual(len(requests), 1)
        self.assertIsNotNone(child.returncode)
        self.assertIn('finished', (self.root/'execution.log').read_text())
        self.assertTrue(logger.receipt()['health_errors'])

    def test_failed_log_capture_keeps_draining_child_and_recovery_callback(self):
        with self.logger() as logger:
            original = logger.event
            def fail_output(kind, **kw):
                if kind == 'PROCESS_OUTPUT': raise OSError('injected_log_write_failure')
                return original(kind, **kw)
            logger.event = fail_output
            child = subprocess.Popen([sys.executable, '-u', '-c',
                "import sys,time;print('first');time.sleep(.2);print('second')"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            requests = []
            self.assertEqual(logger.supervise(child, on_observer_error=lambda errors: requests.append(errors)), 0)
            child.stdout.close(); child.stderr.close()
            logger.event = original
        self.assertEqual(len(requests), 1)
        self.assertGreaterEqual(len(logger.receipt()['health_errors']), 1)

    def test_snapshot_is_immutable_prefix_live_log_continues(self):
        with self.logger() as logger:
            logger.event('BEFORE_SNAPSHOT')
            receipt = logger.snapshot(self.root/'return_logs')
            pins = {k: Path(v['path']).read_bytes() for k, v in receipt['files'].items()}
            logger.event('AFTER_SNAPSHOT')
            for key, body in pins.items():
                self.assertTrue(logger.paths[key].read_bytes().startswith(body))
                self.assertNotIn(b'AFTER_SNAPSHOT', body)
                self.assertEqual(hashlib.sha256(body).hexdigest(), receipt['files'][key]['sha256'])

    def test_finalizer_snapshot_clips_incomplete_tail_without_changing_source(self):
        with self.logger(invocation_id='current') as logger: logger.event('SOURCE_COMPLETE')
        path = self.root/'execution.jsonl'; partial = b'{"unfinished":'
        with path.open('ab') as stream: stream.write(partial)
        original = path.read_bytes()
        receipt = snapshot_log_prefix(self.root/'execution', self.root/'snapshot',
            expected_invocation_id='current', expected_project='nba')
        self.assertEqual(path.read_bytes(), original)
        self.assertEqual(receipt['files']['jsonl']['excluded_incomplete_tail_bytes'], len(partial))
        self.assertEqual(Path(receipt['files']['jsonl']['path']).read_bytes(), original[:-len(partial)])

    def test_finalizer_snapshot_rejects_wrong_invocation_or_project(self):
        with self.logger(invocation_id='current'): pass
        with self.assertRaisesRegex(ValueError, 'CURRENT_INVOCATION_ABSENT'):
            snapshot_log_prefix(self.root/'execution', self.root/'snapshot_wrong_run',
                expected_invocation_id='foreign', expected_project='nba')
        with self.assertRaisesRegex(ValueError, 'ENVELOPE_MISMATCH'):
            snapshot_log_prefix(self.root/'execution', self.root/'snapshot_wrong_project',
                expected_invocation_id='current', expected_project='nfl')

    def test_incremental_checkpoint_reuses_offsets_even_after_restart(self):
        put_calls = []; bodies = {}
        def put(key, body, meta):
            put_calls.append(key); bodies[key] = body
            return {'status': 'PUT_CONFIRMED'}
        checkpoint = IncrementalLogCheckpoint(self.root/'checkpoints', put, max_chunk_bytes=4096)
        p = self.root/'log'; p.write_bytes(b'A'*5000)
        req = {'invocation_id': 'one', 'project': 'nba', 'paths': {'log': str(p)}, 'limits': {'log': p.stat().st_size}}
        first = checkpoint(req); old = len(put_calls)
        second = checkpoint(req)
        self.assertEqual(len(put_calls), old); self.assertEqual(second['new_compressed_bytes'], 0)
        with p.open('ab') as stream: stream.write(b'B'*32)
        third = checkpoint({**req, 'invocation_id': 'two', 'limits': {'log': p.stat().st_size}})
        self.assertEqual(third['new_source_bytes'], 32)
        self.assertEqual(gzip.decompress(bodies[third['new_chunks'][0]['key']]), b'B'*32)
        self.assertEqual(first['new_source_bytes'], 5000)
        remote_manifest = json.loads(gzip.decompress(bodies[third['new_manifest']['key']]))
        self.assertEqual(sum(x['source_bytes'] for x in remote_manifest['chunks']), 5032)

    def test_failed_checkpoint_does_not_advance_offset(self):
        fail = [True]
        def put(key, body, meta):
            if fail[0]: raise OSError('injected_network_failure')
            return {'status': 'PUT_CONFIRMED'}
        checkpoint = IncrementalLogCheckpoint(self.root/'checkpoints', put)
        p = self.root/'log'; p.write_bytes(b'hello')
        req = {'invocation_id': 'one', 'project': 'nba', 'paths': {'log': str(p)}, 'limits': {'log': 5}}
        with self.assertRaises(OSError): checkpoint(req)
        fail[0] = False
        self.assertEqual(checkpoint(req)['new_source_bytes'], 5)

    def test_manifest_retry_does_not_reupload_acknowledged_log_chunks(self):
        failed = [False]; calls = []
        def put(key, body, meta):
            calls.append(key)
            if '/manifests/' in key and not failed[0]:
                failed[0] = True; raise OSError('injected_manifest_upload_failure')
            return {'status': 'PUT_CONFIRMED'}
        checkpoint = IncrementalLogCheckpoint(self.root/'checkpoints', put)
        p = self.root/'log'; p.write_bytes(b'hello')
        req = {'invocation_id': 'one', 'project': 'nba', 'paths': {'log': str(p)}, 'limits': {'log': 5}}
        with self.assertRaises(OSError): checkpoint(req)
        result = checkpoint(req)
        self.assertEqual(len([x for x in calls if '/log/' in x]), 1)
        self.assertIsNotNone(result['new_manifest'])
        self.assertEqual(result['new_source_bytes'], 0)

    def test_checkpoint_network_wait_does_not_stop_heartbeat(self):
        started = threading.Event(); release = threading.Event()
        def sink(req): started.set(); release.wait(4); return {'fixture': True}
        with self.logger(checkpoint_sink=sink) as logger:
            logger.request_checkpoint(); self.assertTrue(started.wait(1))
            time.sleep(.45)
            self.assertGreaterEqual(len([r for r in self.rows() if r['event'] == 'HEARTBEAT']), 3)
            release.set()
        self.assertEqual(logger.receipt()['health_errors'], [])

    def test_s3_sink_records_actual_requests_and_bytes_without_get_or_list(self):
        class FakeS3:
            def __init__(self): self.requests = []
            def put_object(self, **kw):
                self.requests.append(kw)
                return {'ChecksumSHA256': kw['ChecksumSHA256'], 'ETag': 'not-a-sha', 'VersionId': 'fixture-version'}
        client = FakeS3(); sink = S3LogSink(client, 'fixture-bucket', 'tracks/nba/logs')
        result = sink('nba/run/log.gz', b'123', {'sha256': hashlib.sha256(b'123').hexdigest()})
        self.assertEqual(result['status'], 'PUT_CONFIRMED')
        self.assertEqual(sink.receipt()['attempted_body_bytes'], 3)
        self.assertEqual(sink.receipt()['get_calls'], 0); self.assertEqual(sink.receipt()['list_calls'], 0)
        self.assertEqual(len(client.requests), 1)

    def test_supported_project_selectors_share_same_real_framework(self):
        for project in ('nfl', 'fbs', 'nba', 'ncaa_basketball', 'other_project'):
            with LiveExecutionLog(self.root/project, project=project, release='TEST', interval=.1) as logger:
                self.assertEqual(logger.environment()['SEL_EXECUTION_PROJECT'], project)
        self.assertEqual(len(list(self.root.glob('*.log'))), 5)


if __name__ == '__main__':
    unittest.main()
