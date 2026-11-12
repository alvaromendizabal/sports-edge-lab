'use strict';
(function () {
  const $ = id => document.getElementById(id);
  const names = {original:'Actual V062 baseline selection',retained_v061:'Earlier verified V061 original archive',calibrated:'Calibrated shadow revision',mixture_global:'Experimental global mixture',mixture_gated:'Experimental gated mixture',replay:'Retrospective reconstruction'};
  const providers = ['DraftKings','Kalshi','Polymarket Global','Polymarket US'];
  const targets = ['winner','margin','total','cover_probability'];
  const esc = value => String(value == null ? 'Unobserved' : value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const human = value => String(value || 'Unobserved').toLowerCase().replaceAll('_',' ');
  const fmt = (value, digits=1) => value == null ? '—' : Number(value).toFixed(digits);
  const prob = value => value == null ? '—' : (value * 100).toFixed(2)+'%';
  const stamp = value => value ? value.replace('T',' ').replace(/\.\d+(?=Z|[+-])/, '') : 'Exact kickoff unresolved';
  const pacific = value => value ? new Intl.DateTimeFormat('en-US',{timeZone:'America/Los_Angeles',month:'short',day:'numeric',hour:'numeric',minute:'2-digit',timeZoneName:'short'}).format(new Date(value)) : 'Exact kickoff unresolved';
  let data, page = 0, filtered = [];
  function selected(game) {return game.layers[$('layer').value];}
  function filterGames() {
    const period=$('period').value, coverage=$('coverage').value, query=$('search').value.trim().toLowerCase();
    return data.games.filter(g=>{
      if(period==='upcoming' && g.schedule_status!=='CURRENT_ORIGIN_REFRESH_DUE')return false;
      if(period==='refresh_gap' && !g.current_owner_baseline_refresh.attempted)return false;
      if(period==='omitted' && !g.archive_continuity.prior_original_absent_from_current_ledger)return false;
      if(period==='older' && !g.archive_continuity.current_ledger_selects_older_original_issue)return false;
      if(period==='tbd' && g.kickoff_utc!==null)return false;
      if(period==='final' && !g.completed)return false;
      if(period==='pending' && (g.completed || g.kickoff_utc===null || g.schedule_status==='CURRENT_ORIGIN_REFRESH_DUE'))return false;
      const has=selected(g).values.p_home!==null;
      if(coverage==='with'&&!has || coverage==='without'&&has)return false;
      return !query || `${g.home} ${g.away} ${g.game_id}`.toLowerCase().includes(query);
    });
  }
  function render() {
    filtered=filterGames(); const pages=Math.max(1,Math.ceil(filtered.length/30)); page=Math.min(page,pages-1);
    const layer=$('layer').value, withValues=filtered.filter(g=>selected(g).values.p_home!==null).length;
    $('layer-note').textContent=data.layer_definitions[layer];
    $('game-summary').textContent=`${filtered.length} of 888 source games shown · ${withValues} with retained probability · ${filtered.length-withValues} explicit gaps`;
    $('game-rows').innerHTML=filtered.slice(page*30,(page+1)*30).map(g=>{
      const item=selected(g),v=item.values,has=v.p_home!==null;
      const activity=layer==='retained_v061'&&has?'Retained V061 archive; no V062 refresh':g.current_owner_baseline_refresh.attempted?'V062 refresh gap':null;
      return `<tr data-game="${esc(g.game_id)}"><td><button class="game-link" data-detail="${esc(g.game_id)}">${esc(g.away)} at ${esc(g.home)}</button><span class="minor">${esc(pacific(g.kickoff_utc))}</span><span class="minor">${g.completed?`Final: ${g.actual_away_points}–${g.actual_home_points}`:esc(human(g.schedule_status))}</span></td><td class="num">${prob(v.p_home)}</td><td class="num">${fmt(v.home_margin)}</td><td class="num">${fmt(v.total_points)}</td><td class="num">${fmt(v.away_score)}–${fmt(v.home_score)}<span class="minor">away–home</span></td><td class="${has?'ok':'gap'}">${esc(has?names[layer]:human(item.target_status.p_home))}${activity?'<span class="minor">'+esc(activity)+'</span>':''}<span class="minor">${item.information_cutoff_utc?'Information cutoff '+esc(stamp(item.information_cutoff_utc)):layer==='replay'?'Historical availability unproved':'No authenticated issue in this layer'}</span></td></tr>`;
    }).join('') || '<tr><td colspan="6">No games match these filters. Clear the search or choose all games.</td></tr>';
    $('page-status').textContent=`Page ${page+1} of ${pages}`;
    $('previous').disabled=page===0; $('next').disabled=page===pages-1;
    $('download-view').disabled=filtered.length===0;
  }
  function renderLeaders() {
    const season=$('leader-season').value;
    $('leader-rows').innerHTML=data.historical_cohort_leaders.filter(r=>season==='all'||String(r.season)===season).map(r=>`<tr><td>${esc(r.comparison_group)}</td><td>${r.season}</td><td>${esc(r.target)} / ${esc(r.metric)}</td><td>${r.games}</td><td class="num">${fmt(r.best_saved_value,6)}</td><td>${r.compared_card_count}</td><td>Exposed descriptive leader<span class="minor">Not promoted; ${r.original_issued_games??'unobserved'} proved original issues in saved card</span></td></tr>`).join('');
  }
  function openGame(id) {
    const g=data.games.find(g=>g.game_id===id);if(!g)return;
    $('detail-title').textContent=`${g.away} at ${g.home}`;
    const layerRows=Object.entries(g.layers).map(([name,item])=>{const v=item.values;return `<tr><td>${esc(names[name])}<span class="minor">${esc(human(item.status))}</span></td><td>${prob(v.p_home)}</td><td>${fmt(v.home_margin)}</td><td>${fmt(v.total_points)}</td><td>${esc(item.horizon||'No issued horizon')}<span class="minor">Cutoff: ${esc(item.information_cutoff_utc||'Unproved / absent')}</span><span class="minor">Durably observed: ${esc(item.original_durable_observed_at||'Unproved / absent')}</span></td></tr>`}).join('');
    const providerRows=providers.flatMap(provider=>targets.map(target=>{const r=data.provider_evidence[g.provider_reference_ids[provider][target]];return `<tr><td>${esc(provider)}</td><td>${esc(human(target))}</td><td>${target==='winner'||target==='cover_probability'?prob(r.value):fmt(r.value)}<span class="minor">${esc(human(r.interpretation))}</span></td><td>${esc(human(r.status))}<span class="minor">Quote: ${esc(r.quote_at||'Missing')}</span><span class="minor">Acquired: ${esc(r.acquired_at||'Missing')}</span><span class="minor">Qualified matched baseline: ${r.statistically_usable_baseline?'yes':'no'}</span></td></tr>`})).join('');
    $('detail-content').innerHTML=`<p>${g.current_owner_baseline_refresh.attempted?'V062 current-origin refresh failed: exact registered fit pool has no existing state; no refit was authorized.':'No current-origin refresh task for this game.'} The V061 archive keeps its original issue clocks; it is not a new V062 forecast. ${g.archive_continuity.prior_original_absent_from_current_ledger?'This earlier original issue is absent from the actual V062 selection.':''} ${g.archive_continuity.current_ledger_selects_older_original_issue?'The actual V062 selection is an older original issue than the preserved V061 record.':''}</p><p>Game ${esc(id)} · ${esc(stamp(g.kickoff_utc))} · ${g.completed?'Final '+g.actual_away_points+'–'+g.actual_home_points:'Final not observed in this source capture'}</p><div class="clock-grid"><div>Fixture source observed<br><b>${esc(g.source_observed_at||'Missing')}</b></div><div>Latest qualified champion issue<br><b class="gap">None authorized by V062 champion check</b></div></div><section class="detail-block"><h3>Separate saved forecast layers</h3><p>Home probability and signed home margin use the same venue orientation. The actual V062 selection and separately verified V061 archive remain distinct. A calibrated or mixture revision never replaces an original issue. Reconstructions are not issued forecasts. Every displayed value is rounded from a saved authenticated record.</p><div class="table-wrap"><table><thead><tr><th>Layer</th><th>Home win</th><th>Home margin</th><th>Total</th><th>Clocks / horizon</th></tr></thead><tbody>${layerRows}</tbody></table></div></section><section class="detail-block"><h3>Provider reference and source-gap evidence</h3><p>Descriptive retained observations remain distinct from qualified matched pregame benchmarks. A threshold center or point line is not an expected score. Missing quote clocks or late acquisition are not repaired by display.</p><div class="table-wrap"><table><thead><tr><th>Provider</th><th>Target</th><th>Derived reference</th><th>Eligibility and clocks</th></tr></thead><tbody>${providerRows}</tbody></table></div></section>`;
    $('game-detail').showModal();
  }
  function download() {
    const layer=$('layer').value, fields=['game_id','home','away','kickoff_utc','completed','layer','evidence_class','information_cutoff_utc','durable_observed_at','p_home','home_margin','total_points','home_score','away_score','target_status'];
    const quote=v=>'"'+String(v==null?'':v).replaceAll('"','""')+'"';
    const rows=filtered.map(g=>{const i=selected(g),v=i.values;return [g.game_id,g.home,g.away,g.kickoff_utc,g.completed,layer,i.evidence_class,i.information_cutoff_utc,i.original_durable_observed_at,v.p_home,v.home_margin,v.total_points,v.home_score,v.away_score,i.target_status.p_home].map(quote).join(',')});
    const url=URL.createObjectURL(new Blob([[fields.map(quote).join(','),...rows].join('\r\n')],{type:'text/csv;charset=utf-8'}));const a=document.createElement('a');a.href=url;a.download=`fbs-v063-2026-${layer}-${$('period').value}.csv`;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
  }
  window.FBS_LATEST_READY=(async()=>{
    if(typeof DecompressionStream==='undefined')throw new Error('This browser cannot decode the compact inventory. Use the CSV or JSON.gz download.');
    const bytes=Uint8Array.from(atob(window.FBS_LATEST_V063_GZIP),c=>c.charCodeAt(0));
    data=await new Response(new Blob([bytes]).stream().pipeThrough(new DecompressionStream('gzip'))).json();
    if(data.schema!=='fbs.public.v063.latest-authenticated-game-view.v1'||data.games.length!==888)throw new Error('Inventory schema or denominator mismatch.');
    window.FBS_LATEST_V063=data;
    for(const id of ['period','layer','coverage'])$(id).addEventListener('change',()=>{page=0;render()});
    $('search').addEventListener('input',()=>{page=0;render()});
    $('previous').addEventListener('click',()=>{page--;render()});$('next').addEventListener('click',()=>{page++;render()});
    $('game-rows').addEventListener('click',e=>{const b=e.target.closest('[data-detail]');if(b)openGame(b.dataset.detail)});
    $('close-detail').addEventListener('click',()=>$('game-detail').close());
    $('download-view').addEventListener('click',download);$('leader-season').addEventListener('change',renderLeaders);
    $('champion-rows').innerHTML=data.champion_status.roles.map(r=>`<tr><td>${esc(r.objective)}</td><td class="gap">No authorized rolling champion</td></tr>`).join('');
    $('new-research-rows').innerHTML=data.new_research.new_vs_restored_metric_rows.map(r=>`<tr><td>${r.season}</td><td>${esc(r.target)} / ${esc(r.metric)}</td><td>${r.games}</td><td class="num">${fmt(r.restored_selected_control,6)}</td><td class="num">${fmt(r.best_new_value,6)}</td><td>Restored reference leads</td></tr>`).join('');
    $('native-monitor-rows').innerHTML=data.native_latest_label_monitor.selected_descriptive_rows.map(r=>`<tr><td>${esc(r.display_role)}</td><td>${r.games}</td><td>${r.correct}</td><td>${prob(r.accuracy)}</td><td class="num">${fmt(r.log_loss,6)}</td><td class="num">${fmt(r.brier,6)}</td></tr>`).join('');
    render();renderLeaders();return data;
  })();
  window.FBS_LATEST_READY.catch(error=>{$('game-summary').textContent=error.message;$('game-summary').classList.add('gap')});
})();
