"""Render saved public NBA metrics without fitting, inference or rescoring."""
from pathlib import Path
from b083_html import expand_html
import hashlib
import html
import json
import re
import sys

ROOT=Path(__file__).parent
BEGIN='<!-- NBA B077 REVIEW BEGIN -->'
END='<!-- NBA B077 REVIEW END -->'

TEMPLATE=r'''<!-- NBA B077 REVIEW BEGIN -->
<section id="b077-review" aria-labelledby="b077-title">
<style>
#b077-review{margin:28px 0;padding:22px;border:1px solid var(--line);border-radius:9px;background:#f4f8f7}
#b077-review h2{margin:8px 0 12px}#b077-review h3{margin:22px 0 10px}#b077-review .cards{margin:18px 0}
#b077-review .card{background:#fff}#b077-review .filters{margin:18px 0;align-items:end}#b077-review .filters label{min-width:135px}
#b077-review .scroll{max-height:560px;overflow:auto}#b077-review table{font-variant-numeric:tabular-nums}
#b077-review th{position:sticky;top:0;background:#e7efec;z-index:1}#b077-review th,#b077-review td{white-space:normal;min-width:90px;max-width:270px}
#b077-review [hidden]{display:none!important}#b077-review .scope{border-left:4px solid #51786b;padding:9px 13px;background:#fff}
#b077-review .missing{color:#705125}#b077-review .footnote{font-size:13px;line-height:1.55;color:#425650}
#b077-review details{background:#fff;padding:12px;margin:16px 0}#b077-review button{min-height:40px}
@media(max-width:600px){#b077-review{padding:14px}#b077-review .cards{grid-template-columns:1fr 1fr}#b077-review .filters{display:grid;grid-template-columns:1fr 1fr}#b077-review .filters label{min-width:0}}
</style>
<div class="eyebrow">NBA · B077 EVIDENCE</div>
<h2 id="b077-title">Frozen history, current replay and original issues</h2>
<p>This saved snapshot includes B077's latest recovered original forecasts and metric-specific research roles. <strong>It is not a live feed.</strong> Latest original issue: <span id="b077-issue-clock">ISSUE_CLOCK</span>. Review evidence: EVIDENCE_CLOCK.</p>
<div class="cards"><div class="card"><div class="big">ISSUED_GAMES</div><div>games with recovered original issues</div><p class="small">of OFFICIAL_GAMES observed official games</p></div><div class="card"><div class="big">CHAMPION_ROLES</div><div>active metric-specific roles</div><p class="small">historical research selection</p></div><div class="card"><div class="big">160</div><div>completed regular-season games</div><p class="small">132 supported by many replay roles</p></div><div class="card"><div class="big">6</div><div>settled original-issue games</div><p class="small">0 automatic promotions</p></div></div>
<nav aria-label="B077 evidence navigation"><a href="#b077-peaks-title">Per-season descriptive peaks</a> · <a href="#b077-metrics-title">Season and policy metrics</a> · <a href="#b077-venues-title">Named-venue comparisons</a> · <a href="#b077-gates-title">Nomination and promotion gates</a> · <a href="#forecast-rows">All observed games and forecasts</a> · <a href="#champion-rows">Latest historical champions</a></nav>
<p class="scope"><strong>The evidence classes stay separate.</strong> Completed 2024–25 and 2025–26 scores are exposed historical research. Current fixed-state replay is retrospective. Saved frozen and weekly arrays retain their original qualification limits. Original issued rolling forecasts keep their actual issue clocks; early outlooks do not become nominal T60/T120 forecasts.</p>
<h3 id="b077-peaks-title">Best saved values within each historical season</h3>
<p>These are <strong>28 descriptive numerical peak groups</strong> from the exposed historical record, each with 1,230 regular-season games. A season's best saved value can belong to a different model from the preselected two-season champion. Tied saved rows are combined by coarse family; no new metrics are scored and no model is promoted.</p>
<div class="filters" aria-label="Historical peak filters"><label>Peak season<select id="b077-peak-season"><option value="all">Both historical seasons</option><option value="2024-25">2024–25</option><option value="2025-26">2025–26</option></select></label><label>Nominal horizon<select id="b077-peak-horizon"><option value="all">T60 and T120</option><option value="60">T60</option><option value="120">T120</option></select></label><label>Peak target<select id="b077-peak-target"><option value="all">All targets</option><option value="winner">Winner probability</option><option value="margin">Home point margin</option><option value="total">Total points</option></select></label></div>
<p id="b077-peak-count" class="small" aria-live="polite"></p>
<div class="scroll"><table id="b077-peaks"><thead><tr><th>Season</th><th>Horizon / target</th><th>Metric</th><th>Coarse family / ties</th><th>Best saved value</th><th>Games</th></tr></thead><tbody></tbody></table></div>
<p class="footnote">Higher accuracy is better; lower log loss, Brier, MAE and RMSE are better. These extrema were identified after the historical outcomes were exposed. Equal season, horizon and game counts do not prove identical game sets; the saved denominator contract still requires exact game reconciliation. This panel does not establish paired superiority, an independent test or a production selection.</p>
<h3 id="b077-metrics-title">Metrics by season, model role and policy</h3>
<div class="filters" aria-label="B077 metric filters">
<label>Season<select id="b077-season"><option value="2026-27">2026–27 current</option><option value="2024-25">2024–25</option><option value="2025-26">2025–26</option><option value="all">All saved seasons</option></select></label>
<label>Evidence policy<select id="b077-track"><option value="all">All separate policies</option><option value="FROZEN_HISTORICAL">Frozen historical roles</option><option value="CURRENT_FIXED_STATE_REPLAY">Current fixed-state replay</option><option value="SAVED_SEASON_FROZEN_ARRAY">Saved season-frozen arrays</option><option value="SAVED_WEEKLY_CURRENT_ARRAY">Saved weekly-current arrays</option><option value="ORIGINAL_ISSUED_ROLLING">Original issued rolling</option></select></label>
<label>Target<select id="b077-target"><option value="winner">Winner probability</option><option value="margin">Home point margin</option><option value="total">Total points</option><option value="all">All targets</option></select></label>
<label>Phase<select id="b077-phase"><option value="regular">Regular season</option><option value="postseason">Postseason</option><option value="all">All phases</option></select></label>
<label>Nominal horizon<select id="b077-horizon"><option value="all">T60 and T120</option><option value="60">T60</option><option value="120">T120</option></select></label>
<button type="button" id="b077-export">Export shown metrics</button></div>
<p id="b077-metric-count" class="small" aria-live="polite"></p>
<p class="footnote">Metrics are copied from saved owner aggregates and rounded to six decimal places in the public evidence. Integer counts remain exact. Support is scored games / the relevant completed-game denominator. Repeated roles, revisions and horizons are not independent games. No ranking combines different evidence policies or missing-game cohorts.</p>
<div class="scroll"><table id="b077-metrics"><thead><tr><th>Season / policy</th><th>Research role / family</th><th>Target / horizon</th><th>Support</th><th>Accuracy</th><th>Log loss</th><th>Brier</th><th>MAE</th><th>RMSE</th><th>Qualification / missingness</th></tr></thead><tbody></tbody></table></div>
<p id="b077-metric-empty" class="missing" hidden>No saved rows match these filters. No score is inferred.</p>
<h3 id="b077-venues-title">DraftKings, Kalshi and Polymarket comparisons</h3>
<p>Model and venue cells use the same matched games. Kalshi and Polymarket entries are <strong>raw binary bid/ask midpoint references</strong>; fair no-vig probability is not established. Winner contracts do not supply an expected margin or total-points benchmark.</p>
<div class="filters" aria-label="B077 venue filters"><label>Comparison season<select id="b077-venue-season"><option value="2026-27">2026–27 current</option><option value="2024-25">2024–25</option><option value="2025-26">2025–26</option></select></label><label>Venue<select id="b077-provider"><option value="all">All named venues</option><option value="DRAFTKINGS">DraftKings</option><option value="KALSHI">Kalshi</option><option value="POLYMARKET_US">Polymarket US</option><option value="POLYMARKET_INTERNATIONAL">Polymarket international</option></select></label><label>Nominal horizon<select id="b077-venue-horizon"><option value="all">T60 and T120</option><option value="60">T60</option><option value="120">T120</option></select></label><label>Actual issue timing<select id="b077-venue-timing"><option value="all">All saved classes</option><option value="EARLY_OUTLOOK">Early outlook</option><option value="NOMINAL">Nominal horizon</option><option value="LATE">Late horizon, pregame</option></select></label></div>
<div id="b077-provider-cards" class="cards"></div>
<p id="b077-venue-count" class="small" aria-live="polite"></p>
<div class="scroll"><table id="b077-venues"><thead><tr><th>Venue</th><th>Selected role</th><th>Horizon / actual timing</th><th>Matched / model games</th><th>Accuracy · model / venue</th><th>Log loss · model / venue</th><th>Brier · model / venue</th><th>Independent week blocks</th></tr></thead><tbody></tbody></table></div>
<p id="b077-venue-empty" class="missing" hidden>No admitted selected comparison exists for this selection. Missing scores are unavailable, not zero.</p>
<p class="footnote">There is no complete 2024–25, 2025–26 or current-season named-venue ranking in this export. The nonempty current comparisons have at most one week block. Quote-clock ranges are not included in these aggregate rows; original issue/source clocks remain in the game table. The latest B077 source capture does not redetermine the cutoff of an earlier comparison.</p>
<h3 id="b077-gates-title">What qualifies for nomination or production review?</h3>
<p>There is no universal accuracy, log-loss or point-error cutoff. The saved policy requires support and fair comparison within a target, horizon and eligible game cohort. <strong>Historical nomination and production promotion are different decisions.</strong></p>
<div class="scroll"><table id="b077-gates"><thead><tr><th>Decision</th><th>Minimum game support</th><th>Minimum week clusters</th><th>Qualification</th></tr></thead><tbody id="b077-gate-rows"></tbody></table></div>
<p id="b077-nomination-guardrails" class="footnote"></p><p id="b077-production-guardrails" class="footnote"></p>
<p class="scope"><strong>Six settled original-issue games do not satisfy the registered production support.</strong> The historical nomination code reports paired uncertainty but does not require a positive adjusted interval for nomination. A nominated research role therefore does not itself prove an improvement. Production still requires new post-registration originally issued evidence and independent review; no automatic production promotion is authorized.</p>
<details><summary>Coverage gaps and promotion status</summary><ul id="b077-gaps"></ul><p><strong>No automatic production promotion.</strong> Historical research role selection permits prospective shadow monitoring. A new production claim needs the registered independent forward evidence and comparison gates; current retrospective scores do not satisfy that requirement.</p><p>All previously published schedule source fields and clocks are retained. The newer B077 schedule body is unavailable in this recovered return; its three aggregate-only live states are not assigned to individual games. The previous published selected snapshot remains available in <a href="history/b077_selected_outputs.json">history</a>.</p></details>
<p class="small"><a href="b078_recovered_b077_evidence.json">Saved aggregate evidence</a> · <a href="latest_research_outputs.json">All observed games and selected issues</a> · <a href="build_b077_review.py">Deterministic display renderer</a></p>
<script id="b077-evidence" type="application/json">REVIEW_JSON</script>
<script id="b077-peak-evidence" type="application/json">PEAK_JSON</script>
<script>
(()=>{'use strict';const R=JSON.parse(document.getElementById('b077-evidence').textContent),P=JSON.parse(document.getElementById('b077-peak-evidence').textContent),q=id=>document.getElementById(id);
const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const words=v=>String(v??'').replaceAll('_',' ').toLowerCase(),names={DRAFTKINGS:'DraftKings',KALSHI:'Kalshi',POLYMARKET_US:'Polymarket US',POLYMARKET_INTERNATIONAL:'Polymarket international'};
const tracks={FROZEN_HISTORICAL:'Frozen historical',CURRENT_FIXED_STATE_REPLAY:'Current fixed-state replay',SAVED_SEASON_FROZEN_ARRAY:'Saved season-frozen array',SAVED_WEEKLY_CURRENT_ARRAY:'Saved weekly-current array',ORIGINAL_ISSUED_ROLLING:'Original issued rolling'};
const score=(v,metric)=>typeof v!=='number'||!Number.isFinite(v)?'Unavailable':metric==='accuracy'?(100*v).toFixed(2)+'%':v.toFixed(6);
const matches=(selected,value)=>selected==='all'||String(value)===selected;
let shown=[];
function drawPeaks(){const rows=P.historical_peaks.filter(r=>matches(q('b077-peak-season').value,r.season)&&matches(q('b077-peak-horizon').value,r.horizon_minutes)&&matches(q('b077-peak-target').value,r.target));
q('b077-peaks').tBodies[0].innerHTML=rows.map(r=>'<tr data-group="'+esc(r.group_id)+'"><td>'+esc(r.season)+'</td><td>T'+r.horizon_minutes+'<br>'+esc(r.target)+'</td><td>'+esc(words(r.metric))+'</td><td>'+esc(r.families.join('; '))+'<br>'+r.tied_saved_rows+' saved row'+(r.tied_saved_rows===1?'':'s')+'</td><td>'+score(r.saved_metric_value,r.metric)+'</td><td>'+r.games+'</td></tr>').join('');q('b077-peak-count').textContent=rows.length+' descriptive historical groups; no preselected-champion or promotion claim.';}
function drawGates(){const h=P.promotion_gates.historical_nomination,p=P.promotion_gates.registered_production;
q('b077-gate-rows').innerHTML=[['Regular-season historical nomination',h.regular.minimum_games_each_season+' in each frozen season; '+h.regular.minimum_total_games+' total',h.regular.minimum_week_clusters,'Both 2024–25 and 2025–26; exposed forward-shadow nomination only'],['Postseason historical nomination',h.postseason.minimum_games_each_season+' in each frozen season; '+h.postseason.minimum_total_games+' total',h.postseason.minimum_week_clusters,'Both frozen seasons; separate postseason support'],['Registered production review',p.minimum_matched_games+' matched games',p.minimum_cluster_weeks,'New post-registration originally issued evidence and independent review; automatic promotion disabled']].map(row=>'<tr>'+row.map(value=>'<td>'+esc(value)+'</td>').join('')+'</tr>').join('');
q('b077-nomination-guardrails').textContent='Historical nomination also requires '+h.additional_requirements.join(', ')+'. Winner seasonal log loss may degrade by at most '+h.winner_maximum_season_log_loss_degradation+' versus baseline; point-target seasonal MAE by at most '+h.point_maximum_season_mae_degradation+' point. Winner ECE may exceed baseline by at most '+h.winner_maximum_ece_degradation+'.';
q('b077-production-guardrails').textContent='Saved production registry: '+p.multiplicity+'. Calibration: '+p.calibration_guardrail+'. Stability: '+p.stability+'. Resampling: '+p.resampling_unit+'. These registered requirements are not a completed production-qualification result.';}
function drawMetrics(){shown=R.metric_rows.filter(r=>matches(q('b077-season').value,r.season)&&matches(q('b077-track').value,r.evidence_track)&&matches(q('b077-target').value,r.target)&&matches(q('b077-phase').value,r.phase)&&matches(q('b077-horizon').value,r.horizon_minutes));
q('b077-metrics').tBodies[0].innerHTML=shown.map((r,i)=>'<tr data-source="'+esc(r.source_section)+'" data-source-index="'+esc(r.source_index??r.source_role)+'"><td>'+esc(r.season)+'<br>'+esc(tracks[r.evidence_track])+'</td><td>'+esc(words(r.role_alias))+'<br><strong>'+esc(r.family)+'</strong></td><td>'+esc(r.target)+'<br>T'+r.horizon_minutes+(r.issue_horizon_class?'<br>'+esc(words(r.issue_horizon_class)):'')+'</td><td>'+r.scored_games+' / '+r.completed_game_denominator+'</td>'+['accuracy','log_loss','brier','mae','rmse'].map(m=>'<td>'+score(r.metrics[m],m)+'</td>').join('')+'<td>'+esc(words(r.status))+(r.lead_bucket?'<br>'+esc(words(r.lead_bucket)):'')+(r.missing_games?'<br>'+r.missing_games+' missing: '+esc(Object.keys(r.missing_reasons||{}).map(words).join('; ')):'')+'</td></tr>').join('');
q('b077-metric-count').textContent=shown.length+' saved metric rows. Each policy and cohort retains its own support.';q('b077-metric-empty').hidden=shown.length>0;window.NBA_B077_METRIC_STATE={rows:shown.length,season:q('b077-season').value,track:q('b077-track').value};}
function drawVenues(){const season=q('b077-venue-season').value,provider=q('b077-provider').value;
const coverage=R.provider_coverage.filter(r=>r.season===season&&matches(provider,r.provider));q('b077-provider-cards').innerHTML=coverage.map(r=>'<article class="card" data-provider="'+r.provider+'"><strong>'+names[r.provider]+'</strong><div class="big">'+r.maximum_matched_games_in_one_selected_view+'</div><div>maximum matched games in one saved selected view</div><p class="small">'+esc(words(r.status))+'</p></article>').join('');
const rows=R.provider_comparisons.filter(r=>r.season===season&&matches(provider,r.provider)&&matches(q('b077-venue-horizon').value,r.horizon_minutes)&&matches(q('b077-venue-timing').value,r.issue_horizon_class));
q('b077-venues').tBodies[0].innerHTML=rows.map(r=>'<tr data-source-index="'+r.source_index+'"><td>'+names[r.provider]+'</td><td>'+esc(r.role_aliases.map(words).join(', '))+'</td><td>T'+r.horizon_minutes+'<br>'+esc(words(r.issue_horizon_class))+'</td><td>'+r.model_on_same_reference_games.games+' / '+r.full_universe_games+'</td>'+['accuracy','log_loss','brier'].map(m=>'<td>'+score(r.model_on_same_reference_games[m],m)+' / '+score(r.raw_bbo_midpoint_reference[m],m)+'</td>').join('')+'<td>'+r.cluster_weeks+'<br>'+esc(words(r.uncertainty_status))+'</td></tr>').join('');
q('b077-venue-count').textContent=rows.length+' saved comparison rows; no whole-season superiority or promotion claim.';q('b077-venue-empty').hidden=rows.some(r=>r.model_on_same_reference_games.games>0);window.NBA_B077_VENUE_STATE={rows:rows.length,season,provider};}
q('b077-gaps').innerHTML=R.gap_notes.map(n=>'<li>'+esc(n)+'</li>').join('');
for(const id of ['b077-season','b077-track','b077-target','b077-phase','b077-horizon'])q(id).addEventListener('change',drawMetrics);
for(const id of ['b077-venue-season','b077-provider','b077-venue-horizon','b077-venue-timing'])q(id).addEventListener('change',drawVenues);
for(const id of ['b077-peak-season','b077-peak-horizon','b077-peak-target'])q(id).addEventListener('change',drawPeaks);
q('b077-export').addEventListener('click',()=>{const headers=['season','evidence_track','role_alias','family','target','horizon_minutes','scored_games','completed_game_denominator','accuracy','log_loss','brier','mae','rmse','status'];const cell=x=>'"'+String(x??'').replaceAll('"','""')+'"';const text=[headers,...shown.map(r=>headers.map(k=>Object.hasOwn(r.metrics,k)?r.metrics[k]:r[k]))].map(row=>row.map(cell).join(',')).join('\r\n');const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([text],{type:'text/csv;charset=utf-8'}));a.download='nba-b077-saved-metrics.csv';a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000);});
drawMetrics();drawVenues();drawPeaks();drawGates();})();
</script>
</section>
<!-- NBA B077 REVIEW END -->
'''

def render_section(evidence,data,peaks):
    replacements={
        'ISSUE_CLOCK':html.escape(data['latest_forecast_issue_at_utc']),
        'EVIDENCE_CLOCK':html.escape(evidence['evidence_as_of_utc']),
        'ISSUED_GAMES':str(data['coverage']['games_in_original_issued_inventory']),
        'OFFICIAL_GAMES':str(data['coverage']['official_schedule_games']),
        'CHAMPION_ROLES':str(data['coverage']['active_research_champion_roles']),
        'REVIEW_JSON':json.dumps(evidence,sort_keys=True,separators=(',',':'),allow_nan=False).replace('<','\\u003c'),
        'PEAK_JSON':json.dumps(peaks,sort_keys=True,separators=(',',':'),allow_nan=False).replace('<','\\u003c'),
    }
    result=TEMPLATE
    for key,value in replacements.items():result=result.replace(key,value)
    return result

def build(check=False):
    from restore_snapshot_assets import restore
    if (ROOT/'snapshot_asset_manifest.json').exists():restore(ROOT)
    path=ROOT/'latest_research_outputs.html'
    data=json.loads((ROOT/'history/b077_recovered_selected_outputs.json').read_bytes())
    evidence=json.loads((ROOT/'b078_recovered_b077_evidence.json').read_bytes())
    peaks=json.loads((ROOT/'b077_historical_peaks_and_gates.json').read_bytes())
    assert evidence['schema']=='sports-edge-lab.nba.recovered-b077-review.v1'
    current=expand_html(path.read_text())
    clean=re.sub(re.escape(BEGIN)+r'.*?'+re.escape(END)+r'\n?', '',current,flags=re.S)
    anchor='<p><a href="latest_research_outputs.json">Complete observed schedule and selected outputs</a> · <a href="validate_research_snapshot.py">Public evidence validator</a> · <a href="../README.md">NBA research history</a></p>\n'
    if clean.count(anchor)!=1:raise ValueError('The selected-output insertion point must be unique')
    result=clean.replace(anchor,anchor+render_section(evidence,data,peaks),1)
    if check:
        if result!=current:raise ValueError('Saved B077 evidence display is stale')
    else:path.write_text(result)
    return {'status':'PASS' if check else 'BUILT','metric_rows':len(evidence['metric_rows']),
        'provider_comparisons':len(evidence['provider_comparisons']),'historical_peak_groups':len(peaks['historical_peaks']),
        'html_sha256':hashlib.sha256(result.encode()).hexdigest(),'new_scoring':False}

if __name__=='__main__':print(json.dumps(build('--check' in sys.argv),sort_keys=True))
