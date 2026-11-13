"""Render saved B082 owner evidence and separate, verified B083 engineering."""
from pathlib import Path
import hashlib
import html
import json
import re
import sys
from b083_html import expand_html
from build_snapshot_downloads import pack_public_html
ROOT=Path(__file__).resolve().parent
SCHEMA='sports-edge-lab.nba.execution-review.v3'
BEGIN='<!-- NBA EXECUTION REVIEW BEGIN -->'
END='<!-- NBA EXECUTION REVIEW END -->'
POINT='<p id="intro"></p><p id="clocks" class="small"></p>\n'
SOURCE_PINS={'b077_historical_peaks_and_gates.json': '65edad6d038b898b384aa6907070c48180798c7b95404fe00c2952f53d368e85', 'b078_recovered_b077_evidence.json': '74dd8d0632e9efeb1885b410b7c2f5a82129ba5b41f3e2e70114a4aa0e824c1b', 'current_saved_cohort_leaders.json': '2ed1ae7c3abb0dd13daaaa0e7b2c882e800db5b4c939122ea079b390f06a0acd', 'history/b081_selected_outputs.json': '4fbcbaed8b46182a044ba11ad69a2c283d724e42a7a61819091c88ee02ed8087', 'latest_model_review.json': '32768513f97399c65b9bcab52b39686970acb26737c5c73aaa8a495564bce59f', 'latest_research_outputs.json': '3d28fc2e6116b7a75eb0037ccb2a2ea199afd9c29e7a72794ac9ece1722b8fdf', 'latest_v9_acceptance.json': '9c47f58c4b625b97c4b4f6b64d68e2deabce08c202dd57f74ff88d9c4e7a6fbd', 'selected_issue_preservation.json': '9150b15c884b361afedd9301ef967848c8d687695cb7698b4aa6babc7fed3cf1'}
B083_PACKAGE_PIN={'bytes': 178697447, 'sha256': '6ce6373083491767bb41fbe76515db4c847e1bff39aaf015b59780ffc674292b'}
BASE_DISPLAY_SHA256='66d8783c3c37446d45207d3c1d220efb4032b527bff501a6e7771f31f416d192'
RETURN_PIN={'bytes':458509782,'sha256':'01b357ea905c96462071a174e2a6b396aa9120bb38b8117a201c832b40a0cffd','members':10,'payload_members_authenticated':9}
LATEST_ISSUE='2026-11-13T17:26:12.502657+00:00'
def digest(body):return hashlib.sha256(body).hexdigest()
def require(condition,reason):
    if not condition:raise ValueError('EXECUTION_REVIEW_'+reason)
def validate(value):
    require(value.get('schema')==SCHEMA,'SCHEMA')
    run=value['latest_owner_execution'];obs=value['observed_runtime'];science=value['science_preservation']
    fixed=value['replacement_engineering'];log=value['live_logging'];cache=value['cache_evidence'];native=obs['native_fit_exact_intervals']
    require((run['release'],run['status'],run['exit_code'])==('B082','PARTIAL_SUBSTANTIVE_WITH_EXPLICIT_BLOCKERS',2),'OWNER_IDENTITY')
    require((run['new_confirmed_scientific_fits'],run['new_forecasts'],run['provider_requests'],run['new_forecast_distinct_games'])==(318,13860,36,985),'UNSUPPORTED_PROGRESS')
    require(run['native_fit_breakdown']=={'V9_studies':256,'current_season_frozen':34,'champion_issuance':28},'FIT_SCOPE_CHANGED')
    require(run['return']==RETURN_PIN,'RETURN_IDENTITY')
    require(obs['peak_concurrent_scientific_fits']==6 and not obs['twelve_core_scientific_utilization_proven'] and obs['peak_work_class']=='TRANSPORT_FINALIZATION_NOT_SCIENTIFIC_FITS' and native['real_estimator_fit_returns']==318 and native['synthetic_estimator_fit_returns']==0,'RESERVATION_IS_NOT_UTILIZATION')
    require(science['source_sha256']==SOURCE_PINS,'RESEARCH_PINS_CHANGED')
    require(science['latest_original_issue_at_utc']==LATEST_ISSUE,'ORIGINAL_ISSUE_CLOCK')
    require(all(science[key]==0 for key in ['publication_new_fits','publication_new_forecasts','publication_new_scoring','automatic_promotions']),'PUBLICATION_IS_NOT_SCIENCE')
    require(fixed['release']=='B083' and not fixed['owner_execution_completed'] and fixed['verified_new_owner_scientific_fits']==0 and not fixed['all_deployed_sports_retrofitted'],'NO_UNOBSERVED_OWNER_OR_CROSS_SPORT_DEPLOYMENT')
    require(log['heartbeat_samples']==570 and not log['health_errors'] and log['heartbeat_interval_gate']=='PASS' and 10.737<log['maximum_gap_seconds']<10.738,'LOG_EVIDENCE_CHANGED')
    sink=log['s3_checkpoints'];require((sink['scope'],sink['put_calls'],sink['get_calls'],sink['list_calls'],sink['attempted_body_bytes'])==('LOG_CHECKPOINT_SINK_ONLY',128,0,0,14559581),'TRANSFER_SCOPE_CHANGED')
    require(cache['persistent_contexts']['historical_full_object_S3_GETs']==0 and not cache['all_pipeline_S3_calls_instrumented'],'CACHE_SCOPE_CHANGED')
    require(not cache['file_pin_operations']['unique_file_count_claim'] and not cache['file_pin_operations']['physical_IO_bytes_avoided_claim'],'CACHE_OPERATIONS_ARE_NOT_FILES_OR_BYTES_AVOIDED')
    require(value['cost_evidence']['actual_billed_cost_usd'] is None,'ESTIMATE_IS_NOT_INVOICE')
    require(not science['full_future_schedule_complete'] and science['missing_regular_schedule_slots']==24,'MISSING_SCHEDULE_SCOPE_CHANGED')
    saved=fixed['saved_artifact_engineering'];require(saved['issue_inventory']['files']==5536 and saved['issue_inventory']['same_selected_file_pins'] and saved['report_seal']['all_original_report_bytes_preserved'] and not saved['report_seal']['full_owner_inventory_speedup_claim'],'SAVED_ENGINEERING_SCOPE_CHANGED')
    package=fixed['package_verification']
    if package['status']=='PASS':
        require({'bytes':package['exact_package_bytes'],'sha256':package['exact_package_sha256']}==B083_PACKAGE_PIN and package['passed']==package['packaged_tests']==715 and all(package[k]==0 for k in ['failures','errors','skipped','module_errors']) and not package['owner_execution_performed'] and package['real_NBA_fits']==0,'EXACT_PACKAGE_VERIFICATION_CHANGED')
    for row in fixed['live_logging_acceptance']['cases']:
        require(row['observed_max_gap_seconds']<=15 and row['standard_aliases_same_inode'] and not row['actual_AWS_owner_execution'] and not row['actual_NBA_fits'] and not row['synthetic_CPU_probe_performed'],'LIVE_ACCEPTANCE_SCOPE_CHANGED')
    require(value['native_document_authentication']['distinct_authenticated_fit_return_and_result_documents']==925 and value['native_document_authentication']['omitted_model_bodies_in_return_increment']==287 and not value['native_document_authentication']['omitted_model_bodies_authenticated_by_this_audit'],'FIT_DOCUMENTS_ARE_NOT_MODEL_BODIES')
    body=json.dumps(value)
    require(not any(token in body for token in ['recipe_id','feature_names','s3://','/home/','/workspace/','/dev/shm/','api_key','apiKey','PRIVATE KEY']),'PRIVATE_FIELD_OR_PATH')
    return True

def strip_review(body):
    body=expand_html(body)
    require(body.count(BEGIN)==body.count(END) and body.count(BEGIN)<=1,'DUPLICATE_OR_UNCLOSED')
    return re.sub(re.escape(BEGIN)+r'.*?'+re.escape(END)+r'\n?','',body,flags=re.S)

def render(value):
    validate(value);e=lambda v:html.escape(str(v),quote=True)
    run=value['latest_owner_execution'];obs=value['observed_runtime'];native=obs['native_fit_exact_intervals'];log=value['live_logging'];sink=log['s3_checkpoints'];cost=value['cost_evidence'];cache=value['cache_evidence'];fixed=value['replacement_engineering'];science=value['science_preservation'];coverage=science['coverage'];cap=value['capacity_failures'];projection=fixed['heartbeat_projection_replay'];saved=fixed['saved_artifact_engineering']
    context=cache['persistent_contexts'];pins=cache['file_pin_operations']
    facts=[
      ('Actual owner outcome',f"{run['elapsed_seconds']:.3f} seconds; 318 confirmed native estimator fits: 256 V9 studies + 34 current-season frozen + 28 champion issuance. {run['provider_requests']} provider requests."),
      ('New original forecasts',f"13,860 immutable early outlooks across 985 distinct games. Selected-output metadata's 28 estimator fits describes issuance only; 318 is the whole-invocation native-return count. Nominal T60/T120 labels do not turn early outlooks into final-hour issues."),
      ('Actual scientific overlap',f"Peak 6 concurrent native fits; {obs['seconds_with_multiple_native_fits']:.6f} seconds with multiple fits. {native['native_fit_elapsed_seconds_sum']:.6f} summed native-fit seconds and {native['native_fit_process_cpu_seconds']:.3f} process CPU-seconds. Brief fits fell between ten-second samples. Twelve-core scientific utilization is not established."),
      ('Observed process CPU',f"{obs['time_weighted_cpu_cores']:.5f} average observed core equivalents. Peak {obs['peak_cpu_cores']:.5f} was transport finalization. First positive native-return heartbeat: {obs['first_positive_native_return_sample_elapsed_seconds']:.3f} seconds. Reserved cores are not utilized training cores."),
      ('Progress and return bottleneck',f"Internal progress JSONL: {log['internal_progress_jsonl_bytes']:,} bytes. Fast compressed bound {cap['fast_compressed_support_bound_bytes']:,} exceeded {cap['scientific_support_capacity_bytes']:,} capacity bytes, triggering the slower legacy encoding. Final support: {cap['actual_final_support_bytes']:,} bytes. Nine complete budget reconciliations took {cap['full_budget_reconciliation_seconds']:.3f} seconds."),
      ('Persistent Parquet reuse',f"{context['contexts']} contexts; {context['rows']:,} rows; {context['local_bytes']:,} local bytes in {context['elapsed_seconds']:.3f} seconds. Zero historical full-object GETs in this context path; other transfers have separate scopes."),
      ('Pin and ancestor reuse',f"{pins['first_hash_operations']:,} full-body hash operations and {pins['unchanged_stat_identity_reuse_operations']:,} stat-identity reuses. These count operations, not unique files or physical bytes saved. The same six archive proofs were reused by worker and finalizer; prior baseline adoption copied/downloaded zero bytes in that scope."),
      ('Continuous actual-owner logging',f"570 heartbeats; maximum gap {log['maximum_gap_seconds']:.6f} seconds; zero logger health errors. Human log {log['log_bytes']:,} bytes and external JSONL {log['jsonl_bytes']:,} bytes. One startup stale-origin refusal and one child-handoff unavailable event retained the identity guard."),
      ('Log checkpoints only',f"{sink['put_calls']} SDK PUT calls / {sink['attempted_body_bytes']:,} supplied compressed body bytes. Zero GET/LIST calls in this sink. Internal retries and whole-pipeline network traffic are not fully measured."),
      ('Whole-instance cost estimate',f"${float(cost['estimated_whole_instance_invocation_usd']):.6f} over {cost['measured_total_elapsed_seconds']:.3f} seconds at ${float(cost['hourly_usd']):.2f}/hour. Actual billing and NBA-only allocation are unknown; overlapping estimates are not added."),
      ('Forecast and schedule coverage',f"All 1,274 observed canonical games and three secondary observations remain visible. {coverage['official_future_tips_at_report']:,} saved future tips differ from 985 games newly issued. {coverage['all_game_current_role_forecasts_available']:,} of {coverage['all_game_applicable_role_opportunities']:,} applicable role cells are available; {coverage['all_game_current_role_forecasts_missing']:,} remain missing. Twenty-four of 1,230 regular-season schedule identities were not observed."),
      ('Authenticated return',f"{run['return']['bytes']:,} bytes; 10 members; 9 payload pins authenticated. SHA-256 {run['return']['sha256']}.")]
    table=''.join('<tr><th scope="row">'+e(k)+'</th><td>'+e(v)+'</td></tr>' for k,v in facts)
    stages=''.join('<tr><td>'+e(r['stage'].replace('_',' ').title())+'</td><td>'+f"{r['seconds']:.3f}"+'</td><td>'+('Unavailable' if r['average_cores'] is None else f"{r['average_cores']:.4f}")+'</td></tr>' for r in obs['sample_attributed_stages'][:8])
    repairs=''.join('<li>'+e(x)+'</li>' for x in fixed['implemented_repairs']);failure='; '.join(r['stage']+': '+r['reason'] for r in value['scientific_failures']);pres=science['previous_snapshot_preservation'];inventory=saved['issue_inventory'];seal=saved['report_seal'];live=fixed['live_logging_acceptance'];package=fixed['package_verification']
    package_text=(f"PASS: {package['passed']}/{package['packaged_tests']} packaged tests; {package['exact_package_bytes']:,}-byte executable; SHA-256 {package['exact_package_sha256']}. Zero failed, errored or skipped tests. Owner execution remains pending." if package['status']=='PASS' else 'Final exact-package verification is pending; no completed test receipt is claimed.')
    encoded=json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).replace('<','\\u003c')
    return BEGIN+f'''
<section id="nba-execution-review" aria-labelledby="nba-execution-title">
<style>#nba-execution-review{{margin:22px 0;padding:20px;border:1px solid #bdced5;border-radius:8px;background:#f4f8fb}}#nba-execution-review p,#nba-execution-review td,#nba-execution-review li{{overflow-wrap:anywhere}}#nba-execution-review th{{white-space:normal;min-width:120px}}#nba-execution-review .scroll{{max-height:480px}}@media(max-width:600px){{#nba-execution-review{{padding:14px}}}}</style>
<h2 id="nba-execution-title">B082 actual: 318 native fits and 13,860 early outlooks; B083 repairs prepared</h2>
<p id="nba-execution-outcome"><strong>{e(run['status'])}, exit {run['exit_code']}.</strong> The owner ran from {e(run['started_at_utc'])} to {e(run['finished_at_utc'])}. It produced 318 native estimator fits and 13,860 new forecasts, while sustained parallel utilization, source-catalogue recovery and final publication remained incomplete.</p>
<p id="nba-execution-source-clock">Latest authentic original issue: <strong>{e(science['latest_original_issue_at_utc'])}</strong>. Saved evidence closes at {e(science['evidence_as_of_utc'])}; publication does not refresh this date. {pres['unchanged_shared_selected_issues']:,} shared selected issue objects remain exactly unchanged. All {pres['superseded_selected_issues_preserved_in_history']:,} replaced selections remain in dated history with original clocks.</p>
<div class="scroll"><table id="nba-execution-evidence"><thead><tr><th>Evidence</th><th>Actual saved measurement and scope</th></tr></thead><tbody>{table}</tbody></table></div>
<details><summary>Where sampled owner time went</summary><p>Approximate ten-second sample attribution remains separate from exact native-fit intervals.</p><div class="scroll"><table id="nba-execution-stages"><thead><tr><th>Stage</th><th>Seconds</th><th>Average observed cores</th></tr></thead><tbody>{stages}</tbody></table></div></details>
<p id="nba-execution-failures"><strong>Recorded blockers:</strong> {e(failure)}. Failed stages retain checkpoints and receive no fit credit. Automatic promotion remains disabled.</p>
<p id="nba-model-durability"><strong>Saved model durability:</strong> 925 fit-return and committed-result documents authenticate the 318 fit returns. They do not authenticate the 287 model bodies omitted from the returned increment. Existing owner-local or S3 model bodies require separate verification; the return is not claimed to contain every fitted state.</p>
<p id="nba-model-durability-repair"><strong>Prepared preservation fix:</strong> exact committed model bodies can be restored only from authenticated content keys. New commits receive priority for concurrent immutable backup; final sealing requires verified remote checksums or complete retained local bodies under the existing size gate. The adapter does not silently refit or deserialize models. Thirty-three focused durability tests and 46 cache/budget/ancestry regressions passed; these overlap the full packaged suite. Owner cloud recovery and transfers have not been executed in this preparation.</p>
<p id="nba-execution-budget-test"><strong>Verified saved-artifact engineering:</strong> identical {inventory['files']:,} authentic issue-file pins in {inventory['incremental_seconds']:.6f}s versus {inventory['original_seconds']:.6f}s ({inventory['speed_ratio']:.2f}×), for one 4,000-file baseline plus 24 batches of 64 files. The unchanged {seal['original_report_bytes']:,}-byte report sealed into a byte-identical {seal['byte_identical_archive_bytes']:,}-byte archive in {seal['streaming_seconds']:.6f}s versus {seal['original_seconds']:.6f}s with the original verifier. No scientific field was dropped. These isolated timings do not establish owner-run speedup or new training.</p>
<p id="nba-execution-projection-test">Saved telemetry projection: {projection['actual_saved_heartbeat_count']} heartbeats shrink from {projection['original_heartbeat_jsonl_bytes']:,} to {projection['reprojected_heartbeat_jsonl_bytes']:,} bytes ({projection['reduction_percent']:.2f}% less). Fit, CPU, cache, S3, cost, stage, progress and local-I/O counters remain identical. Additional callback coalescing savings are not included; complete scientific reports remain preserved.</p>
<details id="nba-execution-repairs"><summary>Implemented recovery and permanent logging changes</summary><ul>{repairs}</ul></details>
<p id="nba-execution-replacement-status"><strong>{e(fixed['status'])}.</strong> B083 has no completed owner-host sports run in this evidence. Generic logging retains the published NFL/FBS scope fields and command wrapper. This NBA update does not establish retrofitting of every previously deployed sport executable.</p>
<p id="nba-execution-live-test"><strong>Real local logging acceptance:</strong> {live['elapsed_seconds']:.3f} seconds with blocked/failing children. Actual <code>tail -F</code> readers saw growing per-run <code>LIVE_EXECUTION.log</code> and <code>LIVE_EXECUTION.jsonl</code>. Maximum gap {max(r['observed_max_gap_seconds'] for r in live['cases']):.6f} seconds at a ten-second setting; stalled-child diagnostics and failing-child stderr/exit remained visible. Zero sports computation, cloud requests or synthetic CPU probes.</p>
<p id="nba-execution-package-status"><strong>Replacement package verification:</strong> {e(package_text)}</p>
<p>Saved model review: {science['saved_current_review_metric_rows']} metric rows,{science['saved_matched_model_pairs']} matched selected/former comparisons and {science['saved_venue_comparisons']} qualified venue comparisons. Current-season leaders: {science['saved_current_cohort_leaders']} descriptive rows across {science['distinct_exact_current_cohorts']} separate exact cohorts and evidence policies. These subsets do not establish whole-season market superiority or a promoted model.</p>
<p><a href="latest_execution_review.json">Sanitized execution evidence</a> · <a href="history/b082_prepared_execution_review.json">Prior B081 actual/B082 preparation</a> · <a href="history/b081_selected_outputs.json">Preserved B081 selected outputs</a> · <a href="selected_issue_preservation.json">Preservation audit</a> · <a href="../../../runtime/execution/README.md">Shared live logging</a></p>
<script id="nba-execution-data" type="application/json">{encoded}</script></section>
'''+END+'\n'

def attach(body,value):
    clean=strip_review(body);require(digest(clean.encode())==BASE_DISPLAY_SHA256,'BASE_DISPLAY_CHANGED_REVIEW_FIRST');require(clean.count(POINT)==1,'INSERTION_POINT')
    return clean.replace(POINT,POINT+render(value),1)
def build(check=False):
    from restore_snapshot_assets import restore
    if (ROOT/'snapshot_asset_manifest.json').exists():restore(ROOT)
    for name,pin in SOURCE_PINS.items():require(digest((ROOT/name).read_bytes())==pin,'RESEARCH_CHANGED:'+name)
    value=json.loads((ROOT/'latest_execution_review.json').read_bytes())
    if '--require-package' in sys.argv:require(value['replacement_engineering']['package_verification']['status']=='PASS','FINAL_PACKAGE_RECEIPT_REQUIRED')
    path=ROOT/'latest_research_outputs.html';original=path.read_text();body=attach(original,value)
    if check:require(expand_html(original)==body,'DISPLAY_STALE')
    if not check:path.write_text(pack_public_html(body))
    return {'status':'PASS' if check else 'BUILT','source_inputs':SOURCE_PINS,'publication_new_fits':0,'display_bytes':path.stat().st_size,'display_sha256':digest(path.read_bytes())}
if __name__=='__main__':print(json.dumps(build('--check' in sys.argv),sort_keys=True))
