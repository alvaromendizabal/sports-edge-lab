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
BASE_DISPLAY_SHA256 = "759ce36191200e327d6766c0e2c4e26177efb0221caf57a3c5a67c625c6385ce"


def digest(body):
    return hashlib.sha256(body).hexdigest()


def validate(value):
    if value.get("schema") != SCHEMA:
        raise ValueError("EXECUTION_REVIEW_SCHEMA")
    run = value["latest_owner_execution"]
    if run["release"] != "B078" or run["status"] != "PARTIAL_RESUMABLE_OWNER_PIPELINE":
        raise ValueError("EXECUTION_REVIEW_OWNER_IDENTITY")
    if run["new_confirmed_scientific_fits"] != 0 or run["exit_code"] != 2:
        raise ValueError("EXECUTION_REVIEW_UNSUPPORTED_PROGRESS")
    if run["return"]["bytes"] != 104624594 or run["return"]["members"] != 15:
        raise ValueError("EXECUTION_REVIEW_RETURN_IDENTITY")
    if run["return"]["sha256"] != "fee168714d963992f71904c0ff46b161fcc2416a4432cf6e6bdf57963369448d":
        raise ValueError("EXECUTION_REVIEW_RETURN_PIN")
    runtime = value["observed_runtime"]
    if runtime["peak_concurrent_scientific_fits"] != 0 or runtime["twelve_core_scientific_utilization_proven"]:
        raise ValueError("EXECUTION_REVIEW_RESERVATION_IS_NOT_UTILIZATION")
    if value["science_preservation"]["latest_original_issue_at_utc"] != "2026-11-12T02:02:29.830904+00:00":
        raise ValueError("EXECUTION_REVIEW_ORIGINAL_ISSUE_CLOCK")
    if value["science_preservation"]["publication_new_fits"] != 0 or value["science_preservation"]["publication_new_forecasts"] != 0:
        raise ValueError("EXECUTION_REVIEW_PUBLICATION_IS_NOT_SCIENCE")
    replacement = value["replacement_engineering"]
    if replacement["owner_execution_completed"] or replacement["verified_new_owner_scientific_fits"] != 0:
        raise ValueError("EXECUTION_REVIEW_NO_B079_OWNER_RUN")
    if replacement["all_deployed_sports_retrofitted"]:
        raise ValueError("EXECUTION_REVIEW_UNVERIFIED_CROSS_SPORT_DEPLOYMENT")
    body = json.dumps(value, sort_keys=True)
    for forbidden in ("recipe_id", "feature_names", "s3://", "/home/", "/workspace/", "api_key", "apiKey", "PRIVATE KEY"):
        if forbidden in body:
            raise ValueError("EXECUTION_REVIEW_PRIVATE_FIELD_OR_PATH")
    if value["science_preservation"]["source_sha256"] != SOURCE_PINS:
        raise ValueError("EXECUTION_REVIEW_RESEARCH_PINS_CHANGED")
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
    rows = [
        ("Actual owner outcome", f"{run['status']}; exit {run['exit_code']}; {run['elapsed_seconds']:.3f} seconds; zero confirmed new scientific fits"),
        ("Observed process CPU", f"{obs['time_weighted_cpu_cores']:.5f} average cores over {obs['sample_elapsed_seconds']:.3f} measured seconds; {obs['peak_cpu_cores']:.5f} peak; {obs['samples']} samples"),
        ("Reservation versus work", "Most preflight reserved one core. Transport briefly reserved 12, then 11; concurrent native scientific fits stayed zero. Twelve-core training utilization is not established."),
        ("Persistent Parquet materialization", f"{cache['parquet_contexts']} contexts; {cache['parquet_rows']:,} rows; {cache['parquet_build_seconds']:.3f} seconds. Context-cache historical object GET count was zero; whole-pipeline transfers were not fully instrumented."),
        ("Pipeline pin cache", f"{cache['pipeline_hash_operations']:,} full-body hash operations; {cache['pipeline_unchanged_pin_reuses']:,} unchanged-pin reuses; {cache['pipeline_bytes_hashed']:,} bytes hashed"),
        ("Finalizer pin cache", f"{cache['finalizer_hash_operations']} full-body hash operations; {cache['finalizer_unchanged_pin_reuses']:,} unchanged-pin reuses; {cache['finalizer_bytes_hashed']:,} bytes hashed"),
        ("Reused transport proofs", f"{cache['finalizer_archive_proof_hits']} archive proof hits; {cache['finalizer_baseline_proof_hits']} baseline proof hit; one baseline rebuild avoided. These stages are not a controlled whole-run speedup benchmark."),
        ("Authenticated return", f"{run['return']['bytes']:,} bytes; {run['return']['members']} members; every payload SHA-256 authenticated"),
    ]
    cells = "\n".join("<tr><th scope=\"row\">" + esc(a) + "</th><td>" + esc(b) + "</td></tr>" for a, b in rows)
    repairs = "\n".join("<li>" + esc(x) + "</li>" for x in fixed["implemented_repairs"])
    tests = "\n".join("<li>" + esc(x) + "</li>" for x in fixed["verification_summary"])
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).replace("<", "\\u003c")
    return BEGIN + f'''
<section id="nba-execution-review" aria-labelledby="nba-execution-title">
<style>#nba-execution-review{{margin:22px 0;padding:20px;border:1px solid #bdced5;border-radius:8px;background:#f4f8fb}}#nba-execution-review h2{{margin-top:0}}#nba-execution-review p,#nba-execution-review td,#nba-execution-review li{{overflow-wrap:anywhere}}#nba-execution-review th{{white-space:normal;min-width:120px}}#nba-execution-review .scroll{{max-height:480px}}@media(max-width:600px){{#nba-execution-review{{padding:14px}}}}</style>
<h2 id="nba-execution-title">B078 failure recovered; B079 engineering verification</h2>
<p id="nba-execution-outcome"><strong>Latest owner invocation: {esc(run['status'])}, zero confirmed new scientific fits.</strong> It ran from {esc(run['started_at_utc'])} to {esc(run['finished_at_utc'])}. The saved B077 forecasts, champions and model scores below remain unchanged.</p>
<p id="nba-execution-source-clock">Latest authentic original forecast issue: <strong>{esc(value['science_preservation']['latest_original_issue_at_utc'])}</strong>. A later diagnostic, source commit or browser check does not refresh that issue clock.</p>
<div class="scroll"><table id="nba-execution-evidence"><thead><tr><th>Evidence</th><th>Actual saved measurement and qualification</th></tr></thead><tbody>{cells}</tbody></table></div>
<p id="nba-execution-fatal"><strong>Reproduced fatal cause:</strong> the baseline seal rebound a transport measurement context to a different cache directory; the integrity guard then stopped the pipeline. Fixing that exposed a second frame-context directory binding error. Both guards remain active. A separate progress callback overwrote the heartbeat envelope schema and caused the ownership rejection messages.</p>
<details id="nba-execution-repairs"><summary>Implemented recovery and permanent logging changes</summary><ul>{repairs}</ul><ul>{tests}</ul></details>
<p id="nba-execution-replacement-status"><strong>{esc(fixed['status'])}.</strong> The replacement NBA runner uses the shared logging framework. The generic framework supports NFL, FBS, NBA, NCAA basketball and other named project runners; previously deployed non-NBA executables have not been verified as retrofitted. No B079 owner execution or new owner fit result is claimed here.</p>
<p id="nba-execution-package-status"><strong>Replacement package verification:</strong> {esc(fixed['package_verification']['status'])}. Source repairs and the generic runtime are tested; package validation and an owner execution are separate gates.</p>
<p>All {value['science_preservation']['authenticated_completed_frozen_tasks']:,} completed historical frozen tasks remain authenticated. New current-season evaluation, substantial parallel training, fresh market comparisons and new issues require the next owner execution. No model has been promoted by this engineering repair or publication.</p>
<p><a href="latest_execution_review.json">Download sanitized execution evidence</a> · <a href="../../../runtime/execution/README.md">Inspect the shared live logging framework and test contract</a></p>
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
