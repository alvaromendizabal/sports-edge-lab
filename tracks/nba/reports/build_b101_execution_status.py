#!/usr/bin/env python3
"""Render the NBA B101 public review from an allowlisted aggregate snapshot.

This credential-free renderer cannot run an owner campaign, train a model or
refresh a provider. Its self-tests reject unsupported scientific/public claims.
"""
from __future__ import annotations

import argparse
import copy
import html
import json
import math
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
SOURCE = HERE / 'b101_execution_status.json'
OUTPUT = HERE / 'b101_execution_status.html'
SEASONS = ('2024-25', '2025-26', '2026-27')
OBJECTIVES = ('winner_accuracy', 'winner_log_loss', 'winner_brier',
              'margin_mae', 'margin_rmse', 'total_mae', 'total_rmse')
LABELS = {'winner_accuracy':'Winner accuracy', 'winner_log_loss':'Winner log loss',
          'winner_brier':'Winner Brier score', 'margin_mae':'Margin MAE',
          'margin_rmse':'Margin RMSE', 'total_mae':'Total MAE', 'total_rmse':'Total RMSE'}


def validate(d):
    if d['schema'] != 'sel.nba.public_execution_status.b101.v1' or d['owner'] != 'NBA':
        raise ValueError('The dated NBA aggregate schema is required')
    if (d['actual_owner_status'] != 'AVAILABLE_REGISTERED_CAMPAIGN_COMPLETE_V13_PROGRAM_PARTIAL'
            or d['execution_complete'] is not True or d['full_v13_complete'] is not False
            or d['qualified_full_season_champions'] != 0 or d['automatic_promotions'] != 0):
        raise ValueError('Registered campaign completion does not establish full V13 completion')
    actual = d['b100_actual']
    required = {'observed_owner_executions':1,'completed_registered_campaigns':1,
        'new_estimator_fits':0,'new_calibration_fits':0,'new_residual_distribution_fits':320,
        'failed_jobs':0,'new_provider_requests':0,'actual_provider_credits':0,
        'completed_point_variants':5808,'completed_distribution_heads':320,
        'completed_test_games':210,'upcoming_games':990,'forecast_population_games':1200,
        'completed_prediction_rows':1219680,'upcoming_prediction_rows':5749920,
        'new_prediction_ledgers':5808}
    if any(actual.get(k) != v for k,v in required.items()):
        raise ValueError('Preserve actual B100 fit, inference and population counts')
    if (not actual['current_forecasts_complete'] or actual['strict_original_issuance_claimed']
            or actual['test_used_for_selection'] or actual['publication_performed']
            or not actual['prior_test_exposure_preserved']):
        raise ValueError('Frozen inference is not proof of original issuance or deployment')
    population = d['population']
    if (population['common_retained_population_verified'] is not True
            or population['same_point_variant_count'] != 5808
            or population['same_distribution_head_count'] != 320
            or population['full_independent_census_verified'] is not False
            or population['known_missing_validation_games'] != 14
            or population['proposed_extension_rescored'] is not False):
        raise ValueError('Identical retained rows and complete-season qualification are separate')
    by_season = {r['season']:r for r in population['seasons']}
    if set(by_season) != set(SEASONS) or len(population['seasons']) != 3:
        raise ValueError('All annual populations must remain visible')
    for season,n,expanded in (('2024-25',1314,1321),('2025-26',1315,1322),('2026-27',210,None)):
        row = by_season[season]
        if row['retained_completed_games'] != n or row['source_supported_completed_games'] != expanded:
            raise ValueError('Expanded populations cannot inherit scores from the retained cohort')
        if expanded is not None and (row['known_missing_games'],row['missing_play_in_games'],row['missing_cup_final_games']) != (7,6,1):
            raise ValueError('Preserve the known play-in and Cup-final census omissions')
    seen=set()
    for row in d['selected_research_roles']:
        key=(row['role'],row['horizon_minutes'])
        if key in seen or key[0] not in OBJECTIVES or key[1] not in (60,120):
            raise ValueError('Exactly one saved nominee per objective and horizon is required')
        seen.add(key)
        if row['model_family'] not in {'CatBoost','Fixed model blend','Regularized linear model'}:
            raise ValueError('Only the observed coarse selected-role model families are public')
        if row['selection_policy'] != '50/50 annual validation' or row['test_selected'] or row['qualified_full_season_champion']:
            raise ValueError('Previously exposed test outcomes cannot select a research role')
        if set(row['annual']) != set(SEASONS):
            raise ValueError('Every role must retain all three annual populations')
        for season,n in zip(SEASONS,(1314,1315,210)):
            cell=row['annual'][season]
            if cell['n'] != n or not isinstance(cell['value'],(int,float)) or not math.isfinite(cell['value']):
                raise ValueError('Every compared nominee must retain the identical annual denominator')
        if not math.isclose(row['primary_validation_score'],
                (row['annual']['2024-25']['value']+row['annual']['2025-26']['value'])/2,
                abs_tol=0.0000011):
            raise ValueError('The public primary aggregate must match the saved 50/50 policy within display rounding')
    if seen != {(o,h) for o in OBJECTIVES for h in (60,120)}:
        raise ValueError('All fourteen selected roles must remain visible')
    findings = d['distribution_findings']
    if (findings['empirical_heads'], findings['gaussian_heads'],
            findings['empirical_heads_with_infinite_validation_log_mass'],
            findings['gaussian_heads_with_finite_validation_log_mass']) != (160,160,160,160):
        raise ValueError('Preserve the saved empirical zero-mass negative finding')
    if (findings['validation_zero_mass_head_games'] != 3925 or findings['zero_mass_count_is_unique_games']
            or not findings['empirical_heads_remain_eligible_for_crps_and_interval_scores']
            or findings['qualified_exact_line_comparison_cells'] != 0):
        raise ValueError('Head-game losses are not unique games or qualified market comparisons')
    if [r['source'] for r in findings['source_comparisons']] != ['DraftKings','Kalshi','Polymarket US','Polymarket International']:
        raise ValueError('Keep market source and product identities separate')
    cpu = d['cpu']
    if (cpu['requested_worker_ceiling'], cpu['peak_fit_worker_processes'], cpu['measured_full_interval_passes']) != (24,24,0):
        raise ValueError('Worker peaks do not establish a three-minute occupancy pass')
    if (cpu['worker_count_is_measured_occupancy'] or cpu['representative_interval_seconds'] >= 180
            or cpu['residual_fit_stage_seconds'] < cpu['representative_interval_seconds']
            or not math.isclose(cpu['representative_average_cores'],
                cpu['measured_cpu_seconds']/cpu['representative_interval_seconds'],abs_tol=1e-9)):
        raise ValueError('CPU average requires the measured representative interval, not the full stage wall time')
    if (cpu['minimum_admitted_capacity'],cpu['maximum_admitted_capacity']) != (1,24):
        raise ValueError('Do not replace variable safe admission with requested capacity')
    cost = d['cost']
    if cost['actual_billed_cost_usd'] is not None or cost['nba_allocated_cost_usd'] is not None or cost['compute_guard_usd'] != 200:
        raise ValueError('The whole-instance wall estimate is not an invoice or NBA allocation')
    prep = d['b101_preparation']
    zero_fields = ('owner_executions','new_estimator_fits','new_calibration_fits','new_meta_model_fits',
                   'new_residual_distribution_fits','new_inference_rows','new_provider_requests','research_launched')
    if any(prep[k] for k in zero_fields) or prep['owner_cpu_acceptance'] != 'NOT_RUN':
        raise ValueError('B101 preparation cannot claim real owner execution or fitting')
    if prep['status'] not in {'IN_PREPARATION','PREPARED_VERIFIED'}:
        raise ValueError('Unknown B101 preparation state')
    if prep['status'] == 'PREPARED_VERIFIED' and (prep['packaged_verification'] != 'VERIFIED'
            or prep['private_staging_verification'] != 'VERIFIED'):
        raise ValueError('Completed preparation requires packaged and private staging verification')
    if (prep['default_scientific_workers'],prep['opportunistic_scientific_workers'],prep['native_threads_per_worker'],
            prep['log_interval_seconds'],prep['occupancy_minimum_percent'],prep['occupancy_interval_seconds']) != (12,24,1,10,75,180):
        raise ValueError('Preserve the requested finite worker and measurement policy')
    if not all(prep[k] for k in ('explicit_max_workers_is_hard_ceiling','occupancy_gate_is_conditional',
            'completed_states_reused','latest_checkpoint_resolved_at_owner_launch')):
        raise ValueError('A later owner launch must preserve bounded admission and exact checkpoint reuse')
    if ([r['registered_maximum'] for r in prep['planned_branches']] != [None,320,240,162,216,480,None]
            or any(r['status'] != 'PLANNED_NOT_EXECUTED' for r in prep['planned_branches'])):
        raise ValueError('Registered maxima are not completed fit counts')
    contract = d['scientific_contract']
    if contract['selection_weights'] != [[50,50],[40,60],[30,70],[20,80],[10,90]] or contract['primary_validation_weight'] != [50,50]:
        raise ValueError('All five selection-only validation ratios must remain declared')
    if any(contract[k] for k in ('selection_weights_refit_estimators','training_rows_reweighted_by_season',
            'test_outcomes_choose_models_or_calibration','prior_test_exposure_can_be_erased',
            'full_precision_metrics_recomputed_from_public_values')):
        raise ValueError('Preserve frozen selection, no season-row reweighting and prior test exposure')
    if d['publication']['new_public_forecast_values'] or d['publication']['historical_assets_changed'] or d['publication']['production_promotion'] != 'NONE':
        raise ValueError('This addition publishes aggregates and does not change forecasts or promote production')
    serialized=json.dumps(d)
    if re.search(r's3://|/home/|/workspace/|arn:aws:|AKIA[A-Z0-9]{16}|\.pyz\b|\b[a-f0-9]{64}\b|\b(?:model_id|base_id|feature_names|ordered_feature_names|fit_identity|component_refs)\b',serialized,re.I):
        raise ValueError('Private recipe identities, locations, executable packages and hashes are excluded')
    return d


def render(data):
    d=validate(data); e=html.escape
    actual,pop,findings,cpu,prep=(d[k] for k in ('b100_actual','population','distribution_findings','cpu','b101_preparation'))
    rows=[]
    for r in d['selected_research_roles']:
        vals=[('Horizon',f"T{r['horizon_minutes']}"),('Model family',r['model_family'])]
        vals += [(s.replace('-','–'),f"{r['annual'][s]['value']:.6f}") for s in SEASONS]
        vals += [('50/50 validation',f"{r['primary_validation_score']:.6f}")]
        cells=''.join(f'<td data-label="{e(label)}">{e(value)}</td>' for label,value in vals)
        rows.append(f'<tr data-horizon="{r["horizon_minutes"]}"><th scope="row">{e(LABELS[r["role"]])}<small>{"Higher is better" if r["higher_is_better"] else "Lower is better"}</small></th>{cells}</tr>')
    plan=''.join(f'<tr><th scope="row">{e(r["branch"])}</th><td data-label="Registered maximum">{r["registered_maximum"] if r["registered_maximum"] is not None else "—"}</td><td data-label="Planned work">{e(r["unit"])}</td><td data-label="Fit accounting">{e(r["new_fit_type"])}</td></tr>' for r in prep['planned_branches'])
    sources=''.join(f'<li><strong>{e(r["source"])}</strong><span>{e(r["status"])}</span></li>' for r in findings['source_comparisons'])
    gaps=''.join(f'<li>{e(value)}</li>' for value in d['scientific_contract']['remaining_gaps'])
    embedded=json.dumps(d,ensure_ascii=False,indent=2).replace('<','\\u003c')
    prep_label='Prepared and verified; owner execution pending' if prep['status']=='PREPARED_VERIFIED' else 'In preparation; packaged and staging verification pending'
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>NBA B101 research review · Actual B100 completion and next campaign</title>
<meta name="description" content="Actual NBA B100 fits, identical retained populations, selected-role metrics, known census omissions and the separate planned B101 research campaign.">
<style>
:root{{color-scheme:light;--ink:#1e343b;--muted:#566a70;--line:#d7dfd9;--paper:#f4f6f1;--deep:#153941;--green:#235b49;--amber:#995022}}*{{box-sizing:border-box}}body{{margin:0;background:var(--paper);color:var(--ink);font:16px/1.6 system-ui,-apple-system,"Segoe UI",sans-serif}}a{{color:var(--green);text-underline-offset:4px}}a:focus-visible,button:focus-visible,input:focus-visible,summary:focus-visible,[tabindex]:focus-visible{{outline:3px solid #b16b19;outline-offset:4px}}.wrap{{max-width:1220px;margin:0 auto;padding:0 30px}}header{{background:var(--deep);color:#fff;padding:25px 0 45px}}.mast{{display:flex;justify-content:space-between;gap:20px;font-size:12px;letter-spacing:.1em;text-transform:uppercase;margin-bottom:30px}}.mast a{{color:inherit}}.eyebrow{{color:#e4c89e;font-size:12px;letter-spacing:.13em;font-weight:750;text-transform:uppercase}}h1{{max-width:1020px;font-size:clamp(36px,4.5vw,58px);letter-spacing:-.04em;line-height:1.1;margin:12px 0 20px}}.intro{{max-width:940px;font-size:18px;color:#e0e8e5}}.pill{{display:inline-block;border:1px solid #8aa9a1;color:#ebf4ea;padding:5px 11px;border-radius:4px;font-size:13px;font-weight:700}}main{{padding-top:25px!important;padding-bottom:40px!important}}.cards{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:24px}}.card,.panel{{background:#fff;border:1px solid var(--line);border-radius:7px;padding:24px}}.card strong{{display:block;font-size:36px;letter-spacing:-.03em;line-height:1.2}}.card span{{display:block;font-size:13px;color:var(--muted);margin-top:8px}}.panel{{margin-bottom:24px}}.panel.warn{{border-top:4px solid var(--amber)}}h2{{font-size:25px;letter-spacing:-.02em;line-height:1.25;margin:0 0 15px}}h3{{font-size:18px;line-height:1.3;margin:22px 0 10px}}p{{margin:0 0 14px}}p:last-child{{margin-bottom:0}}small,.muted{{color:var(--muted)}}small{{display:block;font-size:12px;font-weight:400}}.columns{{display:grid;grid-template-columns:1fr 1fr;gap:24px}}.columns .panel{{height:100%}}.columns{{margin-bottom:24px}}.columns .panel{{margin-bottom:0}}.notice{{padding:15px 18px;background:#fff2df;border-left:3px solid #ad682b;margin:16px 0}}.links{{display:flex;flex-wrap:wrap;gap:13px 24px;margin-top:20px}}button{{font:inherit;background:var(--green);color:#fff;border:1px solid var(--green);border-radius:4px;padding:10px 15px;cursor:pointer}}button.secondary{{background:white;color:var(--green)}}.controls{{display:flex;align-items:center;justify-content:space-between;gap:16px;flex-wrap:wrap;margin:18px 0}}fieldset{{padding:0;border:0;margin:0;display:flex;gap:16px;align-items:center;flex-wrap:wrap}}legend{{font-size:13px;font-weight:700;margin-bottom:5px}}label{{cursor:pointer;font-size:14px}}input{{accent-color:var(--green);margin-right:5px}}.scroll{{overflow-x:auto;max-width:100%}}table{{border-collapse:collapse;width:100%;font-size:14px}}th,td{{padding:12px 9px;text-align:left;vertical-align:top;border-bottom:1px solid var(--line)}}thead th{{font-size:12px;font-weight:700;color:var(--muted)}}tbody th{{min-width:135px}}.metrics td{{font-variant-numeric:tabular-nums;white-space:nowrap}}.metrics td:nth-child(3){{white-space:normal;min-width:135px}}.metrics tbody tr[hidden]{{display:none!important}}.sources{{list-style:none;padding:0;display:grid;grid-template-columns:1fr 1fr;gap:16px}}.sources li{{border-left:3px solid #b7c8bd;padding:3px 0 3px 13px;margin:0}}.sources span{{display:block;font-size:14px;color:var(--muted)}}ul,ol{{padding-left:22px;margin:10px 0}}li{{margin:9px 0}}.facts{{display:grid;grid-template-columns:1fr auto;gap:9px 16px;margin:16px 0}}.facts dt{{color:var(--muted)}}.facts dd{{margin:0;text-align:right;font-weight:650;font-variant-numeric:tabular-nums}}.status-line{{font-size:13px;font-weight:700;color:var(--amber)}}footer{{font-size:13px;color:var(--muted);border-top:1px solid var(--line);padding-top:20px}}.noscript{{padding:12px;border:1px solid var(--line);margin:10px 0}}[hidden]{{display:none!important}}@media(max-width:760px){{.wrap{{padding:0 18px}}.mast{{display:block}}.mast span{{display:block;margin-top:8px}}.cards{{grid-template-columns:1fr 1fr;gap:10px}}.card,.panel{{padding:18px}}.card strong{{font-size:31px}}.columns{{grid-template-columns:1fr}}h1{{font-size:38px}}.sources{{grid-template-columns:1fr}}.mobile-cards thead{{display:none}}.mobile-cards,.mobile-cards tbody,.mobile-cards tr,.mobile-cards th,.mobile-cards td{{display:block;width:100%}}.mobile-cards tr{{border-bottom:2px solid var(--line);padding:10px 0}}.mobile-cards tbody th{{padding:7px 0 10px;font-size:16px}}.mobile-cards td{{padding:5px 0;border:0;display:grid;grid-template-columns:minmax(118px,1fr) minmax(0,1.2fr);gap:10px;white-space:normal!important;overflow-wrap:anywhere;min-width:0!important}}.mobile-cards td::before{{content:attr(data-label);color:var(--muted);font-size:12px;font-weight:650}}.mobile-cards small{{display:inline-block;margin-left:8px}}.scroll:has(.mobile-cards){{overflow:visible}}.controls{{display:block}}.controls .links{{margin-top:12px}}fieldset{{gap:18px}}.facts{{font-size:14px;grid-template-columns:minmax(0,1.3fr) minmax(0,1fr)}}.facts dd{{overflow-wrap:anywhere}}}}
/* Preserve full text at narrow widths; never conceal overflow with clipping. */
.card,.panel,.columns>*{{min-width:0}}.panel,.card,header,footer{{overflow-wrap:anywhere}}.links>*{{min-width:0;max-width:100%;white-space:normal;overflow-wrap:anywhere}}button{{max-width:100%;white-space:normal;overflow-wrap:anywhere}}
@media(max-width:760px){{.mobile-cards caption{{display:block;width:100%;max-width:100%;text-align:left;overflow-wrap:anywhere}}.columns{{grid-template-columns:minmax(0,1fr)}}.links{{align-items:flex-start}}}}
@media print{{header{{background:white;color:black}}.intro,.eyebrow,.mast a{{color:inherit}}button,.controls{{display:none}}.panel,.card{{break-inside:avoid}}.metrics tbody tr[hidden]{{display:table-row!important}}}}
</style></head><body>
<header><div class="wrap"><div class="mast"><a href="../README.md">Sports Edge Lab · NBA</a><span>Evidence through November 18, 2026 · 1:16 PM Pacific</span></div>
<div class="eyebrow">Actual execution / scientific qualifications / next research</div>
<h1>B100 completed its campaign.<br>B101 extends the research.</h1>
<p class="intro">The latest audited owner run completed all 320 new distribution heads and current forecasts for 5,808 saved point-model variants. The retained game populations match across contenders. Fourteen missing validation games and other V13 qualifications still need work.</p>
<span class="pill">Registered B100 campaign complete · V13 program incomplete</span></div></header>
<main class="wrap">
<section class="cards" aria-label="Verified B100 headline counts"><div class="card"><strong data-metric="distribution-fits">320</strong><span>New residual-distribution fits in B100</span></div><div class="card"><strong data-metric="point-variants">5,808</strong><span>Current point-model variants completed</span></div><div class="card"><strong data-metric="completed-games">210</strong><span>Completed 2026–27 games scored</span></div><div class="card"><strong data-metric="cpu-passes">0</strong><span>Full three-minute CPU occupancy passes</span></div></section>
<section class="panel" aria-labelledby="actual-title"><h2 id="actual-title">What actually completed</h2>
<p>B100 added <strong>320 residual-distribution fits</strong>, with <strong>zero new base-estimator fits, zero new calibration fits, zero failed jobs and zero provider requests</strong>. The original estimators and calibrators were reused. Current frozen inference completed all 5,808 variants across <strong>210 completed games and 990 upcoming games</strong>.</p>
<p>The saved ledgers contain <strong>1,219,680 completed-game prediction rows</strong> and <strong>5,749,920 upcoming-game prediction rows</strong>. These counts are candidate-game rows, not distinct games. Later reconstruction and current inference do not acquire an original historical issue time.</p>
<p class="muted">This review covers one authenticated B100 execution. Earlier B095–B099 failures and historical fit receipts remain separate dated evidence. No new per-game forecast values are published by this status update.</p></section>
<section class="panel warn" aria-labelledby="cohort-title"><h2 id="cohort-title">Identical populations, with known census gaps</h2>
<p>All <strong>5,808 point variants and 320 distribution heads</strong> share the same saved completed-game identities for each season below. These are the populations used by every metric shown here.</p>
<div class="scroll"><table class="mobile-cards cohorts"><thead><tr><th scope="col">Season and role</th><th scope="col">Saved evaluation games</th><th scope="col">Source-supported count</th><th scope="col">Known omissions / qualification</th></tr></thead><tbody>
<tr><th scope="row">2024–25 validation</th><td data-label="Saved games">1,314</td><td data-label="Source-supported">1,321</td><td data-label="Remaining gap">6 play-in games + 1 Cup final; expanded population not yet rescored</td></tr>
<tr><th scope="row">2025–26 validation</th><td data-label="Saved games">1,315</td><td data-label="Source-supported">1,322</td><td data-label="Remaining gap">6 play-in games + 1 Cup final; expanded population not yet rescored</td></tr>
<tr><th scope="row">2026–27 exposed test</th><td data-label="Saved games">210</td><td data-label="Source-supported">Independent full census not yet verified</td><td data-label="Remaining gap">990 upcoming games are forecast, not completed test observations</td></tr></tbody></table></div>
<div class="notice"><strong>The 14 newly identified validation games have no scores in the table below.</strong> B101 must reconcile their authentic identities, infer from the frozen historical models, and rescore all contenders on one expanded manifest. A source-supported extension does not by itself prove a complete independent calendar or historical point-in-time availability.</div></section>
<section class="panel" aria-labelledby="metrics-title"><h2 id="metrics-title">Saved validation-selected research roles</h2>
<p>Each row follows the same already selected model across the two validation seasons and the <strong>210-game, previously exposed 2026–27 test population</strong>. Selection uses the saved <strong>50/50 annual validation</strong> policy. Test outcomes do not choose the displayed nominee. These are <strong>research nominees; no qualified full-season champion</strong> is claimed.</p>
<div class="controls"><fieldset id="horizon-controls" hidden><legend>Forecast horizon</legend><label><input type="radio" name="horizon" value="60">T60</label><label><input type="radio" name="horizon" value="120">T120</label><label><input type="radio" name="horizon" value="all" checked>Both horizons</label></fieldset><div class="links"><button class="secondary" id="download-metrics" hidden>Download visible metrics CSV</button></div></div>
<p id="metric-summary" class="muted" role="status" aria-live="polite">14 selected research roles · both horizons</p>
<div class="scroll"><table class="mobile-cards metrics"><caption class="muted">Annual denominators: 1,314 / 1,315 / 210. Values are rounded saved aggregates; the full-precision private metrics determine ranks.</caption><thead><tr><th scope="col">Objective</th><th scope="col">Horizon</th><th scope="col">Model family</th><th scope="col">2024–25</th><th scope="col">2025–26</th><th scope="col">2026–27 test</th><th scope="col">50/50 validation</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div>
<p class="muted" style="margin-top:15px">Within-season RMSE pools squared errors before taking the square root. The declared policy then averages the two annual RMSE values. The 40/60, 30/70, 20/80 and 10/90 sensitivity policies change evaluation weights only; they do not refit an estimator or change its base predictions.</p></section>
<div class="columns"><section class="panel warn" aria-labelledby="negative-title"><h2 id="negative-title">A substantive distribution finding</h2><p>All <strong>160 empirical heads</strong> assign zero mass to at least one observed validation result. Their negative log-mass loss is infinite, so they cannot win that objective. All <strong>160 Gaussian heads</strong> have finite saved validation log-mass scores.</p><p>The <strong>3,925 validation head-game zero-mass losses</strong> count repeated games across different heads. They are not 3,925 unique games. Empirical heads remain eligible for CRPS and interval-score objectives.</p><p>B101 registers 480 fixed empirical/Gaussian compositions to test positive tails while retaining all 320 original fitted states. Those compositions require <strong>zero new fits</strong>; any improvement remains unmeasured until execution.</p></section>
<section class="panel" aria-labelledby="cpu-title"><h2 id="cpu-title">Measured CPU, with its actual interval</h2><dl class="facts"><dt>Requested worker ceiling</dt><dd>24</dd><dt>Peak fitting worker processes</dt><dd>24</dd><dt>Residual-fit stage wall time</dt><dd>{cpu['residual_fit_stage_seconds']:.2f} seconds</dd><dt>Representative measured interval</dt><dd>{cpu['representative_interval_seconds']:.2f} seconds</dd><dt>Measured CPU / wall average</dt><dd>{cpu['representative_average_cores']:.2f} cores</dd><dt>Safe admitted capacity during interval</dt><dd>1–24 cores</dd><dt>Occupancy of admitted capacity</dt><dd>{cpu['occupancy_of_admitted_capacity']*100:.2f}%</dd><dt>Full three-minute passes</dt><dd>0</dd></dl><p><strong>The requested sustained 12–24-core execution is not yet demonstrated by B100.</strong> The current frozen-inference dispatch lasted 178.08 seconds. Neither a short stage nor a peak process count establishes the conditional 75%-occupancy / three-minute gate.</p><p class="muted">The through-delivery whole-instance wall estimate is USD {d['cost']['whole_instance_wall_estimate_usd']:.6f} at USD 2.57/hour. Actual invoiced cost and NBA allocation are unknown. The USD 200 guard is a ceiling, not reported spending.</p></section></div>
<section class="panel" aria-labelledby="sources-title"><h2 id="sources-title">Market comparisons remain qualified separately</h2><p>The saved distribution campaign has <strong>zero qualified exact-line comparison cells</strong>. Historical quote coverage and exact source/settlement admission are different requirements. Missing comparisons remain unavailable.</p><ul class="sources">{sources}</ul></section>
<section class="panel" aria-labelledby="plan-title"><div class="status-line">B101 · {e(prep_label)}</div><h2 id="plan-title">The registered next campaign</h2><p><strong>Every B101 branch below is planned and unexecuted.</strong> B101 preparation has run zero owner research, zero real NBA fits and zero inference rows. The counts are finite maxima; reused states and numerically equivalent recipes reduce actual new fits.</p><div class="scroll"><table class="mobile-cards plan"><thead><tr><th scope="col">Branch</th><th scope="col">Registered maximum</th><th scope="col">Planned work</th><th scope="col">Fit accounting</th></tr></thead><tbody>{plan}</tbody></table></div><p style="margin-top:16px">New fitting uses authenticated prevalidation history. Learned combinations use chronological heldout predictions; residual calibration uses a later disjoint prevalidation partition. The two validation seasons select models, and fitted components are locked before test reporting. Previously inspected test results remain exposed.</p><p>The owner launch requests 12 scientific workers by default, opportunistically up to 24 when configured and safely admitted. An explicit maximum is a hard ceiling. Native threads stay bounded, independent progress logs run every 10 seconds, and the latest durable checkpoint is resolved again at launch. Completed identities must be reused.</p></section>
<section class="panel warn" aria-labelledby="remaining-title"><h2 id="remaining-title">V13 requirements still unfinished</h2><ol>{gaps}</ol></section>
<section class="panel" aria-labelledby="publication-title"><h2 id="publication-title">Publication and evidence status</h2><p><strong>B100 registered science complete; V13 incomplete. B101 owner execution pending. No production promotion.</strong> This public addition is in source review; main integration pending, website deployment pending. Publishing source does not refresh models or deploy a hosted page.</p><p>Only sanitized aggregates and coarse selected-role families appear here. Exact feature transforms, fitted states, private identifiers, source payloads, checkpoints and storage locators remain excluded.</p><div class="links"><button id="download-status" hidden>Download aggregate evidence JSON</button><a href="b101_execution_status.json">Open aggregate JSON</a><a href="b100_execution_status.html">Dated B100 preparation / B099 execution record</a><a href="b099_execution_status.html">Dated B099 preparation / B098 failure record</a><a href="b098_execution_status.html">Dated B098 preparation / B097 record</a></div><noscript><p class="noscript">All fourteen roles and the complete status remain visible without JavaScript. Use the aggregate JSON link to inspect the underlying public evidence.</p></noscript></section>
<footer>Research-only analytical review. Rounded saved aggregates do not establish prospective superiority or a wagering decision. Original issues, later reconstruction, selection, publication and production remain distinct.</footer>
</main><script type="application/json" id="aggregate-evidence">{embedded}</script><script>
(()=>{{'use strict';const data=JSON.parse(document.getElementById('aggregate-evidence').textContent);let horizon='all';
const save=(name,body,type)=>{{const url=URL.createObjectURL(new Blob([body],{{type}}));const a=document.createElement('a');a.href=url;a.download=name;document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);}};
const selected=()=>data.selected_research_roles.filter(r=>horizon==='all'||String(r.horizon_minutes)===horizon);
document.getElementById('horizon-controls').hidden=false;document.querySelectorAll('input[name="horizon"]').forEach(input=>input.addEventListener('change',()=>{{horizon=input.value;document.querySelectorAll('.metrics tbody tr').forEach(row=>row.hidden=horizon!=='all'&&row.dataset.horizon!==horizon);document.getElementById('metric-summary').textContent=selected().length+' selected research roles · '+(horizon==='all'?'both horizons':'T'+horizon);}}));
const full=document.getElementById('download-status');full.hidden=false;full.addEventListener('click',()=>save('b101_execution_status.json',JSON.stringify(data,null,2)+'\\n','application/json'));
const csv=document.getElementById('download-metrics');csv.hidden=false;csv.addEventListener('click',()=>{{const header=['objective','horizon_minutes','model_family','validation_2024_25_n','validation_2024_25_value','validation_2025_26_n','validation_2025_26_value','test_2026_27_n','test_2026_27_value','primary_50_50_validation','test_selected'];const lines=[header,...selected().map(r=>[r.role,r.horizon_minutes,r.model_family,r.annual['2024-25'].n,r.annual['2024-25'].value,r.annual['2025-26'].n,r.annual['2025-26'].value,r.annual['2026-27'].n,r.annual['2026-27'].value,r.primary_validation_score,false])];const quote=v=>'"'+String(v).replaceAll('"','""')+'"';save('b101_selected_roles_'+horizon+'.csv',lines.map(row=>row.map(quote).join(',')).join('\\r\\n')+'\\r\\n','text/csv');}});
}})();</script></body></html>'''


def self_test(data):
    validate(data)
    mutations = [
        lambda d:d.update(full_v13_complete=True),
        lambda d:d.update(execution_complete=False),
        lambda d:d['b100_actual'].update(new_estimator_fits=320),
        lambda d:d['b100_actual'].update(strict_original_issuance_claimed=True),
        lambda d:d['population'].update(full_independent_census_verified=True),
        lambda d:d['population'].update(proposed_extension_rescored=True),
        lambda d:d['population']['seasons'][0].update(retained_completed_games=1321),
        lambda d:d['selected_research_roles'][0]['annual']['2026-27'].update(n=206),
        lambda d:d['selected_research_roles'][0].update(test_selected=True),
        lambda d:d['selected_research_roles'].pop(),
        lambda d:d['distribution_findings'].update(zero_mass_count_is_unique_games=True),
        lambda d:d['distribution_findings'].update(qualified_exact_line_comparison_cells=1),
        lambda d:d['cpu'].update(measured_full_interval_passes=1),
        lambda d:d['cpu'].update(representative_interval_seconds=d['cpu']['residual_fit_stage_seconds']),
        lambda d:d['cost'].update(actual_billed_cost_usd=0.48),
        lambda d:d['b101_preparation'].update(owner_executions=1),
        lambda d:d['b101_preparation'].update(new_meta_model_fits=162),
        lambda d:d['b101_preparation']['planned_branches'][0].update(status='COMPLETE'),
        lambda d:d['scientific_contract'].update(selection_weights_refit_estimators=True),
        lambda d:d['scientific_contract'].update(training_rows_reweighted_by_season=True),
        lambda d:d['publication'].update(new_public_forecast_values=1),
        lambda d:d['evidence'].update(private_path='/home/private-owner/record'),
        lambda d:d['evidence'].update(private_identity='a'*64),
    ]
    for mutation in mutations:
        bad=copy.deepcopy(data);mutation(bad)
        try:validate(bad)
        except ValueError:continue
        raise AssertionError('Unsupported evidence mutation was admitted')
    return {'negative_cases_rejected':len(mutations),'real_owner_executions':0,'real_owner_fits':0}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check',action='store_true');parser.add_argument('--self-test',action='store_true')
    args=parser.parse_args();data=json.loads(SOURCE.read_text());body=render(data)
    if args.check:
        if not OUTPUT.is_file() or OUTPUT.read_text()!=body:
            raise SystemExit('Committed B101 page differs from validated aggregate evidence')
    else:OUTPUT.write_text(body)
    result={'status':'PASS','render_matches_evidence':True,'real_owner_executions':0,'real_owner_fits':0}
    if args.self_test:result.update(self_test(data))
    print(json.dumps(result,sort_keys=True))


if __name__=='__main__':main()
