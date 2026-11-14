"use strict";
(() => {
  const $=id=>document.getElementById(id);
  const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const pct=v=>v===null||v===undefined||!Number.isFinite(Number(v))?'—':(Number(v)*100).toFixed(2)+'%';
  const interval=v=>Array.isArray(v)?pct(v[0])+' to '+pct(v[1]):'Not established';
  const names={log_loss:'Log loss',brier:'Brier score',error_rate:'Winner error rate',mae:'MAE',rmse:'RMSE'};
  let saved=null;
  function render(){
    if(!saved)return;
    const c=saved.comparisons.find(v=>v.target===$('weighted-target').value&&v.window===$('weighted-window').value);
    $('weighted-limits').innerHTML=(saved.limitations||[]).map(x=>'<li>'+esc(x)+'</li>').join('');
    if(!c){$('weighted-cohort').textContent='No qualified weighted comparison was supplied for this view.';$('weighted-body').innerHTML='';$('weighted-support').textContent='Missing comparisons are not replaced with zero skill.';return;}
    const metric=$('weighted-metric').value, profile=$('weighted-profile').value;
    const rows=c.rows.filter(v=>v.metric===metric&&v.profile===profile).sort((a,b)=>(b.weighted_skill??-Infinity)-(a.weighted_skill??-Infinity)||a.family.localeCompare(b.family));
    $('weighted-cohort').innerHTML='<strong>'+esc(c.window_label)+'</strong><span>'+Object.entries(c.seasons).map(([year,s])=>esc(year)+': '+esc(s.n)+' / '+esc(s.window_final_denominator)+' eligible-window finals ('+esc(s.official_final_denominator)+' season finals)').join(' · ')+'</span>';
    $('weighted-body').innerHTML=rows.map(r=>'<tr><td><strong>'+esc(r.family)+'</strong>'+(r.baseline?'<span class="subline">Fixed simple reference</span>':'')+'</td><td class="'+(r.weighted_skill<0?'skill-negative':'')+'"><strong>'+pct(r.weighted_skill)+'</strong></td><td>'+['2024','2025','2026'].map(y=>pct(r.season_skill[y])).join(' / ')+'</td><td>'+interval(r.conditional_ci95)+'</td><td>'+interval(r.adjusted_interval)+'</td><td>'+pct(r.family_minimum_skill)+' to '+pct(r.family_maximum_skill)+'<span class="subline">'+esc(r.negative_candidates)+' negative / '+esc(r.candidate_count)+' retained candidates</span></td></tr>').join('');
    $('weighted-support').textContent='Reference family: '+c.baseline_family+'. '+c.bootstrap_replicates+' paired calendar-week bootstrap replicates. Week blocks: '+Object.entries(c.seasons).map(([year,s])=>year+' = '+s.week_blocks).join(', ')+'. Independent sample count is not established. Historical selection remains exposed.';
    document.documentElement.dataset.weightedView=c.target+'-'+c.window+'-'+profile+'-'+metric;
  }
  function targetChanged(){const target=$('weighted-target').value;const metrics=target==='winner'?['log_loss','brier','error_rate']:['mae','rmse'];$('weighted-metric').innerHTML=metrics.map(v=>'<option value="'+v+'">'+names[v]+'</option>').join('');render();}
  $('weighted-target').addEventListener('change',targetChanged);
  for(const id of ['weighted-window','weighted-profile','weighted-metric'])$(id).addEventListener('change',render);
  fetch('data/season_skill.json',{cache:'no-cache'}).then(r=>{if(!r.ok)throw new Error('Weighted evidence could not be loaded (HTTP '+r.status+').');return r.json();}).then(value=>{saved=value;render();document.documentElement.dataset.weightedReady='true';}).catch(error=>{$('weighted-error').hidden=false;$('weighted-error').textContent=error.message;$('weighted-cohort').textContent='Weighted evidence is unavailable; the existing game and source views remain separate.';});
})();
