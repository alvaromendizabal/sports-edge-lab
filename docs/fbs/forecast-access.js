'use strict';
(() => {
  const horizons = [{id:'T1440',label:'Day ahead',minutes:1440},{id:'T120',label:'Two hours',minutes:120},{id:'T60',label:'One hour',minutes:60}];
  const clock = value => typeof value === 'string' && Number.isFinite(Date.parse(value)) ? Date.parse(value) : null;
  function deadlines(game, observedAt) {
    const kickoff=game.kickoff_exact===true?clock(game.kickoff):null, observed=clock(observedAt);
    return horizons.map(horizon=>{
      const due=kickoff===null?null:kickoff-horizon.minutes*60000;
      return {horizon:horizon.id,label:horizon.label,deadline_utc:due===null?null:new Date(due).toISOString(),
        status:due===null?'EXACT_KICKOFF_UNRESOLVED':observed===null?'OBSERVATION_CLOCK_UNAVAILABLE':
          due<=observed?'DEADLINE_REACHED_AT_OBSERVATION':'FUTURE_DEADLINE_AT_OBSERVATION',
        qualified_issue:false,issue_reason:'NO_INDIVIDUAL_QUALIFIED_HORIZON_ISSUE_IN_RETAINED_EXPORT'};
    });
  }
  function readiness(row) {
    const verified=row.original_issue_verified===true;
    return {winner:row.targets.winner==='AUTHENTICATED_PRIVATE_OUTLOOK',margin:row.targets.margin==='AUTHENTICATED_PRIVATE_OUTLOOK',
      total:row.targets.total==='AUTHENTICATED_PRIVATE_OUTLOOK',saved_intervals:verified&&row.interval_status==='SAVED_MODEL_INTERVALS_CALIBRATION_UNPROVED',
      coherent_scores:verified&&row.distribution_status==='JOINT_SCORE_COHERENCE_CHECKED',empirical_calibration:false,close_horizon:false,cover:false};
  }
  function summary(rows) {
    const result={games:rows.length,winner:0,margin:0,total:0,saved_intervals:0,coherent_scores:0,empirical_calibration:0,close_horizon:0,cover:0};
    for(const row of rows)for(const [key,present]of Object.entries(readiness(row)))result[key]+=Number(present);
    return result;
  }
  function gap(row,key) {return key==='all'?false:readiness(row)[key]!==true;}
  function executionReadout(record) {
    const observed=value=>typeof value==='number'&&Number.isFinite(value)&&value>=0;
    const count=value=>Number.isSafeInteger(value)&&value>=0?String(value):'Not recorded';
    const seconds=value=>observed(value)?value.toFixed(2)+' s':'Not recorded';
    const timing=record.timing||{},retained=record.retained_work||{};
    const stages=Object.values(record.scientific_stages||{}),unreached=stages.length>0&&stages.every(value=>value==='NOT_REACHED');
    return {heading:`${record.owner_release||'Owner'} ${unreached?'stopped before research':'execution evidence'}`,
      cards:[['Worker before packaging',seconds(timing.worker_before_packaging_seconds)],
        ['Launch observer overall',seconds(timing.launch_observer_seconds)],
        ['New base fits',count(record.new_base_fits)],
        ['New original issues',count(record.new_genuine_issues)],
        ['Retained fitted / calibrated records',count(retained.successful_total)],
        ['Retained original outlooks',count(retained.original_current_origin_issues)]],
      note:'Archived completed attempt. Timing scopes overlap and are not added together. Retained work is not new work from this attempt; this page does not monitor a live process.'};
  }
  const csvCell=value=>'"'+String(value??'').replace(/^([=+@\t\r])/,'\'$1').replaceAll('"','""')+'"';
  function csv(rows, observedAt) {
    const head=['official_game_id','away','home','kickoff_utc','source_observed_at','horizon','deadline_utc','deadline_status','qualified_horizon_issue','issue_reason'];
    return [head,...rows.flatMap(row=>deadlines(row.game,observedAt).map(d=>[row.id,row.game.away,row.game.home,row.game.kickoff_exact?row.game.kickoff:null,observedAt,d.horizon,d.deadline_utc,d.status,d.qualified_issue,d.issue_reason]))].map(row=>row.map(csvCell).join(',')).join('\r\n');
  }
  const api={horizons,deadlines,readiness,summary,gap,csv,executionReadout};
  if(typeof module!=='undefined'&&module.exports)module.exports=api;
  if(typeof window==='undefined')return;
  window.FBSForecastAccess=api;
  function init(){
    const G=window.FBSCompleteReview,F=window.FBSForwardOutlooks,report=window.FBS_FORWARD_OUTLOOKS_V050,$=id=>document.getElementById(id);
    if(!G||!F||!report||!$('forecast-access-summary'))return;
    const rows=F.inventory(G.currentFixtureSnapshot,report),counts=summary(rows),observedAt=report.source_observed_at;
    const attempt=window.FBS_EXECUTION_STATUS_V052||window.FBS_EXECUTION_STATUS_V051;
    if(attempt){$('execution-attempt-summary').textContent=attempt.public_summary;$('execution-attempt-clock').textContent='Stopped '+attempt.stopped_at+' · source remains '+attempt.current_source_observed_at+' · '+attempt.stop_reason+'.';}
    const esc=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
    if(attempt&&$('execution-work-tally')){
      const execution=executionReadout(attempt);
      $('execution-attempt-heading').textContent=execution.heading;
      $('execution-work-tally').innerHTML=execution.cards.map(([label,value])=>`<div role="listitem"><span>${esc(label)}</span><strong>${esc(value)}</strong></div>`).join('');
      $('execution-timing-note').textContent=execution.note;
    }
    const date=value=>value?new Intl.DateTimeFormat('en-US',{timeZone:'America/Los_Angeles',month:'short',day:'numeric',hour:'numeric',minute:'2-digit',timeZoneName:'short'}).format(new Date(value)):'Exact kickoff required';
    $('forecast-access-summary').textContent=`${counts.games} remaining fixtures: ${counts.winner} have authenticated private winner, margin and total outlooks; ${counts.games-counts.winner} need an exact kickoff. Historical displayed values and these later issues remain separate.`;
    const labels={winner:'Winner / probability',margin:'Home margin',total:'Total points',saved_intervals:'Saved intervals',coherent_scores:'Coherent score record',empirical_calibration:'Empirical calibration',close_horizon:'Later horizon issue',cover:'Exact-line output'};
    $('forecast-readiness').innerHTML=Object.entries(labels).map(([key,label])=>`<button class="readiness-item" data-readiness-gap="${key}"><span>${label}</span><strong>${counts[key]} <small>/ ${counts.games}</small></strong><em>${counts.games-counts[key]} ${key==='empirical_calibration'?'not established':key==='close_horizon'?'not separately issued':'gaps'} · inspect</em></button>`).join('');
    $('forecast-readiness').addEventListener('click',event=>{
      const button=event.target.closest('[data-readiness-gap]');if(!button)return;
      $('forward-scope').value='all';$('forward-status').value='all';$('forward-search').value='';$('forward-target').value=button.dataset.readinessGap;
      $('forward-target').dispatchEvent(new Event('change',{bubbles:true}));$('forward-outlooks').scrollIntoView({block:'start'});
    });
    function selected(){return F.select(rows,{scope:$('deadline-scope').value,query:$('deadline-search').value});}
    function render(){
      const visible=selected(),checks=visible.flatMap(row=>deadlines(row.game,observedAt)),unresolved=visible.filter(row=>!row.game.kickoff_exact).length;
      $('deadline-summary').textContent=`${visible.length} fixtures shown · ${checks.filter(d=>d.status==='FUTURE_DEADLINE_AT_OBSERVATION').length} future horizon boundaries · ${checks.filter(d=>d.status==='DEADLINE_REACHED_AT_OBSERVATION').length} boundaries already reached · ${unresolved} unresolved kickoffs. Comparison clock: ${observedAt}. This is a dated timing inventory, not a running scheduler or a source refresh.`;
      $('deadline-rows').innerHTML=visible.map(row=>`<tr><td><button class="row-button" data-deadline-game="${esc(row.id)}">${esc(row.game.away)} at ${esc(row.game.home)}</button><small>${esc(row.id)} · ${esc(row.status)}</small></td>${deadlines(row.game,observedAt).map(d=>`<td>${esc(date(d.deadline_utc))}<small>${d.status==='EXACT_KICKOFF_UNRESOLVED'?'Cannot assign a horizon':d.status==='FUTURE_DEADLINE_AT_OBSERVATION'?'Future at observation':'Reached at observation'}</small><small>No individually qualified horizon issue</small></td>`).join('')}</tr>`).join('')||'<tr><td colspan="4">No fixtures match. Clear the search or select all remaining fixtures.</td></tr>';
      $('deadline-export').disabled=!visible.length;
    }
    for(const id of ['deadline-scope','deadline-search'])$(id).addEventListener(id==='deadline-search'?'input':'change',render);
    $('deadline-rows').addEventListener('click',event=>{const button=event.target.closest('[data-deadline-game]');if(!button)return;const capture=$('capture-view');if(capture.value!=='latest'){capture.value='latest';capture.dispatchEvent(new Event('change',{bubbles:true}));}G.openGame(button.dataset.deadlineGame);});
    $('deadline-export').addEventListener('click',()=>{const url=URL.createObjectURL(new Blob([csv(selected(),observedAt)],{type:'text/csv;charset=utf-8'})),a=document.createElement('a');a.href=url;a.download='fbs-horizon-timing-inventory.csv';document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);});
    render();
  }
  if(window.FBSCompleteReview)init();else document.addEventListener('DOMContentLoaded',init,{once:true});
})();
