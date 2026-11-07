'use strict';
(()=>{
 const D=window.FBS_COMPLETE_DATA,H=window.FBS_COMPLETE_HISTORY,$=id=>document.getElementById(id);
 if(!D||!H){$('result-status').textContent='The report could not be loaded. Use the full season JSON.';return;}
 const games=D.rows.map(row=>Object.fromEntries(D.columns.map((key,index)=>[key,row[index]])));
 const providers=D.providers, state={period:'all',page:0,registryPage:0}; const PAGE=30;
 const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const pct=v=>v==null?'Not recorded':(v*100).toFixed(1)+'%';
 const num=(v,d=1)=>v==null?'Not reported':Number(v).toFixed(d);
 const signed=v=>v==null?'Not recorded':(v>0?'+':'')+Number(v).toFixed(1);
 const time=v=>v?new Intl.DateTimeFormat('en-US',{timeZone:'America/Los_Angeles',month:'short',day:'numeric',hour:'numeric',minute:'2-digit',timeZoneName:'short'}).format(new Date(v)):'Time not retained';
 const pretty=v=>String(v||'No retained record').replaceAll('_',' ').toLowerCase().replace(/^./,c=>c.toUpperCase());
 const missingModel=g=>g.completed?'No retained replay for this completed game':'No authenticated pregame projection';
 const quarantined=g=>/QUARANTINED/.test(g.schedule_join||'');
 const support=(g,p,t)=>{try{return JSON.parse(g[`${p}_${t}_point_support`]||'null');}catch{return null;}};
 function reference(g,p,t){
  const v=g[`${p}_${t}_value`],s=support(g,p,t);
  if(quarantined(g))return {value:'Identity quarantine',kind:'Older kickoff reference excluded from the current join',present:false};
  if(s&&(s.lower_bound!=null||s.upper_bound!=null)){
   const lo=s.lower_bound==null?'open':t==='margin'?signed(s.lower_bound):num(s.lower_bound);
   const hi=s.upper_bound==null?'open':t==='margin'?signed(s.upper_bound):num(s.upper_bound);
   return {value:`${lo} to ${hi}`,kind:'Quoted median interval · not expected points',present:true};
  }
  if(v!=null)return{value:t==='winner'?pct(v):t==='margin'?signed(v):num(v),kind:t==='winner'?'Home-side reference probability':pretty(g[`${p}_${t}_reference_kind`]),present:true};
  return{value:'No retained value',kind:pretty(g[`${p}_${t}_status`]),present:false};
 }
 function option(value,label){return `<option value="${esc(value)}">${esc(label)}</option>`;}
 $('provider-filter').innerHTML=providers.map(p=>option(p,p)).join('');
 [...new Set(games.map(g=>g.week))].sort((a,b)=>a-b).forEach(w=>$('week-filter').insertAdjacentHTML('beforeend',option(w,'Week '+w)));
 function filtered(){const q=$('game-search').value.trim().toLowerCase(),result=$('result-filter').value,model=$('model-filter').value,week=$('week-filter').value;return games.filter(g=>(state.period==='all'||g.period===state.period)&&(!q||`${g.id} ${g.away} ${g.home}`.toLowerCase().includes(q))&&(result==='all'||(result==='complete')===g.completed)&&(week==='all'||g.week===Number(week))&&(model==='all'||model==='present'&&g.replay_p_home!=null||model==='missing'&&g.replay_p_home==null||model==='quarantine'&&quarantined(g)));}
 function small(value){return `<span class="cell-sub">${esc(value)}</span>`;}
 function absent(reason){return `<span class="no-value">${esc(reason)}</span>`;}
 function renderGames(){
  const list=filtered(),p=$('provider-filter').value;state.page=Math.max(0,Math.min(state.page,Math.ceil(list.length/PAGE)-1));
  const page=list.slice(state.page*PAGE,(state.page+1)*PAGE),completed=list.filter(g=>g.completed).length,replays=list.filter(g=>g.replay_p_home!=null).length;
  $('result-status').textContent=`${list.length} games · ${completed} observed complete · ${replays} retained replays`;
  $('period-label').textContent=state.period==='all'?'Cumulative dated capture':D.periods[state.period].label+' · America/Los_Angeles';
  $('reference-heading').innerHTML=esc(p)+'<br><small>retained reference</small>';
  const cov=t=>list.filter(g=>reference(g,p,t).present).length;
  $('provider-coverage').innerHTML=`<span><b>${esc(p)}</b> in this selection</span><span>Winner <b>${cov('winner')} / ${list.length}</b></span><span>Margin line or interval <b>${cov('margin')} / ${list.length}</b></span><span>Total line or interval <b>${cov('total')} / ${list.length}</b></span><span>Historical possession verified: <b>0</b></span>`;
  $('game-rows').innerHTML=page.map(g=>{
   const r=reference(g,p,'winner'),m=reference(g,p,'margin'),t=reference(g,p,'total'),has=g.replay_p_home!=null;
   const picked=has?(g.replay_p_home>=.5?g.replay_p_home:1-g.replay_p_home):null;
   const actual=g.completed?`<span class="cell-value">${esc(g.away_score)} – ${esc(g.home_score)}</span>${small(g.winner+' won')}`:'<span class="chip">No observed final</span>';
   return `<tr><td><span class="matchup">${esc(g.away)} <span class="subtle">at</span> ${esc(g.home)}</span>${small(time(g.kickoff))}${small('Week '+g.week+' · '+g.id)}${quarantined(g)?'<span class="chip amber">Kickoff join quarantined</span>':''}${g.changed_result?'<span class="chip">Updated final</span>':''}</td><td>${actual}</td><td>${has?`<span class="cell-value">${esc(g.replay_winner)}</span>${small(g.replay_correct?'Correct retained pick':'Incorrect retained pick')}`:absent(missingModel(g))}</td><td>${has?`<span class="cell-value">${pct(picked)}</span>${small('Home '+pct(g.replay_p_home))}`:absent('No model probability')}</td><td>${has?`<span class="cell-value">${signed(g.replay_margin)}</span>`:absent('No model point estimate')}</td><td>${absent('No qualified cover probability')}</td><td>${has?`<span class="cell-value">${num(g.replay_total)}</span>`:absent('No model total')}</td><td>${r.present?`<span class="cell-value">Home ${esc(r.value)}</span>`:absent(r.value)}${small('Margin: '+m.value)}${small('Total: '+t.value)}${g[`${p}_winner_quote_at`]?small('Quote '+time(g[`${p}_winner_quote_at`])):small('Quote time not retained')}</td><td><button class="row-button" data-game="${esc(g.id)}" aria-label="Details for ${esc(g.away)} at ${esc(g.home)}">↗</button></td></tr>`;
  }).join('')||'<tr><td colspan="9">No games match these filters. Change a filter to restore the fixture list.</td></tr>';
  $('page-status').textContent=`${list.length?state.page+1:0} / ${Math.ceil(list.length/PAGE)}`;
  $('prev-page').disabled=state.page===0;$('next-page').disabled=(state.page+1)*PAGE>=list.length;
 }
 document.querySelectorAll('[data-period]').forEach(button=>button.addEventListener('click',()=>{state.period=button.dataset.period;state.page=0;document.querySelectorAll('[data-period]').forEach(b=>b.setAttribute('aria-pressed',String(b===button)));renderGames();}));
 ['game-search','result-filter','model-filter','provider-filter','week-filter'].forEach(id=>$(id).addEventListener(id==='game-search'?'input':'change',()=>{state.page=0;renderGames();}));
 $('prev-page').addEventListener('click',()=>{state.page--;renderGames();});$('next-page').addEventListener('click',()=>{state.page++;renderGames();});
 function modelCard(label,value,reason){return `<article><span>${esc(label)}</span><strong>${esc(value)}</strong><span>${esc(reason)}</span></article>`;}
 function openGame(id){
  const g=games.find(x=>x.id===id);if(!g)return;
  $('dialog-title').textContent=g.away+' at '+g.home;
  $('dialog-meta').textContent='2026 · Week '+g.week+' · Official ID '+g.id;
  $('dialog-summary').innerHTML=`<div class="dialog-summary"><span>${esc(time(g.kickoff))}</span><span>${g.completed?esc(g.away_score+' – '+g.home_score+' · '+g.winner+' won'):'No final observed in this capture'}</span><span>${esc(g.population.replaceAll('_',' '))}</span></div>${quarantined(g)?`<div class="notice"><strong>Kickoff revision quarantines the older join.</strong><span>Current official kickoff: ${esc(g.kickoff)}. Older reference kickoff: ${esc(g.previous_kickoff)}. The old model/market identity is not admitted under the new kickoff.</span></div>`:''}`;
  const has=g.replay_p_home!=null;
  $('dialog-model').innerHTML=`<div class="dialog-model">${modelCard('Model winner',has?g.replay_winner:'No projection',has?'Retained retrospective replay':missingModel(g))}${modelCard('Home win probability',has?pct(g.replay_p_home):'Not issued','Original pregame issue time not authenticated')}${modelCard('Home margin',has?signed(g.replay_margin):'No estimate','Positive means the home team')}${modelCard('Cover probability','Not produced','No qualified conditional distribution or cover forecast')}${modelCard('Total points',has?num(g.replay_total):'No estimate',has?num(g.replay_away)+' away · '+num(g.replay_home)+' home':'No model point estimate retained')}</div><p class="subtle">Rolling forecast: no authenticated issue. Prediction intervals: not retained. Injury-adjusted forecast: unavailable. Model report retained at ${esc(D.retained_model_report_at)}; this publication created no new predictions.</p>`;
  $('dialog-providers').innerHTML=providers.map(p=>`<article class="provider-detail"><h4>${esc(p)}</h4>${['winner','margin','total'].map(t=>{
   const r=reference(g,p,t),prefix=`${p}_${t}_`,details=[['Native status',g[prefix+'status']],['Quote timestamp',g[prefix+'quote_at']],['Acquired timestamp',g[prefix+'captured_at']],['Declared cutoff',g[prefix+'declared_cutoff_from_matching_retained_detail']],['Interval end',g[prefix+'interval_end_from_matching_retained_detail']],['Product',g[prefix+'product_from_matching_retained_detail']],['Reference kind',g[prefix+'reference_kind']],['Clock evidence',g[prefix+'clock_evidence_status']],['Historical possession',g[prefix+'historical_possession_proved']==='true'?'Verified':'Not proved'],['Original join',g[prefix+'full_detail_match_status']]];
   return `<div class="provider-target"><strong>${t==='winner'?'Home probability':t==='margin'?'Home margin reference':'Total reference'}: ${esc(r.value)}</strong><p>${esc(r.kind)}</p><details><summary>Inspect product, cutoff & source clocks</summary><dl>${details.map(([key,value])=>`<dt>${esc(key)}</dt><dd>${esc(value||'No retained evidence')}</dd>`).join('')}</dl></details></div>`;
  }).join('')}</article>`).join('');
  $('game-dialog').showModal();
 }
 $('game-rows').addEventListener('click',event=>{const button=event.target.closest('[data-game]');if(button)openGame(button.dataset.game);});
 $('dialog-close').addEventListener('click',()=>$('game-dialog').close());
 $('game-dialog').addEventListener('click',event=>{if(event.target===$('game-dialog')){const r=event.target.getBoundingClientRect();if(event.clientX<r.left||event.clientX>r.right||event.clientY<r.top||event.clientY>r.bottom)event.target.close();}});
 $('export-csv').addEventListener('click',()=>{
  const columns=['id','away','home','kickoff','week','completed','away_score','home_score','replay_status','replay_winner','replay_p_home','replay_margin','replay_total','cover_status','rolling_status','schedule_join'];
  for(const p of providers)for(const t of ['winner','margin','total'])columns.push(`${p}_${t}_value`,`${p}_${t}_status`,`${p}_${t}_quote_at`,`${p}_${t}_captured_at`,`${p}_${t}_point_support`);
  const cell=v=>'"'+String(v??'').replace(/^([=+@\t\r])/,'\'$1').replaceAll('"','""')+'"';
  const csv=[columns.map(cell).join(','),...filtered().map(g=>columns.map(k=>cell(g[k])).join(','))].join('\r\n');
  const a=document.createElement('a'),url=URL.createObjectURL(new Blob([csv],{type:'text/csv;charset=utf-8'}));a.href=url;a.download='fbs-2026-'+state.period+'-dated-review.csv';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
 });
 function renderComparison(){const c=H.common.cohorts.find(c=>c.horizon===$('comparison-horizon').value);$('comparison-rows').innerHTML=Object.entries(c.metrics).map(([p,m])=>`<tr><td><strong>${esc(p==='model'?'Retained model':p)}</strong></td><td>${m.games}</td><td>${pct(m.accuracy)}</td><td>${num(m.logloss,4)}</td><td>${num(m.brier,4)}</td></tr>`).join('');$('comparison-cohort').textContent='Exact cohort SHA-256: '+c.identity_sha256+'. Existing rounded-input diagnostic; same model prediction cutoff unproven.';}
 $('comparison-horizon').addEventListener('change',renderComparison);
 $('provider-cards').innerHTML=providers.map(p=>{const count=t=>games.filter(g=>reference(g,p,t).present).length;return `<article><h3>${esc(p)}</h3><strong>${count('winner')} <span class="subtle">/ 888</span></strong><div class="mini-line"><span>Retained winner reference</span></div><div class="meter"><span style="width:${count('winner')/888*100}%"></span></div><div class="mini-line"><span>Margin line / interval</span><b>${count('margin')}</b></div><div class="mini-line"><span>Total line / interval</span><b>${count('total')}</b></div><p>Numeric and interval availability includes descriptive references. Quote eligibility and historical possession require separate proof. Fees, depth and liquidity are not retained here.</p></article>`;}).join('');
 const registry=H.registry.rows,cohorts=[...new Map(registry.map(r=>[r.cohort_sha256,{season:r.evaluation_season,games:r.games}])).entries()].sort((a,b)=>a[1].season-b[1].season||a[0].localeCompare(b[0]));
 $('cohort-filter').innerHTML=cohorts.map(([hash,c])=>option(hash,`${c.season} · ${c.games} games · cohort ${hash.slice(0,12)}`)).join('');
 const families=[...new Set(registry.map(r=>r.family))].sort();$('family-filter').innerHTML=option('all','All retained families')+families.map(f=>option(f,pretty(f))).join('');
 const targets={winner:[['winner_accuracy','Accuracy ↑'],['winner_logloss','Log loss ↓'],['winner_brier','Brier ↓'],['winner_ece','ECE ↓'],['winner_mcc','MCC ↑'],['winner_roc_auc','ROC AUC ↑'],['winner_pr_auc','PR AUC ↑']],margin:[['margin_mae','MAE ↓'],['margin_rmse','RMSE ↓'],['margin_bias','Bias']],total:[['total_mae','MAE ↓'],['total_rmse','RMSE ↓'],['total_bias','Bias']],cover:[]};
 function renderRegistry(){const hash=$('cohort-filter').value,family=$('family-filter').value,target=$('target-filter').value,metric=target==='winner'?'winner_logloss':target+'_mae';let list=registry.filter(r=>r.cohort_sha256===hash&&(family==='all'||r.family===family));list.sort((a,b)=>(a[metric]??Infinity)-(b[metric]??Infinity)||a.model_id.localeCompare(b.model_id));state.registryPage=Math.max(0,Math.min(state.registryPage,Math.ceil(list.length/20)-1));const current=list.slice(state.registryPage*20,state.registryPage*20+20),cols=targets[target];$('registry-status').textContent=`${list.length} retained scorecards in this exact cohort. `+(target==='cover'?'Cover probability was not evaluated in this source.':'Ordered by '+(target==='winner'?'log loss':'MAE')+' within this cohort only. Unreported metrics do not receive zero values.');$('registry-head').innerHTML='<tr><th>Model identity</th><th>Family / release</th><th>Games</th>'+cols.map(([,title])=>'<th>'+title+'</th>').join('')+(target==='cover'?'<th>Cover likelihood</th>':'')+'</tr>';$('registry-rows').innerHTML=current.map(r=>`<tr><td>${esc(r.model_id)}</td><td>${esc(pretty(r.family))}${small(r.evidence_release)}</td><td>${r.games}</td>${cols.map(([k])=>'<td>'+(r[k]==null?'<span class="subtle">Not reported</span>':k==='winner_accuracy'?pct(r[k]):num(r[k],4))+'</td>').join('')}${target==='cover'?'<td>No qualified cover forecast or metric</td>':''}</tr>`).join('');$('registry-page').textContent=`${list.length?state.registryPage+1:0} / ${Math.ceil(list.length/20)}`;$('registry-prev').disabled=state.registryPage===0;$('registry-next').disabled=(state.registryPage+1)*20>=list.length;}
 ['cohort-filter','family-filter','target-filter'].forEach(id=>$(id).addEventListener('change',()=>{state.registryPage=0;renderRegistry();}));$('registry-prev').addEventListener('click',()=>{state.registryPage--;renderRegistry();});$('registry-next').addEventListener('click',()=>{state.registryPage++;renderRegistry();});
 renderGames();renderComparison();renderRegistry();
 window.FBSCompleteReview={filtered,reference,games};
})();
