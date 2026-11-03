'use strict';
(() => {
 const providers=['DraftKings','Kalshi','Polymarket US','Polymarket Global'];
 const clock=value=>value?Date.parse(value):NaN;
 function reference(game,provider,target,horizon,assessed){
  const kick=clock(game.kickoff);
  const cutoff=horizon==='T60'?kick-3600000:horizon==='T120'?kick-7200000:horizon==='current'?clock(assessed):kick;
  const effective=r=>clock(r.quote_at||(horizon==='current'?r.captured_at:null));
  const end=r=>clock(r.interval_end_at||r.quote_at||(horizon==='current'?r.captured_at:null));
  const rows=game.markets[provider].filter(r=>r.target===target&&r.join_status==='matched'&&Number.isFinite(r.value)&&
   (horizon==='latest_pre_kickoff'?effective(r)<cutoff&&end(r)<cutoff:effective(r)<=cutoff&&end(r)<=cutoff));
  if(!rows.length)return {row:null,status:'absent',cutoff};
  const latest=Math.max(...rows.map(effective)),same=rows.filter(r=>effective(r)===latest);
  const signatures=new Set(same.map(r=>JSON.stringify([r.value,r.picked_home,r.reference_kind,r.product])));
  if(signatures.size!==1)return {row:null,status:'conflict',cutoff};
  same.sort((a,b)=>(a.captured_at||'').localeCompare(b.captured_at||''));
  return {row:same[0],status:!same[0].quote_at?'quote_clock_unknown':latest>=kick?'after_kickoff':'available',cutoff};
 }
 function filterGames(games,state,windows,assessed){
  const query=state.query.trim().toLocaleLowerCase();
  return games.filter(g=>{
   if(state.view==='completed'&&!g.completed)return false;
   if(state.view==='last'||state.view==='current'){
    const w=windows[state.view==='last'?'previous_complete_week':'current_calendar_week'];
    if(!(clock(g.kickoff)>=clock(w.start_inclusive_utc)&&clock(g.kickoff)<clock(w.end_exclusive_utc)))return false;
   }
   if(state.week!=='all'&&state.week!==`${g.phase}:${g.week}`)return false;
   if(query&&!`${g.home} ${g.away} ${g.id} ${g.kickoff}`.toLocaleLowerCase().includes(query))return false;
   if(state.disagreements){
    const row=reference(g,state.provider,'winner',state.horizon,assessed).row;
    if(!g.replay||!row||g.replay.picked_home===row.picked_home)return false;
   }
   return true;
  });
 }
 function csvCell(value){
  let s=value===null||value===undefined?'':String(value);
  if(/^[=+@\t\r]/.test(s)||(/^\-/.test(s)&&!/^\-\d+(?:\.\d+)?$/.test(s)))s="'"+s;
  return '"'+s.replaceAll('"','""')+'"';
 }
 if(typeof module!=='undefined'&&module.exports)module.exports={reference,filterGames,csvCell};
 if(typeof document==='undefined')return;
 const data=JSON.parse(document.getElementById('season-data').textContent);
 const state={view:'all',week:'all',query:'',provider:'DraftKings',horizon:'latest_pre_kickoff',disagreements:false,page:0};
 const size=25;
 const $=id=>document.getElementById(id);
 const formatter=new Intl.DateTimeFormat('en-US',{timeZone:data.timezone,month:'short',day:'numeric',hour:'numeric',minute:'2-digit',timeZoneName:'short'});
 const dateFormatter=new Intl.DateTimeFormat('en-US',{timeZone:data.timezone,month:'short',day:'numeric'});
 const timeFormatter=new Intl.DateTimeFormat('en-US',{timeZone:data.timezone,hour:'numeric',minute:'2-digit',timeZoneName:'short'});
 const local=s=>s?formatter.format(new Date(s)):'Not recorded';
 const num=(x,n=1)=>x===null||x===undefined?'—':Number(x).toFixed(n);
 const sign=x=>`${x>=0?'+':''}${num(x)}`;
 const esc=x=>String(x).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;').replaceAll("'",'&#39;');
 const pick=(g,h)=>h?g.home:g.away;
 const labelKind=k=>({archived_devigged_probability:'Archived no-vig probability',captured_devigged_probability:'Captured no-vig probability',
  archived_line:'Archived line center',captured_line:'Captured line center',trade:'Last recorded trade',minute_candle_close:'Minute candle close',
  book_midpoint:'Book midpoint',display_history:'Public display history'}[k]||String(k||'Reference').replaceAll('_',' '));
 function chosen(g,target,provider=state.provider){return reference(g,provider,target,state.horizon,data.prepared_at);}
 function marketCell(g){
  const win=chosen(g,'winner'),margin=chosen(g,'margin'),total=chosen(g,'total');
  const w=win.row,m=margin.row,t=total.row;
  if(!w&&!m&&!t){
   const known=g.markets[state.provider];
   const message=[win,margin,total].some(x=>x.status==='conflict')?'Conflicting stored references':known.length?'Provider records captured; no comparable price in this window':'No stored reference in this window';
   return `<span class="muted">${message}</span>${known.length?'<span class="sub">See Details for acquisition status</span>':''}`;
  }
  let text=w?`<strong>${esc(pick(g,w.picked_home))}</strong> <span>${num(Math.max(w.value,1-w.value)*100)}%</span>`:'<span class="muted">No winner reference</span>';
  if(m||t)text+=`<span class="sub">${m?'Home '+sign(m.value):'Margin —'} · ${t?'Total '+num(t.value):'Total —'}</span>`;
  const ref=w||m||t;
  text+=`<span class="sub">${ref.quote_at?esc(local(ref.quote_at)):'Captured '+esc(local(ref.captured_at))+' · quote clock unknown'}</span>`;
  if([win,margin,total].some(x=>x.status==='after_kickoff'))text+='<span class="pill warn">After kickoff</span>';
  else if(g.replay&&w&&g.replay.picked_home!==w.picked_home)text+='<span class="pill warn">Winner disagreement</span>';
  return text;
 }
 function gameRow(g){
  const r=g.replay;
  const when=g.kickoff_tbd?'Time TBD':timeFormatter.format(new Date(g.kickoff));
  const actual=g.completed?`<strong>${num(g.away_points,0)} · ${num(g.home_points,0)}</strong><span class="sub">Final</span>`:'<span class="pill quiet">Scheduled</span>';
  const original=r?`<strong>${esc(pick(g,r.picked_home))}</strong><span class="sub">${num((r.picked_home?r.p_home:1-r.p_home)*100)}%</span><span class="pill ${r.correct?'good':'bad'}">${r.correct?'Correct':'Incorrect'}</span>`:'<span class="muted">No recorded forecast</span>';
  const points=r?`<strong>${num(r.away_points)} · ${num(r.home_points)}</strong><span class="sub">Home margin ${sign(r.home_margin)}<br>Total ${num(r.total)}</span>`:'<span class="muted">Not issued</span>';
  return `<tr data-game-row="${esc(g.id)}"><td>${dateFormatter.format(new Date(g.kickoff))}<span class="sub">${esc(when)}<br>${esc(g.phase)} · week ${g.week}</span></td><th scope="row">${esc(g.away)}<span class="at"> at </span>${esc(g.home)}<span class="sub">${g.population==='FBS_V_FBS'?'FBS vs FBS':'FBS-involving · other opponent'}</span></th><td>${actual}</td><td>${original}</td><td>${points}</td><td>${marketCell(g)}</td><td><span class="pill quiet">Not issued</span></td><td><button class="detail-button" data-game="${esc(g.id)}" aria-label="Details for ${esc(g.away)} at ${esc(g.home)}">Details</button></td></tr>`;
 }
 function filtered(){return filterGames(data.games,state,data.windows,data.prepared_at);}
 function render(){
  const list=filtered(),pages=Math.max(1,Math.ceil(list.length/size));state.page=Math.min(state.page,pages-1);
  const visible=list.slice(state.page*size,(state.page+1)*size);
  $('games-body').innerHTML=visible.length?visible.map(gameRow).join(''):'<tr><td colspan="8"><div class="empty-state"><strong>No games match these filters.</strong>Clear the team search or choose All season to return to the complete inventory.</div></td></tr>';
  const covered=list.filter(g=>['winner','margin','total'].some(t=>chosen(g,t).row)).length;
  const replays=list.filter(g=>g.replay).length;
  $('result-status').innerHTML=`<strong>${list.length.toLocaleString()} game${list.length===1?'':'s'}</strong> · ${replays} original replay record${replays===1?'':'s'}`;
  $('reference-status').textContent=`${state.provider}: stored reference for ${covered} of ${list.length} games in this view`;
  $('market-column').textContent=`${state.provider} reference`;
  $('page-status').textContent=list.length?`${state.page*size+1}–${Math.min((state.page+1)*size,list.length)} of ${list.length} · Page ${state.page+1} of ${pages}`:'0 matching games';
  $('previous-page').disabled=state.page===0;$('next-page').disabled=state.page>=pages-1;
  document.querySelectorAll('[data-view]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.view===state.view)));
 }
 function detail(g){
  $('dialog-title').textContent=`${g.away} at ${g.home}`;
  $('dialog-subtitle').textContent=`${local(g.kickoff)}${g.kickoff_tbd?' · kickoff time unresolved':''} · ${g.phase}, week ${g.week} · Game ${g.id}`;
  const r=g.replay;
  $('dialog-summary').innerHTML=`<section class="detail-card"><h3>Actual result</h3><strong>${g.completed?`${num(g.away_points,0)}–${num(g.home_points,0)}`:'Scheduled'}</strong><p>${g.completed?`${esc(g.away)}–${esc(g.home)} · home margin ${sign(g.home_points-g.away_points)} · total ${num(g.home_points+g.away_points,0)}`:'The recorded source had not marked this game complete.'}</p></section><section class="detail-card"><h3>Original model</h3><strong>${r?esc(pick(g,r.picked_home)):'No recorded forecast'}</strong><p>${r?`${num((r.picked_home?r.p_home:1-r.p_home)*100)}% · ${r.correct?'Correct':'Incorrect'}<br>Projected score ${num(r.away_points)}–${num(r.home_points)}<br>Margin error ${sign(r.margin_error)} · total error ${sign(r.total_error)}<br>Retrospective replay; no historical issue timestamp.`:'No probability or point score is invented for this row.'}</p></section><section class="detail-card"><h3>Rolling model</h3><strong>Not issued</strong><p>Source-to-feature values and causal inputs remain unverified for native forecasting. Market collection remains available independently.</p></section>`;
  $('dialog-markets').innerHTML=providers.map(provider=>{
   let seen=false;const parts=['winner','margin','total'].map(target=>{
    const result=chosen(g,target,provider),ref=result.row;
    if(!ref){
     const catalog=g.markets[provider].filter(r=>r.target===target).sort((a,b)=>clock(b.captured_at)-clock(a.captured_at))[0];
     return `<div class="reference"><strong>${target==='winner'?'Winner':target==='margin'?'Home margin':'Total'}</strong><span class="sub">${result.status==='conflict'?'Conflicting stored values at the same clock.':'No comparable reference in the selected window.'}</span>${catalog?`<p>Provider record captured ${esc(local(catalog.captured_at))}. ${catalog.quote_at?'Source event clock: '+esc(local(catalog.quote_at))+'.':'Individual quote timestamp not provided.'} Status: ${esc(String(catalog.price_status||'catalog only').replaceAll('_',' ').toLowerCase())}.</p>${catalog.event_url?`<a href="${esc(catalog.event_url)}" target="_blank" rel="noopener noreferrer">Open provider event ↗</a>`:''}`:''}</div>`;
    }
    seen=true;
    const value=target==='winner'?`${esc(pick(g,ref.picked_home))} · ${num(Math.max(ref.value,1-ref.value)*100)}%`:target==='margin'?sign(ref.value):num(ref.value);
    return `<div class="reference"><strong>${target==='winner'?'Winner':target==='margin'?'Home margin':'Total'}: ${value}</strong>${result.status==='after_kickoff'?' <span class="pill warn">After kickoff</span>':''}<span class="sub">${esc(labelKind(ref.reference_kind))}</span><dl><dt>Source quote</dt><dd>${ref.quote_at?esc(local(ref.quote_at)):'Unknown; capture clock is not a quote clock'}</dd><dt>Captured</dt><dd>${ref.captured_at?esc(local(ref.captured_at)):'Historical possession unproved'}</dd><dt>Use</dt><dd>${ref.evidence_kind==='recovered_historical_observation'?'Recovered historical reference':ref.evidence_kind==='recorded_early_snapshot'?'Recorded early reference':ref.evidence_kind==='current_public_observation'?'Current public snapshot':'Retrospective comparison reference'}</dd><dt>Identity</dt><dd>${esc(String(ref.identity_basis).replaceAll('_',' ').toLowerCase())}</dd></dl>${ref.event_url?`<a href="${esc(ref.event_url)}" target="_blank" rel="noopener noreferrer">Open provider event ↗</a>`:''}</div>`;
   }).join('');
   return `<section class="market-detail"><h3>${esc(provider)} <span class="pill ${seen?'good':'quiet'}">${seen?'Stored reference':g.markets[provider].length?'Records captured':'Coverage gap'}</span></h3>${parts}</section>`;
  }).join('');
  $('dialog-footer').textContent=`Schedule source observed ${local(g.source_at)}. Every reference retains its source and acquisition clocks. None is a verified executable offer; no fee, liquidity, settlement, P&L or ROI claim is inferred. Decision: NO BET; stake $0.`;
  $('game-dialog').showModal();
 }
 function exportCSV(){
  const cols=['game_id','season','phase','native_week','kickoff_utc','away_team','home_team','completed','actual_away_points','actual_home_points','original_evidence','original_p_home','original_winner','original_away_points','original_home_points','original_home_margin','original_total','original_correct','rolling_status','provider','reference_window','market_winner','derived_home_probability','implied_home_margin','implied_total','winner_quote_at','winner_captured_at','winner_reference_kind','margin_quote_at','total_quote_at','NO_BET'];
  const rows=filtered().map(g=>{const r=g.replay,w=chosen(g,'winner').row,m=chosen(g,'margin').row,t=chosen(g,'total').row;return [g.id,g.season,g.phase,g.week,g.kickoff,g.away,g.home,g.completed,g.away_points,g.home_points,r?'retrospective_original_replay':'no_recorded_forecast',r?.p_home,r?pick(g,r.picked_home):null,r?.away_points,r?.home_points,r?.home_margin,r?.total,r?.correct,'not_issued',state.provider,state.horizon,w?pick(g,w.picked_home):null,w?.value,m?.value,t?.value,w?.quote_at,w?.captured_at,w?.reference_kind,m?.quote_at,t?.quote_at,true];});
  const csv=[cols,...rows].map(row=>row.map(csvCell).join(',')).join('\r\n')+'\r\n';
  const url=URL.createObjectURL(new Blob([csv],{type:'text/csv;charset=utf-8'}));
  const a=document.createElement('a');a.href=url;a.download=`fbs-2026-${state.view}-comparison.csv`;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
 }
 function coverage(){
  $('coverage-cards').innerHTML=data.provider_coverage.map(p=>{
   const refs=data.games.flatMap(g=>g.markets[p.provider]);const clocks=refs.map(r=>r.captured_at).filter(Boolean).sort();
   const newest=clocks.length?local(clocks[clocks.length-1]):'No captured panel in this export';
   return `<article class="coverage-card"><h3>${esc(p.provider)}</h3><div class="coverage-value">${p.observed_games}<span class="measure"> / ${data.inventory.observed_games} games with records</span></div><p>${p.completed_games} completed · ${p.scheduled_games} scheduled</p><p>${p.numeric_observations} numeric references on ${p.numeric_reference_games} games<br>${p.timestamped_reference_games} games with a timestamped reference</p><p class="clock">Latest represented capture<br><strong>${esc(newest)}</strong></p></article>`;
  }).join('');
 }
 function weekly(){
  const groups=new Map();
  data.games.filter(g=>g.replay).forEach(g=>{const key=`${g.phase}:${g.week}`;if(!groups.has(key))groups.set(key,{phase:g.phase,week:g.week,n:0,correct:0});const r=groups.get(key);r.n++;r.correct+=Number(g.replay.correct);});
  const rows=[...groups.values()].sort((a,b)=>a.phase.localeCompare(b.phase)||a.week-b.week),max=Math.max(...rows.map(r=>r.n));
  const h=rows.length*31+25;
  $('weekly-chart').innerHTML=`<svg class="svg-chart" viewBox="0 0 500 ${h}" role="img" aria-label="All nine original replay weeks, correct and incorrect winners"><title>Original replay correctness by native week</title>${rows.map((r,i)=>`<g transform="translate(0,${i*31+4})"><text class="chart-label" x="0" y="15">Week ${r.week}</text><rect x="62" y="0" width="${r.n/max*320}" height="20" rx="3" fill="#f3d4dc"></rect><rect x="62" y="0" width="${r.correct/max*320}" height="20" rx="3" fill="#247c70"></rect><text class="chart-label" x="397" y="15">${r.correct} / ${r.n}</text></g>`).join('')}<g transform="translate(62,${h-5})"><rect x="0" y="-9" width="9" height="9" fill="#247c70"></rect><text class="chart-label" x="15" y="0">Correct</text><rect x="95" y="-9" width="9" height="9" fill="#f3d4dc"></rect><text class="chart-label" x="110" y="0">Incorrect</text></g></svg>`;
 }
 $('evidence-clock').textContent=`Owner evidence ${local(data.assessed_at)}`;
 $('observed-count').textContent=data.inventory.observed_games;
 $('observed-note').textContent=`${data.inventory.completed_games} completed · ${data.inventory.scheduled_games} scheduled`;
 $('current-count').textContent=data.inventory.current_week_games;
 $('replay-record').innerHTML=`${data.metrics.season.winner.correct} <small>/ ${data.metrics.season.winner.games}</small>`;
 $('replay-note').textContent=`${num(data.metrics.season.winner.accuracy*100,2)}% correct · retrospective`;
 $('last-record').innerHTML=`${data.metrics.last_week.winner.correct} <small>/ ${data.metrics.last_week.winner.games}</small>`;
 const phases=[...new Set(data.games.map(g=>`${g.phase}:${g.week}`))].sort((a,b)=>a.split(':')[0].localeCompare(b.split(':')[0])||Number(a.split(':')[1])-Number(b.split(':')[1]));
 phases.forEach(phase=>{const option=document.createElement('option');option.value=phase;option.textContent=phase.replace(':',' · week ');$('native-week').append(option);});
 document.querySelectorAll('[data-view]').forEach(b=>b.addEventListener('click',()=>{state.view=b.dataset.view;state.week='all';$('native-week').value='all';state.page=0;render();}));
 $('game-search').addEventListener('input',()=>{state.query=$('game-search').value;state.page=0;render();});
 [['native-week','week'],['provider-select','provider'],['horizon-select','horizon']].forEach(([id,key])=>$(id).addEventListener('change',()=>{state[key]=$(id).value;state.page=0;render();}));
 $('disagreements-only').addEventListener('change',()=>{state.disagreements=$('disagreements-only').checked;state.page=0;render();});
 $('previous-page').addEventListener('click',()=>{state.page--;render();});$('next-page').addEventListener('click',()=>{state.page++;render();});
 $('games-body').addEventListener('click',event=>{const button=event.target.closest('[data-game]');if(button)detail(data.games.find(g=>g.id===button.dataset.game));});
 $('close-dialog').addEventListener('click',()=>$('game-dialog').close());
 $('game-dialog').addEventListener('click',event=>{if(event.target===$('game-dialog')){const box=event.target.getBoundingClientRect();if(event.clientX<box.left||event.clientX>box.right||event.clientY<box.top||event.clientY>box.bottom)event.target.close();}});
 $('export-csv').addEventListener('click',exportCSV);
 $('view-disagreements').addEventListener('click',()=>{state.view='completed';state.provider='DraftKings';state.horizon='T120';state.week='all';state.query='';state.disagreements=true;state.page=0;$('provider-select').value=state.provider;$('horizon-select').value=state.horizon;$('native-week').value='all';$('game-search').value='';$('disagreements-only').checked=true;render();});
 coverage();weekly();render();
})();
