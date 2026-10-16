"""Gap-first, bounded Sports Edge Lab continuation. AWS execution only."""
import argparse
import collections
import concurrent.futures
import datetime as dt
import logging
import sys
import threading
import unittest

from acquire_paid_data import (Archive, BudgetStop, SPORTS, blob, digest, emit,
                               identity, iso, parse, round_robin, self_test)

VERSION = "sports-edge-lab-continuation-v011"
SOURCE_RUNS = ["20261016T003943Z-742acb6443", "20261016T004910Z-fa9211a177",
               "20261016T005814Z-dc2ec3e9a5"]
SOURCE_EVENTS = "shared/acquisition/paid/" + SOURCE_RUNS[0] + "/discovered-events.json"


def request_id(provider, track, endpoint, params, vintage=""):
    return digest(blob(identity(provider, track, endpoint, params, vintage)))


def immutable_missing(record, cutoff):
    req = record.get("request", {})
    date = req.get("params", {}).get("date")
    return bool(record.get("status") == 404 and req.get("provider") == "odds"
                and "/events/" in req.get("endpoint", "") and date
                and parse(date) < cutoff)


class Continuation(Archive):
    def __init__(self, args):
        super().__init__(args)
        self.blocked_statuses = set()
        self.negative = set()
        self.source_receipts = []
        self.source_until = None
        self.seed_counts = collections.Counter()
        self.phase["seed"] = {"status": "running"}

    def failure(self, descriptor, reason, **other):
        # An access denial stops the provider, including all event-path variants.
        if other.get("status") == 403 and descriptor.get("provider"):
            self.budget.disable(descriptor["provider"])
        if immutable_missing({"request": descriptor, **other}, self.end - dt.timedelta(days=7)):
            self.negative.add(digest(blob(descriptor)))
        return super().failure(descriptor, reason, **other)

    def capture(self, provider, track, endpoint, params, label, vintage="", need_data=True):
        rid = request_id(provider, track, endpoint, params, vintage)
        if rid in self.negative:
            self.count(negative_cache_reused=1)
            return None
        return super().capture(provider, track, endpoint, params, label, vintage, need_data)

    def seed(self):
        cutoff = self.end - dt.timedelta(days=7)
        for run in self.args.source_runs:
            self.time_left()
            prefix = "shared/acquisition/paid/" + run
            summary = self.s3_json(prefix + "/summary.json")
            receipts = self.s3_json(prefix + "/receipts.json")
            failures = self.s3_json(prefix + "/failures.json")
            if not summary or not isinstance(receipts, list) or not isinstance(failures, list):
                raise RuntimeError("Required source run receipts unavailable")
            if run == self.args.source_runs[0]:
                self.source_until = parse(summary["until"])
            for receipt in receipts:
                if receipt.get("status") == 200:
                    self.cache[receipt["request_id"]] = receipt
                    self.source_receipts.append(receipt)
            for failure in failures:
                if immutable_missing(failure, cutoff):
                    self.negative.add(digest(blob(failure["request"])))
            self.seed_counts["source_runs"] += 1
        events = self.s3_json(self.args.source_events_key)
        if not isinstance(events, dict):
            raise RuntimeError("Required source event cache unavailable")
        for track in SPORTS:
            for row in events.get(track, []):
                if row.get("id") and row.get("commence_time"):
                    self.events[track][row["id"]] = row
        self.seed_counts.update(successful_request_ids=len(self.cache),
                                permanent_request_404s=len(self.negative))
        self.phase["seed"] = {"status": "completed", **dict(self.seed_counts)}
        self.checkpoint()

    def missing(self, provider, track, endpoint, params, vintage=""):
        rid = request_id(provider, track, endpoint, params, vintage)
        return rid not in self.cache and rid not in self.negative

    def play_vintage(self, day):
        # Match the original collector exactly: recent daily observations use
        # today's vintage; settled historical dates have a stable identity.
        return "" if day < (self.end - dt.timedelta(days=7)).date().isoformat() else self.day

    def game_checkpoint(self, track, target, label):
        return self.capture("odds", track, "/v4/historical/sports/" + SPORTS[track][0] + "/odds",
                            {"date": iso(target), "markets": "h2h,spreads,totals", "regions": "us",
                             "oddsFormat": "decimal", "dateFormat": "iso"}, label, need_data=False)

    def process(self, tasks, fn, phase, workers):
        self.phase[phase] = {"planned_missing_requests": len(tasks), "processed": 0,
                             "successful_or_reused": 0, "negative_responses": 0, "status": "running"}
        def one(*item):
            value = fn(*item)
            with self.lock:
                self.phase[phase]["processed"] += 1
                self.phase[phase]["successful_or_reused" if value is not None else "negative_responses"] += 1
            return value
        # Base parallel scheduler also records completed; it means processed,
        # not success. Explicit success and negative counters above are authoritative.
        self.phase[phase]["completed"] = 0
        try:
            self.parallel_tasks(tasks, one, phase, workers)
        except BudgetStop as exc:
            self.phase[phase].update(status="bounded_stop", reason=str(exc))
            raise

    def odds_gap_work(self):
        # Only new census days; never reread the completed 9,811-day archive.
        cursor = self.source_until.replace(hour=12, minute=0, second=0, microsecond=0)
        if cursor <= self.source_until:
            cursor += dt.timedelta(days=1)
        fresh = 0
        while cursor <= self.end:
            for track in SPORTS:
                self.odds(track, cursor, "odds_new_daily_census")
                fresh += 1
            cursor += dt.timedelta(days=1)
        self.phase["new_daily_census"] = {"requests_processed": fresh, "status": "completed"}
        self.checkpoint()
        groups = {}
        for track, events in self.events.items():
            first = parse(SPORTS[track][1] + "T00:00:00Z")
            targets = set()
            for row in events.values():
                kickoff = parse(row["commence_time"])
                for minutes in (15, 360, 1440, 4320):
                    target = kickoff - dt.timedelta(minutes=minutes)
                    if first <= target <= self.end:
                        targets.add(target)
            endpoint = "/v4/historical/sports/" + SPORTS[track][0] + "/odds"
            tasks = []
            for target in sorted(targets, reverse=True):
                params = {"date": iso(target), "markets": "h2h,spreads,totals", "regions": "us",
                          "oddsFormat": "decimal", "dateFormat": "iso"}
                if self.missing("odds", track, endpoint, params):
                    tasks.append((track, target, "odds_event_derived_checkpoint"))
            groups[track] = tasks
        self.seed_counts["odds_missing_checkpoints"] = sum(map(len, groups.values()))
        self.phase["odds_missing_by_track"] = {k: len(v) for k, v in groups.items()}
        self.process(list(round_robin(groups.values())), self.game_checkpoint, "odds_gap_checkpoints", self.args.odds_workers)

    def cbbd_gap_work(self):
        # Derive dates/game IDs exclusively from already captured game rows.
        games = [r for r in self.source_receipts if r.get("request", {}).get("provider") == "cbbd"
                 and r["request"].get("endpoint") == "/games"]
        dates, ids = set(), set()
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            for receipt, rows in zip(games, pool.map(self.content, games)):
                self.time_left()
                season = receipt["request"]["params"].get("season")
                if not isinstance(rows, list) or not isinstance(season, int):
                    continue
                for row in rows:
                    if not row.get("startDate"):
                        continue
                    when = parse(row["startDate"])
                    if when > self.end:
                        continue
                    if season == 2003 or season >= 2006:
                        dates.add(when.date().isoformat())
                    if season >= 2024 and row.get("id"):
                        ids.add((season, str(row["id"])))
        plays, lineups, substitutions = [], [], []
        for day in sorted(dates, reverse=True):
            params = {"date": day}
            vintage = self.play_vintage(day)
            if self.missing("cbbd", "ncaam", "/plays/date", params, vintage):
                plays.append(("/plays/date", params, "cbbd_daily_plays", vintage))
        for season, game_id in sorted(ids, reverse=True):
            for path, target in (("/lineups/game/", lineups), ("/substitutions/game/", substitutions)):
                endpoint = path + game_id
                if self.missing("cbbd", "ncaam", endpoint, {}):
                    target.append((endpoint, {}, "cbbd_lineups_substitutions", ""))
        self.phase["cbbd_gap_inventory"] = {"cached_game_requests": len(games), "known_play_dates": len(dates),
             "missing_play_dates": len(plays), "eligible_game_ids": len(ids),
             "missing_lineups": len(lineups), "missing_substitutions": len(substitutions)}
        def capture(endpoint, params, label, vintage):
            return self.capture("cbbd", "ncaam", endpoint, params, label, vintage, need_data=False)
        # Interleave detailed-game work with daily plays to give both scope types
        # a share of the bounded call budget; shooting and CFBD are excluded.
        self.process(list(round_robin([plays, lineups, substitutions])), capture, "cbbd_gaps", self.args.stats_workers)

    def summary(self):
        summary = super().summary()
        summary.update(version=VERSION, seed_counts=dict(self.seed_counts),
            source_runs=self.args.source_runs, source_events_key=self.args.source_events_key,
            scope="Missing five-sport game odds checkpoints plus CBBD daily plays and 2024+ lineups/substitutions",
            not_completed_by_this_runner=["player_prop_continuation", "shooting_continuation", "portal_filter_audit",
                "point_in_time_feature_approval", "full_source_coverage", "forecast_training"],
            dedup_policy="Exact successful request identities; exact historical event 404 identities; private immutable raw captures")
        return summary


def continuation_tests():
    class Checks(unittest.TestCase):
        def test_negative_scope(self):
            descriptor = identity("odds", "nba", "/v4/historical/sports/basketball_nba/events/a/odds", {"date": "2025-01-01T12:00:00Z"})
            self.assertTrue(immutable_missing({"request": descriptor, "status": 404}, parse("2026-01-01T00:00:00Z")))
            self.assertFalse(immutable_missing({"request": descriptor, "status": 403}, parse("2026-01-01T00:00:00Z")))
            self.assertFalse(immutable_missing({"request": descriptor, "status": 404}, parse("2024-01-01T00:00:00Z")))
        def test_exact_identity_cache(self):
            a = Continuation.__new__(Continuation)
            a.cache = {request_id("cbbd", "ncaam", "/plays/date", {"date": "2025-01-01"}): {"status": 200}}
            a.negative = set()
            self.assertFalse(a.missing("cbbd", "ncaam", "/plays/date", {"date": "2025-01-01"}))
            self.assertTrue(a.missing("cbbd", "ncaam", "/plays/date", {"date": "2025-01-02"}))
        def test_missing_does_not_collapse_event_dates(self):
            p = "/v4/historical/sports/basketball_nba/events/a/odds"
            self.assertNotEqual(request_id("odds", "nba", p, {"date": "2025-01-01T12:00:00Z"}),
                                request_id("odds", "nba", p, {"date": "2025-01-01T18:00:00Z"}))
        def test_recent_play_vintage_matches_original(self):
            a = Continuation.__new__(Continuation)
            a.end, a.day = parse("2026-10-16T18:00:00Z"), "2026-10-16"
            self.assertEqual(a.play_vintage("2026-10-15"), "2026-10-16")
            self.assertEqual(a.play_vintage("2026-10-09"), "2026-10-16")
            self.assertEqual(a.play_vintage("2026-10-08"), "")
        def test_403_disables_provider(self):
            from acquire_paid_data import Budget
            a = Continuation.__new__(Continuation)
            a.budget, a.lock, a.failures, a.negative = Budget(100, 10), threading.Lock(), [], set()
            a.end = parse("2026-01-01T00:00:00Z")
            a.failure(identity("odds", "nba", "/events/a", {}), "blocked", status=403)
            with self.assertRaises(BudgetStop):
                a.budget.reserve("odds", 30)
            a.budget.reserve("cbbd", 1)
    result = unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.loadTestsFromTestCase(Checks))
    if not result.wasSuccessful():
        raise RuntimeError("Continuation test gate failed")
    return result.testsRun


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bucket", default="sagemaker-sports-edge-lab-560403859723-us-west-2")
    parser.add_argument("--region", default="us-west-2")
    parser.add_argument("--source-runs", nargs="+", default=SOURCE_RUNS)
    parser.add_argument("--source-events-key", default=SOURCE_EVENTS)
    parser.add_argument("--odds-parameter", default="/sports-edge-lab/shared/the-odds-api/key")
    parser.add_argument("--cfbd-parameter", default="/sports-edge-lab/shared/cfbd/key")
    parser.add_argument("--odds-credits", type=int, default=1600000)
    parser.add_argument("--stats-calls", type=int, default=30000)
    parser.add_argument("--max-seconds", type=int, default=14100)
    parser.add_argument("--odds-workers", type=int, default=4)
    parser.add_argument("--stats-workers", type=int, default=4)
    parser.add_argument("--max-response-mb", type=int, default=256)
    parser.add_argument("--hourly-usd", type=float, default=0.461)
    parser.add_argument("--output-dir", default="/opt/ml/processing/output")
    parser.add_argument("--until")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    args.mode = "all"
    logging.getLogger("boto3").setLevel(logging.ERROR)
    logging.getLogger("botocore").setLevel(logging.ERROR)
    try:
        tests = self_test() + continuation_tests()
        emit("SELF_TEST_PASS", tests=tests)
        if args.self_test:
            return 0
        if not (0 <= args.odds_credits <= 1600000 and 0 <= args.stats_calls <= 30000
                and 30 <= args.max_seconds <= 14100 and 1 <= args.odds_workers <= 4
                and 1 <= args.stats_workers <= 4):
            raise ValueError("Continuation bounds exceeded")
        archive = Continuation(args)
        beat = threading.Thread(target=archive.heartbeat, daemon=True)
        beat.start()
        archive.safe_work("seed", archive.seed)
        if archive.phase["seed"]["status"] == "completed":
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
                futures = [pool.submit(archive.safe_work, "odds", archive.odds_gap_work),
                           pool.submit(archive.safe_work, "cbbd", archive.cbbd_gap_work)]
                for future in futures:
                    future.result()
        archive.stop.set()
        beat.join(timeout=10)
        return archive.finish()
    except Exception as exc:
        emit("FATAL", error_type=type(exc).__name__)
        return 1


if __name__ == "__main__":
    sys.exit(main())
