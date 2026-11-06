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
    expected_intent = _canonical({"stage": stage, "status": "INTENT"})
    if result.exists() or prepared.exists() or commit.exists():
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
            if commit.read_bytes() != _receipt(stage, "COMPLETE", raw):
                raise ValueError("committed result changed")
            return {"result": json.loads(raw), "action_reused": True, "new_gets": 0}
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
    _create(commit, _receipt(stage, "COMPLETE", raw))
    return {"result": json.loads(raw), "action_reused": reused, "new_gets": 1}
