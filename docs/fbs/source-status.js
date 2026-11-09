'use strict';
(() => {
  const finite=value=>typeof value==='number'&&Number.isFinite(value);
  const exact=event=>typeof event.id==='string'&&event.identity_status==='EXACT_REGISTERED_NAMES_ORDERED_IDS_AND_KICKOFF';
  const labels={h2h:'Winner source',spreads:'Home-margin source',totals:'Total-points source'};
  function sourceRows(data,{provider='DraftKings',binding='all',query=''}={}) {
    const term=query.trim().toLowerCase();
    return (data?.events||[]).filter(event=>event.provider===provider&&(binding==='all'||exact(event)===(binding==='exact'))&&(!term||`${event.id||''} ${event.away} ${event.home}`.toLowerCase().includes(term)));
  }
  function sourceSummary(rows) {
    const output={events:rows.length,targets:0,exact_events:0,exact_targets:0,raw_t120:0,raw_t60:0,exact_t120:0,exact_t60:0,qualified_cover:0};
    for(const row of rows){
      const bound=exact(row);output.exact_events+=Number(bound);
      for(const target of Object.values(row.targets||{})){
        output.targets++;output.exact_targets+=Number(bound);
        output.raw_t120+=Number(target.source_available_by_t120===true);output.raw_t60+=Number(target.source_available_by_t60===true);
        output.exact_t120+=Number(bound&&target.source_available_by_t120===true);output.exact_t60+=Number(bound&&target.source_available_by_t60===true);
      }
      // Display association never creates a cover prediction or input admission.
    }
    return output;
  }
  function forGame(data,game){
    if(!game?.kickoff_exact||!game.kickoff)return [];
    return (data?.events||[]).filter(row=>exact(row)&&row.id===String(game.id)&&Date.parse(row.kickoff)===Date.parse(game.kickoff));
  }
  const csvCell=value=>'"'+String(value??'').replace(/^([=+@\t\r])/,'\'$1').replaceAll('"','""')+'"';
  function csv(rows){
    const columns=['provider','official_game_id','away','home','kickoff','identity_status','target','source_observed_at','quote_time','source_available_by_t120','source_available_by_t60','historical_model_input_admitted','qualified_cover'];
    const values=rows.flatMap(event=>Object.entries(event.targets||{}).map(([target,row])=>[event.provider,event.id,event.away,event.home,event.kickoff,event.identity_status,labels[target]||'Source target',row.observed_at,row.quote_time,row.source_available_by_t120,row.source_available_by_t60,false,false]));
    return [columns,...values].map(row=>row.map(csvCell).join(',')).join('\r\n');
  }
  function resultGap(observed,evaluated){
    if(!finite(observed)||!finite(evaluated)||observed<evaluated)return null;
    return observed-evaluated;
  }
  const api={sourceRows,sourceSummary,forGame,csv,resultGap};
  if(typeof module!=='undefined'&&module.exports)module.exports=api;
  if(typeof window==='undefined')return;
  window.FBSSourceStatus=api;
  function init(){
    const G=window.FBSCompleteReview,M=window.FBSResearchMethod,$=id=>document.getElementById(id);
    const raw=window.FBS_SOURCE_STATUS_V050||window.FBS_SOURCE_STATUS_V049||window.FBS_SOURCE_STATUS_V048,market=window.FBS_MARKET_STATUS_V050||window.FBS_MARKET_STATUS_V049||window.FBS_MARKET_STATUS_V048;
    const status=raw?{...raw,capture:{...raw.capture,observed_at:raw.capture.official_current_season_observed_at},counts:{...raw.counts,fixtures:raw.counts.identified_fixtures}}:null;
    if(!G||!M||!status||!market||!$('source-status-rows'))return;
    const esc=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
    const time=value=>value&&Number.isFinite(Date.parse(value))?new Intl.DateTimeFormat('en-US',{timeZone:'America/Los_Angeles',month:'short',day:'numeric',hour:'numeric',minute:'2-digit',second:'2-digit',timeZoneName:'short'}).format(new Date(value)):'Clock not retained';
    const metric=window.FBS_EVALUATION_V049,changed=window.FBS_OBSERVATION_STATUS_V046;
    const evaluatedGames=window.FBSForecastEvidence.scoredGames(metric),evaluatedClock=metric.capture.source_observed_at;
    $('source-clock-checked').textContent=time(status.capture.observed_at);
    $('source-clock-results').textContent=time(changed.original2026_source_observed_at);
    $('source-clock-evaluated').textContent=time(evaluatedClock);
    $('source-clock-metrics-computed').textContent='Latest retained aggregate computed '+time(metric.evaluated_at)+'.';
    $('source-clock-checked').title=status.capture.observed_at;
    $('source-clock-results').title=changed.original2026_source_observed_at;
    $('source-clock-evaluated').title=evaluatedClock;
    const finals=status.counts.current_season_completed,gap=resultGap(finals,evaluatedGames);
    $('source-clock-gap').textContent=`${finals} observed 2026 finals · ${evaluatedGames} in the latest evaluated baseline snapshot${gap===null?'':` · ${gap} later finals awaiting owner evaluation`}. Family and target gaps retain their own denominators. No metrics are recomputed from displayed values.`;
    $('source-recheck-summary').textContent=`Latest authenticated source check: ${status.capture.observed_at}; completed ${status.capture.completed_at}. All ${status.counts.fixtures.toLocaleString()} fixture, ordered-team, kickoff and result coordinates match the prior capture. No result coordinates changed in this source capture. New owner forecast work is accounted for separately; the original result and metric clocks remain separate.`;
    $('source-owner-summary').textContent=status.owner_evidence?.public_summary || 'The latest owner evidence is recorded separately from source capture and earlier metric cohorts. A partial execution is not live process state.';
    const windows=M.weekWindows(status.capture.observed_at),all=changed.rows;
    $('source-week-navigation').innerHTML=['previous','current','upcoming'].map(key=>{
      const games=all.filter(g=>g.season===2026&&M.periodFor(g,status.capture.observed_at)===key),finals=games.filter(g=>g.completed).length;
      const label={previous:'Previous week',current:'Dated current week',upcoming:'Upcoming week'}[key];
      return `<a class="source-week-link" href="?season=2026&amp;period=${key}#game-heading"><strong>${label}</strong><span>${windows[key].label}</span><b>${games.length} games · ${finals} observed finals</b><small>${key==='upcoming'?'Inspect saved targets, source associations and explicit gaps':'Open the full dated game inventory'}</small></a>`;
    }).join('');
    $('source-week-anchor').textContent='Pacific date windows are anchored to the authenticated source check, not today’s browser clock. Stored metric cohorts keep their own exact date windows.';
    $('source-status-clock').textContent=`DraftKings observed ${time(market.source_observed_at)}. This view contains association and timing metadata only. Older numeric reference values remain dated separately below.`;
    function render(){
      const provider=$('source-status-provider').value,rows=sourceRows(market,{provider,binding:$('source-status-binding').value,query:$('source-status-search').value}),s=sourceSummary(rows);
      $('source-status-summary').textContent=provider!=='DraftKings'?`${provider}: no new capture in this owner run. Earlier retained references and their gaps remain available below.`:`${s.events} events / ${s.targets} targets shown · ${s.exact_events} exact game associations / ${s.exact_targets} exact targets · ${s.exact_t120} exact targets by T−120 · ${s.exact_t60} by T−60 · 0 qualified cover outputs`;
      $('source-status-rows').innerHTML=rows.map(event=>{
        const bound=exact(event),targets=Object.entries(event.targets||{});
        return `<tr><td><strong>${esc(event.away)} at ${esc(event.home)}</strong><small>${esc(time(event.kickoff))}</small><small>${bound?'Official ID '+esc(event.id):'Official game identity unbound'}</small>${bound?`<button class="model-choice" data-source-game="${esc(event.id)}">Inspect game evidence</button>`:''}</td><td><span class="chip">${bound?'Exact association':'Unmatched source event'}</span><small>${bound?'Registered ordered teams and exact kickoff':'No unique admitted name, ordered-team and kickoff match'}</small></td><td>${targets.map(([key,row])=>`<div><b>${esc(labels[key]||'Source target')}</b><small>Quote ${esc(time(row.quote_time))}</small><small>Captured ${esc(time(row.observed_at))}</small></div>`).join('')}</td><td>${targets.map(([key,row])=>`<div>${esc(labels[key]||'Source target')}<small>T−120: ${row.source_available_by_t120?'source available':'not proved'} · T−60: ${row.source_available_by_t60?'source available':'not proved'}</small></div>`).join('')}</td><td>Not admitted to saved models<small>Fees, depth and liquidity unqualified</small><small>Cover probability unavailable</small></td></tr>`;
      }).join('')||'<tr><td colspan="5">No captured events match this selection. This is an explicit capture or filter gap, not zero-valued source data.</td></tr>';
      $('source-status-export').disabled=!rows.length;
    }
    for(const id of ['source-status-provider','source-status-binding','source-status-search'])$(id).addEventListener(id==='source-status-search'?'input':'change',render);
    $('source-status-export').addEventListener('click',()=>{
      const rows=sourceRows(market,{provider:$('source-status-provider').value,binding:$('source-status-binding').value,query:$('source-status-search').value}),blob=new Blob([csv(rows)],{type:'text/csv;charset=utf-8'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='fbs-source-association-metadata.csv';document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);
    });
    $('source-status-rows').addEventListener('click',event=>{const button=event.target.closest('[data-source-game]');if(button)G.openGame(button.dataset.sourceGame);});
    document.addEventListener('fbs:game-opened',event=>{
      const game=G.games.find(g=>g.id===event.detail.id),rows=forGame(market,game),box=$('dialog-newest-source');if(!box)return;
      const s=sourceSummary(rows);
      box.innerHTML=`<h3>Newest source association for this game</h3><p>${rows.length?`${s.exact_targets} target observations have an exact game and kickoff association; ${s.exact_t120} source-available by T−120 and ${s.exact_t60} by T−60.`:'No exact association in the newest DraftKings capture for this fixture epoch.'}</p><p>Source checked ${esc(time(market.source_observed_at))}. Association and cutoff timing do not add an input to an older saved model. No new numeric quote or qualified cover output is published.</p>`;
    });
    render();
  }
  if(window.FBSCompleteReview)init();else document.addEventListener('DOMContentLoaded',init,{once:true});
})();
