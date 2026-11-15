const assert=require('node:assert/strict'), fs=require('node:fs'), path=require('node:path'), crypto=require('node:crypto');
const {pathToFileURL}=require('node:url');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE_DIR||'playwright');
const pagePath=process.env.NFL_N110_LOCAL_PATH||path.join(__dirname,'n110_current','index.html');
const native=fs.readFileSync(pagePath,'utf8');
const reData=/<script type="application\/json" id="n110data">([\s\S]*?)<\/script>/;
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const dataMatch=native.match(reData);
const trusted=JSON.parse(dataMatch[1]);
assert.equal(trusted.scope,'public');assert.equal(trusted.fixtures.length,272);
assert.equal(new Set(trusted.fixtures.map(f=>f.game)).size,272);assert.equal(trusted.privateMarkets,undefined);
assert.equal(Object.keys(trusted.recipes.arrays).length,0);assert(trusted.recipes.models.length>=1);
assert(!trusted.fixtures.some(game=>game.models.some(model=>Object.hasOwn(model,'privateLaw'))));
assert(!/s3:\/\/|private_review\.html|\/home\/sagemaker-user|AKIA[A-Z0-9]{16}/i.test(native));
for(const f of trusted.fixtures){assert.equal(Object.keys(f.venues).length,3);for(const v of Object.values(f.venues)){for(const o of v.observations||[]){if(o.price!=null)assert(o.price_permission===true);assert(!Object.hasOwn(o,'raw_legs'));}for(const o of v.comparisons||[]){if(o.market_probability!=null)assert(['The Odds API','SportsBookISH'].includes(o.supplier));}}}
const target=process.env.NFL_N110_ONLINE_URL||pathToFileURL(pagePath).href;
const launch=process.env.TEST_CHROMIUM_EXECUTABLE?{executablePath:process.env.TEST_CHROMIUM_EXECUTABLE}:{};launch.args=['--no-sandbox','--disable-dev-shm-usage'];
async function verifyAnonymousRoute(){
 const stable=new URL('../',target), headers={'User-Agent':'SportsEdgeLab publication readback N110','Cache-Control':'no-cache'};
 const urls=[target,stable,new URL('publication.json',stable),new URL('private_review.html',target)];
 const responses=await Promise.all(urls.map(url=>fetch(url,{headers,redirect:'manual',credentials:'omit',signal:AbortSignal.timeout(30000)})));
 assert.deepEqual(responses.slice(0,3).map(r=>r.status),[200,200,200]);assert([403,404,410].includes(responses[3].status));
 const html=await responses[0].text(),nav=await responses[1].text(),manifest=await responses[2].json();
 assert.equal(sha(html.match(reData)[1]),sha(dataMatch[1]));assert.equal(sha(nav.match(reData)[1]),sha(dataMatch[1]));
 assert.equal(manifest.newest_review_path,'n110/');assert.equal(manifest.assets['n110/index.html'].sha256,sha(native));
 console.log(JSON.stringify({verification:'anonymous_public_http',public:responses[0].status,stable:responses[1].status,private:responses[3].status,
  redirects:false,credentials:false,html_sha256:sha(html),native_sha256:sha(native),whole_page_identical:sha(html)===sha(native),embedded_sha256:sha(html.match(reData)[1])}));
}
(async()=>{if(process.env.NFL_N110_ONLINE_URL)await verifyAnonymousRoute();const browser=await chromium.launch(launch);for(const width of [1440,390]){
 const page=await browser.newPage({viewport:{width,height:900},ignoreHTTPSErrors:true});const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto(target,{waitUntil:'domcontentloaded',timeout:60000});await page.waitForSelector('#leaderRows');
 const embedded=await page.locator('#n110data').textContent();assert.equal(sha(embedded),sha(dataMatch[1]));
 assert.equal(await page.title(),'Circa Million Picks & Performance Dashboard');assert(await page.locator('#leaderRows table tbody tr').count()>0);
 if(trusted.calibration){await page.getByText('2026 calibration · market team shrink',{exact:true}).click();assert(await page.getByRole('heading',{name:'Point intervals'}).isVisible());}
 await page.getByRole('button',{name:'Games & venues',exact:true}).click();assert.equal(await page.locator('#caseRows button').count(),272);
 await page.locator('#status').selectOption('Kickoff TBD');const tbd=trusted.fixtures.filter(f=>f.status==='Kickoff TBD').length;assert.equal(await page.locator('#caseRows button').count(),tbd);
 await page.locator('#status').selectOption('');let g=trusted.fixtures.find(f=>f.status==='Scheduled')||trusted.fixtures[0];await page.locator('#gameq').fill(g.game);assert.equal(await page.locator('#caseRows button').count(),1);await page.locator('#caseRows button').click();assert.equal(await page.locator('#gameHeading').innerText(),g.away+' at '+g.home);
 await page.locator('#venue').selectOption('Kalshi');assert.equal(await page.locator('#caseDetail article').count(),1);
 await page.getByRole('button',{name:'Model features',exact:true}).click();assert.equal(await page.locator('#recipeList button').count(),trusted.recipes.models.length);
 await page.getByRole('button',{name:'Market comparisons',exact:true}).click();await page.locator('#marketq').fill('DraftKings');assert(await page.locator('#mk').isVisible());
 await page.getByRole('button',{name:'Circa cards',exact:true}).click();assert(await page.locator('#panel').innerText().then(t=>t.includes('deadline passed')));if(trusted.opening?.length)assert.equal(await page.locator('#openingBody tbody tr').count(),trusted.opening[0].sides.length);
 if(process.env.NFL_N110_ONLINE_URL){await page.goto(new URL('../',target).href,{waitUntil:'domcontentloaded'});await page.waitForSelector('#leaderRows');assert.equal(await page.title(),'Circa Million Picks & Performance Dashboard');await page.getByRole('button',{name:'Games & venues',exact:true}).click();assert.equal(await page.locator('#caseRows button').count(),272);}
 const layout=await page.evaluate(()=>({scroll:document.documentElement.scrollWidth,view:innerWidth}));assert(layout.scroll<=layout.view+2);assert.deepEqual(errors,[]);
 console.log(JSON.stringify({target:process.env.NFL_N110_ONLINE_URL?'deployed':'source',width,scope:'public',data_sha256:sha(embedded),html_sha256:sha(native),fixtures:trusted.fixtures.length,venue_slots:816,boards:trusted.boards.length,private_prices_disclosed:false,errors:errors.length,ready:true}));await page.close();
}await browser.close()})().catch(e=>{console.error(e);process.exit(1)});
