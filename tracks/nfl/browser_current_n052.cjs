'use strict';
const assert=require('node:assert/strict'),path=require('node:path'),fs=require('node:fs');
module.exports=async function checkCurrentReview(browser){
 const page=await browser.newPage(),errors=[],network=[];
 page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>{if(!['file:','data:','blob:'].some(p=>r.url().startsWith(p)))network.push(r.url())});
 for(const width of [1440,390]){
  await page.setViewportSize({width,height:1000});await page.goto('file://'+path.join(__dirname,'review_n052.html'));
  assert.equal(await page.locator('#schedule tbody tr').count(),15);
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false,'N052 overflow '+width);
  assert.equal(await page.locator('h1').count(),1);assert.match(await page.locator('#research').innerText(),/Zero N052 owner fits and zero N052 forecasts/);
  assert.match(await page.locator('#study').innerText(),/higher loss/);assert.equal(await page.locator('#science-metrics tbody tr').count(),3);
  await page.selectOption('#science-period','2026');assert.match(await page.locator('#science-metrics').innerText(),/119/);
  await page.selectOption('#science-period','2025');assert.match(await page.locator('#science-metrics').innerText(),/285/);
  for(const lane of ['original','shadow','fresh','designation']){await page.selectOption('#stream','n051_'+lane);assert.match(await page.locator('#result-status').innerText(),/14 issued cards/);await page.locator('[data-open="2026_09_CIN_ATL"]').click();await page.locator('#exact-clocks summary').click();assert.match(await page.locator('#exact-clocks').innerText(),/2026-11-06/);await page.locator('#cover-detail summary').click();assert.equal(await page.locator('#cover-detail tbody tr').count(),4)}
  await page.locator('[data-open="2026_09_JAX_BAL"]').click();assert.match(await page.locator('#game-detail').innerText(),/No new N051 postgame issue/);
  await page.selectOption('#week','10');assert.equal(await page.locator('#schedule tbody tr').count(),14);await page.locator('[data-open="2026_10_SEA_LV"]').click();assert.match(await page.locator('#game-detail').innerText(),/Unavailable/);
  await page.selectOption('#week','all');assert.equal(await page.locator('#schedule tbody tr').count(),272);
  await page.locator('#search').fill('Week 8');assert.equal(await page.locator('#schedule tbody tr').count(),14);await page.locator('#search').fill('no-such-team');assert.equal(await page.locator('#schedule tbody tr').count(),0);assert.match(await page.locator('#game-detail').innerText(),/No matching games/);
  await page.locator('#search').fill('');await page.selectOption('#week','9');await page.locator('#week').focus();await page.keyboard.press('ArrowDown');assert.equal(await page.locator('#week').inputValue(),'10');
  assert.equal(await page.evaluate(()=>window.NFL_CURRENT_REVIEW.csvRows().length),679);assert.equal(await page.evaluate(()=>window.NFL_CURRENT_REVIEW.data.cards.length),112);
  const [csvDownload]=await Promise.all([page.waitForEvent('download'),page.locator('#download-csv').click()]);const csv=fs.readFileSync(await csvDownload.path(),'utf8');assert.equal(csv.trim().split('\n').length,680);assert.match(csv,/issued_cover_reference/);
  const [jsonDownload]=await Promise.all([page.waitForEvent('download'),page.locator('#download-json').click()]);const data=JSON.parse(fs.readFileSync(await jsonDownload.path(),'utf8'));assert.equal(data.new_total_issue_rows,418);assert.equal(data.science.paired_comparisons.length,864);assert.equal(data.next.owner_correction_fits,0);
  const [pairDownload]=await Promise.all([page.waitForEvent('download'),page.locator('#download-pairs').click()]);assert.equal(fs.readFileSync(await pairDownload.path(),'utf8').trim().split('\n').length,865);
  if(process.env.NFL_SCREENSHOTS){fs.mkdirSync(process.env.NFL_SCREENSHOTS,{recursive:true});await page.evaluate(()=>window.scrollTo(0,0));await page.screenshot({path:path.join(process.env.NFL_SCREENSHOTS,'nfl-n052-current-'+width+'.png')});}
 }
 assert.deepEqual(errors,[]);assert.deepEqual(network,[]);await page.close();console.log('N051 actual / N052 preparation desktop, mobile, four lanes, negative study, oriented cover, clocks and complete downloads: PASS');
};
