#!/usr/bin/env python3
"""Sports Edge Lab paid-data archive. Execute on AWS; never logs credentials.

Raw captures are immutable, content-addressed S3 objects. Request cache entries
are accepted only after a raw capture and receipt have been saved successfully.
This is an acquisition program, not a point-in-time feature builder.
"""
import argparse
import collections
import concurrent.futures
import datetime as dt
import gzip
import hashlib
import io
import itertools
import json
import logging
import os
import queue
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
import zipfile
from pathlib import Path

UTC = dt.timezone.utc
VERSION = "sports-edge-lab-paid-v002"
SPORTS = {
    "nfl": ("americanfootball_nfl", "2020-06-06"),
    "nba": ("basketball_nba", "2020-06-27"),
    "ncaaf": ("americanfootball_ncaaf", "2020-06-06"),
    "ncaam": ("basketball_ncaab", "2020-11-16"),
    "ncaaw": ("basketball_wncaab", "2024-11-12"),
}
HOSTS = {
    "odds": "https://api.the-odds-api.com",
    "cfbd": "https://api.collegefootballdata.com",
    "cbbd": "https://api.collegebasketballdata.com",
}
SOURCE_DOCS = [
    "https://the-odds-api.com/liveapi/guides/v4/",
    "https://the-odds-api.com/historical-odds-data/",
    "https://api.collegefootballdata.com/api/games",
    "https://api.collegefootballdata.com/api/plays",
    "https://api.collegebasketballdata.com/data-availability",
    "https://api.collegebasketballdata.com/api/games",
    "https://api.collegebasketballdata.com/api/plays",
]


def now():
    return dt.datetime.now(UTC)


def iso(value):
    return value.astimezone(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def parse(value):
    return dt.datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)


def blob(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def digest(value):
    return hashlib.sha256(value).hexdigest()


def emit(event, **fields):
    print(json.dumps({"timestamp": iso(now()), "event": event, **fields}, sort_keys=True), flush=True)


def identity(provider, track, endpoint, params, vintage=""):
    if any(k.lower() in {"apikey", "authorization", "token", "key"} for k in params):
        raise ValueError("Secret-like request parameter prohibited from identity")
    return {"provider": provider, "track": track, "endpoint": endpoint,
            "params": dict(sorted(params.items())), "capture_vintage": vintage}


def unique_games(rows):
    return len({str(x.get("gameId", x.get("id", i))) for i, x in enumerate(rows) if isinstance(x, dict)})


class BudgetStop(Exception):
    pass


class Budget:
    """Conservative reservation BEFORE a request; unknown charges stay reserved."""
    def __init__(self, odds_limit, stats_limit):
        self.lock = threading.Lock()
        self.limit = {"odds": odds_limit, "stats": stats_limit}
        self.reserved = {"odds": 0, "stats": 0}
        self.actual_known = {"odds": 0, "stats": 0}
        self.unknown = {"odds": 0, "stats": 0}
        self.providers = {}
        self.disabled = set()

    def reserve(self, provider, amount=None):
        group = "odds" if provider == "odds" else "stats"
        amount = (30 if provider == "odds" else 1) if amount is None else amount
        if not isinstance(amount, int) or amount < 1:
            raise ValueError("Invalid reservation")
        with self.lock:
            if provider in self.disabled:
                raise BudgetStop("provider_disabled")
            if self.reserved[group] + amount > self.limit[group]:
                raise BudgetStop(group + "_budget_exhausted")
            self.reserved[group] += amount
        return group, amount

    def finish(self, provider, reservation, headers):
        group, amount = reservation
        # Every HTTP invocation is a paid-stats call; do not guess refunds.
        actual = 1 if group == "stats" else None
        last = headers.get("x-requests-last")
        if group == "odds" and last is not None:
            try:
                actual = max(0, int(last))
            except (ValueError, TypeError):
                pass
        with self.lock:
            if actual is None:
                self.unknown[group] += amount
            else:
                self.actual_known[group] += actual
                self.reserved[group] += actual - amount
                if actual > amount:
                    self.disabled.add(provider)
            # Headers are provider account totals and may include other jobs.
            old = self.providers.setdefault(provider, {})
            for k, v in headers.items():
                if k in {"x-requests-used", "x-requests-remaining", "x-requests-last", "x-call-limit-remaining"}:
                    try:
                        n = int(v)
                    except (TypeError, ValueError):
                        continue
                    old[k] = min(old.get(k, n), n) if k.endswith("remaining") else max(old.get(k, n), n)
            remaining = old.get("x-requests-remaining", old.get("x-call-limit-remaining"))
            if remaining is not None and remaining < (30 if provider == "odds" else 1):
                self.disabled.add(provider)

    def disable(self, provider):
        with self.lock:
            self.disabled.add(provider)

    def snapshot(self):
        with self.lock:
            return {"limits": dict(self.limit), "reserved_or_known": dict(self.reserved),
                    "actual_known": dict(self.actual_known), "unknown_charge_reserve": dict(self.unknown),
                    "provider_headers": {k: dict(v) for k, v in self.providers.items()},
                    "disabled_providers": sorted(self.disabled)}


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        # Prevent forwarding authentication to another host through redirects.
        return None


class Archive:
    def __init__(self, args):
        import boto3
        from botocore.config import Config
        self.args = args
        self.run_id = now().strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:10]
        self.started = time.monotonic()
        self.deadline = self.started + args.max_seconds
        session = boto3.Session(region_name=args.region)
        config = Config(retries={"total_max_attempts": 4, "mode": "adaptive"},
                        connect_timeout=10, read_timeout=60, max_pool_connections=20)
        self.s3 = session.client("s3", config=config)
        self.ssm = session.client("ssm", config=config)
        self.keys = {}
        # Plaintext exists only in this AWS application runtime. It is never
        # returned through agent tools, printed, persisted, or put into receipts.
        if args.mode in ("all", "odds"):
            self.keys["odds"] = self.ssm.get_parameter(Name=args.odds_parameter, WithDecryption=True)["Parameter"]["Value"]
        if args.mode in ("all", "stats"):
            key = self.ssm.get_parameter(Name=args.cfbd_parameter, WithDecryption=True)["Parameter"]["Value"]
            self.keys["cfbd"] = key
            self.keys["cbbd"] = key
        self.opener = urllib.request.build_opener(NoRedirect)
        self.budget = Budget(args.odds_credits, args.stats_calls)
        self.lock = threading.Lock()
        self.stats = collections.Counter()
        self.receipts = []
        self.failures = []
        self.events = {track: {} for track in SPORTS}
        self.phase = {}
        self.stop = threading.Event()
        self.cache = {}
        self.request_locks = collections.defaultdict(threading.Lock)
        self.blocked_endpoints = set()
        self.blocked_statuses = {403, 404}
        self.seen_checkpoint_requests = set()
        self.coverage = collections.Counter()
        self.day = now().date().isoformat()
        self.end = min(parse(args.until), now() - dt.timedelta(minutes=10)) if args.until else now() - dt.timedelta(minutes=10)

    def time_left(self):
        if self.stop.is_set() or time.monotonic() >= self.deadline:
            raise BudgetStop("time_budget_exhausted")

    def s3_json(self, key):
        try:
            with self.s3.get_object(Bucket=self.args.bucket, Key=key)["Body"] as stream:
                return json.load(stream)
        except self.s3.exceptions.NoSuchKey:
            return None

    def save_json(self, key, value):
        self.s3.put_object(Bucket=self.args.bucket, Key=key, Body=blob(value),
                           ContentType="application/json", ServerSideEncryption="AES256")

    def content(self, receipt):
        with self.s3.get_object(Bucket=self.args.bucket, Key=receipt["raw_key"])["Body"] as stream:
            raw = gzip.decompress(stream.read())
        if digest(raw) != receipt["sha256"]:
            raise RuntimeError("Cached raw hash verification failed")
        return json.loads(raw)

    def count(self, **values):
        with self.lock:
            self.stats.update(values)

    def failure(self, descriptor, reason, **other):
        record = {"request": descriptor, "reason": reason, **other}
        with self.lock:
            self.failures.append(record)
        return None

    def capture(self, provider, track, endpoint, params, label, vintage="", need_data=True):
        self.time_left()
        descriptor = identity(provider, track, endpoint, params, vintage)
        rid = digest(blob(descriptor))
        prefix = "tracks/{}/raw/{}/".format(track, "the-odds-api" if provider == "odds" else provider)
        cache_key = prefix + "request-index/" + rid + ".json"
        with self.request_locks[rid]:
            cached = self.cache.get(rid) or self.s3_json(cache_key)
            if cached and cached.get("status") == 200:
                self.cache[rid] = cached
                self.count(cache_reused=1)
                return self.content(cached) if need_data else True
            if (provider, endpoint) in self.blocked_endpoints:
                return None
            for attempt in range(3):
                self.time_left()
                amount = historical_cost(params) if provider == "odds" else 1
                reservation = self.budget.reserve(provider, amount)
                headers = {"Accept": "application/json", "User-Agent": "SportsEdgeLab/1.0"}
                query = dict(params)
                if provider == "odds":
                    query["apiKey"] = self.keys[provider]
                else:
                    headers["Authorization"] = "Bearer " + self.keys[provider]
                request = urllib.request.Request(HOSTS[provider] + endpoint + "?" + urllib.parse.urlencode(query), headers=headers)
                received_headers = {}
                status, raw, error_type = 0, b"", None
                settle_reservation = True
                try:
                    with self.opener.open(request, timeout=min(50, max(1, self.deadline - time.monotonic()))) as response:
                        status = response.status
                        received_headers = {k.lower(): v for k, v in response.headers.items()}
                        raw = response.read(self.args.max_response_mb * 1024 * 1024 + 1)
                except BudgetStop:
                    # A queued limiter request can be cancelled before HTTP when
                    # another worker receives an access/rate denial. No call was
                    # sent, so undo its reservation and do not count a HTTP call.
                    settle_reservation = False
                    with self.budget.lock:
                        self.budget.reserved[reservation[0]] -= reservation[1]
                    raise
                except urllib.error.HTTPError as exc:
                    status = exc.code
                    received_headers = {k.lower(): v for k, v in exc.headers.items()}
                    # Error bodies can echo credentials. Never capture or log them.
                    exc.close()
                    error_type = "HTTPError"
                except (urllib.error.URLError, TimeoutError, OSError) as exc:
                    error_type = type(exc).__name__
                finally:
                    if settle_reservation:
                        self.budget.finish(provider, reservation, received_headers)
                        self.count(http_calls=1, **{provider + "_http_calls": 1})
                selected = {k: v for k, v in received_headers.items()
                            if k in {"x-requests-last", "x-requests-used", "x-requests-remaining", "x-call-limit-remaining", "content-type", "date"}}
                if status == 200 and len(raw) > self.args.max_response_mb * 1024 * 1024:
                    status, error_type = 0, "ResponseTooLarge"
                if status == 200:
                    # Providers should not echo keys in JSON; do not persist if they do.
                    if any(secret.encode() in raw for secret in self.keys.values() if secret):
                        raise RuntimeError("Credential echo detected; response quarantined without persistence")
                    try:
                        result = json.loads(raw)
                    except (ValueError, UnicodeError):
                        status, error_type = 0, "InvalidJSON"
                receipt = {"version": VERSION, "run_id": self.run_id, "request_id": rid,
                           "request": descriptor, "purpose": label, "retrieved_at": iso(now()),
                           "status": status, "attempt": attempt + 1, "usage_headers": selected,
                           "data_policy": "private_raw_capture_not_pregame_feature_approved"}
                if status == 200:
                    sha = digest(raw)
                    raw_key = prefix + "objects/" + sha[:2] + "/" + sha + ".json.gz"
                    self.s3.upload_fileobj(io.BytesIO(gzip.compress(raw, compresslevel=5, mtime=0)), self.args.bucket, raw_key,
                                           ExtraArgs={"ContentType": "application/json", "ContentEncoding": "gzip",
                                                      "ServerSideEncryption": "AES256", "Metadata": {"sha256": sha}})
                    receipt.update({"raw_key": raw_key, "sha256": sha, "bytes": len(raw),
                                    "records": len(result) if isinstance(result, list) else len(result.get("data", [])) if isinstance(result, dict) and isinstance(result.get("data"), list) else None})
                    receipt_key = prefix + "receipts/" + self.run_id + "/" + rid + ".json"
                    self.save_json(receipt_key, receipt)
                    self.save_json(cache_key, receipt)
                    self.cache[rid] = receipt
                    with self.lock:
                        self.receipts.append({**receipt, "receipt_key": receipt_key})
                        self.stats.update({"captured": 1, "raw_bytes": len(raw), track + "_captured": 1,
                                           provider + "_captured": 1})
                        self.coverage[label] += 1
                    return result if need_data else True
                receipt.update({"error_type": error_type})
                self.save_json(prefix + "failures/" + self.run_id + "/" + rid + "-" + str(attempt) + ".json", receipt)
                if status in (401, 402):
                    self.budget.disable(provider)
                    self.failure(descriptor, "authentication_or_subscription", status=status)
                    raise BudgetStop(provider + "_authentication_or_subscription")
                if status in (400, 403, 404, 422):
                    # Endpoint-level failure does not invalidate another paid service.
                    if status in getattr(self, "blocked_statuses", {403, 404}):
                        self.blocked_endpoints.add((provider, endpoint))
                    return self.failure(descriptor, "endpoint_blocked_or_invalid", status=status)
                if status == 429 or status >= 500 or status == 0:
                    self.count(retryable_incidents=1)
                    if attempt < 2:
                        time.sleep(min(2 ** (attempt + 1), max(0, self.deadline - time.monotonic())))
                        continue
                return self.failure(descriptor, error_type or "http_failure", status=status)

    def odds(self, track, timestamp, label):
        sport = SPORTS[track][0]
        result = self.capture("odds", track, "/v4/historical/sports/" + sport + "/odds",
                              {"date": iso(timestamp), "markets": "h2h,spreads,totals", "regions": "us",
                               "oddsFormat": "decimal", "dateFormat": "iso"}, label)
        if isinstance(result, dict):
            snapshot = result.get("timestamp")
            if snapshot and parse(snapshot) > timestamp:
                self.failure({"track": track, "requested_at": iso(timestamp)}, "future_snapshot_returned", snapshot=snapshot)
                return
            with self.lock:
                for event in result.get("data", []):
                    if event.get("id") and event.get("commence_time"):
                        # Latest-seen schedule is not an assumption of original kickoff.
                        previous = self.events[track].get(event["id"])
                        if previous is None or (snapshot or "") > previous["seen_at_snapshot"]:
                            self.events[track][event["id"]] = {
                                "id": event["id"], "commence_time": event["commence_time"],
                                "home_team": event.get("home_team"), "away_team": event.get("away_team"),
                                "seen_at_snapshot": snapshot or iso(timestamp)}

    def odds_census(self):
        # One fixed UTC timestamp per historical day is a discovery census,
        # not proof of every event/bookmaker or all four pregame horizons.
        schedules = {}
        for track, (_, start) in SPORTS.items():
            cursor = self.end.replace(hour=12, minute=0, second=0, microsecond=0)
            if cursor > self.end:
                cursor -= dt.timedelta(days=1)
            first = parse(start + "T12:00:00Z")
            schedules[track] = []
            while cursor >= first:
                schedules[track].append((track, cursor, "odds_daily_census"))
                cursor -= dt.timedelta(days=1)
        tasks = round_robin(schedules.values())
        self.phase["odds_daily_census"] = {"planned": sum(map(len, schedules.values())), "completed": 0}
        self.parallel_tasks(tasks, self.odds, "odds_daily_census", self.args.odds_workers)

    def odds_checkpoints(self):
        tasks = {}
        event_counts = {}
        for track, events in self.events.items():
            first = parse(SPORTS[track][1] + "T00:00:00Z")
            unique = set()
            for event in events.values():
                kickoff = parse(event["commence_time"])
                for minutes in (15, 360, 1440, 4320):
                    target = kickoff - dt.timedelta(minutes=minutes)
                    if first <= target <= self.end:
                        unique.add(target)
            tasks[track] = [(track, x, "odds_event_derived_checkpoint") for x in sorted(unique, reverse=True)]
            event_counts[track] = len(events)
        self.phase["odds_event_derived_checkpoint"] = {"planned": sum(map(len, tasks.values())), "completed": 0,
                                                       "discovered_events": event_counts,
                                                       "horizons_minutes": [4320, 1440, 360, 15],
                                                       "requires_schedule_and_quote_timestamp_audit": True}
        self.parallel_tasks(round_robin(tasks.values()), self.odds, "odds_event_derived_checkpoint", self.args.odds_workers)

    def parallel_tasks(self, tasks, fn, phase, workers):
        pending = set()
        iterator = iter(tasks)
        exhausted = False
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
            while pending or not exhausted:
                self.time_left()
                while len(pending) < workers and not exhausted:
                    try:
                        item = next(iterator)
                    except StopIteration:
                        exhausted = True
                        break
                    pending.add(pool.submit(fn, *item))
                if not pending:
                    break
                done, pending = concurrent.futures.wait(pending, timeout=1, return_when=concurrent.futures.FIRST_COMPLETED)
                for future in done:
                    future.result()
                    self.phase[phase]["completed"] += 1
        self.phase[phase]["status"] = "planned_requests_processed"

    def stats_capture(self, provider, endpoint, params, label, need_data=False):
        track = "ncaaf" if provider == "cfbd" else "ncaam"
        # Completed historical slices remain cached between days. Ongoing
        # seasons/reference feeds receive a daily vintage for new observations.
        year = params.get("season", params.get("year"))
        current_season = self.end.year + (provider == "cbbd" and self.end.month >= 7)
        vintage = self.day if year is None or year >= current_season else ""
        if params.get("date") and params["date"] < (self.end - dt.timedelta(days=7)).date().isoformat():
            vintage = ""
        return self.capture(provider, track, endpoint, params, label, vintage, need_data)

    def cb_slice(self, endpoint, season, start, end, label):
        if start > self.end:
            return []
        params = {"season": season, "startDateRange": iso(start), "endDateRange": iso(end)}
        result = self.stats_capture("cbbd", endpoint, params, label, True)
        if not isinstance(result, list):
            return []
        limit = 1000 if endpoint == "/games/players" else 3000
        if unique_games(result) >= limit or len(result) >= limit:
            if (end - start).total_seconds() <= 60:
                self.failure(identity("cbbd", "ncaam", endpoint, params), "response_cap_unresolved")
                return result
            middle = start + (end - start) / 2
            # Inclusive boundaries intentionally overlap; downstream dedup by
            # game/player IDs is required and never discards a boundary event.
            return self.cb_slice(endpoint, season, start, middle, label) + self.cb_slice(endpoint, season, middle, end, label)
        return result

    def cfbd_work(self):
        self.phase["cfbd"] = {"status": "running", "seasons": [2000, self.end.year]}
        for endpoint in ("/info", "/teams", "/conferences", "/venues", "/plays/types", "/stats/categories"):
            self.stats_capture("cfbd", endpoint, {}, "cfbd_reference")
        calendars = []
        for year in range(self.end.year, 1999, -1):
            params = {"year": year}
            self.stats_capture("cfbd", "/games", {**params, "seasonType": "both"}, "cfbd_games")
            rows = self.stats_capture("cfbd", "/calendar", params, "cfbd_calendar", True)
            calendars.extend((year, row["week"], row.get("seasonType", "regular"))
                             for row in rows or [] if isinstance(row, dict) and "week" in row)
            for endpoint in ("/lines", "/records", "/rankings", "/stats/season", "/stats/player/season",
                             "/stats/season/advanced", "/ratings/srs", "/ratings/elo", "/ppa/teams", "/ppa/players/season",
                             "/recruiting/players", "/recruiting/teams", "/player/portal", "/draft/picks",
                             "/roster", "/talent", "/coaches", "/player/usage", "/player/returning"):
                self.stats_capture("cfbd", endpoint, params, "cfbd_season" + endpoint)
        self.phase["cfbd"]["weekly_slices"] = len(set(calendars))
        for year, week, season_type in sorted(set(calendars), reverse=True):
            if year < 2001 or season_type not in ("regular", "postseason", "spring_regular", "spring_postseason"):
                continue
            params = {"year": year, "week": week, "seasonType": season_type}
            for endpoint in ("/plays", "/drives", "/games/teams", "/games/players", "/stats/game/advanced"):
                self.stats_capture("cfbd", endpoint, params, "cfbd_weekly" + endpoint)
        self.phase["cfbd"]["status"] = "planned_requests_processed"

    def cbbd_work(self):
        self.phase["cbbd"] = {"status": "running", "seasons": [2003, self.end.year + 1]}
        # Validate the actual authenticated games endpoint; CBBD has no /info.
        self.stats_capture("cbbd", "/games", {"season": self.end.year, "startDateRange": str(self.end.year) + "-03-01T00:00:00Z", "endDateRange": str(self.end.year) + "-03-02T00:00:00Z"}, "cbbd_access_canary")
        if ("cbbd", "/games") in self.blocked_endpoints:
            self.phase["cbbd"]["status"] = "games_endpoint_blocked"
            return
        for endpoint in ("/teams", "/conferences", "/venues", "/plays/types", "/lines/providers"):
            self.stats_capture("cbbd", endpoint, {}, "cbbd_reference")
        play_dates = set()
        lineup_ids = set()
        for season in range(self.end.year + 1, 2002, -1):
            team_stats = self.stats_capture("cbbd", "/stats/team/season", {"season": season}, "cbbd_season/stats/team/season", True)
            for endpoint in ("/stats/player/season", "/ratings/srs", "/ratings/elo", "/ratings/adjusted",
                             "/rankings", "/teams/roster"):
                self.stats_capture("cbbd", endpoint, {"season": season}, "cbbd_season" + endpoint)
            for selector in shooting_selectors(team_stats):
                for endpoint in ("/stats/team/shooting/season", "/stats/player/shooting/season"):
                    self.stats_capture("cbbd", endpoint, {"season": season, **selector}, "cbbd_season" + endpoint)
            for endpoint in ("/recruiting/players", "/recruiting/teams", "/recruiting/portal", "/draft/picks"):
                self.stats_capture("cbbd", endpoint, {"year": season}, "cbbd_season" + endpoint)
            # All twelve months account for atypical calendars and postponements.
            for start, end in season_months(season):
                rows = self.cb_slice("/games", season, start, end, "cbbd_games")
                for row in rows:
                    if row.get("startDate"):
                        when = parse(row["startDate"])
                        if when <= self.end and (season >= 2006 or season == 2003):
                            play_dates.add(when.date().isoformat())
                    if season >= 2024 and row.get("id"):
                        lineup_ids.add((season, row["id"]))
                for endpoint in ("/games/teams", "/games/players", "/lines"):
                    self.cb_slice(endpoint, season, start, end, "cbbd_boxscores" + endpoint)
        self.phase["cbbd"]["play_dates_planned"] = len(play_dates)
        for day in sorted(play_dates, reverse=True):
            self.stats_capture("cbbd", "/plays/date", {"date": day}, "cbbd_daily_plays")
        for season, game_id in sorted(lineup_ids, reverse=True):
            for path in ("/lineups/game/", "/substitutions/game/"):
                self.stats_capture("cbbd", path + str(game_id), {}, "cbbd_lineups_substitutions")
        self.phase["cbbd"]["status"] = "planned_requests_processed"

    def safe_work(self, name, function):
        try:
            function()
        except BudgetStop as exc:
            self.phase.setdefault(name, {})["status"] = "bounded_stop"
            self.phase[name]["reason"] = str(exc)
            emit("WORKSTREAM_STOP", workstream=name, reason=str(exc))
        except Exception as exc:
            # The exception text/traceback might include a credential URL.
            self.phase.setdefault(name, {})["status"] = "failed"
            self.phase[name]["error_type"] = type(exc).__name__
            self.failure({"workstream": name}, "unhandled_runtime_error", error_type=type(exc).__name__)
            emit("WORKSTREAM_ERROR", workstream=name, error_type=type(exc).__name__)

    def odds_work(self):
        self.odds_census()
        self.checkpoint()
        self.odds_checkpoints()

    def summary(self):
        elapsed = time.monotonic() - self.started
        with self.lock:
            stats, failures, phases = dict(self.stats), len(self.failures), dict(self.phase)
            events = {k: len(v) for k, v in self.events.items()}
            coverage = dict(self.coverage)
        return {"version": VERSION, "run_id": self.run_id, "timestamp": iso(now()),
                "elapsed_seconds": round(elapsed, 2), "compute_estimate_usd": round(elapsed / 3600 * self.args.hourly_usd, 4),
                "compute_rate_usd_per_hour": self.args.hourly_usd,
                "compute_estimate_excludes_storage_requests_and_subscription": True,
                "statistics": stats, "failures_count": failures, "phases": phases,
                "budget": self.budget.snapshot(), "discovered_odds_events": events, "capture_coverage": coverage,
                "until": iso(self.end), "bucket": self.args.bucket,
                "scope": "US bookmaker featured markets; direct CFBD/CBBD stats; private raw archive",
                "not_completed_by_this_runner": ["player_props", "non_US_regions", "bookmaker_full_intraday_tape", "odds_schedule_completeness_audit", "point_in_time_feature_approval", "forecast_training"],
                "data_notes": ["End-of-season ratings and postgame data are not pregame features.",
                               "Daily odds census can omit events absent at 12:00 UTC.",
                               "Event-derived checkpoints require kickoff revision and bookmaker last_update auditing.",
                               "Snapshot API may return the closest available snapshot at or before request.",
                               "CBBD is the men's basketball statistical track; women's stats come from other sources.",
                               "No claim of complete source or season coverage follows from HTTP success."],
                "official_documentation": SOURCE_DOCS}

    def checkpoint(self):
        summary = self.summary()
        prefix = "shared/acquisition/paid/" + self.run_id
        self.save_json(prefix + "/progress.json", summary)
        with self.lock:
            events = {k: list(v.values()) for k, v in self.events.items()}
        self.save_json(prefix + "/discovered-events.json", events)
        return summary

    def heartbeat(self):
        while not self.stop.wait(30):
            try:
                summary = self.checkpoint()
                emit("HEARTBEAT", run_id=self.run_id, seconds=summary["elapsed_seconds"],
                     compute_estimate_usd=summary["compute_estimate_usd"], statistics=summary["statistics"],
                     budget=summary["budget"], phases=summary["phases"])
            except Exception as exc:
                emit("CHECKPOINT_ERROR", error_type=type(exc).__name__)

    def finish(self):
        self.stop.set()
        summary = self.checkpoint()
        prefix = "shared/acquisition/paid/" + self.run_id
        self.save_json(prefix + "/summary.json", summary)
        self.save_json(prefix + "/failures.json", self.failures)
        self.save_json(prefix + "/receipts.json", self.receipts)
        out = Path(self.args.output_dir)
        out.mkdir(parents=True, exist_ok=True)
        name = "sports_edge_lab_paid_return_" + self.run_id + ".zip"
        with zipfile.ZipFile(out / name, "w", zipfile.ZIP_DEFLATED) as bundle:
            bundle.writestr("summary.json", blob(summary))
            bundle.writestr("failures.json", blob(self.failures))
            bundle.writestr("receipts.json", blob(self.receipts))
            bundle.writestr("readme.txt", "Raw paid data remains private in S3. This compact return contains metadata and evidence.\n")
        self.s3.upload_file(str(out / name), self.args.bucket, prefix + "/" + name,
                            ExtraArgs={"ServerSideEncryption": "AES256"})
        emit("COMPLETE", run_id=self.run_id, summary_s3="s3://" + self.args.bucket + "/" + prefix + "/summary.json",
             return_zip=name, statistics=summary["statistics"], failures_count=len(self.failures), budget=summary["budget"])
        return 1 if any(x.get("status") == "failed" for x in self.phase.values()) else 0


def round_robin(iterables):
    iterators = collections.deque(iter(x) for x in iterables)
    while iterators:
        iterator = iterators.popleft()
        try:
            yield next(iterator)
            iterators.append(iterator)
        except StopIteration:
            pass


def historical_cost(params):
    markets = set(filter(None, str(params.get("markets", "h2h,spreads,totals")).split(",")))
    regions = set(filter(None, str(params.get("regions", "us")).split(",")))
    if not markets or not regions or "bookmakers" in params:
        raise ValueError("Explicit supported market/region budgeting required")
    return 10 * len(markets) * len(regions)


def shooting_selectors(rows):
    conferences, independent_teams = set(), set()
    for row in rows or []:
        if not isinstance(row, dict):
            continue
        conference = row.get("conference")
        if isinstance(conference, dict):
            conference = conference.get("abbreviation")
        if conference:
            conferences.add(conference)
        elif row.get("team"):
            independent_teams.add(row["team"])
    return ([{"conference": x} for x in sorted(conferences)] +
            [{"team": x} for x in sorted(independent_teams)])


def season_months(season):
    start = dt.datetime(season - 1, 7, 1, tzinfo=UTC)
    for _ in range(12):
        end = dt.datetime(start.year + (start.month == 12), 1 if start.month == 12 else start.month + 1, 1, tzinfo=UTC)
        yield start, end
        start = end


def self_test():
    import unittest

    class Checks(unittest.TestCase):
        def test_order_invariant_identity(self):
            self.assertEqual(digest(blob(identity("cfbd", "ncaaf", "/games", {"year": 2025, "week": 2}))),
                             digest(blob(identity("cfbd", "ncaaf", "/games", {"week": 2, "year": 2025}))))

        def test_secret_rejected(self):
            with self.assertRaises(ValueError):
                identity("odds", "nfl", "/odds", {"apiKey": "fake-secret"})

        def test_atomic_limit(self):
            b = Budget(90, 3)
            with concurrent.futures.ThreadPoolExecutor(max_workers=20) as pool:
                def reserve(_):
                    try:
                        b.reserve("odds")
                        return True
                    except BudgetStop:
                        return False
                self.assertEqual(sum(pool.map(reserve, range(50))), 3)
            self.assertEqual(b.snapshot()["reserved_or_known"]["odds"], 90)

        def test_usage_zero_and_missing(self):
            b = Budget(60, 1)
            b.finish("odds", b.reserve("odds"), {"x-requests-last": "0"})
            b.finish("odds", b.reserve("odds"), {})
            self.assertEqual(b.snapshot()["reserved_or_known"]["odds"], 30)
            self.assertEqual(b.snapshot()["unknown_charge_reserve"]["odds"], 30)

        def test_shared_stats_budget(self):
            b = Budget(30, 1)
            b.reserve("cfbd")
            with self.assertRaises(BudgetStop):
                b.reserve("cbbd")

        def test_unexpected_credit_cost_disables(self):
            b = Budget(100, 10)
            b.finish("odds", b.reserve("odds"), {"x-requests-last": "40"})
            with self.assertRaises(BudgetStop):
                b.reserve("odds")

        def test_calendar_boundaries(self):
            months = list(season_months(2026))
            self.assertEqual(len(months), 12)
            self.assertEqual(iso(months[0][0]), "2025-07-01T00:00:00Z")
            self.assertEqual(iso(months[-1][1]), "2026-07-01T00:00:00Z")
            self.assertTrue(all(a[1] == b[0] for a, b in zip(months, months[1:])))

        def test_fair_interleave(self):
            self.assertEqual(list(round_robin([[1, 3, 5], [2, 4]])), [1, 2, 3, 4, 5])

        def test_nested_teams_count_games(self):
            self.assertEqual(unique_games([{"gameId": 1}, {"gameId": 1}, {"gameId": 2}]), 2)

        def test_gzip_hash_roundtrip(self):
            raw = blob({"data": [{"id": "x"}]})
            self.assertEqual(digest(gzip.decompress(gzip.compress(raw, mtime=0))), digest(raw))

        def test_cbbd_cap_splits_and_preserves_boundary(self):
            archive = Archive.__new__(Archive)
            archive.end = parse("2026-04-01T00:00:00Z")
            calls = []
            def capture(provider, endpoint, params, label, need_data):
                calls.append(params)
                if len(calls) == 1:
                    return [{"id": n} for n in range(3000)]
                return [{"id": len(calls)}]
            archive.stats_capture = capture
            rows = archive.cb_slice("/games", 2026, parse("2026-03-01T00:00:00Z"), parse("2026-03-02T00:00:00Z"), "test")
            self.assertEqual(len(calls), 3)
            self.assertEqual(len(rows), 2)
            self.assertEqual(calls[1]["endDateRange"], calls[2]["startDateRange"])

        def test_completed_stats_cache_stable(self):
            archive = Archive.__new__(Archive)
            archive.end = parse("2026-10-16T00:00:00Z")
            archive.day = "2026-10-16"
            calls = []
            archive.capture = lambda *args: calls.append(args)
            archive.stats_capture("cfbd", "/games", {"year": 2025}, "test")
            archive.stats_capture("cfbd", "/games", {"year": 2026}, "test")
            archive.stats_capture("cbbd", "/games", {"season": 2026}, "test")
            self.assertEqual([x[5] for x in calls], ["", "2026-10-16", ""])

        def test_future_odds_snapshot_quarantined(self):
            archive = Archive.__new__(Archive)
            archive.capture = lambda *args, **kw: {"timestamp": "2025-01-02T00:00:00Z", "data": [{"id": "bad", "commence_time": "2025-01-03T00:00:00Z"}]}
            failures = []
            archive.failure = lambda *args, **kw: failures.append((args, kw))
            archive.odds("nfl", parse("2025-01-01T00:00:00Z"), "test")
            self.assertEqual(len(failures), 1)

        def test_dynamic_market_cost(self):
            self.assertEqual(historical_cost({"markets": "player_points,player_rebounds,player_points", "regions": "us,us2"}), 40)
            b = Budget(120, 0)
            b.reserve("odds", 60)
            b.reserve("odds", 60)
            with self.assertRaises(BudgetStop):
                b.reserve("odds", 60)

        def test_shooting_requires_conference_or_team(self):
            selectors = shooting_selectors([{"conference": "ACC", "team": "Duke"}, {"conference": "ACC", "team": "North Carolina"}, {"conference": None, "team": "Independent"}])
            self.assertEqual(selectors, [{"conference": "ACC"}, {"team": "Independent"}])

    result = unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.loadTestsFromTestCase(Checks))
    if not result.wasSuccessful():
        raise RuntimeError("Self-test gate failed")
    return result.testsRun


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bucket", default="sagemaker-sports-edge-lab-560403859723-us-west-2")
    parser.add_argument("--region", default="us-west-2")
    parser.add_argument("--mode", choices=["all", "odds", "stats"], default="all")
    parser.add_argument("--odds-parameter", default="/sports-edge-lab/shared/the-odds-api/key")
    parser.add_argument("--cfbd-parameter", default="/sports-edge-lab/shared/cfbd/key")
    parser.add_argument("--odds-credits", type=int, default=1000000)
    parser.add_argument("--stats-calls", type=int, default=15000)
    parser.add_argument("--max-seconds", type=int, default=6900)
    parser.add_argument("--odds-workers", type=int, default=4)
    parser.add_argument("--max-response-mb", type=int, default=256)
    parser.add_argument("--hourly-usd", type=float, default=0.484)
    parser.add_argument("--output-dir", default="/opt/ml/processing/output")
    parser.add_argument("--until")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    logging.getLogger("boto3").setLevel(logging.ERROR)
    logging.getLogger("botocore").setLevel(logging.ERROR)
    try:
        count = self_test()
        emit("SELF_TEST_PASS", tests=count)
        if args.self_test:
            return 0
        if not (0 <= args.odds_credits <= 1000000 and 0 <= args.stats_calls <= 15000 and 30 <= args.max_seconds <= 7000 and 1 <= args.odds_workers <= 6):
            raise ValueError("Requested bounds exceed authorized milestone limits")
        archive = Archive(args)
        emit("START", run_id=archive.run_id, mode=args.mode, limits=archive.budget.snapshot()["limits"])
        beat = threading.Thread(target=archive.heartbeat, daemon=True)
        beat.start()
        work = []
        if args.mode in ("all", "odds"):
            work.append(("odds", archive.odds_work))
        if args.mode in ("all", "stats"):
            work.extend([("cfbd", archive.cfbd_work), ("cbbd", archive.cbbd_work)])
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(work)) as pool:
            futures = [pool.submit(archive.safe_work, name, fn) for name, fn in work]
            for future in futures:
                future.result()
        archive.stop.set()
        beat.join(timeout=10)
        return archive.finish()
    except Exception as exc:
        # Never output exception text or traceback: HTTP objects may contain keys.
        emit("FATAL", error_type=type(exc).__name__)
        return 1


if __name__ == "__main__":
    sys.exit(main())
