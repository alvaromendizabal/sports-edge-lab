#!/usr/bin/env python3
"""NFL Edge Lab paid historical odds snapshot planner. Zero paid API calls.

Consumes the owned private S3 game schedule and creates a deduplicated
historical pre-kickoff snapshot plan for The Odds API. No outcome fields
are read or used. NOTE: game clock values are interpreted as US Eastern,
subject to human verification against an official kickoff schedule.
"""
from __future__ import annotations

import argparse
import collections
import csv
import datetime as dt
import hashlib
import io
import json
import sys
import uuid
import zipfile
from zoneinfo import ZoneInfo

VERSION = "nfl-edge-lab-odds-plan-v001-20261015"
REGION = "us-west-2"
BUCKET = "sagemaker-nfl-edge-lab-560403859723-us-west-2"
UTC = dt.timezone.utc
EASTERN = ZoneInfo("America/New_York")


def parse_clock(day, clock):
    if not clock or not day:
        return None
    try:
        date = dt.date.fromisoformat(day)
        bits = clock.strip().split(":")
        if len(bits) != 2:
            return None
        hour, minute = map(int, bits)
        return dt.datetime(date.year, date.month, date.day,
                           hour, minute, tzinfo=EASTERN).astimezone(UTC)
    except (ValueError, TypeError):
        return None


def season_range(spec):
    start, end = map(int, spec.split(":"))
    if not (2020 <= start <= end <= 2026):
        raise ValueError("Seasons must fall in 2020..2026")
    return set(range(start, end+1))


def build_plan(rows, seasons, hours, asof, min_history):
    snapshots = collections.defaultdict(lambda: {"games": set(), "lags": set(), "seasons": set()})
    games = 0
    rejected = collections.Counter()
    for row in rows:
        try:
            season = int(row["season"])
        except (ValueError, KeyError, TypeError):
            rejected["invalid_season"] += 1
            continue
        if season not in seasons:
            continue
        if row.get("game_type") not in ("REG", "WC", "DIV", "CON", "SB"):
            rejected["non_target_game_type"] += 1
            continue
        kickoff = parse_clock(row.get("gameday"), row.get("gametime"))
        if kickoff is None:
            rejected["missing_or_invalid_kickoff"] += 1
            continue
        games += 1
        for lag in hours:
            observed = kickoff - dt.timedelta(hours=lag)
            if observed < min_history:
                rejected["before_vendor_history"] += 1
                continue
            if observed > asof:
                rejected["not_historical_yet"] += 1
                continue
            key = observed.replace(second=0, microsecond=0).isoformat().replace("+00:00", "Z")
            snapshots[key]["games"].add(row.get("game_id", "unknown"))
            snapshots[key]["lags"].add(lag)
            snapshots[key]["seasons"].add(season)
    return ({"utc": key, "games": sorted(value["games"]),
             "lags_hours": sorted(value["lags"]), "seasons": sorted(value["seasons"])}
            for key, value in sorted(snapshots.items())), games, dict(rejected)


def run_test():
    assert parse_clock("2025-09-04", "20:20").isoformat() == "2025-09-05T00:20:00+00:00"
    assert parse_clock("2025-12-04", "20:20").isoformat() == "2025-12-05T01:20:00+00:00"
    assert parse_clock("1999-09-04", "") is None
    assert season_range("2020:2026") == set(range(2020, 2027))
    data = [{"season": "2025", "game_type": "REG", "gameday": "2025-09-07",
             "gametime": "13:00", "game_id": "a"},
            {"season": "2025", "game_type": "REG", "gameday": "2025-09-07",
             "gametime": "13:00", "game_id": "b"}]
    plan, n, issues = build_plan(data, {2025}, [24.0],
                                  dt.datetime(2026, 1, 1, tzinfo=UTC),
                                  dt.datetime(2020, 6, 6, tzinfo=UTC))
    plan = list(plan)
    assert n == 2 and len(plan) == 1 and plan[0]["games"] == ["a", "b"]
    assert not issues
    print(json.dumps({"event": "SELF_TEST_OK", "tests": 6}), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seasons", default="2020:2026")
    parser.add_argument("--lags-hours", default="72,24,6,0.25")
    parser.add_argument("--regions", default="us")
    parser.add_argument("--markets", default="h2h,spreads,totals")
    parser.add_argument("--bucket", default=BUCKET)
    parser.add_argument("--return-dir", default="/opt/ml/processing/report")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    run_test()
    if args.self_test:
        return 0
    lags = [float(x) for x in args.lags_hours.split(",")]
    if not lags or any(x < 0 or x > 336 for x in lags):
        parser.error("lags 0..336h required")
    markets = [x.strip() for x in args.markets.split(",") if x.strip()]
    regions = [x.strip() for x in args.regions.split(",") if x.strip()]
    if not markets or not regions or len(set(markets)) != len(markets):
        parser.error("Unique markets, regions required")
    import boto3
    from pathlib import Path
    s3 = boto3.client("s3", region_name=REGION)
    key = "raw/nfldata/data/games.csv"
    response = s3.get_object(Bucket=args.bucket, Key=key)
    schedule_raw = response["Body"].read()
    reader = csv.DictReader(io.StringIO(schedule_raw.decode("utf-8-sig")))
    required = {"season", "game_type", "gameday", "gametime", "game_id"}
    if not required.issubset(reader.fieldnames or []):
        raise RuntimeError("Unexpected schedule schema: " + str(reader.fieldnames))
    now = dt.datetime.now(UTC)
    min_history = dt.datetime(2020, 6, 6, tzinfo=UTC)
    planned, games, rejects = build_plan(reader, season_range(args.seasons),
                                         lags, now, min_history)
    planned = list(planned)
    estimate_per_request = 10 * len(markets) * len(regions)
    by_season = collections.Counter()
    for item in planned:
        for season in item["seasons"]:
            by_season[str(season)] += 1
    summary = {"version": VERSION,
               "created_utc": now.isoformat(),
               "schedule_s3_uri": f"s3://{args.bucket}/{key}",
               "schedule_sha256": hashlib.sha256(schedule_raw).hexdigest(),
               "seasons": args.seasons,
               "lags_hours": lags,
               "regions": regions,
               "markets": markets,
               "game_rows_with_kickoffs": games,
               "unique_snapshot_requests": len(planned),
               "estimated_credits_per_request": estimate_per_request,
               "estimated_total_credits": len(planned) * estimate_per_request,
               "by_season_snapshots": dict(sorted(by_season.items())),
               "excluded_or_deferred": rejects,
               "notes": [
                   "ESTIMATE ONLY: no paid API calls made; actual vendor credit headers govern",
                   "Kickoff times interpreted as America/New_York; verify schedule semantics before spending",
                   "One featured market request captures multiple events at a given timestamp",
                   "Historical API can return snapshot earlier than requested time",
                   "Snapshot retention/rights subject to subscriber agreement",
               ]}
    from pathlib import Path
    folder = Path(args.return_dir)
    folder.mkdir(parents=True, exist_ok=True)
    run_id = now.strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]
    name = "nfl_edge_lab_odds_plan_" + run_id + ".zip"
    output = folder / name
    payload = json.dumps({"summary": summary, "snapshots": planned},
                         separators=(",", ":")).encode()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("summary.json", json.dumps(summary, indent=2))
        z.writestr("planned_snapshots.json", payload)
    s3_key = "plans/the_odds_api/" + name
    s3.upload_file(str(output), args.bucket, s3_key)
    print(json.dumps({"event": "PLAN_READY", **summary,
                      "return_s3": f"s3://{args.bucket}/{s3_key}"},
                     sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
