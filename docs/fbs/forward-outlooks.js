'use strict';
(() => {
  const targets = ['winner', 'margin', 'total'];
  const labels = {winner:'Winner & probability', margin:'Home margin', total:'Total points', cover:'Exact-line cover'};
  const time = value => typeof value === 'string' && Number.isFinite(Date.parse(value)) ? Date.parse(value) : null;
  const same = (a,b) => a !== null && a !== undefined && b !== null && b !== undefined && String(a) === String(b);
  function matchesEpoch(game, row) {
    return !!row && game.kickoff_exact === true && same(game.id,row.id) && same(game.season,row.season)
      && same(game.home_id,row.home_id) && same(game.away_id,row.away_id)
      && time(game.kickoff) !== null && time(game.kickoff) === time(row.kickoff);
  }
  function recordIndex(report) {
    const index=new Map(), duplicates=new Set();
    for(const row of report?.rows || []) {
      const id=String(row.id);
      if(index.has(id))duplicates.add(id);
      else index.set(id,row);
    }
    for(const id of duplicates)index.delete(id);
    return {index,duplicates};
  }
  function coverage(game, report, indexed=recordIndex(report)) {
    const id=String(game.id), candidate=indexed.index.get(id);
    let reason=null;
    if(!game.kickoff_exact || time(game.kickoff)===null)reason='EXACT_KICKOFF_UNRESOLVED';
    else if(indexed.duplicates.has(id))reason='AMBIGUOUS_CURRENT_OUTLOOK_IDENTITY';
    else if(!candidate)reason=game.completed?'OUTSIDE_CURRENT_OUTLOOK_SCOPE':'CURRENT_OUTLOOK_NOT_RECORDED';
    else if(!matchesEpoch(game,candidate))reason='CURRENT_OUTLOOK_FIXTURE_EPOCH_MISMATCH';
    const row=reason?null:candidate, issued=!!row && row.original_issue_verified===true;
    const cutoff=time(row?.information_cutoff_utc), computed=time(row?.computed_at_utc), issue=time(row?.issued_at_utc), kickoff=time(game.kickoff);
    const validOrder=cutoff!==null && computed!==null && issue!==null && kickoff!==null && cutoff<=computed && computed<=issue && issue<kickoff;
    const qualified=issued && validOrder && row.horizon==='CURRENT_ORIGIN_OUTLOOK';
    const targetStates=Object.fromEntries(targets.map(target=>{
      const state=row?.targets?.[target];
      return [target,reason || (state?.available===true ? qualified?'AUTHENTICATED_PRIVATE_OUTLOOK':'SAVED_PRIVATE_OUTPUT_UNQUALIFIED_ISSUE':state?.reason || 'TARGET_OUTPUT_NOT_RECORDED')];
    }));
    targetStates.cover='NO_QUALIFIED_EXACT_LINE_DISTRIBUTION';
    const allTargets=targets.every(target=>row?.targets?.[target]?.available===true);
    const status=reason || (qualified && allTargets?'AUTHENTICATED_CURRENT_ORIGIN_OUTLOOK':qualified?'PARTIAL_CURRENT_ORIGIN_OUTLOOK':'ISSUE_PROOF_NOT_QUALIFIED');
    const next=reason==='EXACT_KICKOFF_UNRESOLVED'?'Resolve the official kickoff, then register its forecast identity.':
      reason==='CURRENT_OUTLOOK_FIXTURE_EPOCH_MISMATCH' || reason==='AMBIGUOUS_CURRENT_OUTLOOK_IDENTITY'?'Reconcile the original ordered teams and kickoff; do not rebind a saved forecast.':
      reason==='OUTSIDE_CURRENT_OUTLOOK_SCOPE'?'Use the dated historical comparison; this forward study targets remaining games.':
      !qualified?'Recover or produce the missing eligible outlook and its original issue proof.':
      !allTargets?'Complete the missing target under the original source and horizon gates.':
      'Refresh approaching-game inputs and issue each later registered horizon before its own deadline.';
    return {id,game,record:row,status,reason,targets:targetStates,original_issue_verified:qualified,all_targets_available:allTargets,
      interval_status:row?.interval_status || 'INTERVAL_OUTPUT_NOT_RECORDED',
      distribution_status:row?.distribution_status || 'JOINT_SCORE_OUTPUT_NOT_RECORDED',
      information_cutoff_utc:row?.information_cutoff_utc || null,computed_at_utc:row?.computed_at_utc || null,issued_at_utc:row?.issued_at_utc || null,
      horizon:row?.horizon || null,lead_hours:qualified?(kickoff-issue)/3600000:null,
      close_horizon_issues:qualified&&Number.isInteger(row.qualified_close_horizon_issues)&&row.qualified_close_horizon_issues>0?row.qualified_close_horizon_issues:0,next_action:next};
  }
  function inventory(games, report) {
    const indexed=recordIndex(report);
    return games.filter(game=>game.season===2026 && !game.completed).map(game=>coverage(game,report,indexed));
  }
  function select(rows,{scope='upcoming',query='',status='all',target='all'}={}) {
    const q=query.trim().toLowerCase();
    return rows.filter(row=>(scope==='all'||scope==='upcoming'&&row.game.period==='upcoming'||scope==='exact'&&row.game.kickoff_exact||scope==='unresolved'&&!row.game.kickoff_exact)
      &&(!q||`${row.id} ${row.game.away} ${row.game.home}`.toLowerCase().includes(q))
      &&(status==='all'||status==='issued'&&row.original_issue_verified||status==='missing'&&!row.original_issue_verified)
      &&(target==='all'||(targets.includes(target)||target==='cover'?row.targets[target]!=='AUTHENTICATED_PRIVATE_OUTLOOK':
        target==='saved_intervals'?!row.original_issue_verified||row.interval_status!=='SAVED_MODEL_INTERVALS_CALIBRATION_UNPROVED':
        target==='coherent_scores'?!row.original_issue_verified||row.distribution_status!=='JOINT_SCORE_COHERENCE_CHECKED':true)))
      .sort((a,b)=>(time(a.game.kickoff)??Infinity)-(time(b.game.kickoff)??Infinity)||a.id.localeCompare(b.id));
  }
  function summarize(rows) {
    return {games:rows.length,exact:rows.filter(row=>row.game.kickoff_exact).length,unresolved:rows.filter(row=>!row.game.kickoff_exact).length,
      issued:rows.filter(row=>row.original_issue_verified).length,complete:rows.filter(row=>row.original_issue_verified&&row.all_targets_available).length,
      targets:Object.fromEntries(targets.map(target=>[target,rows.filter(row=>row.targets[target]==='AUTHENTICATED_PRIVATE_OUTLOOK').length])),
      qualified_cover:0,close_horizon_games:rows.filter(row=>row.close_horizon_issues>0).length};
  }
  const cell=value=>'"'+String(value??'').replace(/^([=+@\t\r])/,'\'$1').replaceAll('"','""')+'"';
  function csv(rows) {
    const head=['official_game_id','away','home','kickoff','status','winner_status','margin_status','total_status','cover_status','information_cutoff_utc','computed_at_utc','issued_at_utc','horizon','original_issue_verified','interval_status','distribution_status','next_action'];
    const body=rows.map(row=>[row.id,row.game.away,row.game.home,row.game.kickoff_exact?row.game.kickoff:null,row.status,...targets.map(target=>row.targets[target]),row.targets.cover,row.information_cutoff_utc,row.computed_at_utc,row.issued_at_utc,row.horizon,row.original_issue_verified,row.interval_status,row.distribution_status,row.next_action]);
    return [head,...body].map(row=>row.map(cell).join(',')).join('\r\n');
  }
  const api={targets,labels,matchesEpoch,recordIndex,coverage,inventory,select,summarize,csv};
  if(typeof module!=='undefined'&&module.exports)module.exports=api;
  if(typeof window==='undefined')return;
  window.FBSForwardOutlooks=api;
  function init() {
    const report=window.FBS_FORWARD_OUTLOOKS_V050,G=window.FBSCompleteReview,$=id=>document.getElementById(id);
    if(!report||!G||!$('forward-outlook-rows'))return;
    const esc=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
    const date=value=>time(value)===null?'Clock not retained':new Intl.DateTimeFormat('en-US',{timeZone:'America/Los_Angeles',month:'short',day:'numeric',hour:'numeric',minute:'2-digit',timeZoneName:'short'}).format(new Date(value));
    const rows=inventory(G.currentFixtureSnapshot||G.games,report),all=summarize(rows),indexed=recordIndex(report);
    const stateText=state=>({'AUTHENTICATED_PRIVATE_OUTLOOK':'Issued · private values','EXACT_KICKOFF_UNRESOLVED':'Kickoff unresolved','CURRENT_OUTLOOK_NOT_RECORDED':'Outlook not recorded','SAVED_PRIVATE_OUTPUT_UNQUALIFIED_ISSUE':'Saved · issue unqualified','SAVED_MODEL_INTERVALS_CALIBRATION_UNPROVED':'Saved intervals · calibration unproved','JOINT_SCORE_COHERENCE_CHECKED':'Joint-score coherence checked','NO_QUALIFIED_EXACT_LINE_DISTRIBUTION':'No qualified exact-line output','TARGET_OUTPUT_NOT_RECORDED':'Target not recorded'}[state]||state.replaceAll('_',' ').toLowerCase());
    $('stat-forward-issued').textContent=all.issued.toLocaleString();
    if($('method-current-outlooks'))$('method-current-outlooks').textContent=all.issued.toLocaleString()+' authenticated shadow outlooks';
    if($('adaptive-lane-status'))$('adaptive-lane-status').textContent=all.issued.toLocaleString()+' original current-origin issues · no promotion';
    $('stat-forward-note').textContent='Current-origin outlooks · '+all.close_horizon_games+' qualified close-horizon games';
    $('forward-outlook-clock').textContent=`Original source ${report.source_observed_at}. The outlooks retain their own information, computation and issue clocks. This publication creates no forecast.`;
    $('forward-outlook-total').textContent=all.games.toLocaleString();$('forward-outlook-issued').textContent=all.issued.toLocaleString();$('forward-outlook-tbd').textContent=all.unresolved.toLocaleString();$('forward-outlook-close').textContent=all.close_horizon_games.toLocaleString();
    $('forward-outlook-qualification').textContent=report.qualification_note || 'Current-origin outlooks are distinct from future near-start revisions. Distribution coherence is not proof of empirical calibration or promoted forecasting skill.';
    function selected(){return select(rows,{scope:$('forward-scope').value,query:$('forward-search').value,status:$('forward-status').value,target:$('forward-target').value});}
    function render(){
      const visible=selected(),s=summarize(visible);
      $('forward-outlook-summary').textContent=`${s.games} fixtures shown · ${s.issued} authenticated current-origin outlooks · ${s.unresolved} unresolved kickoffs · ${s.close_horizon_games} qualified close-horizon games. Target counts use this same fixture population.`;
      $('forward-target-counts').innerHTML=targets.map(target=>`<span>${labels[target]} <b>${s.targets[target]} / ${s.games}</b></span>`).join('')+`<span>Exact-line cover <b>0 / ${s.games}</b></span>`;
      $('forward-outlook-rows').innerHTML=visible.map(row=>`<tr><td><button class="row-button" data-forward-game="${esc(row.id)}">${esc(row.game.away)} at ${esc(row.game.home)}</button><small>${row.game.kickoff_exact?esc(date(row.game.kickoff)):'Exact kickoff unresolved'} · ${esc(row.id)}</small></td>${targets.map(target=>`<td><span class="chip ${row.targets[target]==='AUTHENTICATED_PRIVATE_OUTLOOK'?'':'warning'}">${esc(stateText(row.targets[target]))}</span></td>`).join('')}<td>${row.original_issue_verified?'Current-origin outlook':'No qualified issue'}<small>${row.issued_at_utc?esc(date(row.issued_at_utc)):'Original issue not established'}</small>${row.lead_hours!==null?'<small>'+esc((row.lead_hours/24).toFixed(1))+' days before kickoff</small>':''}</td><td>${esc(stateText(row.interval_status))}<small>${esc(stateText(row.distribution_status))}</small></td><td>${esc(row.next_action)}<small>${esc(row.status)} · ${esc(stateText(row.targets.cover))}</small></td></tr>`).join('')||'<tr><td colspan="7">No fixtures match these filters. Clear the filters to inspect the complete remaining-game inventory.</td></tr>';
      $('forward-export').disabled=!visible.length;
      const url=new URL(location.href);for(const [key,id]of[['outlook_scope','forward-scope'],['outlook_status','forward-status'],['outlook_target','forward-target']])url.searchParams.set(key,$(id).value);if($('forward-search').value)url.searchParams.set('outlook_search',$('forward-search').value);else url.searchParams.delete('outlook_search');url.hash='forward-outlooks';$('forward-view-link').href=url.href;
    }
    const params=new URL(location.href).searchParams;
    for(const [key,id]of[['outlook_scope','forward-scope'],['outlook_status','forward-status'],['outlook_target','forward-target']])if([...$(id).options].some(option=>option.value===params.get(key)))$(id).value=params.get(key);
    $('forward-search').value=params.get('outlook_search')||'';
    for(const id of ['forward-scope','forward-status','forward-target','forward-search'])$(id).addEventListener(id==='forward-search'?'input':'change',render);
    $('forward-reset').addEventListener('click',()=>{$('forward-scope').value='all';$('forward-status').value='all';$('forward-target').value='all';$('forward-search').value='';render();});
    $('forward-outlook-rows').addEventListener('click',event=>{const button=event.target.closest('[data-forward-game]');if(button){const capture=$('capture-view');if(capture.value!=='latest'){capture.value='latest';capture.dispatchEvent(new Event('change',{bubbles:true}));}G.openGame(button.dataset.forwardGame);}});
    $('forward-export').addEventListener('click',()=>{const url=URL.createObjectURL(new Blob([csv(selected())],{type:'text/csv;charset=utf-8'})),a=document.createElement('a');a.href=url;a.download='fbs-current-outlook-status.csv';document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);});
    document.addEventListener('fbs:game-opened',event=>{
      const game=(G.currentFixtureSnapshot||G.games).find(game=>String(game.id)===String(event.detail.id)),box=$('dialog-current-outlook');if(!box||!game)return;
      const row=coverage(game,report,indexed);
      box.innerHTML=`<h3>Current owner outlook for this fixture</h3><p><strong>${row.original_issue_verified?'Authenticated current-origin outlook':esc(stateText(row.status))}</strong>. ${esc(row.next_action)}</p><div class="outlook-game-targets">${targets.map(target=>`<span>${labels[target]}<b>${esc(stateText(row.targets[target]))}</b></span>`).join('')}<span>Exact-line cover<b>No qualified output</b></span></div>${row.record?`<dl class="outlook-clocks"><dt>Current registered kickoff</dt><dd>${esc(row.record.kickoff)}</dd><dt>Information cutoff</dt><dd>${esc(row.information_cutoff_utc||'Not recorded')}</dd><dt>Computed</dt><dd>${esc(row.computed_at_utc||'Not recorded')}</dd><dt>Original issue</dt><dd>${esc(row.issued_at_utc||'Not recorded')}</dd><dt>Horizon</dt><dd>Current-origin outlook${row.lead_hours!==null?' · '+(row.lead_hours/24).toFixed(1)+' days before kickoff':''}</dd></dl><p>${esc(stateText(row.interval_status))}. ${esc(stateText(row.distribution_status))}. New candidate values remain private; the displayed legacy projections retain their original identity and clocks.</p>`:''}`;
    });
    render();
  }
  if(window.FBSCompleteReview)init();else document.addEventListener('DOMContentLoaded',init,{once:true});
})();
