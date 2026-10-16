#!/usr/bin/env python3
"""Sports Edge Lab: resumable, attributed public statistical archive ingestion.

Run once per sport, or --sport all. Uses no credentials except the AWS role.
Community statistical archives are explicitly recorded as secondary sources;
they are not represented as independently scraped original observations.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
import uuid
import zipfile

REPO = "sportsdataverse/sportsdataverse-data"
API = "https://api.github.com/repos/" + REPO
FORMATS = {".parquet": 0, ".csv.gz": 1, ".csv": 2, ".json.gz": 3, ".json": 4, ".rds": 5}
SPORTS = ("nba", "ncaaf", "ncaam", "ncaaw")
CFB = {"betting", "coach_careers", "drives", "game_rosters", "injuries", "linescores", "pbp", "play_participants", "player_box", "rosters", "schedules", "team_box", "teams"}
COLLEGE = {"lineups", "matchup_stints", "pbp", "player_box", "possessions", "rosters", "schedule", "shots", "team_box", "team_ids", "team_rosters"}
HEADERS = {"User-Agent": "SportsEdgeLab/1.0 (public historical research ingestion)", "Accept": "application/vnd.github+json"}


def utcnow():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def tag_sport(tag):
    # Archive source statistics, not other researchers' engineered features/models.
    if any(word in tag for word in ("model", "ratings", "rolling", "features", "impact", "rapm", "metric_curves", "predictions", "forecast")):
        return None
    if tag.startswith("espn_nba_") or tag.startswith("nba_stats_") or tag in {"nba_crosswalk", "nba_groups"}:
        return "nba"
    if tag.startswith("espn_mens_college_basketball_") or tag in {"espn_mbb_injuries", "mbb_groups"}:
        return "ncaam"
    if tag.startswith("espn_womens_college_basketball_") or tag in {"espn_wbb_injuries", "wbb_groups"}:
        return "ncaaw"
    if tag.startswith("ncaa_mbb_") and tag.removeprefix("ncaa_mbb_") in COLLEGE:
        return "ncaam"
    if tag.startswith("ncaa_wbb_") and tag.removeprefix("ncaa_wbb_") in COLLEGE:
        return "ncaaw"
    if tag.startswith("espn_cfb_") and tag.removeprefix("espn_cfb_") in CFB:
        return "ncaaf"
    if tag.startswith("ncaa_mfb_") and tag.removeprefix("ncaa_mfb_") in {"drives", "linescore", "officials", "pbp", "player_stats", "rosters", "schedule", "team_stats", "teams"}:
        return "ncaaf"
    if tag in {"cfbfastR_cfb_pbp", "cfb_schedules", "cfb_team_info", "cfb_crosswalk", "cfb_groups", "cfb_recruits", "cfb_team_portal"}:
        return "ncaaf"
    return None


def extension(name):
    return next((ext for ext in FORMATS if name.lower().endswith(ext)), None)


def select_assets(releases, sports=SPORTS):
    """Keep one encoding per dataset; never derive URLs or season availability."""
    result, rejected = [], []
    for release in releases:
        tag = release["tag_name"]
        sport = tag_sport(tag)
        if sport not in sports:
            continue
        groups = {}
        for asset in release.get("assets", []):
            name = asset.get("name", "")
            ext = extension(name)
            if not ext or name.startswith(("timestamp.", "package_function.")):
                continue
            if "/" in name or "\\" in name or name.startswith("."):
                raise ValueError("Unsafe source asset name")
            if any(x in name.lower() for x in ("model_artifact", "trained_model", "rapm")):
                rejected.append({"tag": tag, "name": name, "reason": "third_party_model_output"})
                continue
            stem = name[:-len(ext)]
            old = groups.get(stem)
            if old is None or FORMATS[ext] < FORMATS[extension(old["name"])]:
                groups[stem] = asset
        for a in groups.values():
            url = a["browser_download_url"]
            if not url.startswith("https://github.com/" + REPO + "/releases/download/"):
                raise ValueError("Unexpected upstream URL")
            digest = a.get("digest") or ""
            sha = digest.removeprefix("sha256:") if digest.startswith("sha256:") else None
            if sha and not re.fullmatch("[0-9a-f]{64}", sha):
                raise ValueError("Malformed upstream SHA256")
            result.append({"sport": sport, "release": tag, "name": a["name"], "url": url,
                           "asset_id": a["id"], "size": a["size"], "sha256": sha,
                           "updated_at": a.get("updated_at"), "release_url": release.get("html_url"),
                           "lineage": "SportsDataverse compiled statistical archive; upstream rights retained",
                           "pregame_eligibility": "unverified; contains postgame observations"})
    return sorted(result, key=lambda a: ("pbp" in a["release"], a["sport"], a["release"], a["name"])), rejected


def asset_key(a, prefix):
    identity = a["sha256"] or hashlib.sha256((str(a["asset_id"]) + ":" + str(a.get("updated_at"))).encode()).hexdigest()
    return f"{prefix.strip('/')}/{a['sport']}/raw/sportsdataverse/{a['release']}/{identity}/{a['name']}"


class BudgetExceeded(Exception):
    pass


class Budget:
    def __init__(self, seconds, cap):
        self.started = time.monotonic()
        self.deadline = self.started + seconds
        self.cap = cap
        self.bytes = 0
        self.reserved = 0
        self.lock = threading.Lock()

    def check(self):
        if time.monotonic() >= self.deadline:
            raise BudgetExceeded("runtime_cap")

    def consume(self, count):
        with self.lock:
            self.check()
            if self.bytes + count > self.cap:
                raise BudgetExceeded("transfer_cap")
            self.bytes += count

    def reserve(self, count):
        # Each HTTP attempt reserves its full listed size before opening a body.
        # This also bounds transfer volume for failed retries across threads.
        with self.lock:
            self.check()
            if self.reserved + count > self.cap:
                raise BudgetExceeded("transfer_cap")
            self.reserved += count


def get_json(url, budget):
    for attempt in range(4):
        budget.check()
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS), timeout=40) as response:
                return json.load(response)
        except urllib.error.HTTPError as error:
            if error.code not in (429, 500, 502, 503, 504) or attempt == 3:
                raise
            time.sleep(min(2 ** attempt, 8))


def discover(budget):
    releases = []
    for page in range(1, 21):
        batch = get_json(API + f"/releases?per_page=100&page={page}", budget)
        if not isinstance(batch, list):
            raise ValueError("Invalid GitHub releases response")
        releases.extend(batch)
        if len(batch) < 100:
            return releases
    raise ValueError("Release inventory pagination safety cap reached")


def json_bytes(value):
    return json.dumps(value, indent=2, sort_keys=True).encode()


def log(event, **values):
    print(json.dumps({"at": utcnow(), "event": event, **values}, sort_keys=True), flush=True)


def validate_file(path, asset):
    size = os.path.getsize(path)
    if size != asset["size"] or size == 0:
        raise ValueError(f"Source size mismatch expected={asset['size']} actual={size}")
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        magic = f.read(8)
        digest.update(magic)
        while chunk := f.read(4 * 1024 * 1024):
            digest.update(chunk)
    sha = digest.hexdigest()
    if asset.get("sha256") and sha != asset["sha256"]:
        raise ValueError("Source SHA256 mismatch; catalog refresh required")
    ext = extension(asset["name"])
    if ext == ".parquet":
        with open(path, "rb") as f:
            f.seek(-4, 2)
            if magic[:4] != b"PAR1" or f.read(4) != b"PAR1":
                raise ValueError("Invalid Parquet framing")
    if ext in (".csv", ".json") and magic.lower().startswith((b"<!doctyp", b"<html")):
        raise ValueError("HTML returned instead of data")
    if ext == ".json":
        with open(path) as f:
            json.load(f)
    return sha


def acquire(asset, s3, args, budget, transfer):
    from botocore.exceptions import ClientError
    key = asset_key(asset, args.prefix)
    receipt = {**asset, "bucket": args.bucket, "key": key, "checked_at": utcnow()}
    try:
        budget.check()
        try:
            head = s3.head_object(Bucket=args.bucket, Key=key)
        except ClientError as error:
            if error.response.get("ResponseMetadata", {}).get("HTTPStatusCode") != 404:
                raise
            head = None
        if head:
            metadata = head.get("Metadata", {})
            if head["ContentLength"] != asset["size"] or not metadata.get("sha256"):
                raise ValueError("Existing object failed integrity metadata gate")
            if asset.get("sha256") and asset["sha256"] != metadata["sha256"]:
                raise ValueError("Existing object upstream hash mismatch")
            return {**receipt, "status": "reused", "sha256": metadata["sha256"]}
        with tempfile.TemporaryDirectory(prefix="sports-edge-public-") as work:
            path = os.path.join(work, "payload")
            for attempt in range(3):
                budget.check()
                budget.reserve(asset["size"])
                try:
                    with urllib.request.urlopen(urllib.request.Request(asset["url"], headers={"User-Agent": HEADERS["User-Agent"]}), timeout=45) as response, open(path, "wb") as target:
                        while chunk := response.read(min(1024 * 1024, asset["size"] - target.tell())):
                            budget.consume(len(chunk))
                            target.write(chunk)
                        declared = response.headers.get("Content-Length")
                        if declared and int(declared) != asset["size"]:
                            raise ValueError("HTTP content length differs from pinned asset size")
                    break
                except urllib.error.HTTPError as error:
                    if error.code not in (429, 500, 502, 503, 504) or attempt == 2:
                        raise
                    time.sleep(min(2 ** attempt, 8))
            sha = validate_file(path, asset)
            s3.upload_file(path, args.bucket, key, Config=transfer,
                           ExtraArgs={"ServerSideEncryption": "AES256", "Metadata": {
                               "sha256": sha, "source-asset-id": str(asset["asset_id"]),
                               "source-updated-at": str(asset.get("updated_at") or "unknown"),
                               "lineage": "secondary-public-statistical-archive"}})
            receipt.update(status="downloaded", sha256=sha, acquired_at=utcnow())
            s3.put_object(Bucket=args.bucket, Key=key + ".receipt.json", Body=json_bytes(receipt),
                          ContentType="application/json", ServerSideEncryption="AES256")
            return receipt
    except BudgetExceeded as error:
        return {**receipt, "status": "deferred", "reason": str(error)}
    except Exception as error:
        # Preserve per-asset failures and fail the final gate; never pretend success.
        return {**receipt, "status": "failed", "error_type": type(error).__name__, "error": str(error)[:500]}


class SelfTests(unittest.TestCase):
    def test_track_matching(self):
        self.assertEqual(tag_sport("espn_mens_college_basketball_pbp"), "ncaam")
        self.assertEqual(tag_sport("espn_womens_college_basketball_pbp"), "ncaaw")
        self.assertEqual(tag_sport("nba_stats_shots"), "nba")
        self.assertEqual(tag_sport("espn_cfb_pbp"), "ncaaf")
        self.assertIsNone(tag_sport("cfb_model_artifacts"))
        self.assertIsNone(tag_sport("ncaa_mbb_rapm"))

    def test_format_preference_and_url(self):
        assets = [{"name": "schedule_2025" + e, "browser_download_url": f"https://github.com/{REPO}/releases/download/espn_nba_schedules/a", "id": i, "size": 16} for i, e in enumerate((".csv", ".rds", ".parquet"))]
        selected, _ = select_assets([{"tag_name": "espn_nba_schedules", "assets": assets}])
        self.assertEqual(len(selected), 1)
        self.assertEqual(selected[0]["name"], "schedule_2025.parquet")
        assets[2]["browser_download_url"] = "https://unexpected.example/a"
        with self.assertRaises(ValueError):
            select_assets([{"tag_name": "espn_nba_schedules", "assets": assets}])

    def test_budget(self):
        b = Budget(60, 5)
        b.reserve(5)
        with self.assertRaises(BudgetExceeded):
            b.reserve(1)
        b.consume(5)
        with self.assertRaises(BudgetExceeded):
            b.consume(1)

    def test_hash_and_framing(self):
        payload = b"PAR1testPAR1"
        with tempfile.NamedTemporaryFile() as f:
            f.write(payload)
            f.flush()
            asset = {"size": len(payload), "name": "a.parquet", "sha256": hashlib.sha256(payload).hexdigest()}
            self.assertEqual(validate_file(f.name, asset), asset["sha256"])
            asset["sha256"] = "0" * 64
            with self.assertRaises(ValueError):
                validate_file(f.name, asset)

    def test_key(self):
        a = {"sport": "nba", "release": "espn_nba_pbp", "name": "pbp_2025.parquet", "asset_id": 1, "updated_at": "2026", "sha256": "a" * 64}
        self.assertIn("tracks/nba/raw/", asset_key(a, "tracks"))
        b = {**a, "sha256": "b" * 64}
        self.assertNotEqual(asset_key(a, "tracks"), asset_key(b, "tracks"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sport", choices=(*SPORTS, "all"), default="all")
    parser.add_argument("--bucket")
    parser.add_argument("--prefix", default="tracks")
    parser.add_argument("--region", default="us-west-2")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--max-seconds", type=int, default=3600)
    parser.add_argument("--max-download-gb", type=float, default=30)
    parser.add_argument("--hourly-usd", type=float, default=0.461)
    parser.add_argument("--output-dir", default="/opt/ml/processing/output")
    parser.add_argument("--manifest", help="Optional local already-pinned manifest: {'assets': [...]} or asset list")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    test = unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.loadTestsFromTestCase(SelfTests))
    if not test.wasSuccessful():
        return 2
    if args.self_test:
        return 0
    if not args.bucket:
        parser.error("--bucket is required")
    if not 1 <= args.workers <= 8 or not 60 <= args.max_seconds <= 7200 or not 0 < args.max_download_gb <= 100:
        parser.error("Invalid resource bounds")
    import boto3
    from botocore.config import Config
    from boto3.s3.transfer import TransferConfig
    s3 = boto3.client("s3", region_name=args.region, config=Config(retries={"mode": "adaptive", "total_max_attempts": 4}, connect_timeout=10, read_timeout=60, max_pool_connections=16))
    transfer = TransferConfig(max_concurrency=2, multipart_threshold=16 * 1024 * 1024)
    budget = Budget(args.max_seconds - 60, int(args.max_download_gb * 1024 ** 3))
    run_id = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]
    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    records, assets, rejected, fatal = [], [], [], None
    sports = SPORTS if args.sport == "all" else (args.sport,)
    try:
        log("discovery_started", run_id=run_id, sport=args.sport)
        if args.manifest:
            with open(args.manifest) as f:
                manifest = json.load(f)
            candidate_assets = manifest.get("assets", []) if isinstance(manifest, dict) else manifest
            assets = []
            for a in candidate_assets:
                a = dict(a)
                a["release"] = a.get("release", a.get("tag"))
                a["sport"] = tag_sport(a["release"])
                a["sha256"] = (a.get("sha256") or "").removeprefix("sha256:") or None
                if a["sport"] in sports:
                    assets.append(a)
        else:
            releases = discover(budget)
            assets, rejected = select_assets(releases, sports)
        if not assets:
            raise ValueError("No eligible source assets discovered")
        manifest = {"run_id": run_id, "discovered_at": utcnow(), "repository": REPO, "assets": assets, "excluded": rejected}
        (output / "manifest.json").write_bytes(json_bytes(manifest))
        for sport in sports:
            per_sport = {**manifest, "assets": [a for a in assets if a["sport"] == sport]}
            s3.put_object(Bucket=args.bucket, Key=f"{args.prefix}/{sport}/catalogs/public-archive-{run_id}.json", Body=json_bytes(per_sport), ContentType="application/json", ServerSideEncryption="AES256")
        log("manifest_pinned", assets=len(assets), bytes_cataloged=sum(a["size"] for a in assets))
        iterator = iter(assets)
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
            pending = {pool.submit(acquire, a, s3, args, budget, transfer): a for a in [next(iterator, None) for _ in range(args.workers)] if a}
            last_beat = time.monotonic()
            while pending:
                completed, _ = concurrent.futures.wait(pending, timeout=15, return_when=concurrent.futures.FIRST_COMPLETED)
                for future in completed:
                    pending.pop(future)
                    record = future.result()
                    records.append(record)
                    if record["status"] == "failed":
                        log("asset_failed", release=record["release"], name=record["name"], error=record["error"])
                    if time.monotonic() < budget.deadline and budget.bytes < budget.cap:
                        asset = next(iterator, None)
                        if asset:
                            pending[pool.submit(acquire, asset, s3, args, budget, transfer)] = asset
                if time.monotonic() - last_beat >= 15:
                    elapsed = time.monotonic() - budget.started
                    log("heartbeat", completed=len(records), remaining=len(assets) - len(records), downloaded_bytes=budget.bytes, elapsed_seconds=round(elapsed), estimated_compute_usd=round(elapsed / 3600 * args.hourly_usd, 4))
                    last_beat = time.monotonic()
    except Exception as error:
        fatal = {"error_type": type(error).__name__, "error": str(error)[:1000]}
        log("run_error", **fatal)
    elapsed = time.monotonic() - budget.started
    counts = {status: sum(r["status"] == status for r in records) for status in ("downloaded", "reused", "failed", "deferred")}
    counts["not_attempted"] = len(assets) - len(records)
    all_ok = not fatal and bool(assets) and counts["downloaded"] + counts["reused"] == len(assets)
    report = {"run_id": run_id, "sport": args.sport, "completed_at": utcnow(), "all_ok": all_ok, "counts": counts,
              "assets_cataloged": len(assets), "bytes_downloaded_including_retries": budget.bytes,
              "bytes_verified": sum(r["size"] for r in records if r["status"] in ("downloaded", "reused")),
              "elapsed_seconds": round(elapsed, 2), "estimated_compute_usd": round(elapsed / 3600 * args.hourly_usd, 6),
              "cost_note": "Processing compute estimate only; storage, requests, and boot time additional",
              "fatal": fatal, "acceptance_scope": "archive byte-integrity only; schema, coverage and point-in-time gates remain"}
    (output / "report.json").write_bytes(json_bytes(report))
    (output / "receipts.jsonl").write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in records))
    bundle = output / f"sports_edge_lab_public_{args.sport}_return_{run_id}.zip"
    with zipfile.ZipFile(bundle, "w", zipfile.ZIP_DEFLATED) as z:
        for name in ("report.json", "receipts.jsonl", "manifest.json"):
            if (output / name).exists():
                z.write(output / name, name)
    for sport in sports:
        s3.upload_file(str(bundle), args.bucket, f"{args.prefix}/{sport}/acquisition-runs/{run_id}/{bundle.name}", ExtraArgs={"ServerSideEncryption": "AES256"}, Config=transfer)
        s3.put_object(Bucket=args.bucket, Key=f"{args.prefix}/{sport}/acquisition-runs/{run_id}/report.json", Body=json_bytes(report), ContentType="application/json", ServerSideEncryption="AES256")
    log("finished", **report)
    return 0 if all_ok else 3


if __name__ == "__main__":
    sys.exit(main())
