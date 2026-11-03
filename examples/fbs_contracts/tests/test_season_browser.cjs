// CI browser verification of the actual rendered report, not synthetic owner fits.
'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE_DIR||'playwright');
const root=path.resolve(__dirname,'../../..');
const url='file://'+path.join(root,'docs/fbs/index.html');
let browser;
(async()=>{
 browser=await chromium.launch({headless:true});
 const context=await browser.newContext({acceptDownloads:true});
 const page=await context.newPage();const errors=[],requests=[];
 page.on('pageerror',e=>errors.push(e.message));
 page.on('request',r=>{if(!/^(file|data|blob):/.test(r.url()))requests.push(r.url());});
 let states=0;
 for(const width of [1440,390]){
  await page.setViewportSize({width,height:1000});await page.goto(url);
  assert.equal(await page.locator('h1').count(),1);
  assert.equal(await page.locator('#games-body tr').count(),25);
  assert.match(await page.locator('#result-status').innerText(),/^888 games/);
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
  for(const [view,count] of [['completed',622],['last',56],['current',63],['all',888]]){
   await page.locator(`[data-view="${view}"]`).click();
   assert.match(await page.locator('#result-status').innerText(),new RegExp(`^${count} games`));
   assert.equal(await page.locator('[data-view][aria-pressed="true"]').count(),1);states++;
  }
  for(const provider of ['DraftKings','Kalshi','Polymarket US','Polymarket Global']){
   await page.selectOption('#provider-select',provider);
   assert.match(await page.locator('#result-status').innerText(),/^888 games/);
   assert.equal(await page.locator('#market-column').innerText(),provider+' reference');states++;
  }
  await page.selectOption('#provider-select','DraftKings');
  await page.locator('#game-search').fill('TCU');
  assert.ok((await page.locator('#games-body').innerText()).includes('TCU'));
  const matching=await page.locator('#games-body tr').count();assert.ok(matching>0&&matching<25);
  await page.locator('#games-body button').first().focus();await page.keyboard.press('Enter');
  assert.equal(await page.locator('#game-dialog').isVisible(),true);
  assert.equal(await page.locator('#dialog-markets .market-detail').count(),4);
  assert.match(await page.locator('#dialog-footer').innerText(),/Decision: NO BET; stake \$0/);
  await page.keyboard.press('Escape');assert.equal(await page.locator('#game-dialog').isVisible(),false);
  await page.locator('#game-search').fill('');
  await page.locator('#view-disagreements').click();
  assert.match(await page.locator('#result-status').innerText(),/^40 games/);
  await page.locator('#next-page').click();assert.equal(await page.locator('#games-body tr').count(),15);
  const [download]=await Promise.all([page.waitForEvent('download'),page.locator('#export-csv').click()]);
  const csv=fs.readFileSync(await download.path(),'utf8');assert.equal(csv.trim().split('\n').length,41);
  assert.match(csv,/retrospective_original_replay/);assert.match(csv,/"not_issued"/);
  assert.doesNotMatch(csv,/s3:\/\/|api_key|raw_bid|model_weights/);
  await page.locator('#disagreements-only').uncheck();await page.locator('[data-view="current"]').click();
  await page.selectOption('#horizon-select','current');
  assert.match(await page.locator('#result-status').innerText(),/^63 games/);
  assert.match(await page.locator('#games-body').innerText(),/No recorded forecast/);
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
  if(process.env.FBS_SCREENSHOTS){fs.mkdirSync(process.env.FBS_SCREENSHOTS,{recursive:true});
   await page.evaluate(()=>window.scrollTo({top:0,behavior:'instant'}));
   await page.screenshot({path:path.join(process.env.FBS_SCREENSHOTS,`season-${width}-top.png`)});
   await page.locator('#game-explorer').evaluate(el=>el.scrollIntoView({block:'start',behavior:'instant'}));
   await page.screenshot({path:path.join(process.env.FBS_SCREENSHOTS,`season-${width}-games.png`)});}
 }
 const noScript=await browser.newContext({javaScriptEnabled:false,viewport:{width:390,height:1000}});
 const fallback=await noScript.newPage();await fallback.goto(url);
 assert.equal(await fallback.locator('#games-body tr').count(),888);
 assert.match(await fallback.locator('#games-body tr').first().innerText(),/PDT/);
 assert.match(await fallback.locator('noscript').innerText(),/JavaScript is off/);
 assert.equal(await fallback.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
 assert.deepEqual(errors,[]);assert.deepEqual(requests,[]);
 console.log(JSON.stringify({status:'PASS',viewports:[1440,390],inventory_provider_states:states,
   no_script_games:888,current_week:63,disagreement_csv_rows:40,keyboard_dialog:true,
   script_errors:0,external_requests:0}));
})().catch(error=>{console.error(error);process.exitCode=1;}).finally(async()=>{if(browser)await browser.close();});
