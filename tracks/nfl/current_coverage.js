// Offline public derived outputs only. Selecting a clock never changes a model.
(()=>{
 'use strict';
 const D=JSON.parse(document.getElementById('nfl-latest-evidence').textContent);
 const P=JSON.parse(document.getElementById('nfl-point-evidence').textContent);
 const R=JSON.parse(document.getElementById('nfl-source-overlay').textContent);
 const X=JSON.parse(document.getElementById('nfl-reschedule-reference').textContent);
 const H=JSON.parse(document.getElementById('nfl-latest-pregame').textContent);
 const latestWinners=new Map(H.winner_rows.map(r=>[[r.game_id,r.provider].join('|'),{...r,latestHistory:true}]));
 const latestPoints=new Map(H.point_rows.map(r=>[[r.game_id,r.provider,r.target].join('|'),{...r,latestHistory:true}]));
 const Z=JSON.parse(document.getElementById('nfl-source-recovery').textContent);
 const recoveredWinners=new Map(Z.winner_rows.map(r=>[[r.game_id,r.provider].join('|'),r]));
 const recoveredPoints=new Map(Z.point_rows.map(r=>[[r.game_id,r.provider,r.target].join('|'),r]));
 const mappedWinners=new Map(X.winner_rows.map(r=>[[r.game_id,r.provider].join('|'),{...r,scheduleRecovery:true}]));
 const mappedPoints=new Map(X.point_rows.map(r=>[[r.game_id,r.provider,r.target].join('|'),{...r,scheduleRecovery:true}]));
 const sourceWinners=new Map(R.winner_rows.map(r=>[[r.game_id,r.provider].join('|'),r]));
 const sourcePoints=new Map(R.point_rows.map(r=>[[r.game_id,r.provider,r.target].join('|'),r]));
 const pointIndex=new Map(P.rows.map(r=>[[r.game_id,r.provider,r.target,r.horizon].join('|'),r]));
 const get=id=>document.getElementById(id);
 const esc=x=>String(x??'Not available').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const num=(x,n=1)=>x==null?'Not available':Number(x).toFixed(n);
 const pct=x=>x==null?'Not available':num(100*x,1)+'%';
 const signed=x=>x==null?'Not available':(x>0?'+':'')+num(x);
 const when=x=>x?new Intl.DateTimeFormat('en-US',{timeZone:'America/Los_Angeles',month:'short',day:'numeric',hour:'numeric',minute:'2-digit',timeZoneName:'short'}).format(new Date(x)):'Not recorded';
 const horizons={T2:'2 hours before kickoff',T1:'1 hour before kickoff',LATEST_PREGAME:'Latest before kickoff',LATEST_OBSERVED:'Latest observed upcoming'};
 const models=new Map(D.model_sets.map(x=>[x.id??x.model_id,x]));
 const modelLabel=id=>models.get(id)?.label??models.get(id)?.model_label??id;
 const modelId=f=>f.model_id??f.model_set_id;
 const I=JSON.parse(document.getElementById('nfl-primary-issue').textContent);
 const primaryIssues=new Map(I.cards.map(f=>[f.game_id,f]));
 const allGames=D.all_games.map(g=>{
  const issued=primaryIssues.get(g.game_id);
  if(g.completed||!issued)return g;
  return {...g,forecasts:g.forecasts.map(f=>modelId(f)===issued.model_id&&(!f.actual_issue_at||Date.parse(issued.actual_issue_at)>Date.parse(f.actual_issue_at))?issued:f)};
 });
 const providers=D.active_providers;
 const table=(caption,headers,rows)=>'<div class="scroll table-wrap" tabindex="0" role="region" aria-label="'+esc(caption)+'"><table><caption class="table-caption">'+esc(caption)+'</caption><thead><tr>'+headers.map(h=>'<th scope="col">'+esc(h)+'</th>').join('')+'</tr></thead><tbody>'+rows.map(row=>'<tr>'+row.map((v,i)=>(i?'<td>':'<th scope="row">')+v+(i?'</td>':'</th>')).join('')+'</tr>').join('')+'</tbody></table></div>';
 const observationOnly='OBSERVATION_TIME_ONLY_PROVIDER_QUOTE_CLOCK_UNKNOWN';
 const referenceTime=r=>r?.quote_at??(r?.quote_clock_kind===observationOnly?r.acquired_at:null);
 function newerReference(base,recovered,signal){
  if(!recovered)return base;
  if(recovered[signal]==null)return base?.[signal]!=null?base:{...recovered,sourceRecovery:true};
  if(base?.[signal]==null)return {...recovered,sourceRecovery:true};
  const a=referenceTime(base),b=referenceTime(recovered);
  return b&&(!a||Date.parse(b)>=Date.parse(a))?{...recovered,sourceRecovery:true}:base;
 }
 function clockText(r){
  if(r.latestHistory)return 'Pregame candle '+when(r.quote_at)+' · retrospectively acquired '+when(r.acquired_at)+' · no original possession or fill claim';
  if(r.scheduleRecovery)return 'Quote '+when(r.quote_at)+' · captured '+when(r.acquired_at)+' · recovered schedule mapping; not a fresh capture';
  if(r.quote_clock_kind===observationOnly)return 'Observed '+when(r.acquired_at)+' · provider quote time unavailable';
  return r.quote_at?'Quote '+when(r.quote_at)+(r.sourceRecovery?' · captured '+when(r.acquired_at):''):'Source clock unavailable';
 }
 function providerRow(g,p,h){
  const base=g.providers.find(x=>x.provider===p&&x.horizon===h)??{provider:p,horizon:h,derived_pick:null,availability_status:'UNAVAILABLE',unavailable_reason:h==='LATEST_PREGAME'?'Last-before-kickoff history has not yet been authenticated in this snapshot.':h==='LATEST_OBSERVED'?'No authenticated current winner observation in this snapshot.':'No authenticated equivalent winner record at this cutoff.'};
  if(h==='LATEST_PREGAME'&&g.completed)return latestWinners.get([g.game_id,p].join('|'))??{...base,unavailable_reason:'No authenticated latest-pregame reference is published for this game/provider. Earlier T1/T2 records remain separate.'};
  return h==='LATEST_OBSERVED'&&!g.completed?newerReference(newerReference(newerReference(base,sourceWinners.get([g.game_id,p].join('|')),'derived_pick'),mappedWinners.get([g.game_id,p].join('|')),'derived_pick'),recoveredWinners.get([g.game_id,p].join('|')),'derived_pick'):base;
 }
 function selectedGames(){
  const p=get('coverage-period').value;
  return allGames.filter(g=>p==='completed'?g.completed:p==='monday'?g.game_id==='2026_08_CHI_SEA':p==='all'?true:g.week===Number(p));
 }
 function pointRow(g,p,target,h){
  const base=pointIndex.get([g.game_id,p,target,h].join('|'))??null;
  if(h==='LATEST_PREGAME'&&g.completed)return latestPoints.get([g.game_id,p,target].join('|'))??base;
  return h==='LATEST_OBSERVED'&&!g.completed?newerReference(newerReference(newerReference(base,sourcePoints.get([g.game_id,p,target].join('|')),'line'),mappedPoints.get([g.game_id,p,target].join('|')),'line'),recoveredPoints.get([g.game_id,p,target].join('|')),'line'):base;
 }
 function pointCell(g,p,target,h){
  const r=pointRow(g,p,target,h);
  if(!r||r.line==null)return '<span class="provider-state">Not available</span><br><span class="fine">'+esc(r?.reason??(h==='LATEST_PREGAME'?'Latest-pregame source replay pending.':p==='Kalshi'&&!g.completed?'Current Kalshi capture pending.':'No authenticated equivalent reference.'))+'</span>';
  const probability=r.observed_probability==null?'Quoted line; no contract probability exported':pct(r.observed_probability)+' observed probability';
  const state=r.availability_status==='SAVED_LINE_REFERENCE_CLOCK_UNAVAILABLE'?'Saved line · source clock unavailable':r.contract_count+' captured contract'+(r.contract_count===1?'':'s')+' · '+clockText(r)+(r.sourceRecovery?' · recovered source checkpoint':'');
  return '<strong>'+esc(r.predicate)+'</strong><br>'+probability+'<br><span class="fine">'+esc(state)+'</span>';
 }
 function card(g,id,h){
  const actual=g.actual;
  const forecasts=id==='all'?g.forecasts:g.forecasts.filter(f=>modelId(f)===id);
  const selected=forecasts.length?forecasts:[{model_label:modelLabel(id),issue_class:'UNAVAILABLE',unavailable_reason:'This forecast series has no authenticated output for this game.'}];
  const market=providers.map(p=>providerRow(g,p,h));
  const result=actual?esc(g.away)+' '+num(actual.away_score,0)+'–'+num(actual.home_score,0)+' '+esc(g.home):'Upcoming';
  let html='<article class="card game-card latest-game" data-coverage-game="'+esc(g.game_id)+'" data-state="'+(g.completed?'final':'upcoming')+'"><div class="game-head"><div><span class="tag">Week '+g.week+' · '+(g.completed?'Final':'Scheduled')+'</span><h3>'+esc(g.away)+' at '+esc(g.home)+'</h3></div><div class="game-score">'+result+'</div></div><p class="game-clock">Kickoff '+esc(when(g.kickoff_utc))+'<br><span class="fine">'+esc(g.kickoff_utc)+'</span></p>';
  if(!actual){
   const hasProjection=forecasts.some(f=>f.pick||f.home_margin!=null||f.total!=null);
   html+='<p><span class="forecast-readiness">'+(hasProjection?'Early projection · betting assessment pending':'Forecast unavailable · betting assessment unavailable')+'</span></p>';
   html+='<p class="fine injury-status"><strong>Current injury/QB information:</strong> Not verified in this forecast.'+(g.game_id==='2026_09_JAX_BAL'?' <a href="#ravens-qb-context">Read the separate Ravens update.</a>':'')+'</p>';
   html+='<p class="fine wager-status"><strong>Personal wager activity:</strong> Not tracked in this dashboard.</p>';
  }
  html+=table('Selected model outputs · '+g.away+' at '+g.home,['Forecast series','Winner','Home margin','Total'],selected.map(f=>[esc(f.model_label??modelLabel(modelId(f)))+'<span class="game-origin">'+esc(f.issue_class==='RECONSTRUCTED_NOT_ORIGINAL_ISSUED'?'Retrospective reconstruction':f.issue_class==='SAVED_OR_RECONSTRUCTED_NOT_ORIGINAL_ISSUED'?'Saved vector · no original issue':f.issue_class==='EARLY_FORWARD_RESEARCH_ISSUE'?'Actual early research issue':f.issue_class==='T1_RESEARCH_ACTUAL_ISSUE'?'Actual 1-hour research issue':'Unavailable')+'</span>',f.pick?'<strong>'+esc(f.pick)+' '+pct(f.pick_probability)+'</strong>'+(actual?'<br>'+esc(actual.winner==='TIE'?'Tie':f.pick===actual.winner?'Correct winner':'Incorrect winner'):''):'Not available',signed(f.home_margin)+(actual&&f.home_margin!=null?'<br><span class="fine">Actual '+signed(actual.home_margin)+' · absolute error '+num(Math.abs(f.home_margin-actual.home_margin))+'</span>':''),num(f.total)+(actual&&f.total!=null?'<br><span class="fine">Actual '+num(actual.total)+' · absolute error '+num(Math.abs(f.total-actual.total))+'</span>':'')]));
  html+=table(horizons[h]+' · derived provider directions',['Provider','Winner direction','Evidence state'],market.map(p=>[esc(p.provider),p.derived_pick?'<strong>'+esc(p.derived_pick)+'</strong>'+(actual?'<br>'+esc(actual.winner==='TIE'?'Tie':p.correct?'Correct winner':'Incorrect winner'):''):'Not available',p.derived_pick?'<span class="provider-state covered">'+(p.latestHistory?'Retrospective pregame reference':p.scheduleRecovery?'Recovered schedule reference':p.sourceRecovery?'Recovered observation':p.quote_at?'Observed':'Saved reference')+'</span><br>'+esc(clockText(p)):'<span class="provider-state">Coverage gap</span><br>'+esc(p.unavailable_reason??p.availability_status)]));
  html+=table('Market spread and total references · '+g.away+' at '+g.home,['Provider','Home-margin condition','Total condition'],providers.map(p=>[esc(p),pointCell(g,p,'margin',h),pointCell(g,p,'total',h)]));
  html+='<p class="fine">Home margin means '+esc(g.home)+' points minus '+esc(g.away)+' points. A threshold and its probability are not a predicted final margin, mean total or model cover probability.</p>';
  if(g.game_id===X.event_mapping.game_id&&h==='LATEST_OBSERVED')html+='<p class="fine schedule-mapping-note"><strong>Separately verified event mapping:</strong> provider kickoff '+esc(X.event_mapping.provider_kickoff_utc)+'; canonical kickoff '+esc(X.event_mapping.canonical_kickoff_utc)+'; mapping verified '+esc(X.event_mapping.mapping_observed_at)+'. Schedule-revision first publication is unknown. No original forecast or historical metric changed.</p>';
  html+='<p class="fine clock-context">Model information time stays fixed when the market reference changes. '+(h==='T2'?'Same-cutoff comparison only for model rows explicitly labelled T2.':h==='T1'?'A T2 model versus this later T1 market is a supplemental comparison.':h==='LATEST_PREGAME'?'This is a later market benchmark, not a reissued historical prediction.':'This is an observed upcoming reference, not a final pregame quote.')+'</p>';
  html+='<details><summary>Forecast, quote and acquisition clocks</summary><ul>';
  for(const f of selected)html+='<li><strong>'+esc(f.model_label??modelLabel(modelId(f)))+'</strong><br>'+esc(f.unavailable_reason??f.origin??'Selected public output')+'<br>Model horizon: '+esc(f.horizon??'Unavailable')+'; issued: '+esc(f.actual_issue_at??'No original issue; do not backdate')+'; source/feature boundary: '+esc(f.source_asof??'Not separately exported')+'; fit completed: '+esc(f.fit_completed??'Not separately exported')+'.</li>';
  for(const p of market)html+='<li><strong>'+esc(p.provider)+' · '+esc(horizons[h])+'</strong><br>Observed quote: '+esc(p.quote_at??'Unavailable')+'; acquired: '+esc(p.acquired_at??'Unavailable')+'; quote age: '+(p.quote_age_seconds==null?'Unavailable':esc(num(p.quote_age_seconds,0))+' seconds')+'; maximum paired age: '+(p.max_age_seconds==null?'Unavailable':esc(num(p.max_age_seconds,0))+' seconds')+'; team-clock skew: '+(p.pair_clock_skew_seconds==null?'Unavailable':esc(num(p.pair_clock_skew_seconds,0))+' seconds')+'; clock type: '+esc(p.quote_clock_kind??'Not recorded')+'. '+esc(p.unavailable_reason??'Derived direction only; no executable price, fee or liquidity claim.')+'</li>';
  for(const p of providers)for(const target of ['margin','total']){const r=pointRow(g,p,target,h);if(r)html+='<li><strong>'+esc(p)+' · '+esc(target)+' reference</strong><br>'+esc(r.predicate??'No parsed predicate')+'; quote: '+esc(r.quote_at??'Not recorded')+'; acquired: '+esc(r.acquired_at??'Not recorded')+'; reference cutoff: '+esc(r.cutoff_at??'Not recorded')+'; quote age: '+esc(r.quote_age_seconds??'Not recorded')+' seconds; clock type: '+esc(r.quote_clock_kind??'Not recorded')+'. '+esc(r.reason??'')+'</li>';}
  html+='</ul></details></article>';
  return html;
 }
 function render(){
  const games=selectedGames(),id=get('coverage-model').value,h=get('coverage-horizon').value;
  const available=games.filter(g=>g.forecasts.some(f=>(id==='all'||modelId(f)===id)&&f.pick)).length;
  get('coverage-count').textContent=games.length+' games shown · '+games.filter(g=>g.completed).length+' completed · '+available+' with a selected model winner output. Games remain visible even when a stream or provider is unavailable.';
  get('coverage-provider-counts').innerHTML=providers.map(p=>{const n=games.filter(g=>providerRow(g,p,h).derived_pick).length;return '<article class="mini-stat"><span>'+esc(p)+'</span><strong>'+n+' / '+games.length+'</strong><span class="fine">winner directions · '+esc(horizons[h])+'</span></article>';}).join('');
  get('coverage-clock-note').textContent=h==='T2'?'T2 means two hours before kickoff. Use the last genuine observation at or before that cutoff; an exact-minute quote is not required. Quote age stays visible.':h==='T1'?'T1 means one hour before kickoff. It is a separate market reference. Earlier T2 model outputs retain their original information boundary.':h==='LATEST_PREGAME'?'Latest before kickoff is the last authenticated observation strictly before the game starts. It may be shown even when it is later than T2. Missing latest history is never replaced silently with a T2 quote. Monday Chicago–Seattle now has separately authenticated Kalshi winner, margin and total references; other latest-history gaps remain explicit.':'Latest observed upcoming shows a real observed market state for an unstarted game, when available. Reaching T2 is not a requirement for displaying it. An observation is not an executable bet.';
  get('coverage-point-counts').innerHTML=table('Provider coverage by prediction target',['Provider','Winner direction','Margin reference','Total reference'],providers.map(p=>[esc(p),games.filter(g=>providerRow(g,p,h).derived_pick).length+' / '+games.length,...['margin','total'].map(t=>{const rows=games.map(g=>pointRow(g,p,t,h)).filter(r=>r?.line!=null),saved=rows.filter(r=>r.availability_status==='SAVED_LINE_REFERENCE_CLOCK_UNAVAILABLE').length;return (rows.length-saved)+' / '+games.length+' dated references'+(saved?'<br><span class="fine">'+saved+' saved lines · clocks unavailable</span>':'');})]));
  get('coverage-games').innerHTML=games.map(g=>card(g,id,h)).join('');
  get('partial-source-status').textContent='Authenticated N036 source-only recovery adds 13 current reference cells through '+when(Z.as_of)+'. Combined Week 9 coverage: DraftKings 15/15, Kalshi 15/15, Polymarket 13/15 for winner, margin and total. This source run reached its registered public-request budget; it fitted no models and issued no forecasts. Polymarket TB–CHI and BUF–MIN remain unavailable. '+(h==='LATEST_OBSERVED'?'The latest supported current reference is shown; a missing new capture does not erase an older usable reference. Kalshi capture times are observation clocks where provider quote timestamps are unavailable.':'This recovery is not applied to the selected historical horizon.')+' Source recovery leaves model forecasts and historical metrics unchanged; the separate primary-issue addendum retains its own clocks. ';
 }
 get('coverage-period').innerHTML='<option value="9">Current week · Week 9 · 15 games</option><option value="completed">All completed games · 121 finals</option><option value="monday">Monday Nov 2 · CHI 34–17 SEA</option>'+[...new Set(allGames.map(g=>g.week))].sort((a,b)=>a-b).map(w=>'<option value="'+w+'">Week '+w+' · '+allGames.filter(g=>g.week===w).length+' games</option>').join('')+'<option value="all">Full season · 272 scheduled games</option>';
 get('coverage-model').innerHTML=D.model_sets.map(m=>'<option value="'+esc(m.id??m.model_id)+'">'+esc(m.label??m.model_label)+'</option>').join('')+'<option value="all">All model streams · include unavailable</option>';
 get('coverage-model').value=models.has('selected_latest_origin')?'selected_latest_origin':get('coverage-model').options[0].value;
 get('coverage-horizon').innerHTML=Object.entries(horizons).map(([id,label])=>'<option value="'+id+'">'+label+'</option>').join('');
 get('coverage-horizon').value='LATEST_OBSERVED';
 function changePeriod(){const value=get('coverage-period').value;get('coverage-model').value=value==='monday'?'preserved_selected_actual_T1':value==='9'?'selected_latest_origin':'selected_annual';get('coverage-horizon').value=value==='monday'?'T1':value==='9'?'LATEST_OBSERVED':'T2';render();}
 get('coverage-period').addEventListener('change',changePeriod);
 get('show-monday-game').addEventListener('click',()=>{get('coverage-period').value='monday';changePeriod();get('coverage-period').focus();});
 for(const id of ['coverage-model','coverage-horizon'])get(id).addEventListener('change',render);
 get('coverage-asof').textContent='Preserved model/evaluation snapshot '+D.as_of+' · '+allGames.filter(g=>g.completed).length+' completed games retained; '+allGames.filter(g=>g.week===9).length+' current-week games. Owner run status: '+D.owner_run_status+'. A separate primary-stream addendum displays 29 genuine early issues at '+I.as_of+'; no new fit or verified injury input is claimed. Completed artifacts are preserved; this status is not completed-pipeline acceptance.';
 function paired(){
  const year=Number(get('coverage-metric-season').value),week=get('coverage-metric-week').value,id=get('coverage-metric-model').value,provider=get('coverage-metric-provider').value,target=get('coverage-metric-target').value;
  const rows=(week==='ALL'?D.season_metrics:D.weekly_metrics).filter(r=>r.season===year&&(week==='ALL'||String(r.week)===week)&&r.model_id===id&&(provider==='all'||r.provider===provider)&&r.target===target);
  const heads=target==='win'?['Provider / cutoff','Common games','Model / provider correct','Model / provider log loss ↓','Model / provider Brier ↓','Model / provider AUC','Model / provider ECE ↓']:['Provider / cutoff','Common games','Model / provider MAE ↓','Model / provider RMSE ↓','Model / provider bias','Distribution coverage'];
  const out=rows.map(r=>{const a=r.model_metrics,b=r.provider_metrics;return target==='win'?[esc(r.provider)+'<br>'+esc(horizons[r.horizon]??r.horizon),num(a.games,0),num(a.correct,0)+' / '+num(b.correct,0),num(a.log_loss,6)+' / '+num(b.log_loss,6),num(a.brier,6)+' / '+num(b.brier,6),num(a.roc_auc,4)+' / '+num(b.roc_auc,4),num(a.ece_10,4)+' / '+num(b.ece_10,4)]:[esc(r.provider)+'<br>'+esc(horizons[r.horizon]??r.horizon),num(a.games,0),num(a.mae,3)+' / '+num(b.mae,3),num(a.rmse,3)+' / '+num(b.rmse,3),signed(a.bias)+' / '+signed(b.bias),esc(a.distribution_reason??'No registered interval export')];});
  get('coverage-paired-count').textContent=year+' · '+(week==='ALL'?'season totals':'Week '+week)+' · '+modelLabel(id)+' · '+rows.length+' matched provider rows. Each row uses exactly the same games for model and provider. Provider rows can have different event sets; do not rank across those cohorts.';
  get('coverage-paired-table').innerHTML=rows.length?table('Matched provider evaluation · '+year,heads,out):'<p class="empty-state">No equivalent authenticated comparison for this selection. Games remain in the full inventory. No missing market is inferred from a player prop or a spread threshold.</p>';
  const disagreements=D.disagreements.filter(r=>r.season===year&&(week==='ALL'||String(r.week)===week)&&r.model_set_id===id&&(provider==='all'||r.provider===provider));
  const filter=get('coverage-disagreement-result').value,shown=disagreements.filter(r=>filter==='all'||(filter==='model'?r.model_right:r.provider_right));
  const won=disagreements.filter(r=>r.model_right).length,lost=disagreements.filter(r=>r.provider_right).length,low=disagreements.filter(r=>r.provider_right&&r.model_probability_in_50s).length;
  get('coverage-disagreement-count').textContent=disagreements.length+' model/provider disagreement pairs · '+won+' model right · '+lost+' provider right · '+low+' of '+lost+' model losses had model confidence from 50% to below 60%. A game may occur once per provider; these are not independent bets.';
  get('coverage-disagreements').innerHTML=shown.length?table('Winning and losing disagreements', ['Week / game','Final','Model / provider','Correct side','Model confidence in 50s'], shown.map(r=>{const g=allGames.find(g=>g.game_id===r.game_id),a=g?.actual;return ['W'+r.week+' · '+esc(g?g.away+' at '+g.home:r.game_id),a?num(a.away_score,0)+'–'+num(a.home_score,0):esc(r.actual_winner),esc(r.model_pick)+' / '+esc(r.provider_pick)+' ('+esc(r.provider)+')',r.model_right?'Model':esc(r.provider),r.model_probability_in_50s?'Yes':'No'];})):'<p class="empty-state">No disagreements match this selection. This is not a claim of perfect accuracy or complete provider coverage.</p>';
 }
 get('coverage-metric-model').innerHTML=D.model_sets.map(m=>'<option value="'+esc(m.id)+'">'+esc(m.label)+'</option>').join('');
 get('coverage-metric-model').value='descriptive_feedback';
 get('coverage-metric-provider').innerHTML='<option value="all">All supported providers</option>'+providers.map(p=>'<option>'+esc(p)+'</option>').join('');
 get('coverage-metric-week').innerHTML='<option value="ALL">Full season</option>'+Array.from({length:22},(_,i)=>'<option value="'+(i+1)+'">Week '+(i+1)+'</option>').join('');
 for(const id of ['coverage-metric-season','coverage-metric-week','coverage-metric-model','coverage-metric-provider','coverage-metric-target','coverage-disagreement-result'])get(id).addEventListener('change',paired);
 paired();
 render();
})();
