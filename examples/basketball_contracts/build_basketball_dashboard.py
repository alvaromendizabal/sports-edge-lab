"""Build the self-contained public basketball dashboard from approved aggregates."""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / 'docs/basketball/index.html'


def load_evidence():
    directory = ROOT / 'docs/evidence'
    result = {
        'models': json.loads((directory / '2026-10-28-basketball-dashboard.json').read_text()),
        'overlap': json.loads((directory / '2026-10-28-basketball-overlap.json').read_text()),
        'recovery': json.loads((directory / '2026-10-28-basketball-b006-recovery.json').read_text()),
    }
    validate(result)
    return result


def validate(data):
    models, overlap, recovery = (data[k] for k in ('models', 'overlap', 'recovery'))
    seen = set()
    panels = {}
    for r in models['rows']:
        panel = (r['league'], r['horizon_minutes'], r['year'], r['cohort'])
        key = (*panel, r['recipe'])
        if key in seen or r['year'] not in (2025, 2026, 2027):
            raise ValueError('duplicate or unsupported scorecard')
        seen.add(key)
        if panel in panels and panels[panel] != r['n']:
            raise ValueError('different games cannot share a comparison panel')
        panels[panel] = r['n']
        if r['n'] <= 0 or r['correct'] + r['incorrect'] != r['n']:
            raise ValueError('scorecard counts do not reconcile')
        if not math.isclose(r['accuracy'], r['correct'] / r['n'], abs_tol=1e-12):
            raise ValueError('accuracy disagrees with picks')
        if r['monitoring_only'] is not (r['year'] == 2027):
            raise ValueError('monitoring boundary changed')
        if r['year'] == 2027 and (r['league'] != 'nba' or r['n'] != 52):
            raise ValueError('no expanded monitoring panel established')
        if r['recipe'] == 'MARKET_raw' and r['cohort'] != 'matched_MARKET':
            raise ValueError('MARKET must stay on its matched panel')
        if any(not math.isfinite(r[k]) for k in ('log_loss', 'brier', 'accuracy')):
            raise ValueError('finite scoring metrics required')
    if models['frozen_champions'] != {'nba/T60': 'basketball_strength', 'nba/T1440': 'basketball_strength', 'ncaam/T60': 'basketball_rich_combined', 'ncaam/T1440': 'basketball_combined', 'ncaaw/T60': 'basketball_rich_combined', 'ncaaw/T1440': 'basketball_combined'}:
        raise ValueError('retained champions changed')
    if overlap['current_2027_labels_used'] or overlap['historical_seasons'] != [2025, 2026]:
        raise ValueError('overlap investigation must remain historical')
    if len(overlap['overlap_sensitivities']) != 120:
        raise ValueError('all declared overlap sensitivities required')
    for s in overlap['overlap_sensitivities']:
        if s['covered_retained'] > s['covered_full'] or s['uncovered_retained'] > s['uncovered_full']:
            raise ValueError('retention cannot exceed available support')
        if s['status'] != 'estimated_on_common_support':
            if s.get('overlap_gap') is not None:
                raise ValueError('missing overlap cannot have an estimated gap')
            continue
        for arm in ('covered', 'uncovered'):
            if not math.isclose(s[arm + '_retention'], s[arm + '_retained'] / s[arm + '_full'], abs_tol=1e-12):
                raise ValueError('support retention mismatch')
            if not 0 < s['overlap_' + arm + '_ess'] <= s[arm + '_retained'] + 1e-8:
                raise ValueError('effective sample size exceeds retained observations')
        if not math.isclose(s['overlap_gap'], s['overlap_covered_delta'] - s['overlap_uncovered_delta'], abs_tol=1e-12):
            raise ValueError('overlap gap arithmetic')
        if set(s['intervals']) != {'7', '14'}:
            raise ValueError('both calendar-block sensitivities required')
    for row in overlap['league_year_coverage']:
        if row['covered_games'] + row['uncovered_saved_games'] != row['saved_model_games']:
            raise ValueError('coverage denominator mismatch')
    if recovery['status'] != 'SUCCESS_EVIDENCE_RECOVERY' or recovery['completed_modeling_release'] or recovery['latest_completed_real_modeling_release'] != 'B003':
        raise ValueError('recovery cannot become completed modeling')
    if any(recovery[k] != 0 for k in ('new_real_fits', 'model_inferences', 'new_external_requests', 'new_forecasts', 'new_orders')):
        raise ValueError('B006 acquired no new scientific execution')
    if recovery['forecasts']['versions'] != 330 or recovery['forecasts']['new_settlement_check']:
        raise ValueError('preserve forecasts without inventing settlement')
    budget = recovery['resources']
    if budget['additional_budget_authorized'] or budget['open_reservation_is_measured_spend']:
        raise ValueError('budget or reservation interpretation changed')
    if not math.isclose(budget['remaining_conservative_work_seconds'], budget['work_ceiling_seconds'] - budget['open_finalization_reservation_until_seconds'], abs_tol=1e-9):
        raise ValueError('conservative work remainder')
    return {'scorecards': len(seen), 'populated_panels': len(panels), 'overlap_specifications': 120}


PAGE = r'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Basketball evidence | Sports Edge Lab</title>
<style>
:root{--ink:#182940;--muted:#526176;--line:#dce3ed;--blue:#205acc;--teal:#087d70;--warm:#9a4e17;--paper:#f5f7fb}*{box-sizing:border-box}body{margin:0;font:15px/1.55 system-ui,sans-serif;color:var(--ink);background:var(--paper)}a{color:var(--blue)}header{background:#142840;color:white;padding:42px max(24px,calc((100vw - 1200px)/2)) 35px}header a{color:#bfd7ff}.eyebrow{font-size:12px;letter-spacing:.15em;text-transform:uppercase;color:#bed1ed}h1{font-size:clamp(28px,4vw,45px);line-height:1.12;margin:12px 0 16px;letter-spacing:-.025em}header p{max-width:840px;color:#d2dfef}main{max-width:1250px;margin:24px auto;padding:0 24px 50px}.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}.card,section{background:white;border:1px solid var(--line);border-radius:10px;padding:22px;margin-bottom:20px}.card strong{font-size:26px;display:block}.card span,.note,small{color:var(--muted)}h2{font-size:24px;margin:0 0 10px}h3{font-size:18px;margin:24px 0 8px}.controls{display:flex;gap:16px;flex-wrap:wrap;margin:20px 0}.controls label{font-size:12px;font-weight:650;color:var(--muted)}select{display:block;font:inherit;font-size:14px;padding:8px 32px 8px 10px;border:1px solid #bdcbdc;border-radius:5px;background:white;color:var(--ink);margin-top:5px}select:focus{outline:3px solid #bdd7ff}.banner{padding:12px 15px;background:#eef4ff;border-left:4px solid var(--blue);margin:14px 0}.warning{background:#fff7ed;border-left-color:var(--warm)}.table-wrap{overflow:auto}table{width:100%;border-collapse:collapse;font-size:13px}th{text-align:left;color:var(--muted);font-size:11px;letter-spacing:.03em;border-bottom:2px solid var(--line);white-space:nowrap;padding:9px 11px}td{padding:10px 11px;border-bottom:1px solid #edf0f4;white-space:nowrap;font-variant-numeric:tabular-nums}td.num{text-align:right}.winner td:first-child,.winner td:nth-child(3){font-weight:750;color:var(--teal)}.champion{font-size:10px;padding:2px 5px;margin-left:6px;border:1px solid #c6d5eb;border-radius:3px;color:var(--blue)}.bar-row{display:grid;grid-template-columns:170px 1fr 90px;align-items:center;gap:12px;font-size:12px;margin:11px 0}.bar-track{height:16px;background:#edf1f7;border-radius:2px}.bar{height:16px;background:var(--blue);border-radius:2px}.columns{display:grid;grid-template-columns:1fr 1fr;gap:22px}.metric{font-size:23px;font-weight:700;margin:8px 0}.badge{display:inline-block;font-size:11px;padding:3px 7px;border-radius:3px;background:#e8f4ef;color:#1e6350}.muted{color:var(--muted)}footer{padding-top:8px;color:var(--muted);font-size:12px}.empty{padding:24px;color:var(--muted)}.method{max-width:1000px}.clock{display:grid;grid-template-columns:170px 1fr;gap:12px;padding:9px 0;border-bottom:1px solid var(--line)}@media(max-width:760px){.grid,.columns{grid-template-columns:1fr}main{padding:0 14px}header{padding:30px 20px}.card{margin-bottom:0}.grid{margin-bottom:20px}.bar-row{grid-template-columns:115px 1fr 65px}section{padding:17px}.clock{grid-template-columns:1fr}}
</style></head><body>
<header><div class="eyebrow">Sports Edge Lab · Basketball · verified aggregate review</div><h1>Prediction quality needs<br>an honest comparison population.</h1><p>Inspect NBA, NCAA men and NCAA women separately. Historical scorecards, monitoring, missing MARKET support and feature availability carry distinct evidence boundaries.</p><nav><a href="../../README.md">Project</a> · <a href="../BASKETBALL_FEATURE_RELEASE.md">Feature-release contract</a> · <a href="../BASKETBALL_MARKET_COVERAGE.md">Coverage study</a> · <a href="../../notebooks/basketball_feature_release.ipynb">Executed notebook</a></nav></header>
<main><div class="grid"><div class="card"><span>Latest completed modeling release</span><strong>B003</strong><small>B004 stopped; B005/B006 completed evidence recovery.</small></div><div class="card"><span>Cumulative real estimator units</span><strong>238</strong><small>B006 added zero fits, inference or forecasts.</small></div><div class="card"><span>Archived forecast versions</span><strong>330 / 61 games</strong><small>18 files preserved; no new settlement check.</small></div></div>
<section><h2>Compare the same games</h2><p class="note">Only available saved scorecards appear. Historical numerical minima are descriptive; retained champion tags identify the frozen full-model-cohort selection, including when the matched MARKET view is shown. Neither implies a qualified MARKET edge.</p>
<div class="controls"><label>League<select id="league"><option value="nba">NBA</option><option value="ncaam" selected>NCAA men</option><option value="ncaaw">NCAA women</option></select></label><label>Forecast horizon<select id="horizon"><option value="60">T60</option><option value="1440">T1440</option></select></label><label>Season ending<select id="year"><option value="2025">2025 historical</option><option value="2026" selected>2026 historical</option><option value="2027">2027 monitoring only</option></select></label><label>Exact comparison cohort<select id="cohort"><option value="full_basketball">Full model cohort</option><option value="matched_MARKET">Matched sportsbook MARKET</option></select></label></div>
<div id="panel-status" class="banner" aria-live="polite"></div><div id="model-table" class="table-wrap"></div><p class="note">Bold identifies only the historical minimum log loss within this displayed panel. Calibration uses ten fixed bins. Point metrics are unavailable for recipes without saved score predictions. All historical seasons are development-exposed. The NBA monitoring panel is the retained 52-game retrospective cohort, not settlement of the 330 issued versions.</p></section>
<section><h2>Where the saved sportsbook archive has no support</h2><p class="note">This section follows league and season above, but always describes the historical T60 archive. “Uncovered” means no valid saved benchmark; it does not establish no real-world bookmaker offer.</p><div id="coverage-content"></div>
<h3>All declared overlap sensitivities</h3><p class="method note">Empirical coverage fractions in fixed cells define overlap weights; no propensity estimator is trained. The target population changes across methods and support thresholds. Both seven-day and fourteen-day shared-block intervals are shown. These are exploratory, unadjusted sensitivity intervals, not causal effects or tests of equivalence.</p><div id="overlap-table" class="table-wrap"></div></section>
<section><h2>A feature value needs an availability contract</h2><div class="columns"><div><p>The <a href="../../examples/basketball_contracts/feature_release.py">invented-data example</a> separates completion, publication, observation and revision clocks. Later corrections cannot rewrite a pregame snapshot. Missing original clocks stay outside strict timing.</p><div class="clock"><span>Strict protocol</span><span>Qualified original publication and local observation must both precede cutoff.</span></div><div class="clock"><span>Reconstructed research</span><span>A stated 24-hour lag is a research assumption, not authentic publication evidence.</span></div><div class="clock"><span>Same-game exclusion</span><span>The target event's outcome cannot enter its own features, even with an earlier claimed timestamp.</span></div></div><div><p class="banner warning">Synthetic clock flags are caller assertions. A passing public test does not verify any real source's publication time.</p><p>Rolling score context, opponent history, rest and evidence recency are illustrated on invented data. The public example exposes no production feature formulas, model weights or private dynamic-strength kernel.</p><a href="../../notebooks/basketball_feature_release.ipynb">Inspect the executed demonstration →</a></div></div></section>
<section><h2>What the owner recovery established</h2><div id="recovery-content"></div><p class="note">Authenticated returned bytes and ledger statements are evidence of the saved execution; they are not independent billing telemetry. The 493 preparation tests are not newly executed owner tests. Source requests are exhausted at 48/48. No new budget is active.</p></section>
<footer>All data embedded here are sanitized aggregates. No external scripts, fonts, requests or credentials. Sportsbook MARKET, Kalshi, Polymarket US and international Polymarket remain separate. No historical trading profit, order or basketball bankroll is established. Portfolio assessment: 8.5/10 before and after; improved auditability is not new predictive superiority.</footer></main>
<script id="dashboard-evidence" type="application/json">__DATA__</script><script>__SELECTORS__</script><script>
'use strict';
const evidence=JSON.parse(document.getElementById('dashboard-evidence').textContent), api=BasketballDashboard;
const f=(x,d=6)=>x===null||x===undefined?'Unavailable':Number(x).toLocaleString('en-US',{minimumFractionDigits:d,maximumFractionDigits:d});
const pct=x=>f(100*x,2)+'%';
const esc=x=>String(x).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const label=x=>x.replace(/^basketball_/,'').replaceAll('_',' ');
function table(headers,rows){return '<table><thead><tr>'+headers.map(x=>'<th>'+esc(x)+'</th>').join('')+'</tr></thead><tbody>'+rows.join('')+'</tbody></table>'}
function render(){
 const state=Object.fromEntries(['league','horizon','year','cohort'].map(k=>[k,document.getElementById(k).value]));
 const view=api.presentation(evidence.models,state);
 document.getElementById('panel-status').className='banner'+(view.monitoring?' warning':'');
 document.getElementById('panel-status').textContent=view.status+(view.games?' '+view.games.toLocaleString()+' identical games.':'');
 document.getElementById('model-table').innerHTML=view.rows.length?table(['Saved recipe','Games','Log loss','Brier','Correct / wrong','Accuracy','ECE','Margin MAE / RMSE','Total MAE / RMSE'],view.rows.map(r=>'<tr class="'+(view.winnerRecipes.includes(r.recipe)?'winner':'')+'"><td>'+esc(label(r.recipe))+(r.recipe===view.champion?'<span class="champion">Retained</span>':'')+'</td><td class="num">'+f(r.n,0)+'</td><td class="num">'+f(r.log_loss)+'</td><td class="num">'+f(r.brier)+'</td><td class="num">'+r.correct+' / '+r.incorrect+'</td><td class="num">'+pct(r.accuracy)+'</td><td class="num">'+f(r.ece_10_fixed_bins)+'</td><td class="num">'+f(r.margin_mae,3)+' / '+f(r.margin_rmse,3)+'</td><td class="num">'+f(r.total_mae,3)+' / '+f(r.total_rmse,3)+'</td></tr>')):'<div class="empty">No saved comparison for these controls.</div>';
 const coverage=evidence.overlap.league_year_coverage.find(r=>r.league===state.league&&r.year===+state.year);
 const teams=evidence.overlap.team_coverage_aggregate.find(r=>r.league===state.league&&r.year===+state.year);
 if(!coverage){document.getElementById('coverage-content').innerHTML='<p class="banner warning">2027 is monitoring-only. This historical support investigation uses no 2027 outcomes.</p>';document.getElementById('overlap-table').innerHTML='';return}
 document.getElementById('coverage-content').innerHTML='<div class="columns"><div><div class="bar-row"><span>Saved MARKET coverage</span><span class="bar-track"><span class="bar" style="display:block;width:'+100*coverage.covered_fraction_saved+'%"></span></span><strong>'+pct(coverage.covered_fraction_saved)+'</strong></div><p>'+f(coverage.covered_games,0)+' covered / '+f(coverage.saved_model_games,0)+' saved-model games. '+f(coverage.uncovered_saved_games,0)+' uncovered games remain untested against a valid saved benchmark.</p><p class="note">Canonical schedule: '+f(coverage.canonical_schedule_games,0)+' games; '+f(coverage.canonical_without_saved_model,0)+' outside this saved model cohort. Those are different denominators, not recovered forecasts.</p></div><div><div class="metric">'+teams.teams_zero_covered_appearances+' / '+teams.teams_with_saved_games+' teams</div><p>have zero covered appearances. '+coverage.zero_coverage_dates+' of '+coverage.all_game_dates+' saved-game dates have no covered game.</p><p class="note">Team appearances are not independent games. Sparse support limits generalization; zero historical strict eligibility is preserved.</p></div></div>';
 const overlap=api.overlapRows(evidence.overlap,state.league,state.year);
 document.getElementById('overlap-table').innerHTML=table(['Fixed cells','Min / arm','Trim 5–95%','Covered retained','Uncovered retained','Covered / uncovered ESS','Gap','7-day interval','14-day interval'],overlap.map(r=>{
 if(r.status!=='estimated_on_common_support')return '<tr><td>'+esc(label(r.specification))+'</td><td>'+r.minimum_per_arm+'</td><td>'+(r.trim_e_05_95?'Yes':'No')+'</td><td colspan="6">No common support; no estimate</td></tr>';
 const interval=k=>'['+r.intervals[k].gap_ci95.map(x=>f(x)).join(', ')+']';
 return '<tr><td>'+esc(label(r.specification))+'</td><td>'+r.minimum_per_arm+'</td><td>'+(r.trim_e_05_95?'Yes':'No')+'</td><td>'+pct(r.covered_retention)+'</td><td>'+pct(r.uncovered_retention)+'</td><td>'+f(r.overlap_covered_ess,1)+' / '+f(r.overlap_uncovered_ess,1)+'</td><td>'+f(r.overlap_gap)+'</td><td>'+interval('7')+'</td><td>'+interval('14')+'</td></tr>'}));
}
const b=evidence.recovery.resources;
document.getElementById('recovery-content').innerHTML='<span class="badge">B006 SUCCESS_EVIDENCE_RECOVERY</span><p>128 return pins and 423 embedded-source pins verified. 222 inherited native references reconciled without loading models. Zero new fits, inference, external requests, forecasts or orders.</p><div class="columns"><div><span class="muted">Maximum measured active floor</span><div class="metric">'+f(b.maximum_measured_active_floor_seconds,3)+' seconds</div></div><div><span class="muted">Open reservation through (not measured spend)</span><div class="metric">'+f(b.open_finalization_reservation_until_seconds,3)+' seconds</div></div></div><p class="banner warning">'+f(b.remaining_conservative_work_seconds,3)+' seconds conservative headroom is below the unchanged 60-second admission guard. Authenticate the exact closed live receipt before another useful owner batch; no extra budget is authorized.</p>';
for(const id of ['league','horizon','year','cohort'])document.getElementById(id).addEventListener('change',render);render();
</script></body></html>
'''


def render(data):
    validate(data)
    payload = json.dumps(data, separators=(',', ':'), allow_nan=False).replace('<', '\\u003c')
    selectors = (ROOT / 'examples/basketball_contracts/dashboard.js').read_text()
    return PAGE.replace('__DATA__', payload).replace('__SELECTORS__', selectors)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    data = load_evidence()
    page = render(data)
    if args.check:
        if OUTPUT.read_text() != page:
            raise SystemExit('generated basketball dashboard differs')
    else:
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT.write_text(page)
    print(json.dumps({'status': 'PASS', **validate(data), 'network_requests': 0}, sort_keys=True))


if __name__ == '__main__':
    main()
