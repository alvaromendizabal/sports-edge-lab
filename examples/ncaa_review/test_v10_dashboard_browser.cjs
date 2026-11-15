// Actual Chromium, local source plus the deployed public URL when supplied.
const assert=require('node:assert/strict');
const path=require('node:path');
const fs=require('node:fs');
const http=require('node:http');
(async()=>{
 const {chromium}=require(process.env.PLAYWRIGHT_MODULE_DIR||'playwright');
 const browser=await chromium.launch({headless:true});
 const docs=path.resolve(__dirname,'../../docs/ncaa');
 const allowedAssets=new Set(['v10.html','v11.html','v11_r12_canonical_games.json','v11_r12_unresolved_inventory.json','v12.html','v12_r14_public_evidence.json','v12_r14_descriptive_uncertainty.json']);
 const server=http.createServer((request,response)=>{
  const name=request.url.split('?')[0].replace(/^\//,'');
  if(!allowedAssets.has(name)){response.writeHead(404);response.end();return;}
  response.writeHead(200,{'Content-Type':name.endsWith('.json')?'application/json; charset=utf-8':'text/html; charset=utf-8'});
  fs.createReadStream(path.join(docs,name)).pipe(response);
 });
 await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
 const localOrigin=`http://127.0.0.1:${server.address().port}`;
 const receipts=[];
 try{
  const urls=['v10','v11'].map(version=>localOrigin+'/'+version+'.html');
  if(process.env.SEL_V10_LIVE_URL)urls.push(process.env.SEL_V10_LIVE_URL);
  if(process.env.SEL_V11_LIVE_URL)urls.push(process.env.SEL_V11_LIVE_URL);
  for(const url of urls){
   const isV11=/\/v11(?:\.html)?(?:[?#]|$)/.test(url);
   const page=await browser.newPage();const errors=[],assetRequests=[];page.on('pageerror',e=>errors.push(e.message));
   page.on('request',request=>{if(/v11_r12_.*\.json/.test(request.url()))assetRequests.push(request.url());});
   try{
    for(const width of [1440,390]){
     const requestStart=assetRequests.length;
     await page.setViewportSize({width,height:1000});
     const response=await page.goto(url,{waitUntil:'load',timeout:45000});
     if(url.startsWith('https:'))assert.equal(response.status(),200);
     await page.waitForFunction(()=>window.SEL_V10_READY||window.SEL_V10_ERROR||window.SEL_V11_READY||window.SEL_V11_ERROR,{timeout:45000});
     assert.equal(await page.evaluate(()=>window.SEL_V10_ERROR||window.SEL_V11_ERROR),undefined);
     assert.equal(await page.evaluate(()=>(window.SEL_V11_READY||window.SEL_V10_READY).games),isV11?25833:25847);
     assert.equal(await page.evaluate(()=>(window.SEL_V11_READY||window.SEL_V10_READY).models),336);
     assert.match(await page.locator('#scope').innerText(),isV11?/Future unissued candidate values are withheld/:/not a refreshed complete/);
     assert((await page.locator('#leader-rows tr').count())>1);
     for(const [season,competition,total] of [['2027','ncaam',isV11?1773:1779],['2027','ncaaw',isV11?1652:1660],['2026','ncaam',5749],['2026','ncaaw',5621],['2025','ncaam',5758],['2025','ncaaw',5280]]){
      await page.selectOption('#season',season);await page.selectOption('#league',competition);
      assert.match(await page.locator('#game-count').innerText(),new RegExp('^'+total+' games'));
      assert.equal(await page.locator('#game-rows tr').count(),25);
     }
     await page.fill('#search','__no_such_authentic_team__');
     assert.match(await page.locator('#game-count').innerText(),/^0 games/);
     await page.fill('#search','');await page.selectOption('#season','2027');
     await page.selectOption('#league','all');await page.selectOption('#target','total');
     await page.click('#next');assert.match(await page.locator('#game-count').innerText(),/page 2/);
     await page.selectOption('#evidence','ORIGINAL_ISSUED');
     assert.match(await page.locator('#model-rows').innerText(),/No qualified evidence/);
     await page.selectOption('#evidence','all');
     if(isV11){
      await page.waitForFunction(()=>window.SEL_NCAA_CENSUS_READY||window.SEL_NCAA_CENSUS_ERROR,{timeout:15000});
      assert.equal(await page.evaluate(()=>window.SEL_NCAA_CENSUS_ERROR),undefined);
      assert.match(await page.locator('#census-count').innerText(),/^2,502 canonical games/);
      assert.equal(await page.locator('#census-rows tr').count(),25);
      assert.equal(assetRequests.slice(requestStart).some(u=>u.includes('unresolved_inventory')),false);
      await page.selectOption('#census-status','in_progress');
      await page.waitForFunction(()=>window.SEL_NCAA_CENSUS_READY.filteredRows===3);
      assert.match(await page.locator('#census-count').innerText(),/^3 canonical games/);
      await page.selectOption('#census-status','all');
      await page.selectOption('#census-kind','UNRESOLVED_OFFICIAL_RECORD');
      await page.waitForFunction(()=>window.SEL_NCAA_CENSUS_READY.filteredRows===903);
      assert.match(await page.locator('#census-count').innerText(),/^903 inventory rows/);
      await page.selectOption('#census-kind','UNRESOLVED_PROVIDER_SCHEDULE_RECORD');
      await page.waitForFunction(()=>window.SEL_NCAA_CENSUS_READY.filteredRows===21117);
      assert.match(await page.locator('#census-count').innerText(),/^21,117 inventory rows/);
      await page.click('#census-next');assert.match(await page.locator('#census-count').innerText(),/page 2/);
      await page.selectOption('#census-kind','all');
      await page.waitForFunction(()=>window.SEL_NCAA_CENSUS_READY.filteredRows===24522);
      await page.fill('#census-search','ncaam:ncaa:contest:6661200');
      await page.waitForFunction(()=>window.SEL_NCAA_CENSUS_READY.filteredRows===2);
      assert.match(await page.locator('#census-rows').innerText(),/No qualified saved forecast/);
      const [download]=await Promise.all([page.waitForEvent('download'),page.click('#census-export')]);
      const filtered=JSON.parse(fs.readFileSync(await download.path(),'utf8'));
      assert.equal(filtered.row_count,2);assert.equal(filtered.rows.length,2);
      assert.equal(filtered.report_asof,'2026-11-14T05:23:59.250627+00:00');
      assert.equal(filtered.complete_official_universe,false);
      assert.deepEqual(filtered.columns,['league','event_id','away_team','home_team','event_time','time_precision','status','inventory_kind','missing_reasons','away_score','home_score']);
      assert.equal(new Set(filtered.rows.map(r=>r[7])).size,2);
      await page.fill('#census-search','');await page.selectOption('#census-kind','CANONICAL_ACQUISITION_GAME');
      await page.waitForFunction(()=>window.SEL_NCAA_CENSUS_READY.filteredRows===2502);
      assert.match(await page.locator('#weight-status').innerText(),/weighted ranks are withheld/);
      await page.locator('#execution-status summary').click();
      assert.equal(await page.locator('#execution-rows tr').count(),4);
      assert.match(await page.locator('#execution-status').innerText(),/Latest owner execution stopped before fitting/);
      assert.match(await page.locator('#scope').innerText(),/Latest owner execution: R12 resource-deferred before fitting/);
      assert.match(await page.locator('#execution-status').innerText(),/8\.49×/);
      assert.equal(await page.locator('#owner-attempt-rows tr').count(),4);
      assert.match(await page.locator('#execution-tally').innerText(),/15 actual owner runs/);
      assert.match(await page.locator('#r12-return-evidence').innerText(),/2 PUT \/ 2 GET calls/);
      assert.match(await page.locator('#r12-admission-diagnosis').innerText(),/114 reported measured capacity admitted/);
      assert.match(await page.locator('#next-release-status').innerText(),/R13 engineering release verified; owner execution pending/);
      assert.match(await page.locator('#next-release-status').innerText(),/383 \/ 383/);
      assert.equal(await page.locator('#r13-validation-rows tr').count(),7);
      assert.match(await page.locator('#next-release-status').innerText(),/No production 12-core throughput/);
      assert.match(await page.locator('#next-release-status').innerText(),/1\.118636 s/);
      assert.equal(await page.locator('#r12-validation-rows tr').count(),6);
      assert.match(await page.locator('#r12-local-validation').innerText(),/318 \/ 318/);
      assert.match(await page.locator('#r12-local-validation').innerText(),/first local transport attempt stopped/);
     }
     const dimensions=await page.evaluate(()=>({documentWidth:document.documentElement.scrollWidth,viewport:innerWidth}));
     assert.equal(dimensions.documentWidth<=dimensions.viewport,true,JSON.stringify({url,width,...dimensions}));
     if(process.env.DASHBOARD_SCREENSHOTS){
      fs.mkdirSync(process.env.DASHBOARD_SCREENSHOTS,{recursive:true});
      await page.screenshot({path:path.join(process.env.DASHBOARD_SCREENSHOTS,`ncaa-${isV11?'v11':'v10'}-${url.startsWith('https:')?'live':'source'}-${width}.png`),fullPage:true});
     }
     receipts.push({url,width,version:isV11?'v11':'v10',allSixCohorts:true,paging:true,search:true,missingOriginalsExplicit:true,realChromium:true});
    }
    assert.deepEqual(errors,[]);
   }finally{await page.close();}
  }
  // The current V12 view has its own dated cohorts and explicit missing markets.
  for(const width of [1440,390]){
   const page=await browser.newPage({viewport:{width,height:1000}}),errors=[];
   page.on('pageerror',error=>errors.push(error.message));
   try{
    await page.goto(localOrigin+'/v12.html',{waitUntil:'load'});
    await page.waitForFunction(()=>window.SEL_V12_READY||window.SEL_V12_ERROR);
    assert.equal(await page.evaluate(()=>window.SEL_V12_ERROR),undefined);
    assert.equal(await page.evaluate(()=>window.SEL_V12_READY.observedGames),2503);
    await page.waitForFunction(()=>window.SEL_V12_UNCERTAINTY_READY||window.SEL_V12_UNCERTAINTY_ERROR);
    assert.equal(await page.evaluate(()=>window.SEL_V12_UNCERTAINTY_ERROR),undefined);
    assert.equal(await page.locator('#uncertainty-rows tr').count(),7);
    assert.match(await page.locator('#uncertainty-rows').innerText(),/73\.33% – 83\.74%/);
    assert.match(await page.locator('#uncertainty-rows').innerText(),/78\.28% – 85\.08%/);
    await page.waitForFunction(()=>window.SEL_V12_RATING_READY||window.SEL_V12_RATING_ERROR);
    assert.equal(await page.evaluate(()=>window.SEL_V12_RATING_ERROR),undefined);
    assert.equal(await page.locator('#rating-comparison-rows tr').count(),12);
    assert.match(await page.locator('#rating-comparison-scope').innerText(),/unchanged November 14 source evidence/);
    assert.match(await page.locator('#rating-comparison-rows').innerText(),/-1\.42 pp to 3\.98 pp/);
    assert.match(await page.locator('#latest-execution-title').innerText(),/Latest execution: R16 deferred\. Latest model comparison: R14\./);
    assert.match(await page.locator('#latest-execution-r16').innerText(),/484\.95 seconds before return finalization/);
    assert.match(await page.locator('#latest-execution-r16').innerText(),/48 cores/);
    assert.match(await page.locator('#latest-execution-r16').innerText(),/1 core leased at the failure-time admission decision/);
    assert.match(await page.locator('#latest-execution-r16').innerText(),/New target, residual and scalar calibration fits: 0\. Historical target models reused: 40\. Current target fits reused: 0\./);
    assert.match(await page.locator('#latest-execution-r16').innerText(),/not 19\.65 seconds of continuous memory pressure/);
    await page.locator('#prior-execution-r15 summary').click();
    assert.match(await page.locator('#preserved-execution-r15').innerText(),/109\.60 seconds before return finalization/);
    assert.match(await page.locator('#latest-execution-clock').innerText(),/November 14, 2026, 10:09:49 p\.m\. Pacific/);
    assert.equal(await page.locator('#current-model-rows tr').count(),6);
    assert.equal(await page.locator('#historical-rows tr').count(),14);
    assert.equal(await page.locator('#provider-rows tr').count(),8);
    assert.match(await page.locator('#provider-rows').innerText(),/Unavailable \/ Unavailable/);
    assert.match(await page.locator('#game-rows').innerText(),/74 – 72/);
    await page.selectOption('#league','ncaaw');
    assert.match(await page.locator('#game-count').innerText(),/^1,248 matching observed games/);
    assert.equal(await page.locator('#uncertainty-head th').count(),2);
    assert.match(await page.locator('#uncertainty-head').innerText(),/Women · 585/);
    assert.equal(await page.locator('#rating-comparison-rows tr').count(),6);
    assert.match(await page.locator('#rating-comparison-rows').innerText(),/Women · Winner accuracy/);
    await page.selectOption('#game-status','future');
    assert.match(await page.locator('#game-count').innerText(),/^455 matching observed games/);
    assert.match(await page.locator('#game-rows').innerText(),/Unverified/);
    await page.selectOption('#league','ncaam');
    assert.match(await page.locator('#game-count').innerText(),/^438 matching observed games/);
    await page.selectOption('#game-status','scheduled_start_passed');
    assert.match(await page.locator('#game-count').innerText(),/^1 matching observed games/);
    await page.selectOption('#game-status','all');
    await page.click('#next');
    assert.match(await page.locator('#game-count').innerText(),/page 2 of/);
    await page.fill('#game-search','no-such-authentic-team');
    assert.match(await page.locator('#game-count').innerText(),/^0 matching/);
    await page.fill('#game-search','Notre Dame');
    const [download]=await Promise.all([page.waitForEvent('download'),page.click('#download-games')]);
    const exported=JSON.parse(fs.readFileSync(await download.path(),'utf8'));
    assert.equal(exported.complete_official_season_universe,false);
    assert(exported.rows.length>0);
    assert(exported.rows.every(row=>(row.away_team+' '+row.home_team).includes('Notre Dame')));
    await page.fill('#game-search','');await page.selectOption('#league','all');
    await page.selectOption('#historical-season','2025');
    assert.match(await page.locator('#historical-rows').innerText(),/5,758/);
    const dimensions=await page.evaluate(()=>({documentWidth:document.documentElement.scrollWidth,viewport:innerWidth}));
    assert.equal(dimensions.documentWidth<=dimensions.viewport,true,JSON.stringify({width,...dimensions}));
    if(process.env.DASHBOARD_SCREENSHOTS){
     await page.screenshot({path:path.join(process.env.DASHBOARD_SCREENSHOTS,`ncaa-v12-source-${width}.png`),fullPage:true});
    }
    assert.deepEqual(errors,[]);
    receipts.push({version:'v12',width,source:true,datedCohorts:true,missingMarketsExplicit:true,futureClockFilter:true,downloadVerified:true,realChromium:true});
   }finally{await page.close();}
  }
 }finally{await browser.close();await new Promise(resolve=>server.close(resolve));}
 console.log(JSON.stringify({status:'PASS',receipts}));
})().catch(error=>{console.error(error);process.exitCode=1;});

