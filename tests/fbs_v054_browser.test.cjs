'use strict';
// Real browser checks for the new saved-result view; no model execution.
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE_DIR||'playwright');
const root=path.resolve(__dirname,'..'),url='file://'+path.join(root,'docs/fbs/current.html');
let browser;
(async()=>{
 browser=await chromium.launch({headless:true});
 const context=await browser.newContext({acceptDownloads:true}),page=await context.newPage(),errors=[],external=[];
 page.on('pageerror',e=>errors.push(e.message));
 page.on('request',r=>{if(!/^(file|data|blob):/.test(r.url()))external.push(r.url())});
 let layerStates=0;
 for(const width of [1440,390]){
  await page.setViewportSize({width,height:1000});await page.goto(url);
  await page.locator('#game-rows [data-game]').first().waitFor();
  assert.match(await page.locator('#game-summary').innerText(),/^67 source games/);
  assert.match(await page.locator('#execution-summary').innerText(),/3 base fits and 6 mixture fits/);
  assert.equal(await page.locator('#game-rows tr').count(),40);
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false,'page overflow at '+width);
  await page.locator('#next-page').click();assert.equal(await page.locator('#game-rows tr').count(),27);
  await page.locator('#previous-page').click();
  await page.selectOption('#period','all');
  for(const [layer,count] of [['original',122],['latest_foundation',122],['first_calibrated',122],['calibrated',122],['mixture_global',114],['mixture_gated',114],['historical',790]]){
   await page.selectOption('#layer',layer);
   assert.match(await page.locator('#game-summary').innerText(),new RegExp('888 source games shown · '+count+' with saved issue values'));layerStates++;
  }
  await page.selectOption('#season','all');assert.match(await page.locator('#game-summary').innerText(),/^2,742 source games|^2742 source games/);
  await page.selectOption('#season','2026');await page.selectOption('#period','tbd');
  assert.match(await page.locator('#game-summary').innerText(),/^81 source games/);
  await page.selectOption('#period','current_week');await page.selectOption('#layer','mixture_gated');
  await page.locator('#game-rows [data-game]').first().focus();await page.keyboard.press('Enter');
  assert.equal(await page.locator('#game-detail').isVisible(),true);
  assert.match(await page.locator('#detail-content').innerText(),/Saved issue context history/);
  assert.match(await page.locator('#detail-content').innerText(),/Polymarket Global/);
  await page.keyboard.press('Escape');assert.equal(await page.locator('#game-detail').isVisible(),false);
  const [download]=await Promise.all([page.waitForEvent('download'),page.locator('#download-csv').click()]);
  const csv=fs.readFileSync(await download.path(),'utf8');assert.equal(csv.split('\r\n').length,68);
  assert.match(csv,/"mixture_gated"/);assert.match(csv,/"issue_deadline_utc"/);
  await page.locator('#search').fill('not-a-real-team-000');assert.equal(await page.locator('#download-csv').isDisabled(),true);
  await page.locator('#search').fill('');
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
  if(process.env.FBS_SCREENSHOTS){fs.mkdirSync(process.env.FBS_SCREENSHOTS,{recursive:true});
   await page.screenshot({path:path.join(process.env.FBS_SCREENSHOTS,`fbs-current-v054-${width}.png`),fullPage:true});}
 }
 const noScript=await browser.newContext({javaScriptEnabled:false}),fallback=await noScript.newPage();await fallback.goto(url);
 assert.match(await fallback.locator('#execution').innerText(),/three base fits and six mixture fits/);
 assert.equal(await fallback.locator('#mixture-rows tr').count(),11);
 assert.match(await fallback.locator('noscript').innerText(),/every game/);
 await noScript.close();assert.deepEqual(errors,[]);assert.deepEqual(external,[]);
 console.log(JSON.stringify({status:'PASS',viewports:[1440,390],layerStates,currentWeekGames:67,allGames:2742,sourceGames2026:888,savedIssueGames:122,mixtureGames:114,keyboardDialog:true,csvRows:67,noScriptMetrics:11,scriptErrors:0,externalRequests:0}));
})().catch(error=>{console.error(error);process.exitCode=1}).finally(async()=>{if(browser)await browser.close()});
