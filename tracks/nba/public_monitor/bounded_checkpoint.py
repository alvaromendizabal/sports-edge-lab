"""Bounded, credential-free checkpoint example with invented JSON records.

This is a generic storage contract, not a private model or runtime codec.
The caller supplies an immutable returned output. Publication never calls the
original action. Every object is create-only and independently read in full.
"""
from __future__ import annotations

import hashlib
import json
import re


def _json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def _hash(raw):
    return hashlib.sha256(raw).hexdigest()


def _load(raw):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate JSON key")
            result[key] = value
        return result
    return json.loads(raw, object_pairs_hook=unique)


def _pin(raw, records):
    return {"sha256": _hash(raw), "bytes": len(raw), "records": records}


def _positive_integer(value):
    return type(value) is int and value > 0


def _publish(remote, raw):
    key = _hash(raw)
    remote.put_create_only(key, raw)
    if remote.get_full(key) != raw:
        raise ValueError("independent full readback mismatch")
    return key


def publish_records(records, remote, *, max_shard_bytes=65536,
                    max_manifest_bytes=65536, max_shards=256):
    """Publish a bounded sequence of JSON-object rows, then its manifest.

    An oversized single record is refused rather than split ambiguously.
    Equal shard bodies may share one content key while retaining distinct
    sequence positions. A retry may republish the same immutable returned
    output; this function cannot replay its producer or award computation credit.
    """
    if not all(_positive_integer(x) for x in
               (max_shard_bytes, max_manifest_bytes, max_shards)):
        raise ValueError("invalid resource bound")
    shards, pending = [], bytearray()
    count = total_rows = total_bytes = 0
    aggregate = hashlib.sha256()

    def flush():
        nonlocal pending, count
        if not pending:
            return
        if len(shards) >= max_shards:
            raise ValueError("shard count bound")
        raw = bytes(pending)
        _publish(remote, raw)
        shards.append({"ordinal": len(shards), **_pin(raw, count)})
        pending, count = bytearray(), 0

    for row in records:
        if not isinstance(row, dict):
            raise ValueError("record must be an object")
        raw = _json(row) + b"\n"
        if len(raw) > max_shard_bytes:
            raise ValueError("single record exceeds bound")
        if pending and len(pending) + len(raw) > max_shard_bytes:
            flush()
        pending.extend(raw)
        count += 1
        total_rows += 1
        total_bytes += len(raw)
        aggregate.update(raw)
    flush()
    manifest = {"schema": "invented.bounded-records.v1", "shards": shards,
                "records": total_rows, "bytes": total_bytes,
                "payload_sha256": aggregate.hexdigest()}
    raw = _json(manifest)
    if len(raw) > max_manifest_bytes:
        raise ValueError("manifest byte bound")
    return {"sha256": _publish(remote, raw), "bytes": len(raw),
            "new_computation_credit": 0, "producer_invoked": False}


def restore_records(reference, remote, *, max_shard_bytes=65536,
                    max_manifest_bytes=65536, max_shards=256,
                    max_total_bytes=16777216):
    """Validate the complete sequence before returning any reconstructed row.

    This deliberately bounded teaching example materializes at most the
    declared total limit. A production consumer needs a verified spool or an
    equivalent transaction boundary before exposing streamed partial output.
    """
    if not all(_positive_integer(x) for x in
               (max_shard_bytes, max_manifest_bytes, max_shards, max_total_bytes)):
        raise ValueError("invalid resource bound")
    if (not isinstance(reference, dict)
            or not re.fullmatch(r"[0-9a-f]{64}", str(reference.get("sha256", "")))
            or not _positive_integer(reference.get("bytes"))
            or reference["bytes"] > max_manifest_bytes):
        raise ValueError("invalid manifest reference")
    raw = remote.get_full(reference["sha256"])
    if len(raw) != reference["bytes"] or _hash(raw) != reference["sha256"]:
        raise ValueError("manifest pin mismatch")
    manifest = _load(raw)
    if (not isinstance(manifest, dict)
            or set(manifest) != {"schema", "shards", "records", "bytes", "payload_sha256"}
            or manifest["schema"] != "invented.bounded-records.v1"
            or type(manifest["records"]) is not int or manifest["records"] < 0
            or type(manifest["bytes"]) is not int
            or not 0 <= manifest["bytes"] <= max_total_bytes
            or not re.fullmatch(r"[0-9a-f]{64}", str(manifest["payload_sha256"]))
            or not isinstance(manifest["shards"], list)
            or len(manifest["shards"]) > max_shards):
        raise ValueError("manifest schema or capacity mismatch")
    output, total_bytes = [], 0
    aggregate = hashlib.sha256()
    for ordinal, shard in enumerate(manifest["shards"]):
        if (not isinstance(shard, dict)
                or set(shard) != {"ordinal", "sha256", "bytes", "records"}
                or type(shard["ordinal"]) is not int or shard["ordinal"] != ordinal
                or not _positive_integer(shard["bytes"])
                or shard["bytes"] > max_shard_bytes
                or not _positive_integer(shard["records"])
                or not re.fullmatch(r"[0-9a-f]{64}", str(shard["sha256"]))):
            raise ValueError("shard schema, order or capacity mismatch")
        total_bytes += shard["bytes"]
        if total_bytes > manifest["bytes"] or total_bytes > max_total_bytes:
            raise ValueError("aggregate byte bound")
        body = remote.get_full(shard["sha256"])
        if len(body) != shard["bytes"] or _hash(body) != shard["sha256"]:
            raise ValueError("shard pin mismatch")
        if not body.endswith(b"\n"):
            raise ValueError("record boundary mismatch")
        rows = [_load(line) for line in body.splitlines()]
        if (len(rows) != shard["records"]
                or not all(isinstance(row, dict) for row in rows)
                or b"".join(_json(row) + b"\n" for row in rows) != body):
            raise ValueError("record closure mismatch")
        aggregate.update(body)
        output.extend(rows)
    if (len(output) != manifest["records"] or total_bytes != manifest["bytes"]
            or aggregate.hexdigest() != manifest["payload_sha256"]):
        raise ValueError("complete sequence mismatch")
    return output
