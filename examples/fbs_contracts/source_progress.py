"""Sanitized official-game inventory and log-scoped acquisition progress.

This public module validates and renders approved derived reports. It has no
cloud, provider, model, fitting or trading implementation. Source-stage counts
are not independent numerical acceptance or evidence of a live process.
"""
from __future__ import annotations

from datetime import datetime
import html
import json
import math
import re
from zoneinfo import ZoneInfo

INVENTORY_SCHEMA = "fbs.public.official-source-inventory.v1"
PROGRESS_SCHEMA = "fbs.public.source-stage-progress.v1"
INVENTORY_KEYS = {"schema", "verified_at", "source_capture_started_at", "source_capture_completed_at",
                  "source", "verification", "qualifications", "seasons", "rows"}
GAME_KEYS = {"season", "phase", "week", "kickoff", "kickoff_tbd", "home", "away", "population",
             "result_status", "completed", "home_points", "away_points", "home_margin", "total_points",
             "winner", "source_at"}
SEASON_KEYS = {"season", "games", "completed", "not_observed_complete", "pure_fbs_games", "fbs_involving_games"}
PROGRESS_KEYS = {"schema", "log_snapshot_at", "evidence_class", "owner_completion_observed",
                 "current_process_liveness", "numerical_history_replay_complete", "stages",
                 "latest_successor", "review_owner_fits", "review_issued_forecasts", "review_orders"}
STAGE_KEYS = {"season", "wave", "observed_at", "processed_contracts", "registered_contracts",
              "remaining_contracts", "available_historical_cutoff_rows", "failed_cutoff_rows",
              "empty_history_cutoff_rows", "registered_pass_processed", "all_reads_successful_claimed",
              "elapsed_seconds", "stage_remaining_seconds_estimate", "status"}
VERIFICATION_KEYS = {"official_originals_replayed", "total_originals_replayed", "physical_objects_reverified",
                     "official_game_values_reconstructed", "provider_calls_during_review"}
QUALIFICATION_KEYS = {"all_source_rows_retained", "independent_universal_completeness_proven",
                     "historical_model_input_availability_proven", "forecast_outputs_in_this_inventory",
                     "original_replay_cohort_games_unchanged"}
SUCCESSOR_KEYS = {"release", "status", "exit_code", "elapsed_seconds", "collector_started", "reason"}


def require(value, message):
    if not value:
        raise ValueError(message)


def instant(value):
    require(isinstance(value, str), "A recorded timezone-aware clock is required")
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("Invalid source clock") from exc
    require(result.tzinfo is not None, "Naive source clock")
    return result


def integer(value, minimum=0):
    return type(value) is int and value >= minimum


def finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def _public_only(value):
    serialized = json.dumps(value, ensure_ascii=False, allow_nan=False)
    require(not re.search(r"s3://|sagemaker-sports|/home/sagemaker-user|AKIA[0-9A-Z]{16}|secret_access_key|private_model_body|calibration_parameters|raw_receipt_manifest", serialized),
            "Private material is outside the public source-report boundary")


def validate_inventory(doc):
    require(isinstance(doc, dict) and set(doc) == INVENTORY_KEYS and doc["schema"] == INVENTORY_SCHEMA,
            "Unexpected official inventory schema/fields")
    verified = instant(doc["verified_at"])
    started, finished = instant(doc["source_capture_started_at"]), instant(doc["source_capture_completed_at"])
    require(started <= finished <= verified, "Source observation/verification clocks differ")
    require(doc["source"] == {"name": "CollegeFootballData", "url": "https://collegefootballdata.com/"},
            "Unapproved official source attribution")
    proof = doc["verification"]
    require(set(proof) == VERIFICATION_KEYS and all(integer(value) for value in proof.values()), "Invalid source verification summary")
    require(proof["official_originals_replayed"] == 6 and proof["total_originals_replayed"] >= 6
            and proof["provider_calls_during_review"] == 0, "Official season/phase or read-only scope differs")
    qualification = doc["qualifications"]
    require(set(qualification) == QUALIFICATION_KEYS and qualification["all_source_rows_retained"] is True
            and qualification["independent_universal_completeness_proven"] is False
            and qualification["historical_model_input_availability_proven"] is False
            and qualification["forecast_outputs_in_this_inventory"] == 0
            and integer(qualification["original_replay_cohort_games_unchanged"]), "Inventory cannot imply forecast or universal completeness")
    require(isinstance(doc["rows"], list) and isinstance(doc["seasons"], list), "Inventory rows/season summaries missing")
    identities = set()
    for row in doc["rows"]:
        require(isinstance(row, dict) and set(row) == GAME_KEYS, "Unexpected public inventory game field")
        require(type(row["season"]) is int and row["season"] in (2024, 2025, 2026)
                and row["phase"] in ("regular", "postseason") and integer(row["week"]), "Invalid official season/phase/week")
        kickoff, source_at = instant(row["kickoff"]), instant(row["source_at"])
        require(started <= source_at <= finished, "Per-game source clock is outside its authenticated capture")
        require(type(row["kickoff_tbd"]) is bool and type(row["completed"]) is bool, "Invalid official boolean state")
        require(all(isinstance(row[side], str) and row[side] for side in ("home", "away")) and row["home"] != row["away"],
                "Invalid ordered public game identity")
        identity = (row["season"], row["phase"], kickoff.isoformat(), row["home"], row["away"])
        require(identity not in identities, "Duplicate official public game identity")
        identities.add(identity)
        require(row["population"] in ("FBS_V_FBS", "FBS_INVOLVING"), "FBS classification is unproved")
        require(row["result_status"] in ("COMPLETED_WITH_SCORES", "COMPLETED_SCORES_MISSING", "NOT_OBSERVED_COMPLETE"),
                "Unknown captured result state")
        require(row["completed"] == (row["result_status"] == "COMPLETED_WITH_SCORES"), "Captured completion state differs")
        if row["completed"]:
            require(all(finite(row[key]) and row[key] >= 0 and int(row[key]) == row[key] for key in ("home_points", "away_points")),
                    "Completed inventory score missing")
            margin, total = row["home_points"] - row["away_points"], row["home_points"] + row["away_points"]
            winner = row["home"] if margin > 0 else row["away"] if margin < 0 else None
            require(row["home_margin"] == margin and row["total_points"] == total and row["winner"] == winner,
                    "Captured score/margin/total/winner coherence differs")
        else:
            require(all(row[key] is None for key in ("home_points", "away_points", "home_margin", "total_points", "winner")),
                    "Unobserved final score cannot be invented")
    require(proof["official_game_values_reconstructed"] == len(doc["rows"]), "Reconstructed official row denominator differs")
    require(len(doc["seasons"]) == 3 and {row.get("season") for row in doc["seasons"]} == {2024, 2025, 2026},
            "All three official season inventories must remain visible")
    for row in doc["seasons"]:
        require(set(row) == SEASON_KEYS and all(integer(value) for value in row.values()), "Unknown official season summary field")
        games = [game for game in doc["rows"] if game["season"] == row["season"]]
        require(row["games"] == len(games) and row["completed"] == sum(game["completed"] for game in games)
                and row["not_observed_complete"] == sum(not game["completed"] for game in games)
                and row["pure_fbs_games"] == sum(game["population"] == "FBS_V_FBS" for game in games)
                and row["fbs_involving_games"] == sum(game["population"] == "FBS_INVOLVING" for game in games),
                "Official season count closure differs")
    _public_only(doc)
    return doc


def validate_progress(doc):
    require(isinstance(doc, dict) and set(doc) == PROGRESS_KEYS and doc["schema"] == PROGRESS_SCHEMA,
            "Unexpected public progress schema/fields")
    snapshot = instant(doc["log_snapshot_at"])
    require(doc["evidence_class"] == "ATTACHED_EXECUTION_LOG_SNAPSHOT_NOT_LIVE_PROCESS"
            and doc["current_process_liveness"] == "UNKNOWN_FROM_STATIC_LOG"
            and doc["owner_completion_observed"] is False
            and doc["numerical_history_replay_complete"] is False, "Source progress cannot claim live or full numerical acceptance")
    require(all(type(doc[field]) is int and doc[field] == 0 for field in
                ("review_owner_fits", "review_issued_forecasts", "review_orders")),
            "Source progress review is not an owner fit/issue/order")
    require(isinstance(doc["stages"], list), "Source stage list missing")
    identities = set()
    for row in doc["stages"]:
        require(isinstance(row, dict) and set(row) == STAGE_KEYS, "Unexpected source-stage field")
        key = row["season"], row["wave"]
        require(type(row["season"]) is int and row["season"] in (2024, 2025, 2026)
                and row["wave"] in ("headline", "alternates") and key not in identities, "Duplicate or invalid stage identity")
        identities.add(key)
        require(instant(row["observed_at"]) <= snapshot, "Stage clock is later than the observed log")
        require(row["all_reads_successful_claimed"] is False, "Processed does not imply all source reads succeeded")
        for field in ("available_historical_cutoff_rows", "failed_cutoff_rows", "empty_history_cutoff_rows"):
            require(row[field] is None or integer(row[field]), "Invalid stage outcome counter")
        for field in ("elapsed_seconds", "stage_remaining_seconds_estimate"):
            require(row[field] is None or finite(row[field]) and row[field] >= 0, "Invalid stage-only timing")
        if row["processed_contracts"] is None:
            require(row["registered_contracts"] is None and row["remaining_contracts"] is None
                    and row["registered_pass_processed"] is False and row["status"] == "NO_PROGRESS_RECORD_IN_ATTACHED_LOG",
                    "Absent stage progress cannot become a zero/success counter")
        else:
            require(integer(row["processed_contracts"]) and integer(row["registered_contracts"], 1)
                    and row["processed_contracts"] <= row["registered_contracts"]
                    and row["remaining_contracts"] == row["registered_contracts"] - row["processed_contracts"],
                    "Stage work counter closure differs")
            full = row["processed_contracts"] == row["registered_contracts"]
            require(row["registered_pass_processed"] is full and row["status"] ==
                    ("REGISTERED_PASS_PROCESSED_NOT_FULL_SUCCESS" if full else "PARTIAL_LOG_PROGRESS"),
                    "Stage processed/partial state differs")
    successor = doc["latest_successor"]
    require(set(successor) == SUCCESSOR_KEYS and successor["release"] == "V028"
            and successor["status"] == "RECOVERABLE_PREDECESSOR_WAIT_DIAGNOSTIC" and successor["exit_code"] == 2
            and finite(successor["elapsed_seconds"]) and successor["elapsed_seconds"] >= 600
            and successor["collector_started"] is False
            and successor["reason"] == "ACTIVE_FBS_PREDECESSOR_PRESERVED", "Successor diagnostic cannot become collection success")
    _public_only(doc)
    return doc


def render_payload(inventory, progress):
    value = {"inventory": validate_inventory(inventory), "progress": validate_progress(progress)}
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), allow_nan=False).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")


def _clock(value):
    clock = instant(value).astimezone(ZoneInfo("America/Los_Angeles"))
    text = clock.strftime("%b %d, %Y · %I:%M %p %Z")
    return '<time datetime="' + html.escape(value, quote=True) + '" title="' + html.escape(value, quote=True) + '">' + html.escape(text) + '</time>'


def _number(value):
    return "—" if value is None else f"{value:,}"


def render_section(inventory, progress, *, embed_data=True):
    validate_inventory(inventory)
    validate_progress(progress)
    escape = html.escape
    cards = []
    for row in inventory["seasons"]:
        cards.append('<article class="coverage-card"><h3>' + str(row["season"]) + ' official inventory</h3>'
            '<div class="coverage-value">' + _number(row["games"]) + '</div><p>' + _number(row["completed"])
            + ' completed with scores · ' + _number(row["not_observed_complete"]) + ' not observed complete</p>'
            '<p>' + _number(row["pure_fbs_games"]) + ' FBS–FBS · ' + _number(row["fbs_involving_games"]) + ' other FBS-involving</p></article>')
    stages = []
    for row in progress["stages"]:
        work = "Not recorded"
        if row["processed_contracts"] is not None:
            work = _number(row["processed_contracts"]) + ' / ' + _number(row["registered_contracts"])
            work += '<span class="sub">' + _number(row["remaining_contracts"]) + ' contracts pending</span>'
        status = "Pass processed; not full success" if row["registered_pass_processed"] else "Partial in attached log" if row["processed_contracts"] is not None else "No progress record in attached log"
        stages.append('<tr><th scope="row">' + str(row["season"]) + ' · ' + escape(row["wave"]) + '</th><td>' + work
            + '</td><td>' + _number(row["available_historical_cutoff_rows"]) + '</td><td>' + _number(row["failed_cutoff_rows"])
            + ' / ' + _number(row["empty_history_cutoff_rows"])
            + '</td><td>' + escape(status) + '<span class="sub">' + _clock(row["observed_at"]) + '</span></td></tr>')
    rows = []
    for index, row in enumerate(inventory["rows"]):
        score = f'{row["away_points"]:g}–{row["home_points"]:g}' if row["completed"] else 'Not observed complete'
        margin = f'{row["home_margin"]:+g}' if row["completed"] else '—'
        total = f'{row["total_points"]:g}' if row["completed"] else '—'
        rows.append('<tr data-source-row="' + str(index) + '"><td>' + str(row["season"]) + '</td><td>'
            + escape(row["phase"]) + ' · ' + str(row["week"]) + '</td><th scope="row">' + escape(row["away"])
            + ' <span class="at">at</span> ' + escape(row["home"]) + '<span class="sub">' + _clock(row["kickoff"])
            + (' · time TBD' if row["kickoff_tbd"] else '') + '</span></th><td>' + score
            + ('<span class="sub">Away–home · actual result</span>' if row["completed"] else '')
            + '</td><td>' + margin + '</td><td>' + total + '</td><td>' + _clock(row["source_at"]) + '</td></tr>')
    count = len(inventory["rows"])
    section = ('<section id="source-evidence" aria-labelledby="source-evidence-heading">'
        '<div class="section-head"><div><h2 id="source-evidence-heading">All seasons, visible source progress</h2>'
        '<p>Official game inventory and acquisition progress advance independently of live model approval. Every observed game remains visible.</p></div></div>'
        '<div class="coverage-grid">' + ''.join(cards) + '</div>'
        '<div class="panel text-panel" style="margin-top:16px"><h3>Verified source facts, separate from forecasts</h3>'
        '<p>All ' + _number(count) + ' official rows were independently reproduced from the six season/phase originals. Source capture finished '
        + _clock(inventory["source_capture_completed_at"]) + '; numerical review recorded ' + _clock(inventory["verified_at"]) + '.</p>'
        '<p>This inventory contains public schedules and captured final results, not per-game historical model predictions. The original '
        + _number(inventory["qualifications"]["original_replay_cohort_games_unchanged"]) + '-game replay and its model scorecards are unchanged. A later result or price is never relabeled an earlier model input.</p>'
        '<p><strong>Source progress is not a live-process monitor.</strong> The attached log ends ' + _clock(progress["log_snapshot_at"])
        + '. It shows the 2026 passes processed while older-season backfill remained partial. Processed contracts can include failed, empty or unavailable cutoff rows. No full owner completion or new forecast is inferred.</p>'
        '<p>The successor returned a recoverable wait diagnostic after protecting an active predecessor. It began no collection in that invocation. Numeric feature reconstruction still gates genuine forecasts; it does not block source display.</p></div>'
        '<div class="panel" style="margin-top:16px"><div class="table-wrap" tabindex="0" role="region" aria-label="Recorded source stage progress">'
        '<table class="history-table"><caption class="screenreader">Native market stages from the attached execution log; counts are contracts or cutoff rows, not games or admitted forecasts.</caption>'
        '<thead><tr><th scope="col">Season · pass</th><th scope="col">Contracts processed / registered</th><th scope="col">Available historical cutoff rows</th><th scope="col">Failed / empty cutoff rows</th><th scope="col">Evidence state · observed clock</th></tr></thead>'
        '<tbody>' + ''.join(stages) + '</tbody></table></div><p class="fine" style="padding:0 20px">Completed processing is not complete provider coverage, independently replayed historical values, a successful owner return or an issued forecast. Failures remain part of the evidence.</p></div>'
        '<div class="panel" style="margin-top:16px"><details class="methods"><summary>Browse every official game across 2024, 2025 and 2026</summary>'
        '<p>All ' + _number(count) + ' rows are included below, including games without an observed final result. The controls filter display only; no game is deleted.</p>'
        '<div class="filter-grid"><label for="source-season-filter">Season<select id="source-season-filter" disabled><option value="all">All seasons</option><option value="2024">2024</option><option value="2025">2025</option><option value="2026">2026</option></select></label>'
        '<label for="source-result-filter">Captured result<select id="source-result-filter" disabled><option value="all">All result states</option><option value="completed">Completed with scores</option><option value="not_completed">Not observed complete</option></select></label>'
        '<label for="source-team-filter">Find a team<input id="source-team-filter" type="search" placeholder="Team name" disabled></label>'
        '<div><button id="source-clear-filters" type="button" disabled>Reset inventory filters</button></div></div>'
        '<p id="source-inventory-status" role="status" aria-live="polite" aria-atomic="true">' + _number(count) + ' of ' + _number(count) + ' source rows shown.</p>'
        '<noscript><p class="noscript">Filtering requires JavaScript. Every official source row is still included in the table.</p></noscript>'
        '<div class="table-wrap" tabindex="0" role="region" aria-label="All official FBS game observations" style="max-height:560px">'
        '<table class="history-table"><caption class="screenreader">Official schedule and captured actual results. Points, margins and totals here are outcomes, not predictions.</caption>'
        '<thead><tr><th scope="col">Season</th><th scope="col">Phase · week</th><th scope="col">Ordered matchup · kickoff</th><th scope="col">Captured result</th><th scope="col">Actual home margin</th><th scope="col">Actual total</th><th scope="col">Source observed</th></tr></thead>'
        '<tbody id="source-inventory-body">' + ''.join(rows) + '</tbody></table></div><p id="source-inventory-empty" hidden>No games match these display filters. Reset them to recover every source row.</p>'
        '<p class="fine">Source: <a href="https://collegefootballdata.com/">CollegeFootballData</a>. No raw provider payloads, provider identifiers, private recipes or cloud locations are included. Source snapshots do not prove universal completeness or continuous current prices.</p></details></div></section>')
    if embed_data:
        section += '<script type="application/json" id="source-progress-data">' + render_payload(inventory, progress) + '</script>'
    return section
