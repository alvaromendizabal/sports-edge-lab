// Real offline Chromium checks; no AWS, provider data requests or external assets.
'use strict';
const assert=require('node:assert/strict'),path=require('node:path'),fs=require('node:fs');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE_DIR||'playwright');
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:process.env.NFL_BROWSER_EXECUTABLE||undefined});
 try {
 const page=await browser.newPage(),errors=[],network=[];
 page.on('pageerror',e=>errors.push(e.message));
 page.on('request',r=>{if(!r.url().startsWith('file:')&&!r.url().startsWith('data:'))network.push(r.url());});
 const widths=[1440,390];let states=0;
 for(const width of widths){
  await page.setViewportSize({width,height:1000});await page.goto('file://'+path.join(__dirname,'review.html'));
  await page.locator('#results tbody tr').first().waitFor({state:'attached'});
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false,'page overflow at '+width);
  // Current evidence is separately dated; old 316-panel controls remain intact.
  assert.equal(await page.locator('h1').count(),1);
  for(const id of ['kalshi-horizon','current-year','current-target','disagreement-model','disagreement-result'])assert.equal(await page.locator('label[for="'+id+'"]').count(),1);
  assert.match(await page.locator('#current-headline').innerText(),/79/);
  assert.match(await page.locator('#current-comparison').innerText(),/119/);
  assert.match(await page.locator('#current-comparison').innerText(),/0\.644377/);
  await page.selectOption('#kalshi-horizon','T1');
  assert.match(await page.locator('#current-summary').innerText(),/not a same-horizon comparison/);
  assert.match(await page.locator('#current-comparison').innerText(),/0\.644579/);
  await page.selectOption('#kalshi-horizon','T2');
  assert.match(await page.locator('#current-comparison').innerText(),/0\.629080/);
  assert.equal(await page.locator('#current-provider-table tbody tr').count(),3);
  assert.match(await page.locator('#current-providers').innerText(),/incomplete/i);
  assert.match(await page.locator('#current-providers-heading').innerText(),/Archived provider coverage/);
  assert.equal(await page.locator('#current-providers').getAttribute('data-as-of'),'2026-11-03T21:24:00+00:00');
  assert.match(await page.locator('#archived-provider-notice').innerText(),/Superseded provider coverage/);
  assert.equal(await page.locator('#archived-provider-notice a').getAttribute('href'),'#latest-coverage');
  assert.match(await page.locator('#current-execution').innerText(),/Prior accepted N033 execution/);
  assert.match(await page.locator('#current-execution').innerText(),/That N033 execution added 192/);
  assert.doesNotMatch(await page.locator('#current-execution').innerText(),/This execution added/);
  assert.match(await page.locator('#current-snapshots').innerText(),/Week 8/);
  for(const year of ['2024','2025','2026']){
   await page.selectOption('#current-year',year);
   for(const target of ['winner','margin','total']){
    await page.selectOption('#current-target',target);
    assert.match(await page.locator('#current-selection').innerText(),new RegExp(year));
    assert((await page.locator('#current-season-table').innerText()).length>50,'current target has evidence or explicit missing state');
    states++;
   }
  }
  await page.selectOption('#current-target','winner');
  await page.selectOption('#disagreement-result','kalshi');
  assert((await page.locator('#disagreement-table tbody tr').count())>0,'lost disagreements stay visible');
  assert.equal(await page.locator('#disagreement-table [data-result="model"]').count(),0);
  await page.selectOption('#disagreement-result','model');
  assert((await page.locator('#disagreement-table [data-result="model"]').count())>0);
  assert.equal(await page.locator('#disagreement-table [data-result="kalshi"]').count(),0);
  await page.selectOption('#disagreement-result','all');
  await page.locator('#current-year').focus();await page.keyboard.press('ArrowDown');
  assert.equal(await page.locator('#current-year').inputValue(),'2025');
  await page.selectOption('#current-year','2026');
  await page.evaluate(()=>window.scrollTo(0,0));
  if(process.env.NFL_SCREENSHOTS){fs.mkdirSync(process.env.NFL_SCREENSHOTS,{recursive:true});await page.screenshot({path:path.join(process.env.NFL_SCREENSHOTS,'nfl-current-'+width+'.png')});}

  // N035 all-game evidence is separate from the retained N033 scorecard.
  for(const id of ['coverage-period','coverage-model','coverage-horizon','coverage-metric-season','coverage-metric-week','coverage-metric-model','coverage-metric-provider','coverage-metric-target','coverage-disagreement-result'])assert.equal(await page.locator('label[for="'+id+'"]').count(),1);
  assert.equal(await page.locator('#coverage-games [data-coverage-game]').count(),15);
  assert.equal(await page.locator('#coverage-horizon').inputValue(),'LATEST_OBSERVED');
  assert.match(await page.locator('#coverage-provider-counts').innerText(),/14 \/ 15/);
  assert.match(await page.locator('#coverage-provider-counts').innerText(),/11 \/ 15/);
  assert.match(await page.locator('#coverage-asof').innerText(),/FAILED/);
  assert.match(await page.locator('#coverage-clock-note').innerText(),/Reaching T2 is not a requirement/);
  await page.selectOption('#coverage-period','completed');
  assert.equal(await page.locator('#coverage-games [data-coverage-game]').count(),121);
  assert.equal(await page.locator('#coverage-horizon').inputValue(),'T2');
  assert.match(await page.locator('#coverage-provider-counts').innerText(),/121 \/ 121/);
  assert.match(await page.locator('#coverage-provider-counts').innerText(),/92 \/ 121/);
  await page.selectOption('#coverage-model','original_frozen');
  assert.equal(await page.locator('#coverage-games [data-coverage-game]').count(),121);
  assert.match(await page.locator('#coverage-count').innerText(),/0 with a selected model winner output/);
  await page.selectOption('#coverage-horizon','T1');
  assert.match(await page.locator('#coverage-clock-note').innerText(),/one hour before kickoff/);
  assert.match(await page.locator('#coverage-provider-counts').innerText(),/92 \/ 121/);
  await page.selectOption('#coverage-horizon','LATEST_PREGAME');
  assert.equal((await page.locator('#coverage-provider-counts').innerText()).match(/0 \/ 121/g).length,3);
  assert.match(await page.locator('#coverage-clock-note').innerText(),/never replaced silently with a T2 quote/);
  assert.match(await page.locator('#coverage-games').innerText(),/next runtime acquires it separately/);
  for(const week of ['1','2','3','4','5','6','7','8']){
   await page.selectOption('#coverage-period',week);
   assert.equal(await page.locator('#coverage-games [data-coverage-game]').count(),Number(week)<5?16:week==='5'?15:14);
   states++;
  }
  await page.selectOption('#coverage-period','all');
  assert.equal(await page.locator('#coverage-games [data-coverage-game]').count(),272);
  await page.selectOption('#coverage-period','9');
  await page.selectOption('#coverage-metric-provider','Polymarket');
  assert.match(await page.locator('#coverage-paired-table').innerText(),/0\.606083/);
  assert.match(await page.locator('#coverage-paired-table').innerText(),/0\.615317/);
  assert.match(await page.locator('#coverage-paired-count').innerText(),/exactly the same games/);
  await page.selectOption('#coverage-disagreement-result','provider');
  assert((await page.locator('#coverage-disagreements tbody tr').count())>0,'new provider losses remain visible');
  assert.match(await page.locator('#coverage-disagreement-count').innerText(),/below 60%/);
  await page.selectOption('#coverage-metric-target','total');
  assert.match(await page.locator('#coverage-paired-table').innerText(),/No equivalent authenticated comparison/);
  await page.selectOption('#coverage-metric-provider','DraftKings');
  assert.match(await page.locator('#coverage-paired-table').innerText(),/MAE/);
  await page.selectOption('#coverage-metric-target','win');
  await page.selectOption('#coverage-metric-provider','all');
  await page.selectOption('#coverage-disagreement-result','all');
  if(process.env.NFL_SCREENSHOTS){await page.locator('#latest-coverage').scrollIntoViewIfNeeded();await page.screenshot({path:path.join(process.env.NFL_SCREENSHOTS,'nfl-all-games-'+width+'.png')});}
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false,'new all-game view overflow at '+width);
  states+=19;

  assert.equal(await page.locator('#historical-archive').getAttribute('open'),null,'dated archive starts closed');
  for(const id of ['weekly-period','weekly-model','inventory-week','inventory-status'])assert.equal(await page.locator('label[for="'+id+'"]').count(),1);
  assert.equal(await page.locator('#weekly-game-cards [data-game]').count(),14);
  assert.match(await page.locator('#weekly-count').innerText(),/13 with winner probabilities/);
  assert.match(await page.locator('[data-game="2026_08_CHI_SEA"]').innerText(),/Separate genuine T−1h issue/);
  await page.selectOption('#weekly-model','original_frozen');
  assert.equal(await page.locator('#weekly-game-cards [data-game]').count(),14,'missing model coverage cannot drop games');
  assert.match(await page.locator('#weekly-count').innerText(),/0 with winner probabilities/);
  await page.selectOption('#weekly-model','selected_weekly');
  assert.match(await page.locator('#weekly-count').innerText(),/retrospective reconstruction/);
  await page.selectOption('#weekly-period','9');
  assert.equal(await page.locator('#weekly-model').inputValue(),'selected_latest_origin','future view uses historically selected series');
  assert.equal(await page.locator('#weekly-game-cards [data-game]').count(),15);
  assert.equal(await page.locator('#weekly-game-cards .no-bet').count(),15);
  assert.match(await page.locator('#weekly-count').innerText(),/DraftKings 14\/15/);
  assert.match(await page.locator('#weekly-policy').innerText(),/Full-pipeline promotion is false/);
  assert.match(await page.locator('[data-game="2026_09_JAX_BAL"]').innerText(),/JAX 67.8%/);
  assert.match(await page.locator('[data-game="2026_09_LV_SF"]').innerText(),/Unavailable/);
  await page.locator('[data-game="2026_09_JAX_BAL"] summary').click();
  assert.match(await page.locator('[data-game="2026_09_JAX_BAL"]').innerText(),/2026-11-03T21:20:14/);
  assert.equal(await page.locator('#inventory-table tbody tr').count(),272);
  await page.selectOption('#inventory-status','final');assert.equal(await page.locator('#inventory-table tbody tr').count(),121);
  await page.selectOption('#inventory-status','upcoming');assert.equal(await page.locator('#inventory-table tbody tr').count(),151);
  await page.selectOption('#inventory-week','9');assert.equal(await page.locator('#inventory-table tbody tr').count(),15);
  await page.selectOption('#inventory-status','final');assert.equal(await page.locator('#inventory-table tbody tr').count(),0,'no invented future results');
  await page.selectOption('#inventory-week','8');assert.equal(await page.locator('#inventory-table tbody tr').count(),14);
  if(process.env.NFL_SCREENSHOTS){await page.locator('#weekly-cards').scrollIntoViewIfNeeded();await page.screenshot({path:path.join(process.env.NFL_SCREENSHOTS,'nfl-weekly-'+width+'.png')});}
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false,'weekly view overflow at '+width);
  await page.selectOption('#weekly-model','all');assert.equal(await page.locator('#weekly-game-cards [data-game]').count(),15);
  await page.selectOption('#weekly-period','8');
  await page.selectOption('#inventory-status','all');await page.selectOption('#inventory-week','all');
  states+=18;
  await page.locator('#historical-archive>summary').click();
  assert.match(await page.locator('#legacy').innerText(),/316 panels/);
  assert.match(await page.locator('#coverage').innerText(),/280 \/ 285/);
  assert.match(await page.locator('#coverage').innerText(),/272 regular · 13 postseason/);
  for(const id of ['season','target','policy','metric','family','model','week-season','week-provider','time-scenario','time-decision'])assert.equal(await page.locator('label[for="'+id+'"]').count(),1);
  assert.equal(await page.locator('#weekly-results [data-week]').count(),22);
  assert.equal(await page.locator('#provider-summary tbody tr').count(),5);
  assert.match(await page.locator('#storage-evidence').innerText(),/14\.327 GiB/);
  assert.match(await page.locator('#storage-evidence').innerText(),/15,383,494,656 allocated bytes/);
  assert.match(await page.locator('#storage-evidence').innerText(),/0\.656 GiB/);
  assert.match(await page.locator('#storage-evidence').innerText(),/107\.962 GiB/);
  assert.match(await page.locator('#storage-evidence').innerText(),/global cleanup is not repeated/);
  assert.match(await page.locator('#storage-evidence').innerText(),/remaining budget are unknown/);
  assert.match(await page.locator('#storage-evidence').innerText(),/N011 and N012 owner execution are not verified/);
  assert.match(await page.locator('#time-detail [data-time-check="source_bound"]').innerText(),/Does not establish the earlier policy/);
  assert.match(await page.locator('#time-detail [data-time-check="model_availability"]').innerText(),/Not recorded \/ not inferred/);
  for(const scenario of ['origin_bound','complete','equal_boundary','late_input','late_fit','unknown_fit']){
   await page.selectOption('#time-scenario',scenario);
   for(const hours of ['1','48']){
    await page.selectOption('#time-decision',hours);
    const expected=scenario==='complete'&&hours==='1'?'DEMO_ADMISSIBLE':'NOT_ESTABLISHED_FOR_POLICY';
    assert.equal(await page.locator('#time-status [data-time-status]').getAttribute('data-time-status'),expected);
    assert.equal(await page.locator('#time-detail [data-time-check]').count(),4);
    if(scenario==='late_fit'&&hours==='1'){
     assert.match(await page.locator('#time-detail [data-time-check="inputs"]').innerText(),/Strictly before policy/);
     assert.match(await page.locator('#time-detail [data-time-check="model_availability"]').innerText(),/Model completed after policy/);
    }
    if(scenario==='origin_bound'&&hours==='1')assert.match(await page.locator('#time-status').innerText(),/No actual late input or label is established/);
    if(scenario==='late_input')assert.match(await page.locator('#time-status').innerText(),/recorded input or label is too late/);
    states++;
   }
  }
  await page.selectOption('#time-scenario','complete');await page.selectOption('#time-decision','1');
  await page.locator('#time-decision').focus();await page.keyboard.press('ArrowDown');
  assert.equal(await page.locator('#time-decision').inputValue(),'48');
  assert.match(await page.locator('#time-status').innerText(),/2025-10-31T18:00:00\+00:00/);states++;
  await page.selectOption('#time-scenario','origin_bound');await page.selectOption('#time-decision','1');
  await page.selectOption('#week-season','2026');
  assert.equal(await page.locator('#weekly-results [data-future="true"]').count(),4);
  assert.match(await page.locator('#weekly-results').innerText(),/6 expected by format; no captured matchups/);
  await page.selectOption('#week-provider','Kalshi');
  await page.locator('#provider-details summary').click();
  assert.equal(await page.locator('#provider-results [data-provider="Kalshi"]').count(),22);
  assert.match(await page.locator('#provider-results').innerText(),/Not verified \/ Not verified/);
  await page.selectOption('#week-season','all');
  assert.equal(await page.locator('#weekly-results [data-week]').count(),66);
  assert.equal(await page.locator('#provider-results [data-provider="Kalshi"]').count(),66);
  assert.match(await page.locator('#weekly-summary').innerText(),/330 provider\/week evidence states/);
  await page.selectOption('#week-season','2024');await page.selectOption('#week-provider','DraftKings');
  await page.locator('#provider-details summary').click();
  await page.selectOption('#season','2025');assert.match(await page.locator('#coverage').innerText(),/277 \/ 285/);
  await page.selectOption('#policy','fixed');await page.selectOption('#target','margin');
  assert.match(await page.locator('#results').innerText(),/MAE/);
  await page.locator('#metric').focus();await page.keyboard.press('ArrowDown');
  assert.equal(await page.locator('#metric').inputValue(),'rmse');
  await page.selectOption('#family','Constrained ensemble');
  assert((await page.locator('#results [data-model]').count())>0);
  const model=await page.locator('#model option').nth(1).getAttribute('value');
  await page.selectOption('#model',model);assert.equal(await page.locator('#results [data-model]').count(),1);
  await page.selectOption('#family','all');await page.selectOption('#season','2026');
  assert.match(await page.locator('#coverage').innerText(),/77 \/ 107/);
  assert.match(await page.locator('#coverage').innerText(),/165 unplayed/);
  assert.match(await page.locator('#result-boundary').innerText(),/EXPOSED MONITORING/);
  assert.equal(await page.locator('#results .best,#results [data-winner],#results .winner').count(),0);
  const ids=await page.locator('#results [data-model]').evaluateAll(nodes=>nodes.map(n=>n.dataset.model));
  assert.deepEqual(ids,[...ids].sort(),'monitoring stays in stable identifier order');
  await page.selectOption('#season','1999');
  assert.match(await page.locator('#results').innerText(),/No saved panel/);
  assert.match(await page.locator('#coverage').innerText(),/259 known game identities/);
  await page.selectOption('#season','2022');assert.match(await page.locator('#coverage').innerText(),/canceled game/);
  await page.selectOption('#season','2024');await page.selectOption('#target','win');await page.selectOption('#model','all');
  if(process.env.NFL_SCREENSHOTS){fs.mkdirSync(process.env.NFL_SCREENSHOTS,{recursive:true});await page.screenshot({path:path.join(process.env.NFL_SCREENSHOTS,'nfl-review-'+width+'.png'),fullPage:true});}
  states+=13;
 }
 assert.deepEqual(errors,[]);assert.deepEqual(network,[]);
 console.log(JSON.stringify({status:'PASS',viewports:widths,selection_scenarios:states,information_time_scenarios:24,keyboard_control:true,label_checks:38,external_requests:0,script_errors:0,monitoring_ranking:false,complete_week_slots:66,provider_week_states:330,weekly_games:29,schedule_inventory:272,active_providers:3,archived_providers_preserved:true}));
 } finally {
  await browser.close();
 }
})().catch(error=>{console.error(error);process.exitCode=1});
