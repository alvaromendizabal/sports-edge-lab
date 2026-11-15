"""Physically exercise the release recovery executable on stored ZIP archives."""
import hashlib
import io
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile

LIMIT = 512 << 20
CHUNK = bytes(range(256)) * 4096
PROGRAM = pathlib.Path(sys.argv[1]).resolve()
EXPECTED = "72d84f2a5c8579f402417c5f6bc9f6791719f72eade0c20b8db7a5f63923cf5f"
OUTPUT = pathlib.Path(sys.argv[2])


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def metadata(n, value):
    return json.dumps({"files": {"payload.bin": {"bytes": n, "sha256": value}}}, sort_keys=True).encode()


def overhead(n):
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_STORED) as archive:
        archive.writestr("payload.bin", b"")
        archive.writestr("RETURN_MANIFEST.json", metadata(n, "0" * 64))
    return len(output.getvalue())


def copy_chunk(stream, path, maximum):
    count = 0
    sha = hashlib.sha256()
    with path.open("xb") as output:
        while count < maximum:
            data = stream.read(min(len(CHUNK), maximum - count))
            if not data:
                break
            output.write(data)
            sha.update(data)
            count += len(data)
        output.flush()
        os.fsync(output.fileno())
    return {"filename": path.name, "bytes": count, "sha256": sha.hexdigest()}


def run_case(tmp, name, exact):
    root = tmp / name
    root.mkdir()
    source = root / "return.zip"
    n = exact - overhead(exact) if exact else (2 << 30) + 131072
    if exact and n + overhead(n) != exact:
        raise AssertionError("ZIP overhead does not match the proposed boundary")
    h = hashlib.sha256()
    start = time.monotonic()
    with zipfile.ZipFile(source, "w", compression=zipfile.ZIP_STORED, allowZip64=True) as archive:
        member = zipfile.ZipInfo("payload.bin")
        member.file_size = n
        with archive.open(member, "w", force_zip64=n >= 2**31-1) as payload:
            remaining = n
            while remaining:
                block = CHUNK[:min(remaining, len(CHUNK))]
                payload.write(block)
                h.update(block)
                remaining -= len(block)
        archive.writestr("RETURN_MANIFEST.json", metadata(n, h.hexdigest()))
    with source.open("rb") as physical:
        os.fsync(physical.fileno())
    source_size = source.stat().st_size
    disk_bytes = source.stat().st_blocks * 512
    if (exact and source_size != exact) or (not exact and source_size <= 2 << 30):
        raise AssertionError("Physical ZIP size mismatch")
    if disk_bytes < source_size:
        raise AssertionError("The test needs a physically allocated, non-sparse archive")
    logical_sha = digest(source)
    parts = []
    if source_size <= LIMIT:
        parts = [{"filename": source.name, "bytes": source_size, "sha256": logical_sha}]
    else:
        with source.open("rb") as stream:
            while stream.tell() < source_size:
                path = root / f"return.zip.part{len(parts)+1:04d}"
                parts.append(copy_chunk(stream, path, LIMIT))
        if sum(p["bytes"] for p in parts) != source_size or max(p["bytes"] for p in parts) > LIMIT:
            raise AssertionError("Invalid transfer sizes")
        source.unlink()
    doc = {"parts": parts, "logical_zip": {"filename": source.name, "sha256": logical_sha, "bytes": source_size}}
    manifest = root / "parts.json"
    manifest.write_text(json.dumps(doc, sort_keys=True), encoding="utf-8")
    cmd = [sys.executable, "-I", "-u", str(PROGRAM), "--assemble-return", str(manifest),
           "--expected-manifest-sha256", digest(manifest), "--assemble-to", str(source)]
    rejection = {}
    if len(parts) > 1:
        final = root / parts[-1]["filename"]
        moved = final.with_suffix(".saved")
        final.rename(moved)
        missing = subprocess.run(cmd, capture_output=True, text=True)
        rejection["missing"] = missing.returncode != 0 and not source.exists()
        moved.rename(final)
        with final.open("r+b") as stream:
            original = stream.read(1)
            stream.seek(0)
            stream.write(bytes([original[0] ^ 255]))
        corrupt = subprocess.run(cmd, capture_output=True, text=True)
        rejection["corrupt"] = corrupt.returncode != 0 and not source.exists()
        with final.open("r+b") as stream:
            stream.write(original)
        if not all(rejection.values()):
            raise AssertionError("A corrupt or incomplete set passed")
    receipt = json.loads(subprocess.run(cmd, check=True, capture_output=True, text=True).stdout)
    if (receipt["status"] != "ASSEMBLED_READBACK_OK" or receipt["sha256"] != logical_sha
            or receipt["parts"] != len(parts) or receipt["payloads"] != 1):
        raise AssertionError("Exact CLI failed to attest the expected archive")
    if digest(source) != logical_sha:
        raise AssertionError("Independent restored logical digest mismatch")
    with zipfile.ZipFile(source) as archive, archive.open("payload.bin") as payload:
        if hashlib.file_digest(payload, "sha256").digest() != h.digest():
            raise AssertionError("Independent physical member readback mismatch")
    report = {"case": name, "archive_bytes": source_size, "physical_allocated_bytes": disk_bytes,
              "payload_bytes": n, "payload_sha256": h.hexdigest(), "logical_sha256": logical_sha,
              "pieces": parts, "verified_payloads": receipt["payloads"],
              "missing_and_corrupt_rejected": rejection, "seconds": round(time.monotonic()-start, 3)}
    print(json.dumps(report), flush=True)
    shutil.rmtree(root)
    return report


if digest(PROGRAM) != EXPECTED:
    raise SystemExit("Incorrect executable SHA256")
with tempfile.TemporaryDirectory(prefix="n121-transport-") as name:
    tmp = pathlib.Path(name)
    free = shutil.disk_usage(tmp).free
    if free < 5 << 30:
        raise SystemExit(f"Need 5 GiB scratch to write full fixtures; measured {free}")
    cases = [run_case(tmp, name, count) for name, count in
             [("below", LIMIT-1), ("equal", LIMIT), ("above", LIMIT+1), ("multi", None)]]
receipt = {"status": "PASS", "python": sys.version, "runner_sha256": EXPECTED,
           "initial_free_bytes": free, "environment": "GitHub-hosted Linux CI, controlled physical fixture",
           "source": "The fixture frames a stored ZIP; the hash-pinned N121 executable independently verifies/reassembles it.",
           "cases": cases}
OUTPUT.write_text(json.dumps(receipt, sort_keys=True, indent=2) + "\n")
print("All physical N121 assembly/readback and failure checks passed.", flush=True)
