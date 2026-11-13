'use strict';
// Real browser acceptance of the public projection; no private scientific work.
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE_DIR||'playwright');
const root=path.resolve(__dirname,'..'),site=path.join(root,'docs/fbs/v073');
const live=process.env.FBS_V073_LIVE_URL;
const base=live||'http://fbs-v073.test/';
const output=process.env.FBS_SCREENSHOTS;
let browser,checks=0; const check=(ok,msg)=>{assert.ok(ok,msg);checks++;};
(async()=>{
 browser=await chromium.launch({headless:true,args:['--no-sandbox']});
 const context=await browser.newContext(),errors=[],failed=[];
 if(!live)await context.route('http://fbs-v073.test/**',async route=>{
   const pathname=decodeURIComponent(new URL(route.request().url()).pathname);
   const file=path.resolve(site,'.'+(pathname==='/'?'/index.html':pathname));
   if(!file.startsWith(site+path.sep)||!fs.existsSync(file))return route.fulfill({status:404,body:'Missing public asset'});
   const ext=path.extname(file),mime={'.html':'text/html','.css':'text/css','.js':'text/javascript','.json':'application/json'}[ext]||'application/octet-stream';
   return route.fulfill({status:200,contentType:mime,body:fs.readFileSync(file)});
 });
 for(const width of [1440,390]){
  const page=await context.newPage();await page.setViewportSize({width,height:1000});
  page.on('pageerror',e=>errors.push(e.message));page.on('requestfailed',r=>failed.push(r.url()));
  await page.goto(base,{waitUntil:'networkidle'});await page.waitForSelector('html[data-ready="true"]');
  check(await page.locator('#stat-games').innerText()==='2,742','All saved seasons');
  check(await page.locator('#stat-finals').innerText()==='691','Pinned current finals');
  check(await page.locator('#games-body tr').count()===20,'Paginated first load');
  check((await page.locator('#source-label').innerText()).includes('Nov 12, 2026'),'Source clock remains dated');
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
  await page.click('[data-tab="leaders"]');check((await page.locator('#cohort-info').innerText()).includes('687'),'Same-game winner denominator');
  await page.selectOption('#leader-metric','brier');check((await page.locator('#metric-guide').innerText()).includes('Brier score'),'Metric selector');
  check(await page.locator('#calibration-chart svg').count()===1,'Calibration chart');
  await page.selectOption('#leader-target','margin');check((await page.locator('#cohort-info').innerText()).includes('690'),'Same-game margin denominator');
  if(output){fs.mkdirSync(output,{recursive:true});await page.screenshot({path:path.join(output,`fbs-v073-${width}.png`),fullPage:true});}
  await page.click('[data-tab="coverage"]');check(await page.locator('#provider-body tr').count()===12,'Every provider/target denominator');
  check((await page.locator('#provider-summary').innerText()).includes('0 / 10,656'),'No invented qualified provider cells');
  check((await page.locator('#phase-b').innerText()).includes('Disabled'),'No automatic Phase B');
  await page.close();
 }
 check(errors.length===0,'No JavaScript errors');check(failed.length===0,'No failed assets');
 const receipt={status:'PASS',checks,viewports:[1440,390],served_public_files:!live,live_url:live||null,source_snapshot:'2026-11-12T21:04:00.155941Z',new_fits:0,errors,failed};
 if(output)fs.writeFileSync(path.join(output,'FBS_V073_BROWSER_RECEIPT.json'),JSON.stringify(receipt,null,2));
 console.log(JSON.stringify(receipt));
})().catch(e=>{console.error(e);process.exitCode=1;}).finally(async()=>{if(browser)await browser.close();});
