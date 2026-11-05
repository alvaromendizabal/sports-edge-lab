// Source coverage never changes a saved forecast or its scored cohort.
(()=>{
 'use strict';
 const D=JSON.parse(document.getElementById('nfl-n038-source').textContent);
 const C=JSON.parse(document.getElementById('nfl-n039-current-source').textContent);
 const M=JSON.parse(document.getElementById('nfl-latest-evidence').textContent);
 const get=id=>document.getElementById(id);
 const esc=x=>String(x).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const names={winner:'Winner reference',margin:'Margin condition',total:'Total condition'};
 function render(){
  const period=get('provider-review-period').value,upcoming=period==='week9',denominator=upcoming?15:period==='2026'?121:285;
  get('three-provider-cards').innerHTML=['DraftKings','Kalshi','Polymarket'].map(provider=>{
   const rows=upcoming?C.coverage.filter(r=>r.provider===provider):D.historical_coverage.filter(r=>r.provider===provider&&r.season===Number(period));
   const missing=provider==='DraftKings'&&!upcoming;
   let html='<article class="card" data-review-provider="'+provider+'"><span class="tag">'+(upcoming?'Dated Week 9 references':'Latest pregame source review')+'</span><h3>'+provider+'</h3><dl>';
   for(const target of ['winner','margin','total']){const row=rows.find(r=>r.target===target),count=row?.covered_games??row?.available_games;html+='<dt class="fine">'+names[target]+'</dt><dd style="margin:0 0 12px;font-size:24px;font-weight:750">'+(missing?'Separate archive':esc(count)+' <span class="fine">/ '+denominator+' games</span>')+'</dd>';}
   html+='</dl><p class="fine">'+(missing?'DraftKings was not supplied to this public-only historical exporter. Its saved lines and matched performance remain available below; this is not zero provider coverage.':upcoming&&provider==='DraftKings'?'14 fresh November 5 event captures plus one explicitly retained November 4 LV–SF reference. Original quote and acquisition clocks are visible.':upcoming?'These are early-week observations, with no final-hour or executable-price claim.':'Recovered historical observations retain both pregame quote time and later acquisition time. Conditions are not projected scores.')+'</p><a href="#coverage-performance">Inspect matched performance →</a></article>';
   return html;
  }).join('');
  const matched=M.season_metrics.filter(r=>r.season===Number(period)&&r.model_id==='descriptive_feedback'&&r.target==='win'&&r.horizon==='T2');
  const fmt=(x,n=4)=>x==null?'Unavailable':Number(x).toFixed(n);
  get('three-provider-performance').innerHTML=upcoming?'<p class="scope-note">Upcoming games have no outcomes yet. Current-source coverage is not performance.</p>':matched.length?'<h3>Preserved matched winner performance · '+period+'</h3><p class="scope-note">Market-informed probability model · descriptive retrospective leader. Each row pairs the model and provider on identical events at the registered T2 cutoff. Polymarket can have a smaller event set; do not rank providers across different cohorts.</p><div class="scroll table-wrap" tabindex="0" role="region" aria-label="Three-provider matched winner performance"><table><caption class="table-caption">Model / provider values · original cohorts and metrics unchanged</caption><thead><tr><th scope="col">Provider</th><th scope="col">Common games</th><th scope="col">Correct winners</th><th scope="col">Log loss ↓</th><th scope="col">Brier ↓</th></tr></thead><tbody>'+['DraftKings','Kalshi','Polymarket'].map(provider=>{const r=matched.find(r=>r.provider===provider);if(!r)return '<tr><th scope="row">'+provider+'</th><td colspan="4">No qualified comparison in this scorecard</td></tr>';const a=r.model_metrics,b=r.provider_metrics;return '<tr><th scope="row">'+provider+'</th><td>'+a.games+'</td><td>'+a.correct+' / '+b.correct+'</td><td>'+fmt(a.log_loss)+' / '+fmt(b.log_loss)+'</td><td>'+fmt(a.brier)+' / '+fmt(b.brier)+'</td></tr>';}).join('')+'</tbody></table></div><p class="scope-note">Lower probability losses are descriptive. Calibration, uncertainty, fees and executable prices still matter; no durable or prospective betting advantage is established. Full accuracy, calibration, margin, total and disagreement views are below.</p>':'<p class="scope-note">Use the matched-performance controls below for the available historical model series. No missing score is inferred from reference coverage.</p>';
  get('three-provider-source-note').textContent=upcoming?'References cover all 15 Week 9 games for each provider and target. Kalshi and Polymarket are refreshed November 5. DraftKings has 14 fresh games plus one dated November 4 fallback. Another 13 Week 10 games have fresh DraftKings references. These observations are not qualified betting opportunities.':'This source review is separate from T1/T2 evaluation. New historical quotes do not reissue model predictions, expand an old scorecard, establish historical fills, or prove a profitable edge. Complete current source coverage does not imply complete historical seasons.';
 }
 get('provider-review-period').addEventListener('change',render);
 get('n038-run-status').textContent='Historical source export retained through '+D.as_of+'. Current references refreshed through '+C.as_of+'. New early research issues are shown as a separate stream; fitted heads and historical scorecards are preserved. Overall owner research acceptance remains false.';
 render();
})();
