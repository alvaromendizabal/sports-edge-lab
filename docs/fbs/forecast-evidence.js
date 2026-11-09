'use strict';
(() => {
  const finite = value => typeof value === 'number' && Number.isFinite(value);
  const value = (row, key) => finite(row?.[key]) ? row[key] : null;
  const targetColumns = {
    winner: [['accuracy','Accuracy ↑'],['log_loss','Log loss ↓'],['brier','Brier ↓'],['ece10','ECE ↓'],['roc_auc','ROC AUC ↑']],
    margin: [['mae','MAE ↓'],['rmse','RMSE ↓'],['bias','Bias'],['interval80_coverage','80% coverage'],['interval95_coverage','95% coverage'],['saved_same_outcome_crps','Saved CRPS ↓']],
    total: [['mae','MAE ↓'],['rmse','RMSE ↓'],['bias','Bias'],['interval80_coverage','80% coverage'],['interval95_coverage','95% coverage'],['saved_same_outcome_crps','Saved CRPS ↓']],
    cover: []
  };
  function selectRows(report, {scope='baseline', period='2026', target='winner', comparison='own'}={}) {
    const rows = (report?.scopes?.[scope]?.rows || []).filter(row => row.period === period && row.target === target);
    if (comparison !== 'matched') return rows.map(row => ({...row, comparison_status:'RECORDED_FAMILY_COHORT'}));
    return rows.filter(row => row.paired_control?.exact_match === true && Number.isInteger(row.paired_control.games) && row.paired_control.games > 0)
      .map(row => ({...row, games:row.paired_control.games, metrics:row.paired_control.model_metrics,
        control_metrics:row.paired_control.reference_metrics, uncertainty:row.paired_control.uncertainty, exact_game_ids_sha256:row.paired_control.exact_game_ids_sha256,
        comparison_status:'EXACT_MATCHED_CONTROL_COHORT'}));
  }
  function scoredGames(report, scope='baseline', period='2026') {
    const row = report?.scopes?.[scope]?.rows?.find(row => row.period === period && row.target === 'winner' && row.family === 'v038/fixed_equal_blend');
    return Number.isInteger(row?.games) ? row.games : null;
  }
  function periodMatch(windows, storedWindows, period) {
    if (period === 'all') return '2026';
    const selected = windows?.[period];
    if (!selected?.start_utc || !selected?.end_utc) return null;
    for (const [key, row] of Object.entries(storedWindows || {})) {
      if (row.start_utc === selected.start_utc && row.end_utc === selected.end_utc) return key;
    }
    return null;
  }
  function refreshQueue(games, upcoming, projection, localDate) {
    const within=game=>upcoming?.start_utc&&upcoming?.end_utc?
      Date.parse(game.kickoff)>=Date.parse(upcoming.start_utc)&&Date.parse(game.kickoff)<Date.parse(upcoming.end_utc):
      typeof localDate==='function'&&upcoming?.start&&upcoming?.end_exclusive&&localDate(game.kickoff)>=upcoming.start&&localDate(game.kickoff)<upcoming.end_exclusive;
    return games.filter(game => game.season === 2026 && game.kickoff_exact && game.kickoff && within(game))
      .map(game => {
        const saved=projection(game), epoch=!!game.new_fixture_epoch;
        const reason=epoch?'NEW_FIXTURE_EPOCH_PREDICTION_PENDING':saved.available?'NEAR_TERM_MODEL_NOT_ISSUED':'BASELINE_OUTPUT_NOT_AVAILABLE';
        return {id:game.id,away:game.away,home:game.home,kickoff:game.kickoff,reason,
          priority:epoch?1:saved.available?3:2,baseline_saved:!!saved.available,
          issue_status:'NO_AUTHENTICATED_NEAR_TERM_ISSUE',
          next_action:epoch?'Register the resolved kickoff and produce a new forecast':saved.available?
            'Refresh approaching-game inputs and issue before its cutoff':'Recover or produce the missing eligible game forecast'};
      }).sort((a,b)=>a.priority-b.priority||Date.parse(a.kickoff)-Date.parse(b.kickoff)||String(a.id).localeCompare(String(b.id)));
  }
  const csvCell = v => '"'+String(v??'').replace(/^([=+@\t\r])/,'\'$1').replaceAll('"','""')+'"';
  function metricCsv(rows, columns) {
    const optional=['interval80_games','interval95_games','mean_interval80_width','mean_interval95_width','saved_same_outcome_crps_games','crps_missing_games'];
    const metricKeys=[...new Set([...columns,...optional])];
    const controlKeys=metricKeys.map(key=>'control_'+key);
    const header=['family','target','period','evidence_class','comparison_status','games','exact_game_ids_sha256','original_computed_at_utc',...metricKeys,...controlKeys,'calibration_bins','recorded_uncertainty'];
    return [header,...rows.map(row=>header.map(key=>metricKeys.includes(key)?value(row.metrics,key):controlKeys.includes(key)?value(row.control_metrics,key.slice(8)):key==='calibration_bins'?row.metrics?.calibration_bins?JSON.stringify(row.metrics.calibration_bins):null:key==='recorded_uncertainty'?row.uncertainty?JSON.stringify(row.uncertainty):null:row[key]))]
      .map(row=>row.map(csvCell).join(',')).join('\r\n');
  }
  const api={value,targetColumns,selectRows,scoredGames,periodMatch,refreshQueue,metricCsv};
  if(typeof module!=='undefined'&&module.exports)module.exports=api;
  if(typeof window==='undefined')return;
  window.FBSForecastEvidence=api;
  function init(){
    const report=window.FBS_EVALUATION_V049,G=window.FBSCompleteReview,M=window.FBSResearchMethod,$=id=>document.getElementById(id);
    if(!report||!G||!M||!$('forecast-evidence-rows'))return;
    const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
    const time=v=>v&&Number.isFinite(Date.parse(v))?new Intl.DateTimeFormat('en-US',{timeZone:'America/Los_Angeles',month:'short',day:'numeric',hour:'numeric',minute:'2-digit',timeZoneName:'short'}).format(new Date(v)):'Clock not supplied';
    const number=(n,key)=>n===null?'Not supplied':key==='accuracy'||key.includes('_coverage')?(n*100).toFixed(1)+'%':n.toFixed(4);
    const interval=values=>Array.isArray(values)&&values.length===2&&values.every(finite)?'['+values.map(n=>n.toFixed(4)).join(', ')+']':'Not supplied';
    function metricDetail(metrics,key){
      if(key==='saved_same_outcome_crps')return `n=${metrics?.saved_same_outcome_crps_games??'unavailable'} · ${metrics?.crps_missing_games??'unavailable'} without a saved score for this outcome`;
      if(key==='interval80_coverage'||key==='interval95_coverage'){
        const level=key.includes('80')?'80':'95';return `n=${metrics?.['interval'+level+'_games']??'unavailable'} · mean width ${number(value(metrics,'mean_interval'+level+'_width'),'width')}`;
      }
      return key==='roc_auc'&&metrics?.roc_auc_status!=='DEFINED'?(metrics?.roc_auc_status||'Status not supplied'):'';
    }
    function evidenceDetails(row){
      const u=row.uncertainty,parts=[];
      if(u)parts.push(u.status==='DESCRIPTIVE_PAIRED_WEEK_BOOTSTRAP'?`<p>Paired loss difference ${number(value(u,'mean_difference'),'difference')} · descriptive 95% ${interval(u.percentile95)} · multiplicity-adjusted ${interval(u.multiplicity_adjusted_interval)}. ${u.weeks} Pacific week blocks; ${u.registered_contrasts} registered contrasts. Lower candidate-minus-control loss is favorable; no promotion.</p>`:`<p>Uncertainty: ${esc(u.status)} · ${u.weeks??'unavailable'} distinct week blocks. A confidence interval is not invented for this small cohort.</p>`);
      const bins=row.metrics?.calibration_bins;
      if(Array.isArray(bins)&&bins.length)parts.push('<p>Original reliability bins:</p><div class="table-wrap"><table><thead><tr><th>Bin</th><th>Games</th><th>Mean probability</th><th>Observed rate</th></tr></thead><tbody>'+bins.map(bin=>`<tr><td>${bin.bin}</td><td>${bin.games}</td><td>${number(value(bin,'mean_probability'),'probability')}</td><td>${number(value(bin,'observed_rate'),'rate')}</td></tr>`).join('')+'</tbody></table></div>');
      return parts.length?'<details class="metric-evidence-detail"><summary>Recorded diagnostics</summary>'+parts.join('')+'</details>':'';
    }
    const label=family=>report.families?.[family]?.label||family.replaceAll('_',' ').replaceAll('/',' · ');
    $('forecast-evidence-clock').textContent=`Outcome source ${time(report.capture.source_observed_at)} · evaluation ${time(report.evaluated_at)}. Original forecasts and their computation clocks are unchanged.`;
    $('evidence-lane-foundation').textContent=`${scoredGames(report)??'No recorded'} current-season outcomes in the unchanged fixed-blend cohort. Retrospective evaluation; no new forecast issue.`;
    $('evidence-lane-adaptive').textContent='Current-origin adaptive research is reported in the outlook ledger above. These older numerical evaluation banks remain separate; a new issue does not create an observed forward performance result.';
    $('evidence-lane-market').textContent='Four separate source references remain available. Quote association alone does not establish an equivalent, contemporaneous probability benchmark.';
    $('evidence-lane-residual').textContent='Market-residual comparison awaits exact quote, contract, horizon and state qualification. No residual score or probability is substituted.';
    function render(){
      const query={scope:$('evidence-scope').value,period:$('evidence-period').value,target:$('evidence-target').value,comparison:$('evidence-comparison').value};
      const rows=selectRows(report,query),cols=targetColumns[query.target],matched=query.comparison==='matched';
      const outside=query.scope!=='baseline'&&(['2024','2025','previous_week'].includes(query.period)||query.scope==='four_epoch'&&query.period==='current_week');
      const emptyReason=query.target==='cover'?'NO_COMPARABLE_LINE':outside?'OUTSIDE_REGISTERED_STUDY_SCOPE':query.scope==='four_epoch'?'GAME_NOT_YET_PLAYED':matched?'NO_AUTHENTICATED_MATCHED_CONTROL_COHORT':'NO_RECORDED_EVALUATION';
      $('forecast-evidence-head').innerHTML='<tr><th>Model / evidence</th><th>Games</th>'+cols.map(([,title])=>'<th>'+title+'</th>').join('')+'<th>Recorded cohort</th></tr>';
      $('forecast-evidence-rows').innerHTML=rows.map(row=>{
        const values=cols.map(([key])=>'<td>'+number(value(row.metrics,key),key)+'<small>'+esc(metricDetail(row.metrics,key))+'</small>'+(matched?'<small>Control '+number(value(row.control_metrics,key),key)+'</small><small>'+esc(metricDetail(row.control_metrics,key))+'</small>':'')+'</td>').join('');
        const note=row.metric_qualifications?.join(' ')||'Recorded full-precision aggregate; display rounding only';
        return `<tr><td><strong>${esc(label(row.family))}</strong><small>${esc(row.evidence_label||'Exposed retrospective evaluation')}</small></td><td>${row.games}</td>${values}<td><code title="${esc(row.exact_game_ids_sha256)}">${esc(row.exact_game_ids_sha256?.slice(0,12)||'Exact cohort proof not supplied')}</code><small>${esc(note)}</small><small>Scored ${esc(time(row.original_computed_at_utc))}</small>${evidenceDetails(row)}</td></tr>`;
      }).join('')||`<tr><td colspan="${cols.length+3}"><strong>${emptyReason}</strong><small>${query.target==='cover'?'No exact-line cover output or qualified conditional distribution exists.':outside?'This date scope has no registered games in the selected changed-input study.':query.scope==='four_epoch'?'The 105-game outlook has no observed outcomes in this evaluation.':matched?'A different event or timing population is not substituted.':'This scope, date window and target have no recorded metrics.'} Unavailable performance is not zero.</small></td></tr>`;
      $('forecast-evidence-status').textContent=`${rows.length} recorded target rows · ${matched?'each row and its control use the exact same recorded games':'each family retains its own recorded cohort; different counts are not a matched comparison'} · ${report.scopes[query.scope]?.label||query.scope}. No current-season tuning or automatic promotion.`;
      $('forecast-evidence-export').disabled=!rows.length;
      $('forecast-evidence-note').textContent='The owner computed these metrics from unchanged saved forecasts. Historical source eligibility and original issuance remain separate gates. Interval and saved-CRPS denominators are shown independently; a saved CRPS is displayed only for its recorded outcome, and absent values remain unavailable. Recorded diagnostics retain original calibration bins and paired week uncertainty. No score is recomputed from displayed probabilities.';
    }
    for(const id of ['evidence-scope','evidence-period','evidence-target','evidence-comparison'])$(id).addEventListener('change',render);
    $('forecast-evidence-export').addEventListener('click',()=>{
      const rows=selectRows(report,{scope:$('evidence-scope').value,period:$('evidence-period').value,target:$('evidence-target').value,comparison:$('evidence-comparison').value});
      const data=metricCsv(rows,targetColumns[$('evidence-target').value].map(([key])=>key)),url=URL.createObjectURL(new Blob([data],{type:'text/csv;charset=utf-8'})),a=document.createElement('a');
      a.href=url;a.download='fbs-authenticated-evaluation.csv';document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);
    });
    const source=window.FBS_SOURCE_STATUS_V049||window.FBS_SOURCE_STATUS_V048;
    const windows=M.weekWindows(source.capture.official_current_season_observed_at),queue=refreshQueue(G.games,windows.upcoming,game=>G.projection(game,'fixed_equal_blend'),M.pacificDate);
    const pendingEpochs=queue.filter(row=>row.reason==='NEW_FIXTURE_EPOCH_PREDICTION_PENDING').length;
    $('refresh-priority-summary').textContent=`${queue.length} upcoming fixtures · ${pendingEpochs} new kickoff identities awaiting forecasts · ${queue.filter(row=>row.baseline_saved).length} with saved legacy outlooks · 0 authenticated near-term issues. Scope: ${windows.upcoming.label}.`;
    $('refresh-priority-rows').innerHTML=queue.map(row=>`<tr><td><b>${row.priority}</b></td><td><button class="row-button" data-refresh-game="${esc(row.id)}">${esc(row.away)} at ${esc(row.home)}</button><small>${esc(time(row.kickoff))} · ${esc(row.id)}</small></td><td><span class="chip">${row.baseline_saved?'Saved legacy outlook':'New output required'}</span><small>${esc(row.reason)}</small></td><td>${esc(row.next_action)}<small>Source, training, computation and original issue clocks remain separate</small></td></tr>`).join('');
    $('refresh-priority-rows').addEventListener('click',event=>{const button=event.target.closest('[data-refresh-game]');if(button)G.openGame(button.dataset.refreshGame);});
    $('forecast-evidence-issued').textContent='Original issued forecasts in these legacy evaluation banks: 0. New current-origin outlooks are recorded separately above. These exposed retrospective outcomes cannot independently confirm a policy designed after viewing them.';
    document.addEventListener('fbs:open-current-evaluation',event=>{
      const q=event.detail||{};if(q.scope)$('evidence-scope').value=q.scope;if(q.period)$('evidence-period').value=q.period;if(q.target)$('evidence-target').value=q.target;
      render();$('forecast-evidence').scrollIntoView({block:'start'});
    });
    render();
  }
  if(window.FBSCompleteReview)init();else document.addEventListener('DOMContentLoaded',init,{once:true});
})();
