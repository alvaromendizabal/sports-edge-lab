'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const {pathToFileURL}=require('node:url');
const {chromium}=require('playwright');
const dir=process.env.NFL_N125_PUBLIC_DIR||path.join(__dirname,'n125');
const expected=JSON.parse(fs.readFileSync(path.join(dir,'index.html'),'utf8').match(/id="model-data">(.*?)<\/script>/s)[1]);
const local=pathToFileURL(path.join(dir,'index.html')).href;
const live='https://sports-edge-lab-nfl.alv-mendizabal.chatgpt.site/circa/n125/';
async function surface(browser,url,width){
 const context=await browser.newContext({viewport:{width,height:900}}), page=await context.newPage(),errors=[];
 page.on('pageerror',err=>errors.push(String(err)));
 await page.goto(url,{waitUntil:'domcontentloaded',timeout:90000});
 await page.waitForSelector('#leaders tbody tr',{timeout:20000});
 assert.equal(await page.title(),'Circa Million Picks & Performance Dashboard');
 assert.deepEqual(await page.locator('.calendars b').allTextContents(),['285','285','149']);
 await page.selectOption('#objective','margin_mae');
 await page.check('#full');
 const m=expected.leaders.find(r=>r.objective==='margin_mae');
 await page.selectOption('#clock',m.clock_group);
 assert.ok((await page.locator('#leaders').innerText()).includes(m.test_2026));
 await page.selectOption('#objective','binary_accuracy');
 assert.match(await page.locator('#leaders').innerText(),/\/148/);
 assert.ok(expected.leaders.every(r=>!(/draftkings|kalshi|polymarket/i.test(r.champion+' '+r.clock_group))));
 assert.equal(await page.locator('#game option').count(),123);
 await page.selectOption('#game','2026_10_LAC_BAL');
 assert.equal(await page.locator('#projection tbody tr').count(),new Set(expected.future.map(r=>r.recipe)).size);
 assert.equal(await page.locator('#legacy-fixed tbody tr').count(),7);assert.equal(await page.locator('#legacy-week tbody tr').count(),9);
 await page.selectOption('#future-clock','current');assert.equal(await page.locator('#game option').count(),14);assert.match(await page.locator('#future-note').innerText(),/hours before kickoff/);
 await page.selectOption('#future-clock','registered');
 await page.waitForSelector('#law-results tbody tr');
 await page.fill('#law-line','7.5');
 assert.match(await page.locator('#law-results').innerText(),/Exactly 7.5 \(push\)\s+0.000%/);
 await page.selectOption('#feature-year','2026');assert.ok(await page.locator('#feature-coverage tbody tr').count()>0);
 await page.locator('#source-query').evaluate(e=>e.closest('details').open=true);
 await page.fill('#source-query','2026_10_LAC_BAL');
 assert.ok((await page.locator('#source-summary').innerText()).includes('fixture/scope rows matched'));
 assert.ok(await page.locator('#source-fixtures tbody tr').count()>0);
 const v=expected.bench.find(r=>r.venue.toLowerCase().includes('kalshi')&&r.season==='2026'&&Number(r.scored)>0);
 await page.selectOption('#bench-policy',v.policy);await page.selectOption('#bench-venue',v.venue);await page.selectOption('#bench-product',v.product);await page.selectOption('#bench-model',v.model);assert.ok((await page.locator('#benchmark').innerText()).includes(v.scored+' / '+v.calendar_finals));
 await page.locator('#venue-query').evaluate(e=>e.closest('details').open=true);await page.selectOption('#venue-status','UPCOMING');assert.match(await page.locator('#venue-summary').innerText(),/123 games matched/);
 await page.fill('#venue-query','2026_10_LAC_BAL');assert.equal(await page.locator('#venue-fixtures tbody tr').count(),1);
 await page.waitForSelector('#card tbody tr');assert.equal(await page.locator('#card-policy option').count(),14);
 await page.selectOption('#card-policy','n124_raw_long');await page.selectOption('#card-year','2025');await page.selectOption('#card-week','18');assert.equal(await page.locator('#card tbody tr').count(),5);
 assert.ok(await page.locator('#alternatives tbody tr').count()>=20);
 assert.ok(!await page.evaluate(()=>document.documentElement.scrollWidth>window.innerWidth+1));
 assert.deepEqual(errors,[]);await context.close();
}
(async()=>{
 const opts=process.env.NFL_N125_CHROMIUM?{executablePath:process.env.NFL_N125_CHROMIUM}:{};const browser=await chromium.launch(opts);
 try{
  const urls=process.env.NFL_N125_LOCAL_ONLY?[local]:[local,live];
  for(const url of urls){for(const width of [390,1280]) await surface(browser,url,width);}
  for(const a of fs.readFileSync(path.join(dir,'index.html'),'utf8').matchAll(/href="(N125_[^"]+)"/g))assert.ok(fs.existsSync(path.join(dir,a[1])),a[1]);
  console.log('Passed '+urls.length+' source surfaces at 390 px and 1280 px, including standalone model eligibility, price comparisons, all cards and upcoming distributions.');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
