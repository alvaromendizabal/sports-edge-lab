"""Credential-free commit-boundary example using invented JSON results.

An action return is not a committed checkpoint. The retained intent stops an
ambiguous action from being replayed. A saved result can be published again
without calling the action only when its durable prepared record matches. The
remote interface must implement create-only put and independent full get; this
example supplies no network implementation.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import re
import uuid


class UncertainAction(RuntimeError):
    """An intent exists but no durable result establishes action completion."""


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def _digest(raw):
    return hashlib.sha256(raw).hexdigest()


def _receipt(stage, status, raw):
    return _canonical({"stage": stage, "status": status,
                       "result_sha256": _digest(raw), "bytes": len(raw)})


def _create(path, raw):
    try:
        with path.open("xb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
    except FileExistsError:
        if path.read_bytes() != raw:
            raise ValueError("immutable record conflict")
    fd = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _acknowledge(root, stage, committed):
    """Publish a derived marker only from the exact validated commit bytes.

    The immutable commit is the authority. A missing or older JSON marker is
    recoverable without an action or a remote request; corrupt marker bytes
    fail closed. Previous markers remain in an immutable local history.
    """
    marker = root / (stage + ".marker.json")
    def sync_and_read():
        fd = os.open(root, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
        if marker.read_bytes() != committed:
            raise ValueError("marker independent readback mismatch")
    if marker.is_symlink():
        raise ValueError("marker must not be a symbolic link")
    previous = marker.read_bytes() if marker.exists() else None
    if previous is not None:
        if not isinstance(json.loads(previous), dict):
            raise ValueError("marker must be a JSON object")
        if previous == committed:
            sync_and_read()
            return False
        history = root / "marker_history"
        history.mkdir(exist_ok=True)
        _create(history / (stage + "-" + _digest(previous) + ".json"), previous)
    temporary = marker.with_name(marker.name + ".pending-" + uuid.uuid4().hex)
    try:
        with temporary.open("xb") as stream:
            stream.write(committed)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, marker)
        sync_and_read()
    finally:
        temporary.unlink(missing_ok=True)
    return True


def run_stage(directory, stage, action, remote):
    """Commit one JSON-only invented result; never infer success from intent.

    ``directory`` is a caller-owned durable directory. The example assumes one
    admitted writer; production systems also need process locks, authorization,
    bounded storage, source/attempt identity and an authenticated recovery graph.
    """
    if not re.fullmatch(r"[a-z0-9_]{1,48}", stage):
        raise ValueError("unsafe stage name")
    root = Path(directory)
    root.mkdir(parents=True, exist_ok=True)
    intent = root / (stage + ".intent.json")
    result = root / (stage + ".result.json")
    prepared = root / (stage + ".prepared.json")
    commit = root / (stage + ".commit.json")
    marker = root / (stage + ".marker.json")
    if marker.is_symlink():
        raise ValueError("marker must not be a symbolic link")
    expected_intent = _canonical({"stage": stage, "status": "INTENT"})
    if result.exists() or prepared.exists() or commit.exists() or marker.exists():
        if not intent.exists():
            raise ValueError("saved state without intent")
        if intent.read_bytes() != expected_intent:
            raise ValueError("intent changed")
        if not result.is_file() or not prepared.is_file():
            raise UncertainAction("saved result or prepared pin missing; automatic replay refused")
        raw = result.read_bytes()
        if prepared.read_bytes() != _receipt(stage, "PREPARED", raw):
            raise ValueError("prepared result changed")
        json.loads(raw)
        if commit.exists():
            committed = commit.read_bytes()
            if committed != _receipt(stage, "COMPLETE", raw):
                raise ValueError("committed result changed")
            repaired = _acknowledge(root, stage, committed)
            return {"result": json.loads(raw), "action_reused": True, "new_gets": 0,
                    "marker_reconciled": repaired, "marker_acknowledged": True}
        reused = True
    else:
        if intent.exists():
            if intent.read_bytes() != expected_intent:
                raise ValueError("intent changed")
            raise UncertainAction("action may have run; automatic replay refused")
        _create(intent, expected_intent)
        raw = _canonical(action())
        _create(result, raw)
        _create(prepared, _receipt(stage, "PREPARED", raw))
        reused = False
    key = _digest(raw)
    remote.put_create_only(key, raw)
    readback = remote.get_full(key)
    if readback != raw:
        raise ValueError("independent full readback mismatch")
    committed = _receipt(stage, "COMPLETE", raw)
    _create(commit, committed)
    _acknowledge(root, stage, committed)
    return {"result": json.loads(raw), "action_reused": reused, "new_gets": 1,
            "marker_reconciled": False, "marker_acknowledged": True}

