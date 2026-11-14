'use strict';
// Real browser acceptance of the public projection; no private scientific work.
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE_DIR||'playwright');
const root=path.resolve(__dirname,'..'),site=path.join(root,'docs/fbs/v074');
const live=process.env.FBS_V074_LIVE_URL;
const base=live||'http://fbs-v074.test/';
const output=process.env.FBS_SCREENSHOTS;
const weighted=JSON.parse(fs.readFileSync(path.join(site,'data/season_skill.json'),'utf8'));
const skillText=n=>(Number(n)*100).toFixed(2)+'%';
let browser,checks=0; const check=(ok,msg)=>{assert.ok(ok,msg);checks++;};
(async()=>{
 browser=await chromium.launch({headless:true,args:['--no-sandbox']});
 const context=await browser.newContext(),errors=[],failed=[],httpErrors=[];
 if(!live)await context.route('http://fbs-v074.test/**',async route=>{
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
  check(await page.locator('#stat-fits').innerText()==='0','Review does not claim new owner fits');
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
  if(output){fs.mkdirSync(output,{recursive:true});await page.screenshot({path:path.join(output,`fbs-v074-${live?'live':'static'}-${width}.png`),fullPage:true});}
  await page.click('[data-tab="coverage"]');check(await page.locator('#provider-body tr').count()===12,'Every provider/target denominator');
  check((await page.locator('#provider-summary').innerText()).includes('0 / 10,656'),'No invented qualified provider cells');
  check((await page.locator('#phase-b').innerText()).includes('V11.1'),'Current research policy');
  await page.close();
 }
 check(errors.length===0,'No JavaScript errors');check(failed.length===0,'No failed assets');check(httpErrors.length===0,'No HTTP asset failures');
 const receipt={status:'PASS',checks,viewports:[1440,390],served_public_files:!live,live_url:live||null,source_snapshot:'2026-11-13T23:31:35Z',new_fits:0,errors,failed,httpErrors};
 if(output)fs.writeFileSync(path.join(output,`FBS_V074_${live?'LIVE':'STATIC'}_BROWSER_RECEIPT.json`),JSON.stringify(receipt,null,2));
 console.log(JSON.stringify(receipt));
})().catch(e=>{console.error(e);process.exitCode=1;}).finally(async()=>{if(browser)await browser.close();});
