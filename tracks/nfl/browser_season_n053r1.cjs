'use strict';
const assert=require('node:assert/strict'),path=require('node:path'),fs=require('node:fs');
module.exports=async function checkFullSeason(browser){
 const page=await browser.newPage(),errors=[],network=[];
 page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>{if(!['file:','data:','blob:'].some(p=>r.url().startsWith(p)))network.push(r.url())});
 for(const width of [1440,390]){
  await page.setViewportSize({width,height:1000});await page.goto('file://'+path.join(__dirname,'season_review_n053r1.html'));await page.waitForFunction(()=>window.NFL_SEASON_REVIEW);
  assert.equal(await page.locator('#season-ledger tbody tr').count(),272);assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false,'Full season overflow '+width);
  assert.equal(await page.locator('h1').count(),1);assert.match(await page.locator('#coverage').innerText(),/122 completed games/);
  await page.selectOption('#scope','completed');assert.equal(await page.locator('#season-ledger tbody tr').count(),122);
  await page.selectOption('#scope','future');assert.equal(await page.locator('#season-ledger tbody tr').count(),150);
  await page.locator('[data-recent="2026_08_CHI_SEA"]').click();assert.match(await page.locator('#game-detail').innerText(),/CHI 34 – SEA 17/);assert.equal(await page.locator('#lane').inputValue(),'preserved_selected_actual_T1');
  await page.locator('#game-clocks summary').click();assert.match(await page.locator('#game-clocks').innerText(),/2026-11-02/);
  await page.locator('[data-recent="2026_09_JAX_BAL"]').click();assert.equal(await page.locator('#lane').inputValue(),'latest_resolved_fresh');assert.match(await page.locator('#game-detail').innerText(),/Home margin -23.0; total 43.0/);assert.match(await page.locator('#game-detail').innerText(),/Correct winner/);
  await page.locator('#all-game-models summary').click();assert((await page.locator('#all-game-models tbody tr').count())>=12);
  for(const h of ['T1','T2','LATEST_PREGAME','LATEST_OBSERVED','RETAINED_OBSERVED','RESTORED_T1','RESTORED_T2','RESTORED_LATEST_PREGAME']){await page.selectOption('#provider-horizon',h);assert.equal(await page.locator('#season-ledger tbody tr').count(),1)}
  await page.locator('#search').fill('');await page.selectOption('#scope','all');await page.selectOption('#provider-horizon','LATEST_PREGAME');
  for(const lane of ['selected_annual','selected_weekly','selected_event','n052_fresh','n052_designation']){await page.selectOption('#lane',lane);assert.equal(await page.locator('#season-ledger tbody tr').count(),272)}
  await page.locator('#search').fill('2026_09_CIN_ATL');await page.locator('#conditional-probabilities summary').click();assert.equal(await page.locator('#conditional-probabilities tbody tr').count(),4);await page.locator('#search').fill('');
  await page.selectOption('#scope','8');assert.equal(await page.locator('#season-ledger tbody tr').count(),14);await page.locator('#search').fill('no-such-team');assert.equal(await page.locator('#season-ledger tbody tr').count(),0);assert.match(await page.locator('#game-detail').innerText(),/No matching games/);
  await page.locator('#search').fill('');await page.locator('#scope').focus();await page.keyboard.press('ArrowDown');assert.equal(await page.locator('#scope').inputValue(),'9');
  const data=await page.evaluate(()=>({models:window.NFL_SEASON_REVIEW.data.model_rows.length,providers:window.NFL_SEASON_REVIEW.data.provider_rows.length,lanes:window.NFL_SEASON_REVIEW.data.lanes.length,horizons:window.NFL_SEASON_REVIEW.data.provider_horizons.length,export:window.NFL_SEASON_REVIEW.exportRows().length}));assert.equal(data.models,272*data.lanes*3);assert.equal(data.providers,272*9*data.horizons);
  const [download]=await Promise.all([page.waitForEvent('download'),page.locator('#download-season').click()]);const csv=fs.readFileSync(await download.path(),'utf8');assert.equal(csv.trim().split('\n').length,data.export+1);assert.match(csv,/2026_09_JAX_BAL/);assert.match(csv,/2026_08_CHI_SEA/);
  const [jsonDownload]=await Promise.all([page.waitForEvent('download'),page.locator('#download-json').click()]);const payload=JSON.parse(fs.readFileSync(await jsonDownload.path(),'utf8'));assert.equal(payload.games.length,272);assert.equal(payload.next.actual_owner_results,0);assert.equal(payload.new_owner_fits,0);
  assert.equal(await page.locator('#restored-metrics tbody tr').count(),11);const [restoredDownload]=await Promise.all([page.waitForEvent('download'),page.locator('#download-restored').click()]);assert.equal(fs.readFileSync(await restoredDownload.path(),'utf8').trim().split('\n').length,21);
  assert.doesNotMatch(await page.locator('body').innerText(),/\b(?:bets?|betting|wagers?|wagering|gambling|stakes?|profit|profits|EV)\b/i);
  if(process.env.NFL_SCREENSHOTS){fs.mkdirSync(process.env.NFL_SCREENSHOTS,{recursive:true});await page.selectOption('#scope','all');await page.selectOption('#lane','selected_event');await page.evaluate(()=>window.scrollTo(0,0));await page.screenshot({path:path.join(process.env.NFL_SCREENSHOTS,'nfl-n053r1-season-'+width+'.png')});}
 }
 assert.deepEqual(errors,[]);assert.deepEqual(network,[]);await page.close();console.log('Complete272-game season,122finals,versionedlanes,explicitproviderhorizons,realissueclocks,fullCSVandJSON,desktop/mobile: PASS');
};
