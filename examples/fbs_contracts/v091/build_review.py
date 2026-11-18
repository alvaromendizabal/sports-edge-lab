"""Build a compact public execution review from authenticated aggregate evidence.

No provider client, model runner, cloud credential, or continuation body belongs
in this module or its public input. Scientific arrays stay in their dated report.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PUBLIC = ROOT / "docs/fbs/v091"
SCHEMA = "fbs.public.execution-delivery.v091"
PRIVATE_TEXT = re.compile(r"(?:s3://|arn:aws:|/home/sagemaker-user|AKIA[A-Z0-9]{16}|-----BEGIN .*PRIVATE KEY-----)")
PRIVATE_KEYS = {"bucket", "secret", "access_token", "credential", "command", "private_policy_id", "model_weights", "provider_payload", "raw_source_rows"}


def integer(value, name):
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a nonnegative integer")


def finite(value, name):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
        raise ValueError(f"{name} must be finite and nonnegative")


def validate(data):
    if data.get("schema") != SCHEMA or data.get("owner") != "FBS":
        raise ValueError("Unsupported owner or evidence schema")
    allowed = {
        "root": {"schema", "owner", "as_of", "publication", "selection", "latest_attempt", "storage", "retained_science", "prepared", "recovery", "evidence", "launch_incident"},
        "launch_incident": {"release", "status", "reviewed_at", "new_reported_failures", "new_reported_successes", "lifetime_failure_total", "operator_exit_code", "operator_transcript", "diagnosis", "reproduced_error", "isolated_return_code", "isolated_stdout_bytes", "isolated_stderr_bytes", "isolated_child_launches", "isolated_model_fits", "isolated_aws_calls", "reproduction_scope", "prior_verification_limit", "repair_status", "next_release", "summary", "verified_failed_launches", "verified_successful_launches", "distinct_verified_startup_defects", "verified_research_child_launches", "verified_failure_times_utc", "scoped_releases", "scoped_failed_launches", "scoped_successful_launches"},
        "latest_attempt": {"release", "status", "summary", "failure_detail", "started", "successful", "operational_failures", "delivery_failures", "registered_model_jobs", "completed_model_jobs", "recorded_base_fits", "recorded_calibrator_fits", "recorded_forecasts", "recorded_scored_rows", "failed_fits", "fit_count_complete", "scientific_complete", "optimizer_occupancy_accepted", "pre_finalization_seconds", "return_finalization_seconds", "end_to_end_seconds", "estimated_full_host_cost_usd", "cost_is_invoice", "count_note"},
        "storage": {"latest_return_bytes", "latest_return_parts", "prior_scientific_return_bytes", "prior_scientific_return_parts", "previous_executable_bytes", "previous_prepared_zip_bytes", "part_max_bytes", "payload_count", "inherited_payload_count", "inherited_decoded_bytes", "within_return_duplicate_decoded_bytes", "catalog_projection_gzip_bytes", "projection_is_owner_return"},
        "retained_science": {"release", "registered_jobs", "completed_jobs", "base_fits", "calibrator_fits", "market_jobs", "core_jobs", "policy_target_identities", "cohorts", "scientific_complete", "official_schedule_completeness_certified", "horizon_minutes"},
        "prepared": {"release", "status", "evidence_as_of", "owner_executions", "new_scientific_fits", "provider_retrievals", "registered_model_jobs", "validation_jobs", "frozen_test_jobs", "fixed_blend_policies", "minimum_target_workers", "worker_ceiling", "measured_optimizer_cores", "cost_guard_usd", "unlimited_wall_waives_cost_guard", "executable_bytes", "prepared_report_zip_bytes", "review_zip_measurement_status", "delivery_size_scope", "verification_summary", "branches", "horizon_minutes"},
        "recovery": {"resolve_latest_again_at_launch", "verify_dependencies_before_reuse", "preserve_completed_work", "actual_pointer_only_after_integrity", "partial_and_complete_separate", "aggregate_science_cap", "return_changes", "remaining_limit"},
    }
    for name, keys in allowed.items():
        obj = data if name == "root" else data[name]
        if set(obj) != keys:
            raise ValueError(f"Unexpected or missing public fields in {name}")
    for rows, keys in ((data["evidence"], {"role", "sha256", "scope"}), (data["prepared"]["branches"], {"label", "jobs"}), (data["retained_science"]["cohorts"], {"season", "games"})):
        if any(set(row) != keys for row in rows):
            raise ValueError("Unexpected nested public fields")
    def walk(value):
        if isinstance(value, dict):
            if PRIVATE_KEYS.intersection(value):
                raise ValueError("Private input is excluded from the public report")
            for item in value.values():
                walk(item)
        elif isinstance(value, list):
            for item in value:
                walk(item)
        elif isinstance(value, str) and PRIVATE_TEXT.search(value):
            raise ValueError("Private storage or credential text is excluded")
    walk(data)
    pub = data["publication"]
    if pub != {"status": "DRAFT_SOURCE_REVIEW", "website_deployed": False, "production_promoted": False, "new_numerical_forecasts_published": False}:
        raise ValueError("Source review cannot become deployment, promotion or forecast issuance")
    selection = data["selection"]
    if selection != {"validation_seasons": [2024, 2025], "test_season": 2026, "primary_weights": [0.5, 0.5], "test_used_for_selection": False, "season_training_weights_used": False, "previous_test_exposure": True}:
        raise ValueError("Validation selection and prior test exposure must remain explicit")
    incident = data["launch_incident"]
    if incident["release"] != "V091" or incident["status"] != "OWNER_FAILURES_VERIFIED_LOCALLY_REPRODUCED":
        raise ValueError("The incident identity and evidence class must remain explicit")
    for key, expected in (("new_reported_failures", 1), ("new_reported_successes", 0), ("isolated_return_code", 2), ("isolated_stdout_bytes", 0), ("isolated_stderr_bytes", 0), ("isolated_child_launches", 0), ("isolated_model_fits", 0), ("isolated_aws_calls", 0)):
        integer(incident[key], key)
        if incident[key] != expected:
            raise ValueError("Incident counters must match the observed reproduction")
    if incident["operator_exit_code"] is not None or incident["lifetime_failure_total"] is not None:
        raise ValueError("A local reproduction cannot invent an operator exit code or lifetime tally")
    if incident["reproduced_error"] != "SUPERVISOR_RUN_ID_INVALID":
        raise ValueError("The reproduced failure identity is pinned")
    if incident["repair_status"] != data["prepared"]["status"] or incident["next_release"] != data["prepared"]["release"]:
        raise ValueError("Replacement status must match its separate preparation evidence")
    for key, expected in (("verified_failed_launches", 2), ("verified_successful_launches", 0), ("distinct_verified_startup_defects", 1), ("verified_research_child_launches", 0)):
        integer(incident[key], key)
        if incident[key] != expected:
            raise ValueError("Verified owner startup counts differ from the two receipts")
    if incident["verified_failure_times_utc"] != ["2026-11-18T02:19:09.348601Z", "2026-11-18T02:20:36.258110Z"]:
        raise ValueError("Verified startup receipt clocks must remain exact")
    if incident["scoped_releases"] != ["V090", "V091"]:
        raise ValueError("The local tally is scoped to V090 and V091")
    if incident["scoped_failed_launches"] != data["latest_attempt"]["operational_failures"] + incident["verified_failed_launches"] or incident["scoped_successful_launches"] != 0:
        raise ValueError("Scoped totals cannot duplicate or omit the verified attempts")
    latest = data["latest_attempt"]
    for name in ("started", "successful", "operational_failures", "delivery_failures", "registered_model_jobs", "completed_model_jobs", "recorded_base_fits", "recorded_calibrator_fits", "recorded_forecasts", "recorded_scored_rows", "failed_fits"):
        integer(latest[name], name)
    if latest["successful"] + latest["operational_failures"] > latest["started"]:
        raise ValueError("Execution counts overlap")
    if latest["completed_model_jobs"] > latest["registered_model_jobs"]:
        raise ValueError("Completed jobs exceed the attempt's registered work")
    if latest["status"] == "OPERATIONAL_FAILURE_VERIFIED_RESUMABLE" and (latest["successful"] or latest["operational_failures"] != 1):
        raise ValueError("Failed attempt cannot be labeled successful")
    if latest["scientific_complete"] or latest["optimizer_occupancy_accepted"] is not None:
        raise ValueError("This saved early failure proves neither complete science nor sustained fitting")
    for name in ("pre_finalization_seconds", "return_finalization_seconds", "end_to_end_seconds", "estimated_full_host_cost_usd"):
        finite(latest[name], name)
    if latest["cost_is_invoice"] is not False:
        raise ValueError("The recorded cost is an estimate")
    storage = data["storage"]
    for name in ("latest_return_bytes", "latest_return_parts", "prior_scientific_return_bytes", "prior_scientific_return_parts", "previous_executable_bytes", "previous_prepared_zip_bytes"):
        integer(storage[name], name)
    if storage["latest_return_parts"] < 1 or storage["part_max_bytes"] != 512 * 1024 * 1024:
        raise ValueError("Return transport must retain its per-part limit")
    if storage["latest_return_bytes"] > storage["latest_return_parts"] * storage["part_max_bytes"]:
        raise ValueError("Part count cannot carry the declared logical return")
    for name in ("payload_count", "inherited_payload_count", "inherited_decoded_bytes", "within_return_duplicate_decoded_bytes", "catalog_projection_gzip_bytes"):
        integer(storage[name], name)
    if storage["inherited_payload_count"] > storage["payload_count"] or storage["projection_is_owner_return"] is not False:
        raise ValueError("Inherited counts and encoding projections cannot invent a new owner return")
    retained = data["retained_science"]
    if retained["release"] == latest["release"]:
        raise ValueError("The latest failed attempt is separate from retained scientific results")
    if [c["season"] for c in retained["cohorts"]] != [2024, 2025, 2026]:
        raise ValueError("All annual cohorts must remain visible")
    for row in retained["cohorts"]:
        integer(row["games"], "cohort games")
    prepared = data["prepared"]
    if retained["horizon_minutes"] != 120 or prepared["horizon_minutes"] != 120:
        raise ValueError("This finite tranche is registered only for T120")
    if prepared["status"] not in {"PREPARATION_IN_PROGRESS", "PREPARED_NOT_EXECUTED"}:
        raise ValueError("Preparation has no completed owner execution")
    for name in ("owner_executions", "new_scientific_fits", "provider_retrievals"):
        if prepared[name] != 0:
            raise ValueError("Prepared software cannot create a scientific-result claim")
    for name in ("registered_model_jobs", "validation_jobs", "frozen_test_jobs", "fixed_blend_policies", "worker_ceiling"):
        integer(prepared[name], name)
    if prepared["validation_jobs"] + prepared["frozen_test_jobs"] != prepared["registered_model_jobs"]:
        raise ValueError("Prepared phase counts do not match the campaign")
    if sum(branch["jobs"] for branch in prepared["branches"]) != prepared["registered_model_jobs"]:
        raise ValueError("Prepared branch counts do not match the campaign")
    if prepared["worker_ceiling"] != 24 or prepared["minimum_target_workers"] != 12:
        raise ValueError("Retain the explicit 12–24 scientific-worker contract")
    if prepared["measured_optimizer_cores"] is not None:
        raise ValueError("No prepared-run optimizer throughput has been measured")
    if prepared["cost_guard_usd"] != 200 or prepared["unlimited_wall_waives_cost_guard"] is not False:
        raise ValueError("Wall-time settings never waive the compute guard")
    for key in ("executable_bytes", "prepared_report_zip_bytes"):
        if prepared[key] is not None:
            integer(prepared[key], key)
    if prepared["review_zip_measurement_status"] not in {"MEASURED", "OUTSIDE_THIS_PUBLIC_SNAPSHOT"}:
        raise ValueError("Review ZIP measurement scope must be explicit")
    if (prepared["review_zip_measurement_status"] == "MEASURED") != (prepared["prepared_report_zip_bytes"] is not None):
        raise ValueError("Review ZIP measurement and status disagree")
    if prepared["prepared_report_zip_bytes"] is not None and prepared["prepared_report_zip_bytes"] <= 0:
        raise ValueError("A measured review ZIP must have positive physical size")
    if prepared["status"] == "PREPARED_NOT_EXECUTED" and (prepared["executable_bytes"] is None or prepared["executable_bytes"] <= 0):
        raise ValueError("Verified prepared canonical requires positive measured size")
    recovery = data["recovery"]
    for key in ("resolve_latest_again_at_launch", "verify_dependencies_before_reuse", "preserve_completed_work", "actual_pointer_only_after_integrity", "partial_and_complete_separate"):
        if recovery[key] is not True:
            raise ValueError("Recovery integrity contract is incomplete")
    if recovery["aggregate_science_cap"] is not None:
        raise ValueError("Small delivery must not introduce an aggregate science cap")
    for pin in data["evidence"]:
        if not re.fullmatch(r"[a-f0-9]{64}", pin["sha256"]):
            raise ValueError("Evidence requires an exact SHA-256 pin")
    return data


TEMPLATE = r'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="FBS execution, storage and recovery evidence. Latest failed attempt, retained scientific results, and prepared compact delivery are reported separately.">
<title>Sports Edge Lab · FBS execution and delivery</title>
<style>
:root{--paper:#f5f2e9;--white:#fffefa;--ink:#142b38;--muted:#52636a;--line:#d8ded9;--teal:#126e66;--teal-soft:#e2eeea;--red:#9a4030;--red-soft:#f8e9e1;--gold:#b4832b;--navy:#183441;font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;color:var(--ink);background:var(--paper)}*{box-sizing:border-box}body{margin:0}a{color:var(--teal)}a:focus-visible,button:focus-visible,select:focus-visible,summary:focus-visible{outline:3px solid var(--gold);outline-offset:4px}.shell{max-width:1180px;margin:auto;padding:0 28px}.masthead{display:flex;align-items:center;justify-content:space-between;gap:18px;padding:25px 0;border-bottom:1px solid var(--line)}.brand{font-size:13px;font-weight:800;letter-spacing:.12em;text-decoration:none;color:var(--ink)}.brand span{display:block;font-size:10px;color:var(--muted);letter-spacing:.16em;margin-top:5px}.edition{font-size:11px;text-transform:uppercase;letter-spacing:.1em;color:var(--muted)}nav{display:flex;gap:20px;flex-wrap:wrap;font-size:12px;padding:17px 0;border-bottom:1px solid var(--line)}nav a{text-decoration:none}.hero{display:grid;grid-template-columns:1.3fr .7fr;gap:44px;align-items:end;padding:52px 0 36px}.eyebrow{font-size:11px;letter-spacing:.15em;font-weight:800;text-transform:uppercase;color:var(--teal);margin:0 0 13px}h1{font-size:clamp(36px,4.9vw,58px);line-height:1.04;letter-spacing:-.055em;margin:0 0 22px;max-width:800px}h2{font-size:29px;line-height:1.14;letter-spacing:-.035em;margin:0}h3{font-size:17px;line-height:1.3;margin:0 0 13px}.lead{color:var(--muted);font-size:16px;line-height:1.65;max-width:660px;margin:0}.status{background:var(--red-soft);border:1px solid #e9c9bd;padding:22px;border-radius:15px}.pill{display:inline-block;font-size:10px;letter-spacing:.09em;font-weight:800;text-transform:uppercase;padding:7px 9px;border-radius:5px;color:var(--red);background:#fff9f4;margin-bottom:14px}.status h3{font-size:22px;margin-bottom:10px}.status p{font-size:13px;line-height:1.6;color:#67483f;margin:0}.metrics{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}.metric{padding:20px;background:var(--white);border:1px solid var(--line);border-radius:12px}.metric .num{font-size:33px;line-height:1.2;font-variant-numeric:tabular-nums;letter-spacing:-.04em;font-weight:750;margin:8px 0}.metric .label{font-size:10px;text-transform:uppercase;letter-spacing:.1em;font-weight:750;color:var(--muted)}.metric .note{font-size:12px;line-height:1.5;color:var(--muted)}section{padding:38px 0;border-bottom:1px solid var(--line);scroll-margin-top:18px}.section-head{display:flex;justify-content:space-between;align-items:end;gap:20px;margin-bottom:22px}.section-head .eyebrow{margin-bottom:9px}.button{display:inline-flex;align-items:center;justify-content:center;background:var(--teal);border:1px solid var(--teal);color:white;border-radius:7px;padding:11px 14px;font:inherit;font-size:12px;font-weight:650;cursor:pointer;text-decoration:none;white-space:nowrap}.grid{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:20px}.card{min-width:0;padding:25px;background:var(--white);border:1px solid var(--line);border-radius:13px}.card p,.card li{font-size:13px;line-height:1.65;color:var(--muted)}.card p:last-child{margin-bottom:0}.card ul{padding-left:18px;margin-bottom:0}.facts{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:0;margin:0}.facts dt,.facts dd{font-size:12px;padding:10px 0;border-bottom:1px solid #e7e9e4}.facts dt{color:var(--muted);padding-right:18px}.facts dd{margin:0;text-align:right;font-variant-numeric:tabular-nums;font-weight:700}.facts dt:last-of-type,.facts dd:last-child{border-bottom:0}.notice{font-size:12px;line-height:1.65;background:var(--teal-soft);border-left:3px solid var(--teal);padding:16px 18px;border-radius:0 8px 8px 0;margin-top:18px}.warn{background:var(--red-soft);border-left-color:var(--red)}.fine{font-size:11px!important;color:var(--muted);line-height:1.6}.unit-control{font-size:12px;color:var(--muted);display:flex;gap:9px;align-items:center}select{font:inherit;background:var(--white);padding:8px;border:1px solid var(--line);border-radius:6px;color:var(--ink)}.storage-row{margin:0 0 21px}.storage-top{display:flex;justify-content:space-between;gap:15px;font-size:12px;margin-bottom:8px}.storage-top strong{font-variant-numeric:tabular-nums;white-space:nowrap}.bar-track{height:12px;background:#e6ebe6;border-radius:4px;overflow:hidden}.bar{height:100%;border-radius:4px;background:var(--navy)}.bar.latest{background:var(--red)}.bar.prepared{background:var(--teal)}.storage-row .fine{margin:6px 0 0}.steps{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}.step{border-top:3px solid var(--teal);padding:17px;background:var(--white);border-radius:0 0 9px 9px}.step .number{font:700 11px ui-monospace,monospace;color:var(--teal)}.step h3{font-size:15px;margin-top:10px}.step p{font-size:12px;line-height:1.6;color:var(--muted)}.tag{display:inline-block;padding:5px 8px;background:var(--teal-soft);color:var(--teal);font-weight:700;font-size:10px;border-radius:5px;margin:0 5px 7px 0}.tag.pending{background:#eee9dd;color:#6d5c37}table{width:100%;border-collapse:collapse;font-size:12px}th{text-align:left;font-size:10px;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);padding:12px 10px;border-bottom:1px solid var(--line)}td{padding:12px 10px;border-bottom:1px solid var(--line);font-variant-numeric:tabular-nums}td:last-child,th:last-child{text-align:right}.table-wrap{overflow-x:auto}.table-wrap table{min-width:0}.table-wrap td:last-child,.table-wrap th:last-child{width:72px;white-space:nowrap}.split-callout{margin:22px 0 0;display:flex;align-items:start;gap:12px;padding:18px;background:var(--navy);color:white;border-radius:9px;font-size:13px;line-height:1.6}.split-callout strong{color:#a2d9c7}details{margin-top:20px;border:1px solid var(--line);border-radius:10px;background:var(--white);padding:17px}summary{font-size:12px;font-weight:700;cursor:pointer}#evidence-list{padding-left:18px;font-size:11px;line-height:1.7;overflow-wrap:anywhere}code{font-family:ui-monospace,SFMono-Regular,monospace;font-size:11px}.footer{padding:26px 0 40px;font-size:11px;line-height:1.7;color:var(--muted)}.footer a{margin-right:15px}.alert{padding:20px;background:var(--red-soft);color:var(--red);margin:20px 0;border-radius:8px}.hidden{display:none!important}@media(max-width:720px){.shell{padding:0 18px}.masthead{align-items:start}.edition{max-width:115px;text-align:right;font-size:10px}.hero{grid-template-columns:1fr;gap:25px;padding-top:34px}.hero h1{font-size:40px}.metrics{grid-template-columns:1fr 1fr}.metric{padding:15px}.metric .num{font-size:28px}.grid,.steps{grid-template-columns:minmax(0,1fr)}.section-head{align-items:start;flex-direction:column}.section-head h2{font-size:26px}.card{padding:20px}.storage-top{align-items:start}.storage-top span{max-width:210px}.facts dt{max-width:250px}.lead{font-size:15px}nav{gap:15px}.status{padding:20px}section{padding:31px 0}.button{width:100%}}@media(max-width:720px){#incident-facts{grid-template-columns:minmax(0,1fr)}#incident-facts dt{max-width:none;border-bottom:0;padding-bottom:4px}#incident-facts dd{text-align:left;padding-top:0;overflow-wrap:anywhere}}@media print{nav,.button,.unit-control{display:none}.hero{padding-top:20px}.card,section,.metric{break-inside:avoid}body{background:white}}
</style></head><body>
<div class="shell"><header class="masthead"><a class="brand" href="https://github.com/alvaromendizabal/sports-edge-lab">SPORTS EDGE LAB<span>COLLEGE FOOTBALL · FBS</span></a><div class="edition">V091 launch failure<br>and V092 preparation</div></header>
<nav aria-label="Report sections"><a href="#incident">Latest launch failure</a><a href="#execution">Verified prior return</a><a href="#storage">Return size</a><a href="#campaign">Prepared campaign</a><a href="#recovery">Continuation</a></nav>
<main id="report"><div class="hero"><div><p class="eyebrow">LATEST LAUNCHES · FAILURES VERIFIED</p><h1>Repair the launch.<br>Preserve the research.</h1><p class="lead">V091 passed its checksum check, then returned to the shell without visible output. Two owner failure records now confirm the same startup defect reproduced from the exact package. The last verified owner return and retained scientific results remain separately identified below.</p></div><aside class="status"><span class="pill">V091 · two failed launches</span><h3>Failed before<br>scientific dispatch.</h3><p id="incident-summary"></p></aside></div>
<div class="metrics"><article class="metric"><div class="label">V090 recorded new fits</div><div class="num" id="new-fits"></div><div class="note">No registered model stage completed.</div></article><article class="metric"><div class="label">Latest verified return size</div><div class="num" id="return-size"></div><div class="note" id="return-parts"></div></article><article class="metric"><div class="label">V090 return finalization</div><div class="num" id="finalization"></div><div class="note">Measured separately from model work.</div></article><article class="metric"><div class="label">Next registered model jobs</div><div class="num" id="next-jobs"></div><div class="note">Prepared work; owner execution pending.</div></article></div>
<section id="incident" aria-labelledby="incident-title"><div class="section-head"><div><p class="eyebrow">01 / VERIFIED STARTUP FAILURES</p><h2 id="incident-title">The checksum passed. Two launches failed.</h2></div><span class="tag pending" id="repair-status"></span></div><div class="grid"><article class="card"><h3>Observed launch and isolated reproduction</h3><dl class="facts" id="incident-facts"></dl><p id="operator-transcript"></p><p class="fine" id="reproduction-scope"></p></article><article class="card"><h3>Verified cause and missing earlier test</h3><p id="incident-diagnosis"></p><div class="notice warn" id="prior-verification-limit"></div><p class="fine">One pasted launch report led to verification of two V091 startup failures from distinct owner receipts. Together with V090, the scoped total is three failures and zero successes; it is not an all-time count.</p></article></div></section>
<section id="execution" aria-labelledby="execution-title"><div class="section-head"><div><p class="eyebrow">02 / VERIFIED PRIOR RETURN</p><h2 id="execution-title">The prior verified failure and retained science.</h2></div><button class="button" id="download" type="button">Download aggregate evidence</button></div><div class="grid"><article class="card"><span class="tag pending">LAST VERIFIED OWNER RETURN</span><h3>V090 execution accounting</h3><p id="failure-summary"></p><dl class="facts" id="execution-facts"></dl><p class="fine" id="count-note"></p><p class="fine" id="cost-note"></p></article><article class="card"><span class="tag">LAST COMPLETED MODEL TRANCHE</span><h3>V089 results remain retained</h3><dl class="facts" id="retained-facts"></dl><p>The dated comparison keeps the same completed-game populations for every contender, its exact saved metrics, and all previously exposed test labels.</p><p><a id="comparison-link" href="https://github.com/alvaromendizabal/sports-edge-lab/pull/386">Review the preserved comparison source</a></p><p class="fine">The comparison source is in its separate draft review. This execution page does not issue new forecasts or select new champions.</p></article></div><div class="notice warn" id="failure-detail"></div></section>
<section id="storage" aria-labelledby="storage-title"><div class="section-head"><div><p class="eyebrow">03 / OBSERVED STORAGE AND PREPARED DELIVERY</p><h2 id="storage-title">Report bytes separately from research artifacts.</h2></div><label class="unit-control" for="unit">Display unit<select id="unit"><option value="GB">GB · decimal</option><option value="GiB">GiB · binary</option></select></label></div><div class="grid"><article class="card"><h3>Verified sizes</h3><div id="size-bars"></div><p id="executable-size" class="fine"></p><p class="fine">Bars compare observed file bytes. A small review package does not include every large research artifact. Referenced durable artifacts must remain available and pass verification.</p></article><article class="card"><h3>What changes in the next return</h3><ul id="return-changes"></ul><div class="notice" id="delivery-verification"></div></article></div><div class="split-callout"><div><strong>512 MiB is a transport-part limit.</strong> Large required deliveries still use verified ordered parts. Scientific work has no aggregate size cap; the compact design removes repeated delivery of retained artifacts.</div></div></section>
<section id="campaign" aria-labelledby="campaign-title"><div class="section-head"><div><p class="eyebrow">04 / REGISTERED WORK</p><h2 id="campaign-title">A substantial queue, with measured admission.</h2></div><span class="tag pending" id="prepared-status"></span></div><div class="grid"><article class="card"><h3>Scientific work remains owner-launched</h3><div class="table-wrap"><table><thead><tr><th>Registered branch</th><th>Model jobs</th></tr></thead><tbody id="campaign-rows"></tbody></table></div><p id="blend-note"></p></article><article class="card"><h3>12–24 workers, actual optimizer evidence</h3><dl class="facts" id="worker-facts"></dl><p>Preparation and fits share a bounded queue. Native threads, physical memory, storage and the compute guard constrain admission. Independent ten-second logs record actual optimizer activity and ready-work starvation.</p><p class="fine">The prepared release has no measured sustained fit throughput. The conditional 75% / three-minute gate must be evaluated during real eligible work.</p></article></div><div class="notice">2024 and 2025 remain validation; 2026 remains previously exposed test reporting. The five evaluation ratios change annual score weighting only. They do not refit models or change predictions.</div></section>
<section id="recovery" aria-labelledby="recovery-title"><div class="section-head"><div><p class="eyebrow">05 / DURABLE CONTINUATION</p><h2 id="recovery-title">Resolve, verify, and resume completed work.</h2></div></div><div class="steps"><article class="step"><span class="number">01</span><h3>Resolve current evidence</h3><p>Read the newest verified actual return again when the owner launches. A prepared release remains a separate record.</p></article><article class="step"><span class="number">02</span><h3>Verify dependencies</h3><p>Reuse artifacts only when their immutable identities, physical integrity and required dependencies match. Missing or corrupt evidence stays explicit.</p></article><article class="step"><span class="number">03</span><h3>Commit safely</h3><p>Preserve completed work and update the actual pointer only after verified delivery. Partial and complete scientific states remain distinct.</p></article></div><div class="notice" id="recovery-limit"></div><details><summary>Evidence pins and verification scope</summary><ul id="evidence-list"></ul></details></section>
</main><div id="error" class="alert hidden" role="alert"></div><footer class="footer"><p id="as-of"></p><p>Source review only. Website deployment and production promotion remain separate. Public aggregates exclude private continuation bodies, credentials, model weights, raw licensed arrays and unissued numerical forecasts.</p><a href="https://github.com/alvaromendizabal/sports-edge-lab/blob/fbs/v091-compact-delivery-review-20261117/docs/fbs/v091/README.md">Methods and limits</a><a href="https://github.com/alvaromendizabal/sports-edge-lab/blob/f1f51ceac2f9aac41618fe9ddd8517e7a259a758/docs/fbs/PUBLICATION_BOUNDARY_V5.md">FBS publication boundary</a></footer></div>
<script id="report-data" type="application/json">__REPORT_JSON__</script>
<script>
'use strict';
(()=>{
 const el=id=>document.getElementById(id), d=JSON.parse(el('report-data').textContent);
 function requireData(){if(d.schema!=='fbs.public.execution-delivery.v091'||d.owner!=='FBS'||d.prepared.owner_executions!==0||d.prepared.new_scientific_fits!==0||d.publication.website_deployed!==false||d.selection.test_used_for_selection!==false||d.launch_incident.new_reported_failures!==1||d.launch_incident.operator_exit_code!==null||d.launch_incident.isolated_return_code!==2||d.launch_incident.isolated_child_launches!==0||d.launch_incident.isolated_model_fits!==0||d.launch_incident.isolated_aws_calls!==0||d.launch_incident.repair_status!==d.prepared.status||d.launch_incident.next_release!==d.prepared.release||d.launch_incident.verified_failed_launches!==2||d.launch_incident.verified_research_child_launches!==0||d.launch_incident.scoped_failed_launches!==3||d.launch_incident.scoped_successful_launches!==0)throw Error('The saved execution evidence failed its public contract.');}
 const text=(id,v)=>{el(id).textContent=String(v)},number=v=>Number(v).toLocaleString('en-US');
 const pacific=v=>Number.isNaN(Date.parse(v))?v:new Intl.DateTimeFormat('en-US',{timeZone:'America/Los_Angeles',dateStyle:'medium',timeStyle:'short'}).format(new Date(v))+' Pacific';
 function facts(id,rows){const node=el(id);node.replaceChildren();for(const [label,value] of rows){const dt=document.createElement('dt'),dd=document.createElement('dd');dt.textContent=label;dd.textContent=value;node.append(dt,dd);}}
 function bytes(v,unit='GB'){if(v===null)return 'Outside this snapshot';const binary=unit==='GiB',base=binary?1024:1000,labels=binary?['bytes','KiB','MiB','GiB']:['bytes','KB','MB','GB'];let index=0,value=v;while(value>=base&&index<3){value/=base;index++;}return value.toLocaleString('en-US',{minimumFractionDigits:index?2:0,maximumFractionDigits:index?3:0})+' '+labels[index];}
 function sizes(){const unit=el('unit').value, s=d.storage,p=d.prepared;const rows=[['V089 retained scientific return',s.prior_scientific_return_bytes,'',s.prior_scientific_return_parts+' verified parts'],['V090 failed-attempt return',s.latest_return_bytes,'latest',s.latest_return_parts+' verified parts; zero recorded new fits'],[p.release+' prepared review package',p.prepared_report_zip_bytes,'prepared',p.prepared_report_zip_bytes===null?'Review ZIP measurement is recorded separately in the owner delivery handoff.':p.delivery_size_scope]];const max=Math.max(...rows.map(x=>x[1]??0));el('size-bars').replaceChildren();for(const [label,size,cls,note]of rows){const row=document.createElement('div');row.className='storage-row';const top=document.createElement('div');top.className='storage-top';const name=document.createElement('span');name.textContent=label;const value=document.createElement('strong');value.textContent=bytes(size,unit);top.append(name,value);const track=document.createElement('div');track.className='bar-track';track.setAttribute('aria-hidden','true');const bar=document.createElement('div');bar.className='bar '+cls;bar.style.width=size===null?'0':(size/max*100)+'%';track.append(bar);const small=document.createElement('p');small.className='fine';small.textContent=note;row.append(top,track,small);el('size-bars').append(row);}text('return-size',bytes(s.latest_return_bytes,unit));text('executable-size',p.executable_bytes===null?'Canonical executable measurement pending.':'Canonical executable: '+bytes(p.executable_bytes,unit)+'; previous executable: '+bytes(s.previous_executable_bytes,unit)+'. Reduction: '+(100*(1-p.executable_bytes/s.previous_executable_bytes)).toFixed(1)+'%.');}
 try{requireData();const a=d.latest_attempt,r=d.retained_science,p=d.prepared,i=d.launch_incident;
 text('incident-summary',i.summary);text('operator-transcript',i.operator_transcript);text('reproduction-scope',i.reproduction_scope);text('incident-diagnosis',i.diagnosis);text('prior-verification-limit',i.prior_verification_limit);text('repair-status',i.next_release+' · '+(i.repair_status==='PREPARED_NOT_EXECUTED'?'Prepared; owner run pending':'Preparation in progress'));facts('incident-facts',[['Verified V091 successful / failed launches',i.verified_successful_launches+' / '+i.verified_failed_launches],['Distinct verified startup defects',number(i.distinct_verified_startup_defects)],['V090 + V091 successful / failed attempts',i.scoped_successful_launches+' / '+i.scoped_failed_launches],['First verified V091 failure',pacific(i.verified_failure_times_utc[0])],['Second verified V091 failure',pacific(i.verified_failure_times_utc[1])],['Operator process exit code','Not captured in pasted transcript'],['Isolated package return code',number(i.isolated_return_code)],['Isolated stdout / stderr bytes',i.isolated_stdout_bytes+' / '+i.isolated_stderr_bytes],['Research child launches in local check',number(i.isolated_child_launches)],['Local real fits / AWS calls',i.isolated_model_fits+' / '+i.isolated_aws_calls]]);
 text('failure-summary',a.summary);text('failure-detail',a.failure_detail);text('new-fits',number(a.recorded_base_fits));text('return-parts',d.storage.latest_return_parts+' ordered parts · verified delivery');text('finalization',(a.return_finalization_seconds/60).toFixed(1)+' min');text('next-jobs',number(p.registered_model_jobs));
 facts('execution-facts',[['Owner executions started',number(a.started)],['Successful / operationally failed',a.successful+' / '+a.operational_failures],['Delivery failures',number(a.delivery_failures)],['Registered / completed model jobs',a.registered_model_jobs+' / '+a.completed_model_jobs],['Recorded base / calibrator fits',a.recorded_base_fits+' / '+a.recorded_calibrator_fits],['Recorded forecasts / scored rows',a.recorded_forecasts+' / '+a.recorded_scored_rows],['Before finalization',a.pre_finalization_seconds.toFixed(3)+' sec'],['Measured end to end',(a.end_to_end_seconds/60).toFixed(2)+' min']]);
 text('count-note',a.count_note);text('cost-note','Estimated full-host cost: $'+a.estimated_full_host_cost_usd.toFixed(4)+'. This is not a cloud invoice; time after the saved measurement is excluded.');
 facts('retained-facts',[['Completed jobs in the V089 tranche',r.completed_jobs+' / '+r.registered_jobs],['New base / calibrator fits in V089',r.base_fits+' / '+r.calibrator_fits],['Retained market / core jobs',r.market_jobs+' / '+r.core_jobs],['Registered pregame horizon','T'+r.horizon_minutes],['Compared policy/target identities',number(r.policy_target_identities)],['2024 / 2025 / 2026 completed games',r.cohorts.map(x=>number(x.games)).join(' / ')]]);
 for(const change of d.recovery.return_changes){const li=document.createElement('li');li.textContent=change;el('return-changes').append(li);}text('delivery-verification',p.verification_summary);text('prepared-status',p.status==='PREPARED_NOT_EXECUTED'?'Prepared · owner run pending':'Preparation in progress');
 for(const branch of p.branches){const tr=document.createElement('tr');for(const value of [branch.label,number(branch.jobs)]){const td=document.createElement('td');td.textContent=value;tr.append(td);}el('campaign-rows').append(tr);}text('blend-note',p.fixed_blend_policies+' fixed equal-weight blend policies add scoring work with zero estimator fits. Missing required members block a blend.');
 facts('worker-facts',[['Registered pregame horizon','T'+p.horizon_minutes],['Validation / frozen-test jobs',number(p.validation_jobs)+' / '+number(p.frozen_test_jobs)],['Scientific worker target / hard ceiling',p.minimum_target_workers+' / '+p.worker_ceiling],['Measured '+p.release+' optimizer cores','Pending owner execution'],['Compute guard','$'+p.cost_guard_usd],['Prepared owner executions / new fits','0 / 0']]);text('recovery-limit',d.recovery.remaining_limit);
 for(const pin of d.evidence){const li=document.createElement('li');const label=document.createElement('strong');label.textContent=pin.role+': ';const code=document.createElement('code');code.textContent=pin.sha256;li.append(label,code,document.createTextNode(' — '+pin.scope));el('evidence-list').append(li);}text('as-of','V091 incident reviewed '+pacific(i.reviewed_at)+'. Prior verified execution measured '+pacific(d.as_of)+'. Prepared evidence: '+pacific(p.evidence_as_of)+'.');
 el('unit').addEventListener('change',sizes);sizes();el('download').addEventListener('click',()=>{const blob=new Blob([JSON.stringify(d,null,2)+'\n'],{type:'application/json'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='FBS_V091_PUBLIC_EXECUTION_REVIEW.json';document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);});document.documentElement.dataset.ready='true';
 }catch(err){el('report').classList.add('hidden');el('error').classList.remove('hidden');text('error',err.message);document.documentElement.dataset.ready='error';}
})();
</script></body></html>
'''


def render(data):
    validate(data)
    payload = json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    payload = payload.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    return TEMPLATE.replace("__REPORT_JSON__", payload).encode("utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=PUBLIC / "data/status.json")
    parser.add_argument("--output", type=Path, default=PUBLIC / "index.html")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    data = json.loads(args.input.read_text())
    generated = render(data)
    if args.check:
        if args.output.read_bytes() != generated:
            raise SystemExit("Public page differs from authenticated aggregate input")
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_bytes(generated)
    print(json.dumps({"status": "PASS", "bytes": len(generated), "sha256": hashlib.sha256(generated).hexdigest(), "self_contained": True, "research_executions": 0}))


if __name__ == "__main__":
    main()

