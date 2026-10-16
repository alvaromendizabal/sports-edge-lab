"""Cache-aware, bounded player-prop acquisition. Execute on AWS only."""
import argparse
import collections
import concurrent.futures
import datetime as dt
import logging
import math
import re
import sys
import threading
import time
import unittest
import zipfile
from pathlib import Path

from acquire_paid_data import (Archive, Budget, BudgetStop, SPORTS, blob, digest,
                               emit, historical_cost, identity, iso, now, parse,
                               round_robin, self_test)

VERSION = "sports-edge-lab-props-continuation-v014"
SOURCE_RUNS = ["20261016T003943Z-742acb6443", "20261016T004910Z-fa9211a177"]
SOURCE_EVENTS = "shared/acquisition/paid/" + SOURCE_RUNS[0] + "/discovered-events.json"
EXTRA_EVENTS = "shared/acquisition/paid/20261016T182005Z-1999205e92/discovered-events.json"
PROP_START = parse("2023-05-03T05:30:00Z")
FOOTBALL = ["player_pass_yds", "player_pass_tds", "player_rush_yds",
            "player_reception_yds", "player_receptions", "player_anytime_td"]
BASKETBALL = ["player_points", "player_rebounds", "player_assists",
              "player_threes", "player_blocks", "player_steals"]
MARKETS = {"nfl": FOOTBALL, "nba": BASKETBALL, "ncaaf": FOOTBALL, "ncaam": BASKETBALL}
HORIZONS = [1440, 360, 15]


def request_for(track, event, target):
    endpoint = "/v4/historical/sports/" + SPORTS[track][0] + "/events/" + event["id"] + "/odds"
    params = {"date": iso(target), "regions": "us", "markets": ",".join(MARKETS[track]),
              "oddsFormat": "decimal", "dateFormat": "iso"}
    descriptor = identity("odds", track, endpoint, params)
    return digest(blob(descriptor)), descriptor


def immutable_missing(record, cutoff):
    req = record.get("request", {})
    date = req.get("params", {}).get("date")
    try:
        return bool(record.get("status") == 404 and req.get("provider") == "odds"
                    and "/events/" in req.get("endpoint", "") and date and parse(date) < cutoff)
    except (TypeError, ValueError, AttributeError):
        return False


def planned_queries(events, end, excluded):
    groups = {}
    for track in MARKETS:
        tasks = []
        for event in sorted(events.get(track, {}).values(), key=lambda x: x.get("commence_time", ""), reverse=True):
            if not event.get("id") or not re.fullmatch(r"[A-Za-z0-9_-]+", event["id"]):
                continue
            try:
                kickoff = parse(event["commence_time"])
            except (KeyError, TypeError, ValueError, AttributeError):
                continue
            if not (PROP_START < kickoff <= end):
                continue
            for minutes in HORIZONS:
                target = kickoff - dt.timedelta(minutes=minutes)
                rid, _ = request_for(track, event, target)
                if PROP_START <= target <= end and rid not in excluded:
                    tasks.append((track, event, target, minutes))
        groups[track] = tasks
    return round_robin(groups.values())


def finite_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def quote_audit(track, event, target, result):
    """Keep market-local errors local, and index passing quotes in the raw object.

    Recorded time checks are necessary, not sufficient, for a usable historical
    quote. Participant resolution, availability, settlement and schedule-vintage
    checks remain external gates. Kickoff revisions are never silently erased.
    """
    audit = {"schema_version": 2, "track": track, "event_id": event["id"],
             "requested_at": iso(target), "expected_commence_time": event["commence_time"],
             "feature_approved": False, "event_issues": [], "warnings": [], "markets": [],
             "outcomes": 0, "quote_recorded_time_pass": 0, "quote_structure_and_time_pass": 0,
             "markets_recorded_time_pass": 0, "markets_with_passing_quotes": 0}
    if not isinstance(result, dict) or not isinstance(result.get("data"), dict):
        audit["event_issues"].append("missing_event_response")
        return audit
    data = result["data"]
    audit["snapshot_timestamp"] = result.get("timestamp")
    audit["actual_commence_time"] = data.get("commence_time")
    if data.get("id") != event["id"]:
        audit["event_issues"].append("event_id_mismatch")
    try:
        snapshot = parse(result["timestamp"])
        if snapshot > target:
            audit["event_issues"].append("snapshot_after_decision")
        audit["snapshot_age_seconds"] = (target - snapshot).total_seconds()
    except (KeyError, TypeError, ValueError, AttributeError):
        snapshot = None
        audit["event_issues"].append("missing_or_invalid_snapshot_time")
    try:
        actual_start = parse(data["commence_time"])
        if actual_start <= target:
            audit["event_issues"].append("not_pregame_at_actual_kickoff")
        if actual_start != parse(event["commence_time"]):
            audit["warnings"].append("kickoff_revision_requires_schedule_provenance")
        audit["actual_horizon_minutes"] = (actual_start - target).total_seconds() / 60
    except (KeyError, TypeError, ValueError, AttributeError):
        audit["event_issues"].append("missing_or_invalid_kickoff")
    books = data.get("bookmakers", [])
    if not isinstance(books, list):
        audit["event_issues"].append("invalid_bookmakers_schema")
        return audit
    for bi, book in enumerate(books):
        if not isinstance(book, dict) or not isinstance(book.get("markets", []), list):
            audit["warnings"].append("invalid_bookmaker_or_markets_schema")
            continue
        for mi, market in enumerate(book.get("markets", [])):
            if not isinstance(market, dict):
                audit["warnings"].append("invalid_market_schema")
                continue
            issues = []
            stamp = market.get("last_update", book.get("last_update"))
            try:
                updated = parse(stamp)
                if updated > target or (snapshot is not None and updated > snapshot):
                    issues.append("quote_update_after_cutoff")
            except (TypeError, ValueError, AttributeError):
                issues.append("missing_or_invalid_quote_time")
            time_pass = not audit["event_issues"] and not issues
            market_key = market.get("key")
            if market_key not in MARKETS[track]:
                issues.append("unrequested_market")
            outcomes = market.get("outcomes", [])
            if not isinstance(outcomes, list):
                outcomes = []
                issues.append("invalid_outcomes_schema")
            passing, rejected = [], []
            for oi, outcome in enumerate(outcomes):
                errors = []
                if not isinstance(outcome, dict):
                    errors.append("invalid_outcome_schema")
                else:
                    if not finite_number(outcome.get("price")) or outcome["price"] <= 1:
                        errors.append("invalid_decimal_price")
                    if not isinstance(outcome.get("description"), str) or not outcome["description"].strip():
                        errors.append("missing_participant_name")
                    if not isinstance(outcome.get("name"), str) or not outcome["name"].strip():
                        errors.append("missing_outcome_label")
                    if market_key != "player_anytime_td" and not finite_number(outcome.get("point")):
                        errors.append("missing_or_invalid_line")
                if time_pass and not issues and not errors:
                    passing.append(oi)
                elif errors:
                    rejected.append({"outcome_index": oi, "issues": errors})
            row = {"bookmaker_index": bi, "bookmaker": book.get("key"), "market_index": mi,
                   "market": market_key, "last_update": stamp, "issues": issues,
                   "recorded_time_gate_pass": time_pass, "outcomes": len(outcomes),
                   "structure_and_time_passing_outcome_indices": passing,
                   "structurally_rejected_outcomes": rejected, "feature_approved": False}
            audit["markets"].append(row)
            audit["outcomes"] += len(outcomes)
            audit["quote_recorded_time_pass"] += len(outcomes) if time_pass else 0
            audit["quote_structure_and_time_pass"] += len(passing)
            audit["markets_recorded_time_pass"] += int(time_pass)
            audit["markets_with_passing_quotes"] += int(bool(passing))
    audit["warnings"] = sorted(set(audit["warnings"]))
    return audit


class PropsContinuation(Archive):
    def __init__(self, args):
        super().__init__(args)
        self.blocked_statuses = set()
        self.negative = set()
        self.attempted = set()
        self.seed_counts = collections.Counter()
        self.audit_counts = collections.Counter()
        self.source_events_loaded = []
        self.last_source_refresh = 0
        self.phase["seed"] = {"status": "running"}

    def failure(self, descriptor, reason, **other):
        if other.get("status") == 403 and descriptor.get("provider"):
            self.budget.disable(descriptor["provider"])
        if immutable_missing({"request": descriptor, **other}, self.end - dt.timedelta(days=7)):
            with self.lock:
                self.negative.add(digest(blob(descriptor)))
        return super().failure(descriptor, reason, **other)

    def refresh_events(self, force=False):
        if not force and time.monotonic() - self.last_source_refresh < 300:
            return
        for index, key in enumerate(self.args.source_events_keys):
            rows = self.s3_json(key)
            if not isinstance(rows, dict):
                if index == 0:
                    raise RuntimeError("Required source event cache unavailable")
                self.count(optional_source_unavailable=1)
                continue
            with self.lock:
                for track in MARKETS:
                    for event in rows.get(track, []):
                        if not isinstance(event, dict) or not event.get("id") or not event.get("commence_time"):
                            continue
                        old = self.events[track].get(event["id"])
                        if old is None or (event.get("seen_at_snapshot") or "") >= (old.get("seen_at_snapshot") or ""):
                            self.events[track][event["id"]] = event
                if key not in self.source_events_loaded:
                    self.source_events_loaded.append(key)
            self.count(source_event_snapshots_loaded=1)
        self.last_source_refresh = time.monotonic()

    def seed(self):
        for run in self.args.source_runs:
            self.time_left()
            prefix = "shared/acquisition/paid/" + run
            summary = self.s3_json(prefix + "/summary.json")
            receipts = self.s3_json(prefix + "/receipts.json")
            failures = self.s3_json(prefix + "/failures.json")
            if not summary or not isinstance(receipts, list) or not isinstance(failures, list):
                raise RuntimeError("Required source run receipts unavailable")
            for receipt in receipts:
                if receipt.get("status") == 200:
                    rid = digest(blob(receipt["request"]))
                    if rid != receipt["request_id"]:
                        raise RuntimeError("Source receipt identity mismatch")
                    self.cache[rid] = receipt
            for failure in failures:
                if immutable_missing(failure, self.end - dt.timedelta(days=7)):
                    self.negative.add(digest(blob(failure["request"])))
            self.seed_counts["source_runs"] += 1
        self.refresh_events(force=True)
        self.seed_counts.update(successful_request_ids=len(self.cache), permanent_request_404s=len(self.negative))
        self.phase["seed"] = {"status": "completed", **dict(self.seed_counts)}
        self.checkpoint()

    def capture_prop(self, track, event, target, minutes):
        rid, descriptor = request_for(track, event, target)
        with self.lock:
            if rid in self.cache or rid in self.negative or rid in self.attempted:
                self.stats["already_completed_or_negative_skipped"] += 1
                return
            self.attempted.add(rid)
        result = self.capture("odds", track, descriptor["endpoint"], descriptor["params"], "player_props_" + str(minutes) + "min")
        if result is None:
            return
        audit = quote_audit(track, event, target, result)
        audit.update(horizon_minutes=minutes, run_id=self.run_id, request_id=rid,
                     source_events_keys=self.source_events_loaded,
                     raw_key=self.cache[rid]["raw_key"], raw_sha256=self.cache[rid]["sha256"])
        self.save_json("tracks/" + track + "/audits/player-props/" + self.run_id + "/" + rid + ".json", audit)
        with self.lock:
            self.audit_counts.update({"responses_audited": 1, "outcomes": audit["outcomes"],
                                      "quote_recorded_time_pass": audit["quote_recorded_time_pass"],
                                      "quote_structure_and_time_pass": audit["quote_structure_and_time_pass"],
                                      "markets_recorded_time_pass": audit["markets_recorded_time_pass"],
                                      "markets_with_passing_quotes": audit["markets_with_passing_quotes"],
                                      track + "_responses_audited": 1})
            for issue in audit["event_issues"] + audit["warnings"]:
                self.audit_counts["event_" + issue] += 1
            for row in audit["markets"]:
                for issue in row["issues"]:
                    self.audit_counts["market_" + issue] += 1

    def work(self):
        self.phase["player_props"] = {"status": "running", "completed": 0, "initial_missing": None}
        while True:
            self.time_left()
            self.refresh_events()
            with self.lock:
                events = {track: dict(rows) for track, rows in self.events.items()}
                excluded = set(self.cache) | self.negative | self.attempted
            tasks = list(planned_queries(events, self.end, excluded))
            phase = self.phase["player_props"]
            if phase["initial_missing"] is None:
                phase["initial_missing"] = len(tasks)
            phase["currently_pending"] = len(tasks)
            phase["pending_by_track"] = dict(collections.Counter(x[0] for x in tasks))
            phase["planned"] = phase["completed"] + len(tasks)
            if not tasks:
                phase["status"] = "available_archive_requests_processed"
                return
            phase["status"] = "running"
            self.parallel_tasks(tasks[:96], self.capture_prop, "player_props", self.args.odds_workers)
            phase["status"] = "running"

    def summary(self):
        summary = super().summary()
        with self.lock:
            audit_counts = dict(self.audit_counts)
        summary.update(version=VERSION, source_runs=self.args.source_runs,
                       source_events_keys=self.source_events_loaded, seed_counts=dict(self.seed_counts),
                       paid_discovery_requests=0, prop_audits=audit_counts,
                       scope="Historical US bookmaker player props; four tracks; cache-aware continuation",
                       markets=MARKETS, horizons_minutes=HORIZONS,
                       earliest_possible_snapshot=iso(PROP_START), feature_approved=False,
                       not_completed_by_this_runner=["all_event_coverage", "all_prop_markets", "NCAA_women_props",
                           "settlement_mapping", "participant_resolution", "schedule_provenance", "point_in_time_feature_approval", "proven_market_advantage"])
        return summary

    def resume_state(self):
        with self.lock:
            return {"version": VERSION, "run_id": self.run_id, "source_runs": self.args.source_runs,
                    "source_events_keys": list(self.args.source_events_keys),
                    "new_successful_request_ids": [x["request_id"] for x in self.receipts],
                    "immutable_missing_request_ids": sorted(self.negative),
                    "resume_instruction": "Append this run ID to --source-runs after final summary and receipts exist; persisted request-index entries are also reused."}

    def checkpoint(self):
        summary = super().checkpoint()
        self.save_json("shared/acquisition/paid/" + self.run_id + "/resume-state.json", self.resume_state())
        return summary

    def finish(self):
        self.stop.set()
        summary = self.checkpoint()
        prefix = "shared/acquisition/paid/" + self.run_id
        payload = {"summary.json": summary, "failures.json": self.failures,
                   "receipts.json": self.receipts, "resume-state.json": self.resume_state()}
        for name, value in payload.items():
            self.save_json(prefix + "/" + name, value)
        out = Path(self.args.output_dir)
        out.mkdir(parents=True, exist_ok=True)
        name = "sports_edge_lab_props_return_" + self.run_id + ".zip"
        with zipfile.ZipFile(out / name, "w", zipfile.ZIP_DEFLATED) as bundle:
            for part, value in payload.items():
                bundle.writestr(part, blob(value))
            bundle.writestr("readme.txt", "Private raw captures and per-market audits remain in S3. Passing recorded time checks does not approve any feature.\n")
        self.s3.upload_file(str(out / name), self.args.bucket, prefix + "/" + name,
                            ExtraArgs={"ServerSideEncryption": "AES256"})
        emit("COMPLETE", run_id=self.run_id, return_zip=name, statistics=summary["statistics"],
             budget=summary["budget"], prop_audits=summary["prop_audits"])
        return 1 if any(x.get("status") == "failed" for x in self.phase.values()) else 0


def props_tests():
    class Checks(unittest.TestCase):
        def setUp(self):
            self.event = {"id": "one", "commence_time": "2025-01-01T20:00:00Z"}
            self.target = parse("2025-01-01T19:45:00Z")
            self.good = {"name": "Over", "description": "Player One", "point": 20.5, "price": 1.9}
        def response(self, markets):
            return {"timestamp": iso(self.target), "data": {**self.event, "bookmakers": [{"key": "book", "markets": markets}]}}
        def market(self, stamp="2025-01-01T19:44:00Z", outcomes=None):
            return {"key": "player_points", "last_update": stamp, "outcomes": outcomes if outcomes is not None else [self.good]}
        def test_market_local_future_time_does_not_poison_good_market(self):
            a = quote_audit("nba", self.event, self.target, self.response([self.market(), self.market("2025-01-01T19:46:00Z")]))
            self.assertEqual(a["quote_recorded_time_pass"], 1)
            self.assertEqual(a["quote_structure_and_time_pass"], 1)
            self.assertEqual(a["markets"][0]["structure_and_time_passing_outcome_indices"], [0])
            self.assertEqual(a["markets"][1]["structure_and_time_passing_outcome_indices"], [])
            self.assertFalse(a["feature_approved"])
        def test_outcome_local_price_failure(self):
            a = quote_audit("nba", self.event, self.target, self.response([self.market(outcomes=[self.good, {**self.good, "price": float("nan")}])]))
            self.assertEqual(a["quote_recorded_time_pass"], 2)
            self.assertEqual(a["quote_structure_and_time_pass"], 1)
            self.assertEqual(a["markets"][0]["structurally_rejected_outcomes"][0]["outcome_index"], 1)
        def test_missing_participant_is_not_approved(self):
            a = quote_audit("nba", self.event, self.target, self.response([self.market(outcomes=[{"price": 1.9, "point": 20.5, "name": "Over"}])]))
            self.assertEqual(a["quote_structure_and_time_pass"], 0)
        def test_snapshot_after_decision_blocks_every_quote(self):
            r = self.response([self.market()]); r["timestamp"] = "2025-01-01T19:46:00Z"
            a = quote_audit("nba", self.event, self.target, r)
            self.assertEqual(a["quote_recorded_time_pass"], 0)
        def test_event_mismatch_blocks_every_quote(self):
            r = self.response([self.market()]); r["data"]["id"] = "other"
            self.assertEqual(quote_audit("nba", self.event, self.target, r)["quote_structure_and_time_pass"], 0)
        def test_kickoff_revision_visible_and_started_event_blocked(self):
            r = self.response([self.market()]); r["data"]["commence_time"] = "2025-01-01T19:00:00Z"
            a = quote_audit("nba", self.event, self.target, r)
            self.assertEqual(a["quote_recorded_time_pass"], 0)
            self.assertIn("kickoff_revision_requires_schedule_provenance", a["warnings"])
        def test_immutable_missing_is_exact_old_event_request(self):
            rid, req = request_for("nba", self.event, self.target)
            self.assertTrue(immutable_missing({"request": req, "status": 404}, parse("2026-01-01T00:00:00Z")))
            self.assertFalse(immutable_missing({"request": req, "status": 403}, parse("2026-01-01T00:00:00Z")))
            self.assertFalse(immutable_missing({"request": req, "status": 404}, self.target))
            changed = {**req, "endpoint": "/v4/historical/sports/basketball_nba/odds"}
            self.assertFalse(immutable_missing({"request": changed, "status": 404}, parse("2026-01-01T00:00:00Z")))
        def test_cached_and_negative_requests_are_not_planned(self):
            events = {"nba": {"one": self.event}, "nfl": {"one": self.event}}
            all_rows = list(planned_queries(events, parse("2026-01-01T00:00:00Z"), set()))
            rid, _ = request_for(*all_rows[0][:3])
            remaining = list(planned_queries(events, parse("2026-01-01T00:00:00Z"), {rid}))
            self.assertEqual(len(all_rows), 6); self.assertEqual(len(remaining), 5)
            self.assertEqual([r[0] for r in all_rows[:4]], ["nfl", "nba", "nfl", "nba"])
        def test_full_budget_atomic_reservation(self):
            b = Budget(500000, 0)
            def reserve(_):
                try:
                    b.reserve("odds", 60); return 1
                except BudgetStop:
                    return 0
            with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
                self.assertEqual(sum(pool.map(reserve, range(8400))), 8333)
            self.assertEqual(b.snapshot()["reserved_or_known"]["odds"], 499980)
        def test_all_markets_reserve_sixty(self):
            self.assertTrue(all(historical_cost({"markets": ",".join(m), "regions": "us"}) == 60 for m in MARKETS.values()))
        def test_403_disables_provider_without_blocking_other_events(self):
            a = PropsContinuation.__new__(PropsContinuation)
            a.budget, a.lock, a.failures, a.negative = Budget(500, 0), threading.Lock(), [], set()
            a.end = parse("2026-01-01T00:00:00Z")
            _, req = request_for("nba", self.event, self.target)
            a.failure(req, "denied", status=403)
            with self.assertRaises(BudgetStop): a.budget.reserve("odds", 60)
        def test_403_prevents_next_event_http_request(self):
            import types
            import urllib.error
            a = PropsContinuation.__new__(PropsContinuation)
            a.budget, a.lock, a.failures, a.negative = Budget(500, 0), threading.Lock(), [], set()
            a.end, a.deadline = parse("2026-01-01T00:00:00Z"), time.monotonic() + 30
            a.stop, a.cache = threading.Event(), {}
            a.request_locks = collections.defaultdict(threading.Lock)
            a.blocked_endpoints, a.blocked_statuses = set(), set()
            a.args = types.SimpleNamespace(max_response_mb=64)
            a.keys, a.stats = {"odds": "unit-test-key"}, collections.Counter()
            a.run_id = "unit-test"
            a.s3_json = lambda key: None
            a.save_json = lambda key, value: None
            calls = []
            def denied(request, timeout):
                calls.append(1)
                raise urllib.error.HTTPError("https://test.invalid", 403, "denied", {"x-requests-last": "0"}, None)
            a.opener = types.SimpleNamespace(open=denied)
            rid, req = request_for("nba", self.event, self.target)
            self.assertIsNone(a.capture("odds", "nba", req["endpoint"], req["params"], "test"))
            with self.assertRaises(BudgetStop):
                a.capture("odds", "nba", req["endpoint"].replace("/one/", "/two/"), req["params"], "test")
            self.assertEqual(len(calls), 1)
        def test_404_does_not_disable_provider(self):
            a = PropsContinuation.__new__(PropsContinuation)
            a.budget, a.lock, a.failures, a.negative = Budget(500, 0), threading.Lock(), [], set()
            a.end = parse("2026-01-01T00:00:00Z")
            rid, req = request_for("nba", self.event, self.target)
            a.failure(req, "missing", status=404)
            self.assertIn(rid, a.negative); a.budget.reserve("odds", 60)
        def test_capture_skip_requires_no_io(self):
            a = PropsContinuation.__new__(PropsContinuation)
            rid, _ = request_for("nba", self.event, self.target)
            a.cache, a.negative, a.attempted = {rid: {}}, set(), set()
            a.lock, a.stats = threading.Lock(), collections.Counter()
            a.capture_prop("nba", self.event, self.target, 15)
            self.assertEqual(a.stats["already_completed_or_negative_skipped"], 1)
        def test_optional_future_and_before_provider_start_excluded(self):
            events = {"nba": {"future": {"id": "future", "commence_time": "2027-01-01T00:00:00Z"},
                              "old": {"id": "old", "commence_time": "2023-05-02T00:00:00Z"}}}
            self.assertEqual(list(planned_queries(events, parse("2026-01-01T00:00:00Z"), set())), [])
    result = unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.loadTestsFromTestCase(Checks))
    if not result.wasSuccessful():
        raise RuntimeError("Prop continuation self-test gate failed")
    return result.testsRun


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bucket", default="sagemaker-sports-edge-lab-560403859723-us-west-2")
    parser.add_argument("--region", default="us-west-2")
    parser.add_argument("--source-runs", nargs="+", default=SOURCE_RUNS)
    parser.add_argument("--source-events-keys", nargs="+", default=[SOURCE_EVENTS, EXTRA_EVENTS])
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
    args.mode, args.stats_calls = "odds", 0
    logging.getLogger("boto3").setLevel(logging.ERROR)
    logging.getLogger("botocore").setLevel(logging.ERROR)
    try:
        tests = self_test() + props_tests()
        emit("SELF_TEST_PASS", tests=tests, workload=VERSION)
        if args.self_test: return 0
        if not (60 <= args.odds_credits <= 500000 and 30 <= args.max_seconds <= 6900
                and 1 <= args.odds_workers <= 4 and 1 <= args.max_response_mb <= 64):
            raise ValueError("Prop continuation bounds exceeded")
        if any(not re.fullmatch(r"[A-Za-z0-9_-]+", r) for r in args.source_runs):
            raise ValueError("Invalid source run")
        if any(not re.fullmatch(r"shared/acquisition/paid/[A-Za-z0-9_-]+/discovered-events\.json", k) for k in args.source_events_keys):
            raise ValueError("Invalid source event key")
        archive = PropsContinuation(args)
        emit("START", run_id=archive.run_id, workload=VERSION, max_credits=args.odds_credits, paid_discovery_requests=0)
        beat = threading.Thread(target=archive.heartbeat, daemon=True); beat.start()
        archive.safe_work("seed", archive.seed)
        if archive.phase["seed"]["status"] == "completed":
            archive.safe_work("player_props", archive.work)
        archive.stop.set(); beat.join(timeout=10)
        return archive.finish()
    except Exception as exc:
        emit("FATAL", error_type=type(exc).__name__)
        return 1


if __name__ == "__main__":
    sys.exit(main())
