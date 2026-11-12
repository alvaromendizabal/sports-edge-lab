'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const {pathToFileURL}=require('node:url');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE_DIR||'playwright');
const root=path.resolve(__dirname,'..');
const url=pathToFileURL(path.join(root,'docs/fbs/latest-games-v068.html')).href;
const recovered=JSON.parse(fs.readFileSync(path.join(root,'docs/fbs/recovered-original-v069.json'),'utf8'));
const latestAttempt=JSON.parse(fs.readFileSync(path.join(root,'docs/fbs/latest-attempt-v070.json'),'utf8'));
let browser;
(async()=>{
 browser=await chromium.launch({headless:true,...(process.env.FBS_BROWSER_EXECUTABLE?{executablePath:process.env.FBS_BROWSER_EXECUTABLE}:{})});
 const context=await browser.newContext({acceptDownloads:true});
 const page=await context.newPage();const errors=[],external=[];
 page.on('pageerror',e=>errors.push(e.message));
 page.on('request',r=>{if(!/^(file|blob|data):/.test(r.url()))external.push(r.url());});
 let assertions=0;
 const summary=async(n,p)=>{assert.equal(await page.locator('#game-summary').innerText(),`${n} of 888 source games shown · ${p} with retained probability · ${n-p} explicit gaps`);assertions++;};
 for(const width of [1440,390]){
  await page.setViewportSize({width,height:1000});await page.goto(url);await page.evaluate(async()=>{await window.FBS_LATEST_READY;});
  assert.match(await page.locator('#latest-attempt-outcome').innerText(),/V069 exited with code 2 before source refresh or model training/);
  assert.match(await page.locator('#latest-attempt-outcome').innerText(),/0 new model fits, 0 new forecast issues and 0 new prediction outputs/);
  assert.match(await page.locator('#latest-attempt-freshness').innerText(),/No November 12 forecast refresh is claimed/);
  assert.equal(await page.locator('nav a[href="#latest-attempt"]').count(),1);
  const providerRows=await page.locator('#latest-provider-cohorts tr').evaluateAll(rows=>rows.map(r=>({key:r.dataset.providerCohort,cells:[...r.cells].map(c=>c.textContent)})));
  const expectedProviders=latestAttempt.qualified_named_provider_cohorts.map(r=>({key:`${r.season}|${r.venue}`,cells:[`${r.season}`,r.venue,`${r.observed_games}`,`${r.observed_finals}`,...['winner','margin','total','cover_probability'].map(k=>`${r.qualified_games_by_target[k]}`)]}));
  assert.deepEqual(providerRows,expectedProviders);
  const [statusDownload]=await Promise.all([page.waitForEvent('download'),page.locator('#latest-attempt-download').click()]);
  assert.deepEqual(JSON.parse(fs.readFileSync(await statusDownload.path(),'utf8')),latestAttempt);
  if(process.env.FBS_SCREENSHOTS){fs.mkdirSync(process.env.FBS_SCREENSHOTS,{recursive:true});await page.locator('#latest-attempt').screenshot({path:path.join(process.env.FBS_SCREENSHOTS,`fbs-latest-attempt-v070-${width}.png`)});}
  await summary(146,146);assert.equal(await page.locator('#game-rows tr[data-game]').count(),30);
  assert.equal(await page.locator('#annual-rows tr').count(),21);
  assert.equal(await page.locator('#champion-rows td.gap').count(),9);
  assert.match(await page.locator('#execution').innerText(),/1 new fit, 146 genuine current forecast contexts and 739 scalar outputs/);
  assert.match(await page.locator('#execution').innerText(),/12-CPU project ceiling did not become 12 parallel fits/);
  assert.match(await page.locator('#continuation-status').innerText(),/pending owner execution/);
  assert.match(await page.locator('#recovered-original').innerText(),/356 distinct games out of 688 observed finals/);
  assert.match(await page.locator('#recovered-original').innerText(),/no combined prospective score/);
  await page.locator('#recovered-original-details summary').click();
  assert.equal(await page.locator('#recovered-original-rows tr').count(),55);
  const recoveredRows=await page.locator('#recovered-original-rows tr').evaluateAll(rows=>rows.map(row=>({id:row.dataset.recoveredGame,cells:[...row.cells].map(c=>c.textContent)})));
  const expectedRecovered=[...recovered.games].sort((a,b)=>a.kickoff_utc.localeCompare(b.kickoff_utc)||a.game_id.localeCompare(b.game_id)).map(row=>({id:row.game_id,cells:[`${row.away} at ${row.home}`,`${(row.home_probability*100).toFixed(4)}%`,row.kickoff_utc,row.original_issue_at_utc,row.original_input_cutoff_at_utc]}));
  assert.deepEqual(recoveredRows,expectedRecovered);
  const [recoveredDownload]=await Promise.all([page.waitForEvent('download'),page.locator('#recovered-original a[download]').click()]);
  assert.deepEqual(JSON.parse(fs.readFileSync(await recoveredDownload.path(),'utf8')),recovered);
  const recoveryLayout=await page.evaluate(()=>({viewport:innerWidth,width:document.documentElement.scrollWidth}));
  assert.ok(recoveryLayout.width<=width,`expanded recovery table overflow: ${JSON.stringify(recoveryLayout)}`);
  if(process.env.FBS_SCREENSHOTS){fs.mkdirSync(process.env.FBS_SCREENSHOTS,{recursive:true});await page.locator('#recovered-original').screenshot({path:path.join(process.env.FBS_SCREENSHOTS,`fbs-recovered-v069-${width}.png`)});}
  await page.locator('#recovered-original-details summary').click();
  await page.locator('#next').click();assert.equal(await page.locator('#page-status').innerText(),'Page 2 of 5');await page.locator('#previous').click();
  await page.locator('#game-rows button[data-detail]').first().focus();await page.keyboard.press('Enter');
  assert.equal(await page.locator('#game-detail').isVisible(),true);
  assert.equal(await page.locator('#detail-layer-rows tr').count(),7);
  assert.equal(await page.locator('#detail-provider-rows tr').count(),16);
  assert.match(await page.locator('#detail-content').innerText(),/V067 issued a new foundation outlook/);
  assert.match(await page.locator('#detail-content').innerText(),/no calibrated-coverage claim/);
  await page.keyboard.press('Escape');
  await page.selectOption('#period','missing_original');await summary(1,1);
  assert.match(await page.locator('#game-rows').innerText(),/Rutgers at Penn State/);
  assert.notEqual(await page.locator('#game-rows [data-value="probability"]').innerText(),'—');
  await page.selectOption('#layer','original');await summary(1,0);
  for(const target of ['probability','margin','total'])assert.equal(await page.locator(`#game-rows [data-value="${target}"]`).innerText(),'—');
  await page.selectOption('#period','refresh_gap');await summary(0,0);
  await page.selectOption('#period','all');
  for(const [layer,n] of [['current_v067',146],['original',148],['retained_v061',148],['calibrated',122],['mixture_global',114],['mixture_gated',114],['replay',790]]){
   await page.selectOption('#layer',layer);await summary(888,n);
  }
  await page.selectOption('#layer','current_v067');await page.selectOption('#period','upcoming');
  await summary(146,146);
  const [download]=await Promise.all([page.waitForEvent('download'),page.locator('#download-view').click()]);
  const text=fs.readFileSync(await download.path(),'utf8');assert.equal(text.split('\r\n').length,147);
  assert.match(text,/GENUINELY_FUTURE_ISSUED_ROLLING/);assert.match(text,/CURRENT_ORIGIN_SHADOW_ISSUED/);
  await page.selectOption('#period','tbd');await summary(54,0);
  await page.selectOption('#period','final');await summary(688,0);
  await page.selectOption('#period','upcoming');await page.locator('#search').fill('no-such-fixture-068');await summary(0,0);
  assert.equal(await page.locator('#download-view').isDisabled(),true);await page.locator('#search').fill('');
  if(process.env.FBS_SCREENSHOTS){fs.mkdirSync(process.env.FBS_SCREENSHOTS,{recursive:true});await page.screenshot({path:path.join(process.env.FBS_SCREENSHOTS,`fbs-latest-v068-${width}.png`),fullPage:true});}
  const layout=await page.evaluate(()=>({viewport:innerWidth,width:document.documentElement.scrollWidth,offenders:[...document.querySelectorAll('main,main>section,header,code,.filters,select')].map(e=>({tag:e.tagName,id:e.id,right:e.getBoundingClientRect().right,width:e.getBoundingClientRect().width})).filter(e=>e.right>innerWidth)}));
  assert.equal(layout.width>width,false,`overflow at ${width}: ${JSON.stringify(layout)}`);
 }
 assert.deepEqual(errors,[]);assert.deepEqual(external,[]);
 console.log(JSON.stringify({status:'PASS',viewports:[1440,390],selectorAssertions:assertions,errors,externalRequests:external.length}));
})().catch(e=>{console.error(e);process.exitCode=1;}).finally(async()=>{if(browser)await browser.close();});
