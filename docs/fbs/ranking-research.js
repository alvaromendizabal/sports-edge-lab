'use strict';
(() => {
  const number = value => typeof value === 'number' && Number.isFinite(value);
  const clock = value => typeof value === 'string' && Number.isFinite(Date.parse(value)) ? Date.parse(value) : null;
  const escape = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const count = value => number(value) ? value.toLocaleString() : 'Not independently enumerated';
  function presentation(source) {
    const labels={AP:'AP Top 25',COACHES:'Coaches Poll',CFP:'CFP committee',ELO:'Elo',SRS:'SRS',SP:'SP+',FPI:'FPI'};
    const normalize = row => ({...row,source_label:labels[row.source_key]||row.source_label,
      source_kind:row.source_kind==='ORGANIZATION_POLL'?'poll':'rating',
      request_status:row.request_status==='CANONICAL_ORIGINAL_AND_STANDALONE_RECEIPT_VERIFIED'?'VERIFIED_CAPTURE':row.request_status,
      publication_clock_status:row.publication_clock_status==='EXACT_PUBLICATION_TIMESTAMP_ABSENT'?'Exact publication time absent':row.publication_clock_status,
      reason_text:row.source_kind==='ORGANIZATION_POLL'?'Historical edition availability not proved':'Exact team binding and original vintage not proved',
      coverage_note:row.source_kind==='ORGANIZATION_POLL'?'Returned editions; later acquisition is not an earlier publication clock.':'Returned source rows; exact game-team binding remains pending.'});
    const index=new Map(source.rows.map(row=>[row.season+':'+row.source_key,normalize(row)]));
    const rows=[2024,2025,2026].flatMap(season=>Object.keys(labels).map(key=>index.get(season+':'+key)||{
      season,source_key:key,source_label:labels[key],source_kind:['AP','COACHES','CFP'].includes(key)?'poll':'rating',
      request_status:'NOT_CAPTURED_THIS_RUN',records:null,editions:null,teams:null,source_observed_at:null,
      publication_clock_status:'No source capture for this season in this run',admitted_feature_values:0,evaluated_feature_values:0,
      reason_code:'SOURCE_SEASON_NOT_CAPTURED_THIS_RUN',reason_text:'No new source/season capture in this run',
      coverage_note:'This is a run-specific gap; it does not claim the provider lacks historical data.',
      next_action:'Recover an authorized historical as-of version and its original timing; do not substitute the 2026 capture.'}));
    return {rows,selection_history:source.rows.filter(row=>row.season<2024).map(normalize),request_count:source.ranking_request_count,
      feature_counts:{admitted:source.rows.reduce((n,row)=>n+row.admitted_feature_values,0),evaluated:source.feature_counts.evaluated,promoted:0},
      owner_summary:'The registered rolling-policy stage stopped at an input-identity contract before a new verified fit, prediction or evaluation. Nine source requests were preserved; the new source records are not yet materialized or admitted model features.',
      capture_summary:'Ranking-source observations: November 8, 22:13:10–22:13:14 UTC. Original publication times are absent.',
      feature_groups:[
        {label:'Outcome history and rolling policy',actual_evidence:'91,270 retained outputs from prior studies; no new V046 fits or predictions.',qualification_gap:'The redesigned nested rolling policy has not completed its registered pilot.',next_action:'Repair the blocked identity contract, reuse exact saved work and execute only the uncompleted registered question.'},
        {label:'AP, Coaches and CFP editions',actual_evidence:'Separate poll captures for 2022–2026 with edition and team counts.',qualification_gap:'Original publication clocks and historical source availability are unproved; 0 new features admitted.',next_action:'Apply exact team/edition and as-of gates; use actual acquisition time only for later eligible cutoffs.'},
        {label:'Elo, SRS, SP+ and FPI',actual_evidence:'Four 2026 source captures; historical source cells remain explicit.',qualification_gap:'Exact team binding, original vintage and feature materialization remain pending.',next_action:'Validate population and snapshot identity before a controlled rating-family ablation.'},
        {label:'Market levels, paths and interactions',actual_evidence:'Four retained provider views and original path studies, including negative findings.',qualification_gap:'Historical matrices, equivalent products, quote/source timing and qualified cover remain incomplete.',next_action:'Recover original responses and receipts; admit exact matched targets before evaluation.'},
        {label:'Availability, injuries and player roles',actual_evidence:'Dated availability evidence and the earlier negative timing-uncertified study remain separate.',qualification_gap:'Historical role, expected snaps, contribution and replacement quality are not established by report presence.',next_action:'Bind chronological player/team evidence and test qualified availability inputs on matched cohorts.'},
        {label:'Coaching, context and temporal encoding',actual_evidence:'Broad V4 proposals and source/time contracts; no new evaluated features in this cycle.',qualification_gap:'Football-specific identities, effective/known-at clocks and earlier-label transformations remain pending.',next_action:'Materialize only supported distinct definitions and register grouped ablations before outcomes are used.'}
      ]};
  }
  function rowsFor(data, season='all', kind='all') {
    return (data?.rows || []).filter(row => (season === 'all' || row.season === Number(season)) && (kind === 'all' || row.source_kind === kind));
  }
  function relation(sourceTime, referenceTime) {
    const source = clock(sourceTime), reference = clock(referenceTime);
    if (source === null || reference === null) return {code:'CLOCK_EVIDENCE_MISSING',label:'Clock comparison unavailable'};
    return source < reference ? {code:'CAPTURE_BEFORE_REFERENCE',label:'Captured before this clock'} : {code:'CAPTURE_AT_OR_AFTER_REFERENCE',label:'Captured at or after this clock'};
  }
  function gameStatus(game, projection, data) {
    const targets = Object.values(projection?.model || {}).filter(row => number(row.prediction));
    const computed = targets.map(row=>row.computed_at_utc).filter(value=>clock(value)!==null).sort((a,b)=>clock(a)-clock(b));
    const original = computed.length === targets.length && computed.length ? computed[0] : null;
    const cutoff = projection?.record?.cutoff || null;
    return rowsFor(data,String(game.season)).map(row => {
      let reason = 'NOT_INCLUDED_IN_SELECTED_SAVED_MODEL';
      if (game.new_fixture_epoch) reason = 'NEW_FIXTURE_EPOCH_REQUIRES_NEW_MODEL';
      else if (!game.kickoff_exact) reason = 'EXACT_KICKOFF_UNRESOLVED';
      else if (!projection?.available) reason = 'NO_SAVED_MODEL_FOR_THIS_GAME_AND_FAMILY';
      else if (row.request_status !== 'VERIFIED_CAPTURE') reason = row.reason_code || 'SOURCE_CAPTURE_NOT_VERIFIED';
      return {source_key:row.source_key,source_label:row.source_label,source_observed_at:row.source_observed_at,
        original_computed_at:original,registered_cutoff:cutoff,
        versus_computation:relation(row.source_observed_at,original),versus_cutoff:relation(row.source_observed_at,cutoff),
        reason_code:reason,included_in_selected_model:false,qualified_feature_values:0,
        publication_clock_status:row.publication_clock_status,next_action:row.next_action};
    });
  }
  function sourceSummary(rows) {
    const present = rows.filter(row=>row.request_status==='VERIFIED_CAPTURE');
    return {source_season_cells:rows.length,verified_source_season_cells:present.length,
      admitted_feature_values:rows.every(row=>number(row.admitted_feature_values))?rows.reduce((n,row)=>n+row.admitted_feature_values,0):null,
      evaluated_feature_values:rows.every(row=>number(row.evaluated_feature_values))?rows.reduce((n,row)=>n+row.evaluated_feature_values,0):null};
  }
  const csvCell = value => '"'+String(value??'').replace(/^([=+@\t\r])/,'\'$1').replaceAll('"','""')+'"';
  function csv(rows) {
    const fields=['season','source_label','source_kind','request_status','records','editions','teams','source_observed_at','publication_clock_status','admitted_feature_values','evaluated_feature_values','reason_code','next_action'];
    return [fields,...rows.map(row=>fields.map(key=>row[key]))].map(row=>row.map(csvCell).join(',')).join('\r\n');
  }
  const api={rowsFor,relation,gameStatus,sourceSummary,csv,presentation};
  if(typeof module!=='undefined'&&module.exports)module.exports=api;
  if(typeof window==='undefined')return;
  window.FBSRankingResearch=api;
  function init(){
    const source=window.FBS_RANKING_RESEARCH_V047,$=id=>document.getElementById(id),G=window.FBSCompleteReview;
    if(!source||!$('ranking-source-rows')||!G)return;
    const data=presentation(source), current=window.FBS_FORWARD_OUTLOOKS_V050, ranking=current?.ranking_research;
    if(ranking){
      data.owner_summary='The latest owner materialized '+count(ranking.materialized_snapshots)+' ranking snapshots with '+count(ranking.observed_feature_values)+' observed source cells. Ranking-model fits remain '+count(ranking.new_model_fits)+': all '+count(ranking.registered_case_count)+' registered case/horizon records retain an explicit earlier-training-support gap. These counts describe snapshots and cells, not novel feature definitions or measured gains.';
      data.feature_groups[0]={label:'Outcome history and rolling policy',actual_evidence:'The current owner completed 44 base fits and 1,422 target outputs; 4,932 retrospective-development outputs are counted separately. Prior 91,270 outputs are preserved.',qualification_gap:'Current-origin shadow outlooks have no observed outcomes here; later close-horizon updates and production promotion remain separate.',next_action:'Evaluate only after original outcomes become observable; refresh each later eligible horizon under its own source and issue clocks.'};
      data.feature_groups[1].actual_evidence='Separate original poll captures for 2022–2026; the current owner materialized dated ranking snapshots.';
      data.feature_groups[1].qualification_gap='Original publication clocks are absent. Earlier eligible training support remains insufficient for the registered ranking ablations.';
      data.feature_groups[2].actual_evidence='Four preserved 2026 rating captures; current snapshots retain exact source and team bindings.';
      data.feature_groups[2].qualification_gap='Historical source availability and eligible earlier training support remain unproved. No ranking-model fit or gain is established.';
      if($('ranking-current-materialization'))$('ranking-current-materialization').textContent=count(ranking.materialized_snapshots)+' materialized snapshots · '+count(ranking.observed_feature_values)+' observed source cells · '+count(ranking.new_model_fits)+' ranking-model fits · '+count(ranking.new_evaluated_ranking_gains)+' evaluated ranking gains. The source/season census below keeps its original capture clocks and definition-level qualification.';
    }
    function render(){
      const rows=rowsFor(data,$('ranking-season').value,$('ranking-kind').value),summary=sourceSummary(rows);
      $('ranking-status-summary').textContent=`${summary.source_season_cells} source / season cells · ${summary.verified_source_season_cells} captured · ${count(summary.admitted_feature_values)} admitted feature values · ${count(summary.evaluated_feature_values)} evaluated feature values`;
      $('ranking-source-rows').innerHTML=rows.map(row=>`<tr><td><strong>${escape(row.source_label)}</strong><small>${row.season} · ${row.source_kind==='poll'?'Poll editions':'Rating series'}</small></td><td><span class="chip">${row.request_status==='VERIFIED_CAPTURE'?'Capture verified':row.request_status==='NOT_CAPTURED_THIS_RUN'?'Not captured in this run':'Capture not verified'}</span><small>${escape(row.source_observed_at||'No new capture clock')}</small></td><td><b>${count(row.records)}</b> records<small>${count(row.editions)} editions · ${count(row.teams)} teams</small></td><td>${escape(row.publication_clock_status)}<small>${escape(row.coverage_note||'Source coverage does not establish original availability.')}</small></td><td><b>${count(row.admitted_feature_values)}</b> admitted<small>${count(row.evaluated_feature_values)} evaluated</small></td><td><span>${escape(row.reason_text||row.reason_code)}</span><small>${escape(row.next_action)}</small></td></tr>`).join('')||'<tr><td colspan="6">No source cells match this selection. Choose another season or source family.</td></tr>';
      $('ranking-download-csv').disabled=!rows.length;
    }
    $('ranking-season').addEventListener('change',render);$('ranking-kind').addEventListener('change',render);
    $('ranking-download-csv').addEventListener('click',()=>{
      const blob=new Blob([csv(rowsFor(data,$('ranking-season').value,$('ranking-kind').value))],{type:'text/csv;charset=utf-8'}),url=URL.createObjectURL(blob),a=document.createElement('a');
      a.href=url;a.download='fbs-ranking-source-coverage.csv';document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);
    });
    $('ranking-owner-status').textContent=data.owner_summary;
    $('ranking-capture-clock').textContent=data.capture_summary;
    $('ranking-stage-capture').textContent=count(data.request_count)+' verified source requests';
    $('ranking-stage-admitted').textContent=count(data.feature_counts.admitted)+' admitted definitions';
    $('ranking-stage-evaluated').textContent=count(data.feature_counts.evaluated)+' evaluated definitions';
    $('ranking-stage-promoted').textContent=count(data.feature_counts.promoted)+' promoted definitions';
    $('ranking-selection-history').innerHTML=data.selection_history.map(row=>`<tr><td>${row.season} · ${escape(row.source_label)}</td><td>${count(row.editions)}</td><td>${count(row.records)}</td><td>${count(row.teams)}</td><td>${escape(row.source_observed_at)}</td><td>Original publication time absent</td></tr>`).join('');
    $('source-recheck-summary').textContent=`Latest authenticated source check: ${source.capture.observed_at} (capture completed ${source.capture.completed_at}). All ${source.counts.fixtures.toLocaleString()} fixture, team, kickoff and result coordinates match the earlier snapshot: ${source.counts.current_season_completed} season finals, 96 unresolved kickoffs, no new or changed results. The original result clocks below and 683-game evaluation remain unchanged.`;
    const market=window.FBS_MARKET_STATUS_V050||window.FBS_MARKET_STATUS_V049||window.FBS_MARKET_STATUS_V047;
    if(market&&$('latest-market-census-summary'))$('latest-market-census-summary').textContent=`Latest source check ${market.source_observed_at}: ${market.target_rows} raw target observations across ${market.event_count} events; ${market.exact_display_bound_events} events / ${market.exact_display_bound_target_rows} targets have exact registered ordered-team and kickoff associations. ${market.source_available_t120_exact_identity_rows} exact targets meet T−120 and ${market.source_available_t60_exact_identity_rows} meet T−60. The ${market.raw_source_available_t120_rows} raw source-clock checks are a different denominator. Qualified cover: ${market.qualified_model_cover_rows}. No new probability scores or historical feature admission follow from this metadata check.`;
    $('ranking-excluded-summary').textContent=Object.entries(source.excluded_non_fbs_poll_rows).map(([name,n])=>`${name}: ${n.toLocaleString()}`).join(' · ')+'. These source records are excluded from the FBS poll census.';
    const groups=data.feature_groups||[];
    $('research-readiness-rows').innerHTML=groups.map(row=>`<tr><td><strong>${escape(row.label)}</strong></td><td>${escape(row.actual_evidence)}</td><td>${escape(row.qualification_gap)}</td><td>${escape(row.next_action)}</td></tr>`).join('');
    document.addEventListener('fbs:game-opened',event=>{
      const game=G.games.find(g=>g.id===event.detail.id),box=$('dialog-ranking-evidence');if(!game||!box)return;
      const projection=G.projection(game),rows=gameStatus(game,projection,data);
      box.innerHTML='<div class="diagnostic-heading"><div><p class="eyebrow">INPUT EVIDENCE / SELECTED GAME</p><h3>Ranking sources and this saved forecast</h3></div><a class="secondary" href="#ranking-research" data-ranking-overview>Open source inventory</a></div><p>These newer source captures were not inputs to the selected saved model. Earlier capture timing alone cannot qualify a poll edition, historical vintage or new fitted snapshot.</p><div class="table-wrap"><table><thead><tr><th>Source</th><th>Original capture</th><th>Against earliest saved output</th><th>Against registered cutoff</th><th>Input status</th></tr></thead><tbody>'+rows.map(row=>'<tr><td>'+escape(row.source_label)+'</td><td>'+escape(row.source_observed_at||'Not authenticated')+'</td><td>'+escape(row.versus_computation.label)+'<small>'+escape(row.original_computed_at||'Original output clock not proved')+'</small></td><td>'+escape(row.versus_cutoff.label)+'<small>'+escape(row.registered_cutoff||'No bound cutoff for this selection')+'</small></td><td><strong>Not included</strong><small class="reason-code">'+escape(row.reason_code)+'</small></td></tr>').join('')+'</tbody></table></div><p class="footnote">0 admitted new ranking features for this game. The table compares recorded clocks; it does not create a new forecast, evaluate an outcome or authenticate an issue.</p>';
      box.querySelector('[data-ranking-overview]').addEventListener('click',()=>{$('game-dialog').close();$('ranking-season').value=String(game.season);render();});
    });
    render();
  }
  // Deferred scripts run with readyState=interactive before later dependencies.
  if(window.FBSCompleteReview)init();else document.addEventListener('DOMContentLoaded',init,{once:true});
})();
