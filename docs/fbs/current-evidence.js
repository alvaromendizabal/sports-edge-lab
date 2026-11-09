'use strict';
(async() => {
  const finite=value=>typeof value==='number'&&Number.isFinite(value);
  const number=(value,digits=1)=>finite(value)?value.toFixed(digits):'—';
  const percentage=value=>finite(value)?(value*100).toFixed(1)+'%':'—';
  const shortStatus=value=>({AUTHENTICATED_SAVED_FUTURE_SHADOW_ISSUE:'Original future-issued shadow',AUTHENTICATED_SAVED_CALIBRATED_SHADOW_REVISION:'Separate future-issued calibrated shadow',NO_SAVED_ORIGINAL_ISSUE:'No original issue proved',NO_SAVED_CALIBRATED_REVISION:'No calibrated revision',INSUFFICIENT_PRIOR_OUTCOMES:'Insufficient earlier outcomes',EXACT_KICKOFF_UNRESOLVED:'Exact kickoff unresolved'}[value]||String(value||'No saved output').replaceAll('_',' ').toLowerCase());
  function select(data,{season='2026',period='current_week',search=''}={}) {
    const term=search.trim().toLowerCase();
    return data.games.filter(g=>(season==='all'||String(g.season)===season)&&(period==='all'||period==='tbd'&&!g.kickoff_utc||g.period===period||!g.kickoff_utc&&g.nominal_tbd_period===period)&&(!term||`${g.id} ${g.home} ${g.away}`.toLowerCase().includes(term)));
  }
  const cell=value=>'"'+String(value??'').replace(/^([=+@\t\r])/,'\'$1').replaceAll('"','""')+'"';
  function csv(rows,layer) {
    if(!['original','calibrated','historical'].includes(layer))throw new Error('Unknown evidence layer');
    const head=['official_game_id','season','home','away','exact_kickoff_utc','source_observed_at','forecast_layer','evidence_status','home_win_probability','home_margin','total_points','home_score','away_score','information_cutoff_utc','original_durable_observed_at'];
    return [head,...rows.map(g=>{const v=g[layer];return[g.id,g.season,g.home,g.away,g.kickoff_utc,g.source_observed_at,layer,v.status,v.p_home,v.home_margin,v.total_points,v.home_score,v.away_score,v.information_cutoff_utc,v.original_durable_observed_at]})].map(row=>row.map(cell).join(',')).join('\r\n');
  }
  const api={select,csv,shortStatus};if(typeof module!=='undefined'&&module.exports)module.exports=api;
  if(typeof window==='undefined')return;
  const data=await window.FBS_CURRENT_EVIDENCE_V053_READY;if(!data)return;
  window.FBSCurrentEvidence=api;const $=id=>document.getElementById(id),esc=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const date=value=>value?new Intl.DateTimeFormat('en-US',{timeZone:'America/Los_Angeles',month:'short',day:'numeric',year:'numeric',hour:'numeric',minute:'2-digit',timeZoneName:'short'}).format(new Date(value)):'Exact kickoff unresolved';
  let page=0,filtered=[];const size=40;
  $('source-clock').textContent=`Source observed ${date(data.source_observed_at)}; capture completed ${date(data.source_capture_completed_at)}. Calendar view ${date(data.as_of)}. This is a saved snapshot.`;
  $('execution-summary').textContent=data.execution.public_summary;
  const cards=[['New base fits',data.execution.new_base_fits],['New calibrators',data.execution.new_calibration_fits],['New issue records',data.execution.new_genuine_issues],['New feature snapshots',data.execution.new_feature_materializations],['New current scalar outputs',data.execution.new_prediction_records],['Provider requests',data.execution.provider_requests]];
  $('execution-grid').innerHTML=cards.map(([label,value])=>`<article><span>${esc(label)}</span><strong>${value.toLocaleString()}</strong></article>`).join('');
  const metrics=[['joint_log_loss','Joint log loss'],['winner_log_loss','Winner log loss'],['winner_brier','Winner Brier'],['margin_absolute_error','Margin absolute error'],['total_absolute_error','Total absolute error'],['winner_accuracy','Winner accuracy']];
  const comparison=data.saved_r12_comparison;
  $('comparison-rows').innerHTML=metrics.map(([key,label])=>{const delta=comparison.uncertainty.metrics[key]?.mean_difference;return `<tr><td>${esc(label)}</td><td>${number(comparison.aggregate.control[key],6)}</td><td>${number(comparison.aggregate.calibrated[key],6)}</td><td>${finite(delta)?(delta>0?'+':'')+number(delta,6):'Unchanged'}</td></tr>`}).join('');
  $('comparison-qualification').textContent=comparison.qualification+' Evaluation computed '+date(comparison.computed_at_utc)+'. The 122 current calibrated revisions are a separate, unscored issue cohort.';
  function render(){
    filtered=select(data,{season:$('season').value,period:$('period').value,search:$('search').value});
    page=Math.min(page,Math.max(0,Math.ceil(filtered.length/size)-1));const layer=$('layer').value;
    const available=filtered.filter(g=>finite(g[layer].p_home)).length,tbd=filtered.filter(g=>!g.kickoff_utc).length;
    $('game-summary').textContent=`${filtered.length.toLocaleString()} source games shown · ${available.toLocaleString()} with saved ${layer==='historical'?'reconstruction':'issue'} values in this layer · ${(filtered.length-available).toLocaleString()} explicit gaps · ${tbd} unresolved exact kickoffs. Calendar dates and original issue deadlines remain separate.`;
    $('game-rows').innerHTML=filtered.slice(page*size,(page+1)*size).map(g=>{const v=g[layer];return `<tr><td>${esc(g.away)} at ${esc(g.home)}<small>${esc(g.id)} · ${g.completed?`Final ${esc(g.actual_away_points)}–${esc(g.actual_home_points)}`:'No observed final'}</small></td><td>${esc(date(g.kickoff_utc))}${!g.kickoff_utc&&g.nominal_source_date?`<small>Source date ${esc(g.nominal_source_date.slice(0,10))} · time unconfirmed</small>`:''}</td><td><span class="status ${finite(v.p_home)?'available':'gap'}">${esc(shortStatus(v.status))}</span></td><td>${percentage(v.p_home)}</td><td>${number(v.home_margin)}</td><td>${number(v.total_points)}</td><td>${number(v.away_score)} / ${number(v.home_score)}</td><td><button data-game="${esc(g.id)}" aria-label="Inspect ${esc(g.away)} at ${esc(g.home)}">Inspect</button></td></tr>`}).join('')||'<tr><td colspan="8">No games match these filters.</td></tr>';
    $('page-status').textContent=`Page ${filtered.length?page+1:0} of ${Math.ceil(filtered.length/size)}`;
    $('previous-page').disabled=page===0;$('next-page').disabled=(page+1)*size>=filtered.length;$('download-csv').disabled=filtered.length===0;
  }
  function details(id){
    const g=data.games.find(row=>row.id===id);if(!g)return;
    $('detail-title').textContent=`${g.away} at ${g.home}`;
    let text=`<p class="note">Official game ${esc(g.id)} · ${esc(date(g.kickoff_utc))}<br>Source observed ${esc(date(g.source_observed_at))}. ${g.completed?'Final score: '+esc(g.actual_away_points)+'–'+esc(g.actual_home_points):'No observed final.'}</p>`;
    for(const [key,label] of [['original','Original foundation issue'],['calibrated','Separate calibrated revision'],['historical','Historical reconstruction']]){
      const v=g[key];text+=`<section class="detail-layer"><h3>${label}</h3><p>${esc(shortStatus(v.status))}</p><dl><dt>Home win probability</dt><dd>${percentage(v.p_home)}</dd><dt>Home margin / total</dt><dd>${number(v.home_margin)} / ${number(v.total_points)}</dd><dt>Away / home score</dt><dd>${number(v.away_score)} / ${number(v.home_score)}</dd><dt>Information cutoff</dt><dd>${esc(v.information_cutoff_utc||'Not an original issue clock')}</dd><dt>Durable issue observed</dt><dd>${esc(v.original_durable_observed_at||'No original issue proved')}</dd><dt>Saved margin intervals</dt><dd>${esc(v.margin_intervals?JSON.stringify(v.margin_intervals):'Not in this saved layer')}</dd><dt>Saved total intervals</dt><dd>${esc(v.total_intervals?JSON.stringify(v.total_intervals):'Not in this saved layer')}</dd></dl><p>${key==='calibrated'?'This revision keeps its own clocks and does not replace the original foundation issue. Nominal interval coverage is not proved.':key==='historical'?'Exposed retrospective development. These values do not establish an original publication before the game.':'Original publication is preserved separately from later recalibration and retrospective reconstruction.'}</p></section>`;
    }
    text+='<h3>Dated provider references</h3><p class="note">Each source has its own product, capture and quote qualification. Missing values are explicit. No qualified four-provider baseline is established.</p><div class="table-scroll"><table><thead><tr><th>Provider / target</th><th>Saved reference</th><th>Status</th><th>Quote / capture</th></tr></thead><tbody>';
    for(const [provider,targets] of Object.entries(g.providers))for(const [target,v] of Object.entries(targets))text+=`<tr><td>${esc(provider)}<small>${esc(target)}</small></td><td>${number(v.value,3)}</td><td><span class="status">${esc(shortStatus(v.status))}</span></td><td>${esc(v.quote_at||'Quote clock absent')}<small>${esc(v.acquired_at||'Capture clock absent in this reference')}</small></td></tr>`;
    $('detail-content').innerHTML=text+'</tbody></table></div>';$('game-detail').showModal();
  }
  for(const id of ['season','period','layer','search'])$(id).addEventListener(id==='search'?'input':'change',()=>{page=0;render()});
  $('previous-page').onclick=()=>{page--;render()};$('next-page').onclick=()=>{page++;render()};
  $('game-rows').onclick=event=>{const button=event.target.closest('[data-game]');if(button)details(button.dataset.game)};
  $('close-detail').onclick=()=>$('game-detail').close();
  $('download-csv').onclick=()=>{const url=URL.createObjectURL(new Blob([csv(filtered,$('layer').value)],{type:'text/csv;charset=utf-8'})),a=document.createElement('a');a.href=url;a.download='fbs-current-'+$('layer').value+'-evidence.csv';document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000)};
  const query=new URLSearchParams(location.search);for(const key of ['season','period','layer'])if([...$(key).options].some(o=>o.value===query.get(key)))$(key).value=query.get(key);
  render();
})();
