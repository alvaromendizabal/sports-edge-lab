"""Authenticated R7 resource wait and qualified R8 continuation status."""
from pathlib import Path
import html,json,re
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
START='<!-- B063R8_ADMISSION_STATUS_START -->'
END='<!-- B063R8_ADMISSION_STATUS_END -->\n'
BANNER=(HERE/'b063r8_banner.html.tmpl').read_text()

def load_payload():
    value=json.loads((HERE/'B063R8_PUBLIC_STATUS.json').read_text())
    actual=value['latest_actual_owner'];admission=value['actual_admission'];observer=value['actual_observer']
    if (actual['release'],actual['status'],actual['failure_code'])!=('B063R7','RESOURCE_DEFERRED_PARTIAL_WORK_PRESERVED','V7_INITIAL_SHARED_LEASE_UNAVAILABLE'):raise ValueError('Authenticated failure changed')
    if any(actual[k] for k in ('new_owner_fits','scientific_fit_attempts','reused_scientific_fits','failed_scientific_fits','new_checkpoints','reused_checkpoints','new_forecasts','new_metric_scores','new_market_quotes','native_preflight_entered','selftests_entered','full_scientific_run_completed')):raise ValueError('Admission waiting cannot create science')
    if actual['worker_elapsed_seconds']!=121.32082730900038 or actual['admission_phase_seconds']!=120.02053888299997:raise ValueError('Actual clocks changed')
    if (admission['decisions'],admission['reason_counts'],admission['reserved_cpus'],admission['cpu_ready_observations'])!=(118,{'IO_FULL_PRESSURE':118},0,117):raise ValueError('Admission measurements changed')
    if admission['available_CPU_is_safe_IO_capacity'] or admission['foreign_processes_signaled']:raise ValueError('No capacity or process-control invention')
    if observer['JSONL_rows']!=33 or observer['human_event_records']!=33 or observer['heartbeats']!=15 or observer['watchdog_samples']!=13:raise ValueError('Captured row counts changed')
    if not observer['heartbeat_interval_verified'] or not 10<=observer['maximum_monotonic_heartbeat_gap_seconds']<10.01:raise ValueError('Observed heartbeat cadence changed')
    if observer['complete_terminal_log_claimed'] or observer['scientific_workers'] or observer['twelve_core_scientific_acceptance_proven']:raise ValueError('Observed logs do not prove science or post-capture completeness')
    cache=value['actual_cache_and_cost']
    if cache['store_initialized'] or cache['historical_cache_benchmark_exercised'] or cache['zero_defaults_measure_all_S3_calls'] or cache['estimated_cost_usd'] is not None:raise ValueError('Unused cache and unverified cost stay unavailable')
    saved=value['preserved_evidence']
    if (saved['authenticated_prior_target_fits'],saved['exact_content_objects_reverified'],saved['broader_B062_target_fit_receipts'],saved['broader_B062_terminal_commit_references'])!=(22,134,115,2793):raise ValueError('Prior inventories changed')
    if saved['distinct_run_inventories_summed'] or saved['all_broader_model_bytes_reopened'] or saved['new_fit_credit_for_preservation']:raise ValueError('Preserved receipts are not new fits')
    scientific=value['preserved_science']
    if (scientific['historical_candidate_metric_panels'],scientific['historical_per_season_leaders'],scientific['historical_pooled_leaders'],len(scientific['current_observed_replay_leaders']))!=(164,28,14,14):raise ValueError('Saved champion populations changed')
    if any(x['selection_or_promotion_authority'] or x['full_official_season_coverage_certified'] for x in scientific['current_observed_replay_leaders']):raise ValueError('Retrospective monitoring cannot promote')
    metric=value['metric_policy']
    if metric['new_scores'] is not None or any(metric[k] for k in ('current_season_complete','rolling_or_original_issue_promotion','missing_quotes_fabricated','provider_refresh_performed')):raise ValueError('No full-season or provider refresh established')
    prepared=value['prepared_continuation'];fingerprint=prepared['source_sha256']
    if fingerprint is not None and re.fullmatch('[0-9a-f]{64}',fingerprint) is None:raise ValueError('Invalid prepared fingerprint')
    if prepared['owner_execution_verified'] or prepared['new_preparation_scientific_fits'] or prepared['scientific_twelve_core_acceptance_passed']:raise ValueError('Preparation is not owner scientific acceptance')
    if prepared['moderate_IO_aggregate_lanes_per_owner']!=1 or not prepared['severe_or_unknown_IO_deferred'] or not prepared['CPU_memory_disk_fairness_guards_retained']:raise ValueError('Bounded IO policy changed')
    binding=prepared['shared_logger_binding']
    if binding['module_sha256']!='607954a6f5dc4eba98e3edd121360d52aa00ff4a148c8630dd79f125b44b6947' or binding['matching_test_sha256']!='be68fabfddb481a0859d6bde4d8775d10f06b281b7055f8466aaca7d54e18a89':raise ValueError('Dated shared logger binding changed')
    if binding['public_shared_files_modified'] or not binding['prior_R7_logger_provenance_retained']:raise ValueError('Shared lineage must remain preserved')
    if fingerprint is not None and (binding['status']!='PASS' or not binding['sealed_package_members_reopened']):raise ValueError('Sealed source requires physical shared member verification')
    if fingerprint is not None:
        continuity=prepared.get('science_identity_continuity',{})
        if continuity.get('fitted_family_identities_unchanged')!=7 or not continuity.get('all_seven_fitted_families_preserved') or not continuity.get('rolling_v7_execution_identity_changed') or continuity.get('all_eight_unchanged_claimed'):raise ValueError('Seven fitted families preserved; execution identity changes explicitly')
    return value

def strip_banner(body):
    if START not in body and END not in body:return body
    if body.count(START)!=1 or body.count(END)!=1 or body.count(BANNER)!=1:raise ValueError('Unexpected R8 banner')
    return body.replace(BANNER,'',1)

def render_banner(body):
    body=strip_banner(body)
    if body.count('<main>')!=1:raise ValueError('Expected one main')
    return body.replace('<main>','<main>'+BANNER,1)

def render_page():
    payload=load_payload();prepared=payload['prepared_continuation'];validation=prepared['validation']
    raw=json.dumps(payload,indent=2,ensure_ascii=False)+'\n'
    rows=[]
    for row in payload['preserved_science']['current_observed_replay_leaders']:
        label='Men' if row['league']=='ncaam' else 'Women'
        metric=row['metric_name_for_display'].replace('_',' ')
        score=f"{row['value']:.6f}"
        models=' / '.join(row['public_model_ids'])
        rows.append('<tr><td>'+label+'</td><td>'+html.escape(metric)+'</td><td>'+score+'</td><td>'+str(row['games'])+'</td><td>'+html.escape(models)+'</td></tr>')
    return ((HERE/'b063r8_status.html.tmpl').read_text()
        .replace('__B063R8_JSON__',raw.replace('</','<\\/'))
        .replace('__B063R8_SOURCE__',prepared['source_sha256'] or 'Final source pin pending')
        .replace('__B063R8_TESTS__',html.escape(validation['public_summary']) if validation else 'Final sealed verification is pending. No R8 owner execution or scientific throughput is claimed.')
        .replace('__B063R8_LEADERS__',''.join(rows)))

def status_outputs(prior):
    result=dict(prior);landing=ROOT/'docs/ncaa/index.html'
    if landing in result:result[landing]=render_banner(result[landing])
    result[ROOT/'docs/ncaa/b063r8.html']=render_page()
    result[ROOT/'docs/ncaa/data/B063R8_PUBLIC_STATUS.json']=(HERE/'B063R8_PUBLIC_STATUS.json').read_text()
    return result
