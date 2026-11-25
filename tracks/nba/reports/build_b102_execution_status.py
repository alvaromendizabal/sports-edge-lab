#!/usr/bin/env python3
"""Render a dated NBA failure/recovery audit from sanitized aggregate evidence.

No provider request, model fitting, private artifact access or deployment occurs.
"""
from __future__ import annotations
import argparse
import base64
import copy
import html
import json
import math
from pathlib import Path
import re

HERE=Path(__file__).resolve().parent
SOURCE=HERE/'b102_execution_status.json'
OUTPUT=HERE/'b102_execution_status.html'


def validate(data):
    if set(data)!={'schema','owner','evidence_through_utc','engineering_observed_at_utc','overall_scientific_status',
            'full_v13_complete','automatic_promotions','b101_failure','preserved_work','b102_projection_v1',
            'b102_projection_v2','retained_comparison_population','population_qualification','publication','evidence'}:
        raise ValueError('Only the dated public aggregate fields are allowed')
    if (data['schema']!='sel.nba.public_execution_status.b102.v1' or data['owner']!='NBA'
            or data['overall_scientific_status']!='PARTIAL_RESUMABLE' or data['full_v13_complete']
            or data['automatic_promotions']!=0):
        raise ValueError('Cache recovery cannot complete the V13 scientific program')
    failure=data['b101_failure']
    expected={'status':'FAILED','exit_code':2,'projection_tasks':5808,'completed_projection_tasks':2374,
        'deferred_projection_tasks':3434,'individual_projection_failures':0,
        'new_estimator_fits':0,'new_calibration_fits':0,'new_meta_model_fits':0,'new_residual_distribution_fits':0,
        'requested_worker_ceiling':24,'admitted_projection_workers':1,'productive_progress_observed':True,
        'earlier_input_failure':'DECODED_HISTORY_EXCEEDED_64_MIB_IPC_BOUND',
        'projection_admission_cause':'GLOBAL_IO_PSI_UNCONDITIONAL_SINGLE_WORKER_LIMIT',
        'projection_stop_cause':'SCIENTIFIC_OCCUPANCY_GATE_APPLIED_TO_PRODUCTIVE_PRESENTATION_WORK'}
    if any(failure.get(k)!=v for k,v in expected.items()):
        raise ValueError('Retain the actual failed attempt, counts and causal findings')
    if (not math.isclose(failure['measured_cpu_seconds'],60.436192,abs_tol=1e-8)
            or not math.isclose(failure['representative_interval_seconds'],180.84465288,abs_tol=1e-8)
            or not math.isclose(failure['occupancy'],failure['measured_cpu_seconds']/failure['representative_interval_seconds'],abs_tol=1e-10)):
        raise ValueError('CPU measurement must retain its actual one-core denominator')
    prior=data['preserved_work']
    if prior!={'b100_residual_distribution_fits':320,'b101_original_states_verified':320,
        'b101_missing_states_restored':0,'b101_hydration_model_applications_verified':False,
        'historical_point_variants':5808,'new_fit_credit_from_restoration':0}:
        raise ValueError('Verified saved states are not newly restored or applied models')
    actual=data['b102_projection_v1']
    exact={'status':'COMPLETE','native_owner_workload_observed':True,'full_research_run_launched':False,
        'model_variants':5808,'completed_projection_tasks':5808,'new_projections_created':0,
        'verified_warm_reuses':5808,'failed_tasks':0,'deferred_tasks':0,'declared_games_each':1200,
        'completed_test_games':210,'upcoming_games':990,'verified_records':6969600,'missing_records':0,
        'null_predictions':0,'missing_outputs':0,'durably_verified_projection_count':5808,
        'requested_worker_ceiling':24,'peak_physical_workers':24,'measured_overlapping_projection_tasks':21,
        'distinct_completed_worker_pids':29,'native_independent_logging_seconds':10,
        'scientific_occupancy_pass_claimed':False,'new_estimator_fits':0,'new_calibration_fits':0,
        'new_residual_distribution_fits':0,'new_forecast_values':0,'provider_data_requests':0,
        'actual_billed_cost_usd':None,'nba_allocated_cost_usd':None,
        'remaining_bottleneck':'PUBLICATION_BACKLOG_STARVED_VERIFICATION_QUEUE'}
    if any(actual.get(k)!=v for k,v in exact.items()):
        raise ValueError('Preserve actual projection, population and scientific accounting')
    if (not math.isclose(actual['stage_wall_seconds'],144.7571951750004,abs_tol=.01)
            or not 168<actual['completed_task_cpu_seconds']<169
            or not math.isclose(actual['task_cpu_per_stage_wall_second'],
                actual['completed_task_cpu_seconds']/actual['stage_wall_seconds'],abs_tol=1e-9)
            or not math.isclose(actual['whole_instance_wall_interval_estimate_usd'],.10974343368618558,abs_tol=1e-12)):
        raise ValueError('Measured task CPU and wall estimate are not worker peaks or invoices')
    next_run=data['b102_projection_v2']
    if next_run!={'status':'ENGINEERING_TESTED_OWNER_CHECK_PENDING_AT_THIS_EVIDENCE_CUTOFF',
        'targeted_engineering_tests_passed':22,'targeted_engineering_tests_failed':0,
        'verification_and_publication_queues_independent':True,'completed_checkpoint_reference_reuse':True,
        'historical_remote_proofs_relabeled_as_current':False,'scientific_worker_hard_ceiling_preserved':True,
        'productive_work_fixed_wall_timeout':False,'unchanged_cpu_acceptance_percent':75,
        'unchanged_cpu_acceptance_interval_seconds':180,'new_owner_model_fits_claimed':0}:
        raise ValueError('Engineering tests are separate from owner execution and CPU acceptance')
    if data['retained_comparison_population']!=[
        {'season':'2024-25','completed_games':1314,'purpose':'VALIDATION'},
        {'season':'2025-26','completed_games':1315,'purpose':'VALIDATION'},
        {'season':'2026-27','completed_games':210,'purpose':'PREVIOUSLY_EXPOSED_TEST'}]:
        raise ValueError('Preserve identical retained annual populations and test exposure')
    if data['population_qualification']!={'known_validation_omissions':14,'full_independent_census_verified':False,
        'expanded_population_rescored':False,'test_used_for_selection':False,
        'evaluation_weights_change_training_rows':False,'primary_validation_weight':'50/50'}:
        raise ValueError('A missing census cannot be repaired by relabeling scores')
    if data['publication']!={'source_scope':'NBA_SANITIZED_AGGREGATES_ONLY','draft_review':True,
        'merged':False,'deployed':False,'private_models_or_cloud_paths_published':False,'new_scientific_score_claimed':False}:
        raise ValueError('Draft source, deployment and scientific selection remain separate')
    if len(data['evidence'])!=7 or any(set(row)!={'label','bytes','sha256'} or type(row['bytes']) is not int
        or row['bytes']<1 or not re.fullmatch('[0-9a-f]{64}',row['sha256']) for row in data['evidence']):
        raise ValueError('Every source needs a sanitized content hash and byte count')
    serialized=json.dumps(data)
    if re.search(r'/home/|s3://|arn:aws:|sagemaker-sports|tracks/nba/checkpoints|api[_-]?key|secret|password|\.pyz\b',serialized,re.I):
        raise ValueError('Private storage, packages or credentials cannot enter the public snapshot')
    return data


def render(data):
    d=validate(data);a=d['b102_projection_v1'];f=d['b101_failure'];e=html.escape
    raw=json.dumps(d,indent=2)+'\n'
    download='data:application/json;base64,'+base64.b64encode(raw.encode()).decode()
    evidence=''.join('<li><strong>'+e(r['label'])+'</strong><span>'+format(r['bytes'],',')+' bytes</span><code>'+r['sha256']+'</code></li>' for r in d['evidence'])
    populations=''.join('<div class="population"><strong>'+e(r['season'])+'</strong><span>'+format(r['completed_games'],',')+' completed games</span><small>'+e(r['purpose'].replace('_',' ').title())+'</small></div>' for r in d['retained_comparison_population'])
    return '''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; img-src data:; base-uri 'none'; form-action 'none'">
<title>NBA B102 recovery audit · Sports Edge Lab</title>
<style>
:root{color-scheme:light;--ink:#142d38;--muted:#53666f;--line:#d3dfe1;--paper:#f4f7f4;--teal:#0b625c;--red:#9a362e;--orange:#87531f}*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font:16px/1.58 system-ui,sans-serif}a{color:var(--teal);text-underline-offset:.18em}a:focus-visible{outline:3px solid #f6b84b;outline-offset:4px}main{width:min(1120px,100%);margin:auto;padding:44px 30px 72px}header{border-top:5px solid var(--teal);padding-top:24px}.eyebrow{font-size:.77rem;letter-spacing:.14em;font-weight:750;color:var(--teal)}h1{font-size:clamp(2.1rem,5vw,3.45rem);line-height:1.09;letter-spacing:-.045em;max-width:920px;margin:18px 0}h2{font-size:1.65rem;letter-spacing:-.025em;margin:0 0 12px}h3{font-size:1.05rem;margin:0 0 8px}p{margin:10px 0 16px}.lead{font-size:1.15rem;max-width:900px;color:#314c56}.meta{font-size:.84rem;color:var(--muted)}nav{display:flex;gap:12px 22px;flex-wrap:wrap;margin:25px 0 30px}nav a{font-weight:650}.banner{border-left:5px solid var(--orange);padding:16px 20px;background:#fff6e9;margin:24px 0}.cards{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;margin:25px 0}.card{background:white;border:1px solid var(--line);padding:19px;min-width:0;border-radius:8px}.number{font-size:2rem;font-weight:760;letter-spacing:-.04em;line-height:1.2}.caption{font-size:.88rem;color:var(--muted);margin-top:7px}section{background:white;border:1px solid var(--line);border-radius:10px;padding:27px;margin:18px 0;scroll-margin-top:20px}.badge{display:inline-block;border-radius:99px;font-size:.72rem;font-weight:800;letter-spacing:.04em;padding:3px 10px;background:#f5dfdc;color:var(--red);margin-bottom:12px}.badge.verified{background:#dceee8;color:var(--teal)}.badge.prepared{background:#fff0cf;color:var(--orange)}.rows{margin-top:21px}.row{display:grid;grid-template-columns:minmax(150px,1fr) minmax(0,3fr);gap:20px;padding:17px 0;border-top:1px solid var(--line)}.row strong{font-size:.91rem}.row p{margin:0;color:#344e58}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:22px}.grid>*{min-width:0}.fact{font-size:1.8rem;font-weight:760;letter-spacing:-.03em}.note{padding:14px 17px;border-radius:6px;background:#edf3f1;font-size:.92rem}ul{padding-left:22px}li{margin:11px 0}.population-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;margin:20px 0}.population{padding:16px;background:#f1f5f3;display:grid;gap:6px;border-radius:6px}.population small{color:var(--muted)}.sources{list-style:none;padding:0}.sources li{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:4px 16px;border-top:1px solid var(--line);padding:12px 0}.sources code{grid-column:1/-1;overflow-wrap:anywhere;font-size:.74rem;color:var(--muted)}.download{display:inline-block;background:var(--teal);color:white;font-weight:700;padding:11px 17px;border-radius:6px;text-decoration:none;margin:8px 0}footer{padding-top:15px;color:var(--muted);font-size:.87rem}code{overflow-wrap:anywhere}details{border-top:1px solid var(--line);padding-top:14px;margin-top:18px}summary{cursor:pointer;font-weight:700}.muted{color:var(--muted)}@media(max-width:650px){main{padding:24px 18px 44px}section{padding:20px}.cards{grid-template-columns:repeat(2,minmax(0,1fr))}.grid,.population-grid{grid-template-columns:1fr}.row{grid-template-columns:1fr;gap:6px}.sources li{grid-template-columns:1fr}.sources span{font-size:.8rem;color:var(--muted)}.number{font-size:1.65rem}.lead{font-size:1.03rem}}
</style></head><body><main>
<header><div class="eyebrow">SPORTS EDGE LAB / NBA · DATED RECOVERY AUDIT</div>
<h1>Saved projections recovered.<br>Scientific completion remains open.</h1>
<p class="lead">B101 failed after productive work was forced through a one-worker admission limit and the wrong stopping gate. A targeted B102 check authenticated all 5,808 saved projection outputs. It made zero new model fits and exposed a further publication queue bottleneck.</p>
<p class="meta">Native evidence through '''+e(d['evidence_through_utc'])+''' · Engineering record '''+e(d['engineering_observed_at_utc'])+'''</p>
<nav aria-label="Review sections"><a href="#failure">Actual failure</a><a href="#recovered">Verified recovery</a><a href="#throughput">CPU evidence</a><a href="#remaining">Remaining research</a><a href="#evidence">Evidence</a></nav>
</header>
<div class="banner"><strong>Overall scientific status: PARTIAL_RESUMABLE.</strong> The registered full research campaign, full V13 qualification, sustained 12–24-core utilization, champion promotion and website deployment are not established by this recovery record.</div>
<div class="cards" aria-label="Recovery summary"><div class="card"><div class="number">5,808 / 5,808</div><div class="caption">Saved projections verified and reused</div></div><div class="card"><div class="number">320</div><div class="caption">Original distribution model states preserved</div></div><div class="card"><div class="number">21</div><div class="caption">Overlapping projection tasks; not busy cores</div></div><div class="card"><div class="number">0</div><div class="caption">New scientific fits in this targeted check</div></div></div>
<section id="failure"><div class="badge">B101 · FAILED · EXIT 2</div><h2>Why the owner run stopped</h2>
<p>The observed failure left <strong>2,374 of 5,808 projection tasks complete and 3,434 deferred</strong>, with zero individual projection failures. Progress was continuing when admission stopped.</p>
<div class="rows"><div class="row"><strong>Earlier scientific input failure</strong><p>A worker returned the entire decoded historical table. Its result exceeded the 64 MiB interprocess message contract, so downstream scientific work could not begin. This was independent of the later projection-stage failure.</p></div>
<div class="row"><strong>Single-worker admission</strong><p>All 19 projection heartbeat samples recorded a global IO-pressure rule that capped this owner at one worker. The requested 24-worker ceiling did not represent admitted work.</p></div>
<div class="row"><strong>Misapplied stopping gate</strong><p>The presentation stage entered a scientific occupancy gate. Over '''+f'{f["representative_interval_seconds"]:.2f}'+''' seconds it used '''+f'{f["measured_cpu_seconds"]:.2f}'+''' CPU-seconds, or '''+f'{100*f["occupancy"]:.2f}'+'''% of one admitted core. The gate stopped admission at three minutes without checking continuing completions.</p></div></div>
<p class="note">The 3,434 deferred items were unfinished verification and publication tasks. They were not evidence of 3,434 missing Parquet files. B100's existing outputs had to be authenticated before deciding what required creation.</p></section>
<section id="recovered"><div class="badge verified">B102 V1 · TARGETED NATIVE CHECK COMPLETE</div><h2>Every declared projection row was checked</h2>
<div class="grid"><div><div class="fact">6,969,600 verified records</div><p>All 5,808 model variants retained 1,200 declared games each: 210 completed test games and 990 upcoming games. Exact hashes, schemas, lineage and ordered unique game indexes were checked.</p></div><div><div class="fact">0 missing · 0 null · 0 regenerated</div><p>All 5,808 projections were warm reuses and durably verified. There were zero failed tasks, zero deferred tasks and zero newly generated projection outputs.</p></div></div>
<p class="note">This is authentication of saved outputs. It does not create new forecast values, original issue timestamps, fits, rescored annual metrics or a full-season census.</p>
<details><summary>What “320 states preserved” actually establishes</summary><p>B101 verified all 320 original B100 residual-distribution state files. Zero missing files required restoration. Verification alone is not proof of renewed model application; the successful B100 fit record remains historical work and receives no new fit credit.</p></details></section>
<section id="throughput"><h2>Concurrency improved; sustained CPU remains unproven</h2>
<div class="grid"><div><div class="fact">21 overlapping tasks</div><p>The native check reached 24 physical worker processes and 29 distinct completed worker PIDs over the stage. The overlap count comes from actual task start and finish intervals.</p></div><div><div class="fact">'''+f'{a["task_cpu_per_stage_wall_second"]:.2f}'+''' CPU equivalents</div><p>Completed worker tasks accumulated '''+f'{a["completed_task_cpu_seconds"]:.2f}'+''' CPU-seconds across '''+f'{a["stage_wall_seconds"]:.2f}'+''' seconds of stage wall time. This ratio is distinct from the peak worker count and is far below 12–24 busy cores.</p></div></div>
<p>Independent 10-second logs showed that slow publication filled the shared outstanding-work limit and starved the verification queue. The first B102 native check therefore proves complete cache recovery and real concurrency, while retaining this throughput defect.</p>
<p class="meta">Whole-instance interval estimate: USD '''+f'{a["whole_instance_wall_interval_estimate_usd"]:.6f}'+'''. This is neither an AWS invoice nor an allocated NBA charge. The full research campaign was not launched.</p>
<div class="badge prepared">B102 V2 · ENGINEERING TESTED</div><h3>Separate verification from publication backpressure</h3><p>The next revision keeps verification and publication queues independent, reuses authenticated completed-checkpoint references, and stops treating waiting IO threads as occupied scientific cores. The explicit scientific process ceiling and shared CPU lease remain enforced.</p><p><strong>22 targeted engineering tests passed.</strong> A queue regression held publication blocked while all local verification tasks finished. A warm-reuse regression required only the new aggregate checkpoint to be published. These tests are not owner scientific utilization.</p><p>The 75% occupancy / 180-second acceptance threshold remains. Failed measurements remain failures; productive work may continue. Genuine absence of verified progress and stale monitoring still pause admission.</p></section>
<section id="remaining"><h2>What still has to be completed</h2>
<div class="population-grid">'''+populations+'''</div>
<p>The saved comparisons retain identical annual populations and a 50/50 validation default. <strong>Fourteen known validation omissions remain</strong>; scores on the retained rows cannot be relabeled as scores on an expanded full-season cohort. Previously inspected test results remain exposed.</p>
<ul><li>Reconcile and freeze the full all-competition evaluation manifests, including play-in and Cup-final omissions, then rescore all eligible contenders on the same rows.</li><li>Enter the registered scientific campaign using preserved estimators and all 320 distribution states. Complete missing features, controlled ablations, calibrations, learned combinations and distribution comparisons with separate new/reused/failed counts.</li><li>Demonstrate measured scientific fit PIDs, CPU use and completions at 12–24 workers when sufficient work and safe resources are available.</li><li>Close source-specific historical coverage, release-clock and market-overlap gaps. Keep DraftKings, Kalshi and Polymarket comparisons separate, and preserve missingness.</li><li>Publish the resulting completed and upcoming game review with truthful source, commit, merge and deployment status. Scientific selection remains separate from production promotion.</li></ul>
<p><a href="b101_execution_status.html">Open the preserved annual model comparison and B100 research findings</a>. Evaluation-weight sensitivity must not refit estimators, reweight training rows or use test outcomes for selection.</p></section>
<section id="evidence"><h2>Evidence and publication scope</h2><p>This page contains sanitized aggregates and content digests. The private execution packages, model states, individual prediction grids, provider records and storage locations are excluded.</p>
<a id="download-evidence" class="download" href="'''+download+'''" download="nba-b102-recovery-evidence.json">Download exact aggregate evidence</a>
<ul class="sources">'''+evidence+'''</ul><p class="note">Draft source review only. A committed page is not a deployed website, a refreshed source feed or a scientific promotion. This dated record does not claim a later B102 owner run has completed.</p></section>
<footer><a href="../README.md">NBA research archive</a> · <a href="b100_execution_status.html">Earlier B099/B100 recovery record</a><p>Other sports and their scientific records are unchanged. This review presents research engineering evidence and is not a wagering interface.</p></footer>
<script type="application/json" id="aggregate-evidence">'''+raw.replace('</','<\\/')+'''</script>
</main></body></html>
'''


def self_test(data):
    mutations=[]
    def change(section,key,value):
        changed=copy.deepcopy(data)
        if section:changed[section][key]=value
        else:changed[key]=value
        mutations.append(changed)
    for section,key,value in [
        ('','full_v13_complete',True),('','automatic_promotions',1),('','owner','NFL'),
        ('b101_failure','exit_code',0),('b101_failure','new_estimator_fits',1),
        ('b101_failure','admitted_projection_workers',24),('b101_failure','deferred_projection_tasks',0),
        ('preserved_work','b101_missing_states_restored',320),('preserved_work','b101_hydration_model_applications_verified',True),
        ('b102_projection_v1','new_projections_created',5808),('b102_projection_v1','full_research_run_launched',True),
        ('b102_projection_v1','new_forecast_values',6969600),('b102_projection_v1','scientific_occupancy_pass_claimed',True),
        ('b102_projection_v1','task_cpu_per_stage_wall_second',24),('b102_projection_v1','null_predictions',1),
        ('b102_projection_v1','actual_billed_cost_usd',.109743),('b102_projection_v2','new_owner_model_fits_claimed',22),
        ('b102_projection_v2','historical_remote_proofs_relabeled_as_current',True),
        ('population_qualification','test_used_for_selection',True),('population_qualification','expanded_population_rescored',True),
        ('publication','deployed',True),('publication','new_scientific_score_claimed',True)]:change(section,key,value)
    secret=copy.deepcopy(data);secret['evidence'][0]['label']='s3://private-owner-location';mutations.append(secret)
    for changed in mutations:
        try:validate(changed)
        except (ValueError,TypeError,KeyError):continue
        raise AssertionError('An unsupported evidence mutation was accepted')
    print(f'{len(mutations)} unsupported evidence mutations rejected; zero owner fits or provider requests')


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');parser.add_argument('--self-test',action='store_true')
    args=parser.parse_args();data=json.loads(SOURCE.read_text());body=render(data)
    if args.self_test:self_test(data)
    if args.check:
        if OUTPUT.read_text()!=body:raise SystemExit('Generated B102 HTML does not match the evidence snapshot')
        print('B102 deterministic HTML verified')
    else:OUTPUT.write_text(body)

if __name__=='__main__':main()
