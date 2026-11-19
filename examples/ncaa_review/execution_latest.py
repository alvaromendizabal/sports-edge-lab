"""Render the latest owner invocations above the preserved earlier audit.

Only sanitized counters and evidence digests are published. A verified return,
pointer repair, engineering gate and scientific fit keep distinct scopes.
"""
from copy import deepcopy
from datetime import datetime
from html import escape
from pathlib import Path
import base64
import json
import math
import re

HERE = Path(__file__).resolve().parent
DATA = HERE / 'EXECUTION_STATUS_R32_20261119.json'
FORBIDDEN = re.compile(r's3://|/home/|sagemaker-sports|arn:aws|AKIA[0-9A-Z]{16}|secret_access_key|api_key|access_token|\.pyz\b|circa', re.I)
MANIFESTS = (
    'dffcf2cbfa04bd7a640ba1ef559007f02ade814e462361b3e486a37b0a1379ad',
    'dbde68eefe447dae21da32631274156a391ab54bc419987896681eb163171957',
    '9805bf20eb8b3bc0100bcc51ee739eccee859d018a7e192f5ef80f9b0797bf4f',
)
RETURNS = (
    ('9eb363ca19b378194e20496bab3fd78bebf17acb695cf5ea3e8aada4b38432f4', 8686724, 115),
    ('9d73a2955e9027f21be7994b7f30547785d2fae2f43d46034cc662e85dbe5a3f', 8861627, 116),
    ('beaba47640f324cb9ee9f166d0a2da5652b0d6d51e87cd4a6623c511fe53ee3b', 9060737, 116),
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def aware(value):
    result = datetime.fromisoformat(value.replace('Z', '+00:00'))
    require(result.tzinfo is not None, 'Evidence clocks require a timezone')
    return result


def validate(data):
    require(set(data) == {'schema','owner','observed_at','latest_release','status','source_sha256','audit_sha256',
        'invocations','tally','terminal_completed_at','failure','discovery_repair','preserved_bounded_acceptance',
        'cost','next_preparation','remaining_scientific_work','science_contract','publication'}, 'Unexpected latest-evidence fields')
    require(data['schema'] == 'sel.ncaa.public.latest_invocations.v1' and data['owner'] == 'NCAA basketball'
        and data['latest_release'] == 'R32' and data['status'] == 'FAILED_RESUMABLE', 'R32 remains a failed owner execution')
    require(not FORBIDDEN.search(json.dumps(data, allow_nan=False)), 'Private or other-owner content')
    require(data['source_sha256'] == '1f01f3abab9880ab25e6b2cce77b5001ff15255f7d286a59a595c8d2f6636605'
        and re.fullmatch('[0-9a-f]{64}', data['audit_sha256']), 'Actual R32 source and audit identity required')
    require(data['tally'] == {'successful_owner_executions':0,'failed_owner_executions':3,'distinct_run_ids':1,
        'new_scientific_fits':0,'new_stages_completed':0,'completed_stages_reused':0,'completed_stages_invalidated':0,
        'saved_acceptance_fits_preserved':36,'saved_acceptance_fits_refitted':0,'historical_checkpoints_preserved':108,
        'historical_checkpoints_reused_in_these_invocations':0,'all_audited_invocations':15,
        'all_audited_distinct_run_ids':11,'all_audited_completed_campaigns':0}, 'Invocation, preserved and fitted counts must remain separate')
    rows = data['invocations']
    require(len(rows) == 3 and [r['invocation'] for r in rows] == [1,2,3], 'Three distinct owner invocations are required')
    row_fields = {'invocation','started_at','summary_completed_at','elapsed_seconds','status','manifest_sha256',
        'return_sha256','return_bytes','payloads_verified','requested_cpus','peak_granted_cpus','peak_measured_owner_cores',
        'peak_scientific_workers','parent_cpu_seconds','completed_child_cpu_seconds','new_owner_fits',
        'new_stages_completed','completed_stages_reused','completed_stages_invalidated','saved_estimator_components_verified',
        'saved_files_verified','saved_component_verification_seconds','startup_cases_reused','startup_cases_executed',
        'estimated_instance_wall_cost_usd','cost_observation_seconds'}
    previous_end = None
    for i, row in enumerate(rows):
        require(set(row) == row_fields, 'Unknown invocation fields')
        require(row['manifest_sha256'] == MANIFESTS[i]
            and (row['return_sha256'],row['return_bytes'],row['payloads_verified']) == RETURNS[i], 'Exact independently verified return required')
        require(row['status'] == 'FAILED_PARTIAL_WORK_PRESERVED' and row['requested_cpus'] == 36
            and row['peak_granted_cpus'] == 1 and 0 < row['peak_measured_owner_cores'] < 1.01,
            'Configured CPUs do not establish scientific execution')
        require(all(row[k] == 0 for k in ('peak_scientific_workers','completed_child_cpu_seconds','new_owner_fits',
            'new_stages_completed','completed_stages_reused','completed_stages_invalidated','startup_cases_executed')),
            'R32 did not reach stage consumers or fitting')
        require(row['saved_estimator_components_verified'] == 36 and row['saved_files_verified'] == 144
            and row['startup_cases_reused'] == 1430, 'Saved models and startup receipts were reused without fitting')
        numeric = [v for v in row.values() if type(v) in (int,float)]
        require(all(math.isfinite(v) and v >= 0 for v in numeric), 'Measurements must be finite and nonnegative')
        start, end = aware(row['started_at']), aware(row['summary_completed_at'])
        require(start < end <= aware(data['observed_at']) and (previous_end is None or previous_end < start), 'Distinct ordered invocation clocks required')
        previous_end = end
        require(math.isclose(row['estimated_instance_wall_cost_usd'], row['cost_observation_seconds'] * 2.57 / 3600, abs_tol=1e-6), 'Cost interval and estimate do not reconcile')
    require(aware(rows[-1]['summary_completed_at']) < aware(data['terminal_completed_at']) <= aware(data['observed_at']), 'Final native status follows summary generation')
    failure = data['failure']
    require(set(failure) == {'recorded_error','phase','explanation','pointer_error','pointer_explanation'}
        and failure['recorded_error'] == 'B055_CURRENT_B054_TERMINAL_RETURN_FILE_REQUIRED'
        and failure['phase'] == 'BEFORE_FIRST_NUMBERED_STAGE'
        and failure['pointer_error'] == 'V13_POINTER_SOURCE_CONTEXT', 'Owner failure and discovery failure have different causes')
    repair = data['discovery_repair']
    require(repair == {'status':'VERIFIED_FAILED_RETURN_DISCOVERY_RECONCILED','latest_and_partial_point_to_latest_r32':True,
        'scientific_status':'FAILED_RESUMABLE','complete_pointer_written':False,'owner_runs_launched':0,
        'new_scientific_fits':0,'receipt_bytes':4153,
        'receipt_sha256':'14039b1e5c502faf4f44b2bb600bb72d824156f292550ce0789d5c1bd601dcc6'},
        'Pointer reconciliation preserves failed status and adds no science')
    prior = json.loads((HERE/'EXECUTION_STATUS_R31_20261118.json').read_text())
    acceptance = data['preserved_bounded_acceptance']
    require(acceptance == {k:prior['bounded_scientific_acceptance'][k] for k in acceptance}, 'Earlier scientific acceptance is unchanged')
    require(set(acceptance) == {'report_sha256','started_at','completed_at','new_physical_fits_completed',
        'verified_output_checkpoints','peak_real_estimator_kernel_overlap','peak_sampled_owner_core_equivalents',
        'kernel_average_core_equivalents','kernel_measurement_scope','sustained_180_second_75_percent_gate_certified',
        'overlap_of_24_or_36_real_estimator_kernels_observed'}, 'Acceptance evidence must retain its measurement limits')
    require(aware(acceptance['completed_at']) < aware(rows[0]['started_at']), 'Bounded acceptance preceded these owner failures')
    cost = data['cost']
    require(set(cost) == {'sum_recorded_instance_wall_estimates_usd','rate_usd_per_hour','invoice','exclusive_owner_allocation'}
        and cost['invoice'] is False and cost['exclusive_owner_allocation'] is False and cost['rate_usd_per_hour'] == 2.57
        and math.isclose(cost['sum_recorded_instance_wall_estimates_usd'],sum(r['estimated_instance_wall_cost_usd'] for r in rows),abs_tol=1e-9), 'Shared instance estimate is not an invoice')
    n = data['next_preparation']
    require(set(n) == {'release','status','owner_executions','new_scientific_fits','canonical_gate_passed','upload_verified',
        'canonical_source','native_acceptance','note'} and n['release'] == 'R33' and n['owner_executions'] == n['new_scientific_fits'] == 0,
        'R33 preparation has no owner or fit credit')
    require(n['status'] in ('IN_PROGRESS','PREPARED_VERIFIED'), 'Unknown preparation status')
    if n['status'] == 'IN_PROGRESS':
        require(n['canonical_gate_passed'] is False and n['upload_verified'] is False
            and n['canonical_source'] is None and n['native_acceptance'] is None, 'Pending preparation cannot inherit R32 success')
    else:
        p, a = n['canonical_source'], n['native_acceptance']
        require(n['canonical_gate_passed'] is True and n['upload_verified'] is True and isinstance(p,dict)
            and set(p) == {'bytes','sha256'} and type(p['bytes']) is int and p['bytes'] > 0
            and re.fullmatch('[0-9a-f]{64}',p['sha256']) and p['sha256'] != data['source_sha256'], 'R33 needs its own canonical source')
        require(isinstance(a,dict) and set(a) == {'report_sha256','first_fresh_process_passed','second_fresh_process_passed',
            'artifact_cache_scope','owner_dispatches','provider_requests','new_fits'}
            and re.fullmatch('[0-9a-f]{64}',a['report_sha256'])
            and a['first_fresh_process_passed'] is a['second_fresh_process_passed'] is True
            and a['artifact_cache_scope'] == 'EXISTING_DURABLE_CACHES_REUSED_IN_BOTH_PASSES'
            and a['owner_dispatches'] == a['provider_requests'] == a['new_fits'] == 0, 'Native boundary verification is distinct from an owner run')
    require(data['science_contract'] == prior['science_contract'], 'V13 science and exposure limits remain unchanged')
    publication = data['publication']
    require(set(publication) == {'source_state','deployment_verified','owner_runs','new_fits','new_forecasts','provider_requests','note'}
        and publication['source_state'] in ('PREPARED','COMMITTED') and publication['deployment_verified'] is False
        and all(publication[k] == 0 for k in ('owner_runs','new_fits','new_forecasts','provider_requests')), 'Public source edits do not run or deploy research')
    require(len(data['remaining_scientific_work']) == 5 and all(isinstance(x,str) and len(x) > 40 for x in data['remaining_scientific_work']), 'Unfinished science must remain visible')
    return deepcopy(data)


def load():
    return validate(json.loads(DATA.read_text()))


def canonical(data):
    return json.dumps(validate(data),indent=2,sort_keys=True)+'\n'


def render_panel(data=None):
    d = load() if data is None else validate(data)
    n = d['next_preparation']
    table = ''.join('<tr>'+''.join('<td>'+escape(str(value))+'</td>' for value in (
        r['invocation'],r['started_at'][11:26]+' UTC',r['summary_completed_at'][11:26]+' UTC',
        f"{r['elapsed_seconds']:.3f} s",r['peak_scientific_workers'],
        f"{r['saved_estimator_components_verified']} models / {r['saved_files_verified']} files",
        f"{r['saved_component_verification_seconds']:.3f} s"))+'</tr>' for r in d['invocations'])
    hashes = ''.join('<p>Invocation '+str(r['invocation'])+' · manifest <code>'+r['manifest_sha256']+
        '</code><br>Return <code>'+r['return_sha256']+'</code> · '+f"{r['return_bytes']:,} bytes / {r['payloads_verified']} verified payloads"+'</p>' for r in d['invocations'])
    download = base64.b64encode(canonical(d).encode()).decode()
    remaining = ''.join('<li>'+escape(item)+'</li>' for item in d['remaining_scientific_work'])
    release_proof = (('<p class="fine">Verified R33 canonical source: <code>'+n['canonical_source']['sha256']+
        '</code><br>Actual native startup-boundary acceptance: <code>'+n['native_acceptance']['report_sha256']+
        '</code>. Two fresh-process recovery checks passed using existing durable caches in both passes; neither is a cold-artifact-cache benchmark. Zero research dispatches, new fits or provider requests.</p>')
        if n['status'] == 'PREPARED_VERIFIED' else '')
    return f'''<section class="panel" id="latest-execution-panel" aria-labelledby="latest-execution-title">
<p class="eyebrow" style="margin-top:0">Latest actual owner execution · November 19 UTC / November 18 Pacific</p>
<h2 id="latest-execution-title">R32 failed three times before the first numbered stage</h2>
<p id="latest-evidence-scope">Three independently authenticated invocations share one run identity. Their start times and immutable return manifests distinguish them. All three failed; none reached a scientific fitting worker.</p>
<div class="cards"><article class="card"><div class="label">Successful / failed R32 executions</div><div class="value" id="latest-execution-tally">0 / 3</div><p>Three returns were preserved. A verified return is not a successful research campaign.</p></article>
<article class="card"><div class="label">New owner fits / numbered stages</div><div class="value" id="latest-new-work">0 / 0</div><p>Zero completed stages were reused or invalidated; launch stopped before the stage consumer.</p></article>
<article class="card"><div class="label">Previously fitted acceptance models</div><div class="value" id="latest-preserved-models">36</div><p>The same 144 files were verified on each invocation. Zero saved models were refitted.</p></article></div>
<div class="alert"><strong>36 CPUs requested; zero scientific workers ran.</strong><p id="latest-cpu-limit">Each owner performance ledger recorded one CPU granted and approximately one measured owner core. This is not evidence of 12–36-core scientific execution. The earlier bounded acceptance measured 21 overlapping estimator kernels; its 180-second, 75% sustained utilization gate remains uncertified.</p></div>
<div class="table-scroll" tabindex="0" aria-label="R32 invocation evidence table"><table><caption>Actual R32 invocations · all failed before stage one</caption><thead><tr><th>Invocation</th><th>Start on Nov 19</th><th>Summary completed</th><th>Reported elapsed</th><th>Fitting workers</th><th>Saved outputs verified</th><th>Saved-output verification</th></tr></thead><tbody id="latest-invocation-rows">{table}</tbody></table></div>
<p class="fine">Final native status for invocation 3 was recorded at 01:47:58.935075 UTC, after summary generation. The three reported elapsed intervals total 381.504 seconds. Their summed shared-instance wall estimate is $0.267927; it is not an invoice or an exclusive NCAA allocation.</p>
<div class="split"><article><h3>Why the owner stopped</h3><p>{escape(d['failure']['explanation'])}</p><p><code>{escape(d['failure']['recorded_error'])}</code></p><p>The 108 historical estimator checkpoints remain preserved in earlier authenticated artifacts. These invocations did not reach their consumer, so current-invocation historical reuse remains zero. The same 1,430 qualified startup cases were reused; they had not exercised the missing native integration boundary.</p></article>
<article><h3>The stale discovery pointer is repaired</h3><p>{escape(d['failure']['pointer_explanation'])}</p><p id="latest-pointer-repair">The latest and partial indexes now identify the newest R32 failed-resumable return. The complete-return pointer was untouched. Repair launched zero owner campaigns, fits or provider requests.</p><p class="fine">Native reconciliation receipt: <code>{d['discovery_repair']['receipt_sha256']}</code></p></article></div>
<h3 id="latest-preparation-state">{escape(n['release'])} · {escape(n['status'])} · 0 owner executions</h3><p id="latest-preparation-note">{escape(n['note'])}</p>{release_proof}
<h3>Research still unfinished</h3><ol>{remaining}</ol>
<p id="latest-scientific-limit">Men and women keep separate evaluations and registries. Validation remains 2024–25 and 2025–26; 2026–27 has zero selection weight and prior test exposure remains disclosed. There is no new full-population champion or completed campaign.</p>
<p><a id="download-latest-execution" class="button" download="ncaa-latest-execution.json" href="data:application/json;base64,{download}">Download latest invocation evidence</a> · <a href="EXECUTION_RECOVERY_REVIEW_R32_20261119.md">Read the R32 failure review →</a></p>
<details><summary>Exact return and invocation evidence</summary><div class="hashes">{hashes}<p>Three-invocation audit <code>{d['audit_sha256']}</code></p></div></details>
<p class="fine">{escape(d['publication']['note'])} No website deployment is claimed.</p></section>'''


def render_banner(data=None):
    d = load() if data is None else validate(data)
    n = d['next_preparation']
    state = 'preparation is in progress' if n['status'] == 'IN_PROGRESS' else 'canonical preparation and native recovery verification are complete; owner execution remains pending'
    return ('<section id="v12-current-evidence" aria-labelledby="v12-current-title" class="b063-notice" '
        'style="margin-bottom:28px;padding:20px;border:1px solid #ddc49b;border-radius:12px;background:#fff2db">'
        '<p class="b063-eyebrow" style="margin-top:0">Latest actual NCAA execution · R32 · November 18, 2026 Pacific</p>'
        '<h2 id="v12-current-title">Three R32 failures; saved models remain preserved</h2>'
        '<p>The latest observed R32 invocation has a verified partial return with 116 payloads. All three actual '
        'R32 invocations failed before stage one, with zero new owner fits and zero fitting workers. Their shared '
        'run identity does not make them one invocation. Latest-return discovery is now repaired.</p>'
        '<p>The earlier bounded acceptance completed 36 real new estimator components and 21 overlapping estimator kernels. '
        'Those saved components were verified without refitting. Full research and the 180-second, 75% gate remain incomplete. '
        'R33 '+state+'.</p><p><strong><a href="execution.html">Inspect the latest failures and preserved work →</a></strong> · '
        '<a href="three_seasons.html">Preserved three-season comparison</a> · <a href="v12.html">Preserved V12 comparison</a></p></section>')
