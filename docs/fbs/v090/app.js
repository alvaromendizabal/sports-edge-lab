'use strict';
/* Public saved-evidence presentation. No owner research, provider calls or model selection is executed here. */
(function (root) {
  const OBJECTIVES = [
    {id:'winner:log_loss',target:'winner',metric:'log_loss',label:'Winner · log loss',direction:'lower'},
    {id:'winner:brier',target:'winner',metric:'brier',label:'Winner · Brier score',direction:'lower'},
    {id:'winner:accuracy',target:'winner',metric:'accuracy',label:'Winner · accuracy',direction:'higher'},
    {id:'margin:mae',target:'margin',metric:'mae',label:'Margin · MAE',direction:'lower'},
    {id:'margin:rmse',target:'margin',metric:'rmse',label:'Margin · RMSE',direction:'lower'},
    {id:'margin:crps',target:'margin',metric:'crps',label:'Margin · CRPS',direction:'lower'},
    {id:'total:mae',target:'total',metric:'mae',label:'Total · MAE',direction:'lower'},
    {id:'total:rmse',target:'total',metric:'rmse',label:'Total · RMSE',direction:'lower'},
    {id:'total:crps',target:'total',metric:'crps',label:'Total · CRPS',direction:'lower'}
  ];
  const PROFILES=['50/50','40/60','30/70','20/80','10/90'];
  const YEARS=[2024,2025,2026];
  const PAGE_SIZE=25;
  function validateReport(d) {
    if(d.schema!=='fbs.public.saved-evidence.v090'||d.owner!=='FBS')throw Error('Unsupported FBS evidence schema.');
    if(d.selection.primary_profile!=='50/50'||d.selection.test_outcomes_used!==false||d.selection.season_training_weights_used!==false||d.selection.refits_for_sensitivity!==0||d.selection.base_predictions_changed_for_sensitivity!==false)throw Error('Selection safeguards are missing.');
    if(d.selection.test_untouched!==false||d.selection.prior_test_exposure_disclosed!==true)throw Error('Prior test-exposure disclosure is missing.');
    if(d.models.length!==d.execution.total_policy_count||new Set(d.models.map(m=>m.alias)).size!==d.models.length)throw Error('Candidate count or public identity mismatch.');
    const known=new Map(d.models.map(m=>[m.alias,m]));
    const denominators=new Map(d.cohorts.map(c=>[c.season,c.expected_n]));
    for(const m of d.models)for(const year of YEARS){const c=m.annual[String(year)];if(!c||c.expected_n!==denominators.get(year)||c.scored_n+c.missing_n!==c.expected_n)throw Error('Candidate denominator mismatch.');}
    if(d.selection.leaders.length!==45)throw Error('All 45 objective/profile leaders must remain visible.');
    for(const o of OBJECTIVES)for(const profile of PROFILES){
      const leaders=d.selection.leaders.filter(x=>x.target===o.target&&x.metric===o.metric&&x.profile===profile);
      if(leaders.length!==1||!known.has(leaders[0].alias))throw Error('Missing or duplicate validation leader.');
      const ranks=d.selection.ranks.filter(x=>x.target===o.target&&x.metric===o.metric&&x.profile===profile);
      if(!ranks.length||ranks.some(x=>!known.has(x.alias)))throw Error('Invalid validation rank evidence.');
      const first=ranks.find(x=>x.rank===1);if(!first||first.alias!==leaders[0].alias)throw Error('Leader and saved validation rank disagree.');
    }
    return true;
  }
  function rankedModels(d,objective,profile,family='all',mode='all',query=''){
    const o=OBJECTIVES.find(x=>x.id===objective);if(!o||!PROFILES.includes(profile))return [];
    const models=new Map(d.models.map(m=>[m.alias,m]));const q=query.trim().toLowerCase();
    return d.selection.ranks.filter(r=>r.target===o.target&&r.metric===o.metric&&r.profile===profile).map(r=>({...r,model:models.get(r.alias)})).filter(r=>r.model&&(family==='all'||r.model.family===family)&&(mode==='all'||r.model.input_group===mode)&&(!q||(r.model.alias+' '+r.model.family+' '+r.model.label).toLowerCase().includes(q))).sort((a,b)=>(a.rank??Infinity)-(b.rank??Infinity)||a.alias.localeCompare(b.alias));
  }
  function metricN(card,metric){return metric==='crps'?(card.metrics.crps_n??0):(card.metrics.n??card.scored_n);}
  function selectedLeader(d,target,metric,profile){return d.selection.leaders.find(x=>x.target===target&&x.metric===metric&&x.profile===profile)||null;}
  function filteredGames(all,season='2026',status='all',query=''){
    const q=query.trim().toLowerCase();return all.filter(g=>(season==='all'||g.season===Number(season))&&(status==='all'||(status==='completed'&&g.completed)||(status==='pending'&&!g.completed)||(status==='unresolved'&&!g.kickoff_utc))&&(!q||(g.home_team+' '+g.away_team+' '+g.alias).toLowerCase().includes(q)));
  }
  function csv(rows){return rows.map(row=>row.map(value=>{let v=value??'';if(typeof v==='string'&&/^[\t\r ]*[=+@-]/.test(v))v="'"+v;return '"'+String(v).replace(/"/g,'""')+'"';}).join(',')).join('\r\n')+'\r\n';}
  function modelExport(rows,metric,profile){
    const headers=['public_alias','model_family','target','input_group','calibration','validation_profile','saved_validation_rank','selection_score',...YEARS.flatMap(y=>[y+'_metric',y+'_expected_games',y+'_metric_scored_games',y+'_metric_missing_games']), 'evidence_class','test_previously_exposed','test_used_for_selection','production_promoted'];
    return [headers,...rows.map(r=>{const m=r.model;return [m.alias,m.family,m.target,m.input_group,m.calibration,profile,r.rank,r.selection_score,...YEARS.flatMap(y=>{const c=m.annual[String(y)];return[c.metrics[metric]??null,c.expected_n,metricN(c,metric),c.expected_n-metricN(c,metric)];}),m.evidence_class,true,false,false];})];
  }
  function gameExport(rows){return [['public_game_alias','season','away_team','home_team','kickoff_utc','completed','away_points','home_points','kickoff_state','forecast_publication'],...rows.map(g=>[g.alias,g.season,g.away_team,g.home_team,g.kickoff_utc,g.completed,g.away_points,g.home_points,g.kickoff_utc?'OBSERVED':'UNRESOLVED','NEW_UNISSUED_NUMERICAL_OUTPUTS_NOT_PUBLISHED'])];}
  root.FBS090={OBJECTIVES,PROFILES,YEARS,PAGE_SIZE,validateReport,rankedModels,metricN,selectedLeader,filteredGames,csv,modelExport,gameExport};
  if(typeof document==='undefined')return;
  const $=id=>document.getElementById(id);
  const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const num=v=>typeof v==='number'&&Number.isFinite(v)?v.toLocaleString('en-US'):'Not measured';
  const fmt=(v,metric)=>typeof v==='number'&&Number.isFinite(v)?metric==='accuracy'?(100*v).toFixed(3)+'%':v.toFixed(6):'Not available';
  const time=v=>v?new Intl.DateTimeFormat('en-US',{timeZone:'America/Los_Angeles',month:'short',day:'numeric',year:'numeric',hour:'numeric',minute:'2-digit',timeZoneName:'short'}).format(new Date(v)):'Kickoff unresolved';
  const spanSeconds=v=>typeof v==='number'?v<120?v.toFixed(1)+' seconds':(v/60).toFixed(2)+' minutes':'Not measured';
  function factRows(pairs){return pairs.map(([label,value])=>'<div><dt>'+esc(label)+'</dt><dd>'+esc(value)+'</dd></div>').join('');}
  function metricCell(m,year,metric){const c=m.annual[String(year)];return fmt(c.metrics[metric],metric)+'<small>'+num(metricN(c,metric))+' / '+num(c.expected_n)+' games'+(metricN(c,metric)<c.expected_n?' · metric unavailable for '+num(c.expected_n-metricN(c,metric)):'')+'</small>';}
  let data,inventory,modelPage=0,gamePage=0;
  function currentModelRows(){return rankedModels(data,$('objective').value,$('profile').value,$('family').value,$('input-mode').value,$('model-search').value);}
  function currentGames(){return filteredGames(inventory.games,$('game-season').value,$('game-status').value,$('game-search').value);}
  function renderLeaders(){
    const profile=$('profile').value;const models=new Map(data.models.map(m=>[m.alias,m]));let changed=0;
    $('leaders-body').innerHTML=OBJECTIVES.map(o=>{const l=selectedLeader(data,o.target,o.metric,profile),m=models.get(l.alias),primary=selectedLeader(data,o.target,o.metric,'50/50'),isChanged=primary.alias!==l.alias;if(isChanged)changed++;
      return '<tr data-objective="'+o.id+'" data-alias="'+esc(m.alias)+'"><td><strong>'+esc(o.label)+'</strong><small>'+o.direction+' is better</small></td><td><strong>'+esc(m.alias)+' · '+esc(m.family)+'</strong><small>'+esc(m.input_group)+' · '+esc(m.calibration)+'</small>'+(isChanged?'<span class="changed">Different from the 50 / 50 leader</span>':'')+'</td><td>'+metricCell(m,2024,o.metric)+'</td><td>'+metricCell(m,2025,o.metric)+'</td><td><strong>'+fmt(l.value,o.metric)+'</strong><small>'+esc(profile)+' annual weighting</small></td><td class="test-column">'+metricCell(m,2026,o.metric)+'</td></tr>';}).join('');
    $('profile-note').textContent=profile==='50/50'?'Declared primary profile. All sensitivity comparisons use the same saved predictions.':changed+' of 9 objective leaders change from the declared 50 / 50 profile. No models are refitted.';
  }
  function renderModels(){
    const rows=currentModelRows(),o=OBJECTIVES.find(x=>x.id===$('objective').value);const pages=Math.max(1,Math.ceil(rows.length/PAGE_SIZE));modelPage=Math.max(0,Math.min(modelPage,pages-1));
    $('model-count').textContent=num(rows.length)+' policies for '+o.label.toLowerCase()+' · '+$('profile').value+' validation weights';
    $('models-body').innerHTML=rows.slice(modelPage*PAGE_SIZE,(modelPage+1)*PAGE_SIZE).map(r=>{const m=r.model;return '<tr data-policy="'+esc(m.alias)+'"'+(r.rank===1?' class="selected"':'')+'><td class="rank">'+(r.rank??'—')+'</td><td><strong>'+esc(m.alias)+' · '+esc(m.family)+'</strong><small>'+esc(m.calibration)+' · '+esc(m.release)+'</small></td><td>'+esc(m.input_group)+'<small>'+esc(m.study_group)+'</small></td><td>'+metricCell(m,2024,o.metric)+'</td><td>'+metricCell(m,2025,o.metric)+'</td><td><strong>'+fmt(r.selection_score,o.metric)+'</strong><small>Saved validation score</small></td><td class="test-column">'+metricCell(m,2026,o.metric)+'</td></tr>';}).join('')||'<tr><td colspan="7" class="empty">No saved policy matches these filters.</td></tr>';
    $('model-page').textContent='Page '+(modelPage+1)+' of '+pages+' · '+num(rows.length)+' policies';$('model-prev').disabled=modelPage===0;$('model-next').disabled=modelPage+1>=pages;
  }
  function renderGames(){
    const rows=currentGames(),pages=Math.max(1,Math.ceil(rows.length/PAGE_SIZE));gamePage=Math.max(0,Math.min(gamePage,pages-1));
    $('game-summary').textContent=num(rows.length)+' games match these filters · '+num(inventory.games.length)+' observed games retained across all three seasons';
    $('games-body').innerHTML=rows.slice(gamePage*PAGE_SIZE,(gamePage+1)*PAGE_SIZE).map(g=>'<tr data-game="'+esc(g.alias)+'"><td><strong>'+esc(g.away_team)+' at '+esc(g.home_team)+'</strong><small>'+esc(g.alias)+'</small></td><td>'+g.season+'</td><td title="'+esc(g.kickoff_utc||'No resolved kickoff')+'">'+esc(time(g.kickoff_utc))+'</td><td>'+(g.completed?'Completed':g.kickoff_utc?'Not confirmed complete':'Kickoff unresolved')+'</td><td>'+(g.completed&&g.home_points!==null?num(g.away_points)+' – '+num(g.home_points)+'<small>Away – home</small>':'Not graded')+'</td><td>'+(g.completed?'Historical replay; original issuance not established':'New unissued numerical outputs remain private')+'</td></tr>').join('')||'<tr><td colspan="6" class="empty">No observed game matches these filters.</td></tr>';
    $('game-page').textContent='Page '+(gamePage+1)+' of '+pages+' · '+num(rows.length)+' games';$('game-prev').disabled=gamePage===0;$('game-next').disabled=gamePage+1>=pages;
  }
  function download(name,rows){const blob=new Blob([csv(rows)],{type:'text/csv;charset=utf-8'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
  function renderStatic(){
    const e=data.execution,s=data.sources,c=data.compute,p=data.prepared;
    $('tranche-title').textContent=num(e.completed_jobs)+' / '+num(e.registered_jobs)+' new research jobs completed';
    $('tranche-summary').textContent=e.summary;$('snapshot-time').textContent=time(data.as_of);$('snapshot-time').title=data.as_of;
    $('stat-fits').textContent=num(e.new_model_fits);$('stat-calibrators').textContent=num(e.new_calibrator_fits)+' new calibrator fits';$('stat-policies').textContent=num(e.total_policy_count);$('stat-games').textContent=num(data.cohorts.reduce((n,r)=>n+r.expected_n,0));$('stat-failures').textContent=num(e.failed_fits);
    $('cohorts').innerHTML=data.cohorts.map(r=>'<article class="cohort'+(r.season===2026?' test':'')+'"><span class="year">'+r.season+' · '+(r.season===2026?'EXPOSED TEST':'VALIDATION')+'</span><strong>'+num(r.expected_n)+' games</strong><p>Full completed-game population</p></article>').join('');
    $('objective').innerHTML=OBJECTIVES.map(o=>'<option value="'+o.id+'">'+o.label+'</option>').join('');
    for(const value of [...new Set(data.models.map(m=>m.family))].sort())$('family').insertAdjacentHTML('beforeend','<option value="'+esc(value)+'">'+esc(value)+'</option>');
    for(const value of [...new Set(data.models.map(m=>m.input_group))].sort())$('input-mode').insertAdjacentHTML('beforeend','<option value="'+esc(value)+'">'+esc(value)+'</option>');
    $('source-summary').innerHTML=[['Admitted bookmakers',s.books.length],['Qualified T120 model cells',s.qualified_t120_cells],['Declared T120 grid cells',s.t120_grid_cells]].map(([label,value])=>'<article class="source-stat"><strong>'+num(value)+'</strong><p>'+esc(label)+'</p></article>').join('');
    $('providers').innerHTML=s.providers.map(r=>'<article class="provider"><h3>'+esc(r.name)+'</h3><span class="state">'+esc(r.state)+'</span><p>'+esc(r.note)+'</p><a href="../v079/market-readiness.html">Dated earlier comparison evidence</a></article>').join('');
    $('binding-note').textContent=s.note;$('book-list').innerHTML=s.books.map(b=>'<span>'+esc(b)+'</span>').join('');
    $('findings').innerHTML=data.findings.map(x=>'<li>'+esc(x)+'</li>').join('');
    $('source-coverage-body').innerHTML=s.coverage.map(r=>'<tr><td>'+r.season+'</td><td>'+esc(r.target)+'</td><td>'+esc(r.section)+'</td><td>'+num(r.rows_with_any_admitted_source)+'</td><td>'+num(r.all_sources_absent_rows)+'</td><td>'+num(r.rows)+'</td></tr>').join('');
    $('upcoming-note').textContent=inventory.qualification;
    $('execution-facts').innerHTML=factRows([['New base fits',num(e.new_model_fits)],['New calibrators',num(e.new_calibrator_fits)],['New scored prediction rows',num(e.new_scored_prediction_rows)],['New forecast rows, including ungraded',num(e.new_forecast_rows)],['Prior market jobs preserved',num(e.prior_market_jobs_preserved)],['Prior core jobs preserved',num(e.prior_core_jobs_preserved)],['Operationally failed executions',num(e.operational_failures)],['Observed child exit',String(e.child_exit_code)],['Scientific program status','Partial, resumable']]);
    $('execution-note').textContent=e.note;
    $('prepared-summary').textContent=p.summary;$('prepared-facts').innerHTML=factRows([['Owner execution','Not launched by this preparation'],['Registered scientific jobs',num(p.registered_scientific_jobs)],['Registered fixed-blend recipes',num(p.registered_fixed_blend_recipes)],['New scientific results claimed', '0'],['Default cost guard','USD 200'],['Selection default','2024 : 2025 at 50 / 50'],['2026 selection or tuning','Prohibited']]);
    $('compute-facts').innerHTML=factRows([['Registered model-stage wall time',spanSeconds(c.model_stage_seconds)],['Return finalization wall time',spanSeconds(c.return_finalization_seconds)],['End-to-end measured wall time',spanSeconds(c.end_to_end_seconds)],['Estimated full-host compute',typeof c.estimated_cost_usd==='number'?'USD '+c.estimated_cost_usd.toFixed(6):'Not measured'],['Actual cloud invoice','Not available'],['Scientific worker ceiling',num(c.worker_ceiling)],['Measured fit callback CPU',typeof c.fit_callback_cpu_seconds==='number'?c.fit_callback_cpu_seconds.toFixed(3)+' seconds':'Not attached'],['Sustained CPU acceptance',c.cpu_acceptance]]);
    $('cpu-note').textContent=c.note;$('remaining').innerHTML=data.remaining.map(x=>'<li>'+esc(x)+'</li>').join('');
    $('provenance').innerHTML=factRows([['Report schema',data.schema],['Observed evidence time',data.as_of],['Owner return SHA-256',data.provenance.owner_return_sha256],...data.provenance.artifacts.map(a=>[a.label+' SHA-256',a.sha256]),['Publication status','Source review; deployment pending']]);
  }
  async function readJSON(path){const ids={'data/review.json':'fbs090-inline-review','data/games.json':'fbs090-inline-games'},node=document.getElementById(ids[path]);if(node)return JSON.parse(node.textContent);const r=await fetch(path,{cache:'no-store'});if(!r.ok)throw Error('Required public evidence asset is unavailable: '+path);return r.json();}
  function bindEmbeddedDownloads(){for(const [path,id] of Object.entries({'data/review.json':'fbs090-inline-review','data/games.json':'fbs090-inline-games'})){const node=document.getElementById(id);if(!node)continue;for(const a of document.querySelectorAll('a[href="'+path+'"]'))a.addEventListener('click',event=>{event.preventDefault();const url=URL.createObjectURL(new Blob([node.textContent],{type:'application/json'}));const link=document.createElement('a');link.href=url;link.download=a.download||path.split('/').pop();link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);});}}
  async function init(){
    try{
      [data,inventory]=await Promise.all([readJSON('data/review.json'),readJSON('data/games.json')]);validateReport(data);
      if(inventory.schema!=='fbs.public.game-inventory.v090'||inventory.games.length!==inventory.observed_game_count)throw Error('Game-inventory integrity mismatch.');
      renderStatic();renderLeaders();renderModels();renderGames();bindEmbeddedDownloads();
      $('profile').addEventListener('change',()=>{modelPage=0;renderLeaders();renderModels();});
      for(const id of ['objective','family','input-mode'])$(id).addEventListener('change',()=>{modelPage=0;renderModels();});
      $('model-search').addEventListener('input',()=>{modelPage=0;renderModels();});
      $('model-prev').addEventListener('click',()=>{modelPage--;renderModels();});$('model-next').addEventListener('click',()=>{modelPage++;renderModels();});
      for(const id of ['game-season','game-status'])$(id).addEventListener('change',()=>{gamePage=0;renderGames();});
      $('game-search').addEventListener('input',()=>{gamePage=0;renderGames();});$('game-prev').addEventListener('click',()=>{gamePage--;renderGames();});$('game-next').addEventListener('click',()=>{gamePage++;renderGames();});
      $('download-models').addEventListener('click',()=>download('FBS_V090_'+$('objective').value.replace(':','_')+'_'+$('profile').value.replace('/','_')+'_COMPARISON.csv',modelExport(currentModelRows(),OBJECTIVES.find(o=>o.id===$('objective').value).metric,$('profile').value)));
      $('download-games').addEventListener('click',()=>download('FBS_V090_OBSERVED_GAME_INVENTORY.csv',gameExport(currentGames())));
      document.documentElement.dataset.ready='true';
    }catch(e){$('load-error').hidden=false;$('load-error').textContent='This report could not verify all required evidence: '+e.message+' No stale replacement has been substituted.';document.documentElement.dataset.ready='error';}
  }
  init();
})(globalThis);
