#!/usr/bin/env python3
"""Render a dated public status from authenticated aggregate evidence only."""
from __future__ import annotations

import argparse
import copy
from datetime import datetime
import html
import json
import math
from pathlib import Path
import re
from zoneinfo import ZoneInfo

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "b100_execution_status.json"
OUTPUT = HERE / "b100_execution_status.html"


def validate(d):
    if d["owner"] != "NBA" or d["schema"] != "sel.nba.public_execution_status.b100.v1":
        raise ValueError("NBA aggregate schema required")
    if d["actual_owner_status"] != "PARTIAL_RESUMABLE" or any(d[k] for k in ("execution_complete", "full_v13_complete", "automatic_promotions")):
        raise ValueError("Observed partial work cannot become completed science")
    actual = d["b099_actual"]
    if actual["observed_owner_invocations"] != 1 or any(actual[k] for k in ("complete_owner_executions", "new_estimator_fits", "new_calibration_fits", "new_residual_distribution_fits", "publication_performed", "automatic_promotions")):
        raise ValueError("Separate actual work from unperformed fits and publication")
    forecast, dist, projection, cpu = (d[k] for k in ("current_forecast", "distribution", "projections", "cpu"))
    if (forecast["completed_feature_tasks"], forecast["deferred_feature_tasks"], dist["registered_base_tasks"], dist["deferred_base_tasks"]) != (1, 6, 160, 160):
        raise ValueError("Preserve incomplete queue evidence")
    if forecast["all_current_forecast_variants_completed"] or dist["completed_distribution_heads"]:
        raise ValueError("Blocked forecast and distribution work remains incomplete")
    if projection["new"] + projection["reused"] != projection["completed"] or projection["new_fits"]:
        raise ValueError("Projection materialization is not fitting")
    if (projection["new"], projection["reused"], projection["completed"]) != (3776, 2032, 5808):
        raise ValueError("Preserve authenticated new/reused projection counts")
    if cpu["measured_full_interval_passes"] or cpu["projection_interval_gate_pass"]:
        raise ValueError("Short low-occupancy export interval is not a throughput pass")
    expected = cpu["projection_cpu_seconds"] / cpu["projection_interval_seconds"]
    if not math.isclose(expected, cpu["projection_average_cores"], abs_tol=1e-9) or not math.isclose(expected / cpu["projection_capacity_cores"], cpu["projection_occupancy"], abs_tol=1e-9):
        raise ValueError("CPU claims require measured process CPU and wall time")
    pop = d["population"]
    if (pop["refreshed_completed_test_games"], pop["frozen_prediction_contract_completed_test_games"]) != (210, 206) or pop["full_census_verified"] or pop["current_forecast_refresh_completed"]:
        raise ValueError("Fresh population does not certify fresh forecasts or a full census")
    returned = d["latest_return"]
    if returned["scientific_status"] != "PARTIAL_RESUMABLE" or not returned["single_zip"] or returned["parts"] != 1 or returned["bytes"] != 340294167:
        raise ValueError("Preserve actual verified return evidence")
    if d["cost"]["actual_billed_cost_usd"] is not None:
        raise ValueError("Estimated whole-instance cost is not a billed allocation")
    prep = d["b100_preparation"]
    if any(prep[k] for k in ("new_owner_executions", "new_owner_estimator_fits", "new_owner_calibration_fits", "new_owner_distribution_fits", "new_owner_inference_rows", "new_owner_provider_requests", "research_launched_during_preparation")) or prep["owner_cpu_acceptance"] != "NOT_RUN":
        raise ValueError("Preparation cannot claim owner science or throughput")
    if prep["status"] not in {"IN_PREPARATION", "PREPARED_VERIFIED"}:
        raise ValueError("Unknown preparation state")
    if prep["status"] == "PREPARED_VERIFIED" and (prep["final_packaged_verification"] != "VERIFIED" or not isinstance(prep["canonical_engineering_tests"], int) or prep["canonical_engineering_tests"] <= 0 or any(prep[k] != 0 for k in ("engineering_failures", "engineering_errors", "engineering_skips"))):
        raise ValueError("Prepared certification requires final packaged checks")
    contract = d["scientific_contract"]
    if contract["selection_weights"] != [[50,50],[40,60],[30,70],[20,80],[10,90]] or contract["primary_validation_weight"] != [50,50]:
        raise ValueError("Validation weighting policies must remain declared")
    if any(contract[k] for k in ("test_outcomes_choose_models_or_calibration", "training_rows_reweighted_by_season", "previous_test_exposure_erased", "full_independent_game_census_proven", "qualified_full_season_champion")):
        raise ValueError("Scientific limitations must remain explicit")
    if d["publication"]["new_public_forecast_values"] or d["publication"]["historical_scientific_assets_changed"]:
        raise ValueError("Aggregate status cannot change historical science")
    text = json.dumps(d)
    if re.search(r"s3://|/home/sagemaker-user|arn:aws:|AKIA[A-Z0-9]{16}|\.pyz\b|\b(?:model_id|base_id|feature_names)\b", text, re.I):
        raise ValueError("Private owner locations and recipe details are excluded")
    for digest in (d["evidence"]["execution_report_sha256"], d["evidence"]["post_seal_delivery_sha256"], returned["sha256"]):
        if not re.fullmatch(r"[a-f0-9]{64}", digest):
            raise ValueError("Evidence digests must be complete SHA-256 values")
    return d


def pacific(utc):
    return datetime.fromisoformat(utc.replace("Z", "+00:00")).astimezone(ZoneInfo("America/Los_Angeles")).strftime("%b %d, %Y · %I:%M %p Pacific")


def render(data):
    d = validate(data)
    e = html.escape
    actual, forecast, dist, projections, cpu, returned, cost, prep = (d[k] for k in ("b099_actual", "current_forecast", "distribution", "projections", "cpu", "latest_return", "cost", "b100_preparation"))
    prepared = prep["status"] == "PREPARED_VERIFIED"
    heading = "B100 replacement verified; owner execution pending" if prepared else "B100 replacement in preparation"
    gaps = "".join(f"<li>{e(gap)}</li>" for gap in d["scientific_contract"]["remaining_gaps"])
    embedded = json.dumps(d, ensure_ascii=False, indent=2).replace("<", "\\u003c")
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>NBA execution review · B099 partial return and B100 continuation</title>
<meta name="description" content="Verified NBA execution aggregates distinguish completed retrieval and export, deferred science, measured CPU, return integrity and B100 preparation.">
<style>
:root{{color-scheme:light;--ink:#17313e;--muted:#52656e;--navy:#152e3a;--paper:#f2f5f1;--line:#d5ded9;--amber:#8d441f}}*{{box-sizing:border-box}}html{{scroll-behavior:smooth}}body{{margin:0;background:var(--paper);color:var(--ink);font:16px/1.65 system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}}a{{color:#245d4b;text-underline-offset:4px}}a:focus-visible,button:focus-visible,[tabindex]:focus-visible{{outline:3px solid #ad681b;outline-offset:5px}}.wrap{{max-width:1180px;margin:auto;padding:0 28px}}header{{background:var(--navy);color:#f8faf6;padding:26px 0 42px}}.mast{{display:flex;gap:18px;justify-content:space-between;margin-bottom:28px;font-size:12px;letter-spacing:.10em;text-transform:uppercase}}.mast a{{color:inherit}}.eyebrow{{color:#efcba8;font-size:12px;font-weight:750;letter-spacing:.12em;text-transform:uppercase}}h1{{max-width:960px;font-size:clamp(36px,5vw,58px);line-height:1.1;letter-spacing:-.04em;margin:12px 0 20px}}.intro{{max-width:890px;font-size:18px;color:#dce6e1}}.badge{{display:inline-block;border-radius:4px;padding:6px 11px;background:#fae5d3;color:#663a1c;font-size:13px;font-weight:750;margin-top:8px}}main{{padding-top:26px!important;padding-bottom:42px!important}}.cards{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:22px}}.card,.panel{{background:#fff;border:1px solid var(--line);border-radius:8px;padding:24px}}.card strong{{display:block;font-size:34px;letter-spacing:-.03em;line-height:1.2}}.card span{{display:block;font-size:13px;color:var(--muted);margin-top:8px}}.panel{{margin-bottom:22px}}.blocked{{border-top:4px solid var(--amber)}}.columns{{display:grid;grid-template-columns:1.15fr 1fr;gap:22px}}h2{{font-size:24px;line-height:1.25;letter-spacing:-.02em;margin:0 0 14px}}h3{{font-size:17px;line-height:1.35;margin:22px 0 8px}}p{{margin:0 0 14px}}p:last-child{{margin-bottom:0}}.muted,small{{color:var(--muted)}}.scroll{{overflow-x:auto;max-width:100%}}table{{border-collapse:collapse;width:100%;font-size:14px}}th,td{{padding:12px 10px;text-align:left;vertical-align:top;border-bottom:1px solid var(--line)}}thead th{{font-size:12px;color:var(--muted)}}tbody th{{min-width:155px}}td{{min-width:105px}}.note{{padding:14px 16px;background:#faf1e6;border-left:3px solid #b77327;margin:16px 0}}.links{{display:flex;flex-wrap:wrap;gap:14px 24px;margin-top:18px}}.mono{{font:12px/1.6 ui-monospace,monospace;overflow-wrap:anywhere}}ul{{padding-left:21px;margin:10px 0}}li{{margin:8px 0}}button{{font:inherit;font-weight:650;border:1px solid #245d4b;color:#fff;background:#245d4b;border-radius:5px;padding:10px 16px;cursor:pointer}}footer{{border-top:1px solid var(--line);padding-top:20px;color:var(--muted);font-size:13px}}@media(max-width:720px){{.wrap{{padding:0 18px}}.mast{{display:block}}.mast span{{display:block;margin-top:8px}}.cards{{grid-template-columns:repeat(2,1fr);gap:10px}}.card,.panel{{padding:18px}}.card strong{{font-size:30px}}.columns{{grid-template-columns:1fr;gap:0}}h2{{font-size:22px}}.intro{{font-size:17px}}.links{{display:grid;gap:12px}}}}@media(prefers-reduced-motion:reduce){{html{{scroll-behavior:auto}}}}
</style></head><body>
<header><div class="wrap"><div class="mast"><a href="../README.md">Sports Edge Lab / NBA</a><span>{e(pacific(d['snapshot_at_utc']))}</span></div><p class="eyebrow">Actual owner continuation · verified partial return</p><h1>Retrieval and export finished.<br>The scientific queues did not.</h1><p class="intro">B099 refreshed current inputs and completed private export projections. Current forecasts and residual distributions remained blocked by CPU-capacity admission. The owner request for measured 12–24-core scientific throughput remains unmet.</p><span class="badge">PARTIAL_RESUMABLE · no new fits · no full-capacity pass</span></div></header>
<main class="wrap">
<div class="cards" aria-label="Actual B099 counters"><div class="card"><strong data-metric="new-projections">{projections['new']:,}</strong><span>new private export projections</span></div><div class="card"><strong data-metric="provider-requests">{actual['new_provider_requests']}</strong><span>provider requests; zero recorded credits</span></div><div class="card"><strong data-metric="new-fits">0</strong><span>new estimator, calibration or distribution fits</span></div><div class="card"><strong data-metric="completed-games">{forecast['current_completed_games']}</strong><span>completed games in refreshed test inputs</span></div></div>
<section class="panel blocked"><h2>What completed, and what remains deferred</h2><p>One B099 owner continuation is observed. It produced useful retrieval and export work, but no completed owner research campaign. Checkpoints and earlier fitted components remain preserved.</p><div class="scroll" role="region" aria-label="Actual stage outcomes" tabindex="0"><table class="stages"><thead><tr><th scope="col">Work</th><th scope="col">Completed</th><th scope="col">Unfinished or qualified</th></tr></thead><tbody><tr><th scope="row">Current input refresh</th><td>{actual['new_provider_requests']} provider requests</td><td>Refreshed test inputs contain 210 completed games; full independent census remains unverified.</td></tr><tr><th scope="row">Current forecast preparation</th><td>{forecast['completed_feature_tasks']} preparation task</td><td>{forecast['deferred_feature_tasks']} tasks deferred; current forecast refresh incomplete.</td></tr><tr><th scope="row">Residual-distribution preparation</th><td>{dist['completed_base_tasks']} of {dist['registered_base_tasks']} base tasks</td><td>{dist['deferred_base_tasks']} deferred; zero new distribution fits.</td></tr><tr><th scope="row">Private export projections</th><td>{projections['completed']:,} verified: {projections['new']:,} new + {projections['reused']:,} reused</td><td>Projection materialization of saved predictions; no new estimator fit or certified current forecast.</td></tr><tr><th scope="row">Private logical exports</th><td>{projections['independent_exports']} exports</td><td>Private preview created; no public publication or production promotion.</td></tr></tbody></table></div><div class="note">The six forecast-preparation tasks and all 160 residual-input tasks were deferred by the capacity-admission path. An empty top-level fit-failure list does not mean those queues completed.</div></section>
<div class="columns"><section class="panel"><h2>Measured CPU remains below the request</h2><p>The export projection pool reached <strong>{projections['peak_processes']} concurrent processes</strong>. Its measured interval used <strong>{cpu['projection_average_cores']:.2f} average cores</strong>, or <strong>{cpu['projection_occupancy']*100:.2f}% of 24 admitted cores</strong>, over <strong>{cpu['projection_interval_seconds']:.2f} seconds</strong>.</p><p>That is {cpu['projection_cpu_seconds']:.2f} measured process CPU-seconds, with <strong>zero full three-minute occupancy passes</strong>. It measures private export work, not fitted scientific workers.</p><p>The current-forecast preparation stage peaked at one process and deferred six tasks. The residual-input queue remained ready but admitted no completed task.</p><p class="muted">A 24-worker ceiling, a peak process count and earlier B097 throughput do not establish sustained 12–24-core performance for this continuation.</p></section><section class="panel"><h2>Fresh inputs are not fresh forecasts</h2><p>The refreshed input population records <strong>210 completed 2026–27 games</strong>. The frozen prediction contract still records <strong>206 completed games</strong>, because current-forecast preparation did not finish.</p><p>The declared current population contains {forecast['current_population_games']:,} completed and scheduled games. It is not a verified full-season census. Validation populations preserve 1,314 and 1,315 completed games for 2024–25 and 2025–26, with unresolved all-competition coverage.</p><p><strong>No new current public forecasts are added by this status page.</strong> Saved game forecasts retain their original issue, reconstruction and exposure labels.</p></section></div>
<div class="columns"><section class="panel"><h2>A compact, verified return</h2><p>The return is <strong>one ZIP, {returned['bytes']:,} bytes</strong>, with <strong>{returned['payloads']:,} verified payloads</strong>. Its whole-archive SHA-256 and member integrity were verified.</p><p>The status remains <strong>PARTIAL_RESUMABLE</strong>. Successful delivery preserves unfinished work; it does not certify scientific completion or a new champion.</p><p class="muted">This fixes the earlier oversized continuation packaging outcome without altering the dated record of that failure.</p></section><section class="panel"><h2>Cost is an estimate, not an invoice</h2><p>The ledger through delivery estimates <strong>USD {float(cost['whole_instance_wall_interval_estimate_usd']):.4f}</strong> for its whole-instance wall-time interval. The actual billed amount and NBA's allocation on the shared instance are unknown.</p><p>The compute guard remains <strong>USD {float(cost['budget_usd']):.0f}</strong>. It is a ceiling, not the amount reported as spent. Zero provider credits do not imply zero infrastructure cost.</p><p class="muted">Retrieval, projection work, new fitting, CPU evidence and estimated spend remain separate measures.</p></section></div>
<section class="panel" id="b100-preparation"><p class="eyebrow" style="color:var(--amber)">Next deliverable · owner launch remains separate</p><h2>{heading}</h2><p>{e(prep['verification_summary'])}</p><div class="columns"><div><h3>Resume the work still owed</h3><ul><li>Keep queued work resumable through temporary CPU-capacity loss, with bounded waiting, unchanged safety thresholds and real worker accounting.</li><li>Resolve the newest durable checkpoint at launch and reuse completed retrieval, projections, model fits and safe task caches.</li><li>Complete eligible current forecasts from locked fitted components and resume up to {prep['planned_distribution_heads']} registered residual-distribution heads.</li><li>Keep current test outcomes out of fitting, calibration, blend selection and champion selection.</li></ul></div><div><h3>Required owner acceptance</h3><p>Target {prep['default_scientific_workers']} scientific workers, opportunistically up to {prep['opportunistic_scientific_workers']} when configured and safely available. Explicit worker limits remain hard ceilings; each worker's native threads are bounded.</p><p>Independent {prep['log_interval_seconds']}-second logs must record real PIDs, CPU, completions, queue conditions and starvation. A capacity pass requires {prep['occupancy_minimum_percent']}% occupancy over {prep['occupancy_interval_seconds']} seconds when sufficient independent real work and safe capacity exist.</p><p><strong>Zero B100 owner executions, fits or inference rows are credited here.</strong> Engineering tests do not supply a scientific occupancy pass.</p></div></div></section>
<section class="panel"><h2>Preserved science and remaining qualification</h2><p>The earlier B097 evidence retains <strong>672 new estimator fits, 1,232 new calibration fits</strong> and <strong>5,808 scored variants with uncertainty reports</strong>. Its fitting stage previously passed a measured occupancy interval; its export failed. B098 then recorded two pre-dispatch failures. Those dated outcomes remain available below.</p><p>Use 2024–25 and 2025–26 validation metrics with <strong>50/50 as the primary selection policy</strong>; report 40/60, 30/70, 20/80 and 10/90 sensitivity without reweighting training rows or refitting for the evaluation ratio. Completed 2026–27 games, including postseason, are test observations only. Previous test exposure cannot be erased.</p><ul>{gaps}</ul><p><strong>No qualified full-season champion or full V13 completion is claimed.</strong> Market overlap remains separate from the full eligible population.</p></section>
<section class="panel"><h2>Evidence and publication</h2><p>B099 science receipt finished {e(pacific(actual['finished_at_utc']))}. Through-delivery cost receipt: {e(pacific(cost['observed_at_utc']))}. The authenticated execution report and post-seal delivery receipt were rehashed in full before this projection.</p><p class="muted">Execution report SHA-256</p><p class="mono">{d['evidence']['execution_report_sha256']}</p><p class="muted">Verified return SHA-256</p><p class="mono">{returned['sha256']}</p><p><strong>Draft source review · main integration pending · website deployment pending.</strong> B100 owner execution and production promotion are separate events. No historical scientific assets, forecast values or original issue clocks are changed.</p><button id="download-status" type="button">Download aggregate evidence JSON</button><div class="links"><a href="b099_execution_status.html">Dated B098 failures / B099 preparation</a><a href="b098_execution_status.html">Dated B097 / B098 preparation</a><a href="b095_review.html">Saved validation and source-coverage review</a><a href="season_comparison.html">Previously issued selected forecasts</a></div><noscript><p><a href="b100_execution_status.json">Open the adjacent aggregate JSON</a>.</p></noscript></section>
<footer>Sports Edge Lab · NBA only. {e(d['evidence_scope'])} Private delivery locations, active recipes, fitted model bodies and raw provider records are excluded.</footer></main>
<script id="aggregate-evidence" type="application/json">{embedded}</script><script>
'use strict';
document.getElementById('download-status').addEventListener('click', () => {{
const data = JSON.parse(document.getElementById('aggregate-evidence').textContent);
const blob = new Blob([JSON.stringify(data,null,2)+'\\n'],{{type:'application/json'}});
const url = URL.createObjectURL(blob), link = document.createElement('a');
link.href=url;link.download='b100_execution_status.json';document.body.appendChild(link);link.click();link.remove();
setTimeout(() => URL.revokeObjectURL(url),1000);
}});
</script></body></html>
'''


def negative_checks(data):
    cases = [
        (("execution_complete",), True), (("full_v13_complete",), True),
        (("b099_actual", "new_estimator_fits"), 3776),
        (("b099_actual", "complete_owner_executions"), 1),
        (("current_forecast", "all_current_forecast_variants_completed"), True),
        (("current_forecast", "deferred_feature_tasks"), 0),
        (("distribution", "completed_distribution_heads"), 320),
        (("projections", "new_fits"), 3776),
        (("projections", "reused"), 0),
        (("cpu", "projection_average_cores"), 24),
        (("cpu", "measured_full_interval_passes"), 1),
        (("population", "frozen_prediction_contract_completed_test_games"), 210),
        (("population", "full_census_verified"), True),
        (("latest_return", "scientific_status"), "COMPLETE"),
        (("cost", "actual_billed_cost_usd"), 0.4785),
        (("b100_preparation", "new_owner_executions"), 1),
        (("b100_preparation", "owner_cpu_acceptance"), "PASS"),
        (("b100_preparation", "final_packaged_verification"), "PENDING"),
        (("scientific_contract", "training_rows_reweighted_by_season"), True),
        (("scientific_contract", "test_outcomes_choose_models_or_calibration"), True),
        (("evidence", "public_projection_scope"), "s3://private-owner/runner"),
        (("publication", "new_public_forecast_values"), 1),
    ]
    for route, value in cases:
        candidate = copy.deepcopy(data)
        target = candidate
        for key in route[:-1]:
            target = target[key]
        target[route[-1]] = value
        if route == ("b100_preparation", "final_packaged_verification"):
            candidate["b100_preparation"]["status"] = "PREPARED_VERIFIED"
        try:
            validate(candidate)
        except ValueError:
            continue
        raise AssertionError(f"Unsupported evidence accepted: {route}")
    return len(cases)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    data = json.loads(SOURCE.read_text())
    rendered = render(data)
    rejected = negative_checks(data) if args.self_test else 0
    if args.check:
        if OUTPUT.read_text() != rendered:
            raise SystemExit("B100 aggregate HTML differs from authenticated projection")
    else:
        OUTPUT.write_text(rendered)
    print(json.dumps({"status":"PASS", "check":args.check, "unsupported_claims_rejected":rejected, "owner_executions":0, "new_owner_fits":0}))


if __name__ == "__main__":
    main()
