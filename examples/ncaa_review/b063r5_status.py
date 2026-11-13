"""Authenticated preflight failure layered over unchanged NCAA evidence."""
from pathlib import Path
import json
import re
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
START = '<!-- B063R5_PREFLIGHT_STATUS_START -->'
END = '<!-- B063R5_PREFLIGHT_STATUS_END -->\n'
BANNER = (HERE / 'b063r5_banner.html.tmpl').read_text()

def load_payload():
    value = json.loads((HERE / 'B063R5_PUBLIC_STATUS.json').read_text())
    actual = value['latest_actual_owner']; saved = value['preserved_evidence']
    prepared = value['prepared_continuation']; metrics = value['metric_policy']
    if (actual['release'], actual['status'], actual['new_owner_fits']) != ('B063R4', 'PREFLIGHT_FAILED', 0):
        raise ValueError('Latest authenticated owner failure changed')
    if actual['failure_code'] != 'B065_PIDFD_REQUIRED_FOR_PROCESS_CONTROL' or not actual['missing_python_pidfd_binding']:
        raise ValueError('The authenticated missing-binding failure changed')
    for field in ('specific_missing_binding','owner_python_version','owner_kernel_version','owner_libc_version','failure_clock_verified'):
        if actual[field] is not None: raise ValueError('Unobserved owner detail cannot be invented: ' + field)
    for field in ('kernel_pidfd_support_tested_by_failed_code','referenced_recovery_diagnostic_in_attached_return','old_R3_shutdown_verified','return_filename_time_is_failure_time','whole_scientific_run_completed','new_metrics_or_forecasts'):
        if actual[field]: raise ValueError('Failure evidence cannot establish: ' + field)
    if (saved['authenticated_prior_target_fits'], saved['exact_content_objects_reverified'], saved['new_fit_credit_for_preservation'], saved['model_deserializations_in_review']) != (22, 134, 0, 0):
        raise ValueError('Preserved population or reuse fit credit changed')
    if not saved['scientific_runtime_compatibility_still_required'] or not saved['previous_public_science_and_issue_clocks_unchanged']:
        raise ValueError('Prior scientific provenance must remain exact')
    if any(prepared[k] for k in ('owner_execution_verified','owner_environment_verified','new_preparation_scientific_fits','engineering_tests_are_scientific_performance')):
        raise ValueError('Preparation cannot establish new owner science or performance')
    fingerprint = prepared['source_sha256']
    if fingerprint is not None and re.fullmatch('[0-9a-f]{64}', fingerprint) is None:
        raise ValueError('Invalid prepared source fingerprint')
    if metrics['new_scores'] is not None or any(metrics[k] for k in ('current_season_complete','rolling_or_original_issue_promotion','missing_quotes_fabricated','twelve_core_scientific_acceptance_proven','provider_refresh_performed')):
        raise ValueError('Operational status cannot invent scientific completion or provider updates')
    return value

def strip_banner(body):
    if START not in body and END not in body: return body
    if body.count(START) != 1 or body.count(END) != 1 or body.count(BANNER) != 1:
        raise ValueError('Unexpected preflight status banner bytes')
    return body.replace(BANNER, '', 1)

def render_banner(body):
    body = strip_banner(body)
    if body.count('<main>') != 1: raise ValueError('Expected one NCAA main element')
    return body.replace('<main>', '<main>' + BANNER, 1)

def render_page():
    payload = load_payload()
    raw = json.dumps(payload, indent=2, ensure_ascii=False) + '\n'
    prepared = payload['prepared_continuation']
    fingerprint = prepared['source_sha256'] or 'Awaiting the sealed engineering build'
    verification = prepared['validation']
    checks = ('Awaiting the final packaged verification receipt.' if verification is None
              else verification['public_summary'])
    return ((HERE / 'b063r5_status.html.tmpl').read_text()
            .replace('__B063R5_JSON__', raw.replace('</', '<\\/'))
            .replace('__B063R5_SOURCE__', fingerprint)
            .replace('__B063R5_TESTS__', checks))

def status_outputs(prior):
    result = dict(prior); landing = ROOT / 'docs/ncaa/index.html'
    if landing in result: result[landing] = render_banner(result[landing])
    result[ROOT / 'docs/ncaa/b063r5.html'] = render_page()
    result[ROOT / 'docs/ncaa/data/B063R5_PUBLIC_STATUS.json'] = (HERE / 'B063R5_PUBLIC_STATUS.json').read_text()
    return result
