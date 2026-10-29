"""Invented local fixtures only; no credentials, owner paths, or provider calls."""
import copy
import json
import os
from pathlib import Path
import select
import sqlite3
import subprocess
import sys
import tempfile
import unittest

from examples.fbs_contracts.pretraining_checkpoint import checkpoint_inactive_delete_catalog, pretraining_recovery_denial


CHILD = r'''
import fcntl,os,sqlite3,sys
from pathlib import Path
root=Path(sys.argv[1]); lock=(root/'writer.lock').open('a+')
fcntl.flock(lock,fcntl.LOCK_EX)
conn=sqlite3.connect(root/'catalog.sqlite')
conn.execute('PRAGMA journal_mode=DELETE');conn.execute('PRAGMA cache_size=1')
conn.execute('CREATE TABLE objects (name TEXT, value TEXT)')
conn.execute("INSERT INTO objects VALUES ('committed','fixture')");conn.commit()
conn.execute('BEGIN IMMEDIATE')
conn.executemany('INSERT INTO objects VALUES (?,?)',[('uncommitted-'+str(i),'x'*200) for i in range(1000)])
print('READY',flush=True)
command=sys.stdin.readline().strip()
if command=='crash':os._exit(0)
conn.rollback();conn.close()
'''


class PolicyTests(unittest.TestCase):
    def setUp(self):
        self.evidence = {'explicit_selected_run_id': 'example-run', 'observed_run_id': 'example-run',
            'same_user_verified': True, 'source_bytes_verified': True, 'pid_start_verified': True,
            'unique_lock_holder_verified': True, 'all_threads_stopped': True,
            'last_event': {'stage': 'source_inventory', 'status': 'STARTED'},
            'optimizer_markers': 0, 'completed_fit_markers': 0}

    def test_complete_pretraining_evidence_passes_policy_only(self):
        self.assertIsNone(pretraining_recovery_denial(self.evidence))
        with_timestamp = {**self.evidence, 'last_event': {**self.evidence['last_event'], 'at': 'example-time'}}
        self.assertIsNone(pretraining_recovery_denial(with_timestamp))

    def test_every_missing_condition_refuses(self):
        for key in self.evidence:
            with self.subTest(key=key):
                evidence = copy.deepcopy(self.evidence); del evidence[key]
                self.assertIsNotNone(pretraining_recovery_denial(evidence))

    def test_phase_or_work_advance_invalidates_prior_eligibility(self):
        for change in ({'optimizer_markers': 1}, {'completed_fit_markers': 1},
                       {'all_threads_stopped': False},
                       {'last_event': {'stage': 'science', 'status': 'STARTED'}}):
            with self.subTest(change=change):
                self.assertIsNotNone(pretraining_recovery_denial({**self.evidence, **change}))


class CheckpointTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='portable_checkpoint_')
        self.root = Path(self.temporary.name)
        self.child = subprocess.Popen([sys.executable, '-c', CHILD, str(self.root)],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        readable, _, _ = select.select([self.child.stdout], [], [], 10)
        self.assertTrue(readable, 'Invented child fixture failed to start')
        self.assertEqual(self.child.stdout.readline().strip(), 'READY')

    def tearDown(self):
        self.child.communicate(input='release\n' if self.child.poll() is None else None, timeout=5)
        self.temporary.cleanup()

    def checkpoint(self):
        return checkpoint_inactive_delete_catalog(self.root / 'catalog.sqlite', self.root / 'writer.lock', self.root / 'checkpoint')

    def test_active_writer_lock_is_respected(self):
        original_inode = (self.root / 'writer.lock').stat().st_ino
        with self.assertRaises(BlockingIOError):
            self.checkpoint()
        self.assertIsNone(self.child.poll())
        self.assertEqual((self.root / 'writer.lock').stat().st_ino, original_inode)
        self.assertFalse((self.root / 'checkpoint').exists())

    def test_hot_journal_is_preserved_and_only_copy_is_recovered(self):
        self.child.communicate(input='crash\n', timeout=5)
        self.assertEqual(self.child.returncode, 0)
        original = self.root / 'catalog.sqlite'
        journal = self.root / 'catalog.sqlite-journal'
        before = {path.name: path.read_bytes() for path in (original, journal)}
        receipt = self.checkpoint()
        self.assertEqual(receipt['signals_sent'], 0)
        self.assertIn(journal.name, receipt['original_files'])
        for path in (original, journal):
            self.assertEqual(path.read_bytes(), before[path.name])
        connection = sqlite3.connect(self.root / 'checkpoint/recovered/catalog.sqlite')
        try:
            self.assertEqual(connection.execute('SELECT name FROM objects').fetchall(), [('committed',)])
            self.assertEqual(connection.execute('PRAGMA quick_check').fetchall(), [('ok',)])
        finally:
            connection.close()
        self.assertEqual(json.loads((self.root / 'checkpoint/checkpoint.json').read_text()), receipt)

    def test_graceful_writer_exit_produces_usable_checkpoint(self):
        self.child.communicate(input='release\n', timeout=5)
        self.assertEqual(self.checkpoint()['sqlite_integrity'], 'ok')


if __name__ == '__main__':
    unittest.main()
