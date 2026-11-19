#!/usr/bin/env python3
"""Render an offline NBA status dashboard from sanitized, dated aggregates.

Rendering never fits models, retrieves providers, installs owner deliverables,
changes checkpoints, or publishes a website.
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

HERE = Path(__file__).resolve().parent
SOURCE = HERE / 'b104_execution_status.json'
OUTPUT = HERE / 'b104_execution_status.html'


def valid_pin(value):
    return (isinstance(value, dict) and set(value) == {'bytes', 'sha256'}
            and type(value['bytes']) is int and value['bytes'] > 0
            and isinstance(value['sha256'], str)
            and re.fullmatch(r'[0-9a-f]{64}', value['sha256']) is not None)


def validate(data):
    if set(data) != {'schema', 'owner', 'actual_evidence_cutoff_utc', 'actual_B103',
                    'B104_preparation', 'owner_request', 'cumulative_registered_work',
                    'evaluation', 'remaining_campaign', 'requirements_still_open',
                    'publication', 'evidence'}:
        raise ValueError('Only the scoped NBA aggregate fields are allowed')
    if data['schema'] != 'sel.nba.public_execution_status.b104.v1' or data['owner'] != 'NBA':
        raise ValueError('NBA owns this dated status')
    actual = data['actual_B103']
    expected = {'release': 'B103', 'scientific_status': 'PARTIAL_RESUMABLE_BOUNDED_ACCEPTANCE',
        'execution_outcome': 'BOUNDED_TASKS_COMPLETED_FULL_CAMPAIGN_DEFERRED',
        'invocation_exit_code': 2, 'bounded_completed_executions': 1,
        'bounded_failed_executions': 0, 'bounded_incomplete_executions': 0,
        'full_owner_executions': 0, 'execution_complete': False, 'full_v13_complete': False,
        'new_estimator_fits': 12, 'new_calibration_fits': 12,
        'new_meta_model_fits': 0, 'new_residual_distribution_fits': 0,
        'failed_jobs': 0, 'failed_estimator_fits': 0,
        'new_provider_requests': 0, 'actual_provider_credits': 0,
        'B100_distribution_files_verified': 320, 'B100_missing_files_restored': 0,
        'B100_new_application_credit': 0, 'B100_actual_application_counter': None,
        'current_projection_worker_tasks': 0, 'current_projection_files_rehashed': 0,
        'prior_projection_checkpoint_count': 5808, 'full_research_run_launched': False,
        'actual_invoiced_usd': None, 'nba_allocated_cost_usd': None}
    if any(actual.get(key) != value for key, value in expected.items()):
        raise ValueError('Keep bounded completion, fitting, reuse and full research separate')
    cpu = actual['cpu']
    if (cpu['acceptance'] != 'CONDITIONAL_SHORT_QUEUE_COMPLETION_NOT_FULL_CAPACITY_PASS'
            or cpu['measured_full_interval_passes'] != 0
            or cpu['required_representative_seconds'] != 180
            or cpu['required_occupancy_fraction'] != 0.75
            or cpu['context_peak_is_estimator_fit_utilization']
            or cpu['configured_workers_are_measured_busy_cores']
            or not math.isclose(cpu['context_preparation_peak_sampled_owner_cores'], 20.44237471292999)
            or not math.isclose(cpu['estimator_phase_peak_sampled_owner_cores'], 4.616901583083376)
            or not math.isclose(cpu['estimator_phase_elapsed_seconds'], 50.095931)):
        raise ValueError('A requested ceiling or short context peak is not a fit occupancy pass')
    request = data['owner_request']
    if request != {'normal_scientific_worker_target': 12, 'requested_cores': 36,
        'explicit_max_workers': 36, 'native_threads_per_independent_fit': 1,
        'safe_capacity_may_be_lower_than_requested': True,
        'requested_workers_are_measured_busy_cores': False, 'compute_guard_usd': 200,
        'wall_minutes': 0, 'wall_zero_waives_cost_guard': False,
        'useful_cpu_acceptance_occupancy': 0.75, 'useful_cpu_acceptance_seconds': 180}:
        raise ValueError('Retain the requested 12–36 policy, hard ceiling and safeguards')
    prep = data['B104_preparation']
    if prep['status'] not in {'PREPARATION_IN_PROGRESS', 'PREPARED_DELIVERY_NOT_VERIFIED',
                              'DELIVERY_VERIFIED_NATIVE_PENDING',
                              'DELIVERY_AND_NATIVE_INSTALL_VERIFIED_OWNER_EXECUTION_PENDING'}:
        raise ValueError('Unsupported preparation status')
    for name in ('new_owner_executions', 'new_estimator_fits', 'new_calibration_fits',
                 'new_meta_model_fits', 'new_residual_distribution_fits', 'automatic_promotions'):
        if prep.get(name) != 0:
            raise ValueError('Preparing B104 is not new owner research or promotion')
    if not prep['owner_execution_pending'] or prep['full_v13_complete']:
        raise ValueError('Native preparation is not owner execution or full acceptance')
    if prep['canonical_executable'] is not None and not valid_pin(prep['canonical_executable']):
        raise ValueError('Canonical executable evidence needs exact bytes and SHA-256')
    delivered = prep['delivery_full_body_readback_verified']
    if delivered:
        if (prep['status'] not in {'DELIVERY_VERIFIED_NATIVE_PENDING',
                                  'DELIVERY_AND_NATIVE_INSTALL_VERIFIED_OWNER_EXECUTION_PENDING'}
                or not valid_pin(prep['canonical_executable'])
                or not valid_pin(prep['delivery_verification_evidence'])
                or not isinstance(prep['observed_at_utc'], str)):
            raise ValueError('Verified delivery needs exact executable and readback-proof pins')
    elif prep['status'].startswith('DELIVERY_') or prep['delivery_verification_evidence'] is not None:
        raise ValueError('Incomplete transfer is not verified delivery')
    installed = prep['native_physical_installation_verified']
    if installed:
        if (not delivered or not valid_pin(prep['native_installation_verification_evidence'])
                or prep['status'] != 'DELIVERY_AND_NATIVE_INSTALL_VERIFIED_OWNER_EXECUTION_PENDING'):
            raise ValueError('Native installation needs its own authenticated proof')
    elif (prep['native_installation_verification_evidence'] is not None
            or prep['status'] == 'DELIVERY_AND_NATIVE_INSTALL_VERIFIED_OWNER_EXECUTION_PENDING'):
        raise ValueError('Do not relabel remote delivery as native installation')
    if prep['native_readiness_verified']:
        if not installed or not valid_pin(prep['native_readiness_verification_evidence']):
            raise ValueError('Read-only readiness needs its own native proof')
    elif prep['native_readiness_verification_evidence'] is not None:
        raise ValueError('Unverified readiness evidence cannot claim a pass')
    cumulative = data['cumulative_registered_work']
    if (cumulative['preserved_validation_replay_groups_complete'] != 846
            or cumulative['preserved_validation_replay_groups_missing'] != 1583
            or cumulative['preserved_validation_replay_groups_registered'] != 2429
            or cumulative['box_base_estimators_complete'] != 24
            or cumulative['box_calibrators_complete'] != 24
            or cumulative['box_base_recipes_registered'] != 240
            or cumulative['box_base_recipes_missing'] != 216
            or cumulative['registered_counts_are_full_v13_completion']):
        raise ValueError('Cumulative work must use distinct preserved identities')
    evaluation = data['evaluation']
    if (evaluation['validation_declared_completed_games'] != [1321, 1322]
            or evaluation['historical_B100_validation_games'] != [1314, 1315]
            or evaluation['test_declared_completed_games'] != 210
            or evaluation['test_count_scope'] != 'FROZEN_210_GAME_SNAPSHOT_NOT_FRESH_ALL_COMPLETED_GAME_CENSUS'
            or evaluation['fresh_all_completed_test_reporting_complete']
            or evaluation['same_population_all_contender_comparison_complete']
            or evaluation['independent_full_season_census_verified']
            or evaluation['full_season_champions_qualified']
            or evaluation['test_outcomes_select_models']
            or evaluation['market_overlap_is_full_population']
            or not evaluation['prior_test_exposure_preserved']
            or evaluation['weight_sensitivity_refits_estimators']):
        raise ValueError('Frozen populations and exposed test reporting retain their limits')
    if data['remaining_campaign'] != {
        'missing_preserved_validation_replay_groups': 1583, 'missing_box_base_recipes': 216,
        'maximum_additional_calibrators': 216,
        'original_distribution_states_to_apply_without_refit': 320,
        'maximum_additional_meta_models': 162,
        'maximum_additional_combination_residual_heads': 216,
        'fixed_mixtures_without_new_fits': 480, 'registered_maxima_guarantee_full_v13': False}:
        raise ValueError('Registered missing work is not completed science')
    if len(data['requirements_still_open']) != 5 or any(
            item['status'] not in {'INCOMPLETE', 'UNPROVEN', 'PREPARED_REPAIR_OWNER_EXECUTION_PENDING'}
            for item in data['requirements_still_open']):
        raise ValueError('Remaining acceptance requirements must remain visible')
    if data['publication'] != {'draft_pr': 392, 'source_review_only': True,
        'merged': False, 'website_deployed': False, 'new_public_forecast_values': 0,
        'automatic_champion_promotions': 0, 'private_runtime_or_raw_provider_data_published': False}:
        raise ValueError('Draft source is separate from deployment and production promotion')
    if len(data['evidence']) != 4 or any(
            set(row) != {'label', 'bytes', 'sha256'} or not valid_pin({k: row[k] for k in ('bytes', 'sha256')})
            for row in data['evidence']):
        raise ValueError('Use sanitized evidence identities, not private source locations')
    if re.search(r'/home/|s3://|arn:aws:|sagemaker-sports|tracks/nba/checkpoints|api[_-]?key|password|\.pyz\b',
                 json.dumps(data), re.I):
        raise ValueError('Private packages, storage locations and credentials cannot be published')
    return data


def render(data):
    d = validate(data); a = d['actual_B103']; p = d['B104_preparation']; e = html.escape
    raw = json.dumps(d, indent=2, sort_keys=True) + '\n'
    download = 'data:application/json;base64,' + base64.b64encode(raw.encode()).decode()
    delivered = p['delivery_full_body_readback_verified']
    delivery_title = 'Private delivery verified. Owner execution pending.' if delivered else 'Preparation is recorded. Delivery verification remains pending.'
    installed = p['native_physical_installation_verified']
    delivery_text = ('Prepared private delivery and native installation are verified. The full research campaign has not been launched.'
                     if delivered and installed else
                     'Complete-byte verification supports the prepared private delivery. Native installation and the next owner execution remain pending.'
                     if delivered else 'No completed private upload or native installation is certified by this snapshot. The owner research run has not been launched.')
    readiness_text = ('Read-only native readiness passed. It produces zero research fits and does not establish scientific utilization.'
                      if p['native_readiness_verified'] else 'Read-only native readiness remains unverified in this dated snapshot.')
    pending_text = ('The next owner research execution remains pending. Production deployment is separate from this draft source review.'
                    if installed else 'Native installation and the next owner run remain pending. Production deployment is separate from this draft source review.')
    pin_html = '<p class="muted">The canonical executable identity is not yet certified in this snapshot.</p>'
    if p['canonical_executable'] is not None:
        cp = p['canonical_executable']
        pin_html = '<div class="identity"><span>Prepared executable · ' + f'{cp["bytes"]:,}' + ' bytes</span><code>' + cp['sha256'] + '</code></div>'
    if delivered:
        dp = p['delivery_verification_evidence']
        pin_html += '<div class="identity"><span>Delivery verification evidence · ' + f'{dp["bytes"]:,}' + ' bytes</span><code>' + dp['sha256'] + '</code></div>'
    for field, label in [('native_installation_verification_evidence', 'Native installation evidence'),
                         ('native_readiness_verification_evidence', 'Read-only readiness evidence')]:
        proof = p[field]
        if proof is not None:
            pin_html += '<div class="identity"><span>' + label + ' · ' + f'{proof["bytes"]:,}' + ' bytes</span><code>' + proof['sha256'] + '</code></div>'
    requirements = ''.join('<li><div><strong>' + e(row['name']) + '</strong><span class="state">' +
        e(row['status'].replace('_', ' ').lower()) + '</span></div><p>' + e(row['detail']) + '</p></li>'
        for row in d['requirements_still_open'])
    sources = ''.join('<li><strong>' + e(row['label']) + '</strong><span>' + f'{row["bytes"]:,}' +
        ' bytes</span><code>' + row['sha256'] + '</code></li>' for row in d['evidence'])
    return '''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; img-src data:; base-uri 'none'; form-action 'none'">
<title>NBA B104 preparation and B103 actual work · Sports Edge Lab</title>
<style>
:root{color-scheme:light;--ink:#172f3a;--muted:#536771;--line:#d1dfdd;--paper:#f2f5f1;--teal:#0c655b;--amber:#875015}*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--paper);color:var(--ink);font:16px/1.6 system-ui,sans-serif}a{color:var(--teal);text-underline-offset:.18em}a:focus-visible,summary:focus-visible{outline:3px solid #e6a641;outline-offset:4px}main{width:min(1120px,100%);padding:42px 28px 62px;margin:auto}header{border-top:5px solid var(--teal);padding-top:24px}.eyebrow{font-size:.76rem;letter-spacing:.14em;font-weight:800;color:var(--teal)}h1{max-width:900px;font-size:clamp(2.2rem,5vw,3.5rem);line-height:1.08;letter-spacing:-.045em;margin:18px 0}h2{font-size:1.6rem;letter-spacing:-.025em;line-height:1.2;margin:0 0 15px}h3{font-size:1rem;margin:0 0 6px}p{margin:10px 0 16px}.lead{font-size:1.12rem;max-width:900px;color:#36505a}.meta,.muted{font-size:.88rem;color:var(--muted)}nav{display:flex;flex-wrap:wrap;gap:10px 22px;margin:25px 0 28px}nav a{font-weight:650}.notice{padding:18px 20px;background:#fff3df;border-left:5px solid var(--amber);margin:22px 0}.cards{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;margin:24px 0}.card{padding:19px;background:white;border:1px solid var(--line);border-radius:8px;min-width:0}.number{font-size:2rem;font-weight:780;letter-spacing:-.035em;line-height:1.15}.caption{font-size:.86rem;color:var(--muted);margin-top:9px}section{background:white;border:1px solid var(--line);border-radius:10px;margin:18px 0;padding:27px;scroll-margin-top:18px}.badge{display:inline-block;font-size:.72rem;font-weight:800;letter-spacing:.05em;padding:4px 10px;border-radius:99px;margin-bottom:13px;background:#e2efe9;color:var(--teal)}.badge.pending{background:#fff0d0;color:var(--amber)}.columns{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:24px}.columns>*{min-width:0}.metric{font-size:1.9rem;font-weight:770;letter-spacing:-.04em}.note{padding:14px 17px;background:#eef4f0;border-radius:6px}.progress-row{border-top:1px solid var(--line);padding:17px 0}.progress-head{display:flex;justify-content:space-between;gap:12px}.progress-head strong{font-size:1.1rem}.progress-row progress{display:block;width:100%;height:14px;accent-color:var(--teal);margin:10px 0}.progress-row p{margin:0;font-size:.9rem;color:var(--muted)}.policy{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;margin:20px 0}.policy div{padding:17px;background:#eff5f1;border-radius:7px;min-width:0}.policy strong{display:block;font-size:1.7rem;line-height:1.15}.policy span{font-size:.84rem;color:var(--muted)}.identity{border-top:1px solid var(--line);padding:14px 0;display:grid;gap:5px}.identity span{font-size:.85rem}.identity code{font-size:.74rem;overflow-wrap:anywhere}.table-wrap{width:100%;margin:18px 0}table{width:100%;border-collapse:collapse;text-align:left;font-size:.91rem}caption{text-align:left;font-weight:700;margin-bottom:10px}th,td{padding:12px 10px;border-bottom:1px solid var(--line);vertical-align:top}thead th{color:var(--muted);font-size:.8rem;letter-spacing:.03em}.requirements{list-style:none;margin:20px 0 0;padding:0}.requirements li{border-top:1px solid var(--line);padding:17px 0}.requirements li div{display:flex;align-items:baseline;justify-content:space-between;gap:12px}.state{font-size:.72rem;text-transform:uppercase;letter-spacing:.03em;color:var(--amber)}.requirements p{margin:6px 0 0;color:var(--muted);font-size:.93rem}.sources{list-style:none;padding:0}.sources li{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:4px 15px;border-top:1px solid var(--line);padding:13px 0;font-size:.88rem}.sources code{grid-column:1/-1;overflow-wrap:anywhere;color:var(--muted);font-size:.74rem}.download{display:inline-block;color:white;background:var(--teal);padding:11px 18px;border-radius:6px;font-weight:750;text-decoration:none;margin:12px 0}details{border-top:1px solid var(--line);padding-top:14px;margin-top:18px}summary{cursor:pointer;font-weight:700}code,#prepared-status,.notice strong,.note strong{overflow-wrap:anywhere}footer{padding-top:18px;font-size:.87rem;color:var(--muted)}@media(max-width:650px){main{padding:24px 18px 44px}section{padding:20px}.cards{grid-template-columns:repeat(2,minmax(0,1fr))}.number{font-size:1.7rem}.columns,.policy{grid-template-columns:1fr;gap:12px}.policy div{display:flex;align-items:baseline;gap:15px}.policy strong{min-width:2.2rem}.lead{font-size:1.02rem}.progress-head,.requirements li div{display:block}.state{display:block;margin-top:4px}.sources li{grid-template-columns:1fr}.sources span{font-size:.8rem}table,thead,tbody,tr,th,td{display:block}thead{display:none}tr{border-top:1px solid var(--line);padding:10px 0}td,th{border:0;padding:5px 0}td::before{content:attr(data-label) ": ";font-weight:650}tbody th{font-size:1rem}.metric{font-size:1.65rem}}@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}}
</style></head><body><main>
<header><div class="eyebrow">SPORTS EDGE LAB / NBA · CURRENT EXECUTION REVIEW</div>
<h1>Completed work preserved.<br>The next campaign is prepared separately.</h1>
<p class="lead">B103 completed a bounded research scope. B104 prepares the next continuation with a normal target of 12 scientific workers and an explicit ceiling of 36. Scientific completion still needs measured owner-run evidence.</p>
<p class="meta">Latest actual research evidence: ''' + e(d['actual_evidence_cutoff_utc']) + ''' · B104 preparation status: <span id="prepared-status">''' + e(p['status']) + '''</span></p>
<nav aria-label="Status sections"><a href="#actual">Actual B103 work</a><a href="#prepared">B104 preparation</a><a href="#cpu">Measured CPU</a><a href="#population">Evaluation rows</a><a href="#remaining">Remaining work</a><a href="#evidence">Evidence</a></nav></header>
<div class="notice"><strong>PARTIAL_RESUMABLE_BOUNDED_ACCEPTANCE · full V13 remains incomplete.</strong> B103's policy exit 2 followed completion of the selected bounded tasks. It is not a full campaign completion, a sustained CPU pass or a production promotion.</div>
<div class="cards" aria-label="Actual B103 bounded result"><div class="card"><div class="number">12 + 12</div><div class="caption">New estimator + calibration fits in B103</div></div><div class="card"><div class="number">0</div><div class="caption">Observed B103 job failures</div></div><div class="card"><div class="number">320</div><div class="caption">Original distribution files verified; application not credited</div></div><div class="card"><div class="number">0</div><div class="caption">New B104 owner executions in this preparation record</div></div></div>
<section id="actual"><div class="badge">B103 · BOUNDED TASKS COMPLETED</div><h2>New work and preserved work have separate counts</h2>
<p>One bounded execution completed with <strong>12 new estimators, 12 new calibrators and zero failed jobs</strong>. It added no meta-model or residual-distribution fits and made no provider requests. Zero full campaign executions are credited to B103.</p>
<div class="progress-row"><div class="progress-head"><strong>846 / 2,429 replay groups complete</strong><span>1,583 still missing</span></div><progress value="846" max="2429" aria-label="Completed preserved validation replay groups">846 of 2429</progress><p>834 authenticated prior groups + 12 distinct new groups. The completed groups cover 2,151 of 5,808 preserved variants; dependent blends remain incomplete.</p></div>
<div class="progress-row"><div class="progress-head"><strong>24 / 240 box-score base recipes complete</strong><span>216 still missing</span></div><progress value="24" max="240" aria-label="Completed registered box-score base recipes">24 of 240</progress><p>12 distinct prior B102 fits + 12 new B103 fits, with 24 associated calibrators. Prior work is not counted again as new B103 research.</p></div>
<details id="reuse-detail"><summary>What verified state reuse establishes</summary><p>All 320 original distribution files were verified, and zero missing files required restoration. <strong>Zero renewed applications are credited; the actual application counter remains unknown.</strong> Prior authenticated authority for 5,808 projection outputs was reused. B103 performed zero current projection tasks and rehashed zero individual projection files in that stage. Historical verification is not new fitting, application or CPU work.</p></details>
<p class="meta">The verified compact return contains 20,226 bytes and eight payloads, without repacking unchanged historical payloads. The whole-instance through-delivery estimate is USD 0.307878; actual invoiced cost and NBA allocation are unknown.</p></section>
<section id="prepared"><div class="badge pending">B104 · OWNER EXECUTION PENDING</div><h2>''' + e(delivery_title) + '''</h2><p id="delivery-qualification">''' + e(delivery_text) + '''</p><p id="readiness-qualification">''' + e(readiness_text) + '''</p>
<div class="policy" aria-label="Requested owner parallelism"><div><strong>12</strong><span>Normal scientific worker target</span></div><div><strong>36</strong><span>Requested cores / explicit worker ceiling</span></div><div><strong>1</strong><span>Native thread per independent fit</span></div></div>
<p>The owner requests <strong>12–36 cores</strong> where sufficient independent work and safe resources exist. Shared CPU capacity, available memory and I/O can reduce admission. The explicit 36-worker maximum is a hard ceiling; it is not a measured busy-core count. A USD 200 compute guard remains active when the wall-minute setting is zero.</p>
<p>B104 prepares a separate descriptive test refresh <strong>after validation selection locks</strong>, preserving completed validation task identities and fitted components. It also reads the actual pinned storage-navigation bundle and current continuation. Neither preparation nor storage verification creates scientific fits, qualified champions or a completed V13 result.</p>
''' + pin_html + '''<p class="note">''' + e(pending_text) + '''</p></section>
<section id="cpu"><h2>Preparation CPU is useful work. Fit throughput has its own evidence.</h2>
<div class="columns"><div><div class="metric">20.442 CPU equivalents</div><h3>Context-preparation sample peak</h3><p>Measured owner CPU during preparation of real scientific inputs. This peak is not estimator-fitting utilization and does not establish a sustained capacity pass.</p></div><div><div class="metric">4.6169 CPU equivalents</div><h3>Estimator-phase sample peak</h3><p>The fit phase lasted 50.10 seconds and began with 12 ready tasks, using one native thread per independent fit.</p></div></div>
<p class="note"><strong>CONDITIONAL_SHORT_QUEUE_COMPLETION_NOT_FULL_CAPACITY_PASS.</strong> Zero sustained 180-second / 75%-occupancy passes were recorded. The threshold is unchanged; a short completed queue and a configured 36-worker limit do not establish sustained 12–36-core fitting.</p>
<p class="meta">These figures come from 41 independent resource samples. The mirrored log is not an additional set of observations. No synthetic CPU load receives scientific credit.</p></section>
<section id="population"><h2>Compare models only on identical eligible rows</h2>
<div class="table-wrap"><table><caption>Declared completed-game populations</caption><thead><tr><th>Season / use</th><th>Preserved B100</th><th>Expanded frozen campaign</th><th>Qualification</th></tr></thead><tbody>
<tr><th scope="row">2024–25 · validation</th><td data-label="Preserved B100">1,314</td><td data-label="Expanded frozen">1,321</td><td data-label="Qualification">Full contender replay incomplete</td></tr>
<tr><th scope="row">2025–26 · validation</th><td data-label="Preserved B100">1,315</td><td data-label="Expanded frozen">1,322</td><td data-label="Qualification">Full contender replay incomplete</td></tr>
<tr><th scope="row">2026–27 · exposed test</th><td data-label="Preserved B100">210</td><td data-label="Expanded frozen">210</td><td data-label="Qualification">Frozen snapshot; fresh all-completed census unfinished</td></tr>
</tbody></table></div>
<p>Scores from different populations cannot establish an all-model winner. The independent all-competition census and the expanded all-contender comparison remain incomplete. Missing provider overlap stays separate from the full eligible game population.</p>
<details id="selection-detail"><summary>Validation selection and test-exposure safeguards</summary><p>Use 50/50 annual validation metrics as the primary policy, with 40/60, 30/70, 20/80 and 10/90 sensitivity scores. Changing evaluation ratios must not refit estimators or reweight training seasons. Previously inspected test outcomes remain exposed and cannot tune or select features, fitted components, weights or champions. Original issues and reconstructions retain separate labels.</p></details>
<p><a href="b101_execution_status.html">Open the preserved model comparison and its dated qualifications</a> · <a href="b103_execution_status.md">Read the actual B103 execution audit</a></p></section>
<section id="remaining"><h2>The remaining work is explicit</h2><p>The finite campaign still includes 216 base recipes with their calibrators, application of all 320 original distribution states without refitting them, up to 162 meta-models and 216 combination residual heads. Another 480 fixed mixtures require zero new fits. These counts are registered maxima, not a promise that one run completes every V13 branch.</p><ul class="requirements">''' + requirements + '''</ul></section>
<section id="evidence"><h2>Inspect the exact aggregate evidence</h2><p>This page publishes aggregate counts, scientific qualifications and content digests. Private runtime packages, model states, prediction grids, provider records and storage locations are excluded.</p><a class="download" id="download-evidence" href="''' + download + '''" download="nba-b104-current-status-evidence.json">Download exact aggregate evidence</a><ul class="sources">''' + sources + '''</ul><p class="note">Draft PR 392 remains unmerged. No website deployment or champion promotion is established. Source checks and browser rendering are engineering evidence, separate from owner research and scientific acceptance.</p></section>
<footer><a href="../README.md">NBA research archive</a> · <a href="b102_execution_status.html">Preserved projection-recovery audit</a><p>Other owners' records remain unchanged. No new forecasts or model fits are produced by this report.</p></footer>
<script type="application/json" id="aggregate-evidence">''' + raw.replace('</', '<\\/') + '''</script></main></body></html>
'''


def self_test(data):
    cases = []
    def change(section, key, value):
        altered = copy.deepcopy(data)
        altered[section][key] = value
        cases.append(altered)
    for section, key, value in [
        ('actual_B103', 'new_estimator_fits', 36),
        ('actual_B103', 'bounded_failed_executions', 1),
        ('actual_B103', 'execution_complete', True),
        ('actual_B103', 'B100_actual_application_counter', 320),
        ('actual_B103', 'B100_missing_files_restored', 320),
        ('actual_B103', 'current_projection_worker_tasks', 5808),
        ('actual_B103', 'actual_invoiced_usd', 0.307878),
        ('B104_preparation', 'new_owner_executions', 1),
        ('B104_preparation', 'full_v13_complete', True),
        ('owner_request', 'explicit_max_workers', 48),
        ('owner_request', 'requested_workers_are_measured_busy_cores', True),
        ('owner_request', 'wall_zero_waives_cost_guard', True),
        ('cumulative_registered_work', 'box_base_estimators_complete', 12),
        ('evaluation', 'fresh_all_completed_test_reporting_complete', True),
        ('evaluation', 'same_population_all_contender_comparison_complete', True),
        ('evaluation', 'test_outcomes_select_models', True),
        ('evaluation', 'weight_sensitivity_refits_estimators', True),
        ('remaining_campaign', 'registered_maxima_guarantee_full_v13', True),
        ('publication', 'website_deployed', True),
        ('publication', 'automatic_champion_promotions', 1)]:
        change(section, key, value)
    altered = copy.deepcopy(data); altered['actual_B103']['cpu']['measured_full_interval_passes'] = 1; cases.append(altered)
    altered = copy.deepcopy(data); altered['B104_preparation']['native_physical_installation_verified'] = True
    altered['B104_preparation']['native_installation_verification_evidence'] = None; cases.append(altered)
    altered = copy.deepcopy(data); altered['B104_preparation']['native_readiness_verified'] = True
    altered['B104_preparation']['native_readiness_verification_evidence'] = None; cases.append(altered)
    altered = copy.deepcopy(data); altered['B104_preparation']['delivery_full_body_readback_verified'] = True
    altered['B104_preparation']['delivery_verification_evidence'] = None; cases.append(altered)
    altered = copy.deepcopy(data); altered['evidence'][0]['label'] = 's3://private-owner-location'; cases.append(altered)
    for altered in cases:
        try:
            validate(altered)
        except (ValueError, TypeError, KeyError):
            continue
        raise AssertionError('Unsupported evidence mutation was accepted')
    print(f'{len(cases)} unsupported evidence mutations rejected; zero owner fits or provider requests')


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--check', action='store_true'); parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args(); data = json.loads(SOURCE.read_text()); body = render(data)
    if args.self_test:
        self_test(data)
    if args.check:
        if OUTPUT.read_text() != body:
            raise SystemExit('B104 generated HTML differs from the dated aggregate evidence')
        print('B104 deterministic HTML verified')
    else:
        OUTPUT.write_text(body)


if __name__ == '__main__':
    main()
