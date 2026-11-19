"""Sanitized R33 execution evidence above the preserved historical review.

Source tasks, stage reuse, prior fitted artifacts, actual optimizer entry and
publication status retain separate counters. No private artifacts are exposed.
"""
from copy import deepcopy
from html import escape
from pathlib import Path
import base64
import json
import math
import re

from execution_latest_r32 import aware, require, FORBIDDEN, load as load_r32

HERE = Path(__file__).resolve().parent
DATA = HERE / 'EXECUTION_STATUS_R33_20261119.json'
SOURCE_SHA = '8a5b9f7377e69f9a3d0367732693da7e20a41142f0f8fb8f381c9153d3a3cdd3'
RETURN_SHA = '4376b0dc9915207e0623147a4db128a12dca2d71f2ac52110bbe8443924d08b0'


def validate(data):
    expected = {'schema','owner','observed_at','latest_release','status','source_sha256','audit_sha256',
        'execution','failure','tally','source_progress','cpu','cost','preserved_bounded_acceptance',
        'current_bounded_acceptance','next_preparation','remaining_scientific_work','science_contract','publication'}
    require(set(data) == expected, 'Unexpected latest execution fields')
    require(data['schema'] == 'sel.ncaa.public.latest_execution.v2' and data['owner'] == 'NCAA basketball'
        and data['latest_release'] == 'R33' and data['status'] == 'FAILED_AUTOMATIC_INTERRUPTION_RESUMABLE',
        'R33 remains an unsuccessful automatic interruption with preserved work')
    require(not FORBIDDEN.search(json.dumps(data,allow_nan=False)), 'Private or other-owner content')
    require(data['source_sha256'] == SOURCE_SHA and re.fullmatch('[0-9a-f]{64}',data['audit_sha256']),
        'Actual owner source and reconciliation identity required')
    run = data['execution']
    require(set(run) == {'started_at','summary_completed_at','return_verified_at','elapsed_seconds',
        'source_stage_seconds','recorded_terminal_status','scientific_completeness','return_sha256',
        'return_bytes','payloads_verified'}, 'Unexpected execution fields')
    require(run['recorded_terminal_status'] == 'INTERRUPTED_RESUMABLE' and run['scientific_completeness'] == 'PARTIAL'
        and (run['return_sha256'],run['return_bytes'],run['payloads_verified']) == (RETURN_SHA,47016491,553),
        'Verified partial return cannot become a completed campaign')
    require(aware(run['started_at']) < aware(run['summary_completed_at']) < aware(run['return_verified_at'])
        <= aware(data['observed_at']), 'Distinct execution, summary and verification clocks required')
    require(math.isclose(run['elapsed_seconds'],3126.3261266629997,abs_tol=1e-6)
        and math.isclose(run['source_stage_seconds'],2683.134944905003,abs_tol=1e-6), 'Recorded run timing changed')
    failure = data['failure']
    require(set(failure) == {'phase','root_cause','first_error','automatic_stop_reason','user_requested_stop','explanation'}
        and failure['phase'] == '04b_incremental_model_source_refresh'
        and failure['root_cause'] == 'HEARTBEAT_EXCEEDED_LIVE_EVENT_SIZE_BOUND'
        and failure['first_error'] == 'B068_EVENT_SIZE_BOUND'
        and failure['automatic_stop_reason'] == 'LIVE_EXECUTION_OBSERVATION_FAILED'
        and failure['user_requested_stop'] is False, 'Internal observation failure cannot become a user stop or provider denial')
    expected_tally = {'owner_invocations':1,'successful_complete_owner_campaigns':0,'unsuccessful_due_to_execution_defect':1,
        'failed_terminal_status_invocations':0,'interrupted_resumable_invocations':1,'new_scientific_fits':0,
        'new_calibration_fits':0,'historical_estimator_fits_reused':108,'saved_prior_acceptance_models_verified_without_refitting':36,
        'prior_worker_results_republished_without_optimizer':2,'reused_completed_stages':3,'new_stage_completions':1,
        'invalidated_stages':0,'unfinished_stage_nodes':17,'stage_graph_nodes':21}
    require(data['tally'] == expected_tally, 'Reuse, physical publication and actual fitting must remain separate')
    source = data['source_progress']
    require(set(source) == {'scoreboard','box','normalized_request_tasks','completed_normalized_market_snapshots',
        'outcome_rows','quote_rows','additional_partial_snapshot','full_source_coverage_certified','source_tasks_are_scientific_fits',
        'cache_receipt_verification','note'},
        'Unexpected source-progress fields')
    require(source['scoreboard'] == {'completed':23,'reused':9,'total':32}
        and source['box'] == {'completed':130,'reused':0,'total':130}
        and source['normalized_request_tasks'] == {'completed':153,'reused':9,'pending':0,'total':162}
        and source['completed_normalized_market_snapshots'] == 209 and source['additional_partial_snapshot'] == 1
        and source['outcome_rows'] == 1873609 and source['quote_rows'] == 490484
        and source['full_source_coverage_certified'] is source['source_tasks_are_scientific_fits'] is False,
        'Completed scoreboard tasks and market snapshots cannot certify full source coverage or fits')
    cache = source['cache_receipt_verification']
    require(cache == {'report_sha256':'9303f5c62ff15f431bc81a65ea46f2642817d2a7186304bdcf9631655fe64a3c',
        'HTTP_200_receipts':508,'HTTP_422_alias_receipts':254,'distinct_successful_snapshot_ids':508,
        'successful_snapshot_ids_without_normalized_completion':299,'normalized_completion_receipts_verified':209,
        'source_task_completion_receipts_verified':162,'physical_artifact_refs_verified':3231,
        'elapsed_seconds':53.803300108003896,'owner_executions':0,'provider_requests':0,'new_fits':0,
        'logical_row_closure_revalidated':False,'full_source_coverage_certified':False},
        'Read-only receipt authentication cannot become provider retrieval, new source coverage or scientific progress')
    cpu = data['cpu']
    require(set(cpu) == {'requested_ceiling','peak_granted_cpus','peak_actual_scientific_workers','mean_owner_core_equivalents',
        'peak_actual_process_tree_cores','owner_cpu_seconds_total','owner_cpu_measurement_wall_seconds',
        'scientific_utilization_12_to36_proven'}, 'Unexpected CPU evidence fields')
    require(cpu['requested_ceiling'] == 36 and cpu['peak_granted_cpus'] == 12
        and cpu['peak_actual_scientific_workers'] == 0 and cpu['scientific_utilization_12_to36_proven'] is False,
        'Requested or granted slots do not establish scientific worker execution')
    require(math.isclose(cpu['owner_cpu_seconds_total'],2763.066514,abs_tol=1e-6)
        and math.isclose(cpu['owner_cpu_measurement_wall_seconds'],3124.3205335279927,abs_tol=1e-6)
        and math.isclose(cpu['mean_owner_core_equivalents'],cpu['owner_cpu_seconds_total']/cpu['owner_cpu_measurement_wall_seconds'],abs_tol=1e-9)
        and math.isclose(cpu['peak_actual_process_tree_cores'],1.0850666915046974,abs_tol=1e-9),
        'Actual process CPU time and measured wall interval must reconcile')
    cost = data['cost']
    require(set(cost) == {'estimated_whole_instance_invocation_usd','rate_usd_per_hour','invoice',
        'exclusive_owner_allocation','default_guard_usd','guard_triggered'}
        and math.isclose(cost['estimated_whole_instance_invocation_usd'],2.2304176828818876,abs_tol=1e-9)
        and cost['rate_usd_per_hour'] == 2.57 and cost['default_guard_usd'] == 200
        and cost['invoice'] is cost['exclusive_owner_allocation'] is cost['guard_triggered'] is False,
        'Shared-instance estimate is not an invoice, exclusive cost or triggered guard')
    previous = load_r32()
    require(data['preserved_bounded_acceptance'] == previous['preserved_bounded_acceptance'],
        'Earlier bounded acceptance cannot gain new run or sustained-CPU credit')
    require(data['science_contract'] == previous['science_contract'], 'Gender, denominator, validation and test-exposure rules remain unchanged')
    bounded = data['current_bounded_acceptance']
    require(set(bounded) == {'release','status','owner_runs','new_physical_fits_completed','verified_completed_tasks',
        'remaining_candidate_tasks','old_completed_units_refitted','family_counts','peak_real_scientific_worker_overlap',
        'registered_kernel_cpu_seconds','registered_kernel_measurement_span_seconds','average_registered_kernel_core_equivalents',
        'kernel_measurement_scope','elapsed_seconds','estimated_whole_instance_cost_usd','cost_is_invoice','gate_status','gate_reason',
        'gate_measurement_seconds','gate_eligible_seconds','utilization_of_safely_admitted_cpu_budget',
        'sustained_180_second_75_percent_gate_certified','configured_cores_are_acceptance_evidence','provider_requests',
        'test_rows_used','champion_promotions','full_owner_campaign_complete','note'}, 'Unexpected bounded acceptance fields')
    require(bounded['release']=='R34' and bounded['status']=='COMPLETED_FINITE_ACCEPTANCE_CATALOG'
        and bounded['new_physical_fits_completed']==bounded['verified_completed_tasks']==48
        and all(bounded[k]==0 for k in ('owner_runs','remaining_candidate_tasks','old_completed_units_refitted','provider_requests','test_rows_used','champion_promotions'))
        and bounded['family_counts']=={'lightgbm':12,'catboost':12,'pytorch':12,'tensorflow':12}
        and bounded['peak_real_scientific_worker_overlap']==28, 'Actual bounded fitting must remain distinct from owner execution and reused models')
    measured={'registered_kernel_cpu_seconds':1831.132163734,'registered_kernel_measurement_span_seconds':207.9220357479935,
        'average_registered_kernel_core_equivalents':8.806821062262857,'elapsed_seconds':221.91351419400598,
        'estimated_whole_instance_cost_usd':0.1584215920773876,'gate_measurement_seconds':182.02926496000146,
        'gate_eligible_seconds':95.13657032398623,'utilization_of_safely_admitted_cpu_budget':0.8669806349264785}
    require(all(math.isclose(bounded[k],v,rel_tol=0,abs_tol=1e-9) for k,v in measured.items())
        and bounded['kernel_measurement_scope']=='UNCHANGED_REGISTERED_KERNEL_WITH_PREPROCESSING_INFERENCE_AND_LOCAL_PERSISTENCE',
        'Kernel CPU must retain its measured span and preprocessing/inference/persistence scope')
    require(bounded['gate_status']=='CONDITIONAL_SHARED_HOST_DRAINING_ACTIVE_FITS'
        and bounded['gate_reason']=='REGISTERED_FITS_PRESERVED_WHILE_CURRENT_HOST_HEADROOM_PREVENTS_NEW_TARGET_ADMISSION'
        and bounded['sustained_180_second_75_percent_gate_certified'] is bounded['configured_cores_are_acceptance_evidence']
        is bounded['full_owner_campaign_complete'] is bounded['cost_is_invoice'] is False,
        'Finite completion, worker overlap and eligible-window utilization cannot certify sustained full capacity')
    next_run = data['next_preparation']
    require(set(next_run) == {'release','status','owner_executions','new_scientific_fits','canonical_gate_passed',
        'upload_verified','canonical_source','installation_receipt_sha256','native_engineering','native_acceptance','note'} and next_run['release'] == 'R34'
        and next_run['owner_executions'] == 0 and next_run['new_scientific_fits']==bounded['new_physical_fits_completed'],
        'R34 bounded preparation fits are separate from owner runs')
    require(next_run['status'] in ('IN_PROGRESS','PREPARED_VERIFIED'), 'Unknown R34 preparation status')
    engineering=next_run['native_engineering']
    require(isinstance(engineering,dict) and set(engineering)=={'status','source','report_sha256','tests_run','failures','errors','skips','owner_runs','new_scientific_fits'}
        and engineering['status']=='PASSED' and engineering['tests_run']==1572
        and engineering['source']=={'bytes':63101302,'sha256':'861328bebd71ab13817acbaac081ea24af6e92c54a8216b1ac994c800b045ad8'}
        and engineering['report_sha256']=='8e851d9c749f7ec35163bd841cbcf70708ddbb234ceba314e6fb95c1763ffd71'
        and all(type(engineering[k]) is int and engineering[k]==0 for k in ('failures','errors','skips','owner_runs','new_scientific_fits')),
        'Native engineering must retain its exact source, report and zero scientific credit')
    if next_run['status'] == 'IN_PROGRESS':
        require(next_run['canonical_gate_passed'] is next_run['upload_verified'] is False
            and next_run['canonical_source'] is next_run['native_acceptance'] is next_run['installation_receipt_sha256'] is None,
            'Pending R34 must not claim installation or a final recovery gate')
    else:
        source, acceptance = next_run['canonical_source'], next_run['native_acceptance']
        require(next_run['canonical_gate_passed'] is next_run['upload_verified'] is True
            and isinstance(source,dict) and set(source) == {'bytes','sha256'}
            and type(source['bytes']) is int and source['bytes'] > 0
            and re.fullmatch('[0-9a-f]{64}',source['sha256']) and source['sha256'] != SOURCE_SHA
            and source==engineering['source'],
            'A verified R34 preparation needs its own source and installation evidence')
        require(isinstance(next_run['installation_receipt_sha256'],str)
            and re.fullmatch('[0-9a-f]{64}',next_run['installation_receipt_sha256']),
            'A verified installation needs its exact evidence digest')
        require(isinstance(acceptance,dict) and set(acceptance) == {'report_sha256','owner_dispatches','provider_requests','new_fits'}
            and re.fullmatch('[0-9a-f]{64}',acceptance['report_sha256'])
            and acceptance['owner_dispatches'] == acceptance['provider_requests'] == acceptance['new_fits'] == 0,
            'Final native recovery is separate from bounded scientific acceptance')
    require(len(data['remaining_scientific_work']) == 5
        and all(isinstance(v,str) and len(v)>40 for v in data['remaining_scientific_work']), 'Unfinished science remains visible')
    publication = data['publication']
    require(set(publication) == {'source_state','deployment_verified','owner_runs','new_fits','new_forecasts','provider_requests','note'}
        and publication['source_state'] in ('PREPARED','COMMITTED') and publication['deployment_verified'] is False
        and all(publication[k] == 0 for k in ('owner_runs','new_fits','new_forecasts','provider_requests')),
        'Dashboard work does not execute, fit, refresh or deploy owner science')
    return deepcopy(data)


def load():
    return validate(json.loads(DATA.read_text()))


def canonical(data):
    return json.dumps(validate(data),indent=2,sort_keys=True,allow_nan=False)+'\n'


def render_panel(data=None):
    d = load() if data is None else validate(data)
    run, t, source, cpu, n = (d[k] for k in ('execution','tally','source_progress','cpu','next_preparation'))
    bounded = d['current_bounded_acceptance']
    download = base64.b64encode(canonical(d).encode()).decode()
    remaining = ''.join('<li>'+escape(item)+'</li>' for item in d['remaining_scientific_work'])
    rows = ''.join('<tr>'+''.join('<td>'+escape(str(v))+'</td>' for v in row)+'</tr>' for row in (
        ('Scoreboard requests',23,9,'32 / 32','Source outputs; not fits'),
        ('Box requests',130,0,'130 / 130','Source outputs; not fits'),
        ('Market snapshots',209,'Separately tracked','1 additional partial','Full population incomplete'),
    ))
    proof = ('<p class="fine">Verified R34 source: <code>'+n['canonical_source']['sha256']+
        '</code><br>Authentic startup recovery: <code>'+n['native_acceptance']['report_sha256']+
        '</code><br>Verified installation: <code>'+n['installation_receipt_sha256']+'</code>. Owner execution remains pending.</p>') if n['status']=='PREPARED_VERIFIED' else ''
    engineering=n['native_engineering']
    engineering_proof=('<p id="r34-native-engineering">The final R34 executable passed '+format(engineering['tests_run'],',')+
        ' native engineering tests with zero failures, errors or skips. This gate launched zero owner executions and completed zero scientific fits.</p>'+
        '<details><summary>Exact native engineering evidence</summary><p>Source <code>'+engineering['source']['sha256']+
        '</code><br>Regression report <code>'+engineering['report_sha256']+'</code></p></details>')
    return f'''<section class="panel" id="latest-execution-panel" aria-labelledby="latest-execution-title">
<p class="eyebrow" style="margin-top:0">Latest actual owner execution · R33 · November 19 UTC / November 18 Pacific</p>
<h2 id="latest-execution-title">R33 stopped automatically before fitting</h2>
<p id="latest-evidence-scope">The owner preserved useful source work and reused completed stages, then failed to finish because its live heartbeat exceeded a logging limit. The recorded terminal status is <code>INTERRUPTED_RESUMABLE</code>; this was an internal execution defect, not a requested user stop.</p>
<div class="cards"><article class="card"><div class="label">Successful / unsuccessful R33 executions</div><div class="value" id="latest-execution-tally">0 / 1</div><p>One automatic resumable interruption. All 553 return payloads verified; scientific completeness remains partial.</p></article>
<article class="card"><div class="label">New fits / new completed stages</div><div class="value" id="latest-new-work">0 / 1</div><p>Three earlier stages were reused, zero were invalidated, and 17 of 21 stage nodes remain unfinished.</p></article>
<article class="card"><div class="label">Historical fitted checkpoints reused</div><div class="value" id="latest-preserved-models">108</div><p>Another 36 prior acceptance models were verified without refitting. Two old worker results were republished; neither is a new optimizer fit.</p></article></div>
<div class="alert"><strong>0 fitting workers; mean owner CPU use was {cpu['mean_owner_core_equivalents']:.3f} cores.</strong><p id="latest-cpu-limit">36 CPUs were requested and 12 slots were granted at peak. Measured process-tree use peaked at {cpu['peak_actual_process_tree_cores']:.3f} cores. The owner used {cpu['owner_cpu_seconds_total']:,.3f} CPU seconds over a {cpu['owner_cpu_measurement_wall_seconds']:,.3f}-second measurement interval. These source and recovery measurements do not establish 12–36-core fitting or pass the conditional 180-second, 75% scientific utilization gate.</p></div>
<h3>Source progress is preserved separately from fitting</h3>
<div class="table-scroll" tabindex="0" aria-label="R33 source work table"><table><caption>Durable source work · zero scientific fits</caption><thead><tr><th>Workstream</th><th>Completed</th><th>Reused</th><th>Progress</th><th>Meaning</th></tr></thead><tbody id="latest-source-rows">{rows}</tbody></table></div>
<p id="latest-source-scope">{escape(source['note'])} The completed market snapshots contain 1,873,609 normalized outcome rows and 490,484 quote rows. They are neither game forecasts nor estimator completions.</p>
<p id="latest-cache-verification">A separate read-only recovery audit authenticated 508 distinct successful historical responses and all 209 completed snapshot receipts; 299 successful cached snapshots still lack completed normalization. It preserved 254 additional HTTP 422 aliases as unsuccessful receipts. The 53.803-second audit verified 3,231 physical artifact references and launched zero owners, provider requests or fits. Physical integrity does not certify full source coverage.</p>
<div class="split"><article><h3>Why this execution stopped</h3><p>{escape(d['failure']['explanation'])}</p><p><code>B068_EVENT_SIZE_BOUND</code> → <code>LIVE_EXECUTION_OBSERVATION_FAILED</code></p></article>
<article><h3>Verified reuse and remaining work</h3><p id="latest-reuse-state">Three stages were marked <code>SKIPPED_VERIFIED</code>. One source-refresh stage completed. The interrupted stage has 153 completed and nine reused scoreboard/box tasks; its market work still requires continuation. Reused work is not new fitting.</p><p>R33 ran for {run['elapsed_seconds']/60:.3f} reported minutes, including {run['source_stage_seconds']/60:.3f} minutes in the interrupted source stage. The recorded shared-instance wall estimate was ${d['cost']['estimated_whole_instance_invocation_usd']:.6f}; it is not an invoice or an exclusive NCAA allocation. The $200 guard was not reached.</p></article></div>
<h3 id="latest-preparation-state">{escape(n['release'])} · {escape(n['status'])} · 0 owner executions</h3><p id="latest-preparation-note">{escape(n['note'])}</p>{engineering_proof}{proof}
<h3>R34 bounded validation work completed</h3>
<div class="cards"><article class="card"><div class="label">New bounded scientific fits</div><div class="value" id="r34-bounded-new-fits">48 / 48</div><p>Twelve fits each for LightGBM, CatBoost, PyTorch and TensorFlow. Zero completed candidates were refitted; both men's and women's validation work is retained.</p></article>
<article class="card"><div class="label">Peak actual scientific worker overlap</div><div class="value" id="r34-bounded-worker-overlap">28</div><p>Measured from original scientific worker and kernel receipts. This is observed overlap, not a configured worker ceiling.</p></article>
<article class="card"><div class="label">Full NCAA owner executions</div><div class="value">0</div><p>The finite acceptance catalog is complete. The full research campaign and champion selection remain unfinished.</p></article></div>
<p id="r34-bounded-cpu">Registered model kernels consumed {bounded['registered_kernel_cpu_seconds']:,.3f} CPU seconds over a {bounded['registered_kernel_measurement_span_seconds']:.3f}-second kernel span, averaging {bounded['average_registered_kernel_core_equivalents']:.3f} cores. These intervals include preprocessing, fitting, inference and local persistence. Total bounded execution took {bounded['elapsed_seconds']:.3f} seconds; its whole-instance estimate was ${bounded['estimated_whole_instance_cost_usd']:.6f}, not an invoice.</p>
<div class="alert"><strong id="r34-bounded-capacity-limit">The sustained 180-second capacity gate is not certified.</strong><p>Only {bounded['gate_eligible_seconds']:.3f} of {bounded['gate_measurement_seconds']:.3f} measured seconds were eligible as shared-host capacity changed and the finite queue drained. Measured use of the safely admitted CPU budget was {bounded['utilization_of_safely_admitted_cpu_budget']:.1%}; that does not satisfy the missing eligible-duration requirement. Completed fitting work remains preserved.</p></div>
<h3>Research still unfinished</h3><ol>{remaining}</ol>
<p id="latest-scientific-limit">Men and women keep separate evaluations and champion registries. Validation remains 2024–25 and 2025–26; 2026–27 has zero selection weight and prior test exposure remains disclosed. No new full-population champion or completed campaign is claimed. The earlier bounded acceptance retains its 36 saved fits and measured 21-kernel overlap; it is not R33 throughput.</p>
<p><a id="download-latest-execution" class="button" download="ncaa-latest-execution.json" href="data:application/json;base64,{download}">Download latest execution evidence</a> · <a href="EXECUTION_RECOVERY_REVIEW_R33_20261119.md">Read the R33 failure review →</a> · <a href="EXECUTION_RECOVERY_REVIEW_R32_20261119.md">Earlier R32 failure review</a></p>
<details><summary>Exact return and execution evidence</summary><div class="hashes"><p>Return <code>{run['return_sha256']}</code> · {run['return_bytes']:,} bytes / {run['payloads_verified']} verified payloads<br>Reconciliation <code>{d['audit_sha256']}</code></p><p>Started {escape(run['started_at'])}<br>Summary completed {escape(run['summary_completed_at'])}<br>Return verified {escape(run['return_verified_at'])}</p></div></details>
<p class="fine">{escape(d['publication']['note'])} No website deployment is claimed.</p></section>'''


def render_banner(data=None):
    d = load() if data is None else validate(data)
    n = d['next_preparation']
    pending = 'R34 preparation is in progress; no verified installation or owner execution is claimed.' if n['status']=='IN_PROGRESS' else 'R34 preparation and installation are verified; owner execution remains pending.'
    return ('<section id="v12-current-evidence" aria-labelledby="v12-current-title" class="b063-notice" '
        'style="margin-bottom:28px;padding:20px;border:1px solid #ddc49b;border-radius:12px;background:#fff2db">'
        '<p class="b063-eyebrow" style="margin-top:0">Latest actual NCAA execution · R33 · November 18, 2026 Pacific</p>'
        '<h2 id="v12-current-title">R33 preserved source progress, then stopped before fitting</h2>'
        '<p>The latest verified partial return contains 553 payloads. An oversized heartbeat caused an automatic internal stop. '
        'The owner reused three completed stages and 108 historical fitted checkpoints, completed one new stage, '
        'and preserved all 32 scoreboard tasks, 130 box tasks and 209 normalized market snapshots. Market work remains incomplete.</p>'
        '<p>There were zero new fits and zero fitting workers. Actual mean owner CPU use was 0.884 cores; requesting 36 CPUs '
        'and granting 12 slots did not establish scientific parallelism. '+escape(pending)+
        '</p><p>A separate R34 bounded validation acceptance has since completed 48 new fits with 28 observed overlapping scientific workers and zero refits. The full owner campaign has not run, and the sustained 180-second capacity gate remains conditional.'+
        '</p><p><strong><a href="execution.html">Inspect the R33 failure and preserved work →</a></strong> · '
        '<a href="three_seasons.html">Preserved three-season comparison</a> · <a href="v12.html">Preserved V12 comparison</a></p></section>')
