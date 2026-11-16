'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const {pathToFileURL}=require('node:url');
const {gunzipSync}=require('node:zlib');
const {chromium}=require('playwright');
const directory=path.join(__dirname,'n122_current');
const html=fs.readFileSync(path.join(directory,'index.html'),'utf8');
const embedded=JSON.parse(gunzipSync(Buffer.from(html.match(/<script id="data122" type="text\/plain">(.*?)<\/script>/s)[1],'base64')));
const d=embedded;
assert.equal(d.games.length,842);assert.deepEqual(d.counts,[285,285,148]);assert.equal(d.nativeIssues.length,8);
assert.equal(d.contest.cards.length,322);assert.equal(d.contest.cards.reduce((a,c)=>a+c.rows.length,0),9716);
assert.equal(new Set(d.games.map(g=>g.id)).size,842);assert.equal(d.models.length,12);assert.equal(d.decisions.length,10);
assert.equal(d.forward.filter(r=>r.family.startsWith('n122_')&&r.margin!=null).length,369);
for(const m of d.models)assert.deepEqual(m.annual.map(r=>r.n),d.counts);
for(const c of d.contest.cards){assert.equal(new Set(c.rows.slice(0,5).map(r=>r[1])).size,5);assert.ok(c.rows.slice(5).every(r=>r[0]==='Alternative'));}
for(const [name] of d.files)assert.ok(fs.statSync(path.join(directory,name)).size>0,name);
assert.doesNotMatch(JSON.stringify(d),/s3:\/\/|\/home\/sagemaker-user|private-handoff|x-amz-credential|"(?:bid|ask|market_probability|rule_sha256|contract_id|bid_size|ask_size)"\s*:/i);
(async()=>{const browser=await chromium.launch();for(const viewport of [{width:1440,height:850},{width:390,height:844}]){
 const page=await browser.newPage({viewport});const errors=[];page.on('pageerror',e=>errors.push(e.message));await page.goto(pathToFileURL(path.join(directory,'index.html')).href);await page.waitForFunction(()=>document.documentElement.dataset.ready==='1');
 assert.match(await page.locator('main').innerText(),/N122 league and home/);await page.selectOption('#metric','margin_mae');assert.match(await page.locator('#modelRows tbody tr').first().innerText(),/N113/);await page.selectOption('#protocol','rolling');assert.equal(await page.locator('#modelRows tbody tr').count(),48);
 await page.getByRole('link',{name:'Games & markets',exact:true}).first().click();await page.waitForSelector('#gameRows');await page.selectOption('#status','live');assert.match(await page.locator('#gameRows').innerText(),/PIT at CIN/);await page.locator('#gameRows a').click();await page.waitForSelector('main h2');await page.waitForFunction(()=>document.querySelector('main').textContent.includes('Pittsburgh Steelers'));assert.match(await page.locator('main').innerText(),/Pregame issue journals/);
 await page.getByRole('link',{name:'Upcoming forecasts',exact:true}).click();await page.waitForSelector('#fRows');assert.equal(await page.locator('#fRows tbody a').count(),123);
 await page.getByRole('link',{name:'Circa cards',exact:true}).click();await page.waitForSelector('#cweek');assert.equal(await page.locator('#cweek option').count(),46);assert.ok(await page.locator('#card tbody tr').count()>=10);
 await page.getByRole('link',{name:'Evidence',exact:true}).click();await page.waitForSelector('.downloads');assert.equal(await page.locator('.downloads a').count(),d.files.length);
 assert.deepEqual(errors,[]);assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));
 await page.close();
}await browser.close();console.log('Verified full populations, forecasts, roster, source boundaries, 322 cards, accessible navigation, mobile and desktop.');})().catch(e=>{console.error(e);process.exit(1)});
