'use strict';
const assert=require('node:assert/strict'),path=require('node:path'),fs=require('node:fs'),{pathToFileURL}=require('node:url'),{chromium}=require('playwright');
const dir=process.env.NFL_N126_PUBLIC_DIR||path.join(__dirname,'n126');
const source=fs.readFileSync(path.join(dir,'index.html'),'utf8');
const db=JSON.parse(require('node:zlib').gunzipSync(Buffer.from(source.match(/id="data">(.*?)<\/script>/s)[1],'base64')).toString());
const live='https://sports-edge-lab-nfl.alv-mendizabal.chatgpt.site/circa/n126/';
async function open(page,id){await page.locator('#'+id).evaluate(e=>{let p=e.parentElement;while(p){if(p.tagName==='DETAILS')p.open=true;p=p.parentElement;}});}
async function check(browser,url,width){
 const ctx=await browser.newContext({viewport:{width,height:900}}),page=await ctx.newPage(),errs=[];page.on('pageerror',e=>errs.push(String(e)));
 await page.goto(url,{waitUntil:'domcontentloaded',timeout:90000});
 assert.equal(await page.title(),'Circa Million Picks & Performance Dashboard');
 await page.waitForSelector('#leader tbody tr');assert.deepEqual(await page.locator('.calendars b').allTextContents(),['285','285','149']);
 assert.equal(await page.locator('#weight button').count(),5);assert.equal(await page.locator('#weight [aria-pressed=true]').getAttribute('data-weight'),'30/70');
 await page.selectOption('#objective','binary_accuracy');await page.selectOption('#clock','All models available two hours before kickoff');
 for(const w of ['50/50','40/60','30/70','20/80','10/90']){await page.locator('#weight button[data-weight="'+w+'"]').click();assert.match(await page.locator('#leader').innerText(),/\/148/);assert.ok(await page.locator('#sensitivity tbody tr').count()>=5);}
 await page.selectOption('#objective','margin_mae');await page.check('#precision');const rank=db.champs.find(r=>r.clock_group==='All models available two hours before kickoff'&&r.objective==='margin_mae'&&Number(r.weight_2024)===0.1);assert.ok((await page.locator('#leader').innerText()).includes(rank.test_2026));
 await page.locator('#circa-weight button[data-weight="50/50"]').click();assert.ok((await page.locator('#circa-leaders').innerText()).includes('N123'));
 await page.locator('#circa-weight button[data-weight="30/70"]').click();assert.ok((await page.locator('#circa-leaders').innerText()).includes('N124'));
 await page.waitForSelector('#card tbody tr');assert.equal(await page.locator('#card-policy option').count(),16);await page.selectOption('#card-policy','n126_card_calibrated_pool');await page.selectOption('#card-year','2025');await page.selectOption('#card-week','18');assert.equal(await page.locator('#card tbody tr').count(),5);assert.ok(await page.locator('#alternatives tbody tr').count()>=20);
 await page.selectOption('#move-year','2026');assert.ok(await page.locator('#move-coverage tbody tr').count()>=1);
 await page.selectOption('#venue-observation','t120');assert.match(await page.locator('#venue-count').innerText(),/719 games matched/);await page.selectOption('#venue-observation','archive');await page.selectOption('#venue-status','UPCOMING');assert.match(await page.locator('#venue-count').innerText(),/123 games matched/);await page.fill('#venue-query','2026_10_LAC_BAL');assert.equal(await page.locator('#venue-games tbody tr').count(),1);await page.selectOption('#venue-observation','current');assert.equal(await page.locator('#venue-games tbody tr').count(),1);
 const b=db.bench.find(r=>r.venue==='Kalshi'&&String(r.season)==='2026'&&Number(r.scored)>0);await page.selectOption('#venue-policy',b.policy);await page.selectOption('#venue',b.venue);await page.selectOption('#venue-target',b.product);await page.selectOption('#venue-model',b.model);assert.ok((await page.locator('#price-grades').innerText()).includes(b.scored+' / '+b.calendar_finals));
 assert.equal(await page.locator('#game option').count(),123);await page.selectOption('#game','2026_10_LAC_BAL');assert.ok(await page.locator('#forecasts tbody tr').count()>5);assert.equal(await page.locator('#objective-forward tbody tr').count(),19);await page.selectOption('#forecast-scope','current');assert.equal(await page.locator('#game option').count(),14);await page.selectOption('#forecast-scope','fixed');assert.equal(await page.locator('#game option').count(),123);
 await open(page,'law-n');await page.waitForSelector('#law-result tbody tr');await page.fill('#law-n','4.5');assert.match(await page.locator('#law-result').innerText(),/Exactly 4.5\s+0.000%/);
 assert.ok(!(await page.evaluate(()=>document.documentElement.scrollWidth>window.innerWidth+1)),'outer viewport overflow');assert.deepEqual(errs,[]);await ctx.close();
}
(async()=>{const browser=await chromium.launch();try{for(const url of [pathToFileURL(path.join(dir,'index.html')).href,live])for(const w of [390,1280])await check(browser,url,w);for(const m of source.matchAll(/href="(N126_[^"]+)"/g))assert.ok(fs.existsSync(path.join(dir,m[1])),m[1]);console.log('Verified all five validation weights, named-source eligibility, market and Circa panels, 123 upcoming fixtures and mobile width on both the repository page and signed-out live page.');}finally{await browser.close();}})().catch(e=>{console.error(e);process.exitCode=1;});
