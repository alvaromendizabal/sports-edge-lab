"""Portable, owner-independent recovery contracts and a no-signal snapshot.

The policy function does not identify processes or authorize an operating-system
action. Its input must come from independently verified runtime evidence. The
checkpoint function only works when every writer honors the same existing
flock file; callers must never replace or delete that file to obtain a lock.
"""
from __future__ import annotations

import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3


def pretraining_recovery_denial(evidence):
    """Return a refusal reason, or None for a complete policy evidence record.

    These conditions must be checked again after checkpointing and immediately
    before a separately implemented destructive action. This example itself
    neither discovers nor signals any process.
    """
    selected = evidence.get('explicit_selected_run_id')
    if not selected or selected != evidence.get('observed_run_id'):
        return 'An explicit, exact run selection is required'
    for key in ('same_user_verified', 'source_bytes_verified', 'pid_start_verified',
                'unique_lock_holder_verified', 'all_threads_stopped'):
        if evidence.get(key) is not True:
            return 'Missing verified condition: ' + key
    event = evidence.get('last_event')
    if not isinstance(event, dict) or event.get('stage') != 'source_inventory' or event.get('status') != 'STARTED':
        return 'The run is outside the permitted source-inventory phase'
    for key in ('optimizer_markers', 'completed_fit_markers'):
        if type(evidence.get(key)) is not int or evidence[key] != 0:
            return 'Scientific work is present or unproven: ' + key
    return None


def _pin(path):
    checksum = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            checksum.update(block)
    return {'bytes': Path(path).stat().st_size, 'sha256': checksum.hexdigest()}


def _fsync_directory(path):
    descriptor = os.open(path, os.O_RDONLY | getattr(os, 'O_DIRECTORY', 0))
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def checkpoint_inactive_delete_catalog(database, writer_lock, destination):
    """Copy an inactive DELETE-journal SQLite database without mutating it.

    Acquires the existing real writer flock with LOCK_NB, preserves a possible
    hot journal beside the original DB copy, and opens only a second copy for
    SQLite rollback recovery. A nonempty/previous destination is never reused.
    The final receipt is the completion marker; partial output is not a usable
    checkpoint. No process signals are sent and no lock files are removed.
    """
    database, writer_lock, destination = map(Path, (database, writer_lock, destination))
    if database.is_symlink() or writer_lock.is_symlink():
        raise ValueError('Database and existing writer lock must be ordinary files')
    descriptor = os.open(writer_lock, os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0))
    with os.fdopen(descriptor, 'rb') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        locked = os.fstat(lock.fileno())
        current = writer_lock.stat()
        if (locked.st_dev, locked.st_ino) != (current.st_dev, current.st_ino):
            raise ValueError('Writer lock inode changed')
        if any(Path(str(database) + suffix).exists() for suffix in ('-wal', '-shm')):
            raise ValueError('This example supports only DELETE-journal catalogs')
        destination.mkdir(parents=True, exist_ok=False)
        original_dir, recovered_dir = destination / 'original', destination / 'recovered'
        original_dir.mkdir(); recovered_dir.mkdir()
        originals = [database]
        journal = Path(str(database) + '-journal')
        if journal.exists():
            originals.append(journal)
        pins = {}
        for original in originals:
            if original.is_symlink():
                raise ValueError('Journal must be an ordinary file')
            expected = _pin(original)
            for directory in (original_dir, recovered_dir):
                target = directory / original.name
                shutil.copyfile(original, target)
                if _pin(target) != expected or _pin(original) != expected:
                    raise ValueError('Checkpoint source changed or copying failed')
                with target.open('rb') as stream:
                    os.fsync(stream.fileno())
            pins[original.name] = expected
        recovered = recovered_dir / database.name
        connection = sqlite3.connect(recovered)
        try:
            if connection.execute('PRAGMA journal_mode').fetchone()[0] != 'delete':
                raise ValueError('Unexpected journal mode')
            if connection.execute('PRAGMA quick_check').fetchall() != [('ok',)]:
                raise ValueError('Recovered copy failed SQLite quick_check')
        finally:
            connection.close()
        with recovered.open('rb') as stream:
            os.fsync(stream.fileno())
        receipt = {'schema': 'portable.pretraining-checkpoint.v1',
            'writer_lock_acquired_normally': True, 'signals_sent': 0,
            'original_files': pins, 'recovered_database': _pin(recovered),
            'sqlite_integrity': 'ok', 'source_catalog_complete': False,
            'absence_proof': 'UNKNOWN_REQUIRES_FRESH_RECONCILIATION'}
        temporary = destination / 'checkpoint.json.partial'
        with temporary.open('x') as stream:
            json.dump(receipt, stream, sort_keys=True, indent=2)
            stream.write('\n'); stream.flush(); os.fsync(stream.fileno())
        os.replace(temporary, destination / 'checkpoint.json')
        for directory in (original_dir, recovered_dir, destination, destination.parent):
            _fsync_directory(directory)
        return receipt
