"""Render the public V093 partial return, distinct failures and V095 repair evidence.

This consumes a bounded aggregate, never an owner runner, private source feed,
forecast grid or fitted state. It performs no network request or scientific fit.
"""
from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import html
import json
import math
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[3]
PUBLIC = ROOT / "docs/fbs/v093"
SCHEMA = "fbs.public.launch-readiness.v093"
FIELDS = {
    "root": "schema owner as_of publication prepared selection campaign population pricing retained recovery verification attempts verified_return replacement",
    "publication": "status website_deployed production_promoted new_forecasts_published",
    "prepared": "release status snapshot_at canonical_bytes canonical_verified native_packaged_check native_checked_at owner_executions scientific_fits provider_retrievals measured_optimizer_cores",
    "selection": "validation_seasons test_season primary_weights test_used_for_selection season_training_weights_used prior_test_exposure",
    "campaign": "horizon_minutes registered_jobs validation_jobs frozen_test_jobs fixed_blends worker_target worker_ceiling cost_guard_usd wall_time_waives_cost_guard",
    "population": "fresh_current_test_games resolved_again_at_launch validation_identity_required full_current_population_required conditional_status conditional_scope conditional_stage_complete conditional_full_current_test_reporting_complete conditional_current_test_blocked_jobs conditional_champion_eligible no_admission_status no_admission_operational_failure no_admission_required_exit_code",
    "pricing": "api_result public_source_verified native_public_source_verified observed_at rate_usd_per_full_host_hour rate_is_invoice source source_publication_at cache_age_limit_seconds cached_clock_renews_on_reuse account_and_app_check_required permissions_changed public_index_max_bytes public_region_max_bytes public_redirects_allowed official_documentation_url",
    "retained": "release completed_jobs base_fits calibrator_fits policy_target_identities cohorts scientific_complete official_schedule_completeness_certified current_as_of_claim",
    "recovery": "snapshot_at reuse_completed_task_identities resolve_latest_actual_return_at_launch actual_pointer_after_integrity_only partial_status_preserved deduplicated_payload_references part_max_bytes aggregate_science_cap latest_verified_return_release scoped_failed_releases scoped_failed_attempts scoped_successful_attempts",
    "verification": "final_archive_checks compact_resume_checks software_check_failures price_regression_checks price_regression_failures scientific_occupancy_gate native_packaged_children evidence",
    "attempts": "observed_at tally_scope scoped_failed_attempts scoped_successful_attempts scoped_active_attempts latest_actual_return_refreshed first second occupancy memory",
    "verified_return": "run_id status published_at pointer_sha256 integrity_verified durable_available owner_execution_successful scientific_complete partial_or_resumable storage_mode control_zip_bytes control_zip_sha256 part_count new_payload_uploaded_bytes inherited_payload_bytes_not_recopied new_unique_payload_count aggregate_science_cap",
    "replacement": "release status canonical_bytes canonical_sha256 native_verified native_verified_at owner_executions active_run_restart_authorized owner_lock_refusal_status owner_lock_refusal_child_exit required_useful_gate_preserved extra_optimizer_gate_can_abort optimizer_telemetry_retained",
}
ATTEMPT_FIELDS = {'first': 'run_id started_at science_finished_at child_exit_observed_at finalization_finished_at status phase child_exit_code child_exit_observed new_model_fits new_calibrator_fits reused_fit_states failed_fits failed_tasks fit_counts_complete completed_validation_jobs registered_validation_jobs pending_validation_jobs blocked_test_jobs new_scored_prediction_rows new_forecast_rows_including_ungraded prediction_rows_are_games new_original_issue_claimed historical_source_completed_jobs historical_source_registered_jobs observed_fit_pid_count leased_cpu_count selected_worker_capacity estimated_compute_usd cost_observed_at estimate_is_invoice final_result_verified full_current_test_reporting_complete full_current_population_champion_eligible', 'second': 'run_id started_at exit_observed_at status phase child_exit_code primary_error_type primary_errno reason secondary_error new_model_fits new_calibrator_fits actual_return_pointer_advanced', 'occupancy': 'observed_at required_gate_status required_useful_fraction required_window_seconds extra_optimizer_status extra_optimizer_fraction extra_optimizer_window_seconds minimum_fraction minimum_seconds denominator_workers leased_cpus full_24_worker_occupancy_claimed overall_fit_throughput_acceptance_claimed synthetic_or_reserved_load_counted', 'memory': 'budget_bytes resident_bytes_per_worker transient_bytes_per_worker admitted_workers hard_ceiling arbitrary_reserved_cores estimates_are_measured_peak_bounds native_threads_per_worker'}

PRIVATE = re.compile(r"s3://|arn:aws:|/home/sagemaker-user|AKIA[A-Z0-9]{16}|-----BEGIN .*PRIVATE KEY-----|\bcirca\b", re.I)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def timestamp(value):
    require(isinstance(value, str), "Evidence needs a timestamp")
    clock = datetime.fromisoformat(value.replace("Z", "+00:00"))
    require(clock.tzinfo is not None and clock.utcoffset() is not None, "Evidence time needs a timezone")
    return clock


def validate(d):
    require(d.get("schema") == SCHEMA and d.get("owner") == "FBS", "Wrong report identity")
    for section, fields in FIELDS.items():
        value = d if section == "root" else d[section]
        require(isinstance(value, dict) and set(value) == set(fields.split()), "Unknown or missing public fields: " + section)
    require(not PRIVATE.search(json.dumps(d, allow_nan=False)), "Private or out-of-scope text")
    require(d["publication"] == {"status": "SOURCE_REVIEW", "website_deployed": False,
        "production_promoted": False, "new_forecasts_published": False}, "Publication is not deployment or scientific work")
    require(d["selection"] == {"validation_seasons": [2024, 2025], "test_season": 2026,
        "primary_weights": [.5, .5], "test_used_for_selection": False,
        "season_training_weights_used": False, "prior_test_exposure": True}, "Selection boundary changed")
    p, c, g, rate, r, v = (d[k] for k in ("prepared", "campaign", "population", "pricing", "retained", "verification"))
    require(p["release"] == "V093" and p["status"] in {"PREPARATION_IN_PROGRESS", "PREPARED_NOT_EXECUTED"}, "Prepared release cannot claim research")
    require(all(type(p[k]) is int and p[k] == 0 for k in ("owner_executions", "scientific_fits", "provider_retrievals")), "Preparation created no owner science")
    require(p["measured_optimizer_cores"] is None and v["scientific_occupancy_gate"] == "PENDING_OWNER_EXECUTION", "Preparation cannot claim subsequently measured scientific occupancy")
    if p["status"] == "PREPARED_NOT_EXECUTED":
        require(type(p["canonical_bytes"]) is int and p["canonical_bytes"] > 0 and
                p["canonical_verified"] is True and p["native_packaged_check"] is True,
                "Prepared canonical requires physical and native evidence")
        require(timestamp(p["native_checked_at"]) <= timestamp(p["snapshot_at"]) <= timestamp(d["as_of"]), "Native preparation evidence cannot postdate its snapshot")
        require(v["native_packaged_children"] == [0, 2, 130], "Native fixture exits must be observed")
        require(v["evidence"], "Sealed preparation requires evidence pins")
    else:
        require(p["canonical_bytes"] is None and not p["canonical_verified"] and not p["native_packaged_check"], "Unsealed preparation cannot imply staged bytes")
    require(c == {"horizon_minutes": 120, "registered_jobs": 936, "validation_jobs": 624,
        "frozen_test_jobs": 312, "fixed_blends": 84, "worker_target": 12, "worker_ceiling": 24,
        "cost_guard_usd": 200, "wall_time_waives_cost_guard": False}, "Registered campaign or guard changed")
    require(g == {"fresh_current_test_games": None, "resolved_again_at_launch": True,
        "validation_identity_required": True, "full_current_population_required": True,
        "conditional_status": "PARTIAL_VALIDATION_RESEARCH_CURRENT_TEST_BLOCKED",
        "conditional_scope": "REGISTERED_VALIDATION_ONLY_CURRENT_TEST_BLOCKED", "conditional_stage_complete": False,
        "conditional_full_current_test_reporting_complete": False, "conditional_current_test_blocked_jobs": 312,
        "conditional_champion_eligible": False, "no_admission_status": "BLOCKED_NO_ADMITTED_VALIDATION_WORK",
        "no_admission_operational_failure": True, "no_admission_required_exit_code": 2}, "Conditional admission cannot invent full-current completion")
    require(rate["api_result"] == "ACCESS_DENIED" and rate["public_source_verified"] is True and
            rate["native_public_source_verified"] is True, "Public-source proof must remain separate from API denial")
    require(type(rate["rate_usd_per_full_host_hour"]) in (int, float) and
            math.isfinite(rate["rate_usd_per_full_host_hour"]) and rate["rate_usd_per_full_host_hour"] > 0,
            "Invalid hourly rate")
    require(rate["rate_is_invoice"] is False and rate["source"] == "Official AWS regional Price List" and
            rate["cache_age_limit_seconds"] == 86400 and rate["cached_clock_renews_on_reuse"] is False and
            rate["account_and_app_check_required"] is True and rate["permissions_changed"] is False,
            "Pricing authority cannot weaken identity, cost or freshness guards")
    require(rate["public_index_max_bytes"] == 1048576 and rate["public_region_max_bytes"] == 16777216 and
            rate["public_redirects_allowed"] is False, "Bounded public retrieval contract changed")
    require(timestamp(rate["source_publication_at"]) <= timestamp(rate["observed_at"]), "Price publication clock is in the future")
    require(rate["official_documentation_url"] == "https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/using-the-aws-price-list-bulk-api-fetching-price-list-files-manually.html", "Only the approved official source link is allowed")
    require(r == {"release": "V089", "completed_jobs": 90, "base_fits": 90, "calibrator_fits": 90,
        "policy_target_identities": 397, "cohorts": [{"season": 2024, "games": 919}, {"season": 2025, "games": 934}, {"season": 2026, "games": 752}],
        "scientific_complete": False, "official_schedule_completeness_certified": False, "current_as_of_claim": False},
        "Retained science must preserve its dated denominator")
    require(d["recovery"] == {"snapshot_at": p["snapshot_at"], "reuse_completed_task_identities": True, "resolve_latest_actual_return_at_launch": True,
        "actual_pointer_after_integrity_only": True, "partial_status_preserved": True, "deduplicated_payload_references": True,
        "part_max_bytes": 536870912, "aggregate_science_cap": None, "latest_verified_return_release": "V090",
        "scoped_failed_releases": ["V090", "V091"], "scoped_failed_attempts": 3, "scoped_successful_attempts": 0},
        "Recovery and scoped attempt counts changed")
    require(v["final_archive_checks"] == 48 and v["compact_resume_checks"] == 16 and v["software_check_failures"] == 0, "Observed engineering check counts changed")
    require(v["price_regression_checks"] == 16 and v["price_regression_failures"] == 0, "Price check count changed")
    for pin in v["evidence"]:
        require(set(pin) == {"label", "sha256", "scope"} and re.fullmatch(r"[a-f0-9]{64}", pin["sha256"]), "Invalid public evidence pin")
    validate_attempts(d)
    return d


def validate_attempts(d):
    a = d["attempts"]
    for section, fields in ATTEMPT_FIELDS.items():
        require(set(a[section]) == set(fields.split()), "Unknown or missing actual-attempt fields: " + section)
    first, second, occupancy, memory = (a[k] for k in ("first", "second", "occupancy", "memory"))
    require(a["tally_scope"] == "VERIFIED_V090_V091_V093_ATTEMPTS" and
            (a["scoped_failed_attempts"], a["scoped_successful_attempts"], a["scoped_active_attempts"]) == (5, 0, 0),
            "Both finalized failures must remain distinct; neither attempt is still active or successful")
    require(a["latest_actual_return_refreshed"] is True, "The finalized V093 partial return supersedes the preparation-time pointer")
    require(first["run_id"] == "20261118T045410Z-6771c1bd01-fbs093" and
            second["run_id"] == "20261118T045636Z-916e6541b4-fbs093" and first["run_id"] != second["run_id"],
            "Distinct authenticated attempts cannot be combined")
    require(timestamp(d["prepared"]["snapshot_at"]) < timestamp(first["started_at"]) < timestamp(second["started_at"]) <
            timestamp(second["exit_observed_at"]) < timestamp(first["science_finished_at"]) <= timestamp(first["child_exit_observed_at"]) <=
            timestamp(first["finalization_finished_at"]) <= timestamp(a["observed_at"]) <= timestamp(d["as_of"]),
            "Preparation, both exits and durable finalization must keep their observed order")
    require(first["status"] == "SAFE_PARTIAL_FAILURE_V13" and first["phase"] == "JOINT_VALIDATION" and
            first["child_exit_code"] == 2 and first["child_exit_observed"] is True and first["final_result_verified"] is True,
            "Verified partial-failure delivery is not successful or complete science")
    require(tuple(first[k] for k in ("new_model_fits", "new_calibrator_fits", "reused_fit_states", "failed_fits", "failed_tasks")) == (458, 458, 12, 0, 0)
            and first["fit_counts_complete"] is True, "Final work counts must match the actual return")
    require(tuple(first[k] for k in ("completed_validation_jobs", "registered_validation_jobs", "pending_validation_jobs", "blocked_test_jobs")) == (470, 624, 154, 312),
            "Completed work cannot shrink the full registered roster or blocked current-test work")
    require(first["completed_validation_jobs"] == first["new_model_fits"] + first["reused_fit_states"] and
            first["completed_validation_jobs"] + first["pending_validation_jobs"] + first["blocked_test_jobs"] == d["campaign"]["registered_jobs"],
            "Base fits, reused jobs and unfinished work must reconcile")
    require((first["new_scored_prediction_rows"], first["new_forecast_rows_including_ungraded"]) == (967236, 967760) and
            first["prediction_rows_are_games"] is False and first["new_original_issue_claimed"] is False,
            "Output rows are not unique games or newly issued live forecasts")
    require((first["historical_source_completed_jobs"], first["historical_source_registered_jobs"]) == (859, 859),
            "Registered history qualification is separate from model fits and provider-call counts")
    require((first["observed_fit_pid_count"], first["leased_cpu_count"], first["selected_worker_capacity"]) == (16, 24, 16),
            "Observed processes, leased CPUs and selected scientific capacity are distinct")
    require(first["estimated_compute_usd"] == 1.3986283326178637 and first["estimate_is_invoice"] is False and
            timestamp(first["cost_observed_at"]) <= timestamp(a["observed_at"]), "The final compute estimate is not an invoice")
    require(first["full_current_test_reporting_complete"] is False and first["full_current_population_champion_eligible"] is False,
            "A partial validation return cannot claim full current-test metrics or champion eligibility")
    require(second["status"] == "ADMISSION_FAILED" and second["phase"] == "OWNER_LOCK_ADMISSION" and
            second["child_exit_code"] == 1 and second["primary_error_type"] == "BlockingIOError" and second["primary_errno"] == 11 and
            second["reason"] == "EXISTING_ACTIVE_FBS_OWNER_LOCK" and
            second["secondary_error"] == "NO_NEW_FINALIZATION_RECORD; PREDECESSOR_PRESERVED" and
            second["new_model_fits"] == 0 and second["new_calibrator_fits"] == 0 and second["actual_return_pointer_advanced"] is False,
            "The second attempt failed admission before research; the finalization message is secondary")
    require(occupancy == {"observed_at": "2026-11-18T05:18:05.757753Z", "required_gate_status": "PASS_REAL_WORK",
        "required_useful_fraction": 0.8223823158585346, "required_window_seconds": 180.48597579200032,
        "extra_optimizer_status": "CPU_ACCEPTANCE_FAILED", "extra_optimizer_fraction": 0.7478988675809495,
        "extra_optimizer_window_seconds": 180.13498736099973, "minimum_fraction": .75, "minimum_seconds": 180,
        "denominator_workers": 16, "leased_cpus": 24, "full_24_worker_occupancy_claimed": False,
        "overall_fit_throughput_acceptance_claimed": False, "synthetic_or_reserved_load_counted": False},
        "The required useful-work pass and additional optimizer-only failure must remain distinct")
    require(memory == {"budget_bytes": 54529485004, "resident_bytes_per_worker": 2259756319,
        "transient_bytes_per_worker": 1073741824, "admitted_workers": 16, "hard_ceiling": 24,
        "arbitrary_reserved_cores": 0, "estimates_are_measured_peak_bounds": False, "native_threads_per_worker": 1},
        "Preserve actual memory admission and its estimation limits")
    require(memory["budget_bytes"] // (memory["resident_bytes_per_worker"] + memory["transient_bytes_per_worker"]) == memory["admitted_workers"],
            "The recorded memory policy must explain the selected capacity")
    returned = d["verified_return"]
    require(returned["run_id"] == first["run_id"] and returned["status"] == first["status"] and
            returned["published_at"] == first["finalization_finished_at"] and returned["integrity_verified"] is True and
            returned["durable_available"] is True and returned["owner_execution_successful"] is False and
            returned["scientific_complete"] is False and returned["partial_or_resumable"] is True,
            "Integrity-verified partial delivery is not a successful owner execution")
    require(returned["pointer_sha256"] == "3514583110c8377533f8a08aba6b206d5c2e88ee9c44d12060e6cb1fa344801d" and
            returned["storage_mode"] == "CONTROL_ZIP_PLUS_VERIFIED_DURABLE_REFERENCES" and returned["control_zip_bytes"] == 84885900 and
            returned["control_zip_sha256"] == "8c88308eeab9ac4c5f8013e053f3fb64298aab899407f81cdc3bed646c4adc71" and
            returned["part_count"] == 1 and returned["new_payload_uploaded_bytes"] == 2324812938 and
            returned["inherited_payload_bytes_not_recopied"] == 32435360361 and returned["new_unique_payload_count"] == 8588 and
            returned["aggregate_science_cap"] is None, "The compact control ZIP is separate from scientific payload storage")
    repair = d["replacement"]
    require(repair["release"] == "V095" and repair["status"] in {"IN_PREPARATION", "PREPARED_NOT_EXECUTED"} and
            repair["owner_executions"] == 0 and repair["active_run_restart_authorized"] is False and
            repair["owner_lock_refusal_status"] == "OWNER_LAUNCH_REFUSED_ACTIVE_OWNER" and repair["owner_lock_refusal_child_exit"] == 75 and
            repair["required_useful_gate_preserved"] is True and repair["extra_optimizer_gate_can_abort"] is False and repair["optimizer_telemetry_retained"] is True,
            "The replacement preserves owner locks, the required useful-work gate and optimizer measurements")
    if repair["status"] == "IN_PREPARATION":
        require(repair["canonical_bytes"] is None and repair["canonical_sha256"] is None and
                repair["native_verified"] is False and repair["native_verified_at"] is None, "Unsealed V095 cannot claim verified delivery")
    else:
        require(type(repair["canonical_bytes"]) is int and repair["canonical_bytes"] > 0 and
                re.fullmatch(r"[a-f0-9]{64}", repair["canonical_sha256"] or "") and repair["native_verified"] is True and
                timestamp(repair["native_verified_at"]) <= timestamp(d["as_of"]), "V095 delivery requires canonical and native proof")
        require(any(pin["sha256"] == repair["canonical_sha256"] for pin in d["verification"]["evidence"]),
                "The replacement canonical must have its own public evidence pin")


TEMPLATE = r'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Sports Edge Lab · FBS V093 partial return and V095 repair</title>
<meta name="description" content="Verified FBS V093 partial work, two distinct failures, measured acceptance gates, compact return storage and V095 repair preparation.">
<style>
:root{--paper:#f5f2e9;--white:#fffefa;--ink:#142b38;--muted:#52636a;--line:#d8ded9;--teal:#126e66;--soft:#e2eeea;--gold:#b4832b;--warn:#9a4030;font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;color:var(--ink);background:var(--paper)}*{box-sizing:border-box}body{margin:0}a{color:var(--teal)}a:focus-visible,button:focus-visible,select:focus-visible,summary:focus-visible{outline:3px solid var(--gold);outline-offset:4px}.shell{max-width:1160px;margin:auto;padding:0 28px}.masthead{display:flex;justify-content:space-between;gap:20px;padding:26px 0;border-bottom:1px solid var(--line);font-size:12px;font-weight:750;letter-spacing:.1em}.masthead a{text-decoration:none;color:var(--ink)}.masthead small{font-size:10px;color:var(--muted)}nav{display:flex;gap:22px;flex-wrap:wrap;padding:17px 0;font-size:12px;border-bottom:1px solid var(--line)}nav a{text-decoration:none}.hero{display:grid;grid-template-columns:1.4fr .7fr;gap:42px;align-items:center;padding:48px 0 32px}.eyebrow{color:var(--teal);font-size:10px;font-weight:800;letter-spacing:.16em;text-transform:uppercase;margin:0 0 12px}h1{font-size:clamp(36px,5vw,57px);line-height:1.05;letter-spacing:-.05em;margin:0 0 20px}h2{font-size:29px;line-height:1.13;letter-spacing:-.03em;margin:0 0 20px}h3{font-size:17px;margin:0 0 10px}p,li{font-size:14px;line-height:1.65;color:var(--muted)}.lead{font-size:16px;margin:0}.status{background:var(--ink);color:white;border-radius:14px;padding:25px}.status p{color:#c7d8da;font-size:12px}.status .eyebrow{color:#9dd7ca}.status h3{font-size:23px}.metrics{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px}.metric{background:var(--white);border:1px solid var(--line);padding:20px;border-radius:12px}.metric strong{display:block;font-size:35px;font-variant-numeric:tabular-nums;letter-spacing:-.04em;margin:8px 0}.metric span{font-size:10px;font-weight:750;text-transform:uppercase;letter-spacing:.08em;color:var(--muted)}.metric p{font-size:11px;margin:0}section{padding:39px 0;border-bottom:1px solid var(--line);scroll-margin-top:18px}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px}.card{padding:24px;background:var(--white);border:1px solid var(--line);border-radius:12px;min-width:0}.card p{font-size:13px;margin-bottom:0}.fine{font-size:11px;color:var(--muted);line-height:1.6}.notice{background:var(--soft);border-left:3px solid var(--teal);padding:16px 18px;margin-top:18px;border-radius:0 7px 7px 0;font-size:12px;line-height:1.65}.notice.warn{background:#f8e9e1;border-color:var(--warn)}.facts{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:0;margin:0}.facts dt,.facts dd{padding:10px 0;font-size:12px;border-bottom:1px solid #e7e9e4}.facts dt{padding-right:15px;color:var(--muted)}.facts dd{margin:0;font-weight:700;text-align:right;font-variant-numeric:tabular-nums;overflow-wrap:anywhere}.facts dt:last-of-type,.facts dd:last-child{border:0}.controls{display:flex;justify-content:space-between;gap:20px;align-items:end;margin-bottom:20px}label{font-size:12px;display:block;color:var(--muted)}select{display:block;max-width:100%;font:inherit;font-size:13px;padding:10px;border:1px solid var(--line);border-radius:7px;margin-top:8px;background:var(--white);color:var(--ink)}button{font:inherit;font-size:12px;font-weight:700;cursor:pointer;color:white;background:var(--teal);border:1px solid var(--teal);border-radius:7px;padding:12px 15px}.outcome{border:1px solid var(--line);border-radius:12px;background:var(--white);padding:25px}.outcome h3{font-size:23px}.outcome code{display:block;font-size:11px;overflow-wrap:anywhere;color:var(--teal);margin:12px 0}.result-pills{display:flex;gap:9px;flex-wrap:wrap}.result-pills span{font-size:11px;padding:7px 9px;background:var(--soft);border-radius:6px}.evidence-list{padding-left:20px}.evidence-list li{font-size:12px;margin:14px 0}.evidence-list code{display:block;overflow-wrap:anywhere;font-size:10px}.hidden{display:none!important}.error{background:#f8e9e1;color:var(--warn);padding:25px;margin:40px 0;border-radius:10px}summary{cursor:pointer;font-weight:700;font-size:13px}footer{padding:28px 0 42px;display:flex;justify-content:space-between;align-items:start;gap:24px}footer p{font-size:11px;margin:0;max-width:700px}footer a{font-size:12px;white-space:nowrap}.sources{font-size:12px}.readout{font-weight:750;color:var(--ink)}.attempt-id{display:block;font-size:10px;overflow-wrap:anywhere;color:var(--teal);margin-bottom:14px}.scope-line{font-size:12px;line-height:1.7;overflow-wrap:anywhere}.scope-line code{font-size:11px;overflow-wrap:anywhere}@media(max-width:680px){.shell{padding:0 17px}.masthead{padding:22px 0;align-items:start;letter-spacing:.05em}.masthead small{text-align:right;max-width:130px}.hero{grid-template-columns:1fr;gap:25px;padding:34px 0 25px}.metrics{grid-template-columns:repeat(2,minmax(0,1fr))}.metric{padding:17px}.metric strong{font-size:31px}.grid{grid-template-columns:1fr}.controls{display:block}.controls button{margin-top:16px}.card,.outcome{padding:20px}section{padding:31px 0}h2{font-size:25px}footer{display:block}footer a{display:inline-block;margin-top:18px}nav{gap:15px;font-size:11px}.facts dd{max-width:180px}}
</style></head><body><div class="shell">
<header class="masthead"><a href="../">SPORTS EDGE LAB <small>· COLLEGE FOOTBALL</small></a><small>V093 RETURN · V095 REPAIR</small></header>
<nav aria-label="Report navigation"><a href="#attempts">Actual attempts</a><a href="#return">Verified return</a><a href="#changes">Prepared behavior</a><a href="#outcomes">Return meanings</a><a href="#science">Scientific boundary</a><a href="#guard">Cost &amp; workers</a><a href="#evidence">Verification</a></nav>
<main id="report"><div class="hero"><div><p class="eyebrow">VERIFIED PARTIAL OWNER RETURN</p><h1>Work preserved.<br>Two failures explained.</h1><p class="lead" id="latest-run-note"></p></div><aside class="status"><p class="eyebrow">FINALIZED, RESUMABLE, INCOMPLETE</p><h3 id="ready-title"></h3><p id="ready-note"></p><p>Integrity verification confirms the saved return. The owner execution failed; the scientific campaign remains incomplete.</p></aside></div>
<div class="metrics"><article class="metric"><span>Completed new base fits</span><strong id="observed-model-fits"></strong><p>458 calibrator fits and 12 reused fit states are counted separately.</p></article><article class="metric"><span>Validation jobs saved</span><strong id="validation-completed"></strong><p>154 remain pending; all 312 current-test jobs remain blocked.</p></article><article class="metric"><span>Verified control ZIP</span><strong id="control-zip-size"></strong><p>MB, decimal. Scientific payload storage is separate below.</p></article><article class="metric"><span>Compute guard</span><strong id="cost-guard">$200</strong><p>Unlimited wall time keeps the cost ceiling in force.</p></article></div>
<section id="attempts"><p class="eyebrow">01 / ACTUAL OWNER ATTEMPTS</p><h2>Two launches, distinct failure causes</h2><div class="grid"><article class="card"><h3>First attempt: partial work, operational failure</h3><code class="attempt-id" id="first-run-id"></code><dl class="facts" id="first-attempt-facts"></dl><p>The required useful-work gate passed. An additional optimizer-only gate aborted this attempt. Individual fits recorded no errors; that does not make the owner execution successful.</p></article><article class="card"><h3>Second attempt: failed admission</h3><code class="attempt-id" id="second-run-id"></code><dl class="facts" id="second-attempt-facts"></dl><p>The second child raised <code>BlockingIOError</code> while acquiring the FBS owner lock held by the first attempt, which was active at that time. The later missing-finalization message obscured the admission cause.</p><p class="scope-line">Secondary message: <code id="secondary-error"></code></p></article></div><div class="notice warn" id="attempt-tally"></div><p class="fine" id="attempt-observation-limit"></p><div class="card" style="margin-top:18px"><h3>V095 combined repair</h3><p class="readout" id="repair-status"></p><p id="repair-note"></p><code class="attempt-id" id="repair-hash"></code><p>The replacement preserves the 75% / three-minute useful-work acceptance gate and optimizer telemetry. It removes the extra optimizer-only abort requirement. On a busy owner lock, its child reports a bound refusal receipt and exits 75 before pricing, input retrieval or scientific work; the supervisor reports that refusal explicitly.</p></div></section>
<section id="return"><p class="eyebrow">02 / VERIFIED PARTIAL RETURN</p><h2>Saved work is ready for continuation</h2><div class="grid"><article class="card"><h3>Actual result and remaining scope</h3><dl class="facts" id="return-facts"></dl><p id="row-count-note"></p><p>No new champion is promoted from this unfinished tranche. The retained validation leaders below keep their original evidence dates.</p></article><article class="card"><h3>Compact review, separate scientific payloads</h3><dl class="facts" id="storage-facts"></dl><p id="storage-note"></p><p>The control ZIP references verified durable scientific payloads. Its size is not total scientific storage. The per-part transport limit remains 512 MiB; there is no aggregate science cap.</p></article></div></section>
<section id="changes"><p class="eyebrow">03 / ORIGINAL V093 PREPARED BEHAVIOR</p><h2>What V093 prepared</h2><div class="grid"><article class="card"><h3>Refresh price authority safely</h3><p>The native role could not call the pricing query API. The replacement can read the official public regional price list, verify the exact compute scope, and preserve the existing account, app and cost checks.</p></article><article class="card"><h3>Admit unchanged validation work</h3><p>If the current 2026 population differs, unchanged 2024–2025 validation jobs can proceed. Missing frameworks or changed validation evidence stay blocked; the registered roster remains complete.</p></article><article class="card"><h3>Keep incomplete test reporting explicit</h3><p>A completed validation tranche remains a partial scientific return. The new current-population gap artifact keeps every required test game visible with missing metrics and no full-population champion eligibility.</p></article><article class="card"><h3>Resume compactly</h3><p>Resolve the newest verified return at launch, reuse completed task identities, and reference authenticated inherited payloads. New unique payloads retain integrity checks and the per-part transport limit.</p></article></div><div class="notice">The earlier V091 startup-identity repair remains part of V093. <a href="../v091/">The dated failure review</a> preserves three earlier failed V090/V091 attempts. The two later V093 failures are accounted for separately above. The first produced the latest verified partial return; the second admitted no research.</div></section>
<section id="outcomes"><p class="eyebrow">04 / RETURN-SCOPE CONTRACT</p><div class="controls"><div><h2>Completion has an explicit scope</h2><label for="scenario">Preview a return meaning — these are contract examples<select id="scenario"><option value="prepared">V093 preparation snapshot, before launch</option><option value="conditional">Validation complete; current test blocked</option><option value="no-admission">No validation work admitted</option></select></label></div><button id="download" type="button">Download this evidence</button></div><div class="outcome" aria-live="polite"><p class="eyebrow">CONTRACT PREVIEW · NO NEW RUN RESULT</p><h3 id="outcome-title"></h3><code id="outcome-status"></code><p id="outcome-description"></p><div class="result-pills"><span id="outcome-stage"></span><span id="outcome-test"></span><span id="outcome-promotion"></span></div></div><p class="fine">At launch, unchanged populations retain the original full-campaign path. A changed validation population blocks conditional admission. Framework availability may reduce admitted validation work, while all 936 registered jobs remain accounted for.</p></section>
<section id="science"><p class="eyebrow">05 / SCIENTIFIC BOUNDARY</p><h2>Validation selects. Current test reports.</h2><div class="grid"><article class="card"><h3>Preserved selection contract</h3><dl class="facts" id="selection-facts"></dl><p>All five season-weight ratios use the same base predictions. Their differences change annual scoring and ranks, with no season-weighted training or sensitivity refitting.</p></article><article class="card"><h3>Retained V089 evidence</h3><dl class="facts" id="retained-facts"></dl><p>The 919 / 934 / 752 cohorts are the dated verified comparison. They are not a refreshed current-season census. <a href="../v090/">Open its full candidates, metrics and source gaps.</a></p></article></div><div class="notice warn" id="population-note">The fresh current test denominator was unmeasured in the preparation snapshot. The finalized V093 partial return still has 312 blocked current-test jobs and does not supply full-current test metrics. A validation-only return cannot claim full current-test coverage, full-population champion eligibility or full V13 completion.</div></section>
<section id="guard"><p class="eyebrow">06 / OBSERVED COST AND CAPACITY</p><h2>Measured capacity has a denominator</h2><div class="grid"><article class="card"><h3>Preparation-time price evidence</h3><dl class="facts" id="price-facts"></dl><p>Refresh order: authenticated pricing query, official public current region index and its bound offer, then an authenticated cache within its original 24-hour age. Reuse does not renew the price clock.</p><p class="sources"><a id="pricing-doc" href="__OFFICIAL_PRICE_DOC__">Official AWS price-list documentation</a></p></article><article class="card"><h3>Required gate and extra abort gate</h3><dl class="facts" id="worker-facts"></dl><p id="memory-note"></p><p id="occupancy-limit"></p></article></div><p class="fine">The full-host rate supports an estimate, not an invoice. The actual-run cost observation above is separately timestamped. No permission or infrastructure change was made to obtain the public price. Memory-admission values are budget estimates, not measured peak-memory bounds.</p></section>
<section id="evidence"><p class="eyebrow">07 / DATED PREPARATION EVIDENCE</p><h2>Preparation and owner execution keep separate records</h2><div class="grid"><article class="card"><h3>Original V093 preparation checks</h3><p class="fine" id="preparation-clock"></p><dl class="facts" id="verification-facts"></dl></article><article class="card"><h3>Durable continuation</h3><p>At the original V093 preparation clock, V090 was the latest verified return. The actual pointer has since advanced to the integrity-verified V093 partial failure reported above. V089 champion metrics remain dated retained evidence. Resolve the latest verified checkpoint again at any future launch.</p><p>Return pointers advance only after integrity verification. Existing active work, partial status, failed branches, source gaps, negative findings and completed task identities remain preserved.</p></article></div><details class="card" style="margin-top:18px"><summary>Evidence pins and their scope</summary><ul class="evidence-list" id="evidence-list"></ul></details></section></main>
<div id="error" class="error hidden" role="alert"></div><footer><p id="as-of"></p><a href="README.md">Methods &amp; limits</a></footer>
</div><script id="report-data" type="application/json">__REPORT_JSON__</script><script>
'use strict';
(()=>{const el=id=>document.getElementById(id);let d;const text=(id,s)=>{el(id).textContent=String(s)};const clock=s=>s?new Intl.DateTimeFormat('en-US',{timeZone:'America/Los_Angeles',dateStyle:'medium',timeStyle:'short'}).format(new Date(s))+' Pacific':'Preparation in progress';
function check(){
 const a=d.attempts,f=a.first,s=a.second,o=a.occupancy,m=a.memory,r=d.replacement,v=d.verified_return;
 if(f.run_id===s.run_id||f.run_id!=='20261118T045410Z-6771c1bd01-fbs093'||s.run_id!=='20261118T045636Z-916e6541b4-fbs093'||f.status!=='SAFE_PARTIAL_FAILURE_V13'||f.child_exit_code!==2||f.child_exit_observed!==true||f.final_result_verified!==true||f.new_model_fits!==458||f.new_calibrator_fits!==458||f.reused_fit_states!==12||f.failed_fits!==0||f.failed_tasks!==0||f.fit_counts_complete!==true||f.completed_validation_jobs!==470||f.registered_validation_jobs!==624||f.pending_validation_jobs!==154||f.blocked_test_jobs!==312||f.new_scored_prediction_rows!==967236||f.new_forecast_rows_including_ungraded!==967760||f.prediction_rows_are_games!==false||f.new_original_issue_claimed!==false||f.observed_fit_pid_count!==16||f.leased_cpu_count!==24||f.selected_worker_capacity!==16||f.estimate_is_invoice!==false||f.full_current_test_reporting_complete!==false||f.full_current_population_champion_eligible!==false||s.child_exit_code!==1||s.new_model_fits!==0||s.new_calibrator_fits!==0||s.primary_errno!==11||s.phase!=='OWNER_LOCK_ADMISSION'||s.actual_return_pointer_advanced!==false||a.scoped_failed_attempts!==5||a.scoped_successful_attempts!==0||a.scoped_active_attempts!==0||a.latest_actual_return_refreshed!==true)throw Error('The actual-attempt evidence failed its outcome and scope contract.');
 if(o.required_gate_status!=='PASS_REAL_WORK'||o.required_useful_fraction!==0.8223823158585346||o.required_window_seconds!==180.48597579200032||o.extra_optimizer_status!=='CPU_ACCEPTANCE_FAILED'||o.extra_optimizer_fraction!==0.7478988675809495||o.extra_optimizer_window_seconds!==180.13498736099973||o.minimum_fraction!==0.75||o.minimum_seconds!==180||o.denominator_workers!==16||o.leased_cpus!==24||o.full_24_worker_occupancy_claimed!==false||o.overall_fit_throughput_acceptance_claimed!==false||o.synthetic_or_reserved_load_counted!==false||m.admitted_workers!==16||Math.floor(m.budget_bytes/(m.resident_bytes_per_worker+m.transient_bytes_per_worker))!==16||m.estimates_are_measured_peak_bounds!==false)throw Error('The required useful-work pass and extra optimizer-only failure must keep their measured denominators.');
 if(v.run_id!==f.run_id||v.status!==f.status||v.published_at!==f.finalization_finished_at||v.integrity_verified!==true||v.durable_available!==true||v.owner_execution_successful!==false||v.scientific_complete!==false||v.partial_or_resumable!==true||v.control_zip_bytes!==84885900||v.new_payload_uploaded_bytes!==2324812938||v.inherited_payload_bytes_not_recopied!==32435360361||v.aggregate_science_cap!==null)throw Error('Verified partial delivery cannot become successful science or hide payload storage.');
 if(r.release!=='V095'||r.owner_executions!==0||r.active_run_restart_authorized!==false||r.owner_lock_refusal_status!=='OWNER_LAUNCH_REFUSED_ACTIVE_OWNER'||r.owner_lock_refusal_child_exit!==75||r.required_useful_gate_preserved!==true||r.extra_optimizer_gate_can_abort!==false||r.optimizer_telemetry_retained!==true)throw Error('The replacement must preserve owner admission, required useful-work acceptance and optimizer measurements.');
 if(r.status==='PREPARED_NOT_EXECUTED'&&(!r.native_verified||!Number.isInteger(r.canonical_bytes)||r.canonical_bytes<=0||!(/^[a-f0-9]{64}$/).test(r.canonical_sha256||'')||!r.native_verified_at||new Date(r.native_verified_at)>new Date(d.as_of)||!d.verification.evidence.some(pin=>pin.sha256===r.canonical_sha256)))throw Error('The V095 delivery claim lacks canonical or native proof.');
 if(r.status==='IN_PREPARATION'&&(r.native_verified||r.canonical_bytes||r.canonical_sha256||r.native_verified_at))throw Error('Unsealed V095 cannot claim staged delivery.');if(!['PREPARED_NOT_EXECUTED','IN_PREPARATION'].includes(r.status))throw Error('Unknown replacement status.');
 if(d.schema!=='fbs.public.launch-readiness.v093'||d.owner!=='FBS'||d.prepared.owner_executions!==0||d.prepared.scientific_fits!==0||d.prepared.provider_retrievals!==0||d.selection.test_used_for_selection!==false||d.selection.season_training_weights_used!==false||d.selection.prior_test_exposure!==true||d.population.fresh_current_test_games!==null||d.population.conditional_stage_complete!==false||d.population.conditional_full_current_test_reporting_complete!==false||d.population.conditional_champion_eligible!==false||d.population.no_admission_required_exit_code!==2||d.pricing.cached_clock_renews_on_reuse!==false||d.pricing.permissions_changed!==false||d.campaign.cost_guard_usd!==200||d.campaign.wall_time_waives_cost_guard!==false||d.publication.website_deployed!==false)throw Error('The saved readiness evidence failed its public contract.');if(d.prepared.status==='PREPARED_NOT_EXECUTED'&&(!d.prepared.canonical_verified||!d.prepared.native_packaged_check||!d.prepared.canonical_bytes))throw Error('Prepared status requires verified canonical and native evidence.');
}
function facts(id,rows){el(id).replaceChildren();for(const [a,b]of rows){const dt=document.createElement('dt'),dd=document.createElement('dd');dt.textContent=a;dd.textContent=b;el(id).append(dt,dd);}}
function outcome(){const s=el('scenario').value;const options={prepared:['V093 preparation snapshot, before the owner launch',d.prepared.status,'This dated engineering snapshot created no owner run or fit. The subsequent authenticated owner execution is reported separately above.','Preparation-created runs: 0','Snapshot before actual launch'],conditional:['Validation completed; current test remains blocked',d.population.conditional_status,'This example means the admitted validation tranche completed while all 312 registered frozen-test jobs remain blocked. Full-current metrics and champion eligibility remain unavailable; the current-population gap artifact preserves the missing denominator.','Full stage complete: false','Current test complete: false'],'no-admission':['No admissible validation work',d.population.no_admission_status,'This example is an operational failure with required exit code 2. An empty admitted queue does not become a completed research tranche. Blocked jobs and resumable state remain explicit.','Required exit: 2','Full stage complete: false']};const o=options[s];text('outcome-title',o[0]);text('outcome-status',o[1]);text('outcome-description',o[2]);text('outcome-stage',o[3]);text('outcome-test',o[4]);text('outcome-promotion','Promotion: none');}
try{d=JSON.parse(el('report-data').textContent);check();const p=d.prepared,c=d.campaign,r=d.retained,rate=d.pricing,v=d.verification,a=d.attempts,f=a.first,s=a.second,o=a.occupancy,m=a.memory,repair=d.replacement,returned=d.verified_return;const pct=x=>(100*x).toFixed(4)+'%',gib=x=>(x/1073741824).toFixed(2)+' GiB',num=x=>x.toLocaleString('en-US');
text('ready-title','Verified partial failure');text('ready-note','Finalized '+clock(f.finalization_finished_at)+'. Both V093 attempts have observed failure exits; neither is active in this dated record.');text('latest-run-note','The first V093 attempt preserved '+num(f.completed_validation_jobs)+' validation jobs before an extra optimizer-only acceptance gate aborted it. A separate second launch failed owner-lock admission. The saved return is verified and resumable.');text('observed-model-fits',f.new_model_fits);text('validation-completed',f.completed_validation_jobs+' / '+f.registered_validation_jobs);text('control-zip-size',(returned.control_zip_bytes/1e6).toFixed(2));text('cost-guard','$'+c.cost_guard_usd);text('first-run-id',f.run_id);text('second-run-id',s.run_id);
facts('first-attempt-facts',[['Started',clock(f.started_at)],['Child exit observed',clock(f.child_exit_observed_at)],['Child exit code',f.child_exit_code],['New base fits / calibrators',f.new_model_fits+' / '+f.new_calibrator_fits],['Reused fit states',f.reused_fit_states],['Failed fits / tasks',f.failed_fits+' / '+f.failed_tasks],['Fit PIDs / leased CPUs',f.observed_fit_pid_count+' / '+f.leased_cpu_count],['End-to-end compute estimate','$'+f.estimated_compute_usd.toFixed(6)],['Estimate observed',clock(f.cost_observed_at)],['Return integrity / science','Verified / incomplete']]);
facts('second-attempt-facts',[['Started',clock(s.started_at)],['Exit observed',clock(s.exit_observed_at)],['Child exit code',s.child_exit_code],['Failure phase','Owner-lock admission'],['Primary error','BlockingIOError · errno 11'],['New base fits / calibrators','0 / 0'],['Actual-return pointer advanced','No']]);text('secondary-error',s.secondary_error);text('attempt-tally','Verified V090 / V091 / V093 scope: '+a.scoped_failed_attempts+' failed attempts / '+a.scoped_successful_attempts+' finalized successes / '+a.scoped_active_attempts+' active attempts. Both distinct V093 failures are included once.');text('attempt-observation-limit','This is a dated finalization record, not a live process monitor. The latest actual-return pointer was refreshed and identifies the verified V093 partial failure. No existing terminal or predecessor was stopped or restarted to inspect it.');
text('repair-status',repair.status==='PREPARED_NOT_EXECUTED'?'Prepared and native-verified; not executed':'In preparation; delivery verification pending');text('repair-note',repair.status==='PREPARED_NOT_EXECUTED'?'V095 canonical '+num(repair.canonical_bytes)+' bytes and native engineering verification are recorded as of '+clock(repair.native_verified_at)+'. Replacement owner executions: 0. This source report does not launch a continuation or authorize restarting active work.':'V095 combines the admission and acceptance-gate repairs. Canonical staging and native verification are pending; this report makes no delivery or execution claim.');text('repair-hash',repair.canonical_sha256?'SHA-256 '+repair.canonical_sha256:'Canonical SHA-256 pending');
facts('return-facts',[['Durable finalization',clock(returned.published_at)],['Owner execution','Failed · exit 2'],['Saved validation jobs',f.completed_validation_jobs+' / '+f.registered_validation_jobs],['Pending validation / blocked test',f.pending_validation_jobs+' / '+f.blocked_test_jobs],['Registered history qualification',f.historical_source_completed_jobs+' / '+f.historical_source_registered_jobs],['Scored prediction rows',num(f.new_scored_prediction_rows)],['Forecast rows, including ungraded',num(f.new_forecast_rows_including_ungraded)],['Full-current test metrics','Incomplete'],['Full-population champion eligibility','Unavailable']]);text('row-count-note','Prediction counts are output rows across registered policies and seasons, not unique games or a claim of newly issued live forecasts. History-qualification jobs are separate from provider-call counts.');
facts('storage-facts',[['Verified control ZIP',(returned.control_zip_bytes/1e6).toFixed(2)+' MB · '+num(returned.control_zip_bytes)+' B'],['New scientific payload uploads',(returned.new_payload_uploaded_bytes/1e9).toFixed(2)+' GB'],['New unique payloads',num(returned.new_unique_payload_count)],['Inherited payload not recopied',(returned.inherited_payload_bytes_not_recopied/1e9).toFixed(2)+' GB'],['Transport parts',returned.part_count],['Aggregate science cap','None']]);text('storage-note','Exact separate payload accounting: '+num(returned.new_payload_uploaded_bytes)+' new uploaded bytes; '+num(returned.inherited_payload_bytes_not_recopied)+' inherited bytes referenced without another copy.');
facts('selection-facts',[['Validation seasons','2024 + 2025'],['Declared primary weights','50 / 50'],['Test season','2026 · previously exposed'],['Test used for selection','No'],['Season training weighting','No']]);facts('retained-facts',[['Completed tranche jobs','90 / 90'],['Base fits / calibrators','90 / 90'],['Policy / target identities',r.policy_target_identities],['Dated completed-game cohorts',r.cohorts.map(x=>x.games).join(' / ')],['Full scientific program','Partial, resumable']]);
facts('price-facts',[['Full-host rate','$'+rate.rate_usd_per_full_host_hour.toFixed(2)+' / hour'],['Public source verified',clock(rate.observed_at)],['Price publication',clock(rate.source_publication_at)],['Native public access','Verified'],['Maximum original cache age','24 hours'],['Permission changes','None']]);el('pricing-doc').href=rate.official_documentation_url;facts('worker-facts',[['Selected pool / CPU lease',o.denominator_workers+' / '+o.leased_cpus],['Required useful-work gate',o.required_gate_status],['Useful occupancy / interval',pct(o.required_useful_fraction)+' of 16 · '+o.required_window_seconds.toFixed(3)+' s'],['Extra optimizer-only gate',o.extra_optimizer_status],['Optimizer occupancy / interval',pct(o.extra_optimizer_fraction)+' of 16 · '+o.extra_optimizer_window_seconds.toFixed(3)+' s'],['Acceptance floor / minimum window','75% / 180 seconds'],['Registered jobs / fixed blends',c.registered_jobs+' / '+c.fixed_blends],['Validation / frozen-test jobs',c.validation_jobs+' / '+c.frozen_test_jobs]]);text('memory-note','The recorded memory budget of '+gib(m.budget_bytes)+' divided by '+gib(m.resident_bytes_per_worker+m.transient_bytes_per_worker)+' per worker admits '+m.admitted_workers+' scientific workers. The explicit ceiling remains '+m.hard_ceiling+'; native threads are bounded to '+m.native_threads_per_worker+' per worker, with zero arbitrary reserved cores.');text('occupancy-limit','Both occupancy percentages use the selected 16-worker denominator, not the 24-CPU lease. Required useful preparation plus fitting passed. The additional optimizer-only floor failed and aborted V093; this report does not claim all throughput checks passed. V095 preserves the required gate and the measured optimizer evidence.');
facts('verification-facts',[['Final-archive checks',v.final_archive_checks+' passed'],['Compact-resume checks',v.compact_resume_checks+' passed'],['Pricing subset of archive checks',v.price_regression_checks+' passed'],['Canonical physical bytes',p.canonical_bytes===null?'Unsealed':p.canonical_bytes.toLocaleString('en-US')],['Native packaged check',p.native_packaged_check?'Verified':'Pending'],['Native fixture exits',v.native_packaged_children?v.native_packaged_children.join(', '):'Pending'],['Preparation-created runs / fits / retrievals','0 / 0 / 0']]);text('preparation-clock','Preparation snapshot: '+clock(p.snapshot_at)+'. These checks preceded the actual owner launch.');for(const pin of v.evidence){const li=document.createElement('li'),b=document.createElement('strong'),code=document.createElement('code'),span=document.createElement('span');b.textContent=pin.label;code.textContent=pin.sha256;span.textContent=pin.scope;li.append(b,code,span);el('evidence-list').append(li);}if(!v.evidence.length){const li=document.createElement('li');li.textContent='Sealed release evidence is pending.';el('evidence-list').append(li);}text('as-of','Report evidence as of '+clock(d.as_of)+'. Actual exits, finalization and replacement preparation retain their own clocks. Source publication, live website deployment and production promotion remain separate. Publishing this report does not launch owner work.');el('scenario').addEventListener('change',outcome);outcome();el('download').addEventListener('click',()=>{const u=URL.createObjectURL(new Blob([JSON.stringify(d,null,2)+'\n'],{type:'application/json'})),a=document.createElement('a');a.href=u;a.download='FBS_V093_PUBLIC_READINESS.json';document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(u),1000);});document.documentElement.dataset.ready='true';}catch(e){el('report').classList.add('hidden');el('error').classList.remove('hidden');text('error',e.message);document.documentElement.dataset.ready='error';}})();
</script></body></html>
'''


def render(data):
    validate(data)
    payload = json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    payload = payload.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    return TEMPLATE.replace("__REPORT_JSON__", payload).replace("__OFFICIAL_PRICE_DOC__", html.escape(data["pricing"]["official_documentation_url"], quote=True)).encode()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    data = json.loads((PUBLIC / "data/status.json").read_text())
    output = render(data)
    if args.check:
        require((PUBLIC / "index.html").read_bytes() == output, "Generated report differs from aggregate evidence")
    else:
        (PUBLIC / "index.html").write_bytes(output)
    print(json.dumps({"status": "PASS", "bytes": len(output), "sha256": hashlib.sha256(output).hexdigest(),
                      "owner_executions_started_by_generator": 0, "self_contained": True}))


if __name__ == "__main__":
    main()
