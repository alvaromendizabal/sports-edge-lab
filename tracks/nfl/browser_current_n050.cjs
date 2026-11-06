'use strict';
const assert=require('node:assert/strict'),path=require('node:path'),fs=require('node:fs');
module.exports=async function checkCurrentReview(browser){
 const page=await browser.newPage(),errors=[],network=[];
 page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>{if(!r.url().startsWith('file:')&&!r.url().startsWith('data:')&&!r.url().startsWith('blob:'))network.push(r.url())});
 for(const width of [1440,390]){
  await page.setViewportSize({width,height:1000});await page.goto('file://'+path.join(__dirname,'review_n050.html'));
  assert.equal(await page.locator('#schedule tbody tr').count(),15);
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false,'current review overflow '+width);
  assert.equal(await page.locator('h1').count(),1);
  assert.match(await page.locator('#research').innerText(),/Zero N050 owner fits and zero N050 forecasts/);
  assert.match(await page.locator('#result-status').innerText(),/14 issued cards/);
  await page.locator('[data-open="2026_09_JAX_BAL"]').click();
  assert.match(await page.locator('#game-detail').innerText(),/No new N049 postgame issue/);
  assert.match(await page.locator('[data-game="2026_09_JAX_BAL"]').innerText(),/JAX 33 – BAL 10/);
  await page.locator('[data-open="2026_09_CIN_ATL"]').click();
  await page.locator('#exact-clocks summary').click();
  assert.match(await page.locator('#exact-clocks').innerText(),/2026-11-04T01:52:35/);
  assert.match(await page.locator('#exact-clocks').innerText(),/2026-11-06T05:57:29/);
  await page.selectOption('#stream','n049_shadow');assert.match(await page.locator('#result-status').innerText(),/14 issued cards/);
  await page.locator('#exact-clocks summary').click();assert.match(await page.locator('#exact-clocks').innerText(),/2026-11-06T05:58:14/);
  for(const stream of ['fresh_blocked','designation_blocked']){await page.selectOption('#stream',stream);assert.match(await page.locator('#result-status').innerText(),/0 issued cards/);assert.match(await page.locator('#game-detail').innerText(),/Blocked before new issue/)}
  await page.selectOption('#stream','n049_original');await page.selectOption('#week','10');assert.equal(await page.locator('#schedule tbody tr').count(),14);
  await page.selectOption('#week','all');assert.equal(await page.locator('#schedule tbody tr').count(),272);
  await page.locator('#search').fill('Week 8');assert.equal(await page.locator('#schedule tbody tr').count(),14);
  await page.locator('#search').fill('no-such-team');assert.equal(await page.locator('#schedule tbody tr').count(),0);assert.match(await page.locator('#game-detail').innerText(),/No matching games/);
  await page.locator('#search').fill('');await page.selectOption('#week','9');await page.locator('#week').focus();await page.keyboard.press('ArrowDown');assert.equal(await page.locator('#week').inputValue(),'10');
  assert.equal(await page.evaluate(()=>window.NFL_CURRENT_REVIEW.csvRows().length),429);
  assert.equal(await page.evaluate(()=>window.NFL_CURRENT_REVIEW.data.cards.length),56);
  assert.equal(await page.evaluate(()=>window.NFL_CURRENT_REVIEW.data.point_references.length),174);
  const [download]=await Promise.all([page.waitForEvent('download'),page.locator('#download-csv').click()]);
  const csv=fs.readFileSync(await download.path(),'utf8');assert.equal(csv.trim().split('\n').length,430);assert.match(csv,/provider_reference/);assert.match(csv,/issued_model/);
  const [jsonDownload]=await Promise.all([page.waitForEvent('download'),page.locator('#download-json').click()]);const decoded=JSON.parse(fs.readFileSync(await jsonDownload.path(),'utf8'));assert.equal(decoded.games.length,272);assert.equal(decoded.cards.length,56);
  if(process.env.NFL_SCREENSHOTS){fs.mkdirSync(process.env.NFL_SCREENSHOTS,{recursive:true});await page.evaluate(()=>window.scrollTo(0,0));await page.screenshot({path:path.join(process.env.NFL_SCREENSHOTS,'nfl-n050-current-'+width+'.png')});}
 }
 assert.deepEqual(errors,[]);assert.deepEqual(network,[]);await page.close();console.log('N049 actual / N050 readiness desktop, mobile, filters, clocks and complete downloads: PASS');
};
