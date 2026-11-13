"""Authenticated R6 admission failure and qualified R7 engineering status."""
from pathlib import Path
import json,re
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
START='<!-- B063R7_ADMISSION_STATUS_START -->'
END='<!-- B063R7_ADMISSION_STATUS_END -->\n'
BANNER=(HERE/'b063r7_banner.html.tmpl').read_text()

def load_payload():
 value=json.loads((HERE/'B063R7_PUBLIC_STATUS.json').read_text())
 actual=value['latest_actual_owner']; admission=value['actual_admission']; saved=value['preserved_evidence']
 if (actual['release'],actual['status'],actual['failure_code'])!=('B063R6','RESOURCE_DEFERRED_PARTIAL_WORK_PRESERVED','V7_INITIAL_SHARED_LEASE_UNAVAILABLE'):raise ValueError('Authenticated actual status changed')
 if any(actual[k] for k in ('new_owner_fits','scientific_fit_attempts','reused_scientific_fits','failed_scientific_fits','new_checkpoints','reused_checkpoints','new_forecasts','new_metric_scores','new_market_quotes','native_preflight_entered','selftests_entered','full_scientific_run_completed')):raise ValueError('Pre-science admission failure cannot establish work')
 if actual['worker_elapsed_seconds']!=1.7489990870001293 or actual['admission_wait_seconds']!=1.0061335450000115:raise ValueError('Observed clocks changed')
 if (admission['reason'],admission['reserved_cpus'],admission['shared_lease_rechecks_observed'],admission['io_full_avg10_percent'])!=(['IO_FULL_PRESSURE'],0,0,20.14):raise ValueError('Observed resource denial changed')
 if admission['cpu_measurement_ready'] or admission['available_cpu_cores'] is not None or admission['pressure_was_proved_gone_in_actual_R6']:raise ValueError('Unready capacity cannot become a measured grant')
 recovery=value['actual_recovery']
 if recovery['status']!='PRIOR_PINNED_R3_RECOVERY_REVERIFIED' or not recovery['safe_to_launch'] or recovery['unique_old_exact_identities_rechecked_dead']!=2:raise ValueError('Recovery recheck changed')
 if recovery['process_control_required'] or recovery['new_signals_sent'] or recovery['new_lease_releases_claimed']:raise ValueError('No new process-control claim')
 if (saved['authenticated_prior_target_fits'],saved['exact_content_objects_reverified'],saved['new_fit_credit_for_preservation'])!=(22,134,0):raise ValueError('Prior science is preservation only')
 observer=value['actual_observer']
 if observer['included_samples']!=1 or any(observer[k] for k in ('heartbeat_interval_verified','literal_LIVE_EXECUTION_files_present','complete_terminal_log_claimed','twelve_core_scientific_acceptance_proven','scientific_workers')):raise ValueError('Single owner sample is not a cadence or science benchmark')
 cache=value['actual_cache_and_cost']
 if cache['dollar_estimate'] is not None or cache['persistent_history_cache_benchmark_exercised']:raise ValueError('No unobserved cost or cache claim')
 prepared=value['prepared_continuation']; fingerprint=prepared['source_sha256']
 if fingerprint is not None and re.fullmatch('[0-9a-f]{64}',fingerprint) is None:raise ValueError('Invalid prepared fingerprint')
 if any(prepared[k] for k in ('owner_execution_verified','new_preparation_scientific_fits','resource_guards_relaxed','NCAA_live_owner_activation_verified')):raise ValueError('Prepared continuation is not owner acceptance')
 logs=value['shared_logging_engineering']
 if logs['projects']!=['nfl','fbs','nba','ncaa_basketball'] or len(logs['cases'])!=4:raise ValueError('All four local selectors required')
 if any(logs[k] for k in ('synthetic_CPU_probe_performed','scientific_fit_credit','actual_cloud_owner_execution','all_deployed_private_runners_modified')):raise ValueError('Local logging evidence cannot become deployment or science')
 if any(c['status']!='PASS' or not 9.9<c['maximum_gap_seconds']<=15 or c['actual_sports_fit_credit'] for c in logs['cases']):raise ValueError('Actual local cadence changed')
 metrics=value['metric_policy']
 if metrics['new_scores'] is not None or any(metrics[k] for k in ('current_season_complete','rolling_or_original_issue_promotion','missing_quotes_fabricated','provider_refresh_performed')):raise ValueError('No new scores or full-season coverage')
 return value

def strip_banner(body):
 if START not in body and END not in body:return body
 if body.count(START)!=1 or body.count(END)!=1 or body.count(BANNER)!=1:raise ValueError('Unexpected admission status banner')
 return body.replace(BANNER,'',1)

def render_banner(body):
 body=strip_banner(body)
 if body.count('<main>')!=1:raise ValueError('Expected one main element')
 return body.replace('<main>','<main>'+BANNER,1)

def render_page():
 payload=load_payload();prepared=payload['prepared_continuation'];validation=prepared['validation']
 raw=json.dumps(payload,indent=2,ensure_ascii=False)+'\n'
 return ((HERE/'b063r7_status.html.tmpl').read_text()
   .replace('__B063R7_JSON__',raw.replace('</','<\\/'))
   .replace('__B063R7_SOURCE__',prepared['source_sha256'] or 'Awaiting the sealed engineering build')
   .replace('__B063R7_TESTS__',validation['public_summary'] if validation else 'Final sealed verification is pending; the separate all-project logging evidence below is complete.'))

def status_outputs(prior):
 result=dict(prior);landing=ROOT/'docs/ncaa/index.html'
 if landing in result:result[landing]=render_banner(result[landing])
 result[ROOT/'docs/ncaa/b063r7.html']=render_page()
 result[ROOT/'docs/ncaa/data/B063R7_PUBLIC_STATUS.json']=(HERE/'B063R7_PUBLIC_STATUS.json').read_text()
 return result
