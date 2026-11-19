"""Deterministic, bounded public FBS recovery evidence; no private owner execution."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / 'docs/fbs/v101/data/status.json'
OUTPUT = ROOT / 'docs/fbs/v101/index.html'
SHAPES = json.loads((Path(__file__).parent / 'public_shapes.json').read_text())


def require(condition, message):
    if not condition:
        raise ValueError(message)


def boundary(value, location='$'):
    if isinstance(value, dict):
        require(sorted(value) in SHAPES.get(location, []), 'Unexpected public fields: ' + location)
        for key, item in value.items():
            boundary(item, location + '.' + key)
    elif isinstance(value, list):
        for item in value:
            boundary(item, location + '[]')


def validate(data):
    boundary(data)
    raw = json.dumps(data, sort_keys=True)
    require(not re.search(r's3://|/home/|/workspace/|sagemaker|arn:aws|api[_-]?key|secret[_-]?key|circa|feature_names|raw_quotes|owner_relative_path|\.pyz', raw, re.I), 'Private or out-of-scope material')
    require(data['owner'] == 'FBS', 'FBS scope only')
    publication = data['publication']
    require(publication == {'owner_executions_started_by_publication': 0, 'website_deployment_claimed': False, 'production_promoted': False, 'private_artifacts_published': False}, 'Publication cannot execute or deploy')
    attempt = data['latest_attempt']
    require(attempt['version'] == 'V100' and attempt['child_exit_code'] == attempt['supervisor_exit_code'] == 2, 'V100 remains a failed owner execution')
    require(attempt['operational_status'] == 'FAILED_BEFORE_SCIENTIFIC_DISPATCH' and attempt['scientific_status'] == 'SAFE_PARTIAL_FAILURE_V13', 'Failure cannot become success')
    require(attempt['supervisor_status'] == 'VERIFIED_RETURN_PUBLICATION_FINISHED', 'Supervisor transport result must be retained')
    require(attempt['failure_code'] == 'COMMITTED_CHECKPOINT_RECOVERY_NOT_READY; NO_COMPLETED_WORK_RESTART', 'Recovery failure reason changed')
    require(attempt['failed_stage'] == 'checkpoint_recovery' and (attempt['recovery_completed_units'], attempt['recovery_total_units']) == (28513, 44841), 'Recovery denominator changed')
    require(all(attempt[k] == 0 for k in ('new_model_fits', 'new_calibrator_fits', 'new_scoring_tasks', 'reused_fit_admissions_this_attempt')), 'Unreached science cannot be credited')
    require(attempt['fit_counts_complete'] is False, 'Unreached scientific accounting remains incomplete')
    returned = attempt['return']
    require(returned['integrity_verified'] is True and returned['durable_available'] is True and returned['partial_or_resumable'] is True, 'Verified resumable return retained')
    require(returned['owner_execution_successful'] is False, 'Verified transport cannot relabel owner failure')
    require(returned['bytes'] == 73426500 and returned['sha256'] == 'a6601bf92b9c971cd4f7bc38a0650553efed378afc54492ab9db729c942297dd', 'Actual return pin changed')
    require(returned['parts'] == 1 and returned['maximum_part_bytes'] == 512 * 1024 * 1024 and returned['bytes'] <= returned['maximum_part_bytes'], 'Compact return part bound')
    old = {row['version']: row for row in data['preserved_science']}
    require(set(old) == {'V098', 'V099'} and all(r['operational_status'] == 'SUCCESS' for r in old.values()), 'Successful predecessor work cannot be relabeled')
    require(old['V098']['fit_jobs'] == 1125 and old['V098']['new_fits'] + old['V098']['reused_fits'] == 1125, 'V098 fit accounting')
    require(old['V099']['new_scoring_tasks'] == 600 and old['V099']['reused_fits'] == 1125 and old['V099']['new_fits'] == 0, 'V099 completed scoring retained')
    model = data['model_evaluation']
    require(model['validation_seasons'] == [2024, 2025] and model['test_season'] == 2026 and model['test_previously_exposed'] is True, 'Validation/test boundary')
    require(not model['test_used_for_selection'] and not model['training_season_reweighting'] and not model['originally_issued'], 'No selection leakage or issue claim')
    require(model['completed_cohorts'] == [919, 934, 755] and model['new_2026_census_completed'] == 757 and model['new_census_games_scored_by_v100'] == 0, 'Census cannot rewrite evaluated populations')
    require(model['profiles'] == ['50/50', '40/60', '30/70', '20/80', '10/90'], 'Evaluation-only profiles retained')
    refresh = attempt['source_refresh']
    require((refresh['provider_calls'], refresh['new_paid_market_calls'], refresh['observed_games'], refresh['completed_games'], refresh['net_completed_count_increase']) == (2, 0, 888, 757, 2), 'Actual source refresh accounting')
    require(refresh['full_census_certified'] is False and refresh['empty_postseason_response'] is True, 'Empty postseason response cannot prove census')
    perf = data['performance']
    require(perf['configured_workers'] == 36 and perf['sustained_scientific_capacity_pass'] is False and perf['scientific_cpu_acceptance'] == 'NOT_MEASURED_SCIENTIFIC_DISPATCH_NOT_REACHED', 'Configured workers cannot prove scientific CPU')
    require(abs(perf['recovery_cpu_cores'] - perf['recovery_process_cpu_seconds'] / perf['recovery_seconds']) < 1e-9, 'Recovery actual CPU calculation')
    require(abs(perf['custody_cpu_cores'] - perf['custody_process_cpu_seconds'] / perf['custody_seconds']) < 1e-9, 'Custody actual CPU calculation')
    require(perf['scientific_checkpoint_files_modified'] == 0 and perf['working_parallel_verifier_preserved'] is True, 'Checkpoint custody preservation')
    stages = data['attempt_stages']
    require([s['number'] for s in stages] == list(range(1, 22)), 'Numbered stage manifest completeness')
    require(stages[1]['key'] == 'checkpoint_recovery' and stages[1]['status'] == 'Failed', 'Failed stage remains visible')
    require('BEFORE_SUPERVISOR_CLOSURE' in data['stage_snapshot_scope'], 'Child snapshot cannot claim final supervisor state')
    for stage in stages:
        require(stage['status'] in {'Authenticated completed', 'Reused', 'Running', 'Pending', 'Blocked', 'Failed', 'Deferred'}, 'Stage status is explicit')
        require(stage['total'] is None or 0 <= stage['completed'] <= stage['total'], 'Stage progress denominator')
    next_release = data['next_release']
    require(next_release['version'] == 'V101' and not next_release['owner_execution_started'] and not next_release['new_science_claimed'], 'Preparation is not execution')
    require(next_release['runtime_reauthentication_required'] is True and next_release['expected_reusable_fit_jobs'] == 1125 and next_release['expected_reusable_scoring_tasks'] == 600, 'Completed work reuse requirement')
    require(next_release['worker_ceiling_choices'] == [12, 24, 36] and next_release['native_threads_per_worker'] == 1 and next_release['sustained_scientific_capacity_pass'] is False, 'Worker ceilings are not an acceptance result')
    require(next_release['prepared_fit_jobs'] == next_release['prepared_validation_fit_jobs'] + next_release['prepared_frozen_test_fit_jobs'], 'Finite scientific work accounting')
    require(next_release['prepared_census_streams'] == 12 and next_release['prepared_residual_policies'] == 126, 'Registered census and residual scope')
    require(next_release['prepared_residual_forecast_tasks'] == next_release['prepared_residual_uncertainty_tasks'] == 378 and next_release['prepared_residual_metric_comparisons'] == 1134, 'Residual scientific task accounting')
    require(next_release['prepared_maximum_residual_parameter_fits'] == 756 and next_release['prepared_maximum_total_t60_policies'] == 1570, 'Residual bounds remain planned counts')
    for evidence in next_release['validation_evidence']:
        require(evidence['status'] in {'PASS', 'PENDING', 'BLOCKED'} and isinstance(evidence['checks'], int) and evidence['checks'] >= 0, 'Bounded preparation evidence')
    if next_release['prepared_complete']:
        require(next_release['status'] == 'PREPARED_NOT_EXECUTED', 'Prepared status requires final verification')
        require(isinstance(next_release['canonical_bytes'], int) and next_release['canonical_bytes'] > 0 and re.fullmatch('[a-f0-9]{64}', next_release['canonical_sha256'] or ''), 'Prepared executable pin missing')
        require(next_release['validation_evidence'] and all(x['status'] == 'PASS' for x in next_release['validation_evidence']), 'Final preparation evidence required')
    else:
        require(next_release['status'] == 'PREPARED_NOT_EXECUTED' and next_release['canonical_bytes'] is None and next_release['canonical_sha256'] is None, 'Draft must not invent a deliverable pin')
    require(len(data['remaining_work']) >= 6 and any(row['status'] == 'Blocked' for row in data['remaining_work']), 'Unfinished science remains disclosed')


def render(data):
    validate(data)
    payload = json.dumps(data, sort_keys=True, separators=(',', ':'), ensure_ascii=False).replace('<', '\\u003c')
    digest = hashlib.sha256(payload.encode()).hexdigest()
    template = (Path(__file__).parent / 'template.html.in').read_text()
    return template.replace('@@PAYLOAD@@', payload).replace('@@SHA256@@', digest).encode()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    body = render(json.loads(DATA.read_text()))
    if args.check:
        require(OUTPUT.read_bytes() == body, 'Generated public page is stale')
    else:
        OUTPUT.write_bytes(body)
    print(json.dumps({'status': 'PASS', 'public_html_bytes': len(body), 'sha256': hashlib.sha256(body).hexdigest(), 'owner_executions_started': 0}))


if __name__ == '__main__':
    main()
