// Actual offline browser controls and reopen rendering of selected NFL outputs.
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE_DIR||'playwright');
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:process.env.NFL_BROWSER_EXECUTABLE||undefined});
 const source=JSON.parse(fs.readFileSync(path.join(__dirname,'selected_forecasts_n083.json'),'utf8'));
 const health=JSON.parse(fs.readFileSync(path.join(__dirname,'2026-11-13-n082-actual-n083-review.json'),'utf8'));
 let states=0;const errors=[],requests=[];
 try{
  const page=await browser.newPage({acceptDownloads:true});
  page.on('pageerror',e=>errors.push(e.message));
  page.on('request',r=>{if(!/^(file|data|blob):/.test(r.url()))requests.push(r.url());});
  for(const width of [1440,390]){
   await page.setViewportSize({width,height:1000});
   await page.goto('file://'+path.join(__dirname,'season_review_n083.html'));
   await page.locator('#games tr').first().waitFor();
   assert.equal(await page.locator('#games tr').count(),source.games.length);
   assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false,'outer-page overflow');
   assert.equal(await page.locator('h1').count(),1);
   const latest=await page.locator('#latest-attempt').innerText();
   assert.match(latest,/Real model work completed · N082/);
   assert.match(latest,/337 verified completed fits: 324 native \+ 13 meta/);
   assert.match(latest,/136 finals, 1 live, 111 confirmed future and 24 kickoff TBD/);
   assert.match(latest,/None beat the preserved best/);
   assert.match(latest,/2026-11-13T04:18:31\.686021\+00:00/);
   assert.match(latest,/November 12, 2026 at 20:18:31 Pacific \(PST\)/);
   assert.match(latest,/No new N083 owner result/);
   assert.equal(await page.locator('#latest-attempt').isVisible(),true);states++;

   assert.match(await page.locator('#owner-status').innerText(),/at least 337 verified fits \(324 native \/ 13 meta\)/);
   assert.match(await page.locator('#owner-status').innerText(),/444 rows for 111 games/);
   assert.equal(await page.locator('#early-scores tr').count(),9);
   assert.match(await page.locator('#former-leaders').innerText(),/Torch AB/);
   assert.match(await page.locator('#champions').innerText(),/scored \/ 136 completed games; frozen replay/);
   assert.match(await page.locator('#current-monitor').innerText(),/15 unique games/);states+=4;
   assert.equal(await page.locator('#latest-sources tr').count(),4);states++;
   assert.equal(await page.locator('#replay-leaders tr').count(),health.selected_2026_descriptive_leaders.length);
   for(let i=0;i<health.selected_2026_descriptive_leaders.length;i++){
    const r=health.selected_2026_descriptive_leaders[i],cells=await page.locator('#replay-leaders tr').nth(i).locator('td').allTextContents();
    const fmt=r.metric==='accuracy'?(100*r.value).toFixed(2)+'%':r.value.toFixed(['mae','rmse','crps'].includes(r.metric)?3:4);
    assert.deepEqual(cells,[r.target,r.metric,(r.comparison_horizon_seconds/60)+' min',r.model_aliases.join(' / '),fmt,r.games+' games; '+r.selected_candidates_compared+' selected candidates',r.cohort_sha256.slice(0,12)]);
   }states++;
   assert.equal(await page.locator('#former-roles tr').count(),18);states++;
   assert.equal(await page.locator('#replay-markets tr').count(),9);states++;
   assert.equal(await page.locator('#other-horizon-scores tr').count(),health.other_actual_horizon_scorecards.length);
   for(let i=0;i<health.other_actual_horizon_scorecards.length;i++){
    const r=health.other_actual_horizon_scorecards[i],cells=await page.locator('#other-horizon-scores tr').nth(i).locator('td').allTextContents();
    const fmt=m=>r.metrics[m]===undefined?'Unavailable':m==='accuracy'?(100*r.metrics[m]).toFixed(2)+'%':r.metrics[m].toFixed(['mae','rmse','crps'].includes(m)?3:4);
    assert.deepEqual(cells,[r.model_alias,r.target,r.comparison_horizon_seconds+' seconds',String(r.games),...['accuracy','log_loss','brier','mae','rmse'].map(fmt)]);
   }states++;

   assert.match(await page.locator('#coverage-note').innerText(),new RegExp(String(source.counts.games_with_any_preserved_evidence)));
   await page.selectOption('#status','tbd');
   assert.equal(await page.locator('#games tr').count(),source.counts.official_time_tbd_games);
   assert.doesNotMatch(await page.locator('#games').innerText(),/05:00:00 UTC/);
   states++;
   await page.selectOption('#status','completed');
   assert.equal(await page.locator('#games tr').count(),source.counts.completed_games);states++;
   await page.selectOption('#status','future');
   assert.equal(await page.locator('#games tr').count(),health.saved_census.confirmed_future);states++;
   await page.selectOption('#status','live');
   assert.equal(await page.locator('#games tr').count(),1);
   assert.match(await page.locator('#games').innerText(),/WAS at NYG/);
   assert.match(await page.locator('#games').innerText(),/LIVE · 0:48 - 4th Quarter/);states++;
   await page.selectOption('#status','');
   for(const group of ['current_forecasts','earlier_saved_forward','prior_selected_reconstruction']){
    await page.selectOption('#evidence-filter',group);
    const expected=source.games.filter(g=>Object.values(g.targets).some(t=>t[group].length)).length;
    assert.equal(await page.locator('#games tr').count(),expected,group);states++;
   }
   await page.selectOption('#evidence-filter','missing');
   assert.equal(await page.locator('#games tr').count(),source.counts.games_without_prediction_evidence_in_this_projection);states++;
   await page.selectOption('#evidence-filter','');
   await page.getByLabel('Team or game').fill('SEA');
   assert.equal(await page.locator('#games tr').count(),source.games.filter(g=>[g.home_team,g.away_team,g.game_id].join(' ').toLowerCase().includes('sea')).length);states++;
   await page.getByLabel('Team or game').fill('NO_MATCH_EXPECTED');assert.equal(await page.locator('#empty').isVisible(),true);states++;
   await page.getByLabel('Team or game').fill('');
   await page.locator('#week').focus();await page.keyboard.press('ArrowDown');
   const week=await page.locator('#week').inputValue();assert.notEqual(week,'');
   assert.equal(await page.locator('#games tr').count(),source.games.filter(g=>String(g.week)===week).length);states++;
   await page.selectOption('#week','');
   for(const group of ['primary','fallback','all']){
    await page.selectOption('#role-group',group);
    assert.equal(await page.locator('#champions tr').count(),source.selected_historical_roles.filter(r=>group==='all'||r.role_id.startsWith(group+'_')).length);states++;
   }
   await page.selectOption('#role-group','all');
   for(const horizon of ['3600']){
    await page.selectOption('#role-horizon',horizon);
    assert.equal(await page.locator('#champions tr').count(),source.selected_historical_roles.filter(r=>String(r.comparison_horizon_seconds)===horizon).length);states++;
   }
   await page.selectOption('#role-horizon','');
   for(let i=0;i<source.selected_historical_roles.length;i++){
    const role=source.selected_historical_roles[i],card=health.selected_2026_scorecards.find(c=>c.role_id===role.role_id);
    const cells=await page.locator('#champions tr').nth(i).locator('td').allTextContents();
    assert.equal(cells.length,8);assert.equal(cells[0],role.label);
    const v=card.metrics[role.metric],fmt=v===undefined?'Unavailable':role.metric==='accuracy'?(100*v).toFixed(2)+'%':v.toFixed(['mae','rmse','crps'].includes(role.metric)?3:4);
    assert.ok(cells[7].startsWith(fmt));assert.ok(cells[7].includes(card.games+' scored / 136 completed games'));
   }states++;
   assert.equal(await page.locator('#science-cards tr').count(),216);
   for(let i=0;i<health.new_science.cards.length;i++){
    const r=health.new_science.cards[i],cells=await page.locator('#science-cards tr').nth(i).locator('td').allTextContents();
    const fmt=m=>r.metrics[m]===undefined?'Unavailable':m==='accuracy'?(100*r.metrics[m]).toFixed(2)+'%':r.metrics[m].toFixed(['mae','rmse','crps'].includes(m)?3:4);
    assert.deepEqual(cells,[r.model_alias+' / '+r.family,r.season+' / '+r.target,r.comparison_horizon_seconds+'s / '+r.games,...['accuracy','log_loss','brier','mae','rmse','crps'].map(fmt),r.cohort_sha256.slice(0,12)]);
   }states++;
   for(const season of ['2024','2025'])for(const target of ['win','margin','total']){
    await page.selectOption('#science-season',season);await page.selectOption('#science-target',target);
    assert.equal(await page.locator('#science-cards tr').count(),36);states++;
   }
   await page.selectOption('#science-season','');await page.selectOption('#science-target','');
   for(const family of Object.keys(health.new_science.family_counts)){
    await page.selectOption('#science-family',family);assert.equal(await page.locator('#science-cards tr').count(),24);states++;
   }await page.selectOption('#science-family','');
   assert.equal(await page.locator('#new-vs-preserved tr').count(),9);states++;
   assert.equal(await page.locator('#all-current-cards tr').count(),77);
   for(let i=0;i<health.selected_and_retained_2026_scorecards.length;i++){
    const r=health.selected_and_retained_2026_scorecards[i],cells=await page.locator('#all-current-cards tr').nth(i).locator('td').allTextContents();
    const fmt=m=>r.metrics[m]===undefined?'Unavailable':m==='accuracy'?(100*r.metrics[m]).toFixed(2)+'%':r.metrics[m].toFixed(['mae','rmse','crps'].includes(m)?3:4);
    assert.deepEqual(cells,[r.model_alias,r.target+' / '+r.comparison_horizon_seconds+'s',String(r.games),...['accuracy','log_loss','brier','mae','rmse'].map(fmt),r.cohort_sha256.slice(0,12)]);
   }states++;
   assert.equal(await page.locator('#prior-roles tr').count(),27);states++;
   await page.selectOption('#role-group','primary');
   await page.selectOption('#status','future');
   const downloadPromise=page.waitForEvent('download');await page.locator('#download').click();
   const download=await downloadPromise;const exported=JSON.parse(fs.readFileSync(await download.path(),'utf8'));
   assert.equal(exported.games.length,health.saved_census.confirmed_future);assert.equal(exported.selection_filters.status,'future');states++;
   await page.reload();await page.locator('#games tr').first().waitFor();
   assert.equal(await page.locator('#games tr').count(),source.games.length);states++;
   if(process.env.NFL_SCREENSHOTS){fs.mkdirSync(process.env.NFL_SCREENSHOTS,{recursive:true});await page.screenshot({path:path.join(process.env.NFL_SCREENSHOTS,'nfl-selected-season-n083-'+width+'.png'),fullPage:true});}
  }
  assert.deepEqual(errors,[]);assert.deepEqual(requests,[]);
  console.log(JSON.stringify({status:'PASS',review:'N083 actual N082 completed science and incomplete owner acceptance',viewport_widths:[1440,390],states,all_games:source.games.length,console_errors:errors,external_requests:requests,reopen_render_verified:true}));
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
