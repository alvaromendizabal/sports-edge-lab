"""Preserve public gzip assets in bounded Git source packs and reconstruct exact bytes.

Only public status assets are accepted. Source packs are JSON/base64 containers,
not gzip files. The deployed files are the unchanged original gzip payloads.
No fitting, provider acquisition, cloud access or private ledger handling occurs.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile

SCHEMA = "sel.ncaa.public_status_source_transport.v1"
PACK_BYTES = 2 << 20
ROOT = Path(__file__).resolve().parents[2]
DEFAULT_POP = ROOT / "docs" / "ncaa" / "population"


def digest(body):
    return hashlib.sha256(body).hexdigest()


def canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode()


def safe_name(name):
    if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z0-9_-]+\.jsonl\.gz", name):
        raise ValueError("PUBLIC_STATUS_FILENAME_INVALID")
    return name


def pinned(body, pin):
    if len(body) != pin["bytes"] or digest(body) != pin["sha256"]:
        raise ValueError("PUBLIC_STATUS_BYTES_OR_HASH_MISMATCH")


def immutable_write(path, body):
    if path.is_symlink():
        raise ValueError("PUBLIC_STATUS_SYMLINK_REJECTED")
    if path.exists():
        if path.read_bytes() != body:
            raise ValueError("EXISTING_PUBLIC_ASSET_CONFLICT")
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".status-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(body)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return True


def population_pins(population_path):
    raw = population_path.read_bytes()
    value = json.loads(raw)
    if value.get("schema") != "sel.ncaa.b088.population_public.v1":
        raise ValueError("PUBLIC_POPULATION_SCHEMA_INVALID")
    parts = value["status_partition_manifest"]
    pins = {safe_name(p["filename"]): p for p in parts}
    if len(pins) != len(parts) or not pins:
        raise ValueError("PUBLIC_STATUS_PARTITION_SET_INVALID")
    for pin in pins.values():
        if pin["population_hash"] != value["population_hash"] or pin["codec"] != "jsonl_gzip" or pin["scope"] != "EXPLICIT_CELLS_NO_SPARSE_DEFAULTS" or pin["physical_readback_verified"] is not True:
            raise ValueError("PUBLIC_STATUS_PARTITION_CONTRACT_INVALID")
    return raw, value, pins


def pack(population_path, original_parts, source_directory, *, max_pack_bytes=PACK_BYTES):
    """Package exact already-public compressed bytes; no scientific transformation."""
    raw, population, pins = population_pins(Path(population_path))
    source_directory = Path(source_directory)
    if source_directory.is_symlink():
        raise ValueError("PUBLIC_SOURCE_DESTINATION_SYMLINK_REJECTED")
    if source_directory.exists() and any(source_directory.iterdir()):
        raise ValueError("SOURCE_PACK_DESTINATION_MUST_BE_EMPTY")
    source_directory.mkdir(parents=True, exist_ok=True)
    descriptors, pending, estimated = [], [], 256

    def flush():
        nonlocal pending, estimated
        if not pending:
            return
        body = canonical({"schema": SCHEMA + ".pack", "population_hash": population["population_hash"], "encoding": "base64_of_unchanged_gzip_bytes", "entries": pending})
        if len(body) > max_pack_bytes:
            raise ValueError("PUBLIC_SOURCE_PACK_EXCEEDS_DECLARED_BOUND")
        filename = f"pack_{len(descriptors):05d}.json"
        immutable_write(source_directory / filename, body)
        descriptors.append({"filename": filename, "bytes": len(body), "sha256": digest(body), "payload_count": len(pending), "payload_compressed_bytes": sum(e["bytes"] for e in pending)})
        pending, estimated = [], 256

    for filename, pin in sorted(pins.items()):
        path = Path(original_parts) / filename
        if not path.is_file() or path.is_symlink():
            raise ValueError("PUBLIC_STATUS_SOURCE_FILE_MISSING_OR_UNSAFE")
        body = path.read_bytes()
        pinned(body, pin)
        entry = {"filename": filename, "bytes": len(body), "sha256": pin["sha256"], "base64": base64.b64encode(body).decode("ascii")}
        size = len(canonical(entry)) + 1
        if pending and estimated + size > max_pack_bytes:
            flush()
        if estimated + size > max_pack_bytes:
            raise ValueError("SINGLE_PUBLIC_STATUS_ASSET_EXCEEDS_SOURCE_PACK_BOUND")
        pending.append(entry)
        estimated += size
    flush()
    manifest = {"schema": SCHEMA, "population_hash": population["population_hash"], "population_public_bytes": len(raw), "population_public_sha256": digest(raw), "source_encoding": "JSON_PACKS_OF_BASE64_ENCODED_UNCHANGED_GZIP_PAYLOADS", "deployed_encoding": "ORIGINAL_JSONL_GZIP", "private_tables_included": False, "complete": True, "max_source_pack_bytes": max_pack_bytes, "payload_count": len(pins), "payload_compressed_bytes": sum(p["bytes"] for p in pins.values()), "public_status_rows": population["status_ledger_rows"], "packs": descriptors}
    immutable_write(source_directory / "manifest.json", canonical(manifest))
    return manifest


def unpack(population_directory=DEFAULT_POP):
    """Verify complete source identity and reconstruct the deployable public assets."""
    population_directory = Path(population_directory)
    raw, population, expected = population_pins(population_directory / "population_public.json")
    source = population_directory / "source_packs"
    if source.is_symlink():
        raise ValueError("PUBLIC_SOURCE_DIRECTORY_SYMLINK_REJECTED")
    manifest = json.loads((source / "manifest.json").read_bytes())
    if manifest.get("schema") != SCHEMA or manifest.get("complete") is not True or manifest.get("private_tables_included") is not False or manifest.get("population_hash") != population["population_hash"] or manifest.get("population_public_bytes") != len(raw) or manifest.get("population_public_sha256") != digest(raw) or manifest.get("payload_count") != len(expected) or manifest.get("public_status_rows") != population["status_ledger_rows"]:
        raise ValueError("PUBLIC_SOURCE_MANIFEST_IDENTITY_MISMATCH")
    output = population_directory / "status"
    if output.is_symlink():
        raise ValueError("PUBLIC_STATUS_OUTPUT_SYMLINK_REJECTED")
    output.mkdir(parents=True, exist_ok=True)
    extra = {p.name for p in output.glob("*.jsonl.gz")} - set(expected)
    if extra:
        raise ValueError("UNDECLARED_PUBLIC_STATUS_FILES_PRESENT")
    seen, names, created, reused, total_bytes = set(), set(), 0, 0, 0
    for descriptor in manifest["packs"]:
        name = descriptor["filename"]
        if not re.fullmatch(r"pack_[0-9]{5}\.json", name) or name in names:
            raise ValueError("PUBLIC_SOURCE_PACK_NAME_INVALID")
        names.add(name)
        path = source / name
        if path.is_symlink() or not path.is_file():
            raise ValueError("PUBLIC_SOURCE_PACK_MISSING_OR_UNSAFE")
        body = path.read_bytes()
        pinned(body, descriptor)
        if len(body) > manifest["max_source_pack_bytes"]:
            raise ValueError("PUBLIC_SOURCE_PACK_BOUND_EXCEEDED")
        payload = json.loads(body)
        if set(payload) != {"schema", "population_hash", "encoding", "entries"} or payload["schema"] != SCHEMA + ".pack" or payload["population_hash"] != population["population_hash"] or payload["encoding"] != "base64_of_unchanged_gzip_bytes" or len(payload["entries"]) != descriptor["payload_count"]:
            raise ValueError("PUBLIC_SOURCE_PACK_CONTRACT_INVALID")
        part_bytes = 0
        for entry in payload["entries"]:
            if set(entry) != {"filename", "bytes", "sha256", "base64"}:
                raise ValueError("PUBLIC_SOURCE_ENTRY_CONTRACT_INVALID")
            filename = safe_name(entry["filename"])
            if filename not in expected or filename in seen:
                raise ValueError("PUBLIC_SOURCE_PAYLOAD_SET_INVALID")
            pin = expected[filename]
            if entry["bytes"] != pin["bytes"] or entry["sha256"] != pin["sha256"]:
                raise ValueError("PUBLIC_SOURCE_PAYLOAD_PIN_MISMATCH")
            decoded = base64.b64decode(entry["base64"], validate=True)
            pinned(decoded, pin)
            fresh = immutable_write(output / filename, decoded)
            created += int(fresh)
            reused += int(not fresh)
            seen.add(filename)
            part_bytes += len(decoded)
        if part_bytes != descriptor["payload_compressed_bytes"]:
            raise ValueError("PUBLIC_SOURCE_PACK_BYTE_TOTAL_MISMATCH")
        total_bytes += part_bytes
    if seen != set(expected) or total_bytes != manifest["payload_compressed_bytes"]:
        raise ValueError("PUBLIC_SOURCE_REASSEMBLY_INCOMPLETE")
    return {"status": "VERIFIED_PUBLIC_STATUS_REASSEMBLY", "payload_count": len(seen), "created": created, "reused_identical": reused, "compressed_bytes": total_bytes, "public_status_rows": manifest["public_status_rows"], "population_public_sha256": digest(raw), "private_tables_included": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    create = commands.add_parser("pack")
    create.add_argument("--population", type=Path, required=True)
    create.add_argument("--parts-dir", type=Path, required=True)
    create.add_argument("--output", type=Path, required=True)
    restore = commands.add_parser("unpack")
    restore.add_argument("--population-directory", type=Path, default=DEFAULT_POP)
    args = parser.parse_args()
    result = pack(args.population, args.parts_dir, args.output) if args.command == "pack" else unpack(args.population_directory)
    print(json.dumps(result if args.command == "unpack" else {k: v for k, v in result.items() if k != "packs"}, sort_keys=True))


if __name__ == "__main__":
    main()
