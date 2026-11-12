'use strict';
(() => {
  const $=id=>document.getElementById(id);
  const data=JSON.parse($('report-data').textContent);
  const esc=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const fmt=(v,n=3)=>v==null?'—':Number(v).toFixed(n);
  const prob=v=>v==null?'—':`${(v*100).toFixed(2)}%`;
  const human=s=>String(s||'Unobserved').toLowerCase().replaceAll('_',' ');
  const time=v=>v?new Intl.DateTimeFormat('en-US',{timeZone:'America/Los_Angeles',year:'numeric',month:'short',day:'numeric',hour:'numeric',minute:'2-digit',timeZoneName:'short'}).format(new Date(v)):'Exact kickoff unresolved';
  const names={latest:'New V070 foundation outlook',saved:'Latest retained foundation issue',recovered_original:'Recovered earlier original issue'};
  const notes={latest:'104 selected issues were genuinely created during V070. This layer leaves the other games blank; it never substitutes an older issue.',saved:'Latest authenticated selected foundation issue for each game. Older issues retain their original dates and remain distinct from the V070 refresh.',recovered_original:'55 earlier original winner-probability records recovered without fitting or new inference. Point forecasts are unavailable in this recovered winner-only archive.'};
  const missing=(g,layer)=>!g.kickoff?'EXACT_KICKOFF_NOT_PUBLISHED':g.id==='401866465'&&layer!=='recovered_original'?'FIXTURE_REVISION_QUARANTINED':layer==='latest'?(g.completed?'NO_CURRENT_REFRESH_FOR_COMPLETED_GAME':'V070_REFRESH_NOT_COMPLETED'):layer==='saved'?'NO_AUTHENTICATED_SAVED_FOUNDATION_ISSUE':'NO_RECOVERED_ORIGINAL_ISSUE';
  let currentPage=0,filtered=[],lastButton=null;
  const rowsPerPage=30;
  const sourceGames=data.games;
  const current=sourceGames.filter(g=>g.season===2026);
  const latest=current.filter(g=>g.latest);
  $('report-clock').textContent=`Source snapshot: ${time(data.source_as_of_utc)} · Saved report, not a live feed`;
  $('stats').innerHTML=[['888','observed 2026 games'],['691','observed finals'],['197','without an observed final'],['104','new V070 issue games'],['135','upcoming with a retained issue'],['54','unresolved kickoff times']].map(([n,l])=>`<div><strong>${n}</strong><span>${l}</span></div>`).join('');
  $('coverage-rows').innerHTML=data.season_coverage.map(r=>`<tr><td>${r.season}</td><td>${r.official_games}</td><td>${r.completed_games}</td><td>${r.kickoff_not_published_games}</td><td>${r.games_with_genuine_saved_issue}</td><td>${r.new_V070_issue_games}</td></tr>`).join('');
  $('metric-rows').innerHTML=data.annual_leaders.map(r=>`<tr data-metric="${r.season}|${r.target}|${r.metric}"><td>${r.season}</td><td>${esc(human(r.target))}</td><td>${esc(human(r.metric))}</td><td>${esc(r.families.join(' / '))}</td><td>${r.metric==='accuracy'?prob(r.value):fmt(r.value,5)}</td><td>${r.games}</td><td>${r.season===2026?'Saved monitoring cohort':'Exposed historical development'}<small>No promotion authorized</small></td></tr>`).join('');
  const cb=data.separate_685_catboost_winner;
  $('catboost-rows').innerHTML=`<tr><td>CatBoost</td><td>${cb.games}</td><td>${prob(cb.metrics.accuracy)}</td><td>${fmt(cb.metrics.log_loss,5)}</td><td>${fmt(cb.metrics.brier,5)}</td></tr>`;
  $('reconstruction-rows').innerHTML=data.separate_301_leaders.map(r=>`<tr><td>${esc(human(r.metric))}</td><td>${r.metric==='accuracy'?prob(r.value):fmt(r.value,5)}</td><td>${r.games}</td></tr>`).join('');
  $('provider-rows').innerHTML=data.provider_qualified_cohorts.map(r=>`<tr data-provider="${r.season}|${esc(r.provider)}"><td>${r.season}</td><td>${esc(r.provider)}</td><td>${r.official_games}</td><td>${r.completed_games}</td><td>${r.qualified_winner_games}</td><td>${r.qualified_margin_games}</td><td>${r.qualified_total_games}</td><td>${r.qualified_cover_games}</td></tr>`).join('');
  $('comparison-rows').innerHTML=data.separate_231_comparison.map(r=>`<tr><td>${esc(r.label)}</td><td>${r.cohort_games}</td><td>${prob(r.accuracy)}</td><td>${fmt(r.logloss,6)}</td><td>${fmt(r.brier,6)}</td></tr>`).join('');
  $('promotion-requirements').innerHTML=data.promotion_requirements.map(s=>`<li>${esc(s)}</li>`).join('');
  $('source-details').textContent=`Source capture: ${data.source_capture_started_at} to ${data.source_capture_completed_at}. Report as of: ${data.source_as_of_utc}. The selected outputs retain earlier source and issue timestamps. Owner return SHA-256: ${data.source_owner_return_sha256}.`;
  let reportUrl=URL.createObjectURL(new Blob([$('report-data').textContent],{type:'application/json'}));
  $('report-download').href=reportUrl;
  $('report-download').download='latest-v071.json';

  function render() {
    const season=$('season').value,period=$('period').value,layer=$('layer').value,q=$('search').value.trim().toLowerCase();
    filtered=sourceGames.filter(g=>(season==='all'||g.season===+season)&&(!q||`${g.home} ${g.away} ${g.id}`.toLowerCase().includes(q))&&
      (period==='all'||period==='upcoming'&&!g.completed||period==='final'&&g.completed||period==='tbd'&&!g.kickoff||period==='refresh_gap'&&g.season===2026&&!g.completed&&g.kickoff&&!g.latest));
    filtered.sort((a,b)=>(a.kickoff||'9999').localeCompare(b.kickoff||'9999')||a.id.localeCompare(b.id));
    const n=filtered.filter(g=>g[layer]).length;
    $('game-summary').textContent=`${filtered.length} games shown · ${n} with selected issue · ${filtered.length-n} explicit gaps`;
    $('layer-note').textContent=notes[layer];
    const pages=Math.max(1,Math.ceil(filtered.length/rowsPerPage));currentPage=Math.min(currentPage,pages-1);
    $('game-rows').innerHTML=filtered.slice(currentPage*rowsPerPage,(currentPage+1)*rowsPerPage).map(g=>{const x=g[layer];return `<tr data-game="${g.id}"><td><strong>${esc(g.away)} at ${esc(g.home)}</strong><small>${esc(time(g.kickoff))}</small></td><td>${g.completed?`${g.away_points}–${g.home_points}`:'Pending'}<small>${g.completed?'Away–home score':!g.kickoff?'Kickoff unresolved':'No final in source'}</small></td><td data-value="probability">${prob(x?.probability)}</td><td data-value="margin">${fmt(x?.margin,2)}</td><td data-value="total">${fmt(x?.total,2)}</td><td class="${x?'':'gap'}">${x?esc(time(x.issue_at)):esc(human(missing(g,layer)))}<small>${x?esc(human(x.evidence)):'Unavailable in selected layer'}</small></td><td><button data-detail="${g.id}" aria-label="Evidence for ${esc(g.away)} at ${esc(g.home)}">Evidence</button></td></tr>`;}).join('')||'<tr><td colspan="7">No games match these filters.</td></tr>';
    $('page-status').textContent=`Page ${currentPage+1} of ${pages}`;
    $('previous').disabled=currentPage===0;$('next').disabled=currentPage===pages-1;
    $('download-view').disabled=!filtered.length;
  }

  function detail(g) {
    const layer=$('layer').value,x=g[layer];
    $('detail-title').textContent=`${g.away} at ${g.home}`;
    const items=[['Kickoff',g.kickoff||'EXACT_KICKOFF_NOT_PUBLISHED'],['Selected layer',names[layer]],['Schedule/result source observed',g.source_at],['Original information cutoff',x?.cutoff_at||'No selected issue'],['Original issue / durable observation',x?.issue_at||missing(g,layer)],['Computation clock',x?.computed_at||'Not separately projected for this retained layer'],['Evidence class',x?.evidence||'NO_SELECTED_ORIGINAL_ISSUE'],['Champion status','Unpromoted research output']];
    $('detail-content').innerHTML=`<div class="detail-grid">${items.map(([k,v])=>`<div><span>${esc(k)}</span>${esc(v)}</div>`).join('')}</div><h3>Selected values and original clocks</h3><div class="table-wrap"><table><thead><tr><th>Layer</th><th>Home probability</th><th>Home margin</th><th>Total</th><th>Original issue</th></tr></thead><tbody>${Object.keys(names).map(k=>{const r=g[k];return `<tr><td>${esc(names[k])}</td><td>${prob(r?.probability)}</td><td>${fmt(r?.margin,2)}</td><td>${fmt(r?.total,2)}</td><td>${r?esc(r.issue_at):esc(human(missing(g,k)))}</td></tr>`}).join('')}</tbody></table></div><h3>Provider reference qualification</h3><div class="table-wrap"><table><thead><tr><th>Venue</th><th>Target</th><th>Retained status</th></tr></thead><tbody>${data.provider_names.flatMap((v,i)=>data.provider_targets.map((t,j)=>`<tr><td>${esc(v)}</td><td>${esc(human(t))}</td><td>${esc(human(data.provider_status_codes[g.providers[i][j]]))}</td></tr>`)).join('')}</tbody></table></div><p class="scope">Reference availability is distinct from statistical comparability. No fully qualified expected-score or fair-probability baseline is established for these annual report rows. Quoted medians and lines are not substituted for model expectations. Original clocks are not rewritten.</p>`;
    $('game-detail').showModal();$('detail-close').focus();
  }
  $('game-rows').addEventListener('click',event=>{const b=event.target.closest('button[data-detail]');if(b){lastButton=b;detail(sourceGames.find(g=>g.id===b.dataset.detail));}});
  $('detail-close').addEventListener('click',()=>$('game-detail').close());
  $('game-detail').addEventListener('close',()=>lastButton?.focus());
  ['season','period','layer'].forEach(id=>$(id).addEventListener('change',()=>{currentPage=0;render();}));
  $('search').addEventListener('input',()=>{currentPage=0;render();});
  $('previous').addEventListener('click',()=>{currentPage--;render();});
  $('next').addEventListener('click',()=>{currentPage++;render();});
  $('download-view').addEventListener('click',()=>{
    const layer=$('layer').value;
    const rows=[['game_id','season','away','home','kickoff_utc','completed','away_points','home_points','selected_layer','home_probability','home_margin','total_points','issue_at_utc','cutoff_at_utc','evidence_class','gap_reason']];
    for(const g of filtered){const x=g[layer];rows.push([g.id,g.season,g.away,g.home,g.kickoff,g.completed,g.away_points,g.home_points,layer,x?.probability,x?.margin,x?.total,x?.issue_at,x?.cutoff_at,x?.evidence,x?'':missing(g,layer)]);}
    const csv=rows.map(row=>row.map(v=>`"${String(v??'').replaceAll('"','""')}"`).join(',')).join('\r\n')+'\r\n';
    const a=document.createElement('a'),url=URL.createObjectURL(new Blob([csv],{type:'text/csv;charset=utf-8'}));a.href=url;a.download=`fbs-selected-${layer}.csv`;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
  });
  render();
  window.FBS_V071_READY=Promise.resolve({games:sourceGames.length,newIssues:latest.length});
})();
