'use strict';
const {verifyHostedHtml}=require('./n111_current/verified_hosted_html.cjs');
const assert=require('node:assert/strict'),crypto=require('node:crypto'),fs=require('node:fs'),path=require('node:path'),{pathToFileURL}=require('node:url');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE_DIR||'playwright');
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const native=fs.readFileSync(process.env.NFL_N113_LOCAL_PATH||path.join(__dirname,'n113_current','index.html'));
const encoded=native.toString().match(/<script id="n113data" type="application\/json">([\s\S]*?)<\/script>/)[1],data=JSON.parse(encoded);
const supplement=JSON.parse(native.toString().match(/<script id="n113Availability" type="application\/json">([\s\S]*?)<\/script>/)[1]);
const groups=supplement.fixtures.flatMap(g=>g.teams);assert.equal(supplement.fixtures.length,supplement.counts.fixtures);assert.equal(groups.reduce((n,x)=>n+x.listed,0),supplement.counts.reported_players);assert(groups.every(x=>Object.keys(x).every(k=>['team','listed','out','doubtful','questionable','no_designation','did_not_participate','limited','full'].includes(k))));assert(supplement.counts.missing_timed_reports>0);
const stable='https://sports-edge-lab-nfl.alv-mendizabal.chatgpt.site/circa/',live=process.env.NFL_N113_ONLINE_URL,url=live||pathToFileURL(process.env.NFL_N113_LOCAL_PATH||path.join(__dirname,'n113_current','index.html')).href;
const archive='270f6e4d7a1c26c6fa775e904ec410aa7dfca5cf97b24dfac64b4eb04382f0f9';
const stats={current:data.market.fixtures.length,historical:data.market.coverage.history.length};
assert.equal(data.release,'N113');assert.equal(data.scope,'public');assert.equal(stats.current,272);assert.equal(stats.historical,570);
assert.equal(new Set(data.market.fixtures.concat(data.market.coverage.history).map(g=>g.game)).size,842);
assert(!/id="n113private"|s3:\/\/|\/home\/sagemaker-user|AKIA[A-Z0-9]{16}/i.test(native.toString()));
const checkPrivacy=x=>{
 if(x&&typeof x==='object'){for(const key of ['contract_id','token_id','raw_response','source_sha256','model_version'])assert(!Object.hasOwn(x,key),'restricted public data field '+key);
 if(x.market_probability!=null)assert(x.public_price_allowed===true&&['The Odds API','SportsBookISH'].includes(x.supplier));
 Object.values(x).forEach(checkPrivacy);}
};checkPrivacy(data);
const law=data.models.laws.find(r=>data.prior.totals.some(t=>(t.game_id||t.game)===r.game&&t.total));assert(law);const tLaw=data.prior.totals.find(r=>(r.game_id||r.game)===law.game&&r.total).total;
const historicalRating=data.rating.laws.find(r=>String(r.season)==='2024');assert(historicalRating);
assert(data.rating.laws.some(r=>data.market.fixtures.some(g=>g.game===r.game&&g.status==='UPCOMING_TIMED')));
assert(data.models.champion_comparison.length&&data.rating.scores.length);
assert(data.market.pooled_panels.length&&data.market.pooled_weighted.length);
const recovered=data.market.fixtures.filter(g=>g.providers.Polymarket.recovered_historical_at_n113).length;
assert.equal(recovered,data.market.source_assessment.historical_new_games);
const selected=data.circa.next.find(r=>r.picks.length===5&&r.alternatives?.length>=10);assert(selected);
assert(data.models.scores.length&&data.models.paired.length&&data.common.rows.length&&data.market.panels.length);
async function request(u){return fetch(u,{credentials:'omit',redirect:'manual',headers:{'Cache-Control':'no-cache'},signal:AbortSignal.timeout(60000)});}
async function verifyRoutes(){
 const routes=[stable+'n113/',stable+'n112/',stable+'n111/',stable,stable+'publication.json',stable+'n113/private.html',stable+'n113/private_review.html'];
 const [release,prior,n111,current,manifest,...guard]=await Promise.all(routes.map(request));for(const r of [release,prior,n111,current,manifest])assert.equal(r.status,200);
 const m=await manifest.json();verifyHostedHtml(Buffer.from(await release.arrayBuffer()),sha(native),'n113');verifyHostedHtml(Buffer.from(await prior.arrayBuffer()),archive,'n112');verifyHostedHtml(Buffer.from(await n111.arrayBuffer()),'ad73527152d2c7998e54e1d95154b5080c7d28dc114634d5cded207b5a6238de','n111');
 const declared=m.assets['index.html'].sha256;verifyHostedHtml(Buffer.from(await current.arrayBuffer()),declared,'stable');assert.equal(m.assets[m.newest_review_path+'index.html'].sha256,declared);assert.equal(m.assets['n113/index.html'].sha256,sha(native));assert.equal(m.assets['n112/index.html'].sha256,archive);
 for(const r of guard)assert([403,404,410].includes(r.status),'Private dashboard served');
}
async function widthCheck(page,label,width){const v=await page.evaluate(()=>({width:innerWidth,scroll:document.documentElement.scrollWidth}));assert.equal(v.width,width);assert(v.scroll<=width+2,label+' overflow '+JSON.stringify(v));}
(async()=>{if(live)await verifyRoutes();const browser=await chromium.launch({args:['--no-sandbox','--disable-dev-shm-usage'],...(process.env.TEST_CHROMIUM_EXECUTABLE?{executablePath:process.env.TEST_CHROMIUM_EXECUTABLE}:{})});
 try{for(const width of [390,1440]){
 const page=await browser.newPage({viewport:{width,height:910},ignoreHTTPSErrors:true});const errors=[];page.on('pageerror',e=>errors.push(String(e)));
 await page.goto(url,{waitUntil:'domcontentloaded',timeout:60000});await page.waitForSelector('#leadersTable table');assert.equal(await page.title(),'Circa Million Picks & Performance Dashboard');assert.equal(sha(await page.locator('#n113data').textContent()),sha(encoded));await widthCheck(page,'Leaders',width);
 const go=async(button,selector)=>{await page.getByRole('button',{name:button,exact:true}).click();await page.waitForSelector(selector);await widthCheck(page,button,width);};
 await go('Games & venues','#caseRows button');assert.equal(await page.locator('#caseRows button').count(),272);await page.locator('#gameSeason').selectOption('2024');assert.equal(await page.locator('#caseRows button').count(),data.market.coverage.history.filter(g=>g.season===2024).length);
 await page.locator('#gameq').fill(historicalRating.game);assert.equal(await page.locator('#caseRows button').count(),1);await page.locator('#openExplorer').click();await page.waitForSelector('dialog[open] #lawNumbers strong');await page.locator('#closeDialog').click();await page.locator('#gameq').fill('');await page.locator('#gameSeason').selectOption('');assert.equal(await page.locator('#caseRows button').count(),842);await page.locator('#gameSeason').selectOption('2026');await page.locator('#status').selectOption('Kickoff TBD');assert.equal(await page.locator('#caseRows button').count(),data.market.fixtures.filter(r=>r.status==='UPCOMING_TBD').length);
 await page.locator('#status').selectOption('');await page.locator('#gameq').fill(law.game);assert.equal(await page.locator('#caseRows button').count(),1);await page.locator('#caseRows button').click();
 assert.equal(await page.locator('#gameHeading').innerText(),law.away+' at '+law.home);await page.locator('#openExplorer').click();await page.waitForSelector('dialog[open] #lawNumbers strong');
 const probs=async()=>(await page.locator('#lawNumbers .probgrid strong').allTextContents()).map(parseFloat);
 const measure=(law,pred)=>law.p.reduce((s,p,i)=>s+(pred(i+law.min)?p:0),0)*100;
 await page.locator('#lawFamily').selectOption(law.family);await page.locator('#direction').selectOption(law.home);await page.locator('#n').fill('11');await page.locator('#lo').fill('11');await page.locator('#hi').fill('11');await page.locator('#spread').fill('2.5');const p=await probs();
 for(const [i,value] of [[0,measure(law.margin,x=>x<0)],[3,measure(law.margin,x=>x===-11)],[4,measure(law.margin,x=>x<=-11)],[5,measure(law.margin,x=>x===-11)],[7,0]]) assert(Math.abs(p[i]-value)<0.0051,'Distribution readout differs');
 const tf=page.locator('#totalFamily');if(await tf.count())await tf.selectOption({label:'N112 archive · '+data.prior.totals.find(r=>(r.game_id||r.game)===law.game).family.replaceAll('_',' ')});await page.locator('#totalN').fill('41.5');const total=await page.locator('#totalResult').innerText();assert(total.includes('Over '+measure(tLaw,x=>x>41.5).toFixed(2)+'%')&&total.includes('Push 0.00%'));
 assert(await page.locator('dialog').evaluate(e=>e.scrollWidth<=e.clientWidth+2));await page.locator('#closeDialog').click();await page.locator('#venue').selectOption('Kalshi');assert.equal(await page.locator('.venue-card').count(),1);await widthCheck(page,'Game, single venue',width);
 await go('Upcoming forecasts','#upTable tbody tr');await page.locator('#upFamily').selectOption(data.rating.family);assert.equal(await page.locator('#upTable tbody tr').count(),data.market.fixtures.filter(r=>r.status!=='PLAYED').length);
 const issued=data.rating.laws.find(r=>r.issue_utc&&data.market.fixtures.some(g=>g.game===r.game&&g.status==='UPCOMING_TIMED'));if(issued){await page.locator('#upSearch').fill(issued.game);assert.equal(await page.locator('#upTable tbody tr').count(),1);assert((await page.locator('#upTable').innerText()).includes(issued.issue_utc));await page.locator('#upTable button').click();await page.waitForSelector('#gameHeading');assert.equal(await page.locator('#gameHeading').innerText(),issued.away+' at '+issued.home);}
 await go('Games & venues','#caseRows button');const reportGame=supplement.fixtures[0];await page.locator('#gameq').fill(reportGame.game);await page.locator('#caseRows button').click();assert((await page.locator('#gameAvailability').innerText()).includes(supplement.observed_utc));assert((await page.locator('#gameAvailability').innerText()).includes(reportGame.home));
 if(supplement.practice_study?.counts.original_issues>0){const narrow=supplement.practice_study.forecasts.find(r=>r.issue_utc);assert(narrow);await page.locator('#gameq').fill(narrow.game);await page.locator('#caseRows button').click();assert((await page.locator('#gameAvailability').innerText()).includes(narrow.issue_utc));}
 await go('Market comparisons','#marketTable');await page.locator('#marketVenue').selectOption('Polymarket');await page.locator('#marketScope').selectOption('Separate clock and custody groups');const late=data.market.panels.find(r=>r.provider==='Polymarket'&&String(r.checkpoint).startsWith('T5_'));if(late){await page.locator('#marketCheckpoint').selectOption(late.checkpoint);assert((await page.locator('#marketTable').innerText()).includes(late.checkpoint.replaceAll('_',' ')));}await page.locator('#marketScope').selectOption('Distinct matched games');await page.locator('#historyVenue').selectOption('Kalshi');await page.locator('#historyQuery').fill(data.market.coverage.history[0].game);assert.equal(await page.locator('#historyRows tbody tr').count(),1);
 await go('Model features','#modelAvailability');assert((await page.locator('#modelAvailability').innerText()).includes(supplement.counts.reported_players+' listed players'));await page.getByText('Reports by game and club',{exact:true}).click();assert.equal(await page.locator('#modelAvailability details').first().locator('tbody tr').count(),supplement.counts.teams);if(supplement.practice_study)assert((await page.locator('#modelAvailability').innerText()).includes('Practice-limitation margin study'));await go('Circa cards','#cardResults');await page.locator('#cardFamily').selectOption(selected.family);assert(await page.locator('#cardResults').innerText().then(t=>t.includes('Top five')&&t.includes('Alternative')));assert.deepEqual(errors,[]);
 console.log(JSON.stringify({public:live?'hosted':'repository',width,...stats,sha256:sha(native),page_errors:errors.length,validated:'signed margin, total, coverage, all views and all sides'}));await page.close();}
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
