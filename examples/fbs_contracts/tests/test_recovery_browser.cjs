'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE_DIR||'playwright');
const root=path.resolve(__dirname,'../../..');
const data=JSON.parse(fs.readFileSync(path.join(root,'docs/fbs/V025_OPERATIONAL_REVIEW_2026-11-03.json'),'utf8'));
let browser;
(async()=>{
 browser=await chromium.launch({headless:true});
 const context=await browser.newContext({acceptDownloads:true});const page=await context.newPage();
 const errors=[],requests=[];page.on('pageerror',e=>errors.push(e.message));
 page.on('request',r=>{if(!/^(file|data|blob):/.test(r.url()))requests.push(r.url());});
 let states=0;
 for(const width of [1440,390]){
  await page.setViewportSize({width,height:1000});await page.goto('file://'+path.join(root,'docs/fbs/recovery.html'));
  assert.equal(await page.locator('h1').count(),1);
  assert.match(await page.locator('.verdict').innerText(),/197 committed fits/);
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
  for(const [id,status] of [['false-success','REJECTED'],['certified-stop','CERTIFIED_WITH_SOLVER_STOP_RETAINED'],['infeasible','REJECTED']]){
   await page.locator(`[data-certificate="${id}"]`).click();
   assert.equal(await page.locator('#case-status').getAttribute('data-certificate-status'),status);
   assert.equal(await page.locator('[data-certificate][aria-pressed="true"]').count(),1);
   states++;
  }
  await page.locator('[data-certificate="certified-stop"]').focus();await page.keyboard.press('Enter');
  assert.equal(await page.locator('#solver-status').innerText(),'false');
  assert.match(await page.locator('#case-status').innerText(),/Certified/);
  assert.equal(await page.locator('.certificate-grid').evaluate(el=>el.scrollWidth>el.clientWidth),false);
  for(const value of ['all','1','2','3','4','5','6','7','8','9']){
   await page.selectOption('#week-filter',value);
   const expected=data.original_replay_2026.weekly.filter(r=>value==='all'||String(r.week)===value);
   assert.equal(await page.locator('#weekly-table tbody tr:visible').count(),expected.length);
   const rows=await page.locator('#weekly-table tbody tr:visible').evaluateAll(nodes=>nodes.map(node=>[...node.cells].map(cell=>cell.textContent)));
   rows.forEach((row,i)=>{assert.equal(row[1],String(expected[i].games));assert.equal(row[2],String(expected[i].correct_winner));assert.equal(row[4],expected[i].logloss.toFixed(6));});
   states++;
  }
  await page.locator('#week-filter').focus();await page.keyboard.press('ArrowUp');
  assert.equal(await page.locator('#week-filter').inputValue(),'8');
  await page.selectOption('#week-filter','all');
  const [download]=await Promise.all([page.waitForEvent('download'),page.locator('#weekly-csv').click()]);
  const csv=fs.readFileSync(await download.path(),'utf8');assert.equal(csv.trim().split('\n').length,10);
  assert.match(csv,/"margin_rmse"/);assert.equal(download.suggestedFilename(),'fbs-2026-replay-weeks.csv');
  assert.equal(await page.locator('#matched-table tbody tr').count(),4);
  assert.match(await page.locator('#matched-table').innerText(),/0.604359/);
  assert.match(await page.locator('#matched-table').innerText(),/0.553191/);
  assert.equal(await page.locator('#coverage table tbody tr').count(),3);
  assert.match(await page.locator('#coverage').innerText(),/54 \/ 62/);
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
  if(process.env.FBS_SCREENSHOTS){fs.mkdirSync(process.env.FBS_SCREENSHOTS,{recursive:true});
   await page.evaluate(()=>window.scrollTo({top:0,behavior:'instant'}));await page.screenshot({path:path.join(process.env.FBS_SCREENSHOTS,`recovery-${width}-top.png`)});
   await page.locator('#recovery').evaluate(el=>el.scrollIntoView({block:'start',behavior:'instant'}));await page.screenshot({path:path.join(process.env.FBS_SCREENSHOTS,`recovery-${width}-demo.png`)});}
 }
 const fallback=await browser.newContext({javaScriptEnabled:false,viewport:{width:390,height:1000}});const nojs=await fallback.newPage();
 await nojs.goto('file://'+path.join(root,'docs/fbs/recovery.html'));
 assert.equal(await nojs.locator('#weekly-table tbody tr').count(),9);assert.match(await nojs.locator('noscript').innerText(),/JavaScript is off/);
 assert.equal(await nojs.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
 assert.deepEqual(errors,[]);assert.deepEqual(requests,[]);
 console.log(JSON.stringify({status:'PASS',viewports:[1440,390],certificate_and_week_states:states,real_keyboard_actions:true,all_nine_week_csv:true,no_script_week_rows:9,script_errors:0,external_requests:0}));
})().catch(error=>{console.error(error);process.exitCode=1;}).finally(async()=>{if(browser)await browser.close();});
