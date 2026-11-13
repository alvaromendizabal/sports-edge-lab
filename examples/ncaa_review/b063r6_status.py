"""Actual recovery and startup failure over preserved NCAA scientific evidence."""
from pathlib import Path
import json,re
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
START='<!-- B063R6_RECOVERY_STATUS_START -->'
END='<!-- B063R6_RECOVERY_STATUS_END -->\n'
BANNER=(HERE/'b063r6_banner.html.tmpl').read_text()

def load_payload():
 value=json.loads((HERE/'B063R6_PUBLIC_STATUS.json').read_text())
 actual=value['latest_actual_owner']; recovery=value['actual_recovery']; saved=value['preserved_evidence']
 if (actual['release'],actual['status'],actual['new_owner_fits'])!=('B063R5','FAILED_PARTIAL_WORK_PRESERVED',0):raise ValueError('Authenticated owner status changed')
 if actual['failure_code']!='B032_FRESH_PACKAGE_TESTS_FAILED':raise ValueError('Authenticated startup failure changed')
 if (actual['unique_startup_cases'],actual['passed_startup_cases'],actual['errored_startup_cases'],actual['subtest_error_events'])!=(116,115,1,3):raise ValueError('Unique tests and subtest events must remain distinct')
 if any(actual[k] for k in ('new_scientific_fit_attempts','reused_scientific_fits','failed_scientific_fits','new_checkpoints','reused_checkpoints','full_scientific_run_completed','new_metrics_or_forecasts')):raise ValueError('Failed pre-science run cannot establish science')
 if recovery['status']!='EXACT_OLD_OWNER_EXIT_VERIFIED_SAFE_TO_LAUNCH' or not all(recovery[k] for k in ('old_worker_exit_verified','registered_frontend_exit_verified','forced_shutdown','exact_old_lease_released','foreign_lease_records_unchanged','canonical_locks_acquired_before_new_worker','kernel_capability_was_exercised')):raise ValueError('Actual recovery evidence changed')
 if any(recovery[k] for k in ('foreign_process_signals','lock_files_deleted','observed_python_pidfd_open','observed_python_pidfd_send_signal','numeric_PID_signal_fallback')):raise ValueError('Unsafe or unobserved process-control claim')
 if recovery['observed_python_version']!='3.12.15' or recovery['actual_backend']!='libc.pidfd_open + libc.pidfd_send_signal':raise ValueError('Observed owner capability changed')
 if (saved['authenticated_prior_target_fits'],saved['exact_content_objects_reverified'],saved['new_fit_credit_for_preservation'],saved['model_deserializations_in_review'])!=(22,134,0,0):raise ValueError('Prior fits are preservation only')
 observer=value['actual_observer']
 if observer['included_samples']!=5 or len(observer['intervals_seconds'])!=4 or not all(9.9<n<10.1 for n in observer['intervals_seconds']):raise ValueError('Actual observer cadence changed')
 if observer['scientific_workers'] or observer['twelve_core_scientific_acceptance_proven'] or observer['complete_terminal_log_claimed']:raise ValueError('Observer prefix is not scientific acceptance')
 if observer['application_ledger_peak_CPU_equivalents']!=0.6913211502831491 or observer['independent_watchdog_peak_CPU_equivalents']!=0.8239929701863001:raise ValueError('Different CPU samplers must retain exact attribution')
 prepared=value['prepared_continuation']; fingerprint=prepared['source_sha256']
 if fingerprint is not None and re.fullmatch('[0-9a-f]{64}',fingerprint) is None:raise ValueError('Invalid prepared fingerprint')
 if prepared['owner_execution_verified'] or prepared['new_preparation_scientific_fits']:raise ValueError('Preparation is not owner execution')
 metrics=value['metric_policy']
 if metrics['new_scores'] is not None or any(metrics[k] for k in ('current_season_complete','rolling_or_original_issue_promotion','missing_quotes_fabricated','provider_refresh_performed')):raise ValueError('No new scores, quotes or full-season coverage')
 return value

def strip_banner(body):
 if START not in body and END not in body:return body
 if body.count(START)!=1 or body.count(END)!=1 or body.count(BANNER)!=1:raise ValueError('Unexpected recovery status banner')
 return body.replace(BANNER,'',1)

def render_banner(body):
 body=strip_banner(body)
 if body.count('<main>')!=1:raise ValueError('Expected one main element')
 return body.replace('<main>','<main>'+BANNER,1)

def render_page():
 payload=load_payload(); prepared=payload['prepared_continuation']; validation=prepared['validation']
 raw=json.dumps(payload,indent=2,ensure_ascii=False)+'\n'
 return ((HERE/'b063r6_status.html.tmpl').read_text()
   .replace('__B063R6_JSON__',raw.replace('</','<\\/'))
   .replace('__B063R6_SOURCE__',prepared['source_sha256'] or 'Awaiting the sealed engineering build')
   .replace('__B063R6_TESTS__',validation['public_summary'] if validation else 'The final sealed verification receipt is still being prepared.'))

def status_outputs(prior):
 result=dict(prior); landing=ROOT/'docs/ncaa/index.html'
 if landing in result:result[landing]=render_banner(result[landing])
 result[ROOT/'docs/ncaa/b063r6.html']=render_page()
 result[ROOT/'docs/ncaa/data/B063R6_PUBLIC_STATUS.json']=(HERE/'B063R6_PUBLIC_STATUS.json').read_text()
 return result
