"""Credential-free NFL accounting and coordinator-contract demonstration.

The toy ledger is invented. Public real-run aggregates are validated separately;
this module does not reproduce private training, access AWS, or acquire data.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECTS = {"nfl", "ncaa_fbs", "nba", "ncaa_basketball"}
SUBDIRECTORIES = {"src", "config", "data", "runs", "notebooks", "reports", "releases", "archive"}
NFL_WEEKS = tuple(map(str, range(1, 19))) + ("WC", "DIV", "CON", "SB")
PROVIDERS = ("DraftKings", "Underdog", "PrizePicks", "Kalshi", "Polymarket")


def canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def reconcile_games(schedule, prediction_ids, *, season, target):
    """Outer-universe accounting; the season field governs postseason dates."""
    require(target in {"win", "margin", "total"}, "Unknown target")
    ids = [row["game_id"] for row in schedule]
    require(len(ids) == len(set(ids)), "Duplicate schedule identity")
    predictions = list(prediction_ids)
    require(len(predictions) == len(set(predictions)), "Duplicate prediction identity")
    require(set(predictions) <= set(ids), "Prediction outside schedule universe")
    result = {"season": season, "target": target, "accounted": 0, "scored": 0,
        "regular": 0, "postseason": 0, "ties": 0, "canceled": 0, "unplayed": 0,
        "eligible": 0, "predicted_eligible": 0, "missing_prediction": 0, "rows": []}
    for row in schedule:
        require(row["phase"] in {"REG", "POST"}, "Unknown phase")
        require(type(row["season"]) is int, "Football season must be explicit")
        home, away = row.get("home_score"), row.get("away_score")
        require((home is None) == (away is None), "Partial score pair")
        require(all(value is None or (type(value) in (int, float) and math.isfinite(value) and value >= 0) for value in (home, away)), "Invalid score")
        if row["season"] != season:
            continue
        result["accounted"] += 1
        result["regular" if row["phase"] == "REG" else "postseason"] += 1
        if row.get("canceled"):
            require(home is None, "Canceled event cannot have invented final scores")
            result["canceled"] += 1; status = "CANCELED"
        elif home is None:
            result["unplayed"] += 1; status = "UNPLAYED"
        else:
            result["scored"] += 1
            tie = home == away
            result["ties"] += int(tie)
            if target == "win" and tie:
                status = "TIE_OUTSIDE_CONDITIONAL_BINARY_TARGET"
            else:
                result["eligible"] += 1
                if row["game_id"] in predictions:
                    result["predicted_eligible"] += 1; status = "PREDICTION_PRESENT"
                else:
                    result["missing_prediction"] += 1; status = "SCORED_WITHOUT_PREDICTION"
        result["rows"].append({"game_id": row["game_id"], "status": status})
    require(result["accounted"] == result["scored"] + result["canceled"] + result["unplayed"], "Accounting closure failed")
    return result


def admit_coordinator(document, *, filename):
    """Illustrative semantic check, not a real filesystem lock implementation."""
    if (not isinstance(document, dict) or document.get("schema") != "sports-edge-lab.workspace-layout.v1"
            or type(document.get("layout_version")) is not int or document["layout_version"] != 1):
        return {"status": "DEFERRED_UNKNOWN_CONTRACT", "mutation_allowed": False}
    projects = document.get("project_directories", [])
    directories = document.get("required_project_subdirectories", [])
    if (not isinstance(projects, list) or len(projects) != len(PROJECTS)
            or not all(isinstance(item, str) for item in projects) or set(projects) != PROJECTS
            or not isinstance(directories, list) or len(directories) != len(SUBDIRECTORIES)
            or not all(isinstance(item, str) for item in directories) or set(directories) != SUBDIRECTORIES):
        return {"status": "DEFERRED_LAYOUT_CONFLICT", "mutation_allowed": False}
    lock = document.get("organization_lock")
    if not isinstance(lock, str) or not re.fullmatch(r"\.[A-Za-z0-9_-]+\.lock", lock):
        return {"status": "DEFERRED_LOCK_CONTRACT", "mutation_allowed": False}
    return {"status": "RECOGNIZED_REQUIRES_ACTUAL_LOCK", "mutation_allowed": False,
        "observed_filename": filename, "advertised_lock": lock, "document_sha256": digest(document),
        "next_gate": "Acquire the actual advertised lock, then recheck the document identity before any mutation."}


def compare_panel(challenger, market):
    for key in ("season", "target", "policy", "games", "cohort_sha256"):
        require(challenger.get(key) == market.get(key), "Matched-cohort identity differs: " + key)
    require(type(challenger["games"]) is int and challenger["games"] > 0, "Invalid matched sample size")
    delta = {}
    for metric, reference in market["metrics"].items():
        value = challenger["metrics"].get(metric)
        require(type(value) in (int, float) and math.isfinite(value), "Missing/nonfinite challenger metric")
        require(type(reference) in (int, float) and math.isfinite(reference), "Missing/nonfinite MARKET metric")
        delta[metric] = value - reference
    return {"delta": delta, "ranking_permitted": challenger["season"] < 2026,
        "promotion_authorized": False, "qualification": "Separate complete historical family required"}


def validate_weekly_review(review, seasons):
    """Check dated aggregate closure; no new forecasts or provider admission."""
    require(review.get("schema") == "sports-edge-lab.nfl.public-weekly-review.v1", "Unknown weekly schema")
    require(review.get("historical_owner_release") == "N006", "Weekly source is historical N006")
    require(review.get("new_forecasts") == review.get("provider_calls") == review.get("new_estimator_fits") == 0,
            "Aggregate reanalysis cannot become new forecasts or fits")
    require(review.get("schedule_observed_at_utc") == "2026-10-29T19:38:19.361649+00:00", "Dated schedule identity changed")
    require(review.get("saved_availability_semantics") == "UNION_OF_REGISTERED_SAVED_PANELS_NOT_ISSUED_FORECASTS",
            "Saved availability must not become issued forecasts")
    expected = {(season, week) for season in (2024, 2025, 2026) for week in NFL_WEEKS}
    rows, providers = review["weeks"], review["provider_weeks"]
    require(len(rows) == 66, "Expected all 66 NFL season/week slots")
    indexed = {}
    count_fields = ("games_scheduled", "games_scored", "ties", "canceled", "unplayed_from_capture",
                    "unscored_status_unknown", "saved_win_binary", "saved_margin", "saved_total")
    unknown_fields = ("forecast_issued_verified", "forecastable_verified", "settled_profit", "roi",
                      "cumulative_profit", "drawdown", "clv")
    fields = set(count_fields + unknown_fields + ("season", "nfl_week", "schedule_status",
                  "expected_postseason_games_by_format", "economic_status"))
    for row in rows:
        require(set(row) == fields, "Unknown weekly field")
        require(type(row["season"]) is int and type(row["nfl_week"]) is str, "NFL season/week identity must be explicit")
        key = (row["season"], row["nfl_week"])
        require(key in expected and key not in indexed, "Duplicate or unsupported NFL season/week")
        indexed[key] = row
        require(all(type(row[k]) is int and row[k] >= 0 for k in count_fields), "Invalid weekly count")
        require(row["games_scheduled"] == sum(row[k] for k in
            ("games_scored", "canceled", "unplayed_from_capture", "unscored_status_unknown")), "Weekly status closure differs")
        require(row["ties"] <= row["games_scored"], "Weekly ties exceed scored games")
        require(row["saved_win_binary"] <= row["games_scored"] - row["ties"] and
                all(row[k] <= row["games_scored"] for k in ("saved_margin", "saved_total")), "Saved predictions exceed target eligibility")
        require(all(row[k] is None for k in unknown_fields), "Unknown forecasts or economics cannot become zero")
        require(row["economic_status"] == "ISSUED_PICKS_AND_SETTLEMENTS_NOT_VERIFIED", "Settlement qualification changed")
        future = key[0] == 2026 and key[1] in ("WC", "DIV", "CON", "SB")
        if future:
            require(all(row[k] == 0 for k in count_fields), "Future postseason cannot invent matchups or results")
            require(row["schedule_status"] == "NO_CAPTURED_MATCHUPS_NO_IDS_INVENTED" and
                    row["expected_postseason_games_by_format"] == {"WC": 6, "DIV": 4, "CON": 2, "SB": 1}[key[1]],
                    "Future postseason format differs")
        else:
            require(row["schedule_status"] == "CAPTURED_GAME_ROWS" and
                    row["expected_postseason_games_by_format"] == {"WC": 6, "DIV": 4, "CON": 2, "SB": 1}.get(key[1]),
                    "Captured schedule state changed")
    require(set(indexed) == expected, "Missing NFL season/week slot")
    for year in (2024, 2025, 2026):
        selected = [r for r in rows if r["season"] == year]
        for weekly, yearly in (("games_scheduled", "accounted"), ("games_scored", "scored"), ("ties", "ties"),
                               ("canceled", "canceled"), ("unplayed_from_capture", "unplayed"),
                               ("saved_win_binary", "retained"), ("saved_margin", "retained"), ("saved_total", "retained")):
            require(sum(r[weekly] for r in selected) == seasons[year][yearly], "Weekly and season aggregates disagree: " + weekly)
        require(sum(r["games_scheduled"] for r in selected if r["nfl_week"].isdigit()) == seasons[year]["regular"],
                "NFL regular-season denominator differs")
        require(sum(r["games_scheduled"] for r in selected if not r["nfl_week"].isdigit()) == seasons[year]["postseason"],
                "NFL postseason denominator differs")
    expected_providers = {(year, week, provider) for year, week in expected for provider in PROVIDERS}
    require(len(providers) == 330, "Expected all 330 provider/week states")
    keys = set()
    provider_unknowns = ("matched_games", "coverage_fraction", "brier", "log_loss", "settled_profit", "roi")
    for row in providers:
        require(set(row) == set(provider_unknowns + ("season", "nfl_week", "games_scheduled", "provider", "quote_status")),
                "Unknown provider field")
        key = (row["season"], row["nfl_week"], row["provider"])
        require(key in expected_providers and key not in keys, "Duplicate or unsupported provider/week")
        keys.add(key)
        require(type(row["games_scheduled"]) is int and row["games_scheduled"] == indexed[key[:2]]["games_scheduled"],
                "Provider denominator differs")
        require(row["quote_status"] == "NO_VERIFIED_QUOTE" and all(row[k] is None for k in provider_unknowns),
                "Unknown provider evidence cannot become generic MARKET performance")
    require(keys == expected_providers, "Missing provider/week state")
    return {"season_week_slots": 66, "provider_week_slots": 330, "new_forecasts": 0, "provider_calls": 0}


def validate_owner_attempt(data):
    """Historical record arithmetic; this does not observe current storage."""
    attempt = data["n008_owner_attempt"]
    require(data["owner_latest_success"] == "N006" and data["owner_latest_attempt"] == "N008", "Owner release boundary changed")
    require(data["next_owner_execution"] == {"release": "N009", "verified": False}, "Pending owner work cannot become executed")
    require(attempt["status"] == "FAILED_FIRST_STORAGE_GUARD_BEFORE_SCIENCE" and attempt["worker_started"] is True,
            "N008 failure stage changed")
    require(attempt["new_n004_fits"] is None and all(attempt[k] is False for k in
        ("tests_reached", "parent_admission_reached", "coverage_refresh_reached", "n004_science_reached", "persistence_reached")),
        "Unreached N008 science cannot become completed work")
    storage = attempt["storage"]
    require(storage["observed_at_utc"] == "2026-10-29T22:11:59.328807+00:00" and storage["live_observation"] is False,
            "Historical storage cannot become live telemetry")
    for key in ("total_bytes", "used_bytes", "available_bytes", "research_reserve_bytes", "available_inodes"):
        require(type(storage[key]) is int and storage[key] >= 0, "Invalid historical storage count")
    require(storage["total_bytes"] == storage["used_bytes"] + storage["available_bytes"], "Historical storage arithmetic differs")
    require(storage["research_reserve_bytes"] == max(512 * 1024 * 1024, (3 * storage["total_bytes"] + 99) // 100) and
            storage["available_bytes"] < storage["research_reserve_bytes"], "Historical reserve boundary differs")
    require(attempt["owner_cleanup_verified"] is False and attempt["archive_payloads_verified"] == 33,
            "N008 archive audit cannot become owner cleanup")


def validate_evidence(data):
    require(data.get("schema") == "sports-edge-lab.nfl.public-review.v1", "Unknown public evidence schema")
    require(data.get("accepted_reference") == "MARKET", "Reference identity changed")
    require(data.get("prediction_tables") == len(data["rows"]) == 316, "Prediction-table closure differs")
    require(sum(len(row["metrics"]) for row in data["rows"]) == data["recomputed_scalars"] == 948, "Metric-scalar closure differs")
    seasons = {row["season"]: row for row in data["seasons"]}
    require(len(seasons) == len(data["seasons"]) == 28 and set(seasons) == set(range(1999, 2027)), "Season universe differs")
    require(sum(row["accounted"] for row in seasons.values()) == data["all_accounted_games"] == 7549, "All-game accounting differs")
    for year, row in seasons.items():
        require(row["regular"] + row["postseason"] == row["accounted"], "Phase accounting differs")
        require(row["scored"] + row["canceled"] + row["unplayed"] == row["accounted"], "Status accounting differs")
        require(row["ties"] <= row["scored"], "Tie accounting differs")
    for year, cohort in ((2024, 280), (2025, 277)):
        require(seasons[year]["accounted"] == 285 and seasons[year]["retained"] == cohort, "Full season and saved cohort were conflated")
    require(seasons[2026]["scored"] == 107 and seasons[2026]["unplayed"] == 165 and seasons[2026]["retained"] == 77, "Monitoring/unplayed boundary changed")
    keys, groups = set(), {}
    for row in data["rows"]:
        require(re.fullmatch(r"N00[23]-[a-f0-9]{10}", row["model_id"]), "Unstable model identifier")
        require(re.fullmatch(r"[a-f0-9]{64}", row["cohort_sha256"]), "Missing cohort identity")
        require(row["season"] in (2024, 2025, 2026), "Unsupported result season")
        require((row["season"] == 2026) == (row["policy"] == "monitoring"), "Exposed monitoring policy changed")
        key = tuple(row[field] for field in ("season", "target", "policy", "model_id"))
        require(key not in keys, "Duplicate result identity"); keys.add(key)
        for value in row["metrics"].values():
            require(type(value) in (int, float) and math.isfinite(value), "Nonfinite metric")
        panel = {field: row[field] for field in ("season", "target", "policy", "games", "cohort_sha256")}
        panel["metrics"] = row["market_metrics"]
        group = tuple(row[field] for field in ("season", "target", "policy"))
        require(group not in groups or groups[group] == panel, "One panel mixes MARKET cohorts")
        groups[group] = panel
        compare_panel(row, panel)
    require(data["qualification"]["passed"] == 0 and data["qualification"]["n003_corrected_comparisons"] == 522, "Qualification boundary changed")
    weekly = validate_weekly_review(data["weekly_review"], seasons)
    validate_owner_attempt(data)
    text = canonical(data).decode()
    require(not re.search(r"/home/|/tmp/|/workspace/|s3://|arn:aws:|AKIA[A-Z0-9]{16}|ASIA[A-Z0-9]{16}|api[_-]?key|password|credential_value", text, re.I), "Private fields are not public evidence")
    return {"status": "PUBLIC_AGGREGATES_VALIDATED", "seasons": len(seasons), "game_identities": 7549,
        "prediction_tables": 316, "metric_scalars": 948, "matched_panels": len(groups), "private_training_reproduced": False, **weekly}


def build_review(*, check=False):
    data = json.loads((HERE / "evidence.json").read_text())
    receipt = validate_evidence(data)
    template = (HERE / "review.template.html").read_text()
    embedded = canonical(data).decode().replace("<", "\\u003c")
    page = template.replace("__EVIDENCE_JSON__", embedded).replace("__EVIDENCE_SHA__", digest(data))
    require("__EVIDENCE_" not in page, "Unfilled review template")
    output = HERE / "review.html"
    if check:
        require(output.is_file() and output.read_text() == page, "Generated review differs; run contracts.py --build-review")
    else:
        output.write_text(page)
    return {**receipt, "review": "review.html", "evidence_sha256": digest(data), "generated_page_matches": True}


def demo(*, output):
    rows = [
        {"game_id": "DEMO_REG", "season": 2024, "phase": "REG", "date": "2024-09-01", "home_score": 23, "away_score": 20},
        {"game_id": "DEMO_POST", "season": 2024, "phase": "POST", "date": "2025-01-12", "home_score": 31, "away_score": 28},
        {"game_id": "DEMO_TIE", "season": 2024, "phase": "REG", "date": "2024-10-01", "home_score": 17, "away_score": 17},
        {"game_id": "DEMO_FUTURE", "season": 2026, "phase": "REG", "date": "2026-12-01", "home_score": None, "away_score": None},
        {"game_id": "DEMO_CANCELED", "season": 2022, "phase": "REG", "date": "2023-01-02", "home_score": None, "away_score": None, "canceled": True},
    ]
    contract = {"schema": "sports-edge-lab.workspace-layout.v1", "layout_version": 1,
        "project_directories": sorted(PROJECTS), "required_project_subdirectories": sorted(SUBDIRECTORIES),
        "organization_lock": ".example-coordinator.lock", "preserved_extra": {"owned_by": "invented coordinator"}}
    evidence = {"schema": "sports-edge-lab.nfl.demo.v1", "synthetic": True, "new_scientific_fits": 0,
        "input_sha256": digest(rows), "win": reconcile_games(rows, ["DEMO_REG", "DEMO_TIE"], season=2024, target="win"),
        "margin": reconcile_games(rows, ["DEMO_REG", "DEMO_TIE"], season=2024, target="margin"),
        "future": reconcile_games(rows, [], season=2026, target="win"),
        "canceled": reconcile_games(rows, [], season=2022, target="total"),
        "coordinator": admit_coordinator(contract, filename="workspace_layout_manifest.json")}
    destination = Path(output)
    if destination.exists():
        require(json.loads(destination.read_text()) == evidence, "Refuse changed or corrupted accepted demo artifact")
        return {"status": "REUSED", "new_work_units": 0, "artifact_sha256": digest(evidence), "synthetic": True}
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, path = tempfile.mkstemp(prefix="nfl-demo-", dir=destination.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(canonical(evidence)); stream.flush(); os.fsync(stream.fileno())
        require(json.loads(Path(path).read_text()) == evidence, "Staged demo verification failed")
        os.replace(path, destination)
    finally:
        Path(path).unlink(missing_ok=True)
    return {"status": "CREATED", "new_work_units": 1, "artifact_sha256": digest(evidence), "synthetic": True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--check-review", action="store_true")
    action.add_argument("--build-review", action="store_true")
    action.add_argument("--demo", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.demo:
        parser.error("--demo requires --output") if args.output is None else None
        result = demo(output=args.output)
    else:
        result = build_review(check=args.check_review)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
