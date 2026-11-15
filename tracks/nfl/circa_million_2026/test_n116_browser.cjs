'use strict';
const assert=require('node:assert/strict'),crypto=require('node:crypto'),fs=require('node:fs'),path=require('node:path'),zlib=require('node:zlib');
const {pathToFileURL}=require('node:url');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE_DIR||'playwright');
const {verifyHostedHtml}=require('./n111_current/verified_hosted_html.cjs');
const sha=buf=>crypto.createHash('sha256').update(buf).digest('hex');
const local=process.env.NFL_N116_LOCAL_PATH||path.join(__dirname,'n116_current','index.html');
const native=fs.readFileSync(local),html=native.toString(),encoded=html.match(/<script id="n116data" type="application\/octet-stream" data-encoding="gzip-base64">([^<]+)<\/script>/)[1];
const data=JSON.parse(zlib.gunzipSync(Buffer.from(encoded,'base64')));
const stable='https://sports-edge-lab-nfl.alv-mendizabal.chatgpt.site/circa/';
const hosted=process.env.NFL_N116_ONLINE_URL,url=hosted||pathToFileURL(local).href;
const archive='6a8a0a3424a8e2346985ec257c68115721ec47ec305f30668062b0a1d22efd8d';
const older='06a12d6ac9edee803a762b1540d5d11600cc2e559961918707c252d39f6bb3b9';
const games=data.market.fixtures,past=data.market.coverage.history;
const types=['DraftKings','Kalshi','Polymarket'];
assert.equal(data.release,'N116');assert.equal(data.scope,'public');assert.equal(games.length,272);assert.equal(past.length,570);
assert.equal(new Set(games.concat(past).map(g=>g.game)).size,842);assert(games.concat(past).every(g=>types.every(v=>g.providers[v])));
assert(!html.includes('id="n116private"'));
function privacy(x){
 if(typeof x==='string'){assert(!/s3:\/\/|\/home\/sagemaker-user|AKIA[A-Z0-9]{16}/i.test(x));return;}
 if(!x||typeof x!=='object')return;
 for(const key of ['contract_id','token_id','raw_response','source_sha256','model_version'])assert(!Object.hasOwn(x,key),'Restricted public field '+key);
 if(x.market_probability!=null)assert(x.public_price_allowed===true&&['The Odds API','SportsBookISH'].includes(x.supplier));
 Object.values(x).forEach(privacy);
}
privacy(data);
const licensedSummary=data.market.source_assessment.licensed_kalshi_research;
if(licensedSummary){
 const counts=new Set(['current_listed','current_active_minutes','current_completed_minute_marks','eligible_fixtures','historical_recorded','accepted_checkpoints','top_of_book_available','downloaded_bytes','requests']);
 const labels=new Set(['registered_at','license_url','status']);
 for(const [key,value] of Object.entries(licensedSummary)){
  assert(counts.has(key)||labels.has(key),'Unexpected field in the public licensed-source summary');
  if(counts.has(key))assert(Number.isSafeInteger(value)&&value>=0);
 }
 assert(['NOT_ADMITTED','METADATA_ONLY','HISTORICAL_BOOK_CONFIRMED','CURRENT_MINUTE_STATS_CONFIRMED','BOTH_CONFIRMED'].includes(licensedSummary.status));
}
const law=data.models.laws.find(r=>data.football.forecasts.some(t=>(t.game_id||t.game)===r.game&&t.total));assert(law);
const totalRow=data.football.forecasts.find(t=>(t.game_id||t.game)===law.game&&t.total);
const historical=data.prior.margin_laws.find(r=>String(r.game||r.game_id).startsWith('2024_'));assert(historical);
const timed=new Set(games.filter(g=>g.status==='UPCOMING_TIMED').map(g=>g.game));
const futureMargin=data.models.laws.find(r=>timed.has(r.game)&&r.issue_utc&&r.family===data.models.family);
const futureTotal=data.football.forecasts.find(r=>timed.has(r.game||r.game_id)&&r.issue_utc&&r.family===data.football.family);
const retainedTotal=data.football.forecasts.find(r=>timed.has(r.game||r.game_id)&&r.issue_utc&&r.source_release==='N114');assert(retainedTotal);
assert(futureMargin&&futureTotal);assert(data.models.scores.length&&data.football.scores.length&&data.common.rows.length);
assert(data.market.pooled_panels.length&&data.market.reliability.length&&data.market.negative_checks.length);
const held=games.find(g=>Object.values(g.providers).some(p=>p.archived_projections?.length));assert(held);
const selected=data.circa.next.find(r=>r.picks.length===5&&r.alternatives?.length>=10);assert(selected);
const gid=r=>r.game||r.game_id;
async function request(u){return fetch(u,{credentials:'omit',redirect:'manual',headers:{'Cache-Control':'no-cache'},signal:AbortSignal.timeout(60000)});}
async function routes(){
 const urls=[stable+'n116/',stable+'n115/',stable+'n114/',stable,stable+'publication.json',stable+'n116/private.html',stable+'n116/private_review.html'];
 const [release,prior,n114,current,manifest,...guard]=await Promise.all(urls.map(request));for(const x of [release,prior,n114,current,manifest])assert.equal(x.status,200);
 const m=await manifest.json();verifyHostedHtml(Buffer.from(await release.arrayBuffer()),sha(native),'n116');verifyHostedHtml(Buffer.from(await prior.arrayBuffer()),archive,'n115');
 verifyHostedHtml(Buffer.from(await n114.arrayBuffer()),older,'n114');const declared=m.assets['index.html'].sha256;verifyHostedHtml(Buffer.from(await current.arrayBuffer()),declared,'stable');
 assert.equal(m.assets[m.newest_review_path+'index.html'].sha256,declared);assert.equal(m.assets['n116/index.html'].sha256,sha(native));assert.equal(m.assets['n115/index.html'].sha256,archive);
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
  assert.equal(sha(await page.locator('#n116data').textContent()),sha(encoded));await widthCheck(page,'model leaders',width);
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
  await page.locator('#totalFamily').selectOption({label:(totalRow.source_release==='N114'?'Retained N114 · ':'N116 · ')+totalRow.family.replaceAll('_',' ')});await page.locator('#totalN').fill('41.5');const total=await page.locator('#totalResult').innerText();assert(total.includes('Over '+probability(totalRow.total,x=>x>41.5).toFixed(2)+'%')&&total.includes('Push 0.00%'));
  assert(await page.locator('dialog').evaluate(e=>e.scrollWidth<=e.clientWidth+2));await page.locator('#closeDialog').click();
  await page.locator('#gameq').fill(held.game);const venue=types.find(v=>held.providers[v].archived_projections?.length);await page.locator('#venue').selectOption(venue);assert.equal(await page.locator('.venue-card').count(),1);assert((await page.locator('.venue-card').innerText()).includes('earlier contract terms'));
  await go('Upcoming forecasts','#upTable tbody tr');await page.locator('#upFamily').selectOption(futureMargin.family);assert.equal(await page.locator('#upTable tbody tr').count(),games.filter(g=>g.status!=='PLAYED').length);
  await page.locator('#upFamily').selectOption(futureTotal.family);await page.locator('#upSearch').fill(gid(futureTotal));assert.equal(await page.locator('#upTable tbody tr').count(),1);const up=await page.locator('#upTable').innerText();assert(up.includes(futureTotal.issue_utc)&&up.includes(futureTotal.expected_total.toFixed(2)));
  await page.locator('#upFamily').selectOption(retainedTotal.family);await page.locator('#upSearch').fill(gid(retainedTotal));assert((await page.locator('#upTable').innerText()).includes('Retained N114 pregame issue'));await page.locator('#upFamily').selectOption(futureTotal.family);await page.locator('#upSearch').fill(gid(futureTotal));await page.locator('#upTable button').click();await page.waitForSelector('#gameHeading');assert.equal(await page.locator('#gameHeading').innerText(),futureTotal.away+' at '+futureTotal.home);assert.equal(new URL(page.url()).hash,'#games/'+gid(futureTotal));await page.reload();await page.waitForSelector('#gameHeading');assert.equal(await page.locator('#gameHeading').innerText(),futureTotal.away+' at '+futureTotal.home);
  await go('Market comparisons','#marketTable');if(data.market.source_assessment.historical_research?.target==='away_margin_7_to_12'){assert((await page.locator('#marginBucketScores').innerText()).includes(String(data.market.source_assessment.historical_new_checkpoints)));assert(await page.locator('#marginBucketScores tbody tr').count()>0);}const same=page.locator('#identicalPayoff');assert.equal(await same.locator('tbody tr').count(),2*data.payout.panels.length);const later=data.late_kalshi;
  if(later){const lk=await page.locator('#laterKalshi').innerText();assert(lk.includes(later.observed_utc));assert.deepEqual((await page.locator('#laterKalshi tbody td').allTextContents()).map(Number),[later.upcoming_games,later.listed_contracts,later.completed_trade_minutes_contracts,later.recent_trade_minutes_contracts,later.historical_games,later.historical_checkpoints]);}
  const firstScore=data.payout.panels[0].scores.find(x=>x.source==='model');assert((await same.innerText()).includes(firstScore.brier.toFixed(5)));await same.locator('summary').click();assert((await same.innerText()).includes(firstScore.log_loss.toFixed(5)));const perGame=page.locator('#sharedPayoutGames');assert(await perGame.isVisible());const observed=data.payout.panels.flatMap(r=>r.historical_fixtures||[]);assert(observed.length>0);await perGame.locator('summary').click();const upcoming=data.payout.prospective_panels.flatMap(p=>p.fixtures);
  if(upcoming.length){const f=upcoming[0];await page.locator('#payoutGame').selectOption(f.game);const body=await page.locator('#payoutGameRows').innerText();assert(body.includes('result pending')&&body.includes(f.issue_utc));for(const v of f.venues)assert(body.includes((v.age_seconds/60).toFixed(1)+' min'));}
  await page.locator('#payoutGame').selectOption(observed[0].game);assert((await page.locator('#payoutGameRows').innerText()).includes(observed[0].game.replaceAll('_',' ')));await page.locator('#payoutGameLink').click();await page.waitForSelector('#gameHeading');assert((await page.locator('#caseDetail').innerText()).includes('Settled historical replay'));await go('Market comparisons','#marketTable');await page.locator('#marketVenue').selectOption('Polymarket');await page.locator('#marketScope').selectOption('Separate clock and custody groups');
  const late=data.market.panels.find(r=>r.provider==='Polymarket'&&String(r.checkpoint).startsWith('T5_'));if(late){await page.locator('#marketCheckpoint').selectOption(late.checkpoint);assert((await page.locator('#marketTable').innerText()).includes(late.checkpoint.replaceAll('_',' ')));}
  await page.getByText('Probability reliability by venue',{exact:true}).click();await page.locator('#reliabilityCohort').selectOption({index:0});assert.equal(await page.locator('#reliabilityBins tbody tr').count(),data.market.reliability[0].bins.length);
  await page.locator('#historyVenue').selectOption('Kalshi');await page.locator('#historyQuery').fill(past[0].game);assert.equal(await page.locator('#historyRows tbody tr').count(),1);
  await go('Model features','#modelAvailability');if(data.personnel)assert.equal(await page.locator('#personnelDrive tbody tr').count(),data.personnel.groups.length);assert((await page.locator('#modelAvailability').innerText()).includes(data.availability.counts.reported_players+' listed players'));
  const refresh=data.personnel?.current_refresh;
  if(refresh){
   assert.equal(await page.locator('#practiceRefresh tbody tr').count(),refresh.rows.length);
   const revised=refresh.rows.find(r=>r.issue_utc),carried=refresh.rows.find(r=>!r.issue_utc&&r.original_issue_utc);
   for(const r of [revised,carried].filter(Boolean)){
    const row=page.locator('#practiceRefresh tbody tr').filter({hasText:r.game.replaceAll('_',' ')});
    assert.equal(await row.count(),1);
    const values=await row.innerText();
    assert(values.includes(r.original_issue_utc));
    if(r.issue_utc)assert(values.includes(r.issue_utc));
   }
  }
  await go('Circa cards','#cardResults');await page.locator('#cardFamily').selectOption(selected.family);const card=await page.locator('#cardResults').innerText();assert(card.includes('Top five')&&card.includes('Alternative'));assert.deepEqual(errors,[]);
  console.log(JSON.stringify({width,hosted:!!hosted,fixtures:games.length,earlierGames:past.length,sha256:sha(native),errors:errors.length,verified:'views, margin, total, issue clocks, market ages, venue bins, Circa alternatives'}));await page.close();
 }}finally{await browser.close();}
})().catch(err=>{console.error(err);process.exitCode=1;});
