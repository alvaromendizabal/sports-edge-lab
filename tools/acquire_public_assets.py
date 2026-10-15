#!/usr/bin/env python3
"""Download verified nflverse/nfldata sources into a private, resumable S3 data lake.

The source catalog pins GitHub release asset URLs, digest and expected byte size.
No historical betting quotes are fabricated; source observations must be audited
for event-time correctness before they enter a modeling feature warehouse.
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import csv
import datetime as dt
import hashlib
import io
import json
import os
from pathlib import Path
import random
import re
import sys
import threading
import time
import urllib.error
import urllib.request
import uuid
import zipfile

CATALOG_URL = "https://raw.githubusercontent.com/alvaromendizabal/nfl-edge-lab/main/catalog/public_asset_manifest_20261015.json"
VERSION = "nfl-edge-lab-public-v002-20261015"
LOCK = threading.Lock()


def log(event, **values):
    print(json.dumps({"utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                      "event": event, **values}, sort_keys=True, default=str), flush=True)


def seasons_parse(value):
    if re.fullmatch(r"\d{4}:\d{4}", value):
        start, end = map(int, value.split(":"))
        years = set(range(start, end + 1))
    else:
        years = {int(x) for x in value.split(",") if x.strip()}
    if not years or min(years) < 1999 or max(years) > 2026:
        raise ValueError("Allowed NFL seasons: 1999 through 2026")
    return years


def asset_years(filename):
    return {int(s) for s in re.findall(r"(?:19|20)\d{2}", filename)}


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(1024 * 1024)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def valid(path, item):
    if not path.is_file():
        return False
    if path.stat().st_size != int(item["bytes"]):
        return False
    expected = item.get("sha256")
    if expected and digest(path) != expected:
        return False
    if path.suffix == ".parquet":
        if path.stat().st_size < 8:
            return False
        with path.open("rb") as f:
            if f.read(4) != b"PAR1":
                return False
            f.seek(-4, 2)
            if f.read(4) != b"PAR1":
                return False
    return True


def request(url, *, timeout=75):
    headers = {"User-Agent": "nfl-edge-lab/0.2 research-source-audit",
               "Accept": "application/octet-stream, application/json, */*"}
    return urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=timeout)


def load_catalog(spec):
    if spec.startswith(("https://", "http://")):
        with request(spec) as r:
            payload = r.read()
    else:
        payload = Path(spec).read_bytes()
    data = json.loads(payload)
    if data.get("schema_version") != "nfl-edge-lab-public-assets-v1":
        raise ValueError("Unknown source catalog schema")
    if not isinstance(data.get("assets"), list) or not data["assets"]:
        raise ValueError("Empty source catalog")
    seen = set()
    for a in data["assets"]:
        for field in ("source", "release_tag", "name", "url", "bytes"):
            if field not in a:
                raise ValueError("Missing required asset field: " + field)
        key = (a["source"], a["release_tag"], a["name"])
        if key in seen:
            raise ValueError("Duplicate asset key: " + str(key))
        seen.add(key)
        if not a["url"].startswith(("https://github.com/nflverse/",
                                    "https://raw.githubusercontent.com/nflverse/")):
            raise ValueError("Disallowed source host: " + a["url"])
    return data, hashlib.sha256(payload).hexdigest()


def path_for(root, a):
    parts = (a["source"], a["release_tag"], a["name"])
    if any("/" in p or "\\" in p or p in (".", "..") for p in parts):
        raise ValueError("Unsafe catalog path")
    return root.joinpath("raw", *parts)


def download_one(a, root, s3, bucket, deadline):
    target = path_for(root, a)
    target.parent.mkdir(parents=True, exist_ok=True)
    attempts = 0
    reused = valid(target, a)
    if not reused:
        part = target.with_name(target.name + ".part")
        for attempt in range(4):
            attempts = attempt + 1
            if time.monotonic() > deadline:
                return {"asset": a["name"], "tag": a["release_tag"],
                        "status": "deferred", "reason": "runtime_deadline"}
            try:
                # Partial files are only a transport cache; re-fetch if the
                # server ignores Range or gives an incompatible length.
                offset = part.stat().st_size if part.exists() else 0
                headers = {"User-Agent": "nfl-edge-lab/0.2", "Accept": "*/*"}
                if offset:
                    headers["Range"] = "bytes=%d-" % offset
                req = urllib.request.Request(a["url"], headers=headers)
                with urllib.request.urlopen(req, timeout=110) as response:
                    status = response.status
                    mode = "ab" if offset and status == 206 else "wb"
                    with part.open(mode) as fh:
                        while True:
                            block = response.read(1024 * 1024)
                            if not block:
                                break
                            fh.write(block)
                if not valid(part, a):
                    part.unlink(missing_ok=True)
                    raise ValueError("Size, SHA256, or Parquet integrity mismatch")
                os.replace(part, target)
                break
            except Exception as exc:
                if attempt == 3:
                    return {"asset": a["name"], "tag": a["release_tag"],
                            "status": "error", "reason": str(exc)[:220],
                            "attempts": attempts}
                time.sleep(min(3 * (attempt + 1), 12))
    if s3 and bucket:
        key = "/".join(["raw", a["source"], a["release_tag"], a["name"]])
        try:
            s3.upload_file(str(target), bucket, key, ExtraArgs={
                "Metadata": {"source-sha256": (a.get("sha256") or digest(target))[:64]}})
        except Exception as exc:
            return {"asset": a["name"], "tag": a["release_tag"],
                    "status": "error", "reason": "S3 upload: " + str(exc)[:200],
                    "attempts": attempts, "local_verified": True}
    return {"asset": a["name"], "tag": a["release_tag"],
            "status": "reused" if reused else "downloaded",
            "bytes": a["bytes"], "sha256": a.get("sha256") or digest(target),
            "attempts": attempts, "s3": bool(s3 and bucket)}


def write_return(home, manifest_hash, chosen, records, started, bucket, elapsed, error=None):
    home.mkdir(parents=True, exist_ok=True)
    run_id = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]
    final = home / ("nfl_edge_lab_v002_acquisition_return_" + run_id + ".zip")
    counts = {}
    for row in records:
        counts[row["status"]] = counts.get(row["status"], 0) + 1
    status = {"runner": VERSION, "run_id": run_id, "started_utc": started,
              "manifest_sha256": manifest_hash, "planned": len(chosen),
              "completed": len(records), "counts": counts, "elapsed_seconds": round(elapsed, 2),
              "bucket": bucket, "error": error, "all_ok": (
                  not error and len(chosen) == len(records) and
                  all(r["status"] in ("reused", "downloaded") for r in records))}
    with zipfile.ZipFile(final, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("summary.json", json.dumps(status, indent=2))
        z.writestr("receipts.jsonl", "".join(json.dumps(x, sort_keys=True)+"\n" for x in records))
        z.writestr("missing_or_failed.json", json.dumps(
            [x for x in records if x["status"] not in ("reused", "downloaded")], indent=2))
    log("RETURN_READY", path=str(final), **counts, all_ok=status["all_ok"])
    return final, status


def self_test():
    assert seasons_parse("1999:2001") == {1999, 2000, 2001}
    assert asset_years("stats_player_week_2025.parquet") == {2025}
    assert asset_years("games.parquet") == set()
    assert digest(Path(__file__)).isalnum()
    assert "raw/nflverse/pbp/hello.parquet" in str(
        path_for(Path("/tmp"), {"source":"nflverse","release_tag":"pbp","name":"hello.parquet"}))
    try:
        path_for(Path("/tmp"), {"source":"nflverse","release_tag":"pbp","name":"../bad"})
        raise AssertionError("Path guard failed")
    except ValueError:
        pass
    log("SELF_TEST_OK", tests=6)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--seasons", default="1999:2026")
    p.add_argument("--manifest", default=CATALOG_URL)
    p.add_argument("--data-root", default="/home/sagemaker-user/nfl-edge-lab-data")
    p.add_argument("--return-dir", default="/home/sagemaker-user")
    p.add_argument("--bucket", default="sagemaker-nfl-edge-lab-560403859723-us-west-2")
    p.add_argument("--workers", type=int, default=6)
    p.add_argument("--max-seconds", type=int, default=2400)
    p.add_argument("--max-download-gb", type=float, default=5.0)
    p.add_argument("--plan", action="store_true")
    p.add_argument("--self-test", action="store_true")
    p.add_argument("--no-s3", action="store_true")
    a = p.parse_args()
    self_test()
    if a.self_test:
        return 0
    if not 1 <= a.workers <= 12 or a.max_seconds < 60 or a.max_download_gb <= 0:
        p.error("workers must be 1..12, max-seconds >= 60, max-download-gb > 0")
    years = seasons_parse(a.seasons)
    start = time.monotonic()
    started = dt.datetime.now(dt.timezone.utc).isoformat()
    raw_root = Path(a.data_root)
    raw_root.mkdir(parents=True, exist_ok=True)
    rows = []
    error = None
    manifest_hash = "unavailable"
    chosen = []
    bucket = None if a.no_s3 else a.bucket
    try:
        catalog, manifest_hash = load_catalog(a.manifest)
        chosen = [x for x in catalog["assets"] if not asset_years(x["name"])
                  or bool(asset_years(x["name"]) & years)]
        total = sum(int(x["bytes"]) for x in chosen)
        if total > a.max_download_gb * (1024**3):
            raise ValueError("Planned bytes exceed max-download-gb: %d" % total)
        log("PLAN", files=len(chosen), expected_mb=round(total / 1e6, 1),
            manifest_sha256=manifest_hash, s3_bucket=bucket)
        if a.plan:
            return 0
        s3 = None
        if bucket:
            import boto3
            s3 = boto3.client("s3", region_name="us-west-2")
            s3.head_bucket(Bucket=bucket)
        deadline = start + a.max_seconds
        with cf.ThreadPoolExecutor(max_workers=a.workers) as pool:
            pending = {pool.submit(download_one, x, raw_root, s3, bucket, deadline): x
                       for x in chosen}
            while pending:
                done, _ = cf.wait(pending, timeout=25, return_when=cf.FIRST_COMPLETED)
                for future in done:
                    item = pending.pop(future)
                    try:
                        row = future.result()
                    except Exception as exc:
                        row = {"asset": item["name"], "tag": item["release_tag"],
                               "status": "error", "reason": repr(exc)[:250]}
                    rows.append(row)
                    if row["status"] == "error":
                        log("ASSET_ERROR", tag=row["tag"], asset=row["asset"],
                            reason=row.get("reason"))
                if not done:
                    log("HEARTBEAT", finished=len(rows), remaining=len(pending),
                        elapsed=round(time.monotonic() - start),
                        expected_mb=round(total / 1e6))
    except Exception as exc:
        error = repr(exc)
        log("FATAL", message=error)
    finally:
        returned, result = write_return(Path(a.return_dir), manifest_hash,
                                        chosen, rows, started, bucket,
                                        time.monotonic() - start, error)
    return 0 if result["all_ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
