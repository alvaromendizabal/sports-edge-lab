#!/usr/bin/env python3
"""Bounded player-prop archive using event IDs already captured in private S3.

Deploy alongside acquire_paid_data.py. No paid discovery calls are made.
"""
import argparse
import collections
import datetime as dt
import logging
import re
import sys
import threading
import time
import unittest

from acquire_paid_data import (Archive, Budget, BudgetStop, SPORTS, blob, digest,
                               emit, historical_cost, iso, now, parse,
                               round_robin, self_test)

PROP_START = parse("2023-05-03T05:30:00Z")
FOOTBALL = ["player_pass_yds", "player_pass_tds", "player_rush_yds",
            "player_reception_yds", "player_receptions", "player_anytime_td"]
BASKETBALL = ["player_points", "player_rebounds", "player_assists",
              "player_threes", "player_blocks", "player_steals"]
MARKETS = {"nfl": FOOTBALL, "nba": BASKETBALL, "ncaaf": FOOTBALL, "ncaam": BASKETBALL}
HORIZONS = [1440, 360, 15]
DOCS = ["https://the-odds-api.com/sports-odds-data/betting-markets.html",
        "https://the-odds-api.com/liveapi/guides/v4/#get-historical-event-odds"]


def planned_queries(events, end, processed):
    groups = {}
    for track in MARKETS:
        tasks = []
        for event in sorted(events.get(track, {}).values(), key=lambda x: x.get("commence_time", ""), reverse=True):
            if not event.get("id") or not re.fullmatch(r"[A-Za-z0-9_-]+", event["id"]):
                continue
            if not event.get("commence_time"):
                continue
            kickoff = parse(event["commence_time"])
            if not (PROP_START < kickoff <= end):
                continue
            for minutes in HORIZONS:
                target = kickoff - dt.timedelta(minutes=minutes)
                key = (track, event["id"], iso(target))
                if PROP_START <= target <= end and key not in processed:
                    tasks.append((track, event, target, minutes))
        groups[track] = tasks
    return round_robin(groups.values())


def quote_audit(track, event, target, result):
    audit = {"track": track, "event_id": event["id"], "requested_at": iso(target),
             "expected_commence_time": event["commence_time"], "requested_markets": MARKETS[track],
             "usable_for_backtest_without_further_audit": False, "issues": [],
             "outcomes": 0, "markets_returned": [], "bookmakers": 0}
    if not isinstance(result, dict) or not isinstance(result.get("data"), dict):
        audit["issues"].append("missing_event_response")
        return audit
    data = result["data"]
    audit["snapshot_timestamp"] = result.get("timestamp")
    audit["actual_commence_time"] = data.get("commence_time")
    if data.get("id") != event["id"]:
        audit["issues"].append("event_id_mismatch")
    try:
        snapshot = parse(result["timestamp"])
        if snapshot > target:
            audit["issues"].append("snapshot_after_decision")
        audit["snapshot_age_seconds"] = (target - snapshot).total_seconds()
    except (KeyError, TypeError, ValueError, AttributeError):
        snapshot = None
        audit["issues"].append("missing_or_invalid_snapshot_time")
    try:
        actual_start = parse(data["commence_time"])
        if actual_start <= target:
            audit["issues"].append("not_pregame_at_actual_kickoff")
        if actual_start != parse(event["commence_time"]):
            audit["issues"].append("kickoff_revision")
    except (KeyError, TypeError, ValueError, AttributeError):
        audit["issues"].append("missing_or_invalid_kickoff")
    markets = set()
    for book in data.get("bookmakers", []):
        audit["bookmakers"] += 1
        for market in book.get("markets", []):
            markets.add(market.get("key", ""))
            audit["outcomes"] += len(market.get("outcomes", []))
            try:
                updated = parse(market.get("last_update", book.get("last_update")))
                if updated > target or (snapshot and updated > snapshot):
                    audit["issues"].append("quote_update_after_cutoff")
            except (TypeError, ValueError, AttributeError):
                audit["issues"].append("missing_or_invalid_quote_time")
    audit["markets_returned"] = sorted(markets)
    audit["issues"] = sorted(set(audit["issues"]))
    audit["nonempty_snapshot_with_consistent_recorded_times"] = bool(audit["outcomes"] and not audit["issues"])
    # Settlement data, participant mapping, availability, and schedule provenance
    # still require an independent audit even when these timestamp checks pass.
    return audit


class PropsArchive(Archive):
    def __init__(self, args):
        super().__init__(args)
        self.source_key = args.source_events_key
        self.source_progress_key = self.source_key.replace("/discovered-events.json", "/progress.json")
        self.source_census_complete = False
        self.source_loaded_at = None
        self.processed = set()
        self.audits = collections.Counter()
        self.blocked_statuses = {403}
        self.phase["player_props"] = {"status": "running", "completed": 0, "planned": 0}

    def refresh_events(self):
        rows = self.s3_json(self.source_key)
        progress = self.s3_json(self.source_progress_key)
        if rows is None:
            self.count(source_snapshot_not_ready=1)
            return
        with self.lock:
            for track in MARKETS:
                for event in rows.get(track, []):
                    if event.get("id") and event.get("commence_time"):
                        old = self.events[track].get(event["id"])
                        if old is None or event.get("seen_at_snapshot", "") >= old.get("seen_at_snapshot", ""):
                            self.events[track][event["id"]] = event
            self.source_loaded_at = iso(now())
        if progress:
            phase = progress.get("phases", {}).get("odds_daily_census", {})
            self.source_census_complete = phase.get("status") == "planned_requests_processed"
            if phase.get("status") in ("failed", "bounded_stop"):
                self.source_census_complete = True
            if progress.get("phases", {}).get("odds", {}).get("status") in ("failed", "bounded_stop"):
                self.source_census_complete = True
        self.count(source_snapshot_refreshes=1)

    def capture_prop(self, track, event, target, minutes):
        key = (track, event["id"], iso(target))
        with self.lock:
            if key in self.processed:
                return
            self.processed.add(key)
        endpoint = "/v4/historical/sports/" + SPORTS[track][0] + "/events/" + event["id"] + "/odds"
        result = self.capture("odds", track, endpoint,
                              {"date": iso(target), "regions": "us", "markets": ",".join(MARKETS[track]),
                               "oddsFormat": "decimal", "dateFormat": "iso"}, "player_props_" + str(minutes) + "min")
        audit = quote_audit(track, event, target, result)
        audit["horizon_minutes"] = minutes
        audit["source_events_key"] = self.source_key
        audit["run_id"] = self.run_id
        aid = digest(blob({"track": track, "event_id": event["id"], "target": iso(target)}))
        self.save_json("tracks/" + track + "/audits/player-props/" + self.run_id + "/" + aid + ".json", audit)
        with self.lock:
            self.audits.update({"requests_audited": 1, "outcomes_captured": audit["outcomes"],
                                "nonempty_responses": int(audit["outcomes"] > 0),
                                "time_consistent_nonempty_responses": int(audit.get("nonempty_snapshot_with_consistent_recorded_times", False)),
                                track + "_requests_audited": 1, track + "_outcomes": audit["outcomes"]})
            for issue in audit["issues"]:
                self.audits["issue_" + issue] += 1

    def work(self):
        while True:
            self.time_left()
            self.refresh_events()
            with self.lock:
                events = {track: dict(rows) for track, rows in self.events.items()}
                processed = set(self.processed)
            tasks = list(planned_queries(events, self.end, processed))
            self.phase["player_props"]["currently_pending"] = len(tasks)
            self.phase["player_props"]["planned"] = len(processed) + len(tasks)
            if not tasks:
                if self.source_census_complete:
                    self.phase["player_props"]["status"] = "available_archive_events_processed"
                    return
                self.phase["player_props"]["status"] = "waiting_for_source_census"
                self.stop.wait(min(15, max(0, self.deadline - time.monotonic())))
                continue
            self.phase["player_props"]["status"] = "running"
            # Refresh the growing source archive between bounded batches so all
            # leagues enter the queue as soon as their seasons are discovered.
            self.parallel_tasks(tasks[:96], self.capture_prop, "player_props", self.args.odds_workers)
            self.phase["player_props"]["status"] = "running"

    def summary(self):
        summary = super().summary()
        with self.lock:
            audits = dict(self.audits)
        summary.update({"version": "sports-edge-lab-props-v001", "source_events_key": self.source_key,
                        "source_events_last_loaded": self.source_loaded_at,
                        "source_daily_census_complete": self.source_census_complete,
                        "paid_discovery_requests": 0, "prop_audits": audits,
                        "scope": "Historical US-bookmaker player props for NFL/NBA/NCAAF/NCAAM using archived event IDs",
                        "markets": MARKETS, "horizons_minutes": HORIZONS,
                        "earliest_possible_snapshot": iso(PROP_START),
                        "not_completed_by_this_runner": ["all_event_coverage", "all_player_prop_market_types", "NCAA_women_player_props", "prop_settlement_mapping", "point_in_time_feature_approval", "proven_market_advantage"],
                        "official_documentation": DOCS})
        return summary


def props_tests():
    class Tests(unittest.TestCase):
        def test_four_sports_and_correct_reservation(self):
            self.assertEqual(set(MARKETS), {"nfl", "nba", "ncaaf", "ncaam"})
            self.assertTrue(all(historical_cost({"markets": ",".join(x), "regions": "us"}) == 60 for x in MARKETS.values()))
            budget = Budget(120, 0)
            budget.finish("odds", budget.reserve("odds", 60), {"x-requests-last": "20"})
            budget.reserve("odds", 60)
            with self.assertRaises(BudgetStop):
                budget.reserve("odds", 60)

        def test_boundary_future_dedup_and_sport_interleave(self):
            events = {"nfl": {"one": {"id": "one", "commence_time": "2025-01-01T20:00:00Z"},
                              "future": {"id": "future", "commence_time": "2027-01-01T20:00:00Z"}},
                      "nba": {"two": {"id": "two", "commence_time": "2025-01-01T20:00:00Z"}},
                      "ncaam": {"old": {"id": "old", "commence_time": "2023-05-01T00:00:00Z"}}}
            planned = list(planned_queries(events, parse("2026-01-01T00:00:00Z"), {("nfl", "one", "2024-12-31T20:00:00Z")}))
            self.assertEqual(len(planned), 5)
            self.assertEqual([x[0] for x in planned[:4]], ["nfl", "nba", "nfl", "nba"])
            self.assertTrue(all(x[1]["id"] in {"one", "two"} for x in planned))

        def test_future_quote_quarantined(self):
            event = {"id": "one", "commence_time": "2025-01-01T20:00:00Z"}
            result = {"timestamp": "2025-01-01T19:45:00Z", "data": {**event, "bookmakers": [{"markets": [{"key": "player_points", "last_update": "2025-01-01T19:46:00Z", "outcomes": [{"price": 1.9}]}]}]}}
            audit = quote_audit("nba", event, parse("2025-01-01T19:45:00Z"), result)
            self.assertIn("quote_update_after_cutoff", audit["issues"])
            self.assertFalse(audit["nonempty_snapshot_with_consistent_recorded_times"])

        def test_consistent_response_and_rescheduled_event(self):
            event = {"id": "one", "commence_time": "2025-01-01T20:00:00Z"}
            result = {"timestamp": "2025-01-01T19:45:00Z", "data": {**event, "bookmakers": [{"markets": [{"key": "player_points", "last_update": "2025-01-01T19:44:00Z", "outcomes": [{"price": 1.9}]}]}]}}
            audit = quote_audit("nba", event, parse("2025-01-01T19:45:00Z"), result)
            self.assertTrue(audit["nonempty_snapshot_with_consistent_recorded_times"])
            self.assertFalse(audit["usable_for_backtest_without_further_audit"])
            result["data"]["commence_time"] = "2025-01-01T19:00:00Z"
            audit = quote_audit("nba", event, parse("2025-01-01T19:45:00Z"), result)
            self.assertIn("kickoff_revision", audit["issues"])
            self.assertIn("not_pregame_at_actual_kickoff", audit["issues"])

    result = unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
    if not result.wasSuccessful():
        raise RuntimeError("Player prop self-test gate failed")
    return result.testsRun


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bucket", default="sagemaker-sports-edge-lab-560403859723-us-west-2")
    parser.add_argument("--region", default="us-west-2")
    parser.add_argument("--source-events-key")
    parser.add_argument("--odds-parameter", default="/sports-edge-lab/shared/the-odds-api/key")
    parser.add_argument("--odds-credits", type=int, default=500000)
    parser.add_argument("--max-seconds", type=int, default=6900)
    parser.add_argument("--odds-workers", type=int, default=4)
    parser.add_argument("--max-response-mb", type=int, default=64)
    parser.add_argument("--hourly-usd", type=float, default=0.461)
    parser.add_argument("--output-dir", default="/opt/ml/processing/output")
    parser.add_argument("--until")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    logging.getLogger("boto3").setLevel(logging.ERROR)
    logging.getLogger("botocore").setLevel(logging.ERROR)
    try:
        count = self_test() + props_tests()
        emit("SELF_TEST_PASS", tests=count, workload="player_props")
        if args.self_test:
            return 0
        if not args.source_events_key or not re.fullmatch(r"shared/acquisition/paid/[A-Za-z0-9_-]+/discovered-events\.json", args.source_events_key):
            raise ValueError("An existing paid archive event census key is required")
        if not (60 <= args.odds_credits <= 500000 and 30 <= args.max_seconds <= 7000 and 1 <= args.odds_workers <= 6):
            raise ValueError("Requested bounds exceed player-prop milestone limits")
        args.mode, args.stats_calls = "odds", 0
        archive = PropsArchive(args)
        emit("START", run_id=archive.run_id, workload="player_props", source_events_key=args.source_events_key,
             max_credits=args.odds_credits, paid_discovery_requests=0)
        beat = threading.Thread(target=archive.heartbeat, daemon=True)
        beat.start()
        archive.safe_work("player_props", archive.work)
        archive.stop.set()
        beat.join(timeout=10)
        return archive.finish()
    except Exception as exc:
        emit("FATAL", error_type=type(exc).__name__)
        return 1


if __name__ == "__main__":
    sys.exit(main())
