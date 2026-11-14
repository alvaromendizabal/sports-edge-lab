'use strict';
// Real browser acceptance of the public projection; no private scientific work.
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE_DIR||'playwright');
const root=path.resolve(__dirname,'..'),site=path.join(root,'docs/fbs/v075');
const live=process.env.FBS_V075_LIVE_URL;
const base=live||'http://fbs-v075.test/';
const output=process.env.FBS_SCREENSHOTS;
const weighted=JSON.parse(fs.readFileSync(path.join(site,'data/season_skill.json'),'utf8'));
const skillText=n=>(Number(n)*100).toFixed(2)+'%';
let browser,checks=0; const check=(ok,msg)=>{assert.ok(ok,msg);checks++;};
(async()=>{
 browser=await chromium.launch({headless:true,args:['--no-sandbox']});
 const context=await browser.newContext(),errors=[],failed=[],httpErrors=[];
 if(!live)await context.route('http://fbs-v075.test/**',async route=>{
   const pathname=decodeURIComponent(new URL(route.request().url()).pathname);
   const file=path.resolve(site,'.'+(pathname==='/'?'/index.html':pathname));
   if(!file.startsWith(site+path.sep)||!fs.existsSync(file))return route.fulfill({status:404,body:'Missing public asset'});
   const ext=path.extname(file),mime={'.html':'text/html','.css':'text/css','.js':'text/javascript','.json':'application/json'}[ext]||'application/octet-stream';
   return route.fulfill({status:200,contentType:mime,body:fs.readFileSync(file)});
 });
 for(const width of [1440,390]){
  const page=await context.newPage();await page.setViewportSize({width,height:1000});
  page.on('pageerror',e=>errors.push(e.message));page.on('requestfailed',r=>failed.push(r.url()));
  page.on('response',r=>{if(r.status()>=400)httpErrors.push({url:r.url(),status:r.status()});});
  await page.goto(base,{waitUntil:'networkidle'});await page.waitForSelector('html[data-ready="true"]');
  check(await page.locator('#stat-games').innerText()==='2,742','All saved seasons');
  check(await page.locator('#stat-finals').innerText()==='693','Pinned current finals');
  check(await page.locator('#stat-fits').innerText()==='26','Actual verified V074 owner fits are reported');
  check((await page.locator('#issued-evidence').innerText()).includes('0 / 2 correct'),'Original-issued negative result remains visible');
  check(await page.locator('#games-body tr').count()===20,'Paginated first load');
  check((await page.locator('#source-label').innerText()).includes('Nov 13, 2026'),'Source clock remains dated');
  check(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'Responsive page width');
  const first=await page.locator('#games-body').innerText();await page.click('#game-next');
  check(first!==await page.locator('#games-body').innerText(),'Pagination changes actual games');
  await page.fill('#game-search','South Florida');check((await page.locator('#games-body').innerText()).includes('South Florida'),'Team search');
  await page.locator('[data-game]').first().click();await page.waitForSelector('#detail-body .clock-details');
  check(await page.locator('#game-dialog').isVisible(),'Lazy game detail opens');
  await page.locator('#detail-body summary').first().click();
  check(await page.locator('#detail-body details').first().evaluate(el=>el.open),'Original clocks expand');
  await page.selectOption('#detail-target','margin');check(await page.locator('#detail-body .number').count()>0,'Saved margin details');
  await page.keyboard.press('Escape');check(!await page.locator('#game-dialog').isVisible(),'Keyboard closes dialog');
  await page.fill('#game-search','');await page.selectOption('#game-timing','issued');
  check(!(await page.locator('#games-body').innerText()).includes('Later reconstruction'),'Issued filter excludes reconstruction');
  await page.selectOption('#game-timing','all');await page.selectOption('#game-season','2024');
  await page.waitForFunction(()=>document.querySelector('#game-count').textContent.includes('2024 season'));
  check((await page.locator('#game-count').innerText()).includes('920'),'2024 all-game census');
  await page.selectOption('#game-season','2025');await page.waitForFunction(()=>document.querySelector('#game-count').textContent.includes('2025 season'));
  check((await page.locator('#game-count').innerText()).includes('934'),'2025 all-game census');
  await page.click('[data-tab="leaders"]');check((await page.locator('#cohort-info').innerText()).includes('689'),'Same-game winner denominator');
  await page.selectOption('#leader-metric','brier');check((await page.locator('#metric-guide').innerText()).includes('Brier score'),'Metric selector');
  check(await page.locator('#calibration-chart svg').count()===1,'Calibration chart');
  await page.selectOption('#leader-target','margin');check((await page.locator('#cohort-info').innerText()).includes('692'),'Same-game margin denominator');
  await page.click('[data-tab="weighted"]');await page.waitForSelector('html[data-weighted-ready="true"]');
  for(const c of weighted.comparisons){
   await page.selectOption('#weighted-target',c.target);await page.selectOption('#weighted-window',c.window);
   for(const profile of weighted.profiles){
    await page.selectOption('#weighted-profile',profile.id);
    for(const metric of [...new Set(c.rows.map(r=>r.metric))]){
     await page.selectOption('#weighted-metric',metric);
     const expected=c.rows.filter(r=>r.metric===metric&&r.profile===profile.id).sort((a,b)=>(b.weighted_skill??-Infinity)-(a.weighted_skill??-Infinity)||a.family.localeCompare(b.family));
     check(await page.locator('#weighted-body tr').count()===expected.length,'Every weighted selector has the saved family rows');
     const firstRow=page.locator('#weighted-body tr').first();
     check((await firstRow.innerText()).includes(expected[0].family),'Weighted leader agrees with saved aggregate');
     check((await firstRow.locator('td').nth(1).innerText())===skillText(expected[0].weighted_skill),'Weighted value agrees with saved aggregate');
     check((await page.locator('#weighted-cohort').innerText()).includes('2026: '+c.seasons['2026'].n+' / '+c.seasons['2026'].window_final_denominator),'Weighted matched denominator remains visible');
    }
   }
  }
  check((await page.locator('#weighted-limits').innerText()).length>100,'Uncertainty and selection limitations remain visible');
  check(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'Weighted view remains responsive');
  if(output){fs.mkdirSync(output,{recursive:true});await page.screenshot({path:path.join(output,`fbs-v075-${live?'live':'static'}-${width}.png`),fullPage:true});}
  await page.click('[data-tab="refits"]');await page.waitForSelector('html[data-refit-ready="true"]');
  check((await page.locator('#owner-execution').innerText()).includes('26 completed model fits and 8 calibrator fits'),'Executed counts remain explicit');
  check((await page.locator('#refit-coverage').innerText()).includes('138 / 195'),'Complete pending denominator');
  check(await page.locator('#refit-body tr').count()===25,'Coverage rows are paginated');
  check((await page.locator('#refit-page').innerText()).includes('of 195'),'All pending fixtures kept');
  const before=await page.locator('#refit-body').innerText();await page.click('#refit-next');
  check(before!==await page.locator('#refit-body').innerText(),'Coverage paging changes games');
  await page.selectOption('#refit-status','prepared');check((await page.locator('#refit-page').innerText()).includes('of 138'),'Prepared coverage is 138 games');
  await page.selectOption('#refit-status','missing');check((await page.locator('#refit-page').innerText()).includes('of 57'),'All57missing games retained');
  await page.selectOption('#refit-status','issued');check((await page.locator('#refit-page').innerText())==='0 games','Prepared is never relabelled issued');
  await page.selectOption('#refit-status','all');await page.fill('#refit-search','South Florida');
  check((await page.locator('#refit-body').innerText()).includes('South Florida'),'Coverage team search');await page.fill('#refit-search','');
  await page.selectOption('#refit-family','Logistic regression');await page.selectOption('#refit-target','margin');await page.selectOption('#refit-status','prepared');
  check((await page.locator('#refit-page').innerText())==='0 games','Missing target is not filled from another model family');
  await page.selectOption('#refit-target','winner');check((await page.locator('#refit-page').innerText()).includes('of 138'),'Family and target filter exact prepared coverage');
  await page.selectOption('#refit-family','all');await page.selectOption('#refit-target','all');await page.selectOption('#refit-status','all');
  await page.fill('#refit-date','2026-11-14');check((await page.locator('#refit-page').innerText())!=='0 games','Pacific date filter');await page.fill('#refit-date','');
  check(await page.locator('#refit-body').innerText().then(t=>t.includes('Prepared values withheld')),'Prepared values visibly withheld');
  const downloadPromise=page.waitForEvent('download');await page.click('#refit-export');const download=await downloadPromise;
  const exported=fs.readFileSync(await download.path(),'utf8');
  check(exported.split('\n').length===196,'Coverage CSV retains195pendinggames');
  check(!exported.includes('prediction')&&!exported.includes('model_id'),'Coverage CSV doesnotexportvaluesorprivateidentities');
  check(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'Coverage view remains responsive');
  if(output){await page.screenshot({path:path.join(output,`fbs-v075-refits-${live?'live':'static'}-${width}.png`),fullPage:true});}
  await page.click('[data-tab="coverage"]');check(await page.locator('#provider-body tr').count()===12,'Every provider/target denominator');
  check((await page.locator('#provider-summary').innerText()).includes('0 / 10,656'),'No invented qualified provider cells');
  check((await page.locator('#phase-b').innerText()).includes('V11.1'),'Current research policy');
  await page.close();
 }
 check(errors.length===0,'No JavaScript errors');check(failed.length===0,'No failed assets');check(httpErrors.length===0,'No HTTP asset failures');
 const receipt={status:'PASS',checks,viewports:[1440,390],served_public_files:!live,live_url:live||null,source_snapshot:'2026-11-14T02:36:07Z',verified_owner_model_fits:26,verified_owner_calibrator_fits:8,new_fits_by_publication:0,errors,failed,httpErrors};
 if(output)fs.writeFileSync(path.join(output,`FBS_V075_${live?'LIVE':'STATIC'}_BROWSER_RECEIPT.json`),JSON.stringify(receipt,null,2));
 console.log(JSON.stringify(receipt));
})().catch(e=>{console.error(e);process.exitCode=1;}).finally(async()=>{if(browser)await browser.close();});
