'use strict';
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const zlib = require('node:zlib');
const {pathToFileURL} = require('node:url');
const assert = require('node:assert/strict');
const {chromium} = require(process.env.PLAYWRIGHT_MODULE_DIR || 'playwright');
const {verifyHostedHtml} = require('./n111_current/verified_hosted_html.cjs');

const file = process.env.NFL_N120_LOCAL_PATH || path.join(__dirname, 'n120_current', 'index.html');
const stable = 'https://sports-edge-lab-nfl.alv-mendizabal.chatgpt.site/circa/';
const url = process.env.NFL_N120_ONLINE_URL;
const raw = fs.readFileSync(file);
const digest = b => crypto.createHash('sha256').update(b).digest('hex');
const html = raw.toString();
const pack = /<script id="n120data"[^>]*>([^<]+)<\/script>/.exec(html)[1];
const data = JSON.parse(zlib.gunzipSync(Buffer.from(pack,'base64')));
assert.equal(data.fixed.panel.digest,'0ff88bae5f4fe6d141ed3c5ef69037ea29a532acce1804bb1fc7297e3c2e83c2');
assert.deepEqual(data.fixed.panel.season_counts,{'2024':34,'2025':217,'2026':53});
assert.equal(new Set(data.markets.fixtures.map(x=>x.game)).size,272);
assert(data.fixed.eligibility.length>=45 && data.grades.length>0);
if(data.execution.location==='LOCAL_REPLAY')assert.equal(data.issues.length,0);
assert(!/<script[^>]*\bid="n(?:118private|118previous|119private|120owner)"/.test(html));
for(const r of data.cases){assert.equal(r.price,undefined);assert.equal(r.market_probability,undefined);}

async function online() {
 const get = s => fetch(stable+s, {redirect:'manual', credentials:'omit', signal:AbortSignal.timeout(90000)});
 const meta = await (await get('publication.json')).json();
 const hashes = {'n120/':digest(raw),'n119/':'956c16518e58bef00d2237b98f51cd7c4842cccdeeee093beed153ad9117108b','':meta.assets['index.html'].sha256};
 assert.equal(meta.assets['n120/index.html'].sha256, digest(raw));
 for(const [r,h] of Object.entries(hashes)){
   const response = await get(r);
   assert.equal(response.status,200);
   verifyHostedHtml(Buffer.from(await response.arrayBuffer()),h,r||'current');
 }
 for(const r of ['n120/private.html','n120/private_review.html']) assert([403,404,410].includes((await get(r)).status));
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
   await page.waitForSelector('#registry120 tr');
   assert.equal(await page.title(),'Circa Million Picks & Performance Dashboard');
   assert.equal(digest(await page.locator('#n120data').textContent()),digest(pack));
   if(url&&process.env.NFL_N120_SCREEN_DIR){fs.mkdirSync(process.env.NFL_N120_SCREEN_DIR,{recursive:true});await page.screenshot({path:path.join(process.env.NFL_N120_SCREEN_DIR,'n120-champions-'+width+'.png')});}
   for(const period of ['2024','2025','2026','50_35_15','equal','70_20_10']){
    await page.locator('#scope120').selectOption(period);
    for(const target of ['win','ats','margin','total']){
     await page.locator('#target120').selectOption(target);
     const metric=['win','ats'].includes(target)?'log_loss':'mae';
     await page.locator('#metric120').selectOption(metric);
     const rows=data.fixed.rows.filter(r=>r.scope===period&&r.target===target&&r.metric===metric);
     assert.equal(await page.locator('#board120 tbody tr').count(),rows.length);
     assert((await page.locator('#leaders120').innerText()).includes('Fixed panel by season'));
    }
   }
   await page.locator('#calendar120').selectOption('2024');
   assert.equal(await page.locator('#panelCases120 tbody tr').count(),34);
   await view('Games & venues','#caseRows button');
   for(const [season,n] of [['2024',285],['2025',285],['2026',272]]){
     await page.locator('#gameSeason').selectOption(season);
     assert.equal(await page.locator('#caseRows button').count(),n);
   }
   const cases=data.issues.slice(0,3);
   for(const r of cases){
     await page.locator('#caseRows button[data-game="'+r.game+'"]').click();
     const detail=await page.locator('#caseDetail').innerText();
     assert(detail.includes('N120 venue evidence')&&detail.includes(r.issue_utc));
     assert(!detail.includes('Private model and venue prices'));
   }
   await view('Market comparisons','#coverage120');
   for(const year of ['2024','2025','2026'])await page.locator('#season120v').selectOption(year);
   if(url&&process.env.NFL_N120_SCREEN_DIR)await page.screenshot({path:path.join(process.env.NFL_N120_SCREEN_DIR,'n120-markets-'+width+'.png')});
   await view('N120 margin study','#main section');
   await view('Upcoming forecasts','#upScope');
   await page.locator('#upScope').selectOption('N120');
   await view('Circa cards','#cardWeek');
   if(data.contest_cards.length)assert((await page.locator('#card120Details').innerText()).includes('Best five'));
   assert.deepEqual(errors,[]);
   console.log(JSON.stringify({width,hosted:!!url,public_sha256:digest(raw),fixtures:272,models:data.fixed.eligibility.length}));
   await page.close();
  }
 } finally {await browser.close();}
}
run().catch(e=>{console.error(e);process.exitCode=1;});
