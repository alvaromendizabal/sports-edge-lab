"""Credential-free NFL accounting, coordination and information-time contracts.

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
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECTS = {"nfl", "ncaa_fbs", "nba", "ncaa_basketball"}
SUBDIRECTORIES = {"src", "config", "data", "runs", "notebooks", "reports", "releases", "archive"}
NFL_WEEKS = tuple(map(str, range(1, 19))) + ("WC", "DIV", "CON", "SB")
PROVIDERS = ("DraftKings", "Underdog", "PrizePicks", "Kalshi", "Polymarket")
PRESERVED_RESULTS_SHA256 = "e50ad7e1d1177b137fecc7bca58a61ce9405e82e19975f19a6d7600d39100f12"
PRESERVED_WEEKLY_SHA256 = "4ee52b3bad2d4af105588efb015444d37f55260d8169bd5a6ce4ebfe764370e2"


def canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def feature_view_identity(view):
    """Small invented consumer example, not private NFL feature extraction.

    A filename or row count cannot prove compatibility. Bind ordered columns,
    values/missingness, keyed rows, availability clocks and fitted fold state.
    Physical row ordering is irrelevant; model input column order is not.
    """
    require(isinstance(view, dict) and view.get("schema") == "public-feature-view.v1",
            "Unknown feature view schema")
    for field in ("project", "dataset_version", "transform_version", "fold_id"):
        require(isinstance(view.get(field), str) and bool(view[field]),
                "Missing feature identity: " + field)
    require(view["project"] == "nfl", "Feature namespace must remain NFL")
    columns = view.get("columns")
    require(isinstance(columns, list) and len(columns) > 0,
            "Ordered feature columns are required")
    names = []
    for column in columns:
        require(isinstance(column, dict) and set(column) == {"name", "dtype", "unit"},
                "Feature column contract is incomplete")
        require(all(isinstance(column[k], str) and column[k] for k in column),
                "Feature column metadata must be explicit")
        require(column["dtype"] in {"float", "integer", "boolean", "string"},
                "Unsupported feature dtype")
        names.append(column["name"])
    require(len(names) == len(set(names)), "Duplicate feature columns")
    source_rows = view.get("rows")
    require(isinstance(source_rows, list) and source_rows, "Feature rows are required")
    normalized, seen = [], set()
    for row in source_rows:
        require(isinstance(row, dict) and set(row) == {"event_id", "available_at", "values"},
                "Feature row contract is incomplete")
        event_id = row["event_id"]
        require(isinstance(event_id, str) and event_id and event_id not in seen,
                "Duplicate or missing feature event identity")
        seen.add(event_id)
        values = row["values"]
        require(isinstance(values, list) and len(values) == len(columns),
                "Feature values must match ordered columns")
        normalized_values = []
        for value, column in zip(values, columns):
            if value is None:
                normalized_values.append(None)
                continue
            dtype = column["dtype"]
            valid = ((dtype == "float" and type(value) in (float, int) and math.isfinite(value))
                     or (dtype == "integer" and type(value) is int)
                     or (dtype == "boolean" and type(value) is bool)
                     or (dtype == "string" and type(value) is str))
            require(valid, "Feature value violates dtype or finite-value contract")
            normalized_values.append(float(value) if dtype == "float" else value)
        normalized.append({"event_id": event_id,
                           "available_at": utc_clock(row["available_at"]).isoformat(),
                           "values": normalized_values})
    payload = {key: view[key] for key in
               ("schema", "project", "dataset_version", "transform_version", "fold_id", "columns")}
    payload["rows"] = sorted(normalized, key=lambda row: row["event_id"])
    return {"sha256": digest(payload), "rows": len(normalized), "columns": len(columns),
            "project": view["project"], "fold_id": view["fold_id"]}


def compare_feature_consumers(reference, candidate):
    """Prove equality only for the exact supplied invented view, not a whole lake."""
    first, second = feature_view_identity(reference), feature_view_identity(candidate)
    require(first == second, "Feature consumer semantics differ")
    return {"status": "EXACT_SUPPLIED_VIEW_PARITY", **first,
            "synthetic_example": True, "full_owner_migration_verified": False}


def invented_feature_view():
    return {"schema": "public-feature-view.v1", "project": "nfl",
        "dataset_version": "invented-v1", "transform_version": "identity-v1", "fold_id": "invented-fold-1",
        "columns": [{"name": "example_value", "dtype": "float", "unit": "unitless"},
                    {"name": "example_flag", "dtype": "boolean", "unit": "indicator"}],
        "rows": [{"event_id": "DEMO_A", "available_at": "2025-01-01T00:00:00Z", "values": [1.5, True]},
                 {"event_id": "DEMO_B", "available_at": "2025-01-02T00:00:00Z", "values": [None, False]}]}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def utc_clock(value):
    """Accept explicit instants only; date-only and naive clocks prove nothing."""
    require(isinstance(value, str), "Clock must be an explicit ISO timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError("Invalid clock") from error
    require(parsed.tzinfo is not None and parsed.utcoffset() is not None,
            "Clock must include a timezone")
    return parsed.astimezone(timezone.utc)


def audit_information_time(*, kickoff_at, decision_at, source_training_cutoff_at,
                           latest_input_available_at=None, latest_label_available_at=None,
                           model_completed_at=None):
    """Invented example of a stricter policy, not the private NFL feature audit.

    The source cutoff is a documented admissible training boundary. It is not a
    timestamp of actual model completion or proof of the last input used. A late
    boundary leaves the stronger policy unproved; it alone does not prove that
    the model actually used future information. Separate observed-input, label
    and model-completion clocks are required for this illustrative admission.
    """
    kickoff, decision = utc_clock(kickoff_at), utc_clock(decision_at)
    require(decision < kickoff, "Decision must precede kickoff")
    policy = min(decision, kickoff - timedelta(hours=24))
    clocks = {"source_training_cutoff_at": source_training_cutoff_at,
              "latest_input_available_at": latest_input_available_at,
              "latest_label_available_at": latest_label_available_at,
              "model_completed_at": model_completed_at}
    parsed = {key: None if value is None else utc_clock(value) for key, value in clocks.items()}
    checks = {}
    source = parsed["source_training_cutoff_at"]
    checks["source_bound"] = ("MISSING" if source is None else
        "STRICTLY_BEFORE_POLICY" if source < policy else "INSUFFICIENT_FOR_EARLIER_POLICY")
    for key, name in (("latest_input_available_at", "inputs"), ("latest_label_available_at", "labels")):
        value = parsed[key]
        checks[name] = "UNVERIFIED" if value is None else "STRICTLY_BEFORE_POLICY" if value < policy else "OBSERVED_TOO_LATE"
    fit = parsed["model_completed_at"]
    checks["model_availability"] = ("UNVERIFIED" if fit is None else
        "AVAILABLE_BY_POLICY" if fit <= policy else "COMPLETED_AFTER_POLICY")
    admitted = (checks["source_bound"] == checks["inputs"] == checks["labels"] == "STRICTLY_BEFORE_POLICY"
                and checks["model_availability"] == "AVAILABLE_BY_POLICY")
    known_late = any(checks[key] == "OBSERVED_TOO_LATE" for key in ("inputs", "labels"))
    return {"schema": "sports-edge-lab.public-information-time-audit.v1", "synthetic": True,
        "effective_policy_at": policy.isoformat(), "source_clocks": clocks,
        "checks": checks, "status": "DEMO_ADMISSIBLE" if admitted else "NOT_ESTABLISHED_FOR_POLICY",
        "known_late_input_or_label": known_late,
        "actual_fit_time_inferred_from_source_cutoff": False,
        "source_timestamp_rewritten": False, "real_forecast_issued": False}


def temporal_demo_cases():
    """Fixed invented instants; no game, source recipe, weight or forecast."""
    kickoff = datetime(2025, 11, 2, 18, tzinfo=timezone.utc)
    before = lambda hours: (kickoff - timedelta(hours=hours)).isoformat()
    complete = {"source_training_cutoff_at": before(25),
        "latest_input_available_at": before(26), "latest_label_available_at": before(30),
        "model_completed_at": before(24.5)}
    scenarios = [
        ("origin_bound", "Source boundary only: one hour before kickoff",
         {"source_training_cutoff_at": before(1)}),
        ("complete", "Complete invented evidence: all clocks before policy", complete),
        ("equal_boundary", "Source boundary exactly at the policy",
         {**complete, "source_training_cutoff_at": before(24)}),
        ("late_input", "An observed input arrives after the policy",
         {**complete, "latest_input_available_at": before(23), "model_completed_at": before(22)}),
        ("late_fit", "Inputs are earlier; model finishes after the policy",
         {**complete, "model_completed_at": before(1)}),
        ("unknown_fit", "Earlier information; completion time is unknown",
         {**complete, "model_completed_at": None}),
    ]
    rows = []
    for scenario, label, clocks in scenarios:
        for decision_hours in (1, 48):
            arguments = {"kickoff_at": kickoff.isoformat(), "decision_at": before(decision_hours), **clocks}
            rows.append({"scenario": scenario, "label": label, "decision_hours_before": decision_hours,
                         "arguments": arguments, "audit": audit_information_time(**arguments)})
    return {"schema": "sports-edge-lab.nfl.public-time-demo.v1", "synthetic": True,
        "clock_semantics": "Source training cutoff is an admissible boundary, not wall-clock fit completion.",
        "policy": "Earlier of explicit decision and kickoff minus 24 hours; information bounds are strict.",
        "cases": rows}


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
    require(data["owner_latest_success"] == "N006" and data["owner_latest_attempt"] == "N010", "Owner release boundary changed")
    require(data["next_owner_execution"] == {"release": "N012", "verified": False}, "Pending owner work cannot become executed")
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
    latest = data["n009_owner_attempt"]
    require(latest["status"] == "FAILED_INFORMATION_TIME_GUARD",
            "N009 storage recovery cannot become scientific completion")
    require(latest["actual_owner_execution"] is True and latest["archive_payloads_verified"] == 77 and
            latest["output_pins_verified"] == 14, "N009 archive audit changed")
    require(latest["tests"] == {"passed": 909, "inherited": 736, "n009": 173,
            "failures": 0, "errors": 0, "skipped": 0}, "N009 executed test evidence changed")
    require(latest["parent_checkpoints"] == {"original": 147, "n003": 90, "refits": 0} and
            latest["preserved_files"] == {"bridge": 1680, "full_worker": 1948,
                "content_size_mtime_unchanged": True}, "N009 preservation evidence changed")
    require(latest["new_n004_fits"] is None and latest["completed_n004_job_receipts"] == 0 and
            latest["n004_prediction_tables"] == 0, "Unknown fit attempts cannot become measured zero or completed fits")
    require(latest["model_week_fallback"] == "NOT_RESCANNED_INPUTS_UNVERIFIED" and
            latest["fallback_model_panels"] == 0, "Diagnostic fallback cannot replace accepted model results")
    require(all(latest[key] == 0 for key in ("paid_provider_calls", "actual_orders", "automatic_promotions")),
            "N009 must not imply provider acquisition, orders or promotion")
    recovery = latest["storage_recovery"]
    require(recovery["status"] == "ARCHIVED_LOSSLESS_VERIFIED" and
            recovery["independent_full_decompression_verified"] is True and
            recovery["new_retirement_this_invocation"] is True, "Cold archive recovery evidence changed")
    require(recovery["source_allocated_bytes"] - recovery["archive_allocated_bytes"] - recovery["view_allocated_bytes"] ==
            recovery["attributed_allocated_bytes_reclaimed"] == 15383494656, "Allocated recovery arithmetic differs")
    require(recovery["source_logical_bytes"] == 17911418880 and recovery["archive_logical_bytes"] == 2527775402,
            "Logical and allocated bytes must remain distinct")
    require(recovery["observed_shared_available_before_bytes"] == 3798405120 and
            recovery["observed_shared_available_after_bytes"] == 19182432256,
            "Dated shared recovery observations changed")
    final = latest["storage_final"]
    require(final["observed_at_utc"] == "2026-10-30T01:53:36.691688+00:00" and
            final["live_observation"] is False, "N009 historical storage cannot become live telemetry")
    require(final["total_bytes"] == 160982630400 and final["used_bytes"] == 132697722880 and
            final["available_bytes"] == 28284907520 and
            final["total_bytes"] == final["used_bytes"] + final["available_bytes"], "N009 final storage arithmetic differs")
    require(final["research_reserve_bytes"] == 4829478912 and final["available_bytes"] > final["research_reserve_bytes"] and
            final["available_inodes"] == 55244189 and final["total_inodes"] == 56417336,
            "N009 reserve or inode evidence differs")
    require(final["new_execution_allocated_bytes"] is None and final["net_nfl_allocated_change_bytes"] is None and
            final["shared_free_space_is_exclusively_nfl"] is False,
            "Shared capacity movement cannot become attributed NFL execution cost")


    current=data["n010_owner_attempt"]
    require(current["status"] == data["attempt_status"] == "FAILED_FIRST_STORAGE_GUARD_BEFORE_SCIENCE", "N010 failure cannot become successful science")
    require(current["new_scientific_fits"] is None and current["source_gap_count_verified"] is None,
            "Unreached counts must remain unknown")
    require(all(current[k] is False for k in ("tests_reached","parent_admission_reached","clock_migration_reached","science_reached")),
            "Unreached N010 stages cannot become completed")
    require(current["new_reclamation_bytes"] == 0, "Reused historical cleanup is not new reclamation")
    fs=current["storage_final"]
    require(fs["total_bytes"] == fs["used_bytes"] + fs["available_bytes"] and fs["available_bytes"] == 704483328,
            "Latest historical capacity arithmetic changed")
    require(fs["live_observation"] is False and fs["shared_change_attributed_exclusively_to_nfl"] is False,
            "Uploaded shared capacity is not live or exclusively attributed")
    counts=data["execution_outcomes"]
    require(len(counts["rows"]) == counts["authenticated_invocations"] == 6 and
            counts["scoped_successes"] + counts["failed"] + counts["blocked"] == 6 and
            (counts["scoped_successes"],counts["failed"],counts["blocked"],counts["separate_observed_launch_rejections"]) == (2,3,1,1),
            "Deduplicated owner outcomes changed")
    require(counts["lifetime_successes"] is None and counts["lifetime_failures"] is None, "Lifetime outcomes are unknown")
    plan=data["n011_preparation"]
    require(plan["owner_executed"] is False and plan["new_owner_reclamation_bytes"] is None and
            plan["cold_retirement_is_planned_not_owner_verified"] is True, "Preparation cannot become owner execution or reclaimed bytes")
    require(plan["normal_emergency_floor_bytes"] == 512*1024*1024 and plan["strict_scientific_clock_unchanged"] is True and
            plan["automatic_database_expansion"] is False, "Physical admission is separate from scientific clocks")


    maintenance = data["latest_shared_maintenance"]
    require(maintenance["scope_complete"] is True and maintenance["selected_roots_removed"] == 30
            and maintenance["protected_roots_preserved"] == 6, "Shared cleanup scope changed")
    require(maintenance["nfl_scientific_success_credit"] == maintenance["new_scientific_fits"] == 0
            and maintenance["feature_consumer_parity_established_by_cleanup"] is False,
            "Shared maintenance cannot become NFL scientific or feature-migration success")
    require(maintenance["global_cleanup_to_repeat"] is False and maintenance["restore_full_legacy_roots"] is False
            and maintenance["whole_workspace_cleanup_claimed"] is False,
            "Completed scoped cleanup cannot restart or become whole-workspace cleanup")
    require(maintenance["catalog_member_records"] == 55076 and maintenance["catalog_records_are_engineered_columns"] is False,
            "Catalog members are not engineered feature columns")
    shared = maintenance["storage"]
    require(shared["total_bytes"] == shared["used_bytes"] + shared["available_bytes"]
            and shared["available_bytes"] == 115923566592
            and shared["available_bytes"] - shared["prior_available_bytes"] == shared["shared_free_space_delta_bytes"] == 37332123648,
            "Dated shared storage arithmetic changed")
    require(shared["live_observation"] is False and shared["current_storage_measured"] is False
            and shared["shared_change_attributed_exclusively_to_nfl"] is False,
            "Uploaded shared snapshot cannot become live or NFL-exclusive telemetry")
    upcoming = data["n012_preparation"]
    require(upcoming["owner_executed"] is False and upcoming["new_owner_fits"] is None
            and upcoming["owner_feature_consumer_parity_verified"] is False
            and upcoming["owner_scientific_improvement_verified"] is False,
            "N012 preparation cannot become owner execution or scientific improvement")
    require(upcoming["current_season_estimator_fit_excluded"] is True
            and upcoming["current_season_adaptive_selection"] is False
            and upcoming["fold_specific_fitted_transforms"] is True,
            "Current-season nonselection and fold-specific transforms must remain explicit")
    source = data["official_schedule_observation"]
    require(source["frozen_historical_rows_modified"] is False and source["owner_execution"] is False
            and source["qualified_forecasts"] == source["verified_provider_quotes"] == 0,
            "Public schedule observation cannot become owner forecasts or quotes")
    require(source["actual_last_week_pnl"] is None and source["reconstructed_last_week_pnl"] is None
            and source["paper_remaining_budget"] is None and source["new_paper_allocation"] == 0,
            "Unverified issued history and budget must remain unknown")


def preserved_result_receipt(data):
    """A weaker diagnostic cannot replace an earlier authenticated result set."""
    require(digest(data["rows"]) == PRESERVED_RESULTS_SHA256, "Preserved model panels changed")
    require(digest(data["weekly_review"]) == PRESERVED_WEEKLY_SHA256, "Preserved weekly/provider evidence changed")
    return {"status": "ACCEPTED_RESULTS_PRESERVED", "source_release": "N006",
        "latest_attempt": "N010", "latest_attempt_status": data["attempt_status"],
        "model_panels": 316, "metric_scalars": 948, "season_week_slots": 66,
        "provider_week_states": 330, "latest_diagnostic_replaces_results": False,
        "result_rows_sha256_with_lf": PRESERVED_RESULTS_SHA256,
        "weekly_review_sha256_with_lf": PRESERVED_WEEKLY_SHA256}


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
    preserved_result_receipt(data)
    require(data["information_time_demo"] == temporal_demo_cases(), "Invented timing audit differs from executable contract")
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
    evidence = {"schema": "sports-edge-lab.nfl.demo.v3", "synthetic": True, "new_scientific_fits": 0,
        "input_sha256": digest(rows), "win": reconcile_games(rows, ["DEMO_REG", "DEMO_TIE"], season=2024, target="win"),
        "margin": reconcile_games(rows, ["DEMO_REG", "DEMO_TIE"], season=2024, target="margin"),
        "future": reconcile_games(rows, [], season=2026, target="win"),
        "canceled": reconcile_games(rows, [], season=2022, target="total"),
        "coordinator": admit_coordinator(contract, filename="workspace_layout_manifest.json"),
        "information_time": temporal_demo_cases(),
        "feature_consumer_parity": compare_feature_consumers(invented_feature_view(), invented_feature_view())}
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
