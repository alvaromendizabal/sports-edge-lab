#!/usr/bin/env python3
"""Render a bounded, offline NBA status projection; never run owner research."""
from __future__ import annotations

import argparse
import copy
import html
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "b099_execution_status.json"
OUTPUT = HERE / "b099_execution_status.html"


def validate(data):
    if data["owner"] != "NBA" or data["schema"] != "sel.nba.public_execution_status.b099.v1":
        raise ValueError("NBA status schema required")
    if data["execution_complete"] or data["full_v13_complete"] or data["automatic_promotions"]:
        raise ValueError("Failed owner attempts cannot become completed science or promotion")
    if len(data["attempts"]) != 2:
        raise ValueError("The dated attempt scope must remain explicit")
    for attempt in data["attempts"]:
        if attempt["exit_code"] != 2 or any(attempt[k] for k in (
            "scientific_workers_dispatched", "new_estimator_fits", "new_calibration_fits",
            "new_provider_requests", "occupancy_pass"
        )):
            raise ValueError("These pre-dispatch failures have no new scientific credit")
    latest = data["latest_attempt"]
    if latest["scientific_cpu_sample_count"] != 0 or latest["measured_scientific_cores"] is not None:
        raise ValueError("Missing CPU samples must remain unknown, not measured zero")
    if latest["full_interval_occupancy_passes"] or latest["new_verified_science_commits"]:
        raise ValueError("A requested worker count is not a measured capacity pass")
    if latest["actual_billed_cost_usd"] is not None:
        raise ValueError("The actual billed cost is not established by the wall estimate")
    returned = data["latest_return"]
    if returned["scientific_status"] != "PARTIAL_RESUMABLE" or returned["integrity_is_scientific_completion"]:
        raise ValueError("Physical integrity cannot upgrade scientific completion")
    prep = data["b099_preparation"]
    if any(prep[k] for k in ("new_owner_executions", "new_owner_estimator_fits",
                            "new_owner_calibration_fits", "new_owner_distribution_fits",
                            "owner_throughput_pass", "full_v13_complete")):
        raise ValueError("Preparation cannot claim owner execution or scientific capacity")
    if prep.get("new_owner_inference_rows", 0) or prep.get("new_owner_provider_requests", 0):
        raise ValueError("Delivery preparation cannot claim inference or provider retrievals")
    if prep["status"] not in {"PREPARATION_IN_PROGRESS", "PREPARED_VERIFIED"}:
        raise ValueError("Unknown preparation state")
    if prep["status"] == "PREPARED_VERIFIED" and prep["final_packaged_verification"] != "VERIFIED":
        raise ValueError("Prepared verification needs final packaged evidence")
    contract = data["scientific_contract"]
    if any(contract[k] for k in ("test_outcomes_choose_models_or_calibration", "training_rows_reweighted_by_season",
                               "previous_test_exposure_erased", "full_independent_game_census_proven",
                               "qualified_full_season_champion")):
        raise ValueError("Scientific limitations must remain explicit")
    if contract["selection_weights"] != [[50, 50], [40, 60], [30, 70], [20, 80], [10, 90]]:
        raise ValueError("Declared evaluation sensitivity policies changed")
    public = data["publication"]
    if public["new_public_forecast_values"] or public["historical_scientific_assets_changed"]:
        raise ValueError("This status-only projection cannot alter saved scientific values")
    raw = json.dumps(data)
    if re.search(r"s3://|/home/sagemaker-user|arn:aws:|AKIA[A-Z0-9]{16}|\.pyz\b", raw, re.I):
        raise ValueError("Private delivery information is excluded from the public projection")
    for value in (data["evidence"]["latest_execution_report_sha256"], returned["logical_sha256"]):
        if not re.fullmatch(r"[a-f0-9]{64}", value):
            raise ValueError("Evidence digests must be complete SHA-256 values")
    return data


def render(data):
    d = validate(data)
    esc = html.escape
    latest, returned, previous, prep = (d[k] for k in (
        "latest_attempt", "latest_return", "preserved_b097", "b099_preparation"))
    attempts = "".join(
        f'<tr><th scope="row">{esc(a["run_at_utc"].replace("T", " ").replace("Z", " UTC"))}</th>'
        f'<td>{a["exit_code"]}</td><td>{a["new_estimator_fits"]} / {a["new_calibration_fits"]}</td>'
        f'<td>{a["new_provider_requests"]}</td><td>{esc(a["failure_class"])}; before scientific dispatch</td></tr>'
        for a in d["attempts"]
    )
    gaps = "".join(f"<li>{esc(v)}</li>" for v in d["scientific_contract"]["remaining_gaps"])
    embedded = json.dumps(d, ensure_ascii=False, indent=2).replace("<", "\\u003c")
    prepared = prep["status"] == "PREPARED_VERIFIED"
    prep_heading = "B099 package verified; native installation pending" if prepared else "B099 preparation in progress"
    prep_badge = "Remote delivery verified · native preflight and owner execution pending" if prepared else "Final package verification and staging pending"
    prep_evidence = esc(prep.get("verification_summary", "Final package checks and private staging have not yet been certified in this dated public snapshot."))
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>NBA execution review · B098 startup failures and B099 preparation</title>
<meta name="description" content="NBA execution accounting separates failed startup, preserved research, return integrity and pending owner verification.">
<style>
:root{{color-scheme:light;--ink:#17313e;--muted:#52656e;--navy:#152e3a;--paper:#f2f5f1;--line:#d5ded9;--amber:#8d441f}}*{{box-sizing:border-box}}html{{scroll-behavior:smooth}}body{{margin:0;background:var(--paper);color:var(--ink);font:16px/1.65 system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}}a{{color:#245d4b;text-underline-offset:4px}}a:focus-visible,button:focus-visible,[tabindex]:focus-visible{{outline:3px solid #ad681b;outline-offset:5px}}.wrap{{max-width:1180px;margin:auto;padding:0 28px}}header{{background:var(--navy);color:#f8faf6;padding:26px 0 42px}}.mast{{display:flex;gap:18px;justify-content:space-between;margin-bottom:28px;font-size:12px;letter-spacing:.10em;text-transform:uppercase}}.mast a{{color:inherit}}.eyebrow{{color:#efcba8;font-size:12px;font-weight:750;letter-spacing:.12em;text-transform:uppercase}}h1{{max-width:920px;font-size:clamp(36px,5vw,58px);line-height:1.1;letter-spacing:-.04em;margin:12px 0 20px}}.intro{{max-width:870px;font-size:18px;color:#dce6e1}}.badge{{display:inline-block;border-radius:4px;padding:6px 11px;background:#fae5d3;color:#663a1c;font-size:13px;font-weight:750;margin-top:8px}}main{{padding-top:26px!important;padding-bottom:42px!important}}.cards{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:22px}}.card,.panel{{background:#fff;border:1px solid var(--line);border-radius:8px;padding:24px}}.card strong{{display:block;font-size:34px;letter-spacing:-.03em;line-height:1.2}}.card span{{display:block;font-size:13px;color:var(--muted);margin-top:8px}}.panel{{margin-bottom:22px}}.failure{{border-top:4px solid var(--amber)}}.columns{{display:grid;grid-template-columns:1.15fr 1fr;gap:22px}}h2{{font-size:24px;line-height:1.25;letter-spacing:-.02em;margin:0 0 14px}}h3{{font-size:17px;line-height:1.35;margin:22px 0 8px}}p{{margin:0 0 14px}}p:last-child{{margin-bottom:0}}.muted,small{{color:var(--muted)}}.scroll{{overflow-x:auto;max-width:100%}}table{{border-collapse:collapse;width:100%;font-size:14px}}th,td{{padding:12px 10px;text-align:left;vertical-align:top;border-bottom:1px solid var(--line)}}thead th{{font-size:12px;color:var(--muted)}}tbody th{{min-width:160px}}td{{min-width:100px}}.attempts td:last-child{{min-width:240px}}.note{{padding:14px 16px;background:#faf1e6;border-left:3px solid #b77327;margin:16px 0}}.links{{display:flex;flex-wrap:wrap;gap:14px 24px;margin-top:18px}}.mono{{font:12px/1.6 ui-monospace,monospace;overflow-wrap:anywhere}}ul{{padding-left:21px;margin:10px 0}}li{{margin:8px 0}}button{{font:inherit;font-weight:650;border:1px solid #245d4b;color:#fff;background:#245d4b;border-radius:5px;padding:10px 16px;cursor:pointer}}.statusline{{font-weight:650}}footer{{border-top:1px solid var(--line);padding-top:20px;color:var(--muted);font-size:13px}}@media(max-width:720px){{.wrap{{padding:0 18px}}.mast{{display:block}}.mast span{{display:block;margin-top:8px}}.cards{{grid-template-columns:repeat(2,1fr);gap:10px}}.card,.panel{{padding:18px}}.card strong{{font-size:30px}}.columns{{grid-template-columns:1fr;gap:0}}h2{{font-size:22px}}.intro{{font-size:17px}}.links{{display:grid;gap:12px}}}}@media(prefers-reduced-motion:reduce){{html{{scroll-behavior:auto}}}}
</style>
</head>
<body>
<header><div class="wrap"><div class="mast"><a href="../README.md">Sports Edge Lab · NBA</a><span>Execution evidence · November 18, 2026</span></div><p class="eyebrow">Two observed B098 attempts failed</p><h1>Startup failed before<br>scientific work began.</h1><p class="intro">Both B098 attempts stopped while loading preserved inputs. Requesting 24 cores did not produce a scientific worker dispatch or a measured throughput pass. Earlier B097 fits remain preserved; the full V13 program remains incomplete.</p><span class="badge">Partial and resumable · no production promotion</span></div></header>
<main class="wrap">
<section class="cards" aria-label="Observed B098 outcome"><div class="card"><strong data-metric="failed-attempts">2</strong><span>Observed failed owner attempts</span></div><div class="card"><strong data-metric="new-fits">0</strong><span>New estimator or calibration fits</span></div><div class="card"><strong data-metric="cpu-samples">0</strong><span>Scientific CPU samples in latest attempt</span></div><div class="card"><strong data-metric="return-parts">{returned["ordered_parts"]}</strong><span>Verified parts; science still partial</span></div></section>
<div class="columns">
<section class="panel failure"><h2>What failed, and why</h2><p>The saved population producer returned a container with a <strong>records array</strong>. The frozen-input consumer required a bare list. Both attempts rejected the preserved population at that boundary, before dispatching scientific workers.</p><p>The earlier engineering checks did not exercise this actual latest-checkpoint consumer with the wrapped population. Their passing result did not establish launch readiness for the owner&rsquo;s next run.</p><p class="muted">The latest scientific attempt reported {latest["reported_science_elapsed_seconds"]:.2f} seconds before the stop. Return verification and packaging continued separately. Startup failure is not evidence that the available scientific workload was completed.</p></section>
<section class="panel"><h2>What the 24-core request proved</h2><p>It proved a <strong>configured request</strong>, not useful work. The latest receipt contains no scientific CPU samples, no full-interval capacity passes and no new verified science commits.</p><p><strong>Measured scientific cores are unknown.</strong> Missing measurements are not a measured zero-core average. This attempt never reached the stage needed to verify 12–24-core throughput.</p><div class="note"><strong>Completion remains false.</strong> Return integrity, a printed worker limit and engineering tests each answer a different question from completed scientific work.</div></section>
</div>
<section class="panel"><h2>Actual owner attempts</h2><p>{esc(d["evidence_scope"])}</p><div class="scroll" role="region" aria-label="B098 owner attempt table" tabindex="0"><table class="attempts"><thead><tr><th scope="col">Run identity clock</th><th scope="col">Exit</th><th scope="col">New estimator / calibration fits</th><th scope="col">Provider requests</th><th scope="col">Outcome</th></tr></thead><tbody>{attempts}</tbody></table></div><p class="muted" style="margin-top:14px">The first invocation waited for its predecessor before the run identity above was created. Earlier duplicate-launch refusals and B095 initialization failures remain in their dated reports; these two rows are not an all-time execution total.</p></section>
<div class="columns">
<section class="panel"><h2>The return is verified and partial</h2><p>The latest sealed logical return contains <strong>{returned["logical_bytes"]:,} bytes in {returned["ordered_parts"]} ordered parts</strong> and {returned["payloads"]:,} payloads. Integrity verification succeeded. The scientific status remains <strong>PARTIAL_RESUMABLE</strong>.</p><p>Packaging re-embedded {returned["observed_redundant_prior_identities_reembedded"]:,} previously preserved identities after transitive continuation references were lost from the reuse lookup. That transfer volume does not represent new fits or completed research.</p><p class="muted">B099 preparation adds transitive reference reuse and bounded proof caching. The next owner execution still has to demonstrate successful final delivery and checkpoint reuse.</p></section>
<section class="panel"><h2>Cost remains qualified</h2><p>The latest whole-instance wall interval was estimated at <strong>USD {float(latest["whole_instance_wall_interval_estimate_usd"]):.4f}</strong>. The actual invoiced cost and the share attributable to NBA are unknown.</p><p>The <strong>USD {latest["guard_usd"]} compute guard</strong> was a ceiling, not an amount shown as spent. A zero wall-time limit does not remove that guard.</p><p class="muted">Scientific CPU, packaging work, data retrieval and cost are reported separately. Zero provider retrievals do not mean zero infrastructure cost.</p></section>
</div>
<section class="panel"><h2>Preserved B097 science still counts</h2><p>B097 recorded <strong>{previous["new_estimator_fits"]:,} new estimator fits</strong>, <strong>{previous["new_calibration_fits"]:,} new calibration fits</strong>, {previous["reused_estimator_fits"]} reused estimators and {previous["reused_calibration_fits"]} reused calibrators. It completed {previous["completed_base_jobs"]} base jobs and {previous["completed_scored_variants_and_uncertainty_reports"]:,} scored variants with uncertainty reports, with zero failed estimator jobs and four provider requests.</p><div class="scroll" role="region" aria-label="Preserved B097 throughput table" tabindex="0"><table><thead><tr><th scope="col">B097 stage</th><th scope="col">Measured cores</th><th scope="col">Occupancy</th><th scope="col">Observation</th></tr></thead><tbody><tr><th scope="row">Context preparation and fitting</th><td>{previous["fit_measured_cores"]:.2f} / 24 admitted</td><td>{previous["fit_occupancy_percent"]:.2f}% over {previous["fit_interval_seconds"]:.2f}s</td><td>Passed the measured three-minute gate</td></tr><tr><th scope="row">Private prediction export</th><td>{previous["private_export_measured_cores"]:.2f} / 24 gate cores</td><td>{previous["private_export_occupancy_percent"]:.2f}% over {previous["private_export_interval_seconds"]:.2f}s</td><td>Failed with {previous["private_export_pending_jobs"]:,} jobs pending; pool configured for one worker</td></tr></tbody></table></div><p class="muted" style="margin-top:14px">The fitting pass does not carry over to the failed export or either B098 attempt. Preserved scientific work remains reusable; it does not certify full-season champions or a completed V13 campaign.</p></section>
<section class="panel" id="b099-preparation"><p class="eyebrow" style="color:var(--amber)">Next deliverable</p><h2>{prep_heading}</h2><p><strong>{prep_badge}.</strong> {prep_evidence}</p><div class="columns"><div><h3>Work registered for the owner run</h3><ul><li>Decode the authenticated saved population consistently and verify the actual resume path before scientific dispatch.</li><li>Refresh eligible current forecasts from locked model, calibration and blend states, using causal pregame inputs and stable task caches.</li><li>Fit up to <strong>{prep["planned_distribution_heads"]} registered residual-distribution heads</strong> from authenticated prevalidation held-out history. Count these separately from base estimator and winner-calibration fits.</li><li>Evaluate distribution quality and authentic contract probabilities only where settlement, source rights and information clocks are qualified.</li></ul></div><div><h3>Throughput still requires owner evidence</h3><p>Target {prep["default_scientific_workers"]} scientific workers, opportunistically up to {prep["opportunistic_scientific_workers"]} when configured and safely available. Explicit worker limits remain hard ceilings, native threads are bounded, and both context preparation and fitting need real process accounting.</p><p>Independent {prep["log_interval_seconds"]}-second logs must show worker PIDs, CPU, completions and queue conditions. The {prep["occupancy_minimum_percent"]}% occupancy gate needs {prep["occupancy_interval_seconds"]} seconds of sufficient independent real work and safe capacity.</p><p><strong>Zero B099 owner executions and zero new owner fits are credited by this preparation snapshot.</strong> Engineering fixtures cannot supply a scientific throughput pass.</p></div></div></section>
<div class="columns">
<section class="panel"><h2>Scientific rules for continuation</h2><p>Use 2024–25 and 2025–26 for validation, with <strong>50/50 as the primary selection policy</strong> and 40/60, 30/70, 20/80 and 10/90 sensitivity reports. Changing these evaluation ratios must not refit estimators or reweight training rows by season.</p><p>Every completed 2026–27 game belongs to the test manifest once eligible and authenticated, including postseason. Test outcomes do not select features, hyperparameters, calibrators, residual distributions, blends or champions.</p><p>Already inspected test results remain exposed. A historical reconstruction cannot acquire an original issue clock through replay or later retrieval.</p></section>
<section class="panel"><h2>What still blocks full completion</h2><ul>{gaps}</ul><p><strong>No qualified full-season champion or full V13 completion is claimed.</strong> Missing histories remain gaps; they are not replaced with invented market inputs or a smaller common population.</p></section>
</div>
<section class="panel"><h2>Evidence and publication</h2><p>Latest science receipt: <strong>{esc(latest["science_finished_at_utc"].replace("T", " "))}</strong>. Authenticated report: {d["evidence"]["latest_execution_report_bytes"]:,} bytes. Physical SHA-256:</p><p class="mono">{d["evidence"]["latest_execution_report_sha256"]}</p><p>Verified logical return SHA-256:</p><p class="mono">{returned["logical_sha256"]}</p><p class="statusline">Draft source review · main integration pending · website deployment pending · owner B099 execution pending</p><p>This public status projection adds no forecast values or model-performance metrics. Saved scientific reports, selected original issues and provider comparisons retain their original evidence clocks. Source publication, deployment, scientific completion and production promotion are separate events.</p><button id="download-status" type="button">Download aggregate evidence JSON</button><div class="links"><a href="b098_execution_status.html">Earlier B097 / B098 preparation snapshot</a><a href="b095_review.html">Saved validation and source-coverage review</a><a href="season_comparison.html">Previously issued selected forecasts</a></div><noscript><p>JavaScript is required only for the embedded download. <a href="b099_execution_status.json">Open the adjacent aggregate JSON</a>.</p></noscript></section>
<footer>Sports Edge Lab · NBA only. Dated public status: {esc(d["snapshot_at_utc"].replace("T", " ").replace("Z", " UTC"))}. Operational claims are bounded to the authenticated evidence described above. Private delivery details, active recipes, fitted model bodies and raw provider records are excluded.</footer>
</main>
<script id="aggregate-evidence" type="application/json">{embedded}</script>
<script>
'use strict';
document.getElementById('download-status').addEventListener('click', () => {{
  const data = JSON.parse(document.getElementById('aggregate-evidence').textContent);
  const blob = new Blob([JSON.stringify(data, null, 2) + '\\n'], {{type:'application/json'}});
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url; link.download = 'b099_execution_status.json';
  document.body.appendChild(link); link.click(); link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}});
</script>
</body>
</html>
'''


def negative_checks(data):
    cases = [
        (("execution_complete",), True), (("full_v13_complete",), True),
        (("automatic_promotions",), 1), (("latest_attempt", "measured_scientific_cores"), 0),
        (("latest_attempt", "full_interval_occupancy_passes"), 1),
        (("latest_attempt", "actual_billed_cost_usd"), 0),
        (("latest_return", "integrity_is_scientific_completion"), True),
        (("b099_preparation", "new_owner_executions"), 1),
        (("b099_preparation", "owner_throughput_pass"), True),
        (("b099_preparation", "new_owner_inference_rows"), 1),
        (("b099_preparation", "new_owner_provider_requests"), 1),
        (("scientific_contract", "test_outcomes_choose_models_or_calibration"), True),
        (("scientific_contract", "training_rows_reweighted_by_season"), True),
        (("scientific_contract", "qualified_full_season_champion"), True),
        (("publication", "new_public_forecast_values"), 1),
        (("evidence", "private_evidence_publication"), "s3://private-owner/example")
    ]
    for path, value in cases:
        broken = copy.deepcopy(data)
        node = broken
        for key in path[:-1]:
            node = node[key]
        node[path[-1]] = value
        try:
            validate(broken)
        except ValueError:
            continue
        raise AssertionError(f"Invalid evidence accepted: {path}")
    return len(cases)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    data = json.loads(SOURCE.read_text())
    output = render(data)
    if args.check:
        if OUTPUT.read_text() != output:
            raise SystemExit("B099 status HTML is stale")
    else:
        OUTPUT.write_text(output)
    checks = negative_checks(data) if args.self_test else 0
    print(json.dumps({"status": "PASS", "deterministic_html": True,
                      "rejected_invalid_evidence": checks,
                      "owner_executions": 0, "new_owner_fits": 0}))


if __name__ == "__main__":
    main()
