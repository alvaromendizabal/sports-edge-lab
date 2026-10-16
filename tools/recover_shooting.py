#!/usr/bin/env python3
"""Recover only CBBD shooting statistics from already archived season rosters.

Deploy with acquire_paid_data.py v002. Never downloads team-season discovery
data: missing cached seasons remain explicitly pending while the base job runs.
"""
import argparse
import logging
import sys
import threading
import unittest

from acquire_paid_data import (Archive, Budget, BudgetStop, blob, digest, emit,
                               identity, shooting_selectors, self_test)

ENDPOINTS = ("/stats/team/shooting/season", "/stats/player/shooting/season")


def cached_stats_key(season, current_season, day):
    vintage = day if season >= current_season else ""
    request = identity("cbbd", "ncaam", "/stats/team/season", {"season": season}, vintage)
    return "tracks/ncaam/raw/cbbd/request-index/" + digest(blob(request)) + ".json"


def recovery_tasks(season, rows, completed):
    return [(endpoint, {"season": season, **selector})
            for selector in shooting_selectors(rows) for endpoint in ENDPOINTS
            if digest(blob({"endpoint": endpoint, "params": {"season": season, **selector}})) not in completed]


class Recovery(Archive):
    def __init__(self, args):
        super().__init__(args)
        self.loaded_seasons = set()
        self.pending_seasons = set(range(2003, 2028))
        self.completed_tasks = set()
        self.season_selectors = {}
        self.phase["shooting_recovery"] = {"status": "running", "planned": 0, "completed": 0}

    def discover_cached(self):
        tasks = []
        current = self.end.year + (self.end.month >= 7)
        for season in sorted(self.pending_seasons, reverse=True):
            key = cached_stats_key(season, current, self.day)
            receipt = self.s3_json(key)
            if receipt is None or receipt.get("status") != 200:
                continue
            rows = self.content(receipt)
            if not isinstance(rows, list):
                self.failure({"cache_key": key}, "invalid_cached_team_statistics")
                continue
            self.loaded_seasons.add(season)
            self.pending_seasons.remove(season)
            self.season_selectors[str(season)] = shooting_selectors(rows)
            tasks.extend(recovery_tasks(season, rows, self.completed_tasks))
        return tasks

    def recover(self, endpoint, params):
        if endpoint not in ENDPOINTS or not (params.get("conference") or params.get("team")):
            raise ValueError("Only filtered shooting-stat requests allowed")
        task_id = digest(blob({"endpoint": endpoint, "params": params}))
        result = self.stats_capture("cbbd", endpoint, params, "cbbd_season" + endpoint)
        with self.lock:
            self.completed_tasks.add(task_id)
            self.stats["shooting_successful_or_cached_requests"] += int(result is not None)
            self.stats["shooting_failed_requests"] += int(result is None)

    def work(self):
        while True:
            self.time_left()
            tasks = self.discover_cached()
            self.phase["shooting_recovery"]["planned"] += len(tasks)
            self.phase["shooting_recovery"]["pending_source_seasons"] = sorted(self.pending_seasons)
            if tasks:
                self.parallel_tasks(tasks, self.recover, "shooting_recovery", self.args.odds_workers)
            if not self.pending_seasons:
                self.phase["shooting_recovery"]["status"] = "available_cached_seasons_processed"
                return
            self.phase["shooting_recovery"]["status"] = "waiting_for_cached_seasons"
            self.stop.wait(10)

    def summary(self):
        result = super().summary()
        result.update({"version": "sports-edge-lab-cbbd-shooting-recovery-v001",
                       "scope": "CBBD team/player season shooting with documented conference/team filters only",
                       "cached_source_seasons": sorted(self.loaded_seasons),
                       "pending_source_seasons": sorted(self.pending_seasons),
                       "season_selectors": self.season_selectors,
                       "paid_discovery_requests": 0,
                       "not_completed_by_this_runner": ["source_seasons_not_yet_cached", "point_in_time_feature_approval"],
                       "official_documentation": ["https://api.collegebasketballdata.com/api/stats"]})
        return result


def recovery_tests():
    class Tests(unittest.TestCase):
        def test_cached_source_identity(self):
            self.assertEqual(cached_stats_key(2026, 2027, "2026-10-16"), cached_stats_key(2026, 2027, "2026-10-17"))
            self.assertNotEqual(cached_stats_key(2027, 2027, "2026-10-16"), cached_stats_key(2027, 2027, "2026-10-17"))

        def test_only_shooting_with_filters_and_no_duplicate_conferences(self):
            rows = [{"conference": "ACC", "team": "Duke"}, {"conference": "ACC", "team": "North Carolina"}]
            tasks = recovery_tasks(2026, rows, set())
            self.assertEqual(len(tasks), 2)
            self.assertTrue(all(x[0] in ENDPOINTS and x[1] == {"season": 2026, "conference": "ACC"} for x in tasks))
            done = {digest(blob({"endpoint": tasks[0][0], "params": tasks[0][1]}))}
            self.assertEqual(len(recovery_tasks(2026, rows, done)), 1)

        def test_zero_odds_budget(self):
            budget = Budget(0, 2)
            with self.assertRaises(BudgetStop):
                budget.reserve("odds")
            budget.reserve("cbbd")
            budget.reserve("cbbd")
            with self.assertRaises(BudgetStop):
                budget.reserve("cbbd")

    result = unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
    if not result.wasSuccessful():
        raise RuntimeError("Recovery self-test gate failed")
    return result.testsRun


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bucket", default="sagemaker-sports-edge-lab-560403859723-us-west-2")
    parser.add_argument("--region", default="us-west-2")
    parser.add_argument("--cfbd-parameter", default="/sports-edge-lab/shared/cfbd/key")
    parser.add_argument("--stats-calls", type=int, default=2000)
    parser.add_argument("--max-seconds", type=int, default=500)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--hourly-usd", type=float, default=0.461)
    parser.add_argument("--output-dir", default="/opt/ml/processing/output")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    logging.getLogger("boto3").setLevel(logging.ERROR)
    logging.getLogger("botocore").setLevel(logging.ERROR)
    try:
        count = self_test() + recovery_tests()
        emit("SELF_TEST_PASS", tests=count, workload="shooting_recovery")
        if args.self_test:
            return 0
        if not (1 <= args.stats_calls <= 2000 and 30 <= args.max_seconds <= 500 and 1 <= args.workers <= 4):
            raise ValueError("Recovery exceeds milestone limits")
        args.mode, args.odds_credits, args.until = "stats", 0, None
        args.odds_workers, args.max_response_mb = args.workers, 64
        archive = Recovery(args)
        emit("START", run_id=archive.run_id, workload="shooting_recovery", max_calls=args.stats_calls)
        beat = threading.Thread(target=archive.heartbeat, daemon=True)
        beat.start()
        archive.safe_work("shooting_recovery", archive.work)
        archive.stop.set()
        beat.join(timeout=10)
        return archive.finish()
    except Exception as exc:
        emit("FATAL", error_type=type(exc).__name__)
        return 1


if __name__ == "__main__":
    sys.exit(main())
