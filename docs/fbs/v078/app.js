'use strict';
(() => {
  const $ = id => document.getElementById(id);
  const esc = x => String(x ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const n = x => Number(x).toLocaleString('en-US');
  const number = (x, digits=6) => x === null || x === undefined ? 'Not available' : Number(x).toFixed(digits);
  const percent = x => x === null || x === undefined ? 'Not available' : (Number(x)*100).toFixed(3)+'%';
  const providers = [['draftkings','DraftKings'],['kalshi','Kalshi'],['polymarket_global','Polymarket Global'],['polymarket_us','Polymarket US']];
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
    const rows=data.models.filter(r=>r.cohort===cohort&&r.target===target);
    $('model-cards').innerHTML=rows.length?rows.map(r=>`<article class="card model-card"><span class="badge">${esc(r.leader_for || 'Retained comparison')}</span><h3>${esc(r.label)}</h3><p>${esc(r.family)} · ${n(r.n)} games</p><dl class="facts">${Object.entries(r.metrics).filter(([k,v])=>metricLabels[k]&&v!==null).map(([k,v])=>`<div><dt>${esc(metricLabels[k])}</dt><dd>${formatMetric(k,v)}</dd></div>`).join('')}</dl>${r.conditional_accuracy_interval95?`<p class="subtle">Conditional 95% accuracy interval: ${percent(r.conditional_accuracy_interval95[0])}–${percent(r.conditional_accuracy_interval95[1])}. ${esc(r.uncertainty_limitation||r.uncertainty_note||"Descriptive interval; team/week dependence and selection are not validated.")}</p>`:""}<p class="subtle">${esc(r.evidence)}</p><p>${esc(r.features || '')}</p></article>`).join(''):'<article class="card"><h3>No admitted target leader in this cohort</h3><p>The saved evidence does not establish this comparison. Missing metrics stay missing.</p></article>';
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
  function renderProviders() {
    const population=$('provider-population').value,target=$('provider-target').value;
    const cohort=games.filter(g=>g.season===2026&&(population==='all'||(population==='final'?g.status==='final':g.status!=='final')));
    $('provider-cohort').textContent=`${n(cohort.length)} observed games · ${population==='final'?'played':population==='upcoming'?'pending':'played and pending'} · ${target}`;
    $('provider-body').innerHTML=providers.map(([id,name])=>{
      const p=data.providers.find(p=>p.id===id),qualified=cohort.filter(g=>g.providers?.[id]?.[target]?.status==='qualified').length;
      const references=cohort.filter(g=>g.providers?.[id]?.[target]?.observed_reference===true).length;
      return `<tr data-provider="${id}"><td>${name}</td><td>${references?`${n(references)} archived references`:'Not proved for this cohort'}</td><td>${n(qualified)}</td><td>${n(cohort.length)}</td><td>${qualified?'See saved eligible comparison':'Not available'}</td><td>${esc(p?.reason||'Exact current game, contract and time-qualified join missing.')}</td></tr>`;
    }).join('');
  }
  const localDate=g=>g.kickoff?new Intl.DateTimeFormat('en-CA',{timeZone:'America/Los_Angeles',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date(g.kickoff)):'';
  const kickoff=g=>g.kickoff?new Intl.DateTimeFormat('en-US',{timeZone:'America/Los_Angeles',month:'short',day:'numeric',hour:'numeric',minute:'2-digit'}).format(new Date(g.kickoff)):'Kickoff unresolved';
  function filteredGames() {
    const season=Number($('game-season').value), status=$('game-status').value, coverage=$('game-coverage').value, search=$('game-search').value.trim().toLowerCase(),date=$('game-date').value;
    return games.filter(g=>g.season===season&&(status==='all'||g.status===status)&&(coverage==='all'||(coverage==='issued'?g.issued_rows>0:!g.issued_rows))&&(!search||[g.home,g.away,g.id].join(' ').toLowerCase().includes(search))&&(!date||localDate(g)===date));
  }
  function valueCell(c,target) {
    if(!c)return '<span class="muted">Not qualified</span>';
    const value=c.value===null||c.value===undefined?null:target==='winner'?(100*c.value).toFixed(1)+'%':number(c.value,1);
    return `${value!==null?`<strong>${c.value_label?esc(c.value_label)+' ':''}${esc(value)}</strong>`:'<span class="muted">Not available</span>'}<small>${esc(c.display_status||c.status||'Unqualified')}</small>`;
  }
  function renderGames() {
    const rows=filteredGames(),target=$('game-target').value;page=Math.min(page,Math.max(0,Math.ceil(rows.length/25)-1));
    $('game-count').textContent=`${n(rows.length)} games match these filters`;
    $('game-body').innerHTML=rows.slice(page*25,(page+1)*25).map(g=>`<tr data-game="${esc(g.id)}"><td data-label="Game"><small>${esc(kickoff(g))} · ${esc(g.status)}</small><strong>${esc(g.away)} at ${esc(g.home)}</strong></td><td data-label="Result">${g.status==='final'?esc(g.away_score+' – '+g.home_score):'Pending'}</td><td data-label="Model">${valueCell(g.model?.[target],target)}${g.issued_rows?`<small>${n(g.issued_rows)} new issue rows retained</small>`:''}</td>${providers.map(([id,name])=>`<td data-label="${name}">${valueCell(g.providers?.[id]?.[target],target)}</td>`).join('')}<td data-label="Details"><button class="detail-button" data-game-open="${esc(g.id)}">Inspect</button></td></tr>`).join('')||'<tr><td colspan="8">No games match these filters.</td></tr>';
    $('game-page').textContent=`Page ${rows.length?page+1:0} of ${Math.ceil(rows.length/25)}`;$('game-prev').disabled=page===0;$('game-next').disabled=(page+1)*25>=rows.length;
  }
  function openGame(id) {
    const g=games.find(g=>g.id===id), target=$('game-target').value;if(!g)return;
    $('game-dialog-title').textContent=g.away+' at '+g.home;
    $('game-dialog-body').innerHTML=`<p>${esc(kickoff(g))} Pacific · ${esc(g.status)} · Game ${esc(g.id)}</p><p>Source observed: ${esc(g.source_observed_at||data.source_as_of)}</p><p>New issue rows: ${n(g.issued_rows||0)}. ${esc(g.issue_note||'No invented retrospective delivery credit.')}</p><h3>${esc(target)} comparison</h3><div class="table-wrap"><table><thead><tr><th>Source</th><th>Value / state</th><th>Quote / observation or issue clocks</th><th>Evidence / missing reason</th></tr></thead><tbody>${[['model','Selected model'],...providers].map(([id,name])=>{const c=id==='model'?g.model?.[target]:g.providers?.[id]?.[target];return `<tr><td>${name}</td><td>${valueCell(c,target)}</td><td>${esc(c?.quote_time||c?.issue_time||'Not retained / not qualified')}${id!=='model'?'<small>Observed: '+esc(c?.observation_time||'Not retained')+'</small>':''}</td><td>${esc(c?.reason||c?.evidence||'No admitted exact game, target and cutoff comparison in this snapshot.')}</td></tr>`;}).join('')}</tbody></table></div>`;
    $('game-dialog').showModal();
  }
  function downloadGames() {
    const target=$('game-target').value;const headers=['game_id','season','away','home','kickoff_utc','status','away_score','home_score','new_issue_rows','target','model_value','model_status','model_issue_time',...providers.flatMap(([id])=>[id+'_value',id+'_status',id+'_value_label',id+'_quote_time',id+'_observation_time',id+'_missing_reason'])];
    const csv=v=>'"'+String(v??'').replace(/"/g,'""')+'"';
    const rows=filteredGames().map(g=>[g.id,g.season,g.away,g.home,g.kickoff,g.status,g.away_score,g.home_score,g.issued_rows||0,target,g.model?.[target]?.value??'',g.model?.[target]?.status||'not_qualified',g.model?.[target]?.issue_time||'',...providers.flatMap(([id])=>{const c=g.providers?.[id]?.[target];return [c?.value??'',c?.status||'not_qualified',c?.value_label||'',c?.quote_time||'',c?.observation_time||'',c?.reason||'No qualified reference'];})]);
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
    $('stat-fits').textContent=n(data.counts.new_fits);$('stat-reused').textContent=n(data.counts.reused_states);$('stat-fixtures').textContent=n(data.census.fixtures);$('stat-issues').textContent=n(data.counts.new_issue_records);
    facts('owner-facts',[['New fitted models',n(data.counts.new_fits)],['New winner calibrators',n(data.counts.new_winner_calibrators)],['Games with new issues',n(data.counts.new_issue_games)],['Failed model fits',n(data.counts.failed_fits)],['Promotion','None']]);
    facts('execution-facts',data.execution_facts);$('finalization-note').textContent=data.execution_note||'';$('normalized-rows').textContent=n(data.market.normalized_rows);$('market-recovery-detail').textContent=data.market.detail;$('prospective-repair').textContent=data.prospective_repair;$('cpu-detail').textContent=data.cpu_detail;$('feature-progress').textContent=data.feature_progress;
    $('archive-hash').textContent='Logical ZIP SHA-256: '+data.return.logical_archive_sha256;$('manifest-hash').textContent='Manifest SHA-256: '+data.return.manifest_sha256;
    $('model-cohort').innerHTML=data.model_cohorts.map(c=>`<option value="${esc(c.id)}">${esc(c.label)}</option>`).join('');
    $('feature-families').innerHTML=data.feature_families.map(f=>`<div><h3>${esc(f.title)}</h3><p>${esc(f.detail)}</p></div>`).join('');
    $('archive-comparison-body').innerHTML=data.archive_comparisons.map(r=>`<tr><td>${esc(r.cohort)}</td><td>${esc(r.label)}</td><td>${n(r.n)}</td><td>${percent(r.accuracy)}</td><td>${number(r.log_loss)}</td><td>${number(r.brier)}</td></tr>`).join('');
    $('archive-comparison-note').textContent=data.archive_comparison_note;
    $('weighted-limits').innerHTML=data.interval_limits.map(x=>`<li>${esc(x)}</li>`).join('');$('gate-body').innerHTML=data.gates.map(g=>`<tr><td>${esc(g.gate)}</td><td>${esc(g.status)}</td><td>${esc(g.detail)}</td></tr>`).join('');
    document.querySelectorAll('[data-tab]').forEach(b=>b.addEventListener('click',()=>tab(b.dataset.tab)));document.querySelectorAll('[data-jump]').forEach(b=>b.addEventListener('click',()=>tab(b.dataset.jump)));
    document.querySelector('.tabs').addEventListener('keydown',e=>{const tabs=[...document.querySelectorAll('[data-tab]')],i=tabs.indexOf(document.activeElement);if(i<0)return;const j=e.key==='Home'?0:e.key==='End'?tabs.length-1:e.key==='ArrowRight'?(i+1)%tabs.length:e.key==='ArrowLeft'?(i+tabs.length-1)%tabs.length:null;if(j!==null){e.preventDefault();tab(tabs[j].dataset.tab);tabs[j].focus();}});
    ['model-cohort','model-target'].forEach(id=>$(id).addEventListener('change',renderModels));$('score-target').addEventListener('change',setupScoreMetrics);['score-season','score-metric'].forEach(id=>$(id).addEventListener('change',renderScores));['weighted-target','weighted-weight','weighted-window'].forEach(id=>$(id).addEventListener('change',renderWeighted));['provider-population','provider-target'].forEach(id=>$(id).addEventListener('change',renderProviders));
    ['game-season','game-status','game-coverage','game-target','game-date'].forEach(id=>$(id).addEventListener('change',()=>{page=0;renderGames();}));$('game-search').addEventListener('input',()=>{page=0;renderGames();});$('game-prev').addEventListener('click',()=>{page--;renderGames();});$('game-next').addEventListener('click',()=>{page++;renderGames();});$('game-body').addEventListener('click',e=>{const b=e.target.closest('[data-game-open]');if(b)openGame(b.dataset.gameOpen);});$('dialog-close').addEventListener('click',()=>$('game-dialog').close());$('download-games').addEventListener('click',downloadGames);
    const source=document.querySelector('meta[name="public-source-commit"]')?.content;if(source){$('source-link').href='https://github.com/alvaromendizabal/sports-edge-lab/tree/'+source+'/docs/fbs/v078';$('source-version').textContent='Public source '+source.slice(0,12)+' · evidence '+data.source_as_of;}
    renderModels();setupScoreMetrics();renderWeighted();renderProviders();renderGames();tab(location.hash.slice(1)||'overview');document.documentElement.dataset.ready='true';
  }
  init().catch(e=>{$('load-error').hidden=false;$('load-error').textContent=e.message;console.error(e);});
})();
