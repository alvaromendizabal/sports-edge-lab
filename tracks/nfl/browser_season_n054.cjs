'use strict';
const assert=require('node:assert/strict'),path=require('node:path'),fs=require('node:fs');
module.exports=async function checkPublicSeason(browser){
 const page=await browser.newPage(),errors=[],network=[];
 page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>{if(!['file:','data:','blob:'].some(p=>r.url().startsWith(p)))network.push(r.url())});
 for(const width of [1440,390]){
  await page.setViewportSize({width,height:1000});await page.goto('file://'+path.join(__dirname,'season_review_n054.html'));await page.waitForFunction(()=>document.body.dataset.ready==='true');
  assert.equal(await page.locator('h1').count(),1);assert.match(await page.locator('h1').innerText(),/The full season/);
  await page.locator('[data-week="all"]').click();assert.equal(await page.locator('#game-table tbody tr').count(),272);
  await page.selectOption('#phase','STATUS_FINAL');assert.equal(await page.locator('#game-table tbody tr').count(),134);
  await page.selectOption('#phase','STATUS_IN_PROGRESS');assert.equal(await page.locator('#game-table tbody tr').count(),1);
  await page.selectOption('#phase','STATUS_HALFTIME');assert.equal(await page.locator('#game-table tbody tr').count(),0);
  await page.selectOption('#phase','STATUS_SCHEDULED');assert.equal(await page.locator('#game-table tbody tr').count(),137);
  await page.selectOption('#phase','all');await page.locator('#search').fill('Rams');assert.equal(await page.locator('#game-table tbody tr').count(),17);assert.doesNotMatch(await page.locator('#game-table').innerText(),/Chargers/);
  for(const code of ['CHI','LA','LAC']){await page.locator('#search').fill(code);assert.equal(await page.locator('#game-table tbody tr').count(),17);}
  for(const [id,score] of [['2026_08_CHI_SEA','CHI 34 – SEA 17'],['2026_09_JAX_BAL','JAX 33 – BAL 10'],['2026_09_CIN_ATL','CIN 34 – ATL 17']]){
   await page.locator('#search').fill(id);assert.equal(await page.locator('#game-table tbody tr').count(),1);await page.locator('[data-game="'+id+'"]').click();assert.match(await page.locator('#game-detail').innerText(),new RegExp(score));
   await page.locator('#source-detail summary').click();assert.equal(await page.locator('#source-detail tbody tr').count(),198);assert.match(await page.locator('#source-detail').innerText(),/DraftKings/);assert.match(await page.locator('#source-detail').innerText(),/Kalshi/);assert.match(await page.locator('#source-detail').innerText(),/Polymarket/);
  }
  const card=await page.evaluate(()=>window.nflPublicResearch.issued_cards[0]);await page.locator('#search').fill(card.game_id);await page.locator('[data-game="'+card.game_id+'"]').click();assert.match(await page.locator('#game-detail').innerText(),/Bounded actual current-origin issue/);assert.match(await page.locator('#game-detail').innerText(),/eligible earlier labels/);assert.match(await page.locator('#game-detail').innerText(),new RegExp((100*card.pick_probability).toFixed(1)+'%'));
  await page.locator('#search').fill('no-such-team');assert.equal(await page.locator('#game-table tbody tr').count(),0);assert.match(await page.locator('#game-detail').innerText(),/No matching game/);await page.locator('#search').fill('');
  await page.selectOption('#metric-season','all');await page.selectOption('#metric-target','all');assert.equal(await page.locator('#metric-table tbody tr').count(),1289);
  await page.selectOption('#metric-target','win');assert.equal(await page.locator('#metric-table tbody tr').count(),await page.evaluate(()=>window.nflPublicResearch.scoreboards.filter(r=>r.target==='win').length));
  await page.selectOption('#metric-season','2025');await page.selectOption('#metric-target','margin');assert((await page.locator('#metric-table tbody tr').count())>50);
  const [inventory]=await Promise.all([page.waitForEvent('download'),page.locator('#download-inventory').click()]);const body=fs.readFileSync(await inventory.path(),'utf8');assert.equal(body.trim().split('\n').length,273);assert.match(body,/2026_08_CHI_SEA/);assert.match(body,/2026_09_JAX_BAL/);
  const [metrics]=await Promise.all([page.waitForEvent('download'),page.locator('#download-metrics').click()]);assert.equal(fs.readFileSync(await metrics.path(),'utf8').trim().split('\n').length,1290);
  const data=await page.evaluate(()=>window.nflPublicResearch);assert.equal(data.public_scope.complete_candidate_predictions_included,false);assert.equal(data.issued_cards.length,8);assert.equal(data.model_rows,undefined);assert.equal(data.active_research_status.top_level_fit_total,null);assert.equal(data.rolling_policy.actual_new_V4_owner_fits,0);
  assert.equal(data.n060_owner_status.status,'FAILED_BEFORE_RESEARCH_STAGES');assert.equal(data.n061_owner_status.issue_rows,2294);assert.equal(data.n061_owner_status.monitor_evaluations,0);assert.equal(data.provider_capabilities.length,5);assert.equal(data.v5_scope.actual_new_fits,0);assert.equal(data.v5_scope.actual_new_forecasts,0);
  assert.equal(await page.locator('#v5-exposure-table tbody tr').count(),4);assert.equal(await page.locator('#v5-comparison-table tbody tr').count(),15);
  for(const t of ['win','margin','total']){await page.selectOption('#v5-target',t);assert.equal(await page.locator('#v5-comparison-table tbody tr').count(),5);assert.match(await page.locator('#v5-comparison-status').innerText(),/5 of 15/);assert.match(await page.locator('#v5-comparison-table').innerText(),/Awaiting owner execution/)}
  await page.selectOption('#v5-target','all');assert.equal(await page.locator('#v5-comparison-table tbody tr').count(),15);assert.match(await page.locator('#v5-state').innerText(),/Actual N060: partial/);assert.match(await page.locator('#v5-feature-counts').innerText(),/0 admitted, 0 evaluated, 0 promoted/);
  assert.doesNotMatch(JSON.stringify(data),/s3:\/\/|model_sha256|feature_columns|component_bindings|learning_rate|@gmail\.com/);
  assert.doesNotMatch(await page.locator('body').innerText(),/\b(?:bets?|betting|wagers?|wagering|bankroll|parlays?)\b/i);
  const overflow=await page.evaluate(()=>({width:innerWidth,scroll:document.documentElement.scrollWidth}));assert(overflow.scroll<=width+1,'Viewport overflow '+JSON.stringify(overflow));
  if(process.env.NFL_SCREENSHOTS){fs.mkdirSync(process.env.NFL_SCREENSHOTS,{recursive:true});await page.locator('[data-week="9"]').click();await page.evaluate(()=>window.scrollTo(0,0));await page.screenshot({path:path.join(process.env.NFL_SCREENSHOTS,'nfl-n061-'+width+'.png')});await page.locator('#v5-comparison').scrollIntoViewIfNeeded();await page.screenshot({path:path.join(process.env.NFL_SCREENSHOTS,'nfl-n061-rolling-'+width+'.png')});}
 }
 assert.deepEqual(errors,[]);assert.deepEqual(network,[]);await page.close();console.log('N061 actual partials, V5 exposure and public boundary, all272 games/32teams,22equal horizons,1289aggregates,datedcards,exports,mobile: PASS');
};
