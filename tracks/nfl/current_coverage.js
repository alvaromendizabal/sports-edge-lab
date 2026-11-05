// Offline public derived outputs only. Selecting a clock never changes a model.
(()=>{
 'use strict';
 const D=JSON.parse(document.getElementById('nfl-latest-evidence').textContent);
 const P=JSON.parse(document.getElementById('nfl-point-evidence').textContent);
 const R=JSON.parse(document.getElementById('nfl-source-overlay').textContent);
 const X=JSON.parse(document.getElementById('nfl-reschedule-reference').textContent);
 const H=JSON.parse(document.getElementById('nfl-latest-pregame').textContent);
 const N=JSON.parse(document.getElementById('nfl-n038-source').textContent);
 const C=JSON.parse(document.getElementById('nfl-n039-current-source').textContent);
 const C43=JSON.parse(document.getElementById('nfl-n043-current-source').textContent);
 const C42=JSON.parse(document.getElementById('nfl-n042-current-source').textContent);
 const C41=JSON.parse(document.getElementById('nfl-n041-current-source').textContent);
 const C40=JSON.parse(document.getElementById('nfl-n040-current-source').textContent);
 const annotateCurrent=r=>({...r,scheduleRecovery:r.provider==='DraftKings'&&r.game_id==='2026_09_LV_SF',datedRetained:r.provider==='DraftKings'&&r.game_id==='2026_09_LV_SF'&&r.acquired_at.startsWith('2026-11-04'),ownerRecoveredCurrent:r.provider==='DraftKings'&&r.game_id==='2026_09_LV_SF'&&['2026-11-05T04:34:39Z','2026-11-05T08:01:37Z'].includes(r.acquired_at),reviewRecoveredCurrent:r.provider==='DraftKings'&&r.game_id==='2026_09_LV_SF'&&r.acquired_at==='2026-11-05T02:25:27Z'});
 const order=(a,b)=>Date.parse(a.quote_at)-Date.parse(b.quote_at)||Date.parse(a.acquired_at)-Date.parse(b.acquired_at);
 const latestWinners=new Map([...H.winner_rows,...N.winner_rows].sort(order).map(r=>[[r.game_id,r.provider].join('|'),{...r,latestHistory:true}]));
 const latestPoints=new Map([...H.point_rows,...N.point_rows].sort(order).map(r=>[[r.game_id,r.provider,r.target].join('|'),{...r,latestHistory:true}]));
 const Z=JSON.parse(document.getElementById('nfl-source-recovery').textContent);
 const recoveredWinners=new Map(Z.winner_rows.map(r=>[[r.game_id,r.provider].join('|'),r]));
 const recoveredPoints=new Map(Z.point_rows.map(r=>[[r.game_id,r.provider,r.target].join('|'),r]));
 const mappedWinners=new Map(X.winner_rows.map(r=>[[r.game_id,r.provider].join('|'),{...r,scheduleRecovery:true}]));
 const mappedPoints=new Map(X.point_rows.map(r=>[[r.game_id,r.provider,r.target].join('|'),{...r,scheduleRecovery:true}]));
 const dkWinners=N.draftkings_week9.map(r=>({...r,scheduleRecovery:r.normalization_role==='DOCUMENTED_KICKOFF_REVISION_RECOVERY',p_home:r.p_home_no_vig,horizon:'LATEST_OBSERVED',quote_clock_kind:'PROVIDER_BOOKMAKER_LAST_UPDATE',availability_status:'OBSERVED_WINNER_REFERENCE'}));
 const dkPoints=N.draftkings_week9.flatMap(r=>['margin','total'].map(target=>({...r,scheduleRecovery:r.normalization_role==='DOCUMENTED_KICKOFF_REVISION_RECOVERY',target,horizon:'LATEST_OBSERVED',line:target==='margin'?r.home_margin_line_reference:r.total_line_reference,predicate:(target==='margin'?'Home margin > '+r.home_margin_line_reference+' (home handicap '+r.home_spread+')':'Game total > '+r.total_line_reference),observed_probability:null,contract_count:1,quote_clock_kind:'PROVIDER_BOOKMAKER_LAST_UPDATE',reason:'Dated quoted line; not an expected score or executable offer.'})));
 const sourceWinners=new Map([...R.winner_rows,...dkWinners,...N.current_winner_rows,...C.winner_rows.map(annotateCurrent),...C40.winner_rows.map(annotateCurrent),...C41.winner_rows.map(annotateCurrent),...C42.winner_rows.map(annotateCurrent),...C43.winner_rows.map(annotateCurrent)].map(r=>[[r.game_id,r.provider].join('|'),r]));
 const sourcePoints=new Map([...R.point_rows,...dkPoints,...N.current_point_rows,...C.point_rows.map(annotateCurrent),...C40.point_rows.map(annotateCurrent),...C41.point_rows.map(annotateCurrent),...C42.point_rows.map(annotateCurrent),...C43.point_rows.map(annotateCurrent)].map(r=>[[r.game_id,r.provider,r.target].join('|'),r]));
 const pointIndex=new Map(P.rows.map(r=>[[r.game_id,r.provider,r.target,r.horizon].join('|'),r]));
 const get=id=>document.getElementById(id);
 const esc=x=>String(x??'Not available').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const num=(x,n=1)=>x==null?'Not available':Number(x).toFixed(n);
 const pct=x=>x==null?'Not available':num(100*x,1)+'%';
 const signed=x=>x==null?'Not available':(x>0?'+':'')+num(x);
 const when=x=>x?new Intl.DateTimeFormat('en-US',{timeZone:'America/Los_Angeles',month:'short',day:'numeric',hour:'numeric',minute:'2-digit',timeZoneName:'short'}).format(new Date(x)):'Not recorded';
 const horizons={T2:'2 hours before kickoff',T1:'1 hour before kickoff',LATEST_PREGAME:'Latest before kickoff',LATEST_OBSERVED:'Latest observed upcoming'};
 const E=JSON.parse(document.getElementById('nfl-injury-issue').textContent);
 const experimentalIssues=new Map(E.cards.map(f=>[f.game_id,f]));
 const F=JSON.parse(document.getElementById('nfl-injury-refresh').textContent);
 const refreshIssues=new Map(F.cards.map(f=>[f.game_id,f]));
 const G=JSON.parse(document.getElementById('nfl-injury-n040').textContent);
 const priorInjuryIssues=new Map(G.cards.map(f=>[f.game_id,f]));
 const J=JSON.parse(document.getElementById('nfl-injury-n041').textContent);
 const latestInjuryIssues=new Map(J.cards.map(f=>[f.game_id,f]));
 const Q42=JSON.parse(document.getElementById('nfl-current-issues-n042').textContent);
 const Q43=JSON.parse(document.getElementById('nfl-current-issues-n043').textContent);
 const Q={streams:[...Q42.streams,...Q43.streams]};
 const n042Cards=new Map(Q.streams.map(s=>[s.id,new Map(s.cards.map(f=>[f.game_id,f]))]));
 const forecastModels=[...D.model_sets,...Q.streams.map(s=>({id:s.id,label:s.label})),{id:'experimental_injury_issue',label:'Experimental injury challenger · Nov 4'},{id:'experimental_injury_refresh',label:'Prior injury refresh · Nov 5, 00:10 UTC'},{id:'experimental_injury_n040',label:'Prior injury refresh · Nov 5, 01:21 UTC'},{id:'experimental_injury_n041',label:'Prior injury refresh · Nov 5, 02:26 UTC'}];
 const models=new Map(forecastModels.map(x=>[x.id??x.model_id,x]));
 const modelLabel=id=>models.get(id)?.label??models.get(id)?.model_label??id;
 const modelId=f=>f.model_id??f.model_set_id;
 const I=JSON.parse(document.getElementById('nfl-primary-issue').textContent);
 const primaryIssues=new Map(I.cards.map(f=>[f.game_id,f]));
 const allGames=D.all_games.map(g=>{
  const issued=primaryIssues.get(g.game_id);
  if(g.completed||!issued)return g;
  return {...g,forecasts:g.forecasts.map(f=>modelId(f)===issued.model_id&&(!f.actual_issue_at||Date.parse(issued.actual_issue_at)>Date.parse(f.actual_issue_at))?issued:f)};
  }).map(g=>{
  const experimental=experimentalIssues.get(g.game_id);
  const refresh=refreshIssues.get(g.game_id);const prior=priorInjuryIssues.get(g.game_id);const latest=latestInjuryIssues.get(g.game_id);
  return g.completed?g:{...g,forecasts:[...g.forecasts,...(experimental?[experimental]:[]),...(refresh?[refresh]:[]),...(prior?[prior]:[]),...(latest?[latest]:[]),...Q.streams.map(s=>n042Cards.get(s.id).get(g.game_id)).filter(Boolean)]};
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
  if(r.latestHistory)return 'Pregame observation '+when(r.quote_at)+' · retrospectively acquired '+when(r.acquired_at)+' · no original possession or fill claim';
  if(r.ownerRecoveredCurrent)return 'Current quote '+when(r.quote_at)+' · captured '+when(r.acquired_at)+' · exact schedule revision recovered on the owner runtime';
  if(r.reviewRecoveredCurrent)return 'Current quote '+when(r.quote_at)+' · captured '+when(r.acquired_at)+' · exact schedule revision recovered during review; original normalizer omitted this event';
  if(r.datedRetained)return 'Retained November 4 quote '+when(r.quote_at)+' · captured '+when(r.acquired_at)+' · absent from latest capture; earlier public evidence retained, latest owner fallback failed';
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
  const alternate=String(r.reason??'').startsWith('Captured alternate threshold only')?'<br><span class="fine alternate-threshold">Alternate threshold · main line not established</span>':'';
  return '<strong>'+esc(r.predicate)+'</strong>'+alternate+'<br>'+probability+'<br><span class="fine">'+esc(state)+'</span>';
 }
 function n042Context(f){
  const counts=Object.entries(f.injury_source_report_team_count).map(([team,n])=>team+' '+n).join(' and ');
  const has=Object.values(f.injury_source_report_team_count).some(n=>n>0);
  return '<p class="fine injury-status n042-injury-status"><strong>'+esc(f.model_label)+' · injury inputs:</strong> '+(has?'Partial listed reports: '+esc(counts)+' rows.':'No current report rows admitted. Unknown reports do not mean healthy players.')+' Announced starters, full quarterback depth and reserve roles are not verified model inputs.</p><p class="fine n042-model-status"><strong>'+esc(f.calibration_applied?'Preserved calibration':'Raw and uncalibrated research')+'</strong> · '+f.current_training_games+' earlier current-season training games. '+(f.model_id.endsWith('_original')?'Winner has no direct injury fields; point heads use injury inputs.':'Fixed historical recipe includes injury contributions; no automatic promotion or new validation claim.')+'</p><p class="fine n042-clocks">Base features: '+esc(when(f.base_feature_asof_at))+'. Injury cutoff: '+esc(when(f.injury_cutoff_at))+'. Fit completed: '+esc(when(f.fit_completed))+'. Issued: '+esc(when(f.actual_issue_at))+'. Later market references are supplemental observations and do not amend the forecast inputs.</p>';
 }
 function experimentalContext(f){
  const partial=f.injury_report_status==='PARTIAL_LISTED_REPORTS';
  const refreshed=['experimental_injury_refresh','experimental_injury_n040','experimental_injury_n041'].includes(modelId(f));
  const listed=Object.entries(f.injury_source_report_team_count??{}).map(([team,count])=>team+' '+count).join(' and ');
  const report=refreshed?(partial?'Partial listed reports: '+listed+' admitted feature-report rows. This is not a complete roster-health census.':'No current report rows were admitted for this game. Unknown reports do not mean healthy players.'):partial?'Partial listed reports: BAL 9 and JAX 5 admitted rows; 14 rows excluded. Lamar Jackson’s listed DNP was included; Tyler Huntley and Joe Fagnano were excluded by identity matching.':'No current report rows were admitted for this game. Unknown reports do not mean healthy players.';
  return '<p class="fine injury-status experimental-injury-status"><strong>'+esc(f.model_label)+' · injury inputs:</strong> '+esc(report)+' Announced starter, depth chart and injured-reserve status are not verified model inputs.</p><p class="fine experimental-target-views"><strong>Target differences:</strong> Winner uses base features without direct injury fields. Margin and total use injury features with unknown-report flags. These are separate fitted targets; their directions can differ.</p><p class="fine experimental-intervals"><strong>Reference intervals:</strong> home margin '+signed(f.margin_interval.lower)+' to '+signed(f.margin_interval.upper)+' (80% nominal); total '+num(f.total_interval.lower)+' to '+num(f.total_interval.upper)+'. Fixed pre-2024 residual quantiles; no coverage guarantee.</p><p class="fine experimental-clocks">Base features: '+esc(when(f.base_feature_asof_at))+'. Report observed: '+esc(f.injury_observed_at?when(f.injury_observed_at):'No current report admitted')+'. Issued: '+esc(when(f.actual_issue_at))+'. Exact source, injury, fit and issue clocks are in the details below. Early research issue; no final-hour qualification or betting recommendation. Later market observations below are supplemental comparisons, not necessarily inputs available at this issue.</p>';
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
   const experimental=selected.filter(f=>['experimental_injury_issue','experimental_injury_refresh','experimental_injury_n040','experimental_injury_n041'].includes(modelId(f))&&f.pick);
   const current=selected.filter(f=>/^n04[23]_/.test(String(modelId(f)))&&f.pick);
   if(current.length)html+=current.map(n042Context).join('');
   else if(experimental.length)html+=experimental.map(experimentalContext).join('');
   else html+='<p class="fine injury-status"><strong>Current injury/QB information:</strong> Not verified in this forecast.'+(g.game_id==='2026_09_JAX_BAL'?' <a href="#ravens-qb-context">Read the separate Ravens update.</a>':'')+'</p>';
   html+='<p class="fine wager-status"><strong>Personal wager activity:</strong> Not tracked in this dashboard.</p>';
  }
  html+=table('Selected model outputs · '+g.away+' at '+g.home,['Forecast series','Winner','Home margin','Total'],selected.map(f=>[esc(f.model_label??modelLabel(modelId(f)))+'<span class="game-origin">'+esc(f.issue_class==='RECONSTRUCTED_NOT_ORIGINAL_ISSUED'?'Retrospective reconstruction':f.issue_class==='SAVED_OR_RECONSTRUCTED_NOT_ORIGINAL_ISSUED'?'Saved vector · no original issue':f.issue_class==='EARLY_CURRENT_ROLLING_RAW_RESEARCH_ISSUE'?'Actual current rolling research issue · raw':f.issue_class==='EARLY_FORWARD_RAW_SHADOW_ISSUE'?'Actual shadow issue · raw':f.issue_class==='EARLY_FORWARD_RESEARCH_ISSUE'?'Actual early research issue':f.issue_class==='T1_RESEARCH_ACTUAL_ISSUE'?'Actual 1-hour research issue':'Unavailable')+'</span>',f.pick?'<strong>'+esc(f.pick)+' '+pct(f.pick_probability)+'</strong>'+(actual?'<br>'+esc(actual.winner==='TIE'?'Tie':f.pick===actual.winner?'Correct winner':'Incorrect winner'):''):'Not available',signed(f.home_margin)+(actual&&f.home_margin!=null?'<br><span class="fine">Actual '+signed(actual.home_margin)+' · absolute error '+num(Math.abs(f.home_margin-actual.home_margin))+'</span>':''),num(f.total)+(actual&&f.total!=null?'<br><span class="fine">Actual '+num(actual.total)+' · absolute error '+num(Math.abs(f.total-actual.total))+'</span>':'')]));
  const refreshed=selected.find(f=>modelId(f)==='experimental_injury_n041')??selected.find(f=>modelId(f)==='experimental_injury_n040')??selected.find(f=>modelId(f)==='experimental_injury_refresh');
  const prior=refreshed&&modelId(refreshed)==='experimental_injury_n041'?priorInjuryIssues.get(g.game_id):refreshed&&modelId(refreshed)==='experimental_injury_n040'?refreshIssues.get(g.game_id):experimentalIssues.get(g.game_id);
  if(refreshed&&prior)html+='<p class="fine refresh-change"><strong>Since the prior issue:</strong> winner '+pct(prior.pick_probability)+' → '+pct(refreshed.pick_probability)+'; home margin '+signed(prior.home_margin)+' → '+signed(refreshed.home_margin)+'; total '+num(prior.total)+' → '+num(refreshed.total)+'. Same fitted heads, refreshed eligible injury observations; no new fit or retrospective performance gain is claimed.</p>';
  html+=table(horizons[h]+' · derived provider directions',['Provider','Winner direction','Evidence state'],market.map(p=>[esc(p.provider),p.derived_pick?'<strong>'+esc(p.derived_pick)+(typeof p.p_home==='number'?' '+pct(p.derived_pick===g.home?p.p_home:1-p.p_home):'')+'</strong>'+(actual?'<br>'+esc(actual.winner==='TIE'?'Tie':p.correct?'Correct winner':'Incorrect winner'):''):'Not available',p.derived_pick?'<span class="provider-state covered">'+(p.latestHistory?'Retrospective pregame reference':p.scheduleRecovery?'Recovered schedule reference':p.sourceRecovery?'Recovered observation':p.quote_at?'Observed':'Saved reference')+'</span><br>'+esc(clockText(p)):'<span class="provider-state">Coverage gap</span><br>'+esc(p.unavailable_reason??p.availability_status)]));
  html+=table('Market spread and total references · '+g.away+' at '+g.home,['Provider','Home-margin condition','Total condition'],providers.map(p=>[esc(p),pointCell(g,p,'margin',h),pointCell(g,p,'total',h)]));
  html+='<p class="fine">Home margin means '+esc(g.home)+' points minus '+esc(g.away)+' points. A threshold and its probability are not a predicted final margin, mean total or model cover probability.</p>';
  if(g.game_id===X.event_mapping.game_id&&h==='LATEST_OBSERVED')html+='<p class="fine schedule-mapping-note"><strong>Separately verified event mapping:</strong> provider kickoff '+esc(X.event_mapping.provider_kickoff_utc)+'; canonical kickoff '+esc(X.event_mapping.canonical_kickoff_utc)+'; mapping verified '+esc(X.event_mapping.mapping_observed_at)+'. Schedule-revision first publication is unknown. No original forecast or historical metric changed.</p>';
  html+='<p class="fine clock-context">Model information time stays fixed when the market reference changes. '+(h==='T2'?'Same-cutoff comparison only for model rows explicitly labelled T2.':h==='T1'?'A T2 model versus this later T1 market is a supplemental comparison.':h==='LATEST_PREGAME'?'This is a later market benchmark, not a reissued historical prediction.':'This is an observed upcoming reference, not a final pregame quote.')+'</p>';
  html+='<details><summary>Forecast, quote and acquisition clocks</summary><ul>';
  for(const f of selected)html+='<li><strong>'+esc(f.model_label??modelLabel(modelId(f)))+'</strong><br>'+esc(f.unavailable_reason??f.origin??'Selected public output')+'<br>Model horizon: '+esc(f.horizon??'Unavailable')+'; issued: '+esc(f.actual_issue_at??'No original issue; do not backdate')+'; source/feature boundary: '+esc(f.source_asof??'Not separately exported')+'; fit completed: '+esc(f.fit_completed??'Not separately exported')+'.</li>';
  for(const f of selected)if(['experimental_injury_issue','experimental_injury_refresh','experimental_injury_n040','experimental_injury_n041'].includes(modelId(f)))html+='<li class="experimental-exact-clocks"><strong>Experimental injury clocks (UTC)</strong><br>Base features: '+esc(f.base_feature_asof_at)+'; injury cutoff: '+esc(f.injury_cutoff_at)+'; report observed: '+esc(f.injury_observed_at??'No current report admitted')+'; fit completed: '+esc(f.fit_completed)+'; issued: '+esc(f.actual_issue_at)+'.</li>';
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
  get('coverage-clock-note').textContent=h==='T2'?'T2 means two hours before kickoff. Use the last genuine observation at or before that cutoff; an exact-minute quote is not required. Quote age stays visible.':h==='T1'?'T1 means one hour before kickoff. It is a separate market reference. Earlier T2 model outputs retain their original information boundary.':h==='LATEST_PREGAME'?'Latest before kickoff is the last authenticated observation strictly before the game starts. It may be shown even when it is later than T2. Missing latest history is never replaced silently with a T2 quote. All 121 completed games have separately authenticated Kalshi and Polymarket winner, margin and total references. DraftKings latest-pregame references remain outside this public historical export.':'Latest observed upcoming shows a real observed market state for an unstarted game, when available. Reaching T2 is not a requirement for displaying it. An observation is not an executable bet.';
  get('coverage-point-counts').innerHTML=table('Provider coverage by prediction target',['Provider','Winner direction','Margin reference','Total reference'],providers.map(p=>[esc(p),games.filter(g=>providerRow(g,p,h).derived_pick).length+' / '+games.length,...['margin','total'].map(t=>{const rows=games.map(g=>pointRow(g,p,t,h)).filter(r=>r?.line!=null),saved=rows.filter(r=>r.availability_status==='SAVED_LINE_REFERENCE_CLOCK_UNAVAILABLE').length;return (rows.length-saved)+' / '+games.length+' dated references'+(saved?'<br><span class="fine">'+saved+' saved lines · clocks unavailable</span>':'');})]));
  get('coverage-games').innerHTML=games.map(g=>card(g,id,h)).join('');
  document.getElementById('partial-source-status').textContent='Week 9 has fresh Kalshi and Polymarket references for all 15 games. DraftKings also has all 15 current event captures after exact owner schedule recovery of LV–SF. The unchanged base normalizer covered 14; the recovery retains the actual new capture clock without an additional provider request. These are dated early-week observations. Polymarket includes alternate thresholds, not necessarily main lines; threshold prices are not mean-score projections. Historical backfill and additional strikes remain incomplete. Current references are not applied to the selected historical horizon.';
 }
 get('coverage-period').innerHTML='<option value="9">Current week · Week 9 · 15 games</option><option value="completed">All completed games · 121 finals</option><option value="monday">Monday Nov 2 · CHI 34–17 SEA</option>'+[...new Set(allGames.map(g=>g.week))].sort((a,b)=>a-b).map(w=>'<option value="'+w+'">Week '+w+' · '+allGames.filter(g=>g.week===w).length+' games</option>').join('')+'<option value="all">Full season · 272 scheduled games</option>';
 get('coverage-model').innerHTML=forecastModels.map(m=>'<option value="'+esc(m.id??m.model_id)+'">'+esc(m.label??m.model_label)+'</option>').join('')+'<option value="all">All model streams · include unavailable</option>';
 get('coverage-model').value=models.has('selected_latest_origin')?'selected_latest_origin':get('coverage-model').options[0].value;
 get('coverage-horizon').innerHTML=Object.entries(horizons).map(([id,label])=>'<option value="'+id+'">'+label+'</option>').join('');
 get('coverage-horizon').value='LATEST_OBSERVED';
 function changePeriod(){const value=get('coverage-period').value;get('coverage-model').value=value==='monday'?'preserved_selected_actual_T1':value==='9'?'selected_latest_origin':'selected_annual';get('coverage-horizon').value=value==='monday'?'T1':value==='9'?'LATEST_OBSERVED':'T2';render();}
 get('coverage-period').addEventListener('change',changePeriod);
 get('show-monday-game').addEventListener('click',()=>{get('coverage-period').value='monday';changePeriod();get('coverage-period').focus();});
 for(const role of ['original','shadow'])get('show-'+role+'-n043').addEventListener('click',()=>{get('coverage-period').value='9';get('coverage-model').value='n043_'+role;get('coverage-horizon').value='LATEST_OBSERVED';render();get('coverage-model').focus();});
 for(const role of ['fresh','original','shadow'])get('show-'+role+'-n042').addEventListener('click',()=>{get('coverage-period').value='9';get('coverage-model').value='n042_'+role;get('coverage-horizon').value='LATEST_OBSERVED';render();get('coverage-model').focus();});
 get('show-injury-n041').addEventListener('click',()=>{get('coverage-period').value='9';get('coverage-model').value='experimental_injury_n041';get('coverage-horizon').value='LATEST_OBSERVED';render();get('coverage-model').focus();});
 get('show-injury-n040').addEventListener('click',()=>{get('coverage-period').value='9';get('coverage-model').value='experimental_injury_n040';get('coverage-horizon').value='LATEST_OBSERVED';render();get('coverage-model').focus();});
 get('show-injury-refresh').addEventListener('click',()=>{get('coverage-period').value='9';get('coverage-model').value='experimental_injury_refresh';get('coverage-horizon').value='LATEST_OBSERVED';render();get('coverage-model').focus();});
 get('show-injury-challenger').addEventListener('click',()=>{get('coverage-period').value='9';get('coverage-model').value='experimental_injury_issue';get('coverage-horizon').value='LATEST_OBSERVED';render();get('coverage-model').focus();});
 for(const id of ['coverage-model','coverage-horizon'])get(id).addEventListener('change',render);
 get('coverage-asof').textContent='Preserved model/evaluation snapshot '+D.as_of+' · '+allGames.filter(g=>g.completed).length+' completed games retained; '+allGames.filter(g=>g.week===9).length+' current-week games. Owner run status: '+D.owner_run_status+'. A separate primary-stream addendum displays 29 genuine early issues at '+I.as_of+'; that primary-stream issue has no new fit or verified injury input. The prior injury refresh is dated '+F.as_of+'; the prior separate issue is '+G.as_of+' and its next preserved refresh is '+J.as_of+'; N042 separately adds calibrated original, raw shadow and raw current rolling streams at '+Q.streams.map(s=>s.actual_issue_at).join(', ')+'. Completed artifacts are preserved; this status is not completed-pipeline acceptance.';
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
