"""Render authenticated owner aggregates and separate replacement engineering."""
from __future__ import annotations
import hashlib
import html
import json
from pathlib import Path
import re
import sys

ROOT=Path(__file__).resolve().parent
SCHEMA='sports-edge-lab.nba.execution-review.v2'
BEGIN='<!-- NBA EXECUTION REVIEW BEGIN -->'
END='<!-- NBA EXECUTION REVIEW END -->'
POINT='<p id="intro"></p><p id="clocks" class="small"></p>\n'
SOURCE_PINS={'b077_historical_peaks_and_gates.json': '65edad6d038b898b384aa6907070c48180798c7b95404fe00c2952f53d368e85', 'b078_recovered_b077_evidence.json': '74dd8d0632e9efeb1885b410b7c2f5a82129ba5b41f3e2e70114a4aa0e824c1b', 'current_saved_cohort_leaders.json': '7349f9882372af44cebd84a4c828afac82efd242a12e3e70ecbcc0da6082283c', 'history/b077_recovered_selected_outputs.json': '9e6795387c1e64bc6265da04bdd9d4e9fd0fb9860007da7b465549752542149b', 'latest_model_review.json': 'd71286315816a948ac2022ad80673c7b643ae1bbdb043a857ee92c5f1e0e3dd4', 'latest_research_outputs.json': '4fbcbaed8b46182a044ba11ad69a2c283d724e42a7a61819091c88ee02ed8087', 'latest_v9_acceptance.json': '9731fe2af9d8a1e45f32fe4855f4d1ea24949e3b598f30cf2a4bcaa2beaa1f71', 'selected_issue_preservation.json': 'ce0ae0a6f52d3ac52afce43c01aea497edf9f20b90537ed689707c82821844f8'}
B082_PACKAGE_PIN={'bytes': 141653687, 'sha256': 'cc48797f6cec62bc26a49d68bdfe4b00e8b9b16cf419343c9ab7bd121ebfbfc7'}
BASE_DISPLAY_SHA256='3b5fe0ef5c8197ea46066cc2c37acbe60ccb9c999fbc988b1ee02385ec192d9b'

def digest(body):return hashlib.sha256(body).hexdigest()

def validate(value):
    if value.get('schema')!=SCHEMA:raise ValueError('EXECUTION_REVIEW_SCHEMA')
    run=value['latest_owner_execution'];obs=value['observed_runtime'];science=value['science_preservation']
    fixed=value['replacement_engineering'];logging=value['live_logging'];cache=value['cache_evidence']
    if (run['release'],run['status'],run['exit_code'])!=('B081','PARTIAL_SUBSTANTIVE_WITH_EXPLICIT_BLOCKERS',2):
        raise ValueError('EXECUTION_REVIEW_OWNER_IDENTITY')
    if (run['new_confirmed_scientific_fits'],run['new_forecasts'],run['provider_requests'])!=(1,5,52):
        raise ValueError('EXECUTION_REVIEW_UNSUPPORTED_PROGRESS')
    if run['return']!={'bytes':277495287,'sha256':'da85c4d3d81ffbb69114f81c4e4e598a118925b53cd138f27b383fee10a84ea0','members':10,'payload_members_authenticated':9}:
        raise ValueError('EXECUTION_REVIEW_RETURN_IDENTITY')
    if (obs['peak_concurrent_scientific_fits']!=1 or obs['twelve_core_scientific_utilization_proven']
            or obs['peak_work_class']!='TRANSPORT_FINALIZATION_NOT_SCIENTIFIC_FITS'
            or obs['native_fit_exact_intervals']['real_estimator_fit_returns']!=1
            or obs['native_fit_exact_intervals']['synthetic_estimator_fit_returns']!=0):
        raise ValueError('EXECUTION_REVIEW_RESERVATION_IS_NOT_UTILIZATION')
    if science['source_sha256']!=SOURCE_PINS:raise ValueError('EXECUTION_REVIEW_RESEARCH_PINS_CHANGED')
    if science['latest_original_issue_at_utc']!='2026-11-13T03:01:14.158960+00:00':raise ValueError('EXECUTION_REVIEW_ORIGINAL_ISSUE_CLOCK')
    if any(science[key]!=0 for key in ['publication_new_fits','publication_new_forecasts','publication_new_scoring','automatic_promotions']):
        raise ValueError('EXECUTION_REVIEW_PUBLICATION_IS_NOT_SCIENCE')
    if (fixed['release']!='B082' or fixed['owner_execution_completed']
            or fixed['verified_new_owner_scientific_fits']!=0 or fixed['all_deployed_sports_retrofitted']):
        raise ValueError('EXECUTION_REVIEW_NO_UNOBSERVED_OWNER_OR_CROSS_SPORT_DEPLOYMENT')
    if (logging['heartbeat_samples']!=249 or logging['health_errors'] or logging['heartbeat_interval_gate']!='PASS'
            or not 10.77<logging['maximum_gap_seconds']<10.78):
        raise ValueError('EXECUTION_REVIEW_LOG_EVIDENCE_CHANGED')
    sink=logging['s3_checkpoints']
    if (sink['scope'],sink['put_calls'],sink['get_calls'],sink['list_calls'],sink['attempted_body_bytes'])!=('LOG_CHECKPOINT_SINK_ONLY',97,0,0,10926934):
        raise ValueError('EXECUTION_REVIEW_TRANSFER_SCOPE_CHANGED')
    if cache['measurements']['s3_gets_completed']!=7970 or cache['measurements']['all_pipeline_S3_calls_instrumented']:
        raise ValueError('EXECUTION_REVIEW_CACHE_SCOPE_CHANGED')
    warm=cache['repeat_read_gate']
    if (warm['second_pass_network_disabled'] is not True or warm['new_owner_invocation_claim'] is not False
            or warm['second_pass']['s3_gets_completed']!=0 or warm['second_pass']['local_cache_hits']!=7970):
        raise ValueError('EXECUTION_REVIEW_WARM_CACHE_SCOPE_CHANGED')
    admission=value['resource_admission']
    if admission['resource_deferred_stages'] or admission['exact_stage_admission_statuses']!={'ADMITTED_EXACT_THREADS':119}:
        raise ValueError('EXECUTION_REVIEW_RESOURCE_DENIAL_NOT_OBSERVED')
    if value['cost_evidence']['actual_billed_cost_usd'] is not None:raise ValueError('EXECUTION_REVIEW_ESTIMATE_IS_NOT_INVOICE')
    budget=fixed['budget_verification']
    if (budget['selected_files']!=91718 or budget['physical_files_decoded_and_original_sha256_verified']!=3658
            or budget['external_description_count']!=88060 or budget['container_bytes_upper_bound']!=295689922
            or budget['full_report_original_bytes']!=226760148 or budget['full_report_archive_bytes']!=20717397
            or budget['full_owner_ancestor_readback_claimed'] is not False
            or budget['conditional_on_live_verified_ancestor_graph'] is not True
            or budget['new_scientific_fits']!=0):
        raise ValueError('EXECUTION_REVIEW_SAVED_ENGINEERING_SCOPE_CHANGED')
    package=fixed['package_verification']
    if package['status']=='PASS':
        if ({'bytes':package['exact_package_bytes'],'sha256':package['exact_package_sha256']}!=B082_PACKAGE_PIN
                or package['passed']!=package['packaged_tests'] or package['passed']<=0
                or any(package[key]!=0 for key in ('failures','errors','skipped','module_errors'))
                or package['owner_execution_performed'] or package['real_NBA_fits']!=0):
            raise ValueError('EXECUTION_REVIEW_EXACT_PACKAGE_VERIFICATION_CHANGED')
    body=json.dumps(value,sort_keys=True)
    for token in ('recipe_id','feature_names','s3://','/home/','/workspace/','api_key','apiKey','PRIVATE KEY'):
        if token in body:raise ValueError('EXECUTION_REVIEW_PRIVATE_FIELD_OR_PATH')
    return True

def strip_review(body):
    if body.count(BEGIN)!=body.count(END) or body.count(BEGIN)>1:raise ValueError('EXECUTION_REVIEW_DUPLICATE_OR_UNCLOSED')
    return re.sub(re.escape(BEGIN)+r'.*?'+re.escape(END)+r'\n?','',body,flags=re.S)

def render(value):
    validate(value);esc=lambda x:html.escape(str(x),quote=True)
    run=value['latest_owner_execution'];obs=value['observed_runtime'];native=obs['native_fit_exact_intervals']
    log=value['live_logging'];cache=value['cache_evidence'];sink=log['s3_checkpoints'];cost=value['cost_evidence']
    fixed=value['replacement_engineering'];budget=fixed['budget_verification'];cap=value['capacity_failures'];science=value['science_preservation'];projection=fixed['heartbeat_projection_replay']
    warm=cache['repeat_read_gate'];context=cache['authenticated_context_cache'];pins=cache['verified_file_cache']
    rows=[
      ('Actual owner outcome',f"{run['status']}; exit {run['exit_code']}; {run['elapsed_seconds']:.3f} seconds; {run['new_confirmed_scientific_fits']} confirmed native estimator fit; {run['new_forecasts']} new forecasts; {run['provider_requests']} provider requests."),
      ('Actual scientific overlap',f"Peak {obs['peak_concurrent_scientific_fits']} concurrent native fit; {native['native_fit_elapsed_seconds_sum']:.6f} fit seconds and {native['native_fit_process_cpu_seconds']:.3f} process CPU-seconds. The brief fit fell between ten-second samples. Twelve-core scientific utilization is not established."),
      ('Observed process CPU',f"{obs['time_weighted_cpu_cores']:.5f} average core equivalents over {obs['sample_elapsed_seconds']:.3f} measured seconds. Peak {obs['peak_cpu_cores']:.5f} was transport finalization. {obs['one_reserved_core_samples']} heartbeat samples reserved one core; {obs['twelve_reserved_core_samples']} reserved twelve. Compression throughput is not training throughput."),
      ('Resource admission',"All 119 recorded stage admissions accepted the exact requested thread count: 114 requested one, three requested two and two requested three. No stage resource denial was recorded. One 12.142-second control wait recovered; original safety limits stay active."),
      ('Capacity blockage',f"Raw bound {cap['initial_bound_bytes']:,} → {cap['bound_after_first_fit_bytes']:,} bytes after initial forecast work, against {cap['original_scientific_support_allowance_bytes']:,} bytes of scientific allowance. Final raw bound {cap['final_raw_bound_bytes']:,}; physical compressed support {cap['actual_final_support_bytes']:,}. Raw and compressed representations are distinct."),
      ('Persistent Parquet reuse',f"{context['contexts']} authenticated contexts; {context['rows']:,} rows; {context['bytes_read']:,} local bytes in {context['elapsed_seconds']:.3f} seconds; zero historical context-cache GETs and zero label-adapter repeats."),
      ('Owned-market content cache',f"{cache['measurements']['s3_gets_completed']:,} successful GETs / {cache['measurements']['s3_bytes']:,} bytes; {cache['measurements']['local_cache_hits']} local hits. The independent same-invocation repeat pass disabled network and read {warm['second_pass']['local_cache_hits']:,} cached versions in {warm['second_pass']['elapsed_seconds']:.3f} seconds with zero GETs. This is not a later owner execution."),
      ('Pipeline pin cache',f"{pins['files_hashed']:,} full-body hash operations / {pins['bytes_hashed']:,} bytes; {pins['verified_unchanged_files_reused']:,} unchanged-identity pin reuses. Operation counts are not unique files. Whole-pipeline S3 traffic is not fully instrumented."),
      ('Continuous actual-owner logging',f"{log['heartbeat_samples']} heartbeats; maximum gap {log['maximum_gap_seconds']:.6f} seconds; zero logger health errors. Human log {log['log_bytes']:,} bytes; JSONL {log['jsonl_bytes']:,} bytes. One false stalled-progress warning is reproduced despite successful GETs increasing 16 → 5,618."),
      ('Log checkpoints only',f"{sink['put_calls']} SDK PUT calls / {sink['attempted_body_bytes']:,} supplied compressed body bytes / {sink['elapsed_seconds']:.3f} measured transfer seconds; zero GET/LIST calls in this sink. Internal HTTP retry bytes were not measured."),
      ('Whole-instance cost estimate',f"${float(cost['estimated_whole_instance_invocation_usd']):.6f} over {cost['measured_total_elapsed_seconds']:.3f} seconds at ${float(cost['hourly_usd']):.2f}/hour. Actual billed cost and project allocation are unknown; overlapping estimates are not added."),
      ('Authenticated return',f"{run['return']['bytes']:,} bytes; {run['return']['members']} members; all {run['return']['payload_members_authenticated']} payload pins authenticated. SHA-256 {run['return']['sha256']}.")]
    table='\n'.join('<tr><th scope="row">'+esc(k)+'</th><td>'+esc(v)+'</td></tr>' for k,v in rows)
    repairs=''.join('<li>'+esc(x)+'</li>' for x in fixed['implemented_repairs'])
    package=fixed['package_verification']
    if package['status']=='PASS':
        package_text=f"PASS: {package['passed']}/{package['packaged_tests']} packaged tests; {package['exact_package_bytes']:,}-byte executable; SHA-256 {package['exact_package_sha256']}. Zero failed, errored or skipped tests. Exact owner execution remains pending."
    else:package_text='Final exact-package verification is pending; no completed package-test result is claimed.'
    live=fixed['live_logging_acceptance']
    live_gap=max(row['observed_max_gap_seconds'] for row in live['cases'])
    failures='; '.join(row['stage']+': '+row['error_class']+' / '+row['reason'] for row in value['scientific_failures'])
    encoded=json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).replace('<','\\u003c')
    return BEGIN+f'''
<section id="nba-execution-review" aria-labelledby="nba-execution-title">
<style>#nba-execution-review{{margin:22px 0;padding:20px;border:1px solid #bdced5;border-radius:8px;background:#f4f8fb}}#nba-execution-review h2{{margin-top:0}}#nba-execution-review p,#nba-execution-review td,#nba-execution-review li{{overflow-wrap:anywhere}}#nba-execution-review th{{white-space:normal;min-width:120px}}#nba-execution-review .scroll{{max-height:480px}}@media(max-width:600px){{#nba-execution-review{{padding:14px}}}}</style>
<h2 id="nba-execution-title">B081 actual: one fit, five forecasts; B082 recovery prepared</h2>
<p id="nba-execution-outcome"><strong>{esc(run['status'])}, exit {run['exit_code']}.</strong> The owner execution ran from {esc(run['started_at_utc'])} to {esc(run['finished_at_utc'])}. It entered scientific stages and produced one native estimator fit and five new forecasts, while capacity and adapter failures prevented substantial training progress.</p>
<p id="nba-execution-source-clock">Latest authentic original issue: <strong>{esc(science['latest_original_issue_at_utc'])}</strong>. This saved publication adds no fit, score, source refresh or newly issued forecast. It retains 2,700 shared selected issue objects exactly and preserves the five superseded selections in dated history.</p>
<div class="scroll"><table id="nba-execution-evidence"><thead><tr><th>Evidence</th><th>Actual saved measurement and scope</th></tr></thead><tbody>{table}</tbody></table></div>
<p id="nba-execution-failures"><strong>Recorded scientific blockers:</strong> {esc(failures)}. These failures do not erase saved work or receive fit credit. Model promotion remains disabled.</p>
<p id="nba-execution-budget-test"><strong>Verified saved-data engineering:</strong> the unchanged complete 91,718-file inventory and its 88,060 ancestor descriptions produce a {budget['container_bytes_upper_bound']:,}-byte compressed bound after the 3,658 physical files are decoded and authenticated. The live complete ancestor graph is still required; this is not an owner-wide fresh readback. Under pressure only changed physical bytes need compressed measurement; ample raw admission prepares no chunks. The unchanged {budget['full_report_original_bytes']:,}-byte full report round-tripped through a {budget['full_report_archive_bytes']:,}-byte archive with the original verifier: first measurement {budget['first_compressed_measurement_seconds']:.3f}s, same-process warm measurement {budget['same_process_warm_measurement_seconds']:.6f}s, seal and readback {budget['fast_seal_and_full_readback_seconds']:.3f}s. No scientific field was dropped and no controlled owner training speedup is claimed.</p>
<p id="nba-execution-projection-test">Saved telemetry replay: {projection['heartbeat_count']} heartbeats shrink from {projection['replayed_original_heartbeat_json_bytes']:,} to {projection['replayed_B082_evaluation_projection_heartbeat_json_bytes']:,} JSON bytes ({100*projection['replayed_heartbeat_byte_reduction_fraction']:.2f}% less) by bounding repeated evaluation projections. Fit, cache, transfer, CPU, cost and stage counters remain present. This replay is engineering evidence, not a new owner invocation.</p>
<details id="nba-execution-repairs"><summary>Implemented recovery and permanent logging changes</summary><ul>{repairs}</ul></details>
<p id="nba-execution-replacement-status"><strong>{esc(fixed['status'])}.</strong> The generic logger is shared by named projects; previously deployed NFL, FBS and NCAA executables have not been verified as retrofitted. B082 has no completed owner-host sports run in this evidence. Native fitting and successful operational progress have independent clocks.</p>
<p id="nba-execution-live-test"><strong>Real local logging acceptance:</strong> {live['elapsed_seconds']:.3f} seconds supervising blocked and failing children, with actual <code>tail -F</code> observations and independently growing human logs and JSONL. The interval was ten seconds; maximum observed gap was {live_gap:.6f} seconds. Stalled-child diagnostics remained available and the failing child exit stayed visible. These OS process fixtures perform no sports computation or AWS execution.</p>
<p id="nba-execution-package-status"><strong>Replacement package verification:</strong> {esc(package_text)}</p>
<p>Current saved outputs cover {science['observed_canonical_games']:,} canonical game identities and {science['secondary_observations']} secondary observations, {science['champion_roles']} active metric roles and {science['saved_current_review_metric_rows']} saved current-review metric rows. The dated B077 panel retains its {science['saved_dated_b077_metric_rows']} metric rows and {science['saved_dated_b077_venue_rows']} venue comparisons with their earlier clocks. Full future schedule coverage and full-season matched market rankings remain unavailable.</p>
<p><a href="latest_execution_review.json">Download sanitized execution evidence</a> · <a href="history/b081_prepared_execution_review.json">Preserved B080 failure and B081 preparation review</a> · <a href="history/b077_recovered_selected_outputs.json">Preserved earlier selected outputs</a> · <a href="selected_issue_preservation.json">Issue preservation audit</a> · <a href="../../../runtime/execution/README.md">Shared live logging framework</a></p>
<script id="nba-execution-data" type="application/json">{encoded}</script>
</section>
'''+END+'\n'

def attach(body,value):
    clean=strip_review(body)
    if digest(clean.encode())!=BASE_DISPLAY_SHA256:raise ValueError('EXECUTION_REVIEW_BASE_DISPLAY_CHANGED_REVIEW_FIRST')
    if clean.count(POINT)!=1:raise ValueError('EXECUTION_REVIEW_INSERTION_POINT')
    return clean.replace(POINT,POINT+render(value),1)

def build(check=False):
    for name,pin in SOURCE_PINS.items():
        if digest((ROOT/name).read_bytes())!=pin:raise ValueError('EXECUTION_REVIEW_RESEARCH_CHANGED:'+name)
    value=json.loads((ROOT/'latest_execution_review.json').read_bytes())
    if check and value['replacement_engineering']['package_verification']['status']!='PASS':raise ValueError('EXECUTION_REVIEW_FINAL_PACKAGE_RECEIPT_REQUIRED')
    path=ROOT/'latest_research_outputs.html';body=attach(path.read_text(),value).encode()
    if check and path.read_bytes()!=body:raise ValueError('EXECUTION_REVIEW_DISPLAY_STALE')
    if not check:path.write_bytes(body)
    return {'status':'PASS' if check else 'BUILT','source_inputs':SOURCE_PINS,'publication_new_fits':0,'display_bytes':len(body),'display_sha256':digest(body)}

if __name__=='__main__':print(json.dumps(build('--check' in sys.argv),sort_keys=True))
