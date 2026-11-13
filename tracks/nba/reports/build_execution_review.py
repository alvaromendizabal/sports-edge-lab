"""Attach an aggregate execution review without changing saved NBA research."""
from __future__ import annotations

import hashlib
import html
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parent
SCHEMA = "sports-edge-lab.nba.execution-review.v1"
BEGIN = "<!-- NBA EXECUTION REVIEW BEGIN -->"
END = "<!-- NBA EXECUTION REVIEW END -->"
POINT = '<p id="intro"></p><p id="clocks" class="small"></p>\n'
SOURCE_PINS = {
    "latest_research_outputs.json": "9e6795387c1e64bc6265da04bdd9d4e9fd0fb9860007da7b465549752542149b",
    "latest_v9_acceptance.json": "7e39b2285177cd5fc2ab78b9463f21a34bad254e872afb14318b63cfdf1fda5e",
    "b078_recovered_b077_evidence.json": "74dd8d0632e9efeb1885b410b7c2f5a82129ba5b41f3e2e70114a4aa0e824c1b",
    "b077_historical_peaks_and_gates.json": "65edad6d038b898b384aa6907070c48180798c7b95404fe00c2952f53d368e85",
}
B081_PACKAGE_PIN = {"bytes": 122204800, "sha256": "802ff5bfaf1afec93e70478a105543110a5c9317c8bfc909810350021ba65142"}
BASE_DISPLAY_SHA256 = "759ce36191200e327d6766c0e2c4e26177efb0221caf57a3c5a67c625c6385ce"


def digest(body):
    return hashlib.sha256(body).hexdigest()


def validate(value):
    if value.get("schema") != SCHEMA:
        raise ValueError("EXECUTION_REVIEW_SCHEMA")
    run = value["latest_owner_execution"]
    if run["release"] != "B080" or run["status"] != "PARTIAL_RESUMABLE_OWNER_PIPELINE":
        raise ValueError("EXECUTION_REVIEW_OWNER_IDENTITY")
    if run["new_confirmed_scientific_fits"] != 0 or run["exit_code"] != 2:
        raise ValueError("EXECUTION_REVIEW_UNSUPPORTED_PROGRESS")
    if run["return"]["bytes"] != 516246459 or run["return"]["members"] != 10:
        raise ValueError("EXECUTION_REVIEW_RETURN_IDENTITY")
    if run["return"]["sha256"] != "0e7423bcd77c4b34617cf9b3541275fa9138208a02b0b37eb7e38661fd9cf239":
        raise ValueError("EXECUTION_REVIEW_RETURN_PIN")
    if run.get("scientific_stages_reached") is not False or run.get("new_forecasts") != 0:
        raise ValueError("EXECUTION_REVIEW_UNSUPPORTED_PROGRESS")
    if run.get("fatal_error") != "RuntimeError:B078_BASELINE_CAPACITY_PREVENTS_SUBSTANTIVE_WORK":
        raise ValueError("EXECUTION_REVIEW_FAILURE_CLASS")
    runtime = value["observed_runtime"]
    if runtime["peak_concurrent_scientific_fits"] != 0 or runtime["twelve_core_scientific_utilization_proven"]:
        raise ValueError("EXECUTION_REVIEW_RESERVATION_IS_NOT_UTILIZATION")
    if runtime.get('peak_work_class') != 'TRANSPORT_FINALIZATION_NOT_SCIENTIFIC_FITS':
        raise ValueError('EXECUTION_REVIEW_TRANSPORT_IS_NOT_TRAINING')
    if value["science_preservation"]["latest_original_issue_at_utc"] != "2026-11-12T02:02:29.830904+00:00":
        raise ValueError("EXECUTION_REVIEW_ORIGINAL_ISSUE_CLOCK")
    if value["science_preservation"]["publication_new_fits"] != 0 or value["science_preservation"]["publication_new_forecasts"] != 0:
        raise ValueError("EXECUTION_REVIEW_PUBLICATION_IS_NOT_SCIENCE")
    replacement = value["replacement_engineering"]
    if replacement.get("release") != "B081" or replacement["owner_execution_completed"] or replacement["verified_new_owner_scientific_fits"] != 0:
        raise ValueError("EXECUTION_REVIEW_NO_B081_OWNER_RUN")
    if replacement["all_deployed_sports_retrofitted"]:
        raise ValueError("EXECUTION_REVIEW_UNVERIFIED_CROSS_SPORT_DEPLOYMENT")
    body = json.dumps(value, sort_keys=True)
    for forbidden in ("recipe_id", "feature_names", "s3://", "/home/", "/workspace/", "api_key", "apiKey", "PRIVATE KEY"):
        if forbidden in body:
            raise ValueError("EXECUTION_REVIEW_PRIVATE_FIELD_OR_PATH")
    if value["science_preservation"]["source_sha256"] != SOURCE_PINS:
        raise ValueError("EXECUTION_REVIEW_RESEARCH_PINS_CHANGED")
    logging = value['live_logging']
    if logging['heartbeat_samples'] != 104 or logging['health_errors'] or logging['heartbeat_interval_gate'] != 'PASS':
        raise ValueError('EXECUTION_REVIEW_LOG_EVIDENCE_CHANGED')
    if not 10.6 <= logging['maximum_gap_seconds'] < 10.7:
        raise ValueError('EXECUTION_REVIEW_LOG_INTERVAL_CHANGED')
    sink = logging['s3_checkpoints']
    if (sink['scope'] != 'LOG_CHECKPOINT_SINK_ONLY' or sink['put_calls'] != 16
            or sink['get_calls'] != 0 or sink['list_calls'] != 0 or sink['attempted_body_bytes'] != 440937):
        raise ValueError('EXECUTION_REVIEW_TRANSFER_SCOPE_CHANGED')
    cache = value['cache_evidence']
    if (cache['parquet_operation'] != 'VERIFIED_LOCAL_PARQUET_CONTEXT_REUSED'
            or cache['whole_pipeline_s3_transfers_fully_instrumented'] is not False
            or cache['finalizer_hash_operations'] is not None or cache['finalizer_bytes_hashed'] is not None):
        raise ValueError('EXECUTION_REVIEW_CACHE_SCOPE_CHANGED')
    if value['cost_evidence']['actual_billed_cost_usd'] is not None:
        raise ValueError('EXECUTION_REVIEW_COST_IS_NOT_INVOICE')
    failure = value['capacity_failure']
    if (failure['preflight_selected_files'] != 76297 or failure['files_physically_prepared'] != 33977
            or failure['new_objects_compressed'] != 61460 or failure['frame_tasks_submitted'] != 0
            or failure['conservative_bound_bytes'] != 513684626
            or failure['scientific_allowance_bytes'] != 406711828
            or failure['actual_final_scientific_support_bytes'] != 391824722):
        raise ValueError('EXECUTION_REVIEW_ACTUAL_CAPACITY_FAILURE_CHANGED')
    measured = replacement['budget_verification']
    if (measured['selected_files'] != 76324 or measured['selected_pin_matches'] != 76324
            or measured['complete_support_bound_bytes'] != 36821661
            or measured['physical_files'] != 0 or measured['inherited_files'] != 76324
            or measured['declared_omissions_unchanged'] != 2658
            or measured['controlled_end_to_end_speedup_established'] is not False
            or measured['owner_current_source_and_full_ancestry_guards_still_required'] is not True
            or measured['new_scientific_fits'] != 0):
        raise ValueError('EXECUTION_REVIEW_METADATA_TEST_SCOPE_CHANGED')
    package = replacement['package_verification']
    if package['status'] == 'PASS':
        if ({'bytes': package['exact_package_bytes'], 'sha256': package['exact_package_sha256']} != B081_PACKAGE_PIN
                or package['passed'] != package['packaged_tests']
                or package['packaged_tests'] != 489 or package['package_members'] != 1181
                or package['original_B080_members_preserved'] != 1147
                or sum(package[name] for name in ('failures', 'errors', 'skipped', 'module_errors')) != 0
                or package['owner_execution_performed'] is not False):
            raise ValueError('EXECUTION_REVIEW_EXACT_PACKAGE_VERIFICATION_CHANGED')
    return True


def strip_review(body):
    if body.count(BEGIN) != body.count(END) or body.count(BEGIN) > 1:
        raise ValueError("EXECUTION_REVIEW_DUPLICATE_OR_UNCLOSED")
    return re.sub(re.escape(BEGIN) + r".*?" + re.escape(END) + r"\n?", "", body, flags=re.S)


def render(value):
    validate(value)
    esc = lambda x: html.escape(str(x), quote=True)
    run = value["latest_owner_execution"]
    obs = value["observed_runtime"]
    cache = value["cache_evidence"]
    fixed = value["replacement_engineering"]
    package = fixed["package_verification"]
    logging = value['live_logging']; sink = logging['s3_checkpoints']; cost = value['cost_evidence']
    failure = value['capacity_failure']; measured = fixed['budget_verification']
    rows = [
        ("Actual owner outcome", f"{run['status']}; exit {run['exit_code']}; {run['elapsed_seconds']:.3f} seconds; zero confirmed new scientific fits"),
        ("Observed process CPU", f"{obs['time_weighted_cpu_cores']:.5f} average cores over {obs['sample_elapsed_seconds']:.3f} measured seconds; {obs['peak_cpu_cores']:.5f} peak; {obs['samples']} samples"),
        ("Reservation versus work", f"{obs['one_reserved_core_samples']} observed heartbeats reserved one core; {obs['twelve_reserved_core_samples']} reserved twelve. The {obs['peak_cpu_cores']:.5f}-core peak was transport finalization, with zero concurrent scientific fits. Twelve-core training utilization is not established."),
        ("Preflight object preparation", f"{failure['preflight_selected_files']:,} selected files; {failure['files_physically_prepared']:,} files physically prepared and {failure['new_objects_compressed']:,} objects compressed in {failure['preflight_seconds']:.3f} seconds. Zero frame tasks did not mean zero object compression."),
        ("Capacity rejection", f"{failure['conservative_bound_bytes']:,}-byte conservative bound exceeded the {failure['scientific_allowance_bytes']:,}-byte allowance. Final framing later produced a valid {failure['actual_final_scientific_support_bytes']:,}-byte support. These are different representations."),
        ("Persistent Parquet reuse", f"{cache['parquet_contexts']} contexts; {cache['parquet_rows']:,} rows; {cache['parquet_bytes_read']:,} bytes read in {cache['parquet_reuse_seconds']:.3f} seconds. Context-cache historical object GET count was zero; whole-pipeline transfers were not fully instrumented."),
        ("Pipeline pin cache", f"{cache['pipeline_hash_operations']:,} full-body hash operations; {cache['pipeline_unchanged_pin_reuses']:,} unchanged-pin reuses; {cache['pipeline_bytes_hashed']:,} bytes hashed"),
        ("Finalizer pin cache", f"{cache['finalizer_unchanged_pin_reuses']:,} unchanged-pin reuses. Full-body hash operation and byte counts were not reported; null does not mean zero."),
        ("Reused transport proofs", f"{cache['finalizer_archive_proof_hits']} archive proof hits. Baseline-proof hit and avoided-rebuild counters were not reported. Proof reuse did not prevent expensive budget preparation."),
        ("Continuous actual-owner logging", f"{logging['heartbeat_samples']} heartbeats; maximum gap {logging['maximum_gap_seconds']:.6f} seconds; zero logger health errors. Human log {logging['log_bytes']:,} bytes; JSONL {logging['jsonl_bytes']:,} bytes. Logging success is not scientific progress."),
        ("Log checkpoint transfers only", f"{sink['put_calls']} SDK PUT calls; {sink['attempted_body_bytes']:,} compressed body bytes; zero GET or LIST calls; {sink['elapsed_seconds']:.3f} measured transfer seconds. Internal retry network bytes were not observed."),
        ("Measured whole-instance cost estimate", f"${float(cost['estimated_whole_instance_invocation_usd']):.6f} across {cost['measured_total_elapsed_seconds']:.3f} seconds at the verified stored rate. Actual billed cost and project-only allocation are unknown; overlapping stage estimates are not added."),
        ("Authenticated return", f"{run['return']['bytes']:,} bytes; {run['return']['members']} members; every payload SHA-256 authenticated"),
    ]
    cells = "\n".join("<tr><th scope=\"row\">" + esc(a) + "</th><td>" + esc(b) + "</td></tr>" for a, b in rows)
    repairs = "\n".join("<li>" + esc(x) + "</li>" for x in fixed["implemented_repairs"])
    tests = "\n".join("<li>" + esc(x) + "</li>" for x in fixed["verification_summary"])
    if package['status'] == 'PASS':
        package_text = (f"PASS: {package['passed']}/{package['packaged_tests']} tests passed on the exact "
            f"{package['exact_package_bytes']:,}-byte executable in {package['elapsed_seconds']:.3f} seconds. "
            f"SHA-256 {package['exact_package_sha256']}. All {package['original_B080_members_preserved']:,} "
            "original B080 members remain preserved. These local fixture results do not establish an owner-host scientific result.")
    else:
        package_text = 'Final exact-package verification is pending; no completed package-test result is claimed.'
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).replace("<", "\\u003c")
    return BEGIN + f'''
<section id="nba-execution-review" aria-labelledby="nba-execution-title">
<style>#nba-execution-review{{margin:22px 0;padding:20px;border:1px solid #bdced5;border-radius:8px;background:#f4f8fb}}#nba-execution-review h2{{margin-top:0}}#nba-execution-review p,#nba-execution-review td,#nba-execution-review li{{overflow-wrap:anywhere}}#nba-execution-review th{{white-space:normal;min-width:120px}}#nba-execution-review .scroll{{max-height:480px}}@media(max-width:600px){{#nba-execution-review{{padding:14px}}}}</style>
<h2 id="nba-execution-title">B080 stopped before science; B081 recovery prepared</h2>
<p id="nba-execution-outcome"><strong>Latest owner invocation: {esc(run['status'])}, zero confirmed new scientific fits.</strong> It ran from {esc(run['started_at_utc'])} to {esc(run['finished_at_utc'])}. The saved B077 forecasts, champions and model scores below remain unchanged.</p>
<p id="nba-execution-source-clock">Latest authentic original forecast issue: <strong>{esc(value['science_preservation']['latest_original_issue_at_utc'])}</strong>. A later diagnostic, source commit or browser check does not refresh that issue clock.</p>
<div class="scroll"><table id="nba-execution-evidence"><thead><tr><th>Evidence</th><th>Actual saved measurement and qualification</th></tr></thead><tbody>{cells}</tbody></table></div>
<p id="nba-execution-fatal"><strong>Authenticated failure:</strong> <code>{esc(run['fatal_error'])}</code>. Latest-baseline adoption was gated to B078/B079 and excluded B080. Older transport roots left later saved files to be prepared again, and the conservative capacity bound stopped the pipeline before science. B081 explicitly adopts the complete B080 support and measures admission without physical object preparation. The original resource guards remain active.</p>
<p id="nba-execution-budget-test"><strong>Verified engineering result:</strong> all {measured['selected_files']:,} saved selected pins match the accepted support; its new complete reference-container bound is {measured['complete_support_bound_bytes']:,} bytes. Three metadata-bound calculations took {measured['metadata_bound_calculations_seconds']:.3f} seconds locally with zero physical file preparations or compression. The exact replacement source leaves {measured['candidate_headroom_before_admission_reserves_bytes']:,} bytes before the original {measured['original_admission_reserves_bytes']:,}-byte admission protections on this saved inventory; owner source and full ancestry guards still apply. This saved-metadata test and the actual {failure['preflight_seconds']:.3f}-second owner preparation have different scopes and hosts; no controlled whole-run speedup is claimed. {measured['declared_omissions_unchanged']:,} declared omissions and all required older dependencies remain explicit.</p>
<details id="nba-execution-repairs"><summary>Implemented recovery and permanent logging changes</summary><ul>{repairs}</ul><ul>{tests}</ul></details>
<p id="nba-execution-replacement-status"><strong>{esc(fixed['status'])}.</strong> Actual B080 logging met its heartbeat interval gate but training never started. B081 also refreshes stale resource-pressure intervals without relaxing CPU, RAM, disk or shared-owner thresholds. The replacement NBA runner retains the shared logging framework. Previously deployed non-NBA executables have not been verified as retrofitted. No B081 owner execution or new owner fit result is claimed here.</p>
<p id="nba-execution-package-status"><strong>Replacement package verification:</strong> {esc(package_text)}</p>
<p>All {value['science_preservation']['authenticated_completed_frozen_tasks']:,} completed historical frozen tasks remain authenticated. New current-season evaluation, substantial parallel training, fresh market comparisons and new issues require the next owner execution. No model has been promoted by this engineering repair or publication.</p>
<p><a href="latest_execution_review.json">Download sanitized execution evidence</a> · <a href="history/b080_prepared_execution_review.json">Preserved B079 failure and B080 preparation review</a> · <a href="history/b079_prepared_execution_review.json">Earlier B078 failure review</a> · <a href="../../../runtime/execution/README.md">Inspect the shared live logging framework and test contract</a></p>
<script id="nba-execution-data" type="application/json">{encoded}</script>
</section>
''' + END + "\n"


def attach(body, value):
    clean = strip_review(body)
    if digest(clean.encode()) != BASE_DISPLAY_SHA256:
        raise ValueError("EXECUTION_REVIEW_BASE_DISPLAY_CHANGED_REVIEW_FIRST")
    if clean.count(POINT) != 1:
        raise ValueError("EXECUTION_REVIEW_INSERTION_POINT")
    return clean.replace(POINT, POINT + render(value), 1)


def build(check=False):
    for name, pin in SOURCE_PINS.items():
        if digest((ROOT / name).read_bytes()) != pin:
            raise ValueError("EXECUTION_REVIEW_RESEARCH_CHANGED:" + name)
    value = json.loads((ROOT / "latest_execution_review.json").read_bytes())
    if check and value['replacement_engineering']['package_verification']['status'] != 'PASS':
        raise ValueError('EXECUTION_REVIEW_FINAL_PACKAGE_RECEIPT_REQUIRED')
    path = ROOT / "latest_research_outputs.html"
    body = attach(path.read_text(), value).encode()
    if check:
        if path.read_bytes() != body:
            raise ValueError("EXECUTION_REVIEW_DISPLAY_STALE")
    else:
        path.write_bytes(body)
    return {"status": "PASS" if check else "BUILT", "unchanged_research_sources": SOURCE_PINS,
            "source_issue_clock_unchanged": True, "publication_new_fits": 0,
            "display_bytes": len(body), "display_sha256": digest(body)}


if __name__ == "__main__":
    print(json.dumps(build("--check" in sys.argv), sort_keys=True))
