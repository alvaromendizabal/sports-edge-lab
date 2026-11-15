'use strict';
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const zlib = require('node:zlib');
const {pathToFileURL} = require('node:url');
const assert = require('node:assert/strict');
const {chromium} = require(process.env.PLAYWRIGHT_MODULE_DIR || 'playwright');
const {verifyHostedHtml} = require('./n111_current/verified_hosted_html.cjs');

const file = process.env.NFL_N119_LOCAL_PATH || path.join(__dirname, 'n119_current', 'index.html');
const stable = 'https://sports-edge-lab-nfl.alv-mendizabal.chatgpt.site/circa/';
const url = process.env.NFL_N119_ONLINE_URL;
const raw = fs.readFileSync(file);
const digest = b => crypto.createHash('sha256').update(b).digest('hex');
const html = raw.toString();
const pack = /<script id="n119data"[^>]*>([^<]+)<\/script>/.exec(html)[1];
const data = JSON.parse(zlib.gunzipSync(Buffer.from(pack,'base64')));
assert(data.champions.length > 0 && data.leaders.length > 0);
assert.equal(new Set(data.markets.fixtures.map(x=>x.game)).size, 272);
assert(!/<script[^>]*\bid="n(?:118private|118previous|119private)"/.test(html));
for(const recipe of data.champions) for(const k of Object.keys(recipe))
  assert(['id','label','formal_status','availability','public_features','feature_count','targets','release','family_aliases'].includes(k));

async function online() {
 const get = s => fetch(stable+s, {redirect:'manual', credentials:'omit', signal:AbortSignal.timeout(90000)});
 const meta = await (await get('publication.json')).json();
 const hashes = {'n119/':digest(raw),'n118/':'920e68abe1327f1a628e2e0d9d707b01316266362f2ee98fe4c5f5b778a7abaf','':meta.assets['index.html'].sha256};
 assert.equal(meta.assets['n119/index.html'].sha256, digest(raw));
 for(const [r,h] of Object.entries(hashes)){
   const response = await get(r);
   assert.equal(response.status,200);
   verifyHostedHtml(Buffer.from(await response.arrayBuffer()),h,r||'current');
 }
 for(const r of ['n119/private.html','n119/private_review.html']) assert([403,404,410].includes((await get(r)).status));
}

async function run(){
 if(url) await online();
 const browser=await chromium.launch({args:['--no-sandbox','--disable-dev-shm-usage'], ...(process.env.TEST_CHROMIUM_EXECUTABLE?{executablePath:process.env.TEST_CHROMIUM_EXECUTABLE}:{})});
 try {
  for(const width of [390,1440]){
   const page=await browser.newPage({viewport:{width,height:900}});
   const errors=[];page.on('pageerror',e=>errors.push(e.message));
   const view=async (target,selector)=>{
    await page.getByRole('button',{name:target,exact:true}).click();
    await page.waitForSelector(selector);
    assert((await page.evaluate(()=>document.documentElement.scrollWidth-innerWidth))<=2, 'Overflow '+target);
   };
   await page.goto(url||pathToFileURL(file).href,{waitUntil:'domcontentloaded'});
   await page.waitForSelector('#registry119 tr');
   assert.equal(await page.title(),'Circa Million Picks & Performance Dashboard');
   assert.equal(digest(await page.locator('#n119data').textContent()),digest(pack));
   for(const season of ['2024','2025','2026','50_35_15']){
     await page.locator('#s119').selectOption(season);
     assert((await page.locator('#ranking119').innerText()).trim().length);
   }
   await view('Games & venues','#caseRows button');
   assert.equal(await page.locator('#caseRows button').count(),272);
   await page.locator('#gameSeason').selectOption('2024');
   assert.equal(await page.locator('#caseRows button').count(),285);
   await page.locator('#gameSeason').selectOption('2026');
   const actual = data.forecasts.laws || [];
   for(const id of new Set(actual.map(x=>x.game))){
     await page.locator('#caseRows button[data-game="'+id+'"]').click();
     const detail = await page.locator('#caseDetail').innerText();
     for(const item of actual.filter(x=>x.game===id)){
       assert(detail.includes(item.issue_utc));
       assert(detail.includes((item.expected_margin??item.expected_total??item.point).toFixed(2)));
     }
   }
   await page.locator('#caseRows button').last().click();
   assert((await page.locator('#caseDetail').innerText()).includes('N119 venue evidence'));
   await view('N119 market comparisons','#vs119');
   for(const season of ['2024','2025','2026']) await page.locator('#vs119').selectOption(season);
   if(data.markets.frontier_model_comparison){
     assert((await page.locator('#vSeason119').innerText()).includes('N119 signed-margin model'));
     assert((await page.locator('#main').innerText()).includes('Identical spread settlements across all three venues'));
   }
   await view('N119 margin study','#main section');
   await view('Upcoming forecasts','#upScope');
   await page.locator('#upScope').selectOption('N119');
   await view('Circa cards','#cardWeek');
   assert.deepEqual(errors,[]);
   console.log(JSON.stringify({width,hosted:!!url,public_sha256:digest(raw),fixtures:272,models:data.champions.length}));
   await page.close();
  }
 } finally {await browser.close();}
}
run().catch(e=>{console.error(e);process.exitCode=1;});
