'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const {pathToFileURL}=require('node:url'),{gunzipSync}=require('node:zlib');

const dir=fs.existsSync(path.join(__dirname,'n123_current'))?path.join(__dirname,'n123_current'):path.join(__dirname,'public');
const html=fs.readFileSync(path.join(dir,'index.html'),'utf8');
const arr=JSON.parse(html.match(/<script type="application\/json" id="data123">(.*?)<\/script>/s)[1]);
const parseZip=(s,id)=>JSON.parse(gunzipSync(Buffer.from(s.match(new RegExp('<script[^>]* id="'+id+'"[^>]*>(.*?)</script>','s'))[1],'base64')));
const cards=parseZip(html,'card123'),exp=fs.readFileSync(path.join(dir,'N123_Probability_Explorer.html'),'utf8'),laws=parseZip(exp,'saved');
assert.equal(arr.games.length,842);assert.equal(new Set(arr.games.map(g=>g[0])).size,842);
const counts=[2024,2025,2026].map(y=>arr.games.filter(g=>g[1]===y&&g[2]==='FINAL').length);
assert.equal(counts[0],285);assert.equal(counts[1],285);
for(const item of arr.models)assert.deepEqual(item.y.map(y=>y.n),counts);
const direct=JSON.parse(html.match(/<script type="application\/json" id="livePM">(.*?)<\/script>/s)[1]);assert.equal(Object.values(direct).filter(x=>Number(x[2])>0).length,20);assert.equal(Number(direct['2026_10_LAC_BAL'][2]),52);
assert.equal(parseZip(html,'games123').issues['2026_10_LAC_BAL'].length,3);assert.equal(parseZip(html,'games123').venues['2026_10_LAC_BAL'].length,4);
assert.equal(Object.keys(cards).length,276);
for(const weekly of Object.values(cards)){
 const selected=weekly.filter(r=>r[3]>0);assert.equal(selected.length,5);assert.equal(new Set(selected.map(r=>r[0])).size,5);
 for(const row of weekly){const [cover,push,loss,points]=row[2];assert.ok(Math.abs(cover+push+loss-1)<2e-7);assert.ok(Math.abs(points-cover-.5*push)<2e-7)}
}
const future=arr.games.filter(g=>g[2].startsWith('UPCOMING'));
assert.equal(laws.length,3*future.length);
for(const r of laws){assert.ok(future.some(g=>g[0]===r[0]));assert.ok(Math.abs(r[7].reduce((a,b)=>a+b,0)-1)<1e-9);assert.ok(Math.abs(r[8].reduce((a,b)=>a+b,0)-1)<1e-9);}
for(const txt of [html,exp])assert.doesNotMatch(txt,/s3:\/\/|private-handoff|\/home\/sagemaker-user|x-amz-credential|"(?:bid_size|ask_size|contract_id|market_probability|api_key|rule_sha256)"\s*:/i);
for(const p of [...html.matchAll(/href="(N123_[^"#?]+)(?:#[^"]*)?"/g)].map(m=>m[1]))assert.ok(fs.statSync(path.join(dir,p)).size>0,p);
if(process.argv.includes('--verify-data')){console.log('N123 bundled data, probabilities, season coverage and privacy checks passed.');process.exit(0)}
(async()=>{const {chromium}=require('playwright');const browser=await chromium.launch();for(const size of [{width:1440,height:850},{width:390,height:844}]){
 const page=await browser.newPage({viewport:size});const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto(pathToFileURL(path.join(dir,'index.html')).href);await page.waitForFunction(()=>document.documentElement.dataset.ready==='1');
 assert.equal(await page.title(),'Circa Million Picks & Performance Dashboard');
 assert.match(await page.locator('#models').innerText(),/285\/285/);assert.match(await page.locator('#models').innerText(),/N110 plus opening-market fallback/);
 await page.selectOption('#metric','margin_mae');assert.match(await page.locator('#modelResults').innerText(),/N113/);
 await page.selectOption('#modelGroup','n123');assert.match(await page.locator('#modelResults').innerText(),/N123 key-margin/);
 await page.getByRole('link',{name:'Games & markets',exact:true}).click();await page.fill('#search','Baltimore');
 assert.match(await page.locator('#matching').innerText(),/matching games/);assert.match(await page.locator('#fixtures').innerText(),/Baltimore/);
 await page.locator('#fixtures tbody a').first().click();await page.waitForSelector('#fixtureDetail[data-ready]');assert.match(await page.locator('#fixtureDetail').innerText(),/Spread \/ threshold/);await page.selectOption('#status','UPCOMING_TIMED');await page.selectOption('#venue','6');assert.ok(await page.locator('#fixtures tbody tr').count()>0);
 await page.getByRole('link',{name:'Circa cards',exact:true}).click();await page.waitForFunction(()=>document.documentElement.dataset.cardsReady==='1');
 await page.selectOption('#cardPolicy','both_calibrated');await page.selectOption('#cardWeek','2026-10');assert.equal(await page.locator('#cardRows tbody tr').count(),cards['both_calibrated|2026-10'].length);assert.equal((await page.locator('#cardRows tbody tr td:first-child').allTextContents()).filter(x=>x!=='Alternative').length,5);
 await page.getByRole('link',{name:'Upcoming forecasts',exact:true}).click();await page.locator('#forecasts a[href^="N123_Probability_Explorer.html#"]').click();
 await page.waitForFunction(()=>document.documentElement.dataset.ready==='1');assert.equal(await page.locator('#game').inputValue(),'2026_10_LAC_BAL');assert.equal(await page.locator('#family option').count(),3);
 await page.selectOption('#family','team_and_published_qb');await page.selectOption('#side','home');assert.match(await page.locator('#win').innerText(),/55.7|55.8/);
 await page.fill('#spread','3.5');assert.match(await page.locator('#ats').innerText(),/Push\s+0\.00%/);
 assert.equal(errors.length,0,errors.join('\n'));await page.close();
}await browser.close();console.log('N123 desktop/mobile release checks passed.');})().catch(e=>{console.error(e);process.exit(1)});
