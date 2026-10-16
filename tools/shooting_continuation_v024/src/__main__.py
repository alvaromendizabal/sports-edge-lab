"""Resume missing direct CBBD shooting summaries from preserved source caches.

Run this self-contained artifact on AWS. It never downloads play-by-play,
lineups, substitutions, odds, or source discovery. Historical summaries remain
postgame data and are not approved as pregame features.
"""
import argparse
import collections
import concurrent.futures
import logging
import sys
import threading
import time
import unittest
import urllib.error
from types import SimpleNamespace
from unittest.mock import patch

from acquire_paid_data import (Archive, Budget, BudgetStop, blob, digest, emit,
    identity, parse, self_test, shooting_selectors)

VERSION = "sports-edge-lab-cbbd-shooting-continuation-v024"
SOURCE_RUN = "20261016T005814Z-dc2ec3e9a5"
STOPPED_RUN = "20261016T191449Z-151560b90d"
ENDPOINTS = ("/stats/team/shooting/season", "/stats/player/shooting/season")
SEASONS = (2003,) + tuple(range(2006, 2028))


def rid_for(endpoint, params, vintage=""):
    return digest(blob(identity("cbbd", "ncaam", endpoint, params, vintage)))


def season_vintage(season, end, day):
    return day if season >= end.year + (end.month >= 7) else ""


def cached_stats_key(season, end, day):
    rid = rid_for("/stats/team/season", {"season": season}, season_vintage(season, end, day))
    return "tracks/ncaam/raw/cbbd/request-index/" + rid + ".json"


def valid_receipt(receipt, expected_request_id=None):
    if not isinstance(receipt, dict) or receipt.get("status") != 200:
        return False
    request = receipt.get("request", {})
    if request.get("provider") != "cbbd" or request.get("track") != "ncaam":
        return False
    if digest(blob(request)) != receipt.get("request_id"):
        return False
    if expected_request_id and receipt["request_id"] != expected_request_id:
        return False
    sha = receipt.get("sha256", "")
    return (len(sha) == 64 and all(c in "0123456789abcdef" for c in sha)
            and receipt.get("raw_key") == "tracks/ncaam/raw/cbbd/objects/" + sha[:2] + "/" + sha + ".json.gz")


def tasks_for(season, rows, end, day):
    if season not in SEASONS:
        raise ValueError("Season outside documented shooting scope")
    if not isinstance(rows, list) or not all(isinstance(x, dict) for x in rows):
        raise ValueError("Invalid cached team-stat rows")
    vintage = season_vintage(season, end, day)
    tasks = []
    for selector in shooting_selectors(rows):
        if len(selector) != 1 or not all(isinstance(v, str) and v.strip() for v in selector.values()):
            raise ValueError("Invalid shooting selector")
        for endpoint in ENDPOINTS:
            params = {"season": season, **selector}
            tasks.append((endpoint, params, vintage, rid_for(endpoint, params, vintage)))
    return tasks


def positive_shooting(rows, season, team=None):
    return isinstance(rows, list) and any(isinstance(row, dict) and row.get("season") == season
        and (team is None or row.get("team") == team)
        and isinstance(row.get("trackedShots"), (int, float)) and row["trackedShots"] > 0 for row in rows)


class RateLimitedOpener:
    """Global request pacing, including retries; all workers share one limiter."""
    def __init__(self, delegate, owner, interval=0.5, clock=time.monotonic, sleep=time.sleep):
        self.delegate, self.owner, self.interval = delegate, owner, interval
        self.clock, self.sleep = clock, sleep
        self.lock = threading.Lock()
        self.next_at = 0.0

    def open(self, request, timeout):
        with self.lock:
            self.owner.time_left()
            with self.owner.budget.lock:
                if "cbbd" in self.owner.budget.disabled:
                    raise BudgetStop("provider_disabled_before_http")
            wait = max(0, self.next_at - self.clock())
            if wait:
                self.sleep(wait)
            self.owner.time_left()
            with self.owner.budget.lock:
                if "cbbd" in self.owner.budget.disabled:
                    raise BudgetStop("provider_disabled_before_http")
            self.next_at = self.clock() + self.interval
        try:
            return self.delegate.open(request, timeout=timeout)
        except urllib.error.HTTPError as exc:
            # Do not retry or work around authentication/access/rate denials.
            if exc.code in (401, 402, 403, 429):
                self.owner.budget.disable("cbbd")
            raise


class ShootingContinuation(Archive):
    def __init__(self, args):
        super().__init__(args)
        self.opener = RateLimitedOpener(self.opener, self)
        self.blocked_statuses = set()
        self.inventory = {}
        self.source_evidence = []
        self.pending_source_seasons = []
        self.seed_counts = collections.Counter()
        self.plan_key = "shared/acquisition/paid/" + self.run_id + "/shooting-plan.json"
        self.extra_return_members = {}
        self.canary_evidence = []
        self.stopped_audit_key = "shared/acquisition/paid/" + self.run_id + "/stopped-v021-audit.json"

    def audit_stopped_run(self):
        prefix = "tracks/ncaam/raw/cbbd/receipts/" + STOPPED_RUN + "/"
        keys = [obj["Key"] for page in self.s3.get_paginator("list_objects_v2").paginate(
            Bucket=self.args.bucket, Prefix=prefix) for obj in page.get("Contents", [])]
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            receipts = list(pool.map(self.s3_json, keys))
        if not all(valid_receipt(r) and r.get("run_id") == STOPPED_RUN for r in receipts):
            raise RuntimeError("Stopped-run receipt audit failed")
        progress = self.s3_json("shared/acquisition/paid/" + STOPPED_RUN + "/progress.json")
        report = {"source_run": STOPPED_RUN, "snapshot_by_run": self.run_id,
            "status": "operator_stopped_after_empty_response_detection",
            "receipt_count": len(receipts), "empty_receipts": sum(r.get("records") == 0 for r in receipts),
            "nonempty_receipts": sum(isinstance(r.get("records"), int) and r["records"] > 0 for r in receipts),
            "raw_response_bytes": sum(r["bytes"] for r in receipts),
            "distinct_raw_hashes": len({r["sha256"] for r in receipts}),
            "last_progress": progress, "receipts": receipts,
            "interpretation": "HTTP success with empty data is a coverage observation, not acquired shooting records. No invalid query parameters demonstrated; empty caches remain valid."}
        self.save_json(self.stopped_audit_key, report)
        self.extra_return_members["stopped-v021-audit.json"] = report
        self.seed_counts["stopped_v021_empty_receipts"] = report["empty_receipts"]
        self.seed_counts["stopped_v021_nonempty_receipts"] = report["nonempty_receipts"]

    def seed(self):
        prefix = "shared/acquisition/paid/" + self.args.source_run
        previous = self.s3_json(prefix + "/summary.json")
        receipts = self.s3_json(prefix + "/receipts.json")
        if not isinstance(previous, dict) or not isinstance(receipts, list):
            raise RuntimeError("Required shooting source evidence unavailable")
        if previous.get("run_id") != self.args.source_run:
            raise RuntimeError("Shooting source run mismatch")
        for receipt in receipts:
            request = receipt.get("request", {})
            if request.get("endpoint") in ENDPOINTS:
                if not valid_receipt(receipt):
                    raise RuntimeError("Invalid shooting source receipt")
                self.cache[receipt["request_id"]] = receipt
        self.seed_counts["successful_shooting_request_ids"] = len(self.cache)
        self.seed_counts["previous_nonempty_receipts"] = sum(isinstance(r.get("records"), int) and r["records"] > 0 for r in self.cache.values())
        self.seed_counts["previous_empty_receipts"] = sum(r.get("records") == 0 for r in self.cache.values())
        self.seed_counts["previous_failed_requests"] = previous.get("failures_count", 0)
        self.phase["seed"] = {"status": "completed", **dict(self.seed_counts)}

    def cached_positive_gate(self):
        for endpoint in ENDPOINTS:
            rid = rid_for(endpoint, {"season": 2026, "conference": "ACC"})
            receipt = self.cache.get(rid)
            if not valid_receipt(receipt, rid):
                raise RuntimeError("Required positive ACC receipt missing")
            rows = self.content(receipt)
            if not positive_shooting(rows, 2026, "Duke"):
                raise RuntimeError("Known Duke shooting cache failed positive-data gate")
            self.canary_evidence.append({"kind": "cached_positive", "request_id": rid,
                "records": len(rows), "sha256": receipt["sha256"], "requires_positive_tracked_shots": True})
        self.phase["positive_cached_gate"] = {"status": "passed", "endpoints": len(ENDPOINTS)}

    def plan(self):
        tasks = []
        for season in sorted(SEASONS, reverse=True):
            self.time_left()
            key = cached_stats_key(season, self.end, self.day)
            receipt = self.s3_json(key)
            expected = key.rsplit("/", 1)[1].split(".", 1)[0]
            if receipt is None:
                self.pending_source_seasons.append(season)
                self.inventory[str(season)] = {"status": "source_cache_missing"}
                continue
            if not valid_receipt(receipt, expected):
                raise RuntimeError("Invalid source-stat request receipt")
            rows = self.content(receipt)  # verifies preserved raw SHA-256
            all_candidates = tasks_for(season, rows, self.end, self.day)
            candidates = [task for task in all_candidates if "conference" in task[1]]
            missing = [t for t in candidates if t[3] not in self.cache]
            self.inventory[str(season)] = {"status": "source_cache_verified", "source_rows": len(rows),
                "planned_shooting_requests": len(candidates), "seeded_successes": len(candidates) - len(missing),
                "remaining_before_request_index_check": len(missing)}
            self.inventory[str(season)]["deferred_conference_less_team_requests"] = len(all_candidates) - len(candidates)
            self.source_evidence.append({"season": season, "receipt_key": key,
                "raw_key": receipt["raw_key"], "sha256": receipt["sha256"]})
            tasks.extend(missing)
        self.save_json(self.plan_key, {"version": VERSION, "run_id": self.run_id,
            "tasks": [{"endpoint": e, "params": p, "vintage": v, "request_id": r} for e, p, v, r in tasks],
            "source_evidence": self.source_evidence, "inventory": self.inventory})
        return tasks

    def acquire_one(self, endpoint, params, vintage, rid):
        if endpoint not in ENDPOINTS or params.get("season") not in SEASONS:
            raise ValueError("Only documented shooting summaries allowed")
        if len(set(params) & {"team", "conference"}) != 1:
            raise ValueError("Exactly one team/conference filter required")
        if set(params) - {"season", "team", "conference"} or rid != rid_for(endpoint, params, vintage):
            raise ValueError("Invalid planned shooting request")
        result = self.capture("cbbd", "ncaam", endpoint, params, "cbbd_season" + endpoint, vintage, need_data=True)
        if result is not None and not isinstance(result, list):
            self.failure(identity("cbbd", "ncaam", endpoint, params, vintage), "unexpected_shooting_schema")
        with self.lock:
            phase = self.phase["shooting_continuation"]
            phase["processed"] += 1
            phase["remaining"] = phase["planned"] - phase["processed"]
            phase["http_successful_or_reused"] += int(isinstance(result, list))
            phase["unsuccessful"] += int(not isinstance(result, list))
            if isinstance(result, list):
                self.stats["shooting_records_observed"] += len(result)
                self.stats["shooting_nonempty_responses"] += int(bool(result))
                self.stats["shooting_empty_responses"] += int(not result)
                self.stats["shooting_positive_data_responses"] += int(positive_shooting(result, params["season"]))
                season_stats = self.inventory[str(params["season"])]
                season_stats["nonempty_responses_this_run"] = season_stats.get("nonempty_responses_this_run", 0) + int(bool(result))
                season_stats["empty_responses_this_run"] = season_stats.get("empty_responses_this_run", 0) + int(not result)
                season_stats["records_this_run"] = season_stats.get("records_this_run", 0) + len(result)
        return result

    def work(self):
        self.audit_stopped_run()
        self.seed()
        self.cached_positive_gate()
        tasks = self.plan()
        self.phase["shooting_continuation"] = {"status": "running", "planned": len(tasks),
            "processed": 0, "remaining": len(tasks), "completed": 0, "http_successful_or_reused": 0, "unsuccessful": 0}
        self.checkpoint()
        canary_ids = set()
        for endpoint in ENDPOINTS:
            canary = next((t for t in tasks if t[0] == endpoint and t[1] == {"season": 2024, "conference": "ACC"}), None)
            if canary is None:
                raise RuntimeError("Expected 2024 ACC fresh canary absent from gap plan")
            rows = self.acquire_one(*canary)
            self.phase["shooting_continuation"]["completed"] += 1
            if not positive_shooting(rows, 2024, "Duke"):
                raise RuntimeError("Known 2024 ACC shooting failed fresh positive-data gate")
            self.canary_evidence.append({"kind": "fresh_or_request_index_positive", "request_id": canary[3],
                "records": len(rows), "requires_positive_tracked_shots": True})
            canary_ids.add(canary[3])
        self.phase["positive_fresh_gate"] = {"status": "passed", "endpoints": len(ENDPOINTS)}
        self.checkpoint()
        self.parallel_tasks([t for t in tasks if t[3] not in canary_ids], self.acquire_one,
            "shooting_continuation", self.args.workers)

    def summary(self):
        result = super().summary()
        result.update(version=VERSION, source_run=self.args.source_run, seed_counts=dict(self.seed_counts),
            scope="Only missing conference-filtered CBBD team/player season shooting breakdowns: 2003 and 2006-2027",
            source_inventory=self.inventory, pending_source_seasons=self.pending_source_seasons,
            plan_key=self.plan_key, source_evidence=self.source_evidence, paid_discovery_requests=0,
            skipped_documented_absent_seasons=[2004, 2005], maximum_http_requests_per_second=2,
            canary_evidence=self.canary_evidence, stopped_v021_audit_key=self.stopped_audit_key,
            deferred_scope="Conference-less team selectors require independent coverage evidence before paid acquisition",
            not_completed_by_this_runner=["raw_shot_coordinate_acquisition_in_active_plays_job",
                "NCAA_women_shooting", "point_in_time_feature_approval", "complete_season_coverage"],
            official_documentation=["https://api.collegebasketballdata.com/api/stats",
                "https://api.collegebasketballdata.com/data-availability"])
        return result


def shooting_tests():
    def fixture(endpoint="/stats/team/shooting/season", season=2026):
        request = identity("cbbd", "ncaam", endpoint, {"season": season, "conference": "ACC"})
        sha = "a" * 64
        return {"status": 200, "request": request, "request_id": digest(blob(request)),
            "sha256": sha, "raw_key": "tracks/ncaam/raw/cbbd/objects/aa/" + sha + ".json.gz"}
    class Checks(unittest.TestCase):
        def test_doc_scope(self):
            self.assertNotIn(2004, SEASONS)
            self.assertNotIn(2005, SEASONS)
            self.assertIn(2003, SEASONS)
            with self.assertRaises(ValueError):
                tasks_for(2005, [], parse("2026-10-16T00:00:00Z"), "2026-10-16")
        def test_filtered_dedup(self):
            tasks = tasks_for(2026, [{"team": "Duke", "conference": "ACC"},
                {"team": "UNC", "conference": "ACC"}, {"team": "Independent", "conference": None}],
                parse("2026-10-16T00:00:00Z"), "2026-10-16")
            self.assertEqual(len(tasks), 4)
            self.assertEqual(len({t[3] for t in tasks}), 4)
            self.assertEqual({t[0] for t in tasks}, set(ENDPOINTS))
        def test_no_paid_source_discovery(self):
            key = cached_stats_key(2026, parse("2026-10-16T00:00:00Z"), "2026-10-16")
            self.assertTrue(key.startswith("tracks/ncaam/raw/cbbd/request-index/"))
            self.assertEqual(key, cached_stats_key(2026, parse("2026-10-17T00:00:00Z"), "2026-10-17"))
        def test_current_vintage_separate(self):
            end = parse("2026-10-16T00:00:00Z")
            self.assertNotEqual(cached_stats_key(2027, end, "2026-10-16"), cached_stats_key(2027, end, "2026-10-17"))
        def test_receipt_identity_and_path_gate(self):
            good = fixture()
            self.assertTrue(valid_receipt(good))
            self.assertFalse(valid_receipt({**good, "request_id": "wrong"}))
            self.assertFalse(valid_receipt({**good, "raw_key": "elsewhere"}))
            self.assertFalse(valid_receipt({**good, "status": 403}))
        def test_missing_source_no_download(self):
            a = ShootingContinuation.__new__(ShootingContinuation)
            a.time_left = lambda: None
            a.end, a.day = parse("2026-10-16T00:00:00Z"), "2026-10-16"
            a.s3_json = lambda _: None
            a.save_json = lambda *args: None
            a.pending_source_seasons, a.inventory, a.source_evidence, a.cache = [], {}, [], {}
            a.run_id, a.plan_key = "test", "test-plan"
            self.assertEqual(a.plan(), [])
            self.assertEqual(len(a.pending_source_seasons), len(SEASONS))
        def test_success_seed_and_failed_retry(self):
            a = ShootingContinuation.__new__(ShootingContinuation)
            a.args, a.cache, a.seed_counts, a.phase = SimpleNamespace(source_run="run"), {}, collections.Counter(), {}
            good = fixture()
            data = {"summary.json": {"run_id": "run", "failures_count": 12}, "receipts.json": [good]}
            a.s3_json = lambda key: data[key.rsplit("/", 1)[1]]
            a.seed()
            self.assertIn(good["request_id"], a.cache)
            self.assertEqual(a.seed_counts["previous_failed_requests"], 12)
            self.assertNotIn(rid_for(ENDPOINTS[1], good["request"]["params"]), a.cache)
        def test_forbid_overlapping_endpoint(self):
            a = ShootingContinuation.__new__(ShootingContinuation)
            with self.assertRaises(ValueError):
                a.acquire_one("/plays/date", {"date": "2026-10-16"}, "", "x")
        def test_global_spacing_including_first_call(self):
            state = [0.0]
            times = []
            owner = SimpleNamespace(time_left=lambda: None, budget=Budget(0, 10))
            delegate = SimpleNamespace(open=lambda *a, **k: times.append(state[0]))
            op = RateLimitedOpener(delegate, owner, clock=lambda: state[0], sleep=lambda n: state.__setitem__(0, state[0]+n))
            op.open("request", 10)
            op.open("request", 10)
            op.open("request", 10)
            self.assertEqual(times, [0.0, 0.5, 1.0])
        def test_provider_denial_stops(self):
            for status in (401, 402, 403, 429):
                owner = SimpleNamespace(time_left=lambda: None, budget=Budget(0, 10))
                def fail(*a, **k):
                    raise urllib.error.HTTPError("https://api.collegebasketballdata.com", status, "denied", {}, None)
                op = RateLimitedOpener(SimpleNamespace(open=fail), owner)
                with self.assertRaises(urllib.error.HTTPError):
                    op.open("request", 10)
                with self.assertRaises(BudgetStop):
                    owner.budget.reserve("cbbd")
                with self.assertRaises(BudgetStop):
                    op.open("already_reserved_request", 10)
        def test_queued_worker_denied_after_pacing_wait(self):
            owner = SimpleNamespace(time_left=lambda: None, budget=Budget(0, 10))
            calls = []
            op = RateLimitedOpener(SimpleNamespace(open=lambda *a, **k: calls.append(1)), owner,
                clock=lambda: 0, sleep=lambda n: owner.budget.disable("cbbd"))
            op.next_at = 1
            with self.assertRaises(BudgetStop):
                op.open("queued", 10)
            self.assertEqual(calls, [])
        def test_cancelled_before_http_refunds_reservation(self):
            a = ShootingContinuation.__new__(ShootingContinuation)
            a.time_left = lambda: None
            a.cache, a.request_locks = {}, collections.defaultdict(threading.Lock)
            a.s3_json = lambda key: None
            a.blocked_endpoints = set()
            a.budget, a.keys = Budget(0, 10), {"cbbd": "test-placeholder"}
            a.args, a.deadline = SimpleNamespace(max_response_mb=64), time.monotonic() + 100
            counts = []
            a.count = lambda **kw: counts.append(kw)
            def cancelled(*args, **kwargs):
                raise BudgetStop("provider_disabled_before_http")
            a.opener = SimpleNamespace(open=cancelled)
            with self.assertRaises(BudgetStop):
                Archive.capture(a, "cbbd", "ncaam", ENDPOINTS[0], {"season": 2026, "conference": "ACC"}, "test")
            self.assertEqual(a.budget.snapshot()["reserved_or_known"]["stats"], 0)
            self.assertEqual(counts, [])
        def test_raw_capture_cache_blocks_provider_call(self):
            a = ShootingContinuation.__new__(ShootingContinuation)
            good = fixture()
            a.time_left = lambda: None
            a.cache, a.request_locks = {good["request_id"]: good}, collections.defaultdict(threading.Lock)
            a.count = lambda **kw: None
            a.content = lambda r: [{"team": "Duke", "trackedShots": 100}]
            # No S3 getter or opener exists: either call would fail this test.
            result = Archive.capture(a, "cbbd", "ncaam", ENDPOINTS[0], good["request"]["params"], "test")
            self.assertEqual(result[0]["trackedShots"], 100)
        def test_zero_odds_budget(self):
            b = Budget(0, 1)
            with self.assertRaises(BudgetStop):
                b.reserve("odds")
            b.reserve("cbbd")
            with self.assertRaises(BudgetStop):
                b.reserve("cbbd")
        def test_positive_data_gate_rejects_empty_wrong_season_and_zero(self):
            good = [{"season": 2026, "team": "Duke", "trackedShots": 2000}]
            self.assertTrue(positive_shooting(good, 2026, "Duke"))
            self.assertFalse(positive_shooting([], 2026, "Duke"))
            self.assertFalse(positive_shooting(good, 2025, "Duke"))
            self.assertFalse(positive_shooting(good, 2026, "UNC"))
            self.assertFalse(positive_shooting([{"season": 2026, "team": "Duke", "trackedShots": 0}], 2026, "Duke"))
        def test_cached_positive_gate_reads_both_endpoints(self):
            a = ShootingContinuation.__new__(ShootingContinuation)
            a.cache, a.canary_evidence, a.phase = {}, [], {}
            for endpoint in ENDPOINTS:
                receipt = fixture(endpoint)
                a.cache[receipt["request_id"]] = receipt
            a.content = lambda r: [{"season": 2026, "team": "Duke", "trackedShots": 100}]
            a.cached_positive_gate()
            self.assertEqual(len(a.canary_evidence), 2)
            a.content = lambda r: []
            with self.assertRaises(RuntimeError):
                a.cached_positive_gate()
        def test_conference_gap_plan_defers_unknown_teams(self):
            a = ShootingContinuation.__new__(ShootingContinuation)
            a.time_left = lambda: None
            a.end, a.day = parse("2026-10-16T00:00:00Z"), "2026-10-16"
            a.pending_source_seasons, a.inventory, a.source_evidence, a.cache = [], {}, [], {}
            a.run_id, a.plan_key = "test", "test-plan"
            request = identity("cbbd", "ncaam", "/stats/team/season", {"season": 2024})
            receipt = fixture()
            receipt.update(request=request, request_id=digest(blob(request)))
            key = cached_stats_key(2024, a.end, a.day)
            a.s3_json = lambda k: receipt if k == key else None
            a.content = lambda r: [{"team": "Duke", "conference": "ACC"}, {"team": "Widener", "conference": None}]
            a.save_json = lambda *args: None
            tasks = a.plan()
            self.assertEqual(len(tasks), 2)
            self.assertTrue(all(t[1] == {"season": 2024, "conference": "ACC"} for t in tasks))
            self.assertEqual(a.inventory["2024"]["deferred_conference_less_team_requests"], 2)
        def test_valid_empty_seed_is_preserved(self):
            a = ShootingContinuation.__new__(ShootingContinuation)
            a.args, a.cache, a.seed_counts, a.phase = SimpleNamespace(source_run="run"), {}, collections.Counter(), {}
            empty = fixture()
            empty["records"] = 0
            data = {"summary.json": {"run_id": "run", "failures_count": 0}, "receipts.json": [empty]}
            a.s3_json = lambda key: data[key.rsplit("/", 1)[1]]
            a.seed()
            self.assertIn(empty["request_id"], a.cache)
            self.assertEqual(a.seed_counts["previous_empty_receipts"], 1)
        def test_bulk_waits_for_both_positive_canaries(self):
            for positive in (True, False):
                a = ShootingContinuation.__new__(ShootingContinuation)
                calls = []
                a.audit_stopped_run = lambda: calls.append("audit")
                a.seed = lambda: calls.append("seed")
                a.cached_positive_gate = lambda: calls.append("cached_gate")
                tasks = tasks_for(2024, [{"conference": "ACC", "team": "Duke"}],
                    parse("2026-10-16T00:00:00Z"), "2026-10-16")
                a.plan = lambda: tasks
                a.phase, a.canary_evidence, a.args = {}, [], SimpleNamespace(workers=4)
                a.checkpoint = lambda: None
                def one(endpoint, params, vintage, rid):
                    calls.append(endpoint)
                    return [{"season": 2024, "team": "Duke", "trackedShots": 100}] if positive else []
                a.acquire_one = one
                a.parallel_tasks = lambda *args: calls.append("bulk")
                if positive:
                    a.work()
                    self.assertEqual(calls[-3:], [*ENDPOINTS, "bulk"])
                    self.assertEqual(a.phase["shooting_continuation"]["completed"], 2)
                else:
                    with self.assertRaises(RuntimeError):
                        a.work()
                    self.assertNotIn("bulk", calls)
    result = unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.loadTestsFromTestCase(Checks))
    if not result.wasSuccessful():
        raise RuntimeError("Shooting continuation self-test gate failed")
    return result.testsRun


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bucket", default="sagemaker-sports-edge-lab-560403859723-us-west-2")
    parser.add_argument("--region", default="us-west-2")
    parser.add_argument("--source-run", default=SOURCE_RUN)
    parser.add_argument("--cfbd-parameter", default="/sports-edge-lab/shared/cfbd/key")
    parser.add_argument("--stats-calls", type=int, default=3000)
    parser.add_argument("--max-seconds", type=int, default=2100)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--hourly-usd", type=float, default=0.461)
    parser.add_argument("--output-dir", default="/opt/ml/processing/output")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    logging.getLogger("boto3").setLevel(logging.ERROR)
    logging.getLogger("botocore").setLevel(logging.ERROR)
    try:
        count = self_test() + shooting_tests()
        emit("SELF_TEST_PASS", tests=count, workload=VERSION)
        if args.self_test:
            return 0
        if not (1 <= args.stats_calls <= 3000 and 30 <= args.max_seconds <= 2100 and 1 <= args.workers <= 4):
            raise ValueError("Shooting continuation exceeds milestone limits")
        args.mode, args.odds_credits, args.until = "stats", 0, None
        args.odds_workers, args.max_response_mb = args.workers, 64
        archive = ShootingContinuation(args)
        emit("START", run_id=archive.run_id, workload=VERSION, max_calls=args.stats_calls,
            maximum_compute_usd=args.max_seconds/3600*args.hourly_usd)
        beat = threading.Thread(target=archive.heartbeat, daemon=True)
        beat.start()
        archive.safe_work("shooting_continuation", archive.work)
        archive.stop.set()
        beat.join(timeout=10)
        return archive.finish()
    except Exception as exc:
        emit("FATAL", error_type=type(exc).__name__)
        return 1


if __name__ == "__main__":
    sys.exit(main())
