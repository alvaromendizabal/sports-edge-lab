'use strict';
const assert=require('node:assert/strict'),crypto=require('node:crypto'),fs=require('node:fs'),path=require('node:path'),zlib=require('node:zlib');
const {pathToFileURL}=require('node:url');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE_DIR||'playwright');
const {verifyHostedHtml}=require('./n111_current/verified_hosted_html.cjs');
const sha=buf=>crypto.createHash('sha256').update(buf).digest('hex');
const local=process.env.NFL_N114_LOCAL_PATH||path.join(__dirname,'n114_current','index.html');
const native=fs.readFileSync(local),html=native.toString(),encoded=html.match(/<script id="n114data" type="application\/octet-stream" data-encoding="gzip-base64">([^<]+)<\/script>/)[1];
const data=JSON.parse(zlib.gunzipSync(Buffer.from(encoded,'base64')));
const stable='https://sports-edge-lab-nfl.alv-mendizabal.chatgpt.site/circa/';
const hosted=process.env.NFL_N114_ONLINE_URL,url=hosted||pathToFileURL(local).href;
const archive='3940754266378705988f9ea7eecb9ec96bb5e18b62e3a4e09fd828b37cc4076f';
const older='270f6e4d7a1c26c6fa775e904ec410aa7dfca5cf97b24dfac64b4eb04382f0f9';
const games=data.market.fixtures,past=data.market.coverage.history;
const types=['DraftKings','Kalshi','Polymarket'];
assert.equal(data.release,'N114');assert.equal(data.scope,'public');assert.equal(games.length,272);assert.equal(past.length,570);
assert.equal(new Set(games.concat(past).map(g=>g.game)).size,842);assert(games.concat(past).every(g=>types.every(v=>g.providers[v])));
assert(!html.includes('id="n114private"'));
function privacy(x){
 if(typeof x==='string'){assert(!/s3:\/\/|\/home\/sagemaker-user|AKIA[A-Z0-9]{16}/i.test(x));return;}
 if(!x||typeof x!=='object')return;
 for(const key of ['contract_id','token_id','raw_response','source_sha256','model_version'])assert(!Object.hasOwn(x,key),'Restricted public field '+key);
 if(x.market_probability!=null)assert(x.public_price_allowed===true&&['The Odds API','SportsBookISH'].includes(x.supplier));
 Object.values(x).forEach(privacy);
}
privacy(data);
const law=data.models.laws.find(r=>data.football.forecasts.some(t=>(t.game_id||t.game)===r.game&&t.total));assert(law);
const totalRow=data.football.forecasts.find(t=>(t.game_id||t.game)===law.game&&t.total);
const historical=data.prior.margin_laws.find(r=>String(r.game||r.game_id).startsWith('2024_'));assert(historical);
const timed=new Set(games.filter(g=>g.status==='UPCOMING_TIMED').map(g=>g.game));
const futureMargin=data.models.laws.find(r=>timed.has(r.game)&&r.issue_utc);
const futureTotal=data.football.forecasts.find(r=>timed.has(r.game||r.game_id)&&r.issue_utc);
assert(futureMargin&&futureTotal);assert(data.models.scores.length&&data.football.scores.length&&data.common.rows.length);
assert(data.market.pooled_panels.length&&data.market.reliability.length&&data.market.negative_checks.length);
const held=games.find(g=>Object.values(g.providers).some(p=>p.archived_projections?.length));assert(held);
const selected=data.circa.next.find(r=>r.picks.length===5&&r.alternatives?.length>=10);assert(selected);
const gid=r=>r.game||r.game_id;
async function request(u){return fetch(u,{credentials:'omit',redirect:'manual',headers:{'Cache-Control':'no-cache'},signal:AbortSignal.timeout(60000)});}
async function routes(){
 const urls=[stable+'n114/',stable+'n113/',stable+'n112/',stable,stable+'publication.json',stable+'n114/private.html',stable+'n114/private_review.html'];
 const [release,prior,n112,current,manifest,...guard]=await Promise.all(urls.map(request));for(const x of [release,prior,n112,current,manifest])assert.equal(x.status,200);
 const m=await manifest.json();verifyHostedHtml(Buffer.from(await release.arrayBuffer()),sha(native),'n114');verifyHostedHtml(Buffer.from(await prior.arrayBuffer()),archive,'n113');
 verifyHostedHtml(Buffer.from(await n112.arrayBuffer()),older,'n112');const declared=m.assets['index.html'].sha256;verifyHostedHtml(Buffer.from(await current.arrayBuffer()),declared,'stable');
 assert.equal(m.assets[m.newest_review_path+'index.html'].sha256,declared);assert.equal(m.assets['n114/index.html'].sha256,sha(native));assert.equal(m.assets['n113/index.html'].sha256,archive);
 for(const r of guard)assert([403,404,410].includes(r.status),'Private page available');
}
async function widthCheck(page,area,width){const x=await page.evaluate(()=>[innerWidth,document.documentElement.scrollWidth]);assert.equal(x[0],width);assert(x[1]<=width+2,area+' page overflow '+x);}
const probability=(law,pred)=>100*law.p.reduce((s,p,i)=>s+(pred(law.min+i)?p:0),0);
(async()=>{
 if(hosted)await routes();
 const browser=await chromium.launch({args:['--no-sandbox','--disable-dev-shm-usage'],...(process.env.TEST_CHROMIUM_EXECUTABLE?{executablePath:process.env.TEST_CHROMIUM_EXECUTABLE}:{})});
 try{for(const width of [390,1440]){
  const page=await browser.newPage({viewport:{width,height:910},ignoreHTTPSErrors:true}),errors=[];page.on('pageerror',err=>errors.push(String(err)));
  await page.goto(url,{waitUntil:'domcontentloaded',timeout:60000});await page.waitForSelector('#leadersTable table');assert.equal(await page.title(),'Circa Million Picks & Performance Dashboard');
  assert.equal(sha(await page.locator('#n114data').textContent()),sha(encoded));await widthCheck(page,'model leaders',width);
  const go=async(button,selector)=>{await page.getByRole('button',{name:button,exact:true}).click();await page.waitForSelector(selector);await widthCheck(page,button,width);};
  await go('Games & venues','#caseRows button');assert.equal(await page.locator('#caseRows button').count(),272);
  await page.locator('#gameSeason').selectOption('2024');assert.equal(await page.locator('#caseRows button').count(),285);await page.locator('#gameq').fill(gid(historical));
  assert.equal(await page.locator('#caseRows button').count(),1);await page.locator('#openExplorer').click();await page.waitForSelector('dialog[open] #lawNumbers strong');await page.locator('#closeDialog').click();
  await page.locator('#gameq').fill('');await page.locator('#gameSeason').selectOption('');assert.equal(await page.locator('#caseRows button').count(),842);
  await page.locator('#gameSeason').selectOption('2026');await page.locator('#status').selectOption('Kickoff TBD');assert.equal(await page.locator('#caseRows button').count(),games.filter(g=>g.status==='UPCOMING_TBD').length);
  await page.locator('#status').selectOption('');await page.locator('#gameq').fill(law.game);await page.locator('#openExplorer').click();await page.waitForSelector('dialog[open] #lawNumbers strong');
  await page.locator('#lawFamily').selectOption(law.family);await page.locator('#direction').selectOption(law.home);await page.locator('#n').fill('11');await page.locator('#lo').fill('11');await page.locator('#hi').fill('11');await page.locator('#spread').fill('2.5');
  const pp=(await page.locator('#lawNumbers .probgrid strong').allTextContents()).map(parseFloat);
  for(const [i,exp] of [[0,probability(law.margin,m=>m<0)],[3,probability(law.margin,m=>m===-11)],[4,probability(law.margin,m=>m<=-11)],[5,probability(law.margin,m=>m===-11)],[7,0]])assert(Math.abs(pp[i]-exp)<.0051,'Margin probability mismatch');
  await page.locator('#totalFamily').selectOption({label:'N114 · '+totalRow.family.replaceAll('_',' ')});await page.locator('#totalN').fill('41.5');const total=await page.locator('#totalResult').innerText();assert(total.includes('Over '+probability(totalRow.total,x=>x>41.5).toFixed(2)+'%')&&total.includes('Push 0.00%'));
  assert(await page.locator('dialog').evaluate(e=>e.scrollWidth<=e.clientWidth+2));await page.locator('#closeDialog').click();
  await page.locator('#gameq').fill(held.game);const venue=types.find(v=>held.providers[v].archived_projections?.length);await page.locator('#venue').selectOption(venue);assert.equal(await page.locator('.venue-card').count(),1);assert((await page.locator('.venue-card').innerText()).includes('earlier contract terms'));
  await go('Upcoming forecasts','#upTable tbody tr');await page.locator('#upFamily').selectOption(futureMargin.family);assert.equal(await page.locator('#upTable tbody tr').count(),games.filter(g=>g.status!=='PLAYED').length);
  await page.locator('#upFamily').selectOption(futureTotal.family);await page.locator('#upSearch').fill(gid(futureTotal));assert.equal(await page.locator('#upTable tbody tr').count(),1);const up=await page.locator('#upTable').innerText();assert(up.includes(futureTotal.issue_utc)&&up.includes(futureTotal.expected_total.toFixed(2)));
  await page.locator('#upTable button').click();await page.waitForSelector('#gameHeading');assert.equal(await page.locator('#gameHeading').innerText(),futureTotal.away+' at '+futureTotal.home);
  await go('Market comparisons','#marketTable');const same=page.locator('#identicalPayoff');assert.equal(await same.locator('tbody tr').count(),4);assert((await same.innerText()).includes('0.26683'));await same.locator('summary').click();assert((await same.innerText()).includes('0.75759'));await page.locator('#marketVenue').selectOption('Polymarket');await page.locator('#marketScope').selectOption('Separate clock and custody groups');
  const late=data.market.panels.find(r=>r.provider==='Polymarket'&&String(r.checkpoint).startsWith('T5_'));if(late){await page.locator('#marketCheckpoint').selectOption(late.checkpoint);assert((await page.locator('#marketTable').innerText()).includes(late.checkpoint.replaceAll('_',' ')));}
  await page.getByText('Probability reliability by venue',{exact:true}).click();await page.locator('#reliabilityCohort').selectOption({index:0});assert.equal(await page.locator('#reliabilityBins tbody tr').count(),data.market.reliability[0].bins.length);
  await page.locator('#historyVenue').selectOption('Kalshi');await page.locator('#historyQuery').fill(past[0].game);assert.equal(await page.locator('#historyRows tbody tr').count(),1);
  await go('Model features','#modelAvailability');assert((await page.locator('#modelAvailability').innerText()).includes(data.availability.counts.reported_players+' listed players'));
  await go('Circa cards','#cardResults');await page.locator('#cardFamily').selectOption(selected.family);const card=await page.locator('#cardResults').innerText();assert(card.includes('Top five')&&card.includes('Alternative'));assert.deepEqual(errors,[]);
  console.log(JSON.stringify({width,hosted:!!hosted,fixtures:games.length,earlierGames:past.length,sha256:sha(native),errors:errors.length,verified:'views, margin, total, issue clocks, market ages, venue bins, Circa alternatives'}));await page.close();
 }}finally{await browser.close();}
})().catch(err=>{console.error(err);process.exitCode=1;});
