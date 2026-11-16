"""Store identical public status bytes once, retaining every snapshot and pin."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import tempfile

from examples.ncaa_review.public_status_transport import canonical, immutable_write, pinned, population_pins, unpack

SCHEMA = "sel.ncaa.public_shared_status_objects.v1"
SNAPSHOTS = ("population", "population_r17")


def build(docs: Path, *, reconstruct: bool = True):
    docs = Path(docs)
    target = docs / "status_objects"
    if target.is_symlink():
        raise ValueError("PUBLIC_SHARED_STATUS_SYMLINK_REJECTED")
    objects, snapshots = {}, {}
    logical_bytes = logical_parts = logical_rows = 0
    for name in SNAPSHOTS:
        root = docs / name
        if reconstruct:
            unpack(root)
        raw, population, pins = population_pins(root / "population_public.json")
        snapshots[name] = {"population_hash": population["population_hash"], "partitions": len(pins), "status_cells": sum(p["rows"] for p in pins.values())}
        for filename, pin in sorted(pins.items()):
            sha = pin["sha256"]
            if not isinstance(sha, str) or not re.fullmatch(r"[0-9a-f]{64}", sha):
                raise ValueError("PUBLIC_SHARED_STATUS_HASH_INVALID")
            source = root / "status" / filename
            if source.is_symlink():
                raise ValueError("PUBLIC_SHARED_STATUS_SYMLINK_REJECTED")
            body = source.read_bytes()
            pinned(body, pin)
            path = f"status_objects/{sha}.jsonl.gz"
            immutable_write(docs / path, body)
            record = objects.setdefault(sha, {"path": path, "sha256": sha, "bytes": len(body), "references": []})
            if record["bytes"] != len(body):
                raise ValueError("PUBLIC_SHARED_STATUS_IDENTITY_CONFLICT")
            record["references"].append({"snapshot": name, "filename": filename})
            logical_bytes += len(body)
            logical_parts += 1
            logical_rows += pin["rows"]
    physical_bytes = sum(o["bytes"] for o in objects.values())
    receipt = {"schema": SCHEMA, "complete": True, "snapshots": snapshots, "logical_partition_references": logical_parts, "logical_status_cells_across_snapshots": logical_rows, "physical_objects": len(objects), "physical_bytes": physical_bytes, "duplicated_bytes_avoided": logical_bytes - physical_bytes, "original_compressed_bytes_unchanged": True, "instructions": "For each snapshot partition, fetch status_objects/<partition.sha256>.jsonl.gz. Verify compressed bytes/size and logical hash/rows against that snapshot's unchanged population and status manifests. The references below preserve every original filename; no partition or metric was omitted.", "objects": [objects[k] for k in sorted(objects)]}
    destination = docs / "status_objects_manifest.json"
    if destination.is_symlink():
        raise ValueError("PUBLIC_SHARED_STATUS_SYMLINK_REJECTED")
    fd, temporary = tempfile.mkstemp(prefix=".shared-status-", dir=docs)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(canonical(receipt))
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, destination)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return receipt


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--docs-directory", type=Path, default=Path(__file__).resolve().parents[2] / "docs/ncaa")
    parser.add_argument("--already-reconstructed", action="store_true", help="Reuse physically present pinned snapshot parts; all object hashes are still verified.")
    args = parser.parse_args()
    result = build(args.docs_directory, reconstruct=not args.already_reconstructed)
    print(json.dumps({k: v for k, v in result.items() if k != "objects"}))
