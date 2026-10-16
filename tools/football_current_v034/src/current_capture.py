"""Capture a bounded current five-track sports snapshot on AWS."""
import argparse
import collections
import datetime as dt
import logging
import json
import re
import sys
import threading
import time
import unittest
import urllib.error
import urllib.parse
from types import SimpleNamespace

from acquire_paid_data import (Archive, Budget, BudgetStop, HOSTS, SPORTS, blob,
    digest, emit, identity, iso, now, parse, self_test)

VERSION = "sports-edge-lab-current-v026"
LEASE_KEY = "shared/control/current-acquisition/v026-active.json"
HISTORICAL_RUNS = ("20261016T182005Z-1999205e92", "20261016T184218Z-a7117f54b6")
FOOTBALL = ["player_pass_yds", "player_pass_tds", "player_rush_yds", "player_reception_yds", "player_receptions", "player_anytime_td"]
BASKETBALL = ["player_points", "player_rebounds", "player_assists", "player_threes", "player_blocks", "player_steals"]
PROP_MARKETS = {"nfl": FOOTBALL, "ncaaf": FOOTBALL, "nba": BASKETBALL, "ncaam": BASKETBALL}
DOCS = ["https://the-odds-api.com/liveapi/guides/v4/", "https://api.collegefootballdata.com/api/games",
    "https://api.collegefootballdata.com/api/stats", "https://api.collegefootballdata.com/api/teams",
    "https://api.collegebasketballdata.com/api/games", "https://api.collegebasketballdata.com/api/teams"]


def current_odds_cost(endpoint, params):
    if not endpoint.startswith("/v4/sports/") or "/historical/" in endpoint or "date" in params:
        raise ValueError("Historical endpoint or timestamp not permitted in current collector")
    if endpoint.endswith("/events"):
        # Documented free endpoint; reserve one until its response confirms zero.
        return 1
    if not endpoint.endswith("/odds") or "bookmakers" in params:
        raise ValueError("Unsupported current endpoint or bookmaker cost basis")
    markets = set(filter(None, params.get("markets", "").split(",")))
    regions = set(filter(None, params.get("regions", "").split(",")))
    if not markets or regions != {"us"}:
        raise ValueError("Explicit US current-market budget required")
    return len(markets) * len(regions)


def schedule_summary(rows, observed, date_field, id_field="id"):
    counts = collections.Counter()
    dates, ids = [], set()
    for row in rows if isinstance(rows, list) else []:
        if not isinstance(row, dict):
            counts["invalid_rows"] += 1
            continue
        ids.add(str(row.get(id_field)))
        try:
            when = parse(row[date_field])
        except (KeyError, TypeError, ValueError, AttributeError):
            counts["missing_event_time"] += 1
            continue
        dates.append(iso(when))
        counts["upcoming"] += int(when > observed)
        counts["upcoming_seven_days"] += int(observed < when <= observed + dt.timedelta(days=7))
        counts["started_by_schedule"] += int(when <= observed)
        counts["completed_flag_true"] += int(row.get("completed") is True)
    return {"rows": len(rows) if isinstance(rows, list) else None, "distinct_ids": len(ids),
        "earliest_event_time": min(dates) if dates else None, "latest_event_time": max(dates) if dates else None,
        **dict(counts), "schedule_time_is_not_completion_confirmation": True}


def audit_event(row, received):
    audit = {"event_id": row.get("id"), "home_team": row.get("home_team"), "away_team": row.get("away_team"),
        "event_time": row.get("commence_time"), "received_at": iso(received), "feature_approved": False,
        "bookmakers": 0, "markets": 0, "outcomes": 0, "quotes_updated_after_retrieval": 0,
        "quotes_missing_update_time": 0, "quote_times": []}
    try:
        audit["started_by_schedule"] = parse(row["commence_time"]) <= received
    except (KeyError, TypeError, ValueError, AttributeError):
        audit["started_by_schedule"] = None
    for book in row.get("bookmakers", []) if isinstance(row.get("bookmakers", []), list) else []:
        if not isinstance(book, dict):
            continue
        audit["bookmakers"] += 1
        for market in book.get("markets", []) if isinstance(book.get("markets", []), list) else []:
            if not isinstance(market, dict):
                continue
            audit["markets"] += 1
            outcomes = market.get("outcomes", [])
            audit["outcomes"] += len(outcomes) if isinstance(outcomes, list) else 0
            try:
                updated = parse(market.get("last_update", book.get("last_update")))
                audit["quote_times"].append(iso(updated))
                audit["quotes_updated_after_retrieval"] += int(updated > received)
            except (TypeError, ValueError, AttributeError):
                audit["quotes_missing_update_time"] += 1
    quote_times = audit.pop("quote_times")
    audit["oldest_quote_time"] = min(quote_times) if quote_times else None
    audit["newest_quote_time"] = max(quote_times) if quote_times else None
    audit["has_bookmakers"] = audit["bookmakers"] > 0
    audit["has_market_outcomes"] = audit["outcomes"] > 0
    return audit


def choose_props(rows, observed, limit):
    candidates = {}
    for row in rows if isinstance(rows, list) else []:
        if not isinstance(row, dict) or not re.fullmatch(r"[A-Za-z0-9_-]+", str(row.get("id", ""))):
            continue
        try:
            when = parse(row["commence_time"])
        except (KeyError, TypeError, ValueError, AttributeError):
            continue
        if observed < when <= observed + dt.timedelta(days=7):
            candidates[row["id"]] = row
    return sorted(candidates.values(), key=lambda r: (r["commence_time"], r["id"]))[:limit]


def current_weeks(rows, observed):
    weeks = set()
    for row in rows if isinstance(rows, list) else []:
        try:
            start, end = parse(row["startDate"]), parse(row["endDate"])
            week, season_type = row["week"], row["seasonType"]
        except (KeyError, TypeError, ValueError, AttributeError):
            continue
        if start <= observed <= end and isinstance(week, int) and season_type in ("regular", "postseason"):
            weeks.add((week, season_type))
    return sorted(weeks)


def outstanding_odds(summary, final=False):
    budget = summary.get("budget", {})
    limit, reserved = budget.get("limits", {}).get("odds"), budget.get("reserved_or_known", {}).get("odds")
    if not isinstance(limit, int) or not isinstance(reserved, int) or min(limit, reserved) < 0:
        raise ValueError("Historical quota commitment unavailable")
    return 0 if final else max(0, limit - reserved)


def quota_sufficient(remaining, commitments, limit, floor):
    return isinstance(remaining, int) and remaining >= commitments + limit + floor


class CurrentOpener:
    def __init__(self, delegate, owner, interval=0.5, clock=time.monotonic, sleep=time.sleep):
        self.delegate, self.owner, self.interval = delegate, owner, interval
        self.clock, self.sleep, self.lock, self.next_at = clock, sleep, threading.Lock(), 0.0

    def open(self, request, timeout):
        host = urllib.parse.urlsplit(request.full_url).hostname
        provider = next((k for k, v in HOSTS.items() if urllib.parse.urlsplit(v).hostname == host), None)
        if provider is None:
            raise ValueError("Unrecognized authenticated provider host")
        with self.lock:
            self.owner.time_left()
            with self.owner.budget.lock:
                if provider in self.owner.budget.disabled:
                    raise BudgetStop("provider_disabled_before_http")
            delay = max(0, self.next_at - self.clock())
            if delay:
                self.sleep(delay)
            self.owner.time_left()
            with self.owner.budget.lock:
                if provider in self.owner.budget.disabled:
                    raise BudgetStop("provider_disabled_before_http")
            self.next_at = self.clock() + self.interval
        try:
            return self.delegate.open(request, timeout=timeout)
        except urllib.error.HTTPError as exc:
            if exc.code in (401, 402, 403, 429):
                self.owner.budget.disable(provider)
            raise


class CurrentCapture(Archive):
    def __init__(self, args):
        super().__init__(args)
        self.observed = now()
        self.end = self.observed
        self.vintage = "current:" + iso(self.observed) + ":" + self.run_id
        self.blocked_statuses = set()
        self.opener = CurrentOpener(self.opener, self)
        self.current_coverage, self.event_audits, self.extra_return_members = {}, [], {}
        self.event_lists = {}
        self.lease_owned, self.lease_etag = False, None
        self.lease_status, self.quota_preflight = {"status": "not_attempted"}, {}

    def acquire_lease(self):
        from botocore.exceptions import ClientError
        stamp = now()
        body = blob({"owner": self.run_id, "acquired_at": iso(stamp),
            "expires_at": iso(stamp + dt.timedelta(seconds=1200))})
        common = {"Bucket": self.args.bucket, "Key": LEASE_KEY, "Body": body,
            "ContentType": "application/json", "ServerSideEncryption": "AES256"}
        try:
            response = self.s3.put_object(**common, IfNoneMatch="*")
        except ClientError as exc:
            if exc.response.get("Error", {}).get("Code") not in ("PreconditionFailed", "ConditionalRequestConflict", "412", "409"):
                raise
            previous = self.s3.get_object(Bucket=self.args.bucket, Key=LEASE_KEY)
            with previous["Body"] as stream:
                lease = json.load(stream)
            if parse(lease["expires_at"]) > now():
                self.lease_status = {"status": "active_lease_blocked", "expires_at": lease["expires_at"]}
                raise BudgetStop("another_current_collector_has_active_lease")
            try:
                response = self.s3.put_object(**common, IfMatch=previous["ETag"])
            except ClientError as conflict:
                if conflict.response.get("Error", {}).get("Code") in ("PreconditionFailed", "ConditionalRequestConflict", "412", "409"):
                    raise BudgetStop("current_lease_takeover_race")
                raise
        self.lease_etag = response["ETag"]
        self.lease_owned = True
        self.lease_status = {"status": "owned", "expires_at": iso(stamp + dt.timedelta(seconds=1200))}

    def release_lease(self):
        if not self.lease_owned:
            return
        from botocore.exceptions import ClientError
        stamp = iso(now())
        try:
            self.s3.put_object(Bucket=self.args.bucket, Key=LEASE_KEY, IfMatch=self.lease_etag,
                Body=blob({"owner": self.run_id, "released_at": stamp, "expires_at": stamp}),
                ContentType="application/json", ServerSideEncryption="AES256")
            self.lease_owned = False
            self.lease_status = {"status": "released_with_matching_etag", "released_at": stamp}
        except ClientError:
            # No unconditional deletion: an active successor must never be erased.
            self.lease_status["release"] = "not_confirmed_expiry_retained"

    def quota_gate(self):
        commitments, evidence = 0, []
        for run in HISTORICAL_RUNS:
            prefix = "shared/acquisition/paid/" + run
            report = self.s3_json(prefix + "/summary.json")
            final = report is not None
            if report is None:
                report = self.s3_json(prefix + "/progress.json")
            if not isinstance(report, dict) or report.get("run_id") != run:
                raise RuntimeError("Known historical quota evidence missing")
            remaining_bound = outstanding_odds(report, final)
            commitments += remaining_bound
            evidence.append({"run_id": run, "final_summary": final, "unspent_bound": remaining_bound,
                "observed_at": report.get("timestamp")})
        headers = self.budget.snapshot()["provider_headers"].get("odds", {})
        remaining = headers.get("x-requests-remaining")
        self.quota_preflight = {"provider_remaining": remaining, "historical_outstanding_bound": commitments,
            "current_run_limit": self.args.odds_credits, "reserve_floor": self.args.odds_reserve_floor,
            "known_historical_evidence": evidence,
            "passed": quota_sufficient(remaining, commitments, self.args.odds_credits, self.args.odds_reserve_floor)}
        if not self.quota_preflight["passed"]:
            self.budget.disable("odds")
            raise BudgetStop("current_odds_global_reserve_gate")

    def request_cost(self, provider, endpoint, params):
        return current_odds_cost(endpoint, params) if provider == "odds" else 1

    def capture_current(self, provider, track, endpoint, params, label):
        requested = now()
        data = self.capture(provider, track, endpoint, params, label, self.vintage, need_data=True)
        received = now()
        descriptor = identity(provider, track, endpoint, params, self.vintage)
        rid = digest(blob(descriptor))
        receipt = self.cache.get(rid, {})
        entry = {"provider": provider, "track": track, "endpoint": endpoint, "params": params,
            "request_id": rid, "requested_at": iso(requested), "received_at": iso(received),
            "receipt_retrieved_at": receipt.get("retrieved_at"), "raw_key": receipt.get("raw_key"),
            "rows": len(data) if isinstance(data, list) else None, "http_capture_succeeded": data is not None,
            "is_empty_list": data == [], "provider_asof_timestamp_known": False}
        if provider == "odds":
            events = data if isinstance(data, list) else [data] if isinstance(data, dict) and data.get("id") else []
            audits = [audit_event(row, received) for row in events if isinstance(row, dict)]
            entry.update(schedule_summary(events, received, "commence_time"),
                events_with_bookmakers=sum(a["has_bookmakers"] for a in audits),
                events_with_outcomes=sum(a["has_market_outcomes"] for a in audits),
                market_outcomes=sum(a["outcomes"] for a in audits))
            with self.lock:
                self.event_audits = [a for a in self.event_audits if a["request_id"] != rid]
                self.event_audits.extend({"track": track, "request_id": rid, **audit} for audit in audits)
        elif endpoint == "/games":
            entry.update(schedule_summary(data, received, "startDate"))
        with self.lock:
            self.current_coverage[rid] = entry
        return data

    def odds_track(self, track):
        prefix = "/v4/sports/" + SPORTS[track][0]
        events = self.capture_current("odds", track, prefix + "/events", {"dateFormat": "iso"}, "current_events")
        odds = self.capture_current("odds", track, prefix + "/odds", {"regions": "us", "markets": "h2h,spreads,totals",
            "dateFormat": "iso", "oddsFormat": "decimal"}, "current_game_markets")
        # Merge exact event IDs. Live odds can add an event missing from metadata.
        merged = {r["id"]: r for rows in (events, odds) if isinstance(rows, list)
                  for r in rows if isinstance(r, dict) and r.get("id")}
        with self.lock:
            self.event_lists[track] = list(merged.values())
            self.events[track] = {k: {**r, "seen_at_snapshot": iso(now())} for k, r in merged.items()}

    def prop_event(self, track, event):
        # Never request an event which has started while earlier work ran.
        if parse(event["commence_time"]) <= now():
            self.count(current_props_skipped_started=1)
            return
        self.capture_current("odds", track, "/v4/sports/" + SPORTS[track][0] + "/events/" + event["id"] + "/odds",
            {"regions": "us", "markets": ",".join(PROP_MARKETS[track]), "dateFormat": "iso", "oddsFormat": "decimal"},
            "current_player_props")

    def odds_work(self):
        # Documented free event lookup exposes a fresh account quota header.
        self.capture_current("odds", "nfl", "/v4/sports/" + SPORTS["nfl"][0] + "/events",
            {"dateFormat": "iso"}, "current_events_quota_preflight")
        self.quota_gate()
        self.phase["current_game_markets"] = {"status": "running", "planned": 5, "completed": 0}
        self.parallel_tasks([(track,) for track in SPORTS], self.odds_track, "current_game_markets", self.args.workers)
        self.checkpoint()
        tasks = [(track, row) for track in PROP_MARKETS
                 for row in choose_props(self.event_lists.get(track, []), now(), self.args.props_per_track)]
        self.phase["current_props"] = {"status": "running", "planned": len(tasks), "completed": 0,
            "maximum_events_per_track": self.args.props_per_track, "event_window_days": 7}
        self.parallel_tasks(tasks, self.prop_event, "current_props", self.args.workers)

    def cfbd_work_current(self):
        year = self.observed.year
        params = {"year": year}
        calendar = self.capture_current("cfbd", "ncaaf", "/calendar", params, "current_cfbd_calendar")
        games = self.capture_current("cfbd", "ncaaf", "/games", {**params, "seasonType": "both"}, "current_cfbd_games")
        weeks = current_weeks(calendar, self.observed)
        self.phase["current_cfbd_week"] = {"calendar_matched_weeks": weeks,
            "games_matching_weeks": sum(isinstance(g, dict) and (g.get("week"), g.get("seasonType")) in weeks
                for g in games if isinstance(games, list)) if isinstance(games, list) else 0}
        for endpoint in ("/roster", "/stats/season", "/stats/player/season", "/stats/season/advanced"):
            self.capture_current("cfbd", "ncaaf", endpoint, params, "current_cfbd" + endpoint)
        for week, season_type in weeks[:2]:
            for endpoint in ("/games/teams", "/games/players"):
                self.capture_current("cfbd", "ncaaf", endpoint, {**params, "week": week, "seasonType": season_type},
                    "current_cfbd_weekly" + endpoint)
        self.phase["current_cfbd"] = {"status": "planned_requests_processed", "season_requested": year,
            "provider_asof_timestamp_known": False}

    def cbbd_slice(self, season, start, end):
        rows = self.capture_current("cbbd", "ncaam", "/games",
            {"season": season, "startDateRange": iso(start), "endDateRange": iso(end)}, "current_cbbd_schedule")
        if isinstance(rows, list) and len(rows) >= 3000:
            if (end - start).total_seconds() <= 3600:
                self.failure({"provider": "cbbd", "endpoint": "/games"}, "current_schedule_cap_unresolved")
                raise RuntimeError("Schedule response cap unresolved")
            middle = start + (end - start)/2
            self.cbbd_slice(season, start, middle)
            self.cbbd_slice(season, middle, end)

    def cbbd_work_current(self):
        season = self.observed.year + (self.observed.month >= 7)
        self.capture_current("cbbd", "ncaam", "/teams", {"season": season}, "current_cbbd_teams")
        start = self.observed.replace(hour=0, minute=0, second=0, microsecond=0)
        for offset in (0, 15, 30):
            self.cbbd_slice(season, start + dt.timedelta(days=offset), start + dt.timedelta(days=offset+15))
        self.phase["current_cbbd"] = {"status": "planned_requests_processed", "season_requested": season,
            "schedule_window_days": 45, "no_offseason_statistics_requested": True}

    def checkpoint(self):
        summary = super().checkpoint()
        prefix = "shared/acquisition/current/" + self.run_id
        with self.lock:
            audit = {"run_id": self.run_id, "captured_at": iso(now()), "current_vintage": self.vintage,
                "requests": dict(self.current_coverage), "events": list(self.event_audits)}
        self.save_json(prefix + "/freshness-audit.json", audit)
        self.extra_return_members["freshness-audit.json"] = audit
        return summary

    def summary(self):
        result = super().summary()
        with self.lock:
            coverage = dict(self.current_coverage)
        result.update(version=VERSION, current_vintage=self.vintage, observation_started_at=iso(self.observed),
            current_collector_lease=dict(self.lease_status), quota_preflight=dict(self.quota_preflight),
            scope="Fresh current five-track US game markets/events; limited current props; current CFBD; upcoming CBBD schedules",
            current_requests=coverage, official_documentation=DOCS,
            current_request_summary={"requests": len(coverage),
                "http_successes": sum(r["http_capture_succeeded"] for r in coverage.values()),
                "empty_lists": sum(r["is_empty_list"] for r in coverage.values()),
                "nonempty_list_responses": sum(isinstance(r.get("rows"), int) and r["rows"] > 0 for r in coverage.values()),
                "odds_events_with_outcomes_including_repeated_requests": sum(r.get("events_with_outcomes", 0) for r in coverage.values())},
            not_completed_by_this_runner=["recurring_live_polling", "all_prop_events", "all_prop_markets",
                "NCAA_women_statistical_feed", "feature_approval", "provider_publication_time_verification"],
            data_notes=["This is a finite current observation, not historical as-of reconstruction.",
                "Capture time, event time, and bookmaker quote time are distinct fields.",
                "Current rosters and season statistics may contain postgame updates and corrections.",
                "An empty response is not zero performance or proof of full coverage.",
                "CBBD covers the men's statistical track; women's game odds are captured separately."])
        return result


def current_tests():
    class Tests(unittest.TestCase):
        def test_live_market_cost_and_free_discovery_reserve(self):
            self.assertEqual(current_odds_cost("/v4/sports/nfl/odds", {"markets":"h2h,spreads,totals","regions":"us"}),3)
            self.assertEqual(current_odds_cost("/v4/sports/nfl/events/abc/odds", {"markets":",".join(FOOTBALL),"regions":"us"}),6)
            self.assertEqual(current_odds_cost("/v4/sports/nfl/events", {}),1)
        def test_historical_route_rejected(self):
            with self.assertRaises(ValueError):
                current_odds_cost("/v4/historical/sports/nfl/odds", {"markets":"h2h","regions":"us"})
            with self.assertRaises(ValueError):
                current_odds_cost("/v4/sports/nfl/odds", {"date":"2025-01-01","markets":"h2h","regions":"us"})
        def test_current_identity_does_not_alias_historical_or_other_runs(self):
            a=identity("cbbd","ncaam","/teams",{"season":2027},"current:one")
            b=identity("cbbd","ncaam","/teams",{"season":2027},"current:two")
            c=identity("cbbd","ncaam","/teams",{"season":2027},"2026-10-16")
            self.assertEqual(len({digest(blob(x)) for x in (a,b,c)}),3)
        def test_props_window_ids_and_cap(self):
            at=parse("2026-10-16T19:00:00Z")
            rows=[{"id":"ok","commence_time":"2026-10-17T19:00:00Z"},
                {"id":"late","commence_time":"2026-10-25T19:00:00Z"},
                {"id":"started","commence_time":"2026-10-16T18:00:00Z"},
                {"id":"bad/id","commence_time":"2026-10-17T20:00:00Z"}]
            self.assertEqual([r["id"] for r in choose_props(rows+rows,at,12)],["ok"])
            self.assertEqual(choose_props(rows,at,0),[])
        def test_empty_bookmakers_not_claimed_as_coverage(self):
            audit=audit_event({"id":"a","commence_time":"2026-10-17T19:00:00Z","bookmakers":[]},parse("2026-10-16T19:00:00Z"))
            self.assertFalse(audit["has_bookmakers"])
            self.assertFalse(audit["has_market_outcomes"])
        def test_quote_time_separate_from_capture_time(self):
            at=parse("2026-10-16T19:00:00Z")
            row={"id":"a","commence_time":"2026-10-17T19:00:00Z","bookmakers":[{"last_update":"2026-10-16T19:01:00Z",
                "markets":[{"key":"h2h","outcomes":[{"name":"one","price":1.9}]}]}]}
            audit=audit_event(row,at)
            self.assertEqual(audit["quotes_updated_after_retrieval"],1)
            self.assertFalse(audit["feature_approved"])
        def test_calendar_current_week_selection(self):
            at=parse("2026-10-16T19:00:00Z")
            rows=[{"week":7,"seasonType":"regular","startDate":"2026-10-12T00:00:00Z","endDate":"2026-10-19T00:00:00Z"},
                {"week":8,"seasonType":"regular","startDate":"2026-10-19T00:00:00Z","endDate":"2026-10-26T00:00:00Z"}]
            self.assertEqual(current_weeks(rows,at),[(7,"regular")])
        def test_date_coverage_not_capture_date(self):
            at=parse("2026-10-16T19:00:00Z")
            report=schedule_summary([{"id":1,"startDate":"2026-11-01T00:00:00Z"}],at,"startDate")
            self.assertEqual(report["upcoming"],1)
            self.assertEqual(report["upcoming_seven_days"],0)
            self.assertEqual(report["latest_event_time"],"2026-11-01T00:00:00Z")
        def test_rate_denial_cancels_queued_provider_only(self):
            owner=SimpleNamespace(time_left=lambda:None,budget=Budget(500,100))
            def fail(*args,**kwargs):
                raise urllib.error.HTTPError("https://api.the-odds-api.com",429,"rate",{},None)
            opener=CurrentOpener(SimpleNamespace(open=fail),owner)
            request=SimpleNamespace(full_url="https://api.the-odds-api.com/v4/sports/nfl/odds")
            with self.assertRaises(urllib.error.HTTPError): opener.open(request,10)
            with self.assertRaises(BudgetStop): opener.open(request,10)
            owner.budget.reserve("cfbd")
        def test_schedule_cap_is_split(self):
            obj=CurrentCapture.__new__(CurrentCapture)
            calls=[]
            def capture(provider,track,path,params,label):
                calls.append(params)
                return [{}]*3000 if len(calls)==1 else []
            obj.capture_current=capture
            start=parse("2026-10-16T00:00:00Z")
            obj.cbbd_slice(2027,start,start+dt.timedelta(days=15))
            self.assertEqual(len(calls),3)
            self.assertEqual(calls[1]["endDateRange"],calls[2]["startDateRange"])
        def test_provider_budget_and_zero_cost_header(self):
            b=Budget(3,1)
            b.finish("odds",b.reserve("odds",1),{"x-requests-last":"0"})
            b.reserve("odds",3)
            with self.assertRaises(BudgetStop): b.reserve("odds",1)
        def test_cost_hook_current_not_historical(self):
            obj=CurrentCapture.__new__(CurrentCapture)
            self.assertEqual(obj.request_cost("odds","/v4/sports/nfl/odds",{"markets":"h2h,spreads,totals","regions":"us"}),3)
            self.assertEqual(obj.request_cost("cfbd","/games",{"year":2026}),1)
        def test_global_quota_reserves_active_jobs_and_floor(self):
            report={"budget":{"limits":{"odds":1600000},"reserved_or_known":{"odds":527520}}}
            self.assertEqual(outstanding_odds(report),1072480)
            self.assertEqual(outstanding_odds(report,True),0)
            self.assertFalse(quota_sufficient(None,1072480,500,100000))
            self.assertFalse(quota_sufficient(1172979,1072480,500,100000))
            self.assertTrue(quota_sufficient(1172980,1072480,500,100000))
        def test_current_lease_uses_conditional_create_and_release(self):
            obj=CurrentCapture.__new__(CurrentCapture)
            calls=[]
            obj.run_id,obj.args="test",SimpleNamespace(bucket="test")
            obj.lease_owned=False
            def put(**kwargs):
                calls.append(kwargs)
                return {"ETag":"etag"}
            obj.s3=SimpleNamespace(put_object=put)
            obj.acquire_lease()
            self.assertEqual(calls[0]["IfNoneMatch"],"*")
            obj.release_lease()
            self.assertEqual(calls[1]["IfMatch"],"etag")
            self.assertFalse(obj.lease_owned)
        def test_active_lease_blocks_and_expired_lease_uses_etag(self):
            import io
            from botocore.exceptions import ClientError
            for active in (True,False):
                obj=CurrentCapture.__new__(CurrentCapture)
                obj.run_id,obj.args,obj.lease_owned="test",SimpleNamespace(bucket="test"),False
                calls=[]
                def put(**kwargs):
                    calls.append(kwargs)
                    if len(calls)==1:
                        raise ClientError({"Error":{"Code":"PreconditionFailed"}},"PutObject")
                    return {"ETag":"new-etag"}
                expiry=iso(now()+dt.timedelta(seconds=1200 if active else -1))
                obj.s3=SimpleNamespace(put_object=put,get_object=lambda **kw:{"ETag":"old-etag",
                    "Body":io.BytesIO(blob({"owner":"old","expires_at":expiry}))})
                if active:
                    with self.assertRaises(BudgetStop):obj.acquire_lease()
                    self.assertEqual(len(calls),1)
                else:
                    obj.acquire_lease()
                    self.assertEqual(calls[1]["IfMatch"],"old-etag")
                    self.assertTrue(obj.lease_owned)
    result=unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
    if not result.wasSuccessful(): raise RuntimeError("Current collector test gate failed")
    return result.testsRun


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bucket",default="sagemaker-sports-edge-lab-560403859723-us-west-2")
    parser.add_argument("--region",default="us-west-2")
    parser.add_argument("--odds-parameter",default="/sports-edge-lab/shared/the-odds-api/key")
    parser.add_argument("--cfbd-parameter",default="/sports-edge-lab/shared/cfbd/key")
    parser.add_argument("--odds-credits",type=int,default=500)
    parser.add_argument("--odds-reserve-floor",type=int,default=100000)
    parser.add_argument("--stats-calls",type=int,default=100)
    parser.add_argument("--max-seconds",type=int,default=600)
    parser.add_argument("--workers",type=int,default=4)
    parser.add_argument("--props-per-track",type=int,default=12)
    parser.add_argument("--hourly-usd",type=float,default=0.461)
    parser.add_argument("--output-dir",default="/opt/ml/processing/output")
    parser.add_argument("--self-test",action="store_true")
    args=parser.parse_args()
    logging.getLogger("boto3").setLevel(logging.ERROR)
    logging.getLogger("botocore").setLevel(logging.ERROR)
    try:
        count=self_test()+current_tests()
        emit("SELF_TEST_PASS",tests=count,workload=VERSION)
        if args.self_test:return 0
        if not (1<=args.odds_credits<=500 and args.odds_reserve_floor>=100000 and 1<=args.stats_calls<=100 and 30<=args.max_seconds<=600
                and 1<=args.workers<=4 and 0<=args.props_per_track<=12):
            raise ValueError("Current acquisition exceeds bounds")
        args.mode,args.until,args.max_response_mb,args.odds_workers="all",None,64,args.workers
        archive=CurrentCapture(args)
        emit("START",run_id=archive.run_id,version=VERSION,current_vintage=archive.vintage,
            max_odds_credits=args.odds_credits,max_stats_calls=args.stats_calls)
        beat=threading.Thread(target=archive.heartbeat,daemon=True)
        beat.start()
        archive.safe_work("lease",archive.acquire_lease)
        if archive.lease_owned:
            archive.safe_work("current_odds",archive.odds_work)
            archive.safe_work("current_cfbd",archive.cfbd_work_current)
            archive.safe_work("current_cbbd",archive.cbbd_work_current)
            archive.release_lease()
        archive.stop.set()
        beat.join(timeout=10)
        return archive.finish()
    except Exception as exc:
        emit("FATAL",error_type=type(exc).__name__)
        return 1


if __name__=="__main__":
    sys.exit(main())
