'use strict';
(() => {
 const providers=['DraftKings','Kalshi','Polymarket US','Polymarket Global'];
 const clock=value=>value?Date.parse(value):NaN;
 const finite=Number.isFinite;
 function unpack(data){
  if(data.schema==='fbs.public.season-explorer.v1')return data;
  if(data.schema!=='fbs.public.season-explorer.transport.v1'||!Array.isArray(data.reference_fields)||new Set(data.reference_fields).size!==data.reference_fields.length)throw new Error('Invalid public reference transport');
  const fields=data.reference_fields,report=data.report;
  for(const game of report.games)for(const provider of Object.keys(game.markets))game.markets[provider]=game.markets[provider].map(row=>{
   if(!Array.isArray(row)||row.length!==fields.length)throw new Error('Public reference column count differs');
   return Object.fromEntries(fields.map((key,index)=>[key,row[index]]));
  });
  return report;
 }
 function signature(row){
  const products={winner:['SPORTSBOOK_WINNER_H2H_DEVIGGED','sportsbook_winner','sportsbook_game_market'],margin:['SPORTSBOOK_HOME_MARGIN_LINE','sportsbook_home_margin_line','sportsbook_game_market'],total:['SPORTSBOOK_TOTAL_LINE','sportsbook_total_line','sportsbook_game_market']};
  const kinds={winner:['archived_devigged_probability','captured_devigged_probability','vig_removed_two_way_probability'],margin:['archived_line','captured_line','sportsbook_point_line'],total:['archived_line','captured_line','sportsbook_point_line']};
  if(products[row.target]?.includes(row.product)&&kinds[row.target]?.includes(row.reference_kind))return JSON.stringify([row.value,row.picked_home,'equivalent_sportsbook_'+row.target]);
  return JSON.stringify([row.value,row.picked_home,row.reference_kind,row.product]);
 }
 function pointBounds(row,cutoff,assessed,strictBefore=false){
  const support=row?.point_support;
  if(!support)return null;
  const permitted=(value,at)=>Number.isFinite(value)&&clock(at)<=clock(assessed)&&(strictBefore?clock(at)<cutoff:clock(at)<=cutoff);
  const lower=permitted(support.lower_bound,support.lower_capture_at)?support.lower_bound:null;
  const upper=permitted(support.upper_bound,support.upper_capture_at)?support.upper_bound:null;
  const status=lower!==null&&upper!==null?(lower<upper?'bounded':'inconsistent'):lower!==null?'lower_only':upper!==null?'upper_only':'unresolved';
  return {lower,upper,status,method:support.method};
 }
 function reference(game,provider,target,horizon,assessed){
  if(horizon==='auto')horizon=game.completed?'latest_available_pregame':'current';
  const kick=clock(game.kickoff);
  const cutoff=horizon==='T60'?kick-3600000:horizon==='T120'?kick-7200000:horizon==='current'?clock(assessed):kick;
  if(game.kickoff_tbd&&horizon!=='current')return {row:null,status:'kickoff_tbd',cutoff};
  const strictBefore=['latest_pre_kickoff','latest_available_pregame'].includes(horizon);
  const effective=r=>clock(r.quote_at||r.captured_at);
  const end=r=>clock(r.interval_end_at||r.quote_at||r.captured_at);
  const registeredWindow=['T120','T60'].includes(horizon)?horizon:'LATEST_BEFORE_KICKOFF';
  const displayValue=r=>{
   if(Number.isFinite(r.value))return true;
   if(!['margin','total'].includes(target)||r.point_support?.method!=='CAPTURED_BID_ASK_HALF_PROBABILITY_SUPPORT')return false;
   const supported=pointBounds(r,cutoff,assessed,strictBefore);
   return supported&&supported.status!=='unresolved';
  };
  let rows=game.markets[provider].filter(r=>r.target===target&&r.join_status==='matched'&&displayValue(r)&&
   (!r.registered_cutoff_kind||r.registered_cutoff_kind===registeredWindow)&&
   effective(r)<=clock(assessed)&&end(r)<=clock(assessed)&&end(r)>=effective(r)&&(!r.captured_at||clock(r.captured_at)<=clock(assessed))&&
   (strictBefore?effective(r)<cutoff&&end(r)<cutoff:effective(r)<=cutoff&&end(r)<=cutoff));
  if(!rows.length)return {row:null,status:'absent',cutoff};
  // Preserve the registered source-timed benchmark selector. The new display
  // view also considers a later authenticated capture-only pregame snapshot.
  if(!['current','latest_available_pregame'].includes(horizon)){const timestamped=rows.filter(r=>r.quote_at);if(timestamped.length)rows=timestamped;}
  const latest=Math.max(...rows.map(effective)),same=rows.filter(r=>effective(r)===latest);
  const signatures=new Set(same.map(r=>JSON.stringify([signature(r),r.picked_home,
   r.point_support?['method','status','lower_bound','upper_bound','lower_capture_at','upper_capture_at','support_available_at','diagnostic_probability_band_width'].map(k=>r.point_support[k]):null])));
  if(signatures.size!==1)return {row:null,status:'conflict',cutoff};
  same.sort((a,b)=>Number(!a.captured_at)-Number(!b.captured_at)||(a.captured_at||'').localeCompare(b.captured_at||''));
  const pending=horizon!=='current'&&cutoff>clock(assessed);
  const basis=same[0].quote_at?'provider_quote_at':'retrieved_at';
  const status=pending?'cutoff_pending':latest>=kick?'after_kickoff':basis==='retrieved_at'?(horizon==='current'?'quote_clock_unknown':'captured_available_by_cutoff'):'available';
  return {row:same[0],status,cutoff,pending,clock_basis:basis};
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
 if(typeof module!=='undefined'&&module.exports)module.exports={reference,filterGames,csvCell,pointBounds,unpack};
 if(typeof document==='undefined')return;
 const data=unpack(JSON.parse(document.getElementById('season-data').textContent));
 const state={view:'all',week:'all',query:'',provider:'DraftKings',horizon:'auto',disagreements:false,page:0};
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
  book_midpoint:'Book midpoint',minute_book_midpoint:'Minute book midpoint',minute_trade_close:'Minute trade close',
  book_derived_display_midpoint:'Book-derived display midpoint',provider_price_history_interval:'Provider history interval',
  provider_price_history_exact_observation:'Provider history observation',catalog_bid_ask_midpoint:'Catalog midpoint · quote clock unknown',
  implied_threshold_center_from_catalog_bid_ask_midpoint:'Closest-to-50% threshold · diagnostic center',
  display_history:'Public display history'}[k]||String(k||'Reference').replaceAll('_',' '));
 function chosen(g,target,provider=state.provider){return reference(g,provider,target,state.horizon,data.prepared_at);}
 function bounds(g,result){return pointBounds(result.row,result.cutoff,data.prepared_at,['latest_pre_kickoff','latest_available_pregame'].includes(state.horizon)||state.horizon==='auto'&&g.completed);}
 function pointValue(g,result,target){
  const row=result.row;if(!row)return target==='margin'?'Margin —':'Total —';
  const b=bounds(g,result),label=target==='margin'?'Home':'Total',format=target==='margin'?sign:num;
  if(!b)return label+' '+format(row.value);
  if(b.status==='bounded')return label+' '+format(b.lower)+' to '+format(b.upper);
  if(b.status==='lower_only')return label+' > '+format(b.lower);
  if(b.status==='upper_only')return label+' < '+format(b.upper);
  return label+(b.status==='inconsistent'?' bounds inconsistent':' center unresolved');
 }
 function marketCell(g){
  const win=chosen(g,'winner'),margin=chosen(g,'margin'),total=chosen(g,'total');
  const w=win.row,m=margin.row,t=total.row;
  if(!w&&!m&&!t){
   const known=g.markets[state.provider];
   const message=[win,margin,total].some(x=>x.status==='conflict')?'Conflicting stored references':known.length?'Provider records captured; no comparable price in this window':'No stored reference in this window';
   return `<span class="muted">${message}</span>${known.length?'<span class="sub">See Details for acquisition status</span>':''}`;
  }
  let text=w?`<strong>${esc(pick(g,w.picked_home))}</strong> <span>${num(Math.max(w.value,1-w.value)*100)}%</span>`:'<span class="muted">No winner reference</span>';
  if(m||t)text+=`<span class="sub">${esc(pointValue(g,margin,'margin'))} · ${esc(pointValue(g,total,'total'))}</span>`;
  if([m,t].some(r=>r?.point_support))text+='<span class="sub">Captured probability-band bounds</span>';
  else if([m,t].some(r=>r&&String(r.reference_kind).startsWith('implied_threshold_center')))text+='<span class="sub">Historical threshold proxy</span>';
  // A winner clock must not stand in for a separately observed point product.
  for(const [label,ref] of [['Winner',w],['Home margin',m],['Total',t]]){
   text+=`<span class="sub">${label}: ${ref?(ref.quote_at?'source '+esc(local(ref.quote_at)):'captured '+esc(local(ref.captured_at))+' · quote time unknown'):'no compatible reference'}</span>`;
  }
  if([win,margin,total].some(x=>x.status==='after_kickoff'))text+='<span class="pill warn">After kickoff</span>';
  else if([win,margin,total].some(x=>x.pending))text+='<span class="pill warn">Latest known · cutoff pending</span>';
  else if([win,margin,total].some(x=>x.status==='captured_available_by_cutoff'))text+='<span class="sub">Captured snapshot available by cutoff</span>';
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
  const pending=list.filter(g=>['winner','margin','total'].some(t=>chosen(g,t).row&&chosen(g,t).pending)).length;
  const replays=list.filter(g=>g.replay).length;
  $('result-status').innerHTML=`<strong>${list.length.toLocaleString()} game${list.length===1?'':'s'}</strong> · ${replays} original replay record${replays===1?'':'s'}`;
  $('reference-status').textContent=`${state.provider}: stored reference for ${covered} of ${list.length} games in this view${pending?' · '+pending+' cutoff windows pending':''}`;
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
    const value=target==='winner'?`${esc(pick(g,ref.picked_home))} · ${num(Math.max(ref.value,1-ref.value)*100)}%`:esc(pointValue(g,result,target));
    const availability=result.pending?'Latest known snapshot; cutoff pending':result.status==='captured_available_by_cutoff'?'Captured snapshot available by cutoff':result.status==='after_kickoff'?'After kickoff; excluded from pregame comparisons':result.clock_basis==='retrieved_at'?'Available at capture; individual quote clock unknown':'Source-timed reference in selected window';
    const sourceStatus=ref.source_status===null||ref.source_status===undefined?'Not supplied':Array.isArray(ref.source_status)?ref.source_status.join(', '):String(ref.source_status);
    const support=ref.point_support;
    const diagnosticRows=support?[ref,...g.markets[provider]].filter(row=>row.target===target&&row.point_support&&finite(row.value)&&clock(row.captured_at)<=clock(ref.captured_at)&&clock(row.captured_at)<=clock(data.prepared_at)&&clock(row.captured_at)<=result.cutoff&&(!(['latest_pre_kickoff','latest_available_pregame'].includes(state.horizon)||state.horizon==='auto'&&g.completed)||clock(row.captured_at)<clock(g.kickoff))).sort((a,b)=>clock(b.captured_at)-clock(a.captured_at)):[];
    const diagnosticLatest=diagnosticRows.filter(row=>row.captured_at===diagnosticRows[0]?.captured_at);
    const diagnosticRow=new Set(diagnosticLatest.map(row=>JSON.stringify([row.value,row.point_support]))).size===1?diagnosticLatest[0]:null;
    const diagnosticSupport=diagnosticRow?.point_support;
    const diagnostic=support?`<p>Bounds use captured probability bands lying wholly above or below 50%. They are descriptive market bounds, not projected scores, executable offers or a confidence interval. Each supporting capture must qualify for this window.</p><p>Lower support captured ${esc(local(support.lower_capture_at))}; upper support captured ${esc(local(support.upper_capture_at))}.</p><details><summary>Preserved midpoint diagnostic</summary>${diagnosticRow?`<p>${diagnosticRow===ref?'Nearest-half threshold':'Earlier nearest-half threshold'}: ${num(diagnosticRow.value)}. Captured ${esc(local(diagnosticRow.captured_at))}. ${finite(diagnosticSupport.diagnostic_probability_band_width)?'Its probability-band width is '+num(diagnosticSupport.diagnostic_probability_band_width*100)+' percentage points. ':''}A band spanning 50% does not locate a central line. This older diagnostic is retained for audit, not used as the current primary point reference.</p>`:'<p>No eligible scalar center is supported by this capture. A point probability ladder is not an expected-score estimate.</p>'}</details>`:'';
    return `<div class="reference"><strong>${target==='winner'?'Winner':target==='margin'?'Home margin':'Total'}: ${value}</strong>${result.status==='after_kickoff'?' <span class="pill warn">After kickoff</span>':''}${result.pending?' <span class="pill warn">Cutoff pending</span>':''}<span class="sub">${support?'Supported threshold bounds':esc(labelKind(ref.reference_kind))}</span><dl><dt>Source quote</dt><dd>${ref.quote_at?esc(local(ref.quote_at)):'Not supplied; no individual quote time is invented'}</dd><dt>${support?'Diagnostic capture':'Captured'}</dt><dd>${ref.captured_at?esc(local(ref.captured_at)):'Historical possession unproved'}</dd>${support?'<dt>Bounds available</dt><dd>'+esc(local(support.support_available_at))+'</dd>':''}<dt>Availability</dt><dd>${esc(availability)}</dd><dt>Clock basis</dt><dd>${result.clock_basis==='retrieved_at'?'Authenticated capture time':'Provider observation time'}</dd>${ref.source_query_cutoff_kind?'<dt>Source query window</dt><dd>'+esc(ref.source_query_cutoff_kind.replaceAll('_',' ').toLowerCase())+'</dd>':''}${ref.registered_cutoff_kind?'<dt>Registered proxy window</dt><dd>'+esc(ref.registered_cutoff_kind.replaceAll('_',' ').toLowerCase())+'</dd>':''}<dt>Source status</dt><dd>${esc(sourceStatus)}${ref.source_status_field?' ('+esc(ref.source_status_field)+')':''}</dd><dt>Use</dt><dd>${ref.evidence_kind==='recovered_historical_observation'?'Recovered historical reference':ref.evidence_kind==='recorded_early_snapshot'?'Recorded early reference':ref.evidence_kind==='current_public_observation'?'Current public snapshot':'Retrospective comparison reference'}</dd><dt>Identity</dt><dd>${esc(String(ref.identity_basis).replaceAll('_',' ').toLowerCase())}</dd></dl>${diagnostic}${ref.event_url?`<a href="${esc(ref.event_url)}" target="_blank" rel="noopener noreferrer">Open provider event ↗</a>`:''}</div>`;
   }).join('');
   return `<section class="market-detail"><h3>${esc(provider)} <span class="pill ${seen?'good':'quiet'}">${seen?'Stored reference':g.markets[provider].length?'Records captured':'Coverage gap'}</span></h3>${parts}</section>`;
  }).join('');
  $('dialog-footer').textContent=`Schedule source observed ${local(g.source_at)}. Every reference retains its source and acquisition clocks. None is a verified executable offer; no fee, liquidity, settlement, P&L or ROI claim is inferred. Decision: NO BET; stake $0.`;
  $('game-dialog').showModal();
 }
 function exportCSV(){
  const cols=['game_id','season','phase','native_week','kickoff_utc','away_team','home_team','completed','actual_away_points','actual_home_points','original_evidence','original_p_home','original_winner','original_away_points','original_home_points','original_home_margin','original_total','original_correct','rolling_status','provider','reference_window','market_winner','derived_home_probability','margin_reference_or_preserved_diagnostic','total_reference_or_preserved_diagnostic','winner_quote_at','winner_captured_at','winner_reference_kind','winner_clock_basis','winner_window_status','margin_quote_at','margin_diagnostic_capture_at','margin_clock_basis','margin_window_status','margin_reference_kind','margin_bound_status','margin_lower_bound','margin_upper_bound','margin_support_available_at','total_quote_at','total_diagnostic_capture_at','total_clock_basis','total_window_status','total_reference_kind','total_bound_status','total_lower_bound','total_upper_bound','total_support_available_at','NO_BET'];
  const rows=filtered().map(g=>{const r=g.replay,wr=chosen(g,'winner'),mr=chosen(g,'margin'),tr=chosen(g,'total'),w=wr.row,m=mr.row,t=tr.row,mb=bounds(g,mr),tb=bounds(g,tr);return [g.id,g.season,g.phase,g.week,g.kickoff,g.away,g.home,g.completed,g.away_points,g.home_points,r?'retrospective_original_replay':'no_recorded_forecast',r?.p_home,r?pick(g,r.picked_home):null,r?.away_points,r?.home_points,r?.home_margin,r?.total,r?.correct,'not_issued',state.provider,state.horizon==='auto'?(g.completed?'latest_available_pregame':'current'):state.horizon,w?pick(g,w.picked_home):null,w?.value,m?.value,t?.value,w?.quote_at,w?.captured_at,w?.reference_kind,wr.clock_basis,wr.status,m?.quote_at,m?.captured_at,mr.clock_basis,mr.status,m?.reference_kind,mb?.status,mb?.lower,mb?.upper,m?.point_support?.support_available_at,t?.quote_at,t?.captured_at,tr.clock_basis,tr.status,t?.reference_kind,tb?.status,tb?.lower,tb?.upper,t?.point_support?.support_available_at,true];});
  const csv=[cols,...rows].map(row=>row.map(csvCell).join(',')).join('\r\n')+'\r\n';
  const url=URL.createObjectURL(new Blob([csv],{type:'text/csv;charset=utf-8'}));
  const a=document.createElement('a');a.href=url;a.download=`fbs-2026-${state.view}-comparison.csv`;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
 }
 function coverage(){
  const recovery=data.provider_acquisition_summary.filter(p=>p.status==='PARTIAL_HISTORICAL_RECOVERY'||p.status==='COMPLETE_CAPTURE');
  $('history-recovery-status').textContent=recovery.length?`Historical recovery snapshot: ${recovery.map(p=>`${p.provider} ${p.historical_price_rows.toLocaleString()} source-timed references`).join(' · ')}. ${recovery.some(p=>p.status==='PARTIAL_HISTORICAL_RECOVERY')?'Partial recovery; further games remain unresolved.':'Captured recovery pass complete; absent markets remain explicit.'} Retrieval ${local(recovery.map(p=>p.retrieved_at).filter(Boolean).sort().at(-1))}.`:'Historical recovery is not represented in this snapshot.';
  const acquisition=data.reporting_contract.acquisition_status;
  if(acquisition)$('history-recovery-status').textContent+=` Preserved earlier benchmark pass: ${acquisition.processed_contracts.toLocaleString()} contracts processed; ${acquisition.failed_contracts} failed contract reads and ${acquisition.unprocessed_global_alternate_contracts.toLocaleString()} Global alternate contracts were unresolved at that snapshot. The separately dated source-progress panel below describes newer processing; these benchmark numbers are not silently rescored.`;
  $('coverage-cards').innerHTML=data.provider_coverage.map(p=>{
   const refs=data.games.flatMap(g=>g.markets[p.provider]);const clocks=refs.map(r=>r.captured_at).filter(Boolean).sort();
   const newest=clocks.length?local(clocks[clocks.length-1]):'No captured panel in this export';
   const window=data.windows.current_calendar_week;
   const current=data.games.filter(g=>clock(g.kickoff)>=clock(window.start_inclusive_utc)&&clock(g.kickoff)<clock(window.end_exclusive_utc));
   const targets=['winner','margin','total'].map(target=>current.filter(g=>reference(g,p.provider,target,'current',data.prepared_at).row).length);
   const supported=['margin','total'].map(target=>current.map(g=>pointBounds(reference(g,p.provider,target,'current',data.prepared_at).row,clock(data.prepared_at),data.prepared_at)).filter(Boolean));
   const pointNote=['Kalshi','Polymarket Global'].includes(p.provider)?`<p>Supported finite intervals: margin ${supported[0].filter(b=>b.status==='bounded').length} · total ${supported[1].filter(b=>b.status==='bounded').length}<br>One-sided bounds: margin ${supported[0].filter(b=>b.status==='lower_only'||b.status==='upper_only').length} · total ${supported[1].filter(b=>b.status==='lower_only'||b.status==='upper_only').length}</p>`:'';
   return `<article class="coverage-card"><h3>${esc(p.provider)}</h3><div class="coverage-value">${p.observed_games}<span class="measure"> / ${data.inventory.observed_games} games with records</span></div><p>${p.completed_games} completed · ${p.scheduled_games} scheduled</p><p>${p.numeric_observations} numeric records on ${p.numeric_reference_games} games, including preserved diagnostics<br>${p.timestamped_reference_games} games with a timestamped reference</p><p><strong>This week’s latest records</strong><br>Winner ${targets[0]} / ${current.length}<br>Margin ${targets[1]} / ${current.length} · total ${targets[2]} / ${current.length}</p>${pointNote}<p class="clock">Latest represented capture<br><strong>${esc(newest)}</strong></p></article>`;
  }).join('');
 }
 function weekly(){
  const groups=new Map();
  data.games.filter(g=>g.replay).forEach(g=>{const key=`${g.phase}:${g.week}`;if(!groups.has(key))groups.set(key,{phase:g.phase,week:g.week,n:0,correct:0});const r=groups.get(key);r.n++;r.correct+=Number(g.replay.correct);});
  const rows=[...groups.values()].sort((a,b)=>a.phase.localeCompare(b.phase)||a.week-b.week),max=Math.max(...rows.map(r=>r.n));
  const h=rows.length*31+25;
  $('weekly-chart').innerHTML=`<svg class="svg-chart" viewBox="0 0 500 ${h}" role="img" aria-label="All nine original replay weeks, correct and incorrect winners"><title>Original replay correctness by native week</title>${rows.map((r,i)=>`<g transform="translate(0,${i*31+4})"><text class="chart-label" x="0" y="15">Week ${r.week}</text><rect x="62" y="0" width="${r.n/max*320}" height="20" rx="3" fill="#f3d4dc"></rect><rect x="62" y="0" width="${r.correct/max*320}" height="20" rx="3" fill="#247c70"></rect><text class="chart-label" x="397" y="15">${r.correct} / ${r.n}</text></g>`).join('')}<g transform="translate(62,${h-5})"><rect x="0" y="-9" width="9" height="9" fill="#247c70"></rect><text class="chart-label" x="15" y="0">Correct</text><rect x="95" y="-9" width="9" height="9" fill="#f3d4dc"></rect><text class="chart-label" x="110" y="0">Incorrect</text></g></svg>`;
 }
 $('evidence-clock').textContent=`Source evidence review ${local(data.assessed_at)}`;
 $('data-clock').textContent=`Schedule captured ${local(data.games.map(g=>g.source_at).sort().at(-1))}`;
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
