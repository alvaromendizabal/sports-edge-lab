'use strict';
(() => {
  const $ = id => document.getElementById(id);
  const esc = x => String(x ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const n = x => Number(x).toLocaleString('en-US');
  const number = (x, digits=6) => x === null || x === undefined ? 'Not available' : Number(x).toFixed(digits);
  const percent = x => x === null || x === undefined ? 'Not available' : (Number(x)*100).toFixed(3)+'%';
  const providers = [['draftkings','DraftKings'],['kalshi','Kalshi'],['polymarket_global','Polymarket Global'],['polymarket_us','Polymarket US']];
  const modelSources={foundation:{field:'model',alias:'preserved_frozen_foundation',label:'Preserved foundation'},audit:{field:'audit_model',alias:'current_fixed_audit_baseline',label:'Current fixed audit baseline'},leaders:{field:'research_leader_model',alias:'selected_research_leaders_not_promoted',label:'Selected research leaders · not promoted'}};
  const selectedSource=()=>modelSources[$('game-model-source').value]||modelSources.foundation;
  const selectedRoleDescription=()=>{const r=data.research_leader_selection?.rule;return r?`${r.winner} winner, ${r.margin} margin and ${r.total} total by MAE`:'No current research-role selection admitted';};
  const objectiveNames={winner_probability:'Winner probability · log loss / Brier',winner_accuracy:'Winner accuracy',margin_mae:'Margin · average absolute error',total_mae:'Total · average absolute error',total_rmse:'Total · squared-error sensitivity'};
  const objectiveRoles=target=>['winner_probability','winner_accuracy','margin_mae','total_mae','total_rmse'].map(key=>[key,data?.research_objective_selection?.roles?.[key]]).filter(([,r])=>r?.target===target);
  const selectedObjective=()=>$('game-research-objective').value;
  const selectedModel=(g,target)=>selectedSource().field==='research_leader_model'&&selectedObjective()?g.research_objective_models?.[selectedObjective()]:g[selectedSource().field]?.[target];
  const reasonText=reason=>reason==='KICKOFF_UNRESOLVED'?'Kickoff is unresolved, so the pregame cutoff cannot be verified.':reason==='TARGET_NOT_FUTURE_BEFORE_T120_CUTOFF'?'At this source selection, this game is outside the admitted pregame window.':reason;
  const metricLabels = {log_loss:'Log loss',brier:'Brier',accuracy:'Accuracy',mae:'MAE',rmse:'RMSE',bias:'Bias',crps:'CRPS',interval80_coverage:'80% interval coverage'};
  const metrics = {winner:['log_loss','brier','accuracy'],margin:['mae','rmse','crps','bias','interval80_coverage'],total:['mae','rmse','crps','bias','interval80_coverage']};
  const formatMetric = (key,value) => ['accuracy','interval80_coverage'].includes(key) ? percent(value) : number(value);
  const label = p => data?.policies?.find(x=>x.id===p)?.label || p;
  let data, games=[], page=0;
  function tab(id) {
    if (!$('panel-'+id)) id='overview';
    document.querySelectorAll('[data-tab]').forEach(b=>{const on=b.dataset.tab===id;b.classList.toggle('active',on);b.setAttribute('aria-selected',String(on));b.tabIndex=on?0:-1;});
    document.querySelectorAll('[role="tabpanel"]').forEach(p=>p.hidden=p.id!=='panel-'+id);
    history.replaceState(null,'','#'+id);
  }
  const facts = (id, rows) => $(id).innerHTML=rows.map(([k,v])=>`<div><dt>${esc(k)}</dt><dd>${esc(v)}</dd></div>`).join('');
  function renderModels() {
    const cohort=$('model-cohort').value, target=$('model-target').value;
    const c=data.model_cohorts.find(c=>c.id===cohort);
    $('model-cohort-note').textContent=c?.description || '';
    const primary=$('model-objective').value||(target==='winner'?'log_loss':'mae');
    const rank=r=>r.metrics[primary]==null?Infinity:(primary==='accuracy'?-1:1)*r.metrics[primary];
    const rows=data.models.filter(r=>r.cohort===cohort&&r.target===target).slice().sort((a,b)=>rank(a)-rank(b)||a.family.localeCompare(b.family));
    $('model-cards').innerHTML=rows.length?rows.map(r=>`<article class="card model-card"><span class="badge">${esc(r.leader_for || 'Retained comparison')}</span><h3>${esc(r.label)}</h3><p>${esc(r.family)} · ${n(r.n)} games</p><dl class="facts">${Object.entries(r.metrics).filter(([k,v])=>metricLabels[k]&&v!==null).map(([k,v])=>`<div><dt>${esc(metricLabels[k])}</dt><dd>${formatMetric(k,v)}</dd></div>`).join('')}</dl>${r.conditional_accuracy_interval95?`<p class="subtle">Conditional 95% accuracy interval: ${percent(r.conditional_accuracy_interval95[0])}–${percent(r.conditional_accuracy_interval95[1])}. ${esc(r.uncertainty_limitation||r.uncertainty_note||"Descriptive interval; team/week dependence and selection are not validated.")}</p>`:""}<p class="subtle">${esc(r.evidence)}</p><p>${esc(r.features || '')}</p></article>`).join(''):'<article class="card"><h3>No admitted target leader in this cohort</h3><p>The saved evidence does not establish this comparison. Missing metrics stay missing.</p></article>';
  }
  function setupModelObjectives(){
    const target=$('model-target').value,old=$('model-objective').value;
    const choices=target==='winner'?['log_loss','brier','accuracy']:['mae','rmse'];
    $('model-objective').innerHTML=choices.map(k=>`<option value="${k}">${esc(metricLabels[k])} · ${k==='accuracy'?'higher':'lower'} is better</option>`).join('');
    if(choices.includes(old))$('model-objective').value=old;
    renderModels();
  }
  function setupScoreMetrics() {
    const target=$('score-target').value, old=$('score-metric').value;
    $('score-metric').innerHTML=metrics[target].map(m=>`<option value="${m}">${metricLabels[m]}</option>`).join('');
    if(metrics[target].includes(old))$('score-metric').value=old;
    renderScores();
  }
  function renderScores() {
    const season=Number($('score-season').value), target=$('score-target').value, m=$('score-metric').value;
    const rows=data.scores.filter(r=>r.season===season&&r.target===target).slice().sort((a,b)=>(m==='accuracy'?-1:1)*((a[m]??Infinity)-(b[m]??Infinity)));
    $('score-metric-name').textContent=metricLabels[m];
    $('score-cohort').textContent=rows.length?`${n(rows[0].n)} identical games · ${season} · ${rows.length} registered policies · later-fitted reconstruction`:'No saved scorecards for this selection.';
    $('score-body').innerHTML=rows.map(r=>`<tr data-policy="${esc(r.policy)}"><td>${esc(label(r.policy))}</td><td>${formatMetric(m,r[m])}</td><td>${n(r.n)}</td><td>Later-fitted reconstruction</td></tr>`).join('');
    const guides={log_loss:'Lower is better. Confident wrong probabilities receive a larger penalty.',brier:'Lower is better. This is mean squared probability error.',accuracy:'Higher is better at the chosen classification threshold; this does not measure probability calibration.',mae:'Lower is better. Average absolute point error.',rmse:'Lower is better. Larger point errors receive more weight.',crps:'Lower is better. This proper score evaluates the complete predictive distribution.',bias:'Signed average error; its direction matters. A small bias does not guarantee small individual errors.',interval80_coverage:'The nominal interval aims to cover 80% of outcomes. Width, sample size and chronological validity also matter.'};
    $('score-guide').textContent=guides[m];
  }
  function renderWeighted() {
    const rows=data.comparisons.filter(r=>r.target===$('weighted-target').value&&r.weight_policy===$('weighted-weight').value&&r.comparison_window===$('weighted-window').value);
    $('weighted-body').innerHTML=rows.map(r=>`<tr data-policy="${esc(r.policy)}"><td>${esc(label(r.policy))}</td><td>${percent(r.weighted_relative_skill)}</td><td>[${percent(r.adjusted95_interval?.[0])}, ${percent(r.adjusted95_interval?.[1])}]</td>${[2026,2025,2024].map(s=>`<td>${percent(r.season_details?.[s]?.relative_skill)}</td>`).join('')}</tr>`).join('');
    $('weighted-cohort').textContent=rows.length?'Games by season: '+[2026,2025,2024].map(s=>`${s}: ${n(rows[0].season_details[s].n)}`).join(' · ')+' · same model baseline':'No saved comparison in this window.';
    if(!rows.length){$('interval-chart').textContent='No saved interval.';return;}
    const intervals=rows.flatMap(r=>r.adjusted95_interval||[]), lo=Math.min(0,...intervals),hi=Math.max(0,...intervals), span=Math.max(hi-lo,.001);
    const x=v=>160+((v-lo)/span)*640;
    $('interval-chart').innerHTML=`<svg viewBox="0 0 850 ${rows.length*55+55}" role="img" aria-label="Saved weighted skill and adjusted uncertainty intervals"><line x1="${x(0)}" y1="5" x2="${x(0)}" y2="${rows.length*55}" stroke="#9cae9e" stroke-dasharray="4 4"/>${rows.map((r,i)=>{const y=30+i*55;return `<text x="4" y="${y+4}" font-size="12" fill="#526b5e">${esc(label(r.policy))}</text><line x1="${x(r.adjusted95_interval[0])}" y1="${y}" x2="${x(r.adjusted95_interval[1])}" y2="${y}" stroke="#38765b" stroke-width="3"/><circle cx="${x(r.weighted_relative_skill)}" cy="${y}" r="5" fill="#183c2e"/>`;}).join('')}<text x="160" y="${rows.length*55+30}" font-size="11" fill="#526b5e">${percent(lo)}</text><text x="750" y="${rows.length*55+30}" font-size="11" fill="#526b5e">${percent(hi)}</text></svg>`;
  }
  function coverageFlags(g, c) {
    const quote=Date.parse(c?.quote_time||''), observed=Date.parse(c?.observation_time||'');
    const kickoff=Date.parse(g.kickoff||''), source=Date.parse(data.source_as_of);
    const clocks=[quote,observed,kickoff,source].every(Number.isFinite)&&quote<=observed&&observed<=source&&quote<=kickoff-7200000&&observed<=kickoff-7200000;
    return {reference:c?.observed_reference===true,
      display:c?.value!==null&&c?.value!==undefined&&c?.display_eligible===true,
      identity:c?.identity_matched_reference===true,clocks,
      qualified:c?.status==='qualified'};
  }
  function renderProviders() {
    const population=$('provider-population').value,target=$('provider-target').value;
    const cohort=games.filter(g=>g.season===2026&&(population==='all'||(population==='final'?g.status==='final':g.status!=='final')));
    $('provider-cohort').textContent=`${n(cohort.length)} observed games · ${population==='final'?'played':population==='upcoming'?'pending':'played and pending'} · ${target}`;
    $('provider-body').innerHTML=providers.map(([id,name])=>{
      const p=data.providers.find(p=>p.id===id),flags=cohort.map(g=>coverageFlags(g,g.providers?.[id]?.[target]));
      const references=flags.filter(f=>f.reference).length,displayable=flags.filter(f=>f.display).length,qualified=flags.filter(f=>f.qualified).length;
      return `<tr data-provider="${id}"><td>${name}</td><td data-coverage="reference">${n(references)}</td><td data-coverage="display">${n(displayable)}</td><td data-coverage="qualified">${n(qualified)}</td><td data-coverage="denominator">${n(cohort.length)}</td><td>${qualified?'See saved eligible comparison':'Not available'}</td><td>${esc(p?.reason||'Exact current game, contract and time-qualified join missing.')}<br><button class="detail-button coverage-jump" data-provider-open="${id}">Inspect this provider</button></td></tr>`;
    }).join('');
    const timed=cohort.filter(g=>g.status==='pending').length,tbd=cohort.filter(g=>g.status==='tbd').length;
    $('provider-pending-detail').textContent=population==='final'?'The played cohort contains observed finals only.':`${n(timed)} timed pending games + ${n(tbd)} unresolved kickoffs are included. Reference presence, display eligibility and comparison qualification are separate counts.`;
  }
  const localDate=g=>g.kickoff?new Intl.DateTimeFormat('en-CA',{timeZone:'America/Los_Angeles',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date(g.kickoff)):'';
  const kickoff=g=>g.kickoff?new Intl.DateTimeFormat('en-US',{timeZone:'America/Los_Angeles',month:'short',day:'numeric',hour:'numeric',minute:'2-digit'}).format(new Date(g.kickoff)):'Kickoff unresolved';
  function filteredGames() {
    const season=Number($('game-season').value),status=$('game-status').value,coverage=$('game-coverage').value,search=$('game-search').value.trim().toLowerCase(),date=$('game-date').value;
    const provider=$('game-provider').value,state=$('game-provider-state').value,target=$('game-target').value;
    const ids=provider==='all'?providers.map(([id])=>id):[provider];
    const providerMatch=g=>state==='all'||ids.some(id=>{const f=coverageFlags(g,g.providers?.[id]?.[target]);return state==='reference'?f.reference:state==='display'?f.display:state==='qualified'?f.qualified:state==='missing'?!f.reference:state==='blocked'?f.reference&&!f.display:false;});
    const modelMatch=g=>coverage==='all'||(coverage==='issued'?g.issued_rows>0:coverage==='retained'?g.retained_issue_rows>0:coverage==='missing'?!g.issued_rows:coverage==='modelvalue'?selectedModel(g,target)?.value!==null&&selectedModel(g,target)?.value!==undefined:false);
    return games.filter(g=>g.season===season&&(status==='all'||(status==='unfinished'?g.status!=='final':g.status===status))&&modelMatch(g)&&providerMatch(g)&&(!search||[g.home,g.away,g.id].join(' ').toLowerCase().includes(search))&&(!date||localDate(g)===date));
  }
  function inspectProvider(id) {
    if(!providers.some(([p])=>p===id))return;
    $('game-season').value='2026';$('game-status').value=$('provider-population').value==='upcoming'?'unfinished':$('provider-population').value;
    $('game-target').value=$('provider-target').value;$('game-provider').value=id;$('game-provider-state').value='all';
    $('game-coverage').value='all';$('game-search').value='';$('game-date').value='';page=0;renderGames();tab('games');
  }
  function valueCell(c,target) {
    if(!c)return '<span class="muted">Not qualified</span>';
    const value=c.value===null||c.value===undefined?null:target==='winner'?(100*c.value).toFixed(1)+'%':number(c.value,1);
    return `${value!==null?`<strong>${c.value_label?esc(c.value_label)+' ':''}${esc(value)}</strong>`:'<span class="muted">Not available</span>'}<small>${esc(c.display_status||c.status||'Unqualified')}</small>`;
  }
  function setupGameObjectives(){
    const choices=objectiveRoles($('game-target').value),old=selectedObjective();
    $('game-research-objective').innerHTML=choices.map(([key,role])=>`<option value="${esc(key)}">${esc(objectiveNames[key]||key)} · ${esc(role.family)}</option>`).join('');
    if(choices.some(([key])=>key===old))$('game-research-objective').value=old;
    $('game-objective-control').hidden=selectedSource().field!=='research_leader_model'||!choices.length;
  }
  function renderGames() {
    setupGameObjectives();
    const rows=filteredGames(),target=$('game-target').value,source=selectedSource();page=Math.min(page,Math.max(0,Math.ceil(rows.length/25)-1));
    $('game-count').textContent=`${n(rows.length)} games match these filters`;
    $('game-model-heading').textContent=source.label;
    const role=data.research_objective_selection?.roles?.[selectedObjective()];
    const roleNote=role?`${objectiveNames[selectedObjective()]||selectedObjective()}: ${role.family}, selected on ${n(role.cohort_games)} earlier-scored games. Exact scored-state matches among admitted pending values: ${n(role.evaluation_state_matches)}; different states: ${n(role.evaluation_state_mismatches)}. `:'';
    $('game-model-source-note').textContent=source.field==='research_leader_model'?`${roleNote}Selected ${data.research_objective_selection?.selection_time||data.research_leader_selection?.selection_time||'Not admitted'}. The original committed issues retain their own clocks. Selected research leaders; not promoted; superiority unconfirmed. ${role?.caveat||data.research_leader_selection?.exact_state_caveat||''} No historical backfill.`:source.field==='audit_model'?`Fixed research-control selection: ${data.audit_baseline_selection?.selection_time||'Not admitted'}. Original issues retain their own clocks and are not reissued by publication. This source covers pending fixtures only; it is not a promoted champion or the current aggregate leader.`:'The preserved original foundation keeps its saved version and original issue clocks. It is separate from the current research leaderboard and the fixed audit baseline.';
    const seasonRows=games.filter(g=>g.season===Number($('game-season').value));
    $('game-pending-detail').textContent=`Season inventory: ${n(seasonRows.filter(g=>g.status==='final').length)} finals · ${n(seasonRows.filter(g=>g.status==='pending').length)} timed pending · ${n(seasonRows.filter(g=>g.status==='tbd').length)} unresolved kickoffs. Provider evidence filters apply to the selected target and provider; “Any provider” means at least one product matches.`;
    $('game-body').innerHTML=rows.slice(page*25,(page+1)*25).map(g=>{const model=selectedModel(g,target);return `<tr data-game="${esc(g.id)}"><td data-label="Game"><small>${esc(kickoff(g))} · ${esc(g.status)}</small><strong>${esc(g.away)} at ${esc(g.home)}</strong></td><td data-label="Result">${g.status==='final'?esc(g.away_score+' – '+g.home_score):'Pending'}</td><td data-label="${esc(source.label)}">${valueCell(model,target)}${model?.family?`<small>${esc(model.family)}</small>`:''}${model?.issue_time?`<small>Issued ${esc(model.issue_time)}</small>`:''}${model?.reason?`<small>${esc(reasonText(model.reason))}</small>`:''}${g.issued_rows?`<small>${n(g.issued_rows)} research-grid issue rows updated</small>`:''}${g.retained_issue_rows?`<small>${n(g.retained_issue_rows)} earlier committed research rows retained</small>`:''}</td>${providers.map(([id,name])=>`<td data-label="${name}">${valueCell(g.providers?.[id]?.[target],target)}</td>`).join('')}<td data-label="Details"><button class="detail-button" data-game-open="${esc(g.id)}">Inspect</button></td></tr>`;}).join('')||'<tr><td colspan="8">No games match these filters.</td></tr>';
    $('game-page').textContent=`Page ${rows.length?page+1:0} of ${Math.ceil(rows.length/25)}`;$('game-prev').disabled=page===0;$('game-next').disabled=(page+1)*25>=rows.length;
  }
  function openGame(id) {
    const g=games.find(g=>g.id===id), target=$('game-target').value;if(!g)return;
    $('game-dialog-title').textContent=g.away+' at '+g.home;
    const roles=objectiveRoles(target),research=roles.length?roles.map(([key])=>['objective:'+key,'Selected research leaders · '+objectiveNames[key]+' · not promoted']):[['research_leader_model','Selected research leaders · not promoted']];
    $('game-dialog-body').innerHTML=`<p>${esc(kickoff(g))} Pacific · ${esc(g.status)} · Game ${esc(g.id)}</p><p>Source observed: ${esc(g.source_observed_at||data.source_as_of)}</p><p>Updated research-grid issue rows: ${n(g.issued_rows||0)}. Earlier committed research rows retained: ${n(g.retained_issue_rows||0)}. ${esc(g.issue_note||'No invented retrospective delivery credit.')}</p><h3>${esc(target)} comparison</h3><div class="table-wrap"><table><thead><tr><th>Source</th><th>Value / state</th><th>Original evidence clocks</th><th>Evidence / missing reason</th></tr></thead><tbody>${[['model','Preserved frozen foundation'],['audit_model','Current fixed audit baseline'],...research,...providers].map(([id,name])=>{const isObjective=id.startsWith('objective:'),isModel=isObjective||['model','audit_model','research_leader_model'].includes(id),c=isObjective?g.research_objective_models?.[id.slice(10)]:isModel?g[id]?.[target]:g.providers?.[id]?.[target];const clocks=isModel?[['Issued',c?.issue_time],[isObjective||id==='research_leader_model'?'Selected research role':'Selected for audit display',c?.selection_time],['Information cutoff',c?.information_cutoff],['Fit completed',c?.fit_completed_at],['Prepared',c?.prepared_at],['Requested horizon cutoff',c?.requested_horizon_cutoff]]:[['Quote',c?.quote_time],['Observed',c?.observation_time]];return `<tr><td>${esc(name)}${c?.family?'<small>'+esc(c.family)+'</small>':''}</td><td>${valueCell(c,target)}</td><td>${clocks.filter(([label,value])=>value||!isModel).map(([label,value])=>'<small>'+label+': '+esc(value||'Not retained')+'</small>').join('')||'Not retained / not admitted'}</td><td>${esc(c?.reason||c?.evidence||'No admitted exact game, target and cutoff comparison in this snapshot.')}${c?.evaluation_state_matches===false?`<small>Different state from the ${n(c.evaluation_cohort_games)}-game evaluation; those metrics do not validate these weights.</small>`:''}</td></tr>`;}).join('')}</tbody></table></div>`;
    $('game-dialog').showModal();
  }
  function downloadGames() {
    const target=$('game-target').value,source=selectedSource();const headers=['game_id','season','away','home','kickoff_utc','status','away_score','home_score','new_issue_rows','retained_issue_rows','target','model_source','model_research_objective','model_evaluation_cohort_games','model_evaluation_state_matches','model_objective_caveat','model_family','model_value_label','model_value','model_status','model_admission_status','model_issue_time','model_selection_time','model_information_cutoff','model_fit_completed_at','model_prepared_at','model_requested_horizon_cutoff','model_missing_reason','model_evidence',...providers.flatMap(([id])=>[id+'_value',id+'_status',id+'_value_label',id+'_reference_present',id+'_rounded_value_displayable',id+'_identity_matched',id+'_clock_gate_passed',id+'_qualified_comparison',id+'_quote_time',id+'_observation_time',id+'_missing_reason'])];
    const csv=v=>'"'+String(v??'').replace(/"/g,'""')+'"';
    const rows=filteredGames().map(g=>{const model=selectedModel(g,target);return [g.id,g.season,g.away,g.home,g.kickoff,g.status,g.away_score,g.home_score,g.issued_rows||0,g.retained_issue_rows||0,target,source.alias,source.field==='research_leader_model'?selectedObjective():'',model?.evaluation_cohort_games??'',model?.evaluation_state_matches??'',source.field==='research_leader_model'?(data.research_objective_selection?.roles?.[selectedObjective()]?.caveat||''):'',model?.family||'',model?.value_label||'',model?.value??'',model?.status||'unavailable',model?.admission_status||model?.status||'unavailable',model?.issue_time||'',model?.selection_time||'',model?.information_cutoff||'',model?.fit_completed_at||'',model?.prepared_at||'',model?.requested_horizon_cutoff||'',model?.reason||(model?'':'No admitted value for this model source'),model?.evidence||'',...providers.flatMap(([id])=>{const c=g.providers?.[id]?.[target],f=coverageFlags(g,c);return [c?.value??'',c?.status||'not_qualified',c?.value_label||'',f.reference,f.display,f.identity,f.clocks,f.qualified,c?.quote_time||'',c?.observation_time||'',c?.reason||'No qualified reference'];})];});
    const blob=new Blob([[headers,...rows].map(r=>r.map(csv).join(',')).join('\r\n')+'\r\n'],{type:'text/csv;charset=utf-8'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='FBS_'+$('game-season').value+'_FILTERED_COMPARISON.csv';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
  }
  async function init() {
    const responses=await Promise.all(['data/review.json','data/games.json.gz'].map(async p=>{
      const r=await fetch(p);if(!r.ok)throw new Error('Evidence file unavailable: '+p);
      if(!p.endsWith('.gz'))return r.json();
      const bytes=new Uint8Array(await r.arrayBuffer());
      const body=bytes[0]===31&&bytes[1]===139?await new Response(new Blob([bytes]).stream().pipeThrough(new DecompressionStream('gzip'))).text():new TextDecoder().decode(bytes);
      return JSON.parse(body);
    }));data=responses[0];games=responses[1].games;
    $('stat-fits').textContent=n(data.counts.new_fits);if(data.fit_reuse_caveat){$('fit-reuse-note').hidden=false;$('fit-reuse-detail').textContent=data.fit_reuse_caveat;}$('stat-reused').textContent=n(data.counts.reused_states);$('stat-fixtures').textContent=n(data.census.fixtures);$('stat-issues').textContent=n(data.counts.new_issue_records);
    facts('owner-facts',[['Base fit tasks executed',n(data.counts.new_fits)],['New winner calibrators',n(data.counts.new_winner_calibrators)],['Games with updated issues',n(data.counts.new_issue_games)],['Failed model fits',n(data.counts.failed_fits)],['Promotion','None']]);
    if(data.forecast_coverage){const f=data.forecast_coverage;$('issue-coverage-note').textContent=f.description||`${n(f.eligible_games)} eligible future games: ${n(f.updated_issue_games)} with updated issues (${n(f.updated_issue_rows)} records) and ${n(f.reused_issue_games)} with retained prior issues (${n(f.reused_issue_rows)} records). Updated issues do not imply newly added games or newly fitted models.`;}
    if(data.audit_baseline_selection){const s=data.audit_baseline_selection;$('open-audit-baseline').hidden=false;$('audit-admission-note').textContent=`${n(s.admitted_cells)} admitted values across ${n(s.admitted_games)} pending games; ${n(s.missing_games)} pending games retain explicit gaps. Fixed selection time: ${s.selection_time}. Input snapshot: ${data.source_as_of}. Selecting this display adds no fits, inference or forecast issues.`;}else{$('game-model-source').querySelector('option[value="audit"]').disabled=true;}
    if(data.research_leader_selection){const s=data.research_leader_selection;$('open-research-leaders').hidden=false;$('leader-admission-note').textContent=`Selected research leaders: ${n(s.admitted_cells)} admitted values across ${n(s.admitted_games)} pending games; ${n(s.missing_games)} games retain explicit gaps. Actual selection time: ${s.selection_time}. ${selectedRoleDescription()}. Their apparent advantage in ${n(s.selection_cohort_games)} earlier-issued games is not confirmed superiority. No promotion, new inference or issue was created for this display. ${s.exact_state_caveat||''} ${s.uncertainty_limitation||''}`;}else{$('game-model-source').querySelector('option[value="leaders"]').disabled=true;}
    if(data.research_objective_selection){const s=data.research_objective_selection;$('research-objective-note').textContent=`Five distinct objectives expose ${n(s.admitted_cells)} retained values across ${n(s.admitted_games)} pending games. Probability quality and accuracy are separate winner objectives; total MAE and RMSE are separate error objectives. Selection uses ${n(s.selection_cohort_games)} earlier-issued games. A family choice does not transfer another exact state's historical score to these values.`;}
    if(data.actual_child_exit_code!==0){$('owner-status-note').hidden=false;$('owner-status-detail').textContent=data.owner_status_summary||data.execution_note;}
    facts('execution-facts',data.execution_facts);$('finalization-note').textContent=data.execution_note||'';$('normalized-rows').textContent=n(data.market.normalized_rows);$('market-recovery-detail').textContent=data.market.detail;$('bounded-source-progress').textContent=data.market.bounded_source_progress?.detail||'';$('prospective-repair').textContent=data.prospective_repair;$('cpu-detail').textContent=data.cpu_detail;$('feature-progress').textContent=data.feature_progress;
    $('archive-hash').textContent='Logical ZIP SHA-256: '+data.return.logical_archive_sha256;$('manifest-hash').textContent='Manifest SHA-256: '+data.return.manifest_sha256;
    $('model-cohort').innerHTML=data.model_cohorts.map(c=>`<option value="${esc(c.id)}">${esc(c.label)}</option>`).join('');
    $('feature-families').innerHTML=data.feature_families.map(f=>`<div><h3>${esc(f.title)}</h3><p>${esc(f.detail)}</p></div>`).join('');
    if(data.original_weight_recovery){$('original-recovery').hidden=false;$('original-recovery-status').textContent=data.original_weight_recovery.status;$('original-recovery-detail').textContent=data.original_weight_recovery.detail;}
    $('archive-comparison-body').innerHTML=data.archive_comparisons.map(r=>`<tr><td>${esc(r.cohort)}</td><td>${esc(r.label)}</td><td>${n(r.n)}</td><td>${percent(r.accuracy)}</td><td>${number(r.log_loss)}</td><td>${number(r.brier)}</td></tr>`).join('');
    $('archive-comparison-note').textContent=data.archive_comparison_note;
    $('weighted-limits').innerHTML=data.interval_limits.map(x=>`<li>${esc(x)}</li>`).join('');$('gate-body').innerHTML=data.gates.map(g=>`<tr><td>${esc(g.gate)}</td><td>${esc(g.status)}</td><td>${esc(g.detail)}</td></tr>`).join('');
    document.querySelectorAll('[data-tab]').forEach(b=>b.addEventListener('click',()=>tab(b.dataset.tab)));document.querySelectorAll('[data-jump]').forEach(b=>b.addEventListener('click',()=>tab(b.dataset.jump)));
    document.querySelector('.tabs').addEventListener('keydown',e=>{const tabs=[...document.querySelectorAll('[data-tab]')],i=tabs.indexOf(document.activeElement);if(i<0)return;const j=e.key==='Home'?0:e.key==='End'?tabs.length-1:e.key==='ArrowRight'?(i+1)%tabs.length:e.key==='ArrowLeft'?(i+tabs.length-1)%tabs.length:null;if(j!==null){e.preventDefault();tab(tabs[j].dataset.tab);tabs[j].focus();}});
    ['model-cohort','model-objective'].forEach(id=>$(id).addEventListener('change',renderModels));$('model-target').addEventListener('change',setupModelObjectives);$('score-target').addEventListener('change',setupScoreMetrics);['score-season','score-metric'].forEach(id=>$(id).addEventListener('change',renderScores));['weighted-target','weighted-weight','weighted-window'].forEach(id=>$(id).addEventListener('change',renderWeighted));['provider-population','provider-target'].forEach(id=>$(id).addEventListener('change',renderProviders));
    ['game-season','game-status','game-coverage','game-target','game-date','game-provider','game-provider-state','game-model-source','game-research-objective'].forEach(id=>$(id).addEventListener('change',()=>{page=0;renderGames();}));$('game-search').addEventListener('input',()=>{page=0;renderGames();});$('game-prev').addEventListener('click',()=>{page--;renderGames();});$('game-next').addEventListener('click',()=>{page++;renderGames();});$('game-body').addEventListener('click',e=>{const b=e.target.closest('[data-game-open]');if(b)openGame(b.dataset.gameOpen);});$('provider-body').addEventListener('click',e=>{const b=e.target.closest('[data-provider-open]');if(b)inspectProvider(b.dataset.providerOpen);});$('dialog-close').addEventListener('click',()=>$('game-dialog').close());$('download-games').addEventListener('click',downloadGames);
    $('open-audit-baseline').addEventListener('click',()=>{$('game-season').value='2026';$('game-status').value='unfinished';$('game-coverage').value='modelvalue';$('game-model-source').value='audit';$('game-target').value='winner';$('game-provider').value='all';$('game-provider-state').value='all';$('game-search').value='';$('game-date').value='';page=0;renderGames();tab('games');});
    $('open-research-leaders').addEventListener('click',()=>{$('game-season').value='2026';$('game-status').value='unfinished';$('game-coverage').value='modelvalue';$('game-model-source').value='leaders';$('game-target').value='winner';$('game-provider').value='all';$('game-provider-state').value='all';$('game-search').value='';$('game-date').value='';page=0;renderGames();tab('games');});
    const source=document.querySelector('meta[name="public-source-commit"]')?.content;if(source){$('source-link').href='https://github.com/alvaromendizabal/sports-edge-lab/tree/'+source+'/docs/fbs/v078';$('source-version').textContent='Public source '+source.slice(0,12)+' · evidence '+data.source_as_of;}
    setupModelObjectives();setupScoreMetrics();renderWeighted();renderProviders();renderGames();tab(location.hash.slice(1)||'overview');document.documentElement.dataset.ready='true';
  }
  init().catch(e=>{$('load-error').hidden=false;$('load-error').textContent=e.message;console.error(e);});
})();
